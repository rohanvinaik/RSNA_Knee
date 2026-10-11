"""Intent tests for source-linked conversations between same-knee readings."""

from dataclasses import replace

import numpy as np
import pytest

from knee.collapse import conversation
from knee.collapse.analysis import SeriesMeasurement
from knee.collapse.conversation import (
    ConversationInput,
    converse,
    exchange,
    selected_runs,
    subdivide,
)
from knee.collapse.interiors import TRACE_CODES, InteriorReading
from knee.collapse.physical import PlaneFrame
from knee.collapse.profiles import ProfileReading

OFFSETS = np.array([-2.0, -1.0, 0.0, 1.0, 2.0])


def _profile(values, *, valid=None, offsets=OFFSETS) -> ProfileReading:
    values = np.asarray(values, dtype=np.float64)
    if values.ndim == 1:
        values = values[None, :]
    mask = (
        np.ones(values.shape, dtype=bool)
        if valid is None
        else np.asarray(valid, dtype=bool)
    )
    if mask.ndim == 1:
        mask = mask[None, :]
    return ProfileReading(
        samples=values,
        valid=mask,
        slopes=np.full((len(values), max(0, len(offsets) - 1)), np.nan),
        distances_mm=np.asarray(offsets, dtype=np.float64),
        support_code="complete_support",
        support_codes=tuple("complete_support" for _ in values),
        requested_backend="reference",
        effective_backend="reference",
    )


def _measurement(
    uid: str,
    plane: np.ndarray,
    *,
    edge_rows: tuple[int, ...] = (3,),
    point_column: float = 3.5,
    source_band: tuple[float, float] = (-0.2, 0.2),
    spacing: tuple[float, float] = (1.0, 1.0),
    origin: tuple[float, float, float] = (0.0, 0.0, 0.0),
    thickness: float | None = 1.0,
) -> SeriesMeasurement:
    frame = PlaneFrame.from_dicom(
        origin,
        (1.0, 0.0, 0.0, 0.0, 1.0, 0.0),
        spacing,
    )
    points = np.column_stack(
        (np.asarray(edge_rows, dtype=np.float64), np.full(len(edge_rows), point_column))
    )
    count = len(points)
    labels = np.ones(plane.shape, dtype=np.int32)
    zeros = np.zeros(plane.shape, dtype=bool)
    ones = np.ones(plane.shape, dtype=bool)
    interior_profiles = _profile(
        np.tile((5.0, 0.0, 5.0), (count, 1)), offsets=(-1.0, 0.0, 1.0)
    )
    interiors = InteriorReading(
        code="measured",
        dark=zeros,
        available=ones,
        distance_mm=np.zeros(plane.shape, dtype=np.float64),
        markers=np.zeros(plane.shape, dtype=np.int32),
        labels=labels,
        edge_points_rc=points,
        edge_normals_rc=np.tile((0.0, 1.0), (count, 1)),
        edge_regions=np.ones(count, dtype=np.int32),
        edge_kinds=np.ones(count, dtype=np.uint8),
        profiles=interior_profiles,
        band_low_mm=np.full(count, source_band[0]),
        band_high_mm=np.full(count, source_band[1]),
        trace_points_rc=points.copy(),
        trace_codes=np.full(count, TRACE_CODES["bracketed"], dtype=np.uint8),
        distance_error_bound_mm=0.0,
        distance_guard=np.zeros(plane.shape, dtype=np.uint8),
    )
    return SeriesMeasurement(
        code="measured",
        frame=frame,
        acquired_plane=plane,
        interiors=interiors,
        slice_thickness_mm=thickness,
    )


def _inputs(
    donor_measurement,
    recipient_measurement,
    *,
    donor_uid="donor",
    recipient_uid="recipient",
):
    return (
        ConversationInput(donor_uid, "axial", donor_measurement, 1.0),
        ConversationInput(recipient_uid, "axial", recipient_measurement, 1.0),
    )


