"""Intent checks for composing actual growth publications into training rounds."""

from __future__ import annotations

import copy
import hashlib
import json

import pytest

from knee.diagnosis.squint_bootstrap import (
    CALLS_SCHEMA,
    build_admission_review,
    publish_admission_corrections,
)
from knee.diagnosis.squint_identity_growth import IdentityGrowthError
from knee.diagnosis.squint_memory import load_memory_snapshot, save_memory
from knee.json_store import dump_json_atomic
from scripts import squint_round_composition as composition
from tests.test_squint_admission_correction import calls_of, review_of, row
from tests.test_squint_identity_growth import (
    NEGATIVE,
    ROUND_SEEDS,
    SAG,
    identity_memory,
    located,
    placed,
    plausible,
    saved,
    study_record,
    unknown,
)


def inference(tmp_path, parent, *, uid="sx", anatomy=None):
    directory = tmp_path / "inference"
    (directory / "studies").mkdir(parents=True)
    record = study_record(
        uid,
        {"femur": located("femur", [(SAG, (4, 0, 1))], anatomy or plausible("femur"))},
        revision=parent.memory["revision"],
        contexts={"femur": placed("femur", "tibia")},
    )
    path = dump_json_atomic(directory / "studies" / f"{uid}.json.xz", record)
    # The production run stores this beside observations. It is not an MRI record.
    (directory / "studies" / f"{uid}.pin.json").write_text('{"schema":"checkpoint"}')
    receipt = {
        "action": "infer",
        "memory_revision": parent.memory["revision"],
        "memory_manifest_sha256": parent.sha256,
        "work": {
            "studies": [
                {"study_uid": uid, "evidence_path": str(path.relative_to(directory))}
            ]
        },
    }
    (directory / "receipt.json").write_text(json.dumps(receipt))
    return directory, path


def parent_memory(tmp_path):
    return saved(tmp_path, "parent", identity_memory(ROUND_SEEDS))


def review(growth, receipt, destination, *, only_first=False):
    document = build_admission_review(
        growth.memory, growth.sha256, receipt["admitted_case_ids"]
    )
    digest = hashlib.sha256(json.dumps(document).encode()).hexdigest()
    calls = {
        "schema": CALLS_SCHEMA,
        "review_sha256": digest,
        "reader": "fixture visual reviewer",
        "calls": [
            {"candidate_id": cid, "call": "confirm", "notes": "fixture inspection"}
            for cid in (
                receipt["admitted_case_ids"][:1]
                if only_first
                else receipt["admitted_case_ids"]
            )
        ],
    }
    publish_admission_corrections(growth, document, calls, digest, destination)
    return load_memory_snapshot(destination)


def test_growth_uses_receipt_records_and_waits_for_first_admission_review(tmp_path):
    parent = parent_memory(tmp_path)
    directory, record = inference(tmp_path, parent)
    stage = composition.stage_identity_growth(parent, [directory], tmp_path / "stage")
    assert stage.status == "admission_review_required"
    assert stage.snapshot is None
    assert stage.receipt["state_counts"] == {"admitted": 1}
    growth = load_memory_snapshot(tmp_path / "stage" / "identity-growth" / "memory")
    assert growth.memory is not None
    added = [case for case in growth.memory["cases"] if case["study_uid"] == "sx"]
    assert len(added) == 1
    assert added[0]["identity_growth"]["parent_manifest_sha256"] == parent.sha256
    assert added[0]["identity_growth"]["independent_confirmation"] is False
    assert (
        added[0]["identity_growth"]["source"]["record_sha256"]
        == hashlib.sha256(record.read_bytes()).hexdigest()
    )
    assert added[0]["identity_growth"]["source"]["record_sha256_scope"] == "file_bytes"
    assert "direct_visual_teaching" not in added[0]
    assert not (tmp_path / "stage" / "memory").exists()


def test_reviewed_child_is_the_actual_composition_parent_and_resume_reuses_growth(
    tmp_path, monkeypatch
):
    parent = parent_memory(tmp_path)
    directory, _ = inference(tmp_path, parent)
    path = tmp_path / "stage"
    pending = composition.stage_identity_growth(parent, [directory], path)
    growth = load_memory_snapshot(path / "identity-growth" / "memory")
    reviewed = review(growth, pending.receipt, tmp_path / "reviewed")

    def no_second_growth(*args, **kwargs):
        raise AssertionError("identical observations must not be scored twice")

    monkeypatch.setattr(composition, "grow_identity_memory", no_second_growth)
    accepted = composition.stage_identity_growth(
        parent, [directory], path, reviewed_memory=tmp_path / "reviewed"
    )
    assert accepted.status == "ready_to_compose"
    assert accepted.snapshot is not None
    assert accepted.snapshot.memory is not None
    assert accepted.snapshot.sha256 == reviewed.sha256
    assert accepted.snapshot.sha256 != growth.sha256
    # The human review does not rewrite the observation's generating parent.
    added = next(
        case for case in accepted.snapshot.memory["cases"] if case["study_uid"] == "sx"
    )
    assert added["identity_growth"]["parent_manifest_sha256"] == parent.sha256
    assert (
        accepted.snapshot.memory["object_identity_teaching"]["admission_reviews"][-1][
            "reviewed_manifest_sha256"
        ]
        == growth.sha256
    )


