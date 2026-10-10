"""The skeleton follows Figure 8 of *What an <Object> Is* (§2.8): one package per stage."""

import importlib
import pkgutil

import knee

# Figure 8's line, named for the thesis's ROLES. The sibling's <object> is a nucleus and the knee's
# is a bone, so `cell_assignment` and `every_cell` were renamed: a package named for the instance
# breaks the law that the thesis's terms are roles (founder, 2026-10-10).
FIGURE_8 = frozenset(
    {
        "study",
        "collapse",
        "loop",
        "candidates",
        "vectors",
        "cleanup",
        "assignment",
        "every_object",
        "anchor",
        "following",
        "division",
        "output",
        "memory",
        "expert",
        "agencies",
        "record",
    }
)

# Not a stage of the figure: the drawing layer, which imports stages and is imported by none, so
# it can be switched off without the run noticing (§13.7).
BESIDE_THE_FIGURE = frozenset({"pictures"})


def test_the_packages_are_the_figure_8_stages() -> None:
    found = {m.name for m in pkgutil.iter_modules(knee.__path__) if m.ispkg}
    assert found == FIGURE_8 | BESIDE_THE_FIGURE


def test_no_package_is_named_for_the_cell_instance() -> None:
    """The project's own law: the thesis's terms are roles, never the cell instance's content."""
    found = {m.name for m in pkgutil.iter_modules(knee.__path__) if m.ispkg}
    assert not [name for name in found if "cell" in name], found


def test_each_stage_imports_and_carries_its_figure_text() -> None:
    for name in sorted(FIGURE_8):
        module = importlib.import_module(f"knee.{name}")
        assert module.__doc__, name
