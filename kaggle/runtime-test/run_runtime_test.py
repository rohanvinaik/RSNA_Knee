"""Run the RSNA knee production command on Kaggle hardware, offline.

Finds the private runtime dataset (production source, diagnostic memory,
locked Linux wheels), installs that locked closure into an isolated virtual
environment without network, then times the production CLI on the mounted
public test studies:

A. the current diagnostic route, one study at a time, writing the validated
   submission.csv (wiring/timing only; the bundled memory is a smoke memory);
B. recognition with complete object encoding, studies across worker processes.

Each run's exit code, wall time, peak child memory, output bytes and log tails
go to /kaggle/working/runtime-test.json. Nothing is downloaded or submitted.
"""

from __future__ import annotations

import csv
import json
import os
import resource
import shutil
import subprocess
import sys
import tarfile
import time
from pathlib import Path

WORK = Path("/kaggle/working")
SCRATCH = Path("/kaggle/tmp") if Path("/kaggle/tmp").exists() else Path("/tmp")
ROOT = SCRATCH / "rsna-runtime"
REPORT: dict = {
    "started_unix": time.time(),
    "python": sys.version,
    "scratch": str(SCRATCH),
}


def save():
    REPORT["saved_unix"] = time.time()
    (WORK / "runtime-test.json").write_text(json.dumps(REPORT, indent=2, default=str))


SKIP_DIRS = {"train_series", "test_series", "source", "wheels", "memory"}


def find(name, base=Path("/kaggle/input"), depth=5):
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


def tree_bytes(path):
    total = 0
    for item in Path(path).rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


def run(name, cmd, env, timeout):
    started = time.perf_counter()
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    try:
        done = subprocess.run(
            cmd, env=env, capture_output=True, text=True, timeout=timeout, check=False
        )
        rc, out, err = done.returncode, done.stdout, done.stderr
    except subprocess.TimeoutExpired as exc:
        rc, out, err = "timeout", str(exc.stdout or ""), str(exc.stderr or "")
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    entry = {
        "cmd": cmd,
        "exit": rc,
        "wall_s": round(time.perf_counter() - started, 2),
        "children_user_s": round(after.ru_utime - before.ru_utime, 2),
        "children_sys_s": round(after.ru_stime - before.ru_stime, 2),
        "max_child_rss_kib_so_far": after.ru_maxrss,
        "stdout_tail": out[-8000:],
        "stderr_tail": err[-8000:],
    }
    REPORT.setdefault("runs", {})[name] = entry
    save()
    print(f"[{name}] exit={rc} wall={entry['wall_s']}s", flush=True)
    return entry


def cold_reads(comp):
    """Time first reads of training DICOMs: one study serially, others threaded.

    The hidden test is read from the same mount, so how first-open latency
    behaves under concurrency decides how reads must be scheduled.
    """
    from concurrent.futures import ThreadPoolExecutor

    with (comp / "train.csv").open() as handle:
        rows = [line.split(",", 1)[0] for line in handle.read().splitlines()[1:12]]
    studies = [
        comp / "train_series" / uid
        for uid in rows
        if (comp / "train_series" / uid).is_dir()
    ]
    out = {}

    def files_of(study):
        return sorted(f for series in sorted(study.iterdir()) for f in series.iterdir())

    def read_all(paths):
        total = 0
        for path in paths:
            total += len(path.read_bytes())
        return total

    if studies:
        paths = files_of(studies[0])
        started = time.perf_counter()
        size = read_all(paths)
        out["serial"] = {
            "files": len(paths),
            "bytes": size,
            "seconds": round(time.perf_counter() - started, 2),
        }
    for workers, study in zip((8, 32), studies[1:3], strict=False):
        paths = files_of(study)
        started = time.perf_counter()
        with ThreadPoolExecutor(workers) as pool:
            size = sum(pool.map(lambda p: len(p.read_bytes()), paths))
        out[f"threads_{workers}"] = {
            "files": len(paths),
            "bytes": size,
            "seconds": round(time.perf_counter() - started, 2),
        }
    REPORT["cold_reads"] = out
    save()


