"""Write near-miss-records.json and near-miss-table.md for a published memory (Lane A, read-only).

Reads a published memory and the inference records its growth rounds read; writes only into ``--out``.
Nothing here publishes memory, writes a censor or a split, or changes an existing file.

    .venv/bin/python scripts/near_miss_report.py \
        --memory <published-memory> --inference-root data/readings --out <existing-output-folder>

Stages: enumerate every reviewer correction in the memory; join each to the inference record that
produced its proposal (only a recognition-derived admission names one); compare, for a traced one,
the failure's bundle with each positive precedent that actually spoke; write the records and the
table.  It can also survey a caller-supplied work root; no survey root is assumed.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import lzma
import os
import sys
import time
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from knee.diagnosis import squint_near_miss as nm

REPO = Path(__file__).resolve().parents[1]
READINGS = "data/readings"
SKIP_DIRS = frozenset(
    {"__pycache__", ".pytest_cache", "sheets", "montages", "pictures", "contact-sheets"}
)
TOP_READINGS_SHOWN = 8
RECALL_WORDS = (
    "cosine",
    "recall",
    "nearest",
    "speak",
    "resembl",
    "envelope",
    "precedent",
    "kline",
    "identity",
)


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def canonical_sha256(value: object) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), default=repr)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_xz_json(path: str) -> dict[str, Any]:
    with lzma.open(path, "rt") as handle:
        return json.load(handle)


def relative(path: str) -> str:
    try:
        return os.path.relpath(path, REPO)
    except ValueError:
        return path


def study_record_files(root: str) -> list[str]:
    """Per-study inference record files (``<study uid>.json.xz``) under a root, in a stable order."""
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIRS)
        found.extend(
            os.path.join(dirpath, name)
            for name in sorted(filenames)
            if name.endswith(".json.xz") and name.startswith("1.")
        )
    return found


# ----------------------------------------------------------------------------- the inference records


class RecordFinder:
    """Find an inference record by the sha256 of its file bytes, which a growth lineage names.

    The index is built, by hashing bytes only, the first time a sha is asked for.
    """

    def __init__(self, roots: Sequence[str]) -> None:
        self.roots = list(roots)
        self.index: dict[str, list[str]] | None = None
        self.files_hashed = 0
        self._cache: dict[str, dict[str, Any]] = {}

    def _build(self) -> None:
        index: dict[str, list[str]] = {}
        for root in self.roots:
            for path in study_record_files(root):
                index.setdefault(sha256_file(path), []).append(path)
                self.files_hashed += 1
        self.index = index
        log(
            f"hashed {self.files_hashed} inference record files under {len(self.roots)} root(s)"
        )

    def __call__(self, sha: str) -> tuple[str, Mapping[str, Any]] | None:
        if self.index is None:
            self._build()
        paths = (self.index or {}).get(sha)
        if not paths:
            return None
        path = paths[0]
        if path not in self._cache:
            if len(self._cache) >= 2:
                self._cache.pop(next(iter(self._cache)))
            self._cache[path] = load_xz_json(path)
        return relative(path), self._cache[path]


# ----------------------------------------------------------------------------- the bundles


class Bundles:
    """The identity reader's own bundles at one scale: its positive seeds and its negative cases.

    These are the entries ``prepare_identity`` compares (banks already selected at each case's
    confirmed or rejected views).  The reader keeps them in private attributes; this adapter is
    the one place that reads them.
    """

    def __init__(self, memory: Mapping[str, Any], scale: str) -> None:
        from knee.diagnosis.squint_identity import prepare_identity

        prepared = prepare_identity(memory, scale=scale)
        if prepared.get("outcome") != "prepared":
            raise SystemExit(
                f"identity preparation refused at scale {scale}: {dict(prepared)}"
            )
        self.scale = scale
        self.preparation = dict(prepared)
        self.seeds = [self._plain(entry) for entry in prepared._seeds]
        self.negatives = [self._plain(entry) for entry in prepared._negatives]
        self.seeds_by_id = {entry["case_id"]: entry for entry in self.seeds}
        self.negatives_by_id = {entry["case_id"]: entry for entry in self.negatives}

    @staticmethod
    def _plain(entry: Mapping[str, Any]) -> dict[str, Any]:
        if "views" in entry:
            views: list[list[str]] | None = [list(view) for view in entry["views"]]
        else:  # a positive seed: the views its confirming call named, or None when it named none
            stated = ((entry.get("lineage") or {}).get("call") or {}).get("views")
            views = None if stated is None else [list(view) for view in stated]
        plain: dict[str, Any] = {
            "case_id": entry["case_id"],
            "subject": entry["subject"],
            "study_uid": entry["study_uid"],
            "procedure": entry["procedure"],
            "banks": {name: tuple(counts) for name, counts in entry["banks"].items()},
            "views": views,
            "lineage": entry["lineage"],
        }
        if "source_case_id" in entry:
            plain["source_case_id"] = entry["source_case_id"]
        return plain


class BundleCache:
    def __init__(self, memory: Mapping[str, Any]) -> None:
        self.memory = memory
        self._by_scale: dict[str, Bundles] = {}

    def at(self, scale: str) -> Bundles:
        if scale not in self._by_scale:
            log(f"preparing the identity reader's bundles at scale {scale}")
            self._by_scale[scale] = Bundles(self.memory, scale)
        return self._by_scale[scale]


# ----------------------------------------------------------------------------- records


def bundles_source(memory_sha256: str, view: Bundles) -> dict[str, Any]:
    """Which memory, scale and preparation the compared bundles came from."""
    return {
        "memory_manifest_sha256": memory_sha256,
        "scale": view.scale,
        "preparation_source_pin": view.preparation.get("source_pin"),
        "positive_seed_count": len(view.seeds),
        "negative_case_count": len(view.negatives),
    }


def profile_banks(memory: Mapping[str, Any]) -> dict[str, Any]:
    """The banks of each case's own profile, by case id: the query a recall compared (an admission's profile)."""
    banks: dict[str, Any] = {}
    for case in memory.get("cases", ()):
        banks[case["case_id"]] = (case.get("profile") or {}).get("banks")
    for record in (memory.get("object_identity_cases") or {}).get("cases", ()):
        banks.setdefault(record["case_id"], (record.get("profile") or {}).get("banks"))
    return banks


def compare_traced(
    correction: Mapping[str, Any],
    expectation: Mapping[str, Any],
    bundles: BundleCache,
    query_banks: Mapping[str, Any] | None,
    memory_sha256: str,
) -> list[dict[str, Any]]:
    """The failure's bundle against each positive precedent that actually spoke, at the recalled scale.

    A precedent is compared only if the bundle in hand reproduces the terms the inference record
    recorded for it (``nm.compare_speaking_precedent``).
    """
    view = bundles.at(str(expectation["scale"]))
    failure = view.negatives_by_id.get(str(correction["case_id"]))
    source = bundles_source(memory_sha256, view)
    blocks: list[dict[str, Any]] = []
    for voice in expectation["speaking_positive"]:
        precedent = view.seeds_by_id.get(str(voice["case_id"]))
        if failure is None or query_banks is None:
            blocks.append(nm.failure_unavailable(str(voice["case_id"])))
        elif precedent is None:
            blocks.append(nm.precedent_unavailable(str(voice["case_id"])))
        else:
            blocks.append(
                nm.compare_speaking_precedent(
                    voice, query_banks, failure, precedent, view.seeds, source
                )
            )
    return blocks


def build_records(
    memory: Mapping[str, Any],
    finder: RecordFinder,
    bundles: BundleCache,
    memory_sha256: str,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    found = nm.enumerate_corrections(
        memory["object_identity_teaching"],
        memory.get("object_identity_cases"),
        memory.get("object_identity_growth"),
    )
    queries = profile_banks(memory)
    records: list[dict[str, Any]] = []
    for correction in found["corrections"]:
        expectation = nm.join_expectation(
            origin=correction["origin"],
            proposed_identity=correction["proposed_identity"],
            study_uid=correction["study_uid"],
            case_id=correction["case_id"],
            identity_growth=correction["identity_growth"],
            find_record=finder,
        )
        comparisons: list[dict[str, Any]] = []
        if expectation["status"] == nm.EXPECTATION_TRACED:
            comparisons = compare_traced(
                correction,
                expectation,
                bundles,
                queries.get(correction["case_id"]),
                memory_sha256,
            )
        records.append(nm.assemble_record(correction, expectation, comparisons))
    return records, found["not_corrections"]


def join_check(
    memory: Mapping[str, Any],
    finder: RecordFinder,
    bundles: BundleCache,
    memory_sha256: str,
) -> list[dict[str, Any]]:
    """The same join and comparison run on the confirmed recognition-derived admissions.

    They are not corrections, so no record is written for them: this shows only that the join
    resolves each admission to the inference record that produced it with its recorded speaking
    precedents, and that the comparison runs on real bundles.  The admission's own bundle stands
    in for the failure's, only to exercise the code; nothing here is a near miss.
    """
    checks: list[dict[str, Any]] = []
    for case in memory.get("cases", ()):
        growth = case.get("identity_growth")
        if not isinstance(growth, Mapping):
            continue
        expectation = nm.join_expectation(
            origin=nm.ORIGIN_ADMISSION,
            proposed_identity=case["subject"],
            study_uid=case["study_uid"],
            case_id=case["case_id"],
            identity_growth=growth,
            find_record=finder,
        )
        entry: dict[str, Any] = {
            "case_id": case["case_id"],
            "identity": case["subject"],
            "study_uid": case["study_uid"],
            "growth_decision": (growth.get("decision") or {}).get("state"),
            "expectation_status": expectation["status"],
            "reason": expectation.get("reason"),
        }
        if expectation["status"] == nm.EXPECTATION_TRACED:
            entry["inference_record"] = expectation["inference_record"]
            entry["scale"] = expectation["scale"]
            entry["speaking_positive_in_record"] = len(expectation["speaking_positive"])
            entry["speaking_case_ids_in_lineage"] = len(
                growth.get("speaking_case_ids") or ()
            )
            entry["speaking_sets_equal"] = {
                v["case_id"] for v in expectation["speaking_positive"]
            } == set(growth.get("speaking_case_ids") or ())
            entry["negatives_that_applied"] = len(expectation["speaking_negative"])
            view = bundles.at(str(expectation["scale"]))
            source = bundles_source(memory_sha256, view)
            stand_in = view.seeds_by_id.get(case["case_id"])
            query_banks = (case.get("profile") or {}).get("banks")
            states: Counter[str] = Counter()
            cells = readings_with_sides = 0
            sizes: list[int] = []
            partitions_hold = True
            matched = 0
            differing: list[dict[str, Any]] = []
            for voice in expectation["speaking_positive"]:
                precedent = view.seeds_by_id.get(str(voice["case_id"]))
                if stand_in is None or precedent is None:
                    states["bundle_unavailable"] += 1
                    continue
                block = nm.compare_speaking_precedent(
                    voice, query_banks, stand_in, precedent, view.seeds, source
                )
                states[block["state"]] += 1
                check = block["recorded_terms_check"]
                if check["matches"]:
                    matched += 1
                else:
                    differing.append({"precedent_case_id": voice["case_id"], **check})
                if block["state"] == nm.STATE_NOT_COMPARED:
                    continue
                cells += block["compared_cell_count"]
                sizes.append(block["success_population"]["size"])
                for item in block["differences_sorted_for_display"]:
                    side = item["success_side"]
                    if "skipped" in side:
                        continue
                    readings_with_sides += 1
                    partitions_hold &= (
                        sum(side["counts"].values()) == side["population_size"]
                    )
            entry["bundles_from"] = source
            entry["dry_run_comparison"] = {
                "note": (
                    "confirmed admission, not a correction: no record is written; the admission's own bundle "
                    "stands in for a failure. The tallies below count code exercised, not comparisons with listed populations"
                ),
                "pairs_by_state": dict(states),
                "bundle_reproduces_recorded_terms": {
                    "matched": matched,
                    "differed": len(differing),
                    "differing": differing,
                },
                "compared_cells": cells,
                "readings_with_side_counts": readings_with_sides,
                "population_sizes": sizes,
                "side_counts_partition_each_population": partitions_hold,
            }
        checks.append(entry)
    return checks


# ----------------------------------------------------------------------------- the survey


def find_manifests(root: str) -> list[str]:
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIRS)
        if "manifest.json" in filenames:
            found.append(os.path.join(dirpath, "manifest.json"))
    return sorted(found, key=os.path.getmtime)


def survey_memories(root: str) -> list[dict[str, Any]]:
    """Every published memory manifest, read as structured data: how many corrections it holds."""
    from knee.diagnosis.squint_memory import inspect_memory_snapshot

    surveyed: list[dict[str, Any]] = []
    for manifest in find_manifests(root):
        directory = Path(manifest).parent
        snapshot = inspect_memory_snapshot(directory)
        entry: dict[str, Any] = {
            "memory": relative(str(directory)),
            "manifest_sha256": snapshot.sha256,
            "status": snapshot.status,
        }
        memory = snapshot.memory
        if snapshot.status != "squint" or not isinstance(memory, Mapping):
            entry["error_code"] = snapshot.error_code
        else:
            teaching = memory.get("object_identity_teaching") or {}
            calls = teaching.get("calls") or []
            records = (memory.get("object_identity_cases") or {}).get("cases") or []
            reviews = teaching.get("admission_reviews") or []
            entry.update(
                {
                    "revision": memory.get("revision"),
                    "cases": len(memory.get("cases") or ()),
                    "teaching_calls": dict(Counter(row.get("call") for row in calls)),
                    "negative_case_ids": len(teaching.get("negative_case_ids") or ()),
                    "identity_correction_records": sum(
                        1
                        for row in records
                        if isinstance(row, Mapping) and "identity_correction" in row
                    ),
                    "admission_reviews": [
                        {
                            "reader": review.get("reader"),
                            "reviewed": len(review.get("reviewed_candidate_ids") or ()),
                            "calls": dict(
                                Counter(
                                    row.get("call") for row in review.get("calls") or ()
                                )
                            ),
                            "corrected_case_ids": len(
                                review.get("corrected_case_ids") or ()
                            ),
                            "superseded_calls": len(
                                review.get("superseded_calls") or ()
                            ),
                        }
                        for review in reviews
                        if isinstance(review, Mapping)
                    ],
                }
            )
        surveyed.append(entry)
        log(
            f"memory {entry['memory']}: status {entry['status']}, cases {entry.get('cases')}, "
            f"identity_correction records {entry.get('identity_correction_records')}, "
            f"corrected admissions {[r['corrected_case_ids'] for r in entry.get('admission_reviews', [])]}"
        )
        del snapshot, memory
        gc.collect()
    return surveyed


def survey_call_files(root: str) -> list[dict[str, Any]]:
    """Every call file under the root, read as structured data: call kinds, and any on located ids."""
    surveyed = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIRS)
        for name in sorted(filenames):
            if "calls" not in name.lower() or not name.endswith((".json", ".jsonl")):
                continue
            path = os.path.join(dirpath, name)
            try:
                if name.endswith(".jsonl"):
                    with open(path) as handle:
                        calls = [json.loads(line) for line in handle if line.strip()]
                else:
                    with open(path) as handle:
                        payload = json.load(handle)
                    calls = (
                        payload.get("calls") if isinstance(payload, dict) else payload
                    )
            except (OSError, ValueError) as error:
                surveyed.append({"file": relative(path), "error": repr(error)[:120]})
                continue
            if not isinstance(calls, list):
                surveyed.append({"file": relative(path), "calls": None})
                continue
            rows = [row for row in calls if isinstance(row, Mapping)]
            surveyed.append(
                {
                    "file": relative(path),
                    "calls": len(rows),
                    "kinds": dict(Counter(row.get("call") for row in rows)),
                    "on_located_ids": sum(
                        str(row.get("candidate_id", "")).startswith("located:")
                        for row in rows
                    ),
                    "reject_on_located_ids": sum(
                        row.get("call") == "reject"
                        and str(row.get("candidate_id", "")).startswith("located:")
                        for row in rows
                    ),
                    "with_negative_views": sum(
                        bool(row.get("negative_views")) for row in rows
                    ),
                }
            )
    return surveyed


def key_names(value: object, into: set[str]) -> set[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            into.add(str(key))
            key_names(item, into)
    elif isinstance(value, list):
        for item in value:
            key_names(item, into)
    return into


def survey_catalogue_exports(root: str) -> list[dict[str, Any]]:
    """What the catalogue review exports recorded before any call: structure facts, or recall terms."""
    surveyed = []
    for name in ("catalogue-review-r1", "catalogue-called-review-r2"):
        path = os.path.join(root, name, "review.json")
        if not os.path.exists(path):
            continue
        with open(path) as handle:
            review = json.load(handle)
        candidates = review.get("candidates") or []
        names: set[str] = set()
        performed: Counter[str] = Counter()
        for candidate in candidates:
            evidence = candidate.get("evidence")
            key_names(evidence, names)
            performed[
                str(evidence.get("inference_performed"))
                if isinstance(evidence, dict)
                else "no evidence"
            ] += 1
        recall_like = sorted(
            key for key in names if any(word in key.lower() for word in RECALL_WORDS)
        )
        surveyed.append(
            {
                "export": relative(path),
                "status": review.get("status"),
                "candidates": len(candidates),
                "inference_performed": dict(performed),
                "evidence_key_names": sorted(names),
                "recall_like_key_names": recall_like,
            }
        )
    return surveyed


def scan_record_sets(
    roots: Sequence[str], corrected: Mapping[str, Mapping[str, Mapping[str, Any]]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Every per-study inference record, parsed: which sets hold identity recall at all, and which
    of their studies carry a correction, with the located-versus-catalogue comparison for those."""
    by_directory: dict[str, dict[str, Any]] = {}
    not_joined: list[dict[str, Any]] = []
    for root in roots:
        for path in study_record_files(root):
            record = load_xz_json(path)
            directory = relative(os.path.dirname(path))
            entry = by_directory.setdefault(
                directory,
                {"directory": directory, "records": 0, "with_identity_recall": 0},
            )
            entry["records"] += 1
            recall = record.get("identity_recall")
            objects = recall.get("objects") if isinstance(recall, dict) else None
            if not isinstance(objects, dict) or not objects:
                continue
            entry["with_identity_recall"] += 1
            study = record.get("study_uid")
            if study not in corrected:
                continue
            for subject, recalled in sorted(objects.items()):
                catalogue = corrected[study].get(subject)
                if catalogue is None:
                    continue
                located = (record.get("objects") or {}).get(subject) or {}
                located_regions = located.get("regions") or []
                catalogue_regions = catalogue.get("regions") or []
                located_profile = located.get("profile")
                not_joined.append(
                    {
                        "record": relative(path),
                        "study_uid": study,
                        "object": subject,
                        "memory_revision": record.get("memory_revision"),
                        "capacity_exclusion": (
                            record.get("capacity_exclusion") or {}
                        ).get("exclusion_status"),
                        "located_status": located.get("status"),
                        "recall_outcome": recalled.get("outcome"),
                        "recalled_identity": recalled.get("identity"),
                        "speaking_cases": len(recalled.get("speaking_case_ids") or ()),
                        "located_profile_sha256": None
                        if located_profile is None
                        else canonical_sha256(located_profile),
                        "catalogue_profile_sha256": canonical_sha256(
                            catalogue.get("profile")
                        ),
                        "same_profile": located_profile is not None
                        and canonical_sha256(located_profile)
                        == canonical_sha256(catalogue.get("profile")),
                        "located_region_keys": sorted(located_regions[0])
                        if located_regions
                        else None,
                        "catalogue_region_keys": sorted(catalogue_regions[0])
                        if catalogue_regions
                        else None,
                        "joined": False,
                        "why_not": "a located window of the record is another candidate than the catalogue support the reviewer called",
                    }
                )
        log(f"scanned inference records under {relative(root)}")
    return sorted(by_directory.values(), key=lambda item: item["directory"]), not_joined


