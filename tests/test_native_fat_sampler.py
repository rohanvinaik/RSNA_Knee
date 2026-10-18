from types import SimpleNamespace
from typing import Any, cast

import numpy as np

from scripts import run_interiors as run


def test_native_fat_opposed_sample_at_calibration_boundary_is_compatible(monkeypatch):
    class Frame:
        def to_patient(self, rc):
            return np.column_stack((rc, np.zeros(len(rc))))

    frame = Frame()
    target_series = SimpleNamespace(
        volume=np.zeros((1, 1, 1), dtype=np.float64),
    )
    own = cast(
        run.Measured,
        SimpleNamespace(
            record={"series_uid": "target", "view": ["axial", "x", "y"]},
            series=target_series,
            arrays={},
        ),
    )
    source = cast(
        run.Measured,
        SimpleNamespace(
            record={"series_uid": "opposed"},
            series=SimpleNamespace(
                volume=np.zeros((1, 1, 1), dtype=np.float64),
                slice_thickness_mm=(1.0,),
            ),
        ),
    )
    candidate = np.ones((1, 1), dtype=bool)
    row: dict[str, Any] = {
        "slice": 0,
        "candidate": candidate,
        "frame": frame,
        "raw": np.zeros((1, 1), dtype=np.float64),
    }
    candidates: dict[str, list[dict[str, Any]]] = {"hoffa_fat_pad": [row]}
    threshold = 12.5
    samples = SimpleNamespace(
        signal=np.asarray([threshold]),
        selected_z=np.asarray([0], dtype=np.int32),
        native_rc=np.asarray([[0, 0]], dtype=np.int32),
        signed_distance_mm=np.asarray([0.0]),
        status=np.asarray(["valid"]),
    )
    monkeypatch.setattr(run, "plane_frame", lambda *_args: frame)
    monkeypatch.setattr(run, "sample_native_points", lambda *_args, **_kwargs: samples)
    monkeypatch.setattr(run, "reads", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(run, "handed", lambda *_args, **_kwargs: None)

    run.native_fat_opposed_samples(
        own,
        candidates,
        {
            "opposed": {
                "status": "calibrated",
                "threshold": threshold,
                "series_uid": "opposed",
            }
        },
        [source],
    )

    assert row["fat_classes"]["positive_without_known_negative"][0, 0]
    assert row["fat_classes"]["known"][0, 0]
    assert not row["fat_classes"]["negative"][0, 0]


def test_native_fat_non_fs_target_refuses_before_reading_volume():
    class Series:
        row = SimpleNamespace(fluid_sensitive=1, fat_suppression=0)

        @property
        def volume(self):
            raise AssertionError("unsupported sequence must be rejected first")

    own = cast(
        run.Measured,
        SimpleNamespace(
            record={"series_uid": "non-fs", "view": ["axial", "x", "y"]},
            series=Series(),
            arrays={},
        ),
    )

    assert run.native_fat_pad_candidates(own, {}, None, None) == {}
    found, unresolved = run.native_fat_pad_observations(own, {}, {}, "study")

    assert found == []
    assert {item.code for item in unresolved} == {"unsupported_sequence"}
    assert len(unresolved) == 4


def test_native_fat_profiles_skip_volume_when_no_source_is_selected():
    class Series:
        row = SimpleNamespace(fluid_sensitive=1, fat_suppression=1)

        @property
        def volume(self):
            raise AssertionError("unavailable sources must be rejected first")

    own = cast(
        run.Measured,
        SimpleNamespace(
            record={"series_uid": "no-source", "view": ["Axial", "1", "1"]},
            series=Series(),
            arrays={},
        ),
    )

    assert run.native_fat_pad_candidates(own, {}, None, None) == {}


def test_native_fat_calibration_accepts_native_partner_agreement_not_laid_only(
    monkeypatch,
):
    femur_code = run.OBJECT_CODES["femur"]

    def measured(uid: str, code: str):
        objects = np.zeros((2, 2), dtype=np.int16)
        objects[0, 0] = femur_code
        return cast(
            run.Measured,
            SimpleNamespace(
                record={
                    "series_uid": uid,
                    "view": ["Sagittal", "0", "0"],
                    "slice_index": 3,
                    "assignments": {"codes": {"femur": code}},
                },
                series=SimpleNamespace(row=SimpleNamespace(fat_suppression=0)),
                arrays={
                    "a1_objects": objects,
                    "acquired_plane": np.full((2, 2), 20.0),
                },
                assignment=object(),
                frame=object(),
            ),
        )

    agreed = measured("agreed", "agreed_with_its_partner")
    laid = measured("laid", "laid")
    monkeypatch.setattr(run, "field_names", lambda _assignment: ())
    monkeypatch.setattr(run, "reads", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(run, "handed", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        run,
        "measures_of",
        lambda *_args, **_kwargs: SimpleNamespace(light=lambda _mask: 10.0),
    )

    calibrations = run.native_fat_opposed_calibrations([agreed, laid])

    assert calibrations["agreed"]["status"] == "calibrated"
    assert calibrations["agreed"]["source_code"] == "agreed_with_its_partner"
    assert calibrations["laid"]["status"] == "native_femur_calibration_unavailable"
