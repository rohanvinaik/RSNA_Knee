"""The line-up on the route, in the receipt, in the picture adapter, on the line-up drawer and on
the view sheet (the-funnel tasks 3a.1 and 3a.2), both signs. The route hands the pairs record and
every stack to `read_lineups` once per study, after every stack and before any lens reads a
tile (the first lens reads the stack's tiles only after the line-ups), and carries the line-up
on the recipient; the operation reads the pairs record itself and
reads no stack of a plane that is not paired; the writer saves every array on the recipient and
nothing on the partner; the adapter selects one slice, places the partner's centres through the
recipient's frame and alters nothing; the drawer finds the partner through the receipt and
refuses a saved record that disagrees with the writer; the sheet draws the line-up next to the
squint stack and names every silence."""

from __future__ import annotations

import csv
import importlib
import importlib.util
import json
import math
import shutil
import uuid
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, MRImageStorage, generate_uid

from knee import pipeline
from knee.collapse.lineup import (
    MATCH_CODES,
    SLAB_CODES,
    LineUp,
    line_up,
    read_lineups,
)
from knee.collapse.physical import PlaneFrame
from knee.collapse.squint_stack import read_squint_stack
from knee.objects.analysis import DEFAULT_HALF_TILE_MM, AnalysisRequest
from knee.pictures import lineup as pictures
from knee.pictures.lineup import SLICE_STANDINGS, lineup_panels, slice_standing
from knee.study.pairs import AcquisitionPair, AcquisitionPairs
from knee.study.series import Series, SeriesGeometry, walk_indices
from knee.study.tables import LABELS, SeriesRow
from knee.telemetry import recording
from workbench.measure.object_analysis import (
    LINEUP_ARRAYS,
    array_table,
    lineup_record,
    pairs_record,
    series_record,
    squint_stack_record,
)
from workbench.render import all_frames, lineup_frames, view_frames
from workbench.render._out import PROJECT, ArgumentRefusal

_fixture_path = Path(__file__).with_name("test_pipeline_measurements.py")
_fixture_spec = importlib.util.spec_from_file_location(
    "pipeline_measurement_fixture_for_lineup", _fixture_path
)
assert _fixture_spec is not None and _fixture_spec.loader is not None
_fixture_module = importlib.util.module_from_spec(_fixture_spec)
_fixture_spec.loader.exec_module(_fixture_module)
STUDY_UID = _fixture_module.STUDY_UID
_write_corpus = _fixture_module._write_corpus

#: The synthetic study: two series of one plane, one fat-dark (the recipient) and one fat-bright
#: (the partner), and a solitary series of another plane. 16 x 16 planes at half a millimetre,
#: three slices one millimetre apart and one millimetre thick; a 2 mm tile is 4 px, a 4 x 4 grid.
DARK_UID = "series-coronal-dark"
BRIGHT_UID = "series-coronal-bright"
SOLO_UID = "series-axial-solo"
AXIAL = ("1", "0", "0", "0", "1", "0")
SLICES, ROWS, COLUMNS = 3, 16, 16
SPACING_MM = 0.5
TILE_MM = 2.0
HALF_TILE_MM = TILE_MM / 2.0
THICKNESS_MM = 1.0
#: The "scootch": the partner's origin lies a quarter of a millimetre along the column direction
#: (the header's first triplet, +x) from the recipient's, half a pixel at half a millimetre.
SCOOTCH_MM = 0.25

PAIRED = AcquisitionPair("Coronal", (BRIGHT_UID,), (DARK_UID,), (), "paired")
SOLO = AcquisitionPair("Axial", (), (SOLO_UID,), (), "solitary")

MATCHED = MATCH_CODES.index("matched")
UNAVAILABLE = MATCH_CODES.index("partner_unavailable")
IN_SLAB = SLAB_CODES.index("in_slab")
INVALID_SLAB = SLAB_CODES.index("invalid_measurement")


def _request() -> AnalysisRequest:
    return AnalysisRequest(
        tile_mm=TILE_MM,
        offsets_mm=(-0.5, 0.0, 0.5),
        direction_lps=(1.0, 0.0, 0.0),
        backend="reference",
    )


def _pixels(z: int) -> np.ndarray:
    rows, columns = np.indices((ROWS, COLUMNS))
    return (200 + 11 * rows + 7 * columns + 3 * z).astype(np.uint16)


# --- the synthetic corpus on disk, for the route ------------------------------------------------


def _write_slice(path: Path, pixels: np.ndarray, *, position, instance: int) -> None:
    meta = FileMetaDataset()
    meta.MediaStorageSOPClassUID = MRImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds = Dataset()
    ds.file_meta = meta
    ds.SOPClassUID = MRImageStorage
    ds.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    ds.Modality = "MR"
    ds.InstanceNumber = instance
    ds.Rows, ds.Columns = pixels.shape
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 0
    ds.ImagePositionPatient = [str(value) for value in position]
    ds.ImageOrientationPatient = list(AXIAL)
    ds.PixelSpacing = [str(SPACING_MM), str(SPACING_MM)]
    ds.SliceThickness = str(THICKNESS_MM)
    ds.PixelData = pixels.astype(np.uint16, copy=False).tobytes()
    ds.save_as(path, enforce_file_format=True)


