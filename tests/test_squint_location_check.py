from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

import scripts.squint_location_check as script
import tests.squint_upgrade_fixtures as fixture
from knee.diagnosis import squint_location_check as check
from knee.diagnosis.squint_interfaces import ROLE_CONTEXT, ROLE_OBJECT, ROLE_UNQUERIED
from knee.diagnosis.squint_memory import SCHEMA as MEMORY_SCHEMA
from knee.diagnosis.squint_memory import MemorySnapshot
from knee.json_store import dump_json_atomic
from knee.study.tables import LABELS

STUDY = fixture.STUDY_UID
SERIES = fixture.SERIES_UID
OTHER_SERIES = "1.2.826.0.1.3680043.8.498.fixture.other-series"
SUBJECT = "medial_meniscus"
#: The fixture's dark body, tiles rows 3-4 and columns 3-4, on slice 1.
SUPPORT_WINDOW = [1, 2, 3, 5, 3, 5]
DARK_BODY_TILES = np.array([[1, 3, 3], [1, 3, 4], [1, 4, 3], [1, 4, 4]])


def _support_region(
    window=SUPPORT_WINDOW, *, extent="retained_object_support", series=SERIES
):
    return {
        "series_uid": series,
        "source_window": list(window),
        "source_slice": window[0],
        "extent_source": extent,
        "support_code": "selected",
        "native_bounds_rc": [60, 100, 60, 100],
        "view": dict(fixture.VIEW),
    }


def _case(subject=SUBJECT, regions=None, study=STUDY):
    return {
        "case_id": f"squint-case:{study}:{subject}",
        "study_uid": study,
        "subject": subject,
        "condition_calls": {},
        "profile": {
            "schema": "knee.squint-profile/v1",
            "subject": subject,
            "banks": {},
            "source": {},
        },
        "regions": [_support_region()] if regions is None else regions,
        "full_source": {
            "product_path": "/nonexistent/product.h5",
            "product_sha256": "0" * 64,
            "study_uid": study,
        },
    }


def _located(window, *, series=SERIES):
    return {"series_uid": series, "view": dict(fixture.VIEW), "window": list(window)}


def _record(regions, *, subject=SUBJECT, status="proposal", study=STUDY):
    return {
        "schema": "knee.squint-study/v1",
        "study_uid": study,
        "memory_revision": "fixture-revision",
        "study_status": "examined",
        "objects": {subject: {"status": status, "regions": regions}},
    }


def _check(record, cases, coverage=None):
    references = check.own_references(cases)
    rows, _unlocated = check.located_rows(record)
    return [check.check_row(row, references, coverage) for row in rows]


def _territory(object_tiles, *, window=(1, 2, 0, 6, 0, 6), origin="anchor_structure"):
    territory = fixture.teacher_territory(SUBJECT)
    z0, z1, r0, r1, c0, c1 = window
    roles = np.full((z1 - z0, r1 - r0, c1 - c0), ROLE_CONTEXT, dtype=np.int8)
    for z, r, c in object_tiles:
        roles[z - z0, r - r0, c - c0] = ROLE_OBJECT
    territory.update(
        {
            "origin": origin,
            "tile_window": list(window),
            "roles": roles,
            "object_share": np.full(roles.shape, np.nan, dtype=np.float32),
        }
    )
    return territory


def _bounds():
    return np.asarray(fixture.series_record()["stack"].bounds_rc)


def _dark_body_mask():
    mask = np.zeros(
        (fixture.ROWS * fixture.TILE_PX, fixture.COLS * fixture.TILE_PX), bool
    )
    mask[60:100, 60:100] = True
    return mask


# The job's three required cases.


def test_a_located_window_equal_to_its_own_support_is_on_target():
    [row] = _check(_record([_located(SUPPORT_WINDOW)]), [_case()])
    assert row["reference_code"] == "judged"
    [pair] = row["pairs"]
    assert pair["reference"]["kind"] == check.NATIVE_SUPPORT
    judgment = pair["judgment"]
    assert judgment["centre_inside_support_box"]
    assert judgment["within_slice_tolerance"]
    assert judgment["on_target"]
    assert judgment["slice_offset"] == 0
    assert judgment["in_plane_iou"] == 1.0
    summary = check.summarize([row])[SUBJECT]["all_views"][check.NATIVE_SUPPORT]
    assert (summary["pairs"], summary["on_target"]) == (1, 1)


