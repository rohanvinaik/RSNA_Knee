"""A diagnosis speaks only through the views where its object's identity holds.

CLASSICAL_AI_BUILD_DESIGN §5.1 and the OpenSpec requirement "A diagnosis carries
across the views of its object": when a memory carries identity teaching, each
object case's condition evidence speaks only through the views of its confirm
call (every view when the confirm named none). A view called other tissue, and
a view never asserted, carry no condition evidence. The restriction is applied
before preparation builds anything, so no envelope, matrix or selected-bank
union ever holds a withheld bank. A memory without identity teaching prepares
and recalls exactly as before.
"""

from __future__ import annotations

import copy
import hashlib
import json

import numpy as np
import pytest

from knee.diagnosis.squint_interfaces import TERRITORY_PROCEDURE, territory_bank_name
from knee.diagnosis.squint_locator import (
    persisted_recall_cache,
    prepare_recall,
    recall_object,
    recall_source_fingerprint,
)
from knee.diagnosis.squint_memory_view import MemoryViewError, memory_view

TEACHING_SCHEMA = "knee.object-identity-teaching/v1"
V1_PROCEDURE = "knee.squint-profile/scan-tercile-v1"
SAG = ["Sagittal", "0", "0"]
COR = ["Coronal", "0", "0"]


def view_bank(view: list[str], metric: str = "signal_median") -> str:
    """A canonical cheap v2 bank the real question selection reads."""
    return territory_bank_name(
        dict(
            zip(
                ("orientation", "fluid_sensitive", "fat_suppression"), view, strict=True
            )
        ),
        "object",
        metric,
        "overview",
        10.0,
    )


SAG_BANK, COR_BANK = view_bank(SAG), view_bank(COR)
FA, FB, FC = (f"squint-case:study-{name}:femur" for name in "abc")


def femur_case(case_id, study, digit, banks, procedure=TERRITORY_PROCEDURE):
    return {
        "case_id": case_id,
        "study_uid": study,
        "subject": "femur",
        "condition_calls": {"Fracture": digit},
        "presentation_scope": {
            "Fracture": "positive_condition_presentation"
            if digit == 1
            else "normal_for_this_condition_only"
        },
        "profile": {
            "schema": "knee.squint-profile/v1",
            "subject": "femur",
            "banks": {name: list(counts) for name, counts in banks.items()},
            "source": {"procedure": procedure},
        },
        "regions": [],
        "teaching_source": {"kind": "official_train_csv_label"},
    }


def fracture_memory(procedure=TERRITORY_PROCEDURE):
    """Femur Fracture cases: a positive with both views and two normal ones.

    The positive (a) reads (3,0,0) sagittally and (0,0,3) coronally. One
    normal (b) has only a sagittal reading, the other (c) only a coronal one,
    so each view has its own opposing-case envelope.
    """
    return {
        "schema": "knee.squint-memory/v1",
        "revision": "condition-scope-fixture",
        "questions": [],
        "cases": [
            femur_case(
                FA, "study-a", 1, {SAG_BANK: (3, 0, 0), COR_BANK: (0, 0, 3)}, procedure
            ),
            femur_case(FB, "study-b", -1, {SAG_BANK: (1, 2, 0)}, procedure),
            femur_case(FC, "study-c", -1, {COR_BANK: (1, 2, 0)}, procedure),
        ],
    }


def confirm(case_id, **scope):
    return {"candidate_id": case_id, "call": "confirm", "notes": "n", **scope}


def taught(memory, calls, confirmed=None):
    """The memory with identity teaching; confirmed defaults to every confirm."""
    result = copy.deepcopy(memory)
    result["object_identity_teaching"] = {
        "schema": TEACHING_SCHEMA,
        "reader": "fixture-reader",
        "confirmed_case_ids": [
            row["candidate_id"] for row in calls if row["call"] == "confirm"
        ]
        if confirmed is None
        else confirmed,
        "negative_case_ids": [],
        "negative_views": {},
        "alternative_positives": [],
        "calls": calls,
    }
    return result


