from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import numpy as np
import pytest

import knee.diagnosis.squint_locator as locator_module
from knee.diagnosis.squint_contracts import combine_condition
from knee.diagnosis.squint_locator import (
    _banks,
    _batch_terms,
    _case_coarse_matrix,
    _case_matrix,
    _coarse_case_scores,
    _coarse_case_scores_batch,
    _coarse_index,
    _coarse_only_projection,
    _location_scope,
    _object_order,
    _terms,
    _window_coarse_batch,
    _window_coarse_counts,
    locate_objects,
    persisted_recall_cache,
    prepare_recall,
    recall_object,
    resolve_candidate_profile,
)


def _profile(*counts: int) -> dict:
    counts = (*counts, 0) if len(counts) == 2 else counts
    return {
        "schema": "knee.squint-profile/v1",
        "subject": "femur",
        "banks": {"axial/light/whole": list(counts)},
        "source": {
            "study": "current",
            "procedure": "knee.squint-profile/scan-tercile-v1",
        },
    }


def _case(case_id: str, study_uid: str, call: int, counts: tuple[int, ...]) -> dict:
    return {
        "case_id": case_id,
        "study_uid": study_uid,
        "subject": "femur",
        "condition_calls": {"acl": call},
        "profile": _profile(*counts),
        "teaching_source": {"kind": "independent_report", "id": case_id},
    }


def _prepared(memory: dict) -> dict:
    memory["prepared_recall"] = prepare_recall(memory)
    return memory


def test_recall_uses_all_cases_and_empirical_opposing_envelope() -> None:
    memory = {
        "source": {"memory_id": "fixed-1"},
        "cases": [
            _case("positive", "study-positive", 1, (4, 0)),
            _case("negative", "study-negative", -1, (3, 1)),
        ],
    }
    prepared = prepare_recall(memory)
    envelope = next(iter(prepared["envelopes"]["femur"]["acl"].values()))
    assert envelope["available"] is True
    assert envelope["independent_comparison_count"] == 1
    assert envelope["calibrated_probability"] is False
    memory["prepared_recall"] = prepared
    result = recall_object(_profile(4, 0), memory, "acl")
    assert result["outcome"] == "present"
    assert {row["case_id"] for row in result["case_terms"]} == {"positive", "negative"}
    assert result["speaking_calls"] == [1]
    assert result["censor_terms"] == []
    assert result["source"]["memory"] == {"memory_id": "fixed-1"}


def test_recall_without_independent_opposing_comparisons_stays_proposal() -> None:
    memory = {"cases": [_case("only", "study-only", 1, (2, 0))]}
    _prepared(memory)
    result = recall_object(_profile(2, 0), memory, "acl")
    assert result["outcome"] == "proposal"
    assert result["envelope_status"] == "unavailable_proposal_only"
    assert result["speaking_calls"] == []
    assert result["case_terms"][0]["reaches_empirical_envelope"] is False


def test_recall_excludes_same_study_and_keeps_conflicting_cases() -> None:
    memory = {
        "cases": [
            _case("same-study", "held-out", 1, (4, 0)),
            _case("positive", "p", 1, (4, 0)),
            _case("negative", "n", -1, (3, 1)),
        ]
    }
    _prepared(memory)
    result = recall_object(_profile(4, 0), memory, "acl", exclude_study_uid="held-out")
    assert "same-study" in result["excluded_case_ids"]
    assert result["outcome"] == "present"
    assert {row["case_id"] for row in result["case_terms"]} == {"positive", "negative"}
    assert result["speaking_calls"] == [1]


def test_persisted_recall_cache_rebuilds_runtime_indexes_without_pairwise_work(
    monkeypatch,
) -> None:
    memory = {
        "source": {"memory_id": "cache-source"},
        "cases": [
            _case("positive", "study-positive", 1, (4, 0)),
            _case("negative", "study-negative", -1, (3, 1)),
        ],
    }
    expected = prepare_recall(memory)
    cache = persisted_recall_cache(memory, expected)

    def forbidden(*args, **kwargs):
        raise AssertionError("cached restore recomputed pairwise envelopes")

    import knee.diagnosis.squint_locator as locator

    monkeypatch.setattr(locator, "_exact_bank_terms", forbidden)
    restored = locator.prepare_recall(memory, cached=cache)
    assert restored["runtime_indexes_rebuilt"] is True
    assert restored["envelopes"] == expected["envelopes"]
    assert restored["case_indices"] == expected["case_indices"]
    assert restored["case_profile_banks"] == expected["case_profile_banks"]
    assert restored["subject_profile_matrices"]["femur"]["values"].tolist() == (
        expected["subject_profile_matrices"]["femur"]["values"].tolist()
    )


def test_persisted_recall_cache_rejects_changed_profile_source() -> None:
    memory = {
        "cases": [
            _case("positive", "study-positive", 1, (4, 0)),
            _case("negative", "study-negative", -1, (3, 1)),
        ]
    }
    cache = persisted_recall_cache(memory, prepare_recall(memory))
    changed = {**memory, "cases": [dict(row) for row in memory["cases"]]}
    changed["cases"][0]["profile"] = _profile(0, 4)
    restored = prepare_recall(changed, cached=cache)
    assert restored["outcome"] == "prepared"
    assert restored.get("runtime_indexes_rebuilt") is not True
    assert restored["source_fingerprint"] != cache["source_fingerprint"]


