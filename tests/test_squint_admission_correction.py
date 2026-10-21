"""Two-sign intent of reviewing a growth round's admissions on their pictures.

CLASSICAL_AI_BUILD_DESIGN §§5, 7, 7.1 and 13 step 5, and the OpenSpec change
``complete-signed-bootstrap-loop``: the first round's admissions are inspected
before its child becomes the next parent, and a wrong admission returns as a
scoped corrected negative. An admission holds a cheap profile, its regions and
recognition-derived lineage, and no full profile; none is required or made. A
reject becomes an ordinary negative identity case of its proposed identity on
exactly its called views, and the case stops speaking as a positive. A confirm is
recorded and changes nothing: a recognition-derived case does not become an
independent confirmation. Unsure changes nothing. Each test pins one meaning in
both signs through direct calls to the shared API, the identity reader, the
growth round and the CLI.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from knee.diagnosis import squint_identity_growth
from knee.diagnosis.squint_bootstrap import (
    ADMISSION_RECORD_SCHEMA,
    ADMISSION_REVIEW_SCHEMA,
    CALLS_SCHEMA,
    CORRECTION_KIND,
    CORRECTION_SCHEMA,
    RECOGNITION_KIND,
    REVIEW_SCHEMA,
    SquintBootstrapError,
    build_admission_review,
    build_review,
    publish_admission_corrections,
    publish_seed_memory,
    round_admissions,
    validate_calls,
)
from knee.diagnosis.squint_identity import prepare_identity, recall_identity
from knee.diagnosis.squint_identity_growth import (
    CHILD_DIRECTORY,
    DECISIONS_FILE,
    READER,
    admission_decision,
    candidates_from_memory,
    exclusion_studies,
    grow_identity_memory,
    harvest_candidates,
)
from knee.diagnosis.squint_memory import (
    _full_profile_from_validated_case,
    load_memory,
    load_memory_snapshot,
)
from knee.diagnosis.squint_memory_view import memory_view
from tests.test_squint_admission_sheets import series_record
from tests.test_squint_identity_growth import (
    COR,
    FE,
    SAG,
    WINDOW,
    identity_memory,
    plausible,
    profile,
    saved,
    study_record,
)

# The growth suite's signed parent over a catalogue with portable full payloads
# (every H5 product deleted). Imported, it is registered here as a fixture of this
# name, which the test that needs it requests by name.
from tests.test_squint_identity_growth import signed as catalogue_parent  # noqa: F401

pytest.importorskip("matplotlib")

ROOT = Path(__file__).resolve().parents[1]
VIEW_FIELDS = ("orientation", "fluid_sensitive", "fat_suppression")
SERIES = {"series-sag": SAG, "series-cor": COR}
REVIEWER = "lead visual review (Claude Code), fixture"

# A femur and a tibia seed on both views; each one's opposing envelope is 4/5.
SEEDS = (
    ("a1", "femur", "sa", [(SAG, (3, 0, 0)), (COR, (3, 0, 0))]),
    ("t1", "tibia", "st", [(SAG, (2, 1, 0)), (COR, (2, 1, 0))]),
)
# An earlier reviewer rejected this sagittal support as femur.
EARLIER_NEGATIVE = ("n1", "femur", "sn", [(SAG, (1, 2, 0))], [SAG])
# Two femur candidates the frozen parent identifies on both views.
X_BANKS = [(SAG, (4, 0, 1)), (COR, (4, 0, 1))]
W_BANKS = [(SAG, (5, 0, 1)), (COR, (5, 0, 1))]
# A fresh femur candidate the corrected child identifies, with no negative against it.
Z_BANKS = [(SAG, (3, 0, 0)), (COR, (3, 0, 0))]


def _load():
    path = ROOT / "scripts" / "squint_object_bootstrap.py"
    spec = importlib.util.spec_from_file_location(
        "squint_object_bootstrap_admissions", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MOD = _load()


def view_dict(view: list[str]) -> dict[str, str]:
    return dict(zip(VIEW_FIELDS, view, strict=True))


def located_on_both_views(subject: str, by_view) -> dict:
    """A located object as infer_study writes it, read on a sagittal and a coronal series."""
    return {
        "status": "proposal",
        "profile": profile(subject, by_view),
        "regions": [
            {"series_uid": uid, "view": view_dict(view), "window": list(WINDOW)}
            for uid, view in SERIES.items()
        ],
        "sanity": plausible(subject),
        "evidence": {"source": "fixture"},
    }


def records(*studies: tuple[str, list]) -> list[dict]:
    return [
        study_record(uid, {"femur": located_on_both_views("femur", by_view)})
        for uid, by_view in studies
    ]


@pytest.fixture
def grown(tmp_path: Path) -> SimpleNamespace:
    """A frozen signed parent and the child its one growth round published.

    The round admits two femur candidates, x (study sx) and w (study sw), each
    on its coronal and sagittal views.
    """
    parent = saved(
        tmp_path, "parent", identity_memory(SEEDS, negatives=[EARLIER_NEGATIVE])
    )
    receipt = grow_identity_memory(
        parent,
        harvest_candidates(records(("sx", X_BANKS), ("sw", W_BANKS))),
        tmp_path / "round-1",
    )
    assert receipt["outcome"] == "published"
    x, w = receipt["admitted_case_ids"]
    assert x.startswith("located:sx:femur:") and w.startswith("located:sw:femur:")
    child = load_memory_snapshot(tmp_path / "round-1" / CHILD_DIRECTORY)
    return SimpleNamespace(root=tmp_path, parent=parent, child=child, x=x, w=w)


def panel(view: list[str], **states) -> dict:
    return {"view": view_dict(view), "image_state": "read", **states}


def review_of(grown, ids, drawn=None) -> tuple[dict, str]:
    """An admission review whose sheets drew each named view's window; its pin."""
    review = build_admission_review(grown.child.memory, grown.child.sha256, ids)
    for candidate in review["candidates"]:
        views = (drawn or {}).get(candidate["candidate_id"], [SAG, COR])
        candidate["evidence"] = {
            "panels": [panel(view, window_state="drawn") for view in views]
        }
    pin = hashlib.sha256(json.dumps(review, sort_keys=True).encode("utf-8")).hexdigest()
    return review, pin


