"""Held-out populations reach every consumer without remeasuring case pairs."""

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from squint_upgrade_fixtures import study_record

from knee.diagnosis import squint_anatomy_locator, squint_locator, squint_pipeline
from knee.diagnosis.squint_interfaces import MEMORY_VIEW_SCHEMA
from knee.diagnosis.squint_memory import (
    SquintMemoryError,
    full_profile_from_case,
    hydrate_full_profiles,
    save_memory,
)
from knee.diagnosis.squint_memory_view import MemoryViewError, memory_view
from knee.json_store import load_json
from knee.study.tables import LABELS


def _profile(counts=(0, 0, 4), subject="femur"):
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": {"axial/light/whole": list(counts)},
        "source": {"procedure": "knee.squint-profile/scan-tercile-v1"},
    }


def _case(identity, uid, digit, counts, subject="femur"):
    return {
        "case_id": identity,
        "study_uid": uid,
        "subject": subject,
        "condition_calls": {"ACL": digit},
        "profile": _profile(counts, subject),
        "regions": [],
    }


def _memory():
    cases = []
    for subject in ("femur", "diagnosis/ACL"):
        for identity, uid, digit, counts in (
            ("held-positive", "held", 1, (4, 0, 0)),
            ("peer-positive", "positive", 1, (0, 0, 4)),
            ("peer-negative", "negative", -1, (4, 0, 0)),
        ):
            cases.append(_case(f"{subject}:{identity}", uid, digit, counts, subject))
    memory = {
        "schema": "knee.squint-memory/v1",
        "revision": "independently-taught-r1",
        "questions": list(LABELS),
        "source": {"teaching": "independent"},
        "cases": cases,
        "censors": [
            {
                "censor_id": "held-censor",
                "question": "ACL",
                "answer": 1,
                "profile": _profile(),
                "radius_numerator": 1,
                "radius_denominator": 1,
                "source": {"study_uid": "held"},
            },
            {"censor_id": "peer-censor", "question": "ACL", "study_uid": "positive"},
            {"censor_id": "unattributed-censor", "question": "ACL"},
        ],
    }
    memory["prepared_recall"] = squint_locator.prepare_recall(memory)
    return memory


def _no_pairs(*args, **kwargs):
    raise AssertionError("memory view repeated a pairwise measurement")


def _assert_population(view, excluded):
    assert all(row["study_uid"] not in excluded for row in view["cases"])
    for row in view.get("censors", ()):
        assert row.get("study_uid") not in excluded
        assert row.get("source", {}).get("study_uid") not in excluded
    prepared = view["prepared_recall"]
    for subjects in prepared["case_indices"].values():
        for indexes in subjects.values():
            assert all(
                view["cases"][index]["study_uid"] not in excluded for index in indexes
            )
    for questions in prepared["envelopes"].values():
        for buckets in questions.values():
            for bucket in buckets.values():
                assert not any(
                    set(row["study_uids"]) & excluded for row in bucket["comparisons"]
                )


def test_exclusion_changes_warrant_and_censor_but_unexcluded_cases_are_reachable(
    monkeypatch,
):
    memory = _memory()
    before = squint_locator.persisted_recall_cache(memory, memory["prepared_recall"])
    unexcluded = memory_view(memory)
    reachable = squint_locator.recall_object(_profile(), unexcluded, "ACL")
    assert "femur:held-positive" in {row["case_id"] for row in reachable["case_terms"]}
    assert reachable["vetoed_answers"] == [1]
    assert reachable["outcome"] == "unresolved_censored"

    fresh_population = {
        **memory,
        "cases": [row for row in memory["cases"] if row["study_uid"] != "held"],
        "censors": memory["censors"][1:],
    }
    expected = squint_locator.prepare_recall(fresh_population)
    monkeypatch.setattr(squint_locator, "_exact_bank_terms", _no_pairs)
    excluded = memory_view(memory, exclude_study_uids=("held",))
    _assert_population(excluded, {"held"})
    prepared = excluded["prepared_recall"]
    for key in (
        "envelopes",
        "case_indices",
        "censor_indices",
        "case_profile_banks",
        "source_fingerprint",
    ):
        assert prepared[key] == expected[key]
    for subject, matrix in expected["subject_profile_matrices"].items():
        np.testing.assert_array_equal(
            prepared["subject_profile_matrices"][subject]["values"], matrix["values"]
        )
    result = squint_locator.recall_object(_profile(), excluded, "ACL")
    assert result["outcome"] == "present"
    assert result["vetoed_answers"] == []
    assert {row["case_id"] for row in result["case_terms"]} == {
        "femur:peer-positive",
        "femur:peer-negative",
    }
    assert (
        squint_locator.persisted_recall_cache(memory, memory["prepared_recall"])
        == before
    )
    assert "view" not in memory


