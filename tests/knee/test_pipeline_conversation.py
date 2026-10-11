"""Conversation request through the real study route, using the measurement corpus fixture."""

import importlib.util
from pathlib import Path

import knee.study.series as series_module
from knee import pipeline
from knee.collapse.analysis import AnalysisRequest

_fixture_path = Path(__file__).with_name("test_pipeline_measurements.py")
_fixture_spec = importlib.util.spec_from_file_location(
    "pipeline_measurement_fixture", _fixture_path
)
assert _fixture_spec is not None and _fixture_spec.loader is not None
_fixture_module = importlib.util.module_from_spec(_fixture_spec)
_fixture_spec.loader.exec_module(_fixture_module)
STUDY_UID = _fixture_module.STUDY_UID
_write_corpus = _fixture_module._write_corpus


def test_conversation_request_returns_one_record_per_series_and_reads_slices_once(
    tmp_path: Path, monkeypatch
) -> None:
    _write_corpus(tmp_path)
    counts: dict[str, int] = {}
    real_read_slice = series_module.read_slice

    def counted(path):
        counts[path.parent.name] = counts.get(path.parent.name, 0) + 1
        return real_read_slice(path)

    monkeypatch.setattr(series_module, "read_slice", counted)
    request = AnalysisRequest(
        tile_mm=2.0,
        offsets_mm=(-1.0, 0.0, 1.0),
        direction_lps=(1.0, 0.0, 0.0),
        backend="reference",
        prominence_mm=1.0,
        conversation=True,
    )

    result = pipeline.open_and_run(tmp_path, STUDY_UID, request)

    assert len(result.series) == 2
    assert len(result.conversations) == len(result.series)
    assert [row.series_uid for row in result.conversations] == [
        row.series_uid for row in result.series
    ]
    assert counts == {"series-axial": 3, "series-shape-varies": 2}


def test_default_request_keeps_conversation_off_and_conversation_requires_prominence() -> (
    None
):
    import pytest

    with pytest.raises(ValueError, match="invalid_conversation_request"):
        AnalysisRequest(
            tile_mm=2.0,
            offsets_mm=(-1.0, 0.0, 1.0),
            direction_lps=(1.0, 0.0, 0.0),
            backend="reference",
            conversation=True,
        )


def test_default_pipeline_route_returns_no_conversations(tmp_path: Path) -> None:
    _write_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID)
    assert result.conversations == ()
    assert all(row.measurements is None for row in result.series)
