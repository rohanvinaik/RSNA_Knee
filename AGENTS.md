# For agents (and humans) arriving fresh — read before proposing anything

**Listen.** Rohan's words are the specification: do exactly what he asks and no more, restate only what he
said, ask where there is a gap, answer the question he asked first, and trust the thesis («You just don't
fucking TRUST me»). What you broke, you fix. Every correction he had to make, and what would have prevented
it, is in `docs/HOW_TO_BUILD.md`.

**Read the thesis first.** Everything in RSNA_Knee serves one thesis: `docs/THEORY_OF_THE_CASE.md`, Part I.
Read it before anything else, and do not overcomplicate it. Rohan, 2026-10-13: «This is basically the whole
thing. That's it.» At every session start and after every compaction, before anything else, read whole
`docs/conversations/2026-10-13-the-thesis.md`, then `docs/THEORY_OF_THE_CASE.md`, then
`docs/OBJECTS_AND_CONDITIONS.md`, then `docs/HOW_TO_BUILD.md`, then `docs/RESOLVING_THE_PARTS.md` (how each
part is resolved: the views, the lenses, the operations; and the provisional entries for the rest), and
look at the proof study's pictures with the conversation in mind: the parts of the knee the lenses
already pull out.

**How the knee's objects are named.** Rohan, 2026-10-14: «Reasoning off the actual pngs, basic
common-sense domain knowledge, the work I ALREADY did and proved, and basic identification and
assignment of object identity.» And: «I TOLD you to use common-sense reasoning off images.» For each
object in `docs/OBJECTS_AND_CONDITIONS.md`, one at a time:
1. Find its main slice in each series: the one that shows the region the object is identified in, and
   later diagnosed in («Is it not obvious which slice to use?»). The squint
   (`src/knee/collapse/squint_stack.py`) shows every slice of a series cheaply, so finding it is plain.
   Never recompute on every slice («that's completely wrong»; the collapse,
   `../cell_tracking/docs/pipeline_thesis/paper/what_an_object_is.md` §4). The run still reads each
   series' middle slice for most parts, the code's choice and not the thesis's; Rohan, 2026-10-15: «I
   think that you missed the point of this part of the thesis» (`docs/RESOLVING_THE_PARTS.md` §8).
2. Look at the actual pictures of that slice, and say plainly, with common-sense domain knowledge, why the
   object looks like itself there.
3. Write exactly that as a few plain rules on the lenses the interiors already give
   (`src/knee/objects/assignments.py`).
4. Run `scripts/run_interiors.py` on the proof study, look at the picture, and show Rohan before the next
   object.

The loop that works, step by step, what to do straight after a compaction, and where the parts stand:
`docs/HOW_TO_BUILD.md` §2, §7 and "Where it stands".

A part plainly visible in one lens is found by that lens, whichever lens it is: «If it's visible in one lens
but not the other (like "joint fluid")...then great, we know how to find it, problem solved». Seeing a part
and not yet resolving it is the agent's failure, never the project's. No part is found by one lens alone:
«It's not SUPPOSED to be isolateed by ANYTHING alone». A part defined by what it lies between is in the
pictures wherever its neighbours are: «It's literally a form of interstitial fluid. Interstitial. Between
the tibia and femur. We have the tibia, we have the femur. It's...obviously in there?» Where the pictures
do not hold the object at all, it is not named.

The test is validity, not perfection. Rohan, 2026-10-14: «It's not about perfection. It's about validity.»
Each part is resolved at least once, from the lenses, by a rule that is not tuned to that view; then it is
done («If you can resolve objects in one view, then you can do it acceptably as a general process, even if a
few images are a bit weird. Those edge cases are the ENTIRE space of where AI comes in»). "Never wrong" is
said of the lenses, not of the names: «"never wrong" simply refers to the thing doing the measurment. A
thermometer is not wrong. Your inference ... might be». A name a rule gets wrong on some other image is not
a reason to withdraw it.

**One coherent operation.** Rohan, 2026-10-14: «This was supposed to be efficient. JIT and paralell compute,
cheap measures, analyses shared in a single coherent operation.» The run is one graph of named values, each
computed once and handed to every consumer; nothing is computed and thrown away, or computed twice. The
ledger, vulture and the gate stay on, and the pipeline is checked through its real entry point
(`scripts/run_interiors.py`). Details: `docs/HOW_TO_BUILD.md` §5.

Do not:
- build rule machinery;
- chase unseen studies with a new rule per image («even if a few images are a bit weird»);
- change the proof pipeline's lenses unless he asks;
- report in jargon;
- hand Rohan the choice of a remedy for something you broke («YOU'RE the one who fucked it up»);
  fix it;
- let an advisor's or a side agent's advice override his thesis or his words.

Every correction Rohan had to make, with his words and what would have prevented it, is in
`docs/HOW_TO_BUILD.md`, for every agent.

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
