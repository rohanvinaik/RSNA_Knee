"""Intent: cheap region evidence survives missing masks, references and object identity.

All numeric reference bounds here are mechanical fixtures, never MRI healthy values.
"""

import json
from dataclasses import replace

import numpy as np
import pytest

from knee.diagnosis.cheap import (
    build_cheap_profile,
    pair_descriptions,
    source_disposition,
)
from knee.encoding.carrier import HadamardCarrier
from knee.encoding.coarse_adapter import CoarseBlockLayout
from knee.encoding.handoff import encode_observation
from knee.encoding.mri_coarse_spec import make_mri_coarse_spec
from knee.encoding.operation import validate_spec
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    NumericReference,
    compile_layout,
    decode_count_names,
)
from knee.receipt import digest


def test_source_disposition_accepts_only_declared_cheap_native_region_reading():
    assert (
        source_disposition("native", "reading", "region:joint", "cheap/raw-v1")
        == "eligible"
    )


def test_short_explicit_names_are_valid_and_a_long_full_mode_is_refused():
    assert source_disposition("native", "reading", "region:x", "cheap/x") == "eligible"
    assert (
        source_disposition("native", "reading", "region:x", "full/acquired")
        == "explicit_cheap_mode_required"
    )


@pytest.mark.parametrize(
    "args,expected",
    [
        (
            ("projected", "target", "region:joint", "cheap/raw-v1"),
            "native_reading_required",
        ),
        (
            ("laid", "reading", "region:joint", "cheap/raw-v1"),
            "native_reading_required",
        ),
        (
            ("native", "resolved", "region:joint", "cheap/raw-v1"),
            "region_reading_required",
        ),
        (
            ("native", "reading", "object:joint", "cheap/raw-v1"),
            "explicit_region_scope_required",
        ),
        (
            ("native", "reading", "region: ", "cheap/raw-v1"),
            "explicit_region_scope_required",
        ),
        (("native", "reading", "region:joint", "full"), "explicit_cheap_mode_required"),
        (
            ("native", "reading", "region:joint", "cheap/ "),
            "explicit_cheap_mode_required",
        ),
    ],
)
def test_source_disposition_refuses_false_source_claims(args, expected):
    assert source_disposition(*args) == expected


def native_input():
    carrier = HadamardCarrier(("raw", "context"))
    spec = compile_layout(
        LayoutSpec(
            "cheap-fixture-v1",
            carrier.identity,
            (
                BankSpec(
                    "raw", "acquired signal", (MetricSpec("signal", MetricKind.DIGIT),)
                ),
                BankSpec(
                    "context",
                    "caller-observed context",
                    (MetricSpec("view", MetricKind.WORDS, ("Sagittal", "Axial")),),
                ),
            ),
        )
    )
    assert spec is not None
    arrays = {
        # An inspected search region, explicitly not an accepted object mask.
        "inspected_region": np.array([[True, True], [False, True]]),
        "acquired": np.array([[1, 2], [40, 3]], np.uint16),
        "observed": np.array([[True, True], [False, False]]),
    }
    record = {
        "artifact": "study/series-input.npz",
        "series_uid": "series",
        "slice_index": 7,
        "view": ["Sagittal", "1", "1"],
        "arrays": {key: {"digest": digest(value)} for key, value in arrays.items()},
    }
    observation = {
        "artifact": record["artifact"],
        "series_uid": "series",
        "view": record["view"],
        "slices": [7],
        "support": "inspected_region",
        "provenance": "native",
        "kind": "reading",
        "count": 3,
        "code": "object_unresolved",
        "object": "unassigned",
    }
    geometry = {"origin_lps": [0, 1, 2], "basis_lps": [[1, 0], [0, 1], [0, 0]]}
    return {
        "subject": "joint_region",
        "source_id": "study/series/slice7/region",
        "scope": "region:joint-search",
        "mode": "cheap/acquired-v1",
        "producer": "acquired-v1",
        "dependencies": ("decode", "caller_region"),
        "record": record,
        "observation": observation,
        "arrays": arrays,
        "spec": spec,
        "bindings": [
            {
                "bank": "raw",
                "metric": "signal",
                "value": "acquired",
                "available": "observed",
            },
            {
                "bank": "context",
                "metric": "view",
                "source": "record_context",
                "path": ["view", 0],
                "scope": "acquisition",
            },
        ],
        "references": {},
        "geometry": geometry,
        "context": (("view", "Sagittal/1/1"),),
    }


