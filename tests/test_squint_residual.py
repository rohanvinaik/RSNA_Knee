"""Small parts read over their own outline (W12): the part's producer on its located slice.

A synthetic coronal knee, written as real DICOM and read through ``read_study_squints``: a femur
and a tibia, each a marrow body inside a one-pixel dark cortex ring, bright cartilage between them
with a white fluid pocket in its middle, and a dark wedge at each end of the joint. The existing
coronal rule (``assign_plane``) names the wedges as the menisci (sided from the header), the
bright layer within 3 mm of each bone as its cartilage and the pocket as joint fluid; the tests
read what the executor makes of them.

The executor is an explicit tool. The dispatcher (``squint_pipeline._bounded_observation``) runs it
only for a request that names the part's native procedure; a generic request, whatever the part,
asks for the paired finer reading. SQUINT_TRAINING_BUILD §10's "always read a small part over its
outline", and the validation gate that kept an outline reading from deciding until each part was
validated, are withdrawn: an outline reading decides like any compatible cheap reading, under its
own origin name.
"""

from __future__ import annotations

import copy
import csv
import dataclasses
import json
import time
from pathlib import Path

import numpy as np
import pytest
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from knee.collapse.physical import PlaneFrame
from knee.diagnosis import squint_pipeline, squint_profiles, squint_residual
from knee.diagnosis.squint_contracts import CONTRACTS
from knee.diagnosis.squint_interfaces import (
    LEG_INSIDE,
    LEG_MAP_SCHEMA,
    LEG_OUTSIDE,
    RESIDUAL_REQUEST_SCHEMA,
    ROLE_OBJECT,
    TERRITORY_PROCEDURE,
    residual_result_code,
)
from knee.diagnosis.squint_profiles import (
    merge_profiles,
    profile_window,
    read_study_squints,
    refine_window,
)
from knee.diagnosis.squint_residual import (
    LENS_PROMINENCE_MM,
    OWN_OUTLINE_REASON,
    PRODUCERS,
    UNAVAILABLE,
    held_readings,
    holds_reading,
    own_outline,
    producer_for,
    producer_table,
    run_residual,
)

LABELS = (
    "ACL",
    "MCL",
    "Medial Meniscus",
    "Lateral Meniscus",
    "Medial OA",
    "Lateral OA",
    "PF OA",
    "Effusion",
    "Synovitis",
    "Baker's",
    "Contusion",
    "Fracture",
)
CORONAL = (1.0, 0.0, 0.0, 0.0, 0.0, -1.0)  # columns toward patient left, rows inferior
SAGITTAL = (0.0, 1.0, 0.0, 0.0, 0.0, -1.0)  # columns toward posterior, rows inferior
SPLIT = 50.0
MEDIAL_WINDOW = [1, 2, 7, 9, 11, 13]  # slice 1, the joint's tile rows, the medial end
LATERAL_WINDOW = [1, 2, 7, 9, 3, 5]
CENTRAL_WINDOW = [1, 2, 7, 9, 6, 10]
Window = tuple[int, int, int, int, int, int]
MEDIAL_TILES: Window = (1, 2, 7, 9, 11, 13)
CENTRAL_TILES: Window = (1, 2, 7, 9, 6, 10)
# A wedge 14 columns wide with the cortex rows above and below it: a 14 x 14 block whose
# four corners the rule's 2 mm opening (a cross at 1 mm pitch) removes; 8 wide, 14 x 8.
WIDE_WEDGE = 14 * 14 - 4
NARROW_WEDGE = 14 * 8 - 4
# Cartilage: the bright joint places within 3 mm of a bone, two rows above the tibia's and
# two below the femur's marrow, over the 60 columns between the wedges.
CARTILAGE = 2 * 60
FLUID = 4 * 20  # the white pocket in the middle of the joint


def _plane(*, medial=(110, 124), lateral=(36, 50)) -> np.ndarray:
    rows, cols = np.indices((160, 160))
    texture = (rows + 3 * cols) % 7
    plane = (100 + texture).astype(np.uint16)  # the leg's soft tissue
    air = (cols < 20) | (cols >= 140)
    plane[air] = (2 + texture[air] % 5).astype(np.uint16)
    for top in (10, 86):  # femur above, tibia below, each inside a 1-px dark cortex
        plane[top : top + 64, 35:125] = 3
        inner = (slice(top + 1, top + 63), slice(36, 124))
        plane[inner] = 150 + texture[inner]
    plane[74:86, 36:124] = 240 + texture[74:86, 36:124]  # cartilage, above 1.5x marrow
    plane[78:82, 70:90] = 700  # joint fluid, above 4x marrow
    plane[74:86, lateral[0] : lateral[1]] = 3  # the dark wedge at each end
    plane[74:86, medial[0] : medial[1]] = 3
    return plane