def test_irrelevant_exclusion_preserves_every_recall_term_and_maximum(monkeypatch):
    memory = _memory()
    expected = squint_locator.recall_object(_profile(), memory, "ACL")
    monkeypatch.setattr(squint_locator, "_exact_bank_terms", _no_pairs)
    view = memory_view(memory, exclude_study_uids=("never-taught",))
    assert squint_locator.recall_object(_profile(), view, "ACL") == expected
    assert (
        view["prepared_recall"]["envelopes"] == memory["prepared_recall"]["envelopes"]
    )
    assert view["cases"] == memory["cases"]


def test_multiple_and_chained_exclusions_drop_empty_buckets_without_pair_work(
    monkeypatch,
):
    memory = _memory()
    expected = squint_locator.prepare_recall({**memory, "cases": [], "censors": []})
    monkeypatch.setattr(squint_locator, "_exact_bank_terms", _no_pairs)
    first = memory_view(memory, exclude_study_uids=("held",))
    second = memory_view(first, exclude_study_uids=("positive", "held"))
    direct = memory_view(memory, exclude_study_uids=("positive", "held"))
    _assert_population(second, {"positive", "held"})
    assert (
        second["prepared_recall"]["envelopes"] == direct["prepared_recall"]["envelopes"]
    )
    assert second["view"] == direct["view"]
    assert second["view"]["excluded_study_uids"] == ["held", "positive"]
    empty = memory_view(memory, exclude_study_uids=("held", "positive", "negative"))
    assert empty["cases"] == []
    assert empty["prepared_recall"]["envelopes"] == expected["envelopes"]
    assert (
        squint_locator.recall_object(_profile(), empty, "ACL")["outcome"]
        == "unresolved_no_precedent"
    )


def test_portable_full_payloads_and_conflicting_censor_attributions_are_filtered():
    memory = _memory()
    memory["full_profile_contexts"] = {
        "schema": "context-table",
        "contexts": {uid: {"study_uid": uid} for uid in ("held", "positive")},
    }
    memory["full_profile_payloads"] = {
        "schema": "payload-table",
        "payloads": {uid: {"study_uid": uid} for uid in ("held", "positive")},
    }
    memory["censors"].append(
        {
            "censor_id": "conflicting-attribution",
            "question": "ACL",
            "study_uid": "positive",
            "source": {"study_uid": "held"},
        }
    )
    memory["prepared_recall"] = squint_locator.prepare_recall(memory)
    view = memory_view(memory, exclude_study_uids=("held",))
    assert set(view["full_profile_contexts"]["contexts"]) == {"positive"}
    assert set(view["full_profile_payloads"]["payloads"]) == {"positive"}
    assert "conflicting-attribution" not in view["view"]["retained_censor_ids"]
    assert "unattributed-censor" in view["view"]["retained_censor_ids"]
    assert "held" in memory["full_profile_payloads"]["payloads"]


def test_public_full_reader_cannot_resolve_an_excluded_case_handle(tmp_path):
    from test_squint_full_profiles import _fixture_product, _legacy_memory

    product = tmp_path / "study-portable-full.h5"
    manifest, record = _fixture_product(product)
    memory = hydrate_full_profiles(_legacy_memory(product, manifest, record), tmp_path)
    case = memory["cases"][0]
    expected = full_profile_from_case(memory, case)
    unexcluded = memory_view(memory)
    assert full_profile_from_case(unexcluded, case) == expected
    excluded = memory_view(memory, exclude_study_uids=(case["study_uid"],))
    assert excluded["full_profile_contexts"]["contexts"] == {}
    assert excluded["full_profile_payloads"]["payloads"] == {}
    with pytest.raises(SquintMemoryError, match="full_profile_case_not_in_memory"):
        full_profile_from_case(excluded, case)


