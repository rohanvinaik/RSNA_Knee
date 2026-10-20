"""Tests for exact unified-object profile assembly."""

from __future__ import annotations

from dataclasses import fields, replace

import numpy as np
import pytest

from knee.encoding.counts import CountLayout, add_counts
from knee.encoding.object_profile import (
    PLACE_CONFLICT,
    PLACE_COUNTED,
    PLACE_DUPLICATE,
    PLACE_NO_MEASUREMENT,
    PLACE_NOT_ASSEMBLED,
    BankFacet,
    FacetCoordinate,
    ObjectProfile,
    PlaceAddressBatch,
    ProfileCode,
    RowcodeBatch,
    SourceLink,
    assemble_object_profile,
    compile_profile_layout,
    registry_problem,
    validate_profile_layout,
)
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    compile_layout,
)

REF = "a" * 64
COORD_A = FacetCoordinate("sagittal", "t2", "fine", "anterior")
COORD_B = FacetCoordinate("coronal", "t1", "coarse", None)
REGISTRY = (BankFacet("b_a", COORD_A), BankFacet("b_b", COORD_B))


def make_spec(version="v1"):
    return LayoutSpec(
        version,
        "carrier-test",
        (
            BankSpec(
                "b_a",
                "facet_a",
                (
                    MetricSpec("m", MetricKind.DIGIT),
                    MetricSpec("w", MetricKind.WORDS, ("x", "y")),
                ),
            ),
            BankSpec("b_b", "facet_b", (MetricSpec("n", MetricKind.DIGIT),)),
        ),
    )


def make_pl(registry=REGISTRY, ref=REF, version="v1"):
    pl = compile_profile_layout(make_spec(version), registry, ref)
    assert pl is not None
    return pl


def batch(
    pl,
    bank="b_a",
    metric="m",
    codes=(1,),
    coords=((0, 0),),
    source="src1",
    frame="f1",
    kind="native_rc",
    coord=None,
    link="obs0",
):
    if coord is None:
        coord = COORD_A if bank == "b_a" else COORD_B
    if kind == "native_rc":
        arr = np.array(coords, dtype=np.int32).reshape(-1, 2)
    else:
        arr = np.array(coords, dtype=np.float64).reshape(-1, 3)
    return RowcodeBatch(
        bank,
        metric,
        coord,
        source,
        pl.compiled.fingerprint,
        pl.count_layout,
        pl.reference_set_identity,
        np.array(codes, dtype=np.int16),
        PlaceAddressBatch(kind, frame, arr),
        SourceLink(link, "artifact0", "rows", "idx"),
    )


def count_at(result, bank, row):
    return {(b, r): c for b, r, c in result.profile.entries}.get((bank, row), 0)


# --- layout binding -------------------------------------------------------


def test_registry_fingerprint_alters_compiled_version_and_fingerprint():
    pl = make_pl()
    other = make_pl(registry=(BankFacet("b_a", COORD_B), BankFacet("b_b", COORD_B)))
    plain = compile_layout(make_spec())
    assert pl.declared_version == "v1"
    assert pl.compiled.version == f"v1:facet-registry:{pl.registry_fingerprint}"
    assert pl.compiled.fingerprint != plain.fingerprint
    assert pl.compiled.fingerprint != other.compiled.fingerprint
    assert pl.count_layout.layout_id != other.count_layout.layout_id
    assert pl.compiled.fingerprint in pl.count_layout.layout_id
    assert REF in pl.count_layout.layout_id
    reordered = make_pl(registry=tuple(reversed(REGISTRY)))
    assert reordered.compiled.fingerprint == pl.compiled.fingerprint


def test_common_count_layout_validation():
    pl = make_pl()
    assert validate_profile_layout(pl)
    bad = replace(
        pl,
        count_layout=CountLayout(
            "x", pl.count_layout.carrier_id, pl.count_layout.banks
        ),
    )
    assert not validate_profile_layout(bad)
    assert not validate_profile_layout(replace(pl, reference_set_identity="b" * 64))
    assert not validate_profile_layout(replace(pl, registry_fingerprint="0" * 64))
    assert not validate_profile_layout("nope")


