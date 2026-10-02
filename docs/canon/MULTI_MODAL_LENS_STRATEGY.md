# Multi-Modal Lens Discovery Strategy

## Problem Statement

The bimodal pattern in AT_DOMINANT thresholds reveals that **a single "optimal" lens configuration is insufficient**. Different genomic motifs require different detection parameters:

- **TATA boxes** may need strict AT filters (19.66% genome coverage)
- **Alu elements** may need broader AT filters (23.67% genome coverage)
- **CpG islands** need GC-dominant filters with specific ratios

A "one-size-fits-all" approach would either:
- Miss true motifs (if too strict)
- Generate false positives (if too broad)

## Solution: Multi-Modal Lens Library

Instead of finding THE optimal configuration, we:
1. Find ALL local minima in the 6D parameter space
2. Cluster them into ~5-10 "lens families"
3. Biologically validate each family against known motifs
4. Build a library of specialized lenses

---

## Pipeline Architecture

### Phase 1: Exhaustive Parallelized Grid Search

**What it does:**
- Tests all 12,500 threshold configurations
- Uses 10-core parallelization (10× faster than sequential)
- Saves full results to disk (not just top 10)

**Output:**
- `output/lens_library/full_grid_search_results.npz`
  - configs: (12500, 6) array
  - errors: (12500,) array
  - frequencies: (12500, 4) array

**Why save everything:**
- Enables local minima detection
- Allows post-hoc analysis
- Can reanalyze without re-running grid search

---

### Phase 2: Local Minima Detection (3D Topology)

**What it does:**
- Finds configurations where error is lower than all neighbors
- Uses Euclidean distance in 6D parameter space
- Filters minima too close in error space

**Algorithm:**
```python
for each config:
    neighbors = all configs within radius r
    if error(config) < min(error(neighbors)):
        local_minimum = True
```

**Parameters:**
- `neighborhood_radius = 0.15` (relaxed to find more modes)
- `min_separation = 0.005` (tight to avoid duplicates)

**Output:**
- `output/lens_library/local_minima.json`
- Expected: 50-100 distinct modes

**Biological interpretation:**
Each local minimum likely corresponds to a biologically meaningful detector:
- Mode 1 (error=0.708): Broad AT detector → Alu/LINE/TATA
- Mode 2 (error=0.738): Strict AT detector → Core TATA only
- Mode 3: GC detector → CpG islands
- Mode 4: Extreme AT → Heterochromatin/poly-A tails
- ...

---

### Phase 3: Hierarchical Clustering

**What it does:**
- Clusters 50-100 local minima into 5-10 "lens families"
- Uses Ward linkage (minimizes within-cluster variance)
- Picks lowest-error member as family representative

**Why clustering:**
- 50-100 lenses is too many for practical use
- Many minima are probably slight variations of the same detector
- Clustering reveals the fundamental "detector families"

**Output:**
- `output/lens_library/lens_families.json`
- 8 lens families, each with:
  - Representative configuration (lowest error)
  - Member count
  - Average error across family

**Example output:**
```json
{
  "family_id": 1,
  "member_count": 12,
  "representative_error": 0.7079,
  "representative_config": {
    "at_dominant_ratio": 1.7,
    "at_dominant_percentile": 75,
    ...
  },
  "motif_specialization": null  // To be determined in Phase 4
}
```

---

### Phase 4: Biological Validation (Edge Cases)

**What it does:**
- Tests each lens family against synthetic edge cases
- Validates specificity (does it detect what we expect?)

**Edge case sequences:**
1. **pure_AT**: `ATAT` × 256 → Should trigger AT_DOMINANT
2. **pure_GC**: `GCGC` × 256 → Should trigger GC_DOMINANT
3. **pure_YR**: `TGCA` × 256 → Should trigger HINGE (Y→R transitions)
4. **pure_YY_RR**: `TTGG` × 256 → Should NOT trigger HINGE
5. **poly_A**: `A` × 1024 → Should trigger EXTREME_AT
6. **poly_G**: `G` × 1024 → Should trigger EXTREME_GC
7. **TATA_canonical**: `TATAAA` × 170 → AT-rich motif
8. **CpG_canonical**: `CGCGCG` × 170 → GC-rich motif
9. **heterochromatin**: `AAAAATTTTT` × 102 → Low complexity AT
10. **purine_rich**: `AGAG` × 256 → Tests purine/pyrimidine asymmetry
11. **pyrimidine_rich**: `TCTC` × 256 → Complementary test

**Validation metrics:**
- Precision: What % of detected chunks match expected motif?
- Specificity: Does it reject non-matching sequences?

**Output:**
- `output/lens_library/biological_validation.json`
- Each family gets a "motif specialization" label

**Example:**
```json
{
  "family_id": 1,
  "motif_specialization": "broad_AT_detector",
  "detects": ["TATA_canonical", "pure_AT", "Alu_elements"],
  "precision": 0.92
}
```

