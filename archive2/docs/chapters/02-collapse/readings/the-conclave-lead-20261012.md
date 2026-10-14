# The lead's reading: the pipeline is a conclave, not a chain

Written 2026-10-12, **before** opening either second reader, per `docs/SPINE.md`'s working loop.
The founder's words of this date are the oracle of intent and are quoted verbatim in
`teachings.md`; this file is the lead's reading of them and is not warrant for anything.

## The correction that produced this reading

The lead reported that the digit lens was *blocked* because the noise law abstained upstream, and
proposed swapping its population source. The founder's correction:

> "You built this in series. As in, the thing that allows for resolution of objects is not a
> stateless resolution of image processing, but runs serially. We 'get the parsed image' 'after'
> some step or the other runs. We are 'waiting' for some step or another to respond before we allow
> anything to output. That's...not really the point. Truth being resolved through superposition
> means that information is *addative*. Just because one lens, one part of the pipeline isn't able
> to resolve sufficiently, doesn't mean the rest aren't able to say anything."

> "If you're having a conclave/meeting, you don't achieve quorum by reading down the attendance list
> alphabetically and throwing a tantrum when 'Abel Ackerman' is out sick again. One lens, one stage
> not providing sufficient information is...fine? Like, okay? One person being absent doesn't make
> the whole meeting collapse, quorum is a *population*-wide state."

> "It's 'stateless' in that at a single instant, you are measuring if the body being seated has
> sufficient coverage that calling the assembly a 'quorum' rather than 'two women who got lost on
> their way to the bathroom' is an accurate description. The point isn't to achieve a magical serial
> path that happens to work, it's to get all the signals to produce legible output from their path
> whenever we want the pipeline to run, and for us to assemble identity on the superposition of all
> these analyses at each pipeline run. THAT'S what I mean by a 'single, production pipeline'."

The lead's proposed fix was itself the serial error: it treated one member's silence as a fault to
be repaired by finding it a different upstream, rather than as a named absence the body absorbs.

## The reading

**A run is an instant, not a traversal.** At each pipeline run every lens reads whatever it can from
whatever it has, and returns either a reading or a named absence. Nothing waits. Identity is then
assembled over the *population* of readings present at that instant. "How far did the route get" is
not a question the design admits.

**Quorum is a state of the seated body, not a completed path.** The question a run answers is
whether the readings actually present are sufficient coverage to call this an assembly. That is a
property measured over members, and it is measured *after* they have all spoken.

**An absence is a member, not a failure.** `AGENTS.md` law 3 and the shared vocabulary in
`knee.absence` already say a missing reading is silence and never a negative. The conclave reading
adds the converse: a silence must also never be *contagious*.

## What this says the current build gets right

Verified in `knee.pipeline.run_study`, 2026-10-12: `read_lenses`, `read_ownership`, `read_relations`,
`read_pairings` and `read_findings` all run **unconditionally**, with no `if` guarding any of them,
and each returns a record or a named code from the one shared vocabulary. The module comment is
explicit that a guard would be "the route deciding, and the route decides nothing (§13.7)". At the
stage level the body is already seated correctly.

## What is still chain-shaped — five facts

1. **`reached`** is a single scalar high-water mark, computed by a cascade of `if any(...)`. It
   answers "how far did the traversal get". `docs/PIPELINE.md` already calls it coarse.
2. **`ROUTE`'s `built` / `partly` / `not_built`** is an ordered progress table over a path.
3. **`objects` is guarded** (`if analysis is not None`) where its peers are not, so one member is
   seated conditionally.
4. **Nothing convenes the body.** `vectors` — the bundles, where an `<object>`'s profile is assembled
   from its places' readings — is `not_built`, is not called by `run_study`, and `just places`
   reports it unreached. Every member speaks and no minute-book is kept.
