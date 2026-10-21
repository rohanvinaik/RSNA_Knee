from __future__ import annotations

import copy
import json

from knee.diagnosis.squint_identity import prepare_identity, recall_identity

SCHEMA = "knee.object-identity-teaching/v1"
SANITY_SCHEMA = "knee.object-anatomical-sanity/v1"


def bank(scale="10mm", role="object", metric="m", view="[0,1,2]"):
    return (
        f"squint/v2/view={view}/role={role}/metric={metric}/direction=d/scale={scale}"
    )


def profile(counts, subject="X", procedure="proc", banks=None):
    return {
        "subject": subject,
        "banks": banks if banks is not None else {bank(): list(counts)},
        "source": {"procedure": procedure},
    }


def case(cid, subject, study, counts, procedure="proc", banks=None):
    return {
        "case_id": cid,
        "subject": subject,
        "study_uid": study,
        "profile": profile(counts, subject, procedure, banks),
    }


def memory(cases, confirmed=None, calls=None):
    ids = [c["case_id"] for c in cases]
    return {
        "source_manifest_sha256": "sm1",
        "cases": cases,
        "object_identity_teaching": {
            "schema": SCHEMA,
            "confirmed_case_ids": ids if confirmed is None else confirmed,
            "calls": calls
            if calls is not None
            else [{"candidate_id": i, "call": "confirm"} for i in ids],
            "reader_sha256": "r1",
            "source_sha256": "s1",
            "review_sha256": "v1",
            "unrelated_hash": "u1",
        },
    }


def two_identity_memory():
    return memory(
        [
            case("a1", "A", "sa", (1, 0, 0)),
            case("b1", "B", "sb", (0, 1, 0)),
        ]
    )


def sanity(status):
    return {
        "schema": SANITY_SCHEMA,
        "status": status,
        "identity_assertion": None,
        "windows": [],
    }


def by_id(result):
    return {c["case_id"]: c for c in result["cases"]}


def signal(result):
    return (
        result["outcome"],
        result["identity"],
        [
            (
                c["case_id"],
                c["squared_cosine"],
                c["dot"],
                c["common_speaking_banks"],
                c["envelope"],
                c["speaks"],
            )
            for c in result["cases"]
        ],
    )


def test_query_name_cannot_force_answer():
    mem = two_identity_memory()
    for name in ("A", "B", "Z"):
        result = recall_identity(profile((1, 0, 0), subject=name), mem)
        assert result["outcome"] == "identified"
        assert result["identity"] == "A"
    result = recall_identity(profile((0, 1, 0), subject="A"), mem)
    assert result["identity"] == "B"


def test_uncalled_and_rejected_cases_cannot_speak():
    cases = [
        case("a1", "A", "sa", (1, 0, 0)),
        case("b1", "B", "sb", (0, 1, 0)),
        case("c1", "C", "sc", (1, 0, 0)),
        case("d1", "D", "sd", (1, 0, 0)),
    ]
    calls = [
        {"candidate_id": "a1", "call": "confirm"},
        {"candidate_id": "b1", "call": "confirm"},
        {"candidate_id": "d1", "call": "reject"},
    ]
    mem = memory(cases, confirmed=["a1", "b1", "c1", "d1"], calls=calls)
    result = recall_identity(profile((1, 0, 0)), mem)
    assert set(by_id(result)) == {"a1", "b1"}
    assert result["identity"] == "A"
    mem2 = memory(cases, confirmed=["a1", "b1"])
    assert set(by_id(recall_identity(profile((1, 0, 0)), mem2))) == {"a1", "b1"}


def test_diagnosis_configuration_subjects_never_speak():
    cases = [
        case("a1", "A", "sa", (1, 0, 0)),
        case("g1", "diagnosis/x", "sg", (1, 0, 0)),
    ]
    result = recall_identity(profile((1, 0, 0)), memory(cases))
    assert set(by_id(result)) == {"a1"}


