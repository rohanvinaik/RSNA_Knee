# What each section of the thesis IS — the founder's own map

His words, verbatim, 2026-10-11. **This is the highest-value page in the project for grounding**,
because it says what the thesis is *for*, which no amount of reading its mechanisms recovers on its
own. Read it before reading any section of the thesis, and before porting anything from the
cell-tracking build.

> **For what each section actually BUILDS here, read `docs/INSTANTIATION.md`** — the join this page
> does not carry: section → stage → package → computed state → what it owes, with every open ruling
> that is the founder's listed rather than invented.

> "This is a thesis of a type of *machine intelligence*, not a pile of scripts. That's why I wrote
> the thesis that way. The cell tracking and this knee project are completely different projects. Yet
> they are both perfectly coherent expressions of the thesis. Each section of the thesis isn't about
> the engineering of some random piece, it's an exploration of an idea, a concept."

> "**§2 — Vision: What an \<Object> Is**, is about defining the concept of object-oriented reasoning
> on visual data.
>
> **§3 — The World Under the Microscope**, is about defining how the domain being visualized is used
> to constrain the problem space and make reasoning inherent following deterministic resolution of
> the \<object>s of semantic significance.
>
> **§4 — Collapse**, is about how the constraints of a structure-based approach allow constraint to
> appear not only in the logic of the space, but also in the compute requirements of a computer
> vision pipeline, as such structure allows dimensions to be interpreted and pinned in isolation.
>
> **§5 — The Structure: Stages 0 to 4**, etc, is an explanation of the mechanics of how meaning is
> assigned to visual data purely through deterministic systems.
>
> **§6 — Borders**, is about how once an object is identified meaningfully, its role assigned, then
> its exact boundaries and borders can then recursively be refined *given* such assignment.
>
> **§7 — Hypervectors**, goes into the mechanics of how visual data is encoded in a clean interface
> that allows direct linkage between raw pixel/visual data and classical deterministic reasoning,
> with the specific, idiomatic hypervector design of the project as my own invention for this use
> case; the missing substrate for classical approaches to rise again.
>
> **§8** is the kicker, it reveals how all this serves as the complete requirement for a genuinely
> faithful classical AI approach that works on visual data without being brittle or expensive.
>
> **§9** is the teaching regime for classical AI training.
>
> **§10** is about how unlike ML — which always has a ceiling of overfitting and is restricted to its
> training corpus as an accuracy/usefulness maximum — a classical approach can *learn* and seeing
> things *outside* of the parameters of its stored experience can actually make it *smarter*,
> *better*, and *cheaper*, not degenerate and weaker.
>
> **§11** goes into the way that a "Society of Mind" is built for a pipeline like this, how the
> structure of the domain space articulated earlier in the thesis comes back to influence design of
> the AI agencies.
>
> **§12** is an expansion beyond even where this project requires — once first-order \<object>
> recognition is finalized, how this then leads to expansions to arbitrary operations *on* those
> objects, like tracking the position of cells in a whole movie (note — this knee project stops at
> recognition, so this part is literally extra!).
>
> **§13** goes into the raw mechanics, the math, the HDC, the literal way the thing can be built.
>
> **§14** REALLY hammers this by spitballing the whole thesis in different domains."

> "I talked about the ENTIRE thesis, which was ENTIRELY about tracking the positions of cells… but I
> never once said a word about cells or biology at all. The thesis is *general*, the worked example is
> simply one build out of many possible builds. **That's why the thesis IS the answer AND the plan for
> this knee project. It's a solved problem, with direct evidence and articulation.**"

## What this settles, and what it changes

**It settles the porting rule at its root.** A section is an *idea*; the cell build is that idea
instantiated on one kind of object. So the instance's content was never portable — only the idea
was. A thing that "fails to port" is a sign the instance's content was mistaken for the mechanism
(`openspec/changes/every-stage-renders/design.md` carries the worked cases).

**It settles the scope.** §12 is operations *on* resolved objects — tracking, following, division.
**This project stops at recognition**, in his words, so §12 is out of scope and the route's upper
stages are not missing anything.

**It changes one thing in the plan, and the change is real.** His §6:

> "once an object is identified meaningfully, **its role assigned**, then its exact boundaries and
> borders can then recursively be refined **given** such assignment"

Refinement **presupposes a resolved object with an assigned role.** This project has been attempting
contour refinement on *territories* — watershed regions with no role assigned at all. That is §6
applied before its own precondition, and it predicts exactly the walls that work hit: no movement
allowance reaches the stage, no ordered chains exist, and one territory carried 38 edges that were
every one a watershed decision with zero measurements. Those are not defects to engineer around; they
are what §6 looks like when run before identity.

The sibling agrees when read this way: its outline is pulled taut on a **body** the structure has
already resolved, and its clean-up and last look refine **after** assignment, never before.

So the order the thesis gives is: resolve and assign, *then* refine the border recursively. Which is
also why the breadth-first build is the right call — it reaches identity sooner, and border
refinement becomes well-posed instead of being attempted on an object that does not yet exist.

## On the oracle itself

> "The problem of a human fluid intelligence oracle is that it's rather flaky and random. Here I was
> trying to get you to start mindlessly building with sub-agents, but instead I decided to talk about
> the ENTIRE thesis because the vibes were right."

Which is the argument for the contract tooling in one sentence: the plan has to survive the oracle
being unavailable, and the OpenSpec changes, the pins and the telemetry are what hold it between
these conversations.

> "We might not even need the AI part of this, because this problem is STUPIDLY easy compared to
> tracking the position, movement, and division of every cell and ONLY cells from a confluent plate.
> If the build is correct, if the pieces are all there and wired and are processing the images
> correctly, then I can assign meaning to the output and provide creative ideas, clever
> fluid-intelligence inspired hacks to perform structural reasoning on this visual data. But I need
> the literal pieces built and wired and specc'd out and detective two-sign pinned and telemetry
> tracked, etc before I can do that properly."