def test_capacity_projects_cached_opposition_exactly_and_drops_empty_buckets(
    monkeypatch,
):
    from knee.diagnosis import squint_locator

    held = _case("held-positive", "held", 1, (4, 0, 0))
    peer_positive = _case("peer-positive", "peer", 1, (0, 0, 4))
    peer_negative = _case("peer-negative", "peer-negative", -1, (4, 0, 0))
    memory = {
        "source": {"source_id": "source-r"},
        "cases": [held, peer_positive, peer_negative],
        "censors": [
            {"question": "acl", "study_uid": "held"},
            {"question": "acl", "study_uid": "peer"},
        ],
    }
    full = prepare_recall(memory)
    cache = persisted_recall_cache(memory, full)
    filtered = {
        **memory,
        "cases": [peer_positive, peer_negative],
        "censors": [memory["censors"][1]],
    }
    fresh = prepare_recall(filtered)
    with monkeypatch.context() as patcher:
        patcher.setattr(
            squint_locator,
            "_exact_bank_terms",
            lambda *args: (_ for _ in ()).throw(
                AssertionError("capacity projection recomputed pairwise terms")
            ),
        )
        projected = prepare_recall(memory, cached=cache, exclude_study_uid="held")
    assert projected["runtime_indexes_rebuilt"] is True
    assert projected["envelopes"] == fresh["envelopes"]
    assert projected["case_indices"] == fresh["case_indices"]
    assert projected["censor_indices"] == fresh["censor_indices"]
    assert projected["case_profile_banks"] == fresh["case_profile_banks"]
    assert projected["source_fingerprint"] == fresh["source_fingerprint"]
    assert projected["memory_source"] == fresh["memory_source"]
    projected_envelope = next(iter(projected["envelopes"]["femur"]["acl"].values()))
    full_envelope = next(iter(full["envelopes"]["femur"]["acl"].values()))
    assert full_envelope["maximum_squared_cosine"] == {
        "numerator": "256",
        "denominator": "256",
    }
    assert projected_envelope["maximum_squared_cosine"] == {
        "numerator": "0",
        "denominator": "256",
    }
    assert all(
        "held" not in comparison["study_uids"]
        for comparison in projected_envelope["comparisons"]
    )
    for subject, matrix in fresh["subject_profile_matrices"].items():
        np.testing.assert_array_equal(
            projected["subject_profile_matrices"][subject]["values"],
            matrix["values"],
        )

    no_opposition = {
        **memory,
        "cases": [held, peer_positive],
        "censors": [memory["censors"][0]],
    }
    no_opposition_projected = prepare_recall(
        no_opposition,
        cached=persisted_recall_cache(no_opposition, prepare_recall(no_opposition)),
        exclude_study_uid="held",
    )
    no_opposition_fresh = prepare_recall(
        {**no_opposition, "cases": [peer_positive], "censors": []}
    )
    assert no_opposition_projected["envelopes"] == no_opposition_fresh["envelopes"]
    assert not any(
        bucket
        for questions in no_opposition_projected["envelopes"].values()
        for buckets in questions.values()
        for bucket in buckets.values()
    )

    legacy = persisted_recall_cache(memory, full)
    for questions in legacy["preparation"]["envelopes"].values():
        for buckets in questions.values():
            for envelope in buckets.values():
                for comparison in envelope["comparisons"]:
                    comparison.pop("projection_mode")
    calls = []
    original_terms = squint_locator._exact_bank_terms

    def count_terms(*args):
        calls.append(args)
        return original_terms(*args)

    monkeypatch.setattr(squint_locator, "_exact_bank_terms", count_terms)
    legacy_result = prepare_recall(memory, cached=legacy, exclude_study_uid="held")
    assert legacy_result.get("runtime_indexes_rebuilt") is not True
    assert legacy_result["envelopes"] == fresh["envelopes"]
    assert calls


def test_capacity_cache_projection_matches_sequence_calls_and_profileless_rows():
    positive = _case("sequence-positive", "held", 1, (4, 0, 0))
    positive["condition_calls"] = [{"question": "acl", "digit": 1}]
    negative = _case("sequence-negative", "peer", -1, (3, 1, 0))
    negative["condition_calls"] = [{"question": "acl", "digit": -1}]
    duplicate = _case("duplicate-question", "duplicate", 1, (0, 4, 0))
    duplicate["condition_calls"] = [
        {"question": "acl", "digit": 1},
        {"question": "acl", "digit": 1},
    ]
    profileless = {
        "case_id": "profileless-baker",
        "study_uid": "profileless",
        "subject": "femur",
        "condition_calls": [{"question": "baker", "digit": 1}],
    }
    memory = {
        "source": {"source_id": "sequence-cache"},
        "cases": [positive, negative, duplicate, profileless],
        "censors": [
            {"question": "acl", "study_uid": "held"},
            {"question": "baker", "study_uid": "profileless"},
        ],
    }
    full = prepare_recall(memory)
    cache = persisted_recall_cache(memory, full)
    filtered = {
        **memory,
        "cases": [negative, duplicate, profileless],
        "censors": [memory["censors"][1]],
    }
    fresh = prepare_recall(filtered)
    projected = prepare_recall(memory, cached=cache, exclude_study_uid="held")
    assert projected["envelopes"] == fresh["envelopes"]
    assert projected["case_indices"] == fresh["case_indices"]
    assert projected["censor_indices"] == fresh["censor_indices"]
    assert projected["source_fingerprint"] == fresh["source_fingerprint"]
    assert projected["case_indices"]["femur"]["acl"] == [0]
    assert projected["case_indices"]["femur"].get("baker") is None
    assert projected["envelopes"] == {"femur": {"acl": {}}}
    assert projected["censor_indices"]["baker"] == [0]


def test_explicit_censor_vetoes_but_ordinary_negative_does_not() -> None:
    memory = {
        "cases": [
            _case("positive", "p", 1, (4, 0)),
            _case("negative", "n", -1, (3, 1)),
        ],
        "censors": [
            {
                "censor_id": "near-miss",
                "question": "acl",
                "answer": 1,
                "profile": _profile(4, 0),
                "radius_numerator": 1,
                "radius_denominator": 1,
                "source": "explicit-near-miss",
            }
        ],
    }
    _prepared(memory)
    result = recall_object(_profile(4, 0), memory, "acl")
    assert result["vetoed_answers"] == [1]
    assert result["outcome"] == "unresolved_censored"
    assert result["censor_terms"][0]["censor_id"] == "near-miss"


