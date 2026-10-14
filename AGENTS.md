# For agents (and humans) arriving fresh — read before proposing anything

**Read the thesis first.** Everything in RSNA_Knee serves one thesis: `docs/THEORY_OF_THE_CASE.md`, Part I.
Read it before anything else, and do not overcomplicate it. Rohan, 2026-10-13: «This is basically the whole
thing. That's it.»

**The archives are invisible.** `archive/` and `archive2/` hold the old builds. Do not read, lint or check them
unless Rohan says to look in them. Rohan, 2026-10-13: «Ignore lint and other checks on the archive folders.
They're invisible unless I tell you to look in them».

**RSNA_Knee is a classical-AI project. It is not ML.** It may look like it
is "missing the model." It is not — that is the thesis. Before proposing ANY architecture,
approach, or "improvement":

1. Read `docs/THEORY_OF_THE_CASE.md` (this folder) — the design and why classical AI wins
   here. If it is still a stub, ask the founder to fill it (or fill it WITH them) before
   proposing architecture.
2. **Restate the mechanism in your own words** and have the founder confirm it. A
   correct-sounding paraphrase is not the test; the data-flow is.
3. Never reframe the symbolic / deterministic / vector-symbolic / data-geometry /
   story-understanding design as ML. Never propose a model, CNN, transformer, ensemble, or
   classifier as the default. Iterate the *encoder / data geometry / signal*, never model
   capacity.

**Four different things, never collapsed:**
- **AI** — the genus (reasoning, representation, symbolic and vector-symbolic computation).
- **ML** — one narrow, **avoidable** species (gradient-fit models).
- **Classical AI** — symbolic / vector-symbolic / deterministic. Usually the architecture here.
- **Story-understanding intelligence** — Regenesis (the founder's Python port of Winston's
  Genesis; in the MCP list as `mcp__Regenesis__*`). A distinct thing again.

**Know your own bias (this is why the gate exists).** You — and LLMs generally — are
disproportionately drawn to ML and reflexively skeptical of classical AI. It feels like
domain knowledge; it is a prior overriding what the founder specified. The tells: "this
is really ML, just small/downstream"; "you'll need a model for the hard part"; "the
deterministic part is elegant but it caps out"; using "no algorithm beats its data" to
smuggle a model back in.

**The one escape hatch:** the founder may deliberately place a small, bounded model at some
tail of a pipeline (a registration/normalization utility; a <1% candidate-selection
residual). That is the founder's explicit call — never your default, never "the
architecture," never the win path. When they ask, comply; never volunteer it.

Canonical, fully-worked example of this apparatus:
`~/Projects/Kaggle_Killer/competitions/RSNA_Knee/`. Global law: `~/.claude/CLAUDE.md`
("AI IS NOT ML").
