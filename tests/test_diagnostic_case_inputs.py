"""Direct behavioral pins for explicitly attributed diagnostic cases."""

from __future__ import annotations

from pathlib import Path

import pytest

from knee.diagnosis.case_inputs import (
    CaseInputError,
    call_profile_status,
    import_case_inputs,
)
from knee.diagnosis.models import Profile
from knee.diagnosis.store import validate_case
from knee.encoding.counts import BankLayout, CountBundle, CountLayout


def _profile(
    subject: str,
    counts: tuple[int, ...],
    *,
    source_id: str = "study-a",
    context: tuple[tuple[str, str], ...] = (("study_uid", "study-a"),),
) -> Profile:
    layout = CountLayout(
        "layout/v1", "carrier/v1", (BankLayout("signal", len(counts)),)
    )
    return Profile(
        subject,
        CountBundle(layout, (counts,)),
        "full",
        "object:" + subject,
        source_id,
        context=context,
    )


def _document(*cases: dict) -> dict:
    return {"schema": "knee.diagnostic-case-inputs/v1", "cases": list(cases)}


def _case(subject: str, calls: list[dict], *, uid: str = "study-a") -> dict:
    return {"study_uid": uid, "subject": subject, "calls": calls}


def test_call_profile_status_positive_signed_call_is_preserved() -> None:
    assert call_profile_status(1, True) == "signed"


def test_call_profile_status_negative_signed_call_is_preserved() -> None:
    assert call_profile_status(-1, True) == "signed"


def test_call_profile_status_zero_is_abstention_even_for_silent_profile() -> None:
    assert call_profile_status(0, False) == "abstention"


def test_call_profile_status_never_accepts_signed_silent_profile() -> None:
    assert call_profile_status(1, False) == "signed_silent_profile"


def test_call_profile_status_rejects_bool_and_invalid_speaking_state() -> None:
    assert call_profile_status(True, True) == "invalid_call_digit"
    assert call_profile_status(1, 1) == "invalid_profile_speaking_state"


def test_import_resolves_exact_profiles_and_keeps_only_explicit_calls() -> None:
    acl = _profile("acl", (0, 3, 0))
    composed = _profile("diagnosis/ACL", (2, 0, 1))
    profiles = {"study-a": (acl, composed)}
    document = _document(
        _case("acl", [{"question": "ACL", "digit": -1, "source": "human-call"}]),
        _case(
            "diagnosis/ACL",
            [
                {
                    "question": "ACL",
                    "digit": 1,
                    "source": "reviewed-call",
                    "words": "explicit case attribution",
                }
            ],
        ),
    )

    snapshot, receipt = import_case_inputs(document, profiles, revision="design-r1")

    assert len(snapshot.cases) == 2
    assert [case.profile.subject for case in snapshot.cases] == [
        "acl",
        "diagnosis/ACL",
    ]
    assert [case.calls[0].digit for case in snapshot.cases] == [-1, 1]
    assert [case.profile for case in snapshot.cases] == [acl, composed]
    assert all(validate_case(case) == "valid" for case in snapshot.cases)
    assert snapshot.trust == ()
    assert snapshot.censors == ()
    assert receipt["case_count"] == 2
    assert receipt["trust_count"] == receipt["censor_count"] == 0


def test_import_case_id_is_order_independent_but_covers_profile_and_calls() -> None:
    profile = _profile("acl", (0, 3, 0))
    profiles = {"study-a": (profile,)}
    calls = [
        {"question": "B", "digit": -1, "source": "source-b"},
        {"question": "A", "digit": 1, "source": "source-a"},
    ]
    first, _ = import_case_inputs(
        _document(_case("acl", calls)), profiles, revision="r1"
    )
    second, _ = import_case_inputs(
        _document(_case("acl", list(reversed(calls)))), profiles, revision="r1"
    )
    changed, _ = import_case_inputs(
        _document(
            _case(
                "acl",
                [{"question": "A", "digit": -1, "source": "source-a"}],
            )
        ),
        profiles,
        revision="r1",
    )

    assert first.cases[0].case_id == second.cases[0].case_id
    assert first.cases[0].case_id != changed.cases[0].case_id
    assert tuple(call.question for call in first.cases[0].calls) == ("A", "B")


