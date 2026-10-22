"""Both offline wrappers refuse malformed CSV rows before indexing their cells."""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest


@pytest.fixture(
    params=("squint-production/run_squint.py", "squint-scaling/run_scaling.py")
)
def csv_wrapper(request, tmp_path, monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("SQUINT_KAGGLE_WORKING", str(tmp_path / "working"))
    path = root / "kaggle" / request.param
    name = "csv_shape_" + path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    return module


def test_valid_template_and_exact_endpoint_csv_are_accepted(csv_wrapper, tmp_path):
    header = ["StudyInstanceUID", *(f"condition_{i}" for i in range(12))]
    source = tmp_path / "template.csv"
    source.write_text(",".join(header) + "\n" + "study-1," + ",".join([""] * 12) + "\n")
    template = csv_wrapper.read_template(source)
    assert template["header"] == header
    assert template["uids"] == ["study-1"]
    produced = tmp_path / "produced.csv"
    produced.write_text(
        ",".join(header) + "\nstudy-1," + ",".join(["0", "1"] * 6) + "\n"
    )
    result = csv_wrapper.validate_csv(template, produced)
    assert result["rows"] == 1
    assert result["columns"] == 13
    assert result["sha256"] == hashlib.sha256(produced.read_bytes()).hexdigest()


@pytest.mark.parametrize("row", ("\n", "study-1\n"), ids=("blank", "ragged"))
def test_malformed_template_row_is_a_named_refusal(csv_wrapper, tmp_path, row):
    source = tmp_path / "template.csv"
    header = ["StudyInstanceUID", *(f"condition_{i}" for i in range(12))]
    source.write_text(",".join(header) + "\n" + row)
    with pytest.raises(csv_wrapper.SetupError, match="ragged"):
        csv_wrapper.read_template(source)


@pytest.mark.parametrize("row", ("\n", "study-1\n"), ids=("blank", "ragged"))
def test_malformed_produced_row_is_a_named_refusal(csv_wrapper, tmp_path, row):
    header = ["StudyInstanceUID", *(f"condition_{i}" for i in range(12))]
    produced = tmp_path / "produced.csv"
    produced.write_text(",".join(header) + "\n" + row)
    template = {"header": header, "uids": ["study-1"]}
    with pytest.raises(csv_wrapper.SetupError, match="cells"):
        csv_wrapper.validate_csv(template, produced)
