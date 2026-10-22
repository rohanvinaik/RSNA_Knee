#!/usr/bin/env python3
"""Human-called object-identity bootstrap sheets (pure categorization).

export: select object candidates from explicit filters and sorted case ids only,
render native raw pixels with the native teacher-support overlay for every view
that is actually available, build the review with the shared seed API, add
drawing-only evidence, write the final review bytes and hash those exact bytes.

admit: rehash the review file bytes, check the rendered sheets, then hand the
review, the human calls and the hash to the shared seed API. Nothing is
inferred, ranked or relabelled here. A review of a growth child's admissions
(from ``export-admissions``) goes to the shared admission-correction API instead:
each call applies only where it asserts, so a rejected view becomes a negative
case on exactly that view while the admission's other views keep speaking, a
confirm is recorded only, and the corrected memory is a new child of the
reviewed one.

export-admissions: review a growth child's admissions on their pictures before the
child becomes the next parent (by default every standing admission of its latest
round). Each sheet is drawn exactly as ``sheets`` draws a decision: the squint tile
windows the recognition read, on the native slices. The review pins each admitted
case and its round's confirm row, with its cheap profile, regions, views and
lineage. No full profile is required or made, and nothing is recognized.

sheets: draw one picture sheet per identity-admission decision, so the first
growth round's admissions can be looked at before their child memory becomes
the next parent. Nothing is recognized: a decision carries the squint tile
windows the recognition read, and each sheet shows those windows on the native
slices of the study. It runs locally, on the studies under a competition root
(train_series/ or test_series/, found through the competition's own tables).

grow: read the per-study records of squint inference output directories, turn
each located object into a candidate, and decide every candidate against one
frozen signed parent with the shared growth API. ``admission-decisions.json``
is always written in the new output directory; the warranted child, if any, is
published at ``<output>/memory`` unless ``--decisions-only``. ``--labels``
(train.csv) carries each admitted study's official labels onto its admitted
case after every decision is made; ``--held-out`` (one StudyInstanceUID per
line) names studies whose candidates are never admitted and whose labels are
never read, joined with those the parent's growth block already holds out.
"""

from __future__ import annotations

import argparse
import copy
import gc
import hashlib
import importlib.util
import json
import math
import os
import re
import sys
import tempfile
import textwrap
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from itertools import groupby
from pathlib import Path
from typing import Any

from knee.diagnosis.squint_bootstrap import (
    ADMISSION_REVIEW_SCHEMA,
    CALLS_SCHEMA,
    SquintBootstrapError,
    adapt_recorded_calls,
    build_admission_review,
    build_review,
    publish_admission_corrections,
    publish_seed_memory,
    round_admissions,
    validate_calls,
)
from knee.diagnosis.squint_identity_growth import (
    IdentityGrowthError,
    grow_identity_memory,
    harvest_inference,
    inference_record_paths,
)
from knee.diagnosis.squint_memory import SquintMemoryError, load_memory_snapshot

DEFAULT_LIMIT = 12
DIAGNOSIS_PREFIX = "diagnosis/"
BANNER = "UNCALLED PROPOSAL"
SELECTION_RULE = "explicit_filters_and_sorted_case_id_only"
NL = chr(10)
_HEX = re.compile(r"^[0-9a-f]{64}$")
_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


class ObjectBootstrapError(ValueError):
    """Named refusal of the CLI-owned steps; .code is the stable code."""

    def __init__(self, code: str, detail: Any = None):
        super().__init__(code)
        self.code = code
        self.detail = detail


# ---------------------------------------------------------------- utilities


def _plain(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_plain(v) for v in value]
    if hasattr(value, "tolist"):
        return _plain(value.tolist())
    return value


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        _plain(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _json_bytes(value: Any) -> bytes:
    text = json.dumps(_plain(value), indent=2, sort_keys=True, ensure_ascii=False)
    return (text + NL).encode("utf-8")


def _write_bytes(path: Path, data: bytes) -> None:
    path = Path(path)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".part")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.replace(name, path)
    except BaseException:
        Path(name).unlink(missing_ok=True)
        raise


def _parse_json(raw: bytes, code: str) -> Any:
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError) as error:
        raise ObjectBootstrapError(code) from error


def _read_bytes(path: Path, code: str) -> bytes:
    try:
        return Path(path).read_bytes()
    except OSError as error:
        raise ObjectBootstrapError(code, str(path)) from error


def _is_hex(value: Any) -> bool:
    return isinstance(value, str) and _HEX.match(value) is not None


def _is_object_case(case: Any) -> bool:
    return (
        isinstance(case, Mapping)
        and isinstance(case.get("subject"), str)
        and bool(case["subject"])
        and not case["subject"].startswith(DIAGNOSIS_PREFIX)
    )