---

### Phase 5: Confidence Trajectory Profiling

**This is the key innovation**: Different motifs show different confidence patterns across λ values.

**What it does:**
- For each lens family, test known motifs across λ ∈ [0, 0.2, 0.4, 0.6, 0.8, 1.0]
- Classify trajectory pattern
- Determine optimal λ value

**Trajectory patterns:**

**Pattern 1: Monotonic Increase**
```
Confidence: [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
            λ=0 ─────────────────────────> λ=1
```
- **Interpretation**: Matches consensus perfectly
- **Optimal λ**: 1.0 (full lens weight)
- **Example**: Canonical Alu element

**Pattern 2: Peak-then-Drop** ⭐ **THIS IS THE CRITICAL PATTERN**
```
Confidence: [0.3, 0.5, 0.7, 0.85, 0.7, 0.5, 0.3]
            λ=0 ─────↑─────────────────> λ=1
                   λ=0.4 (peak)
```
- **Interpretation**: REAL VARIATION from consensus
- **Optimal λ**: 0.3-0.4 (partial lens influence)
- **Example**: TATA box with SNP (A→G), Alu variant
- **Why the peak**: Lens provides structural context ("this is Alu") without forcing to consensus sequence

**Pattern 3: Monotonic Decrease**
```
Confidence: [0.7, 0.6, 0.5, 0.4, 0.3, 0.2]
            λ=0 ─────────────────────────> λ=1
```
- **Interpretation**: Wrong lens applied
- **Optimal λ**: 0.0 (ignore lens entirely)
- **Example**: Applied Alu lens to LINE element

**Output:**
- `output/lens_library/confidence_trajectories.json`
- For each (family, motif) pair:
  - Average trajectory across test sequences
  - Optimal λ value
  - Pattern classification

**Example:**
```json
{
  "family_id": 1,
  "motif": "TATA_box",
  "trajectory": [0.3, 0.55, 0.72, 0.84, 0.68, 0.51],
  "optimal_lambda": 0.4,
  "pattern": "peak_drop",
  "interpretation": "Real variation - use partial lens influence"
}
```

---

## Query-Time Multi-Modal Decoding

**After building the lens library**, the query engine works like this:

```python
def decode_chunk(chunk_hdv):
    # Try all lens families
    candidates = []

    for family in lens_library:
        # Compute confidence trajectory (quick, 6 evaluations)
        trajectory = [decode_with_lambda(chunk_hdv, family, λ)
                     for λ in [0, 0.2, 0.4, 0.6, 0.8, 1.0]]

        # Classify pattern
        pattern = classify_trajectory(trajectory)

        # Score against family's expected pattern
        if pattern == family.expected_pattern:
            optimal_λ = trajectory_peak(trajectory)
            confidence = max(trajectory)

            candidates.append({
                'family': family,
                'confidence': confidence,
                'optimal_λ': optimal_λ,
                'pattern': pattern
            })

    # Return best-matching lens
    best = max(candidates, key=lambda c: c['confidence'])

    # Decode with optimal λ for this lens
    final_sequence = decode_with_lambda(
        chunk_hdv,
        best['family'],
        best['optimal_λ']
    )

    return final_sequence, best['confidence'], best['family'].motif_type
```

**What this achieves:**
1. **Automatic motif detection**: Identifies which type of genomic region this is
2. **Adaptive lens selection**: Uses the specialized detector for this motif
3. **Optimal λ selection**: Balances context vs. variation based on pattern
4. **Variant preservation**: Peak-then-drop pattern → use intermediate λ → preserve real SNPs

---

## Expected Lens Families

Based on the bimodal pattern observed, we expect ~5-10 families:

1. **Broad AT Detector** (23.67% coverage)
   - Motifs: TATA, Alu, LINE, AT-rich regions
   - Optimal λ: Variable (0.4 for variants, 1.0 for consensus matches)

2. **Strict AT Detector** (19.66% coverage)
   - Motifs: Core TATA boxes, extreme AT regions
   - Optimal λ: 0.3-0.4 (likely shows peak-drop for real TATA boxes)

3. **GC-Dominant Detector**
   - Motifs: CpG islands, promoter regions
   - Optimal λ: 0.4-0.6

4. **Extreme AT Detector**
   - Motifs: Heterochromatin, poly-A tails, satellite DNA
   - Optimal λ: 1.0 (matches consensus)

5. **Extreme GC Detector**
   - Motifs: High-GC genes, poly-G runs
   - Optimal λ: 1.0

6. **Hinge-Dominant Detector**
   - Motifs: Y→R / R→Y transition-rich regions
   - Optimal λ: TBD

7. **Balanced Detector** (no strong bias)
   - Motifs: Coding regions, exons
   - Optimal λ: 0.0-0.2 (minimal lens influence)

