"""Mechanical packaging tests for the squint Kaggle packager and its two private wrappers.

The scripts are loaded from their files (never executed through `main`), with the wrappers'
environment overrides pointed into `tmp_path` so no real Kaggle directory is touched.
"""

from __future__ import annotations

import gzip
import hashlib
import importlib.util
import io
import json
import lzma
import subprocess
import sys
import tarfile
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKAGER = ROOT / "scripts" / "package_squint_kaggle.py"
WRAPPERS = {
    "production": ROOT / "kaggle" / "squint-production" / "run_squint.py",
    "scaling": ROOT / "kaggle" / "squint-scaling" / "run_scaling.py",
}
MEMORY_SCHEMA = "knee.squint-memory/v1"
BIG = 17 << 20  # larger than the removed 16 MiB prefix scan


def load_file(path: Path, name: str, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def packager(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    return load_file(PACKAGER, "package_squint_kaggle_under_test", monkeypatch)


@pytest.fixture(params=sorted(WRAPPERS))
def wrapper(
    request: pytest.FixtureRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> ModuleType:
    monkeypatch.setenv("SQUINT_KAGGLE_INPUT", str(tmp_path / "kaggle-input"))
    monkeypatch.setenv("SQUINT_KAGGLE_WORKING", str(tmp_path / "kaggle-working"))
    monkeypatch.setenv("SQUINT_KAGGLE_SCRATCH", str(tmp_path / "kaggle-scratch"))
    return load_file(
        WRAPPERS[request.param], f"wrapper_{request.param}_under_test", monkeypatch
    )


# ---------------------------------------------------------------------------------------------
# Packager: the memory schema is the exact top-level schema of the whole parsed JSON
# ---------------------------------------------------------------------------------------------


def big_before_schema() -> bytes:
    """Sorted-key canonical shape: a huge `cases` array comes before the top-level `schema`."""
    return (
        b'{"cases": ["'
        + b"x" * BIG
        + b'"], "schema": "'
        + MEMORY_SCHEMA.encode()
        + b'"}\n'
    )


def memory_items(
    directory: Path, name: str, data: bytes
) -> list[tuple[Path, str, str]]:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_bytes(data)
    return [(path, f"memory/{name}", "memory")]


@pytest.mark.parametrize(
    ("name", "encode"),
    [
        ("memory.json", lambda data: data),
        ("memory.json.gz", lambda data: gzip.compress(data, compresslevel=1)),
        ("memory.json.xz", lambda data: lzma.compress(data, preset=0)),
    ],
)
def test_schema_after_a_large_cases_array_is_found(packager, tmp_path, name, encode):
    items = memory_items(tmp_path / "mem", name, encode(big_before_schema()))
    assert packager.detect_memory_schema(items, "directory") == name


def test_schema_only_nested_in_cases_is_refused(packager, tmp_path):
    document = {
        "cases": [{"schema": MEMORY_SCHEMA, "note": MEMORY_SCHEMA}],
        "revision": MEMORY_SCHEMA,
    }
    items = memory_items(
        tmp_path / "mem", "memory.json", json.dumps(document, sort_keys=True).encode()
    )
    with pytest.raises(packager.PackagingError, match="top-level schema"):
        packager.detect_memory_schema(items, "directory")


def test_nested_schema_beside_a_wrong_top_level_schema_is_refused(packager, tmp_path):
    document = {"cases": [{"schema": MEMORY_SCHEMA}], "schema": "something.else/v1"}
    items = memory_items(
        tmp_path / "mem", "memory.json", json.dumps(document, sort_keys=True).encode()
    )
    with pytest.raises(packager.PackagingError, match="top-level schema"):
        packager.detect_memory_schema(items, "directory")


@pytest.mark.parametrize(
    "schema", ["knee.squint-memory/v2", "knee.squint-memory/v1 ", "", None, 1]
)
def test_wrong_schema_is_refused(packager, tmp_path, schema):
    document = {"cases": [], "schema": schema}
    items = memory_items(
        tmp_path / "mem", "memory.json", json.dumps(document, sort_keys=True).encode()
    )
    with pytest.raises(packager.PackagingError, match="top-level schema"):
        packager.detect_memory_schema(items, "directory")


def test_legacy_store_is_named_and_refused(packager, tmp_path):
    items = memory_items(
        tmp_path / "mem",
        "memory.json",
        json.dumps({"schema": "knee.diagnostic-store/v1"}).encode(),
    )
    with pytest.raises(packager.PackagingError, match="legacy"):
        packager.detect_memory_schema(items, "directory")


def test_duplicate_top_level_schema_key_is_refused(packager, tmp_path):
    data = f'{{"schema": "x/v1", "schema": "{MEMORY_SCHEMA}"}}'.encode()
    items = memory_items(tmp_path / "mem", "memory.json", data)
    with pytest.raises(packager.PackagingError, match="duplicate"):
        packager.detect_memory_schema(items, "directory")


def test_unparsable_json_memory_is_refused(packager, tmp_path):
    items = memory_items(
        tmp_path / "mem", "memory.json", b'{"schema": "' + MEMORY_SCHEMA.encode()
    )
    with pytest.raises(packager.PackagingError, match="not readable JSON"):
        packager.detect_memory_schema(items, "directory")


def test_only_top_level_files_of_a_directory_memory_can_declare(packager, tmp_path):
    items = memory_items(tmp_path / "mem" / "inner", "memory.json", big_before_schema())
    items = [(path, "memory/inner/memory.json", role) for path, _, role in items]
    with pytest.raises(packager.PackagingError, match="top-level schema"):
        packager.detect_memory_schema(items, "directory")


def test_obsolete_prefix_reader_is_gone_and_no_shebang(packager):
    assert not hasattr(packager, "SCHEMA_SCAN_LIMIT")
    assert not hasattr(packager, "_schema_prefix")
    assert not PACKAGER.read_text(encoding="utf-8").startswith("#!")


def make_repo(root: Path) -> None:
    files = {
        "src/knee/__init__.py": "",
        "src/knee/diagnosis/__init__.py": "",
        "src/knee/diagnosis/squint_profiles.py": "VALUE = 1\n",
        "src/knee/diagnosis/squint_memory.py": "VALUE = 2\n",
        "src/knee/diagnosis/squint_locator.py": "VALUE = 3\n",
        "src/knee/diagnosis/squint_pipeline.py": "VALUE = 4\n",
        "scripts/run_interiors.py": "print('entry')\n",
    }
    for relative, text in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")


def test_build_accepts_a_large_before_schema_memory(packager, tmp_path):
    repo = tmp_path / "repo"
    make_repo(repo)
    memory = tmp_path / "mem"
    memory.mkdir()
    (memory / "memory.json.gz").write_bytes(
        gzip.compress(big_before_schema(), compresslevel=1)
    )
    out = tmp_path / "out"
    summary = packager.build_staging(memory, out, repo)
    assert summary["memory"]["schema"] == MEMORY_SCHEMA
    assert summary["memory"]["schema_declared_in"] == "memory.json.gz"
    assert sorted(path.name for path in out.iterdir()) == sorted(packager.STAGING_FILES)
    assert packager.verify_staging(out, memory=memory, root=repo)[
        "compared_with_sources"
    ]


def test_build_refuses_a_nested_schema_and_leaves_nothing(packager, tmp_path):
    repo = tmp_path / "repo"
    make_repo(repo)
    memory = tmp_path / "mem"
    memory.mkdir()
    (memory / "memory.json").write_text(
        json.dumps({"cases": [{"schema": MEMORY_SCHEMA}]}), encoding="utf-8"
    )
    out = tmp_path / "out"
    with pytest.raises(packager.PackagingError, match="top-level schema"):
        packager.build_staging(memory, out, repo)
    assert not out.exists()


# ---------------------------------------------------------------------------------------------
# Wrappers: the run receipt is a correctness requirement, not a warning
# ---------------------------------------------------------------------------------------------


def write_receipt(path: Path, document: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def test_missing_receipt_is_refused(wrapper, tmp_path):
    with pytest.raises(wrapper.SetupError, match="no receipt.json"):
        wrapper.inspect_run_receipt(tmp_path / "out" / "receipt.json")


def test_unreadable_receipt_is_refused(wrapper, tmp_path):
    path = tmp_path / "receipt.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(wrapper.SetupError, match="unreadable"):
        wrapper.inspect_run_receipt(path)


@pytest.mark.parametrize(
    "document",
    [
        {},
        [],
        {"work": None},
        {"work": {}},
        {"work": {"bounded_zoom_runs": 3}},
        {"full_anatomy_runs": 0},
        {"studies": [{"full_anatomy_runs": 0}], "work": {"bounded_zoom_runs": 0}},
    ],
)
def test_absent_authoritative_full_anatomy_count_is_refused(
    wrapper, tmp_path, document
):
    path = write_receipt(tmp_path / "receipt.json", document)
    with pytest.raises(
        wrapper.SetupError, match="authoritative work.full_anatomy_runs"
    ):
        wrapper.inspect_run_receipt(path)


@pytest.mark.parametrize("value", [1, 2, 40, -1])
def test_nonzero_full_anatomy_is_refused(wrapper, tmp_path, value):
    path = write_receipt(
        tmp_path / "receipt.json", {"work": {"full_anatomy_runs": value}}
    )
    with pytest.raises(wrapper.SetupError, match="full_anatomy_runs"):
        wrapper.inspect_run_receipt(path)


@pytest.mark.parametrize("value", [True, False, None, "0", 0.0])
def test_non_integer_full_anatomy_count_is_refused(wrapper, tmp_path, value):
    path = write_receipt(
        tmp_path / "receipt.json", {"work": {"full_anatomy_runs": value}}
    )
    with pytest.raises(wrapper.SetupError, match="not an integer count"):
        wrapper.inspect_run_receipt(path)


@pytest.mark.parametrize(
    "document",
    [
        {"work": {"full_anatomy_runs": 0}, "studies": [{"full_anatomy_runs": 1}]},
        {"work": {"full_anatomy_runs": 0}, "route": {"fallback_runs": 2}},
        {"work": {"full_anatomy_runs": 0, "full_reconstruction_runs": 1}},
    ],
)
def test_other_nonzero_fallback_counters_are_refused(wrapper, tmp_path, document):
    path = write_receipt(tmp_path / "receipt.json", document)
    with pytest.raises(wrapper.SetupError, match="forbids"):
        wrapper.inspect_run_receipt(path)


def test_zero_full_anatomy_with_bounded_zoom_runs_is_allowed(wrapper, tmp_path):
    document = {
        "schema": "knee.squint-run-receipt/v1",
        "study_count": 3,
        "work": {"full_anatomy_runs": 0, "bounded_zoom_runs": 7},
    }
    path = write_receipt(tmp_path / "receipt.json", document)
    result = wrapper.inspect_run_receipt(path)
    assert result["present"] is True
    assert result["full_anatomy_runs"] == 0
    assert result["bounded_zoom_runs"] == 7
    assert result["work"] == document["work"]
    assert result["summary"] == {"schema": document["schema"], "study_count": 3}
    assert result["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert wrapper.REPORT["warnings"] == []


# ---------------------------------------------------------------------------------------------
# Wrappers: complete diagnostics, no tail truncation, honest failure paths
# ---------------------------------------------------------------------------------------------


def fake_run(code: int, stdout: str, stderr: str):
    def run(command, **_kwargs):
        return subprocess.CompletedProcess(command, code, stdout=stdout, stderr=stderr)

    return run


def make_wheels(tmp_path: Path) -> Path:
    base = tmp_path / "wheels-dataset"
    (base / "wheels" / "cp313").mkdir(parents=True)
    (base / "wheels" / "cp313" / "a-1-py3-none-any.whl").write_bytes(b"wheel")
    requirements = base / "requirements-cp313.txt"
    requirements.write_text("a==1\n", encoding="utf-8")
    return requirements


def test_install_keeps_complete_pip_output(wrapper, tmp_path, monkeypatch):
    out, err = "o" * 10000 + "END-OUT", "e" * 10000 + "END-ERR"
    monkeypatch.setattr(wrapper.subprocess, "run", fake_run(0, out, err))
    info = wrapper.install_wheels(make_wheels(tmp_path))
    assert info["stdout"] == out
    assert info["stderr"] == err
    log = Path(info["setup_log"]).read_text(encoding="utf-8")
    assert out in log
    assert err in log


def test_failed_install_keeps_complete_output_and_refuses(
    wrapper, tmp_path, monkeypatch
):
    err = "e" * 10000 + "END-ERR"
    monkeypatch.setattr(wrapper.subprocess, "run", fake_run(1, "", err))
    with pytest.raises(wrapper.SetupError, match="offline wheel install failed"):
        wrapper.install_wheels(make_wheels(tmp_path))
    assert wrapper.REPORT["install"]["stderr"] == err
    assert wrapper.REPORT["install"]["exit"] == 1


def test_no_log_tail_truncation_helper_remains(wrapper):
    assert not hasattr(wrapper, "log_tail")


def test_step_enter_returns_the_step(wrapper):
    with wrapper.Step("unit") as step:
        assert isinstance(step, wrapper.Step)
    assert wrapper.REPORT["steps"]["unit"]["ok"] is True


def test_setup_errors_are_recorded_and_return_one(wrapper, monkeypatch):
    def refuse() -> int:
        raise wrapper.SetupError("named refusal")

    monkeypatch.setattr(wrapper, "run", refuse)
    assert wrapper.main() == 1
    assert wrapper.REPORT["status"] == "failed"
    assert "named refusal" in wrapper.REPORT["fatal"]
    assert json.loads(wrapper.RECEIPT.read_text(encoding="utf-8"))["status"] == "failed"


@pytest.mark.parametrize("error", [RuntimeError("unexpected"), KeyboardInterrupt()])
def test_other_failures_are_recorded_then_rethrown(wrapper, monkeypatch, error):
    def explode() -> int:
        raise error

    monkeypatch.setattr(wrapper, "run", explode)
    with pytest.raises(type(error)):
        wrapper.main()
    assert wrapper.REPORT["status"] == "failed"
    assert json.loads(wrapper.RECEIPT.read_text(encoding="utf-8"))["status"] == "failed"


def test_selection_problems_are_listed_whole_in_a_file(tmp_path, monkeypatch):
    monkeypatch.setenv("SQUINT_KAGGLE_INPUT", str(tmp_path / "kaggle-input"))
    monkeypatch.setenv("SQUINT_KAGGLE_WORKING", str(tmp_path / "kaggle-working"))
    monkeypatch.setenv("SQUINT_KAGGLE_SCRATCH", str(tmp_path / "kaggle-scratch"))
    scaling = load_file(
        WRAPPERS["scaling"], "wrapper_scaling_selection_under_test", monkeypatch
    )
    competition = tmp_path / "competition"
    (competition / "train_series" / "present").mkdir(parents=True)
    (competition / "train.csv").write_text(
        "StudyInstanceUID,label\npresent,0\nabsent,1\n", encoding="utf-8"
    )
    stranger = [f"stranger-{index}" for index in range(25)]
    selection = {
        "uids": ["present", "absent", *stranger],
        "partition": "scaling",
        "sha256": "0" * 64,
    }
    with pytest.raises(scaling.SetupError, match="complete lists are in"):
        scaling.plan_studies(competition, selection)
    problems = json.loads(scaling.SELECTION_PROBLEMS_FILE.read_text(encoding="utf-8"))
    assert problems == {"not_in_train_csv": stranger, "not_on_disk": ["absent"]}


# ---------------------------------------------------------------------------------------------
# Wrappers: the runtime dataset as uploaded, and as Kaggle auto-unpacks it
#
# Kaggle extracts runtime-bundle.tar as runtime-bundle/ beside the outer RUNTIME_MANIFEST.json, so a
# search for the manifest finds two. These tests build real stagings with the real packager, lay them
# out the way each upload shape arrives, and drive the wrappers' real find -> select_runtime_manifest ->
# materialise (and run() up to the copy). Copied bytes are compared with the bytes inside the tar.
# ---------------------------------------------------------------------------------------------

MANIFEST = "RUNTIME_MANIFEST.json"
TAR = "runtime-bundle.tar"
NESTED = "runtime-bundle"

SHAPES = {
    # as uploaded: outer manifest + tar
    "tar": {
        "manifest": MANIFEST,
        "mode": "tar",
        "found": 1,
        "shape": "single_manifest",
    },
    # Kaggle unpacked the tar and kept it
    "nested_with_tar": {
        "manifest": MANIFEST,
        "mode": "tar",
        "found": 2,
        "shape": "outer_and_extracted",
    },
    # Kaggle unpacked the tar and it is gone: outer manifest + runtime-bundle/
    "nested_no_tar": {
        "manifest": f"{NESTED}/{MANIFEST}",
        "mode": "directory",
        "found": 2,
        "shape": "outer_and_extracted",
    },
    # the extracted bundle alone (its own manifest at the root)
    "directory": {
        "manifest": MANIFEST,
        "mode": "directory",
        "found": 1,
        "shape": "single_manifest",
    },
    # the outer manifest with the extracted source/ and memory/ beside it, no tar
    "directory_beside_outer": {
        "manifest": MANIFEST,
        "mode": "directory",
        "found": 1,
        "shape": "single_manifest",
    },
}


def read_members(tar_bytes: bytes) -> dict[str, bytes]:
    members: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:") as archive:
        for member in archive:
            handle = archive.extractfile(member)
            assert handle is not None
            members[member.name] = handle.read()
    return members


@pytest.fixture(scope="module")
def bundles(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict]:
    """Two real stagings from the real packager; `beta` is another bundle (other memory bytes)."""
    built: dict[str, dict] = {}
    with pytest.MonkeyPatch.context() as patch:
        packager = load_file(PACKAGER, "package_squint_kaggle_for_bundles", patch)
        for seed in ("alpha", "beta"):
            base = tmp_path_factory.mktemp(f"bundle-{seed}")
            repo, memory, staging = base / "repo", base / "mem", base / "staging"
            make_repo(repo)
            memory.mkdir()
            (memory / "memory.json").write_text(
                json.dumps(
                    {"cases": [], "schema": MEMORY_SCHEMA, "seed": seed}, sort_keys=True
                ),
                encoding="utf-8",
            )
            (memory / "shard-0.bin").write_bytes(
                b"SHARD\n" + hashlib.sha256(seed.encode()).digest() * 400
            )
            packager.build_staging(memory, staging, repo)
            tar = (staging / TAR).read_bytes()
            outer = (staging / MANIFEST).read_bytes()
            members = read_members(tar)
            built[seed] = {
                "outer": outer,
                "metadata": (staging / "dataset-metadata.json").read_bytes(),
                "tar": tar,
                "members": members,  # as the tar holds them, inner manifest included
                "files": {n: d for n, d in members.items() if n != MANIFEST},
                "bundle_id": json.loads(outer)["bundle_id"],
            }
    assert built["alpha"]["bundle_id"] != built["beta"]["bundle_id"]
    return built


def put(path: Path, data: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def dataset(wrapper: ModuleType) -> Path:
    return wrapper.INPUT / wrapper.RUNTIME_HINT


def lay_outer(ds: Path, bundle: dict, *, tar: bool = True) -> None:
    """The dataset root as uploaded: the outer manifest, the metadata and (optionally) the tar."""
    put(ds / MANIFEST, bundle["outer"])
    put(ds / "dataset-metadata.json", bundle["metadata"])
    if tar:
        put(ds / TAR, bundle["tar"])


def lay_members(directory: Path, bundle: dict) -> None:
    """The tar's members unpacked into `directory`, the inner manifest included."""
    for name, data in bundle["members"].items():
        put(directory / name, data)


def lay_shape(ds: Path, bundle: dict, shape: str) -> None:
    if shape == "tar":
        lay_outer(ds, bundle)
    elif shape == "nested_with_tar":
        lay_outer(ds, bundle)
        lay_members(ds / NESTED, bundle)
    elif shape == "nested_no_tar":
        lay_outer(ds, bundle, tar=False)
        lay_members(ds / NESTED, bundle)
    elif shape == "directory":
        lay_members(ds, bundle)
    elif shape == "directory_beside_outer":
        lay_members(ds, bundle)
        put(ds / MANIFEST, bundle["outer"])
    else:
        raise AssertionError(shape)


def read_tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def forbid_reading_the_bundle(patch: pytest.MonkeyPatch, wrapper: ModuleType) -> None:
    """Selection reads manifests and stats files; it never extracts, copies or hashes the bundle."""

    def refuse(*_args: object, **_kwargs: object) -> None:
        raise AssertionError(
            "selection must not read, hash, extract or copy the bundle"
        )

    for name in ("extract_tar", "copy_directory", "materialise", "sha256_file"):
        patch.setattr(wrapper, name, refuse)


def select(wrapper: ModuleType) -> dict:
    """The real search, then the real selector, with the bundle itself off limits."""
    hits = wrapper.find(wrapper.MANIFEST_NAME)
    with pytest.MonkeyPatch.context() as patch:
        forbid_reading_the_bundle(patch, wrapper)
        return wrapper.select_runtime_manifest(hits, wrapper.RUNTIME_HINT)


def prepare_run(wrapper: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    """Everything run() needs besides the runtime dataset; it stops right after the runtime copy."""
    tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
    monkeypatch.setattr(wrapper, "WHEEL_TAG", tag)
    competition = wrapper.INPUT / wrapper.COMPETITION_HINT
    competition.mkdir(parents=True)
    columns = [
        "StudyInstanceUID",
        *(f"condition_{index}" for index in range(wrapper.CONDITION_COUNT)),
    ]
    row = ["study-1", *(["0.5"] * wrapper.CONDITION_COUNT)]
    (competition / "sample_submission.csv").write_text(
        ",".join(columns) + "\n" + ",".join(row) + "\n", encoding="utf-8"
    )
    (competition / "train.csv").write_text(
        "StudyInstanceUID,label\nstudy-1,0\n", encoding="utf-8"
    )
    (competition / "train_series").mkdir()
    (competition / "test_series").mkdir()
    wheels = wrapper.INPUT / wrapper.WHEELS_HINT
    wheels.mkdir(parents=True)
    (wheels / f"requirements-{tag}.txt").write_text("a==1\n", encoding="utf-8")

    def stop(_requirements: Path) -> dict:
        raise wrapper.SetupError("stopped after the runtime copy")

    monkeypatch.setattr(wrapper, "install_wheels", stop)


# (a) the normal tar shape, (b) Kaggle's auto-unpacked shapes, (e) directory-only layouts


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_every_upload_shape_selects_and_copies_the_verified_bytes(
    wrapper, bundles, tmp_path, shape
):
    bundle, want = bundles["alpha"], SHAPES[shape]
    ds = dataset(wrapper)
    lay_shape(ds, bundle, shape)
    assert len(wrapper.find(wrapper.MANIFEST_NAME)) == want["found"]
    chosen = select(wrapper)
    assert chosen["manifest_path"] == ds / want["manifest"]
    assert chosen["manifest"]["bundle_id"] == bundle["bundle_id"]
    assert chosen["selection"]["shape"] == want["shape"]
    assert chosen["selection"]["bundle_id"] == bundle["bundle_id"]
    copied = wrapper.materialise(
        chosen["manifest_path"], chosen["manifest"], tmp_path / "local"
    )
    assert copied["mode"] == want["mode"]
    assert read_tree(tmp_path / "local") == bundle["files"]


@pytest.mark.parametrize("shape", sorted(SHAPES))
def test_run_reaches_the_bundle_through_the_selector_exactly_once(
    wrapper, bundles, monkeypatch, shape
):
    bundle, want = bundles["alpha"], SHAPES[shape]
    prepare_run(wrapper, monkeypatch)
    ds = dataset(wrapper)
    lay_shape(ds, bundle, shape)
    calls: list[str] = []
    for name in ("extract_tar", "copy_directory"):
        real = getattr(wrapper, name)

        def counted(*args, _name=name, _real=real, **kwargs):
            calls.append(_name)
            return _real(*args, **kwargs)

        monkeypatch.setattr(wrapper, name, counted)
    with pytest.raises(wrapper.SetupError, match="stopped after the runtime copy"):
        wrapper.run()
    assert wrapper.REPORT["steps"]["copy_runtime_to_local_disk"]["ok"] is True
    assert wrapper.REPORT["runtime"]["copy"]["mode"] == want["mode"]
    assert calls == ["extract_tar" if want["mode"] == "tar" else "copy_directory"]
    inputs = wrapper.REPORT["inputs"]
    assert inputs["runtime_manifest"] == str(ds / want["manifest"])
    assert inputs["runtime_manifest_selection"]["shape"] == want["shape"]
    assert inputs["runtime_manifest_selection"]["bundle_id"] == bundle["bundle_id"]
    assert read_tree(wrapper.LOCAL / "bundle") == bundle["files"]


def test_selector_reports_why_each_candidate_was_or_was_not_used(wrapper, bundles):
    ds = dataset(wrapper)
    lay_shape(ds, bundles["alpha"], "nested_no_tar")
    chosen = select(wrapper)["selection"]
    assert chosen["route"] == "extracted_directory"
    assert sorted(item["path"] for item in chosen["candidates"]) == sorted(
        [str(ds / MANIFEST), str(ds / NESTED / MANIFEST)]
    )
    assert [item["manifest"] for item in chosen["not_used"]] == [str(ds / MANIFEST)]
    assert "not present" in chosen["not_used"][0]["reason"]


def test_a_usable_archive_is_preferred_over_the_extracted_tree(
    wrapper, bundles, tmp_path
):
    bundle, ds = bundles["alpha"], dataset(wrapper)
    lay_shape(ds, bundle, "nested_with_tar")
    # the extracted copy is damaged and incomplete: it must not even be consulted
    damaged = ds / NESTED / "source" / "scripts" / "run_interiors.py"
    data = bytearray(damaged.read_bytes())
    data[0] ^= 1
    damaged.write_bytes(bytes(data))
    (ds / NESTED / "memory" / "shard-0.bin").unlink()
    chosen = select(wrapper)
    assert chosen["manifest_path"] == ds / MANIFEST
    assert chosen["selection"]["route"] == "tar"
    copied = wrapper.materialise(
        chosen["manifest_path"], chosen["manifest"], tmp_path / "local"
    )
    assert copied["mode"] == "tar"
    assert read_tree(tmp_path / "local") == bundle["files"]


def test_a_wrong_sized_archive_yields_to_the_verified_extracted_tree(
    wrapper, bundles, tmp_path
):
    bundle, ds = bundles["alpha"], dataset(wrapper)
    lay_shape(ds, bundle, "nested_with_tar")
    (ds / TAR).write_bytes(bundle["tar"][:-1])
    chosen = select(wrapper)
    assert chosen["manifest_path"] == ds / NESTED / MANIFEST
    assert chosen["selection"]["route"] == "extracted_directory"
    assert "bytes" in chosen["selection"]["not_used"][0]["reason"]
    copied = wrapper.materialise(
        chosen["manifest_path"], chosen["manifest"], tmp_path / "local"
    )
    assert copied["mode"] == "directory"
    assert read_tree(tmp_path / "local") == bundle["files"]


def test_an_extracted_tree_missing_a_listed_file_is_refused(wrapper, bundles):
    ds = dataset(wrapper)
    lay_shape(ds, bundles["alpha"], "nested_no_tar")
    (ds / NESTED / "memory" / "shard-0.bin").unlink()
    with pytest.raises(
        wrapper.SetupError, match=r"no usable source.*memory/shard-0\.bin"
    ):
        select(wrapper)


@pytest.mark.parametrize("shape", ["nested_no_tar", "directory"])
def test_extracted_bytes_are_still_checked_against_the_manifest(
    wrapper, bundles, tmp_path, shape
):
    ds = dataset(wrapper)
    lay_shape(ds, bundles["alpha"], shape)
    base = ds / NESTED if shape == "nested_no_tar" else ds
    damaged = base / "source" / "scripts" / "run_interiors.py"
    data = bytearray(damaged.read_bytes())
    data[0] ^= 1  # same size, different bytes
    damaged.write_bytes(bytes(data))
    chosen = select(wrapper)  # every listed file is there, so selection cannot tell
    with pytest.raises(wrapper.SetupError, match="hash or size mismatch"):
        wrapper.materialise(
            chosen["manifest_path"], chosen["manifest"], tmp_path / "local"
        )


def test_tar_bytes_are_still_checked_against_the_manifest(wrapper, bundles, tmp_path):
    bundle, ds = bundles["alpha"], dataset(wrapper)
    lay_shape(ds, bundle, "tar")
    raw = bytearray(bundle["tar"])
    at = raw.index(bundle["files"]["memory/shard-0.bin"])
    raw[at + 10] ^= 1  # same size, different bytes
    (ds / TAR).write_bytes(bytes(raw))
    chosen = select(wrapper)
    with pytest.raises(wrapper.SetupError, match="hash or size mismatch in the tar"):
        wrapper.materialise(
            chosen["manifest_path"], chosen["manifest"], tmp_path / "local"
        )


def test_the_generic_choose_is_not_weakened(wrapper, bundles):
    lay_shape(dataset(wrapper), bundles["alpha"], "nested_no_tar")
    hits = wrapper.find(wrapper.MANIFEST_NAME)
    assert len(hits) == 2
    with pytest.raises(wrapper.SetupError, match="ambiguous"):
        wrapper.choose(hits, wrapper.RUNTIME_HINT, "squint runtime manifest")


def test_no_manifest_at_all_is_named(wrapper):
    with pytest.raises(wrapper.SetupError, match="squint runtime manifest not found"):
        wrapper.select_runtime_manifest([], wrapper.RUNTIME_HINT)


# (c) conflicting manifests and bundle identities are refused by name, never guessed

CONFLICTS = {
    # the outer manifest is bundle alpha, the unpacked directory is bundle beta
    "distinct_bundle": r"two different runtime bundles",
    # same bundle_id, but the extracted manifest differs beyond the tar record
    "inconsistent_pair": r"disagree in \['warnings'\]",
    "two_outer_manifests": r"ambiguous.*2 outer and 0 extracted",
    "two_extracted_manifests": r"ambiguous.*0 outer and 2 extracted",
    "third_manifest": r"ambiguous.*1 outer and 2 extracted",
    # an equivalent extracted manifest that is not inside the outer manifest's dataset
    "unrelated_directories": r"not nested",
}


def lay_conflict(wrapper: ModuleType, bundles: dict[str, dict], kind: str) -> None:
    ds, alpha, beta = dataset(wrapper), bundles["alpha"], bundles["beta"]
    if kind == "distinct_bundle":
        lay_outer(ds, alpha, tar=False)
        lay_members(ds / NESTED, beta)
    elif kind == "inconsistent_pair":
        lay_outer(ds, alpha, tar=False)
        lay_members(ds / NESTED, alpha)
        edited = json.loads(alpha["members"][MANIFEST])
        edited["warnings"] = ["edited after packaging"]
        put(
            ds / NESTED / MANIFEST,
            json.dumps(edited, indent=2, sort_keys=True).encode("utf-8"),
        )
    elif kind == "two_outer_manifests":
        lay_outer(ds, alpha)
        put(ds / NESTED / MANIFEST, alpha["outer"])
    elif kind == "two_extracted_manifests":
        lay_members(ds, alpha)
        lay_members(ds / NESTED, alpha)
    elif kind == "third_manifest":
        lay_outer(ds, alpha, tar=False)
        lay_members(ds / NESTED, alpha)
        put(ds / "old" / MANIFEST, beta["members"][MANIFEST])
    elif kind == "unrelated_directories":
        lay_outer(ds, alpha, tar=False)
        lay_members(wrapper.INPUT / f"{wrapper.RUNTIME_HINT}-copy", alpha)
    else:
        raise AssertionError(kind)


@pytest.mark.parametrize("kind", sorted(CONFLICTS))
def test_conflicting_manifests_are_refused_before_anything_is_copied(
    wrapper, bundles, monkeypatch, kind
):
    prepare_run(wrapper, monkeypatch)
    lay_conflict(wrapper, bundles, kind)
    assert len(wrapper.find(wrapper.MANIFEST_NAME)) >= 2
    with pytest.raises(wrapper.SetupError, match=CONFLICTS[kind]):
        select(wrapper)
    # the real run refuses at the same point (the stop-after-copy sentinel would not match)
    with pytest.raises(wrapper.SetupError, match=CONFLICTS[kind]):
        wrapper.run()
    assert not (wrapper.LOCAL / "bundle").exists()
    assert "runtime" not in wrapper.REPORT


def test_every_candidate_is_named_in_an_ambiguity(wrapper, bundles):
    lay_conflict(wrapper, bundles, "third_manifest")
    ds = dataset(wrapper)
    with pytest.raises(wrapper.SetupError, match="ambiguous") as refusal:
        select(wrapper)
    message = str(refusal.value)
    for path in (ds / MANIFEST, ds / NESTED / MANIFEST, ds / "old" / MANIFEST):
        assert str(path) in message
    for seed in ("alpha", "beta"):
        assert bundles[seed]["bundle_id"] in message


# (d) a malformed manifest is a named refusal, never a crash and never skipped


def corrupt_manifest(raw: bytes, how: str) -> bytes:
    if how == "not_json":
        return b"{not json"
    if how == "json_list":
        return b"[]"
    if how == "not_utf8":
        return b"\xff\xfe\x00"
    manifest = json.loads(raw)
    files = manifest["files"]
    if how == "wrong_schema":
        manifest["schema"] = "knee.squint-runtime-manifest/v0"
    elif how == "no_files":
        manifest["files"] = []
    elif how == "entry_without_sha":
        del files[0]["sha256"]
    elif how == "entry_not_object":
        files[0] = "source/x.py"
    elif how == "entry_bytes_not_int":
        files[0]["bytes"] = "12"
    elif how == "bad_bundle_id":
        manifest["bundle_id"] = "0" * 64
    elif how == "path_traversal":
        files[0]["path"] = "../escape.py"
    elif how == "tar_not_object":
        manifest["tar"] = TAR
    elif how == "tar_without_name":
        manifest["tar"] = {"sha256": "0" * 64, "bytes": 1}
    elif how == "tar_name_traversal":
        manifest["tar"] = {"name": "../x.tar", "sha256": "0" * 64, "bytes": 1}
    elif how == "tar_name_is_a_path":
        manifest["tar"] = {"name": "sub/x.tar", "sha256": "0" * 64, "bytes": 1}
    elif how == "memory_not_squint":
        manifest["memory"]["schema"] = "knee.squint-memory/v0"
    else:
        raise AssertionError(how)
    return json.dumps(manifest, indent=2, sort_keys=True).encode("utf-8")


MALFORMED = (
    "not_json",
    "json_list",
    "not_utf8",
    "wrong_schema",
    "no_files",
    "entry_without_sha",
    "entry_not_object",
    "entry_bytes_not_int",
    "bad_bundle_id",
    "path_traversal",
    "tar_not_object",
    "tar_without_name",
    "tar_name_traversal",
    "tar_name_is_a_path",
    "memory_not_squint",
)
# which manifest is damaged, in which layout
DAMAGED = {
    "sole_outer": ("tar", MANIFEST),
    "sole_extracted": ("directory", MANIFEST),
    "pair_outer": ("nested_no_tar", MANIFEST),
    "pair_inner": ("nested_no_tar", f"{NESTED}/{MANIFEST}"),
}


@pytest.mark.parametrize("where", sorted(DAMAGED))
@pytest.mark.parametrize("how", MALFORMED)
def test_a_malformed_manifest_is_refused_and_named(wrapper, bundles, where, how):
    shape, name = DAMAGED[where]
    ds = dataset(wrapper)
    lay_shape(ds, bundles["alpha"], shape)
    target = ds / name
    target.write_bytes(corrupt_manifest(target.read_bytes(), how))
    with pytest.raises(wrapper.SetupError, match="runtime manifest") as refusal:
        select(wrapper)
    assert str(target) in str(refusal.value)


@pytest.mark.parametrize("how", ["not_json", "entry_without_sha", "tar_not_object"])
def test_a_malformed_manifest_stops_the_run_before_any_copy(
    wrapper, bundles, monkeypatch, how
):
    prepare_run(wrapper, monkeypatch)
    ds = dataset(wrapper)
    lay_shape(ds, bundles["alpha"], "nested_no_tar")
    target = ds / NESTED / MANIFEST
    target.write_bytes(corrupt_manifest(target.read_bytes(), how))
    with pytest.raises(wrapper.SetupError, match="runtime manifest"):
        wrapper.run()
    assert not (wrapper.LOCAL / "bundle").exists()
    assert wrapper.REPORT["steps"]["locate_inputs"]["ok"] is False


@pytest.mark.parametrize("bad_bytes", [True, -1], ids=["bool", "negative"])
def test_file_byte_counts_reject_bool_and_negative_for_one_byte_member(
    wrapper, packager, tmp_path, bad_bytes
):
    repo, memory, staging = (
        tmp_path / "repo",
        tmp_path / "memory",
        tmp_path / "staging",
    )
    make_repo(repo)
    memory.mkdir()
    (memory / "memory.json").write_text(
        json.dumps({"cases": [], "schema": MEMORY_SCHEMA, "seed": "byte-count"}),
        encoding="utf-8",
    )
    (memory / "shard-0.bin").write_bytes(b"x")
    packager.build_staging(memory, staging, repo)

    tar_bytes = (staging / TAR).read_bytes()
    members = read_members(tar_bytes)
    bundle = {
        "outer": (staging / MANIFEST).read_bytes(),
        "metadata": (staging / "dataset-metadata.json").read_bytes(),
        "tar": tar_bytes,
    }
    ds = dataset(wrapper)
    lay_outer(ds, bundle)

    selected = wrapper.select_runtime_manifest(
        wrapper.find(wrapper.MANIFEST_NAME), wrapper.RUNTIME_HINT
    )
    entry = next(
        item
        for item in selected["manifest"]["files"]
        if item["path"] == "memory/shard-0.bin"
    )
    assert entry["bytes"] == 1
    copied = wrapper.materialise(
        selected["manifest_path"], selected["manifest"], tmp_path / "verified"
    )
    assert copied["mode"] == "tar"
    assert read_tree(tmp_path / "verified") == {
        name: data for name, data in members.items() if name != MANIFEST
    }

    outer_path = ds / MANIFEST
    malformed = json.loads(outer_path.read_text(encoding="utf-8"))
    entry = next(
        item for item in malformed["files"] if item["path"] == "memory/shard-0.bin"
    )
    entry["bytes"] = bad_bytes
    outer_path.write_text(json.dumps(malformed), encoding="utf-8")
    with pytest.raises(
        wrapper.SetupError, match="runtime manifest.*entry is malformed"
    ):
        wrapper.select_runtime_manifest(
            wrapper.find(wrapper.MANIFEST_NAME), wrapper.RUNTIME_HINT
        )
