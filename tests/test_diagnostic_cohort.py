"""Explicit cohort input: authored from intent, not from the implementation.

The intent: the caller alone declares which studies belong to which opaque
partition, which partitions must never share a study or a known independent
group, and which groups are known. Nothing is defaulted, split, stratified or
read from labels. An absent group is unknown and neutral.
"""

from __future__ import annotations

import ast
import builtins
import dataclasses
import hashlib
import json
from pathlib import Path

import pytest

import knee.diagnosis.cohort as cohort_module
from knee.diagnosis.cohort import (
    Cohort,
    CohortError,
    cohort_document_status,
    load_cohort,
    partition_uids,
    source_group_for,
    uid_status,
)

SCHEMA = "knee.diagnostic-cohort/v1"


def document(**changes):
    base = {
        "schema": SCHEMA,
        "partitions": {"teaching": ["uid-a"], "evaluation": ["uid-b"]},
        "disjoint_partitions": [["teaching", "evaluation"]],
        "source_groups": {"uid-a": "patient-A", "uid-b": "patient-B"},
    }
    base.update(changes)
    return {key: value for key, value in base.items() if value is not ...}


def written(tmp_path, value, name="cohort.json"):
    path = tmp_path / name
    path.write_text(value if isinstance(value, str) else json.dumps(value))
    return path


def load(tmp_path, value):
    return load_cohort(written(tmp_path, value))


def refused(tmp_path, value):
    with pytest.raises(CohortError) as info:
        load(tmp_path, value)
    return info.value


# --- the accepted contract ---------------------------------------------------


def test_valid_cohort_keeps_declared_order_spelling_and_source_identity(tmp_path):
    value = document(
        partitions={"zeta": ["u2", "u1"], "alpha": ["u3"]},
        disjoint_partitions=[["zeta", "alpha"]],
        source_groups={"u3": "g", "u1": "h"},
    )
    path = written(tmp_path, value)
    cohort = load_cohort(path)
    assert isinstance(cohort, Cohort)
    assert cohort.schema == SCHEMA
    assert cohort.partitions == (("zeta", ("u2", "u1")), ("alpha", ("u3",)))
    assert cohort.disjoint_partitions == (("zeta", "alpha"),)
    assert cohort.source_groups == (("u3", "g"), ("u1", "h"))
    assert cohort.source == str(path.resolve())
    assert cohort.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()


def test_cohort_is_immutable_and_has_no_hidden_partitions(tmp_path):
    cohort = load(tmp_path, document())
    with pytest.raises(dataclasses.FrozenInstanceError):
        cohort.partitions = ()
    assert [name for name, _ in cohort.partitions] == ["teaching", "evaluation"]
    assert all(isinstance(uids, tuple) for _, uids in cohort.partitions)


def test_source_identity_follows_the_exact_bytes(tmp_path):
    first = load(tmp_path, document())
    second = load(tmp_path, json.dumps(document()) + " ")
    assert first.partitions == second.partitions
    assert first.sha256 != second.sha256


def test_source_groups_optional_and_empty_object_is_allowed(tmp_path):
    omitted = load(tmp_path, document(source_groups=...))
    empty = load(tmp_path, document(source_groups={}))
    assert omitted.source_groups == () == empty.source_groups


def test_single_partition_with_no_disjoint_pairs_is_a_valid_declaration(tmp_path):
    cohort = load(
        tmp_path,
        document(
            partitions={"only": ["u1"]}, disjoint_partitions=[], source_groups=...
        ),
    )
    assert cohort.partitions == (("only", ("u1",)),)
    assert cohort.disjoint_partitions == ()


def test_opaque_partition_names_are_not_interpreted(tmp_path):
    cohort = load(
        tmp_path,
        document(
            partitions={"test": ["u1"], "train": ["u2"], "x y": ["u3"]},
            disjoint_partitions=[],
            source_groups=...,
        ),
    )
    assert [name for name, _ in cohort.partitions] == ["test", "train", "x y"]


