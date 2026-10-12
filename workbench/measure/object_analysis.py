"""Run Packet A through the production entry point and save its actual returned values."""

import argparse
import json
import platform
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict, fields
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np

from knee import collapse
from knee.collapse.physical import PlaneFrame, Squint
from knee.collapse.structure import StructureReading
from knee.compute.contracts import declared_contracts
from knee.lenses.digits import DIGIT_CODES
from knee.lenses.members import STANDING_CODES
from knee.lenses.places import SILENT, LensesReading, LensReading
from knee.objects.analysis import AnalysisRequest, SeriesMeasurement
from knee.objects.conversation import SeriesConversation
from knee.objects.profiles import ProfileReading
from knee.output.projection import OutputReading
from knee.ownership.claims import OwnershipMember, OwnershipMembers
from knee.pipeline import SeriesRun, StudyRun, run_study
from knee.predicates.findings import CODES as FINDING_CODES
from knee.predicates.findings import FindingsReading
from knee.relations.pair_codes import CODES as PAIRING_CODES
from knee.relations.pairings import PairingReading
from knee.relations.shell import Interstice, RelationsReading
from knee.study.corpus import LOCAL_ROOT, Corpus, open_corpus
from knee.study.decoders import decoder_plugins
from knee.study.shape import CorpusShape
from knee.study.tables import Tables, labeled_uids, split_uids
from knee.telemetry import recording
from knee.vectors.bundles import Bank, BundlesReading, ObjectProfile
from workbench.measure.boundary_records import boundary_record
from workbench.measure.conversation_records import conversation_record
from workbench.measure.interior_records import interior_record

#: The studies `--split` selects when `--uid` names none: the fully labeled training studies (the
#: default), every training study, or every test study.
SPLITS: tuple[str, ...] = ("labeled", "train", "test")

#: The physical axes a request can profile along, as unit directions in the patient's LPS frame.
DIRECTIONS: dict[str, tuple[float, float, float]] = {
    "superior": (0.0, 0.0, 1.0),
    "left": (1.0, 0.0, 0.0),
    "posterior": (0.0, 1.0, 0.0),
}

#: One record's fields beside the arrays saved with it, each dict in the order it was made. The
#: order is part of the saved record, so every builder below keeps it.
Part = tuple[dict, dict[str, np.ndarray]]


def package_version(name: str) -> str | None:
    """The installed version of a package, or None where it is not installed."""
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def source_snapshot() -> dict[str, str]:
    """The SHA-256 of every Python source file of the `knee` package, by path."""
    if collapse.__file__ is None:
        raise RuntimeError("package_source_unavailable")
    package = Path(collapse.__file__).resolve().parent.parent
    return {
        str(path.relative_to(package.parent)): sha256(path.read_bytes()).hexdigest()
        for path in sorted(package.rglob("*.py"))
    }


def json_safe(value: object) -> object:
    """One regime reading as JSON. A reading that was not made stays absent, never a zero.

    `json.dumps(..., allow_nan=False)` refuses NaN, and NaN is exactly how the field stage says it
    could not make a reading (`regime.py`: "A reading not made is NaN, never zero"). None carries
    that through honestly; writing 0.0 there would turn a silence into a measurement.
    """
    if value is None or isinstance(value, (bool, str)):
        return value
    if isinstance(value, (tuple, list)):
        return [json_safe(item) for item in value]
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        return float(value) if np.isfinite(value) else None
    return value


def array_digest(array: np.ndarray) -> str:
    """The SHA-256 of an array's dtype, shape and bytes, so a saved array can be checked."""
    return sha256(
        array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
    ).hexdigest()


def save_study_checkpoint(
    out: Path,
    study: dict,
    request: AnalysisRequest,
    kernels: dict[str, str],
    verification: dict,
    records: list[dict],
    failures: list[dict],
) -> None:
    """Atomically publish one study's saved records for inspection after interruption."""
    directory = out / "checkpoints"
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / f"{study['study_uid']}.json"
    temporary = target.with_suffix(".json.tmp")
    checkpoint = {
        "schema": "physical-measurements-study-checkpoint-v1",
        "study": study,
        "request": asdict(request),
        "kernel_sources": kernels,
        "writer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "detective": verification,
        "records": records,
        "failures": failures,
        "restart": "Inspect saved records; rerun this study with --uid into a fresh output directory. Do not silently merge runs.",
    }
    temporary.write_text(json.dumps(checkpoint, indent=2, allow_nan=False) + "\n")
    temporary.replace(target)


