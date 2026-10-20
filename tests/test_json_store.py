"""Lossless JSON sidecars preserve values and legacy reader behavior."""

from __future__ import annotations

import json
import lzma
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

import knee.json_store as metadata
from knee.json_store import (
    compressed_path,
    dump_json_atomic,
    load_json,
    resolve_json_path,
)
from scripts import run_interiors as run

VALUE = {
    "request": {"prominence_mm": 3.0, "offsets_mm": [0.0, -0.0], "none": None},
    "records": [{"study_uid": "é☃", "n": 1, "x": 2.5, "ok": True}],
    "unread": {},
}


def legacy(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, separators=(",", ":")) + "\n", encoding="utf-8")


def test_write_is_standard_compact_utf8_json_inside_outer_xz(tmp_path):
    path = tmp_path / "metadata.json.xz"
    assert dump_json_atomic(path, VALUE) == path
    raw = lzma.decompress(path.read_bytes(), format=lzma.FORMAT_XZ)
    assert raw == (json.dumps(VALUE, separators=(",", ":")) + "\n").encode("utf-8")
    assert load_json(path) == VALUE
    assert not list(tmp_path.glob("*.part"))


def test_encoder_streams_chunks_and_keeps_custom_default(tmp_path, monkeypatch):
    seen = []
    real = json.JSONEncoder.iterencode

    def counted(self, value, _one_shot=False):
        for chunk in real(self, value, _one_shot):
            seen.append(chunk)
            yield chunk

    monkeypatch.setattr(json.JSONEncoder, "iterencode", counted)
    path = tmp_path / "values.json.xz"
    dump_json_atomic(
        path,
        {"numbers": [np.int64(4), np.float32(0.25)]},
        default=run.plain,
    )
    assert len(seen) > 2
    assert load_json(path) == {"numbers": [4, 0.25]}


def test_legacy_path_and_sidecar_path_resolution_and_precedence(tmp_path):
    plain = tmp_path / "receipt.json"
    sidecar = tmp_path / "receipt.json.xz"
    assert compressed_path(plain) == sidecar
    legacy(plain, {"source": "legacy"})
    assert resolve_json_path(plain) == plain
    assert load_json(plain) == {"source": "legacy"}
    sidecar.write_bytes(
        lzma.compress(json.dumps({"source": "sidecar"}).encode("utf-8"))
    )
    assert load_json(plain) == {"source": "legacy"}
    assert load_json(sidecar) == {"source": "sidecar"}
    plain.unlink()
    assert resolve_json_path(plain) == sidecar
    assert load_json(plain) == {"source": "sidecar"}


def test_requested_sidecar_can_read_only_legacy_file(tmp_path):
    plain = tmp_path / "study_map.json"
    legacy(plain, VALUE)
    assert load_json(tmp_path / "study_map.json.xz") == VALUE


