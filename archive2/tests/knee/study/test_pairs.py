"""Intent tests for the pairing decision (knee.study.pairs.pair_code), written from the contract:
a pair is exactly one fat-bright and one fat-dark series of one plane; one series alone is solitary
and its conjunction will be silence; more than one of a flavour is surplus and nothing is paired;
no series is none; a count that cannot be read is a refusal, never a finding."""

from knee.study.pairs import PAIR_CODES, pair_code


def test_one_of_each_flavour_is_the_pair() -> None:
    assert pair_code(n_bright=1, n_dark=1) == "paired"


def test_one_series_alone_is_solitary_whichever_flavour() -> None:
    assert pair_code(n_bright=1, n_dark=0) == "solitary"
    assert pair_code(n_bright=0, n_dark=1) == "solitary"


def test_a_surplus_of_either_flavour_pairs_nothing() -> None:
    # Which two to lay over each other is not settled by a count, so all are kept and none paired.
    assert pair_code(n_bright=2, n_dark=1) == "surplus"
    assert pair_code(n_bright=1, n_dark=2) == "surplus"
    assert pair_code(n_bright=2, n_dark=0) == "surplus"
    assert pair_code(n_bright=0, n_dark=3) == "surplus"


def test_no_series_is_none_not_solitary() -> None:
    assert pair_code(n_bright=0, n_dark=0) == "none"


def test_a_negative_count_is_a_refusal_not_a_finding() -> None:
    assert pair_code(n_bright=-1, n_dark=1) == "invalid_count"
    assert pair_code(n_bright=1, n_dark=-1) == "invalid_count"


def test_every_code_is_in_the_vocabulary() -> None:
    for n_bright in range(-1, 4):
        for n_dark in range(-1, 4):
            assert pair_code(n_bright, n_dark) in PAIR_CODES


def test_a_pair_is_never_made_across_flavours_of_the_same_kind() -> None:
    # Two fat-bright series are not a pair even though there are two of them.
    assert pair_code(n_bright=2, n_dark=0) != "paired"