def test_same_bank_map_conflict_and_incomplete_registry():
    conflicting = (
        BankFacet("b_a", COORD_A),
        BankFacet("b_a", COORD_B),
        BankFacet("b_b", COORD_B),
    )
    assert registry_problem(conflicting) == "facet_mapping_conflict"
    assert compile_profile_layout(make_spec(), conflicting, REF) is None
    assert (
        compile_profile_layout(make_spec(), (BankFacet("b_a", COORD_A),), REF) is None
    )
    assert compile_profile_layout(make_spec(), REGISTRY, "") is None


# --- efficiency -----------------------------------------------------------


def test_batch_efficiency_no_per_place_records():
    pl = make_pl()
    n = 200_000
    coords = np.stack([np.arange(n), np.zeros(n, dtype=np.int64)], axis=1)
    codes = (np.arange(n) % 3).astype(np.int16)
    b = RowcodeBatch(
        "b_a",
        "m",
        COORD_A,
        "s",
        pl.compiled.fingerprint,
        pl.count_layout,
        REF,
        codes,
        PlaceAddressBatch("native_rc", "f", coords.astype(np.int32)),
        SourceLink("o", "a", "r", "i"),
    )
    r = assemble_object_profile("femur", pl, [b])
    assert r.code is ProfileCode.OK
    rec = r.batches[0]
    assert isinstance(rec.row_status, np.ndarray) and rec.row_status.dtype == np.int8
    assert rec.row_status.nbytes == n
    assert rec.counted == n
    assert len(r.profile.entries) == 3
    assert sum(c for _, _, c in r.profile.entries) == n
    for f in fields(r):
        value = getattr(r, f.name)
        if isinstance(value, (list, tuple)):
            assert len(value) < 100


# --- duplicate / conflict rule ----------------------------------------------


def test_identical_observed_repeat_counts_once_and_links_retained():
    pl = make_pl()
    a = batch(pl, codes=(2,), link="o1")
    b = batch(pl, codes=(2,), link="o2")
    r = assemble_object_profile("o", pl, [a, b])
    assert r.code is ProfileCode.OK
    assert count_at(r, "b_a", 2) == 1
    assert r.batches[0].row_status[0] == PLACE_COUNTED
    assert r.batches[1].row_status[0] == PLACE_DUPLICATE
    assert r.batches[0].source_link.observation == "o1"
    assert r.batches[1].source_link.observation == "o2"


def test_different_observed_rowcodes_conflict_and_count_neither():
    pl = make_pl()
    r = assemble_object_profile(
        "o", pl, [batch(pl, codes=(0,), link="o1"), batch(pl, codes=(2,), link="o2")]
    )
    assert r.code is ProfileCode.CONFLICTING
    assert r.profile.entries == ()
    assert all(rec.row_status[0] == PLACE_CONFLICT for rec in r.batches)
    assert len(r.conflicts) == 1
    c = r.conflicts[0]
    assert c.event_count == 1
    assert sorted(c.link_batch.tolist()) == [0, 1]
    assert sorted(c.link_rowcode.tolist()) == [0, 2]


def test_uncontested_events_survive_other_conflicts():
    pl = make_pl()
    a = batch(pl, codes=(0, 1), coords=((0, 0), (5, 5)))
    b = batch(pl, codes=(2, 1), coords=((0, 0), (5, 5)))
    r = assemble_object_profile("o", pl, [a, b])
    assert r.code is ProfileCode.CONFLICTING
    assert count_at(r, "b_a", 1) == 1
    assert count_at(r, "b_a", 0) == 0 and count_at(r, "b_a", 2) == 0


