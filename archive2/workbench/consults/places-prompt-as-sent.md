# Consult: a place contract — every module declared, and the declaration checked

READ-ONLY. Answer from this text alone. Run nothing, read nothing else, search nothing. Mark what
this text does not determine as **undetermined**. Separate what follows from the stated mechanism
from your own inference, and label the latter as yours.

## The architecture, so you do not import the wrong prior

A **classical-AI, no-machine-learning** computer-vision pipeline for knee MRI. No model, no fitted
weight, none wanted — that is the thesis. A decision returns **named codes**, never a bool. A missing
reading is **silence, never a negative**. Every bar is written down before the run that judges it.
If your answer's load-bearing step is "fit", "train" or "calibrate on the data", it is wrong here.

## The thesis this project instantiates, in its author's own words

He wrote it as a thesis of **a type of machine intelligence, not a pile of scripts**. Each section is
an *idea*, not the engineering of a piece; the worked example (tracking every cell in a microscopy
movie) is one instantiation out of many, and the text never mentions cells or biology:

- §2 **Vision: What an \<Object> Is** — defining object-oriented reasoning on visual data.
- §3 **The World Under the Microscope** — how the domain being visualised constrains the problem
  space and makes reasoning inherent, following deterministic resolution of the \<object>s of
  semantic significance.
- §4 **Collapse** — how a structure-based approach puts constraint not only in the logic of the space
  but in the **compute requirements**, since structure lets dimensions be interpreted and pinned in
  isolation.
- §5 **The Structure: Stages 0 to 4** — the mechanics of how meaning is assigned to visual data
  purely through deterministic systems.
- §6 **Borders** — how, **once an object is identified meaningfully and its role assigned**, its
  exact boundaries can then be **recursively refined *given* such assignment**.
- §7 **Hypervectors** — how visual data is encoded in a clean interface linking raw pixels to
  classical deterministic reasoning.
- §8 — the complete requirement for a faithful classical-AI approach on visual data that is neither
  brittle nor expensive.
- §9 — the teaching regime. §10 — why a classical approach gets *better* on things outside its stored
  experience, where ML has an overfitting ceiling. §11 — how a "Society of Mind" is built for such a
  pipeline. §12 — operations *on* resolved objects (tracking, division); **this project stops at
  recognition, so §12 is out of scope**. §13 — the raw mechanics, the math, the HDC. §14 — the whole
  thesis in other domains.

Two consequences the author draws: **the instance's content was never portable, only the idea was**;
and **the thesis is both the answer and the plan** for this project, because it is a solved problem
with direct evidence.

## The problem to be judged

The author's stated fear, verbatim:

> "agents like you tend to tunnel-vision when there's a hard problem, and build out a mountain of
> code in one arbitrary spot, one function at a time, and sort of lose the thread of *why* the code
> exists, *where* it sits in a greater project pipeline. That makes it impossible to work, since
> there isn't an actual working pipeline, just functionalities in islands, entire unto themselves.
> And it makes efficiency terrible, since things computed for one step are completely forgotten about
> and re-computed from scratch for an entirely different step."

> "My hope is that a proper code organization/planning process that contracts the role of every
> folder, every module, every script that's not otherwise archived out or shelved, so it has a place
> and is resolved properly as part of a greater system that works in concert with the others"

So: two failure modes — **islands** (code with no place in the pipeline) and **recomputation** (a
value computed for one step, forgotten, recomputed for another) — and one hoped-for remedy, a
contract on the role of every folder, module and script.

## What the project already has

- A production route, one function that walks a study through the stages, with each stage's state
  reported honestly (`built` / `partly` / `not_built`) and a rule that a stage is `built` only when it
  has run on real data through the real entry point.
- A **development-only dependency graph** over the same production functions: **a value nothing
  consumes shows as dangling**.
- An **import-layer contract** checked by a linter, and unused-dependency and dead-code tools
  available.
- A **compute contract per kernel**, declaring: kind, language, what it reads, what it writes,
  allocation, work, parallel unit, its reference implementation, and its proof gate.
- A command that prints the build loop with the route's live state, and a declared-change tracker
  whose tasks are read live from their own checklists.
- A rule that a stage is not `built` until it **renders**, and that a renderer only *arranges* values
  the stage computed.
- Two tiers already separated: production source, and a second-tier workbench for probes and
  not-yet-production systems; everything older is archived.

**What nothing declares today:** per *module* and per *folder*, what its role is and where it sits.
So a new module can appear with no declared place and nothing notices; a module can stop being
consumed and nothing notices.

## The plan to be judged (the lead's)

**It must be a command that answers back, not a document.** In this project the loop was written down
three times and built against zero times; what changed behaviour was a planning tool printing 3/23, a
mutation checker refusing to call two survivors equivalent, a linter failing the gate, and an intent
test failing. Documents lose.

**A declared registry**, in the shape of a record the project already trusts elsewhere (a declared
environment file, plus a command that computes observed state against it and prints the next
command). Each folder and module under production source, the workbench and the scripts directory
declares: its **role** in one sentence; the **stage** of the route it belongs to (or *beside the
route*, or *workbench*); what it **consumes** and **produces**, by named record; and the **renderer**
that draws it where the stage contract requires one.

**A check that computes the observed state against it** and reports:

1. **undeclared** — a module exists with no entry (drift);
2. **declared but absent**;
3. **unreached** — a production module not reachable from the route's entry point (an island);
4. **unconsumed** — a produced record nothing reads;
5. **recomputed** — two compute contracts declaring the same `writes`, or two kernels reading the
   same source per study;
6. **unrendered** — a stage whose contract requires a picture and has none.

Run it inside the existing build-loop command and in the commit gate, so drift is **red**, not a note.

## The questions

1. **Does the registry earn its keep, or is it a second source of truth that will rot?** A stale
   registry may be worse than none. The lead's mitigation is that undeclared modules fail the check,
   so adding a module forces declaring it. Is that sufficient? What else rots, and what detects it?
2. **Is "unreached from the route's entry point" the right test for an island?** Name what it would
   wrongly flag and what it would wrongly pass.
3. **Is "two compute contracts declaring the same `writes`" a real detector of recomputation?** What
   does it miss, and what cheaper or sharper signal exists for "computed, forgotten, recomputed"?
4. **§6 says borders are refined only once an object's role is assigned.** The project has been
   attempting contour refinement on watershed territories that carry no role at all. Does that
   ordering error have a structural detector — something a check could catch — or is it only visible
   to a reader who knows the thesis?
5. **What in this plan is ceremony?** Name the part that will cost more than it catches.
6. **What should the registry refuse to contain**, so it stays a contract about *place* and does not
   become a second architecture document competing with the specs?

Answer each in order. You are one voice and never a verdict: report a provable error with its proof,
or ask a question; do not propose a redesign of the project.
