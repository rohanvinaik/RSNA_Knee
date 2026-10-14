"""One picture per VIEW: the acquired plane, and on it every reading that wrote at its places.

The founder, 2026-10-12: "one script that puts out five images -- one of each view, each of the
medical images that form one study, along with every single analysis lens view that has something
to say, some visual output on the original image."

Every other drawer in this directory shows ONE stage's values beside each other. This one turns the
table: one figure per SERIES (the views of a study), the selected acquired plane in grey as the
substrate of every panel, and on it one panel per reading that wrote something at that plane's
places, in route order -- the field's background split, the funnel's squint over the stack,
on the recipient of a paired plane its line-up with the partner's tile centres placed in this
plane, the funnel's first lens, every tile by its code, the funnel's tile digits, every
tile by its digit with silence drawn as silence, and on the recipient of a paired plane the
funnel's conjunction, every tile by the ordered pair of the two acquisitions' digits (the-funnel
tasks 1.2, 3a.2, 2.3, 3b.3 and 3c.2),
its air, the leg closed, the two basins and
the seam, the darkest places and the bodies; each seated lens member's digits and the members'
standing; the objects stage's low-signal and unavailable places, its territories with their peaks,
its edges by what lies across them and its traces by outcome; every ownership member's residual and
the disagreement between members; the relations stage's sample sites by pairing outcome; the
conversation's transported donor bands, its native outcomes and both subdivisions.

A reading that said nothing at this plane's places -- a lens member with no edges, a conversation
with no same-orientation partner, a profile the header's axis denied -- is NOT drawn as an empty
picture. Its panel says so in the stage's own code and words, so the sheet stays the same shape
across the views and a silence is read as a silence. A stage whose reading is not per place (the
bundles, the relations' constructions, the predicates, the output) is named in the sheet's footer
instead, so the picture never implies a stage was silent when it merely spoke elsewhere.

Nothing here measures, thresholds, segments or recounts. Every array is a saved one, validated by
the drawer that owns it: `field_frames` reconstitutes the structural reading and places its tiles in
native pixels; `lens_frames` the seated members and their standing; `partition_frames` the ownership
members and their disagreement; `pair_frames` the pairing reading; and the B1 and B2 arrays are
checked against the writer's descriptors by `field_frames.saved_array`. The colours are those
drawers' own, so a reading looks the same here as in its stage's gallery. One grey base and one
coordinate frame for every panel: native pixels, row 0 at the top, a pixel's centre at +0.5, which
is `field_frames.native_extent`'s frame, so a mask and a point land on the same place.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colormaps
from matplotlib.collections import LineCollection, PolyCollection
from matplotlib.colors import to_rgb
from matplotlib.patches import Patch

from knee.collapse.depth import LENSES
from knee.collapse.first_lens import TILE_CODES
from knee.collapse.lineup import MATCH_CODES
from knee.lenses.conjunction import CONJUNCTION_CODES
from knee.lenses.members import STANDING_CODES
from knee.objects.interiors import EDGE_KINDS, TRACE_CODES
from knee.pictures import collapse
from knee.pictures import conjunction as conjunction_pictures
from knee.pictures import depth as depth_pictures
from knee.pictures import first_lens as lens_pictures
from knee.pictures import squint_stack as squint_pictures
from knee.pictures import tiles as tile_pictures
from workbench.render import (
    conjunction_frames,
    depth_frames,
    field_frames,
    first_lens_frames,
    lens_frames,
    lineup_frames,
    object_conversation,
    pair_frames,
    partition_frames,
    squint_stack_frames,
    tile_digit_frames,
)
from workbench.render._out import PROJECT, ArgumentRefusal
from workbench.render.field_frames import native_extent, saved_array, show_native

#: The sheet: this many panels across, each this wide, at this resolution.
COLUMNS = 6
CELL_INCHES = 4.4
DPI = 110

#: What this drawing paints in, where a stage's own gallery has no colour for the reading. None of
#: them is a grey, so no stored value is ever mistaken for a reading.
BACKGROUND_COLOUR = "#ff1414"
LOW_SIGNAL_COLOUR = "#ff1f1f"
UNAVAILABLE_COLOUR = "#ff00ff"
PEAK_COLOUR = "#00e5ff"
CLAIMED_COLOUR = "#38bdf8"
RESIDUAL_COLOUR = "#d946ef"
DISAGREEMENT_COLOUR = "#facc15"
BARRIER_COLOUR = "#ffea00"

#: The objects stage's edge kinds and trace outcomes, each with a colour. Checked against the stage's
#: own vocabularies before anything is drawn, so a kind the stage adds is refused here rather than
#: drawn in no colour at all.
EDGE_KIND_COLOURS: Mapping[str, str] = {
    "low_signal": "#ef4444",
    "peer_territory": "#22c55e",
    "acquisition_missing": "#ff00ff",
    "frame": "#f59e0b",
    "unseeded_available": "#a855f7",
}
TRACE_COLOURS: Mapping[str, str] = {
    "bracketed": "#00e5ff",
    "no_dark_bracket": "#ffd166",
    "multiple_brackets": "#ff9e00",
    "missing_profile": "#ff00ff",
    "frame_clipped": "#ff00ff",
    "empty_profile": "#9ca3af",
    "invalid_measurement": "#9ca3af",
}

#: The three standings a panel can have before it is painted. `saved` means there is something to
#: draw; `silent` that the stage saved its reading and said it read nothing at this plane's places,
#: with its own code and reason; `not_saved` that this run's writer saved no such reading.
STATUSES: tuple[str, ...] = ("saved", "silent", "not_saved")

#: The drawers whose loaders and colours this sheet reuses, bound into the manifest by digest.
REUSED = (
    ("field_frames", field_frames),
    ("squint_stack_frames", squint_stack_frames),
    ("lineup_frames", lineup_frames),
    ("first_lens_frames", first_lens_frames),
    ("tile_digit_frames", tile_digit_frames),
    ("conjunction_frames", conjunction_frames),
    ("depth_frames", depth_frames),
    ("lens_frames", lens_frames),
    ("partition_frames", partition_frames),
    ("pair_frames", pair_frames),
    ("object_conversation", object_conversation),
)


@dataclass(frozen=True, slots=True)
class Panel:
    """One reading on the plane: who made it, what it is, whether it said anything, and how it is drawn.

    `paint` draws on a Matplotlib axis and returns the drawer's own status word; None for a panel
    that holds a silence, which is written in words instead. `arrays` names the saved arrays drawn.
    """

    stage: str
    reading: str
    status: str
    code: str
    why: str
    arrays: tuple[str, ...]
    paint: Callable[[object], str] | None = None


# ---------------------------------------------------------------------------------------------
# The drawing primitives: one base, one frame, and the three ways a reading sits on it.
# ---------------------------------------------------------------------------------------------


def base(axis, plane: np.ndarray) -> None:
    """The acquired plane in grey on its own scale, in native pixel coordinates; every panel starts here."""
    show_native(
        axis,
        collapse.over(plane, np.zeros(plane.shape, dtype=bool), (0.0, 0.0, 0.0)),
    )


def finish(axis, shape: tuple[int, ...]) -> None:
    """Pin the axis to the plane after every artist is on it, so no point or legend moves the frame."""
    axis.set_xlim(0, shape[1])
    axis.set_ylim(shape[0], 0)
    axis.set_aspect("equal")
    axis.set_axis_off()


def tint(axis, mask: np.ndarray, colour: str, alpha: float) -> None:
    """A boolean mask's places in one colour over the base; every other place is left as it was."""
    rgba = np.zeros((*mask.shape, 4))
    rgba[np.asarray(mask, dtype=bool)] = (*to_rgb(colour), alpha)
    axis.imshow(rgba, extent=native_extent(mask.shape), interpolation="nearest")


