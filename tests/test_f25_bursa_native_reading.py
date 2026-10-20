"""F25 bursa native reading. Not executed by the author; root runs it privately."""

from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
_spec = importlib.util.spec_from_file_location(
    "run_interiors_f25", ROOT / "scripts" / "run_interiors.py"
)
assert _spec is not None and _spec.loader is not None
mod = importlib.util.module_from_spec(_spec)
sys.modules["run_interiors_f25"] = mod
_spec.loader.exec_module(mod)

from knee.collapse.observations import Observation, Unresolved

STUDY = "S"
NAME = mod.BURSA_NAME
KEY = mod.BURSA_READING_KEY
SHAPE = (30, 20)


class F:
    """Affine frame: lps = origin + basis @ [r, c]; basis columns are mm per row/col pixel."""

    def __init__(self, origin, basis):
        self.origin_lps = np.asarray(origin, float)
        self.basis_lps = np.asarray(basis, float)
        self.spacing_rc = (1.0, 1.0)

    def normal(self):
        n = np.cross(self.basis_lps[:, 0], self.basis_lps[:, 1])
        return n / np.linalg.norm(n)

    def to_patient(self, rc):
        return self.origin_lps + np.asarray(rc, float) @ self.basis_lps.T

    def to_native(self, pts):
        return (np.asarray(pts, float) - self.origin_lps) @ np.linalg.pinv(
            self.basis_lps
        ).T


def make_series(uid, frames, volume, fs="1", fl="1", thick=2.0):
    return SimpleNamespace(
        row=SimpleNamespace(series_uid=uid, fluid_sensitive=fl, fat_suppression=fs),
        volume=volume,
        frames=frames,
        slice_thickness_mm=tuple([thick] * len(volume)),
    )


def make_own(uid, view, series, arrays=None):
    return SimpleNamespace(
        record={"series_uid": uid, "view": view, "observations": [], "slice_index": 1},
        arrays=arrays if arrays is not None else {},
        series=series,
    )


def source_pair(
    tilt=0.0,
    address_ok=True,
    count_ok=True,
    claimed_count=None,
    part_uid="A",
    obs_view=("Axial", "1", "1"),
    part_view=None,
    claim=0,
    thick=2.0,
    owner_uid="A",
):
    # AX frame: lps = (c, r, tilt*r); with tilt 0 the source centers have zero SI extent.
    frame = F([0, 0, 0], [[0, 1], [1, 0], [tilt, 0]])
    series = make_series("A", [frame], np.zeros((1, 20, 10)), thick=thick)
    own = make_own(owner_uid, ("Axial", "1", "1"), series)
    support = np.zeros((20, 10), bool)
    for r in range(10, 14):
        support[r, 0] = True
        support[r, 4] = True
    record = {
        "series_uid": part_uid,
        "view": obs_view if part_view is None else part_view,
    }
    if claim is not None:
        record["slice_index"] = claim
    artifact = str(mod.artifact_of(STUDY, record))
    record["artifact"] = artifact
    record["observations"] = [
        Observation(
            object=NAME,
            provenance="native",
            kind="resolved",
            series_uid="A",
            view=obs_view,
            slices=(0,),
            code="identified",
            count=(
                claimed_count
                if claimed_count is not None
                else int(support.sum()) + (0 if count_ok else 1)
            ),
            off_plane_mm=0.0,
            support=mod.BURSA_SUPPORT,
            note="n",
            artifact=artifact if address_ok else "other.npz",
        )
    ]
    return own, (record, {mod.BURSA_SUPPORT: support})


def target(planes=None, fs="1", uid="T"):
    frames = [F([2 * z, 0, 0], [[0, 0], [1, 0], [0, 1]]) for z in range(3)]
    volume = np.ones((3, *SHAPE))
    for z, blobs in (planes or {}).items():
        for r, c in blobs:
            volume[z, r, c] = 1e9
    return make_own(
        uid, ("Sagittal", "1", "1"), make_series(uid, frames, volume, fs=fs)
    )


def ref(uid="T", key="K", light=10.0):
    return SimpleNamespace(
        source_series_uid=uid,
        acquisition_key=key,
        support_address="a1_objects",
        bones_light=light,
        bones_support_digest="d",
        support_codes=(1, 2),
        middle_z=1,
        plane_digest="p",
    )


