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
- **`knee.orchestrate.kernel.main(input_dir, artifacts_dir, out_path)`**, which runs, per study:
  1. ingest;
  2. registration;
  3. γ_s, deviation, and tissue identity and change;
  4. the zone lenses;
  5. explanation, gated by K13a's independence classes and entitlement;
  6. the case-free decisions;
  7. emission (literal, with unavailable keys skipped);
  8. the writer.
- **Packaging:**
  - the `knee` package and its pinned runtime dependencies as a private Kaggle dataset (or a utility script), with
    a content inventory;
  - artifacts (atlas, references, phantom-free maps) as private datasets with manifests and checksums;
  - no native wheel yet.
- **`just firstlight`:** the scoped end-to-end run on a declared panel subset (G in rotation, N `checking`, and a
  fixed local sample). It writes the recognition table, with each abstention's cause, and the AUC (literal).
  - The SAME checks are twin against reference, at this revision, in one environment.
  - The comparison with the previous first-light record is a *diff*, read against the behaviour-change record of
    the chapter that changed it. It is never SAME (`provenance/build/revision_1.md`, §F11).
  - Every later integration-changing chapter re-runs it.
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

- **DEPLOY against VERIFY** on the local sample. THESIS §12.5: "we claim the same answer within an environment,
  never across two". Decisions are equal, except where a value lies within its kernel's declared tolerance of a
  threshold. Those cases are listed, never hidden. Values agree within each kernel's spec.
- **Integration tests through the real entry point** on authored synthetic DICOM fixtures, independent of
  competition data, kept in git.
- **The validator,** adversarially.

## 7. Integration

`just firstlight` becomes a standing acceptance step for K19–K27.

## 8. Acceptance

Written first: `acceptance/K18.toml`.
- **Behavioural correctness:**
  - the DEPLOY run completes on the local sample;
  - the private Kaggle dry run reaches `COMPLETE`, with its log read whole;
  - `submission.csv` validates;
  - **no submission is made.**
- **Representation fidelity:** DEPLOY and VERIFY decisions are equal, boundary cases listed; provenance stamps
  are present.
- **Domain validity (discovery):** the structure-alone recognition table and literal AUC on G (rotation) and N
  `checking`, each with its bounds, recorded as **the baseline**.
  - Until the founder writes the independence bar, most findings abstain with `dependence_unknown`. That is the
    baseline's honest content, a problem named for K13a's bar and never routed around (R1).
  - "A score is information about what a module does, never a target."
- **Performance evidence:** places, lenses and rounds counted per study; cold JIT seconds; warm seconds per study;
  peak RSS per worker. The projected wall time for about 1,300 test studies against the 9-hour limit is the one
  place where seconds are a deployment constraint, not only information.
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
- **2026-10-02, revision 1:**
  - the path gated by K13a (F06);
  - SAME within one environment, and the first-light diff read against intent (F11; THESIS §12.5);
  - the baseline's abstentions as its finding (R1);
  - work counted (F39).