# ---------------------------------------------------------------------------------------------
# The command's arguments, and the request and the studies they describe.
# ---------------------------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """The command's arguments; `--root` defaults to the corpus module's own local root."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=LOCAL_ROOT)
    parser.add_argument(
        "--uid",
        help="measure only this study, whatever --split says; omit to measure every study of --split",
    )
    parser.add_argument(
        "--split",
        choices=SPLITS,
        default="labeled",
        help=(
            "which studies to measure when --uid is omitted: the fully labeled training "
            "studies (default), every training study, or every test study"
        ),
    )
    parser.add_argument("--tile-mm", type=float, required=True)
    parser.add_argument("--span-mm", type=float, required=True)
    parser.add_argument("--samples", type=int, required=True)
    parser.add_argument("--axis", choices=tuple(DIRECTIONS), required=True)
    parser.add_argument("--backend", choices=("reference", "jit"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--prominence-mm",
        type=float,
        help="enable geometric interior/border reading at this physical prominence",
    )
    parser.add_argument(
        "--conversation",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "exchange original same-orientation boundary readings (default). The founder, "
            "2026-10-12, on what the one command does: 'the combined sum total of all the "
            "analyses we have in conversation with one another' -- so this is the shape of the "
            "run, not an option bolted onto it. --no-conversation runs the series in isolation."
        ),
    )
    parser.add_argument(
        "--detective-report",
        type=Path,
        help="complete current-digest Detective JSON report",
    )
    parser.add_argument(
        "--pictures",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "draw every stage after the run (default). --no-pictures is the competition kernel, "
            "where the output is just the diagnosis; the compute is identical either way."
        ),
    )
    return parser


