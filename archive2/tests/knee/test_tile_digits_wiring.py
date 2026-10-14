"""The tile digits on the route, in the receipt, in the picture adapter, on the digit drawer and
on the view sheet (the-funnel tasks 3b.2 and 3b.3), both signs. The route reads the digits per
series right after the first lens, under the regime's own population bar, and carries them on the
run; the writer saves the record once with its edges, bar, counts and two arrays; the adapter
selects the walked slices and alters nothing; the drawer refuses a saved record that disagrees
with the writer and draws one sheet per view with silence as silence; the sheet draws the digits
next to the first lens and names every silence."""

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
from knee.collapse.first_lens import read_first_lens
from knee.collapse.squint_stack import read_squint_stack
from knee.lenses.digits import DIGIT_CODES
from knee.lenses.places import CODE_VALUES, SILENT
from knee.lenses.tiles import (
    DEFAULT_MINIMUM_POPULATION,
    TILE_DIGIT_CODES,
    TileDigits,
    read_tile_digits,
)
from knee.objects.analysis import DEFAULT_TILE_MM, AnalysisRequest
from knee.pictures import tiles as pictures
from knee.pictures.tiles import DIGIT_STANDINGS, digit_panels, walk_standing
from knee.study.series import Series, SeriesGeometry, walk_indices
from knee.study.tables import SeriesRow
from knee.telemetry import recording
from workbench.measure.object_analysis import (
    TILE_DIGIT_ARRAYS,
    array_table,
    first_lens_record,
    series_record,
    squint_stack_record,
    tile_digits_record,
)
from workbench.render import all_frames, tile_digit_frames, view_frames
from workbench.render._out import PROJECT, ArgumentRefusal

_fixture_path = Path(__file__).with_name("test_pipeline_measurements.py")
_fixture_spec = importlib.util.spec_from_file_location(
    "pipeline_measurement_fixture_for_tile_digits", _fixture_path
)
assert _fixture_spec is not None and _fixture_spec.loader is not None
_fixture_module = importlib.util.module_from_spec(_fixture_spec)
_fixture_spec.loader.exec_module(_fixture_module)
STUDY_UID = _fixture_module.STUDY_UID
STACKED_UID = _fixture_module.STACKED_UID
UNSTACKED_UID = _fixture_module.UNSTACKED_UID
_write_corpus = _fixture_module._write_corpus

#: The synthetic series in memory: 24 x 24 planes at half a millimetre, a 2 mm tile is 4 px, a
#: 6 x 6 grid; three slices, all walked. The pattern is the first lens's proof gate's: the
#: border is air (cleared), the ring inside it straddles (kept), the middle holds two bright
#: tiles, a mixed tile away from the air and a dark interior (all kept).
TILE_MM = 2.0
TILE_PX = 4
TILES = 6
SLICES = 3
AXIAL = np.array([1.0, 0.0, 0.0, 0.0, 1.0, 0.0])
AIR, BRIGHT, SPLIT = 0.0, 100.0, 10.0
BAR = 8
PATTERN = ("BBBBBB", "BUUUUB", "BULMUB", "BULDUB", "BUUUUB", "BBBBBB")

BELOW, AT, ABOVE = (CODE_VALUES[name] for name in ("below", "at", "above"))
UNREAD = CODE_VALUES["place_unread"]

