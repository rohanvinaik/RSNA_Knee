"""Run Packet A through the production entry point and save its actual returned values."""

import argparse
import json
import platform
from collections import Counter
from dataclasses import asdict
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np

from knee import collapse
from knee.lenses.digits import DIGIT_CODES
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
            conversations = {r.series_uid: r for r in result.conversations}
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
                if series.pairings is not None:
                    pairings = series.pairings
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
                    lenses = series.lenses
                    plane_index = measurement.slice_index
                    plane_read = (
                        plane_index is not None
                        and 0 <= plane_index < lenses.codes.shape[0]
                    )
                    record["lenses"] = {
                        "code": lenses.code,
                        "why": lenses.why,
                        "low_edge": lenses.low_edge
                        if lenses.low_edge is not None and np.isfinite(lenses.low_edge)
                        else None,
                        "high_edge": lenses.high_edge
                        if lenses.high_edge is not None
                        and np.isfinite(lenses.high_edge)
                        else None,
                        "population_count": lenses.population_count,
                        "minimum_population": lenses.minimum_population,
                        "normalisation": lenses.normalisation,
                        "code_names": DIGIT_CODES,
                        "digit_silence": SILENT,
                        "counts": lenses.counts,
                        "map_scope": "complete native volume (slice,row,column)",
                        "saved_scope": "selected native plane (row,column)",
                        "picture_code": lenses.code if plane_read else "item_unread",
                    }
                    arrays.update(
                        lens_codes=lenses.codes[plane_index]
                        if plane_read
                        else np.empty((0, 0), dtype=np.uint8),
                        lens_digits=lenses.digits[plane_index]
                        if plane_read
                        else np.empty((0, 0), dtype=np.int8),
                    )
                if series.ownership is not None:
                    ownership = series.ownership
                    record["ownership"] = {
                        "code": ownership.code,
                        "why": ownership.why,
                        "claimed_places": ownership.claimed_places,
                        "residual_places": ownership.residual_places,
                        "unavailable_places": ownership.unavailable_places,
                        "objects": int(ownership.objects),
                    }
                    arrays.update(
                        ownership_claims=ownership.claims,
                        ownership_residual=ownership.residual,
                    )
                if series.relations is not None:
                    relations = series.relations
                    record["relations"] = {
                        "code": relations.code,
                        "why": relations.why,
                        "interstices": relations.interstices,
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
                if series.series_uid in conversations:
                    record["conversation"], conversation_arrays = conversation_record(
                        conversations[series.series_uid], args.backend
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
                "ledger": events,
            }
            if result.findings is not None:
                # PER STUDY, not per series: a finding is a statement about the knee. Serialised
                # as returned -- index, structural requirement, named code and reason. No number
                # is written for any finding, because a confidence is knee.output's lossy
                # projection of this record and the projection has not been declared.
                study_entry["findings"] = {
                    "code": result.findings.code,
                    "why": result.findings.why,
                    "code_names": FINDING_CODES,
                    "series_with_population": result.findings.series_with_population,
                    "series_with_construction": result.findings.series_with_construction,
                    "findings": [
                        {
                            "index": finding.index,
                            "requirement": finding.requirement,
                            "code": finding.code,
                            "reason": finding.reason,
                        }
                        for finding in result.findings.findings
                    ],
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
