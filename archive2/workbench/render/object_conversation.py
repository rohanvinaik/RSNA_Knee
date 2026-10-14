"""Render saved production B2 conversations; this module never recomputes them."""

import argparse
import colorsys
import json
from hashlib import sha256
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.patches import Patch

from knee.pictures import objects as object_pictures

TERRITORY = plt.colormaps["tab20"]
EXCHANGE_COLORS = {
    "concurrent": "#00e5ff",
    "peer_only": "#ffb000",
    "disagreement": "#ff3b30",
    "native_missing": "#ff00ff",
    "native_open": "#ff6bd6",
    "native_multiple": "#a855f7",
    "outside_slab": "#8c564b",
    "slab_support_unknown": "#7f7f7f",
    "normal_unavailable": "#d62728",
    "empty_profile": "#bcbd22",
    "invalid_measurement": "#17becf",
}

#: This renderer's own refusal for a saved row it cannot lay a plane out for. It is recorded beside
#: the code the conversation stage saved for that row, which says why upstream; this one says what
#: could not be arranged here.
PLANE_UNAVAILABLE = "acquired_plane_unavailable"


def digest_array(array):
    return sha256(
        array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
    ).hexdigest()


def territory_rgba(labels):
    rgba = np.zeros((*labels.shape, 4))
    for label in np.unique(labels):
        if label:
            rgba[labels == label] = TERRITORY((int(label) - 1) % 20)
            rgba[labels == label, 3] = 0.72
    return rgba


def subdivision_rgba(labels, parents):
    rgba = np.zeros((*labels.shape, 4))
    colors = {}
    for child in np.unique(labels):
        if child:
            parent = int(parents[int(child)])
            base = TERRITORY((parent - 1) % 20)[:3]
            # Siblings retain their parent's hue and receive deterministic shades.
            h, s, v = colorsys.rgb_to_hsv(*base)
            sibling = np.flatnonzero(parents[1:] == parent) + 1
            rank = int(np.flatnonzero(sibling == child)[0])
            if len(sibling) == 1:
                color = (*base, 0.72)
            else:
                value = min(0.95, max(0.42, v * (0.62 + 0.36 * ((rank % 4) / 3))))
                color = (
                    *colorsys.hsv_to_rgb(h, min(1, s * (1 + 0.12 * (rank % 2))), value),
                    0.82,
                )
            rgba[labels == child] = color
            colors[int(child)] = color
    return rgba, colors


def image_base(ax, plane, background=None):
    ax.imshow(plane, cmap="gray")
    if background is not None and background.shape == plane.shape:
        overlay = np.zeros((*plane.shape, 4))
        overlay[background] = (1, 0.08, 0.08, 0.78)
        ax.imshow(overlay, interpolation="nearest")
    ax.set_axis_off()


def edge_segments(points, normals):
    if not len(points):
        return np.empty((0, 2, 2))
    tangent = np.column_stack((-normals[:, 1], normals[:, 0]))
    tangent /= np.maximum(np.max(np.abs(tangent), axis=1)[:, None], 1e-12)
    return np.stack((points - tangent / 2, points + tangent / 2), axis=1)[:, :, ::-1]