def test_loading_the_unreviewed_publication_cannot_impersonate_review(tmp_path):
    parent = parent_memory(tmp_path)
    directory, _ = inference(tmp_path, parent)
    path = tmp_path / "stage"
    composition.stage_identity_growth(parent, [directory], path)
    with pytest.raises(
        composition.RoundCompositionError, match="admission_review_incomplete"
    ):
        composition.stage_identity_growth(
            parent,
            [directory],
            path,
            reviewed_memory=path / "identity-growth" / "memory",
        )


def test_a_round_without_admissions_composes_on_the_original_parent(tmp_path):
    parent = parent_memory(tmp_path)
    directory, _ = inference(tmp_path, parent, anatomy=unknown("femur"))
    stage = composition.stage_identity_growth(parent, [directory], tmp_path / "stage")
    assert stage.status == "ready_to_compose"
    assert stage.snapshot is parent
    assert stage.receipt["outcome"] == "no_admissions"
    assert not (tmp_path / "stage" / "identity-growth" / "memory").exists()


def test_mutated_observation_cannot_resume_the_old_growth(tmp_path):
    parent = parent_memory(tmp_path)
    directory, record = inference(tmp_path, parent)
    path = tmp_path / "stage"
    composition.stage_identity_growth(parent, [directory], path)
    record.write_bytes(record.read_bytes() + b"changed")
    with pytest.raises(
        composition.RoundCompositionError, match="composition_inputs_changed"
    ):
        composition.stage_identity_growth(parent, [directory], path)


def test_a_different_generating_parent_is_refused_before_a_growth_output(tmp_path):
    parent = parent_memory(tmp_path)
    directory, _ = inference(tmp_path, parent)
    receipt_path = directory / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["memory_manifest_sha256"] = "f" * 64
    receipt_path.write_text(json.dumps(receipt))
    with pytest.raises(
        composition.RoundCompositionError, match="inference_generating_parent_mismatch"
    ):
        composition.stage_identity_growth(parent, [directory], tmp_path / "stage")
    assert not (tmp_path / "stage").exists()


def test_held_out_parent_teaching_is_never_dropped_to_make_growth_possible(tmp_path):
    parent = parent_memory(tmp_path)
    directory, _ = inference(tmp_path, parent)
    with pytest.raises(IdentityGrowthError, match="held_out_study_teaches_parent"):
        composition.stage_identity_growth(
            parent, [directory], tmp_path / "stage", held_out=["sa"]
        )
    assert not (tmp_path / "stage" / "identity-growth").exists()
    assert load_memory_snapshot(tmp_path / "parent").sha256 == parent.sha256


def test_incomplete_growth_publication_is_named_and_never_overwritten(tmp_path):
    parent = parent_memory(tmp_path)
    directory, _ = inference(tmp_path, parent)
    output = tmp_path / "stage"
    (output / "identity-growth").mkdir(parents=True)
    marker = output / "identity-growth" / "keep.txt"
    marker.write_text("keep incomplete evidence")
    with pytest.raises(
        composition.RoundCompositionError, match="growth_checkpoint_incomplete"
    ):
        composition.stage_identity_growth(parent, [directory], output)
    assert marker.read_text() == "keep incomplete evidence"


def test_review_selection_without_a_call_does_not_count_as_inspection(tmp_path):
    parent = parent_memory(tmp_path)
    first, _ = inference(tmp_path / "first", parent, uid="sx")
    second, _ = inference(tmp_path / "second", parent, uid="sy")
    path = tmp_path / "stage"
    pending = composition.stage_identity_growth(parent, [first, second], path)
    assert len(pending.receipt["admitted_case_ids"]) == 2
    growth = load_memory_snapshot(path / "identity-growth" / "memory")
    review(growth, pending.receipt, tmp_path / "partly-reviewed", only_first=True)
    with pytest.raises(
        composition.RoundCompositionError, match="admission_review_incomplete"
    ):
        composition.stage_identity_growth(
            parent, [first, second], path, reviewed_memory=tmp_path / "partly-reviewed"
        )


def test_composition_keeps_scoped_negative_cases_and_calls_verbatim(tmp_path):
    parent = saved(
        tmp_path, "parent", identity_memory(ROUND_SEEDS, negatives=(NEGATIVE,))
    )
    directory, _ = inference(tmp_path, parent)
    stage = composition.stage_identity_growth(
        parent, [directory], tmp_path / "stage", require_admission_review=False
    )
    assert stage.status == "ready_to_compose"
    assert stage.snapshot is not None
    assert stage.snapshot.memory is not None
    child = stage.snapshot.memory
    assert child["object_identity_cases"] == parent.memory["object_identity_cases"]
    assert (
        child["object_identity_teaching"]["negative_views"]
        == parent.memory["object_identity_teaching"]["negative_views"]
    )
    assert (
        child["object_identity_teaching"]["calls"][
            : len(parent.memory["object_identity_teaching"]["calls"])
        ]
        == parent.memory["object_identity_teaching"]["calls"]
    )


