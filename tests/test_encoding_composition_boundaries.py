from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest
from test_encoding_composition import _fixture

from knee.encoding.composition import CompositionCode, StudyComposer
from knee.encoding.trace_adapter import TraceEncoding


def _trace(addressed, metadata):
    points = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 0.0], [2.0, 2.0, 0.0]])
    return TraceEncoding(addressed.status, addressed.encoding, points, metadata)


def _observation_metadata(addressed, **changes):
    metadata = dict(addressed.metadata)
    metadata["observation"] = {**metadata["observation"], **changes}
    return metadata


def test_rowcode_below_no_measurement_is_refused_and_nothing_committed():
    prepared, profile, addressed, map_record = _fixture()
    metric = addressed.encoding.metrics[0]
    codes = np.array(metric.row_codes, dtype=np.int16, copy=True)
    codes[2] = -2
    bad_encoding = replace(
        addressed.encoding, metrics=(replace(metric, row_codes=codes),)
    )
    composer = StudyComposer(prepared, map_record)
    result = composer.add(
        "cartilage", 0, 0, replace(addressed, encoding=bad_encoding), profile
    )
    assert result.code is CompositionCode.METRIC_ROW_MISMATCH
    assert not result.batches
    assembly = composer.finalize().objects["cartilage"].assembly
    assert assembly is not None
    assert assembly.profile.entries == ()
    assert len(assembly.batches) == 0


def test_valid_rowcodes_still_compose():
    prepared, profile, addressed, map_record = _fixture()
    result = StudyComposer(prepared, map_record).add(
        "cartilage", 0, 0, addressed, profile
    )
    assert result.code is CompositionCode.OK
    assert len(result.batches) == 3


def test_coordinate_batches_are_immutable_owned_snapshots():
    prepared, profile, addressed, map_record = _fixture()
    original = addressed.points_rc.copy()
    result = StudyComposer(prepared, map_record).add(
        "cartilage", 0, 0, addressed, profile
    )
    assert result.code is CompositionCode.OK
    addressed.points_rc[0, 0] = 99
    addressed.points_rc[2, 1] = 77
    for batch in result.batches:
        coords = batch.addresses.coordinates
        assert 99 not in coords and 77 not in coords
        assert not coords.flags.writeable
        with pytest.raises(ValueError):
            coords.flags.writeable = True
    overview = next(b for b in result.batches if b.facet_coordinate.direction is None)
    np.testing.assert_array_equal(overview.addresses.coordinates, original)
    for index_map in result.batch_index_maps:
        assert not index_map.original_place_indices.flags.writeable
        with pytest.raises(ValueError):
            index_map.original_place_indices.flags.writeable = True


def test_trace_with_single_slice_composes():
    prepared, profile, addressed, map_record = _fixture()
    trace = _trace(addressed, addressed.metadata)
    result = StudyComposer(prepared, map_record).add("cartilage", 0, 0, trace, profile)
    assert result.code is CompositionCode.OK


@pytest.mark.parametrize("slices", [[], [1, 2], [-1], [True], "4", None, ["4"]])
def test_trace_malformed_slices_are_named_refusals(slices):
    prepared, profile, addressed, map_record = _fixture()
    trace = _trace(addressed, _observation_metadata(addressed, slices=slices))
    result = StudyComposer(prepared, map_record).add("cartilage", 0, 0, trace, profile)
    assert result.code is CompositionCode.SPATIAL_INPUT_MALFORMED
    assert not result.batches


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), object()])
def test_trace_nonfinite_or_nonjson_frame_fields_are_named_refusals(bad):
    prepared, profile, addressed, map_record = _fixture()
    metadata = {**addressed.metadata, "owner_series_uid": bad}
    result = StudyComposer(prepared, map_record).add(
        "cartilage", 0, 0, _trace(addressed, metadata), profile
    )
    assert result.code is CompositionCode.SPATIAL_INPUT_MALFORMED
    assert not result.batches


@pytest.mark.parametrize("bad", [float("nan"), object()])
def test_native_nonfinite_or_nonjson_frame_field_is_named_refusal(bad):
    prepared, profile, addressed, map_record = _fixture()
    malformed = replace(
        addressed, metadata=_observation_metadata(addressed, series_uid=bad)
    )
    result = StudyComposer(prepared, map_record).add(
        "cartilage", 0, 0, malformed, profile
    )
    assert result.code is CompositionCode.SPATIAL_INPUT_MALFORMED
    assert not result.batches


@pytest.mark.parametrize("name", [["values"], {"a": 1}, 7, None])
def test_unhashable_or_nonstring_array_name_is_source_unavailable(name):
    prepared, profile, addressed, map_record = _fixture()
    metadata = dict(addressed.metadata)
    binding = {**metadata["bindings"][0], "value": name}
    metadata["bindings"] = [binding]
    result = StudyComposer(prepared, map_record).add(
        "cartilage", 0, 0, replace(addressed, metadata=metadata), profile
    )
    assert result.code is CompositionCode.MEASUREMENT_SOURCE_UNAVAILABLE
    assert not result.batches


def test_nonjson_descriptor_is_source_unavailable():
    prepared, profile, addressed, map_record = _fixture()
    metadata = dict(addressed.metadata)
    refs = {k: dict(v) for k, v in metadata["source_refs"].items()}
    refs["values"]["extra"] = object()
    metadata["source_refs"] = refs
    result = StudyComposer(prepared, map_record).add(
        "cartilage", 0, 0, replace(addressed, metadata=metadata), profile
    )
    assert result.code is CompositionCode.MEASUREMENT_SOURCE_UNAVAILABLE


def test_valid_source_identity_is_stable_across_adds():
    prepared, profile, addressed, map_record = _fixture()
    composer = StudyComposer(prepared, map_record)
    first = composer.add("cartilage", 0, 0, addressed, profile)
    second = composer.add("cartilage", 0, 1, addressed, profile)
    assert first.code is CompositionCode.OK and second.code is CompositionCode.OK
    ids = {b.measurement_source_identity for b in first.batches + second.batches}
    assert len(ids) == 1
    assert len(next(iter(ids))) == 64