def calls_of(pin: str, *rows: dict, reader: str = REVIEWER) -> dict:
    return {
        "schema": CALLS_SCHEMA,
        "review_sha256": pin,
        "reader": reader,
        "calls": list(rows),
    }


def row(candidate_id: str, call: str, **extra) -> dict:
    return {"candidate_id": candidate_id, "call": call, "notes": "pictured", **extra}


def publish(grown, rows, name, drawn=None):
    review, pin = review_of(grown, [grown.x, grown.w], drawn)
    result = publish_admission_corrections(
        grown.child, review, calls_of(pin, *rows), pin, grown.root / name
    )
    return result, load_memory(grown.root / name)


def object_ids(memory: dict) -> list[str]:
    return [case["case_id"] for case in memory["cases"]]


def code_of(fn, *args, **kwargs) -> str:
    with pytest.raises(SquintBootstrapError) as info:
        fn(*args, **kwargs)
    return info.value.code


def query(by_view) -> dict:
    return profile("femur", by_view)


# ------------------------------------------------------------- the review


def test_the_review_pins_each_admission_without_needing_a_full_profile(grown):
    review = build_admission_review(
        grown.child.memory, grown.child.sha256, [grown.x, grown.w]
    )
    assert review["schema"] == ADMISSION_REVIEW_SCHEMA
    assert review["source_manifest_sha256"] == grown.child.sha256
    by_id = {case["case_id"]: case for case in grown.child.memory["cases"]}
    for candidate in review["candidates"]:
        case = by_id[candidate["candidate_id"]]
        assert "full_profile" not in case and "full_profile" not in candidate
        assert candidate["profile"] == case["profile"]
        assert candidate["regions"] == case["regions"]
        assert candidate["identity_growth"] == case["identity_growth"]
        assert candidate["identity_growth"]["independent_confirmation"] is False
        assert candidate["admitted_views"] == [COR, SAG]
        assert candidate["profile_views"] == [COR, SAG]
        assert candidate["admission_call"]["reader"] == READER
    # A seed teacher, not an admission, has no place on this review.
    assert (
        code_of(build_admission_review, grown.child.memory, grown.child.sha256, ["a1"])
        == "candidate_not_recognition_derived"
    )
    # The seed review still needs a full profile, so it cannot take an admission.
    assert (
        code_of(build_review, grown.child.memory, grown.child.sha256, [grown.x])
        == "full_profile_ref_missing"
    )


def test_round_admissions_names_what_no_longer_stands(grown):
    chosen = round_admissions(grown.child.memory)
    assert (chosen["round_index"], chosen["round_count"]) == (0, 1)
    assert chosen["standing"] == [grown.x, grown.w]
    assert chosen["not_standing"] == []
    assert chosen["parent_manifest_sha256"] == grown.parent.sha256
    _, corrected = publish(grown, [row(grown.x, "reject", views=[SAG])], "corrected")
    after = round_admissions(corrected)
    assert after["standing"] == [grown.w]
    assert after["not_standing"] == [
        {"case_id": grown.x, "reason": "corrected_negative"}
    ]
    assert code_of(round_admissions, grown.parent.memory) == (
        "memory_has_no_growth_round"
    )
    assert code_of(round_admissions, grown.child.memory, round_index=1) == (
        "growth_round_unknown"
    )