def check_arguments(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    """Refuse an argument set that cannot make a request, in words, with the way out named."""
    if args.samples < 1 or not np.isfinite(args.span_mm) or args.span_mm <= 0:
        parser.error("positive span-mm and samples required")
    if args.conversation and args.prominence_mm is None:
        # `AnalysisRequest` couples the two, and would raise `invalid_conversation_request`. Said
        # here instead, in words, with the way out named -- a refusal is a verdict, not a crash.
        parser.error(
            "the conversation reads boundaries, so it needs --prominence-mm; "
            "pass --no-conversation to run the series in isolation"
        )


def analysis_request(args: argparse.Namespace) -> AnalysisRequest:
    """The physical request the arguments describe; `AnalysisRequest` itself refuses what it cannot read."""
    return AnalysisRequest(
        args.tile_mm,
        tuple(np.linspace(-args.span_mm, args.span_mm, args.samples))
        if args.samples > 1
        else (0.0,),
        DIRECTIONS[args.axis],
        args.backend,
        prominence_mm=args.prominence_mm,
        conversation=args.conversation,
    )


def select_uids(tables: Tables, split: str, uid: str | None) -> tuple[str, ...]:
    """The studies to measure: the one `--uid` names, else every study of the chosen split."""
    if uid:
        return (uid,)
    if split not in SPLITS:
        raise ValueError(f"invalid_split: {split!r}")
    return labeled_uids(tables) if split == "labeled" else split_uids(tables, split)


# ---------------------------------------------------------------------------------------------
# What the receipt says about the run itself: the standing of its verification and its sources.
# ---------------------------------------------------------------------------------------------


def verification_record(report: Path | None) -> dict:
    """The Detective standing the receipt carries: the report's digest and body, or `not_supplied`."""
    if report is None:
        return {"standing": "not_supplied"}
    return {
        "report_sha256": sha256(report.read_bytes()).hexdigest(),
        "snapshot": json.loads(report.read_text()),
        "profile_codes_source_sha256": sha256(
            Path(collapse.__file__).parent.joinpath("profile_codes.py").read_bytes()
        ).hexdigest(),
    }


def environment_record() -> dict:
    """The interpreter, platform and package versions the run executed under, its JIT settings, and
    the decoder plugins available for each transfer syntax the competition's files need."""
    return {
        "python": platform.python_version(),
        "machine": platform.machine(),
        "numpy": package_version("numpy"),
        "numba": package_version("numba"),
        "llvmlite": package_version("llvmlite"),
        "scipy": package_version("scipy"),
        "scikit_image": package_version("scikit-image"),
        "platform": platform.platform(),
        "jit": {
            "fastmath": False,
            "nogil": True,
            "cache_requested": True,
            "cache_hit": "not_measured",
        },
        # Which plugin decoded the pixels is provenance (task 7.2): the Kaggle interpreter and
        # this one may differ, and a receipt that does not say cannot be compared across them.
        "decoders": {
            name: list(plugins) for name, plugins in decoder_plugins().items()
        },
    }


def corpus_record(shape: CorpusShape) -> dict:
    """The corpus's shape as the study stage counted it when the corpus opened (task 7.1a)."""
    return {
        "studies": dict(shape.studies),
        "series": dict(shape.series),
        "orphan_series": shape.orphan_series,
        "labeled": shape.labeled,
        "views": [
            {"view": list(triple), "series": series, "studies": studies}
            for triple, series, studies in shape.views
        ],
        "views_per_labeled_study": {
            str(distinct): count
            for distinct, count in sorted(shape.views_per_labeled_study.items())
        },
        "labels": {finding: dict(counts) for finding, counts in shape.labels.items()},
        "reports": dict(shape.reports),
        "report_lengths": list(shape.report_lengths),
    }


def contracts_record() -> dict:
    """Every compute contract the running route declared, by its kernel's dotted path (task 7.3).

    Read from the registry `contracted` fills at import, so the receipt carries each kernel's
    declared `work` beside the ledger's counted work for the same run; a reader compares them.
    """
    return {key: asdict(contract) for key, contract in declared_contracts().items()}


def snapshot_standing(before: dict[str, str], after: dict[str, str]) -> str:
    """`unchanged` when no `knee` source file changed during the run, else `changed`."""
    return "unchanged" if before == after else "changed"


def record_codes(records: list[dict]) -> dict[str, int]:
    """How many saved series carry each objects-stage code."""
    return dict(Counter(record["code"] for record in records))


# ---------------------------------------------------------------------------------------------
# One series' record, built from the readings its stages returned. Nothing here touches a file,
# and every builder keeps the order of the keys it writes: the order is part of the saved record.
# ---------------------------------------------------------------------------------------------


def head_record(
    uid: str, series: SeriesRun, measurement: SeriesMeasurement, backend: str
) -> dict:
    """The series' identity and the objects stage's own scalars, its backend requested and not yet invoked."""
    return {
        "study_uid": uid,
        "series_uid": series.series_uid,
        "view": series.view,
        "code": measurement.code,
        "slice_index": measurement.slice_index,
        "projection_norm": measurement.projection_norm,
        "source_plane": measurement.source_plane,
        "orientation_spread": measurement.orientation_spread,
        "slice_thickness_mm": measurement.slice_thickness_mm,
        "validation_code": measurement.validation_code,
        "requested_backend": backend,
        "effective_backend": "not_invoked",
    }


def study_record(series: SeriesRun) -> dict:
    """The study stage's own record: the stack codes, the per-slice codes and the walk through the stack."""
    # THE STUDY STAGE'S OWN RECORD (task 6.9): the series' stack codes, its per-slice
    # codes, and the walk through the stack the stage retains -- which the writer never
    # saved, so the study frame could draw only the objects stage's selected plane.
    return {
        "stack": list(series.stack),
        "study": {
            "slice_codes": list(series.slice_codes),
            "walk_indices": list(series.walk_indices),
            "walk_array": "study_walk" if series.walk is not None else None,
            # Each slice's thickness as the study stage read it (task 7.2); None where unread.
            "slice_thickness_mm": list(series.slice_thickness_mm),
        },
    }


def structure_record(reading: StructureReading) -> Part:
    """The field's structural reading (task 7.1): its codes, levels, profile and counts, and its arrays.

    The native masks and every tile map are saved as arrays beside the record; the profile and
    the air histogram are small and saved in both forms, so the frame can draw them without the
    artifact and a reader can check them against it.
    """
    record = {
        "code": reading.code,
        "why": reading.why,
        "axis": reading.axis,
        "superior": reading.superior,
        "air_level": json_safe(reading.air_level),
        "dark_level": json_safe(reading.dark_level),
        "dip": reading.dip,
        "profile": [json_safe(float(value)) for value in reading.profile],
        "profile_tiles": [int(tile) for tile in reading.profile_tiles],
        "histogram_counts": [int(count) for count in reading.histogram_counts],
        "histogram_edges": [float(edge) for edge in reading.histogram_edges],
        "squint_tile_shape_rc": None
        if reading.squint is None
        else list(reading.squint.tile_shape_rc),
        "counts": dict(reading.counts),
        "arrays": {
            name: f"structure_{name}"
            for name in ("air", "leg", "inside", "basins", "seam", "dark", "bodies")
        },
    }
    arrays = {
        f"structure_{name}": getattr(reading, name)
        for name in ("air", "leg", "inside", "basins", "seam", "dark", "bodies")
    }
    if reading.squint is not None:
        arrays["structure_squint_median"] = reading.squint.median
        arrays["structure_squint_coverage"] = reading.squint.coverage
        record["arrays"]["squint_median"] = "structure_squint_median"
        record["arrays"]["squint_coverage"] = "structure_squint_coverage"
    return record, arrays


def regime_record(series: SeriesRun) -> dict:
    """The series' whole regime key, every reading the field stage made, and the code naming whether it was read."""
    # THE WHOLE REGIME KEY, not one field of it. It is every reading the field stage
    # already computed once per series (twenty-three since the second member was
    # seated), and until 2026-10-12 this writer took `background_split` and dropped
    # the rest. The founder: "we compute the required object, we drop it ... any
    # compute process here is done for the purpose of visual reasoning. If the lenses
    # don't have information that they can literally show, then what are we doing?"
    # A reading the field could not make stays None.
    regime = series.regime
    return {
        "code": "read" if regime is not None else "regime_unreadable",
        "why": series.why,
        # EVERY field, enumerated from the dataclass rather than from a list kept
        # here. A reading added to the regime key is then saved by construction, so
        # this writer can never silently drop one again.
        "readings": {
            field.name: json_safe(getattr(regime, field.name))
            for field in fields(regime)
        }
        if regime is not None
        else {},
    }


def own_background_split(series: SeriesRun) -> float:
    """The background split the field read for this series, NaN where no regime was read."""
    return series.regime.background_split if series.regime is not None else np.nan


def background_record(split: float, plane: np.ndarray | None) -> dict:
    """The background split, and whether the acquired plane can be annotated with it."""
    return {
        "background_split": float(split) if np.isfinite(split) else None,
        "background_annotation_code": "measured"
        if np.isfinite(split) and plane is not None
        else "unavailable",
    }


def walk_arrays(series: SeriesRun) -> dict[str, np.ndarray]:
    """The walk through the stack the study stage retained, when it retained one."""
    return {"study_walk": series.walk} if series.walk is not None else {}


def pairings_record(pairings: PairingReading) -> Part:
    """The sample-supported pairings with the vocabularies that decode them, and their seven arrays."""
    record = {
        "code": pairings.code,
        "why": pairings.why,
        "scope": pairings.scope,
        "counts": dict(pairings.counts),
        "outcome_names": PAIRING_CODES,
        "side_order": ["near", "far"],
        "corner_order": ["00", "01", "10", "11"],
        "inactive_contributor": -1,
        "unread_contributor": -2,
    }
    arrays = {
        "pairing_source_labels": pairings.source_labels,
        "pairing_far_labels": pairings.far_labels,
        "pairing_trace_codes": pairings.trace_codes,
        "pairing_outcome_codes": pairings.outcome_codes,
        "pairing_positions_rc": pairings.positions_rc,
        "pairing_contributor_labels": pairings.contributor_labels,
        "pairing_band_limits_mm": pairings.band_limits_mm,
    }
    return record, arrays


def lens_member_record(member: LensReading, plane_read: bool) -> dict:
    """One seated lens member: its population, its own edges and counts, and where its arrays are saved."""
    return {
        "population": member.population,
        "code": member.code,
        "why": member.why,
        "low_edge": member.low_edge
        if member.low_edge is not None and np.isfinite(member.low_edge)
        else None,
        "high_edge": member.high_edge
        if member.high_edge is not None and np.isfinite(member.high_edge)
        else None,
        "population_count": member.population_count,
        "minimum_population": member.minimum_population,
        "normalisation": member.normalisation,
        "counts": member.counts,
        "picture_code": member.code if plane_read else "item_unread",
        "codes_array": f"lens_codes_{member.population}",
        "digits_array": f"lens_digits_{member.population}",
    }


def lenses_record(reading: LensesReading, plane_index: int | None) -> Part:
    """Every seated lens member and the standing between them, saved for the selected plane only."""
    # EVERY SEATED MEMBER is serialised, each naming its own population, plus
    # the standing between them per place. No field holds "the" reading: the
    # founder, 2026-10-12, "the pipeline should keep everything, including
    # where things conflict", so a consumer that wants one digit per place
    # must come to him for the rule rather than find one written here.
    depth = reading.members[0].codes.shape[0] if reading.members else 0
    plane_read = plane_index is not None and 0 <= plane_index < depth
    record = {
        "members": [
            lens_member_record(member, plane_read) for member in reading.members
        ],
        "code_names": DIGIT_CODES,
        "standing_names": STANDING_CODES,
        "standing_counts": reading.standing_counts,
        "standings_array": "lens_standings",
        "digit_silence": SILENT,
        "map_scope": "complete native volume (slice,row,column)",
        "saved_scope": "selected native plane (row,column)",
    }
    arrays: dict[str, np.ndarray] = {}
    for member in reading.members:
        arrays[f"lens_codes_{member.population}"] = (
            member.codes[plane_index]
            if plane_read
            else np.empty((0, 0), dtype=np.uint8)
        )
        arrays[f"lens_digits_{member.population}"] = (
            member.digits[plane_index]
            if plane_read
            else np.empty((0, 0), dtype=np.int8)
        )
    arrays["lens_standings"] = (
        reading.standings[plane_index]
        if plane_read
        else np.empty((0, 0), dtype=np.uint8)
    )
    return record, arrays


def ownership_member_record(member: OwnershipMember) -> dict:
    """One seated ownership member: its parse, its code and counts, and where its arrays are saved."""
    return {
        "parse": member.parse,
        "code": member.reading.code,
        "why": member.reading.why,
        "claimed_places": member.reading.claimed_places,
        "residual_places": member.reading.residual_places,
        "unavailable_places": member.reading.unavailable_places,
        "objects": int(member.reading.objects),
        "claims_array": f"ownership_{member.parse}_claims",
        "residual_array": f"ownership_{member.parse}_residual",
    }


def ownership_record(ownership: OwnershipMembers) -> Part:
    """Every seated ownership member's partition, and where the solitary and concurrent claims disagree."""
    # EVERY SEATED MEMBER, one partition per parse (task 6.2), each under its
    # own arrays, plus where the solitary and concurrent claims disagree. No
    # key holds "the" partition: the pipeline keeps everything it computes.
    record = {
        "code": ownership.code,
        "why": ownership.why,
        "comparison": ownership.comparison,
        "disagreeing_places": ownership.disagreeing_places,
        "disagreement_array": "ownership_disagreement",
        "members": [ownership_member_record(member) for member in ownership.members],
    }
    arrays: dict[str, np.ndarray] = {}
    for member in ownership.members:
        arrays[f"ownership_{member.parse}_claims"] = member.reading.claims
        arrays[f"ownership_{member.parse}_residual"] = member.reading.residual
    arrays["ownership_disagreement"] = ownership.disagreement
    return record, arrays


def interstice_record(item: Interstice) -> dict:
    """One constructed relation: its structural kind, its two indexed extents and who built it."""
    return {
        "kind": item.kind,
        "first": item.first,
        "second": item.second,
        "series_uid": item.series_uid,
        "provenance": item.provenance,
    }


def relations_record(relations: RelationsReading) -> dict:
    """The relations stage's code and reason, every interstice it constructed, and its pairings' code."""
    return {
        "code": relations.code,
        "why": relations.why,
        "interstices": [interstice_record(item) for item in relations.interstices],
        "pairings_code": relations.pairings.code
        if relations.pairings is not None
        else None,
    }


def bank_record(bank: Bank) -> dict:
    """One bank of an object's profile: its source stage, its status and its rows or its absence."""
    return {
        "name": bank.name,
        "source_stage": bank.source_stage,
        "status": bank.status,
        "rows": dict(bank.rows),
        "why": bank.why,
    }


def object_profile_record(profile: ObjectProfile) -> dict:
    """One indexed extent's profile: how many places wrote it and every bank by name."""
    return {
        "index": profile.index,
        "places": profile.places,
        "banks": [bank_record(bank) for bank in profile.banks],
    }


def vectors_record(bundles: BundlesReading) -> dict:
    """The bundles stage's code and reason, what its profiles were keyed on, the backend it was
    asked for, every other acquisition's gap fraction, and every profile."""
    return {
        "code": bundles.code,
        "why": bundles.why,
        "subject_kind": bundles.subject_kind,
        "planes_read": bundles.planes_read,
        "backend": bundles.backend,
        "slab_gaps": [
            {"series_uid": uid, "gap_fraction": json_safe(gap)}
            for uid, gap in bundles.slab_gaps
        ],
        "profiles": [object_profile_record(profile) for profile in bundles.profiles],
    }


def plane_arrays(
    measurement: SeriesMeasurement, split: float, annotation: str
) -> dict[str, np.ndarray]:
    """The background mask, the acquired plane and the probe sites, each only where it was read."""
    arrays: dict[str, np.ndarray] = {}
    plane = measurement.acquired_plane
    # `measured` is only ever written for a finite split and a plane that was acquired, so the
    # second test cannot refuse a mask the annotation promised. It narrows the type for the checker.
    if annotation == "measured" and plane is not None:
        arrays["background_mask"] = plane <= split
    if plane is not None:
        arrays["acquired_plane"] = plane
    if measurement.points_rc is not None and measurement.normals_rc is not None:
        arrays.update(
            points_rc=measurement.points_rc,
            normals_rc=measurement.normals_rc,
        )
    return arrays


def frame_arrays(frame: PlaneFrame) -> dict[str, np.ndarray]:
    """The plane frame's origin and basis in the patient's LPS frame."""
    return {"origin_lps": frame.origin_lps, "basis_lps": frame.basis_lps}


def squint_arrays(squint: Squint) -> dict[str, np.ndarray]:
    """The squint's median, extrema, coverage and native bounds, one value per tile."""
    return {
        "median": squint.median,
        "minimum": squint.minimum,
        "maximum": squint.maximum,
        "coverage": squint.coverage,
        "bounds_rc": squint.bounds_rc,
    }


def profile_arrays(profiles: ProfileReading) -> dict[str, np.ndarray]:
    """The sampled profiles, their validity, slopes and offsets."""
    return {
        "samples": profiles.samples,
        "valid": profiles.valid,
        "slopes": profiles.slopes,
        "distances_mm": profiles.distances_mm,
    }


def profile_fields(profiles: ProfileReading) -> dict:
    """The profiles' support codes, the backend that ran them and the work they counted."""
    return {
        "support_code": profiles.support_code,
        "support_codes": profiles.support_codes,
        "requested_backend": profiles.requested_backend,
        "effective_backend": profiles.effective_backend,
        "coordinate_evaluations": profiles.samples.size,
        "source_read_upper_bound": 4 * profiles.samples.size,
        "sample_output_bytes": profiles.samples.nbytes + profiles.valid.nbytes,
    }


def measurement_records(
    measurement: SeriesMeasurement, split: float, annotation: str
) -> Part:
    """The objects stage's saved plane, frame, squint and profiles, and the record fields beside them."""
    record: dict = {}
    arrays = plane_arrays(measurement, split, annotation)
    if measurement.frame is not None:
        arrays.update(frame_arrays(measurement.frame))
        record["spacing_rc_mm"] = measurement.frame.spacing_rc
    if measurement.squint is not None:
        arrays.update(squint_arrays(measurement.squint))
        record["tile_shape_rc"] = measurement.squint.tile_shape_rc
    if measurement.profiles is not None:
        arrays.update(profile_arrays(measurement.profiles))
        record.update(profile_fields(measurement.profiles))
    return record, arrays


def stage_records(series: SeriesRun, plane_index: int | None) -> Part:
    """The records of the stages above the objects stage; a stage that returned nothing leaves no key."""
    record: dict = {}
    arrays: dict[str, np.ndarray] = {}
    # The pairing reading is the relations stage's own since task 6.3; it is saved
    # under its own key, exactly as before, from where the stage keeps it.
    pairings = series.relations.pairings if series.relations is not None else None
    if pairings is not None:
        record["pairings"], saved = pairings_record(pairings)
        arrays.update(saved)
    if series.lenses is not None:
        record["lenses"], saved = lenses_record(series.lenses, plane_index)
        arrays.update(saved)
    if series.ownership is not None:
        record["ownership"], saved = ownership_record(series.ownership)
        arrays.update(saved)
    if series.relations is not None:
        record["relations"] = relations_record(series.relations)
    if series.bundles is not None:
        record["vectors"] = vectors_record(series.bundles)
    if series.structure is not None:
        record["structure"], saved = structure_record(series.structure)
        arrays.update(saved)
    return record, arrays


def serialized_records(
    measurement: SeriesMeasurement,
    conversation: SeriesConversation | None,
    backend: str,
) -> Part:
    """The interiors, boundary census and conversation records, each from its own serializer module."""
    record: dict = {}
    arrays: dict[str, np.ndarray] = {}
    if measurement.interiors is not None:
        record["interiors"], saved = interior_record(measurement.interiors)
        arrays.update(saved)
    if measurement.boundaries is not None:
        record["boundaries"], saved = boundary_record(measurement.boundaries)
        arrays.update(saved)
    if conversation is not None:
        record["conversation"], saved = conversation_record(conversation, backend)
        arrays.update(saved)
    return record, arrays


def merged(parts: tuple[Part, ...]) -> Part:
    """Fold records and arrays together in order; a later part never moves a key an earlier one made."""
    record: dict = {}
    arrays: dict[str, np.ndarray] = {}
    for fields_, saved in parts:
        record.update(fields_)
        arrays.update(saved)
    return record, arrays


def series_record(uid: str, series: SeriesRun, backend: str) -> Part:
    """One series' record and its arrays, from the readings its stages returned; touches no file."""
    measurement = series.measurements
    if measurement is None:
        raise RuntimeError("missing_measurement_record")
    split = own_background_split(series)
    head = head_record(uid, series, measurement, backend)
    head.update(study_record(series))
    head["regime"] = regime_record(series)
    head.update(background_record(split, measurement.acquired_plane))
    return merged(
        (
            (head, walk_arrays(series)),
            stage_records(series, measurement.slice_index),
            measurement_records(measurement, split, head["background_annotation_code"]),
            serialized_records(measurement, series.conversation, backend),
        )
    )


# ---------------------------------------------------------------------------------------------
# Saving one series: its arrays beside the receipt, and the record that describes them.
# ---------------------------------------------------------------------------------------------


def array_table(arrays: dict[str, np.ndarray]) -> dict[str, dict]:
    """The shape, dtype, digest and byte size of every array saved beside a record."""
    return {
        name: {
            "shape": a.shape,
            "dtype": a.dtype.str,
            "digest": array_digest(a),
            "bytes": a.nbytes,
        }
        for name, a in arrays.items()
    }


def source_digests(root: Path, split: str, uid: str, series_uid: str) -> dict[str, str]:
    """The SHA-256 of every source DICOM file of one series, keyed by its path under the root."""
    source_dir = (
        root
        / ("train_series" if split == "train" else "test_series")
        / uid
        / series_uid
    )
    return {
        str(path.relative_to(root)): sha256(path.read_bytes()).hexdigest()
        for path in sorted(source_dir.glob("*.dcm"))
    }


def save_series(
    out: Path, root: Path, split: str, uid: str, series: SeriesRun, backend: str
) -> dict:
    """Build one series' record, write its arrays beside the receipt, and return the record."""
    record, arrays = series_record(uid, series, backend)
    record["arrays"] = array_table(arrays)
    record["sources"] = source_digests(root, split, uid, series.series_uid)
    artifact = Path(uid) / f"{series.series_uid}.npz"
    record["artifact"] = str(artifact)
    (out / artifact).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / artifact, allow_pickle=False, **arrays)
    return record


