from __future__ import annotations

import numpy as np
import pytest

from knee.array_archive import open_arrays, write_npz_xz
from knee.encoding.carrier import HadamardCarrier
from knee.encoding.counts import CountBundle
from knee.encoding.handoff import AddressedEncoding
from knee.encoding.operation import _encoding_arrays, encode_study, validate_spec
from knee.encoding.places import EncodingCode, EncodingResult
from knee.json_store import load_json
from knee.receipt import digest


def _spec(*, provenance="native", kind="resolved", support="a1_objects", view=None):
    profile = {
        "object": "femur",
        "provenance": provenance,
        "kind": kind,
        "support": support,
        "readings": [
            {
                "bank": "signal",
                "metric": "light",
                "value": "light_local",
                "available": "valid_local",
                "window": "light_window",
            }
        ],
        "references": [
            {
                "bank": "signal",
                "metric": "light",
                "reference_id": "reference-a",
                "source": "declared test reference",
                "units": "arbitrary intensity",
                "low": 4,
                "high": 6,
            }
        ],
    }
    if view is not None:
        profile["view"] = view
    return {
        "version": "test-v1",
        "banks": [
            {
                "name": "signal",
                "facet": "measured signal",
                "metrics": [{"name": "light", "kind": "digit"}],
            }
        ],
        "profiles": [profile],
    }


def _study(tmp_path, *, wrong_digest=False):
    run_dir = tmp_path / "interiors"
    main_run = tmp_path / "main"
    artifact_rel = "study-1/series-a.npz.xz"
    artifact_path = run_dir / artifact_rel
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    arrays = {
        "a1_objects": np.array([[0, 1, 0], [0, 0, 1]], dtype=np.uint8),
        "light_local": np.array([[3, 5], [7, 8]], dtype=np.int16),
        "valid_local": np.ones((2, 2), dtype=bool),
        "light_window": np.array([0, 2, 1, 3], dtype=np.int32),
    }
    write_npz_xz(artifact_path, arrays)
    digest_map = {name: {"digest": digest(value)} for name, value in arrays.items()}
    if wrong_digest:
        digest_map["light_local"]["digest"] = "0" * 64
    record = {
        "study_uid": "study-1",
        "series_uid": "series-a",
        "view": ["coronal", "fluid", "fat-suppressed"],
        "slice_index": 0,
        "artifact": artifact_rel,
        "arrays": digest_map,
        "plane_frame": {"origin_lps": [1.0, 2.0, 3.0]},
        "observations": [
            {
                "object": "femur",
                "provenance": "native",
                "kind": "resolved",
                "series_uid": "series-a",
                "view": ["coronal", "fluid", "fat-suppressed"],
                "slices": [0],
                "code": "identified",
                "count": 2,
                "off_plane_mm": 0.0,
                "support": "a1_objects",
                "note": "test support",
                "artifact": artifact_rel,
                "row": None,
                "label": 1,
            }
        ],
    }
    objects = {
        "femur": {
            "anatomical_relations": {"tibia": "between"},
            "definition_decisions": [{"code": "identified"}],
            "search_refusals": [],
            "unresolved": {},
            "observations": {"native": {"resolved": {"a1_objects": []}}},
        }
    }
    return (
        run_dir,
        main_run,
        {
            "study_uid": "study-1",
            "records": [record],
            "main_records": [],
            "objects": objects,
        },
        record,
    )


def test_validates_explicit_spec_without_io_and_rejects_incomplete_bindings():
    compiled = validate_spec(_spec())
    assert compiled["layout"].count_layout.banks[0].name == "signal"
    assert compiled["carrier"].identity == compiled["layout"].carrier_id
    bad = _spec()
    bad["profiles"][0]["readings"] = []
    with pytest.raises(ValueError, match="profile_metric_bindings_incomplete"):
        validate_spec(bad)


