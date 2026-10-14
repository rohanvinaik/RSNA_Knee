"""The conjunction on the route, in the receipt, in the picture adapter, on the conjunction
drawer and on the view sheet (the-funnel tasks 3c.1 and 3c.2), both signs. The route reads the
conjunction once per paired plane right after the tile digits and before the conversation,
carries it on the recipient only (the partner and a solitary series carry None) and records
nothing on their behalf; the writer saves the record once on the recipient with its counts,
codes, pair and partner identifier, and nothing on the partner; the adapter selects the walked
slices and alters nothing; the drawer refuses a saved record that disagrees with the writer and
draws one sheet per recipient, or its silence in words; a conjunction the stage did not make,
saved with (0, 0, 0) codes beside a present stack, reaches the reader, the sheet and the drawer
as the named silence `conjunction_absent` and is never compared with the stack's grid; the
sheet draws the conjunction right after the tile digits and says in words that none rides on a
partner or a solitary series."""

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
from knee.collapse.lineup import LineUp, line_up
from knee.collapse.squint_stack import read_squint_stack
from knee.lenses.conjunction import (
    CONJUNCTION_CODES,
    CONJUNCTION_RECORD_CODES,
    READ_CONJUNCTIONS,
    Conjunction,
    conjunction_code,
    read_conjunction,
)
from knee.lenses.places import SILENT
from knee.objects.analysis import AnalysisRequest
from knee.pictures import conjunction as pictures
from knee.pictures.conjunction import (
    CONJUNCTION_STANDINGS,
    conjunction_panels,
    walk_standing,
)
from knee.study.series import walk_indices
from knee.telemetry import recording
from workbench.measure.object_analysis import (
    CONJUNCTION_ARRAYS,
    array_table,
    conjunction_record,
    series_record,
    squint_stack_record,
    tile_digits_record,
)
from workbench.render import all_frames, conjunction_frames, view_frames
from workbench.render._out import PROJECT, ArgumentRefusal


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


#: The line-up's wiring fixture: a study on disk with one paired plane (a fat-dark recipient and
#: a fat-bright partner, scootched a quarter of a millimetre) and one solitary plane; and the
#: measurement fixture's corpus, whose one plane holds two fat-bright series and pairs nothing.
_lineup_fixture = _load(
    "lineup_wiring_fixture_for_conjunction",
    Path(__file__).with_name("test_lineup_wiring.py"),
)
STUDY_UID = _lineup_fixture.STUDY_UID
DARK_UID = _lineup_fixture.DARK_UID
BRIGHT_UID = _lineup_fixture.BRIGHT_UID
SOLO_UID = _lineup_fixture.SOLO_UID
_write_paired_corpus = _lineup_fixture._write_paired_corpus
_write_corpus = _lineup_fixture._write_corpus

#: The conjunction's proof gate's synthetic pair in memory: two patterned series of one plane
#: whose digits differ at known tiles, 24 x 24 at half a millimetre, a 6 x 6 grid of 2 mm tiles,
#: three slices.
_pair_fixture = _load(
    "conjunction_fixture_for_wiring",
    Path(__file__).parent / "lenses" / "test_conjunction.py",
)
_recipient = _pair_fixture._recipient
_partner = _pair_fixture._partner
_lineup = _pair_fixture._lineup
_expected = _pair_fixture._expected
TILE_MM = _pair_fixture.TILE_MM
TILES = _pair_fixture.TILES
SLICES = _pair_fixture.SLICES
PAIR_STUDY = _pair_fixture.STUDY
PAIR_DARK = _pair_fixture.DARK_UID
PAIR_BRIGHT = _pair_fixture.BRIGHT_UID

UNMATCHED = CONJUNCTION_CODES.index("unmatched")


def _request() -> AnalysisRequest:
    return AnalysisRequest(
        tile_mm=2.0,
        offsets_mm=(-0.5, 0.0, 0.5),
        direction_lps=(1.0, 0.0, 0.0),
        backend="reference",
    )


def _conversing_request() -> AnalysisRequest:
    return AnalysisRequest(
        tile_mm=2.0,
        offsets_mm=(-1.0, 0.0, 1.0),
        direction_lps=(1.0, 0.0, 0.0),
        backend="reference",
        prominence_mm=1.0,
        conversation=True,
    )


def _descriptor_table(arrays: dict[str, np.ndarray]) -> dict:
    return json.loads(json.dumps(array_table(arrays), allow_nan=False))


def _loaded(tmp_path: Path, record: dict) -> dict[str, np.ndarray]:
    with np.load(tmp_path / record["artifact"], allow_pickle=False) as saved:
        return {name: saved[name] for name in saved.files}