def test_localization_uses_current_study_profiles_and_preserves_unknowns() -> None:
    memory = {
        "objects": ["femur", "tibia"],
        "object_order": ["femur", "tibia"],
        "cases": [_case("prior", "other-study", 1, (4, 0))],
    }
    study = {
        "study_uid": "current",
        "series": [
            {
                "series_uid": "series-current",
                "candidate_profiles": [
                    {
                        "subject": "femur",
                        "window": [0, 1, 0, 1, 0, 1],
                        "profile": _profile(4, 0),
                    }
                ],
            }
        ],
    }
    result = locate_objects(study, memory)
    assert result["objects"]["femur"]["status"] == "proposal"
    assert (
        result["objects"]["femur"]["evidence"]["patient_coordinates_carried"] is False
    )
    assert result["objects"]["tibia"]["status"] == "unresolved_missing_reading"
    assert result["objects"]["tibia"]["profile"] is None


def test_localization_deadline_retains_unsearched_object_as_unknown() -> None:
    memory = {"objects": ["femur"]}
    result = locate_objects(
        {"study_uid": "current", "series": [{"series_uid": "s"}]}, memory, deadline=0
    )
    assert result["objects"]["femur"]["status"] == "unresolved_missing_reading"


def test_locator_does_not_treat_configuration_subjects_as_anatomy() -> None:
    configuration = _profile(4, 0)
    configuration["subject"] = "diagnosis/ACL"
    result = locate_objects(
        {"study_uid": "current", "series": []},
        {
            "objects": ["femur", "diagnosis/ACL"],
            "cases": [
                _case("femur", "source-femur", 1, (4, 0)),
                {
                    **_case("diagnosis-acl", "source-acl", 1, (4, 0)),
                    "subject": "diagnosis/ACL",
                    "profile": configuration,
                },
            ],
        },
    )
    assert set(result["objects"]) == {"femur"}


def test_location_precedents_prefer_native_scope_then_marker_then_legacy() -> None:
    axial = {
        "orientation": "axial",
        "fluid_sensitive": "yes",
        "fat_suppression": "no",
    }
    coronal = {
        "orientation": "coronal",
        "fluid_sensitive": "yes",
        "fat_suppression": "no",
    }

    def scoped(case_id: str, view: dict, extent_source: str | None) -> dict:
        row = _case(case_id, case_id, 1, (4, 0))
        row["regions"] = (
            [{"view": view, "extent_source": extent_source}]
            if extent_source is not None
            else [{"view": view}]
        )
        return row

    cases = [
        scoped("native-axial", axial, "retained_object_support"),
        scoped("marker-axial", axial, "retained_physical_location"),
        scoped("marker-coronal", coronal, "retained_physical_location"),
        scoped("legacy-axial", axial, None),
    ]
    native_cases, native_examples, native_scope = _location_scope(
        cases, "femur", ("axial", "yes", "no")
    )
    assert [case["case_id"] for case in native_cases] == ["native-axial"]
    assert native_examples[0][1]["extent_source"] == "retained_object_support"
    assert native_scope == "native_object_support"

    marker_cases, _marker_examples, marker_scope = _location_scope(
        [cases[1], cases[2]], "femur", ("axial", "yes", "no")
    )
    assert [case["case_id"] for case in marker_cases] == ["marker-axial"]
    assert marker_scope == "retained_physical_location_marker"

    legacy_cases, _legacy_examples, legacy_scope = _location_scope(
        [cases[3]], "femur", ("axial", "yes", "no")
    )
    assert [case["case_id"] for case in legacy_cases] == ["legacy-axial"]
    assert legacy_scope == "legacy_unspecified_scope"


def test_object_order_respects_bone_dependencies_and_declared_order() -> None:
    known = ["fibula", "acl", "patella", "tibia", "femur"]
    priorities = ["patella", "tibia", "fibula", "femur", "acl"]
    ordered = _object_order(
        known,
        priorities,
        {"femur", "tibia", "fibula", "patella"},
    )
    assert ordered == ["tibia", "femur", "patella", "fibula", "acl"]

    default_order = _object_order(known, (), {"femur", "tibia", "fibula", "patella"})
    assert default_order[:2] == ["femur", "tibia"]
    assert set(default_order[2:4]) == {"fibula", "patella"}


def test_locator_scores_native_scope_cases_when_marker_cases_also_exist() -> None:
    view = {
        "orientation": "axial",
        "fluid_sensitive": "yes",
        "fat_suppression": "no",
    }
    native = _case("native", "native-study", 1, (4, 0))
    native["regions"] = [{"view": view, "extent_source": "retained_object_support"}]
    marker = _case("marker", "marker-study", -1, (100, 0))
    marker["regions"] = [{"view": view, "extent_source": "retained_physical_location"}]
    result = locate_objects(
        {
            "study_uid": "current",
            "series": [
                {
                    "series_uid": "current-series",
                    "view": view,
                    "candidate_profiles": [
                        {"subject": "femur", "profile": _profile(4, 0)}
                    ],
                }
            ],
        },
        {"cases": [native, marker]},
    )
    evidence = result["objects"]["femur"]["evidence"]
    assert [row["case_id"] for row in evidence["case_best_candidates"]] == ["native"]
    assert evidence["location_precedent_scopes"][0]["source"] == (
        "native_object_support"
    )


