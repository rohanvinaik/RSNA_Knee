# The pipeline, start to finish

<!-- The complete system as one route a study takes. Loaded alongside SPINE.md, which carries the
plan and the way of working; this carries the SHAPE of the build. Written 2026-10-10, after the
founder's two-objects teaching settled what the knee's <object> is. -->

## What someone walking in should be able to do

Open `src/knee/`, read the package names in order, and see the thesis operating. Each package is
one stage of Figure 8, each takes the stage below it as given, and each is read without reading
the one above. That is the test this document is written against.

## The audit, and the one thing that fails that test

Everything outside `archive/` is clean and small: eight files at the root (`AGENTS.md`,
`CLAUDE.md`, `README.md`, `justfile`, `pyproject.toml`, `uv.lock`, `.gitignore`,
`.python-version`), two scripts (`ci_local.sh`, `detective_resolution.py`), sixteen stage packages,
tests mirroring the packages, and one chapter folder of records. Nothing is stray, nothing is
duplicated, the gate is one command.

**But five of the sixteen package names are cell tracking's CONTENT, not the thesis's ROLES**, and
that is the project's own stated failure mode (`feedback-terms-are-roles`; and the founder,
2026-10-10: "structure isn't something you can blindly apply. **It has to be re-derived for each
problem space.**").

| package | the problem | checkable fact |
|---|---|---|
| `division` | **bones do not divide** | a domain fact |
| `following` | "FOLLOWING THROUGH **TIME**" | a knee study is a still; Chapter 1 measured no temporal series |
| `anchor` | an anchor is a **time point** resolved in full | same |
| `cell_assignment` | the knee's `<object>` is a **bone**, not a cell | the founder, 2026-10-10 |
| `every_cell` | same | same |

The skeleton was transcribed from Figure 8 before the knee's `<object>` was known. Now it is known,
and the transcription shows. **This is the founder's to rule (law 9)** — the proposal is below, and
nothing is renamed until he says so.

## The route a study takes

Each row is one package. The left column is the thesis's role; the right is what it means here.

| # | package | the role (thesis) | the knee |
|---|---|---|---|
| 1 | `study` | **a movie: the input** | a study's files become data points: every series whole at stored fidelity, geometry per slice, named codes for every zero. **Built.** |
| 2 | `collapse` | **the squint**: reduce fidelity on purpose, warranted by a law, to get a resolvable starting ground | close the leg; read the superior–inferior axis from the header; find **two objects** — femur and tibia — by markers from anatomy; read **the seam** between them. **Partly built.** |
| 3 | `loop` | resolve objects round by round, taking each out with what its laws say it caused, and read the residual again | round 1 takes the two bones and the seam; the residual holds the patella, the fibula, and everything the first pass could not claim. Each round re-reads what is left. |
| 4 | `candidates` | **the emptied box**: what the loop produced, not yet called | each resolved object with its extent, its seam relations, and how it came out |
| 5 | `vectors` | **every place in one language** | each place written as balanced-ternary digits against its series' middles, in one carrier, so any two places can be compared exactly |
| 6 | `cleanup` | on the residual | what no round claimed, read once more against the record |
| 7 | `assignment` *(rename)* | **recall routes each `<object>`** | a resolved object is matched against confirmed cases; one answer standing is recalled, two are a disagreement kept, none is an abstention |
| 8 | `every_object` *(rename)* | the completeness check | is every object the laws require actually present? The per-slice N table says what to expect; a missing one is a reading |
| 9 | — | *the anchor resolved* | **no knee analogue as named.** An anchor is a time point. The role — "a unit resolved in full, against which the rest is carried" — may map to **the study's reference view**, but that is the founder's to say |
| 10 | — | *following through time* | **no knee analogue.** A study is a still. The role — "carry a resolved thing cheaply to where it was not resolved in full" — may map to **carrying a reading across slices of one stack**, but again his to say |
| 11 | — | *division* | **no knee analogue.** Bones do not divide |
| 12 | `output` | **the output** | twelve confidences per study, ordered so that a clear positive outranks a borderline one and a borderline outranks a confident absence |

Beside the line, consulted by any stage:

| package | the role | the knee |
|---|---|---|
| `memory` | the memory and its buckets | confirmed cases with their source, kept under a regime key so only like is compared with like |
| `expert` | calls become cases | the founder's rulings, including the hand re-grade of the labels' folded abstentions |
| `agencies` | the four agencies, each marked where it acts | the bodies that decide a finding by concurrence, or abstain |
| `record` | the kept record of findings | every decision with what was known before it, every abstention with its reason |

