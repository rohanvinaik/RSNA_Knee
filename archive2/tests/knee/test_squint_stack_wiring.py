"""The squint stack on the route, in the receipt, in the picture adapter, on the stack drawer and
on the view sheet (the-funnel tasks 1.1 and 1.2), both signs. The route reads the stack per
series right after the regime, at the request's tile or the declared default, and carries it on
the run; the writer saves every array with its descriptor and the record carries the bar, the
grid and the code; the adapter selects the walked slices and alters nothing; the drawer refuses a
saved record that disagrees with the writer; the sheet draws the stack at its own slice and
refuses a stack that covers another plane."""

from __future__ import annotations

import importlib.util
import json
import shutil
import uuid
from pathlib import Path

import numpy as np
import pytest

from knee import pipeline
from knee.collapse.squint_stack import read_squint_stack
from knee.objects.analysis import DEFAULT_TILE_MM, AnalysisRequest
from knee.pictures import squint_stack as pictures
from knee.pictures.squint_stack import WALK_STANDINGS, stack_panels, walk_standing
from knee.study.series import Series, SeriesGeometry, walk_indices
from knee.study.tables import SeriesRow
from knee.telemetry import recording
from workbench.measure.object_analysis import (
    SQUINT_STACK_ARRAYS,
    array_table,
    series_record,
    squint_stack_record,
)
from workbench.render import squint_stack_frames, view_frames
from workbench.render._out import PROJECT, ArgumentRefusal

_fixture_path = Path(__file__).with_name("test_pipeline_measurements.py")
_fixture_spec = importlib.util.spec_from_file_location(
    "pipeline_measurement_fixture_for_squint_stack", _fixture_path
)
assert _fixture_spec is not None and _fixture_spec.loader is not None
_fixture_module = importlib.util.module_from_spec(_fixture_spec)
_fixture_spec.loader.exec_module(_fixture_module)
STUDY_UID = _fixture_module.STUDY_UID
STACKED_UID = _fixture_module.STACKED_UID
UNSTACKED_UID = _fixture_module.UNSTACKED_UID
_write_corpus = _fixture_module._write_corpus

#: The synthetic corpus: 16 x 16 planes at half a millimetre; a 2 mm tile is 4 px, a 4 x 4 grid.
TILE_MM = 2.0
SLICES, ROWS, COLUMNS = 3, 16, 16
AXIAL = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])


def _request() -> AnalysisRequest:
    return AnalysisRequest(
        tile_mm=TILE_MM,
        offsets_mm=(-0.5, 0.0, 0.5),
        direction_lps=(1.0, 0.0, 0.0),
        backend="reference",
    )


def _synthetic_series() -> Series:
    rows, columns = np.indices((ROWS, COLUMNS))
    volume = np.stack(
        [(200 + 11 * rows + 7 * columns + 3 * z).astype(np.uint16) for z in range(3)]
    )
    positions = np.array([[0.0, 0.0, float(z)] for z in range(SLICES)])
    geometry = SeriesGeometry(
        normal=np.array([0.0, 0.0, 1.0]),
        orientation=np.tile(AXIAL, (SLICES, 1)),
        position=positions,
        spacing=np.full((SLICES, 2), 0.5),
        along_normal=positions[:, 2],
        orientation_spread=0.0,
        origin_spread_mm=0.0,
    )
    indices = walk_indices(SLICES)
    return Series(
        row=SeriesRow("study", "series", "1", "0", "Axial"),
        directory=Path("/nonexistent/the-funnel/squint-wiring"),
        slices=(),
        stack=("stackable",),
        volume=volume,
        geometry=geometry,
        slice_codes=("decoded",) * SLICES,
        walk_indices=indices,
        walk=volume[list(indices)],
    )


def _descriptor_table(arrays: dict[str, np.ndarray]) -> dict:
    return json.loads(json.dumps(array_table(arrays), allow_nan=False))


