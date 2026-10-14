"""Draw the funnel's line-up: per paired plane, the recipient's tiles and the partner's tile centres on one plane.

The-funnel task 3a.2 (`openspec/changes/the-funnel/tasks.md`). The funnel's operation 3a
(`knee.collapse.lineup`) lines the fat-bright partner's squint stack up with the fat-dark
recipient's, by place on the knee; the writer saves the whole line-up on the recipient's record.
This workbench arranges those saved values through `knee.pictures.lineup`: one row per recipient,
the line-up's standing in words, then the recipient's acquired plane at the selected slice in
grey with its tile grid over it, each tile tinted by its match code, the partner's tile centres
at the nearest partner slice placed in the recipient's native frame, and a segment from each
recipient tile's centre to its matched partner centre -- the "scootch", the founder's word
(2026-10-13) for how two pictures of one plane lie over each other; then the nearest partner
slice per recipient slice, by slab code. The partner's saved stack is found through the receipt
by the saved partner identifier. It takes no measurement of its own: every number on the page is
a saved value, and every gap is a named silence, never a zero.

Seven silences are kept apart, because each has its own remedy
(`knee.pictures.lineup.SLICE_STANDINGS`): this run's writer saved no line-up; the saved code is a
word the stage does not say; the stage made no line-up and says why; the selected slice lies
outside the line-up; the stage named no partner slice there; this run holds no saved stack for
the partner; the named partner slice lies outside the partner's stack. A study with no paired
plane draws its silence in words, with the pairs record's own codes beside it. A recipient whose
acquired plane and plane frame the writer did not save draws the line-up's text alone and says
so.

Nothing here lines up, searches, thresholds or recomputes a centre or a distance. The grey scale
is Matplotlib's linear display scale over the plane's own stored values.
"""

import argparse
import json
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from textwrap import fill

import numpy as np

from knee.collapse.lineup import MATCH_CODES, SLAB_CODES
from knee.collapse.physical import PlaneFrame
from knee.collapse.squint_stack import STACK_CODES
from knee.pictures import lineup as pictures
from workbench.render import squint_stack_frames
from workbench.render._out import PROJECT, ArgumentRefusal
from workbench.render.field_frames import (
    native_extent,
    overlay,
    saved_array,
    tile_edges,
)
from workbench.render.study_frames import pairing_line, saved_pairs

#: The line-up's arrays by the short names the writer gives them in `record["lineup"]["arrays"]`,
#: each with the dtype it must have and its number of axes.
LINEUP_ARRAYS: Mapping[str, tuple[np.dtype, int]] = {
    "partner_slice": (np.dtype(np.int64), 1),
    "slab_codes": (np.dtype(np.uint8), 1),
    "partner_tile": (np.dtype(np.int64), 4),
    "distance_mm": (np.dtype(np.float64), 3),
    "match_codes": (np.dtype(np.uint8), 3),
}

#: What each standing a drawn slice can hold says, in words. The codes are the adapter's
#: (`knee.pictures.lineup.SLICE_STANDINGS`); the words are this drawing's.
STANDING_WORDS: Mapping[str, str] = {
    "lined_up": (
        "the recipient's tiles by match code, with the partner's tile centres placed on the "
        "same plane"
    ),
    "lineup_not_saved": "not saved: this run's writer saved no line-up for this series",
    "lineup_code_unknown": "not drawn: the saved code is one the stage does not say",
    "lineup_absent": (
        "not made: the stage lined up no slice; its own code and reason are beside"
    ),
    "slice_outside_lineup": (
        "not drawn: the selected slice lies outside the slices the line-up holds"
    ),
    "partner_slice_absent": (
        "not drawn: the stage named no partner slice at the selected slice"
    ),
    "partner_stack_not_saved": (
        "not drawn: this run holds no saved squint stack for the partner"
    ),
    "partner_slice_outside_stack": (
        "not drawn: the named partner slice lies outside the partner's saved stack"
    ),
}

#: The drawer's own word for a lined-up slice it has nothing to lay under: this run's writer
#: saved no acquired plane, or no plane frame, for the recipient's selected slice.
PLANE_NOT_SAVED = "recipient_plane_not_saved"
PLANE_NOT_SAVED_WORDS = (
    "not drawn over the plane: this run's writer saved no acquired plane or no plane frame for "
    "the recipient's selected slice, so the partner's centres cannot be placed"
)