#: Per slice: 20 border tiles cleared (silent), 1 dark interior below, 13 at (the ring and the
#: mixed tile, median 50), 2 bright tiles above.
PER_SLICE = {
    "below": 1,
    "at": 13,
    "above": 2,
    "place_unread": 20,
    "no_edges": 0,
    "population_too_small": 0,
    "invalid_measurement": 0,
}


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
        directory=Path("/nonexistent/the-funnel/tile-digits-wiring"),
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
    with_digits: bool = True,
    with_stack: bool = True,
    plane: np.ndarray | None = None,
    bar: int = BAR,
    stack_tile_mm: float = TILE_MM,
) -> dict:
    """One series record shaped as the writer saves it, with its arrays on disk."""
    series = _synthetic_series()
    stack = read_squint_stack(series, TILE_MM)
    lens = read_first_lens(stack, SPLIT)
    digits = read_tile_digits(stack, lens, bar)
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
        # The stack the digits are placed by; at another tile than the digits' it is another
        # grid.
        stack_record, stack_arrays = squint_stack_record(
            read_squint_stack(series, stack_tile_mm)
        )
        saved.update(stack_arrays)
        entry["squint_stack"] = stack_record
    lens_record, lens_arrays = first_lens_record(lens)
    saved.update(lens_arrays)
    entry["first_lens"] = lens_record
    if with_digits:
        digits_record, digits_arrays = tile_digits_record(digits)
        saved.update(digits_arrays)
        entry["tile_digits"] = digits_record
    if plane is not None:
        saved["acquired_plane"] = plane
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **saved)
    entry["arrays"] = _descriptor_table(saved)
    return json.loads(json.dumps(entry, allow_nan=False))


def _loaded(tmp_path: Path, record: dict) -> dict[str, np.ndarray]:
    with np.load(tmp_path / record["artifact"], allow_pickle=False) as saved:
        return {name: saved[name] for name in saved.files}


# --- the route ---------------------------------------------------------------------------------


def test_run_study_reads_the_digits_once_per_series_right_after_the_first_lens(
    tmp_path: Path,
) -> None:
    _write_corpus(tmp_path)
    with recording() as run_ledger:
        result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    events = run_ledger.events()
    names = [event.name for event in events]
    assert names.count("squint_stack.consumed_by.tile_digits") == 2
    assert names.count("first_lens.consumed_by.tile_digits") == 2
    assert names.count("tile_digits.produced") == 2
    first = names.index("tile_digits.produced")
    last = max(i for i, name in enumerate(names) if name == "tile_digits.produced")
    # After every first lens, and before anything of step 3 reads a record.
    assert (
        max(i for i, name in enumerate(names) if name == "first_lens.produced") < first
    )
    assert last < names.index("lenses.consumed_by.vectors")
    assert last < names.index("ownership.produced")
    # The digits are the lens's one reader in this phase, and nothing reads the digits yet:
    # their readers are the conjunction (3c) and, later, the dome and the bundles.
    assert not [name for name in names if name.startswith("tile_digits.consumed_by")]
    produced = [dict(e.counts) for e in events if e.name == "tile_digits.produced"]
    assert all(set(counts) == {"counted", "read"} for counts in produced)
    stacked, unstacked = result.series
    assert isinstance(stacked.tile_digits, TileDigits)
    assert stacked.tile_digits.code in ("present", "no_edges")
    assert stacked.tile_digits.codes.shape == (3, 4, 4)
    assert stacked.tile_digits.digits.shape == (3, 4, 4)
    assert sum(stacked.tile_digits.counts) == 3 * 4 * 4
    assert unstacked.tile_digits is not None
    assert unstacked.tile_digits.code == "predecessor_absent"
    assert unstacked.tile_digits.codes.shape == (0, 0, 0)


def test_the_route_hands_the_digits_the_regimes_own_bar(tmp_path: Path) -> None:
    _write_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    stacked, unstacked = result.series
    assert stacked.regime is not None and stacked.tile_digits is not None
    assert (
        stacked.tile_digits.minimum_population
        == stacked.regime.tercile_minimum_population
    )
    # No regime: the declared default is the bar, and the absent stack is named first.
    assert unstacked.regime is None and unstacked.tile_digits is not None
    assert unstacked.tile_digits.minimum_population == DEFAULT_MINIMUM_POPULATION
    assert DEFAULT_MINIMUM_POPULATION == 8


def test_without_a_request_the_route_reads_the_digits_at_the_declared_default_tile(
    tmp_path: Path,
) -> None:
    _write_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID)
    digits = result.series[0].tile_digits
    assert digits is not None
    assert digits.codes.shape == (3, 1, 1)
    assert DEFAULT_TILE_MM == 8.0


