# K00 — The founding record

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K00'` |
| **Depends on** | — |
| **Consumed by** | every chapter (the book, the rules, the manifest) |
| **Commit label / tag** | `knee/K00` · `knee-K00` |

## 1. Purpose and authority

To persist the build so that no session can lose it.
- **The founder** (2026-10-02): "in the "SquishOS" project, a full build plan is persisted past a session by
  writing it out as a "book", with each severable module as a "chapter", with the full intent and context laid
  out cleanly and persistently. I'd like us to use that."
- **Also:** "write the key/useful rules … in a robust CLAUDE.md file in this project level", and "get Codex to
  read your "chapters" and grounding context".
- **Non-goals:** no production code; no data fetched.

## 2. Dependencies and consumers

- **Produced:**
  - `AGENTS.md` and `CLAUDE.md`;
  - `docs/book/`: README, CONSTRAINT_BLOCK, THE_KNEE, FOUNDING_PROMPTS, MIGRATION, REFERENCE_MANIFEST, the
    chapter specs and template, provenance;
  - the retirement of the template stubs and their contracts (`CONTEXT.md`, `.claude/CLAUDE.md`).
- **Consumers:** every later chapter and every session.

## 3. Mechanism

The house founding-record pattern (SquishOS `docs/home/` M00; Detective's DETERMINISTIC_SICP §0): a constraint
block that passes the Remove-X check, a founding design whose decisions carry their deductions, the operator's
words verbatim, and a checksummed source manifest.

## 4. Contracts

- **Each chapter spec follows `chapters/_TEMPLATE.md`**: ten fields, with acceptance in four kinds plus
  evidence scope and invalidation.
- **The manifest** is TOML in SquishOS's format, verified by SquishOS's checker. One owner: it is called, never
  copied.

## 5. Implementation choice

- Markdown and TOML only.
- The manifest checker is SquishOS's `scripts/check_reference_manifest.py`, invoked by path from this repository's
  root. Reusing it is the best approach: it is the house tool and its decision is pinned there.
- **Caveat** (read in its source, 2026-10-02): it resolves `path` relative to the working directory (with `~`
  expanded), but resolves `cited_by` against **SquishOS's** root. So this manifest omits `cited_by` and names
  each source's use in its `role` text.

## 6. Verification

- `python3 ~/Projects/SquishOS/scripts/check_reference_manifest.py docs/book/REFERENCE_MANIFEST.toml` verifies
  every source.
- A link check (every relative link in `docs/book/` resolves) is run as part of acceptance with a short stdlib
  script in the scratchpad. It becomes `just book-check` in K02.
- **The fresh-reader check.** A Codex thread with no memory of the design reads only this book and its grounding,
  reconstructs the build, and is asked whether it agrees.
  - Its transcript lives in `provenance/build/`.
  - Each disagreement gets a recorded disposition: fixed in the book, or carried as an open matter.

## 7. Integration

The repository's `README.md` and `AGENTS.md` route to the book. The LintGate rule file's "canonical module
structure" is the book's chapter table (`CLAUDE.md`).

## 8. Acceptance

- **Behavioural correctness:**
  - the manifest verifies;
  - every book link resolves;
  - the retired stubs have no remaining consumers (Serena references and an AST import scan, recorded in the
    retirement commit `358aa63`);
  - the legacy tests still pass (45).
- **Representation fidelity:**
  - `FOUNDING_PROMPTS.md` matches the transcript byte for byte;
  - `THE_KNEE.md` §2 cites every canon passage it amends;
  - **Remove-X:** `CONSTRAINT_BLOCK.md` alone names the next chapter (K01).
- **Domain validity:** the fresh-reader check reaches agreement, or each disagreement has a recorded
  disposition.
- **Performance evidence:** not applicable.
- **Evidence scope:** the book's files at the tagging revision.
- **Invalidation:**
  - a founder statement that contradicts the book;
  - a canon source whose digest changes;
  - a chapter added or re-ordered without updating README's table and the constraint block.

## 9. Open matters

- **Policy:**
  - Q4 (the open register's emission);
  - whether to extend the SquishOS filter hook at its source to cover `python -m Detective.cli` and
    `just detective`.

## 10. Provenance and status log

- **Sources:**
  - the review (`provenance/review/`);
  - the design (`provenance/build/`);
  - SquishOS `docs/home/` (the book format);
  - the house reference docs (`provenance/build/reading_claude.md` §1).
- **2026-10-02:**
  - the stubs were retired in `358aa63`;
  - the book was written in the commit labelled `knee/K00`.
