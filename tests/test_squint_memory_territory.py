"""The bootstrap compiler's writer choice: v1 rebuilds exactly, v2 reads territories.

One real synthetic DICOM series, laid out as the frozen fixture's slice 1 (air
ring, leg edge, tissue, an enclosed dark body), and one fake bootstrap product
whose supports are saved native coordinates. The territory writer and teacher
supports are the integrated producers; the leg map is the fixture's expected
map, handed in as the compiler's explicit ``leg_maps`` input.

Configuration cases under v2 need the root-owned configuration composer to
accept the territory procedure (``configurations-consumer.patch`` in the W5
record folder); the tests that publish a v2 memory skip until it is applied.
"""

from __future__ import annotations

import csv
import hashlib
import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pydicom
import pytest

import tests.squint_upgrade_fixtures as fixture
from knee.diagnosis import squint_memory as memory_module
from knee.diagnosis.squint_interfaces import (
    TERRITORY_PROCEDURE,
    TERRITORY_SCHEMA,
    parse_territory_bank_name,
)
from knee.study.tables import LABELS
from tests.test_squint_profiles import _write_dicom, _write_tables

STUDY_UID = "1.2.826.0.1.3680043.8.498.5005.1"
SERIES_UID = "1.2.826.0.1.3680043.8.498.5005.2"
MISSING_SERIES_UID = "1.2.826.0.1.3680043.8.498.5005.3"
VIEW = ["Sagittal", "1", "1"]
SHAPE_RC = [160, 160]
V1_REVISION = (
    "bootstrap-2026-10-21-native-supports-v2"
    "+portable-full-profiles-v1+question-configurations-v1"
)
#: SHA-256 of the default writer's manifest on this study, with the temporary
#: root replaced by ``<TMP>``. The same with the base compilers at e7fe990,
#: be221ff and ce49a6e (W5 record folder, ``v1-identity/digests.log``); the
#: default writer must not move it.
V1_MANIFEST_SHA256 = "3ab2fa0d0eb521314b75c5bb23527f8d3197102944b842ce7f1557a4b1772e28"

# Native supports as (row0, row1, col0, col1) blocks; one tile is 20 x 20 pixels.
# A covers 100, 200, 300 and 160 pixels of the dark body's four tiles; B has the
# same box (rows 60-95, columns 60-100) but covers tile (3, 3) whole and one
# pixel of tile (4, 4).
MENISCUS_A = ((60, 65, 60, 80), (60, 70, 80, 100), (80, 95, 60, 80), (80, 88, 80, 100))
MENISCUS_B = ((60, 80, 60, 80), (94, 95, 99, 100))
SUPPORTS = {
    "tibia": ((100, 120, 40, 100),),
    "acl": ((44, 56, 44, 56),),
    # Inside the air ring: a saved support that lies wholly outside the leg.
    "pcl": ((2, 10, 62, 78),),
    # Not a case subject: v1 reads it and throws it away, v2 never reads it.
    "air": ((0, 8, 0, 160),),
}
LABEL_ROW = {"ACL": "1", "MCL": "0", "Medial Meniscus": "0", "Medial OA": "0"}
OBJECT_CASE_FIELDS = (
    "study_uid",
    "subject",
    "condition_calls",
    "presentation_scope",
    "question_roles",
    "label_attribution",
    "full_profile",
    "full_source",
)


def _configurations_accept_territory() -> bool:
    from knee.diagnosis.squint_configurations import with_configuration_cases

    return "procedure" in inspect.signature(with_configuration_cases).parameters


needs_configurations = pytest.mark.skipif(
    not _configurations_accept_territory(),
    reason="awaits configurations-consumer.patch (root-owned squint_configurations)",
)


def _points(*blocks: tuple[int, int, int, int]) -> np.ndarray:
    pieces = []
    for r0, r1, c0, c1 in blocks:
        rows, cols = np.mgrid[r0:r1, c0:c1]
        pieces.append(np.stack([rows.ravel(), cols.ravel()], axis=1))
    return np.unique(np.concatenate(pieces), axis=0).astype(np.int32)


def _support_entry(
    subject: str, member: str, count: int, slice_index: int = 0, record_slice: int = 0
) -> dict:
    observation = {
        "series_uid": SERIES_UID,
        "slices": [slice_index],
        "support": "a1_objects",
        "view": list(VIEW),
    }
    return {
        "source_address": {
            "target_series_uid": SERIES_UID,
            "record_slice_index": record_slice,
            "observation_slices": [slice_index],
            "observation_view": list(VIEW),
            "observation_support": "a1_objects",
            "address_kind": "native_rc",
            "native_shape_rc": list(SHAPE_RC),
            "geometry_status": "available",
        },
        "links": [
            {
                "profile_object": subject,
                "coordinate_field": "points_rc",
                "coordinate_member": member,
                "place_count": count,
                "metadata": {
                    "observation": observation,
                    "native_shape_rc": list(SHAPE_RC),
                },
            }
        ],
    }