def recorded(codes=None, bones=10.0, uid="T"):
    codes = codes or [int(mod.OBJECT_CODES["femur"]), int(mod.OBJECT_CODES["tibia"])]
    return {
        "native_reference": {
            "state": "available",
            "source_series_uid": uid,
            "native_middle_slice": 1,
            "support_address": "a1_objects",
            "support_codes": codes,
            "acquisition_key": "K",
            "femur_light": 8.0,
            "bones_light": bones,
            "bones_support_digest": "d",
        }
    }


@pytest.fixture(autouse=True)
def patched(monkeypatch):
    monkeypatch.setattr(mod, "plane_frame", lambda s, z: s.frames[z], raising=False)
    monkeypatch.setattr(mod, "frame_identity", lambda f, full: "K", raising=False)
    monkeypatch.setattr(
        mod, "finite_of", lambda series: np.isfinite(series.volume), raising=False
    )
    monkeypatch.setattr(
        mod,
        "margin_of",
        lambda uid, z, plane: np.zeros(plane.shape, dtype=bool),
        raising=False,
    )
    monkeypatch.setattr(mod, "handed", lambda *a, **k: None, raising=False)
    monkeypatch.setattr(mod, "reads", lambda *a, **k: None, raising=False)


BLOBS_TIE = [(10, 0), (10, 1), (11, 0), (11, 1), (13, 0), (13, 1), (14, 0), (14, 1)]


def run(measured, group, mapping=None, reference=lambda own: ref()):
    return mod.collect_bursa_native_readings(
        measured, [group], STUDY, mapping, reference_for=reference
    )


def test_profile_ties_full_components_and_one_row_per_plane_are_kept():
    src, group = source_pair()
    tgt = target({0: BLOBS_TIE, 2: BLOBS_TIE})
    said = run([src, tgt], group)
    reading = tgt.record[KEY]
    assert reading["status"] == "measured"
    assert reading["profile"]["maximum_slices_all_ties"] == [0, 2]
    assert reading["profile"]["counts"][1] in (None, 0, 0.0)
    assert (
        len(reading["profile"]["counts"]) == 3
        and len(reading["profile"]["slab_counts"]) == 3
    )
    assert (
        "a4_sagittal_gastrocnemius_semimembranosus_bursa_source_profile_count"
        in tgt.arrays
    )
    assert [p["slice"] for p in reading["planes"]] == [0, 2]
    for plane in reading["planes"]:
        assert plane["lens_code"] == "tied_largest_bodies"
        assert len(plane["components"]) == 2
        assert all(c["tied_or_selected_largest"] for c in plane["components"])
        assert (
            plane["selected_pixels"] == 0 and plane["full_boundary_asserted"] is False
        )
        assert "right" in plane["components"][0]["edges_clipped_by_crop"]
        names = plane["arrays"]
        assert tgt.arrays[names["component_sizes"]].tolist() == [4, 4]
        assert tgt.arrays[names["labels"]].max() == 2
        assert tgt.arrays[names["labels"]].shape == tuple(plane["crop_shape"]) != SHAPE
    seen, missing = said[1]
    assert [o.slices for o in seen] == [(0,), (2,)]
    assert all(o.kind == "reading" and o.provenance == "native" for o in seen)
    assert len(missing) == 2 and all(isinstance(m, Unresolved) for m in missing)
    for o in seen:
        support = tgt.arrays[o.support]
        assert support.dtype == bool and support.shape == SHAPE
        assert o.count == int(support.sum()) == 0
        assert o.artifact == reading["artifact"]
    assert said[0] == ([], [])


