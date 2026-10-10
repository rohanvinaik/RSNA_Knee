# The Knee — the build book

**What it is.** The build plan for the classical-AI RSNA Knee entry, persisted so that no session can lose it. It
takes the form the founder asked for: the SquishOS book, one chapter per severable module, "with the full intent
and context laid out cleanly and persistently" (founder, 2026-10-02). The rigid oracle is the founder's lens principle, stated
first in [`CONSTRAINT_BLOCK.md`](CONSTRAINT_BLOCK.md). The design is being built in session under it (founder,
2026-10-02 23:59:57Z), and the build runs in dependency order.

## How to read this book

1. [`CONSTRAINT_BLOCK.md`](CONSTRAINT_BLOCK.md): the laws, the resolved decisions, the forbidden moves and the next
   action, in two pages.
2. [`THE_KNEE.md`](THE_KNEE.md): the founding design. The mechanism at data-flow level; exactly which canon
   passages the accord amends; the engineering design; the compute topology; the measurement regime; the
   decisions with their deductions.
3. [`FOUNDING_PROMPTS.md`](FOUNDING_PROMPTS.md): the founder's words, verbatim. They win over everything here.
4. The chapter you are building, in [`chapters/`](chapters/), against [`chapters/_TEMPLATE.md`](chapters/_TEMPLATE.md).
5. [`MIGRATION.md`](MIGRATION.md): the legacy `RSNA_Knee` units and each one's reuse-or-retire row.
6. [`provenance/`](provenance/): how the design was reached. `review/` holds Claude's reading of
   KNEE_ARCHITECTURE and three Codex rounds; `build/` holds Claude's design reading, the Codex rounds and the
   fresh-reader check. Read it when a decision is questioned. It is evidence, not canon.

## The chapters (dependency order; whole chapters, never demo slices)

