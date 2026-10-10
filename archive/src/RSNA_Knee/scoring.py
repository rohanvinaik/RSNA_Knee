"""Official competition scorer — Pattern 1: Scorer-First.

Metric (per the competition Evaluation page, recorded in docs/THEORY_OF_THE_CASE.md):
macro-averaged ROC-AUC over 12 binary findings. Each finding's AUC is computed
independently over all test studies; the submission score is their unweighted mean.

Design notes (house rules):
- The AUC core is a PURE, total function over lists of numbers — rank-based
  (Mann-Whitney U) with average ranks for ties. No sklearn dependency, so the
  decision is Detective-pinnable and identical in the kernel (internet off).
- Degenerate-label cases are classified by `auc_status`, which returns NAMED
  STRING CODES ("ok" / "empty" / "no_positives" / "no_negatives"), never a
  bare bool — "cannot determine" and "determined false" must not collapse.
- FINDING COLUMNS ARE NOT HARDCODED YET. The exact column spellings are bound
  from sample_submission.csv (Phase 1.5 format-compliance gate: examine gold,
  never assume). `macro_auc` is generic over finding names until then.
"""

from __future__ import annotations


def auc_status(labels: list) -> str:
    """Classify whether ROC-AUC is defined for a label vector.

    Returns one of:
      "ok"           — at least one positive AND one negative label
      "empty"        — no labels at all
      "no_positives" — labels present but all negative (AUC undefined)
      "no_negatives" — labels present but all positive (AUC undefined)
    """
    if not labels:
        return "empty"
    n_pos = sum(1 for y in labels if y == 1)
    if n_pos == 0:
        return "no_positives"
    if n_pos == len(labels):
        return "no_negatives"
    return "ok"


def average_ranks(scores: list) -> list:
    """1-based ranks of `scores`, ties receiving the average of their span.

    Example: [0.1, 0.5, 0.5, 0.9] -> [1.0, 2.5, 2.5, 4.0]
    """
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1.0
        for t in range(i, j + 1):
            ranks[order[t]] = avg
        i = j + 1
    return ranks


def roc_auc(labels: list, scores: list) -> float:
    """Rank-based ROC-AUC (Mann-Whitney U with tie-averaged ranks).

    Preconditions: len(labels) == len(scores) and auc_status(labels) == "ok".
    Callers gate on `auc_status` first; this function assumes a defined AUC.
    """
    n = len(labels)
    n_pos = sum(1 for y in labels if y == 1)
    n_neg = n - n_pos
    ranks = average_ranks(scores)
    rank_sum_pos = sum(r for r, y in zip(ranks, labels) if y == 1)
    u = rank_sum_pos - n_pos * (n_pos + 1) / 2.0
    return u / (n_pos * n_neg)


def macro_auc(labels_by_finding: dict, scores_by_finding: dict) -> dict:
    """Macro-averaged ROC-AUC over findings, with per-finding breakdown.

    Returns a dict:
      {"score": float,                  # mean AUC over findings with status "ok"
       "per_finding": {name: float},    # AUC per defined finding
       "skipped": {name: status_code},  # findings where AUC was undefined
       "n_scored": int}

    A finding present in labels but with degenerate labels is SKIPPED and
    reported, not silently folded in — the caller decides what a skip means
    (in CV it usually means the fold is too small; on the hidden test the
    organizers guarantee both classes exist).
    """
    per_finding: dict = {}
    skipped: dict = {}
    for name in sorted(labels_by_finding):
        labels = labels_by_finding[name]
        status = auc_status(labels)
        if status != "ok":
            skipped[name] = status
            continue
        per_finding[name] = roc_auc(labels, scores_by_finding[name])
    n_scored = len(per_finding)
    score = sum(per_finding.values()) / n_scored if n_scored else 0.0
    return {
        "score": score,
        "per_finding": per_finding,
        "skipped": skipped,
        "n_scored": n_scored,
    }
