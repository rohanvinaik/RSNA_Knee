"""The three drawers task 6.9 added, both signs: adapters pass values through, readers refuse drift.

Every adapter is called directly by name. The readers are checked against records shaped exactly
as the writer serialises them, and against tampered copies, so a saved record that disagrees with
its stage's vocabulary is reported rather than drawn.
"""

import json
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

from knee.collapse.regime import RegimeKey
from knee.collapse.structure import (
    AXIS_CODES,
    SUPERIOR_CODES,
    StructureBars,
    read_structure,
)
from knee.output.projection import COLUMN_BY_INDEX, Projection, read_output
from knee.pictures import collapse, output, study
from knee.pictures.study import SUPERIOR_ENDS, superior_end
from knee.predicates.findings import read_findings
from workbench.measure.object_analysis import array_table, structure_record
from workbench.render.field_frames import (
    REGIME_READINGS,
    saved_field,
    saved_structure,
)
from workbench.render.output_frames import saved_reading
from workbench.render.study_frames import saved_recorded

# The two bright bodies with a dark band between them of `tests/knee/collapse/test_structure.py`,
# under a coronal-like header: superior-inferior runs along the rows and the first row is superior.
CORONAL = np.array([1.0, 0.0, 0.0, 0.0, 0.0, -1.0])
CORONAL_NORMAL = np.array([0.0, 1.0, 0.0])


def _two_bodies_plane() -> np.ndarray:
    plane = np.full((60, 60), 0.0)
    plane[10:50, 15:45] = 100.0
    plane[25:35, 15:45] = 5.0
    plane[19:22, 19:22] = 0.0
    return plane


def _structure(plane):
    return read_structure(
        plane, CORONAL, CORONAL_NORMAL, (1.0, 1.0), 5.0, False, StructureBars()
    )


def _saved_structure_record(tmp_path: Path, reading, plane) -> dict:
    """A series record shaped as the writer saves a structural reading: JSON round-tripped, arrays on disk."""
    record, arrays = structure_record(reading)
    saved = {"acquired_plane": plane, **arrays} if plane is not None else dict(arrays)
    np.savez_compressed(tmp_path / "s.npz", allow_pickle=False, **saved)
    entry = {"artifact": "s.npz", "arrays": array_table(saved), "structure": record}
    return json.loads(json.dumps(entry, allow_nan=False))


class _Row:
    def __init__(self) -> None:
        self.ownership = type("O", (), {"code": "present"})()
        self.relations = type(
            "R", (), {"code": "construction_absent", "interstices": ()}
        )()


def _descriptor(array: np.ndarray) -> dict:
    return {
        "shape": array.shape,
        "dtype": array.dtype.str,
        "digest": sha256(
            array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
        ).hexdigest(),
        "bytes": array.nbytes,
    }


def _saved_series(tmp_path: Path) -> dict:
    """One series record shaped as the writer saves it, with its arrays on disk."""
    plane = np.arange(16, dtype=np.uint16).reshape(4, 4)
    median = np.array([[1.0, 2.0], [3.0, 4.0]])
    coverage = np.ones((2, 2))
    bounds = np.array(
        [[[0, 2, 0, 2], [0, 2, 2, 4]], [[2, 4, 0, 2], [2, 4, 2, 4]]], dtype=np.int64
    )
    arrays = {
        "acquired_plane": plane,
        "median": median,
        "minimum": median,
        "maximum": median,
        "coverage": coverage,
        "bounds_rc": bounds,
    }
    artifact = tmp_path / "series.npz"
    np.savez_compressed(artifact, allow_pickle=False, **arrays)
    readings: dict[str, object] = {name: None for name in REGIME_READINGS}
    readings["slices"] = 3
    return {
        "series_uid": "series",
        "view": ["Axial", "1", "1"],
        "code": "measured",
        "validation_code": None,
        "slice_index": 1,
        "source_plane": "slice-1.dcm",
        "spacing_rc_mm": [0.5, 0.5],
        "slice_thickness_mm": 3.0,
        "tile_shape_rc": [2, 2],
        "stack": ["stackable"],
        "regime": {"code": "read", "why": "read", "readings": readings},
        "artifact": "series.npz",
        "arrays": {name: _descriptor(array) for name, array in arrays.items()},
    }


# ---------------------------------------------------------------- the adapters


