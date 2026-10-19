# RSNA Knee: anatomical object recognition

This is a classical-AI computer-vision pipeline grounded in **What an \<Object> Is**. Complementary
lossy measurements describe knee structures; anatomical relations combine those readings into named
objects and one physical knee map. Cheap squint views and known neighbours narrow expensive native
questions. Each useful value is computed once at its valid scope and shared with its consumers.

The current build establishes anatomical recognition and reports each object's identity with its
addressed pixel supports. These object pixel bundles are the starting input for the later,
human-specified diagnostic verdict: damage or abnormal states of the identified anatomy. Read [the original conversation](docs/conversations/2026-10-13-the-thesis.md) and
[the theory](docs/THEORY_OF_THE_CASE.md) before proposing changes. Follow
[FULL_BUILD_PLAN §0](docs/FULL_BUILD_PLAN.md#0-grounding-every-session-start-and-every-compaction)
for the complete grounding sequence. The plan's §13 points to the sole current task packet.

## Production requirements

Efficiency and correctness are built together: use anatomical priors and selected native views before
heavy computation, share source-owned measurements, and compile/fuse meaningful residual work with
reference checks. Useful priors need not be perfect. Performance figures never define anatomy.

Finish each study's configured output, then release its decoded images, derived arrays and caches.
Parallel execution bounds submitted and waiting results with the active worker count; completed
studies' working data do not accumulate across the cohort. Retained pixel supports remain addressable
for downstream consumers. The final diagnostic layer will run before that study's completed boundary.

[The binding competition envelope is FULL_BUILD_PLAN §16.9](docs/FULL_BUILD_PLAN.md#169-competition-resource-envelope-w8b-storage-closure-and-w10-verification):

- Competition notebook: **at most 9 hours**, **internet disabled**.
- Documented CPU route: **4 cores, 30 GB RAM**; saved output in `/kaggle/working`: **20 GB total**.
  Scratch has a separate measured quota and session lifetime. Recheck the selected environment;
  the plan includes GPU-route differences and the official sources.
- **W8b must implement and verify storage closure**, preserving every required reading, decision,
  address and reconstruction contract. Moving durable evidence into disposable scratch is insufficient.
- **W10 must verify the integrated compute envelope**: startup/JIT, decoding, recognition, worker/queue
  memory, IPC, hashing/compression and output. Distinguish target-environment measurements from
  projections for the approximately 1,300-study hidden workload and account for capacity left for
  later stages. One proof study or kernel replay does not establish competition fit.

These are deployment limits, not tunable recognition thresholds. Read §§1.3 and 16.6–16.9 of the plan
and [the build workflow](docs/work/current/BUILD_WORKFLOWS.md) when constructing or reviewing any family.

## Run and verify

Use the locked project environment (`uv sync`). One production entry point serves every mode:

```bash
.venv/bin/python scripts/run_interiors.py --study-uid <uid> --root <data-root> --workers 1 --run <new-interiors-dir> --main-run <new-main-dir>
.venv/bin/python scripts/run_interiors.py --labeled --root <data-root> --workers 2 --run <new-interiors-dir> --main-run <new-main-dir>
.venv/bin/python scripts/run_interiors.py --split test --root <data-root> --workers 1 --run <new-interiors-dir> --main-run <new-main-dir>
bash scripts/ci_local.sh
```

Drawing is development-only: add `--draw` to inspect native evidence; production leaves it off.
Compare saved receipts with `scripts/compare_receipts.py` under the plan's equivalence/change rules.
The CI gate, ledger, Vulture, recorded-kernel benchmarks and CodSpeed complement native-image and
whole-run acceptance. Their passing does not establish complete anatomical coverage or resource fit.

## Governing documents

- [AGENTS.md](AGENTS.md): resident project instructions; [CLAUDE.md](CLAUDE.md) imports them and the grounding documents.
- [FULL_BUILD_PLAN.md](docs/FULL_BUILD_PLAN.md): requirements, contracts, ordered work and completion rules.
- [BUILD_WORKFLOWS.md](docs/work/current/BUILD_WORKFLOWS.md): worker routing, verification and integration.
- [OBJECTS_AND_CONDITIONS.md](docs/OBJECTS_AND_CONDITIONS.md): anatomical domain descriptions.
- [RESOLVING_THE_PARTS.md](docs/RESOLVING_THE_PARTS.md): each part's views and complementary measurements.

`archive/` and `archive2/` are outside the active project and remain unread unless Rohan requests them.