def _partner_absent_lineup(recipient, partner) -> LineUp:
    """The line-up of the pair when the partner has no stacked volume: the recipient's own
    stack present, the line-up `no_stacked_volume`, so the conjunction read over it is the
    stage's `predecessor_absent` beside a present stack. The ordinary form of that silence on a
    real run: a paired plane whose partner could not be stacked."""
    gone = read_squint_stack(
        _pair_fixture._series(
            PAIR_BRIGHT, "0", None, origin_x=_pair_fixture.SCOOTCH_MM
        ),
        TILE_MM,
    )
    return line_up(
        recipient[1],
        gone,
        recipient[0].geometry,
        partner[0].geometry,
        _pair_fixture.HALF_TILE_MM,
        _pair_fixture.HALF_THICKNESS_MM,
    )


def _saved_records(
    tmp_path: Path,
    *,
    with_conjunction: bool = True,
    with_stack: bool = True,
    with_plane: bool = True,
    stack_tile_mm: float = TILE_MM,
    partner_absent: bool = False,
) -> tuple[dict, dict]:
    """The recipient's and the partner's records shaped as the writer saves them, their arrays
    on disk, and a receipt beside them naming both: the recipient carries its stack, its tile
    digits and its conjunction; the partner its stack and its digits and no conjunction. With
    `partner_absent` the conjunction is the stage's `predecessor_absent` (the partner's stack
    absent at the line-up) while the recipient's own stack is present."""
    recipient, partner = _recipient(), _partner()
    lineup = (
        _partner_absent_lineup(recipient, partner)
        if partner_absent
        else _lineup(recipient, partner)
    )
    reading = read_conjunction(recipient[2], partner[2], lineup)
    records = []
    for series, stack, digits, conjunction in (
        (*recipient, reading),
        (*partner, None),
    ):
        uid = series.row.series_uid
        volume = series.volume
        assert volume is not None
        indices = walk_indices(SLICES)
        saved: dict[str, np.ndarray] = {"study_walk": volume[list(indices)]}
        entry: dict = {
            "study_uid": PAIR_STUDY,
            "series_uid": uid,
            "view": [
                series.row.anatomical_plane,
                series.row.fluid_sensitive,
                series.row.fat_suppression,
            ],
            "code": "measured",
            "slice_index": 1,
            "source_plane": "slice-1.dcm",
            "artifact": f"{uid}.npz",
            "study": {
                "slice_codes": ["decoded"] * SLICES,
                "walk_indices": list(indices),
                "walk_array": "study_walk",
            },
        }
        if with_stack:
            # The stack the conjunction is placed by; at another tile than the conjunction's
            # it is another grid.
            stack_record, stack_arrays = squint_stack_record(
                read_squint_stack(series, stack_tile_mm)
                if conjunction is not None
                else stack
            )
            saved.update(stack_arrays)
            entry["squint_stack"] = stack_record
        digits_record, digits_arrays = tile_digits_record(digits)
        saved.update(digits_arrays)
        entry["tile_digits"] = digits_record
        if conjunction is not None and with_conjunction:
            conjunction_fields, conjunction_arrays = conjunction_record(conjunction)
            saved.update(conjunction_arrays)
            entry["conjunction"] = conjunction_fields
        if with_plane:
            saved["acquired_plane"] = volume[1]
        np.savez_compressed(tmp_path / entry["artifact"], allow_pickle=False, **saved)
        entry["arrays"] = _descriptor_table(saved)
        records.append(json.loads(json.dumps(entry, allow_nan=False)))
    receipt = {"records": records, "studies": [{"study_uid": PAIR_STUDY}]}
    (tmp_path / "receipt.json").write_text(json.dumps(receipt, allow_nan=False))
    return records[0], records[1]


# --- the route ---------------------------------------------------------------------------------


