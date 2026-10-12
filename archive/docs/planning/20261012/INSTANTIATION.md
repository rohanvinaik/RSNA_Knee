# The instantiation: each thesis section, and what builds it here

<!-- The join that neither docs/THESIS_AS_IDEAS.md (what each section IS) nor docs/OBJECT_MODEL.md
(what the knee IS) holds on its own: section -> stage -> package -> computed state -> what it owes.
Written 2026-10-11. Provenance per row: [F] the founder's words, [T] a thesis section as he mapped
it, [D] a project document, [M] measured this session, [I] the lead's inference, labelled as such. -->

> **State in this file is a SNAPSHOT and is not authority.** Recompute it: `just unit` prints the
> route and `just places`; the numbers below were computed 2026-10-11 and go stale the moment a
> stage lands. Where this file and a command disagree, the command is right.

## The one-sentence claim

**A finding is a predicate violation on an object, or on a relation between objects** [D
`OBJECT_MODEL.md`]. Resolve every element of the knee that matters to its operation and the twelve
findings are read off by arithmetic. Nothing is searched for.

The founder, 2026-10-11 [F]: *"if you actually CAN resolve objects, then 'visual reasoning' is
basically common sense + math"* — and the reason it is not statistics: *"the mapping to diagnoses
here isn't just statistics, it's literally recapitulating the exact process that a
doctor/radiologist would themselves be using for THEIR diagnosis."*

## Why the thesis is the plan, and the cell build is not the template

The founder, 2026-10-11 [F]: *"This is a thesis of a type of machine intelligence, not a pile of
scripts. … Each section of the thesis isn't about the engineering of some random piece, it's an
exploration of an idea, a concept."* And: *"I talked about the ENTIRE thesis, which was ENTIRELY
about tracking the positions of cells… but I never once said a word about cells or biology at all.
The thesis is general, the worked example is simply one build out of many possible builds. That's
why the thesis IS the answer AND the plan for this knee project."*

So: **a section is an idea; the cell build is that idea instantiated on one kind of object.** The
instance's content was never portable — only the idea. A thing that "fails to port" is a sign the
instance's content was mistaken for the mechanism [D `THESIS_AS_IDEAS.md`].

## The join

| § | the idea, as he stated it [F] | what instantiates it here | state [M] |
|---|---|---|---|
| **2** | object-oriented reasoning on visual data | not a stage — it is the architecture: the route's shape, the tiers, the twelve-as-predicates table [D `OBJECT_MODEL.md`] | settled |
| **3** | how the domain constrains the problem space, making reasoning inherent once the `<object>`s are resolved | `knee.study` — what we are shown, at stored fidelity: series, slices, geometry (LPS), the tables, the decoders. Plus the domain's own laws: knee imaging is highly structured, the patient is told not to move, the joint line is a giant normalisation flag, and the twelve define the domain (*"If it's not one of the 12, then to me it doesn't exist"*) | **built**, renders |
| **4** | constraint appearing in the COMPUTE as well as the logic; dimensions pinned in isolation | `knee.collapse` — the field: the regime key, the noise law per series, the variance-stabilising transform, the physical frame, the squint. KneeDiff is the knee's collapse; the collapsed axis is the **population** (n=58, so ~7.6x SNR [D `design.md` §math]) | **partly**, renders |
| **5** | how meaning is assigned to visual data purely deterministically | `knee.objects.interiors` — the dome re-derived for bone: a bone is not an emitter, it is a solid bounded by dark cortex, so it is **deepest** at its centre. The distance transform replaces brightness as the height field, and prominence — never a level — keeps the law that nothing is cut on strength, so a thin bone is never silenced by a thick one | **partly**, renders |
| **6** | *"once an object is identified meaningfully, **its role assigned**, then its exact boundaries and borders can then recursively be refined **given** such assignment"* | **nothing yet, deliberately.** Contour refinement was being attempted on roleless watershed territories — §6 run before its own precondition. Tasks 3.8-3.12 of `object-resolution-toolkit` are **parked**, and re-enter after identity | parked |
| **7** | the clean interface between raw pixels and classical deterministic reasoning; his own idiomatic HDC design | `knee.lenses` (one balanced-ternary digit per place per acquisition, against a **pair of edges** at the terciles of a structurally selected population, both edges in the 0 row) and `knee.vectors` (the bundle: scale x lens, plus relational and provenance banks, as row counts). A tissue class is a **conjunction of rows across acquisitions**, never a threshold on one image | **not built**; both **unreached by the route** |
| **8** | the complete requirement for a faithful classical AI on visual data, neither brittle nor expensive | `knee.memory` — the memory and its buckets. **Deferred by his ruling**: *"we should be able to isolate the components of the knee with NO recognition, pure math"*; recall arrives at diagnosis | beside the route, not built |
| **9** | the teaching regime for classical AI training | `knee.expert` — the expert's calls become cases. Also diagnosis-stage | beside the route, not built |
| **10** | unlike ML's overfitting ceiling, a classical approach gets *smarter, better and cheaper* on things outside its stored experience | the residual pull-out: *"the roles that are still unassigned in the visual field are a lot easier to figure out, since they're definitionally NOT the things you already DO know how to resolve."* Belongs to the `ownership` stage | **no package exists** [M] |
| **11** | the Society of Mind — the domain's structure comes back to shape the agencies | `knee.agencies` and `knee.record`: each agency marked where it acts; truth by concurrence; the committee looks downwards. No Popery | beside the route, not built |
| **12** | operations *on* resolved objects — tracking, following, division | **OUT OF SCOPE**: *"this knee project stops at recognition, so this part is literally extra!"* The five `shelf` packages and the retired `following`/`division` belong here | out of scope |
| **13** | the raw mechanics: the math, the HDC, the literal way to build it | `knee.compute` (`ComputeContract`, `handed_on`) and `knee.telemetry` (the ledger) — plus the whole engineering standard: language by computation shape, reference-then-twin through SAME, §13.5 contracts as data **without a wrapper**, §13.7 measurements and decisions and orchestrations kept apart | beside the route, built |
| **14** | the thesis spitballed across other domains | the existence proof that the knee is one instantiation among many — and the reason the cell build's *content* was never portable | settled |

