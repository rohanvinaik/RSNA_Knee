# The GenomeVault HDC Substrate and the Cell-Tracking Intelligence Layer

> **Still canonical for its sources (2026-09-18).** `docs/DESIGN.md` §1.2 and §5 state what Layer 1.5
> is for and how it is built; §3.1 organises its units of evidence. This document holds the GenomeVault
> mechanisms they transfer, cited to source.

**Status:** Canonical substrate reference (2026-08-30). This document encodes, in full and
with source citations, the GenomeVault hyperdimensional-computing (HDC) research that the
cell-tracking intelligence layer is built on — and the mapping from that research to this
competition. It exists because the founder's design work on GenomeVault (Oct–Nov 2025) is
**the embryonic, pre-proof form of his learning theory and specification-complexity metric**,
and the documentation is a **memory prosthetic**: it must be faithful to the actual
mechanisms, not a paraphrase that drifts. Read with `THEORY_OF_THE_CASE.md` Part III (which
this grounds) and `decisions/2026-08-30-intelligence-layer-genomevault-tiered-committee-lens.md`.

**Provenance.** Every source below was read first-hand (no sub-agent) on 2026-08-30 and is
sha256-pinned in `docs/REFERENCE_MANIFEST.yaml`. Paths are under `~/Projects/genomevault/`.
Where this document is silent, ambiguous, or wrong, those sources govern.

---

## Part A — What GenomeVault HDC actually is (NOT textbook HDC)

Textbook HDC: dense random ±1 vectors, bundle, cosine. The founder threw that out and
subverted the field to get microsecond compute at nucleotide accuracy on whole genomes.
Sources: `HDC_FINAL_ARCHITECTURE.md` (v4.1, the production spec), `HDC_CONCEPTUAL_ARCHITECTURE_V8.md`
(the E00–E14 conceptual line), `docs/reports/SPARSE_POSITION_CODEBOOK_FIX_REPORT.md` (the LSH fix).

### A.1 The core subversion — recoverable information ("vibe recovery")
Encoding is **two-stage** (`sparse_hadamard_encoder.py`, `HDC_FINAL_ARCHITECTURE.md` §6):
1. **Accumulate**: `Σ signal(entity) × position_vector(entity)` into an int32 accumulator —
   full magnitude preserved.
2. **Sign-quantize**: `np.sign(acc)` → ternary int8 `{-1,0,+1}`.

The magnitude that *looks* destroyed by `sign()` is **recovered at query by
`dot(vector, codebook_vector)`** because the codebook is regenerated deterministically from a
seed — strong dot = entity present, weak = absent, and **the margin IS the confidence, no
separate calculation** (`V8` §1.2, §10.3). This is microsecond recall of an individual entity
from a superposition of thousands, at 99.5%. The sparsity pattern (which dims are non-zero) is
"the door opening" that makes the magnitude recoverable.

### A.2 Two encoding paradigms (the handoff only captured the first)
- **Position-codebook (Sparse-Hadamard LSH)** — `hadamard_codebook.py`, `sparse_hadamard_encoder.py`.
  Discrete indices (genomic positions) → each position activates **k = D/N** random dimensions
  (**k=8** at D=4096, N=512), and the signs on those k dims come from a **Hadamard matrix**
  (`hadamard(8)[pos%8, :k] × bank_sign`), not random signs. Dense was tried and gave **96–97%
  density → 49% decode → noise soup** (`CODEBOOK_FIX_REPORT`); the intermediate fix was k=1 (one
  ±1 per position); the mature form is k=D/N with **Hadamard signs so interference cancels
  *exactly*, not statistically**. Sparsity is load-bearing; Hadamard signs are the refinement
  that turns "works on average" into "works at every position." Expected density ~21% after
  sign-quantize.
