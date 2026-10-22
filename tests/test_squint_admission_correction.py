"""Two-sign intent of reviewing a growth round's admissions on their pictures.

CLASSICAL_AI_BUILD_DESIGN §§5, 7, 7.1 and 13 step 5, and the OpenSpec change
``complete-signed-bootstrap-loop``: the first round's admissions are inspected
before its child becomes the next parent, and a wrong admission returns as a
scoped corrected negative. An admission holds a cheap profile, its regions and
recognition-derived lineage, and no full profile; none is required or made.

Rohan, relayed by the lead: «Preserve unaffected positive facets and lineage; apply
the correction only where asserted. Retain the existing ability to express scoped
positive, negative and alternative-identity calls.» A call applies only where it
asserts, in the seed path's own forms: a rejected view (or a confirm's
``negative_views``) becomes an ordinary negative identity case on exactly that
view, an ``also_positive`` view a positive of the named identity, and every other
admitted view keeps speaking for the proposed identity, with its recognition-derived
lineage and its condition evidence. Only when every admitted view is rejected does
the whole case move. A confirm is otherwise recorded and changes nothing: a
recognition-derived case does not become an independent confirmation. Unsure
changes nothing. Each test pins one meaning in both signs through direct calls to
the shared API, the identity reader, condition recall, the growth round and the CLI.
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

from knee.diagnosis import squint_bootstrap, squint_identity_growth
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
from knee.diagnosis.squint_identity import (
    identity_condition_views,
    prepare_identity,
    recall_identity,
)
from knee.diagnosis.squint_identity_growth import (
    CHILD_DIRECTORY,
    DECISIONS_FILE,
    READER,
    admission_decision,
    exclusion_studies,
    grow_identity_memory,
    harvest_candidates,
)
from knee.diagnosis.squint_locator import prepare_recall, recall_object
from knee.diagnosis.squint_memory import (
    _full_profile_from_validated_case,
    load_memory,
    load_memory_snapshot,
    save_memory,
)
from knee.diagnosis.squint_memory_view import memory_view
from tests.test_squint_admission_sheets import series_record
from tests.test_squint_identity_growth import (
    COR,
    FE,
    SAG,
    WINDOW,
    _labels_csv,
    _memory_items,
    bank,
    identity_memory,
    placed,
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
AXIAL = ["Axial", "0", "0"]
VIEW_FIELDS = ("orientation", "fluid_sensitive", "fat_suppression")
SERIES = {"series-sag": SAG, "series-cor": COR}
SERIES_OF = {
    tuple(SAG): "series-sag",
    tuple(COR): "series-cor",
    tuple(AXIAL): "series-ax",
}
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
# A femur candidate with an axial reading no seed shares: admitted coronally and
# sagittally, its axial view is drawn but never asserted.
V_BANKS = [(SAG, (4, 0, 1)), (COR, (4, 0, 1)), (AXIAL, (2, 2, 2))]
# A fresh femur candidate a corrected child identifies, with no negative against it.
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


def located(subject: str, by_view) -> dict:
    """A located object as infer_study writes it, read on one series per view."""
    return {
        "status": "proposal",
        "profile": profile(subject, by_view),
        "regions": [
            {
                "series_uid": SERIES_OF[tuple(view)],
                "view": view_dict(view),
                "window": list(WINDOW),
            }
            for view, _ in by_view
        ],
        "sanity": plausible(subject),
        "evidence": {"source": "fixture"},
    }


def records(*studies: tuple[str, list]) -> list[dict]:
    """Inference records, each femur placed by the anatomy map with the tibia open."""
    return [
        study_record(
            uid,
            {"femur": located("femur", by_view)},
            contexts={"femur": placed("femur", "tibia")},
        )
        for uid, by_view in studies
    ]


def grow(tmp_path: Path, name: str, studies, labels=None) -> SimpleNamespace:
    """A frozen signed parent and the child its one growth round published."""
    parent = saved(
        tmp_path,
        f"{name}-parent",
        identity_memory(SEEDS, negatives=[EARLIER_NEGATIVE]),
    )
    receipt = grow_identity_memory(
        parent, harvest_candidates(records(*studies)), tmp_path / name, labels=labels
    )
    assert receipt["outcome"] == "published"
    child = load_memory_snapshot(tmp_path / name / CHILD_DIRECTORY)
    return SimpleNamespace(
        root=tmp_path, parent=parent, child=child, ids=receipt["admitted_case_ids"]
    )


@pytest.fixture
def grown(tmp_path: Path) -> SimpleNamespace:
    """Two femur admissions, x (study sx) and w (study sw), each coronal and sagittal."""
    made = grow(tmp_path, "round-1", [("sx", X_BANKS), ("sw", W_BANKS)])
    made.x, made.w = made.ids
    assert made.x.startswith("located:sx:femur:")
    assert made.w.startswith("located:sw:femur:")
    return made


@pytest.fixture
def labelled(tmp_path: Path) -> SimpleNamespace:
    """The same round with train.csv carried: x an ACL positive, w an ACL normal."""
    labels = _labels_csv(tmp_path / "train.csv", {"sx": {"ACL": 1}, "sw": {"ACL": 0}})
    made = grow(tmp_path, "labelled", [("sx", X_BANKS), ("sw", W_BANKS)], labels=labels)
    made.x, made.w = made.ids
    return made


@pytest.fixture
def axial(tmp_path: Path) -> SimpleNamespace:
    """One femur admission v whose drawn axial view the admission never asserted."""
    made = grow(tmp_path, "axial", [("sv", V_BANKS)])
    (made.v,) = made.ids
    return made


def panel(view: list[str], **states) -> dict:
    return {"view": view_dict(view), "image_state": "read", **states}


def review_of(child, ids, drawn=None) -> tuple[dict, str]:
    """An admission review whose sheets drew each named view's window; its pin.

    Every profile view is drawn unless ``drawn`` names a candidate's views.
    """
    review = build_admission_review(child.memory, child.sha256, ids)
    for candidate in review["candidates"]:
        views = (drawn or {}).get(candidate["candidate_id"], candidate["profile_views"])
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


def publish(made, rows, name, drawn=None):
    """Review the called admissions of ``made.child`` and publish the calls."""
    ids = list(dict.fromkeys(item["candidate_id"] for item in rows))
    review, pin = review_of(made.child, ids, drawn)
    result = publish_admission_corrections(
        made.child, review, calls_of(pin, *rows), pin, made.root / name
    )
    return result, load_memory(made.root / name), pin


def object_ids(memory: dict) -> list[str]:
    return [case["case_id"] for case in memory["cases"]]


def call_row(memory: dict, case_id: str) -> dict:
    [found] = [
        item
        for item in memory["object_identity_teaching"]["calls"]
        if item["candidate_id"] == case_id
    ]
    return found


def identity_record(memory: dict, case_id: str) -> dict:
    [found] = [
        item
        for item in memory["object_identity_cases"]["cases"]
        if item["case_id"] == case_id
    ]
    return found


def entries(prepared, case_id: str, *, negative: bool = False) -> list:
    population = prepared._negatives if negative else prepared._seeds
    return [entry for entry in population if entry["case_id"] == case_id]


def speaking(recall: dict, case_id: str, *, negative: bool = False) -> bool:
    rows = recall["negative_cases"] if negative else recall["cases"]
    return any(item["case_id"] == case_id and item["speaks"] for item in rows)


def code_of(fn, *args, **kwargs) -> str:
    with pytest.raises(SquintBootstrapError) as info:
        fn(*args, **kwargs)
    return info.value.code


def query(by_view, subject: str = "femur") -> dict:
    return profile(subject, by_view)


SAG_QUERY = [(SAG, (4, 0, 1))]
COR_QUERY = [(COR, (4, 0, 1))]


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
    _, split, _ = publish(grown, [row(grown.x, "reject", views=[SAG])], "split")
    after = round_admissions(split)
    assert after["standing"] == [grown.w]
    assert after["not_standing"] == [
        {"case_id": grown.x, "reason": "admission_corrected_in_part"}
    ]
    _, whole, _ = publish(grown, [row(grown.x, "reject")], "whole")
    assert round_admissions(whole)["not_standing"] == [
        {"case_id": grown.x, "reason": "corrected_negative"}
    ]
    assert code_of(round_admissions, grown.parent.memory) == (
        "memory_has_no_growth_round"
    )
    assert code_of(round_admissions, grown.child.memory, round_index=1) == (
        "growth_round_unknown"
    )


# ---------------------------------------------- a correction where asserted


def test_a_sagittal_reject_keeps_the_coronal_positive_and_scopes_the_negative(grown):
    reviewed = grown.child.memory
    by_id = {case["case_id"]: case for case in reviewed["cases"]}
    admission_row = call_row(reviewed, grown.x)
    # The reviewed child holds no -1 of x for a sagittal query.
    assert not speaking(
        recall_identity(query(SAG_QUERY), reviewed), grown.x, negative=True
    )
    result, split, _ = publish(grown, [row(grown.x, "reject", views=[SAG])], "split")
    assert (result["corrected_case_ids"], result["whole_case_ids"]) == ([grown.x], [])
    assert result["corrections"][grown.x]["effect"] == "facets"
    # The case stays in cases, confirmed and unchanged; only its row narrows, in the
    # seed path's mixed form, keeping its recognition-derived reader and mark.
    [kept] = [case for case in split["cases"] if case["case_id"] == grown.x]
    assert kept == by_id[grown.x]
    teaching = split["object_identity_teaching"]
    assert grown.x in teaching["confirmed_case_ids"]
    assert call_row(split, grown.x) == {
        **admission_row,
        "views": [COR],
        "negative_views": [SAG],
    }
    assert teaching["negative_views"][grown.x] == [SAG]
    # The coronal positive still speaks for a coronal query.
    coronal = recall_identity(query(COR_QUERY), split)
    [positive] = [item for item in coronal["cases"] if item["case_id"] == grown.x]
    assert (positive["identity"], positive["speaks"]) == ("femur", True)
    assert positive["common_speaking_banks"] == [bank(COR)]
    assert coronal["identity"] == "femur"
    assert not speaking(coronal, grown.x, negative=True)
    # The sagittal -1 speaks for a sagittal query, and x speaks for nothing there.
    sagittal = recall_identity(query(SAG_QUERY), split)
    [against] = [
        item for item in sagittal["negative_cases"] if item["case_id"] == grown.x
    ]
    assert (against["digit"], against["speaks"], against["views"]) == (-1, True, [SAG])
    assert not speaking(sagittal, grown.x)


def test_a_whole_reject_still_moves_the_whole_case(grown):
    for name, call in (
        ("every-drawn-view", row(grown.x, "reject")),
        ("every-admitted-view", row(grown.x, "reject", views=[COR, SAG])),
    ):
        result, whole, _ = publish(grown, [call], name)
        assert result["whole_case_ids"] == [grown.x]
        assert result["corrections"][grown.x]["effect"] == "whole_case"
        assert grown.x not in object_ids(whole)
        teaching = whole["object_identity_teaching"]
        assert grown.x not in teaching["confirmed_case_ids"]
        assert teaching["negative_views"][grown.x] == [COR, SAG]
        assert call_row(whole, grown.x) == {**call, "reader": REVIEWER}
        prepared = prepare_identity(whole)
        assert entries(prepared, grown.x) == []
        [negative] = entries(prepared, grown.x, negative=True)
        assert set(negative["banks"]) == {bank(COR), bank(SAG)}
        # The coronal positive a scoped reject keeps is gone with the whole case.
        coronal = recall_identity(query(COR_QUERY), whole, prepared=prepared)
        assert grown.x not in {item["case_id"] for item in coronal["cases"]}


def test_a_labelled_admission_keeps_its_condition_evidence_through_coronal_only(
    labelled,
):
    reviewed = labelled.child.memory
    [case] = [item for item in reviewed["cases"] if item["case_id"] == labelled.x]
    assert case["condition_calls"] == {"ACL": 1}
    assert identity_condition_views(reviewed)["views"][labelled.x] == frozenset(
        {tuple(COR), tuple(SAG)}
    )

    def heard(memory, by_view):
        prepared = prepare_recall(memory)
        assert prepared["outcome"] == "prepared"
        return recall_object(
            query(by_view), {**memory, "prepared_recall": prepared}, "ACL"
        )

    _, split, _ = publish(labelled, [row(labelled.x, "reject", views=[SAG])], "split")
    # Not removed: the case and its carried calls stay, scoped to the coronal view.
    [kept] = [item for item in split["cases"] if item["case_id"] == labelled.x]
    assert kept == case
    assert identity_condition_views(split)["views"][labelled.x] == frozenset(
        {tuple(COR)}
    )
    coronal = heard(split, COR_QUERY)
    assert coronal["outcome"] == "present"
    assert coronal["speaking_case_ids"] == [labelled.x]
    [term] = [item for item in coronal["case_terms"] if item["case_id"] == labelled.x]
    assert (term["call"], term["common_speaking_banks"]) == (1, [bank(COR)])
    # The rejected sagittal facet carries no condition evidence.
    sagittal = heard(split, SAG_QUERY)
    assert labelled.x in sagittal["silent_case_ids"]
    assert all(item["case_id"] != labelled.x for item in sagittal["case_terms"])
    assert sagittal["outcome"] != "present"
    # A whole reject removes the case and every bit of its condition evidence.
    _, whole, _ = publish(labelled, [row(labelled.x, "reject")], "whole")
    assert labelled.x not in identity_condition_views(whole)["views"]
    gone = heard(whole, COR_QUERY)
    assert all(item["case_id"] != labelled.x for item in gone["case_terms"])
    assert gone["outcome"] != "present"


def test_a_reject_on_an_unasserted_view_leaves_the_positive(axial):
    reviewed = axial.child.memory
    admission_row = call_row(reviewed, axial.v)
    assert admission_row["views"] == [COR, SAG]
    [before] = entries(prepare_identity(reviewed), axial.v)
    _, corrected, _ = publish(
        axial, [row(axial.v, "reject", views=[AXIAL])], "unasserted"
    )
    assert axial.v in object_ids(corrected)
    assert call_row(corrected, axial.v) == {**admission_row, "negative_views": [AXIAL]}
    prepared = prepare_identity(corrected)
    [after] = entries(prepared, axial.v)
    assert dict(after["banks"]) == dict(before["banks"])
    [negative] = entries(prepared, axial.v, negative=True)
    assert set(negative["banks"]) == {bank(AXIAL)}
    assert identity_condition_views(corrected)["views"][axial.v] == frozenset(
        {tuple(COR), tuple(SAG)}
    )
    # A reject on an asserted view takes that view from the positive instead.
    _, taken, _ = publish(axial, [row(axial.v, "reject", views=[SAG])], "taken")
    [narrowed] = entries(prepare_identity(taken), axial.v)
    assert set(narrowed["banks"]) == {bank(COR)}


def test_also_positive_gives_its_facet_to_the_other_identity(grown):
    alternative = [{"identity": "tibia", "views": [SAG]}]
    result, given, _ = publish(
        grown,
        [row(grown.x, "reject", views=[SAG], also_positive=alternative)],
        "given",
    )
    entry_id = f"{grown.x}::also_positive::tibia"
    assert result["corrections"][grown.x]["alternative_positive_ids"] == [entry_id]
    assert call_row(given, grown.x)["also_positive"] == alternative
    assert given["object_identity_teaching"]["alternative_positives"] == [
        {"entry_id": entry_id, "case_id": grown.x, "identity": "tibia", "views": [SAG]}
    ]
    prepared = prepare_identity(given)
    [seed] = entries(prepared, entry_id)
    assert (seed["subject"], set(seed["banks"])) == ("tibia", {bank(SAG)})
    # The sagittal facet is now the tibia's; the coronal facet stays the femur's.
    sagittal = recall_identity(query(SAG_QUERY), given, prepared=prepared)
    assert speaking(sagittal, entry_id)
    assert sagittal["identity"] == "tibia"
    coronal = recall_identity(query(COR_QUERY), given, prepared=prepared)
    assert coronal["identity"] == "femur" and speaking(coronal, grown.x)
    # Without also_positive the same reject gives the facet to no identity.
    _, plain, _ = publish(grown, [row(grown.x, "reject", views=[SAG])], "plain")
    assert entries(prepare_identity(plain), entry_id) == []
    assert recall_identity(query(SAG_QUERY), plain)["identity"] is None
    # A whole reject can give a facet away too: the case moves, the facet stays given.
    _, moved, _ = publish(
        grown, [row(grown.x, "reject", also_positive=alternative)], "moved-and-given"
    )
    assert grown.x not in object_ids(moved)
    assert call_row(moved, grown.x)["call"] == "reject"
    prepared = prepare_identity(moved)
    [seed] = entries(prepared, entry_id)
    assert (seed["subject"], set(seed["banks"])) == ("tibia", {bank(SAG)})
    [negative] = entries(prepared, grown.x, negative=True)
    assert set(negative["banks"]) == {bank(COR), bank(SAG)}


def test_a_confirm_with_negative_views_corrects_its_facets_and_is_recorded(grown):
    confirm = row(grown.x, "confirm", views=[COR], negative_views=[SAG])
    result, confirmed, _ = publish(grown, [confirm], "confirmed")
    _, rejected, _ = publish(grown, [row(grown.x, "reject", views=[SAG])], "rejected")
    assert result["confirmed_admission_ids"] == [grown.x]
    assert result["corrections"][grown.x]["effect"] == "facets"
    # The same facets move as with a sagittal reject; the confirm is recorded only.
    assert call_row(confirmed, grown.x) == call_row(rejected, grown.x)
    assert call_row(confirmed, grown.x)["reader"] == READER
    for memory in (confirmed, rejected):
        prepared = prepare_identity(memory)
        assert {
            name for entry in entries(prepared, grown.x) for name in entry["banks"]
        } == {bank(COR)}
        [negative] = entries(prepared, grown.x, negative=True)
        assert set(negative["banks"]) == {bank(SAG)}
    [record_entry] = confirmed["object_identity_teaching"]["admission_reviews"]
    assert record_entry["confirmed_admission_ids"] == [grown.x]
    assert (
        rejected["object_identity_teaching"]["admission_reviews"][0][
            "confirmed_admission_ids"
        ]
        == []
    )


def test_the_negative_facet_names_its_reviewer_and_the_positive_keeps_its_lineage(
    grown,
):
    _, split, pin = publish(grown, [row(grown.x, "reject", views=[SAG])], "split")
    prepared = prepare_identity(split)
    [positive] = entries(prepared, grown.x)
    [negative] = entries(prepared, grown.x, negative=True)
    # The positive facet is still the recognition's: its row and no reviewer.
    assert positive["lineage"]["call"]["reader"] == READER
    assert "reader" not in positive["lineage"]["case"]
    # The negative facet names the reviewer through its identity record.
    assert negative["lineage"]["case"]["reader"] == REVIEWER
    assert negative["lineage"]["case"]["review_sha256"] == pin
    record = identity_record(split, grown.x)
    assert (record["reader"], record["review_sha256"]) == (REVIEWER, pin)
    assert record["identity_correction"]["corrected_by"] == REVIEWER
    # The rows the reader shares between the two facets stay the recognition's.
    assert negative["lineage"]["call"] == call_row(split, grown.x)
    # A whole-case correction's row is the reviewer's own.
    _, whole, _ = publish(grown, [row(grown.x, "reject")], "whole")
    [moved] = entries(prepare_identity(whole), grown.x, negative=True)
    assert moved["lineage"]["call"]["reader"] == REVIEWER
    assert moved["lineage"]["case"]["reader"] == REVIEWER
    # A facet given to another identity names the reviewer the same way.
    alternative = [{"identity": "tibia", "views": [SAG]}]
    _, given, given_pin = publish(
        grown,
        [row(grown.x, "reject", views=[SAG], also_positive=alternative)],
        "given",
    )
    [seed] = entries(prepare_identity(given), f"{grown.x}::also_positive::tibia")
    assert seed["lineage"]["case"]["reader"] == REVIEWER
    assert seed["lineage"]["case"]["review_sha256"] == given_pin


# ---------------------------------------------------------------- scope


def test_the_negative_holds_exactly_the_called_views_not_every_drawn_view(grown):
    _, scoped, _ = publish(grown, [row(grown.x, "reject", views=[SAG])], "scoped")
    _, whole, _ = publish(grown, [row(grown.x, "reject")], "whole")
    _, partly, _ = publish(
        grown, [row(grown.x, "reject")], "partly-drawn", drawn={grown.x: [SAG]}
    )
    assert scoped["object_identity_teaching"]["negative_views"][grown.x] == [SAG]
    # Without views a reject covers every drawn profile view, as on a seed review.
    assert whole["object_identity_teaching"]["negative_views"][grown.x] == [COR, SAG]
    assert partly["object_identity_teaching"]["negative_views"][grown.x] == [SAG]
    for memory, negative_banks, positive_banks in (
        (scoped, {bank(SAG)}, {bank(COR)}),
        (whole, {bank(COR), bank(SAG)}, None),
        # The undrawn coronal view was not called: it keeps speaking.
        (partly, {bank(SAG)}, {bank(COR)}),
    ):
        prepared = prepare_identity(memory)
        [negative] = entries(prepared, grown.x, negative=True)
        assert set(negative["banks"]) == negative_banks
        seeds = entries(prepared, grown.x)
        if positive_banks is None:
            assert seeds == []
        else:
            [seed] = seeds
            assert set(seed["banks"]) == positive_banks
    # A reject naming a view whose window was not drawn is refused, never widened.
    review, pin = review_of(grown.child, [grown.x], drawn={grown.x: [SAG]})
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


def test_unsure_changes_nothing_and_unsure_alone_publishes_nothing(grown):
    _, corrected, _ = publish(
        grown,
        [row(grown.x, "reject", views=[SAG]), row(grown.w, "unsure")],
        "with-unsure",
    )
    by_id = {case["case_id"]: case for case in grown.child.memory["cases"]}
    [kept] = [case for case in corrected["cases"] if case["case_id"] == grown.w]
    assert kept == by_id[grown.w]
    assert call_row(corrected, grown.w) == call_row(grown.child.memory, grown.w)
    [record_entry] = corrected["object_identity_teaching"]["admission_reviews"]
    assert record_entry["unsure_case_ids"] == [grown.w]
    assert record_entry["confirmed_admission_ids"] == []
    review, pin = review_of(grown.child, [grown.x, grown.w])
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
    result, confirmed, _ = publish(
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
    assert result["corrected_case_ids"] == []


# ------------------------------------------------- what the child keeps


@pytest.mark.parametrize("call", ["confirm", "reject"])
def test_correction_publisher_records_its_actual_parent_without_changing_call_scope(
    tmp_path, grown, call
):
    original = copy.deepcopy(grown.child.memory)
    original["parent_revision"] = "grandparent-revision"
    original["parent_manifest_sha256"] = "d" * 64
    parent_directory = tmp_path / "parent-with-historical-lineage"
    save_memory(original, parent_directory)
    source = load_memory_snapshot(parent_directory)
    source_bytes = source.path.read_bytes()
    source_before = copy.deepcopy(source.memory)
    review, pin = review_of(source, [grown.x])
    called = row(grown.x, call, **({"views": [SAG]} if call == "reject" else {}))
    result = publish_admission_corrections(
        source,
        review,
        calls_of(pin, called),
        pin,
        tmp_path / "lineage-corrected-child",
    )

    restored = load_memory_snapshot(tmp_path / "lineage-corrected-child")
    child = restored.memory
    assert restored.sha256 == result["sha256"]
    assert child["parent_revision"] == source_before["revision"]
    assert child["parent_manifest_sha256"] == source.sha256
    assert child["parent_manifest_sha256"] != source_before["parent_manifest_sha256"]
    record = child["object_identity_teaching"]["admission_reviews"][-1]
    assert record["reviewed_revision"] == child["parent_revision"]
    assert record["reviewed_manifest_sha256"] == child["parent_manifest_sha256"]
    assert child["cases"] == source_before["cases"]
    if call == "reject":
        assert child["object_identity_teaching"]["negative_views"][grown.x] == [SAG]
        assert call_row(child, grown.x)["views"] == [COR]
        expected_views = frozenset({tuple(COR)})
    else:
        assert (
            child["object_identity_teaching"]["calls"]
            == source_before["object_identity_teaching"]["calls"]
        )
        assert child["object_identity_cases"] == source_before["object_identity_cases"]
        expected_views = identity_condition_views(source_before)["views"][grown.x]
    assert identity_condition_views(child)["views"][grown.x] == expected_views
    assert source.memory == source_before
    assert source.path.read_bytes() == source_bytes


def test_every_other_record_of_the_reviewed_memory_survives_unchanged(grown):
    reviewed = copy.deepcopy(grown.child.memory)
    teaching = reviewed["object_identity_teaching"]
    result, corrected, pin = publish(
        grown, [row(grown.x, "reject", views=[SAG])], "corrected"
    )
    # The reviewed memory is untouched, in memory and on disk.
    assert grown.child.memory == reviewed
    assert load_memory_snapshot(grown.child.path).sha256 == grown.child.sha256
    # No case changes or leaves; one identity record is added after the others.
    assert corrected["cases"] == reviewed["cases"]
    parent_records = reviewed["object_identity_cases"]["cases"]
    child_records = corrected["object_identity_cases"]["cases"]
    assert child_records[: len(parent_records)] == parent_records
    assert len(child_records) == len(parent_records) + 1
    new = corrected["object_identity_teaching"]
    for position, before in enumerate(teaching["calls"]):
        after = new["calls"][position]
        if before["candidate_id"] == grown.x:
            assert after == {**before, "views": [COR], "negative_views": [SAG]}
        else:
            assert after == before
    assert len(new["calls"]) == len(teaching["calls"])
    assert new["confirmed_case_ids"] == teaching["confirmed_case_ids"]
    assert new["negative_case_ids"] == [*teaching["negative_case_ids"], grown.x]
    assert new["negative_views"]["n1"] == teaching["negative_views"]["n1"]
    assert "alternative_positives" not in new
    for key in ("reader", "schema"):
        assert new[key] == teaching[key]
    assert corrected["object_identity_growth"] == reviewed["object_identity_growth"]
    assert corrected["questions"] == reviewed["questions"]
    assert corrected["revision"].startswith(reviewed["revision"] + "+admission-review-")
    assert result["revision"] == corrected["revision"]
    # The record is the admission as it was, plus who corrected which facet.
    by_id = {case["case_id"]: case for case in reviewed["cases"]}
    record = identity_record(corrected, grown.x)
    added = ("identity_correction", "reader", "review_sha256")
    assert {k: v for k, v in record.items() if k not in added} == by_id[grown.x]
    assert record["identity_growth"]["kind"] == RECOGNITION_KIND
    assert record["identity_growth"]["independent_confirmation"] is False
    correction = record["identity_correction"]
    assert (correction["schema"], correction["kind"]) == (
        CORRECTION_SCHEMA,
        CORRECTION_KIND,
    )
    assert correction["corrected_by"] == REVIEWER
    assert correction["effect"] == "facets"
    assert correction["positive_views_after"] == [COR]
    assert correction["negative_views"] == [SAG]
    assert correction["alternative_positives"] == []
    assert correction["review_sha256"] == pin
    assert correction["reviewed_manifest_sha256"] == grown.child.sha256
    superseded = call_row(reviewed, grown.x)
    assert correction["superseded_call"] == superseded
    assert superseded["reader"] == READER
    [record_entry] = new["admission_reviews"]
    assert record_entry["schema"] == ADMISSION_RECORD_SCHEMA
    assert record_entry["reader"] == REVIEWER
    assert record_entry["corrected_case_ids"] == [grown.x]
    assert record_entry["corrections"][grown.x]["effect"] == "facets"
    assert record_entry["superseded_calls"] == [superseded]
    assert record_entry["confirm_effect"] == (
        "recorded_only_recognition_derived_lineage_kept"
    )


def test_publication_refuses_a_correction_the_reader_would_not_hear_as_called(
    grown, monkeypatch
):
    original = squint_bootstrap._corrected_row

    def dropped_negative(admission_row, effect):
        written = original(admission_row, effect)
        written.pop("negative_views", None)
        return written

    def erased_positive(admission_row, effect):
        return {**effect["call"], "reader": effect["reader"]}

    call = row(grown.x, "reject", views=[SAG])
    for name, wrong in (("dropped", dropped_negative), ("erased", erased_positive)):
        monkeypatch.setattr(squint_bootstrap, "_corrected_row", wrong)
        review, pin = review_of(grown.child, [grown.x])
        out = grown.root / name
        assert (
            code_of(
                publish_admission_corrections,
                grown.child,
                review,
                calls_of(pin, call),
                pin,
                out,
            )
            == "corrected_facets_not_prepared"
        )
        assert not out.exists()
    monkeypatch.setattr(squint_bootstrap, "_corrected_row", original)
    result, _, _ = publish(grown, [call], "heard")
    assert result["outcome"] == "published"


def test_held_out_exclusion_and_the_next_round_hear_the_correction(grown):
    _, corrected, _ = publish(grown, [row(grown.x, "reject", views=[SAG])], "corrected")
    snapshot = load_memory_snapshot(grown.root / "corrected")
    assert "sx" in exclusion_studies(corrected)
    held_out = prepare_identity(corrected, exclude_study_uid="sx")
    assert held_out["negative_case_count"] == 1  # only the earlier n1
    assert entries(held_out, grown.x) == []
    view = memory_view(corrected, exclude_study_uids=("sx",))
    assert grown.x not in object_ids(view)
    assert grown.x not in {r["case_id"] for r in view["object_identity_cases"]["cases"]}
    # A next round on the corrected child: a candidate like x now meets its -1, which
    # applies at 10 mm and opens its identity question; with no finer reading of it,
    # the candidate is never admitted on the squint scale alone.
    [like_x] = harvest_candidates(records(("sy", X_BANKS)))
    scored = admission_decision(like_x, corrected)
    assert grown.x in scored["recall"]["applicable_negative_case_ids"]
    decision = scored["decision"]
    assert (decision["state"], decision["reason"]) == (
        "proposal",
        "squint_contest_unresolved_no_finer_reading",
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
    assert receipt["state_counts"] == {"duplicate": 1, "proposal": 1}
    assert [p.name for p in (grown.root / "round-2").iterdir()] == [DECISIONS_FILE]


def test_the_corrected_child_parents_a_published_round_that_keeps_the_correction(
    grown,
):
    """The corrected child is the next parent, and its grandchild keeps both facets."""
    publish(grown, [row(grown.x, "reject", views=[SAG])], "corrected")
    corrected = load_memory_snapshot(grown.root / "corrected")
    receipt = grow_identity_memory(
        corrected, harvest_candidates(records(("sz", Z_BANKS))), grown.root / "round-2"
    )
    assert receipt["outcome"] == "published"
    [z] = receipt["admitted_case_ids"]
    assert z.startswith("located:sz:femur:")
    grandchild = load_memory_snapshot(grown.root / "round-2" / CHILD_DIRECTORY).memory
    assert z in object_ids(grandchild) and grown.x in object_ids(grandchild)
    parent_records = corrected.memory["object_identity_cases"]["cases"]
    assert grandchild["object_identity_cases"]["cases"] == parent_records
    teaching = grandchild["object_identity_teaching"]
    assert teaching["negative_views"][grown.x] == [SAG]
    assert grown.x in teaching["negative_case_ids"]
    assert grown.x in teaching["confirmed_case_ids"]
    assert (
        teaching["admission_reviews"]
        == (corrected.memory["object_identity_teaching"]["admission_reviews"])
    )
    assert call_row(grandchild, grown.x) == call_row(corrected.memory, grown.x)
    rounds = grandchild["object_identity_growth"]["rounds"]
    assert [entry["parent_manifest_sha256"] for entry in rounds] == [
        grown.parent.sha256,
        corrected.sha256,
    ]
    # The next reader still meets the -1 sagittally and the +1 coronally.
    prepared = prepare_identity(grandchild)
    assert prepared["negative_case_count"] == 2
    sagittal = recall_identity(query(SAG_QUERY), grandchild, prepared=prepared)
    assert speaking(sagittal, grown.x, negative=True)
    coronal = recall_identity(query(COR_QUERY), grandchild, prepared=prepared)
    assert speaking(coronal, grown.x)


# --------------------------------------------------- calls and refusals


def test_admission_calls_keep_their_seed_meanings_and_one_claim_per_view(grown, axial):
    review, pin = review_of(grown.child, [grown.x])
    tibia_sag = [{"identity": "tibia", "views": [SAG]}]
    for call in (
        row(grown.x, "confirm", views=[COR], negative_views=[SAG]),
        row(grown.x, "reject", views=[SAG], also_positive=tibia_sag),
        row(
            grown.x,
            "confirm",
            views=[COR],
            negative_views=[SAG],
            also_positive=tibia_sag,
        ),
    ):
        assert validate_calls(review, calls_of(pin, call), pin)["outcome"] == "valid"
    # A view still speaking for the proposed identity cannot be given to another.
    for call in (
        row(grown.x, "unsure", also_positive=tibia_sag),
        row(
            grown.x,
            "reject",
            views=[SAG],
            also_positive=[{"identity": "tibia", "views": [COR]}],
        ),
    ):
        assert code_of(validate_calls, review, calls_of(pin, call), pin) == (
            "call_views_overlap"
        )
    # A view the admission never asserted can be given, by an unsure as by a seed's.
    v_review, v_pin = review_of(axial.child, [axial.v])
    tibia_axial = [{"identity": "tibia", "views": [AXIAL]}]
    gift = row(axial.v, "unsure", also_positive=tibia_axial)
    assert validate_calls(v_review, calls_of(v_pin, gift), v_pin)["outcome"] == "valid"
    result, given, _ = publish(axial, [gift], "given")
    assert result["corrections"][axial.v]["effect"] == "facets"
    assert call_row(given, axial.v)["views"] == [COR, SAG]
    prepared = prepare_identity(given)
    [seed] = entries(prepared, f"{axial.v}::also_positive::tibia")
    assert (seed["subject"], set(seed["banks"])) == ("tibia", {bank(AXIAL)})
    # A confirm that would leave no admitted view is a reject in all but name.
    leaves_none = row(axial.v, "confirm", views=[AXIAL], negative_views=[COR, SAG])
    assert code_of(validate_calls, v_review, calls_of(v_pin, leaves_none), v_pin) == (
        "admission_confirm_leaves_no_admitted_view"
    )
    # A reject with no drawn view to name is refused, not left to change nothing.
    review, pin = review_of(grown.child, [grown.x], drawn={grown.x: []})
    assert (
        code_of(validate_calls, review, calls_of(pin, row(grown.x, "reject")), pin)
        == "admission_reject_has_no_drawn_view"
    )


def test_a_window_and_a_support_never_stand_in_for_each_other(grown):
    # On an admission review a drawn support is not a drawn window.
    review, pin = review_of(grown.child, [grown.x])
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
    review, pin = review_of(grown.child, [grown.x])
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


def test_a_corrected_admission_is_not_reviewed_again_as_untouched(grown):
    publish(grown, [row(grown.x, "reject", views=[SAG])], "split")
    split = load_memory_snapshot(grown.root / "split")
    assert (
        code_of(build_admission_review, split.memory, split.sha256, [grown.x])
        == "admission_corrected_in_part"
    )
    # The admission no review touched can still be reviewed on that child.
    review = build_admission_review(split.memory, split.sha256, [grown.w])
    assert [c["candidate_id"] for c in review["candidates"]] == [grown.w]
    publish(grown, [row(grown.x, "reject")], "whole")
    whole = load_memory_snapshot(grown.root / "whole")
    assert (
        code_of(build_admission_review, whole.memory, whole.sha256, [grown.x])
        == "unknown_candidate"
    )


def test_the_lineage_kind_is_the_growth_module_own():
    assert RECOGNITION_KIND == squint_identity_growth.RECOGNITION_KIND


def test_a_memory_candidate_admission_keeps_its_full_profile_through_correction(
    request,
):
    """An admission taken from a catalogue holds its paired full profile.

    The review pins it; a coronal reject leaves the case, its condition calls and
    its other facet in place, and the added identity record still reads its full
    profile offline from the child's own tables (no H5 product is left).
    """
    signed = request.getfixturevalue("catalogue_parent")
    receipt = grow_identity_memory(
        signed.parent,
        _memory_items(
            signed.catalogue,
            [FE],
            {FE: placed("femur", "patella")},
            sanity_by_case_id={FE: plausible("femur")},
        ),
        signed.root / "from-memory",
    )
    assert receipt["admitted_case_ids"] == [FE]
    child = load_memory_snapshot(signed.root / "from-memory" / CHILD_DIRECTORY)
    made = SimpleNamespace(root=signed.root, child=child)
    review = build_admission_review(child.memory, child.sha256, [FE])
    [candidate] = review["candidates"]
    [case] = [c for c in child.memory["cases"] if c["case_id"] == FE]
    assert candidate["full_profile"] == case["full_profile"]
    remaining = [view for view in candidate["admitted_views"] if view != COR]
    assert remaining
    _, corrected, _ = publish(made, [row(FE, "reject", views=[COR])], "corrected")
    [kept] = [c for c in corrected["cases"] if c["case_id"] == FE]
    assert kept == case and kept["condition_calls"] == {"ACL": 1}
    assert identity_condition_views(corrected)["views"][FE] == frozenset(
        tuple(view) for view in remaining
    )
    record = identity_record(corrected, FE)
    full = _full_profile_from_validated_case(
        corrected, record, record["full_profile"], record["subject"]
    )
    assert full.source_id == "study-e"
    assert corrected["full_profile_payloads"] == child.memory["full_profile_payloads"]
    assert corrected["object_identity_teaching"]["negative_views"][FE] == [COR]


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


def export(made, name: str, **options):
    log: list = []
    out = made.root / name
    result = MOD.export_admission_review(
        made.child.memory,
        made.child.sha256,
        made.root / "competition",
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
    assert "keep" in index and "only when every admitted view is rejected" in index
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
    assert result["whole_case_ids"] == []
    assert result["confirmed_admission_ids"] == [grown.w]
    corrected = load_memory(grown.root / "corrected")
    assert corrected["object_identity_teaching"]["negative_views"][grown.x] == [SAG]
    assert grown.x in object_ids(corrected)
    assert call_row(corrected, grown.x)["views"] == [COR]


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
    assert "admission_corrected_in_part" in info.value.detail
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
