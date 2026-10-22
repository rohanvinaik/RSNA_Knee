"""Publish independently reviewed visual identity cases into a child memory."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from knee.diagnosis.squint_memory import SquintMemoryError
from knee.diagnosis.squint_visual_teaching import (
    VisualTeachingError,
    publish_visual_cases,
)


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", type=Path, required=True)
    parser.add_argument("--parent-sha256", required=True)
    parser.add_argument("--additions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prepare-recall", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = publish_visual_cases(
            args.parent,
            args.parent_sha256,
            args.additions,
            args.output,
            build_recall_cache=args.prepare_recall,
        )
    except (
        VisualTeachingError,
        SquintMemoryError,
        OSError,
        json.JSONDecodeError,
    ) as error:
        parser.exit(2, f"{getattr(error, 'code', type(error).__name__)}: {error}\n")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