def paint_categories(
    axis, values: np.ndarray, colours: Mapping[int, str], alpha: float
) -> None:
    """A categorical map's places, each value in its colour; a value with no colour is left as it was."""
    rgba = np.zeros((*values.shape, 4))
    for value, colour in colours.items():
        rgba[values == value] = (*to_rgb(colour), alpha)
    axis.imshow(rgba, extent=native_extent(values.shape), interpolation="nearest")


def paint_rgba(axis, rgba: np.ndarray) -> None:
    """An RGBA image another drawer built, placed in the native frame."""
    axis.imshow(rgba, extent=native_extent(rgba.shape[:2]), interpolation="nearest")


def centred(points_rc: np.ndarray) -> np.ndarray:
    """Saved (row, column) places as (x, y) pixel centres in the native frame."""
    return np.asarray(points_rc, dtype=np.float64)[:, ::-1] + 0.5


def title(axis, stage: str, text: str) -> None:
    axis.set_title(fill(f"{stage} · {text}", width=66), fontsize=6.8, loc="left")


def legend(axis, entries: list[tuple[str, str]]) -> None:
    """A legend under the panel, one patch per (label, colour)."""
    if not entries:
        return
    axis.legend(
        handles=[Patch(facecolor=colour, label=label) for label, colour in entries],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.0),
        ncol=2,
        fontsize=5.5,
        frameon=False,
    )


def absent(stage: str, reading: str, what: str) -> Panel:
    """The panel of a reading this run's writer did not save for the series."""
    return Panel(
        stage,
        reading,
        "not_saved",
        "not_saved",
        f"this run's writer saved no {what} for this series",
        (),
    )


def same_shape(name: str, array: np.ndarray, plane: np.ndarray) -> np.ndarray:
    """A saved per-place array must be the plane's shape, else the record and the plane disagree."""
    if array.shape != plane.shape:
        raise ValueError(f"saved_array_does_not_match_the_plane:{name}")
    return array


# ---------------------------------------------------------------------------------------------
# The study and the field.
# ---------------------------------------------------------------------------------------------


def plane_of(record: dict, arrays: Mapping[str, np.ndarray]) -> np.ndarray | None:
    """The saved acquired plane, validated; None when the writer saved none."""
    if "acquired_plane" not in record["arrays"]:
        return None
    plane = saved_array(arrays, record["arrays"], "acquired_plane", 2)
    if plane.dtype.kind not in "iuf":
        raise ValueError("saved_array_representation_invalid:acquired_plane")
    return plane


def plane_panel(plane: np.ndarray, record: dict) -> Panel:
    """The plane itself, as the study stage read it and the objects stage selected it."""

    def paint(axis) -> str:
        base(axis, plane)
        title(
            axis,
            "study",
            f"the acquired plane as stored, stack index {record.get('slice_index')}; "
            "grey on this series' own scale; the file is named in the manifest",
        )
        finish(axis, plane.shape)
        return "drawn"

    return Panel(
        "study",
        "acquired plane",
        "saved",
        record["code"],
        "",
        ("acquired_plane",),
        paint,
    )


def background_panel(
    plane: np.ndarray, record: dict, arrays: Mapping[str, np.ndarray]
) -> Panel:
    """The regime's background split applied to the plane, where the field could read one."""
    annotation = record.get("background_annotation_code")
    if annotation is None:
        return absent("field", "background split", "background annotation")
    if annotation != "measured" or "background_mask" not in record["arrays"]:
        regime = record.get("regime") or {}
        return Panel(
            "field",
            "background split",
            "silent",
            str(annotation),
            str(regime.get("why", "no regime key was saved")),
            (),
        )
    mask = same_shape(
        "background_mask",
        saved_array(arrays, record["arrays"], "background_mask", 2),
        plane,
    )
    if mask.dtype.kind != "b":
        raise ValueError("saved_array_representation_invalid:background_mask")
    split = record.get("background_split")

    def paint(axis) -> str:
        base(axis, plane)
        tint(axis, mask, BACKGROUND_COLOUR, 0.55)
        title(
            axis,
            "field",
            f"places at or below the background split {split:.6g} (red), the valley of "
            "this series' own histogram",
        )
        finish(axis, plane.shape)
        return "drawn"

    return Panel(
        "field",
        "background split",
        "saved",
        "measured",
        "",
        ("background_mask",),
        paint,
    )


def squint_stack_panel(plane: np.ndarray, run: Path, record: dict) -> Panel:
    """The funnel's squint over the stack at this sheet's slice: tile medians placed by the saved bounds.

    The stack is the funnel's operation 1 (the-funnel task 1.2), read through the stack drawer's
    own loader. A record whose writer saved no stack is `not_saved`; a stack the stage did not
    make, or one that does not hold this sheet's slice, is a silence in the adapter's own code; a
    stack whose bounds end elsewhere than this plane's last row and column covers another plane,
    and is refused rather than drawn over the wrong picture.
    """
    if "squint_stack" not in record:
        return absent("field", "squint stack", "squint stack")
    _, frame = squint_stack_frames.saved_stack(run, record)
    index = record.get("slice_index")
    standing = squint_pictures.walk_standing(frame.code, index, frame.slices)
    names = record["squint_stack"]["arrays"]
    arrays = (names["median"], names["bounds_rc"])
    if (
        standing != "squinted"
        or frame.median is None
        or frame.bounds_rc is None
        or not frame.median.size
    ):
        return Panel(
            "field",
            "squint stack",
            "silent",
            str(frame.code),
            f"{standing}: {frame.why}",
            arrays,
        )
    bounds = frame.bounds_rc
    if (int(bounds[-1, -1, 1]), int(bounds[-1, -1, 3])) != plane.shape:
        raise ValueError("saved_squint_stack_covers_another_plane")
    median = frame.median[int(index)]
    edges = field_frames.tile_edges(bounds)
    tile_rows, tile_columns = frame.tile_shape_rc or (0, 0)

    def paint(axis) -> str:
        base(axis, plane)
        colours = colormaps["gray"].with_extremes(bad=field_frames.UNREAD_COLOUR)
        axis.pcolormesh(*edges, median, cmap=colours, alpha=0.6)
        title(
            axis,
            "field",
            f"the funnel's squint over the stack at stack index {index}: tile medians at "
            f"{frame.tile_mm:g} mm ({tile_rows}x{tile_columns} px, "
            f"{median.shape[0]}x{median.shape[1]} tiles) placed by the stack's own native "
            f"bounds; {frame.slices} slices squinted; a fuchsia tile holds no finite pixel",
        )
        finish(axis, plane.shape)
        return "drawn"

    return Panel("field", "squint stack", "saved", frame.code, "", arrays, paint)