def test_a_run_built_without_the_operation_carries_no_digits() -> None:
    run = pipeline.SeriesRun("u", ("Coronal", "1", "1"), ("stackable",), None, "read")
    assert run.tile_digits is None


# --- the writer --------------------------------------------------------------------------------


def test_the_series_record_carries_the_digits_once_with_their_edges_bar_and_counts(
    tmp_path: Path,
) -> None:
    _write_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    stacked, unstacked = result.series
    record, arrays = series_record(STUDY_UID, stacked, "reference")
    saved = record["tile_digits"]
    digits = stacked.tile_digits
    assert digits is not None
    assert saved["code"] == digits.code
    assert saved["why"] == digits.why
    assert saved["code_names"] == list(TILE_DIGIT_CODES)
    assert saved["digit_code_names"] == list(DIGIT_CODES)
    assert saved["digit_silence"] == SILENT
    assert saved["low_edge"] == (
        float(digits.low_edge) if np.isfinite(digits.low_edge) else None
    )
    assert saved["high_edge"] == (
        float(digits.high_edge) if np.isfinite(digits.high_edge) else None
    )
    assert saved["population_count"] == digits.population_count
    assert saved["minimum_population"] == digits.minimum_population
    assert saved["counts"] == dict(zip(DIGIT_CODES, digits.counts, strict=True))
    assert saved["slices"] == 3 and saved["tiles_rc"] == [4, 4]
    assert saved["arrays"] == {
        name: f"tile_digits_{name}" for name in TILE_DIGIT_ARRAYS
    }
    np.testing.assert_array_equal(arrays["tile_digits_codes"], digits.codes)
    np.testing.assert_array_equal(arrays["tile_digits_digits"], digits.digits)
    descriptors = array_table(arrays)
    assert descriptors["tile_digits_codes"]["shape"] == (3, 4, 4)
    assert descriptors["tile_digits_codes"]["dtype"] == "|u1"
    assert descriptors["tile_digits_digits"]["dtype"] == "|i1"
    # Plain data: it round-trips through the receipt's JSON, which refuses NaN.
    assert json.loads(json.dumps(saved, allow_nan=False)) == saved
    # Saved ONCE: one key, two arrays, and the lens's and the stack's keys beside them.
    assert [name for name in arrays if name.startswith("tile_digits_")] == [
        "tile_digits_codes",
        "tile_digits_digits",
    ]
    assert "first_lens_codes" in arrays and "squint_stack_median" in arrays
    # The absent digits are saved as their silence, with empty arrays and edges of None.
    quiet, quiet_arrays = series_record(STUDY_UID, unstacked, "reference")
    assert quiet["tile_digits"]["code"] == "predecessor_absent"
    assert quiet["tile_digits"]["slices"] == 0
    assert quiet["tile_digits"]["tiles_rc"] == [0, 0]
    assert quiet["tile_digits"]["low_edge"] is None
    assert quiet["tile_digits"]["population_count"] == 0
    assert quiet_arrays["tile_digits_codes"].shape == (0, 0, 0)
    assert quiet_arrays["tile_digits_digits"].shape == (0, 0, 0)


def test_an_edge_the_oracle_could_not_read_is_saved_as_none_never_zero() -> None:
    stack = read_squint_stack(_synthetic_series(), TILE_MM)
    digits = read_tile_digits(stack, read_first_lens(stack, SPLIT), 10_000)
    record, arrays = tile_digits_record(digits)
    assert record["code"] == "no_edges"
    assert record["low_edge"] is None and record["high_edge"] is None
    assert record["counts"]["below"] == 0 and record["counts"]["no_edges"] > 0
    assert json.loads(json.dumps(record, allow_nan=False)) == record
    assert set(arrays) == {f"tile_digits_{name}" for name in TILE_DIGIT_ARRAYS}


# --- the adapter -------------------------------------------------------------------------------


