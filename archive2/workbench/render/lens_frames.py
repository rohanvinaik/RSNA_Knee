"""Draw private native-plane lens frames from saved production maps, one per seated member.

The displayed digits and named silences are the stage's saved values, selected
by the writer at the recorded native plane. This renderer applies a fixed color
legend and arranges existing metadata. It takes no measurement, recounts no
places, derives no position and asserts no correspondence or anatomical identity.

Each series draws one column per SEATED MEMBER and one more for their standing.
Nothing here resolves a `dissent`: it is drawn as a disagreement, because that is
the informative case (`chapters/02-collapse/teachings.md`, KEEP EVERYTHING).
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

from knee.lenses.members import STANDING_CODES
from knee.pictures import lenses

COLORS = ("#2563eb", "#22c55e", "#f59e0b", "#9ca3af")
LEGEND = ("-1", "0", "+1", "2: silence")

#: One colour per standing, in STANDING_CODES order. `dissent` is the loud one on purpose: it
#: is where two correct overlapping readings differ, which the founder names as among the most
#: informative data available rather than as an error.
STANDING_COLORS = ("#22c55e", "#dc2626", "#2563eb", "#f59e0b", "#9ca3af", "#7c3aed")


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


def saved_panels(
    run: Path, metadata: dict
) -> tuple[Path, tuple[tuple[dict, lenses.LensPanels], ...], lenses.StandingPanels]:
    """Hand every member's validated saved plane and the standing plane to the adapters."""
    if "lenses" not in metadata:
        raise ValueError("missing_saved_stage_reading")
    if "artifact" not in metadata or "arrays" not in metadata:
        raise ValueError("missing_saved_artifact")
    saved_lenses = metadata["lenses"]
    if not saved_lenses.get("members"):
        raise ValueError("missing_saved_members")
    artifact = run / metadata["artifact"]
    members: list[tuple[dict, lenses.LensPanels]] = []
    with np.load(artifact, allow_pickle=False) as arrays:
        for member in saved_lenses["members"]:
            codes = saved_map(
                arrays, metadata["arrays"], member["codes_array"], np.dtype(np.uint8)
            )
            digits = saved_map(
                arrays, metadata["arrays"], member["digits_array"], np.dtype(np.int8)
            )
            if codes.shape != digits.shape:
                raise ValueError("lens_map_shape_mismatch")
            members.append(
                (
                    member,
                    lenses.panels(
                        code=member["picture_code"],
                        why=member["why"],
                        codes=codes,
                        digits=digits,
                        low_edge=member["low_edge"],
                        high_edge=member["high_edge"],
                        normalisation=member["normalisation"],
                    ),
                )
            )
        standings = saved_map(
            arrays,
            metadata["arrays"],
            saved_lenses["standings_array"],
            np.dtype(np.uint8),
        )
    standing = lenses.standing_panels(
        standings=standings,
        counts=tuple(saved_lenses["standing_counts"]),
        populations=tuple(m["population"] for m in saved_lenses["members"]),
    )
    return artifact, tuple(members), standing


def draw_frame(
    axis: object, member: dict, frame: lenses.LensPanels, metadata: dict
) -> None:
    """Arrange ONE member's selected native plane, its existing counts and the fixed legend."""
    counts = ", ".join(
        f"{name}={count}"
        for name, count in zip(
            metadata["lenses"]["code_names"], member["counts"], strict=True
        )
    )
    title = (
        f"{fill(metadata['series_uid'], width=42)}\n"
        f"member: {member['population']}\n"
        f"{frame.code}: {fill(frame.why, width=60)}\n"
        f"stored-unit edges: {frame.low_edge}, {frame.high_edge}; "
        f"normalisation: {frame.normalisation}\n"
        f"complete-native-volume counts: {fill(counts, width=60)}"
    )
    axis.set_title(title, fontsize=8)
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
            f"{frame.code}\n\n{fill(frame.why, width=60)}",
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


def draw_standing(axis: object, standing: lenses.StandingPanels) -> None:
    """Arrange what the members jointly said, with dissent shown AS dissent."""
    counts = ", ".join(
        f"{name}={count}"
        for name, count in zip(STANDING_CODES, standing.counts, strict=True)
    )
    first, second = standing.populations[0], standing.populations[1]
    axis.set_title(
        f"what the seated members jointly said\n"
        f"first={first} · second={second}\n"
        f"{fill(counts, width=60)}\n"
        "nothing here resolves a dissent",
        fontsize=8,
    )
    if standing.standings.size:
        axis.imshow(
            standing.standings,
            cmap=ListedColormap(STANDING_COLORS),
            vmin=0,
            vmax=len(STANDING_COLORS) - 1,
            interpolation="nearest",
        )
    else:
        axis.text(
            0.03, 0.95, "no saved standing plane", transform=axis.transAxes, va="top"
        )
    axis.legend(
        handles=[
            Patch(facecolor=color, label=label)
            for color, label in zip(STANDING_COLORS, STANDING_CODES, strict=True)
        ],
        loc="lower center",
        bbox_to_anchor=(0.5, -0.12),
        ncol=3,
        frameon=False,
    )
    axis.set_axis_off()


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run and return its manifest.

    The one entry a caller uses, so the single command can draw every stage without knowing each
    renderer's argument spelling. `main()` is a thin wrapper over it, so the hand-typed command
    and the joined run draw the same thing from the same code.
    """
    data_root = Path(__file__).resolve().parents[2] / "data"
    output = out.resolve()
    if not output.is_relative_to(data_root.resolve()):
        raise ValueError("out must be under the project's private data directory")
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    records = [
        record for record in receipt["records"] if record["study_uid"] == study_uid
    ]
    if not records:
        raise ValueError("no saved records for this study")
    loaded = [saved_panels(run, record) for record in records]
    if lenses.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:lenses")
    columns = max(len(members) for _, members, _ in loaded) + 1
    output.mkdir(parents=True, exist_ok=True)
    gallery, axes = plt.subplots(
        len(records),
        columns,
        figsize=(6 * columns, 7 * len(records)),
        layout="constrained",
        squeeze=False,
    )
    series = []
    for row, (metadata, saved) in enumerate(zip(records, loaded, strict=True)):
        artifact, members, standing = saved
        for column, (member, frame) in enumerate(members):
            draw_frame(axes[row, column], member, frame, metadata)
        for column in range(len(members), columns - 1):
            axes[row, column].set_axis_off()
        draw_standing(axes[row, columns - 1], standing)
        series.append(
            {
                "series_uid": metadata["series_uid"],
                "artifact": metadata["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "arrays": {
                    name: metadata["arrays"][name]
                    for member, _ in members
                    for name in (member["codes_array"], member["digits_array"])
                }
                | {
                    metadata["lenses"]["standings_array"]: metadata["arrays"][
                        metadata["lenses"]["standings_array"]
                    ]
                },
                "lenses": metadata["lenses"],
                "frame_kind": "selected native plane, one column per seated member",
            }
        )
    gallery.suptitle(
        "Saved native-plane lens digits per seated member, and where they disagree"
    )
    gallery.savefig(output / "series.png", dpi=160)
    plt.close(gallery)
    manifest = {
        "schema": "lens-frames-v2",
        "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "lenses": sha256(Path(lenses.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": "series.png",
        "color_legend": dict(zip(LEGEND, COLORS, strict=True)),
        "standing_legend": dict(zip(STANDING_CODES, STANDING_COLORS, strict=True)),
        "series": series,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--study-uid", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        draw(args.run, args.study_uid, args.out)
    except ValueError as refusal:
        parser.error(str(refusal))
    output = args.out.resolve()
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
