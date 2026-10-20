import copy
import inspect
from dataclasses import replace
from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest

from knee.collapse.observations import Observation, Unresolved
from knee.collapse.physical import PlaneFrame
from knee.objects import assignments as A
from knee.telemetry import computing, recording
from scripts import run_interiors as ri

STUDY = "STUDY"
AX = np.array([1.0, 0, 0, 0, 1.0, 0])
SAG = np.array([0.0, 1.0, 0.0, 0.0, 0.0, -1.0])
_REAL_SAYINGS = ri.posterior_sayings
CODED = ("mcl", "lcl", "acl")
SUPPORT = {
    "mcl": "a1_objects",
    "lcl": "a1_objects",
    "acl": "a1_objects",
    "sartorius": "a2_sartorius",
    "iliotibial_band": "a2_iliotibial_band",
    "popliteus_tendon": "a2_popliteus_tendon",
    "biceps_femoris_tendon": "a2_biceps_femoris_tendon",
    "tibial_cartilage": "a1_objects",
}
VIEWS = {
    "ax": ("axial", "0", "0"),
    "sag": ("sagittal", "1", "1"),
    "far": ("sagittal", "0", "0"),
}


def _unit_frame(position=(0.0, 0.0, 0.0), orientation=AX, spacing=(1.0, 1.0)):
    return PlaneFrame.from_dicom(np.array(position), orientation, spacing)


def _series(uid, volume, thickness):
    return SimpleNamespace(
        row=SimpleNamespace(series_uid=uid),
        volume=volume,
        slice_thickness_mm=thickness,
        geometry=object(),
        slices=[] if volume is None else list(range(len(volume))),
    )


def _measured(uid, view, series):
    return SimpleNamespace(
        series=series,
        record={"series_uid": uid, "view": view, "slice_index": 0},
        arrays={},
        frame=None,
    )


@pytest.fixture
def world(monkeypatch):
    plane = np.full((40, 40), 10.0)
    plane[20, 9] = 1.0
    plane[20, 13] = 1.0
    frames = {
        "ax": [_unit_frame((0, 0, 0)), _unit_frame((0, 0, 1))],
        "sag": [_unit_frame((2.0 * i, 0, 20), SAG) for i in range(5)],
        "far": [_unit_frame((50.0 + 2.0 * i, 0, 20), SAG) for i in range(5)],
    }
    measured = [
        _measured("ax", VIEWS["ax"], _series("ax", np.zeros((2, 40, 40)), [3.0, 3.0])),
        _measured(
            "sag", VIEWS["sag"], _series("sag", np.stack([plane] * 5), [2.0] * 5)
        ),
        _measured(
            "far", VIEWS["far"], _series("far", np.stack([plane] * 5), [2.0] * 5)
        ),
    ]
    exterior = {"mask": np.zeros((40, 40), dtype=bool)}
    monkeypatch.setattr(ri, "plane_frame", lambda s, z: frames[s.row.series_uid][z])
    monkeypatch.setattr(ri, "finite_of", lambda s: np.isfinite(np.asarray(s.volume)))
    monkeypatch.setattr(ri, "margin_of", lambda uid, z, p: exterior["mask"])
    monkeypatch.setattr(ri, "SQUINT_TILE_MM", 2.0, raising=False)
    five: list = []
    monkeypatch.setattr(
        ri,
        "posterior_sayings",
        lambda record, *a: (
            [],
            [],
            list(five) if record is measured[0].record else [],
            set(),
        ),
    )

    def attach(name, rows, cols, uid="ax", z=0, main=None, on_owner=False, **over):
        mask = np.zeros((40, 40), dtype=bool)
        mask[rows[0] : rows[1], cols[0] : cols[1]] = True
        support = SUPPORT[name]
        code = ri.OBJECT_CODES[name] if name in CODED else None
        array = (
            np.where(mask, code, 0).astype(np.int32)
            if code is not None
            else mask.copy()
        )
        record = {
            "series_uid": uid,
            "view": VIEWS[uid],
            "slice_index": z,
            "assignments": {"codes": {}},
        }
        if main:
            record["main_slice"] = {"object": main}
        artifact = str(ri.artifact_of(STUDY, record))
        row = {
            "object": name,
            "provenance": "native",
            "kind": "resolved",
            "series_uid": uid,
            "view": VIEWS[uid],
            "slices": (z,),
            "code": "identified",
            "count": int(mask.sum()),
            "off_plane_mm": 0.0,
            "support": support,
            "note": "",
            "artifact": artifact,
            "row": None,
            "label": code,
        }
        row.update(over)
        if on_owner:
            owner = next(m for m in measured if m.record["series_uid"] == uid)
            owner.record.setdefault("observations", []).append(row)
        else:
            record["observations"] = [row]
        return ri.PosteriorSource(
            name,
            record,
            {support: array},
            frames[uid][z],
            mask,
            support,
            code,
            artifact,
            int(mask.sum()),
        )

    return SimpleNamespace(
        measured=measured, frames=frames, exterior=exterior, attach=attach, five=five
    )


