"""Intent for the real recall status boundary, independent of admission policy.

Missing support, an observed contradiction and invalid input need different
remedies. This parser supplies no identity assertion or publication warrant.
"""

from knee.diagnosis.squint_identity import _sanity_status


def test_missing_observation_stays_unknown():
    assert _sanity_status(None) == "unknown"


def test_explicit_unknown_does_not_become_support_or_contradiction():
    assert (
        _sanity_status(
            {"schema": "knee.object-anatomical-sanity/v1", "status": "unknown"}
        )
        == "unknown"
    )


def test_supported_status_is_distinct_from_missing_observation():
    assert (
        _sanity_status(
            {"schema": "knee.object-anatomical-sanity/v1", "status": "plausible"}
        )
        == "plausible"
    )


def test_known_contradiction_cannot_become_neutral():
    assert (
        _sanity_status(
            {"schema": "knee.object-anatomical-sanity/v1", "status": "contradicted"}
        )
        == "contradicted"
    )


def test_foreign_schema_cannot_supply_apparent_support():
    assert _sanity_status({"schema": "foreign", "status": "plausible"}) is None


def test_bare_status_string_cannot_supply_an_observation():
    assert _sanity_status("plausible") is None


def test_unrecognized_status_is_invalid_instead_of_negative():
    assert (
        _sanity_status(
            {"schema": "knee.object-anatomical-sanity/v1", "status": "unrecognized"}
        )
        is None
    )


def test_anatomical_prior_cannot_assert_object_identity():
    assert (
        _sanity_status(
            {
                "schema": "knee.object-anatomical-sanity/v1",
                "status": "plausible",
                "identity_assertion": "femur",
            }
        )
        is None
    )
