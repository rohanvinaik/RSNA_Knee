"""The route a study takes, end to end.

This is an ORCHESTRATION in the thesis's sense (SS13.7): it moves values between stages and decides
nothing itself. Every judgement belongs to the stage it came from.

It is the whole of Figure 8's line, in order, and it is honest about its own state: a stage that is
built runs and reports what it read; a stage that is not built reports `not_built` and the route
carries on. So this file is readable as the project's table of contents, and `just run` over the
corpus says exactly how far the pipeline reaches today.

The impure edge stays thin (SS13.7: "reading a movie, writing the output, drawing pictures"). This
module reads studies and returns values. It writes nothing and draws nothing; `knee.pictures` is a
separate layer that takes a finished run and can be switched off without the run noticing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from knee.collapse.regime import RegimeKey, read_regime
from knee.study.corpus import Corpus, Study, read_study
from knee.study.series import read_series

# Figure 8's line, in order, with the state of each stage. A stage is "built" when it runs over a
# real study through Chapter 1's entry point -- never when its unit tests pass. That distinction is
# not pedantry: the noise law passed every unit test and then concurred on 4 of 336 real series.
ROUTE: tuple[tuple[str, str], ...] = (
    ("study", "built"),
    ("collapse", "partly"),
    ("loop", "not_built"),
    ("candidates", "not_built"),
    ("vectors", "not_built"),
    ("cleanup", "not_built"),
    ("assignment", "not_built"),
    ("every_object", "not_built"),
    ("output", "not_built"),
)


@dataclass(frozen=True, slots=True)
class SeriesRun:
    """What the pipeline read from one series, and what it could not read.

    `regime` is the series' regime key when the collapse could read one, else None with `why`
    saying which named code stopped it. A reading not made is never a reading of zero.
    """

    series_uid: str
    view: tuple[str, str, str]
    stack: tuple[str, ...]
    regime: RegimeKey | None
    why: str


@dataclass(frozen=True, slots=True)
class StudyRun:
    """One study's whole route, as far as the pipeline reaches.

    `reached` is the last stage that did anything; `series` holds one `SeriesRun` each, in the
    table's order. Stages beyond `reached` are not failures -- they are unbuilt, and the route
    names them so that what is missing is as legible as what is present.
    """

    uid: str
    split: str
    series: tuple[SeriesRun, ...] = field(default_factory=tuple)
    reached: str = "study"


def run_study(corpus: Corpus, uid: str) -> StudyRun:
    """Walk one study down Figure 8's line, as far as the build reaches.

    Chapter 1 reads the study whole at stored fidelity. The collapse then reads each series' regime
    key -- the cheap whole-field readings that say what a series IS before any expensive work runs.
    Beyond that the route is unbuilt, and `StudyRun.reached` says so.
    """
    study: Study = read_study(corpus, uid)
    folder = "train_series" if study.row.split == "train" else "test_series"
    runs: list[SeriesRun] = []
    for row in study.row.series:
        directory = corpus.root / folder / row.study_uid / row.series_uid
        series = read_series(directory, row)
        view = (row.anatomical_plane, row.fluid_sensitive, row.fat_suppression)
        if series.volume is None:
            runs.append(SeriesRun(row.series_uid, view, series.stack, None, "no_stacked_volume"))
            continue
        key = read_regime(series)
        runs.append(
            SeriesRun(
                series_uid=row.series_uid,
                view=view,
                stack=series.stack,
                regime=key,
                why="read" if key is not None else "regime_unreadable",
            )
        )
    reached = "collapse" if any(r.regime is not None for r in runs) else "study"
    return StudyRun(
        uid=study.row.uid, split=study.row.split, series=tuple(runs), reached=reached
    )


def route_state() -> tuple[tuple[str, str], ...]:
    """Figure 8's line with each stage's state, for a caller that wants to print the map."""
    return ROUTE


def open_and_run(root: Path, uid: str) -> StudyRun:
    """Open the corpus at `root` and run one study. The one call a caller needs."""
    from knee.study.corpus import open_corpus

    return run_study(open_corpus(root), uid)
