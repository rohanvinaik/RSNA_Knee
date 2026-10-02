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
| F01 | intensity comparability: K07 retires N4 and normalization, K09 takes cross-patient medians of stored values, and no gain or bias contract exists | K07, K09, K10 | ARCH §2.3, §3.1, §3.3.3, §3.3.9, §3.4.1; THEORY II.1 (notes §F01) | γ_s on reference tissue for every series; N4 per THEORY II.1; no p2–p98, no histogram match; stored values kept for K24 | grounded |
| F02 | tissue identity vs change: deviation signs cannot name healthy tissue, which K19 and K20 need | K10, K19, K20 | ARCH Table 2.3a, §2.3.2, lens 3, §3.4.3, l.3866 (notes §F02) | the word is a tissue level within the series against muscle; change = word against the zone's normal word, beside z | grounded |
| F03 | witness provenance: a joint multi-series signature is counted as several per-series witnesses | K10, K13, K14 | ARCH §5.3 l.3408–3413 (independence classes), l.3487–3490 (the sandwich), l.3499–3503 (the record per series); §2.3 consequence 3 l.906–908; Table 5.1 rule 3 (notes §F03) | every reading carries its complete source set; voices are per acquisition; the joint signature is a law check that supports, never a voice | grounded |
| F16 | K04 edge contracts: sign conditions of the squared level test; zero-norm tables; silence at bank level; R allocated vs active; float sqrt equality | K04 | | | open |
| F17 | K07 geometry: domains, pullback direction, inverse construction; B-spline invertibility; laterality proof; irregular slices; uncertain chirality | K07 | | | open |
| F18 | K15: `hole` after masking is undefined; headers give no slice profile; subtraction needs an observation model or abstains | K15 | ARCH §4.4 l.2832–2836 (the take removes the law's contribution), l.2850–2865 (post-take check), l.2914–2916; §2.4 consequences 2–3 l.1041–1046; THESIS §4.5 l.793–795; THE_KNEE §2 change 4 (notes §F18) | mask mode (default): ring and lobe only, hole and impossible recorded not_applicable; contribution mode only under a stated law (Table 4.6 halos), with all four checks; the slice profile is a declared rectangular assumption of SliceThickness, measured on phantoms | grounded |
| F40 | K05: geometry validated across slices; available contrasts vs identifiable quantities | K05 | | | open |
| F42 | K08: independent landmark truth; common coordinates across plane templates | K08 | | | open |
| F43 | K09: the actual biological-variance estimator | K09 | | | open |
| F44 | K11: independent physical assumptions; damaged-structure fixtures | K11 | | | open |
| F52 | K24: nuisance gains and offsets in identifiability; physics-space references and their builder | K24 | | | open |

### B. The society and the house laws

| id | the finding | chapters | grounding | disposition | status |
|---|---|---|---|---|---|
| F23 | No Popery: PRESENT from a `SINGLE` provisional take | K16 | ARCH Glossary 'Concurrence' l.5233–5234; Table 5.5 l.3449; Table 5.1 rule 2 l.3236; THESIS §4.4 l.741–748, §4.5 l.778–781 (notes §F23) | SINGLE yields a provisional take only; no PRESENT or ABSENT rests on one voice; the word is ABSTAIN (single_voice) | grounded |
| F06 | confirmation needs measured independence (K23), so before K23 it is impossible, not "rare" | K15, K16, K23 | ARCH §6.2 l.4517–4521 (step 7: independence measured before anything is taught), §6.2.2 l.4585–4623, §5.3 gate l.3415–3425, §6.7 item 8 l.5109–5110; THE_KNEE §2 change 7 (notes §F06) | move the gate before the society (after K13), re-run as structure lenses arrive; the bar is the founder's (ARCH §6.7 item 8) | founder |
| F46 | K14: complete the outcome table; unknown dependence is not `SINGLE` | K14 | ARCH Table 5.5 l.3444–3451; §6.2.5 rule 4 l.4706–4707; THE_KNEE §2 change 7 ('insufficient') | add INSUFFICIENT: voices speak but independence is not established; SINGLE stays 'one class can speak' | grounded |
| F26 | K14's split labels the residual `pathology`: pathology by elimination | K14 | ARCH §5.9 Table 5.14 l.4172, order l.4174–4185, mechanism l.4222–4223; THEORY Law 4 (notes §F26) | pathology only when Table 5.14's positive conditions all hold, else undetermined; the class routes to recall and establishes nothing | grounded |
| F27 | K20 searches lines only inside confirmed edema, so a fracture without detected edema is unreachable; OA marrow-lesion scope stays unresolved | K20 | ARCH lens 15 (Tables 2.8a/b); THE_KNEE §2 change 3; ARCH l.1096 (notes §F27) | line lens questionless over bone, with edema context as a field; OA marrow-lesion scope to the founder | grounded |
| F24 | K22 admits the stability key by discrimination (phantoms above `checking` normals) | K22 | ARCH §6.1.4 l.4403–4406 and §4.3 l.2792–2793 prescribe the phantom-ordering admission; the No Popery law (founder, global) forbids seating by discrimination; ARCH l.4427–4430, l.2779–2781 (notes §F24) | s takes its place in ARCH's key order on ARCH's structural argument, read against phantoms of its size and zone; phantom ordering and |z|-redundancy reported, never gating; the conflict is reported to the founder | grounded |
| F25 | K25's null claims "no shared answer by construction" across studies, which is false | K25 | ARCH §5.5 l.3639–3654, l.3735–3736, l.3783–3786; THESIS §7.1 l.1411–1413, §7.4 l.1518–1521, §7.6; THE_KNEE §2 change 6 (notes §F25) | null = bank-wise exchange within (zone class, regime, visibility pattern): preserves each bank's marginals, breaks co-occurrence; label-free; hard negatives → near-miss censors | grounded |
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
| F19 | K03's oracle contract: a question field and truth polarity; localization vs study-level gold; report silence; `oracle_unavailable`; clustered bounds | K03 | ARCH §6.2.5 Table 6.3 l.4685–4692 and rules 1–5 l.4697–4709; §6.3 l.4713–4724; §5.3 l.3417–3419 (notes §F19) | a recognition table cell per (object or study, question, oracle); oracle_unavailable; G grades study-level only; bounds over studies, the independent unit | grounded |
| F20 | panels: N's relation to T/R/G; R held out of every store; K23's building role; R used for design becomes development evidence | K03, THE_KNEE §5 | ARCH Table 6.3 (R 'held out of every store'), rule 1 l.4698–4700; §6.3 l.4722–4744 (R replicates direction) (notes §F20) | R out of every store, references to maps included; R's objects are never inspected to design a change, only its triples read | grounded |
| F04 | K12 calibrates lens metrics before K13 computes them | K12, K13 | | | open |
| F05 | K12 consumes K14's question rules without depending on K14 | K12, K14 | | | open |
| F07 | K20 needs confirmed edema while K23 depends on K20 | K20, K22, K23 | | | open |
| F08 | K17 needs keys built in K21 and K22; an early emission schema with explicit unavailable keys | K17 | ARCH §6.1.3 l.4337–4373; §6.1.4 l.4406 ('Until then the sequence skips it') | K17 declares every key early; an unbuilt key is skipped with key_unavailable:<name>, never filled | grounded |
| F09 | K24 is selectable after K11 but needs first light (K18) | K24, README | | | open |
| F10 | acceptance is prose, with no commands, fixture digests or numeric expectations | all | | | open |
| F11 | replay: backend equivalence vs an authorized behaviour change; recursive staleness; selected versions; K27 skips an unselected K24 | K02, K18, K27 | | | open |
| F12–F15 | false properties: hashed folds "balanced within one"; tercile ties; longest gap not additive; binomial bounds not monotone | K03, K12, K20 | | | open |
| F41 | K06: report-negative coverage; independent adjudication of parser errors | K06 | | | open |
| F45 | K13: acquisition-specific evidence; uncertainty propagation | K13 | | | open |
| F47 | K17: comparable evidence ordering | K17 | ARCH §6.1.4 l.4388 ('each key is compared only with itself across studies'), Table 6.1 keys l.4399–4425; THE_KNEE §2 change 9 | keys compared only like with like; a study lacking a key is ordered only by the keys it shares (K17, to edit) | grounded |
| F54 | K27: version-aware replay; conditional score estimates | K27 | ARCH §6.1.5 facts 1–3 l.4470–4486 | K27 reports the score as ARCH's conditional identities: the open shares and the decided accuracy per finding, never one number | grounded |

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
| F38 | K22's escalation cannot reach the Mac Pro from offline Kaggle | K22 | ARCH §4.3 l.2759–2764 (R4 and R5 only on escalation); THESIS §12.6; AGENTS override 6 | in the kernel an escalation runs inside the kernel's own budget or is skipped as escalation_unavailable; the Mac Pro is build-time only | grounded |
| F39 | performance evidence needs work and byte accounting, not seconds alone | several | | | open |
| F55 | K00: reconcile the authorities; executable acceptance | K00 | | | open |
| F56 | K02: acceptance manifests, dependency-freshness checks, explicit layer contracts | K02 | | | open |

## Reading log

The sections of ARCH and THESIS read first-hand during this revision, with their line ranges. Reading is never
delegated (R4).

| when | source | lines | sections |
|---|---|---|---|
| 2026-10-02 | ARCH | 490–617, 875–1016, 1237–1354, 1521–1595, 2024–2206, 3187–3527, 4517–4746, 5226–5285 | §1.7–§1.8; §2.3; §2.8; §3.1; §3.3.9–§3.4; §5.1–§5.3; §6.2–§6.3; Glossary C–L |
| 2026-10-02 | THESIS | 739–797 | §4.4–§4.5 |
| 2026-10-02 | ARCH | 3600–3796, 4145–4234 | §5.5; §5.9 |
| 2026-10-02 | THESIS | 1403–1610 | §7.1–§7.7 |
| 2026-10-02 | ARCH | 2661–2795, 4300–4517 | §4.3; §6.1 |
| 2026-10-02 | ARCH | 1016–1081, 2795–2929 | §2.4; §4.4 |
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
## Grounding notes (first-hand; line numbers are `docs/KNEE_ARCHITECTURE.md` unless named)

### §F01 — intensity units
- **The unknown is named in the law.** §2.3 l.880–882: "S ≈ g · PD · (1 − e^(−TR/T1)) · e^(−TE/T2), where g is
  the series' unknown receiver gain." Consequence 4 (l.909–910) claims "Signs survive the unknown gain, since
  each series is read against the reference for its own series type". That holds only if the deviation is
  computed in gain-free units, which nothing in the raw path supplies. Codex's counterexample stands: a series
  at twice the typical gain deviates bright everywhere.
- **ARCH's own remedy is a per-series gain pinned on reference tissue.** Table 3.5 (§3.3.9, l.2030): "Unknown
  receiver gain | absolute intensity means nothing across series | ratios; one γ per series, pinned on
  reference tissue". The gain specialist is §3.3.3, l.1853: "γ_s | a reference tissue read in the series,
  against its recalled regime value: muscle everywhere, marrow fat where unsuppressed | … | γ_s with its spread;
  whether two reference tissues agree | no normal reference tissue in the field". Its zones: l.1859 ("muscle
  and subcutaneous fat. These are …") and §2.10 l.1478.
- **Where the law does not run, ARCH falls back to the BUILT raw path.** §3.3.9 l.2041–2042: "Where the law
  cannot run, a series is read as today: KneeDiff on raw intensity against its series type's reference
  (BUILT). The header records each series' path." Since the accord made the law optional (K24), the raw path
  is now the default, and it needs the same gain contract.
- **Per-series normalizers.** §3.1 l.1574–1592: `n4_correct`, `normalize_intensity` and `histogram_match`
  each multiply one series by its own factor field, which "destroys what layer 1 reads, the ratio of two
  series at one place". So layer 1 reads stored values, and "N4 is applied, if at all, only to the
  proton-density map after the solve". §3.4.1 l.2093–2110, LADDER as ARCH quotes it: v2's N4 and p2–p98 left
  "regional intensity offsets 4–6σ", a "contrast-ratio mismatch that p2–p98 scaling cannot reconcile";
  histogram matching was "blind to which tissue was where". §3.4.2 l.2135: "Histogram matching should become
  unnecessary".
- **THEORY II.1 (binds):** N4 is "the prerequisite for a clean subtract across the diverse international
  scanner/protocol mix".
- **Disposition.** Two representations per series, never merged:
  - the stored values (RescaleSlope and Intercept, plus any vendor scale), kept for K24's law;
  - the comparison representation for the population axis: stored ÷ (N4 field × γ_s).

  The rules:
  - γ_s is ARCH's gain specialist, lifted out of the law and run on every series. It reads muscle everywhere and
    marrow fat where unsuppressed, against the recalled regime value. Two reference tissues are compared, and a
    series with no normal reference tissue in the field is silent on the population axis
    (`gain_unpinned`).
  - There is no p2–p98 scaling and no histogram matching (§3.4.1).
  - The detrend stays a measured question (§3.4.2).
  - Each series records its path (§3.3.9).
  - Reference-tissue zones (muscle, subcutaneous fat) join K08's atlas, per §2.10 l.1478.
  - Chapters: K07 (the N4 field as a measured nuisance; stored values kept), K08 (the reference-tissue zones),
    K09 (references in γ-normalized units), K10 (z in the same units).

### §F02 — tissue identity against change
- **The signature is a tissue-level pattern, not a deviation.** Table 2.3a (§2.3) names tissues by each
  contrast's sign "from the equation", and §2.3.2 l.989 says "The Signature lens … reads only signs. It needs
  co-registration and does not need g." Only a level read within the series, against that series' own
  reference tissue, needs no g. The tissue level is named against muscle: l.3866 "T1 brighter than muscle (the
  T1 tissue level; lens 3's signature)", and l.1096 likewise.
- Table 2.8a lens 3: "the pattern of contrast digits, named by the equation's signs for each series' TR, TE and
  TI". Its open quantity is the correspondence radius.
- **Change is a different reading.** §3.4.3 l.2158–2160: "A place is black when every identified parameter lies
  within the licence (|z_p| below the threshold) and its signature word is its zone's normal one." There are
  three readings: the place's tissue word, the zone's normal word (measured on normals) and the population z.
  §2.3 consequence 1 (l.900–901), "A meniscus turning + on FS holds fluid", is a change of *word*.
- **The book's error.** K10 computed the word "from the deviation signs across the co-registered series",
  which merges identity and change. A healthy ligament then never reads `fibrous` (Codex).
- **Disposition (K10).**
  - The tissue level per series is a three-way digit of the γ-normalized signal against the series' own
    reference tissue. Its middle is set once per the template's middle rule (THESIS §6.2).
  - The tissue word comes from Table 2.3a's expected signs per timing class.
  - The change reading has two parts: (a) the word against the zone's normal word, measured on normals; and
    (b) z per series.
  - K19 and K20 read the tissue word (identity). K13 and the agencies read change.

### §F27 — the line lens and edema
- **ARCH reads lines in committed edema.** Table 2.8a lens 15 (l.1305): "Line | L4 fracture | committed edema,
  with its halo out (layer 6; Part 4 §4.4); T1, FS | the length of a linear dark component reaching cortex".
  Table 2.8b row 15 (l.1331): "for only (an unseen line in dense edema at 3–4 mm is not "no fracture") |
  nothing on its own; "a fracture lies within edema" censors lines outside edema | no committed edema".
- **But the accord amended that censor.** THE_KNEE §2 change 3 lists Table 5.10's "a fracture lies within
  edema" as one of the passages it amends: only physical impossibility is absolute.
- **So:**
  - The line lens measures linear dark components reaching cortex over the bone subregions. It knows no
    question.
  - It records each line's edema context (inside a committed edema object, inside a provisional one, or
    outside) as a separate field.
  - The Monty Hall reading inside committed edema (§4.4; THESIS §4.6) is kept as context. It is no longer a
    gate.
  - The marrow agency holds the sign.
