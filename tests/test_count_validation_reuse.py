from knee.encoding import counts
from knee.encoding.counts import BankLayout, CountBundle, CountLayout


def test_shared_immutable_row_is_validated_once_without_hashing_contents(monkeypatch):
    row = (0,) * 512
    layout = CountLayout(
        "same", "same", tuple(BankLayout(str(i), 512) for i in range(3696))
    )
    bundle = CountBundle(layout, (row,) * 3696)
    original = counts._is_plain_int
    calls = []

    def checked(value):
        calls.append(value)
        return original(value)

    monkeypatch.setattr(counts, "_is_plain_int", checked)
    assert counts._valid_bundle(bundle)
    assert len(calls) == 3696 + 512


def test_reuse_does_not_skip_bank_width_or_malformed_count():
    row = (0, 1)
    wrong_width = CountBundle(
        CountLayout("x", "c", (BankLayout("a", 2), BankLayout("b", 3))), (row, row)
    )
    bad_count = CountBundle(CountLayout("x", "c", (BankLayout("a", 2),)), ((False, 1),))
    assert not counts._valid_bundle(wrong_width)
    assert not counts._valid_bundle(bad_count)


def test_different_rows_are_each_checked_and_lifetimes_do_not_share_cache():
    layout = CountLayout("x", "c", (BankLayout("a", 2), BankLayout("b", 2)))
    assert counts._valid_bundle(CountBundle(layout, ((0, 1), (1, 0))))
    assert not counts._valid_bundle(CountBundle(layout, ((0, 1), (1, -1))))
