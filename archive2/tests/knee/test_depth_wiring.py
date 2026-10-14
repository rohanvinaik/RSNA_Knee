"""The depth collapse on the route, in the request, in the receipt, in the picture adapter, on
the depth drawer and on the view sheet (the-funnel tasks 4.3 and 4.5), both signs. The route
reads the collapse once per series right after the conjunction and before the conversation,
handing the recipient's conjunction over and None to every other series, under the request's
bar or the declared default; the request carries the bar as a number and refuses one that is
not a count; the writer saves the four readings, the choices and the chosen slices once per
series with NaN for silence in the arrays and never in the record; the adapter selects the
readings, the saved planes and the medians at the chosen slices and alters nothing; the drawer
refuses a saved record that disagrees with the writer and draws one sheet per series; the sheet
draws the collapse right after the conjunction and says whether its own slice is a chosen one."""

from __future__ import annotations

import importlib
import importlib.util
import json
import math
import shutil
import uuid
from dataclasses import asdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest

from knee import pipeline
from knee.collapse.depth import (
    CHOICE_CODES,
    DEFAULT_MINIMUM_VALID,
    DEPTH_CODES,
    LENSES,
    DepthCollapse,
    read_depth,
)
from knee.collapse.first_lens import read_first_lens
from knee.collapse.squint_stack import read_squint_stack
from knee.objects.analysis import AnalysisRequest
from knee.pictures import depth as pictures
from knee.pictures.depth import (
    PLANE_SOURCES,
    SHEET_STANDINGS,
    depth_panels,
    plane_source,
    sheet_standing,
)
from knee.telemetry import recording
from workbench.measure.object_analysis import (
    DEPTH_ARRAYS,
    analysis_request,
    array_table,
    build_parser,
    depth_record,
    series_record,
    squint_stack_record,
)
from workbench.render import all_frames, depth_frames, view_frames
from workbench.render._out import PROJECT, ArgumentRefusal


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: The line-up's wiring fixture: a study on disk with one paired plane (a fat-dark recipient and
#: a fat-bright partner) and one solitary plane, three slices each; and the measurement
#: fixture's corpus, one stacked and one unstacked series of a surplus plane.
_lineup_fixture = _load(
    "lineup_wiring_fixture_for_depth", Path(__file__).with_name("test_lineup_wiring.py")
)
STUDY_UID = _lineup_fixture.STUDY_UID
DARK_UID = _lineup_fixture.DARK_UID
BRIGHT_UID = _lineup_fixture.BRIGHT_UID
SOLO_UID = _lineup_fixture.SOLO_UID
_write_paired_corpus = _lineup_fixture._write_paired_corpus
_write_corpus = _lineup_fixture._write_corpus

#: The depth proof gate's synthetic stack in memory: six slices of a 6 x 6 grid whose four
#: readings peak at designed slices (kept at 1, dark at 2, split quality tied at 3 and 5, the
#: above_below share of a hand-built conjunction at 2), so the chosen slices are 1, 2 and 3.
_depth_fixture = _load(
    "depth_fixture_for_wiring", Path(__file__).parent / "collapse" / "test_depth.py"
)
_stack = _depth_fixture._stack
_lens = _depth_fixture._lens
_conjunction = _depth_fixture._conjunction
_series = _depth_fixture._series
_plane = _depth_fixture._plane
PATTERNS = _depth_fixture.PATTERNS
SLICES = _depth_fixture.SLICES
TILE_MM = _depth_fixture.TILE_MM
SPLIT = _depth_fixture.SPLIT
DEPTH_STUDY = _depth_fixture.STUDY
DEPTH_UID = _depth_fixture.UID

#: The walk a saved record carries in these tests: three of the six slices, so a chosen slice
#: may lie on the walk (2), at the selected slice (3) or nowhere a plane was saved (1).
WALK = (0, 2, 5)
SELECTED = 3
BAR = 2


def _request(minimum_valid: int | None = 1) -> AnalysisRequest:
    return AnalysisRequest(
        tile_mm=2.0,
        offsets_mm=(-0.5, 0.0, 0.5),
        direction_lps=(1.0, 0.0, 0.0),
        backend="reference",
        minimum_valid=minimum_valid,
    )


def _conversing_request() -> AnalysisRequest:
    return AnalysisRequest(
        tile_mm=2.0,
        offsets_mm=(-1.0, 0.0, 1.0),
        direction_lps=(1.0, 0.0, 0.0),
        backend="reference",
        prominence_mm=1.0,
        conversation=True,
        minimum_valid=1,
    )


def _descriptor_table(arrays: dict[str, np.ndarray]) -> dict:
    return json.loads(json.dumps(array_table(arrays), allow_nan=False))


def _loaded(tmp_path: Path, record: dict) -> dict[str, np.ndarray]:
    with np.load(tmp_path / record["artifact"], allow_pickle=False) as saved:
        return {name: saved[name] for name in saved.files}


