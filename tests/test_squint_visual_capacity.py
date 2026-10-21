"""The parts of the recall picture sheets that decide what they claim to show
(scripts/squint_visual_capacity.py).

The sheets are development pictures; these tests pin what they claim to show:
the banks a comparison actually read, the exact decode of a difference, the
query profile recall actually used, a box drawn as an address with the
object's own places drawn separately, and the pins that tie a sheet to the run,
memory, code, tile grid and leg map it was written with. A territory-v2 reading
is built here by the production writer (``profile_territory``) from the shared
fixtures, so the script is read against the shape production records, not
against a copy of its own assumptions. Nothing here reads a real study.
"""

from __future__ import annotations

import copy
import hashlib
import json
from fractions import Fraction

import numpy as np
import pytest
from pydicom.uid import generate_uid

from knee.diagnosis import squint_interfaces as shapes
from knee.diagnosis import squint_locator as locator
from knee.diagnosis import squint_profiles as writer
from knee.diagnosis.squint_contracts import combine_condition
from knee.diagnosis.squint_interfaces import ROLE_OBJECT, territory_bank_name
from knee.diagnosis.squint_profiles import cosine_evidence
from knee.diagnosis.squint_questions import question_selection
from scripts.squint_visual_capacity import (
    VisualCapacityError,
    _caption_lines,
    _caption_rows,
    _panel_caption,
    _plan_summary,
    _subject_lines,
    _wrap,
    bank_blocks,
    bank_difference,
    bank_words,
    check_memory_pins,
    chosen_questions,
    compared_roles,
    draw_roles,
    draw_sheet,
    grid_pin,
    inset_corner,
    leg_codes_digest,
    leg_map_pin,
    main,
    named_differences,
    object_box,
    parse_bank,
    profile_before_fine_reading,
    profile_territories,
    question_plan,
    read_images,
    reading_panels,
    recalled_query_profile,
    region_panels,
    region_window,
    row_words,
    selection_pin,
    sheet_requests,
    source_pin,
    support_in_window,
    teaching_phrase,
    teaching_words,
    term_reproduction,
    territory_summary,
    verified_product,
    window_anchors,
    window_native_bounds,
)
from tests import squint_upgrade_fixtures as fixtures
from tests.test_squint_profiles import _write_dicom, _write_tables
from tests.test_squint_profiles_territory import _native_fixture

PROCEDURE = "knee.squint-profile/scan-tercile-v1"
VIEW = '["Coronal","0","0"]'
LENS_BANK = 'facet:["lens_boolean",["Coronal","0","0"],"b1","retained_place",null]'
CONTEXT_BANK = (
    'facet:["acquisition_context",["Coronal","0","0"],"record_context",'
    '"acquisition_record",null]'
)


def bank(metric: str, direction: str, scale: str = "10", view: str = VIEW) -> str:
    return (
        f"squint/v1/view={view}/metric={metric}/direction={direction}/scale={scale}mm"
    )


def profile(banks: dict, subject: str = "medial_meniscus") -> dict:
    return {
        "schema": "knee.squint-profile/v1",
        "subject": subject,
        "banks": {name: list(counts) for name, counts in banks.items()},
        "source": {"procedure": PROCEDURE},
    }


def recorded_term(case_id: str, query: dict, case: dict, call: int) -> dict:
    evidence = cosine_evidence(query, case)
    return {
        "case_id": case_id,
        "call": call,
        "call_scope": "positive_condition_presentation"
        if call == 1
        else "normal_for_this_condition_only",
        "terms": {
            key: evidence[key] for key in ("dot", "left_norm_sq", "right_norm_sq")
        },
        "common_speaking_banks": evidence["common_banks"],
        "squared_cosine": {
            "numerator": str(evidence["dot"] ** 2),
            "denominator": str(evidence["left_norm_sq"] * evidence["right_norm_sq"]),
        },
        "reaches_trust": False,
        "trust": None,
    }


# --------------------------------------------------------------------------
# Bank names


def test_parse_bank_reads_v1_and_v2_names_and_refuses_others() -> None:
    fields = parse_bank(bank("signal_median", "patient_lps_anterior", "2"))
    assert fields == {
        "version": "v1",
        "view": ("Coronal", "0", "0"),
        "role": None,
        "metric": "signal_median",
        "direction": "patient_lps_anterior",
        "scale_mm": 2.0,
    }
    v2 = territory_bank_name(
        {"orientation": "Axial", "fluid_sensitive": "1", "fat_suppression": "1"},
        "context",
        "local_range",
        "overview",
        10.0,
    )
    fields_v2 = parse_bank(v2)
    assert fields_v2 is not None
    assert fields_v2["role"] == "context"
    assert fields_v2["view"] == ("Axial", "1", "1")
    for bad in ("", "squint/v1/view=[1]/metric=a/direction=b/scale=10mm", None, 3):
        assert parse_bank(bad) is None
    words = bank_words(bank("gradient_row", "row", "2"))
    assert "Coronal, not fluid-sensitive, fat not suppressed" in words
    assert "all its places" in words
    assert "coded with the 10 mm thirds" in words


def _v2_bank(role: str, metric: str = "signal_median", scale: float = 10.0) -> str:
    return territory_bank_name(fixtures.VIEW, role, metric, "overview", scale)


def test_compared_roles_are_read_from_the_bank_names_alone() -> None:
    names = [_v2_bank("object"), _v2_bank("context"), _v2_bank("object", "local_range")]
    assert compared_roles(names) == ["context", "object"]
    # Must change with the names: a comparison that read no context bank names no context.
    assert compared_roles([names[0], names[2]]) == ["object"]
    # A v1 bank carries no territory role, and reading it names none.
    assert compared_roles([bank("signal_median", "overview")]) == []
    assert compared_roles([]) == []
    # A role is read in the view whose banks were read, not in every view.
    axial = {"orientation": "Axial", "fluid_sensitive": "1", "fat_suppression": "1"}
    in_two_views = [
        _v2_bank("object"),
        territory_bank_name(axial, "context", "signal_median", "overview", 10.0),
    ]
    assert compared_roles(in_two_views) == ["context", "object"]
    assert compared_roles(in_two_views, ("Coronal", "1", "1")) == ["object"]
    assert compared_roles(in_two_views, ("Axial", "1", "1")) == ["context"]
    assert compared_roles(in_two_views, ("Sagittal", "1", "1")) == []
    # The words say which places a v2 bank was read over; a v1 bank has no role to say.
    assert bank_words(_v2_bank("context")).endswith("10 mm tiles / context places")
    assert bank_words(bank("signal_median", "overview")).endswith("10 mm tiles")


def test_row_words_follow_the_coding_reference_of_the_banks_own_profile() -> None:
    v1_rows = row_words(bank("signal_median", "overview"))
    v2_rows = row_words(_v2_bank("object"))
    assert v1_rows[1] == "within the series' middle third"
    assert v2_rows[1] == "within the leg's middle third"
    assert v1_rows != v2_rows
    # A name that parses as neither keeps the series words: nothing is claimed of the leg.
    assert row_words("not a bank name") == v1_rows


# --------------------------------------------------------------------------
# The exact decode


def test_bank_difference_is_exact_and_silence_is_not_a_middle() -> None:
    assert bank_difference([0, 0, 0], [1, 2, 3]) is None
    assert bank_difference(None, [1, 2, 3]) is None
    difference = bank_difference([3, 1, 0], [0, 1, 3])
    assert difference is not None
    assert difference["share_difference"] == [
        Fraction(3, 4),
        Fraction(0),
        Fraction(-3, 4),
    ]
    assert difference["apart"] == Fraction(3, 4)
    assert difference["row"] == 0
    # Same proportions, different sizes: nothing apart.
    same_shares = bank_difference([1, 2, 3], [2, 4, 6])
    assert same_shares is not None
    assert same_shares["apart"] == 0


def test_named_differences_read_only_the_compared_banks() -> None:
    read = bank("signal_median", "overview")
    unread = bank("signal_minimum", "overview")
    query = {read: [6, 0, 0], unread: [0, 0, 6]}
    normal = {read: [0, 0, 6], unread: [6, 0, 0]}
    first = named_differences(
        query, normal, [read], left_label="query", right_label="normal", limit=3
    )
    assert [item["bank"] for item in first] == [read]
    assert first[0]["statement"].endswith("normal 0 of 6 (0%)")
    assert (
        "query 6 of 6 places below the series' middle third (100%)"
        in (first[0]["statement"])
    )
    # Must not change: a bank the comparison did not read.
    changed_unread = {**normal, unread: [0, 6, 0]}
    assert (
        named_differences(
            query,
            changed_unread,
            [read],
            left_label="query",
            right_label="normal",
            limit=3,
        )
        == first
    )
    # Must change: a bank it did read.
    changed_read = {**normal, read: [6, 0, 0]}
    changed = named_differences(
        query, changed_read, [read], left_label="query", right_label="normal", limit=3
    )
    assert changed != first
    assert changed[0]["apart"] == [0, 1]


def test_named_differences_order_by_most_different_then_name() -> None:
    a = bank("signal_median", "overview")
    b = bank("signal_maximum", "overview")
    c = bank("local_range", "overview")
    left = {a: [2, 0, 0], b: [1, 1, 0], c: [1, 1, 0]}
    right = {a: [0, 0, 2], b: [1, 0, 1], c: [1, 0, 1]}
    items = named_differences(
        left, right, [c, b, a], left_label="query", right_label="p", limit=3
    )
    assert items[0]["bank"] == a
    assert [item["bank"] for item in items[1:]] == sorted([b, c])


# --------------------------------------------------------------------------
# The query profile recall used


def _profiles() -> tuple[dict, dict]:
    base = {
        bank("signal_median", "overview"): [4, 3, 2],
        bank("signal_minimum", "overview"): [5, 2, 2],
        bank("signal_median", "overview", "2"): [40, 30, 22],
        bank("signal_minimum", "overview", "2"): [50, 20, 22],
    }
    case = profile(
        {
            bank("signal_median", "overview"): [1, 1, 2],
            bank("signal_minimum", "overview"): [3, 1, 0],
            bank("signal_median", "overview", "2"): [10, 12, 30],
            bank("signal_minimum", "overview", "2"): [33, 11, 8],
        }
    )
    return base, case