def _write_paired_corpus(root: Path) -> None:
    """A study with one paired plane and one solitary plane, in Kaggle's own layout."""
    (root / "train_series.csv").parent.mkdir(parents=True, exist_ok=True)
    with (root / "train.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("StudyInstanceUID", "Report", *LABELS))
        writer.writerow((STUDY_UID, "", *([""] * len(LABELS))))
    with (root / "test.csv").open("w", newline="", encoding="utf-8") as stream:
        csv.writer(stream).writerow(("StudyInstanceUID",))
    header = (
        "StudyInstanceUID",
        "SeriesInstanceUID",
        "Fluid_Sensitive",
        "Fat_Suppression",
        "Anatomical_Plane",
    )
    with (root / "train_series.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerow((STUDY_UID, DARK_UID, "1", "1", "Coronal"))
        writer.writerow((STUDY_UID, BRIGHT_UID, "0", "0", "Coronal"))
        writer.writerow((STUDY_UID, SOLO_UID, "1", "1", "Axial"))
    with (root / "test_series.csv").open("w", newline="", encoding="utf-8") as stream:
        csv.writer(stream).writerow(header)
    for uid, origin_x in ((DARK_UID, 0.0), (BRIGHT_UID, SCOOTCH_MM), (SOLO_UID, 0.0)):
        directory = root / "train_series" / STUDY_UID / uid
        directory.mkdir(parents=True)
        for z in range(SLICES):
            _write_slice(
                directory / f"slice-{z}.dcm",
                _pixels(z),
                position=(origin_x, 0.0, float(z)),
                instance=z + 1,
            )


# --- the synthetic series in memory, for the operation and the pictures --------------------------


def _series(
    uid: str, flavour: str, plane: str, origin_x: float = 0.0, thickness=THICKNESS_MM
) -> Series:
    volume = np.stack([_pixels(z) for z in range(SLICES)])
    positions = np.array([[origin_x, 0.0, float(z)] for z in range(SLICES)])
    geometry = SeriesGeometry(
        normal=np.array([0.0, 0.0, 1.0]),
        orientation=np.tile(np.array([float(v) for v in AXIAL]), (SLICES, 1)),
        position=positions,
        spacing=np.full((SLICES, 2), SPACING_MM),
        along_normal=positions[:, 2],
        orientation_spread=0.0,
        origin_spread_mm=0.0,
    )
    indices = walk_indices(SLICES)
    return Series(
        row=SeriesRow(STUDY_UID, uid, flavour, flavour, plane),
        directory=Path("/nonexistent/the-funnel/lineup-wiring") / uid,
        slices=(),
        stack=("stackable",),
        volume=volume,
        geometry=geometry,
        slice_codes=("decoded",) * SLICES,
        walk_indices=indices,
        walk=volume[list(indices)],
        slice_thickness_mm=(thickness,) * SLICES,
    )


def _dark_and_bright() -> tuple[Series, Series]:
    return (
        _series(DARK_UID, "1", "Coronal"),
        _series(BRIGHT_UID, "0", "Coronal", origin_x=SCOOTCH_MM),
    )


def _stacks(*series: Series) -> dict:
    return {s.row.series_uid: read_squint_stack(s, TILE_MM) for s in series}


def _pairs(*pairs: AcquisitionPair) -> AcquisitionPairs:
    return AcquisitionPairs(STUDY_UID, pairs, "present")


def _geometries(*series: Series) -> dict:
    return {s.row.series_uid: s.geometry for s in series}


def _thicknesses(*series: Series) -> dict:
    return {s.row.series_uid: s.slice_thickness_mm for s in series}


def _frame_at(series: Series, index: int) -> PlaneFrame:
    geometry = series.geometry
    assert geometry is not None
    return PlaneFrame.from_dicom(
        geometry.position[index], geometry.orientation[index], geometry.spacing[index]
    )


def _descriptor_table(arrays: dict[str, np.ndarray]) -> dict:
    return json.loads(json.dumps(array_table(arrays), allow_nan=False))


def _loaded(tmp_path: Path, record: dict) -> dict[str, np.ndarray]:
    with np.load(tmp_path / record["artifact"], allow_pickle=False) as saved:
        return {name: saved[name] for name in saved.files}


def _saved_pair(
    tmp_path: Path,
    *,
    with_plane: bool = True,
    with_frame: bool = True,
    recipient_stack_tile_mm: float = TILE_MM,
) -> tuple[dict, dict]:
    """The recipient's and the partner's records shaped as the writer saves them, their arrays on
    disk, and a receipt beside them naming both and the study's pairs."""
    dark, bright = _dark_and_bright()
    stacks = _stacks(dark, bright)
    reading = line_up(
        stacks[DARK_UID],
        stacks[BRIGHT_UID],
        dark.geometry,
        bright.geometry,
        HALF_TILE_MM,
        THICKNESS_MM / 2.0,
    )
    records = []
    for series, lineup in ((dark, reading), (bright, None)):
        uid = series.row.series_uid
        assert series.walk is not None and series.volume is not None
        saved: dict[str, np.ndarray] = {"study_walk": series.walk}
        entry: dict = {
            "study_uid": STUDY_UID,
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
                "slice_codes": list(series.slice_codes),
                "walk_indices": list(series.walk_indices),
                "walk_array": "study_walk",
            },
        }
        stack = (
            read_squint_stack(series, recipient_stack_tile_mm)
            if lineup is not None
            else stacks[uid]
        )
        stack_record, stack_arrays = squint_stack_record(stack)
        saved.update(stack_arrays)
        entry["squint_stack"] = stack_record
        if lineup is not None:
            lineup_fields, lineup_arrays = lineup_record(lineup)
            saved.update(lineup_arrays)
            entry["lineup"] = lineup_fields
        if with_plane:
            saved["acquired_plane"] = series.volume[1]
        if with_frame:
            frame = _frame_at(series, 1)
            saved["origin_lps"] = frame.origin_lps
            saved["basis_lps"] = frame.basis_lps
            entry["spacing_rc_mm"] = list(frame.spacing_rc)
        np.savez_compressed(tmp_path / entry["artifact"], allow_pickle=False, **saved)
        entry["arrays"] = _descriptor_table(saved)
        records.append(json.loads(json.dumps(entry, allow_nan=False)))
    receipt = {
        "records": records,
        "studies": [{"study_uid": STUDY_UID, "pairs": pairs_record(_pairs(PAIRED))}],
    }
    (tmp_path / "receipt.json").write_text(json.dumps(receipt, allow_nan=False))
    return records[0], records[1]


# --- the route ---------------------------------------------------------------------------------


def test_run_study_lines_up_each_paired_plane_after_every_stack_and_before_any_lens_reads_a_tile(
    tmp_path: Path,
) -> None:
    _write_paired_corpus(tmp_path)
    with recording() as run_ledger:
        result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    events = run_ledger.events()
    names = [event.name for event in events]
    assert names.count("pairs.consumed_by.lineup") == 1
    assert names.count("squint_stack.consumed_by.lineup") == 1
    assert names.count("lineup.produced") == 1
    read_at = names.index("pairs.consumed_by.lineup")
    # After the pairs record and every stack, and before any lens reads a tile: the first lens
    # reads the stack's tiles only after the line-up, and the whole-volume lens record (voxels,
    # not tiles) is read by the bundles only after it too.
    assert names.index("pairs.produced") < read_at
    assert (
        max(i for i, name in enumerate(names) if name == "squint_stack.produced")
        < read_at
    )
    assert read_at < names.index("squint_stack.consumed_by.lineup")
    assert names.index("squint_stack.consumed_by.lineup") < names.index(
        "lineup.produced"
    )
    assert names.index("lineup.produced") < names.index(
        "squint_stack.consumed_by.first_lens"
    )
    assert names.index("lineup.produced") < names.index("first_lens.produced")
    assert names.index("lineup.produced") < names.index("lenses.consumed_by.vectors")
    assert names.index("lineup.produced") < names.index("ownership.produced")
    assert [dict(e.counts) for e in events if e.name == "pairs.consumed_by.lineup"] == [
        {"planes": 2, "paired": 1}
    ]
    assert [dict(e.counts) for e in events if e.name == "lineup.produced"] == [
        {"matched": SLICES * 16, "in_slab": SLICES}
    ]
    by_uid = {run.series_uid: run for run in result.series}
    reading = by_uid[DARK_UID].lineup
    assert isinstance(reading, LineUp)
    assert reading.code == "present"
    assert reading.recipient_uid == DARK_UID and reading.partner_uid == BRIGHT_UID
    assert reading.half_tile_mm == HALF_TILE_MM
    assert reading.half_thickness_mm == THICKNESS_MM / 2.0
    np.testing.assert_array_equal(reading.partner_slice, np.arange(SLICES))
    assert set(reading.slab_codes.tolist()) == {IN_SLAB}
    assert reading.match_codes.shape == (SLICES, 4, 4)
    assert set(reading.match_codes.ravel().tolist()) == {MATCHED}
    np.testing.assert_allclose(reading.distance_mm, SCOOTCH_MM, atol=1e-9)
    # The partner and the solitary series carry no line-up: that is the silence it is.
    assert by_uid[BRIGHT_UID].lineup is None
    assert by_uid[SOLO_UID].lineup is None


def test_the_route_reads_the_pairs_record_and_no_stack_when_no_plane_is_paired(
    tmp_path: Path,
) -> None:
    # The fixture's corpus: one plane with two fat-bright series, which is surplus.
    _write_corpus(tmp_path)
    with recording() as run_ledger:
        result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    events = run_ledger.events()
    names = [event.name for event in events]
    assert names.count("pairs.consumed_by.lineup") == 1
    assert [dict(e.counts) for e in events if e.name == "pairs.consumed_by.lineup"] == [
        {"planes": 1, "paired": 0}
    ]
    # MUST NOT: record a read of a stack it never read, or a production that never happened.
    assert "squint_stack.consumed_by.lineup" not in names
    assert "lineup.produced" not in names
    assert all(run.lineup is None for run in result.series)


def test_without_a_request_the_route_lines_up_at_the_declared_default_half_tile(
    tmp_path: Path,
) -> None:
    _write_paired_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID)
    reading = {run.series_uid: run for run in result.series}[DARK_UID].lineup
    assert reading is not None
    assert reading.half_tile_mm == DEFAULT_HALF_TILE_MM == 4.0
    # Eight millimetres at half a millimetre a pixel is one 16 px tile: one tile per slice.
    assert reading.match_codes.shape == (SLICES, 1, 1)
    assert set(reading.match_codes.ravel().tolist()) == {MATCHED}