# ---------------------------------------------------------------------------------------------
# One study's entry in the receipt, and the loop that measures the studies in turn.
# ---------------------------------------------------------------------------------------------


def findings_record(findings: FindingsReading) -> dict:
    """The twelve findings of one study as returned: index, requirement, named code, reason and subjects."""
    # PER STUDY, not per series: a finding is a statement about the knee. Serialised
    # as returned -- index, structural requirement, named code, reason, and the
    # subject facts it READ from relations (task 6.4). No number is written for any
    # finding, because a confidence is knee.output's lossy projection of this record
    # and the projection has not been declared.
    return {
        "code": findings.code,
        "why": findings.why,
        "code_names": FINDING_CODES,
        "series_with_population": findings.series_with_population,
        "series_with_construction": findings.series_with_construction,
        "series_with_profiles": findings.series_with_profiles,
        "findings": [
            {
                "index": finding.index,
                "requirement": finding.requirement,
                "code": finding.code,
                "reason": finding.reason,
                "subjects": list(finding.subjects),
                "candidates": finding.candidates,
                "profiles": finding.profiles,
            }
            for finding in findings.findings
        ],
    }


def output_record(output: OutputReading) -> dict:
    """The companion record of the twelve joined to the competition's columns, and the projection's standing."""
    # THE COMPANION RECORD, written in the same run (task 6.8): the twelve joined to
    # the competition's columns by the declared table. Rows are refused by name
    # while the projection is undeclared, and that refusal is saved as the fact.
    return {
        "code": output.code,
        "why": output.why,
        "projection": None if output.projection is None else asdict(output.projection),
        "companion": [
            {
                "index": row.index,
                "column": row.column,
                "code": row.code,
                "reason": row.reason,
                "subjects": list(row.subjects),
                "candidates": row.candidates,
            }
            for row in output.companion
        ],
        "submission_rows": None
        if output.rows is None
        else [[column, value] for column, value in output.rows],
    }


