from types import SimpleNamespace

import numpy as np

from knee.collapse.physical import PlaneFrame
from knee.collapse.squint_stack import SquintStack
from scripts import run_interiors

FRAME = PlaneFrame.from_dicom(
    (0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0, 1.0, 0.0), (1.0, 1.0)
)


def bounds_grid(size=10, extent=50):
    axis = np.asarray(
        [[start, min(start + size, extent)] for start in range(0, extent, size)],
        dtype=np.int64,
    )
    bounds = np.empty((len(axis), len(axis), 4), dtype=np.int64)
    for row, (r0, r1) in enumerate(axis):
        for col, (c0, c1) in enumerate(axis):
            bounds[row, col] = r0, r1, c0, c1
    return bounds


def series_fixture(depth=3):
    plane = np.zeros((50, 50), dtype=np.float64)
    plane[20:30, 20:30] = 100.0
    volume = np.stack([plane.copy() for _ in range(depth)])
    row = SimpleNamespace(
        series_uid="scope-test-series", fat_suppression="0", fluid_sensitive="0"
    )
    slices = tuple(
        SimpleNamespace(
            header=SimpleNamespace(Laterality="R"),
            path=SimpleNamespace(name=f"slice-{z}.dcm"),
        )
        for z in range(depth)
    )
    return SimpleNamespace(
        row=row, volume=volume, geometry=object(), slices=slices
    ), plane


def squint_stack(series, *, coverage=None, bounds=None, code="present", why=""):
    depth = series.volume.shape[0]
    bounds = bounds_grid() if bounds is None else bounds
    if code != "present":
        bounds = np.empty((0, 0, 4), dtype=np.int64)
        maximum = np.empty((0, 0, 0), dtype=np.float64)
        coverage = np.empty((0, 0, 0), dtype=np.float64)
        median = minimum = centres = np.empty((0, 0, 0), dtype=np.float64)
        centres = np.empty((0, 0, 0, 3), dtype=np.float64)
        tile_shape = (0, 0)
    else:
        maximum = np.zeros((depth, *bounds.shape[:2]), dtype=np.float64)
        maximum[:, 2, 2] = 100.0
        coverage = np.ones_like(maximum) if coverage is None else coverage
        median, minimum = maximum.copy(), maximum.copy()
        centres = np.zeros((*maximum.shape, 3), dtype=np.float64)
        tile_shape = (10, 10)
    return SquintStack(
        series.row.series_uid,
        code,
        why,
        run_interiors.SQUINT_TILE_MM,
        tile_shape,
        bounds,
        median,
        minimum,
        maximum,
        coverage,
        centres,
    )


def install_driver_stubs(monkeypatch, stack, calls):
    monkeypatch.setattr(run_interiors, "plane_frame", lambda series, z: FRAME)
    monkeypatch.setattr(run_interiors, "background_split", lambda values: 50.0)

    def read_stack(series, tile_mm, frame_at, finite):
        calls.append((series.row.series_uid, tile_mm))
        return stack

    monkeypatch.setattr(run_interiors, "read_squint_stack", read_stack)

    def name_plane(series, index, plane, frame, split, knee, *, borders):
        lens = run_interiors.lens_of(
            series, index, plane, frame, split, borders=borders
        )
        return (
            {"background_split": split, "interiors": lens[2], "assignments": {}},
            {
                "b1_dark": lens[1].dark,
                "b1_available": lens[1].available,
                "b1_distance_mm": lens[1].distance_mm,
                "b1_markers": lens[1].markers,
                "b1_labels": lens[1].labels,
            },
            object(),
        )

    monkeypatch.setattr(run_interiors, "name_plane", name_plane)


def run_measure(monkeypatch, series, drawn, calls, stack):
    install_driver_stubs(monkeypatch, stack, calls)
    with run_interiors.recording(), run_interiors.computing():
        measured = run_interiors.measure(series, drawn)
        assert not isinstance(measured, str)
        other_z = len(series.volume) - 1
        assert run_interiors.squint_of(series) is measured.stack
        assert len(run_interiors.lens_scopes_of(series, 50.0)) == len(series.volume)
        run_interiors.lens_of(
            series,
            other_z,
            series.volume[other_z],
            FRAME,
            50.0,
        )
        assert len(calls) == 1
        return measured


def test_measure_and_lens_of_share_one_squint_and_use_scope_in_core(monkeypatch):
    series, _ = series_fixture()
    stack = squint_stack(series)
    calls = []
    measured = run_measure(monkeypatch, series, False, calls, stack)

    assert measured.stack is stack
    assert measured.arrays["lens_scope_window_rc"][1].tolist() == [10, 40, 10, 40]
    assert measured.arrays["lens_scope_in_scope_tiles"].shape == (3, 5, 5)
    assert measured.arrays["lens_scope_window_rc"].tolist() == [[10, 40, 10, 40]] * 3
    assert measured.arrays["lens_scope_in_scope_tile_count"].tolist() == [1, 1, 1]
    assert measured.record["lens_scope"]["method"] == run_interiors.LENS_SCOPE_METHOD
    assert measured.record["interiors"]["scope_code"] == "bounded_scope"
    assert measured.arrays["b1_distance_mm"][20:30, 20:30].max() > 0
    assert not measured.arrays["b1_distance_mm"][:10].any()
    assert not measured.arrays["b1_markers"][:10].any()
    assert not measured.arrays["b1_labels"][:10].any()
    assert len(calls) == 1


