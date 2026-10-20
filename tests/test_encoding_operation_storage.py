from pathlib import Path

import numpy as np
import pytest

from knee.array_archive import write_npz_xz
from knee.collapse.anatomical_relations import relationships_for
from knee.encoding import h5_store
from knee.encoding.operation import encode_study, validate_spec
from knee.encoding.places import MetricKind
from knee.encoding.product import open_product
from knee.json_store import load_json
from knee.receipt import digest


def make_spec(**extra):
    spec = {
        "version": "v1",
        "banks": [
            {
                "name": "b",
                "facet": "f",
                "metrics": [{"name": "m", "kind": MetricKind.DIGIT.value}],
            }
        ],
        "profiles": [
            {
                "object": "obj",
                "provenance": "native",
                "kind": "resolved",
                "support": "mask",
                "readings": [
                    {"bank": "b", "metric": "m", "value": "val", "available": "av"}
                ],
            }
        ],
    }
    spec.update(extra)
    return spec


def make_study(tmp_path):
    run, main = tmp_path / "run", tmp_path / "main"
    run.mkdir(parents=True)
    main.mkdir(parents=True)
    mask = np.zeros((3, 3), dtype=bool)
    mask[0, 0] = mask[1, 1] = mask[2, 1] = True
    arrs = {
        "mask": mask,
        "val": np.arange(9, dtype=np.float32).reshape(3, 3),
        "av": np.ones((3, 3), dtype=bool),
    }
    write_npz_xz(run / "a.npz.xz", arrs.items())
    record = {
        "study_uid": "st",
        "series_uid": "s1",
        "artifact": "a.npz.xz",
        "slice_index": 0,
        "view": ["Axial", "1", "1"],
        "arrays": {k: {"digest": digest(v)} for k, v in arrs.items()},
        "observations": [
            {
                "object": "obj",
                "provenance": "native",
                "kind": "resolved",
                "support": "mask",
                "artifact": "a.npz.xz",
                "series_uid": "s1",
                "view": ["Axial", "1", "1"],
                "slices": [0],
            }
        ],
    }
    return run, main, record


def run_once(tmp_path, out_dir, spec):
    run, main, record = make_study(tmp_path / out_dir)
    result = {"study_uid": "st", "records": [record], "main_records": [], "objects": {}}
    out = tmp_path / out_dir / "out" / "enc.json.xz"
    out.parent.mkdir()
    return encode_study(result, run, main, spec, out), out, result


def test_default_storage_and_validation():
    assert validate_spec(make_spec())["storage"] == "npz_xz"
    assert validate_spec(make_spec(storage="npz_xz"))["storage"] == "npz_xz"
    assert validate_spec(make_spec())["h5_compact"] is False


@pytest.mark.parametrize("bad", [None, 0, 1, "true", [], {}])
def test_compact_h5_requires_an_explicit_boolean(bad):
    with pytest.raises(TypeError, match="h5_compact_must_be_bool"):
        validate_spec(make_spec(h5_compact=bad))


def test_real_encoding_publishes_definition_role_and_actual_support_ownership(tmp_path):
    run, main, record = make_study(tmp_path)
    record["observations"][0]["object"] = "acl"
    relations = relationships_for(("acl", "femur", "tibia"))["acl"]
    spec = make_spec(storage="h5", h5_compact=True, authored_definition_context=True)
    spec["profiles"][0]["object"] = "acl"
    prepared = validate_spec(spec)
    result = {
        "study_uid": "st",
        "records": [record],
        "main_records": [],
        "objects": {"acl": {"anatomical_relations": relations}},
    }
    status = encode_study(
        result,
        run,
        main,
        prepared["spec"],
        tmp_path / "encoding.json.xz",
        prepared=prepared,
    )
    with open_product(status["manifest"]) as product:
        definition = product.manifest["definition_context"]
        item = definition["objects"]["acl"]
        assert definition["role"] == "anatomical_definition"
        assert item["status"] == "ok"
        assert item["coordinates"] is None
        assert item["original_relations"] == relations
        assert product.arrays[item["counts"]].sum() == 1
        assert product.arrays[item["carrier_vector"]].shape == (1, 512)
        ownership = product.manifest["support_ownership"]["acl"]
        assert ownership["physical_volume"] == "not_measured"
        assert len(ownership["addressed_supports"]) == 1
        link = ownership["addressed_supports"][0]["links"][0]
        assert link["address_kind"] == "native_rc"
        assert link["place_count"] == 3
        assert product.arrays[link["coordinate_member"]].tolist() == [
            [0, 0],
            [1, 1],
            [2, 1],
        ]
    assert result["objects"]["acl"]["encoding_definition_context"]["status"] == "ok"