def test_a_run_built_without_the_operation_carries_no_lineup() -> None:
    run = pipeline.SeriesRun("u", ("Coronal", "1", "1"), ("stackable",), None, "read")
    assert run.lineup is None


# --- the operation, called directly --------------------------------------------------------------


def test_read_lineups_lines_up_each_paired_plane_keyed_by_the_recipient() -> None:
    dark, bright = _dark_and_bright()
    solo = _series(SOLO_UID, "1", "Axial")
    stacks = _stacks(dark, bright, solo)
    with recording() as run_ledger:
        lineups = read_lineups(
            _pairs(PAIRED, SOLO),
            stacks,
            _geometries(dark, bright, solo),
            _thicknesses(dark, bright, solo),
            HALF_TILE_MM,
        )
    assert list(lineups) == [DARK_UID]
    reading = lineups[DARK_UID]
    assert isinstance(reading, LineUp) and reading.code == "present"
    assert reading.recipient_uid == DARK_UID and reading.partner_uid == BRIGHT_UID
    assert reading.half_tile_mm == HALF_TILE_MM
    assert reading.half_thickness_mm == THICKNESS_MM / 2.0
    assert set(reading.match_codes.ravel().tolist()) == {MATCHED}
    assert set(reading.slab_codes.tolist()) == {IN_SLAB}
    events = run_ledger.events()
    assert [event.name for event in events] == [
        "pairs.consumed_by.lineup",
        "squint_stack.consumed_by.lineup",
        "lineup.produced",
    ]
    assert dict(events[0].counts) == {"planes": 2, "paired": 1}
    assert dict(events[1].counts) == {"recipient": 1, "partner": 1}


def test_read_lineups_reads_no_stack_for_a_plane_that_is_not_paired() -> None:
    # MUST NOT: line a solitary or surplus plane up with anything, or record a read of a stack
    # it never read; the pairs record itself is still read, and said so.
    dark, bright = _dark_and_bright()
    solo = _series(SOLO_UID, "1", "Axial")
    stacks = _stacks(dark, bright, solo)
    surplus = AcquisitionPair("Coronal", (BRIGHT_UID, DARK_UID), (), (), "surplus")
    with recording() as run_ledger:
        lineups = read_lineups(
            _pairs(surplus, SOLO),
            stacks,
            _geometries(dark, bright, solo),
            _thicknesses(dark, bright, solo),
            HALF_TILE_MM,
        )
    assert lineups == {}
    events = run_ledger.events()
    assert [event.name for event in events] == ["pairs.consumed_by.lineup"]
    assert dict(events[0].counts) == {"planes": 2, "paired": 0}
    # A study with no series: the pairs record is handed over, read, and nothing is lined up.
    with recording() as run_ledger:
        assert (
            read_lineups(
                AcquisitionPairs(STUDY_UID, (), "predecessor_empty"), {}, {}, {}, 1.0
            )
            == {}
        )
    assert dict(run_ledger.events()[0].counts) == {"planes": 0, "paired": 0}