def _volume() -> np.ndarray:
    return np.stack([_plane(pattern) for pattern in PATTERNS])


def _collapse(code: str = "present") -> DepthCollapse:
    if code == "present":
        stack = _stack()
        return read_depth(stack, _lens(stack), _conjunction(stack), SPLIT, BAR)
    gone = read_squint_stack(_series(None), TILE_MM)
    return read_depth(gone, read_first_lens(gone, SPLIT), None, SPLIT, BAR)


def _saved_record(
    tmp_path: Path,
    *,
    with_depth: bool = True,
    code: str = "present",
    with_stack: bool = True,
    stack_slices: int = SLICES,
    with_plane: bool = True,
    selected: int = SELECTED,
) -> dict:
    """One series record shaped as the writer saves it, with its arrays on disk and a receipt
    beside it: the stack, the collapse, a walk of three slices and the plane at the selected
    slice."""
    volume = _volume()
    saved: dict[str, np.ndarray] = {"study_walk": volume[list(WALK)]}
    entry: dict = {
        "study_uid": DEPTH_STUDY,
        "series_uid": DEPTH_UID,
        "view": ["Coronal", "1", "1"],
        "code": "measured",
        "slice_index": selected,
        "source_plane": f"slice-{selected}.dcm",
        "artifact": f"{DEPTH_UID}.npz",
        "study": {
            "slice_codes": ["decoded"] * SLICES,
            "walk_indices": list(WALK),
            "walk_array": "study_walk",
        },
    }
    if with_stack:
        # A collapse the stage did not make rides only beside a stack it could not read: on
        # the route the first lens is absent exactly when the stack is.
        if code != "present":
            stack = read_squint_stack(_series(None), TILE_MM)
        elif stack_slices == SLICES:
            stack = _stack()
        else:
            stack = read_squint_stack(_series(volume[:stack_slices]), TILE_MM)
        stack_record, stack_arrays = squint_stack_record(stack)
        saved.update(stack_arrays)
        entry["squint_stack"] = stack_record
    if with_depth:
        depth_fields, depth_arrays = depth_record(_collapse(code))
        saved.update(depth_arrays)
        entry["depth"] = depth_fields
    if with_plane:
        saved["acquired_plane"] = volume[selected]
    np.savez_compressed(tmp_path / entry["artifact"], allow_pickle=False, **saved)
    entry["arrays"] = _descriptor_table(saved)
    record = json.loads(json.dumps(entry, allow_nan=False))
    receipt = {"records": [record], "studies": [{"study_uid": DEPTH_STUDY}]}
    (tmp_path / "receipt.json").write_text(json.dumps(receipt, allow_nan=False))
    return record


# --- the route ---------------------------------------------------------------------------------


def test_run_study_reads_the_depth_once_per_series_right_after_the_conjunction(
    tmp_path: Path,
) -> None:
    _write_paired_corpus(tmp_path)
    with recording() as run_ledger:
        result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    events = run_ledger.events()
    names = [event.name for event in events]
    assert names.count("squint_stack.consumed_by.depth") == 3
    assert names.count("first_lens.consumed_by.depth") == 3
    # The conjunction is handed over on the recipient alone; the partner and the solitary
    # series hand None, and nothing is recorded on their behalf.
    assert names.count("conjunction.consumed_by.depth") == 1
    assert names.count("depth.produced") == 3
    first = names.index("squint_stack.consumed_by.depth")
    last = max(i for i, name in enumerate(names) if name == "depth.produced")
    # After the conjunction and every digit record, and before anything of step 2 or 3 reads.
    assert names.index("conjunction.produced") < first
    assert (
        max(i for i, name in enumerate(names) if name == "tile_digits.produced") < first
    )
    assert last < names.index("lenses.consumed_by.vectors")
    assert last < names.index("ownership.produced")
    assert [
        dict(e.counts) for e in events if e.name == "conjunction.consumed_by.depth"
    ] == [{"conjunction": 1}]
    assert all(
        set(dict(e.counts)) == {"chosen", "standing"}
        for e in events
        if e.name == "depth.produced"
    )
    by_uid = {run.series_uid: run for run in result.series}
    for uid in (DARK_UID, BRIGHT_UID, SOLO_UID):
        collapse = by_uid[uid].depth
        assert isinstance(collapse, DepthCollapse)
        assert collapse.code == "present" and collapse.minimum_valid == 1
        assert collapse.series_uid == uid
        for lens in LENSES:
            assert getattr(collapse, lens).shape == (3,)
        # Every tile is finite and bright on this corpus, so the kept share reads on every
        # slice and the lens stands somewhere under a bar of one.
        assert np.isfinite(collapse.kept_share).all()
        assert collapse.chosen_index[0] >= 0
        np.testing.assert_array_equal(
            collapse.chosen_slices,
            sorted({index for index in collapse.chosen_index if index >= 0}),
        )
    # The recipient read its conjunction: the above_below share is a number somewhere; the
    # partner and the solitary series had none handed over, and theirs is silent throughout.
    assert np.isfinite(by_uid[DARK_UID].depth.above_below_share).any()
    for uid in (BRIGHT_UID, SOLO_UID):
        assert np.isnan(by_uid[uid].depth.above_below_share).all()
        assert by_uid[uid].depth.choice_codes[3] == "all_silent"
        assert by_uid[uid].depth.chosen_index[3] == -1


