"""The first lens on the route, in the receipt, in the picture adapter, on the lens drawer and
on the view sheet (the-funnel tasks 2.1, 2.2 and 2.3), both signs. The route reads the lens
per series after the line-ups and carries it on the run; the record is FROZEN: produced once
per series, saved once by the writer with its split, rule version and counts, and never
recomputed, its one reader in this phase being the tile digits (the-funnel task 3b.2), which
record that read themselves; the adapter selects the walked slices and alters nothing; the
drawer refuses a saved record that disagrees with the writer and draws one sheet per view; the
sheet draws the lens next to the line-up and names every silence."""

from __future__ import annotations

import importlib
import importlib.util
import json
import shutil
import uuid
from pathlib import Path

import numpy as np
import pytest

from knee import pipeline
from knee.collapse.first_lens import (
    LENS_CODES,
    RULE_VERSION,
    TILE_CODES,
    FirstLens,
    read_first_lens,
)
from knee.collapse.squint_stack import read_squint_stack
from knee.objects.analysis import DEFAULT_TILE_MM, AnalysisRequest
from knee.pictures import first_lens as pictures
from knee.pictures.first_lens import LENS_STANDINGS, lens_panels, walk_standing
from knee.study.series import Series, SeriesGeometry, walk_indices
from knee.study.tables import SeriesRow
from knee.telemetry import recording
from workbench.measure.object_analysis import (
    FIRST_LENS_ARRAYS,
    array_table,
    first_lens_record,
    series_record,
    squint_stack_record,
)
from workbench.render import all_frames, first_lens_frames, view_frames
from workbench.render._out import PROJECT, ArgumentRefusal

_fixture_path = Path(__file__).with_name("test_pipeline_measurements.py")
_fixture_spec = importlib.util.spec_from_file_location(
    "pipeline_measurement_fixture_for_first_lens", _fixture_path
)
assert _fixture_spec is not None and _fixture_spec.loader is not None
_fixture_module = importlib.util.module_from_spec(_fixture_spec)
_fixture_spec.loader.exec_module(_fixture_module)
STUDY_UID = _fixture_module.STUDY_UID
STACKED_UID = _fixture_module.STACKED_UID
UNSTACKED_UID = _fixture_module.UNSTACKED_UID
_write_corpus = _fixture_module._write_corpus

#: The synthetic series in memory: 24 x 24 planes at half a millimetre, a 2 mm tile is 4 px, a
#: 6 x 6 grid; three slices, all walked. The pattern is the proof gate's: the border is air,
#: the ring inside it straddles, the middle holds two bright tiles, a mixed tile away from the
#: air and a dark interior.
TILE_MM = 2.0
TILE_PX = 4
TILES = 6
SLICES = 3
AXIAL = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
AIR, BRIGHT, SPLIT = 0.0, 100.0, 10.0
PATTERN = ("BBBBBB", "BUUUUB", "BULMUB", "BULDUB", "BUUUUB", "BBBBBB")

BACKGROUND = TILE_CODES.index("background")
NOT_BACKGROUND = TILE_CODES.index("not_background")
UNDECIDED = TILE_CODES.index("undecided")
TILE_EMPTY = TILE_CODES.index("tile_empty")

#: Per slice: 20 border tiles are air, 12 ring tiles straddle, 4 are not background.
PER_SLICE = {"background": 20, "not_background": 4, "undecided": 12, "tile_empty": 0}


def _request() -> AnalysisRequest:
    return AnalysisRequest(
        tile_mm=TILE_MM,
        offsets_mm=(-0.5, 0.0, 0.5),
        direction_lps=(1.0, 0.0, 0.0),
        backend="reference",
    )


