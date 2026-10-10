# Second fresh-reader check — the prompt (2026-10-02)

GPT-6-Astra at medium effort, model-only, on a NEW thread (`--fresh`), after commit `31f2b1b` (revision 1). The prompt was
this header followed by the full text of each file listed below (KNEE_ARCHITECTURE with line numbers; the THESIS
sections the book cites, with line numbers). Revision 2's toolkit and compute-design commits came after it was sent.

## The header, verbatim

READ-ONLY. Do not run any command, read any file or write anything; everything is below.

You are an independent engineer, reading a build plan cold. You have never seen this project or any discussion
of it. Below is a project's build "book" (one chapter per severable module; lettered chapters such as K02a and
K13a are inserted siblings), its agent rules (AGENTS.md, CLAUDE.md), and the grounding the book rests on:
- the project's theory (THEORY_OF_THE_CASE) and its deep architecture canon (docs/KNEE_ARCHITECTURE.md, "ARCH");
- the sections of the computer-vision thesis (docs/canon/what_an_object_is.md, "THESIS") that the book cites;
- the founder's verbatim words;
- the house engineering doctrine and toolkit;
- the mutation-pinning tool it uses (Detective);
- the local-model harness theory and its reference implementation (SquishOS THE_DYAD,
  CONSTRAINED_OUTPUT_AND_REASONING, the harness spine doc and cassette format, and Uroboros), which ground the
  optional "typist" chapter K02a and its proposed SquishOS extension;
- the competition's own facts.

Each document is delimited `===== FILE: <path> =====`.

The founder's test of the book, in his words: "If you've done it right, then codex--literally a different
agent--should agree with you about how things should be done". The founder also required that every change be
"formally grounded in some section of the architecture document, and where under-specified, from the original
thesis document on computer vision ("what_an_object_is"), or the reference manifest". Judge it as a builder who
must execute it without access to anyone who wrote it.

Binding law, before forming any view: the ARCHITECTURE contains NO machine learning (no model, no fitted weight,
no learned component; registration/normalization is the one sanctioned bounded utility, built classically). The
typist (K02a) is a separate, optional BUILD TOOL the founder placed: a small local model that types code bodies
under a harness, admitted only with a machine-checkable certificate; it is not part of the architecture. The
evaluation regime is "No Popery": members measure one thing and know no question; bodies hold the signs; every
question of every object; identified / abstained / wrong per class; nothing is admitted or seated by its
discrimination of one question. Do not propose ML for the architecture. If something cannot work, say what
structure is missing.

Please produce, in this order:

1. **Reconstruction (≤ 600 words, your own words):** what is being built; the mechanism at data-flow level
   (including how intensities are made comparable, how tissue identity differs from change, and when an answer
   may be assigned); the build order and why (including where independence is measured); which language/compute
   is used for what; how correctness is established (pinning, SAME, panels, acceptance); where heavy compute runs;
   what the typist may and may not do; what is never done.
2. **Per chapter (K00–K27, including K02a and K13a), one line each:** AGREE / AMEND (the amendment) / DISAGREE
   (why) — "would you build it this way?"
3. **Grounding audit:** pick at least eight places where the book cites ARCH or THESIS (section or line) for a
   decision, and say whether the cited passage actually supports it. Flag any decision that cites nothing, or
   cites a passage that does not say what the book claims.
4. **Where a builder would be stuck:** missing contracts, circular or missing dependencies, acceptance that cannot
   be executed, undefined terms, contradictions between documents.
5. **Law and doctrine violations:** anything that breaks the no-ML law, No Popery, decide-or-abstain, "score is
   information", never-auto-submit, the local-Detective rule, reference-first/SAME, the two environments, the
   data policy, or (for K02a) the harness theory's laws (the model never drives; a typed hole; admitted is not
   warranted; abstention is never retried into an answer).
6. **Verdict:** do you agree with how things should be done? YES / YES WITH AMENDMENTS (ranked list) / NO (why).

Be concrete and quote sections. Under 3,000 words. Disagree plainly where you disagree.

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
- `docs/book/chapters/K02a-the-typist.md`
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
- `docs/book/chapters/K13a-hardness-and-gate.md`
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
- `docs/book/provenance/build/typist_squishos_proposal.md`
- `docs/THEORY_OF_THE_CASE.md`
- `docs/FOUNDING_RECORD.md`
- `~/Projects/SquishOS/ops/agents/reference/code-verification.md`
- `~/Projects/SquishOS/docs/home/TOOLKIT.md`
- `~/Projects/SquishOS/ops/agents/reference/detective-protocol.md`
- `~/Projects/SquishOS/ops/agents/reference/no-popery.md`
- `~/Projects/SquishOS/docs/runbooks/compute.md`
- `~/Projects/Kaggle_Killer/CLAUDE.md`
- `~/Projects/SquishOS/docs/theory/THE_DYAD.md`
- `~/Projects/SquishOS/docs/theory/CONSTRAINED_OUTPUT_AND_REASONING.md`
- `~/Projects/SquishOS/docs/spine/09-the-harness.md`
- `~/Projects/SquishOS/cassettes/README.md`
- `~/tools/Uroboros/README.md`
- `~/tools/Uroboros/docs/ARCHITECTURE.md`
- `~/tools/Uroboros/CLAUDE.md`
- `~/tools/Detective/ARCHITECTURE.md (§11 only, lines 798-831)`
- `docs/canon/what_an_object_is.md (THESIS: the sections the book cites, with their line numbers)`
- `competition facts (the Kaggle competition pages, read 2026-10-02)`
- `docs/KNEE_ARCHITECTURE.md (ARCH, the deep canon, amended by THE_KNEE §2; with line numbers)`