def test_read_lineups_refuses_a_paired_plane_that_contradicts_the_stacks_by_name() -> (
    None
):
    dark, bright = _dark_and_bright()
    with pytest.raises(ValueError, match="paired_series_without_a_stack"):
        read_lineups(
            _pairs(PAIRED),
            _stacks(dark),
            _geometries(dark, bright),
            _thicknesses(dark, bright),
            HALF_TILE_MM,
        )
    with pytest.raises(ValueError, match="paired_plane_without_both_flavours"):
        read_lineups(
            _pairs(AcquisitionPair("Coronal", (), (DARK_UID,), (), "paired")),
            _stacks(dark, bright),
            _geometries(dark, bright),
            _thicknesses(dark, bright),
            HALF_TILE_MM,
        )


def test_read_lineups_hands_on_a_missing_geometry_and_thickness_as_the_silences_they_are() -> (
    None
):
    dark, bright = _dark_and_bright()
    stacks = _stacks(dark, bright)
    # No geometry entry for either series: every tile is the silence `line_up` names.
    reading = read_lineups(_pairs(PAIRED), stacks, {}, {}, HALF_TILE_MM)[DARK_UID]
    assert reading.code == "present" and "geometry" in reading.why
    assert set(reading.match_codes.ravel().tolist()) == {UNAVAILABLE}
    # A thickness nobody gave is a refusal per slice, never a slab of zero; the tiles still match.
    reading = read_lineups(
        _pairs(PAIRED), stacks, _geometries(dark, bright), {}, HALF_TILE_MM
    )[DARK_UID]
    assert math.isnan(reading.half_thickness_mm)
    assert set(reading.slab_codes.tolist()) == {INVALID_SLAB}
    assert set(reading.match_codes.ravel().tolist()) == {MATCHED}


# --- the writer --------------------------------------------------------------------------------


def test_the_recipients_record_carries_the_lineup_and_the_partners_carries_none(
    tmp_path: Path,
) -> None:
    _write_paired_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID, _request())
    by_uid = {run.series_uid: run for run in result.series}
    record, arrays = series_record(STUDY_UID, by_uid[DARK_UID], "reference")
    saved = record["lineup"]
    assert saved["code"] == "present"
    assert saved["recipient_uid"] == DARK_UID and saved["partner_uid"] == BRIGHT_UID
    assert saved["half_tile_mm"] == HALF_TILE_MM
    assert saved["half_thickness_mm"] == THICKNESS_MM / 2.0
    assert saved["normal_angle_deg"] == 0.0
    assert saved["match_code_names"] == list(MATCH_CODES)
    assert saved["slab_code_names"] == list(SLAB_CODES)
    assert saved["slices"] == SLICES and saved["tiles_rc"] == [4, 4]
    assert saved["arrays"] == {name: f"lineup_{name}" for name in LINEUP_ARRAYS}
    reading = by_uid[DARK_UID].lineup
    assert reading is not None
    for name in LINEUP_ARRAYS:
        np.testing.assert_array_equal(arrays[f"lineup_{name}"], getattr(reading, name))
    descriptors = array_table(arrays)
    assert descriptors["lineup_partner_tile"]["shape"] == (SLICES, 4, 4, 2)
    assert descriptors["lineup_partner_tile"]["dtype"] == "<i8"
    assert descriptors["lineup_match_codes"]["dtype"] == "|u1"
    assert descriptors["lineup_distance_mm"]["dtype"] == "<f8"
    assert json.loads(json.dumps(saved, allow_nan=False)) == saved
    # The partner's record carries no line-up key and no line-up array: its silence.
    partner, partner_arrays = series_record(STUDY_UID, by_uid[BRIGHT_UID], "reference")
    assert "lineup" not in partner
    assert not [name for name in partner_arrays if name.startswith("lineup_")]


def test_a_bar_the_stage_could_not_read_is_saved_as_none_never_zero() -> None:
    dark, bright = _dark_and_bright()
    reading = read_lineups(
        _pairs(PAIRED),
        _stacks(dark, bright),
        _geometries(dark, bright),
        {},
        HALF_TILE_MM,
    )[DARK_UID]
    record, arrays = lineup_record(reading)
    assert record["half_thickness_mm"] is None
    assert json.loads(json.dumps(record, allow_nan=False)) == record
    assert set(arrays) == {f"lineup_{name}" for name in LINEUP_ARRAYS}


# --- the adapter -------------------------------------------------------------------------------


def test_the_standing_names_a_lined_up_slice_and_every_silence_apart() -> None:
    assert slice_standing("present", 1, 3, 1, 3) == "lined_up"
    assert slice_standing("present", 0, 3, 2, 3) == "lined_up"
    assert slice_standing(None, 1, 3, 1, 3) == "lineup_not_saved"
    assert slice_standing("lesion", 1, 3, 1, 3) == "lineup_code_unknown"
    assert slice_standing("no_stacked_volume", 0, 0, -1, None) == "lineup_absent"
    assert slice_standing("geometry_unreadable", 0, 0, -1, 3) == "lineup_absent"
    assert slice_standing("present", 3, 3, 1, 3) == "slice_outside_lineup"
    assert slice_standing("present", -1, 3, 1, 3) == "slice_outside_lineup"
    assert slice_standing("present", 1, 3, -1, 3) == "partner_slice_absent"
    assert slice_standing("present", 1, 3, 1, None) == "partner_stack_not_saved"
    assert slice_standing("present", 1, 3, 3, 3) == "partner_slice_outside_stack"
    assert slice_standing("present", 1, 3, 0, 0) == "partner_slice_outside_stack"