def _by_uid(world):
    return {m.record["series_uid"]: m for m in world.measured}


def _records(sources):
    return [(s.record, s.arrays) for s in sources]


def _late(world, sources, group=()):
    with recording(), computing():
        return ri.late_native_readings(
            world.measured, list(group), _records(sources), STUDY
        )


def _pair(world):
    # mcl touches both pockets; lcl touches only the one-pixel pocket at (20, 13)
    return [
        world.attach("mcl", (10, 13), (4, 7), main="MCL"),
        world.attach("lcl", (14, 16), (4, 7), main="LCL"),
    ]


# ------------------------------------------------------------ defaults (B8)
def test_default_helpers_are_unchanged(world):
    sig = inspect.signature(ri.posterior_readings_from_sources)
    assert sig.parameters["names"].default == ri.READING_NAMES
    assert sig.parameters["target_planes"].default is None
    src = world.attach("lcl", (10, 13), (4, 7))
    # default call refuses attachment names exactly as B8 refused any non-posterior name
    assert (
        ri._posterior_source_fault(src, _by_uid(world), STUDY)
        == "source_not_a_posterior_reading_object"
    )
    with recording(), computing():
        said = ri.posterior_readings_from_sources(world.measured, [src], STUDY)
    assert said[0][1][0].code == "source_not_a_posterior_reading_object"
    assert said[1] == ([], [])


# ------------------------------------------------------ types, views, filter
def test_mapping_and_competent_view_filter(world):
    assert ri.ATTACHMENT_READING_VIEWS == {
        "mcl": ("sagittal",),
        "lcl": ("sagittal", "axial"),
        "iliotibial_band": ("sagittal", "axial"),
        "popliteus_tendon": ("sagittal", "axial"),
        "biceps_femoris_tendon": ("coronal", "axial"),
        "acl": ("axial", "coronal"),
        "sartorius": ("sagittal", "coronal"),
    }
    none = ri.attachment_target_planes(world.measured, [], STUDY)
    assert {k: set(v) for k, v in none.items()} == {
        k: set(v) for k, v in ri.ATTACHMENT_READING_VIEWS.items()
    }
    axial = [
        world.attach(n, (10, 13), (4, 7), main=n) for n in ri.ATTACHMENT_READING_NAMES
    ]
    got = ri.attachment_target_planes(world.measured, axial, STUDY)
    assert got["mcl"] == {"sagittal"} and got["lcl"] == {"sagittal"}
    assert got["acl"] == {"coronal"} and got["biceps_femoris_tendon"] == {"coronal"}
    assert got["sartorius"] == {"sagittal", "coronal"}
    sagittal = [
        world.attach("mcl", (20, 22), (10, 13), uid="sag", z=2),
        world.attach("lcl", (20, 22), (10, 13), uid="sag", z=2),
        world.attach("acl", (20, 22), (10, 13), uid="sag", z=2),
    ]
    got = ri.attachment_target_planes(world.measured, sagittal, STUDY)
    assert got["mcl"] == frozenset()
    assert got["lcl"] == {"axial"} and got["acl"] == {"axial", "coronal"}
    # an invalid source does not remove a view (unknown is neutral)
    bad = replace(sagittal[0], pixels=1)
    got = ri.attachment_target_planes(world.measured, [bad], STUDY)
    assert got["mcl"] == {"sagittal"}