# ------------------------------------------- reject, confirm and unsure


def test_a_rejected_admission_becomes_a_scoped_negative_and_a_confirm_does_not(grown):
    reviewed = grown.child.memory
    teaching = reviewed["object_identity_teaching"]
    result, corrected = publish(
        grown,
        [row(grown.x, "reject", views=[SAG]), row(grown.w, "confirm")],
        "corrected",
    )
    assert result["corrected_case_ids"] == [grown.x]
    assert result["confirmed_admission_ids"] == [grown.w]
    assert result["negative_views"] == {grown.x: [SAG]}
    # Reject: the whole case leaves the positive side for the negative one.
    assert grown.x not in object_ids(corrected)
    [record] = [
        r
        for r in corrected["object_identity_cases"]["cases"]
        if r["case_id"] == grown.x
    ]
    assert "full_profile" not in record
    new = corrected["object_identity_teaching"]
    assert grown.x not in new["confirmed_case_ids"]
    assert new["negative_case_ids"] == ["n1", grown.x]
    assert new["negative_views"][grown.x] == [SAG]
    [stored] = [r for r in new["calls"] if r["candidate_id"] == grown.x]
    assert (stored["call"], stored["views"], stored["reader"]) == (
        "reject",
        [SAG],
        REVIEWER,
    )
    assert stored["correction"]["kind"] == CORRECTION_KIND
    # Confirm: the admission stays exactly as its round wrote it, row and all.
    by_id = {case["case_id"]: case for case in reviewed["cases"]}
    [kept] = [case for case in corrected["cases"] if case["case_id"] == grown.w]
    assert kept == by_id[grown.w]
    [w_row] = [r for r in new["calls"] if r["candidate_id"] == grown.w]
    [w_before] = [r for r in teaching["calls"] if r["candidate_id"] == grown.w]
    assert w_row == w_before and w_row["reader"] == READER
    assert grown.w in new["confirmed_case_ids"]
    assert grown.w not in new["negative_case_ids"]
    # The confirmation is recorded, beside the reader, not written into the case.
    [record_entry] = new["admission_reviews"]
    assert record_entry["schema"] == ADMISSION_RECORD_SCHEMA
    assert record_entry["confirmed_admission_ids"] == [grown.w]
    assert record_entry["corrected_case_ids"] == [grown.x]
    assert record_entry["reader"] == REVIEWER
    assert record_entry["confirm_effect"] == (
        "recorded_only_recognition_derived_lineage_kept"
    )


def test_unsure_changes_nothing_and_unsure_alone_publishes_nothing(grown):
    _, corrected = publish(
        grown,
        [row(grown.x, "reject", views=[SAG]), row(grown.w, "unsure")],
        "with-unsure",
    )
    by_id = {case["case_id"]: case for case in grown.child.memory["cases"]}
    [kept] = [case for case in corrected["cases"] if case["case_id"] == grown.w]
    assert kept == by_id[grown.w]
    [record_entry] = corrected["object_identity_teaching"]["admission_reviews"]
    assert record_entry["unsure_case_ids"] == [grown.w]
    assert record_entry["confirmed_admission_ids"] == []
    review, pin = review_of(grown, [grown.x, grown.w])
    out = grown.root / "unsure-only"
    assert (
        code_of(
            publish_admission_corrections,
            grown.child,
            review,
            calls_of(pin, row(grown.x, "unsure"), row(grown.w, "unsure")),
            pin,
            out,
        )
        == "no_admission_calls_applied"
    )
    assert not out.exists()


def test_a_confirm_only_review_publishes_the_same_identity_teaching(grown):
    result, confirmed = publish(
        grown, [row(grown.x, "confirm"), row(grown.w, "confirm")], "confirmed"
    )
    reviewed = grown.child.memory
    assert confirmed["cases"] == reviewed["cases"]
    assert confirmed["object_identity_cases"] == reviewed["object_identity_cases"]
    before = dict(prepare_identity(reviewed))
    after = result["identity_preparation"]
    for key in ("seed_count", "negative_case_count"):
        assert after[key] == before[key]
    teaching = confirmed["object_identity_teaching"]
    assert teaching["calls"] == reviewed["object_identity_teaching"]["calls"]
    assert teaching["admission_reviews"][0]["confirmed_admission_ids"] == [
        grown.x,
        grown.w,
    ]


# ---------------------------------------------------------------- scope


