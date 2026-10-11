# Tasks

**Read `just unit` first.** Every unit below takes the full build loop: declared here before code; a
pure decision total over its arguments returning named codes, with **every bar an argument**; PEP 316
contracts; two-sign intent tests calling directly; `just detective converge` with **every survivor
judged**; `just crosshair`; wired so something consumes it, with `just graph` showing nothing
dangling and `just imports` holding; a `ComputeContract` and ledger telemetry; a renderer that only
**arranges**; and a run on real data through `just analyze-objects`.

**What a sub-agent may do**, per `AGENTS.md` law 8: write the body against the spec, the renderer and
the serialiser. **Never**: the contract, the intent tests, a bar, a Detective survivor's verdict or
its equivalence note, or a change to a test to make code pass. A body lands only with its certificate
and after the lead has read it.

## 0. The scaffold: every module has a place, a contract and a picture — before anything is delegated

Nothing in sections 2–4 is handed to a sub-agent until the module it touches has a written role and,
where it is a kernel, a compute contract. The spec a sub-agent reads is only as good as this.

- [x] 0.1 Declare every module's place — where it sits, whether it carries a compute contract, and
      what draws it — in `docs/places.json`, and compute the observed state against it with
      `scripts/places.py`. Report only what a check can compare to something observed: a kernel's
      reads and writes stay in its `ComputeContract`, a stage's state in the route, a bar in the spec
      that declared it. The `role` sentence is the one field nothing can check, so it is **counted
      when unwritten, never passed**. Verify the check names its own blind spots: reachability is by
      import and at module scale, while the failure it exists for is "one function at a time".
- [x] 0.2 Teach the place check **both** idioms the codebase uses to declare a compute contract —
      `CONTRACT = ComputeContract(...)` at module level, and `@contracted(ComputeContract(...))` on
      the kernel. A check that knew only the first reported `profiles.py` and `band_raster.py` as
      kernels missing their contract, which the lead repeated to the founder as a defect in
      production code; both are contracted by the decorator. Verify `contract_disagrees` is none, and
      that the literal reading of one idiom is never taken for the obligation.
- [ ] 0.3 Put the two idioms to the founder as a consistency question rather than resolving it: a
      new kernel's author cannot tell which to use, and the check now has to know both. Verify no
      idiom is changed without his word, since both are his.
- [ ] 0.3b Make the obligation structural rather than remembered: a check that every module holding a
      reference/twin pair declares a `ComputeContract` in either idiom, so the next kernel cannot
      land without one. Verify it fails on a kernel whose contract is removed.
- [ ] 0.4 Add `renders` to the place registry and check it: a stage names the picture module that
      draws it, and the check verifies that module exists and sits in the drawing layer. Verify a
      stage claiming `built` with no renderer is reported.
- [ ] 0.5 Write the 25 unwritten roles by **reading each module whole**, a reading agent returning
      facts (its public functions, its imports, its returns, whether it holds a reference/twin pair)
      and the lead writing the sentence. Verify no role is written for a module nobody read, and that
      the unwritten count is computed rather than asserted.

## 1. The route and the vocabulary — the lead's, and first

- [ ] 1.1 Replace `src/knee/pipeline.py`'s `ROUTE` with the object model's stages (study, field,
      lenses, objects, relations, ownership, bundles, predicates, output) per `docs/OBJECT_MODEL.md`'s
      route table, which records `field` as the collapse's content and `SPINE.md` as folding Figure
      8's remaining roles in. Verify `route_state` still reports honestly, that no stage claims a
      state it has not reached through the real entry point, and that `scripts/unit_loop.py` prints
      the new table.
- [ ] 1.2 Declare the shared absence vocabulary as the capability `stage-totality` requires, with its
      three silences distinguished — predecessor absent, predecessor present but empty, item unread.
      Pin the pure decision two-sign. Verify no stage coins a private code for a silence it names.
- [ ] 1.3 Give `relations` and `ownership` honest shells: each runs, returns the named absence saying
      **why** its record shape is unsettled, and renders a frame that shows it. Verify each is
      consumed by the route and that `just graph` reports nothing dangling.

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
      acquisition, with silence drawn as silence. Verify the renderer arranges only what the stage
      computed, then run it over one study through the real entry point.

## 3. The bundles MVP — delegable

- [ ] 3.1 Implement the profile as row counts over named banks, with every bank present and the
      unwritable ones carried as a **named unavailable status, never rows of zero**. Verify a zero
      count can only mean a reading was made and found nothing.
- [ ] 3.2 Write the two banks this build can honestly fill — the place's own reading (recorded as a
      single plane, never as a volume) and how the object came out (its seeds, its edge counts and
      the two typings of each edge). Verify the record names the stage each quantity came from.
- [ ] 3.3 Wire and render it: the count table, with unavailable banks visible as unavailable. Verify
      no bank is written under the name of a bank whose definition is unsettled.

## 4. The predicates and output MVP — delegable

- [ ] 4.1 Implement the twelve as named decisions over the subjects the object model gives them, each
      returning the abstention code with a reason naming what was not resolved. Verify the stage
      refuses any input from a label, a score or a previous outcome.
- [ ] 4.2 Implement the submission serialiser against `sample_submission.csv`'s schema, taking the
      abstention value as an argument declared in the spec, and writing the companion record of codes
      and reasons **in the same run**. Verify a submission without its companion record is refused.
- [ ] 4.3 Wire and render both: the twelve-row table per study, each row showing its abstention and
      reason. Verify the wires by `just graph` and telemetry, **never** by the submission file —
      a disconnected stage returning twelve abstentions would produce the same file.

## 5. The whole route, end to end

- [ ] 5.1 Run every stage over one study through Chapter 1's entry point, save the image series and
      the receipt, and verify the route reports each stage's state honestly against what it actually
      reached.
- [ ] 5.2 Inspect the image series with the founder. **This is the point of the change**: he assigns
      meaning to what the tooling shows, and nothing in this change may assign it for him.

Readings: `docs/chapters/02-collapse/readings/breadth-first-mvp-{codex,fable}.md`; the lead's own
plan, written before either, `workbench/consults/breadth-first-mvp.md`. Both readers corrected the
claim that totality makes stages *buildable* in any order — it makes them *wireable* — which is why
relations and ownership are shells here and not content.
