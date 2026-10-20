"""Bad coordinates remain bad coordinates even when reference context is missing."""

import numpy as np
import pytest

from knee.encoding.spatial import (
    batch_native_rc_readings,
    joint_status_name,
    native_rc_reading,
    prepare_spatial_context,
)


@pytest.mark.parametrize("reference_present", [True, False])
@pytest.mark.parametrize(
    ("point", "frame", "expected"),
    [
        ([1.0, 2.0], None, "frame_unavailable"),
        ([1.0, 2.0], {}, "malformed_frame"),
        ([float("nan"), 2.0], None, "nonfinite_coordinate"),
    ],
)
def test_batch_and_scalar_preserve_the_actual_coordinate_refusal(
    reference_present, point, frame, expected
):
    context = prepare_spatial_context(
        {
            "schema": "study_map/v1",
            "knee": "R",
            "objects": {
                "femur": {
                    "status": "complete" if reference_present else "partial",
                    "point_lps": [0.0, 0.0, 0.0] if reference_present else None,
                    "precision_mm": [1.0, 1.0, 1.0],
                }
            },
        },
        "femur",
    )
    scalar = native_rc_reading(context, point, view="Axial", frame=frame)
    batch = batch_native_rc_readings(context, np.asarray([point]), frame=frame)
    assert scalar.joint_code_status == expected
    assert joint_status_name(batch.joint_codes[0]) == expected
    assert scalar.joint_code is None
    assert batch.joint_code[0] == -1