def test_non_signal_metadata_does_not_change_signal():
    mem = two_identity_memory()
    other = copy.deepcopy(mem)
    other["object_identity_teaching"]["reader_sha256"] = "zzz"
    other["object_identity_teaching"]["calls"][0]["note"] = "changed"
    other["cases"][0]["source_sha256"] = "new"
    query = profile((1, 0, 0))
    left = recall_identity(query, mem)
    right = recall_identity(query, other)
    assert signal(left) == signal(right)
    assert left["cases"][0]["lineage"] != right["cases"][0]["lineage"]
    assert right["cases"][0]["lineage"]["teaching"]["reader_sha256"] == "zzz"


def test_exclusion_reaches_query_population_and_envelope_opponents():
    mem = memory(
        [
            case("a1", "A", "sa", (1, 0, 0)),
            case("b2", "B", "sb", (1, 1, 0)),
        ]
    )
    query = profile((1, 1, 0))
    base = recall_identity(query, mem)
    assert base["outcome"] == "identified" and base["identity"] == "B"
    assert by_id(base)["a1"]["envelope_status"] == "not_above_envelope"
    no_b = recall_identity(query, mem, exclude_study_uid="sb")
    assert set(by_id(no_b)) == {"a1"}
    assert by_id(no_b)["a1"]["envelope"] is None
    assert no_b["outcome"] == "proposal"
    no_a = recall_identity(query, mem, exclude_study_uid="sa")
    assert set(by_id(no_a)) == {"b2"}
    assert no_a["outcome"] == "proposal"


def test_exact_envelope_boundary_is_not_warranted():
    mem = memory(
        [
            case("a1", "A", "sa", (1, 0, 0)),
            case("b2", "B", "sb", (1, 1, 0)),
        ]
    )
    result = recall_identity(profile((1, 1, 0)), mem)
    a1 = by_id(result)["a1"]
    assert a1["squared_cosine"] == {"numerator": "1", "denominator": "2"}
    assert a1["envelope"]["numerator"] == "1"
    assert a1["envelope"]["denominator"] == "2"
    assert a1["speaks"] is False
    assert result["speaking_identities"] == ["B"]


def test_tie_yields_conflict_without_tie_break():
    result = recall_identity(profile((1, 1, 0)), two_identity_memory())
    assert result["outcome"] == "unresolved_conflict"
    assert result["identity"] is None
    assert result["speaking_identities"] == ["A", "B"]
    assert len(result["nearest_identities"]) == 2


def test_no_compatible_opponent_is_proposal():
    mem = memory(
        [
            case("a1", "A", "sa", (1, 0, 0)),
            case("a2", "A", "sb", (1, 0, 0)),
        ]
    )
    result = recall_identity(profile((1, 0, 0)), mem)
    assert result["outcome"] == "proposal"
    assert result["reason"] == "no_compatible_opposing_case"
    assert result["identity"] is None
    assert result["nearest_identities"][0]["identity"] == "A"


def test_empty_and_malformed_memory():
    empty = memory([])
    assert recall_identity(profile((1, 0, 0)), empty)["outcome"] == "silent"
    assert recall_identity(profile((1, 0, 0)), [])["outcome"] == "invalid_input"
    bad = two_identity_memory()
    bad["object_identity_teaching"]["schema"] = "other"
    assert recall_identity(profile((1, 0, 0)), bad)["outcome"] == "invalid_input"
    missing = {"cases": []}
    assert prepare_identity(missing)["outcome"] == "invalid_input"
    broken = two_identity_memory()
    broken["cases"][0]["profile"] = {"banks": 5}
    assert prepare_identity(broken)["outcome"] == "invalid_input"
    assert (
        prepare_identity(two_identity_memory(), exclude_study_uid="")["outcome"]
        == "invalid_input"
    )
    assert recall_identity({"banks": 1}, two_identity_memory())["outcome"] == (
        "invalid_input"
    )


def test_procedure_mismatch_is_silent():
    result = recall_identity(
        profile((1, 0, 0), procedure="other"), two_identity_memory()
    )
    assert result["outcome"] == "silent"
    assert result["cases"] == []


def test_unread_and_fine_banks_are_neutral():
    mem = two_identity_memory()
    query = profile((1, 0, 0))
    base = recall_identity(query, mem)
    noisy = profile(
        (1, 0, 0),
        banks={
            bank(): [1, 0, 0],
            bank(metric="unread"): [0, 0, 0],
            bank(scale="2mm"): [9, 9, 9],
            bank(role="label"): [9, 9, 9],
            "not-a-bank": [9, 9, 9],
        },
    )
    assert signal(recall_identity(noisy, mem)) == signal(base)
    fine_only = profile((0, 0, 0), banks={bank(scale="2mm"): [1, 0, 0]})
    assert recall_identity(fine_only, mem)["outcome"] == "silent"