def test_sagittal_identity_is_not_requeried_but_axial_is(world):
    src = world.attach("lcl", (20, 22), (10, 13), uid="sag", z=2, main="LCL")
    said = _late(world, [src])
    assert said[1] == ([], []) and said[2] == ([], [])
    assert any(o.object == "lcl" for o in said[0][0]) or any(
        u.object == "lcl" for u in said[0][1]
    )


def test_all_seven_types_are_extracted_from_actual_rows(world):
    built = [
        world.attach(n, (10, 13), (4, 7), main=n) for n in ri.ATTACHMENT_READING_NAMES
    ]
    got, lacking = ri.attachment_reading_sources(
        world.measured, [], _records(built), STUDY
    )
    assert lacking == []
    assert {s.name for s in got} == set(ri.ATTACHMENT_READING_NAMES)
    for s in got:
        assert s.support == SUPPORT[s.name] and s.pixels == 9
        assert (s.label is None) == (s.name not in CODED)
        assert (
            ri._posterior_source_fault(s, _by_uid(world), STUDY, ri.ATTACHMENT_ALLOWED)
            is None
        )


def test_extractor_accepts_an_explicit_non_attachment_name(world, monkeypatch):
    assert (
        inspect.signature(ri.attachment_reading_sources).parameters["names"].default
        == ri.ATTACHMENT_READING_NAMES
    )
    uid = "cor"
    view = ("coronal", "2", "2")
    frame = _unit_frame()
    monkeypatch.setitem(world.frames, uid, [frame])
    owner = _measured(uid, view, _series(uid, np.zeros((1, 40, 40)), [2.0]))
    owner.frame = frame
    mask = np.zeros((40, 40), dtype=bool)
    mask[12:15, 8:11] = True
    label = ri.OBJECT_CODES["tibial_cartilage"]
    array = np.where(mask, label, 0).astype(np.int32)
    owner.arrays = {"a1_objects": array}
    owner.record["view"] = view
    artifact = str(ri.artifact_of(STUDY, owner.record))
    owner.record["observations"] = [
        {
            "object": "tibial_cartilage",
            "provenance": "native",
            "kind": "resolved",
            "series_uid": uid,
            "view": view,
            "slices": (0,),
            "code": "identified",
            "count": 9,
            "off_plane_mm": 0.0,
            "support": "a1_objects",
            "note": "",
            "artifact": artifact,
            "row": None,
            "label": label,
        }
    ]

    got, lacking = ri.attachment_reading_sources(
        [owner], [], [], STUDY, names=("tibial_cartilage",)
    )
    assert lacking == [] and [source.name for source in got] == ["tibial_cartilage"]
    source = got[0]
    assert source.frame is frame and source.pixels == 9
    assert (
        ri._posterior_source_fault(source, {uid: owner}, STUDY, ("tibial_cartilage",))
        is None
    )
    # Explicit opt-in validates the source against its native observation; the default
    # posterior-reader API continues to refuse non-posterior names.
    assert (
        ri._posterior_source_fault(source, {uid: owner}, STUDY)
        == "source_not_a_posterior_reading_object"
    )
    assert ri.attachment_reading_sources([owner], [], [], STUDY)[0] == []


def test_present_record_artifact_must_match_but_missing_is_allowed(world):
    source = world.attach("lcl", (10, 13), (4, 7))
    assert "artifact" not in source.record
    assert (
        ri._posterior_source_fault(source, _by_uid(world), STUDY, ri.ATTACHMENT_ALLOWED)
        is None
    )
    mismatched = replace(
        source, record={**source.record, "artifact": "another-address.npz.xz"}
    )
    assert (
        ri._posterior_source_fault(
            mismatched, _by_uid(world), STUDY, ri.ATTACHMENT_ALLOWED
        )
        == "source_artifact_mismatch"
    )
    explicit_missing = replace(source, record={**source.record, "artifact": None})
    assert (
        ri._posterior_source_fault(
            explicit_missing, _by_uid(world), STUDY, ri.ATTACHMENT_ALLOWED
        )
        == "source_artifact_mismatch"
    )


