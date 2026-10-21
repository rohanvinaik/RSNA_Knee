#!/usr/bin/env python3
"""Check each located object against its own study's bootstrap support, without labels.

Given a completed squint run (its per-study records) and the memory holding
each labelled study's own bootstrap cases, report per object and per view
whether every located region sits on that study's own high-resolution
support: (a) the located object's centre inside the support's tile box,
(b) its slice within two slices of the key slice, (c) both, and (d) where a
record carries a territory, the share of the support's native pixels its
object tiles cover. See ``knee.diagnosis.squint_location_check``.

Labels are never read: not train.csv, not the memory's condition calls, not a
capacity report. From the run receipt only its study index and its memory
identity are read.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import numpy as np

from knee.diagnosis import squint_location_check as check
from knee.diagnosis.squint_memory import SquintMemoryError, load_memory_snapshot
from knee.json_store import load_json

STUDY_SCHEMA = "knee.squint-study/v1"


class LocationCheckError(ValueError):
    """A named refusal to check an unreadable or mismatched run."""


def _studies_root(run: Path) -> Path:
    """The directory holding ``studies/``: the run itself or its ``diagnostics``."""
    for candidate in (run, run / "diagnostics"):
        if (candidate / "studies").is_dir():
            return candidate
    raise LocationCheckError("run_studies_directory_missing")


def _safe_path(root: Path, relative: object) -> Path:
    if type(relative) is not str or not relative:
        raise LocationCheckError("study_evidence_path_invalid")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as error:
        raise LocationCheckError("study_evidence_path_outside_run") from error
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _study_index(
    run: Path,
) -> tuple[list[tuple[str | None, Path | None]], dict[str, Any]]:
    """The run's own study list: its receipt when present, else its records on disk."""
    receipt_path = run / "receipt.json"
    if receipt_path.is_file():
        try:
            receipt = load_json(receipt_path)
        except (OSError, ValueError) as error:
            raise LocationCheckError("run_receipt_invalid") from error
        if not isinstance(receipt, Mapping):
            raise LocationCheckError("run_receipt_invalid")
        work = receipt.get("work")
        studies = work.get("studies") if isinstance(work, Mapping) else None
        if not isinstance(studies, list):
            raise LocationCheckError("run_receipt_studies_missing")
        index: list[tuple[str | None, Path | None]] = []
        seen: set[str] = set()
        for item in studies:
            uid = item.get("study_uid") if isinstance(item, Mapping) else None
            if type(uid) is not str or not uid or uid in seen:
                raise LocationCheckError("run_receipt_study_uid_invalid_or_duplicate")
            seen.add(uid)
            relative = item.get("evidence_path")
            index.append((uid, None if relative is None else _safe_path(run, relative)))
        identity = {
            "study_index": "receipt",
            "receipt_sha256": _sha256(receipt_path),
            "receipt_schema": receipt.get("schema"),
            "memory_manifest_sha256": receipt.get("memory_manifest_sha256"),
            "memory_revision": receipt.get("memory_revision"),
        }
        return index, identity
    paths: dict[str, Path] = {}
    for path in sorted((run / "studies").iterdir()):
        name = path.name
        for suffix in (".json.xz", ".json"):
            if name.endswith(suffix) and path.is_file():
                paths.setdefault(name[: -len(suffix)], path)
    identity = {
        "study_index": "directory_listing",
        "receipt_sha256": None,
        "receipt_schema": None,
        "memory_manifest_sha256": None,
        "memory_revision": None,
    }
    return [(None, paths[stem]) for stem in sorted(paths)], identity


def _default_support_resolver() -> Callable[..., dict[str, Any]] | None:
    """W4's ``squint_support.support_mask`` once it is merged, else None."""
    try:
        module = importlib.import_module("knee.diagnosis.squint_support")
    except ImportError:
        return None
    return getattr(module, "support_mask", None)


#: ``(subject, series_uid, key_slice, full_source) -> (mask or None, code)``.
SupportMaskFor = Callable[
    [str, str, int, Mapping[str, Any] | None], tuple[np.ndarray | None, str]
]