def with_reference(kwargs):
    return {
        **kwargs,
        "references": {
            ("raw", "signal"): NumericReference(
                kwargs["spec"].fingerprint,
                "raw",
                "signal",
                "fixture-r",
                "test only",
                "fixture units",
                2,
                2,
            )
        },
    }


def test_real_encoder_missing_reference_keeps_raw_unresolved_region_and_sources():
    kwargs = native_input()
    result = build_cheap_profile(**kwargs)
    assert result.status == "missing_reference"
    assert result.profile is not None and result.encoding is not None
    assert result.profile.scope == "region:joint-search"
    assert result.metadata["observation"]["code"] == "object_unresolved"
    assert result.metadata["api"].endswith("build_cheap_profile/v1")
    assert result.coordinates.tolist() == [[0, 0], [0, 1], [1, 1]]
    raw = result.encoding.metrics[0]
    assert raw.status.value == "missing_reference"
    assert raw.source_values.tolist() == [1, 2, 3]
    assert raw.source_available.tolist() == [True, True, False]
    assert raw.row_codes.tolist() == [-1, -1, -1]
    assert not any(result.profile.bundle.counts[0])
    assert sum(result.profile.bundle.counts[1]) == 3
    assert ("raw", "signal=missing_reference") in result.profile.bank_statuses
    assert "acquired" in json.loads(dict(result.profile.provenance)["source_refs"])
    kwargs["arrays"]["acquired"][:] = 999
    assert raw.source_values.tolist() == [1, 2, 3]
    assert not raw.source_values.flags.writeable
    assert not result.coordinates.flags.writeable


def test_explicit_reference_uses_exact_encoder_rows_and_never_writes_unobserved_zero():
    kwargs = with_reference(native_input())
    result = build_cheap_profile(**kwargs)
    direct = encode_observation(
        kwargs["record"],
        {**kwargs["observation"], "address_frame": kwargs["geometry"]},
        kwargs["arrays"],
        kwargs["spec"],
        kwargs["bindings"],
        kwargs["references"],
    )
    assert result.status == "ok"
    assert result.profile.bundle == direct.encoding.bundle
    assert result.encoding.metrics[0].row_codes.tolist() == [0, 1, -1]
    assert result.profile.bundle.counts[0][:3] == (1, 1, 0)
    decoded = decode_count_names(
        kwargs["spec"], result.profile.bundle, result.encoding.reference_set_fingerprint
    )
    assert decoded[:3] == (
        ("raw", "acquired signal", "signal", "-1", 1),
        ("raw", "acquired signal", "signal", "0", 1),
        ("raw", "acquired signal", "signal", "+1", 0),
    )


def test_unread_banks_and_empty_inspection_are_silence_not_negative():
    kwargs = native_input()
    kwargs["bindings"] = [
        {
            "bank": "raw",
            "metric": "signal",
            "source": "unread",
            "reason": "not measured at this stage",
        },
        {
            "bank": "context",
            "metric": "view",
            "source": "unread",
            "reason": "not acquired",
        },
    ]
    result = build_cheap_profile(**kwargs)
    assert result.status == "silent"
    assert all(not any(counts) for counts in result.profile.bundle.counts)
    assert len(result.metadata["unread_sources"]) == 2
    assert all(not m.source_available.any() for m in result.encoding.metrics)
    kwargs = native_input()
    kwargs["arrays"]["inspected_region"][:] = False
    kwargs["record"]["arrays"]["inspected_region"]["digest"] = digest(
        kwargs["arrays"]["inspected_region"]
    )
    kwargs["observation"]["count"] = 0
    result = build_cheap_profile(**kwargs)
    assert result.status == "silent"
    assert result.coordinates.shape == (0, 2)
    assert not any(result.profile.bundle.counts[0])


@pytest.mark.parametrize(
    "change,expected",
    [
        ({"geometry": None}, "explicit_geometry_required"),
        ({"geometry": {}}, "invalid_observation_address_frame"),
        ({"subject": ""}, "invalid_identity"),
        ({"dependencies": ("decode", "decode")}, "invalid_dependencies"),
        ({"context": (("view", "x"), ("view", "y"))}, "invalid_context"),
        ({"spec": None}, "invalid_encoding_inputs"),
        ({"bindings": [None]}, "invalid_encoding_inputs"),
        ({"record": None}, "invalid_source"),
    ],
)
def test_malformed_boundary_is_named(change, expected):
    result = build_cheap_profile(**{**native_input(), **change})
    assert result.status == expected
    assert result.profile is None


