"""Tests for ``scripts/squint_object_bootstrap.py sheets``: one picture sheet per
identity-admission decision.

Only the study reader is replaced. It returns a small fake study shaped like
``read_study_squints`` output: series records with a squint ``stack`` (a tile
``bounds_rc`` grid) and a ``native_series`` volume. No competition data and no DICOM
are read. The fake sagittal grid is irregular (tile rows of 7, 9, 5 and 7 px, tile
columns of 6, 8, 7 and 6 px), so a window's pixel box is not a multiple of any one
tile size and a naive ``index * tile_size`` mapping fails these tests.
"""

from __future__ import annotations

import csv
import gc
import hashlib
import importlib.util
import json
import sys
import weakref
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

from knee.study.tables import LABELS, SERIES_COLUMNS, TEST_COLUMNS, TRAIN_COLUMNS

pytest.importorskip("matplotlib")

ROOT = Path(__file__).resolve().parents[1]


def _load():
    path = ROOT / "scripts" / "squint_object_bootstrap.py"
    spec = importlib.util.spec_from_file_location(
        "squint_object_bootstrap_sheets", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


MOD = _load()

SAG = "1.2.826.fixture.series.sagittal"
COR = "1.2.826.fixture.series.coronal"
BARE = "1.2.826.fixture.series.unstacked"
VIEW_SAG = {"orientation": "Sagittal", "fluid_sensitive": "0", "fat_suppression": "0"}
VIEW_COR = {"orientation": "Coronal", "fluid_sensitive": "1", "fat_suppression": "1"}
SAG_ROWS = (0, 7, 16, 21, 28)
SAG_COLS = (0, 6, 14, 21, 27)
COR_EDGES = (0, 7, 14)
# z 1..3, tile row 1, tile column 1 of the irregular sagittal grid: pixels rows 7..15, cols 6..13.
GOOD = [1, 4, 1, 2, 1, 2]
GOOD_RECT = (7, 16, 6, 14)


def grid(row_edges, col_edges):
    bounds = np.zeros((len(row_edges) - 1, len(col_edges) - 1, 4), dtype=np.int64)
    for r in range(len(row_edges) - 1):
        for c in range(len(col_edges) - 1):
            bounds[r, c] = (
                row_edges[r],
                row_edges[r + 1],
                col_edges[c],
                col_edges[c + 1],
            )
    return bounds


def series_record(uid, view, depth, row_edges, col_edges, tile):
    rows, cols = row_edges[-1], col_edges[-1]
    # A smooth grey ramp, so the sheet carries no colour of its own.
    ramp = np.add.outer(np.arange(rows), np.arange(cols)).astype(np.int16)
    volume = np.stack([ramp + 10 * z for z in range(depth)])
    stack = SimpleNamespace(
        code="present",
        bounds_rc=grid(row_edges, col_edges),
        tile_shape_rc=tile,
        tile_mm=10.0,
    )
    native = SimpleNamespace(
        volume=volume,
        slices=tuple(
            SimpleNamespace(path=Path(f"/raw/{uid}/{z:03d}.dcm")) for z in range(depth)
        ),
    )
    return {
        "series_uid": uid,
        "view": dict(view),
        "stack": stack,
        "native_series": native,
    }


def sag_record():
    return series_record(SAG, VIEW_SAG, 5, SAG_ROWS, SAG_COLS, (7, 7))


def cor_record():
    return series_record(COR, VIEW_COR, 3, COR_EDGES, COR_EDGES, (7, 7))


def bare_record():
    """A series the squint could not stack: no volume, and a named stack code."""
    stack = SimpleNamespace(
        code="no_stacked_volume",
        bounds_rc=np.empty((0, 0, 4), dtype=np.int64),
        tile_shape_rc=(0, 0),
        tile_mm=10.0,
    )
    native = SimpleNamespace(volume=None, slices=())
    return {
        "series_uid": BARE,
        "view": dict(VIEW_SAG),
        "stack": stack,
        "native_series": native,
    }


class Study(dict):
    """A study record that can be weakly referenced, so a test can see it released."""


class Reader:
    """A stand-in for the squint reader that keeps a log of how it was called."""

    def __init__(self, unreadable=(), malformed=()):
        self.calls = []
        self.refs = {}
        self.unreadable = set(unreadable)
        self.malformed = set(malformed)

    def __call__(self, root, study_uid, *, tile_mm, io_workers):
        gc.collect()
        alive = sorted(uid for uid, ref in self.refs.items() if ref() is not None)
        self.calls.append(
            {
                "root": root,
                "study": study_uid,
                "tile_mm": tile_mm,
                "io_workers": io_workers,
                "earlier_alive": alive,
            }
        )
        if study_uid in self.unreadable:
            raise ValueError("squint_study_uid_missing")
        if study_uid in self.malformed:
            return Study(schema="knee.squint-study/v1", study_uid=study_uid)
        study = Study(
            schema="knee.squint-study/v1",
            study_uid=study_uid,
            series=[sag_record(), cor_record(), bare_record()],
            work={"series_count": 3},
        )
        self.refs[study_uid] = weakref.ref(study)
        return study


def region(series_uid, window):
    return {"series_uid": series_uid, "window": list(window)}


def decision(
    cid, study, regions, *, state="admitted", subject="femur", identity="femur"
):
    return {
        "candidate_id": cid,
        "study_uid": study,
        "subject": subject,
        "state": state,
        "reason": "high-confidence joint identity; applicable anatomy supports it",
        "recognized_identity": identity,
        "views": [["Sagittal", "0", "0"]],
        "support": {"relation": "femur above tibia", "axes": ["z"]},
        "regions": regions,
        "source": {"round": 1, "parent": "parent-rev"},
    }


def document(decisions):
    return {
        "schema": MOD.DECISIONS_SCHEMA,
        "parent": {"revision": "parent-rev"},
        "decisions": decisions,
    }


def four_decisions():
    return [
        decision("c-b1", "study-b", [region(SAG, GOOD)]),
        decision(
            "c-a2", "study-a", [region(SAG, GOOD), region(COR, [0, 2, 0, 2, 0, 2])]
        ),
        decision("c-a1", "study-a", [region(COR, [0, 2, 0, 2, 0, 2])]),
        decision("c-r1", "study-a", [region(SAG, GOOD)], state="refused"),
    ]


def run(tmp_path, decisions, *, name="sheets", reader=None, **options):
    """Render the sheets for ``decisions`` into a new directory with an injected reader."""
    reader = reader if reader is not None else Reader()
    raw = json.dumps(document(decisions)).encode("utf-8")
    sha = hashlib.sha256(raw).hexdigest()
    out = tmp_path / name
    result = MOD.render_sheets(
        json.loads(raw),
        sha,
        tmp_path / "root",
        out,
        study_reader=reader,
        **options,
    )
    return SimpleNamespace(out=out, result=result, reader=reader, sha=sha)


def sheets_json(out):
    return json.loads((out / "sheets.json").read_text(encoding="utf-8"))


def code_of(fn, *args, **kwargs):
    with pytest.raises(MOD.ObjectBootstrapError) as info:
        fn(*args, **kwargs)
    return info.value.code


# --------------------------------------------------- tile window -> pixels


def test_window_pixel_rect_is_the_union_of_the_tiles_it_names():
    realistic = grid(
        (0, 7, 14, 21, 25), (0, 7, 14, 21, 26)
    )  # ragged last row and column
    # Tile rows 2-3 and columns 1-3: the last tiles are 4 and 5 px, not 7.
    assert MOD.window_pixel_rect(realistic, [0, 1, 2, 4, 1, 4], (25, 26)) == (
        14,
        25,
        7,
        26,
    )
    assert MOD.window_pixel_rect(realistic, [0, 1, 0, 2, 0, 2], (25, 26)) == (
        0,
        14,
        0,
        14,
    )
    irregular = grid(SAG_ROWS, SAG_COLS)
    assert MOD.window_pixel_rect(irregular, GOOD, (28, 27)) == GOOD_RECT
    # Not index * tile size: tile row 1 is 9 px tall here, not 7.
    assert GOOD_RECT != (7, 14, 7, 14)
    # Against the corner tiles' own bounds, as recorded on the stack.
    window = [0, 1, 1, 3, 0, 3]
    rect = MOD.window_pixel_rect(irregular, window, (28, 27))
    assert rect == (
        irregular[1, 0, 0],
        irregular[2, 2, 1],
        irregular[1, 0, 2],
        irregular[2, 2, 3],
    )


def test_window_pixel_rect_is_never_clipped_to_fit():
    realistic = grid((0, 7, 14, 21, 25), (0, 7, 14, 21, 26))
    # The grid has four tile rows: rows 3..4 and columns 4..4 are not on it.
    assert MOD.window_pixel_rect(realistic, [0, 1, 3, 5, 0, 1], (25, 26)) is None
    assert MOD.window_pixel_rect(realistic, [0, 1, 0, 1, 3, 5], (25, 26)) is None
    assert (
        MOD.window_pixel_rect(np.empty((0, 0, 4), dtype=np.int64), GOOD, (28, 27))
        is None
    )


def test_context_rect_adds_whole_tiles_and_stays_on_the_slice():
    assert MOD.context_pixel_rect((30, 44, 30, 44), (7, 7), (100, 100)) == (
        9,
        65,
        9,
        65,
    )
    assert MOD.context_pixel_rect((30, 44, 30, 44), (7, 7), (100, 100), 1) == (
        23,
        51,
        23,
        51,
    )
    # Near the border the view stops at the slice rather than reaching past it.
    assert MOD.context_pixel_rect((2, 9, 90, 99), (7, 7), (100, 100)) == (
        0,
        30,
        69,
        100,
    )


def test_slice_plan_is_half_open_and_the_middle_is_inside_the_window():
    assert MOD._slice_plan([3, 4, 0, 1, 0, 1], False) == [("middle", 3)]
    assert MOD._slice_plan([2, 6, 0, 1, 0, 1], False) == [("middle", 4)]
    assert MOD._slice_plan([2, 6, 0, 1, 0, 1], True) == [
        ("first", 2),
        ("middle", 4),
        ("last", 5),
    ]
    assert MOD._slice_plan([2, 4, 0, 1, 0, 1], True) == [
        ("first", 2),
        ("middle/last", 3),
    ]
    assert MOD._slice_plan([5, 6, 0, 1, 0, 1], True) == [("first/middle/last", 5)]
    for z0 in range(9):
        for z1 in range(z0 + 1, z0 + 10):
            plan = MOD._slice_plan([z0, z1, 0, 1, 0, 1], True)
            slices = [z for _, z in plan]
            assert (
                slices[0] == z0 and slices[-1] == z1 - 1
            )  # the last slice is z1-1, not z1
            assert z0 <= (z0 + z1) // 2 <= z1 - 1


# ------------------------------------------------------ the decisions file


def write_decisions(tmp_path, value, name="admission-decisions.json"):
    path = tmp_path / name
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def test_load_decisions_hashes_the_exact_bytes(tmp_path):
    path = write_decisions(tmp_path, document(four_decisions()))
    loaded, sha = MOD.load_decisions(path)
    assert sha == hashlib.sha256(path.read_bytes()).hexdigest()
    assert [d["candidate_id"] for d in loaded["decisions"]] == [
        "c-b1",
        "c-a2",
        "c-a1",
        "c-r1",
    ]


def test_load_decisions_refuses_by_name(tmp_path):
    good = document(four_decisions())

    def broken(**changes):
        value = json.loads(json.dumps(good))
        for key, new in changes.items():
            value[key] = new
        return write_decisions(
            tmp_path, value, f"d-{len(list(tmp_path.iterdir()))}.json"
        )

    assert (
        code_of(MOD.load_decisions, tmp_path / "absent.json") == "decisions_unreadable"
    )
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{not json", encoding="utf-8")
    assert code_of(MOD.load_decisions, bad_json) == "decisions_unparseable"
    assert (
        code_of(MOD.load_decisions, write_decisions(tmp_path, [], "l.json"))
        == "decisions_malformed"
    )
    assert (
        code_of(MOD.load_decisions, broken(schema="knee.other/v1"))
        == "decisions_schema_unrecognized"
    )
    assert code_of(MOD.load_decisions, broken(decisions={})) == "decisions_malformed"
    assert code_of(MOD.load_decisions, broken(decisions=["x"])) == "decision_malformed"

    def with_decision(**changes):
        decisions = json.loads(json.dumps(four_decisions()))
        decisions[1].update(changes)
        return broken(decisions=decisions)

    for field in ("candidate_id", "study_uid", "subject", "state"):
        assert (
            code_of(MOD.load_decisions, with_decision(**{field: ""}))
            == "decision_field_invalid"
        )
        assert (
            code_of(MOD.load_decisions, with_decision(**{field: 3}))
            == "decision_field_invalid"
        )
    assert (
        code_of(MOD.load_decisions, with_decision(regions="x"))
        == "decision_field_invalid"
    )
    # A repeated candidate_id is named with both places, not drawn twice.
    with pytest.raises(MOD.ObjectBootstrapError) as info:
        MOD.load_decisions(with_decision(candidate_id="c-a1"))
    assert info.value.code == "decision_candidate_id_duplicate"
    assert "decisions[1]" in info.value.detail and "decisions[2]" in info.value.detail


# ---------------------------------------------------------------- selection


def test_selection_by_state_in_stable_order_with_the_limit_named():
    doc = document(four_decisions())
    chosen = MOD.select_decisions(doc)
    assert [d["candidate_id"] for d in chosen["drawn"]] == ["c-a1", "c-a2", "c-b1"]
    assert chosen["states"] == ["admitted"] and chosen["matched"] == 3
    assert chosen["state_counts"] == {"admitted": 3, "refused": 1}
    assert chosen["undrawn_by_limit"] == [] and chosen["limit"] is None
    limited = MOD.select_decisions(doc, limit=2)
    assert [d["candidate_id"] for d in limited["drawn"]] == ["c-a1", "c-a2"]
    assert limited["undrawn_by_limit"] == ["c-b1"] and limited["matched"] == 3
    both = MOD.select_decisions(doc, states=["refused", "admitted"])
    assert [d["candidate_id"] for d in both["drawn"]] == [
        "c-a1",
        "c-a2",
        "c-r1",
        "c-b1",
    ]
    assert both["states"] == ["admitted", "refused"]
    assert [
        d["candidate_id"]
        for d in MOD.select_decisions(doc, states=["refused"])["drawn"]
    ] == ["c-r1"]


def test_selection_refusals_name_what_the_file_holds():
    doc = document(four_decisions())
    with pytest.raises(MOD.ObjectBootstrapError) as info:
        MOD.select_decisions(doc, states=["proposal"])
    assert info.value.code == "no_decisions_selected"
    assert "admitted=3" in info.value.detail and "refused=1" in info.value.detail
    assert code_of(MOD.select_decisions, doc, limit=0) == "limit_invalid"
    assert code_of(MOD.select_decisions, doc, limit=True) == "limit_invalid"
    assert (
        code_of(MOD.select_decisions, doc, states="admitted") == "filter_values_invalid"
    )
    assert code_of(MOD.select_decisions, doc, states=[""]) == "filter_values_invalid"


# --------------------------------------------- rows: the facts as plain data


def read_study(reader=None):
    study = (reader or Reader())(ROOT, "study-a", tile_mm=10.0, io_workers=1)
    return study, MOD._series_index(study)


def test_rows_record_view_slice_rectangle_and_state_as_data():
    study, by_uid = read_study()
    (row,) = MOD._region_rows(region(SAG, GOOD), by_uid, None, False)
    assert row["image_state"] == "read" and row["image_reason"] is None
    assert row["view"] == VIEW_SAG and row["view_label"] == "Sagittal | fluid=0 | FS=0"
    assert (row["slice"], row["slice_role"]) == (2, "middle")
    assert row["window"] == GOOD
    assert row["series_depth"] == 5 and row["image_shape"] == [28, 27]
    assert row["native_rect_rc"] == list(GOOD_RECT)
    assert row["native_rect_rc"] == list(study["series"][0]["stack"].bounds_rc[1, 1])
    assert row["context_rect_rc"] == [0, 28, 0, 27]
    assert row["image_source_path"].endswith(f"{SAG}/002.dcm")
    pixels = row["pixels"]
    assert pixels.dtype == np.float32 and pixels.shape == (28, 27)
    # A copy of the drawn slice: the study's volume is not kept alive by the sheet.
    assert not np.shares_memory(pixels, study["series"][0]["native_series"].volume)
    receipt = MOD._row_receipt(row)
    assert "pixels" not in receipt
    assert json.loads(json.dumps(receipt)) == receipt


def test_rows_for_a_wider_window_follow_the_corner_tiles():
    study, by_uid = read_study()
    bounds = study["series"][0]["stack"].bounds_rc
    (row,) = MOD._region_rows(region(SAG, [1, 4, 1, 3, 0, 3]), by_uid, None, False)
    assert row["native_rect_rc"] == [
        int(bounds[1, 0, 0]),
        int(bounds[2, 2, 1]),
        int(bounds[1, 0, 2]),
        int(bounds[2, 2, 3]),
    ]
    assert row["native_rect_rc"] == [7, 21, 0, 21]


def test_missing_data_is_named_never_skipped():
    _, by_uid = read_study()
    cases = [
        (region(SAG, GOOD), "read"),
        (region("no-such-series", GOOD), "series_missing"),
        (region(SAG, [1, 4, 3, 5, 0, 1]), "window_outside_tile_grid"),
        (region(SAG, [7, 9, 0, 1, 0, 1]), "slice_outside_series"),
        ({"series_uid": SAG}, "window_unreadable"),
        ({"series_uid": SAG, "window": [3, 3, 0, 1, 0, 1]}, "window_unreadable"),
        ({"window": GOOD}, "region_series_unrecorded"),
        ({"series_uid": 5, "window": GOOD}, "region_series_unrecorded"),
        ("not a region", "region_malformed"),
        (region(BARE, GOOD), "native_volume_or_squint_unavailable"),
    ]
    for item, state in cases:
        rows = MOD._region_rows(item, by_uid, None, False)
        assert [r["image_state"] for r in rows] == [state], item
        if state != "read":
            assert rows[0]["pixels"] is None and rows[0]["native_rect_rc"] is None
    # The middle slice is inside the series although the window runs past its end: drawn, and said.
    (late,) = MOD._region_rows(region(SAG, [2, 7, 0, 1, 0, 1]), by_uid, None, False)
    assert late["image_state"] == "read" and late["slice"] == 4
    assert late["notes"] == ["window_z_beyond_series_depth:5"]
    # A study that could not be read is the reason, whatever the regions say.
    (failed,) = MOD._region_rows(region(SAG, GOOD), {}, "ValueError: gone", False)
    assert failed["image_state"] == "study_read_failed"
    assert failed["image_reason"] == "ValueError: gone"


def test_edge_slices_add_the_first_and_last_slice_of_the_window():
    _, by_uid = read_study()
    rows = MOD._region_rows(region(SAG, GOOD), by_uid, None, True)
    assert [(r["slice"], r["slice_role"]) for r in rows] == [
        (1, "first"),
        (2, "middle"),
        (3, "last"),
    ]
    assert {tuple(r["native_rect_rc"]) for r in rows} == {GOOD_RECT}
    # The last slice of [z0, z1) is z1-1: a window ending at the series' depth is still inside it.
    rows = MOD._region_rows(region(SAG, [3, 5, 0, 1, 0, 1]), by_uid, None, True)
    assert [(r["slice"], r["image_state"]) for r in rows] == [(3, "read"), (4, "read")]
    rows = MOD._region_rows(region(SAG, [3, 7, 0, 1, 0, 1]), by_uid, None, True)
    assert [(r["slice"], r["image_state"]) for r in rows] == [
        (3, "read"),
        (5, "slice_outside_series"),
        (6, "slice_outside_series"),
    ]


# ------------------------------------------------------------------ figure


def drawn(fig):
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    canvas = FigureCanvasAgg(fig)
    canvas.draw()
    return np.asarray(canvas.buffer_rgba())


def test_the_window_box_is_drawn_on_the_pixels_its_tiles_cover():
    _, by_uid = read_study()
    rows = MOD._region_rows(region(SAG, GOOD), by_uid, None, False)
    fig = MOD._decision_figure(decision("c", "study-a", []), rows, tile_mm=10.0)
    image = drawn(fig)
    height = image.shape[0]
    # The sheet carries no colour of its own, so the yellow box is the only coloured thing.
    yellow = (image[..., 0].astype(int) - image[..., 2].astype(int)) > 64
    assert len(fig.axes) == 2

    def edges(ax, rect):
        r0, r1, c0, c1 = rect
        (xa, ya), (xb, yb) = ax.transData.transform(
            [(c0 - 0.5, r0 - 0.5), (c1 - 0.5, r1 - 0.5)]
        )
        return (
            height - ya,
            height - yb,
            xa,
            xb,
        )  # top, bottom, left, right in buffer pixels

    for ax in fig.axes:
        extent = ax.get_window_extent()
        inside = np.zeros_like(yellow)
        inside[
            int(height - extent.y1) : int(height - extent.y0) + 1,
            int(extent.x0) : int(extent.x1) + 1,
        ] = True
        ys, xs = np.nonzero(yellow & inside)
        assert ys.size, "no window box on the axes"
        found = (ys.min(), ys.max(), xs.min(), xs.max())
        for got, want in zip(found, edges(ax, GOOD_RECT), strict=True):
            assert abs(got - want) <= 2.5, (found, edges(ax, GOOD_RECT))
        # The index * tile size box (rows 7..13, cols 7..13) shares the top and right edges
        # with the true one, but its bottom and left edges are a pixel or two elsewhere,
        # which is more than 5 buffer pixels at this scale.
        naive = edges(ax, (7, 14, 7, 14))
        assert abs(found[1] - naive[1]) > 5 and abs(found[2] - naive[2]) > 5


def test_the_sheet_names_the_decision_and_is_not_an_uncalled_proposal():
    item = decision(
        "c-x", "study-a", [], subject="femur", identity="tibia", state="admitted"
    )
    fig = MOD._decision_figure(item, [], tile_mm=10.0)
    text = " ".join(t.get_text() for t in fig.texts)
    assert "ADMISSION DECISION - inspect: admitted" in text
    assert "UNCALLED PROPOSAL" not in text
    assert "subject: femur" in text and "recognized identity: tibia" in text
    assert "study: study-a" in text and "candidate: c-x" in text
    assert "views: " in text and "location support: " in text
    assert "reason: high-confidence joint identity" in text and "source: " in text
    assert "not an outline of tissue" in text and "no native support is drawn" in text
    assert "No region is recorded for this decision" in text
    # A decision that records no identity says so, and does not invent one.
    bare = {k: v for k, v in item.items() if k != "recognized_identity"}
    text = " ".join(
        t.get_text() for t in MOD._decision_figure(bare, [], tile_mm=10.0).texts
    )
    assert "recognized identity: unrecorded" in text
    none = dict(item, recognized_identity=None)
    text = " ".join(
        t.get_text() for t in MOD._decision_figure(none, [], tile_mm=10.0).texts
    )
    assert "recognized identity: null" in text


def test_a_list_of_dicts_as_support_wraps_between_tokens_not_through_words():
    # The shape the growth writer records: one dict per location check it passed.
    support = [
        {
            "establishes": "location_only",
            "rule_id": "femur_above_tibia",
            "axis": "z",
            "result": "supported_above",
            "candidate_interval": [10.0, 20.0],
            "target_interval": [0.0, 8.0],
        }
    ]
    item = dict(decision("c-s", "study-a", []), support=support)
    text = " ".join(
        t.get_text() for t in MOD._decision_figure(item, [], tile_mm=10.0).texts
    )
    # Wrapping only inserts a break at a space, so the whole value reads back unbroken.
    assert "location support: " + MOD._shown(support) in text
    assert "supported_above" in text and "femur_above_tibia" in text
    # The index keeps the exact compact form.
    run_index = json.dumps(support, sort_keys=True, separators=(",", ":"))
    assert MOD._verbatim(support) == run_index


def test_long_fields_are_wrapped_and_truncated_on_the_sheet_not_in_the_index(tmp_path):
    long_reason = "joint recall agrees " * 40
    item = dict(decision("c-long", "study-a", [region(SAG, GOOD)]), reason=long_reason)
    run_ = run(tmp_path, [item])
    index = (run_.out / "index.md").read_text(encoding="utf-8")
    assert (
        json.dumps(long_reason) in index
    )  # verbatim in the index, whatever the sheet shows
    assert sheets_json(run_.out)["sheets"][0]["decision"]["reason"] == long_reason
    pieces = MOD._wrapped("word " * 200, lines=2, width=50)
    assert (
        len(pieces) == 2
        and pieces[-1].endswith("...")
        and all(len(p) <= 50 for p in pieces)
    )


def test_markdown_code_spans_survive_backticks():
    assert MOD._md_code("plain") == "`plain`"
    assert MOD._md_code("a`b") == "``a`b``"
    # Text that begins or ends with a backtick is padded so the fence does not merge with it.
    assert MOD._md_code("`x") == "`` `x ``"
    assert MOD._md_code("a``b`") == "``` a``b` ```"


# ----------------------------------------------------------- the whole run


def test_each_study_is_read_once_in_grouped_order_and_released(tmp_path):
    decisions = four_decisions() + [
        decision("c-c1", "study-c", [region(SAG, GOOD)]),
        decision("c-a3", "study-a", [region(SAG, GOOD)]),
    ]
    run_ = run(tmp_path, decisions, io_workers=3, tile_mm=10)
    calls = run_.reader.calls
    # study-a holds four admitted decisions and is still read exactly once; order is sorted.
    assert [c["study"] for c in calls] == ["study-a", "study-b", "study-c"]
    assert all(c["earlier_alive"] == [] for c in calls), (
        "an earlier study was still held"
    )
    assert all(c["io_workers"] == 3 and c["tile_mm"] == 10.0 for c in calls)
    assert all(c["root"] == tmp_path / "root" for c in calls)
    assert run_.result["drawn"] == 5 and run_.result["studies"] == 3
    assert run_.result["matched"] == 5
    assert [s["candidate_id"] for s in sheets_json(run_.out)["sheets"]] == [
        "c-a1",
        "c-a2",
        "c-a3",
        "c-b1",
        "c-c1",
    ]


def test_sheets_json_and_index_pin_every_png(tmp_path):
    run_ = run(tmp_path, four_decisions())
    out = run_.out
    record = sheets_json(out)
    assert record["schema"] == MOD.SHEETS_SCHEMA
    assert record["decisions"]["sha256"] == run_.sha
    assert record["decisions"]["parent"] == {"revision": "parent-rev"}
    assert record["decisions"]["schema"] == MOD.DECISIONS_SCHEMA
    assert record["tile_mm"] == 10.0 and record["edge_slices"] is False
    assert record["selection"]["states"] == ["admitted"]
    assert record["selection"]["state_counts"] == {"admitted": 3, "refused": 1}
    assert record["selection"]["ordering"] == "study_uid,candidate_id"
    files = sorted(p.name for p in out.glob("*.png"))
    assert files == sorted(s["file"] for s in record["sheets"]) and len(files) == 3
    for sheet in record["sheets"]:
        data = (out / sheet["file"]).read_bytes()
        assert data[:8] == bytes.fromhex("89504e470d0a1a0a")
        assert hashlib.sha256(data).hexdigest() == sheet["sha256"]
        assert len(data) == sheet["bytes"]
        # Every decision field travels with its sheet, verbatim.
        original = next(
            d for d in four_decisions() if d["candidate_id"] == sheet["candidate_id"]
        )
        assert sheet["decision"] == original
        assert sheet["study_read"] == {
            "status": "read",
            "error": None,
            "work": {"series_count": 3},
        }
    sheets_bytes = (out / "sheets.json").read_bytes()
    assert run_.result["sheets_json_sha256"] == hashlib.sha256(sheets_bytes).hexdigest()
    index = (out / "index.md").read_text(encoding="utf-8")
    assert run_.result["sheets_json_sha256"] in index and run_.sha in index
    for sheet in record["sheets"]:
        assert sheet["candidate_id"] in index and sheet["file"] in index
        assert sheet["sha256"] in index
    assert "c-r1" not in index  # a refused decision is not drawn unless asked for
    assert "admitted=3 (requested)" in index and "refused=1" in index
    assert "reason" in index and "femur above tibia" in index and '"round":1' in index
    # The pixel rectangle is data, not only a drawing.
    panel = record["sheets"][0]["panels"][0]
    assert (
        panel["image_state"] == "read"
        and panel["view_label"] == "Coronal | fluid=1 | FS=1"
    )
    assert panel["native_rect_rc"] == [0, 14, 0, 14] and panel["slice"] == 1
    assert "pixels" not in panel
    assert not (out / "review.json").exists() and not (out / "calls.json").exists()


def test_the_state_filter_draws_what_it_is_asked_for(tmp_path):
    run_ = run(tmp_path, four_decisions(), states=["refused"])
    assert [s["candidate_id"] for s in sheets_json(run_.out)["sheets"]] == ["c-r1"]
    index = (run_.out / "index.md").read_text(encoding="utf-8")
    assert "admitted=3" in index and "refused=1 (requested)" in index


def test_missing_data_reaches_the_sheet_the_index_and_sheets_json(tmp_path):
    regions = [
        region(SAG, GOOD),
        region("no-such-series", GOOD),
        region(SAG, [1, 4, 3, 5, 0, 1]),
        region(SAG, [7, 9, 0, 1, 0, 1]),
        {"series_uid": SAG},
        {"window": GOOD},
        "not a region",
        region(BARE, GOOD),
        region(SAG, [2, 7, 0, 1, 0, 1]),
    ]
    run_ = run(tmp_path, [decision("c-many", "study-a", regions)])
    panels = sheets_json(run_.out)["sheets"][0]["panels"]
    assert [p["image_state"] for p in panels] == [
        "read",
        "series_missing",
        "window_outside_tile_grid",
        "slice_outside_series",
        "window_unreadable",
        "region_series_unrecorded",
        "region_malformed",
        "native_volume_or_squint_unavailable",
        "read",
    ]
    assert panels[-1]["notes"] == ["window_z_beyond_series_depth:5"]
    expected = Counter(p["image_state"] for p in panels if p["image_state"] != "read")
    assert run_.result["panels_not_drawn"] == dict(sorted(expected.items()))
    assert run_.result["panels"] == 9
    index = (run_.out / "index.md").read_text(encoding="utf-8")
    for state in expected:
        assert f"`{state}`" in index, state
    assert "NOT DRAWN" in index and "window_z_beyond_series_depth:5" in index
    assert "panels not drawn: " in index and "series_missing=1" in index
    # The sheet is still drawn, with every region on it.
    assert (run_.out / sheets_json(run_.out)["sheets"][0]["file"]).stat().st_size > 0


def test_unreadable_and_malformed_studies_are_named_and_still_get_their_sheets(
    tmp_path,
):
    decisions = [
        decision("c-1", "study-a", [region(SAG, GOOD)]),
        decision(
            "c-2", "study-b", [region(SAG, GOOD), region(COR, [0, 2, 0, 2, 0, 2])]
        ),
        decision("c-3", "study-c", [region(SAG, GOOD)]),
    ]
    reader = Reader(unreadable={"study-a"}, malformed={"study-b"})
    run_ = run(tmp_path, decisions, reader=reader)
    assert run_.result["studies_not_read"] == ["study-a", "study-b"]
    sheets = {s["candidate_id"]: s for s in sheets_json(run_.out)["sheets"]}
    assert (
        sheets["c-1"]["study_read"]["error"] == "ValueError: squint_study_uid_missing"
    )
    assert sheets["c-2"]["study_read"]["error"] == "TypeError: study_series_malformed"
    assert sheets["c-3"]["study_read"]["status"] == "read"
    for key in ("c-1", "c-2"):
        assert sheets[key]["study_read"]["status"] == "failed"
        assert {p["image_state"] for p in sheets[key]["panels"]} == {
            "study_read_failed"
        }
        assert (run_.out / sheets[key]["file"]).is_file()
    assert (
        sheets["c-1"]["panels"][0]["image_reason"]
        == "ValueError: squint_study_uid_missing"
    )
    index = (run_.out / "index.md").read_text(encoding="utf-8")
    assert "study NOT READ" in index and "squint_study_uid_missing" in index
    assert (
        "studies not read: " in index and "`study-a`" in index and "`study-b`" in index
    )
    assert run_.result["panels_not_drawn"] == {"study_read_failed": 3}
    # A failed study does not stop the next one.
    assert [c["study"] for c in reader.calls] == ["study-a", "study-b", "study-c"]


def test_the_limit_leaves_a_named_remainder(tmp_path):
    run_ = run(tmp_path, four_decisions(), limit=2)
    record = sheets_json(run_.out)
    assert [s["candidate_id"] for s in record["sheets"]] == ["c-a1", "c-a2"]
    assert record["selection"]["undrawn_by_limit"] == ["c-b1"]
    assert record["selection"]["matched"] == 3 and record["selection"]["limit"] == 2
    assert run_.result["undrawn_by_limit"] == 1 and run_.result["matched"] == 3
    assert len(list(run_.out.glob("*.png"))) == 2
    index = (run_.out / "index.md").read_text(encoding="utf-8")
    assert "left undrawn by the limit: `c-b1`" in index
    assert "matched 3, drawn 2" in index and "limit 2" in index
    assert [c["study"] for c in run_.reader.calls] == [
        "study-a"
    ]  # study-b is never read
    unlimited = run(tmp_path, four_decisions(), name="all")
    assert "left undrawn by the limit: none" in (unlimited.out / "index.md").read_text(
        encoding="utf-8"
    )


def test_edge_slices_draw_the_first_and_last_slice_too(tmp_path):
    run_ = run(
        tmp_path, [decision("c-1", "study-a", [region(SAG, GOOD)])], edge_slices=True
    )
    record = sheets_json(run_.out)
    assert record["edge_slices"] is True
    assert [(p["slice"], p["slice_role"]) for p in record["sheets"][0]["panels"]] == [
        (1, "first"),
        (2, "middle"),
        (3, "last"),
    ]
    assert "first, middle and last" in (run_.out / "index.md").read_text(
        encoding="utf-8"
    )
    plain = run(
        tmp_path, [decision("c-1", "study-a", [region(SAG, GOOD)])], name="plain"
    )
    assert len(sheets_json(plain.out)["sheets"][0]["panels"]) == 1


def test_an_existing_output_is_refused_before_anything_is_read(tmp_path):
    first = run(tmp_path, four_decisions())
    before = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first.out.iterdir()
    }
    again = Reader()
    with pytest.raises(MOD.ObjectBootstrapError) as info:
        run(tmp_path, four_decisions(), reader=again)
    assert info.value.code == "sheets_output_exists"
    assert again.calls == []
    after = {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first.out.iterdir()
    }
    assert after == before
    # A file, or an empty directory, at the output path is refused just the same.
    (tmp_path / "a-file").write_text("x", encoding="utf-8")
    (tmp_path / "a-dir").mkdir()
    for name in ("a-file", "a-dir"):
        assert (
            code_of(run, tmp_path, four_decisions(), name=name, reader=again)
            == "sheets_output_exists"
        )
    assert (
        again.calls == [] and (tmp_path / "a-file").read_text(encoding="utf-8") == "x"
    )


def test_invalid_options_are_refused_before_an_output_is_made(tmp_path):
    for options, code in (
        ({"tile_mm": 0}, "tile_mm_invalid"),
        ({"tile_mm": float("nan")}, "tile_mm_invalid"),
        ({"tile_mm": True}, "tile_mm_invalid"),
        ({"io_workers": 0}, "io_workers_invalid"),
        ({"limit": 0}, "limit_invalid"),
        ({"states": ["nothing"]}, "no_decisions_selected"),
    ):
        assert code_of(run, tmp_path, four_decisions(), name="never", **options) == code
        assert not (tmp_path / "never").exists()


# ------------------------------------- the production reader, on real DICOM


def write_dicom(path, study_uid, series_uid, pixels, z_mm):
    meta = FileMetaDataset()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.MediaStorageSOPClassUID = generate_uid()
    meta.MediaStorageSOPInstanceUID = generate_uid()
    meta.ImplementationClassUID = generate_uid()
    dataset = FileDataset(str(path), {}, file_meta=meta, preamble=b"\0" * 128)
    dataset.SOPClassUID = meta.MediaStorageSOPClassUID
    dataset.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    dataset.StudyInstanceUID = study_uid
    dataset.SeriesInstanceUID = series_uid
    dataset.Modality = "MR"
    dataset.Rows, dataset.Columns = pixels.shape
    dataset.SamplesPerPixel = 1
    dataset.PhotometricInterpretation = "MONOCHROME2"
    dataset.BitsAllocated = 16
    dataset.BitsStored = 16
    dataset.HighBit = 15
    dataset.PixelRepresentation = 0
    dataset.ImagePositionPatient = [0.0, 0.0, float(z_mm)]
    dataset.ImageOrientationPatient = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    dataset.PixelSpacing = [2.5, 2.5]
    dataset.PixelData = np.asarray(pixels, dtype="<u2").tobytes()
    dataset.save_as(path, enforce_file_format=True, little_endian=True)


def write_study(root, split_folder, study_uid, series_uid, depth, shape):
    """Files are named in reverse z order, so file-name order is not stack order."""
    directory = root / split_folder / study_uid / series_uid
    directory.mkdir(parents=True)
    for z in range(depth):
        ramp = np.arange(shape[0] * shape[1]).reshape(shape) + 100 * z
        name = f"{depth - 1 - z:03d}.dcm"
        write_dicom(directory / name, study_uid, series_uid, ramp % 4000, 3.0 * z)


def write_tables(root, train, test):
    def write(name, header, records):
        with (root / name).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(header)
            writer.writerows(records)

    write("train.csv", TRAIN_COLUMNS, [(train[0], "", *("" for _ in LABELS))])
    write(
        "train_series.csv", SERIES_COLUMNS, [(train[0], train[1], "0", "0", "Sagittal")]
    )
    write("test.csv", TEST_COLUMNS, [(test[0],)])
    write("test_series.csv", SERIES_COLUMNS, [(test[0], test[1], "1", "1", "Coronal")])


def test_the_production_reader_finds_both_splits_and_the_box_follows_the_real_bounds(
    tmp_path,
):
    from knee.diagnosis.squint_profiles import read_study_squints

    root = tmp_path / "raw"
    root.mkdir()
    train_uid, train_series, test_uid, test_series, unknown = (
        generate_uid() for _ in range(5)
    )
    write_study(root, "train_series", train_uid, train_series, 3, (42, 61))
    write_study(root, "test_series", test_uid, test_series, 3, (42, 61))
    write_tables(root, (train_uid, train_series), (test_uid, test_series))
    # The window is the last two tile rows and columns of the real grid, so it ends in
    # the ragged tiles: the squint tiles a 42 x 61 slice into whole tiles of 4 pixels.
    stack = read_study_squints(root, train_uid, io_workers=1)["series"][0]["stack"]
    bounds = stack.bounds_rc
    tile_rows, tile_cols = bounds.shape[:2]
    window = [0, 3, tile_rows - 2, tile_rows, tile_cols - 2, tile_cols]
    want = [
        int(bounds[tile_rows - 2, tile_cols - 2, 0]),
        int(bounds[tile_rows - 1, tile_cols - 1, 1]),
        int(bounds[tile_rows - 2, tile_cols - 2, 2]),
        int(bounds[tile_rows - 1, tile_cols - 1, 3]),
    ]
    assert (
        want[1] == 42 and want[3] == 61
    )  # the ragged last tiles end at the image border
    decisions = [
        decision("a-train", train_uid, [region(train_series, window)]),
        decision("b-test", test_uid, [region(test_series, window)]),
        decision("c-nowhere", unknown, [region(train_series, window)]),
    ]
    path = write_decisions(tmp_path, document(decisions))
    out = tmp_path / "out"
    MOD.main(
        ["sheets", "--root", str(root), "--decisions", str(path), "--output", str(out)]
        + ["--io-workers", "2", "--edge-slices"]
    )
    sheets = {s["candidate_id"]: s for s in sheets_json(out)["sheets"]}
    for key, folder, series, label in (
        ("a-train", "train_series", train_series, "Sagittal | fluid=0 | FS=0"),
        ("b-test", "test_series", test_series, "Coronal | fluid=1 | FS=1"),
    ):
        panels = sheets[key]["panels"]
        assert [(p["slice"], p["slice_role"]) for p in panels] == [
            (0, "first"),
            (1, "middle"),
            (2, "last"),
        ]
        for panel in panels:
            assert panel["image_state"] == "read" and panel["view_label"] == label
            assert panel["native_rect_rc"] == want
            assert panel["image_shape"] == [42, 61] and panel["series_depth"] == 3
        # The slice drawn is the file of that study, found under its own split's folder.
        # The files were written in reverse z order, so stack slice 0 is file 002.dcm:
        # the recorded path follows the stack, not the file names.
        assert [Path(p["image_source_path"]).name for p in panels] == [
            "002.dcm",
            "001.dcm",
            "000.dcm",
        ]
        directory = f"/{folder}/{sheets[key]['study_uid']}/{series}/"
        assert all(directory in p["image_source_path"] for p in panels)
        assert sheets[key]["study_read"]["status"] == "read"
        assert sheets[key]["study_read"]["work"]["series_count"] == 1
    # A study that is in neither table is the production reader's own refusal, named.
    panels = sheets["c-nowhere"]["panels"]
    assert {p["image_state"] for p in panels} == {"study_read_failed"}
    assert {p["image_reason"] for p in panels} == {
        "ValueError: squint_study_uid_missing"
    }
    assert sheets["c-nowhere"]["study_read"]["status"] == "failed"
    assert len(list(out.glob("*.png"))) == 3


# ---------------------------------------------------------------------- CLI


def test_parser_defaults():
    args = MOD._parser().parse_args(
        ["sheets", "--root", "r", "--decisions", "d.json", "--output", "o"]
    )
    assert args.action == "sheets"
    assert args.states is None and args.limit is None
    assert args.tile_mm == 10.0 and args.io_workers == 8 and args.edge_slices is False
    args = MOD._parser().parse_args(
        [
            "sheets",
            "--root",
            "r",
            "--decisions",
            "d",
            "--output",
            "o",
            "--state",
            "admitted",
        ]
        + [
            "--state",
            "refused",
            "--limit",
            "4",
            "--tile-mm",
            "2.5",
            "--io-workers",
            "2",
        ]
        + ["--edge-slices"]
    )
    assert args.states == ["admitted", "refused"] and args.limit == 4
    assert args.tile_mm == 2.5 and args.io_workers == 2 and args.edge_slices is True


def test_the_cli_calls_the_production_squint_reader_and_prints_a_summary(
    tmp_path, monkeypatch, capsys
):
    from knee.diagnosis import squint_profiles

    reader = Reader()
    monkeypatch.setattr(
        squint_profiles,
        "read_study_squints",
        lambda root, study_uid, *, io_workers, tile_mm: reader(
            root, study_uid, tile_mm=tile_mm, io_workers=io_workers
        ),
    )
    path = write_decisions(tmp_path, document(four_decisions()))
    out = tmp_path / "from-cli"
    (tmp_path / "root").mkdir()
    result = MOD.main(
        ["sheets", "--root", str(tmp_path / "root"), "--decisions", str(path)]
        + ["--output", str(out), "--limit", "2", "--io-workers", "3"]
    )
    captured = capsys.readouterr()
    assert json.loads(captured.out) == MOD._plain(result)
    assert "sheets: study 1/1 study-a: 2 decision(s)" in captured.err
    assert reader.calls == [
        {
            "root": tmp_path / "root",
            "study": "study-a",
            "tile_mm": 10.0,
            "io_workers": 3,
            "earlier_alive": [],
        }
    ]
    record = sheets_json(out)
    assert record["decisions"]["path"] == str(path)
    assert (
        record["decisions"]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    )
    assert result["drawn"] == 2 and result["undrawn_by_limit"] == 1


def test_cli_refusals_exit_with_the_code_and_make_nothing(tmp_path, monkeypatch):
    from knee.diagnosis import squint_profiles

    def forbidden(*args, **kwargs):
        raise AssertionError("no study may be read")

    monkeypatch.setattr(squint_profiles, "read_study_squints", forbidden)
    wrong = write_decisions(
        tmp_path, dict(document(four_decisions()), schema="knee.x/v1")
    )
    duplicate = write_decisions(
        tmp_path,
        document([decision("same", "s", []), decision("same", "s", [])]),
        "dup.json",
    )
    good = write_decisions(tmp_path, document(four_decisions()), "good.json")
    absent_root = tmp_path / "no-such-root"
    for decisions, root, prefix in (
        (wrong, tmp_path, "decisions_schema_unrecognized"),
        (duplicate, tmp_path, "decision_candidate_id_duplicate"),
        # A mistyped root is refused once, not once per study.
        (good, absent_root, "root_not_a_directory"),
        (good, wrong, "root_not_a_directory"),
    ):
        out = tmp_path / "refused-out"
        with pytest.raises(SystemExit) as info:
            MOD.main(
                ["sheets", "--root", str(root), "--decisions", str(decisions)]
                + ["--output", str(out)]
            )
        assert str(info.value.code).startswith(prefix)
        assert not out.exists()
    assert not absent_root.exists()
