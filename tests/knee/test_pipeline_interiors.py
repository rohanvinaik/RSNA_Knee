"""The geometric reading must consume the actual regime through Chapter 1."""

import numpy as np
from test_pipeline_measurements import (
    STACKED_UID,
    STUDY_UID,
    _write_corpus,
)

from knee import pipeline
from knee.collapse.analysis import AnalysisRequest


def test_real_study_entry_carries_interior_reading_even_when_requested_axis_is_unavailable(
    tmp_path,
):
    _write_corpus(tmp_path)
    request = AnalysisRequest(
        2.0, (-1.0, 0.0, 1.0), (0.0, 0.0, 1.0), "reference", prominence_mm=1.0
    )
    result = pipeline.open_and_run(tmp_path, STUDY_UID, request)
    series = next(s for s in result.series if s.series_uid == STACKED_UID)
    measured = series.measurements
    assert measured is not None and measured.interiors is not None
    assert measured.code == "axis_unavailable"
    assert measured.acquired_plane is not None
    assert series.regime is not None
    np.testing.assert_array_equal(
        measured.interiors.dark,
        np.isfinite(measured.acquired_plane)
        & (measured.acquired_plane <= series.regime.background_split),
    )
    assert measured.interiors.available.shape == measured.acquired_plane.shape
