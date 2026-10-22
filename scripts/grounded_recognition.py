"""Install reviewed references and audit competence on the 58 teaching studies.

Inference is the existing raw-image CLI. This tool attaches labels only after
inference, retains signed parent records, and never selects a call to improve a
score. A proposed region isn't a reviewed identity and a site-negative isn't a
whole-study diagnosis.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from knee.diagnosis.squint_configurations import (
    configuration_reference,
    configuration_role_cases,
)
from knee.diagnosis.squint_identity import identity_condition_views
from knee.diagnosis.squint_locator import prepare_recall, recall_object
from knee.diagnosis.squint_memory import _validate_memory, load_memory, save_memory
from knee.json_store import load_json
from knee.objects.assignments import OBJECT_CODES
from knee.study.tables import LABELS


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def outcome_against_call(outcome: str, label: int | None) -> str:
    """Evaluate an actual answer, never convert silence into normality."""
    if label is None:
        return "unlabeled"
    if outcome in ("assigned", "present"):
        return "identified" if label == 1 else "wrong"
    if outcome in ("defeated", "absent"):
        return "identified" if label == 0 else "wrong"
    return "unresolved"


def extend_references(parent: dict, workset: dict, parent_sha: str) -> dict:
    """A signed child; references speak only at their reviewed question/view scope."""
    if workset.get("schema") != "knee.grounded-reference-workset/v1":
        raise ValueError("reference_workset_schema_invalid")
    if workset.get("spec", {}).get("source_memory_sha256") != parent_sha:
        raise ValueError("reference_parent_pin_stale")
    additions = workset.get("cases")
    if not isinstance(additions, list) or not additions:
        raise ValueError("reference_cases_required")
    child = dict(parent)
    teaching = copy.deepcopy(parent["object_identity_teaching"])
    known = {case["case_id"] for case in parent["cases"]}
    cases = []
    for original in additions:
        case = copy.deepcopy(original)
        cid = case["case_id"]
        if cid in known:
            raise ValueError("reference_case_already_present")
        known.add(cid)
        call = case.get("identity_call")
        if (
            not isinstance(call, dict)
            or call.get("call") != "confirm"
            or not call.get("views")
        ):
            raise ValueError("scoped_visual_confirmation_required")
        if call.get("candidate_id") != cid:
            raise ValueError("reference_identity_call_mismatch")
        if len(case.get("condition_calls", {})) != 1:
            raise ValueError("one_reference_question_required")
        question = next(iter(case["condition_calls"]))
        if question not in LABELS or case["teaching_source"]["official_row"].get(
            question
        ) != str(int(case["condition_calls"][question] == 1)):
            raise ValueError("reference_official_call_mismatch")
        case["question_reference"] = {
            "schema": "knee.question-reference/v1",
            "question": question,
            "scope": "reviewed regional presentation, not a whole-object replacement",
            "spec_sha256": workset["spec_sha256"],
        }
        case["direct_visual_teaching"] = {
            "kind": "reviewed_question_reference",
            "reader": call["reader"],
            "parent_manifest_sha256": parent_sha,
            "source": case["source"],
        }
        cases.append(case)
        teaching["calls"].append(call)
        teaching["confirmed_case_ids"].append(cid)
    child["cases"] = [*parent["cases"], *cases]
    child["object_identity_teaching"] = teaching
    child["parent_revision"] = parent["revision"]
    child["revision"] = parent["revision"] + "+grounded-question-references-r1"
    child["grounded_reference_teaching"] = {
        "schema": "knee.grounded-reference-publication/v1",
        "parent_manifest_sha256": parent_sha,
        "spec_sha256": workset["spec_sha256"],
        "case_ids": [c["case_id"] for c in cases],
        "configuration_policy": "preserve canonical roles and existing configurations; regional references are not whole objects",
    }
    _validate_memory(child)
    scope = identity_condition_views(child)
    if scope.get("outcome") != "scoped" or any(
        c["case_id"] not in scope["views"] for c in cases
    ):
        raise ValueError("reference_identity_views_not_consumed")
    configuration_role_cases(child["cases"])
    return child


def publish(
    workset_path: Path, destination: Path, *, with_configurations: bool = False
) -> dict:
    workset = json.loads(workset_path.read_text())
    parent_path = Path(workset["spec"]["source_memory"])
    parent_sha = sha(parent_path / "manifest.json")
    parent = load_memory(parent_path)
    child = extend_references(parent, workset, parent_sha)
    configurations = []
    if with_configurations:
        scope = identity_condition_views(child)
        added_ids = {case["case_id"] for case in workset["cases"]}
        for case in child["cases"]:
            if case["case_id"] in added_ids:
                views = scope["views"][case["case_id"]]
                if views is None:
                    raise ValueError("reference_scoped_views_required")
                configurations.append(
                    configuration_reference(case, [list(v) for v in sorted(views)])
                )
        child["cases"] = [*child["cases"], *configurations]
        child["revision"] += "+reviewed-question-configurations"
        _validate_memory(child)
    print("Preparing the extended signed memory", flush=True)
    prepared = prepare_recall(child)
    if prepared.get("outcome") != "prepared":
        raise ValueError("reference_recall_preparation_failed")
    result = save_memory(child, destination, prepared_recall=prepared)
    if sha(parent_path / "manifest.json") != parent_sha:
        raise ValueError("parent_changed_during_publication")
    result.update(
        parent_manifest_sha256=parent_sha,
        added_cases=len(workset["cases"]) + len(configurations),
        added_configurations=len(configurations),
    )
    (destination.parent / "publication.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2), flush=True)
    return result


def teaching_rows(root: Path) -> dict:
    with (root / "train.csv").open() as stream:
        return {
            r["StudyInstanceUID"]: r
            for r in csv.DictReader(stream)
            if any(r.get(q) in ("0", "1") for q in LABELS)
        }


def replay_integrated(
    memory_path: Path,
    workset_path: Path,
    output: Path,
    *,
    through_conditions: bool = False,
) -> dict:
    """Check the installed references against all retained opposing expertise."""
    if output.exists():
        raise ValueError("reference_replay_output_already_exists")
    memory = load_memory(memory_path)
    cache = load_json(memory_path / "recall-preparation.json")
    prepared = prepare_recall(memory, cached=cache)
    if prepared.get("outcome") != "prepared":
        raise ValueError("reference_recall_preparation_failed")
    memory = {**memory, "prepared_recall": prepared}
    results = []
    for case in json.loads(workset_path.read_text())["cases"]:
        question, sign = next(iter(case["condition_calls"].items()))
        if through_conditions:
            from knee.diagnosis.declarations import question_for
            from knee.diagnosis.squint_contracts import combine_condition
            from knee.diagnosis.squint_pipeline import _recall_question

            # This addressed support was independently reviewed; no identity
            # or automatic location is being inferred here. The expected call
            # is used only below, after the real consumers answer.
            objects = {
                case["subject"]: {
                    "status": "located",
                    "profile": case["profile"],
                    "regions": case["regions"],
                }
            }
            evidence = _recall_question(
                question_for(question), objects, memory, case["study_uid"], False
            )
            finding = combine_condition(question, evidence)
        else:
            finding = recall_object(case["profile"], memory, question)
        results.append(
            {
                "case_id": case["case_id"],
                "question": question,
                "judgment": outcome_against_call(finding["outcome"], int(sign == 1)),
                "finding": finding,
            }
        )
    result = {
        "scope": (
            "reviewed addressed teaching through condition consumers; not automatic location or transfer"
            if through_conditions
            else "installed teaching replay, not raw-image localization or held-out transfer"
        ),
        "memory_manifest_sha256": sha(memory_path / "manifest.json"),
        "counts": dict(Counter(r["judgment"] for r in results)),
        "cases": results,
    }
    output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, indent=2))
    return result


def build_ledger(
    root: Path, memory: dict, memory_sha: str, run: Path | None = None
) -> dict:
    """Independent labels beside actual reviewed object calls and measured decisions."""
    rows = teaching_rows(root)
    scope = identity_condition_views(memory)
    if scope.get("outcome") != "scoped":
        raise ValueError("teaching_identity_scope_invalid")
    case_index = defaultdict(lambda: defaultdict(list))
    for case in memory["cases"]:
        if (
            not case["subject"].startswith("diagnosis/")
            and case["case_id"] in scope["views"]
        ):
            views = scope["views"][case["case_id"]]
            case_index[case["study_uid"]][case["subject"]].append(
                {
                    "case_id": case["case_id"],
                    "views": None
                    if views is None
                    else [list(v) for v in sorted(views)],
                    "condition_calls": case["condition_calls"],
                    "presentation_scope": case.get("presentation_scope", {}),
                    "question_reference": case.get("question_reference"),
                    "regions": case["regions"],
                    "review": scope["calls"].get(case["case_id"], ()),
                }
            )
    records = {}
    if run is not None:
        receipt = load_json(run / "receipt.json")
        if receipt["memory_manifest_sha256"] != memory_sha:
            raise ValueError("teaching_run_memory_mismatch")
        for entry in receipt["work"]["studies"]:
            uid = entry["study_uid"]
            if uid in rows:
                records[uid] = run / entry["evidence_path"]
    per_condition = {q: Counter() for q in LABELS}
    object_names = tuple(
        obj for obj in OBJECT_CODES if obj not in ("unassigned", "air")
    )
    per_object = {obj: Counter() for obj in object_names}
    studies = []
    for uid, row in sorted(rows.items()):
        record = load_json(records[uid]) if uid in records else None
        questions = {}
        for q in LABELS:
            label = int(row[q]) if row.get(q) in ("0", "1") else None
            finding = None if record is None else record["questions"][q]["finding"]
            actual = (
                None
                if finding is None
                else {
                    key: finding.get(key)
                    for key in ("outcome", "reason", "contract_id")
                }
            )
            judgment = (
                "not_run"
                if actual is None
                else outcome_against_call(actual["outcome"], label)
            )
            per_condition[q][judgment] += 1
            questions[q] = {
                "official_label": label,
                "judgment": judgment,
                "actual": actual,
            }
        objects = {}
        for obj in object_names:
            reviewed = case_index[uid].get(obj, [])
            proposal = None if record is None else record.get("objects", {}).get(obj)
            identity = (
                None
                if record is None
                else record.get("identity_recall", {}).get("objects", {}).get(obj)
            )
            state = (
                "reviewed_teaching_available" if reviewed else "needs_visual_teaching"
            )
            per_object[obj][state] += 1
            objects[obj] = {
                "teaching_status": state,
                "reviewed_presentations": reviewed,
                "production_proposal": None
                if proposal is None
                else {
                    "status": proposal.get("status"),
                    "regions": [
                        {
                            "series_uid": r.get("series_uid"),
                            "view": r.get("view"),
                            "window": r.get("window"),
                        }
                        for r in proposal.get("regions", [])
                    ],
                },
                "production_identity": None
                if identity is None
                else {
                    key: identity.get(key)
                    for key in (
                        "outcome",
                        "identity",
                        "identity_basis",
                        "identity_state",
                        "reason",
                    )
                },
                "proposal_review_status": "not_yet_compared_with_the_actual_image",
            }
        studies.append(
            {
                "study_uid": uid,
                "report": row.get("Report", ""),
                "official_row": row,
                "evidence_path": None
                if run is None or record is None
                else str(run / "studies" / (uid + ".json.xz")),
                "objects": objects,
                "questions": questions,
            }
        )
    return {
        "schema": "knee.grounded-recognition-ledger/v1",
        "scope": "teaching/development competence; includes known teachers, not held-out transfer",
        "memory_manifest_sha256": memory_sha,
        "study_count": len(studies),
        "object_count": len(object_names),
        "run": None if run is None else str(run),
        "per_condition": {q: dict(c) for q, c in per_condition.items()},
        "per_object": {q: dict(c) for q, c in per_object.items()},
        "studies": studies,
    }


def audit(memory_path: Path, root: Path, output: Path, run: Path | None) -> dict:
    if output.exists():
        raise ValueError("teaching_audit_output_already_exists")
    memory_sha = sha(memory_path / "manifest.json")
    memory = load_memory(memory_path)
    ledger = build_ledger(root, memory, memory_sha, run)
    output.mkdir(parents=True)
    for study in ledger.pop("studies"):
        (output / (study["study_uid"] + ".json")).write_text(
            json.dumps(study, indent=2) + "\n"
        )
    (output / "summary.json").write_text(json.dumps(ledger, indent=2) + "\n")
    print(json.dumps(ledger, indent=2))
    return ledger


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    pub = sub.add_parser("publish")
    pub.add_argument(
        "--workset",
        type=Path,
        default=Path(
            "data/readings/grounded-teaching-20261022/references-r3/reference_cases.json"
        ),
    )
    pub.add_argument("--output", type=Path, required=True)
    pub.add_argument("--with-configurations", action="store_true")
    replay = sub.add_parser("replay")
    replay.add_argument("--memory", type=Path, required=True)
    replay.add_argument(
        "--workset",
        type=Path,
        default=Path(
            "data/readings/grounded-teaching-20261022/references-r3/reference_cases.json"
        ),
    )
    replay.add_argument("--output", type=Path, required=True)
    replay.add_argument("--through-conditions", action="store_true")
    report = sub.add_parser("audit")
    report.add_argument("--memory", type=Path, required=True)
    report.add_argument("--root", type=Path, default=Path("data/raw"))
    report.add_argument("--run", type=Path)
    report.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "publish":
        publish(args.workset, args.output, with_configurations=args.with_configurations)
    elif args.command == "replay":
        replay_integrated(
            args.memory,
            args.workset,
            args.output,
            through_conditions=args.through_conditions,
        )
    else:
        audit(args.memory, args.root, args.output, args.run)


if __name__ == "__main__":
    main()
