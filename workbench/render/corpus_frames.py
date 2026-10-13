"""Draw the corpus's shape as the study stage counted it and the writer saved it: what we are shown.

When the corpus opens, `knee.study.shape.corpus_shape` counts, from the tables alone, how many
studies and series each split holds, which view triples the labeled studies carry and how widely,
how the twelve labels are distributed over the training studies, and how long the reports run. The
one command saves that count in the receipt as `receipt["corpus"]`
(`workbench.measure.object_analysis.corpus_record`). This arranges it into a picture.

Every number on the picture is a count the study stage made: nothing is recounted, summed,
normalised or compared. A count of labels is information about the corpus and is read by no stage,
so the picture names each label code as the table gives it and never as a verdict. The saved record
is reconstituted as the stage's own `CorpusShape` and checked against the stage's vocabularies
(`LABEL_CODES`, `REPORT_CODES`, `LABELS`): a saved word the stage does not say is refused rather
than drawn.

The corpus is a fact of the RUN and not of one study, so `draw` takes the parsed receipt and the
output directory, not a run directory and a study. It cannot arrange an input it was not given or
cannot read, and then it RETURNS a manifest whose `refusal` is a named code and whose `why` says it
in words; it does not raise. Matplotlib is supplied per run and is imported after every refusal this
module can make, so `saved_shape` is importable and testable in the ordinary environment.
"""

import argparse
import json
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType

import numpy as np

from knee.study.codes import LABEL_CODES
from knee.study.shape import REPORT_CODES, CorpusShape
from knee.study.tables import LABELS
from workbench.render._out import PROJECT

SCHEMA = "corpus-frames-v1"
IMAGE = "corpus.png"

#: The fields the saved record must carry, each the field of the same name on `CorpusShape`.
FIELDS: tuple[str, ...] = (
    "studies",
    "series",
    "orphan_series",
    "labeled",
    "views",
    "views_per_labeled_study",
    "labels",
    "reports",
    "report_lengths",
)

#: One colour per label code the table can carry. `unrecognized` is fuchsia, the colour this layer
#: gives to a reading that is not one, and `not_given` is grey: neither is a count of anything read.
LABEL_COLOURS: Mapping[str, str] = {
    "1": "#f97316",
    "0": "#3b82f6",
    "not_given": "#9ca3af",
    "unrecognized": "#c026d3",
}
FALLBACK_COLOUR = "#111827"
STUDY_COLOUR = "#2563eb"
SERIES_COLOUR = "#f59e0b"

#: A segment of a label bar carries its count when it is at least this share of the longest bar:
#: a layout rule for the printed numbers, never a reading of the counts.
ANNOTATE_SHARE = 0.035


@dataclass(frozen=True, slots=True)
class Refusal:
    """A saved corpus shape this renderer cannot arrange: a named code, and the reason in words."""

    code: str
    why: str


def whole(value: object) -> bool:
    """A whole, non-negative number. A bool is not one, though Python counts it as an int."""
    return type(value) is int and value >= 0


def saved_counts(
    value: object, where: str, vocabulary: tuple[str, ...] | None = None
) -> dict[str, int] | Refusal:
    """A saved mapping of names to whole counts, its names checked against `vocabulary` when given."""
    if not isinstance(value, dict) or not all(
        type(name) is str and whole(count) for name, count in value.items()
    ):
        return Refusal(
            f"corpus_field_invalid:{where}",
            f"`{where}` is not a mapping of names to whole counts",
        )
    if vocabulary is not None:
        for name in value:
            if name not in vocabulary:
                return Refusal(
                    f"corpus_code_unknown:{where}:{name}",
                    f"`{where}` holds `{name}`, which the study stage does not say",
                )
    return dict(value)


def saved_views(
    value: object,
) -> tuple[tuple[tuple[str, str, str], int, int], ...] | Refusal:
    """The saved view triples with their series and study counts, in the order the stage saved them."""
    invalid = Refusal(
        "corpus_field_invalid:views",
        "`views` is not a list of (plane, fluid-sensitive, fat-suppressed) with two whole counts",
    )
    if not isinstance(value, list):
        return invalid
    views = []
    for item in value:
        if not (
            isinstance(item, dict)
            and isinstance(item.get("view"), list)
            and len(item["view"]) == 3
            and all(type(part) is str for part in item["view"])
            and whole(item.get("series"))
            and whole(item.get("studies"))
        ):
            return invalid
        plane, fluid, fat = item["view"]
        views.append(((plane, fluid, fat), item["series"], item["studies"]))
    return tuple(views)


