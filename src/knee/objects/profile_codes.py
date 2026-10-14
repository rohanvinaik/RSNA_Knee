"""A support decision describes acquired samples, never anatomy."""


def profile_support_code(requested: int, supported: int) -> str:
    """Name complete, partial, missing or empty support, and invalid counts.

    post: __return__ in ('invalid_counts', 'empty_request', 'no_support', 'partial_support', 'complete_support')
    post: (__return__ == 'invalid_counts') == (requested < 0 or supported < 0 or supported > requested)
    post: (__return__ == 'empty_request') == (requested == 0 and supported == 0)
    post: (__return__ == 'no_support') == (requested > 0 and supported == 0)
    post: (__return__ == 'partial_support') == (0 < supported < requested)
    post: (__return__ == 'complete_support') == (requested > 0 and supported == requested)
    """
    if requested < 0 or supported < 0 or supported > requested:
        return "invalid_counts"
    if requested == 0:
        return "empty_request"
    if supported == 0:
        return "no_support"
    if supported < requested:
        return "partial_support"
    return "complete_support"
