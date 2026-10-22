"""Build the 696-row question ledger for the 58 teaching studies.

Joins the 58 x 12 independent targets to the actual ternary answers,
linking each row to its speaking cases, pictured support, and memory/run pins.
"""

from __future__ import annotations

import csv
import json
import lzma
from pathlib import Path
from typing import Any

from knee.json_store import load_json
from knee.study.tables import LABELS


def build_ledger(
    memory_path: Path,
    replayed_run_path: Path,
    labels_csv_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    receipt = load_json(replayed_run_path / "receipt.json")
    receipt_sha = receipt.get("memory_manifest_sha256") or ""

    # Load official label targets
    with labels_csv_path.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        label_rows = {row["StudyInstanceUID"]: row for row in reader}

    rows_696 = []
    summary_by_question: dict[str, dict[str, int]] = {
        q: {"identified": 0, "unresolved": 0, "contradicted": 0} for q in LABELS
    }

    for study_entry in sorted(receipt["work"]["studies"], key=lambda s: s["study_uid"]):
        uid = study_entry["study_uid"]
        evidence_path = replayed_run_path / study_entry["evidence_path"]
        with lzma.open(evidence_path, "rt", encoding="utf-8") as stream:
            study_data = json.load(stream)

        official_row = label_rows.get(uid, {})
        questions = study_data.get("questions", {})
        study_objects = study_data.get("objects", {})

        for q in LABELS:
            raw_label = official_row.get(q)
            if raw_label in ("1", 1):
                target = 1
            elif raw_label in ("0", 0):
                target = -1
            else:
                target = 0

            q_data = questions.get(q, {})
            finding = q_data.get("finding") or {}
            outcome = finding.get("outcome") or "open"
            reason = finding.get("reason") or "unresolved"

            if outcome == "assigned":
                result = 1
            elif outcome == "defeated":
                result = -1
            else:
                result = 0

            if target != 0 and result == target:
                judgment = "identified"
            elif result == 0 or target == 0:
                judgment = "unresolved"
            else:
                judgment = "contradicted"

            summary_by_question[q][judgment] += 1

            # Extract speaking case IDs and pictured support from evidence
            evidence = finding.get("evidence") or {}
            speaking_case_ids = []
            for src in evidence.get("sources", []):
                for key in src.get("keys", []):
                    if key not in speaking_case_ids:
                        speaking_case_ids.append(key)
                for case in src.get("cases", []):
                    cid = case.get("case_id")
                    if cid and cid not in speaking_case_ids:
                        speaking_case_ids.append(cid)

            readings = evidence.get("readings") or {}
            for r in readings.values():
                for cid in r.get("speaking_case_ids", []):
                    if cid not in speaking_case_ids:
                        speaking_case_ids.append(cid)

            # Pictured supports for the question's objects
            q_objects_support = {}
            for subj, obj_data in study_objects.items():
                if isinstance(obj_data, dict) and obj_data.get("regions"):
                    q_objects_support[subj] = {
                        "status": obj_data.get("status"),
                        "regions_count": len(obj_data.get("regions", [])),
                        "first_region": obj_data["regions"][0] if obj_data["regions"] else None,
                    }

            row_record = {
                "study_uid": uid,
                "question": q,
                "target": target,
                "result": result,
                "judgment": judgment,
                "outcome": outcome,
                "reason": reason,
                "contract_id": finding.get("contract_id"),
                "policy_id": finding.get("policy_id"),
                "value": q_data.get("ranking", {}).get("value"),
                "speaking_case_ids": speaking_case_ids,
                "pictured_objects": list(q_objects_support.keys()),
                "pictured_support_summary": q_objects_support,
                "source_pins": {
                    "memory_revision": study_data.get("memory_revision"),
                    "memory_manifest_sha256": receipt_sha,
                    "evidence_path": str(study_entry["evidence_path"]),
                },
            }
            rows_696.append(row_record)

    ledger_doc = {
        "schema": "knee.teaching-question-ledger/v1",
        "description": "58 x 12 = 696 addressed question readback on integrated teaching memory",
        "memory_manifest_sha256": receipt_sha,
        "study_count": len(receipt["work"]["studies"]),
        "question_count": len(LABELS),
        "total_rows": len(rows_696),
        "summary": summary_by_question,
        "rows": rows_696,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(ledger_doc, f, indent=2)
    return ledger_doc

if __name__ == "__main__":
    mem = Path("data/readings/grounded-teaching-20261022/integrated-r4-identity/memory")
    replayed = Path("data/readings/grounded-teaching-20261022/reviewed-teacher-operation-r4")
    train_csv = Path("data/raw/train.csv")
    out = Path("data/readings/grounded-teaching-20261022/teaching-question-ledger-696.json")
    doc = build_ledger(mem, replayed, train_csv, out)
    print(f"Successfully generated {doc['total_rows']} rows in {out}")
    print("Summary by condition:")
    for q, s in doc["summary"].items():
        print(f"  {q}: identified={s['identified']}, unresolved={s['unresolved']}, contradicted={s['contradicted']}")