def test_laid_projected_and_absent_rows_are_not_sources(world):
    laid = world.attach("lcl", (10, 13), (4, 7), main="L", provenance="laid")
    proj = world.attach(
        "acl", (10, 13), (4, 7), main="A", provenance="projected", kind="target"
    )
    none = world.attach("mcl", (10, 13), (4, 7), main="M")
    none.record["observations"] = []
    got, lacking = ri.attachment_reading_sources(
        world.measured, [], _records([laid, proj, none]), STUDY
    )
    assert got == [] and lacking == []


def test_unbuildable_row_is_a_named_unknown(world):
    src = world.attach("lcl", (10, 13), (4, 7), main="LCL")
    got, lacking = ri.attachment_reading_sources(
        world.measured, [], [(src.record, {})], STUDY
    )
    assert got == []
    assert lacking == [
        Unresolved(
            "lcl",
            "native",
            "ax",
            VIEWS["ax"],
            "source_support_missing_or_shape_mismatch",
        )
    ]


def test_identity_row_kept_on_the_owner_record_is_found_once(world):
    src = world.attach("lcl", (10, 13), (4, 7), main="LCL", on_owner=True)
    got, lacking = ri.attachment_reading_sources(
        world.measured, [], _records([src]), STUDY
    )
    assert lacking == [] and [s.name for s in got] == ["lcl"]
    assert (
        ri._posterior_source_fault(got[0], _by_uid(world), STUDY, ri.ATTACHMENT_ALLOWED)
        is None
    )


def test_middle_record_row_is_a_source(world):
    m = world.measured[0]
    src = world.attach("iliotibial_band", (10, 13), (4, 7))
    m.frame, m.arrays = world.frames["ax"][0], src.arrays
    m.record["observations"] = [
        {
            **src.record["observations"][0],
            "artifact": str(ri.artifact_of(STUDY, m.record)),
        }
    ]
    got, lacking = ri.attachment_reading_sources(world.measured, [], [], STUDY)
    assert lacking == [] and [s.name for s in got] == ["iliotibial_band"]
    assert (
        ri._posterior_source_fault(got[0], _by_uid(world), STUDY, ri.ATTACHMENT_ALLOWED)
        is None
    )


# --------------------------------------------------------- identity / address
def _row(s, **over):
    return replace(
        s,
        record={**s.record, "observations": [{**s.record["observations"][0], **over}]},
    )