def test_locator_keeps_two_view_anchor_partial_and_projects_case_offset() -> None:
    from knee.diagnosis.squint_geometry import window_scope_code

    orientations = {
        "sagittal": np.asarray([[0, 1, 0, 0, 0, 1]] * 3, dtype=float),
        "coronal": np.asarray([[1, 0, 0, 0, 0, 1]] * 3, dtype=float),
        "axial": np.asarray([[1, 0, 0, 0, 1, 0]] * 3, dtype=float),
    }

    def series(uid: str, orientation: str, normal_axis: int, offset: float) -> dict:
        normal = np.eye(3)[normal_axis]
        stack = SimpleNamespace(
            bounds_rc=np.asarray([[[0, 4, 0, 4]]], dtype=np.int64),
            median=np.zeros((3, 1, 1)),
        )
        return {
            "series_uid": uid,
            "view": {
                "orientation": orientation,
                "fluid_sensitive": "yes",
                "fat_suppression": "no",
            },
            "stack": stack,
            "geometry": {
                "position": np.asarray(
                    [normal * (offset + (index - 1) * 4.0) for index in range(3)]
                ),
                "orientation": orientations[orientation],
                "spacing": np.asarray([[1.0, 1.0]] * 3),
            },
            "candidate_profiles": [],
        }

    def source_view(orientation: str) -> dict:
        return {
            "orientation": orientation,
            "fluid_sensitive": "yes",
            "fat_suppression": "no",
        }

    source_femur = _case("source-femur", "source-study", 1, (4, 0))
    source_femur["regions"] = [
        {
            "source_point_lps": [10.0, 20.0, 30.0],
            "view": source_view(orientation),
            "extent_source": "retained_object_support",
        }
        for orientation in ("sagittal", "coronal")
    ]
    source_acl = _case("source-acl", "source-study", 1, (4, 0))
    source_acl["subject"] = "acl"
    source_acl["regions"] = [
        {
            "source_point_lps": [12.0, 23.0, 35.0],
            "view": source_view("axial"),
            "extent_source": "retained_object_support",
        }
    ]

    current_series = [
        series("femur-sag", "sagittal", 0, 100.0),
        series("femur-cor", "coronal", 1, 200.0),
        series("acl-ax", "axial", 2, 300.0),
    ]
    for current, subject in zip(
        current_series,
        ("femur", "femur", "acl"),
        strict=True,
    ):
        current["candidate_profiles"] = [
            {
                "subject": subject,
                "window": (1, 2, 0, 1, 0, 1),
                "profile": _profile(4, 0),
            }
        ]

    result = locate_objects(
        {"study_uid": "current-study", "series": current_series},
        {
            "objects": ["femur", "acl"],
            "object_order": ["femur", "acl"],
            "cases": [source_femur, source_acl],
        },
    )
    femur_geometry = result["objects"]["femur"]["evidence"]["spatial_constraints"]
    assert femur_geometry["reference"]["status"] == "partial"
    assert femur_geometry["reference"]["point_lps"] is None
    acl_priors = result["objects"]["acl"]["evidence"]["relative_scope_priors"]
    prior = next(
        row for row in acl_priors["cases"] if row.get("case_id") == "source-acl"
    )
    assert len(prior["planes"]) == 2
    assert prior["scale_status"] == "unscaled_millimetres"
    delta = np.asarray([2.0, 3.0, 5.0])
    for plane in prior["planes"]:
        source_plane = plane["source_plane"]
        expected = float(source_plane["offset_mm"]) + float(
            np.asarray(source_plane["normal"]) @ delta
        )
        assert plane["offset_mm"] == expected
    assert all(plane["offset_mm"] != 12.0 for plane in prior["planes"])

    candidate = series("target-near", "axial", 2, 300.0)
    candidate["geometry"]["position"] = np.asarray(
        [[102.0, 203.0, 296.0], [102.0, 203.0, 300.0], [102.0, 203.0, 304.0]]
    )
    assert window_scope_code(candidate, (1, 2, 0, 1, 0, 1), acl_priors) == "eligible"

    outside = series("target-far", "axial", 2, 300.0)
    outside["geometry"]["position"] = np.asarray(
        [[50.0, 60.0, 296.0], [50.0, 60.0, 300.0], [50.0, 60.0, 304.0]]
    )
    assert (
        window_scope_code(outside, (1, 2, 0, 1, 0, 1), acl_priors)
        == "outside_anatomical_prior"
    )
    unavailable = series("target-unavailable", "axial", 2, 300.0)
    unavailable["geometry"] = None
    assert (
        window_scope_code(unavailable, (1, 2, 0, 1, 0, 1), acl_priors)
        == "geometry_unavailable"
    )


def test_recall_prepares_coarse_only_and_full_bank_envelopes() -> None:
    coarse_bank = (
        'squint/v1/view=["axial","yes","no"]/metric=signal_median/'
        "direction=overview/scale=10mm"
    )
    fine_bank = (
        'squint/v1/view=["axial","yes","no"]/metric=signal_median/'
        "direction=overview/scale=2mm"
    )
    cases = []
    for case_id, study_uid, call, coarse, fine in (
        ("coarse-positive", "study-p", 1, [4, 0, 0], [0, 4, 0]),
        ("coarse-negative", "study-n", -1, [3, 1, 0], [0, 3, 1]),
    ):
        cases.append(
            {
                "case_id": case_id,
                "study_uid": study_uid,
                "subject": "femur",
                "condition_calls": {"acl": call},
                "profile": {
                    "schema": "knee.squint-profile/v1",
                    "subject": "femur",
                    "banks": {coarse_bank: coarse, fine_bank: fine},
                    "source": {"procedure": "knee.squint-profile/scan-tercile-v1"},
                },
            }
        )
    prepared = prepare_recall({"cases": cases})
    envelopes = prepared["envelopes"]["femur"]["acl"]
    coarse = next(
        envelope
        for envelope in envelopes.values()
        if "coarse_10mm" in envelope["projection_modes"]
    )
    full = next(
        envelope
        for envelope in envelopes.values()
        if "full" in envelope["projection_modes"]
    )
    assert coarse["banks"] == [coarse_bank]
    assert full["banks"] == [coarse_bank, fine_bank]
    assert coarse["independent_comparison_count"] == 1
    assert full["independent_comparison_count"] == 1


def test_batched_exact_terms_match_public_cosine_with_sparse_and_large_counts() -> None:
    source = {"procedure": "knee.squint-profile/scan-tercile-v1"}
    left = {
        "schema": "knee.squint-profile/v1",
        "subject": "femur",
        "banks": {
            "shared/coarse": [4, 0, 2],
            "shared/fine": [10**30, 10**30 + 1, 0],
            "silent/shared": [0, 0, 0],
            "left/only": [9, 1, 0],
        },
        "source": source,
    }
    right = {
        "schema": "knee.squint-profile/v1",
        "subject": "femur",
        "banks": {
            "shared/coarse": [3, 1, 2],
            "shared/fine": [10**30, 0, 10**30],
            "silent/shared": [0, 0, 0],
            "right/only": [7, 2, 1],
        },
        "source": source,
    }
    expected = _terms(left, right)
    actual = _batch_terms(_banks(left), [_banks(right)])[0]
    assert actual == expected


