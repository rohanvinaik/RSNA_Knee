"""The packages are the object model's route (docs/OBJECT_MODEL.md), not Figure 8 transcribed.

The founder settled the structure on 2026-10-11: a finding is a predicate violation on an object, or
on a relation between objects. The build is ordered by the knee's own anatomy, so three of Figure 8's
stages were archived for having no knee analogue, and three of the knee's own were added.
"""

import importlib
import pkgutil

import knee

# The route a study takes, in order. Each stage consumes the one below it.
ROUTE = (
    "study",  # files -> series, whole at stored fidelity
    "collapse",  # the field: regime, noise law, physical frame, squint; and today the objects
    "lenses",  # every place, every acquisition, one ternary digit per row
    "relations",  # interstices constructed between facing objects
    "loop",  # the residual pulled out, round by round, until nothing significant is unassigned
    "candidates",  # resolved, not yet called
    "cleanup",  # the residual read once more
    "vectors",  # every place in one language: the bundle (SS7, SS13)
    "every_object",  # the completeness check
    "predicates",  # the twelve, each on its named subject
    "output",  # twelve confidences, with the kept record behind them
)

# Beside the route, consulted by any stage. `assignment` and `memory` are the diagnosis stage's
# recall, which is deliberately NOT part of the object parse (founder, 2026-10-11: "we should be able
# to isolate the components of the knee with NO recognition, pure math").
BESIDE = ("memory", "expert", "agencies", "record", "assignment")

# Not a stage: the drawing layer, which imports stages and is imported by none, so it can be switched
# off without the run noticing (SS13.7).
BESIDE_THE_FIGURE = ("pictures",)

EXPECTED = frozenset(ROUTE) | frozenset(BESIDE) | frozenset(BESIDE_THE_FIGURE)

# Archived 2026-10-11 for having no knee analogue, each a checkable external fact: an anchor is a
# time point resolved in full and a knee study is a still; "following through time" likewise; bones
# do not divide. They are under archive/src/knee/, dug from if a role is ever found for them.
ARCHIVED = frozenset({"anchor", "following", "division"})


def _packages() -> frozenset[str]:
    return frozenset(m.name for m in pkgutil.iter_modules(knee.__path__) if m.ispkg)


def test_the_packages_are_the_object_model_route() -> None:
    assert _packages() == EXPECTED


def test_no_package_is_named_for_the_cell_instance() -> None:
    """The project's own law: the thesis's terms are roles, never the cell instance's content."""
    found = _packages()
    assert not [name for name in found if "cell" in name], found


def test_the_archived_stages_are_gone_from_the_build() -> None:
    """A stage with no knee analogue is not carried as an empty promise in the production path."""
    assert not (_packages() & ARCHIVED)


def test_each_stage_imports_and_carries_its_role() -> None:
    for name in sorted(EXPECTED):
        module = importlib.import_module(f"knee.{name}")
        assert module.__doc__, name