def _saved_record(
    tmp_path: Path, *, with_stack: bool = True, plane: np.ndarray | None = None
) -> dict:
    """One series record shaped as the writer saves it, with its arrays on disk."""
    series = _synthetic_series()
    stack = read_squint_stack(series, TILE_MM)
    record, arrays = squint_stack_record(stack)
    assert series.walk is not None
    saved: dict[str, np.ndarray] = {"study_walk": series.walk}
    if with_stack:
        saved.update(arrays)
    if plane is not None:
        saved["acquired_plane"] = plane
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **saved)
    entry: dict = {
        "study_uid": "study",
        "series_uid": "series",
        "view": ["Axial", "1", "0"],
        "code": "measured",
        "slice_index": 1,
        "source_plane": "slice-1.dcm",
        "artifact": "series.npz",
        "arrays": _descriptor_table(saved),
        "study": {
            "slice_codes": ["decoded"] * SLICES,
            "walk_indices": list(series.walk_indices),
            "walk_array": "study_walk",
        },
    }
    if with_stack:
        entry["squint_stack"] = record
    return json.loads(json.dumps(entry, allow_nan=False))


def _loaded(tmp_path: Path, record: dict) -> dict[str, np.ndarray]:
    with np.load(tmp_path / record["artifact"], allow_pickle=False) as saved:
        return {name: saved[name] for name in saved.files}


# --- the route ---------------------------------------------------------------------------------


def test_run_study_reads_the_stack_per_series_right_after_the_regime_and_carries_it(
    tmp_path: Path,
) -> None:
    _write_corpus(tmp_path)
    with recording() as run_ledger:
        result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    names = [event.name for event in run_ledger.events()]
    assert names.count("study.consumed_by.squint_stack") == 2
    assert names.count("squint_stack.produced") == 2
    # Right after the regime: after the collapse's consumption of the study, before the
    # collapse's own production for the same series.
    assert (
        names.index("study.consumed_by.collapse")
        < names.index("study.consumed_by.squint_stack")
        < names.index("squint_stack.produced")
        < names.index("collapse.produced")
    )
    stacked, unstacked = result.series
    assert stacked.squint_stack is not None and unstacked.squint_stack is not None
    assert stacked.squint_stack.code == "present"
    assert stacked.squint_stack.tile_mm == TILE_MM
    assert stacked.squint_stack.median.shape == (3, 4, 4)
    assert stacked.squint_stack.centres_lps.shape == (3, 4, 4, 3)
    assert unstacked.squint_stack.code == "no_stacked_volume"
    produced = [
        dict(event.counts)
        for event in run_ledger.events()
        if event.name == "squint_stack.produced"
    ]
    assert produced == [{"slices": 3, "tiles": 48}, {"slices": 0, "tiles": 0}]


def test_without_a_request_the_route_squints_at_the_declared_default_tile(
    tmp_path: Path,
) -> None:
    _write_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID)
    stacked = result.series[0]
    assert stacked.squint_stack is not None
    assert stacked.squint_stack.code == "present"
    assert stacked.squint_stack.tile_mm == DEFAULT_TILE_MM
    # Eight millimetres at half a millimetre a pixel is a 16 px tile: one tile over the plane.
    assert stacked.squint_stack.median.shape == (3, 1, 1)
    assert DEFAULT_TILE_MM == 8.0


def test_a_run_built_without_the_operation_carries_no_stack() -> None:
    run = pipeline.SeriesRun("u", ("Axial", "1", "0"), ("stackable",), None, "read")
    assert run.squint_stack is None


# --- the writer --------------------------------------------------------------------------------