def _sagittal(slice_index: int = 0) -> dict:
    return {"outcome": "selected", "series_uid": SERIES_UID, "slice": slice_index}


class _Product:
    """A bootstrap product as ``open_product`` yields it, held in memory."""

    def __init__(self, manifest: dict, arrays: dict):
        self.manifest = manifest
        self.arrays = arrays

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


def _composition(spatial: dict[str, dict]) -> dict:
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
    reference = "reference-set-a"
    return {
        "schema": "knee_object_profiles/v1",
        "objects": {
            subject: {
                "count_layout_id": f"{spec.version}:{compiled.fingerprint}:{reference}",
                "reference_set_identity": reference,
                "sparse_counts": [["fixture/signal", 0, 3], ["fixture/signal", 2, 1]],
                "status": "valid",
                "preparation_status": "prepared",
                "assembly": {"code": "assembled", "batches": []},
                "spatial_context": context,
            }
            for subject, context in spatial.items()
        },
        "layout_fingerprint": compiled.fingerprint,
        "carrier_identity": spec.carrier_id,
        "registry_fingerprint": "registry-fingerprint-a",
        "layout": {
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
        },
    }


def _inputs(
    base: Path,
    *,
    meniscus=MENISCUS_A,
    labels: dict[str, str] = LABEL_ROW,
) -> tuple[Path, Path, _Product]:
    """Write the study's DICOM and tables under ``base`` and make its product."""
    root = base / "raw"
    directory = root / "train_series" / STUDY_UID / SERIES_UID
    directory.mkdir(parents=True)
    coarse = fixture.series_record()["stack"].median[1]
    pixels = np.repeat(np.repeat(coarse, 20, axis=0), 20, axis=1).astype(np.uint16)
    _write_dicom(
        directory / "one.dcm", STUDY_UID, SERIES_UID, pixels, spacing_rc=(0.5, 0.5)
    )
    _write_tables(root, STUDY_UID, SERIES_UID)
    with (root / "train.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=("StudyInstanceUID", "Report", *LABELS)
        )
        writer.writeheader()
        writer.writerow(
            {"StudyInstanceUID": STUDY_UID, "Report": "retained report", **labels}
        )
    products = base / "products"
    products.mkdir()
    (products / f"{STUDY_UID}.h5").touch()
    blocks = {"medial_meniscus": meniscus, **SUPPORTS}
    arrays = {f"{subject}_points": _points(*value) for subject, value in blocks.items()}
    ownership = {
        subject: {
            "addressed_supports": [
                _support_entry(
                    subject, f"{subject}_points", len(arrays[f"{subject}_points"])
                )
            ]
        }
        for subject in blocks
    }
    spatial = {subject: {"keyplanes": {"sagittal": _sagittal()}} for subject in blocks}
    # The ACL's coronal key plane names a series this study never acquired.
    spatial["acl"]["keyplanes"]["coronal"] = {
        "outcome": "selected",
        "series_uid": MISSING_SERIES_UID,
        "slice": 0,
    }
    # The femur was placed by a point alone: no saved support resolves for it.
    spatial["femur"] = {
        "point_lps": [25.0, 45.0, 0.0],
        "keyplanes": {"sagittal": _sagittal()},
    }
    manifest = {
        "study_uid": STUDY_UID,
        "mode": "full",
        "product_storage": "h5",
        "spec": {"version": "fixture-spec-v1"},
        "spec_sha256": "a" * 64,
        "object_composition": _composition(spatial),
        "source_roots": {"run": "/retained/run"},
        "support_ownership": ownership,
        "object_contexts": {},
    }
    return root, products, _Product(manifest, arrays)


def _leg_map(series: dict) -> dict:
    """The fixture's expected leg map on its slice 1, addressed to this series."""
    leg = fixture.expected_leg_map()
    leg.update(
        study_uid=STUDY_UID,
        series_uid=series["series_uid"],
        codes=leg["codes"][1:2],
        leg_share=leg["leg_share"][1:2],
    )
    return leg


class _LegMaps:
    """An explicit leg-map producer that counts its calls."""

    def __init__(self):
        self.calls = 0

    def __call__(self, study: dict) -> dict:
        self.calls += 1
        return {series["series_uid"]: _leg_map(series) for series in study["series"]}


def _compile(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    products: Path,
    product: _Product,
    out: Path,
    **options,
) -> tuple[dict, bytes]:
    import knee.encoding.product as product_module

    monkeypatch.setattr(product_module, "open_product", lambda path: product)
    receipt = memory_module.compile_bootstrap(
        root, products, out, selected_uids=(STUDY_UID,), io_workers=1, **options
    )
    return receipt, (out / "manifest.json").read_bytes()


