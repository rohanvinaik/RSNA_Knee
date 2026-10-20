import copy
import importlib.util
import inspect
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

SRC = Path(__file__).resolve().parents[1] / "scripts" / "run_interiors.py"
spec = importlib.util.spec_from_file_location("run_interiors_gastroc_window", SRC)
assert spec is not None and spec.loader is not None
ri = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = ri
spec.loader.exec_module(ri)

PlaneFrame = ri.PlaneFrame
NAMES = ri.GASTROC_HEADS
N, DEPTH, Z0, AXN = 64, 5, 2, 16
H0, H1 = (10, 30), (14, 36)
_th = np.radians(20.0)
SCEN = {
    "sagittal": ([0, 1, 0, 0, 0, -1], (1.0, 1.0), "sagittal"),
    "coronal": ([1, 0, 0, 0, 0, -1], (0.8, 1.5), "coronal"),
    "oblique": (
        [0, np.cos(_th), np.sin(_th), 0, np.sin(_th), -np.cos(_th)],
        (1.2, 0.9),
        "sagittal",
    ),
}


def frame_factory(orient, spacing):
    o = np.asarray(orient, float)
    nrm = np.cross(o[3:], o[:3])
    base = np.array([20.0, 20.0, 80.0])
    return lambda z: PlaneFrame.from_dicom(base + 3.0 * z * nrm, orient, spacing)


def make_axial(name, lps, pixels=((4, 5),), uid="ax", frame_uid=None):
    objects = np.zeros((AXN, AXN), dtype=np.int32)
    for r, c in pixels:
        objects[r, c] = ri.OBJECT_CODES[name]
    r0, c0 = pixels[0]
    origin = (
        np.asarray(lps, float) - r0 * np.array([0, 1.0, 0]) - c0 * np.array([1.0, 0, 0])
    )
    frame = PlaneFrame.from_dicom(origin, [1, 0, 0, 0, 1, 0], (1.0, 1.0))
    record = {
        "series_uid": uid,
        "view": ("axial", "1", "1"),
        "slice_index": 0,
        "assignments": {"codes": {name: "identified"}, name: 1},
    }
    return SimpleNamespace(
        series=SimpleNamespace(
            row=SimpleNamespace(series_uid=uid if frame_uid is None else frame_uid),
            volume=np.zeros((1, AXN, AXN)),
        ),
        record=record,
        arrays={"a1_objects": objects},
        assignment=SimpleNamespace(
            peaks=[SimpleNamespace(territory=1, peak_rc=(r0, c0))]
        ),
        frame=frame,
    )


def make_target(view, nan_rc=None):
    rng = np.random.default_rng(3)
    vol = rng.normal(100, 5, (DEPTH, N, N))
    if nan_rc is not None:
        vol[Z0, nan_rc[0], nan_rc[1]] = np.nan
    series = SimpleNamespace(
        volume=vol,
        slice_thickness_mm=[3.0] * DEPTH,
        row=SimpleNamespace(series_uid="sag", fluid_sensitive="1", fat_suppression="1"),
    )
    return SimpleNamespace(
        series=series,
        arrays={"a1_objects": np.zeros((N, N), np.int32)},
        record={
            "series_uid": "sag",
            "view": (view, "1", "1"),
            "slice_index": 1,
            "background_split": 10.0,
            "observations": [],
            "assignments": {"codes": {}},
        },
        assignment=None,
        frame=None,
    )


def fake_gradient(st):
    def fn(raw, avail, spacing, groups):
        st.calls["gradient"].append(
            {"raw": raw.shape, "available": np.asarray(avail).shape}
        )
        codes = {n: i + 1 for i, n in enumerate(groups)}
        shape = raw.shape
        labels = np.zeros(shape, np.int32)
        for n, m in groups.items():
            if n.startswith("gastrocnemius_head_location_"):
                labels[m] = codes[n]
        return SimpleNamespace(
            gradient_magnitude=np.zeros(shape),
            gradient_u16=np.zeros(shape, np.uint16),
            gradient_valid=np.asarray(avail, bool).copy(),
            marker_ids=labels.copy(),
            conflicts=np.zeros(shape, bool),
            labels=labels,
            unknown=labels == 0,
            marker_codes=codes,
            marker_counts={n: int(m.sum()) for n, m in groups.items()},
            gradient_facts={},
        )

    return fn