def study_entry(uid: str, result: StudyRun, events: list[dict], written: int) -> dict:
    """One study's entry in the receipt: its roster and ledger, and the per-study findings and output."""
    entry = {
        "study_uid": uid,
        "code": "complete",
        "series_written": written,
        "reached": result.reached,
        # The roster: every stage with the code it returned (task 6.6). Coverage is a
        # population; `reached` beside it is only the telemetry scalar it always was.
        "attendance": [list(stage) for stage in result.attendance],
        "ledger": events,
    }
    if result.findings is not None:
        entry["findings"] = findings_record(result.findings)
    if result.output is not None:
        entry["output"] = output_record(result.output)
    return entry


def failure_record(uid: str, error: Exception) -> dict:
    """A study that raised: its identifier and the type and message of what it raised."""
    return {"study_uid": uid, "type": type(error).__name__, "message": str(error)}


def unread_entry(uid: str, written: int) -> dict:
    """The entry of a study that raised: `partial` if any of its series was saved first, else `failed`."""
    return {
        "study_uid": uid,
        "code": "partial" if written > 0 else "failed",
        "series_written": written,
    }


def measure_study(
    corpus: Corpus,
    uid: str,
    request: AnalysisRequest,
    out: Path,
    records: list[dict],
) -> dict:
    """Run one study through the route, saving each series as it is read; return the study's entry."""
    # Each series' record is appended to `records` as soon as its arrays are on disk, so a study
    # that fails midway leaves the series it finished saved and counted, and the caller names it
    # `partial`.
    start = len(records)
    with recording() as run_ledger:
        result = run_study(corpus, uid, request)
    events = [asdict(event) for event in run_ledger.events()]
    for series in result.series:
        records.append(
            save_series(out, corpus.root, result.split, uid, series, request.backend)
        )
    return study_entry(uid, result, events, len(records) - start)


