# tests/test_encoding_composition_cross_view_intent.py
"""Cross-view composition intent, exercised through the public composition APIs.

One anatomical object is composed across native views.  An exact repeated
source/place/facet/metric event counts once and every link is retained.
Different observed codes for the same event stay a named conflict.  An unread
place is neither a conflict nor a zero row.  Duplicate observation plans do not
change reference identity, and reference qualifications stay tied to the actual
declared view.  The static layout carries no patient UID.

The references below are minimal TEST-ONLY edges (low=0.0, high=1.0).  They
certify arithmetic and wiring only, not any clinical norm.
"""

from __future__ import annotations

from collections import Counter

import numpy as np

from knee.encoding.carrier import HadamardCarrier
from knee.encoding.composition import (
    CompositionCode,
    StudyComposer,
    prepare_composition,
)
from knee.encoding.composition_output import serialize_study_composition
from knee.encoding.handoff import AddressedEncoding
from knee.encoding.object_profile import (
    PLACE_CONFLICT,
    PLACE_COUNTED,
    PLACE_DUPLICATE,
    PLACE_NO_MEASUREMENT,
    ProfileCode,
)
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    NumericReference,
    PlaceReading,
    compile_layout,
    encode_places,
)

VIEW_S = ("sagittal", "fat-suppressed", "fluid")
VIEW_C = ("coronal", "fat-suppressed", "fluid")
OBJECT = "cartilage"
CENTRE = (0, 0, 0)
UP_RIGHT = (1, 1, 0)  # native points (1,1) and (2,2) under the identity-like frame


def _base():
    carrier = HadamardCarrier.from_banks(("intensity",))
    base = compile_layout(
        LayoutSpec(
            "v1",
            carrier.identity,
            (
                BankSpec(
                    "intensity",
                    "signal",
                    (MetricSpec("level", MetricKind.DIGIT, ()),),
                ),
            ),
        )
    )
    assert base is not None
    return base


def _declaration():
    return {
        "version": "intent-v1",
        "view_roles": [list(VIEW_S), list(VIEW_C)],
        "bank_plans": [
            {
                "base_bank": "intensity",
                "lens": "native-signal",
                "scale_scope": "bounded-plane",
            }
        ],
    }


def _reference(ref_id):
    return {
        "bank": "intensity",
        "metric": "level",
        "reference_id": ref_id,
        "source": "test-only-reference",
        "units": "test-unit",
        "low": 0.0,
        "high": 1.0,
    }


def _profile(view, ref_id):
    return {
        "object": OBJECT,
        "provenance": "native",
        "kind": "reading",
        "support": "surface",
        "view": None if view is None else list(view),
        "readings": [
            {
                "bank": "intensity",
                "metric": "level",
                "value": "values",
                "available": "valid",
            }
        ],
        "references": [_reference(ref_id)],
    }


def _prepare(base, profiles):
    result = prepare_composition(base, profiles, _declaration())
    assert result.code is CompositionCode.OK
    assert result.prepared is not None
    return result.prepared


def _map_record():
    return {
        "schema": "study_map/v1",
        "knee": "R",
        "objects": {
            OBJECT: {
                "status": "complete",
                "point_lps": [0.0, 0.0, 0.0],
                "precision_mm": [0.1, 0.1, 0.1],
                "key_planes": {},
            }
        },
    }


def _addressed(
    base, view, ref_id, values, available, *, uid="series-1", artifact="record-1.npz.xz"
):
    reference = NumericReference(
        base.fingerprint,
        "intensity",
        "level",
        ref_id,
        "test-only-reference",
        "test-unit",
        0.0,
        1.0,
    )
    encoded = encode_places(
        base,
        {
            ("intensity", "level"): PlaceReading(
                "intensity",
                "level",
                np.array(values, dtype=np.float64),
                np.array(available, dtype=np.bool_),
            )
        },
        {("intensity", "level"): reference},
    )
    assert encoded.bundle is not None
    observation = {
        "object": OBJECT,
        "provenance": "native",
        "kind": "reading",
        "support": "surface",
        "view": list(view),
        "series_uid": uid,
        "slices": [4],
        "artifact": artifact,
    }
    refs = {
        "values": {
            "artifact": artifact,
            "digest": "value-digest",
            "shape": [3],
            "dtype": "<f8",
        },
        "valid": {
            "artifact": artifact,
            "digest": "valid-digest",
            "shape": [3],
            "dtype": "|b1",
        },
    }
    return AddressedEncoding(
        "encoded",
        encoded,
        np.array([[0, 0], [1, 1], [2, 2]], dtype=np.int32),
        {
            "observation": observation,
            "bindings": [
                {
                    "bank": "intensity",
                    "metric": "level",
                    "source": "array",
                    "value": "values",
                    "available": "valid",
                }
            ],
            "source_refs": refs,
            "plane_frame": {
                "origin_lps": [0.0, 0.0, 0.0],
                "basis_lps": [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]],
            },
        },
    )


