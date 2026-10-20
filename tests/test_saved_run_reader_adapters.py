"""Saved-run artifact consumers use the real shared reader and close it after use."""

from __future__ import annotations

import importlib.util
import io
import json
import lzma
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent


def _script(name: str):
    path = ROOT / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_adapter_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write(path: Path, **arrays: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    np.savez(buffer, allow_pickle=False, **arrays)
    data = buffer.getvalue()
    path.write_bytes(lzma.compress(data) if path.name.endswith(".xz") else data)


@pytest.mark.parametrize("suffix", [".npz", ".npz.xz"])
def test_geometry_reads_and_releases_real_archive(tmp_path: Path, suffix: str) -> None:
    module = _script("slice_positions")
    centres = np.arange(48, dtype=float).reshape(4, 2, 2, 3)
    path = tmp_path / f"record{suffix}"
    _write(path, squint_centres_lps=centres)
    expected = module.stack_geometry(centres)
    actual = module.geometry(path)
    assert actual["n"] == expected["n"]
    assert actual["axis"] == expected["axis"]
    assert actual["reversed"] == expected["reversed"]
    assert actual["extent"] == expected["extent"]
    np.testing.assert_array_equal(actual["q"], expected["q"])


@pytest.mark.parametrize("suffix", [".npz", ".npz.xz"])
def test_section_mask_reads_the_addressed_saved_support(
    tmp_path: Path, suffix: str
) -> None:
    module = _script("key_points")
    support = np.array([[0, 1], [2, 0]], dtype=np.int16)
    run = tmp_path / "run"
    _write(run / f"record{suffix}", support=support)
    row = {
        "artifact": f"record{suffix}",
        "support": "support",
        "row": None,
        "label": 2,
    }
    actual = module.section_mask(row, run, tmp_path / "unused")
    assert actual is not None
    assert actual.tolist() == [[False, False], [True, False]]


def _draw_case(tmp_path: Path, module_name: str, records: list[dict], picture_check):
    module = _script(module_name)
    run = tmp_path / module_name
    run.mkdir()
    (run / "receipt.json").write_text(json.dumps({"records": records}))
    for record in records:
        _write(run / record["artifact"], probe=np.array([3, 7], dtype=np.int16))
    module._picture = picture_check
    if hasattr(module, "_records"):
        module._records = lambda receipt: receipt["records"]
    return module, run


@pytest.mark.parametrize(
    ("module_name", "record"),
    [
        (
            "object_bones",
            {
                "study_uid": "s",
                "series_uid": "series",
                "artifact": "s/a.npz",
                "bones": {"femur": {}},
            },
        ),
        (
            "object_joint",
            {
                "study_uid": "s",
                "series_uid": "series",
                "artifact": "s/a.npz",
                "joint": {"pointed_planes": []},
            },
        ),
        (
            "object_recess",
            {
                "study_uid": "s",
                "series_uid": "series",
                "artifact": "s/a.npz",
                "recess": {"pointed_planes": []},
            },
        ),
    ],
)
def test_single_archive_renderers_keep_open_through_picture_and_close_after(
    tmp_path: Path, module_name: str, record: dict
) -> None:
    retained = []

    def picture(record, *args):
        archive = next(arg for arg in args if hasattr(arg, "files"))
        assert archive["probe"].tolist() == [3, 7]
        retained.append(archive)
        return tmp_path / "render.png"

    module, run = _draw_case(tmp_path, module_name, [record], picture)
    module.draw(run, "s", tmp_path / "out", lambda _: np.zeros((2, 2)))
    assert len(retained) == 1
    with pytest.raises(ValueError, match="archive is closed"):
        retained[0]["probe"]


def test_patella_renderer_keeps_both_artifacts_open_and_closes_them(
    tmp_path: Path,
) -> None:
    prefix = "a3_twin"
    primary = {
        "study_uid": "s",
        "series_uid": "primary",
        "artifact": "s/primary.npz",
        "patella": {"pointed_planes": [], "twin_arrays_prefix": prefix},
        "arrays": {},
    }
    twin = {
        "study_uid": "s",
        "series_uid": "twin",
        "artifact": "s/twin.npz",
        "patella": {},
        "arrays": {f"{prefix}_slices": {}},
    }
    retained = []

    def picture(record, part, arrays, volume_of, twin_pair, prefix_arg, out):
        assert arrays["probe"].tolist() == [3, 7]
        assert twin_pair is not None
        twin_record, twin_arrays = twin_pair
        assert twin_record["artifact"] == "s/twin.npz"
        assert twin_arrays["probe"].tolist() == [3, 7]
        retained.extend((arrays, twin_arrays))
        return tmp_path / "render.png"

    module, run = _draw_case(tmp_path, "object_patella", [primary, twin], picture)
    module.draw(run, "s", tmp_path / "out", lambda _: np.zeros((2, 2)))
    assert len(retained) == 2
    for archive in retained:
        with pytest.raises(ValueError, match="archive is closed"):
            archive["probe"]
