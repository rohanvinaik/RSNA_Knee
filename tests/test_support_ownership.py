from __future__ import annotations

import copy

import pytest

from knee.encoding.support_ownership import summarize_support_ownership


def profile(index: int, *, provenance: str = "native", view: list[str] | None = None):
    return {
        "profile_index": index,
        "object": "meniscus",
        "provenance": provenance,
        "kind": "reading",
        "support": "support_mask",
        "view": view or ["sagittal", "fluid", "fat_dark"],
        "outcomes": [
            {
                "status": "encoded",
                "encoding_status": "encoded",
                "address_kind": "native_rc",
                "artifact": "artifact-a",
                "target_artifact": "artifact-a",
                "target_series_uid": "series-a",
                "owner_series_uid": "series-a",
                "record_view": ["sagittal", "fluid", "fat_dark"],
                "record_slice_index": 0,
                "owner_view": ["sagittal", "fluid", "fat_dark"],
                "owner_slice_index": 0,
                "points_rc": "coords-0",
                "place_count": 0,
                "metrics": [
                    {
                        "bank": "sag_native",
                        "metric": "enclosure",
                        "status": "measured",
                        "row_names": ["negative", "zero", "positive"],
                        "row_codes": "codes-0",
                        "source_values": "values-0",
                        "available": "available-0",
                        "nonfinite_available_count": 0,
                    }
                ],
                "metadata": {
                    "observation": {
                        "study_uid": "study-a",
                        "series_uid": "series-a",
                        "view": ["sagittal", "fluid", "fat_dark"],
                        "slice_index": 0,
                        "support": "support_mask",
                        "row": 0,
                        "label": 0,
                        "artifact": "artifact-a",
                        "slices": [0],
                        "address_frame": {"source": "native_slice_frame"},
                    },
                    "source_refs": {
                        "support_mask": {
                            "artifact": "artifact-a",
                            "digest": "abc",
                            "shape": [0, 4],
                            "dtype": "bool",
                        }
                    },
                    "bindings": [
                        {
                            "bank": "sag_native",
                            "metric": "enclosure",
                            "value": "values-0",
                            "available": "available-0",
                        }
                    ],
                    "references": [],
                    "plane_frame": {
                        "origin_lps": [0.0, 0.0, 0.0],
                        "basis": [[1, 0], [0, 1], [0, 0]],
                    },
                    "plane_frame_source": "observation_address_frame",
                    "native_shape_rc": [0, 4],
                },
            }
        ],
    }


def test_zero_count_row_zero_and_global_filtered_profile_index_are_retained():
    p = profile(19)
    result = summarize_support_ownership("meniscus", [(19, p)])
    assert result["addressed_supports"][0]["links"][0]["profile_index"] == 19
    link = result["addressed_supports"][0]["links"][0]
    assert link["place_count"] == 0
    assert link["metrics"][0]["row_names"][0] == "negative"
    assert result["physical_volume"] == "not_measured"


def test_exact_duplicate_deduplicates_but_retains_both_member_links():
    first = profile(2)
    second = copy.deepcopy(first)
    second["profile_index"] = 7
    second["outcomes"][0]["points_rc"] = "coords-copy"
    second["outcomes"][0]["metrics"][0]["row_codes"] = "codes-copy"
    second["outcomes"][0]["metrics"][0]["source_values"] = "values-copy"
    second["outcomes"][0]["metrics"][0]["available"] = "available-copy"
    second["outcomes"][0]["metadata"]["bindings"][0]["value"] = "values-copy"
    second["outcomes"][0]["metadata"]["bindings"][0]["available"] = "available-copy"
    result = summarize_support_ownership("meniscus", [first, second])
    assert len(result["addressed_supports"]) == 1
    links = result["addressed_supports"][0]["links"]
    assert [link["profile_index"] for link in links] == [2, 7]
    assert {link["coordinate_field"] for link in links} == {"points_rc"}
    assert {link["coordinate_member"] for link in links} == {"coords-0", "coords-copy"}
    assert {link["metrics"][0]["row_codes_member"] for link in links} == {
        "codes-0",
        "codes-copy",
    }


