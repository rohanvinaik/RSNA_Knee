# K02a — The typist *(optional)*

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K02a'`; selected only when `SELECTION.toml` records it |
| **Depends on** | K02: the SAME harness, `just detective`, the store and events. **External:** the SquishOS harness's executable-witness slot (DESIGN_LEDGER H10, proposed in `provenance/build/typist_squishos_proposal.md`; built at its source, never here) |
| **Consumed by** | any later chapter, for the units its §5 marks *typist-eligible*: twins of pinned references, and pure decisions with a finite named-code return |
| **Commit label / tag** | `knee/K02a` · `knee-K02a` |

## 1. Purpose and authority

To let a small local model do the literal typing of eligible bodies, under a harness it does not drive. Nothing it
types is admitted without a machine-checkable certificate and the lead's read. The lead keeps everything that is
judgment: the design, the decomposition, the contracts, the intent and the professional finish.

- **The founder** (2026-10-02, `FOUNDING_PROMPTS.md`):
  - 16:08:14Z: "starting up a small local model--"Uroboros" project-style--with a contract/intent tests and a
    specific, gated scope of operation and constrained output to do the mechanical work/code … Qwen (with an
    Uroboros-style harness) types only that which is explicitly authorized by you and detective, mandated by
    contract and constrained output";
  - 16:19:48Z: "Agree with your "uroboros" claims/ideas, worth working them un";
  - 16:29:22Z: "make sure the new design sent to codex includes the typist additions".
- **It is a build tool, not the architecture.**
  - It types code. The code's behaviour is fixed by specifications and certified by checks.
  - The architecture still holds no learned component (`AGENTS.md` law 1).
  - The founder placed this tool himself, and only he places a model.
