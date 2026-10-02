# Decision Log

Structured record of significant architectural and design decisions for `RSNA_Knee`.
Each file captures what was decided, why, and what alternatives were considered.

## Format

One file per decision, named: `YYYY-MM-DD-topic.md`

```markdown
# Decision: [Short title]

**Date:** YYYY-MM-DD
**Status:** accepted | superseded | rejected
**Context:** What prompted this decision?

## Decision
What was decided.

## Rationale
Why this approach was chosen.

## Alternatives Considered
- Alternative A: why rejected

## Consequences
What changes as a result. What new constraints exist.
```

## How agents should use this

Before proposing an architectural change, check this directory for prior decisions on
the same topic. If your change would contradict an existing decision — especially
`2026-08-18-classical-ai-no-ml.md` — document why circumstances have changed, and
expect the founder to govern (the design has an ML-substitution failure mode; see
`docs/THEORY_OF_THE_CASE.md` Part V).