def test_real_sanity_schema_contradicted_blocks_others_neutral():
    mem = two_identity_memory()
    query = profile((1, 0, 0))
    plain = recall_identity(query, mem)
    for status in ("unknown", "plausible"):
        result = recall_identity(query, mem, sanity=sanity(status))
        assert signal(result) == signal(plain)
        assert result["admitted"] is True
        assert result["sanity"] == {"status": status}
        empty = recall_identity(profile((0, 0, 1)), mem, sanity=sanity(status))
        assert empty["identity"] is None
        assert empty["admitted"] is False
    blocked = recall_identity(query, mem, sanity=sanity("contradicted"))
    assert blocked["outcome"] == "blocked_by_sanity"
    assert blocked["identity"] is None
    assert blocked["admitted"] is False
    assert blocked["cases"] == plain["cases"]
    assert signal(recall_identity(query, mem, sanity=None)) == signal(plain)
    wrong = [
        "unknown",
        {"verdict": "contradicted"},
        {"name": "unknown"},
        {"schema": "other", "status": "unknown"},
        {"schema": SANITY_SCHEMA, "status": "bogus"},
        {"schema": SANITY_SCHEMA, "status": "supported"},
        {"schema": SANITY_SCHEMA, "status": "unknown", "identity_assertion": "A"},
    ]
    for item in wrong:
        assert recall_identity(query, mem, sanity=item)["outcome"] == "invalid_input"


def test_prepared_matches_unprepared_and_is_reusable():
    mem = memory(
        [
            case("a1", "A", "sa", (1, 0, 0)),
            case("b2", "B", "sb", (1, 1, 0)),
            case("b1", "B", "sc", (0, 1, 0)),
        ]
    )
    for exclude in (None, "sb"):
        prep = prepare_identity(mem, exclude_study_uid=exclude)
        assert prep["outcome"] == "prepared"
        for counts in ((1, 1, 0), (1, 0, 0), (0, 1, 0)):
            query = profile(counts)
            assert recall_identity(
                query, mem, exclude_study_uid=exclude, prepared=prep
            ) == recall_identity(query, mem, exclude_study_uid=exclude)


def test_multi_bank_exact_tuple_matching():
    bank_a = bank(metric="a")
    bank_b = bank(metric="b")
    mem = memory(
        [
            case("a1", "A", "sa", None, banks={bank_a: [1, 0, 0], bank_b: [1, 0, 0]}),
            case("b1", "B", "sb", None, banks={bank_a: [1, 0, 0]}),
        ]
    )
    query = profile(None, banks={bank_a: [1, 0, 0], bank_b: [1, 0, 0]})
    result = recall_identity(query, mem)
    cases = by_id(result)
    assert cases["a1"]["common_speaking_banks"] == sorted([bank_a, bank_b])
    assert cases["a1"]["envelope"] is None
    assert cases["a1"]["envelope_status"] == "no_compatible_opposing_case"
    assert cases["a1"]["speaks"] is False
    assert cases["b1"]["common_speaking_banks"] == [bank_a]
    assert cases["b1"]["speaks"] is False
    assert result["outcome"] == "proposal"
    assert result["identity"] is None
    assert result["admitted"] is False


