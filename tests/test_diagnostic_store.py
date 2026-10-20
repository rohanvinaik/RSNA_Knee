from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from knee.diagnosis.models import Call, Case, Censor, Profile, Snapshot, Trust
from knee.diagnosis.store import StoreError, read_store, validate_case, write_store
from knee.encoding.counts import BankLayout, CountBundle, CountLayout


def _layout() -> CountLayout:
    return CountLayout(
        "layout:test:v1",
        "carrier:test:v1",
        (BankLayout("object/acl/sagittal", 4), BankLayout("object/acl/coronal", 4)),
    )


def _profile(
    *,
    source_id: str = "study:source",
    counts: tuple[tuple[int, ...], ...] | None = None,
) -> Profile:
    if counts is None:
        counts = ((0, 3, 0, 0), (0, 0, 0, 0))
    return Profile(
        subject="diagnosis/ACL",
        bundle=CountBundle(_layout(), counts),
        mode="full-native-v1",
        scope="object:acl+attachment-context",
        source_id=source_id,
        context=(("view", "sagittal"), ("acquisition", "fluid-sensitive")),
        bank_statuses=(
            ("object/acl/sagittal", "measured"),
            ("object/acl/coronal", "silent"),
        ),
        provenance=(("receipt", "sha256:receipt"), ("teacher", "independent-reader")),
    )


def _case(
    case_id: str,
    digit: int,
    *,
    study_uid: str | None = None,
    counts: tuple[tuple[int, ...], ...] | None = None,
    question: str = "ACL",
) -> Case:
    uid = study_uid or f"study:{case_id}"
    return Case(
        case_id=case_id,
        study_uid=uid,
        profile=_profile(source_id=uid, counts=counts),
        calls=(
            Call(
                question=question,
                digit=digit,
                source="train-label",
                words=f"call {digit}",
            ),
        ),
        teaching_revision="teach-r1",
    )


def _snapshot(*cases: Case) -> Snapshot:
    return Snapshot(
        revision="memory-r1",
        cases=tuple(cases),
        trust=(Trust(cases[0].case_id, "ACL", 3, 5, "independent-trust-source"),),
        censors=(
            Censor(
                "near-miss-r1",
                "ACL",
                -1,
                _profile(source_id="study:near-miss"),
                1,
                4,
                "confirmed-near-miss",
            ),
        ),
    )


def test_roundtrip_preserves_individual_positive_and_negative_cases(
    tmp_path: Path,
) -> None:
    positive = _case("case-positive", 1, counts=((0, 3, 0, 0), (0, 0, 0, 0)))
    negative = _case("case-negative", -1, counts=((0, 0, 0, 5), (0, 0, 0, 0)))
    snapshot = Snapshot(
        revision="memory-r7",
        cases=(positive, negative),
        trust=(
            Trust("case-positive", "ACL", 3, 5, "reviewed-radius"),
            Trust("case-negative", "ACL", 2, 5, "reviewed-radius"),
        ),
        censors=(
            Censor(
                "censor-1",
                "ACL",
                -1,
                _profile(source_id="miss-1"),
                1,
                8,
                "visual-near-miss",
            ),
        ),
    )

    receipt = write_store(tmp_path / "memory", snapshot)
    loaded = read_store(tmp_path / "memory")

    assert receipt["revision"] == "memory-r7"
    assert receipt["case_count"] == 2
    assert loaded == snapshot
    assert loaded.cases[0].calls[0].digit == 1
    assert loaded.cases[1].calls[0].digit == -1
    assert (
        loaded.cases[0].profile.bundle.counts != loaded.cases[1].profile.bundle.counts
    )
    assert loaded.cases[0].profile.context == positive.profile.context
    assert loaded.cases[0].profile.bank_statuses == positive.profile.bank_statuses
    assert loaded.cases[0].profile.provenance == positive.profile.provenance
    assert loaded.trust == snapshot.trust
    assert loaded.censors == snapshot.censors


def test_large_counts_remain_exact_and_archive_uses_no_pickle(tmp_path: Path) -> None:
    huge = 2**130 + 17
    case = _case("large", 1, counts=((huge, 0, 0, 0), (0, 0, 0, 0)))
    path = tmp_path / "large"

    write_store(path, Snapshot("large-r1", (case,)))

    assert read_store(path).cases[0].profile.bundle.counts[0][0] == huge
    with np.load(path / "profiles.npz", allow_pickle=False) as archive:
        assert archive["counts_decimal"].dtype.kind == "U"
        assert archive["counts_decimal"][0] == str(huge)
        assert archive["bank_indices"].tolist() == [0]
        assert archive["row_indices"].tolist() == [0]


