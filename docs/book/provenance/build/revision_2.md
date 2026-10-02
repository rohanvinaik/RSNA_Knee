# Revision 2 — the compute design, and answering the second fresh read

**Why this file exists.** Two inputs, one revision:
- **The founder's engineering rulings** (16:08Z onward, and 17:14Z–17:32Z; `../../FOUNDING_PROMPTS.md`):
  - read the tool pointers;
  - language-specific modules from the start ("C/C++ for memory management, cache hot vs cold management, Rust
    for speed");
  - Radon kept as an independent instrument;
  - no operation exempt because it looks cheap ("Suit and tie, not just "not naked"").

  These are carried by chapter K02b and laws 14 and 8.
- **The second fresh Codex read** (`codex_fresh2_answer.md`): YES WITH AMENDMENTS; K16 and K25 disagree.

The rules are revision 1's: grounding first-hand in ARCH, THESIS or a manifest source; the lead reads; resume
from this file after a compaction by re-reading the cited lines. Status is `open`, `grounded` or `done`.

## After the second compaction (22:42Z): every disposition re-derived

The *disposition* column of the findings table below was drafted before the compaction from my paraphrase of
Codex's answer. A note written to guide a fix is a lead, never a premise. So each finding is re-derived from:
- Codex's verbatim answer (`codex_fresh2_answer.md`, read whole this session);
- the sources it touches, read **whole, by section**, this session.

A search hit or a line number only locates. A row is `done` only when its disposition has been rewritten from that
reading, and its grounding cell names the sections read. Where a claim is not settled it carries a code, as
`context-handling.md` asks: `unresolved_prerequisite`, `conflicting_definitions` or `stale_source`. The founder
(22:42Z): "make sure you've actually read it, directly, in this post-compact session"; (22:52Z) "post-compact
summaries [are] rather insufficient for design work".

The stopping rule for the fresh reads is the founder's, 22:42:24Z. Stop when Codex "no longer tells you anything
substantially useful", or when "you know how to properly and completely address what it is saying", or when "the
answer is something that's best left to operator intent". Codex is for stress-testing, one voice and never a
verdict. A finding the theory contradicts is answered from the theory and not applied.

### The K14 edit, struck

Immediately after the compaction, G01's draft disposition was written into K14 (uncommitted) from the summary,
before anything was re-read. Read against the sources, it does not hold. It was reverted, and the diff is kept in the
session scratchpad as `K14_struck_edit.diff`. The reasons, each from a section read whole:
1. **It invented what "for" means.** It defined "for" as "beyond its healthy interval … at a coverage level written
   before the run". ARCH defines a lens's "for" reading by its open quantity, "chosen from a few physically sane
   values". Where several are sane, the choice is measured "by the rate of 'for' readings on held-out true normals,
   at a fixed detection rate of planted phantoms" (ARCH §2.8 rule 2), and on those normals "any 'for' reading is
   false" (rule 8). The edit's own first bullet ("at which sane value") contradicts its function signature.
   `conflicting_definitions`.
2. **It keyed the rules to "the twelve findings' questions".** ARCH's committee and gate are per question at a
   zone. The committee record is kept "for each study, zone and question", and the examples are measurements:
   "Two sagittal series fail together on surface contact. Two fat-suppressed series fail together on edema"
   (§5.3). K13a gates "every question the zone lenses can speak to" (K13a §1). The twelve findings are the
   agencies' decisions (§5.2), not the gate's questions.
3. **It moved body content ahead of the gate the body reads.** ARCH puts the reading of a lens as for or against
   in the commit: "Only the commit reads a lens as for or against" (§2.8 rule 1). THESIS §4.5 says the same of
   cells: "only the commit reads a reading as for or against". The accord gives the signs to the agencies
   (THE_KNEE §2 change 6). The edit placed finding-level signs before K13a, without making K13a depend on K14, and
   then fed the gate's own measurements back into the rules (K13a, K23). That is the circularity Codex warned
   against: "those rules must not consume the gate they help measure".
4. **It merged orthogonal with silence in the outcome.** ARCH Table 5.5's ALL SILENT is "no class is entitled",
   routed to Tier 2, the residue type "a question every series is blind to" (§5.1). An entitled reading that bears
   neither way is orthogonal, "not silence: the coverage bank records the read" (§3.5.3, "Three zeros, kept
   apart"). The edit sent entitled-orthogonal committees to ALL_SILENT. `conflicting_definitions`.
5. **Smaller defects.** "ABSENT needs CONCUR on concurring … exclusions" is garbled, and its "(K26)" names the
   wrong home for recall, which is K25. Its sources were cited before any of them had been read this session.

What survives as a question for re-derivation: Codex's G01 and G05 points themselves, below.

### The global changes (SquishOS `0cd3f4c`…`d94d04a`, 2026-10-02), and what they change here

| id | the change at its source | what it changes here | status |
|---|---|---|---|
| H1 | context grounding (`context-handling.md`; global: "A search hit locates evidence; it never authorizes an explanation") | Groundings are read whole by section (`mdq '# <heading>'`, or the section by offset), never as a line number with a few lines around it. Each claim is recorded with what established it and a code. The manifest's hash proves identity, not authority: the canon passages the accord amends are superseded (THE_KNEE §2), whatever their hash | applied in this file; CLAUDE.md's compaction line |
| H2 | completeness over skipping (TOOLKIT.md; `code-verification.md`): a tool is left out only when it conflicts with the house or does not apply. Added: Pyright beside `ty`, mutmut beside Detective, Radon's numbers, asv, structlog, OpenTelemetry, StrictDoc, Nox, LibCST, Atheris, TLA+, ASan/UBSan, Compiler Explorer, SymPy, NetworkX, Lark, Matplotlib, and the process instruments | K02's dependency groups and K02b's instruments table are revisited under the new rule. "One owner per role" is replaced by "one owner per tool", with each tool's claim. Candidates where the claim applies: sanitizers for the C library; Atheris for the decoders and FFI boundaries; asv for budgets across history; structlog for the kernel's run record; SymPy for K04's width proofs; NetworkX for the dependence and chapter graphs; StrictDoc for chapter-to-code tracing; mutmut and Pyright as second readers | open |
| H3 | Detective runs from the environment that runs the target's suite (`detective-protocol.md`, `d94d04a`). A bare `python3` here is miniconda's base, which auto-loads eight undeclared pytest plugins that change outcomes | the `just detective` wrapper names the project's VERIFY interpreter explicitly, never a bare `python`/`python3`, and proves resolution once per session (`~/tools/Detective/AGENTS.md` → *Standing invocation*). AGENTS override 1 and K02 | open |
| H4 | the verdict-CLI hooks see `python -m Detective.cli`, `uv run`, `$( … )` and the other spellings (DESIGN_LEDGER S8, resolved). Residue: a `$VAR` set outside the command; a capture filtered in a later call | CLAUDE.md's "the filter hooks do not see `python -m Detective.cli`" and AGENTS override 1's sentence are stale: verify with the hook's own payload, then correct. The wrapper keeps its log for identity, complete output and exit status. The offer to extend the hook is withdrawn, since it was done at its source | open |
| H5 | Antigravity as a second reader across model families (`antigravity-consultation.md`): "When a second opinion matters, give Codex and Antigravity the same prompt: agreement across model families is evidence, and disagreement is a question for the operator" | fresh read #3 goes to Codex and to Antigravity (Gemini 3.1 Pro, high) with the same prompt. `consult-budget` is run before and after. The prompt's size is checked against the argument limit before the call | open |
| H6 | no AI attribution on commits or pull requests (global) | none to undo: 0 attribution lines in the 42 unpushed commits (checked 22:5xZ). It is a global rule, not restated in this repository | done |
| H7 | the fourth build ethos, instruments on a bench (spine/00): one command, one observation, what its output licenses and no more, a named code and the next command | K01's characterization, K02's `just` verbs and K03's harness are specified as instruments: each prints a named code and the next command | open |
| H8 | Codex reads at most 32 KiB of AGENTS.md, global and project together (`context-maintenance.md`) | measured: `~/.codex/AGENTS.md` 7,378 bytes plus this repository's `AGENTS.md` 14,108 bytes come to 21,486 bytes, within the limit. (The git root is this directory, so `Kaggle_Killer/AGENTS.md` is not read.) Re-measured after each AGENTS.md edit | done |
| H9 | TOOLKIT's "skip Radon" line is gone at the source: Radon's numbers are information | the pending offer to fix it is withdrawn | done |

## The compute design (the founder's rulings)

| id | change | grounding | status |
|---|---|---|---|
| C1 | K02b: language by computation shape; the compute contract; hot and cold, one-hit, in memory; the kernel's budget as a constraint and never a licence; the instruments table; the per-operation plan; the Rust crate and the C library from the start | DETERMINISTIC_SICP §1.1, §3.1, §4.1, §6–§8, §12; THESIS §12.4–§12.7; global `performance.md`, `code-verification.md`; SquishOS TOOLKIT.md; ARCH §2.4, §3.1, §3.2.6, §3.5.5 | done (`c343364`, `ad00394`) |
| C2 | the house tools restored (pyinstrument, line_profiler, Hamilton, beartype and jaxtyping, Codeflash, `cython -a`); Radon kept | `performance.md`; founder 17:29:45Z and 17:30:14Z | done |
| C3 | law 14 / AGENTS law 8, "suit and tie" | founder 17:32:09Z and 17:32:17Z | done |
| C4 | K02b's plan carried into each kernel chapter's §5 (K01, K04, K05, K07, K09, K10, K11, K13, K13a, K18–K25); K09's C order statistics and K25's Rust scan from the start | K02b §3.6 | open |

## The second read's findings

| id | finding (Codex, second read) | chapters | grounding read first-hand | disposition (a pre-compaction draft until re-derived) | status |
|---|---|---|---|---|---|
| G01 | the measurement-to-decision bridge is missing: K13a needs signed per-question error indicators, but the signs arrive in K16 | K14, K13a, K16 | ARCH §5.3 (the committee is per question); Table 2.8b ("Counts", "Rules out" per lens); Table 2.5 (the law term per finding); §4.1 (an exclusion's four conditions); THE_KNEE §2 change 6 (agencies hold the signs) | **struck** (see *The K14 edit, struck*). Was: K14 defines each finding question's signed-reading rules, "for" meaning beyond a healthy interval, consumed by K13a | open: re-derive |
| G02 | K16 DISAGREE: "a confirmed pathological object in a finding's zone" is no finding-specific warrant; Table 5.2's column is "Its check (supports only)" | K16 | ARCH Table 5.16 (the agency's word per study and finding), §5.3, Table 5.2 | PRESENT for F = CONCUR of entitled independent acquisitions' signed readings on F's own question (G01), the object being pathology under the split. ABSENT = concurring observation-qualified exclusions on F's question. Checks support only | open: re-derive |
| G03 | K25 DISAGREE: the bank exchange does not build profiles that cannot carry an answer (one informative bank survives) | K25 | ARCH §5.5 l.3644–3651 (the chance population: held-out true normals for a finding's bucket); change 6 ("what it preserves … with bucket size accounted for"); THESIS §7.4 ("set on real data") | return to ARCH's population: N's `chance` role, profiles of the same zone class, regime and visibility pattern. The radius is the least level at which the nearest-case chance-reach rate is at most a rate written before the run, never "the least level no member reaches", so one normal cannot set it. Split halves; the population's impurity (K09's founder sample) stated beside it; normals that reach become near-miss candidates | open: re-derive |
| G04 | K13a reinstated "κ against reports is an upper bound", which change 7 amended | K13a | THE_KNEE §2 change 7 (it amends §6.2.2's "κ against reports is an upper bound") | removed: report-based κ is reported with its bias named, both directions possible, never as a bound | open: re-derive |
| G05 | K14's outcome function is not total; pairwise dependence is no equivalence relation; dissent must not vanish | K14 | ARCH Table 5.5; §5.3 ("series whose errors the gate cannot separate count as one voice") | outcomes over *sets*: CONCUR needs a set of at least two entitled voices agreeing, every pair `independent_measured` (and multiway once K23 measures it), with no entitled dissent anywhere, dependent or not; an exhaustive table over for, against, orthogonal and silent × dependence status | open: re-derive |
| G06 | intensity contract open: the recalled regime value's gauge; γ as log or divisor; the variance mixes median and mean σ²_meas; the zero denominator | K09, K10 | ARCH §3.3.3 Table 3.3 (gain "against its recalled regime value"); Table 5.9 (regime values: "the median of the regime's cases at read time"); §3.3.9 Table 3.5; §3.4.2 | γ_s multiplicative (ARCH's log gain is its log); regime value = the median of the `reference` members' muscle levels on N4-corrected stored values; x̃ = stored ÷ (N4 × γ_s); one σ²_meas statistic throughout (the median); a zero denominator reads `silent:zero_variance` | open: re-derive |
| G07 | identity collisions: free fluid and marrow edema share (+, −); cortex and fibrous tissue are both dark; spatial bias between a voxel and distant muscle | K10, K19, K20 | ARCH Table 2.3a ("Marrow edema … + (in bone)"): the zone is part of the signature; THE_KNEE §2 change 2 (identity from patient anatomy) | the tissue word is matched *with its zone class* (bone versus soft tissue; cortex shell versus band), so fluid and edema separate by place, as the table itself does. Levels are read on x̃ (N4-corrected), never on stored values against distant muscle | open: re-derive |
| G08 | acceptance reaches forward (K09 on P and z; K10's test deferred to K14; K15 needs line, neck and lining before their readers) | K09, K10, K15, K20 | ARCH §6.6.3 ("Each phase is measured before the next begins") | each acceptance uses only its dependencies' outputs: K09 on synthetic gain and bias; K10's contract test owned by K14; K15's line, neck and lining recovery moved to K20 | open: re-derive |
| G09 | the dependency graph cannot double as the replay graph (perpetual staleness) | K02, README | THESIS §12.6 (kept values keyed by producer, scope and version; a value "stays valid while none of those slices changes") | staleness over immutable artifact versions: construction, consumption and regression replay kept apart; a chapter is stale only when an artifact it consumes changed version | open: re-derive |
| G10 | evaluation units: object counts with a study denominator are not binomial; oracle precedence; contradictory calls | K03 | ARCH §6.2.5 rule 4 | per reported rate, one study-level event per (study, finding, question); object-level counts descriptive, without binomial bounds; oracle precedence phantom > G_study > report_localized; a contradiction reads `oracle_conflict` | open: re-derive |
| G11 | K04 widths: the norms and the final products, not only the dot; i128 overflow; subtraction underflow | K04 | THESIS §12.2 ("widened wherever it could leave 64 bits"); §12.1 ("undone exactly by subtraction") | ‖u‖² ≤ R·C² as well; b²·dot² ≤ 2^20·(R·C²)², which fits i128 only when R·C² < 2^53, else Python int (Rust: checked u128, else refusal); unbundling below zero refuses (`negative_count`) | open: re-derive |
| G12 | THESIS §12.6 cited for behaviour-change records: wrong referent | K02, K18 | §12.6 is about kept values and their invalidation | the behaviour-change record is labelled an engineering deduction, never a THESIS citation | open: re-derive |
| G13 | Tier 0 admitted by a skip-miss rate on "gold finding-bearing zones" (G cannot localize; admission by a discrimination statistic) | K27 | ARCH §5.4 (mandatory pairs by skip-miss on gold and phantoms); §3.2.6 | Tier 0 off by default. Skip-miss is measured on P and on report-localized T calls, never G. Switching it on is the founder's policy, the measurement beside it. Efficiency comes from engineering (law 14) | open: re-derive |
| G14 | K02a: the amendment touches THE_DYAD Laws 2–3 and O4 too; rung-2 off-grammar must be a contract breach (O5); enforceable isolation; candidate-equivalents; staging before install; recertification after edits; a model abstention; held-out tests kept across retries | K02a, typist proposal | CONSTRAINED O5 ("on every rung … a contract breach, never a retry"); THE_DYAD Laws 2–3, 13; Uroboros laws 5–6 | each adopted as stated | open: re-derive |
| G15 | smaller contracts, each answered in its chapter: K05 irregular geometry returned explicitly; K06 mixed-call precedence; K07 two witnesses until K08, local (sampled) against global invertibility; K08 template intensity on x̃; K11 phantom units; K12 checking excluded from calibration, no header in recall; K13 intervals and shared-container dependence; K17 a total ranking algorithm, inventory through entitlement; K18 cohort ranking after the study records; K19 per-series identity; K20 continuity per acquisition; K21 identity before energy (E = 0 with I not identified); K23 multiway estimators, replication as domain; K24 gauges, roles, the selection criterion; K26 censor tests and fold isolation; K27 replay; cross-node checks named concordance; runtime boundary routing in production | per chapter | as each chapter cites | each answered in its chapter | open: re-derive |