def test_empty_malformed_plain_and_truncated_xz_are_not_silently_accepted(tmp_path):
    empty = tmp_path / "empty.json"
    empty.write_text("", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        load_json(empty)
    broken = tmp_path / "broken.json.xz"
    broken.write_bytes(b"\xfd7zXZ\x00\x00\x00\x00")
    with pytest.raises((EOFError, lzma.LZMAError)):
        load_json(broken)


def test_write_serialization_failure_preserves_existing_destination_and_cleans_part(
    tmp_path,
):
    dest = tmp_path / "receipt.json.xz"
    dump_json_atomic(dest, VALUE)
    old = dest.read_bytes()
    with pytest.raises(TypeError):
        dump_json_atomic(dest, {"bad": object()})
    assert dest.read_bytes() == old
    assert not list(tmp_path.glob("*.part"))


def test_atomic_replace_failure_preserves_existing_destination_and_cleans_part(
    tmp_path, monkeypatch
):
    dest = tmp_path / "receipt.json.xz"
    dump_json_atomic(dest, VALUE)
    before = dest.read_bytes()

    def fail(*_args):
        raise OSError("replace_failed")

    monkeypatch.setattr(metadata.os, "replace", fail)
    with pytest.raises(OSError, match="replace_failed"):
        dump_json_atomic(dest, {"replacement": True})
    assert dest.read_bytes() == before
    assert not list(tmp_path.glob("*.part"))


def test_nonserializable_default_failure_keeps_the_legacy_file(tmp_path):
    legacy_path = tmp_path / "receipt.json"
    legacy(legacy_path, VALUE)
    with pytest.raises(TypeError, match="not_json_serializable"):
        dump_json_atomic(
            tmp_path / "receipt.json.xz", {"bad": object()}, default=run.plain
        )
    assert legacy_path.is_file() and load_json(legacy_path) == VALUE
    assert not (tmp_path / "receipt.json.xz").exists()
    assert not list(tmp_path.glob("*.part"))


def _record(study: str, series: str) -> dict:
    return {"study_uid": study, "series_uid": series}


def test_receipt_rerun_merges_all_studies_into_sidecar_and_removes_legacy(tmp_path):
    run.write_receipt(tmp_path, "A", ["a1"], [_record("A", "a1")], {}, {"run": 1})
    run.write_receipt(tmp_path, "B", ["b1"], [_record("B", "b1")], {}, {"run": 2})
    run.write_receipt(
        tmp_path,
        "A",
        ["a1", "a2"],
        [_record("A", "a1"), _record("A", "a2")],
        {},
        {"run": 3},
    )
    assert (tmp_path / "receipt.json.xz").is_file()
    assert not (tmp_path / "receipt.json").exists()
    value = load_json(tmp_path / "receipt.json")
    assert value["records"] == [
        _record("B", "b1"),
        _record("A", "a1"),
        _record("A", "a2"),
    ]
    assert value["telemetry"] == {"B": {"run": 2}, "A": {"run": 3}}


def test_old_receipt_is_read_before_first_sidecar_write(tmp_path):
    original = run.merged_receipt(
        None, run.REQUEST, "A", ["a1"], [_record("A", "a1")], {}, {"run": 1}
    )
    legacy(tmp_path / "receipt.json", original)
    run.write_receipt(tmp_path, "B", ["b1"], [_record("B", "b1")], {}, {"run": 2})
    assert not (tmp_path / "receipt.json").exists()
    merged = load_json(tmp_path / "receipt.json.xz")
    assert merged["records"] == [_record("A", "a1"), _record("B", "b1")]


def test_receipt_request_mismatch_does_not_replace_existing_sidecar(tmp_path):
    old = run.merged_receipt(
        None,
        {**run.REQUEST, "different": True},
        "A",
        ["a1"],
        [_record("A", "a1")],
        {},
        None,
    )
    dump_json_atomic(tmp_path / "receipt.json.xz", old)
    before = (tmp_path / "receipt.json.xz").read_bytes()
    with pytest.raises(ValueError, match="receipt_request_differs"):
        run.write_receipt(tmp_path, "B", ["b1"], [_record("B", "b1")], {}, None)
    assert (tmp_path / "receipt.json.xz").read_bytes() == before


def test_finish_map_writes_and_names_the_actual_sidecar(tmp_path, monkeypatch):
    counts = {
        "objects": 1,
        "complete": 1,
        "partial": 0,
        "pairs_complete": 0,
        "pairs_unresolved": 0,
        "predictions": 0,
        "refinements": 0,
        "uses": {},
    }
    record = {
        "counts": counts,
        "construction": "three_key_planes",
        "number": np.int64(8),
    }
    smap = SimpleNamespace(
        record=lambda _ideal: record, summary=lambda _ideal: {"status": "ok"}
    )
    monkeypatch.setattr(
        run, "ledger", SimpleNamespace(record=lambda *_args, **_kwargs: None)
    )
    from typing import cast

    compact = run.finish_map(
        cast(run.MapContext, SimpleNamespace(smap=smap, ideal=None)), tmp_path, "S"
    )
    assert compact["file"] == "S/study_map.json.xz"
    actual = tmp_path / compact["file"]
    assert actual.is_file()
    assert not (tmp_path / "S" / "study_map.json").exists()
    assert load_json(actual)["number"] == 8


def test_standard_encoder_preserves_nonfinite_values_and_mapping_order(tmp_path):
    path = tmp_path / "ordered.json.xz"
    value = {"second": 2, "first": -0.0, "not_finite": float("nan")}
    dump_json_atomic(path, value)
    raw = lzma.decompress(path.read_bytes()).decode("utf-8")
    assert raw == '{"second":2,"first":-0.0,"not_finite":NaN}\n'
    loaded = load_json(path)
    assert list(loaded) == ["second", "first", "not_finite"]
    assert np.signbit(loaded["first"]) and np.isnan(loaded["not_finite"])


def test_compare_cli_reads_plain_and_xz_receipts(tmp_path, monkeypatch, capsys):
    import sys

    from scripts import compare_receipts

    record = {
        "study_uid": "s",
        "series_uid": "x",
        "arrays": {},
        "interiors": {},
        "assignments": {},
    }
    value = {"records": [record], "request": {}, "unread": {}}
    legacy(tmp_path / "before" / "receipt.json", value)
    dump_json_atomic(tmp_path / "after" / "receipt.json.xz", value)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "compare_receipts",
            str(tmp_path / "before" / "receipt.json"),
            str(tmp_path / "after" / "receipt.json.xz"),
        ],
    )
    with pytest.raises(SystemExit) as stop:
        compare_receipts.main()
    assert stop.value.code == 0
    assert "records: before 1, after 1" in capsys.readouterr().out