def test_recalled_profile_is_the_one_that_reproduces_the_record() -> None:
    base, case = _profiles()
    final = profile(base)
    term = recorded_term("squint-case:s:mm", final, case, 1)
    found = recalled_query_profile(final, [term], {"squint-case:s:mm": case})
    assert found["code"] == "final"
    assert found["checked_terms"] == 1

    coarse_only = profile({k: v for k, v in base.items() if k.endswith("10mm")})
    term = recorded_term("squint-case:s:mm", coarse_only, case, 1)
    found = recalled_query_profile(final, [term], {"squint-case:s:mm": case})
    assert found["code"] == "before_first_fine_reading"
    assert set(found["profile"]["banks"]) == set(coarse_only["banks"])

    doubled = profile(
        {k: [2 * x for x in v] if k.endswith("2mm") else v for k, v in base.items()}
    )
    term = recorded_term("squint-case:s:mm", final, case, -1)
    found = recalled_query_profile(doubled, [term], {"squint-case:s:mm": case})
    assert found["code"] == "before_repeated_fine_reading"
    assert found["profile"]["banks"] == final["banks"]


def test_unreproducible_profile_is_named_unverified_and_unrelated_changes_do_not_matter() -> (
    None
):
    base, case = _profiles()
    final = profile(base)
    term = recorded_term("squint-case:s:mm", final, case, 1)
    # Must change: one count recall did not see.
    perturbed = profile({**base, bank("signal_median", "overview", "2"): [41, 30, 22]})
    found = recalled_query_profile(perturbed, [term], {"squint-case:s:mm": case})
    assert found["code"] == "recalled_profile_not_reconstructed"
    assert found["profile"]["banks"] == perturbed["banks"]
    # Must not change: a silent bank in the case, or the case's teaching calls.
    quiet = profile({**case["banks"], bank("local_range", "overview"): [0, 0, 0]})
    quiet["condition_calls"] = {"Medial Meniscus": -1}
    found = recalled_query_profile(final, [term], {"squint-case:s:mm": quiet})
    assert found["code"] == "final"
    assert recalled_query_profile(None, [term], {})["code"] == "query_profile_missing"
    assert recalled_query_profile(final, [], {})["code"] == "no_recorded_terms"


def test_a_term_is_reproduced_over_the_banks_the_question_selected() -> None:
    read = bank("signal_median", "overview")
    other = bank("signal_minimum", "overview")
    query = profile({read: [4, 3, 2], other: [5, 2, 2]})
    case = profile({read: [1, 1, 2], other: [3, 1, 0]})
    # Recall was told to read one bank, so its term holds that bank alone.
    only_read = recorded_term(
        "squint-case:s:mm",
        profile({read: query["banks"][read]}),
        profile({read: case["banks"][read]}),
        1,
    )
    assert only_read["common_speaking_banks"] == [read]
    args = (query["banks"], case["banks"], only_read)
    assert term_reproduction(*args, [read])["code"] == "reproduced"
    # Must change: had the selection offered the other bank, both profiles speak in
    # it and the term should have read it; so a different selection is named.
    assert term_reproduction(*args, [read, other])["code"] == "banks_differ"
    # With no selection recorded every bank both speak in was offered.
    assert term_reproduction(*args, None)["code"] == "banks_differ"
    # Must not change: a bank only the query speaks in is no common bank; silence
    # adds nothing, whether or not it was offered.
    quiet_case = {read: case["banks"][read]}
    assert term_reproduction(query["banks"], quiet_case, only_read, None)["code"] == (
        "reproduced"
    )
    # Must change: a count moved in the selected bank is named as the side it moved on.
    moved_case = {**case["banks"], read: [2, 1, 2]}
    case_side = term_reproduction(query["banks"], moved_case, only_read, [read])
    assert case_side["code"] == "case_counts_differ"
    moved_query = {**query["banks"], read: [4, 3, 3]}
    query_side = term_reproduction(moved_query, case["banks"], only_read, [read])
    assert query_side["code"] == "query_counts_differ"
    # The memory side is checked apart from the query: with no query known (an
    # unverified one is passed as no banks) the memory still matches the record ...
    assert term_reproduction({}, case["banks"], only_read, [read])["case"] is True
    # ... unless its own counts differ, which is then named as the memory's.
    assert term_reproduction({}, moved_case, only_read, [read])["case"] is False
    # A query that lacks a recorded bank is named as the query, not as the memory.
    lacking = {name: counts for name, counts in query["banks"].items() if name != read}
    absent = term_reproduction(lacking, case["banks"], only_read, [read])
    assert (absent["case"], absent["query"], absent["dot"]) == (True, False, False)
    # A term that is not shaped like a recorded term is not reproduced from anything.
    malformed = term_reproduction(query["banks"], case["banks"], {}, None)
    assert malformed["code"] == "term_malformed"


# --------------------------------------------------------------------------
# A territory-v2 record whose fine banks were added after a question was asked


def _native_places(territory: dict, places: list[tuple[int, int]]) -> dict:
    """The native fixture's territory with its object tiles moved to ``places``."""
    moved = _territory_with_object_tiles(places)
    own = {key: territory[key] for key in ("study_uid", "series_uid", "tile_window")}
    return {**moved, **own}


def _read_coarse_then_fine(tmp_path) -> dict:
    """One object read coarse, then finer, then finer over another region, by the
    production writer, and two memory cases read both ways on the same series.

    ``coarse`` is the profile a question saw before any fine reading existed;
    ``final`` is the same address with its fine reading merged in; ``later`` also
    carries a finer region that no coarse reading covered.
    """
    series, leg, territory = _native_fixture(tmp_path)
    subject = "medial_meniscus"

    def coarse_of(area: dict) -> dict:
        return writer.profile_territory(series, area, leg, subject=subject)

    def fine_of(area: dict) -> dict:
        return writer.refine_territory(series, area, leg, subject=subject)

    def merged(*parts: dict) -> dict:
        return writer.merge_profiles(parts, subject=subject)

    coarse, fine = coarse_of(territory), fine_of(territory)
    elsewhere = _native_places(territory, [(4, 1), (4, 2)])
    areas = ([(2, 2), (2, 3), (3, 2)], [(3, 3), (3, 4), (4, 3)])
    return {
        "coarse": coarse,
        "final": merged(coarse, fine),
        "later": merged(coarse, fine, fine_of(elsewhere)),
        "cases": [
            merged(coarse_of(area), fine_of(area))
            for area in (_native_places(territory, places) for places in areas)
        ],
    }


def _fine_banks(banks) -> set[str]:
    return {name for name in banks if parse_bank(name)["scale_mm"] == 2.0}


def test_a_v2_profile_given_fine_banks_later_is_recalled_from_its_coarse_banks(
    tmp_path,
) -> None:
    parts = _read_coarse_then_fine(tmp_path)
    coarse, final, case = parts["coarse"], parts["final"], parts["cases"][0]
    memory = {"squint-case:s:mm": case}
    fine = _fine_banks(final["banks"])
    assert fine and not fine & set(coarse["banks"])

    # Sign one: the question was asked before the fine reading. Its term holds
    # coarse banks only, so the final profile (which now offers fine banks the
    # case also writes) does not reproduce it, and the profile as it stood before
    # its first fine reading does, with every fine bank left unwritten, not zero.
    early = recorded_term("squint-case:s:mm", coarse, case, 1)
    assert early["common_speaking_banks"]
    assert not fine & set(early["common_speaking_banks"])
    found = recalled_query_profile(final, [early], memory)
    assert found["code"] == "before_first_fine_reading"
    assert found["profile"]["banks"] == coarse["banks"]
    assert not fine & set(found["profile"]["banks"])
    assert found["also_reproduced_by"] == []
    # The recorded selection is still honoured: production's names both scales, and
    # the projection is held to it exactly as the final profile is.
    selected = sorted(set(final["banks"]) | set(case["banks"]))
    found = recalled_query_profile(final, [early], memory, selected_banks=selected)
    assert found["code"] == "before_first_fine_reading"
    # The places it was counted over are the coarse reading's, and no fine reading.
    (before,) = profile_territories(found["profile"])
    (after,) = profile_territories(final)
    assert (before["fine_readings"], after["fine_readings"]) == (0, 1)
    assert before["recorded_native_bounds_rc"] == after["recorded_native_bounds_rc"]
    assert before["territory"] == after["territory"]

    # Sign two: a later question compared fine banks of the same address. Its term
    # names them, so only the final profile reproduces it and it stays the final.
    late = recorded_term("squint-case:s:mm", final, case, 1)
    assert fine & set(late["common_speaking_banks"])
    found = recalled_query_profile(final, [late], memory)
    assert found["code"] == "final"
    assert found["profile"]["banks"] == final["banks"]
    assert found["also_reproduced_by"] == []
    (shown,) = profile_territories(found["profile"])
    assert shown["fine_readings"] == 1

    # Must not change: a profile that never had a fine reading has nothing to leave
    # out, so it is not also reproduced by an identical copy of itself.
    found = recalled_query_profile(coarse, [early], memory)
    assert found["code"] == "final"
    assert found["also_reproduced_by"] == []


def test_the_profile_before_a_fine_reading_leaves_out_only_what_it_added(
    tmp_path,
) -> None:
    parts = _read_coarse_then_fine(tmp_path)
    coarse, final = parts["coarse"], parts["final"]
    record = copy.deepcopy(final)

    # Sign one: the fine banks and the fine reading are left out; the coarse banks
    # and the coarse reading's source stay exactly as written.
    before = profile_before_fine_reading(final, 2.0)
    assert before is not None
    assert before["banks"] == coarse["banks"]
    assert before["source"]["lineage"] == [coarse["source"]]
    assert final == record  # the record is read, never changed
    # Sign two: a profile with nothing fine in it has nothing to leave out, so it
    # is no candidate of its own; one that wrote no fine bank but holds a fine
    # reading in its lineage still leaves that reading out.
    assert profile_before_fine_reading(coarse, 2.0) is None
    silent = profile_before_fine_reading({**coarse, "source": final["source"]}, 2.0)
    assert silent is not None
    assert silent["banks"] == coarse["banks"]
    assert silent["source"]["lineage"] == [coarse["source"]]