@pytest.mark.parametrize("change", ("profile", "call", "censor"))
def test_stale_preparation_source_is_refused_with_named_code_without_rebuild(
    monkeypatch, change
):
    memory = _memory()
    if change == "profile":
        memory["cases"][0]["profile"] = _profile((0, 4, 0))
    elif change == "call":
        memory["cases"][0]["condition_calls"]["ACL"] = -1
    else:
        memory["censors"].append({"question": "ACL", "study_uid": "held"})
    monkeypatch.setattr(squint_locator, "_exact_bank_terms", _no_pairs)
    with pytest.raises(MemoryViewError) as error:
        memory_view(memory, exclude_study_uids=("held",))
    assert error.value.code == "memory_view_preparation_source_mismatch"


def test_selection_identity_is_required_and_retained_in_preparation_fingerprint():
    memory = _memory()
    with pytest.raises(
        MemoryViewError, match="memory_view_preparation_selection_mismatch"
    ):
        memory_view(memory, selection_version="questions-v2")
    legacy = memory_view(memory)
    memory["prepared_recall"]["selection_version"] = "questions-v2"
    selected = memory_view(memory, selection_version="questions-v2")
    assert selected["prepared_recall"]["selection_version"] == "questions-v2"
    assert (
        selected["view"]["preparation_fingerprint"]
        != legacy["view"]["preparation_fingerprint"]
    )


@pytest.mark.parametrize(
    "field,value,code",
    (
        (
            "memory_revision",
            "other-revision",
            "memory_view_preparation_revision_mismatch",
        ),
        (
            "memory_manifest_sha256",
            "b" * 64,
            "memory_view_preparation_manifest_mismatch",
        ),
    ),
)
def test_explicit_preparation_revision_and_manifest_must_match(field, value, code):
    memory = _memory()
    memory["memory_manifest_sha256"] = "a" * 64
    memory["prepared_recall"][field] = value
    with pytest.raises(MemoryViewError) as error:
        memory_view(memory, exclude_study_uids=("held",))
    assert error.value.code == code


def test_parent_population_cannot_change_under_its_identity():
    parent = memory_view({"revision": "r1", "cases": []})
    parent["cases"].append(_case("later", "held", 1, (0, 0, 4)))
    with pytest.raises(MemoryViewError, match="memory_view_parent_source_mismatch"):
        memory_view(parent, exclude_study_uids=("held",))


