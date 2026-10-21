"""Kaggle hardware and workability probe for the RSNA knee pipeline.

Runs offline in a private Kaggle script kernel with the competition data
attached. It records the machine (CPU, memory, disk, limits), the Python
environment and installed package versions, where the competition data is
mounted, how the public test DICOMs decode under each transfer syntax with the
packages already present, a few fixed micro-benchmarks for comparing this
machine with a local one, and the time of exact whole-number cosine terms at
the scale of a diagnostic memory. It installs nothing, uses no network, and
writes /kaggle/working/probe.json plus a short printed summary.
"""

from __future__ import annotations

import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import traceback
from collections import Counter, defaultdict
from importlib import metadata
from pathlib import Path

OUT = Path("/kaggle/working") if Path("/kaggle/working").exists() else Path.cwd()
RESULT: dict = {"started_unix": time.time()}

PACKAGES = (
    "numpy",
    "scipy",
    "scikit-image",
    "pydicom",
    "python-gdcm",
    "gdcm",
    "pylibjpeg",
    "pylibjpeg-libjpeg",
    "pylibjpeg-openjpeg",
    "dicomsdl",
    "imagecodecs",
    "SimpleITK",
    "numba",
    "llvmlite",
    "h5py",
    "pillow",
    "pandas",
    "networkx",
    "tifffile",
    "imageio",
    "lazy-loader",
    "packaging",
)
DECODER_MODULES = (
    "gdcm",
    "pylibjpeg",
    "libjpeg",
    "openjpeg",
    "dicomsdl",
    "imagecodecs",
    "PIL",
)


def section(name):
    """Run one probe section; keep its result or its error, never stop."""

    def wrap(func):
        started = time.perf_counter()
        try:
            RESULT[name] = func()
        except Exception as exc:  # noqa: BLE001 - the probe records any failure; it never aborts
            RESULT[name] = {
                "error": f"{type(exc).__name__}: {exc}",
                "trace": traceback.format_exc()[-2000:],
            }
        RESULT.setdefault("section_seconds", {})[name] = round(
            time.perf_counter() - started, 3
        )
        return func

    return wrap


def run(cmd, timeout=60):
    try:
        done = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
        return {
            "exit": done.returncode,
            "out": done.stdout[-6000:],
            "err": done.stderr[-2000:],
        }
    except Exception as exc:  # noqa: BLE001 - recorded, never raised
        return {"error": f"{type(exc).__name__}: {exc}"}


def read(path):
    try:
        return Path(path).read_text().strip()
    except Exception as exc:  # noqa: BLE001 - recorded, never raised
        return f"unavailable ({type(exc).__name__})"


@section("environment")
def _environment():
    getaffinity = getattr(os, "sched_getaffinity", None)
    affinity = sorted(getaffinity(0)) if getaffinity is not None else None
    return {
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "os_cpu_count": os.cpu_count(),
        "affinity_count": len(affinity) if affinity is not None else None,
        "env": {
            k: v
            for k, v in os.environ.items()
            if k.startswith(("KAGGLE", "OMP", "MKL", "OPENBLAS", "NUMBA", "PYTHON"))
            and not any(
                s in k for s in ("TOKEN", "SECRET", "KEY", "PASSWORD", "CREDENTIAL")
            )
        },
        "cwd": str(Path.cwd()),
    }


@section("cpu")
def _cpu():
    models = Counter()
    flags = set()
    for line in read("/proc/cpuinfo").splitlines():
        if line.startswith("model name"):
            models[line.split(":", 1)[1].strip()] += 1
        elif line.startswith("flags") and not flags:
            flags = set(line.split(":", 1)[1].split())
    return {
        "models": dict(models),
        "simd": {
            f: (f in flags)
            for f in ("sse4_2", "avx", "avx2", "fma", "avx512f", "avx512bw")
        },
        "lscpu": run(["lscpu"]),
        "nproc": run(["nproc"]),
    }


@section("limits")
def _limits():
    meminfo = {}
    for line in read("/proc/meminfo").splitlines():
        key, _, value = line.partition(":")
        if key in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
            meminfo[key] = value.strip()
    return {
        "meminfo": meminfo,
        "cgroup_v2": {
            name: read(f"/sys/fs/cgroup/{name}")
            for name in ("cpu.max", "memory.max", "memory.high", "pids.max")
        },
        "cgroup_v1": {
            name: read(f"/sys/fs/cgroup/{name}")
            for name in (
                "cpu/cpu.cfs_quota_us",
                "cpu/cpu.cfs_period_us",
                "memory/memory.limit_in_bytes",
            )
        },
        "ulimit": run(["bash", "-c", "ulimit -a"]),
    }


@section("disk")
def _disk():
    usage = {}
    for mount in (
        "/kaggle/working",
        "/kaggle/tmp",
        "/kaggle/temp",
        "/tmp",
        "/",
        "/kaggle/input",
        "/dev/shm",
    ):
        if Path(mount).exists():
            total, used, free = shutil.disk_usage(mount)
            usage[mount] = {"total": total, "used": used, "free": free}
    return {"usage": usage, "df": run(["df", "-B1"])}