def _normalised_sha256(raw: bytes, base: Path) -> str:
    for path in sorted({str(base.resolve()), str(base)}, key=len, reverse=True):
        raw = raw.replace(path.encode("utf-8"), b"<TMP>")
    return hashlib.sha256(raw).hexdigest()


def v1_manifest_digest(base: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """The default writer's normalised manifest digest; also run on base compilers."""
    root, products, product = _inputs(base)
    _, raw = _compile(monkeypatch, root, products, product, base / "memory")
    return _normalised_sha256(raw, base)


def _object_cases(memory: dict) -> dict[str, dict]:
    return {
        case["case_id"]: case
        for case in memory["cases"]
        if case["case_id"].startswith("squint-case:")
    }


def _configuration_cases(memory: dict) -> dict[str, dict]:
    return {
        case["case_id"]: case
        for case in memory["cases"]
        if case["case_id"].startswith("squint-configuration:")
    }


def _writer(leg_maps) -> dict:
    """The integrated territory producers, bound as ``_territory_writer`` binds them."""
    from knee.diagnosis import squint_profiles, squint_support

    return {
        "leg_maps": leg_maps,
        "support_mask": squint_support.support_mask,
        "teacher_territory": squint_support.teacher_territory,
        "leg_calibration": squint_profiles.leg_calibration,
        "profile_territory": squint_profiles.profile_territory,
        "refine_territory": squint_profiles.refine_territory,
        "merge_profiles": squint_profiles.merge_profiles,
    }


def _read_regions(tmp_path: Path, writer: dict, *, meniscus=MENISCUS_A):
    from knee.diagnosis.squint_profiles import read_study_squints

    root, _, product = _inputs(tmp_path, meniscus=meniscus)
    study = read_study_squints(root, STUDY_UID, io_workers=1)
    manifest = product.manifest
    return memory_module._territory_profile_regions(
        study,
        manifest["object_composition"]["objects"],
        memory_module._series_index(study),
        manifest["support_ownership"],
        manifest["source_roots"],
        manifest["object_contexts"],
        product.arrays,
        subjects=frozenset(memory_module._question_object_roles()),
        writer=writer,
    )


# --- v1: the default writer rebuilds exactly --------------------------------


def test_default_writer_manifest_is_byte_identical_to_the_base_compiler(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert v1_manifest_digest(tmp_path, monkeypatch) == V1_MANIFEST_SHA256


def test_explicit_v1_writer_equals_the_default_byte_for_byte(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, products, product = _inputs(tmp_path)
    default_receipt, default_raw = _compile(
        monkeypatch, root, products, product, tmp_path / "default"
    )
    explicit_receipt, explicit_raw = _compile(
        monkeypatch, root, products, product, tmp_path / "explicit", writer="squint-v1"
    )
    assert explicit_raw == default_raw
    assert (tmp_path / "explicit" / "recall-preparation.json.xz").read_bytes() == (
        tmp_path / "default" / "recall-preparation.json.xz"
    ).read_bytes()
    assert default_receipt["revision"] == V1_REVISION
    assert "writer" not in default_receipt and "writer" not in explicit_receipt
    memory = json.loads(default_raw)
    assert "territory_writer" not in memory
    assert all("unprofiled_regions" not in case for case in memory["cases"])
    # v1 still reads the point-placed femur over its keypoint tile.
    femur = _object_cases(memory)[f"squint-case:{STUDY_UID}:femur"]
    assert [region["extent_source"] for region in femur["regions"]] == [
        "retained_physical_location"
    ]


# --- named refusals before any study is read ---------------------------------


def test_unknown_writer_and_misplaced_leg_maps_are_refused_before_reading(
    tmp_path: Path,
) -> None:
    empty = tmp_path / "nothing-here"
    with pytest.raises(
        memory_module.SquintMemoryError, match="bootstrap_writer_unknown"
    ):
        memory_module.compile_bootstrap(empty, empty, tmp_path / "out", writer="v3")
    with pytest.raises(
        memory_module.SquintMemoryError,
        match="bootstrap_leg_maps_require_territory_writer",
    ):
        memory_module.compile_bootstrap(
            empty, empty, tmp_path / "out", leg_maps=_LegMaps()
        )


def test_territory_writer_names_each_missing_producer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from knee.diagnosis import squint_configurations

    with monkeypatch.context() as scope:
        scope.setitem(sys.modules, "knee.diagnosis.squint_support", None)
        with pytest.raises(
            memory_module.SquintMemoryError, match="territory_writer_unavailable"
        ):
            memory_module._territory_writer(_LegMaps())
    with monkeypatch.context() as scope:
        scope.setitem(sys.modules, "knee.diagnosis.squint_leg", None)
        with pytest.raises(
            memory_module.SquintMemoryError, match="territory_leg_maps_unavailable"
        ):
            memory_module._territory_writer()
    with pytest.raises(memory_module.SquintMemoryError, match="leg_maps_invalid"):
        memory_module._territory_writer("not callable")  # type: ignore[arg-type]

    def v1_only(profiles, question):
        return {"source": {"procedure": "knee.squint-profile/scan-tercile-v1"}}

    with monkeypatch.context() as scope:
        scope.setattr(squint_configurations, "configuration_profile", v1_only)
        with pytest.raises(
            memory_module.SquintMemoryError,
            match="territory_configurations_unavailable",
        ):
            memory_module._territory_writer(_LegMaps())


# --- v2: each region is read over its own teacher territory ------------------


def test_territory_regions_read_supports_and_name_every_unread_region(
    tmp_path: Path,
) -> None:
    legs = _LegMaps()
    calls: dict[str, list] = {"support_mask": [], "leg_calibration": []}
    writer = _writer(legs)

    def spy(name):
        real = writer[name]

        def wrapped(*args, **kwargs):
            calls[name].append(args[:2])
            return real(*args, **kwargs)

        return wrapped

    writer["support_mask"] = spy("support_mask")
    writer["leg_calibration"] = spy("leg_calibration")
    profiles, regions, unprofiled, receipt = _read_regions(tmp_path, writer)

    # One leg-map call for the study, one leg-only calibration for the series.
    assert legs.calls == 1
    assert len(calls["leg_calibration"]) == 1
    # Only case subjects are read: the air's support is never resolved.
    assert {args[0] for args in calls["support_mask"]} == {
        "acl",
        "femur",
        "medial_meniscus",
        "pcl",
        "tibia",
    }
    assert set(profiles) == {"acl", "medial_meniscus", "tibia"}
    for subject, profile in profiles.items():
        assert profile["source"]["procedure"] == TERRITORY_PROCEDURE
        parsed = [parse_territory_bank_name(name) for name in profile["banks"]]
        assert parsed and all(fields is not None for fields in parsed)
        assert {fields["role"] for fields in parsed} == {"object", "context"}
        assert {fields["scale"] for fields in parsed} == {"10mm", "2mm"}
        assert not any(name.startswith("squint/v1/") for name in profile["banks"])
        assert all(sum(counts) > 0 for counts in profile["banks"].values()), subject

    meniscus = regions["medial_meniscus"]
    assert len(meniscus) == 1
    region = meniscus[0]
    territory = region["territory"]
    assert territory["schema"] == TERRITORY_SCHEMA
    assert territory["origin"] == "teacher_support"
    assert territory["tile_window"] == [0, 1, 2, 6, 2, 6]
    # The v1 address fields keep their meaning: the support's own box and tiles.
    assert region["source_window"] == [0, 1, 3, 5, 3, 5]
    assert region["native_bounds_rc"] == [60, 95, 60, 100]
    assert region["source_slice"] == region["key_slice"] == 0
    assert region["slice_choice"] == {
        "key_slice": 0,
        "used_slice": 0,
        "rule": "key_slice",
        "attempts": [{"slice": 0, "code": "valid"}],
    }
    assert region["extent_source"] == "retained_object_support"
    assert region["fine_refinement"] == "measured_or_silent"
    assert region["profile_procedure"] == TERRITORY_PROCEDURE
    assert territory["role_counts"] == {
        "object": 4,
        "context": 12,
        "outside_leg": 0,
        "unqueried": 0,
    }
    shares = np.asarray(territory["object_share"], dtype=np.float64)
    assert shares[0, 1:3, 1:3].tolist() == [[0.25, 0.5], [0.75, 0.4]]
    support = territory["native_support"]
    assert support["offset_rc"] == [60, 60]
    assert support["slices"] == [0]
    assert support["shape"] == [1, 35, 40]
    assert support["pixel_count"] == 760
    assert len(support["mask_sha256"]) == 64
    json.dumps(regions, allow_nan=False)
    json.dumps(unprofiled, allow_nan=False)

    # A region whose support does not resolve keeps its named reason: no box.
    assert "femur" not in profiles and "femur" not in regions
    assert [row["reason"] for row in unprofiled["femur"]] == ["support_unavailable"]
    assert [row["reason"] for row in unprofiled["pcl"]] == ["support_outside_leg"]
    assert [row["reason"] for row in unprofiled["acl"]] == ["series_unavailable"]
    assert [row["source_slice"] for row in regions["acl"]] == [0]
    assert all(row["profile_status"] == "not_profiled" for row in unprofiled["femur"])
    assert receipt["profiled_regions"] == 3
    assert receipt["unprofiled_regions"] == {
        "series_unavailable": 1,
        "support_outside_leg": 1,
        "support_unavailable": 1,
    }
    assert receipt["leg_maps"][SERIES_UID]["code"] == "valid"
    assert receipt["leg_maps"][SERIES_UID]["counts"]["outside"] == 28
    # The point-placed femur has no outline at any slice of the series.
    femur_choice = unprofiled["femur"][0]["slice_choice"]
    assert femur_choice["rule"] == "nearest_saved_support_in_series"
    assert femur_choice["used_slice"] is None
    assert femur_choice["attempts"] == [{"slice": 0, "code": "support_unavailable"}]
    # An outline that exists but lies outside the leg is not searched past.
    assert unprofiled["pcl"][0]["slice_choice"]["rule"] == "key_slice"
    assert receipt["subjects"]["femur"] == {
        "regions": 1,
        "profiled_at_key_slice": 0,
        "profiled_at_other_slice": 0,
        "unprofiled": {"support_unavailable": 1},
    }
    assert receipt["subjects"]["acl"]["profiled_at_key_slice"] == 1
    assert receipt["subjects"]["acl"]["unprofiled"] == {"series_unavailable": 1}


def _multislice_inputs(base: Path) -> tuple[Path, _Product]:
    """The fixture's three slices as one series, with outlines saved at chosen slices.

    patella: key slice 1, outlines at 0 and 2 (equally near); tibia: key slice
    2, outline only at 0; medial meniscus: outline at its key slice 1; femur:
    key slice 1 and no outline anywhere; fibula: two key planes on this series
    (slices 1 and 2) and one outline, at 0, which only one region may read.
    """
    root = base / "raw"
    directory = root / "train_series" / STUDY_UID / SERIES_UID
    directory.mkdir(parents=True)
    medians = fixture.series_record()["stack"].median
    for z in range(medians.shape[0]):
        pixels = np.repeat(np.repeat(medians[z], 20, axis=0), 20, axis=1)
        path = directory / f"slice{z}.dcm"
        _write_dicom(
            path, STUDY_UID, SERIES_UID, pixels.astype(np.uint16), spacing_rc=(0.5, 0.5)
        )
        dataset = pydicom.dcmread(path)
        dataset.ImagePositionPatient = [0.0, 0.0, 3.0 * z]
        dataset.InstanceNumber = z + 1
        dataset.save_as(path, enforce_file_format=True)
    _write_tables(root, STUDY_UID, SERIES_UID)
    outlines = {
        ("patella", 0): ((60, 80, 60, 80),),
        ("patella", 2): ((60, 80, 60, 80),),
        ("tibia", 0): ((100, 120, 40, 100),),
        ("medial_meniscus", 1): MENISCUS_A,
        ("fibula", 0): ((100, 120, 100, 120),),
    }
    arrays = {f"{s}_z{z}": _points(*blocks) for (s, z), blocks in outlines.items()}
    ownership: dict[str, dict] = {}
    for subject, z in outlines:
        member = f"{subject}_z{z}"
        ownership.setdefault(subject, {"addressed_supports": []})[
            "addressed_supports"
        ].append(_support_entry(subject, member, len(arrays[member]), z, 1))
    spatial = {
        "patella": {"keyplanes": {"sagittal": _sagittal(1)}},
        "tibia": {"keyplanes": {"sagittal": _sagittal(2)}},
        "medial_meniscus": {"keyplanes": {"sagittal": _sagittal(1)}},
        "femur": {"keyplanes": {"sagittal": _sagittal(1)}},
        "fibula": {"keyplanes": {"sagittal": _sagittal(1), "coronal": _sagittal(2)}},
    }
    manifest = {
        "study_uid": STUDY_UID,
        "object_composition": _composition(spatial),
        "source_roots": {},
        "support_ownership": ownership,
        "object_contexts": {},
    }
    return root, _Product(manifest, arrays)


def test_a_key_slice_without_an_outline_reads_the_nearest_saved_outline(
    tmp_path: Path,
) -> None:
    from knee.diagnosis.squint_profiles import read_study_squints

    def legs(study: dict) -> dict:
        maps = {}
        for series in study["series"]:
            leg = fixture.expected_leg_map()
            leg.update(study_uid=STUDY_UID, series_uid=series["series_uid"])
            maps[series["series_uid"]] = leg
        return maps

    root, product = _multislice_inputs(tmp_path)
    study = read_study_squints(root, STUDY_UID, io_workers=1)
    assert study["series"][0]["stack"].median.shape == (3, 8, 8)
    manifest = product.manifest
    profiles, regions, unprofiled, receipt = memory_module._territory_profile_regions(
        study,
        manifest["object_composition"]["objects"],
        memory_module._series_index(study),
        manifest["support_ownership"],
        manifest["source_roots"],
        manifest["object_contexts"],
        product.arrays,
        subjects=frozenset(memory_module._question_object_roles()),
        writer=_writer(legs),
    )
    # At its key slice: unchanged.
    meniscus = regions["medial_meniscus"][0]
    assert meniscus["source_slice"] == meniscus["key_slice"] == 1
    assert meniscus["slice_choice"]["rule"] == "key_slice"
    # No outline at key slice 1; outlines at 0 and 2 are equally near: the lower.
    patella = regions["patella"][0]
    assert patella["key_slice"] == 1 and patella["source_slice"] == 0
    assert patella["source_window"][:2] == [0, 1]
    assert patella["territory"]["tile_window"][:2] == [0, 1]
    assert patella["territory"]["native_support"]["slices"] == [0]
    assert patella["slice_choice"] == {
        "key_slice": 1,
        "used_slice": 0,
        "rule": "nearest_saved_support_in_series",
        "attempts": [
            {"slice": 1, "code": "support_unavailable"},
            {"slice": 0, "code": "valid"},
        ],
        "distance_slices": 1,
        "equally_near_slices": [2],
    }
    tibia = regions["tibia"][0]
    assert (tibia["key_slice"], tibia["source_slice"]) == (2, 0)
    assert tibia["slice_choice"]["distance_slices"] == 2
    assert tibia["slice_choice"]["equally_near_slices"] == []
    # No outline at any slice of the series: the key slice's refusal stands.
    assert "femur" not in regions and "femur" not in profiles
    assert unprofiled["femur"][0]["reason"] == "support_unavailable"
    assert unprofiled["femur"][0]["slice_choice"]["attempts"] == [
        {"slice": 1, "code": "support_unavailable"}
    ]
    # One outline is read once: the second region may not read it again.
    assert [row["source_slice"] for row in regions["fibula"]] == [0]
    refused = unprofiled["fibula"][0]
    assert (refused["key_slice"], refused["reason"]) == (2, "support_unavailable")
    assert refused["slice_choice"]["attempts"] == [
        {"slice": 2, "code": "support_unavailable"},
        {"slice": 0, "code": "support_slice_already_read"},
    ]
    assert receipt["subjects"]["patella"]["profiled_at_other_slice"] == 1
    assert receipt["subjects"]["fibula"] == {
        "regions": 2,
        "profiled_at_key_slice": 0,
        "profiled_at_other_slice": 1,
        "unprofiled": {"support_unavailable": 1},
    }
    for subject in ("patella", "tibia", "fibula", "medial_meniscus"):
        assert profiles[subject]["source"]["procedure"] == TERRITORY_PROCEDURE
    json.dumps(regions, allow_nan=False)
    json.dumps(unprofiled, allow_nan=False)


def test_same_box_different_places_change_the_territory_reading_only(
    tmp_path: Path,
) -> None:
    """Two-sign: the support's own places change v2's reading; v1's box cannot see them."""
    readings = [
        _read_regions(tmp_path / name, _writer(_LegMaps()), meniscus=meniscus)
        for name, meniscus in (("a", MENISCUS_A), ("b", MENISCUS_B))
    ]
    (profiles_a, regions_a, *_), (profiles_b, regions_b, *_) = readings
    region_a = regions_a["medial_meniscus"][0]
    region_b = regions_b["medial_meniscus"][0]
    # The same box: every v1 address field agrees.
    for key in ("source_window", "native_bounds_rc", "relative_extent"):
        assert region_a[key] == region_b[key]
    # Different places: the territory and its object reading differ.
    assert region_a["territory"]["role_counts"]["object"] == 4
    assert region_b["territory"]["role_counts"]["object"] == 2
    assert (
        region_a["territory"]["native_support"]["mask_sha256"]
        != region_b["territory"]["native_support"]["mask_sha256"]
    )
    assert (
        profiles_a["medial_meniscus"]["banks"] != profiles_b["medial_meniscus"]["banks"]
    )
    # Objects whose supports did not change read the same.
    assert profiles_a["tibia"]["banks"] == profiles_b["tibia"]["banks"]
    assert profiles_a["acl"]["banks"] == profiles_b["acl"]["banks"]


def test_a_refused_fine_reading_keeps_the_coarse_reading_and_its_reason(
    tmp_path: Path,
) -> None:
    writer = _writer(_LegMaps())

    def refuse(*args, **kwargs):
        raise ValueError("squint_refine_native_series_unavailable")

    writer["refine_territory"] = refuse
    profiles, regions, _, _ = _read_regions(tmp_path, writer)
    region = regions["medial_meniscus"][0]
    assert region["fine_refinement"] == (
        "refused:squint_refine_native_series_unavailable"
    )
    scales = {
        parse_territory_bank_name(name)["scale"]
        for name in profiles["medial_meniscus"]["banks"]
    }
    assert scales == {"10mm"}


def test_a_writer_profile_that_is_not_role_named_is_refused(tmp_path: Path) -> None:
    writer = _writer(_LegMaps())
    real = writer["profile_territory"]

    def v1_names(*args, **kwargs):
        profile = real(*args, **kwargs)
        profile["banks"] = {
            "squint/v1/view=x/metric=m/direction=d/scale=10mm": [1, 0, 0]
        }
        return profile

    writer["profile_territory"] = v1_names
    with pytest.raises(
        memory_module.SquintMemoryError, match="territory_profile_bank_not_role_named"
    ):
        _read_regions(tmp_path, writer)


def test_compile_script_selects_the_writer_and_keeps_its_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.compile_squint_memory as script
    from knee.diagnosis.squint_leg import leg_maps

    seen: dict = {}

    def compile_stand_in(root, products, out, **options):
        seen.update(root=root, products=products, out=out, **options)
        return {"schema": memory_module.SCHEMA, "case_count": 0}

    monkeypatch.setattr(script, "compile_bootstrap", compile_stand_in)
    receipt = tmp_path / "receipt.json"
    required = [
        "--root",
        str(tmp_path / "raw"),
        "--products",
        str(tmp_path / "products"),
        "--memory",
        str(tmp_path / "memory"),
    ]
    argv = [
        *required,
        "--writer",
        "territory-v2",
        "--leg-maps",
        "knee.diagnosis.squint_leg:leg_maps",
        "--study-uid",
        "a",
        "b",
        "--io-workers",
        "2",
        "--receipt",
        str(receipt),
    ]
    assert script.main(argv) == 0
    assert seen["writer"] == "territory-v2"
    assert seen["leg_maps"] is leg_maps
    assert seen["selected_uids"] == ("a", "b")
    assert seen["io_workers"] == 2
    record = json.loads(receipt.read_text(encoding="utf-8"))
    assert record["writer"] == "territory-v2"
    assert record["store"]["case_count"] == 0
    assert record["work"]["full_anatomy_runs"] == 0
    with pytest.raises(SystemExit, match="receipt_already_exists"):
        script.main(argv)
    seen.clear()
    assert script.main(required) == 0
    assert seen["writer"] == "squint-v1"
    assert seen["leg_maps"] is None and seen["selected_uids"] is None
    with pytest.raises(SystemExit, match="leg_maps_reference_invalid"):
        script.main([*required, "--writer", "territory-v2", "--leg-maps", "nocolon"])


@needs_configurations
def test_a_configuration_composes_the_roles_of_one_writer_only() -> None:
    from knee.diagnosis.squint_configurations import (
        ConfigurationProfileError,
        configuration_profile,
    )

    def role(subject: str, procedure: str, bank: str) -> dict:
        return {
            "schema": "knee.squint-profile/v1",
            "subject": subject,
            "banks": {bank: [1, 2, 0]},
            "source": {"procedure": procedure},
        }

    v2_bank = 'squint/v2/view=["Sagittal","1","1"]/role=object/metric=signal_median/direction=overview/scale=10mm'
    v1_procedure = "knee.squint-profile/scan-tercile-v1"
    acl = role("acl", TERRITORY_PROCEDURE, v2_bank)
    composed = configuration_profile({"acl": acl}, "ACL", procedure=TERRITORY_PROCEDURE)
    assert composed["source"]["procedure"] == TERRITORY_PROCEDURE
    assert composed["banks"] == {f"object/acl/{v2_bank}": [1, 2, 0]}
    tibia_v1 = role(
        "tibia", v1_procedure, "squint/v1/view=x/metric=m/direction=d/scale=10mm"
    )
    with pytest.raises(ConfigurationProfileError, match="procedure_mismatch"):
        configuration_profile(
            {"acl": acl, "tibia": tibia_v1}, "ACL", procedure=TERRITORY_PROCEDURE
        )
    # The default stays v1 and refuses a territory role rather than relabel it.
    with pytest.raises(ConfigurationProfileError, match="procedure_mismatch"):
        configuration_profile({"acl": acl}, "ACL")
    with pytest.raises(ConfigurationProfileError, match="procedure_unknown"):
        configuration_profile({}, "ACL", procedure="knee.squint-profile/other")


def test_one_memory_holds_one_writer() -> None:
    memory = {
        "cases": [
            {"profile": {"source": {"procedure": TERRITORY_PROCEDURE}}},
            {
                "profile": {
                    "source": {"procedure": "knee.squint-profile/scan-tercile-v1"}
                }
            },
        ]
    }
    with pytest.raises(
        memory_module.SquintMemoryError, match="memory_writer_procedure_mixed"
    ):
        memory_module._require_one_writer(memory, TERRITORY_PROCEDURE)
    memory["cases"].pop()
    memory_module._require_one_writer(memory, TERRITORY_PROCEDURE)


@needs_configurations
def test_territory_memory_keeps_calls_scope_and_payloads_and_publishes_its_own_revision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from knee.diagnosis.squint_locator import prepare_recall
    from knee.json_store import load_json

    root, products, product = _inputs(tmp_path)
    _, v1_raw = _compile(monkeypatch, root, products, product, tmp_path / "v1")
    legs = _LegMaps()
    receipt, v2_raw = _compile(
        monkeypatch,
        root,
        products,
        product,
        tmp_path / "v2",
        writer="territory-v2",
        leg_maps=legs,
    )
    v1, v2 = json.loads(v1_raw), json.loads(v2_raw)
    assert legs.calls == 1
    assert v2["revision"] == (
        "bootstrap-2026-10-21-territory-v2"
        "+portable-full-profiles-v1+question-configurations-v1"
    )
    assert receipt["revision"] == v2["revision"] != v1["revision"]
    assert receipt["writer"] == "territory-v2"
    assert v2["procedure"]["writer"] == "territory-v2"
    assert v2["procedure"]["profile_procedure"] == TERRITORY_PROCEDURE

    v1_objects, v2_objects = _object_cases(v1), _object_cases(v2)
    assert set(v2_objects) == {
        f"squint-case:{STUDY_UID}:{subject}"
        for subject in ("acl", "medial_meniscus", "tibia")
    }
    assert set(v2_objects) < set(v1_objects)
    for case_id, case in v2_objects.items():
        for field in OBJECT_CASE_FIELDS:
            assert case[field] == v1_objects[case_id][field], (case_id, field)
        assert (
            case["teaching_source"]["revision"] == "bootstrap-2026-10-21-territory-v2"
        )
        assert case["profile"]["source"]["procedure"] == TERRITORY_PROCEDURE
        assert all(parse_territory_bank_name(name) for name in case["profile"]["banks"])
        assert case["regions"] and all("territory" in row for row in case["regions"])
    assert [
        row["reason"]
        for row in v2_objects[f"squint-case:{STUDY_UID}:acl"]["unprofiled_regions"]
    ] == ["series_unavailable"]

    study = v2["territory_writer"]["studies"][STUDY_UID]
    assert study["unprofiled_subjects"]["femur"]["reason"] == "no_region_profiled"
    assert [
        row["reason"] for row in study["unprofiled_subjects"]["femur"]["regions"]
    ] == ["support_unavailable"]
    assert study["unprofiled_subjects"]["pcl"]["regions"][0]["reason"] == (
        "support_outside_leg"
    )
    assert v2["territory_writer"]["counts"]["objects_without_reading"] == 2

    # Configurations are rebuilt from the v2 object profiles; missing roles stay named.
    v1_configs, v2_configs = _configuration_cases(v1), _configuration_cases(v2)
    assert set(v2_configs) == set(v1_configs)
    for case_id, case in v2_configs.items():
        for field in ("condition_calls", "presentation_scope", "label_attribution"):
            assert case[field] == v1_configs[case_id][field]
        source = case["profile"]["source"]
        assert source["procedure"] == TERRITORY_PROCEDURE
        assert all(
            parse_territory_bank_name(name.split("/", 2)[2])
            for name in case["profile"]["banks"]
        )
    acl = v2_configs[f"squint-configuration:{STUDY_UID}:ACL"]["profile"]["source"]
    assert set(acl["roles"]) == {"acl", "tibia"}
    assert {row["subject"] for row in acl["missing_roles"]} == {"femur", "pcl"}

    # The prepared recall sidecar is rebuilt for the new manifest and restores.
    loaded = memory_module.load_memory(tmp_path / "v2")
    cache = load_json(tmp_path / "v2" / "recall-preparation.json")
    assert cache["memory_manifest_sha256"] == hashlib.sha256(v2_raw).hexdigest()
    assert cache["memory_revision"] == v2["revision"]
    restored = prepare_recall(loaded, cached=cache)
    assert restored["runtime_indexes_rebuilt"] is True
    assert restored["envelopes"] == prepare_recall(loaded)["envelopes"]
    # The old memory stays readable beside it, and neither is overwritten.
    assert memory_module.load_memory(tmp_path / "v1")["revision"] == V1_REVISION
    with pytest.raises(memory_module.SquintMemoryError, match="memory_already_exists"):
        _compile(
            monkeypatch,
            root,
            products,
            product,
            tmp_path / "v1",
            writer="territory-v2",
            leg_maps=_LegMaps(),
        )


@needs_configurations
def test_labels_change_calls_but_never_territory_profiles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Two-sign: a label is a teaching call only; it never moves a reading."""
    memories = []
    for name, acl in (("present", "1"), ("absent", "0")):
        root, products, product = _inputs(
            tmp_path / name, labels={**LABEL_ROW, "ACL": acl}
        )
        _, raw = _compile(
            monkeypatch,
            root,
            products,
            product,
            tmp_path / name / "memory",
            writer="territory-v2",
            leg_maps=_LegMaps(),
        )
        memories.append(_object_cases(json.loads(raw)))
    present, absent = memories
    case_id = f"squint-case:{STUDY_UID}:acl"
    assert present[case_id]["condition_calls"] == {"ACL": 1}
    assert absent[case_id]["condition_calls"] == {"ACL": -1}
    for key in present:
        assert present[key]["profile"]["banks"] == absent[key]["profile"]["banks"]
        territories = [row["territory"] for row in present[key]["regions"]]
        assert territories == [row["territory"] for row in absent[key]["regions"]]