def test_the_negative_holds_exactly_the_called_views_not_every_drawn_view(grown):
    _, scoped = publish(grown, [row(grown.x, "reject", views=[SAG])], "scoped")
    _, whole = publish(grown, [row(grown.x, "reject")], "whole")
    _, partly = publish(
        grown, [row(grown.x, "reject")], "partly-drawn", drawn={grown.x: [SAG]}
    )
    assert scoped["object_identity_teaching"]["negative_views"][grown.x] == [SAG]
    # Without views a reject covers every drawn profile view, as on a seed review.
    assert whole["object_identity_teaching"]["negative_views"][grown.x] == [COR, SAG]
    assert partly["object_identity_teaching"]["negative_views"][grown.x] == [SAG]
    sagittal = profile("femur", [(SAG, (4, 0, 1))])["banks"]
    both = profile("femur", X_BANKS)["banks"]
    for memory, banks in ((scoped, sagittal), (whole, both), (partly, sagittal)):
        prepared = prepare_identity(memory)
        [negative] = [n for n in prepared._negatives if n["case_id"] == grown.x]
        assert set(negative["banks"]) == set(banks)
    # A reject naming a view whose window was not drawn is refused, never widened.
    review, pin = review_of(grown, [grown.x], drawn={grown.x: [SAG]})
    out = grown.root / "not-drawn"
    assert (
        code_of(
            publish_admission_corrections,
            grown.child,
            review,
            calls_of(pin, row(grown.x, "reject", views=[COR])),
            pin,
            out,
        )
        == "view_not_drawn"
    )
    assert not out.exists()


# --------------------------------------------------- speaking, both signs


def test_the_corrected_case_stops_speaking_as_a_positive_and_the_other_still_speaks(
    grown,
):
    like_x = query(X_BANKS)
    before = recall_identity(like_x, grown.child.memory)
    speaking = {r["case_id"] for r in before["cases"] if r["speaks"]}
    assert grown.x in speaking
    _, corrected = publish(grown, [row(grown.x, "reject", views=[SAG])], "corrected")
    after = recall_identity(like_x, corrected)
    assert grown.x not in {r["case_id"] for r in after["cases"]}
    [against] = [r for r in after["negative_cases"] if r["case_id"] == grown.x]
    assert (against["digit"], against["speaks"]) == (-1, True)
    assert after["outcome"] == "unresolved_conflict"
    assert after["conflicted_identities"] == ["femur"]
    # The admission no reviewer corrected still speaks for its identity.
    like_w = recall_identity(query(W_BANKS), corrected)
    [w_row] = [r for r in like_w["cases"] if r["case_id"] == grown.w]
    assert w_row["speaks"] is True and w_row["identity"] == "femur"
    assert w_row["lineage"]["call"]["reader"] == READER


def test_the_identity_reader_meets_the_negative_on_its_views_only(grown):
    before = prepare_identity(grown.child.memory)
    _, corrected = publish(grown, [row(grown.x, "reject", views=[SAG])], "corrected")
    prepared = prepare_identity(corrected)
    assert prepared["seed_count"] == before["seed_count"] - 1
    assert prepared["negative_case_count"] == before["negative_case_count"] + 1
    # A query resembling the corrected case on its sagittal view meets the -1.
    sagittal = recall_identity(query([(SAG, (4, 0, 1))]), corrected, prepared=prepared)
    [against] = [r for r in sagittal["negative_cases"] if r["case_id"] == grown.x]
    assert (against["digit"], against["speaks"]) == (-1, True)
    assert against["envelope_status"] == "above_envelope"
    assert against["views"] == [SAG]
    assert against["lineage"]["call"]["reader"] == REVIEWER
    # A query outside its views shares no bank with it, and it says nothing.
    coronal = recall_identity(query([(COR, (4, 0, 1))]), corrected, prepared=prepared)
    assert grown.x not in {r["case_id"] for r in coronal["negative_cases"]}
    # The same query meets no negative of x on the reviewed child, where x is +1.
    plain = recall_identity(query([(SAG, (4, 0, 1))]), grown.child.memory)
    assert grown.x not in {r["case_id"] for r in plain["negative_cases"]}


# ------------------------------------------------- what the child keeps