def test_cached_matrix_promotes_for_large_query_count() -> None:
    source = {"procedure": "knee.squint-profile/scan-tercile-v1"}
    precedent = {
        "schema": "knee.squint-profile/v1",
        "subject": "femur",
        "banks": {"shared": [1, 0, 0]},
        "source": source,
    }
    query = {
        "schema": "knee.squint-profile/v1",
        "subject": "femur",
        "banks": {"shared": [10**30, 0, 0], "query-only": [10**40, 1, 0]},
        "source": source,
    }
    case_banks = _banks(precedent)
    cache = _case_matrix([case_banks])
    assert cache["safe_int64"] is True
    actual = _batch_terms(_banks(query), [case_banks], matrix_cache=cache)[0]
    assert actual == _terms(query, precedent)


def test_empty_coarse_case_scope_has_explicit_zero_rows() -> None:
    rows, mask = _case_coarse_matrix([], ["available-bank"])
    assert rows.shape == (0, 3)
    assert mask.shape == (0, 1)
    rows, mask = _case_coarse_matrix([_case("c", "s", 1, (4, 0))], [])
    assert rows.shape == (1, 0)
    assert mask.shape == (1, 0)


def test_unrepresented_view_stays_unknown_without_searching_grid(monkeypatch) -> None:
    import knee.diagnosis.squint_locator as locator

    def must_not_search(_stack):
        raise AssertionError("no compatible precedent exists in this view")

    monkeypatch.setattr(locator, "_leg_bounds", must_not_search)
    case = _case("coronal-only", "source", 1, (4, 0))
    case["regions"] = [
        {
            "view": {
                "orientation": "coronal",
                "fluid_sensitive": "yes",
                "fat_suppression": "no",
            },
            "extent_source": "retained_object_support",
        }
    ]
    result = locate_objects(
        {
            "study_uid": "new",
            "series": [
                {
                    "series_uid": "axial",
                    "view": {
                        "orientation": "axial",
                        "fluid_sensitive": "yes",
                        "fat_suppression": "no",
                    },
                    "stack": SimpleNamespace(code="present", median=np.ones((2, 2, 2))),
                }
            ],
        },
        {"cases": [case]},
    )
    assert result["objects"]["femur"]["profile"] is None
    assert (
        result["objects"]["femur"]["evidence"]["reason"]
        == "no_compatible_current_study_candidates"
    )


def test_window_batch_preserves_exact_counts_scores_and_ties() -> None:
    names, integrals = _coarse_index(
        {
            "view": {
                "orientation": "axial",
                "fluid_sensitive": "yes",
                "fat_suppression": "no",
            },
            "stack": SimpleNamespace(tile_mm=10.0),
            "metric_codes": {
                "signal_median": np.array(
                    [[[-1, 0], [1, -1]], [[0, 1], [0, -1]]], dtype=np.int8
                )
            },
        }
    )
    windows = [(0, 1, 0, 2, 0, 2), (1, 2, 0, 2, 0, 2), (0, 2, 0, 1, 0, 2)]
    batch_vectors, batch_banks = _window_coarse_batch(names, integrals, windows)
    for index, window in enumerate(windows):
        vector, banks = _window_coarse_counts(names, integrals, window)
        assert np.array_equal(batch_vectors[index], vector)
        assert np.array_equal(batch_banks[index], banks)
    case_vectors = np.array(
        [
            [1, 0, 1] * len(names),
            [0, 2, 1] * len(names),
        ],
        dtype=np.int64,
    )
    case_banks = np.ones((2, len(names)), dtype=np.bool_)
    batch_scores = _coarse_case_scores_batch(
        batch_vectors, batch_banks, case_vectors, case_banks
    )
    expected = [
        _coarse_case_scores(vector, banks, case_vectors, case_banks)
        for vector, banks in zip(batch_vectors, batch_banks, strict=True)
    ]
    assert batch_scores == expected


def test_recall_warrants_through_contract_trust_fields() -> None:
    profile = {
        "schema": "knee.squint-profile/v1",
        "subject": "acl",
        "banks": {"independent-case-bank": [4, 0, 0]},
        "source": {
            "procedure": "knee.squint-profile/scan-tercile-v1",
        },
    }
    negative_profile = {
        **profile,
        "banks": {"independent-case-bank": [3, 1, 0]},
    }
    memory = {
        "cases": [
            {
                "case_id": "positive-independent-study",
                "study_uid": "positive-study",
                "subject": "acl",
                "condition_calls": {"ACL": 1},
                "profile": profile,
                "teaching_source": {"kind": "report", "id": "positive"},
            },
            {
                "case_id": "negative-independent-study",
                "study_uid": "negative-study",
                "subject": "acl",
                "condition_calls": {"ACL": -1},
                "profile": negative_profile,
                "teaching_source": {"kind": "report", "id": "negative"},
            },
        ]
    }
    _prepared(memory)
    recall = recall_object(profile, memory, "ACL")
    assert recall["outcome"] == "present"
    positive_row = next(row for row in recall["case_terms"] if row["call"] == 1)
    assert positive_row["reaches_empirical_envelope"] is True
    assert positive_row["reaches_trust"] is True
    assert positive_row["trust"]["comparison_kind"] == (
        "strict_squared_cosine_above_finite_empirical_opposition_floor"
    )
    finding = combine_condition("ACL", {"acl": recall})
    assert finding["outcome"] == "assigned"
    assert finding["evidence"]["readings"]["acl"]["trust_checked"] is True


