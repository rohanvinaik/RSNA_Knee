"""The laterality sign: which way is the outer side of the knee, from the witness's side, or abstain.

`docs/OBJECT_MODEL.md`, laterality: the frame tells left from right (LPS: +x is the patient's
left), but not which side of this knee is lateral; a small ringed object beside the inferior big
one on the coronal, the witness (`knee.objects.selection`, `lateral_small_ringed`), sits on the
lateral side, and its side gives the sign. Four of the twelve findings depend on it (Medial and
Lateral Meniscus, Medial and Lateral OA). With no witness the sign is `side_abstained`, and every
side-dependent code downstream abstains with it; a missing reading is never a guess.

The pure decision is `lateral_sign_code`; the orchestration lives in the selection.
"""

from __future__ import annotations

import math

#: Which way the outer side lies along the patient's left-right axis, or the silence.
SIGN_CODES: tuple[str, ...] = ("left", "right", "side_abstained", "invalid_measurement")


def lateral_sign_code(witness_offset_mm: float | None) -> str:
    """The lateral side from the witness's offset along the left-right axis (pure -- pinned).

    `witness_offset_mm` is the witness's centre minus the inferior big object's centre along LPS
    +x (the patient's left), or None when no witness was selected. None is "side_abstained";
    a bool, a non-number or NaN is "invalid_measurement"; exactly zero is "side_abstained" (the
    witness sits on neither side); positive is "left" (the lateral side is the patient's left);
    negative is "right".

    post: __return__ in SIGN_CODES
    """
    if witness_offset_mm is None:
        return "side_abstained"
    if isinstance(witness_offset_mm, bool) or not isinstance(
        witness_offset_mm, (int, float)
    ):
        return "invalid_measurement"
    if math.isnan(witness_offset_mm):
        return "invalid_measurement"
    if witness_offset_mm == 0.0:
        return "side_abstained"
    return "left" if witness_offset_mm > 0.0 else "right"


__all__ = ["SIGN_CODES", "lateral_sign_code"]
