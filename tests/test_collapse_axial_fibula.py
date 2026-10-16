"""The fibula's axial evidence: the slice whose slab holds most of its physical places, only the places
within the slab mapped onto it, the lens territory holding most of them read once per slice, and every
outcome named (tie, unavailable, empty target, missing geometry, no axial series), retained inside the
fibula's own record and arrays."""

from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest

from knee.collapse.physical import PlaneFrame
from knee.objects.interiors import InteriorRegions
from knee.telemetry import computing, recording
from scripts import run_interiors as run

SHAPE = (8, 8)
BASIS = np.array(
    [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]
)  # a row step is +x, a column step +y; normal +z
LABELS = np.zeros(SHAPE, dtype=np.int32)
LABELS[:4] = 1
LABELS[4:] = 2


def flat_stack(origins_z):
    return [PlaneFrame(np.array([0.0, 0.0, z]), BASIS, (1.0, 1.0)) for z in origins_z]


def pixels(rows_cols, z, shift=0.0, frame=None):
    """Scanner places on the pixels `rows_cols` of a slice at height z (or of `frame`), moved `shift` mm along its normal."""
    frame = frame or PlaneFrame(np.array([0.0, 0.0, z]), BASIS, (1.0, 1.0))
    return frame.to_patient(np.asarray(rows_cols, dtype=float)) + shift * frame.normal()


def axial(monkeypatch, frames, finite=True, thick=3.0, labels=LABELS):
    """An axial series over `frames`, its header and lens stood in for; returns it and the lens calls."""
    calls = []

    def lens(plane, *_, available):
        calls.append(1)
        zeros = np.zeros(plane.shape)
        return InteriorRegions(
            "measured",
            zeros.astype(bool),
            available,
            zeros,
            zeros.astype(np.int32),
            labels,
        )

    monkeypatch.setattr(run, "plane_frame", lambda series, z: frames[z])
    monkeypatch.setattr(
        run, "finite_of", lambda series: np.full((len(frames), *SHAPE), finite)
    )
    monkeypatch.setattr(run, "interior_regions", lens)
    series = SimpleNamespace(
        row=SimpleNamespace(series_uid="ax"),
        volume=[np.ones(SHAPE) for _ in frames],
        geometry=SimpleNamespace(position=[f.origin_lps for f in frames]),
        slice_thickness_mm=tuple(thick for _ in frames),
    )
    measured = SimpleNamespace(
        series=series,
        record={"view": ["Axial", "1", "1"], "background_split": 1.0},
        frame=frames[0],
    )
    return cast(run.Measured, measured), calls


def ask(measured, places):
    with computing(), recording():
        return run.fibula_axial(measured, places)


def test_the_slice_whose_slab_holds_most_places_is_read_and_off_slab_places_are_not_projected(
    monkeypatch,
):
    measured, calls = axial(monkeypatch, flat_stack([0, 3, 6, 9]))
    places = np.vstack([pixels([[1, 1], [1, 2], [2, 1]], 6.0), pixels([[6, 6]], 3.0)])
    got = ask(measured, places)
    assert not isinstance(got, str) and len(got) == 1 and len(calls) == 1
    read = got[0]
    assert read.slice_index == 2 and read.on_slab_points == 3 and read.tied_slices == ()
    assert read.code == "territory_holding_most" and read.label == 1
    assert read.target is not None and read.region is not None
    assert (
        read.target.sum() == 3 and not read.target[6, 6]
    )  # the slice-1 place is not projected
    assert (read.region == (LABELS == 1)).all() and read.off_plane_mm == 0.0


