#!/usr/bin/env python3
"""Human-called object-identity bootstrap sheets (pure categorization).

export: select object candidates from explicit filters and sorted case ids only,
render native raw pixels with the native teacher-support overlay for every view
that is actually available, build the review with the shared seed API, add
drawing-only evidence, write the final review bytes and hash those exact bytes.

admit: rehash the review file bytes, check the rendered sheets, then hand the
review, the human calls and the hash to the shared seed API. Nothing is
inferred, ranked or relabelled here.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from knee.diagnosis.squint_bootstrap import (
    CALLS_SCHEMA,
    SquintBootstrapError,
    adapt_recorded_calls,
    build_review,
    publish_seed_memory,
    validate_calls,
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
    admit = sub.add_parser("admit", help="admit explicit signed visual identity calls")
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
    published = publish_seed_memory(
        snapshot, review, calls, review_sha256, Path(args.output)
    )
    return {"action": "admit", "review_sha256": review_sha256, **published}


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


_ACTIONS = {"export": run_export, "admit": run_admit, "adapt": run_adapt}


def main(argv: list[str] | None = None) -> dict[str, Any]:
    args = _parser().parse_args(argv)
    try:
        result = _ACTIONS[args.action](args)
    except (ObjectBootstrapError, SquintBootstrapError, SquintMemoryError) as error:
        detail = getattr(error, "detail", None)
        raise SystemExit(
            error.code + ": " + str(detail) if detail else error.code
        ) from error
    print(json.dumps(_plain(result), ensure_ascii=False, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
