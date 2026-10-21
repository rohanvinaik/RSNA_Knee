"""Picture sheets of what raw squint recall compared, one sheet per question.

Development only. Production never imports this module, and its drawing layer
(matplotlib) is imported only inside ``draw_sheet``. It reads a finished run's
per-study records, the memory that run recalled from, and the native DICOM
slices of the query study and of every precedent it draws. Nothing here
locates, measures for recall, recalls or decides; it shows what was recorded.

For each tissue the question's contract makes defining (its necessary finding,
or its alternatives), a sheet shows, after the model of the thesis's figures
H2b and H2c (What an <Object> Is, sections 7.4-7.6):

* the places the query's profile was counted over, on their native slices. A
  territory-v2 profile carries its own territories (each tile's role: object,
  context, outside the leg), so those tiles are drawn, and drawn solid only for
  the roles whose banks a comparison read. A tile the support touches is not
  pure object: the share of its pixels the support covers is an occupancy, and
  an expected place (no measured support) has no share at all. The box around
  the object tiles is an address and is drawn dashed. Older (v1) records count
  a tile box, which is drawn as that and nothing more;
* the anatomical anchors and predicted points that proposed the reading, where
  the run kept them, and the teacher's native support where a precedent's
  territory came from one;
* the nearest precedent called normal for the question and the nearest called a
  presentation of it, each over its own places, with how it was taught;
* the banks each comparison read, bank by bank, as count tables, with a dashed
  frame for a bank a profile did not write (silent, never a middle);
* how far apart the query lies from each precedent in every compared bank, and
  the largest differences decoded into named readings from the exact counts.

THE PROFILE DRAWN IS THE ONE RECALL USED. Recall scores only the banks a
question selected, so each recorded term (dot, both squared norms, the banks
both profiles spoke in) is re-derived from the counts over its own recorded
banks, and the banks the selection offered that both profiles speak in must be
exactly the recorded ones. The candidates are the object's final profile and,
where a small part's own-outline reading replaced its reading, the expected-area
profile kept beside it; the final profile as it stood before its first 2 mm
reading (a territory-v2 record is read coarse first and may gain fine banks over
the same address for a later question, so an earlier one compared coarse banks
alone: those banks are what is drawn, the 2 mm banks stay unwritten and the 2 mm
readings leave the places drawn); and, for a v1 record only, the earlier form a
repeated 2 mm zoom leaves, an old repair a v2 record never gets. A profile that
reproduces no recorded term set is UNVERIFIED: nothing read from it is drawn as
compared, and no difference is decoded from it. The case side is checked the
same way, so a memory other than the one the run recalled from is named, per
precedent, and not drawn.

PINS. The memory must be the run's: the study record's revision and, where the
run's receipt is present, its manifest digest must equal the loaded memory's.
A teacher product is opened only after its bytes match the digest the memory
recorded; a re-resolved support is drawn only if its mask digest equals the
stored one; leg-map hatching and territory tiles are drawn only on the tile grid
and leg map the profile was written with. The selection each voice recorded is
compared with the current selection's digest, and a run source pin, where one is
supplied, with the digests of the code that draws.

A precedent called positive carries a study-level label: the study was called
positive for the condition. It does not place a lesion in that object or that
window, and every sheet says so.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter
from collections.abc import Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any, TypeGuard

import numpy as np

from knee.diagnosis.squint_interfaces import (
    LEG_MIXED,
    LEG_OUTSIDE,
    ROLE_CONTEXT,
    ROLE_NAMES,
    ROLE_OBJECT,
    ROLE_OUTSIDE_LEG,
    TERRITORY_PROCEDURE,
    parse_territory_bank_name,
)
from knee.diagnosis.squint_location_check import territory_runtime

SCHEMA = "knee.squint-visual-capacity/v1"
FINE_SCALE_MM = 2.0
CONTEXT_MARGIN_TILES = 3
_TITLE_BAND = 0.74
_GROUP_GAP = 0.3
_PANEL_MAX_IN = 3.3
_TITLE_CHARS_PER_IN = 19

# A v1 profile is coded against terciles over the whole series; a territory-v2
# profile against terciles over the series' inside-leg tiles only.
ROW_WORDS = (
    "below the series' middle third",
    "within the series' middle third",
    "above the series' middle third",
)
ROW_WORDS_LEG = (
    "below the leg's middle third",
    "within the leg's middle third",
    "above the leg's middle third",
)
METRIC_ORDER = (
    "signal_median",
    "signal_minimum",
    "signal_maximum",
    "local_range",
    "gradient_row",
    "gradient_column",
)
METRIC_WORDS = {
    "signal_median": "median signal",
    "signal_minimum": "darkest signal",
    "signal_maximum": "brightest signal",
    "local_range": "signal range",
    "gradient_row": "signal change down the rows",
    "gradient_column": "signal change along the columns",
}
METRIC_SHORT = {
    "signal_median": "median",
    "signal_minimum": "darkest",
    "signal_maximum": "brightest",
    "local_range": "range",
    "gradient_row": "change, rows",
    "gradient_column": "change, columns",
}
# A signal metric's whole-window bank is "overview"; a gradient metric's is
# named by its own axis. Each metric has exactly one, so they share a column.
_ALL_PLACES = ("overview", "row", "column")
DIRECTION_ORDER = (
    "all",
    "patient_lps_left",
    "patient_lps_right",
    "patient_lps_anterior",
    "patient_lps_posterior",
    "patient_lps_superior",
    "patient_lps_inferior",
    "stack_depth_first",
    "stack_depth_middle",
    "stack_depth_last",
)
DIRECTION_WORDS = {
    "all": "all its places",
    "patient_lps_left": "its patient-left half",
    "patient_lps_right": "its patient-right half",
    "patient_lps_anterior": "its anterior half",
    "patient_lps_posterior": "its posterior half",
    "patient_lps_superior": "its superior half",
    "patient_lps_inferior": "its inferior half",
    "stack_depth_first": "its first third of slices",
    "stack_depth_middle": "its middle third of slices",
    "stack_depth_last": "its last third of slices",
}
DIRECTION_SHORT = {
    "all": "all",
    "patient_lps_left": "L",
    "patient_lps_right": "R",
    "patient_lps_anterior": "A",
    "patient_lps_posterior": "P",
    "patient_lps_superior": "S",
    "patient_lps_inferior": "I",
    "stack_depth_first": "z1",
    "stack_depth_middle": "z2",
    "stack_depth_last": "z3",
}

# Colours after H2b/H2c: blue below the middle, grey at it, red above it.
BELOW = "#2a6fdb"
MIDDLE = "#8d939c"
ABOVE = "#e2483d"
OBJECT = "#ff2fd0"
CONTEXT = "#1fd1f0"
ADDRESS = "#ffd400"
ANCHOR = "#ff9f1a"
PREDICTED = "#ffffff"
SILENT = "#9aa0a6"
INK = "#2b2f36"
SOFT_INK = "#5d6470"

_V1_BANK = re.compile(
    r"^squint/v1/view=(\[[^\]]*\])/metric=([^/]+)/direction=([^/]+)/scale=([^/]+)mm$"
)


# --------------------------------------------------------------------------
# Names of banks and readings, in plain words


def parse_bank(name: object) -> dict[str, Any] | None:
    """Split a v1 squint bank name, or a v2 territory bank name, into fields."""
    if not isinstance(name, str):
        return None
    match = _V1_BANK.match(name)
    if match is not None:
        try:
            view = json.loads(match.group(1))
            scale = float(match.group(4))
        except (json.JSONDecodeError, ValueError):
            return None
        if (
            not isinstance(view, list)
            or len(view) != 3
            or not all(isinstance(value, str) for value in view)
            or not math.isfinite(scale)
            or scale <= 0
        ):
            return None
        return {
            "version": "v1",
            "view": tuple(view),
            "role": None,
            "metric": match.group(2),
            "direction": match.group(3),
            "scale_mm": scale,
        }
    fields = parse_territory_bank_name(name)
    if fields is None:
        return None
    return {
        "version": "v2",
        "view": tuple(fields["view"]),
        "role": fields["role"],
        "metric": fields["metric"],
        "direction": fields["direction"],
        "scale_mm": fields["scale_mm"],
    }


def direction_column(direction: str) -> str:
    """The grid column of a bank direction: whole-window banks share ``all``."""
    return "all" if direction in _ALL_PLACES else direction


def view_words(view: Sequence[str]) -> str:
    """Name a series view by its plane and its two acquisition flags."""
    if not isinstance(view, (list, tuple)) or len(view) != 3:
        return "unknown view"
    orientation, fluid, fat = (str(value) for value in view)
    fluid_words = {"1": "fluid-sensitive", "0": "not fluid-sensitive"}.get(
        fluid, f"fluid-sensitive={fluid}"
    )
    fat_words = {"1": "fat-suppressed", "0": "fat not suppressed"}.get(
        fat, f"fat-suppressed={fat}"
    )
    return f"{orientation}, {fluid_words}, {fat_words}"


def view_short(view: Sequence[str]) -> str:
    """A short view label: plane, then FS when fat is suppressed."""
    if not isinstance(view, (list, tuple)) or len(view) != 3:
        return "unknown view"
    orientation, fluid, fat = (str(value) for value in view)
    flags = []
    if fluid == "1":
        flags.append("fluid")
    if fat == "1":
        flags.append("FS")
    return orientation + (" " + " ".join(flags) if flags else " non-FS")


def view_key(view: object) -> tuple[str, str, str] | None:
    """A series view mapping as the (plane, fluid, fat) tuple a bank name carries."""
    if not isinstance(view, Mapping):
        return None
    return (
        str(view.get("orientation", "?")),
        str(view.get("fluid_sensitive", "?")),
        str(view.get("fat_suppression", "?")),
    )


def bank_words(name: str) -> str:
    """One bank in plain words, or its raw name when it does not parse."""
    fields = parse_bank(name)
    if fields is None:
        return name
    column = direction_column(fields["direction"])
    scale = fields["scale_mm"]
    scale_words = f"{scale:g} mm tiles"
    if scale < 10.0:
        scale_words += " (coded with the 10 mm thirds)"
    parts = [
        view_words(fields["view"]),
        METRIC_WORDS.get(fields["metric"], fields["metric"]),
        DIRECTION_WORDS.get(column, fields["direction"]),
        scale_words,
    ]
    if fields["role"] is not None:
        parts.append(f"{fields['role']} places")
    return " / ".join(parts)


def row_words(name: str) -> tuple[str, str, str]:
    """The words for a bank's three rows: its profile's coding reference differs."""
    fields = parse_bank(name)
    return ROW_WORDS_LEG if fields and fields["version"] == "v2" else ROW_WORDS


# --------------------------------------------------------------------------
# The exact decode of a difference


def _counts(value: object) -> tuple[int, int, int] | None:
    if (
        isinstance(value, (list, tuple))
        and len(value) == 3
        and all(type(item) is int and item >= 0 for item in value)
    ):
        return (int(value[0]), int(value[1]), int(value[2]))
    return None


def bank_difference(left: object, right: object) -> dict[str, Any] | None:
    """Exact row shares of one bank in two profiles; None where either is silent.

    ``apart`` is the bank's most different reading: the largest absolute
    difference between the two profiles' shares of its three rows.
    """
    a, b = _counts(left), _counts(right)
    if a is None or b is None or not any(a) or not any(b):
        return None
    left_total, right_total = sum(a), sum(b)
    differences = [
        Fraction(x, left_total) - Fraction(y, right_total)
        for x, y in zip(a, b, strict=True)
    ]
    magnitudes = [abs(value) for value in differences]
    apart = max(magnitudes)
    row = magnitudes.index(apart)
    return {
        "left": list(a),
        "right": list(b),
        "left_total": left_total,
        "right_total": right_total,
        "share_difference": differences,
        "apart": apart,
        "row": row,
    }


def named_differences(
    left_banks: Mapping[str, Sequence[int]],
    right_banks: Mapping[str, Sequence[int]],
    compared: Sequence[str],
    *,
    left_label: str,
    right_label: str,
    limit: int,
) -> list[dict[str, Any]]:
    """Decode the largest per-bank differences over the banks a comparison read.

    Ordered by the most different reading, then by bank name, so equal
    differences keep one fixed order. Each item states the exact counts.
    """
    rows = []
    for name in compared:
        difference = bank_difference(left_banks.get(name), right_banks.get(name))
        if difference is None:
            continue
        rows.append((name, difference))
    rows.sort(key=lambda item: (-item[1]["apart"], item[0]))
    result = []
    for name, difference in rows[: max(0, limit)]:
        row = difference["row"]
        words = row_words(name)[row]
        left_count = difference["left"][row]
        right_count = difference["right"][row]
        left_share = Fraction(left_count, difference["left_total"])
        right_share = Fraction(right_count, difference["right_total"])
        statement = (
            f"{bank_words(name)}: {left_label} {left_count} of "
            f"{difference['left_total']} places {words} "
            f"({float(left_share):.0%}); {right_label} {right_count} of "
            f"{difference['right_total']} ({float(right_share):.0%})"
        )
        result.append(
            {
                "bank": name,
                "row": row,
                "row_words": words,
                "left_counts": difference["left"],
                "right_counts": difference["right"],
                "apart": [
                    difference["apart"].numerator,
                    difference["apart"].denominator,
                ],
                "statement": statement,
            }
        )
    return result


# --------------------------------------------------------------------------
# The query profile recall used for one question


def profile_without_scale(profile: Mapping[str, Any], scale_mm: float) -> dict:
    """The same profile with every bank at ``scale_mm`` removed."""
    banks = {
        name: list(counts)
        for name, counts in profile.get("banks", {}).items()
        if (parse_bank(name) or {}).get("scale_mm") != scale_mm
    }
    return {**profile, "banks": banks}


def profile_with_scale_halved(
    profile: Mapping[str, Any], scale_mm: float
) -> dict | None:
    """The profile with ``scale_mm`` counts halved; None if any count is odd."""
    banks: dict[str, list[int]] = {}
    for name, counts in profile.get("banks", {}).items():
        values = list(counts)
        if (parse_bank(name) or {}).get("scale_mm") == scale_mm:
            if any(value % 2 for value in values):
                return None
            values = [value // 2 for value in values]
        banks[name] = values
    return {**profile, "banks": banks}


def _without_fine_readings(source: object) -> object:
    """The source with every fine (refinement) reading left out of its lineage."""
    if not isinstance(source, Mapping) or not isinstance(source.get("lineage"), list):
        return source
    return {
        **source,
        "lineage": [
            _without_fine_readings(reading)
            for reading in source["lineage"]
            if not (isinstance(reading, Mapping) and reading.get("refinement") is True)
        ],
    }


def profile_before_fine_reading(
    profile: Mapping[str, Any], scale_mm: float
) -> dict | None:
    """A territory-v2 profile as it stood before its first fine reading.

    Its ``scale_mm`` banks are left unwritten (``profile_without_scale``: absent,
    never zero) and its fine readings leave the source lineage, so the places read
    from it are the coarse ones the remaining banks were counted over, never a
    finer region added after. None when the profile holds no fine bank and no fine
    reading to leave out: it would be the profile itself.
    """
    coarse = profile_without_scale(profile, scale_mm)
    source = _without_fine_readings(profile.get("source"))
    nothing_left_out = len(coarse["banks"]) == len(profile.get("banks", {}))
    if nothing_left_out and source == profile.get("source"):
        return None
    return {**coarse, "source": source}


#: Codes under which a profile has been shown to be the one a recall compared.
VERIFIED_QUERY_CODES = (
    "final",
    "expected_area_profile",
    "before_first_fine_reading",
    "before_repeated_fine_reading",
)


def _speaks(banks: Mapping[str, Any], name: str) -> bool:
    counts = _counts(banks.get(name))
    return counts is not None and any(counts)


def term_reproduction(
    query_banks: Mapping[str, Any],
    case_banks: Mapping[str, Any],
    term: Mapping[str, Any],
    selected: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Re-derive one recorded recall term from the two profiles' own counts.

    A term is the dot product and both squared norms over the banks both
    profiles speak in, and only the banks the question selected when it
    selected any (``selected``: the names the voice recorded). The sums are
    taken over the term's recorded banks; the banks the selection offered that
    both profiles speak in must be exactly those banks. The bank list, the
    case side (the memory), the query side (the profile) and the dot are
    checked apart so that a different memory and a different query are named
    as what they are. Silence is not a count: an unwritten bank adds nothing.
    """
    recorded = term.get("terms")
    banks = term.get("common_speaking_banks")
    if (
        not isinstance(recorded, Mapping)
        or not isinstance(banks, list)
        or any(not isinstance(name, str) for name in banks)
        or any(
            type(recorded.get(key)) is not int
            for key in ("dot", "left_norm_sq", "right_norm_sq")
        )
    ):
        return {
            "code": "term_malformed",
            "banks": False,
            "query": False,
            "case": False,
            "dot": False,
        }
    pool = set(selected) if selected is not None else set(query_banks) | set(case_banks)
    offered = sorted(
        name
        for name in pool
        if _speaks(query_banks, name) and _speaks(case_banks, name)
    )
    dot = query_sq = case_sq = 0
    for name in banks:
        left, right = _counts(query_banks.get(name)), _counts(case_banks.get(name))
        # Each side's norm comes from that side alone. A query that is not known
        # (an unverified one has no banks here) or that lacks a recorded bank must
        # not make the memory look different, nor the reverse.
        if left is not None:
            query_sq += sum(a * a for a in left)
        if right is not None:
            case_sq += sum(b * b for b in right)
        if left is not None and right is not None:
            dot += sum(a * b for a, b in zip(left, right, strict=True))
    flags = {
        "banks": sorted(banks) == offered,
        "case": case_sq == recorded["right_norm_sq"],
        "query": query_sq == recorded["left_norm_sq"],
        "dot": dot == recorded["dot"],
    }
    named = {
        "banks": "banks_differ",
        "case": "case_counts_differ",
        "query": "query_counts_differ",
        "dot": "dot_differs",
    }
    code = next((named[key] for key, ok in flags.items() if not ok), "reproduced")
    return {"code": code, **flags}


