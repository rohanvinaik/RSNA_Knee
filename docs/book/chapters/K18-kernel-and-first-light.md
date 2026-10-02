# K18 — The kernel and first light

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K18'` |
| **Depends on** | K17 (emission), K02 (DEPLOY environment, packaging verbs); through them, every chapter K03–K16 |
| **Consumed by** | every chapter after it (`just firstlight` is in their acceptance), K27 |
| **Commit label / tag** | `knee/K18` · `knee-K18` |

## 1. Purpose and authority

To run the complete path, DICOM to `submission.csv`, in the deployment environment and in a private Kaggle dry
run, early. The result is the structure-alone run: scoped, measured and kept.
- **The accord:** "build a scoped end-to-end path early, then rerun it as breadth and intelligence are added"
  (Codex design round 2, final item 11).
- **D2:** first light is not a demo slice. It is the integration of whole chapters, scoped honestly.
- **THEORY Law 8 and the Kaggle protocol** (`../../CLAUDE.md`): never auto-submit.

## 2. Dependencies and consumers

**Produced:**
- **`knee.orchestrate.kernel.main(input_dir, artifacts_dir, out_path)`**, which runs, per study: ingest →
  registration → deviation and signatures → zone lenses → explanation → case-free decisions → emission (literal)
  → the writer.
- **Packaging:**
  - the `knee` package and its pinned runtime dependencies as a private Kaggle dataset (or a utility script), with
    a content inventory;
  - artifacts (atlas, references, phantom-free maps) as private datasets with manifests and checksums;
  - no native wheel yet.
- **`just firstlight`:** the scoped end-to-end run on a declared panel subset (G in rotation, N `checking`, and a
  fixed local sample). It writes the recognition table, the AUC (literal) and its SAME and decision checks against
  the previous first-light record. Every later integration-changing chapter re-runs it.
- **The private Kaggle dry run:** `kaggle kernels push` with `competition_sources`, `kernels status`, then
  `kernels output` read whole.

**Consumers:** K19–K27.

## 3. Mechanism

- **Per-study streaming:** one study in RAM per worker. Workers are declared from K01's Kaggle core and RAM
  measurement.
- **JIT warm-up** happens once per process, at a declared point. Cold compile time is measured apart from warm
  throughput. The Numba cache lives in `/kaggle/working`, if K01 found it writable and useful.
- **Every run's provenance** stamps the backend, the requested and effective JIT mode, the artifact digests and
  the code digest.

## 4. Contracts

- **The kernel reads only `/kaggle/input/...`** plus its attached datasets, and writes only `/kaggle/working`.
- **`submission.csv`** is validated by K03's validator before it is written.
- **Artifacts are private datasets** (competition rules 4.b.1; Private Sharing): never public, never in git.

## 5. Implementation choice

- **Python orchestration** over the chapters' kernels: Numba twins in production, references in the SAME checks.
- **Prior art:** `../../CLAUDE.md`'s submission protocol (push via the CLI; `competition_sources` mounts data).
  **Decision:** follow it exactly.

## 6. Verification

- **SAME:** the DEPLOY run against the VERIFY run on the local sample: decisions equal, values within each
  kernel's spec.
- **Integration tests through the real entry point** on authored synthetic DICOM fixtures, independent of
  competition data, kept in git.
- **The validator,** adversarially.

## 7. Integration

`just firstlight` becomes a standing acceptance step for K19–K27.

## 8. Acceptance

- **Behavioural correctness:**
  - the DEPLOY run completes on the local sample;
  - the private Kaggle dry run reaches `COMPLETE`, with its log read whole;
  - `submission.csv` validates;
  - **no submission is made.**
- **Representation fidelity:** DEPLOY and VERIFY decisions are equal; provenance stamps are present.
- **Domain validity:** the structure-alone recognition table and literal AUC on G (rotation) and N `checking`,
  each with its bounds, recorded as **the baseline**. "A score is information about what a module does, never a
  target."
- **Performance evidence:** cold JIT seconds; warm seconds per study; peak RSS per worker; the projected wall time
  for about 1,300 test studies against the 9-hour limit.
- **Evidence scope:** the exercised environment and inputs only (Codex design round 2, A7): not general
  correctness.
- **Invalidation:** any change in K03–K17, in the artifacts, or in the Kaggle image (re-checked against K01's
  record).

## 9. Open matters

- **Facts:** the runtime budget at full test size.
- **Policy:** none. The submit decision belongs to the founder at K27.

## 10. Provenance and status log

- **Sources:**
  - `../../CLAUDE.md` (the Kaggle protocol);
  - THE_KNEE §3.6, §4, §5 and §6 (D2);
  - Codex design rounds 1 and 2.
- **2026-10-02:** specified in K00.