def lineup_panel(plane: np.ndarray, run: Path, record: dict) -> Panel:
    """The funnel's line-up at this sheet's slice: the recipient's tiles by match code, the partner's centres over them.

    The line-up is the funnel's operation 3a (the-funnel task 3a.2), read through the line-up
    drawer's own reader, which finds the partner's saved stack through the run's receipt. A record
    whose writer saved no line-up is `not_saved`: a partner, a solitary or a surplus series
    carries none, and that is the silence it is. A slice the picture cannot show is a silence in
    the adapter's own code; a lined-up slice whose plane frame the writer did not save is a
    silence in this drawer's; a line-up whose recipient grid ends elsewhere than this plane's last
    row and column covers another plane, and is refused rather than drawn over the wrong picture.
    """
    if "lineup" not in record:
        return absent("field", "line-up", "line-up")
    drawing = lineup_frames.saved_lineup(
        run,
        record,
        lineup_frames.partner_record(lineup_frames.receipt_records(run), record),
    )
    panels = drawing.panels
    at = panels.at
    names = record["lineup"]["arrays"]
    arrays = (
        names["match_codes"],
        names["partner_tile"],
        names["partner_slice"],
        names["slab_codes"],
    )
    if at.standing != "lined_up":
        return Panel(
            "field",
            "line-up",
            "silent",
            str(panels.code),
            f"{at.standing}: {panels.why}",
            arrays,
        )
    if (
        drawing.bounds_rc is None
        or at.recipient_centres_rc is None
        or at.partner_centres_rc is None
        or at.partner_tile is None
        or at.match_codes is None
    ):
        return Panel(
            "field",
            "line-up",
            "silent",
            str(panels.code),
            f"{lineup_frames.PLANE_NOT_SAVED}: {lineup_frames.PLANE_NOT_SAVED_WORDS}",
            arrays,
        )
    bounds = drawing.bounds_rc
    if (int(bounds[-1, -1, 1]), int(bounds[-1, -1, 3])) != plane.shape:
        raise ValueError("saved_lineup_covers_another_plane")
    edges = field_frames.tile_edges(bounds)
    recipient_centres, partner_tile, match_codes, partner_centres = (
        at.recipient_centres_rc,
        at.partner_tile,
        at.match_codes,
        at.partner_centres_rc,
    )
    counts = ", ".join(
        f"{name} {n}" for name, n in lineup_frames.match_counts(match_codes).items()
    )
    partner_tail = str(panels.partner_uid)[-8:]

    def paint(axis) -> str:
        base(axis, plane)
        entries = []
        for value, name in enumerate(MATCH_CODES):
            mask = match_codes == value
            if mask.any():
                colour = lineup_frames.MATCH_COLOURS[name]
                field_frames.overlay(
                    axis, edges, mask, colour, lineup_frames.TINT_ALPHA
                )
                entries.append((f"{name} ({int(mask.sum())})", colour))
        segments = lineup_frames.scootch_segments(
            recipient_centres, partner_tile, partner_centres
        )
        if len(segments):
            axis.add_collection(
                LineCollection(
                    list(segments),
                    colors=lineup_frames.SCOOTCH_COLOUR,
                    linewidths=0.6,
                )
            )
        placed = partner_centres.reshape(-1, 2)
        finite = np.isfinite(placed).all(axis=1)
        points = centred(placed[finite])
        axis.scatter(
            points[:, 0],
            points[:, 1],
            marker="+",
            s=16,
            c=lineup_frames.PARTNER_COLOUR,
            linewidths=0.6,
        )
        title(
            axis,
            "field",
            f"the funnel's line-up at stack index {at.index}: the recipient's tiles tinted "
            f"by match code ({counts}); the partner's (...{partner_tail}) tile centres at "
            f"its slice {at.partner_index} ({at.slab_code}) as cyan +; a yellow segment "
            f"from each tile centre to its matched partner centre, the scootch; match bar "
            f"{lineup_frames.number(panels.half_tile_mm, 'mm')}",
        )
        legend(
            axis,
            [
                *entries,
                ("+ partner tile centre", lineup_frames.PARTNER_COLOUR),
                ("segment to the match", lineup_frames.SCOOTCH_COLOUR),
            ],
        )
        finish(axis, plane.shape)
        return "drawn"

    return Panel("field", "line-up", "saved", str(panels.code), "", arrays, paint)


def first_lens_panel(plane: np.ndarray, run: Path, record: dict) -> Panel:
    """The funnel's first lens at this sheet's slice: every tile by its code, placed by the stack's saved bounds.

    The lens is the funnel's operation 2 (the-funnel task 2.3), read through the lens drawer's
    own reader, which finds the squint stack's saved bounds on the same record. A record whose
    writer saved no lens is `not_saved`; a slice the picture cannot show is a silence in the
    adapter's own code; a lens whose grid ends elsewhere than this plane's last row and column
    covers another plane, and is refused rather than drawn over the wrong picture. Background
    is drawn red at a low alpha, undecided amber, a tile with no finite pixel grey, and
    not_background is left untouched, in the lens drawer's own colours.
    """
    if "first_lens" not in record:
        return absent("field", "first lens", "first lens")
    _, frame = first_lens_frames.saved_lens(run, record)
    index = record.get("slice_index")
    standing = lens_pictures.walk_standing(frame.code, index, frame.slices)
    names = record["first_lens"]["arrays"]
    arrays = (names["codes"],)
    if (
        standing != "named"
        or frame.codes is None
        or frame.bounds_rc is None
        or not frame.codes.size
    ):
        return Panel(
            "field",
            "first lens",
            "silent",
            str(frame.code),
            f"{standing}: {frame.why}",
            arrays,
        )
    bounds = frame.bounds_rc
    if (int(bounds[-1, -1, 1]), int(bounds[-1, -1, 3])) != plane.shape:
        raise ValueError("saved_first_lens_covers_another_plane")
    codes = frame.codes[int(index)]
    edges = field_frames.tile_edges(bounds)
    counts = ", ".join(
        f"{name} {n}" for name, n in first_lens_frames.tile_counts(codes).items()
    )
    split = first_lens_frames.number(frame.split)

    def paint(axis) -> str:
        base(axis, plane)
        entries = []
        for value, name in enumerate(TILE_CODES):
            colour = first_lens_frames.CODE_COLOURS[name]
            mask = codes == value
            if colour is None or not mask.any():
                continue
            field_frames.overlay(
                axis, edges, mask, colour, first_lens_frames.CODE_ALPHAS[name]
            )
            entries.append((f"{name} ({int(mask.sum())})", colour))
        title(
            axis,
            "field",
            f"the funnel's first lens at stack index {index}: every tile by its code under "
            f"split {split}, rule {frame.rule_version} ({frame.code}); background red at "
            f"a low alpha (cleared), undecided amber (in play), not background untouched, "
            f"no finite pixel grey; at this slice {counts}",
        )
        legend(axis, entries)
        finish(axis, plane.shape)
        return "drawn"

    return Panel("field", "first lens", "saved", str(frame.code), "", arrays, paint)


def tile_digits_panel(plane: np.ndarray, run: Path, record: dict) -> Panel:
    """The funnel's tile digits at this sheet's slice: every tile by its digit, silence as silence, placed by the stack's saved bounds.

    The digits are the funnel's operation 3b (the-funnel task 3b.3), read through the digit
    drawer's own reader, which finds the squint stack's saved bounds on the same record. A
    record whose writer saved no digits is `not_saved`; a slice the picture cannot show is a
    silence in the adapter's own code; digits whose grid ends elsewhere than this plane's last
    row and column cover another plane, and are refused rather than drawn over the wrong
    picture. Below, at and above are drawn in the lens gallery's three colours and every
    silence in one neutral tone, in the digit drawer's own colours; a series whose oracle gave
    no pair of edges draws every tile as silence and the title says which word it gave.
    """
    if "tile_digits" not in record:
        return absent("lenses", "tile digits", "tile digits")
    _, frame = tile_digit_frames.saved_digits(run, record)
    index = record.get("slice_index")
    standing = tile_pictures.walk_standing(frame.code, index, frame.slices)
    names = record["tile_digits"]["arrays"]
    arrays = (names["codes"], names["digits"])
    if (
        standing != "named"
        or frame.codes is None
        or frame.bounds_rc is None
        or not frame.codes.size
    ):
        return Panel(
            "lenses",
            "tile digits",
            "silent",
            str(frame.code),
            f"{standing}: {frame.why}",
            arrays,
        )
    bounds = frame.bounds_rc
    if (int(bounds[-1, -1, 1]), int(bounds[-1, -1, 3])) != plane.shape:
        raise ValueError("saved_tile_digits_cover_another_plane")
    codes = frame.codes[int(index)]
    edges = field_frames.tile_edges(bounds)
    counts = tile_digit_frames.digit_counts(codes)
    read = ", ".join(f"{name} {counts[name]}" for name in tile_digit_frames.READ_VALUES)
    silent = tile_digit_frames.silent_count(counts)
    low = tile_digit_frames.number(frame.low_edge)
    high = tile_digit_frames.number(frame.high_edge)

    def paint(axis) -> str:
        base(axis, plane)
        entries = []
        for name, value in tile_digit_frames.READ_VALUES.items():
            mask = codes == value
            if not mask.any():
                continue
            colour = tile_digit_frames.DIGIT_COLOURS[name]
            field_frames.overlay(
                axis, edges, mask, colour, tile_digit_frames.DIGIT_ALPHA
            )
            entries.append((f"{name} ({int(mask.sum())})", colour))
        silence = tile_digit_frames.silence_mask(codes)
        if silence.any():
            field_frames.overlay(
                axis,
                edges,
                silence,
                tile_digit_frames.SILENCE_COLOUR,
                tile_digit_frames.SILENCE_ALPHA,
            )
            entries.append(
                (f"silence ({int(silence.sum())})", tile_digit_frames.SILENCE_COLOUR)
            )
        title(
            axis,
            "lenses",
            f"the funnel's tile digits at stack index {index}: every tile against this "
            f"series' own kept-tile edges {low} and {high} ({frame.population_count} tiles "
            f"counted under a bar of {frame.minimum_population}; {frame.code}); below blue, "
            f"at green, above amber, silence grey; at this slice {read}, silence {silent}",
        )
        legend(axis, entries)
        finish(axis, plane.shape)
        return "drawn"

    return Panel("lenses", "tile digits", "saved", str(frame.code), "", arrays, paint)