def test_stale_prepared_reuse_is_rejected():
    mem = two_identity_memory()
    query = profile((1, 0, 0))
    prep = prepare_identity(mem)
    fresh = recall_identity(query, mem)
    assert fresh["identity"] == "A"
    assert recall_identity(query, mem, prepared=prep) == fresh
    changed = copy.deepcopy(mem)
    changed["object_identity_teaching"]["calls"][0]["call"] = "reject"
    changed["cases"][1]["profile"]["banks"][bank()] = [1, 0, 0]
    stale = recall_identity(query, changed, prepared=prep)
    assert stale["outcome"] == "invalid_preparation"
    assert stale["reason"] == "memory_mismatch"
    assert stale.get("identity") is None
    assert "cases" not in stale
    identical_copy = copy.deepcopy(mem)
    assert recall_identity(query, identical_copy, prepared=prep)["outcome"] == (
        "invalid_preparation"
    )
    wrong_exclusion = recall_identity(query, mem, exclude_study_uid="sb", prepared=prep)
    assert wrong_exclusion["outcome"] == "invalid_preparation"
    assert wrong_exclusion["reason"] == "exclusion_mismatch"
    assert (
        recall_identity(query, mem, prepared={"outcome": "prepared"})["outcome"]
        == "invalid_preparation"
    )
    # Reuse reads the frozen snapshot, not mutable content of the original mapping.
    mem["cases"][0]["profile"]["banks"][bank()] = [0, 0, 1]
    assert recall_identity(query, mem, prepared=prep) == fresh


def test_provenance_keys_retained_with_seed_lineage():
    result = recall_identity(profile((1, 0, 0)), two_identity_memory())
    for item in result["cases"]:
        lineage = item["lineage"]
        assert lineage["source"]["source_manifest_sha256"] == "sm1"
        assert lineage["teaching"]["review_sha256"] == "v1"
        assert lineage["teaching"]["reader_sha256"] == "r1"
        assert lineage["teaching"]["source_sha256"] == "s1"
        assert "unrelated_hash" not in lineage["teaching"]
        assert lineage["call"]["candidate_id"] == item["case_id"]
    pins = {
        recall_identity(profile((1, 0, 0)), two_identity_memory())["prepared_view"][
            "source_pin"
        ]
    }
    other = two_identity_memory()
    other["object_identity_teaching"]["review_sha256"] = "v2"
    changed = recall_identity(profile((1, 0, 0)), other)
    assert changed["prepared_view"]["source_pin"] not in pins
    assert signal(changed) == signal(
        recall_identity(profile((1, 0, 0)), two_identity_memory())
    )


def test_different_identities_from_same_study_are_countercases_and_exclusion_removes_both():
    mem = memory(
        [
            case("a1", "A", "same-study", (1, 0, 0)),
            case("b1", "B", "same-study", (0, 1, 0)),
        ]
    )
    result = recall_identity(profile((1, 0, 0)), mem)
    assert result["outcome"] == "identified"
    assert result["identity"] == "A"
    assert by_id(result)["a1"]["envelope"]["opponent_case_ids"] == ["b1"]
    excluded = recall_identity(profile((1, 0, 0)), mem, exclude_study_uid="same-study")
    assert excluded["outcome"] == "silent"
    assert excluded["reason"] == "no_eligible_seed_cases"
    assert excluded["cases"] == []


def test_reviewed_views_filter_only_seed_signal_banks():
    view_a = bank(view='["Sagittal","0","0"]', metric="a")
    view_b = bank(view='["Coronal","0","0"]', metric="b")
    first = case(
        "a1",
        "A",
        "sa",
        None,
        banks={view_a: [1, 0, 0], view_b: [0, 1, 0]},
    )
    second = case(
        "b1",
        "B",
        "sb",
        None,
        banks={view_a: [0, 1, 0], view_b: [0, 1, 0]},
    )
    mem = memory(
        [first, second],
        calls=[
            {
                "candidate_id": "a1",
                "call": "confirm",
                "views": [["Sagittal", "0", "0"]],
            },
            {"candidate_id": "b1", "call": "confirm"},
        ],
    )
    prepared = prepare_identity(mem)
    assert prepared["outcome"] == "prepared"
    seeds = {seed["case_id"]: seed for seed in prepared._seeds}
    assert set(seeds["a1"]["banks"]) == {view_a}
    assert set(seeds["b1"]["banks"]) == {view_a, view_b}
    query = profile(None, banks={view_a: [1, 0, 0], view_b: [1, 0, 0]})
    result = recall_identity(query, mem, prepared=prepared)
    cases = by_id(result)
    assert cases["a1"]["common_speaking_banks"] == [view_a]
    assert cases["b1"]["common_speaking_banks"] == sorted([view_a, view_b])


# ------------------------------------------------- signed identity teaching
# A reject (or a confirm's negative_views) is an ordinary negative identity
# case: a -1 on its proposed identity, on its own views. also_positive is a
# positive of a known alternative identity. Both live outside memory["cases"].

