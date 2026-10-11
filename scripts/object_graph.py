"""Validate and draw a development-only graph; it contains no anatomical assertions."""

import argparse
import json
import os
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

os.environ["HAMILTON_TELEMETRY_ENABLED"] = "false"
from hamilton import driver

from knee.collapse.analysis import AnalysisRequest
from workbench.graph import object_measurements


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--study-uid", help="also execute one real study")
    parser.add_argument("--prominence-mm", type=float)
    parser.add_argument("--conversation", action="store_true")
    parser.add_argument("--backend", choices=("reference", "jit"), default="reference")
    args = parser.parse_args()
    request = AnalysisRequest(
        3.0,
        tuple(-3.0 + 0.5 * i for i in range(13)),
        (0.0, 0.0, 1.0),
        args.backend,
        prominence_mm=args.prominence_mm,
        conversation=args.conversation,
    )
    inputs = {
        "corpus_root": Path("data/raw"),
        "study_uid": args.study_uid or "structural-validation-only",
        "analysis_request": request,
    }
    graph = driver.Builder().with_modules(object_measurements).build()
    graph.validate_execution(
        ["study_run", "support_records", "work_counts"], inputs=inputs
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    graph.display_all_functions(str(args.out), render_kwargs={"format": "svg"})
    print(
        "graph_valid: production study route -> returned measurements -> support/work records"
    )
    if args.study_uid:
        outputs = graph.execute(["support_records", "work_counts"], inputs=inputs)
        report = {
            "study_uid": args.study_uid,
            "request": asdict(request),
            "observer_sha256": sha256(
                Path(object_measurements.__file__).read_bytes()
            ).hexdigest(),
            "runner_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
            "outputs": outputs,
        }
        report_path = args.out.with_suffix(".execution.json")
        report_path.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
