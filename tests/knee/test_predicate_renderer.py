"""Intent tests for the predicates picture adapter and the saved-record reader, both signs.

The picture layer may only ARRANGE. These tests pin that it passes the stage's values through
unchanged, and that a saved record which disagrees with the stage's own vocabulary is REFUSED
rather than drawn -- a drawn corruption is worse than a missing picture, because it looks like
evidence.
"""

import pytest

from knee.pictures.predicates import FindingRow, PredicatesPanels, panels
from knee.predicates.findings import read_findings
from workbench.render.predicate_frames import saved_reading


class _Row:
    def __init__(self, ownership_code: str = "", relations_code: str = "") -> None:
        self.ownership = type("O", (), {"code": ownership_code})()
        self.relations = type("R", (), {"code": relations_code})()


def _saved(reading) -> dict:
    """One study entry shaped exactly as the production writer serialises it."""
    return {
        "findings": {
            "code": reading.code,
            "why": reading.why,
            "series_with_population": reading.series_with_population,
            "series_with_construction": reading.series_with_construction,
            "findings": [
                {
                    "index": f.index,
                    "requirement": f.requirement,
                    "code": f.code,
                    "reason": f.reason,
                }
                for f in reading.findings
            ],
        }
    }


# ---------------------------------------------------------------- the picture adapter


def test_the_adapter_passes_every_value_through_unchanged():
    reading = read_findings((_Row("present"),))
    frame = panels(reading)
    assert isinstance(frame, PredicatesPanels)
    assert frame.code == reading.code
    assert frame.why == reading.why
    assert frame.series_with_population == reading.series_with_population
    assert frame.series_with_construction == reading.series_with_construction
    assert len(frame.rows) == 12
    for row, finding in zip(frame.rows, reading.findings, strict=True):
        assert isinstance(row, FindingRow)
        assert (row.index, row.requirement, row.code, row.reason) == (
            finding.index,
            finding.requirement,
            finding.code,
            finding.reason,
        )


def test_the_adapter_draws_twelve_rows_even_for_a_named_absence():
    frame = panels(read_findings(None))
    assert len(frame.rows) == 12
    assert [r.index for r in frame.rows] == list(range(12))


def test_the_adapter_carries_no_number_against_any_finding():
    # MUST NOT: a confidence is knee.output's lossy projection of this record. No field of a
    # drawn row may be numeric except the index.
    for row in panels(read_findings((_Row("present"),))).rows:
        assert isinstance(row.index, int)
        for value in (row.requirement, row.code, row.reason):
            assert isinstance(value, str)
            assert not value.replace(".", "").isdigit()


# ---------------------------------------------------------------- the saved-record reader


def test_a_faithful_saved_record_reconstitutes_the_reading():
    reading = read_findings((_Row("present"), _Row("present")))
    restored = saved_reading(_saved(reading))
    assert restored == reading


def test_a_record_with_no_findings_is_refused():
    with pytest.raises(ValueError, match="missing_saved_findings"):
        saved_reading({})


def test_a_record_missing_a_row_is_refused():
    # MUST NOT: eleven rows must never be drawn as if they were the twelve.
    saved = _saved(read_findings((_Row("present"),)))
    saved["findings"]["findings"].pop()
    with pytest.raises(ValueError, match="saved_findings_count_mismatch"):
        saved_reading(saved)


def test_a_record_whose_index_sequence_is_not_the_twelve_in_order_is_refused():
    # MUST NOT: the row order IS the competition's column order, so the sequence must be 0..11
    # exactly. A permuted or relabelled sequence would mislabel findings in the drawn table.
    # (Swapping rows 0 and 1 is deliberately NOT the case under test: their requirement, code and
    # reason are identical, so that swap is a genuine no-op and refusing it would be noise.)
    for index, replacement in ((3, 9), (0, 11), (11, 0)):
        saved = _saved(read_findings((_Row("present"),)))
        saved["findings"]["findings"][index]["index"] = replacement
        with pytest.raises(ValueError, match="saved_findings_index_mismatch"):
            saved_reading(saved)


def test_a_code_outside_the_stages_vocabulary_is_refused():
    # MUST NOT: a code this unit does not own must never reach the picture.
    saved = _saved(read_findings((_Row("present"),)))
    saved["findings"]["findings"][3]["code"] = "violated"
    with pytest.raises(ValueError, match="saved_finding_code_unknown:violated"):
        saved_reading(saved)


def test_a_reason_that_no_longer_names_its_requirement_is_refused():
    # MUST NOT: a reason and its requirement drifting apart is exactly what the composed
    # sentence exists to prevent, so the renderer refuses rather than drawing the drift.
    saved = _saved(read_findings((_Row("present"),)))
    saved["findings"]["findings"][5]["reason"] = "something else entirely"
    with pytest.raises(ValueError, match="saved_finding_reason_mismatch:5"):
        saved_reading(saved)