def test_minus_one_plus_observed_and_unique_minus_one():
    pl = make_pl()
    none = batch(pl, codes=(-1,), link="o1")
    seen = batch(pl, codes=(2,), link="o2")
    r = assemble_object_profile("o", pl, [none, seen])
    assert count_at(r, "b_a", 2) == 1
    assert r.batches[0].row_status[0] == PLACE_NO_MEASUREMENT
    assert r.batches[0].status is ProfileCode.SILENT
    assert r.batches[1].row_status[0] == PLACE_COUNTED
    assert r.code is ProfileCode.PARTIAL

    alone = assemble_object_profile("o", pl, [none])
    assert alone.code is ProfileCode.SILENT
    assert alone.profile.entries == ()
    assert alone.batches[0].source_link.observation == "o1"

    conflict = assemble_object_profile(
        "o", pl, [none, batch(pl, codes=(0,)), batch(pl, codes=(2,))]
    )
    assert conflict.batches[0].row_status[0] == PLACE_NO_MEASUREMENT
    assert conflict.profile.entries == ()


def test_partial_batch_status():
    pl = make_pl()
    r = assemble_object_profile(
        "o", pl, [batch(pl, codes=(-1, 1), coords=((0, 0), (1, 1)))]
    )
    assert r.batches[0].status is ProfileCode.PARTIAL
    assert r.code is ProfileCode.PARTIAL
    assert count_at(r, "b_a", 1) == 1


def test_known_middle_row_counts():
    pl = make_pl()
    r = assemble_object_profile("o", pl, [batch(pl, codes=(1,))])
    assert r.code is ProfileCode.OK
    assert count_at(r, "b_a", 1) == 1


# --- event separation ---------------------------------------------------------


def test_source_place_bank_metric_and_facet_separation():
    pl = make_pl()
    r = assemble_object_profile(
        "o", pl, [batch(pl, source="s1"), batch(pl, source="s2")]
    )
    assert count_at(r, "b_a", 1) == 2
    r = assemble_object_profile(
        "o", pl, [batch(pl, coords=((0, 0),)), batch(pl, coords=((0, 1),))]
    )
    assert count_at(r, "b_a", 1) == 2
    # different metric (words rows start at 3) and different bank/facet
    r = assemble_object_profile(
        "o",
        pl,
        [
            batch(pl, metric="m", codes=(1,)),
            batch(pl, metric="w", codes=(3,)),
            batch(pl, bank="b_b", metric="n", codes=(1,)),
        ],
    )
    assert r.code is ProfileCode.OK
    assert count_at(r, "b_a", 1) == 1
    assert count_at(r, "b_a", 3) == 1
    assert count_at(r, "b_b", 1) == 1


def test_native_rc_and_lps_do_not_alias():
    pl = make_pl()
    native = batch(pl, coords=((1, 2),))
    lps = batch(pl, kind="patient_lps", coords=((1.0, 2.0, 0.0),))
    other_frame = batch(pl, coords=((1, 2),), frame="f2")
    r = assemble_object_profile("o", pl, [native, lps, other_frame])
    assert count_at(r, "b_a", 1) == 3
    zero = batch(pl, kind="patient_lps", coords=((0.0, 1.0, 2.0),))
    neg = batch(pl, kind="patient_lps", coords=((-0.0, 1.0, 2.0),))
    r = assemble_object_profile("o", pl, [zero, neg])
    assert count_at(r, "b_a", 1) == 1


def test_facet_mapping_conflict_is_never_pooled():
    pl = make_pl()
    good = batch(pl, coords=((0, 0),), link="good")
    wrong = batch(pl, coord=COORD_B, coords=((9, 9),), link="wrong")
    r = assemble_object_profile("o", pl, [good, wrong])
    assert r.code is ProfileCode.FACET_MAPPING_CONFLICT
    assert count_at(r, "b_a", 1) == 1
    assert r.batches[1].row_status[0] == PLACE_NOT_ASSEMBLED
    assert r.batches[1].source_link.observation == "wrong"
    assert r.mismatches[0].code is ProfileCode.FACET_MAPPING_CONFLICT


# --- mismatch / malformed -------------------------------------------------------