def test_copying_the_review_onto_an_unrelated_valid_memory_does_not_make_a_continuation(
    tmp_path,
):
    parent = parent_memory(tmp_path)
    directory, _ = inference(tmp_path, parent)
    path = tmp_path / "stage"
    pending = composition.stage_identity_growth(parent, [directory], path)
    growth = load_memory_snapshot(path / "identity-growth" / "memory")
    reviewed = review(growth, pending.receipt, tmp_path / "reviewed")
    foreign = copy.deepcopy(reviewed.memory)
    foreign["revision"] += "-unrelated"
    foreign["cases"] = [case for case in foreign["cases"] if case["case_id"] != "t1"]
    teaching = foreign["object_identity_teaching"]
    teaching["confirmed_case_ids"].remove("t1")
    teaching["calls"] = [
        call for call in teaching["calls"] if call["candidate_id"] != "t1"
    ]
    save_memory(foreign, tmp_path / "foreign")
    with pytest.raises(
        composition.RoundCompositionError, match="reviewed_child_lost_parent_case"
    ):
        composition.stage_identity_growth(
            parent, [directory], path, reviewed_memory=tmp_path / "foreign"
        )


def test_existing_reviewed_reject_remains_a_scoped_negative_in_composed_child(tmp_path):
    parent = parent_memory(tmp_path)
    directory, _ = inference(tmp_path, parent)
    path = tmp_path / "stage"
    pending = composition.stage_identity_growth(parent, [directory], path)
    growth = load_memory_snapshot(path / "identity-growth" / "memory")
    cid = pending.receipt["admitted_case_ids"][0]
    document, digest = review_of(growth, [cid])
    calls = calls_of(digest, row(cid, "reject", views=[SAG]))
    publish_admission_corrections(
        growth, document, calls, digest, tmp_path / "corrected"
    )
    ready = composition.stage_identity_growth(
        parent, [directory], path, reviewed_memory=tmp_path / "corrected"
    )
    assert ready.status == "ready_to_compose"
    assert ready.snapshot is not None and ready.snapshot.memory is not None
    memory = ready.snapshot.memory
    assert cid not in [case["case_id"] for case in memory["cases"]]
    assert memory["object_identity_teaching"]["negative_views"][cid] == [SAG]
    negative = next(
        case
        for case in memory["object_identity_cases"]["cases"]
        if case["case_id"] == cid
    )
    assert negative["identity_growth"]["parent_manifest_sha256"] == parent.sha256


def test_first_round_requires_every_call_but_later_spot_check_applies_its_real_correction(
    tmp_path,
):
    parent = saved(
        tmp_path, "parent", identity_memory(ROUND_SEEDS, negatives=(NEGATIVE,))
    )
    first, _ = inference(tmp_path / "first", parent, uid="sx")
    second, _ = inference(tmp_path / "second", parent, uid="sy")
    path = tmp_path / "stage"
    pending = composition.stage_identity_growth(parent, [first, second], path)
    growth = load_memory_snapshot(path / "identity-growth" / "memory")
    rejected, unreviewed = pending.receipt["admitted_case_ids"]
    document, digest = review_of(growth, [rejected, unreviewed])
    calls = calls_of(digest, row(rejected, "reject", views=[SAG]))
    publish_admission_corrections(
        growth, document, calls, digest, tmp_path / "spot-reviewed"
    )
    with pytest.raises(
        composition.RoundCompositionError, match="admission_review_incomplete"
    ):
        composition.stage_identity_growth(
            parent,
            [first, second],
            path,
            reviewed_memory=tmp_path / "spot-reviewed",
        )
    later = composition.stage_identity_growth(
        parent,
        [first, second],
        path,
        reviewed_memory=tmp_path / "spot-reviewed",
        require_admission_review=False,
    )
    assert later.status == "ready_to_compose"
    assert later.snapshot is not None and later.snapshot.memory is not None
    memory = later.snapshot.memory
    assert rejected not in [case["case_id"] for case in memory["cases"]]
    kept = next(case for case in memory["cases"] if case["case_id"] == unreviewed)
    assert kept["identity_growth"]["independent_confirmation"] is False
    assert kept["identity_growth"]["parent_manifest_sha256"] == parent.sha256
    assert memory["object_identity_teaching"]["negative_views"][rejected] == [SAG]
    assert memory["object_identity_teaching"]["negative_views"]["n1"] == [SAG]
    inherited = parent.memory["object_identity_cases"]["cases"]
    assert memory["object_identity_cases"]["cases"][: len(inherited)] == inherited
