"""Export report text for a human reader or admit independently authored calls.

This command never interprets report prose and never uses train.csv labels as
teaching calls. Admission requires both reader call records and the original
reports, plus already produced per-study squint inference records.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from knee.diagnosis.squint_memory import load_memory, save_memory
from knee.diagnosis.squint_reports import (
    ACCEPTED_STATUSES,
    ReportCallError,
    admit_report_cases,
    export_report_batch,
    import_report_calls,
    read_reports,
)
from knee.json_store import load_json


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)

    export = actions.add_parser(
        "export", help="export full reports for independent reading"
    )
    export.add_argument("--train-csv", required=True, type=Path)
    export.add_argument("--output", required=True, type=Path)
    export.add_argument("--study-uid", nargs="+")

    admit = actions.add_parser(
        "admit", help="validate calls and publish a new memory revision"
    )
    admit.add_argument("--train-csv", required=True, type=Path)
    admit.add_argument("--calls", required=True, type=Path)
    admit.add_argument("--findings-dir", required=True, type=Path)
    admit.add_argument("--memory", required=True, type=Path)
    admit.add_argument("--revision", required=True)
    admit.add_argument("--output-memory", required=True, type=Path)
    return parser


def _call_study_uid(call: dict[str, Any]) -> str | None:
    uid = call.get("study_uid")
    if not isinstance(uid, str) and isinstance(call.get("record"), dict):
        uid = call["record"].get("study_uid")
    return uid if isinstance(uid, str) else None


def _call_subject(call: dict[str, Any]) -> str | None:
    subject = call.get("subject")
    if not isinstance(subject, str) and isinstance(call.get("record"), dict):
        subject = call["record"].get("subject")
    return subject if isinstance(subject, str) else None


def _located_findings(
    findings_dir: Path,
    calls: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    refs: dict[str, set[str]] = {}
    for call in calls:
        if call.get("status") not in ACCEPTED_STATUSES:
            continue
        uid, subject = _call_study_uid(call), _call_subject(call)
        if uid is None or subject is None:
            continue
        if not uid or Path(uid).name != uid:
            raise ReportCallError("study_uid_invalid_for_findings_path")
        refs.setdefault(uid, set()).add(subject)

    findings: list[dict[str, Any]] = []
    for uid, subjects in refs.items():
        path = findings_dir / "studies" / f"{uid}.json"
        try:
            record = load_json(path)
        except (OSError, ValueError, UnicodeError) as error:
            # A missing inference record leaves the report call unmatched; it is
            # not permission to invent an object profile or source address.
            if not path.exists() and not path.with_name(path.name + ".xz").exists():
                continue
            raise ReportCallError("inference_result_unreadable") from error
        if (
            not isinstance(record, dict)
            or record.get("schema") != "knee.squint-study/v1"
            or record.get("study_uid") != uid
        ):
            raise ReportCallError("inference_result_identity_mismatch")
        objects = record.get("objects")
        if not isinstance(objects, dict):
            continue
        for subject in sorted(subjects):
            located = objects.get(subject)
            if not isinstance(located, dict) or located.get("status") not in (
                "proposal",
                "located",
            ):
                continue
            profile = located.get("profile")
            if not isinstance(profile, dict) or profile.get("subject") != subject:
                continue
            findings.append(
                {
                    "study_uid": uid,
                    "subject": subject,
                    "status": located["status"],
                    "mode": "cheap",
                    "profile": profile,
                    "regions": located.get("regions", []),
                }
            )
    return findings


def run_export(args: argparse.Namespace) -> dict[str, Any]:
    return export_report_batch(args.train_csv, args.output, args.study_uid)


def run_admit(args: argparse.Namespace) -> dict[str, Any]:
    reports = read_reports(args.train_csv)
    calls = import_report_calls(args.calls, reports)
    memory = load_memory(args.memory)
    findings = _located_findings(args.findings_dir, calls)
    revised = admit_report_cases(
        memory,
        findings,
        calls,
        args.revision,
        reports=reports,
        located_statuses=("proposal", "located"),
    )
    publication = save_memory(revised, args.output_memory)
    receipt = revised["report_admissions"][-1]
    return {
        "action": "admit",
        "revision": args.revision,
        "memory": publication,
        "added_case_count": receipt["added_case_count"],
        "admitted": receipt["admitted"],
        "unmatched_calls": receipt["unmatched_calls"],
        "retained_calls": receipt["retained_calls"],
        "prior_opposition": receipt.get("prior_opposition", []),
    }


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = _parser().parse_args(argv)
    result = run_export(args) if args.action == "export" else run_admit(args)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
