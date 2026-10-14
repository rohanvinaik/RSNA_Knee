"""Draw the funnel's selection: one sheet per series, each chosen slice's territories tinted by role over the acquired plane.

The-funnel task 5b.5 (`openspec/changes/the-funnel/tasks.md`). The funnel's operation 5b
(`knee.objects.selection`) names every territory of a chosen slice's tile dome by the view's own
rule and carries the laterality sign its Coronal witness gives; the writer saves the record whole.
This workbench arranges those saved values through `knee.pictures.selection`: ONE SHEET PER SERIES
(one image per series), so the founder can check the objects by eye (task 5b.6, E3). The first
panel states the series, its view and, per chosen slice, the selection's standing in words. Then
one panel per chosen slice: the acquired plane at that slice in grey where the writer saved it,
and over it every territory tinted by its role code, placed in native pixels by the squint
stack's saved bounds, each with its index, its role word and its facts (tiles, superior, anterior
and left-right in millimetres) written at the dome's own saved peak for that territory, and the
laterality sign in the panel's title. Under each panel is the table of the slice's territories
with every fact the stage read and the candidate decision's word on each. It takes no measurement
of its own: every number on the page is a saved value, and every gap is a named silence, never a
zero.

Five standings are kept apart, because each has its own remedy
(`knee.pictures.selection.SELECTION_STANDINGS`): the selection was made and named; this run's
writer saved no selection; the saved code is a word the stage does not say; the stage read no dome
and says why; the dome held no territory. A slice whose plane the writer did not save draws its
territories alone on the tile grid and the title says so. A selection saved without the series'
squint stack, over another grid than the stack's, whose labels disagree with its objects, or whose
peaks do not lie in their territories disagrees with the writer and is refused rather than drawn.

Nothing here thresholds, labels, dilates, computes a centroid or recomputes a fact. The grey scale
is Matplotlib's linear display scale over each plane's own stored values.
"""

import argparse
import json
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from textwrap import fill

import numpy as np

from knee.objects.laterality import SIGN_CODES
from knee.objects.selection import (
    ANTERIOR_CODES,
    PAIR_CODES,
    PLANE_KINDS,
    ROLE_CODES,
    SELECTION_CODES,
    WITNESS_CODES,
)
from knee.objects.tile_dome import BORDER_CODES
from knee.pictures import selection as pictures
from workbench.render import squint_stack_frames
from workbench.render._out import PROJECT, ArgumentRefusal
from workbench.render.field_frames import (
    native_extent,
    overlay,
    saved_array,
    tile_edges,
)

#: The selection's arrays by the short names the writer gives them in
#: `record["selection"]["arrays"]`: the dome's labels, one grid per saved slice (required), and the
#: acquired plane at each saved slice (optional; the writer names None when it saved none).
LABELS_ARRAY = "labels"
PLANES_ARRAY = "planes"

#: The vocabularies a saved selection must carry beside its codes, each the stage's own.
VOCABULARIES: Mapping[str, tuple[str, ...]] = {
    "code_names": SELECTION_CODES,
    "role_code_names": ROLE_CODES,
    "pair_code_names": PAIR_CODES,
    "anterior_code_names": ANTERIOR_CODES,
    "witness_code_names": WITNESS_CODES,
    "sign_code_names": SIGN_CODES,
}

#: The roles and the candidate words each view's own rule can say (`knee.objects.selection`,
#: `_paired_roles` and `_axial_roles`), keyed by the told plane word. The Coronal and the Sagittal
#: take the big pair and one candidate role each; the Axial takes its own two roles and has no
#: candidate decision, so its table of candidate words is empty and it saves none, not even "". A
#: saved slice is held to the table of its record's OWN `plane_kind` and to no other view's.
VIEW_ROLES: Mapping[str, tuple[str, ...]] = {
    "Coronal": ("superior_big", "inferior_big", "lateral_small_ringed", "unselected"),
    "Sagittal": ("superior_big", "inferior_big", "anterior_small", "unselected"),
    "Axial": ("central_big", "anterior_small", "unselected"),
}
VIEW_CANDIDATES: Mapping[str, tuple[str, ...]] = {
    "Coronal": WITNESS_CODES,
    "Sagittal": ANTERIOR_CODES,
    "Axial": (),
}