def test_a_located_window_three_slices_off_is_not_on_target():
    [row] = _check(_record([_located([4, 5, 3, 5, 3, 5])]), [_case()])
    judgment = row["pairs"][0]["judgment"]
    assert judgment["centre_inside_support_box"]
    assert judgment["slice_offset"] == 3
    assert not judgment["within_slice_tolerance"]
    assert not judgment["on_target"]
    [edge] = _check(_record([_located([3, 4, 3, 5, 3, 5])]), [_case()])
    assert edge["pairs"][0]["judgment"]["slice_offset"] == check.SLICE_TOLERANCE
    assert edge["pairs"][0]["judgment"]["on_target"]


def test_a_region_whose_series_has_no_own_support_is_unknown_never_a_miss():
    record = _record(
        [_located(SUPPORT_WINDOW), _located([1, 2, 0, 2, 0, 2], series=OTHER_SERIES)]
    )
    rows = _check(record, [_case()])
    assert [row["reference_code"] for row in rows] == [
        "judged",
        "no_own_region_in_series",
    ]
    assert rows[1]["pairs"] == []
    summary = check.summarize(rows)[SUBJECT]["all_views"]
    assert summary["located_regions"] == 2
    assert summary["unknown_reference"] == {"no_own_region_in_series": 1}
    assert summary[check.NATIVE_SUPPORT]["pairs"] == 1
    assert summary[check.NATIVE_SUPPORT]["on_target"] == 1
    [missing] = _check(
        _record([_located([4, 5, 0, 2, 0, 2])], subject="acl"), [_case()]
    )
    assert missing["reference_code"] == "no_own_case"
    assert missing["pairs"] == []


def test_the_support_box_is_half_open_like_every_window():
    # Centre (5, 5) sits on the far edge of rows and columns 3-4: outside.
    [far] = _check(_record([_located([1, 2, 4, 6, 4, 6])]), [_case()])
    assert far["located"]["centre_rc"] == [5.0, 5.0]
    assert not far["pairs"][0]["judgment"]["centre_inside_support_box"]
    # Centre (3, 3) sits on the near edge: inside.
    [near] = _check(_record([_located([1, 2, 2, 4, 2, 4])]), [_case()])
    assert near["located"]["centre_rc"] == [3.0, 3.0]
    assert near["pairs"][0]["judgment"]["centre_inside_support_box"]


# What the yardstick is measured against.


def test_a_physical_location_is_judged_apart_never_as_a_support_hit_or_miss():
    point = _support_region([1, 2, 3, 4, 3, 4], extent="retained_physical_location")
    rows = _check(_record([_located([1, 2, 0, 6, 0, 6])]), [_case(regions=[point])])
    [pair] = rows[0]["pairs"]
    assert pair["reference"]["kind"] == check.PHYSICAL_LOCATION
    summary = check.summarize(rows)[SUBJECT]["all_views"]
    assert summary[check.NATIVE_SUPPORT]["pairs"] == 0
    assert summary[check.PHYSICAL_LOCATION]["pairs"] == 1
    assert check.pooled_reference_table(rows)[SUBJECT]["pairs"] == 1


def test_unusable_own_regions_and_located_windows_have_named_codes():
    odd = _support_region()
    odd["extent_source"] = "something_else"
    [row] = _check(_record([_located(SUPPORT_WINDOW)]), [_case(regions=[odd])])
    assert row["reference_code"] == "own_region_extent_unrecognized"
    broken = _support_region()
    broken["source_window"] = [1, 1, 3, 5, 3, 5]
    [row] = _check(_record([_located(SUPPORT_WINDOW)]), [_case(regions=[broken])])
    assert row["reference_code"] == "own_region_window_invalid"
    [row] = _check(
        _record([{"series_uid": SERIES, "view": dict(fixture.VIEW)}]), [_case()]
    )
    assert row["located_code"] == "located_window_missing"
    [row] = _check(_record([_located([1, 2, 3, 5, 3, 3])]), [_case()])
    assert row["located_code"] == "located_window_invalid"
    summary = check.summarize([row])[SUBJECT]["all_views"]
    assert summary["located_defects"] == {"located_window_invalid": 1}
    assert summary[check.NATIVE_SUPPORT]["pairs"] == 0