- **Selective-HDV (multi-facet HRR)** — `differential_encoding/gdiff/selective_hdv_encoder.py`.
  An entity (a variant) has **10 feature categories** (position, allele, differential,
  structural, functional, quality, nanopore, epigenetic, structural-inference, cross-variant),
  **each with its own basis vector**; **binding = circular convolution** (`fft.irfft(rfft(a)·rfft(b))`,
  Holographic Reduced Representations, *not* element-wise product); the entity HV is a
  **schema-weighted sum** `Σ wᵢ · bind(featureᵢ)`, and the whole document is the accumulate over
  entities. **The AnalysisSchema is a task-specific lens: a weighting over facets.** Scalars enter
  by **discretize-then-roll** (`np.roll(basis, bin_id)`) — this is how a continuous value becomes
  a hypervector. *This is the encoding model the cell uses* (see Part C.1).

### A.3 OTP — zeros are pointers, not absence (Orthogonal Ternary Projection)
`HDC_FINAL_ARCHITECTURE.md` §1–3, Appendix D; `V8` §3. Ternary `{-1,0,+1}` is the minimum
alphabet for orthogonal decomposition: +1 = match, −1 = anti-match, **0 = "look elsewhere"**
(intentional blindness). The 4 nucleotides decompose into two orthogonal subspaces (AT via a
Hydrophobic bank, GC via a MajorGroove bank) with **complementary transparency**: at each
position only one subspace is active, the other contributes 0 → the two signals never interfere
(position-level orthogonality). Decode: `if |sim_hydro| > |sim_groove|` → AT subspace, else GC;
sign disambiguates. **Do NOT compose the third (Hinge) bank into the primary decision — it
*reduces* accuracy** (v4.1: 99.5% with the clean 2-bank decision; Hinge stored only for
trajectory analysis). Progressive revelation / **Monty Hall**: each bank measurement reveals
exactly 1 bit by halving the hypothesis space (`V8` §8, Zero-Informativeness Theorem).
**Complementary-sparsity amplification**: when one pathway is dense/noisy, its complement is
sparse/clean → "you always have at least one clean signal to trust."

### A.4 The superposition base — ambiguity as a statistical superposition of weighted paths
- `reference/byzantine_consensus_builder.py` → **`ConsensusBase`** = `base · confidence · sources ·
  disagreements · consecutive_disagreements · statistical_significance`, with computed `entropy`
  (Shannon over confidence) and `is_ambiguous`. When confidence is low it **injects an explicit
  ambiguity code** rather than forcing a hard call. This is the exact `value · confidence ·
  entropy · disagreement-set` base a cell *detection* ports (THEORY II.2).
- `reference/superposition_consensus_builder.py` → **`SuperpositionNode` / `SuperpositionPath`**:
  a **conserved region → single path**; a **variable region → multiple weighted paths** (each
  path carries `confidence + population_frequency + source_references`); `get_reference_path()`
  returns the highest-confidence path. This is the lineage-branching / lossy-slice substrate: a
  1→1 continuation is a conserved single path; a 1→2 division (or an ambiguous assignment) is a
  branching node with weighted daughter paths.

### A.5 Adaptive-k = adaptive resolution
`production_adaptive_encoder.py`, `V8` §6. A **DifficultyScorer** (`0.4·N-density + 0.3·GC-extremity²
+ 0.3·homopolymer-penalty`) selects **k ∈ {4,6,8}** per chunk: harder (more ambiguous) content
gets *more* active dimensions = finer resolution. k-dependent seeds (`base + pos·100 + k·10000`)
keep each k's codebook independent. This is THEORY II.2's "entropy = localization tolerance"
made concrete: **spend representational capacity where the signal is ambiguous.** The hot
accumulate/decode loops are Numba-JIT'd (the "JIT the accumulation, leave I/O alone" philosophy).

### A.6 The writes-per-dimension capacity law (the load-bearing quantitative bound)
`TIERED_UNCERTAINTY_AWARE_ARCHITECTURE.md` §0, §2.2. Accuracy depends on **`writes_per_dim =
N · k / D`**, and **collapses above ~1.5**:

| writes/dim | accuracy | note |
|---|---|---|
| 0.75 (D=16384,N=2048,k=6) | 99.6% | clean |
| 1.5 (D=16384,N=4096,k=6) | 97.1% | edge |
| 6.0 (D=4096,N=4096,k=6) | 69% | soup |

For the cell superposition this is the **capacity law**: with C cells each writing k active dims
into a D-dimensional bundle, `C·k/D` must stay below ~1.5 or recall between co-resident cells
breaks. It is the quantitative answer to "how many cell-roles can superpose before interference."