#: Every key a saved territory carries, in the order the writer saves them.
OBJECT_KEYS: tuple[str, ...] = (
    "index",
    "role_code",
    "tiles",
    "centre_lps",
    "superior_mm",
    "anterior_mm",
    "left_right_mm",
    "superior_extent_mm",
    "anterior_face_mm",
    "touches_leg_border",
    "ringed",
)

#: What each standing a chosen slice can hold says, in words. The codes are the adapter's
#: (`knee.pictures.selection.SELECTION_STANDINGS`); the words are this drawing's.
STANDING_WORDS: Mapping[str, str] = {
    "named": "every territory of this slice tinted by its role, over the plane",
    "selection_not_saved": "not saved: this run's writer saved no selection for this series",
    "selection_code_unknown": "not drawn: the saved code is one the stage does not say",
    "selection_absent": (
        "not made: the stage read no dome to select from; its own reason is beside"
    ),
    "no_territory": "the dome at this slice held no territory, so none was put to a rule",
}

#: What each role is tinted in, and how much of the plane shows through. Every role word the
#: stage says has an entry, checked before anything is drawn. `unselected` is a quiet grey: it is
#: kept and shown, never hidden.
ROLE_COLOURS: Mapping[str, str] = {
    "superior_big": "#2563eb",
    "inferior_big": "#16a34a",
    "anterior_small": "#f59e0b",
    "lateral_small_ringed": "#dc2626",
    "central_big": "#7c3aed",
    "unselected": "#6b7280",
}
ROLE_ALPHAS: Mapping[str, float] = {
    "superior_big": 0.5,
    "inferior_big": 0.5,
    "anterior_small": 0.6,
    "lateral_small_ringed": 0.6,
    "central_big": 0.5,
    "unselected": 0.22,
}

#: One sheet per series: the text panel then one panel per chosen slice, and under each the table.
PANEL_INCHES = 4.6
ROW_INCHES = 5.0
TABLE_INCHES = 2.6
DPI = 120


def saved_number(value: object, where: str) -> float | None:
    """A saved fact as a float; None where the writer saved None (a fact the stage could not read).

    A value that is neither None nor a finite number is a record that disagrees, and is raised.
    """
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not np.isfinite(value)
    ):
        raise ValueError(f"saved_selection_not_a_number:{where}")
    return float(value)


def saved_whole(value: object, where: str, minimum: int) -> int:
    """A saved count or index: a whole number at or above `minimum`, never a bool, else raised."""
    if type(value) is not int or value < minimum:
        raise ValueError(f"saved_selection_not_a_whole_number:{where}")
    return value


def saved_word(
    value: object, field: str, vocabulary: tuple[str, ...], blank: bool = False
) -> str:
    """A saved word that must be one the stage says (or "" where `blank`), else raised by name."""
    if type(value) is not str or not (value in vocabulary or (blank and value == "")):
        raise ValueError(f"saved_selection_{field}_unknown:{value}")
    return value


def saved_pair(value: object, where: str, length: int) -> tuple[float | None, ...]:
    """A saved list of exactly `length` facts, each a number or None."""
    if type(value) is not list or len(value) != length:
        raise ValueError(f"saved_selection_not_a_list:{where}")
    return tuple(saved_number(item, where) for item in value)


def saved_object(entry: dict) -> pictures.SavedObject:
    """One saved territory, every field checked against the stage's vocabulary and types."""
    if type(entry) is not dict:
        raise ValueError("saved_selection_object_not_a_record")
    missing = [key for key in OBJECT_KEYS if key not in entry]
    if missing:
        raise ValueError(f"saved_selection_object_field_missing:{missing[0]}")
    border, ringed = entry["touches_leg_border"], entry["ringed"]
    if type(border) is not bool:
        raise ValueError("saved_selection_object_not_a_bool:touches_leg_border")
    if type(ringed) is not bool:
        raise ValueError("saved_selection_object_not_a_bool:ringed")
    centre = saved_pair(entry["centre_lps"], "centre_lps", 3)
    extent = saved_pair(entry["superior_extent_mm"], "superior_extent_mm", 2)
    return pictures.SavedObject(
        index=saved_whole(entry["index"], "index", 1),
        role_code=saved_word(entry["role_code"], "role", ROLE_CODES),
        tiles=saved_whole(entry["tiles"], "tiles", 1),
        centre_lps=(centre[0], centre[1], centre[2]),
        superior_mm=saved_number(entry["superior_mm"], "superior_mm"),
        anterior_mm=saved_number(entry["anterior_mm"], "anterior_mm"),
        left_right_mm=saved_number(entry["left_right_mm"], "left_right_mm"),
        superior_extent_mm=(extent[0], extent[1]),
        anterior_face_mm=saved_number(entry["anterior_face_mm"], "anterior_face_mm"),
        touches_leg_border=border,
        ringed=ringed,
    )


