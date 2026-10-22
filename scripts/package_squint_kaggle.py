"""Stage the private Kaggle runtime dataset for the squint-first production pipeline.

One fresh output directory is written. It is exactly what `kaggle datasets create -p <output>` takes:

    <output>/dataset-metadata.json   id rohanvinaik/rsna-knee-squint-runtime (the caller uploads it)
    <output>/runtime-bundle.tar      deterministic tar: source/, memory/, config/ and RUNTIME_MANIFEST.json
    <output>/RUNTIME_MANIFEST.json   the same manifest plus the tar's own sha256 and size

Inside the tar:

    source/src/knee/**/*.py          every Python file of the package, nothing else of src/
    source/scripts/run_interiors.py  the one runtime entry point (plus any --extra-script)
    memory/...                       the supplied squint memory, byte for byte
    config/scaling-selection.json    only when --scaling-selection is supplied (see below)
    RUNTIME_MANIFEST.json            every file above by path, role, sha256 and size

The two Kaggle wrappers (`kaggle/squint-production/run_squint.py`, `kaggle/squint-scaling/run_scaling.py`)
verify the tar against the outer manifest, copy the code and memory to local disk and check every file
against the inner manifest before running anything.

What it does not do: it never touches the network, uploads, submits to the competition, edits the source
or the memory, runs the pipeline, or holds credentials. It refuses (exit 2, nothing left behind) when:
no top-level JSON file of the memory (plain, .gz or .xz, parsed whole) has the exact top-level
`schema` value `knee.squint-memory/v1` (a string nested elsewhere, such as inside `cases`, is not a
schema); any file is a symlink, a pickle or model artifact, an
object-dtype numpy array, a credential-like name, DICOM pixel data or a teaching label file; any text carries
a secret-like string; a shipped Python file asks numpy for `allow_pickle=True` or does not parse as the
offline runtime's Python (3.13, the interpreter of the cp313 wheels; a best-effort grammar check, so the
newer syntax CPython's parser version-gates, such as template strings, is refused);
a shipped file imports a `knee` module, or a name a `knee` package binds, that the bundle does not hold; or
the source lacks the squint production modules.

The import rule counts every import wherever it sits: the production code reaches several modules lazily and
some behind `except ImportError`, where a missing one is a quiet degrade to open results after hours of work,
not a crash, and the wrappers' import check cannot see it. Shipped code is parsed, never imported or run:
modules are checked, and the names a package's `__init__` binds; attributes of a plain module are not.

Not packaged, by construction: `.git`, `.serena`, caches, `data/`, archives, tests, study data, reading
products and anything under `src/` that is not a `.py` file (those are listed under `source.excluded` in the
manifest with their reason, so nothing is dropped silently).

`--scaling-selection FILE` ships an optional, caller-authored list of study UIDs for the scaling notebook
(`knee.squint-scaling-selection/v1`). It is a selection of which studies to read, never a label: any other key
(calls, labels, predictions) is refused. Unknown labels are not part of it and are preserved by the notebook.

Determinism: sorted members, mtime 0, owner 0:0, mode 0644, canonical JSON with sorted keys and no clock
anywhere. The same inputs give byte-identical output.

CLI (invoked with Python; the file is not executable and has no shebang):
    python scripts/package_squint_kaggle.py --memory MEMORY --output NEWDIR [--root-source REPO] [--verify]
                             [--extra-script scripts/x.py ...] [--scaling-selection FILE]
    python scripts/package_squint_kaggle.py --output EXISTINGDIR --verify [--memory MEMORY] [--root-source REPO]

`--root-source` defaults to the repository that holds this script. With `--verify` and an existing output
the staging is re-read independently (tar, manifests, metadata, secrets, pickle) and, when `--memory` or
`--root-source` are given, compared with those sources to prove it is not stale. With `--verify` on a build
the same re-read also compares the staging with its sources.

Exit 0 with a JSON summary on stdout; 2 on a refusal (reason on stderr). Standard library only.
"""

from __future__ import annotations

import argparse
import ast
import gzip
import hashlib
import io
import json
import lzma
import os
import re
import shutil
import stat
import struct
import sys
import tarfile
import zipfile
from collections.abc import Callable, Mapping, Sequence
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import IO, Any