## The structure the findings are read off

[D `OBJECT_MODEL.md`]

- **T1 objects** — the elements, resolved from the data's own geometry. Bones first, because the rest
  is defined against them: femur, tibia, patella, fibula, each with its sub-objects, and for each:
  cortex, subchondral plate, marrow.
- **T2 relations (interstices)** — one per facing pair, **constructed, never detected**. *"Interstitial
  space… is the space between the two bones we resolve as objects! That's LITERALLY what the term
  means."* [F] This is the load-bearing move: it kills the compartment problem, because medial,
  lateral and patellofemoral are *enumerated by which bone surfaces face each other* and so cannot
  be missed. A relation carries its gap, its walls, its fill and its contents.
  **A wall is cartilage backed by a subchondral plate — not bone**, so the OA predicate reads the
  cartilage thickness profile and not the gap.
- **T3 spans** — attached to two bones and running **outside** the interstice between them. The MCL
  is the scored instance: extra-articular, not interstitial content.
- **T4 the envelope (the capsule)** — larger than the union of the interstices, since it includes the
  suprapatellar recess. It carries a volume, a lining and an outline.

## What every stage owes, whatever it computes

[D `STAGE_CONTRACT.md`] Three first-order requirements, **equal in rank**, settled 2026-10-11 [F]:
*"the competition itself scores for efficiency, so that's a first-order consideration, alongside the
image output and clean modular production-spec design."*

1. **The picture** — `ENFORCED`. A stage is not `built` until it renders, and a renderer may only
   **arrange** values the stage already computed. One that has to measure is evidence against the
   **stage**.
2. **Performance engineering** — a `ComputeContract` per kernel naming its reference and proof gate;
   language by computation shape; a plain reference before any accelerated twin, admitted only by
   the decision-preserving SAME harness; structlog and OTel; measured with the named instruments and
   never a one-off profile.
3. **Clean, modular, production-spec** — one stage consumes only the stage below it; measurements,
   decisions and orchestrations kept apart; nothing deleted; every array states shape, dtype, axis
   order, units and frame.

## The breadth-first build, and why it is this shape

The founder, 2026-10-11 [F]: *"Actually, breadth first. Recovering context is the expensive part. I
can afford to spend tokens, but a fluid intelligence oracle is expensive to maintain… I can get to
the refinement of the baseline functional pipeline when it actually EXISTS, and each step can put out
a non-stupid image, even if it's not actually good quality."*

And what the build is **for** [F]: *"If the build is correct, if the pieces are all there and wired
and are processing the images correctly, then I can assign meaning to the output and provide creative
ideas, clever fluid-intelligence inspired hacks to perform structural reasoning on this visual data.
But I need the literal pieces built and wired and specc'd out and detective two-sign pinned and
telemetry tracked, etc before I can do that properly."*

So the MVP's job is **the hardware** — the pre-AI part — sufficient for him to assign meaning to
annotated visual output. It is declared as `openspec/changes/every-stage-renders/`, and the two
second readers corrected one claim in it: totality over a missing predecessor buys **wireability**,
not buildability, which is why `relations` and `ownership` get honest shells rather than content.

**§6 is also why breadth-first is the right call** [I]: it reaches identity sooner, and border
refinement becomes well-posed instead of being attempted on an object that does not yet exist.

## The failure this scaffold exists to prevent

The founder, 2026-10-11 [F]: *"agents like you tend to tunnel-vision when there's a hard problem, and
build out a mountain of code in one arbitrary spot, one function at a time, and sort of lose the
thread of why the code exists, where it sits in a greater project pipeline. That makes it impossible
to work, since there isn't an actual working pipeline, just functionalities in islands, entire unto
themselves. And it makes efficiency terrible, since things computed for one step are completely
forgotten about and re-computed from scratch for an entirely different step."*