CASES_SCHEMA = "knee.object-identity-cases/v1"
SAG = ["Sagittal", "0", "0"]
COR = ["Coronal", "0", "0"]
OLD_RECALL_KEYS = [
    "admitted",
    "calibrated_probability",
    "cases",
    "identity",
    "nearest_cases",
    "nearest_identities",
    "outcome",
    "prepared_view",
    "proposed_name",
    "reason",
    "sanity",
    "schema",
    "speaking_identities",
]


def vbank(view, metric="m"):
    return bank(view=json.dumps(view, separators=(",", ":")), metric=metric)


def vcase(cid, subject, study, by_view):
    banks = {vbank(view): list(counts) for view, counts in by_view}
    return case(cid, subject, study, None, banks=banks)


def sag(counts):
    return profile(None, banks={vbank(SAG): list(counts)})


def _identity_record(mem, record):
    table = mem.setdefault(
        "object_identity_cases", {"schema": CASES_SCHEMA, "cases": []}
    )
    if all(item["case_id"] != record["case_id"] for item in table["cases"]):
        table["cases"].append(record)


def add_negative(mem, record, views, call=None, append_call=True):
    """One ordinary negative identity case: -1 on the record's own subject."""
    _identity_record(mem, record)
    teaching = mem["object_identity_teaching"]
    teaching.setdefault("negative_case_ids", []).append(record["case_id"])
    teaching.setdefault("negative_views", {})[record["case_id"]] = [
        list(view) for view in views
    ]
    if append_call:
        teaching["calls"].append(
            call or {"candidate_id": record["case_id"], "call": "reject"}
        )
    return mem


def add_alternative(mem, record, identity, views):
    _identity_record(mem, record)
    mem["object_identity_teaching"].setdefault("alternative_positives", []).append(
        {
            "entry_id": f"{record['case_id']}::also_positive::{identity}",
            "case_id": record["case_id"],
            "identity": identity,
            "views": [list(view) for view in views],
        }
    )
    return mem


def seeds_a_b():
    return memory(
        [
            vcase("a1", "A", "sa", [(SAG, (3, 0, 0))]),
            vcase("b1", "B", "sb", [(SAG, (0, 0, 3))]),
        ]
    )


def rejected_a_memory():
    """Seeds of A and B, and a candidate proposed as A whose pictured support,
    (1, 2, 0), the reviewer rejected as other tissue."""
    return add_negative(seeds_a_b(), vcase("n1", "A", "sn", [(SAG, (1, 2, 0))]), [SAG])


def test_rejected_candidate_speaks_against_its_identity_only_above_its_envelope():
    mem = rejected_a_memory()
    like_negative = sag((1, 2, 0))
    assert recall_identity(like_negative, seeds_a_b())["identity"] == "A"
    result = recall_identity(like_negative, mem)
    assert result["outcome"] == "unresolved_conflict"
    assert result["reason"] == "identity_spoken_for_and_against"
    assert result["identity"] is None and result["admitted"] is False
    assert result["speaking_identities"] == ["A"]
    assert result["opposed_identities"] == ["A"]
    assert result["conflicted_identities"] == ["A"]
    assert by_id(result)["a1"]["speaks"] is True
    [row] = result["negative_cases"]
    assert (row["case_id"], row["identity"], row["digit"]) == ("n1", "A", -1)
    assert row["views"] == [SAG]
    assert row["squared_cosine"] == {"numerator": "25", "denominator": "25"}
    # Its envelope is what it shares with A's own positive seed: 9/45.
    assert (row["envelope"]["numerator"], row["envelope"]["denominator"]) == (
        "9",
        "45",
    )
    assert row["envelope"]["opponent_case_ids"] == ["a1"]
    assert row["envelope_status"] == "above_envelope" and row["speaks"] is True

    like_seed = recall_identity(sag((3, 0, 0)), mem)
    assert like_seed["outcome"] == "identified" and like_seed["identity"] == "A"
    [quiet] = like_seed["negative_cases"]
    assert quiet["squared_cosine"] == {"numerator": "9", "denominator": "45"}
    assert quiet["envelope_status"] == "not_above_envelope"
    assert quiet["speaks"] is False
    assert like_seed["opposed_identities"] == []

    other = recall_identity(sag((0, 2, 1)), mem)
    assert other["outcome"] == "identified" and other["identity"] == "B"
    assert other["opposed_identities"] == ["A"]
    assert other["conflicted_identities"] == []


