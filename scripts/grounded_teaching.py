"""Build the hand-defined teaching references, using the production writer/recall.

Polygons are annotations of named teaching images, never proposed search rules.
This creates a reference workset, not a child of the current signed memory.
Labels and the written interpretations are attached AFTER image measurements.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

from knee.diagnosis.squint_leg import leg_maps
from knee.diagnosis.squint_locator import prepare_recall, recall_object
from knee.diagnosis.squint_memory import (
    _json_value,
    _territory_address,
    carry_condition_calls,
)
from knee.diagnosis.squint_profiles import (
    cosine_evidence,
    merge_profiles,
    profile_territory,
    read_study_squints,
    refine_territory,
)
from knee.diagnosis.squint_support import teacher_territory
from knee.encoding.carrier import ROW_WIDTH, HadamardCarrier
from knee.study.tables import LABELS


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_categories(
    spec: object, rows: dict, *, require_all_questions: bool = True
) -> None:
    """Require exact, independently labeled opposing examples for every question."""
    if not isinstance(spec, dict) or spec.get("schema") != "knee.grounded-teaching/v1":
        raise ValueError("teaching_schema_invalid")
    categories = spec.get("categories", [])
    questions = [c["question"] for c in categories]
    if require_all_questions and (len(questions) != 12 or len(set(questions)) != 12):
        raise ValueError("twelve_unique_questions_required")
    if not require_all_questions:
        if (
            not questions
            or len(set(questions)) != len(questions)
            or not set(questions) <= set(LABELS)
        ):
            raise ValueError("unique_known_questions_required")
        namespace = spec.get("case_namespace")
        if not isinstance(namespace, str) or not namespace.strip():
            raise ValueError("incremental_case_namespace_required")
    for category in categories:
        for key in ("identity", "normal_reference", "altered_reference"):
            if not category.get(key):
                raise ValueError("teaching_meaning_required")
        for side, sign in (("normal", "0"), ("diagnosed", "1")):
            sample = category[side]
            uid = sample["study_uid"]
            if uid not in rows or rows[uid].get(category["question"]) != sign:
                raise ValueError("independent_condition_call_mismatch")
            polygon = np.asarray(sample["polygon_xy"], dtype=float)
            if polygon.ndim != 2 or polygon.shape[1] != 2 or len(polygon) < 3:
                raise ValueError("teaching_polygon_invalid")
            if not np.isfinite(polygon).all() or not sample.get("visual_reading"):
                raise ValueError("visual_observation_required")


def reference_memory(cases: list, revision: str) -> dict:
    """Prepare the ordinary reader over this explicit teaching workset only."""
    questions = sorted({q for case in cases for q in case["condition_calls"]})
    memory = {
        "schema": "knee.squint-memory/v1",
        "revision": revision,
        "questions": questions,
        "cases": cases,
    }
    prepared = prepare_recall(memory)
    if prepared.get("outcome") != "prepared":
        raise ValueError(f"teaching_preparation_failed:{prepared.get('reason')}")
    memory["prepared_recall"] = prepared
    return memory


def replay_workset(path: Path) -> dict:
    """Replay already measured teaching cases without decoding images again."""
    workset = json.loads(path.read_text())
    if workset.get("schema") != "knee.grounded-reference-workset/v1":
        raise ValueError("teaching_workset_schema_invalid")
    memory = reference_memory(workset["cases"], workset["spec_sha256"])
    results = []
    for case in workset["cases"]:
        for question, call in case["condition_calls"].items():
            finding = recall_object(case["profile"], memory, question)
            expected = "present" if call == 1 else "absent"
            results.append(
                {
                    "case_id": case["case_id"],
                    "question": question,
                    "expected": expected,
                    "actual": finding["outcome"],
                }
            )
    return {
        "scope": "teaching_replay_not_held_out",
        "cases": results,
        "identified": sum(r["actual"] == r["expected"] for r in results),
        "abstained": sum(r["actual"] not in {"present", "absent"} for r in results),
        "wrong": sum(
            r["actual"] in {"present", "absent"} and r["actual"] != r["expected"]
            for r in results
        ),
    }


def measure_sample(study: dict, legs: dict, sample: dict, subject: str) -> dict:
    """Read only the addressed image support; no diagnostic call is an input."""
    from matplotlib.path import Path as PolygonPath

    series = next(s for s in study["series"] if s["series_uid"] == sample["series_uid"])
    z = sample["slice"]
    image = series["native_series"].volume[z]
    polygon = np.asarray(sample["polygon_xy"], dtype=float)
    if (
        (polygon < 0).any()
        or (polygon[:, 0] >= image.shape[1]).any()
        or (polygon[:, 1] >= image.shape[0]).any()
    ):
        raise ValueError("teaching_polygon_outside_frame")
    yy, xx = np.indices(image.shape)
    mask = (
        PolygonPath(polygon)
        .contains_points(np.column_stack((xx.ravel(), yy.ravel())))
        .reshape(image.shape)
    )
    rr, cc = np.nonzero(mask)
    if not len(rr):
        raise ValueError("teaching_support_empty")
    bounds = [int(rr.min()), int(rr.max()) + 1, int(cc.min()), int(cc.max()) + 1]
    territory = teacher_territory(
        study["study_uid"],
        series,
        subject,
        {
            "code": "resolved",
            "mask": mask,
            "bbox": bounds,
            "source_address": {
                "target_series_uid": series["series_uid"],
                "observation_slices": [z],
                "kind": "visual_teaching",
            },
        },
        z,
        legs[series["series_uid"]],
    )
    if territory.get("code") != "resolved":
        raise ValueError(f"teaching_support_refused:{territory.get('code')}")
    leg = legs[series["series_uid"]]
    coarse = profile_territory(series, territory, leg, subject=subject)
    fine = refine_territory(series, territory, leg, subject=subject)
    profile = merge_profiles([coarse, fine], subject=subject)
    native_path = Path(series["source"]["native_slice_paths"][z])
    return {
        "profile": _json_value(profile),
        "image": image,
        "mask": mask,
        "bounds": bounds,
        "view": series["view"],
        "native_path": str(native_path),
        "native_sha256": digest(native_path),
        "territory": _json_value(_territory_address(territory)),
    }


def compare_references(normal: dict, diagnosed: dict) -> dict:
    """Name proportional/silent readings honestly; retain every bank difference."""
    terms = cosine_evidence(normal, diagnosed)
    differences = []
    for name in terms["common_banks"]:
        a, b = normal["banks"][name], diagnosed["banks"][name]
        # Compare proportions exactly; a mere size multiplier is not a direction.
        if any(x * sum(b) != y * sum(a) for x, y in zip(a, b, strict=True)):
            differences.append({"bank": name, "normal": a, "diagnosed": b})
    return {
        "outcome": "distinct_measured_profiles"
        if differences
        else "silent"
        if terms["code"] == "silent"
        else "parallel_profiles",
        "terms": terms,
        "named_differences": differences,
    }


def draw_pair(category: dict, measured: dict, target: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(12, 11))
    for col, side in enumerate(("normal", "diagnosed")):
        item, sample = measured[side], category[side]
        image, mask = item["image"], item["mask"]
        values = image[image > 0]
        low, high = np.percentile(values, (1, 99.5))
        for row in range(2):
            ax = axes[row, col]
            ax.imshow(image, cmap="gray", vmin=low, vmax=high)
            if row:
                ax.contour(mask, levels=[0.5], colors=["#ff2fd0"], linewidths=1.1)
                r0, r1, c0, c1 = item["bounds"]
                margin = max(r1 - r0, c1 - c0) * 0.5 + 12
                ax.set_xlim(max(0, c0 - margin), min(image.shape[1], c1 + margin))
                ax.set_ylim(min(image.shape[0], r1 + margin), max(0, r0 - margin))
            ax.axis("off")
            ax.set_title(
                f"{side.upper()} · {item['view']['orientation']} · z={sample['slice']}"
                if row == 0
                else "Actual teaching support (rough)"
            )
    fig.suptitle(
        f"{category['question']}: {category['subject']}\n"
        "Independent condition calls; magenta marks the sampled teaching region"
    )
    fig.tight_layout()
    fig.savefig(target, dpi=115)
    plt.close(fig)


def build(
    spec_path: Path, root: Path, output: Path, *, require_all_questions: bool = True
) -> dict:
    if output.exists():
        raise ValueError("teaching_output_already_exists")
    spec = json.loads(spec_path.read_text())
    if (
        digest(Path(spec["source_memory"]) / "manifest.json")
        != spec["source_memory_sha256"]
    ):
        raise ValueError("source_memory_pin_stale")
    with (root / "train.csv").open() as handle:
        rows = {r["StudyInstanceUID"]: r for r in csv.DictReader(handle)}
    validate_categories(spec, rows, require_all_questions=require_all_questions)
    output.mkdir(parents=True)
    namespace = spec.get("case_namespace")
    case_prefix = f"grounded:{namespace}:" if namespace else "grounded:"
    cases, measured, receipts = [], {}, {}
    # Complete a study once and release it; all examples share its one reading.
    uids = sorted(
        {c[s]["study_uid"] for c in spec["categories"] for s in ("normal", "diagnosed")}
    )
    for uid in uids:
        print(f"Reading teaching study {uid}", flush=True)
        study = read_study_squints(root, uid, io_workers=3)
        legs = leg_maps(study)
        for c in spec["categories"]:
            for side, call in (("normal", -1), ("diagnosed", 1)):
                sample = c[side]
                if sample["study_uid"] != uid:
                    continue
                item = measure_sample(study, legs, sample, c["subject"])
                slug = c["question"].lower().replace(" ", "-").replace("'", "")
                cid = f"{case_prefix}{slug}:{side}"
                measured[cid] = item
                # Calls and interpretations are attached only after measuring.
                case = {
                    "case_id": cid,
                    "study_uid": uid,
                    "subject": c["subject"],
                    "condition_calls": {c["question"]: call},
                    "profile": item["profile"],
                    "regions": [
                        {
                            "series_uid": sample["series_uid"],
                            "view": item["view"],
                            "window": item["territory"]["tile_window"],
                            "territory": item["territory"],
                        }
                    ],
                    "source": {
                        "kind": "independent_direct_visual_teaching",
                        "native_dicom_path": item["native_path"],
                        "native_dicom_sha256": item["native_sha256"],
                        "sample": sample,
                    },
                    "teaching_source": {
                        "kind": "independent_visual_and_official_call",
                        "reader": spec["reader"],
                        "native_sha256": item["native_sha256"],
                        "sample": sample,
                        "official_row": rows[uid],
                    },
                }
                view = item["view"]
                identity_call = {
                    "candidate_id": cid,
                    "call": "confirm",
                    "reader": spec["reader"],
                    "notes": sample["visual_reading"],
                    "views": [
                        [
                            view["orientation"],
                            view["fluid_sensitive"],
                            view["fat_suppression"],
                        ]
                    ],
                }
                localized = []
                if call == 1 and c["question"] in {"Fracture", "Contusion"}:
                    localized = [
                        {
                            "study_uid": uid,
                            "subject": c["subject"],
                            "question": c["question"],
                            "digit": 1,
                            "source": {
                                "kind": "independent_report_localization",
                                "official_report": rows[uid]["Report"],
                                "pictured_site": sample["visual_reading"],
                            },
                        }
                    ]
                carried = carry_condition_calls(
                    case,
                    identity_call,
                    {c["question"]: int(call == 1)},
                    localized_calls=localized,
                )
                if carried["condition_calls"] != {c["question"]: call}:
                    raise ValueError("teaching_condition_not_implicated_by_object")
                case["condition_calls"] = carried["condition_calls"]
                case["presentation_scope"] = carried["presentation_scope"]
                case["condition_teaching"] = carried
                case["identity_call"] = identity_call
                cases.append(case)
        del study, legs
    memory = reference_memory(cases, digest(spec_path))
    pages = []
    for c in spec["categories"]:
        slug = c["question"].lower().replace(" ", "-").replace("'", "")
        pair = {
            side: measured[f"{case_prefix}{slug}:{side}"]
            for side in ("normal", "diagnosed")
        }
        receipt = compare_references(
            pair["normal"]["profile"], pair["diagnosed"]["profile"]
        )
        names = tuple(
            sorted(
                set(pair["normal"]["profile"]["banks"])
                | set(pair["diagnosed"]["profile"]["banks"])
            )
        )
        carrier = HadamardCarrier.from_banks(names)
        for side, item in pair.items():
            counts = np.zeros((len(names), ROW_WIDTH), dtype=np.int64)
            for i, name in enumerate(names):
                counts[i, :3] = item["profile"]["banks"].get(name, [0, 0, 0])
            vectors = carrier.encode(counts)
            if not np.array_equal(carrier.decode(vectors), counts):
                raise ValueError("teaching_hdc_roundtrip_failed")
            np.savez_compressed(
                output / f"{slug}-{side}.npz",
                counts=counts,
                vectors=vectors,
                banks=np.array(names),
                mask=item["mask"],
            )
            finding = recall_object(item["profile"], memory, c["question"])
            receipt[side + "_teaching_replay"] = finding
        receipt["carrier_identity"] = carrier.identity
        receipts[c["question"]] = receipt
        draw_pair(c, pair, output / f"{slug}.png")
        c["measured_comparison"] = receipt["outcome"]
        c["normal_replay"] = receipt["normal_teaching_replay"]["outcome"]
        c["diagnosed_replay"] = receipt["diagnosed_teaching_replay"]["outcome"]
        pages.extend(
            [
                f"## {c['question']} — {c['subject']}",
                c["identity"],
                f"**Normal reference:** {c['normal_reference']}",
                f"**Altered reference:** {c['altered_reference']}",
                f"![{c['question']}](../{output.as_posix()}/{slug}.png)"
                if require_all_questions
                else f"![{c['question']}]({slug}.png)",
                f"**Normal image:** {c['normal']['visual_reading']}",
                f"**Diagnosed image:** {c['diagnosed']['visual_reading']}",
                (
                    f"**Encoding:** {receipt['outcome']}; "
                    f"{len(receipt['named_differences'])} nonproportional named banks. "
                    f"Teaching replay: {c['normal_replay']} / {c['diagnosed_replay']}."
                ),
                f"[Measured differences and actual recall](../{output.as_posix()}/receipt.json)"
                if require_all_questions
                else "[Measured differences and actual recall](receipt.json)",
                "",
            ]
        )
    (output / "reference_cases.json").write_text(
        json.dumps(
            _json_value(
                {
                    "schema": "knee.grounded-reference-workset/v1",
                    "spec": spec,
                    "spec_sha256": digest(spec_path),
                    "label_sha256": digest(root / "train.csv"),
                    "cases": cases,
                }
            ),
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    (output / "receipt.json").write_text(
        json.dumps(_json_value(receipts), indent=2) + "\n"
    )
    doc = (
        Path("docs/GROUNDED_TEACHING.md")
        if require_all_questions
        else output / "README.md"
    )
    doc.write_text(
        "# Hand-defined normal and condition teaching references\n\n"
        "These are independently source-labeled, visually addressed teaching presentations. "
        "The regions are annotations of these images, not rules for locating new knees. "
        "Identity and state stay separate. The pinned signed parent is untouched.\n\n"
        "This workset uses the production 10 mm and 2 mm writers, exact Hadamard carrier "
        "and ordinary case-recall engine. Labels and written meanings are not feature banks. "
        "Teaching replay checks the supplied examples, not held-out transfer. "
        "Named bank differences are image measurements, not automatically clinical causes.\n\n"
        "[Workset files, reproduction, replay and scope](teaching/README.md).\n\n"
        "Clinical reference: [Chien et al., MRI of the knee](https://doi.org/10.5114/pjr.2020.99415). "
        "Each case retains the entire independent official report and label row.\n\n"
        + "\n\n".join(pages)
        + "\n"
    )
    return {
        "outcome": "grounded_references_built",
        "cases": len(cases),
        "categories": [
            {
                "question": c["question"],
                "comparison": c["measured_comparison"],
                "normal": c["normal_replay"],
                "diagnosed": c["diagnosed_replay"],
            }
            for c in spec["categories"]
        ],
        "guide": str(doc),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--spec", type=Path, default=Path("docs/teaching/seed_categories.json")
    )
    parser.add_argument("--root", type=Path, default=Path("data/raw"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--replay", type=Path)
    parser.add_argument(
        "--partial",
        action="store_true",
        help="Build a named incremental batch without replacing the initial reference guide.",
    )
    args = parser.parse_args()
    if args.replay:
        print(json.dumps(replay_workset(args.replay), indent=2))
    elif args.output:
        print(
            json.dumps(
                build(
                    args.spec,
                    args.root,
                    args.output,
                    require_all_questions=not args.partial,
                ),
                indent=2,
            )
        )
    else:
        parser.error("--output or --replay is required")