@pytest.fixture
def env(monkeypatch):
    st = SimpleNamespace(
        frame=None,
        fake=False,
        calls={"scoped": [], "field": [], "gradient": [], "margin": []},
    )
    cache = {}

    def boom(*a, **k):
        raise AssertionError("full-frame path called")

    for n in ("lens_of", "field_of", "interior_regions"):
        monkeypatch.setattr(ri, n, boom)

    def scoped(series, index, plane, spacing, split, window, reader=None):
        r0, r1, c0, c1 = window
        raw = np.asarray(plane)[r0:r1, c0:c1].copy()
        fin = np.isfinite(raw)
        st.calls["scoped"].append(
            {"plane": np.shape(plane), "window": tuple(window), "raw": raw.shape}
        )
        reading = SimpleNamespace(
            available=fin.copy(),
            markers=np.zeros(raw.shape, np.int32),
            dark=np.zeros(raw.shape, bool),
            labels=np.ones(raw.shape, np.int32),
            distance_mm=np.ones(raw.shape),
        )
        return SimpleNamespace(
            window_rc=tuple(window), raw=raw, finite=fin, reading=reading
        )

    def field(plane, reading, basis, outside=None):
        st.calls["field"].append(
            {
                "plane": plane.shape,
                "outside": None if outside is None else outside.shape,
                "basis": np.asarray(basis),
            }
        )
        return SimpleNamespace(leg=np.ones(plane.shape, bool))

    real = ri.native_gradient_territories

    def grad(raw, avail, spacing, groups):
        if st.fake:
            return fake_gradient(st)(raw, avail, spacing, groups)
        st.calls["gradient"].append(
            {"raw": raw.shape, "available": np.asarray(avail).shape}
        )
        return real(raw, avail, spacing, groups)

    def margin_of(uid, z, raw):
        st.calls["margin"].append(raw.shape)
        return np.zeros(raw.shape, bool)

    def once(name, key, fn):
        k = (name, key)
        if k not in cache:
            cache[k] = fn()
        return cache[k]

    monkeypatch.setattr(ri, "scoped_interior_of", scoped)
    monkeypatch.setattr(ri, "read_field", field)
    monkeypatch.setattr(ri, "native_gradient_territories", grad)
    monkeypatch.setattr(ri, "margin_of", margin_of)
    monkeypatch.setattr(ri, "plane_frame", lambda series, z: st.frame(z))
    monkeypatch.setattr(ri, "once", once)
    monkeypatch.setattr(ri, "reads", lambda *a, **k: None)
    monkeypatch.setattr(ri, "handed", lambda *a, **k: None)
    monkeypatch.setattr(ri, "ledger", SimpleNamespace(record=lambda *a, **k: None))
    return st


def run(env, kind, rcs=(H0, H1), nan_rc=None, prep=None):
    orient, spacing, view = SCEN[kind]
    fac = frame_factory(orient, spacing)
    env.frame = fac
    tgt = make_target(view, nan_rc)
    axs = [
        make_axial(NAMES[i], fac(Z0).to_patient(np.array([rc], float))[0], uid=f"ax{i}")
        for i, rc in enumerate(rcs)
    ]
    if prep:
        prep(tgt, fac)
    src = ri.native_gastrocnemius_head_sources(axs, "study")
    out = ri.name_native_gastrocnemius_heads(axs + [tgt], src, "study")
    return tgt, axs, src, out[len(axs)], fac, view


def unpack(arrays, pre, key, i):
    off, shapes = arrays[f"{pre}_offsets"], arrays[f"{pre}_shapes"]
    return arrays[f"{pre}_{key}"][off[i] : off[i + 1]].reshape(tuple(shapes[i]))


def lps_of(fac, rc):
    return fac(Z0).to_patient(np.array([rc], float))[0]


# ---- source validation and retention -------------------------------------------------


def test_source_validation_named_not_absence():
    lps = np.array([1.0, 2.0, 3.0])
    cases = {
        "native_source_acquisition_invalid": lambda a: a.record.update(series_uid="x"),
        "native_source_slice_invalid": lambda a: a.record.update(slice_index=True),
        "native_source_slice_invalid#oob": lambda a: a.record.update(slice_index=5),
        "native_source_support_invalid": lambda a: a.arrays.update(
            a1_objects=np.zeros((8, 8), np.int32)
        ),
        "native_source_support_invalid#3d": lambda a: a.arrays.update(
            a1_objects=np.zeros((1, AXN, AXN), np.int32)
        ),
        "native_source_support_invalid#float": lambda a: a.arrays.update(
            a1_objects=np.zeros((AXN, AXN), float)
        ),
    }
    for label, mutate in cases.items():
        ax = make_axial(NAMES[0], lps)
        mutate(ax)
        res = ri.native_gastrocnemius_head_sources([ax], "study")[NAMES[0]]
        assert res["status"] == "unavailable"
        assert [c["status"] for c in res["detail"]["considered"]] == [
            label.split("#")[0]
        ]
    ax = make_axial(NAMES[0], lps)
    ax.series.volume = np.zeros((AXN, AXN))
    res = ri.native_gastrocnemius_head_sources([ax], "study")[NAMES[0]]
    assert res["detail"]["considered"][0]["status"] == "native_source_slice_invalid"


