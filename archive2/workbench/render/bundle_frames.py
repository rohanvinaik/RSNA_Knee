"""Draw each object's bundle, its profile as banks of counts, from one saved production study record.

Task 6.7 of `openspec/changes/every-stage-renders`, the picture of the vectors stage. A profile is
row counts over named banks, and the stage carries a bank it cannot write as `unavailable` with a
reason and no rows -- never as rows of zero, because a zero count asserts that a reading was made
and found nothing. This renderer keeps that visible: an unavailable bank is drawn grey with the
stage's own reason and no count cells, so it cannot be read as a column of zeros.

It reads only `record["vectors"]` from the saved receipt, through `knee.pictures.vectors`, and it
ARRANGES. Every number on the picture is a count the stage saved: nothing is recounted, summed,
normalised or compared, no object is named for what it is, and no two profiles are judged alike.
A saved record that disagrees with the stage's own vocabulary is refused rather than drawn, because
a drawn corruption looks like evidence.

One picture per study: a heading per series saying what the stage returned for it, then one table
per object in a grid. Matplotlib is supplied per run and is imported inside `draw`, so
`saved_reading` and `table_lines` are importable and testable in the ordinary environment.
"""

import argparse
import json
from hashlib import sha256
from math import ceil, floor, sqrt
from pathlib import Path
from textwrap import fill, wrap
from typing import Any

from knee.pictures import vectors
from knee.vectors.bundles import (
    BANK_STATUS,
    CODES,
    SUBJECT_KIND,
    Bank,
    BundlesReading,
    ObjectProfile,
)

#: Object tables per row of a series' grid, and the size of one table. These are the picture's
#: layout and no more: they say nothing about the study. Every series uses the same grid width, so
#: a table is the same size whether a series has two objects or twenty.
COLUMNS = 6
TABLE_WIDTH_INCHES = 3.1
LINE_INCHES = 0.105
TITLE_INCHES = 0.32
#: A series' heading is its identifier and one line per line `heading_lines` returns: this much
#: besides, and this much for each line.
HEADING_INCHES = 0.35
HEADING_LINE_INCHES = 0.145
LABEL_WIDTH = 38
REASON_WIDTH = 38

#: The drawing's resolution is lowered, never the content cut, when a study has many objects: an
#: image may not exceed this many pixels in total or on one side.
MAX_DPI = 160
MIN_DPI = 20
MAX_PIXELS = 40_000_000
MAX_SIDE_PIXELS = 60_000

#: One fill per kind of line. An unavailable bank is the grey one, header and reason alike.
FILLS = {
    "written": "#dbeafe",
    "unavailable": "#9ca3af",
    "row": "#ffffff",
    "reason": "#e5e7eb",
}


def saved_field(saved: object, key: str) -> object:
    """One field of a saved mapping; a record that lacks it disagrees with this renderer."""
    if not isinstance(saved, dict) or key not in saved:
        raise ValueError(f"saved_vectors_field_missing:{key}")
    return saved[key]


def saved_text(saved: object, key: str) -> str:
    """A saved string. Saved values come from JSON, so the exact type is the honest test."""
    value = saved_field(saved, key)
    if type(value) is not str:
        raise ValueError(f"saved_vectors_field_not_text:{key}")
    return value


def saved_count(saved: object, key: str) -> int:
    """A whole, non-negative number; a bool is not one, though Python counts it as an int."""
    value = saved_field(saved, key)
    if type(value) is not int or value < 0:
        raise ValueError(f"saved_vectors_field_not_a_count:{key}")
    return value


def saved_bank(saved: object) -> Bank:
    """Reconstitute one bank from its saved entry, refusing a status its rows contradict.

    An unavailable bank holding rows would draw a reading that was never made, and a written bank
    holding none would draw an absence as a bank: either means the record and the stage disagree.
    """
    name = saved_text(saved, "name")
    status = saved_text(saved, "status")
    if status not in BANK_STATUS:
        raise ValueError(f"saved_bank_status_unknown:{status}")
    rows = saved_field(saved, "rows")
    if not isinstance(rows, dict) or not all(
        isinstance(row, str) and type(count) is int and count >= 0
        for row, count in rows.items()
    ):
        raise ValueError(f"saved_bank_rows_invalid:{name}")
    if status == "unavailable" and rows:
        raise ValueError(f"saved_bank_unavailable_with_rows:{name}")
    if status == "written" and not rows:
        raise ValueError(f"saved_bank_written_without_rows:{name}")
    return Bank(
        name=name,
        source_stage=saved_text(saved, "source_stage"),
        status=status,
        rows=dict(rows),
        why=saved_text(saved, "why"),
    )