def test_a_teacher_location_region_is_read_by_the_production_address_rule():
    region = {k: v for k, v in _support_region().items() if k != "native_bounds_rc"}
    [row] = _check(_record([region]), [_case()])
    assert row["located_window_key"] == "source_window"
    assert row["pairs"][0]["judgment"]["on_target"]


class _NoLabels(dict):
    """A case or memory that fails the test if a label-bearing field is read."""

    FORBIDDEN = frozenset(
        {"condition_calls", "label_attribution", "presentation_scope", "label_ledger"}
    )

    def __getitem__(self, key):
        if key in self.FORBIDDEN:
            raise AssertionError(f"label field read: {key}")
        return super().__getitem__(key)

    def get(self, key, default=None):
        if key in self.FORBIDDEN:
            raise AssertionError(f"label field read: {key}")
        return super().get(key, default)

    def __iter__(self):
        raise AssertionError("whole case iterated")

    def keys(self):
        raise AssertionError("whole case iterated")

    def items(self):
        raise AssertionError("whole case iterated")

    def values(self):
        raise AssertionError("whole case iterated")


def test_labels_are_never_read():
    case = _case()
    case["condition_calls"] = {"Medial Meniscus": 1}
    case["presentation_scope"] = {"Medial Meniscus": "positive_condition_presentation"}
    [row] = _check(_record([_located(SUPPORT_WINDOW)]), [_NoLabels(case)])
    assert row["pairs"][0]["judgment"]["on_target"]


# A box is an address; a territory's object tiles are the claim.


def test_a_territory_is_judged_by_its_object_tiles_not_its_window():
    support = _support_region([1, 2, 4, 5, 4, 5])
    window = [1, 2, 0, 6, 0, 6]
    [box] = _check(_record([_located(window)]), [_case(regions=[support])])
    assert box["located"]["source"] == "window_without_territory"
    assert not box["pairs"][0]["judgment"]["centre_inside_support_box"]
    on_support = {**_located(window), "territory": _territory(DARK_BODY_TILES)}
    [row] = _check(_record([on_support]), [_case(regions=[support])])
    assert row["located"]["source"] == "territory_object_role"
    assert row["located"]["centre_rc"] == [4.0, 4.0]
    assert row["pairs"][0]["judgment"]["on_target"]
    quieter = _territory(DARK_BODY_TILES)
    quieter["roles"][quieter["roles"] == ROLE_CONTEXT] = ROLE_UNQUERIED
    [same] = _check(
        _record([{**_located(window), "territory": quieter}]),
        [_case(regions=[support])],
    )
    assert same["pairs"][0]["judgment"] == row["pairs"][0]["judgment"]
    elsewhere = {**_located(window), "territory": _territory([(1, 1, 1)])}
    [miss] = _check(_record([elsewhere]), [_case(regions=[support])])
    assert not miss["pairs"][0]["judgment"]["centre_inside_support_box"]


def test_a_serialized_territory_reads_like_its_runtime_shape():
    runtime = fixture.teacher_territory(SUBJECT)
    share = runtime["object_share"]
    address = {
        **runtime,
        "roles": runtime["roles"].astype(np.int64).tolist(),
        "object_share": np.where(np.isfinite(share), share, None).tolist(),
        "native_support": {
            "slices": [1],
            "offset_rc": [60, 60],
            "shape": [1, 40, 40],
            "pixel_count": 1600,
            "mask_sha256": "0" * 64,
        },
    }
    address = json.loads(json.dumps(address))
    normalized, code = check.territory_runtime(address)
    assert code == "valid"
    assert normalized is not None
    assert normalized["native_support"] is None
    np.testing.assert_array_equal(normalized["roles"], runtime["roles"])
    row = {
        "study_uid": STUDY,
        "subject": SUBJECT,
        "series_uid": SERIES,
        "located_window": runtime["tile_window"],
    }
    from_runtime = check.located_object_tiles({**row, "territory": runtime})
    from_record = check.located_object_tiles({**row, "territory": address})
    assert from_runtime["centre_rc"] == from_record["centre_rc"] == [4.0, 4.0]
    assert from_runtime["slice"] == from_record["slice"] == 1
    np.testing.assert_array_equal(from_runtime["tiles"], from_record["tiles"])
    unknown_role = json.loads(json.dumps(address))
    unknown_role["roles"][0][0][0] = 7
    assert check.territory_runtime(unknown_role) == (None, "territory_role_unknown")
    other_series = check.located_object_tiles(
        {**row, "series_uid": OTHER_SERIES, "territory": address}
    )
    assert other_series == {"code": "territory_identity_mismatch"}


