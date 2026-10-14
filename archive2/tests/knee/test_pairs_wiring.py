"""The pairs on the route, in the receipt and on the study drawer's caption (the-funnel tasks 0.1
and 0.2), both signs. The route reads the pairs once per study before any series is measured and
carries them on the run; the writer saves them in the study's entry as plain data; the drawer
words each plane's code from the adapter's vocabulary, says when none was saved, and refuses a
saved record that disagrees with the writer."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from knee import pipeline
from knee.pictures import study
from knee.pictures.study import PAIRING_CAPTIONS, pairing_caption
from knee.study.pairs import PAIR_CODES
from knee.telemetry import recording
from workbench.measure.object_analysis import pairs_record, study_entry
from workbench.render import study_frames

_fixture_path = Path(__file__).with_name("test_pipeline_measurements.py")
_fixture_spec = importlib.util.spec_from_file_location(
    "pipeline_measurement_fixture_for_pairs", _fixture_path
)
assert _fixture_spec is not None and _fixture_spec.loader is not None
_fixture_module = importlib.util.module_from_spec(_fixture_spec)
_fixture_spec.loader.exec_module(_fixture_module)
STUDY_UID = _fixture_module.STUDY_UID
STACKED_UID = _fixture_module.STACKED_UID
UNSTACKED_UID = _fixture_module.UNSTACKED_UID
_write_corpus = _fixture_module._write_corpus


# --- the route ---------------------------------------------------------------------------------


def test_run_study_reads_the_pairs_once_before_any_series_and_carries_them(
    tmp_path: Path,
) -> None:
    _write_corpus(tmp_path)
    with recording() as run_ledger:
        result = pipeline.open_and_run(tmp_path, STUDY_UID)
    names = [event.name for event in run_ledger.events()]
    assert names.count("pairs.produced") == 1
    assert names.count("study.consumed_by.pairs") == 1
    assert names.index("study.produced") < names.index("study.consumed_by.pairs")
    assert names.index("pairs.produced") < names.index("collapse.produced")
    assert result.pairs is not None
    assert result.pairs.code == "present"
    # The synthetic corpus: two Axial series, both fat-bright, so the one plane is surplus and
    # both series are kept.
    (pair,) = result.pairs.pairs
    assert pair.plane == "Axial"
    assert pair.code == "surplus"
    assert pair.bright_uids == (STACKED_UID, UNSTACKED_UID)
    assert pair.dark_uids == ()


def test_a_run_built_without_the_operation_carries_no_pairs() -> None:
    assert pipeline.StudyRun(uid="u", split="train").pairs is None


# --- the writer --------------------------------------------------------------------------------


def test_the_study_entry_carries_the_pairs_as_plain_data(tmp_path: Path) -> None:
    _write_corpus(tmp_path)
    result = pipeline.open_and_run(tmp_path, STUDY_UID)
    entry = study_entry(STUDY_UID, result, [], len(result.series))
    saved = entry["pairs"]
    assert result.pairs is not None
    assert saved == pairs_record(result.pairs)
    assert saved["code"] == "present"
    # Plain as saved: a list, the same before and after the receipt's JSON.
    assert saved["code_names"] == list(PAIR_CODES)
    assert saved["pairs"] == [
        {
            "plane": "Axial",
            "bright_uids": [STACKED_UID, UNSTACKED_UID],
            "dark_uids": [],
            "unreadable_uids": [],
            "code": "surplus",
        }
    ]
    # Plain data: it round-trips through the receipt's JSON, which refuses NaN.
    assert json.loads(json.dumps(entry, allow_nan=False))["pairs"] == saved


def test_a_run_without_pairs_writes_no_pairs_key() -> None:
    entry = study_entry("u", pipeline.StudyRun(uid="u", split="train"), [], 0)
    assert "pairs" not in entry


# --- the adapter and the drawer ----------------------------------------------------------------


def test_the_adapter_hands_on_every_code_the_stage_says_and_names_the_rest() -> None:
    for code in PAIR_CODES:
        assert pairing_caption(code) == code
    # MUST NOT: word a code the stage does not say, or a value that is not text.
    for stray in ("lesion", "", None, 1, True, ("paired",)):
        assert pairing_caption(stray) == "pairing_code_unknown"
    assert all(pairing_caption(code) in PAIRING_CAPTIONS for code in (*PAIR_CODES, "x"))


def test_every_pairing_caption_is_worded_by_the_drawer() -> None:
    assert all(code in study_frames.PAIRING_WORDS for code in PAIRING_CAPTIONS)
    assert PAIRING_CAPTIONS == (*PAIR_CODES, "pairing_code_unknown")


def test_the_drawer_reads_the_study_entrys_saved_pairs_and_words_each_plane() -> None:
    receipt = {
        "studies": [
            {"study_uid": "other", "pairs": {"code": "present", "pairs": []}},
            {
                "study_uid": "s",
                "pairs": {
                    "code": "present",
                    "code_names": list(PAIR_CODES),
                    "pairs": [
                        {
                            "plane": "Coronal",
                            "bright_uids": ["a"],
                            "dark_uids": ["b"],
                            "unreadable_uids": [],
                            "code": "paired",
                        },
                        {
                            "plane": "Axial",
                            "bright_uids": [],
                            "dark_uids": ["c"],
                            "unreadable_uids": ["d"],
                            "code": "solitary",
                        },
                    ],
                },
            },
        ]
    }
    saved = study_frames.saved_pairs(receipt, "s")
    assert saved is not None and len(saved["pairs"]) == 2
    line = study_frames.pairing_line(saved)
    assert line.startswith(
        "pairs (study stage, from the series table; record present): "
    )
    assert (
        "Coronal paired (one fat-bright and one fat-dark series): 1 fat-bright, 1 fat-dark, 0 unreadable"
        in line
    )
    assert (
        "Axial solitary (one series; its conjunction will be silence): 0 fat-bright, 1 fat-dark, 1 unreadable"
        in line
    )
    assert line.index("Coronal") < line.index("Axial")


def test_the_drawer_says_when_no_pairs_record_was_saved() -> None:
    assert study_frames.saved_pairs({"records": []}, "s") is None
    assert study_frames.saved_pairs({"studies": [{"study_uid": "s"}]}, "s") is None
    assert (
        study_frames.saved_pairs({"studies": [{"study_uid": "t", "pairs": {}}]}, "s")
        is None
    )
    assert study_frames.pairing_line(None) == study_frames.PAIRS_NOT_SAVED
    assert "not saved" in study_frames.pairing_line(None)
    empty = study_frames.pairing_line({"code": "predecessor_empty", "pairs": []})
    assert empty.endswith("no plane in the record")


def test_the_drawer_names_an_unknown_code_and_never_words_it_as_a_pairing() -> None:
    line = study_frames.pairing_line(
        {
            "code": "present",
            "pairs": [
                {
                    "plane": "Axial",
                    "bright_uids": [],
                    "dark_uids": [],
                    "unreadable_uids": [],
                    "code": "lesion",
                }
            ],
        }
    )
    assert "not worded" in line
    assert "lesion" not in line.split("not worded")[1]
    assert study.pairing_caption("lesion") == "pairing_code_unknown"


def test_the_drawer_words_an_all_unreadable_plane_as_no_readable_series() -> None:
    """`none` is the code of a plane in the table whose every flag the stage could not read, so
    its words say "no readable series" beside the count of unreadable series."""
    saved = study_frames.saved_pairs(
        {
            "studies": [
                {
                    "study_uid": "s",
                    "pairs": {
                        "code": "present",
                        "code_names": list(PAIR_CODES),
                        "pairs": [
                            {
                                "plane": "Axial",
                                "bright_uids": [],
                                "dark_uids": [],
                                "unreadable_uids": ["a", "b"],
                                "code": "none",
                            }
                        ],
                    },
                }
            ]
        },
        "s",
    )
    line = study_frames.pairing_line(saved)
    assert (
        "Axial none (no readable series of this plane): 0 fat-bright, 0 fat-dark, 2 unreadable"
        in line
    )
    # MUST NOT: assert "no series of this plane" beside a count of unreadable series; a plane
    # with no series at all is absent from the table and has no record to word.
    assert "no series of this plane" not in study_frames.PAIRING_WORDS["none"]
    assert "no series of this plane" not in line


def test_the_drawer_refuses_identifier_fields_that_are_not_lists_of_text() -> None:
    # MUST NOT: count the characters of a string, the items of a mapping, or a missing field as
    # zero; each is a record that disagrees with the writer, named by its field and raised.
    def receipt(**fields: object) -> dict:
        plane = {
            "plane": "Coronal",
            "bright_uids": ["a"],
            "dark_uids": ["b"],
            "unreadable_uids": [],
            "code": "paired",
            **fields,
        }
        return {
            "studies": [
                {"study_uid": "s", "pairs": {"code": "present", "pairs": [plane]}}
            ]
        }

    assert study_frames.saved_pairs(receipt(), "s") is not None
    for name in study_frames.PAIR_IDENTIFIER_FIELDS:
        assert name in ("bright_uids", "dark_uids", "unreadable_uids")
        for stray in ("abc", None, 3, {"a": 1}, ("a",), ["a", 1], [None], [["a"]]):
            with pytest.raises(
                ValueError, match=f"saved_pair_identifiers_not_a_list_of_text:{name}"
            ):
                study_frames.saved_pairs(receipt(**{name: stray}), "s")
        missing = receipt()
        del missing["studies"][0]["pairs"]["pairs"][0][name]
        with pytest.raises(
            ValueError, match=f"saved_pair_identifiers_not_a_list_of_text:{name}"
        ):
            study_frames.saved_pairs(missing, "s")
    # An empty list is a count of zero the stage made, and is kept.
    kept = study_frames.saved_pairs(receipt(bright_uids=[], code="solitary"), "s")
    assert kept is not None
    assert "0 fat-bright, 1 fat-dark, 0 unreadable" in study_frames.pairing_line(kept)


def test_the_drawer_refuses_a_saved_record_that_disagrees_with_the_writer() -> None:
    # MUST NOT: draw a pairs record that is not a record, a plane that is not a mapping, or a
    # plane whose name or code is not text; each is named and raised, never worded.
    with pytest.raises(ValueError, match="saved_pairs_not_a_record"):
        study_frames.saved_pairs({"studies": [{"study_uid": "s", "pairs": "yes"}]}, "s")
    with pytest.raises(ValueError, match="saved_pairs_not_a_record"):
        study_frames.saved_pairs(
            {"studies": [{"study_uid": "s", "pairs": {"code": "present"}}]}, "s"
        )
    with pytest.raises(ValueError, match="saved_pair_not_a_record"):
        study_frames.saved_pairs(
            {"studies": [{"study_uid": "s", "pairs": {"pairs": ["Axial"]}}]}, "s"
        )
    with pytest.raises(ValueError, match="saved_pair_plane_or_code_not_text"):
        study_frames.saved_pairs(
            {
                "studies": [
                    {
                        "study_uid": "s",
                        "pairs": {"pairs": [{"plane": 1, "code": "paired"}]},
                    }
                ]
            },
            "s",
        )
