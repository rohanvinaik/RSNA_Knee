"""Teaching intent: independent signs, honest blanks and composite source scope.

These direct-caller tests precede Detective pinning. Image content must never
receive a diagnosis word; family labels must never become per-bone targets.
"""

import csv
import dataclasses
import hashlib
import json
from dataclasses import FrozenInstanceError, replace
from typing import cast

import pytest

from knee.diagnosis.models import Profile
from knee.diagnosis.teaching import (
    binary_label_status,
    csv_label_status,
    labels_from_csv,
    teach_from_labels,
)
from knee.encoding.counts import BankLayout, CountBundle, CountLayout
from knee.study.tables import LABELS, TRAIN_COLUMNS


def profile(
    question="ACL",
    *,
    source="image-1",
    mode="full",
    counts=(2, 0, 1),
    context=(),
    provenance=(),
):
    bundle = CountBundle(
        CountLayout("test-v1", "carrier-v1", (BankLayout("object/ACL/content", 3),)),
        (counts,),
    )
    return Profile(
        f"diagnosis/{question}",
        bundle,
        mode,
        f"question:{question}",
        source,
        context=context,
        provenance=provenance,
    )


def csv_file(tmp_path, rows, header=TRAIN_COLUMNS):
    path = tmp_path / "train.csv"
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)
    return path


def csv_row(uid="study-1", **labels):
    return [
        uid,
        'Report, with "fracture" and\na newline',
        *(labels.get(question, "") for question in LABELS),
    ]


def entries(receipt, question):
    return [entry for entry in receipt["ledger"] if entry["question"] == question]


def test_direct_positive_and_negative_calls_keep_images_and_scope():
    image = profile()
    positive, pos = teach_from_labels({"s": [image]}, {"s": {"ACL": 1}}, revision="r1")
    negative, neg = teach_from_labels({"s": [image]}, {"s": {"ACL": 0}}, revision="r1")
    assert positive.cases[0].calls[0].digit == 1
    assert negative.cases[0].calls[0].digit == -1
    assert positive.cases[0].profile is image
    assert negative.cases[0].profile is image
    assert image.bundle.counts == ((2, 0, 1),)
    assert entries(pos, "ACL")[0]["digit"] == 1
    assert entries(neg, "ACL")[0]["digit"] == -1
    assert positive.trust == negative.trust == ()
    assert positive.censors == negative.censors == ()
    assert json.loads(positive.cases[0].calls[0].words)["call_scope"] == "diagnosis/ACL"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1", "positive"),
        ("0", "negative"),
        ("", "blank"),
        ("1.0", "invalid_label"),
        ("True", "invalid_label"),
        (" 0", "invalid_label"),
    ],
)
def test_csv_label_decision_from_intent(raw, expected):
    assert csv_label_status(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (1, "positive"),
        (0, "negative"),
        (None, "blank"),
        (True, "invalid_type"),
        (False, "invalid_type"),
        (0.0, "invalid_type"),
        (1.0, "invalid_type"),
        ("1", "invalid_type"),
        (-1, "invalid_label"),
        (2, "invalid_label"),
    ],
)
def test_binary_label_decision_from_intent(raw, expected):
    assert binary_label_status(raw) == expected


def test_csv_reads_real_schema_and_preserves_zero_and_blank(tmp_path):
    path = csv_file(tmp_path, [csv_row(ACL="1", MCL="0"), csv_row("blank")])
    labels = labels_from_csv(path)
    assert labels["study-1"]["ACL"] == 1
    assert labels["study-1"]["MCL"] == 0
    assert labels["study-1"]["Fracture"] is None
    assert all(value is None for value in labels["blank"].values())
    assert tuple(labels["study-1"]) == LABELS
    assert "Report" not in labels["study-1"]


@pytest.mark.parametrize(
    "raw",
    ["true", "false", "True", "False", "1.0", "0.0", "-1", "2", " ", "01", " 1", "0 "],
)
def test_csv_refuses_nonbinary_spelling(tmp_path, raw):
    with pytest.raises(ValueError, match="invalid_label"):
        labels_from_csv(csv_file(tmp_path, [csv_row(ACL=raw)]))