def test_candidate_profile_catalog_preserves_ties_and_factors_shared_payloads() -> None:
    context = {
        "series_uid": "series-current",
        "calibration": {"signal_median": [index % 7 for index in range(1200)]},
    }
    first = _profile(4, 0)
    first["source"]["series_context"] = context
    same_content = dict(first)
    distinct_same_address = {
        **first,
        "banks": {
            **first["banks"],
            "unshared bank/scope": [0, 0, 3],
        },
    }
    distinct_scope = {
        **first,
        "source": {**first["source"], "scope": "different-scope"},
    }
    full_profiles = [first, distinct_same_address, distinct_scope, same_content]
    candidates = [
        {
            "subject": "femur",
            "window": [0, 1, 0, 1, 0, 1],
            "profile": profile,
        }
        for profile in full_profiles
    ]
    result = locate_objects(
        {
            "study_uid": "current",
            "series": [
                {
                    "series_uid": "series-current",
                    "view": {
                        "orientation": "axial",
                        "fluid_sensitive": "yes",
                        "fat_suppression": "no",
                    },
                    "candidate_profiles": candidates,
                }
            ],
        },
        {"cases": [_case("prior", "other-study", 1, (4, 0))]},
    )

    located = result["objects"]["femur"]
    refs = [row["profile_ref"] for row in located["candidate_profiles"]]
    evidence = located["evidence"]
    profile_catalog = evidence["candidate_profile_catalog"]
    bank_catalog = evidence["candidate_bank_catalog"]
    context_catalog = evidence["candidate_series_context_catalog"]
    assert len(located["candidate_profiles"]) == 4
    assert len(profile_catalog) == 3
    assert len(bank_catalog) == 2
    assert len(context_catalog) == 1
    assert refs[0] == refs[3]
    assert refs[1] != refs[0]
    assert refs[2] != refs[0]
    assert (
        profile_catalog[refs[0]]["banks_ref"] == profile_catalog[refs[2]]["banks_ref"]
    )
    assert (
        profile_catalog[refs[0]]["series_context_ref"]
        == profile_catalog[refs[2]]["series_context_ref"]
    )
    assert [resolve_candidate_profile(located, ref) for ref in refs] == full_profiles
    assert [row["window"] for row in located["candidate_profiles"]] == [
        [0, 1, 0, 1, 0, 1]
    ] * 4
    assert [row["squared_similarity"] for row in located["candidate_profiles"]] == [
        {"numerator": "256", "denominator": "256"}
    ] * 4

    best = evidence["case_best_candidates"]
    assert len(best) == 1
    assert best[0]["case_id"] == "prior"
    assert best[0]["squared_similarity"] == {
        "numerator": "256",
        "denominator": "256",
    }
    assert len(best[0]["candidates"]) == 4
    assert [row["profile_ref"] for row in best[0]["candidates"]] == refs
    assert [
        resolve_candidate_profile(located, row["profile_ref"])
        for row in best[0]["candidates"]
    ] == full_profiles
    assert located["profile"] is None

    factored_size = len(
        __import__("json").dumps(
            {
                "profiles": profile_catalog,
                "banks": bank_catalog,
                "series_contexts": context_catalog,
            },
            sort_keys=True,
        )
    )
    repeated_full_size = len(
        __import__("json").dumps(full_profiles * 2, sort_keys=True)
    )
    assert factored_size < repeated_full_size

    with pytest.raises(ValueError, match="candidate_profile_ref_missing"):
        resolve_candidate_profile(located, "absent-profile-ref")
    broken = dict(located)
    broken_evidence = dict(evidence)
    broken_profiles = dict(profile_catalog)
    broken_profiles[refs[0]] = {"schema": "wrong/v1", "status": "available"}
    broken_evidence["candidate_profile_catalog"] = broken_profiles
    broken["evidence"] = broken_evidence
    with pytest.raises(ValueError, match="candidate_profile_schema_invalid"):
        resolve_candidate_profile(broken, refs[0])
    broken = dict(located)
    broken_evidence = dict(evidence)
    broken_profiles = dict(profile_catalog)
    broken_profiles[refs[0]] = {
        **profile_catalog[refs[0]],
        "banks_ref": "absent-bank-ref",
    }
    broken_evidence["candidate_profile_catalog"] = broken_profiles
    broken["evidence"] = broken_evidence
    with pytest.raises(ValueError, match="candidate_profile_banks_ref_missing"):
        resolve_candidate_profile(broken, refs[0])
    broken_profiles[refs[0]] = {
        **profile_catalog[refs[0]],
        "series_context_ref": "absent-context-ref",
    }
    broken_evidence["candidate_profile_catalog"] = broken_profiles
    with pytest.raises(
        ValueError, match="candidate_profile_series_context_ref_missing"
    ):
        resolve_candidate_profile(broken, refs[0])


def test_coarse_projection_requires_exact_scale_identity() -> None:
    readings = {
        "axial/signal/scale=10mm": [1, 2, 3],
        "axial/gradient/scale=1e1mm": [4, 5, 6],
        "axial/rounding-neighbour/scale=10.000000000000000001mm": [7, 8, 9],
        "axial/invalid/scale=not-a-numbermm": [10, 11, 12],
        "axial/invalid/scale=sNaNmm": [13, 14, 15],
    }
    result = _coarse_only_projection({"subject": "femur", "banks": readings})
    assert result is not None
    assert result["banks"] == {
        "axial/signal/scale=10mm": [1, 2, 3],
        "axial/gradient/scale=1e1mm": [4, 5, 6],
    }