def saved_slice(entry: dict) -> pictures.SavedSlice:
    """One chosen slice's saved selection, apart from its arrays, every field checked."""
    if type(entry) is not dict:
        raise ValueError("saved_selection_slice_not_a_record")
    why = entry.get("why")
    if type(why) is not str:
        raise ValueError("saved_selection_slice_field_invalid:why")
    candidates = entry.get("candidate_codes")
    if type(candidates) is not list:
        raise ValueError("saved_selection_slice_field_invalid:candidate_codes")
    peaks = entry.get("peaks_rc")
    if type(peaks) is not list or not all(
        type(peak) is list
        and len(peak) == 2
        and all(type(size) is int and size >= 0 for size in peak)
        for peak in peaks
    ):
        raise ValueError("saved_selection_slice_field_invalid:peaks_rc")
    objects = entry.get("objects")
    if type(objects) is not list:
        raise ValueError("saved_selection_slice_field_invalid:objects")
    return pictures.SavedSlice(
        slice_index=saved_whole(entry.get("slice_index"), "slice_index", -1),
        code=saved_word(entry.get("code"), "code", SELECTION_CODES),
        why=why,
        pair_code=saved_word(entry.get("pair_code"), "pair_code", PAIR_CODES),
        lateral_sign=saved_word(entry.get("lateral_sign"), "sign", SIGN_CODES),
        candidate_codes=tuple(
            saved_word(word, "candidate_code", (*ANTERIOR_CODES, *WITNESS_CODES), True)
            for word in candidates
        ),
        peaks_rc=tuple((int(peak[0]), int(peak[1])) for peak in peaks),
        objects=tuple(saved_object(item) for item in objects),
        border=saved_word(entry.get("border"), "border", BORDER_CODES),
    )


def check_keys(slices: tuple[pictures.SavedSlice, ...]) -> None:
    """A saved slice is named by its border AND its stack index; the same pair twice is raised.

    The same stack index under the two borders is two readings of one slice, both kept; so is the
    same border at two indices. Only an entry whose (border, index) was already saved is a record
    that disagrees with the writer, raised as `saved_selection_slice_repeated` with the pair.
    """
    seen: set[tuple[str, int]] = set()
    for item in slices:
        key = (item.border, item.slice_index)
        if key in seen:
            raise ValueError(
                f"saved_selection_slice_repeated:{item.border}:{item.slice_index}"
            )
        seen.add(key)


def check_view(item: pictures.SavedSlice, plane_kind: str) -> None:
    """The roles and the candidate words of one saved slice must be ones the record's own view says.

    `plane_kind` is the selection record's own told plane word. Within the slice the roles are
    checked first, in the order saved, then the candidate words, so the refusal is always the
    first in that order. A role of another view's rule is
    `saved_selection_role_not_of_view:<view>:<role>`; a candidate word of another view's rule is
    `saved_selection_candidate_not_of_view:<view>:<word>`, and so is any entry at all on a view
    with no candidate decision (the Axial), the blank word included. A plane word that is not
    one of `PLANE_KINDS` is `saved_selection_plane_kind_unknown`.
    """
    if plane_kind not in VIEW_ROLES:
        raise ValueError(f"saved_selection_plane_kind_unknown:{plane_kind}")
    roles = VIEW_ROLES[plane_kind]
    for obj in item.objects:
        if obj.role_code not in roles:
            raise ValueError(
                f"saved_selection_role_not_of_view:{plane_kind}:{obj.role_code}"
            )
    words = VIEW_CANDIDATES[plane_kind]
    allowed = (*words, "") if words else ()
    for word in item.candidate_codes:
        if word not in allowed:
            raise ValueError(
                f"saved_selection_candidate_not_of_view:{plane_kind}:{word}"
            )


