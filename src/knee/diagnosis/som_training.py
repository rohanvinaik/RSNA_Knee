"""Optional three-stage trainer over fixed HDC numerical features.

Torch is imported only by training functions. The shipped artifact is executed by
``som_navigation`` using NumPy, with the same dual paths and per-question gate.
"""

from __future__ import annotations

import json
import math
import os
import pickle
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np

from knee.diagnosis.som_navigation import (
    FORMAT,
    N_CONDITIONS,
    architecture_for,
    file_sha256,
    load_navigation,
    predict_navigation,
    predict_navigation_details,
    schema_parts,
    weight_shapes,
)


@dataclass(frozen=True)
class TrainingConfig:
    """Explicit capacity and bounded training controls, never anatomical thresholds."""

    hidden: int = 32
    context: int = 8
    gate: int = 16
    epochs1: int = 20
    epochs2: int = 20
    epochs3: int = 10
    batch_size: int = 16
    lr1: float = 0.001
    lr2: float = 0.001
    weight_decay: float = 0.01
    seed: int = 0
    threads: int = 4
    device: str = "cpu"
    pab_window: int = 20
    pab_patience: int = 5
    pab_thresholds: tuple[float, float, float] = (0.015, 0.01, 0.008)
    max_no_improve: int = 40

    def validate(self) -> None:
        for name in (
            "hidden",
            "context",
            "gate",
            "epochs1",
            "epochs2",
            "epochs3",
            "batch_size",
            "threads",
            "pab_window",
            "pab_patience",
            "max_no_improve",
        ):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ValueError(f"{name} must be a positive integer")
        if self.threads > 4:
            raise ValueError("training is bounded to at most four CPU threads")
        if type(self.seed) is not int or self.seed < 0:
            raise ValueError("seed must be a nonnegative integer")
        for name in ("lr1", "lr2"):
            if not math.isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if not math.isfinite(self.weight_decay) or self.weight_decay < 0:
            raise ValueError("weight_decay must be finite and nonnegative")
        if len(self.pab_thresholds) != 3 or any(
            not math.isfinite(t) or t < 0 for t in self.pab_thresholds
        ):
            raise ValueError("three finite nonnegative PAB thresholds are required")
        if self.device not in {"cpu", "mps"}:
            raise ValueError("device must be cpu or mps")


@dataclass(frozen=True)
class TrainingData:
    schema: Mapping[str, Any]
    X: np.ndarray
    y: np.ndarray
    label_mask: np.ndarray
    study_uids: np.ndarray
    train_mask: np.ndarray
    validation_mask: np.ndarray
    pins: Mapping[str, str]


