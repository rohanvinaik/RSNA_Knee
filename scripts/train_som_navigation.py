#!/usr/bin/env python3
"""Train three-stage navigation on a pinned fixed-HDC dataset; export NumPy runtime."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from knee.diagnosis.som_training import TrainingConfig, train_navigation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset", required=True, help="folder containing dataset.npz and schema.json"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="new artifact directory, or explicit resume target",
    )
    parser.add_argument("--resume", action="store_true")
    for name, default in (
        ("hidden", 32),
        ("context", 8),
        ("gate", 16),
        ("epochs1", 20),
        ("epochs2", 20),
        ("epochs3", 10),
        ("batch-size", 16),
        ("seed", 0),
        ("threads", 4),
        ("pab-window", 20),
        ("pab-patience", 5),
        ("max-no-improve", 40),
    ):
        parser.add_argument("--" + name, type=int, default=default)
    parser.add_argument("--lr1", type=float, default=0.001)
    parser.add_argument("--lr2", type=float, default=0.001)
    parser.add_argument("--weight-decay", type=float, default=0.01)
    parser.add_argument(
        "--pab-thresholds", type=float, nargs=3, default=(0.015, 0.01, 0.008)
    )
    parser.add_argument("--device", choices=("cpu", "mps"), default="cpu")
    args = vars(parser.parse_args(argv))
    dataset, output, resume = (args.pop(k) for k in ("dataset", "output", "resume"))
    args["pab_thresholds"] = tuple(args["pab_thresholds"])
    result = train_navigation(dataset, output, TrainingConfig(**args), resume=resume)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
