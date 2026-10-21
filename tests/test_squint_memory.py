from __future__ import annotations

import csv
import hashlib
import io
import json
import lzma
from pathlib import Path

import numpy as np
import pytest

from knee.diagnosis.squint_memory import (
    SCHEMA,
    SquintMemoryError,
    _condition_calls,
    _question_object_roles,
    _read_labels,
    _support_bbox,
    inspect_memory_snapshot,
    load_memory,
    load_memory_snapshot,
    save_memory,
)
from knee.study.tables import LABELS


def _memory() -> dict:
    return {
        "schema": SCHEMA,
        "revision": "test-revision",
        "questions": list(LABELS),
        "procedure": {"id": "knee.squint-ternary/v1"},
        "source_identities": {},
        "label_ledger": {},
        "object_conditions": {},
        "object_question_roles": {},
        "cases": [
            {
                "case_id": "case:study-a:femur",
                "study_uid": "study-a",
                "subject": "femur",
                "condition_calls": {"ACL": 1},
                "presentation_scope": {"ACL": "positive_condition_presentation"},
                "question_roles": {"ACL": "implicated"},
                "profile": {
                    "schema": "knee.squint-profile/v1",
                    "subject": "femur",
                    "banks": {"bank/a": [2, 0, 5]},
                    "source": {"window": [0, 1, 0, 2, 0, 2]},
                },
                "regions": [],
                "full_profile": {
                    "subject": "femur",
                    "mode": "full",
                    "scope": "object:femur",
                    "layout_id": "layout-a",
                    "carrier_id": "carrier-a",
                    "bank_count": 1,
                    "bank_names_sha256": "0" * 64,
                },
                "full_source": {
                    "product_path": "/products/study-a.h5",
                    "product_sha256": "1" * 64,
                    "study_uid": "study-a",
                    "source_roots": {},
                },
                "teaching_source": {"kind": "official_train_csv_label"},
            },
            {
                "case_id": "case:study-b:pcl",
                "study_uid": "study-b",
                "subject": "pcl",
                "condition_calls": {},
                "presentation_scope": {
                    "kind": "structural_context",
                    "label_scope": "condition_not_asked_or_unlabeled",
                },
                "question_roles": {"ACL": "context"},
                "profile": {
                    "schema": "knee.squint-profile/v1",
                    "subject": "pcl",
                    "banks": {"bank/b": [0, 3, 0]},
                    "source": {},
                },
                "regions": [],
                "full_profile": {"subject": "pcl", "mode": "full"},
                "full_source": {"product_path": "/products/study-b.h5"},
                "teaching_source": {"kind": "official_train_csv_label"},
            },
        ],
    }


def test_official_csv_header_and_empty_labels_are_preserved() -> None:
    with pytest.raises(SquintMemoryError, match="train_csv_missing"):
        _read_labels(Path("/no/such/root"))
    import tempfile

    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        with (root / "train.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(
                stream, fieldnames=("StudyInstanceUID", "Report", *LABELS)
            )
            writer.writeheader()
            writer.writerow(
                {"StudyInstanceUID": "study-a", "Report": "", "ACL": "1", "MCL": ""}
            )
        assert _read_labels(root) == {
            "study-a": {
                question: (1 if question == "ACL" else None) for question in LABELS
            }
        }


def test_label_calls_keep_positive_and_explicit_negative_scopes_distinct() -> None:
    values = {question: None for question in LABELS}
    values.update({"ACL": 1, "MCL": 0, "Medial OA": 0})
    calls, scopes = _condition_calls("femur", values)
    assert calls == {"ACL": 1, "MCL": -1, "Medial OA": -1}
    assert scopes == {
        "ACL": "positive_condition_presentation",
        "MCL": "condition_negative_with_other_positive_presentation",
        "Medial OA": "condition_negative_with_other_positive_presentation",
    }

    values["ACL"] = 0
    calls, scopes = _condition_calls("femur", values)
    assert calls["ACL"] == -1
    assert scopes["ACL"] == "normal_for_this_condition_only"

    values["ACL"] = None
    calls, scopes = _condition_calls("femur", values)
    assert "ACL" not in calls
    assert "ACL" not in scopes


def test_context_objects_are_mapped_from_question_declarations() -> None:
    roles = _question_object_roles()
    assert roles["pcl"]["ACL"] == "context"
    assert roles["acl"]["ACL"] == "implicated"
    assert roles["femur"]["Fracture"] == "implicated"
    assert roles["joint"]["Medial OA"] == "context"


