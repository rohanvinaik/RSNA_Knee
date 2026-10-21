"""Intent of merging recorded visual calls into one publishable calls file, in both signs.

A reviewer's call says something about exactly the views it names. Merging files may
change how a call is written, never what it asserts or who asserted it.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from knee.diagnosis.squint_bootstrap import (
    CALLS_SCHEMA,
    REVIEW_SCHEMA,
    SquintBootstrapError,
    adapt_recorded_calls,
    validate_calls,
)

SAGITTAL = ["Sagittal", "0", "0"]
CORONAL = ["Coronal", "0", "0"]
PIN = "a" * 64
ROOT = Path(__file__).resolve().parents[1]


def _cli():
    path = ROOT / "scripts" / "squint_object_bootstrap.py"
    spec = importlib.util.spec_from_file_location("squint_object_bootstrap_adapt", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _candidate(candidate_id: str, subject: str = "femur") -> dict:
    return {
        "candidate_id": candidate_id,
        "case_id": candidate_id,
        "study_uid": f"study-{candidate_id}",
        "subject": subject,
        "profile_sha256": "c" * 64,
        "source_product_sha256": "d" * 64,
        "full_profile": {
            "payload_ref": f"payload-{candidate_id}",
            "context_ref": f"context-{candidate_id}",
            "product_record_sha256": "e" * 64,
        },
        "profile_views": [SAGITTAL, CORONAL],
        "evidence": {
            "panels": [
                {
                    "view": {
                        "orientation": view[0],
                        "fluid_sensitive": view[1],
                        "fat_suppression": view[2],
                    },
                    "image_state": "read",
                    "support_state": "drawn",
                }
                for view in (SAGITTAL, CORONAL)
            ]
        },
    }


@pytest.fixture
def review() -> dict:
    return {
        "schema": REVIEW_SCHEMA,
        "source_manifest_sha256": "b" * 64,
        "candidates": [_candidate("c46"), _candidate("c5"), _candidate("c8")],
    }


def _reject_46() -> dict:
    # As recorded: the far sagittal support is the whole leg outline; the coronal
    # support mixes soft tissue and condyle and was deliberately left unasserted.
    return {
        "number": 46,
        "candidate_id": "c46",
        "call": "reject",
        "notes": "far sagittal support is the leg outline; coronal left unasserted",
        "negative_views": [SAGITTAL],
    }


def test_a_scoped_reject_keeps_exactly_its_recorded_views(review):
    adapted = adapt_recorded_calls(
        [("lead-calls", "Claude Code lead", [_reject_46()])], PIN
    )

    call = adapted["calls"]["calls"][0]
    assert call["views"] == [SAGITTAL]
    assert "negative_views" not in call
    checked = validate_calls(review, adapted["calls"], PIN)
    assert checked["negative_views"] == {"c46": [SAGITTAL]}
    assert CORONAL not in checked["negative_views"]["c46"]


def test_dropping_the_recorded_scope_would_widen_the_reject(review):
    # Why the adapter carries the scope: a reject with no views rejects every drawn view.
    widened = {
        key: value
        for key, value in _reject_46().items()
        if key in ("candidate_id", "call", "notes")
    }
    calls = {
        "schema": CALLS_SCHEMA,
        "review_sha256": PIN,
        "reader": "x",
        "calls": [widened],
    }

    checked = validate_calls(review, calls, PIN)

    assert checked["negative_views"] == {"c46": [SAGITTAL, CORONAL]}
    adapted = adapt_recorded_calls(
        [("lead-calls", "Claude Code lead", [_reject_46()])], PIN
    )
    assert (
        validate_calls(review, adapted["calls"], PIN)["negative_views"]
        != checked["negative_views"]
    )


def test_a_mixed_view_confirm_keeps_its_positive_and_negative_scopes_apart(review):
    record = {
        "number": 5,
        "candidate_id": "c5",
        "call": "confirm",
        "notes": "coronal is the distal femur; sagittal is posterior thigh tissue",
        "views": [CORONAL],
        "negative_views": [SAGITTAL],
    }

    adapted = adapt_recorded_calls([("lead-calls", "Claude Code lead", [record])], PIN)
    checked = validate_calls(review, adapted["calls"], PIN)

    assert adapted["calls"]["calls"][0]["views"] == [CORONAL]
    assert adapted["calls"]["calls"][0]["negative_views"] == [SAGITTAL]
    assert checked["confirmed_case_ids"] == ["c5"]
    assert checked["negative_views"] == {"c5": [SAGITTAL]}


def test_each_call_keeps_its_own_reader(review):
    root = {
        "candidate_id": "c8",
        "call": "reject",
        "notes": "soft tissue beside the condyle",
    }
    lead = _reject_46()
    named = {**lead, "candidate_id": "c5", "reader": "a named second reviewer"}

    adapted = adapt_recorded_calls(
        [
            ("root-calls", "Codex lead", [root]),
            ("lead-calls", "Claude Code lead", [lead, named]),
        ],
        PIN,
    )
    validate_calls(review, adapted["calls"], PIN)

    readers = {
        call["candidate_id"]: call["reader"] for call in adapted["calls"]["calls"]
    }
    assert readers == {
        "c8": "Codex lead",
        "c46": "Claude Code lead",
        "c5": "a named second reviewer",
    }


def test_a_call_cannot_carry_an_empty_reader(review):
    adapted = adapt_recorded_calls(
        [("lead-calls", "Claude Code lead", [_reject_46()])], PIN
    )
    adapted["calls"]["calls"][0]["reader"] = ""

    with pytest.raises(SquintBootstrapError) as error:
        validate_calls(review, adapted["calls"], PIN)

    assert error.value.code == "call_reader_invalid"


def test_a_candidate_called_in_two_sources_is_refused():
    with pytest.raises(SquintBootstrapError) as error:
        adapt_recorded_calls(
            [("a", "reader one", [_reject_46()]), ("b", "reader two", [_reject_46()])],
            PIN,
        )

    assert error.value.code == "adapt_duplicate_candidate"


def test_a_reject_with_two_different_scopes_is_refused_not_guessed():
    record = {**_reject_46(), "views": [CORONAL]}

    with pytest.raises(SquintBootstrapError) as error:
        adapt_recorded_calls([("lead-calls", "Claude Code lead", [record])], PIN)

    assert error.value.code == "adapt_reject_scope_ambiguous"


def test_source_records_are_not_changed_and_extra_keys_go_to_the_mapping():
    records = [_reject_46()]
    before = copy.deepcopy(records)

    adapted = adapt_recorded_calls([("lead-calls", "Claude Code lead", records)], PIN)

    assert records == before
    assert "number" not in adapted["calls"]["calls"][0]
    assert adapted["mapping"]["c46"] == {
        "origin": "lead-calls",
        "recorded": {"number": 46},
    }


def test_the_cli_writes_a_validated_calls_file_and_its_adaptation_record(
    tmp_path, review
):
    main = _cli().main

    review_path = tmp_path / "review.json"
    review_path.write_text(json.dumps(review), encoding="utf-8")
    pin = hashlib.sha256(review_path.read_bytes()).hexdigest()
    root = tmp_path / "calls-root.json"
    root.write_text(
        json.dumps(
            {
                "schema": CALLS_SCHEMA,
                "review_sha256": pin,
                "reader": "Codex lead",
                "calls": [
                    {"candidate_id": "c8", "call": "reject", "notes": "soft tissue"}
                ],
            }
        ),
        encoding="utf-8",
    )
    lead = tmp_path / "calls-lead.jsonl"
    lead.write_text(json.dumps(_reject_46()) + "\n", encoding="utf-8")
    sources_before = (root.read_bytes(), lead.read_bytes())
    out = tmp_path / "adapted"

    result = main(
        [
            "adapt",
            "--review",
            str(review_path),
            "--calls",
            str(root),
            "--jsonl",
            str(lead),
            "Claude Code lead",
            "--output",
            str(out),
        ]
    )

    assert result["call_count"] == 2
    assert result["negative"] == 2
    calls = json.loads((out / "calls.json").read_text(encoding="utf-8"))
    assert {c["candidate_id"]: c["views"] for c in calls["calls"] if "views" in c} == {
        "c46": [SAGITTAL]
    }
    adaptation = json.loads((out / "adaptation.json").read_text(encoding="utf-8"))
    assert [source["reader"] for source in adaptation["sources"]] == [
        "Codex lead",
        "Claude Code lead",
    ]
    assert (root.read_bytes(), lead.read_bytes()) == sources_before
    with pytest.raises(SystemExit):
        main(
            [
                "adapt",
                "--review",
                str(review_path),
                "--calls",
                str(root),
                "--output",
                str(out),
            ]
        )
