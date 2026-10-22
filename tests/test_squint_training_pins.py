"""R4 intent: identical completed inputs resume; stale or incomplete inputs never do.

These are physical input-identity checks. They do not add an identity, anatomical
or clinical admission rule to the classical-AI system.
"""

from __future__ import annotations

import copy
import hashlib
import os
import zipfile

import pytest

from knee.diagnosis import squint_training_pins
from knee.diagnosis.squint_training_pins import (
    TrainingPinError,
    archive_study_inventory,
    checkpoint_identity_code,
    training_source_identity,
    verified_study_input,
)


@pytest.fixture
def study(tmp_path):
    root = tmp_path / "corpus"
    directory = root / "train_series" / "1.2.3" / "4.5"
    directory.mkdir(parents=True)
    (root / "train_series.csv").write_text(
        "StudyInstanceUID,SeriesInstanceUID,Fluid_Sensitive,Fat_Suppression,Anatomical_Plane\n"
        "1.2.3,4.5,True,False,Sagittal\n"
    )
    image = directory / "1.dcm"
    image.write_bytes(bytes(128) + b"DICM" + b"first image")
    second = directory / "2.dcm"
    second.write_bytes(bytes(128) + b"DICM" + b"second image")
    expected = {
        "4.5/1.dcm": {"size": image.stat().st_size},
        "4.5/2.dcm": {"size": second.stat().st_size},
    }
    return root, image, expected, tmp_path / "cache"


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "repo"
    for name in ("diagnosis", "study", "collapse", "objects"):
        directory = root / "src" / "knee" / name
        directory.mkdir(parents=True)
        (directory / "producer.py").write_text("VALUE = 1\n")
    (root / "scripts").mkdir()
    (root / "scripts" / "prepare_squint_training.py").write_text("VALUE = 1\n")
    (root / "pyproject.toml").write_text('[project]\nname = "knee"\n')
    (root / "uv.lock").write_text("version = 1\n")
    return root


@pytest.fixture
def checkpoint():
    return {
        "code": {"sha256": "a" * 64},
        "study_input": {"sha256": "b" * 64},
        "memory_manifest_sha256": "c" * 64,
        "record_sha256": "d" * 64,
    }


def test_identical_checkpoint_authorizes_resume(checkpoint):
    assert (
        checkpoint_identity_code(checkpoint, copy.deepcopy(checkpoint))
        == "checkpoint_pin_identical"
    )


def test_changed_source_must_not_resume(checkpoint):
    changed = copy.deepcopy(checkpoint)
    changed["code"]["sha256"] = "e" * 64
    assert checkpoint_identity_code(checkpoint, changed) == "checkpoint_source_changed"


def test_changed_study_must_not_resume(checkpoint):
    changed = copy.deepcopy(checkpoint)
    changed["study_input"]["sha256"] = "e" * 64
    assert checkpoint_identity_code(checkpoint, changed) == "checkpoint_study_changed"


def test_changed_parent_or_record_must_not_resume(checkpoint):
    changed = copy.deepcopy(checkpoint)
    changed["record_sha256"] = "e" * 64
    assert checkpoint_identity_code(checkpoint, changed) == "checkpoint_context_changed"


@pytest.mark.parametrize(
    "malformed", [None, {}, {"code": {}}, {"code": {"sha256": "a"}}]
)
def test_malformed_pin_must_not_authorize_resume(checkpoint, malformed):
    assert checkpoint_identity_code(checkpoint, malformed) == "checkpoint_pin_invalid"


def test_pin_includes_decoders_profiles_anchors_and_object_writers(repository):
    original = training_source_identity(repository, environment={"python": "test"})
    repeat = training_source_identity(repository, environment={"python": "test"})
    assert original == repeat
    for name in ("diagnosis", "study", "collapse", "objects"):
        path = repository / "src" / "knee" / name / "producer.py"
        previous = path.read_text()
        path.write_text(previous + "# changed producer\n")
        changed = training_source_identity(repository, environment={"python": "test"})
        assert changed["sha256"] != original["sha256"]
        path.write_text(previous)