def test_a_v2_profile_that_does_not_reproduce_the_record_stays_unverified(
    tmp_path,
) -> None:
    parts = _read_coarse_then_fine(tmp_path)
    coarse, final, case = parts["coarse"], parts["final"], parts["cases"][0]
    memory = {"squint-case:s:mm": case}
    fine = _fine_banks(final["banks"])
    early = recorded_term("squint-case:s:mm", coarse, case, 1)
    late = recorded_term("squint-case:s:mm", final, case, 1)
    read = early["common_speaking_banks"][0]
    unverified = "recalled_profile_not_reconstructed"
    assert recalled_query_profile(final, [early], memory)["code"] != unverified

    def counts_moved(profile: dict, name: str, by: int) -> dict:
        first, *rest = profile["banks"][name]
        return {**profile, "banks": {**profile["banks"], name: [first + by, *rest]}}

    # Must change: a coarse count the term read, moved, is not a profile it came
    # from; the final profile as recorded is then the one named as unreproduced.
    moved = counts_moved(final, read, 1)
    found = recalled_query_profile(moved, [early], memory)
    assert found["code"] == unverified
    assert found["profile"]["banks"] == moved["banks"]
    assert found["memory_case_differs"] == []
    # Must change: a bank the term read, missing from the record (silence is not a
    # count, so it is not made up).
    gone = {n: c for n, c in final["banks"].items() if n != read}
    found = recalled_query_profile({**final, "banks": gone}, [early], memory)
    assert found["code"] == unverified
    # Must change: the memory's counts differ from the record, and it is named so.
    changed = counts_moved(case, read, 1)
    found = recalled_query_profile(final, [early], {"squint-case:s:mm": changed})
    assert found["code"] == unverified
    assert found["memory_case_differs"] == ["squint-case:s:mm"]
    # Must change: a recorded selection that did not offer a bank the term read.
    narrower = [name for name in early["common_speaking_banks"] if name != read]
    found = recalled_query_profile(final, [early], memory, selected_banks=narrower)
    assert found["code"] == unverified
    # Must not change: a fine count the coarse term never read.
    unread = counts_moved(final, min(fine), 1)
    found = recalled_query_profile(unread, [early], memory)
    assert found["code"] == "before_first_fine_reading"
    # Must change: fine counts doubled against a term that read them. A v1 record
    # can be halved back (an old repair for a repeated fine reading); a v2 record
    # is not, and the profile before its fine reading lacks the banks the term read.
    doubled = {
        **final,
        "banks": {
            name: [2 * value for value in counts] if name in fine else counts
            for name, counts in final["banks"].items()
        },
    }
    assert recalled_query_profile(final, [late], memory)["code"] == "final"
    found = recalled_query_profile(doubled, [late], memory)
    assert found["code"] == unverified
    assert found["also_reproduced_by"] == []


def test_a_coarse_comparison_is_drawn_over_its_coarse_places_not_a_later_finer_region(
    tmp_path,
) -> None:
    parts = _read_coarse_then_fine(tmp_path)
    coarse, later = parts["coarse"], parts["later"]
    normal, shown = parts["cases"]

    def defining(asked: dict) -> dict:
        """The plan for a record finished as ``later`` whose terms came from ``asked``."""
        memory, record = _memory_and_record((asked, normal, shown))
        record["objects"]["medial_meniscus"]["profile"] = later
        cases = {case["case_id"]: case for case in memory["cases"]}
        return question_plan(record, "Medial Meniscus", memory, cases)["defining"][0]

    # The finished record holds a fine reading of the same address and of another
    # region; the final profile was counted over both.
    assert sorted(p["fine_readings"] for p in reading_panels(later, [])) == [1, 1]
    # Sign one: the question compared coarse banks only, so what is drawn as
    # compared is the coarse reading's one place, with no fine reading and with
    # the fine banks unwritten. The precedents' memory counts match the record.
    early = defining(coarse)
    assert early["query"]["code"] == "before_first_fine_reading"
    assert early["query"]["verified"] is True
    assert early["query"]["withheld_bank_count"] == 0
    assert set(early["query"]["banks"]) == set(coarse["banks"])
    assert [p["fine_readings"] for p in early["panels"]] == [0]
    assert [p["window"] for p in early["panels"]] == [(0, 1, 3, 5, 3, 5)]
    assert early["normal"]["code"] == early["presentation"]["code"] == "drawn"
    # Sign two: a question that compared the fine banks is drawn over every place
    # the final profile was counted over, the finer region too.
    final = defining(later)
    assert final["query"]["code"] == "final"
    assert set(final["query"]["banks"]) == set(later["banks"])
    assert final["panel_scope"] == {
        "source": "recalled_profile_lineage",
        "fine_readings_in_final_not_compared": 0,
    }
    assert sorted(p["fine_readings"] for p in final["panels"]) == [1, 1]
    assert sorted(p["window"] for p in final["panels"]) == [
        (0, 1, 3, 5, 3, 5),
        (0, 1, 4, 5, 1, 3),
    ]


def test_ambiguous_coarse_terms_do_not_show_later_fine_readings_as_compared(
    tmp_path,
) -> None:
    parts = _read_coarse_then_fine(tmp_path)
    coarse, final = parts["coarse"], parts["later"]
    # Neither precedent ever wrote a fine bank. Both the final query and its
    # projection therefore reproduce the same exact coarse terms.
    memory, record = _memory_and_record((final, coarse, coarse))
    cases = {case["case_id"]: case for case in memory["cases"]}

    plan = question_plan(record, "Medial Meniscus", memory, cases)
    subject = plan["defining"][0]

    assert subject["query"]["code"] == "final"
    assert subject["query"]["also_reproduced_by"] == ["before_first_fine_reading"]
    assert subject["query"]["banks"] == final["banks"]
    assert subject["compared_banks"]
    assert not _fine_banks({name: [] for name in subject["compared_banks"]})
    assert [panel["fine_readings"] for panel in subject["panels"]] == [0]
    assert [panel["window"] for panel in subject["panels"]] == [(0, 1, 3, 5, 3, 5)]
    assert subject["panel_scope"] == {
        "source": "coarse_lineage_for_coarse_only_comparison",
        "fine_readings_in_final_not_compared": 2,
    }
    assert _plan_summary(plan)["defining"][0]["panel_scope"] == subject["panel_scope"]
    assert any(
        "2 fine readings held in the final profile were not compared" in line
        for line in _subject_lines(plan, subject, 20.0)
    )


def test_unverified_query_names_address_only_panel_scope(tmp_path) -> None:
    parts = _read_coarse_then_fine(tmp_path)
    memory, record = _memory_and_record(
        (parts["later"], parts["cases"][0], parts["cases"][1])
    )
    voice = record["questions"]["Medial Meniscus"]["objects"]["medial_meniscus"]
    read_bank = voice["case_terms"][0]["common_speaking_banks"][0]
    first, *rest = record["objects"]["medial_meniscus"]["profile"]["banks"][read_bank]
    record["objects"]["medial_meniscus"]["profile"]["banks"][read_bank] = [
        first + 1,
        *rest,
    ]
    cases = {case["case_id"]: case for case in memory["cases"]}

    subject = question_plan(record, "Medial Meniscus", memory, cases)["defining"][0]

    assert subject["query"]["verified"] is False
    assert subject["panels"][0]["counted_by"] == "located_address_only"
    assert subject["panel_scope"]["source"] == "located_address_only_unverified"


# --------------------------------------------------------------------------
# A box is an address; the object's places are drawn separately


def test_same_box_different_support_gives_different_object_places() -> None:
    series = fixtures.series_record()
    territory = fixtures.teacher_territory()
    window = territory["tile_window"]
    native = window_native_bounds(series["stack"].bounds_rc, window)
    assert native == (0, 120, 0, 120)
    # Two supports inside the same box: one full object tile, one sparse speck.
    full = np.zeros((1, 40, 40), dtype=bool)
    full[0, :20, :20] = True
    speck = np.zeros((1, 40, 40), dtype=bool)
    speck[0, 5:7, 5:7] = True
    counts = []
    for mask in (full, speck):
        support = {
            **territory,
            "native_support": {"mask": mask, "slices": [1], "offset_rc": [60, 60]},
        }
        counts.append(support_in_window(mask, (60, 60), native))
        summary = territory_summary(support)
        assert summary["object_tiles"] == 4
        assert summary["outside_leg_tiles"] == 11
        assert summary["support_px"] == int(mask.sum())
    # The address is identical; what the object occupies is not.
    assert counts == [400, 4]
    # A box-only stand-in cannot tell them apart.
    box_px = (native[1] - native[0]) * (native[3] - native[2])
    assert box_px == 14400
    assert counts[0] / box_px != counts[1] / box_px
    assert int(np.count_nonzero(territory["roles"] == ROLE_OBJECT)) == 4


def test_inset_goes_to_the_corner_farthest_from_the_window() -> None:
    upper_left_window = inset_corner(0.1, 0.1)
    assert upper_left_window[0] > 0.5 and upper_left_window[1] < 0.5
    lower_right_window = inset_corner(0.9, 0.9)
    assert lower_right_window[0] < 0.5 and lower_right_window[1] > 0.5


# --------------------------------------------------------------------------
# What a territory-v2 profile was counted over (written by the production writer)


def _territory_profile(territory: dict | None = None) -> tuple[dict, dict]:
    """A territory-v2 profile from the production writer, and the leg map it used."""
    leg = fixtures.expected_leg_map()
    written = writer.profile_territory(
        fixtures.series_record(),
        territory or fixtures.teacher_territory(),
        leg,
        subject="medial_meniscus",
    )
    return written, leg


def _territory_with_object_tiles(places: list[tuple[int, int]]) -> dict:
    """The fixture territory with its object tiles moved to ``places`` (row, column)."""
    territory = fixtures.teacher_territory()
    territory["roles"][territory["roles"] == ROLE_OBJECT] = shapes.ROLE_CONTEXT
    territory["object_share"][:] = np.nan
    for row, column in places:
        territory["roles"][0, row, column] = ROLE_OBJECT
        territory["object_share"][0, row, column] = 0.5
    return territory


def test_object_box_is_the_box_around_the_object_tiles_not_the_window() -> None:
    territory = fixtures.teacher_territory()
    # The window addresses 36 tiles; the object tiles are 4 of them.
    assert territory["tile_window"] == [1, 2, 0, 6, 0, 6]
    window = territory["tile_window"]
    assert object_box(territory["roles"], window) == (1, 2, 3, 5, 3, 5)
    # Must change: the box follows the object tiles while the window stays put.
    roles = territory["roles"].copy()
    roles[roles == ROLE_OBJECT] = shapes.ROLE_CONTEXT
    roles[0, 1, 2] = ROLE_OBJECT
    assert object_box(roles, window) == (1, 2, 1, 2, 2, 3)
    # A territory with no object tile has no box: a context ring is not an object.
    roles[roles == ROLE_OBJECT] = shapes.ROLE_CONTEXT
    assert object_box(roles, window) is None