def saved_labels(value: object) -> dict[str, dict[str, int]] | Refusal:
    """The saved label counts per finding, each finding and each code checked against the stage's own."""
    if not isinstance(value, dict):
        return Refusal("corpus_field_invalid:labels", "`labels` is not a mapping")
    labels = {}
    for finding, counts in value.items():
        if finding not in LABELS:
            return Refusal(
                f"corpus_finding_unknown:{finding}",
                f"`labels` holds `{finding}`, which is not one of the table's findings",
            )
        checked = saved_counts(counts, f"labels.{finding}", LABEL_CODES)
        if isinstance(checked, Refusal):
            return checked
        labels[finding] = checked
    return labels


def saved_shape(corpus: object) -> CorpusShape | Refusal:
    """Reconstitute the study stage's `CorpusShape` from a saved record, or name why it cannot be.

    Total: a record that is not an object, lacks a field, holds a count that is not a whole number
    or a word the stage does not say, or names splits in one mapping that the other lacks, is a
    `Refusal` with a code of its own, so the remedy for each stays distinct. Nothing is recounted,
    and the order of every saved mapping and list is kept.
    """
    if not isinstance(corpus, dict):
        return Refusal(
            "corpus_not_a_record", "the saved corpus shape is not a JSON object"
        )
    for name in FIELDS:
        if name not in corpus:
            return Refusal(
                f"corpus_field_missing:{name}", f"the saved corpus lacks `{name}`"
            )
    studies = saved_counts(corpus["studies"], "studies")
    if isinstance(studies, Refusal):
        return studies
    series = saved_counts(corpus["series"], "series")
    if isinstance(series, Refusal):
        return series
    reports = saved_counts(corpus["reports"], "reports", REPORT_CODES)
    if isinstance(reports, Refusal):
        return reports
    per_study = saved_counts(
        corpus["views_per_labeled_study"], "views_per_labeled_study"
    )
    if isinstance(per_study, Refusal):
        return per_study
    views = saved_views(corpus["views"])
    if isinstance(views, Refusal):
        return views
    labels = saved_labels(corpus["labels"])
    if isinstance(labels, Refusal):
        return labels
    if set(studies) != set(series):
        return Refusal(
            "corpus_splits_disagree",
            "`studies` and `series` name different splits, though the stage counts both over the same studies",
        )
    if not all(whole(corpus[name]) for name in ("orphan_series", "labeled")):
        return Refusal(
            "corpus_field_invalid:counts",
            "`orphan_series` and `labeled` are not whole counts",
        )
    if not all(name.isdigit() for name in per_study):
        return Refusal(
            "corpus_field_invalid:views_per_labeled_study",
            "a key of `views_per_labeled_study` is not a whole number of views",
        )
    lengths = corpus["report_lengths"]
    if (
        not isinstance(lengths, list)
        or len(lengths) not in (0, 3)
        or not all(whole(length) for length in lengths)
    ):
        return Refusal(
            "corpus_field_invalid:report_lengths",
            "`report_lengths` is not empty or the shortest, median and longest whole lengths",
        )
    return CorpusShape(
        studies=MappingProxyType(studies),
        series=MappingProxyType(series),
        orphan_series=corpus["orphan_series"],
        labeled=corpus["labeled"],
        views=views,
        views_per_labeled_study=MappingProxyType(
            {int(name): count for name, count in per_study.items()}
        ),
        labels=MappingProxyType(
            {finding: MappingProxyType(counts) for finding, counts in labels.items()}
        ),
        reports=MappingProxyType(reports),
        report_lengths=(lengths[0], lengths[1], lengths[2]) if lengths else (),
    )


def view_name(view: tuple[str, str, str]) -> str:
    """A view triple as the table gives it, in words that keep each part's own name."""
    plane, fluid, fat = view
    return f"{plane} · fluid-sensitive {fluid} · fat-suppressed {fat}"


def refused(refusal: Refusal) -> dict:
    """The manifest of a drawing that was not made: the named code and the reason, nothing drawn."""
    return {"schema": SCHEMA, "refusal": refusal.code, "why": refusal.why}


def draw_splits(axis, shape: CorpusShape) -> None:
    """Studies and series per split, as the stage counted them (orphan series are not among them)."""
    splits = list(shape.studies)
    place = np.arange(len(splits))
    width = 0.38
    studies = axis.bar(
        place - width / 2,
        [shape.studies[name] for name in splits],
        width,
        color=STUDY_COLOUR,
        label="studies",
    )
    series = axis.bar(
        place + width / 2,
        [shape.series[name] for name in splits],
        width,
        color=SERIES_COLOUR,
        label="series",
    )
    axis.bar_label(studies, padding=2, fontsize=8)
    axis.bar_label(series, padding=2, fontsize=8)
    axis.set_xticks(place, splits)
    axis.legend(fontsize=7)
    axis.set_title("studies and series per split", fontsize=9)


