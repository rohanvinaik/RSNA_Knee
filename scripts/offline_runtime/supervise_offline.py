#!/usr/bin/env python3
"""Run one bounded, network-isolated CLI case and record host/container evidence."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_MEMORY_BYTES = 24_000_000_000
DEFAULT_OUTPUT_BUDGET_BYTES = 20_000_000_000

THREAD_ENV = (
    "OMP_NUM_THREADS=1",
    "OPENBLAS_NUM_THREADS=1",
    "MKL_NUM_THREADS=1",
    "NUMBA_NUM_THREADS=1",
    "NUMEXPR_NUM_THREADS=1",
    "BLIS_NUM_THREADS=1",
    # multiprocessing forkserver sockets need chmod semantics provided by the
    # container tmpfs; persistent cache material stays on the scratch mount.
    "TMPDIR=/tmp",
    "XDG_CACHE_HOME=/scratch/cache",
    # Fixed container cache location, not an authentication value.
    "NUMBA_CACHE_DIR=/scratch/numba-cache",  # pragma: allowlist secret
)

WRAPPER = r"""set +e
python /app/scripts/run_interiors.py "$@"
status=$?
printf '%s\n' "$status" > /out/.cli-exit
while [ ! -e /out/.release-container ]; do sleep 0.2; done
exit "$status"
"""
CGROUP_READ = r"""for p in memory.peak memory.current memory.max memory.stat memory.events memory.swap.peak memory.swap.current cpu.max cpu.stat pids.current pids.max; do
  if [ -r "/sys/fs/cgroup/$p" ]; then
    printf '%s=' "$p"
    tr '\n' ',' < "/sys/fs/cgroup/$p"
    printf '\n'
  else
    printf '%s=unavailable\n' "$p"
  fi