def test_the_field_adapter_passes_saved_values_through_and_keeps_absences() -> None:
    median = np.array([[1.0, np.nan]])
    frame = collapse.field_panels(
        {"slices": 3, "dark": None},
        median,
        median,
        median,
        median,
        None,
        None,
        "read",
        "w",
    )
    assert frame.readings == (("slices", 3), ("dark", None))
    np.testing.assert_array_equal(frame.median, median)
    assert frame.bounds_rc is None and frame.tile_shape_rc is None
    absent = collapse.field_panels({}, None, None, None, None, None, None, None, None)
    assert absent.readings == () and absent.median is None and absent.code is None


def test_the_study_adapter_keeps_the_stored_dtype_and_absences() -> None:
    plane = np.arange(4, dtype=np.uint16).reshape(2, 2)
    frame = study.recorded_panels(plane, (0.5, 0.5), 3.0, 1, ("a code",))
    assert frame.plane is not None and frame.plane.dtype == np.uint16
    assert frame.spacing_mm == (0.5, 0.5) and frame.slice_index == 1
    absent = study.recorded_panels(None, None, None, None, ())
    assert absent.plane is None and absent.thickness_mm is None and absent.codes == ()


def test_the_output_adapter_passes_the_reading_through_unchanged() -> None:
    reading = read_output(read_findings((_Row(),)))
    frame = output.panels(reading)
    assert frame.code == "projection_undeclared"
    assert frame.companion is reading.companion
    assert frame.submission_rows is None and frame.projection is None


def test_the_superior_end_is_named_from_the_field_stages_two_header_codes() -> None:
    """Task 7.1: the study picture says where superior lies, from the structural reading's axis
    and superior codes alone. Row 0 is the top of a drawn plane and column 0 its left; the stack
    is ordered ascending along its normal."""
    assert superior_end("rows", "decreasing") == "top_edge"
    assert superior_end("rows", "increasing") == "bottom_edge"
    assert superior_end("columns", "decreasing") == "left_edge"
    assert superior_end("columns", "increasing") == "right_edge"
    assert superior_end("normal", "decreasing") == "first_slice"
    assert superior_end("normal", "increasing") == "last_slice"
    assert superior_end(None, None) == "not_saved"
    assert superior_end("rows", None) == "not_saved"
    assert superior_end("ambiguous", "increasing") == "axis_ambiguous"
    assert superior_end("unreadable", "unreadable") == "axis_unreadable"
    assert superior_end("rows", "unreadable") == "direction_unreadable"
    assert superior_end("diagonal", "increasing") == "axis_code_unknown"
    assert superior_end("rows", "up") == "superior_code_unknown"


def test_the_superior_end_is_total_and_never_an_edge_without_a_direction() -> None:
    # MUST NOT: name an edge or a stack end from an axis that names no direction, from a
    # direction the stage could not read, or from a word the stage does not say; and every
    # answer is one of the declared ends, so a picture never carries a word from nowhere.
    edges = {
        "top_edge",
        "bottom_edge",
        "left_edge",
        "right_edge",
        "first_slice",
        "last_slice",
    }
    for axis in (*AXIS_CODES, None, "", "diagonal"):
        for superior in (*SUPERIOR_CODES, None, "", "up"):
            end = superior_end(axis, superior)
            assert end in SUPERIOR_ENDS, (axis, superior)
            if end in edges:
                assert axis in ("rows", "columns", "normal")
                assert superior in ("increasing", "decreasing")


# ---------------------------------------------------------------- the readers, positive


def test_the_field_reader_reconstitutes_the_saved_regime_and_squint(
    tmp_path: Path,
) -> None:
    record = _saved_series(tmp_path)
    artifact, frame = saved_field(tmp_path, record)
    assert artifact == tmp_path / "series.npz"
    assert frame.code == "read"
    assert dict(frame.readings)["slices"] == 3
    assert frame.median is not None and frame.median.shape == (2, 2)
    assert frame.tile_shape_rc == (2, 2)
    assert len(REGIME_READINGS) == len(RegimeKey.__dataclass_fields__)


def test_the_study_reader_labels_each_code_with_its_stage(tmp_path: Path) -> None:
    record = _saved_series(tmp_path)
    _, frame = saved_recorded(tmp_path, record)
    assert frame.plane is not None and frame.plane.dtype == np.uint16
    assert frame.codes[0] == "study stage stack codes: stackable"
    assert frame.codes[1] == "objects stage code: measured"
    assert frame.walk is None and frame.walk_indices == ()


