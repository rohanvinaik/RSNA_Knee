# CLAUDE.md — RSNA_Knee

@AGENTS.md

## Claude Code specifics

- **Serena** is activated on this directory by path. Sub-agents orient with `aider-map` and `Read`, never their
  own Serena.
- **The filter hooks do not see `python -m Detective.cli`** (verified 2026-10-02). Use `just detective …`, which
  logs every run and refuses a pipe. For a long run, read the `.detective/runs/` log whole.
- **Probe scripts** go in the scratchpad and are written with `Write`, not a heredoc. Hooks refuse `cat`, `sed`
  and `grep` on Python source; structural questions go to Serena or an AST query.
- **Codex transcripts** of each design and review round go in `docs/book/provenance/`, with your own reading
  first.
- **LintGate files.** `.claude/rules/lg_focus.md` and `lg_session.md` are telemetry, observational and not
  instructions. `.claude/rules/theory.md` is LintGate-managed. Its "canonical module structure" is the book's
  chapter table.
- **After a compaction:** re-read `docs/book/CONSTRAINT_BLOCK.md`, run `git tag -l 'knee-*'`, and re-ground on git
  and the files. A summary of this project is a lead, not a fact.