# (d): the support's own native pixels.


def test_support_coverage_counts_the_supports_own_pixels():
    mask, bounds = _dark_body_mask(), _bounds()
    full = check.support_coverage(DARK_BODY_TILES, 1, mask, bounds)
    assert full["code"] == "measured"
    assert (full["support_pixels"], full["share_on_key_slice"]) == (1600, 1.0)
    assert check.support_coverage(DARK_BODY_TILES[:1], 1, mask, bounds)[
        "share_on_key_slice"
    ] == pytest.approx(0.25)
    shifted = check.support_coverage(DARK_BODY_TILES + [3, 0, 0], 1, mask, bounds)
    assert shifted["share_on_key_slice"] == 0.0
    assert shifted["share_in_plane"] == 1.0
    lopsided = np.zeros_like(mask)
    lopsided[60:80, 60:80] = True
    lopsided[99, 99] = True
    same_box = check.support_coverage(DARK_BODY_TILES[:1], 1, lopsided, bounds)
    assert same_box["share_on_key_slice"] == pytest.approx(400 / 401)
    assert check.support_coverage(DARK_BODY_TILES, 1, np.zeros_like(mask), bounds) == {
        "code": "support_empty"
    }
    assert check.support_coverage(DARK_BODY_TILES, 1, mask[:100], bounds) == {
        "code": "support_frame_mismatch"
    }
    assert check.support_coverage(DARK_BODY_TILES + [0, 9, 0], 1, mask, bounds) == {
        "code": "object_tiles_outside_grid"
    }


def test_coverage_is_measured_only_for_a_territory_on_a_native_support():
    calls = []

    def coverage(row, reference, tiles):
        calls.append(reference["kind"])
        return check.support_coverage(
            tiles, reference["key_slice"], _dark_body_mask(), _bounds()
        )

    territory_row = {
        **_located([1, 2, 0, 6, 0, 6]),
        "territory": _territory(DARK_BODY_TILES),
    }
    [measured] = _check(_record([territory_row]), [_case()], coverage)
    assert measured["pairs"][0]["coverage"]["share_on_key_slice"] == 1.0
    [unrequested] = _check(_record([territory_row]), [_case()])
    assert unrequested["pairs"][0]["coverage"] == {"code": "coverage_not_requested"}
    [box_only] = _check(_record([_located(SUPPORT_WINDOW)]), [_case()], coverage)
    assert "coverage" not in box_only["pairs"][0]
    point = _support_region(extent="retained_physical_location")
    [location] = _check(_record([territory_row]), [_case(regions=[point])], coverage)
    assert "coverage" not in location["pairs"][0]
    assert calls == [check.NATIVE_SUPPORT]
    summary = check.summarize([measured, box_only])[SUBJECT]["all_views"]
    coverage_summary = summary[check.NATIVE_SUPPORT]["territory_coverage"]
    assert coverage_summary["codes"] == {"measured": 1, "no_territory": 1}
    assert coverage_summary["median_share_on_key_slice"] == 1.0


def test_unlocated_supports_name_what_became_of_the_object():
    cases = [_case(regions=[_support_region(), _support_region(series=OTHER_SERIES)])]
    references = check.own_references(cases)
    record = _record([_located(SUPPORT_WINDOW)])
    rows, unlocated = check.located_rows(record)
    checked = [check.check_row(row, references) for row in rows]
    [missing] = check.unlocated_supports(STUDY, checked, unlocated, references)
    assert (missing["series_uid"], missing["object_state"]) == (
        OTHER_SERIES,
        "located_in_other_series",
    )
    record = _record([], status="unresolved_missing_reading")
    rows, unlocated = check.located_rows(record)
    states = [
        item["object_state"]
        for item in check.unlocated_supports(STUDY, [], unlocated, references)
    ]
    assert states == ["not_located:unresolved_missing_reading"] * 2


