"""Intent pins for warranted whole-normal recall and relevant-tissue coverage."""

from knee.diagnosis import squint_contracts


def test_negative_with_extra_defining_site_coverage_stays_complete() -> None:
    assert (
        squint_contracts._configuration_case_disposition(
            call=-1,
            covered_subjects=["a", "b"],
            positive_branches=[["b"]],
            required_negative=["a"],
        )
        == "negative_configuration"
    )


def test_positive_call_with_nonempty_uncovered_branches_is_incomplete() -> None:
    assert (
        squint_contracts._configuration_case_disposition(
            call=1,
            covered_subjects=["a"],
            positive_branches=[["b"], ["c", "d"]],
            required_negative=["b", "c", "d"],
        )
        == "positive_coverage_incomplete"
    )


def test_context_subject_does_not_complete_negative_coverage() -> None:
    assert (
        squint_contracts._configuration_case_disposition(
            call=-1,
            covered_subjects=["joint"],
            positive_branches=[["b"]],
            required_negative=["a"],
        )
        == "context_only"
    )


def test_whole_normal_can_speak_without_every_separately_normal_site() -> None:
    assert (
        squint_contracts._configuration_case_disposition(
            call=-1,
            covered_subjects=["femur"],
            positive_branches=[["femur"], ["tibia"]],
            required_negative=["femur", "tibia"],
        )
        == "negative_configuration"
    )


def test_missing_comparison_is_not_whole_normal_recall() -> None:
    assert (
        squint_contracts._configuration_case_disposition(
            call=-1,
            covered_subjects=[],
            positive_branches=[["femur"], ["tibia"]],
            required_negative=["femur", "tibia"],
        )
        == "context_only"
    )


def test_an_unsigned_case_is_not_a_normal_configuration() -> None:
    assert (
        squint_contracts._configuration_case_disposition(
            call=0,
            covered_subjects=["femur", "tibia"],
            positive_branches=[["femur"], ["tibia"]],
            required_negative=["femur", "tibia"],
        )
        == "invalid_call"
    )