def test_run_study_reads_the_conjunction_once_per_paired_plane_right_after_the_digits(
    tmp_path: Path,
) -> None:
    _write_paired_corpus(tmp_path)
    with recording() as run_ledger:
        result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    events = run_ledger.events()
    names = [event.name for event in events]
    assert names.count("tile_digits.consumed_by.conjunction") == 1
    assert names.count("lineup.consumed_by.conjunction") == 1
    assert names.count("conjunction.produced") == 1
    read_at = names.index("tile_digits.consumed_by.conjunction")
    # After every series' tile digits and the line-up, and before anything of step 3 reads a
    # record: the conjunction is the digits' and the line-up's reader in this phase.
    assert (
        max(i for i, name in enumerate(names) if name == "tile_digits.produced")
        < read_at
    )
    assert names.index("lineup.produced") < read_at
    assert read_at < names.index("lineup.consumed_by.conjunction")
    assert names.index("lineup.consumed_by.conjunction") < names.index(
        "conjunction.produced"
    )
    assert names.index("conjunction.produced") < names.index(
        "lenses.consumed_by.vectors"
    )
    assert names.index("conjunction.produced") < names.index("ownership.produced")
    # Its one reader in this phase is the depth collapse (the-funnel task 4.3), which records
    # that read itself, once, on the recipient only; later the dome and the bundles.
    assert [name for name in names if name.startswith("conjunction.consumed_by")] == [
        "conjunction.consumed_by.depth"
    ]
    assert names.index("conjunction.produced") < names.index(
        "conjunction.consumed_by.depth"
    )
    assert [
        dict(e.counts)
        for e in events
        if e.name == "tile_digits.consumed_by.conjunction"
    ] == [{"own": 1, "partner": 1}]
    assert [
        dict(e.counts) for e in events if e.name == "lineup.consumed_by.conjunction"
    ] == [{"lineup": 1}]
    produced = [dict(e.counts) for e in events if e.name == "conjunction.produced"]
    assert len(produced) == 1 and set(produced[0]) == {"read"}
    by_uid = {run.series_uid: run for run in result.series}
    reading = by_uid[DARK_UID].conjunction
    assert isinstance(reading, Conjunction)
    assert reading.code == "present"
    assert reading.recipient_uid == DARK_UID and reading.partner_uid == BRIGHT_UID
    assert reading.codes.shape == (3, 4, 4) and reading.codes.dtype == np.uint8
    assert sum(reading.counts) == 3 * 4 * 4
    assert produced[0]["read"] == sum(reading.counts[: len(READ_CONJUNCTIONS)])
    # The codes are the scalar decision over the run's own digits and line-up at every tile.
    own, partner, lineup = (
        by_uid[DARK_UID].tile_digits,
        by_uid[BRIGHT_UID].tile_digits,
        by_uid[DARK_UID].lineup,
    )
    assert own is not None and partner is not None and lineup is not None
    np.testing.assert_array_equal(reading.codes, _expected(own, partner, lineup))
    # The partner and the solitary series carry no conjunction: that is the silence it is.
    assert by_uid[BRIGHT_UID].conjunction is None
    assert by_uid[SOLO_UID].conjunction is None


def test_the_conjunction_precedes_the_conversation_and_the_stages_that_read_the_parse(
    tmp_path: Path,
) -> None:
    _write_paired_corpus(tmp_path)
    with recording() as run_ledger:
        pipeline.open_and_run(tmp_path, STUDY_UID, _conversing_request())
    names = [event.name for event in run_ledger.events()]
    assert names.index("conjunction.produced") < names.index("conversation.produced")
    assert names.index("conjunction.produced") < names.index("ownership.produced")
    assert names.index("conjunction.produced") < names.index("relations.produced")


def test_the_route_reads_no_conjunction_when_no_plane_is_paired(tmp_path: Path) -> None:
    # MUST NOT: record a read of digits or a line-up it never read, or a production that never
    # happened; the fixture's corpus has one plane with two fat-bright series, a surplus.
    _write_corpus(tmp_path)
    with recording() as run_ledger:
        result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    names = [event.name for event in run_ledger.events()]
    assert not [name for name in names if "conjunction" in name]
    assert all(run.conjunction is None for run in result.series)


def test_a_run_built_without_the_operation_carries_no_conjunction() -> None:
    run = pipeline.SeriesRun("u", ("Coronal", "1", "1"), ("stackable",), None, "read")
    assert run.conjunction is None


# --- the writer --------------------------------------------------------------------------------