# --- leakage across a declared disjoint pair ---------------------------------


def test_known_study_shared_across_declared_pair_is_refused_either_pair_order(tmp_path):
    for pair in (["teaching", "evaluation"], ["evaluation", "teaching"]):
        error = refused(
            tmp_path,
            document(
                partitions={"teaching": ["u1", "shared"], "evaluation": ["shared"]},
                disjoint_partitions=[pair],
                source_groups=...,
            ),
        )
        assert error.code == "cohort_disjoint_uid_overlap"
        assert error.detail.endswith(":shared")


def test_known_group_shared_across_declared_pair_is_refused(tmp_path):
    for pair in (["teaching", "evaluation"], ["evaluation", "teaching"]):
        error = refused(
            tmp_path,
            document(
                disjoint_partitions=[pair],
                source_groups={"uid-a": "patient-X", "uid-b": "patient-X"},
            ),
        )
        assert error.code == "cohort_disjoint_group_overlap"
        assert error.detail.endswith(":patient-X")


def test_group_overlap_with_a_third_partition_must_name_a_declared_pair(tmp_path):
    base = {"teaching": ["u1"], "evaluation": ["u2"], "audit": ["u3"]}
    groups = {"u1": "G", "u2": "H", "u3": "G"}
    allowed = load(
        tmp_path,
        document(
            partitions=base,
            disjoint_partitions=[["teaching", "evaluation"]],
            source_groups=groups,
        ),
    )
    assert source_group_for(allowed, "u1") == source_group_for(allowed, "u3") == "G"
    error = refused(
        tmp_path,
        document(
            partitions=base,
            disjoint_partitions=[["teaching", "evaluation"], ["teaching", "audit"]],
            source_groups=groups,
        ),
    )
    assert error.code == "cohort_disjoint_group_overlap"


def test_a_study_may_appear_in_partitions_not_forbidden_to_share(tmp_path):
    cohort = load(
        tmp_path,
        document(
            partitions={"a": ["u1", "u2"], "b": ["u2"], "c": ["u3"]},
            disjoint_partitions=[["a", "c"], ["b", "c"]],
            source_groups=...,
        ),
    )
    assert partition_uids(cohort, "a", ["u1", "u2", "u3"]) == ("u1", "u2")
    assert partition_uids(cohort, "b", ["u2"]) == ("u2",)


def test_group_shared_inside_one_partition_is_not_leakage(tmp_path):
    cohort = load(
        tmp_path,
        document(
            partitions={"a": ["u1", "u2"], "b": ["u3"]},
            disjoint_partitions=[["a", "b"]],
            source_groups={"u1": "G", "u2": "G", "u3": "H"},
        ),
    )
    assert source_group_for(cohort, "u1") == source_group_for(cohort, "u2") == "G"


def test_leakage_is_checked_only_for_declared_pairs_not_for_all_partitions(tmp_path):
    cohort = load(
        tmp_path,
        document(
            partitions={"a": ["u1"], "b": ["u2"]},
            disjoint_partitions=[],
            source_groups={"u1": "G", "u2": "G"},
        ),
    )
    assert source_group_for(cohort, "u2") == "G"


# --- absent groups are unknown and neutral -----------------------------------


def test_absent_groups_are_neutral_for_leakage_and_return_empty(tmp_path):
    cohort = load(
        tmp_path,
        document(
            partitions={"a": ["u1", "u2"], "b": ["u3", "u4"]},
            disjoint_partitions=[["a", "b"]],
            source_groups={"u1": "G"},
        ),
    )
    assert source_group_for(cohort, "u1") == "G"
    for unknown in ("u2", "u3", "u4", "not-in-the-cohort"):
        assert source_group_for(cohort, unknown) == ""


