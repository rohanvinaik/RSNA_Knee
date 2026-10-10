# The spine: the knee, built chapter by chapter on Figure 8

<!-- Loaded in every session through CLAUDE.md (`@docs/SPINE.md`); AGENTS.md points here. The plan and the way
of working, in the founder's words where they exist. No state is written here: it is read from the code (each
stage package's docstring says whether the founder has given the knee's version) and from git. -->

## What this project is

A classical-AI computer-vision system for RSNA Knee Abnormality Detection: for each knee MRI study, a confidence
for each of 12 findings, scored by macro-averaged ROC-AUC. There is no machine learning in the architecture. It
instantiates the computer-vision thesis *What an \<Object> Is*, whose whole system is drawn in its Figure 8
(§2.8), and it is built from that figure, one stage at a time. The founder, 2026-10-10:
- "Set up a project structure that basically lets us build the high-level structure laid out by that ASCII
  diagram in the thesis. Then I'll walk you though every step, explaining everything along the way."
- "We need to build something like it here. That includes a lot of the literal mechanics, the workflow, but also
  some things need to be ripped out or changed up. So I'm going to guide you through this step-by-step."
- "the "spine", the step-by-step chapters of the project from the thesis that this computer vision project will
  instantiate and that I will walk you through, and the PI-Undergrad workflow, driven with the thesis and the
  cell-tracking project as an oracle that we'll use to work this project out"

## How we work: the PI–undergrad pass

The founder's words, 2026-10-10 (the first group recorded in memory `feedback_pi_undergrad`):
- "I'm the PI, you're the undergrad … Every time there's a decision to make, or a problem, something that's just
  not making the math math properly, your normal instinct is to try and solve it quickly. Bad instinct. *I* am the
  domain expert, and I KNOW that the idea is complete and correct. If you're having problems, it's because you're
  missing something. Your task is to work through what I
  told you, then when you can't make things fit together, to think through the problem using simple, clear
  language and reasoning in the language of the domain space, then present the apparent incongruity in the
  theory."
- "I need to control and manually guide the assertions you make, the ways you think through the information
  theory of it all. Sub-agents and workflows are easier, but it lets you work unbounded and direct your own
  understanding and interpretation, which is just not rigorous enough engagement with the premises of the
  problem."
- "a valid lens is ALWAYS correct. It is never wrong. Not because its magical, but because it is defined only to
  be a measurment"; ""Silence" is meaningful, not a default negative score"; "Domain errors are also utterly
  fatal."
- "I guess..we go in order? The PI-UNdergrad pass, you tell, I teach?"
- "any time you doubt what I'm saying, you think i'm on something, you want proof before you validate what seems
  to be an extreme case of AI psychosis on my part, I will give it to you. I will explain it thoroughly … But
  please, don't build ML crap because it seems "better". You don't know what will work better. I do. And I
  promise I'll explain, but you have to actually engage, ask me if you doubt, work out problems with me, don't
  just assume."

Each chapter, in order:
1. **Read the oracle for the stage, whole**: its sections of the thesis, and how the cell-tracking project built
   it (below). `archive/` is dug from as needed; it is never the plan.
2. **Tell**: say in plain words what the thesis stage does, what the cell-tracking build of it does, and what
   the knee brings to it. Facts are measured, and labelled as measured. What does not fit is put to the founder
   as a question in the domain's terms; it is never settled with a number, a threshold or a quick fix.
3. **The founder teaches**: what carries over, what is ripped out, what changes, and why. When the lead doubts,
   it asks for the explanation; it never steers toward a smaller claim.
4. **Record**: the stage package's docstring states the knee's version, with his words quoted and dated, in place
   of "The knee's version: not yet given by the founder."
5. **Build** it to work ("Most important is to make the code actually work, to be built"), under the house's
   engineering in `AGENTS.md`.
6. **Verify** through the real entry point and adversarially; pin pure decisions with `just detective`; run
   `just gate` before every commit.

No sub-agents or workflows for the **reasoning**. The design is the founder's (`AGENTS.md`, law 9): the lead tells
what it understands and what it measured, and asks.

## The working loop (founder, 2026-10-10)

His words: "the workflow you should be using is to work it out with fable/codex and ground on truth with cheap
agents mining on the text/advisors on questions you need to solve. I can guide where needed, but this is a nice,
clean workflow loop you've been using, I'd like to persist it."