def test_digest_mismatch_unknown_word_and_mismatched_reference_do_not_make_profiles():
    kwargs = native_input()
    kwargs["arrays"]["acquired"][0, 0] = 9
    result = build_cheap_profile(**kwargs)
    assert result.status == "digest_mismatch" and result.profile is None
    kwargs = native_input()
    kwargs["record"]["view"][0] = "unknown-view"
    result = build_cheap_profile(**kwargs)
    assert result.status == "invalid_input" and result.profile is None
    kwargs = with_reference(native_input())
    kwargs["references"][("raw", "signal")] = replace(
        kwargs["references"][("raw", "signal")], layout_fingerprint="other"
    )
    result = build_cheap_profile(**kwargs)
    assert result.status == "identity_mismatch" and result.profile is None
    assert result.encoding.metrics[0].source_values.tolist() == [1, 2, 3]


@pytest.mark.parametrize(
    "field,value",
    [
        ("provenance", ["native"]),
        ("series_uid", ""),
        ("artifact", None),
        ("note", object()),
    ],
)
def test_malformed_observation_values_are_named(field, value):
    kwargs = native_input()
    kwargs["observation"][field] = value
    result = build_cheap_profile(**kwargs)
    assert result.status in ("invalid_source_identity", "invalid_source")
    assert result.profile is None


def test_available_region_survives_object_refusal_without_touching_full_mask():
    kwargs = native_input()
    kwargs["observation"]["code"] = "none"
    result = build_cheap_profile(**kwargs)
    assert result.status == "missing_reference"
    assert result.encoding.metrics[0].source_values.tolist() == [1, 2, 3]
    assert result.profile is not None
    assert not any(name.startswith("a1_") for name in result.metadata["source_refs"])


@pytest.mark.parametrize(
    "provenance,kind,mode,expected",
    [
        ("projected", "target", "cheap/acquired-v1", "native_reading_required"),
        ("laid", "reading", "cheap/acquired-v1", "native_reading_required"),
        ("native", "resolved", "cheap/acquired-v1", "region_reading_required"),
        ("native", "reading", "full/acquired", "explicit_cheap_mode_required"),
    ],
)
def test_public_entry_consumes_source_disposition(provenance, kind, mode, expected):
    kwargs = native_input()
    kwargs["observation"].update(provenance=provenance, kind=kind)
    kwargs["mode"] = mode
    result = build_cheap_profile(**kwargs)
    assert result.status == expected
    assert result.profile is None and result.encoding is None


def test_nonfinite_measured_signal_remains_raw_and_silent_at_that_place():
    kwargs = with_reference(native_input())
    kwargs["arrays"]["acquired"] = np.array([[1, np.nan], [40, np.inf]])
    kwargs["arrays"]["observed"][:] = True
    kwargs["record"]["arrays"] = {
        key: {"digest": digest(value)} for key, value in kwargs["arrays"].items()
    }
    result = build_cheap_profile(**kwargs)
    assert result.status == "ok"
    assert result.encoding.metrics[0].nonfinite_available_count == 2
    assert result.encoding.metrics[0].row_codes.tolist() == [0, -1, -1]
    assert np.isnan(result.encoding.metrics[0].source_values[1])


def coarse_input():
    kwargs = native_input()
    arrays = {
        "offsets": np.array([0, 4], np.int64),
        "shapes": np.array([[2, 2]], np.int32),
        "slices": np.array([7], np.int32),
        "windows": np.array([[2, 5, 4, 7]], np.int32),
        "block_px": np.array([[2, 2]], np.int32),
        "block_mm": np.array([[1.0, 1.0]], np.float64),
        "inspected_region": np.array([True, True, False, True]),
        "median": np.array([1.0, 2.0, 90.0, 3.0]),
    }
    kwargs["arrays"] = arrays
    kwargs["record"]["arrays"] = {
        key: {"digest": digest(value)} for key, value in arrays.items()
    }
    kwargs["observation"]["row"] = 0
    kwargs["geometry"] = CoarseBlockLayout(
        "offsets",
        "shapes",
        "slices",
        "windows",
        "block_px",
        "block_mm",
        ("inspected_region", "median"),
        count_meaning="coarse_blocks",
    )
    kwargs["bindings"] = [
        {
            "bank": "raw",
            "metric": "signal",
            "value": "median",
            "availability_policy": "finite_values",
        },
        {
            "bank": "context",
            "metric": "view",
            "source": "unread",
            "reason": "coarse context not bound",
        },
    ]
    return kwargs


