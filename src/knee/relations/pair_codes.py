"""Exact categorical warrant on supplied footprints, never label interpolation."""

CODES = (
    "paired",
    "profile_unbracketed",
    "item_unread",
    "invalid_measurement",
    "source_unassigned",
    "far_unassigned",
    "source_ambiguous",
    "far_ambiguous",
    "source_mismatch",
    "same_object",
)


def pair_code(source: int, trace: int, near: list[int], far: list[int]) -> str:
    """Name the supplied facts. -1 is inactive; -2 is unread; zero is unassigned.

    post: __return__ in CODES
    post: __return__ != 'paired' or (source > 0 and trace == 1)
    post: __return__ != 'paired' or all(x in (-1, source) for x in near)
    post: __return__ != 'paired' or (len(set(x for x in far if x != -1)) == 1 and any(x > 0 and x != source for x in far))
    """
    if source < 0 or trace < 0 or trace > 7:
        return "invalid_measurement"
    if any(x < -2 for x in near + far):
        return "invalid_measurement"
    if trace == 0:
        return "item_unread"
    if trace != 1:
        return "profile_unbracketed"
    if source == 0:
        return "source_unassigned"
    near_labels = set(near) - {-1}
    far_labels = set(far) - {-1}
    if not near_labels or not far_labels or -2 in near_labels or -2 in far_labels:
        return "item_unread"
    if 0 in near_labels:
        return "source_unassigned"
    if len(near_labels) != 1:
        return "source_ambiguous"
    if source not in near_labels:
        return "source_mismatch"
    if 0 in far_labels:
        return "far_unassigned"
    if len(far_labels) != 1:
        return "far_ambiguous"
    if source in far_labels:
        return "same_object"
    return "paired"