def saved_profile(saved: object) -> ObjectProfile:
    banks = saved_field(saved, "banks")
    if type(banks) is not list:
        raise ValueError("saved_vectors_banks_not_a_list")
    return ObjectProfile(
        index=saved_count(saved, "index"),
        places=saved_count(saved, "places"),
        banks=tuple(saved_bank(bank) for bank in banks),
    )


def saved_number(value: object) -> float | None:
    """A saved int or float as a float; None for anything else, a bool included.

    Saved values come from JSON, so a bool is the one value Python would count as a number and
    the record never means as one.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def saved_gap(saved: object) -> tuple[str, float | None]:
    """One other acquisition's saved gap fraction as (its series uid, a fraction or None).

    None is a fraction the stage could not read and stays None. The stage's `gap_fraction` returns
    a value in [0, 1), so any other number, a bool or a NaN is a record that disagrees with it.
    """
    uid = saved_text(saved, "series_uid")
    fraction = saved_field(saved, "gap_fraction")
    if fraction is None:
        return uid, None
    number = saved_number(fraction)
    if number is None:
        raise ValueError(f"saved_slab_gap_not_a_number:{uid}")
    if not 0.0 <= number < 1.0:
        raise ValueError(f"saved_slab_gap_out_of_range:{uid}")
    return uid, number


def saved_slab_gaps(saved: object) -> tuple[tuple[str, float | None], ...]:
    """Every other acquisition's saved gap fraction, in the order the stage saved them."""
    gaps = saved_field(saved, "slab_gaps")
    if type(gaps) is not list:
        raise ValueError("saved_vectors_slab_gaps_not_a_list")
    return tuple(saved_gap(gap) for gap in gaps)


def saved_reading(record: dict) -> BundlesReading:
    """Reconstitute the stage's returned reading from one saved series record, without deciding.

    Every saved field is checked against the vocabulary the stage owns rather than trusted: a
    record without the stage, a code outside `CODES`, a status outside `BANK_STATUS`, a subject
    kind the stage does not write, or a status its rows contradict means the record and this
    renderer disagree, and that is reported rather than drawn. The backend the stage was asked for
    and the gap fractions it returned are read from the record like every other field: a record
    that lacks them is refused, and is never handed the stage's defaults, which would state a
    backend and a set of gaps the run never recorded. The backend is any text the stage recorded,
    because the stage records a request it refused as faithfully as one it ran.
    """
    if "vectors" not in record:
        raise ValueError("missing_saved_vectors")
    saved = record["vectors"]
    code = saved_text(saved, "code")
    if code not in CODES:
        raise ValueError(f"saved_vectors_code_unknown:{code}")
    if saved_text(saved, "subject_kind") != SUBJECT_KIND:
        raise ValueError("saved_vectors_subject_kind_mismatch")
    profiles = saved_field(saved, "profiles")
    if type(profiles) is not list:
        raise ValueError("saved_vectors_profiles_not_a_list")
    return BundlesReading(
        code=code,
        why=saved_text(saved, "why"),
        subject_kind=SUBJECT_KIND,
        planes_read=saved_count(saved, "planes_read"),
        profiles=tuple(saved_profile(profile) for profile in profiles),
        backend=saved_text(saved, "backend"),
        slab_gaps=saved_slab_gaps(saved),
    )