def test_the_places_centre_selects_the_slab_not_the_slab_holding_the_most_places(
    monkeypatch,
):
    # a long section: a plateau of counts, the most places at its two ends, its centre between
    measured, calls = axial(monkeypatch, flat_stack([0, 3, 6, 9]))
    places = np.vstack(
        [
            pixels([[1, 1], [1, 2], [2, 1], [2, 2]], 0.0),
            pixels([[1, 1], [1, 2]], 3.0),
            pixels([[1, 1], [1, 2], [2, 1], [2, 2]], 6.0),
        ]
    )
    got = ask(measured, places)
    assert not isinstance(got, str) and len(got) == 1 and len(calls) == 1
    assert got[0].slice_index == 1 and got[0].on_slab_points == 2
    assert got[0].tied_slices == ()


def test_two_source_views_mapping_to_one_target_plane_read_the_lens_once(monkeypatch):
    measured, calls = axial(monkeypatch, flat_stack([0, 3, 6, 9]))
    sagittal = pixels([[1, 1], [1, 2]], 6.0)
    coronal = pixels([[2, 2], [3, 3], [2, 3]], 6.2)
    with computing(), recording():
        first = run.fibula_axial(measured, sagittal)
        other = run.fibula_axial(measured, coronal)
        again = run.fibula_axial(measured, sagittal)
    assert not isinstance(first, str) and not isinstance(other, str)
    assert not isinstance(again, str)
    assert len(calls) == 1  # the plane's lens, once, for both views
    assert first[0].slice_index == other[0].slice_index == 2
    assert first[0].target is not None and other[0].target is not None
    assert first[0].target.sum() == 2 and other[0].target.sum() == 3
    assert (
        again[0].target is first[0].target
    )  # the same places: handed on, not made again
    assert other[0].off_plane_mm == pytest.approx(0.2)


def test_places_on_two_slabs_equally_name_each_slice_and_none_is_dropped(monkeypatch):
    measured, calls = axial(monkeypatch, flat_stack([0, 3, 6, 9]))
    got = ask(
        measured, pixels([[1, 1], [2, 2]], 1.5)
    )  # the slabs of slices 0 and 1 meet at 1.5
    assert not isinstance(got, str)
    assert [(r.slice_index, r.tied_slices) for r in got] == [(0, (1,)), (1, (0,))]
    assert len(calls) == 2


def test_territories_sharing_the_most_places_are_a_named_tie_and_none_is_chosen(
    monkeypatch,
):
    measured, _ = axial(monkeypatch, flat_stack([0, 3, 6, 9]))
    got = ask(measured, pixels([[1, 1], [2, 2], [5, 5], [6, 6]], 0.0))
    assert not isinstance(got, str)
    read = got[0]
    assert read.code == "tie" and read.tied_labels == (1, 2) and read.label is None
    assert read.hits == {1: 2, 2: 2}
    assert read.region is not None and not read.region.any()
    assert read.target is not None and read.target.sum() == 4  # the evidence is kept


def test_a_target_the_lens_never_saw_is_unavailable_not_empty(monkeypatch):
    measured, _ = axial(monkeypatch, flat_stack([0, 3, 6, 9]), finite=False)
    got = ask(measured, pixels([[1, 1], [2, 2]], 3.0))
    assert not isinstance(got, str)
    read = got[0]
    assert read.code == "unavailable" and read.target_pixels == 0 and read.hits == {}
    assert (
        read.target is not None and read.target.sum() == 2
    )  # where the places fall is kept
    assert read.region is not None and not read.region.any()


def test_a_target_on_no_territory_is_named_for_what_it_is(monkeypatch):
    bare = np.zeros(SHAPE, dtype=np.int32)
    measured, _ = axial(monkeypatch, flat_stack([0, 3]), labels=bare)
    got = ask(measured, pixels([[1, 1]], 0.0))
    assert not isinstance(got, str) and got[0].code == "no_territory_under_the_places"


def test_no_place_on_any_slab_reads_nothing_and_projects_nothing(monkeypatch):
    measured, calls = axial(monkeypatch, flat_stack([0, 3, 6, 9]))
    got = ask(measured, pixels([[1, 1], [2, 2]], 100.0))
    assert not isinstance(got, str) and len(got) == 1 and not calls
    read = got[0]
    assert read.code == "empty_target" and read.on_slab_points == 0
    assert read.slice_index == 3 and read.off_plane_mm == pytest.approx(91.0)
    assert read.labels is None and read.target is None and read.region is None