def product_support_mask(
    resolver: Callable[..., dict[str, Any]] | None,
) -> SupportMaskFor:
    """Resolve a support's native mask from its own bootstrap product.

    ``resolver`` takes the compiler's ``_support_bbox`` arguments and returns
    the mask itself (W4's ``support_mask``). The product is opened only after
    its bytes match the case's recorded SHA-256.
    """
    product_sha: dict[str, str] = {}

    def lookup(
        subject: str,
        series_uid: str,
        key_slice: int,
        source: Mapping[str, Any] | None,
    ) -> tuple[np.ndarray | None, str]:
        if resolver is None:
            return None, "support_mask_resolver_unavailable"
        if not isinstance(source, Mapping):
            return None, "support_product_missing"
        raw_path = source.get("product_path")
        path = Path(raw_path) if isinstance(raw_path, str) and raw_path else None
        if path is None or not path.is_file():
            return None, "support_product_missing"
        actual = product_sha.setdefault(str(path), _sha256(path))
        if source.get("product_sha256") != actual:
            return None, "support_product_sha256_mismatch"
        from knee.encoding.product import ProductError, open_product

        try:
            with open_product(path) as product:
                manifest = product.manifest
                ownership = manifest.get("support_ownership", {})
                roots = manifest.get("source_roots", {})
                resolved = resolver(
                    subject,
                    series_uid,
                    key_slice,
                    ownership if isinstance(ownership, dict) else {},
                    roots if isinstance(roots, dict) else {},
                    {},
                    product.arrays,
                )
                mask = (
                    np.array(resolved["mask"], dtype=np.bool_, copy=True)
                    if isinstance(resolved, Mapping)
                    and resolved.get("code") == "resolved"
                    else None
                )
        except SquintMemoryError as error:
            return None, f"support_resolution_refused:{error.code}"
        except (ProductError, OSError):
            return None, "support_product_unreadable"
        if mask is None:
            code = resolved.get("code") if isinstance(resolved, Mapping) else None
            return None, str(code or "support_resolution_invalid")
        return mask, "resolved"

    return lookup


class SupportCoverage:
    """(d) for one run: the support's native mask and the series' tile bounds.

    The mask comes from ``support_mask_for`` (by default the study's own
    bootstrap product through the compiler's support resolution), the bounds
    from the series' own squint (``read_study_squints``). Either missing leaves
    (d) unknown with a named code; nothing is guessed from a box.
    """

    def __init__(
        self,
        references: Mapping[tuple[str, str], Mapping[str, Any]],
        *,
        root: Path | None,
        support_mask_for: SupportMaskFor,
        bounds_reader: Callable[[str], dict[str, np.ndarray]] | None = None,
        io_workers: int = 2,
    ):
        self._references = references
        self._root = root
        self._support_mask_for = support_mask_for
        self._bounds_reader = bounds_reader
        self._io_workers = io_workers
        self._bounds: dict[str, dict[str, np.ndarray] | str] = {}
        self._masks: dict[tuple, tuple[np.ndarray | None, str]] = {}

    def release(self, study_uid: str) -> None:
        """Drop one finished study's bounds and masks."""
        self._bounds.pop(study_uid, None)
        for key in [key for key in self._masks if key[0] == study_uid]:
            del self._masks[key]

    def _series_bounds(self, study_uid: str, series_uid: str) -> np.ndarray | str:
        if study_uid not in self._bounds:
            if self._bounds_reader is not None:
                self._bounds[study_uid] = self._bounds_reader(study_uid)
            elif self._root is None:
                self._bounds[study_uid] = "tile_bounds_unavailable_no_root"
            else:
                from knee.diagnosis.squint_profiles import read_study_squints

                try:
                    study = read_study_squints(
                        self._root, study_uid, io_workers=self._io_workers
                    )
                except (OSError, TypeError, ValueError):
                    self._bounds[study_uid] = "tile_bounds_unreadable"
                else:
                    self._bounds[study_uid] = {
                        series["series_uid"]: np.asarray(series["stack"].bounds_rc)
                        for series in study.get("series", [])
                    }
        bounds = self._bounds[study_uid]
        if isinstance(bounds, str):
            return bounds
        return bounds.get(series_uid, "tile_bounds_series_missing")

    def _support(
        self, study_uid: str, subject: str, series_uid: str, reference: Mapping
    ) -> tuple[np.ndarray | None, str]:
        key = (study_uid, subject, series_uid, reference["key_slice"])
        if key not in self._masks:
            own = self._references.get((study_uid, subject), {})
            source = own.get("full_sources", {}).get(str(reference.get("case_id")))
            self._masks[key] = self._support_mask_for(
                subject, series_uid, reference["key_slice"], source
            )
        return self._masks[key]

    def __call__(
        self, row: Mapping[str, Any], reference: Mapping[str, Any], tiles: np.ndarray
    ) -> dict[str, Any]:
        bounds = self._series_bounds(row["study_uid"], row["series_uid"])
        if isinstance(bounds, str):
            return {"code": bounds}
        mask, code = self._support(
            row["study_uid"], row["subject"], row["series_uid"], reference
        )
        if mask is None:
            return {"code": code}
        return check.support_coverage(tiles, reference["key_slice"], mask, bounds)