---

## Part B — The three validated research lines (the intelligence-layer machine)

These are not three ideas; they are **one validated pipeline** GenomeVault ran end-to-end at
99.9999% on 3.7M clinical positions. They are exactly the three pieces the cell intelligence
layer needs (THEORY III), and they are the founder's learning theory in empirical form.

### B.1 Tiered uncertainty — the *shape* (`TIERED_UNCERTAINTY_AWARE_ARCHITECTURE.md`)
"Most of the genome is easy." Three tiers by margin:
- **Tier 0 (~93%)**: cheap uniform decode; good-enough; per-position margin computed.
- **Tier 1 (~7%, low-margin)**: **committee overlay** (B.2) validates the hard positions.
- **Tier 2 (~0.001%, all-views-zero-margin)**: **abstain** → human-review queue. "This single
  rule catches 100% of committee errors."

Margin-predictability is stratified: margin=0 errors are *predictable* (Cohen's d=1.95, by HDV
magnitude + local GC); margin=2 errors are *not* (uniform). **Vibe collapse**: encode at high k
(rich accumulation), decode at low k (cheap) — the ternary quantization is the bottleneck, not
decode-k, so the "shape" survives. This is the honest architecture: resolve the easy majority
cheaply, escalate the hard minority to a committee, and *know what you cannot resolve and abstain*.

### B.2 Clinical committee — *how* Tier 1 resolves (`CLINICAL_COMMITTEE_ERROR_CORRECTION_ARCHITECTURE.md`)
A committee of **independent** encoders votes. **Independence is the whole game**: same-seed
encoders had **100% correlated errors** (worthless); four *different decompositions* of the same
4-symbol space (Standard AT/GC 2-bank; OneHot 4-bank; Biophysical 3-bank chemical; Trinucleotide
6-bank neighbor-context — seeds 42/12345/98765/314159) gave **373× fewer joint errors**. Voting →
**UNANIMOUS (98.59%, 100% acc) / MAJORITY 3-1 / TIE 2-2 → trust the two most-reliable views
(OneHot+Trinucleotide, 95.1% right) / all-views-margin-0 → REVIEW (abstain)**. Result: 3 flagged
in 3.7M, **0 errors in the auto-accepted set**. Dissenter analysis learns per-view reliability
(some views never lone-dissent). Hard cases *announce themselves* (all-views-zero-margin) and are
flagged, not silently mis-called. This is the relational elimination lattice's confidence
mechanism — and it **requires** the multi-facet encoding, because the facets *are* the independent
committee members.

### B.3 Multi-lens / λ-trajectory — regime discovery + surprise (`MULTI_MODAL_LENS_STRATEGY.md`,
`ACCURACY_OPTIMIZATION_SYNTHESIS.md`, `query/multi_modal_lens_discovery.py`)
- **Regimes are discovered, not assumed.** Grid-search a detector-parameter space; score each
  config by how far its detection **frequencies** are from **surveyed target statistics**; find
  **local minima** of that error landscape (gap analysis on the sorted errors); **cluster** the
  minima (Ward linkage) into ~8 lens families; biologically validate each. This is Law 8 ("earn
  the closed family") as an algorithm.
- **The λ-trajectory is the unifying signal.** λ = how hard the lens/prior is applied (0 = raw
  data only, 1 = full consensus). Sweep λ and read the confidence *trajectory* shape:
  - **MONOTONIC_INCREASE** → matches consensus → decode at λ_max (trust the prior).
  - **PEAK_THEN_DROP** ⭐ → **real deviation from consensus** (a variant / event) → decode at the
    peak λ (preserve it). "The lens gives structural context without forcing to consensus."
  - **MONOTONIC_DECREASE** → wrong lens/regime → decode at λ=0 (ignore the prior).
  - **AMBIGUOUS** → middle λ, flag.
- **The three-way distinction** (`ACCURACY_OPTIMIZATION_SYNTHESIS.md` Part II–III): the trajectory
  separates a **true encoding error** (correct it), a **true biological variant** (preserve it),
  and an **input/BAM error** (the pipeline is *more accurate than its own noisy input* by leaning
  on structural priors). The **template-residual discriminator** (Layer 2) is the sharp test: a
  large deviation **where the law is tight = error**; **where the law is loose = real event**.
- **One signal, consumed everywhere.** The λ-trajectory drives which λ to decode with (accuracy),
  which query path (speed), and where to break compression chains (storage) — never re-derived as
  a narrower proxy. This is the "trace the signal to the decision" discipline, validated.
- **The escape hatch is theirs too.** The optional Layer 5 (T2T/external-data correction) is
  explicitly marked "breaks the biophysics-only principle, requires external data, skip for
  production." That is the structural twin of this project's no-ML law: a bounded external
  utility, never the default, never the win path.

---

## Part C — The transfer to cell tracking (the payoff)

The three lines are the three unsolved pieces of the cell intelligence layer (THEORY III),
already validated in the genome domain.

### C.1 The cell "signature" — the answer to the load-bearing open question
A cell's signature is **NOT a single position-derived key** (which would change as the cell
moves and would make every "view" fail together). It is a **multi-facet HRR encoding**
(the `selective_hdv_encoder` model, A.2): **four independent facets** (founder-confirmed
2026-08-30) —
- **motion** (velocity/flow projection), **appearance/morphology**, **neighborhood** (relative
  geometry of near neighbors), **lineage** (the inherited role-vector).