def test_the_depth_precedes_the_conversation_and_the_stages_that_read_the_parse(
    tmp_path: Path,
) -> None:
    _write_paired_corpus(tmp_path)
    with recording() as run_ledger:
        pipeline.open_and_run(tmp_path, STUDY_UID, _conversing_request())
    names = [event.name for event in run_ledger.events()]
    last = max(i for i, name in enumerate(names) if name == "depth.produced")
    assert last < names.index("conversation.produced")
    assert last < names.index("ownership.produced")
    assert last < names.index("relations.produced")


def test_without_a_request_the_route_stands_lenses_under_the_declared_default_bar(
    tmp_path: Path,
) -> None:
    _write_paired_corpus(tmp_path)
    with recording() as run_ledger:
        result = pipeline.open_and_run(tmp_path, STUDY_UID)
    assert DEFAULT_MINIMUM_VALID == 8
    for run in result.series:
        assert run.depth is not None
        assert run.depth.minimum_valid == DEFAULT_MINIMUM_VALID
        # Three slices cannot carry eight finite readings: every lens abstains by name, and
        # no slice is chosen -- never a guess.
        assert set(run.depth.choice_codes) <= {"too_few_valid", "all_silent"}
        assert run.depth.chosen_index == (-1, -1, -1, -1)
        assert run.depth.chosen_slices.shape == (0,)
    produced = [
        dict(e.counts) for e in run_ledger.events() if e.name == "depth.produced"
    ]
    assert produced == [{"chosen": 0, "standing": 0}] * 3


def test_the_route_hands_the_requests_bar_and_the_regimes_own_split(
    tmp_path: Path,
) -> None:
    _write_paired_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID, _request(minimum_valid=3))
    for run in result.series:
        assert run.depth is not None and run.regime is not None
        assert run.depth.minimum_valid == 3
        # The dark share reads against the regime's own valley: a number where the regime
        # read one, silence where it did not.
        if np.isfinite(run.regime.background_split):
            assert np.isfinite(run.depth.dark_share).all()
        else:
            assert np.isnan(run.depth.dark_share).all()


def test_the_route_hands_no_conjunction_to_the_depth_when_no_plane_is_paired(
    tmp_path: Path,
) -> None:
    # MUST NOT: record a read of a conjunction that was never made; the fixture's corpus has
    # one plane with two fat-bright series (a surplus) and one of them unstacked.
    _write_corpus(tmp_path)
    with recording() as run_ledger:
        result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    names = [event.name for event in run_ledger.events()]
    assert "conjunction.consumed_by.depth" not in names
    assert names.count("depth.produced") == 2
    stacked, unstacked = result.series
    assert stacked.depth is not None and stacked.depth.code == "present"
    assert np.isnan(stacked.depth.above_below_share).all()
    assert unstacked.depth is not None
    assert unstacked.depth.code == "predecessor_absent"
    assert unstacked.depth.kept_share.shape == (0,)
    assert unstacked.depth.chosen_slices.shape == (0,)


def test_a_run_built_without_the_operation_carries_no_depth() -> None:
    run = pipeline.SeriesRun("u", ("Coronal", "1", "1"), ("stackable",), None, "read")
    assert run.depth is None


# --- the request's bar -------------------------------------------------------------------------


def test_the_request_resolves_the_bar_once_and_carries_the_number() -> None:
    request = _request(minimum_valid=None)
    assert request.minimum_valid == DEFAULT_MINIMUM_VALID == 8
    assert asdict(request)["minimum_valid"] == 8
    assert _request(minimum_valid=3).minimum_valid == 3
    assert _request(minimum_valid=0).minimum_valid == 0


def test_a_bar_that_is_not_a_count_is_refused_by_name() -> None:
    for bar in (-1, True, 2.0, "2"):
        with pytest.raises(ValueError, match="invalid_minimum_valid"):
            _request(minimum_valid=bar)  # type: ignore[arg-type]