def test_the_standing_names_a_named_slice_and_every_silence_apart() -> None:
    assert walk_standing("present", 0, 3) == "named"
    assert walk_standing("present", 2, 3) == "named"
    assert walk_standing("no_edges", 1, 3) == "named"
    assert walk_standing("population_too_small", 1, 3) == "named"
    assert walk_standing(None, 0, 3) == "digits_not_saved"
    assert walk_standing("predecessor_absent", 0, 0) == "digits_absent"
    assert walk_standing("present", 3, 3) == "slice_outside_digits"
    assert walk_standing("present", -1, 3) == "slice_outside_digits"
    assert walk_standing("present", 0, 0) == "slice_outside_digits"
    assert walk_standing("lesion", 0, 3) == "digits_code_unknown"


def test_the_standing_is_total_and_never_named_without_a_held_slice() -> None:
    # MUST NOT: draw a slice from digits whose predecessor was absent, nor from an index that
    # is not a whole number inside them; and every answer is one of the declared standings.
    for code in (*TILE_DIGIT_CODES, None, "", 1):
        for index in (0, 1, 2, 3, -1, True, 1.0, None, "1"):
            standing = walk_standing(code, index, 3)
            assert standing in DIGIT_STANDINGS, (code, index)
            if standing == "named":
                assert code in TILE_DIGIT_CODES and code != "predecessor_absent"
                assert type(index) is int and 0 <= index < 3


def test_the_adapter_selects_the_walked_slices_and_alters_nothing() -> None:
    series = _synthetic_series()
    stack = read_squint_stack(series, TILE_MM)
    digits = read_tile_digits(stack, read_first_lens(stack, SPLIT), BAR)
    frame = digit_panels(
        digits.code,
        digits.why,
        digits.low_edge,
        digits.high_edge,
        digits.population_count,
        digits.minimum_population,
        digits.counts,
        digits.codes,
        digits.digits,
        stack.bounds_rc,
        series.walk_indices,
        series.walk,
    )
    assert frame.code == "present" and frame.slices == SLICES
    assert (frame.low_edge, frame.high_edge) == (digits.low_edge, digits.high_edge)
    assert frame.population_count == digits.population_count
    assert frame.minimum_population == BAR
    assert frame.counts == digits.counts
    assert [step.index for step in frame.walked] == list(series.walk_indices)
    assert series.walk is not None
    for step, index in zip(frame.walked, series.walk_indices, strict=True):
        assert step.standing == "named"
        assert step.plane is not None and step.plane.dtype == np.uint16
        np.testing.assert_array_equal(step.plane, series.walk[index])
        assert step.codes is not None and step.codes.dtype == np.uint8
        np.testing.assert_array_equal(step.codes, digits.codes[index])
        assert step.digits is not None and step.digits.dtype == np.int8
        np.testing.assert_array_equal(step.digits, digits.digits[index])
    assert frame.codes is not None and frame.codes.dtype == np.uint8
    assert frame.digits is not None and frame.digits.dtype == np.int8
    assert frame.bounds_rc is not None and frame.bounds_rc.dtype == np.int64


def test_the_adapter_keeps_every_absence_absent() -> None:
    frame = digit_panels(
        None, None, None, None, None, None, None, None, None, None, (0, 2), None
    )
    assert frame.code is None and frame.slices == 0 and frame.codes is None
    assert frame.low_edge is None and frame.population_count is None
    assert frame.counts is None and frame.digits is None
    assert [step.standing for step in frame.walked] == ["digits_not_saved"] * 2
    assert all(
        step.plane is None and step.codes is None and step.digits is None
        for step in frame.walked
    )
    absent = digit_panels(
        "predecessor_absent",
        "why",
        None,
        None,
        0,
        BAR,
        (0,) * len(DIGIT_CODES),
        np.empty((0, 0, 0), dtype=np.uint8),
        np.empty((0, 0, 0), dtype=np.int8),
        np.empty((0, 0, 4), dtype=np.int64),
        (0,),
        None,
    )
    assert [step.standing for step in absent.walked] == ["digits_absent"]