def _plane() -> np.ndarray:
    plane = np.full((TILES * TILE_PX, TILES * TILE_PX), BRIGHT, dtype=np.float64)
    for i, row in enumerate(PATTERN):
        for j, kind in enumerate(row):
            r0, c0 = i * TILE_PX, j * TILE_PX
            if kind in "BD":
                plane[r0 : r0 + TILE_PX, c0 : c0 + TILE_PX] = AIR
            elif kind in "UM":
                plane[r0 : r0 + TILE_PX // 2, c0 : c0 + TILE_PX] = AIR
    return plane


def _synthetic_series() -> Series:
    volume = np.stack([_plane().astype(np.uint16) for _ in range(SLICES)])
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
        row=SeriesRow("study", "series", "1", "1", "Coronal"),
        directory=Path("/nonexistent/the-funnel/first-lens-wiring"),
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
    tmp_path: Path,
    *,
    with_lens: bool = True,
    with_stack: bool = True,
    plane: np.ndarray | None = None,
    split: float = SPLIT,
    stack_tile_mm: float = TILE_MM,
) -> dict:
    """One series record shaped as the writer saves it, with its arrays on disk."""
    series = _synthetic_series()
    stack = read_squint_stack(series, TILE_MM)
    lens = read_first_lens(stack, split)
    assert series.walk is not None
    saved: dict[str, np.ndarray] = {"study_walk": series.walk}
    entry: dict = {
        "study_uid": "study",
        "series_uid": "series",
        "view": ["Coronal", "1", "1"],
        "code": "measured",
        "slice_index": 1,
        "source_plane": "slice-1.dcm",
        "artifact": "series.npz",
        "study": {
            "slice_codes": ["decoded"] * SLICES,
            "walk_indices": list(series.walk_indices),
            "walk_array": "study_walk",
        },
    }
    if with_stack:
        # The stack the lens is placed by; at another tile than the lens's it is another grid.
        stack_record, stack_arrays = squint_stack_record(
            read_squint_stack(series, stack_tile_mm)
        )
        saved.update(stack_arrays)
        entry["squint_stack"] = stack_record
    if with_lens:
        lens_record, lens_arrays = first_lens_record(lens)
        saved.update(lens_arrays)
        entry["first_lens"] = lens_record
    if plane is not None:
        saved["acquired_plane"] = plane
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **saved)
    entry["arrays"] = _descriptor_table(saved)
    return json.loads(json.dumps(entry, allow_nan=False))


def _loaded(tmp_path: Path, record: dict) -> dict[str, np.ndarray]:
    with np.load(tmp_path / record["artifact"], allow_pickle=False) as saved:
        return {name: saved[name] for name in saved.files}


# --- the route ---------------------------------------------------------------------------------


def test_run_study_reads_the_lens_once_per_series_after_the_lineups_and_only_the_digits_later_name_it(
    tmp_path: Path,
) -> None:
    _write_corpus(tmp_path)
    with recording() as run_ledger:
        result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    events = run_ledger.events()
    names = [event.name for event in events]
    assert names.count("squint_stack.consumed_by.first_lens") == 2
    assert names.count("first_lens.produced") == 2
    first = names.index("first_lens.produced")
    last = max(i for i, name in enumerate(names) if name == "first_lens.produced")
    # After the line-ups (the pairs record read by the line-up), after every stack, and
    # before anything of step 3 reads a record.
    assert names.index("pairs.consumed_by.lineup") < first
    assert (
        max(i for i, name in enumerate(names) if name == "squint_stack.produced")
        < first
    )
    assert last < names.index("lenses.consumed_by.vectors")
    assert last < names.index("ownership.produced")
    # THE FREEZE (task 2.2): the record is produced once per series and never recomputed. Its
    # readers in this phase are the tile digits (the-funnel task 3b.2), once per series right
    # after the lens, and then the depth collapse (the-funnel task 4.3), once per series after
    # the conjunction; each records that read itself, and no other row names it.
    readers = [name for name in names if name.startswith("first_lens.consumed_by")]
    assert readers == [
        *(["first_lens.consumed_by.tile_digits"] * 2),
        *(["first_lens.consumed_by.depth"] * 2),
    ]
    assert not [
        name
        for name in names[last + 1 :]
        if "first_lens" in name
        and name
        not in ("first_lens.consumed_by.tile_digits", "first_lens.consumed_by.depth")
    ]
    produced = [dict(e.counts) for e in events if e.name == "first_lens.produced"]
    assert all(
        set(counts) == {"background", "not_background", "undecided"}
        for counts in produced
    )
    stacked, unstacked = result.series
    assert isinstance(stacked.first_lens, FirstLens)
    assert stacked.first_lens.code in ("present", "split_unavailable")
    assert stacked.first_lens.codes.shape == (3, 4, 4)
    assert stacked.first_lens.rule_version == RULE_VERSION
    assert sum(stacked.first_lens.counts) == 3 * 4 * 4
    assert unstacked.first_lens is not None
    assert unstacked.first_lens.code == "predecessor_absent"
    assert unstacked.first_lens.codes.shape == (0, 0, 0)


