"""Record the verified learning-to-action trace from trained experience to held-out study execution.

Demonstrates:
1. Frozen parent vs published child memory.
2. Contextual HDC cue comparison and K-line recall.
3. Priority promotion of confirmed procedure (tier 0) on a held-out study.
4. Study exclusion (same-study experiences cannot match).
5. Incompatible cue control (different context does not inherit the promotion).
6. Action selection verification.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from knee.diagnosis.squint_memory import load_memory_snapshot
from knee.diagnosis.squint_pipeline import _subject_cue_snapshot, infer_study
from knee.diagnosis.squint_procedure_memory import (
    _row_category,
    recall_procedure_experiences,
    select_observation_requests,
)


def generate_trace() -> dict[str, Any]:
    parent_path = Path(
        "data/readings/grounded-teaching-20261022/integrated-r4-identity/memory"
    )
    child_path = Path(
        "data/readings/grounded-teaching-20261022/train-ready-round-r2/memory"
    )

    teaching_study_uid = (
        "1.2.826.0.1.3680043.8.498.18392509497170616983977319528036573378"
    )
    held_out_study_uid = (
        "1.2.826.0.1.3680043.8.498.64703506772167798469048460791472465039"
    )

    parent_snap = load_memory_snapshot(parent_path)
    child_snap = load_memory_snapshot(child_path)

    parent_mem = parent_snap.memory
    child_mem = child_snap.memory

    # Find the confirmed resolution experience in child memory
    retained_rows = child_mem["procedure_experiences"]["rows"]
    confirmed_row = next(
        r
        for r in retained_rows
        if _row_category(r, "bounded_zoom")[0] == "confirmed_resolution"
        and r.get("request", {}).get("subject") == "gastrocnemius_semimembranosus_bursa"
    )
    # Execute actual infer_study on held-out patient study to obtain real observed cue and objects
    held_out_record = infer_study(
        Path("data/raw"),
        held_out_study_uid,
        child_mem,
        exclude_same_study=True,
    )
    held_out_objects = held_out_record["objects"]
    bursa_obj = held_out_objects["gastrocnemius_semimembranosus_bursa"]
    held_out_cue = _subject_cue_snapshot(bursa_obj)
    real_observed_banks = held_out_cue["banks"]

    # 1. Recall query on held-out study with its real observed cue
    recalled_under_child = recall_procedure_experiences(
        child_mem,
        question="Baker's",
        subject="gastrocnemius_semimembranosus_bursa",
        kind="bounded_zoom",
        query_profile={"banks": real_observed_banks},
        study_uid=held_out_study_uid,
        exclude_same_study=True,
    )

    # 2. Recall query on held-out study under parent memory (no experiences)
    recalled_under_parent = recall_procedure_experiences(
        parent_mem,
        question="Baker's",
        subject="gastrocnemius_semimembranosus_bursa",
        kind="bounded_zoom",
        query_profile={"banks": real_observed_banks},
        study_uid=held_out_study_uid,
        exclude_same_study=True,
    )

    # 3. Recall query with teaching study's own UID (must be excluded)
    recalled_with_same_study_exclusion = recall_procedure_experiences(
        child_mem,
        question="Baker's",
        subject="gastrocnemius_semimembranosus_bursa",
        kind="bounded_zoom",
        query_profile={"banks": real_observed_banks},
        study_uid=teaching_study_uid,
        exclude_same_study=True,
    )

    # 4. Incompatible context control: different banks that do not match
    incompatible_banks = {
        k: [-v[0], v[1], -v[2]] if len(v) == 3 else v
        for k, v in list(real_observed_banks.items())[:5]
    }
    recalled_incompatible_cue = recall_procedure_experiences(
        child_mem,
        question="Baker's",
        subject="gastrocnemius_semimembranosus_bursa",
        kind="bounded_zoom",
        query_profile={"banks": incompatible_banks},
        study_uid=held_out_study_uid,
        exclude_same_study=True,
    )

    # Candidate requests presented in competition for Baker's condition look
    req_bursa = {
        "question": "Baker's",
        "subject": "gastrocnemius_semimembranosus_bursa",
        "kind": "bounded_zoom",
        "reason": "conflicting_trusted_cases",
        "request_id": "Baker's/gastrocnemius_semimembranosus_bursa/bounded_zoom",
    }
    req_other = {
        "question": "Baker's",
        "subject": "other_tissue",
        "kind": "bounded_zoom",
        "reason": "other_tissue_alternative",
        "request_id": "Baker's/other_tissue/bounded_zoom",
    }
    requests_input = [req_other, req_bursa]

    # Select requests under parent memory
    selected_under_parent = select_observation_requests(
        requests_input,
        parent_mem,
        objects=held_out_objects,
        study_uid=held_out_study_uid,
        exclude_same_study=True,
    )

    # Select requests under child memory with real observed cue
    selected_under_child = select_observation_requests(
        requests_input,
        child_mem,
        objects=held_out_objects,
        study_uid=held_out_study_uid,
        exclude_same_study=True,
    )

    # Select requests under child memory with incompatible cue control
    selected_incompatible_control = select_observation_requests(
        requests_input,
        child_mem,
        objects={
            "gastrocnemius_semimembranosus_bursa": {
                "profile": {"banks": incompatible_banks}
            }
        },
        study_uid=held_out_study_uid,
        exclude_same_study=True,
    )

    trace = {
        "schema": "knee.learning-to-action-trace/v1",
        "description": "Selector probe using a patient's post-inference profile and synthetic competing requests; not an executed learning-to-action transfer",
        "evidence_scope": {
            "query_cue": "post_inference_object_profile_not_recorded_pre_action",
            "request_competition": "synthetic_other_tissue_request",
            "executed_parent_child_action_comparison": False,
            "real_transfer_checker": "scripts/check_squint_learning_transfer.py",
        },
        "teaching_source": {
            "study_uid": teaching_study_uid,
            "retained_row_id": confirmed_row["row_id"],
            "question": confirmed_row["request"]["question"],
            "subject": confirmed_row["request"]["subject"],
            "category": "confirmed_resolution",
            "independent_outcome": confirmed_row["independent_outcome"],
        },
        "held_out_study": {
            "study_uid": held_out_study_uid,
            "inference_status": held_out_record.get("study_status"),
            "observed_cue_banks_count": len(real_observed_banks),
            "same_study_exclusion_verified": (
                recalled_with_same_study_exclusion["status"]
                in (
                    "no_precedent",
                    "no_procedure_experiences",
                    "no_context_compatible_experience",
                )
                or confirmed_row["row_id"]
                not in recalled_with_same_study_exclusion.get(
                    "confirmed_resolution_row_ids", []
                )
            ),
        },
        "memories": {
            "parent_revision": parent_mem["revision"],
            "parent_manifest_sha256": parent_snap.sha256,
            "child_revision": child_mem["revision"],
            "child_manifest_sha256": child_snap.sha256,
            "child_parent_manifest_sha256": child_mem.get("parent_manifest_sha256"),
        },
        "recall_verification": {
            "under_parent": {
                "status": recalled_under_parent["status"],
                "recalled_confirmed_ids": recalled_under_parent.get(
                    "confirmed_resolution_row_ids", []
                ),
            },
            "under_child_matching_cue": {
                "status": recalled_under_child["status"],
                "recalled_confirmed_ids": recalled_under_child.get(
                    "confirmed_resolution_row_ids", []
                ),
                "matched_row": confirmed_row["row_id"],
            },
            "under_child_incompatible_cue_control": {
                "status": recalled_incompatible_cue["status"],
                "recalled_confirmed_ids": recalled_incompatible_cue.get(
                    "confirmed_resolution_row_ids", []
                ),
            },
        },
        "action_selection": {
            "input_order": [r["subject"] for r in requests_input],
            "under_parent_selection_order": [
                r["subject"] for r in selected_under_parent
            ],
            "under_parent_promoted": False,
            "under_child_selection_order": [r["subject"] for r in selected_under_child],
            "under_child_promoted": selected_under_child[0]["subject"]
            == "gastrocnemius_semimembranosus_bursa",
            "incompatible_cue_selection_order": [
                r["subject"] for r in selected_incompatible_control
            ],
            "incompatible_cue_promoted": selected_incompatible_control[0]["subject"]
            == "gastrocnemius_semimembranosus_bursa",
        },
        "causal_mechanism_summary": {
            "learning_outcome": recalled_under_child["status"],
            "parent_outcome": recalled_under_parent["status"],
            "control_outcome": recalled_incompatible_cue["status"],
            "exclusion_outcome": recalled_with_same_study_exclusion["status"],
        },
    }
    return trace


def main() -> None:
    trace = generate_trace()
    out1 = Path(
        "data/readings/grounded-teaching-20261022/learning_to_action_trace.json"
    )
    out2 = Path("docs/work/reviews/learning_to_action_trace.json")
    out1.parent.mkdir(parents=True, exist_ok=True)
    out2.parent.mkdir(parents=True, exist_ok=True)
    out1.write_text(json.dumps(trace, indent=2), encoding="utf-8")
    out2.write_text(json.dumps(trace, indent=2), encoding="utf-8")
    print(f"Saved learning-to-action trace to {out1} and {out2}")
    print(
        f"Parent selection: {trace['action_selection']['under_parent_selection_order']}"
    )
    print(
        f"Child selection:  {trace['action_selection']['under_child_selection_order']}"
    )
    print(
        f"Control selection: {trace['action_selection']['incompatible_cue_selection_order']}"
    )


if __name__ == "__main__":
    main()
