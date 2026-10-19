"""The native-middle reference: exact identity, named unavailable states, optional default
unchanged, local geometry still required, and the real pointed callers."""

import inspect
from dataclasses import replace
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest
from scipy import ndimage as ndi

from knee.collapse.physical import PlaneFrame
from knee.objects import assignments as A
from knee.objects.interiors import InteriorRegions
from knee.telemetry import computing, recording
from scripts import run_interiors as run

SHAPE = (48, 40)
FRAME = PlaneFrame(
    np.array([10.0, 20.0, 30.0]),
    np.array([[0.0, 0.0], [1.0, 0.0], [0.0, 1.0]]),
    (1.0, 1.0),
)
FIELD_CODES = {"air": "abstain_no_leg", "skin": "abstain_no_air"}
FEMUR, TIBIA = int(A.OBJECT_CODES["femur"]), int(A.OBJECT_CODES["tibia"])


def _feet():
    femur, tibia = np.zeros(SHAPE, bool), np.zeros(SHAPE, bool)
    femur[18:32, 8:22] = True
    tibia[34:40, 8:22] = True
    return {"f": femur, "t": tibia}


def _objects():
    objects = np.zeros(SHAPE, np.int8)
    objects[20:31, 10:21] = FEMUR
    objects[34:40, 8:22] = TIBIA
    return objects


@pytest.fixture
def rig(monkeypatch):
    plane = np.full(SHAPE, 5.0)
    plane[20:31, 10:21] = 100.0
    plane[5:12, 11:18] = 100.0
    volume = np.stack([plane] * 3)
    finite = np.isfinite(volume)
    seen: dict[str, list] = {"lens": []}
    feet = _feet()

    def lens(raw, spacing, split, prominence, *, available, scope=None):
        seen["lens"].append(raw.shape)
        mask = raw > 50
        labels, _ = ndi.label(mask)
        return InteriorRegions(
            "measured",
            ~mask,
            available.copy(),
            ndi.distance_transform_edt(mask),
            np.zeros(raw.shape, np.int32),
            labels.astype(np.int32),
        )

    def field(raw, reading, basis, outside=None):
        return A.Field(
            reading.labels > 0,
            np.zeros(raw.shape, np.int8),
            dict(FIELD_CODES),
            A.territory_peaks(reading.labels, reading.distance_mm, basis),
            (False, True, True),
        )

    monkeypatch.setattr(run, "reads", lambda *a, **k: None)
    monkeypatch.setattr(run, "handed", lambda *a, **k: None)
    monkeypatch.setattr(run, "plane_frame", lambda s, z: FRAME)
    monkeypatch.setattr(run, "finite_of", lambda s: finite)
    monkeypatch.setattr(run, "bone_footprint", lambda s, z, f, shape, p, key: feet[key])
    monkeypatch.setattr(run, "interior_regions", lens)
    monkeypatch.setattr(
        run,
        "lens_scopes_of",
        lambda series, _split: tuple(
            run.full_frame_scope(series.volume[z].shape, reason="test fixture")
            for z in range(len(series.volume))
        ),
    )
    monkeypatch.setattr(run, "read_field", field)
    monkeypatch.setattr(run, "margin", lambda raw: np.zeros(raw.shape, bool))
    row = SimpleNamespace(series_uid="scope", fluid_sensitive="0", fat_suppression="1")
    own = SimpleNamespace(
        series=SimpleNamespace(row=row, volume=volume),
        record={"background_split": 1.0, "slice_index": 1},
        arrays={"acquired_plane": plane, "a1_objects": _objects()},
        frame=FRAME,
    )
    return SimpleNamespace(own=own, seen=seen)


def ask(own, window, **kw):
    return run.patella_plane(
        cast(Any, own),
        1,
        np.zeros((1, 3)),
        np.zeros((1, 3)),
        ("f", "t"),
        None,
        profile_window=window,
        **kw,
    )