def test_the_series_record_carries_the_stacks_bar_grid_code_and_every_array(
    tmp_path: Path,
) -> None:
    _write_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    stacked = result.series[0]
    record, arrays = series_record(STUDY_UID, stacked, "reference")
    saved = record["squint_stack"]
    assert saved["code"] == "present"
    assert saved["tile_mm"] == TILE_MM
    assert saved["tile_shape_rc"] == [4, 4]
    assert saved["slices"] == 3 and saved["tiles_rc"] == [4, 4]
    assert saved["code_names"] == [
        "present",
        "no_stacked_volume",
        "geometry_unreadable",
    ]
    assert saved["arrays"] == {
        name: f"squint_stack_{name}" for name in SQUINT_STACK_ARRAYS
    }
    # Every array is saved under its own key, with the stage's own values, and described.
    assert stacked.squint_stack is not None
    for name in SQUINT_STACK_ARRAYS:
        np.testing.assert_array_equal(
            arrays[f"squint_stack_{name}"], getattr(stacked.squint_stack, name)
        )
    descriptors = array_table(arrays)
    assert descriptors["squint_stack_median"]["shape"] == (3, 4, 4)
    assert descriptors["squint_stack_centres_lps"]["dtype"] == "<f8"
    assert descriptors["squint_stack_bounds_rc"]["dtype"] == "<i8"
    # Plain data: it round-trips through the receipt's JSON, which refuses NaN.
    assert json.loads(json.dumps(saved, allow_nan=False)) == saved
    # The objects stage's own selected-slice squint keeps its keys; nothing collides.
    assert "median" in arrays and "squint_stack_median" in arrays


def test_an_absent_stack_is_saved_as_its_silence_with_empty_arrays() -> None:
    series = _synthetic_series()
    from dataclasses import replace

    stack = read_squint_stack(replace(series, volume=None), TILE_MM)
    record, arrays = squint_stack_record(stack)
    assert record["code"] == "no_stacked_volume"
    assert record["slices"] == 0 and record["tiles_rc"] == [0, 0]
    assert arrays["squint_stack_median"].shape == (0, 0, 0)
    assert arrays["squint_stack_centres_lps"].shape == (0, 0, 0, 3)
    assert json.loads(json.dumps(record, allow_nan=False)) == record


# --- the adapter -------------------------------------------------------------------------------


def test_the_standing_names_a_squinted_slice_and_every_silence_apart() -> None:
    assert walk_standing("present", 0, 3) == "squinted"
    assert walk_standing("present", 2, 3) == "squinted"
    assert walk_standing(None, 0, 3) == "stack_not_saved"
    assert walk_standing("no_stacked_volume", 0, 3) == "stack_absent"
    assert walk_standing("geometry_unreadable", 0, 0) == "stack_absent"
    assert walk_standing("present", 3, 3) == "slice_outside_stack"
    assert walk_standing("present", -1, 3) == "slice_outside_stack"
    assert walk_standing("present", 0, 0) == "slice_outside_stack"
    assert walk_standing("lesion", 0, 3) == "stack_code_unknown"


def test_the_standing_is_total_and_never_squinted_without_a_present_stack() -> None:
    # MUST NOT: draw a slice from a stack that is not present, nor from an index that is not a
    # whole number inside it; and every answer is one of the declared standings.
    for code in ("present", "no_stacked_volume", "geometry_unreadable", None, "", 1):
        for index in (0, 1, 2, 3, -1, True, 1.0, None, "1"):
            standing = walk_standing(code, index, 3)
            assert standing in WALK_STANDINGS, (code, index)
            if standing == "squinted":
                assert code == "present"
                assert type(index) is int and 0 <= index < 3


def test_the_adapter_selects_the_walked_slices_and_alters_nothing() -> None:
    series = _synthetic_series()
    stack = read_squint_stack(series, TILE_MM)
    frame = stack_panels(
        stack.code,
        stack.why,
        stack.tile_mm,
        stack.tile_shape_rc,
        stack.median,
        stack.coverage,
        stack.bounds_rc,
        series.walk_indices,
        series.walk,
    )
    assert frame.code == "present" and frame.slices == 3
    assert frame.tile_mm == TILE_MM and frame.tile_shape_rc == (4, 4)
    assert [step.index for step in frame.walked] == list(series.walk_indices)
    assert series.walk is not None
    for step, index in zip(frame.walked, series.walk_indices, strict=True):
        assert step.standing == "squinted"
        assert step.plane is not None and step.plane.dtype == np.uint16
        np.testing.assert_array_equal(step.plane, series.walk[index])
        assert step.median is not None and step.coverage is not None
        np.testing.assert_array_equal(step.median, stack.median[index])
        np.testing.assert_array_equal(step.coverage, stack.coverage[index])
    assert frame.median is not None and frame.median.dtype == np.float64
    assert frame.bounds_rc is not None and frame.bounds_rc.dtype == np.int64


