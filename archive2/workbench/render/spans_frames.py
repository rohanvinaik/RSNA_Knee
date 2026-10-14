"""Draw the funnel's round 3: one sheet per series, the spans and the envelope of each chosen slice over its plane.

The-funnel task 9.3 (`openspec/changes/the-funnel/tasks.md`). The funnel's operation 9
(`knee.relations.spans`) names, on each slice the depth collapse chose, every dark body outside
the interstices by what it touches (a span reaches both big objects), and the fluid-like envelope
that touches an interstice with its posterior pouch and the neck joining them. The writer saves
both records beside the series' record; this workbench arranges those saved values through
`knee.pictures.spans`: ONE SHEET PER SERIES, a text panel with the stage's standing in words, then
one panel per chosen slice AND BORDER -- the acquired plane at that slice in grey, the envelope
over it in green with its pouch in a darker green, the above tiles that touch no interstice in a
third tone beside it, and each dark body tinted by its code with its index and side written on
it. The dome is read under two borders and both are kept, so a slice has two panels side by side
and every title names its border. The counts are in each panel's title, the neck's width among them: the
`Envelope` record carries the neck's width and not its row, so the neck is marked in words and the
picture does not invent a place for it. It takes no measurement of its own: every number on the
page is a saved value, and every gap is a named silence, never a zero.

THE SAVED SHAPE (what the writer saves for a series, `record["spans"]` and `record["envelope"]`;
the arrays sit in the series' artifact beside the others and are named in each record's
`arrays`). One series holds several chosen slices, each read under both borders of the dome, so
the arrays are STACKED along their first axis in the order of the record's `slices`, and cut
back by what each entry says:

- `code_names`, `span_code_names`, `side_code_names` (spans) and `code_names`,
  `pouch_code_names` (envelope): the stage's vocabularies, as lists, checked against the stage's;
- `tiles_rc`: [tiles_down, tiles_across], the grid every tile array is over;
- `slices`: one dict per chosen slice AND border, in the order the writer saved them (any order:
  the entries are keyed by `border` and `slice_index` together, never by the slice alone), with
  `slice_index` (-1 for the stage's `predecessor_absent`, which names no slice), `border` (a word
  of `knee.objects.tile_dome.BORDER_CODES`), `code` and `why`; the spans' entry adds `spans`, one
  dict per body in order (`index`, `code`, `side_code`); the envelope's adds `pouch_code`,
  `pouch_count`, `neck_tiles` and `tiles` (the envelope's count);
- `arrays`: the short names of the stacked arrays. Spans: `tiles` bool (B, tiles_down,
  tiles_across) and `centre_lps` float64 (B, 3), every body of every entry in order, B the number
  of bodies the entries list. Envelope: `tiles`, `pouch_tiles` and `unjoined` bool (K,
  tiles_down, tiles_across), one per entry; `unjoined` is every above tile of a component that
  touches no interstice, kept beside the envelope and never inside it. Either record may also
  name `planes`, any numeric dtype, (K, rows, columns): the acquired plane at each of its
  entries, in entry order, which the writer holds and the study stage's walk need not.

The plane of a chosen slice is a silence of its own. The chosen slice is generally neither a slice
the study stage walks nor the objects stage's selected slice, so the plane comes from the first
source that has one (`knee.pictures.spans.PLANE_SOURCES`): the planes the writer saved for the
slices, the walk, the selected plane; a slice with none draws its tiles alone on the tile grid and
the title says so. Five standings of a record are kept apart, because each has its own remedy
(`knee.pictures.spans.STANDINGS`): this run's writer saved none for the slice; the saved code is a
word the stage does not say; the stage had no predecessor and says why; the stage read and found
nothing to name.

A record the stage did not make is a record this drawer cannot arrange, and a record that
disagrees with the writer -- a vocabulary that is not the stage's, a code it does not say, a
border it does not say, a grid that is not the squint stack's, a slice outside the stack, a
(border, slice) named twice, an array whose dtype, shape or digest disagrees with its descriptor
or whose length is not what the entries list, a count that is not its array's, an unjoined tile
that is also an envelope tile, a plane of another shape than the stack's -- is refused by name
rather than drawn.

Nothing here thresholds, labels, dilates or recomputes. The grey scale is Matplotlib's linear
display scale over each plane's own stored values.
"""

import argparse
import json
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from textwrap import fill
from typing import Any, cast

import numpy as np