def test_the_route_hands_the_lens_the_regimes_own_split(tmp_path: Path) -> None:
    _write_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    stacked, unstacked = result.series
    assert stacked.regime is not None and stacked.first_lens is not None
    split = stacked.regime.background_split
    if np.isfinite(split):
        assert stacked.first_lens.split == split
        assert stacked.first_lens.code == "present"
    else:
        assert np.isnan(stacked.first_lens.split)
        assert stacked.first_lens.code == "split_unavailable"
    # No regime: NaN handed over, and the absent stack is named before the split is read.
    assert unstacked.regime is None and unstacked.first_lens is not None
    assert np.isnan(unstacked.first_lens.split)


def test_without_a_request_the_route_reads_the_lens_at_the_declared_default_tile(
    tmp_path: Path,
) -> None:
    _write_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID)
    lens = result.series[0].first_lens
    assert lens is not None
    assert lens.codes.shape == (3, 1, 1)
    assert DEFAULT_TILE_MM == 8.0


def test_a_run_built_without_the_operation_carries_no_lens() -> None:
    run = pipeline.SeriesRun("u", ("Coronal", "1", "1"), ("stackable",), None, "read")
    assert run.first_lens is None


# --- the writer --------------------------------------------------------------------------------


def test_the_series_record_carries_the_lens_once_with_its_split_rule_and_counts(
    tmp_path: Path,
) -> None:
    _write_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    stacked, unstacked = result.series
    record, arrays = series_record(STUDY_UID, stacked, "reference")
    saved = record["first_lens"]
    lens = stacked.first_lens
    assert lens is not None
    assert saved["code"] == lens.code
    assert saved["code_names"] == list(LENS_CODES)
    assert saved["tile_code_names"] == list(TILE_CODES)
    assert saved["rule_version"] == RULE_VERSION
    assert saved["split"] == (float(lens.split) if np.isfinite(lens.split) else None)
    assert saved["counts"] == dict(zip(TILE_CODES, lens.counts, strict=True))
    assert saved["slices"] == 3 and saved["tiles_rc"] == [4, 4]
    assert saved["arrays"] == {name: f"first_lens_{name}" for name in FIRST_LENS_ARRAYS}
    np.testing.assert_array_equal(arrays["first_lens_codes"], lens.codes)
    descriptors = array_table(arrays)
    assert descriptors["first_lens_codes"]["shape"] == (3, 4, 4)
    assert descriptors["first_lens_codes"]["dtype"] == "|u1"
    # Plain data: it round-trips through the receipt's JSON, which refuses NaN.
    assert json.loads(json.dumps(saved, allow_nan=False)) == saved
    # Saved ONCE: one key, one array, and the stack's own keys beside them untouched.
    assert [name for name in arrays if name.startswith("first_lens_")] == [
        "first_lens_codes"
    ]
    assert "squint_stack_median" in arrays
    # The absent lens is saved as its silence, with empty codes and a split of None.
    quiet, quiet_arrays = series_record(STUDY_UID, unstacked, "reference")
    assert quiet["first_lens"]["code"] == "predecessor_absent"
    assert quiet["first_lens"]["slices"] == 0
    assert quiet["first_lens"]["tiles_rc"] == [0, 0]
    assert quiet["first_lens"]["split"] is None
    assert quiet_arrays["first_lens_codes"].shape == (0, 0, 0)


def test_a_split_the_regime_could_not_read_is_saved_as_none_never_zero() -> None:
    lens = read_first_lens(
        read_squint_stack(_synthetic_series(), TILE_MM), float("nan")
    )
    record, arrays = first_lens_record(lens)
    assert record["code"] == "split_unavailable"
    assert record["split"] is None
    assert record["counts"]["background"] == 0
    assert json.loads(json.dumps(record, allow_nan=False)) == record
    assert set(arrays) == {f"first_lens_{name}" for name in FIRST_LENS_ARRAYS}