def coronal_only_a(memory=None):
    """Femur a confirmed coronally; its sagittal support called other tissue."""
    return taught(
        fracture_memory() if memory is None else memory,
        [confirm(FA, views=[COR], negative_views=[SAG]), confirm(FB), confirm(FC)],
    )


def query(banks, procedure=TERRITORY_PROCEDURE):
    return {
        "schema": "knee.squint-profile/v1",
        "subject": "femur",
        "banks": {name: list(counts) for name, counts in banks.items()},
        "source": {"procedure": procedure},
    }


SAG_QUERY = {SAG_BANK: (3, 0, 0)}
COR_QUERY = {COR_BANK: (0, 0, 3)}


def recall(memory, banks, procedure=TERRITORY_PROCEDURE, prepared=None):
    prepared = prepare_recall(memory) if prepared is None else prepared
    return recall_object(
        query(banks, procedure), {**memory, "prepared_recall": prepared}, "Fracture"
    )


def _plain(value):
    if isinstance(value, np.ndarray):
        return {
            "dtype": str(value.dtype),
            "shape": list(value.shape),
            "data": value.tolist(),
        }
    if isinstance(value, (set, frozenset)):
        return sorted(value)
    raise TypeError(type(value).__name__)


def digest(value) -> str:
    """Exact content digest of a preparation or recall, numpy arrays included."""
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), default=_plain)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def golden(procedure):
    """Every recall product of the untaught fixture, by digest."""
    memory = fracture_memory(procedure)
    prepared = prepare_recall(memory)
    attached = {**memory, "prepared_recall": prepared}
    view = memory_view(attached, exclude_study_uids=("study-b",))
    return {
        "fingerprint": recall_source_fingerprint(memory),
        "prepared": digest(prepared),
        "persisted": digest(persisted_recall_cache(memory, prepared)),
        "sagittal": digest(
            recall_object(query(SAG_QUERY, procedure), attached, "Fracture")
        ),
        "coronal": digest(
            recall_object(query(COR_QUERY, procedure), attached, "Fracture")
        ),
        "view": digest(view["prepared_recall"]),
        "view_recall": digest(
            recall_object(query(COR_QUERY, procedure), view, "Fracture")
        ),
    }


# Captured on fca0c77, before identity scoping existed: a memory without
# identity teaching must prepare and recall exactly so.
GOLDEN = {
    TERRITORY_PROCEDURE: {
        "fingerprint": "c76418b48da6cccb3c2a83a3860967aea19b64b92696a8d2d42c972a6364f187",  # pragma: allowlist secret
        "prepared": "2aeeae64d1fdb42205798c091c11440671f5d0534a00080ee712669b3af03402",  # pragma: allowlist secret
        "persisted": "b036adc1606fe67f52fb954785aeab96cf0ea910e2f37d48147e098f9343f5ff",  # pragma: allowlist secret
        "sagittal": "12046308414c69d2c717b6f23589791ef4c58c84db9fea55265ea6348ff1e91d",  # pragma: allowlist secret
        "coronal": "c7953bc08048cb44c8fb1cee0d382f9bd48cb948ce39ecf4eb7f20390b23c903",  # pragma: allowlist secret
        "view": "d778f931a249c6bb3e9e7fb5c778ff852d63f5389be14bd5e2e8dde496cdd12b",  # pragma: allowlist secret
        "view_recall": "5b0c20f08c386eb89e4bedb06d56b11dc920a23ee76a2ba6b288e73b33eee8ca",  # pragma: allowlist secret
    },
    V1_PROCEDURE: {
        "fingerprint": "71f151d8ae2aaf656547571fadb40175b1b6358db387fa140d589f60d4348789",  # pragma: allowlist secret
        "prepared": "54829790266c23fb7ea4086d08a31c4783d54f7ec44c03ea547fba8df697cc0b",  # pragma: allowlist secret
        "persisted": "b1b012271543a203d624d42b64c46354d2a9f8ed5ac57229864d9b091684f20c",  # pragma: allowlist secret
        "sagittal": "cf55c34ae8942a19277d899f0c78b91fce191c40ae3c887da710d23332b44420",  # pragma: allowlist secret
        "coronal": "eaaa0c988032d49ba775c3c90d718bf2a1dcdcd42b3aaf01a56f5ca724808b15",  # pragma: allowlist secret
        "view": "5a7c858bdb99cef57e633698c097d5fc33ea63b850ddbe6f1571157fee581e8f",  # pragma: allowlist secret
        "view_recall": "a2068fba84b5c7f2ecbe5720f6c42fe04ae4da655d18ff88ffba02811b6841a8",  # pragma: allowlist secret
    },
}
PROCEDURES = pytest.mark.parametrize("procedure", [TERRITORY_PROCEDURE, V1_PROCEDURE])


