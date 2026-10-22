"""Publish paired configuration precedents from reviewed question presentations.

No new anatomy or diagnosis is inferred: each case composes only the measured
role actually pictured, with unobserved roles explicit, and retains the official
condition call independently. Existing necessary-tissue and multi-site absence
contracts still decide whether a query comparison warrants a whole answer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from knee.diagnosis.squint_configurations import (
    configuration_reference,
)
from knee.diagnosis.squint_identity import identity_condition_views
from knee.diagnosis.squint_locator import prepare_recall
from knee.diagnosis.squint_memory import load_memory, save_memory


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--parent-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = args.parent / "manifest.json"
    parent_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
    if parent_sha != args.parent_sha256:
        raise ValueError("parent_pin_stale")
    if args.output.exists():
        raise ValueError("configuration_child_already_exists")
    parent = load_memory(args.parent)
    scope = identity_condition_views(parent)
    additions = []
    for case in parent["cases"]:
        if case.get("question_reference") is None:
            continue
        allowed = scope["views"].get(case["case_id"])
        if allowed is None:
            raise ValueError("reference_scoped_views_required")
        additions.append(
            configuration_reference(case, [list(v) for v in sorted(allowed)])
        )
    if not additions:
        raise ValueError("no_reviewed_references")
    held = {c["case_id"] for c in parent["cases"]}
    if any(c["case_id"] in held for c in additions):
        raise ValueError("configuration_references_already_present")
    child = {
        **parent,
        "cases": [*parent["cases"], *additions],
        "parent_revision": parent["revision"],
        "revision": parent["revision"] + "+reviewed-question-configurations-r1",
        "grounded_configuration_teaching": {
            "parent_manifest_sha256": parent_sha,
            "case_ids": [c["case_id"] for c in additions],
        },
    }
    print("Preparing reviewed configuration references", flush=True)
    prepared = prepare_recall(child)
    if prepared.get("outcome") != "prepared":
        raise ValueError("configuration_preparation_failed")
    result = save_memory(child, args.output, prepared_recall=prepared)
    result.update(parent_manifest_sha256=parent_sha, added_cases=len(additions))
    (args.output.parent / "publication.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