def add_original(ax, plane, arrays, record, background=None, show_legend=True):
    image_base(ax, plane, background)
    labels = arrays.get("b1_labels")
    handles = []
    if labels is not None and labels.shape == plane.shape:
        ax.imshow(territory_rgba(labels), interpolation="nearest")
        for label in np.unique(labels):
            if label:
                handles.append(
                    Patch(
                        facecolor=TERRITORY((int(label) - 1) % 20),
                        label=f"original territory {int(label)}",
                    )
                )
                points = np.argwhere(labels == label)
                r, c = points.mean(axis=0)
                ax.text(
                    c,
                    r,
                    str(int(label)),
                    color="white",
                    fontsize=7,
                    ha="center",
                    va="center",
                    weight="bold",
                )
    if "b1_edge_points_rc" in arrays and "b1_edge_normals_rc" in arrays:
        points, normals = arrays["b1_edge_points_rc"], arrays["b1_edge_normals_rc"]
        seg = edge_segments(points, normals)
        codes = arrays.get("b1_trace_codes", np.ones(len(seg), dtype=int))
        colors = {1: "#00e5ff", 2: "#ffd166", 3: "#ff9e00", 4: "#ff00ff", 5: "#ff00ff"}
        for code, color in colors.items():
            if np.any(codes == code):
                ax.add_collection(
                    LineCollection(seg[codes == code], colors=color, linewidths=0.8)
                )
                handles.append(Patch(color=color, label=f"B1 trace code {code}"))
        trace_points = arrays.get("b1_trace_points_rc", np.empty((0, 2)))
        resolved = codes == 1
        if len(trace_points) == len(codes) and np.any(resolved):
            selected = trace_points[resolved]
            ax.scatter(selected[:, 1], selected[:, 0], s=4, c="#00e5ff", linewidths=0)
            handles.append(
                Patch(color="#00e5ff", label="saved B1 bracketed native traces")
            )
        unresolved = ~resolved
        if np.any(unresolved):
            ax.add_collection(
                LineCollection(
                    seg[unresolved], colors="#ffd166", linewidths=0.25, alpha=0.55
                )
            )
            handles.append(
                Patch(color="#ffd166", label="saved unresolved B1 edge support")
            )
    if background is not None and np.any(background):
        handles.append(
            Patch(color="red", label="saved surrounding-background predicate")
        )
    if handles and show_legend:
        ax.legend(
            handles=handles,
            fontsize=5,
            loc="upper left",
            bbox_to_anchor=(1.01, 1),
            borderaxespad=0,
            framealpha=0.9,
        )
    ax.set_title(
        "Original B1 territories + profile traces\nterritory IDs are original labels"
    )


def all_exchange_items(record, arrays):
    conversation = record["conversation"]
    for index, exchange in enumerate(conversation.get("exchanges", [])):
        prefix = f"b2_exchange{index}_"
        yield (
            exchange,
            {
                key[len(prefix) :]: value
                for key, value in arrays.items()
                if key.startswith(prefix)
            },
        )


def slice_position(row):
    """Where a saved row sorts among those of its view: a saved silence first, then by saved index.

    A series with no stacked volume saves `slice_index: None`, a reading its stage did not make.
    The silence is placed by this rule and is never given a number to sort on; the saved integers
    sort as saved.
    """
    index = row.get("slice_index")
    return (False, 0) if index is None else (True, int(index))


def plane_unavailable(plane):
    """True where a saved row has no acquired plane this renderer can lay out: none saved, not
    two-dimensional, or empty."""
    return plane is None or plane.ndim != 2 or not plane.size


def standing(row, plane):
    """What a saved row says about itself where it is listed: the code its conversation stage saved
    for it, and this renderer's refusal where it could not lay the row's plane out. Both are read,
    never computed."""
    return {
        "conversation_code": row["conversation"].get("code"),
        "refusal": PLANE_UNAVAILABLE if plane_unavailable(plane) else None,
    }


def mark_plane_unavailable(axes, view_label, row):
    """Say on every axis of a row that its acquired plane is unavailable, with the conversation
    stage's own saved code beside the view, so the silence reads as the stage's silence."""
    for ax in axes:
        ax.set_axis_off()
        ax.text(
            0.5,
            0.5,
            f"Acquired plane unavailable\n{view_label}\n"
            f"conversation stage code: {row['conversation'].get('code')}",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )


def panel_record(stage, row, artifact, peers, plane):
    """One saved row's entry in a stage's panel list: where it came from, which donors it heard
    from, and its standing. A row whose plane is unavailable is listed too, with the refusal."""
    return {
        "stage": stage,
        "series_uid": row["series_uid"],
        "source_plane": row.get("source_plane"),
        "slice_index": row.get("slice_index"),
        "artifact": str(artifact.resolve()),
        "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
        "donor_uids": [meta["donor_uid"] for meta, _ in peers],
        **standing(row, plane),
    }


