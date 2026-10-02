# K01 — Characterization: what the tools, the target and the machines actually are

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K01'` |
| **Depends on** | K00 |
| **Consumed by** | K02 (environments, tool configuration), K05 (decoders, census), K07 (resampling backends), K18 (packaging), every chapter that chooses a language |
| **Commit label / tag** | `knee/K01` · `knee-K01` |

## 1. Purpose and authority

To measure before freezing anything that depends on what the tools, the deployment target and the machines
actually are.
- **The founder:** "ACTUALLY look into it"; "use the one that's local, not the one that's installed from PyPI";
  "for heavy compute, I have the Mac Pro sitting around. SquishOS has it registered, including how to access and
  use".
- **The accord:** "characterize deployment/tool capabilities before freezing language and Python choices"
  (design round 1, amendment 4).
- **Non-goals:** no production code; no environment rebuilt (that is K02); no submission.

## 2. Dependencies and consumers

- **Produced:**
  - `docs/book/records/K01-capabilities.toml`: tools, runtimes and machines only, with no
    competition-derived content; dated, with how each fact was measured.
  - the local data census (transfer syntaxes, tag presence, counts): a derived record, which may enter git
    (AGENTS override 7). Its raw logs stay in `data/records/K01/`.
- **Consumers:**
  - K02 picks the VERIFY Python and builds DEPLOY from the measured Kaggle versions.
  - K05 chooses decoders.
  - K18 packages for the measured runtime.
- **Minimal launch procedure, independent of K02** (Codex design round 2, D9):
  - plain scripts in `tools/characterize/`, standard library plus the existing venv;
  - labelled as measurement scaffolding, never imported by `knee`;
  - retired, or kept as historical instruments, by row in `MIGRATION.md`.

## 3. Mechanism

Five measurements, each recorded with its date, its method and its raw output location.

1. **The local Detective.**
   - Its identity: `python -m Detective.cli --version` with `PYTHONPATH=$HOME/tools/Detective:$HOME/tools/Wesker`,
     plus the git revisions of both checkouts.
   - Its advertised capabilities: `--help`.
   - Its operational capabilities, exercised through the protocol:
     - `regime` on this repository, its printed blocks followed exactly;
     - one `diagnose` on a legacy pure function (`src/RSNA_Knee/scoring.py::auc_status`), read whole.
   - The project interpreter it runs under is recorded. The current venv is conda-based, and EP-C4 warns
     against that.
   - **Before K02's wrapper exists,** these runs use the module form directly. Each run's complete stdout and
     stderr is captured to `data/records/K01/detective/<stamp>-<verb>.log` with its exit status, and read whole
     (the house protocol). The filter hook does not see the module form, which is why the capture matters. K02
     re-runs this probe through `just detective`.
2. **The Kaggle runtime** — a **private dry-run kernel**, never a submission.
   - The push follows `../../CLAUDE.md`'s Kaggle protocol: a push dir with `kernel-metadata.json` and
     `competition_sources`, the CLI authenticated from `KAGGLE_API_TOKEN` loaded from
     `~/Projects/Kaggle_Killer/.env`.
   - The script prints:
     - `sys.version`, the platform and CPU flags (AVX2? AVX-512?), the core count, RAM and free disk;
     - which directories are writable;
     - the installed versions of numpy, scipy, numba (with an `njit` compile test and Numba-cache behaviour
       under `/kaggle/working`), pydicom, pylibjpeg (and its plugins), gdcm, SimpleITK, scikit-image and
       pandas;
     - the decode of every public test sample slice, grouped by transfer-syntax UID.
3. **The Mac Pro** (`squishhub`), through SquishOS only.
   - **Identify the node first:** `squishos-fleet profile squishhub` (no network), then `card` and
     `verify squishhub`; the card says its last verification is stale. The compute runbook says it plainly:
     "Measure what that environment actually has before trusting a workload to it".
   - A probe job via `squishos-compute run squishhub -- '<probe>'`, measuring:
     - the Python versions, uv's presence, free disk and cores;
     - Docker's presence;
     - whether Numba 0.68 installs and compiles on x86_64 macOS 12.
   - Every code printed (`denied`, `blocked`, `absent`, `unmet`, `unknown`) is recorded as printed.
   - **Placing the Kaggle token on the node is put to the founder first.** No secret moves without his word at
     that moment.
4. **The local data census** (`data/` only): the transfer-syntax UIDs and the tag presence over every locally
   present DICOM, with the series classes present. Locally there is one class, sagittal FS; the full census over
   all 24,371 series is K05's.
5. **Hook coverage.** Does the SquishOS filter hook see `python -m Detective.cli`? On 2026-10-02 it did not.
   Re-confirm, and record.

## 4. Contracts

- `K01-capabilities.toml` holds sections `[detective]`, `[kaggle_runtime]`, `[macpro]`, `[dev_seat]` and
  `[hooks]`.
- Each entry is `{value, measured_at, method, raw}`, where `raw` is the path to its gitignored log.
- An unmeasurable fact reads `"unknown"` with its reason, never a guess.

## 5. Implementation choice

- Stdlib Python scripts and the CLIs named above.
- No reuse question arises: these are measurements, not code the build keeps.

## 6. Verification

- The scripts run read-only.
- Each fact is cross-checked where a second route exists:
  - the Kaggle versions, via `pip list` and the module's own `__version__`;
  - the Mac Pro, via `profile` and the probe.

## 7. Integration

K02's configuration and every language decision cite `K01-capabilities.toml` by key.

## 8. Acceptance

Written first: `acceptance/K01.toml`.
- **Behavioural correctness:**
  - each of the five measurements is recorded, or carries a named "unknown";
  - the dry-run kernel's status is `COMPLETE` and its log is read whole;
  - `regime` has run, and its printed next action is taken or recorded.
- **Representation fidelity:** every TOML value traces to its raw log.
- **Domain validity:** the decode test covers every transfer syntax the public sample holds, and the gaps are
  named.
- **Performance evidence:** the Numba cold-compile time on Kaggle and on the Mac Pro, scoped as "a 20-line probe
  kernel".
- **Evidence scope:** the runtimes as of the measuring date. Kaggle images change.
- **Invalidation:**
  - a Kaggle image update, detected by K18's runtime check;
  - a Detective or Wesker checkout revision change;
  - a change to the Mac Pro's OS or Python.
- **No submission has been made.**

## 9. Open matters

- **Facts:** all of the above. K02 waits on them.
- **Policy:**
  - placing the token on the Mac Pro;
  - whether to extend the SquishOS hook at its source.

## 10. Provenance and status log

- **Sources:**
  - SquishOS `docs/runbooks/compute.md`, the operative path for jobs. `docs/runbooks/fleet.md` still says that
    offloading is NOT-BUILT (its l.52–53). That stale line belongs to SquishOS, to be fixed there;
  - `../../CLAUDE.md` (the Kaggle protocol);
  - Detective `ARCHITECTURE.md` §11;
  - `THE_KNEE.md` §3.6 and §4.
- **2026-10-02:** specified in K00.
- **2026-10-02, revision 1:** the pre-K02 Detective capture (F29); the node identified before any job (F37);
  the compute runbook cited as operative (F36); the census as a derived record (R2).