def test_the_command_line_names_the_bar_beside_the_half_tile() -> None:
    required = [
        "--tile-mm",
        "2",
        "--span-mm",
        "1",
        "--samples",
        "3",
        "--axis",
        "superior",
        "--backend",
        "reference",
        "--out",
        "nowhere",
        "--no-conversation",
    ]
    parser = build_parser()
    assert analysis_request(parser.parse_args(required)).minimum_valid == 8
    assert (
        analysis_request(
            parser.parse_args([*required, "--minimum-valid", "3"])
        ).minimum_valid
        == 3
    )
    with pytest.raises(SystemExit):
        parser.parse_args([*required, "--minimum-valid", "three"])


# --- the writer --------------------------------------------------------------------------------


def test_every_series_record_carries_the_depth_with_its_readings_and_choices(
    tmp_path: Path,
) -> None:
    _write_paired_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    for run in result.series:
        record, arrays = series_record(STUDY_UID, run, "reference")
        saved = record["depth"]
        collapse = run.depth
        assert collapse is not None
        assert saved["code"] == collapse.code and saved["why"] == collapse.why
        assert saved["code_names"] == list(DEPTH_CODES)
        assert saved["choice_code_names"] == list(CHOICE_CODES)
        assert saved["lenses"] == list(LENSES)
        assert saved["minimum_valid"] == 1
        assert saved["chosen_index"] == list(collapse.chosen_index)
        assert saved["choice_codes"] == list(collapse.choice_codes)
        assert saved["slices"] == 3
        assert saved["chosen"] == int(collapse.chosen_slices.shape[0])
        assert saved["arrays"] == {name: f"depth_{name}" for name in DEPTH_ARRAYS}
        for lens in LENSES:
            np.testing.assert_array_equal(
                arrays[f"depth_{lens}"], getattr(collapse, lens)
            )
        np.testing.assert_array_equal(
            arrays["depth_chosen_slices"], collapse.chosen_slices
        )
        descriptors = array_table(arrays)
        assert descriptors["depth_kept_share"]["shape"] == (3,)
        assert descriptors["depth_kept_share"]["dtype"] == "<f8"
        assert descriptors["depth_chosen_slices"]["dtype"] == "<i8"
        # Plain data: it round-trips through the receipt's JSON, which refuses NaN; a silent
        # reading is NaN in its array and never a number in the record.
        assert json.loads(json.dumps(saved, allow_nan=False)) == saved
        # Saved ONCE: the five arrays, beside the stack's own keys.
        assert sorted(name for name in arrays if name.startswith("depth_")) == sorted(
            f"depth_{name}" for name in DEPTH_ARRAYS
        )
        assert "squint_stack_median" in arrays
    by_uid = {run.series_uid: run for run in result.series}
    _, arrays = series_record(STUDY_UID, by_uid[SOLO_UID], "reference")
    assert np.isnan(arrays["depth_above_below_share"]).all()


def test_an_absent_depth_is_saved_as_its_silence_with_empty_arrays() -> None:
    record, arrays = depth_record(_collapse("predecessor_absent"))
    assert record["code"] == "predecessor_absent"
    assert record["slices"] == 0 and record["chosen"] == 0
    assert record["chosen_index"] == [-1, -1, -1, -1]
    assert record["choice_codes"] == ["all_silent"] * 4
    assert record["minimum_valid"] == BAR
    assert json.loads(json.dumps(record, allow_nan=False)) == record
    assert set(arrays) == {f"depth_{name}" for name in DEPTH_ARRAYS}
    assert all(array.shape == (0,) for array in arrays.values())
    assert arrays["depth_chosen_slices"].dtype == np.int64


def test_the_record_of_the_proof_gates_stack_names_the_designed_choices() -> None:
    record, arrays = depth_record(_collapse())
    assert record["chosen_index"] == [1, 2, 3, 2]
    assert record["choice_codes"] == ["chosen", "chosen", "tie_middle", "chosen"]
    np.testing.assert_array_equal(arrays["depth_chosen_slices"], [1, 2, 3])
    assert record["chosen"] == 3 and record["slices"] == SLICES
    # The silences are NaN in the arrays: the flat slices' split quality, slice 4's above_below
    # share.
    assert math.isnan(arrays["depth_split_quality"][0])
    assert math.isnan(arrays["depth_above_below_share"][4])


# --- the adapter -------------------------------------------------------------------------------


def test_the_sheet_standing_names_chosen_unchosen_and_every_silence_apart() -> None:
    assert sheet_standing("present", 2, 6, (1, 2, 3)) == "chosen"
    assert sheet_standing("present", 4, 6, (1, 2, 3)) == "unchosen"
    assert sheet_standing("present", 0, 6, ()) == "unchosen"
    assert sheet_standing(None, 2, 6, (1, 2, 3)) == "depth_not_saved"
    assert sheet_standing("predecessor_absent", 0, 0, ()) == "depth_absent"
    assert sheet_standing("present", 6, 6, (1, 2, 3)) == "slice_outside_depth"
    assert sheet_standing("present", -1, 6, (1, 2, 3)) == "slice_outside_depth"
    assert sheet_standing("present", 0, 0, ()) == "slice_outside_depth"
    assert sheet_standing("lesion", 2, 6, (1, 2, 3)) == "depth_code_unknown"


