"""W7 intent checks against the frozen selection shape, independent of W6 delivery."""

from __future__ import annotations

import copy
import json
import sys
from types import ModuleType, SimpleNamespace

import pytest

from knee.diagnosis import squint_locator as locator
from knee.diagnosis.squint_interfaces import (
    SELECTION_SCHEMA,
    TERRITORY_PROCEDURE,
    parse_territory_bank_name,
    territory_bank_name,
)

VIEW = {"orientation": "Coronal", "fluid_sensitive": "1", "fat_suppression": "1"}


def bank(metric="signal_median", role="object", scale=10.0):
    return territory_bank_name(VIEW, role, metric, "overview", scale)


def selection(question="ACL", metric="signal_median"):
    return {
        "schema": SELECTION_SCHEMA,
        "question_id": question,
        "version": "test-declared-v1",
        "cheap_procedure": TERRITORY_PROCEDURE,
        "configuration_subject": "diagnosis/" + question,
        "subjects": {"acl": "defining", "femur": "supporting"},
        "cheap": [
            {
                "subject": subject,
                "role": "object",
                "metrics": [metric],
                "scales_mm": [10.0, 2.0],
            }
            for subject in ("acl", "femur")
        ],
        "full_prefixes": [],
        "unavailable": [],
    }


@pytest.fixture(autouse=True)
def question_adapter(monkeypatch):
    """A literal test adapter until W6 is merged; never a production selector."""
    existing = sys.modules.get("knee.diagnosis.squint_questions")
    if existing is not None and hasattr(existing, "SELECTION_VERSION"):
        return existing
    module = ModuleType("knee.diagnosis.squint_questions")

    def select_cheap_banks(selected, subject, names):
        descriptors = [row for row in selected["cheap"] if row["subject"] == subject]
        result = []
        for name in names:
            raw = name
            if name.startswith("object/"):
                owner, _, raw = name[len("object/") :].partition("/")
                if owner != subject:
                    continue
            fields = parse_territory_bank_name(raw)
            if fields and any(
                fields["role"] == row["role"]
                and fields["metric"] in row["metrics"]
                and fields["scale_mm"] in row["scales_mm"]
                for row in descriptors
            ):
                result.append(name)
        return tuple(
            sorted(result)
        ), "selected" if result else "no_selected_bank_present"

    module.question_selection = selection
    module.select_cheap_banks = select_cheap_banks
    monkeypatch.setitem(sys.modules, module.__name__, module)
    return module


def profile(counts=(4, 0, 0), *, subject="acl", extra=(0, 4, 0)):
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": {
            bank(): list(counts),
            bank("local_range"): list(extra),
            bank(role="context"): [4, 0, 0],
        },
        "source": {"procedure": TERRITORY_PROCEDURE},
    }


def case(case_id, call, counts, *, subject="acl"):
    return {
        "case_id": case_id,
        "study_uid": "study-" + case_id,
        "subject": subject,
        "condition_calls": {"ACL": call},
        "profile": profile(counts, subject=subject),
        "teaching_source": {"kind": "independent_call"},
    }


def memory():
    return {"cases": [case("positive", 1, (4, 0, 0)), case("negative", -1, (3, 1, 0))]}


def test_unselected_banks_never_enter_arithmetic_or_change_results(monkeypatch):
    selected = selection()
    original = memory()
    original["censors"] = [
        {
            "question": "ACL",
            "answer": -1,
            "profile": profile(),
            "radius_numerator": 1,
            "radius_denominator": 1,
        }
    ]
    changed = copy.deepcopy(original)
    for row in changed["cases"]:
        row["profile"]["banks"][bank("local_range")] = [10**40, 0, 10**40]
        row["profile"]["banks"][bank(role="context")] = [0, 10**50, 0]
    changed["censors"][0]["profile"]["banks"][bank("local_range")] = [0, 0, 10**50]
    exact = locator._exact_bank_terms

    def assert_selected(left, right):
        assert set(left) <= {bank()}
        assert set(right) <= {bank()}
        return exact(left, right)

    monkeypatch.setattr(locator, "_exact_bank_terms", assert_selected)
    original["prepared_recall"] = locator.prepare_recall(original, selection=selected)
    changed["prepared_recall"] = locator.prepare_recall(changed, selection=selected)
    assert (
        original["prepared_recall"]["envelopes"]
        == changed["prepared_recall"]["envelopes"]
    )
    matrix = changed["prepared_recall"]["question_profile_matrices"]["acl"]["ACL"]
    assert matrix["names"] == (bank(),)
    assert matrix["safe_int64"]
    query = profile()
    altered_query = profile(extra=(10**50, 0, 0))
    altered_query["banks"][bank(role="context")] = [0, 0, 10**40]
    expected = locator.recall_object(query, original, "ACL", selection=selected)
    actual = locator.recall_object(altered_query, changed, "ACL", selection=selected)
    assert actual == expected
    assert actual["outcome"] == "present"
    assert all(
        row["common_speaking_banks"] == [bank()]
        for row in actual["case_terms"] + actual["censor_terms"]
    )