def test_the_study_reader_reconstitutes_the_saved_walk(tmp_path: Path) -> None:
    record = _saved_series(tmp_path)
    walk = np.stack([np.full((4, 4), v, dtype=np.uint16) for v in (1, 2, 3)])
    np.savez_compressed(tmp_path / "walk.npz", allow_pickle=False, study_walk=walk)
    record["artifact"] = "walk.npz"
    record["arrays"] = {"study_walk": _descriptor(walk)}
    record["study"] = {
        "slice_codes": ["decoded", "decoded", "decoded"],
        "walk_indices": [0, 1, 2],
        "walk_array": "study_walk",
    }
    _, frame = saved_recorded(tmp_path, record)
    assert frame.plane is None
    assert frame.walk is not None and frame.walk.shape == (3, 4, 4)
    assert frame.walk_indices == (0, 1, 2)
    assert frame.slice_codes == ("decoded",) * 3
    # MUST NOT: a walk whose saved indices do not match its slices is a contradiction, refused.
    record["study"]["walk_indices"] = [0, 1]
    with pytest.raises(ValueError, match="saved_walk_indices_mismatch"):
        saved_recorded(tmp_path, record)


def test_the_field_reader_reconstitutes_the_writers_structural_record(
    tmp_path: Path,
) -> None:
    """Task 7.1: the structural reading the writer saves comes back as the stage returned it --
    its codes, its arrays, its profile and dip and its counts -- and is arranged, never remeasured.
    A reading the stage did not make round-trips too, over empty arrays, and arranges nothing."""
    plane = _two_bodies_plane()
    reading = _structure(plane)
    assert reading.code == "present"
    drawing = saved_structure(
        tmp_path, _saved_structure_record(tmp_path, reading, plane), None, None
    )
    assert drawing is not None
    frame = drawing.frame
    assert (frame.code, frame.axis_code, frame.superior_code) == (
        "present",
        "rows",
        "decreasing",
    )
    assert frame.axis == 0 and frame.sign == 1.0
    np.testing.assert_array_equal(frame.plane, plane)
    for name in ("air", "leg", "inside", "basins", "seam", "dark", "bodies"):
        np.testing.assert_array_equal(getattr(frame, name), getattr(reading, name))
    np.testing.assert_array_equal(frame.profile, reading.profile)
    np.testing.assert_array_equal(frame.profile_tiles, reading.profile_tiles)
    assert frame.dip == reading.dip
    assert dict(frame.counts) == dict(reading.counts)
    assert frame.squint is not None and reading.squint is not None
    np.testing.assert_array_equal(frame.squint, reading.squint.median)
    assert frame.squint_tile_shape_rc == reading.squint.tile_shape_rc
    assert drawing.arranged is not None
    assert drawing.placement == "tile_grid:objects_squint_bounds_not_saved"
    assert drawing.bounds_rc is None
    silent = _structure(None)
    assert silent.code == "predecessor_absent"
    quiet = saved_structure(
        tmp_path, _saved_structure_record(tmp_path, silent, None), None, None
    )
    assert quiet is not None
    assert quiet.frame.code == "predecessor_absent"
    assert quiet.frame.air.shape == (0, 0) and quiet.frame.profile.shape == (0,)
    assert quiet.arranged is None and quiet.placement == "no_tiles"
    assert (
        saved_structure(tmp_path, {"artifact": "s.npz", "arrays": {}}, None, None)
        is None
    )


def test_the_field_reader_refuses_a_structural_record_that_disagrees_with_the_stage(
    tmp_path: Path,
) -> None:
    # MUST NOT: draw a code the stage does not say, a dip outside the profile, or an array whose
    # digest is not the writer's; each is named and raised, never drawn.
    plane = _two_bodies_plane()
    record = _saved_structure_record(tmp_path, _structure(plane), plane)
    named = json.loads(json.dumps(record))
    named["structure"]["code"] = "lesion"
    with pytest.raises(ValueError, match="saved_structure_code_unknown"):
        saved_structure(tmp_path, named, None, None)
    stepped = json.loads(json.dumps(record))
    stepped["structure"]["dip"] = 99
    with pytest.raises(ValueError, match="saved_structure_dip_invalid"):
        saved_structure(tmp_path, stepped, None, None)
    tampered = json.loads(json.dumps(record))
    tampered["arrays"]["structure_leg"]["digest"] = "changed"
    with pytest.raises(ValueError, match="saved_array_digest_mismatch"):
        saved_structure(tmp_path, tampered, None, None)