8. **Multi-Layer Detector** (TATA + CpG, etc.)
   - Motifs: Complex regulatory regions
   - Optimal λ: Context-dependent

---

## Validation Against Real Genome

**Next steps after Phase 5:**

1. Download UCSC annotations:
   - TATA boxes (experimentally validated)
   - CpG islands (algorithmically defined)
   - Repeat elements (RepeatMasker: Alu, LINE, SINE)

2. For each lens family:
   - Apply to whole genome
   - Compute overlap with ground truth
   - Measure precision/recall/F1

3. Build ROC curves:
   - True positives: Detected chunks that overlap ground truth
   - False positives: Detected chunks with no overlap
   - False negatives: Ground truth regions not detected

4. Annotate lens families with biological specificity:
   ```json
   {
     "family_id": 1,
     "best_for": "TATA boxes",
     "precision": 0.87,
     "recall": 0.92,
     "F1": 0.89
   }
   ```

---

## Why This Works

### The Blind Men and the Elephant

We're taking a bottom-up approach:
1. **We don't know** a priori which parameters detect which motifs
2. **But we can** brute-force test all parameter combinations
3. **The error landscape** naturally clusters into biological categories
4. **Local minima** = distinct biological detectors
5. **Ground truth validation** tells us what each detector is finding

This avoids:
- Hand-tuning thresholds for each motif (too brittle)
- Assuming we know all genomic motif types (we don't)
- Missing novel motif classes (we'll discover them as local minima)

### Connection to Confidence Trajectories

The λ trajectory approach is the **algorithmic implementation** of the "peak-then-drop = real variation" insight:

- We don't manually decide when to use λ=0.4 vs λ=1.0
- **The trajectory pattern tells us automatically**
- Monotonic increase → use λ=1.0
- Peak-then-drop → use λ_optimal (at peak)
- This is a **data-driven variant preservation strategy**

---

## Computational Cost

### Grid Search (Phase 1)
- **Serial**: 12,500 configs × 2.3s/config = 7.97 hours
- **10-core parallel**: 7.97 hours / 10 = **~48 minutes**
- **One-time cost** (results saved to disk)

### Local Minima Detection (Phase 2)
- Distance matrix: O(N²) where N=12,500
- **~5-10 minutes** (dominated by pdist calculation)

### Hierarchical Clustering (Phase 3)
- **~1 minute** (scipy.cluster.hierarchy is fast)

### Biological Validation (Phase 4)
- 8 families × 11 edge cases = 88 tests
- **~1 minute** (synthetic sequences, no I/O)

### Confidence Trajectories (Phase 5)
- 8 families × 11 motifs × 6 λ values = 528 decodes
- **~2 minutes** (fast decoding)

**Total: ~60 minutes one-time cost**

**Query time:**
- Per-chunk: 8 families × 6 λ values = 48 decodes
- With lens caching: **~10-20 μs per chunk**

---

## Files Created

```
genomevault/hdv_validation/hdc_experimentation/
├── query/
│   ├── multi_modal_lens_discovery.py       (Phases 1-3)
│   ├── biological_lens_validation.py       (Phases 4-5)
│   └── threshold_grid_search.py            (Original, for comparison)
├── output/lens_library/
│   ├── full_grid_search_results.npz        (12,500 configs, all errors)
│   ├── local_minima.json                   (50-100 modes)
│   ├── lens_families.json                  (8 representative lenses)
│   ├── biological_validation.json          (Edge case results)
│   └── confidence_trajectories.json        (λ profiles per motif)
└── docs/
    └── MULTI_MODAL_LENS_STRATEGY.md        (This file)
```

---

## Next Actions

1. ✅ **Phase 1-3 running now** (~48 min, 10-core parallel)
2. **When complete, review** `lens_families.json` to see discovered modes
3. **Run Phase 4** biological validation
4. **Run Phase 5** confidence trajectory profiling
5. **Integrate** lens library into query engine
6. **Validate** on real genomic regions with UCSC annotations

---

## Key Innovation: Pattern Recognition for Variant Preservation

Traditional decoders: "Should I trust the lens or not?"

**Our approach:** "What does the confidence trajectory tell me?"

- **Monotonic increase**: Data agrees with consensus → trust lens fully
- **Peak-then-drop**: Real biological variation → use optimal λ at peak
- **Monotonic decrease**: Wrong lens → ignore it

This is a **principled, data-driven approach** to the fundamental problem of balancing context (lens) vs. variation (data).

The multi-modal lens library ensures we have **specialized detectors** for different genomic contexts, and the trajectory analysis ensures we apply **optimal λ values** automatically.

---

**Author:** Claude Code
**Date:** November 23, 2025
**Status:** Phases 1-3 in progress, Phases 4-5 ready to run
