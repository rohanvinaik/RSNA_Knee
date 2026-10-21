from __future__ import annotations

import json
import sys
from types import ModuleType, SimpleNamespace

import numpy as np

import knee.diagnosis.squint_anatomy_locator as anatomy_locator
import knee.diagnosis.squint_locator as locator

VIEW = {"orientation": "axial", "fluid_sensitive": "yes", "fat_suppression": "no"}
BANK = 'squint/v1/view=["axial","yes","no"]/metric=signal_median/direction=overview/scale=10mm'
PROCEDURE = "knee.squint-profile/scan-tercile-v1"


def _fixture(windows: list[tuple[int, ...]], monkeypatch):
    stack = SimpleNamespace(
        code="present",
        median=np.ones((2, 2, 2), dtype=np.float64),
        maximum=np.ones((2, 2, 2), dtype=np.float64),
        coverage=np.ones((2, 2, 2), dtype=np.float64),
        centres_lps=np.stack(
            [
                np.stack(
                    [
                        np.stack(
                            [np.array([z * 10.0, r * 10.0, c * 10.0]) for c in range(2)]
                        )
                        for r in range(2)
                    ]
                )
                for z in range(2)
            ]
        ),
        tile_mm=10.0,
    )
    codes = np.array([[[-1, 1], [0, 0]], [[1, 1], [0, -1]]], dtype=np.int8)
    series = {
        "series_uid": "current-series",
        "view": VIEW,
        "stack": stack,
        "metric_codes": {"signal_median": codes},
    }
    helper = ModuleType("knee.diagnosis.squint_anatomical_priors")
    helper_calls: list[dict] = []

    def anatomical_windows(actual_series, subject, **kwargs):
        helper_calls.append({"subject": subject, **kwargs})
        return {
            "status": "proposed",
            "windows": list(windows),
            "provenance": {"prior": "test-fixture", "subject": subject},
        }

    helper.anatomical_windows = anatomical_windows
    monkeypatch.setitem(sys.modules, helper.__name__, helper)
    profile = {
        "schema": "knee.squint-profile/v1",
        "subject": "femur",
        "banks": {BANK: [1, 0, 0]},
        "source": {"procedure": PROCEDURE, "view": VIEW},
    }
    memory = {
        "objects": ["femur"],
        "cases": [
            {
                "case_id": "case-femur",
                "study_uid": "other-study",
                "subject": "femur",
                "condition_calls": {},
                "profile": profile,
                "regions": [{"view": VIEW, "extent_source": "retained_object_support"}],
            }
        ],
    }
    return series, memory, helper_calls


def _patch_exact(monkeypatch, calls: list[tuple[int, ...]]):
    def profile_window(series, window, *, subject):
        calls.append(tuple(window))
        selected = series["metric_codes"]["signal_median"][
            window[0] : window[1], window[2] : window[3], window[4] : window[5]
        ]
        counts = [int(np.count_nonzero(selected == code)) for code in (-1, 0, 1)]
        return {
            "schema": "knee.squint-profile/v1",
            "subject": subject,
            "banks": {BANK: counts},
            "source": {"procedure": PROCEDURE, "view": VIEW, "window": list(window)},
        }

    writer = sys.modules.get("knee.diagnosis.squint_profiles")
    if writer is None:
        import knee.diagnosis.squint_profiles as writer
    monkeypatch.setattr(writer, "profile_window", profile_window, raising=False)
    monkeypatch.setattr(
        writer,
        "merge_profiles",
        lambda profiles, *, subject: profiles[0],
        raising=False,
    )
    monkeypatch.setattr(
        anatomy_locator,
        "object_geometry",
        lambda *args: {"reference": {"status": "partial", "point_lps": None}},
    )
    return profile_window