def test_measured_middle_row_is_not_silence(tmp_path: Path) -> None:
    case = _case("middle", 0, counts=((0, 1, 0, 0), (0, 0, 0, 0)))
    path = tmp_path / "middle"

    write_store(path, Snapshot("middle-r1", (case,)))
    loaded = read_store(path).cases[0].profile.bundle.counts

    assert loaded[0] == (0, 1, 0, 0)
    assert any(loaded[0])
    assert loaded[1] == (0, 0, 0, 0)
    assert not any(loaded[1])
    assert loaded != tuple(tuple(0 for _ in bank) for bank in loaded)


@pytest.mark.parametrize("digit", [True, False, 2, -2, 1.0, "1", None])
def test_validate_case_rejects_non_plain_signed_digits(digit: object) -> None:
    malformed = _case("bad-digit", 1)
    object.__setattr__(malformed.calls[0], "digit", digit)

    assert validate_case(malformed) == "invalid_call_digit"


def test_validate_case_rejects_duplicate_questions_and_bad_count_types() -> None:
    duplicate_calls = _case("duplicate-calls", 1)
    object.__setattr__(
        duplicate_calls,
        "calls",
        duplicate_calls.calls + (Call("ACL", -1, "second-source"),),
    )
    bad_counts = _case("bool-count", 1, counts=((True, 0, 0, 0), (0, 0, 0, 0)))

    assert validate_case(duplicate_calls) == "duplicate_call_question"
    assert validate_case(bad_counts) == "invalid_profile_bundle"


@pytest.mark.parametrize(
    ("snapshot", "reason"),
    [
        (Snapshot("r1", (_case("same", 1), _case("same", -1))), "duplicate_case_id"),
        (
            Snapshot(
                "r1", (_case("one", 1),), trust=(Trust("missing", "ACL", 1, 2, "src"),)
            ),
            "unknown_trust_case",
        ),
        (
            Snapshot(
                "r1",
                (_case("one", 1),),
                censors=(Censor("c", "ACL", 0, _profile(), 1, 2, "src"),),
            ),
            "invalid_censor_answer",
        ),
    ],
)
def test_write_store_rejects_malformed_snapshots(
    tmp_path: Path, snapshot: Snapshot, reason: str
) -> None:
    with pytest.raises(StoreError, match=reason):
        write_store(tmp_path / "bad", snapshot)
    assert not (tmp_path / "bad").exists()


def test_abstention_only_case_is_retained_without_signed_promotion(
    tmp_path: Path,
) -> None:
    abstention = _case("abstain", 0)
    path = tmp_path / "abstain"

    write_store(path, Snapshot("abstain-r1", (abstention,)))
    loaded = read_store(path)

    assert len(loaded.cases) == 1
    assert loaded.cases[0].calls[0].digit == 0
    assert loaded.cases[0].case_id == "abstain"


def test_existing_store_is_immutable_and_not_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "immutable"
    original = Snapshot("r1", (_case("first", 1),))
    write_store(path, original)
    manifest_before = (path / "manifest.json").read_bytes()

    with pytest.raises(StoreError, match="store_already_exists"):
        write_store(path, Snapshot("r2", (_case("second", -1),)))

    assert (path / "manifest.json").read_bytes() == manifest_before
    assert read_store(path) == original


def test_read_rejects_missing_archive_and_digest_mismatch(tmp_path: Path) -> None:
    path = tmp_path / "corrupt"
    write_store(path, Snapshot("r1", (_case("one", 1),)))
    manifest_path = path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    archive = path / manifest["archive"]["file"]
    archive.write_bytes(archive.read_bytes() + b"corruption")

    with pytest.raises(StoreError, match="archive_digest_mismatch"):
        read_store(path)

    archive.unlink()
    with pytest.raises(StoreError, match="archive_missing"):
        read_store(path)


def test_read_rejects_malformed_manifest_and_encoding_fields(tmp_path: Path) -> None:
    path = tmp_path / "malformed"
    write_store(path, Snapshot("r1", (_case("one", 1),)))
    manifest_path = path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["encoding"]["integer_format"] = "float64"
    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(StoreError, match="invalid_encoding_metadata"):
        read_store(path)

    manifest_path.write_text("{")
    with pytest.raises(StoreError, match="malformed_manifest"):
        read_store(path)