def test_every_other_record_of_the_reviewed_memory_survives_unchanged(grown):
    reviewed = copy.deepcopy(grown.child.memory)
    teaching = reviewed["object_identity_teaching"]
    result, corrected = publish(
        grown, [row(grown.x, "reject", views=[SAG])], "corrected"
    )
    # The reviewed memory is untouched, in memory and on disk.
    assert grown.child.memory == reviewed
    assert load_memory_snapshot(grown.child.path).sha256 == grown.child.sha256
    assert corrected["cases"] == [
        case for case in reviewed["cases"] if case["case_id"] != grown.x
    ]
    parent_records = reviewed["object_identity_cases"]["cases"]
    child_records = corrected["object_identity_cases"]["cases"]
    assert child_records[: len(parent_records)] == parent_records
    new = corrected["object_identity_teaching"]
    for position, before in enumerate(teaching["calls"]):
        after = new["calls"][position]
        if before["candidate_id"] == grown.x:
            assert after["call"] == "reject"
        else:
            assert after == before
    assert len(new["calls"]) == len(teaching["calls"])
    assert new["confirmed_case_ids"] == [
        case_id for case_id in teaching["confirmed_case_ids"] if case_id != grown.x
    ]
    assert new["negative_views"]["n1"] == teaching["negative_views"]["n1"]
    for key in ("reader", "schema"):
        assert new[key] == teaching[key]
    assert corrected["object_identity_growth"] == reviewed["object_identity_growth"]
    assert corrected["questions"] == reviewed["questions"]
    assert corrected["revision"].startswith(reviewed["revision"] + "+admission-review-")
    assert result["revision"] == corrected["revision"]
    # The moved record is the admission as it was, plus who corrected it.
    by_id = {case["case_id"]: case for case in reviewed["cases"]}
    [record] = [r for r in child_records if r["case_id"] == grown.x]
    assert {k: v for k, v in record.items() if k != "identity_correction"} == (
        by_id[grown.x]
    )
    assert record["identity_growth"]["kind"] == RECOGNITION_KIND
    assert record["identity_growth"]["independent_confirmation"] is False
    correction = record["identity_correction"]
    assert correction["schema"] == CORRECTION_SCHEMA
    assert correction["corrected_by"] == REVIEWER
    assert correction["negative_views"] == [SAG]
    assert correction["reviewed_manifest_sha256"] == grown.child.sha256
    [superseded] = [r for r in teaching["calls"] if r["candidate_id"] == grown.x]
    assert correction["superseded_call"] == superseded
    assert superseded["reader"] == READER
    assert new["admission_reviews"][0]["superseded_calls"] == [superseded]


def test_held_out_exclusion_and_the_next_round_hear_the_correction(grown):
    _, corrected = publish(grown, [row(grown.x, "reject", views=[SAG])], "corrected")
    snapshot = load_memory_snapshot(grown.root / "corrected")
    assert "sx" in exclusion_studies(corrected)
    held_out = prepare_identity(corrected, exclude_study_uid="sx")
    assert held_out["negative_case_count"] == 1  # only the earlier n1
    view = memory_view(corrected, exclude_study_uids=("sx",))
    assert grown.x not in {r["case_id"] for r in view["object_identity_cases"]["cases"]}
    # A next round on the corrected child: a candidate like x now meets its -1.
    [like_x] = harvest_candidates(records(("sy", X_BANKS)))
    decision = admission_decision(like_x, corrected)["decision"]
    assert (decision["state"], decision["reason"]) == (
        "conflict",
        "identity_spoken_for_and_against",
    )
    # On the reviewed child, before the correction, the same candidate is admitted.
    assert admission_decision(like_x, grown.child.memory)["decision"]["state"] == (
        "admitted"
    )
    # And x's own object is held, so it never returns as a positive of itself.
    [again] = harvest_candidates(records(("sx", X_BANKS)))
    assert admission_decision(again, corrected)["decision"]["reason"] == (
        "case_id_already_in_parent"
    )
    receipt = grow_identity_memory(snapshot, [like_x, again], grown.root / "round-2")
    assert receipt["state_counts"] == {"conflict": 1, "duplicate": 1}
    assert [p.name for p in (grown.root / "round-2").iterdir()] == [DECISIONS_FILE]


