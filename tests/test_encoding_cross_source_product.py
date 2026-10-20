"""Cross-source encoding and public H5 product reconstruction.

Synthetic producer-shaped fixtures only: one native 2-D support, one posterior
trace support and one fibula-axial packed support, all declared against a single
layout with an identical explicit numeric reference for the same digit metric.
These tests certify arithmetic, addressing and wiring only; the reference is a
fixture declaration, not a clinical norm.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from knee.array_archive import write_npz_xz
from knee.collapse.posterior import FOLLOWED, START_NAMES
from knee.encoding import operation
from knee.encoding.carrier import HadamardCarrier
from knee.encoding.counts import (
    BankLayout,
    CountBundle,
    CountCode,
    CountLayout,
    add_counts,
)
from knee.encoding.operation import encode_study, validate_spec
from knee.encoding.places import decode_count_names
from knee.encoding.product import open_product
from knee.receipt import digest

STUDY = "study-cross-1"
OBJECT = "fibula"
FACET = "synthetic digit readings"
ROW_NAMES = ("-1", "0", "+1")

NATIVE_VIEW = ["coronal", "fluid", "fat-suppressed"]
TRACE_VIEW = ["axial", "fluid", "fat-suppressed"]
PACKED_VIEW = ["Axial", "1", "1"]

NATIVE_ARTIFACT = f"{STUDY}/native-series.npz.xz"
TRACE_OWNER_ARTIFACT = f"{STUDY}/trace-owner.npz.xz"
TRACE_TARGET_ARTIFACT = f"{STUDY}/trace-target.npz.xz"
PACKED_ARTIFACT = f"{STUDY}/fibula-owner-fibula.npz.xz"

TRACE_PREFIX = "a3_posterior_trace_fibula"
TRACE_SUPPORT = f"{TRACE_PREFIX}_points_lps"
PACKED = "a3_fibula_axial_"

TRACE_LAYOUT = {
    "family": "posterior_trace",
    "identity_sources": {
        "owner_artifact": "observation.artifact",
        "target_series_uid": "target_record.series_uid",
        "target_view": "target_record.view",
        "target_slice": "observation.slices[0]",
        "row": "observation.row",
    },
    "offsets_suffix": "_offsets",
    "slices_suffix": "_slices",
    "starts_suffix": "_starts",
    "stops_suffix": "_stops",
    "coordinates": "patient_lps",
    "availability": "finite_values",
}

# Independent hand-derived expectations (digit rows: 0 -> "-1", 1 -> "0", 2 -> "+1").
EXPECTED_LIGHT_CODES = {
    "native": [1, 0, 2, -1],  # measured zero, below, above, unavailable
    "trace": [1, 0, 2, 1],  # measured zero, below, above, measured 0.5 (middle)
    "packed": [1, 2, 0, -1],  # measured zero, above, below, unavailable
}
EXPECTED_PROFILE_LIGHT_COUNTS = {
    "native": (1, 1, 1),
    "trace": (1, 2, 1),
    "packed": (1, 1, 1),
}
EXPECTED_COMBINED_LIGHT_COUNTS = (3, 4, 3)


def _reference() -> dict:
    return {
        "bank": "signal",
        "metric": "light",
        "reference_id": "shared-explicit-fixture-reference",
        "source": "synthetic fixture declaration",
        "units": "fixture units",
        "low": -1.0,
        "high": 1.0,
    }


def _unread(metric: str) -> dict:
    return {
        "bank": "signal",
        "metric": metric,
        "source": "unread",
        "reason": "second digit metric is not measured by this source",
    }


def _native_profile() -> dict:
    return {
        "object": OBJECT,
        "provenance": "native",
        "kind": "resolved",
        "support": "native_mask",
        "view": list(NATIVE_VIEW),
        "readings": [
            {
                "bank": "signal",
                "metric": "light",
                "value": "native_light",
                "available": "native_avail",
            },
            _unread("aux"),
        ],
        "references": [_reference()],
    }


def _trace_profile() -> dict:
    return {
        "object": OBJECT,
        "provenance": "native",
        "kind": "reading",
        "support": TRACE_SUPPORT,
        "view": list(TRACE_VIEW),
        "support_layout": deepcopy(TRACE_LAYOUT),
        "readings": [
            {"bank": "signal", "metric": "light", "value": "light"},
            _unread("aux"),
        ],
        "references": [_reference()],
    }


def _packed_profile() -> dict:
    return {
        "object": OBJECT,
        "provenance": "native",
        "kind": "reading",
        "support": f"{PACKED}region",
        "view": list(PACKED_VIEW),
        "support_layout": {
            "family": "fibula_axial",
            "identity_sources": {
                "owner_series_uid": "record.series_uid",
                "artifact": "record.artifact",
                "target_series_uid": "axial_evidence.series_uid",
                "target_view": "axial_evidence.view",
                "target_slice": "axial_evidence.slice",
                "row": "observation.row_to_axial_evidence.row",
            },
            "offsets": f"{PACKED}offsets",
            "shapes": f"{PACKED}shapes",
            "slices": f"{PACKED}slices",
            "packed_arrays": [
                f"{PACKED}region",
                f"{PACKED}target",
                f"{PACKED}available",
                f"{PACKED}values",
            ],
            "target_pixels_array": f"{PACKED}target",
            "frame_arrays": {
                "origin_lps": f"{PACKED}origin_lps",
                "basis_lps": f"{PACKED}basis_lps",
                "normal_lps": f"{PACKED}normal_lps",
                "thickness_mm": f"{PACKED}thickness_mm",
            },
            "count_meaning": "fibula_axial_target_pixels",
        },
        "readings": [
            {
                "bank": "signal",
                "metric": "light",
                "value": f"{PACKED}values",
                "available": f"{PACKED}available",
            },
            _unread("aux"),
        ],
        "references": [_reference()],
    }


def _spec(profiles: list[dict], storage: str | None = None) -> dict:
    spec = {
        "version": "cross-source-v1",
        "banks": [
            {
                "name": "signal",
                "facet": FACET,
                "metrics": [
                    {"name": "light", "kind": "digit"},
                    {"name": "aux", "kind": "digit"},
                ],
            }
        ],
        "profiles": profiles,
    }
    if storage is not None:
        spec["storage"] = storage
    return spec


def _write_artifact(run_dir: Path, artifact: str, arrays: dict) -> dict:
    path = run_dir / artifact
    path.parent.mkdir(parents=True, exist_ok=True)
    write_npz_xz(path, arrays.items())
    return {name: {"digest": digest(array)} for name, array in arrays.items()}


def _build_study(tmp_path: Path):
    run_dir = tmp_path / "run"
    main_run = tmp_path / "main"
    run_dir.mkdir(parents=True, exist_ok=True)
    main_run.mkdir(parents=True, exist_ok=True)

    # --- native 2-D labelled support, places (0,0) (0,2) (1,0) (1,1) ---
    native_arrays = {
        "native_mask": np.asarray([[1, 0, 1], [1, 1, 0]], dtype=np.uint8),
        "native_light": np.asarray(
            [[0.0, 9.0, -5.0], [5.0, 7.0, 9.0]], dtype=np.float32
        ),
        "native_avail": np.asarray([[True, True, True], [True, False, True]]),
    }
    native_digests = _write_artifact(run_dir, NATIVE_ARTIFACT, native_arrays)
    native_record = {
        "study_uid": STUDY,
        "series_uid": "native-series",
        "view": list(NATIVE_VIEW),
        "slice_index": 0,
        "artifact": NATIVE_ARTIFACT,
        "arrays": native_digests,
        "observations": [
            {
                "object": OBJECT,
                "provenance": "native",
                "kind": "resolved",
                "series_uid": "native-series",
                "view": list(NATIVE_VIEW),
                "slices": [0],
                "code": "identified",
                "count": 4,
                "support": "native_mask",
                "row": None,
                "label": 1,
                "artifact": NATIVE_ARTIFACT,
            }
        ],
    }

    # --- posterior trace: owner artifact distinct from the target record ---
    trace_arrays = {
        TRACE_SUPPORT: np.asarray(
            [[1.0, 2.0, 3.0], [1.5, 2.5, 3.5], [2.0, 3.0, 4.0], [2.5, 3.5, 4.5]],
            dtype=np.float64,
        ),
        f"{TRACE_PREFIX}_offsets": np.asarray([0, 4], dtype=np.int64),
        f"{TRACE_PREFIX}_slices": np.asarray([2], dtype=np.int32),
        f"{TRACE_PREFIX}_starts": np.asarray([0], dtype=np.int32),
        f"{TRACE_PREFIX}_stops": np.asarray([[0, 1]], dtype=np.int32),
        f"{TRACE_PREFIX}_light": np.asarray([0.0, -3.0, 3.0, 0.5], dtype=np.float32),
    }
    trace_digests = _write_artifact(run_dir, TRACE_OWNER_ARTIFACT, trace_arrays)
    trace_owner_record = {
        "study_uid": STUDY,
        "series_uid": "trace-owner",
        "view": ["sagittal", "owner", "owner"],
        "slice_index": 0,
        "artifact": TRACE_OWNER_ARTIFACT,
        "arrays": trace_digests,
    }
    trace_target_record = {
        "study_uid": STUDY,
        "series_uid": "trace-target",
        "view": list(TRACE_VIEW),
        "slice_index": 2,
        "artifact": TRACE_TARGET_ARTIFACT,
        "observations": [
            {
                "object": OBJECT,
                "provenance": "native",
                "kind": "reading",
                "series_uid": "trace-target",
                "view": list(TRACE_VIEW),
                "slices": [2],
                "code": (
                    "tube_followed" if START_NAMES[0] == FOLLOWED else START_NAMES[0]
                ),
                "count": 4,
                "support": TRACE_SUPPORT,
                "row": 0,
                "label": None,
                "artifact": TRACE_OWNER_ARTIFACT,
            }
        ],
    }

    # --- fibula axial packed family: row 1 (slice 10) is a 2x3 plane ---
    packed_arrays = {
        f"{PACKED}offsets": np.asarray([0, 4, 10], dtype=np.int64),
        f"{PACKED}shapes": np.asarray([[2, 2], [2, 3]], dtype=np.int32),
        f"{PACKED}slices": np.asarray([7, 10], dtype=np.int32),
        f"{PACKED}region": np.asarray(
            [False, False, False, False, True, False, True, True, True, False]
        ),
        f"{PACKED}target": np.asarray(
            [False, False, False, False, True, False, False, False, True, False]
        ),
        f"{PACKED}available": np.asarray(
            [True, True, True, True, True, True, True, True, False, True]
        ),
        f"{PACKED}values": np.asarray(
            [9.0, 9.0, 9.0, 9.0, 0.0, 9.0, 3.0, -4.0, 9.0, 9.0], dtype=np.float64
        ),
        f"{PACKED}origin_lps": np.asarray([[0.0, 0.0, 0.0], [1.0, 2.0, 3.0]]),
        f"{PACKED}basis_lps": np.stack([np.eye(3)[:, :2], np.eye(3)[:, :2]]),
        f"{PACKED}normal_lps": np.asarray([[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]]),
        f"{PACKED}thickness_mm": np.asarray([2.0, 2.5]),
    }
    packed_digests = _write_artifact(run_dir, PACKED_ARTIFACT, packed_arrays)
    packed_record = {
        "study_uid": STUDY,
        "artifact": PACKED_ARTIFACT,
        "series_uid": "fibula-owner",
        "arrays": packed_digests,
        "axial_evidence": [
            {
                "series_uid": "axial-target",
                "view": list(PACKED_VIEW),
                "slice": 7,
                "row": None,
                "code": "no_labels",
                "target_pixels": 0,
                "region_pixels": 0,
            },
            {
                "series_uid": "axial-target",
                "view": list(PACKED_VIEW),
                "slice": 10,
                "row": 1,
                "code": "picked",
                "target_pixels": 2,
                "region_pixels": 4,
            },
        ],
        "observations": [
            {
                "object": OBJECT,
                "provenance": "native",
                "kind": "reading",
                "artifact": PACKED_ARTIFACT,
                "series_uid": "axial-target",
                "view": list(PACKED_VIEW),
                "slices": [10],
                "row": 1,
                "support": f"{PACKED}region",
                "label": None,
                "code": "picked",
                "count": 2,
            }
        ],
    }

    result = {
        "study_uid": STUDY,
        "records": [
            native_record,
            trace_target_record,
            trace_owner_record,
            packed_record,
        ],
        "main_records": [],
        "objects": {OBJECT: {}},
    }
    return (
        run_dir,
        main_run,
        result,
        {"native": native_arrays, "trace": trace_arrays, "packed": packed_arrays},
    )


def _metric(outcome: dict, metric: str) -> dict:
    return next(item for item in outcome["metrics"] if item["metric"] == metric)


def _bundle_from_manifest(outcome: dict) -> CountBundle:
    described = outcome["bundle_layout"]
    layout = CountLayout(
        described["layout_id"],
        described["carrier_id"],
        tuple(
            BankLayout(item["name"], item["row_count"]) for item in described["banks"]
        ),
    )
    return CountBundle(
        layout, tuple(tuple(int(n) for n in bank) for bank in outcome["counts"])
    )


def _expected_named_rows(light_counts, aux_counts):
    return (
        *(
            ("signal", FACET, "light", name, int(n))
            for name, n in zip(ROW_NAMES, light_counts, strict=True)
        ),
        *(
            ("signal", FACET, "aux", name, int(n))
            for name, n in zip(ROW_NAMES, aux_counts, strict=True)
        ),
    )


def test_three_source_families_share_identity_and_reconstruct_from_h5(tmp_path):
    pytest.importorskip("h5py")
    run_dir, main_run, result, arrays = _build_study(tmp_path)
    spec = _spec([_native_profile(), _trace_profile(), _packed_profile()], "h5")
    compiled = validate_spec(spec)["layout"]
    out = tmp_path / "out"
    out.mkdir()

    status = encode_study(result, run_dir, main_run, spec, out / "enc.json")

    h5_file = out / "enc.h5"
    assert status["manifest"] == status["archive"] == str(h5_file)
    assert [p.name for p in out.iterdir()] == ["enc.h5"]
    links = result["objects"][OBJECT]["encoding"]
    assert [link["profile_index"] for link in links] == [0, 1, 2]
    assert all(link["manifest"] == str(h5_file) for link in links)

    with open_product(status["manifest"]) as product:
        assert product.storage == "h5"
        manifest = product.manifest
        assert manifest["spec"]["storage"] == "h5"
        assert manifest["layout_fingerprint"] == compiled.fingerprint
        assert len(manifest["profiles"]) == 3
        assert all(len(p["outcomes"]) == 1 for p in manifest["profiles"])
        outcomes = {
            name: profile["outcomes"][0]
            for name, profile in zip(
                ("native", "trace", "packed"), manifest["profiles"], strict=True
            )
        }
        assert manifest["work"]["opened_artifacts"] == 3
        assert manifest["work"]["bundle_count"] == 3
        assert manifest["work"]["addressed_places"] == 4 + 4 + 4
        assert manifest["work"]["metric_row_arrays"] == 6

        # ---- per-profile row codes: measured zero vs unread vs unavailable ----
        light_codes: dict[str, list[int]] = {}
        for name, outcome in outcomes.items():
            assert outcome["status"] == "ok"
            assert outcome["encoding_status"] == "ok"
            assert outcome["place_count"] == 4
            light = _metric(outcome, "light")
            aux = _metric(outcome, "aux")
            assert light["row_names"] == list(ROW_NAMES)
            assert aux["row_names"] == list(ROW_NAMES)
            codes = product.arrays[light["row_codes"]]
            aux_codes = product.arrays[aux["row_codes"]]
            assert codes.dtype == np.int16 and aux_codes.dtype == np.int16
            light_codes[name] = codes.tolist()
            assert light_codes[name] == EXPECTED_LIGHT_CODES[name]
            assert light["status"] == "ok"

            # Unread: every place -1, named silent, and no count contribution.
            assert aux_codes.tolist() == [-1, -1, -1, -1]
            assert aux["status"] == "silent"
            counts = outcome["counts"][0]
            assert tuple(counts[3:6]) == (0, 0, 0)
            assert not any(counts[3:])

            # Measured zero takes the declared middle row and increments it.
            assert codes[0] == 1
            assert tuple(counts[:3]) == EXPECTED_PROFILE_LIGHT_COUNTS[name]
            assert counts[1] == int(np.count_nonzero(codes == 1))
            assert not any(counts[6:])

        # An unavailable (unmeasured) light place is not a measured middle.
        assert light_codes["native"][3] == -1
        assert light_codes["packed"][3] == -1

        # ---- shared layout / reference identities across families ----
        fingerprints = {o["reference_set_fingerprint"] for o in outcomes.values()}
        layout_ids = {o["bundle_layout"]["layout_id"] for o in outcomes.values()}
        carrier_ids = {o["bundle_layout"]["carrier_id"] for o in outcomes.values()}
        assert len(fingerprints) == 1 and None not in fingerprints
        assert len(layout_ids) == 1
        assert len(carrier_ids) == 1
        assert carrier_ids == {manifest["carrier_identity"]}
        assert {o["layout_fingerprint"] for o in outcomes.values()} == {
            compiled.fingerprint
        }
        reference_fp = next(iter(fingerprints))
        assert next(iter(layout_ids)).endswith(f":{reference_fp}")

        # ---- source addresses stay distinguishable ----
        native, trace, packed = (
            outcomes["native"],
            outcomes["trace"],
            outcomes["packed"],
        )
        assert product.arrays[native["points_rc"]].tolist() == [
            [0, 0],
            [0, 2],
            [1, 0],
            [1, 1],
        ]
        assert native["artifact"] == native["target_artifact"] == NATIVE_ARTIFACT
        assert set(native["metadata"]["source_refs"]) == {
            "native_mask",
            "native_light",
            "native_avail",
        }
        native_address = native["metadata"]["unread_sources"][0]["source_address"]
        assert native_address["artifact"] == NATIVE_ARTIFACT
        assert native_address["series_uid"] == "native-series"
        assert native_address["slice_index"] == 0
        assert native_address["support"] == "native_mask"

        assert product.arrays[trace["points_lps"]].tolist() == (
            arrays["trace"][TRACE_SUPPORT].tolist()
        )
        assert trace["artifact"] == TRACE_OWNER_ARTIFACT
        assert trace["target_artifact"] == TRACE_TARGET_ARTIFACT
        assert trace["metadata"]["row"] == 0
        assert trace["metadata"]["slice_index"] == 2
        assert trace["metadata"]["point_count"] == 4
        assert trace["metadata"]["owner_series_uid"] == "trace-owner"
        assert trace["metadata"]["target_series_uid"] == "trace-target"
        assert trace["metadata"]["addresses"] == "patient_lps_points"
        assert trace["metadata"]["unread_sources"][0]["source_address"] == {
            "owner_artifact": TRACE_OWNER_ARTIFACT,
            "owner_series_uid": "trace-owner",
            "target_series_uid": "trace-target",
            "target_view": TRACE_VIEW,
            "support": TRACE_SUPPORT,
            "row": 0,
            "slice_index": 2,
        }

        assert product.arrays[packed["points_rc"]].tolist() == [
            [0, 0],
            [0, 2],
            [1, 0],
            [1, 1],
        ]
        assert packed["artifact"] == PACKED_ARTIFACT
        assert packed["metadata"]["packed_row"] == 1
        assert packed["metadata"]["packed_slice_index"] == 10
        assert packed["metadata"]["source_owner_series_uid"] == "fibula-owner"
        assert packed["metadata"]["target_series_uid"] == "axial-target"
        assert packed["metadata"]["target_view"] == PACKED_VIEW
        assert packed["metadata"]["declared_count"] == 2
        assert packed["metadata"]["packed_target_count"] == 2
        assert packed["metadata"]["decoded_support_count"] == 4
        assert packed["metadata"]["packed_frame"]["origin_lps"] == [1.0, 2.0, 3.0]
        packed_address = packed["metadata"]["unread_sources"][0]["source_address"]
        assert packed_address["owner_artifact"] == PACKED_ARTIFACT
        assert packed_address["owner_series_uid"] == "fibula-owner"
        assert packed_address["target_series_uid"] == "axial-target"
        assert packed_address["row"] == 1
        assert packed_address["slice_index"] == 10

        assert len({native["artifact"], trace["artifact"], packed["artifact"]}) == 3

        # ---- reconstruct bundles from manifest fields + public count API ----
        bundles = {name: _bundle_from_manifest(o) for name, o in outcomes.items()}
        layouts = {bundle.layout for bundle in bundles.values()}
        assert len(layouts) == 1

        # Independent expectation from the emitted per-place row codes.
        all_light = np.concatenate(
            [np.asarray(light_codes[name]) for name in ("native", "trace", "packed")]
        )
        written = all_light[all_light >= 0]
        expected_light = np.bincount(written, minlength=3).tolist()
        assert tuple(expected_light) == EXPECTED_COMBINED_LIGHT_COUNTS
        expected_aux = [0, 0, 0]

        for name, bundle in bundles.items():
            per_profile = np.bincount(
                [c for c in light_codes[name] if c >= 0], minlength=3
            ).tolist()
            decoded = decode_count_names(compiled, bundle, reference_fp)
            assert decoded == _expected_named_rows(per_profile, [0, 0, 0])

        total = bundles["native"]
        for name in ("trace", "packed"):
            added = add_counts(total, bundles[name])
            assert added.code is CountCode.OK
            assert added.bundle is not None
            total = added.bundle
        reversed_total = add_counts(
            add_counts(bundles["packed"], bundles["trace"]).bundle, bundles["native"]
        )
        assert reversed_total.code is CountCode.OK
        assert reversed_total.bundle == total

        manual = tuple(
            tuple(
                sum(bundles[name].counts[bank][row] for name in bundles)
                for row in range(512)
            )
            for bank in range(1)
        )
        assert total.counts == manual

        decoded_total = decode_count_names(compiled, total, reference_fp)
        assert decoded_total == _expected_named_rows(expected_light, expected_aux)
        assert decoded_total == (
            ("signal", FACET, "light", "-1", 3),
            ("signal", FACET, "light", "0", 4),
            ("signal", FACET, "light", "+1", 3),
            ("signal", FACET, "aux", "-1", 0),
            ("signal", FACET, "aux", "0", 0),
            ("signal", FACET, "aux", "+1", 0),
        )

        # A bundle bound to different reference identity is refused by name.
        assert decode_count_names(compiled, total, "0" * 64) is None

        # ---- carrier vectors decode back to the same exact counts ----
        carrier = HadamardCarrier.from_banks(["signal"])
        assert carrier.identity == manifest["carrier_identity"]
        for outcome in outcomes.values():
            assert outcome["carrier_status"] == "encoded"
            vector = product.arrays[outcome["carrier_vector"]]
            assert vector.shape == (1, 512) and vector.dtype == np.int32
            assert carrier.decode(vector)[0].tolist() == outcome["counts"][0]


@pytest.mark.parametrize("storage", ["npz_xz", "h5"])
def test_duplicate_profile_opens_and_verifies_each_source_once(
    tmp_path, monkeypatch, storage
):
    if storage == "h5":
        pytest.importorskip("h5py")
    run_dir, main_run, result, arrays = _build_study(tmp_path)
    spec = _spec([_native_profile(), _native_profile()], storage)

    opens: list[Path] = []
    original_open = operation.open_arrays

    def counted_open(path):
        opens.append(Path(path))
        return original_open(path)

    import knee.encoding.handoff as handoff_module

    original_digest = handoff_module.digest
    verified_names: list[tuple] = []

    def counted_digest(array):
        verified_names.append((array.shape, array.dtype.str))
        return original_digest(array)

    monkeypatch.setattr(operation, "open_arrays", counted_open)
    monkeypatch.setattr(handoff_module, "digest", counted_digest)

    out = tmp_path / "out"
    out.mkdir()
    status = encode_study(result, run_dir, main_run, spec, out / "enc.json")

    # One archive opening and one verification per distinct source array.
    assert len(opens) == 1
    assert opens[0].name == "native-series.npz.xz"
    assert len(verified_names) == 3

    work = status["work"]
    native_arrays = arrays["native"]
    assert work["opened_artifacts"] == 1
    assert work["verified_source_arrays"] == 3
    assert work["source_bytes_verified"] == sum(
        a.nbytes for a in native_arrays.values()
    )
    assert work["addressed_places"] == 8
    assert work["bundle_count"] == 2
    assert work["metric_row_arrays"] == 4

    # The two addressed outputs remain separate.
    with open_product(status["manifest"]) as product:
        manifest = product.manifest
        assert manifest["work"]["opened_artifacts"] == 1
        first, second = (p["outcomes"][0] for p in manifest["profiles"])
        assert first["status"] == second["status"] == "ok"
        assert first["points_rc"] != second["points_rc"]
        assert first["points_rc"].startswith("p0_o0000_")
        assert second["points_rc"].startswith("p1_o0000_")
        for key in ("points_rc",):
            a, b = product.arrays[first[key]], product.arrays[second[key]]
            assert a is not b
            assert a.tolist() == b.tolist()
        for metric in ("light", "aux"):
            m0, m1 = _metric(first, metric), _metric(second, metric)
            assert m0["row_codes"] != m1["row_codes"]
            c0, c1 = product.arrays[m0["row_codes"]], product.arrays[m1["row_codes"]]
            assert c0 is not c1
            assert c0.tolist() == c1.tolist()
        assert (
            product.arrays[_metric(first, "light")["row_codes"]].tolist()
            == (EXPECTED_LIGHT_CODES["native"])
        )
        assert product.arrays[_metric(first, "aux")["row_codes"]].tolist() == [-1] * 4
        assert first["counts"] == second["counts"]
        assert first["reference_set_fingerprint"] == second["reference_set_fingerprint"]
        assert first["bundle_layout"] == second["bundle_layout"]
        assert first["metadata"]["source_refs"] == second["metadata"]["source_refs"]