def make_ref(own, femur=98.0, bones=96.0):
    ref = run.native_middle_reference(own, femur, bones)
    assert isinstance(ref, run.NativeMiddleReference)
    return ref


# ---- identity -------------------------------------------------------------------------------


def test_exact_identity_is_required(rig):
    own = rig.own
    ref = make_ref(own)
    ok = run.reference_use(ref, own, FRAME, "femur")
    assert ok.state == "usable" and ok.light == 98.0 and ok.reference is ref
    assert run.reference_use(ref, own, FRAME, "bones").light == 96.0
    assert ref.support_address == "a1_objects"
    assert ref.support_codes == (FEMUR, TIBIA) and ref.middle_z == 1
    assert ref.source_series_uid == "scope"
    for change, state in (
        ({"source_series_uid": "other"}, "series_mismatch"),
        ({"middle_z": 2}, "middle_slice_mismatch"),
        ({"support_address": "a2_x"}, "support_address_mismatch"),
        ({"frame_key": "x"}, "middle_frame_mismatch"),
        ({"acquisition_key": "x"}, "acquisition_mismatch"),
        ({"plane_digest": "x"}, "plane_mismatch"),
        ({"femur_support_digest": "x"}, "support_mismatch"),
    ):
        got = run.reference_use(replace(ref, **change), own, FRAME, "femur")
        assert got.state == state and got.light is None, state
    # a pointed plane of a different acquisition geometry is not the same acquisition
    other = PlaneFrame(FRAME.origin_lps, FRAME.basis_lps * 2.0, (2.0, 2.0))
    assert run.reference_use(ref, own, other, "femur").state == "acquisition_mismatch"
    # the support is recomputed from the caller's own a1_objects
    changed = _objects()
    changed[20, 10] = 0
    own.arrays["a1_objects"] = changed
    assert run.reference_use(ref, own, FRAME, "femur").state == "support_mismatch"
    own.arrays["a1_objects"] = np.zeros(SHAPE, np.int8)
    assert run.reference_use(ref, own, FRAME, "femur").state == "support_empty"


def test_absent_wrong_and_unavailable_are_distinct_named_states(rig):
    own = rig.own
    assert run.reference_use(None, own, FRAME, "femur").state == "not_supplied"
    assert run.reference_use("support_empty", own, FRAME, "femur").state == (
        "unavailable_support_empty"
    )
    assert run.reference_use(cast(Any, 3.0), own, FRAME, "femur").state == "wrong_type"
    femur_only = run.native_middle_reference(own, 98.0)
    assert isinstance(femur_only, run.NativeMiddleReference)
    assert femur_only.bones_light is None and femur_only.support_codes == (FEMUR,)
    assert run.reference_use(femur_only, own, FRAME, "bones").state == (
        "role_not_in_reference"
    )
    assert run.reference_record(None) == {"state": "not_supplied"}
    assert run.reference_record("support_empty")["state"] == "unavailable_support_empty"


def test_reference_requires_real_native_masks_and_a_usable_light(rig):
    own = rig.own
    good = own.arrays["a1_objects"]
    own.arrays["a1_objects"] = np.zeros(SHAPE, np.int8)
    assert run.native_middle_reference(own, 98.0, 96.0) == "support_empty"
    only_femur = np.zeros(SHAPE, np.int8)
    only_femur[20:31, 10:21] = FEMUR
    own.arrays["a1_objects"] = only_femur
    assert run.native_middle_reference(own, 98.0, 96.0) == "support_empty"
    assert isinstance(run.native_middle_reference(own, 98.0), run.NativeMiddleReference)
    for bad in (good.astype(float), good[:5], good.astype(bool), None, "x"):
        own.arrays["a1_objects"] = bad
        assert run.native_middle_reference(own, 98.0, 96.0) == "support_malformed"
    own.arrays.pop("a1_objects")
    assert run.native_middle_reference(own, 98.0) == "support_malformed"
    own.arrays["a1_objects"] = good
    for bad in (float("nan"), 0.0, -1.0, None, True, "x"):
        assert (
            run.native_middle_reference(own, cast(Any, bad), cast(Any, bad))
            == "light_unavailable"
        )
    assert isinstance(
        run.native_middle_reference(own, float("nan"), 96.0), run.NativeMiddleReference
    )