# --- the adapter -------------------------------------------------------------------------------


def test_the_standing_names_a_named_slice_and_every_silence_apart() -> None:
    assert walk_standing("present", 0, 3) == "named"
    assert walk_standing("present", 2, 3) == "named"
    assert walk_standing("split_unavailable", 1, 3) == "named"
    assert walk_standing(None, 0, 3) == "lens_not_saved"
    assert walk_standing("predecessor_absent", 0, 0) == "lens_absent"
    assert walk_standing("present", 3, 3) == "slice_outside_lens"
    assert walk_standing("present", -1, 3) == "slice_outside_lens"
    assert walk_standing("present", 0, 0) == "slice_outside_lens"
    assert walk_standing("lesion", 0, 3) == "lens_code_unknown"


def test_the_standing_is_total_and_never_named_without_a_held_slice() -> None:
    # MUST NOT: draw a slice from a lens whose stack was absent, nor from an index that is not
    # a whole number inside it; and every answer is one of the declared standings.
    for code in (*LENS_CODES, None, "", 1):
        for index in (0, 1, 2, 3, -1, True, 1.0, None, "1"):
            standing = walk_standing(code, index, 3)
            assert standing in LENS_STANDINGS, (code, index)
            if standing == "named":
                assert code in ("present", "split_unavailable")
                assert type(index) is int and 0 <= index < 3


def test_the_adapter_selects_the_walked_slices_and_alters_nothing() -> None:
    series = _synthetic_series()
    stack = read_squint_stack(series, TILE_MM)
    lens = read_first_lens(stack, SPLIT)
    frame = lens_panels(
        lens.code,
        lens.why,
        lens.split,
        lens.rule_version,
        lens.counts,
        lens.codes,
        stack.bounds_rc,
        series.walk_indices,
        series.walk,
    )
    assert frame.code == "present" and frame.slices == SLICES
    assert frame.split == SPLIT and frame.rule_version == RULE_VERSION
    assert frame.counts == lens.counts
    assert [step.index for step in frame.walked] == list(series.walk_indices)
    assert series.walk is not None
    for step, index in zip(frame.walked, series.walk_indices, strict=True):
        assert step.standing == "named"
        assert step.plane is not None and step.plane.dtype == np.uint16
        np.testing.assert_array_equal(step.plane, series.walk[index])
        assert step.codes is not None and step.codes.dtype == np.uint8
        np.testing.assert_array_equal(step.codes, lens.codes[index])
    assert frame.codes is not None and frame.codes.dtype == np.uint8
    assert frame.bounds_rc is not None and frame.bounds_rc.dtype == np.int64


def test_the_adapter_keeps_every_absence_absent() -> None:
    frame = lens_panels(None, None, None, None, None, None, None, (0, 2), None)
    assert frame.code is None and frame.slices == 0 and frame.codes is None
    assert frame.split is None and frame.counts is None
    assert [step.standing for step in frame.walked] == ["lens_not_saved"] * 2
    assert all(step.plane is None and step.codes is None for step in frame.walked)
    absent = lens_panels(
        "predecessor_absent",
        "why",
        None,
        RULE_VERSION,
        (0, 0, 0, 0),
        np.empty((0, 0, 0), dtype=np.uint8),
        np.empty((0, 0, 4), dtype=np.int64),
        (0,),
        None,
    )
    assert [step.standing for step in absent.walked] == ["lens_absent"]


# --- the drawer's reader -----------------------------------------------------------------------


def test_the_reader_reconstitutes_a_writer_shaped_record(tmp_path: Path) -> None:
    record = _saved_record(tmp_path)
    artifact, frame = first_lens_frames.saved_lens(tmp_path, record)
    assert artifact == tmp_path / "series.npz"
    assert frame.code == "present" and frame.slices == SLICES
    assert frame.split == SPLIT and frame.rule_version == RULE_VERSION
    assert frame.counts == tuple(PER_SLICE[name] * SLICES for name in TILE_CODES)
    assert frame.codes is not None and frame.codes.shape == (SLICES, TILES, TILES)
    assert frame.bounds_rc is not None and frame.bounds_rc.shape == (TILES, TILES, 4)
    assert [step.standing for step in frame.walked] == ["named"] * SLICES
    assert all(step.plane is not None for step in frame.walked)
    assert first_lens_frames.tile_counts(frame.walked[0].codes) == PER_SLICE