def _install_profile(monkeypatch, values, *, valid=None):
    result = _profile(values, valid=valid)

    def sample(plane, points, normals, offsets, spacing, backend, *, metric_rc=None):
        rows = len(points)
        return replace(
            result,
            samples=np.tile(result.samples, (rows, 1)),
            valid=np.tile(result.valid, (rows, 1)),
            slopes=np.tile(result.slopes, (rows, 1)),
            distances_mm=np.asarray(offsets, dtype=np.float64),
        )

    monkeypatch.setattr(conversation, "sample_profiles", sample)


def test_donor_only_evidence_cuts_conditional_map_but_not_concurrent_map(
    monkeypatch,
) -> None:
    _install_profile(monkeypatch, np.full(5, 5.0))
    donor_plane = np.full((9, 7), 5.0)
    recipient_plane = np.full((9, 7), 5.0)
    donor = _measurement("donor", donor_plane, edge_rows=tuple(range(9)))
    recipient = _measurement("recipient", recipient_plane, edge_rows=())
    assert donor.interiors is not None and recipient.interiors is not None
    source_before = donor.interiors.labels.copy()
    recipient_before = recipient.interiors.labels.copy()

    result = converse(_inputs(donor, recipient), OFFSETS, backend="reference")
    recipient_result = result[1]
    assert recipient_result.exchanges[0].code == "measured"
    assert np.all(
        recipient_result.exchanges[0].trace_codes
        == conversation.EXCHANGE_CODES["peer_only"]
    )
    assert not np.any(recipient_result.concurrent_barrier)
    assert np.any(recipient_result.conditional_barrier)
    assert (
        len(
            np.unique(
                recipient_result.conditional_labels[
                    recipient_result.conditional_labels > 0
                ]
            )
        )
        == 2
    )
    np.testing.assert_array_equal(recipient.interiors.labels, recipient_before)
    np.testing.assert_array_equal(donor.interiors.labels, source_before)


def test_native_matching_boundary_contributes_to_both_readings(monkeypatch) -> None:
    values = np.array([5.0, 5.0, 0.0, 5.0, 5.0])
    _install_profile(monkeypatch, values)
    donor = _measurement("donor", np.full((7, 7), 5.0), edge_rows=tuple(range(7)))
    recipient = _measurement("recipient", np.full((7, 7), 5.0), edge_rows=())

    result = converse(_inputs(donor, recipient), OFFSETS)
    recipient_result = result[1]
    exchange_result = recipient_result.exchanges[0]
    assert np.all(
        exchange_result.trace_codes == conversation.EXCHANGE_CODES["concurrent"]
    )
    np.testing.assert_array_equal(
        recipient_result.concurrent_barrier, recipient_result.conditional_barrier
    )
    assert np.any(recipient_result.concurrent_barrier)


@pytest.mark.parametrize(
    ("values", "band", "expected_code"),
    [
        ([0, 5, 0, 5, 0], (-0.5, 0.5), "concurrent"),
        ([5, 0, 5, 0, 5], (-2.0, 2.0), "native_multiple"),
        ([0, 5, 5, 5, 0], (-2.0, 2.0), "native_open"),
        ([5, 5, 5, 5, 5], (-0.5, 0.5), "peer_only"),
    ],
)
def test_native_run_relation_keeps_disjoint_multiple_open_and_empty_distinct(
    values, band, expected_code
) -> None:
    profiles = _profile(values)
    runs, bounded, opened, low, high = selected_runs(
        profiles, 1.0, np.array([band[0]]), np.array([band[1]])
    )
    expected = {
        "concurrent": (3, 1, 0),
        "native_multiple": (2, 2, 0),
        "native_open": (2, 0, 2),
        "peer_only": (0, 0, 0),
    }[expected_code]
    assert (int(runs[0]), int(bounded[0]), int(opened[0])) == expected
    if expected_code == "concurrent":
        assert low[0] == pytest.approx(-0.5)
        assert high[0] == pytest.approx(0.5)
    else:
        assert np.isnan(low[0]) and np.isnan(high[0])