#: What a sheet says of a series that carries no conjunction: the record holds no such key
#: because the conjunction rides on the recipient of a paired plane only.
NO_CONJUNCTION_WORDS = (
    "no conjunction rides on this series: this run's writer saved none for it, as on the "
    "fat-bright partner of a paired plane and on a solitary or surplus series; the "
    "conjunction is carried on the fat-dark recipient of a paired plane"
)


def conjunction_panel(plane: np.ndarray, run: Path, record: dict) -> Panel:
    """The funnel's conjunction at this sheet's slice: every tile of the recipient by its code, placed by the stack's saved bounds.

    The conjunction is the funnel's operation 3c (the-funnel task 3c.2), read through the
    conjunction drawer's own reader, which finds the recipient's squint stack's saved bounds on
    the same record. It rides on the recipient of a paired plane only, so a record with no
    conjunction (a partner, a solitary or a surplus series, or a run whose writer saved none)
    has a panel that says in words that no conjunction rides on this series. A slice the
    picture cannot show is a silence in the adapter's own code; a conjunction whose grid ends
    elsewhere than this plane's last row and column covers another plane, and is refused rather
    than drawn over the wrong picture. The nine read pairs are drawn in the conjunction drawer's
    nine colours and the two silences and the unmatched tile in its neutral tones.
    """
    if "conjunction" not in record:
        return Panel(
            "lenses", "conjunction", "not_saved", "not_saved", NO_CONJUNCTION_WORDS, ()
        )
    _, frame = conjunction_frames.saved_conjunction(run, record)
    index = record.get("slice_index")
    standing = conjunction_pictures.walk_standing(frame.code, index, frame.slices)
    names = record["conjunction"]["arrays"]
    arrays = (names["codes"],)
    if (
        standing != "named"
        or frame.codes is None
        or frame.bounds_rc is None
        or not frame.codes.size
    ):
        return Panel(
            "lenses",
            "conjunction",
            "silent",
            str(frame.code),
            f"{standing}: {frame.why}",
            arrays,
        )
    bounds = frame.bounds_rc
    if (int(bounds[-1, -1, 1]), int(bounds[-1, -1, 3])) != plane.shape:
        raise ValueError("saved_conjunction_covers_another_plane")
    codes = frame.codes[int(index)]
    edges = field_frames.tile_edges(bounds)
    counts = conjunction_frames.code_counts(codes)
    present = ", ".join(f"{name} {n}" for name, n in counts.items() if n)
    partner_tail = str(frame.partner_uid)[-8:]

    def paint(axis) -> str:
        base(axis, plane)
        entries = []
        for value, name in enumerate(CONJUNCTION_CODES):
            mask = codes == value
            if not mask.any():
                continue
            colour = conjunction_frames.CODE_COLOURS[name]
            field_frames.overlay(
                axis, edges, mask, colour, conjunction_frames.CODE_ALPHAS[name]
            )
            entries.append((f"{name} ({int(mask.sum())})", colour))
        title(
            axis,
            "lenses",
            f"the funnel's conjunction at stack index {index}: the partner's "
            f"(...{partner_tail}) digit and this series' own at each tile, read together "
            f"through the line-up as <partner>_<own> ({frame.code}); the nine pairs in nine "
            f"colours, the silences and unmatched tiles in greys, the refusal magenta; at "
            f"this slice {present}",
        )
        legend(axis, entries)
        finish(axis, plane.shape)
        return "drawn"

    return Panel("lenses", "conjunction", "saved", str(frame.code), "", arrays, paint)


#: The colour a sheet's slice is framed in when a lens stands at it, and when none does; neither
#: a grey, so the frame is never read as a value of the plane.
CHOSEN_COLOUR = "#16a34a"
UNCHOSEN_COLOUR = "#dc2626"


def depth_panel(plane: np.ndarray, run: Path, record: dict) -> Panel:
    """The funnel's depth collapse: where each lens stands, the chosen slices, and whether this sheet's slice is one.

    The collapse is the funnel's operation 4 (the-funnel task 4.5), read through the depth
    drawer's own reader, which finds the squint stack on the same record. A record whose writer
    saved no collapse is `not_saved`; a collapse the stage did not make, or a sheet's slice the
    collapse does not hold, is a silence in the adapter's own code. Else the plane is drawn with
    a frame in one of two colours, green when this sheet's slice is one a lens stands at and red
    when it is not, and the title names each lens's slice with its word and the chosen slices:
    nothing is measured, and the one question the panel answers is a membership read off the
    saved choices.
    """
    if "depth" not in record:
        return absent("field", "depth collapse", "depth collapse")
    _, frame = depth_frames.saved_depth(run, record)
    index = record.get("slice_index")
    standing = depth_pictures.sheet_standing(
        frame.code, index, frame.slices, frame.chosen_slices
    )
    names = record["depth"]["arrays"]
    arrays = (*(names[lens] for lens in LENSES), names["chosen_slices"])
    if standing not in ("chosen", "unchosen"):
        return Panel(
            "field",
            "depth collapse",
            "silent",
            str(frame.code),
            f"{standing}: {frame.why}",
            arrays,
        )
    stood = "; ".join(depth_frames.standing_words(s) for s in frame.standings)
    chosen = ", ".join(str(held) for held in frame.chosen_slices) or "none"
    colour = CHOSEN_COLOUR if standing == "chosen" else UNCHOSEN_COLOUR
    membership = "among" if standing == "chosen" else "not among"

    def paint(axis) -> str:
        from matplotlib.patches import Rectangle

        base(axis, plane)
        axis.add_patch(
            Rectangle(
                (0.0, 0.0),
                float(plane.shape[1]),
                float(plane.shape[0]),
                fill=False,
                edgecolor=colour,
                linewidth=3.0,
            )
        )
        title(
            axis,
            "field",
            f"the funnel's depth collapse under a bar of {frame.minimum_valid} "
            f"({frame.code}): {stood}; chosen slices {chosen}; this sheet's slice {index} "
            f"is {membership} them (frame {'green' if standing == 'chosen' else 'red'})",
        )
        legend(
            axis,
            [
                ("this slice is a chosen one", CHOSEN_COLOUR),
                ("this slice is not", UNCHOSEN_COLOUR),
            ],
        )
        finish(axis, plane.shape)
        return "drawn"

    return Panel("field", "depth collapse", "saved", str(frame.code), "", arrays, paint)