def test_the_pooled_table_follows_the_leads_rounding_and_median():
    regions = [
        _located(window)
        for window in ([1, 2, 3, 5, 3, 5], [4, 5, 0, 2, 0, 2], [5, 6, 3, 4, 3, 4])
    ]
    cases = [_case(regions=[_support_region()])]
    rows = [
        check.check_row(row, check.own_references(cases))
        for row in check.located_rows(_record(regions))[0]
    ]
    table = check.pooled_reference_table(rows)[SUBJECT]
    assert table["pairs"] == 3
    assert table["in_plane_overlap"] == round(2 / 3, 2)
    assert table["centre_inside_support_box"] == round(2 / 3, 2)
    assert table["within_2_slices_of_key"] == round(1 / 3, 2)
    assert table["centre_inside_and_within_2_slices"] == round(1 / 3, 2)
    assert table["median_iou"] == 0.25
    assert table["median_slice_offset"] == 3


# The script, end to end.


def _write_memory(directory: Path, cases) -> str:
    memory = {
        "schema": MEMORY_SCHEMA,
        "revision": "fixture-revision",
        "questions": list(LABELS),
        "label_ledger": {},
        "cases": cases,
    }
    directory.mkdir(parents=True)
    raw = json.dumps(memory).encode()
    (directory / "manifest.json").write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


def _write_run(directory: Path, records, *, memory_sha: str | None) -> Path:
    studies = directory / "diagnostics" / "studies"
    rows = []
    for record in records:
        path = dump_json_atomic(studies / f"{record['study_uid']}.json", record)
        rows.append(
            {"study_uid": record["study_uid"], "evidence_path": f"studies/{path.name}"}
        )
    if memory_sha is not None:
        receipt = {
            "schema": "knee.squint-run/v1",
            "memory_manifest_sha256": memory_sha,
            "memory_revision": "fixture-revision",
            "work": {"studies": rows},
        }
        (directory / "diagnostics" / "receipt.json").write_text(json.dumps(receipt))
    return directory


def test_the_script_writes_its_report_and_refuses_to_overwrite(tmp_path, capsys):
    configuration = _case(subject="diagnosis/Medial Meniscus", regions=[])
    memory_sha = _write_memory(tmp_path / "memory", [_case(), configuration])
    record = _record(
        [
            _located(SUPPORT_WINDOW),
            _located([4, 5, 3, 5, 3, 5]),
            _located([1, 2, 0, 1, 0, 1], series=OTHER_SERIES),
        ]
    )
    run = _write_run(tmp_path / "run", [record], memory_sha=memory_sha)
    output, markdown = tmp_path / "out" / "check.json", tmp_path / "out" / "check.md"
    argv = [
        "--run",
        str(run),
        "--memory",
        str(tmp_path / "memory"),
        "--output",
        str(output),
    ]
    assert script.main([*argv, "--markdown", str(markdown)]) == 0
    report = json.loads(output.read_text())
    assert report["memory"]["matches_run"] is True
    assert report["run"]["study_index"] == "receipt"
    assert report["criteria"]["labels_read"] is False
    support = report["objects"][SUBJECT]["all_views"][check.NATIVE_SUPPORT]
    assert (
        support["pairs"],
        support["on_target"],
        support["within_slice_tolerance"],
    ) == (2, 1, 1)
    assert report["objects"][SUBJECT]["all_views"]["unknown_reference"] == {
        "no_own_region_in_series": 1
    }
    assert (
        f"| {SUBJECT} | 3 | 2 | 2/2 (100%) | 1/2 (50%) | 1/2 (50%) |"
        in markdown.read_text()
    )
    assert script.main(argv) == 2
    assert "output_already_exists" in capsys.readouterr().err