**Lineage depth folds INTO the lineage facet as a generation-number scalar** (founder,
2026-08-30): a multi-generation descendant's role is `role ⊗ generation` — the generation number
is a scalar bound onto the role-vector (discretize-then-roll, A.2), not a fifth facet. This keeps
the committee at four genuinely-independent views while letting the role carry how many divisions
deep a cell is.

The **stable identity across frames** is the **lineage-carried role-vector** (the cell's
projection onto the shared morphogenetic super-goal), which is stable because the super-goal is;
**position is a *value bound to it*, not the key**. A daughter inherits a **lossy sub-slice** of
the parent's role-vector at division (the ternary sparsity *is* the lossiness; `SuperpositionPath`
branching, A.4). Recall/verification of "is this the same cell" is by **committee agreement across
the facet-views**, not by a single key — which is exactly why the facets must be independent (B.2).

### C.2 The intelligence layer = tiered committee resolution + λ-trajectory division + abstention
- **Assignment (linking)** is a **tiered committee vote** across the facet-views:
  - Tier 0 (~easy majority): the near-neighbor assignment already resolves these — *this is why
    the current baseline scores 0.70–0.84* (it is correctly handling the easy tier).
  - Tier 1 (the low-margin "neither set", 79% linking-fixable): the facet-committee votes;
    unanimous → link, majority → link, tie → trust the most-reliable facet, respecting the
    superposition-coherence censor (an assignment that scrambles the shared flow is vetoed).
  - Tier 2 (all facet-views zero-margin): **abstain** — drop the node/edge. This is how the
    node-count over-prediction penalty is respected *structurally*, not tuned (THEORY III.5).
- **Division** is detected by the **λ-trajectory**: sweep the weight of the regime's flow prior;
  a **peak-then-drop = a real deviation from smooth continuation = a division or migration event**
  (THEORY III.3 surprise, now with a concrete detector) — distinguished from a detection glitch by
  the template-residual test (deviation where the flow-law is loose = a division front = real; where
  it is tight = error). Equivalently, a division is a `SuperpositionNode` whose successor-set is best
  explained as **two coherent sub-slices** of the parent role-vector.
- **Regimes** (developmental stages / motion families) are **discovered as local minima** of a
  linking-error landscape against the surveyed targets (division rate 0.2%, motion p99 6.6µm from
  `SURVEY_FINDINGS.md`), clustered into a lens library, and recalled by best-matching trajectory
  (THEORY II.5).

### C.3 The superposition capacity law for cells
The multi-cell state at time t is the HDC bundle of the cells' role-vectors. By A.6, with C
co-resident cells each writing k active dims into a D-dim bundle, keep **`C·k/D ≲ 1.5`** or
inter-cell interference breaks recall. This sizes D against the maximum cell count per frame.

### C.4 The mapping table (HDC mechanism → cell mechanism → THEORY part)