def test_drawn_and_undrawn_middle_lens_share_scoped_measurements(monkeypatch):
    series, _ = series_fixture()
    stack = squint_stack(series)
    plain = run_measure(monkeypatch, series, False, [], stack)
    drawn = run_measure(monkeypatch, series, True, [], stack)
    for name in (
        "b1_dark",
        "b1_available",
        "b1_distance_mm",
        "b1_markers",
        "b1_labels",
    ):
        np.testing.assert_array_equal(plain.arrays[name], drawn.arrays[name])
    assert (
        plain.record["interiors"]["scope_window_rc"]
        == drawn.record["interiors"]["scope_window_rc"]
    )
    assert "edge_counts" not in plain.record["interiors"]
    assert "edge_counts" in drawn.record["interiors"]


def test_unknown_coverage_stays_in_scope_through_measure(monkeypatch):
    series, _ = series_fixture()
    coverage = np.ones((3, 5, 5), dtype=np.float64)
    coverage[:, 0, 0] = np.nan
    stack = squint_stack(series, coverage=coverage)
    calls = []
    measured = run_measure(monkeypatch, series, False, calls, stack)

    assert measured.arrays["lens_scope_in_scope_tiles"][1, 0, 0]
    assert measured.arrays["lens_scope_window_rc"][1].tolist() == [0, 40, 0, 40]
    assert measured.record["interiors"]["scope_code"] == "bounded_scope"


def test_gapped_bounds_and_unavailable_squint_take_named_full_frame(monkeypatch):
    series, _ = series_fixture()
    gap_bounds = bounds_grid()
    row_bounds = np.asarray([[0, 8], [10, 18], [20, 28], [30, 38], [40, 50]])
    for row, (r0, r1) in enumerate(row_bounds):
        gap_bounds[row, :, 0] = r0
        gap_bounds[row, :, 1] = r1
    calls = []
    gap_measured = run_measure(
        monkeypatch, series, False, calls, squint_stack(series, bounds=gap_bounds)
    )
    assert gap_measured.arrays["lens_scope_in_scope_tiles"][1, 2, 2]
    assert gap_measured.arrays["lens_scope_window_rc"][1].tolist() == [0, 50, 0, 50]
    assert (
        gap_measured.arrays["lens_scope_codes"][1]
        == "full_frame_tile_bounds_incomplete"
    )

    calls = []
    unavailable = squint_stack(
        series,
        code="geometry_unreadable",
        why="slice frame unavailable",
    )
    unavailable_measured = run_measure(monkeypatch, series, False, calls, unavailable)
    assert unavailable_measured.arrays["lens_scope_window_rc"][1].tolist() == [
        0,
        50,
        0,
        50,
    ]
    assert (
        unavailable_measured.arrays["lens_scope_codes"][1]
        == "full_frame_squint_unavailable"
    )
    assert (
        unavailable_measured.record["lens_scope"]["reasons"]
        == ["slice frame unavailable"] * 3
    )


def test_malformed_slice_keeps_grid_shape_and_full_frame_fallback_in_measure(
    monkeypatch,
):
    series, _ = series_fixture()
    coverage = np.ones((3, 5, 5), dtype=np.float64)
    coverage[1, 2, 2] = np.inf
    stack = squint_stack(series, coverage=coverage)
    measured = run_measure(monkeypatch, series, False, [], stack)
    assert measured.arrays["lens_scope_in_scope_tiles"][1].shape == (5, 5)
    assert measured.arrays["lens_scope_in_scope_tiles"][1].all()
    assert measured.arrays["lens_scope_in_scope_tile_count"][1] == 25
    assert measured.arrays["lens_scope_window_rc"][1].tolist() == [0, 50, 0, 50]
    assert measured.arrays["lens_scope_codes"][1] == "full_frame_squint_unavailable"
    assert "coverage" in measured.arrays["lens_scope_reasons"][1]
    assert measured.arrays["lens_scope_in_scope_tiles"].shape == (3, 5, 5)
    assert measured.arrays["lens_scope_in_scope_tiles"][1].all()
    assert measured.arrays["lens_scope_window_rc"][1].tolist() == [0, 50, 0, 50]
    assert measured.arrays["lens_scope_in_scope_tile_count"][1] == 25
    assert measured.arrays["lens_scope_codes"][1] == "full_frame_squint_unavailable"
    assert "coverage" in measured.arrays["lens_scope_reasons"][1]