def test_profile_territories_lists_each_territory_once_through_a_merge() -> None:
    written, leg = _territory_profile()
    (entry,) = profile_territories(written)
    assert entry["territory"]["tile_window"] == [1, 2, 0, 6, 0, 6]
    assert entry["view"] == fixtures.VIEW
    # What the coarse reading recorded of the grid and the leg map it was written
    # with: the production writer's own record, not recomputed here.
    assert entry["recorded_native_bounds_rc"] == [0, 120, 0, 120]
    assert entry["leg_map_sha256"] == written["source"]["leg_map"]["codes_sha256"]
    assert entry["leg_map_sha256"] == leg_codes_digest(leg)
    assert entry["fine_readings"] == 0
    # A merge keeps each reading's source beneath it: two territories, in address order.
    later = fixtures.teacher_territory()
    later["tile_window"] = [2, 3, 0, 6, 0, 6]
    second, _ = _territory_profile(later)
    merged = writer.merge_profiles([second, written], subject="medial_meniscus")
    windows = [e["territory"]["tile_window"] for e in profile_territories(merged)]
    assert windows == [[1, 2, 0, 6, 0, 6], [2, 3, 0, 6, 0, 6]]
    # Must not change: one territory twice in a lineage is still one territory.
    twice = writer.merge_profiles([written, written], subject="medial_meniscus")
    assert len(profile_territories(twice)) == 1
    # A finer reading over the same territory is counted and does not replace the
    # native bounds the coarse reading recorded (refine_territory writes
    # ``refinement`` and its fine grid as the source ``window``).
    fine = {
        **copy.deepcopy(written["source"]),
        "refinement": True,
        "window": [0, 1, 0, 30, 0, 30],
        "native_bounds_rc": [0, 118, 0, 118],
    }
    with_fine = {"banks": {}, "source": {"lineage": [fine, written["source"]]}}
    (entry,) = profile_territories(with_fine)
    assert entry["fine_readings"] == 1
    assert entry["recorded_native_bounds_rc"] == [0, 120, 0, 120]
    # A v1 profile counted a tile box and has no territory; nor has a non-profile.
    box_only = profile({bank("signal_median", "overview"): [1, 1, 1]})
    assert profile_territories(box_only) == []
    assert profile_territories(None) == []


def test_reading_panels_are_the_profiles_own_territories_or_else_the_tile_box() -> None:
    written, leg = _territory_profile()
    regions = [
        {
            "series_uid": fixtures.SERIES_UID,
            "view": dict(fixtures.VIEW),
            "window": [1, 2, 3, 5, 3, 5],
            "anchors": [
                {"kind": "anchor_point", "label": "femur", "point_lps": [1.0, 2.0, 3.0]}
            ],
        },
        {
            "series_uid": "another-series",
            "view": dict(fixtures.VIEW),
            "window": [0, 1, 0, 2, 0, 2],
        },
    ]
    # The profile was counted over one territory; a located region it was not
    # counted over (another series) is not a panel.
    (panel,) = reading_panels(written, regions)
    assert panel["counted_by"] == "territory"
    assert panel["origin"] == "teacher_support"
    assert panel["territory_code"] == "valid"
    assert panel["window"] == (1, 2, 3, 5, 3, 5)
    assert panel["territory"]["tile_window"] == [1, 2, 0, 6, 0, 6]
    assert panel["region"] is regions[0]
    assert panel["anchors"] == regions[0]["anchors"]
    assert panel["recorded_native_bounds_rc"] == [0, 120, 0, 120]
    assert panel["leg_map_sha256"] == leg_codes_digest(leg)
    # Must change: a territory record that cannot be validated is named, not drawn from.
    broken = copy.deepcopy(written)
    broken["source"]["territory"]["roles"][0][0][0] = 9
    (refused,) = reading_panels(broken, regions)
    assert refused["territory"] is None
    assert refused["territory_code"] == "territory_role_unknown"
    assert refused["window"] is None
    # A v1 profile counted the tile box of each located region: a panel apiece, as a box.
    v1_panels = reading_panels(
        profile({bank("signal_median", "overview"): [1, 1, 1]}), regions
    )
    assert [p["counted_by"] for p in v1_panels] == ["tile_box", "tile_box"]
    assert all(p["territory"] is None for p in v1_panels)
    # With no reproduced profile only the located addresses remain, claiming nothing
    # was counted over them.
    addresses = region_panels(regions, "located_address_only")
    assert [p["counted_by"] for p in addresses] == ["located_address_only"] * 2
    assert [p["window"] for p in addresses] == [(1, 2, 3, 5, 3, 5), (0, 1, 0, 2, 0, 2)]


def test_grid_pin_names_a_tile_grid_other_than_the_one_the_profile_was_written_on() -> (
    None
):
    bounds = np.asarray(fixtures.series_record()["stack"].bounds_rc)
    territory = fixtures.teacher_territory()
    panel = {"territory": territory, "recorded_native_bounds_rc": [0, 120, 0, 120]}
    assert grid_pin(panel, bounds) == "matches"
    # Must change: the same window on a coarser grid is other pixels...
    assert grid_pin(panel, bounds * 2) == "differs"
    # ... and on a grid the window does not reach there are no pixels at all.
    far = {**territory, "tile_window": [1, 2, 20, 22, 0, 6]}
    assert grid_pin({**panel, "territory": far}, bounds) == "differs"
    # Must not claim what was not recorded.
    unrecorded = {**panel, "recorded_native_bounds_rc": None}
    assert grid_pin(unrecorded, bounds) == "not_recorded"
    assert grid_pin({**panel, "territory": None}, bounds) == "not_recorded"


def test_leg_map_pin_hatches_only_from_the_leg_map_the_profile_was_written_with() -> (
    None
):
    written, leg = _territory_profile()
    digest = leg_codes_digest(leg)
    assert digest == written["source"]["leg_map"]["codes_sha256"]
    image = {"leg_codes": leg["codes"][1], "leg_codes_sha256": digest}
    panel = {"leg_map_sha256": digest}
    assert leg_map_pin(panel, image) == "profile_leg_map"
    # Must change: a leg map that differs by one tile has another digest, is named
    # as differing, and is not drawn.
    other = leg["codes"].copy()
    other[1, 4, 4] = shapes.LEG_OUTSIDE
    other_digest = leg_codes_digest({"codes": other})
    assert other_digest != digest
    differing = {"leg_codes": other[1], "leg_codes_sha256": other_digest}
    assert leg_map_pin(panel, differing) == "differs_from_profile"
    # A v1 profile used no leg map: the prior may be drawn, as inspection only.
    assert leg_map_pin({"leg_map_sha256": None}, image) == "inspection_only"
    # No leg codes read: nothing to draw, whatever the profile pinned.
    assert leg_map_pin(panel, {"leg_codes": None}) == "unavailable"
    assert leg_codes_digest(None) is None
    assert leg_codes_digest({"codes": [[1]]}) is None


class _Patches:
    """Stands in for the axes: only what is added to it is looked at."""

    def __init__(self) -> None:
        self.added: list = []

    def add_patch(self, patch) -> None:
        self.added.append(patch)


def test_draw_roles_tells_nothing_known_from_nothing_read() -> None:
    territory = fixtures.teacher_territory()
    bounds = np.asarray(fixtures.series_record()["stack"].bounds_rc)

    def drawn_as_read(compared) -> int:
        axes = _Patches()
        draw_roles(
            axes, territory["roles"][0], territory["tile_window"], bounds, compared
        )
        # A tile of a role a comparison read has the heavier outline.
        return sum(1 for patch in axes.added if patch.get_linewidth() == 0.8)

    # The window holds 4 object tiles, 21 context tiles and 11 outside the leg.
    assert drawn_as_read(["object", "context"]) == 25
    # Must change with the roles read: each role alone, and none.
    assert drawn_as_read(["object"]) == 4
    assert drawn_as_read(["context"]) == 21
    assert drawn_as_read([]) == 0
    # Nothing known of what was read (a support re-resolved for inspection) is not
    # "none": it draws every role as read, so that it is not mistaken for a result.
    assert drawn_as_read(None) == 25


# --------------------------------------------------------------------------
# Plans from records


def _region(series_uid: str, window: list[int], **extra) -> dict:
    return {
        "series_uid": series_uid,
        "view": {
            "orientation": "Coronal",
            "fluid_sensitive": "0",
            "fat_suppression": "0",
        },
        "window": window,
        **extra,
    }


def test_window_anchors_read_the_matching_window_source_only() -> None:
    region = _region("S1", [3, 4, 2, 4, 1, 5])
    record = {
        "evidence": {
            "proposal_sources": [
                {
                    "series_uid": "S1",
                    "provenance": {
                        "hypotheses": [
                            {
                                "anchor": "femur",
                                "kind": "current_anchor_relative_prior",
                                "anchor_point_lps": [1.0, 2.0, 3.0],
                            },
                            {
                                "anchor": "tibia",
                                "kind": "current_anchor_relative_prior",
                                "anchor_point_lps": [4.0, 5.0, 6.0],
                            },
                        ],
                        "window_sources": [
                            {
                                "window": [3, 4, 2, 4, 1, 5],
                                "sources": [
                                    {
                                        "hypothesis_index": 0,
                                        "predicted_point_lps": [7.0, 8.0, 9.0],
                                    }
                                ],
                            },
                            {
                                "window": [9, 10, 2, 4, 1, 5],
                                "sources": [
                                    {
                                        "hypothesis_index": 1,
                                        "predicted_point_lps": [0.0, 0.0, 0.0],
                                    }
                                ],
                            },
                        ],
                    },
                },
                {
                    "series_uid": "S2",
                    "provenance": {"hypotheses": [], "window_sources": []},
                },
            ]
        }
    }
    anchors = window_anchors(record, region)
    assert [(a["kind"], a["point_lps"]) for a in anchors] == [
        ("anchor_point", [1.0, 2.0, 3.0]),
        ("predicted_point", [7.0, 8.0, 9.0]),
    ]
    own = window_anchors({}, {**region, "source_point_lps": [1.5, 2.5, 3.5]})
    assert own == [
        {
            "kind": "object_reference_point",
            "label": "its own reference point",
            "point_lps": [1.5, 2.5, 3.5],
        }
    ]
    assert region_window({"source_window": [1, 2, 0, 1, 0, 1]}) == (1, 2, 0, 1, 0, 1)
    assert region_window({"window": [2, 2, 0, 1, 0, 1]}) is None