def test_negative_without_a_positive_of_its_identity_stays_silent_and_named():
    mem = add_negative(seeds_a_b(), vcase("n9", "C", "sn", [(SAG, (1, 2, 0))]), [SAG])
    result = recall_identity(sag((1, 2, 0)), mem)
    [row] = result["negative_cases"]
    assert row["identity"] == "C" and row["envelope"] is None
    assert row["envelope_status"] == "no_compatible_opposing_case"
    assert row["speaks"] is False
    assert result["opposed_identities"] == []
    assert result["outcome"] == "identified" and result["identity"] == "A"
    assert prepare_identity(mem)["negative_case_count"] == 1


def test_only_a_reject_or_negative_views_writes_a_negative_case():
    for call in ("unsure", "confirm"):
        mem = add_negative(
            seeds_a_b(),
            vcase("n1", "A", "sn", [(SAG, (1, 2, 0))]),
            [SAG],
            call={"candidate_id": "n1", "call": call},
        )
        assert prepare_identity(mem)["negative_case_count"] == 0
        result = recall_identity(sag((1, 2, 0)), mem)
        assert result["negative_cases"] == []
        assert result["identity"] == "A"


def test_confirm_with_negative_views_writes_each_sign_on_its_own_views():
    record = vcase("c1", "A", "sc", [(SAG, (1, 2, 0)), (COR, (3, 0, 0))])
    row = {
        "candidate_id": "c1",
        "call": "confirm",
        "views": [COR],
        "negative_views": [SAG],
    }
    mem = memory(
        [
            vcase("a2", "A", "sa", [(SAG, (3, 0, 0))]),
            vcase("b1", "B", "sb", [(SAG, (0, 0, 3)), (COR, (0, 0, 3))]),
            record,
        ],
        calls=[
            {"candidate_id": "a2", "call": "confirm"},
            {"candidate_id": "b1", "call": "confirm"},
            row,
        ],
    )
    add_negative(mem, copy.deepcopy(record), [SAG], append_call=False)
    prepared = prepare_identity(mem)
    seeds = {seed["case_id"]: seed for seed in prepared._seeds}
    negatives = {case["case_id"]: case for case in prepared._negatives}
    assert set(seeds["c1"]["banks"]) == {vbank(COR)}
    assert set(negatives["c1"]["banks"]) == {vbank(SAG)}
    rejected_facet = recall_identity(sag((1, 2, 0)), mem, prepared=prepared)
    assert rejected_facet["outcome"] == "unresolved_conflict"
    assert rejected_facet["conflicted_identities"] == ["A"]
    confirmed_facet = recall_identity(
        profile(None, banks={vbank(COR): [3, 0, 0]}), mem, prepared=prepared
    )
    assert confirmed_facet["outcome"] == "identified"
    assert confirmed_facet["identity"] == "A"
    assert confirmed_facet["negative_cases"] == []


def test_exclusion_removes_negative_cases_and_their_opposing_seeds_first():
    mem = memory(
        [
            vcase("a1", "A", "sa", [(SAG, (3, 0, 0))]),
            vcase("a2", "A", "sc", [(SAG, (1, 1, 0))]),
            vcase("b1", "B", "sb", [(SAG, (0, 0, 3))]),
        ]
    )
    seeds_only = copy.deepcopy(mem)
    add_negative(mem, vcase("n1", "A", "sn", [(SAG, (1, 2, 0))]), [SAG])
    query = sag((1, 2, 0))
    full = recall_identity(query, mem)
    [row] = full["negative_cases"]
    assert row["envelope"]["opponent_case_ids"] == ["a2"]
    assert (row["envelope"]["numerator"], row["envelope"]["denominator"]) == (
        "9",
        "10",
    )
    assert row["envelope"]["comparison_count"] == 2
    assert full["outcome"] == "unresolved_conflict"
    without_a2 = recall_identity(query, mem, exclude_study_uid="sc")
    [row] = without_a2["negative_cases"]
    assert row["envelope"]["opponent_case_ids"] == ["a1"]
    assert row["envelope"]["comparison_count"] == 1
    assert (row["envelope"]["numerator"], row["envelope"]["denominator"]) == (
        "9",
        "45",
    )
    held_out = recall_identity(query, mem, exclude_study_uid="sn")
    assert prepare_identity(mem, exclude_study_uid="sn")["negative_case_count"] == 0
    assert held_out["negative_cases"] == []
    assert held_out["outcome"] == "identified" and held_out["identity"] == "A"
    reference = recall_identity(query, seeds_only, exclude_study_uid="sn")
    assert held_out["cases"] == reference["cases"]


