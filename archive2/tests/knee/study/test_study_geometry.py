"""Slice geometry from tags as stored (knee.study.geometry): every reading says which zero it found, and the normal
is the right-handed unit normal of any orthonormal orientation."""

from __future__ import annotations

import numpy as np
from hypothesis import assume, given
from hypothesis import strategies as st
from pydicom.dataset import Dataset

from knee.study.geometry import (
    along,
    decimals,
    orientation_of,
    position_of,
    slice_normal,
    spacing_of,
)

component = st.floats(min_value=-1.0, max_value=1.0, allow_nan=False)
vector = st.tuples(component, component, component)
AXIAL = ["1", "0", "0", "0", "1", "0"]


def header(**tags: object) -> Dataset:
    ds = Dataset()
    for keyword, value in tags.items():
        setattr(ds, keyword, value)
    return ds


def test_present_tags_are_read_as_float64() -> None:
    ds = header(ImagePositionPatient=["1.5", "-2", "3.25"], PixelSpacing=["0.4", "0.6"])
    status, position = position_of(ds)
    assert status == "present" and position is not None
    assert position.dtype == np.float64 and position.tolist() == [1.5, -2.0, 3.25]
    status, spacing = spacing_of(ds)
    assert status == "present" and spacing is not None
    assert spacing.tolist() == [0.4, 0.6]


def test_an_absent_tag_is_absent() -> None:
    assert position_of(header()) == ("absent", None)
    assert orientation_of(header()) == ("absent", None)


def test_a_tag_with_no_value_is_empty() -> None:
    assert position_of(header(ImagePositionPatient="")) == ("empty", None)


def test_a_wrongly_sized_tag_is_malformed() -> None:
    assert spacing_of(header(PixelSpacing=["0.5"])) == ("malformed", None)
    ds = header(PixelSpacing=["0.5", "0.5", "0.5"])
    assert decimals(ds, "PixelSpacing", 2) == ("malformed", None)


def test_a_degenerate_orientation_is_degenerate() -> None:
    parallel = header(ImageOrientationPatient=["1", "0", "0", "1", "0", "0"])
    zero_row = header(ImageOrientationPatient=["0", "0", "0", "0", "1", "0"])
    assert orientation_of(parallel) == ("degenerate", None)
    assert orientation_of(zero_row) == ("degenerate", None)


def test_an_axial_slice_faces_plus_z() -> None:
    status, orientation = orientation_of(header(ImageOrientationPatient=AXIAL))
    assert status == "present" and orientation is not None
    assert slice_normal(orientation).tolist() == [0.0, 0.0, 1.0]


@given(vector, vector)
def test_the_normal_is_unit_orthogonal_and_right_handed(
    a: tuple[float, ...], b: tuple[float, ...]
) -> None:
    row = np.array(a)
    assume(np.linalg.norm(row) > 1e-3)
    row = row / np.linalg.norm(row)
    column = np.array(b) - np.dot(b, row) * row
    assume(np.linalg.norm(column) > 1e-3)
    column = column / np.linalg.norm(column)
    normal = slice_normal(np.concatenate([row, column]))
    assert np.isclose(np.linalg.norm(normal), 1.0)
    assert np.isclose(np.dot(normal, row), 0.0, atol=1e-9)
    assert np.isclose(np.dot(normal, column), 0.0, atol=1e-9)
    assert np.isclose(np.linalg.det(np.stack([row, column, normal])), 1.0)


@given(st.lists(vector, min_size=1, max_size=8))
def test_along_is_the_projection_on_the_normal(
    points: list[tuple[float, float, float]],
) -> None:
    positions = np.array(points) * 100.0
    normal = np.array([0.0, 0.6, 0.8])
    assert np.allclose(along(positions, normal), positions @ normal)
