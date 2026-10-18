"""Tests for native white-body selection at retinacular source locations."""

import numpy as np

from knee.collapse.retinacula import closest_white_body, white_components


class _Frame:
    spacing_rc = np.array([0.5, 0.5])

    def to_patient(self, rc):
        points = np.asarray(rc, dtype=float)
        return np.column_stack(
            (points[:, 1] * 0.5, points[:, 0] * 0.5, np.zeros(len(points)))
        )


def _scene():
    white = np.zeros((40, 70), dtype=bool)
    white[10:22, 8:20] = True
    white[10:22, 40:52] = True
    labels, components = white_components(white, _Frame.spacing_rc)
    source = np.array([[15, 23], [16, 23]], dtype=np.int32)
    outward = np.tile(np.arange(70, dtype=float), (40, 1))
    return labels, components, source, outward


def test_unique_nearest_two_millimeter_body_is_returned_whole():
    labels, components, source, outward = _scene()
    body, core, detail = closest_white_body(
        labels, components, source, _Frame(), outward, require_inward=False
    )

    assert detail["status"] == "selected_nearest_native_white_body"
    assert detail["selected_component_id"] == 1
    assert np.array_equal(body, labels == 1)
    assert core.any()
    assert np.all(core <= body)


def test_equal_nearest_bodies_are_named_as_a_tie():
    white = np.zeros((40, 70), dtype=bool)
    white[10:22, 8:20] = True
    white[10:22, 40:52] = True
    labels, components = white_components(white, _Frame.spacing_rc)
    source = np.array([[15, 29], [15, 30]], dtype=np.int32)
    outward = np.tile(np.arange(70, dtype=float), (40, 1))

    body, core, detail = closest_white_body(
        labels, components, source, _Frame(), outward, require_inward=False
    )

    assert detail["status"] == "tied_nearest_native_white_bodies"
    assert not body.any()
    assert not core.any()


def test_coronal_component_must_be_on_the_inward_side_of_the_source():
    labels, components, source, outward = _scene()
    outward = np.tile(np.arange(40, dtype=float)[:, None], (1, 70))
    source[:, 0] = 8
    outward[source[:, 0], source[:, 1]] = 8.0

    body, core, detail = closest_white_body(
        labels, components, source, _Frame(), outward, require_inward=True
    )

    assert detail["status"] == "no_two_mm_body_in_anatomical_order"
    assert not body.any()
    assert not core.any()


def test_empty_white_image_has_no_native_body():
    white = np.zeros((40, 70), dtype=bool)
    labels, components = white_components(white, _Frame.spacing_rc)
    body, core, detail = closest_white_body(
        labels,
        components,
        np.array([[12, 12]], dtype=np.int32),
        _Frame(),
        np.zeros_like(white, dtype=float),
        require_inward=False,
    )

    assert detail["status"] == "no_native_white_body"
    assert not body.any()
    assert not core.any()
