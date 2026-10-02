# Revision 1 — answering the fresh-reader check

**Why this file exists.** The fresh read (`codex_fresh_answer.md`) found defects in the book at `fae32fc`. The
founder ruled at 16:29:22Z (`../../FOUNDING_PROMPTS.md`):
- every change is formally grounded in a section of `docs/KNEE_ARCHITECTURE.md` (ARCH);
- where ARCH is under-specified, it is grounded in `docs/canon/what_an_object_is.md` (THESIS) or a source in
  `../../REFERENCE_MANIFEST.toml`;
- acceptance bars are discovery;
- derived records may enter git;
- the typist goes to Codex with the revision.

At 16:35:20Z he ruled that the lead does all of the reading itself.

This file is the working record that lets the revision survive a compaction. It holds each finding, its grounding
read first-hand (section, lines, a short quote), the disposition and the status.

**Resuming after a compaction.** Read this file top to bottom. For a finding marked `grounded` but not `done`,
re-read its cited lines before editing: a note is a lead, and the lines are the fact. Never re-derive a grounding
from this file alone.

**Status codes:**
- `open`: not yet read;
- `grounded`: its sections have been read and the disposition decided;
- `done`: the book is edited (the commit is named);
- `founder`: it needs his ruling, with the evidence beside it.

## Rulings in force

| ruling | carried by | status |
|---|---|---|
| R1 · acceptance is discovery: "the 'bars' might not look so good for a long time, and fixing it is a problem to solve, not a design to discard or work around" | `CONSTRAINT_BLOCK.md`; `chapters/_TEMPLATE.md` §8; each chapter's §8 | open |
| R2 · derived records may enter git | `AGENTS.md` override 7 | done (this commit) |
| R3 · the typist goes into the book before the next Codex read | the typist chapter; `AGENTS.md`; `CONSTRAINT_BLOCK.md`; the manifest | open |
| R4 · the lead reads everything; no sub-agents for grounding | `CLAUDE.md`; `AGENTS.md` → *How a session runs* | done (this commit) |

## Findings

Numbered in the order of Codex's answer (its §3 and §4, then the per-chapter lines its §3 and §4 do not cover).
Grounding is filled in only from first-hand reading of the cited lines.

### A. The substrate

| id | the finding | chapters | grounding | disposition | status |
|---|---|---|---|---|---|
| F01 | intensity comparability: K07 retires N4 and normalization, K09 takes cross-patient medians of stored values, and no gain or bias contract exists | K07, K09, K10 | | | open |
| F02 | tissue identity vs change: deviation signs cannot name healthy tissue, which K19 and K20 need | K10, K19, K20 | | | open |
| F03 | witness provenance: a joint multi-series signature is counted as several per-series witnesses | K10, K13, K14 | | | open |
| F16 | K04 edge contracts: sign conditions of the squared level test; zero-norm tables; silence at bank level; R allocated vs active; float sqrt equality | K04 | | | open |
| F17 | K07 geometry: domains, pullback direction, inverse construction; B-spline invertibility; laterality proof; irregular slices; uncertain chirality | K07 | | | open |
| F18 | K15: `hole` after masking is undefined; headers give no slice profile; subtraction needs an observation model or abstains | K15 | | | open |
| F40 | K05: geometry validated across slices; available contrasts vs identifiable quantities | K05 | | | open |
| F42 | K08: independent landmark truth; common coordinates across plane templates | K08 | | | open |
| F43 | K09: the actual biological-variance estimator | K09 | | | open |
| F44 | K11: independent physical assumptions; damaged-structure fixtures | K11 | | | open |
| F52 | K24: nuisance gains and offsets in identifiability; physics-space references and their builder | K24 | | | open |

### B. The society and the house laws

| id | the finding | chapters | grounding | disposition | status |
|---|---|---|---|---|---|
| F23 | No Popery: PRESENT from a `SINGLE` provisional take | K16 | | | open |
| F06 | confirmation needs measured independence (K23), so before K23 it is impossible, not "rare" | K15, K16, K23 | | | open |
| F46 | K14: complete the outcome table; unknown dependence is not `SINGLE` | K14 | | | open |
| F26 | K14's split labels the residual `pathology`: pathology by elimination | K14 | | | open |
| F27 | K20 searches lines only inside confirmed edema, so a fracture without detected edema is unreachable; OA marrow-lesion scope stays unresolved | K20 | | | open |
| F24 | K22 admits the stability key by discrimination (phantoms above `checking` normals) | K22 | | | open |
| F25 | K25's null claims "no shared answer by construction" across studies, which is false | K25 | | | open |
| F50 | K21: window and null matching; zero-energy cases; layout extension | K21 | | | open |
| F53 | K26: evaluation feedback kept apart from teaching; censor construction and chance tests | K26 | | | open |
| F21 | unowned: suppression-failure readings, MCL fluid and thickening, variant recognition, agency warrants, censor chance tests, Tier-0 header machinery | several | | | open |
| F22 | unowned: K19's displaced-fragment phantoms; K24's reference builder | K11, K19, K24 | | | open |
| F48 | K19: surface extraction, damaged configurations, independent placement validation | K19 | | | open |
| F49 | K20: the missing injury measurements | K20 | | | open |
| F51 | K23: the evidence of statistical independence, and when it applies | K23 | | | open |

### C. Measurement, order, acceptance