from knee.objects.tile_dome import BORDER_CODES
from knee.pictures import spans as pictures
from knee.relations.interstice import SIDE_CODES
from knee.relations.spans import (
    ENVELOPE_CODES,
    POUCH_CODES,
    SPAN_CODES,
    SPANS_RECORD_CODES,
    Envelope,
    Span,
    Spans,
)
from workbench.render import squint_stack_frames
from workbench.render._out import PROJECT, ArgumentRefusal
from workbench.render.field_frames import (
    native_extent,
    overlay,
    saved_array,
    tile_edges,
)

#: The spans' stacked arrays by the short names the writer gives them in `record["spans"]
#: ["arrays"]`, each with the dtype it must have and its number of axes: every body of every
#: slice, one after the other, `tiles` (B, TR, TC) and `centre_lps` (B, 3).
SPANS_ARRAYS: Mapping[str, tuple[np.dtype, int]] = {
    "tiles": (np.dtype(np.bool_), 3),
    "centre_lps": (np.dtype(np.float64), 2),
}

#: The envelope's likewise, one tile map per entry: `tiles`, `pouch_tiles` and `unjoined`, each
#: (K, TR, TC).
ENVELOPE_ARRAYS: Mapping[str, tuple[np.dtype, int]] = {
    "tiles": (np.dtype(np.bool_), 3),
    "pouch_tiles": (np.dtype(np.bool_), 3),
    "unjoined": (np.dtype(np.bool_), 3),
}

#: The optional stacked planes either record may name: (K, rows, columns), one per slice entry.
PLANES_ARRAY = "planes"

#: The vocabularies each saved record carries beside its codes, which must be the stage's.
SPANS_VOCABULARIES: Mapping[str, tuple[str, ...]] = {
    "code_names": SPANS_RECORD_CODES,
    "span_code_names": SPAN_CODES,
    "side_code_names": SIDE_CODES,
}
ENVELOPE_VOCABULARIES: Mapping[str, tuple[str, ...]] = {
    "code_names": ENVELOPE_CODES,
    "pouch_code_names": POUCH_CODES,
}

#: What each standing of a record says, in words. The codes are the adapter's
#: (`knee.pictures.spans.STANDINGS`); the words are this drawing's, one set for each record.
SPANS_WORDS: Mapping[str, str] = {
    "named": "every dark body, tinted by its code, with its index and side",
    "not_saved": "not saved: this run's writer saved no spans for this slice",
    "code_unknown": "not drawn: the saved code is one the stage does not say",
    "predecessor_absent": "not made: the stage had no conjunction, selection, dome or interstice to read",
    "none_found": "no dark body lies outside every interstice at this slice",
}
ENVELOPE_WORDS: Mapping[str, str] = {
    "named": "the body of above tiles that touches an interstice, with its pouch",
    "not_saved": "not saved: this run's writer saved no envelope for this slice",
    "code_unknown": "not drawn: the saved code is one the stage does not say",
    "predecessor_absent": "not made: the stage had no digits, selection or interstice to read",
    "none_found": "no above tile touches an interstice at this slice",
}

#: What each source of a chosen slice's plane says, in words.
PLANE_WORDS: Mapping[str, str] = {
    "saved_for_slice": "over the acquired plane the writer saved for this slice",
    "study_walk": "over the study stage's walked plane at this slice",
    "selected_plane": "over the objects stage's selected plane",
    "plane_not_saved": "tiles alone: no acquired plane is saved for this slice",
}

#: What each span code is drawn in; the envelope and its pouch are two tones of one green. None
#: is a grey, so no stored value is ever mistaken for a reading. The above tiles that touch no
#: interstice are kept beside the envelope and drawn in a tone of their own (cyan).
SPAN_COLOURS: Mapping[str, str] = {
    "span": "#ef4444",
    "touches_one": "#facc15",
    "touches_none": "#a855f7",
    "inside_interstice": "#3b82f6",
    "invalid_measurement": "#ff00ff",
}
ENVELOPE_COLOUR = "#22c55e"
POUCH_COLOUR = "#064e3b"
UNJOINED_COLOUR = "#06b6d4"
TINT_ALPHA = 0.5
POUCH_ALPHA = 0.85

#: What a body's side is written as on the picture.
SIDE_WORDS: Mapping[str, str] = {
    "medial": "medial",
    "lateral": "lateral",
    "side_abstained": "side ?",
    "invalid_measurement": "side !",
}

#: How to read a panel, written in the text panel so the sheet's title stays one line. The neck
#: is marked by its width in each panel's title: the `Envelope` carries the width, not its row.
KEY_LINES: tuple[str, ...] = (
    "how to read the panels",
    "  red: a span, a dark body that reaches",
    "    both big objects, outside every",
    "    interstice",
    "  yellow: a dark body reaching one",
    "  purple: a dark body reaching neither",
    "  blue: a dark body inside an interstice",
    "  green: the envelope; dark green: its pouch",
    "  cyan: above tiles touching no interstice,",
    "    kept beside the envelope",
    "  on each body: its index and its side",
    "  the neck: its width, in each title",
    "    (the record carries the width, not",
    "    its row)",
    "  each title names its border; the two",
    "    borders of a slice sit side by side",
)

