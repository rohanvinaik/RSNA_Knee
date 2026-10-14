"""The joiner can call this drawer, and a corruption signal is never dressed as a typo."""

import inspect

import pytest

from workbench.render._out import ArgumentRefusal
from workbench.render.object_packet import CENTRE_OF_THE_FRAME, draw

# --- positive: what it must do -------------------------------------------------------------


def test_the_joiner_can_draw_without_knowing_this_renderer_s_argument_spelling() -> (
    None
):
    """`draw(run, study_uid, out)` is the one entry every renderer exposes, per task 4b.1."""
    parameter = inspect.signature(draw).parameters["probe_fraction_rc"]
    assert parameter.default is not inspect.Parameter.empty
    assert parameter.default == CENTRE_OF_THE_FRAME


def test_the_display_default_is_inside_the_frame() -> None:
    assert len(CENTRE_OF_THE_FRAME) == 2
    assert all(0.0 <= value <= 1.0 for value in CENTRE_OF_THE_FRAME)


@pytest.mark.parametrize(
    "fraction", [(-0.1, 0.5), (0.5, 1.1), (float("nan"), 0.5), (float("inf"), 0.0)]
)
def test_a_fraction_outside_the_frame_is_refused_as_an_argument(tmp_path, fraction):
    """Checked before any file is read, so it is an argument fault and nothing else."""
    with pytest.raises(ArgumentRefusal):
        draw(tmp_path, "any-study", tmp_path / "out", probe_fraction_rc=fraction)


# --- negative: what it must NEVER do -------------------------------------------------------


def test_catching_an_argument_refusal_never_catches_a_corruption_signal() -> None:
    """The defect this closes: `main()` caught plain ValueError, so a saved-array digest
    mismatch and a malformed receipt exited 2 as a usage error — telling the operator they
    mistyped a flag when the saved run was corrupt."""
    assert issubclass(ArgumentRefusal, ValueError)
    assert not issubclass(ValueError, ArgumentRefusal)
    with pytest.raises(ValueError) as raised:
        raise ValueError("saved_array_digest_mismatch")
    assert not isinstance(raised.value, ArgumentRefusal)


def test_a_missing_run_is_not_reported_as_an_argument_refusal(tmp_path) -> None:
    """A receipt that is not there is a state fault, not a mistyped flag, so it propagates."""
    with pytest.raises(OSError):
        draw(tmp_path / "absent", "any-study", tmp_path / "out")