#: The saved arrays `knee.pictures.objects.panels` arranges besides the donors' own places: the plane
#: the series was read at, B1's territories, and both subdivisions with their parent maps.
PARTED_ARRAYS = (
    "acquired_plane",
    "b1_labels",
    "b2_concurrent_labels",
    "b2_conditional_labels",
    "b2_concurrent_parents",
    "b2_conditional_parents",
)


def donor_arrays(peers):
    """The peers' transported places, trace codes and derived traces, joined in peer order.

    Returns (joined arrays, the name of what a peer lacks). A series with no exchange joins to
    nothing, which is what it is; a peer that lacks one of the three is named and nothing is joined
    over the gap.
    """
    nothing = {
        "points_rc": np.empty((0, 2)),
        "trace_codes": np.empty(0, dtype=np.uint8),
        "derived_trace_rc": np.empty((0, 2)),
    }
    joined = {}
    for name, empty in nothing.items():
        parts = []
        for index, (_metadata, fields) in enumerate(peers):
            if name not in fields:
                return {}, f"b2_exchange{index}_{name}"
            parts.append(fields[name])
        joined[name] = np.concatenate(parts) if parts else empty
    return joined, ""


def parted_more(arrays, peers):
    """How many more children the saved conditional subdivision made than the saved concurrent one.

    Returns (the count or None, a code that says why there is none). The count is the adapter's own,
    `knee.pictures.objects.parted_more_by`, asked of the saved arrays arranged by
    `knee.pictures.objects.panels`: nothing is recounted here. An array the run did not save, or
    arrays the adapter refuses to arrange as one parse of one plane, make the count a named silence
    and never a zero.
    """
    for name in PARTED_ARRAYS:
        if name not in arrays:
            return None, f"not saved ({name})"
    donors, lacking = donor_arrays(peers)
    if lacking:
        return None, f"not saved ({lacking})"
    try:
        shaped = object_pictures.panels(
            arrays["acquired_plane"],
            arrays["b1_labels"],
            donors["points_rc"],
            donors["trace_codes"],
            donors["derived_trace_rc"],
            arrays["b2_concurrent_labels"],
            arrays["b2_conditional_labels"],
            arrays["b2_concurrent_parents"],
            arrays["b2_conditional_parents"],
        )
    except ValueError as refusal:
        return None, f"not arranged ({refusal})"
    return object_pictures.parted_more_by(shaped), "counted"


def more_text(count, code):
    """The line a subdivision's panel carries for `parted_more_by`, or why there is none."""
    if count is None:
        return f"parted_more_by: {code}"
    return f"parted_more_by {count:+d} (conditional children - concurrent children)"


def draw_bands(ax, plane, record, arrays, peers, show_legend=True):
    image_base(ax, plane, arrays.get("background_mask"))
    present = set()
    for _metadata, fields in peers:
        quads = fields.get("donor_quads_rc", np.empty((0, 4, 2)))
        codes = fields.get("trace_codes", np.empty(0, dtype=int))
        if len(quads):
            code_names = {
                value: name
                for name, value in record["conversation"]["exchange_codes"].items()
            }
            colors = [
                EXCHANGE_COLORS.get(code_names.get(int(code), ""), "#ffffff")
                for code in codes
            ]
            present.update(int(code) for code in np.unique(codes))
            ax.add_collection(
                PolyCollection(
                    quads[:, :, ::-1],
                    facecolors=colors,
                    edgecolors=colors,
                    alpha=0.27,
                    linewidths=0.35,
                )
            )
            ax.scatter(
                fields["points_rc"][:, 1],
                fields["points_rc"][:, 0],
                s=2,
                c=colors,
                alpha=0.9,
            )
    codebook = record["conversation"]["exchange_codes"]
    handles = [
        Patch(color=EXCHANGE_COLORS.get(name, "#ffffff"), label=name)
        for name, value in codebook.items()
        if value in present
    ]
    if handles and show_legend:
        ax.legend(
            handles=handles,
            fontsize=5,
            loc="upper left",
            bbox_to_anchor=(1.01, 1),
            borderaxespad=0,
            framealpha=0.9,
        )
    ax.set_title("Transported donor bands\ncolored by saved native outcome")