def test_selected_query_and_selected_case_can_change_cosine_envelope_and_outcome():
    selected = selection()
    store = memory()
    store["prepared_recall"] = locator.prepare_recall(store, selection=selected)
    positive = locator.recall_object(profile(), store, "ACL", selection=selected)
    negative = locator.recall_object(
        profile((3, 1, 0)), store, "ACL", selection=selected
    )
    assert positive["outcome"] == "present"
    assert negative["outcome"] == "absent"
    assert (
        positive["case_terms"][0]["squared_cosine"]
        != negative["case_terms"][0]["squared_cosine"]
    )
    changed = memory()
    changed["cases"][1]["profile"]["banks"][bank()] = [0, 4, 0]
    updated = locator.prepare_recall(changed, selection=selected)
    assert updated["envelopes"] != store["prepared_recall"]["envelopes"]
    assert (
        next(iter(updated["envelopes"]["acl"]["ACL"].values()))[
            "maximum_squared_cosine"
        ]["numerator"]
        == "0"
    )


def test_unselected_payload_is_not_read_as_counts():
    selected = selection()
    store = memory()
    store["prepared_recall"] = locator.prepare_recall(store, selection=selected)
    expected = locator.recall_object(profile(), store, "ACL", selection=selected)
    changed = memory()
    for row in changed["cases"]:
        row["profile"]["banks"][bank("local_range")] = "not a selected count payload"
    changed["prepared_recall"] = locator.prepare_recall(changed, selection=selected)
    query = profile()
    query["banks"][bank("local_range")] = "not a selected count payload"
    actual = locator.recall_object(query, changed, "ACL", selection=selected)
    assert actual == expected


def test_missing_envelope_and_observed_below_envelope_have_distinct_reasons():
    selected = selection()
    store = memory()
    store["prepared_recall"] = locator.prepare_recall(store, selection=selected)
    below = locator.recall_object(profile((0, 0, 4)), store, "ACL", selection=selected)
    assert below["outcome"] == "proposal"
    assert {row["reason_code"] for row in below["case_terms"]} == {
        "below_empirical_envelope"
    }
    store = {"cases": [store["cases"][0]]}
    store["prepared_recall"] = locator.prepare_recall(store, selection=selected)
    missing = locator.recall_object(profile(), store, "ACL", selection=selected)
    assert missing["outcome"] == "proposal"
    assert missing["case_terms"][0]["reason_code"] == "no_compatible_envelope"
    assert missing["case_terms"][0]["trust"] is None
    assert below["case_terms"][0]["trust"] is not None


@pytest.mark.parametrize(
    "invalid,reason",
    [
        (None, "selection_schema_invalid"),
        ({}, "selection_schema_invalid"),
        ({**selection(), "cheap": []}, "selection_empty"),
    ],
)
def test_empty_or_invalid_selection_is_named(invalid, reason):
    store = memory()
    result = locator.recall_object(profile(), store, "ACL", selection=invalid)
    assert result["reason"] == reason
    assert result["speaking_calls"] == []
    prepared = locator.prepare_recall(store, selection=invalid)
    assert prepared["outcome"] == "invalid_selection"


def test_incompatible_bank_selection_never_falls_back_to_all_banks():
    selected = selection(metric="full_profile_lens")
    result = locator.recall_object(profile(), memory(), "ACL", selection=selected)
    assert result["reason"] == "selection_no_compatible_banks"
    assert result["case_terms"] == []
    selected = selection()
    wrong_procedure = profile()
    wrong_procedure["source"]["procedure"] = "other_calibration"
    result = locator.recall_object(wrong_procedure, memory(), "ACL", selection=selected)
    assert result["reason"] == "selection_procedure_mismatch"