def _row(prepared, view, direction, offset):
    """(expanded bank, absolute row) for digit offset 0=-1, 1=0, 2=+1."""
    bank = prepared.facets_by_key[("intensity", view, direction)]
    return bank, prepared.metric_rows[(bank, "level", "signal")].start + offset


def test_repeated_events_count_once_across_views_and_recompose_exactly():
    base = _base()
    p_s, p_c = _profile(VIEW_S, "ref-s"), _profile(VIEW_C, "ref-c")
    prepared = _prepare(base, [p_s, p_c])

    values, available = [-0.5, 0.7, 1.5], [True, True, False]
    first = _addressed(base, VIEW_S, "ref-s", values, available)
    composer = StudyComposer(prepared, _map_record())
    results = [
        composer.add(OBJECT, 0, 0, first, p_s),
        # An independently built equal copy: same source/place/facet/metric events.
        composer.add(
            OBJECT, 0, 1, _addressed(base, VIEW_S, "ref-s", values, available), p_s
        ),
        composer.add(
            OBJECT,
            1,
            2,
            _addressed(
                base, VIEW_C, "ref-c", values, available, artifact="record-2.npz.xz"
            ),
            p_c,
        ),
        # A target-only observation supplies no measurement and no vote.
        composer.add(
            OBJECT,
            0,
            3,
            AddressedEncoding("target_only", None, None, first.metadata),
            p_s,
        ),
    ]
    assert [r.code for r in results[:3]] == [CompositionCode.OK] * 3
    assert all(len(r.batches) == 3 for r in results[:3])  # overview + two directions
    assert results[3].code is CompositionCode.TARGET_ONLY
    assert not results[3].batches

    study = composer.finalize()
    composition = study.objects[OBJECT]
    assembly = composition.assembly
    assert assembly is not None
    assert assembly.conflicts == ()
    assert ProfileCode.CONFLICTING not in assembly.outcomes

    # Each view counts its two measured places once; copies add no vote.
    expected = {}
    for view in (VIEW_S, VIEW_C):
        for direction, offset in ((None, 0), (None, 1), (CENTRE, 0), (UP_RIGHT, 1)):
            expected[_row(prepared, view, direction, offset)] = 1
    assert {(b, r): c for b, r, c in assembly.profile.entries} == expected
    assert sum(c for _, _, c in assembly.profile.entries) == 8

    arrays, metadata = serialize_study_composition(study, prepared)
    joint = metadata["objects"][OBJECT]
    published = {(b, r): c for b, r, c in joint["sparse_counts"]}
    assert published == expected

    # Links are retained: three batches per observation, including the duplicate.
    records = joint["assembly"]["batches"]
    assert Counter(item["source_link"]["observation"] for item in records) == {
        "p0/o0": 3,
        "p0/o1": 3,
        "p1/o2": 3,
    }
    assert sum(item["counted"] for item in records) == 8
    assert sum(item["duplicate"] for item in records) == 4
    assert sum(item["conflict"] for item in records) == 0
    for item in records:
        if item["source_link"]["observation"] == "p0/o1":
            assert item["counted"] == 0

    # Original place links of the first observation.
    maps = [
        m
        for m in joint["batch_index_maps"]
        if m["source_link"]["observation"] == "p0/o0"
    ]
    maps.sort(key=lambda m: m["object_batch_ordinal"])
    assert [m["direction"] for m in maps] == [None, list(CENTRE), list(UP_RIGHT)]
    assert [arrays[m["original_place_indices"]["key"]].tolist() for m in maps] == [
        [0, 1, 2],
        [0],
        [1, 2],
    ]

    # Exact recomposition from the published row codes and place statuses.
    recomposed = Counter()
    for item in records:
        status = arrays[item["row_status"]["key"]]
        rowcodes = arrays[item["batch_payload"]["rowcodes"]["key"]]
        for code in rowcodes[status == PLACE_COUNTED].tolist():
            recomposed[(item["bank"], code)] += 1
    assert dict(recomposed) == published

    # The exact bundle, carrier round trip and named decode agree.
    bank_index = {bank.name: i for i, bank in enumerate(prepared.layout.banks)}
    table = np.zeros((len(prepared.layout.banks), 512), dtype=np.int64)
    for (bank, row), count in expected.items():
        table[bank_index[bank], row] = count
    bundle = assembly.to_count_bundle()
    assert bundle is not None
    assert bundle.counts == tuple(tuple(int(x) for x in row) for row in table)
    assert prepared.layout.carrier_id == prepared.carrier.identity
    np.testing.assert_array_equal(
        prepared.carrier.decode(prepared.carrier.encode(table)), table
    )
    names = assembly.decoded_names()
    assert names is not None
    assert {(b, m, r, c) for b, _, m, r, c in names if c} == {
        (
            bank,
            "level",
            ("-1", "0", "+1")[
                row - prepared.metric_rows[(bank, "level", "signal")].start
            ],
            1,
        )
        for (bank, row) in expected
    }


