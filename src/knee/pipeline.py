"""The route a study takes, end to end.

This is an ORCHESTRATION in the thesis's sense (SS13.7): it moves values between stages and decides
nothing itself. Every judgement belongs to the stage it came from.

It is the object model's route, in order (`docs/OBJECT_MODEL.md`, `docs/PIPELINE_AS_OBJECT.md`), and
it is honest about its own state: a stage that is built runs and reports what it read; a stage that
is not built reports `not_built` and the route carries on. So this file is readable as the project's
table of contents, and `just run` over the corpus says exactly how far the pipeline reaches today.

The impure edge stays thin (SS13.7: "reading a movie, writing the output, drawing pictures"). This
module reads studies and returns values. It writes nothing and draws nothing; `knee.pictures` is a
separate layer that takes a finished run and can be switched off without the run noticing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from knee.collapse.regime import RegimeKey, read_regime
from knee.lenses.places import LensReading, read_lenses
from knee.objects.analysis import AnalysisRequest, SeriesMeasurement, measure_series
from knee.objects.conversation import ConversationInput, SeriesConversation, converse
from knee.ownership.claims import OwnershipReading, read_ownership
from knee.predicates.findings import FindingsReading, read_findings
from knee.relations.pairings import PairingReading, read_pairings
from knee.relations.shell import RelationsReading, read_relations
from knee.study.corpus import Corpus, Study, read_study
from knee.telemetry import ledger

# The object model's route, in order, with the state of each stage. A stage is "built" when it runs
# over a real study through Chapter 1's entry point -- never when its unit tests pass. That
# distinction is not pedantry: the noise law passed every unit test and then concurred on 4 of 336
# real series.
#
# Entries are PACKAGE names, because `test_a_stage_is_not_built_until_it_renders` reads them against
# `knee.pictures`; `docs/OBJECT_MODEL.md` names two of them differently as stages, noted below.
# Four of Figure 8's transcribed stages were archived 2026-10-12 at the founder's ruling ("Begone,
# Satan!"): loop, candidates, cleanup and every_object, whose roles fold into objects and ownership.
ROUTE: tuple[tuple[str, str], ...] = (
    ("study", "built"),  # the input, whole at stored fidelity
    ("collapse", "partly"),  # the FIELD: regime, noise law, physical frame, the squint
    ("lenses", "not_built"),  # every place, every acquisition, one ternary digit
    ("objects", "partly"),  # the <object>s, and SS6's refinement of their borders
    ("relations", "not_built"),  # rendered shell; facing-pair construction still absent
    ("ownership", "built"),  # real-study partition, consumed and rendered
    ("vectors", "not_built"),  # the BUNDLES: each <object>'s profile as row counts
    # `partly`: it runs per study, returns twelve named standings and renders them, but it DECIDES
    # nothing -- no subject is constructed for ten of the twelve and no correspondence is declared
    # for any. It produces its record; what it does not do is read a knee.
    ("predicates", "partly"),  # the twelve, each on its named subject
    ("output", "not_built"),  # twelve confidences, with the kept record behind them
)


@dataclass(frozen=True, slots=True)
class SeriesRun:
    """What the pipeline read from one series, and what it could not read.

    `regime` is the series' regime key when the collapse could read one, else None with `why`
    saying which named code stopped it. A reading not made is never a reading of zero.

    `ownership` and `relations` are ALWAYS present, never None, because both stages are total over
    a missing predecessor: each returns a record or a named absence from the one shared vocabulary
    (`knee.absence`). That is what lets the route run end to end whatever is missing, and it is why
    the absence vocabulary had to be declared before either stage was built.
    """

    series_uid: str
    view: tuple[str, str, str]
    stack: tuple[str, ...]
    regime: RegimeKey | None
    why: str
    measurements: SeriesMeasurement | None = None
    ownership: OwnershipReading | None = None
    relations: RelationsReading | None = None
    lenses: LensReading | None = None
    pairings: PairingReading | None = None


@dataclass(frozen=True, slots=True)
class StudyRun:
    """One study's whole route, as far as the pipeline reaches.

    `reached` is the last stage that did anything; `series` holds one `SeriesRun` each, in the
    table's order. Stages beyond `reached` are not failures -- they are unbuilt, and the route
    names them so that what is missing is as legible as what is present.

    `findings` is the twelve, per STUDY rather than per series, because a finding is a statement
    about the knee and the series are the acquisitions it was read from. It is never None: the
    stage is total over the series tuple and returns twelve named standings whatever it met.
    """

    uid: str
    split: str
    series: tuple[SeriesRun, ...] = field(default_factory=tuple)
    reached: str = "study"
    conversations: tuple[SeriesConversation, ...] = field(default_factory=tuple)
    findings: FindingsReading | None = None


def run_study(
    corpus: Corpus, uid: str, analysis: AnalysisRequest | None = None
) -> StudyRun:
    """Walk one study down the object model's route, as far as the build reaches.

    Chapter 1 reads the study whole at stored fidelity. The collapse then reads each series' regime
    key -- the cheap whole-field readings that say what a series IS before any expensive work runs.
    Beyond that the route is unbuilt, and `StudyRun.reached` says so.
    """
    study: Study = read_study(corpus, uid)
    # WHO RECORDS WHAT. A stage with one natural exit records its own `produced` -- lenses,
    # pairings, ownership, relations do. `read_study` and `read_regime` have several exits and are
    # pinned, so the route counts them here rather than threading a side effect through a pinned
    # decision; the route can see exactly what came back. Either way every stage is counted, so a
    # stage that ran can be told from one that never executed.
    ledger.record("study.produced", series=len(study.series))
    runs: list[SeriesRun] = []
    for series in study.series:
        row = series.row
        key = read_regime(series) if series.volume is not None else None
        ledger.record("collapse.produced", regime=1 if key is not None else 0)
        ledger.record("collapse.consumed", regime=1 if key is not None else 0)
        lenses = read_lenses(series.volume, key)
        ledger.record("lenses.consumed", places=int(lenses.codes.size))
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
        # Both stages are TOTAL over a missing predecessor, so both run unconditionally and
        # neither is guarded by an `if`. A guard here would be the route deciding, and the route
        # decides nothing (SS13.7); the stage names its own silence.
        interiors = getattr(measurements, "interiors", None)
        ownership = read_ownership(interiors)
        ledger.record("ownership.consumed", objects=int(ownership.objects))
        relations = read_relations(interiors)
        ledger.record("relations.consumed", interstices=len(relations.interstices))
        frame = getattr(measurements, "frame", None)
        pairings = read_pairings(
            interiors, frame.spacing_rc if frame is not None else None
        )
        ledger.record("pairings.consumed", profiles=int(pairings.outcome_codes.size))
        if series.volume is None:
            runs.append(
                SeriesRun(
                    row.series_uid,
                    view,
                    series.stack,
                    None,
                    "no_stacked_volume",
                    measurements,
                    ownership,
                    relations,
                    lenses,
                    pairings,
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
                ownership=ownership,
                relations=relations,
                lenses=lenses,
                pairings=pairings,
            )
        )
    # The furthest stage that actually read something. Ownership advances it only where it
    # returned a reading; relations never does, because its construction is unbuilt and saying
    # otherwise would claim a stage the build has not reached.
    reached = "collapse" if any(r.regime is not None for r in runs) else "study"
    if any(r.ownership is not None and r.ownership.code == "present" for r in runs):
        reached = "ownership"
    # THE PREDICATES, per study: a finding is a statement about the knee, so the twelve are
    # evaluated once over all its series rather than once per acquisition. Total over the tuple,
    # so it runs unconditionally and names its own silence -- the route decides nothing (SS13.7).
    findings = read_findings(tuple(runs))
    ledger.record("predicates.consumed", findings=len(findings.findings))
    # It does NOT advance `reached`, for the reason relations does not: it runs and resolves
    # nothing, so naming it would claim a stage the build has not reached. Its own code says
    # only whether series were handed over, which is true of almost every study -- wiring it
    # to `reached` made the route report "predicates" for a study whose regime was all it read,
    # and `test_open_and_run_attaches_real_measurements_and_reads_each_series_once` caught it.
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
        ledger.record("conversation.produced", series=len(conversations))
        ledger.record(
            "conversation.consumed",
            exchanges=sum(len(c.exchanges) for c in conversations),
        )
    return StudyRun(
        uid=study.row.uid,
        split=study.row.split,
        series=tuple(runs),
        reached=reached,
        conversations=conversations,
        findings=findings,
    )


def route_state() -> tuple[tuple[str, str], ...]:
    """The object model's route with each stage's state, for a caller that wants to print the map."""
    return ROUTE


def open_and_run(
    root: Path, uid: str, analysis: AnalysisRequest | None = None
) -> StudyRun:
    """Open the corpus at `root` and run one study. The one call a caller needs."""
    from knee.study.corpus import open_corpus

    return run_study(open_corpus(root), uid, analysis)
