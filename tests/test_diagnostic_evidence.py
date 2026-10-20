from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import numpy as np
import pytest

from knee.diagnosis.evidence import SourceEvidenceError, load_source, retain_source
from knee.diagnosis.models import Profile
from knee.encoding.counts import BankLayout, CountBundle, CountLayout


class State(StrEnum):
    SILENT = "silent"
    MIDDLE = "middle"


@dataclass(frozen=True)
class ProfileLike:
    subject: str
    bundle: CountBundle
    mode: str
    scope: str


def _profile(status: str) -> ProfileLike:
    layout = CountLayout(
        "layout-v1", "carrier-v1", (BankLayout("bank/a", 5), BankLayout("bank/b", 3))
    )
    if status == "silent":
        counts = ((0, 0, 0, 0, 0), (0, 0, 0))
    else:
        counts = ((0, 2, 0, 0, 0), (0, 0, 0))
    return ProfileLike(
        "cartilage", CountBundle(layout, counts), "full", f"status:{status}"
    )


def test_roundtrip_exact_sparse_counts_arrays_and_typed_fields(tmp_path: Path) -> None:
    huge = (1 << 120) + 17
    layout = CountLayout("large", "carrier", (BankLayout("huge", 4),))
    bundle = CountBundle(layout, ((0, huge, 0, 0),))
    nan_array = np.array([1.25, np.nan, np.inf, -np.inf], dtype=np.float64)
    words = np.array(["native", "unavailable"], dtype="<U16")
    source = {
        "study_uid": "1.2.840.1",
        "mode": "cheap/example",
        "profiles": (
            Profile(
                "object",
                bundle,
                "cheap/test",
                "region:caller",
                "frame-1",
                (("view", "sagittal"),),
                (("bank", "silent"),),
                (("path", "/source/frame.dcm"),),
            ),
            _profile("silent"),
            _profile("middle"),
        ),
        "profile_counts": (
            bundle.counts,
            _profile("silent").bundle.counts,
            _profile("middle").bundle.counts,
        ),
        "status": State.SILENT,
        "shared_measurement_arrays": {
            "a": nan_array,
            "b": nan_array.copy(),
            "words": words,
        },
        "frame": {"path": "/source/frame.dcm", "series_uid": "series", "z": 12},
    }
    receipt = retain_source(tmp_path, "1.2.840.1", source)
    restored = load_source(Path(receipt["manifest"]))
    root = restored["source"]
    assert isinstance(root, dict)
    assert root["profiles"][0]["$record_type"] == "knee.diagnosis.models.Profile"
    assert root["profiles"][0]["fields"]["bundle"]["sparse_rows"] == [[0, 1, str(huge)]]
    assert root["profiles"][0]["fields"]["context"] == (("view", "sagittal"),)
    assert root["profiles"][0]["fields"]["bundle"]["layout"]["banks"] == [
        {"name": "huge", "row_count": 4}
    ]
    assert root["profiles"][1]["fields"]["scope"] == "status:silent"
    assert root["profiles"][2]["fields"]["scope"] == "status:middle"
    assert root["status"] == {
        "$enum_type": f"{State.__module__}.{State.__qualname__}",
        "value": "silent",
    }
    arrays = root["shared_measurement_arrays"]
    assert arrays["a"] is arrays["b"]
    np.testing.assert_array_equal(arrays["a"], nan_array)
    np.testing.assert_array_equal(arrays["words"], words)
    assert root["frame"] == source["frame"]
    assert root["profile_counts"][0] == ((0, huge, 0, 0),)


def test_compact_product_source_and_path_roundtrip(tmp_path: Path) -> None:
    source = {
        "product": {"path": "/retained/product.h5", "sha256": "abc"},
        "mode": "full",
    }
    receipt = retain_source(tmp_path, "study-1", source)
    assert load_source(Path(receipt["manifest"]))["source"] == source


@pytest.mark.parametrize("uid", ["../escape", "a/b", "a\\b", "", ".", ".."])
def test_rejects_unsafe_uid(tmp_path: Path, uid: str) -> None:
    with pytest.raises(SourceEvidenceError, match="unsafe_study_uid"):
        retain_source(tmp_path, uid, {})


def test_refuses_repeat_publication(tmp_path: Path) -> None:
    retain_source(tmp_path, "same", {"mode": "full"})
    with pytest.raises(SourceEvidenceError, match="already_exists"):
        retain_source(tmp_path, "same", {"mode": "full"})


def test_rejects_profile_count_mismatch_before_publication(tmp_path: Path) -> None:
    profile = _profile("silent")
    with pytest.raises(SourceEvidenceError, match="profile_counts_mismatch"):
        retain_source(
            tmp_path, "bad", {"profiles": (profile,), "profile_counts": (((0,),),)}
        )
    assert not (tmp_path / "sources" / "bad").exists()


def test_rejects_object_arrays_and_unsupported_objects(tmp_path: Path) -> None:
    with pytest.raises(SourceEvidenceError, match="object_dtype_array_unsupported"):
        retain_source(
            tmp_path, "object-array", {"array": np.array([object()], dtype=object)}
        )
    with pytest.raises(SourceEvidenceError, match="unsupported_source_value"):
        retain_source(tmp_path, "unsupported", {"thing": object()})


def test_archive_corruption_is_named(tmp_path: Path) -> None:
    receipt = retain_source(
        tmp_path, "corrupt", {"array": np.arange(3, dtype=np.int16)}
    )
    archive = Path(receipt["manifest"]).parent / "arrays.npz"
    archive.write_bytes(archive.read_bytes() + b"corrupt")
    with pytest.raises(SourceEvidenceError, match="archive_digest_mismatch"):
        load_source(Path(receipt["manifest"]))