def test_the_recipients_record_carries_the_conjunction_and_the_partners_carries_none(
    tmp_path: Path,
) -> None:
    _write_paired_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    by_uid = {run.series_uid: run for run in result.series}
    record, arrays = series_record(STUDY_UID, by_uid[DARK_UID], "reference")
    saved = record["conjunction"]
    reading = by_uid[DARK_UID].conjunction
    assert reading is not None
    assert saved["code"] == reading.code and saved["why"] == reading.why
    assert saved["recipient_uid"] == DARK_UID and saved["partner_uid"] == BRIGHT_UID
    assert saved["code_names"] == list(CONJUNCTION_CODES)
    assert saved["read_names"] == list(READ_CONJUNCTIONS)
    assert saved["counts"] == dict(zip(CONJUNCTION_CODES, reading.counts, strict=True))
    assert saved["slices"] == 3 and saved["tiles_rc"] == [4, 4]
    assert saved["arrays"] == {
        name: f"conjunction_{name}" for name in CONJUNCTION_ARRAYS
    }
    np.testing.assert_array_equal(arrays["conjunction_codes"], reading.codes)
    descriptors = array_table(arrays)
    assert descriptors["conjunction_codes"]["shape"] == (3, 4, 4)
    assert descriptors["conjunction_codes"]["dtype"] == "|u1"
    # Plain data: it round-trips through the receipt's JSON, which refuses NaN.
    assert json.loads(json.dumps(saved, allow_nan=False)) == saved
    # Saved ONCE: one key, one array, beside the digits', the line-up's and the stack's keys.
    assert [name for name in arrays if name.startswith("conjunction_")] == [
        "conjunction_codes"
    ]
    assert "tile_digits_codes" in arrays and "lineup_match_codes" in arrays
    # The partner's and the solitary series' records carry no conjunction key and no
    # conjunction array: their silence.
    for uid in (BRIGHT_UID, SOLO_UID):
        other, other_arrays = series_record(STUDY_UID, by_uid[uid], "reference")
        assert "conjunction" not in other
        assert not [name for name in other_arrays if name.startswith("conjunction_")]


def test_an_absent_conjunction_is_saved_as_its_silence_with_empty_arrays() -> None:
    recipient, partner = _recipient(), _partner()
    reading = read_conjunction(
        recipient[2], partner[2], _partner_absent_lineup(recipient, partner)
    )
    assert reading.code == "predecessor_absent"
    record, arrays = conjunction_record(reading)
    assert record["code"] == "predecessor_absent"
    assert record["slices"] == 0 and record["tiles_rc"] == [0, 0]
    assert all(count == 0 for count in record["counts"].values())
    assert json.loads(json.dumps(record, allow_nan=False)) == record
    assert set(arrays) == {f"conjunction_{name}" for name in CONJUNCTION_ARRAYS}
    assert arrays["conjunction_codes"].shape == (0, 0, 0)


# --- the adapter -------------------------------------------------------------------------------


def test_the_standing_names_a_named_slice_and_every_silence_apart() -> None:
    assert walk_standing("present", 0, 3) == "named"
    assert walk_standing("present", 2, 3) == "named"
    assert walk_standing(None, 0, 3) == "conjunction_not_saved"
    assert walk_standing("predecessor_absent", 0, 0) == "conjunction_absent"
    assert walk_standing("present", 3, 3) == "slice_outside_conjunction"
    assert walk_standing("present", -1, 3) == "slice_outside_conjunction"
    assert walk_standing("present", 0, 0) == "slice_outside_conjunction"
    assert walk_standing("lesion", 0, 3) == "conjunction_code_unknown"


def test_the_standing_is_total_and_never_named_without_a_held_slice() -> None:
    # MUST NOT: draw a slice from a conjunction whose predecessor was absent, nor from an
    # index that is not a whole number inside it; and every answer is one of the declared
    # standings.
    for code in (*CONJUNCTION_RECORD_CODES, None, "", 1):
        for index in (0, 1, 2, 3, -1, True, 1.0, None, "1"):
            standing = walk_standing(code, index, 3)
            assert standing in CONJUNCTION_STANDINGS, (code, index)
            if standing == "named":
                assert code == "present"
                assert type(index) is int and 0 <= index < 3


def test_the_adapter_selects_the_walked_slices_and_alters_nothing() -> None:
    recipient, partner = _recipient(), _partner()
    reading = read_conjunction(recipient[2], partner[2], _lineup(recipient, partner))
    volume = recipient[0].volume
    assert volume is not None
    indices = walk_indices(SLICES)
    walk = volume[list(indices)]
    frame = conjunction_panels(
        reading.code,
        reading.why,
        reading.recipient_uid,
        reading.partner_uid,
        reading.counts,
        reading.codes,
        recipient[1].bounds_rc,
        indices,
        walk,
    )
    assert frame.code == "present" and frame.slices == SLICES
    assert frame.recipient_uid == PAIR_DARK and frame.partner_uid == PAIR_BRIGHT
    assert frame.counts == reading.counts
    assert [step.index for step in frame.walked] == list(indices)
    for step, index in zip(frame.walked, indices, strict=True):
        assert step.standing == "named"
        assert step.plane is not None
        np.testing.assert_array_equal(step.plane, volume[index])
        assert step.codes is not None and step.codes.dtype == np.uint8
        np.testing.assert_array_equal(step.codes, reading.codes[index])
    assert frame.codes is not None and frame.codes.dtype == np.uint8
    assert frame.bounds_rc is not None and frame.bounds_rc.dtype == np.int64


