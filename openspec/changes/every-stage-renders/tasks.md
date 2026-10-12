# Tasks

**Read `just unit` first.** Every unit below takes the full build loop: declared here before code; a
pure decision total over its arguments returning named codes, with **every bar an argument**; PEP 316
contracts; two-sign intent tests calling directly; `just detective converge` with **every survivor
judged**; `just crosshair`; wired so something consumes it, with `just graph` showing nothing
dangling and `just imports` holding; a `ComputeContract` and ledger telemetry; a renderer that only
**arranges**; and a run on real data through `just analyze-objects`.

**The design this change builds is `docs/PIPELINE_AS_OBJECT.md`** — the pipeline as one functional
object, its four capacity properties, and what each stage's picture shows.

**What a sub-agent may do**, per `AGENTS.md` law 8: write the body against the spec, the renderer and
the serialiser. **Never**: the contract, the intent tests, a bar, a Detective survivor's verdict or
its equivalence note, or a change to a test to make code pass. A body lands only with its certificate
and after the lead has read it.

## The acceptance, which is the founder's and is written before the run it judges

> "Doesn't have to be good, or able to diagnose — it has to have the requisite component of the full
> thesis, and have the symbolic **capacity** to resolve and reason on these `<object>`s."

So the pass is complete when **one study, through the real entry point, produces every stage having
run, having returned a record or a named absence, and having rendered what it resolved** — and the
four capacity properties hold:

1. **symbols exist** — the field is parsed into `<object>`s with extents and boundaries, and every
   place is owned by one or named unassigned;
2. **a language exists** — every place carries a ternary digit per acquisition against a pair of
   edges from that series' own distribution, silence distinct from the middle digit;
3. **reasoning composes** — every decision is a named code, total over its arguments, every bar an
   argument, **and the decision reads a RELATION between its subjects rather than a property of one**;
4. **the correspondence is named** — the expected reading `e` is declared as a hand-given
   correspondence with its author and date, never computed and never fitted.

**Not an acceptance condition** (withdrawn 2026-10-12, both readers refused it): "a lens that needs
re-tuning per study is brittle". It is a counterfactual about a second study and acceptance is one.
What replaces it is the **provenance check** — every threshold has a declared provenance, either the
series' own distribution or a named design constant declared with the general pattern it encodes.
Per the founder, the check reports provenance and never rules on generality, because a constant found
by eye is legitimate when its rule describes how the anatomy presents *generally*. The guard against
over-fitting is his.

## The dispatch question, which binds tasks 2.4, 3.1 and 4.1

Codex, 2026-10-12: *"Removing anatomical words from records does not establish that anatomical
classification is absent from **dispatch**."* Before each of those tasks is implemented, its own
answer is recorded: **what resolved fact selects the structural role / the subject kind / the
predicate's subject, and which earlier stage computed it?** If the selector is a relational fact an
earlier stage produced, identity is not assumed. If it is a kind-label, it is, and the task stops.

## 0. The scaffold: every module has a place, a contract and a picture — before anything is delegated

- [x] 0.1 Declare every module's place in `docs/places.json` and compute the observed state against
      it with `scripts/places.py`. The `role` sentence is the one field nothing can check, so it is
      **counted when unwritten, never passed**.
- [x] 0.2 Teach the place check **both** idioms the codebase uses to declare a compute contract.
- [x] 0.5 Write the 25 unwritten roles by **reading each module whole**, a reading agent returning
      facts and the lead writing the sentence. Verified: 0 of 83 unwritten, computed by `just places`.
- [x] 0.3 **Unify to one compute-contract form.** Founder's ruling 2026-10-12: *"I guess only one? …
      the bigger risk is you forgetting that there are two formats."* The form is
      `CONTRACT = ComputeContract(...)` at module level **applied with `@contracted(CONTRACT)` on the
      reference kernel** — which `boundaries.py` already does, and which is the only form that both
      names the contract where a reader meets it and attaches it to the function it describes.
      Verify `contracted` still returns the kernel unwrapped (§13.5), and that each module carries
      exactly one contract, on its **reference** and not on its twin or its orchestrator.
- [x] 0.3a **Read `interiors.py` and `ledger.py` whole and establish whether their declared
      `CONTRACT` is attached to anything.** `find_referencing_symbols` on `contracted` returns six
      files and neither is among them, while `places.json` declares both as carrying a contract — so
      their contract is likely declared and never attached, which links it to no kernel. Verify by
      reading, not by the reference query alone, since absence there is not proof.