def measure_studies(
    corpus: Corpus,
    uids: tuple[str, ...],
    request: AnalysisRequest,
    out: Path,
    kernels: dict[str, str],
    verification: dict,
) -> tuple[list[dict], list[dict], list[dict]]:
    """Measure each study in turn and checkpoint it; return the series records, failures and study entries."""
    # A study that raises is recorded as a failure and the run goes on: what it saved stays saved.
    records: list[dict] = []
    failures: list[dict] = []
    studies: list[dict] = []
    for uid in uids:
        start = len(records)
        try:
            entry = measure_study(corpus, uid, request, out, records)
            studies.append(entry)
            print(f"measured {uid}: {entry['series_written']} series", flush=True)
        except Exception as error:
            failures.append(failure_record(uid, error))
            studies.append(unread_entry(uid, len(records) - start))
            print(f"unreadable {uid}: {type(error).__name__}: {error}", flush=True)
        save_study_checkpoint(
            out,
            studies[-1],
            request,
            kernels,
            verification,
            records[start:],
            [f for f in failures if f.get("study_uid") == uid],
        )
    return records, failures, studies


# ---------------------------------------------------------------------------------------------
# The receipt, the drawing pass, and what the command prints when it finishes.
# ---------------------------------------------------------------------------------------------


def receipt_record(
    *,
    request: AnalysisRequest,
    verification: dict,
    studies: list[dict],
    records: list[dict],
    failures: list[dict],
    kernels: dict[str, str],
    snapshot_code: str,
    codes: dict[str, int],
    study_count: int,
    corpus: CorpusShape,
) -> dict:
    """The receipt: the run's request, environment and provenance hashes, the corpus's shape, every
    declared compute contract, and every saved record."""
    return {
        "schema": "physical-measurements-v2",
        "source_snapshot_code": snapshot_code,
        "detective": verification,
        "studies": studies,
        "scope": "middle acquired plane per series, not full-volume contour tracing",
        "request": asdict(request),
        "environment": environment_record(),
        "corpus": corpus_record(corpus),
        "compute_contracts": contracts_record(),
        "writer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "interior_serializer_sha256": sha256(
            Path(__file__).with_name("interior_records.py").read_bytes()
        ).hexdigest(),
        "boundary_serializer_sha256": sha256(
            Path(__file__).with_name("boundary_records.py").read_bytes()
        ).hexdigest(),
        "conversation_serializer_sha256": sha256(
            Path(__file__).with_name("conversation_records.py").read_bytes()
        ).hexdigest(),
        "kernel_sources": kernels,
        "study_count": study_count,
        "series_count": len(records),
        "codes": codes,
        "failures": failures,
        "records": records,
    }