def test_stale_preparation_is_refused_and_cache_rebuilt_by_name():
    selected = selection()
    store = memory()
    current = locator.prepare_recall(store, selection=selected)
    stale = copy.deepcopy(current)
    stale.pop("selection_identity")
    stale.pop("selections")
    store["prepared_recall"] = stale
    refused = locator.recall_object(profile(), store, "ACL", selection=selected)
    assert refused["reason"] == "recall_preparation_selection_identity_missing"
    refused = locator.recall_object(profile(), store, "ACL")
    assert refused["reason"] == "recall_preparation_selection_identity_missing"
    cache = locator.persisted_recall_cache(store, current)
    cache["preparation"].pop("selection_identity")
    rebuilt = locator.prepare_recall(store, cached=cache, selection=selected)
    assert rebuilt["cache_status"] == "rebuilt_selection_identity_mismatch"
    assert rebuilt["envelopes"] == current["envelopes"]
    assert locator._runtime_recall_cache(store, stale) is None


def test_empty_multi_question_selection_never_prepares_all_banks():
    prepared = locator.prepare_recall(memory(), selections={})
    assert prepared == {"outcome": "invalid_selection", "reason": "selection_empty"}


def test_selection_version_and_descriptor_and_selected_tuple_bind_identity():
    selected = selection()
    store = memory()
    prepared = locator.prepare_recall(store, selection=selected)
    cache = locator.persisted_recall_cache(store, prepared)
    changed = {**selected, "version": "test-declared-v2"}
    updated = locator.prepare_recall(store, cached=cache, selection=changed)
    assert updated["cache_status"] == "rebuilt_selection_identity_mismatch"
    assert updated["source_fingerprint"] != prepared["source_fingerprint"]
    store["prepared_recall"] = prepared
    refused = locator.recall_object(profile(), store, "ACL", selection=changed)
    assert refused["reason"] == "recall_preparation_selection_identity_mismatch"
    changed = selection(metric="local_range")
    refused = locator.recall_object(profile(), store, "ACL", selection=changed)
    assert refused["reason"] == "recall_preparation_selection_identity_mismatch"
    assert prepared["selection_identity"]["ACL"]["selected_banks"]["acl"] == [bank()]


def test_selected_cache_restore_and_exclusion_match_fresh_without_pairwise_work(
    monkeypatch,
):
    selected = selection()
    store = memory()
    store["cases"].append(case("held", 1, (0, 4, 0)))
    store["censors"] = [{"question": "ACL", "study_uid": "study-held"}]
    prepared = locator.prepare_recall(store, selection=selected)
    cache = json.loads(json.dumps(locator.persisted_recall_cache(store, prepared)))
    filtered = {**store, "cases": store["cases"][:2], "censors": []}
    fresh = locator.prepare_recall(filtered, selection=selected)

    def forbidden(*args, **kwargs):
        raise AssertionError("restored preparation recomputed a cosine")

    monkeypatch.setattr(locator, "_exact_bank_terms", forbidden)
    restored = locator.prepare_recall(store, cached=cache, selection=selected)
    assert restored["runtime_indexes_rebuilt"]
    projected = locator.prepare_recall(
        store, cached=cache, selection=selected, exclude_study_uid="study-held"
    )
    assert projected["runtime_indexes_rebuilt"]
    for key in (
        "envelopes",
        "selection_identity",
        "case_indices",
        "censor_indices",
        "source_fingerprint",
        "question_case_profile_banks",
    ):
        assert projected[key] == fresh[key]
    result = locator.recall_object(
        profile(), {**filtered, "prepared_recall": projected}, "ACL", selection=selected
    )
    assert result["outcome"] == "present"


def test_two_questions_project_their_own_banks_before_preparation():
    store = memory()
    for row in store["cases"]:
        row["condition_calls"]["MCL"] = row["condition_calls"]["ACL"]
    selected = {"ACL": selection(), "MCL": selection("MCL", "local_range")}
    prepared = locator.prepare_recall(store, selections=selected)
    assert prepared["question_profile_matrices"]["acl"]["ACL"]["names"] == (bank(),)
    assert prepared["question_profile_matrices"]["acl"]["MCL"]["names"] == (
        bank("local_range"),
    )
    result = locator.recall_object(
        profile(), {**store, "prepared_recall": prepared}, "MCL"
    )
    assert {
        name for row in result["case_terms"] for name in row["common_speaking_banks"]
    } == {bank("local_range")}