def test_read_rejects_missing_store_and_non_directory(tmp_path: Path) -> None:
    with pytest.raises(StoreError, match="store_missing"):
        read_store(tmp_path / "absent")
    file_path = tmp_path / "not-a-directory"
    file_path.write_text("file")
    with pytest.raises(StoreError, match="store_not_directory"):
        read_store(file_path)


def test_large_mostly_silent_layout_is_sparse_and_shared_after_readback(
    tmp_path: Path,
) -> None:
    huge = 2**180 + 91
    banks = tuple(BankLayout(f"facet-{index:04d}", 512) for index in range(3696))
    layout = CountLayout("layout:production-size:v1", "carrier:512:v1", banks)
    zero_row = (0,) * 512
    counts_a = [zero_row] * len(banks)
    counts_b = [zero_row] * len(banks)
    row_a = [0] * 512
    row_a[511] = huge
    row_b = [0] * 512
    row_b[7] = 5
    counts_a[0] = tuple(row_a)
    counts_b[1] = tuple(row_b)
    profile_a = Profile(
        "diagnosis/ACL",
        CountBundle(layout, tuple(counts_a)),
        "full-v1",
        "composite",
        "study:a",
    )
    profile_b = Profile(
        "diagnosis/ACL",
        CountBundle(layout, tuple(counts_b)),
        "full-v1",
        "composite",
        "study:b",
    )
    cases = (
        Case("case-a", "study:a", profile_a, (Call("ACL", 1, "label"),), "r1"),
        Case("case-b", "study:b", profile_b, (Call("ACL", -1, "label"),), "r1"),
    )
    path = tmp_path / "production-size"

    write_store(path, Snapshot("large-r1", cases))

    manifest = json.loads((path / "manifest.json").read_text())
    assert len(manifest["layouts"]) == 1
    assert {profile["layout_index"] for profile in manifest["profiles"]} == {0}
    assert manifest["archive"]["nonzero_count"] == 2
    with np.load(path / "profiles.npz", allow_pickle=False) as archive:
        assert archive["counts_decimal"].tolist() == [str(huge), "5"]
        assert archive["profile_offsets"].tolist() == [0, 1, 2]
        assert archive["bank_indices"].tolist() == [0, 1]
        assert archive["row_indices"].tolist() == [511, 7]

    loaded = read_store(path)
    assert (
        loaded.cases[0].profile.bundle.layout is loaded.cases[1].profile.bundle.layout
    )
    assert loaded.cases[0].profile.bundle.counts[0][511] == huge
    assert loaded.cases[1].profile.bundle.counts[1][7] == 5
    shared_zero = loaded.cases[0].profile.bundle.counts[1]
    assert shared_zero == zero_row
    assert all(
        case.profile.bundle.counts[bank_index] is shared_zero
        for case in loaded.cases
        for bank_index in range(len(banks))
        if not any(case.profile.bundle.counts[bank_index])
    )


def _many_shared_profiles() -> Snapshot:
    layout = CountLayout(
        "layout:shared-production:v1",
        "carrier:512:v1",
        tuple(BankLayout(f"facet-{index:04d}", 512) for index in range(3696)),
    )
    silent = (0,) * 512
    active = (0,) * 511 + (2**180 + 91,)
    cases = []
    for index in range(24):
        rows = [silent] * len(layout.banks)
        rows[index] = active
        rows[-1] = active
        profile = Profile(
            "diagnosis/ACL",
            CountBundle(layout, tuple(rows)),
            "full-v1",
            "composite",
            f"study:{index}",
        )
        cases.append(
            Case(
                f"case:{index}",
                f"study:{index}",
                profile,
                (Call("ACL", 1 if index % 2 else -1, "label"),),
                "r1",
            )
        )
    return Snapshot("shared-r1", tuple(cases))