def test_locator_uses_finite_anatomy_windows_via_shared_profile_writer(
    monkeypatch,
) -> None:
    calls: list[tuple[int, ...]] = []
    bank = (
        'squint/v1/view=["axial","yes","no"]/metric=signal_median/'
        "direction=overview/scale=10mm"
    )

    def profile_window(series: dict, window: tuple[int, ...], *, subject: str) -> dict:
        calls.append(window)
        return {
            "subject": subject,
            "banks": {bank: [1, 7, 0]},
            "source": {"procedure": "knee.squint-profile/scan-tercile-v1"},
        }

    writer = ModuleType("knee.diagnosis.squint_profiles")
    writer.profile_window = profile_window
    monkeypatch.setitem(sys.modules, writer.__name__, writer)
    windows = [(0, 1, 0, 2, 0, 2)]
    helper_calls = []
    cached_foreground = np.zeros((2, 2, 2), dtype=bool)
    cached_foreground[0, 0, 0] = True

    def cached_leg_bounds(_stack, _leg_map=None):
        return (0, 0, 0), (2, 2, 2), cached_foreground

    monkeypatch.setattr(locator_module, "_leg_bounds", cached_leg_bounds)
    helper = ModuleType("knee.diagnosis.squint_anatomical_priors")

    def anatomical_windows(series, subject, **kwargs):
        helper_calls.append((subject, kwargs, series.get("foreground")))
        return {"status": "proposed", "windows": windows, "provenance": {"stub": True}}

    helper.anatomical_windows = anatomical_windows
    monkeypatch.setitem(sys.modules, helper.__name__, helper)
    stack = SimpleNamespace(
        code="present",
        median=np.ones((2, 2, 2)),
        coverage=np.ones((2, 2, 2)),
        centres_lps=np.zeros((2, 2, 2, 3)),
        tile_mm=10.0,
    )
    case_profile = {
        "subject": "femur",
        "banks": {bank: [1, 7, 0]},
        "source": {"procedure": "knee.squint-profile/scan-tercile-v1"},
    }
    case_profile["source"]["window"] = [0, 1, 0, 2, 0, 2]
    memory = {"cases": [_case("prior", "other", 1, (4, 0))]}
    memory["cases"][0]["profile"] = case_profile
    result = locate_objects(
        {
            "study_uid": "current",
            "series": [
                {
                    "series_uid": "series-current",
                    "view": {
                        "orientation": "axial",
                        "fluid_sensitive": "yes",
                        "fat_suppression": "no",
                    },
                    "stack": stack,
                    "metric_codes": {
                        "signal_median": np.array(
                            [[[-1, 0], [0, 0]], [[0, 0], [0, 0]]],
                            dtype=np.int8,
                        )
                    },
                }
            ],
        },
        memory,
    )
    assert calls == [(0, 1, 0, 2, 0, 2)], (
        helper_calls,
        result["objects"]["femur"]["evidence"],
    )
    assert helper_calls[0][0] == "femur"
    assert helper_calls[0][1]["knee_scale_mm"] is None
    assert helper_calls[0][2] is not None
    assert helper_calls[0][2].dtype == np.dtype(bool)
    assert helper_calls[0][2] is cached_foreground
    assert result["objects"]["femur"]["status"] == "proposal"
    assert result["objects"]["femur"]["regions"][0]["window"] == (0, 1, 0, 2, 0, 2)
    assert result["evidence"]["candidate_generation"] == "finite_anatomy_first"


def test_locator_refines_only_finite_coarse_best_window(monkeypatch) -> None:
    calls: list[tuple[int, ...]] = []
    bank = (
        'squint/v1/view=["axial","yes","no"]/metric=signal_median/'
        "direction=overview/scale=10mm"
    )

    def profile_window(series: dict, window: tuple[int, ...], *, subject: str) -> dict:
        calls.append(window)
        return {
            "subject": subject,
            "banks": {bank: [2, 0, 0]},
            "source": {"procedure": "knee.squint-profile/scan-tercile-v1"},
        }

    writer = ModuleType("knee.diagnosis.squint_profiles")
    writer.profile_window = profile_window
    monkeypatch.setitem(sys.modules, writer.__name__, writer)
    finite_windows = [(0, 1, 0, 1, 0, 1), (2, 3, 0, 1, 0, 1)]
    helper = ModuleType("knee.diagnosis.squint_anatomical_priors")
    helper.anatomical_windows = lambda *_args, **_kwargs: {
        "status": "proposed",
        "windows": finite_windows,
        "provenance": {"stub": "two-finite-windows"},
    }
    monkeypatch.setitem(sys.modules, helper.__name__, helper)
    stack = SimpleNamespace(
        code="present",
        median=np.ones((4, 1, 1)),
        coverage=np.ones((4, 1, 1)),
        centres_lps=np.zeros((4, 1, 1, 3)),
        tile_mm=10.0,
    )
    case_profile = {
        "subject": "femur",
        "banks": {bank: [2, 0, 0]},
        "source": {
            "window": [0, 2, 0, 1, 0, 1],
            "procedure": "knee.squint-profile/scan-tercile-v1",
        },
    }
    memory = {
        "cases": [
            {
                **_case("prior", "other", 1, (2, 0)),
                "profile": case_profile,
            }
        ]
    }
    result = locate_objects(
        {
            "study_uid": "current",
            "series": [
                {
                    "series_uid": "series-current",
                    "view": {
                        "orientation": "axial",
                        "fluid_sensitive": "yes",
                        "fat_suppression": "no",
                    },
                    "stack": stack,
                    "metric_codes": {
                        "signal_median": np.array(
                            [[[-1]], [[-1]], [[1]], [[1]]], dtype=np.int8
                        )
                    },
                }
            ],
        },
        memory,
    )
    assert calls == [(0, 1, 0, 1, 0, 1)], result["objects"]["femur"]["evidence"]
    finalists = next(
        iter(result["objects"]["femur"]["evidence"]["coarse_finalists"].values())
    )
    assert finalists["candidate_count"] == 1
    assert finalists["candidates"][0]["window"] == list(finite_windows[0])
    assert (
        result["objects"]["femur"]["evidence"]["case_best_candidates"][0]["case_id"]
        == "prior"
    )