#: What each match code and each slab code is drawn in. None is a grey, so no stored value is
#: ever mistaken for a reading; the two silences share one colour no reading takes.
MATCH_COLOURS: Mapping[str, str] = {
    "matched": "#22c55e",
    "beyond_half_tile": "#f59e0b",
    "partner_unavailable": "#ff00ff",
    "invalid_measurement": "#a855f7",
}
SLAB_COLOURS: Mapping[str, str] = {
    "in_slab": "#22c55e",
    "nearest_only": "#f59e0b",
    "no_partner": "#ff00ff",
    "invalid_measurement": "#a855f7",
}
#: The partner's tile centres, the recipient's, and the segment joining a tile to its match.
PARTNER_COLOUR = "#00e5ff"
RECIPIENT_COLOUR = "#ffffff"
SCOOTCH_COLOUR = "#facc15"
SELECTED_COLOUR = "#dc2626"

#: How much of the plane shows through the tints laid over it.
TINT_ALPHA = 0.35

#: One row per recipient: the text panel, the grid over the plane, the partner slice per slice.
PANEL_INCHES = 5.2
ROW_INCHES = 5.6
DPI = 120


@dataclass(frozen=True, slots=True)
class LineUpDrawing:
    """One recipient's saved line-up as the adapter arranges it, with what the drawer lays it over.

    artifact: the recipient's saved arrays. panels: the adapter's arrangement at the selected
    slice. bounds_rc: the recipient's saved native bounds (TR, TC, 4) int64, which place its
    tiles; None when the record carries no line-up. plane: the recipient's saved acquired plane
    at the selected slice, in its stored dtype; None when the writer saved none.
    """

    artifact: Path
    panels: pictures.LineUpPanels
    bounds_rc: np.ndarray | None
    plane: np.ndarray | None


def saved_number(value: object, where: str) -> float | None:
    """A saved bar or angle as a float; None where the writer saved None (a reading not made).

    A value that is neither None nor a finite number is a record that disagrees, and is raised.
    """
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(value)
    ):
        raise ValueError(f"saved_lineup_not_a_number:{where}")
    return float(value)


def receipt_records(run: Path) -> list[dict]:
    """Every series record of the run's receipt, or none when the run has no readable receipt.

    Total: a run with no receipt (a test's scratch directory, a record drawn alone) holds no
    partner to find, and the adapter then names that silence; it is never raised here.
    """
    path = run / "receipt.json"
    if not path.is_file():
        return []
    receipt = json.loads(path.read_text())
    records = receipt.get("records") if isinstance(receipt, dict) else None
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def partner_record(records: list[dict], record: dict) -> dict | None:
    """The saved record of the recipient's partner: the series its line-up names, in the same study.

    None when the recipient carries no line-up, or when the run holds no such record. A record
    is never its own partner.
    """
    saved = record.get("lineup")
    if type(saved) is not dict:
        return None
    partner_uid = saved.get("partner_uid")
    for candidate in records:
        if (
            candidate is not record
            and candidate.get("study_uid") == record.get("study_uid")
            and candidate.get("series_uid") == partner_uid
        ):
            return candidate
    return None


def saved_plane_frame(
    arrays: Mapping[str, np.ndarray], record: dict
) -> PlaneFrame | None:
    """The recipient's saved plane frame at the selected slice, or None when the writer saved none.

    The objects stage saves its frame as `origin_lps` (3,), `basis_lps` (3, 2) and
    `spacing_rc_mm`; a frame that is only partly there, or whose parts are not those shapes,
    disagrees with the writer and is raised.
    """
    descriptors = record["arrays"]
    parts = (
        "origin_lps" in descriptors,
        "basis_lps" in descriptors,
        record.get("spacing_rc_mm") is not None,
    )
    if not any(parts):
        return None
    if not all(parts):
        raise ValueError("saved_plane_frame_incomplete")
    origin = saved_array(arrays, descriptors, "origin_lps", 1)
    basis = saved_array(arrays, descriptors, "basis_lps", 2)
    spacing = record["spacing_rc_mm"]
    if origin.shape != (3,) or basis.shape != (3, 2) or len(spacing) != 2:
        raise ValueError("saved_plane_frame_invalid")
    return PlaneFrame(origin, basis, (float(spacing[0]), float(spacing[1])))