def test_the_adapter_keeps_every_absence_absent() -> None:
    frame = stack_panels(None, None, None, None, None, None, None, (0, 2), None)
    assert frame.code is None and frame.slices == 0 and frame.median is None
    assert [step.standing for step in frame.walked] == ["stack_not_saved"] * 2
    assert all(step.plane is None and step.median is None for step in frame.walked)
    absent = stack_panels(
        "no_stacked_volume",
        "why",
        2.0,
        (0, 0),
        np.empty((0, 0, 0)),
        np.empty((0, 0, 0)),
        np.empty((0, 0, 4), dtype=np.int64),
        (0,),
        None,
    )
    assert [step.standing for step in absent.walked] == ["stack_absent"]


def test_the_adapter_hands_a_saved_index_through_uncoerced_and_names_one_outside_the_stack() -> (
    None
):
    # MUST NOT: round a saved 2.7 into slice 2, or raise on a saved word. Each saved index
    # reaches `walk_standing` as saved, and only a whole number inside the stack selects a map.
    series = _synthetic_series()
    stack = read_squint_stack(series, TILE_MM)
    saved_indices: tuple[object, ...] = (0, 2.7, "1", None, True, 2)
    frame = stack_panels(
        stack.code,
        stack.why,
        stack.tile_mm,
        stack.tile_shape_rc,
        stack.median,
        stack.coverage,
        stack.bounds_rc,
        saved_indices,
        None,
    )
    assert [step.standing for step in frame.walked] == [
        "squinted",
        "slice_outside_stack",
        "slice_outside_stack",
        "slice_outside_stack",
        "slice_outside_stack",
        "squinted",
    ]
    assert [step.index for step in frame.walked] == list(saved_indices)
    assert type(frame.walked[1].index) is float and frame.walked[2].index == "1"
    assert frame.walked[4].index is True
    for step in frame.walked[1:5]:
        assert step.median is None and step.coverage is None
    assert frame.walked[0].median is not None and frame.walked[5].median is not None
    np.testing.assert_array_equal(frame.walked[0].median, stack.median[0])
    np.testing.assert_array_equal(frame.walked[5].median, stack.median[2])


# --- the drawer's reader -----------------------------------------------------------------------


def test_the_reader_reconstitutes_a_writer_shaped_record(tmp_path: Path) -> None:
    record = _saved_record(tmp_path)
    artifact, frame = squint_stack_frames.saved_stack(tmp_path, record)
    assert artifact == tmp_path / "series.npz"
    assert frame.code == "present" and frame.slices == 3
    assert frame.tile_mm == TILE_MM and frame.tile_shape_rc == (4, 4)
    assert frame.median is not None and frame.median.shape == (3, 4, 4)
    assert [step.standing for step in frame.walked] == ["squinted"] * 3
    assert all(step.plane is not None for step in frame.walked)


def test_the_reader_says_when_no_stack_was_saved(tmp_path: Path) -> None:
    record = _saved_record(tmp_path, with_stack=False)
    _, frame = squint_stack_frames.saved_stack(tmp_path, record)
    assert frame.code is None and frame.median is None
    assert [step.standing for step in frame.walked] == ["stack_not_saved"] * 3


