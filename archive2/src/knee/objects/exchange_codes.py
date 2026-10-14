"""Pure scoped decisions for a transported sample-run reading."""


def exchange_code(
    coverage_code: str,
    valid_count: int,
    sample_count: int,
    dark_runs: int,
    bounded_matches: int,
    open_matches: int,
) -> str:
    """Name coverage, native support, and donor-selected runs separately.

    post: __return__ in ('invalid_measurement', 'outside_slab', 'slab_support_unknown', 'normal_unavailable', 'empty_profile', 'native_missing', 'native_open', 'native_multiple', 'concurrent', 'peer_only', 'disagreement')
    post: __return__ != 'concurrent' or (coverage_code == 'covered' and valid_count == sample_count and sample_count > 0 and bounded_matches == 1 and open_matches == 0)
    """
    if (
        coverage_code
        not in ("covered", "outside_slab", "slab_support_unknown", "normal_unavailable")
        or sample_count < 0
        or not 0 <= valid_count <= sample_count
        or not 0 <= dark_runs <= (sample_count + 1) // 2
        or bounded_matches < 0
        or open_matches < 0
        or bounded_matches + open_matches > dark_runs
    ):
        return "invalid_measurement"
    if coverage_code != "covered":
        return coverage_code
    if sample_count == 0:
        return "empty_profile"
    if valid_count < sample_count:
        return "native_missing"
    if open_matches:
        return "native_open"
    if bounded_matches > 1:
        return "native_multiple"
    if bounded_matches == 1:
        return "concurrent"
    if dark_runs == 0:
        return "peer_only"
    return "disagreement"