def saved_lineup(run: Path, record: dict, partner: dict | None) -> LineUpDrawing:
    """Reconstitute one series' saved line-up at its selected slice, without measuring.

    Total over a series whose writer saved no line-up: that is handed on as the silence it is.
    A line-up record that is not a mapping, a code the stage does not say, a recipient that is
    not this series, vocabularies that are not the stage's, a bar or a grid that is not what the
    writer saves, an array whose dtype, shape or digest disagrees with its descriptor, arrays that
    do not share one grid, a slice count that is not the arrays', a saved code outside its
    vocabulary, a line-up saved without the recipient's own stack, or a stack whose grid is not
    the line-up's, means the record and this renderer disagree, and is raised rather than drawn.
    The partner's saved stack, where the run holds it, is validated through the stack drawer's
    own reader before its centres are read.
    """
    artifact = run / record["artifact"]
    descriptors = record["arrays"]
    index = record.get("slice_index")
    saved = record.get("lineup")
    if saved is None:
        return LineUpDrawing(
            artifact,
            pictures.lineup_panels(
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                index,
            ),
            None,
            None,
        )
    if type(saved) is not dict:
        raise ValueError("saved_lineup_not_a_record")
    for key in ("code", "why", "recipient_uid", "partner_uid"):
        if type(saved.get(key)) is not str:
            raise ValueError(f"saved_lineup_field_invalid:{key}")
    if saved["code"] not in STACK_CODES:
        raise ValueError(f"saved_lineup_code_unknown:{saved['code']}")
    if saved["recipient_uid"] != record.get("series_uid"):
        raise ValueError("saved_lineup_recipient_mismatch")
    if saved.get("match_code_names") != list(MATCH_CODES) or saved.get(
        "slab_code_names"
    ) != list(SLAB_CODES):
        raise ValueError("saved_lineup_vocabulary_mismatch")
    names = saved.get("arrays")
    if type(names) is not dict:
        raise ValueError("saved_lineup_arrays_missing")
    for short in LINEUP_ARRAYS:
        if type(names.get(short)) is not str:
            raise ValueError(f"saved_lineup_array_unnamed:{short}")
    tiles = saved.get("tiles_rc")
    if not (
        isinstance(tiles, list)
        and len(tiles) == 2
        and all(type(size) is int and size >= 0 for size in tiles)
    ):
        raise ValueError("saved_lineup_tiles_invalid")
    half_tile = saved_number(saved.get("half_tile_mm"), "half_tile_mm")
    half_thickness = saved_number(saved.get("half_thickness_mm"), "half_thickness_mm")
    angle = saved_number(saved.get("normal_angle_deg"), "normal_angle_deg")
    drawn: dict[str, np.ndarray] = {}
    plane = None
    with np.load(artifact, allow_pickle=False) as arrays:
        for short, (dtype, ndim) in LINEUP_ARRAYS.items():
            array = saved_array(arrays, descriptors, names[short], ndim)
            if array.dtype != dtype:
                raise ValueError(f"saved_lineup_representation_invalid:{short}")
            drawn[short] = array
        frame = saved_plane_frame(arrays, record)
        if "acquired_plane" in descriptors:
            plane = saved_array(arrays, descriptors, "acquired_plane", 2)
            if plane.dtype.kind not in "iuf":
                raise ValueError("saved_array_representation_invalid:acquired_plane")
    slices = int(drawn["partner_slice"].shape[0])
    grid = (slices, int(tiles[0]), int(tiles[1]))
    if (
        drawn["slab_codes"].shape != (slices,)
        or drawn["partner_tile"].shape != (*grid, 2)
        or drawn["distance_mm"].shape != grid
        or drawn["match_codes"].shape != grid
    ):
        raise ValueError("saved_lineup_shape_mismatch")
    if saved.get("slices") != slices:
        raise ValueError("saved_lineup_slices_mismatch")
    if drawn["slab_codes"].size and int(drawn["slab_codes"].max()) >= len(SLAB_CODES):
        raise ValueError("saved_lineup_slab_code_unknown")
    if drawn["match_codes"].size and int(drawn["match_codes"].max()) >= len(
        MATCH_CODES
    ):
        raise ValueError("saved_lineup_match_code_unknown")
    # A line-up is made over the recipient's own stack, so a record that saved the one and not
    # the other disagrees with the writer; the stack's grid must be the line-up's.
    if "squint_stack" not in record:
        raise ValueError("saved_lineup_without_a_recipient_stack")
    _, stack = squint_stack_frames.saved_stack(run, record)
    bounds = stack.bounds_rc
    if bounds is not None and slices and tuple(bounds.shape[:2]) != grid[1:]:
        raise ValueError("saved_lineup_grid_mismatch")
    partner_centres = None
    if partner is not None and "squint_stack" in partner:
        # The partner's stack through the stack drawer's reader, which validates every one of
        # its arrays against the writer's descriptors; then its centres, which that reader does
        # not hand on, read under the same descriptor.
        squint_stack_frames.saved_stack(run, partner)
        with np.load(run / partner["artifact"], allow_pickle=False) as arrays:
            partner_centres = saved_array(
                arrays,
                partner["arrays"],
                partner["squint_stack"]["arrays"]["centres_lps"],
                4,
            )
    return LineUpDrawing(
        artifact,
        pictures.lineup_panels(
            saved["code"],
            saved["why"],
            saved["recipient_uid"],
            saved["partner_uid"],
            half_tile,
            half_thickness,
            angle,
            drawn["partner_slice"],
            drawn["slab_codes"],
            drawn["partner_tile"],
            drawn["distance_mm"],
            drawn["match_codes"],
            bounds,
            partner_centres,
            frame,
            index,
        ),
        bounds,
        plane,
    )