def test_map_variation_reports_actual_map_sidecar_path(tmp_path):
    from scripts import map_pair_variation

    run_dir = tmp_path / "run"
    dump_json_atomic(run_dir / "receipt.json.xz", {"records": [{"study_uid": "s"}]})
    dump_json_atomic(
        run_dir / "s" / "study_map.json.xz",
        {
            "schema": "study_map/v1",
            "construction": "single_section_centroid",
            "knee": "R",
            "scale": {"mm": 100.0, "source": "test"},
            "objects": {},
        },
    )
    result = map_pair_variation.analyze(run_dir)
    assert result["studies"]["s"]["path"] == str(run_dir / "s" / "study_map.json.xz")
    assert result["studies"]["s"]["status"] == "wrong_construction"


def test_key_plane_and_work_count_readers_accept_compressed_metadata(tmp_path):
    from scripts import joint_work_counts, key_points

    dump_json_atomic(
        tmp_path / "key-planes.json.xz",
        {"schema": key_points.KEY_PLANES_SCHEMA, "studies": {"s": {"planes": []}}},
    )
    assert key_points.load_key_planes(tmp_path / "key-planes.json.xz") == {
        "s": {"planes": []}
    }
    dump_json_atomic(
        tmp_path / "receipt.json.xz",
        {"records": [{"series_uid": "q"}], "telemetry": {"s": {"events": {}}}},
    )
    records, telemetry = joint_work_counts.load(tmp_path)
    assert list(records) == ["q"]
    assert telemetry == {"s": {"events": {}}}


def test_drawing_reader_loads_sidecar_and_keeps_existing_npz_address(
    tmp_path, monkeypatch
):
    from scripts import object_joint

    run_dir = tmp_path / "run"
    study = run_dir / "s"
    study.mkdir(parents=True)
    np.savez(study / "arrays.npz", probe=np.array([4, 9], dtype=np.int16))
    record = {
        "study_uid": "s",
        "series_uid": "series",
        "artifact": "s/arrays.npz",
        "arrays": {},
        "joint": {"pointed_planes": []},
    }
    dump_json_atomic(run_dir / "receipt.json", {"records": [record]})
    seen = []

    def picture(_record, _part, arrays, _volume_of, out):
        seen.append(arrays["probe"].tolist())
        return out / "panel.png"

    monkeypatch.setattr(object_joint, "_picture", picture)
    result = object_joint.draw(
        run_dir, "s", tmp_path / "pictures", lambda _uid: np.zeros((2, 2))
    )
    assert result == [tmp_path / "pictures" / "panel.png"]
    assert seen == [[4, 9]]
    assert not (run_dir / "receipt.json").exists()
