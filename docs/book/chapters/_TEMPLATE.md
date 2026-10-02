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
- **Typist eligibility** (K02a): which units are twins of pinned references, and which are pure decisions with a
  finite named-code return. Only these may be typed by the typist, and only with a certificate.
- **Concurrency:** process × thread ownership, and nested library threads.
- **Cache lifecycle:** keys and invalidation; immutable artifacts kept apart from writable caches.

## 6. Verification

- **The intent corpus:** hand-written tests stating the intended behaviour, authored before the
  characterization is read.
- **Detective scope and standing:** the functions, their pinning route (synthesized literal or bounded-array
  inputs, or captured real arguments) and their current-digest standing.
  - A function that cannot be pinned is guarded by ordinary unit tests, and says so (Detective
    ARCHITECTURE §11).
  - A branch that synthesis cannot reach is answered by extracting its pure decision, which preserves behaviour.
    The design is never bent to suit the tool.
- **Properties:** the Hypothesis laws, stateful tests where the chapter has a store or cache, and CrossHair
  where its contracts are supported.
- **SAME obligations** for each accelerated twin, by contract (THESIS §12.5):
  - codes and whole-number results match exactly;
  - floats match within the declared tolerance, with boundary cases routed to the reference;
  - declared nonfinite values match by position;
  - one environment at a time, never across two.
- **The unverified residual,** named.

## 7. Integration

- **The real entry command** (a `just` verb or a module entry point).
- **Artifact inputs,** with their digests.
- **Output schema,** and where its consumer reads it.
- **The end-to-end check** through the real command.

## 8. Acceptance

**Written first.** The chapter's first act writes its acceptance manifest (`acceptance/Kxx.toml`), before
anything is built. It holds:
- the executable commands, with fixture IDs and digests;
- the expected answers **and expected abstentions**;
- the malformed, empty and boundary cases;
- dependency enforcement;
- execution in the DEPLOY environment where the kernel imports this chapter;
- for every domain reading, its expectation, written before the run (ARCH §6.2.5 rule 5).

Reported in four kinds. None substitutes for another:
- **behavioural correctness** (gates the tag);
- **representation fidelity** (gates the tag);
- **domain validity** (*discovery*: recorded and never gating). It is read per class as identified, abstained or
  wrong, with counts and bounds, against the expectation written before the run.
  - A miss "names a disease" (ARCH §6.6.3). It opens a problem in §9, and Law 5 says where to look.
  - It is never a reason to discard the design or route around it, and it is never retuned to meet the
    expectation (founder, 2026-10-02 16:29:22Z).
- **performance evidence** (gates only its own claims). It is work and bytes counted per unit, with seconds
  beside them as information (ARCH §3.2.6). Each budget names its scope.

The tag says the chapter is built, verified and measured. It never says its numbers are good.

## 9. Open matters

- **Facts:** each with the measurement that settles it, and where its result is recorded.
- **Policy or meaning:** each a question for the founder, stated with the measurements beside it.

## 10. Provenance and status log

- **Sources:** with `REFERENCE_MANIFEST.toml` ids.
- **Deductions** behind each decision taken here.
- **Status log:** dated notes. Acceptance at revision `<sha>`, tag `knee-Kxx`, Codex review in `provenance/`.