def table_lines(profile: vectors.ProfilePanel) -> list[tuple[str, str, str]]:
    """Every line of one profile's table as (label, count text, kind), from the saved values alone.

    A bank is a header naming it and its source stage beside its status; a name too long for the
    column, such as one carrying a whole series identifier, continues on the lines below with the
    same kind, so no name is ever cut off. A written bank then lists its rows with the stage's own
    counts; an unavailable bank lists its saved reason in their place and no count at all. The
    kinds are `written`, `unavailable`, `row` and `reason`.
    """
    lines: list[tuple[str, str, str]] = []
    for bank in profile.banks:
        heading = wrap(f"{bank.name}  [{bank.source_stage}]", width=LABEL_WIDTH) or [""]
        lines.append((heading[0], bank.status, bank.status))
        lines.extend((rest, "", bank.status) for rest in heading[1:])
        if bank.status == "unavailable":
            lines.extend(
                (reason, "", "reason")
                for reason in wrap(bank.why, width=REASON_WIDTH) or [""]
            )
        else:
            lines.extend((f"  {name}", str(count), "row") for name, count in bank.rows)
    return lines


def gap_text(fraction: float | None) -> str:
    """One saved gap fraction as text; None is a fraction the stage could not read, never a zero."""
    return "not read" if fraction is None else f"{fraction:.4g}"


def heading_lines(frame: vectors.BundlesPanels) -> list[str]:
    """The lines of a series' heading after its identifier, every one a value the stage saved.

    What the stage returned and what the profiles are keyed on, the backend the through-plane
    banks were REQUESTED to use, and the gap fraction of every other acquisition's own stack, one
    per line in the stage's order. A gap fraction belongs to an acquisition and not to any
    object's places, so it is stated here and never inside a table.
    """
    lines = [
        *f"stage: {frame.code} - {fill(frame.why, width=170)}".splitlines(),
        (
            f"keyed on: {frame.subject_kind}; planes read: {frame.planes_read}; "
            f"objects: {len(frame.profiles)}"
        ),
        f"through-plane banks requested on backend: {frame.backend}",
    ]
    if frame.slab_gaps:
        lines.append("gap fraction of each other acquisition's own stack, as saved:")
        lines.extend(f"    {uid}: {gap_text(gap)}" for uid, gap in frame.slab_gaps)
    else:
        lines.append(
            "gap fraction of each other acquisition's own stack: none saved "
            "(no other acquisition was read)"
        )
    return lines


def heading_inches(frame: vectors.BundlesPanels) -> float:
    """How tall a series' heading is: its identifier and `heading_lines`, a fixed height per line."""
    return HEADING_INCHES + HEADING_LINE_INCHES * (1 + len(heading_lines(frame)))


def series_inches(frame: vectors.BundlesPanels) -> float:
    """How tall a series' section is: its heading, then a grid of equally tall tables."""
    if not frame.profiles:
        return heading_inches(frame)
    lines = max(len(table_lines(profile)) for profile in frame.profiles)
    rows = ceil(len(frame.profiles) / COLUMNS)
    return heading_inches(frame) + rows * (lines * LINE_INCHES + TITLE_INCHES)


def resolution(width: float, height: float) -> int:
    """The dpi that keeps the whole picture inside the pixel limits, at most MAX_DPI."""
    by_area = floor(sqrt(MAX_PIXELS / (width * height)))
    by_side = floor(MAX_SIDE_PIXELS / max(width, height))
    return max(MIN_DPI, min(MAX_DPI, by_area, by_side))