- **The seat comes from the content.** THE_DYAD Law 1: "Classify before you seat".
  - Remove-the-warrant test (THE_DYAD II.3): a body's authority comes from its specification, its reference and
    its tests, all outside the model. So the content is *correctness-shaped*.
  - The seat is therefore the typed hole, inside a loop the model does not drive (THE_DYAD Law 2: "Agency is the
    bug").
  - It is never the collaborator seat, where a formalized prompt drifts (THE_DYAD Law 7).
- **The reference implementation is Uroboros** (CONSTRAINED_OUTPUT_AND_REASONING, preamble). Its laws carry over
  unchanged: the model never drives; one unit at a time; proven or nothing; verify with the receipt.
- **The departure, stated.**
  - Uroboros's model selects *values*, and "the harness writes the call syntax".
  - Here the model writes a *body*, which is executable syntax.
  - CONSTRAINED_OUTPUT E2 knows two slot kinds: grounded selection and open typed witness. O8 says "The harness
    writes every piece of executable syntax".
  - So this chapter needs a **third slot kind, the executable witness**. Its injection closure is a grammar, an
    allowlist and a sandbox, where E2's closure is a literal-only interpreter.
  - That slot is a SquishOS theory amendment (founder agreement, 16:19:48Z). It is proposed with its text in
    `provenance/build/typist_squishos_proposal.md`, read by Codex with this book, and written into SquishOS only
    after accord.
- **Non-goals.** The typist never types any of the following:
  - decomposition, names, signatures, types or contracts;
  - intent tests, properties, expectations or bars (the teaching set is the human's by theorem: CONSTRAINED E10);
  - references for numeric kernels, whose output is open (E5: no finite regime certifies it);
  - impure code: I/O, DICOM, files, the kernel's packaging, orchestration;
  - anything in K03 (the judge);
  - Rust or C, until a separate qualification.

  It never chooses what to type next.

## 2. Dependencies and consumers

**Produced** (`tools/typist/`, dev-only; never on the kernel path, enforced by Import Linter):
- `unit_spec`: the lead's specification of one unit. It holds:
  - the signature with types;
  - the docstring contract (domain, the named-code vocabulary, invariants);
  - the identifier vocabulary;
  - for a twin, the reference's source and its contract;
  - for a decision body, the *shown* intent cases (never the held-out ones).
- `type_unit(spec) -> TypistOutcome` (the inverted-control loop, as Uroboros's `process_function`), returning
  one of these codes:
  - `certified`, with its certificate;
  - `needs_author` (no certificate within the pass budget);
  - `unauthorized_behaviour` (a surviving mutant of the body's own; the lead authorizes with an intent case, or
    rejects);
  - `contract_breach` (output outside the grammar on the decode-time rung);
  - `failed` (transport, budget, sandbox).
- `admission(body_text, allowlist) -> admitted | refused:<cause>`: a pure decision, pinned.
- `next_move(outcome_so_far, evidence) -> retry | hand_back:<kind> | stop`: a pure decision, pinned. A retry is
  legal only with new evidence.
- **The certificate:** `{unit_id, body_digest, spec_digest, test_set_digest, discharge, evidence:
  {same_record | mutation_report}, model, engine, grammar_version, passes}`. It is bound by content address to
  what it certifies (CONSTRAINED O20).
- **The qualification record** (CONSTRAINED M3).

**Consumers:** later chapters' eligible units, through `just type <chapter> <unit>`.

## 3. Mechanism

1. **The lead writes the unit spec first,** with the tests that will judge it.
   - A twin's judge is its pinned reference.
   - A decision body's judge is an intent suite with *held-out* cases the model never sees, plus properties.
2. **One bounded call.**
   - The harness builds the prompt: the spec, the shown cases, the vocabulary and an explicit answer block.
   - Thinking is off (`think = false`), and there is no free-text rationale. THE_DYAD Law 13: nothing fluent is
     addressed to the confirmer, and the confirmer here is the lead.
   - The model returns only the body. The harness writes everything else: the `def` line, the docstring, the
     decorators (`@njit` for a twin) and the imports.
3. **The constraint ladder** (CONSTRAINED O5), named per engine:
   - **Rung 1, decode-time grammar.** On llama-server, a GBNF grammar over an allowlisted Python subset whose
     identifiers come only from the sourced vocabulary.
     - The subset admits: assignments; `if/elif/else`; `for` over `range`, `enumerate` and `zip`; `return`; the
       allowlisted calls (a Numba-supported NumPy subset for twins); string literals only from the named-code
       vocabulary.
     - It excludes: `import`, `def`, `class`, `lambda`, `while`, `try`, `with`, `global`, attribute access
       beyond the allowlist, and every dunder.
     - Output outside the grammar has probability zero.
   - **Rung 2, admission only.** On an engine that takes only a JSON schema (Ollama), the body is a length-capped
     string slot, and the grammar is enforced at admission. The rung is recorded on every call.
4. **Admission** (deterministic, defense in depth): an `ast` parse against the allowlist, then ruff, then ty.
   - On rung 1, a violation is a contract breach. It stops loudly and is never retried.
   - On rung 2, a violation refuses that pass.
5. **Evaluation only in a sandbox:** a subprocess with no network, its own temporary directory, and CPU, memory
   and time walls.
6. **The discharge,** by unit class (THE_DYAD Law 13; CONSTRAINED O12):
   - **A twin** (`discharge = check`). It must pass SAME against its pinned reference (K02's harness: generated,
     recorded and boundary cases, by contract), and the reference's Detective suite must be green against it.
     "Cheap slop is acceptable input to a gate that cannot be argued with" (THE_DYAD II.11).
   - **A decision body** (`discharge = downstream`, then `operator`):
     - (i) the intent suite, held-out cases included, is green;
     - (ii) the intent suite alone kills every killable mutant of the body (`just detective diagnose` with only
       the intent suite). A survivor is behaviour nobody authorized, and it hands back
       `unauthorized_behaviour`;
     - (iii) the properties are green;
     - (iv) `just detective converge` completes the pin;
     - (v) the lead reads the body before it is committed.
   - The scope is stated with the certificate (CONSTRAINED E4). A mutation-complete intent suite certifies what
     its oracle separates, and nothing wider. A body that hard-codes the shown cases can pass (ii); that is why
     the held-out cases and properties exist.
7. **The guards** (Uroboros law 4; CONSTRAINED D5):
   - a per-call wall;
   - a pass budget of three;
   - a stop on no progress.
   - A retry carries *new* evidence: the failing case's name, the SAME diff's location, or the surviving mutant's
     line, as Uroboros's focus block names the one condition to drive. A pass is never retried on unchanged
     evidence (O11).
8. **The hand-back is typed** (CONSTRAINED O11):
   - `needs_author`: the lead types the unit;
   - `unauthorized_behaviour`: the lead decides, and authorizing means writing the intent case that pins the
     behaviour.
   - An abstention is a result. It is never retried into an answer.
9. **Professionalization.** After certification the lead may refactor for SICP clarity, under the now-pinned
   suite: behaviour preserved, green as the proof.

## 4. Contracts

- **The unit spec, the outcome codes and the certificate,** as in §2.
- **The grammar** is a versioned SquishOS cassette artifact. It is data, never code ("a cartridge cannot smuggle
  logic past the gate", THE_DYAD Part III).
- **Raw records.** Every call is recorded raw: the prompt digest, the grammar version, the model, the engine and
  its version, the decode options, the output, the admission result and the certificate (CONSTRAINED O9).
- **No competition data in a prompt.** The model sees source code and specifications only. SAME and the intent
  suites run on synthetic and phantom inputs. A captured argument derived from competition data never enters a
  prompt.

## 5. Implementation choice

- **The knee-side caller** (`tools/typist/`, Python) discharges the warrant. It reuses `knee.verify.same` and
  `just detective`. Its pure decisions are pinned.
- **The model call goes through `squishos-harness`.** "Local models are reached only through a harness" (global
  rules). The cassettes are `typist-twin` and `typist-body`, with the new slot kind (H10).
- **The engine, measured 2026-10-02:**
  - llama-server (Homebrew build 10809) serves `qwen3-4b-instruct-2507-q4_K_M` on `:8080`, so rung 1 is
    available for it today;
  - `qwen3.5:4b` runs on Ollama 0.32.5, at rung 2 only. llama.cpp b10180 could not load it (SquishOS spine 09,
    2026-09-11), and whether build 10809 does is measured here (CONSTRAINED O19: wire facts are measured per
    engine and dated);
  - the bake-off qualified `qwen3:4b-instruct` for *selecting test inputs*, a different task. Nothing has been
    measured for typing bodies.
- **Prior art.** The patterns of Uroboros (`synth.py`'s typed skeleton, `cycle.py`'s guards, `nextstep.py`'s
  typed next step) and of the SquishOS harness hardware (the gate, the loop, admission, records) are reused,
  their code is not (Law 5).

## 6. Verification

- **Intent tests, one per law:**
  - no unit is admitted without its certificate;
  - no retry happens on unchanged evidence;
  - a survivor is never pinned automatically;
  - on rung 1 an off-grammar body is a contract breach, never a retry;
  - the harness, never the model, writes the `def` line and the imports.

  The loop is driven by a fake model, so no model is needed.
- **Detective** converges `admission` and `next_move`, and **CrossHair** looks for counterexamples to their
  contracts. Finding nothing is not a proof (the house toolkit: a pure decision gets a Detective pin plus
  CrossHair).
- **Grammar fuzzing:** everything the grammar generates, the AST allowlist admits.
- **SAME** for twins comes from K02. The mutation report for decision bodies is a Detective run, read whole.

## 7. Integration

`just type <chapter> <unit>` writes the certified body into the working tree with its certificate. The lead
reads it and commits it under the chapter's label. Nothing reaches DEPLOY through `tools/typist`.

## 8. Acceptance

Written first: `acceptance/K02a.toml`.
- **Behavioural correctness:** the laws hold (intent tests), and `admission` and `next_move` stand pinned.
- **Representation fidelity:** every certificate is bound to its body and test set, and every call is recorded
  raw.
- **Domain validity (discovery):** the qualification run (CONSTRAINED M1–M3).
  - **The fixture:** knee-shaped units on a measured complexity gradient, twins and decision bodies. The
    gradient is read by Radon (cyclomatic, as the bake-off measured it: CONSTRAINED M1, "measured with radon, not
    eyeballed") and by Detective's parsimony lenses, two independent channels,
    with planted traps:
    - a decision whose held-out case contradicts the plausible reading;
    - a twin with a boundary case;
    - a spec that touches I/O, which must be refused before any call.
  - **Per model, engine and unit class:** certified, handed back, and *wrong-but-admitted*.
  - **Wrong-but-admitted must be zero.** Any instance is a structural bug in the gate, fixed in the gate (E3).
    It is the one domain reading that blocks the typist's *selection*.
  - Other misses open problems, as R1 says.
- **Performance evidence:**
  - certified units per 1,000 output tokens;
  - the lead's tokens saved per certified unit;
  - passes and mutants run per unit.

  All of these are counted.
- **Selection:** the founder selects the typist in `SELECTION.toml`, with the qualification table beside his word.
- **Evidence scope:** the models, the engines and their versions, the grammar version, the fixture version.
- **Invalidation:** a change of model, engine, grammar or harness.

## 9. Open matters

- **Facts:**
  - which model qualifies, and on which rung;
  - whether llama.cpp build 10809 loads `qwen3.5:4b`;
  - the certified rate per unit class.
- **Policy (founder):**
  - selecting the typist after qualification;
  - the SquishOS theory amendment, the third slot kind, after Codex's read.

## 10. Provenance and status log

- **Sources (manifest ids):**
  - `squishos-the-dyad`;
  - `squishos-constrained-output`;
  - `squishos-harness-spine`;
  - `squishos-cassettes`;
  - `uroboros-readme`, `uroboros-architecture` and `uroboros-law`;
  - `detective-architecture` (§11).
- **Deductions:** the seat from Law 1; the slot from E2 and O8, extended; the discharge from Law 13 and O12; the
  guards from D5 and O11; qualification from M1–M3.
- **2026-10-02:** specified in revision 1 (`provenance/build/revision_1.md`, R3), at the founder's request.