def test_unique_winner_keeps_all_eligible_and_invalid_visible():
    lps = np.array([1.0, 2.0, 3.0])
    big = make_axial(NAMES[0], lps, pixels=((4, 5), (4, 6)), uid="a")
    small = make_axial(NAMES[0], lps, pixels=((4, 5),), uid="b")
    bad = make_axial(NAMES[0], lps, uid="c")
    bad.record["slice_index"] = 9
    res = ri.native_gastrocnemius_head_sources([small, big, bad], "study")[NAMES[0]]
    assert res["status"] == "selected" and res["selected"]["owner"] is big
    det = res["detail"]
    assert sorted(e["count"] for e in det["eligible"]) == [1, 2]
    assert all("area_mm2" in e and "peak_rc" in e for e in det["eligible"])
    assert [c["status"] for c in det["considered"]] == ["native_source_slice_invalid"]
    tie = ri.native_gastrocnemius_head_sources(
        [make_axial(NAMES[0], lps, uid="a"), make_axial(NAMES[0], lps, uid="b")],
        "study",
    )[NAMES[0]]
    assert tie["status"] == "tied" and len(tie["detail"]["eligible"]) == 2


def test_ax_identity_unchanged(env):
    lps = lps_of(frame_factory(*SCEN["sagittal"][:2]), H0)
    ax = make_axial(NAMES[0], lps)
    before = (ax.arrays["a1_objects"].copy(), copy.deepcopy(ax.record["assignments"]))
    src = ri.native_gastrocnemius_head_sources([ax], "study")
    assert src[NAMES[0]]["status"] == "selected"
    assert src[NAMES[1]]["status"] == "unavailable"
    assert np.array_equal(ax.arrays["a1_objects"], before[0])
    assert ax.record["assignments"] == before[1]


# ---- window geometry -------------------------------------------------------------------


@pytest.mark.parametrize("kind", list(SCEN))
def test_window_matches_physical_masks(kind):
    orient, spacing, _ = SCEN[kind]
    fac = frame_factory(orient, spacing)
    frame = fac(Z0)
    pts = np.vstack([lps_of(fac, H0), lps_of(fac, H1)])
    level = float(pts[:, 2].max())
    w = ri._gastro_window(frame, (N, N), {"a": pts[:1], "b": pts[1:]}, level)
    assert w["status"] == "ok"
    r0, r1, c0, c1 = w["window_rc"]
    assert (r1 - r0) * (c1 - c0) < N * N
    assert w["scope"]["partial"] and w["scope"]["padding_mm"] == ri.SQUINT_TILE_MM
    nrm = np.asarray(frame.normal())
    u = np.cross(nrm, [0, 0, 1.0])
    u /= np.linalg.norm(u)
    grid = np.array([(r, c) for r in range(N) for c in range(N)], float)
    phys = frame.to_patient(grid)
    t_src, tol = pts @ u, float(np.max(np.abs(frame.basis_lps[2])))
    lo, hi = t_src.min() - ri.SQUINT_TILE_MM, t_src.max() + ri.SQUINT_TILE_MM
    inside = (
        (grid[:, 0] >= r0) & (grid[:, 0] < r1) & (grid[:, 1] >= c0) & (grid[:, 1] < c1)
    )
    t = phys @ u
    out = ~inside
    assert np.all(
        (phys[out, 2] > level + tol - 1e-6)
        | (t[out] < lo + 1e-6)
        | (t[out] > hi - 1e-6)
    )
    for rc in (H0, H1):
        assert r0 <= rc[0] < r1 and c0 <= rc[1] < c1