def test_unique_largest_is_cropped_clipped_and_counted_on_exact_support():
    src, group = source_pair()
    tgt = target(
        {0: [(10, 0), (10, 1), (10, 2), (11, 0), (11, 1), (13, 0)], 2: [(13, 0)]}
    )
    said = run([src, tgt], group)
    plane = tgt.record[KEY]["planes"][0]
    assert plane["lens_code"] == "selected"
    assert (
        plane["selected_pixels"] == 4
    )  # (10,2) lies outside the crop: unknown, not claimed
    assert (
        "right" in plane["components"][0]["edges_clipped_by_crop"]
        or "right" in plane["components"][1]["edges_clipped_by_crop"]
    )
    seen, missing = said[1]
    first = seen[0]
    support = tgt.arrays[first.support]
    assert first.count == int(support.sum()) == 4
    assert np.argwhere(support).tolist() == [[10, 0], [10, 1], [11, 0], [11, 1]]
    assert len(seen) == 2 and missing == []


def test_map_guide_adds_location_not_boundary():
    src, group = source_pair()
    tgt = target({0: [(20, 0), (20, 1)], 2: [(13, 0)]})
    guide = SimpleNamespace(
        status="guided",
        slices=(0, 2),
        half_px=(0.0, 0.0),
        placements=[{"status": "ok", "point_lps": [0.0, 20.0, 0.0]}],
    )
    mapping = SimpleNamespace(guide=lambda name, own: guide)
    said = run([src, tgt], group, mapping)
    plane = tgt.record[KEY]["planes"][0]
    assert plane["query_basis"] == "projected_source_plus_map_guide"
    assert plane["map_guide"] == "guided" and plane["guide_boxes"]
    assert plane["selected_pixels"] == 2
    support = tgt.arrays[said[1][0][0].support]
    assert np.argwhere(support).tolist() == [[20, 0], [20, 1]]


def test_default_reference_consumes_existing_record_and_never_measures(monkeypatch):
    import knee.objects.assignments as asg

    def boom(*a, **k):
        raise AssertionError("marrow_light must not be called")

    monkeypatch.setattr(asg, "marrow_light", boom)
    monkeypatch.setattr(mod, "marrow_light", boom, raising=False)
    calls = []

    def fake(own, femur, bones=None):
        calls.append((femur, bones))
        return ref(light=bones)

    monkeypatch.setattr(mod, "native_middle_reference", fake)
    src, group = source_pair()
    tgt = target({0: BLOBS_TIE, 2: BLOBS_TIE})
    tgt.record["patella"] = recorded(codes=[int(mod.OBJECT_CODES["femur"])], bones=None)
    tgt.record["recess"] = recorded()
    mod.collect_bursa_native_readings([src, tgt], [group], STUDY, None)
    reading = tgt.record[KEY]
    assert reading["status"] == "measured" and calls == [(8.0, 10.0)]
    assert reading["planes"][0]["calibration"]["bones_light"] == 10.0


def test_default_reference_without_usable_record_is_named_unavailable(monkeypatch):
    calls = []
    monkeypatch.setattr(mod, "native_middle_reference", lambda *a, **k: calls.append(a))
    src, group = source_pair()
    for records in (
        {},
        {"patella": recorded(codes=[int(mod.OBJECT_CODES["femur"])], bones=None)},
        {"recess": recorded(uid="elsewhere")},
    ):
        tgt = target({0: BLOBS_TIE, 2: BLOBS_TIE})
        tgt.record.update(records)
        said = mod.collect_bursa_native_readings([src, tgt], [group], STUDY, None)
        assert (
            tgt.record[KEY]["status"] == "calibration_no_existing_bones_light_reference"
        )
        assert said[1][0] == [] and len(said[1][1]) == 2
    assert calls == []


def test_zero_si_axial_centers_get_voxel_support_span():
    src, group = source_pair(tilt=0.0, claim=np.int64(0), claimed_count=np.int64(8))
    sources = mod.native_bursa_source([group], [src], STUDY)[NAME]
    points = sources["selected"]["points_lps"]
    meta = sources["selected"]["metadata"]
    assert np.ptp(points[:, 2]) == 0.0
    assert meta["span_lps_mm"] == pytest.approx([5.0, 4.0, 2.0])
    assert meta["slice_thickness_mm"] == 2.0
    assert meta["normal_lps"] == pytest.approx([0.0, 0.0, -1.0])
    assert (
        meta["slice"] == 0 and meta["artifact"] and meta["support"] == mod.BURSA_SUPPORT
    )
    assert meta["frame_basis_lps"] == [[0.0, 1.0], [1.0, 0.0], [0.0, 0.0]]
    tgt = target({0: BLOBS_TIE, 2: BLOBS_TIE})
    run([src, tgt], group)
    assert tgt.record[KEY]["status"] == "measured"
    assert all(v > 0 for v in tgt.record[KEY]["source"]["span_lps_mm"])