- **The OA marrow-lesion scope.** l.1096 lists "An OA marrow lesion: under cartilage loss, in a narrowed
  compartment" as a confounder of Contusion. Whether the official Contusion label includes such lesions is
  label scope, a founder matter under AGENTS law 6. The book keeps it unresolved and measures how G treats it.

### §F23 — no answer rests on one voice
- **The Glossary is the rule.** ARCH l.5233–5234: "Concurrence. Agreement among independent voices: the only way
  a lesion-object is committed or an answer assigned; refused on disagreement (THESIS §4.4–§4.5; Part 5 §5.3)."
- **SINGLE yields a take, not an answer.** Table 5.5 l.3449: "SINGLE | one class can speak | a take carrying
  "single voice" (Part 4 §4.4), only where the reading passes its own persistence test". That take is the loop's
  object.
- **"So does every answer built on them" (l.3505–3507)** describes the one-series build of that day ("Today.
  With one series per study…"). It is not a licence: Table 5.1 rule 2 (l.3236) and the Glossary forbid an answer
  from one voice.
- THESIS §4.4 l.741–742: truth is "assigned where independent readings agree, refused where they disagree,
  never by one tuned pipeline or one voice". l.747: "A lens alone at its depth keeps every body". It keeps them;
  it does not decide them.
- **Disposition (K16).** PRESENT needs a concurring object. ABSENT needs concurring exclusions (Table 5.5:
  CONCUR, "the exclusion stands"). A SINGLE take keeps the object and writes the word ABSTAIN with cause
  `single_voice`. First light abstains widely, and that is its honest finding (R1).

### §F06 — independence is measured before agreement counts
- **ARCH puts the gate at recipe step 7.** §6.2 l.4517–4521: "*Measure the substrate* on the domain's own data
  before anything is taught: … and whether the views' errors are independent" (THESIS §13.1, step 7).
- §6.2.2 defines the gate. It reads each series' reading of a finding's host zone on studies with an oracle,
  and computes φ and κ per pair of series types, each with its count and bound. It emits the gate table and the
  κ map. §5.3 l.3415–3425 gives the same, over three measuring sets: phantoms, held-out true normals and gold.
- **The bar is the founder's.** ARCH §6.7 item 8 (l.5109–5110): "GenomeVault's max φ < 0.25 … is adopted
  provisionally until the founder sets the knee's own bar, written before the run". THE_KNEE §2 change 7
  dropped the imported bar ("no imported bar; "insufficient" where independence is not established"). So until
  the founder writes a bar, no pair counts as two voices, and no answer is assigned.
- **Disposition.**
  - The gate runs as soon as per-series readings exist (after K13), on P, N and G. It is re-run when K20 adds
    the structure questions.
  - It is no longer deferred to K23. K23 keeps the hardness map and the κ map as a lens (§6.2.2, "a failed pair
    is not discarded").
  - This breaks the K15/K16/K20 ↔ K23 bootstraps.
  - **Founder:** the bar (ARCH §6.7 item 8).

### §F03 — witnesses by acquisition, with their sources
- ARCH §5.3 l.3408–3413: "Independence is therefore per question … series whose errors the gate cannot
  separate count as one voice."
- l.3487–3490: "Readings concur only where they land one lesion in one patient-space place."
- l.3499–3503: the record keeps "each series' entitlement … its word".
- The joint signature is a law check. §2.3 consequence 3 (l.906–908): "*Cross-contrast consistency is a
  check.* All the series covering a place must name one tissue change." Table 5.1 rule 3: law checks support
  and never establish.
- **Disposition (K10, K13, K14).**
  - Every reading carries its complete source set (series ids).
  - Voices are per-acquisition readings: each series' tissue level and z.
  - A reading computed from several series is one dependent reading, whose sources are all of them. It can
    never concur with its own sources.
  - The joint signature word is a consistency check: it supports, never votes.

### §F19 — the judge's oracle contract
- **The panels.** ARCH Table 6.3 l.4685–4692: G "establishes", N gives negatives and nulls, R is "a large,
  noisy second oracle", and P is "label-free tests".
- **The rules.** Rules 1–5, l.4697–4709: one role per study per measurement; no self-comparison; gold only in
  rotation; "Every rate with its count and bound. A count that cannot bound a rate reads "insufficient", never
  zero"; bars before runs.
- **The read.** §6.3 l.4722–4724: per finding, the triple identified, abstained and wrong, "with its bounds and
  never summed".
- **Localization.** §5.3 l.3417–3419 grades a localization only by "gold, where a localized call fixes the
  place". The competition's G is study-level, so localization is graded only by P (truth by construction) or by
  a localized report call (R, T).
- **Disposition (K03).**
  - A cell is keyed (study or object, question, oracle kind). The oracle is one of `G_study`,
    `report_localized`, `phantom`, `none`. With `none` the cell reads `oracle_unavailable`, never wrong.
  - Report silence is `oracle_unavailable` for that question, never a negative.
  - Every bound counts studies (the independent unit), never voxels or objects within one study.

### §F20 — R is held out of everything
- Table 6.3 says R is "held out of every store", and rule 1 says "One role per study per measurement".
- §6.3 l.4744: R is used to replicate a triple's direction ("replicated on R").
- **Disposition (K03, THE_KNEE §5).**
  - R is excluded from every store: references, templates, quantizers, nulls, maps and case memory.
  - Its objects are never inspected to design a change; only its triples are read.
  - Changes are designed from T and from G read in rotation (§5.6, §6.2.5 rule 3).
  - K23's building role is named.

### §F26 — the split's `pathology` is positive and routes only
- ARCH Table 5.14 (l.4172) gives Pathology positive conditions: "a lawful signature, constraints holding, a
  deviation where the population is tight, and no variant law explaining it". It goes to "its agency's
  recall".
- The order (l.4174–4185) is constraint, then consistency, then variant, then "*Pathology.* What remains goes to
  its agency."
- The mechanism (l.4222–4223): "Only pathology bears on a finding". It bears on one; under Law 4 only an agency
  decides.
- **Disposition (K14).**
  - `split` returns `pathology` only when all four of Table 5.14's conditions are read positively.
  - An object that clears steps 1–3 without them is `undetermined`. This is the "unexplained" type of Table
    1.7, kept as a finding.
  - Neither class establishes anything. Both route to recall and the agency, and the cause travels with them.

### §F25 — the trust radius's null
- **ARCH as written.** §5.5 l.3644–3651: "The chance population: profiles … that cannot carry the bucket's
  answer, by construction. For a bucket of a finding, these are held-out true normals". "The statistic: each
  member's cosine with its *nearest* case". "The radius: the least level no member reaches, written … before
  any run it judges". l.3652–3654 charges the bucket for its size. l.3735–3736: "Levels are set against chance,
  on populations that cannot carry the answer, before the run." l.3785–3786 admits the failure: "A "normal" with
  an unreported lesion raises a radius".
- **The accord amended this.** THE_KNEE §2 change 6 amends §5.5's "trust radius set to exclude every
  opposite-answer example". Its replacement: "a specified null mechanism (what it preserves, conditioned on
  visibility and context, with bucket size accounted for); hard negatives become near-miss censors".
- **The book's K25 replacement was false.** Cross-study pairs "with no shared answer by construction" share
  answers at the prevalence rate (Codex).
- **THESIS grounds a label-free null.**
  - §7.1 l.1411–1413: cases are "compared one by one, never summed …, since a sum would lose which readings
    occurred together in each case". What a case carries is the co-occurrence of its readings.
  - §7.4 l.1518–1521: the radius "lies where the resemblances chance alone produces end, and it is set on real
    data. It says when a resemblance is not an accident".
  - §7.6: a confirmed failure that resembles a case is a near miss, and writes a censor.
- **Disposition (K25).**
  - **The null mechanism.** Within a stratum (zone class × regime × visibility pattern, meaning the set of
    non-silent banks), each bank's row is exchanged at random among real objects of that stratum.
    - It preserves each bank's marginal distribution and the visibility pattern.
    - It breaks the co-occurrence of readings within one object.
    - So no null profile can carry any answer, by construction, without a label.
  - **What chance reach bounds.** The statistic is each null profile's cosine to its nearest case, which
    charges the bucket's size. The radius is the least level at which the chance-reach rate is at most a
    rate written before the run, computed on one half of the null draws and checked on the other.
  - **Opposite-answer examples** are never the null. A true normal that reaches a case is a near miss for
    THESIS §7.6, and so a censor candidate or a founder's sheet (ARCH l.3785–3786).
  - **Its calibration is measured, not tuned.** The rate at which real `null`-role normals reach cases is
    reported beside the shuffle's rate. An excess names structure the shuffle broke, which belongs in the
    stratum key (Law 5), and it never moves the radius.

### §F24 — stability's admission into emission (ARCH against the No Popery law)
- **ARCH prescribes the admission test Codex rejects.** §6.1.4 l.4403–4406: "s becomes a key only once it passes
  the information test … The test is run here without labels: where the keys above s tie, s must order planted
  phantoms above true normals. Until then the sequence skips it." §4.3 l.2792–2793 has the same: "s enters
  emission only if it adds to the rank already given by |z|".
- **The founder's law forbids it.** No Popery (global CLAUDE.md, 2026-09-17; house `no-popery.md`) names
  "seating decided by a member's discrimination on one query" as a tell. Ordering planted phantoms above normals
  is discrimination on one query (lesion or none). By AGENTS → *Where truth lives*, the founder's words outrank a
  derived canon document. Book K13 §9 already follows the law ("each sane value reported, none selected").
- **ARCH's structural argument places s anyway.** l.4427–4430: "The keys run from the evidence least likely to
  be jointly wrong to the most likely: independent series are different evidence; stability is the same
  evidence surviving a step either way; H is one statistic of one reading." The same section names the known
  inversion: s inverts for thin lesions, which is why s is read "against phantoms of the same size and zone,
  never as an absolute" (l.2779–2781).
- **Disposition (K17, K22).**
  - s holds the second key on that structural argument.
  - Its digit's middle is set once on the teaching studies' committed readings (THESIS §6.2), and s is read
    against phantoms of its size and zone.
  - Two things are *reported* and never gate: whether s orders P above N where the keys above tie, and whether s
    is a function of |z| (the redundancy ARCH l.2784 names).
  - **Reported to the founder:** ARCH and the No Popery law conflict here, and the book follows the law.

### §F08 and §F47 — early keys, and comparison only like with like
- ARCH §6.1.3 lists what emission reads: the decision word, the voices, s, H and σ. H comes from §4.5 (K21) and
  s from §4.3 (K22), both built after K17.
- ARCH already has the skip semantics, l.4406: "Until then the sequence skips it".
- **Disposition (K17).** Every key is declared at K17. A key whose chapter is not yet accepted is skipped and
  recorded as `key_unavailable:<name>`, never filled with a default.
- Under §6.1.4 l.4388, "each key is compared only with itself across studies". So a study is ordered by a key
  only against studies that carry it. With THE_KNEE §2 change 9 (witness-set comparability), a key whose
  witness sets differ is not compared.

### §F54 — the score, stated conditionally
- ARCH §6.1.5 gives exact identities. Fact 1: AUC = 1 − ½·(o₊/n₊)·(o₋/n₋) when every decision is right. Fact 2
  gives Q4's stake. Fact 3: abstention after a wrong decision never costs.
- **Disposition (K27).** The expected score is reported through these identities: per finding, the open shares
  and the decided accuracy with bounds. It is never one number.

### §F38 — the kernel cannot reach the Mac Pro
- ARCH §4.3 l.2759–2764 runs the expensive families R4 and R5 "only on escalation". The kernel has no internet
  (AGENTS override 6).
- **Disposition (K22).** In DEPLOY an escalation runs inside the kernel's own budget, or is skipped and recorded
  as `escalation_unavailable`. The Mac Pro serves build time only.

### §F18 — post-checks under masks
- **ARCH's take subtracts the law's contribution.** §4.4 l.2832–2836: "The knee's take removes what the object's
  law says the object contributes. It leaves the population's expected value". The post-take check (l.2850–2861)
  then reads a ring as "a same-sign deviation hugging the take's border", a hole as "an opposite-sign deviation
  inside the footprint", a lobe and an impossible patch.
- **The accord replaced default subtraction with masks.** THE_KNEE §2 change 4: reversible masks; "subtraction
  only under a stated contribution law". Under a mask nothing inside the footprint changes, so a hole cannot
  form, and an impossible patch is a property of a subtraction (Codex).
- **The slice profile.** §2.4 consequences 2–3 (l.1041–1046) give partial volume and the header's SliceThickness
  and SpacingBetweenSlices. The headers carry no profile shape. ARCH bounds the halo "no wider than the slice
  profile through-plane" (l.2915–2916), and "the slice geometry in the headers sets the partial-volume rim"
  (l.2863–2864).
- **Disposition (K15).**
  - **Mask mode (default):** ring (outside the footprint and halo) and lobe. Hole and impossible are recorded
    `not_applicable:mask`.
  - **Contribution mode:** only where Table 4.6 states the law (an effusion's partial-volume rim; a Baker's
    wall). The contribution is subtracted inside the halo, and all four checks run as ARCH writes them.
  - **The profile assumption:** a rectangle of width SliceThickness, declared and measured on phantoms (ARCH
    l.2920–2923: ring, hole and lobe rates). Where SpacingBetweenSlices ≠ SliceThickness, the halo takes ARCH's
    bound and no subtraction is made.