def test_conflicting_codes_are_named_while_unread_is_neither_conflict_nor_zero():
    base = _base()
    p_s, p_c = _profile(VIEW_S, "ref-s"), _profile(VIEW_C, "ref-c")
    prepared = _prepare(base, [p_s, p_c])
    composer = StudyComposer(prepared, _map_record())
    available = [True, True, False]
    # Place 1 is observed "at" in one record and "above" in a record of the same
    # source/place/facet/metric.  Place 0 agrees.  Place 2 is unread everywhere.
    adds = [
        _addressed(base, VIEW_S, "ref-s", [-0.5, 0.7, 1.5], available),
        _addressed(base, VIEW_S, "ref-s", [-0.5, 1.5, 1.5], available),
        # Wholly unread record on the same source: no row, no conflict.
        _addressed(base, VIEW_S, "ref-s", [0.0, 0.0, 0.0], [False, False, False]),
    ]
    for outcome, addressed in enumerate(adds):
        assert (
            composer.add(OBJECT, 0, outcome, addressed, p_s).code is CompositionCode.OK
        )

    study = composer.finalize()
    composition = study.objects[OBJECT]
    assembly = composition.assembly
    assert assembly is not None
    assert assembly.code is ProfileCode.CONFLICTING

    # Only the agreeing place counts; the conflicted event and unread place write nothing.
    expected = {
        _row(prepared, VIEW_S, None, 0): 1,
        _row(prepared, VIEW_S, CENTRE, 0): 1,
    }
    assert {(b, r): c for b, r, c in assembly.profile.entries} == expected

    # Batch ordinals: add0 -> 0,1,2; add1 -> 3,4,5; unread add2 -> overview only, 6.
    status = [record.row_status.tolist() for record in assembly.batches]
    assert len(status) == 7
    assert status[0] == [PLACE_COUNTED, PLACE_CONFLICT, PLACE_NO_MEASUREMENT]
    assert status[3] == [PLACE_DUPLICATE, PLACE_CONFLICT, PLACE_NO_MEASUREMENT]
    assert status[6] == [PLACE_NO_MEASUREMENT] * 3
    assert status[1] == [PLACE_COUNTED] and status[4] == [PLACE_DUPLICATE]
    assert status[2] == [PLACE_CONFLICT, PLACE_NO_MEASUREMENT]
    assert status[5] == [PLACE_CONFLICT, PLACE_NO_MEASUREMENT]

    overview_bank, overview_at = _row(prepared, VIEW_S, None, 1)
    _, overview_above = _row(prepared, VIEW_S, None, 2)
    by_bank = {c.bank: c for c in assembly.conflicts}
    assert len(assembly.conflicts) == 2
    overview = by_bank[overview_bank]
    assert overview.event_count == 1
    assert overview.link_batch.tolist() == [0, 3]
    assert overview.link_place.tolist() == [1, 1]
    assert overview.link_rowcode.tolist() == [overview_at, overview_above]
    directional_bank, directional_at = _row(prepared, VIEW_S, UP_RIGHT, 1)
    _, directional_above = _row(prepared, VIEW_S, UP_RIGHT, 2)
    directional = by_bank[directional_bank]
    assert directional.event_count == 1
    assert directional.link_batch.tolist() == [2, 5]
    assert directional.link_place.tolist() == [0, 0]
    assert directional.link_rowcode.tolist() == [directional_at, directional_above]
    # The directional local place 0 is original place 1, the same event as the overview's.
    assert composition.batch_index_maps[2].original_place_indices[0] == 1

    arrays, metadata = serialize_study_composition(study, prepared)
    joint = metadata["objects"][OBJECT]
    assert joint["status"] == "conflicting"
    assert {(b, r): c for b, r, c in joint["sparse_counts"]} == expected
    published = {c["bank"]: c for c in joint["assembly"]["conflicts"]}
    assert set(published) == {overview_bank, directional_bank}
    assert arrays[published[overview_bank]["link_batch"]["key"]].tolist() == [0, 3]
    assert arrays[published[overview_bank]["link_place"]["key"]].tolist() == [1, 1]
    assert arrays[published[directional_bank]["link_batch"]["key"]].tolist() == [2, 5]


