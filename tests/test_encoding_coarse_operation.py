"""Coarse-block family through the real validate_spec / encode_study path."""

from __future__ import annotations

import copy

import numpy as np
import pytest

from knee.array_archive import open_arrays, write_npz_xz
from knee.encoding.mri_coarse_spec import make_mri_coarse_spec
from knee.encoding.operation import encode_study, validate_spec
from knee.json_store import load_json
from knee.receipt import digest

STUDY = "study-1"
VIEW = ["Axial", "1", "1"]
TOKEN = "{arrays_prefix}"
PX = "a4_patella_coarse"
PAT_ART = "study-1/AX-patella.npz.xz"
FIB_ART = "study-1/HOLDER-fibula.npz.xz"
SL = (5, 7)
ROWS = (
    {
        "slice": 5,
        "window": (0, 10, 0, 10),
        "px": (4, 4),
        "mm": (2.0, 2.0),
        "body": {(0, 0), (1, 1), (2, 2)},
        "seeds": {(0, 1), (2, 0)},
    },
    {
        "slice": 7,
        "window": (2, 6, 3, 9),
        "px": (2, 3),
        "mm": (2.0, 3.0),
        "body": {(1, 1)},
        "seeds": {(0, 0), (1, 0)},
    },
)
BANKS = [
    {
        "name": "b",
        "facet": "f",
        "metrics": [
            {"name": "flag", "kind": "words", "words": ["False", "True"]},
            {"name": "med", "kind": "digit"},
        ],
    }
]
REFS = [
    {
        "bank": "b",
        "metric": "med",
        "reference_id": "r",
        "source": "declared test reference",
        "units": "a.u.",
        "low": 1,
        "high": 5,
    }
]


