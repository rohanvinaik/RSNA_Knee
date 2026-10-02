# K02 — Verification infrastructure

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K02'` |
| **Depends on** | K01 (the measured Kaggle runtime, the Detective identity, the Mac Pro environment) |
| **Consumed by** | every later chapter: environments, `just` verbs, the gate, the backend registry, the SAME harness, events, the store |
| **Commit label / tag** | `knee/K02` · `knee-K02` |

## 1. Purpose and authority

To build the machinery every chapter is verified with, before anything it verifies.
- **The founder:** "everything guided by the right tooling", "fully mutant-pinned through Detective", "use the one
  that's local".
- **The accord:** two environments; the decision-preserving SAME; the backend registry; the gate configuration
  (THE_KNEE §3.3, §3.6, §3.7).
- **Non-goals:** no domain code.

## 2. Dependencies and consumers

**Produced:**
- **The package skeleton** `src/knee/`, in four areas: `knee/core` (schemas, vocabularies, pure operations),
  `knee/run` (runtime readers and bodies), `knee/build` (offline artifact builders) and `knee/orchestrate`
  (runners). Plus `knee/verify` (the SAME harness and test support), never imported by `run`.
- **`pyproject.toml`** for `knee`:
  - runtime dependencies per K01;
  - dependency groups, following the house toolkit (SquishOS `docs/home/TOOLKIT.md`, "one owner per role";
    the global `code-verification.md` → *The toolkit*):
    - `dev`: pytest, hypothesis, pinned ruff, import-linter, deptry, crosshair-tool, pyperf, and icontract
      (optional);
    - `tools`: the investigators py-spy, memray, viztracer and scalene, plus IPython;
    - `accel`: numba;
  - **Tools the toolkit does not list are vetted here before adoption,** each against "one owner per role". Three
    are proposed:
    - apache-hamilton, to draw the run's graph dev-side;
    - beartype and jaxtyping, for runtime array shape and dtype contracts.

    pyinstrument is dropped, because it duplicates the investigators' role. Radon is never added: the toolkit
    skips it, since "Detective's parsimony lenses and LintGate cover complexity".
  - a separately pinned **DEPLOY** requirements file built from K01's Kaggle versions.
- **The VERIFY environment:** a uv-managed CPython of Kaggle's minor version if that is ≥ 3.12, else 3.12, with
  `.python-version`. It replaces the conda-based `.venv`.
- **`justfile`**, with these verbs:
  - `gate`;
  - `detective <args>`: the local-pair wrapper. It runs
    `PYTHONPATH=$HOME/tools/Detective:$HOME/tools/Wesker <VERIFY python> -m Detective.cli <args>`, records both
    checkouts' revisions, tees complete stdout and stderr to `.detective/runs/<stamp>-<verb>.log`, preserves the
    exit status, and appends nothing the verb's grammar does not take;
  - `accept <K>`: runs the chapter's acceptance manifest `acceptance/<K>.toml`, reports pass, fail or recorded
    per kind, and computes staleness recursively over the book's table (a stale dependency makes its consumers
    stale). It replays the versions `SELECTION.toml` selects, and skips an unselected optional chapter
    explicitly;
  - `book-check` (manifest plus links);
  - `deploy-check` (production imports and smoke in DEPLOY);
  - `trace`, `bench`, and `same <kernel>`.
- **Configuration:**
  - ruff, pinned, with `tests/detective` excluded from lint and format and `docs/canon` from format;
  - Import Linter contracts: layers by area; `knee` never imports `RSNA_Knee`; nothing on the kernel path
    imports `knee.orchestrate.teach`, `knee.orchestrate.text` or the harness;
  - deptry, with `package_module_name_map`;
  - pytest: markers `detective` and `realdata`; `filterwarnings=error`; `xfail_strict`.
- **`knee.core.accel`, the backend registry:**
  - backends `reference` and `jit`;
  - configuration before any kernel binds;
  - a pure decision `backend_disposition(requested, numba_available, required) -> code`;
  - the requested and effective backend stamped in provenance;
  - a declared warm-up.