def test_middle_identity_and_role_validation_are_shared_once_per_context(
    rig, monkeypatch
):
    own = rig.own
    own.arrays["a1_objects"].setflags(write=False)
    own.arrays["acquired_plane"].setflags(write=False)
    own.frame.origin_lps.setflags(write=False)
    own.frame.basis_lps.setflags(write=False)
    original_support = run.reference_support_digests
    original_digest = run.digest
    counts: dict[str, Any] = {"support": 0, "large_digest_shapes": []}

    def counted_support(*args, **kwargs):
        counts["support"] += 1
        return original_support(*args, **kwargs)

    def counted_digest(value):
        array = np.asarray(value)
        if array.shape == SHAPE:
            counts["large_digest_shapes"].append(array.shape)
        return original_digest(value)

    monkeypatch.setattr(run, "reference_support_digests", counted_support)
    monkeypatch.setattr(run, "digest", counted_digest)
    pointed_frame = PlaneFrame(
        FRAME.origin_lps + np.array([0.0, 0.0, 4.0]),
        FRAME.basis_lps,
        FRAME.spacing_rc,
    )
    with computing():
        bundle = run.native_middle_bundle(own)
        femur_only = run.native_middle_reference(own, 98.0)
        composite = run.native_middle_reference(own, 98.0, 96.0)
        assert isinstance(femur_only, run.NativeMiddleReference)
        assert isinstance(composite, run.NativeMiddleReference)
        assert run.native_middle_bundle(own) is bundle
        assert run.native_middle_reference(own, 98.0, 96.0) is composite
        assert counts["support"] == 1  # both role supports are built together once
        assert counts["large_digest_shapes"] == [SHAPE, SHAPE, SHAPE]

        # The identical femur role product in the two readers shares base validation.
        for reference in (femur_only, composite, femur_only, composite):
            got = run.reference_use(reference, own, pointed_frame, "femur")
            assert got.state == "usable" and got.light == 98.0
        for _ in range(3):
            got = run.reference_use(composite, own, pointed_frame, "bones")
            assert got.state == "usable" and got.light == 96.0
        other_acquisition = PlaneFrame(
            FRAME.origin_lps,
            FRAME.basis_lps * 2.0,
            (2.0, 2.0),
        )
        assert (
            run.reference_use(composite, own, other_acquisition, "femur").state
            == "acquisition_mismatch"
        )
        assert counts["support"] == 1
        assert counts["large_digest_shapes"] == [SHAPE, SHAPE, SHAPE]

        # Same UID and same geometry do not share across a different measured owner or arrays.
        other = SimpleNamespace(
            series=own.series,
            record=dict(own.record),
            arrays={
                "acquired_plane": own.arrays["acquired_plane"].copy(),
                "a1_objects": own.arrays["a1_objects"].copy(),
            },
            frame=own.frame,
        )
        other.arrays["a1_objects"].setflags(write=False)
        other.arrays["acquired_plane"].setflags(write=False)
        other_reference = run.native_middle_reference(other, 98.0, 96.0)
        assert isinstance(other_reference, run.NativeMiddleReference)
        assert run.reference_use(
            other_reference, other, pointed_frame, "bones"
        ).state == ("usable")
        assert counts["support"] == 2
        assert counts["large_digest_shapes"] == [SHAPE] * 6


# ---- white_as_fluid ---------------------------------------------------------------------------