def test_known_group_against_unknown_group_is_not_leakage_even_if_same_patient(
    tmp_path,
):
    cohort = load(
        tmp_path,
        document(
            partitions={"a": ["u1"], "b": ["u2"]},
            disjoint_partitions=[["a", "b"]],
            source_groups={"u1": "G"},
        ),
    )
    assert source_group_for(cohort, "u2") == ""


def test_literal_unknown_is_a_genuine_group_not_a_magic_string(tmp_path):
    cohort = load(
        tmp_path,
        document(
            partitions={"a": ["u1"], "b": ["u2"]},
            disjoint_partitions=[],
            source_groups={"u1": "unknown"},
        ),
    )
    assert source_group_for(cohort, "u1") == "unknown"
    assert source_group_for(cohort, "u2") == ""
    error = refused(
        tmp_path,
        document(
            partitions={"a": ["u1"], "b": ["u2"]},
            disjoint_partitions=[["a", "b"]],
            source_groups={"u1": "unknown", "u2": "unknown"},
        ),
    )
    assert error.code == "cohort_disjoint_group_overlap"
    assert error.detail.endswith(":unknown")


def test_group_spelling_is_exact_no_case_or_whitespace_rewriting(tmp_path):
    cohort = load(
        tmp_path,
        document(
            partitions={"a": ["u1", "u2"], "b": ["u3", "u4"]},
            disjoint_partitions=[["a", "b"]],
            source_groups={
                "u1": "Patient-A",
                "u2": " patient-A",
                "u3": "patient-A",
                "u4": "patient-A ",
            },
        ),
    )
    assert source_group_for(cohort, "u1") == "Patient-A"
    assert source_group_for(cohort, "u2") == " patient-A"
    assert source_group_for(cohort, "u4") == "patient-A "


@pytest.mark.parametrize("group", ["", " ", "\t\n", "a\0b", None, 7, True, ["g"], {}])
def test_empty_or_non_string_group_is_invalid(tmp_path, group):
    error = refused(tmp_path, document(source_groups={"uid-a": group}))
    assert error.code == "cohort_source_group_invalid"


def test_group_key_must_name_a_declared_study(tmp_path):
    error = refused(tmp_path, document(source_groups={"uid-z": "G"}))
    assert error.code == "cohort_source_group_unknown_uid"
    assert error.detail == "uid-z"


@pytest.mark.parametrize("groups", [None, [], "g", 3, [["uid-a", "g"]]])
def test_source_groups_must_be_an_object_when_present(tmp_path, groups):
    error = refused(tmp_path, document(source_groups=groups))
    assert error.code == "cohort_source_groups_invalid"


# --- duplicates ---------------------------------------------------------------


def test_duplicate_json_keys_are_refused_at_every_level(tmp_path):
    top = (
        '{"schema":"knee.diagnostic-cohort/v1","partitions":{"a":["u1"]},'
        '"partitions":{"a":["u2"]},"disjoint_partitions":[]}'
    )
    names = (
        '{"schema":"knee.diagnostic-cohort/v1","partitions":{"a":["u1"],'
        '"a":["u2"]},"disjoint_partitions":[]}'
    )
    groups = (
        '{"schema":"knee.diagnostic-cohort/v1","partitions":{"a":["u1"]},'
        '"disjoint_partitions":[],"source_groups":{"u1":"g","u1":"h"}}'
    )
    for text, key in ((top, "partitions"), (names, "a"), (groups, "u1")):
        error = refused(tmp_path, text)
        assert error.code == "cohort_duplicate_json_key"
        assert error.detail == key


def test_duplicate_uid_inside_one_partition_is_refused_exactly(tmp_path):
    error = refused(
        tmp_path,
        document(partitions={"a": ["u1", "u2", "u1"]}, disjoint_partitions=[]),
    )
    assert error.code == "cohort_duplicate_uid"
    assert error.detail == "a:u1"


