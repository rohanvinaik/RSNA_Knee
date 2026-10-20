"""The offline Kaggle packager, checked against tiny source and memory fixtures.

Each property is checked with two signs: the thing that must be there is, and the thing that must be
refused is, with no output left behind. Nothing here touches the network, Kaggle or the real project
tree; the notebook is executed against a fixture bundle laid out as Kaggle would mount it.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

import pytest

from knee.diagnosis.models import Snapshot
from knee.diagnosis.store import write_store

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "package_kaggle.py"
_SPEC = importlib.util.spec_from_file_location("package_kaggle", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
pk = importlib.util.module_from_spec(_SPEC)
sys.modules["package_kaggle"] = pk
_SPEC.loader.exec_module(pk)

RUN_SCRIPT = """import json
import sys
from pathlib import Path

import knee

arguments = sys.argv[1:]
out = Path(arguments[arguments.index("--diagnostic-output") + 1])
memory = Path(arguments[arguments.index("--diagnostic-memory") + 1])
out.mkdir(parents=True, exist_ok=True)
payload = {
    "argv": arguments,
    "knee": knee.__file__,
    "memory": json.loads((memory / "manifest.json").read_text()),
}
(out / "result.json").write_text(json.dumps(payload))
if "--diagnostic-submission-template" in arguments and "--fail" not in arguments:
    (out / "submission.csv").write_text("runner-owned fixture artifact\\n")