def case_banks(prepared, index):
    """One case's prepared banks: question-selected (v2) or every bank (v1)."""
    if "selections" in prepared:
        return prepared["question_case_profile_banks"]["Fracture"][index]
    return prepared["case_profile_banks"][index]


def femur_matrix(prepared):
    if "selections" in prepared:
        return prepared["question_profile_matrices"]["femur"]["Fracture"]
    return prepared["subject_profile_matrices"]["femur"]


@PROCEDURES
def test_memory_without_identity_teaching_recalls_byte_identically(procedure):
    assert golden(procedure) == GOLDEN[procedure]


@PROCEDURES
def test_a_facet_called_other_tissue_supports_no_diagnosis(procedure):
    """The reproduced failure, on the selected v2 path and the v1 path alike.

    Femur a is confirmed coronally and its sagittal support was called other
    tissue; it holds a positive Fracture presentation. On fca0c77 a
    sagittal-only query returned present, spoken only by that rejected bank.
    """
    memory = coronal_only_a(fracture_memory(procedure))
    before = copy.deepcopy(memory)
    prepared = prepare_recall(memory)
    assert prepared["outcome"] == "prepared"
    assert ("selections" in prepared) == (procedure == TERRITORY_PROCEDURE)

    sagittal = recall(memory, SAG_QUERY, procedure, prepared)
    assert sagittal["outcome"] == "proposal"
    assert sagittal["speaking_calls"] == [] and sagittal["speaking_case_ids"] == []
    assert FA in sagittal["silent_case_ids"]
    assert all(row["case_id"] != FA for row in sagittal["case_terms"])

    coronal = recall(memory, COR_QUERY, procedure, prepared)
    assert coronal["outcome"] == "present"
    assert coronal["speaking_case_ids"] == [FA]
    [row] = [row for row in coronal["case_terms"] if row["case_id"] == FA]
    assert (row["call"], row["common_speaking_banks"]) == (1, [COR_BANK])

    # The withheld bank entered nothing preparation built.
    assert set(case_banks(prepared, 0)) == {COR_BANK}
    assert list(prepared["envelopes"]["femur"]["Fracture"]) == [json.dumps([COR_BANK])]
    for bucket in prepared["envelopes"]["femur"]["Fracture"].values():
        for comparison in bucket["comparisons"]:
            if FA in comparison["case_ids"]:
                assert SAG_BANK not in comparison["common_speaking_banks"]
    matrix = femur_matrix(prepared)
    row_index = matrix["row_by_case"][0]
    assert not matrix["speaks"][row_index][matrix["names"].index(SAG_BANK)]
    assert not matrix["values"][row_index][matrix["names"].index(SAG_BANK)].any()
    # Only which facets speak changed; the stored payload did not.
    assert memory == before
    assert memory["cases"][0]["profile"]["banks"][SAG_BANK] == [3, 0, 0]


@PROCEDURES
def test_a_whole_case_confirm_is_heard_through_every_view(procedure):
    memory = taught(fracture_memory(procedure), [confirm(FA), confirm(FB), confirm(FC)])
    prepared = prepare_recall(memory)
    for banks in (SAG_QUERY, COR_QUERY):
        result = recall(memory, banks, procedure, prepared)
        assert result["outcome"] == "present"
        assert result["speaking_case_ids"] == [FA]
    # Nothing is withheld, so preparation measures what it measured untaught.
    plain = prepare_recall(fracture_memory(procedure))
    assert prepared["envelopes"] == plain["envelopes"]