def test_the_adapter_keeps_every_absence_absent() -> None:
    frame = conjunction_panels(None, None, None, None, None, None, None, (0, 2), None)
    assert frame.code is None and frame.slices == 0 and frame.codes is None
    assert frame.recipient_uid is None and frame.partner_uid is None
    assert frame.counts is None and frame.bounds_rc is None
    assert [step.standing for step in frame.walked] == ["conjunction_not_saved"] * 2
    assert all(step.plane is None and step.codes is None for step in frame.walked)
    absent = conjunction_panels(
        "predecessor_absent",
        "why",
        PAIR_DARK,
        PAIR_BRIGHT,
        (0,) * len(CONJUNCTION_CODES),
        np.empty((0, 0, 0), dtype=np.uint8),
        np.empty((0, 0, 4), dtype=np.int64),
        (0,),
        None,
    )
    assert [step.standing for step in absent.walked] == ["conjunction_absent"]


# --- the drawer's reader -----------------------------------------------------------------------


def test_the_reader_reconstitutes_a_writer_shaped_record(tmp_path: Path) -> None:
    recipient, _ = _saved_records(tmp_path)
    artifact, frame = conjunction_frames.saved_conjunction(tmp_path, recipient)
    assert artifact == tmp_path / f"{PAIR_DARK}.npz"
    assert frame.code == "present" and frame.slices == SLICES
    assert frame.recipient_uid == PAIR_DARK and frame.partner_uid == PAIR_BRIGHT
    assert frame.counts is not None and sum(frame.counts) == SLICES * TILES * TILES
    assert frame.codes is not None and frame.codes.shape == (SLICES, TILES, TILES)
    assert frame.bounds_rc is not None and frame.bounds_rc.shape == (TILES, TILES, 4)
    assert [step.standing for step in frame.walked] == ["named"] * SLICES
    assert all(step.plane is not None for step in frame.walked)
    first = frame.walked[0].codes
    assert first is not None
    counts = conjunction_frames.code_counts(first)
    assert set(counts) == set(CONJUNCTION_CODES)
    assert sum(counts.values()) == TILES * TILES
    # The known tiles of the proof gate's pair, read off the saved codes.
    words = [[CONJUNCTION_CODES[c] for c in row] for row in first]
    assert words[3][3] == "above_below" and words[2][2] == "below_above"
    assert conjunction_frames.read_count(counts) == sum(
        counts[name] for name in READ_CONJUNCTIONS
    )


def test_the_reader_says_when_no_conjunction_was_saved(tmp_path: Path) -> None:
    recipient, partner = _saved_records(tmp_path, with_conjunction=False)
    for record in (recipient, partner):
        _, frame = conjunction_frames.saved_conjunction(tmp_path, record)
        assert frame.code is None and frame.codes is None and frame.bounds_rc is None
        assert [step.standing for step in frame.walked] == [
            "conjunction_not_saved"
        ] * SLICES


def test_the_reader_hands_on_a_conjunction_the_stage_did_not_make_as_its_silence(
    tmp_path: Path,
) -> None:
    # The ordinary form of the stage's silence: the partner's stack absent while the recipient
    # stacks, so the writer saved (0, 0, 0) codes beside a present three-slice 6 x 6 stack. The
    # reader names it, and never compares the empty grid with the stack's.
    recipient, _ = _saved_records(tmp_path, partner_absent=True)
    assert recipient["conjunction"]["code"] == "predecessor_absent"
    assert recipient["squint_stack"]["code"] == "present"
    assert recipient["squint_stack"]["slices"] == SLICES
    artifact, frame = conjunction_frames.saved_conjunction(tmp_path, recipient)
    assert artifact == tmp_path / f"{PAIR_DARK}.npz"
    assert frame.code == "predecessor_absent"
    assert "line-up is no_stacked_volume" in str(frame.why)
    assert frame.recipient_uid == PAIR_DARK and frame.partner_uid == PAIR_BRIGHT
    assert frame.slices == 0
    assert frame.codes is not None and frame.codes.shape == (0, 0, 0)
    assert frame.counts == (0,) * len(CONJUNCTION_CODES)
    assert frame.bounds_rc is None
    assert [step.standing for step in frame.walked] == ["conjunction_absent"] * SLICES
    assert all(step.codes is None for step in frame.walked)
    assert all(step.plane is not None for step in frame.walked)
    # MUST NOT: hand on an absent conjunction that holds codes, which the stage never writes,
    # nor one saved without the recipient's stack; each is named and raised.
    arrays = _loaded(tmp_path, recipient)
    arrays["conjunction_codes"] = np.zeros((SLICES, TILES, TILES), dtype=np.uint8)
    np.savez_compressed(tmp_path / recipient["artifact"], allow_pickle=False, **arrays)
    held = json.loads(json.dumps(recipient))
    held["arrays"] = _descriptor_table(arrays)
    held["conjunction"]["slices"] = SLICES
    held["conjunction"]["tiles_rc"] = [TILES, TILES]
    with pytest.raises(ValueError, match="saved_conjunction_absent_with_codes"):
        conjunction_frames.saved_conjunction(tmp_path, held)
    alone, _ = _saved_records(tmp_path, partner_absent=True, with_stack=False)
    with pytest.raises(ValueError, match="saved_conjunction_without_a_stack"):
        conjunction_frames.saved_conjunction(tmp_path, alone)


