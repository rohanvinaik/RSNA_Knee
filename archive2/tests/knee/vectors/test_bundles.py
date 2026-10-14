"""The bundles stage's contract, both signs, ahead of its body (task 6.7).

These pin the record shape and the stage's totality. The body's own intent tests -- what each
bank counts -- are added with the body.
"""

from knee.absence import CODES as ABSENCE_CODES
from knee.vectors.bundles import (
    BANK_STATUS,
    CODES,
    SUBJECT_KIND,
    UNAVAILABLE_BANKS,
    BundlesReading,
    bank_status_code,
    read_bundles,
)


def test_the_stage_is_total_and_names_its_silence():
    for arguments in (
        (None, None, None),
        (object(), 0, ""),
        ("ownership", "lenses", "measurement"),
    ):
        reading = read_bundles(*arguments)
        assert isinstance(reading, BundlesReading)
        assert reading.code in CODES
        assert reading.code in ABSENCE_CODES


def test_the_subject_kind_is_the_indexed_extent_and_never_a_name():
    reading = read_bundles(None, None, None)
    assert reading.subject_kind == SUBJECT_KIND
    for word in ("femur", "tibia", "bone", "cartilage", "medial", "lateral"):
        assert word not in reading.subject_kind


def test_one_plane_is_read_and_the_record_says_so():
    assert read_bundles(None, None, None).planes_read == 1


def test_unavailable_banks_are_named_with_their_reason():
    names = [name for name, _ in UNAVAILABLE_BANKS]
    assert "conjunction_across_acquisitions" in names
    for _name, why in UNAVAILABLE_BANKS:
        assert why


def test_bank_status_both_signs():
    assert bank_status_code(True, True) == "written"
    assert bank_status_code(False, True) == "unavailable"
    assert bank_status_code(True, False) == "unavailable"
    assert bank_status_code(False, False) == "unavailable"
    assert set(BANK_STATUS) == {"written", "unavailable"}


def test_a_bank_is_never_written_without_its_source():
    # MUST NOT: a bank written from nothing would be rows of zero asserting a reading was made.
    for countable in (False, True):
        assert bank_status_code(False, countable) != "written"