def scootch_segments(
    recipient_centres_rc: np.ndarray,
    partner_tile: np.ndarray,
    partner_centres_rc: np.ndarray,
) -> np.ndarray:
    """One segment per recipient tile with a named partner tile, from its centre to its match.

    The saved pairing, drawn: tile (i, j) is joined to the partner tile the stage named at
    (i, j); a tile the stage named no partner for (-1), or whose own or whose partner's centre is
    NaN, has no segment. Returns float64 (N, 2, 2) in the native picture frame, (x, y) with a
    pixel's centre at +0.5, as every drawer here places a point. Nothing is matched here.
    """
    recipient = np.asarray(recipient_centres_rc, dtype=np.float64).reshape(-1, 2)
    tiles = np.asarray(partner_tile, dtype=np.int64).reshape(-1, 2)
    placed = np.asarray(partner_centres_rc, dtype=np.float64)
    named = (
        (tiles[:, 0] >= 0)
        & (tiles[:, 1] >= 0)
        & (tiles[:, 0] < placed.shape[0])
        & (tiles[:, 1] < placed.shape[1])
    )
    if not named.any():
        return np.zeros((0, 2, 2), dtype=np.float64)
    targets = placed[tiles[named, 0], tiles[named, 1]]
    segments = np.stack(
        (recipient[named][:, ::-1] + 0.5, targets[:, ::-1] + 0.5), axis=1
    )
    return segments[np.isfinite(segments).all(axis=(1, 2))]


def match_counts(match_codes: np.ndarray | None) -> dict[str, int]:
    """How many tiles at the drawn slice carry each match code, from the saved codes; empty when none."""
    if match_codes is None:
        return {}
    codes = np.asarray(match_codes)
    return {
        name: int(np.count_nonzero(codes == value))
        for value, name in enumerate(MATCH_CODES)
    }


def slab_counts(slab_codes: np.ndarray | None) -> dict[str, int]:
    """How many recipient slices carry each slab code, from the saved codes; empty when none."""
    if slab_codes is None:
        return {}
    codes = np.asarray(slab_codes)
    return {
        name: int(np.count_nonzero(codes == value))
        for value, name in enumerate(SLAB_CODES)
    }


def number(value: float | None, unit: str) -> str:
    """A saved bar or angle as text; None is how a reading the stage could not make comes back."""
    return "not read" if value is None else f"{value:g} {unit}"


