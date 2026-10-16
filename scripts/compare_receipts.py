"""Two runs' receipts compared record by record: whether every record, its decisions and its saved
arrays by their digests, is the same in both, each study's telemetry set aside. How a change meant to
leave the outputs alone is checked (`AGENTS.md`, "Running and testing"): copy a run's receipts
aside, run the change, and compare the receipts from before it with those after.

With `--borders-aside` the border readings are set aside too: the four border arrays and the counts
of what they found, which only a run that draws reads (`run_interiors.py --draw`). Where both
receipts hold a record's border readings they are still compared, and reported apart. With
`--study-uid` only those studies' records are compared, and the receipts' other entries (the
request, the silences) are compared only when every study is.

Run: `.venv/bin/python scripts/compare_receipts.py <before receipt.json> <after receipt.json>
[--borders-aside] [--study-uid <uid> ...]`. It prints what differs and exits 1 when anything does.
"""

import argparse
import copy
import json
import sys
from pathlib import Path

# The border readings a record keeps where its run drew (`run_interiors.slice_record`), and the
# counts of what they found (`run_interiors.lens_of`).
BORDER_ARRAYS = (
    "b1_edge_points_rc",
    "b1_edge_normals_rc",
    "b1_trace_codes",
    "b1_trace_points_rc",
)
BORDER_COUNTS = ("edge_counts", "trace_counts", "backend")


def record_key(record: dict) -> tuple[str, str, str | None]:
    """A record's study, its series, and the part whose own slice it is (None for a middle slice)."""
    return (
        record["study_uid"],
        record["series_uid"],
        record.get("main_slice", {}).get("object"),
    )


def holds_borders(record: dict) -> bool:
    return any(name in record.get("arrays", {}) for name in BORDER_ARRAYS)


def comparable(record: dict, borders_aside: bool) -> dict:
    """The record as compared: its telemetry set aside, and with `borders_aside` its border
    readings."""
    record = copy.deepcopy(record)
    record.pop("telemetry", None)
    if borders_aside:
        for name in BORDER_ARRAYS:
            record.get("arrays", {}).pop(name, None)
        for name in BORDER_COUNTS:
            record.get("interiors", {}).pop(name, None)
    return record


def borders_of(record: dict) -> dict:
    """A record's border readings: their arrays' digests and the counts of what they found."""
    return {
        "arrays": {name: record["arrays"].get(name) for name in BORDER_ARRAYS},
        "counts": {
            name: record.get("interiors", {}).get(name) for name in BORDER_COUNTS
        },
    }


def compare(
    before: dict, after: dict, borders_aside: bool, studies: frozenset[str]
) -> dict:
    """What differs between two receipts: the records only one holds; each record whose compared
    fields differ, with those fields; how many records on each side hold border readings and, where
    both do, which differ; and, when every study is compared, which of the other entries differ."""

    def records(receipt: dict) -> dict:
        return {
            record_key(r): r
            for r in receipt["records"]
            if not studies or r["study_uid"] in studies
        }

    old, new = records(before), records(after)
    common = sorted(set(old) & set(new), key=str)
    differing = {}
    for key in common:
        first = comparable(old[key], borders_aside)
        second = comparable(new[key], borders_aside)
        fields = sorted(
            f for f in set(first) | set(second) if first.get(f) != second.get(f)
        )
        if fields:
            differing[key] = fields
    both = [k for k in common if holds_borders(old[k]) and holds_borders(new[k])]
    entries = (
        []
        if studies
        else sorted(
            name
            for name in (set(before) | set(after)) - {"records", "telemetry"}
            if before.get(name) != after.get(name)
        )
    )
    return {
        "records": (len(old), len(new)),
        "only_before": sorted(set(old) - set(new), key=str),
        "only_after": sorted(set(new) - set(old), key=str),
        "differing": differing,
        "holding_borders": (
            sum(holds_borders(r) for r in old.values()),
            sum(holds_borders(r) for r in new.values()),
        ),
        "borders_differing": [
            k for k in both if borders_of(old[k]) != borders_of(new[k])
        ],
        "entries_differing": entries,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument(
        "--borders-aside",
        action="store_true",
        help="set aside the border readings, which only a run that draws reads",
    )
    parser.add_argument("--study-uid", nargs="+", default=[])
    args = parser.parse_args()
    found = compare(
        json.loads(args.before.read_text()),
        json.loads(args.after.read_text()),
        args.borders_aside,
        frozenset(args.study_uid),
    )
    before_count, after_count = found["records"]
    print(f"records: before {before_count}, after {after_count}")
    print(f"only before: {found['only_before']}")
    print(f"only after: {found['only_after']}")
    for key, fields in found["differing"].items():
        print(f"differs: {key}: {fields}")
    aside = ", border readings aside" if args.borders_aside else ""
    print(f"records that differ{aside}: {len(found['differing'])}")
    holding_before, holding_after = found["holding_borders"]
    print(
        f"records holding border readings: before {holding_before}, after {holding_after}; "
        f"where both do, differing: {len(found['borders_differing'])}"
    )
    if args.study_uid:
        print("other entries: not compared when studies are chosen")
    else:
        print(f"other entries differing: {found['entries_differing'] or 'none'}")
    differs = any(
        found[name]
        for name in (
            "only_before",
            "only_after",
            "differing",
            "borders_differing",
            "entries_differing",
        )
    )
    sys.exit(1 if differs else 0)


if __name__ == "__main__":
    main()
