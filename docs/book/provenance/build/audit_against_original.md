# The audit: every change the book makes to the founder's design

## The rule, in his words (2026-10-02; `../../FOUNDING_PROMPTS.md`)

- "We have ZERO evidence of anyhting outside of pure theory. *I* am the authority on what works or doesn't. You don't
  understand the design. Something that LOOKs like it doesn't work well might actually be CRITICALLY important. You
  do not have the authority to change the design *I* built based on a random guess, when you don't know the intent"
- "Make SURE you are not changing anything other than that which is definitevely/provably correct, or warranted by
  my explicit words"
- "Not just this session--EVERY change to the original design"
- "there is LITERALLY not an actual functional codebase that meets the design intent"

## The original design

Unchanged since it was merged; the hashes match `REFERENCE_MANIFEST.toml`, checked 2026-10-02.

| document | commit | sha256 (first 16) |
|---|---|---|
| `docs/KNEE_ARCHITECTURE.md` (ARCH) | `f405450` "the knee-as-law design, layers 0-9" | `d913777da4425a3d` |
| `docs/THEORY_OF_THE_CASE.md` (THEORY; Laws 1–8 bind) | `88752f0` | `59e916c5400d3cba` |
| `docs/FOUNDING_RECORD.md` | `88752f0` | `46fdec436d11d567` |

Also part of it:
- `docs/canon/`;
- the founder's rulings quoted in `docs/canon/SESSION_BRIEF_2026-10-02.md` §3;
- his explicit words in `../../FOUNDING_PROMPTS.md`;
- his standing rules in the global and Kaggle_Killer instructions: No Popery, AI is not ML, the structure-first
  epistemology.

## How each change is classified

- **P, provably correct.** The row carries the proof, of one of these kinds:
  - logic or arithmetic;
  - an internal contradiction in the original, with both passages quoted;
  - an order of work that cannot execute, with the dependency named;
  - a checkable external fact: the competition's literal data and framing, or a file format's semantics. It is
    admissible as a fact and never as a warrant on design. The founder (23:22:50Z): "the competition's literal
    data and framing is acceptable, not implicit warrants on design or conception". So a fact can correct a
    statement of fact, and a design inferred from that fact is N.

  A judgment that something works better, or a prediction of how it will behave, is not proof.
- **W, warranted by his explicit words.** The row quotes them, with their source and time. His 15:24:53Z "your
  recommendations are generally in line with the intent" warrants no specific change. He confirmed this at
  23:22:50Z: "my warrant was general and high-level, not open authority". Codex had his "implicit authority on
  design … It was provisional", and a provisional authority is not run with.
- **N, neither.** The book returns to the original design's text. Where I see a problem in the original, it goes
  to him as a question with the argument beside it, and Codex's point too if there is one. It is never made as a
  change.

The book's engineering (how the design is built: languages, Detective, SAME, tests, the Mac Pro, the typist) is
in scope wherever it alters what the design does. Where it only implements, it is checked against his words on
engineering (15:24:53Z, 16:08:14Z, 17:22:59Z, 17:32:09Z).

## The inventory

### A. The review accord (THE_KNEE §2), ten changes

| id | the change, as THE_KNEE states it | the original it amends | class | proof or quote | action |
|---|---|---|---|---|---|
| A1 | Layer 1 is not the general substrate | ARCH Part 3 §3.3, §3.4 | N | see A1, classified, below | revert to layer 1 as the substrate (§3.1–§3.6) |
| A2 | patient-specific delineation | ARCH §1.5, §2.2 item 2, §2.10 | N | see A2, classified, below | revert to the atlas's zones (§2.2, §2.10) |
| A3 | negative knowledge in three tiers | ARCH Table 1.7, §2.8 rule 3, §4.1, Table 2.8b, Table 5.10 | N, except the label text as fact | see A3, classified, below | revert to §4.1; the label inference to him (Q3) |
| A4 | nested and overlapping objects; explanation records | ARCH §1.4, §2.2 (L1), §4.4, Table 4.6 | N; one quoted inconsistency | see A4, classified, below | revert to L1 and §4.4; a question on §1.5's halo |
| A5 | identity separated from conflict | ARCH §4.5; THEORY II.5 | N; two arithmetic notes P | see A5, classified, below | revert to §4.5; the notes kept |
| A6 | questionless members | ARCH §2.8 rule 4, Table 2.8b, §5.8, §5.5 | A6.a W but against ARCH; the rest N | see A6, classified, below | the sign question to him; revert §5.5, §5.8 |
| A7 | per-acquisition witnesses; explicit dependence | ARCH §5.3, §6.2.2 | A7.e P; the rest N, or no change | see A7, classified, below | qualify the κ sentence; revert classes, bar, outcomes; one question |
| A8 | provenance and roles | ARCH §5.5, §5.7, §6.2.5 | A8.a and A8.e P; the rest N | see A8, classified, below | revert the successor and the name; a question on localizing gold |
| A9 | emission keys | ARCH §6.1.1, §6.1.4 | A9.a P; A9.c W; A9.b N | see A9, classified, below | revert to c₊ first |
| A10 | contracts and build order | ARCH §6.6, Glossary, §5.3, §6.4 (falsifier 7), §3.4.2 | mixed (see below) | see A10, classified, below | Phases 0–9; Phase 5's bridge moved; the single-voice question to him |