def draw_profile(axis: Any, profile: vectors.ProfilePanel, tallest: int) -> None:
    """One object's table: the stage's banks, counts and reasons, top-aligned at a shared scale."""
    lines = table_lines(profile)
    axis.set_axis_off()
    axis.set_title(
        f"object {profile.index}: {profile.places} places",
        fontsize=7,
        loc="left",
        pad=2,
    )
    if not lines:
        axis.text(
            0.02, 0.98, "no banks", transform=axis.transAxes, va="top", fontsize=6
        )
        return
    height = len(lines) / tallest
    table = axis.table(
        cellText=[[label, text] for label, text, _ in lines],
        cellColours=[[FILLS.get(kind, FILLS["row"])] * 2 for _, _, kind in lines],
        colWidths=[0.72, 0.28],
        cellLoc="left",
        bbox=[0.0, 1.0 - height, 1.0, height],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(5.5)
    for (row, _), cell in table.get_celld().items():
        cell.set_linewidth(0.3)
        if lines[row][2] in BANK_STATUS:
            cell.set_text_props(weight="bold")


def draw_series(
    subfigure: Any, uid: str, frame: vectors.BundlesPanels, inches: float
) -> None:
    """A series' section: what the stage returned for it, then one table per object."""
    subfigure.suptitle(
        "\n".join([uid, *heading_lines(frame)]),
        fontsize=8,
        x=0.004,
        y=0.995,
        ha="left",
        va="top",
    )
    if not frame.profiles:
        return
    columns = COLUMNS
    rows = ceil(len(frame.profiles) / columns)
    subfigure.subplots_adjust(
        left=0.005,
        right=0.995,
        bottom=0.003,
        top=1.0 - heading_inches(frame) / inches,
        wspace=0.08,
        hspace=0.12,
    )
    axes = subfigure.subplots(rows, columns, squeeze=False)
    tallest = max(len(table_lines(profile)) for profile in frame.profiles)
    for position in range(rows * columns):
        axis = axes[position // columns][position % columns]
        if position < len(frame.profiles):
            draw_profile(axis, frame.profiles[position], tallest)
        else:
            axis.set_axis_off()


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run and return its manifest.

    The one entry a caller uses, so the single command can draw every stage without knowing each
    renderer's argument spelling. `main()` is a thin wrapper over it, so the hand-typed command
    and the joined run draw the same thing from the same code.

    Every refusal is made BEFORE Matplotlib is imported: the output must lie under the project's
    private data directory, the receipt must hold records for this study, and every record must
    carry the stage and agree with its vocabulary. Matplotlib is supplied per run and is never a
    production dependency, so it is imported only once there is something valid to draw.
    """
    data_root = Path(__file__).resolve().parents[2] / "data"
    output = out.resolve()
    if not output.is_relative_to(data_root.resolve()):
        raise ValueError("out must be under the project's private data directory")
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    saved = receipt.get("records") if type(receipt) is dict else None
    if type(saved) is not list:
        raise ValueError("missing_saved_records")
    records = [
        record
        for record in saved
        if isinstance(record, dict) and record.get("study_uid") == study_uid
    ]
    if not records:
        raise ValueError("no saved records for this study")
    series = [
        (saved_text(record, "series_uid"), vectors.panels(saved_reading(record)))
        for record in records
    ]
    if vectors.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:vectors")

    import matplotlib.pyplot as plt

    heights = [series_inches(frame) for _, frame in series]
    width = TABLE_WIDTH_INCHES * COLUMNS
    dpi = resolution(width, sum(heights))
    output.mkdir(parents=True, exist_ok=True)
    figure = plt.figure(figsize=(width, sum(heights)))
    subfigures = figure.subfigures(
        len(series), 1, height_ratios=heights, hspace=0.0, squeeze=False
    )
    for (uid, frame), inches, subfigure in zip(
        series, heights, subfigures[:, 0], strict=True
    ):
        draw_series(subfigure, uid, frame, inches)
    figure.savefig(output / "series.png", dpi=dpi)
    plt.close(figure)

    manifest = {
        "schema": "bundle-frames-v1",
        "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": {
            "vectors": sha256(Path(vectors.__file__).read_bytes()).hexdigest()
        },
        "study_uid": study_uid,
        "image": "series.png",
        "dpi": dpi,
        "frame_kind": "selected native plane, one table per object",
        "series": [
            {
                "series_uid": uid,
                "stage_code": frame.code,
                "subject_kind": frame.subject_kind,
                "planes_read": frame.planes_read,
                "backend_requested": frame.backend,
                "slab_gaps": [
                    {"series_uid": other, "gap_fraction": gap}
                    for other, gap in frame.slab_gaps
                ],
                "profiles": [
                    {
                        "index": profile.index,
                        "places": profile.places,
                        "banks": [
                            {"name": bank.name, "status": bank.status}
                            for bank in profile.banks
                        ],
                    }
                    for profile in frame.profiles
                ],
            }
            for uid, frame in series
        ],
        "note": (
            "Every count is a count the vectors stage saved; none is recomputed here. A bank "
            "the stage could not write is drawn grey with its reason and no count cells, and "
            "is never rows of zero."
        ),
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