def _memory_and_record(profiles: tuple[dict, dict, dict] | None = None):
    """A one-question memory and record; ``profiles`` is (query, normal, presentation)."""
    if profiles is None:
        base, _ = _profiles()
        final = profile(base)
        normal = profile(
            {
                bank("signal_median", "overview"): [3, 0, 0],
                bank("signal_minimum", "overview"): [2, 1, 0],
            }
        )
        shown = profile({bank("signal_median", "overview"): [0, 0, 3]})
    else:
        final, normal, shown = profiles
    cases = [
        {
            "case_id": "squint-case:N:medial_meniscus",
            "study_uid": "N",
            "subject": "medial_meniscus",
            "condition_calls": {"Medial Meniscus": -1},
            "profile": normal,
            "regions": [
                _region(
                    "NS",
                    [1, 2, 3, 5, 3, 5],
                    source_window=[1, 2, 3, 5, 3, 5],
                    extent_source="retained_object_support",
                    source_point_lps=[0.0, 0.0, 0.0],
                )
            ],
            "full_profile": {
                "availability": "retained_sparse_counts",
                "payload_ref": "full-payload:x",
                "context_ref": "full-context:x",
            },
        },
        {
            "case_id": "squint-case:P:medial_meniscus",
            "study_uid": "P",
            "subject": "medial_meniscus",
            "condition_calls": {"Medial Meniscus": 1},
            "profile": shown,
            "regions": [
                _region(
                    "PS", [0, 1, 0, 2, 0, 2], extent_source="retained_physical_location"
                )
            ],
        },
    ]
    memory = {
        "cases": cases,
        "label_ledger": {"Q": {"Medial Meniscus": 0}},
        "full_profile_payloads": {
            "payloads": {
                "full-payload:x": {
                    "record": {
                        "status": "partial",
                        "sparse_counts": [
                            [LENS_BANK, 1, 3],
                            [LENS_BANK, 3, 2],
                            [CONTEXT_BANK, 1, 1],
                        ],
                    }
                }
            }
        },
        "full_profile_contexts": {
            "contexts": {
                "full-context:x": {
                    "object_composition": {
                        "layout": {"banks": [{"name": f"facet:{i}"} for i in range(40)]}
                    }
                }
            }
        },
    }
    terms = [
        recorded_term("squint-case:N:medial_meniscus", final, normal, -1),
        recorded_term("squint-case:P:medial_meniscus", final, shown, 1),
    ]
    record = {
        "study_uid": "Q",
        "values": {"Medial Meniscus": 0.4985},
        "objects": {
            "medial_meniscus": {
                "status": "proposal",
                "profile": final,
                "regions": [_region("QS", [1, 2, 2, 5, 1, 6])],
                "evidence": {"source": "current_study_anatomy_first_finite_windows"},
            }
        },
        "questions": {
            "Medial Meniscus": {
                "finding": {
                    "outcome": "open",
                    "reason": "medial_meniscus_unknown:proposal_without_sourced_trust",
                    "evidence": {
                        "kind": "single_tissue",
                        "necessary": ["medial_meniscus"],
                        "alternatives": [],
                        "supporting": ["femur"],
                        "readings": {
                            "medial_meniscus": {
                                "state": "unknown",
                                "code": "proposal_without_sourced_trust",
                            },
                            "femur": {"state": "unknown", "code": "no_precedent"},
                        },
                        "joint_voice": {
                            "state": "conflict",
                            "code": "conflicting_trusted_cases",
                        },
                        "joint_configuration_coverage": {
                            "status": "no_covered_warranted_configuration_cases"
                        },
                    },
                },
                "ranking": {"tier": "open"},
                "objects": {
                    "medial_meniscus": {
                        "outcome": "proposal",
                        "case_terms": terms,
                        "nearest_negative_case_ids": ["squint-case:N:medial_meniscus"],
                        "nearest_positive_case_ids": ["squint-case:P:medial_meniscus"],
                        "speaking_case_ids": [],
                        "location_status": "proposal",
                        "regions": [_region("QS", [1, 2, 2, 5, 1, 6])],
                    },
                    "femur": {"outcome": "unresolved_no_precedent", "case_terms": []},
                },
            }
        },
    }
    return memory, record


def test_question_plan_reads_defining_tissue_precedents_and_scope() -> None:
    memory, record = _memory_and_record()
    cases = {case["case_id"]: case for case in memory["cases"]}
    plan = question_plan(record, "Medial Meniscus", memory, cases)
    assert plan["study_label"] == 0
    assert [s["subject"] for s in plan["defining"]] == ["medial_meniscus"]
    assert [s["subject"] for s in plan["supporting"]] == ["femur"]
    subject = plan["defining"][0]
    assert subject["role"] == "necessary"
    # Both memory cases are of this tissue and called for the question.
    assert subject["memory_cases_other_studies"] == 2
    assert subject["query"]["code"] == "final"
    assert subject["normal"]["case_id"] == "squint-case:N:medial_meniscus"
    assert subject["normal"]["call"] == -1
    assert subject["normal"]["call_scope"] == "normal_for_this_condition_only"
    assert subject["presentation"]["call_scope"] == "positive_condition_presentation"
    assert subject["normal"]["full_profile"] == {
        "availability": "retained_sparse_counts",
        "status": "partial",
        "written_banks": 2,
        "sparse_rows": 3,
        "written_by_facet_kind": {"acquisition_context": 1, "lens_boolean": 1},
        "layout_banks": 40,
    }
    # A precedent without a full profile reference says so.
    assert subject["presentation"]["full_profile"] == {
        "availability": "no_full_profile_reference"
    }
    # The precedent's own reference point travels with its region.
    assert subject["normal"]["regions"][0]["anchors"][0]["kind"] == (
        "object_reference_point"
    )
    # No case called positive was compared: named, not fabricated.
    voice = record["questions"]["Medial Meniscus"]["objects"]["medial_meniscus"]
    voice["nearest_positive_case_ids"] = []
    plan = question_plan(record, "Medial Meniscus", memory, cases)
    assert plan["defining"][0]["presentation"] is None


def test_sheet_requests_ask_for_supports_only_where_support_was_retained() -> None:
    memory, record = _memory_and_record()
    cases = {case["case_id"]: case for case in memory["cases"]}
    plan = question_plan(record, "Medial Meniscus", memory, cases)
    requests = sheet_requests([plan])
    assert requests["Q"] == {"slices": {("QS", 1)}, "supports": set()}
    assert requests["N"] == {
        "slices": {("NS", 1)},
        "supports": {("medial_meniscus", "NS", 1)},
    }
    assert requests["P"] == {"slices": {("PS", 0)}, "supports": set()}


def test_bank_blocks_keep_uncompared_views_out_of_the_drawn_grid() -> None:
    other = '["Axial","1","1"]'
    query = {
        bank("signal_median", "overview"): [1, 1, 1],
        bank("signal_median", "overview", view=other): [1, 1, 1],
    }
    normal = {bank("signal_median", "overview"): [2, 0, 0]}
    blocks = bank_blocks(
        {"query": query, "normal": normal},
        {"normal": [bank("signal_median", "overview")]},
    )["blocks"]
    assert [(b["view"], b["compared"]) for b in blocks] == [
        (("Axial", "1", "1"), False),
        (("Coronal", "0", "0"), True),
    ]
    assert blocks[0]["writers"] == ["query"]


def test_question_plan_reads_the_finding_the_contract_writes() -> None:
    memory, record = _memory_and_record()
    # The finding is the contract's own output, not a copy of what the plan expects.
    finding = combine_condition("Medial Meniscus", {})
    record["questions"]["Medial Meniscus"]["finding"] = finding
    cases = {case["case_id"]: case for case in memory["cases"]}
    plan = question_plan(record, "Medial Meniscus", memory, cases)
    evidence = finding["evidence"]
    assert plan["finding"]["outcome"] == finding["outcome"] == "open"
    assert plan["finding"]["reason"] == finding["reason"]
    assert plan["finding"]["kind"] == evidence["kind"]
    assert plan["finding"]["contract_id"] == finding["contract_id"]
    necessary = list(evidence["necessary"])
    alternatives = [s for s in evidence["alternatives"] if s not in necessary]
    assert [s["subject"] for s in plan["defining"]] == necessary + alternatives
    assert [s["role"] for s in plan["defining"]] == (
        ["necessary"] * len(necessary) + ["alternative"] * len(alternatives)
    )
    assert [s["subject"] for s in plan["supporting"]] == list(evidence["supporting"])
    for subject in plan["defining"]:
        reading = evidence["readings"][subject["subject"]]
        assert subject["reading"] == {
            "state": reading["state"],
            "code": reading["code"],
        }
    # Supporting tissue is context: it is listed and never drawn as defining.
    assert not {s["subject"] for s in plan["supporting"]} & {
        s["subject"] for s in plan["defining"]
    }