**Two oracles, each with its own way in.** Both are truth; neither is opinion.

| oracle | what it settles | how it is read |
|---|---|---|
| the thesis, *What an \<Object> Is* | theory, explanation, why a thing is the way it is | **read** — whole sections, by a mining agent where the section is long |
| the cell-tracking build | literal engineering, what was actually done | **symbolically traced** — Serena `find_symbol` / `find_referencing_symbols`, then the unit read whole |

**The loop, in order:**

1. **Hit something uncertain.** Say so rather than resolving it with a plausible guess.
2. **Ground on the oracles.** Launch a cheap mining agent at the thesis, or trace the sibling build symbolically.
   A miner returns facts with locations and verbatim quotations, and no judgement. It says what it did not look
   at. Its facts are checked against the founder's words before they become premises.
3. **Work it out with Fable and Codex.** Write the lead's own reading to the chapter's `readings/` *before*
   opening either answer. They are second readers, never warrant (law 9): they may report a provable error with
   its proof, or ask a question. Agreement reached independently is evidence; disagreement is a question for the
   founder.
4. **Call the advisor** on the question itself — before a multi-file plan locks, when the same failure returns
   twice, and before declaring work done.
5. **Measure, on the real corpus, through Chapter 1's entry point.** A stage that has only seen synthetic data is
   not built. Run it over the 58 and read the table before building the stage above it.
6. **Record to the chapter's folder before the next step** — a reading to `readings/`, a measurement to
   `measurements/`, and the chapter's `README.md` kept current — so a compaction costs one unit, not the session.
7. **Tell the founder**: the mechanism as read, what was measured, and where the lead is still uncertain.

**What never delegates:** the synthesis, the interpretation, the telling, and every judgement. A miner informs
the lead of facts; it never tells the lead what the founder is asking, what a thing means, or what to build.

### The founder's place in the loop, which is not the end of it

He is **not** a terminus the loop reports to. He is the one who **corrects a misframing**, and nothing else in
the loop can do that job:

- a **miner** returns what the text says, but cannot know the lead asked the wrong question;
- **Fable and Codex** reason *inside* the framing they are handed, so a bad frame comes back elaborated;
- the **advisor** reads the same transcript, so it inherits the same blind spot.

His words, 2026-10-10: "I am the one that guides misunderstandings, like your 'pleural effusion brightness' issue
that you were stuck on."

**The worked case.** The lead concluded a level map was impossible, because on a fluid-sensitive sequence the
brightest tissue is fluid, so any bright anchor would normalize away the finding. That was reported as a genuine
incongruity. He answered: "confluent plates vs sparse plates obviously ALSO have the same global signal scale-up
issue, no?" — which named where to look and said the answer already existed. The loop then resolved it in one
pass. It could not have found that on its own.

**So the tell to watch for.** An apparent **blocker** is the signal. His law: "*I* am the domain expert, and I
KNOW that the idea is complete and correct. If you're having problems, it's because you're missing something."
And 2026-10-10: "if you simply trust that this IS a genuine implementation of computer vision, then problems like
that CAN'T be definitive blockers or unresolvable incongruities. **The answer *exists*.** We simply have to work
it out together."

When the lead's conclusion is that something cannot work, that conclusion is **evidence of a missing
understanding, never a finding**. It goes to him immediately — with the framing laid bare and the reasoning shown,
and **without a verdict attached**. "Here is where I am stuck and here is how I am framing it" — never "here is
why this is impossible."

The loop re-enters at step 2 once he has redirected it.

## The oracle: the thesis and the cell-tracking project

- **The thesis**, *What an \<Object> Is*:
  `~/Projects/Kaggle_Killer/competitions/cell_tracking/docs/pipeline_thesis/paper/what_an_object_is.md` (the
  current copy; `archive/docs/canon/what_an_object_is.md` is older, and its line numbers differ). Per its §2.8:
  §1 is the theory of information beneath the loop; §3 the world under the microscope and its laws; §4–§12 the
  system, one element at a time (§4–§6 carry H1, §7 H2, §8–§10 H3, §11–§12 H4); §13 the mechanics beneath the
  language and the memory.