def test_a_diagnosis_clear_in_one_view_is_recalled_from_another_identity_view():
    """OpenSpec "Diagnosis clear in sagittal, object present coronally"."""
    memory = taught(
        fracture_memory(),
        [confirm(FA, views=[SAG, COR]), confirm(FB), confirm(FC)],
    )
    result = recall(memory, COR_QUERY)
    assert result["outcome"] == "present"
    [row] = [row for row in result["case_terms"] if row["case_id"] == FA]
    assert (row["call"], row["common_speaking_banks"]) == (1, [COR_BANK])
    assert row["call_scope"] == "positive_condition_presentation"


def test_an_unasserted_identity_carries_no_condition_evidence():
    unsure = {"candidate_id": FA, "call": "unsure", "notes": "n"}
    memories = (
        taught(fracture_memory(), [unsure, confirm(FB), confirm(FC)]),
        # A confirm row whose id was never confirmed establishes nothing either.
        taught(
            fracture_memory(),
            [confirm(FA), confirm(FB), confirm(FC)],
            confirmed=[FB, FC],
        ),
    )
    for memory in memories:
        prepared = prepare_recall(memory)
        assert case_banks(prepared, 0) == {}
        for banks in (SAG_QUERY, COR_QUERY):
            result = recall(memory, banks, prepared=prepared)
            assert FA in result["silent_case_ids"]
            assert result["outcome"] != "present"


def test_configuration_roles_speak_only_through_their_objects_identity_views():
    from knee.diagnosis.squint_configurations import (
        configuration_profile,
        with_configuration_cases,
    )
    from knee.study.tables import LABELS

    memory = fracture_memory()
    memory["label_ledger"] = {
        uid: {**dict.fromkeys(LABELS), "Fracture": label}
        for uid, label in (("study-a", 1), ("study-b", 0), ("study-c", 0))
    }
    configured = with_configuration_cases(memory, procedure=TERRITORY_PROCEDURE)
    roles = {case["study_uid"]: case for case in configured["cases"][3:]}
    assert set(roles["study-a"]["profile"]["banks"]) == {
        "object/femur/" + SAG_BANK,
        "object/femur/" + COR_BANK,
    }
    scoped = coronal_only_a(configured)
    prepared = prepare_recall(scoped)
    index = scoped["cases"].index(roles["study-a"])
    assert set(prepared["question_case_profile_banks"]["Fracture"][index]) == {
        "object/femur/" + COR_BANK
    }

    def configuration_query(banks):
        return configuration_profile(
            {"femur": query(banks)}, "Fracture", procedure=TERRITORY_PROCEDURE
        )

    attached = {**scoped, "prepared_recall": prepared}
    sagittal = recall_object(configuration_query(SAG_QUERY), attached, "Fracture")
    assert sagittal["outcome"] != "present"
    assert roles["study-a"]["case_id"] in sagittal["silent_case_ids"]
    coronal = recall_object(configuration_query(COR_QUERY), attached, "Fracture")
    assert coronal["outcome"] == "present"
    assert coronal["speaking_case_ids"] == [roles["study-a"]["case_id"]]
    # Unscoped, the same configuration still hears its sagittal role.
    plain = recall_object(
        configuration_query(SAG_QUERY),
        {**configured, "prepared_recall": prepare_recall(configured)},
        "Fracture",
    )
    assert plain["outcome"] == "present"


def test_identity_calls_enter_the_preparation_identity():
    plain = fracture_memory()
    scoped = coronal_only_a()
    whole = taught(fracture_memory(), [confirm(FA), confirm(FB), confirm(FC)])
    identities = {
        recall_source_fingerprint(memory) for memory in (plain, scoped, whole)
    }
    assert len(identities) == 3
    # Lineage alone, and identity records preparation never reads, change nothing.
    lineage = copy.deepcopy(scoped)
    lineage["object_identity_teaching"]["reader"] = "another-reader"
    for row in lineage["object_identity_teaching"]["calls"]:
        row["notes"] = "re-read"
    outside = copy.deepcopy(scoped)
    outside["object_identity_teaching"]["calls"].append(
        {"candidate_id": "squint-case:study-z:femur", "call": "reject", "notes": "n"}
    )
    for same in (lineage, outside):
        assert recall_source_fingerprint(same) == recall_source_fingerprint(scoped)