def test_a_reversed_oblique_stack_finds_the_slab_by_each_slices_own_plane(monkeypatch):
    tilt = np.deg2rad(30.0)
    basis = np.array([[1.0, 0.0], [0.0, np.cos(tilt)], [0.0, np.sin(tilt)]])
    normal = np.cross(basis[:, 0], basis[:, 1])
    # the highest slice first: index 0 lies furthest along the normal
    frames = [PlaneFrame(k * 3.0 * normal, basis, (1.0, 1.0)) for k in (3, 2, 1, 0)]
    measured, _ = axial(monkeypatch, frames)
    wanted = [[1, 1], [2, 1]]
    got = ask(measured, pixels(wanted, 0.0, shift=0.4, frame=frames[1]))
    assert not isinstance(got, str)
    read = got[0]
    assert read.slice_index == 1 and read.on_slab_points == 2 and read.tied_slices == ()
    expected = np.zeros(SHAPE, dtype=bool)
    expected[1, 1] = expected[2, 1] = True
    assert read.target is not None and (read.target == expected).all()
    assert read.off_plane_mm == pytest.approx(0.4)
    assert read.code == "territory_holding_most" and read.label == 1
    assert np.allclose(read.frame.normal(), frames[1].normal())


def test_a_series_that_cannot_place_a_slab_is_an_unknown_named_by_why(monkeypatch):
    places = pixels([[1, 1]], 0.0)
    measured, calls = axial(monkeypatch, flat_stack([0, 3]))
    series = measured.series
    unreadable = flat_stack([0, 3])
    monkeypatch.setattr(
        run,
        "plane_frame",
        lambda s, z: "geometry_unreadable: invalid_position" if z else unreadable[0],
    )
    assert ask(measured, places) == "geometry_unreadable: invalid_position"
    monkeypatch.setattr(run, "plane_frame", lambda s, z: unreadable[z])
    for change, why in (
        ({"volume": None}, "no_stacked_volume"),
        ({"geometry": None}, "geometry_unreadable"),
        ({"slice_thickness_mm": (3.0, None)}, "no_slice_thickness"),
        ({"slice_thickness_mm": ()}, "no_slice_thickness"),
        ({"slice_thickness_mm": (3.0,)}, "no_slice_thickness"),
    ):
        broken = SimpleNamespace(**{**vars(series), **change})
        assert (
            ask(SimpleNamespace(series=broken, record=measured.record), places) == why
        )  # type: ignore[arg-type]
    assert not calls


# -- through fibula_observations and the record ---------------------------------------------------


def found(physical, tmp_artifact="study/sg-fibula.npz"):
    source = PlaneFrame(
        np.array([5.0, 0.0, 0.0]),
        np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]),
        (1.0, 1.0),
    )
    arrays = {
        "a3_fibula_head_status": np.array([0], dtype=np.int8),
        "a3_fibula_detailed_slices": np.array([1], dtype=np.int32),
        "a3_fibula_other_plane_slices": np.empty(0, dtype=np.int32),
        "a3_fibula_pointer_runs": np.empty((0, 2), dtype=np.int32),
        "a3_fibula_pointer_run_confirmation": np.empty(0, dtype=np.int8),
        "a3_fibula_places_lps": physical,
    }
    record = {"series_uid": "sg", "slice_index": 1, "artifact": tmp_artifact}
    return run.FibulaFound(
        record, arrays, source, physical, physical, 5.0, "sg", 1, ((1, 4.0, 4),)
    )


def sagittal():
    return cast(
        run.Measured,
        SimpleNamespace(
            series=SimpleNamespace(row=SimpleNamespace(series_uid="sg")),
            record={"series_uid": "sg", "view": ["Sagittal", "0", "0"]},
        ),
    )