def test_shared_production_rows_are_checked_once_per_write_and_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from knee.diagnosis import store

    snapshot = _many_shared_profiles()
    original = store._plain_int
    zero_checks = 0
    zero = 0

    def counted(value: object) -> bool:
        nonlocal zero_checks
        if value is zero:
            zero_checks += 1
        return original(value)

    monkeypatch.setattr(store, "_plain_int", counted)
    path = tmp_path / "shared"
    write_store(path, snapshot)
    # One complete check for each of the two distinct immutable row objects.
    assert zero_checks <= 2 * 512
    zero_checks = 0
    loaded = read_store(path)
    # Each decoded nonzero bank is distinct; the silent row is shared.
    assert zero_checks <= (2 * len(snapshot.cases) + 1) * 512
    assert loaded == snapshot
    manifest = json.loads((path / "manifest.json").read_text())
    assert len(manifest["layouts"][0]["banks"]) == 3696
    assert manifest["archive"]["nonzero_count"] == 48
    with np.load(path / "profiles.npz", allow_pickle=False) as archive:
        assert archive["profile_offsets"].tolist() == list(range(0, 49, 2))
        assert archive["counts_decimal"].tolist() == [str(2**180 + 91)] * 48
    shared = loaded.cases[0].profile.bundle.counts[1]
    assert all(case.profile.bundle.counts[100] is shared for case in loaded.cases)