def test_lock_reference_and_environment_change_source_epoch(repository, tmp_path):
    reference = tmp_path / "reference.json"
    reference.write_text('{"writer":"one"}')
    original = training_source_identity(
        repository,
        reference_files={"writer": reference},
        environment={"decoder": "one"},
    )
    reference.write_text('{"writer":"two"}')
    assert (
        training_source_identity(
            repository,
            reference_files={"writer": reference},
            environment={"decoder": "one"},
        )["sha256"]
        != original["sha256"]
    )
    reference.write_text('{"writer":"one"}')
    assert (
        training_source_identity(
            repository,
            reference_files={"writer": reference},
            environment={"decoder": "two"},
        )["sha256"]
        != original["sha256"]
    )
    (repository / "uv.lock").write_text("version = 2\n")
    assert (
        training_source_identity(
            repository,
            reference_files={"writer": reference},
            environment={"decoder": "one"},
        )["sha256"]
        != original["sha256"]
    )


def test_identical_files_reuse_cached_hashes(study, monkeypatch):
    root, _image, expected, cache = study
    original = verified_study_input(
        root, "1.2.3", expected_files=expected, cache_directory=cache
    )

    def must_not_read_bytes(_path):
        raise AssertionError("unchanged study was rehashed")

    monkeypatch.setattr(squint_training_pins, "_read_digest", must_not_read_bytes)
    assert (
        verified_study_input(
            root, "1.2.3", expected_files=expected, cache_directory=cache
        )
        == original
    )


def test_same_size_changed_bytes_invalidate_study_identity_even_if_mtime_restored(
    study,
):
    root, image, expected, cache = study
    original = verified_study_input(
        root, "1.2.3", expected_files=expected, cache_directory=cache
    )
    timestamp = image.stat()
    image.write_bytes(bytes(128) + b"DICM" + b"other image")
    os.utime(image, ns=(timestamp.st_atime_ns, timestamp.st_mtime_ns))
    changed = verified_study_input(
        root, "1.2.3", expected_files=expected, cache_directory=cache
    )
    assert changed["sha256"] != original["sha256"]


def test_timestamp_change_alone_keeps_content_identity(study):
    root, image, expected, cache = study
    original = verified_study_input(
        root, "1.2.3", expected_files=expected, cache_directory=cache
    )
    stat = image.stat()
    os.utime(image, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1000000))
    assert (
        verified_study_input(
            root, "1.2.3", expected_files=expected, cache_directory=cache
        )
        == original
    )


def test_changed_series_metadata_invalidates_study_identity(study):
    root, _image, expected, cache = study
    original = verified_study_input(
        root, "1.2.3", expected_files=expected, cache_directory=cache
    )
    (root / "train_series.csv").write_text(
        "StudyInstanceUID,SeriesInstanceUID,Fluid_Sensitive,Fat_Suppression,Anatomical_Plane\n"
        "1.2.3,4.5,True,True,Sagittal\n"
    )
    changed = verified_study_input(
        root, "1.2.3", expected_files=expected, cache_directory=cache
    )
    assert changed["sha256"] != original["sha256"]


def test_missing_series_metadata_cannot_claim_ready(study):
    root, _image, expected, cache = study
    (root / "train_series.csv").unlink()
    with pytest.raises(TrainingPinError, match="study_series_metadata_invalid:1.2.3"):
        verified_study_input(
            root, "1.2.3", expected_files=expected, cache_directory=cache
        )


def test_missing_expected_slice_is_incomplete_not_ready(study):
    root, image, expected, cache = study
    image.unlink()
    with pytest.raises(TrainingPinError, match="study_incomplete:1.2.3"):
        verified_study_input(
            root, "1.2.3", expected_files=expected, cache_directory=cache
        )


def test_added_slice_cannot_reuse_old_inventory(study):
    root, image, expected, cache = study
    verified_study_input(root, "1.2.3", expected_files=expected, cache_directory=cache)
    image.with_name("3.dcm").write_bytes(b"additional file")
    with pytest.raises(TrainingPinError, match="study_inventory_mismatch:1.2.3"):
        verified_study_input(
            root, "1.2.3", expected_files=expected, cache_directory=cache
        )