def draw_native(ax, plane, record, arrays, peers, show_legend=True):
    image_base(ax, plane, arrays.get("background_mask"))
    codebook = record["conversation"]["exchange_codes"]
    for metadata, fields in peers:
        codes = fields.get("trace_codes", np.empty(0, dtype=int))
        points = fields.get("points_rc", np.empty((0, 2)))
        trace = fields.get("derived_trace_rc", np.empty((0, 2)))
        for name, value in codebook.items():
            select = codes == value
            color = EXCHANGE_COLORS.get(name, "#ffffff")
            if np.any(select):
                ax.scatter(
                    points[select, 1],
                    points[select, 0],
                    s=5,
                    c=color,
                    label=f"{metadata['donor_uid'][-8:]} · {name} ({select.sum()})",
                )
        resolved = (
            np.isfinite(trace).all(axis=1) if len(trace) else np.zeros(0, dtype=bool)
        )
        if np.any(resolved):
            ax.scatter(
                trace[resolved, 1],
                trace[resolved, 0],
                s=9,
                facecolors="none",
                edgecolors=EXCHANGE_COLORS["concurrent"],
                linewidths=0.45,
            )
    if np.any(arrays.get("background_mask", np.zeros((0, 0), dtype=bool))):
        ax.scatter(
            [],
            [],
            marker="s",
            color="red",
            label="saved surrounding-background predicate",
        )
    ax.scatter(
        [],
        [],
        marker="o",
        facecolors="none",
        edgecolors=EXCHANGE_COLORS["concurrent"],
        label="derived concurrent intersection",
    )
    if show_legend and ax.get_legend_handles_labels()[0]:
        ax.legend(
            fontsize=5,
            loc="upper left",
            bbox_to_anchor=(1.01, 1),
            borderaxespad=0,
            framealpha=0.9,
        )
    ax.set_title(
        "Native outcomes + derived concurrent traces\nopen circles: derived intersections",
        fontsize=9,
    )


