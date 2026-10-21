"""Private offline Kaggle script: squint-first production inference on the mounted test studies.

A thin wrapper. It decides nothing about the images or the diagnosis; it sets up an offline,
verified, local copy of the code and the squint memory, runs the project's real entry point once,
and publishes what that run wrote.

Steps (each timed in /kaggle/working/squint-production-runtime.json):

1. find the attached private runtime dataset (rohanvinaik/rsna-knee-squint-runtime), the official
   competition files and the locked cp313 wheels dataset (rohanvinaik/rsna-knee-wheels-cp313);
2. require the release's expected bundle_id and memory-manifest sha256 before choosing any mounted
   version, then copy the code and memory to LOCAL disk: the dataset's tar is streamed once, its sha256 is
   checked against the outer RUNTIME_MANIFEST.json and every file against the inner manifest, so the
   run reads nothing from the network-backed mount except the study images. Kaggle may instead have
   auto-unpacked the tar as runtime-bundle/ beside the outer manifest, so two manifests are found;
   `select_runtime_manifest` recognises exactly that pair (the inner manifest equals the outer one except
   for its tar record), prefers a usable tar and otherwise the extracted tree whose listed files are all
   present, and refuses every other pair by name. The copy still checks every file's sha256 and size;
3. install the locked wheels with `pip --no-index` into a local `--target` directory;
4. run, with one thread per process for BLAS/Numba (the studies are spread over four workers):

       python scripts/run_interiors.py --split test --root <competition mount> --workers 4 \\
           --diagnostic-mode infer --diagnostic-memory <local memory> \\
           --diagnostic-submission-template <official sample_submission.csv> \\
           --diagnostic-output /kaggle/working/squint-production/diagnostics

   The argument vector is checked against a whitelist: no products, no recipes, no labels, no
   reconstruction route, no drawing, no teaching. There is no fallback to a full reconstruction;
   a failed run publishes no submission;
5. validate the produced CSV against the official template (exact header, study UIDs in order, twelve
   condition columns, finite values in [0, 1]) and publish it as /kaggle/working/submission.csv.
   The run's own receipt.json must exist and its authoritative `work.full_anatomy_runs` must be present
   and exactly 0 (any fallback-run counter anywhere in it must be 0 too); bounded zoom runs
   (`work.bounded_zoom_runs`) are the route's own work and are allowed. Otherwise nothing is published.

Retained under /kaggle/working: the run's whole diagnostic output directory (evidence, per-study
records, the full actual receipts), the complete run log, squint-production-setup.log (complete pip,
import-check and entry-point help output), and squint-production-runtime.json (wall, CPU, peak
process-tree RSS/PSS, output bytes, file hashes, environment). Nothing is ever truncated into the
receipt: long output stays in its file and the receipt names the file. Nothing is downloaded, uploaded or submitted to the
competition; the kernel is private and has internet, GPU and TPU off.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import platform
import resource
import shutil
import signal
import subprocess
import sys
import tarfile
import threading
import time
import traceback
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Self

KERNEL = "squint-production"
# The overrides exist only for rehearsing the script against a local fake mount; Kaggle sets none.
INPUT = Path(os.environ.get("SQUINT_KAGGLE_INPUT", "/kaggle/input"))
WORK = Path(os.environ.get("SQUINT_KAGGLE_WORKING", "/kaggle/working"))
_KAGGLE_TMP = Path("/kaggle/tmp")
SCRATCH = Path(
    os.environ.get(
        "SQUINT_KAGGLE_SCRATCH",
        str(_KAGGLE_TMP if _KAGGLE_TMP.exists() else Path("/tmp")),
    )
)
LOCAL = SCRATCH / f"rsna-{KERNEL}"
RECEIPT = WORK / f"{KERNEL}-runtime.json"
LOG = WORK / f"{KERNEL}-run.log"
SETUP_LOG = WORK / f"{KERNEL}-setup.log"
OUT_PARENT = WORK / KERNEL
OUT_DIR = OUT_PARENT / "diagnostics"

RUNTIME_HINT = "rsna-knee-squint-runtime"
WHEELS_HINT = "rsna-knee-wheels-cp313"
COMPETITION_HINT = "rsna-knee-abnormality-detection"
WHEEL_TAG = "cp313"
MANIFEST_SCHEMA = "knee.squint-runtime-manifest/v1"
MEMORY_SCHEMA = "knee.squint-memory/v1"
MANIFEST_NAME = "RUNTIME_MANIFEST.json"
# Release pins come from verified staging. The uploaded dataset must match both
# before launching; unpinned or stale mounts refuse before inference.
EXPECTED_RUNTIME_BUNDLE_ID: str | None = (
    "60c5fb8ed63eb1c17abf0d3da6def516dc9b3538e1a234e1f19b732177b50d9b"
)
EXPECTED_MEMORY_MANIFEST_SHA256: str | None = (
    "e8169d459a9d3a212a53162ae4c99902499d5b705a847da2d327721deeeccffa"
)
CONDITION_COUNT = 12
WORKERS = 4
KAGGLE_LIMIT_S = 9 * 3600
RESERVE_S = 20 * 60
SAMPLE_INTERVAL_S = 2.0
TREE_INTERVAL_S = 30.0
SKIP_DIRS = {"train_series", "test_series", "source", "wheels", "memory"}
MAX_DIRS_VISITED = 5000
THREAD_VARS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "NUMBA_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
)
ALLOWED_FLAGS = {
    "--split",
    "--root",
    "--workers",
    "--diagnostic-mode",
    "--diagnostic-memory",
    "--diagnostic-submission-template",
    "--diagnostic-output",
    "--squint-time-limit",
}
IMPORT_CHECK = (
    "import sys\n"
    "import numpy, scipy, skimage, pydicom, gdcm, numba, h5py\n"
    "import knee, knee.diagnosis.squint_pipeline as pipeline\n"
    "assert knee.__file__.startswith(sys.argv[1]), knee.__file__\n"
    "assert numpy.__file__.startswith(sys.argv[2]), numpy.__file__\n"
    "assert callable(getattr(pipeline, 'run_squint_cli', None)), 'run_squint_cli is missing'\n"
    "print(sys.version)\n"
    "print(numpy.__version__, scipy.__version__, skimage.__version__, pydicom.__version__,"
    " numba.__version__, h5py.__version__)\n"
    "print(knee.__file__)\n"
    "print(pipeline.__file__)\n"
)

STARTED = time.time()
REPORT: dict = {
    "kernel": KERNEL,
    "started_unix": STARTED,
    "python": sys.version,
    "status": "started",
    "steps": {},
    "warnings": [],
    "contract": {
        "route": "squint-first: input-available squints, located anatomy, individual case recall",
        "full_reconstruction_fallback_called": False,
        "competition_submission_made": False,
        "network": "none; wheels and code come from attached private datasets",
    },
}


class SetupError(RuntimeError):
    """A named refusal before or after the run; the receipt keeps the reason."""


def save() -> None:
    REPORT["saved_unix"] = time.time()
    WORK.mkdir(parents=True, exist_ok=True)
    part = RECEIPT.with_name(RECEIPT.name + ".part")
    part.write_text(
        json.dumps(REPORT, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(part, RECEIPT)


def say(message: str) -> None:
    print(f"[{KERNEL} +{time.time() - STARTED:7.1f}s] {message}", flush=True)


class Step:
    """Time one step into the receipt, saving it on entry and on exit."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.began = 0.0

    def __enter__(self) -> Self:
        self.began = time.perf_counter()
        REPORT["steps"][self.name] = {"running": True}
        save()
        say(f"step {self.name}")
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        REPORT["steps"][self.name] = {
            "seconds": round(time.perf_counter() - self.began, 2),
            "ok": exc_type is None,
        }
        save()
        return False


