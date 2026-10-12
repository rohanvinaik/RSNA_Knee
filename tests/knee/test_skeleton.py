"""The packages are the object model's route (docs/OBJECT_MODEL.md), not Figure 8 transcribed.

The founder settled the structure on 2026-10-11: a finding is a predicate violation on an object, or
on a relation between objects. The build is ordered by the knee's own anatomy, so Figure 8's stages
with no knee analogue were archived and the knee's own were added.

Five more were archived on 2026-10-12 at his ruling -- "Begone, Satan! ... I'd rather lose work and
have to re-do it than have you be constantly confused when you encounter old things we haven't
structured properly." Four of them (loop, candidates, cleanup, every_object) held Figure 8 roles the
object model folds into `objects` and `ownership`; `assignment` is recall-routed and belongs to the
diagnosis stage, which this project does not reach (SS12, out of scope).
"""

import importlib
import pkgutil

import knee
import knee.pictures

# Below the route: project-wide layers every stage may stand on. Not stages; they know no knee.
# Split out of knee.collapse on 2026-10-11 (founder: "got thrown into that junk pile instead of
# being organized properly").
FOUNDATION = ("compute", "telemetry")

# The route a study takes, in order. Each stage consumes the one below it.
ROUTE = (
    "study",  # files -> series, whole at stored fidelity
    "collapse",  # the field: regime, noise law, physical frame, the squint
    "lenses",  # every place, every acquisition, one ternary digit per row
    "objects",  # the <object>s resolved from geometry, and SS6's refinement of their borders
    "relations",  # interstices CONSTRUCTED between facing <object>s
    "ownership",  # every place claimed or named unassigned; its picture is the residual map
    "vectors",  # every place in one language: the bundle (SS7, SS13)
    "predicates",  # the twelve, each on its named subject
    "output",  # twelve confidences, with the kept record behind them
)

# Beside the route, consulted by any stage. `memory` and `expert` are the diagnosis stage's recall,
# which is deliberately NOT part of the object parse (founder, 2026-10-11: "we should be able to
# isolate the components of the knee with NO recognition, pure math").
BESIDE = ("memory", "expert", "agencies", "record")

# Not a stage: the drawing layer, which imports stages and is imported by none, so it can be switched
# off without the run noticing (SS13.7).
BESIDE_THE_FIGURE = ("pictures",)

EXPECTED = (
    frozenset(ROUTE)
    | frozenset(BESIDE)
    | frozenset(BESIDE_THE_FIGURE)
    | frozenset(FOUNDATION)
)

# Archived 2026-10-11 for having no knee analogue, each a checkable external fact: an anchor is a
# time point resolved in full and a knee study is a still; "following through time" likewise; bones
# do not divide. They are under archive/src/knee/, dug from if a role is ever found for them.
#
# Archived 2026-10-12 at the founder's ruling, for having no stage in the settled route: loop,
# candidates, cleanup and every_object fold into `objects` and `ownership`; `assignment` is recall,
# which belongs to diagnosis. Losing their work was explicitly accepted rather than worked around.
ARCHIVED = frozenset(
    {
        "anchor",
        "following",
        "division",
        "loop",
        "candidates",
        "cleanup",
        "every_object",
        "assignment",
    }
)


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


def test_a_stage_is_not_built_until_it_renders() -> None:
    """A stage that cannot show its work is not finished.

    The founder, 2026-10-11: "image output of each stage should be a requirement. Again, visual
    reasoning, computer vision." So the requirement is enforced here rather than remembered: a stage
    may claim `built` or `partly` in ROUTE only if `knee.pictures` carries a module of its name.

    This is the one-way dependency stated in knee/pictures/__init__.py -- pictures import stages and
    no stage imports pictures -- so this test reads the renderer names, never calls them.
    """
    from knee.pipeline import ROUTE

    renderers = frozenset(
        module.name for module in pkgutil.iter_modules(knee.pictures.__path__)
    )
    claiming = {stage for stage, state in ROUTE if state in ("built", "partly")}
    missing = sorted(claiming - renderers)
    assert not missing, (
        f"these stages claim to be built but render nothing: {missing}. "
        "Either the stage draws what it resolved, or ROUTE says not_built."
    )


def test_no_stage_imports_the_drawing_layer() -> None:
    """Deleting `knee.pictures` must not change a single reading the pipeline makes (SS13.7)."""
    for name in sorted(EXPECTED - {"pictures"}):
        module = importlib.import_module(f"knee.{name}")
        source_root = module.__path__[0]
        for found in pkgutil.walk_packages([source_root], prefix=f"knee.{name}."):
            submodule = importlib.import_module(found.name)
            imported = getattr(submodule, "__dict__", {})
            offenders = [
                key
                for key, value in imported.items()
                if getattr(value, "__module__", "").startswith("knee.pictures")
                or (getattr(value, "__name__", "") or "").startswith("knee.pictures")
            ]
            assert not offenders, f"{found.name} imports the drawing layer: {offenders}"