def test_the_axial_territory_is_a_native_reading_kept_in_the_fibulas_own_arrays(
    monkeypatch,
):
    measured, calls = axial(monkeypatch, flat_stack([0, 3, 6, 9]))
    fibula = found(pixels([[1, 1], [1, 2], [2, 1]], 6.0))
    own = sagittal()
    with computing(), recording():
        seen, unplaced = run.fibula_observations(
            own, fibula, None, None, [own, measured]
        )
    axial_obs = [o for o in seen if o.provenance == "native" and o.series_uid == "ax"]
    target = [o for o in seen if o.provenance == "projected"]
    assert len(axial_obs) == 1 and len(target) == 1 and len(calls) == 1
    got = axial_obs[0]
    assert (got.kind, got.code, got.slices, got.count) == (
        "reading",
        "territory_holding_most",
        (2,),
        3,
    )
    # the support is a boolean flat packed array: a label selects nothing in it, the row is
    # addressed by the offsets and shapes beside it, and the territory's number is in the
    # labelled array whose same slice the note names
    assert (got.artifact, got.row, got.label) == ("study/sg-fibula.npz", 0, None)
    assert got.support == "a3_fibula_axial_region"
    assert "a3_fibula_axial_offsets[0]:a3_fibula_axial_offsets[1]" in got.note
    assert "a3_fibula_axial_shapes[0]" in got.note and "number (1)" in got.note
    assert fibula.arrays["a3_fibula_axial_region"].dtype == bool
    assert fibula.arrays["a3_fibula_axial_labels"].dtype.kind in "iu"
    arrays = fibula.arrays
    assert arrays["a3_fibula_axial_slices"].tolist() == [2]
    shape, offsets = (
        arrays["a3_fibula_axial_shapes"][0],
        arrays["a3_fibula_axial_offsets"],
    )
    region = arrays["a3_fibula_axial_region"][offsets[0] : offsets[1]].reshape(shape)
    assert (region == (LABELS == 1)).all()
    assert arrays["a3_fibula_axial_target"].sum() == 3
    assert arrays["a3_fibula_axial_normal_lps"][0].tolist() == [0.0, 0.0, 1.0]
    assert arrays["a3_fibula_source_basis_lps"].shape == (3, 2)
    assert (
        arrays["a3_fibula_places_lps"] is fibula.physical
    )  # the source's places stay beside it
    entry = fibula.record["axial_evidence"][0]
    assert entry["row"] == 0 and entry["territory_hits"] == {"1": 3}
    assert not [u for u in unplaced if u.code == "no_axial_series"]


def test_no_axial_series_is_named_and_adds_no_work_or_arrays(monkeypatch):
    calls = []
    monkeypatch.setattr(run, "interior_regions", lambda *a, **k: calls.append(1))
    fibula = found(pixels([[1, 1]], 0.0))
    before = set(fibula.arrays)
    own = sagittal()
    _, unplaced = run.fibula_observations(own, fibula, None, None, [own])
    codes = [(u.provenance, u.series_uid, u.code) for u in unplaced]
    assert ("native", None, "no_axial_series") in codes
    assert set(fibula.arrays) == before and "axial_evidence" not in fibula.record
    assert not calls


def test_an_axial_series_without_geometry_is_a_native_unknown_not_an_absence(
    monkeypatch,
):
    measured, _ = axial(monkeypatch, flat_stack([0, 3]))
    measured.series.geometry = None
    fibula = found(pixels([[1, 1]], 0.0))
    own = sagittal()
    seen, unplaced = run.fibula_observations(own, fibula, None, None, [own, measured])
    assert ("native", "ax", "geometry_unreadable") in [
        (u.provenance, u.series_uid, u.code) for u in unplaced
    ]
    assert not [o for o in seen if o.provenance == "native" and o.series_uid == "ax"]
    assert "a3_fibula_axial_slices" not in fibula.arrays