Each change is several sub-changes. Each sub-change is classified on its own and gets its own row as it is read.

#### A1, classified (ARCH Part 3 read whole: §3.1–§3.6, Tables 3.1–3.8)

**The original.**
- Layer 1, the MR signal law, is the substrate. It is solved per place from the study's own series, where the
  inventory identifies a term. The identifiable set, the gain specialist pinned on reference tissue (§3.3.3) and
  recalled regime coefficients (§3.3.5) are part of it, with silence and its cause where a term is not identified.
- Layer 2 compares tissue parameters with their population reference (§3.4.2).
- The per-series raw chain is "the degraded path for any series the law cannot read" (§3.1, §3.3.9).
- The order of the build is §3.6. It starts with tags and inventories, then the front end on "stored values with
  rescale" through one kept transform. Next come the gain and decay specialists with leave-one-series-out, and
  physics-space KneeDiff against raw on the fixed instrument.

| sub | the change | class | why | action |
|---|---|---|---|---|
| A1.a | per-series-class references and signatures "carry the substrate", with the raw path made general | N | not provable: ARCH states the law's feasibility as OPEN, to be measured (§2.3.2, §3.3.9), and the founder said questions are "resolved by building and observing" (15:24:53Z). Not in his words | revert to layer 1 as the substrate where identified, with ARCH's degraded path |
| A1.b | the law "runs only where a declared forward operator has rank and conditioning" | N | ARCH already silences an unidentified term: "What a study can identify depends on its inventory" (§3.3.3); "T1 falls silent by propagation alone" (§3.3.7). "Conditioning" is a judgment added to it | revert to ARCH's identifiable set and its σ-propagated silences |
| A1.c | regime corrections "named as offsets, never as physical coefficients" | N | a naming and conception change. ARCH: "regime coefficients", read as "-ish" values (§3.3.5, §3.3.9) | revert |
| A1.d | K24, "the law", made optional and placed after first light | N | follows from A1.a. ARCH's §3.6 builds the gain and decay specialists early | revert: layer 1 is core, in ARCH's order |

#### A2, classified (ARCH §1.5, §2.2 and §2.10 read whole)

**The original.**
- "*Structures are found for free.* The atlas places every always-present structure, so only lesion-objects are
  searched for, in the residual" (§2.2, consequence 2).
- A structure the data does not show is either a finding or an input error, and "The constraint reference …
  decides which".
- Zones come from a template-space label volume (§2.10). Table 2.10b lists the zones to add, from template
  geometry. Multi-atlas votes are kept as fractions, the per-plane atlas route is OPEN, and an unusual knee is
  caught "per study by a placement margin below zero".