| id | the finding | chapters | grounding | disposition | status |
|---|---|---|---|---|---|
| F19 | K03's oracle contract: a question field and truth polarity; localization vs study-level gold; report silence; `oracle_unavailable`; clustered bounds | K03 | | | open |
| F20 | panels: N's relation to T/R/G; R held out of every store; K23's building role; R used for design becomes development evidence | K03, THE_KNEE §5 | | | open |
| F04 | K12 calibrates lens metrics before K13 computes them | K12, K13 | | | open |
| F05 | K12 consumes K14's question rules without depending on K14 | K12, K14 | | | open |
| F07 | K20 needs confirmed edema while K23 depends on K20 | K20, K22, K23 | | | open |
| F08 | K17 needs keys built in K21 and K22; an early emission schema with explicit unavailable keys | K17 | | | open |
| F09 | K24 is selectable after K11 but needs first light (K18) | K24, README | | | open |
| F10 | acceptance is prose, with no commands, fixture digests or numeric expectations | all | | | open |
| F11 | replay: backend equivalence vs an authorized behaviour change; recursive staleness; selected versions; K27 skips an unselected K24 | K02, K18, K27 | | | open |
| F12–F15 | false properties: hashed folds "balanced within one"; tercile ties; longest gap not additive; binomial bounds not monotone | K03, K12, K20 | | | open |
| F41 | K06: report-negative coverage; independent adjudication of parser errors | K06 | | | open |
| F45 | K13: acquisition-specific evidence; uncertainty propagation | K13 | | | open |
| F47 | K17: comparable evidence ordering | K17 | | | open |
| F54 | K27: version-aware replay; conditional score estimates | K27 | | | open |

### D. Governance and the house tools

| id | the finding | chapters | grounding | disposition | status |
|---|---|---|---|---|---|
| F28 | AGENTS and CLAUDE say the Detective wrapper refuses pipes; THE_KNEE §3.7 says it does not | AGENTS, CLAUDE | `THE_KNEE.md` §3.7 and D5 (the later, Codex-reviewed decision) | follow THE_KNEE | done (this commit) |
| F35 | THE_KNEE says THEORY Laws 1–8 are unchanged, while AGENTS forbade what Law 3 sanctions | AGENTS, THE_KNEE | THEORY Law 3 (l. 281–282): "One sanctioned bounded-ML utility: registration/normalization (II.1) … Nothing else learns." FOUNDING_RECORD (l. 16–17): "Maybe I'll end up using some small model somewhere for some reason, but NO, the architecture is NOT NOT NOT ML." | AGENTS restates Law 3 and the founder's reservation; THE_KNEE states what the book builds classically | AGENTS done (this commit); THE_KNEE open |
| F33 | K03 commits a corpus digest despite "nothing derived enters git" | K03 | founder, 16:29:22Z | allowed (R2) | open (K03 wording) |
| F34 | saved reviews, receipts and generated tests need a stated destination when they hold derived material | K02, K03 | R2; AGENTS override 7 | git for records; `data/` for bulk | open |
| F29 | K01 needs the wrapper before K02 builds it | K01, K02 | | | open |
| F30 | some acceptances demand that every function be pinned; Detective §11 allows honest unpinnability | several | | | open |
| F31 | K09's reference is NumPy's median, not plain Python | K09 | | | open |
| F32 | SAME must carry declared nonfinite behaviour | K02 | | | open |
| F36 | the fleet runbook says offloading is NOT-BUILT; the compute runbook supplies it | THE_KNEE §4, K01 | | | open |
| F37 | identify the node before any remote action | K01 | | | open |
| F38 | K22's escalation cannot reach the Mac Pro from offline Kaggle | K22 | | | open |
| F39 | performance evidence needs work and byte accounting, not seconds alone | several | | | open |
| F55 | K00: reconcile the authorities; executable acceptance | K00 | | | open |
| F56 | K02: acceptance manifests, dependency-freshness checks, explicit layer contracts | K02 | | | open |

## Reading log

The sections of ARCH and THESIS read first-hand during this revision, with their line ranges. Reading is never
delegated (R4).

| when | source | lines | sections |
|---|---|---|---|
</content>
</invoke>
<invoke name="Bash">
<parameter name="command">cd /Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee && git add AGENTS.md CLAUDE.md docs/book/FOUNDING_PROMPTS.md docs/book/provenance/build/revision_1.md && git commit -q -F - <<'EOF'
knee/K00: record the founder's rulings; open revision 1; the lead reads

- FOUNDING_PROMPTS: the founder's messages of 16:08Z-16:35Z, byte-exact
  (the typist proposal; the fresh read; "formally grounded in some section
  of the architecture document"; acceptance as discovery; derived records
  in git; "I want YOU to do this").
- AGENTS/CLAUDE: the lead does all grounding reading itself; sub-agents
  only on the founder's request (16:35:20Z).
- AGENTS/CLAUDE: the Detective wrapper keeps complete logs and preserves
  the exit status; it does not refuse pipes (THE_KNEE 3.7, D5). F28.
- AGENTS law 1: THEORY Law 3's one sanctioned utility (registration and
  normalization) and the founder's own reservation, quoted. F35 (part).
- AGENTS override 7: derived records may enter git; the GitHub repository
  is private (checked) and stays so while it holds them. R2.
- provenance/build/revision_1.md: the working record of revision 1, every
  finding with its grounding, disposition and status, so the revision
  survives a compaction.
EOF
git log --oneline -2