def draw_subdivision(ax, plane, arrays, kind, show_legend=True, more=""):
    labels = arrays[f"b2_{kind}_labels"]
    parents = arrays[f"b2_{kind}_parents"]
    barrier = arrays[f"b2_{kind}_barrier"]
    image_base(ax, plane, arrays.get("background_mask"))
    if labels.shape != plane.shape or barrier.shape != plane.shape:
        ax.set_title(
            f"{kind.capitalize()} subdivision unavailable\nsource territory map unavailable"
        )
        return
    rgba, colors = subdivision_rgba(labels, parents)
    ax.imshow(rgba, interpolation="nearest")
    overlay = np.zeros((*plane.shape, 4))
    overlay[barrier] = (1.0, 0.92, 0.05, 0.95)
    ax.imshow(overlay, interpolation="nearest")
    handles = [
        Patch(
            color="#ffea00",
            label=f"retained {kind} barrier ({int(barrier.sum())} cells)",
        )
    ]
    if np.any(arrays.get("background_mask", np.zeros((0, 0), dtype=bool))):
        handles.append(
            Patch(color="red", label="saved surrounding-background predicate")
        )
    parent_children = {}
    for child in sorted(colors):
        parent_children.setdefault(int(parents[child]), []).append(child)
        pixels = np.argwhere(labels == child)
        if len(pixels) >= 36:
            r, c = pixels.mean(axis=0)
            ax.text(
                c,
                r,
                f"{int(parents[child])}.{child}",
                color="white",
                fontsize=5,
                ha="center",
                va="center",
                weight="bold",
            )
    for parent, children in sorted(parent_children.items()):
        handles.append(
            Patch(
                facecolor=colors[children[0]],
                label=f"original parent {parent}: {len(children)} children",
            )
        )
    if show_legend:
        ax.legend(
            handles=handles,
            fontsize=5,
            loc="upper left",
            bbox_to_anchor=(1.01, 1),
            borderaxespad=0,
            framealpha=0.9,
        )
    original = arrays.get("b1_labels", np.zeros((0, 0), dtype=np.int32))
    territory_count = int(np.count_nonzero(np.unique(original)))
    ax.set_title(
        f"{kind.capitalize()} subdivision\n"
        f"{territory_count} original · {len(colors)} children · {int(barrier.sum())} barrier cells\n"
        "child IDs map explicitly to original parents" + (f"\n{more}" if more else ""),
        fontsize=9,
    )


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run and return its manifest.

    The one entry a caller uses, so the single command can draw every stage without knowing each
    renderer's argument spelling. `main()` is a thin wrapper over it, so the hand-typed command
    and the joined run draw the same thing from the same code.
    """
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    records = [
        row
        for row in receipt["records"]
        if row["study_uid"] == study_uid and "conversation" in row
    ]
    if not records:
        raise ValueError("no saved B2 conversation records for selected study")
    records.sort(key=lambda row: (tuple(row.get("view", ())), slice_position(row)))
    out.mkdir(parents=True, exist_ok=True)
    prepared = []
    for row in records:
        artifact = run / row["artifact"]
        with np.load(artifact, allow_pickle=False) as saved:
            arrays = dict(saved)
        for name, descriptor in row["arrays"].items():
            if digest_array(arrays[name]) != descriptor["digest"]:
                raise ValueError(f"saved_array_digest_mismatch:{name}")
        plane = arrays.get("acquired_plane")
        prepared.append(
            (row, arrays, artifact, list(all_exchange_items(row, arrays)), plane)
        )

    # `parted_more_by` of every saved row, from the adapter and the saved arrays alone; a row that
    # cannot be arranged carries the reason in place of the count.
    parted = {
        row["series_uid"]: parted_more(arrays, peers)
        for row, arrays, _artifact, peers, _plane in prepared
    }

    def more_for(row):
        return more_text(*parted[row["series_uid"]])

    views = len(prepared)
    stages = [
        "01-original-b1",
        "02-donor-bands",
        "03-native-outcomes",
        "04-concurrent-subdivision",
        "05-conditional-subdivision",
    ]
    panels = []
    renderers = []
    for filename in stages:
        fig, axes = plt.subplots(
            views, 2, figsize=(18, 4.6 * views), squeeze=False, layout="constrained"
        )
        for index, (row, arrays, artifact, peers, plane) in enumerate(prepared):
            view = row.get("view", ["view", "?", "?"])
            view_label = f"{view[0]} · fs={view[1]} · fat={view[2]} · slice {row.get('slice_index')}"
            if plane_unavailable(plane):
                mark_plane_unavailable(axes[index], view_label, row)
                panels.append(panel_record(filename, row, artifact, peers, plane))
                continue
            if filename == stages[0]:
                image_base(axes[index, 0], plane, arrays.get("background_mask"))
                axes[index, 0].set_title(
                    "Acquired plane; RED marks saved background predicate"
                )
                add_original(
                    axes[index, 1], plane, arrays, row, arrays.get("background_mask")
                )
            elif filename == stages[1]:
                add_original(
                    axes[index, 0], plane, arrays, row, arrays.get("background_mask")
                )
                draw_bands(axes[index, 1], plane, row, arrays, peers)
            elif filename == stages[2]:
                draw_bands(axes[index, 0], plane, row, arrays, peers)
                draw_native(axes[index, 1], plane, row, arrays, peers)
            elif filename == stages[3]:
                add_original(
                    axes[index, 0], plane, arrays, row, arrays.get("background_mask")
                )
                draw_subdivision(
                    axes[index, 1], plane, arrays, "concurrent", more=more_for(row)
                )
            else:
                add_original(
                    axes[index, 0], plane, arrays, row, arrays.get("background_mask")
                )
                draw_subdivision(
                    axes[index, 1], plane, arrays, "conditional", more=more_for(row)
                )
            axes[index, 0].set_title(
                axes[index, 0].get_title() + "\n" + view_label, fontsize=8
            )
            panels.append(panel_record(filename, row, artifact, peers, plane))
        fig.suptitle(f"B2 same-knee conversation · {filename}", fontsize=15)
        path = out / f"{filename}.png"
        fig.savefig(path, dpi=145)
        plt.close(fig)
        renderers.append(path)

    # Compact five-view overview: one row per saved view, one column per reading.
    fig, axes = plt.subplots(
        views, 5, figsize=(30, 4.2 * views), squeeze=False, layout="constrained"
    )
    for index, (row, arrays, _artifact, peers, plane) in enumerate(prepared):
        view = row.get("view", ["view", "?", "?"])
        view_label = (
            f"{view[0]} fs={view[1]} fat={view[2]} · slice {row.get('slice_index')}"
        )
        if plane_unavailable(plane):
            mark_plane_unavailable(axes[index], view_label, row)
            continue
        add_original(
            axes[index, 0], plane, arrays, row, arrays.get("background_mask"), False
        )
        draw_bands(axes[index, 1], plane, row, arrays, peers, False)
        draw_native(axes[index, 2], plane, row, arrays, peers, False)
        draw_subdivision(
            axes[index, 3], plane, arrays, "concurrent", False, more_for(row)
        )
        draw_subdivision(
            axes[index, 4], plane, arrays, "conditional", False, more_for(row)
        )
        axes[index, 0].set_title(
            axes[index, 0].get_title() + "\n" + view_label, fontsize=7
        )
    fig.suptitle(
        "B2 conversation across saved acquired views · source measurements and derived readings",
        fontsize=16,
    )
    code_counts = {
        name: 0
        for row, *_ in prepared
        for name in row["conversation"]["exchange_codes"]
    }
    for row, _arrays, _, peers, plane in prepared:
        if plane is None:
            continue
        for _, fields in peers:
            for name, value in row["conversation"]["exchange_codes"].items():
                code_counts[name] += int(
                    np.count_nonzero(fields.get("trace_codes", np.empty(0)) == value)
                )
    global_handles = [
        Patch(color=EXCHANGE_COLORS.get(name, "#ffffff"), label=f"{name}: {count}")
        for name, count in code_counts.items()
    ]
    global_handles.extend(
        (
            Patch(color="red", label="saved background predicate"),
            Patch(color="#ffea00", label="retained barrier"),
            Patch(color="#00e5ff", label="original B1 bracketed trace"),
        )
    )
    fig.legend(
        handles=global_handles,
        loc="center left",
        bbox_to_anchor=(1.005, 0.5),
        fontsize=7,
        framealpha=0.9,
    )
    overview = out / "series.png"
    fig.savefig(overview, dpi=130, bbox_inches="tight")
    plt.close(fig)

    focused_views = []
    for index, (row, arrays, artifact, peers, plane) in enumerate(prepared, start=1):
        focused = plt.figure(figsize=(27, 6.5), layout="constrained")
        grid = focused.add_gridspec(2, 5, height_ratios=(1, 0.22))
        focused_axes = [focused.add_subplot(grid[0, column]) for column in range(5)]
        legend_axis = focused.add_subplot(grid[1, :])
        legend_axis.set_axis_off()
        view = row.get("view", ["view", "?", "?"])
        view_label = (
            f"{view[0]} · fs={view[1]} · fat={view[2]} · slice {row.get('slice_index')}"
        )
        if plane_unavailable(plane):
            mark_plane_unavailable(focused_axes, view_label, row)
        else:
            add_original(
                focused_axes[0],
                plane,
                arrays,
                row,
                arrays.get("background_mask"),
                False,
            )
            draw_bands(focused_axes[1], plane, row, arrays, peers, False)
            draw_native(focused_axes[2], plane, row, arrays, peers, False)
            draw_subdivision(
                focused_axes[3], plane, arrays, "concurrent", False, more_for(row)
            )
            draw_subdivision(
                focused_axes[4], plane, arrays, "conditional", False, more_for(row)
            )
            focused_axes[0].set_title(focused_axes[0].get_title() + "\n" + view_label)
        local_code_counts = {name: 0 for name in row["conversation"]["exchange_codes"]}
        for _, fields in peers:
            for name, value in row["conversation"]["exchange_codes"].items():
                local_code_counts[name] += int(
                    np.count_nonzero(fields.get("trace_codes", np.empty(0)) == value)
                )
        focused_handles = [
            Patch(
                color=EXCHANGE_COLORS.get(name, "#ffffff"),
                label=f"{name}: {count}",
            )
            for name, count in local_code_counts.items()
        ]
        focused_handles.extend(
            (
                Patch(color="red", label="saved background predicate"),
                Patch(color="#ffea00", label="retained barrier"),
                Patch(
                    color="#00e5ff",
                    label="original B1 bracketed trace / derived intersection",
                ),
            )
        )
        legend_axis.legend(
            handles=focused_handles, loc="center", ncol=4, fontsize=7, frameon=False
        )
        focused.suptitle(
            f"B2 same-knee conversation · {view_label}\n"
            f"recipient series UID {row['series_uid']}\n"
            f"{more_for(row)}",
            fontsize=13,
        )
        focused_path = out / f"view-{index:02d}.png"
        focused.savefig(focused_path, dpi=145)
        plt.close(focused)
        focused_views.append(
            {
                "image": focused_path.name,
                "image_sha256": sha256(focused_path.read_bytes()).hexdigest(),
                "series_uid": row["series_uid"],
                "source_plane": row.get("source_plane"),
                "slice_index": row.get("slice_index"),
                "view": row.get("view"),
                "artifact": str(artifact.resolve()),
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "donor_uids": [meta["donor_uid"] for meta, _ in peers],
                **standing(row, plane),
            }
        )

    manifest = {
        "schema": "object-conversation-b2-visuals-v1",
        "study_uid": study_uid,
        "run_path": str(run.resolve()),
        "receipt_path": str(receipt_path.resolve()),
        "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
        "renderer_path": str(Path(__file__).resolve()),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "serializer_path": str(
            (
                Path(__file__).parents[1] / "measure" / "conversation_records.py"
            ).resolve()
        ),
        "serializer_sha256": sha256(
            (
                Path(__file__).parents[1] / "measure" / "conversation_records.py"
            ).read_bytes()
        ).hexdigest(),
        "scope": "all saved conversation records in the selected study; middle acquired planes and their source UID/index links; every recorded exchange retained; no measurements rerun",
        "color_legend": {
            "red": "saved surrounding-background predicate",
            "yellow": "retained geometric barrier cells",
            "territories": "original B1 numeric territory labels",
            "cyan": "concurrent native result",
            "amber": "donor-only peer result",
            "magenta": "missing native support",
            "open cyan circles": "derived trace intersections",
        },
        "subdivision_children": [
            {
                "series_uid": row["series_uid"],
                "reading": kind,
                "children": [
                    {"child_id": child, "original_parent_id": int(parent)}
                    for child, parent in enumerate(arrays[f"b2_{kind}_parents"])
                    if child
                ],
            }
            for row, arrays, _, _, _ in prepared
            for kind in ("concurrent", "conditional")
        ],
        "parted_more_by": [
            {
                "series_uid": uid,
                "value": count,
                "code": code,
            }
            for uid, (count, code) in parted.items()
        ],
        "stages": [path.name for path in renderers],
        "overview": overview.name,
        "image": overview.name,
        "focused_views": focused_views,
        "panels": panels,
        "image_sha256": {
            path.name: sha256(path.read_bytes()).hexdigest()
            for path in [overview, *renderers]
        }
        | {entry["image"]: entry["image_sha256"] for entry in focused_views},
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument(
        "--uid", required=True, help="study UID whose saved B2 records are rendered"
    )
    parser.add_argument(
        "--out", type=Path, default=Path("data/pictures/object-toolkit/conversation-b2")
    )
    args = parser.parse_args()
    try:
        manifest = draw(args.run, args.uid, args.out)
    except ValueError as refusal:
        parser.error(str(refusal))
    print(
        json.dumps(
            {
                "series": str((args.out / manifest["overview"]).resolve()),
                "images": len(manifest["stages"]) + len(manifest["focused_views"]) + 1,
                "manifest": str((args.out / "manifest.json").resolve()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