def test_view_identity_and_missing_preparation_do_not_invent_readings():
    memory = {"revision": "r1", "cases": [], "memory_manifest_sha256": "a" * 64}
    before = copy.deepcopy(memory)
    view = memory_view(memory, exclude_study_uids=("b", "a", "b"))
    assert "prepared_recall" not in view
    assert view["view"]["schema"] == MEMORY_VIEW_SCHEMA
    assert view["view"]["revision"] == "r1"
    assert view["view"]["manifest_identity"] == {
        "scope": "manifest_bytes",
        "sha256": "a" * 64,
    }
    assert view["view"]["excluded_study_uids"] == ["a", "b"]
    assert view["view"]["preparation_code"] == "recall_preparation_required"
    assert memory == before
    content = {"revision": "r1", "cases": []}
    unpinned = memory_view(content)
    assert unpinned["view"]["manifest_identity"] == {
        "scope": "canonical_manifest_content",
        "sha256": hashlib.sha256(
            json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }


@pytest.mark.parametrize(
    "memory,exclusions,code",
    (
        (None, (), "memory_view_memory_invalid"),
        ({"cases": None}, (), "memory_view_cases_invalid"),
        ({"cases": []}, "held", "memory_view_excluded_study_uids_invalid"),
        ({"cases": []}, (None,), "memory_view_excluded_study_uids_invalid"),
        ({"cases": []}, ("",), "memory_view_excluded_study_uids_invalid"),
        ({"cases": []}, None, "memory_view_excluded_study_uids_invalid"),
        ({"cases": [{"study_uid": []}]}, (), "memory_view_study_uid_invalid"),
        (
            {"cases": [], "memory_manifest_sha256": "wrong"},
            (),
            "memory_view_manifest_sha256_invalid",
        ),
        ({"cases": [], "prepared_recall": {}}, (), "memory_view_preparation_invalid"),
    ),
)
def test_malformed_view_inputs_have_named_refusals(memory, exclusions, code):
    with pytest.raises(MemoryViewError) as error:
        memory_view(memory, exclude_study_uids=exclusions)
    assert error.value.code == code


def test_legacy_comparisons_missing_provenance_are_refused_without_pairs(monkeypatch):
    memory = _memory()
    bucket = next(iter(memory["prepared_recall"]["envelopes"]["femur"]["ACL"].values()))
    bucket["comparisons"][0].pop("projection_mode")
    monkeypatch.setattr(squint_locator, "_exact_bank_terms", _no_pairs)
    with pytest.raises(
        MemoryViewError, match="memory_view_preparation_projection_unavailable"
    ):
        memory_view(memory, exclude_study_uids=("held",))


def test_cached_and_raw_location_receive_the_same_excluded_population(monkeypatch):
    view = memory_view(_memory(), exclude_study_uids=("held",))
    study = {
        "study_uid": "held",
        "series": [
            {
                "series_uid": "query-series",
                "candidate_profiles": [
                    {
                        "subject": "femur",
                        "profile": _profile(),
                        "window": [0, 1, 0, 1, 0, 1],
                    }
                ],
            }
        ],
    }
    locations = squint_locator.locate_objects(study, view)
    cases = locations["objects"]["femur"]["evidence"]["case_best_candidates"]
    assert {row["case_id"] for row in cases} == {
        "femur:peer-positive",
        "femur:peer-negative",
    }

    seen = []

    def raw(current, memory, deadline):
        seen.append(memory)
        _assert_population(memory, {"held"})
        return {"objects": {}}

    monkeypatch.setattr(squint_anatomy_locator, "locate_anatomy_first", raw)
    squint_locator.locate_objects(study_record(), view)
    assert seen == [view]


def test_direct_api_and_cli_capacity_consume_identical_view(monkeypatch, tmp_path):
    memory = _memory()
    prepared = memory.pop("prepared_recall")
    saved = save_memory(memory, tmp_path / "memory", prepared_recall=prepared)
    memory["memory_manifest_sha256"] = saved["sha256"]
    memory["prepared_recall"] = prepared
    seen = []

    def locate(study, population, *, deadline):
        seen.append(population)
        _assert_population(population, {"held"})
        return {"objects": {}}

    monkeypatch.setattr(squint_locator, "locate_objects", locate)
    monkeypatch.setattr(
        "knee.diagnosis.squint_profiles.read_study_squints",
        lambda *a, **k: {"study_uid": "held", "series": [], "work": {}},
    )
    direct = squint_pipeline.infer_study(
        tmp_path, "held", memory, exclude_same_study=True
    )
    receipt = squint_pipeline.run_squint_cli(
        argparse.Namespace(
            root=tmp_path,
            study_uid=["held"],
            workers=1,
            diagnostic_mode="capacity",
            diagnostic_memory=tmp_path / "memory",
            diagnostic_output=tmp_path / "capacity",
        )
    )
    assert len(seen) == 2
    assert seen[0]["view"] == seen[1]["view"]
    assert seen[0]["cases"] == seen[1]["cases"]
    assert seen[0]["censors"] == seen[1]["censors"]
    assert (
        seen[0]["prepared_recall"]["envelopes"]
        == seen[1]["prepared_recall"]["envelopes"]
    )
    retained = load_json(
        tmp_path / "capacity" / receipt["work"]["studies"][0]["evidence_path"]
    )
    assert retained["values"] == direct["values"]
    assert retained["questions"] == direct["questions"]
    assert retained["capacity_exclusion"]["excluded_case_count"] == 2
    assert retained["capacity_exclusion"]["excluded_censor_count"] == 1


def test_real_cli_entrypoint_excludes_the_dicom_study(tmp_path):
    from test_squint_orchestration import _study

    uid, _study_record = _study(tmp_path)
    memory = _memory()
    memory.pop("prepared_recall")
    for row in memory["cases"]:
        if row["study_uid"] == "held":
            row["study_uid"] = uid
    memory["censors"][0]["source"]["study_uid"] = uid
    prepared = squint_locator.prepare_recall(memory)
    save_memory(memory, tmp_path / "memory", prepared_recall=prepared)
    worktree = Path(__file__).resolve().parents[1]
    command = [
        sys.executable,
        str(worktree / "scripts" / "run_interiors.py"),
        "--root",
        str(tmp_path),
        "--study-uid",
        uid,
        "--workers",
        "1",
        "--diagnostic-mode",
        "capacity",
        "--diagnostic-memory",
        str(tmp_path / "memory"),
        "--diagnostic-output",
        str(tmp_path / "cli"),
        "--squint-time-limit",
        "60",
    ]
    result = subprocess.run(
        command,
        check=False,
        cwd=worktree,
        env={
            **os.environ,
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(worktree / "src"),
        },
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=60,
    )
    assert result.returncode == 0, result.stdout
    receipt = load_json(tmp_path / "cli" / "receipt.json")
    study = receipt["work"]["studies"][0]
    assert study["capacity_exclusion"]["excluded_study_uid"] == uid
    assert study["capacity_exclusion"]["excluded_case_count"] == 2
    assert study["capacity_exclusion"]["excluded_censor_count"] == 1
    assert study["recall_preparation_source"] == "study_excluded_projected"
    assert study["full_anatomy_runs"] == 0
    assert set(load_json(tmp_path / "cli" / study["evidence_path"])["values"]) == set(
        LABELS
    )


def test_identity_teaching_records_leave_the_population_with_their_study():
    memory = _memory()
    memory["object_identity_cases"] = {
        "schema": "knee.object-identity-cases/v1",
        "cases": [
            {"case_id": "negative-held", "study_uid": "held", "subject": "femur"},
            {"case_id": "negative-peer", "study_uid": "positive", "subject": "femur"},
        ],
    }
    expected = squint_locator.prepare_recall(memory)
    memory["prepared_recall"] = expected
    view = memory_view(memory, exclude_study_uids=("held",))
    table = view["object_identity_cases"]
    assert table["schema"] == "knee.object-identity-cases/v1"
    assert [row["case_id"] for row in table["cases"]] == ["negative-peer"]
    assert len(memory["object_identity_cases"]["cases"]) == 2
    # Condition recall's preparation never reads the identity table.
    assert (
        expected["source_fingerprint"]
        == squint_locator.prepare_recall(
            {
                key: value
                for key, value in memory.items()
                if key != "object_identity_cases"
            }
        )["source_fingerprint"]
    )
    with pytest.raises(MemoryViewError) as error:
        memory_view({"cases": [], "object_identity_cases": {"cases": None}})
    assert error.value.code == "memory_view_object_identity_cases_invalid"


def test_procedure_experiences_leave_the_population_with_their_study():
    memory = _memory()
    memory["procedure_experiences"] = {
        "schema": "knee.squint-procedure-experience-memory/v1",
        "rows": [
            {
                "row_id": "run|held|000",
                "study_uid": "held",
                "source": {"study_uid": "held"},
            },
            {
                "row_id": "run|positive|000",
                "study_uid": "positive",
                "source": {"study_uid": "positive"},
            },
        ],
    }
    view = memory_view(memory, exclude_study_uids=("held",))
    table = view["procedure_experiences"]
    assert [row["row_id"] for row in table["rows"]] == ["run|positive|000"]
    assert len(memory["procedure_experiences"]["rows"]) == 2
    with pytest.raises(MemoryViewError) as error:
        memory_view({"cases": [], "procedure_experiences": {"rows": None}})
    assert error.value.code == "memory_view_procedure_experiences_invalid"