def test_the_corrected_child_parents_a_published_round_that_keeps_the_correction(
    grown,
):
    """The corrected child is the next parent, and its grandchild keeps the -1."""
    publish(grown, [row(grown.x, "reject", views=[SAG])], "corrected")
    corrected = load_memory_snapshot(grown.root / "corrected")
    receipt = grow_identity_memory(
        corrected, harvest_candidates(records(("sz", Z_BANKS))), grown.root / "round-2"
    )
    assert receipt["outcome"] == "published"
    [z] = receipt["admitted_case_ids"]
    assert z.startswith("located:sz:femur:")
    grandchild = load_memory_snapshot(grown.root / "round-2" / CHILD_DIRECTORY).memory
    assert z in object_ids(grandchild) and grown.x not in object_ids(grandchild)
    parent_records = corrected.memory["object_identity_cases"]["cases"]
    assert grandchild["object_identity_cases"]["cases"] == parent_records
    teaching = grandchild["object_identity_teaching"]
    assert teaching["negative_views"][grown.x] == [SAG]
    assert grown.x in teaching["negative_case_ids"]
    assert (
        teaching["admission_reviews"]
        == (corrected.memory["object_identity_teaching"]["admission_reviews"])
    )
    [x_row] = [r for r in teaching["calls"] if r["candidate_id"] == grown.x]
    assert (x_row["call"], x_row["views"], x_row["reader"]) == (
        "reject",
        [SAG],
        REVIEWER,
    )
    rounds = grandchild["object_identity_growth"]["rounds"]
    assert [entry["parent_manifest_sha256"] for entry in rounds] == [
        grown.parent.sha256,
        corrected.sha256,
    ]
    # The next reader still meets the corrected case's -1 on its sagittal view.
    prepared = prepare_identity(grandchild)
    assert prepared["negative_case_count"] == 2
    heard = recall_identity(query([(SAG, (4, 0, 1))]), grandchild, prepared=prepared)
    [against] = [r for r in heard["negative_cases"] if r["case_id"] == grown.x]
    assert (against["digit"], against["speaks"]) == (-1, True)


# --------------------------------------------------------------- refusals


def test_admission_calls_refuse_a_split_of_the_recognition_derived_row(grown):
    review, pin = review_of(grown, [grown.x])
    for extra, code in (
        (
            {"views": [COR], "negative_views": [SAG]},
            "admission_negative_views_unsupported",
        ),
        (
            {"also_positive": [{"identity": "tibia", "views": [SAG]}]},
            "admission_also_positive_unsupported",
        ),
    ):
        call = "confirm" if "negative_views" in extra else "reject"
        calls = calls_of(pin, row(grown.x, call, **extra))
        assert code_of(validate_calls, review, calls, pin) == code
    # A reject with no drawn view to name is refused, not left to change nothing.
    review, pin = review_of(grown, [grown.x], drawn={grown.x: []})
    assert (
        code_of(validate_calls, review, calls_of(pin, row(grown.x, "reject")), pin)
        == "admission_reject_has_no_drawn_view"
    )


def test_a_window_and_a_support_never_stand_in_for_each_other(grown):
    # On an admission review a drawn support is not a drawn window.
    review, pin = review_of(grown, [grown.x])
    review["candidates"][0]["evidence"] = {
        "panels": [panel(SAG, support_state="drawn")]
    }
    calls = calls_of(pin, row(grown.x, "reject", views=[SAG]))
    assert code_of(validate_calls, review, calls, pin) == "view_not_drawn"
    review["candidates"][0]["evidence"] = {"panels": [panel(SAG, window_state="drawn")]}
    assert validate_calls(review, calls, pin)["negative_views"] == {grown.x: [SAG]}
    # On a seed review a drawn window is not a drawn support.
    seed_review = {
        "schema": REVIEW_SCHEMA,
        "source_manifest_sha256": "b" * 64,
        "candidates": [
            {
                "candidate_id": "seed-c",
                "case_id": "seed-c",
                "study_uid": "study-c",
                "subject": "femur",
                "profile_sha256": "c" * 64,
                "source_product_sha256": "d" * 64,
                "full_profile": {
                    "payload_ref": "payload-c",
                    "context_ref": "context-c",
                    "product_record_sha256": "e" * 64,
                },
                "profile_views": [SAG],
                "evidence": {"panels": [panel(SAG, window_state="drawn")]},
            }
        ],
    }
    seed_calls = calls_of(pin, row("seed-c", "reject", views=[SAG]))
    assert code_of(validate_calls, seed_review, seed_calls, pin) == "view_not_drawn"
    seed_review["candidates"][0]["evidence"] = {
        "panels": [panel(SAG, support_state="drawn")]
    }
    assert validate_calls(seed_review, seed_calls, pin)["negative_views"] == {
        "seed-c": [SAG]
    }


def test_each_publisher_refuses_the_other_review_and_stale_or_unsafe_inputs(grown):
    review, pin = review_of(grown, [grown.x])
    calls = calls_of(pin, row(grown.x, "reject", views=[SAG]))
    out = grown.root / "child"
    assert (
        code_of(publish_seed_memory, grown.child, review, calls, pin, out)
        == "review_malformed"
    )
    seed_review = {**review, "schema": REVIEW_SCHEMA}
    assert (
        code_of(
            publish_admission_corrections, grown.child, seed_review, calls, pin, out
        )
        == "review_malformed"
    )
    # Reviewed from another memory: refused before anything is written.
    assert (
        code_of(publish_admission_corrections, grown.parent, review, calls, pin, out)
        == "stale_source_pin"
    )
    assert (
        code_of(
            publish_admission_corrections,
            grown.child,
            review,
            calls,
            pin,
            grown.child.path.parent / "inside",
        )
        == "output_path_unsafe"
    )
    out.mkdir()
    assert (
        code_of(publish_admission_corrections, grown.child, review, calls, pin, out)
        == "output_exists"
    )
    assert not any(out.iterdir())