def test_public_locator_scores_finite_atlas_windows_before_exact_profiles(monkeypatch):
    first = (0, 1, 0, 1, 0, 1)
    second = (1, 2, 0, 1, 0, 1)
    series, memory, helper_calls = _fixture([first, second], monkeypatch)
    calls: list[tuple[int, ...]] = []
    _patch_exact(monkeypatch, calls)

    result = locator.locate_objects(
        {"study_uid": "current-study", "knee_side": None, "series": [series]}, memory
    )

    located = result["objects"]["femur"]
    assert result["evidence"]["candidate_generation"] == "finite_anatomy_first"
    assert helper_calls[0]["knee_side"] is None
    assert calls == [first]
    assert located["status"] == "proposal"
    assert located["regions"][0]["window"] == first
    assert (
        located["evidence"]["proposal_sources"][0]["provenance"]["prior"]
        == "test-fixture"
    )
    finalists = next(iter(located["evidence"]["coarse_finalists"].values()))
    assert finalists["candidate_count"] == 1
    assert finalists["candidates"][0]["window"] == list(first)
    costs = next(iter(located["evidence"]["candidate_costs_by_view"].values()))
    assert costs["windows_proposed"] == 2
    assert costs["windows_scored"] == 2
    assert costs["full_profiles_materialized"] == 1
    assert costs["proposal_sources"][0]["series_uid"] == "current-series"
    assert costs["relative_scope_check"] == "direct_finite_candidate_scope_check"
    assert located["evidence"]["location_scope_codes"] == {"geometry_unavailable": 2}


def test_coarse_tie_set_is_kept_but_not_expanded_past_refinement_budget(monkeypatch):
    windows = [
        (z, z + 1, r, r + 1, c, c + 1)
        for z in range(2)
        for r in range(2)
        for c in range(2)
    ]
    # Duplicate-free over-budget finite proposals require more than the 2x2x2 grid,
    # so extend the stack grid while retaining a compact fixture.
    series, memory, _helper_calls = _fixture(windows[:2], monkeypatch)
    stack = series["stack"]
    stack.median = np.ones((18, 1, 1), dtype=np.float64)
    stack.maximum = np.ones((18, 1, 1), dtype=np.float64)
    stack.coverage = np.ones((18, 1, 1), dtype=np.float64)
    stack.centres_lps = np.array([[[[float(z), 0.0, 0.0]]] for z in range(18)])
    series["metric_codes"]["signal_median"] = np.zeros((18, 1, 1), dtype=np.int8)
    many = [(z, z + 1, 0, 1, 0, 1) for z in range(17)]
    monkeypatch.setattr(
        sys.modules["knee.diagnosis.squint_anatomical_priors"],
        "anatomical_windows",
        lambda *_a, **_k: {
            "status": "proposed",
            "windows": many,
            "provenance": {"test": True},
        },
    )
    calls: list[tuple[int, ...]] = []
    _patch_exact(monkeypatch, calls)
    monkeypatch.setattr(locator, "_MAX_EXACT_REFINEMENTS_PER_VIEW", 4)

    result = locator.locate_objects(
        {"study_uid": "current-study", "series": [series]}, memory
    )

    located = result["objects"]["femur"]
    assert calls == []
    assert located["status"] == "unresolved_candidate_tie"
    tie = next(iter(located["evidence"]["coarse_ties"].values()))
    assert tie["status"] == "unresolved_refinement_budget_exceeded"
    assert tie["candidate_count"] == 17
    assert len(tie["candidates"]) == 17
    finalists = next(iter(located["evidence"]["coarse_finalists"].values()))
    assert finalists["candidate_count"] == 17
    assert [row["window"] for row in finalists["candidates"]] == [
        list(window) for window in many
    ]
    costs = next(iter(located["evidence"]["candidate_costs_by_view"].values()))
    assert costs["windows_proposed"] == 17
    assert costs["windows_scored"] == 17
    assert costs["full_profiles_materialized"] == 0


