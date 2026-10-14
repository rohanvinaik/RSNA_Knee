"""Hamilton's development graph observes one pass through the production route."""

from pathlib import Path

from knee.lenses.places import STANDING_VALUES, LensesReading
from knee.objects.analysis import AnalysisRequest, SeriesMeasurement
from knee.objects.boundaries import PAIR_CODE_VALUES
from knee.objects.conversation import SeriesConversation
from knee.pipeline import StudyRun, open_and_run
from knee.relations.pairings import PairingReading


def study_run(
    corpus_root: Path, study_uid: str, analysis_request: AnalysisRequest
) -> StudyRun:
    return open_and_run(corpus_root, study_uid, analysis_request)


def series_measurements(study_run: StudyRun) -> tuple[SeriesMeasurement, ...]:
    return tuple(s.measurements for s in study_run.series if s.measurements is not None)


def squint_tiles(series_measurements: tuple[SeriesMeasurement, ...]) -> int:
    return sum(
        m.squint.median.size for m in series_measurements if m.squint is not None
    )


def native_samples(series_measurements: tuple[SeriesMeasurement, ...]) -> int:
    return sum(
        m.profiles.samples.size for m in series_measurements if m.profiles is not None
    )


def support_records(
    series_measurements: tuple[SeriesMeasurement, ...],
) -> tuple[str, ...]:
    return tuple(
        m.profiles.support_code if m.profiles is not None else m.code
        for m in series_measurements
    )


def interior_counts(
    series_measurements: tuple[SeriesMeasurement, ...],
) -> dict[str, int]:
    readings = [m.interiors for m in series_measurements if m.interiors is not None]
    if not readings:
        return {}
    return {
        "territories": sum(int(r.labels.max(initial=0)) for r in readings),
        "directed_edges": sum(len(r.edge_regions) for r in readings),
        "boundary_coordinate_evaluations": sum(
            r.profiles.samples.size for r in readings if r.profiles is not None
        ),
    }


def boundary_counts(
    series_measurements: tuple[SeriesMeasurement, ...],
) -> dict[str, int]:
    censuses = [m.boundaries for m in series_measurements if m.boundaries is not None]
    if not censuses:
        return {}
    read = PAIR_CODE_VALUES["read"]
    return {
        "census_territories": sum(len(c.labels) for c in censuses),
        "touching_pairs": sum(len(c.pair_labels) for c in censuses),
        "divide_sites": sum(int(c.pair_sites.sum()) for c in censuses),
        "pairs_with_a_read_relief": sum(
            int((c.pair_codes == read).sum()) for c in censuses
        ),
    }


def conversations(study_run: StudyRun) -> tuple[SeriesConversation, ...]:
    return study_run.conversations


def lens_readings(study_run: StudyRun) -> tuple[LensesReading, ...]:
    return tuple(s.lenses for s in study_run.series if s.lenses is not None)


def lens_counts(lens_readings: tuple[LensesReading, ...]) -> dict[str, int]:
    # Counted over SEATED MEMBERS, not over series: the work is per member, and a member that
    # could not place its pair still wrote a map of its own named silence. `dissenting_places`
    # is kept as counted work in its own right -- it is where two correct overlapping readings
    # differ, which the founder names as the most informative case rather than an error rate.
    members = [member for reading in lens_readings for member in reading.members]
    return {
        "lens_seated_members": len(members),
        "lens_native_places": sum(member.codes.size for member in members),
        "lens_output_bytes": sum(
            member.codes.nbytes + member.digits.nbytes for member in members
        )
        + sum(reading.standings.nbytes for reading in lens_readings),
        "lens_dissenting_places": sum(
            reading.standing_counts[STANDING_VALUES["dissent"]]
            for reading in lens_readings
        ),
    }


def pairing_readings(study_run: StudyRun) -> tuple[PairingReading, ...]:
    # The pairing reading lives inside the relations record since task 6.3: the stage reads it
    # itself and carries it, so the graph reads it from where the stage keeps it.
    return tuple(
        s.relations.pairings
        for s in study_run.series
        if s.relations is not None and s.relations.pairings is not None
    )


def pairing_counts(pairing_readings: tuple[PairingReading, ...]) -> dict[str, int]:
    return {
        "pairing_profiles": sum(r.outcome_codes.size for r in pairing_readings),
        "sample_supported_pairs": sum(r.counts["paired"] for r in pairing_readings),
    }


def conversation_counts(
    conversations: tuple[SeriesConversation, ...],
) -> dict[str, int]:
    if not conversations:
        return {}
    peers = [peer for reading in conversations for peer in reading.exchanges]
    return {
        "exchange_pairs": len(peers),
        "exchanged_source_edges": sum(len(p.source_edge_indices) for p in peers),
        "exchange_coordinate_evaluations": sum(
            p.profiles.samples.size for p in peers if p.profiles is not None
        ),
        "raster_cell_visits": sum(sum(p.raster_visits) for p in peers),
        "concurrent_pieces": sum(len(r.concurrent_parents) - 1 for r in conversations),
        "conditional_pieces": sum(
            len(r.conditional_parents) - 1 for r in conversations
        ),
    }


def work_counts(
    native_samples: int,
    squint_tiles: int,
    interior_counts: dict[str, int],
    boundary_counts: dict[str, int],
    conversation_counts: dict[str, int],
    lens_counts: dict[str, int],
    pairing_counts: dict[str, int],
) -> dict[str, int]:
    return {
        "profile_coordinate_evaluations": native_samples,
        "source_read_upper_bound": 4 * native_samples,
        "profile_sample_output_bytes": 9 * native_samples,
        "squint_tiles": squint_tiles,
        **interior_counts,
        **boundary_counts,
        **conversation_counts,
        **lens_counts,
        **pairing_counts,
    }