def test_the_reader_refuses_a_saved_record_that_disagrees_with_the_writer(
    tmp_path: Path,
) -> None:
    # MUST NOT: draw a tampered array, a code the stage does not say, a conjunction saved for
    # another recipient, a slice count that is not the codes', a vocabulary that is not the
    # stage's, counts that are not the stage's, a code value outside the vocabulary, a
    # conjunction saved without its stack, or a stack whose grid is not the conjunction's;
    # each is named and raised.
    recipient, _ = _saved_records(tmp_path)

    def copy() -> dict:
        return json.loads(json.dumps(recipient))

    tampered = copy()
    tampered["arrays"]["conjunction_codes"]["digest"] = "changed"
    with pytest.raises(ValueError, match="saved_array_digest_mismatch"):
        conjunction_frames.saved_conjunction(tmp_path, tampered)
    named = copy()
    named["conjunction"]["code"] = "lesion"
    with pytest.raises(ValueError, match="saved_conjunction_code_unknown"):
        conjunction_frames.saved_conjunction(tmp_path, named)
    other = copy()
    other["conjunction"]["recipient_uid"] = "another"
    with pytest.raises(ValueError, match="saved_conjunction_recipient_mismatch"):
        conjunction_frames.saved_conjunction(tmp_path, other)
    counted = copy()
    counted["conjunction"]["slices"] = 2
    with pytest.raises(ValueError, match="saved_conjunction_slices_mismatch"):
        conjunction_frames.saved_conjunction(tmp_path, counted)
    worded = copy()
    worded["conjunction"]["code_names"] = list(READ_CONJUNCTIONS)
    with pytest.raises(ValueError, match="saved_conjunction_vocabulary_mismatch"):
        conjunction_frames.saved_conjunction(tmp_path, worded)
    miscounted = copy()
    miscounted["conjunction"]["counts"] = {"at_at": 1}
    with pytest.raises(ValueError, match="saved_conjunction_counts_invalid"):
        conjunction_frames.saved_conjunction(tmp_path, miscounted)
    shaped = copy()
    shaped["conjunction"] = "yes"
    with pytest.raises(ValueError, match="saved_conjunction_not_a_record"):
        conjunction_frames.saved_conjunction(tmp_path, shaped)
    unnamed = copy()
    unnamed["conjunction"]["partner_uid"] = None
    with pytest.raises(ValueError, match="saved_conjunction_field_invalid:partner_uid"):
        conjunction_frames.saved_conjunction(tmp_path, unnamed)
    outside = copy()
    arrays = _loaded(tmp_path, outside)
    arrays["conjunction_codes"] = np.full(
        arrays["conjunction_codes"].shape, len(CONJUNCTION_CODES), dtype=np.uint8
    )
    np.savez_compressed(tmp_path / outside["artifact"], allow_pickle=False, **arrays)
    outside["arrays"] = _descriptor_table(arrays)
    with pytest.raises(ValueError, match="saved_conjunction_code_unknown:codes"):
        conjunction_frames.saved_conjunction(tmp_path, outside)
    alone, _ = _saved_records(tmp_path, with_stack=False)
    with pytest.raises(ValueError, match="saved_conjunction_without_a_stack"):
        conjunction_frames.saved_conjunction(tmp_path, alone)
    other_grid, _ = _saved_records(tmp_path, stack_tile_mm=4.0)
    with pytest.raises(ValueError, match="saved_conjunction_grid_mismatch"):
        conjunction_frames.saved_conjunction(tmp_path, other_grid)


# --- the drawer --------------------------------------------------------------------------------


def test_an_out_directory_outside_data_is_an_argument_refusal(tmp_path: Path) -> None:
    _saved_records(tmp_path)
    with pytest.raises(ArgumentRefusal, match="private data directory"):
        conjunction_frames.draw(tmp_path, PAIR_STUDY, tmp_path / "out")


