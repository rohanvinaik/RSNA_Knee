from __future__ import annotations

import io
import json
import lzma
import math

import pytest

from knee.json_store import dump_json_atomic, load_json


def _unbuffered_xz(value, default=None):
    destination = io.BytesIO()
    encoder = json.JSONEncoder(
        default=default, separators=(",", ":"), ensure_ascii=True, allow_nan=True
    )
    with lzma.LZMAFile(destination, "wb", format=lzma.FORMAT_XZ, preset=6) as stream:
        for chunk in encoder.iterencode(value):
            stream.write(chunk.encode("utf-8"))
        stream.write(b"\n")
    return destination.getvalue()


def test_buffered_writer_keeps_exact_xz_bytes_and_json_semantics(tmp_path):
    class CustomValue:
        pass

    value = {
        "text": "knee-é-☃" + "x" * 1_500_000,
        "ordered_second": 2,
        "signed_zero": -0.0,
        "nan": float("nan"),
        "custom": CustomValue(),
    }

    def default(_value):
        return {"custom_value": "preserved"}

    expected = _unbuffered_xz(value, default=default)
    destination = tmp_path / "large.json.xz"

    dump_json_atomic(destination, value, default=default)

    assert destination.read_bytes() == expected
    loaded = load_json(destination)
    assert list(loaded) == list(value)
    assert loaded["text"] == value["text"]
    assert loaded["ordered_second"] == 2
    assert loaded["signed_zero"] == 0.0
    assert math.copysign(1.0, loaded["signed_zero"]) == -1.0
    assert json.loads(json.dumps(loaded))["custom"] == {"custom_value": "preserved"}
    assert math.isnan(loaded["nan"])
    assert not list(tmp_path.glob("*.part"))


def test_one_million_tiny_encoder_pieces_become_bounded_lzma_writes(
    tmp_path, monkeypatch
):
    def one_million_pieces(_self, _value, _one_shot=False):
        yield '{"value":"'
        for _ in range(1_000_000):
            yield "x"
        yield '"}'

    writes = []
    real_write = lzma.LZMAFile.write

    def counted_write(self, data):
        writes.append(len(data))
        return real_write(self, data)

    monkeypatch.setattr(json.JSONEncoder, "iterencode", one_million_pieces)
    monkeypatch.setattr(lzma.LZMAFile, "write", counted_write)
    destination = tmp_path / "many-pieces.json.xz"

    dump_json_atomic(destination, {"not_used_by_fixture": True})

    assert len(writes) == 16
    assert sum(writes) == len('{"value":"') + 1_000_000 + len('"}') + 1
    assert max(writes) <= 64 * 1024
    assert load_json(destination) == {"value": "x" * 1_000_000}


def test_buffered_writer_cleans_part_and_preserves_destination_on_failure(
    tmp_path, monkeypatch
):
    from knee import json_store

    destination = tmp_path / "stable.json.xz"
    dump_json_atomic(destination, {"stable": True})
    original = destination.read_bytes()

    def fail_replace(*_args):
        raise OSError("replace_failed")

    monkeypatch.setattr(json_store.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replace_failed"):
        dump_json_atomic(destination, {"new": "y" * 100_000})

    assert destination.read_bytes() == original
    assert not list(tmp_path.glob("*.part"))
