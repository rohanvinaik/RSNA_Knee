"""A series is assembled whole (knee.study.series), on synthetic uncompressed slices: ordered along its normal,
stacked only when its files form one stack, and nothing dropped."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from conftest import pattern, write_slice

from knee.study.series import WALK_COUNT, read_series, walk_indices
from knee.study.tables import SeriesRow

ROW = SeriesRow("study", "series", "1", "1", "Axial")
ROWS, COLUMNS = 16, 24


def written(
    directory: Path, zs: list[str], dtype: type[np.integer] = np.uint16
) -> dict[str, np.ndarray]:
    """One slice per z, named so that file-name order is not z order; returns z -> its pixels."""
    directory.mkdir()
    out = {}
    for index, z in enumerate(zs):
        pixels = pattern(ROWS, COLUMNS, dtype, seed=index)
        write_slice(
            directory / f"{chr(ord('a') + index)}.dcm",
            pixels,
            position=("0", "0", z),
            instance=index + 1,
        )
        out[z] = pixels
    return out


@pytest.mark.parametrize("dtype", [np.uint16, np.int16])
def test_slices_are_stacked_in_order_along_the_normal_at_stored_fidelity(
    tmp_path: Path, dtype: type[np.integer]
) -> None:
    pixels = written(tmp_path / "s", ["3", "1", "0", "2"], dtype)
    series = read_series(tmp_path / "s", ROW)
    assert series.stack == ("stackable",)
    assert series.volume is not None and series.geometry is not None
    assert series.volume.shape == (4, ROWS, COLUMNS)
    assert series.volume.dtype == np.dtype(dtype)
    for k, z in enumerate(["0", "1", "2", "3"]):
        assert np.array_equal(series.volume[k], pixels[z])
        assert np.array_equal(series.slices[k].pixels, pixels[z])
    assert series.geometry.along_normal.tolist() == [0.0, 1.0, 2.0, 3.0]
    assert series.geometry.normal.tolist() == [0.0, 0.0, 1.0]
    assert series.geometry.spacing.tolist() == [[0.5, 0.5]] * 4
    assert series.geometry.orientation_spread == 0.0


def test_every_tag_is_kept_but_the_pixel_data_moves_to_pixels(tmp_path: Path) -> None:
    written(tmp_path / "s", ["0", "1"])
    first = read_series(tmp_path / "s", ROW).slices[0]
    assert first.header.EchoTime == "12.5"
    assert first.header.InstanceNumber == 1
    assert str(first.header.file_meta.TransferSyntaxUID) == "1.2.840.10008.1.2.1"
    assert "PixelData" not in first.header


def test_a_small_orientation_difference_is_measured_not_judged(tmp_path: Path) -> None:
    directory = tmp_path / "s"
    directory.mkdir()
    write_slice(
        directory / "a.dcm", pattern(ROWS, COLUMNS, np.uint16), position=("0", "0", "0")
    )
    tilted = ("1", "0", "0", "0", "0.99999", "0.0044721")
    write_slice(
        directory / "b.dcm",
        pattern(ROWS, COLUMNS, np.uint16),
        position=("0", "0", "1"),
        orientation=tilted,
    )
    series = read_series(directory, ROW)
    assert series.stack == ("stackable",)
    assert series.geometry is not None
    assert series.geometry.orientation_spread == pytest.approx(0.0044721)


def test_a_differently_shaped_slice_keeps_every_slice_but_no_volume(
    tmp_path: Path,
) -> None:
    written(tmp_path / "s", ["0", "1", "2"])
    write_slice(
        tmp_path / "s" / "z.dcm", pattern(8, 8, np.uint16), position=("0", "0", "3")
    )
    series = read_series(tmp_path / "s", ROW)
    assert series.stack == ("shape_varies",)
    assert series.volume is None
    assert len(series.slices) == 4


def test_a_repeated_position_is_named(tmp_path: Path) -> None:
    written(tmp_path / "s", ["0", "1", "1"])
    series = read_series(tmp_path / "s", ROW)
    assert series.stack == ("positions_repeat",)
    assert series.volume is None
    assert series.geometry is not None


def test_a_slice_without_a_position_leaves_file_name_order_and_no_geometry(
    tmp_path: Path,
) -> None:
    written(tmp_path / "s", ["2", "0"])
    write_slice(
        tmp_path / "s" / "c.dcm", pattern(ROWS, COLUMNS, np.uint16), position=None
    )
    series = read_series(tmp_path / "s", ROW)
    assert series.stack == ("position_absent",)
    assert series.geometry is None and series.volume is None
    assert [s.path.name for s in series.slices] == ["a.dcm", "b.dcm", "c.dcm"]


def test_a_malformed_position_is_named_malformed_not_absent(tmp_path: Path) -> None:
    written(tmp_path / "s", ["2", "0"])
    write_slice(
        tmp_path / "s" / "c.dcm", pattern(ROWS, COLUMNS, np.uint16), position=("0", "0")
    )
    series = read_series(tmp_path / "s", ROW)
    assert series.stack == ("position_malformed",)
    assert series.geometry is None and series.volume is None


def test_a_degenerate_orientation_is_named(tmp_path: Path) -> None:
    written(tmp_path / "s", ["0", "1"])
    flat = ("1", "0", "0", "1", "0", "0")
    write_slice(
        tmp_path / "s" / "c.dcm",
        pattern(ROWS, COLUMNS, np.uint16),
        position=("0", "0", "2"),
        orientation=flat,
    )
    series = read_series(tmp_path / "s", ROW)
    assert series.stack == ("orientation_degenerate",)
    assert series.geometry is None and series.volume is None


def test_a_missing_directory_and_an_empty_one(tmp_path: Path) -> None:
    assert read_series(tmp_path / "absent", ROW).stack == ("directory_missing",)
    (tmp_path / "empty").mkdir()
    empty = read_series(tmp_path / "empty", ROW)
    assert empty.stack == ("no_slices",)
    assert empty.slices == ()
    assert empty.slice_codes == () and empty.walk is None and empty.walk_indices == ()


# --------------------------------------------------------------------------------------------
# The stage's own retained picture content (task 6.9): per-slice codes and the walk.
# --------------------------------------------------------------------------------------------


def test_walk_indices_visit_both_ends_evenly_and_never_beyond_the_stack() -> None:
    assert walk_indices(0) == ()
    assert walk_indices(1) == (0,)
    assert walk_indices(3) == (0, 1, 2)
    assert walk_indices(8) == tuple(range(8))
    assert walk_indices(30) == (0, 4, 8, 12, 17, 21, 25, 29)
    assert walk_indices(5, 2) == (0, 4)
    assert walk_indices(5, 0) == ()
    assert walk_indices(-3) == ()
    for slices in range(40):
        indices = walk_indices(slices)
        assert len(indices) == min(slices, WALK_COUNT)
        assert all(0 <= index < slices for index in indices)
        assert list(indices) == sorted(set(indices))


def test_a_stacked_series_retains_its_walk_and_its_per_slice_codes(
    tmp_path: Path,
) -> None:
    pixels = written(tmp_path / "s", ["3", "1", "0", "2"])
    series = read_series(tmp_path / "s", ROW)
    assert series.slice_codes == ("decoded",) * 4
    assert series.walk_indices == (0, 1, 2, 3)
    assert series.walk is not None
    assert series.walk.shape == (4, ROWS, COLUMNS)
    assert series.walk.dtype == np.dtype(np.uint16)
    for k, z in enumerate(["0", "1", "2", "3"]):
        assert np.array_equal(series.walk[k], pixels[z])


def test_an_unstackable_series_keeps_its_slice_codes_and_no_walk(
    tmp_path: Path,
) -> None:
    written(tmp_path / "s", ["0", "1", "2"])
    write_slice(
        tmp_path / "s" / "z.dcm", pattern(8, 8, np.uint16), position=("0", "0", "3")
    )
    series = read_series(tmp_path / "s", ROW)
    assert series.volume is None and series.walk is None
    assert series.walk_indices == ()
    assert series.slice_codes == ("decoded",) * 4


def test_the_picture_walks_the_same_slices_the_stage_retains(tmp_path: Path) -> None:
    """One rule for which slices a walk visits: the adapter reads it from the stage."""
    from knee.pictures.study import panels

    written(tmp_path / "s", [str(z) for z in range(12)])
    series = read_series(tmp_path / "s", ROW)
    assert series.volume is not None and series.walk is not None
    frame = panels(series.volume, series.slice_codes, (0.5, 0.5), 1.0)
    assert frame.walk.shape[0] == len(series.walk_indices) == WALK_COUNT
    np.testing.assert_array_equal(frame.walk, series.walk.astype(np.float64))
