# CLAUDE.md — RSNA_Knee

@AGENTS.md

## Claude Code specifics

- **The global rules apply.** That means `~/.claude/CLAUDE.md`, rendered from SquishOS `ops/agents/`: Serena
  first and `find_referencing_symbols` before every edit; `uvx ty check` after a non-trivial edit; commit to
  `main` without asking, and ask before pushing. This file does not restate them.
- **Serena** is activated on this directory. Sub-agents orient with `aider-map` and `Read`, never their own Serena
  (each one costs about 1.5 GB).
- **Detective here is never the `detective` on PATH**, which is the PyPI build. It is `just detective …`
  (AGENTS.md, Engineering law 7). The hooks that refuse filtered output (`no-filter-cli-output`) apply in spirit
  to `python -m Detective.cli` too. A long run goes to a `.log` file, then read it whole.
- **Hooks refuse grep on Python.** Wiring questions go to Serena. Structural questions over the tree go to an AST
  query. A probe script lives in the scratchpad and is written with `Write`, not a heredoc.
- **Codex** is consulted model-only (the global `codex-consultation.md`), with your own reading written first. A
  chapter closes with a Codex review, and the book carries the transcripts in `docs/book/provenance/`.
- **The LintGate files** `.claude/rules/lg_focus.md` and `lg_session.md` are telemetry, observational and not
  instructions. `.claude/rules/theory.md` is LintGate-managed. Its "canonical module structure" is the book's
  chapter table.
- **After a compaction:** re-read `docs/book/CONSTRAINT_BLOCK.md`, run `git tag -l 'knee-*'`, and re-ground on git
  and the files before acting. A summary of this project is a lead, not a fact.