@pytest.mark.parametrize(
    "change,fault",
    [
        (lambda s: s, None),
        (lambda s: replace(s, name="femur"), "source_not_a_posterior_reading_object"),
        (
            lambda s: replace(s, record={**s.record, "slice_index": True}),
            "source_slice_out_of_range",
        ),
        (
            lambda s: replace(s, record={**s.record, "slice_index": 0.5}),
            "source_slice_out_of_range",
        ),
        (lambda s: _row(s, slices=(1,)), "source_observation_slice_mismatch"),
        (lambda s: _row(s, slices=(False,)), "source_observation_slice_mismatch"),
        (lambda s: _row(s, slices=(0, 1)), "source_observation_slice_mismatch"),
        (lambda s: _row(s, slices=0), "source_observation_slice_mismatch"),
        (lambda s: _row(s, view=0), "source_observation_series_mismatch"),
        (lambda s: _row(s, label=99), "source_observation_label_mismatch"),
        (lambda s: _row(s, row=0), "source_observation_row_mismatch"),
        (lambda s: _row(s, count=1), "source_observation_count_mismatch"),
        (lambda s: _row(s, count=True), "source_observation_count_mismatch"),
        (lambda s: _row(s, count=9.0), "source_observation_count_mismatch"),
        (lambda s: _row(s, support="a2_other"), "source_observation_support_mismatch"),
        (lambda s: _row(s, artifact="elsewhere"), "source_observation_missing"),
        (lambda s: _row(s, provenance="laid"), "source_observation_missing"),
        (
            lambda s: replace(s, record={**s.record, "observations": []}),
            "source_observation_missing",
        ),
        (lambda s: replace(s, artifact="elsewhere"), "source_artifact_mismatch"),
        (lambda s: replace(s, label=s.label + 1), "source_label_mismatch"),
        (lambda s: replace(s, pixels=s.pixels + 1), "source_count_mismatch"),
        (
            lambda s: replace(s, arrays={s.support: s.arrays[s.support][:, :5]}),
            "source_support_missing_or_shape_mismatch",
        ),
        (
            lambda s: replace(
                s, arrays={s.support: s.arrays[s.support].astype(np.float32)}
            ),
            "source_support_dtype_mismatch",
        ),
        (
            lambda s: replace(s, record={**s.record, "series_uid": "zzz"}),
            "source_series_not_measured",
        ),
        (lambda s: replace(s, frame=_unit_frame((0, 0, 7))), "source_frame_mismatch"),
    ],
)
def test_coded_source_address_validation(world, change, fault):
    good = world.attach("lcl", (10, 13), (4, 7))
    got = ri._posterior_source_fault(
        change(good), _by_uid(world), STUDY, ri.ATTACHMENT_ALLOWED
    )
    assert got == fault


def test_boolean_support_must_be_boolean_and_owner_uid_must_match(world):
    good = world.attach("sartorius", (10, 13), (4, 7))
    by = _by_uid(world)
    assert ri._posterior_source_fault(good, by, STUDY, ri.ATTACHMENT_ALLOWED) is None
    wrong = replace(
        good, arrays={good.support: good.arrays[good.support].astype(np.uint8)}
    )
    assert (
        ri._posterior_source_fault(wrong, by, STUDY, ri.ATTACHMENT_ALLOWED)
        == "source_support_dtype_mismatch"
    )
    ax = world.measured[0]
    owner = SimpleNamespace(
        series=_series("other-actual", ax.series.volume, [3.0, 3.0]),
        record=ax.record,
        arrays=ax.arrays,
    )
    assert (
        ri._posterior_source_fault(
            good, {"ax": cast(ri.Measured, owner)}, STUDY, ri.ATTACHMENT_ALLOWED
        )
        == "source_series_uid_mismatch"
    )


# --------------------------------------------------- the late pipeline point
def test_late_main_record_source_exists_only_after_late_index_posterior(
    world, monkeypatch
):
    monkeypatch.setattr(ri, "posterior_sayings", _REAL_SAYINGS)
    ax = world.measured[0]
    ax.frame = world.frames["ax"][0]
    ax.record["assignments"] = {"codes": {}}
    mask = np.zeros((40, 40), dtype=bool)
    mask[10:13, 4:7] = True
    record = {
        "series_uid": "ax",
        "view": VIEWS["ax"],
        "slice_index": 0,
        "assignments": {"codes": {"popliteus_tendon": "identified"}},
        "main_slice": {"object": "LCL"},
    }
    arrays = {"a2_popliteus_tendon": mask, "a1_objects": np.zeros((40, 40), np.int8)}
    before, _ = ri.attachment_reading_sources([ax], [], [(record, arrays)], STUDY)
    assert before == []
    ri.index_posterior([ax], (), [(record, arrays)], STUDY, None, False)
    after, lacking = ri.attachment_reading_sources([ax], [], [(record, arrays)], STUDY)
    assert lacking == [] and [s.name for s in after] == ["popliteus_tendon"]
    assert (
        ri._posterior_source_fault(after[0], {"ax": ax}, STUDY, ri.ATTACHMENT_ALLOWED)
        is None
    )