def structure_panels(run: Path, record: dict) -> list[Panel]:
    """The field's structural reading, each of its four pictures drawn by the field gallery's own code."""
    _, squint = field_frames.saved_field(run, record)
    drawing = field_frames.saved_structure(
        run, record, squint.bounds_rc, squint.tile_shape_rc
    )
    if drawing is None:
        return [absent("field", "structural reading", "structural reading")]
    frame = drawing.frame
    if frame.air.size == 0:
        return [
            Panel("field", "structural reading", "silent", frame.code, frame.why, ())
        ]
    names = record["structure"]["arrays"]

    def painter(draw, *extra) -> Callable[[object], str]:
        """The field gallery's own drawing of one reading, retitled for this sheet.

        The gallery sets a centred title; it is cleared, and this sheet's left title carries its
        words, so a panel never shows two titles.
        """

        def paint(axis) -> str:
            status = draw(axis, drawing, frame.plane, *extra)
            words = axis.get_title().replace("\n", " ")
            axis.set_title("")
            axis.set_title(fill("field · " + words, width=66), fontsize=6.8, loc="left")
            axis.set_axis_off()
            return status

        return paint

    def tiles(draw_fallback, layers, text: str) -> Callable[[object], str]:
        """A tile reading on the plane: the tiles over the grey base, in native pixels, where the
        saved squint bounds place them (`drawing.bounds_rc`, `field_frames.tile_placement`); else
        the field gallery's own drawing on the tile grid, whose title says why."""
        if drawing.bounds_rc is None:
            return painter(draw_fallback)
        edges = field_frames.tile_edges(drawing.bounds_rc)

        def paint(axis) -> str:
            base(axis, frame.plane)
            for mask, colour, alpha in layers():
                field_frames.overlay(axis, edges, mask, colour, alpha)
            title(axis, "field", text)
            finish(axis, frame.plane.shape)
            return "drawn"

        return paint

    # The two silences `field_frames.draw_basins` and `draw_dark_and_bodies` name: no squint was
    # read, or no tile carries a basin label. Named here with the stage's own reason, so the panel
    # is a silence in words and never an empty picture.
    tiles_read = frame.inside.size > 0
    basins_read = tiles_read and bool(frame.basins.any())

    def basin_layers():
        return [
            (frame.basins == 1, field_frames.BASIN_COLOURS[0], 0.35),
            (frame.basins == 2, field_frames.BASIN_COLOURS[1], 0.35),
            (frame.seam, field_frames.SEAM_COLOUR, 0.9),
        ]

    def body_layers():
        ranks = [int(value) for value in np.unique(frame.bodies) if value > 0]
        colours = field_frames.BODY_COLOURS
        return [
            *(
                (frame.bodies == rank, colours[(rank - 1) % len(colours)], 0.35)
                for rank in ranks
            ),
            (frame.dark, field_frames.DARK_COLOUR, 0.6),
        ]

    basins = (
        tiles(
            field_frames.draw_basins,
            basin_layers,
            "the two basins (blue 1, amber 2) seeded by the header's axis alone, and the "
            "seam between them (green); tiles placed in native pixels by the saved squint "
            "bounds",
        )
        if basins_read
        else None
    )
    bodies = (
        tiles(
            field_frames.draw_dark_and_bodies,
            body_layers,
            f"the darkest places (cyan, at or below {field_frames.number(frame.dark_level)}) "
            f"and the largest bright bodies by rank "
            f"({frame.counts.get('bodies_total', 'not saved')} in all); tiles placed in "
            "native pixels by the saved squint bounds",
        )
        if tiles_read
        else None
    )
    pictures = (
        ("the air", painter(field_frames.draw_air), ("air",)),
        ("the leg, closed", painter(field_frames.draw_leg, frame.leg), ("leg",)),
        ("the two basins and the seam", basins, ("basins", "seam")),
        ("the darkest places and the bright bodies", bodies, ("dark", "bodies")),
    )
    return [
        Panel(
            "field",
            reading,
            "saved" if paint is not None else "silent",
            frame.code,
            frame.why,
            tuple(names[short] for short in shorts),
            paint,
        )
        for reading, paint, shorts in pictures
    ]


# ---------------------------------------------------------------------------------------------
# The lenses.
# ---------------------------------------------------------------------------------------------


def member_panel(plane: np.ndarray, member: dict, frame, silent_digit: int) -> Panel:
    """One seated member's digits at every place, in the lens gallery's colours."""
    reading = f"member {member['population']}"
    arrays = (member["codes_array"], member["digits_array"])
    # A member whose own code is not `present` read nothing at this plane, whatever map was saved
    # for it (a member with no edges saves a map of silences): it is a silence, in its own words.
    if not frame.digits.size or frame.code != "present":
        return Panel("lenses", reading, "silent", frame.code, frame.why, arrays)
    digits = same_shape(member["digits_array"], frame.digits, plane)
    colours = {
        -1: lens_frames.COLORS[0],
        0: lens_frames.COLORS[1],
        1: lens_frames.COLORS[2],
        int(silent_digit): lens_frames.COLORS[3],
    }

    def paint(axis) -> str:
        base(axis, plane)
        paint_categories(axis, digits, colours, 0.4)
        title(
            axis,
            "lenses",
            f"{reading}: each place's digit against this series' own stored-unit edges "
            f"{frame.low_edge} and {frame.high_edge}; normalisation {frame.normalisation}",
        )
        legend(
            axis,
            list(zip(lens_frames.LEGEND, lens_frames.COLORS, strict=True)),
        )
        finish(axis, plane.shape)
        return "drawn"

    return Panel("lenses", reading, "saved", frame.code, frame.why, arrays, paint)


def standing_panel(plane: np.ndarray, standing, saved_lenses: dict) -> Panel:
    """What the seated members jointly said per place; a dissent is drawn as a dissent."""
    arrays = (saved_lenses["standings_array"],)
    if not standing.standings.size:
        return Panel(
            "lenses",
            "standing of the members",
            "silent",
            "no_standing_plane",
            "no standing plane was saved for the selected plane",
            arrays,
        )
    standings = same_shape(arrays[0], standing.standings, plane)
    colours = dict(enumerate(lens_frames.STANDING_COLORS))
    counts = ", ".join(
        f"{name}={count}"
        for name, count in zip(STANDING_CODES, standing.counts, strict=True)
    )

    def paint(axis) -> str:
        base(axis, plane)
        paint_categories(axis, standings, colours, 0.4)
        title(
            axis,
            "lenses",
            f"what the members jointly said at each place, {standing.populations[0]} "
            f"and {standing.populations[1]}; whole-volume counts {counts}; nothing here "
            "resolves a dissent",
        )
        legend(
            axis, list(zip(STANDING_CODES, lens_frames.STANDING_COLORS, strict=True))
        )
        finish(axis, plane.shape)
        return "drawn"

    return Panel(
        "lenses", "standing of the members", "saved", "present", "", arrays, paint
    )


def lens_panels(plane: np.ndarray, run: Path, record: dict) -> list[Panel]:
    """Every seated member, then their standing, through the lens gallery's own loader."""
    if "lenses" not in record:
        return [absent("lenses", "seated members", "lens reading")]
    _, members, standing = lens_frames.saved_panels(run, record)
    silent_digit = record["lenses"]["digit_silence"]
    panels = [
        member_panel(plane, member, frame, silent_digit) for member, frame in members
    ]
    panels.append(standing_panel(plane, standing, record["lenses"]))
    return panels


# ---------------------------------------------------------------------------------------------
# The objects: B1's interiors, and B2's conversation.
# ---------------------------------------------------------------------------------------------


def segments_by_name(
    axis, segments: np.ndarray, codes: np.ndarray, names: Mapping[int, str], colours
) -> list[tuple[str, str]]:
    """Line segments drawn per named code, in that name's colour; returns the legend entries."""
    entries = []
    for value in (int(v) for v in np.unique(codes)):
        name = names[value]
        selected = codes == value
        axis.add_collection(
            LineCollection(segments[selected], colors=colours[name], linewidths=0.55)
        )
        entries.append((f"{name} ({int(selected.sum())})", colours[name]))
    return entries