def test_the_standing_is_total_and_never_lined_up_without_a_held_partner_slice() -> (
    None
):
    # MUST NOT: draw a slice from a line-up that is not present, from an index outside it, or
    # against a partner slice the partner's saved stack does not hold; and every answer is one
    # of the declared standings, so a picture never carries a word from nowhere.
    for code in ("present", "no_stacked_volume", "geometry_unreadable", None, "", 1):
        for index in (0, 1, 2, 3, -1, True, 1.0, None, "1"):
            for partner_slice in (-1, 0, 2, 3, True, None, 1.5):
                for partner_slices in (None, 0, 3, True, "3"):
                    standing = slice_standing(
                        code, index, 3, partner_slice, partner_slices
                    )
                    assert standing in SLICE_STANDINGS, (code, index, partner_slice)
                    if standing == "lined_up":
                        assert code == "present"
                        assert type(index) is int and 0 <= index < 3
                        assert (
                            type(partner_slice) is int and type(partner_slices) is int
                        )
                        assert 0 <= partner_slice < partner_slices


def test_the_adapter_selects_the_slice_places_the_partners_centres_and_alters_nothing() -> (
    None
):
    dark, bright = _dark_and_bright()
    stacks = _stacks(dark, bright)
    reading = line_up(
        stacks[DARK_UID],
        stacks[BRIGHT_UID],
        dark.geometry,
        bright.geometry,
        HALF_TILE_MM,
        THICKNESS_MM / 2.0,
    )
    panels = lineup_panels(
        reading.code,
        reading.why,
        reading.recipient_uid,
        reading.partner_uid,
        reading.half_tile_mm,
        reading.half_thickness_mm,
        reading.normal_angle_deg,
        reading.partner_slice,
        reading.slab_codes,
        reading.partner_tile,
        reading.distance_mm,
        reading.match_codes,
        stacks[DARK_UID].bounds_rc,
        stacks[BRIGHT_UID].centres_lps,
        _frame_at(dark, 1),
        1,
    )
    assert panels.code == "present" and panels.slices == SLICES
    assert panels.recipient_uid == DARK_UID and panels.partner_uid == BRIGHT_UID
    assert panels.half_tile_mm == HALF_TILE_MM
    assert panels.half_thickness_mm == THICKNESS_MM / 2.0
    assert panels.normal_angle_deg == 0.0
    np.testing.assert_array_equal(panels.partner_slice, reading.partner_slice)
    np.testing.assert_array_equal(panels.slab_codes, reading.slab_codes)
    at = panels.at
    assert at.standing == "lined_up" and at.index == 1
    assert at.partner_index == 1 and at.slab_code == "in_slab"
    assert at.match_codes is not None and at.partner_tile is not None
    assert at.distance_mm is not None
    np.testing.assert_array_equal(at.match_codes, reading.match_codes[1])
    np.testing.assert_array_equal(at.partner_tile, reading.partner_tile[1])
    np.testing.assert_array_equal(at.distance_mm, reading.distance_mm[1])
    assert at.match_codes.dtype == np.uint8 and at.partner_tile.dtype == np.int64
    assert at.distance_mm.dtype == np.float64
    # The recipient's centres are the midpoints of its saved bounds: tile (0, 0) holds pixel
    # rows and columns 0..3 and is centred at 1.5; tile (2, 3) at (9.5, 13.5).
    assert at.recipient_centres_rc is not None
    assert at.recipient_centres_rc.shape == (4, 4, 2)
    np.testing.assert_allclose(at.recipient_centres_rc[0, 0], (1.5, 1.5))
    np.testing.assert_allclose(at.recipient_centres_rc[2, 3], (9.5, 13.5))
    # The partner's centres, a quarter of a millimetre along the column direction, land half a
    # pixel to the right of the recipient's in its own frame, and nowhere else.
    assert at.partner_centres_rc is not None
    assert at.partner_centres_rc.shape == (4, 4, 2)
    np.testing.assert_allclose(
        at.partner_centres_rc,
        at.recipient_centres_rc + np.array([0.0, SCOOTCH_MM / SPACING_MM]),
        atol=1e-9,
    )
    # The two arrays the adapter owns are frozen; the saved arrays are handed on as they came.
    assert not at.recipient_centres_rc.flags.writeable
    assert not at.partner_centres_rc.flags.writeable
    # Another slice: its own partner slice, its own saved values.
    other = lineup_panels(
        reading.code,
        reading.why,
        reading.recipient_uid,
        reading.partner_uid,
        reading.half_tile_mm,
        reading.half_thickness_mm,
        reading.normal_angle_deg,
        reading.partner_slice,
        reading.slab_codes,
        reading.partner_tile,
        reading.distance_mm,
        reading.match_codes,
        stacks[DARK_UID].bounds_rc,
        stacks[BRIGHT_UID].centres_lps,
        _frame_at(dark, 2),
        2,
    )
    assert other.at.partner_index == 2
    np.testing.assert_array_equal(other.at.match_codes, reading.match_codes[2])


