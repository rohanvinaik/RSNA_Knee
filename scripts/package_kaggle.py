#!/usr/bin/env python3
"""Package this project's source and a supplied immutable diagnostic memory for an offline Kaggle notebook.

One fresh output directory is written, holding two things Kaggle takes separately:

    <output>/dataset/   uploaded as a Kaggle dataset
        source/scripts/run_interiors.py      the one runtime entry point (plus any --runtime-script)
        source/src/knee/**/*.py              every current Python file of the package
        memory/manifest.json, memory/profiles.npz   the caller's memory, byte for byte
        wheelhouse/*.whl, requirements.txt   only when supplied; installed with --no-index
        bundle-manifest.json                 every shipped file by path, sha256 and size
        dataset-metadata.json
    <output>/kernel/    pushed as a Kaggle notebook
        rsna-knee-offline.ipynb              locate and verify the mounted bundle, optionally
                                             install the wheelhouse offline, then ONE
                                             run_interiors.py invocation
        kernel-metadata.json                 internet off, no GPU, dataset and competition attached

What it does not do: it never reads the network, downloads a package, edits the source or the memory,
runs the pipeline, invents a probability policy, or writes a submission. The run's argument vector is
the caller's, taken verbatim; the notebook only substitutes the placeholders `{source}`, `{memory}`,
`{working}`, `{input}` and `{bundle}` for the paths Kaggle mounts. If run_interiors.py exits non-zero
the notebook raises; there is no fallback output.

Not packaged, by construction: anything outside `src/knee` and the runtime scripts (so no `.git`,
archives, `tests/`, `data/`, study data, reading products, caches or credentials). Inside `src/knee`
only `.py` files are copied; every other file or directory met is listed under `excluded` in the
manifest with its reason, so nothing is dropped silently.

CLI:
    package_kaggle.py build --source-root R --memory-dir M --output-dir O \\
        --dataset-id owner/slug --kernel-id owner/slug --competition-source SLUG \\
        --run-argv-json '["--split","test","--diagnostic-mode","infer","--diagnostic-memory","{memory}","--diagnostic-output","{working}/diagnostic"]' \\
        [--wheelhouse DIR] [--requirements FILE] [--runtime-script scripts/x.py ...]
    package_kaggle.py verify O

Exit 0 on success (a JSON summary on stdout), 2 on a refusal (the reason on stderr; no output left).

API: `PackageSpec`, `build_bundle(spec) -> dict`, `validate_bundle(output_dir) -> dict`,
`PackagingError`. Everything is standard library.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import IO, Any

BUNDLE_SCHEMA = "rsna-knee-kaggle-bundle/v1"
MANIFEST_NAME = "bundle-manifest.json"
DATASET_METADATA_NAME = "dataset-metadata.json"
KERNEL_METADATA_NAME = "kernel-metadata.json"
NOTEBOOK_NAME = "rsna-knee-offline.ipynb"
DEFAULT_RUN_SCRIPT = "scripts/run_interiors.py"
SOURCE_PACKAGE = ("src", "knee")
MEMORY_FILES = ("manifest.json", "profiles.npz")
REQUIREMENTS_DEST = "requirements.txt"
UNLISTED_TOP_LEVEL = frozenset({MANIFEST_NAME, DATASET_METADATA_NAME})
REQUIRED_PATHS = (
    "source/scripts/run_interiors.py",
    "source/src/knee/__init__.py",
    "memory/manifest.json",
    "memory/profiles.npz",
)
ROLES = frozenset({"runtime_script", "source", "memory", "wheelhouse", "requirements"})
ALLOWED_PLACEHOLDERS = ("bundle", "input", "memory", "source", "working")
PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
OWNER_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
HASH_OPTION_RE = re.compile(r"^--hash=sha256:[0-9a-f]{64}$")
REQUIREMENT_RE = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._-]*(\[[A-Za-z0-9,._-]+\])?"
    r"((===|==|~=|!=|<=|>=|<|>)[^\s;,@]+)?"
    r"(,(===|==|~=|!=|<=|>=|<|>)[^\s;,@]+)*;?$"
)
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
        "archive",
        "archive2",
        "tests",
    }
)
CACHE_SUFFIXES = frozenset({".pyc", ".pyo", ".nbc", ".nbi"})
ARCHIVE_SUFFIXES = frozenset(
    {".zip", ".tar", ".tgz", ".gz", ".bz2", ".xz", ".7z", ".rar", ".whl"}
)
CREDENTIAL_SUFFIXES = frozenset({".pem", ".key", ".p12", ".pfx", ".token", ".env"})
CREDENTIAL_PREFIXES = (".env", ".netrc", "id_rsa", "id_ed25519", "id_ecdsa")
FORBIDDEN_NOTEBOOK_WORDS = (
    "urlopen",
    "urllib",
    "requests",
    "curl ",
    "wget",
    "--index-url",
    "--extra-index-url",
    "pip download",
    "git clone",
    "open('submission.csv', 'w')",
)
ZIP_MAGICS = (b"PK\x03\x04", b"PK\x05\x06")


class PackagingError(Exception):
    """A refusal: nothing was built, or the bundle does not verify."""


@dataclass(frozen=True)
class PlannedFile:
    """One file to copy: where it is, where it goes in the dataset, and its role."""

    source: Path
    dest: str
    role: str


@dataclass(frozen=True)
class PackageSpec:
    """Everything the caller decides. Nothing here has a default that guesses."""

    source_root: Path
    memory_dir: Path
    output_dir: Path
    dataset_id: str
    kernel_id: str
    competition_sources: tuple[str, ...]
    run_argv: tuple[str, ...]
    wheelhouse: Path | None = None
    requirements: Path | None = None
    runtime_scripts: tuple[str, ...] = ()
    input_root: str = "/kaggle/input"
    working_root: str = "/kaggle/working"


# ---------------------------------------------------------------------------------------------
# Files: safe opening, hashing, copying
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
        for block in iter(lambda: reader.read(1 << 20), b""):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def copy_hashed(source: Path, destination: Path) -> tuple[str, int]:
    """Copy by streaming, hashing the bytes written; an existing destination is a collision."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    with open_regular(source) as reader:
        try:
            writer = destination.open("xb")
        except FileExistsError as exc:
            raise PackagingError(f"collision at {destination}") from exc
        with writer:
            for block in iter(lambda: reader.read(1 << 20), b""):
                digest.update(block)
                size += len(block)
                writer.write(block)
    return digest.hexdigest(), size