def object_panels(
    plane: np.ndarray, record: dict, arrays: Mapping[str, np.ndarray]
) -> list[Panel]:
    """B1's per-place readings: low signal and unavailable, territories with peaks, edges, traces."""
    if "interiors" not in record:
        return [absent("objects", "interiors", "interior reading")]
    descriptors = record["arrays"]
    dark = same_shape("b1_dark", saved_array(arrays, descriptors, "b1_dark", 2), plane)
    available = same_shape(
        "b1_available", saved_array(arrays, descriptors, "b1_available", 2), plane
    )
    labels = same_shape(
        "b1_labels", saved_array(arrays, descriptors, "b1_labels", 2), plane
    )
    markers = same_shape(
        "b1_markers", saved_array(arrays, descriptors, "b1_markers", 2), plane
    )
    points = saved_array(arrays, descriptors, "b1_edge_points_rc", 2)
    normals = saved_array(arrays, descriptors, "b1_edge_normals_rc", 2)
    kinds = saved_array(arrays, descriptors, "b1_edge_kinds", 1)
    codes = saved_array(arrays, descriptors, "b1_trace_codes", 1)
    traces = saved_array(arrays, descriptors, "b1_trace_points_rc", 2)
    if not len(points) == len(normals) == len(kinds) == len(codes) == len(traces):
        raise ValueError("b1_edge_arrays_do_not_match")
    saved = record["interiors"]
    code, why = saved["code"], saved["scope"]
    kind_names = {int(v): k for k, v in saved["edge_kind_codes"].items()}
    trace_names = {int(v): k for k, v in saved["trace_codes"].items()}
    for name in (*kind_names.values(), *trace_names.values()):
        if name not in EDGE_KIND_COLOURS and name not in TRACE_COLOURS:
            raise ValueError(f"saved_objects_vocabulary_uncoloured:{name}")
    segments = object_conversation.edge_segments(points, normals) + 0.5
    peaks = [
        (int(region), np.argwhere(markers == region).mean(axis=0))
        for region in np.unique(markers)
        if region
    ]
    territory_count = int(np.count_nonzero(np.unique(labels)))

    def paint_low(axis) -> str:
        base(axis, plane)
        tint(axis, dark, LOW_SIGNAL_COLOUR, 0.6)
        tint(axis, ~available, UNAVAILABLE_COLOUR, 0.8)
        title(
            axis,
            "objects",
            "B1's surrounding information: measured low signal (red) and places the stage "
            "could not read (magenta)",
        )
        finish(axis, plane.shape)
        return "drawn"

    def paint_territories(axis) -> str:
        base(axis, plane)
        paint_rgba(axis, object_conversation.territory_rgba(labels))
        for index, (row, column) in peaks:
            axis.plot(column + 0.5, row + 0.5, "+", color=PEAK_COLOUR, markersize=7)
            axis.text(
                column + 0.5,
                row + 0.5,
                f" {index}",
                color="white",
                fontsize=6,
                ha="left",
                va="center",
                clip_on=True,
            )
        title(
            axis,
            "objects",
            f"B1's {territory_count} territories, each an indexed extent and not a name, "
            "with the interior peak (cyan +) that seeded it",
        )
        finish(axis, plane.shape)
        return "drawn"

    def paint_edges(axis) -> str:
        base(axis, plane)
        entries = segments_by_name(axis, segments, kinds, kind_names, EDGE_KIND_COLOURS)
        title(
            axis,
            "objects",
            "B1's territory edges, each coloured by what lies ACROSS it",
        )
        legend(axis, entries)
        finish(axis, plane.shape)
        return "drawn"

    def paint_traces(axis) -> str:
        base(axis, plane)
        entries = segments_by_name(axis, segments, codes, trace_names, TRACE_COLOURS)
        bracketed = codes == saved["trace_codes"]["bracketed"]
        if bracketed.any():
            found = centred(traces[bracketed])
            axis.scatter(found[:, 0], found[:, 1], s=0.8, c=TRACE_COLOURS["bracketed"])
        title(
            axis,
            "objects",
            "B1's native profile traces across each edge, by outcome; a bracketed trace's "
            "dark-band midpoint is the cyan point",
        )
        legend(axis, entries)
        finish(axis, plane.shape)
        return "drawn"

    pictures = (
        ("low signal and unavailable", paint_low, ("b1_dark", "b1_available")),
        ("territories and their peaks", paint_territories, ("b1_labels", "b1_markers")),
        (
            "edges by what lies across them",
            paint_edges,
            ("b1_edge_points_rc", "b1_edge_normals_rc", "b1_edge_kinds"),
        ),
        (
            "traces by outcome",
            paint_traces,
            ("b1_edge_points_rc", "b1_trace_codes", "b1_trace_points_rc"),
        ),
    )
    return [
        Panel("objects", reading, "saved", code, why, names, paint)
        for reading, paint, names in pictures
    ]


def exchange_arrays(
    arrays: Mapping[str, np.ndarray], descriptors: dict, index: int
) -> dict[str, np.ndarray]:
    """One exchange's drawn arrays, validated: the donor's quads, its places, codes and derived traces."""
    prefix = f"b2_exchange{index}_"
    return {
        "donor_quads_rc": saved_array(
            arrays, descriptors, prefix + "donor_quads_rc", 3
        ),
        "points_rc": saved_array(arrays, descriptors, prefix + "points_rc", 2),
        "trace_codes": saved_array(arrays, descriptors, prefix + "trace_codes", 1),
        "derived_trace_rc": saved_array(
            arrays, descriptors, prefix + "derived_trace_rc", 2
        ),
    }


def subdivision_panel(
    plane: np.ndarray,
    record: dict,
    arrays: Mapping[str, np.ndarray],
    kind: str,
    originals: int | None,
) -> Panel:
    """One of the conversation's two subdivisions, with its retained barrier, over the plane."""
    descriptors = record["arrays"]
    names = (f"b2_{kind}_labels", f"b2_{kind}_parents", f"b2_{kind}_barrier")
    labels = same_shape(names[0], saved_array(arrays, descriptors, names[0], 2), plane)
    parents = saved_array(arrays, descriptors, names[1], 1)
    barrier = same_shape(names[2], saved_array(arrays, descriptors, names[2], 2), plane)
    if barrier.dtype.kind != "b":
        raise ValueError(f"saved_array_representation_invalid:{names[2]}")
    if int(labels.max(initial=0)) >= len(parents):
        raise ValueError(f"saved_subdivision_parents_too_short:{kind}")
    rgba, colours = object_conversation.subdivision_rgba(labels, parents)
    children = len(colours)
    cells = int(barrier.sum())
    saved = record["conversation"]
    parent_of = {child: int(parents[child]) for child in colours}
    from_originals = (
        f"{originals} original" if originals is not None else "originals not saved"
    )

    def paint(axis) -> str:
        base(axis, plane)
        paint_rgba(axis, rgba)
        tint(axis, barrier, BARRIER_COLOUR, 0.95)
        for child, parent in parent_of.items():
            pixels = np.argwhere(labels == child)
            if len(pixels) >= 36:
                row, column = pixels.mean(axis=0)
                axis.text(
                    column + 0.5,
                    row + 0.5,
                    f"{parent}.{child}",
                    color="white",
                    fontsize=5,
                    ha="center",
                    va="center",
                    weight="bold",
                    clip_on=True,
                )
        title(
            axis,
            "objects",
            f"the conversation's {kind} subdivision: {from_originals} → {children} children, "
            f"labelled parent.child; {cells} retained barrier cells (yellow); "
            f"conversation {saved['code']}",
        )
        finish(axis, plane.shape)
        return "drawn"

    return Panel(
        "objects", f"{kind} subdivision", "saved", saved["code"], "", names, paint
    )


