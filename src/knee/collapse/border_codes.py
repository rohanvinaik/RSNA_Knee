"""Named outcomes for one dark-interval reading; no anatomical question."""


def border_code(
    frame_clipped: bool,
    valid_count: int,
    sample_count: int,
    dark_runs: int,
    bounded: bool,
) -> str:
    """Separate unobserved, multiply observed and uniquely bracketed intervals.

    post: __return__ in ('invalid_measurement', 'frame_clipped', 'empty_profile', 'missing_profile', 'no_dark_bracket', 'multiple_brackets', 'bracketed')
    post: __return__ != 'bracketed' or (not frame_clipped and valid_count == sample_count and sample_count > 0 and dark_runs == 1 and bounded)
    """
    if (
        valid_count < 0
        or sample_count < 0
        or valid_count > sample_count
        or dark_runs < 0
    ):
        return "invalid_measurement"
    if frame_clipped:
        return "frame_clipped"
    if sample_count == 0:
        return "empty_profile"
    if valid_count != sample_count:
        return "missing_profile"
    if dark_runs > 1:
        return "multiple_brackets"
    if dark_runs == 0 or not bounded:
        return "no_dark_bracket"
    return "bracketed"