def test_the_adapter_keeps_every_absence_absent_and_places_nothing_it_cannot() -> None:
    nothing = lineup_panels(
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
        None,
        None,
        None,
        1,
    )
    assert nothing.code is None and nothing.slices == 0
    assert nothing.partner_slice is None and nothing.slab_codes is None
    at = nothing.at
    assert at.standing == "lineup_not_saved" and at.index == 1
    assert at.partner_index is None and at.slab_code is None
    assert at.recipient_centres_rc is None and at.partner_centres_rc is None
    assert at.partner_tile is None and at.distance_mm is None and at.match_codes is None
    dark, bright = _dark_and_bright()
    stacks = _stacks(dark, bright)
    frame = _frame_at(dark, 1)
    # MUST NOT: place a partner centre where the stage named no partner slice (a geometry it did
    # not have); the recipient's own grid still stands, and the saved tiles are handed on as the
    # silences they are.
    silent = line_up(
        stacks[DARK_UID], stacks[BRIGHT_UID], None, bright.geometry, HALF_TILE_MM, 0.5
    )
    panels = lineup_panels(
        silent.code,
        silent.why,
        silent.recipient_uid,
        silent.partner_uid,
        silent.half_tile_mm,
        silent.half_thickness_mm,
        silent.normal_angle_deg,
        silent.partner_slice,
        silent.slab_codes,
        silent.partner_tile,
        silent.distance_mm,
        silent.match_codes,
        stacks[DARK_UID].bounds_rc,
        stacks[BRIGHT_UID].centres_lps,
        frame,
        1,
    )
    assert panels.at.standing == "partner_slice_absent"
    assert panels.at.partner_centres_rc is None and panels.at.partner_index is None
    assert panels.at.recipient_centres_rc is not None
    assert panels.at.match_codes is not None
    assert set(panels.at.match_codes.ravel().tolist()) == {UNAVAILABLE}
    reading = line_up(
        stacks[DARK_UID],
        stacks[BRIGHT_UID],
        dark.geometry,
        bright.geometry,
        HALF_TILE_MM,
        0.5,
    )
    # Without the partner's saved stack: named, never placed.
    panels = lineup_panels(
        reading.code,
        reading.why,
        reading.recipient_uid,
        reading.partner_uid,
        reading.half_tile_mm,
        reading.half_thickness_mm,
        reading.normal_angle_deg,
        reading.partner_slice,
        reading.slab_codes,
        reading.partner_tile,
        reading.distance_mm,
        reading.match_codes,
        stacks[DARK_UID].bounds_rc,
        None,
        frame,
        1,
    )
    assert panels.at.standing == "partner_stack_not_saved"
    assert panels.at.partner_centres_rc is None
    # Without the recipient's frame: lined up, with nothing placed.
    panels = lineup_panels(
        reading.code,
        reading.why,
        reading.recipient_uid,
        reading.partner_uid,
        reading.half_tile_mm,
        reading.half_thickness_mm,
        reading.normal_angle_deg,
        reading.partner_slice,
        reading.slab_codes,
        reading.partner_tile,
        reading.distance_mm,
        reading.match_codes,
        stacks[DARK_UID].bounds_rc,
        stacks[BRIGHT_UID].centres_lps,
        None,
        1,
    )
    assert panels.at.standing == "lined_up" and panels.at.partner_centres_rc is None
    # A slice the line-up does not hold.
    panels = lineup_panels(
        reading.code,
        reading.why,
        reading.recipient_uid,
        reading.partner_uid,
        reading.half_tile_mm,
        reading.half_thickness_mm,
        reading.normal_angle_deg,
        reading.partner_slice,
        reading.slab_codes,
        reading.partner_tile,
        reading.distance_mm,
        reading.match_codes,
        stacks[DARK_UID].bounds_rc,
        stacks[BRIGHT_UID].centres_lps,
        frame,
        SLICES,
    )
    assert panels.at.standing == "slice_outside_lineup"
    assert panels.at.match_codes is None and panels.at.partner_centres_rc is None
    # A line-up the stage did not make, over a partner that has no stack.
    from dataclasses import replace

    absent = read_squint_stack(replace(bright, volume=None), TILE_MM)
    gone = line_up(stacks[DARK_UID], absent, dark.geometry, bright.geometry, 1.0, 0.5)
    panels = lineup_panels(
        gone.code,
        gone.why,
        gone.recipient_uid,
        gone.partner_uid,
        gone.half_tile_mm,
        gone.half_thickness_mm,
        gone.normal_angle_deg,
        gone.partner_slice,
        gone.slab_codes,
        gone.partner_tile,
        gone.distance_mm,
        gone.match_codes,
        stacks[DARK_UID].bounds_rc,
        stacks[BRIGHT_UID].centres_lps,
        frame,
        1,
    )
    assert panels.code == "no_stacked_volume" and panels.slices == SLICES
    assert panels.at.standing == "lineup_absent"


def test_the_scootch_segments_join_each_tile_to_the_partner_tile_the_stage_named() -> (
    None
):
    recipient = np.array([[[1.5, 1.5], [1.5, 5.5]]])
    partner_tile = np.array([[[0, 1], [-1, -1]]])
    partner = np.array([[[1.5, 1.0], [1.5, 2.0]]])
    segments = lineup_frames.scootch_segments(recipient, partner_tile, partner)
    # Tile (0, 0) is joined to partner tile (0, 1); tile (0, 1), which the stage named no
    # partner for, has no segment. Each point is (x, y) with a pixel's centre at +0.5.
    assert segments.shape == (1, 2, 2)
    np.testing.assert_allclose(segments[0], [[2.0, 2.0], [2.5, 2.0]])
    # MUST NOT: draw a segment to a partner centre that is NaN, or from one.
    partner[0, 1] = np.nan
    assert lineup_frames.scootch_segments(recipient, partner_tile, partner).shape == (
        0,
        2,
        2,
    )
    assert lineup_frames.scootch_segments(
        recipient, np.full((1, 2, 2), -1), partner
    ).shape == (0, 2, 2)


# --- the drawer's reader -----------------------------------------------------------------------


def test_the_reader_reconstitutes_a_writer_shaped_record_and_finds_the_partner(
    tmp_path: Path,
) -> None:
    recipient, partner = _saved_pair(tmp_path)
    records = lineup_frames.receipt_records(tmp_path)
    assert lineup_frames.partner_record(records, recipient) == partner
    assert lineup_frames.partner_record(records, partner) is None
    drawing = lineup_frames.saved_lineup(tmp_path, recipient, partner)
    assert drawing.artifact == tmp_path / f"{DARK_UID}.npz"
    panels = drawing.panels
    assert panels.code == "present" and panels.slices == SLICES
    assert panels.partner_uid == BRIGHT_UID
    assert panels.at.standing == "lined_up"
    assert panels.at.partner_index == 1 and panels.at.slab_code == "in_slab"
    assert panels.at.partner_centres_rc is not None
    assert panels.at.partner_centres_rc.shape == (4, 4, 2)
    assert drawing.bounds_rc is not None and drawing.bounds_rc.shape == (4, 4, 4)
    assert drawing.plane is not None and drawing.plane.dtype == np.uint16
    # The partner's own record carries no line-up: the reader hands on that silence.
    quiet = lineup_frames.saved_lineup(tmp_path, partner, None)
    assert quiet.panels.code is None
    assert quiet.panels.at.standing == "lineup_not_saved"
    assert quiet.bounds_rc is None and quiet.plane is None


