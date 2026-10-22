"""Pinned split, masked supervision and three-stage export intent."""

from __future__ import annotations

import json

import numpy as np
import pytest

from knee.diagnosis import som_training
from knee.diagnosis.som_navigation import load_navigation, predict_navigation
from knee.diagnosis.som_training import (
    TrainingConfig,
    load_training_data,
    masked_binary_loss,
    train_navigation,
)


def dataset(folder):
    folder.mkdir()
    schema = {
        "feature_names": [f"bank_{i}" for i in range(5)],
        "labels": [f"condition_{i}" for i in range(12)],
        "specialist_groups": [
            {
                "name": "bone",
                "feature_indices": [0, 1],
                "condition_indices": list(range(12)),
            },
            {
                "name": "fluid",
                "feature_indices": [2, 3],
                "condition_indices": list(range(6, 12)),
            },
        ],
    }
    (folder / "schema.json").write_text(json.dumps(schema))
    rng = np.random.default_rng(12)
    X = rng.normal(size=(12, 5)).astype(np.float32)
    X[:, 4] = 7  # A constant feature has unit scale, not a division by zero.
    y = rng.integers(0, 2, size=(12, 12)).astype(np.float32)
    mask = np.ones((12, 12), dtype=bool)
    mask[:, 1] = False
    y[:, 1] = np.nan  # The unknown channel is deliberately not a negative.
    np.savez_compressed(
        folder / "dataset.npz",
        X=X,
        y=y,
        label_mask=mask,
        study_uids=np.array([f"study_{i}" for i in range(12)]),
        train_mask=np.arange(12) < 8,
        validation_mask=np.arange(12) >= 8,
    )
    return folder


def test_known_targets_survive_and_unknown_nan_is_masked(tmp_path):
    loaded = load_training_data(dataset(tmp_path / "dataset"))
    assert loaded.label_mask[:, 0].all()
    assert not loaded.label_mask[:, 1].any()
    assert np.isfinite(loaded.y).all()
    assert set(loaded.study_uids[loaded.train_mask]).isdisjoint(
        loaded.study_uids[loaded.validation_mask]
    )


def test_same_study_cannot_cross_splits(tmp_path):
    folder = dataset(tmp_path / "dataset")
    with np.load(folder / "dataset.npz") as saved:
        arrays = {k: saved[k] for k in saved.files}
    arrays["study_uids"][8] = arrays["study_uids"][0]
    np.savez_compressed(folder / "dataset.npz", **arrays)
    with pytest.raises(ValueError, match="study may not cross"):
        load_training_data(folder)


def test_unknown_label_has_no_loss_or_gradient():
    torch = pytest.importorskip("torch")
    logits = torch.tensor([[0.0, 0.0]], requires_grad=True)
    targets = torch.tensor([[1.0, float("nan")]])
    loss = masked_binary_loss(logits, targets, torch.tensor([[True, False]]))
    loss.backward()
    assert torch.isfinite(loss)
    assert logits.grad[0, 0] < 0
    assert logits.grad[0, 1] == 0


def test_three_stages_freeze_then_joint_and_export_matches(tmp_path):
    pytest.importorskip("torch")
    folder = dataset(tmp_path / "dataset")
    out = tmp_path / "model"
    config = TrainingConfig(
        hidden=4,
        context=2,
        gate=3,
        epochs1=1,
        epochs2=1,
        epochs3=1,
        batch_size=4,
        threads=1,
        weight_decay=0,
    )
    receipt = train_navigation(folder, out, config)
    assert [row["stage"] for row in receipt["stages"]] == [1, 2, 3]
    assert receipt["stages"][0]["specialist_parameters_changed"]
    assert not receipt["stages"][0]["gate_parameters_changed"]
    assert not receipt["stages"][1]["specialist_parameters_changed"]
    assert receipt["stages"][1]["gate_parameters_changed"]
    assert receipt["stages"][2]["specialist_parameters_changed"]
    assert receipt["stages"][2]["maximum_learning_rate"] == config.lr1 / 10
    assert receipt["numpy_torch_max_abs_error"] < 2e-6
    assert receipt["numpy_torch_trust_max_abs_error"] < 2e-6
    model = load_navigation(out)
    assert model.scale[4] == 1
    values = predict_navigation(model, load_training_data(folder).X)
    assert values.shape == (12, 12) and np.isfinite(values).all()
    with pytest.raises(ValueError, match="already exists"):
        train_navigation(folder, out, config)


