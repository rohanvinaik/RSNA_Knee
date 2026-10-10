# Fresh-reader check — the prompt (2026-10-02)

Sent to GPT-6-Astra at medium effort, model-only (`CODEX_HOME=~/.config/codex-model-only/home`), on a NEW thread
(`--fresh`, thread `01a0fd63-124e-7843-bcad-b216bab9d6b6`), from an empty room, after commit `fae32fc`.
The prompt was this header followed by the full text of each file listed below, each delimited
`===== FILE: <path> =====`. Contents are not repeated here; the book files are at `fae32fc` and the external
grounding is checksummed in `REFERENCE_MANIFEST.toml`. A short block of competition facts from the public
competition pages was also included.

## The header, verbatim

READ-ONLY. Do not run any command, read any file or write anything; everything is below.

You are an independent engineer, reading a build plan cold. You have never seen this project or any discussion
of it. Below is a project's build "book" (one chapter per severable module), its agent rules (AGENTS.md,
CLAUDE.md), and the grounding the book rests on: the project's theory and canon, the founder's verbatim words,
the house engineering doctrine it cites, the tool it pins with (Detective), the machine registry it uses for heavy
compute (SquishOS), and the competition's own facts. Each document is delimited `===== FILE: <path> =====`.

The founder's test of the book, in his words: "If you've done it right, then codex--literally a different
agent--should agree with you about how things should be done". So judge it as a builder who must execute it
without access to anyone who wrote it.

Note the project's binding law before forming any view: the architecture contains NO machine learning (no model,
no fitted weight, no learned component; registration is the one bounded utility), and its evaluation regime is
"No Popery" (members measure one thing and know no question; bodies hold the signs; every question of every
object; identified / abstained / wrong per class). Do not propose ML. If something cannot work, say what
structure is missing.

Please produce, in this order:

1. **Reconstruction (≤ 600 words, your own words):** what is being built; the mechanism at data-flow level; the
   build order and why; which language/compute is used for what and why; how correctness is established (pinning,
   SAME, panels); where heavy compute runs; what is never done.
2. **Per chapter (K00–K27), one line each:** AGREE / AMEND (the amendment) / DISAGREE (why) — "would you build
   it this way?"
3. **Where a builder would be stuck:** missing contracts, circular or missing dependencies, acceptance that cannot
   be executed or measured, terms used but never defined, contradictions between documents.
4. **Law and doctrine violations:** anything that breaks the no-ML law, No Popery, decide-or-abstain, "score is
   information", never-auto-submit, the local-Detective rule, reference-first/SAME, the two environments, or the
   data policy.
5. **Verdict:** do you agree with how things should be done? YES / YES WITH AMENDMENTS (ranked list) / NO (why).

Be concrete and quote sections. Under 2,500 words. Disagree plainly where you disagree.

## The files, in order

- `AGENTS.md`
- `CLAUDE.md`
- `docs/book/README.md`
- `docs/book/CONSTRAINT_BLOCK.md`
- `docs/book/THE_KNEE.md`
- `docs/book/FOUNDING_PROMPTS.md`
- `docs/book/MIGRATION.md`
- `docs/book/SELECTION.toml`
- `docs/book/chapters/_TEMPLATE.md`
- `docs/book/chapters/K00-founding-record.md`
- `docs/book/chapters/K01-characterization.md`
- `docs/book/chapters/K02-verification-infrastructure.md`
- `docs/book/chapters/K03-acceptance-corpus-and-harness.md`
- `docs/book/chapters/K04-carrier-arithmetic.md`
- `docs/book/chapters/K05-corpus-and-ingest.md`
- `docs/book/chapters/K06-text-oracle.md`
- `docs/book/chapters/K07-frame-and-bootstrap-registration.md`
- `docs/book/chapters/K08-atlas-and-refined-registration.md`
- `docs/book/chapters/K09-population-references.md`
- `docs/book/chapters/K10-deviation-and-signatures.md`
- `docs/book/chapters/K11-phantoms.md`
- `docs/book/chapters/K12-measurement-layout.md`
- `docs/book/chapters/K13-zone-lenses.md`
- `docs/book/chapters/K14-society-contracts.md`
- `docs/book/chapters/K15-explanation-loop.md`
- `docs/book/chapters/K16-agencies-case-free.md`
- `docs/book/chapters/K17-emission.md`
- `docs/book/chapters/K18-kernel-and-first-light.md`
- `docs/book/chapters/K19-delineation.md`
- `docs/book/chapters/K20-structure-lenses.md`
- `docs/book/chapters/K21-identity-conflict-reader.md`
- `docs/book/chapters/K22-perturbation.md`
- `docs/book/chapters/K23-hardness-and-dependence.md`
- `docs/book/chapters/K24-the-law.md`
- `docs/book/chapters/K25-memory.md`
- `docs/book/chapters/K26-teaching-and-recall-agencies.md`
- `docs/book/chapters/K27-final-kernel.md`
- `docs/THEORY_OF_THE_CASE.md`
- `docs/FOUNDING_RECORD.md`
- `~/Projects/SquishOS/ops/agents/reference/code-verification.md`
- `~/Projects/SquishOS/ops/agents/reference/performance.md`
- `~/Projects/SquishOS/ops/agents/reference/detective-protocol.md`
- `~/Projects/SquishOS/ops/agents/reference/no-popery.md`
- `~/Projects/SquishOS/ops/agents/reference/context-maintenance.md`
- `~/tools/Detective/docs/theory/deterministic_sicp/CONSTRAINT_BLOCK.md`
- `~/Projects/SquishOS/docs/runbooks/fleet.md`
- `~/Projects/SquishOS/docs/runbooks/compute.md`
- `~/Projects/Kaggle_Killer/CLAUDE.md`
- `~/tools/Detective/ARCHITECTURE.md (§11 only, lines 798-831)`
- `competition facts (the Kaggle competition pages, read 2026-10-02)`
- `docs/KNEE_ARCHITECTURE.md (the deep canon, amended by THE_KNEE §2)`