def check_slice(item: pictures.SavedSlice, grid: np.ndarray) -> None:
    """The saved objects, labels and peaks of one slice must say one thing, or the record is raised.

    A selection that named territories needs exactly the territories the labels hold, each with
    the tile count the labels give it and its dome peak inside it; one that named none needs a map
    with none. Counting a saved map's labels here checks the record against itself; it draws and
    decides nothing.
    """
    if grid.size and int(grid.min()) < 0:
        raise ValueError("saved_selection_label_negative")
    held = {
        int(label): int(n)
        for label, n in zip(*np.unique(grid[grid > 0], return_counts=True), strict=True)
    }
    if item.code != "present":
        if item.objects or item.candidate_codes:
            raise ValueError("saved_selection_objects_without_territory")
        if item.code == "no_territory" and held:
            raise ValueError("saved_selection_labels_without_objects")
        return
    if sorted(held) != [obj.index for obj in item.objects]:
        raise ValueError("saved_selection_objects_labels_mismatch")
    if item.candidate_codes and len(item.candidate_codes) != len(item.objects):
        raise ValueError("saved_selection_candidate_codes_mismatch")
    for obj in item.objects:
        if held[obj.index] != obj.tiles:
            raise ValueError(f"saved_selection_tiles_mismatch:{obj.index}")
        if obj.index > len(item.peaks_rc):
            raise ValueError(f"saved_selection_peak_missing:{obj.index}")
        row, column = item.peaks_rc[obj.index - 1]
        if row >= grid.shape[0] or column >= grid.shape[1]:
            raise ValueError(f"saved_selection_peak_outside_territory:{obj.index}")
        if int(grid[row, column]) != obj.index:
            raise ValueError(f"saved_selection_peak_outside_territory:{obj.index}")


def saved_selection(run: Path, record: dict) -> tuple[Path, pictures.SelectionPanels]:
    """Reconstitute one series' saved selection and the squint stack that places it, without measuring.

    Total over a series whose writer saved no selection: that is handed on as the silence it is.
    A selection record that is not a mapping, a plane word or code or role or sign the stage does
    not say, vocabularies that are not the stage's, a fact that is not a number, an array whose
    dtype, shape or digest disagrees with its descriptor, a slice count or a grid that is not the
    labels', objects that are not the labels' territories, a peak outside its territory, a
    selection saved without the series' squint stack, or a stack whose grid, slices or plane are
    not the selection's, means the record and this renderer disagree, and is raised rather than
    drawn. The stack is read through the stack drawer's own reader, which validates it against the
    writer's descriptors; its bounds place the tiles.
    """
    artifact = run / record["artifact"]
    descriptors = record["arrays"]
    saved = record.get("selection")
    if saved is None:
        return artifact, pictures.selection_panels(None, (), None, None, None)
    if type(saved) is not dict:
        raise ValueError("saved_selection_not_a_record")
    plane_kind = saved.get("plane_kind")
    if type(plane_kind) is not str or plane_kind not in PLANE_KINDS:
        raise ValueError(f"saved_selection_plane_kind_unknown:{plane_kind}")
    for key, vocabulary in VOCABULARIES.items():
        if saved.get(key) != list(vocabulary):
            raise ValueError("saved_selection_vocabulary_mismatch")
    names = saved.get("arrays")
    if type(names) is not dict or type(names.get(LABELS_ARRAY)) is not str:
        raise ValueError(f"saved_selection_array_unnamed:{LABELS_ARRAY}")
    plane_name = names.get(PLANES_ARRAY)
    if plane_name is not None and type(plane_name) is not str:
        raise ValueError(f"saved_selection_array_unnamed:{PLANES_ARRAY}")
    tiles = saved.get("tiles_rc")
    if not (
        isinstance(tiles, list)
        and len(tiles) == 2
        and all(type(size) is int and size >= 0 for size in tiles)
    ):
        raise ValueError("saved_selection_tiles_invalid")
    entries = saved.get("slices")
    if type(entries) is not list:
        raise ValueError("saved_selection_slices_invalid")
    slices = tuple(saved_slice(entry) for entry in entries)
    check_keys(slices)
    for item in slices:
        check_view(item, plane_kind)
    with np.load(artifact, allow_pickle=False) as arrays:
        labels = saved_array(arrays, descriptors, names[LABELS_ARRAY], 3)
        if labels.dtype != np.int32:
            raise ValueError(f"saved_selection_representation_invalid:{LABELS_ARRAY}")
        planes = None
        if plane_name is not None:
            planes = saved_array(arrays, descriptors, plane_name, 3)
            if planes.dtype.kind not in "iuf":
                raise ValueError(
                    f"saved_selection_representation_invalid:{PLANES_ARRAY}"
                )
    if labels.shape[0] != len(slices) or (
        planes is not None and planes.shape[0] != len(slices)
    ):
        raise ValueError("saved_selection_slices_mismatch")
    if tuple(labels.shape[1:]) != (int(tiles[0]), int(tiles[1])):
        raise ValueError(f"saved_selection_shape_mismatch:{LABELS_ARRAY}")
    for item, grid in zip(slices, labels, strict=True):
        check_slice(item, grid)
    bounds = None
    if labels.size:
        # The selection is made over the series' own squint stack, so a record that saved the
        # one and not the other disagrees with the writer; the stack's grid, slices and plane
        # must be the selection's, because the stack's bounds are what place its tiles.
        if "squint_stack" not in record:
            raise ValueError("saved_selection_without_a_stack")
        _, stack = squint_stack_frames.saved_stack(run, record)
        bounds = stack.bounds_rc
        if bounds is None or tuple(bounds.shape[:2]) != tuple(labels.shape[1:]):
            raise ValueError("saved_selection_grid_mismatch")
        if any(item.slice_index >= stack.slices for item in slices):
            raise ValueError("saved_selection_slice_outside_stack")
        if planes is not None and (int(bounds[-1, -1, 1]), int(bounds[-1, -1, 3])) != (
            tuple(planes.shape[1:])
        ):
            raise ValueError("saved_selection_covers_another_plane")
    return artifact, pictures.selection_panels(
        plane_kind, slices, labels, planes, bounds
    )


