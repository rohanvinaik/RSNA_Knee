"""The skeleton follows Figure 8 of *What an <Object> Is* (§2.8): one package per stage."""

import importlib
import pkgutil

import knee

FIGURE_8 = frozenset(
    {
        "study",
        "collapse",
        "loop",
        "candidates",
        "vectors",
        "cleanup",
        "cell_assignment",
        "every_cell",
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


def test_the_packages_are_the_figure_8_stages() -> None:
    found = {m.name for m in pkgutil.iter_modules(knee.__path__) if m.ispkg}
    assert found == FIGURE_8


def test_each_stage_imports_and_carries_its_figure_text() -> None:
    for name in sorted(FIGURE_8):
        module = importlib.import_module(f"knee.{name}")
        assert module.__doc__, name