def _write_slice(path, study_uid, series_uid, pixels, z, *, orientation, laterality):
    meta = FileMetaDataset()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.MediaStorageSOPClassUID = generate_uid()
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.ImplementationClassUID = generate_uid()
    dataset = FileDataset(str(path), {}, file_meta=meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    dataset.StudyInstanceUID = study_uid
    dataset.SeriesInstanceUID = series_uid
    dataset.Modality = "MR"
    dataset.Rows, dataset.Columns = pixels.shape
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 16
    dataset.BitsStored = 16
    dataset.HighBit = 15
    dataset.PixelRepresentation = 0
    normal = np.cross(np.asarray(orientation[:3]), np.asarray(orientation[3:]))
    dataset.ImagePositionPatient = list(
        np.asarray((-80.0, -80.0, 80.0)) * (1 - np.abs(normal)) + 3.0 * z * normal
    )
    dataset.ImageOrientationPatient = list(orientation)
    dataset.PixelSpacing = [1.0, 1.0]
    dataset.SliceThickness = 3.0
    if laterality is not None:
        dataset.Laterality = laterality
    dataset.PixelData = np.asarray(pixels, dtype="<u2").tobytes()
    dataset.save_as(path, enforce_file_format=True, little_endian=True)


def _study(
    tmp_path: Path,
    *,
    laterality="R",
    fat_suppression="1",
    planes=None,
    sagittal=False,
) -> dict:
    """A one-study root: a coronal series (and optionally a sagittal one), read and leg-mapped."""
    uid = generate_uid()
    rows = []
    specs = [("Coronal", CORONAL, fat_suppression)]
    if sagittal:
        specs.append(("Sagittal", SAGITTAL, "1"))
    for name, orientation, fs in specs:
        series_uid = generate_uid()
        directory = tmp_path / "train_series" / uid / series_uid
        directory.mkdir(parents=True)
        stack = planes or [_plane(), _plane(), _plane()]
        for z, pixels in enumerate(stack):
            _write_slice(
                directory / f"{z:03d}.dcm",
                uid,
                series_uid,
                pixels,
                z,
                orientation=orientation,
                laterality=laterality,
            )
        rows.append((uid, series_uid, "1", fs, name))
    with (tmp_path / "train.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(("StudyInstanceUID", "Report", *LABELS))
        writer.writerow((uid, "", *([""] * len(LABELS))))
    header = (
        "StudyInstanceUID",
        "SeriesInstanceUID",
        "Fluid_Sensitive",
        "Fat_Suppression",
        "Anatomical_Plane",
    )
    with (tmp_path / "train_series.csv").open(
        "w", newline="", encoding="utf-8"
    ) as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)
    for name, columns in (
        ("test.csv", ("StudyInstanceUID",)),
        ("test_series.csv", header),
    ):
        with (tmp_path / name).open("w", newline="", encoding="utf-8") as stream:
            csv.writer(stream).writerow(columns)
    study = read_study_squints(tmp_path, uid, io_workers=1, tile_mm=10.0)
    study["leg_maps"] = {
        row["series_uid"]: _leg_map(uid, row) for row in study["series"]
    }
    return study


def _leg_map(study_uid: str, series: dict) -> dict:
    """The leg the synthetic image holds: every tile inside but the air's four columns."""
    shape = series["stack"].median.shape
    codes = np.full(shape, LEG_INSIDE, dtype=np.int8)
    codes[:, :, [0, 1, 14, 15]] = LEG_OUTSIDE
    share = np.where(codes == LEG_INSIDE, 1.0, 0.0).astype(np.float32)
    codes.flags.writeable = False
    share.flags.writeable = False
    return {
        "schema": LEG_MAP_SCHEMA,
        "study_uid": study_uid,
        "series_uid": series["series_uid"],
        "tile_mm": 10.0,
        "codes": codes,
        "leg_share": share,
        "rule": "test:constructed",
        "provenance": {
            "background_split": {"code": "measured", "value": SPLIT, "source": "test"}
        },
    }


def _coronal(study: dict) -> dict:
    return next(s for s in study["series"] if s["view"]["orientation"] == "Coronal")


def _sagittal(study: dict) -> dict:
    return next(s for s in study["series"] if s["view"]["orientation"] == "Sagittal")


def _request(subject: str, series_uid: str, window=MEDIAL_WINDOW, lens=None) -> dict:
    producer = producer_for(subject)
    return {
        "schema": RESIDUAL_REQUEST_SCHEMA,
        "question_id": "Medial Meniscus",
        "subject": subject,
        "series_uid": series_uid,
        "reason": OWN_OUTLINE_REASON,
        "lens": lens or (producer.lens if producer else "no_producer"),
        "tile_window": list(window),
    }


def _located(series: dict, *windows, profile=None) -> dict:
    return {
        "status": "proposal",
        "profile": profile,
        "regions": [
            {"series_uid": series["series_uid"], "window": list(window)}
            for window in windows
        ],
    }


@pytest.fixture
def naming_calls(monkeypatch):
    """Count the producer's naming calls without changing them."""
    calls = []
    real = squint_residual.assign_plane

    def counted(plane, *args, **kwargs):
        calls.append(plane.copy())
        return real(plane, *args, **kwargs)

    monkeypatch.setattr(squint_residual, "assign_plane", counted)
    return calls


def _object_bank(profile: dict, metric="signal_median", scale="10mm") -> list[int]:
    name = next(
        name
        for name in profile["banks"]
        if "/role=object/" in name
        and f"/metric={metric}/" in name
        and "/direction=overview/" in name
        and name.endswith(f"/scale={scale}")
    )
    return profile["banks"][name]


# ---------------------------------------------------------------------------
# the producer runs only on the located slice and writes banks over its support
# ---------------------------------------------------------------------------


def test_meniscus_request_runs_its_producer_once_and_writes_over_the_found_support(
    tmp_path, naming_calls
):
    study = _study(tmp_path)
    series = _coronal(study)
    objects: dict = {}
    before = copy.deepcopy(objects)

    result = run_residual(
        _request("medial_meniscus", series["series_uid"]), study, objects
    )

    assert residual_result_code(result) == "valid"
    assert result["code"] == "measured"
    assert objects == before  # run_residual reads objects, never writes them
    assert len(naming_calls) == 1  # one naming, of the located slice only
    np.testing.assert_array_equal(naming_calls[0], series["native_series"].volume[1])
    support = result["territory"]["native_support"]
    assert support["slices"] == [1]
    # The medial wedge, rows 74-85 x cols 110-123, with the cortex rows 73 and 86 that
    # touch it: the rule's 2 mm opening keeps that 14 x 14 block without its four corners.
    assert support["offset_rc"] == [73, 110]
    assert support["mask"].shape == (1, 14, 14)
    assert int(support["mask"].sum()) == WIDE_WEDGE
    assert not support["mask"][0, [0, 0, -1, -1], [0, -1, 0, -1]].any()
    territory = result["territory"]
    assert territory["origin"] == "residual_native_support"
    # The object tiles are the tiles the support covers; one context ring around them.
    assert int(np.count_nonzero(territory["roles"] == ROLE_OBJECT)) == 4
    assert result["profile"]["source"]["procedure"] == TERRITORY_PROCEDURE
    assert sum(_object_bank(result["profile"])) == 4  # 10 mm: four object tiles
    assert sum(_object_bank(result["profile"], scale="2mm")) == 8 * 7  # 2 mm tiles
    assert {item["scale_mm"] for item in result["readings"]} == {10.0, 2.0}
    assert result["support_in_request_window_share"] == 1.0
    assert result["cost"]["native_slices_read"] == 1
    assert result["cost"]["native_slices_shared"] == 0
    assert (
        result["cost"]["background_split_source"] == "leg_map_recorded_background_split"
    )
    json.dumps(squint_residual.residual_record(result))


def test_same_window_different_support_changes_the_banks(tmp_path):
    wide = _study(tmp_path / "wide")
    narrow = _study(
        tmp_path / "narrow",
        planes=[_plane(medial=(116, 124)) for _ in range(3)],
    )
    a = run_residual(
        _request("medial_meniscus", _coronal(wide)["series_uid"]), wide, {}
    )
    b = run_residual(
        _request("medial_meniscus", _coronal(narrow)["series_uid"]), narrow, {}
    )
    assert a["code"] == b["code"] == "measured"
    assert a["territory"]["tile_window"] == b["territory"]["tile_window"]
    assert int(a["territory"]["native_support"]["mask"].sum()) == WIDE_WEDGE
    assert int(b["territory"]["native_support"]["mask"].sum()) == NARROW_WEDGE
    assert sum(_object_bank(a["profile"], scale="2mm")) == 8 * 7
    assert sum(_object_bank(b["profile"], scale="2mm")) == 8 * 4


def test_other_slices_never_reach_the_reading_but_the_located_slice_does(tmp_path):
    study = _study(tmp_path)
    series = _coronal(study)
    request = _request("medial_meniscus", series["series_uid"])
    base = run_residual(request, study, {})

    native = series["native_series"]
    volume = np.array(native.volume, copy=True)
    volume[0] = 255
    volume[2] = 7  # other slices rewritten wholesale
    series["native_series"] = dataclasses.replace(native, volume=volume)
    study.pop("_residual_slice_namings")  # a fresh naming, from the rewritten volume
    others = run_residual(request, study, {})
    assert others["support"] == base["support"]
    assert others["profile"]["banks"] == base["profile"]["banks"]

    volume = np.array(native.volume, copy=True)
    volume[1, 74:86, 110:116] = 150  # the located slice's wedge, partly filled in
    series["native_series"] = dataclasses.replace(native, volume=volume)
    study.pop("_residual_slice_namings")
    changed = run_residual(request, study, {})
    assert changed["code"] == "measured"
    assert changed["support"]["support_count"] == NARROW_WEDGE
    assert changed["support"]["mask_sha256"] != base["support"]["mask_sha256"]


def test_each_covered_part_is_its_own_label_of_the_same_naming(tmp_path, naming_calls):
    study = _study(tmp_path)
    uid = _coronal(study)["series_uid"]
    found = {
        subject: run_residual(_request(subject, uid, window), study, {})
        for subject, window in (
            ("medial_meniscus", MEDIAL_WINDOW),
            ("lateral_meniscus", LATERAL_WINDOW),
            ("femoral_cartilage", CENTRAL_WINDOW),
            ("tibial_cartilage", CENTRAL_WINDOW),
            ("joint_fluid", CENTRAL_WINDOW),
        )
    }
    assert {subject: item["code"] for subject, item in found.items()} == dict.fromkeys(
        found, "measured"
    )
    assert len(naming_calls) == 1  # one naming of slice 1 served all five parts
    shared = [item["cost"]["native_slices_shared"] for item in found.values()]
    assert shared == [0, 1, 1, 1, 1]
    lateral = found["lateral_meniscus"]["territory"]["native_support"]
    assert lateral["offset_rc"] == [73, 36]
    assert int(lateral["mask"].sum()) == WIDE_WEDGE
    femoral = found["femoral_cartilage"]["territory"]["native_support"]
    tibial = found["tibial_cartilage"]["territory"]["native_support"]
    fluid = found["joint_fluid"]["territory"]["native_support"]
    assert (femoral["offset_rc"], int(femoral["mask"].sum())) == ([74, 50], CARTILAGE)
    assert (tibial["offset_rc"], int(tibial["mask"].sum())) == ([84, 50], CARTILAGE)
    assert (fluid["offset_rc"], int(fluid["mask"].sum())) == ([78, 70], FLUID)
    # Equal shapes give equal mask digests (the two wedges, the two cartilage layers); the
    # reading's address places each one, so all five readings are distinct.
    digests = {item["support"]["mask_sha256"] for item in found.values()}
    assert len(digests) == 3
    addresses = {
        json.dumps(item["readings"][0]["address"], sort_keys=True)
        for item in found.values()
    }
    assert len(addresses) == 5


def test_slice_naming_equals_the_runners_name_plane(tmp_path):
    from scripts import run_interiors

    assert run_interiors.PROMINENCE_MM == LENS_PROMINENCE_MM
    study = _study(tmp_path)
    series = _coronal(study)
    native = series["native_series"]
    geometry = native.geometry
    frame = PlaneFrame.from_dicom(
        geometry.position[1], geometry.orientation[1], geometry.spacing[1]
    )
    with run_interiors.recording(), run_interiors.computing():
        _record, _arrays, runner = run_interiors.name_plane(
            native, 1, native.volume[1], frame, SPLIT, "R", borders=False
        )
    ours, evidence = squint_residual._name_slice(
        native, series["stack"], 1, SPLIT, frame
    )
    np.testing.assert_array_equal(ours.objects, runner.objects)
    assert ours.codes == runner.codes
    for key in ("meniscus", "cartilage", "joint_fluid"):
        assert evidence["codes"][key] == "identified"
    assert evidence["codes"]["meniscus_side"] == "from_the_header"


# ---------------------------------------------------------------------------
# what writes nothing
# ---------------------------------------------------------------------------


def test_part_without_a_producer_is_unavailable_and_writes_nothing(
    tmp_path, naming_calls
):
    study = _study(tmp_path)
    series = _coronal(study)
    objects = {"acl": _located(series, MEDIAL_WINDOW)}
    for subject in ("acl", "pcl", "femur", "not_an_object"):
        result = run_residual(_request(subject, series["series_uid"]), study, objects)
        assert result["code"] == "procedure_unavailable"
        assert "territory" not in result and "profile" not in result
        assert residual_result_code(result) == "valid"
    assert "acl_on_slice" in UNAVAILABLE["acl"]
    before = copy.deepcopy(objects)
    record = own_outline("acl", study, objects)
    assert record["code"] == "procedure_unavailable"
    assert record["reason"] == UNAVAILABLE["acl"]
    assert record["results"] == [] and record["profile_replaced"] is False
    assert objects["acl"]["profile"] == before["acl"]["profile"]
    assert naming_calls == []
    json.dumps(record)


def test_deadline_before_the_run_reads_nothing(tmp_path, naming_calls):
    study = _study(tmp_path)
    series = _coronal(study)
    result = run_residual(
        _request("medial_meniscus", series["series_uid"]),
        study,
        {},
        deadline=time.monotonic() - 1.0,
    )
    assert result["code"] == "deadline_before_residual"
    assert naming_calls == []
    assert "profile" not in result


def test_requested_lens_must_be_the_parts_own_producer(tmp_path, naming_calls):
    study = _study(tmp_path)
    series = _coronal(study)
    result = run_residual(
        _request("medial_meniscus", series["series_uid"], lens="physical_squint"),
        study,
        {},
    )
    assert result["code"] == "procedure_unavailable"
    assert result["reason"] == "request_lens_is_not_this_objects_producer"
    assert naming_calls == []


def test_views_the_definition_does_not_read_are_named_not_run(tmp_path, naming_calls):
    plain = _study(tmp_path / "t1", fat_suppression="0")
    result = run_residual(
        _request("medial_meniscus", _coronal(plain)["series_uid"]), plain, {}
    )
    assert result["code"] == "procedure_unavailable"
    assert "fat_suppressed_coronal" in result["reason"]

    both = _study(tmp_path / "both", sagittal=True)
    result = run_residual(
        _request("medial_meniscus", _sagittal(both)["series_uid"]), both, {}
    )
    assert result["code"] == "procedure_unavailable"
    assert result["reason"].startswith("rule_reads_a_slice_with_side_to_side")
    assert naming_calls == []


def test_unsided_knee_and_missing_wedge_are_named_refusals(tmp_path):
    unsided = _study(tmp_path / "unsided", laterality=None)
    result = run_residual(
        _request("medial_meniscus", _coronal(unsided)["series_uid"]), unsided, {}
    )
    assert result["code"] == "no_compatible_reading"
    assert "meniscus_side=abstain_header_names_no_knee" in result["reason"]

    flat = _study(tmp_path / "flat", planes=[_plane(medial=(124, 124))] * 3)
    result = run_residual(
        _request("medial_meniscus", _coronal(flat)["series_uid"]), flat, {}
    )
    assert result["code"] == "no_compatible_reading"
    assert result["reason"].startswith("medial_meniscus_not_named:")
    assert "profile" not in result


def test_missing_regions_and_malformed_requests_are_named(tmp_path):
    study = _study(tmp_path)
    series = _coronal(study)
    gone = _request("medial_meniscus", "1.2.3.not.in.this.study")
    assert run_residual(gone, study, {})["reason"] == "series_not_in_study"
    outside = _request("medial_meniscus", series["series_uid"], [1, 2, 7, 9, 11, 17])
    assert run_residual(outside, study, {})["reason"] == "window_outside_squint_grid"
    broken = {**_request("medial_meniscus", series["series_uid"]), "tile_window": [1]}
    with pytest.raises(ValueError, match="residual_request_invalid"):
        run_residual(broken, study, {})


def test_leg_maps_are_measured_once_and_shared_when_the_study_lacks_them(tmp_path):
    study = _study(tmp_path)
    series = _coronal(study)
    del study["leg_maps"]
    series["background_split"] = SPLIT  # a split measured elsewhere, supplied
    first = run_residual(_request("medial_meniscus", series["series_uid"]), study, {})
    assert first["cost"]["leg_maps"] == "measured_by_residual_and_kept_for_the_study"
    assert series["series_uid"] in study["leg_maps"]
    second = run_residual(_request("mcl", series["series_uid"]), study, {})
    assert second["cost"]["leg_maps"] == "study_shared"


# ---------------------------------------------------------------------------
# own_outline: once per part per study, replacing the expected-area reading
# ---------------------------------------------------------------------------


def test_own_outline_replaces_the_expected_area_reading_once_per_study(
    tmp_path, naming_calls
):
    study = _study(tmp_path)
    series = _coronal(study)
    expected = profile_window(series, MEDIAL_TILES, subject="medial_meniscus")
    objects = {
        "medial_meniscus": _located(
            series, MEDIAL_WINDOW, profile=copy.deepcopy(expected)
        )
    }
    located = objects["medial_meniscus"]
    assert expected["banks"]
    # Neither reading is gated on an outline: each is a compatible cheap reading that decides
    # at its own scope (the validation gate of VALIDATED_OUTLINE_PARTS is withdrawn).
    assert squint_pipeline._decision_scope("medial_meniscus", expected) == "decide"

    record = own_outline(
        "medial_meniscus", study, objects, question_id="Medial Meniscus"
    )
    assert record["code"] == "measured"
    assert record["profile_replaced"] is True
    assert located["expected_area_profile"] == expected  # kept beside, not lost
    assert located["profile"]["source"]["procedure"] == TERRITORY_PROCEDURE
    assert located["profile"]["source"]["readings"] == held_readings(located["profile"])
    assert squint_pipeline._decision_scope("medial_meniscus", located["profile"]) == (
        "decide"
    )
    # Names stay: the outline is residual native support, never relabelled a teacher's.
    assert squint_pipeline._profile_origins(located["profile"]) == {
        "residual_native_support"
    }
    assert squint_pipeline._profile_origins(expected) == set()
    assert record["cost"]["native_slices_read"] == 1
    assert record["cost"]["seconds"] > 0
    json.dumps(record)
    json.dumps(objects)

    replaced = copy.deepcopy(located["profile"])
    again = own_outline("medial_meniscus", study, objects)
    assert again["code"] == "already_measured" and again["repeat"] is True
    assert again["cost"]["native_slices_read"] == 0
    assert located["profile"] == replaced  # nothing written, no doubled counts
    assert len(naming_calls) == 1  # and nothing read again
    # The same reading asked for directly is already held.
    direct = run_residual(
        _request("medial_meniscus", series["series_uid"]), study, objects
    )
    assert direct["code"] == "already_measured"
    assert len(naming_calls) == 1


def test_own_outline_reads_each_located_region_and_names_each_outcome(tmp_path):
    study = _study(tmp_path, sagittal=True)
    coronal, sagittal = _coronal(study), _sagittal(study)
    located = {
        "status": "proposal",
        "profile": None,
        "regions": [
            {"series_uid": sagittal["series_uid"], "window": MEDIAL_WINDOW},
            {"series_uid": coronal["series_uid"], "window": MEDIAL_WINDOW},
            {"series_uid": coronal["series_uid"], "window": [1, 2, 6, 9, 10, 13]},
            {"series_uid": coronal["series_uid"], "window": [2, 3, 7, 9, 11, 13]},
            {"series_uid": coronal["series_uid"], "window": "not a window"},
        ],
    }
    objects = {"medial_meniscus": located}
    record = own_outline("medial_meniscus", study, objects)
    assert [item["code"] for item in record["results"]] == [
        "procedure_unavailable",
        "measured",
        "already_measured",  # same producer, series and slice: not read again
        "measured",  # another slice: another reading of other places
        "object_region_unavailable",
    ]
    assert record["code"] == "measured"
    assert record["cost"]["native_slices_read"] == 2
    profile = located["profile"]
    assert isinstance(profile, dict)
    assert len(held_readings(profile)) == 4  # two slices, two scales each
    assert sum(_object_bank(profile)) == 2 * 4
    json.dumps(record)


def test_own_outline_without_a_measured_region_keeps_the_expected_reading(tmp_path):
    study = _study(tmp_path, laterality=None)
    series = _coronal(study)
    expected = profile_window(series, MEDIAL_TILES, subject="medial_meniscus")
    objects = {"medial_meniscus": _located(series, MEDIAL_WINDOW, profile=expected)}
    record = own_outline("medial_meniscus", study, objects)
    assert record["code"] == "no_compatible_reading"
    assert record["profile_replaced"] is False
    assert objects["medial_meniscus"]["profile"] is expected
    assert "expected_area_profile" not in objects["medial_meniscus"]
    unlocated = own_outline(
        "lateral_meniscus", study, {"lateral_meniscus": {"regions": []}}
    )
    assert (unlocated["code"], unlocated["reason"]) == (
        "object_region_unavailable",
        "no_located_region",
    )


def test_holds_reading_knows_the_teacher_pair_of_coarse_and_fine_readings(tmp_path):
    study = _study(tmp_path)
    series = _coronal(study)
    window: Window = (1, 2, 7, 9, 11, 13)
    # As squint_memory's v1 compiler wrote a region: a 10 mm and a 2 mm reading merged.
    pair = merge_profiles(
        (
            profile_window(series, window, subject="femur"),
            refine_window(series, window, subject="femur", tile_mm=2.0),
        ),
        subject="femur",
    )
    profile = merge_profiles((pair,), subject="femur")
    uid = series["series_uid"]
    assert holds_reading(profile, series_uid=uid, window=window, scale_mm=2.0)
    assert holds_reading(profile, series_uid=uid, window=window, scale_mm=10.0)
    assert not holds_reading(
        profile, series_uid=uid, window=(1, 2, 7, 9, 3, 5), scale_mm=2.0
    )
    assert not holds_reading(profile, series_uid="another", window=window, scale_mm=2.0)
    assert not holds_reading(None, series_uid=uid, window=window, scale_mm=2.0)


# ---------------------------------------------------------------------------
# the consumer hook in squint_pipeline._bounded_observation
#
# The own-outline step is an explicit tool: only a request that names the part's
# native procedure (its ``lens``) runs it. A request that does not name one asks
# for the paired finer reading, whatever the part, and never reads an outline.
# SQUINT_TRAINING_BUILD §10's "always outline a small part" is withdrawn.
# ---------------------------------------------------------------------------


def _lens(subject: str) -> str:
    producer = producer_for(subject)
    assert producer is not None
    return producer.lens


def _named(subject: str, **extra) -> dict:
    """A request that names the part's own native procedure, as a caller must to ask for it."""
    return {
        "object": subject,
        "question": "Medial Meniscus",
        "lens": _lens(subject),
        **extra,
    }


def _boom(*args, **kwargs):
    raise AssertionError("the native own-outline step must not be selected here")


def test_a_request_naming_the_procedure_reads_a_small_part_over_its_own_outline(
    tmp_path, naming_calls
):
    study = _study(tmp_path)
    series = _coronal(study)
    expected = profile_window(series, MEDIAL_TILES, subject="medial_meniscus")
    objects = {"medial_meniscus": _located(series, MEDIAL_WINDOW, profile=expected)}
    attempted: set = set()
    request = _named("medial_meniscus")
    observed = squint_pipeline._bounded_observation(
        request, study, objects, attempted, None
    )
    assert observed["code"] == "measured"
    assert observed["lens"] == request["lens"]
    assert observed["own_outline"]["results"][0]["support"]["support_count"] == (
        WIDE_WEDGE
    )
    assert "medial_meniscus" in attempted
    located = objects["medial_meniscus"]
    assert located["expected_area_profile"] == expected
    # The outline reading decides like any compatible cheap reading, under its own name.
    assert squint_pipeline._decision_scope("medial_meniscus", located["profile"]) == (
        "decide"
    )
    assert squint_pipeline._profile_origins(located["profile"]) == {
        "residual_native_support"
    }
    assert len(naming_calls) == 1
    # Named again, by this or another question, nothing is read again.
    again = squint_pipeline._bounded_observation(
        _named("medial_meniscus", question="Medial OA"), study, objects, attempted, None
    )
    assert again["code"] == "already_measured"
    assert again["own_outline"]["repeat"] is True
    assert len(naming_calls) == 1
    # A generic request after it adds no finer reading over the part's own reading.
    generic = squint_pipeline._bounded_observation(
        {"object": "medial_meniscus", "question": "MCL"},
        study,
        objects,
        attempted,
        None,
    )
    assert generic == {
        "code": "shared_observation_already_available",
        "subject": "medial_meniscus",
    }
    json.dumps(observed)
    json.dumps(objects)


def test_a_generic_request_on_a_small_part_reads_the_paired_finer_lens_not_its_outline(
    tmp_path, naming_calls, monkeypatch
):
    study = _study(tmp_path)
    series = _coronal(study)
    window = MEDIAL_TILES
    monkeypatch.setattr(squint_residual, "own_outline", _boom)
    monkeypatch.setattr(squint_residual, "run_residual", _boom)
    coarse = profile_window(series, window, subject="medial_meniscus")
    expected_pair = merge_profiles(
        (
            coarse,
            refine_window(series, window, subject="medial_meniscus", tile_mm=2.0),
        ),
        subject="medial_meniscus",
    )
    objects = {
        "medial_meniscus": _located(
            series, MEDIAL_WINDOW, profile=copy.deepcopy(coarse)
        )
    }
    observed = squint_pipeline._bounded_observation(
        {"object": "medial_meniscus", "question": "Medial Meniscus"},
        study,
        objects,
        set(),
        None,
    )
    assert observed["code"] == "measured"
    assert observed["lens"] == "physical_squint"
    assert "own_outline" not in observed
    located = objects["medial_meniscus"]
    assert "own_outline" not in located
    assert located["profile"]["banks"] == expected_pair["banks"]
    assert naming_calls == []  # no native slice was named
    assert squint_pipeline._decision_scope("medial_meniscus", located["profile"]) == (
        "decide"
    )


def test_a_named_procedure_for_a_part_without_one_names_what_is_missing(
    tmp_path, naming_calls
):
    study = _study(tmp_path)
    series = _coronal(study)
    expected = profile_window(series, CENTRAL_TILES, subject="acl")
    objects = {"acl": _located(series, CENTRAL_WINDOW, profile=expected)}
    observed = squint_pipeline._bounded_observation(
        {
            "object": "acl",
            "question": "ACL",
            "lens": "knee.objects.assignments.acl_on_slice",
        },
        study,
        objects,
        set(),
        None,
    )
    assert observed["code"] == "procedure_unavailable"
    assert observed["reason"] == UNAVAILABLE["acl"]
    assert objects["acl"]["profile"] is expected  # no box refinement in its place
    assert "own_outline" not in objects["acl"]
    assert naming_calls == []
    json.dumps(observed)


def test_a_generic_request_on_a_part_without_a_native_producer_gets_the_paired_reading(
    tmp_path,
):
    study = _study(tmp_path)
    series = _coronal(study)
    window = CENTRAL_TILES
    coarse = profile_window(series, window, subject="acl")
    expected_pair = merge_profiles(
        (coarse, refine_window(series, window, subject="acl", tile_mm=2.0)),
        subject="acl",
    )
    objects = {"acl": _located(series, CENTRAL_WINDOW, profile=copy.deepcopy(coarse))}
    observed = squint_pipeline._bounded_observation(
        {"object": "acl", "question": "ACL"}, study, objects, set(), None
    )
    assert observed["code"] == "measured"
    assert objects["acl"]["profile"]["banks"] == expected_pair["banks"]


def test_a_named_procedure_that_is_not_the_parts_own_reads_nothing(
    tmp_path, naming_calls
):
    study = _study(tmp_path)
    series = _coronal(study)
    expected = profile_window(series, MEDIAL_TILES, subject="medial_meniscus")
    objects = {"medial_meniscus": _located(series, MEDIAL_WINDOW, profile=expected)}
    attempted: set = set()
    # The six coronal producers share one lens, so another part's coronal lens is this
    # part's own; a procedure the table does not give this part is a different name.
    assert _lens("mcl") == _lens("medial_meniscus")
    other = "knee.objects.assignments.acl_on_slice"
    assert other != _lens("medial_meniscus")
    observed = squint_pipeline._bounded_observation(
        {"object": "medial_meniscus", "lens": other},
        study,
        objects,
        attempted,
        None,
    )
    assert observed["code"] == "procedure_unavailable"
    assert observed["reason"] == "request_lens_is_not_this_objects_producer"
    assert objects["medial_meniscus"]["profile"] is expected
    assert "own_outline" not in objects["medial_meniscus"]
    assert attempted == set()
    assert naming_calls == []


def test_a_named_procedure_after_the_deadline_reads_and_records_nothing(
    tmp_path, naming_calls
):
    study = _study(tmp_path)
    series = _coronal(study)
    expected = profile_window(series, MEDIAL_TILES, subject="medial_meniscus")
    objects = {"medial_meniscus": _located(series, MEDIAL_WINDOW, profile=expected)}
    attempted: set = set()
    observed = squint_pipeline._bounded_observation(
        _named("medial_meniscus"),
        study,
        objects,
        attempted,
        time.monotonic() - 1.0,
    )
    assert observed["code"] == "deadline_before_residual"
    assert "own_outline" not in objects["medial_meniscus"]  # a later call may still run
    assert attempted == set()
    assert naming_calls == []


def test_the_paired_finer_lens_named_explicitly_is_the_generic_reading(
    tmp_path, monkeypatch
):
    study = _study(tmp_path)
    series = _coronal(study)
    monkeypatch.setattr(squint_residual, "own_outline", _boom)
    coarse = profile_window(series, MEDIAL_TILES, subject="femur")
    objects = {"femur": _located(series, MEDIAL_WINDOW, profile=coarse)}
    observed = squint_pipeline._bounded_observation(
        {"object": "femur", "lens": "physical_squint"}, study, objects, set(), None
    )
    assert observed["code"] == "measured"
    assert observed["lens"] == "physical_squint"


def test_a_generic_request_never_doubles_the_pixels_of_a_part_read_over_its_outline(
    tmp_path,
):
    study = _study(tmp_path)
    series = _coronal(study)
    expected = profile_window(series, MEDIAL_TILES, subject="medial_meniscus")
    objects = {"medial_meniscus": _located(series, MEDIAL_WINDOW, profile=expected)}
    own_outline("medial_meniscus", study, objects)
    replaced = copy.deepcopy(objects["medial_meniscus"]["profile"])
    # A caller that holds no record of the earlier step still must not read the expected
    # area's region and add it to a profile whose own outline replaced that area.
    fresh = squint_pipeline._bounded_observation(
        {"object": "medial_meniscus", "question": "MCL"}, study, objects, set(), None
    )
    assert fresh["code"] == "already_measured"
    assert objects["medial_meniscus"]["profile"] == replaced


@pytest.mark.parametrize("subject", ["femur", "medial_meniscus"])
def test_bounded_observation_does_not_double_a_held_fine_reading(
    tmp_path, monkeypatch, subject
):
    study = _study(tmp_path)
    series = _coronal(study)
    window = MEDIAL_TILES
    calls = []
    real_refine = squint_profiles.refine_window

    def counted(*args, **kwargs):
        calls.append(args[1])
        return real_refine(*args, **kwargs)

    monkeypatch.setattr(squint_profiles, "refine_window", counted)
    monkeypatch.setattr(squint_residual, "own_outline", _boom)
    held_pair = merge_profiles(
        (
            profile_window(series, window, subject=subject),
            real_refine(series, window, subject=subject, tile_mm=2.0),
        ),
        subject=subject,
    )
    objects = {subject: _located(series, window, profile=copy.deepcopy(held_pair))}
    attempted: set = set()
    observed = squint_pipeline._bounded_observation(
        {"object": subject, "question": "Medial OA"}, study, objects, attempted, None
    )
    assert observed["code"] == "already_measured"
    assert observed["held_regions"] == [
        {"series_uid": series["series_uid"], "window": list(window)}
    ]
    assert calls == []
    assert objects[subject]["profile"] == held_pair  # the 2 mm counts are not doubled
    assert subject in attempted

    # Without the 2 mm reading held, the finer reading is made and added once.
    coarse_only = profile_window(series, window, subject=subject)
    objects = {subject: _located(series, window, profile=copy.deepcopy(coarse_only))}
    observed = squint_pipeline._bounded_observation(
        {"object": subject, "question": "Medial OA"}, study, objects, set(), None
    )
    assert observed["code"] == "measured"
    assert calls == [window]
    assert objects[subject]["profile"]["banks"] == held_pair["banks"]
    json.dumps(observed)


# ---------------------------------------------------------------------------
# the table
# ---------------------------------------------------------------------------


def test_every_contract_part_has_a_producer_or_a_named_unavailability():
    subjects = {
        subject
        for contract in CONTRACTS
        for subject in (
            *contract.necessary,
            *contract.alternatives,
            *contract.supporting,
        )
    }
    assert subjects <= set(PRODUCERS) | set(UNAVAILABLE)
    assert not set(PRODUCERS) & set(UNAVAILABLE)
    assert set(PRODUCERS) == {
        "medial_meniscus",
        "lateral_meniscus",
        "mcl",
        "femoral_cartilage",
        "tibial_cartilage",
        "joint_fluid",
    }
    # Every small part Rohan named (SQUINT_TRAINING_BUILD §10) is either covered or named
    # unavailable, so a request that names the native procedure for one always gets an answer.
    small_parts = {
        "medial_meniscus",
        "lateral_meniscus",
        "acl",
        "pcl",
        "mcl",
        "femoral_cartilage",
        "tibial_cartilage",
        "patellar_cartilage",
        "trochlear_cartilage",
        "synovium",
        "joint_fluid",
    }
    assert small_parts <= set(PRODUCERS) | set(UNAVAILABLE)
    table = producer_table()
    json.dumps(table)
    assert all(table[name]["status"] == "available" for name in PRODUCERS)
    assert all(
        table[name]["status"] == "procedure_unavailable" and table[name]["reason"]
        for name in UNAVAILABLE
    )
