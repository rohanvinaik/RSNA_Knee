"""Draw private ownership and relation frames from saved production readings.

The ownership frame displays EVERY seated member's two saved masks and saved counts -- one
member per parse the stages below produced (task 6.2) -- and, where the solitary and
concurrent members were compared, the saved disagreement mask between their claims, drawn
AS a disagreement because that is the informative case. The relations frame displays
pipeline construction status, not study-derived relation evidence. This workbench arranges
values through the picture modules; it does not derive a mask, measure a place, count an
object, resolve a disagreement or construct an interstice.
"""

import argparse
import json
from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path
from textwrap import fill

import matplotlib.pyplot as plt
import numpy as np

from knee.ownership.claims import OwnershipReading
from knee.pictures import ownership, relations
from knee.relations.shell import RelationsReading


def saved_mask(
    arrays: Mapping[str, np.ndarray], descriptors: dict, name: str
) -> np.ndarray:
    """Validate a saved mask's representation and recorded content digest."""
    if name not in arrays or name not in descriptors:
        raise ValueError(f"missing_saved_mask:{name}")
    mask = arrays[name]
    descriptor = descriptors[name]
    if mask.dtype.str != descriptor["dtype"]:
        raise ValueError(f"saved_array_dtype_mismatch:{name}")
    if mask.shape != tuple(descriptor["shape"]):
        raise ValueError(f"saved_array_shape_mismatch:{name}")
    digest = sha256(
        mask.dtype.str.encode() + str(mask.shape).encode() + mask.tobytes()
    ).hexdigest()
    if digest != descriptor["digest"]:
        raise ValueError(f"saved_array_digest_mismatch:{name}")
    if mask.dtype.kind != "b" or mask.ndim != 2:
        raise ValueError(f"saved_mask_representation_invalid:{name}")
    return mask


def saved_panels(run: Path, metadata: dict) -> tuple:
    """Reconstitute existing readings from one saved record, without measuring.

    Returns the artifact path, one `(parse, OwnershipPanels)` per saved member, the saved
    disagreement mask, and the relations panels.
    """
    if "ownership" not in metadata or "relations" not in metadata:
        raise ValueError("missing_saved_stage_reading")
    if "artifact" not in metadata or "arrays" not in metadata:
        raise ValueError("missing_saved_artifact")
    saved_ownership = metadata["ownership"]
    if not saved_ownership.get("members"):
        raise ValueError("missing_saved_members")
    artifact = run / metadata["artifact"]
    members = []
    with np.load(artifact, allow_pickle=False) as arrays:
        for member in saved_ownership["members"]:
            claims = saved_mask(arrays, metadata["arrays"], member["claims_array"])
            residual = saved_mask(arrays, metadata["arrays"], member["residual_array"])
            if claims.shape != residual.shape:
                raise ValueError("ownership_mask_shape_mismatch")
            reading = OwnershipReading(
                code=member["code"],
                why=member["why"],
                claims=claims,
                residual=residual,
                claimed_places=member["claimed_places"],
                residual_places=member["residual_places"],
                unavailable_places=member["unavailable_places"],
                objects=member["objects"],
            )
            members.append((member["parse"], ownership.panels(reading)))
        disagreement = saved_mask(
            arrays, metadata["arrays"], saved_ownership["disagreement_array"]
        )
    saved_relations = metadata["relations"]
    relations_reading = RelationsReading(
        code=saved_relations["code"],
        why=saved_relations["why"],
        interstices=tuple(saved_relations["interstices"]),
    )
    return artifact, tuple(members), disagreement, relations.panels(relations_reading)


def draw_mask(axis: object, mask: np.ndarray, title: str, code: str, why: str) -> None:
    """Display a saved mask, or its existing named absence when it is empty."""
    axis.set_title(title, fontsize=8)
    if mask.size:
        axis.imshow(mask, cmap="gray", vmin=0, vmax=1)
    else:
        axis.text(
            0.03,
            0.95,
            f"{code}\n\n{fill(why, width=40)}",
            transform=axis.transAxes,
            va="top",
            wrap=True,
        )
    axis.set_axis_off()