def test_white_as_fluid_optional_scalar_and_default_unchanged():
    plane = np.arange(16.0).reshape(4, 4)
    objects = np.zeros((4, 4), np.int8)
    objects[0, :2], objects[3, :2] = FEMUR, TIBIA
    base = A.white_as_fluid(plane, objects)
    assert base is not None
    np.testing.assert_array_equal(A.white_as_fluid(plane, objects, None, None), base)
    got = A.white_as_fluid(plane, objects, None, 2.0)
    np.testing.assert_array_equal(got, plane > A.FLUID_BRIGHTER * 2.0)
    for bad in (float("nan"), float("inf"), 0, -3.0, True, "x", None):
        np.testing.assert_array_equal(
            A.white_as_fluid(plane, objects, None, cast(Any, bad)), base
        )
    objects[3, :2] = 0  # local geometry still required
    reference_white = A.white_as_fluid(plane, objects, None, 2.0)
    assert reference_white is not None
    np.testing.assert_array_equal(reference_white, plane > A.FLUID_BRIGHTER * 2.0)
    assert A.white_as_fluid(plane, objects, None, None) is None
    for bad in (float("nan"), float("inf"), 0, -3.0, True, "x"):
        assert A.white_as_fluid(plane, objects, None, cast(Any, bad)) is None
    no_spatial_relation, no_lining = A.anterior_synovial_recess(
        reference_white, objects, np.eye(3)
    )
    assert not no_spatial_relation.any() and not no_lining.any()
    assert list(inspect.signature(A.white_as_fluid).parameters) == [
        "plane", "objects", "measures", "reference_light",
    ]  # fmt: skip
    # the per-slice consumer and the axial projected path keep their signatures
    assert "reference" not in inspect.signature(A.assign_plane).parameters
    assert list(inspect.signature(run.recess_axial_plane).parameters) == [
        "own", "z", "leg", "thick", "knee", "asked",
    ]  # fmt: skip


def test_middle_bundle_bypasses_memoization_for_writable_inputs(rig):
    own = rig.own
    assert own.arrays["a1_objects"].flags.writeable
    with computing():
        before = run.native_middle_bundle(own)
        assert not before.cacheable
        own.arrays["a1_objects"][0, 0] = FEMUR
        after = run.native_middle_bundle(own)
    assert after is not before
    assert after.femur_support_digest != before.femur_support_digest