def test_the_reader_says_when_no_lens_was_saved(tmp_path: Path) -> None:
    record = _saved_record(tmp_path, with_lens=False)
    _, frame = first_lens_frames.saved_lens(tmp_path, record)
    assert frame.code is None and frame.codes is None and frame.bounds_rc is None
    assert [step.standing for step in frame.walked] == ["lens_not_saved"] * SLICES
    unavailable = _saved_record(tmp_path, split=float("nan"))
    _, frame = first_lens_frames.saved_lens(tmp_path, unavailable)
    assert frame.code == "split_unavailable" and frame.split is None
    assert [step.standing for step in frame.walked] == ["named"] * SLICES


def test_the_reader_refuses_a_saved_record_that_disagrees_with_the_writer(
    tmp_path: Path,
) -> None:
    # MUST NOT: draw a tampered array, a code the stage does not say, a slice count that is
    # not the codes', a vocabulary that is not the stage's, a split that is not a number,
    # counts that are not the stage's, a lens saved without its stack, or a stack whose grid
    # is not the lens's; each is named and raised.
    tampered = _saved_record(tmp_path)
    tampered["arrays"]["first_lens_codes"]["digest"] = "changed"
    with pytest.raises(ValueError, match="saved_array_digest_mismatch"):
        first_lens_frames.saved_lens(tmp_path, tampered)
    named = _saved_record(tmp_path)
    named["first_lens"]["code"] = "lesion"
    with pytest.raises(ValueError, match="saved_first_lens_code_unknown"):
        first_lens_frames.saved_lens(tmp_path, named)
    counted = _saved_record(tmp_path)
    counted["first_lens"]["slices"] = 2
    with pytest.raises(ValueError, match="saved_first_lens_slices_mismatch"):
        first_lens_frames.saved_lens(tmp_path, counted)
    worded = _saved_record(tmp_path)
    worded["first_lens"]["tile_code_names"] = ["background", "not_background"]
    with pytest.raises(ValueError, match="saved_first_lens_vocabulary_mismatch"):
        first_lens_frames.saved_lens(tmp_path, worded)
    barred = _saved_record(tmp_path)
    barred["first_lens"]["split"] = "ten"
    with pytest.raises(ValueError, match="saved_first_lens_not_a_number"):
        first_lens_frames.saved_lens(tmp_path, barred)
    miscounted = _saved_record(tmp_path)
    miscounted["first_lens"]["counts"] = {"background": 1}
    with pytest.raises(ValueError, match="saved_first_lens_counts_invalid"):
        first_lens_frames.saved_lens(tmp_path, miscounted)
    shaped = _saved_record(tmp_path)
    shaped["first_lens"] = "yes"
    with pytest.raises(ValueError, match="saved_first_lens_not_a_record"):
        first_lens_frames.saved_lens(tmp_path, shaped)
    alone = _saved_record(tmp_path, with_stack=False)
    with pytest.raises(ValueError, match="saved_first_lens_without_a_stack"):
        first_lens_frames.saved_lens(tmp_path, alone)
    other_grid = _saved_record(tmp_path, stack_tile_mm=4.0)
    with pytest.raises(ValueError, match="saved_first_lens_grid_mismatch"):
        first_lens_frames.saved_lens(tmp_path, other_grid)


