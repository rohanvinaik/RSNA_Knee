#!/usr/bin/env python3
"""Compile one bootstrap squint memory with a chosen profile writer.

Bootstrap tooling, never imported by production. The real entry point's teach
route (``scripts/run_interiors.py --diagnostic-mode teach``) compiles with the
default ``squint-v1`` writer only; this script selects the writer and keeps its
receipt. The memory directory must be fresh: a published memory is never
overwritten, and a territory memory never mixes with a v1 one.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
import time
from pathlib import Path

from knee.diagnosis.squint_memory import (
    BOOTSTRAP_WRITERS,
    WRITER_V1,
    compile_bootstrap,
)

_DEFAULT_LEG_MAPS = "knee.diagnosis.squint_leg:leg_maps"


def _leg_maps(reference: str):
    """Resolve ``module:callable``: the territory writer's explicit leg-map input."""
    module_name, separator, attribute = reference.partition(":")
    if not separator or not module_name or not attribute:
        raise SystemExit("leg_maps_reference_invalid")
    value = getattr(importlib.import_module(module_name), attribute, None)
    if not callable(value):
        raise SystemExit("leg_maps_reference_not_callable")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, required=True, help="train.csv and the DICOM studies"
    )
    parser.add_argument(
        "--products", type=Path, required=True, help="existing full H5 products"
    )
    parser.add_argument(
        "--memory", type=Path, required=True, help="fresh directory to publish into"
    )
    parser.add_argument("--writer", choices=BOOTSTRAP_WRITERS, default=WRITER_V1)
    parser.add_argument(
        "--leg-maps",
        help=f"module:callable for the territory writer (default {_DEFAULT_LEG_MAPS})",
    )
    parser.add_argument(
        "--study-uid",
        nargs="+",
        help="only these studies (default: every fully labelled study)",
    )
    parser.add_argument("--io-workers", type=int, default=8)
    parser.add_argument(
        "--receipt", type=Path, help="write the receipt here; refuses an existing file"
    )
    args = parser.parse_args(argv)
    if args.receipt is not None and args.receipt.exists():
        raise SystemExit("receipt_already_exists")
    started = time.perf_counter()
    store = compile_bootstrap(
        args.root,
        args.products,
        args.memory,
        selected_uids=tuple(args.study_uid) if args.study_uid else None,
        io_workers=args.io_workers,
        writer=args.writer,
        leg_maps=_leg_maps(args.leg_maps) if args.leg_maps else None,
    )
    result = {
        "schema": "knee.squint-memory-compile/v1",
        "argv": list(sys.argv if argv is None else argv),
        "writer": args.writer,
        "leg_maps": args.leg_maps
        or (None if args.writer == WRITER_V1 else _DEFAULT_LEG_MAPS),
        "store": store,
        "work": {
            "elapsed_seconds": time.perf_counter() - started,
            "full_anatomy_runs": 0,
        },
    }
    text = json.dumps(result, sort_keys=True)
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        with args.receipt.open("x", encoding="utf-8") as stream:
            stream.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