- [x] 0.3b Make the obligation structural rather than remembered: a check that every module holding a
      reference/twin pair declares a `ComputeContract` in the one form. **Enumerate the kernels and
      reference/twin pairs first** — Codex: *"the reported six compute contracts do not establish how
      many contracts are missing; the text does not identify every numeric kernel."* Verify it fails
      on a kernel whose contract is removed, and on one whose contract is declared but unattached.
- [x] 0.4 Add `renders` to the place registry and check it: a stage names the picture module that
      draws it, and the check verifies that module exists and sits in the drawing layer. Verify a
      stage claiming `built` with no renderer is reported. **Also record, per stage, whether its frame
      arranges values computed from the STUDY or values about the PIPELINE** — Fable: *"a stage is not
      built until it renders" cannot distinguish them*, so without this the route will report
      `relations` as built while its purpose is unserved.
- [x] 0.6 **Archive the five shelf packages and create `ownership`.** Founder's ruling 2026-10-12:
      *"Begone, Satan! … I'd rather lose work and have to re-do it than have you be constantly
      confused when you encounter old things we haven't structured properly."* `loop`, `candidates`,
      `cleanup`, `every_object` and `assignment` move to `archive/src/knee/` under their old paths;
      `src/knee/ownership/` is created fresh and not inherited from `cleanup` or `every_object`.
      Verify `just places` reports no `absent` and no `undeclared`, that the skeleton test follows,
      and that nothing in production imported any of the five.

## 1. The route and the vocabulary — the lead's, and first

- [x] 1.1 Replace `src/knee/pipeline.py`'s `ROUTE` with the object model's **nine** stages — study,
      collapse (the field), lenses, objects, relations, ownership, vectors (the bundles), predicates,
      output. **Not ten:** §6's border refinement is work inside `objects`, not a stage beside it, and
      a first draft of `docs/PIPELINE_AS_OBJECT.md` wrongly added it to the founder's settled route.
      Entries are package names because `test_a_stage_is_not_built_until_it_renders` reads them
      against `knee.pictures`. Verify `route_state` still reports honestly, that no stage claims a
      state it has not reached through the real entry point, and that `scripts/unit_loop.py` prints
      the new table.
- [ ] 1.2 Declare the shared absence vocabulary as `stage-totality` requires, with its three silences
      distinguished — predecessor absent, predecessor present but empty, item unread. Pin the pure
      decision two-sign. Verify no stage coins a private code for a silence it already names.
      **A fourth silence IS needed after all**, and this reversed twice. Fable proved the original
      shells required a silence that was none of the three. The lead then wrote that it dissolved,
      because 1.3 would make both stages real. 1.3a now shows relations cannot be real yet, so 1.3b
      keeps a shell whose silence is about a **missing construction**, not a missing input — still
      none of the three. The `stage-totality` spec already permits this: it says "at least three".
- [ ] 1.3 **Give `ownership` a thin REAL implementation.** The founder's `<object>` ruling removed
      identity as a blocker, and ownership needs nothing else: every place claimed by one `<object>`
      or named `unassigned` is `interiors.labels` read directly — a non-zero label is a claim, a zero
      inside the available field is the residual. It returns a record, it renders, and **its picture
      is the residual map**, every place nothing claims, which is the next structure argument and the
      channel the founder reads to supply the next lens. Verify it is consumed by the route and that
      `just graph` reports nothing dangling.
- [ ] 1.3a **Record which territory each bracketed profile reached across the dark.** This is the
      pairing `relations` needs and **it does not exist in any record**. Confirmed in source
      2026-10-12 by reading `interiors.py` whole: `boundary_edges` does
      `regions.append(labels[rows, cols])` — the territory's **own** label — and uses the neighbour
      only at `kind[padded[nr, nc] > 0] = EDGE_KINDS["peer_territory"]`, to set the edge kind. So the
      far side is genuinely unrecorded, and the pairs the thesis wants are bounded **across dark**,
      which are precisely the pairs that are *not* watershed-adjacent. Its own unit, its own contract,
      pinned two-sign. **Corrects a false claim this lead wrote into task 1.3 on 2026-10-12** — that
      relations was constructible "from the facing-pair graph the boundary census already computes".
      It is constructible in principle and it is **not a lookup**.
- [ ] 1.3b **`relations` stays an honest shell until 1.3a lands**, and its absence names the missing
      construction rather than a missing input. It runs, returns that named absence, and renders a
      frame showing it. Verify the absence it returns is not one of 1.2's three input silences, since
      it is not about an input at all.