def test_window_named_unavailable_states():
    fac = frame_factory(*SCEN["sagittal"][:2])
    pts = lps_of(fac, H0)[None]
    horizontal = PlaneFrame.from_dicom((0, 0, 0), [1, 0, 0, 0, 1, 0], (1.0, 1.0))
    assert (
        ri._gastro_window(horizontal, (N, N), {"a": pts}, 0.0)["status"]
        == "native_window_leg_axis_unavailable"
    )
    nan = np.array([[np.nan, 0.0, 0.0]])
    assert (
        ri._gastro_window(fac(Z0), (N, N), {"a": nan}, 0.0)["status"]
        == "native_window_no_usable_source"
    )
    far = pts + np.array([0.0, 5000.0, 0.0])
    assert (
        ri._gastro_window(fac(Z0), (N, N), {"a": far}, 0.0)["status"]
        == "native_window_no_usable_source"
    )


def test_invalid_window_gives_named_context_without_work(env):
    orient, spacing, view = SCEN["sagittal"]
    env.frame = frame_factory(orient, spacing)
    tgt = make_target(view)
    ctx = ri._gastro_context(tgt, Z0, {}, {}, 0.0, {"status": "native_window_empty"})
    assert ctx["status"] == "native_window_empty"
    assert not env.calls["scoped"] and not env.calls["gradient"]


# ---- crop, no full-frame path, sharing -------------------------------------------------


@pytest.mark.parametrize("kind", list(SCEN))
def test_crop_shapes_shared_context_and_roundtrip(env, kind):
    tgt, _, _, (_, _), fac, view = run(env, kind)
    info = tgt.record["a4_gastroc_context"]
    assert Z0 in info["context_slices"]  # lens_of/field_of/interior_regions would raise
    n_ctx = len(info["context_slices"])
    assert (
        len(env.calls["scoped"])
        == len(env.calls["field"])
        == len(env.calls["gradient"])
        == n_ctx
    )
    for s, f, g in zip(
        env.calls["scoped"], env.calls["field"], env.calls["gradient"], strict=True
    ):
        r0, r1, c0, c1 = s["window"]
        assert s["plane"] == (N, N) and s["raw"] == (r1 - r0, c1 - c0)
        assert s["raw"][0] * s["raw"][1] < N * N
        assert f["plane"] == f["outside"] == g["raw"] == g["available"] == s["raw"]
    cands = [c for c in tgt.record["a4_gastroc_candidates"] if c["slice"] == Z0]
    assert {c["head"] for c in cands} == set(NAMES)  # both heads, one context
    win = info["window_rc"][Z0]
    local = ri.local_frame(fac(Z0), win)
    for name, rc in zip(NAMES, (H0, H1), strict=True):
        full = info["locations_full_rc"][Z0][name]
        loc = info["locations_local_rc"][Z0][name]
        assert full == rc and (loc[0] + win[0], loc[1] + win[2]) == rc
        assert np.allclose(
            local.to_patient(np.array([loc], float)),
            fac(Z0).to_patient(np.array([rc], float)),
        )
    i = info["context_slices"].index(Z0)
    pre = f"a4_{view}_gastroc_context"
    raw = unpack(tgt.arrays, pre, "raw", i)
    assert np.array_equal(raw, tgt.series.volume[Z0][win[0] : win[1], win[2] : win[3]])
    assert tuple(tgt.arrays[f"{pre}_window_rc"][i]) == tuple(win)
    assert tgt.arrays[f"{pre}_offsets"][-1] == sum(
        int(np.prod(s)) for s in tgt.arrays[f"{pre}_shapes"]
    )
    for key in ("gradient_valid", "labels", "bone_femur", "lens_markers", "margin"):
        assert unpack(tgt.arrays, pre, key, i).shape == raw.shape
    assert env.calls["margin"] and all(m == (N, N) for m in env.calls["margin"])


def test_outside_window_location_is_unknown(env):
    orient, spacing, view = SCEN["sagittal"]
    fac = frame_factory(orient, spacing)
    env.frame = fac
    tgt = make_target(view)
    pts = lps_of(fac, H0)[None]
    w = ri._gastro_window(fac(Z0), (N, N), {"a": pts}, float(pts[0, 2]))
    r0, _, c0, _ = w["window_rc"]
    outside = (r0 - 1, c0) if r0 > 0 else (r0, c0 - 1)
    ctx = ri._gastro_context(
        tgt, Z0, {NAMES[0]: outside, NAMES[1]: H0}, {}, float(pts[0, 2]), w
    )
    assert ctx["status"] == "measured"
    assert ctx["location_local_rc"][NAMES[0]] is None
    assert ctx["location_full_rc"][NAMES[0]] == outside
    assert ctx["location_local_rc"][NAMES[1]] == (H0[0] - r0, H0[1] - c0)
    assert f"gastrocnemius_head_location_{NAMES[0]}" not in ctx["marker_groups"]