def test_the_reader_refuses_a_saved_record_that_disagrees_with_the_writer(
    tmp_path: Path,
) -> None:
    # MUST NOT: draw a tampered array, a code the stage does not say, a walk whose indices do
    # not match its slices, or a slice count that is not the maps'; each is named and raised.
    tampered = _saved_record(tmp_path)
    tampered["arrays"]["squint_stack_median"]["digest"] = "changed"
    with pytest.raises(ValueError, match="saved_array_digest_mismatch"):
        squint_stack_frames.saved_stack(tmp_path, tampered)
    named = _saved_record(tmp_path)
    named["squint_stack"]["code"] = "lesion"
    with pytest.raises(ValueError, match="saved_squint_stack_code_unknown"):
        squint_stack_frames.saved_stack(tmp_path, named)
    walked = _saved_record(tmp_path)
    walked["study"]["walk_indices"] = [0, 1]
    with pytest.raises(ValueError, match="saved_walk_indices_mismatch"):
        squint_stack_frames.saved_stack(tmp_path, walked)
    counted = _saved_record(tmp_path)
    counted["squint_stack"]["slices"] = 2
    with pytest.raises(ValueError, match="saved_squint_stack_slices_mismatch"):
        squint_stack_frames.saved_stack(tmp_path, counted)
    barred = _saved_record(tmp_path)
    barred["squint_stack"]["tile_mm"] = "two"
    with pytest.raises(ValueError, match="saved_squint_stack_not_a_number"):
        squint_stack_frames.saved_stack(tmp_path, barred)
    shaped = _saved_record(tmp_path)
    shaped["squint_stack"] = "yes"
    with pytest.raises(ValueError, match="saved_squint_stack_not_a_record"):
        squint_stack_frames.saved_stack(tmp_path, shaped)


def test_the_reader_hands_a_saved_index_through_and_names_one_that_is_not_a_whole_number(
    tmp_path: Path,
) -> None:
    # MUST NOT: coerce a saved 1.5 into slice 1, or raise on a saved "2": each reaches the
    # adapter's decision as saved and is named `slice_outside_stack`; a walk whose saved
    # indices are not a list at all disagrees with the writer and is refused by name.
    record = _saved_record(tmp_path)
    record["study"]["walk_indices"] = [0, 1.5, "2"]
    _, frame = squint_stack_frames.saved_stack(tmp_path, record)
    assert [step.standing for step in frame.walked] == [
        "squinted",
        "slice_outside_stack",
        "slice_outside_stack",
    ]
    assert [step.index for step in frame.walked] == [0, 1.5, "2"]
    assert frame.walked[0].median is not None
    assert frame.walked[1].median is None and frame.walked[2].median is None
    # The plane at each step is still the study stage's saved walk, whatever the index says.
    assert all(step.plane is not None for step in frame.walked)
    unlisted = _saved_record(tmp_path)
    unlisted["study"]["walk_indices"] = "012"
    with pytest.raises(ValueError, match="saved_walk_indices_not_a_list"):
        squint_stack_frames.saved_stack(tmp_path, unlisted)


