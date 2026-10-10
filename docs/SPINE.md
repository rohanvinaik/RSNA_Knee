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

No sub-agents or workflows for the reasoning. The design is the founder's (`AGENTS.md`, law 9): the lead tells
what it understands and what it measured, and asks.

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

## Resuming after the compaction of 2026-10-10 (written at the founder's word, before it)

- Chapter 1 (`study`) is built and committed (361c519): `open_corpus`, `read_study`, every series whole at
  stored fidelity, named codes for every zero. Measured: none of the 58 labeled studies is all-normal (1 to 9
  positive findings each), and Kaggle's kernel lacks a JPEG Lossless decoder (no shipping until the work is done).
- Chapter 2 (`collapse`) is being taught. His words so far are in `src/knee/collapse/__init__.py`. He said what
  August built is not to be recapitulated; the thesis is the design source.
- Exact next steps:
  1. Re-read, whole: this file; `AGENTS.md`'s opening section; `src/knee/collapse/__init__.py`; and in
     `~/Projects/Kaggle_Killer/competitions/cell_tracking/docs/pipeline_thesis/paper/v7_parts/`: `03_collapse.md`
     (§4), `04_structure.md` (§5: stage 0's four lenses and the composite, stage 1 the black by seniority, stage 2
     the bodies), and `01_information.md` (§1; read whole in consecutive parts: lines 1–703, 704–1406, 1407–end;
     §1.3 the squint, §1.4 the change, §1.8 a reference and its difference, §1.11 wide and narrow lenses,
     seniority, concurrence, §1.12 yes/no/nothing said, §1.14 decide or abstain).
  2. Done after the compaction (2026-10-10): his request "read that stuff first, come back with your
     interpretation and understanding for how this informs the build" was answered, and he answered the tell's
     questions. His answers are in `src/knee/collapse/__init__.py`: what "black", "speck" and "lens" mean, the
     joint line as the knee's normalization flag, the platonic knee as the superposition of the 58's normal
     parts, and that the competition's labels stand.
  3. Build Chapter 2 only on his go, one step at a time. Record each new teaching in the stage's docstring as it
     comes.

## Where things live

- `src/knee/<stage>/`: the build. Each package's docstring carries the figure's text for its stage, and the
  knee's version once the founder has given it.
- `tests/`: the tests, Detective's generated suites among them.
- `data/raw/`: the competition's files, in Kaggle's own layout (gitignored).
- `archive/`: everything from before 2026-10-10, under its old path.
- The project verbs: `just test`, `just lint`, `just types`, `just gate`, `just detective <verb> …`,
  `just detective-resolution`.