def test_missing_native_samples_remain_missing_even_with_no_dark_run(
    monkeypatch,
) -> None:
    valid = np.array([True, False, True, True, True])
    _install_profile(monkeypatch, np.full(5, 5.0), valid=valid)
    donor = _measurement("donor", np.full((7, 7), 5.0))
    recipient = _measurement("recipient", np.full((7, 7), 5.0), edge_rows=())

    record = exchange(
        ConversationInput("donor", "axial", donor, 1.0),
        ConversationInput("recipient", "axial", recipient, 1.0),
        OFFSETS,
        "reference",
    )
    assert record.trace_codes[0] == conversation.EXCHANGE_CODES["native_missing"]
    assert record.profiles is not None and not record.profiles.valid.all()


def test_same_orientation_pairs_are_ordered_and_do_not_borrow_derived_records(
    monkeypatch,
) -> None:
    _install_profile(monkeypatch, np.full(5, 5.0))
    measurements = tuple(
        _measurement(uid, np.full((7, 7), 5.0), edge_rows=(row,))
        for uid, row in (("a", 1), ("b", 3), ("c", 5))
    )
    items = tuple(
        ConversationInput(uid, "axial", measurement, 1.0)
        for uid, measurement in zip(("a", "b", "c"), measurements, strict=True)
    )

    records = converse(items, OFFSETS)
    assert [
        tuple(exchange.donor_uid for exchange in record.exchanges) for record in records
    ] == [("b", "c"), ("a", "c"), ("a", "b")]
    for record in records:
        for exchange_record in record.exchanges:
            donor_index = "abc".index(exchange_record.donor_uid)
            donor_interiors = measurements[donor_index].interiors
            assert donor_interiors is not None
            np.testing.assert_array_equal(exchange_record.source_edge_indices, [0])
            np.testing.assert_array_equal(
                exchange_record.source_regions,
                donor_interiors.edge_regions,
            )


def test_different_orientation_has_no_exchange() -> None:
    measurement = _measurement("one", np.zeros((2, 4)), edge_rows=())
    records = converse(
        (
            ConversationInput("axial", "axial", measurement, 1.0),
            ConversationInput("coronal", "coronal", measurement, 1.0),
        ),
        OFFSETS,
    )
    assert [record.code for record in records] == ["solitary", "solitary"]
    assert all(record.exchanges == () for record in records)
    assert records[0].concurrent_barrier.shape == (2, 4)


def test_empty_plane_and_empty_subdivision_are_retained() -> None:
    empty_labels = np.empty((0, 4), dtype=np.int32)
    empty_barrier = np.empty((0, 4), dtype=bool)
    refined, parents = subdivide(empty_labels, empty_barrier)
    assert refined.shape == (0, 4)
    assert refined.dtype == np.int32
    assert parents.tolist() == [0]
    assert not refined.flags.writeable and not parents.flags.writeable

    measurement = _measurement("empty", np.empty((0, 4)), edge_rows=())
    records = converse(
        (ConversationInput("empty", "axial", measurement, 1.0),), OFFSETS
    )
    assert records[0].code == "solitary"
    assert records[0].concurrent_barrier.shape == (0, 4)
    assert records[0].conditional_labels.shape == (0, 4)


def test_real_native_sampler_reads_donor_band_against_bright_recipient() -> None:
    donor = _measurement("donor", np.full((9, 7), 5.0), edge_rows=tuple(range(9)))
    recipient = _measurement("recipient", np.full((9, 7), 5.0), edge_rows=())
    assert donor.interiors is not None and recipient.interiors is not None
    original_labels = recipient.interiors.labels.copy()

    result = converse(_inputs(donor, recipient), OFFSETS, backend="reference")[1]

    exchange_record = result.exchanges[0]
    assert exchange_record.profiles is not None
    assert exchange_record.profiles.valid.all()
    assert np.all(
        exchange_record.trace_codes == conversation.EXCHANGE_CODES["peer_only"]
    )
    assert not np.any(result.concurrent_barrier)
    assert np.any(result.conditional_barrier)
    assert len(np.unique(result.conditional_labels[result.conditional_labels > 0])) == 2
    np.testing.assert_array_equal(recipient.interiors.labels, original_labels)