# ---------------------------------------------------------------------------------------------
# Finding and verifying inputs
# ---------------------------------------------------------------------------------------------


def find(name: str, depth: int = 5) -> list[Path]:
    """Find a file by name a few levels under the input mount, never walking the image folders."""
    hits: list[Path] = []
    level = [INPUT] if INPUT.exists() else []
    visited = 0
    for _ in range(depth):
        following: list[Path] = []
        for folder in level:
            visited += 1
            if visited > MAX_DIRS_VISITED:
                return hits
            try:
                entries = sorted(folder.iterdir())
            except OSError:
                continue
            for entry in entries:
                if entry.name == name and entry.is_file():
                    hits.append(entry)
                elif entry.is_dir() and entry.name not in SKIP_DIRS:
                    following.append(entry)
        level = following
    return hits


def choose(hits: list[Path], hint: str, what: str) -> Path:
    if not hits:
        raise SetupError(f"{what} not found under {INPUT}")
    preferred = [hit for hit in hits if hint in str(hit)]
    pool = preferred or hits
    distinct = {str(hit.resolve()): hit for hit in pool}
    if len(distinct) != 1:
        raise SetupError(f"{what} is ambiguous: {sorted(distinct)}")
    return next(iter(distinct.values()))


def blocks(handle):
    """Successive 1 MiB blocks of an open binary file."""
    while True:
        block = handle.read(1 << 20)
        if not block:
            return
        yield block


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in blocks(handle):
            digest.update(block)
    return digest.hexdigest()


