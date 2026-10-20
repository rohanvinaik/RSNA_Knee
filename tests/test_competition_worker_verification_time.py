from __future__ import annotations

import math
from argparse import Namespace
from pathlib import Path

import pytest

from scripts import run_interiors as runner


def _completion(archive: Path, seconds: float) -> dict:
    return {
        "schema": "verified_competition_encoding/v1",
        "study_uid": "study",
        "base_spec_sha256": "spec-hash",
        "archive": str(archive),
        "manifest": str(archive),
        "status": "complete",
        "work": {
            "product_verified_arrays": 0,
            "product_verified_bytes": 0,
            "product_verification_seconds": seconds,
        },
        "object_sources": {
            "schema": "knee-object-sources/v1",
            "status": "complete",
            "archive": str(archive),
        },
    }


@pytest.mark.parametrize("seconds", [math.nan, math.inf, -math.inf])
def test_nonfinite_worker_verification_time_refuses_before_stage_or_cleanup(
    monkeypatch, tmp_path, seconds
):
    archive = tmp_path / "encoding" / "study.h5"
    archive.parent.mkdir(parents=True)
    archive.write_bytes(b"worker-owned-product")
    result = {
        "study_uid": "study",
        "series_uids": [],
        "unread": {},
        "main_unread": {},
        "telemetry": {"read_by_no_stage": [], "computed_once": {}},
        "named": {},
        "objects": {},
        "study_map": {"uses": 0},
        "competition_encoding": _completion(archive, seconds),
    }
    args = Namespace(
        encoding_declaration={"version": "test"},
        encoding_prepared={"spec_sha256": "spec-hash"},
        encoding_run=archive.parent,
        competition_output=True,
        competition_worker_encoding=True,
        draw=False,
        run=tmp_path / "run",
        main_run=tmp_path / "main",
    )
    events: list[str] = []

    class Batch:
        def add(self, *_args):
            events.append("stage")

    monkeypatch.setattr(
        runner,
        "_delete_competition_intermediates",
        lambda *_args: events.append("cleanup"),
    )

    with pytest.raises(
        ValueError, match="competition_worker_product_verification_missing"
    ):
        runner.report(result, args, Batch())

    assert events == []
    assert archive.read_bytes() == b"worker-owned-product"