- **The cell-tracking project**, the thesis built: `~/Projects/Kaggle_Killer/competitions/cell_tracking/`, its
  code in `src/cell_tracking/` (a map of it in `docs/CODE_MAP.md`). Where it built a stage is located when that
  stage's chapter opens. "Spine" here is the founder's casual word; this file does not follow cell tracking's
  `docs/BUILD_SPINE.md` (founder, 2026-10-10: "do NOT hinge on the "spine" document from cell tracking, I was just
  using a casual term").

## The corpus

The 58 labeled studies (founder, 2026-10-10: "We only need the 58 labeled studies. The advantage of a
classical/symbolic approach--if it works on a handful of cases, scaling up doesn't really add in much utility for
training. So the 58 are enough."). They are in `data/raw/train_series/`; at scoring, the hidden test studies
arrive in the kernel.

## The chapters

In Figure 8's order. The order after Chapter 1, and when the packages beside the line are built, are the
founder's to set. The sections are the ones Figure 8, its caption or §2.8's road map name for each stage's terms,
except Chapter 1's §3, which is the lead's reading.

| ch | package | Figure 8 | thesis sections |
|---|---|---|---|
| 1 | `study` | A MOVIE: the input. For the knee: the competition, its files, and the data points a study becomes | the world and its laws, §3 (the lead's reading) |
| 2 | `collapse` | THE COLLAPSE (the squint): in depth; in time | the composite §4.3; H1 §4–§6 |
| 3 | `loop` | THE LOOP, round by round (Figure 19) | the bodies §4.2; the cheap readings §5.1; the black §5.2; the footprint §5.4; the band §5.5; the halo §3.1; the site search and reaching down §5.6; the last look §5.7 |
| 4 | `candidates` | THE EMPTIED BOX; THE CANDIDATES | the emptied box §5.7; the footprint §5.4; the band §5.5 |
| 5 | `vectors` | THE VECTORS: every place in one language | §7 (a context §7.1); §13 |
| 6 | `cleanup` | THE CLEAN-UP, on the residual | §10 |
| 7 | `cell_assignment` | THE CELL ASSIGNMENT: recall routes each \<object> | the Scissors and out of focus §8.2 |
| 8 | `every_cell` | EVERY CELL | the count §3.4; §11 |
| 9 | `anchor` | THE ANCHOR RESOLVED | Figure 8 |
| 10 | `following` | FOLLOWING THROUGH TIME | §12: the static model §12.1, the guarantee and the Ephemeris move §12.4; the jiggle §3.2 |
| 11 | `division` | DIVISION | the dean §12.6 |
| 12 | `output` | THE OUTPUT. For the knee: the 12 findings per study | Figure 8 |
| beside | `memory` | THE MEMORY AND ITS BUCKETS | §8, §9 (the buckets §8.1, §9); §13 |
| beside | `expert` | THE EXPERT: calls become cases | Figure 8 |
| beside | `agencies` | the four agencies, each marked where it acts | §11 |
| beside | `record` | the kept record of findings, where the agencies meet | §11 |

## Where things live

- `src/knee/<package>/`: the build, one package per chapter. Its `__init__.py` docstring carries Figure 8's
  text for that stage, the knee's version in a paragraph, and a pointer to the chapter's record. It stays
  short: a docstring is not a notebook.
- **`docs/chapters/NN-<package>/`: the chapter's record. Read `README.md` there FIRST** in a new session or
  after a compaction. Each chapter folder holds:
  - `README.md` — where it stands: the chapter's task in one line, the mechanism as settled, what is built,
    what is **not** working with the traced reason, what is open and the founder's to rule, any claim
    withdrawn, and the chapter's own vocabulary.
  - `teachings.md` — the founder's words, verbatim and dated, in the order given. Never paraphrased.
  - `design.md` — the design, with provenance per element.
  - `readings/` — what the **oracles** say: the thesis read whole, the sibling build traced symbolically,
    and the second readers, each with the lead's own reading written **first**.
  - `measurements/` — what was measured on the **real corpus**, through Chapter 1's entry point.

  The readings are the oracle's; the measurements are the corpus's. A reading never substitutes for a
  measurement, and state stays computed from code, tests and git — these say what was measured and what it
  meant.
- `tests/`: the tests, Detective's generated suites among them.
- `data/raw/`: the competition's files, in Kaggle's own layout (gitignored).
- `archive/`: everything from before 2026-10-10, under its old path.
- The project verbs: `just test`, `just lint`, `just types`, `just gate`, `just detective <verb> …`,
  `just detective-resolution`.
