"""Replay retained image readings through the real condition consumers.

No new location, identity, measurement or observation is claimed. Default reuse
of old identity decisions requires identical measured cases and signed identity
teaching. Explicit teacher-support mode instead reads the current independently
reviewed supports and does not reuse the old automatic identity decisions.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from knee.diagnosis.declarations import QUESTIONS
from knee.diagnosis.squint_configurations import configuration_role_cases
from knee.diagnosis.squint_contracts import combine_condition, rank_condition
from knee.diagnosis.squint_identity import identity_condition_views
from knee.diagnosis.squint_locator import _scoped_cases, prepare_recall
from knee.diagnosis.squint_memory import load_memory
from knee.diagnosis.squint_pipeline import _recall_question, _regions_not_read
from knee.json_store import dump_json_atomic, load_json


def identity_reuse_code(old: dict, new: dict) -> str:
    """The measured identity inputs must be unchanged before reusing a decision."""
    for key in ("object_identity_teaching", "object_identity_cases"):
        if old.get(key) != new.get(key):
            return "identity_teaching_changed"
    left = [c for c in old["cases"] if not c["subject"].startswith("diagnosis/")]
    right = [c for c in new["cases"] if not c["subject"].startswith("diagnosis/")]
    return "identity_inputs_unchanged" if left == right else "identity_cases_changed"


def teaching_inputs(memory: dict) -> tuple[dict, dict]:
    """Confirmed native teaching profiles, with calls used only for identity scope."""
    from knee.diagnosis.squint_capacity_control import teacher_profiles

    scope = identity_condition_views(memory)
    if scope.get("outcome") != "scoped":
        raise ValueError("teaching_identity_scope_invalid")
    aliases = scope.get("identity_sources", {})
    confirmed: list[dict] = []
    for case in _scoped_cases(memory["cases"], scope):
        cid = case["case_id"]
        if (
            cid not in scope["views"]
            or cid in aliases
            or case["subject"].startswith("diagnosis/")
        ):
            continue
        allowed = scope["views"][cid]
        regions = []
        for region in case["regions"]:
            view = region.get("view", {})
            key = (
                tuple(
                    view.get(k)
                    for k in ("orientation", "fluid_sensitive", "fat_suppression")
                )
                if isinstance(view, dict)
                else tuple(view)
                if isinstance(view, (list, tuple))
                else ()
            )
            if allowed is None or key in allowed:
                regions.append(region)
        confirmed.append({**case, "regions": regions})
    canonical = configuration_role_cases(confirmed)
    seen = set()
    for case in canonical:
        key = (case["study_uid"], case["subject"])
        if key in seen:
            raise ValueError("canonical_teaching_object_ambiguous")
        seen.add(key)
    references = {}
    for case in confirmed:
        marker = case.get("question_reference")
        if isinstance(marker, dict):
            key = (case["study_uid"], marker["question"])
            if key in references:
                raise ValueError("question_teaching_presentation_ambiguous")
            references[key] = case
    return teacher_profiles({"cases": canonical}), references


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--source-memory", type=Path, required=True)
    parser.add_argument("--memory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--teacher-supports", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("replay_output_already_exists")
    old_manifest = args.source_memory / "manifest.json"
    source_receipt = load_json(args.run / "receipt.json")
    if (
        source_receipt["memory_manifest_sha256"]
        != hashlib.sha256(old_manifest.read_bytes()).hexdigest()
    ):
        raise ValueError("source_run_memory_mismatch")
    old = load_memory(args.source_memory)
    new = load_memory(args.memory)
    code = (
        "independently_reviewed_teaching_inputs"
        if args.teacher_supports
        else identity_reuse_code(old, new)
    )
    if code not in {
        "identity_inputs_unchanged",
        "independently_reviewed_teaching_inputs",
    }:
        raise ValueError(code)
    del old
    prepared = prepare_recall(
        new, cached=load_json(args.memory / "recall-preparation.json")
    )
    if prepared.get("outcome") != "prepared":
        raise ValueError("replay_preparation_failed")
    new = {**new, "prepared_recall": prepared}
    teachers, references = teaching_inputs(new) if args.teacher_supports else ({}, {})
    source_mode = (
        "reviewed_teaching_supports"
        if args.teacher_supports
        else "retained_query_replay"
    )
    digest = hashlib.sha256((args.memory / "manifest.json").read_bytes()).hexdigest()
    args.output.mkdir(parents=True)
    started = time.perf_counter()

    def one(entry):
        source = args.run / entry["evidence_path"]
        record: dict = load_json(source)
        uid = record["study_uid"]
        questions, values = {}, {}
        if args.teacher_supports:
            from knee.diagnosis.squint_capacity_control import locate_teacher_profiles

            record = {
                "schema": "knee.squint-study/v1",
                "study_uid": uid,
                "study_status": "reviewed_teaching_supports",
                "objects": locate_teacher_profiles({"study_uid": uid}, teachers)[
                    "objects"
                ],
                "question_reference_inputs": {},
                "identity_source": "independent scoped teaching calls; not new identity inference",
            }
            not_read = {}
        else:
            not_read = _regions_not_read(record["identity_consumption"])
        for question in QUESTIONS:
            objects = record["objects"]
            reference = references.get((uid, question.question_id))
            if reference is not None:
                objects = {
                    **objects,
                    reference["subject"]: {
                        "status": "located",
                        "profile": reference["profile"],
                        "regions": reference["regions"],
                    },
                }
                record["question_reference_inputs"][question.question_id] = reference[
                    "case_id"
                ]
            evidence = _recall_question(
                question, objects, new, uid, False, not_read_as=not_read
            )
            finding = combine_condition(question.question_id, evidence)
            rank = finding.get("rank") or rank_condition(finding)
            questions[question.question_id] = {
                "finding": finding,
                "ranking": rank,
                "objects": evidence,
            }
            values[question.question_id] = rank["value"]
        record.update(
            questions=questions,
            values=values,
            memory_revision=new["revision"],
            retained_query_replay={
                "source_path": str(source),
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "identity_reuse": code,
                "not_rerun": [
                    "location",
                    "identity",
                    "measurement",
                    "additional_observations",
                ],
            },
        )
        record["source_work"] = record.pop("work", {})
        record["work"] = {
            "full_anatomy_runs": 0,
            "source_mode": source_mode,
        }
        path = dump_json_atomic(
            args.output / "studies" / (uid + ".json"), record, compression_preset=0
        )
        print("Recalled " + uid, flush=True)
        return {"study_uid": uid, "evidence_path": str(path.relative_to(args.output))}

    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
        studies = list(pool.map(one, source_receipt["work"]["studies"]))
    receipt = {
        "schema": "knee.squint-run/v1",
        "action": source_mode,
        "source_mode": source_mode,
        "memory_manifest_sha256": digest,
        "memory_revision": new["revision"],
        "studies": len(studies),
        "source_run": str(args.run),
        "source_memory_manifest_sha256": source_receipt["memory_manifest_sha256"],
        "work": {
            "elapsed_seconds": time.perf_counter() - started,
            "studies": studies,
            "full_anatomy_runs": 0,
        },
    }
    (args.output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
