# The audit: every change the book makes to the founder's design

## The rule, in his words (2026-10-02; `../../FOUNDING_PROMPTS.md`)

- "We have ZERO evidence of anyhting outside of pure theory. *I* am the authority on what works or doesn't. You don't
  understand the design. Something that LOOKs like it doesn't work well might actually be CRITICALLY important. You
  do not have the authority to change the design *I* built based on a random guess, when you don't know the intent"
- "Make SURE you are not changing anything other than that which is definitevely/provably correct, or warranted by
  my explicit words"
- "Not just this session--EVERY change to the original design"
- "there is LITERALLY not an actual functional codebase that meets the design intent"

## The original design

Unchanged since it was merged; the hashes match `REFERENCE_MANIFEST.toml`, checked 2026-10-02.

| document | commit | sha256 (first 16) |
|---|---|---|
| `docs/KNEE_ARCHITECTURE.md` (ARCH) | `f405450` "the knee-as-law design, layers 0-9" | `d913777da4425a3d` |
| `docs/THEORY_OF_THE_CASE.md` (THEORY; Laws 1–8 bind) | `88752f0` | `59e916c5400d3cba` |
| `docs/FOUNDING_RECORD.md` | `88752f0` | `46fdec436d11d567` |

Also part of it:
- `docs/canon/`;
- the founder's rulings quoted in `docs/canon/SESSION_BRIEF_2026-10-02.md` §3;
- his explicit words in `../../FOUNDING_PROMPTS.md`;
- his standing rules in the global and Kaggle_Killer instructions: No Popery, AI is not ML, the structure-first
  epistemology.

## How each change is classified

- **P, provably correct.** The row carries the proof, of one of these kinds:
  - logic or arithmetic;
  - an internal contradiction in the original, with both passages quoted;
  - an order of work that cannot execute, with the dependency named;
  - a checkable external fact: the competition's literal data and framing, or a file format's semantics. It is
    admissible as a fact and never as a warrant on design. The founder (23:22:50Z): "the competition's literal
    data and framing is acceptable, not implicit warrants on design or conception". So a fact can correct a
    statement of fact, and a design inferred from that fact is N.

  A judgment that something works better, or a prediction of how it will behave, is not proof.
- **W, warranted by his explicit words.** The row quotes them, with their source and time. His 15:24:53Z "your
  recommendations are generally in line with the intent" warrants no specific change. He confirmed this at
  23:22:50Z: "my warrant was general and high-level, not open authority". Codex had his "implicit authority on
  design … It was provisional", and a provisional authority is not run with.
- **N, neither.** The book returns to the original design's text. Where I see a problem in the original, it goes
  to him as a question with the argument beside it, and Codex's point too if there is one. It is never made as a
  change.

The book's engineering (how the design is built: languages, Detective, SAME, tests, the Mac Pro, the typist) is
in scope wherever it alters what the design does. Where it only implements, it is checked against his words on
engineering (15:24:53Z, 16:08:14Z, 17:22:59Z, 17:32:09Z).

## The inventory

### A. The review accord (THE_KNEE §2), ten changes

| id | the change, as THE_KNEE states it | the original it amends | class | proof or quote | action |
|---|---|---|---|---|---|
| A1 | Layer 1 is not the general substrate | ARCH Part 3 §3.3, §3.4 | — | — | — |
| A2 | patient-specific delineation | ARCH §1.5, §2.2 item 2, §2.10 | — | — | — |
| A3 | negative knowledge in three tiers | ARCH Table 1.7, §2.8 rule 3, §4.1, Table 2.8b, Table 5.10 | — | — | — |
| A4 | nested and overlapping objects; explanation records | ARCH §1.4, §2.2 (L1), §4.4, Table 4.6 | — | — | — |
| A5 | identity separated from conflict | ARCH §4.5; THEORY II.5 | — | — | — |
| A6 | questionless members | ARCH §2.8 rule 4, Table 2.8b, §5.8, §5.5 | — | — | — |
| A7 | per-acquisition witnesses; explicit dependence | ARCH §5.3, §6.2.2 | — | — | — |
| A8 | provenance and roles | ARCH §5.5, §5.7, §6.2.5 | — | — | — |
| A9 | emission keys | ARCH §6.1.1, §6.1.4 | — | — | — |
| A10 | contracts and build order | ARCH §6.6, Glossary, §5.3, §6.4 (falsifier 7), §3.4.2 | — | — | — |

Each change is several sub-changes. Each sub-change is classified on its own and gets its own row as it is read.

### B. Revision 1 (THE_KNEE §2.1, R1.1–R1.15; `revision_1.md` F01–F57)

To be listed row by row from `revision_1.md`. Each row's grounding note says which canon passage it follows or
amends.

### C. Departures in the chapters that A and B do not list

To be found by reading each chapter against ARCH. For example, K13 §9's "No selection of sane values" departs from
ARCH §2.8 rule 2, where the choice among sane values is measured.

### D. The engineering design (THE_KNEE §3–§4; K01, K02, K02a, K02b)

Checked against his words on engineering, and for anything that alters what the design does.

## Status

Open. Revision 2's design edits were withdrawn (`48fa94f`). Nothing else has been reverted. No row is classified
yet. The next step is A1–A10: read each amended passage whole, then classify every sub-change.