def test_missing_anatomical_helper_is_named_and_does_not_sweep_grid(monkeypatch):
    first = (0, 1, 0, 1, 0, 1)
    series, memory, _helper_calls = _fixture([first], monkeypatch)
    missing_helper = ModuleType("knee.diagnosis.squint_anatomical_priors")
    monkeypatch.setitem(sys.modules, missing_helper.__name__, missing_helper)
    calls: list[tuple[int, ...]] = []
    _patch_exact(monkeypatch, calls)

    result = locator.locate_objects(
        {"study_uid": "current-study", "series": [series]}, memory
    )

    located = result["objects"]["femur"]
    assert calls == []
    assert located["status"] == "unresolved_missing_reading"
    assert (
        located["evidence"]["proposal_sources"][0]["reason"]
        == "anatomical_prior_helper_unavailable"
    )


def test_stack_unavailable_uses_existing_cached_profile_route():
    case_profile = {
        "schema": "knee.squint-profile/v1",
        "subject": "femur",
        "banks": {BANK: [1, 0, 0]},
        "source": {"procedure": PROCEDURE},
    }
    memory = {
        "cases": [
            {
                "case_id": "prior",
                "study_uid": "other",
                "subject": "femur",
                "condition_calls": {},
                "profile": case_profile,
            }
        ],
    }
    result = locator.locate_objects(
        {
            "study_uid": "current",
            "series": [
                {
                    "series_uid": "cached",
                    "candidate_profiles": [
                        {"subject": "femur", "profile": case_profile}
                    ],
                }
            ],
        },
        memory,
    )
    assert result["objects"]["femur"]["status"] == "proposal"
    assert (
        locator.resolve_candidate_profile(
            result["objects"]["femur"],
            result["objects"]["femur"]["candidate_profiles"][0]["profile_ref"],
        )
        == case_profile
    )


def test_deferring_the_fine_reading_changes_nothing_on_a_v1_memory(monkeypatch):
    first = (0, 1, 0, 1, 0, 1)
    second = (1, 2, 0, 1, 0, 1)
    series, memory, _helper_calls = _fixture([first, second], monkeypatch)
    calls: list[tuple[int, ...]] = []
    _patch_exact(monkeypatch, calls)
    # Anchors given (none), so no producer runs and no clock is recorded in the result.
    study = {
        "study_uid": "current-study",
        "knee_side": None,
        "series": [series],
        "anchors": {},
    }

    reference = locator.locate_objects(study, memory)
    deferred = locator.locate_objects(study, memory, refine_finalists=False)

    # A v1 memory makes no 2 mm territory reading: its writer ran exactly as before,
    # once per location, and the located result and its evidence are the same.
    assert calls == [first, first]
    assert json.dumps(deferred, sort_keys=True, default=str) == json.dumps(
        reference, sort_keys=True, default=str
    )
    assert "fine_reading" not in deferred["evidence"]


def test_no_series_clears_native_support_retained_from_a_previous_location():
    study = {
        "study_uid": "current-study",
        "series": [],
        anatomy_locator.NATIVE_SUPPORT_RETAINED: [{"subject": "femur"}],
    }

    located = anatomy_locator.locate_anatomy_first(study, {"cases": []})

    assert located["outcome"] == "unresolved_missing_reading"
    assert anatomy_locator.NATIVE_SUPPORT_RETAINED not in study


def test_deferring_the_fine_reading_changes_nothing_on_the_cached_profile_route():
    case_profile = {
        "schema": "knee.squint-profile/v1",
        "subject": "femur",
        "banks": {BANK: [1, 0, 0]},
        "source": {"procedure": PROCEDURE},
    }
    memory = {
        "cases": [
            {
                "case_id": "prior",
                "study_uid": "other",
                "subject": "femur",
                "condition_calls": {},
                "profile": case_profile,
            }
        ],
    }
    study = {
        "study_uid": "current",
        "series": [
            {
                "series_uid": "cached",
                "candidate_profiles": [{"subject": "femur", "profile": case_profile}],
            }
        ],
    }
    reference = locator.locate_objects(study, memory)
    deferred = locator.locate_objects(study, memory, refine_finalists=False)
    assert reference["objects"]["femur"]["status"] == "proposal"
    assert deferred == reference