| sub | the change | class | why | action |
|---|---|---|---|---|
| A2.a | "the atlas proposes search regions"; containers from robust neighbours (K19's delineation) | N | not provable: whether atlas placement suffices is the design's own question, with its own instruments (the NCC gate, the placement margin, the constraint reference). Not in his words | revert to the atlas's zones and ARCH's checks on them |
| A2.b | "identity evidence comes from patient data" (I, read on the patient's own anatomy) | N | as above. ARCH reads a structure against its own prior through the λ-trajectory (§1.5, §4.5) | revert, together with A5 |

#### A3, classified (ARCH §1.7 and Table 1.7, §2.8 and Table 2.8b, §4.1 and Table 4.1, §5.6 and Table 5.10 read whole)

**The original.**
- An exclusion mark is "a −1 written on one finding's question at one place, by a lens entitled to write it". Four
  conditions make it one: a positive reading; a law naming the incompatibility; a lens that can read there in
  health; no censor having removed the evidence (§4.1).
- "T1-bright marrow is the senior excluder of edema" (§4.1).
- "The licensed 0 is the Deviation lens's exclusion mark, and it must be written" (§2.8 rule 3; §3.4.3; Table 2.8b
  row 1: "no lesion at this voxel, in this series").
- Per finding, the partition into excluded, blind and remainder is absolute: "A body lying in F's excluded part is
  censored for F, absolutely".
- Table 5.10's law-given censors are absolute, among them "A fracture lies within edema".

| sub | the change | class | why | action |
|---|---|---|---|---|
| A3.a | three tiers (absolute physical impossibility; exclusion qualified by coverage and resolution certificates; supportive sign) in place of the exclusion mark and the partition | N | not provable; not in his words. ARCH's own observation qualification is its condition 3, the hardness map | revert to §4.1 |
| A3.b | "T1 confirms edema and, together with the suppression map, rejects the fat explanation", in place of T1 as senior excluder | N | a judgment of how the pathways behave | revert |
| A3.c | "fat-suppressed fluid-sensitive series are the sensitive pathway, and mild bruises can be T1-occult" | N | a medical claim, not provable here and not in his words | revert |
| A3.d | "'Licensed' never means 'excluded'" | N | it reverses his explicit design (§2.8 rule 3). Whether a lesion can sit inside the licence is the kind of question the design itself measures, not a proof | revert: the licensed 0 is the Deviation lens's exclusion mark |
| A3.e | "With the official labels, an intact band cannot exclude ACL or MCL injury" | the label text is P, as fact; the inference is N | the competition's definitions (ACL and MCL mean "injury"; Meniscus "tear"; Contusion "bone contusion / bone bruise") are its literal framing, admissible as fact. What the band excluder does under "injury" is a design inference (founder, 23:22:50Z: "not implicit warrants on design or conception") | keep the definitions recorded as fact. The inference goes to him under ARCH's own Q3 (§4.1, §2.11, §5.6) |
| A3.f | Table 5.10's absolutes ("a fracture lies within edema"; "no neck, no Baker's") made non-absolute | N | not provable; not in his words | revert to Table 5.10 |

#### A4, classified (ARCH §1.4, §1.5, §2.2, §4.4 and Table 4.6, Glossary "Halo" read whole)

**The original.**
- L1: "each voxel belongs to one zone and holds one tissue and at most one lesion (L1; RECIPE §6)" (§1.4, clause
  2). Clause 5: "no two objects in one space".
- The take "removes what the object's law says the object contributes", and leaves the population's expected
  value (§4.4).
- Halos are law-given (Table 4.6). Edema is taken first, and the fracture line is found by "reaching inside
  committed edema" (§4.4: "the smooth container first, then what it held").

| sub | the change | class | why | action |
|---|---|---|---|---|
| A4.a | "ownership of measured contribution kept apart from membership in findings" | N | a conceptual change, not provable, not in his words | revert |
| A4.b | "reversible explanation masks" in place of the take | N | as above | revert to §4.4's take |
| A4.c | "subtraction only under a stated contribution law" | N | ARCH's take already subtracts by the object's law. Restricting it, with masks elsewhere, is a change | revert |
| A4.d | "edema is not a halo of a fracture line" | the inconsistency is P; the choice is his | §1.5 lists "an edema around its fracture line" among halos. §4.4, Table 4.6 and the Glossary ("Halo … an edema's feathered margin") make edema an object with its own halo, and find the line inside it. Both passages are quoted | a question to him. Until he answers, the book implements §4.4 and Table 4.6, the specification, and states the open question |
| A4.e | nested and overlapping objects, against L1's "at most one lesion" per voxel | N | it amends his law L1; not provable | revert to L1 and clause 5 |

#### A5, classified (ARCH §4.5 and THEORY II.5 read whole; the algebra redone)

**The original.**
- The λ-trajectory in closed form: identity(λ) = exp(−½(1−λ)²p̂_S), fidelity(λ) = exp(−½λ²B), B = ‖z‖² − p̂_S.
- λ* = p̂_S/‖z‖², and the drop to λ = 1 is ½B²/‖z‖².
- The words are bands of ‖z‖²/p̂_S. MONO_DOWN holds "when ‖z‖² exceeds five times p̂_S", that is, λ* < 0.2.
- The placement margin m separates misplacement from deviation, and the statistic is read per window.
- ARCH itself departs from THEORY II.5's "Peak height = confidence": "The drop is the reading emission uses". That
  departure is the founder's own, and it stands.

| sub | the change | class | why | action |
|---|---|---|---|---|
| A5.a | "the four words are legacy routing codes for cells of (I, D)"; I as identity evidence on patient data (K19) | N | a re-conception of his trajectory; not provable, not in his words | revert to §4.5 |
| A5.b | "The \|z\| survival profile from the thresholded sweep is a reading in its own right" | N | ARCH keeps the sweep as the closed form's twin, a check ("It tests whether the closed form describes what the pipeline does") | revert |
| A5.c | "sampled MONO_DOWN needs E > 10p̂, not 5p̂" | the arithmetic is P; no correction follows | the log-confidence is a parabola in λ, so the grid's best point is the one nearest λ*. The sampled maximum sits at λ = 0 only when λ* < 0.1, that is ‖z‖² > 10p̂_S. ARCH defines MONO_DOWN on the closed form's λ*, where its 5p̂_S is exact | no change to ARCH's words. The fact is noted where K21 compares the closed form with its sweep: disagreement in the band from 5p̂_S to 10p̂_S is within the grid's resolution, which ARCH's own "beyond the grid's resolution" already excludes *(my reading of that phrase)* |
| A5.d | "'fidelity' exceeds 1 when E < p̂" | P | with B < 0, exp(−½λ²B) > 1 for λ > 0. So ARCH's prose "It falls from 1" is inexact there, though ARCH already assigns those studies MONO_UP ("every ‖z‖² ≤ p̂_S … reads so") | a factual note only; the mechanism is unchanged |
| A5.e | "the SURE remark is a conditional fixed-shrinkage analogy" | N | ARCH's exponent, p̂ − 2λp̂ + λ²‖z‖², is Stein's estimate with p̂ in place of p, and ARCH says so ("with the measured p̂_S in the place of the voxel count") | no change |
| A5.f | D renamed "the windowed reference-conflict energy, named honestly" | N | a renaming | revert |

#### A6, classified (ARCH §2.8 rules 1–5, Table 2.8b, §4.1, §5.5, §5.8 read whole; the No Popery law)

**The original.**
- "A lens is 'a cheap, deliberately lossy view that measures one thing and knows no question'" (§2.8 rule 1).
- Yet "Each lens declares whether it counts for, against or both (Table 2.8b)" (rule 4), and an entitled lens
  writes exclusion marks on a finding's question (rule 5; §4.1).
- Lens families are "chosen by aggregate prevalence matching, the count's analog", then validated on phantoms and
  gold, "necessary, not sufficient" (§5.8).
- The trust radius is "the least level no member reaches" over a chance population of true normals at the same
  zone class and regime (§5.5).

| sub | the change | class | why | action |
|---|---|---|---|---|
| A6.a | "lenses emit measurements and visibility; agencies hold the signs" | W, against his own ARCH | his No Popery law (global and Kaggle_Killer instructions, 2026-09-17): "every member … measures ONE thing about an object and knows no question; a body … holds the signs"; a tell is "a docstring that states a member's sign". His ARCH (2026-10-02) keeps lens-declared directions and lens-written exclusion marks (§2.8 rules 4–5, §4.1) | a question to him: which governs the knee, No Popery or ARCH rules 4–5? The book keeps A6.a, which is warranted, until he rules |
| A6.b | "no seating by prevalence", against §5.8's prevalence-matched families | N | No Popery's tell is "seating decided by discrimination on one query". ARCH says prevalence matching is not discrimination ("A detector that fires at random, at the right rate, matches perfectly and carries nothing") and uses it only to propose. Whether it is Popery is his to say | revert to §5.8. A question to him: does he count prevalence matching as Popery? |
| A6.c | the radius from "a specified null mechanism (… conditioned on visibility and context …)" | N | not provable, not in his words. ARCH already charges the bucket's size through the nearest-case statistic | revert to §5.5 |
| A6.d | "hard negatives become near-miss censors" | N | ARCH sends a normal that reaches to "the founder's sheet" (§5.5, *Fails*), and writes censors only from confirmed failures (§5.6) | revert |

#### A7, classified (ARCH §4.4, §5.3 and Table 5.5, §6.2.2, Glossary read whole)

**The original.**
- "The committee is the series", one voice per series.
- "series whose errors the gate cannot separate count as one voice" (independence classes).
- GenomeVault's levels "adopted provisionally until the founder sets the knee's own bar" (§5.3; §6.2.2).
- "Agreement counts only between voices whose independence has been measured" (§4.4).
- Table 5.5's four outcomes: CONCUR, SINGLE, DISAGREE, ALL SILENT.

| sub | the change | class | why | action |
|---|---|---|---|---|
| A7.a | witnesses per acquisition, upstream of any joint reconstruction | no change | it restates ARCH: the committee is the series, and imputed series are "never a voice" | none |
| A7.b | "dependence is a graph of shared causes with multiway checks", in place of independence classes | N, plus a question | the gap is P: "cannot separate" is pairwise and need not be transitive, so the classes are not determined when A and B, and B and C, cannot be separated but A and C can. The fix is a design choice, his | revert to classes, and ask him how a class is formed when the pairwise relation does not chain |
| A7.c | "no imported bar" | N | ARCH adopts GenomeVault's levels "provisionally until the founder sets the knee's own bar" | revert |
| A7.d | INSUFFICIENT as a fifth outcome | N | under ARCH, series the gate cannot separate count as one voice, and unmeasured agreement does not count (§4.4) | revert to Table 5.5 |
| A7.e | "κ against reports is an upper bound" (§6.2.2) amended | P | a counterexample, with binary readings and report errors independent of the views. Each view errs at 0.1, both at 0.08, so the true κ = 8. Reports err at 0.2. Each view then disagrees with the report at 0.26, both at 0.24, and the observed κ = 0.24/0.26² ≈ 3.55 < 8. So it is not an upper bound in general: report noise can deflate as well as inflate it | qualify ARCH's sentence with the counterexample. Its own measurement stays: "the gap between κ against reports and κ against gold" |

#### A8, classified (ARCH §5.5, §5.7, §6.2.5 and Table 6.3 read whole)

**The original.**
- The chance population for an "absent" bucket is "phantoms planted in true normals, and gold positives localized
  to the zone" (§5.5).
- A call follows its object by place. A call with no clear successor "goes to the founder's sheet" (§5.7, rule 2).
- One role per study per measurement (§6.2.5, rule 1).
- N is "true normals", with its bias stated: "report-derived: an unreported lesion makes a "normal" false" (Table
  6.3).

| sub | the change | class | why | action |
|---|---|---|---|---|
| A8.a | "gold is study-level only" | P, as fact | the competition's literal data: twelve study-level labels per training study, with no localization | record it as fact |
| A8.b | "localized authority comes from report calls (noisy) or the founder" | N, plus a question | a design inference from A8.a (founder, 23:22:50Z: not a warrant). The gap it points at is real. For a finding with more than one zone, a study-level gold label cannot say which zone, so §5.5's "gold positives localized to the zone" has no stated mechanism there | revert. A question to him: how is a gold positive localized for a finding of several zones (by a report call's successor, by his sheet, or only for findings of one zone)? |
| A8.c | "an ambiguous successor stays unresolved" | N | ARCH sends it to "the founder's sheet" (§5.7) | revert |
| A8.d | "true normals" renamed "report-negative candidates" | N | his term. ARCH already states their bias (Table 6.3) | revert the name |
| A8.e | "gold already shaped the parser's rules and is not untouched evidence for parser-derived claims" | P | fact: the parser records "gold gate 2026-08-29", which ARCH quotes (§5.6). Logic: evidence used to shape a rule is not independent evidence for that rule | keep, as a note |

#### A9, classified (ARCH §6.1.1–§6.1.6 read whole)

**The original.**
- Emission is three registers. The upper is ordered by c₊ first, then the s-digit, then H.
- The middle is "*Literal* (Law 7): none, all at 0.5. *Ordered* (Q4)". "Any strictly monotone map of the scores
  leaves the AUC unchanged" (§6.1.1).

| sub | the change | class | why | action |
|---|---|---|---|---|
| A9.a | "strictly monotone" → "strictly increasing" | P | a strictly decreasing map turns every AUC a into 1 − a | keep |
| A9.b | "witness-set comparability, never a raw series count", in place of c₊ as the first key | N | a judgment ("that would rank protocol richness"); not provable, not in his words | revert to Table 6.1's c₊ |
| A9.c | Law 7's literal 0.5 as the submitted default | W | THEORY Law 7: "where the evidence is open, abstain (→ 0.5) rather than fabricate a confident score". Q4 stays his (ARCH Table 6.1) | keep |

#### A10, classified (ARCH §3.4.2, §5.3, §6.2.1, §6.3, §6.4 falsifier 7, §6.6.3 and the Glossary read whole)

**The original.**
- Phases 0–9 (§6.6.3), "Each phase is measured before the next begins". The law is Phase 4, the ledger Phase 5, the
  lenses Phase 6, the loop Phase 7, the society Phase 8, and emission and the dry run Phase 9.
- The structure-alone run: "layers 0–7 and the law checks, with no cases and no censors, emitted by the same rule"
  (§6.3).

| sub | the change | class | why | action |
|---|---|---|---|---|
| A10.a | Phase 5's gate on H2's bridge cannot run in Phase 5 | P | an order that cannot execute. The bridge reads "the surface-contact bank", "the line bank, after the edema's pull-out" and the like (Table 6.2). Those are lens banks (Phase 6) and banks read after a take (Phase 7) | each hard pair's bridge runs once its banks exist. Phase 5's other gates (the exact decode and its twin; re-seeding changes nothing) stay |
| A10.b | the book's chapters in dependency order | W | founder, 15:24:53Z: a "book", with each severable module as a "chapter" | keep the chapter form |
| A10.b′ | "first light early" (an end-to-end kernel at K18, before the law, the structure lenses and the society) | N | it reorders his phases. ARCH runs emission and the dry run in Phase 9 | revert to Phases 0–9, with the chapters mapped onto them |
| A10.c | "provisional take, confirmed object and finding decision kept distinct", and "no answer from one voice" | the inconsistency is P; the rule is his | the Glossary: concurrence is "the only way a lesion-object is committed or an answer assigned". §5.3, *Today*: "The loop's takes carry "single voice" …, and so does every answer built on them". Whether a single voice can carry an answer, marked as such, is not settled by ARCH | a question to him. Until he answers, the book states both passages and chooses neither |
| A10.d | falsifier 7 reworded to "stable meaning within a regime" | N | a rewording | revert to ARCH's wording. A small question: does "coefficients cluster by regime" mean the regime coefficients, or the tissue parameters of the reference tissues? |
| A10.e | z's denominator gains the centre's uncertainty, var(μ̂) | P | for an observation x independent of the reference members, var(x − μ̂) = var(x) + var(μ̂). §3.4.2's σ²_bio + σ²_meas leaves the second term out. For a median of n members under the normal model, var(μ̂) ≈ (π/2)·σ²/n | keep the term, with its stated model |
| A10.f | K16's "case-free decision path" | no change | it is ARCH's own structure-alone run (§6.3) | none |

### B. Revision 1 (THE_KNEE §2.1, R1.1–R1.15; `revision_1.md` F01–F57)

To be listed row by row from `revision_1.md`. Each row's grounding note says which canon passage it follows or
amends.

### C. Departures in the chapters that A and B do not list

To be found by reading each chapter against ARCH. For example, K13 §9's "No selection of sane values" departs from
ARCH §2.8 rule 2, where the choice among sane values is measured.

### D. The engineering design (THE_KNEE §3–§4; K01, K02, K02a, K02b)

Checked against his words on engineering, and for anything that alters what the design does.

## Status

- **A1–A10 are classified** (2026-10-02, 23:3xZ–00:xxZ). Every amended passage was read whole this session.
- **Nothing has been reverted yet**, apart from revision 2's edits (`48fa94f`).
- **Next: B, revision 1's rows**, then C and D, then the reverts as one revision back to the original, with the
  founder's questions gathered for him.