def test_the_reader_names_what_the_run_does_not_hold(tmp_path: Path) -> None:
    recipient, _ = _saved_pair(tmp_path)
    # No partner record handed over: the partner's stack is not in this run.
    drawing = lineup_frames.saved_lineup(tmp_path, recipient, None)
    assert drawing.panels.at.standing == "partner_stack_not_saved"
    assert drawing.panels.at.partner_centres_rc is None
    assert lineup_frames.receipt_records(tmp_path / "nowhere") == []
    # No plane and no frame saved: lined up, but nothing to lay it over or place it with.
    recipient, partner = _saved_pair(tmp_path, with_plane=False, with_frame=False)
    drawing = lineup_frames.saved_lineup(tmp_path, recipient, partner)
    assert drawing.panels.at.standing == "lined_up"
    assert drawing.plane is None and drawing.panels.at.partner_centres_rc is None


def test_the_reader_refuses_a_saved_record_that_disagrees_with_the_writer(
    tmp_path: Path,
) -> None:
    # MUST NOT: draw a tampered array, a code the stage does not say, a line-up that names
    # another recipient, a slice count that is not the arrays', a vocabulary that is not the
    # stage's, a bar that is not a number, a line-up saved without its stack, or a stack whose
    # grid is not the line-up's; each is named and raised.
    recipient, partner = _saved_pair(tmp_path)

    def copy() -> dict:
        return json.loads(json.dumps(recipient))

    tampered = copy()
    tampered["arrays"]["lineup_match_codes"]["digest"] = "changed"
    with pytest.raises(ValueError, match="saved_array_digest_mismatch"):
        lineup_frames.saved_lineup(tmp_path, tampered, partner)
    named = copy()
    named["lineup"]["code"] = "lesion"
    with pytest.raises(ValueError, match="saved_lineup_code_unknown"):
        lineup_frames.saved_lineup(tmp_path, named, partner)
    other = copy()
    other["lineup"]["recipient_uid"] = "another"
    with pytest.raises(ValueError, match="saved_lineup_recipient_mismatch"):
        lineup_frames.saved_lineup(tmp_path, other, partner)
    counted = copy()
    counted["lineup"]["slices"] = 2
    with pytest.raises(ValueError, match="saved_lineup_slices_mismatch"):
        lineup_frames.saved_lineup(tmp_path, counted, partner)
    worded = copy()
    worded["lineup"]["match_code_names"] = ["matched"]
    with pytest.raises(ValueError, match="saved_lineup_vocabulary_mismatch"):
        lineup_frames.saved_lineup(tmp_path, worded, partner)
    barred = copy()
    barred["lineup"]["half_tile_mm"] = "one"
    with pytest.raises(ValueError, match="saved_lineup_not_a_number"):
        lineup_frames.saved_lineup(tmp_path, barred, partner)
    shaped = copy()
    shaped["lineup"] = "yes"
    with pytest.raises(ValueError, match="saved_lineup_not_a_record"):
        lineup_frames.saved_lineup(tmp_path, shaped, partner)
    alone = copy()
    del alone["squint_stack"]
    with pytest.raises(ValueError, match="saved_lineup_without_a_recipient_stack"):
        lineup_frames.saved_lineup(tmp_path, alone, partner)
    # A partner whose saved stack was tampered is refused through the stack drawer's reader.
    tampered_partner = json.loads(json.dumps(partner))
    tampered_partner["arrays"]["squint_stack_centres_lps"]["digest"] = "changed"
    with pytest.raises(ValueError, match="saved_array_digest_mismatch"):
        lineup_frames.saved_lineup(tmp_path, recipient, tampered_partner)
    # A recipient stack squinted at another tile than the line-up: the grids disagree.
    recipient, partner = _saved_pair(tmp_path, recipient_stack_tile_mm=4.0)
    with pytest.raises(ValueError, match="saved_lineup_grid_mismatch"):
        lineup_frames.saved_lineup(tmp_path, recipient, partner)


# --- the drawer --------------------------------------------------------------------------------


def test_an_out_directory_outside_data_is_an_argument_refusal(tmp_path: Path) -> None:
    _saved_pair(tmp_path)
    with pytest.raises(ArgumentRefusal, match="private data directory"):
        lineup_frames.draw(tmp_path, STUDY_UID, tmp_path / "out")


def test_the_drawer_writes_one_picture_with_its_manifest(tmp_path: Path) -> None:
    """The impure edge, end to end: one image under data/, bound to the receipt."""
    _saved_pair(tmp_path)
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = lineup_frames.draw(tmp_path, STUDY_UID, out)
        assert (out / "series.png").exists()
        assert (out / "manifest.json").exists()
        assert manifest["image"] == "series.png"
        assert manifest["standings"] == list(SLICE_STANDINGS)
        assert manifest["silence"] is None
        (series,) = manifest["series"]
        assert series["series_uid"] == DARK_UID and series["partner_uid"] == BRIGHT_UID
        assert series["standing"] == "lined_up" and series["drawn"] == "lined_up"
        assert series["slices_panel"] == "drawn"
        assert series["partner_index"] == 1 and series["slab_code"] == "in_slab"
        assert series["match_counts"] == {
            "matched": 16,
            "beyond_half_tile": 0,
            "partner_unavailable": 0,
            "invalid_measurement": 0,
        }
        assert series["slab_counts"]["in_slab"] == SLICES
        assert series["lineup"]["tiles_rc"] == [4, 4]
        assert "Coronal paired" in manifest["pairs_caption"]
        # The note names every silence the adapter can name, the seventh included.
        assert len(SLICE_STANDINGS) == 8 and "seven silences" in manifest["note"]
        assert "a saved code the stage does not say" in manifest["note"]
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_a_study_with_no_paired_plane_draws_its_silence_in_words(
    tmp_path: Path,
) -> None:
    _, partner = _saved_pair(tmp_path)
    receipt = {
        "records": [partner],
        "studies": [{"study_uid": STUDY_UID, "pairs": pairs_record(_pairs(SOLO))}],
    }
    (tmp_path / "receipt.json").write_text(json.dumps(receipt, allow_nan=False))
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = lineup_frames.draw(tmp_path, STUDY_UID, out)
        assert (out / "series.png").exists()
        assert manifest["series"] == []
        assert manifest["silence"] is not None
        assert "no plane is paired" in manifest["silence"]
        assert "Axial solitary" in manifest["silence"]
    finally:
        shutil.rmtree(out, ignore_errors=True)