def test_save_load_is_exact_atomic_and_refuses_overwrite(tmp_path: Path) -> None:
    destination = tmp_path / "memory"
    memory = _memory()
    receipt = save_memory(memory, destination)
    stored = destination / "manifest.json"
    raw = stored.read_bytes()
    assert json.loads(raw) == memory
    assert receipt["sha256"] == hashlib.sha256(raw).hexdigest()
    assert load_memory(destination) == memory
    assert load_memory(stored) == memory
    with pytest.raises(SquintMemoryError, match="memory_already_exists"):
        save_memory(memory, destination)


@pytest.mark.parametrize(
    ("mutate", "code"),
    [
        (lambda case: case.update(case_id=""), "memory_case_id_invalid_or_duplicate"),
        (
            lambda case: case["profile"]["banks"]["bank/a"].__setitem__(0, True),
            "memory_case_count_invalid",
        ),
        (
            lambda case: case["condition_calls"].update(ACL=0),
            "memory_case_calls_invalid",
        ),
        (
            lambda case: case["profile"]["banks"]["bank/a"].__setitem__(0, -1),
            "memory_case_count_invalid",
        ),
    ],
)
def test_save_rejects_malformed_case_data(tmp_path: Path, mutate, code: str) -> None:
    memory = _memory()
    mutate(memory["cases"][0])
    with pytest.raises(SquintMemoryError, match=code):
        save_memory(memory, tmp_path / "bad")


def test_load_rejects_malformed_manifest_and_duplicate_case_ids(tmp_path: Path) -> None:
    path = tmp_path / "memory"
    path.mkdir()
    (path / "manifest.json").write_text("{", encoding="utf-8")
    with pytest.raises(SquintMemoryError, match="memory_manifest_invalid"):
        load_memory(path)

    memory = _memory()
    memory["cases"][1]["case_id"] = memory["cases"][0]["case_id"]
    (path / "manifest.json").write_text(json.dumps(memory), encoding="utf-8")
    with pytest.raises(SquintMemoryError, match="memory_case_id_invalid_or_duplicate"):
        load_memory(path)


def test_memory_snapshot_names_unavailable_invalid_legacy_and_squint_states(
    tmp_path: Path,
) -> None:
    assert inspect_memory_snapshot(None).status == "unavailable"

    directory = tmp_path / "memory-states"
    directory.mkdir()
    path = directory / "manifest.json"
    path.write_text('{"schema":"legacy-memory/v1"}', encoding="utf-8")
    legacy = inspect_memory_snapshot(directory)
    assert legacy.status == "legacy"
    assert legacy.declared_schema == "legacy-memory/v1"
    with pytest.raises(SquintMemoryError, match="memory_schema_invalid"):
        load_memory(directory)

    path.write_text("not-json", encoding="utf-8")
    invalid = inspect_memory_snapshot(directory)
    assert invalid.status == "invalid"
    assert invalid.error_code == "memory_manifest_invalid"
    with pytest.raises(SquintMemoryError, match="memory_manifest_invalid"):
        load_memory_snapshot(directory)

    valid = _memory()
    path.write_text(json.dumps(valid), encoding="utf-8")
    snapshot = load_memory_snapshot(directory)
    assert snapshot.status == "squint"
    assert snapshot.memory == valid
    assert snapshot.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert load_memory(directory) == valid

    malformed_squint = {"schema": SCHEMA}
    path.write_text(json.dumps(malformed_squint), encoding="utf-8")
    bad_squint = inspect_memory_snapshot(directory)
    assert bad_squint.status == "invalid"
    assert bad_squint.declared_schema == SCHEMA
    assert bad_squint.error_code == "memory_revision_invalid"