def test_a_memory_other_than_the_one_recalled_from_is_named_per_precedent() -> None:
    memory, record = _memory_and_record()
    normal_id = "squint-case:N:medial_meniscus"
    cases = {case["case_id"]: case for case in memory["cases"]}
    subject = question_plan(record, "Medial Meniscus", memory, cases)["defining"][0]
    assert subject["query"]["verified"] is True
    assert subject["normal"]["code"] == subject["presentation"]["code"] == "drawn"
    # Must change: one count of a compared bank is other than the record's.
    changed = copy.deepcopy(cases)
    changed[normal_id]["profile"]["banks"][bank("signal_median", "overview")][0] += 1
    subject = question_plan(record, "Medial Meniscus", memory, changed)["defining"][0]
    assert subject["normal"]["code"] == "memory_case_differs_from_record"
    assert subject["normal"]["reproduction"]["case"] is False
    # The query then cannot be shown to be what was compared: it is withheld, with the
    # case that differs named, and nothing is decoded from it.
    assert subject["query"]["verified"] is False
    assert subject["query"]["code"] == "recalled_profile_not_reconstructed"
    assert subject["query"]["memory_case_differs"] == [normal_id]
    assert subject["query"]["banks"] == {}
    assert subject["query"]["withheld_bank_count"] > 0
    # Must not change: the precedent whose counts are the record's is still drawn.
    assert subject["presentation"]["code"] == "drawn"
    # Must not change: when only the query cannot be reproduced the memory is not
    # blamed. Both precedents are still drawn and no case is named as differing.
    perturbed = copy.deepcopy(record)
    query_banks = perturbed["objects"]["medial_meniscus"]["profile"]["banks"]
    query_banks[bank("signal_median", "overview")][0] += 1
    subject = question_plan(perturbed, "Medial Meniscus", memory, cases)["defining"][0]
    assert subject["query"]["verified"] is False
    assert subject["query"]["code"] == "recalled_profile_not_reconstructed"
    assert subject["query"]["memory_case_differs"] == []
    assert subject["normal"]["code"] == subject["presentation"]["code"] == "drawn"
    # A precedent the memory no longer holds is named, not left out.
    missing = {k: v for k, v in cases.items() if k != "squint-case:P:medial_meniscus"}
    subject = question_plan(record, "Medial Meniscus", memory, missing)["defining"][0]
    assert subject["presentation"] == {
        "case_id": "squint-case:P:medial_meniscus",
        "code": "precedent_not_in_memory",
    }


def test_chosen_questions_keep_the_records_order_and_refuse_a_name_it_lacks() -> None:
    record = {"questions": {"ACL": {}, "MCL": {}, "Fracture": {}}}
    assert chosen_questions(record, None) == ["ACL", "MCL", "Fracture"]
    assert chosen_questions(record, ["Fracture", "ACL"]) == ["ACL", "Fracture"]
    # A misspelt question must not end in a run that drew nothing.
    with pytest.raises(VisualCapacityError, match="question_not_in_record:Acl"):
        chosen_questions(record, ["ACL", "Acl"])


def test_teaching_words_name_the_source_and_never_a_localization() -> None:
    bootstrap = {
        "teaching_source": {"kind": "official_train_csv_label", "revision": "r1"}
    }
    assert teaching_words(bootstrap) == {
        "kind": "official_train_csv_label",
        "revision": "r1",
        "source_scope": None,
        "pixel_localization_confirmed": None,
    }
    admitted = {
        "teaching": {
            "kind": "independent_report_calls",
            "revision": "r2",
            "source_scope": "study_condition",
            "pixel_localization_confirmed": False,
            "calls": [],
        },
        "teaching_source": "report-calls-sha256:abc",
        "teaching_revision": "r2",
    }
    assert teaching_words(admitted) == {
        "kind": "independent_report_calls",
        "revision": "r2",
        "source_scope": "study_condition",
        "pixel_localization_confirmed": False,
    }
    # A bare string source (a case without a teaching record) is carried as the kind.
    bare = teaching_words(
        {"teaching_source": "report-calls-sha256:abc", "teaching_revision": "r2"}
    )
    assert (bare["kind"], bare["revision"]) == ("report-calls-sha256:abc", "r2")
    # A case that states nothing is given no source.
    assert teaching_words({}) == {
        "kind": None,
        "revision": None,
        "source_scope": None,
        "pixel_localization_confirmed": None,
    }
    # In words: report calls say no lesion was placed; an official label is not
    # given a localization statement it never made; nothing recorded says so.
    assert teaching_phrase(teaching_words(admitted)) == (
        "independent report calls (study-level; no pixel localization confirmed)"
    )
    assert teaching_phrase(teaching_words(bootstrap)) == "the official study label"
    assert teaching_phrase(teaching_words({})) == "an unrecorded source"


# --------------------------------------------------------------------------
# Pins: the run, the memory, the code, the teacher product and the selection


def test_check_memory_pins_refuses_a_memory_other_than_the_one_the_run_used() -> None:
    record = {
        "schema": "knee.squint-study/v1",
        "study_uid": "Q",
        "memory_revision": "rev-1",
    }
    memory = {"revision": "rev-1"}
    receipt = {
        "memory_manifest_sha256": "abc",
        "memory_revision": "rev-1",
        "_sha256": "receipt-digest",
    }
    pins = check_memory_pins(record, receipt, memory, "abc")
    assert pins["record_revision"] == pins["receipt"] == "matches"
    assert pins["capacity_population"] == "not_requested"
    # No receipt beside the run: the pin says it is absent, never that it matches.
    assert check_memory_pins(record, None, memory, "abc")["receipt"] == "absent"
    # Must change: each pin that does not hold is refused by its own name.
    wrong_schema = {**record, "schema": "knee.squint-study/v2"}
    with pytest.raises(VisualCapacityError, match="^study_record_schema_invalid:Q$"):
        check_memory_pins(wrong_schema, None, memory, "abc")
    wrong_revision = {**record, "memory_revision": "rev-0"}
    with pytest.raises(VisualCapacityError, match="^study_memory_revision_mismatch:Q$"):
        check_memory_pins(wrong_revision, None, memory, "abc")
    with pytest.raises(
        VisualCapacityError, match="^run_memory_manifest_sha256_mismatch$"
    ):
        check_memory_pins(record, receipt, memory, "another-manifest")
    stale = {**receipt, "memory_revision": "rev-0"}
    with pytest.raises(VisualCapacityError, match="^run_memory_revision_mismatch$"):
        check_memory_pins(record, stale, memory, "abc")
    # A capacity run's exclusion names the population it prepared from this memory.
    applied = {
        "exclusion_status": "applied",
        "prepared_population_identity": {"memory_manifest_sha256": "abc"},
    }
    capacity = {**record, "capacity_exclusion": applied}
    assert check_memory_pins(capacity, receipt, memory, "abc")[
        "capacity_population"
    ] == ("matches")
    other = {
        **applied,
        "prepared_population_identity": {"memory_manifest_sha256": "zzz"},
    }
    with pytest.raises(
        VisualCapacityError, match="^capacity_population_memory_mismatch:Q$"
    ):
        check_memory_pins({**record, "capacity_exclusion": other}, None, memory, "abc")
    # Must not change: a run that applied no exclusion states none, and is not refused.
    unexcluded = {**record, "capacity_exclusion": {"exclusion_status": "not_requested"}}
    pins = check_memory_pins(unexcluded, None, memory, "abc")
    assert pins["capacity_population"] == "not_requested"


def test_source_pin_names_the_files_whose_digest_differs_from_the_runs(
    tmp_path,
) -> None:
    (tmp_path / "a.py").write_text("one\n", encoding="utf-8")
    (tmp_path / "b.py").write_text("two\n", encoding="utf-8")
    digests = {
        name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()
        for name in ("a.py", "b.py")
    }
    pin = tmp_path / "pin.json"
    pin.write_text(json.dumps(digests), encoding="utf-8")
    # No pin supplied is stated, not assumed to be the same.
    assert source_pin(None, tmp_path) == {"status": "not_supplied"}
    same = source_pin(pin, tmp_path)
    assert (same["status"], same["files"]) == ("same", 2)
    assert same["differing"] == same["missing"] == []
    assert same["pin_sha256"] == hashlib.sha256(pin.read_bytes()).hexdigest()
    # Must change: a file edited since the run, and one gone; the pin may also be a
    # run's invocation record holding the digests as ``source_before``.
    (tmp_path / "a.py").write_text("changed\n", encoding="utf-8")
    (tmp_path / "b.py").unlink()
    invocation = tmp_path / "invocation.json"
    invocation.write_text(
        json.dumps({"source_before": digests, "elapsed": 1}), encoding="utf-8"
    )
    differs = source_pin(invocation, tmp_path)
    assert differs["status"] == "differs"
    assert (differs["differing"], differs["missing"]) == (["a.py"], ["b.py"])
    # A pin that cannot be read or lists nothing is refused, never read as the same.
    with pytest.raises(VisualCapacityError, match="^run_source_pin_unreadable$"):
        source_pin(tmp_path / "absent.json", tmp_path)
    empty = tmp_path / "empty.json"
    empty.write_text("{}", encoding="utf-8")
    with pytest.raises(VisualCapacityError, match="^run_source_pin_invalid$"):
        source_pin(empty, tmp_path)


def test_verified_product_opens_only_bytes_that_match_the_recorded_digest(
    tmp_path,
) -> None:
    product = tmp_path / "teacher.h5"
    product.write_bytes(b"teacher bytes")
    digest = hashlib.sha256(b"teacher bytes").hexdigest()
    recorded = {"path": str(product), "sha256": digest}
    assert verified_product(recorded) == (str(product), "verified")
    # Must change: a product that was never recorded, is gone, or has no digest is
    # not opened ...
    assert verified_product(None) == (None, "teacher_product_unrecorded")
    gone = {"path": str(tmp_path / "gone.h5"), "sha256": digest}
    assert verified_product(gone) == (None, "teacher_product_unavailable")
    undigested = {"path": str(product), "sha256": None}
    assert verified_product(undigested) == (None, "teacher_product_digest_unrecorded")
    # ... and neither is one whose bytes changed after the memory recorded them.
    product.write_bytes(b"teacher bytes, edited since")
    assert verified_product(recorded) == (None, "teacher_product_sha256_mismatch")


def test_selection_pin_compares_the_recorded_declaration_with_the_current_one() -> None:
    selection = question_selection("Medial Meniscus")
    digest = locator._selection_digest(selection)
    voice = {
        "source": {
            "selection": {
                "version": selection["version"],
                "descriptor_sha256": digest,
                "selected_banks": ["b-bank", "a-bank"],
            }
        }
    }
    pin = selection_pin("Medial Meniscus", voice)
    assert pin["status"] == "matches_current"
    assert pin["selected_banks"] == ["b-bank", "a-bank"]
    # Must change: another declaration digest is named, and the banks the run
    # recorded stay the ones drawn.
    recorded = voice["source"]["selection"]
    moved = {"source": {"selection": {**recorded, "descriptor_sha256": "0" * 64}}}
    pin = selection_pin("Medial Meniscus", moved)
    assert pin["status"] == "differs_from_current"
    assert pin["selected_banks"] == ["b-bank", "a-bank"]
    # A voice that recorded no selection (an older run) has nothing to compare.
    assert selection_pin("Medial Meniscus", {}) == {
        "status": "not_recorded",
        "selected_banks": None,
    }
    # A question the declarations do not know cannot be compared now, and says so.
    assert selection_pin("Not A Question", voice)["status"] == "unavailable_now"