def load_training_data(folder: str | Path) -> TrainingData:
    """Read pinned arrays, rejecting cross-study leakage and unknown-as-negative conversion."""
    root = Path(folder)
    schema_path, data_path = root / "schema.json", root / "dataset.npz"
    schema = json.loads(schema_path.read_text())
    names, _labels, _groups = schema_parts(schema)
    required = {"X", "y", "label_mask", "study_uids", "train_mask", "validation_mask"}
    with np.load(data_path, allow_pickle=False) as saved:
        if not required <= set(saved.files):
            raise ValueError("training dataset is missing required arrays")
        arrays = {name: np.asarray(saved[name]).copy() for name in required}
    X, y = arrays["X"], arrays["y"]
    if X.dtype != np.float32 or X.ndim != 2 or X.shape[1] != len(names) or not len(X):
        raise ValueError("X must be nonempty float32 [N,D] in the schema feature order")
    if (
        not np.isfinite(X).all()
        or y.dtype != np.float32
        or y.shape != (len(X), N_CONDITIONS)
    ):
        raise ValueError("invalid training features or target shape/dtype")
    for name in ("label_mask", "train_mask", "validation_mask"):
        expected = y.shape if name == "label_mask" else (len(X),)
        if arrays[name].dtype != np.bool_ or arrays[name].shape != expected:
            raise ValueError(f"{name} must be bool with shape {expected}")
    known = arrays["label_mask"]
    if not np.isfinite(y[known]).all() or not np.isin(y[known], (0, 1)).all():
        raise ValueError(
            "observed diagnoses must be independently supplied binary targets"
        )
    # Unknown target storage is not a negative and must not poison BCE through NaN * zero.
    y = np.where(known, y, np.float32(0)).astype(np.float32)
    train, validation = arrays["train_mask"], arrays["validation_mask"]
    uids = arrays["study_uids"]
    if uids.dtype.kind != "U" or uids.shape != (len(X),) or any(not u for u in uids):
        raise ValueError("study_uids must be nonempty Unicode identities")
    if np.any(train & validation) or not train.any() or not validation.any():
        raise ValueError("nonempty disjoint training and validation masks are required")
    if set(uids[train]) & set(uids[validation]):
        raise ValueError("a study may not cross training and validation")
    if not known[train].any() or not known[validation].any():
        raise ValueError("both splits require independently known diagnosis targets")
    expected_splits = (
        ("train_uids", set(uids[train])),
        ("validation_uids", set(uids[validation])),
    )
    for name, actual in expected_splits:
        if name in schema and set(schema[name]) != actual:
            raise ValueError(f"schema {name} disagrees with the array split")
    pins = {
        "dataset_sha256": file_sha256(data_path),
        "schema_sha256": file_sha256(schema_path),
    }
    return TrainingData(schema, X, y, known, uids, train, validation, pins)


def build_torch_navigation(architecture: Mapping[str, Any]) -> Any:
    """Build the optional training twin; its exact parameters have a NumPy implementation."""
    import torch
    from torch import nn

    d, h, c, g = (
        architecture[k] for k in ("feature_count", "hidden", "context", "gate")
    )
    groups = architecture["groups"]

    class Specialist(nn.Module):
        def __init__(self, indices: list[int]) -> None:
            super().__init__()
            self.indices = tuple(indices)
            self.domain1 = nn.Linear(len(indices), h)
            self.domain2 = nn.Linear(h, h)
            self.context = nn.Linear(d, c)
            self.opinion = nn.Linear(h + c, N_CONDITIONS)

        def forward(self, values: Any) -> Any:
            own = nn.functional.gelu(
                self.domain1(values[:, self.indices]), approximate="tanh"
            )
            own = nn.functional.gelu(self.domain2(own), approximate="tanh")
            context = nn.functional.gelu(self.context(values), approximate="tanh")
            return self.opinion(torch.cat((own, context), dim=1))

    class Navigation(nn.Module):
        applicable: Any  # Registered bool tensor; PyTorch's dynamic Module lookup also admits modules.

        def __init__(self) -> None:
            super().__init__()
            self.specialists = nn.ModuleList(
                Specialist(row["feature_indices"]) for row in groups
            )
            self.gate_context = nn.Linear(d, g)
            self.gate_head = nn.Linear(
                g + len(groups) * N_CONDITIONS, len(groups) * N_CONDITIONS
            )
            applicable = torch.zeros((len(groups), N_CONDITIONS), dtype=torch.bool)
            for i, row in enumerate(groups):
                applicable[i, row["condition_indices"]] = True
            self.register_buffer("applicable", applicable, persistent=False)

        def opinions(self, values: Any) -> Any:
            return torch.stack([member(values) for member in self.specialists], dim=1)

        def combine_details(self, values: Any, opinions: Any) -> tuple[Any, Any]:
            context = nn.functional.gelu(self.gate_context(values), approximate="tanh")
            gate_opinions = opinions.masked_fill(~self.applicable, 0)
            inputs = torch.cat((context, gate_opinions.flatten(start_dim=1)), dim=1)
            logits = self.gate_head(inputs).reshape(-1, len(groups), N_CONDITIONS)
            trust = torch.softmax(logits.masked_fill(~self.applicable, -1e9), dim=1)
            return (opinions * trust).sum(dim=1), trust.transpose(1, 2)

        def combine(self, values: Any, opinions: Any) -> Any:
            return self.combine_details(values, opinions)[0]

        def details(self, values: Any) -> tuple[Any, Any]:
            return self.combine_details(values, self.opinions(values))

        def forward(self, values: Any) -> Any:
            return self.combine(values, self.opinions(values))

    return Navigation()


