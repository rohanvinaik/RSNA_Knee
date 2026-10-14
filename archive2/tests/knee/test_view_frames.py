"""The view sheets: one per series, every reading on its plane, every silence in words.

Both signs. A record carrying only its plane draws the plane and names every other stage's
reading as not saved; a seated member that read nothing is a silence with the stage's own code,
never an empty picture; a saved array that disagrees with its descriptor is refused by name; and
an output directory outside the private data directory is an argument refusal.
"""

import json
import shutil
import uuid
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

from workbench.render import view_frames
from workbench.render._out import PROJECT, ArgumentRefusal


def _descriptor(array: np.ndarray) -> dict:
    return {
        "shape": list(array.shape),
        "dtype": array.dtype.str,
        "digest": sha256(
            array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
        ).hexdigest(),
        "bytes": array.nbytes,
    }


def _record(tmp_path: Path, arrays: dict[str, np.ndarray], **extra) -> dict:
    """One series record shaped as the writer saves it, with its arrays on disk."""
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **arrays)
    record = {
        "study_uid": "study",
        "series_uid": "series",
        "view": ["Sagittal", "0", "0"],
        "code": "measured",
        "slice_index": 1,
        "source_plane": "slice-1.dcm",
        "artifact": "series.npz",
        "arrays": {name: _descriptor(array) for name, array in arrays.items()},
    }
    record.update(extra)
    return json.loads(json.dumps(record, allow_nan=False))


def _loaded(tmp_path: Path, record: dict) -> dict[str, np.ndarray]:
    with np.load(tmp_path / record["artifact"], allow_pickle=False) as saved:
        return {name: saved[name] for name in saved.files}


def _plane() -> np.ndarray:
    return np.arange(16, dtype=np.uint16).reshape(4, 4)


def test_a_plane_alone_is_drawn_and_every_other_reading_is_named_not_saved(
    tmp_path: Path,
) -> None:
    record = _record(tmp_path, {"acquired_plane": _plane()})
    plane, panels = view_frames.view_panels(tmp_path, record, _loaded(tmp_path, record))
    assert plane is not None and plane.dtype == np.uint16
    assert (panels[0].stage, panels[0].status) == ("study", "saved")
    assert panels[0].paint is not None
    rest = panels[1:]
    assert {panel.status for panel in rest} == {"not_saved"}
    assert all(panel.paint is None for panel in rest)
    assert {panel.stage for panel in rest} == {
        "field",
        "lenses",
        "objects",
        "ownership",
        "relations",
    }


def test_no_plane_is_one_named_silence_and_nothing_is_overlaid_on_nothing(
    tmp_path: Path,
) -> None:
    record = _record(tmp_path, {"other": np.zeros(2)})
    plane, panels = view_frames.view_panels(tmp_path, record, _loaded(tmp_path, record))
    assert plane is None
    assert [(p.stage, p.reading, p.status) for p in panels] == [
        ("study", "acquired plane", "not_saved")
    ]


def test_a_silent_member_is_a_silence_with_the_stages_own_code(tmp_path: Path) -> None:
    """MUST NOT: a member with no edges is never drawn as an empty digit map."""
    arrays = {
        "acquired_plane": _plane(),
        "lens_codes_m": np.empty((0, 0), dtype=np.uint8),
        "lens_digits_m": np.empty((0, 0), dtype=np.int8),
        "lens_standings": np.empty((0, 0), dtype=np.uint8),
    }
    lenses = {
        "members": [
            {
                "population": "m",
                "code": "no_edges",
                "why": "the population has no edges",
                "low_edge": None,
                "high_edge": None,
                "population_count": 0,
                "minimum_population": 8,
                "normalisation": "none",
                "counts": [0, 0, 0, 0, 16, 0, 0],
                "picture_code": "no_edges",
                "codes_array": "lens_codes_m",
                "digits_array": "lens_digits_m",
            }
        ],
        "standing_counts": [0, 0, 0, 0, 0, 0],
        "standings_array": "lens_standings",
        "digit_silence": 2,
    }
    record = _record(tmp_path, arrays, lenses=lenses)
    _, panels = view_frames.view_panels(tmp_path, record, _loaded(tmp_path, record))
    by_reading = {(p.stage, p.reading): p for p in panels}
    member = by_reading[("lenses", "member m")]
    assert (member.status, member.code, member.paint) == ("silent", "no_edges", None)
    assert member.why == "the population has no edges"
    standing = by_reading[("lenses", "standing of the members")]
    assert (standing.status, standing.paint) == ("silent", None)


def test_a_tampered_array_is_refused_by_name_never_drawn(tmp_path: Path) -> None:
    record = _record(tmp_path, {"acquired_plane": _plane()})
    record["arrays"]["acquired_plane"]["digest"] = "changed"
    with pytest.raises(ValueError, match="saved_array_digest_mismatch"):
        view_frames.view_panels(tmp_path, record, _loaded(tmp_path, record))


def test_an_out_directory_outside_data_is_an_argument_refusal(tmp_path: Path) -> None:
    record = _record(tmp_path, {"acquired_plane": _plane()})
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    with pytest.raises(ArgumentRefusal, match="private data directory"):
        view_frames.draw(tmp_path, "study", tmp_path / "out")


def test_the_sheet_is_written_once_per_series_with_its_manifest(tmp_path: Path) -> None:
    """The impure edge, end to end: one image per series under data/, bound to the receipt."""
    record = _record(tmp_path, {"acquired_plane": _plane()})
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = view_frames.draw(tmp_path, "study", out)
        assert manifest["images"] == ["01-sagittal-fs0-fat0.png"]
        assert (out / "01-sagittal-fs0-fat0.png").exists()
        assert (out / "manifest.json").exists()
        view = manifest["views"][0]
        assert view["panels"][0]["drawn"] == "drawn"
        assert {panel["drawn"] for panel in view["panels"][1:]} == {"not_saved"}
        assert view["plane"]["dtype"] == "<u2"
    finally:
        shutil.rmtree(out, ignore_errors=True)