def role_counts(step: pictures.ChosenSelection) -> dict[str, int]:
    """How many territories of one slice carry each role, from the saved objects; empty when none."""
    counts: dict[str, int] = {}
    for item in step.objects:
        counts[item.role_code] = counts.get(item.role_code, 0) + 1
    return counts


def number(value: float | None) -> str:
    """A saved fact as text; None is how a fact the stage could not read comes back."""
    return "not read" if value is None else f"{value:.1f}"


def image_name(index: int, record: dict) -> str:
    """One sheet per series, named as the view sheets are: its order, plane and the two flags."""
    view, fluid, fat = record["view"]
    return f"{index:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"


def drawn_order(
    chosen: tuple[pictures.ChosenSelection, ...],
) -> tuple[pictures.ChosenSelection, ...]:
    """The saved slices in the order the sheet draws them: by stack index, and at one index by border.

    The two borders' readings of one slice fall in adjacent columns, in the order of
    `BORDER_CODES`, so the founder compares them side by side; the order the writer saved them in
    does not matter. Nothing is dropped, merged or recomputed: a slice is named by its border AND
    its index. A border that is not a word of `BORDER_CODES` is never reached here, because the
    reader refuses it first.
    """
    return tuple(
        sorted(chosen, key=lambda step: (step.index, BORDER_CODES.index(step.border)))
    )


def panel_title(step: pictures.ChosenSelection) -> str:
    """The first line of a panel's title: its border, its stack index and the lateral sign saved with it.

    Every panel carries this, the silent ones included, so no panel is ever read as the other
    border's reading of the same slice.
    """
    sign = step.lateral_sign if step.lateral_sign is not None else "not saved"
    return f"{step.border} · stack index {step.index} · lateral sign: {sign}"


def selection_lines(record: dict, frame: pictures.SelectionPanels) -> list[str]:
    """The text panel: the series, its view, and each chosen slice's standing, pair word and sign."""
    view, fluid, fat = record["view"]
    lines = [
        fill(record["series_uid"], width=40),
        f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat}",
        "",
    ]
    if frame.plane_kind is None:
        lines.append("selection (objects): not saved")
        lines.append(fill(STANDING_WORDS["selection_not_saved"], width=40))
        return lines
    lines += [f"selection (objects): {frame.plane_kind} rule", ""]
    if not frame.chosen:
        lines.append(fill("no chosen slice was handed to the selection", width=40))
    for step in drawn_order(frame.chosen):
        lines += [
            f"{step.border} · stack index {step.index}: {step.code}",
            f"  standing    {step.standing}",
            f"  pair rule   {step.pair_code}",
            f"  lateral     {step.lateral_sign}",
            f"  territories {len(step.objects)}",
            f"  with a role {sum(1 for o in step.objects if o.role_code != 'unselected')}",
            "",
        ]
    return lines