def test_explicit_compact_h5_uses_public_product_path_without_changing_arrays(tmp_path):
    h5py = pytest.importorskip("h5py")
    legacy, _, _ = run_once(tmp_path, "old", make_spec(storage="h5"))
    compact, _, _ = run_once(tmp_path, "new", make_spec(storage="h5", h5_compact=True))
    with h5py.File(compact["manifest"], "r") as store:
        assert store.attrs["schema_version"] == 3
    with (
        open_product(legacy["manifest"]) as old,
        open_product(compact["manifest"]) as new,
    ):
        assert list(old.arrays) == list(new.arrays)
        assert old.manifest["profiles"] == new.manifest["profiles"]
        assert old.manifest["encoded_arrays"] == new.manifest["encoded_arrays"]
        for key in old.arrays:
            before, after = old.arrays[key], new.arrays[key]
            assert before.dtype.str == after.dtype.str
            assert before.shape == after.shape
            assert before.tobytes(order="C") == after.tobytes(order="C")


def test_explicit_byte_encoding_uses_real_consumer_and_keeps_legacy_arrays(tmp_path):
    h5py = pytest.importorskip("h5py")
    spec = make_spec(storage="h5", h5_encoding="byte_xor")
    assert validate_spec(spec)["h5_encoding"] == "byte_xor"
    legacy, _, _ = run_once(tmp_path, "legacy-bytes", make_spec(storage="h5"))
    encoded, _, _ = run_once(tmp_path, "row-bytes", spec)
    with h5py.File(encoded["manifest"], "r") as stored:
        assert stored.attrs["schema_version"] == 4
    with (
        open_product(legacy["manifest"]) as before,
        open_product(encoded["manifest"]) as after,
    ):
        assert before.manifest["profiles"] == after.manifest["profiles"]
        assert before.manifest["encoded_arrays"] == after.manifest["encoded_arrays"]
        assert list(before.arrays) == list(after.arrays)
        for key in before.arrays:
            a, b = before.arrays[key], after.arrays[key]
            assert a.dtype.str == b.dtype.str
            assert a.shape == b.shape
            assert a.tobytes(order="C") == b.tobytes(order="C")


def test_explicit_modular_h5_encoding_uses_real_consumer_and_public_product(tmp_path):
    h5py = pytest.importorskip("h5py")
    spec = make_spec(storage="h5", h5_encoding="modular_hybrid")
    assert validate_spec(spec)["h5_encoding"] == "modular_hybrid"
    legacy, _, _ = run_once(tmp_path, "legacy-modular", make_spec(storage="h5"))
    encoded, _, _ = run_once(tmp_path, "modular-hybrid", spec)
    with h5py.File(encoded["manifest"], "r") as stored:
        assert stored.attrs["schema_version"] == 5
    with (
        open_product(legacy["manifest"]) as before,
        open_product(encoded["manifest"]) as after,
    ):
        assert before.manifest["profiles"] == after.manifest["profiles"]
        assert before.manifest["encoded_arrays"] == after.manifest["encoded_arrays"]
        assert list(before.arrays) == list(after.arrays)
        for key in before.arrays:
            left, right = before.arrays[key], after.arrays[key]
            assert left.dtype.str == right.dtype.str
            assert left.shape == right.shape
            assert left.tobytes(order="C") == right.tobytes(order="C")


@pytest.mark.parametrize("value", [None, True, 3, [], {}, "future"])
def test_unknown_h5_encoding_is_refused_before_publication(value):
    with pytest.raises(ValueError, match="invalid_h5_encoding"):
        validate_spec(make_spec(storage="h5", h5_encoding=value))


@pytest.mark.parametrize("encoding", ["byte_xor", "modular_hybrid"])
def test_conflicting_h5_encodings_are_refused(encoding):
    with pytest.raises(ValueError, match="conflicting_h5_encoding"):
        validate_spec(make_spec(storage="h5", h5_encoding=encoding, h5_compact=True))


def test_npz_storage_can_keep_an_inactive_h5_codec(tmp_path):
    status, _, _ = run_once(tmp_path, "npz-codec", make_spec(h5_encoding="byte_xor"))
    assert status["archive"].endswith(".npz.xz")
    with open_product(status["manifest"]) as product:
        assert list(product.arrays) == list(product.manifest["encoded_arrays"])


@pytest.mark.parametrize("bad", ["zip", "H5", "", 5, None, ["h5"]])
def test_invalid_storage_fails_in_validate_spec(bad):
    with pytest.raises(ValueError, match="invalid_encoding_storage"):
        validate_spec(make_spec(storage=bad))