- **`knee.verify.same`, the SAME harness** (THESIS §12.5: "A speed-up changes how an answer is computed, never
  the answer"):
  - runs a kernel's reference and twin over Hypothesis-generated inputs and recorded frames;
  - compares by the kernel's contract:
    - codes, assignments, decisions and whole-number results exactly;
    - floats within the declared tolerance, on intermediate values only;
    - declared nonfinite values by position;
  - routes threshold-boundary cases to the reference;
  - holds within one environment, never across two;
  - writes a SAME record that names its evidence scope.
- **The behaviour-change record** (THESIS §12.6, "each drop names its cause"). A chapter that changes decisions
  on purpose records the prior and new reference digests and its intent. Its first-light run is read as a diff
  against the prior first-light record, never as SAME.
- **`knee.core.events`:** local structured JSONL events carrying finding IDs.
- **`knee.core.store`:** content-addressed keys, manifests, atomic publish, interrupted-write detection; key
  derivation as a pure decision.
- **`MIGRATION.md` enforcement:** the Import Linter contract, plus a test asserting every legacy unit has a row.

**Consumers:** all later chapters.

## 3. Mechanism

- **The gate** runs in this order: ruff check, ruff format --check, pytest (legacy and `knee`, generated suites
  collected), lint-imports, deptry; ty is advisory. It stops at the first failure and prints which step failed.
  `cargo fmt --check`, `clippy -D warnings` and `test` are added once `native/` exists.
- **`just accept <K>`** runs the chapter's acceptance manifest. Engineering kinds pass or fail. Domain readings
  are recorded against their pre-written expectations and never gate (`CONSTRAINT_BLOCK.md` law 12). Staleness
  is computed recursively over the table.

## 4. Contracts

- **SAME record:** `{kernel, reference_digest, twin_digest, backend, environment, inputs: {generated_n, frames:
  [ids]}, exact_fields_equal, float_fields_max_ulp, nonfinite_positions_equal, boundary_routed_n, verdict:
  same|different|invalid_measurement}`. An undeclared nonfinite value is `invalid_measurement`; a declared one
  compares by position.
- **Behaviour-change record:** `{chapter, kernel, prior_reference_digest, new_reference_digest, intent,
  firstlight_diff}`.
- **Acceptance manifest** (`acceptance/<K>.toml`): commands; fixtures with digests; expected answers and
  abstentions; engineering checks; domain readings, each with its expectation and its class breakdown.
- **Events:** `{run_id, stage, finding_id?, code, at}`, with no competition-derived payloads.
- **Store keys:** a digest over (input digests, parameters, versions, code digest, environment and node, seed).

## 5. Implementation choice

- **Python and `just`.**
- **The backend registry is built fresh.** Cell-tracking's `accel.py` was the starting point, and its defects are
  avoided: the mode bound at decoration time, the compiled flag set early, the silent fallback, and the
  error-model differences left unmentioned.
- **Prior art:** cell-tracking's `pyproject` tools extra is the template for the `tools` group, adapted.

## 6. Verification

- **Intent tests** for the wrapper: it logs complete output, preserves the exit code, never truncates.
- **Backend registry:** every refusal path is tested, and `backend_disposition` is converged.
- **SAME harness self-test:**
  - a toy kernel with a deliberately divergent twin must read `different`;
  - a faithful twin must read `same`;
  - a twin producing an undeclared NaN must read `invalid_measurement`;
  - a declared nonfinite output, at the same positions, must read `same`.
- **The wrapper re-runs K01's Detective probe** (K01 ran the module form directly, before this wrapper existed).
- **`just accept`'s staleness:** a stale fixture dependency makes its consumers stale, recursively.
- **The Import Linter contracts must bite:** a seeded violating import in a test fixture fails lint-imports.
- **Store:** Hypothesis stateful tests for atomic publish and interrupted writes.

## 7. Integration

`just gate` is the pre-commit gate from here on. Every chapter's acceptance runs through `just accept`.

## 8. Acceptance

- **Behavioural correctness:**
  - `just gate` is green. That includes the pre-existing ruff findings, resolved by configuration (generated
    suites excluded) or a fix (legacy `tools/build_atlas.py` FURB192);
  - `just detective regime` is clean, or its printed repair has been applied;
  - all the self-tests above pass;
  - `knee.core.accel.backend_disposition` stands `pinned`.
- **Representation fidelity:** the DEPLOY requirements equal K01's measured Kaggle versions.
- **Domain validity:** not applicable.
- **Performance evidence:** the gate's wall time is recorded, informational only.
- **Evidence scope:** this revision, VERIFY and DEPLOY as pinned.
- **Invalidation:** a change to the toolchain, the pinned ruff, the Detective or Wesker revision, or K01's
  runtime record.

## 9. Open matters

- **Fact:** whether DEPLOY can be reproduced locally with uv for Kaggle's exact Python patch version. If not, the
  nearest available minor, with the gap named.

## 10. Provenance and status log

- **Sources:**
  - THE_KNEE §3;
  - the global `code-verification.md` (*The toolkit*), `verification-gates.md` and `repo-hygiene.md`;
  - SquishOS `docs/home/TOOLKIT.md`;
  - Detective `ARCHITECTURE.md` §11.
- **2026-10-02:** specified in K00.
- **2026-10-02, revision 1** (`provenance/build/revision_1.md`):
  - acceptance manifests and recursive staleness (F10, F11, F56);
  - SAME by contract, with declared nonfinite values and one environment (F32; THESIS §12.5);
  - the behaviour-change record (F11; THESIS §12.6);
  - the wrapper re-runs K01's probe (F29).