def conversation_panels(
    plane: np.ndarray,
    record: dict,
    arrays: Mapping[str, np.ndarray],
    originals: int | None,
) -> list[Panel]:
    """B2's per-place readings: the donors' bands, the native outcomes, and both subdivisions."""
    if "conversation" not in record:
        return [absent("objects", "conversation", "conversation")]
    saved = record["conversation"]
    descriptors = record["arrays"]
    codebook: dict[str, int] = saved["exchange_codes"]
    code_names = {int(value): name for name, value in codebook.items()}
    exchanges = [
        (metadata, exchange_arrays(arrays, descriptors, index))
        for index, metadata in enumerate(saved["exchanges"])
    ]
    partner = ", ".join(meta["donor_uid"][-8:] for meta, _ in exchanges)
    no_partner = Panel(
        "objects",
        "donor bands",
        "silent",
        saved["code"],
        "no same-orientation partner: nothing was transported into this plane",
        (),
    )
    panels: list[Panel] = []
    if not exchanges:
        panels.append(no_partner)
        panels.append(
            Panel(
                "objects",
                "native outcomes",
                "silent",
                saved["code"],
                no_partner.why,
                (),
            )
        )
    else:
        names = tuple(
            f"b2_exchange{index}_{name}"
            for index in range(len(exchanges))
            for name in ("donor_quads_rc", "points_rc", "trace_codes")
        )

        def paint_bands(axis) -> str:
            base(axis, plane)
            present: set[int] = set()
            for _meta, fields in exchanges:
                quads, codes = fields["donor_quads_rc"], fields["trace_codes"]
                if not len(quads):
                    continue
                colours = [
                    object_conversation.EXCHANGE_COLORS.get(
                        code_names.get(int(code), ""), "#ffffff"
                    )
                    for code in codes
                ]
                present.update(int(code) for code in np.unique(codes))
                axis.add_collection(
                    PolyCollection(
                        quads[:, :, ::-1] + 0.5,
                        facecolors=colours,
                        edgecolors=colours,
                        alpha=0.3,
                        linewidths=0.3,
                    )
                )
            title(
                axis,
                "objects",
                f"the conversation: the donor's ({partner}) bounded dark bands transported "
                "into this plane, each coloured by what THIS plane said at the same place",
            )
            legend(
                axis,
                [
                    (name, object_conversation.EXCHANGE_COLORS.get(name, "#ffffff"))
                    for name, value in codebook.items()
                    if value in present
                ],
            )
            finish(axis, plane.shape)
            return "drawn"

        def paint_native(axis) -> str:
            base(axis, plane)
            entries = []
            for _meta, fields in exchanges:
                codes, points = fields["trace_codes"], centred(fields["points_rc"])
                for name, value in codebook.items():
                    selected = codes == value
                    if not selected.any():
                        continue
                    colour = object_conversation.EXCHANGE_COLORS.get(name, "#ffffff")
                    axis.scatter(
                        points[selected, 0], points[selected, 1], s=3, c=colour
                    )
                    entries.append((f"{name} ({int(selected.sum())})", colour))
                trace = fields["derived_trace_rc"]
                resolved = (
                    np.isfinite(trace).all(axis=1)
                    if len(trace)
                    else np.zeros(0, dtype=bool)
                )
                if resolved.any():
                    found = centred(trace[resolved])
                    axis.scatter(
                        found[:, 0],
                        found[:, 1],
                        s=8,
                        facecolors="none",
                        edgecolors=object_conversation.EXCHANGE_COLORS["concurrent"],
                        linewidths=0.4,
                    )
                    entries.append(
                        (
                            f"derived concurrent trace ({int(resolved.sum())})",
                            object_conversation.EXCHANGE_COLORS["concurrent"],
                        )
                    )
            title(
                axis,
                "objects",
                "the conversation's native outcomes at the donor's places, and the derived "
                "traces where both readings concur (open circles)",
            )
            legend(axis, entries)
            finish(axis, plane.shape)
            return "drawn"

        panels.append(
            Panel(
                "objects", "donor bands", "saved", saved["code"], "", names, paint_bands
            )
        )
        panels.append(
            Panel(
                "objects",
                "native outcomes",
                "saved",
                saved["code"],
                "",
                names,
                paint_native,
            )
        )
    for kind in ("concurrent", "conditional"):
        panels.append(subdivision_panel(plane, record, arrays, kind, originals))
    return panels


# ---------------------------------------------------------------------------------------------
# Ownership and relations.
# ---------------------------------------------------------------------------------------------


def member_residual_panel(plane: np.ndarray, parse: str, frame) -> Panel:
    """One ownership member's partition: its residual loud, its claims faint."""
    reading = f"member {parse}"
    if not frame.claims.size:
        return Panel("ownership", reading, "silent", frame.code, frame.why, ())
    claims = same_shape(f"ownership_{parse}_claims", frame.claims, plane)
    residual = same_shape(f"ownership_{parse}_residual", frame.residual, plane)

    def paint(axis) -> str:
        base(axis, plane)
        tint(axis, claims, CLAIMED_COLOUR, 0.18)
        tint(axis, residual, RESIDUAL_COLOUR, 0.6)
        title(
            axis,
            "ownership",
            f"{reading}: the residual, {frame.residual_places} places (fuchsia), beside "
            f"{frame.claimed_places} places claimed by {frame.objects} <object>s (faint "
            f"blue); {frame.unavailable_places} unavailable",
        )
        finish(axis, plane.shape)
        return "drawn"

    return Panel(
        "ownership",
        reading,
        "saved",
        frame.code,
        frame.why,
        (f"ownership_{parse}_claims", f"ownership_{parse}_residual"),
        paint,
    )


def disagreement_panel(
    plane: np.ndarray, disagreement: np.ndarray, saved: dict
) -> Panel:
    """Where the solitary and concurrent members' claims disagree, drawn AS a disagreement."""
    comparison = saved["comparison"]
    arrays = (saved["disagreement_array"],)
    if not disagreement.size:
        return Panel(
            "ownership",
            "disagreement between members",
            "silent",
            comparison,
            "the two members were not compared",
            arrays,
        )
    mask = same_shape(arrays[0], disagreement, plane)

    def paint(axis) -> str:
        base(axis, plane)
        tint(axis, mask, DISAGREEMENT_COLOUR, 0.9)
        title(
            axis,
            "ownership",
            f"solitary against concurrent claims: {comparison}; "
            f"{saved['disagreeing_places']} disagreeing places (yellow); nothing here "
            "resolves a disagreement",
        )
        finish(axis, plane.shape)
        return "drawn"

    return Panel(
        "ownership",
        "disagreement between members",
        "saved",
        comparison,
        "",
        arrays,
        paint,
    )


def ownership_panels(plane: np.ndarray, run: Path, record: dict) -> list[Panel]:
    """Every seated ownership member, then their disagreement, through the partition gallery's loader."""
    if "ownership" not in record or "relations" not in record:
        return [absent("ownership", "members", "ownership reading")]
    _, members, disagreement, _ = partition_frames.saved_panels(run, record)
    panels = [member_residual_panel(plane, parse, frame) for parse, frame in members]
    panels.append(disagreement_panel(plane, disagreement, record["ownership"]))
    return panels


def pairing_panel(plane: np.ndarray, run: Path, record: dict) -> Panel:
    """The relations stage's sample sites, near and far, by pairing outcome."""
    if "pairings" not in record:
        return absent("relations", "pairings", "pairing reading")
    _, reading, _ = pair_frames.saved_panels(run, record)
    names = record["pairings"]["outcome_names"]
    counts = dict(reading.counts)

    def paint(axis) -> str:
        base(axis, plane)
        entries = []
        for code in (int(c) for c in np.unique(reading.outcome_codes)):
            colour = pair_frames.PALETTE[code]
            selected = reading.outcome_codes == code
            for side, marker in ((0, "o"), (1, "x")):
                sites = reading.positions_rc[selected, side, :]
                sites = centred(sites[np.isfinite(sites).all(axis=1)])
                if not len(sites):
                    continue
                style = (
                    {"facecolors": "none", "edgecolors": colour}
                    if marker == "o"
                    else {"c": colour}
                )
                axis.scatter(
                    sites[:, 0],
                    sites[:, 1],
                    marker=marker,
                    s=5,
                    linewidths=0.4,
                    **style,
                )
            entries.append((f"{names[code]} ({counts.get(names[code], '?')})", colour))
        title(
            axis,
            "relations",
            f"pairings: {reading.code}: {reading.why}; o near, x far, the flanking sample "
            "sites of each profile by outcome; indexed extents, no interstice constructed",
        )
        legend(axis, entries)
        finish(axis, plane.shape)
        return "drawn"

    return Panel(
        "relations",
        "pairings",
        "saved",
        reading.code,
        reading.why,
        ("pairing_positions_rc", "pairing_outcome_codes"),
        paint,
    )