# --- the drawer's reader -----------------------------------------------------------------------


def test_the_reader_reconstitutes_a_writer_shaped_record(tmp_path: Path) -> None:
    record = _saved_record(tmp_path)
    artifact, frame = tile_digit_frames.saved_digits(tmp_path, record)
    assert artifact == tmp_path / "series.npz"
    assert frame.code == "present" and frame.slices == SLICES
    assert frame.low_edge is not None and frame.high_edge is not None
    assert frame.population_count == SLICES * 16 and frame.minimum_population == BAR
    assert frame.counts == tuple(PER_SLICE[name] * SLICES for name in DIGIT_CODES)
    assert frame.codes is not None and frame.codes.shape == (SLICES, TILES, TILES)
    assert frame.digits is not None and frame.digits.shape == (SLICES, TILES, TILES)
    assert frame.bounds_rc is not None and frame.bounds_rc.shape == (TILES, TILES, 4)
    assert [step.standing for step in frame.walked] == ["named"] * SLICES
    assert all(step.plane is not None for step in frame.walked)
    assert tile_digit_frames.digit_counts(frame.walked[0].codes) == PER_SLICE
    assert tile_digit_frames.silent_count(PER_SLICE) == 20
    silence = tile_digit_frames.silence_mask(frame.walked[0].codes)
    assert int(silence.sum()) == 20
    assert silence[0, 0] and not silence[3, 3]


def test_the_reader_says_when_no_digits_were_saved(tmp_path: Path) -> None:
    record = _saved_record(tmp_path, with_digits=False)
    _, frame = tile_digit_frames.saved_digits(tmp_path, record)
    assert frame.code is None and frame.codes is None and frame.bounds_rc is None
    assert [step.standing for step in frame.walked] == ["digits_not_saved"] * SLICES
    silent = _saved_record(tmp_path, bar=10_000)
    _, frame = tile_digit_frames.saved_digits(tmp_path, silent)
    assert frame.code == "no_edges" and frame.low_edge is None
    assert [step.standing for step in frame.walked] == ["named"] * SLICES
    assert tile_digit_frames.silence_mask(frame.walked[0].codes).all()