def test_prepared_signed_view_matches_unprepared_and_is_reusable():
    mem = rejected_a_memory()
    for exclude in (None, "sn", "sa"):
        prepared = prepare_identity(mem, exclude_study_uid=exclude)
        assert prepared["outcome"] == "prepared"
        for counts in ((1, 2, 0), (3, 0, 0), (0, 2, 1)):
            query = sag(counts)
            assert recall_identity(
                query, mem, exclude_study_uid=exclude, prepared=prepared
            ) == recall_identity(query, mem, exclude_study_uid=exclude)


def test_memory_without_signed_teaching_keeps_todays_output():
    mem = two_identity_memory()
    result = recall_identity(profile((1, 0, 0)), mem)
    # Pin computed by the code before signed teaching existed (e750739).
    assert (
        result["prepared_view"]["source_pin"]
        == (
            "e4317c133b3aeecf3ba0bc025ff60bc4ccc8dfe712a71e68556d33adf7662e96"  # pragma: allowlist secret
        )
    )
    assert sorted(result) == OLD_RECALL_KEYS
    assert sorted(result["cases"][0]) == [
        "case_id",
        "common_speaking_banks",
        "dot",
        "envelope",
        "envelope_status",
        "identity",
        "left_norm_sq",
        "lineage",
        "right_norm_sq",
        "speaks",
        "squared_cosine",
        "study_uid",
    ]
    assert sorted(prepare_identity(mem)) == [
        "exclude_study_uid",
        "outcome",
        "schema",
        "seed_count",
        "source_pin",
    ]
    declared_empty = copy.deepcopy(mem)
    teaching = declared_empty["object_identity_teaching"]
    teaching.update(
        negative_case_ids=[],
        negative_views={},
        negatives_not_written=[],
        alternative_positives=[],
    )
    declared_empty["object_identity_cases"] = {"schema": CASES_SCHEMA, "cases": []}
    for exclude in (None, "sa"):
        assert dict(prepare_identity(declared_empty, exclude_study_uid=exclude)) == (
            dict(prepare_identity(mem, exclude_study_uid=exclude))
        )
        for counts in ((1, 0, 0), (0, 1, 0), (1, 1, 0), (0, 0, 1)):
            query = profile(counts)
            assert recall_identity(
                query, declared_empty, exclude_study_uid=exclude
            ) == recall_identity(query, mem, exclude_study_uid=exclude)


def alternative_memory(with_alternative=True):
    """A patella-proposed candidate whose sagittal support is plainly femur."""
    mem = memory(
        [
            vcase("t1", "T", "st", [(SAG, (0, 3, 0))]),
            vcase("p1", "P", "sp", [(SAG, (0, 0, 3))]),
        ]
    )
    record = vcase("c1", "P", "sc", [(SAG, (3, 0, 0)), (COR, (0, 0, 3))])
    call = {"candidate_id": "c1", "call": "reject", "views": [SAG]}
    if with_alternative:
        call["also_positive"] = [{"identity": "F", "views": [SAG]}]
        add_alternative(mem, record, "F", [SAG])
    return add_negative(mem, record, [SAG], call=call)


