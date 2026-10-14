# Detective returns UNGATEABLE for any kernel under a call-form decorator (measured 2026-10-12)

A defect report, in the protocol's words: an UNGATEABLE standing "measures the engine, not your
suite; it is a defect to report, not a gap to close". This is the report. Detective is the local
checkout at `~/tools/Detective`, so its maintainer is the founder.

## What was measured

A scoped Sonnet builder (the composition packet, task 7.4) reproduced the standing in a throwaway
project under this session's scratchpad (`det_scratch/`), never against repository code, with one
trivial pure function under ten decoration forms. The lead read the engine's own run logs for the
plain, the local call-form and the imported plain cases. The function under every form:

```python
def kernel(value: int) -> int:
    if value > 3:
        return value + 1
    return value
```

| decoration | mutants | Detective's final line |
|---|---|---|
| none | 12 | `✓ COMPLETE (operator universe) · 12/12 killed` |
| plain form, defined locally (`@tagged`) | 12 | `✓ COMPLETE` |
| plain form, imported from another module | 12 | `✓ COMPLETE` |
| plain form, setting an attribute on the function | 12 | `✓ COMPLETE` |
| call form, local, literal argument (`@tagged_with("x")`) | 14 | `⚠ UNGATEABLE — one or more mutants could not be BUILT` |
| call form, local, constant argument | 14 | `⚠ UNGATEABLE` |
| call form, imported, literal argument | 14 | `⚠ UNGATEABLE` |
| call form, imported, constant argument | 14 | `⚠ UNGATEABLE` |
| this project's `@contracted(CONTRACT)`, original | 14 | `⚠ UNGATEABLE` |
| this project's `@contracted(CONTRACT)`, with the registry (7.3) | 14 | `⚠ UNGATEABLE` |

From the call-form log, verbatim: `kernel: 14/14 mutants`, then `▸ 2 survivor(s) remain —
classifying`, then `⚠ unclassified 2 — the search could not run on them`, then the STOP. The plain
form's log: `12/12 mutants`, `12/12 killed`, `reproducibility confirmed`.

## What it says, and what is inference

Fact: with a call-form decorator the mutant universe grows by two and those two cannot be built;
the function body is identical in every row. Inference, the builder's and then the lead's, not
verified by reading the engine: the mutation operators reach the decorator expression, and a
mutant made there cannot be bound as a function. The registry added for task 7.3 changes nothing
either way.

Consequence for this project: every kernel carries `@contracted(CONTRACT)`, the one form settled
under task 0.3. The four UNGATEABLE standings on the record (`count_by_extent`,
`footprint_labels_reference`, `place_codes_reference`, `read_ownership`) were recorded as a wall
against array-shaped functions. They are not: `read_ownership` takes an object and
`place_codes_reference` an array, and both share the decorator. Earlier records that said "an
array-shaped function" (`docs/TOOLING.md`, the composition record, task 2.3's note) read the
refusal's cause into it; the protocol says not to theorise past a refusal, and this measurement is
what answers instead.

## What follows (task 7.11)

The one form becomes the plain decorator `@contracted`, which reads the module's one `CONTRACT`
declaration, so the kernel line is a bare name and the engine's operators have nothing to mutate
on it. One form still, as the founder ruled; only its spelling changes, for a measured reason.
Then the four kernels are converged again, and what they return is their real standing.