@pytest.mark.parametrize(
    "header",
    [
        (),
        TRAIN_COLUMNS[:-1],
        (*TRAIN_COLUMNS, "Extra"),
        ("StudyInstanceUID", "Report", *reversed(LABELS)),
        (*TRAIN_COLUMNS[:-1], "ACL"),
    ],
)
def test_csv_refuses_malformed_schema(tmp_path, header):
    with pytest.raises(ValueError, match="invalid_train_columns"):
        labels_from_csv(csv_file(tmp_path, [], header))


@pytest.mark.parametrize("row", [[], ["study"], csv_row()[:-1], [*csv_row(), "extra"]])
def test_csv_refuses_incomplete_or_extra_cells(tmp_path, row):
    with pytest.raises(ValueError, match="invalid_row_width"):
        labels_from_csv(csv_file(tmp_path, [row]))


def test_csv_refuses_malformed_quotes(tmp_path):
    path = csv_file(tmp_path, [])
    with path.open("a") as handle:
        handle.write('study,"unterminated report\n')
    with pytest.raises(ValueError, match="malformed_csv"):
        labels_from_csv(path)


def test_csv_refuses_empty_file_duplicate_and_empty_uids(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("")
    with pytest.raises(ValueError, match="invalid_train_columns"):
        labels_from_csv(path)
    with pytest.raises(ValueError, match="duplicate_study_uid"):
        labels_from_csv(csv_file(tmp_path, [csv_row(), csv_row()]))
    with pytest.raises(ValueError, match="invalid_study_uid"):
        labels_from_csv(csv_file(tmp_path, [csv_row(" ")]))


def test_multi_condition_study_teaches_only_its_composites():
    images = [profile("ACL"), profile("MCL"), profile("Fracture")]
    snapshot, receipt = teach_from_labels(
        {"s": images}, {"s": {"ACL": 1, "MCL": 0, "Fracture": 1}}, revision="r"
    )
    assert [
        (case.profile.subject, case.calls[0].question, case.calls[0].digit)
        for case in snapshot.cases
    ] == [
        ("diagnosis/ACL", "ACL", 1),
        ("diagnosis/MCL", "MCL", -1),
        ("diagnosis/Fracture", "Fracture", 1),
    ]
    assert receipt["case_count"] == 3
    assert all(len(case.calls) == 1 for case in snapshot.cases)
    assert all(
        case.profile.subject not in ("femur", "tibia", "patella", "fibula")
        for case in snapshot.cases
    )


def test_blank_missing_and_unasked_remain_distinct_zero_calls():
    snapshot, receipt = teach_from_labels(
        {"s": [profile("ACL"), profile("MCL")], "unlabelled": [profile()]},
        {"s": {"ACL": None, "Fracture": 0}, "blank": {"ACL": None}},
        revision="r",
    )
    assert snapshot.cases == ()
    outcomes = {
        (entry["study_uid"], entry["question"]): entry["reason"]
        for entry in receipt["ledger"]
    }
    assert outcomes["s", "ACL"] == "blank_label"
    assert outcomes["s", "MCL"] == "not_asked"
    assert outcomes["s", "Fracture"] == "missing_profile"
    assert outcomes["unlabelled", "ACL"] == "no_label_row"
    assert all(entry["digit"] == 0 for entry in receipt["ledger"])
    assert next(s for s in receipt["studies"] if s["study_uid"] == "blank")["all_blank"]


def test_all_blank_rows_teach_nothing_even_with_images():
    snapshot, receipt = teach_from_labels(
        {"s": [profile()]}, {"s": dict.fromkeys(LABELS)}, revision="r"
    )
    assert snapshot.cases == ()
    assert len(receipt["ledger"]) == 12
    assert {entry["reason"] for entry in receipt["ledger"]} == {"blank_label"}


@pytest.mark.parametrize("label", [0, 1])
def test_silent_image_cannot_be_promoted_as_signed_evidence(label):
    snapshot, receipt = teach_from_labels(
        {"s": [profile(counts=(0, 0, 0))]}, {"s": {"ACL": label}}, revision="r"
    )
    assert snapshot.cases == ()
    entry = entries(receipt, "ACL")[0]
    assert entry["label"] == label
    assert entry["digit"] == 0
    assert entry["reason"] == "silent_profile"


def test_encoded_middle_is_an_observation_not_a_missing_call():
    snapshot, _ = teach_from_labels(
        {"s": [profile(counts=(0, 5, 0))]}, {"s": {"ACL": 0}}, revision="r"
    )
    assert snapshot.cases[0].calls[0].digit == -1


@pytest.mark.parametrize("label", [True, False, 0.0, 1.0, "0", "", -1, 2])
def test_teaching_rejects_coerced_or_nonbinary_labels(label):
    with pytest.raises(ValueError, match="invalid_type|invalid_label"):
        teach_from_labels({"s": [profile()]}, {"s": {"ACL": label}}, revision="r")


def test_unknown_question_or_object_profile_is_refused():
    with pytest.raises(ValueError, match="unknown_question"):
        teach_from_labels({}, {"s": {"Not a condition": 1}}, revision="r")
    with pytest.raises(ValueError, match="not_question_composite"):
        teach_from_labels(
            {"s": [replace(profile(), subject="femur")]},
            {"s": {"Fracture": 1}},
            revision="r",
        )


def test_reports_retained_as_provenance_cannot_supply_labels():
    image = profile(provenance=(("report", "All bones fractured; ACL normal"),))
    snapshot, _ = teach_from_labels({"s": [image]}, {"s": {"ACL": 0}}, revision="r")
    assert snapshot.cases[0].profile.provenance == image.provenance
    assert snapshot.cases[0].calls[0].question == "ACL"
    assert snapshot.cases[0].calls[0].digit == -1
    assert len(snapshot.cases) == 1


def test_study_split_and_stronger_source_group_exclusion_survive():
    full = profile(
        context=(("study_uid", "s"), ("split", "train")),
        provenance=(("source_group", "patient-7"),),
    )
    cheap = replace(full, mode="cheap", source_id="image-cheap")
    snapshot, receipt = teach_from_labels(
        {"s": [full, cheap]}, {"s": {"ACL": 1}}, revision="r"
    )
    assert len(snapshot.cases) == 2
    assert receipt["exclude_study_uids"] == ["s"]
    assert receipt["exclude_source_groups"] == ["patient-7"]
    assert all(
        json.loads(case.calls[0].words)["split"] == "train" for case in snapshot.cases
    )
    assert {case.profile.mode for case in snapshot.cases} == {"cheap", "full"}


def test_unknown_patient_and_split_are_explicit_not_invented():
    _, receipt = teach_from_labels({"s": [profile()]}, {"s": {"ACL": 1}}, revision="r")
    assert receipt["studies"][0]["split"] is None
    assert receipt["studies"][0]["source_group"] is None
    assert receipt["exclude_source_groups"] == []


@pytest.mark.parametrize(
    "images",
    [
        [profile(context=(("study_uid", "other"),))],
        [profile(context=(("split", "train"),), provenance=(("split", "test"),))],
        [
            profile(context=(("source_group", "p1"),)),
            profile(source="2", context=(("source_group", "p2"),)),
        ],
    ],
)
def test_conflicting_source_metadata_is_refused(images):
    with pytest.raises(ValueError, match="mismatch|contradictory"):
        teach_from_labels({"s": images}, {"s": {"ACL": 1}}, revision="r")


def test_duplicate_profiles_refused_but_distinct_studies_never_pooled():
    image = profile()
    with pytest.raises(ValueError, match="duplicate_profile"):
        teach_from_labels({"s": [image, image]}, {"s": {"ACL": 1}}, revision="r")
    snapshot, _ = teach_from_labels(
        {"s1": [image], "s2": [image]},
        {"s1": {"ACL": 1}, "s2": {"ACL": 1}},
        revision="r",
    )
    assert len(snapshot.cases) == 2
    assert snapshot.cases[0].case_id != snapshot.cases[1].case_id
    assert all(case.profile.bundle.counts == ((2, 0, 1),) for case in snapshot.cases)


def test_deterministic_identity_and_immutable_corrected_revision():
    images = {"s2": [profile("MCL"), profile()], "s1": [profile()]}
    labels = {"s1": {"ACL": 0}, "s2": {"MCL": 1, "ACL": 1}}
    original, receipt = teach_from_labels(images, labels, revision="r1")
    again, again_receipt = teach_from_labels(
        {uid: list(reversed(value)) for uid, value in reversed(list(images.items()))},
        dict(reversed(list(labels.items()))),
        revision="r1",
    )
    assert again == original
    assert again_receipt == receipt
    corrected, correction_receipt = teach_from_labels(
        images, {**labels, "s1": {"ACL": 1}}, revision="r2"
    )
    assert original.revision == "r1"
    assert original.cases[0].calls[0].digit == -1
    assert corrected.cases[0].calls[0].digit == 1
    assert original.cases[0].case_id != corrected.cases[0].case_id
    assert correction_receipt["revision"] == "r2"
    with pytest.raises(FrozenInstanceError):
        original.revision = "overwrite"  # ty: ignore[invalid-assignment]
    receipt["ledger"].clear()
    assert len(original.cases) == 3
    assert all(case.teaching_revision == "r1" for case in original.cases)


@pytest.mark.parametrize("revision", ["", " ", None, 1])
def test_revision_must_be_explicit(revision):
    with pytest.raises(ValueError, match="invalid_revision"):
        teach_from_labels({}, {}, revision=revision)


def test_malformed_counts_and_metadata_refused():
    image = profile(counts=(True, 0, 1))
    with pytest.raises(ValueError, match="invalid_profile_counts"):
        teach_from_labels({"s": [image]}, {"s": {"ACL": 1}}, revision="r")
    with pytest.raises(ValueError, match="invalid_profile_metadata"):
        teach_from_labels(
            {"s": [profile(context=(("split", "train"), ("split", "test")))]},
            {"s": {"ACL": 1}},
            revision="r",
        )


def test_empty_inputs_produce_explicit_empty_revision():
    snapshot, receipt = teach_from_labels({}, {}, revision="empty-r")
    assert snapshot.cases == ()
    assert receipt["case_count"] == 0
    assert receipt["ledger"] == []
    json.dumps(receipt)


def test_sparse_identity_is_explicit_and_independently_reconstructible():
    """An auditor can reconstruct the fingerprint without expanding zeros."""

    def digest(value):
        return hashlib.sha256(
            json.dumps(
                value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode()
        ).hexdigest()

    image = profile(context=(("reference", "external-r1"),), counts=(0, 17, 0))
    snapshot, receipt = teach_from_labels(
        {"s": [image]}, {"s": {"ACL": 1}}, revision="r"
    )
    layout = {
        "schema_version": "knee.diagnostic-count-layout/v1",
        "layout_id": "test-v1",
        "carrier_id": "carrier-v1",
        "banks": [["object/ACL/content", 3]],
    }
    row_digest = digest(
        {
            "schema_version": "knee.diagnostic-count-row-sparse/v1",
            "row_count": 3,
            "nonzero_rows": [[1, "11"]],
        }
    )
    bundle_digest = digest(
        {
            "schema_version": "knee.diagnostic-count-bundle-sparse/v1",
            "layout_fingerprint": digest(layout),
            "speaking_banks": [[0, row_digest]],
        }
    )
    fingerprint = digest(
        {
            "schema_version": "knee.diagnostic-profile-sparse/v1",
            "subject": "diagnosis/ACL",
            "bundle_fingerprint": bundle_digest,
            "mode": "full",
            "scope": "question:ACL",
            "source_id": "image-1",
            "context": [["reference", "external-r1"]],
            "bank_statuses": [],
            "provenance": [],
        }
    )
    entry = entries(receipt, "ACL")[0]
    assert entry["profile_fingerprint"] == fingerprint
    assert receipt["identity_schema_version"] == "knee.diagnostic-case-sparse/v2"
    assert receipt["identity_layouts"] == {digest(layout): layout}
    call = snapshot.cases[0].calls[0]
    identity = {
        "schema_version": "knee.diagnostic-case-sparse/v2",
        "revision": "r",
        "study_uid": "s",
        "profile_fingerprint": fingerprint,
        "call": {
            "question": call.question,
            "digit": 1,
            "source": call.source,
            "words": call.words,
        },
    }
    assert snapshot.cases[0].case_id == f"case-sha256:{digest(identity)}"


@pytest.mark.parametrize("label", [0, 1])
def test_production_size_sparse_teaching_scans_shared_rows_once(monkeypatch, label):
    """Three 3696-bank roles reuse silent rows across two independent cases."""
    scans = {}

    class Row(tuple):
        def __iter__(self):
            scans[id(self)] = scans.get(id(self), 0) + 1
            return super().__iter__()

    silent = Row((0,) * 512)
    observed = Row((0,) * 511 + (1 << 20000,))
    banks = tuple(
        BankLayout(f"object/role-{role}/facet-{i}", 512)
        for role in range(3)
        for i in range(3696)
    )
    layout = CountLayout("production-shape", "carrier-512", banks)
    rows = (observed,) + (silent,) * (len(banks) - 1)
    images = [
        replace(profile(), bundle=CountBundle(layout, rows), source_id="one"),
        replace(profile(), bundle=CountBundle(layout, rows), source_id="two"),
    ]

    def forbid_dense(*args, **kwargs):
        pytest.fail("dense dataclasses.asdict conversion is forbidden")

    from knee.diagnosis import teaching

    monkeypatch.setattr(dataclasses, "asdict", forbid_dense)
    if hasattr(teaching, "asdict"):
        monkeypatch.setattr(teaching, "asdict", forbid_dense)
    result, receipt = teach_from_labels(
        {"s": images}, {"s": {"ACL": label}}, revision="production-shape"
    )
    assert len(result.cases) == 2
    assert all(case.calls[0].digit == (1 if label else -1) for case in result.cases)
    assert {id(case.profile) for case in result.cases} == {id(p) for p in images}
    assert scans == {id(silent): 1, id(observed): 1}
    assert len(receipt["identity_layouts"]) == 1
    json.dumps(receipt)
    teach_from_labels({"s": images}, {"s": {"ACL": label}}, revision="again")
    assert scans == {id(silent): 2, id(observed): 2}, "cache must end with the run"
    print(
        {
            "banks": len(banks),
            "rows_per_bank": 512,
            "logical_count_cells_per_profile": len(banks) * 512,
            "distinct_row_scans_per_run": 2,
            "layout_documents_per_run": 1,
            "signed_cases": len(result.cases),
            "digit": 1 if label else -1,
        }
    )


def test_production_object_distinct_rows_scan_once_across_cases():
    scans = {}

    class Row(tuple):
        def __iter__(self):
            scans[id(self)] = scans.get(id(self), 0) + 1
            return super().__iter__()

    rows = tuple(Row([1 if i == 0 else 0] + [0] * 511) for i in range(3696))
    layout = CountLayout(
        "production-object",
        "carrier-512",
        tuple(BankLayout(f"facet-{i}", 512) for i in range(3696)),
    )
    image = replace(profile(), bundle=CountBundle(layout, rows))
    result, receipt = teach_from_labels(
        {"positive": [image], "negative": [image]},
        {"positive": {"ACL": 1}, "negative": {"ACL": 0}},
        revision="r",
    )
    assert len(result.cases) == 2
    assert {case.calls[0].digit for case in result.cases} == {-1, 1}
    assert len(scans) == 3696
    assert set(scans.values()) == {1}
    assert all(case.profile is image for case in result.cases)
    assert len(receipt["identity_layouts"]) == 1
    print(
        {
            "banks": 3696,
            "rows_per_bank": 512,
            "distinct_row_scans": len(scans),
            "validated_count_cells": 3696 * 512,
            "independent_signed_cases": 2,
        }
    )


def test_identity_tracks_every_profile_field_and_exact_integer_change():
    image = profile(counts=(1 << 20000, 0, 0))

    def identity(candidate):
        question = candidate.subject.removeprefix("diagnosis/")
        snapshot, receipt = teach_from_labels(
            {"s": [candidate]}, {"s": {question: 1}}, revision="r"
        )
        return snapshot.cases[0].case_id, entries(receipt, question)[0][
            "profile_fingerprint"
        ]

    baseline = identity(image)
    variants = [
        replace(image, bundle=replace(image.bundle, counts=((1 << 20000 | 1, 0, 0),))),
        replace(image, bundle=replace(image.bundle, counts=((0, 1 << 20000, 0),))),
        replace(
            image,
            bundle=replace(
                image.bundle, layout=replace(image.bundle.layout, layout_id="new")
            ),
        ),
        replace(
            image,
            bundle=replace(
                image.bundle, layout=replace(image.bundle.layout, carrier_id="new")
            ),
        ),
        replace(
            image,
            bundle=replace(
                image.bundle,
                layout=replace(image.bundle.layout, banks=(BankLayout("role/new", 3),)),
            ),
        ),
        replace(image, context=(("reference", "new"),)),
        replace(image, provenance=(("reference", "new"),)),
        replace(image, bank_statuses=(("object/ACL/content", "partial"),)),
        replace(image, mode="cheap"),
        replace(image, scope="other-scope"),
        replace(image, source_id="other-source"),
        replace(image, subject="diagnosis/MCL"),
        replace(image, context=(("unrecognized-context", "retained"),)),
    ]
    for variant in variants:
        changed = identity(variant)
        assert changed[0] != baseline[0]
        assert changed[1] != baseline[1]


def test_complete_layout_identity_includes_silent_banks_and_cardinality():
    base = profile()
    variants = [
        base,
        replace(
            base,
            bundle=CountBundle(
                replace(
                    base.bundle.layout,
                    banks=(*base.bundle.layout.banks, BankLayout("silent", 2)),
                ),
                (*base.bundle.counts, (0, 0)),
            ),
        ),
        replace(
            base,
            bundle=CountBundle(
                replace(
                    base.bundle.layout, banks=(BankLayout("object/ACL/content", 4),)
                ),
                ((2, 0, 1, 0),),
            ),
        ),
    ]
    case_ids = []
    for image in variants:
        result, _ = teach_from_labels({"s": [image]}, {"s": {"ACL": 0}}, revision="r")
        case_ids.append(result.cases[0].case_id)
    assert len(set(case_ids)) == len(variants)


def test_sparse_ids_ignore_allocation_and_input_order_but_preserve_call_changes():
    first = profile(context=(("reference", "r1"), ("view", "v1")))
    equivalent = replace(first, context=tuple(reversed(first.context)))
    positive, receipt = teach_from_labels(
        {"s": [first]}, {"s": {"ACL": 1}}, revision="r"
    )
    again, _ = teach_from_labels({"s": [equivalent]}, {"s": {"ACL": 1}}, revision="r")
    negative, neg = teach_from_labels(
        {"s": [equivalent]}, {"s": {"ACL": 0}}, revision="r"
    )
    assert positive.cases[0].case_id == again.cases[0].case_id
    assert positive.cases[0].case_id != negative.cases[0].case_id
    assert (
        entries(receipt, "ACL")[0]["profile_fingerprint"]
        == entries(neg, "ACL")[0]["profile_fingerprint"]
    )
    assert positive.cases[0].profile is first
    assert negative.cases[0].profile is equivalent


@pytest.mark.parametrize(
    "rows",
    [
        ((1, 0, 0), (True, 0, 0)),
        ((1, 0, 0), (0, -1, 0)),
        ((1, 0, 0), (0, 0.5, 0)),
        ((1, 0, 0), (0, 0)),
        ((1, 0, 0), [0, 0, 0]),
    ],
)
def test_speaking_first_bank_never_hides_invalid_later_rows(rows):
    image = profile()
    image = replace(
        image,
        bundle=CountBundle(
            replace(
                image.bundle.layout,
                banks=(BankLayout("first", 3), BankLayout("later", 3)),
            ),
            rows,
        ),
    )
    with pytest.raises(ValueError, match="invalid_profile_counts"):
        teach_from_labels({"s": [image]}, {"s": {"ACL": 1}}, revision="r")


def test_layout_serialized_once_and_rows_validated_once_for_all_questions(monkeypatch):
    from knee.diagnosis import teaching

    seen = []
    layout_validations = []
    digest = teaching._digest
    valid_layout = teaching._valid_layout

    def observe_digest(document):
        if isinstance(document, dict) and "schema_version" in document:
            seen.append(document["schema_version"])
        return digest(document)

    def observe_layout(layout):
        layout_validations.append(id(layout))
        return valid_layout(layout)

    monkeypatch.setattr(teaching, "_digest", observe_digest)
    monkeypatch.setattr(teaching, "_valid_layout", observe_layout)
    original = profile()
    images = [
        original,
        replace(original, subject="diagnosis/MCL", source_id="two"),
        replace(
            original,
            subject="diagnosis/Fracture",
            source_id="three",
            bundle=replace(original.bundle, layout=replace(original.bundle.layout)),
        ),
    ]
    result, receipt = teach_from_labels(
        {"s": images, "other": [original]},
        {"s": {"ACL": 1, "MCL": 0, "Fracture": 1}, "other": {"ACL": 0}},
        revision="r",
    )
    assert len(result.cases) == 4
    assert len(receipt["identity_layouts"]) == 1
    assert seen.count("knee.diagnostic-count-layout/v1") == 1
    assert seen.count("knee.diagnostic-count-row-sparse/v1") == 1
    assert seen.count("knee.diagnostic-profile-sparse/v1") == 3
    assert len(layout_validations) == len(set(layout_validations)) == 2


@pytest.mark.parametrize(
    "bad_layout",
    [
        None,
        CountLayout("", "carrier", (BankLayout("one", 3),)),
        CountLayout("layout", "", (BankLayout("one", 3),)),
        CountLayout("layout", "carrier", ()),
        CountLayout(
            "layout", "carrier", cast(tuple[BankLayout, ...], [BankLayout("one", 3)])
        ),
        CountLayout("layout", "carrier", (BankLayout("", 3),)),
        CountLayout("layout", "carrier", (BankLayout("one", 0),)),
        CountLayout("layout", "carrier", (BankLayout("one", True),)),
        CountLayout("layout", "carrier", (BankLayout("one", cast(int, 3.0)),)),
        CountLayout("layout", "carrier", (BankLayout("one", 3), BankLayout("one", 3))),
    ],
)
def test_sparse_validation_agrees_with_count_validator_on_bad_layout(bad_layout):
    from knee.encoding.counts import CountCode, cosine_terms

    bundle = CountBundle(bad_layout, ((1, 0, 0),))
    assert cosine_terms(bundle, bundle, ()).code == CountCode.INVALID_INPUT
    with pytest.raises(ValueError, match="invalid_profile_counts"):
        teach_from_labels(
            {"s": [replace(profile(), bundle=bundle)]}, {"s": {"ACL": 1}}, revision="r"
        )


def test_reused_row_still_requires_each_bank_cardinality():
    row = (1, 0, 0)
    bundle = CountBundle(
        CountLayout("layout", "carrier", (BankLayout("one", 3), BankLayout("two", 4))),
        (row, row),
    )
    with pytest.raises(ValueError, match="invalid_profile_counts"):
        teach_from_labels(
            {"s": [replace(profile(), bundle=bundle)]}, {"s": {"ACL": 1}}, revision="r"
        )