@pytest.mark.parametrize("recipient", [None, "nan_split"])
def test_unavailable_recipient_retains_named_outcome(recipient) -> None:
    donor = _measurement("donor", np.full((7, 7), 5.0))
    recipient_measurement = (
        None if recipient is None else _measurement("recipient", np.full((7, 7), 5.0))
    )
    recipient_input = ConversationInput(
        "recipient",
        "axial",
        recipient_measurement,
        float("nan") if recipient == "nan_split" else 1.0,
    )
    record = exchange(
        ConversationInput("donor", "axial", donor, 1.0),
        recipient_input,
        OFFSETS,
        "reference",
    )
    assert record.code == "recipient_unavailable"
    assert record.concurrent_barrier.shape == (
        (0, 0) if recipient_measurement is None else (7, 7)
    )


@pytest.mark.parametrize(
    ("origin", "thickness", "expected"),
    [
        ((0.0, 0.0, 1.0), 0.5, "outside_slab"),
        ((0.0, 0.0, 1.0), None, "slab_support_unknown"),
    ],
)
def test_slab_support_uses_acquired_thickness_and_names_unknown(
    monkeypatch, origin, thickness, expected
) -> None:
    _install_profile(monkeypatch, np.full(5, 5.0))
    donor = _measurement("donor", np.full((7, 7), 5.0))
    recipient = _measurement(
        "recipient", np.full((7, 7), 5.0), origin=origin, thickness=thickness
    )
    record = exchange(
        ConversationInput("donor", "axial", donor, 1.0),
        ConversationInput("recipient", "axial", recipient, 1.0),
        OFFSETS,
        "reference",
    )
    assert np.all(record.coverage_codes == conversation.COVERAGE[expected])
    assert record.code == "measured"
    assert not np.any(record.conditional_barrier)


def test_physical_frame_transform_respects_unequal_native_spacing(monkeypatch) -> None:
    _install_profile(monkeypatch, np.full(5, 5.0))
    donor = _measurement(
        "donor",
        np.full((8, 8), 5.0),
        edge_rows=(2,),
        point_column=3.5,
        spacing=(2.0, 1.0),
    )
    recipient = _measurement(
        "recipient", np.full((8, 8), 5.0), edge_rows=(), spacing=(1.0, 2.0)
    )
    record = exchange(
        ConversationInput("donor", "axial", donor, 1.0),
        ConversationInput("recipient", "axial", recipient, 1.0),
        OFFSETS,
        "reference",
    )
    np.testing.assert_allclose(record.points_rc, [[4.0, 1.75]], atol=1e-12)


def test_subdivision_preserves_original_parent_and_barrier_places() -> None:
    labels = np.zeros((7, 7), dtype=np.int32)
    labels[:, 1:6] = 4
    barrier = np.zeros(labels.shape, dtype=bool)
    barrier[:, 3] = True
    before = labels.copy()

    refined, parents = subdivide(labels, barrier)
    np.testing.assert_array_equal(labels, before)
    np.testing.assert_array_equal(refined[:, 3], 0)
    assert np.all(refined[:, 2] > 0) and np.all(refined[:, 4] > 0)
    assert refined[3, 2] != refined[3, 4]
    for child in np.unique(refined[refined > 0]):
        assert parents[child] == 4
    assert not refined.flags.writeable and not parents.flags.writeable


def test_exchange_outputs_and_original_maps_are_immutable(monkeypatch) -> None:
    _install_profile(monkeypatch, np.full(5, 5.0))
    donor = _measurement("donor", np.full((7, 7), 5.0))
    recipient = _measurement("recipient", np.full((7, 7), 5.0), edge_rows=())
    assert recipient.interiors is not None
    original = recipient.interiors.labels.copy()
    result = converse(_inputs(donor, recipient), OFFSETS)[1]
    np.testing.assert_array_equal(recipient.interiors.labels, original)
    for value in (
        result.concurrent_barrier,
        result.conditional_barrier,
        result.concurrent_labels,
        result.conditional_labels,
        result.concurrent_parents,
        result.conditional_parents,
        result.exchanges[0].points_rc,
        result.exchanges[0].conditional_barrier,
    ):
        assert not value.flags.writeable