def test_the_sheet_standing_is_total_and_never_chosen_without_a_held_slice() -> None:
    # MUST NOT: call a slice chosen from a collapse that stood no lens, from an index that is
    # not a whole number inside the readings, or from a choice that is not that index; and
    # every answer is one of the declared standings.
    for code in (*DEPTH_CODES, None, "", 1):
        for index in (0, 1, 2, 3, -1, True, 1.0, None, "1"):
            for chosen in ((), (1,), (0, 2), (True,), (1.0,)):
                standing = sheet_standing(code, index, 3, chosen)  # type: ignore[arg-type]
                assert standing in SHEET_STANDINGS, (code, index, chosen)
                if standing == "chosen":
                    assert code == "present"
                    assert type(index) is int and 0 <= index < 3
                    assert index in chosen and type(chosen[chosen.index(index)]) is int


def test_the_plane_source_names_the_walk_then_the_selected_slice_then_nothing() -> None:
    assert plane_source(2, WALK, SELECTED) == "walk"
    assert plane_source(3, WALK, SELECTED) == "selected"
    assert plane_source(1, WALK, SELECTED) == "plane_not_saved"
    assert plane_source(1, WALK, None) == "plane_not_saved"
    # The walk is named before the selected slice when both hold the index.
    assert plane_source(2, WALK, 2) == "walk"
    # MUST NOT: read a bool or a float as an index, or a walked bool as a slice.
    for index in (True, 2.0, None, "2"):
        assert plane_source(index, WALK, SELECTED) == "plane_not_saved"
    assert plane_source(1, (True,), 1.0) == "plane_not_saved"
    for index in (0, 1, 2, 3, -1, True, 1.0, None):
        for selected in (3, None, True, 1.0):
            assert plane_source(index, WALK, selected) in PLANE_SOURCES


def test_the_adapter_selects_the_readings_the_planes_and_the_medians_and_alters_nothing() -> (
    None
):
    stack = _stack()
    collapse = read_depth(stack, _lens(stack), _conjunction(stack), SPLIT, BAR)
    volume = _volume()
    frame = depth_panels(
        collapse.code,
        collapse.why,
        collapse.minimum_valid,
        collapse.kept_share,
        collapse.dark_share,
        collapse.split_quality,
        collapse.above_below_share,
        collapse.chosen_index,
        collapse.choice_codes,
        tuple(int(index) for index in collapse.chosen_slices),
        stack.median,
        stack.bounds_rc,
        WALK,
        volume[list(WALK)],
        SELECTED,
        volume[SELECTED],
    )
    assert frame.code == "present" and frame.slices == SLICES
    assert frame.minimum_valid == BAR
    assert [lens for lens, _ in frame.readings] == list(LENSES)
    for (lens, reading), name in zip(frame.readings, LENSES, strict=True):
        assert lens == name and reading.dtype == np.float64
        np.testing.assert_array_equal(reading, getattr(collapse, name))
    assert [(s.lens, s.index, s.code) for s in frame.standings] == [
        ("kept_share", 1, "chosen"),
        ("dark_share", 2, "chosen"),
        ("split_quality", 3, "tie_middle"),
        ("above_below_share", 2, "chosen"),
    ]
    assert frame.standings[0].reading == collapse.kept_share[1]
    assert frame.standings[2].reading == 1.0
    assert frame.chosen_slices == (1, 2, 3)
    assert [c.index for c in frame.chosen] == [1, 2, 3]
    assert [c.lenses for c in frame.chosen] == [
        ("kept_share",),
        ("dark_share", "above_below_share"),
        ("split_quality",),
    ]
    assert [c.source for c in frame.chosen] == ["plane_not_saved", "walk", "selected"]
    assert frame.chosen[0].plane is None
    assert frame.chosen[1].plane is not None
    np.testing.assert_array_equal(frame.chosen[1].plane, volume[2])
    assert frame.chosen[2].plane is not None
    np.testing.assert_array_equal(frame.chosen[2].plane, volume[3])
    for chosen in frame.chosen:
        assert chosen.median is not None
        np.testing.assert_array_equal(chosen.median, stack.median[chosen.index])
    assert frame.bounds_rc is not None and frame.bounds_rc.dtype == np.int64