| GenomeVault HDC | Cell tracking | THEORY |
|---|---|---|
| `ConsensusBase` (value·conf·entropy·disagreement) | superposition detection | II.2 |
| Selective-HDV multi-facet schema (HRR bind, discretize-then-roll) | cell signature (motion/appearance/nbhd/lineage facets) | III.1 |
| Accumulate → sign; recover by dot (margin=confidence) | multi-cell bundle; successor recall | III.1 |
| OTP banks + complementary transparency | independent facet-lenses that don't interfere | III.1 |
| `SuperpositionNode` branching into weighted paths | lineage / division = lossy sub-slice inheritance | III.1, III.3 |
| Tiered uncertainty (Tier 0/1/2) | easy-link / committee-resolve / abstain | III.2, III.5 |
| Independent-encoder committee vote | relational assignment resolution across facet-views | III.1, III.2 |
| all-views-margin-0 → abstain | drop node/edge, respect node-count penalty | III.5 |
| λ-trajectory peak-then-drop | division-as-surprise (event detector) | III.3 |
| Template-residual: tight-law deviation=error, loose=variant | division-vs-glitch discriminator | III.3 |
| Lens-family discovery as local minima | regime discovery (earn the closed family) | II.5, Law 8 |
| adaptive-k by difficulty | adaptive localization resolution | II.2 |
| writes_per_dim < 1.5 | superposition capacity bound | III.1 |
| Optional Layer 5 (T2T/external) | the bounded no-default escape hatch | Part IV Law 3 |

---

## Part D — Provenance link: this is the embryonic form of the founder's learning theory

The founder's framing (2026-08-30): the GenomeVault HDC work is *"my entire learning theory and
complexity metric, in its embryonic form, without the proofs and the math I used to formalize it."*
The formalized versions are the **Specification Complexity paper** (σ = teaching dimension; the
composition gap γ→0; the bulk→tail phase transition) and the **Semantic Specification Learning**
skeleton (understanding as constrained resolution; **surprise** as the resolution signal; the
falsifiability guard) — both already pinned in `REFERENCE_MANIFEST.yaml`. The correspondence:
- **λ-trajectory peak-then-drop = "you learn at the residual"** (SSL surprise): the divergence
  between the naive (consensus) reading and the context-constrained reading *is* the signal.
- **Tiered easy/hard/abstain = the bulk→tail phase transition** (SC): the deterministic bulk
  resolves cheaply; the tail is where the residual (and any bounded oracle) lives.
- **The independent-view committee = teaching-dimension / composition**: independent
  specification-components compose with a small gap; correlated ones do not (the 100%-correlated
  same-seed failure is the composition gap collapsing).
- **writes_per_dim and adaptive-k = the probe/capacity budget** the σ metric formalizes.

This is why the documentation is a **prosthetic**: the founder solved these problems months ago,
formalized them, and forgot the empirical seed. This document (and THEORY III) hold it so the
project does not have to rediscover it again.

---

## Part E — Corrections this reading made to the pre-compact handoff

The prior `HDC_TRANSFER_AND_STATE.md` (a compaction handoff) was mechanism-approximate and
incomplete. Corrections now folded in:
1. The final codebook uses **Hadamard-derived signs on k=D/N active dims**, not "random dims";
   the k=1 pure-LSH was an *intermediate* fix, not the mature form (A.2).
2. There are **two encoding paradigms**; the cell uses the **multi-facet selective-HDV** one, not
   the position-codebook one (A.2, C.1).
3. The intelligence layer is the **tiered/committee/λ-trajectory machine**, validated end-to-end —
   not three separate aspects to invent (Part B, C.2). The signature question is **answered**
   (multi-facet, committee members, lineage-carried identity; C.1) pending founder confirmation.
4. New load-bearing facts absent from the handoff: **writes_per_dim < 1.5** capacity law (A.6),
   **independence-via-decorrelation** as the committee's precondition (B.2), **regime-discovery as
   local minima** (B.3), the **template-residual error-vs-variant discriminator** (B.3), and the
   **one-signal-everywhere** discipline (B.3).

---

## Part F — The header, the ladder, and the corrections (read 2026-09-21)