def check_run(
    run: Path,
    memory: Path,
    *,
    root: Path | None = None,
    support_mask_for: SupportMaskFor | None = None,
    bounds_reader: Callable[[str], dict[str, np.ndarray]] | None = None,
) -> dict[str, Any]:
    """Check every located region of a run against its study's own supports.

    ``support_mask_for`` and ``bounds_reader`` supply (d); by default the
    support comes from its own bootstrap product and the bounds from the
    series' squint under ``root``.
    """
    run_root = _studies_root(Path(run))
    index, run_identity = _study_index(run_root)
    try:
        snapshot = load_memory_snapshot(Path(memory))
    except SquintMemoryError as error:
        raise LocationCheckError(f"memory_unreadable:{error.code}") from error
    assert snapshot.memory is not None
    references = check.own_references(snapshot.memory["cases"])
    memory_identity = {
        "path": str(snapshot.path),
        "sha256": snapshot.sha256,
        "revision": snapshot.memory.get("revision"),
    }
    del snapshot
    run_sha = run_identity["memory_manifest_sha256"]
    memory_identity["matches_run"] = (
        "run_identity_unavailable"
        if run_sha is None
        else run_sha == memory_identity["sha256"]
    )
    coverage = SupportCoverage(
        references,
        root=root,
        support_mask_for=product_support_mask(_default_support_resolver())
        if support_mask_for is None
        else support_mask_for,
        bounds_reader=bounds_reader,
    )
    checked: list[dict[str, Any]] = []
    unlocated_rows: list[dict[str, Any]] = []
    unlocated_objects: dict[str, Counter] = defaultdict(Counter)
    record_revisions: Counter = Counter()
    not_examined: list[dict[str, Any]] = []
    for expected_uid, path in index:
        if path is None or not path.is_file():
            not_examined.append(
                {"study_uid": expected_uid, "code": "study_record_missing"}
            )
            continue
        try:
            record = load_json(path)
        except (OSError, ValueError) as error:
            raise LocationCheckError(f"study_record_unreadable:{path.name}") from error
        if not isinstance(record, Mapping) or record.get("schema") != STUDY_SCHEMA:
            raise LocationCheckError(f"study_record_schema_invalid:{path.name}")
        study_uid = record.get("study_uid")
        if type(study_uid) is not str or (
            expected_uid is not None and study_uid != expected_uid
        ):
            raise LocationCheckError(f"study_record_identity_mismatch:{path.name}")
        record_revisions[str(record.get("memory_revision"))] += 1
        if record.get("study_status") == "not_examined_budget":
            not_examined.append({"study_uid": study_uid, "code": "not_examined_budget"})
            continue
        rows, unlocated = check.located_rows(record)
        del record
        study_checked = [check.check_row(row, references, coverage) for row in rows]
        coverage.release(study_uid)
        checked.extend(study_checked)
        for (subject, status), count in unlocated.items():
            unlocated_objects[subject][status] += count
        unlocated_rows.extend(
            check.unlocated_supports(study_uid, study_checked, unlocated, references)
        )
    unlocated_summary: dict[str, Counter] = defaultdict(Counter)
    for item in unlocated_rows:
        unlocated_summary[item["subject"]][item["object_state"]] += 1
    located_support_series = Counter(
        subject
        for _study, subject, _series in {
            (row["study_uid"], row["subject"], row["series_uid"])
            for row in checked
            if any(
                pair["reference"]["kind"] == check.NATIVE_SUPPORT
                for pair in row["pairs"]
            )
        }
    )
    return {
        "schema": check.SCHEMA,
        "criteria": {
            "reference": "the study's own case region for that object in the same series",
            "native_support": "case region extent_source retained_object_support; the yardstick",
            "physical_location_only": "case region extent_source retained_physical_location: "
            "one tile at the object's reference point, judged apart, never a support hit or miss",
            "unknown": "no own case, no own region in that series, or an unusable own region; "
            "counted apart",
            "a_centre": "mean (row + 0.5, column + 0.5) of the located object tiles inside the "
            "support's source_window in-plane box, half-open",
            "b_slice": "|located slice - key slice| <= "
            f"{check.SLICE_TOLERANCE}; the key slice is source_window[0]",
            "c_both": "(a) and (b)",
            "d_coverage": "only for a located territory against a native support: support "
            "pixels inside the territory's object tiles / all support pixels, on the key "
            "slice and in plane",
            "object_tiles": "a region without a territory claims every tile of its window; a "
            "territory claims its object-role tiles only",
            "labels_read": False,
        },
        "run": {"path": str(run_root.resolve()), **run_identity},
        "memory": memory_identity,
        "studies": {
            "listed": len(index),
            "checked": len(index) - len(not_examined),
            "not_examined": not_examined,
            "record_memory_revisions": dict(sorted(record_revisions.items())),
        },
        "objects": check.summarize(checked),
        "unlocated_objects": {
            subject: dict(sorted(counts.items()))
            for subject, counts in sorted(unlocated_objects.items())
        },
        "unlocated_supports": {
            "per_subject": {
                subject: {
                    "own_supports_located_in_their_series": located_support_series[
                        subject
                    ],
                    **dict(sorted(counts.items())),
                }
                for subject, counts in sorted(
                    (subject, unlocated_summary[subject])
                    for subject in set(unlocated_summary) | set(located_support_series)
                )
            },
            "rows": unlocated_rows,
        },
        "pooled_reference_table": check.pooled_reference_table(checked),
        "rows": checked,
    }