# ------------------------------------------- shared context, crops, named states
def test_overlapping_attachment_and_posterior_queries_share_one_cropped_context(
    world, monkeypatch
):
    seen = []
    real = A.enclosed_darkness

    def spy(plane):
        seen.append(plane.copy())
        return real(plane)

    monkeypatch.setattr(A, "enclosed_darkness", spy)
    five = world.attach(
        "lcl", (10, 13), (4, 7)
    )  # stands in for a posterior source below
    posterior = ri.PosteriorSource(
        "gracilis",
        {
            "series_uid": "ax",
            "view": VIEWS["ax"],
            "slice_index": 0,
            "assignments": {"codes": {"gracilis": "identified"}},
        },
        {
            "a1_objects": np.where(five.mask, ri.OBJECT_CODES["gracilis"], 0).astype(
                np.int32
            )
        },
        world.frames["ax"][0],
        five.mask,
        "a1_objects",
        ri.OBJECT_CODES["gracilis"],
        str(ri.artifact_of(STUDY, {"series_uid": "ax"})),
        int(five.mask.sum()),
    )
    world.five.append(posterior)
    attach = world.attach("lcl", (14, 16), (4, 7), main="LCL")
    said = _late(world, [attach])
    # tied planes 2 and 3: one heavy reading each, two objects each, cropped
    assert [p.shape for p in seen] == [(5, 10), (5, 10)]
    here, missing = said[1]
    assert missing == []
    by = {(o.object, o.slices[0]): o for o in here}
    assert set(by) == {("gracilis", 2), ("gracilis", 3), ("lcl", 2), ("lcl", 3)}
    arrays = world.measured[1].arrays
    stack = arrays[ri.READING_SUPPORT_KEY]
    plane = world.measured[1].series.volume[2]
    r0, r1, c0, c1 = arrays["a22_posterior_context0_window_rc_exclusive"].tolist()
    assert (r0, r1, c0, c1) == (18, 23, 8, 18)
    np.testing.assert_array_equal(
        arrays["a22_posterior_context0_raw"], plane[r0:r1, c0:c1]
    )
    lcl = by[("lcl", 2)]
    contacted = arrays["a22_posterior_context0_m1_lcl_contacted"]
    np.testing.assert_array_equal(stack[lcl.row][r0:r1, c0:c1], contacted)
    assert int(stack[lcl.row].sum()) == int(contacted.sum()) == lcl.count
    # marker-sized one-pixel basin remains available: no minimum area
    assert lcl.count == 1 and {tuple(p) for p in np.argwhere(stack[lcl.row])} == {
        (20, 13)
    }
    g = by[("gracilis", 2)]
    assert {tuple(p) for p in np.argwhere(stack[g.row])} == {(20, 9), (20, 13)}
    assert (lcl.provenance, lcl.kind, lcl.label) == ("native", "reading", None)
    assert lcl.support == ri.READING_SUPPORT_KEY
    assert lcl.artifact == str(ri.artifact_of(STUDY, world.measured[1].record))


def test_boundary_nonfinite_empty_missing_and_ties_are_named(world):
    ext = np.zeros((40, 40), dtype=bool)
    ext[:, 9] = True
    world.exterior["mask"] = ext
    here, _ = _late(world, _pair(world))[1]
    stack = world.measured[1].arrays[ri.READING_SUPPORT_KEY]
    mcl = next(o for o in here if o.object == "mcl" and o.slices == (2,))
    assert {tuple(p) for p in np.argwhere(stack[mcl.row])} == {(20, 13)}
    assert not stack[:, 20, 9].any()


def test_nonfinite_pocket_leaves_a_named_unknown(world):
    world.measured[1].series.volume[:, 20, 13] = np.nan
    here, missing = _late(world, _pair(world))[1]
    assert {o.object for o in here} == {"mcl"}
    assert [(u.object, u.code) for u in missing] == [
        ("lcl", "enclosed_darkness_not_in_source_contact")
    ]


