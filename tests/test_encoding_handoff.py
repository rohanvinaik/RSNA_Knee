"""Intent checks at the addressed measurement/representation boundary."""

import numpy as np

from knee.encoding.carrier import HadamardCarrier
from knee.encoding.handoff import encode_observation
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    NumericReference,
    compile_layout,
)
from knee.receipt import digest


def fixture():
    carrier = HadamardCarrier(("test_lens",))
    layout = compile_layout(
        LayoutSpec(
            "test-only",
            carrier.identity,
            (
                BankSpec(
                    "test_lens", "test-only", (MetricSpec("number", MetricKind.DIGIT),)
                ),
            ),
        )
    )
    assert layout is not None
    support = np.zeros((2, 5, 6), dtype=bool)
    support[1, 2, 3:5] = True
    arrays = {
        "support": support,
        "raw_crop": np.array([[2, 4]], dtype=np.uint16),
        "available_crop": np.array([[True, False]]),
        "window": np.array([2, 3, 3, 5], dtype=np.int32),
    }
    record = {
        "series_uid": "series",
        "view": ["sagittal", "fluid", "fat-suppressed"],
        "study_uid": "study",
        "slice_index": 7,
        "artifact": "study/series.npz.xz",
        "arrays": {name: {"digest": digest(a)} for name, a in arrays.items()},
        "plane_frame": {"origin_lps": [0, 1, 2], "basis_lps": [[1, 0], [0, 1], [0, 0]]},
    }
    obs = {
        "object": "test_object",
        "series_uid": "series",
        "view": ["sagittal", "fluid", "fat-suppressed"],
        "slices": [7],
        "artifact": record["artifact"],
        "support": "support",
        "row": 1,
        "label": None,
        "count": 2,
        "kind": "reading",
        "provenance": "native",
    }
    bindings = [
        {
            "bank": "test_lens",
            "metric": "number",
            "value": "raw_crop",
            "available": "available_crop",
            "window": "window",
        }
    ]
    # Mechanical fixture only, never a clinical healthy reference.
    refs = {
        ("test_lens", "number"): NumericReference(
            layout.fingerprint,
            "test_lens",
            "number",
            "fixture",
            "unit test",
            "arbitrary fixture units",
            2,
            2,
        )
    }
    return layout, record, obs, arrays, bindings, refs


def test_crop_row_codes_are_addressed_to_actual_support_and_unknown_exterior():
    layout, record, obs, arrays, bindings, refs = fixture()
    encoded = encode_observation(record, obs, arrays, layout, bindings, refs)
    assert encoded.status == "ok"
    assert encoded.points_rc is not None
    assert encoded.encoding is not None and encoded.encoding.bundle is not None
    assert encoded.points_rc.tolist() == [[2, 3], [2, 4]]
    assert encoded.encoding.metrics[0].row_codes.tolist() == [1, -1]
    assert encoded.encoding.bundle.counts[0][:3] == (0, 1, 0)
    assert encoded.metadata["source_refs"]["raw_crop"]["digest"] == digest(
        arrays["raw_crop"]
    )
    assert encoded.metadata["plane_frame"] == record["plane_frame"]
    assert encoded.metadata["references"][0]["source"] == "unit test"


def test_projected_target_is_never_encoded_as_observed_tissue():
    layout, record, obs, arrays, bindings, refs = fixture()
    obs.update(provenance="projected", kind="target")
    encoded = encode_observation(record, obs, arrays, layout, bindings, refs)
    assert encoded.status == "target_only"
    assert encoded.encoding is None and encoded.points_rc is None


def test_digest_and_count_mismatches_are_named_and_keep_source_address():
    layout, record, obs, arrays, bindings, refs = fixture()
    arrays["raw_crop"][0, 0] = 3
    encoded = encode_observation(record, obs, arrays, layout, bindings, refs)
    assert encoded.status == "digest_mismatch"
    assert encoded.metadata["observation"] == obs
    layout, record, obs, arrays, bindings, refs = fixture()
    obs["count"] = 1
    assert (
        encode_observation(record, obs, arrays, layout, bindings, refs).status
        == "support_count_mismatch"
    )