# ---------------------------------------------------------------------------------------------
# One view: its panels in route order, its footer, and its sheet.
# ---------------------------------------------------------------------------------------------


def footer_lines(record: dict) -> list[str]:
    """What is NOT per place and therefore not on this sheet, named with the stage's own code."""
    vectors = record.get("vectors")
    relations = record.get("relations")
    return [
        "not per place, so not on this sheet: "
        + (
            f"vectors (bundles) {vectors['code']}: {vectors['why']}"
            if vectors
            else "vectors (bundles) not saved"
        ),
        (
            f"relations {relations['code']}: {relations['why']}; "
            f"constructions: {len(relations['interstices'])}"
            if relations
            else "relations not saved"
        ),
        "predicates and output are per study: see predicates-findings and output-companion",
    ]


def view_panels(
    run: Path, record: dict, arrays: Mapping[str, np.ndarray]
) -> tuple[np.ndarray | None, list[Panel]]:
    """Every reading on one series' plane, in route order; a plane the writer did not save ends it."""
    plane = plane_of(record, arrays)
    if plane is None:
        return None, [absent("study", "acquired plane", "acquired plane")]
    originals = (
        int(np.count_nonzero(np.unique(arrays["b1_labels"])))
        if "interiors" in record and "b1_labels" in record["arrays"]
        else None
    )
    panels = [plane_panel(plane, record), background_panel(plane, record, arrays)]
    # The funnel's operation 1 sits right after the regime on the route, so its panel does here;
    # the line-up (operation 3a) follows it, on the recipient of a paired plane; then the first
    # lens (operation 2), read after the line-ups, as the route reads it.
    panels.append(squint_stack_panel(plane, run, record))
    panels.append(lineup_panel(plane, run, record))
    panels.append(first_lens_panel(plane, run, record))
    # The tile digits (operation 3b) follow the first lens, as the route reads them; the
    # conjunction (operation 3c) follows the digits, on the recipient of a paired plane, and
    # on every other series its panel says in words that none rides there.
    panels.append(tile_digits_panel(plane, run, record))
    panels.append(conjunction_panel(plane, run, record))
    # The depth collapse (operation 4) follows the conjunction, as the route reads it: where
    # each lens stands, and whether this sheet's own slice is one of the chosen.
    panels.append(depth_panel(plane, run, record))
    panels += structure_panels(run, record)
    panels += lens_panels(plane, run, record)
    panels += object_panels(plane, record, arrays)
    panels += conversation_panels(plane, record, arrays, originals)
    panels += ownership_panels(plane, run, record)
    panels.append(pairing_panel(plane, run, record))
    return plane, panels


def paint_panel(axis, panel: Panel) -> str:
    """Draw one panel: its reading, or its silence in the stage's own words."""
    if panel.paint is None:
        field_frames.silence(
            axis,
            f"{panel.stage} · {panel.reading}",
            f"{panel.status}: {panel.code}\n\n{panel.why}",
        )
        return panel.status
    return panel.paint(axis)


def image_name(index: int, record: dict) -> str:
    view, fluid, fat = record["view"]
    return f"{index:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"


def draw_view(
    path: Path, record: dict, panels: list[Panel], footer: list[str]
) -> list[str]:
    """One series' sheet: its panels in route order, the footer, saved to `path`; returns each status."""
    rows = -(-len(panels) // COLUMNS)
    sheet, axes = plt.subplots(
        rows,
        COLUMNS,
        figsize=(CELL_INCHES * COLUMNS, (CELL_INCHES + 1.1) * rows + 1.0),
        layout="constrained",
        squeeze=False,
    )
    sheet.get_layout_engine().set(rect=(0.0, 0.035, 1.0, 0.965))
    statuses = [
        paint_panel(axis, panel) for axis, panel in zip(axes.flat, panels, strict=False)
    ]
    for axis in list(axes.flat)[len(panels) :]:
        axis.set_axis_off()
    view, fluid, fat = record["view"]
    sheet.suptitle(
        f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat} · stack index "
        f"{record.get('slice_index')} · series {record['series_uid']}\n"
        "one sheet per view: the acquired plane under every reading that wrote at its places, "
        "in route order; a silent reading says so in its own panel",
        fontsize=10,
    )
    sheet.text(
        0.005,
        0.004,
        "\n".join(footer),
        fontsize=6.5,
        va="bottom",
        ha="left",
        family="monospace",
    )
    sheet.savefig(path, dpi=DPI)
    plt.close(sheet)
    return statuses


def panel_record(panel: Panel, drawn: str) -> dict:
    return {
        "stage": panel.stage,
        "reading": panel.reading,
        "status": panel.status,
        "drawn": drawn,
        "code": panel.code,
        "why": panel.why,
        "arrays": list(panel.arrays),
    }


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw one sheet per view of the study from the saved run and return the manifest.

    The one entry a caller uses, so the single command can draw it without knowing this module's
    argument spelling; `main()` is a thin wrapper over it.
    """
    target = out.resolve()
    if not target.is_relative_to((PROJECT / "data").resolve()):
        raise ArgumentRefusal("out must be under the project's private data directory")
    receipt_path = run / "receipt.json"
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes)
    records = [r for r in receipt["records"] if r["study_uid"] == study_uid]
    if not records:
        raise ArgumentRefusal("no saved records for this study")
    # A kind or an outcome the objects stage says that this sheet has no colour for would be drawn
    # in no colour at all; it is refused before anything is drawn, as the study drawer refuses an
    # end it cannot word.
    uncoloured = [
        *(name for name in EDGE_KINDS if name not in EDGE_KIND_COLOURS),
        *(name for name in TRACE_CODES if name not in TRACE_COLOURS),
    ]
    if uncoloured:
        raise RuntimeError(f"objects_vocabulary_uncoloured:{','.join(uncoloured)}")
    target.mkdir(parents=True, exist_ok=True)
    views = []
    for index, record in enumerate(records, start=1):
        artifact = run / record["artifact"]
        with np.load(artifact, allow_pickle=False) as saved:
            arrays = {name: saved[name] for name in saved.files}
        plane, panels = view_panels(run, record, arrays)
        footer = footer_lines(record)
        name = image_name(index, record)
        statuses = draw_view(target / name, record, panels, footer)
        views.append(
            {
                "image": name,
                "image_sha256": sha256((target / name).read_bytes()).hexdigest(),
                "series_uid": record["series_uid"],
                "view": record["view"],
                "slice_index": record.get("slice_index"),
                "source_plane": record.get("source_plane"),
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "plane": None if plane is None else record["arrays"]["acquired_plane"],
                "panels": [
                    panel_record(panel, drawn)
                    for panel, drawn in zip(panels, statuses, strict=True)
                ],
                "not_per_place": footer,
            }
        )
    for module_name, module in REUSED:
        if module.__file__ is None:
            raise RuntimeError(f"drawer_source_unavailable:{module_name}")
    manifest = {
        "schema": "view-frames-v1",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "reused_drawers_sha256": {
            name: sha256(Path(str(module.__file__)).read_bytes()).hexdigest()
            for name, module in REUSED
        },
        "study_uid": study_uid,
        "image": views[0]["image"],
        "images": [view["image"] for view in views],
        "frame_kind": "study",
        "statuses": list(STATUSES),
        "views": views,
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--study-uid", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    # ONLY the argument refusals. A saved-array digest mismatch or a malformed receipt is a
    # corruption signal and must propagate, never be dressed as a mistyped flag.
    try:
        manifest = draw(args.run, args.study_uid, args.out)
    except ArgumentRefusal as refusal:
        parser.error(str(refusal))
    target = args.out.resolve()
    print(
        json.dumps(
            {
                "images": [str(target / name) for name in manifest["images"]],
                "manifest": str(target / "manifest.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