def signature(path: Path) -> tuple[int, int]:
    info = os.lstat(path)
    return info.st_size, info.st_mtime_ns


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


def refuse_symlink_components(root: Path, relative: PurePosixPath) -> Path:
    """Walk root/relative component by component; any symlink on the way is refused."""
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise PackagingError(f"unsafe symlink: {current}")
    return current


def check_collisions(planned: Sequence[PlannedFile]) -> None:
    """Refuse two files for one bundle path (case-insensitively) or a file that is also a directory."""
    files: dict[str, str] = {}
    for item in planned:
        key = item.dest.casefold()
        if key in files:
            raise PackagingError(
                f"collision: {files[key]!r} and {item.dest!r} map to one bundle path"
            )
        files[key] = item.dest
    for item in planned:
        parts = PurePosixPath(item.dest).parts
        for end in range(1, len(parts)):
            prefix = "/".join(parts[:end]).casefold()
            if prefix in files:
                raise PackagingError(
                    f"collision: {files[prefix]!r} is a file and a directory of {item.dest!r}"
                )


# ---------------------------------------------------------------------------------------------
# Collecting what goes in
# ---------------------------------------------------------------------------------------------


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


def collect_source(
    root: Path, extra_scripts: Sequence[str]
) -> tuple[list[PlannedFile], list[dict[str, str]]]:
    """Every .py of src/knee plus the runtime scripts, as a plan, and what was left out and why."""
    package = refuse_symlink_components(root, PurePosixPath(*SOURCE_PACKAGE))
    if not package.is_dir():
        raise PackagingError(f"source package is missing: {package}")
    if not (package / "__init__.py").is_file():
        raise PackagingError(f"source package has no __init__.py: {package}")
    found: list[Path] = []
    excluded: list[dict[str, str]] = []
    _walk_source(package, root, found, excluded)
    planned = [
        PlannedFile(path, "source/" + path.relative_to(root).as_posix(), "source")
        for path in found
    ]
    for script in (DEFAULT_RUN_SCRIPT, *extra_scripts):
        relative = safe_relative(script)
        if (
            relative.parts[0] != "scripts"
            or len(relative.parts) < 2
            or relative.suffix != ".py"
        ):
            raise PackagingError(
                f"runtime script must be scripts/<name>.py: {script!r}"
            )
        path = refuse_symlink_components(root, relative)
        if not path.is_file():
            raise PackagingError(f"runtime script is missing: {script}")
        planned.append(
            PlannedFile(path, "source/" + relative.as_posix(), "runtime_script")
        )
    return planned, sorted(excluded, key=lambda item: item["path"])