# ----------------------------------------------------------------------------- the table


def md_cell(text: object, limit: int = 110) -> str:
    shown = str(text).replace("|", "/").replace("\n", " ")
    return shown if len(shown) <= limit else shown[: limit - 1] + "…"


def short_id(case_id: str) -> str:
    parts = case_id.split(":")
    if len(parts) >= 3:
        return f"{parts[0].split('-')[0]}:…{parts[1][-6:]}:{parts[2]}"
    return case_id


def scope_text(views: object) -> str:
    if not isinstance(views, list) or not views:
        return "-"
    return ", ".join("/".join(str(part) for part in view) for view in views)


def render_comparison(
    block: Mapping[str, Any],
    describe_bank: Callable[[str], str] | None,
    describe_row: Callable[[str, int], str] | None,
    top: int = TOP_READINGS_SHOWN,
) -> list[str]:
    lines = [f"- precedent `{short_id(str(block.get('precedent_case_id')))}`"]
    if block.get("state") == nm.STATE_NOT_COMPARED:
        lines[0] += f": not compared ({block.get('reason')})"
        check = block.get("recorded_terms_check")
        if check:
            lines[0] += (
                f"; recorded {check['recorded']}, recomputed from the bundle in hand {check['recomputed']}"
            )
        return lines
    source = block.get("bundles_from") or {}
    lines[0] += (
        f" (bundle reproduces the recorded terms: {block.get('bundle_matches_recorded_terms')}; "
        f"memory `{str(source.get('memory_manifest_sha256'))[:12]}`, scale {source.get('scale')}, "
        f"preparation `{str(source.get('preparation_source_pin'))[:12]}`)"
    )
    lines[0] += (
        f": {block['statement']}; {len(block['shared_banks'])} shared banks, "
        f"{block['differing_cell_count']} of {block['compared_cell_count']} rows differ; "
        f"one-sided {len(block['failure_only_banks'])} failure / {len(block['precedent_only_banks'])} precedent, "
        f"silent {len(block['silent_banks'])}; other successes counted: {block['success_population']['size']}"
    )
    shown = [
        item
        for item in block["differences_sorted_for_display"]
        if item["difference"]["exact"] != "0"
    ][:top]
    if not shown:
        return lines
    lines.append("")
    lines.append(f"  First {len(shown)} rows in display order ({nm.DISPLAY_ORDER})")
    lines.append("")
    lines.append(
        "  | bank | row | failure | precedent | failure - precedent | precedent side | beyond failure | equal | not read |"
    )
    lines.append("  |---|---|---|---|---|---|---|---|---|")
    for item in shown:
        side = item["success_side"]
        counts = side.get("counts", {})
        bank_text = describe_bank(item["bank"]) if describe_bank else item["bank"]
        row_text = (
            describe_row(item["bank"], item["row"])
            if describe_row
            else item["row_name"]
        )
        lines.append(
            f"  | {md_cell(bank_text, 120)} | {md_cell(row_text, 40)} | {item['failure']['fraction']} | "
            f"{item['precedent']['fraction']} | {item['difference']['exact']} | "
            f"{counts.get('precedent_side', '-')} | {counts.get('beyond_failure', '-')} | "
            f"{counts.get('equal_to_failure', '-')} | {counts.get('bank_not_read', '-')} |"
        )
    lines.append("")
    return lines