def masked_binary_loss(logits: Any, targets: Any, mask: Any) -> Any:
    """BCE over actually known targets; an unknown digit contributes no gradient."""
    import torch

    safe_targets = torch.where(mask, targets, torch.zeros_like(targets))
    losses = torch.nn.functional.binary_cross_entropy_with_logits(
        logits, safe_targets, reduction="none"
    )
    return (losses * mask).sum() / mask.sum().clamp_min(1)


def _json_write(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    os.replace(temporary, path)


def export_navigation(
    model: Any,
    schema: Mapping[str, Any],
    architecture: Mapping[str, Any],
    mean: np.ndarray,
    scale: np.ndarray,
    output: Path,
    provenance: Mapping[str, Any],
) -> dict[str, Any]:
    """Export only finite NumPy weights, schema and explicit training provenance."""
    output.mkdir(parents=True, exist_ok=True)
    shapes = weight_shapes(architecture)
    weights = {
        k: v.detach().cpu().numpy().astype(np.float32)
        for k, v in model.state_dict().items()
    }
    if set(weights) != set(shapes) or any(
        weights[k].shape != v for k, v in shapes.items()
    ):
        raise ValueError("Torch model parameters disagree with the NumPy architecture")
    arrays: dict[str, Any] = {
        **weights,
        "input_mean": mean.astype(np.float32),
        "input_scale": scale.astype(np.float32),
    }
    if any(not np.isfinite(v).all() for v in arrays.values()):
        raise ValueError("cannot export nonfinite weights or conditioning")
    _json_write(output / "schema.json", schema)
    np.savez_compressed(output / "weights.npz", **arrays)
    manifest = {
        "format": FORMAT,
        "architecture": dict(architecture),
        "schema_sha256": file_sha256(output / "schema.json"),
        "weights_sha256": file_sha256(output / "weights.npz"),
        "parameter_count": sum(a.size for a in weights.values()),
        "conditioning": "training_split_mean_std_constant_scale_one",
        "provenance": dict(provenance),
    }
    _json_write(output / "navigation.json", manifest)
    load_navigation(output)
    return manifest


def _condition_report(
    logits: np.ndarray, y: np.ndarray, mask: np.ndarray, labels: list[str]
) -> dict:
    """Keep per-question losses and target availability separate; no society-wide score."""
    rows = {}
    for i, name in enumerate(labels):
        valid = mask[:, i]
        count = int(valid.sum())
        loss = np.logaddexp(0, logits[valid, i]) - y[valid, i] * logits[valid, i]
        rows[name] = {
            "known": count,
            "positive": int(y[valid, i].sum()),
            "negative": int(count - y[valid, i].sum()),
            "binary_cross_entropy": float(loss.mean()) if count else None,
        }
    return rows


def _load_training_checkpoint(path: Path, device: Any) -> dict[str, Any]:
    """Read only tensors and primitive checkpoint state; never execute pickle globals."""
    import torch

    try:
        checkpoint = torch.load(path, map_location=device, weights_only=True)
    except (OSError, EOFError, RuntimeError, pickle.UnpicklingError) as error:
        raise ValueError("resume checkpoint is unsafe or unreadable") from error
    required = {
        "pins",
        "config",
        "model",
        "source_pins",
        "stage",
        "epoch",
        "history",
        "numpy_rng",
        "stage_reports",
        "training_state",
    }
    if (
        not isinstance(checkpoint, dict)
        or not required <= checkpoint.keys()
        or any(
            not isinstance(checkpoint[name], dict)
            for name in ("pins", "config", "model", "source_pins", "numpy_rng")
        )
        or any(
            not isinstance(checkpoint[name], list)
            for name in ("history", "stage_reports")
        )
        or type(checkpoint["stage"]) is not int
        or not 0 <= checkpoint["stage"] <= 3
        or type(checkpoint["epoch"]) is not int
        or checkpoint["epoch"] < 0
        or (
            checkpoint["training_state"] is not None
            and not isinstance(checkpoint["training_state"], dict)
        )
    ):
        raise ValueError("resume checkpoint state is malformed")
    return checkpoint


def train_navigation(
    dataset: str | Path,
    output: str | Path,
    config: TrainingConfig | None = None,
    *,
    resume: bool = False,
) -> dict[str, Any]:
    """Run specialist, frozen gate and lower-rate joint stages, checkpointing each epoch."""
    import torch

    config = config or TrainingConfig()
    config.validate()
    data = load_training_data(dataset)
    architecture = architecture_for(
        data.schema, config.hidden, config.context, config.gate
    )
    output = Path(output)
    if output.exists() and not resume:
        raise ValueError(
            "training output already exists; use explicit resume or a new directory"
        )
    output.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output / "training-checkpoint.pt"
    source_pins = {
        "trainer": file_sha256(Path(__file__)),
        "runtime": file_sha256(Path(__file__).with_name("som_navigation.py")),
    }
    torch.set_num_threads(config.threads)
    if config.device == "mps" and not torch.backends.mps.is_available():
        raise ValueError("MPS was requested but is unavailable")
    device = torch.device(config.device)
    torch.manual_seed(config.seed)
    model = build_torch_navigation(architecture).to(device)
    mean = data.X[data.train_mask].astype(np.float64).mean(axis=0).astype(np.float32)
    scale = data.X[data.train_mask].astype(np.float64).std(axis=0).astype(np.float32)
    scale[scale == 0] = 1
    conditioned = (data.X - mean) / scale
    if not np.isfinite(conditioned).all():
        raise ValueError("training-only input conditioning is nonfinite")
    X = torch.as_tensor(conditioned, device=device)
    y = torch.as_tensor(data.y, device=device)
    mask = torch.as_tensor(data.label_mask, device=device)
    train_indices = np.flatnonzero(data.train_mask)
    val_indices = np.flatnonzero(data.validation_mask)
    rng = np.random.default_rng(config.seed)
    config_row = json.loads(json.dumps(asdict(config)))
    start_stage, start_epoch, history, resumed_state = 0, 0, [], None
    if resume:
        if not checkpoint_path.exists():
            raise ValueError("resume requires an existing training checkpoint")
        resumed_state = _load_training_checkpoint(checkpoint_path, device)
        if (
            resumed_state["pins"] != dict(data.pins)
            or resumed_state["config"] != config_row
            or resumed_state.get("source_pins") != source_pins
        ):
            raise ValueError("resume dataset/schema/configuration mismatch")
        model.load_state_dict(resumed_state["model"])
        start_stage, start_epoch = resumed_state["stage"], resumed_state["epoch"]
        history = resumed_state["history"]
        rng.bit_generator.state = resumed_state["numpy_rng"]
    epochs = (config.epochs1, config.epochs2, config.epochs3)
    rates = (config.lr1, config.lr2, config.lr1 / 10)
    labels = architecture["labels"]
    stage_reports = (
        list(resumed_state.get("stage_reports", [])) if resumed_state else []
    )

    def save_checkpoint(stage: int, epoch: int, state: dict[str, Any] | None) -> None:
        payload = {
            "pins": dict(data.pins),
            "config": config_row,
            "model": model.state_dict(),
            "source_pins": source_pins,
            "stage": stage,
            "epoch": epoch,
            "history": history,
            "numpy_rng": rng.bit_generator.state,
            "stage_reports": stage_reports,
            "training_state": state,
        }
        temporary = checkpoint_path.with_suffix(".tmp")
        torch.save(payload, temporary)
        os.replace(temporary, checkpoint_path)
        _json_write(output / "history.json", history)

    for stage in range(start_stage, 3):
        before_stage = {
            k: t.detach().cpu().clone() for k, t in model.state_dict().items()
        }
        for parameter in model.parameters():
            parameter.requires_grad_(stage != 0)
        for parameter in model.specialists.parameters():
            parameter.requires_grad_(stage != 1)
        parameters = [p for p in model.parameters() if p.requires_grad]
        optimizer = torch.optim.AdamW(
            parameters, lr=rates[stage], weight_decay=config.weight_decay
        )
        batches = math.ceil(len(train_indices) / config.batch_size)
        scheduler = torch.optim.lr_scheduler.OneCycleLR(
            optimizer,
            max_lr=rates[stage],
            total_steps=max(2, epochs[stage] * batches),
            pct_start=0.3,
        )
        state: dict[str, Any] = {
            "losses": [],
            "stable_count": 0,
            "no_improve": 0,
            "best_loss": math.inf,
            "best_model": None,
            "updates": 0,
        }
        first_epoch = start_epoch if stage == start_stage else 0
        if (
            resumed_state
            and stage == start_stage
            and resumed_state["training_state"] is not None
        ):
            state = resumed_state["training_state"]
            optimizer.load_state_dict(state["optimizer"])
            scheduler.load_state_dict(state["scheduler"])
        # Frozen specialist opinions are computed once for stage 2, not every training batch.
        with torch.no_grad():
            cached_opinions: Any = model.opinions(X).detach() if stage == 1 else None
        stop = "epoch_cap"
        for epoch in range(first_epoch, epochs[stage]):
            model.train()
            order = rng.permutation(train_indices)
            for begin in range(0, len(order), config.batch_size):
                selected = torch.as_tensor(
                    order[begin : begin + config.batch_size], device=device
                )
                if not bool(mask[selected].any()):
                    continue
                optimizer.zero_grad()
                if stage == 0:
                    opinions = model.opinions(X[selected])
                    applicable = mask[selected, None, :] & model.applicable[None]
                    targets = y[selected, None, :].expand_as(opinions)
                    loss = masked_binary_loss(opinions, targets, applicable)
                else:
                    logits = (
                        model.combine(X[selected], cached_opinions[selected])
                        if stage == 1
                        else model(X[selected])
                    )
                    loss = masked_binary_loss(logits, y[selected], mask[selected])
                if not torch.isfinite(loss):
                    raise ValueError(
                        "nonfinite training loss; refusing a model artifact"
                    )
                loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    parameters, max_norm=1.0, error_if_nonfinite=True
                )
                optimizer.step()
                scheduler.step()
                state["updates"] += 1
            model.eval()
            with torch.no_grad():
                v = torch.as_tensor(val_indices, device=device)
                if stage == 0:
                    opinions = model.opinions(X[v])
                    applicable = mask[v, None, :] & model.applicable[None]
                    validation_loss = masked_binary_loss(
                        opinions, y[v, None, :].expand_as(opinions), applicable
                    )
                    counts = model.applicable.sum(dim=0).clamp_min(1)
                    validation_logits = (opinions * model.applicable[None]).sum(
                        dim=1
                    ) / counts
                else:
                    validation_logits = (
                        model.combine(X[v], cached_opinions[v])
                        if stage == 1
                        else model(X[v])
                    )
                    validation_loss = masked_binary_loss(
                        validation_logits, y[v], mask[v]
                    )
                value = float(validation_loss.cpu())
            if not math.isfinite(value):
                raise ValueError("nonfinite validation loss")
            state["losses"].append(value)
            if value < state["best_loss"]:
                state["best_loss"] = value
                state["no_improve"] = 0
                state["best_model"] = {
                    k: t.detach().cpu().clone() for k, t in model.state_dict().items()
                }
            else:
                state["no_improve"] += 1
            losses = state["losses"]
            stability = None
            if len(losses) > config.pab_window:
                recent = losses[-config.pab_window - 1 :]
                changes = [abs(b - a) / (abs(a) + 1e-8) for a, b in pairwise(recent)]
                stability = sum(changes) / len(changes)
                state["stable_count"] = (
                    state["stable_count"] + 1
                    if stability < config.pab_thresholds[stage]
                    else 0
                )
            row = {
                "stage": stage + 1,
                "epoch": epoch + 1,
                "updates": state["updates"],
                "learning_rate": float(optimizer.param_groups[0]["lr"]),
                "optimizer_validation_loss": value,
                "pab_relative_change": stability,
                "per_condition": _condition_report(
                    validation_logits.cpu().numpy(),
                    data.y[val_indices],
                    data.label_mask[val_indices],
                    labels,
                ),
            }
            history.append(row)
            state["optimizer"], state["scheduler"] = (
                optimizer.state_dict(),
                scheduler.state_dict(),
            )
            save_checkpoint(stage, epoch + 1, state)
            print(
                json.dumps({k: v for k, v in row.items() if k != "per_condition"}),
                flush=True,
            )
            if state["no_improve"] >= config.max_no_improve:
                stop = "stalled"
                break
            if state["stable_count"] >= config.pab_patience:
                stop = "stable"
                break
        if state["best_model"] is not None:
            model.load_state_dict(state["best_model"])
        changed = {
            k: not torch.equal(t.detach().cpu(), before_stage[k])
            for k, t in model.state_dict().items()
        }
        stage_reports.append(
            {
                "stage": stage + 1,
                "stop": stop,
                "completed_epochs": len(state["losses"]),
                "updates": state["updates"],
                "best_optimizer_validation_loss": state["best_loss"],
                "specialists_frozen": stage == 1,
                "maximum_learning_rate": rates[stage],
                "specialist_parameters_changed": any(
                    v for k, v in changed.items() if k.startswith("specialists.")
                ),
                "gate_parameters_changed": any(
                    v for k, v in changed.items() if not k.startswith("specialists.")
                ),
            }
        )
        save_checkpoint(stage + 1, 0, None)
        resumed_state = None
    model.eval()
    provenance = {
        **data.pins,
        "config": config_row,
        "stages": stage_reports,
        "train_studies": sorted(set(data.study_uids[data.train_mask])),
        "validation_studies": sorted(set(data.study_uids[data.validation_mask])),
        "source_pins": data.schema.get("source_pins", {}),
        "trainer_source_sha256": file_sha256(Path(__file__)),
        "runtime_source_sha256": file_sha256(
            Path(__file__).with_name("som_navigation.py")
        ),
    }
    manifest = export_navigation(
        model, data.schema, architecture, mean, scale, output, provenance
    )
    probe = data.X[: min(16, len(data.X))]
    with torch.no_grad():
        probe_logits, probe_trust = model.details(
            torch.as_tensor((probe - mean) / scale, device=device)
        )
        expected = torch.sigmoid(probe_logits).cpu().numpy()
        expected_trust = probe_trust.cpu().numpy()
    numpy_model = load_navigation(output)
    actual = predict_navigation(numpy_model, probe)
    actual_trust = predict_navigation_details(numpy_model, probe)["trust_weights"]
    error = float(np.max(np.abs(expected - actual)))
    if not np.allclose(expected, actual, rtol=2e-5, atol=2e-6):
        raise ValueError("NumPy/Torch export parity failed")
    if not np.allclose(expected_trust, actual_trust, rtol=2e-5, atol=2e-6):
        raise ValueError("NumPy/Torch routing weight parity failed")
    receipt = {
        "format": FORMAT,
        **data.pins,
        "parameter_count": manifest["parameter_count"],
        "numpy_torch_max_abs_error": error,
        "stages": stage_reports,
        "numpy_torch_trust_max_abs_error": float(
            np.max(np.abs(expected_trust - actual_trust))
        ),
        "train_rows": int(data.train_mask.sum()),
        "validation_rows": int(data.validation_mask.sum()),
        "known_training_targets": int(data.label_mask[data.train_mask].sum()),
        "known_validation_targets": int(data.label_mask[data.validation_mask].sum()),
        "artifact_sha256": file_sha256(output / "navigation.json"),
        "fixed_hdc_encoder": True,
        "localized_lesion_supervision": False,
    }
    _json_write(output / "training-receipt.json", receipt)
    return receipt