5. **Absence is transitive inside the lens stage, and this is the sharpest one.** The digit lens has
   exactly one source for its edge pair, `regime.terciles`, which sits at the end of a chain:
   quiet population → `coil_code` → `dark_sigma` → `stabilizer` table → foreground cut → above-cut
   values → terciles. When the coil identity refuses, `dark` is NaN, the table is None, the cut is
   NaN, the above-cut population is empty and the terciles come back NaN — so the lens writes
   `no_edges` over the entire acquisition. Measured on one study: **3 of 5 acquisitions silent**.

   The silence itself is correct and correctly named. What the conclave reading rejects is that
   **one member's absence is caused by another member's absence.** Abel Ackerman being out sick does
   not make Beatrice absent too. A member's reading should depend only on what that member can obtain
   for itself.

## Why this is the same thing as "SICP-style", which the lead had been treating as a separate ask

The founder has asked for SICP-style decomposition and for performance engineering as first-order
requirements, repeatedly, and the lead had been reading those as style and as tooling. Under the
conclave reading they are the same requirement:

- **A chain makes a reading meaningful only in sequence.** Its value depends on where in the walk it
  was produced, so an abstention anywhere forces a guard, a default or a recomputation somewhere
  else. That is precisely the failure the founder named on 2026-10-11: *"things computed for one
  step are completely forgotten about and re-computed from scratch for an entirely different step."*
- **A conclave makes every reading a named value computed once where it becomes known and handed to
  every consumer** — the SICP discipline as `performance.md` states it. Order stops being
  load-bearing; only presence is. The assembly is then a pure function over the population of
  readings available, which is exactly the shape `AGENTS.md` requires of a decision: total over its
  arguments, returning named codes, every bar an argument.
- **The parallel unit falls out of the design rather than being chosen.** Members are independent, so
  the natural unit is (acquisition × lens); `ComputeContract.parallel_unit` already has a field for
  it. A chain would serialise work the problem does not actually order.
- **The cheap profile is only expressible in a conclave.** Thesis figure H2b sets a full profile
  beside a cheap one, bank by bank, marking each `Same rows` / `Whole pipeline only` /
  `Reads no Composite` / `Not written`. That *is* seating fewer members under a budget and reporting
  the quorum obtained. In a chain, dropping a step breaks everything after it; in a conclave it
  costs named rows and nothing else. This is the mechanism for the trade he named — "balance
  resolution and diagnosis quality with computational efficiency for the competition submission
  pipeline" — and it is already specified, not something to invent.
- **`handed_on` is the minute-book.** A frozen value a second consumer reads rather than recomputes.

So "clean SICP-style modular production pipeline" and "the competition scores for efficiency" are
not two requirements beside the thesis. They are what the conclave shape buys.

## The quorum report, as the lead reads it

`object-bundles` already encodes the distinction the conclave needs, and the lead did not previously
see that this is what it was for:

> "a bank this build cannot write ... appears with a named unavailable status, and **not** as rows of
> zero, because a zero count asserts that the reading was made and found nothing"

Absent member versus member present and silent. So the assembly is: per `<object>`, the counts of its
places' readings per (acquisition × lens), with unavailable members named unavailable. That table is
the seated body at that instant, and it is what the founder would read to supply the conjunctions
that name things.

## What the lead is NOT deciding

Whether the digit population may also be read against `background_split` — the histogram valley the
interiors stage already uses, which resolved on all five acquisitions — is a change to the founder's
design and is his to rule (law 9). The conclave reading does not settle it; it only says that the
present behaviour is a *transitive* absence rather than an independent one, which is a fact about the
dependency and not a proposal.

Whether `reached` should be removed, and what replaces `ROUTE`'s progress words, likewise go to him.

## The questions put to the second readers

1. Is the transitive-absence claim correct as a design principle — that in a conclave each member's
   reading must depend only on inputs it can obtain for itself, and that the terciles' dependence on
   the noise-law chain violates it? Or is a shared upstream measurement a legitimate member whose
   absence may properly silence others?
2. Is the lead's identification of the SICP discipline and the conclave shape as the *same*
   requirement sound, or is there a provable error in it?
3. Is the quorum report as described — per `<object>`, counts per (acquisition × lens), unavailable
   named rather than zeroed — the right form, and does it already follow from `object-bundles`?
4. Does `reached` have any legitimate role in a stateless-at-an-instant design?