def _check_terms(
    profile: Mapping[str, Any],
    terms: Sequence[Mapping[str, Any]],
    case_profiles: Mapping[str, Mapping[str, Any] | None],
    selected: Sequence[str] | None,
) -> list[dict[str, Any]]:
    banks = profile.get("banks", {})
    rows = []
    for term in terms:
        case_id = term.get("case_id")
        case = case_profiles.get(case_id)
        case_banks = case.get("banks") if isinstance(case, Mapping) else None
        if not isinstance(case_banks, Mapping):
            rows.append(
                {
                    "case_id": case_id,
                    "code": "case_not_in_memory",
                    "banks": False,
                    "query": False,
                    "case": False,
                    "dot": False,
                }
            )
            continue
        rows.append(
            {"case_id": case_id, **term_reproduction(banks, case_banks, term, selected)}
        )
    return rows


def recalled_query_profile(
    final_profile: Mapping[str, Any] | None,
    terms: Sequence[Mapping[str, Any]],
    case_profiles: Mapping[str, Mapping[str, Any] | None],
    *,
    expected_area_profile: Mapping[str, Any] | None = None,
    selected_banks: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Find the query profile that reproduces every recorded term exactly.

    Candidates, in order: the final profile; the expected-area profile a small
    part's own-outline reading replaced (the run keeps it beside the final
    one); the final profile without its 2 mm banks (recalled before a first
    2 mm reading); and, for a v1 record only, the final profile with its 2 mm
    counts halved (recalled before the same windows were read at 2 mm a second
    time). A territory-v2 record is read coarse first and may gain fine banks
    over the same address for a later question, so an earlier question can have
    compared coarse banks alone: its projection also leaves the fine readings
    out of the source, and is offered only where there is a fine bank or reading
    to leave out. The halved counts were only ever an old v1 repair. The first
    to reproduce every term names the profile; any other that also does is
    listed, never hidden. A profile that reproduces none leaves the query
    UNVERIFIED, with the code of each term and the precedents whose memory
    counts differ from the record.
    """
    if not isinstance(final_profile, Mapping) or not isinstance(
        final_profile.get("banks"), Mapping
    ):
        return {
            "code": "query_profile_missing",
            "profile": None,
            "checked_terms": 0,
            "term_codes": {},
            "memory_case_differs": [],
            "also_reproduced_by": [],
        }
    if not terms:
        return {
            "code": "no_recorded_terms",
            "profile": dict(final_profile),
            "checked_terms": 0,
            "term_codes": {},
            "memory_case_differs": [],
            "also_reproduced_by": [],
        }
    candidates: list[tuple[str, dict | None]] = [("final", dict(final_profile))]
    if isinstance(expected_area_profile, Mapping) and isinstance(
        expected_area_profile.get("banks"), Mapping
    ):
        candidates.append(("expected_area_profile", dict(expected_area_profile)))
    source = final_profile.get("source")
    if isinstance(source, Mapping) and source.get("procedure") == TERRITORY_PROCEDURE:
        candidates.append(
            (
                "before_first_fine_reading",
                profile_before_fine_reading(final_profile, FINE_SCALE_MM),
            )
        )
    else:
        candidates += [
            (
                "before_first_fine_reading",
                profile_without_scale(final_profile, FINE_SCALE_MM),
            ),
            (
                "before_repeated_fine_reading",
                profile_with_scale_halved(final_profile, FINE_SCALE_MM),
            ),
        ]
    reproducing = []
    first_checks = None
    for code, profile in candidates:
        if profile is None:
            continue
        checks = _check_terms(profile, terms, case_profiles, selected_banks)
        first_checks = first_checks or checks
        if all(row["code"] == "reproduced" for row in checks):
            reproducing.append((code, profile, checks))
    checks = reproducing[0][2] if reproducing else first_checks or []
    result = {
        "checked_terms": len(terms),
        "term_codes": dict(Counter(row["code"] for row in checks)),
        "memory_case_differs": [row["case_id"] for row in checks if not row["case"]],
        "also_reproduced_by": [code for code, _, _ in reproducing[1:]],
    }
    if reproducing:
        return {"code": reproducing[0][0], "profile": reproducing[0][1], **result}
    return {
        "code": "recalled_profile_not_reconstructed",
        "profile": dict(final_profile),
        **result,
    }


# --------------------------------------------------------------------------
# Regions, windows and territories


def region_window(region: Mapping[str, Any]) -> tuple[int, ...] | None:
    """The tile window of a region: ``window``, else ``source_window``."""
    window = region.get("window", region.get("source_window"))
    if (
        isinstance(window, (list, tuple))
        and len(window) == 6
        and all(type(value) is int for value in window)
    ):
        z0, z1, r0, r1, c0, c1 = window
        if 0 <= z0 < z1 and 0 <= r0 < r1 and 0 <= c0 < c1:
            return tuple(window)
    return None


def window_native_bounds(
    bounds_rc: np.ndarray, window: Sequence[int]
) -> tuple[int, int, int, int]:
    """Native half-open pixel bounds of a tile window: the union of its tiles."""
    _, _, r0, r1, c0, c1 = window
    tiles = np.asarray(bounds_rc)[r0:r1, c0:c1]
    if tiles.ndim != 3 or tiles.shape[-1] != 4 or not tiles.size:
        raise ValueError("window_outside_tile_grid")
    return (
        int(tiles[..., 0].min()),
        int(tiles[..., 1].max()),
        int(tiles[..., 2].min()),
        int(tiles[..., 3].max()),
    )


def crop_bounds(
    native: Sequence[int],
    tile_px: Sequence[int],
    shape: Sequence[int],
    margin_tiles: int = CONTEXT_MARGIN_TILES,
) -> tuple[int, int, int, int]:
    """A view around a window: ``margin_tiles`` tiles each side, inside the slice."""
    r0, r1, c0, c1 = native
    rows, cols = int(shape[0]), int(shape[1])
    dr, dc = int(tile_px[0]) * margin_tiles, int(tile_px[1]) * margin_tiles
    return (max(0, r0 - dr), min(rows, r1 + dr), max(0, c0 - dc), min(cols, c1 + dc))


def territory_summary(territory: Mapping[str, Any]) -> dict[str, Any]:
    """Count a territory's roles and its support's share of the window it names.

    The window here is the territory's own tile window; ``object_share`` is the
    measured share of each tile's native pixels the support covers. It is an
    occupancy, never a purity: a tile with any support is an object tile, and
    an expected place (no measured support) has no share at all.
    """
    roles = np.asarray(territory.get("roles"))
    share = np.asarray(territory.get("object_share"), dtype=np.float64)
    support = territory.get("native_support") or {}
    mask = support.get("mask")
    support_px = int(np.count_nonzero(mask)) if isinstance(mask, np.ndarray) else None
    shares = [
        round(float(value), 4)
        for value in share[roles == ROLE_OBJECT].reshape(-1)
        if np.isfinite(value)
    ]
    return {
        "origin": territory.get("origin"),
        "object_tiles": int(np.count_nonzero(roles == ROLE_OBJECT)),
        "context_tiles": int(np.count_nonzero(roles == ROLE_CONTEXT)),
        "outside_leg_tiles": int(np.count_nonzero(roles == ROLE_OUTSIDE_LEG)),
        "tiles": int(roles.size),
        "slices": int(roles.shape[0]) if roles.ndim == 3 else None,
        "support_px": support_px,
        "object_tile_shares": shares,
        "share_status": "measured_occupancy" if shares else "not_measured",
    }


def object_box(
    roles: np.ndarray, tile_window: Sequence[int]
) -> tuple[int, int, int, int, int, int] | None:
    """The half-open tile box around a territory's object places: an address only."""
    places = np.argwhere(np.asarray(roles) == ROLE_OBJECT)
    if not len(places):
        return None
    z0, _, r0, _, c0, _ = (int(value) for value in tile_window)
    low, high = places.min(axis=0), places.max(axis=0) + 1
    return (
        z0 + int(low[0]),
        z0 + int(high[0]),
        r0 + int(low[1]),
        r0 + int(high[1]),
        c0 + int(low[2]),
        c0 + int(high[2]),
    )


def compared_roles(
    banks: Sequence[str], view: Sequence[str] | None = None
) -> list[str]:
    """The territory roles whose banks a comparison read, from the bank names.

    With ``view`` (plane and the two acquisition flags, as a bank name carries
    them) only the banks of that view count: a place in a view no comparison
    read a bank of was not compared, whatever its role.
    """
    roles = set()
    for name in banks:
        fields = parse_bank(name)
        if fields is None or fields["role"] is None:
            continue
        if view is not None and fields["view"] != tuple(view):
            continue
        roles.add(fields["role"])
    return sorted(roles)


def profile_territories(profile: object) -> list[dict[str, Any]]:
    """The territories a profile was counted over, from its own source lineage.

    A territory-v2 reading keeps the territory it was written over (the roles
    of every tile, the measured shares and the support's digest) in its source,
    and a merge keeps each reading's source beneath it. Each distinct territory
    is listed once, with the view it was read in, the native bounds its coarse
    reading recorded for that window, the digest of the leg map it was written
    with, and how many paired 2 mm readings it carries. A v1 profile counted a
    tile box and has none.
    """
    found: dict[tuple, dict[str, Any]] = {}
    stack = [profile.get("source") if isinstance(profile, Mapping) else None]
    while stack:
        source = stack.pop()
        if not isinstance(source, Mapping):
            continue
        lineage = source.get("lineage")
        if isinstance(lineage, list):
            stack.extend(lineage)
        territory = source.get("territory")
        if not isinstance(territory, Mapping):
            continue
        window = territory.get("tile_window")
        key = (
            territory.get("series_uid"),
            json.dumps(window),
            json.dumps(territory.get("roles")),
        )
        window_list = list(window) if isinstance(window, (list, tuple)) else None
        entry = found.setdefault(
            key,
            {
                "territory": territory,
                "view": None,
                "recorded_native_bounds_rc": None,
                "leg_map_sha256": None,
                "fine_readings": 0,
            },
        )
        if isinstance(source.get("view"), Mapping) and entry["view"] is None:
            entry["view"] = dict(source["view"])
        leg = source.get("leg_map")
        if isinstance(leg, Mapping) and isinstance(leg.get("codes_sha256"), str):
            entry["leg_map_sha256"] = leg["codes_sha256"]
        if source.get("refinement") is True:
            entry["fine_readings"] += 1
        elif (
            window_list is not None
            and list(source.get("window") or ()) == window_list
            and isinstance(source.get("native_bounds_rc"), (list, tuple))
        ):
            entry["recorded_native_bounds_rc"] = list(source["native_bounds_rc"])
    return sorted(
        found.values(),
        key=lambda entry: (
            str(entry["territory"].get("series_uid")),
            list(entry["territory"].get("tile_window") or ()),
        ),
    )


def support_digest(territory: Mapping[str, Any]) -> str | None:
    """The mask digest a territory record kept for its native support, if any."""
    for key in ("native_support_address", "native_support"):
        address = territory.get(key)
        if isinstance(address, Mapping) and isinstance(address.get("mask_sha256"), str):
            return address["mask_sha256"]
    return None