def render_table(
    payload: Mapping[str, Any],
    describe_bank: Callable[[str], str] | None = None,
    describe_row: Callable[[str, int], str] | None = None,
) -> str:
    records = payload["records"]
    summary = payload["summary"]
    lines = [
        "# Near-miss records",
        "",
        (
            f"Memory `{payload['memory']['path']}`, manifest sha256 `{payload['memory']['manifest_sha256']}`, "
            f"{payload['memory']['cases']} cases. Generated {payload['generated']}."
        ),
        "",
        (
            "A record keeps a reviewer correction beside what the memory expected (the positive precedents that "
            "actually spoke for the proposal in the inference record that produced it) and every decoded "
            "difference against each of them. It writes no censor and no split, applies no threshold, and "
            "names no reading as the significant difference."
        ),
        "",
        "## Summary",
        "",
        "| measure | count |",
        "|---|---|",
        f"| reviewer corrections found | {summary['corrections']} |",
    ]
    for key in (
        "by_status",
        "by_origin",
        "by_call_kind",
        "unavailable_reasons",
        "not_corrections",
    ):
        for name, count in sorted(summary[key].items()):
            lines.append(f"| {key.replace('_', ' ')}: {name} | {count} |")
    traced = [r for r in records if r["status"] != nm.STATUS_UNAVAILABLE]
    lines += ["", "## Corrections with a recorded expectation", ""]
    if not traced:
        lines.append(
            "None. No correction in this memory was produced by an identity recall that an inference "
            "record holds; see the next sections."
        )
    for record in traced:
        correction, expectation = record["correction"], record["expectation"]
        lines += [
            "",
            f"### `{short_id(correction['case_id'])}` ({correction['proposed_identity']}), {record['status']}",
            "",
            (
                f"- reviewer `{correction['reader']}`, call {correction['reviewer_call'].get('call')}, "
                f"rejected views {scope_text(correction['negative_views'])} ({correction['negative_views_source']})"
            ),
            f"- note: {md_cell(correction['reviewer_call'].get('notes'), 400)}",
            (
                f"- expectation: inference record `{expectation['inference_record']['path']}` "
                f"(sha256 `{expectation['inference_record']['sha256']}`), scale {expectation['scale']}, recalled "
                f"identity {expectation['recalled_identity']}, {len(expectation['speaking_positive'])} positive "
                f"precedents spoke, {len(expectation['speaking_negative'])} negative cases applied"
            ),
            "",
        ]
        for block in record["comparisons"]:
            lines += render_comparison(block, describe_bank, describe_row)
    unavailable = [r for r in records if r["status"] == nm.STATUS_UNAVAILABLE]
    lines += [
        "",
        f"## Corrections kept as expectation_unavailable ({len(unavailable)})",
        "",
    ]
    for reason, count in sorted(summary["unavailable_reasons"].items()):
        lines.append(f"- `{reason}` ({count}): {nm.REASONS.get(str(reason), '')}")
    lines += [
        "",
        "| # | proposed | case | study | call | rejected views (source) | reader | reviewer's note |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for number, record in enumerate(unavailable, 1):
        correction = record["correction"]
        lines.append(
            f"| {number} | {correction['proposed_identity']} | `{short_id(correction['case_id'])}` | "
            f"…{str(correction['study_uid'])[-6:]} | {correction['call_kind']} | "
            f"{scope_text(correction['negative_views'])} ({correction['negative_views_source'].split('_')[0]}) | "
            f"{md_cell(str(correction['reader']).split(' — ')[0], 40)} | "
            f"{md_cell(correction['reviewer_call'].get('notes'), 90)} |"
        )
    lines += [
        "",
        "## Join check on the confirmed admissions (not corrections; no record written)",
        "",
    ]
    checks = payload.get("join_check") or []
    if checks:
        lines += [
            "| admission | recall record resolved | scale | speaking in record | in lineage | same set | bundles reproduce recorded terms | negatives applied | dry-run pairs |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for check in checks:
            dry = check.get("dry_run_comparison") or {}
            terms = dry.get("bundle_reproduces_recorded_terms") or {}
            lines.append(
                f"| `{short_id(check['case_id'])}` | {check['expectation_status']} | {check.get('scale', '-')} | "
                f"{check.get('speaking_positive_in_record', '-')} | {check.get('speaking_case_ids_in_lineage', '-')} | "
                f"{check.get('speaking_sets_equal', '-')} | {terms.get('matched', '-')} of {check.get('speaking_positive_in_record', '-')} | "
                f"{check.get('negatives_that_applied', '-')} | {dry.get('pairs_by_state', '-')} |"
            )
    else:
        lines.append("No admission with a recognition-derived lineage in this memory.")
    lines += [
        "",
        "## Calls that are not corrections",
        "",
        "| reason | count |",
        "|---|---|",
    ]
    for reason, count in sorted(summary["not_corrections"].items()):
        lines.append(f"| {reason} | {count} |")
    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------------- main


def plain_word_helpers() -> tuple[
    Callable[[str], str] | None, Callable[[str, int], str] | None
]:
    """The development script's plain words for a bank and a row, or (None, None) without it.

    Words are a convenience for the table only; no record depends on them.
    """
    sys.path.insert(0, str(REPO / "scripts"))
    try:
        from squint_visual_capacity import bank_words, row_words
    except ImportError as error:
        log(
            f"plain-word helpers unavailable ({error!r}); the table shows raw bank names"
        )
        return None, None

    def words_for_row(bank: str, row: int) -> str:
        return row_words(bank)[row]

    return bank_words, words_for_row


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    from knee.diagnosis.squint_memory import load_memory_snapshot

    memory_dir = Path(args.memory)
    log(f"loading memory {relative(str(memory_dir))}")
    snapshot = load_memory_snapshot(memory_dir)
    memory = snapshot.memory
    assert memory is not None
    log(f"memory sha256 {snapshot.sha256}, {len(memory['cases'])} cases")
    roots = [str(path) for path in (args.inference_root or [REPO / READINGS])]
    finder = RecordFinder(roots)
    bundles = BundleCache(memory)
    records, not_corrections = build_records(memory, finder, bundles, snapshot.sha256)
    summary = nm.summarize(records, not_corrections)
    log(
        f"corrections {summary['corrections']}: {summary['by_status']} origins {summary['by_origin']}"
    )
    log(f"not corrections: {summary['not_corrections']}")
    checks = join_check(memory, finder, bundles, snapshot.sha256)
    for check in checks:
        log(
            f"join check {short_id(check['case_id'])}: {check['expectation_status']}, "
            f"speaking in record {check.get('speaking_positive_in_record')}, "
            f"same set as lineage {check.get('speaking_sets_equal')}, "
            f"dry run {check.get('dry_run_comparison', {}).get('pairs_by_state')}, "
            f"bundles reproduce recorded terms {check.get('dry_run_comparison', {}).get('bundle_reproduces_recorded_terms', {}).get('matched')} of "
            f"{check.get('speaking_positive_in_record')}"
        )
    teaching = memory["object_identity_teaching"]
    growth = memory.get("object_identity_growth") or {}
    payload: dict[str, Any] = {
        "schema": nm.RECORDS_SCHEMA,
        "generated": datetime.now(UTC).isoformat(timespec="seconds"),
        "memory": {
            "path": relative(str(memory_dir)),
            "manifest_sha256": snapshot.sha256,
            "revision": memory.get("revision"),
            "cases": len(memory["cases"]),
            "teaching_reader": teaching.get("reader"),
            "teaching_review_sha256": teaching.get("review_sha256"),
            "growth_rounds": [
                {
                    "round_index": index,
                    "candidate_count": entry.get("candidate_count"),
                    "state_counts": entry.get("state_counts"),
                    "admitted": len(entry.get("admitted_case_ids") or ()),
                    "parent_manifest_sha256": entry.get("parent_manifest_sha256"),
                    "decisions_sha256": entry.get("decisions_sha256"),
                }
                for index, entry in enumerate(growth.get("rounds") or ())
            ],
            "admission_reviews": [
                {
                    "reader": review.get("reader"),
                    "review_sha256": review.get("review_sha256"),
                    "confirmed": len(review.get("confirmed_admission_ids") or ()),
                    "corrected_case_ids": review.get("corrected_case_ids"),
                    "unsure_case_ids": review.get("unsure_case_ids"),
                }
                for review in teaching.get("admission_reviews") or ()
            ],
        },
        "definition": {
            "correction": "a reviewer call that says 'not this object' at some view: a reject, or a confirm that carries negative_views",
            "record": "the correction, its recorded expectation (positive precedents that spoke in the inference record that produced the proposal), and every decoded difference against each of them",
            "not_written": ["censor", "split", "threshold", "chance test", "verdict"],
            "comparison": "only where the identity question, the profile procedure and the bank name agree; every count carries the case ids of its population",
            "row_names": list(nm.ROW_NAMES),
            "display_order": nm.DISPLAY_ORDER,
        },
        "summary": summary,
        "records": records,
        "join_check": checks,
    }
    if not args.skip_survey and args.survey_root:
        corrected: dict[str, dict[str, dict[str, Any]]] = {}
        table = {
            r["case_id"]: r
            for r in (memory.get("object_identity_cases") or {}).get("cases", ())
        }
        for record in records:
            correction = record["correction"]
            case = table.get(correction["case_id"])
            if case is not None:
                corrected.setdefault(correction["study_uid"], {})[
                    correction["proposed_identity"]
                ] = case
        loop_root = str(args.survey_root)
        survey: dict[str, Any] = {"inference_roots": [relative(root) for root in roots]}
        del memory, snapshot, bundles
        gc.collect()
        survey["memories"] = survey_memories(loop_root)
        survey["call_files"] = survey_call_files(loop_root)
        survey["catalogue_exports"] = survey_catalogue_exports(loop_root)
        survey["inference_record_sets"], survey["records_not_joined"] = (
            scan_record_sets(roots, corrected)
        )
        payload["survey"] = survey
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--memory", required=True, help="published memory directory to inspect"
    )
    parser.add_argument(
        "--inference-root",
        action="append",
        default=None,
        help="root containing inference records; repeat for multiple roots",
    )
    parser.add_argument(
        "--survey-root",
        help="optional current work root for the memory/call/inference survey",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="existing output folder for the JSON records and Markdown table",
    )
    parser.add_argument(
        "--skip-survey",
        action="store_true",
        help="skip the survey of every memory, call file and record set",
    )
    args = parser.parse_args(argv)
    out = Path(args.out)
    if not out.is_dir():
        parser.error(f"--out {out} is not a folder")
    describe_bank, describe_row = plain_word_helpers()
    payload = build_payload(args)
    (out / "near-miss-records.json").write_text(
        json.dumps(payload, indent=1, default=str) + "\n"
    )
    (out / "near-miss-table.md").write_text(
        render_table(payload, describe_bank, describe_row)
    )
    log(f"wrote {out / 'near-miss-records.json'} and {out / 'near-miss-table.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
