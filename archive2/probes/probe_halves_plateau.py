"""Process 1 probe, read-only: the two halves seeded from the plateaus either side of the band.

Per slice of each fat-bright coronal and sagittal series: the profile along the header's up-down
axis over the central third of the kept leg (`knee.collapse.structure._profile`); the band step is
the step that sits deepest below its enclosing level, the lower of the brightest step above it and
the brightest step below it (an enclosed dip, never an end); the seeds are the central-third kept
tiles two and three steps above the band (upper) and two and three steps below it (lower); the
watershed is the existing one (`-smooth`, Gaussian of one tile, mask the kept tiles). Prints per
slice the band step, the dip's depth as a share of its enclosing level, and the crossing span,
and draws every slice with the crossings marked.
"""

import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage
from skimage.segmentation import watershed

from knee.collapse import structure
from knee.collapse.first_lens import read_first_lens
from knee.collapse.regime import read_regime
from knee.collapse.squint_stack import read_squint_stack
from knee.study.corpus import LOCAL_ROOT, open_corpus, read_study

KEPT = (1, 2)


def enclosed_dip(profile):
    """(step, depth share) of the deepest enclosed dip; (-1, nan) when no step is enclosed."""
    finite = np.flatnonzero(np.isfinite(profile))
    best, best_depth, best_share = -1, 0.0, math.nan
    for position, step in enumerate(finite[1:-1], start=1):
        above = np.nanmax(profile[finite[:position]])
        below = np.nanmax(profile[finite[position + 1 :]])
        level = min(above, below)
        depth = level - profile[step]
        if depth > best_depth:
            best, best_depth = int(step), float(depth)
            best_share = float(depth / level) if level > 0 else math.nan
    return best, best_share


def central_columns(inside_along, central_fraction):
    across = np.flatnonzero(inside_along.any(axis=0))
    if across.size == 0:
        return None
    first, last = int(across[0]), int(across[-1])
    trim = max(0, math.floor((last - first + 1) * (1.0 - central_fraction) / 2.0))
    return first + trim, last + 1 - trim


def halves(median, inside, axis, superior, bars):
    field = np.where(inside, median, np.nan)
    profile, _ = structure._profile(field, axis, superior, bars.central_fraction)
    band, share = enclosed_dip(profile)
    if band < 0:
        return None, band, share
    inside_along = structure._along_first(inside, axis, superior)
    span = central_columns(inside_along, bars.central_fraction)
    if span is None:
        return None, band, share
    steps = inside_along.shape[0]
    seeds_along = np.zeros(inside_along.shape, dtype=np.int32)
    for offset in (2, 3):
        if band - offset >= 0:
            seeds_along[band - offset, span[0] : span[1]] = 1
        if band + offset < steps:
            seeds_along[band + offset, span[0] : span[1]] = 2
    seeds_along[~inside_along] = 0
    if not (seeds_along == 1).any() or not (seeds_along == 2).any():
        return None, band, share
    seeds = np.ascontiguousarray(structure._from_along_first(seeds_along, axis, superior))
    filled = np.where(inside, median, median[inside].min())
    smooth = ndimage.gaussian_filter(filled, bars.smoothing_sigma)
    basins = watershed(-smooth, markers=seeds, mask=inside).astype(np.int8)
    return basins, band, share


def crossings(median, basins, axis, superior):
    field = structure._along_first(median, axis, superior)
    labels = structure._along_first(basins, axis, superior)
    steps, across = labels.shape
    found = []
    for column in range(across):
        for step in range(steps - 1):
            if labels[step, column] == 1 and labels[step + 1, column] == 2:
                above, below = step - 2, step + 3
                ok = (
                    above >= 0
                    and below < steps
                    and labels[above, column] == 1
                    and labels[below, column] == 2
                )
                shows = bool(
                    ok
                    and field[step : step + 2, column].min()
                    < min(field[above, column], field[below, column])
                )
                found.append((step, column, shows))
                break
    return found


def to_tile(step, column, axis, superior, shape):
    rows, cols = shape
    if axis == "rows":
        return ((rows - 1 - step) if superior == "increasing" else step), column
    return column, ((cols - 1 - step) if superior == "increasing" else step)


def main(study_uid: str, out_dir: Path) -> None:
    corpus = open_corpus(LOCAL_ROOT)
    study = read_study(corpus, study_uid)
    out_dir.mkdir(parents=True, exist_ok=True)
    bars = structure.StructureBars()
    for number, series in enumerate(study.series, start=1):
        row = series.row
        if row.anatomical_plane == "Axial" or str(row.fluid_sensitive) == "1":
            continue
        regime = read_regime(series)
        stack = read_squint_stack(series, 8.0)
        first = read_first_lens(stack, regime.background_split)
        orientation = np.asarray(series.geometry.orientation[0], dtype=float)
        normal = np.cross(orientation[:3], orientation[3:6])
        axis = structure.axis_code(orientation[5], orientation[2], normal[2])
        chosen_z = {"rows": orientation[5], "columns": orientation[2]}.get(axis, normal[2])
        superior = structure.superior_code(chosen_z)
        count = len(stack.median)
        per_line = 6
        lines = int(np.ceil(count / per_line))
        top = float(np.percentile(series.volume, 99.5))
        figure, axes = plt.subplots(
            lines, per_line, figsize=(per_line * 3.0, lines * 3.0 + 0.8), squeeze=False
        )
        report = []
        for z in range(count):
            box = axes[z // per_line][z % per_line]
            box.set_axis_off()
            box.imshow(series.volume[z], cmap="gray", vmin=0, vmax=top)
            median = stack.median[z]
            inside = np.isin(first.codes[z], KEPT) & np.isfinite(median)
            if not inside.any():
                report.append(f"{z}:none")
                continue
            basins, band, share = halves(median, inside, axis, superior, bars)
            if basins is None:
                report.append(f"{z}:b{band}/unseeded")
                box.set_title(f"index {z}: unseeded", fontsize=8)
                continue
            found = crossings(median, basins, axis, superior)
            span = sum(1 for _, _, shows in found if shows)
            report.append(f"{z}:b{band}/d{share:.2f}/s{span}")
            for step, column, shows in found:
                r0, r1, c0, c1 = stack.bounds_rc[to_tile(step, column, axis, superior, basins.shape)]
                box.add_patch(
                    patches.Rectangle(
                        (c0, r0),
                        c1 - c0,
                        r1 - r0,
                        fill=False,
                        edgecolor="red" if shows else "yellow",
                        linewidth=0.8,
                    )
                )
            box.set_title(f"index {z}: band step {band}, dip {share:.2f}, span {span}", fontsize=8)
        for z in range(count, lines * per_line):
            axes[z // per_line][z % per_line].set_axis_off()
        figure.suptitle(
            f"{row.anatomical_plane} fat-bright: halves seeded either side of the deepest enclosed "
            f"dip of the central-third profile; red where the crossing shows the band",
            fontsize=11,
        )
        figure.tight_layout(rect=(0, 0, 1, 0.97))
        name = f"{number:02d}-{row.anatomical_plane}-plateau-halves.png"
        figure.savefig(out_dir / name, dpi=70)
        plt.close(figure)
        print(f"{name}: tiles {stack.median.shape[1:]}")
        print("  " + " ".join(report))


if __name__ == "__main__":
    main(sys.argv[1], Path(sys.argv[2]))
