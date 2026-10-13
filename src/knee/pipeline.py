"""The route a study takes, end to end.

This is an ORCHESTRATION in the thesis's sense (SS13.7): it moves values between stages and decides
nothing itself. Every judgement belongs to the stage it came from.

It is the object model's route, in order (`docs/OBJECT_MODEL.md`, `docs/PIPELINE_AS_OBJECT.md`), and
it is honest about its own state: a stage that is built runs and reports what it read; a stage that
is not built reports its named absence and the route carries on. So this file is readable as the
project's table of contents.

**The order is the dependency order, and the conversation sits where its readers are** (task 6.1,
`specs/route-composition`). Until 2026-10-12 the route partitioned, related and predicated every
series and THEN conversed, so the conversation's refined parse reached nothing -- the Codex
reading of the handoff: "Its subdivisions and disagreements are retained and rendered, but cannot
affect those earlier decisions." Now every series is measured first, the acquisitions converse,
and only then do ownership, relations and the bundles read the parse, each seating what the
conversation gave it beside the solitary reading. The founder's standard sentence names this:
"the combined sum total of all the analyses we have in conversation with one another".

**Who records what.** A stage records its own `<stage>.produced`, and a CONSUMER records
`<producer>.consumed_by.<consumer>` at the point it reads the record (task 6.5) -- never the route
after production, which said a value was consumed when nothing had read it. The route records only
for the two pinned multi-exit readers, `read_study` and `read_regime`, so no side effect threads
through a pinned decision.

The impure edge stays thin (SS13.7: "reading a movie, writing the output, drawing pictures"). This
module reads studies and returns values. It writes nothing and draws nothing; `knee.pictures` is a
separate layer that takes a finished run and can be switched off without the run noticing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from knee.collapse.regime import RegimeKey, read_regime
from knee.collapse.structure import StructureReading, read_structure, told_sign
from knee.lenses.places import LensesReading, read_lenses
from knee.objects.analysis import AnalysisRequest, SeriesMeasurement, measure_series
from knee.objects.conversation import ConversationInput, SeriesConversation, converse
from knee.output.projection import OutputReading, Projection, read_output
from knee.ownership.claims import OwnershipMembers, read_ownership_members
from knee.predicates.findings import FindingsReading, read_findings
from knee.relations.shell import RelationsReading, read_relations
from knee.study.corpus import Corpus, Series, Study, read_study
from knee.study.series import selected_slice
from knee.telemetry import ledger
from knee.vectors.bundles import BundlesReading, read_bundles

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
    ("relations", "not_built"),  # carries its pairings; interstice extent still absent
    ("ownership", "built"),  # one member per parse, consumed and rendered
    # `partly`: the first increment ran over the real study (51 profiles, 2026-10-12) and
    # renders; the conjunction, composite, dome-link and ring banks are carried unavailable.
    ("vectors", "partly"),  # the BUNDLES: each <object>'s profile as row counts
    # `partly`: it runs per study, reads its subject facts from relations, ownership and the
    # bundles, returns twelve named standings and renders them, but it DECIDES nothing -- no
    # construction exists for ten of the twelve and no correspondence is declared for any.
    ("predicates", "partly"),  # the twelve, each on its named subject
    # `partly`: the companion record is written and drawn on every run; submission rows are
    # refused by name while the numeric projection is the founder's to declare.
    ("output", "partly"),  # the companion record, and the refused projection
)

#: The stages in route order, for the attendance roster.
STAGES: tuple[str, ...] = tuple(stage for stage, _ in ROUTE)


@dataclass(frozen=True, slots=True)
class SeriesRun:
    """What the pipeline read from one series, and what it could not read.

    `regime` is the series' regime key when the collapse could read one, else None with `why`
    saying which named code stopped it. A reading not made is never a reading of zero.

    `conversation` is this series' own reading from the same-orientation conversation, or None
    when none was requested; it is carried HERE, on the series it is about, because ownership and
    relations read it, and a value is kept where its consumers find it.

    `ownership`, `relations` and `bundles` are ALWAYS present, never None, because each stage is
    total over a missing predecessor: each returns a record or a named absence from the one shared
    vocabulary (`knee.absence`). That is what lets the route run end to end whatever is missing.
    """

    series_uid: str
    view: tuple[str, str, str]
    stack: tuple[str, ...]
    regime: RegimeKey | None
    why: str
    measurements: SeriesMeasurement | None = None
    conversation: SeriesConversation | None = None
    ownership: OwnershipMembers | None = None
    relations: RelationsReading | None = None
    lenses: LensesReading | None = None
    bundles: BundlesReading | None = None
    # The study stage's own retained picture content (task 6.9): its per-slice codes, and the
    # walk through the stack it keeps so the writer can save it without the whole volume; and
    # (task 7.2) each slice's thickness as the study stage read it from the header it owns.
    slice_codes: tuple[str, ...] = ()
    walk_indices: tuple[int, ...] = ()
    walk: np.ndarray | None = None
    slice_thickness_mm: tuple[float | None, ...] = ()
    # The geometry's two spreads (task 7.12), measured by the study stage and never judged: how
    # far any slice's direction cosines, and its in-plane origin, depart from the first slice's.
    # None where the series has no geometry.
    orientation_spread: float | None = None
    origin_spread_mm: float | None = None
    # The field's structural reading (task 7.1): air, the leg, the axis, the profile, the basins
    # and the seam, read from the selected plane; None when no analysis named a tile, as
    # `measurements` is.
    structure: StructureReading | None = None


@dataclass(frozen=True, slots=True)
class StudyRun:
    """One study's whole route, with every stage's attendance.

    `series` holds one `SeriesRun` each, in the table's order. `findings` is the twelve, per STUDY
    rather than per series, because a finding is a statement about the knee; `output` is the
    companion record and the projection's standing. Neither is ever None: both stages are total.

    `attendance` names every route stage with the code that stage itself returned for this study
    -- the conclave reading, in which coverage is a population and never a high-water mark.
    `reached` survives beside it as the telemetry scalar it always was: the furthest stage that
    read something, which says nothing about which members supplied readings.
    """

    uid: str
    split: str
    series: tuple[SeriesRun, ...] = field(default_factory=tuple)
    reached: str = "study"
    findings: FindingsReading | None = None
    output: OutputReading | None = None
    attendance: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    @property
    def conversations(self) -> tuple[SeriesConversation, ...]:
        """Every series' conversation reading, in series order, for a caller that wants them together."""
        return tuple(
            run.conversation for run in self.series if run.conversation is not None
        )


