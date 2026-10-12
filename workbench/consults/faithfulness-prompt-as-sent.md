READ-ONLY. Do not run any command and do not read any file. Answer from this text alone.

You are a second reader on a classical-AI computer-vision project. You are one independent voice,
never a verdict. You may report a provable error with its proof, or ask a question. You do not
propose the design: the design belongs to the project's founder, whose words are quoted below and
outrank every reading of them, yours and mine.

# The project, and the one thing you must not get wrong

RSNA Knee Abnormality Detection: 12 binary findings per knee MRI study, macro-averaged ROC-AUC.

**There is no machine learning in the architecture, by thesis and not by preference.** No CNN, no
transformer, no fitted weight, no learned embedding, no "small learned component". If your reading
concludes a model is needed anywhere, you have misread something — say which passage misled you,
because that is itself a finding. The words "Kaggle", "vision", "AUC" and "competition" fire an ML
prior; they do not license it.

The architecture: resolve every element of the knee significant to its operation as an `<object>`;
construct the relations between them; read each of the twelve findings as a **predicate violation**
on an object or a relation. An interstice (the space between two bones) is **constructed, not
detected** — it exists the moment its two bounding objects do, which is why the compartments cannot
be missed. Recognition is mechanical: a knee is a fixed anatomy, so identity follows from invariant
relations and no stored case is consulted during the parse.

# The founder's words, verbatim — the oracle of intent

These are six prompts from 2026-10-11, in order. Everything I ask you about is downstream of them.

**22:31 — the hardware.**
> "I will rate objects when shown as an actual image I can use for visual reasoning. But for now,
> the thing I want to do is build the basic hardware of the <object> thesis, sufficient to enable
> us--following some direct guidance with domain-knowledge, fluid-intelligence oracle, PI-undergrad
> work--to assign meaning to the tooling's output as annotated/processed visual data. THe point here
> is to get all the tooling functioning to make this a properly-instantiated pipeline as designed,
> as outlined by the <object> thesis. The hardware part, the pre-AI stuff."

**22:38 — breadth first.**
> "Actually, breadth first. Recovering context is the expensive part. I can afford to spend tokens,
> but a fluid intelligence oracle is expensive to maintain. You just need data centers and
> electricity and token budgets, I need food and sleep and for the vibes to not be off, which is a
> lot harder. So since I've invested the time to get you set up to be aligned properly, which was
> EXPENSIVE, let's build wide. I can get to the refinement of the baseline functional pipeline when
> it actually EXISTS, and each step can put out a non-stupid image, even if it's not actually good
> quality."

**22:48 — sub-agents, bounded.**
> "You can have these sub-agents code up one small piece and ensure it's wired and registered and
> pinned according to a stric contract of design. Then when they finish, you hold authority over all
> the code planning and high-level progress tracking and functionality and wiring, etc, with me to
> guide it properly. Sub-agents for boring and literal stuff that already has an established shape,
> an established place in the clean production pipeline, an established implementation oracle in my
> words, the <object> thesis, and the actual working instantiation of the thesis (ideation and
> creative inspiration, not literal 1-1 porting) in the cell tracking project."

**23:21 — the thesis IS the plan.**
> "This is a thesis of a type of *machine intelligence*, not a pile of scripts. That's why I wrote
> the thesis that way. The cell tracking and this knee project are completely different projects.
> Yet they are both perfectly coherent expressions of the thesis. Each section of the thesis isn't
> about the engineering of some random piece, it's an exploration of an idea, a concept."
>
> "Section 6--Borders, is about how once an object is identified meaningfully, its role assigned,
> then its exact boundaries and borders can then recursively be refined *given* such assignment."
>
> "Section 12 is an expansion beyond even where this project requires--once first-order <object>
> recognition is finalized, how this then leads to expansions to arbitrary operations *on* those
> objects, like tracking the position of cells in a whole movie (note--this knee project stops at
> recognition, so this part is literally extra!)."
>
> "I talked about the ENTIRE thesis, which was ENTIRELY about tracking the positions of cells...but
> I never once said a word about cells or biology at all. The thesis is *general*, the worked example
> is simply one build out of many possible builds. That's why the thesis IS the answer AND the plan
> for this knee project."