def test_conflicting_meaning_is_named_and_provenance_or_view_is_not_pooled():
    first = profile(1)
    changed = copy.deepcopy(first)
    changed["profile_index"] = 2
    changed["outcomes"][0]["metadata"]["source_refs"]["support_mask"]["digest"] = (
        "different"
    )
    other_view = profile(3, view=["axial", "fluid", "fat_dark"])
    result = summarize_support_ownership("meniscus", [first, changed, other_view])
    assert result["conflicts"][0]["code"] == "source_address_meaning_conflict"
    assert len(result["addressed_supports"]) == 2
    laid = profile(4, provenance="laid")
    result2 = summarize_support_ownership("meniscus", [first, laid])
    assert len(result2["addressed_supports"]) == 2


def test_named_nonplace_outcomes_preserve_unknown_count_and_metadata():
    p = profile(0)
    outcome = p["outcomes"][0]
    outcome.pop("points_rc")
    outcome["place_count"] = None
    outcome["status"] = "target_only"
    result = summarize_support_ownership("meniscus", [p])
    assert result["addressed_supports"] == []
    assert result["non_place_outcomes"][0]["status"] == "target_only"
    assert result["non_place_outcomes"][0]["place_count"] is None
    assert (
        result["non_place_outcomes"][0]["source_refs"]["support_mask"]["digest"]
        == "abc"
    )


def test_coarse_grid_keeps_owner_target_window_block_scale_and_no_pixel_claim():
    p = profile(0)
    out = p["outcomes"][0]
    out["address_kind"] = "coarse_grid_rc"
    out.pop("points_rc")
    out["scope_coordinates"] = "grid_rc"
    out["owner_series_uid"] = "fibula-holder"
    out["target_series_uid"] = "target-series"
    out["metadata"].update(
        {
            "scope_address": {
                "target_series_uid": "target-series",
                "window_rc": [10, 30, 20, 40],
                "block_px": [4, 4],
                "block_mm": [2.0, 2.0],
                "grid_shape": [5, 5],
            },
            "lineage": {"owner_artifact": "holder", "packed_row": 0},
            "count_interpreted_as_blocks": True,
            "support_block_count": 0,
        }
    )
    result = summarize_support_ownership("meniscus", [p])
    source = result["addressed_supports"][0]["source_address"]
    assert source["address_kind"] == "coarse_grid_rc"
    assert source["scope_address"]["window_rc"] == [10, 30, 20, 40]
    assert source["scope_address"]["block_mm"] == [2.0, 2.0]
    assert source["owner_series_uid"] == "fibula-holder"
    assert source["target_series_uid"] == "target-series"
    assert result["physical_volume"] == "not_measured"


def test_missing_acquisition_or_frame_stays_unresolved_and_input_is_unchanged():
    p = profile(0)
    p["outcomes"][0]["metadata"].pop("plane_frame")
    p["outcomes"][0]["target_series_uid"] = None
    p["outcomes"][0]["owner_series_uid"] = "owner-series-must-not-substitute"
    p["outcomes"][0]["metadata"]["observation"]["series_uid"] = None
    before = copy.deepcopy(p)
    result = summarize_support_ownership("meniscus", [p])
    assert result["cross_acquisition_overlap"] == "unresolved"
    assert result["geometry_retention"] == "no_frame_retained_or_unknown"
    address = result["addressed_supports"][0]["source_address"]
    assert address["observation_slices"] == [0]
    assert address["record_slice_index"] == 0
    assert address["observation_address_frame"] == {"source": "native_slice_frame"}
    assert p == before


def test_filtered_profiles_require_original_index_and_reject_relabeling():
    p = profile(0)
    with pytest.raises(ValueError, match="global_profile_index_required"):
        summarize_support_ownership("meniscus", [p | {"profile_index": None}])
    with pytest.raises(ValueError, match="profile_index_disagreement"):
        summarize_support_ownership("meniscus", [(8, p)], profile_indices=[9])
    with pytest.raises(ValueError, match="profile_index_disagreement"):
        summarize_support_ownership("meniscus", [(8, p)])
    with pytest.raises(ValueError, match="profile_index_disagreement"):
        summarize_support_ownership("meniscus", [p], profile_indices=[9])


def test_caller_study_uid_is_retained_without_replacing_unknown_target_address():
    p = profile(0)
    p["outcomes"][0]["target_series_uid"] = None
    result = summarize_support_ownership("meniscus", [p], study_uid="caller-study")
    address = result["addressed_supports"][0]["source_address"]
    assert address["caller_study_uid"] == "caller-study"
    assert address["target_series_uid"] is None
    assert address["owner_series_uid"] == "series-a"
    assert result["cross_acquisition_overlap"] == "unresolved"