## How each module is built — the same five steps, every time

This is the SICP discipline the project runs on: each layer is built on the one below it, through
an interface narrow enough to state in a sentence, and nothing reaches past its neighbour.

1. **Read the oracle for the stage** — the thesis section, and the sibling build traced
   symbolically. Record both to the chapter's `readings/`.
2. **Tell the founder** what the stage does, what the sibling did, and what the knee brings. Put
   what does not fit to him as a question in the domain's terms.
3. **Record his teaching** verbatim in the chapter's `teachings.md`.
4. **Build it, in three kinds kept apart (§13.7):**
   - a **measurement** returns a number or a field, with its scope and provenance, and decides
     nothing;
   - a **decision** returns a named code or an abstention, is pure and total over its arguments,
     and every bar it reads is an **argument** rather than a constant inside it;
   - an **orchestration** moves values between stages and decides nothing.
5. **Verify through the real entry point:** `uvx ty check`, `just detective converge` on every pure
   decision, `just gate` before the commit, and **a run over all 58 studies** before the stage
   above it is started. A stage that has only seen synthetic data is not built — measured the hard
   way, when the noise law passed its unit tests and then concurred on 4 of 336 real series.

## The invariants, which hold at every stage

- **Decide or abstain; unknown is never false.** A decision returns a named code; a missing reading
  is silence, not a negative; a refusal is a verdict.
- **Nothing is deleted.** A stage's removals are decisions by readings entitled to make them, kept
  as records. Fill the mask, never the values.
- **No level is chosen to separate gold**, to match a prevalence, or to move a score. Every bar is
  an argument, written down before the run it judges.
- **A measurement is in named units** — millimetres, degrees, counts, or noise units — never in
  raw values whose meaning changes between series.
- **Reference first, twin second.** Every numeric kernel exists as a plain NumPy reference, pinned,
  before any accelerated twin, and the twin is admitted only by a decision-preserving harness.
- **Truth by concurrence.** A member measures one thing and knows no question; a body holds the
  signs; disagreement is kept, never averaged away.

## Built as of 2026-10-10

- `src/knee/pipeline.py` — the route, walking Figure 8's line in order, honest about its own state.
  `ROUTE` carries each stage's state; a stage counts as **built** only when it has run over real
  studies through Chapter 1's entry point.
- `src/knee/pictures/` — the drawing layer. One renderer per stage, importing stages and imported
  by none, switchable off. Its contract is the founder's test: **a picture should be basically
  free, and a renderer that has to compute something is evidence the stage is not reasoning
  visually.**
- `assignment` and `every_object` renamed from the cell instance to the role, with a test guarding
  that no package is named for the instance.

## What is open before chapter 3 can start

1. **The noise law's ruling** — three options are on the table (see `chapters/02-collapse/README.md`).
2. **The five package names**, above — his to rule.
3. **Chapters 9, 10 and 11** have no knee analogue as named. Either the role maps to something the
   knee does have, or the chapter is struck and Figure 8's row is marked "not instantiated here".
   Striking a row is a change to the founder's design and needs his word.
4. **The "black" / background clearance stage.** The founder, 2026-10-10: *"I do have to give you
   some guidance on the 'black'/background noise clearance stage, but the bones are REALLY good."*
   **His guidance is owed and the stage waits on it.** What is known so far: air by connectivity to
   the frame's border works cleanly and he called it "VERY clean"; the enclosed holes are not yet
   filled, and the gestalt prior he named is **closure** (§5.3's "contiguous, closed"); and four
   intensity instruments have failed, so the reading must be structural.
5. ~~**Promoting the scratchpad probes.**~~ **Done, 2026-10-10.** The eleven probes are in
   `workbench/` (`measure/` and `render/`, with the consultants' prompts in `consults/`), and
   `workbench/README.md` states the three tiers and exactly what the gate asks of each. The five
   render scripts had hardcoded the session scratchpad by its UUID, which made every recorded
   picture unreproducible the moment the session ended; they now write to `data/pictures/` through
   `_out.pictures_dir()`, gitignored because a rendered knee is pixels. What remains of this item:
   the *pure* panel-arranging keeps moving into `knee.pictures` as each stage's renderer settles,
   and the measuring is not yet behind a `just` verb.