def test_an_out_directory_outside_data_is_an_argument_refusal(tmp_path: Path) -> None:
    record = _saved_record(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    with pytest.raises(ArgumentRefusal, match="private data directory"):
        squint_stack_frames.draw(tmp_path, "study", tmp_path / "out")


def test_the_drawer_writes_one_picture_with_its_manifest(tmp_path: Path) -> None:
    """The impure edge, end to end: one image under data/, bound to the receipt."""
    record = _saved_record(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = squint_stack_frames.draw(tmp_path, "study", out)
        assert (out / "series.png").exists()
        assert (out / "manifest.json").exists()
        assert manifest["image"] == "series.png"
        assert manifest["standings"] == list(WALK_STANDINGS)
        (series,) = manifest["series"]
        assert series["squint_stack"]["code"] == "present"
        assert series["squint_stack"]["tiles_rc"] == [4, 4]
        assert [step["drawn"] for step in series["walked"]] == ["squinted"] * 3
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_drawer_draws_a_saved_index_that_is_not_a_whole_number_as_its_silence(
    tmp_path: Path,
) -> None:
    """The impure edge with a saved 1.5: the slice is a silence in words on the page, and the
    manifest carries the index as saved beside the standing, never a rounded slice."""
    record = _saved_record(tmp_path)
    record["study"]["walk_indices"] = [0, 1.5, 2]
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = squint_stack_frames.draw(tmp_path, "study", out)
        assert (out / "series.png").exists()
        (series,) = manifest["series"]
        assert series["walked"] == [
            {"index": 0, "standing": "squinted", "drawn": "squinted"},
            {
                "index": 1.5,
                "standing": "slice_outside_stack",
                "drawn": "slice_outside_stack",
            },
            {"index": 2, "standing": "squinted", "drawn": "squinted"},
        ]
    finally:
        shutil.rmtree(out, ignore_errors=True)


# --- the view sheet ----------------------------------------------------------------------------


def test_the_sheet_draws_the_stack_at_its_own_slice(tmp_path: Path) -> None:
    plane = _synthetic_series().volume
    assert plane is not None
    record = _saved_record(tmp_path, plane=plane[1])
    _, panels = view_frames.view_panels(tmp_path, record, _loaded(tmp_path, record))
    by_reading = {(p.stage, p.reading): p for p in panels}
    panel = by_reading[("field", "squint stack")]
    assert (panel.status, panel.code) == ("saved", "present")
    assert panel.paint is not None
    assert panel.arrays == ("squint_stack_median", "squint_stack_bounds_rc")
    # It sits right after the regime's split, before the structural reading.
    readings = [p.reading for p in panels]
    assert readings.index("background split") < readings.index("squint stack")
    assert readings.index("squint stack") < readings.index("structural reading")


def test_the_sheet_names_a_stack_that_was_not_saved_or_not_made(tmp_path: Path) -> None:
    plane = _synthetic_series().volume
    assert plane is not None
    unsaved = _saved_record(tmp_path, with_stack=False, plane=plane[1])
    _, panels = view_frames.view_panels(tmp_path, unsaved, _loaded(tmp_path, unsaved))
    panel = {(p.stage, p.reading): p for p in panels}[("field", "squint stack")]
    assert (panel.status, panel.paint) == ("not_saved", None)
    outside = _saved_record(tmp_path, plane=plane[1])
    outside["slice_index"] = 9
    _, panels = view_frames.view_panels(tmp_path, outside, _loaded(tmp_path, outside))
    panel = {(p.stage, p.reading): p for p in panels}[("field", "squint stack")]
    assert (panel.status, panel.code, panel.paint) == ("silent", "present", None)
    assert panel.why.startswith("slice_outside_stack")


def test_the_sheet_names_a_saved_slice_index_that_is_not_a_whole_number(
    tmp_path: Path,
) -> None:
    # MUST NOT: draw the stack at slice 1 for a saved "1" or a saved 1.5; the saved index reaches
    # the adapter's decision as saved and the panel is its silence, in words.
    plane = _synthetic_series().volume
    assert plane is not None
    for saved_index in ("1", 1.5):
        record = _saved_record(tmp_path, plane=plane[1])
        record["slice_index"] = saved_index
        _, panels = view_frames.view_panels(tmp_path, record, _loaded(tmp_path, record))
        panel = {(p.stage, p.reading): p for p in panels}[("field", "squint stack")]
        assert (panel.status, panel.code, panel.paint) == ("silent", "present", None)
        assert panel.why.startswith("slice_outside_stack")


def test_the_sheet_refuses_a_stack_that_covers_another_plane(tmp_path: Path) -> None:
    # MUST NOT: lay a 16 x 16 stack's tiles over a 4 x 4 plane.
    record = _saved_record(tmp_path, plane=np.arange(16, dtype=np.uint16).reshape(4, 4))
    with pytest.raises(ValueError, match="saved_squint_stack_covers_another_plane"):
        view_frames.view_panels(tmp_path, record, _loaded(tmp_path, record))


def test_the_picture_module_is_the_adapter_the_sheet_and_drawer_read() -> None:
    assert view_frames.squint_pictures is pictures
    assert squint_stack_frames.pictures is pictures
