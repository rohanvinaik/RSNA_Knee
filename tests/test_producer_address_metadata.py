from __future__ import annotations

import pytest

from knee.collapse.observations import Observation, describe_objects, rows
from knee.collapse.physical import PlaneFrame
from scripts.run_interiors import _address_frame, observe_in


def test_existing_observation_rows_keep_the_old_shape_without_frame_metadata():
    observation = Observation(
        "mcl",
        "native",
        "reading",
        "series",
        ("Axial", "1", "1"),
        (12,),
        "identified",
        4,
        0.0,
        "a4_axial_mcl_z12_support",
        "local reading",
        "study/series.npz.xz",
    )

    result = rows([observation])[0]

    assert "address_frame" not in result
    assert result["support"] == "a4_axial_mcl_z12_support"
    assert result["slices"] == (12,)


def test_observe_in_retains_the_exact_oblique_slice_frame():
    frame = PlaneFrame.from_dicom(
        [12.0, -4.0, 7.0],
        [0.0, 1.0, 0.0, 0.6, 0.0, 0.8],
        [0.7, 1.3],
    )
    record = {
        "series_uid": "series",
        "view": ["Axial", "1", "1"],
    }
    address = _address_frame(frame)

    observation = observe_in(
        record,
        "mcl",
        "native",
        "resolved",
        (12,),
        "identified",
        9,
        0.0,
        "a4_axial_mcl_z12_support",
        "bounded local section",
        "study/series.npz.xz",
        address_frame=address,
    )

    retained = rows([observation])[0]["address_frame"]
    assert retained["origin_lps"] == [12.0, -4.0, 7.0]
    assert retained["basis_lps"] == frame.basis_lps.tolist()
    assert retained["basis_lps"] != [[1.3, 0.0], [0.0, 0.7], [0.0, 0.0]]


@pytest.mark.parametrize("with_frame", [True, False])
def test_object_output_keeps_observation_frame_without_inventing_one(with_frame):
    record = {"series_uid": "series", "view": ["Axial", "1", "1"]}
    frame = {
        "origin_lps": [12.0, -4.0, 7.0],
        "basis_lps": [[0.0, 1.3], [0.7, 0.0], [0.0, 0.0]],
    }
    observation = observe_in(
        record,
        "mcl",
        "native",
        "reading",
        (12,),
        "identified",
        2,
        0.0,
        "a4_axial_mcl_z12_support",
        "native slice",
        "study/series.npz.xz",
        address_frame=frame if with_frame else None,
    )
    record["observations"] = rows([observation])
    described = describe_objects([record], ("mcl",))
    reference = described["mcl"]["observations"]["native"]["reading"][
        "a4_axial_mcl_z12_support"
    ][0]
    assert reference["slices"] == (12,)
    if with_frame:
        assert reference["address_frame"] == frame
    else:
        assert "address_frame" not in reference


@pytest.mark.parametrize(
    "address",
    [
        {"origin_lps": [0.0, 0.0], "basis_lps": [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]},
        {
            "origin_lps": [0.0, 0.0, 0.0],
            "basis_lps": [[1.0, 0.0], [0.0, True], [0.0, 0.0]],
        },
        {"origin_lps": [0.0, 0.0, 0.0], "basis_lps": [[1.0, 0.0], [0.0, 1.0]]},
    ],
)
def test_malformed_retained_slice_frame_is_rejected(address):
    with pytest.raises(ValueError, match="observation_address_frame"):
        Observation(
            "pcl",
            "native",
            "reading",
            "series",
            ("Axial", "1", "1"),
            (15,),
            "partial_reading",
            3,
            0.0,
            "a4_axial_pcl_z15_support",
            "bounded local section",
            "study/series.npz.xz",
            address_frame=address,
        )
