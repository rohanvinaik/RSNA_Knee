"""Run Packet A through the production entry point and save its actual returned values."""

import argparse
import json
import platform
from collections import Counter
from dataclasses import asdict, fields
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np

from knee import collapse
from knee.lenses.digits import DIGIT_CODES
from knee.lenses.members import STANDING_CODES
from knee.lenses.places import SILENT
from knee.objects.analysis import AnalysisRequest
from knee.pipeline import run_study
from knee.predicates.findings import CODES as FINDING_CODES
from knee.relations.pair_codes import CODES as PAIRING_CODES
from knee.study.corpus import open_corpus
from knee.study.tables import labeled_uids
from knee.telemetry import recording
from workbench.measure.boundary_records import boundary_record
from workbench.measure.conversation_records import conversation_record
from workbench.measure.interior_records import interior_record


def package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def source_snapshot() -> dict[str, str]:
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("data/raw"))
    parser.add_argument("--uid", help="omit to measure all fully labeled studies")
    parser.add_argument("--tile-mm", type=float, required=True)
    parser.add_argument("--span-mm", type=float, required=True)
    parser.add_argument("--samples", type=int, required=True)
    parser.add_argument(
        "--axis", choices=("superior", "left", "posterior"), required=True
    )
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
    args = parser.parse_args()
    if args.samples < 1 or not np.isfinite(args.span_mm) or args.span_mm <= 0:
        parser.error("positive span-mm and samples required")
    if args.conversation and args.prominence_mm is None:
        # `AnalysisRequest` couples the two, and would raise `invalid_conversation_request`. Said
        # here instead, in words, with the way out named -- a refusal is a verdict, not a crash.
        parser.error(
            "the conversation reads boundaries, so it needs --prominence-mm; "
            "pass --no-conversation to run the series in isolation"
        )
    directions = {
        "superior": (0.0, 0.0, 1.0),
        "left": (1.0, 0.0, 0.0),
        "posterior": (0.0, 1.0, 0.0),
    }
    request = AnalysisRequest(
        args.tile_mm,
        tuple(np.linspace(-args.span_mm, args.span_mm, args.samples))
        if args.samples > 1
        else (0.0,),
        directions[args.axis],
        args.backend,
        prominence_mm=args.prominence_mm,
        conversation=args.conversation,
    )
    corpus = open_corpus(args.root)
    uids = (args.uid,) if args.uid else labeled_uids(corpus.tables)
    args.out.mkdir(parents=True, exist_ok=True)
    kernels_before = source_snapshot()
    verification = {"standing": "not_supplied"}
    if args.detective_report is not None:
        verification = {
            "report_sha256": sha256(args.detective_report.read_bytes()).hexdigest(),
            "snapshot": json.loads(args.detective_report.read_text()),
            "profile_codes_source_sha256": sha256(
                Path(collapse.__file__).parent.joinpath("profile_codes.py").read_bytes()
            ).hexdigest(),
        }
    records, failures, studies = [], [], []
    for uid in uids:
        start = len(records)
        try:
            with recording() as run_ledger:
                result = run_study(corpus, uid, request)
            events = [asdict(event) for event in run_ledger.events()]
            for series in result.series:
                measurement = series.measurements
                if measurement is None:
                    raise RuntimeError("missing_measurement_record")
                record = {
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
                    "requested_backend": args.backend,
                    "effective_backend": "not_invoked",
                }
                # THE WHOLE REGIME KEY, not one field of it. It is every reading the field stage
                # already computed once per series (twenty-three since the second member was
                # seated), and until 2026-10-12 this writer took `background_split` and dropped
                # the rest. The founder: "we compute the required object, we drop it ... any
                # compute process here is done for the purpose of visual reasoning. If the lenses
                # don't have information that they can literally show, then what are we doing?"
                # A reading the field could not make stays None.
                regime = series.regime
                # THE STUDY STAGE'S OWN RECORD (task 6.9): the series' stack codes, its per-slice
                # codes, and the walk through the stack the stage retains -- which the writer never
                # saved, so the study frame could draw only the objects stage's selected plane.
                record["stack"] = list(series.stack)
                record["study"] = {
                    "slice_codes": list(series.slice_codes),
                    "walk_indices": list(series.walk_indices),
                    "walk_array": "study_walk" if series.walk is not None else None,
                }
                record["regime"] = {
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
                split = (
                    series.regime.background_split
                    if series.regime is not None
                    else np.nan
                )
                record["background_split"] = (
                    float(split) if np.isfinite(split) else None
                )
                record["background_annotation_code"] = (
                    "measured"
                    if np.isfinite(split) and measurement.acquired_plane is not None
                    else "unavailable"
                )
                arrays = {}
                if series.walk is not None:
                    arrays["study_walk"] = series.walk
                # The pairing reading is the relations stage's own since task 6.3; it is saved
                # under its own key, exactly as before, from where the stage keeps it.
                pairings = (
                    series.relations.pairings if series.relations is not None else None
                )
                if pairings is not None:
                    record["pairings"] = {
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
                    arrays.update(
                        pairing_source_labels=pairings.source_labels,
                        pairing_far_labels=pairings.far_labels,
                        pairing_trace_codes=pairings.trace_codes,
                        pairing_outcome_codes=pairings.outcome_codes,
                        pairing_positions_rc=pairings.positions_rc,
                        pairing_contributor_labels=pairings.contributor_labels,
                        pairing_band_limits_mm=pairings.band_limits_mm,
                    )
                if series.lenses is not None:
                    # EVERY SEATED MEMBER is serialised, each naming its own population, plus
                    # the standing between them per place. No field holds "the" reading: the
                    # founder, 2026-10-12, "the pipeline should keep everything, including
                    # where things conflict", so a consumer that wants one digit per place
                    # must come to him for the rule rather than find one written here.
                    reading = series.lenses
                    plane_index = measurement.slice_index
                    depth = reading.members[0].codes.shape[0] if reading.members else 0
                    plane_read = plane_index is not None and 0 <= plane_index < depth
                    record["lenses"] = {
                        "members": [
                            {
                                "population": member.population,
                                "code": member.code,
                                "why": member.why,
                                "low_edge": member.low_edge
                                if member.low_edge is not None
                                and np.isfinite(member.low_edge)
                                else None,
                                "high_edge": member.high_edge
                                if member.high_edge is not None
                                and np.isfinite(member.high_edge)
                                else None,
                                "population_count": member.population_count,
                                "minimum_population": member.minimum_population,
                                "normalisation": member.normalisation,
                                "counts": member.counts,
                                "picture_code": member.code
                                if plane_read
                                else "item_unread",
                                "codes_array": f"lens_codes_{member.population}",
                                "digits_array": f"lens_digits_{member.population}",
                            }
                            for member in reading.members
                        ],
                        "code_names": DIGIT_CODES,
                        "standing_names": STANDING_CODES,
                        "standing_counts": reading.standing_counts,
                        "standings_array": "lens_standings",
                        "digit_silence": SILENT,
                        "map_scope": "complete native volume (slice,row,column)",
                        "saved_scope": "selected native plane (row,column)",
                    }
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
                if series.ownership is not None:
                    # EVERY SEATED MEMBER, one partition per parse (task 6.2), each under its
                    # own arrays, plus where the solitary and concurrent claims disagree. No
                    # key holds "the" partition: the pipeline keeps everything it computes.
                    ownership = series.ownership
                    record["ownership"] = {
                        "code": ownership.code,
                        "why": ownership.why,
                        "comparison": ownership.comparison,
                        "disagreeing_places": ownership.disagreeing_places,
                        "disagreement_array": "ownership_disagreement",
                        "members": [
                            {
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
                            for member in ownership.members
                        ],
                    }
                    for member in ownership.members:
                        arrays[f"ownership_{member.parse}_claims"] = (
                            member.reading.claims
                        )
                        arrays[f"ownership_{member.parse}_residual"] = (
                            member.reading.residual
                        )
                    arrays["ownership_disagreement"] = ownership.disagreement
                if series.relations is not None:
                    relations = series.relations
                    record["relations"] = {
                        "code": relations.code,
                        "why": relations.why,
                        "interstices": [
                            {
                                "kind": item.kind,
                                "first": item.first,
                                "second": item.second,
                                "series_uid": item.series_uid,
                                "provenance": item.provenance,
                            }
                            for item in relations.interstices
                        ],
                        "pairings_code": pairings.code
                        if pairings is not None
                        else None,
                    }
                if series.bundles is not None:
                    bundles = series.bundles
                    record["vectors"] = {
                        "code": bundles.code,
                        "why": bundles.why,
                        "subject_kind": bundles.subject_kind,
                        "planes_read": bundles.planes_read,
                        "profiles": [
                            {
                                "index": profile.index,
                                "places": profile.places,
                                "banks": [
                                    {
                                        "name": bank.name,
                                        "source_stage": bank.source_stage,
                                        "status": bank.status,
                                        "rows": dict(bank.rows),
                                        "why": bank.why,
                                    }
                                    for bank in profile.banks
                                ],
                            }
                            for profile in bundles.profiles
                        ],
                    }
                if record["background_annotation_code"] == "measured":
                    arrays["background_mask"] = measurement.acquired_plane <= split
                if measurement.acquired_plane is not None:
                    arrays["acquired_plane"] = measurement.acquired_plane
                if (
                    measurement.points_rc is not None
                    and measurement.normals_rc is not None
                ):
                    arrays.update(
                        points_rc=measurement.points_rc,
                        normals_rc=measurement.normals_rc,
                    )
                if measurement.frame is not None:
                    arrays.update(
                        origin_lps=measurement.frame.origin_lps,
                        basis_lps=measurement.frame.basis_lps,
                    )
                    record["spacing_rc_mm"] = measurement.frame.spacing_rc
                if measurement.squint is not None:
                    q = measurement.squint
                    arrays.update(
                        median=q.median,
                        minimum=q.minimum,
                        maximum=q.maximum,
                        coverage=q.coverage,
                        bounds_rc=q.bounds_rc,
                    )
                    record["tile_shape_rc"] = q.tile_shape_rc
                if measurement.profiles is not None:
                    p = measurement.profiles
                    arrays.update(
                        samples=p.samples,
                        valid=p.valid,
                        slopes=p.slopes,
                        distances_mm=p.distances_mm,
                    )
                    record.update(
                        support_code=p.support_code,
                        support_codes=p.support_codes,
                        requested_backend=p.requested_backend,
                        effective_backend=p.effective_backend,
                        coordinate_evaluations=p.samples.size,
                        source_read_upper_bound=4 * p.samples.size,
                        sample_output_bytes=p.samples.nbytes + p.valid.nbytes,
                    )
                if measurement.interiors is not None:
                    record["interiors"], interior_arrays = interior_record(
                        measurement.interiors
                    )
                    arrays.update(interior_arrays)
                if measurement.boundaries is not None:
                    record["boundaries"], boundary_arrays = boundary_record(
                        measurement.boundaries
                    )
                    arrays.update(boundary_arrays)
                if series.conversation is not None:
                    record["conversation"], conversation_arrays = conversation_record(
                        series.conversation, args.backend
                    )
                    arrays.update(conversation_arrays)
                record["arrays"] = {
                    name: {
                        "shape": a.shape,
                        "dtype": a.dtype.str,
                        "digest": array_digest(a),
                        "bytes": a.nbytes,
                    }
                    for name, a in arrays.items()
                }
                source_dir = (
                    args.root
                    / ("train_series" if result.split == "train" else "test_series")
                    / uid
                    / series.series_uid
                )
                record["sources"] = {
                    str(path.relative_to(args.root)): sha256(
                        path.read_bytes()
                    ).hexdigest()
                    for path in sorted(source_dir.glob("*.dcm"))
                }
                artifact = Path(uid) / f"{series.series_uid}.npz"
                record["artifact"] = str(artifact)
                (args.out / artifact).parent.mkdir(parents=True, exist_ok=True)
                np.savez_compressed(args.out / artifact, allow_pickle=False, **arrays)
                records.append(record)
            study_entry = {
                "study_uid": uid,
                "code": "complete",
                "series_written": len(records) - start,
                "reached": result.reached,
                # The roster: every stage with the code it returned (task 6.6). Coverage is a
                # population; `reached` beside it is only the telemetry scalar it always was.
                "attendance": [list(entry) for entry in result.attendance],
                "ledger": events,
            }
            if result.findings is not None:
                # PER STUDY, not per series: a finding is a statement about the knee. Serialised
                # as returned -- index, structural requirement, named code, reason, and the
                # subject facts it READ from relations (task 6.4). No number is written for any
                # finding, because a confidence is knee.output's lossy projection of this record
                # and the projection has not been declared.
                study_entry["findings"] = {
                    "code": result.findings.code,
                    "why": result.findings.why,
                    "code_names": FINDING_CODES,
                    "series_with_population": result.findings.series_with_population,
                    "series_with_construction": result.findings.series_with_construction,
                    "series_with_profiles": result.findings.series_with_profiles,
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
                        for finding in result.findings.findings
                    ],
                }
            if result.output is not None:
                # THE COMPANION RECORD, written in the same run (task 6.8): the twelve joined to
                # the competition's columns by the declared table. Rows are refused by name
                # while the projection is undeclared, and that refusal is saved as the fact.
                study_entry["output"] = {
                    "code": result.output.code,
                    "why": result.output.why,
                    "projection": None
                    if result.output.projection is None
                    else asdict(result.output.projection),
                    "companion": [
                        {
                            "index": row.index,
                            "column": row.column,
                            "code": row.code,
                            "reason": row.reason,
                            "subjects": list(row.subjects),
                            "candidates": row.candidates,
                        }
                        for row in result.output.companion
                    ],
                    "submission_rows": None
                    if result.output.rows is None
                    else [[column, value] for column, value in result.output.rows],
                }
            studies.append(study_entry)
            print(f"measured {uid}: {len(result.series)} series", flush=True)
        except Exception as error:
            failures.append(
                {"study_uid": uid, "type": type(error).__name__, "message": str(error)}
            )
            studies.append(
                {
                    "study_uid": uid,
                    "code": "partial" if len(records) > start else "failed",
                    "series_written": len(records) - start,
                }
            )
            print(f"unreadable {uid}: {type(error).__name__}: {error}", flush=True)
        save_study_checkpoint(
            args.out,
            studies[-1],
            request,
            kernels_before,
            verification,
            records[start:],
            [f for f in failures if f.get("study_uid") == uid],
        )
    codes = Counter(record["code"] for record in records)
    kernels_after = source_snapshot()
    if kernels_after != kernels_before:
        failures.append({"code": "source_changed_during_run"})
    receipt = {
        "schema": "physical-measurements-v2",
        "source_snapshot_code": "unchanged"
        if kernels_before == kernels_after
        else "changed",
        "detective": verification,
        "studies": studies,
        "scope": "middle acquired plane per series, not full-volume contour tracing",
        "request": asdict(request),
        "environment": {
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
        },
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
        "kernel_sources": kernels_before,
        "study_count": len(uids),
        "series_count": len(records),
        "codes": dict(codes),
        "failures": failures,
        "records": records,
    }
    (args.out / "receipt.json").write_text(
        json.dumps(receipt, indent=2, allow_nan=False) + "\n"
    )

    # THE SAME COMMAND DRAWS. The founder, 2026-10-12: the drawing "is just the output of the
    # analysis, but since this is visual data, it can most effectively be judged visually, so why
    # not print? ... it should be absurdly cheap to put out, since it's just a printed copy of the
    # analysis that is already required." Thesis SS13.7 puts "drawing pictures" at the thin impure
    # edge beside "reading a movie, writing the output" -- which is here -- and its purpose clause
    # is "so pictures are a layer that can be switched off", which is `--no-pictures`.
    #
    # Imported INSIDE the branch: with pictures off nothing pulls in Matplotlib, so this module
    # stays importable in the ordinary environment, where its tests run.
    galleries = []
    if args.pictures:
        from workbench.render.all_frames import draw_all

        pictures_root = Path(__file__).resolve().parents[2] / "data" / "pictures"
        for uid in uids:
            target = pictures_root / args.out.name / uid
            try:
                index = draw_all(args.out, uid, target)
            except Exception as refusal:
                galleries.append(
                    {
                        "study_uid": uid,
                        "code": "not_drawn",
                        "why": f"{type(refusal).__name__}: {refusal}",
                    }
                )
                continue
            galleries.append(
                {
                    "study_uid": uid,
                    "code": "drawn",
                    "out": str(target),
                    "drawn": index["drawn"],
                    "not_drawn": index["not_drawn"],
                }
            )

    print(
        json.dumps(
            {
                "study_count": len(uids),
                "series_count": len(records),
                "codes": dict(codes),
                "pictures": "off" if not args.pictures else galleries,
                "failures": failures,
            },
            indent=2,
        )
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