# --------------------------------------------------------------------------
# One sheet, drawn


def test_draw_sheet_draws_unwritten_banks_as_unread(tmp_path) -> None:
    memory, record = _memory_and_record()
    cases = {case["case_id"]: case for case in memory["cases"]}
    plan = question_plan(record, "Medial Meniscus", memory, cases)
    series = fixtures.series_record()
    bounds = np.asarray(series["stack"].bounds_rc)
    pixels = np.tile(np.linspace(0, 1, 160, dtype=np.float32), (160, 1))

    def image():
        return {
            "code": "read",
            "pixels": pixels,
            "bounds_rc": bounds,
            "tile_shape_rc": (20, 20),
            "tile_mm": 10.0,
            # Columns run along patient x, rows along patient y, 1 mm pixels.
            "frame_inputs": [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0, 0.0, 1.0, 0.0],
                [1.0, 1.0],
            ],
            "view": ("Coronal", "0", "0"),
            "leg_codes": None,
            "leg_rule": None,
            "source_path": None,
        }

    images = {("Q", "QS", 1): image(), ("N", "NS", 1): image(), ("P", "PS", 0): image()}
    mask = np.zeros((1, 10, 10), dtype=bool)
    mask[0, 2:6, 3:7] = True
    roles = np.full((1, 4, 4), 2, dtype=np.int8)
    roles[0, 1:3, 1:3] = ROLE_OBJECT
    territories = {
        ("N", "medial_meniscus", "NS", 1): {
            "code": "resolved",
            "tile_window": [1, 2, 2, 6, 2, 6],
            "roles": roles,
            "object_share": np.zeros((1, 4, 4)),
            "native_support": {"mask": mask, "offset_rc": [60, 62]},
            "resolver": "test",
        }
    }
    plan["defining"][0]["panels"][0]["anchors"] = [
        {
            "kind": "anchor_point",
            "label": "femur (current_anchor_relative_prior)",
            "point_lps": [50.0, 70.0, 3.0],
        }
    ]
    drawn = draw_sheet(
        plan,
        images,
        territories,
        tmp_path / "sheet.png",
        run_label="test run",
        source_line="Sources: test",
        dpi=40,
    )
    assert (tmp_path / "sheet.png").stat().st_size > 0
    # The normal precedent writes no 2 mm bank and the presentation writes one
    # bank: their missing banks are drawn dashed, never as middles.
    assert drawn["cells"]["silent"] > 0
    groups = drawn["subjects"][0]["groups"]
    assert groups["query"][0]["code"] == "drawn"
    assert "territory" not in groups["query"][0]
    normal_panel = groups["normal"][0]
    assert normal_panel["support_px_in_window"] == 16
    assert normal_panel["window_px"] == 1600
    assert normal_panel["support_share_of_window"] == pytest.approx(0.01)
    anchor = groups["query"][0]["anchors"][0]
    assert anchor["native_rc"] == pytest.approx([70.0, 50.0])
    # Signed along the frame normal, rows x columns: here patient -z.
    assert anchor["off_plane_mm"] == pytest.approx(-3.0)
    assert anchor["in_view"] is True
    named = drawn["subjects"][0]["named_differences"]
    assert named["normal"] and named["presentation"]


def _territory_memory_and_record():
    """A one-question memory and record whose three profiles are territory-v2 readings."""
    territories = (
        fixtures.teacher_territory(),
        _territory_with_object_tiles([(2, 2), (2, 5), (5, 2), (5, 5)]),
        _territory_with_object_tiles([(3, 3), (3, 4), (4, 3)]),
    )
    query, normal, shown = (_territory_profile(t)[0] for t in territories)
    return _memory_and_record((query, normal, shown))


def _slice_image(bounds, size: int, tile: int, leg: dict | None = None) -> dict:
    """A native slice as ``read_images`` returns one: raw pixels on a tile grid."""
    return {
        "code": "read",
        "pixels": np.tile(np.linspace(0, 1, size, dtype=np.float32), (size, 1)),
        "bounds_rc": bounds,
        "tile_shape_rc": (tile, tile),
        "tile_mm": 10.0,
        "frame_inputs": None,
        "view": ("Coronal", "1", "1"),
        "leg_codes": None if leg is None else leg["codes"][1],
        "leg_rule": None if leg is None else leg["rule"],
        "leg_codes_sha256": None if leg is None else leg_codes_digest(leg),
        "source_path": None,
    }


def test_draw_sheet_draws_the_profiles_own_territory_and_refuses_another_grid(
    tmp_path,
) -> None:
    memory, record = _territory_memory_and_record()
    cases = {case["case_id"]: case for case in memory["cases"]}
    plan = question_plan(record, "Medial Meniscus", memory, cases)
    subject = plan["defining"][0]
    # The production writer's profile reproduces every recorded term, so it is the
    # profile drawn, and the places are the territory it was counted over.
    assert subject["query"]["verified"] is True
    assert subject["profile_versions"] == ["v2"]
    assert subject["compared_roles"] == ["context", "object"]
    (panel,) = subject["panels"]
    assert panel["counted_by"] == "territory"
    assert panel["window"] == (1, 2, 3, 5, 3, 5)

    leg = fixtures.expected_leg_map()
    bounds = np.asarray(fixtures.series_record()["stack"].bounds_rc)
    series_uid = fixtures.SERIES_UID

    def images(bounds_rc, size, tile, leg_map):
        return {
            (uid, series_uid, 1): _slice_image(bounds_rc, size, tile, leg_map)
            for uid in ("Q", "N", "P")
        }

    drawn = draw_sheet(
        plan,
        images(bounds, 160, 20, leg),
        {},
        tmp_path / "territory.png",
        run_label="test run",
        dpi=40,
    )
    assert (tmp_path / "territory.png").stat().st_size > 0
    groups = drawn["subjects"][0]["groups"]
    query = groups["query"][0]
    assert query["code"] == "drawn"
    assert query["roles_from"] == "profile_territory"
    assert query["grid_pin"] == "matches"
    assert query["leg_map"] == "profile_leg_map"
    assert query["compared_roles"] == ["context", "object"]
    assert query["window_outside_leg_tiles"] == 0
    summary = query["territory"]
    assert summary["origin"] == "teacher_support"
    assert (summary["object_tiles"], summary["context_tiles"]) == (4, 21)
    assert summary["outside_leg_tiles"] == 11
    # A support's share of a tile is an occupancy; it is measured and never purity.
    assert summary["share_status"] == "measured_occupancy"
    assert sorted(summary["object_tile_shares"]) == [0.25, 0.4, 0.5, 0.75]
    for key in ("normal", "presentation"):
        assert groups[key][0]["roles_from"] == "profile_territory"

    # Must change: the same territory on another tile grid is other pixels, so its
    # tiles are not drawn on them (the address of the window still is).
    other_grid = bounds * 5 // 4
    moved = draw_sheet(
        plan,
        images(other_grid, 200, 25, leg),
        {},
        tmp_path / "other-grid.png",
        run_label="test run",
        dpi=40,
    )
    query = moved["subjects"][0]["groups"]["query"][0]
    assert query["code"] == "drawn"
    assert query["grid_pin"] == "differs"
    assert query["roles_from"] == "not_drawn_tile_grid_differs"
    assert "territory" not in query
    # Must change: a leg map that is not the one the profile was written with is
    # named and not drawn.
    other_leg = fixtures.expected_leg_map()
    other_leg["codes"][:, 4, 4] = shapes.LEG_OUTSIDE
    unpinned = draw_sheet(
        plan,
        images(bounds, 160, 20, other_leg),
        {},
        tmp_path / "other-leg.png",
        run_label="test run",
        dpi=40,
    )
    query = unpinned["subjects"][0]["groups"]["query"][0]
    assert query["leg_map"] == "differs_from_profile"
    assert query["window_outside_leg_tiles"] is None
    assert query["roles_from"] == "profile_territory"


def test_a_place_no_comparison_read_is_not_drawn_as_compared(tmp_path) -> None:
    memory, record = _territory_memory_and_record()
    cases = {case["case_id"]: case for case in memory["cases"]}
    plan = question_plan(record, "Medial Meniscus", memory, cases)
    leg = fixtures.expected_leg_map()
    bounds = np.asarray(fixtures.series_record()["stack"].bounds_rc)
    images = {
        (uid, fixtures.SERIES_UID, 1): _slice_image(bounds, 160, 20, leg)
        for uid in ("Q", "N", "P")
    }

    def compared_in_panels(plan_drawn, name):
        drawn = draw_sheet(
            plan_drawn, images, {}, tmp_path / name, run_label="test run", dpi=40
        )
        groups = drawn["subjects"][0]["groups"]
        return {key: groups[key][0]["compared_roles"] for key in groups}

    # The panels lie in the coronal view and the comparisons read its object and
    # context banks.
    read = ["context", "object"]
    assert compared_in_panels(plan, "read.png") == {
        "query": read,
        "normal": read,
        "presentation": read,
    }
    # Must change: comparisons that read banks of another view only did not read
    # these places, whatever their roles.
    axial = {"orientation": "Axial", "fluid_sensitive": "1", "fat_suppression": "1"}
    elsewhere = [
        territory_bank_name(axial, "object", "signal_median", "overview", 10.0)
    ]
    moved = copy.deepcopy(plan)
    subject = moved["defining"][0]
    subject["compared_banks"] = elsewhere
    for key in ("normal", "presentation"):
        subject[key]["common_banks"] = elsewhere
    assert compared_in_panels(moved, "other-view.png") == {
        "query": [],
        "normal": [],
        "presentation": [],
    }
    # Must change: with no comparison at all (no precedent was compared) nothing
    # was read either; the places the profile was counted over are still shown.
    bare = copy.deepcopy(record)
    voice = bare["questions"]["Medial Meniscus"]["objects"]["medial_meniscus"]
    voice["case_terms"] = []
    voice["nearest_negative_case_ids"] = []
    voice["nearest_positive_case_ids"] = []
    uncompared = question_plan(bare, "Medial Meniscus", memory, cases)
    assert uncompared["defining"][0]["query"]["code"] == "no_recorded_terms"
    assert (
        uncompared["defining"][0]["panel_scope"]["source"]
        == "profile_lineage_without_recorded_terms"
    )
    drawn = draw_sheet(
        uncompared, images, {}, tmp_path / "none.png", run_label="test run", dpi=40
    )
    query = drawn["subjects"][0]["groups"]["query"][0]
    assert query["roles_from"] == "profile_territory"
    assert query["compared_roles"] == []