**23:28 — the failure the scaffold exists to prevent.**
> "I'm SUPER cautious about this, because agents like you tend to tunnel-vision when there's a hard
> problem, and build out a mountain of code in one arbitrary spot, one function at a time, and sort
> of lose the thread of *why* the code exists, *where* it sits in a greater project pipeline. That
> makes it impossible to work, since there isn't an actual working pipeline, just functionalities in
> islands, entire unto themselves. And it makes efficiency terrible, since things computed for one
> step are completely forgotten about and re-computed from scratch for an entirely different step.
> My hope is that a proper code organization/planning process that contracts the role of every
> folder, every module, every script that's not otherwise archived out or shelved, so it has a place
> and is resolved properly as part of a greater system that works in concert with the others."

**23:46 — the scaffold, built once, and its properties.**
> "We should build the scaffold of the project once, cleanly, correctly. Everything linked to how the
> full pipeline will consume it, the math/compute being done in each step, how it's meant to be fit
> in with the others, what it does, its output (including compute that can be shared/optimized/used
> to calculate one path efficiently, with the proper efficiencies of C++/Rust/JIT/etc, that can
> produce as many outputs as needed as efficiently as possible), a visual output that shows the
> actual reasoning process on images themselves to demonstrate visual reasoning, the orchestration of
> the thesis stages, how each module is set up to do one thing (SICP-style), with what it needs to
> import and put out, the most atomic functions that would be able to perform such an operation, the
> intent and negative specification contract for its behavior, and useful hardware and reasoning that
> isn't module specific, can serve as whole-project global tools that might be useful for other
> processes, etc. Sounds good? I know that's a lot, we can mechanize a decent amount of this work
> with sub-agents or a workflow or something. But this needs to be done properly, cleanly, so that
> new sessions can work without losing the plot."

# What was actually built against those words

**The route** (nine stages), with state computed today, not recalled:

| stage | produces | state |
|---|---|---|
| study | files to series, whole at stored fidelity | built, renders |
| field | regime key, noise law, variance-stabilising transform, physical frame, squint | partly, renders |
| lenses | per-place readings across acquisitions, as ternary digits | not built; UNREACHED by the route |
| objects | the knee's significant elements | partly, renders |
| relations | interstices per facing pair: gap, walls, fill, contents | not built; unreached |
| ownership | every place owned; residual pulled out | **no package exists at all** |
| bundles | each object's profile: banks and rows, as row counts | not built; unreached |
| predicates | the twelve, each on its subject | not built; unreached |
| output | twelve confidences, with the kept record behind them | not built; unreached |

Measured: 83 modules, 29 reached from the production route, 7 declared on the route and reached by
none of it, 3 renderers against 12 route stages.

**A place registry.** `docs/places.json` declares, per module: `where` it sits (a route stage /
beside the route / the drawing layer / the second-tier workbench / a project verb / shelved), whether
it carries a compute contract (a boolean), a one-sentence `role`, and whether it runs its work on
import. `scripts/places.py` computes the observed state against it and reports `undeclared`,
`absent`, `unreached`, `misplaced`, `contract_disagrees`, and the count of roles nothing can check.
It deliberately does not gate, on the stated grounds that a stage being built is unreached for as
long as it is being built, and a gate there would teach the next session to misdeclare place to go
green. All 83 roles are now written, each from a reading agent that read the module whole.

**The declared breadth-first change**, in order:
- §0 the scaffold, before anything is delegated: the registry; both compute-contract idioms taught to
  the check; all roles written. Open: a structural check that every reference/twin pair declares a
  compute contract; adding `renders` to the registry.
- §1 the route and the vocabulary, the lead's own and first: replace the route table with the nine
  stages; declare one shared absence vocabulary distinguishing three silences (predecessor absent /
  predecessor present but empty / item unread); give `relations` and `ownership` honest shells that
  run, return a named absence saying why their record shape is unsettled, and render a frame showing
  it.
- §2 lenses, delegable: one balanced-ternary digit per place per acquisition against a **pair of
  edges** (low and high, both belonging to the middle row) read from that series' own distribution;
  silence kept distinct from the middle digit; wired and rendered as a three-colour digit map.
