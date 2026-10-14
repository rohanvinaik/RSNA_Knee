# CLAUDE.md — RSNA_Knee

## ⇒ BEFORE YOU WRITE ANY CODE IN THIS REPOSITORY: **`just unit`**

It prints the build loop, declared route standing, whole open tasks and structural place diagnostics.
Execution, successful rendering and certification require their own evidence. **Run it;
do not try to remember the loop.** This line is deliberately a pointer to a command and not a
summary of one: the loop is also written in `docs/STAGE_CONTRACT.md` and `docs/SPINE.md`, and on
2026-10-11 the lead had both in context and built against neither. What changed its behaviour that
day was `plan-status` printing 3/23, Detective refusing to call two survivors equivalent, ruff
failing the gate, and an intent test failing — commands that answer back, never prose. A fourth copy
of the loop in this file would fail the same way, so there isn't one.

**Read first:** `AGENTS.md` (imported below), then `docs/OBJECT_MODEL.md`,
`docs/PIPELINE_AS_OBJECT.md` and `docs/BUILD_PLAN.md`. `docs/SPINE.md` (imported below)
keeps the PI–undergrad pass; its chapter table is superseded. The immediate change is
`every-stage-renders`. The oracle governs every design decision, and it supersedes the architecture document.

@AGENTS.md

@docs/SPINE.md

## Claude Code specifics

- **Your native pull runs against the oracle.** The founder: "You have a bad habit of finding a set of signals that
  kinda vibe and jumping to assign a label to it". As a neural net you reach for the most plausible label; this
  project runs on strict knowability. Assign only what is known, reject only what is known not to be, and abstain
  on the rest. A category's name never outruns its warrant.
- **The understanding is yours; the mining may be delegated.** Grounding means knowing:
  - the thesis and the cell-tracking build of the chapter's stage (the two oracles);
  - the founder's words;
  - the sources a chapter cites.

  The lead does the **synthesis, the interpretation and the telling**, always. Founder, 2026-10-02 16:35:20Z:
  "I want YOU to do this … We are lITERALLY establishing the persistent, post-compact stable context grounding."

  **Standing authorization, founder 2026-10-10**, which amends the former rule that a sub-agent was launched only
  when he asked each time: "Make sure you're using cheap agents/advisors to look into the thesis and the cell
  tracking project build as needed when you're uncertain. Both are oracles of truth--one on theory and
  explanation, one on literal engineering. One can be read, one symbolically traced, but the workflow you should
  be using is to work it out with fable/codex and ground on truth with cheap agents mining on the text/advisors on
  questions you need to solve. I can guide where needed, but this is a nice, clean workflow loop."

  So a reading agent may be launched without asking. It is a **miner**, never a reasoner: it reads named units
  whole and returns **facts with their locations and verbatim quotations**, says plainly what it did not look at,
  and offers no judgement. Information still flows downward only — it informs the lead of facts, and never of
  meaning, intent or what to build. The loop itself is in `docs/SPINE.md`.
- **Serena** is activated on this directory by path.
- **The filter hooks do not see `python -m Detective.cli`** (verified 2026-10-02). Use `just detective …`, which
  keeps every run's complete output in `.detective/runs/` and preserves its exit status. It does not refuse pipes
  (`THE_KNEE.md` §3.7, D5). Read each run whole.
- **Probe scripts** go in the scratchpad and are written with `Write`, not a heredoc. Hooks refuse `cat`, `sed`
  and `grep` on Python source; structural questions go to Serena or an AST query.
- **Design/review transcripts** go in the relevant chapter’s `readings/`, with your own reading first,
  as specified by `docs/SPINE.md`. `workbench/consults/` keeps the request and lead preparation.
  The earlier rounds are in `archive/docs/book/provenance/`.
- **LintGate files.** `.claude/rules/lg_focus.md` and `lg_session.md` are telemetry, observational and not
  instructions. `.claude/rules/theory.md` is LintGate-managed. Its "canonical module structure" is the stage
  packages of `src/knee/` (the current nine-stage object route).
- **After a compaction:** re-read `AGENTS.md`'s opening section, the rigid oracle and `docs/SPINE.md`, then
  re-ground on git and the files: the current chapter's package in `src/knee/`. A summary of this project is a
  lead, not a fact.
