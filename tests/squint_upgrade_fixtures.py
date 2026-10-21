"""Small synthetic inputs shared by the squint-to-training upgrade lanes.

One series record shaped like ``read_study_squints`` output, without a native
``Series`` (lanes that need native pixels build a real DICOM study as
``tests/test_squint_profiles.py`` does). Its 3 x 8 x 8 tile grid, 20 x 20
native pixels per tile, holds:

* air: the outer ring of tiles (rows 0 and 7, columns 0 and 7);
* the leg's edge: row 1, columns 1-6, half air and half tissue in each tile;
* leg tissue everywhere else, brighter than the air;
* a dark body enclosed by the leg at rows 3-4, columns 3-4. It is as dark as
  much of the air but is leg: cortex, tendon and meniscus look like this.

The expected leg map and a teacher territory over the dark body come with it.
The codes and cutoffs are made by the production writer's own functions, over
every available tile as the v1 writer does, so a test can show what changes
when the cutoffs are taken over the leg alone.
"""

from __future__ import annotations

import numpy as np

from knee.collapse.squint_stack import SquintStack
from knee.diagnosis import squint_profiles as writer
from knee.diagnosis.squint_interfaces import (
    LEG_INSIDE,
    LEG_MAP_SCHEMA,
    LEG_MIXED,
    LEG_OUTSIDE,
    ROLE_CONTEXT,
    ROLE_OBJECT,
    ROLE_OUTSIDE_LEG,
    TERRITORY_SCHEMA,
)

STUDY_UID = "1.2.826.0.1.3680043.8.498.fixture.study"
SERIES_UID = "1.2.826.0.1.3680043.8.498.fixture.series"
VIEW = {"orientation": "Coronal", "fluid_sensitive": "1", "fat_suppression": "1"}
DEPTH, ROWS, COLS = 3, 8, 8
TILE_PX = 20
DARK_BODY = (slice(3, 5), slice(3, 5))


def _grids() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # A small deterministic spread inside each class, as real scans have, so
    # that no tile sits exactly on a tercile edge.
    spread = np.arange(DEPTH * ROWS * COLS, dtype=np.float64).reshape(DEPTH, ROWS, COLS)
    spread /= spread.size
    median = 100.0 + 150.0 * spread
    minimum = median - 70.0
    maximum = median + 100.0
    ring = np.zeros((ROWS, COLS), dtype=np.bool_)
    ring[0, :] = ring[-1, :] = ring[:, 0] = ring[:, -1] = True
    edge = np.zeros((ROWS, COLS), dtype=np.bool_)
    edge[1, 1:-1] = True
    dark = np.zeros((ROWS, COLS), dtype=np.bool_)
    dark[DARK_BODY] = True
    for z in range(DEPTH):
        median[z][ring] = 0.2 + 0.8 * spread[z][ring]
        minimum[z][ring] = 0.0
        maximum[z][ring] = 3.0
        median[z][edge] = 35.0 + 10.0 * spread[z][edge]
        minimum[z][edge] = 0.0
        maximum[z][edge] = 200.0
        median[z][dark] = 2.0 + spread[z][dark]
        minimum[z][dark] = 0.0
        maximum[z][dark] = 30.0
    return median, minimum, maximum