def _measure(
    series: Series, analysis: AnalysisRequest | None, key: RegimeKey | None
) -> SeriesMeasurement | None:
    """The objects stage over one series, when an analysis was requested."""
    if analysis is None:
        return None
    if analysis.prominence_mm is None:
        return measure_series(series, analysis)
    return measure_series(
        series,
        analysis,
        background_split=key.background_split if key is not None else float("nan"),
    )


def _structure(
    series: Series, analysis: AnalysisRequest | None
) -> StructureReading | None:
    """The field's structural reading of the selected plane, when an analysis names the tile.

    Read by the same rule as the objects stage: the plane is `selected_slice`'s, and without an
    analysis request there is no tile to squint at, so the reading is not made, as the objects
    stage's is not. The reading itself is total: a series without a volume, without a geometry
    or with a request outside its stack is handed None for the plane or the header and names
    that silence itself. The told sign is the series table's flag, never the pixels.
    """
    if analysis is None:
        return None
    volume, geometry = series.volume, series.geometry
    index = selected_slice(0 if volume is None else len(volume), analysis.slice_index)
    plane = None if volume is None or index is None else volume[index]
    header_read = geometry is not None and index is not None
    orientation = geometry.orientation[index] if header_read else None
    normal = None if geometry is None else geometry.normal
    spacing = (
        (float(geometry.spacing[index][0]), float(geometry.spacing[index][1]))
        if header_read
        else (float("nan"), float("nan"))
    )
    return read_structure(
        plane,
        orientation,
        normal,
        spacing,
        analysis.tile_mm,
        told_sign(series.row.fluid_sensitive),
        analysis.structure_bars,
    )