def territory_anchors(territory: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The anchor and expected points a relation territory kept for its placement.

    Where the knee's side was unknown the territory keeps both mirrored
    hypotheses; each is returned and named, so a disagreement is drawn twice.
    """
    anchors: list[dict[str, Any]] = []
    for row in territory.get("anchors") or ():
        if not isinstance(row, Mapping):
            continue
        name = str(row.get("anchor", "unknown anchor"))
        side = row.get("knee_side_hypothesis")
        if _finite_point(row.get("anchor_point_lps")):
            anchors.append(
                {
                    "kind": "anchor_point",
                    "label": f"{name} ({row.get('kind', 'unknown')})",
                    "point_lps": [float(v) for v in row["anchor_point_lps"]],
                }
            )
        if _finite_point(row.get("expected_point_lps")):
            anchors.append(
                {
                    "kind": "predicted_point",
                    "label": f"predicted from {name}"
                    + (f" (side hypothesis {side})" if side else ""),
                    "point_lps": [float(v) for v in row["expected_point_lps"]],
                }
            )
    return anchors


def support_in_window(
    mask: np.ndarray, offset_rc: Sequence[int], native: Sequence[int]
) -> int:
    """Support pixels that fall inside a native window (half-open)."""
    r0, r1, c0, c1 = native
    mask = np.asarray(mask, dtype=bool)
    if mask.ndim == 3:
        mask = mask.any(axis=0)
    rows, cols = np.nonzero(mask)
    rows = rows + int(offset_rc[0])
    cols = cols + int(offset_rc[1])
    return int(
        np.count_nonzero((rows >= r0) & (rows < r1) & (cols >= c0) & (cols < c1))
    )


def inset_corner(
    centre_x: float, centre_y_from_top: float, size: float = 0.3
) -> list[float]:
    """Axes bounds of an inset in the corner farthest from a point.

    The point is given as fractions of the panel, x from the left and y from the
    top; the bounds are matplotlib axes fractions, y from the bottom.
    """
    point = (centre_x, 1.0 - centre_y_from_top)
    corners = [
        (1.0 - size - 0.01, 1.0 - size - 0.01),
        (0.01, 1.0 - size - 0.01),
        (1.0 - size - 0.01, 0.01),
        (0.01, 0.01),
    ]

    def distance(corner: tuple[float, float]) -> float:
        return math.hypot(
            corner[0] + size / 2 - point[0], corner[1] + size / 2 - point[1]
        )

    best = max(corners, key=distance)
    return [best[0], best[1], size, size]


def window_anchors(
    object_record: Mapping[str, Any], region: Mapping[str, Any]
) -> list[dict[str, Any]]:
    """The anchors and predicted points that proposed one located window.

    A region with its own reference point (a teacher's region) gives that point.
    A bone located by its structural anchor gives the anchor's reference, built
    from its key planes (never one section's centre). A region carrying its
    territory gives the anchors that territory kept; otherwise they are read
    from the object's retained location evidence: the window source whose
    window equals this region's, each source's hypothesis and its anchor.
    """
    anchors: list[dict[str, Any]] = []
    point = region.get("source_point_lps")
    if _finite_point(point):
        anchors.append(
            {
                "kind": "object_reference_point",
                "label": "its own reference point",
                "point_lps": [float(value) for value in point],
            }
        )
    window = region_window(region)
    evidence = object_record.get("evidence")
    anchor = evidence.get("anchor") if isinstance(evidence, Mapping) else None
    if isinstance(anchor, Mapping) and _finite_point(anchor.get("reference_lps")):
        anchors.append(
            {
                "kind": "anchor_point",
                "label": f"structural anchor reference ({anchor.get('status')})",
                "point_lps": [float(value) for value in anchor["reference_lps"]],
            }
        )
    territory = region.get("territory")
    if isinstance(territory, Mapping) and territory.get("anchors"):
        return anchors + territory_anchors(territory)
    if window is None or not isinstance(evidence, Mapping):
        return anchors
    seen: set[tuple[str, tuple[float, ...]]] = set()
    for proposal in evidence.get("proposal_sources", ()) or ():
        if not isinstance(proposal, Mapping):
            continue
        if proposal.get("series_uid") != region.get("series_uid"):
            continue
        provenance = proposal.get("provenance")
        if not isinstance(provenance, Mapping):
            continue
        hypotheses = provenance.get("hypotheses") or []
        for row in provenance.get("window_sources", ()) or ():
            if not isinstance(row, Mapping) or list(row.get("window", ())) != list(
                window
            ):
                continue
            for source in row.get("sources", ()) or ():
                index = (
                    source.get("hypothesis_index")
                    if isinstance(source, Mapping)
                    else None
                )
                hypothesis = (
                    hypotheses[index]
                    if type(index) is int and 0 <= index < len(hypotheses)
                    else {}
                )
                name = str(hypothesis.get("anchor", "unknown anchor"))
                kind = str(hypothesis.get("kind", "unknown"))
                anchor_point = hypothesis.get("anchor_point_lps")
                if _finite_point(anchor_point):
                    key = (
                        "anchor:" + name,
                        tuple(round(float(v), 3) for v in anchor_point),
                    )
                    if key not in seen:
                        seen.add(key)
                        anchors.append(
                            {
                                "kind": "anchor_point",
                                "label": f"{name} ({kind})",
                                "point_lps": [float(v) for v in anchor_point],
                            }
                        )
                predicted = source.get("predicted_point_lps")
                if _finite_point(predicted):
                    key = (
                        "predicted:" + name,
                        tuple(round(float(v), 3) for v in predicted),
                    )
                    if key not in seen:
                        seen.add(key)
                        anchors.append(
                            {
                                "kind": "predicted_point",
                                "label": f"predicted from {name}",
                                "point_lps": [float(v) for v in predicted],
                            }
                        )
    return anchors


def _finite_point(value: object) -> TypeGuard[Sequence[float]]:
    return (
        isinstance(value, (list, tuple))
        and len(value) == 3
        and all(
            isinstance(item, (int, float)) and math.isfinite(item) for item in value
        )
    )


# --------------------------------------------------------------------------
# One question's plan, from the record and the memory alone


def _short(uid: object) -> str:
    return "…" + str(uid)[-6:] if isinstance(uid, str) and uid else "none"


def _case_short(case_id: object) -> str:
    """A case named by its study: ``squint-case:<uid>:<subject>`` -> ``…<uid tail>``."""
    if not isinstance(case_id, str) or not case_id:
        return "none"
    parts = case_id.split(":")
    return "study " + _short(parts[1]) if len(parts) >= 3 else _short(case_id)


def _image_groups(
    plan: Mapping[str, Any], subject: Mapping[str, Any], fig_w: float, margin: float
) -> tuple[list[tuple], list[int], float]:
    """The query's and two precedents' panel groups, their slots and panel width."""
    groups: list[tuple] = [
        ("query", subject["panels"], plan["study_uid"], subject["subject"])
    ]
    for key in ("normal", "presentation"):
        precedent = subject.get(key)
        if isinstance(precedent, Mapping) and precedent.get("code") == "drawn":
            groups.append(
                (
                    key,
                    precedent["panels"],
                    precedent["study_uid"],
                    precedent["subject"],
                )
            )
        else:
            groups.append((key, [], None, None))
    slots = [max(1, len(panels)) for _, panels, _, _ in groups]
    width = fig_w - 2 * margin - _GROUP_GAP * (len(groups) - 1)
    return groups, slots, min(_PANEL_MAX_IN, width / sum(slots))


def _fraction(value: object) -> tuple[int, int] | None:
    if isinstance(value, Mapping):
        try:
            numerator = int(value["numerator"])
            denominator = int(value["denominator"])
        except (KeyError, TypeError, ValueError):
            return None
        if denominator > 0 and numerator >= 0:
            return (numerator, denominator)
    return None


def _full_profile_summary(memory: Mapping[str, Any], case: Mapping[str, Any]) -> dict:
    full = case.get("full_profile")
    if not isinstance(full, Mapping):
        return {"availability": "no_full_profile_reference"}
    summary: dict[str, Any] = {"availability": full.get("availability")}
    payloads = (memory.get("full_profile_payloads") or {}).get("payloads") or {}
    payload = (
        payloads.get(full.get("payload_ref")) if isinstance(payloads, Mapping) else None
    )
    record = payload.get("record") if isinstance(payload, Mapping) else None
    if isinstance(record, Mapping):
        rows = record.get("sparse_counts") or []
        written = sorted(
            {
                row[0]
                for row in rows
                if isinstance(row, list) and row and isinstance(row[0], str)
            }
        )
        kinds: dict[str, int] = {}
        for name in written:
            kind = facet_kind(name)
            kinds[kind] = kinds.get(kind, 0) + 1
        summary.update(
            {
                "status": record.get("status"),
                "written_banks": len(written),
                "sparse_rows": len(rows),
                "written_by_facet_kind": kinds,
            }
        )
    contexts = (memory.get("full_profile_contexts") or {}).get("contexts") or {}
    context = (
        contexts.get(full.get("context_ref")) if isinstance(contexts, Mapping) else None
    )
    composition = (
        context.get("object_composition") if isinstance(context, Mapping) else None
    )
    layout = composition.get("layout") if isinstance(composition, Mapping) else None
    banks = layout.get("banks") if isinstance(layout, Mapping) else None
    if isinstance(banks, list):
        summary["layout_banks"] = len(banks)
    return summary


def facet_kind(name: object) -> str:
    """The facet kind of a full-profile bank name ``facet:[kind, ...]``."""
    if isinstance(name, str) and name.startswith("facet:"):
        try:
            fields = json.loads(name[len("facet:") :])
        except json.JSONDecodeError:
            return "unparsed"
        if isinstance(fields, list) and fields and isinstance(fields[0], str):
            return fields[0]
    return "unparsed"


def region_panels(
    regions: Sequence[Mapping[str, Any]], counted_by: str
) -> list[dict[str, Any]]:
    """Each located region as a panel that names only its address.

    ``counted_by`` says what the address stands for: ``tile_box`` (a v1 profile
    counted every tile of the box) or ``located_address_only`` (the profile
    counted over these places is not known, so nothing is claimed about them).
    """
    return [
        {
            "counted_by": counted_by,
            "series_uid": region.get("series_uid"),
            "view": region.get("view"),
            "window": region_window(region),
            "region": region,
            "territory": None,
            "territory_code": None,
            "origin": None,
            "anchors": list(region.get("anchors") or ()),
            "recorded_native_bounds_rc": None,
            "leg_map_sha256": None,
            "support_digest": None,
            "subject": None,
            "fine_readings": 0,
        }
        for region in regions
    ]


def reading_panels(
    profile: object, regions: Sequence[Mapping[str, Any]]
) -> list[dict[str, Any]]:
    """What a profile's banks were counted over, panel by panel.

    A territory-v2 profile names its territories in its own source, so those
    are the panels, each with the role of every tile; the regions the run
    located are matched to them by series and slice for the location evidence
    they carry, and a located region no territory was read over is not a panel
    (it was not compared). A profile with no territory (v1) counted the tile
    box of each located region, and each region is a panel.
    """
    entries = profile_territories(profile)
    if not entries:
        return region_panels(regions, "tile_box")
    panels = []
    for entry in entries:
        record = entry["territory"]
        runtime, code = territory_runtime(record)
        box = (
            object_box(runtime["roles"], runtime["tile_window"])
            if runtime is not None
            else None
        )
        window = box if box is not None else region_window(record)
        same_series = [
            region
            for region in regions
            if region.get("series_uid") == record.get("series_uid")
            and window is not None
            and (region_window(region) or (None,))[0] == window[0]
        ]
        region = next(
            (r for r in same_series if region_window(r) == window),
            same_series[0] if same_series else None,
        )
        panels.append(
            {
                "counted_by": "territory",
                "series_uid": record.get("series_uid"),
                "view": entry["view"] or (region or {}).get("view"),
                "window": window,
                "region": region,
                "territory": runtime,
                "territory_code": code,
                "origin": record.get("origin"),
                "anchors": list((region or {}).get("anchors") or ())
                or territory_anchors(record),
                "recorded_native_bounds_rc": entry["recorded_native_bounds_rc"],
                "leg_map_sha256": entry["leg_map_sha256"],
                "support_digest": support_digest(record),
                "subject": record.get("subject"),
                "fine_readings": entry["fine_readings"],
            }
        )
    return panels


def teaching_words(case: Mapping[str, Any]) -> dict[str, Any]:
    """How a precedent was taught: its source kind and whether a lesion was placed.

    A bootstrap case is an official study label; an admitted case is a report
    call. Neither places a lesion in an object: ``pixel_localization_confirmed``
    is carried through when the case states it.
    """
    teaching = case.get("teaching")
    source = case.get("teaching_source")
    if isinstance(teaching, Mapping):
        return {
            "kind": teaching.get("kind"),
            "revision": teaching.get("revision"),
            "source_scope": teaching.get("source_scope"),
            "pixel_localization_confirmed": teaching.get(
                "pixel_localization_confirmed"
            ),
        }
    if isinstance(source, Mapping):
        return {
            "kind": source.get("kind"),
            "revision": source.get("revision"),
            "source_scope": None,
            "pixel_localization_confirmed": None,
        }
    return {
        "kind": source if isinstance(source, str) else None,
        "revision": case.get("teaching_revision"),
        "source_scope": None,
        "pixel_localization_confirmed": None,
    }


def selection_pin(question: str, voice: Mapping[str, Any]) -> dict[str, Any]:
    """Whether the selection a voice recorded is the one the current code derives.

    The voice keeps the digest of the declaration it selected banks from and
    the query banks it selected. The digest is compared with the current
    selection's, by the locator's own function, so a changed declaration is
    named; the recorded banks stay the ones drawn either way.
    """
    source = voice.get("source")
    recorded = source.get("selection") if isinstance(source, Mapping) else None
    if not isinstance(recorded, Mapping):
        return {"status": "not_recorded", "selected_banks": None}
    pin: dict[str, Any] = {
        "version": recorded.get("version"),
        "descriptor_sha256": recorded.get("descriptor_sha256"),
        "selected_banks": list(recorded.get("selected_banks") or ()),
    }
    try:
        from knee.diagnosis.squint_locator import _selection_digest
        from knee.diagnosis.squint_questions import question_selection

        current = _selection_digest(question_selection(question))
    except (ImportError, ValueError):
        return {**pin, "status": "unavailable_now"}
    matches = current == recorded.get("descriptor_sha256")
    return {**pin, "status": "matches_current" if matches else "differs_from_current"}


def _precedent(
    case_id: str | None,
    tied: Sequence[str],
    terms_by_id: Mapping[str, Mapping[str, Any]],
    cases_by_id: Mapping[str, Mapping[str, Any]],
    memory: Mapping[str, Any],
    *,
    question: str | None = None,
    query_banks: Mapping[str, Any] | None = None,
    selected_banks: Sequence[str] | None = None,
) -> dict[str, Any] | None:
    """One drawn precedent: its recorded term, its own places and how it was taught.

    ``query_banks`` is the verified query profile's banks, or None when the
    query is unverified; the memory side of the term is checked either way, and
    a case whose counts differ from the record is named and not drawn. A case
    admitted from a report keeps its per-question scope as ``condition_scopes``
    rather than ``presentation_scope``; the recall term then carries none, and
    the case's own is shown, named as such.
    """
    if case_id is None:
        return None
    case = cases_by_id.get(case_id)
    term = terms_by_id.get(case_id)
    if not isinstance(case, Mapping):
        return {"case_id": case_id, "code": "precedent_not_in_memory"}
    if not isinstance(term, Mapping):
        return {"case_id": case_id, "code": "precedent_without_recorded_term"}
    profile = case.get("profile") or {}
    banks = {name: list(counts) for name, counts in profile.get("banks", {}).items()}
    reproduction = term_reproduction(query_banks or {}, banks, term, selected_banks)
    if reproduction["code"] == "term_malformed":
        return {"case_id": case_id, "code": "recorded_term_malformed"}
    if not reproduction["case"]:
        return {
            "case_id": case_id,
            "code": "memory_case_differs_from_record",
            "reproduction": reproduction,
        }
    regions = [
        {**dict(region), "anchors": window_anchors({}, region)}
        for region in case.get("regions", ()) or ()
        if isinstance(region, Mapping)
    ]
    case_scopes = case.get("condition_scopes")
    case_scope = case_scopes.get(question) if isinstance(case_scopes, Mapping) else None
    return {
        "code": "drawn",
        "case_id": case_id,
        "study_uid": case.get("study_uid"),
        "subject": case.get("subject"),
        "call": term.get("call"),
        "call_scope": term.get("call_scope") or case_scope,
        "call_scope_source": (
            "recall_term"
            if term.get("call_scope")
            else "case_condition_scopes"
            if case_scope
            else None
        ),
        "squared_cosine": _fraction(term.get("squared_cosine")),
        "reaches_trust": term.get("reaches_trust"),
        "reason_code": term.get("reason_code"),
        "trust": _fraction(term.get("trust")),
        "common_banks": list(term.get("common_speaking_banks", ())),
        "banks": banks,
        "regions": regions,
        "panels": reading_panels(profile, regions),
        "reproduction": reproduction if query_banks is not None else None,
        "teaching": teaching_words(case),
        "tied_case_ids": [value for value in tied if value != case_id],
        "full_profile": _full_profile_summary(memory, case),
    }


def question_plan(
    record: Mapping[str, Any],
    question: str,
    memory: Mapping[str, Any],
    cases_by_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    """Everything one sheet draws for one question, read from what was recorded."""
    row = record["questions"][question]
    finding = row.get("finding", {})
    evidence = finding.get("evidence", {}) if isinstance(finding, Mapping) else {}
    readings = evidence.get("readings", {}) if isinstance(evidence, Mapping) else {}
    necessary = list(evidence.get("necessary", ()) or ())
    alternatives = [
        s for s in evidence.get("alternatives", ()) or () if s not in necessary
    ]
    supporting = list(evidence.get("supporting", ()) or ())
    voices = row.get("objects", {})
    located = record.get("objects", {})
    defining = []
    for subject, role in [(s, "necessary") for s in necessary] + [
        (s, "alternative") for s in alternatives
    ]:
        voice = voices.get(subject, {}) if isinstance(voices, Mapping) else {}
        object_record = located.get(subject, {}) if isinstance(located, Mapping) else {}
        terms = [t for t in voice.get("case_terms", ()) or () if isinstance(t, Mapping)]
        terms_by_id = {
            t["case_id"]: t for t in terms if isinstance(t.get("case_id"), str)
        }
        case_profiles = {
            case_id: (cases_by_id.get(case_id) or {}).get("profile")
            for case_id in terms_by_id
        }
        pin = selection_pin(question, voice)
        recalled = recalled_query_profile(
            object_record.get("profile"),
            terms,
            case_profiles,
            expected_area_profile=object_record.get("expected_area_profile"),
            selected_banks=pin["selected_banks"],
        )
        verified = recalled["code"] in VERIFIED_QUERY_CODES
        query_banks = dict(recalled["profile"]["banks"]) if verified else None
        compared = sorted({name for term in terms for name in _bank_names(term)})
        normal_ids = list(voice.get("nearest_negative_case_ids", ()) or ())
        presentation_ids = list(voice.get("nearest_positive_case_ids", ()) or ())
        regions = []
        for region in voice.get("regions") or object_record.get("regions") or ():
            if not isinstance(region, Mapping):
                continue
            regions.append(
                {
                    **{k: v for k, v in region.items()},
                    "anchors": window_anchors(object_record, region),
                }
            )
        panel_profile = recalled["profile"]
        final_fine_readings_not_compared = 0
        query_source = (
            panel_profile.get("source") if isinstance(panel_profile, Mapping) else None
        )
        comparison_fields = [parse_bank(name) for name in compared]
        coarse_only_v2_comparison = (
            verified
            and bool(compared)
            and isinstance(query_source, Mapping)
            and query_source.get("procedure") == TERRITORY_PROCEDURE
            and all(
                fields is not None
                and fields["version"] == "v2"
                and fields["scale_mm"] != FINE_SCALE_MM
                for fields in comparison_fields
            )
        )
        if coarse_only_v2_comparison:
            # Keep the exact recalled profile and counts, but do not draw later
            # refinement places as though a coarse-only comparison read them.
            panel_profile = (
                profile_before_fine_reading(panel_profile, FINE_SCALE_MM)
                or panel_profile
            )
            final_profile = object_record.get("profile")
            final_fine_readings_not_compared = sum(
                entry["fine_readings"] for entry in profile_territories(final_profile)
            )
        if verified or recalled["code"] == "no_recorded_terms":
            panels = reading_panels(panel_profile, regions)
        else:
            # The profile that was compared is not known, so the places it was
            # counted over are not either: only the addresses the run located.
            panels = region_panels(regions, "located_address_only")
        shown_banks = (recalled["profile"] or {}).get("banks", {})
        versions = {
            fields["version"]
            for name in [*shown_banks, *(n for t in terms for n in _bank_names(t))]
            if (fields := parse_bank(name)) is not None
        }
        if coarse_only_v2_comparison:
            panel_scope_source = "coarse_lineage_for_coarse_only_comparison"
        elif verified:
            panel_scope_source = "recalled_profile_lineage"
        elif recalled["code"] == "no_recorded_terms":
            panel_scope_source = "profile_lineage_without_recorded_terms"
        else:
            panel_scope_source = "located_address_only_unverified"
        panel_scope = {
            "source": panel_scope_source,
            "fine_readings_in_final_not_compared": final_fine_readings_not_compared,
        }
        reading = readings.get(subject, {}) if isinstance(readings, Mapping) else {}
        called = [
            case
            for case in cases_by_id.values()
            if isinstance(case, Mapping)
            and case.get("subject") == subject
            and question in (case.get("condition_calls") or {})
        ]
        defining.append(
            {
                "subject": subject,
                "role": role,
                # Cases of this tissue the memory holds with a call for this
                # question, from studies other than this one.
                "memory_cases_other_studies": sum(
                    1
                    for case in called
                    if case.get("study_uid") != record.get("study_uid")
                ),
                "reading": {"state": reading.get("state"), "code": reading.get("code")},
                "outcome": voice.get("outcome", "no_recall_voice"),
                "envelope_status": voice.get("envelope_status"),
                "location_status": voice.get(
                    "location_status", object_record.get("status", "unavailable")
                ),
                "location_source": _location_source(object_record),
                "anchor": anchor_words(object_record),
                "decision_scope": voice.get("decision_scope"),
                "query_origins": voice.get("query_origins"),
                "own_outline": _own_outline_words(object_record),
                "selection": {k: v for k, v in pin.items() if k != "selected_banks"},
                "regions": regions,
                "panels": panels,
                "profile_versions": sorted(versions),
                "compared_banks": compared,
                "compared_roles": compared_roles(compared),
                "panel_scope": panel_scope,
                "term_count": len(terms),
                "speaking_count": len(voice.get("speaking_case_ids", ()) or ()),
                "not_compared": {
                    "excluded_same_study": len(voice.get("excluded_case_ids") or ()),
                    "incompatible_encoding": len(
                        voice.get("incompatible_case_ids") or ()
                    ),
                    "silent_no_common_reading": len(voice.get("silent_case_ids") or ()),
                    "censors_compared": len(voice.get("censor_terms") or ()),
                    "vetoed_answers": list(voice.get("vetoed_answers") or ()),
                },
                "query": {
                    "code": recalled["code"],
                    "verified": verified,
                    "checked_terms": recalled["checked_terms"],
                    "term_codes": recalled["term_codes"],
                    "memory_case_differs": recalled["memory_case_differs"],
                    "also_reproduced_by": recalled["also_reproduced_by"],
                    "banks": query_banks if query_banks is not None else {},
                    "withheld_bank_count": 0 if verified else len(shown_banks),
                },
                "normal": _precedent(
                    normal_ids[0] if normal_ids else None,
                    normal_ids,
                    terms_by_id,
                    cases_by_id,
                    memory,
                    question=question,
                    query_banks=query_banks,
                    selected_banks=pin["selected_banks"],
                ),
                "presentation": _precedent(
                    presentation_ids[0] if presentation_ids else None,
                    presentation_ids,
                    terms_by_id,
                    cases_by_id,
                    memory,
                    question=question,
                    query_banks=query_banks,
                    selected_banks=pin["selected_banks"],
                ),
            }
        )
    supporting_rows = []
    for subject in supporting:
        voice = voices.get(subject, {}) if isinstance(voices, Mapping) else {}
        reading = readings.get(subject, {}) if isinstance(readings, Mapping) else {}
        supporting_rows.append(
            {
                "subject": subject,
                "state": reading.get("state"),
                "code": reading.get("code"),
                "outcome": voice.get("outcome", "no_recall_voice"),
                "nearest_normal": (voice.get("nearest_negative_case_ids") or [None])[0],
                "nearest_presentation": (
                    voice.get("nearest_positive_case_ids") or [None]
                )[0],
            }
        )
    configuration = (
        voices.get(f"diagnosis/{question}", {}) if isinstance(voices, Mapping) else {}
    )
    # The contract records None, not {}, for a question with no configuration voice.
    coverage = (
        evidence.get("joint_configuration_coverage") or {}
        if isinstance(evidence, Mapping)
        else {}
    )
    joint_voice = (
        (evidence.get("joint_voice") or {}) if isinstance(evidence, Mapping) else {}
    )
    ranking = row.get("ranking", {}) if isinstance(row.get("ranking"), Mapping) else {}
    ledger = (memory.get("label_ledger") or {}).get(record.get("study_uid"), {})
    return {
        "schema": SCHEMA,
        "study_uid": record.get("study_uid"),
        "question": question,
        "finding": {
            "outcome": finding.get("outcome"),
            "reason": finding.get("reason"),
            "kind": evidence.get("kind") if isinstance(evidence, Mapping) else None,
            "contract_id": finding.get("contract_id"),
            "decided_by": evidence.get("decided_by")
            if isinstance(evidence, Mapping)
            else None,
        },
        "ranking": {
            "value": record.get("values", {}).get(question),
            "tier": ranking.get("tier"),
        },
        "study_label": ledger.get(question) if isinstance(ledger, Mapping) else None,
        "defining": defining,
        "supporting": supporting_rows,
        "configuration": {
            "outcome": configuration.get("outcome", "no_configuration_voice"),
            "term_count": len(configuration.get("case_terms", ()) or ()),
            "nearest_normal": (
                configuration.get("nearest_negative_case_ids") or [None]
            )[0],
            "nearest_presentation": (
                configuration.get("nearest_positive_case_ids") or [None]
            )[0],
            "joint_voice": {
                "state": joint_voice.get("state"),
                "code": joint_voice.get("code"),
            },
            "coverage": coverage.get("status"),
        },
    }


def _location_source(object_record: Mapping[str, Any]) -> str:
    evidence = object_record.get("evidence")
    if not isinstance(evidence, Mapping):
        return "no_location_evidence"
    for key in ("location_mode", "source"):
        value = evidence.get(key)
        if isinstance(value, str) and value:
            route = evidence.get("location_route")
            return (
                f"{value}; route {route}" if isinstance(route, str) and route else value
            )
    return "unnamed_location_evidence"


def _bank_names(term: Mapping[str, Any]) -> list[str]:
    names = term.get("common_speaking_banks")
    return (
        [name for name in names if isinstance(name, str)]
        if isinstance(names, list)
        else []
    )


def anchor_words(object_record: Mapping[str, Any]) -> str | None:
    """A bone's structural anchor in words: its status and the key planes it chose.

    The reference an anchor gives is built from its key planes; a partial
    anchor has planes and no reference. Neither is the centre of a section.
    """
    evidence = object_record.get("evidence")
    anchor = evidence.get("anchor") if isinstance(evidence, Mapping) else None
    if not isinstance(anchor, Mapping):
        return None
    planes = anchor.get("key_planes")
    chosen = (
        [
            f"{orientation} slice {plane.get('slice')}"
            for orientation, plane in sorted(planes.items())
            if isinstance(plane, Mapping) and plane.get("outcome") == "selected"
        ]
        if isinstance(planes, Mapping)
        else []
    )
    return f"structural anchor {anchor.get('status')}; key planes: {', '.join(chosen) or 'none selected'}"


def _own_outline_words(object_record: Mapping[str, Any]) -> dict[str, Any] | None:
    """Whether a small part's own-outline reading replaced its expected-area reading."""
    own = object_record.get("own_outline")
    if not isinstance(own, Mapping):
        return None
    return {
        "code": own.get("code"),
        "profile_replaced": own.get("profile_replaced"),
        "kept_expected_area_profile": isinstance(
            object_record.get("expected_area_profile"), Mapping
        ),
    }


# --------------------------------------------------------------------------
# What must be read from disk for a set of plans


def sheet_requests(plans: Sequence[Mapping[str, Any]]) -> dict[str, dict[str, set]]:
    """Native slices and teacher supports to read, grouped by study.

    A panel asks for a teacher support only when its places came from one: its
    territory's origin is a teacher's support, or (an older record, with no
    territory) its region says its extent came from retained object support. A
    window a locator proposed, a bone's structural support and a residual
    support are addresses or runtime masks the record does not keep: they ask
    for the slice alone.
    """
    requests: dict[str, dict[str, set]] = {}

    def want(study_uid: object, subject: object, panel: Mapping[str, Any]) -> None:
        window = panel.get("window")
        series_uid = panel.get("series_uid")
        if (
            not isinstance(study_uid, str)
            or window is None
            or not isinstance(series_uid, str)
        ):
            return
        entry = requests.setdefault(study_uid, {"slices": set(), "supports": set()})
        entry["slices"].add((series_uid, window[0]))
        region = panel.get("region") or {}
        from_support = panel.get("origin") == "teacher_support" or (
            panel.get("origin") is None
            and region.get("extent_source") == "retained_object_support"
        )
        owner = panel.get("subject") or subject
        if from_support and isinstance(owner, str):
            entry["supports"].add((owner, series_uid, window[0]))

    for plan in plans:
        for subject in plan["defining"]:
            for panel in subject["panels"]:
                want(plan["study_uid"], subject["subject"], panel)
            for key in ("normal", "presentation"):
                precedent = subject.get(key)
                if isinstance(precedent, Mapping) and precedent.get("code") == "drawn":
                    for panel in precedent["panels"]:
                        want(precedent["study_uid"], precedent["subject"], panel)
    return requests


def bank_blocks(
    profiles: Mapping[str, Mapping[str, Sequence[int]]],
    compared: Mapping[str, Sequence[str]],
) -> dict[str, Any]:
    """Arrange the banks of several profiles into one grid per view.

    A cell is one bank: (metric, scale, direction column). ``compared`` names,
    per comparison, the banks it read. A block no comparison read is kept with
    ``compared`` False so the sheet can name it rather than draw it.
    """
    parsed: dict[str, dict[str, Any]] = {}
    unparsed: set[str] = set()
    for banks in profiles.values():
        for name in banks:
            fields = parse_bank(name)
            if fields is None:
                unparsed.add(name)
            else:
                parsed[name] = fields
    compared_names = {name for names in compared.values() for name in names}
    grouped: dict[tuple, set[str]] = {}
    for name, fields in parsed.items():
        grouped.setdefault((fields["view"], fields["role"]), set()).add(name)
    blocks = []
    for key in sorted(grouped, key=lambda item: (item[0], item[1] or "")):
        names = grouped[key]
        metrics = [
            m for m in METRIC_ORDER if any(parsed[n]["metric"] == m for n in names)
        ]
        metrics += sorted({parsed[n]["metric"] for n in names} - set(metrics))
        scales = sorted({parsed[n]["scale_mm"] for n in names}, reverse=True)
        present = {direction_column(parsed[n]["direction"]) for n in names}
        directions = [d for d in DIRECTION_ORDER if d in present]
        directions += sorted(present - set(directions))
        cells = {
            (
                parsed[n]["metric"],
                parsed[n]["scale_mm"],
                direction_column(parsed[n]["direction"]),
            ): n
            for n in names
        }
        writers = sorted(
            label for label, banks in profiles.items() if any(n in banks for n in names)
        )
        blocks.append(
            {
                "view": key[0],
                "role": key[1],
                "compared": any(n in compared_names for n in names),
                "metrics": metrics,
                "columns": [(s, d) for s in scales for d in directions],
                "cells": cells,
                "writers": writers,
            }
        )
    return {"blocks": blocks, "unparsed": sorted(unparsed)}


# --------------------------------------------------------------------------
# Reading native slices and teacher supports, one study at a time


def verified_product(product: Mapping[str, Any] | None) -> tuple[str | None, str]:
    """A teacher product's path, only if its bytes match the digest the memory kept.

    The memory records each product's path and SHA-256 when it is compiled. A
    product that has since changed, or whose digest was never recorded, is not
    opened: a support read from it would not be the one the case was written
    over.
    """
    if not isinstance(product, Mapping):
        return None, "teacher_product_unrecorded"
    path, expected = product.get("path"), product.get("sha256")
    if not isinstance(path, str) or not Path(path).is_file():
        return None, "teacher_product_unavailable"
    if not isinstance(expected, str) or not expected:
        return None, "teacher_product_digest_unrecorded"
    if _sha256(Path(path)) != expected:
        return None, "teacher_product_sha256_mismatch"
    return path, "verified"


def leg_codes_digest(leg_map: object) -> str | None:
    """The digest the territory writer keeps of a leg map's codes."""
    codes = leg_map.get("codes") if isinstance(leg_map, Mapping) else None
    if not isinstance(codes, np.ndarray):
        return None
    return hashlib.sha256(np.ascontiguousarray(codes).tobytes()).hexdigest()


def _slice_image(
    series: Mapping[str, Any] | None,
    z: int,
    leg_map,
    leg_sha256: str | None = None,
) -> dict[str, Any]:
    """One native slice, its tile grid and leg codes, as plain picklable values."""
    if series is None:
        return {"code": "series_missing"}
    native = series.get("native_series")
    stack = series.get("stack")
    volume = getattr(native, "volume", None)
    if volume is None or stack is None or getattr(stack, "code", None) != "present":
        return {"code": "native_volume_or_squint_unavailable"}
    if not 0 <= z < volume.shape[0]:
        return {"code": "slice_outside_series"}
    frame_inputs = None
    geometry = series.get("geometry")
    if isinstance(geometry, Mapping):
        try:
            frame_inputs = [
                [float(v) for v in np.asarray(geometry[key][z]).reshape(-1)]
                for key in ("position", "orientation", "spacing")
            ]
        except (IndexError, KeyError, TypeError, ValueError):
            frame_inputs = None
    leg_codes = None
    if isinstance(leg_map, Mapping) and isinstance(leg_map.get("codes"), np.ndarray):
        leg_codes = np.array(leg_map["codes"][z], copy=True)
    return {
        "code": "read",
        "pixels": np.array(volume[z], dtype=np.float32, copy=True),
        "bounds_rc": np.array(stack.bounds_rc, copy=True),
        "tile_shape_rc": tuple(int(v) for v in stack.tile_shape_rc),
        "tile_mm": float(stack.tile_mm),
        "frame_inputs": frame_inputs,
        "view": tuple(
            series.get("view", {}).get(key, "?")
            for key in ("orientation", "fluid_sensitive", "fat_suppression")
        ),
        "leg_codes": leg_codes,
        "leg_rule": leg_map.get("rule") if isinstance(leg_map, Mapping) else None,
        "leg_codes_sha256": leg_sha256,
        "source_path": str(native.slices[z].path.resolve())
        if hasattr(native, "slices")
        else None,
    }


def _frame(image: Mapping[str, Any]):
    from knee.collapse.physical import PlaneFrame

    inputs = image.get("frame_inputs")
    if not inputs:
        return None
    try:
        return PlaneFrame.from_dicom(*inputs)
    except (TypeError, ValueError):
        return None


def _compact_territory(territory: Mapping[str, Any], info: Mapping[str, Any]) -> dict:
    if territory.get("code") != "resolved":
        return {
            "code": str(territory.get("code")),
            "support_code": info.get("code") if isinstance(info, Mapping) else None,
        }
    support = territory.get("native_support") or {}
    mask = np.ascontiguousarray(support.get("mask"), dtype=np.bool_)
    return {
        "code": "resolved",
        "tile_window": list(territory["tile_window"]),
        "roles": np.array(territory["roles"], copy=True),
        "object_share": np.array(territory["object_share"], copy=True),
        "native_support": {
            "mask": np.array(mask, copy=True),
            "offset_rc": list(support.get("offset_rc", (0, 0))),
        },
        "mask_sha256": hashlib.sha256(mask.tobytes()).hexdigest(),
        "resolver": (info.get("provenance") or {}).get("resolver"),
        "support_bbox": list(info.get("bbox") or ()),
    }


def read_study_images(
    root: Path,
    study_uid: str,
    need: Mapping[str, Sequence[tuple]],
    product: Mapping[str, Any] | None,
    io_workers: int,
) -> tuple[dict, dict, dict]:
    """One study's requested slices and teacher supports, read and released.

    Runs in its own short-lived process when called from ``read_images``, so the
    study's decoded volumes leave with the process. Returns the slices, the
    territories (or their named refusals) and this study's work. The teacher
    product is opened only if its bytes match the digest the memory recorded.
    """
    from knee.diagnosis.squint_leg import leg_maps
    from knee.diagnosis.squint_profiles import read_study_squints
    from knee.diagnosis.squint_support import support_mask, teacher_territory

    started = time.perf_counter()
    images: dict[tuple, dict] = {}
    territories: dict[tuple, dict] = {}
    study = read_study_squints(Path(root), study_uid, io_workers=io_workers)
    by_uid = {row["series_uid"]: row for row in study["series"]}
    try:
        legs = dict(leg_maps(study))
        leg_status = "measured"
    except (TypeError, ValueError) as error:
        # As the locator does: no leg map is no hatching, and the reason is kept.
        legs, leg_status = {}, f"unavailable:{error}"
    for series_uid, z in sorted(need["slices"]):
        images[(study_uid, series_uid, z)] = _slice_image(
            by_uid.get(series_uid),
            z,
            legs.get(series_uid),
            leg_codes_digest(legs.get(series_uid)),
        )
    supports = sorted(need["supports"])
    path, product_code = (
        verified_product(product) if supports else (None, "not_requested")
    )
    if supports and path is None:
        for subject, series_uid, z in supports:
            territories[(study_uid, subject, series_uid, z)] = {"code": product_code}
    elif path is not None:
        from knee.encoding.product import open_product

        with open_product(Path(path)) as opened:
            manifest = opened.manifest
            ownership = manifest.get("support_ownership", {})
            roots = manifest.get("source_roots", {})
            cache: dict = {}
            for subject, series_uid, z in supports:
                info = support_mask(
                    subject, series_uid, z, ownership, roots, cache, opened.arrays
                )
                series = by_uid.get(series_uid)
                territory = (
                    teacher_territory(
                        study_uid, series, subject, info, z, legs.get(series_uid)
                    )
                    if series is not None
                    else {"code": "series_missing"}
                )
                territories[(study_uid, subject, series_uid, z)] = _compact_territory(
                    territory, info
                )
    work = {
        "seconds": round(time.perf_counter() - started, 3),
        "series_read": study["work"].get("series_read"),
        "slices_read": study["work"].get("slices_read"),
        "slices_drawn": len(need["slices"]),
        "supports_requested": len(supports),
        "teacher_product": product_code,
        "leg_maps": leg_status,
    }
    return images, territories, work


def read_images(
    root: Path,
    requests: Mapping[str, Mapping[str, set]],
    products: Mapping[str, Mapping[str, Any]],
    *,
    io_workers: int,
    isolate: bool = True,
) -> tuple[dict, dict, dict]:
    """Read every requested slice and support, one study at a time.

    With ``isolate`` each study is read in a fresh process that exits after it,
    one at a time, so decoded volumes never accumulate in this process.
    ``products`` maps a study to its teacher product's recorded path and digest.
    """
    images: dict[tuple, dict] = {}
    territories: dict[tuple, dict] = {}
    work: dict[str, dict] = {}
    jobs = [
        (
            study_uid,
            {
                "slices": sorted(requests[study_uid]["slices"]),
                "supports": sorted(requests[study_uid]["supports"]),
            },
        )
        for study_uid in sorted(requests)
    ]
    if isolate:
        import multiprocessing
        from concurrent.futures import ProcessPoolExecutor

        context = multiprocessing.get_context("spawn")
        with ProcessPoolExecutor(
            max_workers=1, mp_context=context, max_tasks_per_child=1
        ) as pool:
            for study_uid, need in jobs:
                study_images, study_territories, study_work = pool.submit(
                    read_study_images,
                    root,
                    study_uid,
                    need,
                    products.get(study_uid),
                    io_workers,
                ).result()
                images.update(study_images)
                territories.update(study_territories)
                work[study_uid] = study_work
    else:
        for study_uid, need in jobs:
            study_images, study_territories, study_work = read_study_images(
                root, study_uid, need, products.get(study_uid), io_workers
            )
            images.update(study_images)
            territories.update(study_territories)
            work[study_uid] = study_work
    return images, territories, work


# --------------------------------------------------------------------------
# Drawing (development only)


def _caption_lines(plan: Mapping[str, Any], run_label: str) -> list[str]:
    question = plan["question"]
    versions = {v for subject in plan["defining"] for v in subject["profile_versions"]}
    territory = "v2" in versions
    box = "v1" in versions or not versions
    lines = []
    if territory:
        lines.append(
            "The dashed yellow frame is the box around the object-role tiles. It is an "
            "address, not the object's outline."
        )
        lines.append(
            "Territory tiles (the places this profile was counted over): magenta = object "
            "role, cyan = context ring, grey hatch = outside the leg, never read. A tile "
            "the support touches is not pure object: the share of its pixels the support "
            "covers is an occupancy, and an expected place has no measured share. Solid "
            "outlines are roles whose banks a comparison read; dotted outlines were not "
            "read here. The magenta contour is the teacher's native support, drawn only "
            "where its digest equals the stored one."
        )
    if box:
        lines.append(
            "A v1 profile counted every 10 mm tile of its window alike; the dashed "
            "yellow frame is that window, an address and not the object's outline. "
            "Magenta/cyan/grey, where drawn, are a re-resolved teacher support for "
            "inspection only: that profile did not use these roles, and a support's "
            "share of the window is an occupancy, not purity."
        )
    lines.append(
        "A presentation precedent is a case called positive for "
        f"{question} by the official study label or by an independent report call "
        "(its teaching is shown). Either is a study-level call: it does not place a "
        "lesion in this object or in this window."
    )
    lines.append(
        "A normal-for-question precedent is a case called negative for "
        f"{question}; its scope is shown (normal for this condition only, or "
        "negative with another condition positive in that study)."
    )
    thirds = []
    if box:
        thirds.append("a v1 bank: thirds of the whole series")
    if territory:
        thirds.append(
            "a v2 bank: thirds over the series' inside-leg tiles (mixed tiles are "
            "coded, never set the cutoffs)"
        )
    lines.append(
        "Count tables: per bank, its places below / within / above the middle third of "
        f"that metric ({'; '.join(thirds)}; the 2 mm rung is coded with the 10 mm "
        "thirds). A dashed frame is a bank that profile did not write: silent, never "
        "a middle."
    )
    lines.append(
        "The query is drawn only from a profile that reproduces every recorded term "
        "(the dot and both squared norms over the recorded banks); otherwise it is "
        "marked UNVERIFIED and nothing is drawn or decoded from it as compared."
    )
    lines.append(
        f"Run: {run_label}. The official label of this study is shown for "
        "evaluation only; recall never reads it."
    )
    return lines


def _cosine_words(value: Sequence[int] | None) -> str:
    if not value:
        return "no recorded comparison"
    numerator, denominator = value
    return f"squared cosine {numerator / denominator:.4f}, cosine {math.sqrt(numerator / denominator):.4f}"


def _precedent_title(
    kind: str, precedent: Mapping[str, Any] | None, question: str
) -> str:
    if not isinstance(precedent, Mapping):
        return f"{kind}: no case of this call was compared"
    if precedent.get("code") != "drawn":
        return f"{kind}: {precedent.get('case_id')} ({precedent.get('code')})"
    call = precedent.get("call")
    scope = str(precedent.get("call_scope") or "?").replace("_", " ")
    if precedent.get("call_scope_source") == "case_condition_scopes":
        scope += ", scope kept by the case"
    trust = ENVELOPE_WORDS.get(
        precedent.get("reason_code"),
        "reaches its envelope"
        if precedent.get("reaches_trust")
        else "below its envelope"
        if precedent.get("trust") is not None
        else "no envelope",
    )
    ties = precedent.get("tied_case_ids") or []
    tie_words = f"; tied with {len(ties)} more" if ties else ""
    return (
        f"{kind}: study {_short(precedent.get('study_uid'))}, called "
        f"{'+1' if call == 1 else '-1' if call == -1 else call} for {question} ({scope})\n"
        f"{_cosine_words(precedent.get('squared_cosine'))}; {trust}{tie_words}\n"
        f"taught by {teaching_phrase(precedent.get('teaching'))}"
    )


ENVELOPE_WORDS = {
    "above_empirical_envelope": "reaches its envelope",
    "below_empirical_envelope": "below its envelope",
    "no_compatible_envelope": "no compatible envelope",
}
TEACHING_WORDS = {
    "official_train_csv_label": "the official study label",
    "independent_report_calls": "independent report calls",
}


def teaching_phrase(teaching: Mapping[str, Any] | None) -> str:
    """How a precedent was taught, in words; a study-level call places no lesion."""
    if not isinstance(teaching, Mapping) or not teaching.get("kind"):
        return "an unrecorded source"
    kind = str(teaching["kind"])
    words = TEACHING_WORDS.get(kind, kind)
    if teaching.get("pixel_localization_confirmed") is False:
        words += " (study-level; no pixel localization confirmed)"
    return words


def _panel_title(panel: Mapping[str, Any], image: Mapping[str, Any] | None) -> str:
    window = panel.get("window")
    if window is None:
        return "window unreadable"
    z0, z1, r0, r1, c0, c1 = window
    view_tuple = view_key(panel.get("view")) or ("?", "?", "?")
    tile_mm = image.get("tile_mm", 10.0) if isinstance(image, Mapping) else 10.0
    slices = f"slice {z0}" if z1 - z0 == 1 else f"slices {z0}-{z1 - 1}, only {z0} drawn"
    key = (panel.get("region") or {}).get("key_slice")
    if type(key) is int and key != z0:
        slices += f" (key plane {key}; nearest saved support used)"
    tiles = "object tiles" if panel.get("counted_by") == "territory" else "tiles"
    return (
        f"{view_short(view_tuple)}  series {_short(panel.get('series_uid'))}  {slices}\n"
        f"{tiles} r{r0}-{r1 - 1} c{c0}-{c1 - 1} ({r1 - r0}x{c1 - c0} = "
        f"{(r1 - r0) * tile_mm:g}x{(c1 - c0) * tile_mm:g} mm)"
    )


def grid_pin(panel: Mapping[str, Any], bounds_rc: np.ndarray) -> str:
    """Whether this study's tile grid is the one the profile was written on.

    The coarse reading recorded the native bounds of its territory's tile
    window. The same window on the grid read now must give those bounds, or
    the territory's tiles would be drawn on the wrong pixels.
    """
    territory = panel.get("territory")
    recorded = panel.get("recorded_native_bounds_rc")
    if territory is None or recorded is None:
        return "not_recorded"
    try:
        now = list(window_native_bounds(bounds_rc, territory["tile_window"]))
    except ValueError:
        return "differs"
    return "matches" if now == list(recorded) else "differs"


def leg_map_pin(panel: Mapping[str, Any], image: Mapping[str, Any]) -> str:
    """How the leg codes drawn relate to the profile's own leg map.

    ``profile_leg_map``: their digest equals the one the profile was written
    with. ``differs_from_profile``: they do not, and are not drawn.
    ``inspection_only``: the profile (v1) used no leg map. ``unavailable``: no
    leg codes were read.
    """
    if not isinstance(image.get("leg_codes"), np.ndarray):
        return "unavailable"
    pinned = panel.get("leg_map_sha256")
    if pinned is None:
        return "inspection_only"
    return (
        "profile_leg_map"
        if image.get("leg_codes_sha256") == pinned
        else "differs_from_profile"
    )


def draw_roles(
    ax,
    roles: np.ndarray,
    tile_window: Sequence[int],
    bounds: np.ndarray,
    compared: Sequence[str] | None,
) -> None:
    """One slice of a territory's roles: solid for roles a comparison read.

    ``compared`` is the roles whose banks a comparison read in this view. None
    is not "none": it says nothing is known of what was read (a support
    re-resolved for inspection), and every role is drawn as read. An empty
    sequence says no comparison read this view, and every role is dotted.
    """
    from matplotlib.patches import Rectangle

    _, _, tr0, tr1, tc0, tc1 = tile_window
    for i, tr in enumerate(range(tr0, tr1)):
        for j, tc in enumerate(range(tc0, tc1)):
            a, b, c, d = (int(v) for v in bounds[tr, tc])
            role = int(roles[i, j])
            if role == ROLE_OUTSIDE_LEG:
                ax.add_patch(
                    Rectangle(
                        (c - 0.5, a - 0.5),
                        d - c,
                        b - a,
                        fill=False,
                        edgecolor="#b8bcc2",
                        hatch="////",
                        linewidth=0.5,
                    )
                )
            elif role in ROLE_NAMES:
                read = compared is None or ROLE_NAMES[role] in compared
                is_object = role == ROLE_OBJECT
                ax.add_patch(
                    Rectangle(
                        (c - 0.5, a - 0.5),
                        d - c,
                        b - a,
                        facecolor=OBJECT if is_object else "none",
                        alpha=(0.16 if read else 0.07) if is_object else 0.9,
                        edgecolor=OBJECT if is_object else CONTEXT,
                        linewidth=0.8 if read else 0.5,
                        linestyle="-" if read else (0, (1.5, 1.5)),
                    )
                )


def _draw_panel(ax, panel, image, support, compared) -> dict[str, Any]:
    """One panel over its native slice; returns what was drawn and measured.

    ``panel`` is what a profile was counted over (``reading_panels``); ``support``
    the teacher support re-resolved for it, when one was requested; ``compared``
    the territory roles whose banks a comparison read in this panel's own view
    (empty when none did).
    """
    from matplotlib.patches import Rectangle

    ax.set_xticks([])
    ax.set_yticks([])
    window = panel.get("window")
    if window is None:
        ax.text(0.5, 0.5, "window unreadable", ha="center", va="center", fontsize=7)
        return {"code": "window_unreadable"}
    if not isinstance(image, Mapping) or image.get("code") != "read":
        code = image.get("code") if isinstance(image, Mapping) else "image_not_read"
        ax.text(
            0.5,
            0.5,
            f"native slice not drawn:\n{code}",
            ha="center",
            va="center",
            fontsize=7,
        )
        return {"code": str(code)}
    pixels = image["pixels"]
    bounds = image["bounds_rc"]
    try:
        native = window_native_bounds(bounds, window)
    except ValueError as error:
        ax.text(0.5, 0.5, str(error), ha="center", va="center", fontsize=7)
        return {"code": str(error)}
    r0, r1, c0, c1 = crop_bounds(native, image["tile_shape_rc"], pixels.shape)
    crop = pixels[r0:r1, c0:c1]
    finite = crop[np.isfinite(crop)]
    low, high = np.percentile(finite, (1.0, 99.0)) if finite.size else (0.0, 1.0)
    if not high > low:
        high = low + 1.0
    ax.imshow(
        crop,
        cmap="gray",
        vmin=low,
        vmax=high,
        interpolation="nearest",
        extent=(c0 - 0.5, c1 - 0.5, r1 - 0.5, r0 - 0.5),
    )
    ax.set_xlim(c0 - 0.5, c1 - 0.5)
    ax.set_ylim(r1 - 0.5, r0 - 0.5)
    _, _, wr0, wr1, wc0, wc1 = window
    leg_state = leg_map_pin(panel, image)
    # Hatching is drawn only for a leg map the profile was written with, or for a
    # v1 profile, which used none and is drawn against the prior for inspection.
    leg = (
        image.get("leg_codes")
        if leg_state in ("profile_leg_map", "inspection_only")
        else None
    )
    outside = mixed = 0
    for tr in range(wr0, wr1):
        for tc in range(wc0, wc1):
            a, b, c, d = (int(v) for v in bounds[tr, tc])
            ax.add_patch(
                Rectangle(
                    (c - 0.5, a - 0.5),
                    d - c,
                    b - a,
                    fill=False,
                    edgecolor="white",
                    linewidth=0.3,
                    alpha=0.35,
                )
            )
            if isinstance(leg, np.ndarray) and leg[tr, tc] == LEG_OUTSIDE:
                outside += 1
                ax.add_patch(
                    Rectangle(
                        (c - 0.5, a - 0.5),
                        d - c,
                        b - a,
                        fill=False,
                        edgecolor="#b8bcc2",
                        hatch="////",
                        linewidth=0.0,
                    )
                )
            elif isinstance(leg, np.ndarray) and leg[tr, tc] == LEG_MIXED:
                mixed += 1
    measured: dict[str, Any] = {
        "code": "drawn",
        "window": list(window),
        "window_native_rc": list(native),
        "window_px": int((native[1] - native[0]) * (native[3] - native[2])),
        "window_tiles": int((wr1 - wr0) * (wc1 - wc0)),
        "window_outside_leg_tiles": outside if isinstance(leg, np.ndarray) else None,
        "window_mixed_leg_tiles": mixed if isinstance(leg, np.ndarray) else None,
        "leg_map": leg_state,
        "counted_by": panel.get("counted_by"),
        "origin": panel.get("origin"),
        "source_path": image.get("source_path"),
    }
    # The roles drawn are the profile's own territory, on the grid it was
    # written on. A v1 profile has none; then a re-resolved teacher support
    # shows its roles for inspection only.
    own = panel.get("territory")
    resolved = isinstance(support, Mapping) and support.get("code") == "resolved"
    shown = None
    if own is not None:
        measured["grid_pin"] = grid_pin(panel, bounds)
        if measured["grid_pin"] != "differs":
            shown = ("profile_territory", own, window[0] - own["tile_window"][0])
    elif resolved:
        shown = ("re_resolved_teacher_support", support, 0)
    if shown is not None:
        source, drawn_territory, k = shown
        draw_roles(
            ax,
            np.asarray(drawn_territory["roles"])[k],
            drawn_territory["tile_window"],
            bounds,
            compared if source == "profile_territory" else None,
        )
        measured["roles_from"] = source
        measured["territory"] = territory_summary(drawn_territory)
        measured["compared_roles"] = list(compared)
    elif own is not None:
        measured["roles_from"] = "not_drawn_tile_grid_differs"
    if isinstance(support, Mapping) and not resolved:
        measured["support_code"] = support.get("code")
    if resolved:
        expected = panel.get("support_digest")
        if expected is not None and support.get("mask_sha256") != expected:
            measured["support_code"] = "mask_digest_differs_from_record"
        else:
            mask = np.asarray(support["native_support"]["mask"], dtype=bool)
            mask2d = mask.any(axis=0) if mask.ndim == 3 else mask
            orow, ocol = support["native_support"]["offset_rc"]
            if mask2d.any():
                padded = np.pad(mask2d.astype(float), 1)
                ys = np.arange(orow - 1, orow + mask2d.shape[0] + 1)
                xs = np.arange(ocol - 1, ocol + mask2d.shape[1] + 1)
                ax.contour(
                    xs, ys, padded, levels=[0.5], colors=[OBJECT], linewidths=1.1
                )
            in_window = support_in_window(mask2d, (orow, ocol), native)
            region = panel.get("region") or {}
            measured.update(
                {
                    "support_code": "drawn",
                    # Equal to the stored digest, or no digest was stored (an
                    # older record) and only the bounds below tie it to the case.
                    "support_mask_digest_matches": True if expected else None,
                    "support_px_in_window": in_window,
                    "support_share_of_window": round(
                        in_window / measured["window_px"], 4
                    )
                    if measured["window_px"]
                    else None,
                    "support_resolver": support.get("resolver"),
                    # The support resolved now against the bounds the region recorded.
                    "support_matches_region_bounds": (
                        list(support.get("support_bbox") or ())
                        == list(region.get("native_bounds_rc") or ())
                    )
                    if region.get("native_bounds_rc") is not None
                    else None,
                }
            )
    wr_native = native
    ax.add_patch(
        Rectangle(
            (wr_native[2] - 0.5, wr_native[0] - 0.5),
            wr_native[3] - wr_native[2],
            wr_native[1] - wr_native[0],
            fill=False,
            edgecolor=ADDRESS,
            linewidth=1.2,
            linestyle=(0, (4, 2)),
        )
    )
    frame = _frame(image)
    drawn_anchors = []
    for anchor in panel.get("anchors") or ():
        if frame is None:
            break
        point = np.asarray([anchor["point_lps"]], dtype=np.float64)
        row, col = frame.to_native(point)[0]
        off = float((point[0] - frame.origin_lps) @ frame.normal())
        visible = bool(r0 - 0.5 <= row <= r1 - 0.5 and c0 - 0.5 <= col <= c1 - 0.5)
        drawn_anchors.append(
            {
                **anchor,
                "native_rc": [float(row), float(col)],
                "off_plane_mm": round(off, 1),
                "in_view": visible,
            }
        )
        if not visible:
            continue
        if anchor["kind"] == "predicted_point":
            ax.plot([col], [row], marker="+", color=PREDICTED, markersize=7, mew=1.2)
        else:
            ax.plot(
                [col], [row], marker="o", mfc="none", mec=ANCHOR, markersize=6, mew=1.3
            )
            if anchor["kind"] == "anchor_point":
                ax.annotate(
                    anchor["label"].split(" (")[0] + f" ({abs(off):.0f} mm off)",
                    (col, row),
                    xytext=(3, -3),
                    textcoords="offset points",
                    fontsize=5.2,
                    color=ANCHOR,
                )
    measured["anchors"] = drawn_anchors
    # The crop fills the axes once its aspect is applied, so crop fractions are
    # axes fractions; the inset goes to the corner farthest from the window.
    ax.apply_aspect()
    centre_x = ((native[2] + native[3]) / 2 - (c0 - 0.5)) / (c1 - c0)
    centre_y = ((native[0] + native[1]) / 2 - (r0 - 0.5)) / (r1 - r0)
    inset = ax.inset_axes(inset_corner(centre_x, centre_y))
    whole = pixels
    finite_whole = whole[np.isfinite(whole)]
    wlow, whigh = (
        np.percentile(finite_whole, (1.0, 99.0)) if finite_whole.size else (0.0, 1.0)
    )
    if not whigh > wlow:
        whigh = wlow + 1.0
    inset.imshow(whole, cmap="gray", vmin=wlow, vmax=whigh, interpolation="nearest")
    inset.add_patch(
        Rectangle(
            (native[2] - 0.5, native[0] - 0.5),
            native[3] - native[2],
            native[1] - native[0],
            fill=False,
            edgecolor=ADDRESS,
            linewidth=0.8,
        )
    )
    inset.set_xticks([])
    inset.set_yticks([])
    for spine in inset.spines.values():
        spine.set_edgecolor("white")
        spine.set_linewidth(0.6)
    return measured


LEG_WORDS = {
    "profile_leg_map": "the leg map this profile was written with",
    "inspection_only": "the leg prior, for inspection (this profile used none)",
    "differs_from_profile": "not drawn: the leg map read now differs from the profile's",
}


def _panel_caption(measured: Mapping[str, Any], panel: Mapping[str, Any]) -> str:
    if measured.get("code") != "drawn":
        return str(measured.get("code"))
    lines = []
    leg_words = ""
    if measured.get("window_outside_leg_tiles") is not None:
        leg_words = (
            f"; {measured['window_outside_leg_tiles']} outside the leg, "
            f"{measured['window_mixed_leg_tiles']} straddling it"
        )
    lines.append(
        f"window: {measured['window_tiles']} tiles, {measured['window_px']} px{leg_words}"
    )
    if measured.get("leg_map") in LEG_WORDS:
        lines.append(f"leg: {LEG_WORDS[measured['leg_map']]}")
    territory = measured.get("territory")
    if measured.get("roles_from") == "profile_territory" and territory:
        shares = territory["object_tile_shares"]
        if shares:
            share_words = (
                f"each object tile has {min(shares):.0%}-{max(shares):.0%} of its "
                "pixels under the support (an occupancy, not purity)"
            )
        else:
            share_words = "expected places: no support was measured, so no share"
        lines.append(
            f"counted over {territory['object_tiles']} object, "
            f"{territory['context_tiles']} context, {territory['outside_leg_tiles']} "
            f"outside-leg tiles ({measured.get('origin')}); {share_words}"
        )
        if measured.get("grid_pin") == "matches":
            lines.append("tile grid equals the one the profile was written on")
    elif measured.get("roles_from") == "not_drawn_tile_grid_differs":
        lines.append(
            "territory tiles not drawn: the tile grid read now differs from the one "
            "the profile was written on"
        )
    elif territory:
        lines.append(
            "roles shown for inspection only: this profile counted the whole window"
        )
    if measured.get("support_code") == "drawn":
        share = measured.get("support_share_of_window")
        share_words = (
            f"{share:.1%} of the window" if share is not None else "window unavailable"
        )
        touched = (
            f"; touches {territory['object_tiles']} tiles, none pure object"
            if territory
            else ""
        )
        lines.append(
            f"native support: {measured['support_px_in_window']} px = "
            f"{share_words}{touched}"
        )
        if measured.get("support_mask_digest_matches") is None:
            lines.append(
                "support tied to the case by its bounds only (no stored digest)"
            )
        if measured.get("support_matches_region_bounds") is False:
            lines.append(
                "support resolved now differs from the region's recorded bounds"
            )
    elif measured.get("support_code"):
        lines.append(f"no support drawn: {measured['support_code']}")
    elif panel.get("counted_by") == "located_address_only":
        lines.append("address only: the profile compared is not reproduced")
    elif (panel.get("region") or {}).get(
        "extent_source"
    ) == "retained_physical_location":
        lines.append("physical-location fallback: no native support, a location only")
    elif not territory:
        lines.append("address only: no object support was recorded for this window")
    return "\n".join(lines)


def _caption_rows(panel: Mapping[str, Any], width: int) -> int:
    """Rows the fullest caption this panel can carry takes when wrapped to ``width``.

    A sheet is laid out before any panel is drawn, so the room under the panels
    is reserved for the longest caption ``_panel_caption`` can write for them:
    every optional row present, at its widest.
    """
    territory = panel.get("territory")
    summary = territory_summary(territory) if territory is not None else None
    fullest = {
        "code": "drawn",
        "window_tiles": 9999,
        "window_px": 9999999,
        "window_outside_leg_tiles": 99,
        "window_mixed_leg_tiles": 99,
        "leg_map": "differs_from_profile",
        "roles_from": "profile_territory" if summary else None,
        "grid_pin": "matches",
        "origin": panel.get("origin"),
        "territory": summary,
        "support_code": "drawn",
        "support_px_in_window": 9999999,
        "support_share_of_window": 0.999,
        "support_mask_digest_matches": None,
        "support_matches_region_bounds": False,
    }
    return sum(
        _wrap(line, width).count("\n") + 1
        for line in _panel_caption(fullest, panel).split("\n")
    )


def _draw_bank_block(
    fig, x, y_top, block, profiles, comparisons, fig_w, fig_h, counter
):
    """One view's count tables (H2b) and its two 'how far apart' grids (H2c)."""
    from matplotlib.patches import Rectangle

    metrics, columns, cells = block["metrics"], block["columns"], block["cells"]
    label_w = 1.05
    cell_w, apart_w, row_h = 0.24, 0.11, 0.25
    grid_w = cell_w * len(columns)
    apart_grid_w = apart_w * len(columns)
    height = row_h * len(metrics)
    ax = fig.add_axes(
        [
            x / fig_w,
            1 - (y_top + 0.42 + height) / fig_h,
            (label_w + grid_w + 2 * (apart_grid_w + 0.25)) / fig_w,
            (height + 0.42) / fig_h,
        ]
    )
    ax.set_xlim(0, label_w + grid_w + 2 * (apart_grid_w + 0.25))
    ax.set_ylim(height + 0.42, 0)
    ax.axis("off")
    title = view_words(block["view"]) + (
        f" / {block['role']} places" if block["role"] else ""
    )
    ax.text(0, 0.1, title, fontsize=6.6, color=INK, va="top", fontweight="bold")
    scales = []
    for index, (scale, direction) in enumerate(columns):
        cx = label_w + index * cell_w
        ax.text(
            cx + cell_w / 2,
            0.40,
            DIRECTION_SHORT.get(direction, direction[:3]),
            fontsize=4.6,
            ha="center",
            va="bottom",
            color=SOFT_INK,
        )
        if scale not in scales:
            scales.append(scale)
            ax.text(cx, 0.27, f"{scale:g} mm", fontsize=5, va="bottom", color=INK)
    offsets = [label_w + grid_w + 0.25, label_w + grid_w + 0.25 + apart_grid_w + 0.25]
    for offset, (label, _) in zip(offsets, comparisons, strict=True):
        ax.text(
            offset,
            0.27,
            f"how far apart: {label} (columns as in the table)",
            fontsize=5,
            va="bottom",
            color=INK,
        )
    for r, metric in enumerate(metrics):
        y = 0.42 + r * row_h
        ax.text(
            label_w - 0.05,
            y + row_h / 2,
            METRIC_SHORT.get(metric, metric),
            fontsize=5.4,
            ha="right",
            va="center",
            color=INK,
        )
        for index, (scale, direction) in enumerate(columns):
            name = cells.get((metric, scale, direction))
            cx = label_w + index * cell_w
            if name is None:
                continue
            for k, (_, banks) in enumerate(profiles):
                by = y + 0.02 + k * (row_h - 0.04) / len(profiles)
                bh = (row_h - 0.04) / len(profiles) - 0.012
                counts = _counts(banks.get(name))
                if counts is None or not any(counts):
                    counter["silent"] += 1
                    ax.add_patch(
                        Rectangle(
                            (cx + 0.012, by),
                            cell_w - 0.024,
                            bh,
                            fill=False,
                            edgecolor=SILENT,
                            linewidth=0.35,
                            linestyle=(0, (1.5, 1.5)),
                        )
                    )
                    continue
                counter["written"] += 1
                total = sum(counts)
                left = cx + 0.012
                for value, colour in zip(counts, (BELOW, MIDDLE, ABOVE), strict=True):
                    width = (cell_w - 0.024) * value / total
                    if width > 0:
                        ax.add_patch(
                            Rectangle(
                                (left, by),
                                width,
                                bh,
                                facecolor=colour,
                                edgecolor="none",
                            )
                        )
                    left += width
            for offset, (_, (left_banks, right_banks, read)) in zip(
                offsets, comparisons, strict=True
            ):
                ax_x = offset + index * apart_w
                difference = (
                    bank_difference(left_banks.get(name), right_banks.get(name))
                    if name in read
                    else None
                )
                if difference is None:
                    ax.add_patch(
                        Rectangle(
                            (ax_x + 0.01, y + 0.05),
                            apart_w - 0.02,
                            row_h - 0.1,
                            fill=False,
                            edgecolor=SILENT,
                            linewidth=0.3,
                            linestyle=(0, (1.5, 1.5)),
                        )
                    )
                    continue
                counter["compared"] += 1
                ax.add_patch(
                    Rectangle(
                        (ax_x + 0.01, y + 0.05),
                        apart_w - 0.02,
                        row_h - 0.1,
                        facecolor="#eceef1",
                        edgecolor="none",
                    )
                )
                bar = (row_h - 0.1) * float(difference["apart"])
                ax.add_patch(
                    Rectangle(
                        (ax_x + 0.01, y + row_h - 0.05 - bar),
                        apart_w - 0.02,
                        bar,
                        facecolor="#4a5160",
                        edgecolor="none",
                    )
                )
    return height + 0.42


QUERY_WORDS = {
    "final": "the run's final profile",
    "expected_area_profile": (
        "the expected-area profile (the part's own-outline reading replaced it later)"
    ),
    "before_first_fine_reading": "the profile before its first 2 mm reading",
    "before_repeated_fine_reading": "the profile before its 2 mm reading was repeated",
    "no_recorded_terms": "the final profile (no recorded terms to check)",
    "query_profile_missing": "no query profile",
    "recalled_profile_not_reconstructed": (
        "UNVERIFIED: no profile in the record reproduces the recorded terms; "
        "nothing is drawn or decoded from it as compared"
    ),
}
SCOPE_WORDS = {
    "decide": "decide",
    "grade_only": (
        "grade_only (a small part not read over its own outline may grade within "
        "open and never assigns or defeats)"
    ),
}


def _subject_lines(
    plan: Mapping[str, Any], subject: Mapping[str, Any], width_in: float
) -> list[str]:
    """What the sheet says about one defining tissue's reading, wrapped to a width."""
    query = subject["query"]
    checked = (
        f" (checked on {query['checked_terms']} recorded terms)"
        if query["checked_terms"]
        else ""
    )
    also = (
        "; also reproduced by " + ", ".join(query["also_reproduced_by"])
        if query["also_reproduced_by"]
        else ""
    )
    origins = ", ".join(subject["query_origins"] or ()) or "none recorded"
    own = subject["own_outline"]
    own_words = (
        f"; own-outline reading {own['code']}"
        + (" (replaced the expected-area profile)" if own["profile_replaced"] else "")
        if own
        else ""
    )
    selection = subject["selection"]
    skipped = subject["not_compared"]
    scope = subject["decision_scope"]
    lines = [
        (
            f"location: {subject['location_status']} ({subject['location_source']})  ·  "
            f"query profile drawn: {QUERY_WORDS.get(query['code'], query['code'])}"
            f"{checked}{also}  ·  memory: {subject.get('memory_cases_other_studies', 0)} "
            f"cases of this tissue called for {plan['question']} from other studies"
        ),
        (
            f"{subject['anchor'] or 'no structural anchor recorded'}  ·  query read over "
            f"territory origin(s): {origins}{own_words}  ·  decision scope: "
            f"{SCOPE_WORDS.get(scope, scope or 'not recorded')}"
            f"  ·  question selection: {selection['status']}"
        ),
        (
            f"not compared: {skipped['excluded_same_study']} excluded (same study), "
            f"{skipped['incompatible_encoding']} incompatible encoding, "
            f"{skipped['silent_no_common_reading']} silent (no common selected reading); "
            f"{skipped['censors_compared']} censors compared"
            + (
                f", vetoed answers {skipped['vetoed_answers']}"
                if skipped["vetoed_answers"]
                else ""
            )
        ),
    ]
    fine_not_compared = subject["panel_scope"]["fine_readings_in_final_not_compared"]
    if fine_not_compared:
        count_word = "reading" if fine_not_compared == 1 else "readings"
        lines.append(
            f"{fine_not_compared} fine {count_word} held in the final profile were "
            "not compared; panels show the coarse source lineage."
        )
    if not query["verified"] and query["code"] != "no_recorded_terms":
        lines.append(
            f"term codes {query['term_codes']}; precedents whose memory counts "
            f"differ from the record: {len(query['memory_case_differs'])}"
        )
    chars = int(width_in * 17)
    return [
        part
        for line in lines
        for part in _wrap(line, chars).replace("\n   ", "\n").split("\n")
    ]


def draw_sheet(
    plan: Mapping[str, Any],
    images: Mapping[tuple, Mapping[str, Any]],
    territories: Mapping[tuple, Mapping[str, Any]],
    path: Path,
    *,
    run_label: str,
    source_line: str = "",
    dpi: int = 120,
) -> dict[str, Any]:
    """Draw one question's sheet and return what each panel showed and measured."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.lines as mlines
    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt

    question = plan["question"]
    margin = 0.35
    # Wide enough that every region panel keeps at least 2.6 in.
    most_slots = max(
        (
            sum(_image_groups(plan, subject, 24.0, margin)[1])
            for subject in plan["defining"]
        ),
        default=0,
    )
    fig_w = max(24.0, 2 * margin + 2 * _GROUP_GAP + 2.6 * most_slots)
    counter = {"written": 0, "silent": 0, "compared": 0}
    # Heights, so the figure can be made once at its full size.
    layouts: list[dict[str, Any]] = []
    for subject in plan["defining"]:
        query_banks = subject["query"]["banks"]
        normal = (
            subject["normal"]
            if isinstance(subject["normal"], Mapping)
            and subject["normal"].get("code") == "drawn"
            else None
        )
        presentation = (
            subject["presentation"]
            if isinstance(subject["presentation"], Mapping)
            and subject["presentation"].get("code") == "drawn"
            else None
        )
        # An unverified query has no banks here: no row, and no difference below
        # can be read from it (its comparisons have nothing to read).
        profiles = [("query", query_banks)] if subject["query"]["verified"] else []
        comparisons = []
        compared: dict[str, list[str]] = {}
        if normal is not None:
            profiles.append(("normal", normal["banks"]))
            compared["normal"] = normal["common_banks"]
        if presentation is not None:
            profiles.append(("presentation", presentation["banks"]))
            compared["presentation"] = presentation["common_banks"]
        comparisons.append(
            (
                "query vs normal",
                (
                    query_banks,
                    normal["banks"] if normal else {},
                    set(normal["common_banks"]) if normal else set(),
                ),
            )
        )
        comparisons.append(
            (
                "query vs presentation",
                (
                    query_banks,
                    presentation["banks"] if presentation else {},
                    set(presentation["common_banks"]) if presentation else set(),
                ),
            )
        )
        blocks = bank_blocks(dict(profiles), compared)
        drawn_blocks = [block for block in blocks["blocks"] if block["compared"]]
        lines = (len(drawn_blocks) + 1) // 2
        block_h = sum(
            max(
                0.25 * len(drawn_blocks[2 * i]["metrics"]),
                0.25 * len(drawn_blocks[2 * i + 1]["metrics"])
                if 2 * i + 1 < len(drawn_blocks)
                else 0,
            )
            + 0.55
            for i in range(lines)
        )
        groups, slots, panel_w = _image_groups(plan, subject, fig_w, margin)
        # Under the panels goes the fullest caption any of them can carry, wrapped
        # as it will be written (0.09 in a row), and never less than four rows.
        caption_rows_needed = max(
            (
                _caption_rows(panel, int(panel_w * 23))
                for _, panels, _, _ in groups
                for panel in panels
            ),
            default=0,
        )
        image_band = _TITLE_BAND + panel_w + 0.09 * max(4, caption_rows_needed)
        head = _subject_lines(plan, subject, fig_w - 2 * margin)
        head_h = 0.34 + 0.135 * len(head) + 0.1
        layouts.append(
            {
                "profiles": profiles,
                "comparisons": comparisons,
                "blocks": blocks,
                "drawn_blocks": drawn_blocks,
                "groups": groups,
                "slots": slots,
                "panel_w": panel_w,
                "image_band": image_band,
                "head": head,
                "head_h": head_h,
                "height": head_h + image_band + block_h + 0.35 + 1.55,
            }
        )
    caption_lines = [
        _wrap(line, int((fig_w - 2 * margin) * 15.5)).replace("\n   ", "\n")
        for line in _caption_lines(plan, run_label)
    ]
    caption_rows = sum(line.count("\n") + 1 for line in caption_lines)
    header_h = 1.2 + 0.155 * caption_rows + 0.12
    full_words = []
    for subject in plan["defining"]:
        for key in ("normal", "presentation"):
            precedent = subject[key]
            if isinstance(precedent, Mapping) and precedent.get("code") == "drawn":
                full = precedent.get("full_profile") or {}
                kinds = ", ".join(
                    f"{kind} {count}"
                    for kind, count in sorted(
                        (full.get("written_by_facet_kind") or {}).items()
                    )
                )
                full_words.append(
                    f"{subject['subject']} {key} (study {_short(precedent.get('study_uid'))}): "
                    f"{full.get('status', full.get('availability'))}, writes "
                    f"{full.get('written_banks', '?')} of {full.get('layout_banks', '?')} "
                    f"layout banks{' (' + kinds + ')' if kinds else ''}"
                )
    full_text = (
        "Full profiles (kept in memory beside the cheap ones; squint recall compared "
        "only the cheap banks above; the query has no full profile; banks not "
        "written are silent): " + ("; ".join(full_words) or "none")
    )
    full_lines = _wrap(full_text, int(fig_w * 17)).replace("\n   ", "\n")
    full_line_count = full_lines.count("\n") + 1
    footer_h = (
        1.65 + 0.19 * (max(1, len(plan["supporting"])) + 2) + 0.12 * full_line_count
    )
    fig_h = (
        header_h
        + sum(layout["height"] for layout in layouts)
        + footer_h
        + (0.9 if not layouts else 0)
    )
    fig = plt.figure(figsize=(fig_w, fig_h), dpi=dpi)
    fig.patch.set_facecolor("white")

    def text(x, y, value, **kw):
        fig.text(x / fig_w, 1 - y / fig_h, value, va="top", **kw)

    finding = plan["finding"]
    ranking = plan["ranking"]
    label = plan.get("study_label")
    label_words = {1: "positive (1)", 0: "negative (0)"}.get(
        label, "blank / unavailable"
    )
    text(
        margin,
        0.25,
        f"What recall compared for {question}",
        fontsize=17,
        color=INK,
        fontweight="bold",
    )
    value = ranking.get("value")
    status = plan.get("study_status")
    status_words = (
        f"  ·  STUDY NOT EXAMINED ({status}): nothing was compared"
        if status not in (None, "examined")
        else ""
    )
    text(
        margin,
        0.72,
        f"Study {plan['study_uid']}  ·  finding {finding.get('outcome')} ({finding.get('reason')})  ·  "
        f"contract kind {finding.get('kind')}  ·  value {value:.4f} ({ranking.get('tier')})  ·  "
        f"official study label {label_words}{status_words}"
        if isinstance(value, (int, float))
        else f"Study {plan['study_uid']}  ·  finding {finding.get('outcome')} ({finding.get('reason')}){status_words}",
        fontsize=9.5,
        color=SOFT_INK,
    )
    row = 0
    for line in caption_lines:
        for part in line.split("\n"):
            text(margin, 1.02 + row * 0.155, part, fontsize=7.4, color=INK)
            row += 1
    fig.add_artist(
        mlines.Line2D(
            [margin / fig_w, 1 - margin / fig_w],
            [1 - (header_h - 0.08) / fig_h] * 2,
            color="#c9ccd1",
            linewidth=0.8,
        )
    )
    y = header_h
    manifest_subjects = []
    if not layouts:
        text(
            margin,
            y + 0.1,
            "This question names no defining tissue in its recorded finding; nothing to draw.",
            fontsize=9,
            color=INK,
        )
        y += 0.9
    for subject, layout in zip(plan["defining"], layouts, strict=True):
        reading = subject["reading"]
        query = subject["query"]
        text(
            margin,
            y + 0.05,
            f"{subject['subject']}  —  {subject['role']} tissue  ·  reading {reading.get('state')} "
            f"({reading.get('code')})  ·  recall {subject['outcome']}  ·  {subject['term_count']} "
            f"precedents compared, {subject['speaking_count']} reach their envelope",
            fontsize=11,
            color=INK,
            fontweight="bold",
        )
        for row, part in enumerate(layout["head"]):
            text(
                margin,
                y + 0.34 + 0.135 * row,
                part,
                fontsize=7.4,
                color=INK if not query["verified"] and row == 0 else SOFT_INK,
            )
        y += layout["head_h"]
        groups, slots, panel_w = layout["groups"], layout["slots"], layout["panel_w"]
        gap = _GROUP_GAP
        x = margin
        subject_manifest = {
            "subject": subject["subject"],
            "role": subject["role"],
            "query_profile": query["code"],
            "query_verified": query["verified"],
            "query_term_codes": query["term_codes"],
            "query_also_reproduced_by": query["also_reproduced_by"],
            "memory_case_differs": query["memory_case_differs"],
            "decision_scope": subject["decision_scope"],
            "query_origins": subject["query_origins"],
            "own_outline": subject["own_outline"],
            "selection": subject["selection"],
            "not_compared": subject["not_compared"],
            "compared_roles": subject["compared_roles"],
            "image_band_px": [
                round(y * dpi),
                round((y + layout["image_band"]) * dpi),
            ],
            "groups": {},
        }
        for (key, panels, study_uid, case_subject), count in zip(
            groups, slots, strict=True
        ):
            if key == "query":
                what = (
                    "place(s) counted"
                    if query["verified"]
                    else "place(s) in the final profile (no precedent was compared)"
                    if query["code"] == "no_recorded_terms"
                    else "located address(es) only"
                )
                title = f"Query: this study ({_short(plan['study_uid'])}), {len(panels)} {what}"
            else:
                title = _precedent_title(
                    "Nearest called normal"
                    if key == "normal"
                    else "Nearest called a presentation",
                    subject[key],
                    question,
                )
            title = _wrap_lines(title, int(count * panel_w * _TITLE_CHARS_PER_IN))
            text(
                x,
                y,
                title,
                fontsize=6.9,
                color=INK,
                fontweight="bold" if key == "query" else "normal",
            )
            drawn = []
            if not panels:
                ax = fig.add_axes(
                    (
                        x / fig_w,
                        1 - (y + _TITLE_BAND + panel_w) / fig_h,
                        panel_w / fig_w,
                        panel_w / fig_h,
                    )
                )
                ax.axis("off")
                reason = "no located region" if key == "query" else "no region to draw"
                if key == "query" and subject["location_status"] in (
                    "unavailable",
                    None,
                ):
                    reason = f"not located ({subject['location_status']})"
                ax.text(
                    0.5,
                    0.5,
                    reason,
                    ha="center",
                    va="center",
                    fontsize=7,
                    color=SOFT_INK,
                    transform=ax.transAxes,
                )
            # The banks a comparison read: the query's panels by every comparison
            # of this tissue, a precedent's by its own comparison. A panel's roles
            # are those read in its own view, so a place in a view no comparison
            # read is not drawn as compared.
            banks_read = (
                subject["compared_banks"]
                if key == "query"
                else (subject[key].get("common_banks") or [])
                if isinstance(subject[key], Mapping)
                else []
            )
            for index, panel in enumerate(panels):
                roles_read = compared_roles(banks_read, view_key(panel.get("view")))
                px = x + index * panel_w
                ax = fig.add_axes(
                    (
                        (px + 0.03) / fig_w,
                        1 - (y + _TITLE_BAND + panel_w - 0.06) / fig_h,
                        (panel_w - 0.06) / fig_w,
                        (panel_w - 0.06) / fig_h,
                    )
                )
                window = panel.get("window")
                image_key = (
                    study_uid,
                    panel.get("series_uid"),
                    window[0] if window else None,
                )
                territory_key = (
                    study_uid,
                    panel.get("subject") or case_subject,
                    panel.get("series_uid"),
                    window[0] if window else None,
                )
                image = images.get(image_key)
                measured = _draw_panel(
                    ax, panel, image, territories.get(territory_key), roles_read
                )
                ax.set_title(_panel_title(panel, image), fontsize=5.4, pad=2, color=INK)
                text(
                    px + 0.03,
                    y + _TITLE_BAND + panel_w - 0.02,
                    "\n".join(
                        _wrap(line, int(panel_w * 23)).replace("\n   ", "\n")
                        for line in _panel_caption(measured, panel).split("\n")
                    ),
                    fontsize=5.3,
                    color=SOFT_INK,
                )
                drawn.append(
                    {
                        **measured,
                        "series_uid": panel.get("series_uid"),
                        "study_uid": study_uid,
                        # Pixel box of this panel and its caption in the PNG.
                        "panel_px": [
                            round((px + 0.03) * dpi),
                            round((y + _TITLE_BAND - 0.3) * dpi),
                            round((px + panel_w - 0.03) * dpi),
                            round((y + _TITLE_BAND + panel_w + 0.3) * dpi),
                        ],
                    }
                )
            subject_manifest["groups"][key] = drawn
            x += count * panel_w + gap
        y += layout["image_band"]
        # Count tables and how far apart.
        blocks = layout["drawn_blocks"]
        bx = margin
        line_top = y
        line_h = 0.0
        for index, block in enumerate(blocks):
            if index % 2 == 0 and index:
                y = line_top + line_h + 0.13
                line_top = y
                line_h = 0.0
                bx = margin
            used = _draw_bank_block(
                fig,
                bx,
                line_top,
                block,
                layout["profiles"],
                layout["comparisons"],
                fig_w,
                fig_h,
                counter,
            )
            line_h = max(line_h, used)
            bx += 11.7
        if blocks:
            y = line_top + line_h + 0.13
        uncompared = [
            block for block in layout["blocks"]["blocks"] if not block["compared"]
        ]
        names = "; ".join(
            f"{view_short(block['view'])}"
            f"{' ' + block['role'] + ' places' if block['role'] else ''} "
            f"(written by {', '.join(block['writers'])})"
            for block in uncompared
        )
        profile_names = ", ".join(label for label, _ in layout["profiles"])
        text(
            margin,
            y,
            f"Rows in each cell, top to bottom: {profile_names}.  Views no comparison read: {names or 'none'}."
            + (
                f"  Unparsed bank names: {len(layout['blocks']['unparsed'])}."
                if layout["blocks"]["unparsed"]
                else ""
            ),
            fontsize=6.4,
            color=SOFT_INK,
        )
        y += 0.35
        # Named differences.
        column_x = [margin, margin + fig_w / 2 - 0.2]
        named = {}
        for (label, (left, right, read)), cx, key in zip(
            layout["comparisons"], column_x, ("normal", "presentation"), strict=True
        ):
            precedent = subject[key]
            if read and not query["verified"]:
                text(
                    cx,
                    y,
                    f"{label}: named differences withheld; no profile in the record "
                    "reproduces the recorded terms, so none is read from the query",
                    fontsize=7.2,
                    color=INK,
                    fontweight="bold",
                )
                named[key] = []
                continue
            if not read:
                text(
                    cx,
                    y,
                    f"{label}: no comparison to decode",
                    fontsize=7.2,
                    color=INK,
                    fontweight="bold",
                )
                named[key] = []
                continue
            items = named_differences(
                left, right, sorted(read), left_label="query", right_label=key, limit=4
            )
            named[key] = items
            text(
                cx,
                y,
                f"Where they differ, named ({label}, {len(read)} banks read; "
                f"{_cosine_words(precedent.get('squared_cosine'))})",
                fontsize=7.2,
                color=INK,
                fontweight="bold",
            )
            for i, item in enumerate(items):
                text(
                    cx,
                    y + 0.24 + i * 0.3,
                    f"{i + 1}. " + _wrap(item["statement"], 190),
                    fontsize=6.3,
                    color=INK,
                )
        subject_manifest["named_differences"] = named
        subject_manifest["full_profiles"] = {
            key: subject[key].get("full_profile")
            if isinstance(subject[key], Mapping)
            else None
            for key in ("normal", "presentation")
        }
        manifest_subjects.append(subject_manifest)
        y += 1.55
    # Supporting tissue, the configuration voice, full profiles and the legend.
    text(
        margin,
        y,
        "Supporting tissue (context: reported, never decisive):",
        fontsize=7.6,
        color=INK,
        fontweight="bold",
    )
    for i, row in enumerate(plan["supporting"]):
        text(
            margin + 0.2,
            y + 0.19 * (i + 1),
            f"{row['subject']}: reading {row['state']} ({row['code']}); recall {row['outcome']}; nearest normal {_case_short(row['nearest_normal'])}; nearest presentation {_case_short(row['nearest_presentation'])}",
            fontsize=6.6,
            color=SOFT_INK,
        )
    if not plan["supporting"]:
        text(
            margin + 0.2,
            y + 0.19,
            "none named by this contract",
            fontsize=6.6,
            color=SOFT_INK,
        )
    config = plan["configuration"]
    yy = y + 0.19 * (max(1, len(plan["supporting"])) + 1)
    text(
        margin,
        yy,
        f"Whole-condition configuration voice: recall {config['outcome']} over {config['term_count']} configuration cases; "
        f"nearest called normal {_case_short(config['nearest_normal'])}, nearest called positive {_case_short(config['nearest_presentation'])}; "
        f"joint voice {config['joint_voice'].get('state')} ({config['joint_voice'].get('code')}); defining-tissue coverage: {config['coverage']}",
        fontsize=6.6,
        color=SOFT_INK,
    )
    text(margin, yy + 0.19, full_lines, fontsize=6.6, color=SOFT_INK)
    legend_y = yy + 0.3 + 0.12 * full_line_count
    swatches = [
        (BELOW, "below the middle third"),
        (MIDDLE, "within it"),
        (ABOVE, "above it"),
    ]
    lx = margin
    for colour, words in swatches:
        fig.add_artist(
            mpatches.Rectangle(
                (lx / fig_w, 1 - (legend_y + 0.13) / fig_h),
                0.16 / fig_w,
                0.12 / fig_h,
                transform=fig.transFigure,
                facecolor=colour,
                edgecolor="none",
            )
        )
        text(lx + 0.22, legend_y, words, fontsize=6.8, color=INK)
        lx += 2.6
    text(
        margin,
        legend_y + 0.22,
        "dashed grey frame: a bank not written (silent)  ·  dashed yellow: box of the "
        "places counted (an address)  ·  magenta: object-role tiles, and the teacher's "
        "native support contour where drawn  ·  cyan: context tiles  ·  dotted "
        "outline: a role no comparison read  ·  grey hatch: outside the leg\n"
        "orange circle: an anchor's reference point (labelled, with its distance off "
        "this slice) or the object's own reference point (unlabelled)  ·  white +: "
        "point the relation predicted",
        fontsize=6.6,
        color=INK,
    )
    if source_line:
        text(margin, legend_y + 0.62, source_line, fontsize=6.2, color=SOFT_INK)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi, facecolor="white")
    plt.close(fig)
    return {
        "question": question,
        "path": str(path),
        "size_in": [fig_w, round(fig_h, 2)],
        "cells": dict(counter),
        "subjects": manifest_subjects,
    }


def _wrap_lines(value: str, width: int) -> str:
    """Wrap each line of a multi-line title to ``width`` characters."""
    width = max(18, width)
    return "\n".join(
        _wrap(line, width).replace("\n   ", "\n") for line in value.split("\n")
    )


def _wrap(value: str, width: int) -> str:
    words = value.split(" ")
    lines, current = [], ""
    for word in words:
        if current and len(current) + 1 + len(word) > width:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current:
        lines.append(current)
    return "\n   ".join(lines)


# --------------------------------------------------------------------------
# The command


class VisualCapacityError(ValueError):
    """A named refusal to draw sheets from a run, memory or output that do not match."""


def studies_directory(run: Path) -> Path:
    """A run root (holding ``diagnostics/``) or its diagnostics directory."""
    for candidate in (run / "diagnostics" / "studies", run / "studies"):
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("run_studies_directory_missing")


def run_receipt(studies: Path) -> dict[str, Any] | None:
    """The run's receipt beside its ``studies`` directory, or None when absent."""
    from knee.json_store import load_json, resolve_json_path

    path = resolve_json_path(studies.parent / "receipt.json")
    if not path.is_file():
        return None
    try:
        receipt = load_json(path)
    except (OSError, ValueError) as error:
        raise VisualCapacityError("run_receipt_invalid") from error
    if not isinstance(receipt, Mapping):
        raise VisualCapacityError("run_receipt_invalid")
    return {**receipt, "_sha256": _sha256(path)}


def check_memory_pins(
    record: Mapping[str, Any],
    receipt: Mapping[str, Any] | None,
    memory: Mapping[str, Any],
    manifest_sha256: str | None,
) -> dict[str, Any]:
    """The loaded memory must be the one the run recalled from, or a named refusal.

    The study record names the memory revision it recalled from; the run's
    receipt, where present, its manifest digest; a capacity run's per-study
    exclusion record the digest of the population it prepared. Each that is
    present must equal what was loaded. Nothing here is a guess: a record that
    states none of these cannot be tied to the memory and says so.
    """
    uid = record.get("study_uid")
    if record.get("schema") != "knee.squint-study/v1":
        raise VisualCapacityError(f"study_record_schema_invalid:{uid}")
    revision = memory.get("revision")
    if record.get("memory_revision") != revision:
        raise VisualCapacityError(f"study_memory_revision_mismatch:{uid}")
    pins: dict[str, Any] = {
        "memory_revision": revision,
        "record_revision": "matches",
        "receipt": "absent",
        "capacity_population": "not_requested",
    }
    if receipt is not None:
        if receipt.get("memory_manifest_sha256") != manifest_sha256:
            raise VisualCapacityError("run_memory_manifest_sha256_mismatch")
        if receipt.get("memory_revision") != revision:
            raise VisualCapacityError("run_memory_revision_mismatch")
        pins["receipt"] = "matches"
        pins["receipt_sha256"] = receipt.get("_sha256")
        pins["capacity_control"] = receipt.get("capacity_control")
    exclusion = record.get("capacity_exclusion")
    if (
        isinstance(exclusion, Mapping)
        and exclusion.get("exclusion_status") == "applied"
    ):
        identity = exclusion.get("prepared_population_identity")
        if (
            not isinstance(identity, Mapping)
            or identity.get("memory_manifest_sha256") != manifest_sha256
        ):
            raise VisualCapacityError(f"capacity_population_memory_mismatch:{uid}")
        pins["capacity_population"] = "matches"
    return pins


def chosen_questions(
    record: Mapping[str, Any], questions: Sequence[str] | None
) -> list[str]:
    """The record's questions to draw, in the record's order.

    A question asked for that the record does not hold is refused by name: a
    misspelt ``--question`` must not end in a run that drew nothing.
    """
    held = list(record["questions"])
    if questions is None:
        return held
    unknown = sorted(set(questions) - set(held))
    if unknown:
        raise VisualCapacityError(f"question_not_in_record:{','.join(unknown)}")
    return [question for question in held if question in questions]


def source_pin(pin_path: Path | None, repo_root: Path) -> dict[str, Any]:
    """Compare a run's recorded source digests with the code that draws.

    ``pin_path`` is a JSON mapping of repository-relative path to SHA-256, or an
    object holding one as ``source_before`` (the form a run's invocation record
    keeps). Every file it lists is hashed under ``repo_root``; a file that
    differs or is missing is named. No pin supplied is stated, not assumed.
    """
    from knee.json_store import load_json

    if pin_path is None:
        return {"status": "not_supplied"}
    try:
        data = load_json(pin_path)
    except (OSError, ValueError) as error:
        raise VisualCapacityError("run_source_pin_unreadable") from error
    files = data.get("source_before", data) if isinstance(data, Mapping) else None
    if not isinstance(files, Mapping) or not files:
        raise VisualCapacityError("run_source_pin_invalid")
    differing, missing = [], []
    for relative, digest in sorted(files.items()):
        path = repo_root / str(relative)
        if not path.is_file():
            missing.append(relative)
        elif _sha256(path) != digest:
            differing.append(relative)
    return {
        "status": "differs" if differing or missing else "same",
        "pin": str(pin_path),
        "pin_sha256": _sha256(pin_path),
        "files": len(files),
        "differing": differing,
        "missing": missing,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_identity() -> dict[str, Any]:
    import knee

    package = Path(knee.__file__).resolve().parent
    names = (
        "diagnosis/squint_profiles.py",
        "diagnosis/squint_memory.py",
        "diagnosis/squint_support.py",
        "diagnosis/squint_leg.py",
        "diagnosis/squint_interfaces.py",
        "diagnosis/squint_locator.py",
        "diagnosis/squint_questions.py",
        "diagnosis/squint_location_check.py",
        "diagnosis/squint_pipeline.py",
        "encoding/product.py",
        "collapse/physical.py",
    )
    files = {
        name: _sha256(package / name) if (package / name).is_file() else None
        for name in names
    }
    head = None
    try:
        head = (
            subprocess.run(
                ["git", "-C", str(package), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
                timeout=20,
            ).stdout.strip()
            or None
        )
    except (OSError, subprocess.SubprocessError):
        head = None
    return {
        "knee_package": str(package),
        "repo_root": str(package.parent.parent),
        "git_head": head,
        "files_sha256": files,
        "script_sha256": _sha256(Path(__file__).resolve()),
    }


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").lower() or "sheet"


def _json_default(value: Any) -> Any:
    if isinstance(value, Fraction):
        return [value.numerator, value.denominator]
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (set, tuple)):
        return list(value)
    raise TypeError(f"not_json:{type(value).__name__}")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".part")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, default=_json_default)
            stream.write("\n")
        os.replace(name, path)
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise


def make_sheets(
    run: Path,
    memory_path: Path,
    root: Path,
    study_uids: Sequence[str],
    output: Path,
    *,
    run_label: str,
    io_workers: int = 2,
    questions: Sequence[str] | None = None,
    dpi: int = 120,
    run_source_pin: Path | None = None,
    require_same_source: bool = False,
) -> dict[str, Any]:
    """Write one sheet per question for each study, with a manifest beside them.

    Refuses, by name, a memory other than the run's, a run source pin the
    drawing code does not match when ``require_same_source`` is set, and any
    sheet directory that already holds a manifest (nothing is overwritten).
    """
    from knee.diagnosis.squint_memory import load_memory_snapshot
    from knee.json_store import load_json, resolve_json_path

    snapshot = load_memory_snapshot(memory_path)
    memory = snapshot.memory
    if memory is None:
        raise VisualCapacityError(snapshot.error_code or "memory_snapshot_invalid")
    cases_by_id = {case["case_id"]: case for case in memory["cases"]}
    products = {
        uid: {
            "path": identity.get("product_path"),
            "sha256": identity.get("product_sha256"),
        }
        for uid, identity in (memory.get("source_identities") or {}).items()
        if isinstance(identity, Mapping)
    }
    studies = studies_directory(run)
    receipt = run_receipt(studies)
    identity = _source_identity()
    pin = source_pin(run_source_pin, Path(identity["repo_root"]))
    if require_same_source and pin["status"] != "same":
        raise VisualCapacityError("run_source_differs_from_drawing_code")
    result: dict[str, Any] = {
        "schema": SCHEMA,
        "run": str(run.resolve()),
        "run_label": run_label,
        "memory_manifest": str(snapshot.path),
        "memory_manifest_sha256": snapshot.sha256,
        "memory_revision": memory.get("revision"),
        "source": identity,
        "run_source_pin": pin,
        "studies": {},
    }
    for study_uid in study_uids:
        directory = output / _slug(run_label) / study_uid
        if (directory / "manifest.json").exists():
            raise VisualCapacityError(f"sheets_already_exist:{directory}")
        record_path = resolve_json_path(studies / f"{study_uid}.json")
        record = load_json(record_path)
        if not isinstance(record, Mapping) or record.get("study_uid") != study_uid:
            raise VisualCapacityError("study_record_identity_mismatch")
        pins = check_memory_pins(record, receipt, memory, snapshot.sha256)
        chosen = chosen_questions(record, questions)
        plans = [question_plan(record, q, memory, cases_by_id) for q in chosen]
        for plan in plans:
            plan["study_status"] = record.get("study_status")
        images, territories, work = read_images(
            root, sheet_requests(plans), products, io_workers=io_workers
        )
        sheets: list[dict[str, Any]] = []
        record_sha = _sha256(record_path)
        source_line = (
            f"Sources: record {record_path.name} (sha256 {record_sha[:12]}…) · memory "
            f"{memory.get('revision')} (manifest sha256 {str(snapshot.sha256)[:12]}…; "
            f"run receipt {pins['receipt']}) · knee source "
            f"{str(identity.get('git_head'))[:10]} (run source pin: {pin['status']}) · "
            "drawn by scripts/squint_visual_capacity.py (development only)"
        )
        for index, plan in enumerate(plans, start=1):
            path = directory / f"{index:02d}-{_slug(plan['question'])}.png"
            drawn = draw_sheet(
                plan,
                images,
                territories,
                path,
                run_label=run_label,
                source_line=source_line,
                dpi=dpi,
            )
            sheets.append(
                {"plan": _plan_summary(plan), "drawn": drawn, "sha256": _sha256(path)}
            )
        study_manifest = {
            "schema": SCHEMA,
            "study_uid": study_uid,
            "study_status": record.get("study_status"),
            "record": str(record_path.resolve()),
            "record_sha256": record_sha,
            "memory_manifest_sha256": snapshot.sha256,
            "pins": pins,
            "run_source_pin": pin,
            "run_label": run_label,
            "image_reads": work,
            "territories": {
                "|".join(str(part) for part in key): {
                    k: v
                    for k, v in value.items()
                    if k not in ("roles", "object_share", "native_support")
                }
                for key, value in territories.items()
            },
            "sheets": sheets,
        }
        _write_json(directory / "manifest.json", study_manifest)
        result["studies"][study_uid] = {
            "directory": str(directory),
            "sheets": [sheet["drawn"]["path"] for sheet in sheets],
            "precedent_studies_read": len(work) - (1 if study_uid in work else 0),
        }
    return result


def _region_summary(region: Mapping[str, Any]) -> dict[str, Any]:
    """A located region without its territory's tile arrays (the panels keep those)."""
    kept = {k: v for k, v in region.items() if k != "territory"}
    territory = region.get("territory")
    if isinstance(territory, Mapping):
        kept["territory"] = {
            "origin": territory.get("origin"),
            "tile_window": territory.get("tile_window"),
            "support_digest": support_digest(territory),
        }
    return kept


def _panel_summary(panel: Mapping[str, Any]) -> dict[str, Any]:
    """What a panel counted over, as plain values: no tile array, no runtime mask."""
    territory = panel.get("territory")
    window = panel.get("window")
    return {
        "counted_by": panel.get("counted_by"),
        "origin": panel.get("origin"),
        "series_uid": panel.get("series_uid"),
        "view": panel.get("view"),
        "window": list(window) if window else None,
        "territory_code": panel.get("territory_code"),
        "tile_window": list(territory["tile_window"]) if territory else None,
        "territory": territory_summary(territory) if territory else None,
        "support_digest": panel.get("support_digest"),
        "recorded_native_bounds_rc": panel.get("recorded_native_bounds_rc"),
        "leg_map_sha256": panel.get("leg_map_sha256"),
        "fine_readings": panel.get("fine_readings"),
        "anchors": panel.get("anchors"),
    }


def _plan_summary(plan: Mapping[str, Any]) -> dict[str, Any]:
    def precedent(value):
        if not isinstance(value, Mapping):
            return None
        kept = {
            k: v for k, v in value.items() if k not in ("banks", "regions", "panels")
        }
        if "panels" in value:
            kept["panels"] = [_panel_summary(p) for p in value["panels"]]
            kept["regions"] = [_region_summary(r) for r in value["regions"]]
        return kept

    return {
        "question": plan["question"],
        "study_status": plan.get("study_status"),
        "finding": plan["finding"],
        "ranking": plan["ranking"],
        "study_label": plan["study_label"],
        "configuration": plan["configuration"],
        "supporting": plan["supporting"],
        "defining": [
            {
                "subject": s["subject"],
                "role": s["role"],
                "reading": s["reading"],
                "outcome": s["outcome"],
                "location_status": s["location_status"],
                "memory_cases_other_studies": s.get("memory_cases_other_studies"),
                "location_source": s["location_source"],
                "anchor": s["anchor"],
                "decision_scope": s["decision_scope"],
                "query_origins": s["query_origins"],
                "own_outline": s["own_outline"],
                "selection": s["selection"],
                "profile_versions": s["profile_versions"],
                "compared_banks": s["compared_banks"],
                "compared_roles": s["compared_roles"],
                "panel_scope": s["panel_scope"],
                "not_compared": s["not_compared"],
                "query_profile": {k: v for k, v in s["query"].items() if k != "banks"},
                "regions": [_region_summary(r) for r in s["regions"]],
                "panels": [_panel_summary(p) for p in s["panels"]],
                "normal": precedent(s["normal"]),
                "presentation": precedent(s["presentation"]),
            }
            for s in plan["defining"]
        ],
    }


EPILOG = """\
Writes <output>/<label>/<study uid>/NN-<question>.png and a manifest.json per
study, and <output>/<label>/run-manifest.json. Nothing is overwritten: a sheet
directory or a run manifest that already exists is refused by name.

Development only. It reads the run's records, the memory the run recalled from
and the native DICOM slices of the studies it draws; it never locates, recalls
or decides, and nothing in production imports it.

Example (from the repository root):
  PYTHONPATH=src .venv/bin/python scripts/squint_visual_capacity.py \\
      --run <run>/diagnostics --label <name> --memory <memory directory> \\
      --root <competition files> --study-uid <uid> \\
      --question "Medial Meniscus" --output <new directory>
"""


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").split("\n\n")[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--run",
        type=Path,
        required=True,
        help="run root (holding diagnostics/) or its diagnostics directory "
        "(holding receipt.json and studies/)",
    )
    parser.add_argument("--label", required=True, help="the run's name on every sheet")
    parser.add_argument(
        "--memory",
        type=Path,
        required=True,
        help="the memory the run recalled from: its directory or manifest.json",
    )
    parser.add_argument(
        "--root", type=Path, required=True, help="the competition's files (data/raw)"
    )
    parser.add_argument(
        "--study-uid",
        action="append",
        required=True,
        help="a study of the run to draw; repeat for several",
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="where the sheets are written"
    )
    parser.add_argument(
        "--question",
        action="append",
        default=None,
        help="draw only this question (as the record names it); repeat for "
        "several; default is every question the record holds",
    )
    parser.add_argument(
        "--io-workers",
        type=int,
        default=2,
        help="threads reading one study's series (default 2)",
    )
    parser.add_argument(
        "--dpi", type=int, default=120, help="resolution of the sheets (default 120)"
    )
    parser.add_argument(
        "--run-source-pin",
        type=Path,
        default=None,
        help=(
            "JSON of repository-relative paths to the SHA-256 the run was made "
            "with (or a run invocation record holding it as source_before)"
        ),
    )
    parser.add_argument(
        "--require-same-source",
        action="store_true",
        help="refuse when the drawing code differs from the run source pin",
    )
    args = parser.parse_args(argv)
    started = time.perf_counter()
    summary = args.output / _slug(args.label) / "run-manifest.json"
    try:
        if summary.exists():
            raise VisualCapacityError(f"sheets_already_exist:{summary}")
        result = make_sheets(
            args.run,
            args.memory,
            args.root,
            args.study_uid,
            args.output,
            run_label=args.label,
            io_workers=args.io_workers,
            questions=args.question,
            dpi=args.dpi,
            run_source_pin=args.run_source_pin,
            require_same_source=args.require_same_source,
        )
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2
    result["seconds"] = round(time.perf_counter() - started, 2)
    _write_json(summary, result)
    print(
        json.dumps(
            {
                "summary": str(summary),
                "seconds": result["seconds"],
                "studies": {
                    uid: len(row["sheets"]) for uid, row in result["studies"].items()
                },
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
