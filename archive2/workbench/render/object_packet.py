"""Render a source-linked image series from a saved production Packet A run."""

import argparse
import json
from collections.abc import Sequence
from hashlib import sha256
from pathlib import Path

import numpy as np

from workbench.render._out import ArgumentRefusal

#: Where in the frame the detail panel looks, as a (row, column) fraction. The nearest ALREADY
#: MEASURED profile site to that point is the one drawn large.
#:
#: THIS IS NOT A BAR, and an earlier agent refused to supply one because it read it as one. A bar
#: is a threshold a DECISION reads, and no decision reads this: it selects which of the stage's own
#: measured profiles the picture zooms in on, and changes no reading, no named code and no
#: measurement. The centre of the frame is a display default, and the manifest records whichever
#: value was used, so the choice is visible rather than assumed.
CENTRE_OF_THE_FRAME: tuple[float, float] = (0.5, 0.5)


def draw(
    run: Path,
    study_uid: str,
    out: Path,
    *,
    probe_fraction_rc: Sequence[float] = CENTRE_OF_THE_FRAME,
) -> dict:
    """Draw this stage from the saved run and return its manifest.

    The one entry a caller uses, so the single command can draw every stage without knowing each
    renderer's argument spelling. `main()` is a thin wrapper over it, so the hand-typed command
    and the joined run draw the same thing from the same code.
    """
    fraction = np.asarray(probe_fraction_rc, dtype=np.float64)
    if (
        not np.all(np.isfinite(fraction))
        or np.any(fraction < 0)
        or np.any(fraction > 1)
    ):
        raise ArgumentRefusal("probe fractions must lie in [0,1]")
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    records = [
        r
        for r in receipt["records"]
        if r["study_uid"] == study_uid and "acquired_plane" in r["arrays"]
    ]
    if not records:
        raise ArgumentRefusal("no saved acquired planes for this study")

    # Imported HERE, after every refusal this function can make, and not at module scope. That is
    # the form `pair_frames` already uses: the module then imports without Matplotlib, so the
    # ordinary gate can test its argument handling, and a run with pictures off never loads it.
    # Matplotlib is supplied per run and is never a production dependency (`docs/STAGE_CONTRACT.md`).
    import matplotlib.pyplot as plt

    from workbench.render.object_profiles import draw_record

    out.mkdir(parents=True, exist_ok=True)
    gallery, axes = plt.subplots(
        len(records),
        5,
        figsize=(20, 4 * len(records)),
        layout="constrained",
        squeeze=False,
    )
    panels = []
    for row, metadata in enumerate(records):
        artifact = run / metadata.get("artifact", f"{metadata['series_uid']}.npz")
        with np.load(artifact, allow_pickle=False) as arrays:
            record = dict(arrays)
        for name, descriptor in metadata["arrays"].items():
            array = record[name]
            digest = sha256(
                array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
            ).hexdigest()
            if digest != descriptor["digest"]:
                raise ValueError("saved_array_digest_mismatch")
        record["spacing_rc_mm"] = np.asarray(metadata["spacing_rc_mm"])
        record["background_split"] = metadata.get("background_split")
        target = fraction * (np.asarray(record["acquired_plane"].shape) - 1)
        profile = (
            int(np.argmin(np.sum((record["points_rc"] - target) ** 2, axis=1)))
            if "points_rc" in record
            else 0
        )
        view, fluid, fat = metadata["view"]
        title = f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat}"
        draw_record(axes[row], record, profile, title)
        figure, one_axes = plt.subplots(1, 5, figsize=(20, 4), layout="constrained")
        draw_record(one_axes, record, profile, title)
        name = f"{row + 1:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"
        figure.savefig(out / name, dpi=160)
        plt.close(figure)
        panels.append(
            {
                "image": name,
                "artifact": str(artifact),
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "source_plane": metadata["source_plane"],
                "slice_index": metadata["slice_index"],
                "profile_index": profile,
                "profile_site_rc": record["points_rc"][profile].tolist()
                if "points_rc" in record
                else None,
            }
        )
    gallery.suptitle(
        "Packet A: acquired image → RED background annotation → squint → CYAN samples → measured profile",
        fontsize=17,
    )
    gallery.savefig(out / "series.png", dpi=160)
    plt.close(gallery)
    manifest = {
        "schema": "packet-a-visuals-v2",
        "color_legend": {
            "red": "saved mask from the production regime's whole-series background split",
            "cyan": "supported native profile sample locations",
            "magenta": "missing profile support",
        },
        "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "layout_sha256": sha256(
            Path(__file__).with_name("object_profiles.py").read_bytes()
        ).hexdigest(),
        "probe_fraction_rc": fraction.tolist(),
        "scope": "all saved middle planes in the chosen study; red background-split mask, cyan samples, magenta missing support",
        "panels": panels,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--study-uid", required=True)
    parser.add_argument("--probe-fraction-rc", type=float, nargs=2, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = draw(
            args.run,
            args.study_uid,
            args.out,
            probe_fraction_rc=args.probe_fraction_rc,
        )
    # ONLY the argument refusals. A bare `except ValueError` here swallowed
    # `saved_array_digest_mismatch` and a malformed receipt into an exit-2 usage error, which
    # dresses a corruption signal as a typo. Those propagate.
    except ArgumentRefusal as refusal:
        parser.error(str(refusal))
    print(
        json.dumps(
            {
                "images": len(manifest["panels"]),
                "series": str((args.out / "series.png").resolve()),
                "manifest": str((args.out / "manifest.json").resolve()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