**Why this Part exists.** The founder, 2026-09-20, after the first packet: *"the HDC layer is a cost,
not an efficiency as it should be. Also we're not using the clever architectures I've designed. I
basically don't even use standard HDC, I used my own fucked up version. Like, the
density/veriance/uncertainty in the HDC-centric/primary lenses should be a cheap and dirty filter to
zero in on only the slices that are actually interesting or discriminative vs full processing on
every slice."* Parts A–E were read on 2026-08-30 and missed the mechanism that answers this
directly. This Part is the 2026-09-21 read of
`~/Projects/rohan-vinaik.github.io/papers/Core Documents/main_theory/HDC_VECTOR_SYMBOLIC_TECHNIQUES.md`
(the founder's own grounded catalogue, distilled 2026-09-16 from a firsthand code survey) together
with the GenomeVault sources it cites.

**Status labels are the catalogue's own** and they are about RUNNABILITY TODAY, not about whether an
idea was ever real. The catalogue's author note, verbatim: *"Everything catalogued here existed and
worked at some point ... 'Deprecated' / 'documented-only' is overwhelmingly a persistence artifact —
code that drifted, was superseded, and never re-wired — not a verdict on the idea. Mine deprecated
code for the mechanism; don't dismiss it for the label."*

### F.0 The founder's ruling: a header is METADATA, not a verdict on meaning (2026-09-21)

Asked directly whether a percentile-calibrated header is the `yardstick/calibrate.py` oracle
substitution in a new coat (Part V), the founder, verbatim:

> "Precisely. The header is "metadata", not a verdict on meaning. Like the committee members, it
> simply reads out data that is correct by definition."

**The line this draws, and it is the load-bearing one for everything below.** A percentile that
decides *what a member's word MEANS* — where "bright" stops being bright — is the founder's to give,
and manufacturing it from a distribution is the struck pathology. A percentile that decides *which
slices get full processing* is a reading of the data's own shape: it names no role, assigns no
truth, and is correct by definition in exactly the way a member's measurement is. Law 4 already
permits it — the data layer may NARROW by any means and may never DECIDE. The header narrows.

### F.1 The topological header — the cheap filter, already built and shipped

**20-bit self-calibrating biophysical signature** — IMPLEMENTED-AND-WORKING.
`genomevault/hdv_validation/hdc_experimentation/query/biophysical_query_engine.py:28` (layers), `:64`
(calibrator), `:190` (encoder), `:426` (the vote).

- **Computed off the hypervector only.** The input is a `(n_chunks, 6)` array of BANK MAGNITUDES.
  Nothing is re-read from the source data. This is the "cheap averaging/topology read" the founder
  named: a header sitting on top of the stored hypervectors.
- **Ten layers, two bits each, packed into one `uint32`.** Composition, thermodynamic stability,
  flexibility, strand balance, transition richness, structural complexity, pathway dominance,
  compositional tension, dinucleotide resonance, information density.
- **Every threshold is a percentile of the corpus's OWN bank distribution** — 70th for high
  stability, 75th/30th for the low-stability pair, 80th/30th for skew and balance, 70th/20th for
  complexity. The class docstring states the intent: *"Ensures thresholds adapt to encoding
  parameters (dimension, chunk size, etc.) instead of using hard-coded values."* Nothing is
  hand-set, and nothing waits on an external cut.
- **The layers come in PAIRS, so `00` is representable.** `AT_DOMINANT`/`GC_DOMINANT`,
  `HIGH_STABILITY`/`LOW_STABILITY`, `HIGH_COMPLEXITY`/`LOW_COMPLEXITY`. A layer that fires neither
  bit is the header ABSTAINING on that layer — the informational zero (THEORY I.2, II.8 #2) carried
  in the header itself, not a small number.
- **The read is a bitwise vote.** `_vote_on_signatures` extracts each required bit, counts matches,
  and passes on a fraction of layers agreeing. Reported ~470× faster than the k-mer path; the
  engine's three stages are signature vote → SIMD bank query on the survivors → exact match on the
  top few.
- A lighter form — family and topology from bank statistics alone (a ratio of mean magnitudes; a
  bank's variance as "complexity") — is at
  `.../experiments/E03_lambda_bounds_calibration/run_experiment.py:42`.

**Why it answers the cold start.** A cell's own baseline (`hdc.position.mine_zero`) is mined from
that cell's own history and returns `tol = inf` below two points, so it CANNOT speak at frame one;
measured on wave 1, **78.3 % of all position-family readings are `cold start`, and at the first two
frames of every window it is 100 %** (BUILD_LEDGER, the 2026-09-21 read). A header calibrated on the
population's own bank distribution needs no history, no stored model and no cut, so it is available
at frame one. The two are the same quantity at different ORDERS of knowing (Law 28): the header is
zeroth-order (a region), the mined baseline first-order (one identity across frames).

### F.2 E10 — the 8-byte chunk header with a TRAJECTORY-PATTERN byte

`genomevault/hdv_validation/hdc_experimentation/experiments/E10_chunk_metadata_index/config.yaml`
and `output/PROOF_PACKAGE.md`. The catalogue lists this DOCUMENTED-ONLY ("config+results but no run
script currently in the tree"); the schema and the measured results are both present and are
recorded here because the schema is the closest thing in either repo to a time-story in a byte.

Eight `uint8` fields per chunk: `family`, `template_id`, **`trajectory_pattern`**, `gc_content`,
`bank0_nonzero`, `bank1_nonzero`, `bank2_nonzero`, `flags`.

**The trajectory byte** is the transferable part: bits 0–1 carry the pattern type
(`MONO_UP` / `PEAK_DROP` / `MONO_DOWN` / `AMBIGUOUS` — the λ-trajectory shapes of B.3), bits 2–7
carry the average λ_optimal scaled to 0–63. Its declared routing:

| pattern | route | why |
|---|---|---|
| `MONO_UP` | aggressive path | matches the prior; safe to compress / skip |
| **`PEAK_DROP`** | **preserve path** | **a real deviation is here — break the chain, preserve it** |
| `MONO_DOWN` | conservative path | wrong lens for this region |
| `AMBIGUOUS` | conservative path | middle λ |

That is the routing shape the cell problem wants: a two-bit read, carried in metadata, that says
whether a span is ordinary, carries a real event, or cannot be read — decided before any expensive
member is convened.

**Measured, reported whole including what failed** (PROOF_PACKAGE, 10,000 chunks of 5,897,587):
- index size **45.0 MB** for 5.9 M chunks at 8 bytes — SUPPORTED (target <60 MB);
- family prediction **100.00 %**, GC-content correlation **1.0000** — SUPPORTED (target >99 %);
- skip-decompression for the F5 family **100 %** — SUPPORTED (target >95 %);
- **query routing NOT SUPPORTED** — 9,923 ns routed against 11,058 ns baseline, a **1.11× speedup**
  where the target was 350 ns and the config expected 1.55×. The package's own note: *"Target was
  aggressive; infrastructure validated."*
- trajectory distribution over the sample: `AMBIGUOUS` 62.0 %, `PEAK_DROP` 31.5 %, `MONO_UP` 5.1 %,
  `MONO_DOWN` 1.3 %.

**Read honestly: the header's ACCURACY and SIZE delivered; its routing SPEEDUP did not.** The
saving is not automatic and must be measured on our own data, not assumed from this precedent.

### F.3 Storage — the precision ladder, and what the founder's int16 point means concretely

IMPLEMENTED-AND-WORKING. `.../quantization/generate_int4_quantized_h5.py:23` (int4 quantise then
two-values-per-byte nibble pack), `:59` (unpack); binary and ternary siblings; binary hypervectors
packed into `uint64` with a cached 16-bit popcount LUT for Hamming search
(`genomevault/hypervector/index.py:54,453`, LUT `operations/hamming_lut.py:25`, `pack_bits` /
`unpack_bits` at `encoding/packed.py:12`).

The founder, 2026-09-21: *"our actual read of the data shows that int16 is good enough for lossless.
It's pretty simple RBG microscopy, so seems reasonable that int16 and float32 would be
byte-identical. Otherwise, yeah ... Then float64 just becomes simply absurd."* The source volumes are
`uint16` and a region profile is integer COUNTS, so the ladder above is the concrete form of that
point: the comparison a key needs is a packed-integer Hamming, not a float64 cosine over an
unquantised accumulator (`substrate/compose/key.key_resemblance` → `hdc.banks.bank_similarity`,
measured 2026-09-21 as a float64 cosine over a float32 accumulator).

**A correction the founder made the same day, and it governs the ladder too:** the ~21 % density of
A.2 is NOT a law of nature. Verbatim: *"the ~21% sparsity from the documentation was born of the
specific form I built in my GenomeVault project, to encode nucleotide data. Not really a law of
nature, and the architecture should reflect the data its encoding."* Density for microscopy is a
question the data answers, never a constant inherited from the four-symbol alphabet.

### F.4 Corrections to Parts A–E, and provenance warnings for anyone mining GenomeVault

1. **"Vibe collapse" (encode at high k, decode at low k) is REFUTED BY ITS OWN RESULTS.** B.1 records
   it without qualification and the lead repeated it on 2026-09-21 as a candidate cheap filter. The
   catalogue: it is IMPLEMENTED (`E26b_vibe_collapse.py:77`) but its *committed* results **lose all
   four comparisons** while a doc labels it "(Validated)". Treat as a useful negative to re-check,
   never as a mechanism to build on. The real prefilter is F.1.
2. **`genomevault/hypervector/` is DEPRECATED** (`__init__.py:4-13` → use
   `hypervector_transform.AdaptiveEncoder`). The live tree is `genomevault/hypervector_transform/`
   plus `hdv_validation/hdc_experimentation/`. Strong ideas — the ECC (ε,δ) budget allocator,
   bit-packed Hamming, the bio-aware decoder — live in the DEAD package and need re-wiring, not
   reinvention.
3. **The literal 3D-h5 tensor was NOT confirmed.** The real unusual layout is a multi-bank ×
   multi-precision LADDER h5 with int4 nibble packing (F.3).
4. **Codebook independence is a GO/NO-GO GATE, not an assumption.** A committee sharing one codebook
   gave ~100 % CORRELATED errors and bought zero error correction; the fix is a per-encoder seed, and
   it is validated as a gate (max φ < 0.25, scaled 4-way < 35, including the margin-0 worst case).
   `.../shared/clinical_encoders/multi_seed_encoder.py:8-18,434,640`; gate at
   `.../E25_clinical_committee/scripts/E25e_independence_matrix.py:77,320,343`. B.2 states the
   finding; this records that it is a gate we are obliged to MEASURE, which is why
   `data/archetypes/independence_map.json` exists (1,642 pairs).
5. **The writes-per-dimension capacity law `(N·k)/D` is DOCUMENTED-ONLY** in the catalogue's own
   assessment, as is the three-tier uncertainty storage. A.6 states them as settled; they are
   recovery targets.

### F.5 What transfers here, and at which order

| GenomeVault mechanism | cell-tracking use | order (Law 28) | state here |
|---|---|---|---|
| bank-magnitude header, percentile-calibrated | a per-region metadata read available at frame one | region (zeroth) | NOT BUILT; `ObjectRecord.bank_row_totals` and `profile_rows` already carry the magnitudes |
| paired layer bits, `00` = abstain | the informational zero inside the header | region | NOT BUILT |
| bitwise vote over the signature | the cheap-and-dirty prefilter before any member is convened | region | NOT BUILT; `hdc.position.signature` / `hamming` / `discriminates` exist with ZERO production consumers |
| E10 trajectory byte (`PEAK_DROP` → preserve) | routing a span as ordinary / eventful / unreadable | chain | NOT BUILT |
| int4 nibble pack, `uint64` popcount Hamming | the key comparison, in place of a float64 cosine | — | NOT BUILT |
| per-encoder seeds as an independence GATE | measuring that our banks fail independently | — | measured once (`independence_map.json`) |
| adaptive-k by difficulty | spending dimensions where a region is ambiguous | region | NOT BUILT |

**The discipline that governs every row of that table:** none of it is a decision. Each is a
measurement or a route, correct by definition, which NARROWS what the conclave is asked (Law 4).
The bodies still hold the signs and still decide, and a header that disagrees with a body is a fact
about the header, recorded, never an override.