def draw(run: Path, study_uid: str, out: Path) -> dict:
    """Draw this stage from the saved run and return its manifest.

    The one entry a caller uses, so the single command can draw every stage without a subprocess
    and without knowing each renderer's argument spelling. `main()` is a thin wrapper over it, so
    the hand-typed command and the joined run draw the same thing from the same code.
    """
    data_root = Path(__file__).resolve().parents[2] / "data"
    output = out.resolve()
    if not output.is_relative_to(data_root.resolve()):
        raise ValueError("out must be under the project's private data directory")
    receipt_path = run / "receipt.json"
    receipt = json.loads(receipt_path.read_text())
    records = [
        record for record in receipt["records"] if record["study_uid"] == study_uid
    ]
    if not records:
        raise ValueError("no saved records for this study")
    loaded = [saved_panels(run, record) for record in records]
    output.mkdir(parents=True, exist_ok=True)
    # Two columns per seated member, one for the disagreement, one for relations.
    columns = 2 * max(len(members) for _, members, _, _ in loaded) + 2
    gallery, axes = plt.subplots(
        len(records),
        columns,
        figsize=(5 * columns, 4 * len(records)),
        layout="constrained",
        squeeze=False,
    )
    series = []
    for row, (metadata, saved) in enumerate(zip(records, loaded, strict=True)):
        artifact, members, disagreement, relations_frame = saved
        series_uid = metadata["series_uid"]
        label = fill(series_uid, width=42)
        column = 0
        for parse, frame in members:
            draw_mask(
                axes[row, column],
                frame.claims,
                f"{label}\n{parse}: {frame.code}: {frame.why}\n"
                f"claims: {frame.claimed_places} places; {frame.objects} objects",
                frame.code,
                frame.why,
            )
            draw_mask(
                axes[row, column + 1],
                frame.residual,
                f"{label}\n{parse} residual: {frame.residual_places} places; "
                f"unavailable: {frame.unavailable_places} places",
                frame.code,
                frame.why,
            )
            column += 2
        for spare in range(column, columns - 2):
            axes[row, spare].set_axis_off()
        saved_ownership = metadata["ownership"]
        draw_mask(
            axes[row, columns - 2],
            disagreement,
            f"{label}\nsolitary vs concurrent claims: {saved_ownership['comparison']}; "
            f"disagreeing: {saved_ownership['disagreeing_places']} places\n"
            "nothing here resolves a disagreement",
            saved_ownership["comparison"],
            "the two members were not compared",
        )
        axes[row, columns - 1].set_title(
            f"{label}\nrelations: pipeline construction status", fontsize=8
        )
        axes[row, columns - 1].text(
            0.03,
            0.95,
            f"{relations_frame.code}\n\n{fill(relations_frame.why, width=46)}\n\n"
            f"pairings: {metadata['relations'].get('pairings_code')}",
            transform=axes[row, columns - 1].transAxes,
            va="top",
            wrap=True,
        )
        axes[row, columns - 1].set_axis_off()
        series.append(
            {
                "series_uid": series_uid,
                "artifact": metadata["artifact"],
                "artifact_sha256": sha256(artifact.read_bytes()).hexdigest(),
                "masks": {
                    name: metadata["arrays"][name]
                    for member in saved_ownership["members"]
                    for name in (member["claims_array"], member["residual_array"])
                }
                | {
                    saved_ownership["disagreement_array"]: metadata["arrays"][
                        saved_ownership["disagreement_array"]
                    ]
                },
                "ownership": saved_ownership,
                "relations": metadata["relations"],
                "frame_kinds": {"ownership": "study", "relations": "pipeline"},
            }
        )
    gallery.suptitle(
        "Saved ownership members, one partition per parse, their disagreement, "
        "and relation construction status"
    )
    gallery.savefig(output / "series.png", dpi=160)
    plt.close(gallery)
    picture_modules = {}
    for name, module in (("ownership", ownership), ("relations", relations)):
        if module.__file__ is None:
            raise RuntimeError(f"picture_module_source_unavailable:{name}")
        picture_modules[name] = sha256(Path(module.__file__).read_bytes()).hexdigest()
    manifest = {
        "schema": "partition-frames-v2",
        "receipt_sha256": sha256(receipt_path.read_bytes()).hexdigest(),
        "renderer_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "picture_module_sha256": picture_modules,
        "study_uid": study_uid,
        "image": "series.png",
        "series": series,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n"
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--study-uid", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        draw(args.run, args.study_uid, args.out)
    except ValueError as refusal:
        parser.error(str(refusal))
    output = args.out.resolve()
    print(
        json.dumps(
            {
                "series": str(output / "series.png"),
                "manifest": str(output / "manifest.json"),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
