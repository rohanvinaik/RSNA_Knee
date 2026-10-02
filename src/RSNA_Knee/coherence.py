"""Coherence / Trajectory Disambiguation — Pattern 7.

For ambiguous candidates (2-3 supports, interference in the middle band),
compute similarity at INCREASING DECOMPOSITION DEPTHS.

Correct matches CONVERGE (similarity increases with depth).
Wrong matches DIVERGE (similarity decreases with depth).

Dynamic weighting: more uncertain candidates get more trajectory
influence on their final score.

Reference: DATA_GEOMETRY_ARCHITECTURE.md, Pattern 7.
"""

from __future__ import annotations


def compute_trajectory(
    candidate_features: set[str],
    seed_features: set[str],
    expand_fn=None,
    max_depth: int = 3,
) -> list[float]:
    """Compute similarity at increasing decomposition depths.

    expand_fn: given a set of features, returns the expanded set
    (one hop through shared entities/anchors/contexts).

    Returns [sim_depth_0, sim_depth_1, sim_depth_2, ...]
    """
    trajectory = []
    current_candidate = set(candidate_features)
    current_seed = set(seed_features)

    for depth in range(max_depth):
        if not current_candidate or not current_seed:
            trajectory.append(0.0)
            continue
        intersection = len(current_candidate & current_seed)
        union = len(current_candidate | current_seed)
        trajectory.append(intersection / union if union > 0 else 0.0)

        if expand_fn:
            current_candidate = expand_fn(current_candidate)
            current_seed = expand_fn(current_seed)

    return trajectory


def trajectory_score(trajectory: list[float]) -> float:
    """Score from convergence/divergence pattern.

    Positive = converging (genuine). Negative = diverging (false positive).
    Deeper layers weighted more.
    """
    if len(trajectory) < 2:
        return 0.0
    score = 0.0
    for i in range(1, len(trajectory)):
        delta = trajectory[i] - trajectory[i - 1]
        layer_weight = 1.0 + (i * 0.5)
        score += delta * layer_weight
    return score
