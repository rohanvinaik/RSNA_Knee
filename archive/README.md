# RSNA Knee Abnormality Detection — `RSNA_Knee`

A classical-AI data-geometry entry for the RSNA Knee Abnormality Detection competition. **There is no machine
learning in the architecture.** Each study is registered into a platonic knee's frame, compared place by place
against normal knees, read by questionless lenses, and decided by a society of agencies that concur or abstain.

## Read in this order

1. **[`AGENTS.md`](AGENTS.md)**: the house rules for every agent. Read it before proposing anything; this project
   has a recorded ML-substitution failure mode.
2. **[`docs/book/`](docs/book/README.md)**: the build book. Start with its `CONSTRAINT_BLOCK.md` and
   `THE_KNEE.md`, then the chapter being built.
3. **[`docs/THEORY_OF_THE_CASE.md`](docs/THEORY_OF_THE_CASE.md)** and
   **[`docs/KNEE_ARCHITECTURE.md`](docs/KNEE_ARCHITECTURE.md)**: the design canon, as amended by
   `docs/book/THE_KNEE.md` §2.
4. **[`docs/FOUNDING_RECORD.md`](docs/FOUNDING_RECORD.md)** and
   **[`docs/book/FOUNDING_PROMPTS.md`](docs/book/FOUNDING_PROMPTS.md)**: the founder's words, verbatim.
5. **[`decisions/`](decisions/)**: the dated decision log.

## Status

Computed, never written here: run `git tag -l 'knee-*'`, and `just accept <chapter>` once K02 exists.
