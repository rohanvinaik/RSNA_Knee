"""Intent tests for the v4 detrend (low-frequency nuisance removal).

The scale-separation contract: a whole-region offset (protocol residue) is
TREND and must vanish; a lesion-scale blob is SIGNAL and must survive.
"""

import numpy as np

from RSNA_Knee.platonic_reference import detrend_diff


def _mask(shape=(2, 64, 64)):
    return np.ones(shape, dtype=bool)


def test_constant_offset_is_removed():
    diff = np.full((2, 64, 64), 0.5)
    out = detrend_diff(diff, _mask(), spatial_sigma=16.0)
    assert np.abs(out).max() < 0.05


def test_lesion_scale_blob_survives():
    diff = np.zeros((1, 64, 64))
    yy, xx = np.mgrid[0:64, 0:64]
    blob = np.exp(-((yy - 32) ** 2 + (xx - 32) ** 2) / (2 * 3.0**2))
    diff[0] = blob
    out = detrend_diff(diff, _mask((1, 64, 64)), spatial_sigma=16.0)
    # the blob's peak survives detrending nearly intact
    assert out[0, 32, 32] > 0.8 * blob[32, 32]


def test_offset_plus_blob_keeps_only_blob():
    diff = np.zeros((1, 64, 64))
    yy, xx = np.mgrid[0:64, 0:64]
    blob = np.exp(-((yy - 20) ** 2 + (xx - 40) ** 2) / (2 * 3.0**2))
    diff[0] = 0.6 + blob  # regional offset + lesion
    out = detrend_diff(diff, _mask((1, 64, 64)), spatial_sigma=16.0)
    assert out[0, 20, 40] > 0.7  # lesion peak survives
    far = out[0, 55, 10]
    assert abs(far) < 0.1  # offset removed away from the lesion


def test_off_knee_cells_are_zero():
    diff = np.full((1, 32, 32), 1.0)
    knee = np.zeros((1, 32, 32), dtype=bool)
    knee[0, 8:24, 8:24] = True
    out = detrend_diff(diff, knee, spatial_sigma=8.0)
    assert np.all(out[~knee] == 0.0)
