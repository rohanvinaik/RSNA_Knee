# Consult: a breadth-first MVP for a classical-AI computer-vision pipeline

READ-ONLY. Answer from this text alone. Do not run any command, read any file, or search. Mark
anything this text does not determine as **undetermined** rather than filling it in. Separate what
follows from the stated mechanism from your own inference, and label the latter as yours.

## The architecture, so you do not import the wrong prior

A **classical-AI, no-machine-learning** pipeline for knee MRI: twelve binary findings per study.
There is no model, no fitted weight, no learned embedding, and none is wanted — that is the thesis,
not a limitation. Nothing may be tuned to a label or a score. Every bar is written down before the
run that judges it. A decision returns **named codes**, never a bool. A missing reading is
**silence, never a negative**. If your answer's load-bearing step is "fit", "train", "calibrate on
the data" or "choose the threshold that separates the classes", it is wrong here — say what
deterministic or measured quantity would do the job instead, or say none would.

The governing claim: **a finding is a predicate violation on an object, or on a relation between
objects.** Resolve the knee's elements as objects and the twelve are read off them by arithmetic.
An interstice is **constructed, not detected** — it exists the moment its two bounding objects do.

## The decision that has just been taken, and the question

The project lead proposed finishing one stage properly (depth-first). The founder chose
**breadth-first**, in his own words:

> "Recovering context is the expensive part. I can afford to spend tokens, but a fluid intelligence
> oracle is expensive to maintain. You just need data centers and electricity and token budgets, I
> need food and sleep and for the vibes to not be off… let's build wide. I can get to the refinement
> of the baseline functional pipeline when it actually EXISTS, and each step can put out a
> non-stupid image, even if it's not actually good quality."

> "build the basic hardware of the \<object> thesis, sufficient to enable us — following some direct
> guidance with domain-knowledge, fluid-intelligence oracle, PI-undergrad work — to assign meaning to
> the tooling's output as annotated/processed visual data. The point here is to get all the tooling
> functioning to make this a properly-instantiated pipeline as designed."

So: **mechanism now, meaning later.** He rules on objects only when shown an actual image he can
reason over. No stage may name anatomy, admit an object, or decide that a reading means a cortex.
Every bar a stage reads is an **argument, never a constant**.

## The route, as it reports itself today

```
study            built        renders
collapse         partly       renders
lenses           not_built    NO RENDERER
objects          partly       renders
relations        not_built    NO RENDERER
loop             not_built    NO RENDERER
candidates       not_built    NO RENDERER
cleanup          not_built    NO RENDERER
vectors          not_built    NO RENDERER
every_object     not_built    NO RENDERER
predicates       not_built    NO RENDERER
output           not_built    NO RENDERER
```

Those stage names are **transcribed from the thesis's system figure and are superseded**. The
settled structure is: study · field · lenses · objects · relations · ownership · bundles ·
predicates · output. Correcting the route is an open, declared task.

## What the machinery actually does today, measured this week

Established by reading each production unit whole:

- Bones are resolved as **territories**: a watershed on the negative Euclidean distance transform of
  the imaged interior, seeded by prominence markers. A bone is *deepest* at its centre where a
  nucleus is *brightest*, so the distance transform replaces brightness; prominence, never a level.
- The **interior excludes dark**: it is the finite places above the series' background split. So a
  divide between two territories exists only where the interior is *connected across*.
- **One 2D plane per series**, the middle slice. Nothing is volumetric.
- The noise law is **per-series scalars**; nothing in the object stage consumes any noise figure, so
  **there is no movement allowance in the pipeline at all**.
- A boundary interface carries **two independent typings**: what lies *across* it (`low_signal`,
  `peer_territory`, `acquisition_missing`, `frame`, `unseeded_available`) and what a profile cast
  across it *found* (`bracketed`, `no_dark_bracket`, `multiple_brackets`, `missing_profile`,
  `frame_clipped`, `empty_profile`, `invalid_measurement`). A position is set only where they agree.
- **There are no ordered chains**: the stage returns an unordered set of directed interface points.
- Measured on one study, five series: of all directed interfaces, **22–41% actually bracketed a
  position**, while 68–92% merely have dark across them. One territory had 38 edges, every one a
  watershed decision, and zero measurements.

## The plan to be judged

**The architectural claim it rests on: every stage must be TOTAL over a missing predecessor.** If a
stage's input is absent it returns a named code and renders an honest empty frame; it never fails and
never substitutes a default. This is already the project's law. The claim is that it is what makes a
breadth-first build possible: stages become independently buildable and simultaneously wireable,
because none depends on another being *good* — only on another being honest about being *absent*.

Per-stage MVP:

| stage | the MVP record | the MVP picture |
|---|---|---|
| lenses | one ternary digit per place per acquisition against the **series' own tercile edges**, which the regime key already computes | the three-colour digit map per acquisition |
| objects | territories + the boundary census + ordered contour chains | arcs in the colour of their warrant |
| relations | per touching pair, the constructed interstice: divide sites, relief, the places between — all already measured | the interstice drawn between two territories |
| ownership | every place assigned to a territory, an interstice, background, or **unassigned**; the residual reported | the ownership map, residual visible |
| bundles | per object, its profile as row counts over the banks writable today | the count table |
| predicates | the twelve, each a named decision over its subject, returning **abstained** everywhere | a twelve-row table, every row abstaining with its reason |
| output | twelve confidences per study in the submission's schema, all at the abstention value | the written file, validated against the sample submission |

The claim about the top of that table: **an all-abstaining `predicates`/`output` pair is not a
failure but the honest baseline.** A pipeline that reaches the end and abstains on all twelve
*exists*, proves every wire, and matches the project's epistemology; every later increment turns one
abstention into an assignment **with a warrant**.

On the lenses stage: the static middle is settled as a pair of edges at the terciles of a
structurally selected population, but the knee's **local structural normalisation is the founder's
and is not given**. The MVP therefore reads the terciles of the series' own foreground with no
spatial correction and records `normalisation: none`.

Each MVP unit still gets the full discipline: declared in a spec before code; a pure total decision
returning named codes; PEP 316 contracts; two-sign intent tests; mutation convergence with every
survivor judged; a symbolic contract check; wired into the production route so something consumes
it, with a dependency graph showing nothing dangling; a compute contract and ledger telemetry; a
renderer that only *arranges* values the stage computed; and a run on real data through the real
entry point.

## The questions

1. **Is "total over a missing predecessor" sufficient** to make these stages independently
   buildable, or is there a pair among them with a real ordering dependency that abstention cannot
   paper over? Name it concretely if so.
2. **Is an all-abstaining predicates/output pair honest**, or does writing a submission-shaped file
   of abstentions create a false artefact? What would make it honest if it is not?
3. **For the bundles stage**, the thesis's banks are the voxel, the 16×16 neighbourhood, the lens,
   the plate, the dome link, the ring, the lenses' conversation, and how the object came out. Given
   what the pipeline measures today, which are honestly writable and which would be fabrication?
4. **Must the route's rename precede everything**, or can stages be built against the settled names
   while the route is corrected in parallel? What breaks either way?
5. **Where does this plan hide a week?** Name the stage whose "non-stupid image, even if not good
   quality" is far more expensive than it looks, and why.
6. **What must this MVP refuse to do**, so that building wide does not quietly assign meaning the
   founder has not given? State each as something a contract can forbid, not as advice.

Answer each in order. You are one independent voice and never a verdict: you may report a provable
error with its proof, or ask a question, but you do not propose a redesign of the project.