sys.exit(3 if "--fail" in arguments else 0)
"""
DEFAULT_ARGV = (
    "--split",
    "test",
    "--diagnostic-mode",
    "infer",
    "--diagnostic-memory",
    "{memory}",
    "--diagnostic-output",
    "{working}/diagnostic",
)
SUBMISSION_ARGV = (
    *DEFAULT_ARGV,
    "--diagnostic-submission-template",
    "{input}/sample_submission.csv",
    "--diagnostic-readout",
    "test_fixture:readout",
)
EXPECTED_PATHS = {
    "source/scripts/run_interiors.py",
    "source/src/knee/__init__.py",
    "source/src/knee/core.py",
    "source/src/knee/sub/__init__.py",
    "source/src/knee/sub/mod.py",
    "memory/manifest.json",
    "memory/profiles.npz",
}
WHEEL_NUMPY = "numpy-2.0.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl"
WHEEL_PURE = "idna-3.7-py3-none-any.whl"


def write(path: Path, text: str | bytes = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_text(text)
    return path


def write_zip(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("arr_0.npy", b"tiny")
    return path


def make_source(root: Path) -> Path:
    write(
        root / "pyproject.toml",
        '[project]\nname = "tiny"\nrequires-python = ">=3.11"\n',
    )
    write(root / "scripts" / "run_interiors.py", RUN_SCRIPT)
    write(root / "scripts" / "draw_other.py", "OTHER = 1\n")
    write(root / "src" / "knee" / "__init__.py", "")
    write(root / "src" / "knee" / "core.py", "VALUE = 1\n")
    write(root / "src" / "knee" / "sub" / "__init__.py", "")
    write(root / "src" / "knee" / "sub" / "mod.py", "NAME = 'mod'\n")
    write(root / "src" / "knee" / "__pycache__" / "core.cpython-314.pyc", b"\0pyc")
    write(root / "src" / "knee" / "tests" / "test_core.py", "def test(): pass\n")
    write(root / "src" / "knee" / ".env", "TOKEN=hidden\n")
    write(root / "src" / "knee" / "blob.zip", b"PK\x03\x04")
    write(root / "src" / "knee" / "notes.md", "notes\n")
    write(root / "src" / "knee" / "cache.nbc", b"nbc")
    write(root / "src" / "knee" / "sub" / "archive" / "old.py", "OLD = 1\n")
    write(root / "tests" / "test_outside.py", "OUTSIDE = 1\n")
    write(root / "data" / "study" / "a.dcm", b"dicom")
    write(root / "data" / "readings" / "note.md", "reading\n")
    write(root / "archive" / "old.py", "OLD = 2\n")
    write(root / ".git" / "config", "[core]\n")
    return root


def make_memory(root: Path) -> Path:
    root.parent.mkdir(parents=True, exist_ok=True)
    write_store(root, Snapshot("package-test-r1", ()))
    return root


@pytest.fixture
def world(tmp_path: Path) -> Path:
    make_source(tmp_path / "project")
    make_memory(tmp_path / "memory")
    return tmp_path


def make_spec(world: Path, **overrides) -> pk.PackageSpec:
    values = {
        "source_root": world / "project",
        "memory_dir": world / "memory",
        "output_dir": world / "out",
        "dataset_id": "alice/rsna-knee-bundle",
        "kernel_id": "alice/rsna-knee-offline",
        "competition_sources": ("rsna-test-comp",),
        "run_argv": DEFAULT_ARGV,
        "input_root": str(world / "input"),
        "working_root": str(world / "working"),
    }
    values.update(overrides)
    return pk.PackageSpec(**values)


def build(world: Path, **overrides) -> dict:
    return pk.build_bundle(make_spec(world, **overrides))


def manifest_of(output: Path) -> dict:
    return json.loads((output / "dataset" / pk.MANIFEST_NAME).read_text())


def bundle_paths(output: Path) -> set[str]:
    dataset = output / "dataset"
    return {
        path.relative_to(dataset).as_posix()
        for path in dataset.rglob("*")
        if path.is_file() and path.name not in pk.UNLISTED_TOP_LEVEL
    }


def refuses(world: Path, match: str, **overrides) -> None:
    with pytest.raises(pk.PackagingError, match=match):
        build(world, **overrides)
    assert not (world / "out").exists(), "a refusal must leave no output behind"


# ---- contents: what is copied, and what is not ---------------------------------------------


def test_bundle_holds_exactly_the_source_and_memory(world: Path) -> None:
    result = build(world)
    output = world / "out"
    assert bundle_paths(output) == EXPECTED_PATHS
    assert {entry["path"] for entry in manifest_of(output)["files"]} == EXPECTED_PATHS
    assert result["file_count"] == len(EXPECTED_PATHS)
    # the other sign: nothing from outside src/knee and the runtime script, none of the junk
    on_disk = " ".join(sorted(bundle_paths(output)))
    for absent in (
        "draw_other",
        "test_core",
        ".env",
        "blob.zip",
        "notes.md",
        "cache.nbc",
        "old.py",
        ".pyc",
        "a.dcm",
        "note.md",
        "test_outside",
        ".git",
        "pyproject",
    ):
        assert absent not in on_disk


def test_every_exclusion_is_listed_with_its_reason(world: Path) -> None:
    build(world)
    excluded = {
        item["path"]: item["reason"] for item in manifest_of(world / "out")["excluded"]
    }
    assert excluded == {
        "src/knee/__pycache__/": "excluded_directory",
        "src/knee/tests/": "excluded_directory",
        "src/knee/sub/archive/": "excluded_directory",
        "src/knee/.env": "credential_name",
        "src/knee/blob.zip": "archive",
        "src/knee/notes.md": "non_python_file",
        "src/knee/cache.nbc": "cache_file",
    }
    assert list(excluded) == sorted(excluded)


def test_copies_are_byte_identical_and_the_manifest_hashes_them(world: Path) -> None:
    build(world)
    output = world / "out"
    for entry in manifest_of(output)["files"]:
        copied = output / "dataset" / entry["path"]
        assert pk.sha256_file(copied) == (entry["sha256"], entry["bytes"])
    assert (output / "dataset/source/src/knee/core.py").read_bytes() == b"VALUE = 1\n"
    assert (output / "dataset/memory/profiles.npz").read_bytes() == (
        world / "memory/profiles.npz"
    ).read_bytes()
    assert manifest_of(output)["requires_python"] == ">=3.11"


def test_extra_runtime_script_is_copied_only_when_asked(world: Path) -> None:
    build(world, runtime_scripts=("scripts/draw_other.py",))
    manifest = manifest_of(world / "out")
    roles = {entry["path"]: entry["role"] for entry in manifest["files"]}
    assert roles["source/scripts/draw_other.py"] == "runtime_script"
    assert roles["source/scripts/run_interiors.py"] == "runtime_script"
    assert roles["source/src/knee/core.py"] == "source"


# ---- determinism ---------------------------------------------------------------------------


def test_two_builds_of_the_same_inputs_are_byte_identical(world: Path) -> None:
    build(world, output_dir=world / "first")
    build(world, output_dir=world / "second")
    names = (
        f"dataset/{pk.MANIFEST_NAME}",
        f"dataset/{pk.DATASET_METADATA_NAME}",
        f"kernel/{pk.NOTEBOOK_NAME}",
        f"kernel/{pk.KERNEL_METADATA_NAME}",
    )
    for name in names:
        assert (world / "first" / name).read_bytes() == (
            world / "second" / name
        ).read_bytes()


def test_changing_one_source_byte_changes_the_bundle_id(world: Path) -> None:
    first = build(world, output_dir=world / "first")["bundle_id"]
    (world / "project/src/knee/core.py").write_text("VALUE = 2\n")
    second = build(world, output_dir=world / "second")["bundle_id"]
    assert first != second
    assert build(world, output_dir=world / "third")["bundle_id"] == second


# ---- memory: copied, never modified, exactly two files --------------------------------------


def test_memory_is_not_modified(world: Path) -> None:
    memory = world / "memory"
    for name in pk.MEMORY_FILES:
        os.utime(memory / name, ns=(1_000_000_000, 1_000_000_000))
    before = {
        name: ((memory / name).read_bytes(), os.stat(memory / name).st_mtime_ns)
        for name in pk.MEMORY_FILES
    }
    build(world)
    after = {
        name: ((memory / name).read_bytes(), os.stat(memory / name).st_mtime_ns)
        for name in pk.MEMORY_FILES
    }
    assert before == after
    assert sorted(path.name for path in memory.iterdir()) == sorted(pk.MEMORY_FILES)


def _memory_missing_npz(memory: Path) -> None:
    (memory / "profiles.npz").unlink()


def _memory_extra_file(memory: Path) -> None:
    write(memory / "notes.txt", "extra")


def _memory_bad_json(memory: Path) -> None:
    (memory / "manifest.json").write_text("{not json")


def _memory_json_list(memory: Path) -> None:
    (memory / "manifest.json").write_text("[1, 2]")


def _memory_wrong_schema(memory: Path) -> None:
    manifest_path = memory / "manifest.json"
    document = json.loads(manifest_path.read_text())
    document["schema"] = "other-store/v1"
    manifest_path.write_text(json.dumps(document))


def _memory_not_zip(memory: Path) -> None:
    (memory / "profiles.npz").write_bytes(b"not a zip")


def _memory_symlinked_file(memory: Path) -> None:
    elsewhere = write_zip(memory.parent / "elsewhere.npz")
    (memory / "profiles.npz").unlink()
    (memory / "profiles.npz").symlink_to(elsewhere)


@pytest.mark.parametrize(
    ("damage", "match"),
    [
        (_memory_missing_npz, "exactly"),
        (_memory_extra_file, "exactly"),
        (_memory_bad_json, "not JSON"),
        (_memory_json_list, "JSON object"),
        (_memory_wrong_schema, "knee.diagnostic-store/v1"),
        (_memory_not_zip, "zip"),
        (_memory_symlinked_file, "symlink"),
    ],
)
def test_malformed_memory_is_refused(world: Path, damage, match: str) -> None:
    damage(world / "memory")
    refuses(world, match)


def test_symlinked_memory_directory_is_refused(world: Path) -> None:
    (world / "memory-link").symlink_to(world / "memory", target_is_directory=True)
    refuses(world, "symlink", memory_dir=world / "memory-link")


# ---- source: symlinks, traversal, completeness ----------------------------------------------


def test_symlinked_source_file_is_refused(world: Path) -> None:
    write(world / "elsewhere.py", "X = 1\n")
    (world / "project/src/knee/linked.py").symlink_to(world / "elsewhere.py")
    refuses(world, "symlink")


def test_symlinked_source_directory_is_refused(world: Path) -> None:
    write(world / "elsewhere" / "inner.py", "X = 1\n")
    (world / "project/src/knee/linked").symlink_to(
        world / "elsewhere", target_is_directory=True
    )
    refuses(world, "symlink")


def test_symlinked_runtime_script_is_refused(world: Path) -> None:
    (world / "project/scripts/run_interiors.py").unlink()
    write(world / "elsewhere.py", RUN_SCRIPT)
    (world / "project/scripts/run_interiors.py").symlink_to(world / "elsewhere.py")
    refuses(world, "symlink")


def test_symlinked_source_root_is_refused(world: Path) -> None:
    (world / "project-link").symlink_to(world / "project", target_is_directory=True)
    refuses(world, "symlink", source_root=world / "project-link")


@pytest.mark.parametrize(
    "script",
    [
        "../outside.py",
        "/etc/hostname.py",
        "scripts/../src/knee/core.py",
        "scripts//x.py",
        "src/knee/core.py",
        "scripts/missing.py",
        "scripts/notpython.txt",
        "scripts\\x.py",
    ],
)
def test_unsafe_or_wrong_runtime_script_is_refused(world: Path, script: str) -> None:
    write(world / "project/scripts/notpython.txt", "x")
    refuses(world, "unsafe path|must be scripts|missing", runtime_scripts=(script,))


def test_source_without_a_package_is_refused(world: Path) -> None:
    (world / "project/src/knee/__init__.py").unlink()
    refuses(world, "__init__")


# ---- output placement -----------------------------------------------------------------------


def test_existing_output_is_refused_and_left_alone(world: Path) -> None:
    write(world / "out" / "keep.txt", "mine")
    with pytest.raises(pk.PackagingError, match="already exists"):
        build(world)
    assert (world / "out" / "keep.txt").read_text() == "mine"


def test_output_inside_source_or_memory_is_refused(world: Path) -> None:
    with pytest.raises(pk.PackagingError, match="overlaps"):
        build(world, output_dir=world / "project" / "dist")
    with pytest.raises(pk.PackagingError, match="overlaps"):
        build(world, output_dir=world / "memory" / "dist")
    assert not (world / "project" / "dist").exists()
    assert sorted(path.name for path in (world / "memory").iterdir()) == sorted(
        pk.MEMORY_FILES
    )


def test_output_reached_through_a_symlink_into_the_source_is_refused(
    world: Path,
) -> None:
    (world / "alias").symlink_to(world / "project", target_is_directory=True)
    with pytest.raises(pk.PackagingError, match="overlaps"):
        build(world, output_dir=world / "alias" / "dist")
    assert not (world / "project" / "dist").exists()


def test_output_outside_both_is_accepted(world: Path) -> None:
    assert Path(
        build(world, output_dir=world / "elsewhere" / "deep" / "out")["output"]
    ).is_dir()


# ---- collisions -----------------------------------------------------------------------------


def _planned(*dests: str) -> list:
    return [pk.PlannedFile(Path("/x"), dest, "source") for dest in dests]


def test_collisions_are_refused_including_case_and_file_versus_directory() -> None:
    pk.check_collisions(_planned("source/a.py", "source/b.py", "source/sub/a.py"))
    with pytest.raises(pk.PackagingError, match="collision"):
        pk.check_collisions(_planned("source/a.py", "source/a.py"))
    with pytest.raises(pk.PackagingError, match="collision"):
        pk.check_collisions(_planned("source/Mod.py", "source/mod.py"))
    with pytest.raises(pk.PackagingError, match="collision"):
        pk.check_collisions(_planned("source/sub", "source/sub/a.py"))


def test_repeating_the_default_runtime_script_collides(world: Path) -> None:
    refuses(world, "collision", runtime_scripts=("scripts/run_interiors.py",))


# ---- offline wheelhouse and requirements ----------------------------------------------------


def make_wheelhouse(root: Path) -> Path:
    write_zip(root / WHEEL_NUMPY)
    write_zip(root / WHEEL_PURE)
    return root


GOOD_REQUIREMENTS = (
    "numpy==2.0.0 ; python_version >= '3.11' \\\n    --hash=sha256:"
    + "a" * 64
    + "\n# comment\nidna==3.7\n"
)


def test_wheelhouse_with_requirements_installs_by_requirements(world: Path) -> None:
    make_wheelhouse(world / "wheels")
    write(world / "reqs.txt", GOOD_REQUIREMENTS)
    build(world, wheelhouse=world / "wheels", requirements=world / "reqs.txt")
    output = world / "out"
    manifest = manifest_of(output)
    assert manifest["offline_install"] == {"mode": "requirements"}
    assert {
        "requirements.txt",
        f"wheelhouse/{WHEEL_NUMPY}",
        f"wheelhouse/{WHEEL_PURE}",
    } <= bundle_paths(output)
    assert (output / "dataset/requirements.txt").read_text() == GOOD_REQUIREMENTS


def test_wheelhouse_alone_installs_the_listed_wheels(world: Path) -> None:
    make_wheelhouse(world / "wheels")
    build(world, wheelhouse=world / "wheels")
    install = manifest_of(world / "out")["offline_install"]
    assert install == {
        "mode": "wheels",
        "wheels": sorted([f"wheelhouse/{WHEEL_NUMPY}", f"wheelhouse/{WHEEL_PURE}"]),
    }


def test_without_a_wheelhouse_nothing_is_installed_and_the_unknown_is_stated(
    world: Path,
) -> None:
    result = build(world)
    assert manifest_of(world / "out")["offline_install"] is None
    assert any("no wheelhouse" in warning for warning in result["warnings"])
    assert not any(
        path.startswith("wheelhouse") for path in bundle_paths(world / "out")
    )


def test_requirements_without_a_wheelhouse_are_refused(world: Path) -> None:
    write(world / "reqs.txt", GOOD_REQUIREMENTS)
    refuses(world, "need a wheelhouse", requirements=world / "reqs.txt")


@pytest.mark.parametrize(
    ("name", "content", "match"),
    [
        ("numpy-2.0.0-cp312-cp312-macosx_11_0_arm64.whl", b"PK\x03\x04", "Linux"),
        ("numpy-2.0.0-cp312-cp312-win_amd64.whl", b"PK\x03\x04", "Linux"),
        ("readme.txt", b"x", "non-wheel"),
        (WHEEL_PURE, b"not a zip", "zip"),
    ],
)
def test_bad_wheelhouse_entries_are_refused(
    world: Path, name: str, content: bytes, match: str
) -> None:
    write(world / "wheels" / name, content)
    refuses(world, match, wheelhouse=world / "wheels")


def test_empty_wheelhouse_is_refused(world: Path) -> None:
    (world / "wheels").mkdir()
    refuses(world, "empty", wheelhouse=world / "wheels")


@pytest.mark.parametrize(
    "line",
    [
        "numpy @ https://example.invalid/numpy.whl",
        "git+https://example.invalid/repo.git",
        "--index-url https://pypi.org/simple",
        "--extra-index-url https://example.invalid",
        "-r other.txt",
        "-e .",
        "./local/path",
        "file:///tmp/x.whl",
        "numpy==2.0.0 --find-links https://example.invalid",
        "numpy@1.0",
    ],
)
def test_requirements_that_could_reach_a_network_are_refused(line: str) -> None:
    with pytest.raises(pk.PackagingError):
        pk.validate_requirements("idna==3.7\n" + line + "\n")


def test_pinned_requirements_with_hashes_and_markers_are_accepted() -> None:
    pk.validate_requirements(GOOD_REQUIREMENTS)
    pk.validate_requirements("")


# ---- the caller's argv and the ids ----------------------------------------------------------


@pytest.mark.parametrize("argv", [(), ("--x", "{nonsense}"), ("--x", "{Source}")])
def test_bad_run_argv_is_refused(world: Path, argv: tuple[str, ...]) -> None:
    refuses(world, "argv|placeholder", run_argv=argv)


def test_run_argv_is_taken_verbatim_and_unreferenced_memory_is_warned(
    world: Path,
) -> None:
    argv = ("--split", "test", "--root", "{input}/some-comp", "--literal", "{x")
    result = build(world, run_argv=argv)
    assert manifest_of(world / "out")["run_argv"] == list(argv)
    assert any("{memory}" in warning for warning in result["warnings"])
    # the other sign: an argv that does reference the memory draws no such warning
    referenced = build(world, output_dir=world / "again", run_argv=DEFAULT_ARGV)
    assert not any("{memory}" in warning for warning in referenced["warnings"])


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("dataset_id", "no-owner-slash"),
        ("dataset_id", "alice/Bad_Slug"),
        ("dataset_id", "alice/abc"),
        ("kernel_id", "alice/" + "a" * 51),
        ("competition_sources", ()),
        ("competition_sources", ("Not A Slug",)),
    ],
)
def test_bad_ids_are_refused(world: Path, field: str, value) -> None:
    refuses(world, "must be|required", **{field: value})


# ---- metadata and notebook ------------------------------------------------------------------


def test_kaggle_metadata_is_offline_cpu_and_attaches_only_the_bundle(
    world: Path,
) -> None:
    build(world, competition_sources=("rsna-test-comp", "other-comp"))
    kernel = json.loads((world / "out/kernel" / pk.KERNEL_METADATA_NAME).read_text())
    assert kernel["enable_internet"] == "false"
    assert kernel["enable_gpu"] == "false"
    assert kernel["enable_tpu"] == "false"
    assert kernel["is_private"] == "true"
    assert kernel["id"] == "alice/rsna-knee-offline"
    assert kernel["title"] == "rsna knee offline"
    assert kernel["code_file"] == pk.NOTEBOOK_NAME
    assert kernel["dataset_sources"] == ["alice/rsna-knee-bundle"]
    assert kernel["competition_sources"] == ["rsna-test-comp", "other-comp"]
    assert kernel["kernel_sources"] == [] and kernel["model_sources"] == []
    dataset = json.loads((world / "out/dataset" / pk.DATASET_METADATA_NAME).read_text())
    assert dataset["id"] == "alice/rsna-knee-bundle"
    assert 6 <= len(dataset["title"]) <= 50


def test_notebook_is_valid_python_with_one_invocation_and_no_fallback(
    world: Path,
) -> None:
    build(world)
    notebook = json.loads((world / "out/kernel" / pk.NOTEBOOK_NAME).read_text())
    assert notebook["nbformat"] == 4
    code = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    sources = ["".join(cell["source"]) for cell in code]
    for source in sources:
        compile(source, "<cell>", "exec")
    joined = "\n".join(sources)
    for forbidden in pk.FORBIDDEN_NOTEBOOK_WORDS:
        assert forbidden not in joined
    assert "--no-index" in joined
    assert "check=True" in joined  # the install fails loudly
    config = pk.notebook_config(notebook)
    assert config["run_argv"] == list(DEFAULT_ARGV)
    assert config["bundle_id"] == manifest_of(world / "out")["bundle_id"]
    assert config["offline_install"] is None


def test_notebook_id_algorithm_matches_the_packagers() -> None:
    namespace: dict = {"hashlib": __import__("hashlib")}
    start = pk.CELL_VERIFY.index("def tree_id")
    end = pk.CELL_VERIFY.index("def verify_bundle")
    exec(pk.CELL_VERIFY[start:end], namespace)  # noqa: S102 — execute notebook-defined algorithm
    entries = [
        {"path": "b/x", "sha256": "1" * 64},
        {"path": "a/y", "sha256": "2" * 64},
    ]
    assert namespace["tree_id"](entries) == pk.tree_id(entries)
    assert namespace["tree_id"](entries) != pk.tree_id(entries[:1])


# ---- verification: the untampered passes, each tamper is caught ------------------------------


def _tamper_source(output: Path) -> None:
    (output / "dataset/source/src/knee/core.py").write_text("VALUE = 2\n")


def _tamper_extra_file(output: Path) -> None:
    write(output / "dataset/source/src/knee/extra.py", "")


def _tamper_missing_memory(output: Path) -> None:
    (output / "dataset/memory/profiles.npz").unlink()


def _tamper_symlink(output: Path) -> None:
    target = output / "dataset/source/src/knee/core.py"
    copy = output / "dataset/elsewhere.txt"
    shutil.copy(target, copy)
    target.unlink()
    target.symlink_to(copy)


def _tamper_notebook_syntax(output: Path) -> None:
    path = output / "kernel" / pk.NOTEBOOK_NAME
    notebook = json.loads(path.read_text())
    notebook["cells"][2]["source"] = ["def broken(:\n"]
    path.write_text(json.dumps(notebook))


def _tamper_notebook_submission(output: Path) -> None:
    path = output / "kernel" / pk.NOTEBOOK_NAME
    notebook = json.loads(path.read_text())
    notebook["cells"][3]["source"].append("open('submission.csv', 'w').write('fake')\n")
    path.write_text(json.dumps(notebook))


def _tamper_internet(output: Path) -> None:
    path = output / "kernel" / pk.KERNEL_METADATA_NAME
    metadata = json.loads(path.read_text())
    metadata["enable_internet"] = "true"
    path.write_text(json.dumps(metadata))


def _tamper_gpu(output: Path) -> None:
    path = output / "kernel" / pk.KERNEL_METADATA_NAME
    metadata = json.loads(path.read_text())
    metadata["enable_gpu"] = "true"
    path.write_text(json.dumps(metadata))


def _tamper_manifest_id(output: Path) -> None:
    path = output / "dataset" / pk.MANIFEST_NAME
    manifest = json.loads(path.read_text())
    manifest["bundle_id"] = "0" * 64
    path.write_text(json.dumps(manifest))


def test_an_untampered_bundle_verifies(world: Path) -> None:
    built = build(world)
    summary = pk.validate_bundle(world / "out")
    assert summary["bundle_id"] == built["bundle_id"]
    assert summary["file_count"] == len(EXPECTED_PATHS)


@pytest.mark.parametrize(
    ("tamper", "match"),
    [
        (_tamper_source, "mismatch"),
        (_tamper_extra_file, "not in the manifest"),
        (_tamper_missing_memory, "missing"),
        (_tamper_symlink, "symlink"),
        (_tamper_notebook_syntax, "does not parse"),
        (_tamper_notebook_submission, "submission"),
        (_tamper_internet, "enable_internet"),
        (_tamper_gpu, "enable_gpu"),
        (_tamper_manifest_id, "bundle_id"),
    ],
)
def test_each_tamper_is_caught(world: Path, tamper, match: str) -> None:
    build(world)
    tamper(world / "out")
    with pytest.raises(pk.PackagingError, match=match):
        pk.validate_bundle(world / "out")


# ---- the notebook, executed against a bundle laid out as Kaggle mounts it -------------------


def mount(world: Path, name: str = "rsna-knee-bundle") -> Path:
    mounted = world / "input" / name
    shutil.copytree(world / "out" / "dataset", mounted)
    write(
        world / "input" / "rsna-test-comp" / "test.csv", "study\n"
    )  # a competition mount is not a bundle
    return mounted


def run_notebook(world: Path) -> dict:
    notebook = json.loads((world / "out/kernel" / pk.NOTEBOOK_NAME).read_text())
    namespace: dict = {"__name__": "__notebook__"}
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            exec(compile("".join(cell["source"]), "<cell>", "exec"), namespace)  # noqa: S102 — integration-test generated notebook
    return namespace


def test_notebook_runs_the_one_script_with_the_callers_argv(world: Path) -> None:
    build(world)
    mounted = mount(world)
    namespace = run_notebook(world)
    result = json.loads((world / "working/diagnostic/result.json").read_text())
    assert result["argv"] == [
        "--split",
        "test",
        "--diagnostic-mode",
        "infer",
        "--diagnostic-memory",
        str(mounted / "memory"),
        "--diagnostic-output",
        str(world / "working/diagnostic"),
    ]
    assert result["knee"].startswith(str(mounted / "source" / "src"))
    assert result["memory"] == json.loads((world / "memory/manifest.json").read_text())
    record = json.loads((world / "working" / "package-run.json").read_text())
    assert record["returncode"] == 0
    assert record["bundle_id"] == namespace["CONFIG"]["bundle_id"]
    assert not (world / "working" / "submission.csv").exists()


def test_notebook_exposes_requested_runner_submission_at_working_root(
    world: Path,
) -> None:
    build(world, run_argv=SUBMISSION_ARGV)
    mount(world)
    write(world / "input/sample_submission.csv", "fixture-template\n")
    run_notebook(world)
    expected = "runner-owned fixture artifact\n"
    assert (world / "working/diagnostic/submission.csv").read_text() == expected
    assert (world / "working/submission.csv").read_text() == expected


def test_notebook_failure_raises_and_writes_no_substitute(world: Path) -> None:
    build(world, run_argv=(*SUBMISSION_ARGV, "--fail"))
    mount(world)
    write(world / "input/sample_submission.csv", "fixture-template\n")
    with pytest.raises(RuntimeError, match="exited 3"):
        run_notebook(world)
    assert (
        json.loads((world / "working" / "package-run.json").read_text())["returncode"]
        == 3
    )
    assert not (world / "working/submission.csv").exists()
    assert (world / "working/diagnostic/result.json").is_file()


def test_notebook_finds_the_bundle_wherever_kaggle_mounts_it(world: Path) -> None:
    build(world)
    mounted = world / "input" / "datasets" / "alice" / "renamed-mount"
    shutil.copytree(world / "out" / "dataset", mounted)
    run_notebook(world)
    assert (world / "working/diagnostic/result.json").is_file()


def test_notebook_refuses_a_changed_unlisted_missing_or_duplicated_bundle(
    world: Path,
) -> None:
    build(world)
    mounted = mount(world)
    core = mounted / "source/src/knee/core.py"
    core.write_text("VALUE = 2\n")
    with pytest.raises(RuntimeError, match="sha256 mismatch"):
        run_notebook(world)
    core.write_text("VALUE = 1\n")
    write(mounted / "source/src/knee/injected.py", "")
    with pytest.raises(RuntimeError, match="unlisted"):
        run_notebook(world)
    (mounted / "source/src/knee/injected.py").unlink()
    shutil.copytree(mounted, world / "input" / "second-copy")
    with pytest.raises(RuntimeError, match="found 2"):
        run_notebook(world)
    shutil.rmtree(world / "input" / "second-copy")
    shutil.rmtree(mounted)
    with pytest.raises(RuntimeError, match="found 0"):
        run_notebook(world)
    assert not (world / "working" / "result.json").exists()


def test_notebook_ignores_unlisted_dataset_metadata_but_still_runs(world: Path) -> None:
    build(world)
    mounted = mount(world)
    (mounted / pk.DATASET_METADATA_NAME).write_text("{}")
    run_notebook(world)
    assert (world / "working/diagnostic/result.json").is_file()


# ---- command line ---------------------------------------------------------------------------


def cli_args(world: Path, *extra: str, argv: str | None = None) -> list[str]:
    return [
        "build",
        "--source-root",
        str(world / "project"),
        "--memory-dir",
        str(world / "memory"),
        "--output-dir",
        str(world / "out"),
        "--dataset-id",
        "alice/rsna-knee-bundle",
        "--kernel-id",
        "alice/rsna-knee-offline",
        "--competition-source",
        "rsna-test-comp",
        "--run-argv-json",
        argv if argv is not None else json.dumps(list(DEFAULT_ARGV)),
        *extra,
    ]


def test_cli_builds_prints_a_summary_and_verifies(
    world: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert pk.main(cli_args(world)) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["bundle_id"] == manifest_of(world / "out")["bundle_id"]
    assert pk.main(["verify", str(world / "out")]) == 0
    assert json.loads(capsys.readouterr().out)["bundle_id"] == summary["bundle_id"]


def test_cli_refusals_exit_two_with_the_reason(
    world: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert pk.main(cli_args(world, argv='["--x","{nonsense}"]')) == 2
    assert pk.main(cli_args(world, argv="not json")) == 2
    assert pk.main(cli_args(world, argv='{"a": 1}')) == 2
    assert not (world / "out").exists()
    err = capsys.readouterr().err
    assert err.count("refused") == 3
    assert pk.main(cli_args(world)) == 0
    assert pk.main(cli_args(world)) == 2  # the output now exists
    assert pk.main(["verify", str(world / "nowhere")]) == 2
    _tamper_source(world / "out")
    assert pk.main(["verify", str(world / "out")]) == 2


def test_cli_passes_wheelhouse_requirements_and_runtime_scripts(world: Path) -> None:
    make_wheelhouse(world / "wheels")
    write(world / "reqs.txt", GOOD_REQUIREMENTS)
    args = cli_args(
        world,
        "--wheelhouse",
        str(world / "wheels"),
        "--requirements",
        str(world / "reqs.txt"),
        "--runtime-script",
        "scripts/draw_other.py",
    )
    assert pk.main(args) == 0
    paths = bundle_paths(world / "out")
    assert "requirements.txt" in paths and "source/scripts/draw_other.py" in paths
