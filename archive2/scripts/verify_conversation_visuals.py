"""Check saved B2 picture lineage without rerunning a measurement or renderer."""

import argparse
import json
from hashlib import sha256
from pathlib import Path


def digest(path: Path) -> str | None:
    return sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def picture_status(folder: Path) -> dict:
    manifest_path = folder / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    receipt_path = Path(manifest["receipt_path"])
    receipt = json.loads(receipt_path.read_text())
    records = [
        row
        for row in receipt["records"]
        if row["study_uid"] == manifest["study_uid"] and "conversation" in row
    ]
    by_uid = {row["series_uid"]: row for row in records}
    focus = manifest["focused_views"]
    checks = {
        "receipt_current": digest(receipt_path) == manifest["receipt_sha256"],
        "renderer_current": digest(Path(manifest["renderer_path"]))
        == manifest["renderer_sha256"],
        "serializer_current": digest(Path(manifest["serializer_path"]))
        == manifest["serializer_sha256"],
        "all_views_present_once": len(focus) == len(by_uid)
        and {entry["series_uid"] for entry in focus} == set(by_uid),
        "all_stage_images_present": len(manifest["stages"]) == 5
        and set(manifest["image_sha256"])
        == {manifest["overview"], *manifest["stages"], *(x["image"] for x in focus)},
        "images_current": all(
            digest(folder / name) == expected
            for name, expected in manifest["image_sha256"].items()
        ),
        "artifacts_current": all(
            digest(Path(entry["artifact"])) == entry["artifact_sha256"]
            for entry in [*manifest["panels"], *focus]
        ),
    }
    checks["source_coordinates_match"] = all(
        entry["series_uid"] in by_uid
        and entry["source_plane"] == by_uid[entry["series_uid"]]["source_plane"]
        and entry["slice_index"] == by_uid[entry["series_uid"]]["slice_index"]
        and entry["donor_uids"]
        == [
            peer["donor_uid"]
            for peer in by_uid[entry["series_uid"]]["conversation"]["exchanges"]
        ]
        and Path(entry["artifact"]).resolve()
        == (receipt_path.parent / by_uid[entry["series_uid"]]["artifact"]).resolve()
        for entry in [*manifest["panels"], *focus]
    )
    checks["focused_views_match"] = all(
        entry["series_uid"] in by_uid
        and entry["view"] == by_uid[entry["series_uid"]]["view"]
        and entry["image_sha256"] == manifest["image_sha256"][entry["image"]]
        for entry in focus
    )
    # Stage keys omit the .png suffix in the renderer's panel records.
    checks["all_stage_panels_present_once"] = len(manifest["panels"]) == 5 * len(
        by_uid
    ) and {(entry["stage"], entry["series_uid"]) for entry in manifest["panels"]} == {
        (Path(stage).stem, uid) for stage in manifest["stages"] for uid in by_uid
    }
    return {
        "standing": "current" if records and all(checks.values()) else "mismatch",
        "scope": "picture integrity and lineage; recompute B1/B2 numerical standing separately",
        "checks": checks,
        "views": len(focus),
        "images": len(manifest["image_sha256"]),
        "manifest_sha256": digest(manifest_path),
        "checker_sha256": digest(Path(__file__)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    try:
        result = picture_status(args.folder)
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = {"standing": "invalid_manifest", "error": str(error)}
    (args.folder / "visual-status.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["standing"] == "current" else 1)


if __name__ == "__main__":
    main()