def test_silent_profile_accepts_explicit_abstention_only() -> None:
    silent = _profile("acl", (0, 0, 0))
    snapshot, _ = import_case_inputs(
        _document(_case("acl", [{"question": "ACL", "digit": 0, "source": "review"}])),
        {"study-a": (silent,)},
        revision="r1",
    )
    assert snapshot.cases[0].calls[0].digit == 0
    with pytest.raises(CaseInputError, match="signed_silent_profile"):
        import_case_inputs(
            _document(
                _case("acl", [{"question": "ACL", "digit": 1, "source": "review"}])
            ),
            {"study-a": (silent,)},
            revision="r1",
        )


def test_import_reads_json_path_and_records_exact_source_digest(tmp_path: Path) -> None:
    profile = _profile("acl", (0, 1))
    path = tmp_path / "cases.json"
    path.write_text(
        '{"schema":"knee.diagnostic-case-inputs/v1","cases":['
        '{"study_uid":"study-a","subject":"acl","calls":['
        '{"question":"ACL","digit":1,"source":"review"}]}]}',
        encoding="utf-8",
    )
    _, receipt = import_case_inputs(path, {"study-a": (profile,)}, revision="r1")
    assert receipt["source"] == str(path.resolve())
    assert len(receipt["source_sha256"]) == 64


@pytest.mark.parametrize(
    ("document", "profiles", "revision", "reason"),
    [
        ({"schema": "wrong", "cases": []}, {}, "r1", "schema_unsupported"),
        (_document(), {"study-a": ()}, "", "revision_invalid"),
        (
            _document(
                _case("acl", [{"question": "ACL", "digit": True, "source": "s"}])
            ),
            {"study-a": (_profile("acl", (1,)),)},
            "r1",
            "digit",
        ),
        (
            _document(_case("acl", [{"question": "ACL", "digit": 1, "source": ""}])),
            {"study-a": (_profile("acl", (1,)),)},
            "r1",
            "source_invalid",
        ),
        (
            _document(
                _case(
                    "acl",
                    [{"question": "ACL", "digit": 1, "source": "s"}],
                    uid="missing",
                )
            ),
            {"study-a": (_profile("acl", (1,)),)},
            "r1",
            "study_uid_not_found",
        ),
        (
            _document(_case("acl", [{"question": "ACL", "digit": 1, "source": "s"}])),
            {"study-a": (_profile("other", (1,)),)},
            "r1",
            "subject_not_found",
        ),
    ],
)
def test_import_rejects_malformed_or_unmatched_records(
    document: dict,
    profiles: dict[str, tuple[Profile, ...]],
    revision: str,
    reason: str,
) -> None:
    with pytest.raises(CaseInputError, match=reason):
        import_case_inputs(document, profiles, revision=revision)


def test_import_rejects_ambiguous_and_duplicate_profile_references() -> None:
    profile = _profile("acl", (1,))
    with pytest.raises(CaseInputError, match="subject_ambiguous"):
        import_case_inputs(
            _document(_case("acl", [{"question": "ACL", "digit": 1, "source": "s"}])),
            {"study-a": (profile, profile)},
            revision="r1",
        )
    row = _case("acl", [{"question": "ACL", "digit": 1, "source": "s"}])
    with pytest.raises(CaseInputError, match="reference_duplicate"):
        import_case_inputs(_document(row, row), {"study-a": (profile,)}, revision="r1")


@pytest.mark.parametrize(
    ("profile_inventory", "reason"),
    [
        (None, "case_study_profiles_invalid"),
        ((object(),), "case_study_profile_record_invalid"),
    ],
)
def test_import_rejects_malformed_profile_inventory(
    profile_inventory: object, reason: str
) -> None:
    document = _document(
        _case("acl", [{"question": "ACL", "digit": 1, "source": "review"}])
    )
    with pytest.raises(CaseInputError, match=reason):
        import_case_inputs(
            document,
            {"study-a": profile_inventory},  # type: ignore[dict-item]
            revision="r1",
        )


def test_import_rejects_study_metadata_mismatch_and_duplicate_question_calls() -> None:
    mismatched = _profile("acl", (1,), context=(("study_uid", "study-b"),))
    with pytest.raises(CaseInputError, match="study_uid_mismatch"):
        import_case_inputs(
            _document(_case("acl", [{"question": "ACL", "digit": 1, "source": "s"}])),
            {"study-a": (mismatched,)},
            revision="r1",
        )
    profile = _profile("acl", (1,))
    duplicate_calls = [
        {"question": "ACL", "digit": 1, "source": "s1"},
        {"question": "ACL", "digit": -1, "source": "s2"},
    ]
    with pytest.raises(CaseInputError, match="question_duplicate"):
        import_case_inputs(
            _document(_case("acl", duplicate_calls)),
            {"study-a": (profile,)},
            revision="r1",
        )