def write_receipt(out: Path, receipt: dict) -> None:
    """Write the receipt as JSON that refuses NaN, so a reading that was not made is never saved as a number."""
    (out / "receipt.json").write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + "\n"
    )


def gallery_entry(
    draw: Callable[[Path, str, Path], dict], out: Path, uid: str, target: Path
) -> dict:
    """One study's drawing outcome: `drawn` with the index's counts, or `not_drawn` with the reason."""
    try:
        index = draw(out, uid, target)
    except Exception as refusal:
        return {
            "study_uid": uid,
            "code": "not_drawn",
            "why": f"{type(refusal).__name__}: {refusal}",
        }
    return {
        "study_uid": uid,
        "code": "drawn",
        "out": str(target),
        "drawn": index["drawn"],
        "not_drawn": index["not_drawn"],
    }


def draw_galleries(out: Path, uids: tuple[str, ...]) -> list[dict]:
    """Draw every stage of every study from the saved run; a drawer that refuses is recorded, never raised."""
    # THE SAME COMMAND DRAWS. The founder, 2026-10-12: the drawing "is just the output of the
    # analysis, but since this is visual data, it can most effectively be judged visually, so why
    # not print? ... it should be absurdly cheap to put out, since it's just a printed copy of the
    # analysis that is already required." Thesis SS13.7 puts "drawing pictures" at the thin impure
    # edge beside "reading a movie, writing the output" -- which is here -- and its purpose clause
    # is "so pictures are a layer that can be switched off", which is `--no-pictures`.
    #
    # Imported INSIDE this function, which `main` calls only with pictures on: with pictures off
    # nothing pulls in Matplotlib, so this module stays importable in the ordinary environment,
    # where its tests run.
    from workbench.render.all_frames import draw_all

    pictures_root = Path(__file__).resolve().parents[2] / "data" / "pictures"
    return [
        gallery_entry(draw_all, out, uid, pictures_root / out.name / uid)
        for uid in uids
    ]