def table_lines(step: pictures.ChosenSelection) -> list[str]:
    """The slice's territories as a table: every fact the stage read, and the candidate word on each."""
    header = f"{step.border} · stack index {step.index}"
    if not step.objects:
        return [header, fill(STANDING_WORDS[step.standing], width=48)]
    lines = [
        header,
        "idx role                 tiles    S      A      L   edge ring candidate",
    ]
    for position, item in enumerate(step.objects):
        word = step.candidate_codes[position] if step.candidate_codes else ""
        lines.append(
            f"{item.index:>3} {item.role_code:<20} {item.tiles:>4} "
            f"{number(item.superior_mm):>6} {number(item.anterior_mm):>6} "
            f"{number(item.left_right_mm):>6}   "
            f"{'y' if item.touches_leg_border else 'n'}    "
            f"{'y' if item.ringed else 'n'}  {word}"
        )
    lines.append("S superior, A anterior, L left-right: tile-centre means, mm, LPS")
    return lines


def territory_text(item: pictures.SavedObject) -> str:
    """The words written on a territory: its index and role, its tile count and its three coordinates."""
    return (
        f"{item.index} {item.role_code}\n{item.tiles} tiles\n"
        f"S {number(item.superior_mm)} A {number(item.anterior_mm)} "
        f"L {number(item.left_right_mm)}"
    )


def draw_chosen(axis, step: pictures.ChosenSelection, frame: pictures.SelectionPanels):
    """One chosen slice: the plane in grey with every territory tinted by its role, or the silence in words.

    Returns the slice's standing, `tiles_alone` when the territories are drawn with no plane
    beneath, or the silence the panel holds.
    """
    axis.set_axis_off()
    title = panel_title(step)
    if step.standing != "named" or step.labels is None or frame.bounds_rc is None:
        axis.set_title(title, fontsize=8)
        words = STANDING_WORDS[step.standing]
        if step.standing == "selection_absent" and step.why is not None:
            words = f"{words}: {step.why}"
        axis.text(0.03, 0.95, fill(words, width=38), transform=axis.transAxes, va="top")
        return step.standing
    edges = tile_edges(frame.bounds_rc)
    columns_edges, rows_edges = edges
    if step.plane is not None:
        axis.imshow(
            step.plane,
            cmap="gray",
            interpolation="nearest",
            extent=native_extent(step.plane.shape),
        )
        standing, where = "named", "over the acquired plane"
    else:
        standing, where = (
            "tiles_alone",
            "tiles alone: no plane saved at this slice",
        )
    from matplotlib.patches import Patch

    for item in step.objects:
        overlay(
            axis,
            edges,
            step.labels == item.index,
            ROLE_COLOURS[item.role_code],
            alpha=ROLE_ALPHAS[item.role_code],
        )
    for item in step.objects:
        # The index is written at the dome's own saved peak for the territory (territory `k` is
        # peak `k - 1`'s), placed through the stack's saved bounds: no centre is computed here.
        row, column = step.peaks_rc[item.index - 1]
        r0, r1, c0, c1 = (int(v) for v in frame.bounds_rc[row, column])
        axis.text(
            (c0 + c1) / 2,
            (r0 + r1) / 2,
            territory_text(item),
            ha="center",
            va="center",
            fontsize=4.5,
            color="white",
            bbox={"facecolor": "black", "alpha": 0.55, "pad": 1.0, "edgecolor": "none"},
        )
    counts = role_counts(step)
    axis.set_xlim(0, float(columns_edges[-1]))
    axis.set_ylim(float(rows_edges[-1]), 0)
    axis.set_aspect("equal")
    axis.legend(
        handles=[
            Patch(facecolor=ROLE_COLOURS[role], label=f"{role} ({counts[role]})")
            for role in ROLE_CODES
            if role in counts
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.0),
        ncol=2,
        fontsize=5.5,
        frameon=False,
    )
    axis.set_title(
        f"{title}\n{frame.plane_kind} rule, pair rule: {step.pair_code}; territories "
        f"by role, {where}",
        fontsize=8,
    )
    return standing