# ---------------------------------------------------------------- fixtures
def packed(prefix, bone):
    grids = {"body": [], "seeds": []}
    shapes = []
    for r in ROWS:
        g = (
            -(-(r["window"][1] - r["window"][0]) // r["px"][0]),
            -(-(r["window"][3] - r["window"][2]) // r["px"][1]),
        )
        shapes.append(g)
        for key, packed_rows in grids.items():
            grid = np.zeros(g, bool)
            for i, j in r[key]:
                grid[i, j] = True
            packed_rows.append(grid.ravel())
    sizes = [a * b for a, b in shapes]
    n = sum(sizes)
    median = np.arange(n, dtype=np.float32) + 1.0
    median[4] = np.nan  # row 0 block (1, 1)
    labels = np.zeros(n, np.int8)
    labels[[0, 8]] = 2
    labels[1] = 1
    avail = np.zeros(n, bool)
    avail[0] = True
    data = {
        "offsets": np.concatenate(([0], np.cumsum(sizes))).astype(np.int64),
        "shapes": np.array(shapes, np.int32),
        "slices": np.array([r["slice"] for r in ROWS], np.int32),
        "windows_rc": np.array([r["window"] for r in ROWS], np.int32),
        "block_px": np.array([r["px"] for r in ROWS], np.int32),
        "block_mm": np.array([r["mm"] for r in ROWS], np.float64),
        "median": median,
        f"{bone}_body": np.concatenate(grids["body"]),
        f"{bone}_seeds": np.concatenate(grids["seeds"]),
        "labels": labels,
        "avail": avail,
        "badavail": np.zeros(n, np.int8),
        "cplx": np.ones(n, np.complex64),
        "origin_lps": np.zeros((2, 3)),
        "basis_lps": np.broadcast_to(np.eye(3)[:, :2], (2, 3, 2)).copy(),
    }
    return {f"{prefix}_{k}": v for k, v in data.items()}


def obs(obj, uid, view, artifact, support, row, slice_, count=None, label=None):
    return {
        "object": obj,
        "provenance": "native",
        "kind": "reading",
        "series_uid": uid,
        "view": list(view),
        "slices": [slice_],
        "code": "section",
        "count": count,
        "off_plane_mm": 0.0,
        "support": support,
        "note": "",
        "artifact": artifact,
        "row": row,
        "label": label,
    }


def record_of(arrays, uid, view, artifact, observations, **extra):
    record = {
        "study_uid": STUDY,
        "series_uid": uid,
        "view": list(view),
        "slice_index": 5,
        "artifact": artifact,
        "arrays": {k: {"digest": digest(v)} for k, v in arrays.items()},
        "observations": observations,
    }
    record.update(extra)
    return record


def patella(support="patella_body", rows=(0, 1)):
    arrays = packed(PX, "patella")
    observations = [
        obs("patella", "AX", VIEW, PAT_ART, f"{PX}_{support}", r, SL[r]) for r in rows
    ]
    return record_of(arrays, "AX", VIEW, PAT_ART, observations), arrays


def layout_decl(prefix, packed_names, **over):
    decl = {
        "family": "native_coarse_blocks",
        "offsets": f"{prefix}_offsets",
        "shapes": f"{prefix}_shapes",
        "slices": f"{prefix}_slices",
        "windows_rc": f"{prefix}_windows_rc",
        "block_px": f"{prefix}_block_px",
        "block_mm": f"{prefix}_block_mm",
        "packed_arrays": [f"{prefix}_{n}" for n in packed_names],
    }
    decl.update(over)
    return decl


def readings(
    prefix, flag="patella_body", med="median", policy="finite_values", avail=None
):
    med_reading = {"bank": "b", "metric": "med", "value": f"{prefix}_{med}"}
    if avail:
        med_reading["available"] = f"{prefix}_{avail}"
    else:
        med_reading["availability_policy"] = policy
    return [
        {
            "bank": "b",
            "metric": "flag",
            "value": f"{prefix}_{flag}",
            "availability_policy": "all_stored",
        },
        med_reading,
    ]


def profile(obj, support, layout, rds):
    return {
        "object": obj,
        "provenance": "native",
        "kind": "reading",
        "support": support,
        "readings": rds,
        "references": copy.deepcopy(REFS),
        "support_layout": layout,
    }


def make_spec(profiles):
    return {"version": "coarse-v1", "banks": copy.deepcopy(BANKS), "profiles": profiles}


EXTRAS = ["avail", "badavail", "cplx", "labels"]


def patella_spec(support="patella_body", extras=(), rds=None, **over):
    names = ["median", "patella_body", "patella_seeds", *extras]
    layout = layout_decl(PX, names, **over)
    return make_spec(
        [
            profile(
                "patella",
                f"{PX}_{support}",
                layout,
                rds or readings(PX, flag="patella_body"),
            )
        ]
    )


def fibula(targets=(("T-A", "pfx_a"), ("T-B", "pfx_b"))):
    arrays, planes, observations = {}, {}, []
    for uid, pfx in targets:
        arrays.update(packed(pfx, "fibula"))
        planes[uid] = {
            "orientation": "axial",
            "arrays_prefix": pfx,
            "slices_read": list(SL),
        }
        for kind, counts in (("body", (3, 1)), ("seeds", (2, 2))):
            for row in (0, 1):
                observations.append(
                    obs(
                        "fibula",
                        uid,
                        VIEW,
                        FIB_ART,
                        f"{pfx}_fibula_{kind}",
                        row,
                        SL[row],
                        counts[row],
                    )
                )
    record = record_of(
        arrays,
        "HOLDER",
        ["Sagittal", "0", "0"],
        FIB_ART,
        observations,
        fibula_key_planes=planes,
    )
    return record, arrays


def fibula_spec(kinds=("body", "seeds"), count_meaning="coarse_blocks"):
    profiles = []
    for kind in kinds:
        over = {
            "target_evidence": {
                "record_field": "fibula_key_planes",
                "orientation": "axial",
            }
        }
        if count_meaning:
            over["count_meaning"] = count_meaning
        layout = layout_decl(TOKEN, ["median", "fibula_body", "fibula_seeds"], **over)
        if kind == "body":
            layout["frame_arrays"] = {
                "origin_lps": f"{TOKEN}_origin_lps",
                "basis_lps": f"{TOKEN}_basis_lps",
            }
        profiles.append(
            profile(
                "fibula",
                f"{TOKEN}_fibula_{kind}",
                layout,
                readings(TOKEN, flag=f"fibula_{kind}"),
            )
        )
    return make_spec(profiles)


def go(tmp_path, items, spec):
    run_dir = tmp_path / "run"
    for record, arrays in items:
        path = run_dir / record["artifact"]
        path.parent.mkdir(parents=True, exist_ok=True)
        write_npz_xz(path, arrays)
    result = {
        "study_uid": STUDY,
        "records": [r for r, _ in items],
        "main_records": [],
        "objects": {},
    }
    return encode_study(result, run_dir, tmp_path / "main", spec, tmp_path / "out.json")


def outs(links, index=0):
    return links["profiles"][index]["outcomes"]


def statuses(links, index=0):
    return [o["status"] for o in outs(links, index)]


def metric(outcome, name):
    return next(m for m in outcome["metrics"] if m["metric"] == name)


# ---------------------------------------------------------- validation
def test_builtin_mri_coarse_declarations_bind_all_shared_metrics():
    prepared = validate_spec(make_mri_coarse_spec())
    assert len(prepared["profiles"]) == 462
    assert len(prepared["layout"].banks) == 11
    expected = {
        (bank.name, metric.name)
        for bank in prepared["layout"].banks
        for metric in bank.metrics
    }
    assert all(
        {(row["bank"], row["metric"]) for row in profile["readings"]} == expected
        for profile in prepared["profiles"]
    )
    geometry_names = {
        "offsets",
        "shapes",
        "slices",
        "windows_rc",
        "block_px",
        "block_mm",
    }
    coarse_profiles = [
        profile
        for profile in make_mri_coarse_spec()["profiles"]
        if profile.get("support_layout", {}).get("family") == "native_coarse_blocks"
    ]
    assert coarse_profiles
    for profile in coarse_profiles:
        declaration = profile["support_layout"]
        metadata_names = {declaration[key] for key in geometry_names}
        assert metadata_names.isdisjoint(declaration["packed_arrays"])
        assert declaration["packed_arrays"]
        assert all(
            "median" in name or "depth" in name or "body" in name or "seeds" in name
            for name in declaration["packed_arrays"]
        )


def test_valid_coarse_declarations_compile_without_io():
    patella_prepared = validate_spec(patella_spec())
    assert (
        patella_prepared["profiles"][0]["support_layout"]["family"]
        == "native_coarse_blocks"
    )
    assert (
        validate_spec(fibula_spec())["profiles"][1]["support"]
        == f"{TOKEN}_fibula_seeds"
    )


def _p(s):
    return s["profiles"][0]


MUTATIONS = [
    lambda s: _p(s)["support_layout"].update(extra=1),
    lambda s: _p(s)["support_layout"].pop("block_mm"),
    lambda s: _p(s)["support_layout"].update(offsets=""),
    lambda s: _p(s)["support_layout"].update(offsets=f"{TOKEN}_offsets"),
    lambda s: _p(s)["support_layout"].update(offsets="x_{y}_offsets"),
    lambda s: _p(s)["support_layout"].update(packed_arrays=[]),
    lambda s: _p(s)["support_layout"].update(
        packed_arrays=[f"{PX}_median", f"{PX}_median", f"{PX}_patella_body"]
    ),
    lambda s: _p(s)["support_layout"].update(count_meaning="native_pixels"),
    lambda s: _p(s)["support_layout"].update(frame_arrays={"bad": "x"}),
    lambda s: _p(s)["support_layout"].update(
        target_evidence={"record_field": "other", "orientation": "axial"}
    ),
    lambda s: _p(s).update(support="not_declared"),
    lambda s: _p(s).update(provenance="laid"),
    lambda s: _p(s)["readings"][1].update(value="not_declared"),
    lambda s: _p(s)["readings"][1].update(available=f"{PX}_avail"),  # with policy too
    lambda s: _p(s)["readings"][1].pop("availability_policy"),  # neither
    lambda s: _p(s)["readings"][1].update(availability_policy="any_value"),
    lambda s: _p(s)["readings"][1].update(window=f"{PX}_median"),
    lambda s: _p(s)["readings"].__setitem__(
        1,
        {
            "bank": "b",
            "metric": "med",
            "source": "record_context",
            "path": ["view", 1],
            "scope": "acquisition",
        },
    ),
]


@pytest.mark.parametrize("mutate", MUTATIONS)
def test_malformed_patella_declaration_is_a_named_value_error(mutate):
    spec = patella_spec(extras=("avail",))
    mutate(spec)
    with pytest.raises(ValueError, match="invalid_coarse_layout"):
        validate_spec(spec)


FIBULA_MUTATIONS = [
    lambda s: _p(s)["support_layout"].update(offsets="x_{arrays_prefix}_offsets"),
    lambda s: _p(s)["support_layout"].update(offsets="plain_offsets"),
    lambda s: _p(s)["support_layout"]["target_evidence"].update(orientation=""),
    lambda s: _p(s).update(support="pfx_fibula_body"),
    lambda s: _p(s)["support_layout"]["target_evidence"].update(extra=1),
]


@pytest.mark.parametrize("mutate", FIBULA_MUTATIONS)
def test_malformed_fibula_token_declaration_is_refused(mutate):
    spec = fibula_spec()
    mutate(spec)
    with pytest.raises(ValueError, match="invalid_coarse_layout"):
        validate_spec(spec)


# --------------------------------------------------------------- patella
def test_patella_body_and_seed_rows_keep_coarse_grid_addresses(tmp_path):
    record, arrays = patella()
    record["observations"] += [
        obs("patella", "AX", VIEW, PAT_ART, f"{PX}_patella_seeds", r, SL[r])
        for r in (0, 1)
    ]
    body = patella_spec("patella_body")["profiles"][0]
    seeds = patella_spec("patella_seeds")["profiles"][0]
    seeds["readings"] = readings(PX, flag="patella_seeds")
    links = go(tmp_path, [(record, arrays)], make_spec([body, seeds]))
    load_json(links["manifest"])
    assert statuses(links, 0) == ["ok", "ok"] and statuses(links, 1) == ["ok", "ok"]
    b0, b1 = outs(links, 0)
    s0 = outs(links, 1)[0]
    with open_arrays(links["archive"]) as a:
        c0, c1, sc = (a[o["scope_coordinates"]] for o in (b0, b1, s0))
        bounds0 = a[b0["metadata"]["native_bounds_rc"]]
    assert c0.tolist() == [[0, 0], [1, 1], [2, 2]] and c0.dtype == np.int64
    assert c1.tolist() == [[1, 1]]
    assert sc.tolist() == [[0, 1], [2, 0]]
    assert bounds0.tolist() == [[0, 4, 0, 4], [4, 8, 4, 8], [8, 10, 8, 10]]
    assert b0["address_kind"] == "coarse_grid_rc"
    assert "points_rc" not in b0 and "points_lps" not in b0
    assert b1["metadata"]["scope_address"] == {
        "target_series_uid": "AX",
        "target_view": VIEW,
        "slice_index": 7,
        "window_rc": [2, 6, 3, 9],
        "block_px": [2, 3],
        "block_mm": [2.0, 3.0],
        "grid_shape": [2, 2],
    }
    assert links["work"]["addressed_places"] == 3 + 1 + 2 + 2  # blocks, not pixels


def test_patella_row_codes_follow_finite_values_and_explicit_bool_availability(
    tmp_path,
):
    record, arrays = patella(rows=(0,))
    links = go(tmp_path, [(record, arrays)], patella_spec())
    with open_arrays(links["archive"]) as a:
        assert a[metric(outs(links)[0], "med")["row_codes"]].tolist() == [3, -1, 4]
        assert a[metric(outs(links)[0], "flag")["row_codes"]].tolist() == [1, 1, 1]
    spec = patella_spec(extras=EXTRAS, rds=readings(PX, avail="avail"))
    links = go(tmp_path / "x", [(record, arrays)], spec)
    with open_arrays(links["archive"]) as a:
        assert a[metric(outs(links)[0], "med")["row_codes"]].tolist() == [3, -1, -1]


def test_declared_names_are_exact(tmp_path):
    record, arrays = patella(rows=(0,))
    missing = go(tmp_path / "a", [(record, arrays)], patella_spec("patella_seeds"))
    assert statuses(missing) == ["missing_observation"]
    spec = patella_spec()
    _p(spec)["support_layout"]["offsets"] = f"{PX}_offsetz"
    assert statuses(go(tmp_path / "b", [(record, arrays)], spec)) == ["missing_array"]


def test_exact_integer_label_is_preserved_and_bool_label_refused(tmp_path):
    record, arrays = patella(rows=(0,))
    record["observations"] = [
        obs("patella", "AX", VIEW, PAT_ART, f"{PX}_labels", 0, 5, label=2)
    ]
    spec = patella_spec("labels", extras=("labels",))
    links = go(tmp_path / "a", [(record, arrays)], spec)
    assert statuses(links) == ["ok"]
    with open_arrays(links["archive"]) as a:
        assert a[outs(links)[0]["scope_coordinates"]].tolist() == [[0, 0], [2, 2]]
    record["observations"][0]["label"] = True
    assert statuses(go(tmp_path / "b", [(record, arrays)], spec)) == [
        "invalid_support_label"
    ]


@pytest.mark.parametrize(
    ("meaning", "count", "status", "interpreted", "declared"),
    [
        (None, None, "ok", False, None),
        (None, 999, "ok", False, 999),
        ("coarse_blocks", 3, "ok", True, 3),
        ("coarse_blocks", None, "ok", False, None),
        ("coarse_blocks", 4, "support_count_mismatch", None, None),
        ("coarse_blocks", True, "invalid_support_count", None, None),
    ],
)
def test_count_is_interpreted_only_under_declared_coarse_blocks(
    tmp_path, meaning, count, status, interpreted, declared
):
    record, arrays = patella(rows=(0,))
    record["observations"][0]["count"] = count
    over = {"count_meaning": meaning} if meaning else {}
    links = go(tmp_path, [(record, arrays)], patella_spec(**over))
    outcome = outs(links)[0]
    assert outcome["status"] == status
    if status == "ok":
        meta = outcome["metadata"]
        assert meta["count_interpreted_as_blocks"] is interpreted
        assert meta["declared_count"] == declared
        assert meta["support_block_count"] == 3


@pytest.mark.parametrize(
    ("kw", "expected"),
    [
        ({}, ["ok", "ok"]),
        ({"policy": "all_stored"}, ["availability_policy_dtype_mismatch"] * 2),
        ({"med": "patella_body"}, ["availability_policy_dtype_mismatch"] * 2),
        ({"med": "cplx"}, ["availability_policy_dtype_mismatch"] * 2),
        ({"med": "labels", "policy": "all_stored"}, ["ok", "ok"]),
        ({"avail": "badavail"}, ["availability_array_dtype_mismatch"] * 2),
    ],
)
def test_availability_policies_and_dtypes_are_named_by_the_adapter(
    tmp_path, kw, expected
):
    record, arrays = patella()
    spec = patella_spec(extras=EXTRAS, rds=readings(PX, **kw))
    assert statuses(go(tmp_path, [(record, arrays)], spec)) == expected


@pytest.mark.parametrize(
    "failure", ["missing_array", "missing_digest", "digest_mismatch"]
)
def test_source_failures_are_named(tmp_path, failure):
    record, arrays = patella(rows=(0,))
    name = f"{PX}_median"
    if failure == "missing_array":
        del arrays[name]
    elif failure == "missing_digest":
        del record["arrays"][name]
    else:
        record["arrays"][name]["digest"] = "0" * 64
    assert statuses(go(tmp_path, [(record, arrays)], patella_spec())) == [failure]


# ---------------------------------------------------------------- fibula
def test_fibula_prefix_resolves_per_target_for_body_and_seed_supports(tmp_path):
    record, arrays = fibula()
    links = go(tmp_path, [(record, arrays)], fibula_spec())
    body, seeds = outs(links, 0), outs(links, 1)
    assert [o["status"] for o in body + seeds] == ["ok"] * 8
    assert [o["metadata"]["scope_address"]["target_series_uid"] for o in body] == [
        "T-A",
        "T-A",
        "T-B",
        "T-B",
    ]
    assert [o["metadata"]["support_block_count"] for o in body] == [3, 1, 3, 1]
    assert [o["metadata"]["support_block_count"] for o in seeds] == [2, 2, 2, 2]
    assert all(o["metadata"]["count_interpreted_as_blocks"] for o in body + seeds)
    assert all(o["metadata"]["geometry_status"] == "frame_available" for o in body)
    assert all(o["metadata"]["geometry_status"] == "frame_not_declared" for o in seeds)
    for o, pfx, other in ((body[0], "pfx_a", "pfx_b"), (body[2], "pfx_b", "pfx_a")):
        refs = o["metadata"]["source_refs"]
        assert f"{pfx}_median" in refs and f"{other}_median" not in refs
        assert o["metadata"]["lineage"]["owner_series_uid"] == "HOLDER"
    with open_arrays(links["archive"]) as a:
        assert a[seeds[0]["scope_coordinates"]].tolist() == [[0, 1], [2, 0]]
        assert a[seeds[1]["scope_coordinates"]].tolist() == [[0, 0], [1, 0]]


FIBULA_CASES = [
    (
        "no_summary",
        lambda r: r["fibula_key_planes"].clear(),
        ["target_evidence_missing"] * 2,
    ),
    (
        "other_key",
        lambda r: r.update(fibula_key_planes={"T-X": r["fibula_key_planes"]["T-A"]}),
        ["target_evidence_missing"] * 2,
    ),
    (
        "orientation",
        lambda r: r["fibula_key_planes"]["T-A"].update(orientation="sagittal"),
        ["target_view_mismatch"] * 2,
    ),
    (
        "no_prefix",
        lambda r: r["fibula_key_planes"]["T-A"].pop("arrays_prefix"),
        ["arrays_prefix_mismatch"] * 2,
    ),
    (
        "empty_prefix",
        lambda r: r["fibula_key_planes"]["T-A"].update(arrays_prefix=""),
        ["arrays_prefix_mismatch"] * 2,
    ),
    (
        "int_prefix",
        lambda r: r["fibula_key_planes"]["T-A"].update(arrays_prefix=7),
        ["arrays_prefix_mismatch"] * 2,
    ),
    (
        "other_target_prefix",
        lambda r: r["fibula_key_planes"]["T-A"].update(arrays_prefix="pfx_b"),
        ["arrays_prefix_mismatch"] * 2,
    ),
    (
        "slice_value",
        lambda r: r["fibula_key_planes"]["T-A"].update(slices_read=[5, 9]),
        ["ok", "target_slice_mismatch"],
    ),
    (
        "slice_short",
        lambda r: r["fibula_key_planes"]["T-A"].update(slices_read=[5]),
        ["ok", "target_slice_mismatch"],
    ),
    (
        "bool_row",
        lambda r: r["observations"][0].update(row=True),
        ["invalid_packed_row", "ok"],
    ),
    (
        "far_row",
        lambda r: r["observations"][1].update(row=9),
        ["ok", "target_slice_mismatch"],
    ),
    (
        "owner_artifact",
        lambda r: [
            o.update(artifact="study-1/other.npz.xz") for o in r["observations"]
        ],
        ["ordinary_source_owner_record_missing"] * 2,
    ),
    (
        "target_view",
        lambda r: [o.update(view=["Sagittal", "0", "0"]) for o in r["observations"]],
        ["target_view_mismatch"] * 2,
    ),
    (
        "count",
        lambda r: r["observations"][0].update(count=4),
        ["support_count_mismatch", "ok"],
    ),
]


@pytest.mark.parametrize(
    ("name", "mutate", "expected"), FIBULA_CASES, ids=[c[0] for c in FIBULA_CASES]
)
def test_fibula_evidence_mismatches_are_named_not_silent(
    tmp_path, name, mutate, expected
):
    record, arrays = fibula(targets=(("T-A", "pfx_a"),))
    mutate(record)
    links = go(tmp_path, [(record, arrays)], fibula_spec(kinds=("body",)))
    assert statuses(links) == expected
    assert "missing_observation" not in statuses(links)


def test_fibula_count_not_interpreted_without_declared_meaning(tmp_path):
    record, arrays = fibula(targets=(("T-A", "pfx_a"),))
    record["observations"][0]["count"] = 99
    links = go(tmp_path, [(record, arrays)], fibula_spec(("body",), count_meaning=None))
    first = outs(links)[0]
    assert first["status"] == "ok"
    assert first["metadata"]["count_interpreted_as_blocks"] is False
    assert first["metadata"]["declared_count"] == 99
    assert first["metadata"]["support_block_count"] == 3


# ------------------------------------------------------ unrelated paths
def test_ordinary_profile_is_unchanged_beside_a_coarse_profile(tmp_path):
    record, arrays = patella(rows=(0,))
    ordinary_art = "study-1/ord.npz.xz"
    ord_arrays = {
        "a1_objects": np.array([[0, 1, 0], [0, 0, 1]], dtype=np.uint8),
        "light_local": np.array([[3, 5], [7, 8]], dtype=np.int16),
        "flag_local": np.ones((2, 2), dtype=bool),
        "valid_local": np.ones((2, 2), dtype=bool),
        "light_window": np.array([0, 2, 1, 3], dtype=np.int32),
    }
    ord_obs = obs(
        "femur", "OR", VIEW, ordinary_art, "a1_objects", None, 0, count=2, label=1
    )
    ord_obs["kind"] = "resolved"
    ord_record = record_of(ord_arrays, "OR", VIEW, ordinary_art, [ord_obs])
    ord_record["slice_index"] = 0

    def ordinary(support):
        return {
            "object": "femur",
            "provenance": "native",
            "kind": "resolved",
            "support": support,
            "readings": [
                {
                    "bank": "b",
                    "metric": "flag",
                    "value": "flag_local",
                    "available": "valid_local",
                    "window": "light_window",
                },
                {
                    "bank": "b",
                    "metric": "med",
                    "value": "light_local",
                    "available": "valid_local",
                    "window": "light_window",
                },
            ],
            "references": copy.deepcopy(REFS),
        }

    spec = make_spec(
        [
            ordinary("a1_objects"),
            ordinary(f"{TOKEN}_a1_objects"),  # no family: literal exact match only
            patella_spec()["profiles"][0],
        ]
    )
    links = go(tmp_path, [(ord_record, ord_arrays), (record, arrays)], spec)
    assert statuses(links, 0) == ["ok"]
    assert statuses(links, 1) == ["missing_observation"]
    assert statuses(links, 2) == ["ok"]
    outcome = outs(links, 0)[0]
    assert outcome.get("address_kind", True)
    assert "points_rc" in outcome and "scope_coordinates" not in outcome
    with open_arrays(links["archive"]) as a:
        assert a[outcome["points_rc"]].tolist() == [[0, 1], [1, 2]]
        assert a[metric(outcome, "med")["row_codes"]].tolist() == [3, 4]