def test_a_stale_published_preparation_is_rebuilt_or_refused_by_name():
    scoped = coronal_only_a()
    fresh = prepare_recall(scoped)
    plain = fracture_memory()
    # On fca0c77 a taught memory's published cache was byte for byte the
    # untaught one's (digest captured there): the pre-scoping preparation.
    before_scoping = persisted_recall_cache(plain, prepare_recall(plain))
    assert digest(before_scoping) == GOLDEN[TERRITORY_PROCEDURE]["persisted"]
    whole = taught(fracture_memory(), [confirm(FA), confirm(FB), confirm(FC)])
    other_calls = persisted_recall_cache(whole, prepare_recall(whole))
    for stale in (before_scoping, other_calls):
        stale = json.loads(json.dumps(stale))
        rebuilt = prepare_recall(scoped, cached=stale)
        assert rebuilt["cache_status"] == "rebuilt_incompatible_cache"
        assert rebuilt["source_fingerprint"] == fresh["source_fingerprint"]
        assert rebuilt["envelopes"] == fresh["envelopes"]
        held_out = prepare_recall(scoped, cached=stale, exclude_study_uid="study-b")
        assert held_out["cache_status"] == "rebuilt_incompatible_cache"
    for stale in (prepare_recall(plain), prepare_recall(whole)):
        for excluded in ((), ("study-b",)):
            with pytest.raises(MemoryViewError) as info:
                memory_view(
                    {**scoped, "prepared_recall": stale}, exclude_study_uids=excluded
                )
            assert info.value.code == "memory_view_preparation_source_mismatch"
    # The current preparation is reused as it is, never rebuilt.
    current = json.loads(json.dumps(persisted_recall_cache(scoped, fresh)))
    restored = prepare_recall(scoped, cached=current)
    assert restored["runtime_indexes_rebuilt"] is True
    for key in ("envelopes", "selection_identity", "question_case_profile_banks"):
        assert restored[key] == fresh[key]


def test_held_out_projection_keeps_the_identity_scope():
    scoped = coronal_only_a()
    prepared = prepare_recall(scoped)
    cache = json.loads(json.dumps(persisted_recall_cache(scoped, prepared)))
    projected = prepare_recall(scoped, cached=cache, exclude_study_uid="study-b")
    assert projected["runtime_indexes_rebuilt"] is True
    fresh = prepare_recall(memory_view(scoped, exclude_study_uids=("study-b",)))
    for key in (
        "envelopes",
        "selection_identity",
        "case_indices",
        "source_fingerprint",
        "question_case_profile_banks",
    ):
        assert projected[key] == fresh[key]
    assert set(projected["question_case_profile_banks"]["Fracture"][0]) == {COR_BANK}


@pytest.mark.parametrize(
    "mutate,reason",
    [
        (
            lambda t: t.update(schema="other"),
            "object_identity_teaching_schema_mismatch",
        ),
        (lambda t: t.update(confirmed_case_ids="x"), "confirmed_case_ids_required"),
        (
            lambda t: t["calls"][0].update(views=[["Coronal", "0"]]),
            "teaching_call_views_invalid",
        ),
        (
            lambda t: t["calls"][0].update(views=[SAG], negative_views=[SAG]),
            "teaching_call_views_overlap",
        ),
    ],
)
def test_unreadable_identity_teaching_refuses_condition_preparation(mutate, reason):
    from knee.diagnosis.squint_identity import prepare_identity

    memory = coronal_only_a()
    mutate(memory["object_identity_teaching"])
    assert prepare_identity(memory) == {"outcome": "invalid_input", "reason": reason}
    assert prepare_recall(memory) == {"outcome": "invalid_input", "reason": reason}
    with pytest.raises(ValueError, match=reason):
        recall_source_fingerprint(memory)
    with pytest.raises(MemoryViewError) as info:
        memory_view(memory, exclude_study_uids=("study-b",))
    assert info.value.code == "memory_view_recall_source_invalid"