def test_identity_mismatches_named_with_links_and_uncontested_kept():
    pl = make_pl()
    other = make_pl(registry=(BankFacet("b_a", COORD_B), BankFacet("b_b", COORD_B)))
    old = batch(other, link="old")
    old2 = replace(batch(pl, link="ref"), reference_set_identity="c" * 64)
    good = batch(pl, coords=((3, 3),), link="good")
    r = assemble_object_profile("o", pl, [old, old2, good])
    assert r.code is ProfileCode.MISMATCH
    assert count_at(r, "b_a", 1) == 1
    assert len(r.mismatches) == 2
    assert "layout_fingerprint" in r.mismatches[0].fields
    assert "count_layout" in r.mismatches[0].fields
    assert "reference_set_identity" in r.mismatches[1].fields
    assert r.batches[0].source_link.observation == "old"
    assert r.batches[0].row_status[0] == PLACE_NOT_ASSEMBLED


def _mutations():
    pl = make_pl()
    base = batch(pl, codes=(1, 1), coords=((0, 0), (1, 1)))
    ok_addr = base.addresses
    yield pl, replace(base, rowcodes=np.array([1, 1], dtype=np.int32))
    yield pl, replace(base, rowcodes=np.zeros((2, 1), dtype=np.int16))
    yield pl, replace(base, rowcodes=np.array([1], dtype=np.int16))
    yield pl, replace(base, rowcodes=np.array([1, 3], dtype=np.int16))  # outside m rows
    yield pl, replace(base, rowcodes=np.array([1, -2], dtype=np.int16))
    yield pl, replace(base, rowcodes=np.array([1, 600], dtype=np.int16))
    yield (
        pl,
        replace(
            base,
            addresses=PlaceAddressBatch(
                "native_rc", "f", np.zeros((2, 2), dtype=np.float64)
            ),
        ),
    )
    yield (
        pl,
        replace(
            base,
            addresses=PlaceAddressBatch("native_rc", "f", np.array([[0, 0], [-1, 0]])),
        ),
    )
    yield (
        pl,
        replace(
            base,
            addresses=PlaceAddressBatch(
                "patient_lps",
                "f",
                np.array([[0, 0, np.nan], [0, 0, 0]], dtype=np.float64),
            ),
        ),
    )
    yield (
        pl,
        replace(
            base,
            addresses=PlaceAddressBatch(
                "patient_lps", "f", np.zeros((2, 3), dtype=np.float32)
            ),
        ),
    )
    yield (
        pl,
        replace(base, addresses=PlaceAddressBatch("weird", "f", ok_addr.coordinates)),
    )
    yield (
        pl,
        replace(
            base, addresses=PlaceAddressBatch("native_rc", "", ok_addr.coordinates)
        ),
    )
    yield pl, replace(base, source_link=None)
    yield pl, replace(base, source_link=SourceLink("", "a", "r", "i"))
    yield pl, replace(base, bank="missing")
    yield pl, replace(base, metric="missing")
    yield pl, replace(base, measurement_source_identity="")
    yield pl, "not a batch"


@pytest.mark.parametrize("pl,bad", list(_mutations()))
def test_malformed_batches_named_and_isolated(pl, bad):
    good = batch(pl, coords=((7, 7),), link="good")
    r = assemble_object_profile("o", pl, [bad, good])
    assert r.code is ProfileCode.MALFORMED
    assert r.batches[0].status is ProfileCode.MALFORMED
    assert r.batches[0].detail
    assert len(r.malformed) == 1
    assert count_at(r, "b_a", 1) == 1
    assert r.batches[1].status is ProfileCode.VALID


def test_invalid_layout_object_and_batches_container():
    pl = make_pl()
    b = batch(pl)
    bad_pl = replace(pl, registry_fingerprint="0" * 64)
    r = assemble_object_profile("o", bad_pl, [b])
    assert r.code is ProfileCode.MALFORMED
    assert r.batches[0].source_link.observation == "obs0"
    assert r.profile.entries == ()
    assert assemble_object_profile("", pl, [b]).code is ProfileCode.MALFORMED
    assert assemble_object_profile("o", pl, "nope").code is ProfileCode.MALFORMED
    assert assemble_object_profile("o", pl, []).code is ProfileCode.SILENT