def draw_table(axis, step: pictures.ChosenSelection) -> None:
    """The slice's table of territories under its panel."""
    axis.set_axis_off()
    axis.text(
        0.0,
        1.0,
        "\n".join(table_lines(step)),
        transform=axis.transAxes,
        va="top",
        family="monospace",
        fontsize=5.5,
    )


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run, one sheet per series, and return its manifest.

    The one entry a caller uses, so the single command can draw every stage without knowing each
    renderer's argument spelling. `main()` is a thin wrapper over it.

    Matplotlib is supplied PER RUN and is never a production dependency, so it is imported after
    every refusal this function can make: the validators above are then importable and testable in
    the ordinary environment.
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
    loaded = [saved_selection(run, record) for record in records]
    if pictures.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:selection")
    # Every standing the adapter can name has words here, and every role a colour and a share of
    # the plane, checked before anything is drawn.
    unworded = [
        name for name in pictures.SELECTION_STANDINGS if name not in STANDING_WORDS
    ]
    if unworded:
        raise RuntimeError(f"selection_standing_unworded:{','.join(unworded)}")
    uncoloured = [
        name
        for name in ROLE_CODES
        if name not in ROLE_COLOURS or name not in ROLE_ALPHAS
    ]
    if uncoloured:
        raise RuntimeError(f"selection_vocabulary_uncoloured:{','.join(uncoloured)}")

    import matplotlib.pyplot as plt

    target.mkdir(parents=True, exist_ok=True)
    series = []
    for index, (record, (artifact, frame)) in enumerate(
        zip(records, loaded, strict=True), start=1
    ):
        across = 1 + max(len(frame.chosen), 1)
        sheet, axes = plt.subplots(
            2,
            across,
            figsize=(PANEL_INCHES * across, ROW_INCHES + TABLE_INCHES),
            height_ratios=(ROW_INCHES, TABLE_INCHES),
            layout="constrained",
            squeeze=False,
        )
        for axis in axes.flat:
            axis.set_axis_off()
        text = axes[0, 0]
        text.set_title("the selection", fontsize=8)
        text.text(
            0.0,
            1.0,
            "\n".join(selection_lines(record, frame)),
            transform=text.transAxes,
            va="top",
            family="monospace",
            fontsize=6.5,
        )
        standings = []
        if not frame.chosen:
            axes[0, 1].text(
                0.03,
                0.5,
                "no chosen slice saved for this series: nothing was selected",
                transform=axes[0, 1].transAxes,
                va="center",
            )
        for column, step in enumerate(frame.chosen, start=1):
            standings.append(
                {
                    "index": step.index,
                    "standing": step.standing,
                    "drawn": draw_chosen(axes[0, column], step, frame),
                    "code": step.code,
                    "pair_code": step.pair_code,
                    "lateral_sign": step.lateral_sign,
                    "roles": role_counts(step),
                }
            )
            draw_table(axes[1, column], step)
        view, fluid, fat = record["view"]
        sheet.suptitle(
            f"The funnel's selection · {view} · fluid-sensitive={fluid}, "
            f"fat-suppressed={fat} · series {record['series_uid']}\n"
            "the selection's standing, then each chosen slice's territories tinted by role, "
            "over the acquired plane where it was saved, placed by the squint stack's own "
            "native bounds; each index is written at its territory's dome peak, with its "
            "facts; the laterality sign is in each title\n"
            + " · ".join(f"{role}: {ROLE_COLOURS[role]}" for role in ROLE_CODES),
            fontsize=9,
        )
        name = image_name(index, record)
        sheet.savefig(target / name, dpi=DPI)
        plt.close(sheet)
        saved = record.get("selection")
        series.append(
            {
                "image": name,
                "image_sha256": sha256((target / name).read_bytes()).hexdigest(),
                "series_uid": record["series_uid"],
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "view": record["view"],
                "selection": None
                if saved is None
                else {
                    "plane_kind": frame.plane_kind,
                    "tiles_rc": list(saved["tiles_rc"]),
                    "slices": len(frame.chosen),
                    "arrays": {
                        short: record["arrays"][key]
                        for short, key in saved["arrays"].items()
                        if key is not None
                    },
                },
                "chosen": standings,
                "frame_kind": "study",
            }
        )
    manifest = {
        "schema": "selection-frames-v1",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "selection": sha256(Path(pictures.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": series[0]["image"],
        "images": [entry["image"] for entry in series],
        "frame_kind": "study",
        "standings": list(pictures.SELECTION_STANDINGS),
        "legend": {
            "role_colours": dict(ROLE_COLOURS),
            "role_alphas": dict(ROLE_ALPHAS),
        },
        "series": series,
        "note": (
            "Every value is a saved one. A slice the stage read no dome for, a dome with no "
            "territory and a selection this run's writer did not save are three silences, each "
            "named; none is a zero. One sheet per series, for the founder's eye-check."
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