def test_condition_scope_reads_confirms_exactly_as_identity_recall():
    from knee.diagnosis.squint_identity import (
        _signal_banks,
        identity_condition_views,
        prepare_identity,
    )

    unsure = {"candidate_id": FC, "call": "unsure", "notes": "n"}
    reject = {"candidate_id": FA, "call": "reject", "notes": "n", "views": [SAG]}
    alternative = [{"identity": "tibia", "views": [SAG]}]
    shapes = (
        [confirm(FA), confirm(FB), confirm(FC)],
        [confirm(FA, views=[COR], negative_views=[SAG]), confirm(FB), confirm(FC)],
        [confirm(FA, views=[SAG]), confirm(FB, views=[SAG]), unsure],
        [confirm(FA, views=[COR], also_positive=alternative), confirm(FB)],
        [confirm(FA), confirm(FA), confirm(FB)],
        [reject, confirm(FB), confirm(FC)],
    )
    for calls in shapes:
        memory = taught(fracture_memory(), calls)
        scope = identity_condition_views(memory)
        prepared = prepare_identity(memory)
        assert scope["outcome"] == "scoped"
        assert prepared["outcome"] == "prepared"
        seeds = {seed["case_id"]: seed for seed in prepared._seeds}
        assert set(scope["views"]) == set(seeds)
        cases = {case["case_id"]: case for case in memory["cases"]}
        for case_id, views in scope["views"].items():
            raw = {
                name: tuple(counts)
                for name, counts in cases[case_id]["profile"]["banks"].items()
            }
            selected = None if views is None else set(views)
            assert dict(seeds[case_id]["banks"]) == _signal_banks(raw, selected)


# --------------------------------------------- the carry, for joined labels

AXIAL = ["Axial", "0", "0"]


def object_case(subject, views=(SAG, COR)):
    return {
        "case_id": f"squint-case:study-q:{subject}",
        "study_uid": "study-q",
        "subject": subject,
        "profile": {
            "schema": "knee.squint-profile/v1",
            "subject": subject,
            "banks": {view_bank(view): [1, 0, 0] for view in views},
            "source": {"procedure": TERRITORY_PROCEDURE},
        },
    }


def label_row(**values):
    from knee.study.tables import LABELS

    row = dict.fromkeys(LABELS)
    row.update(values)
    return row


def localized(subject, digit=1, question="Fracture", study="study-q"):
    return {
        "question": question,
        "study_uid": study,
        "subject": subject,
        "digit": digit,
        "source": {"kind": "visual_call", "view": SAG, "reader": "fixture-reader"},
    }


def test_carry_makes_a_single_object_positive_a_presentation_in_each_identity_view():
    from knee.diagnosis.squint_memory import (
        CONDITION_CARRY_SCHEMA,
        _condition_calls,
        carry_condition_calls,
    )

    acl = object_case("acl", views=(SAG, COR, AXIAL))
    labels = label_row(ACL=1)
    result = carry_condition_calls(
        acl, confirm(acl["case_id"], views=[SAG, COR]), labels
    )
    assert result["schema"] == CONDITION_CARRY_SCHEMA
    calls, scopes = _condition_calls("acl", labels)
    assert (result["condition_calls"], result["presentation_scope"]) == (calls, scopes)
    assert result["presentation_scope"] == {"ACL": "positive_condition_presentation"}
    # Every identity view at once; the unasserted axial facet carries nothing.
    assert result["identity_views"] == [COR, SAG]
    assert result["speaks_through"] == {"ACL": [COR, SAG]}
    assert result["labels"] == {"ACL": 1}
    whole = carry_condition_calls(acl, confirm(acl["case_id"]), labels)
    assert whole["identity_scope"] == "whole_case"
    assert whole["speaks_through"] == {"ACL": [AXIAL, COR, SAG]}