def test_measure_study_publishes_middle_support_after_map_before_patella():
    import ast
    import inspect

    tree = ast.parse(inspect.getsource(run.measure_study))
    function = next(
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    container = next(node for node in function.body if isinstance(node, ast.With))
    statements = container.body
    map_index = next(
        i
        for i, statement in enumerate(statements)
        if any(
            isinstance(node, ast.Call) and ast.unparse(node.func) == "build_study_map"
            for node in ast.walk(statement)
        )
    )
    publication_index = next(
        i
        for i, statement in enumerate(statements)
        if isinstance(statement, ast.For)
        and ast.unparse(statement.target) == "own"
        and ast.unparse(statement.iter) == "measured"
        and any(
            isinstance(node, ast.Call)
            and ast.unparse(node.func) == "own.arrays['a1_objects'].setflags"
            for node in ast.walk(statement)
        )
    )
    patella_index = next(
        i
        for i, statement in enumerate(statements)
        if any(
            isinstance(node, ast.Call) and ast.unparse(node.func) == "name_the_patella"
            for node in ast.walk(statement)
        )
    )
    assert map_index < publication_index < patella_index
    publication = statements[publication_index]
    calls = [
        ast.unparse(node.func)
        for node in ast.walk(publication)
        if isinstance(node, ast.Call)
    ]
    assert "own.arrays['a1_objects'].setflags" in calls
    assert "native_middle_bundle" not in calls


# ---- patella ------------------------------------------------------------------------------------


def test_valid_reference_scopes_to_the_profile_domain_and_skips_remeasuring(
    rig, monkeypatch
):
    monkeypatch.setattr(
        run,
        "lens_of",
        lambda *a, **k: pytest.fail("whole-frame read after local success"),
    )
    ref = make_ref(rig.own)
    with computing(), recording():
        got = ask(rig.own, (2, 36, 6, 24), reference=ref)
    assert got.code == "identified" and got.window_rc == (2, 36, 6, 24)
    assert rig.seen["lens"] == [(34, 18)]  # footprints did not enlarge the lens
    assert "femur_footprint" not in got.scope_reason
    assert "native_middle_reference" in got.scope_reason
    assert got.reference is not None and got.reference.state == "usable"
    assert got.reference.reference is ref
    assert got.light == 98.0 and got.attempts[0].light == 98.0  # reused, not remeasured
    assert got.attempts[0].window_rc == got.window_rc
    assert got.available[2:36, 6:24].all() and not got.available[40, 30]
    rec = run.use_record(got.reference)
    assert rec is not None
    assert (
        rec["source_series_uid"] == "scope" and rec["support_address"] == "a1_objects"
    )


def test_default_and_incompatible_references_keep_the_old_scope_and_calibration(rig):
    ref = make_ref(rig.own)
    with computing(), recording():
        default = ask(rig.own, (2, 36, 6, 24))
        bad = ask(
            rig.own, (2, 36, 6, 24), reference=replace(ref, source_series_uid="x")
        )
        text = ask(rig.own, (2, 36, 6, 24), reference="support_empty")
    for got, state in (
        (default, "not_supplied"),
        (bad, "series_mismatch"),
        (text, "unavailable_support_empty"),
    ):
        assert got.reference is not None and got.reference.state == state
        assert got.window_rc == (2, 40, 6, 24) and "femur_footprint" in got.scope_reason
        assert got.light == pytest.approx(100.0)
        assert got.code == "identified"


def test_local_geometry_still_required_and_miss_history_survives(rig):
    ref = make_ref(rig.own)
    with computing(), recording() as led:
        got = ask(rig.own, (30, 45, 6, 24), reference=ref)
        names = {e.name for e in led.events()}
    assert rig.seen["lens"] == [(15, 18), (48, 40)]  # local miss, then the broadening
    assert got.scope_code == "broadened_full_frame_local_scope_missed"
    assert got.window_rc is None and got.code == "identified"
    (attempt,) = got.attempts
    assert attempt.window_rc == (30, 45, 6, 24)  # footprints did not widen the attempt
    assert attempt.code != "identified"
    assert got.light == 98.0 and got.reference.state == "usable"
    assert "patella.scope_broadened" in names


def test_without_a_profile_domain_the_whole_frame_is_read_with_the_reference(rig):
    ref = make_ref(rig.own)
    with computing(), recording():
        got = ask(rig.own, None, reference=ref)
    assert rig.seen["lens"] == [SHAPE] and got.attempts == ()
    assert got.scope_code == "full_frame_no_profile_or_map_domain"
    assert got.light == 98.0


# ---- recess callers --------------------------------------------------------------------------


@pytest.fixture
def recess_rig(monkeypatch, rig):
    own = rig.own
    pointed = _objects()
    own.arrays["a3_patella_plane_objects"] = np.stack([pointed])
    seen: dict[str, list] = {"white": [], "patella": []}

    def white(plane, objects, measures=None, reference_light=None):
        seen["white"].append(reference_light)

    def patella(*args, **kwargs):
        seen["patella"].append((args, kwargs))
        return SimpleNamespace(objects=pointed.copy(), labels=None, available=None)

    monkeypatch.setattr(run, "white_as_fluid", white)
    monkeypatch.setattr(run, "patella_plane", patella)
    monkeypatch.setattr(run, "measures_of", lambda *a: "measures")
    leg = SimpleNamespace(femur_lps=np.zeros((1, 3)), tibia_lps=np.zeros((1, 3)))
    return SimpleNamespace(own=own, seen=seen, leg=leg)


def test_anterior_fallback_gets_profile_window_reference_and_no_invented_centre(
    recess_rig,
):
    own, seen = recess_rig.own, recess_rig.seen
    ref = make_ref(own)
    got = run.recess_anterior_plane(
        cast(Any, own), 2, cast(Any, recess_rig.leg), ("f", "t"), {}, ("fluid",),
        ref, (2, 10, 3, 9),
    )  # fmt: skip
    ((args, kwargs),) = seen["patella"]
    assert len(args) == 7 and args[6] == "recess" and args[5] is None
    assert kwargs == {"profile_window": (2, 10, 3, 9), "reference": ref}
    assert seen["white"] == [96.0]  # the combined bones light, not remeasured
    assert got.reference is not None and got.reference.state == "usable"
    assert got.source == run.RECESS_SOURCES[2] and got.code == "read"


def test_anterior_without_reference_or_window_is_unchanged(recess_rig):
    own, seen = recess_rig.own, recess_rig.seen
    got = run.recess_anterior_plane(
        cast(Any, own), 2, cast(Any, recess_rig.leg), ("f", "t"), {}, ("fluid",)
    )
    ((_, kwargs),) = seen["patella"]
    assert kwargs == {"profile_window": None, "reference": None}
    assert seen["white"] == [None]
    assert got.reference is not None and got.reference.state == "not_supplied"


def test_saved_patella_row_is_reused_and_still_uses_the_reference(recess_rig):
    own, seen = recess_rig.own, recess_rig.seen
    ref = make_ref(own)
    got = run.recess_anterior_plane(
        cast(Any, own),
        2,
        cast(Any, recess_rig.leg),
        ("f", "t"),
        {2: 0},
        ("fluid",),
        ref,
    )
    assert seen["patella"] == []  # no second pointed read
    assert got.source == run.RECESS_SOURCES[0] and got.source_row == 0
    assert seen["white"] == [96.0]
    mismatched = replace(ref, middle_z=7)
    run.recess_anterior_plane(
        cast(Any, own), 2, cast(Any, recess_rig.leg), ("f", "t"), {2: 0}, ("fluid",),
        mismatched,
    )  # fmt: skip
    assert seen["white"] == [96.0, None]  # incompatible: per-point calibration


def test_side_plane_uses_the_validated_reference(recess_rig, monkeypatch):
    own, seen = recess_rig.own, recess_rig.seen
    monkeypatch.setattr(
        run, "lens_of", lambda *a, **k: (None, SimpleNamespace(dark=None), None)
    )
    monkeypatch.setattr(run, "field_of", lambda *a, **k: SimpleNamespace(leg=None))
    ref = make_ref(own)
    objects = _objects()
    got = run.recess_side_plane(cast(Any, own), 2, objects, 0, ("fluid",), ref)
    assert seen["white"] == [96.0]
    assert got.reference is not None and got.reference.state == "usable"
    run.recess_side_plane(cast(Any, own), 2, objects, 0, ("fluid",))
    assert seen["white"] == [96.0, None]
    mismatched = run.recess_side_plane(
        cast(Any, own), 2, objects, 0, ("fluid",), replace(ref, source_series_uid="x")
    )
    assert mismatched.reference is not None
    assert mismatched.reference.state == "series_mismatch"  # fmt: skip


def test_recess_window_is_taken_only_from_a_read_valid_profile_row():
    profile = SimpleNamespace(
        window_rc=np.array(
            [[1, 5, 2, 8], [-1, -1, -1, -1], [3, 3, 0, 4], [1, 5, 2, 8]]
        ),
        status={
            run.FLUID: np.array(
                [run.JOINT_BODY, run.JOINT_NOT_READ, run.JOINT_BODY, run.JOINT_NOT_READ]
            )
        },
    )
    assert run.recess_profile_window(profile, 0) == (1, 5, 2, 8)
    assert run.recess_profile_window(profile, 1) is None
    assert run.recess_profile_window(profile, 2) is None
    assert run.recess_profile_window(profile, 3) is None
    assert run.recess_profile_window(profile, 9) is None
    assert run.recess_profile_window(SimpleNamespace(), 0) is None


def test_read_recess_keeps_the_native_reference_beside_the_unchanged_calibration(
    monkeypatch,
):
    uid = "anterior-series"
    frame = run.PlaneFrame(
        np.zeros(3), np.asarray([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]]), (1.0, 1.0)
    )
    objects = np.zeros((3, 3), dtype=np.int8)
    objects[0, 0] = objects[1, 1] = FEMUR
    objects[2, 2] = TIBIA
    volume = np.ones((3, 3, 3), dtype=float)

    class Measures:
        @staticmethod
        def light(mask):
            return float(np.count_nonzero(mask) * 10)

    series = SimpleNamespace(
        row=SimpleNamespace(series_uid=uid, fat_suppression="1", fluid_sensitive="1"),
        volume=volume,
        geometry=SimpleNamespace(
            position=[np.asarray([0.0, 0.0, float(z)]) for z in range(3)]
        ),
        slice_thickness_mm=[1.0, 1.0, 1.0],
    )
    own = SimpleNamespace(
        series=series,
        record={
            "series_uid": uid,
            "slice_index": 1,
            "background_split": 50.0,
            "assignments": {"knee": "R", "femur": 1, "tibia": 2, "codes": {}},
            "patella": {"pointed_planes": []},
        },
        arrays={
            "a1_objects": objects,
            "acquired_plane": volume[1],
            "b1_available": np.ones((3, 3), bool),
        },
        stack=SimpleNamespace(code="present"),
        assignment=SimpleNamespace(in_plane=(False, True, True)),
        frame=frame,
    )
    leg = run.Leg(
        np.asarray([[1.0, 1.0, 1.0]]), np.asarray([[0.0, 0.0, -5.0]]), None, None,
        np.asarray([[1.0, 2.0, 3.0]]), identity="ctx",
    )  # fmt: skip
    status = np.full(3, run.JOINT_NOT_READ, dtype=np.int8)
    profile = run.JointProfile(
        names=(run.FLUID,),
        status={run.FLUID: status},
        area_mm2={run.FLUID: np.zeros(3, dtype=float)},
        seen_blocks=np.zeros((3, 1), dtype=np.int32),
        unseen_blocks=np.zeros((3, 1), dtype=np.int32),
        corridor_px=np.zeros(3, dtype=np.int32),
        corridor=np.zeros((3, 1, 1), dtype=bool),
        could={run.FLUID: np.zeros((3, 1, 1), dtype=bool)},
        window_rc=np.zeros((3, 4), dtype=np.int32),
        cell_mm=np.ones((3, 2), dtype=float),
        block_px=np.ones((3, 2), dtype=np.int32),
        fine=(),
        level={run.FLUID: (10.0, 20.0)},
    )
    monkeypatch.setattr(run, "measures_of", lambda *args: Measures())
    monkeypatch.setattr(run, "levels", lambda *args: {run.FLUID: (10.0, 20.0)})
    monkeypatch.setattr(
        run, "recess_corridor",
        lambda *args: (lambda z, plane, shape: np.ones(shape, bool), {"frame": "test"}),
    )  # fmt: skip
    monkeypatch.setattr(run, "joint_profile", lambda *args, **kwargs: profile)
    with run.recording(), run.computing():
        result = run.read_recess(
            cast(run.Measured, own), None, leg, np.asarray([1.0, 2.0, 3.0]), {}
        )
    assert isinstance(result, run.RecessRead)
    reference = result.record["native_reference"]
    assert reference["state"] == "available"
    assert reference["femur_light"] == 20.0 and reference["bones_light"] == 30.0
    assert reference["support_address"] == "a1_objects"
    assert reference["support_codes"] == [FEMUR, TIBIA]
    assert (
        reference["source_series_uid"] == uid and reference["native_middle_slice"] == 1
    )
    calibration = result.record["profile_calibration"]
    assert calibration["method"] == "acquired_light_over_native_named_middle_bone_masks"
    assert calibration["femur_light"] == 20.0 and calibration["bones_light"] == 30.0
