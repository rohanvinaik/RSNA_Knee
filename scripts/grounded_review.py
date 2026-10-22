"""Show the actual queried tissue beside each independent teaching question.

Development-only display. Official answers are captions, never inputs to
location, profile construction or recall. A rectangle is sampled support,
not a tissue certification. The source inference record remains authoritative.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

from knee.diagnosis.squint_profiles import read_study_squints
from knee.json_store import load_json
from scripts.squint_visual_capacity import window_native_bounds


def draw_study(
    record: dict, root: Path, row: dict, subjects: dict, output: Path
) -> dict:
    uid = record["study_uid"]
    study = read_study_squints(root, uid, io_workers=2)
    series = {s["series_uid"]: s for s in study["series"]}
    fig, axes = plt.subplots(2, 6, figsize=(21, 12))
    shown = []
    for ax, (question, subject) in zip(axes.flat, subjects.items(), strict=True):
        obj = record["objects"].get(subject, {})
        regions = obj.get("regions", [])
        finding = record["questions"][question]["finding"]["outcome"]
        ax.set_title(
            f"{question}: official {row[question]}, answer {finding}\n{subject}",
            fontsize=10,
        )
        ax.axis("off")
        if not regions:
            ax.text(0.1, 0.5, "No region read", transform=ax.transAxes)
            shown.append(
                {"question": question, "subject": subject, "code": "no_region"}
            )
            continue
        # Show the first actual selected region; no source label chooses a view.
        region = regions[0]
        acquisition = series[region["series_uid"]]
        window = region["window"]
        z = window[0]
        image = acquisition["native_series"].volume[z]
        bounds = window_native_bounds(acquisition["stack"].bounds_rc, window)
        r0, r1, c0, c1 = bounds
        ax.imshow(image, cmap="gray")
        ax.add_patch(
            Rectangle(
                (c0, r0),
                c1 - c0,
                r1 - r0,
                fill=False,
                edgecolor="orange",
                linewidth=1.4,
            )
        )
        view = acquisition["view"]
        ax.text(
            0.01,
            0.02,
            f"{view['orientation']} FS={view['fat_suppression']} slice={z}",
            color="white",
            fontsize=8,
            transform=ax.transAxes,
            bbox={"facecolor": "black", "alpha": 0.5, "pad": 2},
        )
        shown.append(
            {
                "question": question,
                "subject": subject,
                "code": "shown",
                "series_uid": region["series_uid"],
                "slice": z,
                "native_bounds": bounds,
            }
        )
    fig.suptitle(
        uid
        + "\nOrange: sampled query window, not an asserted boundary. Each question may hold other views.",
        fontsize=11,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(output / (uid + ".png"), dpi=110)
    plt.close(fig)
    return {"study_uid": uid, "panels": shown}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--spec", type=Path, default=Path("docs/teaching/seed_categories.json")
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("review_output_already_exists")
    receipt = load_json(args.run / "receipt.json")
    with (args.root / "train.csv").open() as stream:
        rows = {r["StudyInstanceUID"]: r for r in csv.DictReader(stream)}
    spec = json.loads(args.spec.read_text())
    subjects = {c["question"]: c["subject"] for c in spec["categories"]}
    args.output.mkdir(parents=True)
    index = []
    for entry in receipt["work"]["studies"]:
        uid = entry["study_uid"]
        if uid not in rows:
            continue
        record = load_json(args.run / entry["evidence_path"])
        index.append(draw_study(record, args.root, rows[uid], subjects, args.output))
        print("Drew " + uid, flush=True)
    (args.output / "index.json").write_text(
        json.dumps(
            {
                "scope": "unreviewed query pictures; not new calls",
                "run": str(args.run),
                "memory_manifest_sha256": receipt["memory_manifest_sha256"],
                "studies": index,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
