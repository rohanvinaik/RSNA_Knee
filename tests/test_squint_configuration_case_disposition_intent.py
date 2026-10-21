"""Intent pins for negative completeness and positive branch coverage."""

from knee.diagnosis import squint_contracts


def test_negative_with_extra_defining_site_coverage_stays_complete() -> None:
    assert (
        squint_contracts._configuration_case_disposition(
            call=-1,
            covered_subjects=["a", "b"],
            positive_branches=[["b"]],
            required_negative=["a"],
        )
        == "complete_negative"
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