def test_carry_keeps_a_study_level_bone_positive_unlocalized():
    from knee.diagnosis.squint_memory import carry_condition_calls

    femur = object_case("femur")
    labels = label_row(Fracture=1)
    for calls in ((), (localized("tibia"),), (localized("femur", study="study-r"),)):
        result = carry_condition_calls(
            femur, confirm(femur["case_id"]), labels, localized_calls=calls
        )
        assert result["presentation_scope"]["Fracture"] == (
            "positive_condition_presentation"
        )
        assert result["localized_calls"] == {}
        assert result["unapplied_localized_calls"] == []


def test_carry_localizes_a_bone_positive_only_through_a_sourced_call_naming_it():
    from knee.diagnosis.squint_memory import (
        LOCALIZED_PRESENTATION_SCOPE,
        carry_condition_calls,
    )

    femur = object_case("femur", views=(SAG, COR, AXIAL))
    identity = confirm(femur["case_id"], views=[SAG, COR])
    call = localized("femur")
    result = carry_condition_calls(
        femur, identity, label_row(Fracture=1), localized_calls=[call]
    )
    assert result["condition_calls"]["Fracture"] == 1
    assert result["presentation_scope"]["Fracture"] == LOCALIZED_PRESENTATION_SCOPE
    assert result["speaks_through"]["Fracture"] == [COR, SAG]
    assert result["localized_calls"] == {"Fracture": [call]}
    assert result["labels"]["Fracture"] == 1
    # A localized call never creates or flips a call; it is kept by name.
    blank = carry_condition_calls(femur, identity, label_row(), localized_calls=[call])
    assert "Fracture" not in blank["condition_calls"]
    assert blank["unapplied_localized_calls"] == [
        {"call": call, "reason": "label_absent"}
    ]
    negative = carry_condition_calls(
        femur, identity, label_row(Fracture=0), localized_calls=[call]
    )
    assert negative["condition_calls"]["Fracture"] == -1
    assert negative["presentation_scope"]["Fracture"] == (
        "normal_for_this_condition_only"
    )
    assert negative["unapplied_localized_calls"] == [
        {"call": call, "reason": "label_not_positive"}
    ]


def test_carry_never_carries_a_normal_label_beyond_its_own_calls():
    from knee.diagnosis.squint_memory import _condition_calls, carry_condition_calls

    femur = object_case("femur")
    identity = confirm(femur["case_id"])
    for labels in (label_row(Fracture=0), label_row(Fracture=0, ACL=1), label_row()):
        result = carry_condition_calls(femur, identity, labels)
        expected = _condition_calls("femur", labels)
        assert (result["condition_calls"], result["presentation_scope"]) == expected
    # A localized negative is no carry input: kept by name, never applied.
    negative = localized("femur", digit=-1)
    result = carry_condition_calls(
        femur, identity, label_row(Fracture=1), localized_calls=[negative]
    )
    assert result["presentation_scope"]["Fracture"] == (
        "positive_condition_presentation"
    )
    assert result["unapplied_localized_calls"] == [
        {"call": negative, "reason": "carry_is_positive_only"}
    ]


def test_carry_never_speaks_through_a_facet_called_other_tissue():
    from knee.diagnosis.squint_memory import SquintMemoryError, carry_condition_calls

    femur = object_case("femur")
    labels = label_row(Fracture=1, ACL=1)
    result = carry_condition_calls(
        femur, confirm(femur["case_id"], views=[COR], negative_views=[SAG]), labels
    )
    assert result["identity_views"] == [COR]
    assert result["speaks_through"] == {"Fracture": [COR], "ACL": [COR]}
    refusals = (
        (
            confirm(femur["case_id"], negative_views=[SAG]),
            "teaching_call_views_overlap",
        ),
        (
            {"candidate_id": femur["case_id"], "call": "reject", "notes": "n"},
            "teaching_call_not_confirm",
        ),
        (confirm("squint-case:study-q:tibia"), "carry_identity_call_not_this_case"),
    )
    for identity, code in refusals:
        with pytest.raises(SquintMemoryError) as info:
            carry_condition_calls(femur, identity, labels)
        assert info.value.code == code
