# Design

## The decision this change rests on, and its two corrections

**The claim.** Every stage is *total over a missing predecessor*: input absent → a named code, still
rendered, never a failure and never a default. That is already the project's law (*a missing reading
is silence, never a negative*), and it is what lets the stages be built in parallel.

**Correction one, from both second readers independently** (`readings/breadth-first-mvp-fable.md`,
`readings/breadth-first-mvp-codex.md`): totality buys **wireability, not buildability**. Fable:
*"abstention only covers a predecessor that is absent, not one whose record shape is unsettled."*
Codex: *"totality alone does not settle coordinate systems, identifiers, support representations, or
overlap rules."*

So the change is split by **whether a stage's record shape is settled**:

| shape settled → build the content | shape unsettled → build an honest shell |
|---|---|
| lenses, bundles, predicates, output, **ownership** | **relations, until its pairing is constructed** |

A shell runs, returns a named absence saying *why* (not merely *that*), and renders a frame that
shows it. That is the MVP for a stage whose contract would otherwise be written from a guess.

**Revised 2026-10-12, and the two halves came apart.** The founder ruled that an interstice is
defined between two `<object>`s — *"a resolvable sub-set of the visual field"* — and not between two
role-bearing objects, so **identity was never the blocker**. The lead then wrote in task 1.3 that
relations was therefore constructible "from the facing-pair graph the boundary census already
computes". **That claim is false**, and the section below says why in source terms. So:

- **`ownership` moves to settled.** Every place claimed by one `<object>` or named `unassigned` is
  `interiors.labels` read directly: a non-zero label is a claim, a zero inside the available field is
  the residual. No identity, no new record shape, no construction. It becomes thin and real.
- **`relations` stays a shell for one more step**, not because of identity but because the pairing it
  needs is a complete interstice construction, not merely a touching-pair census.
Later sampled dark pairs are now retained as a candidate; the shell still constructs
no extent and is not connected to that candidate as a construction consumer.

**Correction two.** The proposal's earlier claim that an end-to-end run "proves every wire" is false,
and Codex gives the counterexample: *"a disconnected predicates stage that always returns twelve
abstentions produces the same final file."* The wires are evidenced by `just graph` showing nothing
dangling, `just imports` holding the layer contract, and ledger telemetry — never by the artifact.

## Why relations still needs a construction step — confirmed in source 2026-10-12

**This survives the founder's `<object>` ruling untouched, because it is not about identity.** The
lead re-read `interiors.py` whole on 2026-10-12 and Fable's claim holds: `boundary_edges` does
`regions.append(labels[rows, cols])` — the territory's **own** label — and reads the neighbour only
to decide *that* a place is an edge and of which *kind*. The far side is not recorded.

**Sharpened the same day, by the sub-agent that wrote the shell, and the refinement matters.** Two
imprecisions in the lead's version: the neighbour is also read to *select* which places are edges
(`neighbor != labels`), not only to set a kind; and, more consequentially, **for a `peer_territory`
edge the neighbour's label *would* record the far side.** The record is only genuinely absent for the
pairs this stage actually wants — those bounded **across dark** — because `read_interiors` labels
only `interior = available & ~dark` and runs watershed with `mask=interior`, so across a dark band
the neighbour is a dark place whose label is **0**.

So the missing unit is not "store the far side". It is **construct the dark-bounded pairing**, which
is a different and harder operation. An interstice between two `<object>`s is constructible **in
principle** today and is **not a lookup**; writing relations before that construction exists would
write a contract that changes under its feet.

The plan said relations' "places between" were *all already measured*. They are not. Fable:

> "the pairs the thesis cares about are bounded **across dark**, i.e. precisely the pairs that are
> **not** touching under the current definition."

The census's touching pairs are watershed-adjacent, and the interior excludes dark, so two
territories separated by a dark cortex are not a touching pair at all. Worse, the far side is not
recorded: `boundary_edges` keeps `labels[rows, cols]`, the territory's **own** label, and uses the
neighbour's label only to set the edge kind. **A bracketed profile does not record the territory it
reached**, so dark-bounded pairing is a construction, not a lookup. Building relations now would
write a contract that changes under its feet.