def test_the_drawer_writes_one_sheet_per_recipient_with_its_manifest(
    tmp_path: Path,
) -> None:
    """The impure edge, end to end: one image per recipient under data/, bound to the receipt."""
    _saved_records(tmp_path)
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = conjunction_frames.draw(tmp_path, PAIR_STUDY, out)
        # The recipient is the first record, so its sheet carries the view sheets' first name;
        # the partner, the second record, has no sheet.
        assert manifest["images"] == ["01-coronal-fs1-fat1.png"]
        assert manifest["image"] == "01-coronal-fs1-fat1.png"
        assert (out / "01-coronal-fs1-fat1.png").exists()
        assert (out / "manifest.json").exists()
        assert manifest["silence"] is None
        assert manifest["standings"] == list(CONJUNCTION_STANDINGS)
        assert list(manifest["legend"]["pairs"]) == list(READ_CONJUNCTIONS)
        assert len(set(manifest["legend"]["pairs"].values())) == 9
        assert set(manifest["legend"]["neutral"]) == {
            "partner_silent",
            "self_silent",
            "unmatched",
            "invalid_measurement",
        }
        (series,) = manifest["series"]
        assert series["image"] == "01-coronal-fs1-fat1.png"
        assert (
            series["series_uid"] == PAIR_DARK and series["partner_uid"] == PAIR_BRIGHT
        )
        assert series["conjunction"]["code"] == "present"
        assert series["conjunction"]["tiles_rc"] == [TILES, TILES]
        assert sum(series["conjunction"]["counts"].values()) == SLICES * TILES * TILES
        assert [step["drawn"] for step in series["walked"]] == ["named"] * SLICES
        assert all(
            sum(step["counts"].values()) == TILES * TILES for step in series["walked"]
        )
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_a_study_with_no_recipient_draws_its_silence_in_words(tmp_path: Path) -> None:
    _, partner = _saved_records(tmp_path)
    receipt = {"records": [partner], "studies": [{"study_uid": PAIR_STUDY}]}
    (tmp_path / "receipt.json").write_text(json.dumps(receipt, allow_nan=False))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = conjunction_frames.draw(tmp_path, PAIR_STUDY, out)
        assert (out / "series.png").exists()
        assert manifest["images"] == ["series.png"]
        assert manifest["series"] == []
        assert manifest["silence"] is not None
        assert "no series of this study carries a conjunction" in manifest["silence"]
    finally:
        shutil.rmtree(out, ignore_errors=True)


# --- the view sheet ----------------------------------------------------------------------------


def test_the_sheet_draws_the_conjunction_on_the_recipient_right_after_the_tile_digits(
    tmp_path: Path,
) -> None:
    recipient, _ = _saved_records(tmp_path)
    _, panels = view_frames.view_panels(
        tmp_path, recipient, _loaded(tmp_path, recipient)
    )
    by_reading = {(p.stage, p.reading): p for p in panels}
    panel = by_reading[("lenses", "conjunction")]
    assert (panel.status, panel.code) == ("saved", "present")
    assert panel.paint is not None
    assert panel.arrays == ("conjunction_codes",)
    readings = [p.reading for p in panels]
    assert readings.index("tile digits") + 1 == readings.index("conjunction")
    assert readings.index("conjunction") < readings.index("structural reading")


def test_the_sheet_says_in_words_that_no_conjunction_rides_on_a_partner(
    tmp_path: Path,
) -> None:
    _, partner = _saved_records(tmp_path)
    _, panels = view_frames.view_panels(tmp_path, partner, _loaded(tmp_path, partner))
    panel = {(p.stage, p.reading): p for p in panels}[("lenses", "conjunction")]
    assert (panel.status, panel.paint) == ("not_saved", None)
    assert panel.why.startswith("no conjunction rides on this series")
    assert "recipient" in panel.why
    # A series whose writer saved no conjunction at all says the same words.
    recipient, _ = _saved_records(tmp_path, with_conjunction=False)
    _, panels = view_frames.view_panels(
        tmp_path, recipient, _loaded(tmp_path, recipient)
    )
    panel = {(p.stage, p.reading): p for p in panels}[("lenses", "conjunction")]
    assert (panel.status, panel.paint) == ("not_saved", None)
    assert panel.why == view_frames.NO_CONJUNCTION_WORDS


def test_the_sheet_names_a_slice_the_conjunction_cannot_show(tmp_path: Path) -> None:
    recipient, _ = _saved_records(tmp_path)
    outside = json.loads(json.dumps(recipient))
    outside["slice_index"] = 9
    _, panels = view_frames.view_panels(tmp_path, outside, _loaded(tmp_path, outside))
    panel = {(p.stage, p.reading): p for p in panels}[("lenses", "conjunction")]
    assert (panel.status, panel.code, panel.paint) == ("silent", "present", None)
    assert panel.why.startswith("slice_outside_conjunction")