def test_the_room_under_the_panels_holds_the_fullest_caption(tmp_path) -> None:
    memory, record = _territory_memory_and_record()
    cases = {case["case_id"]: case for case in memory["cases"]}
    plan = question_plan(record, "Medial Meniscus", memory, cases)
    leg = fixtures.expected_leg_map()
    bounds = np.asarray(fixtures.series_record()["stack"].bounds_rc)
    images = {
        (uid, fixtures.SERIES_UID, 1): _slice_image(bounds, 160, 20, leg)
        for uid in ("Q", "N", "P")
    }
    drawn = draw_sheet(
        plan, images, {}, tmp_path / "room.png", run_label="test run", dpi=40
    )
    subject = plan["defining"][0]
    panels = {
        "query": subject["panels"][0],
        "normal": subject["normal"]["panels"][0],
        "presentation": subject["presentation"]["panels"][0],
    }

    def rows(text: str, width: int) -> int:
        return sum(_wrap(line, width).count("\n") + 1 for line in text.split("\n"))

    for key, panel in panels.items():
        written = drawn["subjects"][0]["groups"][key][0]
        for width in (59, 75):
            # No caption written is longer than the room reserved under its panel.
            assert rows(_panel_caption(written, panel), width) <= _caption_rows(
                panel, width
            )
        # The room follows the width the caption is wrapped to.
        assert _caption_rows(panel, 59) >= _caption_rows(panel, 75)
    # Must change with the kind of panel: a territory panel's caption is longer than
    # the four rows a box and an address once needed.
    assert _caption_rows(panels["query"], 75) > 4
    (box_panel,) = region_panels(
        [{"series_uid": "S", "view": {}, "window": [0, 1, 0, 2, 0, 2]}], "tile_box"
    )
    assert _caption_rows(box_panel, 75) < _caption_rows(panels["query"], 75)


def test_sheet_requests_ask_for_a_support_only_where_the_territory_came_from_one() -> (
    None
):
    memory, record = _territory_memory_and_record()
    cases = {case["case_id"]: case for case in memory["cases"]}
    plan = question_plan(record, "Medial Meniscus", memory, cases)
    series_uid = fixtures.SERIES_UID
    asked = {
        "slices": {(series_uid, 1)},
        "supports": {("medial_meniscus", series_uid, 1)},
    }
    requests = sheet_requests([plan])
    assert requests["Q"] == requests["N"] == requests["P"] == asked
    # Must change: a territory placed by a relation is an address, with no support
    # of a teacher to ask for; the slice alone is read.
    related = copy.deepcopy(plan)
    for panel in related["defining"][0]["panels"]:
        panel["origin"] = "anatomical_relation"
    assert sheet_requests([related])["Q"] == {
        "slices": {(series_uid, 1)},
        "supports": set(),
    }


def test_every_sheet_says_what_a_label_and_a_share_do_not_show() -> None:
    def text_of(memory, record, label):
        cases = {case["case_id"]: case for case in memory["cases"]}
        plan = question_plan(record, "Medial Meniscus", memory, cases)
        return " ".join(_caption_lines(plan, label))

    v1_memory, v1_record = _memory_and_record()
    v2_memory, v2_record = _territory_memory_and_record()
    v1_text = text_of(v1_memory, v1_record, "run one")
    v2_text = text_of(v2_memory, v2_record, "run two")
    for text, label in ((v1_text, "run one"), (v2_text, "run two")):
        # A study-level call places no lesion; a support's share is an occupancy; a
        # query that is not the one recall compared is marked; the label is for
        # evaluation only.
        assert "does not place a lesion" in text
        assert "occupancy" in text
        assert "UNVERIFIED" in text
        assert "recall never reads it" in text
        assert f"Run: {label}." in text
    # Must change with what was drawn: territory words only for a v2 profile, the
    # box-only words only for a v1 profile.
    assert "Territory tiles" in v2_text
    assert "Territory tiles" not in v1_text
    assert "A v1 profile counted every 10 mm tile" in v1_text
    assert "A v1 profile counted every 10 mm tile" not in v2_text


def test_importing_the_sheet_script_loads_no_drawing_layer() -> None:
    """Drawing is development only: matplotlib loads inside draw_sheet alone."""
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    code = (
        "import sys, scripts.squint_visual_capacity as s; "
        "print(int('matplotlib' in sys.modules), int(hasattr(s, 'draw_sheet')))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=root,
        env={"PYTHONPATH": str(root / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    assert result.stdout.split() == ["0", "1"]
    # And no production module names the sheet script.
    for path in (root / "src" / "knee").rglob("*.py"):
        assert "squint_visual_capacity" not in path.read_text(encoding="utf-8"), path


# --------------------------------------------------------------------------
# Reading native slices (a synthetic DICOM study; no real study is read)


def _synthetic_study(root, pixels):
    uid, series_uid = generate_uid(), generate_uid()
    directory = root / "train_series" / uid / series_uid
    directory.mkdir(parents=True)
    _write_dicom(directory / "one.dcm", uid, series_uid, pixels)
    _write_tables(root, uid, series_uid)
    return uid, series_uid, directory / "one.dcm"


def test_read_images_reads_the_requested_native_slice_and_names_what_it_cannot(
    tmp_path,
) -> None:
    pixels = np.arange(16).reshape(4, 4)
    uid, series_uid, dicom = _synthetic_study(tmp_path, pixels)
    requests = {
        uid: {
            "slices": {(series_uid, 0), (series_uid, 5), ("no-such-series", 0)},
            "supports": set(),
        }
    }
    images, territories, work = read_images(
        tmp_path, requests, {}, io_workers=1, isolate=False
    )
    drawn = images[(uid, series_uid, 0)]
    assert drawn["code"] == "read"
    # The raw pixels at the address, not a windowed or resampled picture of them.
    assert np.array_equal(drawn["pixels"], pixels.astype(np.float32))
    assert drawn["bounds_rc"].shape == (4, 4, 4)
    assert drawn["tile_mm"] == 10.0
    assert drawn["view"] == ("Sagittal", "1", "1")
    assert drawn["source_path"] == str(dicom.resolve())
    # The plane frame is built from the slice's own DICOM geometry.
    assert drawn["frame_inputs"][0] == [0.0, 0.0, 0.0]
    assert drawn["frame_inputs"][1] == [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
    # Must change: a slice the series lacks, and a series the study lacks, are named.
    assert images[(uid, series_uid, 5)] == {"code": "slice_outside_series"}
    assert images[(uid, "no-such-series", 0)] == {"code": "series_missing"}
    assert territories == {}
    assert work[uid]["teacher_product"] == "not_requested"
    assert (work[uid]["series_read"], work[uid]["slices_drawn"]) == (1, 3)


def test_read_images_opens_a_teacher_product_only_if_its_digest_is_the_recorded_one(
    tmp_path,
) -> None:
    uid, series_uid, _ = _synthetic_study(tmp_path, np.arange(16).reshape(4, 4))
    ask = {uid: {"slices": {(series_uid, 0)}, "supports": {("femur", series_uid, 0)}}}
    key = (uid, "femur", series_uid, 0)
    # No product recorded for the study: the support is refused by that name.
    _, territories, work = read_images(tmp_path, ask, {}, io_workers=1, isolate=False)
    assert territories == {key: {"code": "teacher_product_unrecorded"}}
    assert work[uid]["teacher_product"] == "teacher_product_unrecorded"
    # Must change: a product whose bytes are not the recorded ones is never opened
    # (these bytes are not an archive, so opening them would fail otherwise).
    product = tmp_path / "teacher.h5"
    product.write_bytes(b"not the bytes the memory recorded")
    products = {uid: {"path": str(product), "sha256": "0" * 64}}
    images, territories, work = read_images(
        tmp_path, ask, products, io_workers=1, isolate=False
    )
    assert territories == {key: {"code": "teacher_product_sha256_mismatch"}}
    assert work[uid]["teacher_product"] == "teacher_product_sha256_mismatch"
    # The native slice is read whatever the product: the picture needs no support.
    assert images[(uid, series_uid, 0)]["code"] == "read"


# --------------------------------------------------------------------------
# The command


def test_main_refuses_by_name_and_writes_nothing(tmp_path, capsys) -> None:
    output = tmp_path / "sheets"
    argv = [
        "--run",
        str(tmp_path / "run"),
        "--label",
        "Test Run",
        "--memory",
        str(tmp_path / "memory"),
        "--root",
        str(tmp_path),
        "--study-uid",
        "Q",
        "--output",
        str(output),
    ]
    # A memory that is not there is refused first, by the name the memory loader gives.
    assert main(argv) == 2
    captured = capsys.readouterr()
    assert captured.err.strip() == "memory_manifest_missing"
    assert captured.out == ""
    assert not output.exists()
    # Must change: a run manifest already in the output is named and left as it was.
    manifest = output / "test-run" / "run-manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text("{}", encoding="utf-8")
    assert main(argv) == 2
    assert capsys.readouterr().err.startswith("sheets_already_exist:")
    assert manifest.read_text(encoding="utf-8") == "{}"


def test_main_describes_its_options_and_demands_the_required_ones(capsys) -> None:
    with pytest.raises(SystemExit) as stopped:
        main(["--help"])
    assert stopped.value.code == 0
    text = capsys.readouterr().out
    for option in (
        "--run",
        "--label",
        "--memory",
        "--root",
        "--study-uid",
        "--output",
        "--question",
        "--io-workers",
        "--dpi",
        "--run-source-pin",
        "--require-same-source",
    ):
        assert option in text
    assert "Nothing is overwritten" in text
    # Must change: without the required options it is a usage error, not a run.
    with pytest.raises(SystemExit) as stopped:
        main([])
    assert stopped.value.code == 2
    assert "required" in capsys.readouterr().err


def test_the_script_runs_as_a_command() -> None:
    import subprocess
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "scripts/squint_visual_capacity.py", "--help"],
        cwd=root,
        env={"PYTHONPATH": str(root / "src"), "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    assert result.stdout.startswith("usage:")
    assert "--require-same-source" in result.stdout