def collect_memory(memory_dir: Path) -> list[PlannedFile]:
    """The memory is exactly manifest.json + profiles.npz; anything else, or less, is refused."""
    if memory_dir.is_symlink() or not memory_dir.is_dir():
        raise PackagingError(f"memory directory is not a plain directory: {memory_dir}")
    with os.scandir(memory_dir) as scan:
        names = sorted(entry.name for entry in scan)
    if names != sorted(MEMORY_FILES):
        raise PackagingError(
            f"memory must hold exactly {list(MEMORY_FILES)}, found {names}"
        )
    with open_regular(memory_dir / "manifest.json") as reader:
        try:
            document = json.loads(reader.read().decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise PackagingError(f"memory manifest.json is not JSON: {exc}") from exc
    if not isinstance(document, dict):
        raise PackagingError("memory manifest.json must hold a JSON object")
    if document.get("schema") != "knee.diagnostic-store/v1":
        raise PackagingError(
            "memory manifest.json is not a knee.diagnostic-store/v1 store"
        )
    archive = document.get("archive")
    if not isinstance(archive, dict) or archive.get("file") != "profiles.npz":
        raise PackagingError(
            "memory manifest.json must declare profiles.npz as its archive"
        )
    with open_regular(memory_dir / "profiles.npz") as reader:
        if reader.read(4) not in ZIP_MAGICS:
            raise PackagingError("memory profiles.npz is not a zip/npz file")
    return [
        PlannedFile(memory_dir / name, f"memory/{name}", "memory")
        for name in MEMORY_FILES
    ]


def _wheel_is_linux(name: str) -> bool:
    parts = name[: -len(".whl")].split("-")
    if len(parts) not in (5, 6):
        return False
    return all(tag == "any" or "linux" in tag for tag in parts[-1].split("."))


def collect_wheelhouse(wheelhouse: Path) -> list[PlannedFile]:
    if wheelhouse.is_symlink() or not wheelhouse.is_dir():
        raise PackagingError(f"wheelhouse is not a plain directory: {wheelhouse}")
    with os.scandir(wheelhouse) as scan:
        names = sorted(entry.name for entry in scan)
    if not names:
        raise PackagingError("wheelhouse is empty")
    planned = []
    for name in names:
        if not name.endswith(".whl"):
            raise PackagingError(f"wheelhouse holds a non-wheel entry: {name!r}")
        if not _wheel_is_linux(name):
            raise PackagingError(
                f"wheel is not a Linux (or pure-Python 'any') wheel: {name!r}"
            )
        with open_regular(wheelhouse / name) as reader:
            if reader.read(4) not in ZIP_MAGICS:
                raise PackagingError(f"wheel is not a zip file: {name!r}")
        planned.append(
            PlannedFile(wheelhouse / name, f"wheelhouse/{name}", "wheelhouse")
        )
    return planned


def validate_requirements(text: str) -> None:
    """Pinned names only (with optional --hash); anything that could reach a network is refused."""
    joined = text.replace("\\\r\n", " ").replace("\\\n", " ")
    for raw in joined.splitlines():
        line = re.sub(r"(^|\s)#.*$", "", raw).strip()
        if not line:
            continue
        if "://" in line or line.startswith(("git+", "file:")):
            raise PackagingError(
                f"requirements line names a URL or path, which is refused: {line!r}"
            )
        tokens = line.split()
        if tokens[0].startswith("-") or not REQUIREMENT_RE.match(tokens[0]):
            raise PackagingError(
                f"requirements line is not a plain requirement: {line!r}"
            )
        for token in tokens[1:]:
            if token.startswith("-") and not HASH_OPTION_RE.match(token):
                raise PackagingError(
                    f"requirements option is refused (only --hash=sha256:...): {token!r}"
                )
            if token == "@":
                raise PackagingError(
                    f"requirements direct reference is refused: {line!r}"
                )


def collect_requirements(requirements: Path) -> PlannedFile:
    with open_regular(requirements) as reader:
        data = reader.read((1 << 20) + 1)
    if len(data) > 1 << 20:
        raise PackagingError("requirements file is over 1 MiB")
    try:
        validate_requirements(data.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise PackagingError(f"requirements file is not UTF-8: {exc}") from exc
    return PlannedFile(requirements, REQUIREMENTS_DEST, "requirements")


# ---------------------------------------------------------------------------------------------
# Spec checks
# ---------------------------------------------------------------------------------------------


def split_id(identifier: str, what: str) -> tuple[str, str]:
    owner, _, slug = identifier.partition("/")
    if not OWNER_RE.match(owner) or not SLUG_RE.match(slug) or not 6 <= len(slug) <= 50:
        raise PackagingError(
            f"{what} must be owner/slug (slug: lowercase-with-hyphens, 6-50 chars): {identifier!r}"
        )
    return owner, slug


def validate_run_argv(argv: Sequence[str]) -> list[str]:
    """The caller's argv must be a non-empty list of strings; unknown {placeholders} are refused."""
    if not isinstance(argv, (list, tuple)) or not argv:
        raise PackagingError("run argv must be a non-empty list of strings")
    warnings: list[str] = []
    seen: set[str] = set()
    for token in argv:
        if not isinstance(token, str) or "\0" in token:
            raise PackagingError(f"run argv holds a non-string or NUL token: {token!r}")
        for name in PLACEHOLDER_RE.findall(token):
            if name not in ALLOWED_PLACEHOLDERS:
                raise PackagingError(
                    f"run argv placeholder {{{name}}} is unknown; allowed: {list(ALLOWED_PLACEHOLDERS)}"
                )
            seen.add(name)
    if "memory" not in seen:
        warnings.append(
            "run argv does not reference {memory}: the bundled memory will be unused"
        )
    return warnings


def check_disjoint(output: Path, others: dict[str, Path | None]) -> None:
    for name, other in others.items():
        if other is None:
            continue
        if (
            output == other
            or output.is_relative_to(other)
            or other.is_relative_to(output)
        ):
            raise PackagingError(
                f"output directory overlaps the {name}: {output} vs {other}"
            )


def tree_id(entries: Sequence[dict[str, Any]]) -> str:
    """The bundle's identity: its sorted (path, sha256) pairs. The notebook recomputes the same."""
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: item["path"]):
        digest.update(entry["path"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(entry["sha256"].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def dumps(document: object) -> str:
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


def title_of(slug: str) -> str:
    return slug.replace("-", " ")


# ---------------------------------------------------------------------------------------------
# The notebook
# ---------------------------------------------------------------------------------------------

NOTEBOOK_INTRO = """# RSNA knee: offline source + memory run

Generated by `scripts/package_kaggle.py`. Internet is off and no GPU is used. This notebook:

1. finds the attached bundle dataset by its content id and verifies every file's sha256;
2. installs the bundled wheelhouse with `--no-index` when one was supplied (never the network);
3. runs `source/scripts/run_interiors.py` once, with the argument vector chosen when the bundle was
   built. Results go under `/kaggle/working`. A failing run raises: there is no fallback output.
"""

CELL_VERIFY = """\
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

CONFIG = json.loads(__CONFIG_JSON__)
INPUT_ROOT = Path(CONFIG["input_root"])
WORKING = Path(CONFIG["working_root"])
MANIFEST = "bundle-manifest.json"
UNLISTED_TOP_LEVEL = {MANIFEST, "dataset-metadata.json"}


def read_manifest(directory):
    path = directory / MANIFEST
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def subdirectories(parent):
    if not parent.is_dir():
        return []
    return [child for child in sorted(parent.iterdir()) if child.is_dir()]


def candidate_directories():
    owner, _, slug = CONFIG["dataset_id"].partition("/")
    candidates = [INPUT_ROOT / slug, INPUT_ROOT / "datasets" / owner / slug]
    candidates += subdirectories(INPUT_ROOT)
    for owner_directory in subdirectories(INPUT_ROOT / "datasets"):
        candidates += subdirectories(owner_directory)
    return candidates


def find_bundle():
    found = {}
    for directory in candidate_directories():
        manifest = read_manifest(directory)
        if manifest is not None and manifest.get("bundle_id") == CONFIG["bundle_id"]:
            found[str(directory.resolve())] = directory
    if len(found) != 1:
        raise RuntimeError("expected exactly one mounted bundle " + CONFIG["bundle_id"] + ", found " + str(len(found)))
    return next(iter(found.values()))


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_id(entries):
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: item["path"]):
        digest.update(entry["path"].encode("utf-8"))
        digest.update(b"\\0")
        digest.update(entry["sha256"].encode("ascii"))
        digest.update(b"\\n")
    return digest.hexdigest()


def verify_bundle(bundle):
    manifest = read_manifest(bundle)
    if manifest is None or manifest.get("bundle_id") != CONFIG["bundle_id"]:
        raise RuntimeError("bundle manifest is missing or is not this notebook's bundle")
    entries = manifest["files"]
    if tree_id(entries) != CONFIG["bundle_id"]:
        raise RuntimeError("bundle manifest does not hash to its own id")
    listed = {entry["path"] for entry in entries}
    present = set()
    for directory, _, names in os.walk(bundle):
        for name in names:
            relative = (Path(directory) / name).relative_to(bundle).as_posix()
            if relative not in UNLISTED_TOP_LEVEL:
                present.add(relative)
    if present != listed:
        raise RuntimeError("bundle files differ from its manifest: missing " + str(sorted(listed - present))
                           + ", unlisted " + str(sorted(present - listed)))
    for entry in entries:
        if sha256_file(bundle / entry["path"]) != entry["sha256"]:
            raise RuntimeError("sha256 mismatch: " + entry["path"])
    return manifest


BUNDLE = find_bundle()
verify_bundle(BUNDLE)
print("bundle verified:", CONFIG["bundle_id"], "at", BUNDLE)
"""

CELL_INSTALL = """\
INSTALL = CONFIG["offline_install"]
if INSTALL is None:
    print("no wheelhouse supplied: nothing installed; the image's own packages are used")
else:
    command = [
        sys.executable, "-m", "pip", "install", "--no-index", "--no-input",
        "--disable-pip-version-check", "--only-binary=:all:", "--find-links", str(BUNDLE / "wheelhouse"),
    ]
    if INSTALL["mode"] == "requirements":
        command += ["-r", str(BUNDLE / "requirements.txt")]
    else:
        command += [str(BUNDLE / wheel) for wheel in INSTALL["wheels"]]
    subprocess.run(command, check=True, env=dict(os.environ, PIP_NO_INDEX="1"))
"""

CELL_RUN = """\
import shutil

SUBSTITUTIONS = {
    "bundle": str(BUNDLE),
    "input": str(INPUT_ROOT),
    "memory": str(BUNDLE / "memory"),
    "source": str(BUNDLE / "source"),
    "working": str(WORKING),
}


def expand(token):
    for name, value in SUBSTITUTIONS.items():
        token = token.replace("{" + name + "}", value)
    return token


ARGV = [expand(token) for token in CONFIG["run_argv"]]
SCRIPT = BUNDLE / "source" / "scripts" / "run_interiors.py"
COMMAND = [sys.executable, str(SCRIPT), *ARGV]
WORKING.mkdir(parents=True, exist_ok=True)
python_path = [str(BUNDLE / "source" / "src")]
if os.environ.get("PYTHONPATH"):
    python_path.append(os.environ["PYTHONPATH"])
ENVIRONMENT = dict(
    os.environ,
    PYTHONPATH=os.pathsep.join(python_path),
    PYTHONDONTWRITEBYTECODE="1",
    NUMBA_CACHE_DIR=str(WORKING / ".numba-cache"),
    PIP_NO_INDEX="1",
)
completed = subprocess.run(COMMAND, cwd=str(WORKING), env=ENVIRONMENT)
record = {"bundle_id": CONFIG["bundle_id"], "command": COMMAND, "returncode": completed.returncode}
(WORKING / "package-run.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
if completed.returncode != 0:
    raise RuntimeError("run_interiors.py exited " + str(completed.returncode) + "; no fallback output is written")
if "--diagnostic-submission-template" in ARGV:
    output_positions = [index for index, token in enumerate(ARGV) if token == "--diagnostic-output"]
    if len(output_positions) != 1 or output_positions[0] + 1 >= len(ARGV):
        raise RuntimeError("requested submission has no unique --diagnostic-output directory")
    diagnostic_output = Path(ARGV[output_positions[0] + 1]).resolve()
    try:
        relative_output = diagnostic_output.relative_to(WORKING.resolve())
    except ValueError as error:
        raise RuntimeError("diagnostic output for a requested submission must be under /kaggle/working") from error
    if not relative_output.parts:
        raise RuntimeError("diagnostic output for a requested submission must be a fresh subdirectory")
    produced_submission = diagnostic_output / "submission.csv"
    if not produced_submission.is_file():
        raise RuntimeError("run_interiors.py succeeded but did not produce the requested submission.csv")
    visible_submission = WORKING / "submission.csv"
    if produced_submission != visible_submission.resolve():
        shutil.copyfile(produced_submission, visible_submission)
print("run_interiors.py finished; results are under", WORKING)
"""


def _lines(text: str) -> list[str]:
    return text.splitlines(keepends=True)


def build_notebook(config: dict[str, Any]) -> dict[str, Any]:
    config_literal = repr(json.dumps(config, sort_keys=True))
    code_cells = (
        CELL_VERIFY.replace("__CONFIG_JSON__", config_literal),
        CELL_INSTALL,
        CELL_RUN,
    )
    cells: list[dict[str, Any]] = [
        {"cell_type": "markdown", "metadata": {}, "source": _lines(NOTEBOOK_INTRO)}
    ]
    cells += [
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": _lines(source),
        }
        for source in code_cells
    ]
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 4,
    }


def notebook_config(notebook: dict[str, Any]) -> dict[str, Any]:
    """The CONFIG literal of the first code cell, read without running anything."""
    for cell in notebook["cells"]:
        if cell["cell_type"] != "code":
            continue
        for node in ast.walk(ast.parse("".join(cell["source"]))):
            if (
                isinstance(node, ast.Assign)
                and any(
                    isinstance(target, ast.Name) and target.id == "CONFIG"
                    for target in node.targets
                )
                and isinstance(node.value, ast.Call)
                and len(node.value.args) == 1
                and isinstance(node.value.args[0], ast.Constant)
                and isinstance(node.value.args[0].value, str)
            ):
                return json.loads(node.value.args[0].value)
    raise PackagingError("notebook has no CONFIG = json.loads('...') cell")


def check_notebook(
    notebook: object, manifest: dict[str, Any], problems: list[str]
) -> None:
    if (
        not isinstance(notebook, dict)
        or notebook.get("nbformat") != 4
        or not isinstance(notebook.get("cells"), list)
    ):
        problems.append("notebook is not an nbformat 4 document")
        return
    code = []
    script_names = 0
    for index, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", []))
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            problems.append(f"notebook code cell {index} does not parse: {exc}")
        else:
            script_names += sum(
                isinstance(node, ast.Constant) and node.value == "run_interiors.py"
                for node in ast.walk(tree)
            )
        code.append(source)
    if not code:
        problems.append("notebook has no code cells")
        return
    joined = "\n".join(code)
    for word in FORBIDDEN_NOTEBOOK_WORDS:
        if word in joined:
            problems.append(f"notebook code mentions {word!r}")
    if "pip" in joined and "--no-index" not in joined:
        problems.append("notebook installs without --no-index")
    if script_names != 1:
        problems.append(
            "notebook must name run_interiors.py exactly once (one invocation)"
        )
    try:
        config = notebook_config(notebook)
    except (PackagingError, SyntaxError, ValueError) as exc:
        problems.append(f"notebook CONFIG unreadable: {exc}")
        return
    if config.get("bundle_id") != manifest.get("bundle_id"):
        problems.append("notebook bundle_id differs from the manifest's")
    if config.get("run_argv") != manifest.get("run_argv"):
        problems.append("notebook run_argv differs from the manifest's")
    if config.get("dataset_id") != manifest.get("dataset_id"):
        problems.append("notebook dataset_id differs from the manifest's")


# ---------------------------------------------------------------------------------------------
# Verification of a built bundle
# ---------------------------------------------------------------------------------------------


def _load_json(path: Path, problems: list[str]) -> Any:
    try:
        with open_regular(path) as reader:
            return json.loads(reader.read().decode("utf-8"))
    except (PackagingError, UnicodeDecodeError, ValueError) as exc:
        problems.append(f"{path.name}: {exc}")
        return None


def _check_manifest_files(
    dataset: Path, manifest: dict[str, Any], problems: list[str]
) -> None:
    entries = manifest.get("files")
    if manifest.get("schema") != BUNDLE_SCHEMA or not isinstance(entries, list):
        problems.append("manifest schema or files are wrong")
        return
    clean = []
    for entry in entries:
        try:
            safe_relative(entry["path"])
            if (
                not SHA256_RE.match(entry["sha256"])
                or entry["role"] not in ROLES
                or entry["bytes"] < 0
            ):
                raise KeyError("sha256/role/bytes")
        except (KeyError, TypeError, PackagingError) as exc:
            problems.append(f"manifest entry is malformed: {entry!r} ({exc})")
            continue
        clean.append(entry)
    if len(clean) != len(entries):
        return
    listed = {entry["path"] for entry in clean}
    if len(listed) != len(clean):
        problems.append("manifest lists a path twice")
    if tree_id(clean) != manifest.get("bundle_id"):
        problems.append("manifest bundle_id is not the hash of its files")
    for required in REQUIRED_PATHS:
        if required not in listed:
            problems.append(f"manifest lacks required file {required}")
    present: set[str] = set()
    for directory, _, names in os.walk(dataset):
        for name in names:
            path = Path(directory) / name
            relative = path.relative_to(dataset).as_posix()
            if path.is_symlink():
                problems.append(f"unsafe symlink in bundle: {relative}")
            if relative not in UNLISTED_TOP_LEVEL:
                present.add(relative)
    for relative in sorted(listed - present):
        problems.append(f"listed file is missing: {relative}")
    for relative in sorted(present - listed):
        problems.append(f"file is not in the manifest: {relative}")
    for entry in clean:
        if entry["path"] in present:
            try:
                digest, size = sha256_file(dataset / entry["path"])
            except PackagingError as exc:
                problems.append(str(exc))
                continue
            if digest != entry["sha256"] or size != entry["bytes"]:
                problems.append(f"hash or size mismatch: {entry['path']}")


def _check_metadata(
    output: Path, manifest: dict[str, Any], problems: list[str]
) -> None:
    dataset_meta = _load_json(output / "dataset" / DATASET_METADATA_NAME, problems)
    if isinstance(dataset_meta, dict):
        if dataset_meta.get("id") != manifest.get("dataset_id"):
            problems.append("dataset-metadata id differs from the manifest's")
        if not 6 <= len(str(dataset_meta.get("title", ""))) <= 50:
            problems.append("dataset-metadata title must be 6-50 characters")
    kernel = _load_json(output / "kernel" / KERNEL_METADATA_NAME, problems)
    if isinstance(kernel, dict):
        expected = {
            "enable_internet": "false",
            "enable_gpu": "false",
            "enable_tpu": "false",
            "language": "python",
            "kernel_type": "notebook",
            "code_file": NOTEBOOK_NAME,
        }
        for key, value in expected.items():
            if kernel.get(key) != value:
                problems.append(
                    f"kernel-metadata {key} must be {value!r}, is {kernel.get(key)!r}"
                )
        if kernel.get("dataset_sources") != [manifest.get("dataset_id")]:
            problems.append(
                "kernel-metadata dataset_sources must be exactly the bundle dataset"
            )
        if not kernel.get("competition_sources"):
            problems.append("kernel-metadata has no competition_sources")
        if kernel.get("kernel_sources") or kernel.get("model_sources"):
            problems.append("kernel-metadata must attach no kernel or model sources")
        try:
            _, slug = split_id(str(kernel.get("id")), "kernel id")
            if kernel.get("title") != title_of(slug):
                problems.append("kernel-metadata title must be the id slug with spaces")
        except PackagingError as exc:
            problems.append(str(exc))
    notebook = _load_json(output / "kernel" / NOTEBOOK_NAME, problems)
    if notebook is not None:
        check_notebook(notebook, manifest, problems)


def validate_bundle(output_dir: Path) -> dict[str, Any]:
    """Re-read a built bundle: manifest hashes, file set, notebook syntax and metadata."""
    output = Path(output_dir)
    problems: list[str] = []
    manifest = _load_json(output / "dataset" / MANIFEST_NAME, problems)
    if isinstance(manifest, dict):
        _check_manifest_files(output / "dataset", manifest, problems)
        _check_metadata(output, manifest, problems)
    elif manifest is not None:
        problems.append("manifest is not a JSON object")
    if problems:
        raise PackagingError("bundle does not verify:\n- " + "\n- ".join(problems))
    assert isinstance(manifest, dict)
    return {
        "bundle_id": manifest["bundle_id"],
        "dataset_id": manifest["dataset_id"],
        "file_count": len(manifest["files"]),
    }


# ---------------------------------------------------------------------------------------------
# The build
# ---------------------------------------------------------------------------------------------


def _requires_python(root: Path) -> str | None:
    try:
        with open_regular(root / "pyproject.toml") as reader:
            return tomllib.loads(reader.read().decode("utf-8"))["project"][
                "requires-python"
            ]
    except (PackagingError, UnicodeDecodeError, tomllib.TOMLDecodeError, KeyError):
        return None


def _plan(
    spec: PackageSpec,
    source_root: Path,
    memory_dir: Path,
    wheelhouse: Path | None,
    requirements: Path | None,
):
    planned, excluded = collect_source(source_root, spec.runtime_scripts)
    planned += collect_memory(memory_dir)
    if requirements is not None and wheelhouse is None:
        raise PackagingError(
            "requirements need a wheelhouse: nothing is ever downloaded"
        )
    if wheelhouse is not None:
        planned += collect_wheelhouse(wheelhouse)
    if requirements is not None:
        planned.append(collect_requirements(requirements))
    check_collisions(planned)
    return planned, excluded


def _copy_plan(planned: Sequence[PlannedFile], dataset: Path) -> list[dict[str, Any]]:
    before = {item.dest: signature(item.source) for item in planned}
    entries = []
    for item in sorted(planned, key=lambda planned_file: planned_file.dest):
        destination = dataset.joinpath(*PurePosixPath(item.dest).parts)
        digest, size = copy_hashed(item.source, destination)
        entries.append(
            {"path": item.dest, "role": item.role, "sha256": digest, "bytes": size}
        )
    for item, entry in zip(
        sorted(planned, key=lambda planned_file: planned_file.dest),
        entries,
        strict=True,
    ):
        again, _ = sha256_file(item.source)
        if again != entry["sha256"] or signature(item.source) != before[item.dest]:
            raise PackagingError(
                f"stale_source_input: {item.source} changed while it was packaged"
            )
    return entries


def build_bundle(spec: PackageSpec) -> dict[str, Any]:
    """Build the bundle into a fresh `spec.output_dir`; on any failure nothing is left behind."""
    _, dataset_slug = split_id(spec.dataset_id, "dataset id")
    _, kernel_slug = split_id(spec.kernel_id, "kernel id")
    if not spec.competition_sources or not all(
        SLUG_RE.match(slug) for slug in spec.competition_sources
    ):
        raise PackagingError(
            "at least one competition source slug (lowercase-with-hyphens) is required"
        )
    warnings = validate_run_argv(spec.run_argv)

    source_root = Path(os.path.realpath(spec.source_root))
    memory_dir = Path(os.path.abspath(spec.memory_dir))
    wheelhouse = Path(os.path.abspath(spec.wheelhouse)) if spec.wheelhouse else None
    requirements = (
        Path(os.path.abspath(spec.requirements)) if spec.requirements else None
    )
    for given, what in (
        (spec.source_root, "source root"),
        (spec.memory_dir, "memory directory"),
    ):
        if Path(os.path.abspath(given)).is_symlink():
            raise PackagingError(f"unsafe symlink: the {what} argument is a symlink")
    output = Path(os.path.abspath(spec.output_dir))
    if os.path.lexists(output):
        raise PackagingError(
            f"output already exists (a fresh directory is required): {output}"
        )
    output = Path(os.path.realpath(output))
    check_disjoint(
        output,
        {
            "source root": source_root,
            "memory directory": Path(os.path.realpath(memory_dir)),
            "wheelhouse": Path(os.path.realpath(wheelhouse)) if wheelhouse else None,
            "requirements file": Path(os.path.realpath(requirements))
            if requirements
            else None,
        },
    )

    planned, excluded = _plan(spec, source_root, memory_dir, wheelhouse, requirements)
    install: dict[str, Any] | None = None
    if wheelhouse is not None:
        wheels = sorted(item.dest for item in planned if item.role == "wheelhouse")
        install = (
            {"mode": "requirements"}
            if requirements is not None
            else {"mode": "wheels", "wheels": wheels}
        )
    else:
        warnings.append(
            "no wheelhouse: runtime dependencies come from the Kaggle image, which is not verified here"
        )

    dataset, kernel = output / "dataset", output / "kernel"
    output.mkdir(parents=True, exist_ok=False)
    try:
        dataset.mkdir()
        kernel.mkdir()
        entries = _copy_plan(planned, dataset)
        bundle_id = tree_id(entries)
        by_path = {entry["path"]: entry["sha256"] for entry in entries}
        manifest = {
            "schema": BUNDLE_SCHEMA,
            "bundle_id": bundle_id,
            "dataset_id": spec.dataset_id,
            "requires_python": _requires_python(source_root),
            "memory": {name: by_path[f"memory/{name}"] for name in MEMORY_FILES},
            "offline_install": install,
            "run_argv": list(spec.run_argv),
            "scope": "src/knee/**/*.py and the runtime scripts only; nothing else of the checkout",
            "files": entries,
            "excluded": excluded,
        }
        config = {
            "bundle_id": bundle_id,
            "dataset_id": spec.dataset_id,
            "input_root": spec.input_root,
            "working_root": spec.working_root,
            "offline_install": install,
            "run_argv": list(spec.run_argv),
        }
        (dataset / MANIFEST_NAME).write_text(dumps(manifest), encoding="utf-8")
        (dataset / DATASET_METADATA_NAME).write_text(
            dumps(
                {
                    "title": title_of(dataset_slug),
                    "id": spec.dataset_id,
                    "licenses": [{"name": "other"}],
                }
            ),
            encoding="utf-8",
        )
        (kernel / NOTEBOOK_NAME).write_text(
            dumps(build_notebook(config)), encoding="utf-8"
        )
        (kernel / KERNEL_METADATA_NAME).write_text(
            dumps(
                {
                    "id": spec.kernel_id,
                    "title": title_of(kernel_slug),
                    "code_file": NOTEBOOK_NAME,
                    "language": "python",
                    "kernel_type": "notebook",
                    "is_private": "true",
                    "enable_gpu": "false",
                    "enable_tpu": "false",
                    "enable_internet": "false",
                    "dataset_sources": [spec.dataset_id],
                    "competition_sources": list(spec.competition_sources),
                    "kernel_sources": [],
                    "model_sources": [],
                }
            ),
            encoding="utf-8",
        )
        summary = validate_bundle(output)
    except BaseException:
        shutil.rmtree(output, ignore_errors=True)
        raise
    return {
        **summary,
        "output": str(output),
        "dataset_dir": str(dataset),
        "kernel_dir": str(kernel),
        "kernel_id": spec.kernel_id,
        "excluded_count": len(excluded),
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="build a fresh bundle")
    build.add_argument("--source-root", type=Path, required=True)
    build.add_argument("--memory-dir", type=Path, required=True)
    build.add_argument("--output-dir", type=Path, required=True)
    build.add_argument(
        "--dataset-id", required=True, help="owner/slug of the Kaggle dataset"
    )
    build.add_argument(
        "--kernel-id", required=True, help="owner/slug of the Kaggle notebook"
    )
    build.add_argument(
        "--competition-source",
        action="append",
        required=True,
        dest="competition_sources",
    )
    build.add_argument(
        "--run-argv-json",
        required=True,
        help="JSON list: argv of the one run_interiors.py call",
    )
    build.add_argument("--wheelhouse", type=Path)
    build.add_argument("--requirements", type=Path)
    build.add_argument(
        "--runtime-script", action="append", default=[], dest="runtime_scripts"
    )
    verify = commands.add_parser("verify", help="re-verify a built output directory")
    verify.add_argument("output_dir", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "verify":
            result = validate_bundle(args.output_dir)
        else:
            try:
                run_argv = json.loads(args.run_argv_json)
            except ValueError as exc:
                raise PackagingError(f"--run-argv-json is not JSON: {exc}") from exc
            validate_run_argv(run_argv)
            result = build_bundle(
                PackageSpec(
                    source_root=args.source_root,
                    memory_dir=args.memory_dir,
                    output_dir=args.output_dir,
                    dataset_id=args.dataset_id,
                    kernel_id=args.kernel_id,
                    competition_sources=tuple(args.competition_sources),
                    run_argv=tuple(run_argv),
                    wheelhouse=args.wheelhouse,
                    requirements=args.requirements,
                    runtime_scripts=tuple(args.runtime_scripts),
                )
            )
    except PackagingError as exc:
        print(f"package_kaggle: refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