def test_resume_is_bound_to_dataset_and_config(tmp_path):
    pytest.importorskip("torch")
    folder = dataset(tmp_path / "dataset")
    out = tmp_path / "model"
    config = TrainingConfig(
        hidden=4,
        context=2,
        gate=3,
        epochs1=1,
        epochs2=1,
        epochs3=1,
        batch_size=4,
        threads=1,
    )
    train_navigation(folder, out, config)
    resumed = train_navigation(folder, out, config, resume=True)
    assert len(resumed["stages"]) == 3
    with np.load(folder / "dataset.npz") as saved:
        arrays = {k: saved[k] for k in saved.files}
    arrays["X"][0, 0] += 1
    np.savez_compressed(folder / "dataset.npz", **arrays)
    with pytest.raises(
        ValueError, match="resume dataset/schema/configuration mismatch"
    ):
        train_navigation(folder, out, config, resume=True)


def test_interrupted_resume_restores_optimizer_scheduler_and_rng(tmp_path, monkeypatch):
    torch = pytest.importorskip("torch")
    folder = dataset(tmp_path / "dataset")
    config = TrainingConfig(
        hidden=4,
        context=2,
        gate=3,
        epochs1=2,
        epochs2=2,
        epochs3=1,
        batch_size=4,
        threads=1,
    )
    uninterrupted = tmp_path / "uninterrupted"
    resumed = tmp_path / "resumed"
    train_navigation(folder, uninterrupted, config)
    real_write = som_training._json_write

    def interrupt_after_checkpoint(path, value):
        if path.name == "history.json":
            raise InterruptedError("simulated interruption after checkpoint")
        return real_write(path, value)

    monkeypatch.setattr(som_training, "_json_write", interrupt_after_checkpoint)
    with pytest.raises(InterruptedError, match="simulated interruption"):
        train_navigation(folder, resumed, config)
    checkpoint = torch.load(resumed / "training-checkpoint.pt", weights_only=True)
    assert (checkpoint["stage"], checkpoint["epoch"]) == (0, 1)
    assert checkpoint["training_state"]["optimizer"]["state"]
    assert checkpoint["training_state"]["scheduler"]["last_epoch"] == 2
    assert checkpoint["numpy_rng"]["bit_generator"] == "PCG64"
    monkeypatch.setattr(som_training, "_json_write", real_write)
    train_navigation(folder, resumed, config, resume=True)
    expected, actual = load_navigation(uninterrupted), load_navigation(resumed)
    for name in expected.weights:
        np.testing.assert_array_equal(actual.weights[name], expected.weights[name])
    np.testing.assert_array_equal(
        predict_navigation(actual, load_training_data(folder).X),
        predict_navigation(expected, load_training_data(folder).X),
    )


class _UnsupportedCheckpointValue:
    """A saved custom object that the restricted checkpoint loader must refuse."""


@pytest.mark.parametrize("payload", [None, {}, []], ids=["null", "missing", "list"])
def test_resume_refuses_malformed_checkpoint_before_using_state(tmp_path, payload):
    torch = pytest.importorskip("torch")
    folder = dataset(tmp_path / "dataset")
    out = tmp_path / "model"
    out.mkdir()
    torch.save(payload, out / "training-checkpoint.pt")
    with pytest.raises(ValueError, match="checkpoint state is malformed"):
        train_navigation(folder, out, TrainingConfig(threads=1), resume=True)
    assert not (out / "navigation.json").exists()


def test_resume_refuses_pickle_globals_without_unsafe_fallback(tmp_path):
    torch = pytest.importorskip("torch")
    folder = dataset(tmp_path / "dataset")
    out = tmp_path / "model"
    out.mkdir()
    torch.save(_UnsupportedCheckpointValue(), out / "training-checkpoint.pt")
    with pytest.raises(ValueError, match="checkpoint is unsafe or unreadable"):
        train_navigation(folder, out, TrainingConfig(threads=1), resume=True)
    assert not (out / "navigation.json").exists()


def test_resume_refuses_tampered_source_pin(tmp_path):
    torch = pytest.importorskip("torch")
    folder = dataset(tmp_path / "dataset")
    out = tmp_path / "model"
    config = TrainingConfig(
        hidden=4,
        context=2,
        gate=3,
        epochs1=1,
        epochs2=1,
        epochs3=1,
        threads=1,
    )
    train_navigation(folder, out, config)
    checkpoint_path = out / "training-checkpoint.pt"
    checkpoint = torch.load(checkpoint_path, weights_only=True)
    checkpoint["source_pins"]["trainer"] = "0" * 64
    torch.save(checkpoint, checkpoint_path)
    with pytest.raises(
        ValueError, match="resume dataset/schema/configuration mismatch"
    ):
        train_navigation(folder, out, config, resume=True)