@section("gpu")
def _gpu():
    return {"nvidia_smi": shutil.which("nvidia-smi") is not None}


@section("packages")
def _packages():
    wanted = {}
    for name in PACKAGES:
        try:
            wanted[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            wanted[name] = None
    importable = {}
    for module in DECODER_MODULES:
        try:
            importlib.import_module(module)
            importable[module] = True
        except Exception as exc:  # noqa: BLE001 - recorded, never raised
            importable[module] = f"{type(exc).__name__}: {exc}"[:200]
    every = sorted(
        {
            (d.metadata["Name"] or "?").lower(): d.version
            for d in metadata.distributions()
        }.items()
    )
    return {
        "wanted": wanted,
        "decoder_modules_importable": importable,
        "all_distributions": dict(every),
        "pip_count": len(every),
    }


SKIP_DIRS = {"train_series", "test_series"}


def shallow_find(name, base=Path("/kaggle/input"), depth=4):
    """Find a file by name a few levels down, never walking the image folders."""
    hits, level = [], [base] if base.exists() else []
    for _ in range(depth):
        nxt = []
        for folder in level:
            try:
                entries = sorted(folder.iterdir())
            except OSError:
                continue
            for entry in entries:
                if entry.name == name and entry.is_file():
                    hits.append(entry)
                elif entry.is_dir() and entry.name not in SKIP_DIRS:
                    nxt.append(entry)
        level = nxt
    return hits


def find_competition_root():
    return [path.parent for path in shallow_find("sample_submission.csv")]


@section("mount")
def _mount():
    base = Path("/kaggle/input")
    listing = []
    if base.exists():
        for path in sorted(base.iterdir()):
            listing.append(str(path))
            if path.is_dir():
                for child in sorted(path.iterdir())[:20]:
                    listing.append(str(child))
    roots = find_competition_root()
    detail = {}
    for root in roots:
        test_series = root / "test_series"
        files = sorted(test_series.rglob("*.dcm")) if test_series.exists() else []
        detail[str(root)] = {
            "entries": sorted(p.name for p in root.iterdir())[:40],
            "test_csv": read(root / "test.csv")[:2000],
            "test_series_csv_rows": len(read(root / "test_series.csv").splitlines()),
            "test_dicom_files": len(files),
            "test_studies": len({f.parts[len(test_series.parts)] for f in files}),
            "train_series_present": (root / "train_series").exists(),
        }
    return {
        "input_listing": listing,
        "competition_roots": [str(r) for r in roots],
        "detail": detail,
    }


@section("dicom_decode")
def _dicom_decode():
    import pydicom

    roots = find_competition_root()
    if not roots:
        return {"error": "no competition root found"}
    files = sorted((roots[0] / "test_series").rglob("*.dcm"))
    by_syntax = defaultdict(
        lambda: {
            "files": 0,
            "decoded": 0,
            "failed": 0,
            "first_error": None,
            "read_seconds": 0.0,
            "decode_seconds": 0.0,
            "shapes": Counter(),
        }
    )
    for path in files:
        started = time.perf_counter()
        ds = pydicom.dcmread(path)
        read_s = time.perf_counter() - started
        syntax = str(getattr(ds.file_meta, "TransferSyntaxUID", "unknown"))
        name = getattr(getattr(ds.file_meta, "TransferSyntaxUID", None), "name", syntax)
        entry = by_syntax[f"{syntax} {name}"]
        entry["files"] += 1
        entry["read_seconds"] += read_s
        started = time.perf_counter()
        try:
            array = ds.pixel_array
            entry["decoded"] += 1
            entry["shapes"][f"{array.shape}:{array.dtype}"] += 1
        except Exception as exc:  # noqa: BLE001 - recorded, never raised
            entry["failed"] += 1
            if entry["first_error"] is None:
                entry["first_error"] = f"{type(exc).__name__}: {exc}"[:600]
        entry["decode_seconds"] += time.perf_counter() - started
    out = {}
    for key, entry in by_syntax.items():
        entry = dict(entry)
        entry["shapes"] = dict(entry["shapes"])
        entry["read_seconds"] = round(entry["read_seconds"], 3)
        entry["decode_seconds"] = round(entry["decode_seconds"], 3)
        out[key] = entry
    return {
        "pydicom": pydicom.__version__,
        "files": len(files),
        "by_transfer_syntax": out,
    }


@section("micro_benchmarks")
def _micro():
    import numpy as np
    from scipy import ndimage

    results = {}
    started = time.perf_counter()
    total = 0
    for i in range(3_000_000):
        total += i * i
    results["python_loop_3e6_s"] = round(time.perf_counter() - started, 4)

    rng = np.random.default_rng(20261021)
    image = rng.random((512, 512))
    mask = image > 0.5
    for name, func in (
        ("edt_512_s", lambda: ndimage.distance_transform_edt(mask)),
        ("median5_512_s", lambda: ndimage.median_filter(image, size=5)),
        ("label_512_s", lambda: ndimage.label(mask)),
        ("sort_4e6_s", lambda: np.sort(rng.random(4_000_000))),
    ):
        best = float("inf")
        for _ in range(3):
            started = time.perf_counter()
            func()
            elapsed = time.perf_counter() - started
            best = min(best, elapsed)
        results[name] = round(best, 5)
    try:
        from skimage.segmentation import watershed

        markers = ndimage.label(image > 0.97)[0]
        started = time.perf_counter()
        watershed(image, markers)
        results["watershed_512_s"] = round(time.perf_counter() - started, 5)
    except Exception as exc:  # noqa: BLE001 - recorded, never raised
        results["watershed_512_s"] = f"{type(exc).__name__}: {exc}"[:200]
    return results


@section("cosine_terms")
def _cosine_terms():
    """Exact whole-number dot and norm terms of one query against stored cases.

    Shapes are illustrative of a diagnostic memory: a question selects a few
    thousand expanded banks of three rows each, and each case speaks in a
    sparse subset. Dense and sparse forms give identical integer terms.
    """
    import numpy as np

    rng = np.random.default_rng(7)
    cases, dims, nnz = 2000, 8400 * 3, 600
    dense = np.zeros((cases, dims), dtype=np.int64)
    rows = np.repeat(np.arange(cases), nnz)
    cols = rng.integers(0, dims, size=cases * nnz)
    np.add.at(dense, (rows, cols), rng.integers(1, 400, size=cases * nnz))
    query = np.zeros(dims, dtype=np.int64)
    query[rng.integers(0, dims, size=nnz)] = rng.integers(1, 400, size=nnz)
    norms = np.einsum("ij,ij->i", dense, dense)

    dots = dense @ query
    started = time.perf_counter()
    for _ in range(5):
        dots = dense @ query
    dense_s = (time.perf_counter() - started) / 5

    indptr = np.zeros(cases + 1, dtype=np.int64)
    indices, values = [], []
    for i in range(cases):
        nz = np.flatnonzero(dense[i])
        indices.append(nz)
        values.append(dense[i, nz])
        indptr[i + 1] = indptr[i] + nz.size
    indices = np.concatenate(indices)
    values = np.concatenate(values)
    out = {
        "cases": cases,
        "dims": dims,
        "nnz_per_case": nnz,
        "dense_numpy_query_s": round(dense_s, 5),
    }
    try:
        import numba

        @numba.njit(cache=False)
        def sparse_dots(indptr, indices, values, query):
            result = np.zeros(indptr.size - 1, dtype=np.int64)
            for i in range(indptr.size - 1):
                acc = 0
                for k in range(indptr[i], indptr[i + 1]):
                    acc += values[k] * query[indices[k]]
                result[i] = acc
            return result

        started = time.perf_counter()
        first = sparse_dots(indptr, indices, values, query)
        compile_s = time.perf_counter() - started
        sparse = first
        started = time.perf_counter()
        for _ in range(50):
            sparse = sparse_dots(indptr, indices, values, query)
        sparse_s = (time.perf_counter() - started) / 50
        out.update(
            {
                "numba": numba.__version__,
                "numba_compile_plus_first_s": round(compile_s, 4),
                "numba_sparse_query_s": round(sparse_s, 6),
                "dense_equals_sparse": bool(
                    np.array_equal(dots, sparse) and np.array_equal(first, sparse)
                ),
                "terms_for_1300_studies_x_12_questions_s": round(
                    sparse_s * 1300 * 12, 2
                ),
            }
        )
    except Exception as exc:  # noqa: BLE001 - recorded, never raised
        out["numba_error"] = f"{type(exc).__name__}: {exc}"[:400]
    out["norms_checksum"] = int(norms.sum() % 1_000_003)
    return out


RESULT["finished_unix"] = time.time()
RESULT["elapsed_s"] = round(RESULT["finished_unix"] - RESULT["started_unix"], 2)
(OUT / "probe.json").write_text(json.dumps(RESULT, indent=2, default=str))

summary = {
    "python": RESULT.get("environment", {}).get("python", "?").split()[0],
    "cpus": RESULT.get("environment", {}).get("os_cpu_count"),
    "cpu_models": RESULT.get("cpu", {}).get("models"),
    "mem": RESULT.get("limits", {}).get("meminfo"),
    "roots": RESULT.get("mount", {}).get("competition_roots"),
    "decoders": RESULT.get("packages", {}).get("decoder_modules_importable"),
    "wanted": RESULT.get("packages", {}).get("wanted"),
    "decode": {
        k: (v.get("files"), v.get("decoded"), v.get("first_error"))
        for k, v in RESULT.get("dicom_decode", {}).get("by_transfer_syntax", {}).items()
    },
    "micro": RESULT.get("micro_benchmarks"),
    "cosine": RESULT.get("cosine_terms"),
    "elapsed_s": RESULT["elapsed_s"],
}
print(json.dumps(summary, indent=2, default=str))
