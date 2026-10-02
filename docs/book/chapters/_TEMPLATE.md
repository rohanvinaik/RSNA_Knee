# Kxx — <name>

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-Kxx'`; staleness by `just accept Kxx` |
| **Depends on** | <chapters, and the artifacts or contracts consumed from each> |
| **Consumed by** | <chapters, and the values each consumes> |
| **Commit label / tag** | `knee/Kxx` · `knee-Kxx` |

## 1. Purpose and authority

- **The founder's requirement it serves,** quoted with date (`FOUNDING_PROMPTS.md`, `FOUNDING_RECORD.md`).
- **The accord clause or canon passage it implements or amends** (`THE_KNEE.md` §2).
- **Explicit non-goals.**

## 2. Dependencies and consumers

- **Produced values:** each named for what it is, as a function returns it.
- **Actual consumers:** each named, chapter and function.
- **Bootstrap requirements**, if this chapter needs an artifact that a later chapter refines.
- **Forbidden imports:** the Import Linter contracts this chapter adds or must keep.

## 3. Mechanism

- **Data flow:** inputs → operations → outputs, at the level of what is computed numerically.
- **Equations and relations,** with units and frames.
- **Named outcomes:** every code a decision returns, and the unresolved cases (abstentions, refusals) kept
  apart from the negatives.

## 4. Contracts

Each value it hands on carries its schema: shape, dtype, endianness, axis order, units, coordinate frame,
transform direction, missing-value status fields (never NaN as unknown), ownership and mutation rules, the
numerical semantics (declared limits, proved integer widths, the float policy), and the serialization and
manifest fields.

## 5. Implementation choice

- **Language and compute,** and the measurement that chose it (AGENTS.md, Project override 3).
- **Prior art and reuse:** what exists, and whether it is reused, rewritten or retired. Each reuse carries its
  argument (Law 5) and a migration-ledger row.
- **Memory and access layout:** scratch bytes, bytes scanned, block rationale.
- **Concurrency:** process × thread ownership, and nested library threads.
- **Cache lifecycle:** keys and invalidation; immutable artifacts kept apart from writable caches.

## 6. Verification

- **The intent corpus:** hand-written tests stating the intended behaviour, authored before the
  characterization is read.
- **Detective scope and standing:** the functions, their pinning route (synthesized literal or bounded-array
  inputs, or captured real arguments) and their current-digest standing.
- **Properties:** the Hypothesis laws, stateful tests where the chapter has a store or cache, and CrossHair
  where its contracts are supported.
- **SAME obligations** for each accelerated twin: what must match exactly, and how boundary cases are routed.
- **The unverified residual,** named.

## 7. Integration

- **The real entry command** (a `just` verb or a module entry point).
- **Artifact inputs,** with their digests.
- **Output schema,** and where its consumer reads it.
- **The end-to-end check** through the real command.

## 8. Acceptance

Executable commands, with fixture IDs and digests. Expected answers **and expected abstentions**.
Malformed, empty and boundary cases. Dependency enforcement. Execution in the DEPLOY environment where the
kernel imports this chapter. The location of the evidence.

Reported in four kinds. None substitutes for another:
- **behavioural correctness;**
- **representation fidelity;**
- **domain validity;**
- **performance evidence** (each budget names its scope).

## 9. Open matters

- **Facts:** each with the measurement that settles it, and where its result is recorded.
- **Policy or meaning:** each a question for the founder, stated with the measurements beside it.

## 10. Provenance and status log

- **Sources:** with `REFERENCE_MANIFEST.toml` ids.
- **Deductions** behind each decision taken here.
- **Status log:** dated notes. Acceptance at revision `<sha>`, tag `knee-Kxx`, Codex review in `provenance/`.