def test_bootstrap_compiler_publishes_object_and_configuration_cases(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import knee.diagnosis.squint_memory as memory_module
    import knee.encoding.product as product_module
    from knee.diagnosis import squint_profiles

    uid = "study-compiled"
    root = tmp_path / "raw"
    root.mkdir()
    with (root / "train.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=("StudyInstanceUID", "Report", *LABELS)
        )
        writer.writeheader()
        writer.writerow(
            {
                "StudyInstanceUID": uid,
                "Report": "retained report text",
                "ACL": "1",
                "MCL": "0",
            }
        )
    products = tmp_path / "products"
    products.mkdir()
    (products / f"{uid}.h5").touch()
    from knee.encoding.places import (
        BankSpec,
        LayoutSpec,
        MetricKind,
        MetricSpec,
        compile_layout,
    )

    spec = LayoutSpec(
        "fixture-layout-v1",
        "fixture-carrier-v1",
        (
            BankSpec(
                "fixture/signal",
                "signal",
                (MetricSpec("level", MetricKind.WORDS, ("low", "mid", "high")),),
            ),
        ),
    )
    compiled = compile_layout(spec)
    assert compiled is not None
    layout = {
        "version": spec.version,
        "carrier_id": spec.carrier_id,
        "fingerprint": compiled.fingerprint,
        "banks": [
            {
                "name": bank.name,
                "facet": bank.facet,
                "metrics": [
                    {
                        "name": metric.name,
                        "kind": metric.kind.value,
                        "words": list(metric.words),
                    }
                    for metric in bank.metrics
                ],
            }
            for bank in spec.banks
        ],
    }
    reference_id = "reference-set-a"
    objects = {
        subject: {
            "count_layout_id": (
                f"{spec.version}:{compiled.fingerprint}:{reference_id}"
            ),
            "reference_set_identity": reference_id,
            "sparse_counts": [["fixture/signal", 0, 3], ["fixture/signal", 2, 1]],
            "status": "valid",
            "preparation_status": "prepared",
            "assembly": {"code": "assembled", "batches": []},
        }
        for subject in ("acl", "femur", "tibia", "pcl", "mcl", "medial_meniscus")
    }
    composition = {
        "schema": "knee_object_profiles/v1",
        "objects": objects,
        "layout_fingerprint": compiled.fingerprint,
        "carrier_identity": spec.carrier_id,
        "registry_fingerprint": "registry-fingerprint-a",
        "layout": layout,
    }

    class FakeProduct:
        def __init__(self):
            self.arrays = {}
            self.manifest = {
                "study_uid": uid,
                "mode": "full",
                "product_storage": "h5",
                "spec": {"version": "fixture-spec-v1"},
                "spec_sha256": "a" * 64,
                "object_composition": composition,
                "source_roots": {"run": "/retained/run"},
                "support_ownership": {},
                "object_contexts": {},
            }

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

    profiles = {
        subject: {
            "schema": "knee.squint-profile/v1",
            "subject": subject,
            "banks": {"view/signal_median/overview/10mm": [index + 1, 0, 2]},
            "source": {
                "procedure": "knee.squint-profile/scan-tercile-v1",
                "window": [0, 1, 0, 1, 0, 1],
            },
        }
        for index, subject in enumerate(objects)
    }
    monkeypatch.setattr(product_module, "open_product", lambda path: FakeProduct())
    monkeypatch.setattr(memory_module, "_digest", lambda path: "a" * 64)
    monkeypatch.setattr(
        squint_profiles, "read_study_squints", lambda *args, **kwargs: {}
    )
    monkeypatch.setattr(memory_module, "_series_index", lambda study: {})
    monkeypatch.setattr(
        memory_module,
        "_profile_regions",
        lambda study, records, *args: (
            profiles,
            {subject: [{"source_window": [0, 1, 0, 1, 0, 1]}] for subject in profiles},
        ),
    )

    destination = tmp_path / "compiled-memory"
    receipt = memory_module.compile_bootstrap(
        root,
        products,
        destination,
        selected_uids=(uid,),
        io_workers=1,
    )
    stored = load_memory(destination)
    object_cases = [
        case for case in stored["cases"] if case["case_id"].startswith("squint-case:")
    ]
    configuration_cases = [
        case
        for case in stored["cases"]
        if case["case_id"].startswith("squint-configuration:")
    ]
    assert (
        receipt["object_case_count"],
        receipt["configuration_case_count"],
        receipt["case_count"],
    ) == (6, 2, 8)
    assert len(object_cases) == 6
    assert [case["condition_calls"] for case in configuration_cases] == [
        {"ACL": 1},
        {"MCL": -1},
    ]
    acl_configuration = configuration_cases[0]
    assert acl_configuration["profile"]["subject"] == "diagnosis/ACL"
    assert set(acl_configuration["profile"]["source"]["roles"]) == {
        "acl",
        "femur",
        "tibia",
        "pcl",
    }
    assert acl_configuration["profile"]["banks"][
        "object/acl/view/signal_median/overview/10mm"
    ] == [1, 0, 2]
    assert (
        acl_configuration["profile"]["source"]["procedure"]
        == "knee.squint-profile/scan-tercile-v1"
    )
    assert "condition_calls" not in json.dumps(
        acl_configuration["profile"], sort_keys=True
    )
    assert stored["revision"].endswith("+question-configurations-v1")
    assert receipt["configuration_case_count"] == 2


def test_support_bbox_uses_observation_slice_and_explicit_femur_companion(
    tmp_path: Path,
) -> None:
    source_root = tmp_path / "interiors"
    artifact = Path("study/series.npz.xz")
    artifact_path = source_root / artifact
    artifact_path.parent.mkdir(parents=True)
    regions = np.zeros((8, 10, 12), dtype=np.bool_)
    regions[7, 2:8, 3:10] = True
    regions[4, 0:2, 0:2] = True
    buffer = io.BytesIO()
    np.savez_compressed(
        buffer,
        a3_femur_plane_region=regions,
        a3_femur_plane_slices=np.array([0, 2, 5, 6, 7, 15, 17, 22]),
    )
    artifact_path.write_bytes(lzma.compress(buffer.getvalue()))

    support_ownership = {
        "femur": {
            "addressed_supports": [
                {
                    "source_address": {
                        "target_series_uid": "series-a",
                        # This record slice is provenance, not the observation.
                        "record_slice_index": 18,
                        "observation_slices": [22],
                        "observation_row": 7,
                        "observation_support": "a3_femur_plane_region",
                        "observation_label": None,
                        "observation_artifact": str(artifact),
                        "source_root": "run",
                        "address_kind": "native_rc",
                        "native_shape_rc": [10, 12],
                        "geometry_status": "available",
                    }
                }
            ]
        }
    }
    resolved = _support_bbox(
        "femur",
        "series-a",
        22,
        support_ownership,
        {"run": str(source_root)},
        {},
    )
    assert resolved == (2, 8, 3, 10)
    address = support_ownership["femur"]["addressed_supports"][0]["source_address"]
    address["observation_row"] = 4
    assert (
        _support_bbox(
            "femur", "series-a", 22, support_ownership, {"run": str(source_root)}, {}
        )
        is None
    )
    address["observation_row"] = 7

    assert (
        _support_bbox(
            "femur",
            "series-a",
            18,
            support_ownership,
            {"run": str(source_root)},
            {},
        )
        is None
    )


def test_support_bbox_uses_verified_public_native_coordinates() -> None:
    coordinates = np.array([[191, 226], [198, 240], [194, 232]], dtype=np.int32)
    address = {
        "target_series_uid": "series-a",
        "record_slice_index": 9,
        "observation_slices": [15],
        "observation_view": ["Coronal", "1", "1"],
        "observation_support": "a1_objects",
        "address_kind": "native_rc",
        "native_shape_rc": [320, 320],
        "geometry_status": "available",
    }
    entry = {
        "source_address": address,
        "links": [
            {
                "profile_object": "medial_meniscus",
                "coordinate_field": "points_rc",
                "coordinate_member": "p73_o0000_points_rc",
                "place_count": 3,
                "metadata": {
                    "observation": {
                        "series_uid": "series-a",
                        "slices": [15],
                        "support": "a1_objects",
                        "view": ["Coronal", "1", "1"],
                    },
                    "native_shape_rc": [320, 320],
                },
            }
        ],
    }
    support_ownership = {"medial_meniscus": {"addressed_supports": [entry]}}
    assert _support_bbox(
        "medial_meniscus",
        "series-a",
        15,
        support_ownership,
        {},
        {},
        {"p73_o0000_points_rc": coordinates},
    ) == (191, 199, 226, 241)
    # The same points cannot be relabeled as the selected slice 16.
    assert (
        _support_bbox(
            "medial_meniscus",
            "series-a",
            16,
            support_ownership,
            {},
            {},
            {"p73_o0000_points_rc": coordinates},
        )
        is None
    )


def test_support_bbox_refuses_out_of_bounds_public_coordinates() -> None:
    address = {
        "target_series_uid": "series-a",
        "observation_slices": [15],
        "observation_view": ["Coronal", "1", "1"],
        "observation_support": "a1_objects",
        "address_kind": "native_rc",
        "native_shape_rc": [320, 320],
        "geometry_status": "available",
    }
    entry = {
        "source_address": address,
        "links": [
            {
                "profile_object": "patella",
                "coordinate_field": "points_rc",
                "coordinate_member": "points",
                "place_count": 1,
                "metadata": {
                    "observation": {
                        "series_uid": "series-a",
                        "slices": [15],
                        "support": "a1_objects",
                        "view": ["Coronal", "1", "1"],
                    }
                },
            }
        ],
    }
    with pytest.raises(SquintMemoryError, match="support_coordinate_out_of_bounds"):
        _support_bbox(
            "patella",
            "series-a",
            15,
            {"patella": {"addressed_supports": [entry]}},
            {},
            {},
            {"points": np.array([[320, 1]], dtype=np.int32)},
        )