def test_reference_identity_ignores_duplicate_plans_keeps_view_scopes_and_uid_free_layout():
    base = _base()
    p_s, p_c = _profile(VIEW_S, "ref-s"), _profile(VIEW_C, "ref-c")
    plain = _prepare(base, [p_s, p_c])

    # Duplicate observation plans (also one with no reference) change no identity.
    duplicate = {**p_s, "provenance": "projected", "support": "coarse"}
    missing = {**duplicate, "references": []}
    repeated = _prepare(base, [p_s, p_c, duplicate, missing])
    assert repeated.object_codes[OBJECT] is CompositionCode.OK
    assert (
        repeated.object_reference_identities[OBJECT]
        == plain.object_reference_identities[OBJECT]
    )
    assert repeated.layout.fingerprint == plain.layout.fingerprint
    assert repeated.carrier.identity == plain.carrier.identity
    assert repeated.registry == plain.registry
    assert (
        repeated.profile_layouts[OBJECT].count_layout
        == plain.profile_layouts[OBJECT].count_layout
    )

    # A reference that applies to every view has the same meaning as the same
    # reference qualified to each declared view; per-view qualifications differ.
    wildcard = _prepare(base, [_profile(None, "ref-s")])
    explicit = _prepare(base, [_profile(VIEW_S, "ref-s"), _profile(VIEW_C, "ref-s")])
    assert (
        wildcard.object_reference_identities[OBJECT]
        == explicit.object_reference_identities[OBJECT]
    )
    assert (
        plain.object_reference_identities[OBJECT]
        != explicit.object_reference_identities[OBJECT]
    )

    # A wildcard cannot hide a contradiction with a view-qualified reference.
    contradiction = _prepare(base, [_profile(None, "ref-s"), p_c])
    assert (
        contradiction.object_codes[OBJECT] is CompositionCode.REFERENCE_MAPPING_CONFLICT
    )

    # A missing reference supplies no competing meaning and borrows none.
    only_s = _prepare(base, [p_s])
    coronal_missing = _prepare(base, [p_s, {**p_c, "references": []}])
    assert coronal_missing.object_codes[OBJECT] is CompositionCode.OK
    assert (
        coronal_missing.object_reference_identities[OBJECT]
        == only_s.object_reference_identities[OBJECT]
    )
    assert (
        coronal_missing.object_reference_identities[OBJECT]
        != explicit.object_reference_identities[OBJECT]
    )

    # Static vocabulary and layout do not depend on the patient's series UID.
    def publish(uid):
        composer = StudyComposer(plain, _map_record())
        added = composer.add(
            OBJECT,
            0,
            0,
            _addressed(
                base, VIEW_S, "ref-s", [-0.5, 0.7, 1.5], [True, True, False], uid=uid
            ),
            p_s,
        )
        assert added.code is CompositionCode.OK
        return serialize_study_composition(composer.finalize(), plain)[1]

    first, second = publish("series-A"), publish("series-B")
    assert first["layout"] == second["layout"]
    assert first["registry"] == second["registry"]
    assert first["layout_fingerprint"] == second["layout_fingerprint"]
    assert (
        first["objects"][OBJECT]["sparse_counts"]
        == second["objects"][OBJECT]["sparse_counts"]
    )
    static_text = repr(first["layout"]) + repr(first["registry"])
    assert "series-A" not in static_text and "series-B" not in static_text