def summary_record(
    uids: tuple[str, ...],
    records: list[dict],
    codes: dict[str, int],
    pictures: list[dict] | str,
    failures: list[dict],
) -> dict:
    """What the command prints when it finishes: the counts and codes, the drawing outcome and the failures."""
    return {
        "study_count": len(uids),
        "series_count": len(records),
        "codes": codes,
        "pictures": pictures,
        "failures": failures,
    }


def main() -> None:
    """Parse the arguments, measure the studies, write the receipt, draw, and report."""
    parser = build_parser()
    args = parser.parse_args()
    check_arguments(parser, args)
    request = analysis_request(args)
    corpus = open_corpus(args.root)
    uids = select_uids(corpus.tables, args.split, args.uid)
    args.out.mkdir(parents=True, exist_ok=True)
    kernels_before = source_snapshot()
    verification = verification_record(args.detective_report)
    records, failures, studies = measure_studies(
        corpus, uids, request, args.out, kernels_before, verification
    )
    codes = record_codes(records)
    snapshot_code = snapshot_standing(kernels_before, source_snapshot())
    if snapshot_code == "changed":
        failures.append({"code": "source_changed_during_run"})
    write_receipt(
        args.out,
        receipt_record(
            request=request,
            verification=verification,
            studies=studies,
            records=records,
            failures=failures,
            kernels=kernels_before,
            snapshot_code=snapshot_code,
            codes=codes,
            study_count=len(uids),
            corpus=corpus.shape,
        ),
    )
    pictures = draw_galleries(args.out, uids) if args.pictures else "off"
    print(
        json.dumps(summary_record(uids, records, codes, pictures, failures), indent=2)
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