| ch | delivers | depends on |
|---|---|---|
| [K00](chapters/K00-founding-record.md) | the founding record: this book, the rules, the manifest, the provenance | — |
| [K01](chapters/K01-characterization.md) | characterization: the local Detective's capabilities; the Kaggle runtime; the Mac Pro's environment; local data census; hook coverage | K00 |
| [K02](chapters/K02-verification-infrastructure.md) | verification infrastructure: VERIFY/DEPLOY environments, `justfile`, gate config, Import Linter, the backend registry, the SAME harness, acceptance manifests and recursive staleness, events, store skeleton | K01 |
| [K02b](chapters/K02b-compute-design-and-native-layer.md) | the compute design and the native layer: language by computation shape, the compute contract per kernel, hot/cold and one-hit memory, the kernel's budget, the instruments; the Rust crate and the C library, built and packaged for every environment | K02, K01 |
| [K02a](chapters/K02a-the-typist.md) *(optional)* | the typist: a small local model types eligible bodies (twins of pinned references; finite-code decisions) under the SquishOS harness, admitted only with a certificate; its qualification run | K02 |
| [K03](chapters/K03-acceptance-corpus-and-harness.md) | acceptance corpus and harness: vocabulary and the 12 columns; panels and roles; the recognition table; authored cases; the scorer | K02 |
| [K04](chapters/K04-carrier-arithmetic.md) | carrier arithmetic: the exact ledger's algebra, declared limits, the exact level test, decode, packed signs for ordering | K02 |
| [K05](chapters/K05-corpus-and-ingest.md) | corpus and ingest: fetch, header census, decoders by transfer syntax, stored values, geometry, inventory, regime keys, identifiable sets; sharded on the Mac Pro | K02, K03 |
| [K06](chapters/K06-text-oracle.md) | text oracle: localized ternary calls from the reports; softness; the report-negative candidates; gold dependence recorded | K03 |
| [K07](chapters/K07-frame-and-bootstrap-registration.md) | frame and bootstrap registration: chirality, box, plane grids, rigid intra-study alignment, the bootstrap template and landmarks, kept transforms, constraint readings | K05 |
| [K08](chapters/K08-atlas-and-refined-registration.md) | atlas and refined registration: unbiased templates, re-registration, zones, landmarks and attachments, multi-atlas votes | K07, K03, K06 |
| [K09](chapters/K09-population-references.md) | population references: the role-split report-negative pool, the founder's sample check, robust references per class × regime × place | K08, K06 |
| [K10](chapters/K10-deviation-and-signatures.md) | deviation and signatures: z with stated numerics, the licensed record, residual, windows, sign patterns | K09 |
| [K11](chapters/K11-phantoms.md) | phantoms: independently specified truth; geometry, acquisition, misregistration, lesion and near-miss phantoms | K10, K08 |
| [K12](chapters/K12-measurement-layout.md) | measurement layout v1: the schema (facets, banks, rows, the question → banks map, the edge rule), versioned; edges land as each metric's readings exist | K04, K10, K03 |
| [K13](chapters/K13-zone-lenses.md) | zone lenses: the volumetric, questionless measurements, per acquisition, with a visibility and uncertainty contract; their edges set (layout v1.1) | K12, K11, K08 |
| [K13a](chapters/K13a-hardness-and-gate.md) | the hardness map and the independence gate, for the zone questions: healthy false readings, φ and κ per pair of series families, entitlement data | K13, K09, K11, K03 |
| [K14](chapters/K14-society-contracts.md) | society contracts (pure): witnesses and dependence schema, three-tier negative knowledge, the split, decision words, the kept-record schema | K03 |
| [K15](chapters/K15-explanation-loop.md) | explanation loop: provisional takes, objects confirmed by gated concurrence, explanation records, nesting, post-checks, the kept record | K13a, K14 |
| [K16](chapters/K16-agencies-case-free.md) | agencies, case-free: the structure-alone decision path; placement records | K15, K14 |
| [K17](chapters/K17-emission.md) | emission: registers, the literal 0.5, ordered variants reported for Q4, witness-set comparability | K16, K03 |
| [K18](chapters/K18-kernel-and-first-light.md) | the kernel and **first light**: packaging, private datasets, DEPLOY run, private Kaggle dry run, the structure-alone run | K17, K02 |
| [K19](chapters/K19-delineation.md) | delineation: containers, identity evidence I, visibility certificates, placement uncertainty | K08, K10, K18 |
| [K20](chapters/K20-structure-lenses.md) | structure lenses: contact, bow tie, extrusion, continuity, angle, neck, line, cartilage, margin; layout v2 | K19, K12, K11 |
| [K21](chapters/K21-identity-conflict-reader.md) | identity–conflict reader: (I, D) cells, the four legacy words, the \|z\| survival profile, shapes in health | K19, K10, K11 |
| [K22](chapters/K22-perturbation.md) | perturbation: frame and quantizer families, stability, flip axis, sandwich, stated limitations | K20, K21, K07, K12 |
| [K23](chapters/K23-hardness-and-dependence.md) | the hardness map and the gate, extended to the structure questions; multiway dependence; the κ map as a lens | K22, K13a |
| [K24](chapters/K24-the-law.md) *(optional)* | the quantitative law, only where identifiable: named offsets and gains, typed misfit, leave-one-series-out, its own physics-space references | K18, K10, K05, K11 |
| [K25](chapters/K25-memory.md) | memory: cases with sources, the null mechanism for trust radii, recall, routed procedures, the recall kernel | K04, K12, K14, K15, K06, K20 |
| [K26](chapters/K26-teaching-and-recall-agencies.md) | teaching and agencies with recall: curricula, sheets, near-miss censors, trajectories in rotation, H2's bridge | K25, K23, K06 |
| [K27](chapters/K27-final-kernel.md) | the final kernel: the selected configuration validated, the full private dry run, the expected score with bounds beside the structure-alone score; never auto-submit | K26, K18 (and K24 if selected) |

**Parallel tracks:**
- K04 alongside K05–K11;
- K06 alongside K05–K07;
- K14 alongside K05–K13a;
- the optional K02a at any time after K02, when its selection is recorded;
- the optional K24 at any time after K18, when its selection is recorded.

## Conventions