def draw_singles(axis, shape: CorpusShape) -> None:
    """The two counts that belong to no split: orphan series and labeled studies."""
    bars = axis.bar(
        [
            "series whose study is\nin neither table",
            "training studies with\nall twelve labels given",
        ],
        [shape.orphan_series, shape.labeled],
        color=["#6b7280", STUDY_COLOUR],
    )
    axis.bar_label(bars, padding=2, fontsize=8)
    axis.tick_params(axis="x", labelsize=7)
    axis.set_title("orphan series and labeled studies", fontsize=9)


def draw_views_per_study(axis, shape: CorpusShape) -> None:
    """How many distinct view triples a labeled study carries, to how many labeled studies."""
    distinct = sorted(shape.views_per_labeled_study)
    if not distinct:
        axis.set_axis_off()
        axis.text(0.5, 0.5, "no labeled study", ha="center", va="center")
    else:
        bars = axis.bar(
            [str(count) for count in distinct],
            [shape.views_per_labeled_study[count] for count in distinct],
            color=STUDY_COLOUR,
        )
        axis.bar_label(bars, padding=2, fontsize=8)
        axis.set_xlabel("distinct views a labeled study carries", fontsize=8)
        axis.set_ylabel("labeled studies", fontsize=8)
    axis.set_title("views per labeled study", fontsize=9)


def draw_views(axis, shape: CorpusShape) -> None:
    """Every view triple the labeled studies carry: its series and the labeled studies carrying it."""
    if not shape.views:
        axis.set_axis_off()
        axis.text(0.5, 0.5, "no labeled study carries a view", ha="center", va="center")
        axis.set_title("views over the labeled studies", fontsize=9)
        return
    place = np.arange(len(shape.views))
    height = 0.38
    series = axis.barh(
        place - height / 2,
        [count for _, count, _ in shape.views],
        height,
        color=SERIES_COLOUR,
        label="series carrying the view",
    )
    studies = axis.barh(
        place + height / 2,
        [count for _, _, count in shape.views],
        height,
        color=STUDY_COLOUR,
        label="labeled studies carrying it",
    )
    axis.bar_label(series, padding=2, fontsize=7)
    axis.bar_label(studies, padding=2, fontsize=7)
    axis.set_yticks(place, [view_name(view) for view, _, _ in shape.views], fontsize=7)
    axis.invert_yaxis()
    axis.legend(fontsize=7, loc="lower right")
    axis.set_title(
        "views over the labeled studies, in the order the stage saved them", fontsize=9
    )


def draw_reports(axis, shape: CorpusShape) -> None:
    """What the report column holds for the training studies, and how long the present reports run."""
    codes = [code for code in REPORT_CODES if code in shape.reports]
    bars = axis.bar(codes, [shape.reports[code] for code in codes], color="#0d9488")
    axis.bar_label(bars, padding=2, fontsize=8)
    if shape.report_lengths:
        shortest, median, longest = shape.report_lengths
        lengths = f"present reports, in characters:\nshortest {shortest} · median {median} · longest {longest}"
    else:
        lengths = "no report text is present, so no length is read"
    axis.set_xlabel(lengths, fontsize=8)
    axis.set_title("the report column (training studies)", fontsize=9)