def test_the_sheet_and_the_drawer_say_in_words_that_the_stage_named_no_tile(
    tmp_path: Path,
) -> None:
    # A writer-shaped `predecessor_absent` record of the partner-absent form, with the
    # recipient's stack present, reaches the sheet's panel and the drawer's sheet as the
    # adapter's own silence, in words; before this both raised `saved_conjunction_grid_mismatch`
    # and every view sheet of the study went undrawn.
    recipient, _ = _saved_records(tmp_path, partner_absent=True)
    panel = view_frames.conjunction_panel(
        _loaded(tmp_path, recipient)["acquired_plane"], tmp_path, recipient
    )
    assert (panel.status, panel.code, panel.paint) == (
        "silent",
        "predecessor_absent",
        None,
    )
    assert panel.why.startswith("conjunction_absent: ")
    assert "line-up is no_stacked_volume" in panel.why
    assert panel.arrays == ("conjunction_codes",)
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = conjunction_frames.draw(tmp_path, PAIR_STUDY, out)
        assert manifest["images"] == ["01-coronal-fs1-fat1.png"]
        assert manifest["silence"] is None
        (series,) = manifest["series"]
        assert series["conjunction"]["code"] == "predecessor_absent"
        assert series["conjunction"]["slices"] == 0
        assert [step["drawn"] for step in series["walked"]] == [
            "conjunction_absent"
        ] * SLICES
        # MUST NOT: record a slice as named, or count a tile, from a conjunction that holds
        # none.
        assert {step["standing"] for step in series["walked"]} == {"conjunction_absent"}
        assert all(step["counts"] == {} for step in series["walked"])
        sheets = view_frames.draw(tmp_path, PAIR_STUDY, out / "views")
        views = {view["series_uid"]: view for view in sheets["views"]}
        drawn = next(
            p for p in views[PAIR_DARK]["panels"] if p["reading"] == "conjunction"
        )
        assert (drawn["drawn"], drawn["code"]) == ("silent", "predecessor_absent")
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_sheet_refuses_a_conjunction_that_covers_another_plane(
    tmp_path: Path,
) -> None:
    # MUST NOT: lay a 24 x 24 grid's tiles over a 4 x 4 plane. The panel is asked directly:
    # on the whole sheet the squint stack's own panel refuses the same plane first.
    recipient, _ = _saved_records(tmp_path)
    with pytest.raises(ValueError, match="saved_conjunction_covers_another_plane"):
        view_frames.conjunction_panel(
            np.arange(16, dtype=np.uint16).reshape(4, 4), tmp_path, recipient
        )


def test_the_sheet_is_drawn_with_the_conjunction_panel_on_the_recipient(
    tmp_path: Path,
) -> None:
    _saved_records(tmp_path)
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = view_frames.draw(tmp_path, PAIR_STUDY, out)
        views = {view["series_uid"]: view for view in manifest["views"]}
        recipient = next(
            p for p in views[PAIR_DARK]["panels"] if p["reading"] == "conjunction"
        )
        assert recipient["drawn"] == "drawn"
        partner = next(
            p for p in views[PAIR_BRIGHT]["panels"] if p["reading"] == "conjunction"
        )
        assert partner["drawn"] == "not_saved"
        assert "conjunction_frames" in manifest["reused_drawers_sha256"]
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_picture_module_is_the_adapter_the_sheet_and_drawer_read() -> None:
    assert conjunction_frames.pictures is pictures
    assert view_frames.conjunction_pictures is pictures
    assert view_frames.conjunction_frames is conjunction_frames
    assert ("lenses", "conjunction", "conjunction_frames") in all_frames.DRAWINGS
    digits_at = all_frames.DRAWINGS.index(
        ("lenses", "tile_digits", "tile_digit_frames")
    )
    assert all_frames.DRAWINGS[digits_at + 1] == (
        "lenses",
        "conjunction",
        "conjunction_frames",
    )
    module = importlib.import_module("workbench.render.conjunction_frames")
    assert module.draw is conjunction_frames.draw


def test_the_unmatched_word_is_the_scalars_and_the_colours_cover_the_vocabulary() -> (
    None
):
    # The drawer colours every word the stage says, and the word for a tile with no partner
    # tile is the decision's own.
    assert set(conjunction_frames.CODE_COLOURS) == set(CONJUNCTION_CODES)
    assert set(conjunction_frames.CODE_ALPHAS) == set(CONJUNCTION_CODES)
    assert CONJUNCTION_CODES[UNMATCHED] == conjunction_code(
        SILENT, SILENT, "partner_unavailable"
    )