- **Commits** go straight to `main`, each message starting with its chapter: `knee/K05: …`. Pushes are asked for.
- **Lettered siblings.** A chapter inserted after the table was written takes a letter (K02a, K13a), as the
  SquishOS book's adapters do (M05a–M05j). Numbers are stable labels. The table's order is the build order.
- **Acceptance is written first, and it is discovery** (founder, 2026-10-02 16:29:22Z; ARCH §6.6.3: "no phase has
  a target score. A no-go names a disease").
  - A chapter's first act writes its acceptance manifest: the commands, the fixtures with digests, the readings,
    and each domain reading's expectation.
  - Engineering acceptance gates the tag: behavioural correctness, representation fidelity, SAME, every
    function's standing, work counted.
  - Domain readings are recorded per class against their expectations, and they never gate. A miss opens a
    problem in the chapter's §9. It is never a reason to discard the design or work around it, and never
    retuned to meet the expectation.
- **Acceptance is a tag:** `git tag knee-K05` when a chapter passes its acceptance. Add a dated note to its status
  log, with its Codex review (model-only, saved in `provenance/`). The tag says the chapter is built, verified and
  measured, never that its numbers are good.
- **Status is computed, not written.**
  - `git tag -l 'knee-*'` is the record of progress.
  - `just accept K05` re-runs a chapter's acceptance at HEAD. A chapter whose acceptance no longer passes is
    stale, whatever its tag says. Staleness is recursive: a stale dependency makes its consumers stale.
  - Each chapter's *Invalidation* field names the changes that make it stale.
- **Optional chapters** (K02a, K24) are skipped by the next-chapter rule unless their selection is recorded in
  `docs/book/SELECTION.toml` (absent means not selected). K27 validates the recorded selection: if K24 is
  selected, its acceptance and the invalidation it causes downstream are required; if not, its absence is
  explicit.
- **First light is re-run.** Every chapter after K18 that changes integration re-runs `just firstlight`, the
  structure-alone run. Two different checks follow, never confused:
  - **SAME** (THESIS §12.5): an accelerated twin against its reference, at one revision, in one environment.
  - **A behaviour change:** a chapter that changes decisions on purpose records a new reference version with
    its intent. Its run is read as a diff against the previous first-light record, never as SAME.
- **The house rules** live in `AGENTS.md`; the global rules in `~/.claude/CLAUDE.md` and the SquishOS reference
  docs.

## How a session runs

1. **Start.** Read `CONSTRAINT_BLOCK.md`.
2. **Pick.** Run `git tag -l 'knee-*'` and apply the next-chapter rule. Read the chapter in full, with its
   substrate and prior art.
3. **Restate** the chapter's mechanism at data-flow level before changing anything the design derives.
4. **Build** to its acceptance. Commit as you go, with the label.
5. **Close.** Gate, `just accept Kxx`, Codex review, a dated status note, then the tag.
6. **If the context runs out mid-chapter:** the chapter's build list, the labelled commits and the pre-compaction
   snapshot carry it into the next session. Re-ground on git and the files; a summary is a lead, not a fact.

## Where things live

| what | where |
|---|---|
| the house rules for every agent | `AGENTS.md` (canonical) and `CLAUDE.md` (Claude-specific lines) |
| the design canon | `docs/THEORY_OF_THE_CASE.md`, `docs/KNEE_ARCHITECTURE.md` (as amended), `docs/canon/` |
| this book | `docs/book/` |
| the sources, checksummed | `docs/book/REFERENCE_MANIFEST.toml`; verify with `python3 ~/Projects/SquishOS/scripts/check_reference_manifest.py docs/book/REFERENCE_MANIFEST.toml` |
| the new code | `src/knee/` (from K02 on) |
| legacy code | `src/RSNA_Knee/`, `tools/` (quarantined; `MIGRATION.md`) |
| data, derived artifacts, caches | `data/` (gitignored); private Kaggle datasets for kernel artifacts |
| the Mac Pro | identify it first: `squishos-fleet profile squishhub` (no network); jobs through `squishos-compute` (`~/Projects/SquishOS/docs/runbooks/compute.md`, the operative runbook) |
| the typist (K02a) | `tools/typist/` (dev-only, never in DEPLOY), through `squishos-harness` |