def test_coarse_real_encoder_preserves_block_bounds_and_missing_reference_without_object_mask():
    kwargs = coarse_input()
    result = build_cheap_profile(**kwargs)
    assert result.status == "missing_reference"
    assert result.address_kind == "coarse_grid_rc"
    assert result.coordinates.tolist() == [[0, 0], [0, 1], [1, 1]]
    assert result.metadata["native_bounds_rc"].tolist() == [
        [2, 4, 4, 6],
        [2, 4, 6, 7],
        [4, 5, 6, 7],
    ]
    assert result.metadata["scope_address"]["window_rc"] == [2, 5, 4, 7]
    assert result.encoding.metrics[0].source_values.tolist() == [1.0, 2.0, 3.0]
    result = build_cheap_profile(**with_reference(kwargs))
    assert result.status == "ok"
    assert result.profile.bundle.counts[0][:3] == (1, 1, 1)


def test_installed_mri_coarse_declaration_writes_real_membership_and_retains_numeric_silence():
    declaration = make_mri_coarse_spec()
    prepared = validate_spec(declaration)
    declared_profile = next(
        profile
        for profile in declaration["profiles"]
        if profile["support"] == "a4_axial_coarse_femur_body"
    )
    kwargs = coarse_input()
    renames = {
        "offsets": "a4_axial_coarse_offsets",
        "shapes": "a4_axial_coarse_shapes",
        "slices": "a4_axial_coarse_slices",
        "windows": "a4_axial_coarse_windows_rc",
        "block_px": "a4_axial_coarse_block_px",
        "block_mm": "a4_axial_coarse_block_mm",
        "median": "a4_axial_coarse_median",
        "inspected_region": "a4_axial_coarse_femur_body",
    }
    arrays = {renames[name]: value for name, value in kwargs["arrays"].items()}
    arrays["a4_axial_coarse_depth"] = np.array([0.0, 1.0, 2.0, 3.0])
    arrays["a4_axial_coarse_femur_seeds"] = np.array([False, True, False, False])
    kwargs["arrays"] = arrays
    kwargs["record"]["arrays"] = {
        name: {"digest": digest(value)} for name, value in arrays.items()
    }
    kwargs["observation"]["support"] = declared_profile["support"]
    layout = declared_profile["support_layout"]
    kwargs["geometry"] = CoarseBlockLayout(
        layout["offsets"],
        layout["shapes"],
        layout["slices"],
        layout["windows_rc"],
        layout["block_px"],
        layout["block_mm"],
        tuple(layout["packed_arrays"]),
        count_meaning=layout["count_meaning"],
    )
    kwargs["spec"] = prepared["layout"]
    kwargs["bindings"] = declared_profile["readings"]
    result = build_cheap_profile(**kwargs)
    assert result.status == "missing_reference"
    assert result.profile is not None
    membership = next(
        m
        for m in result.encoding.metrics
        if (m.bank, m.metric) == ("coarse_unfiltered", "membership")
    )
    median = next(
        m
        for m in result.encoding.metrics
        if (m.bank, m.metric) == ("coarse_unfiltered", "median")
    )
    assert membership.row_codes.tolist() == [1, 1, 1]
    assert membership.status.value == "ok"
    assert median.status.value == "missing_reference"
    assert median.source_values.tolist() == [1.0, 2.0, 3.0]
    decoded = decode_count_names(
        prepared["layout"],
        result.profile.bundle,
        result.encoding.reference_set_fingerprint,
    )
    assert (
        "coarse_unfiltered",
        "unfiltered coarse-grid body or seed membership and readings",
        "membership",
        "True",
        3,
    ) in decoded
    assert all(
        not any(row)
        for bank, row in zip(
            result.profile.bundle.layout.banks,
            result.profile.bundle.counts,
            strict=True,
        )
        if bank.name != "coarse_unfiltered"
    )


def test_pairing_records_sources_and_silences_without_incompatible_comparison():
    cheap = build_cheap_profile(**native_input()).profile
    full = build_cheap_profile(**with_reference(native_input())).profile
    full = replace(
        full, mode="full", scope="object:joint_region", source_id="full-source"
    )
    pair = pair_descriptions(full, cheap)
    assert pair["full"]["source_id"] == "full-source"
    assert pair["cheap"]["scope"] == "region:joint-search"
    assert pair["common_speaking_banks"] == ["context"]
    assert pair["differing_availability_banks"] == ["raw"]
    assert pair["cheap_silent_banks"] == ["raw"]
    assert pair["comparison_performed"] is False
    assert "similarity" not in pair
    json.dumps(pair)
    with pytest.raises(ValueError, match="pair_subject_mismatch"):
        pair_descriptions(replace(full, subject="other"), cheap)