def test_also_positive_facet_recalls_its_identity_and_leaves_others_alone():
    entry = "c1::also_positive::F"
    mem, plain = alternative_memory(), alternative_memory(with_alternative=False)
    femur_like = sag((3, 0, 0))
    found = recall_identity(femur_like, mem)
    assert found["outcome"] == "identified" and found["identity"] == "F"
    row = by_id(found)[entry]
    assert (row["identity"], row["source_case_id"], row["speaks"]) == ("F", "c1", True)
    assert found["opposed_identities"] == ["P"]
    assert recall_identity(femur_like, plain)["identity"] is None
    for counts in ((0, 3, 0), (0, 0, 3)):
        query = sag(counts)
        with_it, without_it = recall_identity(query, mem), recall_identity(query, plain)
        assert (
            with_it["outcome"],
            with_it["identity"],
            with_it["speaking_identities"],
        ) == (
            without_it["outcome"],
            without_it["identity"],
            without_it["speaking_identities"],
        )
    prepared = prepare_identity(mem)
    assert prepared["seed_count"] == 3
    assert prepared["alternative_positive_count"] == 1
    tibia = by_id(recall_identity(sag((0, 3, 0)), mem))["t1"]
    assert entry in tibia["envelope"]["opponent_case_ids"]
    held_out = recall_identity(femur_like, mem, exclude_study_uid="sc")
    assert entry not in by_id(held_out)
    assert held_out["identity"] is None
    assert (
        prepare_identity(mem, exclude_study_uid="sc")["alternative_positive_count"] == 0
    )


def _set_teaching(key, value):
    def mutate(mem):
        mem["object_identity_teaching"][key] = value

    return mutate


def _drop_identity_cases(mem):
    del mem["object_identity_cases"]


def _identity_cases_schema(mem):
    mem["object_identity_cases"]["schema"] = "other"


def _drop_negative_views(mem):
    del mem["object_identity_teaching"]["negative_views"]


def _duplicate_negative_view(mem):
    mem["object_identity_teaching"]["negative_views"]["n1"] = [SAG, SAG]


def _call_disagrees_with_negative_views(mem):
    mem["object_identity_teaching"]["calls"][-1]["views"] = [COR]


def test_malformed_signed_teaching_is_refused_by_name():
    for mutate, reason in (
        (_set_teaching("negative_case_ids", "n1"), "negative_case_ids_invalid"),
        (_set_teaching("negative_case_ids", ["n1", "n1"]), "negative_case_ids_invalid"),
        (_set_teaching("alternative_positives", "x"), "alternative_positives_invalid"),
        (_drop_identity_cases, "object_identity_cases_invalid"),
        (_identity_cases_schema, "object_identity_cases_invalid"),
        (_drop_negative_views, "negative_views_required"),
        (_duplicate_negative_view, "negative_views_invalid"),
        (_call_disagrees_with_negative_views, "negative_views_mismatch"),
    ):
        mem = rejected_a_memory()
        mutate(mem)
        assert prepare_identity(mem) == {"outcome": "invalid_input", "reason": reason}


def test_a_view_cannot_carry_two_claims_in_one_seed_call():
    record = vcase("a1", "A", "sa", [(SAG, (3, 0, 0)), (COR, (3, 0, 0))])
    for row in (
        {
            "candidate_id": "a1",
            "call": "confirm",
            "views": [SAG],
            "negative_views": [SAG],
        },
        {"candidate_id": "a1", "call": "confirm", "negative_views": [SAG]},
        {
            "candidate_id": "a1",
            "call": "confirm",
            "views": [COR, SAG],
            "also_positive": [{"identity": "B", "views": [SAG]}],
        },
    ):
        mem = memory([copy.deepcopy(record)], calls=[row])
        assert prepare_identity(mem) == {
            "outcome": "invalid_input",
            "reason": "teaching_call_views_overlap",
        }


def test_malformed_alternative_positives_are_refused_by_name():
    mem = alternative_memory()
    mem["object_identity_teaching"]["alternative_positives"][0]["views"] = [COR]
    assert prepare_identity(mem)["reason"] == "alternative_positive_views_mismatch"
    mem = alternative_memory()
    alternative = mem["object_identity_teaching"]["alternative_positives"][0]
    alternative["identity"] = "P"
    mem["object_identity_teaching"]["calls"][-1]["also_positive"][0]["identity"] = "P"
    assert prepare_identity(mem)["reason"] == "alternative_positive_identity_invalid"
    mem = alternative_memory()
    mem["object_identity_teaching"]["alternative_positives"][0]["entry_id"] = "t1"
    assert prepare_identity(mem)["reason"] == "duplicate_seed_case_id"