def _cases_by_id(memory: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    cases = memory.get("cases") if isinstance(memory, Mapping) else None
    if not isinstance(cases, list):
        raise ObjectBootstrapError("memory_cases_invalid")
    by_id: dict[str, Mapping[str, Any]] = {}
    for case in cases:
        if isinstance(case, Mapping) and isinstance(case.get("case_id"), str):
            by_id[case["case_id"]] = case
    return by_id


def source_product(
    memory: Mapping[str, Any], case: Mapping[str, Any]
) -> dict[str, Any]:
    """Actual product address for rendering; never invented.

    Prefer source_identities[study]; fall back to the case full_source. The
    sha must agree with case full_source.product_sha256.
    """
    full = case.get("full_source")
    if not isinstance(full, Mapping):
        raise ObjectBootstrapError("source_product_sha256_missing", case.get("case_id"))
    case_sha = full.get("product_sha256")
    if not isinstance(case_sha, str) or not case_sha:
        raise ObjectBootstrapError("source_product_sha256_missing", case.get("case_id"))
    identities = memory.get("source_identities")
    identity = (
        identities.get(case.get("study_uid"))
        if isinstance(identities, Mapping)
        else None
    )
    if isinstance(identity, Mapping):
        path = identity.get("product_path")
        if isinstance(path, str) and path:
            if identity.get("product_sha256") != case_sha:
                raise ObjectBootstrapError(
                    "source_product_mismatch", case.get("case_id")
                )
            return {"path": path, "sha256": case_sha, "origin": "source_identities"}
    path = full.get("product_path")
    if isinstance(path, str) and path:
        return {"path": path, "sha256": case_sha, "origin": "full_source"}
    return {"path": None, "sha256": case_sha, "origin": "unavailable"}


# ---------------------------------------------------------------- selection


def select_case_ids(
    memory: Mapping[str, Any],
    *,
    study_uids: Sequence[str] = (),
    subjects: Sequence[str] = (),
    case_ids: Sequence[str] = (),
    limit: int = DEFAULT_LIMIT,
) -> list[str]:
    """Object case ids from explicit filters, in stable sorted-id order.

    Nothing here reads a score, support, profile or similarity.
    """
    if type(limit) is not int or limit <= 0:
        raise ObjectBootstrapError("limit_invalid")
    for values in (study_uids, subjects, case_ids):
        if isinstance(values, (str, bytes)) or any(
            not isinstance(v, str) or not v for v in values
        ):
            raise ObjectBootstrapError("filter_values_invalid")
    by_id = _cases_by_id(memory)
    for cid in case_ids:
        if cid not in by_id:
            raise ObjectBootstrapError("case_id_unknown", cid)
        if not _is_object_case(by_id[cid]):
            raise ObjectBootstrapError("case_id_not_object_case", cid)
    wanted, studies, subs = set(case_ids), set(study_uids), set(subjects)
    chosen = sorted(
        cid
        for cid, case in by_id.items()
        if _is_object_case(case)
        and (not wanted or cid in wanted)
        and (not studies or case.get("study_uid") in studies)
        and (not subs or case.get("subject") in subs)
    )
    if not chosen:
        raise ObjectBootstrapError("no_object_cases_selected")
    return chosen[:limit]


# ------------------------------------------------------------ sheet checks


def verify_sheets(review: Any, directory: Path) -> None:
    """Each sheet must stay inside the review directory and keep its pinned bytes."""
    base = Path(directory).resolve()
    candidates = review.get("candidates") if isinstance(review, Mapping) else None
    if not isinstance(candidates, list) or not candidates:
        raise ObjectBootstrapError("review_malformed")
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            raise ObjectBootstrapError("review_malformed")
        evidence = candidate.get("evidence")
        sheet = evidence.get("sheet") if isinstance(evidence, Mapping) else None
        rel = candidate.get("sheet_path")
        pinned = sheet.get("sha256") if isinstance(sheet, Mapping) else None
        if (
            not isinstance(sheet, Mapping)
            or not isinstance(rel, str)
            or not rel
            or not _is_hex(pinned)
            or sheet.get("file") != rel
        ):
            raise ObjectBootstrapError(
                "review_evidence_unrendered", candidate.get("candidate_id")
            )
        path = (base / rel).resolve()
        if path == base or base not in path.parents:
            raise ObjectBootstrapError("review_sheet_path_escape", rel)
        if not path.is_file():
            raise ObjectBootstrapError("review_sheet_missing", rel)
        if _sha256_file(path) != pinned:
            raise ObjectBootstrapError("review_sheet_sha256_mismatch", rel)


# ---------------------------------------------------------------- rendering


def _visual() -> Any:
    name = "squint_visual_capacity"
    if name in sys.modules:
        return sys.modules[name]
    path = Path(__file__).resolve().with_name("squint_visual_capacity.py")
    spec = (
        importlib.util.spec_from_file_location(name, path) if path.is_file() else None
    )
    if spec is None or spec.loader is None:
        raise ObjectBootstrapError("visual_capacity_helpers_unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as error:
        sys.modules.pop(name, None)
        raise ObjectBootstrapError("visual_capacity_helpers_unavailable") from error
    return module


def _visual_attr(name: str) -> Callable:
    helper = getattr(_visual(), name, None)
    if not callable(helper):
        raise ObjectBootstrapError("visual_capacity_helpers_unavailable", name)
    return helper


def _default_image_reader(root, study_uid, need, product):
    return _visual_attr("read_study_images")(Path(root), study_uid, need, product, 4)


def _view_label(view: Any) -> str:
    if view is None:
        return "view_unrecorded"
    if isinstance(view, str):
        return view
    if isinstance(view, Mapping):
        return (
            f"{view.get('orientation', '?')} | fluid={view.get('fluid_sensitive', '?')}"
            f" | FS={view.get('fat_suppression', '?')}"
        )
    return json.dumps(_plain(view), sort_keys=True, separators=(",", ":"))


def _window_tuple(value: Any) -> list[int] | None:
    if (
        isinstance(value, (str, bytes))
        or not isinstance(value, Sequence)
        or len(value) != 6
    ):
        return None
    if any(type(v) is not int for v in value) or min(value) < 0:
        return None
    z0, z1, r0, r1, c0, c1 = value
    if z1 <= z0 or r1 <= r0 or c1 <= c0:
        return None
    return [int(v) for v in value]


def _candidate_panels(regions: Any, window_of: Callable) -> list[dict]:
    panels: list[dict] = []
    seen: set = set()
    for region in regions or []:
        if not isinstance(region, Mapping):
            continue
        try:
            window = _window_tuple(window_of(region))
        except (TypeError, ValueError, KeyError, IndexError):
            window = None
        view = region.get("view")
        panel = {
            "series_uid": region.get("series_uid"),
            "view": view,
            "view_label": _view_label(view),
            "window": window,
            "slice": window[0] if window else None,
        }
        key = (str(panel["series_uid"]), panel["view_label"], json.dumps(window))
        if key in seen:
            continue
        seen.add(key)
        panels.append(panel)
    return panels


def _native_bounds(
    image: Mapping[str, Any], window: Sequence[int], shape: tuple
) -> tuple | None:
    import numpy as np

    bounds = np.asarray(image.get("bounds_rc"))
    _, _, wr0, wr1, wc0, wc1 = window
    if (
        bounds.ndim != 3
        or bounds.shape[2] != 4
        or not (0 <= wr0 < wr1 <= bounds.shape[0])
        or not (0 <= wc0 < wc1 <= bounds.shape[1])
    ):
        return None
    sub = bounds[wr0:wr1, wc0:wc1]
    r0 = max(0, int(sub[..., 0].min()))
    r1 = min(int(shape[0]), int(sub[..., 1].max()))
    c0 = max(0, int(sub[..., 2].min()))
    c1 = min(int(shape[1]), int(sub[..., 3].max()))
    if r1 <= r0 or c1 <= c0:
        return None
    return r0, r1, c0, c1


def _evaluate(
    panel, study_uid, subject, images, territories, study_error
) -> dict[str, Any]:
    import numpy as np

    row: dict[str, Any] = {
        "panel": panel,
        "image_state": None,
        "image_reason": None,
        "image_source_path": None,
        "support_state": "not_attempted",
        "support_reason": None,
        "support_mask_sha256": None,
        "support_resolver": None,
        "support_mask_px": None,
        "pixels": None,
        "native": None,
        "mask": None,
        "offset": None,
    }
    series_uid = panel["series_uid"]
    if panel["window"] is None:
        row["image_state"] = "window_unreadable"
        return row
    if not isinstance(series_uid, str) or not series_uid:
        row["image_state"] = "region_series_unrecorded"
        return row
    if study_error:
        row["image_state"] = "study_read_failed"
        row["image_reason"] = study_error
        return row
    z = panel["slice"]
    image = images.get((study_uid, series_uid, z))
    if not isinstance(image, Mapping):
        row["image_state"] = "image_not_returned"
        return row
    if image.get("code") != "read":
        row["image_state"] = str(image.get("code"))
        return row
    pixels = np.asarray(image.get("pixels"))
    if pixels.ndim != 2 or not pixels.size:
        row["image_state"] = "pixels_invalid"
        return row
    native = _native_bounds(image, panel["window"], pixels.shape)
    if native is None:
        row["image_state"] = "window_outside_tile_grid"
        return row
    row.update(
        image_state="read",
        pixels=pixels,
        native=native,
        image_source_path=image.get("source_path"),
    )
    territory = territories.get((study_uid, subject, series_uid, z))
    if not isinstance(territory, Mapping):
        row["support_state"] = "support_not_returned"
        return row
    if territory.get("code") != "resolved":
        row["support_state"] = str(territory.get("code"))
        row["support_reason"] = territory.get("support_code")
        return row
    support = territory.get("native_support")
    mask = (
        np.asarray(support.get("mask"), dtype=bool)
        if isinstance(support, Mapping)
        else None
    )
    offset = support.get("offset_rc") if isinstance(support, Mapping) else None
    if mask is not None and mask.ndim == 3:
        mask = mask.any(axis=0)
    if (
        mask is None
        or mask.ndim != 2
        or not isinstance(offset, (list, tuple))
        or len(offset) != 2
        or any(type(v) is not int for v in offset)
    ):
        row["support_state"] = "support_mask_invalid"
        return row
    if not mask.any():
        row["support_state"] = "support_empty"
        return row
    if (
        offset[0] < 0
        or offset[1] < 0
        or offset[0] + mask.shape[0] > pixels.shape[0]
        or offset[1] + mask.shape[1] > pixels.shape[1]
    ):
        row["support_state"] = "support_outside_slice"
        return row
    row.update(
        support_state="drawn",
        mask=mask,
        offset=(int(offset[0]), int(offset[1])),
        support_mask_sha256=territory.get("mask_sha256"),
        support_resolver=territory.get("resolver"),
        support_mask_px=int(mask.sum()),
    )
    return row


def _limits(np: Any, array: Any) -> tuple[float, float]:
    finite = array[np.isfinite(array)]
    if not finite.size:
        return 0.0, 1.0
    low, high = np.percentile(finite, (1.0, 99.0))
    if not high > low:
        high = low + 1.0
    return float(low), float(high)


def _contour(np: Any, ax: Any, mask: Any, offset: tuple) -> None:
    padded = np.pad(mask.astype(float), 1)
    ys = np.arange(offset[0] - 1, offset[0] + mask.shape[0] + 1)
    xs = np.arange(offset[1] - 1, offset[1] + mask.shape[1] + 1)
    ax.contour(xs, ys, padded, levels=[0.5], colors=["#ff00ff"], linewidths=1.1)


def _render_sheet(path: Path, candidate: Mapping[str, Any], rows: list[dict]) -> None:
    import numpy as np
    from matplotlib.figure import Figure
    from matplotlib.patches import Rectangle

    n = max(1, len(rows))
    height = 2.2 + 3.7 * n
    fig = Figure(figsize=(10.0, height), dpi=100)

    def top(offset: float) -> float:
        return 1.0 - offset / height

    cid = candidate["candidate_id"]
    identity = candidate["proposed_identity"]
    study = candidate["study_uid"]
    views = sorted(
        {r["panel"]["view_label"] for r in rows if r["image_state"] == "read"}
    )
    view_text = ", ".join(views) if views else "none"
    fig.text(
        0.5,
        top(0.1),
        BANNER,
        ha="center",
        va="top",
        fontsize=26,
        weight="bold",
        color="#b00020",
    )
    fig.text(
        0.02,
        top(0.75),
        "candidate: " + cid,
        ha="left",
        va="top",
        fontsize=8,
        family="monospace",
    )
    fig.text(
        0.02,
        top(1.0),
        "proposed identity: " + str(identity) + "    study: " + str(study),
        ha="left",
        va="top",
        fontsize=8,
    )
    fig.text(
        0.02,
        top(1.25),
        "Magenta: recorded teacher support. Yellow dashed: coarse tile window. Confirm / reject / unsure refers to object identity.",
        ha="left",
        va="top",
        fontsize=7,
    )
    fig.text(
        0.02, top(1.5), "available views: " + view_text, ha="left", va="top", fontsize=8
    )
    fig.subplots_adjust(
        top=top(1.9), bottom=0.02, left=0.04, right=0.98, hspace=0.45, wspace=0.08
    )
    if not rows:
        fig.text(
            0.5,
            0.45,
            "No view available: no region address is recorded for this case",
            ha="center",
            va="center",
            fontsize=10,
        )
    for i, row in enumerate(rows):
        left = fig.add_subplot(n, 2, 2 * i + 1)
        right = fig.add_subplot(n, 2, 2 * i + 2)
        for ax in (left, right):
            ax.set_xticks([])
            ax.set_yticks([])
        panel = row["panel"]
        series = str(panel["series_uid"])[-12:]
        head = (
            str(panel["view_label"])
            + " | series ..."
            + series
            + " | slice "
            + str(panel["slice"])
        )
        left.set_title(head + " | native raw", fontsize=7)
        right.set_title("cropped context", fontsize=7)
        if row["image_state"] != "read":
            state = row["image_state"]
            for ax in (left, right):
                ax.text(
                    0.5,
                    0.5,
                    "native slice not drawn:" + NL + str(state),
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                    fontsize=8,
                )
            continue
        pixels = row["pixels"]
        r0, r1, c0, c1 = row["native"]
        mask, offset = row["mask"], row["offset"]
        low, high = _limits(np, pixels)
        left.imshow(pixels, cmap="gray", vmin=low, vmax=high, interpolation="nearest")
        kr0, kr1, kc0, kc1 = r0, r1, c0, c1
        if mask is not None:
            kr0, kr1 = min(kr0, offset[0]), max(kr1, offset[0] + mask.shape[0])
            kc0, kc1 = min(kc0, offset[1]), max(kc1, offset[1] + mask.shape[1])
        pad = 16
        kr0, kr1 = max(0, kr0 - pad), min(pixels.shape[0], kr1 + pad)
        kc0, kc1 = max(0, kc0 - pad), min(pixels.shape[1], kc1 + pad)
        crop = pixels[kr0:kr1, kc0:kc1]
        clow, chigh = _limits(np, crop)
        right.imshow(
            crop,
            cmap="gray",
            vmin=clow,
            vmax=chigh,
            interpolation="nearest",
            extent=(kc0 - 0.5, kc1 - 0.5, kr1 - 0.5, kr0 - 0.5),
        )
        for ax in (left, right):
            ax.add_patch(
                Rectangle(
                    (c0 - 0.5, r0 - 0.5),
                    c1 - c0,
                    r1 - r0,
                    fill=False,
                    edgecolor="#ffd400",
                    linewidth=1.0,
                    linestyle=(0, (4, 2)),
                )
            )
            if mask is not None:
                _contour(np, ax, mask, offset)
            else:
                note = "NATIVE SUPPORT UNAVAILABLE: " + str(row["support_state"])
                ax.text(
                    0.5,
                    0.04,
                    note,
                    transform=ax.transAxes,
                    ha="center",
                    va="bottom",
                    fontsize=7,
                    color="white",
                    bbox={"facecolor": "#b00020", "alpha": 0.85, "pad": 2},
                )
        left.set_xlim(-0.5, pixels.shape[1] - 0.5)
        left.set_ylim(pixels.shape[0] - 0.5, -0.5)
        right.set_xlim(kc0 - 0.5, kc1 - 0.5)
        right.set_ylim(kr1 - 0.5, kr0 - 0.5)
    fig.savefig(str(path), format="png", metadata={"Software": None})


def _panel_receipt(row: Mapping[str, Any]) -> dict[str, Any]:
    panel = row["panel"]
    return {
        "series_uid": panel["series_uid"],
        "view": panel["view"],
        "view_label": panel["view_label"],
        "slice": panel["slice"],
        "window": panel["window"],
        "image_state": row["image_state"],
        "image_reason": row["image_reason"],
        "image_source_path": row["image_source_path"],
        "support_state": row["support_state"],
        "support_reason": row["support_reason"],
        "support_mask_sha256": row["support_mask_sha256"],
        "support_resolver": row["support_resolver"],
        "support_mask_px": row["support_mask_px"],
    }


def _sheet_name(index: int, cid: str) -> str:
    stem = _SAFE.sub("_", cid)[:48].strip("._") or "candidate"
    short = hashlib.sha256(cid.encode("utf-8")).hexdigest()[:8]
    return f"sheet-{index:03d}-{stem}-{short}.png"


def _index_markdown(review: Mapping[str, Any], review_sha256: str) -> str:
    lines = [
        "# Object identity bootstrap review",
        "",
        "**"
        + BANNER
        + "** - every case below is a proposal until explicit human calls are admitted.",
        "",
        "- review_sha256 (over the exact bytes of review.json): `"
        + review_sha256
        + "`",
        "- source_manifest_sha256: `" + str(review["source_manifest_sha256"]) + "`",
        "- memory_revision: `" + str(review.get("memory_revision")) + "`",
        "- candidates: " + str(len(review["candidates"])),
        "",
        "Edit `calls.json`: set `reader` and list only the candidates you call (confirm, reject or unsure).",
        "Candidates you leave out stay uncalled and never become seeds. Then run `admit`.",
    ]
    for candidate in review["candidates"]:
        evidence = candidate["evidence"]
        name = candidate["sheet_path"]
        views = evidence.get("available_views") or []
        lines += [
            "",
            "## `" + candidate["candidate_id"] + "`",
            "",
            "- status: **" + BANNER + "**",
            "- proposed identity: `" + str(candidate["proposed_identity"]) + "`",
            "- study_uid: `" + str(candidate["study_uid"]) + "`",
            "- available views: "
            + (", ".join("`" + v + "`" for v in views) if views else "none"),
        ]
        for panel in evidence.get("panels", []):
            label = panel["view_label"]
            if panel["image_state"] != "read":
                lines.append(
                    "- unavailable view `" + label + "`: " + str(panel["image_state"])
                )
            elif panel["support_state"] != "drawn":
                lines.append(
                    "- view `"
                    + label
                    + "` native support unavailable: "
                    + str(panel["support_state"])
                )
        lines += [
            "",
            "![" + candidate["candidate_id"] + "](" + name + ")",
            "",
            "[sheet](" + name + ")",
        ]
    return NL.join(lines) + NL


def export_review(
    memory: Mapping[str, Any],
    source_manifest_sha256: str,
    root: Path,
    output: Path,
    *,
    study_uids: Sequence[str] = (),
    subjects: Sequence[str] = (),
    case_ids: Sequence[str] = (),
    limit: int = DEFAULT_LIMIT,
    image_reader: Callable | None = None,
    window_of: Callable | None = None,
) -> dict[str, Any]:
    """Write index.md, review.json, calls.json and one PNG sheet per candidate."""
    ids = select_case_ids(
        memory, study_uids=study_uids, subjects=subjects, case_ids=case_ids, limit=limit
    )
    by_id = _cases_by_id(memory)
    output = Path(output)
    if os.path.lexists(output):
        raise ObjectBootstrapError("export_output_exists", str(output))
    names = {cid: _sheet_name(i, cid) for i, cid in enumerate(ids)}
    products = {cid: source_product(memory, by_id[cid]) for cid in ids}
    review = build_review(memory, source_manifest_sha256, ids, sheets=names)
    reader = image_reader or _default_image_reader
    window_of = window_of or _visual_attr("region_window")
    output.mkdir(parents=True, exist_ok=False)

    groups: dict[tuple, list[dict]] = {}
    for candidate in review["candidates"]:
        cid = candidate["candidate_id"]
        case = by_id[cid]
        candidate["proposed_identity"] = case["subject"]
        candidate["regions"] = copy.deepcopy(_plain(case.get("regions", [])))
        product = products[cid]
        key = (candidate["study_uid"], product["path"], product["sha256"])
        groups.setdefault(key, []).append(candidate)
    for key in sorted(groups, key=lambda k: (k[0], str(k[1]), k[2])):
        study_uid = key[0]
        group = groups[key]
        product = products[group[0]["candidate_id"]]
        panels = {
            c["candidate_id"]: _candidate_panels(c["regions"], window_of) for c in group
        }
        need: dict[str, set] = {"slices": set(), "supports": set()}
        for candidate in group:
            for panel in panels[candidate["candidate_id"]]:
                if (
                    panel["window"] is not None
                    and isinstance(panel["series_uid"], str)
                    and panel["series_uid"]
                ):
                    need["slices"].add((panel["series_uid"], panel["slice"]))
                    need["supports"].add(
                        (candidate["subject"], panel["series_uid"], panel["slice"])
                    )
        images: dict = {}
        territories: dict = {}
        work = None
        error = None
        status = "no_requests"
        if need["slices"]:
            if product["path"] is None:
                error = "source_product_path_unavailable"
                status = "failed"
            else:
                try:
                    images, territories, work = reader(
                        Path(root),
                        study_uid,
                        need,
                        {"path": product["path"], "sha256": product["sha256"]},
                    )
                    status = "read"
                except (
                    OSError,
                    ValueError,
                    TypeError,
                    KeyError,
                    IndexError,
                    RuntimeError,
                ) as exc:
                    images, territories, work = {}, {}, None
                    error = type(exc).__name__ + ": " + str(exc)
                    status = "failed"
        for candidate in group:
            cid = candidate["candidate_id"]
            rows = [
                _evaluate(
                    p, study_uid, candidate["subject"], images, territories, error
                )
                for p in panels[cid]
            ]
            sheet_path = output / names[cid]
            _render_sheet(sheet_path, candidate, rows)
            data = sheet_path.read_bytes()
            candidate["evidence"] = {
                "status": "rendered",
                "banner": BANNER,
                "sheet": {
                    "file": names[cid],
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "bytes": len(data),
                },
                "available_views": sorted(
                    {
                        r["panel"]["view_label"]
                        for r in rows
                        if r["image_state"] == "read"
                    }
                ),
                "panels": [_panel_receipt(r) for r in rows],
                "source_product": {
                    "path": product["path"],
                    "sha256": product["sha256"],
                    "origin": product["origin"],
                },
                "read_receipt": {
                    "status": status,
                    "error": error,
                    "work": _plain(work),
                    "root": str(root),
                },
                "inference_performed": False,
            }
    review["status"] = BANNER
    review["memory_revision"] = memory.get("revision")
    review["selection"] = {
        "rule": SELECTION_RULE,
        "ranking": "none",
        "study_uids": sorted(study_uids),
        "subjects": sorted(subjects),
        "case_ids": sorted(case_ids),
        "limit": limit,
    }
    review = _plain(review)
    review_bytes = _json_bytes(review)
    review_sha256 = hashlib.sha256(review_bytes).hexdigest()
    _write_bytes(output / "review.json", review_bytes)
    template = {
        "schema": CALLS_SCHEMA,
        "review_sha256": review_sha256,
        "reader": "",
        "calls": [],
    }
    _write_bytes(output / "calls.json", _json_bytes(template))
    (output / "index.md").write_text(
        _index_markdown(review, review_sha256), encoding="utf-8"
    )
    return {
        "action": "export",
        "output": str(output),
        "review_sha256": review_sha256,
        "candidate_count": len(review["candidates"]),
        "candidate_ids": [c["candidate_id"] for c in review["candidates"]],
    }


# ------------------------------------------------------------ admission sheets
#
# ``sheets`` draws one picture sheet per identity-admission decision so that the
# first growth round's admissions are looked at before their child memory becomes
# the next parent (docs/OBJECT_BOOTSTRAP_GUIDE.md, "Grow a recognition corpus").
# Nothing is recognized here. A decision carries the squint tile windows the
# recognition read; the sheet shows those windows on the native slices of the
# study. The sheets are drawn locally, from the studies under a competition root
# (``train_series/`` or ``test_series/``, found through the competition's own
# tables by the squint reader). The drawing stays in this script: the import
# contract keeps matplotlib out of ``knee``.

DECISIONS_SCHEMA = "knee.identity-admission-decisions/v1"
SHEETS_SCHEMA = "knee.identity-admission-sheets/v1"
SHEET_BANNER = "ADMISSION DECISION - inspect"
SHEET_DEFAULT_STATE = "admitted"
SHEET_ORDERING = "study_uid,candidate_id"
SHEET_TILE_MM = 10.0
SHEET_IO_WORKERS = 8
SHEET_CONTEXT_TILES = 3
_REQUIRED_TEXT = ("candidate_id", "study_uid", "subject", "state")
_ABSENT = object()
_ROW_RECEIPT_KEYS = (
    "series_uid",
    "view",
    "view_label",
    "window",
    "slice",
    "slice_role",
    "series_depth",
    "image_shape",
    "image_state",
    "image_reason",
    "image_source_path",
    "native_rect_rc",
    "context_rect_rc",
    "notes",
)


def load_decisions(path: Path) -> tuple[dict[str, Any], str]:
    """The decisions document and the sha256 of its exact bytes, or a named refusal.

    The schema, the required text fields of every decision, a list of regions and
    the uniqueness of each candidate_id are checked here, before any study is read.
    The descriptive fields (recognized_identity, views, support, reason, source)
    are shown as recorded and are not judged.
    """
    raw = _read_bytes(path, "decisions_unreadable")
    document = _parse_json(raw, "decisions_unparseable")
    if not isinstance(document, dict):
        raise ObjectBootstrapError("decisions_malformed")
    if document.get("schema") != DECISIONS_SCHEMA:
        raise ObjectBootstrapError(
            "decisions_schema_unrecognized", repr(document.get("schema"))
        )
    decisions = document.get("decisions")
    if not isinstance(decisions, list):
        raise ObjectBootstrapError("decisions_malformed")
    first_seen: dict[str, int] = {}
    for index, decision in enumerate(decisions):
        where = f"decisions[{index}]"
        if not isinstance(decision, dict):
            raise ObjectBootstrapError("decision_malformed", where)
        for key in _REQUIRED_TEXT:
            value = decision.get(key)
            if not isinstance(value, str) or not value:
                raise ObjectBootstrapError("decision_field_invalid", f"{where}.{key}")
        if not isinstance(decision.get("regions"), list):
            raise ObjectBootstrapError("decision_field_invalid", f"{where}.regions")
        candidate_id = decision["candidate_id"]
        if candidate_id in first_seen:
            raise ObjectBootstrapError(
                "decision_candidate_id_duplicate",
                f"{candidate_id} at decisions[{first_seen[candidate_id]}] and {where}",
            )
        first_seen[candidate_id] = index
    return document, hashlib.sha256(raw).hexdigest()


def select_decisions(
    document: Mapping[str, Any],
    *,
    states: Sequence[str] = (),
    limit: int | None = None,
) -> dict[str, Any]:
    """The decisions to draw: the requested states, in sorted (study_uid, candidate_id) order.

    ``limit`` bounds how many are drawn this run. What it leaves undrawn is listed by
    candidate_id, never dropped without a trace. Nothing here reads a score or a window.
    """
    if limit is not None and (type(limit) is not int or limit <= 0):
        raise ObjectBootstrapError("limit_invalid")
    if isinstance(states, (str, bytes)) or any(
        not isinstance(s, str) or not s for s in states
    ):
        raise ObjectBootstrapError("filter_values_invalid")
    wanted = sorted(set(states)) or [SHEET_DEFAULT_STATE]
    decisions = document["decisions"]
    counts = Counter(d["state"] for d in decisions)
    chosen = sorted(
        (d for d in decisions if d["state"] in wanted),
        key=lambda d: (d["study_uid"], d["candidate_id"]),
    )
    if not chosen:
        held = ", ".join(f"{s}={n}" for s, n in sorted(counts.items())) or "none"
        raise ObjectBootstrapError(
            "no_decisions_selected",
            "requested " + ", ".join(wanted) + "; the file holds " + held,
        )
    drawn = chosen if limit is None else chosen[:limit]
    return {
        "states": wanted,
        "limit": limit,
        "ordering": SHEET_ORDERING,
        "state_counts": dict(sorted(counts.items())),
        "matched": len(chosen),
        "drawn": drawn,
        "undrawn_by_limit": [d["candidate_id"] for d in chosen[len(drawn) :]],
    }


def window_pixel_rect(
    bounds_rc: Any, window: Sequence[int], shape: Sequence[int]
) -> tuple[int, int, int, int] | None:
    """Native half-open pixel rectangle (r0, r1, c0, c1) of a tile window.

    It is the union of the window's tiles' own bounds, so a ragged edge tile is
    exactly as large as the stack made it. None when the window's tile rows or
    columns do not lie on the grid: the rectangle is never clipped to fit.
    """
    return _native_bounds({"bounds_rc": bounds_rc}, window, tuple(shape))


def context_pixel_rect(
    rect: Sequence[int],
    tile_px: Sequence[int],
    shape: Sequence[int],
    margin_tiles: int = SHEET_CONTEXT_TILES,
) -> tuple[int, int, int, int]:
    """A view around a window: ``margin_tiles`` whole tiles each side, kept inside the slice."""
    r0, r1, c0, c1 = rect
    dr, dc = int(tile_px[0]) * margin_tiles, int(tile_px[1]) * margin_tiles
    return (
        max(0, r0 - dr),
        min(int(shape[0]), r1 + dr),
        max(0, c0 - dc),
        min(int(shape[1]), c1 + dc),
    )


def _slice_plan(window: Sequence[int], edge_slices: bool) -> list[tuple[str, int]]:
    """The slices of a half-open window to show: its middle, and optionally first and last.

    The window holds slices z0 .. z1-1, so the last is z1-1, not z1, and (z0+z1)//2
    always lies inside it. Slices that coincide share one entry with joined roles.
    """
    z0, z1 = window[0], window[1]
    wanted = [("middle", (z0 + z1) // 2)]
    if edge_slices:
        wanted = [("first", z0), ("middle", (z0 + z1) // 2), ("last", z1 - 1)]
    roles: dict[int, list[str]] = {}
    for role, z in wanted:
        roles.setdefault(z, []).append(role)
    return [("/".join(names), z) for z, names in sorted(roles.items())]


def _new_row(
    series_uid: Any, window: list[int] | None, role: str | None, z: int | None
) -> dict[str, Any]:
    return {
        "series_uid": series_uid,
        "view": None,
        "view_label": "view_unrecorded",
        "window": window,
        "slice": z,
        "slice_role": role,
        "series_depth": None,
        "image_shape": None,
        "image_state": None,
        "image_reason": None,
        "image_source_path": None,
        "native_rect_rc": None,
        "context_rect_rc": None,
        "notes": [],
        "pixels": None,
    }


def _read_row(row: dict[str, Any], record: Mapping[str, Any]) -> None:
    """Fill one row from its series record, or name why the slice cannot be drawn."""
    import numpy as np

    stack = record.get("stack")
    native = record.get("native_series")
    volume = getattr(native, "volume", None)
    if volume is None or stack is None or getattr(stack, "code", None) != "present":
        row["image_state"] = "native_volume_or_squint_unavailable"
        return
    depth = int(volume.shape[0])
    row["series_depth"] = depth
    z, window = row["slice"], row["window"]
    if not 0 <= z < depth:
        row["image_state"] = "slice_outside_series"
        return
    shape = (int(volume.shape[1]), int(volume.shape[2]))
    rect = window_pixel_rect(stack.bounds_rc, window, shape)
    if rect is None:
        row["image_state"] = "window_outside_tile_grid"
        return
    pixels = np.array(volume[z], dtype=np.float32)
    if pixels.ndim != 2 or not pixels.size:
        row["image_state"] = "pixels_invalid"
        return
    if window[1] > depth:
        row["notes"].append(f"window_z_beyond_series_depth:{depth}")
    paths = getattr(native, "slices", ())
    row.update(
        image_state="read",
        image_shape=list(shape),
        image_source_path=str(paths[z].path.resolve()) if len(paths) > z else None,
        native_rect_rc=list(rect),
        context_rect_rc=list(context_pixel_rect(rect, stack.tile_shape_rc, shape)),
        pixels=pixels,
    )


def _region_rows(
    region: Any,
    by_uid: Mapping[str, Mapping[str, Any]],
    study_error: str | None,
    edge_slices: bool,
) -> list[dict[str, Any]]:
    """The rows one region draws: one per slice shown, each with its image state named."""
    if not isinstance(region, Mapping):
        row = _new_row(None, None, None, None)
        row["image_state"] = "region_malformed"
        return [row]
    series_uid = region.get("series_uid")
    window = _window_tuple(region.get("window"))
    if window is None:
        row = _new_row(series_uid, None, None, None)
        row["image_state"] = "window_unreadable"
        return [row]
    rows = []
    for role, z in _slice_plan(window, edge_slices):
        row = _new_row(series_uid, window, role, z)
        if not isinstance(series_uid, str) or not series_uid:
            row["image_state"] = "region_series_unrecorded"
        elif study_error:
            row["image_state"] = "study_read_failed"
            row["image_reason"] = study_error
        elif series_uid not in by_uid:
            row["image_state"] = "series_missing"
        else:
            record = by_uid[series_uid]
            row["view"] = _plain(record.get("view"))
            row["view_label"] = _view_label(record.get("view"))
            _read_row(row, record)
        rows.append(row)
    return rows


def _row_receipt(row: Mapping[str, Any]) -> dict[str, Any]:
    """The plain fields of a row; the pixels never travel past the sheet they were drawn on."""
    return {key: _plain(row[key]) for key in _ROW_RECEIPT_KEYS}


def _shown(value: Any) -> str:
    """A decision field as recorded, for the sheet: text as it is, anything else JSON.

    The JSON is spaced after its separators so that a long value wraps between tokens,
    not through the middle of a word; the index carries the exact compact form.
    """
    if value is _ABSENT:
        return "unrecorded"
    if isinstance(value, str):
        return " ".join(value.split())
    return json.dumps(
        _plain(value), sort_keys=True, ensure_ascii=False, separators=(", ", ": ")
    )


def _verbatim(value: Any) -> str:
    """A decision field exactly as recorded (always JSON, so text keeps its quotes)."""
    if value is _ABSENT:
        return "unrecorded"
    return json.dumps(
        _plain(value), sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )


def _md_code(text: str) -> str:
    """A markdown code span that survives backticks inside the text.

    The fence is longer than any run of backticks in the text, and the text is padded
    with one space on each side only when it begins or ends with a backtick.
    """
    fence = "`"
    while fence in text:
        fence += "`"
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def _wrapped(text: str, lines: int = 2, width: int = 118) -> list[str]:
    pieces = textwrap.wrap(
        text, width=width, break_long_words=True, break_on_hyphens=False
    ) or [""]
    if len(pieces) > lines:
        pieces = pieces[:lines]
        pieces[-1] = pieces[-1][: width - 3] + "..."
    return pieces


def _tile_text(window: Sequence[int] | None) -> str:
    if window is None:
        return "window unreadable"
    z0, z1, r0, r1, c0, c1 = window
    return f"tile window z {z0}..{z1 - 1}, tile rows {r0}..{r1 - 1}, tile cols {c0}..{c1 - 1}"


def _decision_figure(
    decision: Mapping[str, Any], rows: list[dict[str, Any]], *, tile_mm: float
) -> Any:
    """One sheet: the decision's fields on top, then each region's native slice with its window box."""
    import numpy as np
    from matplotlib.figure import Figure
    from matplotlib.patches import Rectangle

    who = (
        f"subject: {decision['subject']}    recognized identity: "
        f"{_shown(decision.get('recognized_identity', _ABSENT))}    "
        f"study: {decision['study_uid']}"
    )
    legend = (
        "Yellow dashed box: the squint tile window the recognition read. It is not an "
        "outline of tissue, and no native support is drawn. Left: the whole native "
        f"slice. Right: the window with {SHEET_CONTEXT_TILES} tiles of context. Tiles "
        f"are {tile_mm:g} mm; tile indices are inclusive. Grey: native raw."
    )
    # (text, monospace, most lines shown); the index carries every field in full.
    fields: list[tuple[str, bool, int]] = [
        ("candidate: " + decision["candidate_id"], True, 2),
        (who, False, 2),
        ("views: " + _shown(decision.get("views", _ABSENT)), False, 2),
        ("location support: " + _shown(decision.get("support", _ABSENT)), False, 2),
        ("reason: " + _shown(decision.get("reason", _ABSENT)), False, 2),
        ("source: " + _shown(decision.get("source", _ABSENT)), False, 2),
        (legend, False, 3),
    ]
    lines = [
        (piece, mono) for text, mono, most in fields for piece in _wrapped(text, most)
    ]
    header = 0.7 + 0.19 * len(lines)
    n = max(1, len(rows))
    height = header + 0.15 + 3.7 * n
    fig = Figure(figsize=(10.0, height), dpi=100)

    def top(offset: float) -> float:
        return 1.0 - offset / height

    fig.text(
        0.5,
        top(0.08),
        f"{SHEET_BANNER}: {decision['state']}",
        ha="center",
        va="top",
        fontsize=18,
        weight="bold",
        color="#1f3a93",
    )
    for i, (piece, mono) in enumerate(lines):
        extra = {"family": "monospace"} if mono else {}
        fig.text(
            0.02, top(0.55 + 0.19 * i), piece, ha="left", va="top", fontsize=8, **extra
        )
    fig.subplots_adjust(
        top=top(header + 0.1),
        bottom=0.02,
        left=0.04,
        right=0.98,
        hspace=0.45,
        wspace=0.08,
    )
    if not rows:
        fig.text(
            0.5,
            0.45,
            "No region is recorded for this decision",
            ha="center",
            va="center",
            fontsize=10,
        )
    for i, row in enumerate(rows):
        left = fig.add_subplot(n, 2, 2 * i + 1)
        right = fig.add_subplot(n, 2, 2 * i + 2)
        for ax in (left, right):
            ax.set_xticks([])
            ax.set_yticks([])
        role = f" ({row['slice_role']})" if row["slice_role"] else ""
        head = (
            f"{row['view_label']} | series ...{str(row['series_uid'])[-12:]}"
            f" | slice {row['slice']}{role}"
        )
        left.set_title(head + " | native raw", fontsize=7)
        if row["image_state"] != "read":
            right.set_title(_tile_text(row["window"]), fontsize=7)
            reason = f"{NL}{row['image_reason']}" if row["image_reason"] else ""
            for ax in (left, right):
                ax.text(
                    0.5,
                    0.5,
                    f"native slice not drawn:{NL}{row['image_state']}{reason}",
                    transform=ax.transAxes,
                    ha="center",
                    va="center",
                    fontsize=8,
                )
            continue
        r0, r1, c0, c1 = row["native_rect_rc"]
        kr0, kr1, kc0, kc1 = row["context_rect_rc"]
        pixels = row["pixels"]
        low, high = _limits(np, pixels)
        left.imshow(pixels, cmap="gray", vmin=low, vmax=high, interpolation="nearest")
        crop = pixels[kr0:kr1, kc0:kc1]
        clow, chigh = _limits(np, crop)
        right.imshow(
            crop,
            cmap="gray",
            vmin=clow,
            vmax=chigh,
            interpolation="nearest",
            extent=(kc0 - 0.5, kc1 - 0.5, kr1 - 0.5, kr0 - 0.5),
        )
        for ax in (left, right):
            ax.add_patch(
                Rectangle(
                    (c0 - 0.5, r0 - 0.5),
                    c1 - c0,
                    r1 - r0,
                    fill=False,
                    edgecolor="#ffd400",
                    linewidth=1.0,
                    linestyle=(0, (4, 2)),
                )
            )
        left.set_xlim(-0.5, pixels.shape[1] - 0.5)
        left.set_ylim(pixels.shape[0] - 0.5, -0.5)
        right.set_xlim(kc0 - 0.5, kc1 - 0.5)
        right.set_ylim(kr1 - 0.5, kr0 - 0.5)
        right.set_title(
            f"{_tile_text(row['window'])} | pixels rows {r0}:{r1}, cols {c0}:{c1}",
            fontsize=7,
        )
    return fig


def _default_study_reader(
    root: Path, study_uid: str, *, tile_mm: float, io_workers: int
) -> dict[str, Any]:
    """The production squint reader, looked up when called so a test can stand in for it."""
    from knee.diagnosis import squint_profiles

    return squint_profiles.read_study_squints(
        Path(root), study_uid, io_workers=io_workers, tile_mm=tile_mm
    )


def _series_index(study: Any) -> dict[str, Mapping[str, Any]]:
    series = study.get("series") if isinstance(study, Mapping) else None
    if not isinstance(series, (list, tuple)):
        raise TypeError("study_series_malformed")
    return {
        record["series_uid"]: record
        for record in series
        if isinstance(record, Mapping) and isinstance(record.get("series_uid"), str)
    }


def _draw_study(
    reader: Callable[..., Any],
    root: Path,
    study_uid: str,
    group: list[dict[str, Any]],
    names: Mapping[str, str],
    output: Path,
    *,
    tile_mm: float,
    io_workers: int,
    edge_slices: bool,
) -> list[dict[str, Any]]:
    """Read one study once, draw every sheet that needs it, and return plain receipts only.

    The study, its volumes and every slice copied for drawing go out of scope with
    this call; nothing but the receipts reaches the next study.
    """
    error = None
    work = None
    by_uid: Mapping[str, Mapping[str, Any]] = {}
    try:
        study = reader(Path(root), study_uid, tile_mm=tile_mm, io_workers=io_workers)
        by_uid = _series_index(study)
        work = _plain(study.get("work"))
    except Exception as exc:  # noqa: BLE001 - the decoders' failures are open-ended
        # A study that cannot be read is the reason on each of its sheets, and the
        # run goes on to the next study; whatever the reader raised is named.
        error = f"{type(exc).__name__}: {exc}"
    receipts = []
    for decision in group:
        rows = [
            row
            for region in decision["regions"]
            for row in _region_rows(region, by_uid, error, edge_slices)
        ]
        path = output / names[decision["candidate_id"]]
        figure = _decision_figure(decision, rows, tile_mm=tile_mm)
        figure.savefig(str(path), format="png", metadata={"Software": None})
        data = path.read_bytes()
        receipts.append(
            {
                "file": path.name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "candidate_id": decision["candidate_id"],
                "study_uid": study_uid,
                "subject": decision["subject"],
                "state": decision["state"],
                "decision": _plain(decision),
                "study_read": {
                    "status": "failed" if error else "read",
                    "error": error,
                    "work": work,
                },
                "panels": [_row_receipt(row) for row in rows],
            }
        )
    return receipts


def _panel_markdown(panel: Mapping[str, Any]) -> str:
    label = _md_code(panel["view_label"])
    series = _md_code(str(panel["series_uid"]))
    role = f" ({panel['slice_role']})" if panel["slice_role"] else ""
    where = f"series {series}, slice {panel['slice']}{role}"
    tiles = _tile_text(panel["window"])
    if panel["image_state"] != "read":
        reason = f" ({panel['image_reason']})" if panel["image_reason"] else ""
        return (
            f"- NOT DRAWN {label} {where}: {_md_code(str(panel['image_state']))}{reason};"
            f" {tiles}"
        )
    r0, r1, c0, c1 = panel["native_rect_rc"]
    notes = "".join(f"; note {_md_code(note)}" for note in panel["notes"])
    return (
        f"- {label} {where} of {panel['series_depth']}: {tiles}; native pixels rows "
        f"{r0}..{r1 - 1}, cols {c0}..{c1 - 1} (half-open rows [{r0}, {r1}), cols "
        f"[{c0}, {c1})){notes}"
    )


def _panels_not_drawn(sheets: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    """How many panels were not drawn, by the state that names why."""
    tally = Counter(
        panel["image_state"]
        for sheet in sheets
        for panel in sheet["panels"]
        if panel["image_state"] != "read"
    )
    return dict(sorted(tally.items()))


def _studies_not_read(sheets: Sequence[Mapping[str, Any]]) -> list[str]:
    return sorted(
        {s["study_uid"] for s in sheets if s["study_read"]["status"] != "read"}
    )


def _sheets_index_markdown(record: Mapping[str, Any], sheets_sha256: str) -> str:
    selection = record["selection"]
    sheets = record["sheets"]
    unavailable = _panels_not_drawn(sheets)
    unread = _studies_not_read(sheets)
    counts = ", ".join(
        f"{state}={n}" + (" (requested)" if state in selection["states"] else "")
        for state, n in selection["state_counts"].items()
    )
    lines = [
        "# Identity admission decision sheets",
        "",
        "**"
        + SHEET_BANNER
        + "** - one sheet per decision. The yellow box is the squint "
        "tile window the recognition read; it is not an outline of tissue.",
        "",
        "- decisions file: "
        + _md_code(str(record["decisions"]["path"]))
        + " sha256 `"
        + record["decisions"]["sha256"]
        + "`",
        "- decisions parent: " + _md_code(_verbatim(record["decisions"]["parent"])),
        "- sheets.json sha256: `" + sheets_sha256 + "`",
        "- competition root: " + _md_code(str(record["root"])),
        f"- squint tile size: {record['tile_mm']:g} mm; edge slices: "
        + ("first, middle and last" if record["edge_slices"] else "middle only"),
        "- decisions by state: " + (counts or "none"),
        f"- requested states: {', '.join(selection['states'])}; matched "
        f"{selection['matched']}, drawn {len(sheets)}, order {selection['ordering']}"
        + (f", limit {selection['limit']}" if selection["limit"] is not None else ""),
        "- studies not read: "
        + (", ".join(_md_code(u) for u in unread) if unread else "none"),
        "- panels not drawn: "
        + (
            ", ".join(f"{state}={n}" for state, n in sorted(unavailable.items()))
            if unavailable
            else "none"
        ),
        "- left undrawn by the limit: "
        + (
            ", ".join(_md_code(c) for c in selection["undrawn_by_limit"])
            if selection["undrawn_by_limit"]
            else "none"
        ),
    ]
    for sheet in sheets:
        decision = sheet["decision"]
        lines += [
            "",
            "## " + _md_code(sheet["candidate_id"]),
            "",
            "- state: **" + sheet["state"] + "**",
            "- subject: " + _md_code(sheet["subject"]),
            "- recognized identity: "
            + _md_code(_verbatim(decision.get("recognized_identity", _ABSENT))),
            "- study_uid: " + _md_code(sheet["study_uid"]),
            "- views: " + _md_code(_verbatim(decision.get("views", _ABSENT))),
            "- location support: "
            + _md_code(_verbatim(decision.get("support", _ABSENT))),
            "- reason: " + _md_code(_verbatim(decision.get("reason", _ABSENT))),
            "- source: " + _md_code(_verbatim(decision.get("source", _ABSENT))),
            "- sheet: " + _md_code(sheet["file"]) + " sha256 `" + sheet["sha256"] + "`",
        ]
        status = sheet["study_read"]
        if status["status"] != "read":
            lines.append("- study NOT READ: " + _md_code(str(status["error"])))
        if not sheet["panels"]:
            lines.append("- no region is recorded for this decision")
        lines += [_panel_markdown(panel) for panel in sheet["panels"]]
        lines += ["", f"![{sheet['candidate_id']}]({sheet['file']})"]
    return NL.join(lines) + NL


def render_sheets(
    document: Mapping[str, Any],
    decisions_sha256: str,
    root: Path,
    output: Path,
    *,
    decisions_path: Path | str | None = None,
    states: Sequence[str] = (),
    limit: int | None = None,
    tile_mm: float = SHEET_TILE_MM,
    io_workers: int = SHEET_IO_WORKERS,
    edge_slices: bool = False,
    study_reader: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Write one PNG per selected decision, then sheets.json and index.md.

    Each study is read once and released before the next. A missing study, series or
    slice is named on its sheet, in the index and in sheets.json, never skipped.
    ``study_reader(root, study_uid, tile_mm=, io_workers=)`` defaults to the production
    squint reader. An existing output directory is refused before anything is read.
    """
    if (
        isinstance(tile_mm, bool)
        or not isinstance(tile_mm, (int, float))
        or not math.isfinite(tile_mm)
        or tile_mm <= 0
    ):
        raise ObjectBootstrapError("tile_mm_invalid")
    if type(io_workers) is not int or io_workers <= 0:
        raise ObjectBootstrapError("io_workers_invalid")
    selection = select_decisions(document, states=states, limit=limit)
    drawn = selection["drawn"]
    output = Path(output)
    if os.path.lexists(output):
        raise ObjectBootstrapError("sheets_output_exists", str(output))
    output.mkdir(parents=True, exist_ok=False)
    reader = study_reader or _default_study_reader
    names = {
        d["candidate_id"]: _sheet_name(i, d["candidate_id"])
        for i, d in enumerate(drawn)
    }
    groups = [
        (uid, list(group))
        for uid, group in groupby(drawn, key=lambda d: d["study_uid"])
    ]
    sheets: list[dict[str, Any]] = []
    for number, (study_uid, group) in enumerate(groups, 1):
        print(
            f"sheets: study {number}/{len(groups)} {study_uid}: {len(group)} decision(s)",
            file=sys.stderr,
            flush=True,
        )
        sheets.extend(
            _draw_study(
                reader,
                Path(root),
                study_uid,
                group,
                names,
                output,
                tile_mm=float(tile_mm),
                io_workers=io_workers,
                edge_slices=edge_slices,
            )
        )
        # Matplotlib figures are reference cycles; collect them with the study.
        gc.collect()
    record = {
        "schema": SHEETS_SCHEMA,
        "decisions": {
            "path": None if decisions_path is None else str(decisions_path),
            "sha256": decisions_sha256,
            "schema": document.get("schema"),
            "parent": document.get("parent"),
        },
        "root": str(root),
        "tile_mm": float(tile_mm),
        "edge_slices": bool(edge_slices),
        "selection": {k: v for k, v in selection.items() if k != "drawn"},
        "sheets": sheets,
    }
    sheets_bytes = _json_bytes(record)
    sheets_sha256 = hashlib.sha256(sheets_bytes).hexdigest()
    _write_bytes(output / "sheets.json", sheets_bytes)
    (output / "index.md").write_text(
        _sheets_index_markdown(_plain(record), sheets_sha256), encoding="utf-8"
    )
    return {
        "action": "sheets",
        "output": str(output),
        "decisions_sha256": decisions_sha256,
        "sheets_json_sha256": sheets_sha256,
        "matched": selection["matched"],
        "drawn": len(sheets),
        "undrawn_by_limit": len(selection["undrawn_by_limit"]),
        "studies": len(groups),
        "studies_not_read": _studies_not_read(sheets),
        "panels": sum(len(s["panels"]) for s in sheets),
        "panels_not_drawn": _panels_not_drawn(sheets),
    }


# ------------------------------------------------------------ admission review
#
# ``export-admissions`` turns a growth child's admissions into a review that
# ``admit`` applies (CLASSICAL_AI_BUILD_DESIGN §§7.1, 13 step 5: the first round's
# admissions are inspected before its child becomes the next parent, and a wrong
# one returns as a scoped negative). Each admission's sheet is drawn by
# ``_draw_study`` exactly as ``sheets`` draws a decision. A view counts as drawn on
# the review when its window was drawn on a read native slice (``window_state``);
# no native support exists for a recognition-derived admission, and none is drawn.

ADMISSION_REVIEW_BANNER = "ADMISSION REVIEW"
ADMISSION_SELECTION_RULE = "growth_round_standing_admissions"


def _admission_sheet_regions(regions: Any) -> list[Any]:
    """Each region as the sheet reads it: a recorded ``source_window`` is its window.

    Inference admissions record ``window``. A memory-candidate admission keeps its
    catalogue regions, which may record ``source_window`` instead, as the growth
    decision reads them. Anything else is passed on and named on its sheet.
    """
    result: list[Any] = []
    for region in regions if isinstance(regions, list) else []:
        if (
            isinstance(region, Mapping)
            and "window" not in region
            and "source_window" in region
        ):
            region = {**region, "window": region["source_window"]}
        result.append(region)
    return result


def _admission_drawing(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """The decision fields ``_draw_study`` draws for one admission, from its lineage.

    A field the lineage does not record is left out, and the sheet says so.
    """
    lineage = candidate["identity_growth"]
    decision = lineage.get("decision")
    decision = decision if isinstance(decision, Mapping) else {}
    drawing: dict[str, Any] = {
        "candidate_id": candidate["candidate_id"],
        "study_uid": candidate["study_uid"],
        "subject": candidate["subject"],
        "state": str(decision.get("state") or "admitted"),
        "views": candidate["admitted_views"],
        "regions": _admission_sheet_regions(candidate["regions"]),
    }
    for key in ("reason", "recognized_identity", "support"):
        if key in decision:
            drawing[key] = decision[key]
    if "source" in lineage:
        drawing["source"] = lineage["source"]
    return drawing


def _admission_evidence(
    sheet: Mapping[str, Any], tile_mm: float, edge_slices: bool
) -> dict[str, Any]:
    """The review's record of one drawn sheet; each panel names whether its window was drawn."""
    panels = [
        {
            **panel,
            "window_state": "drawn" if panel["image_state"] == "read" else "not_drawn",
        }
        for panel in sheet["panels"]
    ]
    return {
        "status": "rendered",
        "banner": SHEET_BANNER,
        "evidence_kind": "squint_tile_window",
        "native_support": "none_recorded_for_a_recognition_derived_admission",
        "sheet": {
            "file": sheet["file"],
            "sha256": sheet["sha256"],
            "bytes": sheet["bytes"],
        },
        "available_views": sorted(
            {p["view_label"] for p in panels if p["window_state"] == "drawn"}
        ),
        "panels": panels,
        "study_read": sheet["study_read"],
        "tile_mm": tile_mm,
        "edge_slices": edge_slices,
        "inference_performed": False,
    }


def _admission_index_markdown(review: Mapping[str, Any], review_sha256: str) -> str:
    lines = [
        "# Identity admission review",
        "",
        "**"
        + ADMISSION_REVIEW_BANNER
        + "** - every case below was admitted by recognition against a frozen parent: "
        "recognition-derived, not a visual call. The yellow box is the squint tile window "
        "the recognition read; it is not an outline of tissue, and no native support is "
        "drawn.",
        "",
        "- review_sha256 (over the exact bytes of review.json): `"
        + review_sha256
        + "`",
        "- source_manifest_sha256: `" + str(review["source_manifest_sha256"]) + "`",
        "- memory_revision: " + _md_code(str(review.get("memory_revision"))),
        "- selection: " + _md_code(_verbatim(review.get("selection", _ABSENT))),
        "- candidates: " + str(len(review["candidates"])),
        "",
        "Edit `calls.json`: set `reader` to the actual visual reviewer and list the admissions",
        "you call. `reject` makes the views you name (every drawn view when `views` is",
        "omitted) a negative case of the proposed identity; the admission's other views keep",
        "speaking for it, and only when every admitted view is rejected does the whole case",
        "move. `negative_views` and `also_positive` keep their seed meanings. `confirm`",
        "otherwise leaves an admission as it is and records your confirmation; `unsure`, or",
        "leaving it out, changes nothing. Then run `admit` with `--memory` the memory this",
        "review was exported from.",
    ]
    for candidate in review["candidates"]:
        evidence = candidate["evidence"]
        lineage = candidate["identity_growth"]
        decision = lineage.get("decision")
        decision = decision if isinstance(decision, Mapping) else {}
        drawn = evidence["available_views"]
        lines += [
            "",
            "## " + _md_code(candidate["candidate_id"]),
            "",
            "- proposed identity: " + _md_code(str(candidate["subject"])),
            "- study_uid: " + _md_code(str(candidate["study_uid"])),
            "- admitted views: " + _md_code(_verbatim(candidate["admitted_views"])),
            "- profile views: " + _md_code(_verbatim(candidate["profile_views"])),
            "- drawn views: "
            + (", ".join(_md_code(view) for view in drawn) if drawn else "none"),
            "- recognized by: "
            + _md_code(_verbatim(lineage.get("recognized_by", _ABSENT)))
            + " against parent "
            + _md_code(_verbatim(lineage.get("parent_manifest_sha256", _ABSENT))),
            "- speaking cases: "
            + _md_code(_verbatim(lineage.get("speaking_case_ids", _ABSENT))),
            "- location support: "
            + _md_code(_verbatim(decision.get("support", _ABSENT))),
            "- sheet: "
            + _md_code(evidence["sheet"]["file"])
            + " sha256 `"
            + evidence["sheet"]["sha256"]
            + "`",
        ]
        if evidence["study_read"]["status"] != "read":
            lines.append(
                "- study NOT READ: " + _md_code(str(evidence["study_read"]["error"]))
            )
        if not evidence["panels"]:
            lines.append("- no region is recorded for this admission")
        lines += [_panel_markdown(panel) for panel in evidence["panels"]]
        lines += ["", f"![{candidate['candidate_id']}]({evidence['sheet']['file']})"]
    return NL.join(lines) + NL


def export_admission_review(
    memory: Mapping[str, Any],
    source_manifest_sha256: str,
    root: Path,
    output: Path,
    *,
    case_ids: Sequence[str] = (),
    round_index: int | None = None,
    tile_mm: float = SHEET_TILE_MM,
    io_workers: int = SHEET_IO_WORKERS,
    edge_slices: bool = False,
    study_reader: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    """Write review.json, calls.json, index.md and one PNG per admission of a growth child.

    By default every standing admission of the latest growth round (``round_index``
    names another round, 0 being the first); ``case_ids`` choose admissions
    explicitly, each of which must still stand. A round's admission that no longer
    stands is named in the review's selection, never dropped without a trace. Each
    study is read once, by ``study_reader(root, study_uid, tile_mm=, io_workers=)``
    (default: the production squint reader), and released before the next. No
    recognition runs and no full profile is read.
    """
    if (
        isinstance(tile_mm, bool)
        or not isinstance(tile_mm, (int, float))
        or not math.isfinite(tile_mm)
        or tile_mm <= 0
    ):
        raise ObjectBootstrapError("tile_mm_invalid")
    if type(io_workers) is not int or io_workers <= 0:
        raise ObjectBootstrapError("io_workers_invalid")
    if isinstance(case_ids, (str, bytes)) or any(
        not isinstance(value, str) or not value for value in case_ids
    ):
        raise ObjectBootstrapError("filter_values_invalid")
    output = Path(output)
    if os.path.lexists(output):
        raise ObjectBootstrapError("export_output_exists", str(output))
    if case_ids:
        ids = list(case_ids)
        selection: dict[str, Any] = {
            "rule": "explicit_case_ids",
            "case_ids": sorted(case_ids),
        }
    else:
        chosen = round_admissions(memory, round_index=round_index)
        ids = list(chosen["standing"])
        selection = {"rule": ADMISSION_SELECTION_RULE}
        selection.update(
            (key, chosen[key])
            for key in (
                "round_index",
                "round_count",
                "parent_manifest_sha256",
                "decisions_sha256",
                "admitted_case_ids",
                "not_standing",
            )
        )
        if not ids:
            raise ObjectBootstrapError(
                "no_standing_admissions", _verbatim(chosen["not_standing"])
            )
    by_id = _cases_by_id(memory)
    ids.sort(key=lambda cid: (str(by_id.get(cid, {}).get("study_uid", "")), cid))
    names = {cid: _sheet_name(i, cid) for i, cid in enumerate(ids)}
    review = build_admission_review(memory, source_manifest_sha256, ids, sheets=names)
    output.mkdir(parents=True, exist_ok=False)
    reader = study_reader or _default_study_reader
    drawings = [_admission_drawing(candidate) for candidate in review["candidates"]]
    groups = [
        (uid, list(group))
        for uid, group in groupby(drawings, key=lambda d: d["study_uid"])
    ]
    drawn: dict[str, dict[str, Any]] = {}
    for number, (study_uid, group) in enumerate(groups, 1):
        print(
            f"export-admissions: study {number}/{len(groups)} {study_uid}: "
            f"{len(group)} admission(s)",
            file=sys.stderr,
            flush=True,
        )
        for sheet in _draw_study(
            reader,
            Path(root),
            study_uid,
            group,
            names,
            output,
            tile_mm=float(tile_mm),
            io_workers=io_workers,
            edge_slices=edge_slices,
        ):
            drawn[sheet["candidate_id"]] = sheet
        # Matplotlib figures are reference cycles; collect them with the study.
        gc.collect()
    for candidate in review["candidates"]:
        candidate["proposed_identity"] = candidate["subject"]
        candidate["evidence"] = _admission_evidence(
            drawn[candidate["candidate_id"]], float(tile_mm), bool(edge_slices)
        )
    review["memory_revision"] = memory.get("revision")
    review["selection"] = selection
    review = _plain(review)
    review_bytes = _json_bytes(review)
    review_sha256 = hashlib.sha256(review_bytes).hexdigest()
    _write_bytes(output / "review.json", review_bytes)
    template = {
        "schema": CALLS_SCHEMA,
        "review_sha256": review_sha256,
        "reader": "",
        "calls": [],
    }
    _write_bytes(output / "calls.json", _json_bytes(template))
    (output / "index.md").write_text(
        _admission_index_markdown(review, review_sha256), encoding="utf-8"
    )
    return {
        "action": "export-admissions",
        "output": str(output),
        "review_sha256": review_sha256,
        "candidate_count": len(review["candidates"]),
        "candidate_ids": [c["candidate_id"] for c in review["candidates"]],
        "not_standing": selection.get("not_standing", []),
        "studies": len(groups),
        "studies_not_read": _studies_not_read(list(drawn.values())),
        "panels_not_drawn": _panels_not_drawn(list(drawn.values())),
    }


# ---------------------------------------------------------------------- CLI


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Object-identity bootstrap sheets")
    sub = parser.add_subparsers(dest="action", required=True)
    export = sub.add_parser("export", help="render uncalled proposal sheets")
    export.add_argument("--memory", type=Path, required=True)
    export.add_argument("--root", type=Path, required=True)
    export.add_argument("--output", type=Path, required=True)
    export.add_argument("--study-uid", dest="study_uids", action="append", default=None)
    export.add_argument("--subject", dest="subjects", action="append", default=None)
    export.add_argument("--case-id", dest="case_ids", action="append", default=None)
    export.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    admissions = sub.add_parser(
        "export-admissions",
        help="render one review sheet per admission of a growth child memory",
    )
    admissions.add_argument(
        "--memory",
        type=Path,
        required=True,
        help="the growth child memory whose admissions are reviewed",
    )
    admissions.add_argument(
        "--root",
        type=Path,
        required=True,
        help="competition root holding train_series/ and test_series/",
    )
    admissions.add_argument("--output", type=Path, required=True)
    admissions.add_argument(
        "--case-id",
        dest="case_ids",
        action="append",
        default=None,
        help="an admitted case to review; repeatable; default every standing admission",
    )
    admissions.add_argument(
        "--round",
        dest="round_index",
        type=int,
        default=None,
        help="growth round whose admissions are reviewed, 0 being the first; "
        "default the latest",
    )
    admissions.add_argument(
        "--tile-mm",
        type=float,
        default=SHEET_TILE_MM,
        help="squint tile size the admissions' windows were made on",
    )
    admissions.add_argument("--io-workers", type=int, default=SHEET_IO_WORKERS)
    admissions.add_argument(
        "--edge-slices",
        action="store_true",
        help="also draw each window's first and last slice, not only its middle",
    )
    admit = sub.add_parser(
        "admit",
        help="admit explicit signed visual identity calls, or apply calls on admissions",
    )
    admit.add_argument("--memory", type=Path, required=True)
    admit.add_argument("--review", type=Path, required=True)
    admit.add_argument("--calls", type=Path, required=True)
    admit.add_argument("--output", type=Path, required=True)
    adapt = sub.add_parser(
        "adapt", help="merge recorded visual calls into one calls file, scope unchanged"
    )
    adapt.add_argument("--review", type=Path, required=True)
    adapt.add_argument(
        "--calls",
        type=Path,
        action="append",
        default=[],
        help="a recorded calls document pinned to this review; its reader is kept",
    )
    adapt.add_argument(
        "--jsonl",
        nargs=2,
        metavar=("PATH", "READER"),
        action="append",
        default=[],
        help="recorded calls, one JSON object per line, and who made them",
    )
    adapt.add_argument("--output", type=Path, required=True)
    sheets = sub.add_parser(
        "sheets", help="draw one picture sheet per identity-admission decision"
    )
    sheets.add_argument(
        "--root",
        type=Path,
        required=True,
        help="competition root holding train_series/ and test_series/",
    )
    sheets.add_argument(
        "--decisions",
        type=Path,
        required=True,
        help="an admission-decisions.json (" + DECISIONS_SCHEMA + ")",
    )
    sheets.add_argument("--output", type=Path, required=True)
    sheets.add_argument(
        "--state",
        dest="states",
        action="append",
        default=None,
        help="decision state to draw; repeatable; default " + SHEET_DEFAULT_STATE,
    )
    sheets.add_argument(
        "--limit",
        type=int,
        default=None,
        help="bound on the sheets drawn this run; what it leaves out is listed",
    )
    sheets.add_argument(
        "--tile-mm",
        type=float,
        default=SHEET_TILE_MM,
        help="squint tile size the decisions' windows were made on",
    )
    sheets.add_argument("--io-workers", type=int, default=SHEET_IO_WORKERS)
    sheets.add_argument(
        "--edge-slices",
        action="store_true",
        help="also draw each window's first and last slice, not only its middle",
    )
    grow = sub.add_parser(
        "grow",
        help="decide located inference objects against one frozen signed parent",
    )
    grow.add_argument("--parent", type=Path, required=True)
    grow.add_argument(
        "--inference",
        type=Path,
        action="append",
        required=True,
        help="a squint diagnostic output directory; its studies/ records are read",
    )
    grow.add_argument("--output", type=Path, required=True)
    grow.add_argument(
        "--decisions-only",
        action="store_true",
        help="write admission-decisions.json and publish no child memory",
    )
    grow.add_argument(
        "--labels",
        type=Path,
        default=None,
        help=(
            "the competition's train.csv; after every decision, only the rows of "
            "studies with an admitted candidate are read and carried onto it"
        ),
    )
    grow.add_argument(
        "--held-out",
        dest="held_out",
        type=Path,
        default=None,
        help=(
            "a file of StudyInstanceUIDs, one per line, whose candidates are never "
            "admitted and whose labels are never read"
        ),
    )
    return parser


def run_export(args: argparse.Namespace) -> dict[str, Any]:
    snapshot = load_memory_snapshot(args.memory)
    if not isinstance(snapshot.memory, dict) or not isinstance(snapshot.sha256, str):
        raise ObjectBootstrapError("invalid_snapshot_state")
    return export_review(
        snapshot.memory,
        snapshot.sha256,
        args.root,
        args.output,
        study_uids=args.study_uids or [],
        subjects=args.subjects or [],
        case_ids=args.case_ids or [],
        limit=args.limit,
    )


def run_admit(args: argparse.Namespace) -> dict[str, Any]:
    review_path = Path(args.review)
    raw = _read_bytes(review_path, "review_unreadable")
    review_sha256 = hashlib.sha256(raw).hexdigest()
    review = _parse_json(raw, "review_unparseable")
    if not isinstance(review, dict):
        raise ObjectBootstrapError("review_malformed")
    if "review_sha256" in review:
        raise ObjectBootstrapError("review_self_hash_present")
    calls = _parse_json(
        _read_bytes(Path(args.calls), "calls_unreadable"), "calls_unparseable"
    )
    verify_sheets(review, review_path.resolve().parent)
    snapshot = load_memory_snapshot(args.memory)
    validate_calls(review, calls, review_sha256)
    # A review of a growth child's admissions corrects that child; any other review
    # publishes a seed from its candidate catalogue. Each publisher refuses the other.
    publish = (
        publish_admission_corrections
        if review.get("schema") == ADMISSION_REVIEW_SCHEMA
        else publish_seed_memory
    )
    published = publish(snapshot, review, calls, review_sha256, Path(args.output))
    return {"action": "admit", "review_sha256": review_sha256, **published}


def run_export_admissions(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root)
    if not root.is_dir():
        raise ObjectBootstrapError("root_not_a_directory", str(root))
    snapshot = load_memory_snapshot(args.memory)
    if not isinstance(snapshot.memory, dict) or not isinstance(snapshot.sha256, str):
        raise ObjectBootstrapError("invalid_snapshot_state")
    return export_admission_review(
        snapshot.memory,
        snapshot.sha256,
        root,
        Path(args.output),
        case_ids=args.case_ids or [],
        round_index=args.round_index,
        tile_mm=args.tile_mm,
        io_workers=args.io_workers,
        edge_slices=args.edge_slices,
    )


def run_adapt(args: argparse.Namespace) -> dict[str, Any]:
    """Write ``calls.json`` and ``adaptation.json``; validated before anything is written."""
    output = Path(args.output)
    if output.exists() or output.is_symlink():
        raise ObjectBootstrapError("output_exists")
    review_path = Path(args.review)
    raw_review = _read_bytes(review_path, "review_unreadable")
    review_sha256 = hashlib.sha256(raw_review).hexdigest()
    review = _parse_json(raw_review, "review_unparseable")
    if not isinstance(review, dict):
        raise ObjectBootstrapError("review_malformed")
    sources: list[tuple[str, str, list[Any]]] = []
    provenance: list[dict[str, Any]] = []
    for path in args.calls:
        raw = _read_bytes(Path(path), "calls_unreadable")
        document = _parse_json(raw, "calls_unparseable")
        if not isinstance(document, dict) or not isinstance(
            document.get("calls"), list
        ):
            raise ObjectBootstrapError("calls_malformed")
        if document.get("review_sha256") != review_sha256:
            raise ObjectBootstrapError("stale_review_pin")
        sources.append((str(path), str(document.get("reader", "")), document["calls"]))
        provenance.append(
            {
                "path": str(path),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "reader": document.get("reader"),
            }
        )
    for path, reader in args.jsonl:
        raw = _read_bytes(Path(path), "calls_unreadable")
        records = [
            _parse_json(line.encode("utf-8"), "calls_unparseable")
            for line in raw.decode("utf-8").splitlines()
            if line.strip()
        ]
        sources.append((str(path), reader, records))
        provenance.append(
            {
                "path": str(path),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "reader": reader,
            }
        )
    adapted = adapt_recorded_calls(sources, review_sha256)
    checked = validate_calls(review, adapted["calls"], review_sha256)
    output.mkdir(parents=True)
    _write_bytes(output / "calls.json", _json_bytes(adapted["calls"]))
    _write_bytes(
        output / "adaptation.json",
        _json_bytes(
            {
                "schema": "knee.object-identity-call-adaptation/v1",
                "review_sha256": review_sha256,
                "sources": provenance,
                "mapping": adapted["mapping"],
            }
        ),
    )
    return {
        "action": "adapt",
        "output": str(output),
        "review_sha256": review_sha256,
        "call_count": len(adapted["calls"]["calls"]),
        "confirmed": len(checked["confirmed_case_ids"]),
        "negative": len(checked["negative_case_ids"]),
        "alternative_positives": len(checked["alternative_positives"]),
        "negatives_not_written": len(checked["negatives_not_written"]),
    }


def run_sheets(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root)
    if not root.is_dir():
        # Refused here, not once per study: a mistyped root would otherwise leave an
        # output directory of "study not read" sheets that blocks the rerun.
        raise ObjectBootstrapError("root_not_a_directory", str(root))
    document, decisions_sha256 = load_decisions(Path(args.decisions))
    return render_sheets(
        document,
        decisions_sha256,
        root,
        Path(args.output),
        decisions_path=Path(args.decisions),
        states=args.states or [],
        limit=args.limit,
        tile_mm=args.tile_mm,
        io_workers=args.io_workers,
        edge_slices=args.edge_slices,
    )


def held_out_file(path: Path) -> tuple[list[str], dict[str, Any]]:
    """The StudyInstanceUIDs of a held-out file, one per line, and its provenance.

    Each line is stripped and blank lines are skipped. A line holding whitespace
    inside it, a repeated study, or a file naming no study is refused by name.
    """
    raw = _read_bytes(Path(path), "held_out_file_unreadable")
    try:
        text = raw.decode("utf-8")
    except UnicodeError as error:
        raise ObjectBootstrapError("held_out_file_unreadable", str(path)) from error
    uids = [line.strip() for line in text.splitlines() if line.strip()]
    if not uids:
        raise ObjectBootstrapError("held_out_file_empty", str(path))
    for uid in uids:
        if any(character.isspace() for character in uid) or "\0" in uid:
            raise ObjectBootstrapError("held_out_file_line_invalid", uid)
    repeated = sorted(uid for uid, count in Counter(uids).items() if count > 1)
    if repeated:
        raise ObjectBootstrapError("held_out_file_duplicate", repeated[0])
    return uids, {
        "path": str(Path(path).resolve()),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "study_uid_count": len(uids),
    }


def run_grow(args: argparse.Namespace) -> dict[str, Any]:
    """Stream every inference record's candidates into one frozen-parent round."""
    output = Path(args.output)
    if output.exists() or output.is_symlink():
        raise ObjectBootstrapError("output_exists")
    held_out: list[str] = []
    held_out_source = None
    if args.held_out is not None:
        held_out, held_out_source = held_out_file(Path(args.held_out))
    directories = [Path(directory) for directory in args.inference]
    sources = [
        {"path": str(directory), "records": len(inference_record_paths(directory))}
        for directory in directories
    ]
    snapshot = load_memory_snapshot(args.parent)
    result = grow_identity_memory(
        snapshot,
        harvest_inference(directories),
        output,
        decisions_only=args.decisions_only,
        labels=None if args.labels is None else Path(args.labels),
        held_out=held_out,
    )
    return {
        "action": "grow",
        "inference": sources,
        "held_out_file": held_out_source,
        **result,
    }


_ACTIONS = {
    "export": run_export,
    "export-admissions": run_export_admissions,
    "admit": run_admit,
    "adapt": run_adapt,
    "sheets": run_sheets,
    "grow": run_grow,
}


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = _parser().parse_args(argv)
    try:
        result = _ACTIONS[args.action](args)
    except (
        ObjectBootstrapError,
        SquintBootstrapError,
        SquintMemoryError,
        IdentityGrowthError,
    ) as error:
        detail = getattr(error, "detail", None)
        raise SystemExit(
            error.code + ": " + str(detail) if detail else error.code
        ) from error
    print(json.dumps(_plain(result), ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