def test_spellings_differing_by_case_or_whitespace_are_distinct_studies(tmp_path):
    cohort = load(
        tmp_path,
        document(
            partitions={"a": ["U1", "u1", "u1 ", " u1"]},
            disjoint_partitions=[],
            source_groups=...,
        ),
    )
    assert partition_uids(cohort, "a", ["u1 ", " u1", "u1", "U1"]) == (
        "U1",
        "u1",
        "u1 ",
        " u1",
    )


@pytest.mark.parametrize(
    "pairs",
    [
        [["teaching", "evaluation"], ["teaching", "evaluation"]],
        [["teaching", "evaluation"], ["evaluation", "teaching"]],
    ],
)
def test_duplicate_pair_in_either_order_is_refused(tmp_path, pairs):
    error = refused(tmp_path, document(disjoint_partitions=pairs))
    assert error.code == "cohort_disjoint_duplicate_pair"


# --- disjoint pair shape ------------------------------------------------------


@pytest.mark.parametrize(
    ("pairs", "code"),
    [
        ([["teaching", "teaching"]], "cohort_disjoint_pair_same_partition"),
        ([["teaching", "missing"]], "cohort_disjoint_unknown_partition"),
        ([["missing", "evaluation"]], "cohort_disjoint_unknown_partition"),
        ([["teaching"]], "cohort_disjoint_pair_malformed"),
        ([["teaching", "evaluation", "teaching"]], "cohort_disjoint_pair_malformed"),
        ([[]], "cohort_disjoint_pair_malformed"),
        ([["teaching", None]], "cohort_disjoint_pair_malformed"),
        ([["teaching", 1]], "cohort_disjoint_pair_malformed"),
        ([["teaching", True]], "cohort_disjoint_pair_malformed"),
        ([None], "cohort_disjoint_pair_malformed"),
        ([{"a": "b"}], "cohort_disjoint_pair_malformed"),
        (["teaching"], "cohort_disjoint_pair_malformed"),
        (None, "cohort_disjoint_partitions_invalid"),
        ({}, "cohort_disjoint_partitions_invalid"),
        ("teaching", "cohort_disjoint_partitions_invalid"),
    ],
)
def test_malformed_disjoint_pairs_have_named_refusals(tmp_path, pairs, code):
    assert refused(tmp_path, document(disjoint_partitions=pairs)).code == code


# --- null / malformed / empty -------------------------------------------------


@pytest.mark.parametrize(
    ("text", "code"),
    [
        ("", "cohort_empty"),
        ("  \n\t ", "cohort_empty"),
        ("{}", "cohort_empty"),
        ("null", "cohort_not_object"),
        ("[]", "cohort_not_object"),
        ("[1]", "cohort_not_object"),
        ('"x"', "cohort_not_object"),
        ("7", "cohort_not_object"),
        ("true", "cohort_not_object"),
        ("{", "cohort_json_malformed"),
        ("{'schema': 1}", "cohort_json_malformed"),
        ('{"schema": }', "cohort_json_malformed"),
        ("﻿{}", "cohort_json_malformed"),
    ],
)
def test_null_empty_and_malformed_documents_have_named_refusals(tmp_path, text, code):
    assert refused(tmp_path, text).code == code


def test_deeply_nested_json_is_malformed_not_a_crash(tmp_path):
    assert refused(tmp_path, "[" * 100000).code == "cohort_json_malformed"


