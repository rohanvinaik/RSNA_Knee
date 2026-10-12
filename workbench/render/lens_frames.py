"""Draw private native-plane lens frames from saved production maps.

The displayed digits and named silences are the stage's saved values, selected
by the writer at the recorded native plane. This renderer applies a fixed color
legend and arranges existing metadata. It takes no measurement, recounts no
places, derives no position and asserts no correspondence or anatomical identity.
"""

import argparse
import json
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.patches import Patch

from knee.pictures import lenses

COLORS = ("#2563eb", "#22c55e", "#f59e0b", "#9ca3af")
LEGEND = ("-1", "0", "+1", "2: silence")


def saved_map(
    arrays: Mapping[str, np.ndarray],
    descriptors: dict,
    name: str,
    dtype: np.dtype,
) -> np.ndarray:
    """Validate one saved map's dtype, shape and recorded content digest."""
    if name not in arrays or name not in descriptors:
        raise ValueError(f"missing_saved_map:{name}")
    array = arrays[name]
    descriptor = descriptors[name]
    if array.dtype.str != descriptor["dtype"]:
        raise ValueError(f"saved_array_dtype_mismatch:{name}")
    if array.shape != tuple(descriptor["shape"]):
        raise ValueError(f"saved_array_shape_mismatch:{name}")
    digest = sha256(
        array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
    ).hexdigest()
    if digest != descriptor["digest"]:
        raise ValueError(f"saved_array_digest_mismatch:{name}")
    if array.dtype != dtype or array.ndim != 2:
        raise ValueError(f"saved_map_representation_invalid:{name}")
    return array


def saved_panels(run: Path, metadata: dict) -> tuple[Path, lenses.LensPanels]:
    """Hand validated saved plane arrays and existing metadata to the picture adapter."""
    if "lenses" not in metadata:
        raise ValueError("missing_saved_stage_reading")
    if "artifact" not in metadata or "arrays" not in metadata:
        raise ValueError("missing_saved_artifact")
    artifact = run / metadata["artifact"]
    with np.load(artifact, allow_pickle=False) as arrays:
        codes = saved_map(arrays, metadata["arrays"], "lens_codes", np.dtype(np.uint8))
        digits = saved_map(arrays, metadata["arrays"], "lens_digits", np.dtype(np.int8))
    if codes.shape != digits.shape:
        raise ValueError("lens_map_shape_mismatch")
    saved_lenses = metadata["lenses"]
    return artifact, lenses.panels(
        code=saved_lenses["picture_code"],
        why=saved_lenses["why"],
        codes=codes,
        digits=digits,
        low_edge=saved_lenses["low_edge"],
        high_edge=saved_lenses["high_edge"],
        normalisation=saved_lenses["normalisation"],
    )


def draw_frame(axis: object, frame: lenses.LensPanels, metadata: dict) -> None:
    """Arrange the stage's selected native plane, existing counts and fixed legend."""
    saved_lenses = metadata["lenses"]
    counts = ", ".join(
        f"{name}={count}"
        for name, count in zip(
            saved_lenses["code_names"], saved_lenses["counts"], strict=True
        )
    )
    title = (
        f"{fill(metadata['series_uid'], width=42)}\n"
        "selected native plane (row,column)\n"
        f"{frame.code}: {fill(frame.why, width=85)}\n"
        f"stored-unit edges: {frame.low_edge}, {frame.high_edge}; "
        f"normalisation: {frame.normalisation}\n"
        f"complete-native-volume counts: {fill(counts, width=85)}"
    )
    axis.set_title(title, fontsize=9)
    if frame.digits.size:
        axis.imshow(
            frame.digits,
            cmap=ListedColormap(COLORS),
            norm=BoundaryNorm((-1.5, -0.5, 0.5, 1.5, 2.5), len(COLORS)),
            interpolation="nearest",
        )
    else:
        axis.text(
            0.03,
            0.95,
            f"{frame.code}\n\n{fill(frame.why, width=85)}",
            transform=axis.transAxes,
            va="top",
            wrap=True,
        )
    axis.legend(
        handles=[
            Patch(facecolor=color, label=label)
            for color, label in zip(COLORS, LEGEND, strict=True)
        ],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.08),
        ncol=4,
        frameon=False,
    )
    axis.set_axis_off()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--study-uid", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data_root = Path(__file__).resolve().parents[2] / "data"
    output = args.out.resolve()
    if not output.is_relative_to(data_root.resolve()):
        parser.error("out must be under the project's private data directory")
    receipt_path = args.run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    records = [
        record for record in receipt["records"] if record["study_uid"] == args.study_uid
    ]
    if not records:
        parser.error("no saved records for this study")
    loaded = [saved_panels(args.run, record) for record in records]
    if lenses.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:lenses")
    output.mkdir(parents=True, exist_ok=True)
    gallery, axes = plt.subplots(
        len(records),
        1,
        figsize=(10, 7 * len(records)),
        layout="constrained",
        squeeze=False,
    )
    series = []
    for row, (metadata, saved) in enumerate(zip(records, loaded, strict=True)):
        artifact, frame = saved
        draw_frame(axes[row, 0], frame, metadata)
        series.append(
            {
                "series_uid": metadata["series_uid"],
                "artifact": metadata["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "arrays": {
                    name: metadata["arrays"][name]
                    for name in ("lens_codes", "lens_digits")
                },
                "lenses": metadata["lenses"],
                "frame_kind": "selected native plane",
            }
        )
    gallery.suptitle("Saved native-plane lens digits; silence is distinct from middle")
    gallery.savefig(output / "series.png", dpi=160)
    plt.close(gallery)
    manifest = {
        "schema": "lens-frames-v1",
        "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "lenses": sha256(Path(lenses.__file__).read_bytes()).hexdigest()
        },
        "study_uid": args.study_uid,
        "image": "series.png",
        "color_legend": dict(zip(LEGEND, COLORS, strict=True)),
        "series": series,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {
                "series": str(output / "series.png"),
                "manifest": str(output / "manifest.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
