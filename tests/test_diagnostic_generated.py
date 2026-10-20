from __future__ import annotations

from pathlib import Path

import pytest

from knee.diagnosis.evidence import load_source, retain_source
from knee.diagnosis.generated import GeneratedStudyError, generated_studies
from knee.encoding import h5_store
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    compile_layout,
)


def _manifest(study_uid: str) -> dict:
    spec = LayoutSpec(
        "generated-test-v1",
        "carrier-generated-test-v1",
        (
            BankSpec(
                "signal", "signal facet", (MetricSpec("tone", MetricKind.DIGIT, ()),)
            ),
        ),
    )
    compiled = compile_layout(spec)
    assert compiled is not None
    reference = "reference:test-v1"
    return {
        "study_uid": study_uid,
        "encoded_arrays": {},
        "mode": "full",
        "object_composition": {
            "schema": "knee_object_profiles/v1",
            "carrier_identity": compiled.carrier_id,
            "layout_fingerprint": compiled.fingerprint,
            "registry_fingerprint": "registry-test",
            "layout": {
                "version": compiled.version,
                "carrier_id": compiled.carrier_id,
                "fingerprint": compiled.fingerprint,
                "banks": [
                    {
                        "name": "signal",
                        "facet": "signal facet",
                        "metrics": [{"name": "tone", "kind": "digit", "words": []}],
                    }
                ],
            },
            "objects": {
                "acl": {
                    "status": "partial",
                    "preparation_status": "ok",
                    "reference_set_identity": reference,
                    "count_layout_id": f"{compiled.version}:{compiled.fingerprint}:{reference}",
                    "sparse_counts": [["signal", 4, 3]],
                    "assembly": {
                        "code": "partial",
                        "batches": [{"bank": "signal", "status": "partial"}],
                    },
                }
            },
        },
    }


def _write_product(directory: Path, study_uid: str, name: str = "product.h5") -> Path:
    pytest.importorskip("h5py")
    path = directory / name
    h5_store.write_h5(path, _manifest(study_uid), {})
    return path


def _write_empty_product(directory: Path, study_uid: str) -> Path:
    pytest.importorskip("h5py")
    manifest = _manifest(study_uid)
    manifest["object_composition"]["objects"] = {}
    path = directory / "empty.h5"
    h5_store.write_h5(path, manifest, {})
    return path


def test_generated_studies_yields_detached_profiles_and_cleans_one_study_at_a_time(
    tmp_path,
):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    product_paths: list[Path] = []

    def producer(uid: str, fresh: Path) -> Path:
        assert fresh.is_dir()
        assert not any(fresh.iterdir())
        path = _write_product(fresh, uid)
        product_paths.append(path)
        return path

    studies = generated_studies(
        ("study-001", "study-002"), producer, scratch_root=scratch
    )
    first_uid, first_profiles, first_source = next(studies)
    assert first_uid == "study-001"
    assert len(first_profiles) == 1
    assert first_profiles[0].source_id == first_uid
    assert first_profiles[0].bundle.counts[0][4] == 3
    assert first_source["profiles"] is first_profiles
    assert first_source["api"] == "knee.diagnosis.generated.generated_studies/v1"
    assert first_source["source_api"] == "generated"
    assert first_source["mode"] == "full"
    assert first_source["producer"].endswith(
        "test_generated_studies_yields_detached_profiles_and_cleans_one_study_at_a_time.<locals>.producer"
    )
    assert first_source["full_anatomy_runs"] == 1
    assert first_source["product_path"] == product_paths[0]
    assert first_source["product_transient"] is True
    assert first_source["product_retained"] is False
    assert product_paths[0].is_file()

    second_uid, second_profiles, second_source = next(studies)
    assert second_uid == "study-002"
    assert second_profiles[0].source_id == second_uid
    assert second_source["product_transient"] is True
    assert first_source["profiles"] is first_profiles
    assert not product_paths[0].exists()
    assert product_paths[1].is_file()

    with pytest.raises(StopIteration):
        next(studies)
    assert not product_paths[1].exists()
    assert not tuple(scratch.iterdir())
    # The detached profile remains usable after its source product is removed.
    assert first_profiles[0].bundle.counts[0][4] == 3


def test_generated_studies_leaves_external_product_untouched(tmp_path):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    external = tmp_path / "caller-owned"
    external.mkdir()
    product = _write_product(external, "study-001")

    def producer(uid: str, fresh: Path) -> Path:
        assert uid == "study-001"
        return product

    rows = list(generated_studies(("study-001",), producer, scratch_root=scratch))
    assert len(rows) == 1
    source = rows[0][2]
    assert source["product_path"] == product
    assert source["product_transient"] is False
    assert source["product_retained"] is True
    assert product.is_file()
    assert not tuple(scratch.iterdir())