def _share(count: int, total: int) -> str:
    return f"{count}/{total} ({100 * count / total:.0f}%)" if total else "–"


def _codes(counts: Mapping[str, int]) -> str:
    return ", ".join(f"{code} {count}" for code, count in counts.items()) or "–"


def _object_line(name: str, view: str | None, summary: Mapping[str, Any]) -> str:
    support = summary[check.NATIVE_SUPPORT]
    location = summary[check.PHYSICAL_LOCATION]
    pairs = support["pairs"]
    offset = support["median_slice_offset"]
    coverage = support["territory_coverage"]
    cells = [
        name,
        *([] if view is None else [view]),
        str(summary["located_regions"]),
        str(pairs),
        _share(support["centre_inside_support_box"], pairs),
        _share(support["within_slice_tolerance"], pairs),
        _share(support["on_target"], pairs),
        "–" if offset is None else f"{offset:g}",
        str(sum(summary["unknown_reference"].values())),
        f"{_share(location['on_target'], location['pairs'])}",
        str(coverage["measured"]),
    ]
    return "| " + " | ".join(cells) + " |"


_YARDSTICK = (
    "Yardstick: the study's own native support for that object in the same series "
    "(case region `extent_source = retained_object_support`). (a) the centre of the "
    "located object tiles inside the support's tile box; (b) the located slice within "
    f"{check.SLICE_TOLERANCE} slices of the key slice; (c) both; (d) territory share of "
    "the support's native pixels (only where a record carries a territory). Unknown "
    "(no own support in that series) is counted apart. A case region that kept only the "
    "object's physical reference point (one tile) is judged apart under (c) and never "
    "counted as a support hit or miss."
)
_OBJECT_COLUMNS = (
    "Located regions | Judged on own support | (a) centre in box | "
    "(b) within 2 slices | (c) both | Median slice offset | Unknown | "
    "Physical location only: (c) | (d) measured |"
)
_POOLED_NOTE = (
    "Every (located region, own case region in the same series) pair, fractions to two "
    "places, medians by `statistics.median`, as `locator-truth-check` reports them."
)