def tree_id(entries: list[dict]) -> str:
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: item["path"]):
        digest.update(entry["path"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(entry["sha256"].encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def safe_member(name: str) -> PurePosixPath:
    relative = PurePosixPath(name)
    if (
        not name
        or "\0" in name
        or "\\" in name
        or relative.is_absolute()
        or relative.as_posix() != name
        or any(part in ("", ".", "..") for part in relative.parts)
    ):
        raise SetupError(f"unsafe path in the runtime bundle: {name!r}")
    return relative


class HashingReader:
    def __init__(self, handle) -> None:
        self.handle = handle
        self.digest = hashlib.sha256()
        self.size = 0

    def read(self, count: int = -1) -> bytes:
        data = self.handle.read(count)
        self.digest.update(data)
        self.size += len(data)
        return data


def load_manifest(path: Path) -> dict:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise SetupError(f"runtime manifest unreadable: {error}") from error
    if not isinstance(manifest, dict) or manifest.get("schema") != MANIFEST_SCHEMA:
        raise SetupError(f"runtime manifest schema is not {MANIFEST_SCHEMA}")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise SetupError("runtime manifest lists no files")
    for entry in files:
        safe_member(entry["path"])
        if (
            len(entry["sha256"]) != 64
            or type(entry["bytes"]) is not int
            or entry["bytes"] < 0
        ):
            raise SetupError(f"runtime manifest entry is malformed: {entry!r}")
    if len({entry["path"] for entry in files}) != len(files):
        raise SetupError("runtime manifest lists a path twice")
    if tree_id(files) != manifest.get("bundle_id"):
        raise SetupError("runtime manifest does not hash to its own bundle_id")
    memory = manifest.get("memory")
    if not isinstance(memory, dict) or memory.get("schema") != MEMORY_SCHEMA:
        raise SetupError(f"bundled memory does not declare {MEMORY_SCHEMA}")
    if not isinstance(manifest.get("source"), dict) or not isinstance(
        manifest.get("pythonpath"), list
    ):
        raise SetupError("runtime manifest lacks its source or pythonpath block")
    for item in manifest["pythonpath"]:
        safe_member(item)
    paths = {entry["path"] for entry in files}
    if manifest.get("entrypoint") not in paths or memory.get("entry") not in (
        {"memory"} | {p for p in paths if p.startswith("memory/")}
    ):
        raise SetupError(
            "runtime manifest entrypoint or memory entry is not in the bundle"
        )
    return manifest


def extract_tar(tar_path: Path, manifest: dict, dest: Path) -> dict:
    """Stream the tar once to local disk, hashing the archive and every member as it is written."""
    expected = {entry["path"]: entry for entry in manifest["files"]}
    record = manifest.get("tar")
    if not isinstance(record, dict):
        raise SetupError("outer manifest has no tar record")
    seen: set[str] = set()
    inner = None
    with tar_path.open("rb") as raw:
        reader = HashingReader(raw)
        with tarfile.open(fileobj=reader, mode="r|") as archive:  # type: ignore[call-overload]
            for member in archive:
                if not member.isreg():
                    raise SetupError(f"tar member is not a regular file: {member.name}")
                relative = safe_member(member.name)
                name = relative.as_posix()
                if name in seen:
                    raise SetupError(f"tar holds {name} twice")
                seen.add(name)
                source = archive.extractfile(member)
                if source is None:
                    raise SetupError(f"tar member cannot be read: {name}")
                if name == MANIFEST_NAME:
                    inner = json.loads(source.read().decode("utf-8"))
                    continue
                entry = expected.get(name)
                if entry is None:
                    raise SetupError(f"tar member is not in the manifest: {name}")
                target = dest.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                size = 0
                with target.open("xb") as out:
                    for block in blocks(source):
                        digest.update(block)
                        size += len(block)
                        out.write(block)
                if digest.hexdigest() != entry["sha256"] or size != entry["bytes"]:
                    raise SetupError(f"hash or size mismatch in the tar: {name}")
        while reader.read(1 << 20):
            pass
    if reader.digest.hexdigest() != record.get("sha256") or reader.size != record.get(
        "bytes"
    ):
        raise SetupError("runtime-bundle.tar does not match its manifest record")
    missing = sorted(set(expected) - seen)
    if missing:
        raise SetupError(f"tar lacks manifest files: {missing}")
    if inner != {k: v for k, v in manifest.items() if k != "tar"}:
        raise SetupError("inner manifest differs from the outer manifest")
    return {
        "mode": "tar",
        "tar_sha256": reader.digest.hexdigest(),
        "tar_bytes": reader.size,
    }


def copy_directory(base: Path, manifest: dict, dest: Path) -> dict:
    """The dataset arrived already extracted: copy and verify every listed file."""
    for entry in manifest["files"]:
        relative = safe_member(entry["path"])
        source = base.joinpath(*relative.parts)
        target = dest.joinpath(*relative.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256()
        size = 0
        with source.open("rb") as reader, target.open("xb") as out:
            for block in blocks(reader):
                digest.update(block)
                size += len(block)
                out.write(block)
        if digest.hexdigest() != entry["sha256"] or size != entry["bytes"]:
            raise SetupError(f"hash or size mismatch: {entry['path']}")
    return {"mode": "directory"}


def materialise(manifest_path: Path, manifest: dict, dest: Path) -> dict:
    base = manifest_path.parent
    record = manifest.get("tar")
    tar_path = base / record["name"] if isinstance(record, dict) else None
    if tar_path is not None and tar_path.is_file():
        return extract_tar(tar_path, manifest, dest)
    if (base / "source").is_dir() and (base / "memory").is_dir():
        return copy_directory(base, manifest, dest)
    raise SetupError(
        f"no runtime-bundle.tar and no extracted source/ beside {manifest_path}"
    )


# ---------------------------------------------------------------------------------------------
# Choosing the runtime manifest: the dataset as uploaded, or as Kaggle auto-unpacked it
# ---------------------------------------------------------------------------------------------


def check_tar_record(manifest: dict) -> None:
    """An outer manifest names its archive as {name, sha256, bytes}; any other `tar` value is malformed."""
    if "tar" not in manifest:
        return
    record = manifest["tar"]
    ok = (
        isinstance(record, dict)
        and isinstance(record.get("name"), str)
        and isinstance(record.get("sha256"), str)
        and len(record["sha256"]) == 64
        and isinstance(record.get("bytes"), int)
        and not isinstance(record["bytes"], bool)
        and record["bytes"] >= 0
    )
    if ok:
        # a plain file name beside the manifest, never a path
        ok = safe_member(record["name"]).parts == (record["name"],)
    if not ok:
        raise SetupError(f"tar record is malformed: {record!r}")


def load_candidate(path: Path) -> dict:
    """Read and validate one candidate manifest whole; any defect is a refusal that names the file."""
    try:
        manifest = load_manifest(path)
        check_tar_record(manifest)
    except SetupError as error:
        raise SetupError(f"runtime manifest {path}: {error}") from error
    except (KeyError, TypeError, AttributeError, ValueError) as error:
        raise SetupError(
            f"runtime manifest {path} is malformed: {type(error).__name__}: {error}"
        ) from error
    return manifest


def memory_manifest_sha256(manifest: dict) -> str:
    """Return the declared digest for the memory's own manifest file."""
    memory = manifest["memory"]
    entry = safe_member(memory["entry"]).as_posix()
    path = f"{entry}/manifest.json"
    for file_entry in manifest["files"]:
        if file_entry["path"] == path:
            return file_entry["sha256"]
    raise SetupError(f"runtime manifest has no memory manifest file: {path}")


def archive_state(base: Path, manifest: dict) -> tuple[Path | None, str]:
    """The recorded archive beside `base` when it is really there with the recorded size (a stat only)."""
    record = manifest["tar"]
    tar_path = base / record["name"]
    if not tar_path.is_file():
        return None, f"{tar_path} is not present"
    try:
        size = tar_path.stat().st_size
    except OSError as error:
        return None, f"{tar_path} cannot be inspected: {error}"
    if size != record["bytes"]:
        return (
            None,
            f"{tar_path} is {size} bytes but the manifest records {record['bytes']} bytes",
        )
    return tar_path, f"{tar_path} is present with the recorded size"


def layout_problems(base: Path, manifest: dict) -> list[str]:
    """Why an extracted tree beside `base` cannot be copied: absent source/memory or listed files (stats only)."""
    problems = [
        f"{name}/ is not a directory"
        for name in ("source", "memory")
        if not (base / name).is_dir()
    ]
    for entry in manifest["files"]:
        relative = safe_member(entry["path"])
        if not base.joinpath(*relative.parts).is_file():
            problems.append(f"{entry['path']} is missing")
    return problems


def describe_candidate(path: Path, manifest: dict) -> str:
    kind = "outer, names its tar" if "tar" in manifest else "no tar record"
    return f"{path} [{kind}; bundle_id {manifest['bundle_id']}]"


def decided(
    path: Path, manifest: dict, shape: str, route: str, candidates: list, not_used: list
) -> dict:
    return {
        "manifest_path": path,
        "manifest": manifest,
        "selection": {
            "shape": shape,
            "route": route,
            "manifest": str(path),
            "bundle_id": manifest["bundle_id"],
            "candidates": candidates,
            "not_used": not_used,
        },
    }


def select_runtime_manifest(
    hits: list[Path],
    hint: str,
    *,
    expected_bundle_id: str | None = None,
    expected_memory_manifest_sha256: str | None = None,
) -> dict:
    """The one runtime manifest to materialise from, or a named refusal.

    Only manifests are read (whole) and files are stat'ed: nothing is hashed, extracted or copied here.
    `materialise` still streams the tar or copies the tree and checks every file's sha256 and size
    against the chosen manifest. The generic `choose` is not used for the runtime and not weakened.

    * First, every candidate is matched against both explicit release pins. Nonmatching, self-consistent
      versions are recorded as excluded and never considered as fallbacks.
    * One matching manifest (a tar beside it, or an extracted source/ and memory/ beside it): used as found,
      and `materialise` decides between the tar and the directory exactly as before.
    * Kaggle's auto-unpacked dataset: the outer manifest (it has a `tar` record) and, in a directory below
      it, the extracted bundle's own manifest. They are one bundle only if the extracted manifest equals the
      outer one in every field except the `tar` record. The recorded archive is then used when it is
      really there with the recorded size, otherwise the extracted tree when every listed file is present.
    * Among matching candidates, anything else is refused, naming every candidate: a pair that disagrees
      beyond the tar record, two outer or two extracted manifests, a third manifest, an equivalent pair that
      is not nested, or any malformed manifest. No sort order, shortest path or first hit picks a winner.
    """
    what = "squint runtime manifest"
    if expected_bundle_id is None:
        expected_bundle_id = EXPECTED_RUNTIME_BUNDLE_ID
    if expected_memory_manifest_sha256 is None:
        expected_memory_manifest_sha256 = EXPECTED_MEMORY_MANIFEST_SHA256
    if not isinstance(expected_bundle_id, str) or len(expected_bundle_id) != 64:
        raise SetupError("runtime bundle pin is not configured")
    if (
        not isinstance(expected_memory_manifest_sha256, str)
        or len(expected_memory_manifest_sha256) != 64
    ):
        raise SetupError("memory manifest pin is not configured")
    if not hits:
        raise SetupError(f"{what} not found under {INPUT}")
    pool = [hit for hit in hits if hint in str(hit)] or hits
    distinct = {str(hit.resolve()): hit for hit in pool}
    paths = [distinct[key] for key in sorted(distinct)]
    manifests: dict[Path, dict] = {path: load_candidate(path) for path in paths}
    all_candidates = [
        {
            "path": str(path),
            "bundle_id": manifests[path]["bundle_id"],
            "memory_manifest_sha256": memory_manifest_sha256(manifests[path]),
            "tar_record": "tar" in manifests[path],
        }
        for path in paths
    ]
    pin_record = {
        "expected_bundle_id": expected_bundle_id,
        "expected_memory_manifest_sha256": expected_memory_manifest_sha256,
        "observed_candidates": all_candidates,
    }
    REPORT.setdefault("inputs", {})["runtime_source_pin"] = pin_record
    matching = [
        path
        for path in paths
        if manifests[path]["bundle_id"] == expected_bundle_id
        and memory_manifest_sha256(manifests[path]) == expected_memory_manifest_sha256
    ]
    if not matching:
        observed = "; ".join(
            f"{item['path']} [bundle_id={item['bundle_id']}, "
            f"memory_manifest_sha256={item['memory_manifest_sha256']}]"
            for item in all_candidates
        )
        raise SetupError(
            "runtime pin mismatch: expected "
            f"bundle_id={expected_bundle_id}, "
            f"memory_manifest_sha256={expected_memory_manifest_sha256}; "
            f"observed: {observed or 'no candidates'}"
        )
    excluded = [
        item
        for item in all_candidates
        if item["path"] not in {str(path) for path in matching}
    ]
    paths = matching
    candidates = [
        item for item in all_candidates if item["path"] in {str(path) for path in paths}
    ]
    pin_selection = {**pin_record, "excluded_candidates": excluded}
    if len(paths) == 1:
        only = paths[0]
        result = decided(
            only, manifests[only], "single_manifest", "as_found", candidates, []
        )
        result["selection"]["source_pin"] = pin_selection
        return result
    outers = [path for path in paths if "tar" in manifests[path]]
    extracted = [path for path in paths if "tar" not in manifests[path]]
    if len(paths) != 2 or len(outers) != 1:
        raise SetupError(
            f"{what} is ambiguous: expected the one outer manifest and the one extracted manifest that "
            f"Kaggle unpacks from its tar, found {len(outers)} outer and {len(extracted)} extracted: "
            + "; ".join(describe_candidate(path, manifests[path]) for path in paths)
        )
    outer_path, inner_path = outers[0], extracted[0]
    outer, inner = manifests[outer_path], manifests[inner_path]
    if inner["bundle_id"] != outer["bundle_id"]:
        raise SetupError(
            f"{what}: two different runtime bundles are mounted and none is chosen: "
            f"{describe_candidate(outer_path, outer)} and {describe_candidate(inner_path, inner)}"
        )
    if inner != {key: value for key, value in outer.items() if key != "tar"}:
        absent = object()
        differing = sorted(
            key
            for key in (set(inner) | set(outer)) - {"tar"}
            if inner.get(key, absent) != outer.get(key, absent)
        )
        raise SetupError(
            f"{what}: {outer_path} and {inner_path} name the same bundle_id {outer['bundle_id']} but "
            f"disagree in {differing}; the extracted manifest must equal the outer one except its tar record"
        )
    outer_dir, inner_dir = outer_path.resolve().parent, inner_path.resolve().parent
    if outer_dir not in inner_dir.parents:
        raise SetupError(
            f"{what}: the equivalent manifests are not nested: {inner_path} is not inside {outer_dir}, "
            "so it is not the unpacked copy of that dataset's tar"
        )
    archive, archive_note = archive_state(outer_path.parent, outer)
    if archive is not None:
        unused = [
            {
                "manifest": str(inner_path),
                "reason": "the recorded archive is usable and preferred",
            }
        ]
        result = decided(
            outer_path, outer, "outer_and_extracted", "tar", candidates, unused
        )
        result["selection"]["source_pin"] = pin_selection
        return result
    problems = layout_problems(inner_path.parent, inner)
    if problems:
        raise SetupError(
            f"{what}: runtime bundle {outer['bundle_id']} has no usable source: the archive "
            f"{archive_note}; the extracted layout at {inner_path.parent} lacks: {'; '.join(problems)}"
        )
    unused = [
        {
            "manifest": str(outer_path),
            "reason": f"its archive is not usable: {archive_note}",
        }
    ]
    result = decided(
        inner_path,
        inner,
        "outer_and_extracted",
        "extracted_directory",
        candidates,
        unused,
    )
    result["selection"]["source_pin"] = pin_selection
    return result


# ---------------------------------------------------------------------------------------------
# Offline wheels and the environment
# ---------------------------------------------------------------------------------------------


def append_setup_log(
    title: str, command: list[str], code: int, stdout: str, stderr: str
) -> None:
    """Keep one setup command's complete output in a file; the receipt refers to it."""
    SETUP_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SETUP_LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"=== {title}: exit {code}\n$ {' '.join(command)}\n")
        handle.write(f"--- stdout\n{stdout}\n--- stderr\n{stderr}\n")


def install_wheels(requirements: Path) -> dict:
    shipped = requirements.parent / "wheels" / WHEEL_TAG
    if not shipped.is_dir():
        raise SetupError(f"no wheels/{WHEEL_TAG} beside {requirements}")
    wheels = LOCAL / "wheels"
    wheels.mkdir(parents=True)
    copied = []
    for wheel in sorted(shipped.iterdir()):
        if wheel.name.endswith(".whl") and not wheel.name.startswith("._"):
            shutil.copyfile(wheel, wheels / wheel.name)
            copied.append(wheel.name)
    if not copied:
        raise SetupError(f"no wheels in {shipped}")
    site = LOCAL / "site"
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--no-index",
        "--find-links",
        str(wheels),
        "--target",
        str(site),
        "-r",
        str(requirements),
        "--disable-pip-version-check",
        "--no-input",
        "--quiet",
    ]
    done = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        env=dict(os.environ, PIP_NO_INDEX="1"),
        timeout=1800,
    )
    append_setup_log(
        "offline wheel install", command, done.returncode, done.stdout, done.stderr
    )
    info = {
        "route": "target",
        "exit": done.returncode,
        "requirements": str(requirements),
        "requirements_sha256": sha256_file(requirements),
        "wheels": copied,
        "stdout": done.stdout,
        "stderr": done.stderr,
        "setup_log": str(SETUP_LOG),
    }
    if done.returncode != 0:
        REPORT["install"] = info
        raise SetupError("offline wheel install failed")
    return info


def child_env(site: Path, bundle: Path, manifest: dict) -> dict:
    """One thread per process for every numerical library; local caches; our code and wheels first."""
    env = dict(os.environ)
    python_path = [str(site)] + [
        str(bundle.joinpath(*PurePosixPath(p).parts)) for p in manifest["pythonpath"]
    ]
    if env.get("PYTHONPATH"):
        python_path.append(env["PYTHONPATH"])
    env.update(
        {
            "PYTHONPATH": os.pathsep.join(python_path),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUNBUFFERED": "1",
            "NUMBA_CACHE_DIR": str(LOCAL / "numba-cache"),
            "TMPDIR": str(LOCAL / "tmp"),
            "PIP_NO_INDEX": "1",
        }
    )
    for name in THREAD_VARS:
        env[name] = "1"
    return env


def environment_facts() -> dict:
    facts: dict = {
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "work": str(WORK),
        "scratch": str(SCRATCH),
        "thread_env": {name: "1" for name in THREAD_VARS},
    }
    if hasattr(os, "sched_getaffinity"):
        facts["cpus_available"] = len(os.sched_getaffinity(0))
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                facts["mem_total_kib"] = int(line.split()[1])
                break
    except (OSError, ValueError, IndexError):
        pass
    facts["cgroup"] = cgroup_facts()
    for label, path in (("work", WORK), ("scratch", SCRATCH)):
        if path.exists():
            facts[f"disk_{label}"] = shutil.disk_usage(path)._asdict()
    return facts


def cgroup_facts() -> dict:
    out = {}
    for label, path in (
        ("memory_peak_v2", "/sys/fs/cgroup/memory.peak"),
        ("memory_max_v2", "/sys/fs/cgroup/memory.max"),
        ("memory_max_usage_v1", "/sys/fs/cgroup/memory/memory.max_usage_in_bytes"),
        ("memory_limit_v1", "/sys/fs/cgroup/memory/memory.limit_in_bytes"),
    ):
        try:
            out[label] = Path(path).read_text().strip()
        except OSError:
            continue
    return out


# ---------------------------------------------------------------------------------------------
# Running the real entry point, sampled
# ---------------------------------------------------------------------------------------------

PAGE = os.sysconf("SC_PAGE_SIZE") if hasattr(os, "sysconf") else 4096


def tree_bytes(path: Path) -> tuple[int, int]:
    files = total = 0
    stack = [path]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as scan:
                for entry in scan:
                    if entry.is_dir(follow_symlinks=False):
                        stack.append(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        files += 1
                        total += entry.stat(follow_symlinks=False).st_size
        except OSError:
            continue
    return files, total


def process_table() -> tuple[dict, dict]:
    children: dict[int, list[int]] = {}
    rss: dict[int, int] = {}
    try:
        names = os.listdir("/proc")
    except OSError:
        return children, rss
    for name in names:
        if not name.isdigit():
            continue
        try:
            with open(f"/proc/{name}/stat", "rb") as handle:
                data = handle.read()
            fields = data[data.rindex(b")") + 2 :].split()
            parent, pages = int(fields[1]), int(fields[21])
        except (OSError, ValueError, IndexError):
            continue
        children.setdefault(parent, []).append(int(name))
        rss[int(name)] = pages * PAGE
    return children, rss


def pss_bytes(pid: int) -> int | None:
    try:
        with open(f"/proc/{pid}/smaps_rollup", "rb") as handle:
            for line in handle:
                if line.startswith(b"Pss:"):
                    return int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        return None
    return None


class Sampler(threading.Thread):
    """Peak resident memory summed over the command's whole process tree, and the output size."""

    def __init__(self, root_pid: int, watch: Path) -> None:
        super().__init__(daemon=True)
        self.root_pid = root_pid
        self.watch = watch
        self.stopper = threading.Event()
        self.peak_rss = self.peak_pss = self.peak_processes = self.samples = 0
        self.peak_output_bytes = self.peak_output_files = 0
        self.errors = 0
        self._next_tree = 0.0

    def sample(self) -> None:
        children, rss = process_table()
        pids, stack = [], [self.root_pid]
        while stack:
            pid = stack.pop()
            pids.append(pid)
            stack.extend(children.get(pid, ()))
        self.peak_rss = max(self.peak_rss, sum(rss.get(pid, 0) for pid in pids))
        pss = [pss_bytes(pid) for pid in pids]
        if any(value is not None for value in pss):
            self.peak_pss = max(self.peak_pss, sum(value or 0 for value in pss))
        self.peak_processes = max(self.peak_processes, len(pids))
        self.samples += 1
        if time.monotonic() >= self._next_tree and self.watch.exists():
            files, total = tree_bytes(self.watch)
            self.peak_output_files = max(self.peak_output_files, files)
            self.peak_output_bytes = max(self.peak_output_bytes, total)
            self._next_tree = time.monotonic() + TREE_INTERVAL_S

    def run(self) -> None:
        while not self.stopper.wait(SAMPLE_INTERVAL_S):
            try:
                self.sample()
            except (OSError, ValueError):
                # Expected: a process vanished mid-read (ProcessLookupError is an OSError) or /proc text
                # was unparsable. Sampling must not disturb the run; the count lands in the receipt.
                self.errors += 1

    def finish(self) -> dict:
        self.stopper.set()
        self.join(timeout=10)
        return {
            "samples": self.samples,
            "sampler_errors": self.errors,
            "peak_process_tree_rss_bytes": self.peak_rss,
            "peak_process_tree_pss_bytes": self.peak_pss or None,
            "peak_process_count": self.peak_processes,
            "peak_output_bytes_sampled": self.peak_output_bytes,
            "peak_output_files_sampled": self.peak_output_files,
        }


def stop_group(process: subprocess.Popen) -> None:
    for sig, wait_s in ((signal.SIGTERM, 60), (signal.SIGKILL, 30)):
        try:
            os.killpg(process.pid, sig)
        except (ProcessLookupError, PermissionError):
            return
        try:
            process.wait(timeout=wait_s)
            return
        except subprocess.TimeoutExpired:
            continue


def run_logged(
    argv: list[str], env: dict, cwd: Path, timeout_s: float, watch: Path
) -> dict:
    began = time.perf_counter()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    timed_out = False
    with LOG.open("ab") as log:
        process = subprocess.Popen(
            argv,
            env=env,
            cwd=str(cwd),
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        sampler = Sampler(process.pid, watch)
        sampler.start()
        try:
            code = process.wait(timeout=max(1.0, timeout_s))
        except subprocess.TimeoutExpired:
            timed_out = True
            stop_group(process)
            code = process.returncode
        finally:
            peaks = sampler.finish()
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    files, total = tree_bytes(watch) if watch.exists() else (0, 0)
    return {
        "argv": argv,
        "exit": code,
        "timed_out": timed_out,
        "wall_s": round(time.perf_counter() - began, 2),
        "children_user_s": round(after.ru_utime - before.ru_utime, 2),
        "children_sys_s": round(after.ru_stime - before.ru_stime, 2),
        "largest_single_child_rss_kib_so_far": after.ru_maxrss,
        "output_files": files,
        "output_bytes": total,
        "log": str(LOG),
        "log_bytes": LOG.stat().st_size,
        "log_sha256": sha256_file(LOG),
        **peaks,
        "cgroup_after": cgroup_facts(),
    }


def check_argv(argv: list[str]) -> None:
    """Only the production inference vector may run: a whitelist, not a blacklist."""
    flags = [token for token in argv[2:] if token.startswith("--")]
    unknown = sorted(set(flags) - ALLOWED_FLAGS)
    if unknown:
        raise SetupError(f"refusing flags outside the production whitelist: {unknown}")
    if len(flags) != len(set(flags)):
        raise SetupError("a flag is repeated in the production command")
    pairs = {
        argv[i]: argv[i + 1]
        for i in range(2, len(argv) - 1)
        if argv[i].startswith("--")
    }
    if pairs.get("--diagnostic-mode") != "infer" or pairs.get("--split") != "test":
        raise SetupError("production runs `--diagnostic-mode infer --split test` only")
    if pairs.get("--workers") != str(WORKERS):
        raise SetupError(f"production runs --workers {WORKERS}")
    try:
        internal_limit = Decimal(pairs["--squint-time-limit"])
    except (KeyError, InvalidOperation) as error:
        raise SetupError(
            "production requires a positive --squint-time-limit"
        ) from error
    if not internal_limit.is_finite() or internal_limit <= 0:
        raise SetupError("production requires a positive --squint-time-limit")


# ---------------------------------------------------------------------------------------------
# The official CSV, and the run's own receipt
# ---------------------------------------------------------------------------------------------


def read_rows(path: Path) -> tuple[list[list[str]], bytes]:
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    return list(csv.reader(io.StringIO(text, newline=""), strict=True)), raw


def read_template(path: Path) -> dict:
    rows, raw = read_rows(path)
    if (
        not rows
        or len(rows[0]) != CONDITION_COUNT + 1
        or rows[0][0] != "StudyInstanceUID"
    ):
        raise SetupError(
            f"{path} is not a StudyInstanceUID + {CONDITION_COUNT} condition template"
        )
    uids = [row[0] for row in rows[1:]]
    if (
        not uids
        or len(set(uids)) != len(uids)
        or any(len(row) != len(rows[0]) for row in rows[1:])
    ):
        raise SetupError(f"{path} has no studies, duplicate studies or ragged rows")
    return {"header": rows[0], "uids": uids, "sha256": hashlib.sha256(raw).hexdigest()}


def validate_csv(template: dict, produced: Path) -> dict:
    rows, raw = read_rows(produced)
    if not rows or rows[0] != template["header"]:
        raise SetupError("the produced CSV header differs from the official template's")
    uids = [row[0] for row in rows[1:]]
    if uids != template["uids"]:
        raise SetupError(
            "the produced CSV study UIDs differ from the official template's, or are out of order"
        )
    for row in rows[1:]:
        if len(row) != len(rows[0]):
            raise SetupError(f"a produced row has {len(row)} cells, not {len(rows[0])}")
        for cell in row[1:]:
            try:
                value = Decimal(cell)
            except InvalidOperation as error:
                raise SetupError(
                    f"non-numeric probability {cell!r} for {row[0]}"
                ) from error
            if not value.is_finite() or value < 0 or value > 1:
                raise SetupError(f"probability {cell!r} for {row[0]} is outside [0, 1]")
    return {
        "rows": len(rows) - 1,
        "columns": len(rows[0]),
        "header_matches_template": True,
        "uids_match_in_order": True,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def is_breach_key(key: str) -> bool:
    return key in ("full_anatomy_runs", "full_reconstruction_runs") or key.endswith(
        "fallback_runs"
    )


def breach_values(node, path: str = "") -> list[tuple[str, int]]:
    found: list[tuple[str, int]] = []
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}/{key}"
            if (
                is_breach_key(str(key))
                and isinstance(value, int)
                and not isinstance(value, bool)
            ):
                found.append((here, value))
            found.extend(breach_values(value, here))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(breach_values(value, f"{path}[{index}]"))
    return found


def inspect_run_receipt(path: Path) -> dict:
    """Publication gate on the entry point's own receipt.json.

    The receipt must exist, and its authoritative `work.full_anatomy_runs` must be present and exactly 0;
    a missing receipt or counter is a refusal, not a warning. Any other full-anatomy / fallback counter
    found anywhere in the receipt must be 0 too. `work.bounded_zoom_runs` is the route's own work and
    is allowed. The receipt file itself stays whole under the retained output directory.
    """
    if not path.is_file():
        raise SetupError(
            f"the run wrote no receipt.json at {path}; full_anatomy_runs=0 is unproven"
        )
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise SetupError(f"run receipt.json is unreadable: {error}") from error
    work = document.get("work") if isinstance(document, dict) else None
    if not isinstance(work, dict) or "full_anatomy_runs" not in work:
        raise SetupError(
            f"run receipt.json has no authoritative work.full_anatomy_runs: {path}"
        )
    authoritative = work["full_anatomy_runs"]
    if isinstance(authoritative, bool) or not isinstance(authoritative, int):
        raise SetupError(
            f"work.full_anatomy_runs is not an integer count: {authoritative!r}"
        )
    if authoritative != 0:
        raise SetupError(
            f"the run reports work.full_anatomy_runs={authoritative}; production forbids it"
        )
    found = breach_values(document)
    nonzero = [(where, value) for where, value in found if value != 0]
    if nonzero:
        raise SetupError(
            f"the run reports full anatomy or fallback work, which production forbids: {nonzero}"
        )
    summary = {
        key: document[key]
        for key in (
            "schema",
            "action",
            "source_route",
            "memory_schema",
            "memory_revision",
            "study_count",
        )
        if key in document
    }
    return {
        "present": True,
        "path": str(path),
        "full_anatomy_runs": authoritative,
        "bounded_zoom_runs": work.get("bounded_zoom_runs"),
        "work": work,
        "full_anatomy_run_keys": [where for where, _ in found],
        "summary": summary,
        "sha256": sha256_file(path),
    }


def inventory(path: Path) -> dict:
    top: dict[str, dict] = {}
    files = total = 0
    with os.scandir(path) as scan:
        entries = sorted(scan, key=lambda entry: entry.name)
    for entry in entries:
        if entry.is_dir(follow_symlinks=False):
            count, size = tree_bytes(Path(entry.path))
        else:
            count, size = 1, entry.stat(follow_symlinks=False).st_size
        top[entry.name] = {"files": count, "bytes": size}
        files += count
        total += size
    return {"files": files, "bytes": total, "top_level": top}


def publish_submission(produced: Path, template: dict) -> dict:
    final = WORK / "submission.csv"
    part = WORK / ".submission.csv.part"
    shutil.copyfile(produced, part)
    os.replace(part, final)
    checked = validate_csv(template, final)
    if checked["sha256"] != sha256_file(produced):
        raise SetupError("published submission.csv differs from the produced one")
    return {"path": str(final), **checked}


# ---------------------------------------------------------------------------------------------
# The run
# ---------------------------------------------------------------------------------------------


def run() -> int:
    if LOCAL.exists():
        shutil.rmtree(LOCAL)
    for name in ("tmp", "numba-cache", "cwd"):
        (LOCAL / name).mkdir(parents=True)
    REPORT["environment"] = environment_facts()
    tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
    REPORT["wheel_tag"] = tag
    if tag != WHEEL_TAG:
        raise SetupError(
            f"interpreter is {tag}; this kernel installs only the locked {WHEEL_TAG} wheels"
        )

    with Step("locate_inputs"):
        REPORT.setdefault("inputs", {})["runtime_source_pin"] = {
            "expected_bundle_id": EXPECTED_RUNTIME_BUNDLE_ID,
            "expected_memory_manifest_sha256": EXPECTED_MEMORY_MANIFEST_SHA256,
        }
        runtime = select_runtime_manifest(find(MANIFEST_NAME), RUNTIME_HINT)
        manifest_path = runtime["manifest_path"]
        template_path = choose(
            find("sample_submission.csv"),
            COMPETITION_HINT,
            "official sample_submission.csv",
        )
        requirements = choose(
            find(f"requirements-{WHEEL_TAG}.txt"),
            WHEELS_HINT,
            "locked requirements file",
        )
        competition = template_path.parent
        template = read_template(template_path)
        REPORT["inputs"] = {
            "runtime_manifest": str(manifest_path),
            "runtime_manifest_selection": runtime["selection"],
            "runtime_source_pin": runtime["selection"]["source_pin"],
            "competition_root": str(competition),
            "sample_submission": str(template_path),
            "sample_submission_sha256": template["sha256"],
            "template_studies": len(template["uids"]),
            "test_series_present": (competition / "test_series").is_dir(),
        }

    with Step("copy_runtime_to_local_disk"):
        manifest = runtime["manifest"]
        bundle = LOCAL / "bundle"
        REPORT["runtime"] = {
            "bundle_id": manifest["bundle_id"],
            "expected_bundle_id": EXPECTED_RUNTIME_BUNDLE_ID,
            "expected_memory_manifest_sha256": EXPECTED_MEMORY_MANIFEST_SHA256,
            "actual_memory_manifest_sha256": memory_manifest_sha256(manifest),
            "dataset_id": manifest.get("dataset_id"),
            "memory": manifest["memory"],
            "source": {k: v for k, v in manifest["source"].items() if k != "excluded"},
            "warnings": manifest.get("warnings", []),
            "copy": materialise(manifest_path, manifest, bundle),
        }
        memory_path = bundle.joinpath(*PurePosixPath(manifest["memory"]["entry"]).parts)
        script = bundle.joinpath(*PurePosixPath(manifest["entrypoint"]).parts)

    with Step("install_locked_wheels_offline"):
        REPORT["install"] = install_wheels(requirements)
    env = child_env(LOCAL / "site", bundle, manifest)
    python = sys.executable

    with Step("import_check"):
        import_command = [python, "-c", IMPORT_CHECK, str(bundle), str(LOCAL / "site")]
        checked = subprocess.run(
            import_command,
            env=env,
            cwd=str(LOCAL / "cwd"),
            capture_output=True,
            text=True,
            check=False,
            timeout=900,
        )
        append_setup_log(
            "import check",
            import_command,
            checked.returncode,
            checked.stdout,
            checked.stderr,
        )
        REPORT["import_check"] = {
            "exit": checked.returncode,
            "stdout": checked.stdout,
            "stderr": checked.stderr,
            "setup_log": str(SETUP_LOG),
        }
        if checked.returncode != 0:
            raise SetupError(
                "the locked environment or the bundled code does not import"
            )
        help_command = [python, str(script), "--help"]
        helped = subprocess.run(
            help_command,
            env=env,
            cwd=str(LOCAL / "cwd"),
            capture_output=True,
            text=True,
            check=False,
            timeout=900,
        )
        append_setup_log(
            "entry point --help",
            help_command,
            helped.returncode,
            helped.stdout,
            helped.stderr,
        )
        REPORT["entrypoint_help_exit"] = helped.returncode
        REPORT["entrypoint_help_log"] = str(SETUP_LOG)
        if helped.returncode != 0:
            raise SetupError("scripts/run_interiors.py --help failed")

    if OUT_DIR.exists():
        raise SetupError(f"refusing to reuse an existing output directory: {OUT_DIR}")
    OUT_PARENT.mkdir(parents=True, exist_ok=True)
    limit = KAGGLE_LIMIT_S - RESERVE_S - (time.time() - STARTED)
    if limit <= 0:
        raise SetupError("no notebook runtime budget remains before inference launch")
    REPORT["time_budget_s"] = round(limit, 1)
    argv = [
        python,
        str(script),
        "--split",
        "test",
        "--root",
        str(competition),
        "--workers",
        str(WORKERS),
        "--diagnostic-mode",
        "infer",
        "--diagnostic-memory",
        str(memory_path),
        "--diagnostic-submission-template",
        str(template_path),
        "--diagnostic-output",
        str(OUT_DIR),
        "--squint-time-limit",
        str(limit),
    ]
    check_argv(argv)
    with Step("run_squint_inference"):
        info = run_logged(argv, env, LOCAL / "cwd", limit, OUT_PARENT)
        REPORT["run"] = info
        save()
    if info["timed_out"]:
        raise SetupError(
            "the run exceeded the time budget and was stopped; nothing is published"
        )
    if info["exit"] != 0:
        raise SetupError(
            f"the entry point exited {info['exit']}; no fallback output is written"
        )

    with Step("verify_and_publish"):
        produced = OUT_DIR / "submission.csv"
        if not produced.is_file():
            raise SetupError(
                "the run succeeded but did not produce the requested submission.csv"
            )
        REPORT["run_receipt"] = inspect_run_receipt(OUT_DIR / "receipt.json")
        REPORT["submission_check"] = validate_csv(template, produced)
        REPORT["published_submission"] = publish_submission(produced, template)
        retained = {}
        for name in ("receipt.json", "submission-receipt.json", "submission.csv"):
            candidate = OUT_DIR / name
            if candidate.is_file():
                retained[name] = {
                    "sha256": sha256_file(candidate),
                    "bytes": candidate.stat().st_size,
                }
        REPORT["retained"] = retained
        REPORT["evidence_inventory"] = inventory(OUT_DIR)
    return 0


def record_failure(error: BaseException) -> None:
    REPORT["status"] = "failed"
    REPORT["fatal"] = f"{type(error).__name__}: {error}"
    REPORT["traceback"] = traceback.format_exc()
    say(f"FAILED: {REPORT['fatal']}")


def main() -> int:
    code = 1
    try:
        code = run()
        REPORT["status"] = "completed"
    except SetupError as error:  # a named refusal: recorded in the receipt, exit code 1
        record_failure(error)
    except (
        BaseException
    ) as error:  # anything else is recorded in the receipt, then re-raised
        record_failure(error)
        raise
    finally:
        REPORT["finished_unix"] = time.time()
        REPORT["elapsed_s"] = round(time.time() - STARTED, 1)
        try:
            REPORT["disk_after"] = {
                str(path): shutil.disk_usage(path)._asdict()
                for path in (WORK, SCRATCH)
                if path.exists()
            }
            REPORT["work_tree_after"] = dict(
                zip(("files", "bytes"), tree_bytes(WORK), strict=True)
            )
        except OSError:
            pass
        save()
    say(f"status={REPORT['status']} elapsed={REPORT['elapsed_s']}s")
    return code


if __name__ == "__main__":
    sys.exit(main())