def test_femur_tibia_separation_is_not_used_as_femoral_breadth(monkeypatch):
    first = (0, 1, 0, 1, 0, 1)
    series, memory, helper_calls = _fixture([first], monkeypatch)
    base_case = memory["cases"][0]
    for subject in ("tibia", "meniscus"):
        case = {
            **base_case,
            "case_id": f"case-{subject}",
            "subject": subject,
            "profile": {
                **base_case["profile"],
                "subject": subject,
                "banks": {BANK: [1, 0, 0]},
            },
        }
        memory["cases"].append(case)
    calls: list[tuple[int, ...]] = []
    _patch_exact(monkeypatch, calls)

    def geometry(subject, _regions, _series_by_uid):
        point = {"tibia": [0.0, 0.0, 100.0]}.get(subject)
        reference = {
            "status": "complete" if point is not None else "partial",
            "point_lps": point,
        }
        planes = {
            "sagittal": {
                "outcome": "selected",
                "normal": [1.0, 0.0, 0.0],
                "offset_mm": 0.0,
                "precision_mm": 2.0,
                "native_plane_identity": f"{subject}-sagittal-native",
            }
        }
        return {"subject": subject, "reference": reference, "planes": planes}

    monkeypatch.setattr(anatomy_locator, "object_geometry", geometry)

    result = locator.locate_objects(
        {"study_uid": "current-study", "series": [series]}, memory
    )

    assert result["objects"]["meniscus"]["status"] == "proposal"
    meniscus_call = next(row for row in helper_calls if row["subject"] == "meniscus")
    assert meniscus_call["knee_scale_mm"] is None
    assert meniscus_call["anchors"]["femur"]["reference"]["status"] == "partial"
    assert meniscus_call["anchors"]["femur"]["reference"]["point_lps"] is None
    assert (
        meniscus_call["anchors"]["femur"]["planes"]["sagittal"]["native_plane_identity"]
        == "femur-sagittal-native"
    )
    assert meniscus_call["anchors"]["tibia"]["reference"]["point_lps"] == [
        0.0,
        0.0,
        100.0,
    ]
    assert (
        result["objects"]["femur"]["evidence"]["spatial_constraints"]["reference"][
            "status"
        ]
        == "partial"
    )
    assert (
        result["objects"]["femur"]["evidence"]["spatial_constraints"]["reference"][
            "point_lps"
        ]
        is None
    )


def test_relative_scope_check_consumes_only_supplied_finite_windows():
    from knee.diagnosis.squint_geometry import window_scope_codes

    stack = SimpleNamespace(
        median=np.ones((2, 1, 1), dtype=np.float64),
        bounds_rc=np.asarray([[[0, 10, 0, 10]]], dtype=np.int64),
    )
    series = {
        "stack": stack,
        "geometry": {
            "position": np.asarray([[0.0, 0.0, 0.0], [0.0, 0.0, 10.0]]),
            "orientation": np.asarray([[1, 0, 0, 0, 1, 0]] * 2, dtype=np.float64),
            "spacing": np.asarray([[1.0, 1.0]] * 2),
        },
    }
    priors = {
        "cases": [
            {
                "status": "available",
                "planes": [
                    {
                        "normal": [0.0, 0.0, 1.0],
                        "offset_mm": 0.0,
                        "precision_mm": 1.0,
                    }
                ],
            }
        ]
    }
    finite_windows = [(0, 1, 0, 1, 0, 1), (1, 2, 0, 1, 0, 1)]

    codes = window_scope_codes(series, finite_windows, priors)

    assert codes == ["eligible", "outside_anatomical_prior"]