def test_links_retained_on_every_outcome():
    pl = make_pl()
    mixed = [
        batch(pl, codes=(0,), link="a"),
        batch(pl, codes=(2,), link="b"),
        batch(pl, codes=(-1,), coords=((4, 4),), link="c"),
        replace(batch(pl, link="d"), layout_fingerprint="z"),
        replace(batch(pl, link="e"), rowcodes=np.array([1], dtype=np.int8)),
        batch(pl, coord=COORD_B, link="f"),
    ]
    r = assemble_object_profile("o", pl, mixed)
    assert [rec.source_link.observation for rec in r.batches] == list("abcdef")
    assert [rec.place_count for rec in r.batches][:4] == [1, 1, 1, 1]
    assert set(r.outcomes) >= {
        ProfileCode.CONFLICTING,
        ProfileCode.SILENT,
        ProfileCode.MISMATCH,
        ProfileCode.MALFORMED,
        ProfileCode.FACET_MAPPING_CONFLICT,
    }


# --- exact CountBundle round trip and large counts --------------------------------


def test_sparse_to_count_bundle_round_trip_and_decode():
    pl = make_pl()
    r = assemble_object_profile(
        "o",
        pl,
        [
            batch(pl, codes=(0, 1, 1), coords=((0, 0), (1, 0), (2, 0))),
            batch(pl, metric="w", codes=(4,)),
            batch(pl, bank="b_b", metric="n", codes=(2,)),
        ],
    )
    bundle = r.to_count_bundle()
    assert bundle is not None
    assert bundle.layout == pl.count_layout
    assert bundle.layout.layout_id.endswith(REF)
    assert bundle.counts[0][0] == 1 and bundle.counts[0][1] == 2
    assert bundle.counts[0][4] == 1
    assert bundle.counts[1][2] == 1
    assert sum(sum(bank) for bank in bundle.counts) == 5
    assert all(type(c) is int for bank in bundle.counts for c in bank)
    sparse = tuple(
        (pl.count_layout.banks[bi].name, ri, c)
        for bi, bank in enumerate(bundle.counts)
        for ri, c in enumerate(bank)
        if c
    )
    assert sparse == r.profile.entries
    decoded = r.decoded_names()
    assert decoded is not None
    assert ("b_a", "facet_a", "m", "0", 2) in decoded
    assert ("b_b", "facet_b", "n", "+1", 1) in decoded


def test_large_exact_counts_stay_python_integers():
    pl = make_pl()
    big = 10**40
    profile = ObjectProfile("o", pl.count_layout, (("b_a", 1, big),))
    bundle = profile.to_count_bundle()
    assert bundle.counts[0][1] == big and type(bundle.counts[0][1]) is int
    doubled = add_counts(bundle, bundle)
    assert doubled.bundle.counts[0][1] == 2 * big
    assert (
        ObjectProfile("o", pl.count_layout, (("nope", 0, 1),)).to_count_bundle() is None
    )
    assert (
        ObjectProfile("o", pl.count_layout, (("b_a", 512, 1),)).to_count_bundle()
        is None
    )
    r = assemble_object_profile(
        "o",
        pl,
        [
            batch(
                pl,
                codes=[1] * 100_000,
                coords=[(i, 0) for i in range(100_000)],
            )
        ],
    )
    assert count_at(r, "b_a", 1) == 100_000
    assert type(r.profile.entries[0][2]) is int


def test_big_endian_native_rc_uint64_above_int64_is_malformed():
    pl = make_pl()
    bad = batch(pl)
    coordinates = np.array([[2**63, 0]], dtype=">u8")
    malformed = replace(
        bad, addresses=PlaceAddressBatch("native_rc", "f1", coordinates)
    )
    result = assemble_object_profile("o", pl, [malformed])
    assert result.code is ProfileCode.MALFORMED
    assert result.batches[0].detail == "native_rc_too_large"
