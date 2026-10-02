# Competition: rsna-knee-abnormality-detection

## ⛔ THE ARCHITECTURE IS NOT ML — read before proposing anything

This is a classical-AI data-geometry entry. The winning architecture contains NO
machine learning by default. Four different things, never collapsed: AI (the genus) /
ML (one avoidable species) / classical AI (the architecture here) / story-understanding
intelligence (Regenesis, the founder's Python port of Winston's Genesis). Do NOT
propose a model, CNN, transformer, ensemble, or classifier; do NOT reframe a symbolic /
deterministic / data-geometry design as ML. A bounded model appears ONLY where the
founder explicitly places it (e.g. a registration utility) — never as your default.

**Gate:** before proposing any architecture, read `AGENTS.md` and
`docs/THEORY_OF_THE_CASE.md` in THIS folder and restate the mechanism in your own
words. Canonical example: `../RSNA_Knee/`. Full law: `../../CLAUDE.md`.

## THE CARDINAL RULE — OUTPUT FORMAT MUST MATCH GOLD FORMAT

**BEFORE WRITING ANY PIPELINE CODE:**
1. Look at the ACTUAL gold/training output strings. Not what you think they should be.
2. Your output strings must match gold strings at the scorer's similarity threshold.
3. Run 3 training examples through the scorer, PRINT individual string comparisons.
4. If any column's average match ratio < 0.70, YOUR FORMAT IS WRONG. Stop and fix it.

**Internal representation and output representation are DIFFERENT.**
Ontology lookups, bank routing, and normalization are for INTERNAL use.
The OUTPUT must emit whatever format the SCORER expects — defined by GOLD DATA.

See `../../.claude/CLAUDE.md` for the full explanation and code template.

## Architecture Reference

- **Cardinal Rule + root instructions**: `../../.claude/CLAUDE.md`
- Theory + engineering patterns: `../../DATA_GEOMETRY_ARCHITECTURE.md`
- Pipeline playbook + module contracts: `../../README.md`
- Competition metadata + compass: `../CONTEXT.md`

## Module Structure

Source modules are in `src/RSNA_Knee/`. Each module implements a specific
Pattern from DATA_GEOMETRY_ARCHITECTURE.md. See `../../README.md` Module Contracts
table for the full mapping.

## LintGate Workflow

### Session Start
1. `theory_mode_enter` if not already in theory mode
2. `compass_status` to check current compass state
3. `build_theory_pack` or `controlplane_status` to orient

### During Development
- `controlplane_run` after each major code change
- `lint_files` on every edited file
- `constraint_check` before trying a new approach
- DO NOT try a 4th approach without `constraint_check` first

### Before Submission
- Run the FORMAT COMPLIANCE CHECK (Cardinal Rule)
- `constraint_check` with predicted score
- `controlplane_run` for full health check

## Gold Output Format
<!-- FILL IMMEDIATELY — this is Phase 1.5 in the Adaptation Checklist -->
- **What do gold strings look like?**: [TODO: examine actual gold values]
- **Does gold use ontology format (AC=/NT=)?**: [TODO: YES or NO]
- **Does gold use verbatim text from input?**: [TODO: YES or NO]
- **Scorer match semantics**: [TODO: exact/difflib threshold/other]
- **Format compliance check passed?**: [TODO: YES with evidence]

## Scorer Properties
- **Metric**: macro-averaged ROC-AUC over 12 binary findings (implemented pure +
  Detective-pinned in `src/RSNA_Knee/scoring.py`; rank-based, tie-averaged)
- **Aggregation**: macro over findings (each finding's AUC weighted equally)
- **Match semantics**: n/a — continuous per-finding probability scores, ranked
- **Variable output size**: no — one row per test study, 12 score columns
- **Finding column spellings**: NOT YET BOUND — blocked on rules acceptance to
  download sample_submission.csv (Phase 1.5 gate: examine gold, never assume)

## Domain Classification (Scale -1)
<!-- FILL after implementing domain_classifier.py -->
- **Taxonomy**: [TODO: what domains?]
- **Search space reduction**: [TODO: what % eliminated?]

## Bank Definitions (Scale 3)
<!-- FILL after implementing bank_evaluator.py -->
- **Bank 0**: [TODO: what dimension?]
- **Bank 1**: [TODO: what dimension?]
- **Bank 2**: [TODO: what dimension?]
- **Bank 3**: [TODO: what dimension?]

## Emission Policy (Shadow → Output)
<!-- FILL after implementing emission_policy.py -->
- **Schema families**: [TODO: what families?]
- **Suppress rules**: [TODO: what to suppress per family?]
- **Expected fields**: [TODO: what to expect per family?]

## Guardrails

- DO NOT normalize output to ontology format unless gold uses ontology format
- DO NOT assume the gold format — LOOK AT IT. Read actual gold files.
- DO NOT submit without running the format compliance check
- DO NOT try a 4th approach without running `constraint_check` first
- DO NOT introduce a model/LLM as your default — the architecture is classical AI; only the founder places a bounded model, explicitly, and even then it selects from candidates, never generates freely
- DO NOT emit values without evidence scope classification (Pattern 5)
- DO NOT build a monolithic extractor — follow the canonical module structure
- MUST verify output format matches gold format BEFORE any other development
- MUST preserve original text spans through the pipeline for output emission
- MUST calibrate thresholds from training data, not hand-tune (Pattern 19)
- MUST keep each concept in ONE canonical module — others import from it