def test_finite_helper_keeps_case_index_for_relative_anchor_priors(
    monkeypatch,
) -> None:
    bank = (
        'squint/v1/view=["axial","yes","no"]/metric=signal_median/'
        "direction=overview/scale=10mm"
    )
    writer = ModuleType("knee.diagnosis.squint_profiles")

    def profile_window(series: dict, window: tuple[int, ...], *, subject: str) -> dict:
        codes = series["metric_codes"]["signal_median"]
        selected = codes[
            window[0] : window[1], window[2] : window[3], window[4] : window[5]
        ]
        counts = [int(np.count_nonzero(selected == digit)) for digit in (-1, 0, 1)]
        return {
            "subject": subject,
            "banks": {bank: counts},
            "source": {
                "procedure": "knee.squint-profile/scan-tercile-v1",
                "window": list(window),
            },
        }

    writer.profile_window = profile_window
    monkeypatch.setitem(sys.modules, writer.__name__, writer)
    finite_windows = {
        "femur": [(0, 1, 0, 1, 0, 1)],
        "meniscus": [(1, 2, 0, 1, 0, 1)],
        "tibia": [(2, 3, 0, 1, 0, 1)],
    }
    helper = ModuleType("knee.diagnosis.squint_anatomical_priors")

    def anatomical_windows(_series, subject, **_kwargs):
        return {
            "status": "proposed",
            "windows": finite_windows[subject],
            "provenance": {"stub_subject": subject},
        }

    helper.anatomical_windows = anatomical_windows
    monkeypatch.setitem(sys.modules, helper.__name__, helper)

    def source_case(subject: str, call: int, point: tuple[float, float, float]) -> dict:
        return {
            "case_id": f"case-{subject}",
            "study_uid": "source-study",
            "subject": subject,
            "condition_calls": {"acl": call},
            "profile": {
                "subject": subject,
                "banks": {
                    bank: {
                        "femur": [1, 0, 0],
                        "meniscus": [0, 1, 0],
                        "tibia": [0, 0, 1],
                    }[subject]
                },
                "source": {"procedure": "knee.squint-profile/scan-tercile-v1"},
            },
            "regions": [
                {
                    "source_window": [0, 1, 0, 1, 0, 1],
                    "source_point_lps": list(point),
                    "view": {
                        "orientation": "axial",
                        "fluid_sensitive": "yes",
                        "fat_suppression": "no",
                    },
                }
            ],
        }

    memory = {
        "cases": [
            source_case("femur", 1, (0.0, 0.0, 0.0)),
            source_case("meniscus", 1, (0.0, 0.0, 60.0)),
            source_case("tibia", -1, (0.0, 0.0, 100.0)),
        ]
    }
    stack = SimpleNamespace(
        code="present",
        median=np.ones((3, 1, 1)),
        coverage=np.ones((3, 1, 1)),
        bounds_rc=np.asarray([[[0, 2, 0, 2]]], dtype=np.int64),
        centres_lps=np.array(
            [[[0.0, 0.0, 0.0]], [[0.0, 0.0, 60.0]], [[0.0, 0.0, 100.0]]]
        ).reshape(3, 1, 1, 3),
        tile_mm=10.0,
    )
    geometry = {
        "position": np.asarray([[0.0, 0.0, 0.0], [0.0, 0.0, 60.0], [0.0, 0.0, 100.0]]),
        "orientation": np.asarray([[1, 0, 0, 0, 1, 0]] * 3, dtype=float),
        "spacing": np.asarray([[1.0, 1.0]] * 3),
    }
    result = locate_objects(
        {
            "study_uid": "current-study",
            "series": [
                {
                    "series_uid": "current-series",
                    "view": {
                        "orientation": "axial",
                        "fluid_sensitive": "yes",
                        "fat_suppression": "no",
                    },
                    "stack": stack,
                    "geometry": geometry,
                    "metric_codes": {
                        "signal_median": np.array([[[-1]], [[0]], [[1]]], dtype=np.int8)
                    },
                }
            ],
        },
        memory,
    )
    assert result["objects"]["femur"]["status"] == "proposal"
    assert result["objects"]["tibia"]["status"] == "proposal"
    assert result["objects"]["meniscus"]["status"] == "proposal", result["objects"][
        "meniscus"
    ]["evidence"]
    assert result["objects"]["meniscus"]["regions"][0]["window"] == (
        1,
        2,
        0,
        1,
        0,
        1,
    )
    meniscus_priors = result["objects"]["meniscus"]["evidence"]["relative_scope_priors"]
    source = next(
        row for row in meniscus_priors["cases"] if row.get("case_id") == "case-meniscus"
    )
    assert source["case_index"] == 1
    assert source["status"] == "available"
    assert [row["offset_mm"] for row in source["planes"]] == [-60.0, -60.0]
    assert (
        result["objects"]["meniscus"]["evidence"]["relative_scope_priors"]["subject"]
        == "meniscus"
    )
    assert (
        result["objects"]["meniscus"]["evidence"]["proposal_sources"][0][
            "relative_scope_check"
        ]
        == "direct_finite_candidate_scope_check"
    )


def test_capacity_projection_keeps_context_only_profile_without_envelope(monkeypatch):
    from knee.diagnosis import squint_locator

    held = _case("held-positive", "held", 1, (4, 0, 0))
    peer_positive = _case("peer-positive", "peer", 1, (0, 0, 4))
    peer_negative = _case("peer-negative", "peer-negative", -1, (4, 0, 0))
    context_only = _case("context-only", "context", 0, (0, 4, 0))
    context_only["subject"] = "patella"
    context_only["condition_calls"] = {}
    memory = {
        "source": {"source_id": "context-only-projection"},
        "cases": [held, peer_positive, peer_negative, context_only],
        "censors": [],
    }
    full = prepare_recall(memory)
    assert "patella" not in full["envelopes"]
    cache = persisted_recall_cache(memory, full)
    filtered_memory = {
        **memory,
        "cases": [peer_positive, peer_negative, context_only],
    }
    fresh = prepare_recall(filtered_memory)
    with monkeypatch.context() as patcher:
        patcher.setattr(
            squint_locator,
            "_exact_bank_terms",
            lambda *args: (_ for _ in ()).throw(
                AssertionError("valid capacity cache projection recomputed pair terms")
            ),
        )
        projected = prepare_recall(memory, cached=cache, exclude_study_uid="held")
    assert projected["runtime_indexes_rebuilt"] is True
    assert projected["envelopes"] == fresh["envelopes"]
    assert projected["case_indices"] == fresh["case_indices"]
    assert projected["censor_indices"] == fresh["censor_indices"]
    assert projected["case_profile_banks"] == fresh["case_profile_banks"]
    assert projected["source_fingerprint"] == fresh["source_fingerprint"]
    assert projected["memory_source"] == fresh["memory_source"]
    assert "patella" not in projected["envelopes"]
    assert 2 in projected["case_profile_banks"]
    assert "patella" in projected["subject_profile_matrices"]
    for subject, matrix in fresh["subject_profile_matrices"].items():
        np.testing.assert_array_equal(
            projected["subject_profile_matrices"][subject]["values"],
            matrix["values"],
        )