## 2. The lenses MVP — delegable

- [ ] 2.1 Correct `knee.lenses.digits.digit_code` to take a **low and a high edge**, both belonging to
      the middle row, replacing the withdrawn witness-middle-plus-spread-band shape. Re-pin it
      two-sign; verify no bar is a literal in the body.
- [ ] 2.2 Implement the per-series edge pair from the series' own foreground, reading
      `RegimeKey.terciles`, and refuse with a named code where the population is too small to place a
      pair. Verify two acquisitions of one knee are each read against their own edges.
- [ ] 2.3 Write the digits for every place of every acquisition, recording `normalisation: none` and
      keeping an unread place **silent** rather than writing it as the middle digit. Verify silence
      and the middle digit are distinguishable in the record.
- [ ] 2.4 Wire it into the production route and render it: the three-colour digit map per
      acquisition, with silence drawn as silence. **Record the dispatch answer first.** Verify the
      renderer arranges only what the stage computed, then run it over one study through the real
      entry point.

## 3. The bundles MVP — delegable

- [ ] 3.1 Implement the profile as row counts over named banks, with every bank present and the
      unwritable ones carried as a **named unavailable status, never rows of zero**, and with **the
      subject kind it was keyed on recorded** so a consumer handed a territory-keyed profile can
      abstain rather than take the territory for its subject. **Record the dispatch answer first**:
      if "subject kind" is anatomical this task stops. Verify a zero count can only mean a reading
      was made and found nothing.
- [ ] 3.2 Write the two banks this build can honestly fill — the place's own reading (recorded as a
      single plane, never as a volume) and how the object came out (its seeds, its edge counts and
      the two typings of each edge). Verify the record names the stage each quantity came from.
- [ ] 3.3 Wire and render it: the count table, with unavailable banks visible as unavailable. Verify
      no bank is written under the name of a bank whose definition is unsettled.

## 4. The predicates and output MVP — delegable

- [ ] 4.1 Implement the twelve as named decisions over the subjects the object model gives them, each
      returning the abstention code with a reason naming what was not resolved, **and each reading a
      RELATION between its subjects rather than a property of one** (capacity property 3). **Record
      the dispatch answer first**: how does a predicate come to receive `<object>` 3 and 7 rather than
      4 and 9? Verify the stage refuses any input from a label, a score or a previous outcome.
- [ ] 4.2 Implement the submission serialiser against `sample_submission.csv`'s schema, taking the
      abstention value as an argument **declared in the spec before any run** — it is not declared
      there today, and under Law 4 that is a bar the founder owes. Write the companion record of
      codes and reasons **in the same run**; the submission is its lossy projection. Verify a
      submission without its companion record is refused.
- [ ] 4.3 Wire and render both: the twelve-row table per study, each row showing its abstention and
      reason. Verify the wires by `just graph` and telemetry, **never** by the submission file — a
      disconnected stage returning twelve abstentions would produce the same file.

## 5. The whole route, end to end

- [ ] 5.1 Run every stage over one study through Chapter 1's entry point, save the image series and
      the receipt, and verify the route reports each stage's state honestly against what it actually
      reached, **and that the four capacity properties hold**. One study is PROOF and not a smoke
      test — evidence is existential, and the 58-study run is engineering scheduled separately.
- [ ] 5.2 **The first grading round**, which the founder settled as *both* readers' proposals:
      the **alphabet** (the digit map with silence drawn as silence; the parse with measured boundary
      distinguished from constructed) **and** the first complete **sentence**
      (object–interstice–object with its boundary provenance visible). Not the predicates — grading
      those first would be grading words before letters. **This is the point of the change**: he
      assigns meaning to what the tooling shows, and nothing here may assign it for him.

## Beside this change, unparked rather than duplicated

**Borders — §6 — is `object-resolution-toolkit` tasks 3.8–3.12**, unparked 2026-10-12 on the argument
that if no pipeline record ever carries an anatomical name and §6's precondition were an anatomical
name, §6 could never run *in principle*. Its "role" is the structural role a lens assigns. It is
sequenced after §1, does not block §2–§4, and is **not delegable**: its own task text requires the
support contract specified before implementation.

Readings: `docs/chapters/02-collapse/readings/breadth-first-mvp-{codex,fable}.md`,
`faithfulness-{codex,fable}.md`, `pipeline-as-object-{codex,fable}.md`; the lead's own readings,
written before each, in `workbench/consults/`.
