# The migration ledger: legacy `RSNA_Knee` and `tools/` → `knee`

One row per legacy unit (the founder, 2026-10-02: "design things fresh, only use older stuff when it's genuinely the
best approach").
- A unit leaves only when its row's **decision** and **retirement acceptance** are recorded by the owning chapter.
- Consumers are checked first, with Serena `find_referencing_symbols` and an AST import scan.
- Until a unit leaves, its tests keep running in the gate.
- An Import Linter contract forbids `knee` from importing `RSNA_Knee` (K02).

`decision` takes one of four values:
- `reuse-after-review`: the logic moves into `knee`, is re-converged with the local Detective, and gets intent
  tests;
- `rewrite`;
- `retire`;
- `historical`: kept only as a historical instrument, never as a decision path.

| legacy unit | symbols (production consumers today) | owner | decision (argument) | replacement | retirement acceptance |
|---|---|---|---|---|---|
| `src/RSNA_Knee/scoring.py` | `roc_auc`, `average_ranks`, `macro_auc`, `auc_status` | K03 | reuse-after-review (the metric is fixed; pure; pinned; 16 intent tests) | `knee.core.score` | SAME on toy columns; new certificates; legacy tests retired with it |
| `src/RSNA_Knee/kneediff.py` | `residual_z`, `classify_cell`, `survival_fraction` | K10 | rewrite (the denominator and the record's semantics change) | `knee.core.deviation` | K10 acceptance; consumers checked |
| `src/RSNA_Knee/kneediff.py` | `make_or_break_verdict` | K09 | historical (the fixed instrument never moves; LADDER) | stays with `tools/make_or_break.py` | — |
| `src/RSNA_Knee/platonic_reference.py` | `build_reference`, `residual_map`, `detrended_residual_map`, `max_masked_window_density`, `max_window_density` | K09, K10 | rewrite (median and MAD, the variance decomposition, fallback; windows by running sums) | `knee.build.reference`, `knee.core.deviation` | K09 and K10 acceptance |
| `src/RSNA_Knee/anatomy.py` | bone masks, `joint_line`, `condyles_and_notch`, `classify_bone_groups`, `build_zone_labels` | K07, K08, K13 | reuse-after-review for the rule logic; the single-study template is superseded | `knee.build.atlas`, `knee.build.bootstrap` | K08 acceptance |
| `src/RSNA_Knee/hdc_encoder.py` | `ternary_cell`, `ResidualHDCEncoder`, `similarity`, `bundle_prototype` | K04, K12 | retire (random collisions; the licensed 0 dropped; prototypes; KNEE_ARCHITECTURE §3.5.1) | `knee.core.ledger`, `knee.core.layout` | K12 acceptance; its generated suite retired with it |
| `src/RSNA_Knee/report_parser.py` | `parse_report`, `sentence_asserts`, term tables | K06 | reuse-after-review (unique, error-driven multilingual lexicon; gold dependence recorded) | `knee.orchestrate.text` | SAME on all reports where behaviour is unchanged |
| `tools/register_and_export.py` | `derive_side`, `load_canonical_volume`, `register_full`, `n4_correct`, `normalize_intensity`, `histogram_match` | K07 | `derive_side` and `load_canonical_volume`: reuse-after-review, with chirality from three witnesses; `register_full`: rewrite (keep the transform; stored values); `n4_correct`: rewrite as a measured nuisance field, never applied in place (THEORY II.1; ARCH §3.1); `normalize_intensity` and `histogram_match`: retire, replaced by the gain specialist's γ_s (ARCH §3.3.3, §3.4.1) | `knee.core.frame`, `knee.run.register` | K07 acceptance |
| `tools/register_normals.py`, `tools/build_true_layout.py`, `tools/select_normal_pool.py`, `tools/select_positive_pool.py` | pool and layout builders | K06, K09 | rewrite (roles from K03; report-negative pool from K06) | `knee.build.reference`, `knee.orchestrate.harness` | K09 acceptance |
| `tools/build_atlas.py` | atlas build | K08 | rewrite (unbiased template; extended zones; votes) | `knee.build.atlas` | K08 acceptance |
| `tools/fetch_labeled_studies.py`, `tools/fetch_from_bundle.py`, `tools/auto_resume_fetch.py`, `tools/fetch_watchdog.sh`, `tools/remote/` | fetching | K05 | the ranged-read logic: reuse-after-review if it passes SAME and adversarial tests; `pick_series`: retire (one series per study) | `knee.build.corpus` | K05 acceptance |
| `tools/parser_validate.py` | the parser's gold gate | K06 | reuse-after-review (reports disagreements with evidence) | `knee.orchestrate.text` | K06 acceptance |
| `tools/make_or_break.py` | the fixed instrument | K09 | historical | unchanged | — |
| `tools/lens_eval.py`, `tools/lens_eval2.py` | prototype lens reads | K25 | historical (THESIS §7.1 forbids prototypes as decisions) | — | K25 acceptance records them as historical |
| `tests/test_scoring.py`, `tests/test_kneediff.py`, `tests/test_detrend.py`, `tests/detective/*` | legacy tests and generated suites | with their units | retire with their unit, after the replacement's tests and certificates exist | — | per unit |

**External prior art** (not migrated; a decision recorded per chapter):

| prior art | chapter | decision |
|---|---|---|
| cell-tracking `accel.py` | K02 | the starting point; the backend registry is built fresh, its defects avoided (THE_KNEE §3.3) |
| cell-tracking `hdc/banks.py` | K04 | not shared (Q16): the knee needs a count-table-first API with declared limits and an exact level test |
| GenomeVault code | all | ideas only, never code (founder: "I'll be rebuilding it completely from scratch") |
| SquishOS `scripts/check_reference_manifest.py` | K00 | reused by path (house tool; `cited_by` caveat) |