def test_nothing_enclosed_and_far_series_are_named_not_absent(world):
    said = _late(world, _pair(world))
    assert {(u.object, u.code) for u in said[2][1]} == {
        ("mcl", "source_outside_target_slabs"),
        ("lcl", "source_outside_target_slabs"),
    }
    for m in world.measured[1:]:
        m.series.volume[:] = 10.0
    here, missing = _late(world, _pair(world))[1]
    assert here == [] and {u.code for u in missing} == {
        "no_enclosed_darkness_in_query_context"
    }


def test_empty_sources_and_tied_sources(world):
    with recording(), computing():
        assert ri.late_native_readings(world.measured, [], [], STUDY) == [
            ([], []),
            ([], []),
            ([], []),
        ]
    a = world.attach("lcl", (10, 13), (4, 7), z=0, main="A")
    b = world.attach("lcl", (10, 13), (4, 7), z=1, main="B")
    here, _ = _late(world, [a, b])[1]
    assert len(here) == 4 and all("exactly tied largest areas" in o.note for o in here)


def test_invalid_attachment_source_is_retained_not_dropped(world):
    bad = world.attach("lcl", (10, 13), (4, 7), main="LCL")
    bad.record["observations"][0]["count"] = 1
    said = _late(world, [bad])
    assert (
        Unresolved(
            "lcl",
            "native",
            "ax",
            VIEWS["ax"],
            "source_observation_count_mismatch",
        )
        in said[0][1]
    )
    assert said[1] == ([], [])


# ------------------------------------------- once, prefix, grouped output, wiring
def test_one_pass_emits_every_reading_once_and_keeps_the_prefix(world):
    prior = ri.observation_rows(
        [
            Observation(
                "femur",
                "native",
                "resolved",
                "sag",
                VIEWS["sag"],
                (2,),
                "identified",
                5,
                0.0,
                "a1_objects",
                "",
                "STUDY/sag.npz.xz",
                None,
                1,
            )
        ]
    )
    world.measured[1].record["observations"] = copy.deepcopy(prior)
    before = copy.deepcopy([m.record for m in world.measured])
    said = _late(world, _pair(world))
    assert [
        {k: v for k, v in m.record.items() if k != "a22_posterior_readings"}
        for m in world.measured
    ] == before
    here = said[1][0]
    keys = [(o.object, o.slices) for o in here]
    assert len(keys) == len(set(keys)) == 4
    ri.keep_recess(world.measured, said)
    rows = world.measured[1].record["observations"]
    assert rows[: len(prior)] == prior
    readings = [r for r in rows if r["kind"] == "reading"]
    assert (
        len(readings) == 4 and len({(r["object"], r["slices"]) for r in readings}) == 4
    )
    described = ri.describe_objects(
        [m.record for m in world.measured], ri.MAP_NAMES, {}
    )
    assert "source_contacted_enclosed_darkness" in repr(described["lcl"])
    assert ri.READING_SUPPORT_KEY in repr(described["mcl"])


def test_measure_study_calls_the_reading_once_at_the_late_point():
    src = inspect.getsource(ri.measure_study)
    assert "posterior_native_readings(" not in src
    assert src.count("late_native_readings(") == 1
    first_index = src.index("index_posterior(measured, EARLY_MIDDLE_PARTS, group_found")
    joint = src.index("joint_existing(")
    late_index = src.index("(*LATE_MIDDLE_PARTS, *CONTEXT_MIDDLE_PARTS)")
    call = src.index("late_native_readings(")
    appended = src.index("keep_recess(measured, posterior_reading_said)")
    final_save = src.index("save_study_record(run_dir, own.record, own.arrays)")
    assert first_index < joint < late_index < call < appended < final_save
    assert src.count("keep_recess(measured, posterior_reading_said)") == 1
    assert src.count("save_study_record(run_dir, own.record, own.arrays)") == 1
    assert "late_main_records" in src
    assert (
        'reads("posterior_readings", ("observations", "unresolved"), "keep_recess")'
        in src
    )
    assert (
        inspect.getsource(ri.late_native_readings).count(
            "posterior_readings_from_sources("
        )
        == 1
    )