@dataclass(frozen=True, slots=True)
class _Measured:
    """One series after step 1: what the field, the lenses and the objects stage read from it."""

    series: Series
    key: RegimeKey | None
    lenses: LensesReading
    measurement: SeriesMeasurement | None
    structure: StructureReading | None


def _attendance(
    runs: tuple[SeriesRun, ...], findings: FindingsReading, output: OutputReading
) -> tuple[tuple[str, str], ...]:
    """Every stage with the code it returned, in `STAGES` order: `present` if any series read, else the first silence."""

    def over_series(codes: list[str]) -> str:
        if not codes:
            return "predecessor_absent"
        return "present" if "present" in codes else codes[0]

    lens_codes = [
        "present"
        if any(m.code == "present" for m in run.lenses.members)
        else run.lenses.members[0].code
        for run in runs
        if run.lenses is not None and run.lenses.members
    ]
    by_stage = {
        "study": "present" if runs else "predecessor_empty",
        "collapse": over_series(
            ["present" if r.regime is not None else r.why for r in runs]
        ),
        "lenses": over_series(lens_codes),
        "objects": over_series(
            [
                "present" if r.measurements.code == "measured" else r.measurements.code
                for r in runs
                if r.measurements is not None
            ]
        ),
        "relations": over_series([r.relations.code for r in runs if r.relations]),
        "ownership": over_series([r.ownership.code for r in runs if r.ownership]),
        "vectors": over_series([r.bundles.code for r in runs if r.bundles]),
        "predicates": findings.code,
        "output": output.code,
    }
    # `STAGES` orders the roster (task 7.2): a stage added to ROUTE without a reading here is a
    # KeyError on the first run, never a roster that silently omits it.
    return tuple((stage, by_stage[stage]) for stage in STAGES)