def lineup_lines(record: dict, drawing: LineUpDrawing) -> list[str]:
    """The text panel: the recipient, its view, the pair, the bars, and the standing at the slice."""
    panels = drawing.panels
    view, fluid, fat = record["view"]
    lines = [
        fill(record["series_uid"], width=46),
        f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat}",
        "",
    ]
    if panels.code is None:
        lines.append("line-up (collapse): not saved")
        lines.append(fill(STANDING_WORDS["lineup_not_saved"], width=46))
        return lines
    at = panels.at
    counts = ", ".join(
        f"{name} {n}" for name, n in match_counts(at.match_codes).items()
    )
    slabs = ", ".join(
        f"{name} {n}" for name, n in slab_counts(panels.slab_codes).items()
    )
    lines += [
        f"line-up (collapse): {panels.code}",
        fill(f"why: {panels.why}", width=46),
        "",
        "partner (fat-bright, same plane)",
        fill(str(panels.partner_uid), width=46),
        "",
        f"match bar      {number(panels.half_tile_mm, 'mm')} (half a tile)",
        f"slab bar       {number(panels.half_thickness_mm, 'mm')} (half the thickness)",
        f"normals        {number(panels.normal_angle_deg, 'deg')} apart",
        f"slices         {panels.slices} of the recipient",
    ]
    if at.match_codes is not None:
        lines.append(
            f"grid           {at.match_codes.shape[0]} x {at.match_codes.shape[1]} tiles"
        )
    lines += [
        f"selected slice {at.index}",
        "partner slice  "
        + (
            "none named"
            if at.partner_index is None
            else f"{at.partner_index} ({at.slab_code})"
        ),
        f"standing       {at.standing}",
        "",
    ]
    if counts:
        lines.append(fill(f"tiles at this slice: {counts}", width=46))
    if slabs:
        lines.append(fill(f"slices over the stack: {slabs}", width=46))
    return lines