def test_nonfinite_crop_sample_is_unavailable_and_support_outside_window_unknown(env):
    env.fake = True
    nan = (30, 30)
    tgt, _, _, (here, _), _, view = run(env, "sagittal", nan_rc=nan)
    info = tgt.record["a4_gastroc_context"]
    win = info["window_rc"][Z0]
    i = info["context_slices"].index(Z0)
    pre = f"a4_{view}_gastroc_context"
    avail = unpack(tgt.arrays, pre, "available", i)
    assert not avail[nan[0] - win[0], nan[1] - win[2]]
    assert avail.sum() == avail.size - 1
    for o in here:
        stack = tgt.arrays[o.support]
        mask = stack[o.row]
        outside = np.ones_like(mask)
        outside[win[0] : win[1], win[2] : win[3]] = False
        assert not mask[outside].any()


def test_one_pixel_seeded_basin_is_valid_native_reading(env):
    env.fake = True
    tgt, _, _, (here, _), _, _ = run(env, "oblique")
    reads_ = [o for o in here if o.object in NAMES]
    assert {o.object for o in reads_} == set(NAMES)
    for o, rc in zip(
        sorted(reads_, key=lambda o: NAMES.index(o.object)), (H0, H1), strict=True
    ):
        assert (o.provenance, o.kind, o.code) == (
            "native",
            "reading",
            ri.GASTROC_SCOPED_CODE,
        )
        assert o.count == 1 and o.off_plane_mm == 0.0
        mask = tgt.arrays[o.support][o.row]
        assert mask.shape == (N, N) and mask.sum() == 1 and mask[rc]
        assert tuple(tgt.arrays[f"{o.support}_window_rc"][o.row]) == tuple(
            tgt.record["a4_gastroc_context"]["window_rc"][Z0]
        )
    assert ri.observation_rows(reads_)


# ---- bone conflicts --------------------------------------------------------------------


def _bone_prep(artifact_override=None):
    def prep(tgt, fac):
        region = np.zeros((1, N, N), bool)
        region[0, H0[0] - 2 : H0[0] + 3, H0[1] - 2 : H0[1] + 3] = True
        tgt.arrays["a3_femur_plane_region"] = region
        tgt.arrays["a3_femur_plane_slices"] = np.asarray([Z0], np.int32)
        art = artifact_override or str(ri.artifact_of("study", tgt.record))
        tgt.record["observations"] = [
            {
                "object": "femur",
                "provenance": "native",
                "kind": "resolved",
                "code": "identified",
                "series_uid": "sag",
                "view": tgt.record["view"],
                "slices": [Z0],
                "support": "a3_femur_plane_region",
                "artifact": art,
                "row": 0,
                "label": None,
                "count": int(region[0].sum()),
            }
        ]

    return prep


@pytest.mark.parametrize("kind", list(SCEN))
def test_known_bone_conflict_refuses_unknown_neutral(env, kind):
    env.fake = True
    tgt, _, _, (here, missing), _, _ = run(env, kind, prep=_bone_prep())
    cand = next(
        c
        for c in tgt.record["a4_gastroc_candidates"]
        if c["slice"] == Z0 and c["head"] == NAMES[0]
    )
    assert cand["status"] == "known_native_bone_conflict"
    assert cand["bone_context"]["femur"]["metadata"]["addresses"]
    assert not [o for o in here if o.object == NAMES[0]]
    assert any(
        m.object == NAMES[0] and "known_native_bone_conflict" in m.code for m in missing
    )
    env.calls["scoped"].clear()
    tgt2, _, _, (here2, _), _, _ = run(env, kind, prep=_bone_prep("wrong.npz"))
    assert tgt2.record["a4_gastroc_context"]["bone_status"][Z0]["femur"].startswith(
        "unknown"
    )
    assert [o for o in here2 if o.object == NAMES[0]]


# ---- PCL defaults ----------------------------------------------------------------------


def test_pcl_defaults_unchanged():
    out = ri.native_pcl_sources([], "study")
    assert out["pcl"]["status"] == "unavailable"
    assert inspect.signature(ri.name_native_pcl_sections).parameters.get(
        "ligament", True
    )
    assert (
        inspect.signature(ri.name_native_ligament_sections)
        .parameters["ligament"]
        .default
        == "pcl"
    )