done"""


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def run(
    command: list[str], *, timeout: float = 15.0
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command, check=False, capture_output=True, text=True, timeout=timeout
    )


def folder_size(root: Path) -> tuple[int, int]:
    total = 0
    files = 0
    if root.exists():
        for directory, _, names in os.walk(root):
            for name in names:
                path = Path(directory) / name
                try:
                    total += path.stat().st_size
                    files += 1
                except FileNotFoundError:
                    continue
    return total, files


def filesystem_capacity(path: Path) -> dict[str, int | str]:
    """Report host-visible filesystem capacity; this does not establish a hard quota."""
    stats = os.statvfs(path)
    block = stats.f_frsize or stats.f_bsize
    return {
        "path": str(path),
        "total_bytes": int(block * stats.f_blocks),
        "free_bytes": int(block * stats.f_bfree),
        "available_bytes": int(block * stats.f_bavail),
    }


def validate_resource_limits(
    memory_bytes: int,
    output_budget_bytes: int,
    interval: float,
    timeout_seconds: float,
) -> None:
    if (
        isinstance(memory_bytes, bool)
        or not isinstance(memory_bytes, int)
        or memory_bytes <= 0
    ):
        raise ValueError("--memory-bytes must be a positive integer")
    if (
        isinstance(output_budget_bytes, bool)
        or not isinstance(output_budget_bytes, int)
        or output_budget_bytes <= 0
    ):
        raise ValueError("--output-budget-bytes must be a positive integer")
    if not math.isfinite(interval) or interval <= 0:
        raise ValueError("--interval must be positive and finite")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be positive and finite")


def docker_vm_memory_total() -> tuple[int | None, str | None]:
    result = run(["docker", "info", "--format", "{{.MemTotal}}"])
    if result.returncode != 0:
        return None, result.stderr.strip() or "docker_info_unavailable"
    try:
        value = int(result.stdout.strip())
    except ValueError:
        return None, f"unparseable_docker_vm_memory_total:{result.stdout.strip()}"
    return (value, None) if value > 0 else (None, "invalid_docker_vm_memory_total")


def output_budget_exceeded(output_bytes: int, budget_bytes: int) -> bool:
    return output_bytes > budget_bytes


def positive_integer(value: str) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if number <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def human_bytes(value: str) -> int | None:
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([KMGT]?i?B)", value, re.IGNORECASE)
    if match is None:
        return None
    number = float(match.group(1))
    unit = match.group(2).upper()
    scale = 1024 if "I" in unit else 1000
    prefix = unit[0]
    power = {"B": 0, "K": 1, "M": 2, "G": 3, "T": 4}[prefix]
    return int(number * (scale**power))


def get_stats(name: str) -> dict[str, Any] | None:
    template = "{{.CPUPerc}}|{{.MemUsage}}|{{.PIDs}}|{{.BlockIO}}"
    result = run(["docker", "stats", "--no-stream", "--format", template, name])
    if result.returncode != 0:
        return None
    fields = result.stdout.strip().split("|", 3)
    if len(fields) != 4:
        return {"raw": result.stdout.strip()}
    memory = fields[1].split("/", 1)[0].strip()
    return {
        "cpu_percent": fields[0].strip(),
        "memory_raw": fields[1].strip(),
        "memory_used_bytes": human_bytes(memory),
        "pids": fields[2].strip(),
        "block_io": fields[3].strip(),
    }


def case_arguments(
    case: str,
    workers: int = 4,
    *,
    encode_objects: bool = False,
    competition_output: bool = False,
) -> list[str]:
    if case == "proof-bursa-parallel":
        args = [
            "--study-uid",
            "1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149",
            "1.2.826.0.1.3680043.8.498.13335129881737731410081002627729200903",
            "--workers",
            str(workers),
        ]
    elif case == "public-test":
        args = ["--split", "test", "--workers", str(workers)]
    elif case == "labeled-cohort":
        args = ["--labeled", "--workers", str(workers)]
    else:
        raise ValueError(f"unsupported case: {case}")
    if not isinstance(encode_objects, bool):
        raise TypeError("encode_objects_must_be_bool")
    if not isinstance(competition_output, bool):
        raise TypeError("competition_output_must_be_bool")
    if competition_output:
        # --competition-output implies the built-in H5 encoder; no duplicate flag.
        args.extend(("--competition-output", "--encoding-run", "/out/encoding"))
    elif encode_objects:
        args.extend(("--encode-objects", "--encoding-run", "/out/encoding"))
    return args


def inspect_image(image_ref: str) -> dict[str, Any]:
    result = run(
        [
            "docker",
            "image",
            "inspect",
            "--format",
            "{{.Id}}|{{.Os}}|{{.Architecture}}|{{json .RepoDigests}}|{{json .Config.Labels}}|{{json .Config.Env}}",
            image_ref,
        ]
    )
    if result.returncode != 0:
        raise RuntimeError(f"image inspect failed: {result.stderr.strip()}")
    parts = result.stdout.strip().split("|", 5)
    if len(parts) != 6:
        raise RuntimeError(f"unexpected image inspect output: {result.stdout!r}")
    info = {
        "image_id": parts[0],
        "os": parts[1],
        "architecture": parts[2],
        "repo_digests": json.loads(parts[3]),
        "labels": json.loads(parts[4]),
        "image_environment": json.loads(parts[5]),
    }
    if info["os"] != "linux" or info["architecture"] != "amd64":
        raise RuntimeError(f"wrong image platform: {info['os']}/{info['architecture']}")
    return info


def validate_pins(
    manifest: dict[str, Any],
    build: dict[str, Any],
    image: dict[str, Any],
    expected_image_id: str,
) -> str:
    if image.get("image_id") != expected_image_id:
        raise RuntimeError(
            f"image id mismatch: {image.get('image_id')} != {expected_image_id}"
        )
    labels = image.get("labels", {})
    if build.get("source_tree_sha256") != manifest.get("source_tree_sha256"):
        raise RuntimeError("build metadata/source manifest tree hash mismatch")
    if build.get("source_revision") != manifest.get("source_revision"):
        raise RuntimeError("build metadata/source manifest revision mismatch")
    if labels.get("org.rsna-knee.source-tree-sha256") != manifest.get(
        "source_tree_sha256"
    ):
        raise RuntimeError("image/source manifest tree hash mismatch")
    if labels.get("org.opencontainers.image.revision") != manifest.get(
        "source_revision"
    ):
        raise RuntimeError("image/source manifest revision mismatch")
    base_image = build.get("base_image")
    if not isinstance(base_image, str) or "@sha256:" not in base_image:
        raise RuntimeError("build metadata has no digest-pinned base image")
    return base_image.rsplit("@sha256:", 1)[1]


def run_case(
    case: str,
    *,
    data_root: Path,
    output_root: Path,
    scratch_root: Path,
    context: Path,
    build_metadata_path: Path,
    image_ref: str,
    expected_image_id: str,
    workers: int,
    interval: float,
    timeout_seconds: float,
    memory_bytes: int = DEFAULT_MEMORY_BYTES,
    output_budget_bytes: int = DEFAULT_OUTPUT_BUDGET_BYTES,
    encode_objects: bool = False,
    competition_output: bool = False,
) -> dict[str, Any]:
    if not isinstance(encode_objects, bool):
        raise TypeError("encode_objects_must_be_bool")
    if not isinstance(competition_output, bool):
        raise TypeError("competition_output_must_be_bool")
    validate_resource_limits(
        memory_bytes, output_budget_bytes, interval, timeout_seconds
    )
    if data_root.is_symlink():
        raise RuntimeError(f"data root must not be a symlink: {data_root}")
    data_root = data_root.resolve(strict=True)
    if not data_root.is_dir():
        raise RuntimeError(f"data root is not a directory: {data_root}")
    output_root = output_root.resolve()
    scratch_root = scratch_root.resolve()
    if (
        output_root == scratch_root
        or output_root in scratch_root.parents
        or scratch_root in output_root.parents
    ):
        raise RuntimeError(
            "output and scratch roots must be distinct, non-nested paths"
        )
    if output_root.exists() or scratch_root.exists():
        raise RuntimeError(f"refusing non-fresh roots: {output_root}, {scratch_root}")

    context = context.resolve(strict=True)
    build_metadata_path = build_metadata_path.resolve(strict=True)
    manifest = json.loads((context / "source-manifest.json").read_text())
    build = json.loads(build_metadata_path.read_text())
    image = inspect_image(image_ref)
    base_digest = validate_pins(manifest, build, image, expected_image_id)

    output_root.parent.mkdir(parents=True, exist_ok=True)
    scratch_root.parent.mkdir(parents=True, exist_ok=True)
    output_root.mkdir()
    scratch_root.mkdir()
    for subdir in ("cache", "numba-cache"):
        (scratch_root / subdir).mkdir()

    filesystem_capacity_start = {
        "input": filesystem_capacity(data_root),
        "output": filesystem_capacity(output_root),
        "scratch": filesystem_capacity(scratch_root),
        "hard_quota": "unknown_not_enforced_by_supervisor",
    }
    docker_memory_total, docker_memory_error = docker_vm_memory_total()

    source_tree = manifest["source_tree_sha256"]

    name = f"rsna-knee-runtime-{case}-{os.getpid()}"
    if run(["docker", "inspect", name]).returncode == 0:
        raise RuntimeError(f"container name already exists: {name}")
    # Competition mode puts consumed intermediate work on measured scratch;
    # the retained final encoding stays under /out/encoding.
    recognition_run = "/scratch/interiors" if competition_output else "/out/interiors"
    main_run = "/scratch/main" if competition_output else "/out/main"
    intermediate_base = scratch_root if competition_output else output_root
    cli_args = case_arguments(
        case,
        workers,
        encode_objects=encode_objects,
        competition_output=competition_output,
    ) + [
        "--root",
        "/data",
        "--run",
        recognition_run,
        "--main-run",
        main_run,
        "--out",
        "/out/pictures/interiors",
        "--assignments-out",
        "/out/pictures/assignments",
        "--main-out",
        "/out/pictures/main-slices",
    ]
    docker_args = [
        "docker",
        "run",
        "--name",
        name,
        "--platform",
        "linux/amd64",
        "--network",
        "none",
        "--cpus",
        "4",
        "--memory",
        str(memory_bytes),
        "--memory-swap",
        str(memory_bytes),
        "--read-only",
        "--tmpfs",
        "/tmp:rw,nosuid,nodev,size=512m",
        "--mount",
        f"type=bind,src={data_root},dst=/data,readonly",
        "--mount",
        f"type=bind,src={output_root},dst=/out",
        "--mount",
        f"type=bind,src={scratch_root},dst=/scratch",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
    ]
    for entry in THREAD_ENV:
        docker_args.extend(("-e", entry))
    docker_args.extend(
        ("--entrypoint", "/bin/sh", image_ref, "-c", WRAPPER, "offline-wrapper")
    )
    docker_args.extend(cli_args)

    metadata = {
        "schema": "offline-container-run/v1",
        "case": case,
        "started_utc": utc_now(),
        "host_platform": run(
            ["docker", "info", "--format", "{{.OSType}}/{{.Architecture}}"]
        ).stdout.strip(),
        "docker_vm_memory_total_bytes": docker_memory_total,
        "docker_vm_memory_total_status": docker_memory_error or "measured",
        "host_architecture_note": "Mac ARM host; linux/amd64 execution is emulated, not Intel Skylake timing.",
        "input_root": str(data_root),
        "input_mount_read_only": True,
        "output_root": str(output_root),
        "competition_output_enabled": competition_output,
        "object_encoding_enabled": encode_objects or competition_output,
        "encoding_run_in_container": (
            "/out/encoding" if (encode_objects or competition_output) else None
        ),
        "intermediate_roots": {
            "recognition_run_in_container": recognition_run,
            "main_run_in_container": main_run,
            "recognition_run_host": str(intermediate_base / "interiors"),
            "main_run_host": str(intermediate_base / "main"),
            "location": "scratch" if competition_output else "output",
            "lifetime": (
                "released_by_cli_after_verified_final_h5"
                if competition_output
                else "retained_diagnostic"
            ),
        },
        "scratch_root": str(scratch_root),
        "output_mount_writable": True,
        "scratch_mount_writable": True,
        "image": image,
        "base_image_digest": base_digest,
        "source": {
            "revision": manifest["source_revision"],
            "source_tree_sha256": source_tree,
            "runner_sha256": next(
                row["sha256"]
                for row in manifest["files"]
                if row["path"] == "scripts/run_interiors.py"
            ),
            "runtime_lock_sha256": manifest["runtime_dependency_lock_sha256"],
            "runtime_export_sha256": manifest["runtime_dependency_export_sha256"],
        },
        "container_limits": {
            "platform": "linux/amd64",
            "network": "none",
            "cpus": 4,
            "memory_bytes": memory_bytes,
            "memory_swap_bytes": memory_bytes,
            "docker_vm_memory_total_bytes": docker_memory_total,
            "output_budget_bytes": output_budget_bytes,
            "output_budget_measurement": (
                "sampled recursive file sizes, including run metadata, logs, receipts, "
                "and pending .part files; interval sampling, not a hard filesystem quota"
            ),
            "filesystem_hard_quota": "unknown_not_enforced_by_supervisor",
            "workers": workers,
            "native_threads": 1,
            "home_override": None,
        },
        "environment_overrides": list(THREAD_ENV),
        "argv_in_container": ["python", "/app/scripts/run_interiors.py", *cli_args],
        "docker_argv": docker_args,
        "container_name": name,
        "sample_interval_seconds": interval,
        "timeout_seconds": timeout_seconds,
        "filesystem_capacity_start": filesystem_capacity_start,
    }
    (output_root / "run-metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n"
    )
    log_path = output_root / "container.log"
    samples_path = output_root / "resource-samples.jsonl"
    started = time.monotonic()
    cli_finished: float | None = None
    samples: list[dict[str, Any]] = []
    cgroup: dict[str, Any] | None = None
    exit_code: int | None = None
    timed_out = False
    stop_reason: str | None = None
    with (
        log_path.open("wb") as log,
        samples_path.open("w", encoding="utf-8") as samples_file,
    ):
        process = subprocess.Popen(docker_args, stdout=log, stderr=subprocess.STDOUT)
        try:
            while True:
                now = time.monotonic()
                marker = output_root / ".cli-exit"
                if cli_finished is None and marker.exists():
                    cli_finished = now
                    try:
                        cgroup_result = run(
                            ["docker", "exec", name, "/bin/sh", "-c", CGROUP_READ]
                        )
                        cgroup = {
                            "returncode": cgroup_result.returncode,
                            "raw": cgroup_result.stdout,
                            "stderr": cgroup_result.stderr,
                        }
                    except (OSError, subprocess.TimeoutExpired) as error:
                        cgroup = {"unavailable": str(error)}
                    (output_root / "cgroup-after-cli.json").write_text(
                        json.dumps(cgroup, indent=2, sort_keys=True) + "\n"
                    )
                    (output_root / ".release-container").write_text("release\n")
                stats = get_stats(name)
                out_bytes, out_files = folder_size(output_root)
                scratch_bytes, scratch_files = folder_size(scratch_root)
                sample = {
                    "elapsed_seconds": now - started,
                    "sampled_utc": utc_now(),
                    "docker_stats": stats,
                    "output_bytes": out_bytes,
                    "output_files": out_files,
                    "scratch_bytes": scratch_bytes,
                    "scratch_files": scratch_files,
                    "filesystem_capacity": {
                        "input": filesystem_capacity(data_root),
                        "output": filesystem_capacity(output_root),
                        "scratch": filesystem_capacity(scratch_root),
                        "hard_quota": "unknown_not_enforced_by_supervisor",
                    },
                }
                samples.append(sample)
                samples_file.write(json.dumps(sample, sort_keys=True) + "\n")
                samples_file.flush()
                exit_code = process.poll()
                if output_budget_exceeded(out_bytes, output_budget_bytes):
                    stop_reason = "output_budget_exceeded"
                    if exit_code is None:
                        stop = run(["docker", "stop", "--time", "2", name], timeout=10)
                        if stop.returncode != 0:
                            run(["docker", "kill", name], timeout=10)
                    break
                if exit_code is not None:
                    stop_reason = "container_exit"
                    break
                if now - started > timeout_seconds:
                    timed_out = True
                    stop_reason = "timeout"
                    stop = run(["docker", "stop", "--time", "2", name], timeout=10)
                    if stop.returncode != 0:
                        run(["docker", "kill", name], timeout=10)
                    break
                time.sleep(interval)
            if process.poll() is None:
                process.wait(timeout=20)
            exit_code = process.returncode
        finally:
            if process.poll() is None:
                (output_root / ".release-container").write_text("release\n")
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    run(["docker", "stop", "--time", "2", name], timeout=10)
                    process.wait(timeout=10)

    inspect = run(
        [
            "docker",
            "inspect",
            "--format",
            "{{json .State}}|{{json .HostConfig}}|{{json .Mounts}}",
            name,
        ]
    )
    inspect_payload = None
    if inspect.returncode == 0:
        pieces = inspect.stdout.strip().split("|", 2)
        if len(pieces) == 3:
            inspect_payload = {
                "state": json.loads(pieces[0]),
                "host_config": json.loads(pieces[1]),
                "mounts": json.loads(pieces[2]),
            }
    final_output_bytes, final_output_files = folder_size(output_root)
    final_scratch_bytes, final_scratch_files = folder_size(scratch_root)
    measured_budget_exceeded = (
        stop_reason == "output_budget_exceeded"
        or output_budget_exceeded(final_output_bytes, output_budget_bytes)
    )
    if measured_budget_exceeded and stop_reason != "output_budget_exceeded":
        stop_reason = "output_budget_exceeded_after_last_sample"
    result = {
        **metadata,
        "finished_utc": utc_now(),
        "cli_elapsed_seconds_from_container_start": None
        if cli_finished is None
        else cli_finished - started,
        "docker_run_elapsed_seconds": time.monotonic() - started,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "stop_reason": stop_reason,
        "output_budget_exceeded": measured_budget_exceeded,
        "filesystem_capacity_end": {
            "input": filesystem_capacity(data_root),
            "output": filesystem_capacity(output_root),
            "scratch": filesystem_capacity(scratch_root),
            "hard_quota": "unknown_not_enforced_by_supervisor",
        },
        "status": "completed"
        if exit_code == 0 and not timed_out and not measured_budget_exceeded
        else "output_budget_exceeded"
        if measured_budget_exceeded
        else "failed_or_incomplete",
        "sample_count": len(samples),
        "sampled_cpu_percent_max": max(
            (
                float(row["docker_stats"]["cpu_percent"].rstrip("%"))
                for row in samples
                if row["docker_stats"] and row["docker_stats"].get("cpu_percent")
            ),
            default=None,
        ),
        "sampled_memory_bytes_max": max(
            (
                row["docker_stats"]["memory_used_bytes"]
                for row in samples
                if row["docker_stats"]
                and row["docker_stats"].get("memory_used_bytes") is not None
            ),
            default=None,
        ),
        "sampled_output_bytes_max": max(
            (row["output_bytes"] for row in samples), default=0
        ),
        "sampled_scratch_bytes_max": max(
            (row["scratch_bytes"] for row in samples), default=0
        ),
        "final_output_bytes": final_output_bytes,
        "final_output_files": final_output_files,
        "final_scratch_bytes": final_scratch_bytes,
        "final_scratch_files": final_scratch_files,
        "container_inspect_after_run": inspect_payload,
        "cgroup_snapshot_after_cli": cgroup,
        "container_log": str(log_path),
        "resource_samples": str(samples_path),
    }
    (output_root / "run-result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    rm = run(["docker", "rm", name])
    result["container_removed"] = rm.returncode == 0
    if rm.returncode != 0:
        result["container_remove_error"] = rm.stderr.strip()
    (output_root / "run-result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    if exit_code != 0 or timed_out or measured_budget_exceeded:
        print(
            json.dumps(
                {
                    "case": case,
                    "status": result["status"],
                    "exit_code": exit_code,
                    "output_root": str(output_root),
                }
            )
        )
        return {
            "exit_code": 1
            if exit_code is None or measured_budget_exceeded
            else exit_code,
            **result,
        }
    print(
        json.dumps(
            {
                "case": case,
                "status": result["status"],
                "exit_code": exit_code,
                "output_root": str(output_root),
            }
        )
    )
    return {"exit_code": 0, **result}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "case", choices=("proof-bursa-parallel", "public-test", "labeled-cohort")
    )
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--scratch-root", type=Path, required=True)
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--build-metadata", type=Path, required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--image-id", required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--encode-objects",
        action="store_true",
        help="run the built-in H5 object encoding into the supervised output budget",
    )
    parser.add_argument(
        "--competition-output",
        action="store_true",
        help=(
            "competition retention: built-in H5 encoding, intermediates on scratch "
            "and released after verified final output"
        ),
    )
    parser.add_argument(
        "--memory-bytes", type=positive_integer, default=DEFAULT_MEMORY_BYTES
    )
    parser.add_argument(
        "--output-budget-bytes",
        type=positive_integer,
        default=DEFAULT_OUTPUT_BUDGET_BYTES,
    )
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--timeout-seconds", type=float, default=32_400.0)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    try:
        validate_resource_limits(
            args.memory_bytes,
            args.output_budget_bytes,
            args.interval,
            args.timeout_seconds,
        )
    except ValueError as error:
        parser.error(str(error))
    result = run_case(
        args.case,
        data_root=args.data_root,
        output_root=args.output_root,
        scratch_root=args.scratch_root,
        context=args.context,
        build_metadata_path=args.build_metadata,
        image_ref=args.image,
        expected_image_id=args.image_id,
        workers=args.workers,
        interval=args.interval,
        timeout_seconds=args.timeout_seconds,
        memory_bytes=args.memory_bytes,
        output_budget_bytes=args.output_budget_bytes,
        encode_objects=args.encode_objects,
        competition_output=args.competition_output,
    )
    return int(result["status"] != "completed")


if __name__ == "__main__":
    raise SystemExit(main())