def draw_grid(axis, drawing: LineUpDrawing) -> str:
    """The recipient's tiles by match code over its plane, with the partner's centres and the scootch.

    Returns the slice's standing, or `recipient_plane_not_saved` when a lined-up slice has no
    saved plane or frame to be drawn over; the silence is then written in words.
    """
    from matplotlib.collections import LineCollection
    from matplotlib.patches import Patch

    panels = drawing.panels
    at = panels.at
    axis.set_axis_off()
    axis.set_title(f"recipient stack index {at.index}", fontsize=8)
    if at.standing != "lined_up":
        words = STANDING_WORDS[at.standing]
        if at.standing == "lineup_absent":
            words = f"{words}: {panels.code}"
        axis.text(0.03, 0.95, fill(words, width=44), transform=axis.transAxes, va="top")
        return at.standing
    if (
        drawing.plane is None
        or drawing.bounds_rc is None
        or at.recipient_centres_rc is None
        or at.partner_centres_rc is None
        or at.partner_tile is None
        or at.match_codes is None
    ):
        axis.text(
            0.03,
            0.95,
            fill(PLANE_NOT_SAVED_WORDS, width=44),
            transform=axis.transAxes,
            va="top",
        )
        return PLANE_NOT_SAVED
    plane = drawing.plane
    axis.imshow(
        plane, cmap="gray", interpolation="nearest", extent=native_extent(plane.shape)
    )
    edges = tile_edges(drawing.bounds_rc)
    present = []
    for value, name in enumerate(MATCH_CODES):
        mask = at.match_codes == value
        if mask.any():
            overlay(axis, edges, mask, MATCH_COLOURS[name], alpha=TINT_ALPHA)
            present.append((f"{name} ({int(mask.sum())})", MATCH_COLOURS[name]))
    segments = scootch_segments(
        at.recipient_centres_rc, at.partner_tile, at.partner_centres_rc
    )
    if len(segments):
        axis.add_collection(
            LineCollection(list(segments), colors=SCOOTCH_COLOUR, linewidths=0.7)
        )
    recipient = at.recipient_centres_rc.reshape(-1, 2)
    axis.scatter(
        recipient[:, 1] + 0.5,
        recipient[:, 0] + 0.5,
        marker=".",
        s=6,
        c=RECIPIENT_COLOUR,
    )
    partner = at.partner_centres_rc.reshape(-1, 2)
    finite = np.isfinite(partner).all(axis=1)
    axis.scatter(
        partner[finite, 1] + 0.5,
        partner[finite, 0] + 0.5,
        marker="+",
        s=22,
        c=PARTNER_COLOUR,
        linewidths=0.7,
    )
    axis.set_xlim(0, plane.shape[1])
    axis.set_ylim(plane.shape[0], 0)
    axis.set_aspect("equal")
    axis.legend(
        handles=[
            *(Patch(facecolor=colour, label=label) for label, colour in present),
            Patch(facecolor=PARTNER_COLOUR, label="+ partner tile centre"),
            Patch(facecolor=SCOOTCH_COLOUR, label="segment: tile centre to its match"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.0),
        ncol=2,
        fontsize=5.5,
        frameon=False,
    )
    axis.set_title(
        f"recipient stack index {at.index} -> partner slice {at.partner_index} "
        f"({at.slab_code})\ntiles by match code over the plane; + the partner's tile "
        "centres in this frame;\na segment from each tile centre to its match: the scootch",
        fontsize=8,
    )
    return at.standing


def draw_slices(axis, drawing: LineUpDrawing) -> str:
    """The nearest partner slice per recipient slice, by slab code, with the selected slice marked.

    Returns `drawn`, or the silence the panel holds when no slice was lined up.
    """
    panels = drawing.panels
    axis.set_title(
        "the nearest partner slice per recipient slice, by slab code\n"
        f"slab bar {number(panels.half_thickness_mm, 'mm')}; "
        f"normals {number(panels.normal_angle_deg, 'deg')} apart",
        fontsize=8,
    )
    if panels.partner_slice is None or panels.slab_codes is None or not panels.slices:
        axis.set_axis_off()
        words = (
            STANDING_WORDS["lineup_not_saved"]
            if panels.code is None
            else f"{STANDING_WORDS['lineup_absent']}: {panels.code}"
        )
        axis.text(0.03, 0.95, fill(words, width=44), transform=axis.transAxes, va="top")
        return "lineup_not_saved" if panels.code is None else "lineup_absent"
    z = np.arange(panels.slices)
    for value, name in enumerate(SLAB_CODES):
        selected = panels.slab_codes == value
        if selected.any():
            axis.scatter(
                z[selected],
                panels.partner_slice[selected],
                s=12,
                c=SLAB_COLOURS[name],
                label=f"{name} ({int(selected.sum())})",
            )
    at = panels.at
    if isinstance(at.index, int) and not isinstance(at.index, bool):
        axis.axvline(at.index, color=SELECTED_COLOUR, linewidth=1.0)
    axis.set_xlabel("recipient slice (stack index)", fontsize=7)
    axis.set_ylabel("nearest partner slice (its stack index; -1 none)", fontsize=7)
    axis.tick_params(labelsize=6)
    axis.legend(fontsize=6, frameon=False)
    return "drawn"


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run and return its manifest.

    The one entry a caller uses, so the single command can draw every stage without knowing each
    renderer's argument spelling. `main()` is a thin wrapper over it.

    Matplotlib is supplied PER RUN and is never a production dependency, so it is imported after
    every refusal this function can make: the validators above are then importable and testable
    in the ordinary environment.
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
    recipients = [record for record in records if "lineup" in record]
    loaded = [
        saved_lineup(run, record, partner_record(records, record))
        for record in recipients
    ]
    pairs_line = pairing_line(saved_pairs(receipt, study_uid))
    if pictures.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:lineup")
    # Every standing the adapter can name has words here, and every code a colour, checked
    # before anything is drawn: a code with no colour would be drawn in no colour at all.
    unworded = [name for name in pictures.SLICE_STANDINGS if name not in STANDING_WORDS]
    if unworded:
        raise RuntimeError(f"slice_standing_unworded:{','.join(unworded)}")
    uncoloured = [
        *(name for name in MATCH_CODES if name not in MATCH_COLOURS),
        *(name for name in SLAB_CODES if name not in SLAB_COLOURS),
    ]
    if uncoloured:
        raise RuntimeError(f"lineup_vocabulary_uncoloured:{','.join(uncoloured)}")

    import matplotlib.pyplot as plt

    target.mkdir(parents=True, exist_ok=True)
    rows = max(1, len(recipients))
    gallery, axes = plt.subplots(
        rows,
        3,
        figsize=(PANEL_INCHES * 3, ROW_INCHES * rows),
        layout="constrained",
        squeeze=False,
    )
    for axis in axes.flat:
        axis.set_axis_off()
    silence = None
    if not recipients:
        silence = (
            "no series of this study carries a line-up: no plane is paired, or this "
            "run's writer saved none. " + pairs_line
        )
        axes[0, 0].set_title("the line-up", fontsize=8)
        axes[0, 0].text(
            0.0,
            1.0,
            fill(silence, width=60),
            transform=axes[0, 0].transAxes,
            va="top",
            fontsize=7,
        )
    series = []
    for row, (record, drawing) in enumerate(zip(recipients, loaded, strict=True)):
        text = axes[row, 0]
        text.set_title("the line-up, on the recipient", fontsize=8)
        text.text(
            0.0,
            1.0,
            "\n".join(lineup_lines(record, drawing)),
            transform=text.transAxes,
            va="top",
            family="monospace",
            fontsize=6.5,
        )
        grid_status = draw_grid(axes[row, 1], drawing)
        axes[row, 2].set_axis_on()
        slices_status = draw_slices(axes[row, 2], drawing)
        panels = drawing.panels
        saved = record["lineup"]
        series.append(
            {
                "series_uid": record["series_uid"],
                "partner_uid": panels.partner_uid,
                "artifact": record["artifact"],
                "artifact_sha256": sha256(drawing.artifact.read_bytes()).hexdigest(),
                "view": record["view"],
                "lineup": {
                    "code": panels.code,
                    "why": panels.why,
                    "half_tile_mm": panels.half_tile_mm,
                    "half_thickness_mm": panels.half_thickness_mm,
                    "normal_angle_deg": panels.normal_angle_deg,
                    "slices": panels.slices,
                    "tiles_rc": list(saved.get("tiles_rc") or ()),
                    "arrays": {
                        short: record["arrays"][key]
                        for short, key in saved["arrays"].items()
                    },
                },
                "slice_index": record.get("slice_index"),
                "partner_index": panels.at.partner_index,
                "slab_code": panels.at.slab_code,
                "standing": panels.at.standing,
                "drawn": grid_status,
                "slices_panel": slices_status,
                "match_counts": match_counts(panels.at.match_codes),
                "slab_counts": slab_counts(panels.slab_codes),
                "frame_kind": "study",
            }
        )
    gallery.suptitle(
        "The funnel's line-up, one row per recipient (the fat-dark series of a paired plane): "
        "its standing, then its tiles by match code over its acquired plane at the selected "
        "slice with the partner's tile centres placed in the same frame, then the nearest "
        "partner slice per recipient slice by slab code\n"
        + fill(pairs_line, width=160),
        fontsize=10,
    )
    gallery.savefig(target / "series.png", dpi=DPI)
    plt.close(gallery)
    manifest = {
        "schema": "lineup-frames-v1",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "lineup": sha256(Path(pictures.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": "series.png",
        "frame_kind": "study",
        "standings": list(pictures.SLICE_STANDINGS),
        "legend": {
            "match_codes": dict(MATCH_COLOURS),
            "slab_codes": dict(SLAB_COLOURS),
            "partner_tile_centre": PARTNER_COLOUR,
            "recipient_tile_centre": RECIPIENT_COLOUR,
            "scootch_segment": SCOOTCH_COLOUR,
        },
        "pairs_caption": pairs_line,
        "silence": silence,
        "series": series,
        "note": (
            "Every value is a saved one. A line-up this run's writer did not save, a saved "
            "code the stage does not say, a line-up the stage did not make, a slice it does "
            "not hold, a partner slice it did not name, a partner stack this run does not hold "
            "and a partner slice that stack does not hold are seven silences, each named; none "
            "is a zero."
        ),
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
        draw(args.run, args.study_uid, args.out)
    except ArgumentRefusal as refusal:
        parser.error(str(refusal))
    target = args.out.resolve()
    print(
        json.dumps(
            {
                "series": str(target / "series.png"),
                "manifest": str(target / "manifest.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
