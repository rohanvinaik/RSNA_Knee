"""Run facts for OpenSpec task 3.8a: what the object stage actually produces on one real study.

The other half of 3.8a is code facts, in `docs/chapters/02-collapse/readings/
what-the-machinery-does-code-facts.md`. They are kept apart on purpose: a reader can establish what
the code does, and only a run can establish what the data does.

This ARRANGES values the production stage already returned and measures nothing of its own, so a
number here is evidence about the stage rather than about this file. It runs one study through the
real entry point (`knee.pipeline.run_study`), never from a saved array, because `just
interiors-status` and `just conversation-status` report the saved B1/B2 runs stale against current
source.

**No parameter is chosen here.** The analysis request is read from a prior run's receipt, so the
tile, the span, the samples, the axis, the backend and the prominence are the ones the record
already used. A bar invented in a probe is a bar nobody wrote down.

Usage:
    PYTHONPATH=.:src .venv/bin/python -m workbench.measure.machinery_facts \
        --receipt data/measurements/<run>/receipt.json [--root data/raw] [--uid UID]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from knee.objects.analysis import AnalysisRequest
from knee.objects.interiors import EDGE_KINDS, TRACE_CODES
from knee.pipeline import run_study
from knee.study.corpus import open_corpus

GUARDS = {0: "not_in_search", 1: "low_signal", 2: "missing", 3: "virtual_frame"}


def counted(values: np.ndarray, names: dict[str, int]) -> str:
    """`name=count` for each named code actually present, so an absent code is absent, not zero."""
    present = [
        f"{name}={int(np.count_nonzero(values == code))}"
        for name, code in names.items()
        if np.any(values == code)
    ]
    return "  ".join(present) if present else "none"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("data/raw"))
    parser.add_argument("--uid", help="omit to take the receipt's first study")
    args = parser.parse_args()

    receipt = json.loads(args.receipt.read_text())
    request = AnalysisRequest(**receipt["request"])
    uid = args.uid or receipt["studies"][0]["study_uid"]
    print(f"request, from {args.receipt} (nothing chosen here):")
    for field, value in receipt["request"].items():
        print(f"  {field}: {value}")
    print(f"study: {uid}\n")

    result = run_study(open_corpus(args.root), uid, request)

    for series in result.series:
        measurement = series.measurements
        if measurement is None or measurement.interiors is None:
            print(f"{series.view}  {series.series_uid}: no interior reading\n")
            continue
        reading = measurement.interiors
        census = measurement.boundaries
        plane = reading.dark.shape
        spacing = (
            measurement.frame.spacing_rc
            if measurement.frame is not None
            else (1.0, 1.0)
        )
        place_mm2 = float(spacing[0]) * float(spacing[1])

        available = reading.available
        dark = reading.dark
        interior = available & ~dark
        labels = reading.labels
        unclaimed = interior & (labels == 0)

        print(
            f"=== {series.view}  slice {measurement.slice_index}  {plane[0]}x{plane[1]}"
        )
        print(
            f"    code={reading.code}  spacing_rc={tuple(round(float(s), 4) for s in spacing)} mm"
            f"  thickness={measurement.slice_thickness_mm} mm"
        )
        print(
            f"    available={int(available.sum())}  dark={int(dark.sum())}"
            f"  interior={int(interior.sum())}"
            f"  INTERIOR CLAIMED BY NO TERRITORY={int(unclaimed.sum())}"
        )
        print(
            f"    distance_guard over interior: {counted(reading.distance_guard[interior], {v: k for k, v in GUARDS.items()})}"
        )

        kinds = reading.edge_kinds
        traces = reading.trace_codes
        regions = reading.edge_regions
        places = np.unique(reading.edge_points_rc, axis=0)
        print(
            f"    directed interfaces={len(kinds)}  distinct half-place points={len(places)}"
            f"  (an ordered chain is built by nothing: see the code-facts reading, section 8)"
        )
        print(f"    edge kinds : {counted(kinds, EDGE_KINDS)}")
        print(f"    trace codes: {counted(traces, TRACE_CODES)}")

        print("    edge kind x trace code:")
        for kind_name, kind_code in EDGE_KINDS.items():
            row = traces[kinds == kind_code]
            if not len(row):
                continue
            print(f"      {kind_name:<20} {counted(row, TRACE_CODES)}")

        if census is None:
            print()
            continue
        order = np.argsort(
            [int(np.count_nonzero(labels == label)) for label in census.labels]
        )
        print(
            "    territories, smallest first (area, depth, how its edges type, how many bracketed):"
        )
        for at in order:
            label = int(census.labels[at])
            held = int(np.count_nonzero(labels == label))
            mine = regions == label
            print(
                f"      #{label:<4} {held:>7} places  {held * place_mm2:>9.1f} mm2"
                f"  peak={float(census.peak_mm[at]):>6.2f} mm"
                f"  edges={int(mine.sum()):>5}"
                f"  bracketed={int(np.count_nonzero(traces[mine] == TRACE_CODES['bracketed'])):>5}"
                f"  | {counted(kinds[mine], EDGE_KINDS)}"
            )
        print()


if __name__ == "__main__":
    main()