def test_the_output_reader_round_trips_a_writer_shaped_entry() -> None:
    reading = read_output(read_findings((_Row(),)))
    saved = {
        "output": {
            "code": reading.code,
            "why": reading.why,
            "projection": None,
            "companion": [
                {
                    "index": r.index,
                    "column": r.column,
                    "code": r.code,
                    "reason": r.reason,
                    "subjects": list(r.subjects),
                    "candidates": r.candidates,
                }
                for r in reading.companion
            ],
            "submission_rows": None,
        }
    }
    assert saved_reading(saved) == reading


def test_the_output_reader_round_trips_a_declared_projection() -> None:
    projection = Projection(0.5, "a test, not the founder", "2026-10-12")
    reading = read_output(read_findings((_Row(),)), projection)
    saved = {
        "output": {
            "code": reading.code,
            "why": reading.why,
            "projection": {
                "value": 0.5,
                "author": projection.author,
                "declared": projection.declared,
            },
            "companion": [
                {
                    "index": r.index,
                    "column": r.column,
                    "code": r.code,
                    "reason": r.reason,
                    "subjects": list(r.subjects),
                    "candidates": r.candidates,
                }
                for r in reading.companion
            ],
            "submission_rows": [[c, v] for c, v in reading.rows or ()],
        }
    }
    assert saved_reading(saved) == reading


# ---------------------------------------------------------------- the readers, negative


def test_the_field_reader_refuses_a_reading_the_stage_does_not_own(
    tmp_path: Path,
) -> None:
    record = _saved_series(tmp_path)
    record["regime"]["readings"]["invented"] = 1.0
    with pytest.raises(ValueError, match="saved_regime_reading_unknown"):
        saved_field(tmp_path, record)


def test_the_field_reader_refuses_a_partly_saved_squint(tmp_path: Path) -> None:
    record = _saved_series(tmp_path)
    del record["arrays"]["coverage"]
    with pytest.raises(ValueError, match="saved_squint_incomplete"):
        saved_field(tmp_path, record)


def test_the_field_reader_refuses_a_tampered_array(tmp_path: Path) -> None:
    record = _saved_series(tmp_path)
    record["arrays"]["median"]["digest"] = "changed"
    with pytest.raises(ValueError, match="saved_array_digest_mismatch"):
        saved_field(tmp_path, record)


def test_the_field_reader_draws_a_series_with_no_regime_and_no_squint(
    tmp_path: Path,
) -> None:
    record = _saved_series(tmp_path)
    del record["regime"]
    for name in ("median", "minimum", "maximum", "coverage", "bounds_rc"):
        del record["arrays"][name]
    del record["tile_shape_rc"]
    _, frame = saved_field(tmp_path, record)
    assert frame.code is None and frame.readings == () and frame.median is None


def test_the_study_reader_refuses_a_spacing_that_is_not_a_pair(tmp_path: Path) -> None:
    record = _saved_series(tmp_path)
    record["spacing_rc_mm"] = [0.5]
    with pytest.raises(ValueError, match="saved_spacing_mismatch"):
        saved_recorded(tmp_path, record)


def test_the_output_reader_refuses_a_missing_short_or_misjoined_record() -> None:
    reading = read_output(read_findings((_Row(),)))
    base = {
        "code": reading.code,
        "why": reading.why,
        "projection": None,
        "companion": [
            {
                "index": r.index,
                "column": r.column,
                "code": r.code,
                "reason": r.reason,
                "subjects": list(r.subjects),
                "candidates": r.candidates,
            }
            for r in reading.companion
        ],
        "submission_rows": None,
    }
    with pytest.raises(ValueError, match="missing_saved_output"):
        saved_reading({})
    short = {**base, "companion": base["companion"][:11]}
    with pytest.raises(ValueError, match="saved_companion_count_mismatch"):
        saved_reading({"output": short})
    misjoined = {**base, "companion": [dict(r) for r in base["companion"]]}
    misjoined["companion"][0]["column"] = COLUMN_BY_INDEX[1][1]
    with pytest.raises(ValueError, match="saved_companion_column_mismatch"):
        saved_reading({"output": misjoined})
    # MUST NOT: submission rows beside a non-present standing are a contradiction, never drawn.
    rows = {**base, "submission_rows": [[c, 0.5] for _, c in COLUMN_BY_INDEX]}
    with pytest.raises(ValueError, match="saved_submission_rows_without_present"):
        saved_reading({"output": rows})