MANIFEST_SCHEMA = "knee.squint-runtime-manifest/v1"
MEMORY_SCHEMA = "knee.squint-memory/v1"
LEGACY_MEMORY_SCHEMAS = ("knee.diagnostic-store/v1", "knee.diagnostic-memory/v1")
SELECTION_SCHEMA = "knee.squint-scaling-selection/v1"
DATASET_ID = "rohanvinaik/rsna-knee-squint-runtime"
TAR_NAME = "runtime-bundle.tar"
MANIFEST_NAME = "RUNTIME_MANIFEST.json"
METADATA_NAME = "dataset-metadata.json"
STAGING_FILES = (METADATA_NAME, MANIFEST_NAME, TAR_NAME)
RUNNER = "scripts/run_interiors.py"
SELECTION_DEST = "config/scaling-selection.json"
ENTRYPOINT = "source/" + RUNNER
PYTHONPATH_ENTRIES = ["source/src"]
SOURCE_PACKAGE = ("src", "knee")
SOURCE_ROOT = "source/" + SOURCE_PACKAGE[0] + "/"
# The interpreter the offline wheels (cp313) and both Kaggle wrappers run: shipped files must parse as it does.
RUNTIME_PYTHON = (3, 13)
REQUIRED_PATHS = (
    "source/scripts/run_interiors.py",
    "source/src/knee/__init__.py",
    "source/src/knee/diagnosis/squint_profiles.py",
    "source/src/knee/diagnosis/squint_memory.py",
    "source/src/knee/diagnosis/squint_locator.py",
    "source/src/knee/diagnosis/squint_pipeline.py",
)
ROLES = frozenset({"source", "runtime_script", "memory", "config", "navigation"})
NAVIGATION_FILES = ("navigation.json", "schema.json", "weights.npz")
NAVIGATION_SCHEMA = "knee.som-navigation-artifact/v1"
PYTHON_ROLES = frozenset({"source", "runtime_script"})
SELECTION_KEYS = frozenset({"schema", "study_uids", "partition", "source", "note"})
DEFAULT_PARTITION = "scaling"
UID_RE = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._-]*$")
PARTITION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DEFAULT_ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_DIR_NAMES = frozenset(
    {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".hypothesis",
        ".cache",
        ".idea",
        ".vscode",
        ".serena",
        "serena",
        "archive",
        "archive2",
        "tests",
    }
)
FORBIDDEN_COMPONENTS = EXCLUDED_DIR_NAMES
CACHE_SUFFIXES = frozenset({".pyc", ".pyo", ".nbc", ".nbi"})
ARCHIVE_SUFFIXES = frozenset(
    {".zip", ".tar", ".tgz", ".gz", ".bz2", ".xz", ".7z", ".rar", ".whl"}
)
CREDENTIAL_SUFFIXES = frozenset({".pem", ".key", ".p12", ".pfx", ".token", ".env"})
CREDENTIAL_PREFIXES = (".env", ".netrc", "id_rsa", "id_ed25519", "id_ecdsa")
PICKLE_SUFFIXES = frozenset(
    {
        ".pkl",
        ".pickle",
        ".pk",
        ".joblib",
        ".dill",
        ".cloudpickle",
        ".pt",
        ".pth",
        ".ckpt",
        ".onnx",
        ".safetensors",
    }
)
PICKLE_MODULES = frozenset(
    {
        "pickle",
        "cPickle",
        "_pickle",
        "dill",
        "cloudpickle",
        "joblib",
        "shelve",
        "marshal",
    }
)
IMAGE_DATA_SUFFIXES = frozenset({".dcm", ".dicom", ".ima", ".nii"})
TEACHING_SOURCE_NAMES = frozenset(
    {
        "train.csv",
        "teaching-source.csv",
        "teaching-ledger.json",
        "labels.csv",
        "train_labels.csv",
    }
)
SECRET_PATTERNS: tuple[tuple[str, re.Pattern[bytes]], ...] = (
    ("private_key", re.compile(rb"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----")),
    ("kaggle_key_json", re.compile(rb'"key"\s*:\s*"[0-9a-f]{32}"')),
    ("kaggle_token", re.compile(rb"KGAT_[0-9a-fA-F]{20,}")),
    ("aws_access_key", re.compile(rb"AKIA[0-9A-Z]{16}")),
    ("github_token", re.compile(rb"gh[pousr]_[A-Za-z0-9]{36,}")),
    ("slack_token", re.compile(rb"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("provider_secret_key", re.compile(rb"sk-(?:ant-)?[A-Za-z0-9_\-]{32,}")),
    (
        "credential_assignment",
        re.compile(
            rb"(?i)(?:api[_-]?key|secret|passwd|password)\s*[:=]\s*['\"][A-Za-z0-9_\-+/=]{24,}['\"]"
        ),
    ),
)
CHUNK = 1 << 20
OVERLAP = 512
KEPT_LIMIT = 64 << 20
NPY_HEADER_LIMIT = 1 << 16
TAR_FIXED = (0o644, 0, 0, 0, "", "")

Opener = Callable[[], IO[bytes]]


class PackagingError(Exception):
    """A refusal: nothing was built, or the staging does not verify."""


@dataclass(frozen=True)
class Planned:
    """One file of the bundle: where it is, where it goes, its role and what it holds."""

    source: Path | None
    dest: str
    role: str
    sha256: str
    bytes: int


@dataclass(frozen=True)
class PythonFacts:
    """What one shipped Python file says about the package it ships with."""

    warnings: tuple[str, ...]
    # (module, names, line) of each import of the shipped package, relative ones made absolute
    imports: tuple[tuple[str, tuple[str, ...], int], ...]
    # the names a package's `__init__` binds at module level; None when they cannot be listed
    defined: frozenset[str] | None


# ---------------------------------------------------------------------------------------------
# Safe file access and hashing
# ---------------------------------------------------------------------------------------------


def open_regular(path: Path) -> IO[bytes]:
    """Open a regular file for reading; a symlink or any other kind of entry is refused."""
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise PackagingError(f"cannot stat {path}: {exc}") from exc
    if stat.S_ISLNK(info.st_mode):
        raise PackagingError(f"unsafe symlink: {path}")
    if not stat.S_ISREG(info.st_mode):
        raise PackagingError(f"not a regular file: {path}")
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError as exc:
        raise PackagingError(f"cannot open {path}: {exc}") from exc
    return os.fdopen(descriptor, "rb")


def sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with open_regular(path) as reader:
        for block in iter(lambda: reader.read(CHUNK), b""):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def path_opener(path: Path) -> Opener:
    return lambda: open_regular(path)


class _HashingReader:
    """Reads through to an inner file while hashing exactly what was read."""

    def __init__(self, handle: IO[bytes]) -> None:
        self.handle = handle
        self.digest = hashlib.sha256()
        self.size = 0

    def read(self, count: int = -1) -> bytes:
        data = self.handle.read(count)
        self.digest.update(data)
        self.size += len(data)
        return data


def safe_relative(text: str) -> PurePosixPath:
    """A relative POSIX path with no `..`, `.`, empty, absolute or backslash component."""
    relative = PurePosixPath(text)
    if (
        not text
        or "\0" in text
        or "\\" in text
        or relative.is_absolute()
        or relative.as_posix() != text
        or any(part in ("", ".", "..") for part in relative.parts)
    ):
        raise PackagingError(f"unsafe path (traversal or non-normal form): {text!r}")
    return relative


def tree_id(entries: Sequence[dict[str, Any]]) -> str:
    """The bundle's identity: its sorted (path, sha256) pairs. The wrappers recompute the same."""
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: item["path"]):
        digest.update(entry["path"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(entry["sha256"].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def dumps(document: object) -> str:
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


# ---------------------------------------------------------------------------------------------
# Content checks: secrets, pickle, object arrays
# ---------------------------------------------------------------------------------------------


def check_pickle_magic(block: bytes, label: str) -> None:
    if len(block) >= 2 and block[0] == 0x80 and 2 <= block[1] <= 5:
        raise PackagingError(f"{label}: starts like a pickle stream; pickle is refused")


def hash_and_scan(
    reader: IO[bytes], label: str, keep: bool
) -> tuple[str, int, bytes | None]:
    """One pass: sha256, size, secret-like strings (across block seams) and the pickle magic."""
    digest = hashlib.sha256()
    size = 0
    tail = b""
    kept: list[bytes] = []
    first = True
    for block in iter(lambda: reader.read(CHUNK), b""):
        if first:
            check_pickle_magic(block, label)
            first = False
        window = tail + block
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(window):
                raise PackagingError(
                    f"{label}: secret-like content ({name}) is refused"
                )
        tail = window[-OVERLAP:]
        digest.update(block)
        size += len(block)
        if keep:
            if size > KEPT_LIMIT:
                raise PackagingError(f"{label}: too large to inspect as text")
            kept.append(block)
    return digest.hexdigest(), size, (b"".join(kept) if keep else None)


def descr_has_object(descr: object) -> bool:
    """True when a numpy dtype description holds an object ('O') kind anywhere."""
    if isinstance(descr, str):
        return descr.lstrip("<>|=!@")[:1] == "O"
    if isinstance(descr, (list, tuple)):
        for item in descr:
            if isinstance(item, tuple) and len(item) >= 2:
                if descr_has_object(item[1]):
                    return True
            elif isinstance(item, (list, str)) and descr_has_object(item):
                return True
    return False


def check_npy_header(data: bytes, label: str) -> None:
    if data[:6] != b"\x93NUMPY" or len(data) < 12:
        raise PackagingError(f"{label}: not a numpy .npy array")
    major = data[6]
    if major == 1:
        (length,) = struct.unpack("<H", data[8:10])
        start = 10
    elif major in (2, 3):
        (length,) = struct.unpack("<I", data[8:12])
        start = 12
    else:
        raise PackagingError(f"{label}: unknown .npy version {major}")
    raw = data[start : start + length]
    if len(raw) != length:
        raise PackagingError(f"{label}: .npy header is truncated or too large to check")
    try:
        header = ast.literal_eval(raw.decode("latin-1" if major < 3 else "utf-8"))
    except (ValueError, SyntaxError, UnicodeDecodeError) as exc:
        raise PackagingError(f"{label}: unreadable .npy header: {exc}") from exc
    if not isinstance(header, dict) or "descr" not in header:
        raise PackagingError(f"{label}: .npy header has no dtype")
    if descr_has_object(header["descr"]):
        raise PackagingError(
            f"{label}: object-dtype arrays are pickled and are refused"
        )


def check_container(suffix: str, opener: Opener, label: str) -> None:
    """Header-level checks of numpy and compressed members, run against the stored bytes."""
    if suffix == ".npy":
        with opener() as reader:
            check_npy_header(reader.read(NPY_HEADER_LIMIT), label)
    elif suffix == ".npz":
        with opener() as reader:
            try:
                with zipfile.ZipFile(reader) as archive:
                    for info in archive.infolist():
                        member = info.filename
                        if not member.endswith(".npy"):
                            raise PackagingError(
                                f"{label}: npz member {member!r} is not a .npy array"
                            )
                        with archive.open(info) as handle:
                            check_npy_header(
                                handle.read(NPY_HEADER_LIMIT), f"{label}::{member}"
                            )
            except zipfile.BadZipFile as exc:
                raise PackagingError(
                    f"{label}: not a valid npz archive: {exc}"
                ) from exc
    elif suffix in (".xz", ".gz"):
        try:
            if suffix == ".xz":
                with opener() as reader, lzma.open(reader, "rb") as handle:
                    check_pickle_magic(handle.read(16), f"{label} (decompressed)")
            else:
                with opener() as reader, gzip.open(reader, "rb") as handle:
                    check_pickle_magic(handle.read(16), f"{label} (decompressed)")
        except (lzma.LZMAError, OSError, EOFError) as exc:
            raise PackagingError(f"{label}: unreadable compressed file: {exc}") from exc


def module_of(dest: str) -> tuple[str, bool] | None:
    """The dotted module a shipped source file is, and whether it is a package's `__init__`."""
    if not dest.startswith(SOURCE_ROOT) or not dest.endswith(".py"):
        return None
    parts = PurePosixPath(dest[len(SOURCE_ROOT) : -len(".py")]).parts
    if parts[-1] == "__init__":
        return ".".join(parts[:-1]), True
    return ".".join(parts), False


def package_imports(
    tree: ast.AST, label: str
) -> tuple[tuple[str, tuple[str, ...], int], ...]:
    """Every import of the shipped package, wherever it sits, as (module, names, line)."""
    located = module_of(label)
    package = (
        ""
        if located is None
        else located[0]
        if located[1]
        else located[0].rpartition(".")[0]
    )
    parts = package.split(".") if package else []
    found: list[tuple[str, tuple[str, ...], int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend((alias.name, (), node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names = tuple(alias.name for alias in node.names)
            module = node.module or ""
            if node.level and located is None:
                continue  # a script has no package to be relative to
            if node.level > len(parts):
                # above the top package: never resolves
                module = "." * node.level + module
            elif node.level:
                base = parts[: len(parts) - node.level + 1]
                module = ".".join([*base, *([module] if module else [])])
            found.append((module, names, node.lineno))
    own = SOURCE_PACKAGE[-1]
    return tuple(
        item
        for item in sorted(found, key=lambda item: (item[2], item[0]))
        if item[0].partition(".")[0] in (own, "")
    )


def bound_names(tree: ast.Module) -> frozenset[str] | None:
    """The names a module binds at its top level, or None when they cannot be listed."""
    names: set[str] = set()
    pending: list[ast.AST] = list(tree.body)
    while pending:
        node = pending.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name == "__getattr__":
                return None
            names.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                if alias.name == "*":
                    return None
                names.add(alias.asname or alias.name.partition(".")[0])
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names.update(
                name.id
                for target in targets
                for name in ast.walk(target)
                if isinstance(name, ast.Name)
            )
        else:
            for field in ("body", "orelse", "finalbody", "handlers", "cases"):
                pending.extend(getattr(node, field, ()))
    return frozenset(names)


def inspect_python(label: str, data: bytes) -> PythonFacts:
    """Parse a shipped file as the offline runtime's Python; refuse allow_pickle=True; report its imports."""
    try:
        tree = ast.parse(data, filename=label, feature_version=RUNTIME_PYTHON)
    except (SyntaxError, ValueError) as exc:
        raise PackagingError(
            f"{label} does not parse as Python {RUNTIME_PYTHON[0]}.{RUNTIME_PYTHON[1]} "
            f"(the offline runtime): {exc}"
        ) from exc
    warnings: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.keyword)
            and node.arg == "allow_pickle"
            and isinstance(node.value, ast.Constant)
            and node.value.value is True
        ):
            raise PackagingError(f"{label}: allow_pickle=True is refused")
        if isinstance(node, ast.Import):
            names = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module.split(".")[0]]
        else:
            continue
        for name in names:
            if name in PICKLE_MODULES:
                warnings.append(f"{label} imports {name}")
    located = module_of(label)
    return PythonFacts(
        tuple(warnings),
        package_imports(tree, label),
        bound_names(tree) if located is not None and located[1] else None,
    )


def import_problems(facts_by_dest: Mapping[str, PythonFacts]) -> list[str]:
    """Imports of the shipped package that name a module, or a package name, the bundle does not hold."""
    modules: dict[str, bool] = {}  # dotted name -> is a package
    inits: dict[str, PythonFacts] = {}
    for dest, facts in facts_by_dest.items():
        located = module_of(dest)
        if located is None:
            continue
        name, is_package = located
        modules[name] = is_package
        if is_package:
            inits[name] = facts
        parts = name.split(".")
        for end in range(1, len(parts)):
            modules.setdefault(".".join(parts[:end]), True)
    problems: list[str] = []
    for dest in sorted(facts_by_dest):
        for module, names, line in facts_by_dest[dest].imports:
            if module not in modules:
                problems.append(
                    f"{dest}:{line}: imports {module}, which the bundle does not ship"
                )
                continue
            if not modules[module]:
                continue  # the attributes of a plain module are not listed
            init = inits.get(module)
            for name in names:
                if f"{module}.{name}" in modules or name == "*":
                    continue
                if init is not None and init.defined is None:
                    continue  # a star import or module __getattr__: not guessed at
                if init is None or name not in (init.defined or ()):
                    problems.append(
                        f"{dest}:{line}: imports {module}.{name}, which the bundle does not ship"
                    )
    return problems


def require_closed_imports(facts_by_dest: Mapping[str, PythonFacts]) -> None:
    problems = import_problems(facts_by_dest)
    if problems:
        raise PackagingError(
            "the shipped source is not closed under its own imports:\n- "
            + "\n- ".join(problems)
        )


def validate_selection_bytes(data: bytes, label: str) -> dict[str, Any]:
    """The optional scaling selection: study UIDs to read, and nothing that could be a label."""
    try:
        document = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise PackagingError(f"{label}: not JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise PackagingError(f"{label}: must hold a JSON object")
    extra = sorted(set(document) - SELECTION_KEYS)
    if extra:
        raise PackagingError(
            f"{label}: keys {extra} are refused; a selection names studies only, "
            "never calls, labels or predictions"
        )
    if document.get("schema") != SELECTION_SCHEMA:
        raise PackagingError(f"{label}: schema must be {SELECTION_SCHEMA}")
    uids = document.get("study_uids")
    if (
        not isinstance(uids, list)
        or not uids
        or not all(isinstance(uid, str) and UID_RE.match(uid) for uid in uids)
        or len(set(uids)) != len(uids)
    ):
        raise PackagingError(
            f"{label}: study_uids must be a nonempty list of unique UIDs"
        )
    partition = document.get("partition", DEFAULT_PARTITION)
    if not isinstance(partition, str) or not PARTITION_RE.match(partition):
        raise PackagingError(f"{label}: partition must be a simple name")
    for key in ("source", "note"):
        if key in document and not isinstance(document[key], str):
            raise PackagingError(f"{label}: {key} must be a string")
    return {"partition": partition, "study_uids": list(uids)}


def non_python_reason(name: str) -> str:
    lowered = name.lower()
    suffix = Path(lowered).suffix
    if suffix in CACHE_SUFFIXES:
        return "cache_file"
    if (
        lowered.startswith(CREDENTIAL_PREFIXES)
        or suffix in CREDENTIAL_SUFFIXES
        or "credential" in lowered
        or lowered == "kaggle.json"
    ):
        return "credential_name"
    if suffix in ARCHIVE_SUFFIXES:
        return "archive"
    return "non_python_file"


def check_name(dest: str, role: str) -> None:
    """Name-level refusals for one bundle path."""
    path = PurePosixPath(dest)
    lowered = path.name.lower()
    suffix = path.suffix.lower()
    if (
        lowered.startswith(CREDENTIAL_PREFIXES)
        or suffix in CREDENTIAL_SUFFIXES
        or "credential" in lowered
        or lowered == "kaggle.json"
    ):
        raise PackagingError(f"{dest}: credential-like file name")
    if suffix in PICKLE_SUFFIXES:
        raise PackagingError(f"{dest}: pickle or model artifact ({suffix}) is refused")
    if role in PYTHON_ROLES:
        if suffix != ".py":
            raise PackagingError(f"{dest}: only .py files are shipped as source")
        bad = [part for part in path.parts[:-1] if part in FORBIDDEN_COMPONENTS]
        if bad:
            raise PackagingError(f"{dest}: path component {bad[0]!r} is never shipped")
    elif role == "memory":
        if any(part.startswith(".") for part in path.parts):
            raise PackagingError(f"{dest}: hidden file in the memory; remove it first")
        if lowered in TEACHING_SOURCE_NAMES:
            raise PackagingError(
                f"{dest}: teaching labels must not travel with inference memory"
            )
        if suffix in IMAGE_DATA_SUFFIXES:
            raise PackagingError(f"{dest}: study image data is not part of the memory")
    elif role == "config":
        if dest != SELECTION_DEST:
            raise PackagingError(f"{dest}: unknown config file")
    elif role == "navigation":
        if dest not in {"navigation/" + name for name in NAVIGATION_FILES}:
            raise PackagingError(f"{dest}: unknown navigation file")
    else:
        raise PackagingError(f"{dest}: unknown role {role!r}")


def inspect_payload(
    dest: str, role: str, opener: Opener
) -> tuple[str, int, list[str], PythonFacts | None]:
    """Every content check for one file as stored: the same call builds and verifies."""
    check_name(dest, role)
    keep = role in PYTHON_ROLES or role == "config"
    with opener() as reader:
        digest, size, kept = hash_and_scan(reader, dest, keep)
    warnings: list[str] = []
    facts: PythonFacts | None = None
    if role in PYTHON_ROLES:
        assert kept is not None
        facts = inspect_python(dest, kept)
        warnings = list(facts.warnings)
    elif role in ("memory", "navigation"):
        check_container(PurePosixPath(dest).suffix.lower(), opener, dest)
    elif role == "config":
        assert kept is not None
        validate_selection_bytes(kept, dest)
    return digest, size, warnings, facts


# ---------------------------------------------------------------------------------------------
# Collecting what goes in
# ---------------------------------------------------------------------------------------------


def _walk_source(
    directory: Path, root: Path, files: list[Path], excluded: list[dict[str, str]]
) -> None:
    with os.scandir(directory) as scan:
        entries = sorted(scan, key=lambda entry: entry.name)
    for entry in entries:
        path = Path(entry.path)
        relative = path.relative_to(root).as_posix()
        is_dir = entry.is_dir(follow_symlinks=False)
        if entry.name in EXCLUDED_DIR_NAMES and (is_dir or entry.is_symlink()):
            excluded.append({"path": relative + "/", "reason": "excluded_directory"})
        elif entry.is_symlink():
            raise PackagingError(f"unsafe symlink: {relative}")
        elif is_dir:
            _walk_source(path, root, files, excluded)
        elif not entry.is_file(follow_symlinks=False):
            raise PackagingError(f"not a regular file: {relative}")
        elif entry.name.endswith(".py"):
            files.append(path)
        else:
            excluded.append({"path": relative, "reason": non_python_reason(entry.name)})


def refuse_symlink_components(root: Path, relative: PurePosixPath) -> Path:
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise PackagingError(f"unsafe symlink: {current}")
    return current


def scan_source(
    root: Path, extra_scripts: Sequence[str]
) -> tuple[list[tuple[Path, str, str]], list[dict[str, str]], list[str]]:
    """Every .py of src/knee plus the runner scripts, as (path, dest, role), the exclusions and scripts."""
    package = refuse_symlink_components(root, PurePosixPath(*SOURCE_PACKAGE))
    if not package.is_dir():
        raise PackagingError(f"source package is missing: {package}")
    if not (package / "__init__.py").is_file():
        raise PackagingError(f"source package has no __init__.py: {package}")
    found: list[Path] = []
    excluded: list[dict[str, str]] = []
    _walk_source(package, root, found, excluded)
    items = [
        (path, "source/" + path.relative_to(root).as_posix(), "source")
        for path in found
    ]
    scripts: list[str] = []
    for script in (RUNNER, *extra_scripts):
        relative = safe_relative(script)
        if (
            relative.parts[0] != "scripts"
            or len(relative.parts) != 2
            or relative.suffix != ".py"
        ):
            raise PackagingError(
                f"runtime script must be scripts/<name>.py: {script!r}"
            )
        path = refuse_symlink_components(root, relative)
        if not path.is_file():
            raise PackagingError(f"runtime script is missing: {script}")
        if script not in scripts:
            scripts.append(script)
            items.append((path, "source/" + relative.as_posix(), "runtime_script"))
    return items, sorted(excluded, key=lambda item: item["path"]), scripts


def _walk_memory(directory: Path, base: Path, out: list[tuple[Path, str]]) -> None:
    with os.scandir(directory) as scan:
        entries = sorted(scan, key=lambda entry: entry.name)
    for entry in entries:
        path = Path(entry.path)
        relative = path.relative_to(base).as_posix()
        if entry.is_symlink():
            raise PackagingError(f"unsafe symlink in the memory: {relative}")
        if entry.is_dir(follow_symlinks=False):
            _walk_memory(path, base, out)
        elif entry.is_file(follow_symlinks=False):
            out.append((path, "memory/" + relative))
        else:
            raise PackagingError(f"not a regular file in the memory: {relative}")


def plan_memory(memory: Path) -> tuple[list[tuple[Path, str, str]], str, str]:
    """The memory as (path, dest, 'memory') items, its layout, and the entry the wrappers pass on."""
    if memory.is_symlink():
        raise PackagingError(
            f"unsafe symlink: the memory argument is a symlink: {memory}"
        )
    found: list[tuple[Path, str]] = []
    if memory.is_file():
        found.append((memory, f"memory/{memory.name}"))
        layout, entry = "file", f"memory/{memory.name}"
    elif memory.is_dir():
        _walk_memory(memory, memory, found)
        layout, entry = "directory", "memory"
    else:
        raise PackagingError(f"memory not found: {memory}")
    if not found:
        raise PackagingError("memory holds no files")
    for _, dest in found:
        safe_relative(dest)
    return [(path, dest, "memory") for path, dest in found], layout, entry


def plan_navigation(
    navigation: Path,
) -> tuple[list[tuple[Path, str, str]], dict[str, Any]]:
    """Ship exactly one validated numerical artifact, never training payloads."""
    from knee.diagnosis.som_navigation import load_navigation

    if navigation.is_symlink() or not navigation.is_dir():
        raise PackagingError("navigation must be a plain artifact directory")
    paths = [navigation / name for name in NAVIGATION_FILES]
    before = {path.name: sha256_file(path) for path in paths}
    try:
        model = load_navigation(navigation)
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise PackagingError(f"invalid navigation artifact: {error}") from error
    if {path.name: sha256_file(path) for path in paths} != before:
        raise PackagingError("navigation changed during validation")
    metadata = {
        "schema": NAVIGATION_SCHEMA,
        "entry": "navigation",
        "files": {
            name: {"sha256": before[name][0], "bytes": before[name][1]}
            for name in NAVIGATION_FILES
        },
        "labels": list(model.architecture["labels"]),
        "specialists": [group["name"] for group in model.architecture["groups"]],
        "feature_count": model.architecture["feature_count"],
        "parameter_count": model.manifest["parameter_count"],
    }
    return [(path, "navigation/" + path.name, "navigation") for path in paths], metadata


def _object_without_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """A JSON object that repeats a key is ambiguous (which `schema` counts?), so it is refused."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _read_memory_document(path: Path, name: str) -> Any:
    """Parse one whole memory JSON file (plain, .gz or .xz); nothing is read from a prefix."""
    try:
        with ExitStack() as stack:
            reader = stack.enter_context(open_regular(path))
            if name.endswith(".xz"):
                handle: IO[bytes] = stack.enter_context(lzma.open(reader, "rb"))
            elif name.endswith(".gz"):
                handle = stack.enter_context(gzip.open(reader, "rb"))
            else:
                handle = reader
            data = handle.read()
        return json.loads(
            data.decode("utf-8"), object_pairs_hook=_object_without_duplicate_keys
        )
    except PackagingError:
        raise
    except (lzma.LZMAError, OSError, EOFError, UnicodeDecodeError, ValueError) as exc:
        raise PackagingError(f"memory file {name} is not readable JSON: {exc}") from exc


def detect_memory_schema(items: Sequence[tuple[Path, str, str]], layout: str) -> str:
    """The top-level JSON file whose own top-level `schema` is exactly knee.squint-memory/v1.

    Every candidate is parsed whole, so a large `cases` array that sorts before `schema` is fine, and a
    schema string nested anywhere else is not a declaration. A legacy store is named and refused.
    """
    legacy = False
    seen: list[str] = []
    for path, dest, _ in items:
        relative = dest[len("memory/") :]
        if layout == "directory" and "/" in relative:
            continue
        lowered = relative.lower()
        if not lowered.endswith((".json", ".json.xz", ".json.gz")):
            continue
        document = _read_memory_document(path, lowered)
        declared = document.get("schema") if isinstance(document, dict) else None
        if declared == MEMORY_SCHEMA:
            return relative
        if declared in LEGACY_MEMORY_SCHEMAS:
            legacy = True
        seen.append(f"{relative}: {declared!r}")
    if legacy:
        raise PackagingError(
            f"the memory is a legacy diagnostic store; the squint route needs {MEMORY_SCHEMA}"
        )
    found = "; ".join(seen) if seen else "no top-level JSON file"
    raise PackagingError(
        f"no top-level JSON file of the memory has top-level schema == {MEMORY_SCHEMA} ({found})"
    )


def check_collisions(items: Sequence[tuple[Any, str, str]]) -> None:
    seen: dict[str, str] = {}
    for _, dest, _ in items:
        key = dest.casefold()
        if key in seen:
            raise PackagingError(
                f"collision: {seen[key]!r} and {dest!r} map to one path"
            )
        seen[key] = dest
    for _, dest, _ in items:
        parts = PurePosixPath(dest).parts
        for end in range(1, len(parts)):
            if "/".join(parts[:end]).casefold() in seen:
                raise PackagingError(
                    f"collision: a file is also a directory of {dest!r}"
                )


def check_disjoint(output: Path, others: dict[str, Path]) -> None:
    for name, other in others.items():
        if (
            output == other
            or output.is_relative_to(other)
            or other.is_relative_to(output)
        ):
            raise PackagingError(
                f"output directory overlaps the {name}: {output} vs {other}"
            )


def optional_hash(path: Path) -> str | None:
    try:
        return sha256_file(path)[0]
    except PackagingError:
        return None


def plan_all(
    memory: Path | None,
    root: Path | None,
    extra_scripts: Sequence[str],
    selection: Path | None,
    *,
    roles: frozenset[str] = ROLES,
    navigation: Path | None = None,
) -> dict[str, Any]:
    """Plan and inspect every file of the requested roles; the same path serves build and comparison."""
    items: list[tuple[Path, str, str]] = []
    excluded: list[dict[str, str]] = []
    scripts: list[str] = []
    layout = entry = schema_file = None
    navigation_metadata = None
    if root is not None and roles & PYTHON_ROLES:
        found, excluded, scripts = scan_source(root, extra_scripts)
        items += found
    if memory is not None and "memory" in roles:
        found_memory, layout, entry = plan_memory(memory)
        schema_file = detect_memory_schema(found_memory, layout)
        items += found_memory
    if selection is not None and "config" in roles:
        items.append((selection, SELECTION_DEST, "config"))
    if navigation is not None and "navigation" in roles:
        found_navigation, navigation_metadata = plan_navigation(navigation)
        items += found_navigation
    check_collisions(items)
    payloads: list[Planned] = []
    warnings: set[str] = set()
    facts_by_dest: dict[str, PythonFacts] = {}
    for path, dest, role in items:
        digest, size, found_warnings, facts = inspect_payload(
            dest, role, path_opener(path)
        )
        warnings.update(found_warnings)
        if facts is not None:
            facts_by_dest[dest] = facts
        payloads.append(Planned(path, dest, role, digest, size))
    require_closed_imports(facts_by_dest)
    return {
        "payloads": sorted(payloads, key=lambda item: item.dest),
        "excluded": excluded,
        "scripts": scripts,
        "layout": layout,
        "entry": entry,
        "schema_file": schema_file,
        "warnings": sorted(warnings),
        "navigation": navigation_metadata,
    }


def entries_of(payloads: Sequence[Planned]) -> list[dict[str, Any]]:
    return [
        {
            "path": item.dest,
            "role": item.role,
            "sha256": item.sha256,
            "bytes": item.bytes,
        }
        for item in sorted(payloads, key=lambda planned: planned.dest)
    ]


def memory_block(
    entries: Sequence[dict[str, Any]], layout: str, entry: str, schema_file: str
) -> dict[str, Any]:
    memory = [item for item in entries if item["role"] == "memory"]
    return {
        "schema": MEMORY_SCHEMA,
        "schema_declared_in": schema_file,
        "layout": layout,
        "entry": entry,
        "files": len(memory),
        "bytes": sum(item["bytes"] for item in memory),
        "tree_sha256": tree_id(memory),
    }


def selection_block(
    entries: Sequence[dict[str, Any]], data: bytes | None
) -> dict[str, Any] | None:
    config = [item for item in entries if item["role"] == "config"]
    if not config:
        return None
    assert data is not None
    summary = validate_selection_bytes(data, SELECTION_DEST)
    return {
        "path": SELECTION_DEST,
        "sha256": config[0]["sha256"],
        "partition": summary["partition"],
        "study_count": len(summary["study_uids"]),
    }


# ---------------------------------------------------------------------------------------------
# The build
# ---------------------------------------------------------------------------------------------


def _tar_info(name: str, size: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.size = size
    info.mtime = 0
    info.mode = 0o644
    info.uid = info.gid = 0
    info.uname = info.gname = ""
    info.type = tarfile.REGTYPE
    return info


def write_tar(path: Path, payloads: Sequence[Planned], manifest_bytes: bytes) -> None:
    members: list[tuple[str, Planned | None]] = [(item.dest, item) for item in payloads]
    members.append((MANIFEST_NAME, None))
    members.sort(key=lambda pair: pair[0])
    with tarfile.open(
        path, "w", format=tarfile.PAX_FORMAT, encoding="utf-8"
    ) as archive:
        for name, item in members:
            if item is None:
                archive.addfile(
                    _tar_info(name, len(manifest_bytes)), io.BytesIO(manifest_bytes)
                )
                continue
            assert item.source is not None
            with open_regular(item.source) as reader:
                hashing = _HashingReader(reader)
                archive.addfile(_tar_info(name, item.bytes), hashing)  # type: ignore[arg-type]
            if hashing.digest.hexdigest() != item.sha256 or hashing.size != item.bytes:
                raise PackagingError(
                    f"stale_source_input: {item.source} changed while it was packaged"
                )


def metadata_document() -> dict[str, Any]:
    return {
        "id": DATASET_ID,
        "licenses": [{"name": "other"}],
        "title": DATASET_ID.split("/", 1)[1].replace("-", " "),
    }


def build_staging(
    memory: Path,
    output: Path,
    root: Path,
    extra_scripts: Sequence[str] = (),
    selection: Path | None = None,
    navigation: Path | None = None,
) -> dict[str, Any]:
    """Build the staging into a fresh `output`; on any failure nothing is left behind."""
    root = Path(os.path.realpath(root))
    memory_abs = Path(os.path.abspath(memory))
    output_abs = Path(os.path.abspath(output))
    if os.path.lexists(output_abs):
        raise PackagingError(
            f"output already exists (a fresh directory is required): {output_abs}"
        )
    output_real = Path(os.path.realpath(output_abs))
    check_disjoint(
        output_real,
        {"source root": root, "memory": Path(os.path.realpath(memory_abs))},
    )
    if selection is not None:
        selection = Path(os.path.abspath(selection))
    plan = plan_all(memory_abs, root, extra_scripts, selection, navigation=navigation)
    payloads: list[Planned] = plan["payloads"]
    paths = {item.dest for item in payloads}
    for required in REQUIRED_PATHS:
        if required not in paths:
            raise PackagingError(
                f"the source lacks {required}; build from the integrated tree"
            )
    entries = entries_of(payloads)
    selection_bytes = selection.read_bytes() if selection is not None else None
    inner = {
        "schema": MANIFEST_SCHEMA,
        "bundle_id": tree_id(entries),
        "dataset_id": DATASET_ID,
        "entrypoint": ENTRYPOINT,
        "pythonpath": list(PYTHONPATH_ENTRIES),
        "memory": memory_block(
            entries, plan["layout"], plan["entry"], plan["schema_file"]
        ),
        "scaling_selection": selection_block(entries, selection_bytes),
        "source": {
            "package": "/".join(SOURCE_PACKAGE),
            "python_files": sum(1 for item in entries if item["role"] == "source"),
            "runtime_scripts": plan["scripts"],
            "pyproject_sha256": optional_hash(root / "pyproject.toml"),
            "uv_lock_sha256": optional_hash(root / "uv.lock"),
            "excluded": plan["excluded"],
        },
        "scope": (
            "src/knee/**/*.py, the runtime scripts, the supplied memory, an optional scaling "
            "selection and optional three-file numerical navigation artifact only; nothing else of the checkout"
        ),
        "warnings": plan["warnings"],
        "files": entries,
    }
    if plan["navigation"] is not None:
        inner["navigation"] = plan["navigation"]
    output_real.mkdir(parents=True, exist_ok=False)
    try:
        tar_part = output_real / (TAR_NAME + ".part")
        write_tar(tar_part, payloads, dumps(inner).encode("utf-8"))
        tar_path = output_real / TAR_NAME
        os.replace(tar_part, tar_path)
        tar_digest, tar_size = sha256_file(tar_path)
        outer = dict(inner)
        outer["tar"] = {"name": TAR_NAME, "sha256": tar_digest, "bytes": tar_size}
        (output_real / MANIFEST_NAME).write_text(dumps(outer), encoding="utf-8")
        (output_real / METADATA_NAME).write_text(
            dumps(metadata_document()), encoding="utf-8"
        )
        summary = verify_staging(output_real)
    except BaseException:
        shutil.rmtree(output_real, ignore_errors=True)
        raise
    return {
        **summary,
        "output": str(output_real),
        "excluded_count": len(plan["excluded"]),
        "warnings": plan["warnings"],
    }


# ---------------------------------------------------------------------------------------------
# Verification of a staging directory
# ---------------------------------------------------------------------------------------------


def _read_json(path: Path, problems: list[str]) -> Any:
    try:
        with open_regular(path) as reader:
            return json.loads(reader.read().decode("utf-8"))
    except (PackagingError, UnicodeDecodeError, ValueError) as exc:
        problems.append(f"{path.name}: {exc}")
        return None


def _clean_entries(
    manifest: dict[str, Any], problems: list[str]
) -> list[dict[str, Any]]:
    entries = manifest.get("files")
    if not isinstance(entries, list):
        problems.append("manifest files are missing")
        return []
    clean = []
    for entry in entries:
        try:
            safe_relative(entry["path"])
            if (
                not SHA256_RE.match(entry["sha256"])
                or entry["role"] not in ROLES
                or not isinstance(entry["bytes"], int)
                or entry["bytes"] < 0
            ):
                raise KeyError("sha256/role/bytes")
        except (KeyError, TypeError, PackagingError) as exc:
            problems.append(f"manifest entry is malformed: {entry!r} ({exc})")
            continue
        clean.append(entry)
    if len({entry["path"] for entry in clean}) != len(clean):
        problems.append("manifest lists a path twice")
    return clean


def _verify_tar(
    tar_path: Path, expected: dict[str, dict[str, Any]], problems: list[str]
) -> tuple[dict[str, Any] | None, dict[str, PythonFacts]]:
    seen: list[str] = []
    inner: dict[str, Any] | None = None
    facts_by_dest: dict[str, PythonFacts] = {}
    with ExitStack() as stack:
        try:
            archive = stack.enter_context(tarfile.open(tar_path, "r:"))
        except (tarfile.TarError, OSError) as exc:
            problems.append(f"{TAR_NAME} cannot be opened: {exc}")
            return None, facts_by_dest
        for member in archive:
            name = member.name
            seen.append(name)
            try:
                safe_relative(name)
            except PackagingError as exc:
                problems.append(str(exc))
                continue
            if not member.isreg():
                problems.append(f"tar member is not a regular file: {name}")
                continue
            fixed = (
                member.mode,
                member.uid,
                member.gid,
                member.mtime,
                member.uname,
                member.gname,
            )
            if fixed != TAR_FIXED:
                problems.append(f"tar member has non-deterministic metadata: {name}")
            handle = archive.extractfile(member)
            if handle is None:
                problems.append(f"tar member cannot be read: {name}")
                continue
            if name == MANIFEST_NAME:
                with handle:
                    data = handle.read()
                try:
                    inner = json.loads(data.decode("utf-8"))
                except (UnicodeDecodeError, ValueError) as exc:
                    problems.append(f"inner manifest is not JSON: {exc}")
                else:
                    if data != dumps(inner).encode("utf-8"):
                        problems.append("inner manifest is not in canonical form")
                continue
            handle.close()
            entry = expected.get(name)
            if entry is None:
                problems.append(f"tar member is not in the manifest: {name}")
                continue
            try:
                digest, size, _, facts = inspect_payload(
                    name,
                    entry["role"],
                    lambda m=member: archive.extractfile(m),  # type: ignore[arg-type,return-value]
                )
            except PackagingError as exc:
                problems.append(str(exc))
                continue
            if facts is not None:
                facts_by_dest[name] = facts
            if digest != entry["sha256"] or size != entry["bytes"]:
                problems.append(f"hash or size mismatch in the tar: {name}")
    if seen != sorted(seen):
        problems.append("tar members are not in sorted order")
    if len(set(seen)) != len(seen):
        problems.append("tar holds a member twice")
    for name in sorted(set(expected) - set(seen)):
        problems.append(f"manifest file is missing from the tar: {name}")
    if MANIFEST_NAME not in seen:
        problems.append("tar has no inner RUNTIME_MANIFEST.json")
    problems.extend(import_problems(facts_by_dest))
    return inner, facts_by_dest


def _check_manifest(
    outer: dict[str, Any], clean: list[dict[str, Any]], problems: list[str]
) -> None:
    if outer.get("schema") != MANIFEST_SCHEMA:
        problems.append("manifest schema is wrong")
    if outer.get("dataset_id") != DATASET_ID:
        problems.append("manifest dataset_id is wrong")
    if (
        outer.get("entrypoint") != ENTRYPOINT
        or outer.get("pythonpath") != PYTHONPATH_ENTRIES
    ):
        problems.append("manifest entrypoint or pythonpath is wrong")
    if tree_id(clean) != outer.get("bundle_id"):
        problems.append("manifest bundle_id is not the hash of its files")
    paths = {entry["path"] for entry in clean}
    for required in REQUIRED_PATHS:
        if required not in paths:
            problems.append(f"manifest lacks required file {required}")
    memory = outer.get("memory")
    if not isinstance(memory, dict) or memory.get("schema") != MEMORY_SCHEMA:
        problems.append("manifest memory block is wrong")
    else:
        recomputed = memory_block(
            clean,
            str(memory.get("layout")),
            str(memory.get("entry")),
            str(memory.get("schema_declared_in")),
        )
        if recomputed != memory or memory.get("files", 0) < 1:
            problems.append("manifest memory block does not match its files")
        if memory.get("entry") not in {
            "memory",
            *(p for p in paths if p.startswith("memory/")),
        }:
            problems.append("manifest memory entry is not in the bundle")
    source = outer.get("source")
    if not isinstance(source, dict) or source.get("python_files") != sum(
        1 for entry in clean if entry["role"] == "source"
    ):
        problems.append("manifest source block does not match its files")
    config = [entry for entry in clean if entry["role"] == "config"]
    selection = outer.get("scaling_selection")
    if bool(config) != (selection is not None):
        problems.append("manifest scaling_selection does not match its config files")
    elif selection is not None and (
        selection.get("path") != SELECTION_DEST
        or selection.get("sha256") != config[0]["sha256"]
    ):
        problems.append("manifest scaling_selection does not match its config file")
    navigation_entries = {
        PurePosixPath(row["path"]).name: row
        for row in clean
        if row["role"] == "navigation"
    }
    navigation = outer.get("navigation")
    if bool(navigation_entries) != (navigation is not None):
        problems.append("manifest navigation does not match its files")
    elif navigation is not None:
        expected_files = {
            name: {"sha256": row["sha256"], "bytes": row["bytes"]}
            for name, row in navigation_entries.items()
        }
        if (
            not isinstance(navigation, dict)
            or navigation.get("schema") != NAVIGATION_SCHEMA
            or navigation.get("entry") != "navigation"
            or set(navigation_entries) != set(NAVIGATION_FILES)
            or any(
                row["path"] != "navigation/" + name
                for name, row in navigation_entries.items()
            )
            or navigation.get("files") != expected_files
        ):
            problems.append("manifest navigation block is invalid or unpinned")


def _compare_sources(
    clean: list[dict[str, Any]],
    memory: Path | None,
    root: Path | None,
    extra_scripts: Sequence[str],
    selection: Path | None,
    problems: list[str],
    navigation: Path | None = None,
) -> list[str]:
    compared: list[str] = []
    wanted: set[str] = set()
    if root is not None:
        wanted |= PYTHON_ROLES
    if memory is not None:
        wanted.add("memory")
    if selection is not None:
        wanted.add("config")
    if navigation is not None:
        wanted.add("navigation")
    if not wanted:
        return compared
    plan = plan_all(
        memory,
        root,
        extra_scripts,
        selection,
        roles=frozenset(wanted),
        navigation=navigation,
    )
    fresh = {item.dest: (item.sha256, item.bytes) for item in plan["payloads"]}
    stored = {
        entry["path"]: (entry["sha256"], entry["bytes"])
        for entry in clean
        if entry["role"] in wanted
    }
    for path in sorted(set(fresh) | set(stored)):
        if fresh.get(path) != stored.get(path):
            problems.append(f"stale or different from its source: {path}")
    compared = sorted(wanted)
    return compared


def verify_staging(
    output_dir: Path,
    *,
    memory: Path | None = None,
    root: Path | None = None,
    extra_scripts: Sequence[str] = (),
    selection: Path | None = None,
    navigation: Path | None = None,
) -> dict[str, Any]:
    """Re-read a staging: file set, metadata, tar, hashes, secrets, pickle; optionally against its sources."""
    output = Path(os.path.abspath(output_dir))
    root = Path(os.path.realpath(root)) if root is not None else None
    memory = Path(os.path.abspath(memory)) if memory is not None else None
    selection = Path(os.path.abspath(selection)) if selection is not None else None
    problems: list[str] = []
    if output.is_symlink() or not output.is_dir():
        raise PackagingError(f"staging is not a plain directory: {output}")
    present = sorted(entry.name for entry in os.scandir(output))
    if present != sorted(STAGING_FILES):
        raise PackagingError(
            f"staging must hold exactly {sorted(STAGING_FILES)}, found {present}"
        )
    for name in STAGING_FILES:
        if not stat.S_ISREG(os.lstat(output / name).st_mode):
            raise PackagingError(f"staging entry is not a regular file: {name}")
    expected_meta = dumps(metadata_document()).encode("utf-8")
    if (output / METADATA_NAME).read_bytes() != expected_meta:
        problems.append("dataset-metadata.json is not the expected canonical document")
    outer = _read_json(output / MANIFEST_NAME, problems)
    if not isinstance(outer, dict):
        raise PackagingError(
            "staging does not verify:\n- "
            + "\n- ".join(problems or ["manifest is not an object"])
        )
    clean = _clean_entries(outer, problems)
    _check_manifest(outer, clean, problems)
    tar_record = outer.get("tar")
    digest, size = sha256_file(output / TAR_NAME)
    if not isinstance(tar_record, dict) or tar_record != {
        "name": TAR_NAME,
        "sha256": digest,
        "bytes": size,
    }:
        problems.append("manifest tar record does not match the tar file")
    inner, facts_by_dest = _verify_tar(
        output / TAR_NAME, {entry["path"]: entry for entry in clean}, problems
    )
    if inner is not None and inner != {k: v for k, v in outer.items() if k != "tar"}:
        problems.append("inner manifest differs from the outer manifest")
    compared = _compare_sources(
        clean, memory, root, extra_scripts, selection, problems, navigation
    )
    if problems:
        raise PackagingError("staging does not verify:\n- " + "\n- ".join(problems))
    return {
        "bundle_id": outer["bundle_id"],
        "dataset_id": outer["dataset_id"],
        "tar_sha256": digest,
        "tar_bytes": size,
        "file_count": len(clean),
        "memory": outer["memory"],
        "scaling_selection": outer["scaling_selection"],
        "compared_with_sources": compared,
        "source_checks": {
            "python_grammar": "{}.{}".format(*RUNTIME_PYTHON),
            "python_files": len(facts_by_dest),
            "package_imports": sum(len(f.imports) for f in facts_by_dest.values()),
        },
        "dataset_dir": str(output),
    }


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--memory",
        type=Path,
        help="squint memory (directory or single file), packaged byte for byte",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="fresh staging directory (or an existing one with --verify)",
    )
    parser.add_argument(
        "--root-source",
        type=Path,
        default=None,
        help="repository root (default: the repository holding this script)",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="re-read the staging independently (and against its sources)",
    )
    parser.add_argument(
        "--extra-script",
        action="append",
        default=[],
        dest="extra_scripts",
        help="another scripts/<name>.py the runner needs",
    )
    parser.add_argument(
        "--navigation",
        type=Path,
        default=None,
        help="optional numerical learned-navigation artifact directory (three files only)",
    )
    parser.add_argument(
        "--scaling-selection",
        type=Path,
        default=None,
        help="optional knee.squint-scaling-selection/v1 UID list for the scaling notebook",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.verify and os.path.lexists(args.output):
            result = verify_staging(
                args.output,
                memory=args.memory,
                root=args.root_source,
                extra_scripts=tuple(args.extra_scripts),
                selection=args.scaling_selection,
                navigation=args.navigation,
            )
        else:
            if args.memory is None:
                parser.error("--memory is required to build a staging")
            root = args.root_source if args.root_source is not None else DEFAULT_ROOT
            result = build_staging(
                args.memory,
                args.output,
                root,
                tuple(args.extra_scripts),
                args.scaling_selection,
                args.navigation,
            )
            if args.verify:
                result["verified"] = verify_staging(
                    result["output"],
                    memory=args.memory,
                    root=root,
                    extra_scripts=tuple(args.extra_scripts),
                    selection=args.scaling_selection,
                    navigation=args.navigation,
                )
    except PackagingError as exc:
        print(f"package_squint_kaggle: refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