def test_the_reader_refuses_a_saved_record_that_disagrees_with_the_writer(
    tmp_path: Path,
) -> None:
    # MUST NOT: draw a tampered array, a code the stage does not say, a slice count that is
    # not the codes', a vocabulary that is not the stage's, an edge that is not a number, a
    # bar that is not a count, counts that are not the stage's, digits that are not the
    # codes' own values, digits saved without their stack, or a stack whose grid is not the
    # digits'; each is named and raised.
    tampered = _saved_record(tmp_path)
    tampered["arrays"]["tile_digits_codes"]["digest"] = "changed"
    with pytest.raises(ValueError, match="saved_array_digest_mismatch"):
        tile_digit_frames.saved_digits(tmp_path, tampered)
    named = _saved_record(tmp_path)
    named["tile_digits"]["code"] = "lesion"
    with pytest.raises(ValueError, match="saved_tile_digits_code_unknown"):
        tile_digit_frames.saved_digits(tmp_path, named)
    counted = _saved_record(tmp_path)
    counted["tile_digits"]["slices"] = 2
    with pytest.raises(ValueError, match="saved_tile_digits_slices_mismatch"):
        tile_digit_frames.saved_digits(tmp_path, counted)
    worded = _saved_record(tmp_path)
    worded["tile_digits"]["digit_code_names"] = ["below", "at", "above"]
    with pytest.raises(ValueError, match="saved_tile_digits_vocabulary_mismatch"):
        tile_digit_frames.saved_digits(tmp_path, worded)
    silenced = _saved_record(tmp_path)
    silenced["tile_digits"]["digit_silence"] = 0
    with pytest.raises(ValueError, match="saved_tile_digits_silence_mismatch"):
        tile_digit_frames.saved_digits(tmp_path, silenced)
    edged = _saved_record(tmp_path)
    edged["tile_digits"]["low_edge"] = "fifty"
    with pytest.raises(ValueError, match="saved_tile_digits_not_a_number"):
        tile_digit_frames.saved_digits(tmp_path, edged)
    barred = _saved_record(tmp_path)
    barred["tile_digits"]["minimum_population"] = -1
    with pytest.raises(ValueError, match="saved_tile_digits_not_a_count"):
        tile_digit_frames.saved_digits(tmp_path, barred)
    miscounted = _saved_record(tmp_path)
    miscounted["tile_digits"]["counts"] = {"below": 1}
    with pytest.raises(ValueError, match="saved_tile_digits_counts_invalid"):
        tile_digit_frames.saved_digits(tmp_path, miscounted)
    shaped = _saved_record(tmp_path)
    shaped["tile_digits"] = "yes"
    with pytest.raises(ValueError, match="saved_tile_digits_not_a_record"):
        tile_digit_frames.saved_digits(tmp_path, shaped)
    disagreeing = _saved_record(tmp_path)
    arrays = _loaded(tmp_path, disagreeing)
    arrays["tile_digits_digits"] = np.where(
        arrays["tile_digits_digits"] == -1, 1, arrays["tile_digits_digits"]
    ).astype(np.int8)
    np.savez_compressed(tmp_path / "series.npz", allow_pickle=False, **arrays)
    disagreeing["arrays"] = _descriptor_table(arrays)
    with pytest.raises(ValueError, match="saved_tile_digits_disagree_with_codes"):
        tile_digit_frames.saved_digits(tmp_path, disagreeing)
    alone = _saved_record(tmp_path, with_stack=False)
    with pytest.raises(ValueError, match="saved_tile_digits_without_a_stack"):
        tile_digit_frames.saved_digits(tmp_path, alone)
    other_grid = _saved_record(tmp_path, stack_tile_mm=4.0)
    with pytest.raises(ValueError, match="saved_tile_digits_grid_mismatch"):
        tile_digit_frames.saved_digits(tmp_path, other_grid)