def test_the_script_reads_a_run_without_a_receipt(tmp_path):
    _write_memory(tmp_path / "memory", [_case()])
    run = _write_run(
        tmp_path / "run", [_record([_located(SUPPORT_WINDOW)])], memory_sha=None
    )
    report = script.check_run(run / "diagnostics", tmp_path / "memory")
    assert report["run"]["study_index"] == "directory_listing"
    assert report["memory"]["matches_run"] == "run_identity_unavailable"
    assert (
        report["objects"][SUBJECT]["all_views"][check.NATIVE_SUPPORT]["on_target"] == 1
    )
    with pytest.raises(
        script.LocationCheckError, match="run_studies_directory_missing"
    ):
        script.check_run(tmp_path / "memory", tmp_path / "memory")


def test_the_script_never_reads_labels_from_the_memory(tmp_path, monkeypatch):
    _write_memory(tmp_path / "memory", [_case()])
    run = _write_run(
        tmp_path / "run", [_record([_located(SUPPORT_WINDOW)])], memory_sha=None
    )
    guarded = _NoLabels(
        {
            "schema": MEMORY_SCHEMA,
            "revision": "fixture-revision",
            "label_ledger": {STUDY: {"Medial Meniscus": 1}},
            "cases": [
                _NoLabels({**_case(), "condition_calls": {"Medial Meniscus": 1}})
            ],
        }
    )
    snapshot = MemorySnapshot(
        tmp_path / "memory" / "manifest.json",
        "a" * 64,
        "squint",
        MEMORY_SCHEMA,
        guarded,
    )
    monkeypatch.setattr(script, "load_memory_snapshot", lambda _path: snapshot)
    report = script.check_run(run, tmp_path / "memory")
    assert (
        report["objects"][SUBJECT]["all_views"][check.NATIVE_SUPPORT]["on_target"] == 1
    )


def test_the_script_measures_coverage_only_with_both_inputs(tmp_path, monkeypatch):
    _write_memory(tmp_path / "memory", [_case()])
    region = {**_located([1, 2, 0, 6, 0, 6]), "territory": _territory(DARK_BODY_TILES)}
    region["territory"] = {
        **region["territory"],
        "roles": region["territory"]["roles"].tolist(),
        "object_share": [[[None] * 6] * 6],
    }
    run = _write_run(tmp_path / "run", [_record([region])], memory_sha=None)

    def coverage_codes(**kwargs):
        report = script.check_run(run, tmp_path / "memory", **kwargs)
        return report["objects"][SUBJECT]["all_views"][check.NATIVE_SUPPORT][
            "territory_coverage"
        ]

    supplied = coverage_codes(
        support_mask_for=lambda subject, series, key_slice, source: (
            _dark_body_mask(),
            "resolved",
        ),
        bounds_reader=lambda study_uid: {SERIES: _bounds()},
    )
    assert supplied["codes"] == {"measured": 1}
    assert supplied["median_share_on_key_slice"] == 1.0
    assert coverage_codes()["codes"] == {"tile_bounds_unavailable_no_root": 1}
    (tmp_path / "no-scans").mkdir()
    assert coverage_codes(root=tmp_path / "no-scans")["codes"] == {
        "tile_bounds_unreadable": 1
    }
    monkeypatch.setattr(script, "_default_support_resolver", lambda: None)
    assert coverage_codes(bounds_reader=lambda study_uid: {SERIES: _bounds()})[
        "codes"
    ] == {"support_mask_resolver_unavailable": 1}


def test_the_product_support_lookup_refuses_before_opening_a_wrong_product(tmp_path):
    def resolver(*_args):
        raise AssertionError("resolver reached without a verified product")

    lookup = script.product_support_mask(resolver)
    assert lookup(
        SUBJECT, SERIES, 1, {"product_path": str(tmp_path / "absent.h5")}
    ) == (
        None,
        "support_product_missing",
    )
    product = tmp_path / "product.h5"
    product.write_bytes(b"not the recorded product")
    assert lookup(
        SUBJECT, SERIES, 1, {"product_path": str(product), "product_sha256": "0" * 64}
    ) == (
        None,
        "support_product_sha256_mismatch",
    )
    assert script.product_support_mask(None)(SUBJECT, SERIES, 1, {}) == (
        None,
        "support_mask_resolver_unavailable",
    )