def test_an_out_directory_outside_data_is_an_argument_refusal(tmp_path: Path) -> None:
    record = _saved_record(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    with pytest.raises(ArgumentRefusal, match="private data directory"):
        first_lens_frames.draw(tmp_path, "study", tmp_path / "out")


def test_the_drawer_writes_one_sheet_per_view_with_its_manifest(tmp_path: Path) -> None:
    """The impure edge, end to end: one image per series under data/, bound to the receipt."""
    record = _saved_record(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = first_lens_frames.draw(tmp_path, "study", out)
        assert manifest["images"] == ["01-coronal-fs1-fat1.png"]
        assert manifest["image"] == "01-coronal-fs1-fat1.png"
        assert (out / "01-coronal-fs1-fat1.png").exists()
        assert (out / "manifest.json").exists()
        assert manifest["standings"] == list(LENS_STANDINGS)
        assert manifest["legend"]["tile_codes"]["not_background"] is None
        (series,) = manifest["series"]
        assert series["image"] == "01-coronal-fs1-fat1.png"
        assert series["first_lens"]["code"] == "present"
        assert series["first_lens"]["split"] == SPLIT
        assert series["first_lens"]["tiles_rc"] == [TILES, TILES]
        assert [step["drawn"] for step in series["walked"]] == ["named"] * SLICES
        assert all(step["counts"] == PER_SLICE for step in series["walked"])
    finally:
        shutil.rmtree(out, ignore_errors=True)


# --- the view sheet ----------------------------------------------------------------------------


def test_the_sheet_draws_the_lens_at_its_own_slice_next_to_the_lineup(
    tmp_path: Path,
) -> None:
    plane = _synthetic_series().volume
    assert plane is not None
    record = _saved_record(tmp_path, plane=plane[1])
    _, panels = view_frames.view_panels(tmp_path, record, _loaded(tmp_path, record))
    by_reading = {(p.stage, p.reading): p for p in panels}
    panel = by_reading[("field", "first lens")]
    assert (panel.status, panel.code) == ("saved", "present")
    assert panel.paint is not None
    assert panel.arrays == ("first_lens_codes",)
    readings = [p.reading for p in panels]
    assert readings.index("line-up") + 1 == readings.index("first lens")
    assert readings.index("first lens") < readings.index("structural reading")


def test_the_sheet_names_a_lens_that_was_not_saved_or_cannot_be_shown(
    tmp_path: Path,
) -> None:
    plane = _synthetic_series().volume
    assert plane is not None
    unsaved = _saved_record(tmp_path, with_lens=False, plane=plane[1])
    _, panels = view_frames.view_panels(tmp_path, unsaved, _loaded(tmp_path, unsaved))
    panel = {(p.stage, p.reading): p for p in panels}[("field", "first lens")]
    assert (panel.status, panel.paint) == ("not_saved", None)
    outside = _saved_record(tmp_path, plane=plane[1])
    outside["slice_index"] = 9
    _, panels = view_frames.view_panels(tmp_path, outside, _loaded(tmp_path, outside))
    panel = {(p.stage, p.reading): p for p in panels}[("field", "first lens")]
    assert (panel.status, panel.code, panel.paint) == ("silent", "present", None)
    assert panel.why.startswith("slice_outside_lens")


def test_the_sheet_refuses_a_lens_that_covers_another_plane(tmp_path: Path) -> None:
    # MUST NOT: lay a 24 x 24 lens's tiles over a 4 x 4 plane. The panel is asked directly:
    # on the whole sheet the squint stack's own panel refuses the same plane first.
    record = _saved_record(tmp_path)
    with pytest.raises(ValueError, match="saved_first_lens_covers_another_plane"):
        view_frames.first_lens_panel(
            np.arange(16, dtype=np.uint16).reshape(4, 4), tmp_path, record
        )


def test_the_sheet_is_drawn_with_the_lens_panel(tmp_path: Path) -> None:
    plane = _synthetic_series().volume
    assert plane is not None
    record = _saved_record(tmp_path, plane=plane[1])
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = view_frames.draw(tmp_path, "study", out)
        (view,) = manifest["views"]
        panel = next(p for p in view["panels"] if p["reading"] == "first lens")
        assert panel["drawn"] == "drawn"
        assert "first_lens_frames" in manifest["reused_drawers_sha256"]
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_picture_module_is_the_adapter_the_sheet_and_drawer_read() -> None:
    assert first_lens_frames.pictures is pictures
    assert view_frames.lens_pictures is pictures
    assert view_frames.first_lens_frames is first_lens_frames
    assert ("collapse", "first_lens", "first_lens_frames") in all_frames.DRAWINGS
    module = importlib.import_module("workbench.render.first_lens_frames")
    assert module.draw is first_lens_frames.draw