def test_record_frame_does_not_migrate_to_a_different_slice():
    layout, record, obs, arrays, bindings, refs = fixture()
    obs["slices"] = [8]
    encoded = encode_observation(record, obs, arrays, layout, bindings, refs)
    assert encoded.status == "ok"
    assert encoded.metadata["plane_frame"] is None
    assert encoded.metadata["geometry_status"] == "frame_not_retained_for_slice"


def test_packed_trace_and_wrong_artifact_cannot_be_guessed_as_image_support():
    layout, record, obs, arrays, bindings, refs = fixture()
    arrays["support"] = np.zeros((20, 3), dtype=float)
    record["arrays"]["support"]["digest"] = digest(arrays["support"])
    assert (
        encode_observation(record, obs, arrays, layout, bindings, refs).status
        == "support_adapter_required"
    )
    obs["artifact"] = "other.npz.xz"
    assert (
        encode_observation(record, obs, arrays, layout, bindings, refs).status
        == "source_artifact_mismatch"
    )


def test_reference_missing_is_named_and_original_measurements_stay_addressed():
    layout, record, obs, arrays, bindings, _ = fixture()
    encoded = encode_observation(record, obs, arrays, layout, bindings, {})
    assert encoded.status == "missing_reference"
    assert encoded.encoding is not None and encoded.encoding.bundle is not None
    assert not any(encoded.encoding.bundle.counts[0])
    assert encoded.metadata["source_refs"]["raw_crop"]["shape"] == [1, 2]


def test_implicit_plane_and_noninteger_count_cannot_be_misaddressed():
    layout, record, obs, arrays, bindings, refs = fixture()
    obs["count"] = 2.0
    assert (
        encode_observation(record, obs, arrays, layout, bindings, refs).status
        == "invalid_support_count"
    )
    obs["count"] = 2
    arrays["support"] = arrays["support"][1]
    record["arrays"]["support"]["digest"] = digest(arrays["support"])
    obs.update(row=None, slices=[8])
    assert (
        encode_observation(record, obs, arrays, layout, bindings, refs).status
        == "plane_address_required"
    )


def test_plane_frame_retention_uses_existing_frame_without_new_measurement():
    import importlib.util
    import sys
    from pathlib import Path
    from types import SimpleNamespace

    from knee.collapse.physical import PlaneFrame
    from knee.objects.interiors import InteriorRegions

    name = "_encoding_driver"
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parents[1] / "scripts/run_interiors.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    frame = PlaneFrame.from_dicom([1, 2, 3], [1, 0, 0, 0, 1, 0], [0.5, 0.75])
    shape = (2, 3)
    zeros = np.zeros(shape)
    reading = InteriorRegions(
        "ok",
        np.zeros(shape, dtype=bool),
        np.ones(shape, dtype=bool),
        zeros,
        np.zeros(shape, dtype=np.int32),
        np.zeros(shape, dtype=np.int32),
    )
    series = SimpleNamespace(
        row=SimpleNamespace(
            series_uid="series",
            anatomical_plane="Axial",
            fluid_sensitive="1",
            fat_suppression="1",
        ),
        slices=[SimpleNamespace(path=Path("image.dcm"))],
    )
    field = SimpleNamespace(objects=np.zeros(shape, dtype=np.int8), peaks=())
    record, _ = module.slice_record(
        series, 0, 1, "R", (zeros, reading, {}), field, frame=frame
    )
    assert record["plane_frame"]["origin_lps"] == frame.origin_lps.tolist()
    assert record["plane_frame"]["basis_lps"] == frame.basis_lps.tolist()
    assert record["plane_frame"]["spacing_rc"] == list(frame.spacing_rc)