#: One sheet per series: the text panel, then one panel per chosen slice. The sheet grows taller
#: when the text panel holds more lines than ROW_INCHES fits, at LINE_INCHES a line.
PANEL_INCHES = 4.6
ROW_INCHES = 5.6
LINE_INCHES = 0.12
DPI = 120


def saved_shell(
    kind: str,
    saved: object,
    vocabularies: Mapping[str, tuple[str, ...]],
    arrays_wanted: tuple[str, ...],
    grid: tuple[int, int],
    stack_slices: int,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """The slice entries and the array names of one saved record, once its shell agrees.

    A record that is not a mapping, a vocabulary that is not the stage's, a tile grid that is not
    the squint stack's, an array table that does not name every array in `arrays_wanted` (and
    `planes` as text when it names it), a slice list that is not a list, an entry that is not a
    mapping, a slice index that is not a whole number, outside the stack, or below zero without
    being the stage's `predecessor_absent`, a border that is not a word of `BORDER_CODES`, a
    (border, slice index) pair named twice, a code the stage does not say, a reason that is not
    text, is raised by name. The same slice under the two borders is two entries and agrees.
    """
    if type(saved) is not dict:
        raise ValueError(f"saved_{kind}_not_a_record")
    for key, expected in vocabularies.items():
        if saved.get(key) != list(expected):
            raise ValueError(f"saved_{kind}_vocabulary_mismatch")
    tiles = saved.get("tiles_rc")
    if not (
        isinstance(tiles, list)
        and len(tiles) == 2
        and all(type(size) is int and size >= 0 for size in tiles)
    ):
        raise ValueError(f"saved_{kind}_tiles_invalid")
    if (tiles[0], tiles[1]) != grid:
        raise ValueError(f"saved_{kind}_grid_mismatch")
    names = saved.get("arrays")
    if type(names) is not dict:
        raise ValueError(f"saved_{kind}_arrays_missing")
    for short in (*arrays_wanted, *((PLANES_ARRAY,) if PLANES_ARRAY in names else ())):
        if type(names.get(short)) is not str:
            raise ValueError(f"saved_{kind}_array_unnamed:{short}")
    entries = saved.get("slices")
    if type(entries) is not list:
        raise ValueError(f"saved_{kind}_slices_invalid")
    seen: set[tuple[str, int]] = set()
    checked: list[dict[str, Any]] = []
    for item in entries:
        if type(item) is not dict:
            raise ValueError(f"saved_{kind}_slice_not_a_record")
        entry = cast("dict[str, Any]", item)
        index = entry.get("slice_index")
        if type(index) is not int:
            raise ValueError(f"saved_{kind}_slice_index_invalid")
        border = entry.get("border")
        if border not in BORDER_CODES:
            raise ValueError(f"saved_{kind}_border_unknown:{border}")
        if (border, index) in seen:
            raise ValueError(f"saved_{kind}_slice_repeated:{border}:{index}")
        seen.add((border, index))
        for key in ("code", "why"):
            if type(entry.get(key)) is not str:
                raise ValueError(f"saved_{kind}_field_invalid:{key}")
        if entry["code"] not in vocabularies["code_names"]:
            raise ValueError(f"saved_{kind}_code_unknown:{entry['code']}")
        if index < 0 and entry["code"] != "predecessor_absent":
            raise ValueError(f"saved_{kind}_slice_index_invalid")
        if index >= stack_slices:
            raise ValueError(f"saved_{kind}_slice_outside_stack:{index}")
        checked.append(entry)
    return checked, cast("dict[str, str]", names)


def saved_stacked(
    arrays: Mapping[str, np.ndarray],
    descriptors: dict,
    kind: str,
    names: dict[str, str],
    short: str,
    dtype: np.dtype,
    ndim: int,
) -> np.ndarray:
    """One stacked array a record names, validated against the writer's descriptor and the stage's dtype."""
    array = saved_array(arrays, descriptors, names[short], ndim)
    if array.dtype != dtype:
        raise ValueError(f"saved_{kind}_representation_invalid:{short}")
    return array


def saved_count(value: object, where: str) -> int:
    """A saved count: a whole number at or above zero, and not a bool."""
    if type(value) is not int or value < 0:
        raise ValueError(f"saved_envelope_count_invalid:{where}")
    return value


def saved_spans(
    arrays: Mapping[str, np.ndarray],
    descriptors: dict,
    names: dict[str, str],
    entries: list[dict[str, Any]],
    series_uid: str,
    grid: tuple[int, int],
) -> tuple[Spans, ...]:
    """Reconstitute the stage's `Spans` of every chosen slice from the saved entries and stacked arrays.

    The stacked arrays hold every body of every slice one after the other, so each entry takes
    the next as many bodies as it lists. The bodies' codes and sides must be the stage's, and
    the arrays' lengths the number of bodies listed, each the dtype and shape the stage returns;
    anything else is raised by name.
    """
    counts = []
    for entry in entries:
        if type(entry.get("spans")) is not list:
            raise ValueError("saved_spans_bodies_invalid")
        counts.append(len(entry["spans"]))
    drawn = {
        short: saved_stacked(arrays, descriptors, "spans", names, short, dtype, ndim)
        for short, (dtype, ndim) in SPANS_ARRAYS.items()
    }
    total = sum(counts)
    if drawn["tiles"].shape != (total, *grid) or drawn["centre_lps"].shape != (
        total,
        3,
    ):
        raise ValueError("saved_spans_shape_mismatch")
    readings = []
    start = 0
    for entry, count in zip(entries, counts, strict=True):
        bodies = []
        for offset, item in enumerate(entry["spans"]):
            if type(item) is not dict:
                raise ValueError("saved_spans_body_not_a_record")
            body = cast("dict[str, Any]", item)
            if type(body.get("index")) is not int:
                raise ValueError("saved_spans_body_index_invalid")
            if body.get("code") not in SPAN_CODES:
                raise ValueError(f"saved_spans_body_code_unknown:{body.get('code')}")
            if body.get("side_code") not in SIDE_CODES:
                raise ValueError(f"saved_spans_side_unknown:{body.get('side_code')}")
            bodies.append(
                Span(
                    index=body["index"],
                    tiles=drawn["tiles"][start + offset],
                    centre_lps=drawn["centre_lps"][start + offset],
                    code=body["code"],
                    side_code=body["side_code"],
                )
            )
        start += count
        readings.append(
            Spans(
                series_uid=series_uid,
                slice_index=entry["slice_index"],
                code=entry["code"],
                why=entry["why"],
                spans=tuple(bodies),
                border=entry["border"],
            )
        )
    return tuple(readings)


def saved_envelope(
    arrays: Mapping[str, np.ndarray],
    descriptors: dict,
    names: dict[str, str],
    entries: list[dict[str, Any]],
    series_uid: str,
    grid: tuple[int, int],
) -> tuple[Envelope, ...]:
    """Reconstitute the stage's `Envelope` of every chosen slice from the saved entries and arrays.

    The stacked arrays hold one tile map per entry, in entry order. Each pouch code must be the
    stage's, each count a whole number and the array's own, each array the dtype and grid the
    stage returns, each pouch inside its envelope and no unjoined tile inside it (the stage keeps
    them beside the envelope, never in it); anything else is raised by name.
    """
    drawn = {
        short: saved_stacked(arrays, descriptors, "envelope", names, short, dtype, ndim)
        for short, (dtype, ndim) in ENVELOPE_ARRAYS.items()
    }
    expected = (len(entries), *grid)
    if any(array.shape != expected for array in drawn.values()):
        raise ValueError("saved_envelope_shape_mismatch")
    readings = []
    for position, entry in enumerate(entries):
        if entry.get("pouch_code") not in POUCH_CODES:
            raise ValueError(
                f"saved_envelope_pouch_code_unknown:{entry.get('pouch_code')}"
            )
        pouch_count = saved_count(entry.get("pouch_count"), "pouch_count")
        neck_tiles = saved_count(entry.get("neck_tiles"), "neck_tiles")
        tile_count = saved_count(entry.get("tiles"), "tiles")
        tiles, pouch = drawn["tiles"][position], drawn["pouch_tiles"][position]
        if tile_count != int(np.count_nonzero(tiles)) or pouch_count != int(
            np.count_nonzero(pouch)
        ):
            raise ValueError("saved_envelope_count_mismatch")
        if (pouch & ~tiles).any():
            raise ValueError("saved_envelope_pouch_outside_envelope")
        unjoined = drawn["unjoined"][position]
        if (unjoined & tiles).any():
            raise ValueError("saved_envelope_unjoined_overlaps_envelope")
        readings.append(
            Envelope(
                series_uid=series_uid,
                slice_index=entry["slice_index"],
                code=entry["code"],
                why=entry["why"],
                tiles=tiles,
                pouch_tiles=pouch,
                pouch_count=pouch_count,
                neck_tiles=neck_tiles,
                pouch_code=entry["pouch_code"],
                unjoined=unjoined,
                border=entry["border"],
            )
        )
    return tuple(readings)


def saved_planes(
    arrays: Mapping[str, np.ndarray],
    descriptors: dict,
    kind: str,
    names: dict[str, str],
    entries: list[dict[str, Any]],
    planes: dict[int, np.ndarray],
) -> None:
    """Add the planes a record names (one per slice entry, in order) to `planes`, by slice index.

    Only a record that names `planes` adds any; the first plane named for a slice stands, and a
    slice that names no slice (index -1) has none. A stack that is not numeric, or is not one
    plane per entry, is raised by name.
    """
    if PLANES_ARRAY not in names:
        return
    stacked = saved_array(arrays, descriptors, names[PLANES_ARRAY], 3)
    if stacked.dtype.kind not in "iuf":
        raise ValueError(f"saved_{kind}_representation_invalid:{PLANES_ARRAY}")
    if stacked.shape[0] != len(entries):
        raise ValueError(f"saved_{kind}_shape_mismatch:{PLANES_ARRAY}")
    for position, entry in enumerate(entries):
        if entry["slice_index"] >= 0:
            planes.setdefault(entry["slice_index"], stacked[position])


def saved_round_three(
    run: Path, record: dict
) -> tuple[Path, pictures.RoundThreePanels]:
    """Reconstitute one series' saved spans and envelope and the planes to lay them over, without measuring.

    Total over a series whose writer saved neither: that is handed on as the silence it is. A
    record saved without the series' squint stack (the stack's bounds place the tiles), or over
    another grid than the stack's, a walk whose saved indices are not a list or do not match its
    planes, a plane of another shape than the stack's, and everything `saved_shell`,
    `saved_spans` and `saved_envelope` refuse, means the record and this renderer disagree, and is
    raised rather than drawn. The stack is read through the stack drawer's own reader, which
    validates it against the writer's descriptors.
    """
    artifact = run / record["artifact"]
    descriptors = record["arrays"]
    saved_spans_record = record.get("spans")
    saved_envelope_record = record.get("envelope")
    if saved_spans_record is None and saved_envelope_record is None:
        return artifact, pictures.round_three_panels(
            None, None, None, {}, (), None, None, None
        )
    # The stack drawer's reader validates the stack against the writer's descriptors and the
    # study's saved walk against its planes, and refuses either by name before anything here.
    _, stack = squint_stack_frames.saved_stack(run, record)
    bounds = stack.bounds_rc
    if "squint_stack" not in record or bounds is None:
        raise ValueError("saved_round_three_without_a_stack")
    grid = (int(bounds.shape[0]), int(bounds.shape[1]))
    native = (int(bounds[-1, -1, 1]), int(bounds[-1, -1, 3])) if bounds.size else (0, 0)
    saved_study = record.get("study") or {}
    walk_name = saved_study.get("walk_array")
    walk_indices = tuple(saved_study.get("walk_indices", ()))
    planes: dict[int, np.ndarray] = {}
    spans = envelopes = None
    with np.load(artifact, allow_pickle=False) as arrays:
        if saved_spans_record is not None:
            entries, names = saved_shell(
                "spans",
                saved_spans_record,
                SPANS_VOCABULARIES,
                tuple(SPANS_ARRAYS),
                grid,
                stack.slices,
            )
            spans = saved_spans(
                arrays, descriptors, names, entries, record["series_uid"], grid
            )
            saved_planes(arrays, descriptors, "spans", names, entries, planes)
        if saved_envelope_record is not None:
            entries, names = saved_shell(
                "envelope",
                saved_envelope_record,
                ENVELOPE_VOCABULARIES,
                tuple(ENVELOPE_ARRAYS),
                grid,
                stack.slices,
            )
            envelopes = saved_envelope(
                arrays, descriptors, names, entries, record["series_uid"], grid
            )
            saved_planes(arrays, descriptors, "envelope", names, entries, planes)
        walk = (
            saved_array(arrays, descriptors, walk_name, 3)
            if walk_name is not None
            else None
        )
        selected = None
        if "acquired_plane" in descriptors:
            selected = saved_array(arrays, descriptors, "acquired_plane", 2)
            if selected.dtype.kind not in "iuf":
                raise ValueError("saved_array_representation_invalid:acquired_plane")
    panels = pictures.round_three_panels(
        spans,
        envelopes,
        bounds,
        planes,
        walk_indices,
        walk,
        record.get("slice_index"),
        selected,
    )
    for chosen in panels.slices:
        if chosen.plane is not None and tuple(chosen.plane.shape) != native:
            raise ValueError("saved_round_three_covers_another_plane")
    return artifact, panels


def body_counts(spans: Spans | None) -> dict[str, int]:
    """How many saved bodies carry each span code, from the saved codes; empty when none."""
    if spans is None:
        return {}
    return {
        name: sum(1 for body in spans.spans if body.code == name)
        for name in SPAN_CODES
        if any(body.code == name for body in spans.spans)
    }


def spans_text(chosen: pictures.ChosenSlice) -> str:
    """The spans' line of a panel: the stage's standing in words, with the saved bodies counted."""
    if chosen.spans_standing not in ("named", "none_found"):
        return f"spans: {SPANS_WORDS[chosen.spans_standing]}"
    counts = body_counts(chosen.spans)
    tally = " · ".join(f"{n} {name}" for name, n in counts.items()) or "no body"
    if chosen.spans_standing == "none_found":
        return f"spans: {SPANS_WORDS['none_found']} ({tally})"
    return f"spans: {tally}"


def envelope_text(chosen: pictures.ChosenSlice) -> str:
    """The envelope's line of a panel: the stage's standing in words, then its tiles, pouch, neck and unjoined tiles."""
    envelope = chosen.envelope
    if chosen.envelope_standing != "named" or envelope is None:
        return f"envelope: {ENVELOPE_WORDS[chosen.envelope_standing]}"
    return (
        f"envelope: {tiles_word(int(np.count_nonzero(envelope.tiles)))} · pouch "
        f"{envelope.pouch_count} ({envelope.pouch_code}) · neck "
        f"{tiles_word(envelope.neck_tiles)} · unjoined "
        f"{tiles_word(int(np.count_nonzero(envelope.unjoined)))}"
    )


def panel_title(chosen: pictures.ChosenSlice) -> str:
    """A panel's title: the border it was read under, its stack index and plane, then the two records' lines."""
    return (
        f"{chosen.border} · stack index {chosen.index} · {PLANE_WORDS[chosen.plane_source]}\n"
        f"{fill(spans_text(chosen), width=60)}\n{fill(envelope_text(chosen), width=60)}"
    )


def tiles_word(count: int) -> str:
    """A saved count of tiles as words: one tile, two tiles, zero tiles."""
    return f"{count} tile" if count == 1 else f"{count} tiles"


def sheet_lines(record: dict, panels: pictures.RoundThreePanels) -> list[str]:
    """The text panel: the series, its view, and each chosen slice's standing under each border in words."""
    view, fluid, fat = record["view"]
    lines = [
        fill(record["series_uid"], width=40),
        f"{view} · fluid-sensitive={fluid}, fat-suppressed={fat}",
        "",
    ]
    if "spans" not in record and "envelope" not in record:
        lines.append("round 3 (relations): not saved")
        lines.append(
            fill("this run's writer saved no spans and no envelope for this series", 40)
        )
        return lines
    if not panels.slices:
        lines.append("round 3 (relations): saved, naming no chosen slice")
        return lines
    lines.append(
        f"round 3 (relations): {len(panels.slices)} readings, one per chosen slice and border"
    )
    for chosen in panels.slices:
        lines += [
            "",
            f"stack index {chosen.index} · {chosen.border}",
            fill(f"  {PLANE_WORDS[chosen.plane_source]}", width=40),
            fill(f"  {spans_text(chosen)}", width=40),
            fill(f"  {envelope_text(chosen)}", width=40),
        ]
        # A reading's reason is long and sits in the manifest whole; a silence's reason is what
        # explains the gap, so it is written here.
        for record_at, standing_at in (
            (chosen.spans, chosen.spans_standing),
            (chosen.envelope, chosen.envelope_standing),
        ):
            if record_at is not None and standing_at != "named":
                lines.append(fill(f"  {record_at.code}: {record_at.why}", width=40))
    return [*lines, "", *KEY_LINES]


def draw_chosen(axis, chosen: pictures.ChosenSlice, bounds_rc: np.ndarray) -> dict:
    """One chosen slice under one border: the plane in grey, the envelope, its pouch and the unjoined tiles, and each body by its code.

    Returns what was drawn: the border, the two standings and the plane source. Each record
    answers for itself: one the stage did not make says why in the title and the other still draws.
    """
    from matplotlib.patches import Patch

    axis.set_axis_off()
    columns_edges, rows_edges = edges = tile_edges(bounds_rc)
    if chosen.plane is not None:
        axis.imshow(
            chosen.plane,
            cmap="gray",
            interpolation="nearest",
            extent=native_extent(chosen.plane.shape),
        )
    handles = []
    envelope = chosen.envelope
    if chosen.envelope_standing == "named" and envelope is not None:
        # The unjoined tiles first, beneath: they never overlap the envelope, and a tone of their own.
        if envelope.unjoined.any():
            overlay(axis, edges, envelope.unjoined, UNJOINED_COLOUR, alpha=TINT_ALPHA)
        if envelope.tiles.any():
            overlay(axis, edges, envelope.tiles, ENVELOPE_COLOUR, alpha=TINT_ALPHA)
        if envelope.pouch_tiles.any():
            overlay(axis, edges, envelope.pouch_tiles, POUCH_COLOUR, alpha=POUCH_ALPHA)
        handles.append(
            Patch(
                facecolor=ENVELOPE_COLOUR,
                label=f"envelope ({int(np.count_nonzero(envelope.tiles))})",
            )
        )
        handles.append(
            Patch(facecolor=POUCH_COLOUR, label=f"pouch ({envelope.pouch_count})")
        )
        handles.append(
            Patch(
                facecolor=UNJOINED_COLOUR,
                label=f"unjoined ({int(np.count_nonzero(envelope.unjoined))})",
            )
        )
    spans = chosen.spans
    if chosen.spans_standing in ("named", "none_found") and spans is not None:
        for name, count in body_counts(spans).items():
            handles.append(
                Patch(facecolor=SPAN_COLOURS[name], label=f"{name} ({count})")
            )
        for body in spans.spans:
            rows, columns = np.nonzero(body.tiles)
            if rows.size:
                overlay(
                    axis, edges, body.tiles, SPAN_COLOURS[body.code], alpha=TINT_ALPHA
                )
                pick = rows.size // 2
                axis.text(
                    0.5
                    * (columns_edges[columns[pick]] + columns_edges[columns[pick] + 1]),
                    0.5 * (rows_edges[rows[pick]] + rows_edges[rows[pick] + 1]),
                    f"{body.index} {SIDE_WORDS[body.side_code]}",
                    color="white",
                    fontsize=6,
                    ha="center",
                    va="center",
                    bbox={
                        "facecolor": "black",
                        "edgecolor": "none",
                        "alpha": 0.55,
                        "pad": 0.6,
                    },
                )
    axis.set_xlim(0, float(columns_edges[-1]))
    axis.set_ylim(float(rows_edges[-1]), 0)
    axis.set_aspect("equal")
    if handles:
        axis.legend(
            handles=handles,
            loc="upper center",
            bbox_to_anchor=(0.5, 0.0),
            ncol=3,
            fontsize=5.5,
            frameon=False,
        )
    axis.set_title(panel_title(chosen), fontsize=7)
    return {
        "index": chosen.index,
        "border": chosen.border,
        "plane_source": chosen.plane_source,
        "spans_standing": chosen.spans_standing,
        "envelope_standing": chosen.envelope_standing,
    }


def image_name(index: int, record: dict) -> str:
    """One sheet per series, named as the view sheets are: its order, plane and the two flags."""
    view, fluid, fat = record["view"]
    return f"{index:02d}-{view.lower()}-fs{fluid}-fat{fat}.png"


def spans_manifest(panels: pictures.RoundThreePanels) -> list[dict]:
    """What the sheet says of each chosen slice's spans under each border, from the saved records alone."""
    return [
        {
            "slice_index": chosen.index,
            "border": chosen.border,
            "standing": chosen.spans_standing,
            "code": None if chosen.spans is None else chosen.spans.code,
            "why": None if chosen.spans is None else chosen.spans.why,
            "bodies": [
                {"index": b.index, "code": b.code, "side_code": b.side_code}
                for b in ([] if chosen.spans is None else chosen.spans.spans)
            ],
            "counts": body_counts(chosen.spans),
        }
        for chosen in panels.slices
    ]


def envelope_manifest(panels: pictures.RoundThreePanels) -> list[dict]:
    """What the sheet says of each chosen slice's envelope under each border, from the saved records alone."""
    rows = []
    for chosen in panels.slices:
        envelope = chosen.envelope
        rows.append(
            {
                "slice_index": chosen.index,
                "border": chosen.border,
                "standing": chosen.envelope_standing,
                "code": None if envelope is None else envelope.code,
                "why": None if envelope is None else envelope.why,
                "tiles": None
                if envelope is None
                else int(np.count_nonzero(envelope.tiles)),
                "unjoined": None
                if envelope is None
                else int(np.count_nonzero(envelope.unjoined)),
                "pouch_count": None if envelope is None else envelope.pouch_count,
                "neck_tiles": None if envelope is None else envelope.neck_tiles,
                "pouch_code": None if envelope is None else envelope.pouch_code,
            }
        )
    return rows


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run, one sheet per series, and return its manifest.

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
    loaded = [saved_round_three(run, record) for record in records]
    if pictures.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:spans")
    # Every standing and plane source the adapter can name has words here, and every span code a
    # colour, checked before anything is drawn: a code with no colour would be drawn in none.
    unworded = [
        *(name for name in pictures.STANDINGS if name not in SPANS_WORDS),
        *(name for name in pictures.STANDINGS if name not in ENVELOPE_WORDS),
        *(name for name in pictures.PLANE_SOURCES if name not in PLANE_WORDS),
    ]
    if unworded:
        raise RuntimeError(f"round_three_unworded:{','.join(unworded)}")
    uncoloured = [
        *(name for name in SPAN_CODES if name not in SPAN_COLOURS),
        *(name for name in SIDE_CODES if name not in SIDE_WORDS),
    ]
    if uncoloured:
        raise RuntimeError(f"round_three_vocabulary_uncoloured:{','.join(uncoloured)}")

    import matplotlib.pyplot as plt

    target.mkdir(parents=True, exist_ok=True)
    series = []
    for index, (record, (artifact, panels)) in enumerate(
        zip(records, loaded, strict=True), start=1
    ):
        across = 1 + max(len(panels.slices), 1)
        lines = sheet_lines(record, panels)
        sheet, axes = plt.subplots(
            1,
            across,
            figsize=(
                PANEL_INCHES * across,
                max(ROW_INCHES, LINE_INCHES * len(lines) + 1.2),
            ),
            layout="constrained",
            squeeze=False,
        )
        for axis in axes.flat:
            axis.set_axis_off()
        text = axes[0, 0]
        text.set_title("round 3: the spans and the envelope", fontsize=8)
        text.text(
            0.0,
            1.0,
            "\n".join(lines),
            transform=text.transAxes,
            va="top",
            family="monospace",
            fontsize=6.5,
        )
        drawn = []
        if not panels.slices:
            axes[0, 1].text(
                0.03,
                0.5,
                "no chosen slice saved for this series: nothing to draw",
                transform=axes[0, 1].transAxes,
                va="center",
            )
        for column, chosen in enumerate(panels.slices, start=1):
            # `saved_round_three` holds the stack's bounds whenever it holds a chosen slice.
            bounds = cast("np.ndarray", panels.bounds_rc)
            drawn.append(draw_chosen(axes[0, column], chosen, bounds))
        view, fluid, fat = record["view"]
        sheet.suptitle(
            f"The funnel's round 3 · {view} · fluid-sensitive={fluid}, fat-suppressed={fat} "
            f"· series {record['series_uid']}",
            fontsize=9,
        )
        name = image_name(index, record)
        sheet.savefig(target / name, dpi=DPI)
        plt.close(sheet)
        series.append(
            {
                "image": name,
                "image_sha256": sha256((target / name).read_bytes()).hexdigest(),
                "series_uid": record["series_uid"],
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "view": record["view"],
                "spans": None
                if "spans" not in record
                else {
                    "slices": spans_manifest(panels),
                    "arrays": {
                        short: record["arrays"][key]
                        for short, key in record["spans"]["arrays"].items()
                    },
                },
                "envelope": None
                if "envelope" not in record
                else {
                    "slices": envelope_manifest(panels),
                    "arrays": {
                        short: record["arrays"][key]
                        for short, key in record["envelope"]["arrays"].items()
                    },
                },
                "chosen": drawn,
                "frame_kind": "study",
            }
        )
    manifest = {
        "schema": "spans-frames-v2",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "spans": sha256(Path(pictures.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": series[0]["image"],
        "images": [entry["image"] for entry in series],
        "frame_kind": "study",
        "standings": list(pictures.STANDINGS),
        "plane_sources": list(pictures.PLANE_SOURCES),
        "legend": {
            "span_codes": dict(SPAN_COLOURS),
            "envelope": ENVELOPE_COLOUR,
            "pouch": POUCH_COLOUR,
            "unjoined": UNJOINED_COLOUR,
            "sides": dict(SIDE_WORDS),
        },
        "series": series,
        "note": (
            "Every value is a saved one. Spans or an envelope this run's writer did not save, "
            "a saved code the stage does not say, a stage that had no predecessor, a stage "
            "that found nothing to name, and a chosen slice with no plane saved are five "
            "silences, each named; none is a zero. The neck is marked by its width: the record "
            "carries no row for it."
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
