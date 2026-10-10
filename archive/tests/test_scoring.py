"""Intent tests for the macro ROC-AUC scorer (Pattern 1).

Authored from INTENT, not from the code: known-answer AUC cases a
radiology-competition scorer must satisfy, plus the degenerate-label codes.
Detective's synth suite pins behaviour; this file pins meaning.
"""

from RSNA_Knee.scoring import auc_status, average_ranks, macro_auc, roc_auc

# --- auc_status: the degenerate-label codes ---------------------------------


def test_status_empty():
    assert auc_status([]) == "empty"


def test_status_no_positives():
    assert auc_status([0, 0, 0]) == "no_positives"


def test_status_no_negatives():
    assert auc_status([1, 1]) == "no_negatives"


def test_status_ok():
    assert auc_status([0, 1]) == "ok"


# --- average_ranks: tie handling --------------------------------------------


def test_ranks_no_ties():
    assert average_ranks([0.1, 0.9, 0.5]) == [1.0, 3.0, 2.0]


def test_ranks_ties_get_average_of_span():
    assert average_ranks([0.1, 0.5, 0.5, 0.9]) == [1.0, 2.5, 2.5, 4.0]


def test_ranks_all_tied():
    assert average_ranks([0.3, 0.3, 0.3]) == [2.0, 2.0, 2.0]


# --- roc_auc: known answers --------------------------------------------------


def test_auc_perfect_separation_is_1():
    assert roc_auc([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]) == 1.0


def test_auc_inverted_separation_is_0():
    assert roc_auc([1, 1, 0, 0], [0.1, 0.2, 0.8, 0.9]) == 0.0


def test_auc_all_scores_tied_is_half():
    assert roc_auc([0, 1, 0, 1], [0.5, 0.5, 0.5, 0.5]) == 0.5


def test_auc_one_swap():
    # positives at 0.9 and 0.3; negative at 0.5 sits between them:
    # 1 of 2 positive/negative pairs correctly ordered, 1 wrong -> 0.5
    assert roc_auc([1, 0, 1], [0.9, 0.5, 0.3]) == 0.5


def test_auc_tie_across_classes_counts_half():
    # pos/neg tied at 0.5 -> that pair contributes 0.5; other pair correct
    assert roc_auc([0, 1, 1], [0.5, 0.5, 0.9]) == 0.75


# --- macro_auc: aggregation + skip reporting ---------------------------------


def test_macro_mean_over_defined_findings():
    labels = {"acl": [0, 1], "effusion": [0, 0, 1, 1]}
    scores = {"acl": [0.2, 0.7], "effusion": [0.9, 0.8, 0.2, 0.1]}
    out = macro_auc(labels, scores)
    assert out["per_finding"] == {"acl": 1.0, "effusion": 0.0}
    assert out["score"] == 0.5
    assert out["skipped"] == {}
    assert out["n_scored"] == 2


def test_macro_skips_degenerate_findings_and_reports_them():
    labels = {"acl": [0, 1], "fracture": [0, 0]}
    scores = {"acl": [0.2, 0.7], "fracture": [0.1, 0.2]}
    out = macro_auc(labels, scores)
    assert out["per_finding"] == {"acl": 1.0}
    assert out["score"] == 1.0
    assert out["skipped"] == {"fracture": "no_positives"}
    assert out["n_scored"] == 1


def test_macro_all_skipped_scores_zero_not_crash():
    out = macro_auc({"acl": []}, {"acl": []})
    assert out == {
        "score": 0.0,
        "per_finding": {},
        "skipped": {"acl": "empty"},
        "n_scored": 0,
    }


# --- out-of-contract behaviour, pinned explicitly ----------------------------


def test_roc_auc_out_of_contract_degenerate_labels_fail_fast():
    # roc_auc's contract requires auc_status(labels) == "ok"; callers gate on
    # it first. Outside the contract the function fails FAST with a zero
    # division (n_neg == 0), never a silent wrong number.
    import pytest

    with pytest.raises(ZeroDivisionError):
        roc_auc([1], [1])