def test_h5_unavailable_fails_before_any_output(tmp_path, monkeypatch):
    def missing():
        raise h5_store.OptionalDependencyError("no h5py")

    monkeypatch.setattr(h5_store, "_h5py", missing)
    with pytest.raises(
        h5_store.OptionalDependencyError, match="h5_storage_unavailable"
    ):
        validate_spec(make_spec(storage="h5"))
    run, main, record = make_study(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    with pytest.raises(h5_store.OptionalDependencyError):
        encode_study(
            {"study_uid": "st", "records": [record], "main_records": [], "objects": {}},
            run,
            main,
            make_spec(storage="h5"),
            out / "enc.json.xz",
        )
    assert list(out.iterdir()) == []


def test_legacy_default_outputs_and_return_keys(tmp_path):
    status, out, result = run_once(tmp_path, "legacy", make_spec())
    assert set(status) == {"manifest", "archive", "profiles", "work"}
    assert status["manifest"] == str(out)
    assert status["archive"].endswith("enc.npz.xz")
    assert sorted(p.name for p in out.parent.iterdir()) == ["enc.json.xz", "enc.npz.xz"]
    manifest = load_json(out)
    assert manifest["archive"] == status["archive"]
    link = result["objects"]["obj"]["encoding"][0]
    assert link["manifest"] == str(out) and link["archive"] == status["archive"]
    with open_product(out) as p:
        assert p.manifest == manifest
        assert list(p.arrays) == list(manifest["encoded_arrays"])
        for k, e in manifest["encoded_arrays"].items():
            assert digest(p.arrays[k]) == e["digest"]


def test_explicit_npz_xz_is_equivalent_to_omission(tmp_path):
    s1, out1, _ = run_once(tmp_path, "a", make_spec())
    s2, out2, _ = run_once(tmp_path, "b", make_spec(storage="npz_xz"))
    with open(s1["archive"], "rb") as first, open(s2["archive"], "rb") as second:
        assert first.read() == second.read()
    m1, m2 = load_json(out1), load_json(out2)
    for m in (m1, m2):
        for key in ("spec", "spec_sha256", "archive", "source_roots"):
            m.pop(key)
    assert m1 == m2


def test_h5_single_product_same_manifest_and_arrays(tmp_path):
    pytest.importorskip("h5py")
    s_leg, out_leg, _ = run_once(tmp_path, "legacy", make_spec())
    s_h5, out_h5, result = run_once(tmp_path, "h5", make_spec(storage="h5"))

    h5_file = out_h5.parent / "enc.h5"
    assert s_h5["manifest"] == s_h5["archive"] == str(h5_file)
    assert set(s_h5) == set(s_leg)
    assert [p.name for p in out_h5.parent.iterdir()] == [
        "enc.h5"
    ]  # no duplicate products
    link = result["objects"]["obj"]["encoding"][0]
    assert link["manifest"] == link["archive"] == str(h5_file)

    legacy = load_json(out_leg)
    with open_product(h5_file) as p_h5, open_product(out_leg) as p_leg:
        h5m = p_h5.manifest
        assert h5m["archive"] == str(h5_file)
        assert h5m["spec"] == {**legacy["spec"], "storage": "h5"}
        # Every other field and meaning is unchanged (source roots differ only by tmp dir).
        skip = {"archive", "spec", "spec_sha256", "source_roots"}
        assert {k: v for k, v in h5m.items() if k not in skip} == {
            k: v for k, v in legacy.items() if k not in skip
        }
        assert h5m["encoded_arrays"]  # emitted arrays exist
        assert list(p_h5.arrays) == list(p_leg.arrays)
        for k, e in h5m["encoded_arrays"].items():
            a, b = p_h5.arrays[k], p_leg.arrays[k]
            assert digest(a) == digest(b) == e["digest"]
            assert a.dtype == b.dtype and a.shape == b.shape


@pytest.mark.parametrize("storage", ["npz_xz", "h5"])
def test_relative_output_addresses_reopen_product_without_cwd_fallback(
    tmp_path, monkeypatch, storage
):
    pytest.importorskip("h5py") if storage == "h5" else None
    run, main, record = make_study(tmp_path / "source")
    monkeypatch.chdir(tmp_path)
    result = {"study_uid": "st", "records": [record], "main_records": [], "objects": {}}
    output = Path("relative-product/out/enc.json.xz")
    status = encode_study(result, run, main, make_spec(storage=storage), output)
    assert Path(status["manifest"]).is_absolute()
    assert Path(status["archive"]).is_absolute()
    with open_product(status["manifest"]) as product:
        assert Path(product.manifest["archive"]).is_absolute()
        assert list(product.arrays) == list(product.manifest["encoded_arrays"])