His remedy, in his words: *"a proper code organization/planning process that contracts the role of
every folder, every module, every script that's not otherwise archived out or shelved, so it has a
place and is resolved properly as part of a greater system that works in concert with the others."*

That is `docs/places.json` and `scripts/places.py` (`just places`). Every module declares **where** it
sits, whether it carries a **contract**, and its **role**; the check computes the observed state
against it and reports `undeclared / absent / unreached / misplaced / contract_disagrees`, plus the
count of roles nothing can check. It deliberately **does not gate** (`justfile` 100-103): *a stage
being built is unreached for as long as it is being built, and a gate there would teach the next
session to misdeclare place to go green.*

## What a sub-agent may build, and what it may never touch

His authorization, 2026-10-11 [F]: *"Sub-agents for boring and literal stuff that already has an
established shape, an established place in the clean production pipeline, an established
implementation oracle in my words, the `<object>` thesis, and the actual working instantiation of the
thesis (ideation and creative inspiration, not literal 1-1 porting) in the cell tracking project."*
And: *"you hold authority over all the code planning and high-level progress tracking and
functionality and wiring, etc, with me to guide it properly."*

| a sub-agent MAY | a sub-agent NEVER |
|---|---|
| write the body against the spec | the contract |
| write the renderer | the intent tests |
| write the serialiser | a bar |
| | a Detective survivor's verdict or its equivalence note |
| | a change to a test to make code pass |

A body lands only with its certificate and **after the lead has read it**. A reading agent is a
**miner**: it reads named units whole and returns facts with locations and verbatim quotations, says
what it did not look at, and offers no judgement. Information flows downward only.

## What is still the founder's to rule

Recorded so none of it is quietly invented. Each is a question of **policy or meaning**, not fact.

1. **The abstention value written into the submission.** The `abstaining-findings` spec says it
   *"SHALL be an argument declared in this specification before any run"* — and no requirement in
   that spec names it [M]. Under Law 4 a bar is written before the run it judges.
2. **The two compute-contract idioms** (`CONTRACT = …` at module level, `@contracted(…)` on the
   kernel). Both are compliant — `contracted` attaches to `function.__dict__` and returns the
   function **unwrapped**, so §13.5's "never a decorator on the hot path" is satisfied [M,
   `contracts.py:26-32`]. The open question is which a new kernel's author should use.
3. **Whether the study stage owes compute contracts.** Seven files, zero contracts, in the stage that
   decodes every pixel of every series (`slices.py:28`) [M].
4. **The five `shelf` packages** — `loop`, `candidates`, `cleanup`, `every_object`, `assignment`:
   keep, archive, or fold.
5. **`AGENTS.md` law 9's** *"Nothing is built. No codebase meets the design"* — written 2026-10-02,
   now false, and in the first document a new session reads.
6. **The chapter's open bars** [D `design.md`]: the change level in population sigmas; the coverage
   count below which a place abstains; the concurrence tolerance in standard errors; the
   quiet-population share; the smallest region that must survive the squint.
7. **The knee's local structural normalisation.** His ruling settled the *ordering* and the tercile
   mechanism, not the normalisation itself; the record holds that the coil's S/I falloff is
   **multiplicative** on signal, so the sibling's additive haze does not port [D `03-lenses`].
8. **Valleys or terciles** for a multimodal series, and **values or digits** into the stack.
9. **The anatomical inventory** — which elements, and what warrants each name. Stated *before* any
   round is run against it.
10. **`docs/provenance/` vs the chapter's `readings/`**: the project `CLAUDE.md` routes Codex
    transcripts to the first, `SPINE.md` puts the record in the second.

## Structural gaps the scaffold surfaced

All measured 2026-10-11, all recorded rather than silently patched.

- **`ownership` has no package at all**, though the route table names it and task 1.3 asks for its
  shell. `just places` reports the declared set and the filesystem set as identical with no absences,
  so this is an omission and not a drift.
- **Three renderers against twelve route stages** (`study`, `collapse`, `objects`), where the stage
  contract wants one per stage, named for the stage. Task 0.4 makes it structural.
- **Seven stages declared on the route and reached by none of it** — lenses x3, relations, vectors,
  predicates, output. *That number IS `every-stage-renders`*, and it goes to zero as the change lands.
- **Twelve modules do their work on import** — the seven `workbench/measure` probes and five of the
  `workbench/render` scripts — none with a `main()` or an `if __name__` guard, and
  `object_toolkit_geometry.py` writes a measurements file merely by being imported.
- **`structure.py:29`** declares `air_by_connectivity(plane, seed_quantile=0.5)` and never uses
  `seed_quantile`; a caller passing it is silently ignored.
- **The saved B1 and B2 runs recompute as `unverified_or_stale`**: their arrays and receipts are
  intact, but every source, writer, serialiser and verifier digest has moved.