def test_lenses_receive_cropped_arrays_and_nonfinite_pixels_stay_unknown(monkeypatch):
    import knee.objects.assignments as asg

    calls = {"white": [], "body": []}
    real_white, real_body = asg.white_as_fluid, asg.white_body_at_location

    def spy_white(plane, objects, measures=None, reference_light=None):
        calls["white"].append(
            (
                plane.shape,
                objects.shape,
                bool(np.isnan(plane).any()),
                bool(np.isinf(plane).any()),
            )
        )
        return real_white(plane, objects, measures, reference_light=reference_light)

    def spy_body(white, target_mask):
        calls["body"].append((white.shape, target_mask.shape, white.copy()))
        return real_body(white, target_mask)

    monkeypatch.setattr(asg, "white_as_fluid", spy_white)
    monkeypatch.setattr(asg, "white_body_at_location", spy_body)
    margin = np.zeros(SHAPE, dtype=bool)
    margin[10, 0] = True
    monkeypatch.setattr(
        mod,
        "margin_of",
        lambda uid, z, plane: margin if z == 0 else np.zeros(plane.shape, bool),
    )
    src, group = source_pair()
    tgt = target({0: BLOBS_TIE, 2: BLOBS_TIE})
    tgt.series.volume[0, 10, 1] = np.nan
    tgt.series.volume[0, 11, 1] = np.inf
    run([src, tgt], group)
    info = tgt.record[KEY]["planes"][0]
    crop_shape = tuple(info["crop_shape"])
    r0, c0 = info["crop_offset_rc"]
    assert crop_shape != SHAPE
    assert calls["white"][0] == (crop_shape, crop_shape, True, True)
    white_in, query_in, white_seen = calls["body"][0]
    assert white_in == query_in == crop_shape
    assert not white_seen[10 - r0, 1 - c0] and not white_seen[11 - r0, 1 - c0]
    finite = tgt.arrays[info["arrays"]["finite"]]
    margin_seen = tgt.arrays[info["arrays"]["margin"]]
    available = tgt.arrays[info["arrays"]["available"]]
    assert not finite[10 - r0, 1 - c0] and not finite[11 - r0, 1 - c0]
    assert margin_seen[10 - r0, 0 - c0] and not available[10 - r0, 0 - c0]
    assert not white_seen[10 - r0, 0 - c0]
    assert info["unknown_nonfinite_pixels"] == 2
    assert info["unknown_margin_pixels"] == 1
    assert tgt.arrays[info["arrays"]["plane"]].shape == crop_shape


def test_calibration_absent_and_wrong_identity_are_named_refusals():
    src, group = source_pair()
    tgt = target({0: BLOBS_TIE, 2: BLOBS_TIE})
    said = run([src, tgt], group, reference=lambda own: "light_unavailable")
    assert tgt.record[KEY]["status"] == "calibration_light_unavailable"
    assert said[1][0] == [] and len(said[1][1]) == 2
    assert not any("_bursa_native_reading_z" in k for k in tgt.arrays)
    tgt2 = target({0: BLOBS_TIE, 2: BLOBS_TIE})
    run([src, tgt2], group, reference=lambda own: ref(key="other"))
    assert tgt2.record[KEY]["status"] == "calibration_wrong_acquisition"
    tgt3 = target({0: BLOBS_TIE, 2: BLOBS_TIE})
    run([src, tgt3], group, reference=lambda own: ref(uid="elsewhere"))
    assert tgt3.record[KEY]["status"] == "calibration_wrong_series"


def test_calibration_provenance_recorded():
    src, group = source_pair()
    tgt = target({0: BLOBS_TIE, 2: BLOBS_TIE})
    run([src, tgt], group)
    calibration = tgt.record[KEY]["planes"][0]["calibration"]
    assert calibration["bones_light"] == 10.0 and calibration["scalar"] == "bones_light"
    assert calibration["source_series_uid"] == "T"


