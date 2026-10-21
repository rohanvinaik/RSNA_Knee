from __future__ import annotations

import copy
from pathlib import Path

from test_squint_identity import profile, sanity, two_identity_memory

from knee.diagnosis import squint_identity, squint_pipeline


def located(counts, proposed, verdict="unknown"):
    return {
        "profile": profile(counts, subject=proposed),
        "sanity": sanity(verdict),
        "status": "located",
        "regions": [],
    }


def identity_signal(result):
    return (
        result["outcome"],
        result.get("identity"),
        tuple(
            (
                row["case_id"],
                row["squared_cosine"],
                tuple(row["common_speaking_banks"]),
                row["envelope"],
                row["speaks"],
            )
            for row in result.get("cases", [])
        ),
    )


def test_identity_consumer_prepares_once_and_preserves_sanity_independently(
    monkeypatch,
):
    mem = two_identity_memory()
    objects = {
        "proposed-B": located((1, 0, 0), "B", "unknown"),
        "proposed-A": located((1, 0, 0), "A", "plausible"),
        "contradicted-B": located((1, 0, 0), "B", "contradicted"),
    }
    original = squint_identity.prepare_identity
    preparations = []

    def counted(memory_value, *, exclude_study_uid=None):
        preparations.append(exclude_study_uid)
        return original(memory_value, exclude_study_uid=exclude_study_uid)

    monkeypatch.setattr(squint_identity, "prepare_identity", counted)
    before = copy.deepcopy(mem)
    result = squint_pipeline._identity_readings(objects, mem, None)

    assert preparations == [None]
    assert result["schema"] == "knee.study-object-identity/v1"
    assert result["outcome"] == "examined"
    assert result["memory_published"] is False
    assert result["objects"]["proposed-B"]["identity"] == "A"
    assert result["objects"]["proposed-A"]["identity"] == "A"
    assert result["objects"]["proposed-B"]["sanity"] == {"status": "unknown"}
    assert result["objects"]["proposed-A"]["sanity"] == {"status": "plausible"}
    assert result["objects"]["contradicted-B"]["outcome"] == "blocked_by_sanity"
    assert result["objects"]["contradicted-B"]["identity"] is None
    assert mem == before
    assert "identity" not in mem and "identity_recall" not in mem


def test_identity_consumer_exclusion_removes_seed_from_scoring_and_envelope():
    mem = two_identity_memory()
    result = squint_pipeline._identity_readings(
        {"query": located((1, 0, 0), "B")}, mem, "sb"
    )
    reading = result["objects"]["query"]
    assert result["preparation"]["exclude_study_uid"] == "sb"
    assert result["preparation"]["seed_count"] == 1
    assert [case["case_id"] for case in reading["cases"]] == ["a1"]
    assert reading["cases"][0]["envelope"] is None
    assert reading["outcome"] == "proposal"
    assert reading["identity"] is None


def test_identity_consumer_non_signal_seed_metadata_changes_lineage_not_signal():
    base = two_identity_memory()
    changed = copy.deepcopy(base)
    teaching = changed["object_identity_teaching"]
    teaching["reader_sha256"] = "reader-new"
    teaching["source_sha256"] = "source-new"
    teaching["review_sha256"] = "review-new"
    left = squint_pipeline._identity_readings(
        {"query": located((1, 0, 0), "B")}, base, None
    )["objects"]["query"]
    right = squint_pipeline._identity_readings(
        {"query": located((1, 0, 0), "B")}, changed, None
    )["objects"]["query"]
    assert identity_signal(left) == identity_signal(right)
    assert right["cases"][0]["lineage"]["teaching"]["reader_sha256"] == "reader-new"
    assert right["cases"][0]["lineage"]["teaching"]["source_sha256"] == "source-new"
    assert right["cases"][0]["lineage"]["teaching"]["review_sha256"] == "review-new"


def test_public_infer_study_returns_identity_evidence_at_boundary(monkeypatch):
    from knee.diagnosis import declarations, squint_locator, squint_profiles

    mem = two_identity_memory()
    objects = {"proposed-B": located((1, 0, 0), "B", "plausible")}
    monkeypatch.setattr(declarations, "QUESTIONS", ())
    monkeypatch.setattr(
        squint_profiles,
        "read_study_squints",
        lambda root, uid, io_workers=8: {
            "work": {"raw_read_mocked": True},
            "leg_map_status": "available",
            "leg_maps": {},
        },
    )
    monkeypatch.setattr(
        squint_locator,
        "locate_objects",
        lambda study, memory, **kwargs: {"objects": objects},
    )
    before = copy.deepcopy(mem)

    result = squint_pipeline.infer_study(Path("."), "current-study", mem)

    assert result["schema"] == "knee.squint-study/v1"
    assert result["study_status"] == "examined"
    assert result["identity_recall"]["schema"] == "knee.study-object-identity/v1"
    assert result["identity_recall"]["outcome"] == "examined"
    assert result["identity_recall"]["objects"]["proposed-B"]["identity"] == "A"
    assert result["questions"] == {}
    assert result["values"] == {}
    assert result["work"]["raw_read_mocked"] is True
    assert mem == before
    assert result["identity_recall"]["memory_published"] is False


def test_legacy_unreviewed_memory_stays_named_and_unexamined():
    mem = {"cases": [{"case_id": "auto", "subject": "A"}]}
    result = squint_pipeline._identity_readings(
        {"query": located((1, 0, 0), "A")}, mem, None
    )
    assert result == {"outcome": "unreviewed_candidate_memory", "objects": {}}
    assert mem == {"cases": [{"case_id": "auto", "subject": "A"}]}


def test_identity_consumer_hears_negative_cases_and_excludes_their_study():
    from test_squint_identity import rejected_a_memory, sag

    mem = rejected_a_memory()
    objects = {
        "proposed-A": {
            "profile": sag((1, 2, 0)),
            "sanity": sanity("unknown"),
            "status": "located",
            "regions": [],
        }
    }
    before = copy.deepcopy(mem)
    result = squint_pipeline._identity_readings(objects, mem, None)
    assert result["preparation"]["negative_case_count"] == 1
    reading = result["objects"]["proposed-A"]
    assert reading["outcome"] == "unresolved_conflict"
    assert reading["conflicted_identities"] == ["A"]
    assert [row["case_id"] for row in reading["negative_cases"]] == ["n1"]
    assert result["memory_published"] is False
    assert mem == before
    # The capacity path: the study-excluded population, then the excluded uid.
    view, _evidence = squint_pipeline._study_excluded_memory(mem, "sn")
    assert view["object_identity_cases"]["cases"] == []
    held = squint_pipeline._identity_readings(objects, view, "sn")
    assert held["preparation"]["negative_case_count"] == 0
    assert held["objects"]["proposed-A"]["identity"] == "A"
    assert held["objects"]["proposed-A"]["negative_cases"] == []