def run_study(
    corpus: Corpus,
    uid: str,
    analysis: AnalysisRequest | None = None,
    projection: Projection | None = None,
) -> StudyRun:
    """Walk one study down the object model's route, in dependency order.

    1. Chapter 1 reads the study whole at stored fidelity; per series the collapse reads the regime
       key and the structure of the selected plane, the lenses read every place against the key,
       and the objects stage measures the plane.
    2. The same-orientation acquisitions converse, each series receiving its refined parse.
    3. Per series, ownership seats one member per parse, relations reads its pairings, and the
       bundles read what the lenses and the partition said about each object.
    4. Per study, the predicates read their subject facts from ownership and relations, and the
       output joins the twelve to the competition's columns -- refusing rows while the projection
       is undeclared.

    `projection` is the declared numeric value with its author and date, and it is None today.
    """
    study: Study = read_study(corpus, uid)
    ledger.record("study.produced", series=len(study.series))

    # 1. Measure every series. The route counts the two pinned multi-exit readers here; every
    # other stage records its own production, and every consumer its own consumption. The field
    # reads two things per series, the regime key and the structural reading of the selected
    # plane (task 7.1), and records both under its one `collapse.produced`.
    measured: list[_Measured] = []
    for series in study.series:
        ledger.record(
            "study.consumed_by.collapse", volume=1 if series.volume is not None else 0
        )
        key = read_regime(series) if series.volume is not None else None
        structure = _structure(series, analysis)
        ledger.record(
            "collapse.produced",
            regime=1 if key is not None else 0,
            structure=1 if structure is not None and structure.code == "present" else 0,
        )
        lenses = read_lenses(series.volume, key)
        measured.append(
            _Measured(series, key, lenses, _measure(series, analysis, key), structure)
        )

    # 2. The conversation, over every ordered same-orientation pair, BEFORE anything reads a parse.
    conversation_of: dict[str, SeriesConversation] = {}
    if analysis is not None and analysis.conversation:
        inputs = tuple(
            ConversationInput(
                read.series.row.series_uid,
                read.series.row.anatomical_plane,
                read.measurement,
                read.key.background_split if read.key is not None else float("nan"),
            )
            for read in measured
        )
        for reading in converse(
            inputs, np.asarray(analysis.offsets_mm), analysis.backend
        ):
            conversation_of[reading.series_uid] = reading

    # 3. Per series, the stages that read the parse. Each is TOTAL over a missing predecessor, so
    # each runs unconditionally and none is guarded by an `if`: a guard here would be the route
    # deciding, and the route decides nothing (SS13.7); the stage names its own silence.
    runs: list[SeriesRun] = []
    for read in measured:
        series, key, lenses, measurement = (
            read.series,
            read.key,
            read.lenses,
            read.measurement,
        )
        row = series.row
        conversation = conversation_of.get(row.series_uid)
        interiors = getattr(measurement, "interiors", None)
        frame = getattr(measurement, "frame", None)
        ownership = read_ownership_members(interiors, conversation)
        relations = read_relations(interiors, frame.spacing_rc if frame else None)
        others = tuple(
            (other.series, other.measurement)
            for other in measured
            if other.series.row.series_uid != row.series_uid
        )
        # The backend the request names selects the slab rule's twin (task 7.10); with no
        # request there is no kernel path to select, and the reference is the stage's default.
        bundles = read_bundles(
            ownership,
            lenses,
            measurement,
            others,
            backend=analysis.backend if analysis is not None else "reference",
        )
        runs.append(
            SeriesRun(
                series_uid=row.series_uid,
                view=(row.anatomical_plane, row.fluid_sensitive, row.fat_suppression),
                stack=series.stack,
                regime=key,
                why="no_stacked_volume"
                if series.volume is None
                else ("read" if key is not None else "regime_unreadable"),
                measurements=measurement,
                conversation=conversation,
                ownership=ownership,
                relations=relations,
                lenses=lenses,
                bundles=bundles,
                slice_codes=series.slice_codes,
                walk_indices=series.walk_indices,
                walk=series.walk,
                slice_thickness_mm=series.slice_thickness_mm,
                orientation_spread=(
                    None
                    if series.geometry is None
                    else float(series.geometry.orientation_spread)
                ),
                origin_spread_mm=(
                    None
                    if series.geometry is None
                    else float(series.geometry.origin_spread_mm)
                ),
                structure=read.structure,
            )
        )

    # 4. Per study: the predicates over every series' facts, and the output over the twelve.
    series_runs = tuple(runs)
    findings = read_findings(series_runs)
    output = read_output(findings, projection)

    # The furthest stage that actually read something -- a scalar kept for telemetry. Ownership
    # advances it only where a member returned a reading; relations never does, because its
    # construction is unbuilt, and predicates never does, because it resolves nothing
    # (`test_open_and_run_attaches_real_measurements_and_reads_each_series_once` caught the case
    # where wiring it reported "predicates" for a study whose regime was all it read).
    reached = "collapse" if any(r.regime is not None for r in runs) else "study"
    if any(r.ownership is not None and r.ownership.code == "present" for r in runs):
        reached = "ownership"
    return StudyRun(
        uid=study.row.uid,
        split=study.row.split,
        series=series_runs,
        reached=reached,
        findings=findings,
        output=output,
        attendance=_attendance(series_runs, findings, output),
    )


def route_state() -> tuple[tuple[str, str], ...]:
    """The object model's route with each stage's state, for a caller that wants to print the map."""
    return ROUTE


def open_and_run(
    root: Path,
    uid: str,
    analysis: AnalysisRequest | None = None,
    projection: Projection | None = None,
) -> StudyRun:
    """Open the corpus at `root` and run one study. The one call a caller needs."""
    from knee.study.corpus import open_corpus

    return run_study(open_corpus(root), uid, analysis, projection)