def test_non_fs_target_and_missing_source_are_named():
    src, group = source_pair()
    nonfs = target(fs="0")
    run([src, nonfs], group)
    assert nonfs.record[KEY]["status"] == "target_not_fluid_sensitive_fat_suppressed"
    tgt = target({0: BLOBS_TIE})
    mod.collect_bursa_native_readings(
        [src, tgt], [], STUDY, None, reference_for=lambda o: ref()
    )
    assert tgt.record[KEY]["status"] == "source_unavailable"


@pytest.mark.parametrize(
    "kwargs, expected",
    [
        ({"address_ok": False}, "invalid_native_address"),
        ({"count_ok": False}, "invalid_native_count"),
        ({"claimed_count": 8.0}, "invalid_native_count"),
        ({"claimed_count": True}, "invalid_native_count"),
        ({"part_uid": "B"}, "source_series_uid_mismatch"),
        ({"owner_uid": "B"}, "source_series_uid_mismatch"),
        ({"obs_view": ("Axial", "1", "2")}, "source_view_mismatch"),
        ({"part_view": ("Axial", "1", "2")}, "source_view_mismatch"),
        ({"claim": 5}, "source_slice_mismatch"),
        ({"claim": None}, "source_slice_unverified"),
        ({"claim": True}, "source_slice_unverified"),
        ({"thick": 0.0}, "source_thickness_unavailable"),
    ],
)
def test_source_ownership_mismatch_refuses(kwargs, expected):
    src, group = source_pair(**kwargs)
    tgt = target({0: BLOBS_TIE})
    said = run([src, tgt], group)
    reading = tgt.record[KEY]
    assert reading["status"] == "source_invalid_source_context"
    assert [i["status"] for i in reading["source"]["invalid_sources"]] == [expected]
    assert said[1][0] == []
    assert [u.code for u in said[1][1]] == ["source_invalid_source_context"]
    assert not any("_bursa_native_reading_z" in k for k in tgt.arrays)


def test_target_without_source_points_is_named_unknown():
    src, group = source_pair()
    tgt = target({0: BLOBS_TIE})
    tgt.series.frames = [
        F([500 + 2 * z, 0, 0], [[0, 0], [1, 0], [0, 1]]) for z in range(3)
    ]
    run([src, tgt], group)
    assert tgt.record[KEY]["status"] in (
        "no_source_points_in_target_half_slabs",
        "target_profile_unusable",
    )


def test_old_records_arrays_and_source_observations_preserved():
    src, group = source_pair()
    tgt = target({0: BLOBS_TIE, 2: BLOBS_TIE})
    keep = np.arange(3)
    tgt.arrays["old"] = keep
    tgt.record["observations"] = ["old_row"]
    before = dict(tgt.record)
    original = list(group[0]["observations"])
    run([src, tgt], group)
    assert tgt.arrays["old"] is keep and tgt.record["observations"] == ["old_row"]
    assert all(tgt.record[k] == v for k, v in before.items() if k != KEY)
    assert group[0]["observations"] == original
    assert group[0]["observations"][0].kind == "resolved"
    assert src.record["observations"] == []


def test_wiring_is_single_call_before_record_save():
    tree = ast.parse((ROOT / "scripts" / "run_interiors.py").read_text())
    fn = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "measure_study"
    )

    def lines(name, first_arg=None):
        out = []
        for n in ast.walk(fn):
            if (
                isinstance(n, ast.Call)
                and getattr(n.func, "id", None) == name
                and (
                    first_arg is None
                    or (n.args and getattr(n.args[0], "id", None) == first_arg)
                )
            ):
                out.append(n.lineno)
        return sorted(out)

    collect = lines("collect_bursa_native_readings")
    assert len(collect) == 1
    last_keep = [l for l in lines("keep_recess") if l < collect[0]]
    assert last_keep and collect[0] - max(last_keep) < 15
    save = lines("save_study_record", "run_dir")
    assert save and collect[0] < min(save)
    delegated_save = lines("save", "destination")
    assert len(delegated_save) == 1
    assert len(lines("measure_study")) == 0
