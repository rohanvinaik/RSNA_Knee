"""What round 3 resolved, drawn: the spans and the envelope of each chosen slice, tinted over its plane.

The funnel's operation 9 (`openspec/changes/the-funnel/design.md` R9, task 9.3):
`knee.relations.spans.read_spans` names every dark body of a chosen slice by what it touches (a
span reaches both big objects outside every interstice), and `read_envelope` names the fluid-like
body that touches an interstice, with its posterior pouch and the neck joining them. Its picture is
the one the design states: per chosen slice, each span tinted by its code with its side written on
it, the envelope tinted with its pouch in a second tone, the counts in the title, over the acquired
plane at that slice, each tile placed in native pixels by the squint stack's saved bounds.

Every value here is one the stage computed and the writer saved, handed on as the stage's own
records (`Spans`, `Envelope`): the drawer reconstitutes them from the saved arrays and checks them
against the stage's vocabularies, and this module only chooses which stored values to show for
which slice. Nothing here measures, thresholds, labels or recomputes. Two things the stage does not
record are therefore not drawn, and the picture says so in words rather than inventing them: the
neck's location (the `Envelope` carries its width in tiles, not its row, so the neck is marked by
its width in the title) and a plane the writer did not save for a chosen slice.

Two decisions are pure and total. `standing` names what one saved record of one chosen slice can
show; `plane_source` names where the picture of one chosen slice gets its plane, because the chosen
slice is generally neither a slice the study stage walks nor the objects stage's selected slice, and
a slice with no plane saved is drawn on the tile grid alone and says so.

The dome is read under two borders (`knee.objects.tile_dome.BORDER_CODES`), both seated, and every
record below it carries the border it was read under. So a saved record is keyed by its border AND
its slice, never by the slice alone: a panel is one chosen slice under one border, the two borders'
panels of one slice sit next to each other so they can be compared, and nothing read under one
border is ever shown under the other.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TypeVar

import numpy as np

from knee.objects.tile_dome import BORDER_CODES
from knee.relations.spans import ENVELOPE_CODES, SPANS_RECORD_CODES, Envelope, Spans

_Saved = TypeVar("_Saved", Spans, Envelope)

#: What one saved record (the spans, or the envelope) of one chosen slice can show. `named` is a
#: reading drawn; the rest are the silences, each with its own remedy: this run's writer saved
#: none for the slice; the saved code is a word the stage does not say; the stage had no
#: predecessor to read (its own reason is beside); the stage read and found nothing to name.
STANDINGS: tuple[str, ...] = (
    "named",
    "not_saved",
    "code_unknown",
    "predecessor_absent",
    "none_found",
)

#: Where the picture of one chosen slice gets its plane: an array the writer saved for that very
#: slice; the study stage's walk, when the slice is one it visits; the objects stage's selected
#: plane, when the slice is that one; or nowhere, which is a silence and never a blank plane.
PLANE_SOURCES: tuple[str, ...] = (
    "saved_for_slice",
    "study_walk",
    "selected_plane",
    "plane_not_saved",
)


def _whole(value: object) -> bool:
    """Whether the value is an int that is not a bool."""
    return isinstance(value, int) and not isinstance(value, bool)


def standing(code: object, vocabulary: tuple[str, ...], none_code: str) -> str:
    """Name what one saved record of one chosen slice can show, from its saved code.

    `code` is the record's saved code, or None when the writer saved no record for the slice;
    `vocabulary` the stage's codes for that record (`SPANS_RECORD_CODES` or `ENVELOPE_CODES`);
    `none_code` the word that vocabulary uses for "read, and nothing to name" (`no_candidate`,
    `no_fluid_like`). Total: no saved record is `not_saved`; a code that is not text, or that the
    vocabulary does not say, is `code_unknown`, named and never drawn; `predecessor_absent` is
    itself; the none word is `none_found`; any other word of the vocabulary is `named`. It selects
    nothing and counts nothing.

    post: __return__ in STANDINGS
    """
    if code is None:
        return "not_saved"
    if not isinstance(code, str) or code not in vocabulary:
        return "code_unknown"
    if code == "predecessor_absent":
        return "predecessor_absent"
    if code == none_code:
        return "none_found"
    return "named"


def plane_source(
    index: object,
    saved_for_slice: bool,
    walk_indices: tuple[object, ...],
    selected_index: object,
    selected_saved: bool,
) -> str:
    """Name where the picture of one chosen slice gets its plane.

    `index` is the chosen slice's stack index; `saved_for_slice` whether the writer saved a plane
    for that slice; `walk_indices` the slices the study stage's saved walk holds a plane for
    (empty when no walk was saved); `selected_index` the objects stage's selected slice, and
    `selected_saved` whether its plane was saved. Total: an index that is not a whole number has
    no plane; a plane saved for the slice itself comes first, then the walk, then the selected
    plane; otherwise `plane_not_saved`.

    post: __return__ in PLANE_SOURCES
    """
    if not _whole(index):
        return "plane_not_saved"
    if saved_for_slice:
        return "saved_for_slice"
    if any(_whole(walked) and walked == index for walked in walk_indices):
        return "study_walk"
    if selected_saved and _whole(selected_index) and selected_index == index:
        return "selected_plane"
    return "plane_not_saved"


@dataclass(frozen=True, slots=True)
class ChosenSlice:
    """One chosen slice of the picture under one border: its plane, and the stage's own records saved for it.

    index: the chosen slice's stack index as saved. plane: (rows, columns) in the dtype it was
    saved in, from `plane_source`, or None when `plane_source` is `plane_not_saved`.
    spans_standing, envelope_standing: from `STANDINGS`. spans, envelope: the stage's records as
    saved, or None where the writer saved none for this slice under this border. Nothing is
    derived. border: the word of `BORDER_CODES` both records were read under; the other border's
    reading of the same slice is another `ChosenSlice`, never this one's.
    """

    index: int
    plane: np.ndarray | None
    plane_source: str
    spans_standing: str
    spans: Spans | None
    envelope_standing: str
    envelope: Envelope | None
    border: str


@dataclass(frozen=True, slots=True)
class RoundThreePanels:
    """One series' saved round 3, AS THE WRITER SAVED IT, ready for the workbench to draw.

    bounds_rc: (tiles_down, tiles_across, 4) int64, the squint stack's saved half-open native
    bounds that place the tiles; None when none was handed on. slices: one `ChosenSlice` per
    distinct (border, chosen slice) the saved records name, grouped by slice in the order the
    records first name them (the spans', then any the envelope names alone), and under one slice
    the borders in the order of `BORDER_CODES`, so the two readings of a slice sit next to each
    other. An absent value stays absent, never a zero.
    """

    bounds_rc: np.ndarray | None
    slices: tuple[ChosenSlice, ...]


def _first_at(records: tuple[_Saved, ...], border: str, index: int) -> _Saved | None:
    """The first saved record that names this chosen slice under this border, or None."""
    for record in records:
        if record.border == border and record.slice_index == index:
            return record
    return None


def _border_rank(border: str) -> int:
    """Where a border word stands among `BORDER_CODES`; a word that is not one stands after them all."""
    return BORDER_CODES.index(border) if border in BORDER_CODES else len(BORDER_CODES)


def round_three_panels(
    spans: tuple[Spans, ...] | None,
    envelopes: tuple[Envelope, ...] | None,
    bounds_rc: np.ndarray | None,
    planes: Mapping[int, np.ndarray],
    walk_indices: tuple[object, ...],
    walk: np.ndarray | None,
    selected_index: object,
    selected_plane: np.ndarray | None,
) -> RoundThreePanels:
    """Hand on one series' saved spans and envelope per chosen slice, reading nothing of the study.

    Every argument is a value a stage computed and the writer saved: the stage's own `Spans` and
    `Envelope` records (None when the writer saved none; an empty tuple when it saved a record
    that names no slice), the squint stack's saved `bounds_rc`, the planes the writer saved for
    particular chosen slices (by stack index), the study stage's `walk_indices` with the `walk`
    of planes at them, and the objects stage's selected slice with its plane. The panels are the
    distinct (border, slice) pairs the two records name, each record keyed by its border AND its
    slice: the slices in the order the records first name them (the spans' first), and under one
    slice the borders in the order of `BORDER_CODES`, so the two readings of a slice sit side by
    side and neither shadows the other. For each, `plane_source` names where its plane comes
    from (a plane belongs to the slice, so both borders of a slice lie over the same one) and the
    plane is selected from that source; `standing` names what each record can show; the records
    themselves are handed on untouched. The bounds are handed on as int64; the planes keep their
    saved dtype. Nothing is measured, resampled or derived, and an absent value stays absent.
    """
    saved_spans = () if spans is None else tuple(spans)
    saved_envelopes = () if envelopes is None else tuple(envelopes)
    named: list[tuple[str, int]] = []
    for record in (*saved_spans, *saved_envelopes):
        key = (record.border, record.slice_index)
        if key not in named:
            named.append(key)
    first_named = list(dict.fromkeys(index for _, index in named))
    # A stable sort: a border word that is not one of `BORDER_CODES` keeps the order it was named in.
    order = sorted(
        named, key=lambda key: (first_named.index(key[1]), _border_rank(key[0]))
    )
    walked = tuple(walk_indices) if walk is not None else ()
    steps = {
        index: step
        for step, index in reversed(list(enumerate(walked)))
        if _whole(index)
    }
    chosen = []
    for border, index in order:
        source = plane_source(
            index,
            index in planes,
            walked,
            selected_index,
            selected_plane is not None,
        )
        if source == "saved_for_slice":
            plane = planes[index]
        elif source == "study_walk" and walk is not None:
            plane = np.asarray(walk[steps[index]])
        elif source == "selected_plane":
            plane = selected_plane
        else:
            plane = None
        found_spans = _first_at(saved_spans, border, index)
        found_envelope = _first_at(saved_envelopes, border, index)
        chosen.append(
            ChosenSlice(
                index=index,
                plane=plane,
                plane_source=source,
                spans_standing=standing(
                    None if found_spans is None else found_spans.code,
                    SPANS_RECORD_CODES,
                    "no_candidate",
                ),
                spans=found_spans,
                envelope_standing=standing(
                    None if found_envelope is None else found_envelope.code,
                    ENVELOPE_CODES,
                    "no_fluid_like",
                ),
                envelope=found_envelope,
                border=border,
            )
        )
    return RoundThreePanels(
        bounds_rc=None if bounds_rc is None else np.asarray(bounds_rc, dtype=np.int64),
        slices=tuple(chosen),
    )