def test_non_utf8_missing_and_non_path_sources_are_named(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_bytes(b"\xff\xfe{}")
    with pytest.raises(CohortError) as info:
        load_cohort(bad)
    assert info.value.code == "cohort_not_utf8"
    with pytest.raises(CohortError) as info:
        load_cohort(tmp_path / "absent.json")
    assert info.value.code == "cohort_unreadable"
    with pytest.raises(CohortError) as info:
        load_cohort(tmp_path)
    assert info.value.code == "cohort_unreadable"
    with pytest.raises(CohortError) as info:
        load_cohort(str(bad))
    assert info.value.code == "cohort_path_invalid"
    with pytest.raises(CohortError) as info:
        load_cohort(None)
    assert info.value.code == "cohort_path_invalid"


def test_unknown_top_level_key_is_refused_even_if_everything_else_is_valid(tmp_path):
    error = refused(tmp_path, document(split_ratio=0.8))
    assert error.code == "cohort_unknown_key"
    assert error.detail == "split_ratio"
    assert refused(tmp_path, document(seed=1)).code == "cohort_unknown_key"


@pytest.mark.parametrize("key", ["schema", "partitions", "disjoint_partitions"])
def test_every_required_key_is_required(tmp_path, key):
    error = refused(tmp_path, document(**{key: ...}))
    assert error.code == "cohort_missing_key"
    assert error.detail == key


@pytest.mark.parametrize(
    "schema",
    [
        None,
        1,
        True,
        "",
        "knee.diagnostic-cohort/v2",
        "KNEE.diagnostic-cohort/v1",
        ["x"],
    ],
)
def test_only_the_exact_schema_is_supported(tmp_path, schema):
    assert (
        refused(tmp_path, document(schema=schema)).code == "cohort_schema_unsupported"
    )


@pytest.mark.parametrize("partitions", [None, [], "a", 1, True, [["a", ["u1"]]]])
def test_partitions_must_be_an_object(tmp_path, partitions):
    error = refused(tmp_path, document(partitions=partitions, disjoint_partitions=[]))
    assert error.code == "cohort_partitions_invalid"


def test_at_least_one_partition_is_required(tmp_path):
    error = refused(tmp_path, document(partitions={}, disjoint_partitions=[]))
    assert error.code == "cohort_partitions_empty"


@pytest.mark.parametrize("name", ["", " ", "\t"])
def test_empty_partition_names_are_refused(tmp_path, name):
    error = refused(
        tmp_path, document(partitions={name: ["u1"]}, disjoint_partitions=[])
    )
    assert error.code == "cohort_partition_name_invalid"


@pytest.mark.parametrize("uids", [None, "u1", 1, {}, {"u1": 1}, True])
def test_each_partition_must_be_a_list(tmp_path, uids):
    error = refused(tmp_path, document(partitions={"a": uids}, disjoint_partitions=[]))
    assert error.code == "cohort_partition_not_list"


def test_each_declared_partition_must_be_nonempty(tmp_path):
    error = refused(
        tmp_path, document(partitions={"a": ["u1"], "b": []}, disjoint_partitions=[])
    )
    assert error.code == "cohort_partition_empty"
    assert error.detail == "b"


@pytest.mark.parametrize("uid", [None, 1, 1.5, True, False, ["u"], {"u": 1}])
def test_uid_must_be_a_string_with_exact_type(tmp_path, uid):
    error = refused(tmp_path, document(partitions={"a": [uid]}, disjoint_partitions=[]))
    assert error.code == "cohort_uid_not_string"


@pytest.mark.parametrize(
    "uid", ["", " ", "\t\n", ".", "..", "a/b", "/a", "a\\b", "a\0b", "../x"]
)
def test_unsafe_study_ids_are_refused(tmp_path, uid):
    error = refused(tmp_path, document(partitions={"a": [uid]}, disjoint_partitions=[]))
    assert error.code == "cohort_uid_unsafe"


def test_uid_safety_is_the_same_decision_as_the_pipeline_boundary():
    from knee.diagnosis.pipeline import DiagnosticRunError, _safe_uid

    samples = [
        "",
        " ",
        "\t",
        ".",
        "..",
        "...",
        ".hidden",
        "a",
        " a ",
        "a b",
        "a/b",
        "a\\b",
        "a\0b",
        "1.2.840.113619.2.1",
        "uid-é",
        None,
        1,
        True,
        b"a",
        ["a"],
    ]
    for sample in samples:
        try:
            _safe_uid(sample)
            accepted = True
        except DiagnosticRunError:
            accepted = False
        assert (uid_status(sample) == "ok") is accepted, repr(sample)


def test_uid_with_surrounding_whitespace_is_retained_not_normalized(tmp_path):
    cohort = load(
        tmp_path,
        document(partitions={"a": [" u1 "]}, disjoint_partitions=[], source_groups=...),
    )
    assert cohort.partitions == (("a", (" u1 ",)),)


# --- the pure decision, called directly ----------------------------------------


def test_document_status_is_ok_for_the_reference_document():
    assert cohort_document_status(document()) == "ok"


def test_document_status_names_each_defect_without_raising():
    assert cohort_document_status(None) == "cohort_not_object"
    assert cohort_document_status([]) == "cohort_not_object"
    assert cohort_document_status({}) == "cohort_empty"
    assert cohort_document_status(document(extra=1)) == "cohort_unknown_key:extra"
    assert (
        cohort_document_status(document(partitions=...))
        == "cohort_missing_key:partitions"
    )
    assert cohort_document_status(document(schema="x")) == "cohort_schema_unsupported"
    assert (
        cohort_document_status(
            document(
                partitions={"a": ["u"], "b": ["u"]},
                disjoint_partitions=[["a", "b"]],
                source_groups=...,
            )
        )
        == "cohort_disjoint_uid_overlap:a|b:u"
    )
    assert (
        cohort_document_status(
            document(source_groups={"uid-a": "same", "uid-b": "same"})
        )
        == "cohort_disjoint_group_overlap:teaching|evaluation:same"
    )
    assert (
        cohort_document_status(document(source_groups={"uid-a": "same", "uid-b": "x"}))
        == "ok"
    )


def test_document_status_reports_each_missing_required_key_by_name():
    assert cohort_document_status(document(schema=...)) == "cohort_missing_key:schema"
    assert (
        cohort_document_status(document(partitions=...))
        == "cohort_missing_key:partitions"
    )
    assert (
        cohort_document_status(document(disjoint_partitions=...))
        == "cohort_missing_key:disjoint_partitions"
    )
    assert cohort_document_status(document(source_groups=...)) == "ok"


def test_document_status_schema_must_be_an_exact_string_not_a_subclass():
    class Spoof(str):
        pass

    assert (
        cohort_document_status(document(schema=Spoof(SCHEMA)))
        == "cohort_schema_unsupported"
    )
    assert cohort_document_status(document(schema=SCHEMA)) == "ok"


def test_document_status_group_membership_ignores_declaration_order():
    # Groups listed in a different order than the studies they name, across
    # partitions: membership is a set test, never a one-shot scan.
    assert (
        cohort_document_status(
            document(
                partitions={"a": ["u1", "u2"], "b": ["u3"]},
                disjoint_partitions=[["a", "b"]],
                source_groups={"u3": "H", "u2": "G", "u1": "G"},
            )
        )
        == "ok"
    )


def test_group_membership_ignores_declaration_order_through_the_loader(tmp_path):
    cohort = load(
        tmp_path,
        document(
            partitions={"a": ["u1", "u2"], "b": ["u3"]},
            disjoint_partitions=[["a", "b"]],
            source_groups={"u3": "H", "u2": "G", "u1": "G"},
        ),
    )
    assert cohort.source_groups == (("u3", "H"), ("u2", "G"), ("u1", "G"))
    assert [source_group_for(cohort, u) for u in ("u1", "u2", "u3")] == ["G", "G", "H"]


def test_document_status_non_string_dictionary_names_are_refused():
    assert (
        cohort_document_status(document(partitions={1: ["u"]}, disjoint_partitions=[]))
        == "cohort_partition_name_invalid"
    )
    assert (
        cohort_document_status(document(source_groups={1: "g"}))
        == "cohort_source_group_unknown_uid:1"
    )
    assert uid_status("ok-id") == "ok"
    assert uid_status(3) == "cohort_uid_not_string"
    assert uid_status("..") == "cohort_uid_unsafe"


# --- requested selection ------------------------------------------------------


def test_partition_uids_returns_declared_order_not_available_order(tmp_path):
    cohort = load(
        tmp_path,
        document(
            partitions={"a": ["u3", "u1", "u2"], "b": ["u4"]},
            disjoint_partitions=[["a", "b"]],
            source_groups=...,
        ),
    )
    assert partition_uids(cohort, "a", ["u4", "u2", "u1", "u3"]) == ("u3", "u1", "u2")
    assert partition_uids(cohort, "a", ("u1", "u2", "u3", "zz", "u4")) == (
        "u3",
        "u1",
        "u2",
    )
    assert partition_uids(cohort, "b", ["u4"]) == ("u4",)


def test_partition_uids_unknown_partition_is_named(tmp_path):
    cohort = load(tmp_path, document())
    for name in ("Teaching", "", "missing"):
        with pytest.raises(CohortError) as info:
            partition_uids(cohort, name, ["uid-a", "uid-b"])
        assert info.value.code == "cohort_partition_unknown"
    with pytest.raises(CohortError) as info:
        partition_uids(cohort, None, ["uid-a"])
    assert info.value.code == "cohort_partition_name_invalid"


def test_partition_uids_refuses_any_missing_requested_study(tmp_path):
    cohort = load(
        tmp_path,
        document(
            partitions={"a": ["u1", "u2", "u3"]},
            disjoint_partitions=[],
            source_groups=...,
        ),
    )
    with pytest.raises(CohortError) as info:
        partition_uids(cohort, "a", ["u1"])
    assert info.value.code == "cohort_requested_uid_missing"
    assert info.value.detail == "u2"
    assert info.value.uids == ("u2", "u3")
    with pytest.raises(CohortError) as info:
        partition_uids(cohort, "a", [])
    assert info.value.code == "cohort_requested_uid_missing"
    # No fuzzy match: the available spelling must be exact.
    with pytest.raises(CohortError) as info:
        partition_uids(cohort, "a", ["U1", "u2 ", "u3"])
    assert info.value.code == "cohort_requested_uid_missing"


def test_partition_uids_refuses_ambiguous_requested_study(tmp_path):
    cohort = load(
        tmp_path,
        document(
            partitions={"a": ["u1", "u2"]}, disjoint_partitions=[], source_groups=...
        ),
    )
    with pytest.raises(CohortError) as info:
        partition_uids(cohort, "a", ["u1", "u2", "u1"])
    assert info.value.code == "cohort_available_uid_ambiguous"
    assert info.value.uids == ("u1",)
    # A duplicate that no partition member requested is not this selection's concern.
    assert partition_uids(cohort, "a", ["u1", "u2", "other", "other"]) == ("u1", "u2")


def test_partition_uids_available_must_be_a_sequence_of_strings(tmp_path):
    cohort = load(tmp_path, document())
    for bad in ("uid-a", b"uid-a", None, 5, {"uid-a"}, ["uid-a", None], ["uid-a", 1]):
        with pytest.raises(CohortError) as info:
            partition_uids(cohort, "teaching", bad)
        assert info.value.code == "cohort_available_invalid"
    with pytest.raises(CohortError) as info:
        partition_uids(None, "teaching", ["uid-a"])
    assert info.value.code == "cohort_invalid"


def test_source_group_for_rejects_non_string_and_non_cohort(tmp_path):
    cohort = load(tmp_path, document())
    for bad in (None, 1, True, b"uid-a"):
        with pytest.raises(CohortError) as info:
            source_group_for(cohort, bad)
        assert info.value.code == "cohort_uid_not_string"
    with pytest.raises(CohortError) as info:
        source_group_for(None, "uid-a")
    assert info.value.code == "cohort_invalid"
    assert source_group_for(cohort, "uid-a") == "patient-A"
    assert source_group_for(cohort, "uid-a ") == ""


def test_partition_uids_is_repeatable_and_does_not_mutate_inputs(tmp_path):
    cohort = load(tmp_path, document())
    available = ["uid-b", "uid-a"]
    first = partition_uids(cohort, "teaching", available)
    second = partition_uids(cohort, "teaching", available)
    assert first == second == ("uid-a",)
    assert available == ["uid-b", "uid-a"]


# --- boundaries: no labels, no cycle, this lane, the real exclusion consumer ---


def test_labels_are_never_opened_or_imported(tmp_path, monkeypatch):
    # A hostile sibling train.csv: if anything touched it, the guard would fire.
    (tmp_path / "train.csv").mkdir()
    opened = []
    real_open = builtins.open
    real_read_bytes = Path.read_bytes
    real_read_text = Path.read_text

    def spy_open(file, *args, **kwargs):
        opened.append(str(file))
        return real_open(file, *args, **kwargs)

    def spy_read_bytes(self, *args, **kwargs):
        opened.append(str(self))
        return real_read_bytes(self, *args, **kwargs)

    def spy_read_text(self, *args, **kwargs):
        opened.append(str(self))
        return real_read_text(self, *args, **kwargs)

    path = written(tmp_path, document())
    monkeypatch.setattr(builtins, "open", spy_open)
    monkeypatch.setattr(Path, "read_bytes", spy_read_bytes)
    monkeypatch.setattr(Path, "read_text", spy_read_text)
    cohort = load_cohort(path)
    partition_uids(cohort, "teaching", ["uid-a"])
    source_group_for(cohort, "uid-a")
    assert opened == [str(path)]
    tree = ast.parse(Path(cohort_module.__file__).read_text())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    assert not any(name.split(".")[0] in ("knee", "csv") for name in imported), imported


def test_module_is_imported_from_this_lane_and_cannot_cycle_with_pipeline():
    lane = Path(__file__).resolve().parents[1]
    assert Path(cohort_module.__file__).resolve() == (
        lane / "src/knee/diagnosis/cohort.py"
    )


def test_declared_group_reaches_the_existing_exclusion_consumer(tmp_path):
    """source_group_for feeds the group exclusion the capacity route performs."""
    from knee.diagnosis.composition import compose_question_profile
    from knee.diagnosis.models import Call, Case, Profile, Question, Snapshot
    from knee.diagnosis.retrieval import recall
    from knee.encoding.counts import BankLayout, CountBundle, CountLayout

    cohort = load(
        tmp_path,
        document(
            partitions={"teaching": ["related", "other"], "evaluation": ["query"]},
            disjoint_partitions=[],
            source_groups={"related": "patient-A", "query": "patient-A", "other": "B"},
        ),
    )
    layout = CountLayout("layout", "carrier", (BankLayout("signal", 3),))
    question = Question("ACL", "diagnosis/ACL", ("femur",), ("object/femur/signal",))

    def composed(uid):
        return compose_question_profile(
            (
                Profile(
                    "femur",
                    CountBundle(layout, ((1, 0, 0),)),
                    "cheap/fixture-v1",
                    "region:bone",
                    "source:" + uid,
                    context=(
                        ("study_uid", uid),
                        ("source_group", source_group_for(cohort, uid)),
                    ),
                ),
            ),
            question,
        )

    snapshot = Snapshot(
        "r1",
        tuple(
            Case(uid, uid, composed(uid), (Call("ACL", sign, "independent"),), "r1")
            for uid, sign in (("related", 1), ("other", -1))
        ),
    )
    query = composed("query")
    group = dict(query.provenance)["source_group"]
    assert group == source_group_for(cohort, "query") == "patient-A"
    result = recall(query, question, snapshot, exclude_source_group=group)
    assert result["source_group_excluded_case_ids"] == ["related"]
    assert [row["case_id"] for row in result["case_terms"]] == ["other"]
