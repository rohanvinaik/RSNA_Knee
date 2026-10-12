"""Arrange saved flanking sample sites; no complete interstice is constructed here."""

import argparse
import json
from hashlib import sha256
from pathlib import Path
from textwrap import fill

import numpy as np

import knee.pictures.pairings as pictures
from knee.relations.pairings import PairingReading

PALETTE = (
    "#1f77b4",
    "#ff7f0e",
    "#2ca02c",
    "#d62728",
    "#9467bd",
    "#8c564b",
    "#e377c2",
    "#17becf",
    "#bcbd22",
    "#333333",
)
PAIRING_ARRAYS = (
    ("pairing_source_labels", "int32", 1),
    ("pairing_far_labels", "int32", 1),
    ("pairing_trace_codes", "uint8", 1),
    ("pairing_outcome_codes", "uint8", 1),
    ("pairing_positions_rc", "float64", 3),
    ("pairing_contributor_labels", "int32", 3),
    ("pairing_band_limits_mm", "float64", 2),
)


def saved_array(arrays, descriptors, name, dtype, ndim):
    """Validate exactly the writer's shape, dtype and digest representation."""
    if name not in arrays or name not in descriptors:
        raise ValueError(f"missing_saved_array:{name}")
    array = arrays[name]
    descriptor = descriptors[name]
    if array.dtype != np.dtype(dtype) or array.ndim != ndim:
        raise ValueError(f"saved_representation_invalid:{name}")
    if tuple(descriptor["shape"]) != array.shape:
        raise ValueError(f"saved_shape_mismatch:{name}")
    if descriptor["dtype"] != array.dtype.str:
        raise ValueError(f"saved_dtype_mismatch:{name}")
    digest = sha256(
        array.dtype.str.encode() + str(array.shape).encode() + array.tobytes()
    ).hexdigest()
    if descriptor["digest"] != digest:
        raise ValueError(f"saved_digest_mismatch:{name}")
    return array


def saved_panels(run: Path, metadata: dict):
    """Validate saved arrays and pass the unchanged reading to its picture adapter."""
    artifact = run / metadata["artifact"]
    descriptors = metadata["arrays"]
    stage = metadata.get("pairings")
    if stage is None:
        raise ValueError("missing_stage_metadata:pairings")
    if stage["side_order"] != ["near", "far"] or stage["corner_order"] != [
        "00",
        "01",
        "10",
        "11",
    ]:
        raise ValueError("saved_pairing_axis_order_mismatch")
    with np.load(artifact, allow_pickle=False) as arrays:
        loaded = {
            name: saved_array(arrays, descriptors, name, dtype, ndim)
            for name, dtype, ndim in PAIRING_ARRAYS
        }
        labels = (
            saved_array(arrays, descriptors, "b1_labels", "int32", 2)
            if "b1_labels" in arrays.files
            else np.empty((0, 0), dtype=np.int32)
        )
    count = loaded["pairing_source_labels"].size
    expected = (
        (count,),
        (count,),
        (count,),
        (count,),
        (count, 2, 2),
        (count, 2, 4),
        (count, 2),
    )
    for (name, _, _), shape in zip(PAIRING_ARRAYS, expected, strict=True):
        if loaded[name].shape != shape:
            raise ValueError(f"saved_pairing_shape_mismatch:{name}")
    reading = PairingReading(
        stage["code"],
        stage["why"],
        *(loaded[name] for name, _, _ in PAIRING_ARRAYS),
        stage["counts"],
        stage["scope"],
    )
    return artifact, pictures.panels(reading), labels


def draw_frame(axis, reading, labels, metadata):
    """Arrange saved native sites and counts; no derived border or pairing."""
    names = metadata["pairings"]["outcome_names"]
    if labels.size:
        axis.imshow(labels, cmap="tab20", interpolation="nearest")
    handles = []
    for code in np.unique(reading.outcome_codes):
        index = int(code)
        name = names[index]
        color = PALETTE[index]
        selected = reading.outcome_codes == code
        labelled = False
        for side, marker in ((0, "o"), (1, "x")):
            sites = reading.positions_rc[selected, side, :]
            sites = sites[np.isfinite(sites).all(axis=1)]
            if not len(sites):
                continue
            style = (
                {"facecolors": "none", "edgecolors": color}
                if marker == "o"
                else {"c": color}
            )
            artist = axis.scatter(
                sites[:, 1], sites[:, 0], marker=marker, s=18, linewidths=0.8, **style
            )
            if not labelled:
                handles.append((artist, name))
                labelled = True
    if not labels.size:
        axis.set_aspect("equal")
        axis.invert_yaxis()
    if handles:
        axis.legend(
            [h for h, _ in handles],
            [name for _, name in handles],
            loc="upper right",
            fontsize=7,
            title="outcome",
        )
    title = "\n".join(
        [
            fill(metadata["series_uid"], 70),
            fill(f"{reading.code}: {reading.why}", 90),
            fill(reading.scope, 90),
            fill(f"saved counts: {json.dumps(dict(reading.counts))}", 90),
            "o near, x far; flanking sample sites; indexed extents; complete interstices unresolved",
        ]
    )
    axis.set_title(title, fontsize=8, loc="left")
    axis.set_axis_off()


def main():
    import matplotlib.pyplot as plt

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--study-uid", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data_root = Path(__file__).resolve().parents[2] / "data"
    out = args.out.resolve()
    if not out.is_relative_to(data_root.resolve()):
        parser.error("out must be under the project private data directory")
    receipt_path = args.run / "receipt.json"
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes)
    records = [r for r in receipt["records"] if r["study_uid"] == args.study_uid]
    if not records:
        parser.error("no saved records for this study")
    loaded = [saved_panels(args.run, record) for record in records]
    if pictures.__file__ is None:
        raise RuntimeError("picture_module_source_unavailable:pairings")
    out.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(
        len(records),
        1,
        figsize=(10, 7 * len(records)),
        layout="constrained",
        squeeze=False,
    )
    series = []
    for axis, record, saved in zip(axes[:, 0], records, loaded, strict=True):
        artifact, reading, labels = saved
        draw_frame(axis, reading, labels, record)
        names = [name for name, _, _ in PAIRING_ARRAYS]
        if "b1_labels" in record["arrays"]:
            names.append("b1_labels")
        series.append(
            {
                "series_uid": record["series_uid"],
                "artifact": record["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "pairings": record["pairings"],
                "arrays": {name: record["arrays"][name] for name in names},
            }
        )
    fig.savefig(out / "series.png", dpi=160)
    plt.close(fig)
    manifest = {
        "schema": "pairing-frames-v1",
        "receipt_sha256": sha256(receipt_bytes).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": sha256(
            Path(pictures.__file__).read_bytes()
        ).hexdigest(),
        "study_uid": args.study_uid,
        "image": "series.png",
        "series": series,
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n"
    )
    print(
        json.dumps(
            {"series": str(out / "series.png"), "manifest": str(out / "manifest.json")}
        )
    )


if __name__ == "__main__":
    main()
