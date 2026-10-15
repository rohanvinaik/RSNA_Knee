"""The input stage's decisions: pure, total over their arguments, returning named codes."""


def label_code(raw: str) -> str:
    """The host's label for one finding, as a named code (pure — pinned).

    "1" and "0" are the host's values, kept as given. A blank cell is "not_given": no label was given, which is not
    a 0. Any other value is "unrecognized", carried rather than coerced.
    """
    if raw == "1":
        return "1"
    if raw == "0":
        return "0"
    if raw == "":
        return "not_given"
    return "unrecognized"


def tag_reasons(
    tag: str, n_absent: int, n_empty: int, n_malformed: int, n_degenerate: int
) -> list[str]:
    """The reasons a geometry tag stops a stack, one per kind of zero some file holds (pure — pinned).

    "<tag>_absent", "<tag>_empty", "<tag>_malformed" and "<tag>_degenerate", in that order, each when its count is
    not zero: four different zeros, kept apart.
    """
    reasons: list[str] = []
    if n_absent:
        reasons.append(f"{tag}_absent")
    if n_empty:
        reasons.append(f"{tag}_empty")
    if n_malformed:
        reasons.append(f"{tag}_malformed")
    if n_degenerate:
        reasons.append(f"{tag}_degenerate")
    return reasons


def stack_codes(
    directory_exists: bool,
    n_slices: int,
    n_multiframe: int,
    geometry_reasons: list[str],
    n_shapes: int,
    n_dtypes: int,
    n_positions: int,
    n_distinct_positions: int,
) -> tuple[str, ...]:
    """Whether a series' files form one stack of slices, as named codes (pure — pinned).

    ("stackable",) when every file holds one frame, no geometry tag stops the stack (`geometry_reasons`, from
    `tag_reasons`, is empty), all files share one Rows x Columns and one stored dtype, and no two of them share a
    position. Otherwise every reason that holds, in this order: "multiframe_file", the geometry reasons as given,
    "shape_varies", "dtype_varies", and "positions_repeat", which is judged only when all n_slices files have a
    position (n_positions). A missing directory is ("directory_missing",) and an empty one ("no_slices",): two
    different zeros, kept apart.
    """
    if not directory_exists:
        return ("directory_missing",)
    if n_slices == 0:
        return ("no_slices",)
    reasons = ["multiframe_file"] if n_multiframe else []
    reasons.extend(geometry_reasons)
    if n_shapes > 1:
        reasons.append("shape_varies")
    if n_dtypes > 1:
        reasons.append("dtype_varies")
    if n_positions == n_slices and n_distinct_positions < n_slices:
        reasons.append("positions_repeat")
    return tuple(reasons) or ("stackable",)