def series_record() -> dict:
    """One series record as ``read_study_squints`` returns it, minus ``native_series``."""
    median, minimum, maximum = _grids()
    coverage = np.ones_like(median)
    bounds = np.zeros((ROWS, COLS, 4), dtype=np.int64)
    centres = np.zeros((DEPTH, ROWS, COLS, 3), dtype=np.float64)
    for r in range(ROWS):
        for c in range(COLS):
            bounds[r, c] = (
                r * TILE_PX,
                (r + 1) * TILE_PX,
                c * TILE_PX,
                (c + 1) * TILE_PX,
            )
            for z in range(DEPTH):
                # Coronal: columns run patient left, rows run inferior, slices posterior.
                centres[z, r, c] = (c * 10.0 + 5.0, z * 3.0, -(r * 10.0 + 5.0))
    for array in (median, minimum, maximum, coverage, bounds, centres):
        array.flags.writeable = False
    stack = SquintStack(
        series_uid=SERIES_UID,
        code="present",
        why="fixture",
        tile_mm=10.0,
        tile_shape_rc=(TILE_PX, TILE_PX),
        bounds_rc=bounds,
        median=median,
        minimum=minimum,
        maximum=maximum,
        coverage=coverage,
        centres_lps=centres,
    )
    values = writer._metrics(stack)
    available = writer._metric_availability(stack, values)
    calibration, codes = writer._calibrate(values, available)
    source = {
        "api": "fixture",
        "study_uid": STUDY_UID,
        "series_uid": SERIES_UID,
        "tile_mm": 10.0,
        "procedure": writer._PROCEDURE,
        "geometry_status": "available",
        "calibration": calibration,
        "native_slice_paths": (),
    }
    return {
        "series_uid": SERIES_UID,
        "view": dict(VIEW),
        "shape": (DEPTH, ROWS * TILE_PX, COLS * TILE_PX),
        "geometry": None,
        "stack": stack,
        "metric_values": values,
        "metric_available": available,
        "metric_codes": codes,
        "calibration": calibration,
        "source": source,
        "native_series": None,
    }


def study_record() -> dict:
    """A one-series study as ``read_study_squints`` returns it."""
    return {
        "schema": "knee.squint-study/v1",
        "study_uid": STUDY_UID,
        "series": [series_record()],
        "work": {"series_count": 1},
    }


def expected_leg_map() -> dict:
    """The leg map the fixture's anatomy implies: ring outside, edge mixed, rest inside."""
    codes = np.full((DEPTH, ROWS, COLS), LEG_INSIDE, dtype=np.int8)
    share = np.ones((DEPTH, ROWS, COLS), dtype=np.float32)
    codes[:, 0, :] = codes[:, -1, :] = codes[:, :, 0] = codes[:, :, -1] = LEG_OUTSIDE
    share[codes == LEG_OUTSIDE] = 0.0
    codes[:, 1, 1:-1] = LEG_MIXED
    share[:, 1, 1:-1] = 0.5
    return {
        "schema": LEG_MAP_SCHEMA,
        "study_uid": STUDY_UID,
        "series_uid": SERIES_UID,
        "tile_mm": 10.0,
        "codes": codes,
        "leg_share": share,
        "rule": "fixture:expected",
        "provenance": {"fixture": True},
        "counts": {
            "inside": int(np.count_nonzero(codes == LEG_INSIDE)),
            "outside": int(np.count_nonzero(codes == LEG_OUTSIDE)),
            "mixed": int(np.count_nonzero(codes == LEG_MIXED)),
            "unknown": 0,
        },
    }


def teacher_territory(subject: str = "medial_meniscus") -> dict:
    """Teacher support over the dark body on slice 1, with one ring of context.

    The window reaches the leg's edge and the air at its top-left corner so that
    a writer must drop outside-leg places and keep mixed ones in scope.
    """
    window = [1, 2, 0, 6, 0, 6]
    roles = np.full((1, 6, 6), ROLE_CONTEXT, dtype=np.int8)
    share = np.full((1, 6, 6), np.nan, dtype=np.float32)
    roles[0, 0, :] = ROLE_OUTSIDE_LEG
    roles[0, :, 0] = ROLE_OUTSIDE_LEG
    roles[0, 3:5, 3:5] = ROLE_OBJECT
    share[0, 3:5, 3:5] = np.asarray([[0.25, 0.5], [0.75, 0.4]], dtype=np.float32)
    return {
        "schema": TERRITORY_SCHEMA,
        "study_uid": STUDY_UID,
        "series_uid": SERIES_UID,
        "subject": subject,
        "origin": "teacher_support",
        "tile_window": window,
        "roles": roles,
        "object_share": share,
        "native_support": None,
        "anchors": [],
        "relation": None,
        "key_planes": {
            "coronal": {"series_uid": SERIES_UID, "slice": 1, "outcome": "selected"}
        },
        "provenance": {"fixture": True},
    }