def test_current_directory_alone_does_not_prove_completion(study):
    root, _image, _expected, cache = study
    with pytest.raises(TrainingPinError, match="study_readiness_unknown:1.2.3"):
        verified_study_input(root, "1.2.3", expected_files=None, cache_directory=cache)


@pytest.mark.parametrize(
    "expected",
    [
        {},
        {"../1.dcm": {"size": 1}},
        {"4.5/1.dcm": {"size": 0}},
        {"4.5/1.dcm": {"size": True}},
    ],
)
def test_invalid_inventory_is_refused(study, expected):
    root, _image, _expected, cache = study
    with pytest.raises(TrainingPinError, match="study_inventory_invalid:1.2.3"):
        verified_study_input(
            root, "1.2.3", expected_files=expected, cache_directory=cache
        )


def test_corrupt_cache_is_refused_instead_of_silently_authorizing_resume(study):
    root, _image, expected, cache = study
    verified_study_input(root, "1.2.3", expected_files=expected, cache_directory=cache)
    (cache / "train-1.2.3.json").write_text("not JSON")
    with pytest.raises(TrainingPinError, match="study_cache_invalid"):
        verified_study_input(
            root, "1.2.3", expected_files=expected, cache_directory=cache
        )


def test_archive_inventory_checks_real_expected_bytes_and_partial_extraction(
    study, tmp_path
):
    root, image, expected, cache = study
    archive = tmp_path / "source.zip"
    with zipfile.ZipFile(archive, "w") as output:
        for name in expected:
            output.write(
                root / "train_series" / "1.2.3" / name, "train_series/1.2.3/" + name
            )
        output.writestr("train_series/9.9/1/1.dcm", b"another study")
    inventory = archive_study_inventory(archive, ["1.2.3"])
    assert set(inventory) == {"1.2.3"}
    original = verified_study_input(
        root, "1.2.3", expected_files=inventory["1.2.3"], cache_directory=cache
    )
    assert (
        original["files"]["4.5/1.dcm"]["sha256"]
        == hashlib.sha256(image.read_bytes()).hexdigest()
    )
    image.write_bytes(bytes(128) + b"DICM" + b"other image")
    with pytest.raises(TrainingPinError, match="study_content_mismatch:1.2.3"):
        verified_study_input(
            root, "1.2.3", expected_files=inventory["1.2.3"], cache_directory=cache
        )


def test_absent_study_or_invalid_archive_is_not_ready(tmp_path):
    archive = tmp_path / "source.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("train_series/1.2.3/1/1.dcm", b"one")
    with pytest.raises(TrainingPinError, match="study_readiness_unknown:9.9"):
        archive_study_inventory(archive, ["9.9"])
    archive.write_text("not a ZIP")
    with pytest.raises(TrainingPinError, match="study_inventory_unreadable"):
        archive_study_inventory(archive, ["1.2.3"])


def test_appledouble_sidecar_is_not_a_new_study_image(study):
    root, image, expected, cache = study
    original = verified_study_input(
        root, "1.2.3", expected_files=expected, cache_directory=cache
    )
    image.with_name("._" + image.name).write_bytes(b"AppleDouble metadata")
    assert (
        verified_study_input(
            root, "1.2.3", expected_files=expected, cache_directory=cache
        )
        == original
    )


def test_native_reader_never_passes_appledouble_to_dicom_decoder(tmp_path, monkeypatch):
    from knee.study import series as series_module
    from knee.study.tables import SeriesRow

    (tmp_path / "._1.dcm").write_bytes(b"AppleDouble metadata")
    (tmp_path / "1.dcm").write_bytes(b"real image placeholder")
    read = []

    class RealImageReached(Exception):
        pass

    def read_image(path):
        read.append(path.name)
        assert not path.name.startswith("._")
        raise RealImageReached

    monkeypatch.setattr(series_module, "read_slice", read_image)
    row = SeriesRow(
        study_uid="1",
        series_uid="2",
        fluid_sensitive="0",
        fat_suppression="0",
        anatomical_plane="Sagittal",
    )
    with pytest.raises(RealImageReached):
        series_module.read_series(tmp_path, row)
    assert read == ["1.dcm"]