def test_a_corrected_admission_cannot_be_reviewed_again(grown):
    publish(grown, [row(grown.x, "reject", views=[SAG])], "corrected")
    corrected = load_memory_snapshot(grown.root / "corrected")
    assert (
        code_of(build_admission_review, corrected.memory, corrected.sha256, [grown.x])
        == "unknown_candidate"
    )
    # The remaining admission can still be reviewed on the corrected child.
    review = build_admission_review(corrected.memory, corrected.sha256, [grown.w])
    assert [c["candidate_id"] for c in review["candidates"]] == [grown.w]


def test_the_lineage_kind_is_the_growth_module_own():
    assert RECOGNITION_KIND == squint_identity_growth.RECOGNITION_KIND


def test_a_memory_candidate_admission_keeps_its_full_profile_through_correction(
    request,
):
    """An admission taken from a catalogue holds its paired full profile.

    The review pins it, and after a reject the moved record still reads its full
    profile offline from the child's own tables (no H5 product is left).
    """
    signed = request.getfixturevalue("catalogue_parent")
    receipt = grow_identity_memory(
        signed.parent,
        candidates_from_memory(
            signed.catalogue,
            candidate_ids=[FE],
            sanity_by_case_id={FE: plausible("femur")},
        ),
        signed.root / "from-memory",
    )
    assert receipt["admitted_case_ids"] == [FE]
    child = load_memory_snapshot(signed.root / "from-memory" / CHILD_DIRECTORY)
    review = build_admission_review(child.memory, child.sha256, [FE])
    [candidate] = review["candidates"]
    [case] = [c for c in child.memory["cases"] if c["case_id"] == FE]
    assert candidate["full_profile"] == case["full_profile"]
    candidate["evidence"] = {
        "panels": [panel(view, window_state="drawn") for view in (SAG, COR)]
    }
    pin = hashlib.sha256(json.dumps(review, sort_keys=True).encode("utf-8")).hexdigest()
    out = signed.root / "corrected"
    result = publish_admission_corrections(
        child, review, calls_of(pin, row(FE, "reject", views=[COR])), pin, out
    )
    assert result["corrected_case_ids"] == [FE]
    corrected = load_memory(out)
    [record] = [
        r for r in corrected["object_identity_cases"]["cases"] if r["case_id"] == FE
    ]
    full = _full_profile_from_validated_case(
        corrected, record, record["full_profile"], record["subject"]
    )
    assert full.source_id == "study-e"
    assert corrected["full_profile_payloads"] == child.memory["full_profile_payloads"]
    assert corrected["object_identity_teaching"]["negative_views"][FE] == [COR]
    # Its condition calls leave condition recall with it: no wrong tissue answers ACL.
    assert FE not in object_ids(corrected)
    assert record["condition_calls"] == case["condition_calls"]


def test_a_recorded_source_window_is_the_window_the_sheet_draws():
    window = [0, 1, 0, 2, 0, 2]
    regions = [
        {"series_uid": "s1", "source_window": window, "view": {"orientation": "x"}},
        {"series_uid": "s2", "window": [1, 2, 0, 1, 0, 1], "source_window": window},
        "not a region",
    ]
    drawn = MOD._admission_sheet_regions(regions)
    assert drawn[0] == {**regions[0], "window": window}
    assert drawn[1] == regions[1]  # a recorded window is never replaced
    assert drawn[2] == "not a region"  # passed on, and named on its sheet
    assert MOD._admission_sheet_regions(None) == []


# --------------------------------------------------------------------- CLI


def study_reader(log: list):
    def read(root, study_uid, *, tile_mm, io_workers):
        log.append(study_uid)
        edges = (0, 7, 14, 21)
        return {
            "schema": "knee.squint-study/v1",
            "study_uid": study_uid,
            "series": [
                series_record(uid, view_dict(view), 2, edges, edges, (7, 7))
                for uid, view in SERIES.items()
            ],
            "work": {"series_count": 2},
        }

    return read


def export(grown, name: str, **options):
    log: list = []
    out = grown.root / name
    result = MOD.export_admission_review(
        grown.child.memory,
        grown.child.sha256,
        grown.root / "competition",
        out,
        study_reader=study_reader(log),
        **options,
    )
    return SimpleNamespace(out=out, result=result, log=log)