# --- the view sheet ----------------------------------------------------------------------------


def test_the_sheet_draws_the_lineup_on_the_recipient_next_to_the_squint_stack(
    tmp_path: Path,
) -> None:
    recipient, partner = _saved_pair(tmp_path)
    _, panels = view_frames.view_panels(
        tmp_path, recipient, _loaded(tmp_path, recipient)
    )
    by_reading = {(p.stage, p.reading): p for p in panels}
    panel = by_reading[("field", "line-up")]
    assert (panel.status, panel.code) == ("saved", "present")
    assert panel.paint is not None
    assert panel.arrays == (
        "lineup_match_codes",
        "lineup_partner_tile",
        "lineup_partner_slice",
        "lineup_slab_codes",
    )
    readings = [p.reading for p in panels]
    assert readings.index("squint stack") + 1 == readings.index("line-up")
    assert readings.index("line-up") < readings.index("structural reading")
    # The partner's sheet carries the silence: its record saved no line-up.
    _, panels = view_frames.view_panels(tmp_path, partner, _loaded(tmp_path, partner))
    panel = {(p.stage, p.reading): p for p in panels}[("field", "line-up")]
    assert (panel.status, panel.paint) == ("not_saved", None)


def test_the_sheet_names_a_slice_the_lineup_cannot_show(tmp_path: Path) -> None:
    recipient, _ = _saved_pair(tmp_path)
    outside = json.loads(json.dumps(recipient))
    outside["slice_index"] = 9
    _, panels = view_frames.view_panels(tmp_path, outside, _loaded(tmp_path, outside))
    panel = {(p.stage, p.reading): p for p in panels}[("field", "line-up")]
    assert (panel.status, panel.code, panel.paint) == ("silent", "present", None)
    assert panel.why.startswith("slice_outside_lineup")
    # Without the receipt beside the record the partner's stack cannot be found: named, never
    # drawn as a grid with no partner on it.
    (tmp_path / "receipt.json").unlink()
    _, panels = view_frames.view_panels(
        tmp_path, recipient, _loaded(tmp_path, recipient)
    )
    panel = {(p.stage, p.reading): p for p in panels}[("field", "line-up")]
    assert (panel.status, panel.paint) == ("silent", None)
    assert panel.why.startswith("partner_stack_not_saved")


def test_the_sheet_refuses_a_lineup_that_covers_another_plane(tmp_path: Path) -> None:
    # MUST NOT: lay a 16 x 16 line-up's tiles over a 4 x 4 plane.
    recipient, _ = _saved_pair(tmp_path)
    with pytest.raises(ValueError, match="saved_lineup_covers_another_plane"):
        view_frames.lineup_panel(
            np.arange(16, dtype=np.uint16).reshape(4, 4), tmp_path, recipient
        )


def test_the_sheet_words_a_bar_the_stage_could_not_read_instead_of_formatting_it(
    tmp_path: Path,
) -> None:
    recipient, _ = _saved_pair(tmp_path)
    plane = _loaded(tmp_path, recipient)["acquired_plane"]
    panel = view_frames.lineup_panel(plane, tmp_path, recipient)
    assert panel.status == "saved" and panel.paint is not None
    figure, axis = plt.subplots()
    try:
        assert panel.paint(axis) == "drawn"
        # The sheet sets every panel's title at the left.
        assert "match bar 1 mm" in axis.get_title(loc="left").replace("\n", " ")
    finally:
        plt.close(figure)
    # MUST NOT: format a bar the writer saved as None (a reading the stage could not make,
    # which the reader hands on as None); it is worded as the drawer words it, and the panel
    # is still drawn.
    unread = json.loads(json.dumps(recipient))
    unread["lineup"]["half_tile_mm"] = None
    panel = view_frames.lineup_panel(plane, tmp_path, unread)
    assert panel.status == "saved" and panel.paint is not None
    figure, axis = plt.subplots()
    try:
        assert panel.paint(axis) == "drawn"
        assert "match bar not read" in axis.get_title(loc="left").replace("\n", " ")
    finally:
        plt.close(figure)


def test_the_sheet_is_drawn_with_the_lineup_panel_on_the_recipient(
    tmp_path: Path,
) -> None:
    _saved_pair(tmp_path)
    out = PROJECT / "data" / "pictures" / "_pytest" / uuid.uuid4().hex
    try:
        manifest = view_frames.draw(tmp_path, STUDY_UID, out)
        views = {view["series_uid"]: view for view in manifest["views"]}
        recipient = next(
            p for p in views[DARK_UID]["panels"] if p["reading"] == "line-up"
        )
        assert recipient["drawn"] == "drawn"
        partner = next(
            p for p in views[BRIGHT_UID]["panels"] if p["reading"] == "line-up"
        )
        assert partner["drawn"] == "not_saved"
        assert "lineup_frames" in manifest["reused_drawers_sha256"]
    finally:
        shutil.rmtree(out, ignore_errors=True)


def test_the_picture_module_is_the_adapter_the_sheet_and_drawer_read() -> None:
    assert lineup_frames.pictures is pictures
    assert view_frames.lineup_frames is lineup_frames
    assert ("collapse", "lineup", "lineup_frames") in all_frames.DRAWINGS
    module = importlib.import_module("workbench.render.lineup_frames")
    assert module.draw is lineup_frames.draw