def _markdown(report: Mapping[str, Any]) -> str:
    run, memory = report["run"], report["memory"]
    studies = report["studies"]
    lines = [
        "# Squint location check against each study's own bootstrap supports",
        "",
        f"Run: `{run['path']}` (study index: {run['study_index']})  ",
        f"Run receipt SHA-256: `{run['receipt_sha256']}`  ",
        f"Memory: `{memory['path']}`  ",
        (
            f"Memory SHA-256: `{memory['sha256']}`; revision `{memory['revision']}`; "
            f"matches the run's memory: {memory['matches_run']}  "
        ),
        (
            f"Studies checked: {studies['checked']} of {studies['listed']}. "
            "No labels were read."
        ),
        "",
        _YARDSTICK,
        "",
        "## Per object, all views",
        "",
        f"| Object | {_OBJECT_COLUMNS}",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    objects = report["objects"]
    for name, result in objects.items():
        lines.append(_object_line(name, None, result["all_views"]))
    lines.extend(
        [
            "",
            "## Per object and view",
            "",
            "View is orientation / fluid-sensitive / fat-suppressed.",
            "",
            f"| Object | View | {_OBJECT_COLUMNS}",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for name, result in objects.items():
        for view, summary in result["views"].items():
            lines.append(_object_line(name, view, summary))
    lines.extend(
        [
            "",
            "## Unknown and defect codes",
            "",
            "| Object | Unknown reference | Located defects | (d) codes on own supports |",
            "|---|---|---|---|",
        ]
    )
    for name, result in objects.items():
        summary = result["all_views"]
        lines.append(
            f"| {name} | {_codes(summary['unknown_reference'])} | "
            f"{_codes(summary['located_defects'])} | "
            f"{_codes(summary[check.NATIVE_SUPPORT]['territory_coverage']['codes'])} |"
        )
    lines.extend(
        [
            "",
            "## Own native supports in a series where the object was not located",
            "",
            "| Object | Own supports located in their series | Not located there: object state |",
            "|---|---:|---|",
        ]
    )
    for name, counts in report["unlocated_supports"]["per_subject"].items():
        rest = {
            key: value for key, value in counts.items() if not key.startswith("own_")
        }
        lines.append(
            f"| {name} | {counts['own_supports_located_in_their_series']} | {_codes(rest)} |"
        )
    lines.extend(
        [
            "",
            "## The lead's r3 convention: own supports and physical locations pooled",
            "",
            _POOLED_NOTE,
            "",
            (
                "| Object | Pairs | In-plane overlap | Centre inside | Within 2 slices | "
                "Both | Median IoU | Median slice offset |"
            ),
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for name, row in report["pooled_reference_table"].items():
        lines.append(
            f"| {name} | {row['pairs']} | {row['in_plane_overlap']} | "
            f"{row['centre_inside_support_box']} | {row['within_2_slices_of_key']} | "
            f"{row['centre_inside_and_within_2_slices']} | {row['median_iou']} | "
            f"{row['median_slice_offset']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _write_new(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run",
        type=Path,
        required=True,
        help="run directory holding studies/ (or its parent holding diagnostics/)",
    )
    parser.add_argument(
        "--memory", type=Path, required=True, help="memory directory or manifest.json"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="new JSON report path"
    )
    parser.add_argument(
        "--markdown", type=Path, help="optional new Markdown report path"
    )
    parser.add_argument(
        "--root",
        type=Path,
        help="competition files, read only to bound territory tiles for (d)",
    )
    args = parser.parse_args(argv)
    try:
        if (
            args.markdown is not None
            and args.markdown.resolve() == args.output.resolve()
        ):
            raise LocationCheckError("output_paths_must_be_distinct")
        for output in (args.output, args.markdown):
            if output is not None and output.exists():
                raise LocationCheckError("output_already_exists:" + str(output))
        report = check_run(args.run, args.memory, root=args.root)
        _write_new(
            args.output,
            json.dumps(report, sort_keys=True, indent=1, allow_nan=False) + "\n",
        )
        if args.markdown is not None:
            _write_new(args.markdown, _markdown(report))
    except (LocationCheckError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(f"wrote {args.output}")
    if args.markdown is not None:
        print(f"wrote {args.markdown}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