def test_malformed_selected_case_is_incompatible_only_for_its_question():
    store = memory()
    store["cases"][0]["profile"]["banks"][bank()] = [-1, 0, 0]
    for row in store["cases"]:
        row["condition_calls"]["MCL"] = row["condition_calls"]["ACL"]
    prepared = locator.prepare_recall(
        store, selections={"ACL": selection(), "MCL": selection("MCL", "local_range")}
    )
    store["prepared_recall"] = prepared
    result = locator.recall_object(profile(), store, "ACL")
    assert result["incompatible_case_ids"] == ["positive"]
    result = locator.recall_object(profile(), store, "MCL")
    assert result["incompatible_case_ids"] == []
    malformed_query = profile((-1, 0, 0))
    result = locator.recall_object(malformed_query, store, "ACL")
    assert result["reason"] == "invalid_profile"


def test_configurations_select_each_qualified_role_and_censor_identically():
    selected = selection()
    store = memory()
    for row in store["cases"]:
        own = row["profile"]["banks"]
        row["subject"] = "diagnosis/ACL"
        row["profile"]["subject"] = "diagnosis/ACL"
        row["profile"]["banks"] = {
            **{f"object/acl/{name}": counts for name, counts in own.items()},
            **{f"object/femur/{name}": counts for name, counts in own.items()},
            f"object/unrelated/{bank()}": [10**30, 0, 0],
        }
    store["censors"] = [
        {
            "question": "ACL",
            "answer": -1,
            "profile": store["cases"][0]["profile"],
            "radius_numerator": 1,
            "radius_denominator": 1,
        }
    ]
    store["prepared_recall"] = locator.prepare_recall(store, selection=selected)
    result = locator.recall_object(
        store["cases"][0]["profile"], store, "ACL", selection=selected
    )
    expected = [f"object/acl/{bank()}", f"object/femur/{bank()}"]
    assert result["outcome"] == "present"
    assert all(
        row["common_speaking_banks"] == expected
        for row in result["case_terms"] + result["censor_terms"]
    )
    assert result["source"]["selection"]["subjects"] == selected["subjects"]


def test_selected_neutral_is_measured_and_unwritten_is_silent_with_large_exact_counts():
    store = memory()
    store["cases"][0]["profile"]["banks"][bank()] = [0, 10**30, 0]
    store["cases"][1]["profile"]["banks"][bank()] = [0, 0, 10**30]
    store["cases"].append(case("unread", 1, (0, 0, 0)))
    store["prepared_recall"] = locator.prepare_recall(store, selection=selection())
    result = locator.recall_object(
        profile((0, 10**30, 0)), store, "ACL", selection=selection()
    )
    assert result["outcome"] == "present"
    assert result["case_terms"][0]["terms"] == {
        "dot": 10**60,
        "left_norm_sq": 10**60,
        "right_norm_sq": 10**60,
    }
    assert result["silent_case_ids"] == ["unread"]
    assert {row["case_id"]: row["reason_code"] for row in result["case_reasons"]}[
        "unread"
    ] == "no_common_selected_reading"


def test_pipeline_supplies_one_selection_to_object_and_configuration(monkeypatch):
    from knee.diagnosis import squint_configurations, squint_pipeline

    seen = []

    def recall(profile, memory, **kwargs):
        seen.append((profile["subject"], memory["recall_selection"]))
        return {"outcome": "proposal"}

    monkeypatch.setattr(locator, "recall_object", recall)
    monkeypatch.setattr(
        squint_configurations,
        "configuration_profile",
        lambda profiles, question: {
            "subject": "diagnosis/ACL",
            "banks": {"qualified": [1, 0, 0]},
        },
    )
    squint_pipeline._recall_question(
        SimpleNamespace(question_id="ACL", objects=("acl",)),
        {"acl": {"profile": profile()}},
        {},
        "query",
        False,
    )
    assert [subject for subject, _ in seen] == ["acl", "diagnosis/ACL"]
    assert seen[0][1] is seen[1][1]
    assert seen[0][1]["question_id"] == "ACL"