- §3 bundles, delegable: an object's profile as **row counts** over named banks, with a bank this
  build cannot write carried as a named unavailable status and never as rows of zero, because a zero
  count asserts a reading was made and found nothing.
- §4 predicates and output, delegable: the twelve as named decisions over the subjects the object
  model gives them, each returning the abstention code with a reason naming what was not resolved;
  a submission serialiser plus a companion record of codes and reasons written in the same run.
- §5 run every stage over one study through the real entry point, save the image series, then the
  founder inspects it. That inspection is stated as the point of the whole change.

**Binding constraints on all of it.** No stage record, code or picture may carry an anatomical name,
or assert that a reading is a particular tissue, or mark an element as an admitted object; a record
schema may not hold a field whose values are anatomical names. A stage is not "built" until it
renders, and a renderer may only ARRANGE values the stage already computed — one that has to measure
is evidence against the stage. Every stage must be total over a missing predecessor, returning a
named code rather than raising, and may never substitute a default, a zero or a neighbouring reading.
Every numeric kernel carries a compute contract naming its reference and proof gate; a plain
reference exists before any accelerated twin, and the twin is admitted only where codes, assignments,
memberships, ties and decisions match. Pure decisions return named codes, are total over their
arguments, and every bar they read is an argument rather than a constant.

**Contour refinement is parked**, on the grounds that his §6 refines borders only once an object's
role is assigned, and the work had been running on watershed territories carrying index numbers and
no role at all.

# My own reading, written before I open yours

Faithful: breadth over depth is the declared shape; §6 explains the parking structurally rather than
by hunch; §12 being out of scope means the unbuilt stages are not omissions; a spec forbids naming
anatomy, which is a mechanical guard on the founder's stated worry that I find signals that vibe and
assign a label; the sub-agent boundary is narrow and written down.

Not yet faithful, and I think this is the substance: his 23:46 prompt names about fourteen properties
per module and the registry declares four. Unclaimed by any per-module declaration: how the pipeline
consumes it, the compute in the step, its interface to its neighbours, its output, **shared
compute**, the language choice, its atomic decomposition, its import/export surface, its intent and
negative contract. Some have mechanical homes already (the compute contract carries reads, writes,
allocation, work, parallel unit, language, reference, proof gate; a dependency graph shows a value
nothing consumes as dangling; a layer contract holds imports; the two-sign loop supplies intent and
negative tests) — but only six modules carry a compute contract and nothing checks that the ones
that should, do.

Sharpest: **the specific failure he named has no check.** "Things computed for one step are
completely forgotten about and re-computed from scratch." A telemetry ledger exists whose stated job
includes what was recomputed; it is off by default and not wired through the route. So that
inefficiency is currently unmeasured.

# The four questions, and please answer these rather than grading the plan

1. **Does the breadth-first pass as specified actually deliver 22:31's purpose** — "sufficient to
   enable us to assign meaning to the tooling's output as annotated/processed visual data" — or does
   it deliver 22:38's letter while missing it? Its end state is twelve abstentions and one picture per
   stage, and a picture of a named absence is not something meaning can be assigned to. If that gap
   is real, what is the smallest change that closes it without assigning meaning on his behalf?

2. **Is there a §6 trap inside §3?** The bundles stage writes "an object's profile — the bundle of its
   places". But `objects` today resolves **territories carrying index numbers**, not objects with
   assigned roles. Is a profile over a roleless territory the same category of error as refining a
   border over one — §6 run before its own precondition — or is it admissible because a profile is a
   measurement record and the spec forbids deriving identity or resemblance from it? Give your
   reasoning, not a verdict.

3. **The fourteen properties.** Is declaring the missing ten per module in a registry the right move,
   or is a registry of that size a documentation layer that will drift, with the mechanical checks
   being the only durable answer? Where exactly is the line between a property worth declaring and a
   property that should only ever be computed?

4. **Shared compute.** What would actually catch "computed for one step and re-computed from scratch
   for another", as a mechanical check rather than a discipline? Name the check and what it would
   have to read.

Answer in prose with your reasoning shown. Mark clearly what you take as established from the text
above, what you infer, and what you cannot determine from it. Where you did not or could not
consider something, say so rather than implying it is absent.