## The absence vocabulary has a hard ordering before every stage

Fable: *"If each stage coins its own codes, the dependency graph passes vacuously while the codes do
not compose."* So one shared vocabulary is declared first, and it must distinguish at least:
predecessor **absent**; predecessor **present but empty**; predecessor present and **this item
unread**. Those are three different silences and collapsing them loses the distinction the project
runs on.

## The lenses MVP, and the one thing it may not claim

The static middle is settled — a pair of edges at the terciles of a structurally selected population,
both edges in the 0 row (`chapters/03-lenses/teachings.md`). The knee's **local structural
normalisation is the founder's and is not given**. The MVP therefore reads the terciles of the
series' own foreground, which `RegimeKey.terciles` already computes, and records
`normalisation: none`. It is a real reading against the image's own distribution — which is what
defeats scanner scaling — and it is honest about the correction it does not apply.

Task 2.1 replaces the old `digits.digit_code` shape (a witness middle plus a spread band) with
low/high edges first; that correction is independently settled and blocks nothing.

## The output file, which is the one place the epistemology meets a foreign schema

A confidence column cannot carry silence. Fable: without conditions it is *"a constant wearing a
prediction's shape."* Three, each a contract rather than advice: the abstention value is declared
in the spec **before CSV emission** and may never be chosen by reference to a score or a label; the
companion record of named codes is written **in the same run**, so the submission is derivable from
the codes and never the reverse; and the ledger records that every row abstained.

**Founder correction, 2026-10-12:** "I don't know, that should resolve experientially, when actually
running and seeing it in action". Named decisions run, record and render without a numeric
projection. That inspection precedes its declaration; CSV emission is refused while it remains
undeclared. This supersedes the earlier requirement to declare it before any run.

## What ports, and what never could

The founder, 2026-10-11, on how the thesis is built:

> "every section is basically an *idea* in computer vision. Not a thesis about what a cell is, but
> *how* an object is resolved, with the objects being resolved in that specific chapter being cells"

So each section is a **general mechanism**, and the cell-tracking build is that mechanism
*instantiated* on one kind of object. **What ports is the idea; the instance's content was never
portable at all.** A thing that "fails to port" is therefore not a problem with the port — it is a
sign that the instance's content was mistaken for the mechanism. Three cases already measured, each
read the right way round:

| the instance's content, which never ported | the idea, which does |
|---|---|
| loops close by construction, because marching squares runs on a filled mask | a border is read from the data's own shape — and the knee's shape is an unordered edge set, so its border must be **built**, which is a different operation for the same idea |
| the allowance is the flicker of the light over how steeply it falls | a border is known no more finely than its instrument — and the knee has **no** allowance reaching the object stage, so the idea is unsatisfied and must not be faked |
| the oval round two centres, because a nucleus is roundish | a shape prior is applied **as a pull, never imposed** — bone's prior is its own (radial growth, straight where straight), and is not the oval |

`AGENTS.md` law 5 is the same rule in its enforceable form: existing code is reused only where a
chapter argues it is the best approach, and the argument is recorded in the chapter.

## Delegation

Units whose shape is settled are written by a sub-agent against a strict spec; the lead keeps the
contract, the intent tests, the survivor judgments, the wiring and the telling. A body lands only
with its certificate and after the lead has read it (`AGENTS.md` law 8). A sub-agent never weakens a
test to make code pass, never judges a Detective survivor, and never writes an equivalence note.

**Execution continuation, founder instruction 2026-10-12:** "Make sure you update the openspec
contract, then continue the mechanized build process that I outlined with my prompts and our
conversation earlier this session". Sonnet over the Anthropic API and local sub-agents remain
mechanical workers under the boundary above. Each packet names its declared task, settled input
and output shape, allowed files and direct intent tests. The lead records the body review and
the exact verification standing before admission. An engineering refusal keeps the affected unit
open; it neither becomes a pass nor changes the design. Independent declared work can continue.
For unsettled units such as 1.3a, establish the support contract first; delegation never supplies it.