def test_generated_studies_close_cleans_suspended_owned_product(tmp_path):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    produced: list[Path] = []

    def producer(uid: str, fresh: Path) -> Path:
        path = _write_product(fresh, uid)
        produced.append(path)
        return path

    rows = generated_studies(("study-001", "study-002"), producer, scratch_root=scratch)
    next(rows)
    assert produced[0].exists()
    rows.close()
    assert not produced[0].exists()
    assert not tuple(scratch.iterdir())


def test_generated_source_metadata_roundtrips_profiles_through_source_evidence(
    tmp_path,
):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    output = tmp_path / "retained"

    def producer(uid: str, fresh: Path) -> Path:
        return _write_product(fresh, uid)

    studies = generated_studies(("study-001",), producer, scratch_root=scratch)
    uid, profiles, source_metadata = next(studies)
    receipt = retain_source(output, uid, source_metadata)
    studies.close()
    loaded = load_source(Path(receipt["manifest"]))
    encoded_profiles = loaded["source"]["profiles"]
    assert encoded_profiles[0]["fields"]["source_id"] == uid
    bundle = encoded_profiles[0]["fields"]["bundle"]
    assert bundle["sparse_rows"] == [[0, 4, "3"]]
    assert profiles[0].source_id == uid
    assert not source_metadata["product_path"].exists()
    assert not tuple(scratch.iterdir())


@pytest.mark.parametrize(
    ("uids", "expected"),
    [
        ((), "study_uids_nonempty_required"),
        (("study-001", "study-001"), "study_uid_duplicate"),
        (("study/unsafe",), "study_uid_invalid"),
        ("study-001", "study_uids_sequence_required"),
    ],
)
def test_generated_studies_rejects_invalid_uid_selection_before_producer(
    tmp_path, uids, expected
):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    called = False

    def producer(uid: str, fresh: Path) -> Path:
        nonlocal called
        called = True
        return fresh / "product.h5"

    with pytest.raises(GeneratedStudyError, match=expected):
        next(generated_studies(uids, producer, scratch_root=scratch))
    assert not called
    assert not tuple(scratch.iterdir())


def test_generated_studies_rejects_empty_mismatched_or_missing_product_and_cleans(
    tmp_path,
):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    external = tmp_path / "caller-owned"
    external.mkdir()

    def empty(uid: str, fresh: Path) -> Path:
        return _write_empty_product(external, uid)

    empty_path = empty("study-001", external)
    with pytest.raises(GeneratedStudyError, match="generated_profiles_empty"):
        next(generated_studies(("study-001",), empty, scratch_root=scratch))
    assert empty_path.is_file()
    assert not tuple(scratch.iterdir())

    def mismatch(uid: str, fresh: Path) -> Path:
        return _write_product(fresh, "different-study")

    rows = generated_studies(("study-001",), mismatch, scratch_root=scratch)
    with pytest.raises(
        GeneratedStudyError, match="generated_product_study_uid_mismatch"
    ):
        next(rows)
    assert not tuple(scratch.iterdir())
    assert (
        empty_path.is_file()
    )  # External caller data was never owned by the generator.

    def missing(uid: str, fresh: Path) -> Path:
        return fresh / "absent.h5"

    with pytest.raises(GeneratedStudyError, match="generated_product_missing"):
        next(generated_studies(("study-001",), missing, scratch_root=scratch))
    assert not tuple(scratch.iterdir())


def test_generated_studies_producer_failure_does_not_leave_owned_temporary_data(
    tmp_path,
):
    scratch = tmp_path / "scratch"
    scratch.mkdir()

    def producer(uid: str, fresh: Path) -> Path:
        (fresh / "partial.txt").write_text("partial", encoding="utf-8")
        raise RuntimeError("producer failure")

    rows = generated_studies(("study-001",), producer, scratch_root=scratch)
    with pytest.raises(GeneratedStudyError, match="producer_failed"):
        next(rows)
    assert not tuple(scratch.iterdir())


def test_generated_studies_requires_existing_scratch_root(tmp_path):
    missing = tmp_path / "missing"

    def producer(uid: str, fresh: Path) -> Path:
        return fresh / "product.h5"

    with pytest.raises(
        GeneratedStudyError, match="scratch_root_existing_directory_required"
    ):
        next(generated_studies(("study-001",), producer, scratch_root=missing))
    assert not missing.exists()