def test_encodes_addressed_native_places_and_keeps_object_context(tmp_path):
    run_dir, main_run, result, _ = _study(tmp_path)
    output = tmp_path / "encodings" / "study-1.json.xz"
    links = encode_study(
        result,
        run_dir,
        main_run,
        _spec(view=["coronal", "fluid", "fat-suppressed"]),
        output,
    )
    assert links["manifest"].endswith("study-1.json.xz")
    manifest = load_json(links["manifest"])
    assert (
        manifest["meaning"]
        == "addressed count encoding only; no cross-view alias or volume"
    )
    assert manifest["object_contexts"]["femur"]["anatomical_relations"] == {
        "tibia": "between"
    }
    outcome = manifest["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "ok"
    assert outcome["metadata"]["source_refs"]["light_local"]["shape"] == [2, 2]
    assert outcome["metadata"]["plane_frame"] == {"origin_lps": [1.0, 2.0, 3.0]}
    with open_arrays(links["archive"]) as archive:
        points = archive[outcome["points_rc"]]
        row_codes = archive[outcome["metrics"][0]["row_codes"]]
        carrier_vector = archive[outcome["carrier_vector"]]
    assert np.array_equal(points, np.array([[0, 1], [1, 2]], dtype=np.int32))
    assert np.array_equal(row_codes, np.array([0, 2], dtype=np.int16))
    assert carrier_vector.shape == (1, 512) and carrier_vector.dtype == np.int32
    link = result["objects"]["femur"]["encoding"][0]
    assert link["manifest"] == links["manifest"]
    assert link["status"] == "ok"
    assert links["work"] == {
        "opened_artifacts": 1,
        "verified_source_arrays": 4,
        "source_bytes_verified": 34,
        "emitted_array_bytes": 2068,
        "addressed_places": 2,
        "metric_row_arrays": 1,
        "bundle_count": 1,
    }


def test_projected_target_is_named_without_opening_source_archive(
    tmp_path, monkeypatch
):
    run_dir, main_run, result, record = _study(tmp_path)
    target = dict(record["observations"][0])
    target.update(
        provenance="projected",
        kind="target",
        code="pointed",
        count=None,
        off_plane_mm=None,
    )
    record["observations"] = [target]
    from knee.encoding import operation

    def unexpected_open(_path):
        raise AssertionError("target observation must not open its source archive")

    monkeypatch.setattr(operation, "open_arrays", unexpected_open)
    output = tmp_path / "target.json"
    links = encode_study(
        result, run_dir, main_run, _spec(provenance="projected", kind="target"), output
    )
    manifest = load_json(links["manifest"])
    outcome = manifest["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "target_only"
    assert "points_rc" not in outcome
    assert links["work"]["opened_artifacts"] == 0
    with open_arrays(links["archive"]) as archive:
        assert archive.files == []


def test_digest_mismatch_is_named_and_missing_observation_is_not_absence(tmp_path):
    run_dir, main_run, result, _ = _study(tmp_path, wrong_digest=True)
    links = encode_study(result, run_dir, main_run, _spec(), tmp_path / "bad.json")
    outcome = load_json(links["manifest"])["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "digest_mismatch"

    empty = {"study_uid": "study-1", "records": [], "main_records": [], "objects": {}}
    missing = encode_study(empty, run_dir, main_run, _spec(), tmp_path / "missing.json")
    outcome = load_json(missing["manifest"])["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "missing_observation"


def test_main_records_load_from_main_run_root(tmp_path):
    run_dir, main_run, result, record = _study(tmp_path)
    source = run_dir / record["artifact"]
    destination = main_run / record["artifact"]
    destination.parent.mkdir(parents=True)
    destination.write_bytes(source.read_bytes())
    result["records"] = []
    result["main_records"] = [record]
    links = encode_study(result, run_dir, main_run, _spec(), tmp_path / "main.json")
    outcome = load_json(links["manifest"])["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "ok"


def test_repeated_profiles_open_artifact_and_load_each_verified_array_once(
    tmp_path, monkeypatch
):
    run_dir, main_run, result, _ = _study(tmp_path)
    from knee.encoding import operation

    original_open = operation.open_arrays
    opened = []
    reads = {}

    class CountingArchive:
        def __init__(self, archive):
            self.archive = archive

        @property
        def files(self):
            return self.archive.files

        def __contains__(self, name):
            return name in self.archive.files

        def __getitem__(self, name):
            reads[name] = reads.get(name, 0) + 1
            return self.archive[name]

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self.archive.close()

    def counting_open(path):
        opened.append(path)
        return CountingArchive(original_open(path))

    monkeypatch.setattr(operation, "open_arrays", counting_open)
    spec = _spec()
    spec["profiles"].append(dict(spec["profiles"][0]))
    links = encode_study(result, run_dir, main_run, spec, tmp_path / "reuse.json")
    assert len(opened) == 1
    assert reads == {
        "a1_objects": 1,
        "light_local": 1,
        "valid_local": 1,
        "light_window": 1,
    }
    outcomes = load_json(links["manifest"])["profiles"]
    assert [entry["outcomes"][0]["status"] for entry in outcomes] == ["ok", "ok"]


def test_counts_and_layout_are_retained_when_carrier_vector_overflows():
    validated = validate_spec(_spec())
    layout = validated["layout"]
    carrier: HadamardCarrier = validated["carrier"]
    huge_counts = ((2**40,) + (0,) * 511,)
    bundle = CountBundle(layout.count_layout, huge_counts)
    encoded = EncodingResult(EncodingCode.OK, bundle, (), "a" * 64)
    points = np.array([[0, 0]], dtype=np.int32)
    arrays, outcome = _encoding_arrays(
        AddressedEncoding("ok", encoded, points, {}), carrier, layout, "overflow"
    )
    assert outcome["carrier_status"] == "int32_overflow"
    assert outcome["counts"][0][0] == 2**40
    assert outcome["bundle_layout"]["layout_id"] == layout.count_layout.layout_id
    assert outcome["bundle_layout"]["carrier_id"] == carrier.identity
    assert outcome["reference_set_fingerprint"] == "a" * 64
    assert "overflow_carrier_vector" not in arrays


def test_prepared_spec_is_owned_reused_and_rejects_other_declarations(
    tmp_path, monkeypatch
):
    from knee.encoding import operation

    run_dir, main_run, result, _ = _study(tmp_path)
    caller_spec = _spec()
    prepared = validate_spec(caller_spec)
    assert prepared["spec"] is not caller_spec
    caller_spec["version"] = "caller-mutated-after-prepare"
    with pytest.raises(ValueError, match="prepared_spec_identity_mismatch"):
        encode_study(
            result,
            run_dir,
            main_run,
            caller_spec,
            tmp_path / "mismatch.json",
            prepared=prepared,
        )

    class NoCanonicalization:
        @staticmethod
        def dumps(*_args, **_kwargs):
            raise AssertionError("prepared plans must reuse the canonical fingerprint")

    monkeypatch.setattr(operation, "json", NoCanonicalization)
    output_a = encode_study(
        result,
        run_dir,
        main_run,
        prepared["spec"],
        tmp_path / "prepared-a.json",
        prepared=prepared,
    )
    output_b = encode_study(
        result,
        run_dir,
        main_run,
        prepared["spec"],
        tmp_path / "prepared-b.json",
        prepared=prepared,
    )
    assert (
        load_json(output_a["manifest"])["spec_sha256"]
        == load_json(output_b["manifest"])["spec_sha256"]
    )


def _context_spec(*, source_path=("view", 1), scope="acquisition", words=True):
    profile = {
        "object": "femur",
        "provenance": "native",
        "kind": "resolved",
        "support": "a1_objects",
        "view": ["coronal", "fluid", "fat-suppressed"],
        "readings": [
            {
                "bank": "signal",
                "metric": "light",
                "value": "light_local",
                "available": "valid_local",
                "window": "light_window",
            },
            {
                "bank": "context",
                "metric": "view_part" if words else "split",
                "source": "record_context",
                "path": list(source_path),
                "scope": scope,
            },
        ],
        "references": [
            {
                "bank": "signal",
                "metric": "light",
                "reference_id": "reference-a",
                "source": "declared test reference",
                "units": "arbitrary intensity",
                "low": 4,
                "high": 6,
            }
        ],
    }
    banks = [
        {
            "name": "signal",
            "facet": "measured signal",
            "metrics": [{"name": "light", "kind": "digit"}],
        },
        {
            "name": "context",
            "facet": "declared context",
            "metrics": [
                {
                    "name": "view_part" if words else "split",
                    "kind": "words" if words else "digit",
                    "words": ["fluid", "other"] if words else [],
                }
            ],
        },
    ]
    if not words:
        profile["references"].append(
            {
                "bank": "context",
                "metric": "split",
                "reference_id": "context-reference",
                "source": "declared test reference",
                "units": "arbitrary intensity",
                "low": 0,
                "high": 10,
            }
        )
    return {"version": "context-v1", "banks": banks, "profiles": [profile]}


def test_record_context_view_word_broadcasts_over_existing_addressed_places(tmp_path):
    run_dir, main_run, result, _record = _study(tmp_path)
    links = encode_study(
        result,
        run_dir,
        main_run,
        _context_spec(),
        tmp_path / "context.json",
    )
    manifest = load_json(links["manifest"])
    outcome = manifest["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "ok"
    assert outcome["place_count"] == 2
    context = outcome["metadata"]["context_sources"][0]
    assert context == {
        "bank": "context",
        "metric": "view_part",
        "source": "record_context",
        "path": ["view", 1],
        "scope": "acquisition",
        "source_address": {
            "series_uid": "series-a",
            "view": ["coronal", "fluid", "fat-suppressed"],
            "slice_index": 0,
            "artifact": "study-1/series-a.npz.xz",
        },
        "status": "available",
        "value": "fluid",
        "scalar_type": "str",
    }
    with open_arrays(links["archive"]) as archive:
        points = archive[outcome["points_rc"]]
        metrics = {item["metric"]: item for item in outcome["metrics"]}
        signal_codes = archive[metrics["light"]["row_codes"]]
        context_codes = archive[metrics["view_part"]["row_codes"]]
    assert points.shape == (2, 2)
    assert np.all(signal_codes >= 0)
    assert np.all(context_codes == outcome["metrics"][1]["row_names"].index("fluid"))
    assert manifest["work"]["addressed_places"] == 2


@pytest.mark.parametrize(
    "record_type,observation_type", [(tuple, list), (list, tuple), (tuple, tuple)]
)
def test_live_and_serialized_acquisition_views_have_the_same_context_identity(
    tmp_path, record_type, observation_type
):
    run_dir, main_run, result, record = _study(tmp_path)
    record["view"] = record_type(record["view"])
    record["observations"][0]["view"] = observation_type(
        record["observations"][0]["view"]
    )
    links = encode_study(
        result, run_dir, main_run, _context_spec(), tmp_path / "live-context.json"
    )
    outcome = load_json(links["manifest"])["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "ok"
    assert outcome["metadata"]["context_sources"][0]["value"] == "fluid"
    assert outcome["place_count"] == 2


@pytest.mark.parametrize(
    ("path", "record_update", "reason"),
    [
        (["missing_context"], {}, "context_path_unavailable"),
        (["background_split"], {"background_split": None}, "context_value_null"),
        (
            ["background_split"],
            {"background_split": float("nan")},
            "context_value_nonfinite",
        ),
    ],
)
def test_missing_null_and_nonfinite_record_scalars_are_unavailable(
    tmp_path, path, record_update, reason
):
    run_dir, main_run, result, record = _study(tmp_path)
    record.update(record_update)
    links = encode_study(
        result,
        run_dir,
        main_run,
        _context_spec(source_path=path, words=False),
        tmp_path / "unavailable.json",
    )
    outcome = load_json(links["manifest"])["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "ok"
    context = outcome["metadata"]["context_sources"][0]
    assert context["status"] == "unavailable"
    assert context["reason"] == reason
    metric = next(item for item in outcome["metrics"] if item["metric"] == "split")
    with open_arrays(links["archive"]) as archive:
        assert np.array_equal(
            archive[metric["row_codes"]], np.full(2, -1, dtype=np.int16)
        )


def test_record_plane_context_refuses_slice_mismatch_and_acquisition_view_mismatch(
    tmp_path,
):
    run_dir, main_run, result, record = _study(tmp_path)
    record["slice_index"] = 2
    links = encode_study(
        result,
        run_dir,
        main_run,
        _context_spec(source_path=("slice_index",), scope="record_plane", words=False),
        tmp_path / "plane-mismatch.json",
    )
    outcome = load_json(links["manifest"])["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "context_record_plane_slice_mismatch"

    run_dir, main_run, result, record = _study(tmp_path / "view")
    record["view"] = ["sagittal", "fluid", "fat-suppressed"]
    links = encode_study(
        result,
        run_dir,
        main_run,
        _context_spec(),
        tmp_path / "view-mismatch.json",
    )
    outcome = load_json(links["manifest"])["profiles"][0]["outcomes"][0]
    assert outcome["status"] == "context_acquisition_view_mismatch"


@pytest.mark.parametrize(
    "path",
    [[], ["view", True], ["view", -1], ["view", "*"]],
)
def test_record_context_paths_are_explicit_and_non_executable(path):
    with pytest.raises(ValueError, match="invalid_profile_reading_binding"):
        validate_spec(_context_spec(source_path=path))


def test_packed_support_rejects_record_context_bindings():
    spec = _context_spec()
    spec["profiles"][0].update(
        object="fibula",
        kind="reading",
        support="a3_fibula_axial_region",
    )
    spec["profiles"][0]["support_layout"] = {
        "family": "fibula_axial",
        "identity_sources": {
            "owner_series_uid": "record.series_uid",
            "artifact": "record.artifact",
            "target_series_uid": "axial_evidence.series_uid",
            "target_view": "axial_evidence.view",
            "target_slice": "axial_evidence.slice",
            "row": "observation.row_to_axial_evidence.row",
        },
        "offsets": "a3_fibula_axial_offsets",
        "shapes": "a3_fibula_axial_shapes",
        "slices": "a3_fibula_axial_slices",
        "packed_arrays": [
            "a3_fibula_axial_region",
            "a3_fibula_axial_target",
            "a3_fibula_axial_available",
            "light_local",
            "valid_local",
        ],
        "target_pixels_array": "a3_fibula_axial_target",
        "frame_arrays": {
            "origin_lps": "a3_fibula_axial_origin_lps",
            "basis_lps": "a3_fibula_axial_basis_lps",
            "normal_lps": "a3_fibula_axial_normal_lps",
            "thickness_mm": "a3_fibula_axial_thickness_mm",
        },
        "count_meaning": "fibula_axial_target_pixels",
    }
    with pytest.raises(ValueError, match="packed_record_context_unsupported"):
        validate_spec(spec)


def test_context_is_shared_without_recomputing_or_allocating_per_place_values(
    tmp_path, monkeypatch
):
    from knee.encoding import handoff

    original = handoff.encode_places
    captured = []

    def capture(layout, readings, references):
        captured.append(readings["context", "view_part"])
        return original(layout, readings, references)

    monkeypatch.setattr(handoff, "encode_places", capture)
    run_dir, main_run, result, _ = _study(tmp_path)
    output = encode_study(
        result, run_dir, main_run, _context_spec(), tmp_path / "shared-context.json"
    )
    assert output["profiles"][0]["outcomes"][0]["status"] == "ok"
    assert len(captured) == 1
    assert captured[0].values.shape == (2,)
    assert captured[0].values.strides == (0,)
    assert captured[0].available.strides == (0,)


def test_retained_object_sources_reuse_the_open_artifact_and_publish_in_h5(
    tmp_path, monkeypatch
):
    import sys
    from pathlib import Path
    from types import ModuleType

    from knee.encoding import operation
    from knee.encoding.product import open_product

    run_dir, main_run, result, record = _study(tmp_path)
    source_path = (run_dir / record["artifact"]).resolve()
    spec = _spec()
    spec["storage"] = "h5"
    spec["retain_object_sources"] = True
    calls = {"open": 0, "retain": 0, "archive": None}
    source_module = ModuleType("knee.encoding.object_sources")

    class Plan:
        artifacts = (source_path,)

        def retain_artifact(self, path, archive, verified_arrays, emitted_arrays):
            calls["retain"] += 1
            calls["archive"] = archive
            assert path == source_path
            assert (
                "a1_objects",
                record["arrays"]["a1_objects"]["digest"],
            ) in verified_arrays
            emitted_arrays["object_source_retained"] = verified_arrays[
                ("a1_objects", record["arrays"]["a1_objects"]["digest"])
            ]

        def finish(self):
            return {
                "schema": "knee-object-sources/v1",
                "status": "complete",
                "archive": str(calls["expected_archive"]),
                "objects": {"femur": {"observations": [], "unresolved": []}},
            }

    def prepare(study_result, candidates, archive_path):
        assert study_result is result
        assert candidates[0][0] is record
        assert candidates[0][1] == run_dir
        assert archive_path.suffix == ".h5"
        calls["expected_archive"] = archive_path
        return Plan()

    source_module.ObjectSourceError = ValueError
    source_module.prepare_object_sources = prepare
    monkeypatch.setitem(sys.modules, "knee.encoding.object_sources", source_module)
    original_open = operation.open_arrays

    def counted_open(path):
        calls["open"] += 1
        return original_open(path)

    monkeypatch.setattr(operation, "open_arrays", counted_open)
    output = tmp_path / "encoding" / "study.json.xz"
    statuses = encode_study(result, run_dir, main_run, spec, output)

    assert calls["open"] == 1
    assert calls["retain"] == 1
    assert statuses["object_sources"]["status"] == "complete"
    with open_product(Path(statuses["manifest"])) as product:
        assert product.manifest["object_sources"] == statuses["object_sources"]
        assert product.arrays["object_source_retained"].shape == (2, 3)