def test_an_out_directory_outside_data_is_an_argument_refusal(tmp_path: Path) -> None:
    record = _saved_record(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    with pytest.raises(ArgumentRefusal, match="private data directory"):
        tile_digit_frames.draw(tmp_path, "study", tmp_path / "out")


def test_the_drawer_writes_one_sheet_per_view_with_its_manifest(tmp_path: Path) -> None:
    """The impure edge, end to end: one image per series under data/, bound to the receipt."""
    record = _saved_record(tmp_path)
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = tile_digit_frames.draw(tmp_path, "study", out)
        assert manifest["images"] == ["01-coronal-fs1-fat1.png"]
        assert manifest["image"] == "01-coronal-fs1-fat1.png"
        assert (out / "01-coronal-fs1-fat1.png").exists()
        assert (out / "manifest.json").exists()
        assert manifest["standings"] == list(DIGIT_STANDINGS)
        assert set(manifest["legend"]["digits"]) == {"below", "at", "above"}
        assert manifest["legend"]["silence"] == tile_digit_frames.SILENCE_COLOUR
        assert manifest["legend"]["silence_words"] == [
            "place_unread",
            "no_edges",
            "population_too_small",
            "invalid_measurement",
        ]
        (series,) = manifest["series"]
        assert series["image"] == "01-coronal-fs1-fat1.png"
        assert series["tile_digits"]["code"] == "present"
        assert series["tile_digits"]["population_count"] == SLICES * 16
        assert series["tile_digits"]["tiles_rc"] == [TILES, TILES]
        assert [step["drawn"] for step in series["walked"]] == ["named"] * SLICES
        assert all(step["counts"] == PER_SLICE for step in series["walked"])
    finally:
        shutil.rmtree(out, ignore_errors=True)


# --- the view sheet ----------------------------------------------------------------------------


def test_the_sheet_draws_the_digits_at_their_own_slice_next_to_the_first_lens(
    tmp_path: Path,
) -> None:
    plane = _synthetic_series().volume
    assert plane is not None
    record = _saved_record(tmp_path, plane=plane[1])
    _, panels = view_frames.view_panels(tmp_path, record, _loaded(tmp_path, record))
    by_reading = {(p.stage, p.reading): p for p in panels}
    panel = by_reading[("lenses", "tile digits")]
    assert (panel.status, panel.code) == ("saved", "present")
    assert panel.paint is not None
    assert panel.arrays == ("tile_digits_codes", "tile_digits_digits")
    readings = [p.reading for p in panels]
    assert readings.index("first lens") + 1 == readings.index("tile digits")
    assert readings.index("tile digits") < readings.index("structural reading")


def test_the_sheet_names_digits_that_were_not_saved_or_cannot_be_shown(
    tmp_path: Path,
) -> None:
    plane = _synthetic_series().volume
    assert plane is not None
    unsaved = _saved_record(tmp_path, with_digits=False, plane=plane[1])
    _, panels = view_frames.view_panels(tmp_path, unsaved, _loaded(tmp_path, unsaved))
    panel = {(p.stage, p.reading): p for p in panels}[("lenses", "tile digits")]
    assert (panel.status, panel.paint) == ("not_saved", None)
    outside = _saved_record(tmp_path, plane=plane[1])
    outside["slice_index"] = 9
    _, panels = view_frames.view_panels(tmp_path, outside, _loaded(tmp_path, outside))
    panel = {(p.stage, p.reading): p for p in panels}[("lenses", "tile digits")]
    assert (panel.status, panel.code, panel.paint) == ("silent", "present", None)
    assert panel.why.startswith("slice_outside_digits")
    # A series whose oracle gave no edges is still drawn: every tile as silence, named so.
    silent = _saved_record(tmp_path, plane=plane[1], bar=10_000)
    _, panels = view_frames.view_panels(tmp_path, silent, _loaded(tmp_path, silent))
    panel = {(p.stage, p.reading): p for p in panels}[("lenses", "tile digits")]
    assert (panel.status, panel.code) == ("saved", "no_edges")
    assert panel.paint is not None


def test_the_sheet_refuses_digits_that_cover_another_plane(tmp_path: Path) -> None:
    # MUST NOT: lay a 24 x 24 grid's tiles over a 4 x 4 plane. The panel is asked directly:
    # on the whole sheet the squint stack's own panel refuses the same plane first.
    record = _saved_record(tmp_path)
    with pytest.raises(ValueError, match="saved_tile_digits_cover_another_plane"):
        view_frames.tile_digits_panel(
            np.arange(16, dtype=np.uint16).reshape(4, 4), tmp_path, record
        )


def test_the_sheet_is_drawn_with_the_digits_panel(tmp_path: Path) -> None:
    plane = _synthetic_series().volume
    assert plane is not None
    record = _saved_record(tmp_path, plane=plane[1])
    (tmp_path / "receipt.json").write_text(json.dumps({"records": [record]}))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = view_frames.draw(tmp_path, "study", out)
        (view,) = manifest["views"]
        panel = next(p for p in view["panels"] if p["reading"] == "tile digits")
        assert panel["drawn"] == "drawn"
        assert "tile_digit_frames" in manifest["reused_drawers_sha256"]
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_picture_module_is_the_adapter_the_sheet_and_drawer_read() -> None:
    assert tile_digit_frames.pictures is pictures
    assert view_frames.tile_pictures is pictures
    assert view_frames.tile_digit_frames is tile_digit_frames
    assert ("lenses", "tile_digits", "tile_digit_frames") in all_frames.DRAWINGS
    lens_at = all_frames.DRAWINGS.index(("collapse", "first_lens", "first_lens_frames"))
    assert all_frames.DRAWINGS[lens_at + 1] == (
        "lenses",
        "tile_digits",
        "tile_digit_frames",
    )
    module = importlib.import_module("workbench.render.tile_digit_frames")
    assert module.draw is tile_digit_frames.draw
