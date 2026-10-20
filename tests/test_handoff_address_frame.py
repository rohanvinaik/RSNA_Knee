"""Intent checks for per-observation slice frames and measurement guards."""

import numpy as np
import pytest

from knee.encoding.carrier import HadamardCarrier
from knee.encoding.handoff import address_frame_status, encode_observation
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    compile_layout,
)
from knee.receipt import digest

VALID_FRAME = {
    "origin_lps": [12.0, -4.0, 7.0],
    "basis_lps": [[0.0, 1.3], [0.6, 0.0], [0.8, 0.0]],
}


def fixture():
    carrier = HadamardCarrier(("lens",))
    layout = compile_layout(
        LayoutSpec(
            "address-frame-test",
            carrier.identity,
            (
                BankSpec(
                    "lens",
                    "test",
                    (MetricSpec("word", MetricKind.WORDS, ("False", "True")),),
                ),
            ),
        )
    )
    assert layout is not None
    support = np.zeros((5, 6), dtype=bool)
    support[2, 3:5] = True
    arrays = {"support": support}
    record_frame = {
        "origin_lps": [1.0, 2.0, 3.0],
        "basis_lps": [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]],
    }
    record = {
        "series_uid": "series",
        "view": ["Axial", "1", "1"],
        "slice_index": 7,
        "artifact": "study/series.npz.xz",
        "arrays": {"support": {"digest": digest(support)}},
        "plane_frame": record_frame,
    }
    observation = {
        "object": "mcl",
        "provenance": "native",
        "kind": "reading",
        "series_uid": "series",
        "view": ["Axial", "1", "1"],
        "slices": [8],
        "artifact": record["artifact"],
        "support": "support",
        "row": None,
        "label": None,
        "count": 2,
    }
    return layout, record, observation, arrays


def test_intent_valid_observation_frame_addresses_2d_support_on_its_slice():
    layout, record, observation, arrays = fixture()
    observation["address_frame"] = VALID_FRAME

    encoded = encode_observation(record, observation, arrays, layout, [], {})

    assert encoded.points_rc is not None
    assert encoded.points_rc.tolist() == [[2, 3], [2, 4]]
    assert encoded.metadata["plane_frame"] == VALID_FRAME
    assert encoded.metadata["plane_frame_source"] == "observation.address_frame"
    assert encoded.metadata["native_shape_rc"] == [5, 6]


def test_intent_invalid_explicit_frame_refuses_instead_of_falling_back():
    layout, record, observation, arrays = fixture()
    observation["address_frame"] = {
        "origin_lps": [0.0, 0.0, 0.0],
        "basis_lps": [[1.0, 2.0], [2.0, 4.0], [0.0, 0.0]],
    }

    encoded = encode_observation(record, observation, arrays, layout, [], {})

    assert encoded.status == "invalid_observation_address_frame"
    assert encoded.points_rc is None
    assert encoded.metadata["plane_frame_source"] == "observation.address_frame_invalid"
    assert "plane_frame" not in encoded.metadata
    assert record["plane_frame"] is not None


def test_intent_missing_frame_keeps_existing_nonmiddle_refusal():
    layout, record, observation, arrays = fixture()

    encoded = encode_observation(record, observation, arrays, layout, [], {})

    assert encoded.status == "plane_address_required"
    assert encoded.points_rc is None


def test_intent_observation_frame_does_not_authorize_record_plane_measurements():
    layout, record, observation, arrays = fixture()
    observation["address_frame"] = VALID_FRAME
    values = np.ones((5, 6), dtype=bool)
    arrays["values"] = values
    arrays["available"] = np.ones((5, 6), dtype=bool)
    record["arrays"].update(
        values={"digest": digest(arrays["values"])},
        available={"digest": digest(arrays["available"])},
    )
    binding = [
        {"bank": "lens", "metric": "word", "value": "values", "available": "available"}
    ]

    encoded = encode_observation(record, observation, arrays, layout, binding, {})

    assert encoded.status == "measurement_plane_address_required"
    assert encoded.points_rc is None


def test_intent_observation_frame_does_not_authorize_record_plane_context():
    layout, record, observation, arrays = fixture()
    observation["address_frame"] = VALID_FRAME
    binding = [
        {
            "bank": "lens",
            "metric": "word",
            "source": "record_context",
            "scope": "record_plane",
            "path": "missing",
        }
    ]

    encoded = encode_observation(record, observation, arrays, layout, binding, {})

    assert encoded.status == "context_record_plane_slice_mismatch"
    assert encoded.points_rc is None


def test_intent_matching_record_slice_keeps_existing_frame_provenance():
    layout, record, observation, arrays = fixture()
    observation["slices"] = [7]

    encoded = encode_observation(record, observation, arrays, layout, [], {})

    assert encoded.metadata["plane_frame"] == record["plane_frame"]
    assert encoded.metadata["plane_frame_source"] == "record.plane_frame"


@pytest.mark.parametrize(
    "frame",
    [
        {},
        {"origin_lps": [0.0, 1.0], "basis_lps": [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]},
        {
            "origin_lps": [0.0, 1.0, 2.0],
            "basis_lps": [[1.0, 0.0], [0.0, True], [0.0, 1.0]],
        },
        {
            "origin_lps": [0.0, 1.0, float("nan")],
            "basis_lps": [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]],
        },
        {
            "origin_lps": [0.0, 1.0, 2.0],
            "basis_lps": [[1.0, 0.0], [2.0, 0.0], [0.0, 0.0]],
        },
    ],
)
def test_intent_explicit_frame_requires_finite_nonboolean_nondegenerate_axes(frame):
    assert address_frame_status(frame) == "frame_invalid"