def test_the_adapter_keeps_every_absence_absent() -> None:
    frame = depth_panels(
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        (),
        None,
        None,
        None,
    )
    assert frame.code is None and frame.slices == 0 and frame.minimum_valid is None
    assert frame.readings == () and frame.standings == () and frame.chosen == ()
    assert frame.chosen_slices == () and frame.bounds_rc is None
    absent = _collapse("predecessor_absent")
    quiet = depth_panels(
        absent.code,
        absent.why,
        absent.minimum_valid,
        absent.kept_share,
        absent.dark_share,
        absent.split_quality,
        absent.above_below_share,
        absent.chosen_index,
        absent.choice_codes,
        tuple(int(index) for index in absent.chosen_slices),
        None,
        None,
        (),
        None,
        None,
        None,
    )
    assert quiet.code == "predecessor_absent" and quiet.slices == 0
    assert [s.index for s in quiet.standings] == [-1] * 4
    assert all(math.isnan(s.reading) for s in quiet.standings)
    assert quiet.chosen == ()
    # A lens standing nowhere, and a chosen slice the stack does not hold, stay absent.
    stack = _stack()
    collapse = read_depth(stack, _lens(stack), None, SPLIT, BAR)
    partial = depth_panels(
        collapse.code,
        collapse.why,
        collapse.minimum_valid,
        collapse.kept_share,
        collapse.dark_share,
        collapse.split_quality,
        collapse.above_below_share,
        collapse.chosen_index,
        collapse.choice_codes,
        (1, 9),
        stack.median,
        stack.bounds_rc,
        (),
        None,
        None,
        None,
    )
    assert partial.standings[3].index == -1 and math.isnan(partial.standings[3].reading)
    assert partial.chosen[1].index == 9 and partial.chosen[1].median is None
    assert partial.chosen[1].plane is None and partial.chosen[1].lenses == ()
    assert partial.chosen[0].source == "plane_not_saved"


# --- the drawer's reader -----------------------------------------------------------------------


def test_the_reader_reconstitutes_a_writer_shaped_record(tmp_path: Path) -> None:
    record = _saved_record(tmp_path)
    artifact, frame = depth_frames.saved_depth(tmp_path, record)
    assert artifact == tmp_path / f"{DEPTH_UID}.npz"
    assert frame.code == "present" and frame.slices == SLICES
    assert frame.minimum_valid == BAR
    assert frame.chosen_slices == (1, 2, 3)
    assert [(s.lens, s.index, s.code) for s in frame.standings] == [
        ("kept_share", 1, "chosen"),
        ("dark_share", 2, "chosen"),
        ("split_quality", 3, "tie_middle"),
        ("above_below_share", 2, "chosen"),
    ]
    assert [c.source for c in frame.chosen] == ["plane_not_saved", "walk", "selected"]
    assert frame.chosen[1].plane is not None and frame.chosen[2].plane is not None
    assert all(c.median is not None for c in frame.chosen)
    assert frame.bounds_rc is not None and frame.bounds_rc.shape == (6, 6, 4)


def test_the_reader_says_when_no_depth_was_saved(tmp_path: Path) -> None:
    record = _saved_record(tmp_path, with_depth=False)
    _, frame = depth_frames.saved_depth(tmp_path, record)
    assert frame.code is None and frame.readings == () and frame.chosen == ()
    assert frame.bounds_rc is not None
    absent = _saved_record(tmp_path, code="predecessor_absent")
    _, frame = depth_frames.saved_depth(tmp_path, absent)
    assert frame.code == "predecessor_absent" and frame.slices == 0
    assert frame.chosen == () and [s.index for s in frame.standings] == [-1] * 4


