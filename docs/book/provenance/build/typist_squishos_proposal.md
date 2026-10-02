# The typist's SquishOS extension: a proposal (2026-10-02)

**Status: PROPOSED, not written into SquishOS.** The founder agreed in principle (16:19:48Z: "Agree with your
"uroboros" claims/ideas, worth working them un"). SquishOS's own protocol has a second reader settle a theory
reading before it is written in (CONSTRAINED_OUTPUT_AND_REASONING Part VIII), so this text goes to Codex with the
revised book. It is written into SquishOS only after accord, at its source:
- `docs/theory/CONSTRAINED_OUTPUT_AND_REASONING.md`;
- `docs/DESIGN_LEDGER.md`;
- `src/squishos/harness/`;
- `cassettes/`.

The knee's consumer is chapter K02a.

## Why the theory, as written, does not admit the typist

- **E2 knows two slot kinds:**
  - a grounded-selection slot, "a closed enum over sourced candidates";
  - an open typed witness slot, which "locks arity and type and admits any literal of the type".

  Its injection argument: "the harness writes every piece of executable syntax and the interpreter accepts only
  a literal allowlist". **O8:** "The harness writes every piece of executable syntax and the interpreter accepts
  only literals".
- **The typist's output is a function body,** which is executable syntax. So the gate (`cassette_verdict`)
  rightly refuses a correctness cassette whose value is free text. The spine doc says the gate requires "≥1 typed
  value slot" and admits free text only as a `proposal`.
- **A proposal cannot carry it either.** A body to a specification is correctness-shaped (THE_DYAD II.3), and
  "A generative output is a proposal and never enters a correctness slot" (Law 8).

## The amendment, proposed

**E2, a third kind: the executable witness slot.**
- **What it holds.** Source text in a declared grammar: an allowlisted subset of one language, whose identifiers
  come only from a sourced vocabulary.
- **Where it is closed.**
  - Rung 1: at decode time, where the engine enforces a grammar.
  - Rung 2: at admission, where it does not. The rung is recorded.
- **How it runs.** The text is parsed against the allowlist before it is ever run. It is evaluated only in a
  sandbox: no network, its own directory, CPU, memory and time walls.
- **What it is worth.** Like every witness it carries no authority. "Deterministic verification warrants only the
  result it establishes", and "a witness that establishes nothing makes no progress and earns no certificate".
- **Its two discharges:**
  - **`check`:** SAME against a pinned reference, with that reference's mutation-complete suite green;
  - **`downstream`, then `operator`:** an intent suite, held-out cases included, that kills every killable
    mutant of the body, with properties green; then the lead reads the body.

**O8, amended.** "The harness writes every piece of executable syntax, except the body in an executable witness
slot. There, the grammar, the allowlist and the sandbox close what a literal-only interpreter closes for a value."

**O4 and the guide.** This adds nothing to "select, never generate" for values. A body is generated, so the
three guards carry the weight that selection carries for a value:
- the grammar;
- the allowlist;
- the discharge.

**THE_DYAD Law 13 holds unchanged.** An admitted body is well-formed, not warranted, and its discharge is
declared.

## DESIGN_LEDGER H10, proposed

| H10 | the executable witness slot |
|---|---|
| status | PROPOSED (2026-10-02), from RSNA_Knee K02a |
| hardware | `schema`: an executable slot kind (grammar file, allowlist file, length cap). `decisions.cassette_verdict`: refuse unless the discharge is `check` or `downstream` and a sandbox is declared. `run`: the sandboxed evaluation hook belongs to the *caller*, as every warrant's discharge does ("Any operation-specific computation … lives in the calling layer"). `decisions.admission`: the AST allowlist |
| cassettes | `typist-twin` (`discharge = check`), `typist-body` (`discharge = downstream`, then `operator`), each with a GBNF grammar and an allowlist as data |
| engines | rung 1 on llama-server (GBNF); rung 2 on Ollama (JSON schema with a length-capped string, the grammar enforced at admission) |
| measured by | the qualification run of K02a (CONSTRAINED M1–M3): per class, certified, handed back, and wrong-but-admitted, which must be zero |
| never | a free-text rationale beside the body (Law 13); a retry on unchanged evidence (O11); the model choosing the next unit (Law 2) |