def test_read_constructs_a_silent_row_only_once_per_declared_width(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from knee.diagnosis import store

    path = tmp_path / "zero-construction"
    write_store(path, _many_shared_profiles())
    original = store._zero_row
    widths = []

    def counted(width: int) -> tuple[int, ...]:
        widths.append(width)
        return original(width)

    monkeypatch.setattr(store, "_zero_row", counted)
    loaded = read_store(path)
    assert widths == [512]
    assert len(loaded.cases) == 24


@pytest.mark.parametrize("bad_value", [True, -1, 1.0, "0", None])
def test_shared_row_is_fully_validated_before_silence_reuse(
    tmp_path: Path,
    bad_value: object,
) -> None:
    # A deceptive all-zero prefix must not hide a malformed last entry.
    row = (0,) * 511 + (bad_value,)
    layout = CountLayout(
        "layout:bad", "carrier:512", (BankLayout("a", 512), BankLayout("b", 512))
    )
    profile = Profile(
        "subject", CountBundle(layout, (row, row)), "full", "scope", "source"
    )
    case = Case("bad", "study", profile, (Call("ACL", -1, "label"),), "r1")
    assert validate_case(case) == "invalid_profile_bundle"
    with pytest.raises(StoreError, match="invalid_profile_bundle"):
        write_store(tmp_path / "bad", Snapshot("r1", (case,)))
    assert not (tmp_path / "bad").exists()


def test_reused_row_still_checks_each_declared_width_and_bank_name(
    tmp_path: Path,
) -> None:
    row = (0, 0, 0, 0)
    for layout in (
        CountLayout(
            "layout:width", "carrier", (BankLayout("a", 4), BankLayout("b", 5))
        ),
        CountLayout(
            "layout:names", "carrier", (BankLayout("a", 4), BankLayout("a", 4))
        ),
    ):
        profile = Profile(
            "subject", CountBundle(layout, (row, row)), "full", "scope", "source"
        )
        case = Case("bad", "study", profile, (Call("ACL", 1, "label"),), "r1")
        assert validate_case(case) == "invalid_profile_bundle"
        with pytest.raises(StoreError, match="invalid_profile_bundle"):
            write_store(
                tmp_path / layout.layout_id.replace(":", "-"), Snapshot("r1", (case,))
            )


def test_validation_reuse_does_not_survive_a_public_call(tmp_path: Path) -> None:
    case = _case("changed", 1)
    assert validate_case(case) == "valid"
    write_store(tmp_path / "first", Snapshot("r1", (case,)))
    object.__setattr__(case.profile.bundle, "counts", ((0, 0, 0, True), (0, 0, 0, 0)))
    assert validate_case(case) == "invalid_profile_bundle"
    with pytest.raises(StoreError, match="invalid_profile_bundle"):
        write_store(tmp_path / "second", Snapshot("r2", (case,)))


@pytest.mark.parametrize("value", [0, -1, 7, 2**180])
def test_plain_integer_decision_accepts_python_integers(value: int) -> None:
    from knee.diagnosis.store import _plain_int

    assert _plain_int(value) is True


@pytest.mark.parametrize("value", [True, False, 1.0, "1", None, ()])
def test_plain_integer_decision_rejects_other_types(value: object) -> None:
    from knee.diagnosis.store import _plain_int

    assert _plain_int(value) is False


def test_reuse_never_hashes_a_row_or_assumes_a_zero_prefix(tmp_path: Path) -> None:
    class ImmutableRow(tuple):
        def __hash__(self) -> int:
            raise AssertionError("row content must not be hashed")

    # The same active row occurs at multiple addresses and in several profiles.
    row = ImmutableRow((0, 0, 0, 13))
    first = _case("first", 1, counts=(row, row))
    second = _case("second", -1, counts=(row, row))
    path = tmp_path / "no-row-hash"
    snapshot = Snapshot("r1", (first, second))
    write_store(path, snapshot)
    assert read_store(path) == snapshot
    with np.load(path / "profiles.npz", allow_pickle=False) as archive:
        assert archive["profile_offsets"].tolist() == [0, 2, 4]
        assert archive["bank_indices"].tolist() == [0, 1, 0, 1]
        assert archive["row_indices"].tolist() == [3, 3, 3, 3]
        assert archive["counts_decimal"].tolist() == ["13"] * 4


def test_counts_beyond_interpreter_decimal_digit_limit_remain_exact(
    tmp_path: Path,
) -> None:
    # No process-wide integer digit-limit change is allowed for a store operation.
    import sys

    limit_before = sys.get_int_max_str_digits()
    value = 2**20000 + 17
    snapshot = Snapshot(
        "r1", (_case("huge", 1, counts=((value, 0, 0, 0), (0, 0, 0, 0))),)
    )
    assert validate_case(snapshot.cases[0]) == "valid"
    path = tmp_path / "unbounded-integer"
    write_store(path, snapshot)
    assert read_store(path) == snapshot
    assert sys.get_int_max_str_digits() == limit_before


def _rewrite_archive(path: Path, **replacements: object) -> None:
    import hashlib

    archive_path = path / "profiles.npz"
    with np.load(archive_path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    arrays.update(replacements)
    np.savez_compressed(archive_path, **arrays)
    manifest_path = path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["archive"]["sha256"] = hashlib.sha256(
        archive_path.read_bytes()
    ).hexdigest()
    manifest.pop("manifest_sha256")
    canonical = json.dumps(
        manifest,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()
    manifest["manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    manifest_path.write_text(json.dumps(manifest))


@pytest.mark.parametrize(
    ("replacement", "reason"),
    [
        (
            {"bank_indices": np.asarray([2, 1], dtype=np.uint64)},
            "sparse_bank_index_out_of_range",
        ),
        (
            {"row_indices": np.asarray([4, 3], dtype=np.uint64)},
            "sparse_row_index_out_of_range",
        ),
        (
            {"bank_indices": np.asarray([0, 0], dtype=np.uint64)},
            "sparse_addresses_not_canonical",
        ),
        (
            {"bank_indices": np.asarray([1, 0], dtype=np.uint64)},
            "sparse_addresses_not_canonical",
        ),
        ({"counts_decimal": np.asarray(["0", "1"])}, "invalid_count_encoding"),
        ({"counts_decimal": np.asarray(["01", "1"])}, "noncanonical_count_encoding"),
        ({"counts_decimal": np.asarray(["-1", "1"])}, "invalid_count_encoding"),
    ],
)
def test_read_rejects_malformed_sparse_addresses_and_values_after_checksum(
    tmp_path: Path,
    replacement: dict[str, object],
    reason: str,
) -> None:
    path = tmp_path / "malformed-sparse"
    snapshot = Snapshot("r1", (_case("one", 1, counts=((0, 0, 0, 1), (0, 0, 0, 1))),))
    write_store(path, snapshot)
    _rewrite_archive(path, **replacement)
    with pytest.raises(StoreError, match=reason):
        read_store(path)


def test_shared_row_decimal_serialization_is_reused_within_one_write(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from knee.diagnosis import store

    original = store._count_decimal
    calls = []

    def counted(value: int) -> str:
        calls.append(value)
        return original(value)

    monkeypatch.setattr(store, "_count_decimal", counted)
    snapshot = _many_shared_profiles()
    write_store(tmp_path / "first", snapshot)
    assert calls == [2**180 + 91]
    calls.clear()
    write_store(tmp_path / "second", snapshot)
    assert calls == [2**180 + 91]


@pytest.mark.parametrize(
    ("row", "expected"),
    [((), ()), ((0, 0, 0), ()), ((0, 7, 0, 2**180), ((1, 7), (3, 2**180)))],
)
def test_sparse_row_decision_preserves_exact_addresses(
    row: object, expected: object
) -> None:
    from knee.diagnosis.store import _validated_sparse_row

    assert _validated_sparse_row(row) == expected


@pytest.mark.parametrize("row", [[0, 1], None, (0, True), (0, -1), (0, 1.0), (0, "1")])
def test_sparse_row_decision_refuses_invalid_rows(row: object) -> None:
    from knee.diagnosis.store import _validated_sparse_row

    assert _validated_sparse_row(row) is None


def test_identical_counts_do_not_merge_distinct_layout_declarations(
    tmp_path: Path,
) -> None:
    from dataclasses import replace

    first = _case("first", 1)
    second = _case("second", -1)
    distinct = CountLayout(
        "layout:other", "carrier:other", (BankLayout("b", 4), BankLayout("a", 4))
    )
    second = replace(
        second,
        profile=replace(
            second.profile, bundle=CountBundle(distinct, first.profile.bundle.counts)
        ),
    )
    snapshot = Snapshot("r1", (first, second))
    path = tmp_path / "distinct-layouts"
    write_store(path, snapshot)
    manifest = json.loads((path / "manifest.json").read_text())
    assert len(manifest["layouts"]) == 2
    assert [p["layout_index"] for p in manifest["profiles"]] == [0, 1]
    loaded = read_store(path)
    assert loaded == snapshot
    assert (
        loaded.cases[0].profile.bundle.layout
        is not loaded.cases[1].profile.bundle.layout
    )


def test_manifest_checksum_still_guards_profile_metadata(tmp_path: Path) -> None:
    path = tmp_path / "metadata-tamper"
    write_store(path, Snapshot("r1", (_case("one", 1),)))
    manifest_path = path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["profiles"][0]["subject"] = "changed"
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(StoreError, match="manifest_digest_mismatch"):
        read_store(path)


@pytest.mark.parametrize("layout", [None, "layout", (), {}])
def test_missing_or_malformed_layout_is_a_named_rejection(
    tmp_path: Path, layout: object
) -> None:
    profile = Profile(
        "subject", CountBundle(layout, ((0,),)), "full", "scope", "source"
    )
    case = Case("bad", "study", profile, (Call("ACL", 1, "label"),), "r1")
    assert validate_case(case) == "invalid_profile_bundle"
    with pytest.raises(StoreError, match="invalid_profile_bundle"):
        write_store(tmp_path / "bad-layout", Snapshot("r1", (case,)))


def _expand_string_references_to_legacy(manifest: dict[str, object]) -> None:
    encoding = manifest["metadata_encoding"]
    assert isinstance(encoding, dict)
    strings = encoding["strings"]
    pair_table = encoding["pairs"]
    assert isinstance(strings, list)
    assert isinstance(pair_table, list)

    def decode(value: object) -> str:
        assert type(value) is int and 0 <= value < len(strings)
        result = strings[value]
        assert isinstance(result, str)
        return result

    def pairs(references: object) -> None:
        assert isinstance(references, list)
        for index, pair_ref in enumerate(references):
            assert type(pair_ref) is int and 0 <= pair_ref < len(pair_table)
            pair = pair_table[pair_ref]
            assert isinstance(pair, list) and len(pair) == 2
            references[index] = [decode(pair[0]), decode(pair[1])]

    for layout in manifest["layouts"]:
        layout["layout_id"] = decode(layout["layout_id"])
        layout["carrier_id"] = decode(layout["carrier_id"])
        for bank in layout["banks"]:
            bank["name"] = decode(bank["name"])
    for profile in manifest["profiles"]:
        for field in ("subject", "mode", "scope", "source_id"):
            profile[field] = decode(profile[field])
        for field in ("context", "bank_statuses", "provenance"):
            pairs(profile[field])
    for case in manifest["cases"]:
        for field in ("case_id", "study_uid", "teaching_revision"):
            case[field] = decode(case[field])
        for call in case["calls"]:
            for field in ("question", "source", "words"):
                call[field] = decode(call[field])
    for trust in manifest["trust"]:
        for field in ("case_id", "question", "source"):
            trust[field] = decode(trust[field])
    for censor in manifest["censors"]:
        for field in ("censor_id", "question", "source"):
            censor[field] = decode(censor[field])
    del manifest["metadata_encoding"]


def test_metadata_string_table_preserves_and_interns_large_unicode_values(
    tmp_path: Path,
) -> None:
    from knee.diagnosis.models import Censor, Trust
    from knee.diagnosis.store import _MetadataStringTable
    from knee.encoding.counts import BankLayout, CountBundle, CountLayout

    repeated = (" MRI映像—κ-line " * 12_000) + "終端"
    base = _profile()
    layout = CountLayout(
        "layout:独自",
        "carrier:三値",
        (BankLayout("bank/骨🦴", 4), BankLayout("bank/静", 4)),
    )
    bundle = CountBundle(layout, ((0, 3, 0, 0), (0, 0, 0, 0)))
    profiles = tuple(
        Profile(
            base.subject,
            bundle,
            base.mode,
            base.scope,
            f"source:{index}",
            context=(("view", "sagittal"), ("shared-context", repeated)),
            bank_statuses=(("bank/α", "measured"), ("bank/β", repeated)),
            provenance=(("source_layouts", repeated), ("producer", "exact-測定")),
        )
        for index in range(2)
    )
    cases = tuple(
        Case(
            f"case:{index}",
            f"study:{index}",
            profiles[index],
            (Call("ACL", 1 if index == 0 else -1, repeated, repeated),),
            "revision:共有",
        )
        for index in range(2)
    )
    snapshot = Snapshot(
        "metadata-r1",
        cases,
        (Trust("case:0", "ACL", 3, 5, repeated),),
        (Censor("censor:0", "ACL", -1, profiles[0], 1, 8, repeated),),
    )
    path = tmp_path / "metadata-interner"
    write_store(path, snapshot)

    manifest_path = path / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    encoding = manifest["metadata_encoding"]
    assert encoding["schema"] == _MetadataStringTable.schema
    table = encoding["strings"]
    assert table.count(repeated) == 1
    assert "bank/骨🦴" in table
    assert isinstance(manifest["profiles"][0]["subject"], int)
    assert (
        manifest["profiles"][0]["bank_statuses"]
        == manifest["profiles"][1]["bank_statuses"]
    )
    assert all(
        type(pair_id) is int for pair_id in manifest["profiles"][0]["provenance"]
    )
    assert manifest_bytes.count(repeated.encode("utf-8")) == 1
    assert manifest["archive"]["nonzero_count"] == 3

    loaded = read_store(path)
    assert loaded == snapshot
    assert loaded.cases[0].profile.bundle.layout.banks[0].name == "bank/骨🦴"
    assert (
        loaded.cases[0].profile.context[1][1] is loaded.cases[1].profile.context[1][1]
    )
    with np.load(path / "profiles.npz", allow_pickle=False) as archive:
        assert archive["counts_decimal"].tolist() == ["3", "3", "3"]


def test_metadata_string_table_rejects_bad_reference_after_valid_digest(
    tmp_path: Path,
) -> None:
    from knee.diagnosis.store import _canonical_json, _sha256

    path = tmp_path / "bad-string-reference"
    repeated = "相同語境"
    base = _profile()
    profile = Profile(
        base.subject,
        base.bundle,
        base.mode,
        base.scope,
        base.source_id,
        context=(("view", "sagittal"), ("shared", repeated)),
        provenance=(("source_layouts", repeated),),
    )
    write_store(
        path,
        Snapshot("metadata-r1", (Case("case:0", "study:0", profile, (), "r1"),)),
    )
    manifest_path = path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["profiles"][0]["context"][0] = len(manifest["metadata_encoding"]["pairs"])
    manifest.pop("manifest_sha256")
    manifest["manifest_sha256"] = _sha256(_canonical_json(manifest))
    manifest_path.write_bytes(_canonical_json(manifest) + b"\n")

    with pytest.raises(StoreError, match="invalid_metadata_pair_reference"):
        read_store(path)


def test_current_legacy_direct_string_manifest_still_reads(tmp_path: Path) -> None:
    from knee.diagnosis.store import _canonical_json, _sha256

    snapshot = Snapshot("legacy-r1", (_case("legacy", -1),))
    path = tmp_path / "legacy-current-format"
    write_store(path, snapshot)
    manifest_path = path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    _expand_string_references_to_legacy(manifest)
    manifest.pop("manifest_sha256")
    manifest["manifest_sha256"] = _sha256(_canonical_json(manifest))
    manifest_path.write_bytes(_canonical_json(manifest) + b"\n")

    assert read_store(path) == snapshot