def test_the_reader_refuses_a_saved_record_that_disagrees_with_the_writer(
    tmp_path: Path,
) -> None:
    # MUST NOT: draw a tampered array, a code the stage does not say, a vocabulary that is not
    # the stage's, a bar that is not a count, choices that are not one index and one word per
    # lens, a word outside the vocabulary, choices that disagree with the chosen slices or with
    # their own words, a reading of another length than the saved slice count, chosen slices
    # that are not ascending distinct indices inside the readings, a collapse saved without
    # its stack, or a stack of another number of slices; each is named and raised.
    record = _saved_record(tmp_path)

    def copy() -> dict:
        return json.loads(json.dumps(record))

    tampered = copy()
    tampered["arrays"]["depth_kept_share"]["digest"] = "changed"
    with pytest.raises(ValueError, match="saved_array_digest_mismatch"):
        depth_frames.saved_depth(tmp_path, tampered)
    named = copy()
    named["depth"]["code"] = "lesion"
    with pytest.raises(ValueError, match="saved_depth_code_unknown"):
        depth_frames.saved_depth(tmp_path, named)
    worded = copy()
    worded["depth"]["lenses"] = ["kept_share"]
    with pytest.raises(ValueError, match="saved_depth_vocabulary_mismatch"):
        depth_frames.saved_depth(tmp_path, worded)
    barred = copy()
    barred["depth"]["minimum_valid"] = "eight"
    with pytest.raises(ValueError, match="saved_depth_not_a_count:minimum_valid"):
        depth_frames.saved_depth(tmp_path, barred)
    short = copy()
    short["depth"]["chosen_index"] = [1, 2, 3]
    with pytest.raises(ValueError, match="saved_depth_choices_invalid"):
        depth_frames.saved_depth(tmp_path, short)
    unworded = copy()
    unworded["depth"]["choice_codes"] = ["chosen", "chosen", "middle", "chosen"]
    with pytest.raises(ValueError, match="saved_depth_choice_code_unknown"):
        depth_frames.saved_depth(tmp_path, unworded)
    disagreeing = copy()
    disagreeing["depth"]["chosen_index"] = [4, 2, 3, 2]
    with pytest.raises(ValueError, match="saved_depth_choices_mismatch"):
        depth_frames.saved_depth(tmp_path, disagreeing)
    contradicting = copy()
    contradicting["depth"]["choice_codes"] = [
        "all_silent",
        "chosen",
        "tie_middle",
        "chosen",
    ]
    with pytest.raises(ValueError, match="saved_depth_choices_mismatch"):
        depth_frames.saved_depth(tmp_path, contradicting)
    counted = copy()
    counted["depth"]["slices"] = 5
    with pytest.raises(ValueError, match="saved_depth_slices_mismatch:kept_share"):
        depth_frames.saved_depth(tmp_path, counted)
    miscounted = copy()
    miscounted["depth"]["chosen"] = 2
    with pytest.raises(ValueError, match="saved_depth_chosen_mismatch"):
        depth_frames.saved_depth(tmp_path, miscounted)
    shaped = copy()
    shaped["depth"] = "yes"
    with pytest.raises(ValueError, match="saved_depth_not_a_record"):
        depth_frames.saved_depth(tmp_path, shaped)
    unsorted = copy()
    arrays = _loaded(tmp_path, unsorted)
    arrays["depth_chosen_slices"] = np.array([3, 2, 1], dtype=np.int64)
    np.savez_compressed(tmp_path / unsorted["artifact"], allow_pickle=False, **arrays)
    unsorted["arrays"] = _descriptor_table(arrays)
    with pytest.raises(ValueError, match="saved_depth_chosen_slices_invalid"):
        depth_frames.saved_depth(tmp_path, unsorted)
    alone = _saved_record(tmp_path, with_stack=False)
    with pytest.raises(ValueError, match="saved_depth_without_a_stack"):
        depth_frames.saved_depth(tmp_path, alone)
    other_stack = _saved_record(tmp_path, stack_slices=5)
    with pytest.raises(ValueError, match="saved_depth_stack_mismatch"):
        depth_frames.saved_depth(tmp_path, other_stack)


# --- the drawer --------------------------------------------------------------------------------


def test_an_out_directory_outside_data_is_an_argument_refusal(tmp_path: Path) -> None:
    _saved_record(tmp_path)
    with pytest.raises(ArgumentRefusal, match="private data directory"):
        depth_frames.draw(tmp_path, DEPTH_STUDY, tmp_path / "out")


def test_the_drawer_writes_one_sheet_per_series_with_its_manifest(
    tmp_path: Path,
) -> None:
    """The impure edge, end to end: one image per series under data/, bound to the receipt."""
    _saved_record(tmp_path)
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = depth_frames.draw(tmp_path, DEPTH_STUDY, out)
        assert manifest["images"] == ["01-coronal-fs1-fat1.png"]
        assert manifest["image"] == "01-coronal-fs1-fat1.png"
        assert (out / "01-coronal-fs1-fat1.png").exists()
        assert (out / "manifest.json").exists()
        assert manifest["standings"] == list(SHEET_STANDINGS)
        assert manifest["sources"] == list(PLANE_SOURCES)
        assert list(manifest["legend"]["lenses"]) == list(LENSES)
        (series,) = manifest["series"]
        assert series["series_uid"] == DEPTH_UID
        assert series["curves"] == "drawn"
        assert series["depth"]["code"] == "present"
        assert series["depth"]["minimum_valid"] == BAR
        assert series["depth"]["chosen_slices"] == [1, 2, 3]
        assert [lens["index"] for lens in series["depth"]["lenses"]] == [1, 2, 3, 2]
        assert series["chosen"] == [
            {
                "index": 1,
                "lenses": ["kept_share"],
                "source": "plane_not_saved",
                "drawn": "plane_not_saved",
            },
            {
                "index": 2,
                "lenses": ["dark_share", "above_below_share"],
                "source": "walk",
                "drawn": "walk",
            },
            {
                "index": 3,
                "lenses": ["split_quality"],
                "source": "selected",
                "drawn": "selected",
            },
        ]
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_a_collapse_the_stage_did_not_make_draws_its_silence_in_words(
    tmp_path: Path,
) -> None:
    _saved_record(tmp_path, code="predecessor_absent")
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = depth_frames.draw(tmp_path, DEPTH_STUDY, out)
        (series,) = manifest["series"]
        assert series["curves"] == "depth_absent"
        assert series["chosen"] == []
        assert series["depth"]["code"] == "predecessor_absent"
        assert (out / "01-coronal-fs1-fat1.png").exists()
    finally:
        shutil.rmtree(out, ignore_errors=True)
    _saved_record(tmp_path, with_depth=False)
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = depth_frames.draw(tmp_path, DEPTH_STUDY, out)
        (series,) = manifest["series"]
        assert series["curves"] == "depth_not_saved"
        assert series["depth"] is None and series["chosen"] == []
    finally:
        shutil.rmtree(out, ignore_errors=True)