def test_export_draws_each_admission_window_and_admit_applies_the_calls(grown):
    exported = export(grown, "review")
    out = exported.out
    assert exported.log == ["sw", "sx"]  # each study read once, in sorted order
    raw = (out / "review.json").read_bytes()
    pin = hashlib.sha256(raw).hexdigest()
    review = json.loads(raw)
    assert exported.result["review_sha256"] == pin
    assert review["schema"] == ADMISSION_REVIEW_SCHEMA
    assert review["selection"]["rule"] == MOD.ADMISSION_SELECTION_RULE
    assert review["selection"]["admitted_case_ids"] == [grown.x, grown.w]
    assert [c["candidate_id"] for c in review["candidates"]] == [grown.w, grown.x]
    for candidate in review["candidates"]:
        evidence = candidate["evidence"]
        assert evidence["evidence_kind"] == "squint_tile_window"
        assert {
            tuple(p["view"][field] for field in VIEW_FIELDS) for p in evidence["panels"]
        } == {tuple(SAG), tuple(COR)}
        assert {p["window_state"] for p in evidence["panels"]} == {"drawn"}
        assert "support_state" not in evidence["panels"][0]
        data = (out / candidate["sheet_path"]).read_bytes()
        assert data[:8] == bytes.fromhex("89504e470d0a1a0a")
        assert hashlib.sha256(data).hexdigest() == evidence["sheet"]["sha256"]
    MOD.verify_sheets(review, out)
    template = json.loads((out / "calls.json").read_text(encoding="utf-8"))
    assert (template["review_sha256"], template["calls"]) == (pin, [])
    index = (out / "index.md").read_text(encoding="utf-8")
    assert "recognition-derived, not a visual call" in index and pin in index
    calls = calls_of(pin, row(grown.x, "reject", views=[SAG]), row(grown.w, "confirm"))
    (out / "my-calls.json").write_text(json.dumps(calls), encoding="utf-8")
    result = MOD.main(
        [
            "admit",
            "--memory",
            str(grown.child.path.parent),
            "--review",
            str(out / "review.json"),
            "--calls",
            str(out / "my-calls.json"),
            "--output",
            str(grown.root / "corrected"),
        ]
    )
    assert result["corrected_case_ids"] == [grown.x]
    assert result["confirmed_admission_ids"] == [grown.w]
    corrected = load_memory(grown.root / "corrected")
    assert corrected["object_identity_teaching"]["negative_views"][grown.x] == [SAG]
    assert grown.x not in object_ids(corrected)


def test_export_refuses_by_name_and_writes_nothing(grown):
    out = grown.root / "taken"
    out.mkdir()
    with pytest.raises(MOD.ObjectBootstrapError) as info:
        export(grown, "taken")
    assert info.value.code == "export_output_exists"
    with pytest.raises(SquintBootstrapError) as shared:
        export(grown, "seed-case", case_ids=["a1"])
    assert shared.value.code == "candidate_not_recognition_derived"
    assert not (grown.root / "seed-case").exists()
    publish(grown, [row(grown.x, "reject", views=[SAG]), row(grown.w, "reject")], "all")
    corrected = load_memory_snapshot(grown.root / "all")
    with pytest.raises(MOD.ObjectBootstrapError) as info:
        MOD.export_admission_review(
            corrected.memory,
            corrected.sha256,
            grown.root,
            grown.root / "nothing-stands",
            study_reader=study_reader([]),
        )
    assert info.value.code == "no_standing_admissions"
    assert "corrected_negative" in info.value.detail
    assert not (grown.root / "nothing-stands").exists()


def test_adapt_keeps_a_recorded_reject_scope_on_an_admission_review(grown):
    exported = export(grown, "review")
    pin = exported.result["review_sha256"]
    recorded = exported.out / "recorded.jsonl"
    recorded.write_text(
        json.dumps(
            {
                "candidate_id": grown.x,
                "call": "reject",
                "notes": "posterior soft tissue, sagittal",
                "negative_views": [SAG],
                "number": 3,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = MOD.main(
        [
            "adapt",
            "--review",
            str(exported.out / "review.json"),
            "--jsonl",
            str(recorded),
            REVIEWER,
            "--output",
            str(grown.root / "adapted"),
        ]
    )
    assert (result["negative"], result["review_sha256"]) == (1, pin)
    adapted = json.loads((grown.root / "adapted" / "calls.json").read_text())
    [call] = adapted["calls"]
    assert (call["views"], call["reader"]) == ([SAG], REVIEWER)
    assert "negative_views" not in call