def main():
    manifests = find("RUNTIME_MANIFEST.json")
    tars = find("runtime-bundle.tar")
    if ROOT.exists():
        shutil.rmtree(ROOT)
    ROOT.mkdir(parents=True)
    if manifests:
        bundle = manifests[0].parent
        REPORT["bundle_mode"] = f"extracted directory {bundle}"
    elif tars:
        started = time.perf_counter()
        with tarfile.open(tars[0]) as archive:
            try:
                archive.extractall(ROOT / "bundle", filter="data")
            except TypeError:  # Pythons before the extraction-filter backport
                archive.extractall(ROOT / "bundle")
        bundle = ROOT / "bundle"
        REPORT["bundle_mode"] = (
            f"tar {tars[0]} extracted in {time.perf_counter() - started:.1f}s"
        )
    else:
        REPORT["fatal"] = "runtime bundle not found under /kaggle/input"
        save()
        return
    REPORT["bundle_manifest"] = json.loads(
        (bundle / "RUNTIME_MANIFEST.json").read_text()
    )

    competition = [p.parent for p in find("sample_submission.csv")]
    REPORT["competition_roots"] = [str(p) for p in competition]
    if not competition:
        REPORT["fatal"] = "competition data not mounted"
        save()
        return
    comp = competition[0]

    tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
    found = find(f"requirements-{tag}.txt")
    REPORT["wheel_tag"] = tag
    if not found:
        REPORT["fatal"] = f"no requirements-{tag}.txt in any attached input"
        save()
        return
    requirements = found[0]
    shipped = requirements.parent / "wheels" / tag
    if not shipped.exists():
        REPORT["fatal"] = f"no wheels/{tag} beside {requirements}"
        save()
        return
    cold_reads(comp)
    wheels = ROOT / "wheels"
    wheels.mkdir()
    for wheel in shipped.iterdir():
        if wheel.name.endswith(".whl") and not wheel.name.startswith("._"):
            shutil.copy(wheel, wheels / wheel.name)
    REPORT["wheels"] = sorted(p.name for p in wheels.iterdir())

    venv = ROOT / "venv"
    started = time.perf_counter()
    made = subprocess.run(
        [sys.executable, "-m", "venv", str(venv)],
        capture_output=True,
        text=True,
        check=False,
    )
    REPORT["venv_create"] = {"exit": made.returncode, "err": made.stderr[-2000:]}
    python = venv / "bin" / "python"
    if made.returncode == 0 and python.exists():
        install = subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--find-links",
                str(wheels),
                "-r",
                str(requirements),
                "--disable-pip-version-check",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        REPORT["install"] = {
            "route": "venv",
            "exit": install.returncode,
            "err": install.stderr[-4000:],
            "seconds": round(time.perf_counter() - started, 1),
        }
        pythonpath = [str(bundle / "source" / "src")]
    else:
        site = ROOT / "site"
        install = subprocess.run(
            [
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
                "--quiet",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        REPORT["install"] = {
            "route": "target",
            "exit": install.returncode,
            "err": install.stderr[-4000:],
            "seconds": round(time.perf_counter() - started, 1),
        }
        python = Path(sys.executable)
        pythonpath = [str(site), str(bundle / "source" / "src")]
    save()
    if install.returncode != 0:
        REPORT["fatal"] = "offline install failed"
        save()
        return

    env = dict(os.environ)
    env.update(
        {
            "PYTHONPATH": os.pathsep.join(pythonpath),
            "PYTHONDONTWRITEBYTECODE": "1",
            "NUMBA_CACHE_DIR": str(ROOT / "numba-cache"),
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "NUMEXPR_NUM_THREADS": "1",
            "NUMBA_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
        }
    )
    check = (
        "import sys, numpy, scipy, skimage, pydicom, gdcm, numba, h5py; "
        "import knee.diagnosis.pipeline, knee.encoding.operation; "
        "print(sys.version); print(numpy.__version__, scipy.__version__, skimage.__version__, "
        "pydicom.__version__, numba.__version__, h5py.__version__)"
    )
    run("imports", [str(python), "-c", check], env, 600)

    script = str(bundle / "source" / "scripts" / "run_interiors.py")
    memory = str(bundle / "memory")
    template = str(comp / "sample_submission.csv")

    out_a = ROOT / "route-a"
    a = run(
        "A_diagnostic_serial",
        [
            str(python),
            script,
            "--split",
            "test",
            "--root",
            str(comp),
            "--workers",
            "1",
            "--diagnostic-mode",
            "infer",
            "--diagnostic-memory",
            memory,
            "--diagnostic-submission-template",
            template,
            "--diagnostic-output",
            str(out_a / "diagnostics"),
        ],
        env,
        5400,
    )
    a["output_bytes"] = tree_bytes(out_a) if out_a.exists() else 0
    produced = out_a / "diagnostics" / "submission.csv"
    if produced.exists():
        with produced.open() as handle:
            rows = list(csv.reader(handle))
        with open(template) as handle:
            sample = list(csv.reader(handle))
        a["submission_check"] = {
            "header_matches": rows[0] == sample[0],
            "uids_match_in_order": [r[0] for r in rows[1:]]
            == [r[0] for r in sample[1:]],
            "rows": len(rows) - 1,
        }
        shutil.copy(produced, WORK / "submission.csv")
    for receipt in (out_a / "diagnostics").glob("*receipt*.json"):
        shutil.copy(receipt, WORK / f"route-a-{receipt.name}")
    save()

    out_b = ROOT / "route-b"
    workers = str(min(4, max(1, (os.cpu_count() or 1))))
    b = run(
        "B_recognition_encoding_parallel",
        [
            str(python),
            script,
            "--split",
            "test",
            "--root",
            str(comp),
            "--workers",
            workers,
            "--competition-output",
            "--run",
            str(out_b / "interiors"),
            "--main-run",
            str(out_b / "main"),
            "--encoding-run",
            str(out_b / "encoding"),
        ],
        env,
        5400,
    )
    b["workers"] = workers
    b["output_bytes"] = tree_bytes(out_b) if out_b.exists() else 0
    for receipt in out_b.rglob("receipt.json"):
        shutil.copy(receipt, WORK / f"route-b-{receipt.parent.name}-receipt.json")
    REPORT["disk_after"] = {
        str(p): shutil.disk_usage(p)._asdict() for p in (WORK, SCRATCH) if p.exists()
    }
    REPORT["elapsed_s"] = round(time.time() - REPORT["started_unix"], 1)
    save()
    print(json.dumps({k: REPORT.get(k) for k in ("install", "elapsed_s")}, default=str))


if __name__ == "__main__":
    try:
        main()
    finally:
        save()