def draw_labels(axis, shape: CorpusShape) -> list[str]:
    """Each finding's label codes over the training studies, one stacked bar per finding.

    The codes are the table's own, `1` and `0` as given, kept apart from a blank (`not_given`) and
    from a value the stage did not recognise. Returns the findings the saved record held, in the
    table's order; a finding it lacks is left out and named in the title, never drawn as empty.
    """
    findings = [finding for finding in LABELS if finding in shape.labels]
    longest = max(
        (sum(shape.labels[finding].values()) for finding in findings), default=0
    )
    for row, finding in enumerate(findings):
        left = 0
        for code in LABEL_CODES:
            if code not in shape.labels[finding]:
                continue
            count = shape.labels[finding][code]
            axis.barh(
                row,
                count,
                left=left,
                color=LABEL_COLOURS.get(code, FALLBACK_COLOUR),
                label=code if row == 0 else None,
            )
            if longest and count / longest >= ANNOTATE_SHARE:
                axis.text(
                    left + count / 2,
                    row,
                    str(count),
                    ha="center",
                    va="center",
                    fontsize=7,
                    color="white",
                )
            left += count
        # Every saved count, exactly, beside its bar: the small segments cannot be read from the bar.
        axis.text(
            longest * 1.01,
            row,
            " · ".join(
                f"{code} {shape.labels[finding][code]}"
                for code in LABEL_CODES
                if code in shape.labels[finding]
            ),
            ha="left",
            va="center",
            fontsize=7,
        )
    axis.set_xlim(0, longest * 1.4)
    axis.set_yticks(range(len(findings)), findings, fontsize=8)
    axis.invert_yaxis()
    axis.set_xlabel("training studies", fontsize=8)
    absent = [finding for finding in LABELS if finding not in shape.labels]
    axis.set_title(
        "label codes per finding over the training studies, as the table gives them"
        + (f"\nnot saved: {', '.join(absent)}" if absent else ""),
        fontsize=9,
    )
    axis.legend(
        fontsize=7,
        ncols=len(LABEL_CODES),
        loc="upper center",
        bbox_to_anchor=(0.5, -0.12),
    )
    return findings


def draw(receipt: object, out: Path) -> dict:
    """Draw the saved corpus shape from a parsed receipt and return its manifest.

    A drawing of the RUN: `receipt` is the parsed `receipt.json` and `out` the directory the picture
    and its manifest go in, which must lie under the project's private data directory. Total: a
    receipt that is not a mapping, carries no corpus or carries one this module cannot read, an
    output outside `data/`, or a missing Matplotlib, each returns the manifest of a drawing that
    was not made, with a named `refusal` and its reason in `why`, and nothing is raised.
    """
    target = out.resolve()
    if not target.is_relative_to((PROJECT / "data").resolve()):
        return refused(
            Refusal(
                "out_outside_data",
                "out must be under the project's private data directory",
            )
        )
    if not isinstance(receipt, Mapping):
        return refused(
            Refusal("receipt_not_a_mapping", "the receipt is not a JSON object")
        )
    if "corpus" not in receipt:
        return refused(
            Refusal(
                "corpus_not_saved",
                "this run's receipt carries no corpus shape: its writer saved none",
            )
        )
    shape = saved_shape(receipt["corpus"])
    if isinstance(shape, Refusal):
        return refused(shape)
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        return refused(
            Refusal(
                "matplotlib_unavailable",
                "Matplotlib is supplied per run and is not importable here",
            )
        )

    target.mkdir(parents=True, exist_ok=True)
    figure = plt.figure(figsize=(18, 14), layout="constrained")
    grid = figure.add_gridspec(3, 6)
    draw_splits(figure.add_subplot(grid[0, 0:2]), shape)
    draw_singles(figure.add_subplot(grid[0, 2:4]), shape)
    draw_views_per_study(figure.add_subplot(grid[0, 4:6]), shape)
    draw_views(figure.add_subplot(grid[1, 0:4]), shape)
    draw_reports(figure.add_subplot(grid[1, 4:6]), shape)
    findings = draw_labels(figure.add_subplot(grid[2, :]), shape)
    figure.suptitle(
        "The corpus's shape, as the study stage counted it when the corpus opened\n"
        "every number is a saved count; none is recounted here, and no stage reads a label count",
        fontsize=12,
    )
    figure.savefig(target / IMAGE, dpi=110)
    plt.close(figure)
    manifest = {
        "schema": SCHEMA,
        "image": IMAGE,
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "corpus_sha256": sha256(
            json.dumps(receipt["corpus"], sort_keys=True, default=str).encode()
        ).hexdigest(),
        "panels": [
            "splits",
            "orphans_and_labeled",
            "views_per_labeled_study",
            "views",
            "reports",
            "labels",
        ],
        "splits": list(shape.studies),
        "views": len(shape.views),
        "findings": findings,
        "label_codes": list(LABEL_CODES),
        "note": (
            "Every value is a count the study stage saved when the corpus opened. A label count "
            "is information about the corpus and is read by no stage; no code is named a verdict."
        ),
    }
    (target / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "run", type=Path, help="the saved run directory with receipt.json"
    )
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = json.loads((args.run / "receipt.json").read_text())
    except (OSError, ValueError) as unreadable:
        parser.error(f"the run's receipt cannot be read: {unreadable}")
    manifest = draw(receipt, args.out)
    if "refusal" in manifest:
        parser.error(f"{manifest['refusal']}: {manifest['why']}")
    target = args.out.resolve()
    print(
        json.dumps(
            {
                "image": str(target / manifest["image"]),
                "manifest": str(target / "manifest.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