# --- the view sheet ----------------------------------------------------------------------------


def _title_of(panel) -> str:
    figure, axis = plt.subplots()
    try:
        assert panel.paint(axis) == "drawn"
        return axis.get_title(loc="left").replace("\n", " ")
    finally:
        plt.close(figure)


def test_the_sheet_draws_the_depth_right_after_the_conjunction_and_says_its_slice_is_chosen(
    tmp_path: Path,
) -> None:
    record = _saved_record(tmp_path, selected=SELECTED)
    _, panels = view_frames.view_panels(tmp_path, record, _loaded(tmp_path, record))
    by_reading = {(p.stage, p.reading): p for p in panels}
    panel = by_reading[("field", "depth collapse")]
    assert (panel.status, panel.code) == ("saved", "present")
    assert panel.paint is not None
    assert panel.arrays == (
        *(f"depth_{lens}" for lens in LENSES),
        "depth_chosen_slices",
    )
    readings = [p.reading for p in panels]
    assert readings.index("conjunction") + 1 == readings.index("depth collapse")
    assert readings.index("depth collapse") < readings.index("structural reading")
    title = _title_of(panel)
    assert "this sheet's slice 3 is among them" in title
    assert "split_quality: slice 3 (tie_middle)" in title
    assert "chosen slices 1, 2, 3" in title


def test_the_sheet_says_when_its_slice_is_not_a_chosen_one(tmp_path: Path) -> None:
    record = _saved_record(tmp_path, selected=4)
    _, panels = view_frames.view_panels(tmp_path, record, _loaded(tmp_path, record))
    panel = {(p.stage, p.reading): p for p in panels}[("field", "depth collapse")]
    assert (panel.status, panel.code) == ("saved", "present")
    assert "this sheet's slice 4 is not among them" in _title_of(panel)


def test_the_sheet_names_a_depth_that_was_not_saved_or_cannot_be_shown(
    tmp_path: Path,
) -> None:
    unsaved = _saved_record(tmp_path, with_depth=False)
    _, panels = view_frames.view_panels(tmp_path, unsaved, _loaded(tmp_path, unsaved))
    panel = {(p.stage, p.reading): p for p in panels}[("field", "depth collapse")]
    assert (panel.status, panel.paint) == ("not_saved", None)
    absent = _saved_record(tmp_path, code="predecessor_absent")
    _, panels = view_frames.view_panels(tmp_path, absent, _loaded(tmp_path, absent))
    panel = {(p.stage, p.reading): p for p in panels}[("field", "depth collapse")]
    assert (panel.status, panel.code, panel.paint) == (
        "silent",
        "predecessor_absent",
        None,
    )
    assert panel.why.startswith("depth_absent")
    outside = _saved_record(tmp_path)
    outside["slice_index"] = 9
    _, panels = view_frames.view_panels(tmp_path, outside, _loaded(tmp_path, outside))
    panel = {(p.stage, p.reading): p for p in panels}[("field", "depth collapse")]
    assert (panel.status, panel.code, panel.paint) == ("silent", "present", None)
    assert panel.why.startswith("slice_outside_depth")


def test_the_sheet_is_drawn_with_the_depth_panel(tmp_path: Path) -> None:
    _saved_record(tmp_path)
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = view_frames.draw(tmp_path, DEPTH_STUDY, out)
        (view,) = manifest["views"]
        panel = next(p for p in view["panels"] if p["reading"] == "depth collapse")
        assert panel["drawn"] == "drawn"
        assert "depth_frames" in manifest["reused_drawers_sha256"]
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_picture_module_is_the_adapter_the_sheet_and_drawer_read() -> None:
    assert depth_frames.pictures is pictures
    assert view_frames.depth_pictures is pictures
    assert view_frames.depth_frames is depth_frames
    assert ("collapse", "depth", "depth_frames") in all_frames.DRAWINGS
    conjunction_at = all_frames.DRAWINGS.index(
        ("lenses", "conjunction", "conjunction_frames")
    )
    assert all_frames.DRAWINGS[conjunction_at + 1] == (
        "collapse",
        "depth",
        "depth_frames",
    )
    module = importlib.import_module("workbench.render.depth_frames")
    assert module.draw is depth_frames.draw
