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
from knee.objects.analysis import AnalysisRequest, SeriesMeasurement, measure_series
from knee.objects.conversation import ConversationInput, SeriesConversation, converse
from knee.study.corpus import Corpus, Study, read_study

# Figure 8's line, in order, with the state of each stage. A stage is "built" when it runs over a
# real study through Chapter 1's entry point -- never when its unit tests pass. That distinction is
# not pedantry: the noise law passed every unit test and then concurred on 4 of 336 real series.
ROUTE: tuple[tuple[str, str], ...] = (
    ("study", "built"),
    ("collapse", "partly"),
    ("lenses", "not_built"),
    ("objects", "partly"),
    ("relations", "not_built"),
    ("loop", "not_built"),
    ("candidates", "not_built"),
    ("cleanup", "not_built"),
    ("vectors", "not_built"),
    ("every_object", "not_built"),
    ("predicates", "not_built"),
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
    measurements: SeriesMeasurement | None = None


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
    conversations: tuple[SeriesConversation, ...] = field(default_factory=tuple)


def run_study(
    corpus: Corpus, uid: str, analysis: AnalysisRequest | None = None
) -> StudyRun:
    """Walk one study down Figure 8's line, as far as the build reaches.

    Chapter 1 reads the study whole at stored fidelity. The collapse then reads each series' regime
    key -- the cheap whole-field readings that say what a series IS before any expensive work runs.
    Beyond that the route is unbuilt, and `StudyRun.reached` says so.
    """
    study: Study = read_study(corpus, uid)
    runs: list[SeriesRun] = []
    for series in study.series:
        row = series.row
        key = read_regime(series) if series.volume is not None else None
        measurements = None
        if analysis is not None:
            measurements = (
                measure_series(series, analysis)
                if analysis.prominence_mm is None
                else measure_series(
                    series,
                    analysis,
                    background_split=key.background_split
                    if key is not None
                    else float("nan"),
                )
            )
        view = (row.anatomical_plane, row.fluid_sensitive, row.fat_suppression)
        if series.volume is None:
            runs.append(
                SeriesRun(
                    row.series_uid,
                    view,
                    series.stack,
                    None,
                    "no_stacked_volume",
                    measurements,
                )
            )
            continue
        runs.append(
            SeriesRun(
                series_uid=row.series_uid,
                view=view,
                stack=series.stack,
                regime=key,
                why="read" if key is not None else "regime_unreadable",
                measurements=measurements,
            )
        )
    reached = "collapse" if any(r.regime is not None for r in runs) else "study"
    conversations = ()
    if analysis is not None and analysis.conversation:
        import numpy as np

        inputs = tuple(
            ConversationInput(
                r.series_uid,
                r.view[0],
                r.measurements,
                r.regime.background_split if r.regime is not None else float("nan"),
            )
            for r in runs
        )
        conversations = converse(
            inputs, np.asarray(analysis.offsets_mm), analysis.backend
        )
    return StudyRun(
        uid=study.row.uid,
        split=study.row.split,
        series=tuple(runs),
        reached=reached,
        conversations=conversations,
    )


def route_state() -> tuple[tuple[str, str], ...]:
    """Figure 8's line with each stage's state, for a caller that wants to print the map."""
    return ROUTE


def open_and_run(
    root: Path, uid: str, analysis: AnalysisRequest | None = None
) -> StudyRun:
    """Open the corpus at `root` and run one study. The one call a caller needs."""
    from knee.study.corpus import open_corpus

    return run_study(open_corpus(root), uid, analysis)
