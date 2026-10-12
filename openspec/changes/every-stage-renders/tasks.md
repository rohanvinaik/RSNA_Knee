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
   argument, **and where the object model gives a finding a relation as its subject, the decision
   reads that RELATION between its two subjects rather than a property of one** (scoped 2026-10-12
   by the founder's Fracture sentence, which makes a fracture a predicate on one object;
   `docs/PIPELINE_AS_OBJECT.md`);
4. **the correspondence is named** — the expected reading `e` is declared as a hand-given
   correspondence with its author and date, never computed and never fitted.

**Not an acceptance condition** (withdrawn 2026-10-12, both readers refused it): "a lens that needs
re-tuning per study is brittle". It is a counterfactual about a second study and acceptance is one.
What replaces it is the **provenance check** — every threshold has a declared provenance, either the
series' own distribution or a named design constant declared with the general pattern it encodes.
Per the founder, the check reports provenance and never rules on generality, because a constant found
by eye is legitimate when its rule describes how the anatomy presents *generally*. The guard against
over-fitting is his.

The universal relational wording this item once carried was the lead's, not the founder's, and
his own sentence contradicted it; it is scoped as above, and `knee.predicates` reads a relation
for the ten construction-subject findings and a population for the two object-subject ones.

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

Continuation discipline (founder instruction 2026-10-12): mechanize settled packets through Sonnet
API calls and local sub-agents under the delegation contract above. Record exact verification
standing per unit; a refusal leaves that unit open while independent declared work continues.
Task 1.3a now has its support contract and a connected/rendered candidate, but admission
remains open. Continue under the existing dependency order; do not treat it as unwritten
or certified. The dated reconciliation run and `docs/BUILD_PLAN.md` locate current evidence.

- [x] 1.1 Replace `src/knee/pipeline.py`'s `ROUTE` with the object model's **nine** stages — study,
      collapse (the field), lenses, objects, relations, ownership, vectors (the bundles), predicates,
      output. **Not ten:** §6's border refinement is work inside `objects`, not a stage beside it, and
      a first draft of `docs/PIPELINE_AS_OBJECT.md` wrongly added it to the founder's settled route.
      Entries are package names because `test_a_stage_is_not_built_until_it_renders` reads them
      against `knee.pictures`. Verify `route_state` still reports honestly, that no stage claims a
      state it has not reached through the real entry point, and that `scripts/unit_loop.py` prints
      the new table.
- [x] 1.2 Declare the shared absence vocabulary as `stage-totality` requires, with its three silences
      distinguished — predecessor absent, predecessor present but empty, item unread. Pin the pure
      decision two-sign. Verify no stage coins a private code for a silence it already names.
      **A fourth silence IS needed after all**, and this reversed twice. Fable proved the original
      shells required a silence that was none of the three. The lead then wrote that it dissolved,
      because 1.3 would make both stages real. 1.3a now shows relations cannot be real yet, so 1.3b
      keeps a shell whose silence is about a **missing construction**, not a missing input — still
      none of the three. The `stage-totality` spec already permits this: it says "at least three".
      *(DONE 2026-10-12, `e79c633` + `2cb49e3`. Four codes; `absence_code` and `is_silence` both
      Detective-COMPLETE with zero survivors; both CrossHair-confirmed over all paths; 13 intent
      tests. Held open deliberately until the unit had a CONSUMER — step 7 of the loop — which
      `run_study` now is.)*
- [x] 1.3 **Give `ownership` a thin REAL implementation.** The founder's `<object>` ruling removed
      identity as a blocker, and ownership needs nothing else: every place claimed by one `<object>`
      or named `unassigned` is `interiors.labels` read directly — a non-zero label is a claim, a zero
      inside the available field is the residual. It returns a record, it renders, and **its picture
      is the residual map**, every place nothing claims, which is the next structure argument and the
      channel the founder reads to supply the next lens. Verify it is consumed by the route and that
      `just graph` reports nothing dangling.
      *(PARTLY done 2026-10-12, `0006f4e` + `2cb49e3`: built, 12 intent tests, `ownership_code`
      Detective-COMPLETE 3/3, CrossHair run, consumed by `run_study`, `just graph` valid.
      Renderer remainder completed in this session: Sonnet API body read by lead, 10 direct
      picture intent tests; writer saves returned masks/counts/codes; partition_frames draws five
      series through the real entry point in data/measurements/partition-frames-20261012 and
      data/pictures/partition-frames-20261012. Graph valid; import contract kept. Ownership's
      frame is study-derived; relations' frame is pipeline status.)*
- [ ] 1.3a **Record which territory each bracketed profile reached across the dark.** This is the
      pairing `relations` needs. **At declaration it did not exist in any record**; the
      candidate below now retains sampled pairs, with complete extents and admission still owed. Confirmed in source
      2026-10-12 by reading `interiors.py` whole: `boundary_edges` does
      `regions.append(labels[rows, cols])` — the territory's **own** label — and reads the neighbour
      only to decide *that* a place is an edge (`neighbor != labels`) and of which *kind*. **Sharpened
      the same day by the sub-agent that wrote 1.3b, and the refinement changes what this task is:**
      for a `peer_territory` edge the neighbour's label *would* record the far side, so merely
      storing it is not the job. The pairs the thesis wants are bounded **across dark**, and there
      `interior = available & ~dark` with watershed `mask=interior`, so the neighbour is a dark place
      whose label is **0** — there is no far-side label to store. `dark_bands` records where a band
      lies (a position) and never which territory a profile reached beyond it. **So this task is to
      CONSTRUCT the dark-bounded pairing, not to record an existing one.** Its own unit, its own
      contract,
      pinned two-sign. **Corrects a false claim this lead wrote into task 1.3 on 2026-10-12** — that
      relations was constructible "from the facing-pair graph the boundary census already computes".
      It is constructible in principle and it is **not a lookup**.
      Support contract declared before implementation in `specs/dark-bounded-pairing/spec.md`;
      lead reasoning is `docs/chapters/02-collapse/readings/dark-pairing-lead-20261012.md`.
      This unit retains the native contributing labels immediately flanking the existing bracket,
      not an interpolated label. It records sample-supported pairs and every refusal; complete
      interstice extent construction remains a separate obligation of relations.
      *(Candidate implemented, wired and rendered 2026-10-12. One study/five series retains every
      profile outcome; 597 supported sampled pairs, not complete interstices. Pure `pair_code`
      Detective COMPLETE modulo five crash-only value gaps; CrossHair Not confirmed. Numeric
      `footprint_labels_reference` Detective UNGATEABLE: mutants could not be BUILT; no retry or
      waiver. Ordinary gate passes, but LintGate/compute-budget obligations remain. Task stays open.
      Full standing and receipts: `workbench/consults/dark-pairing-status-20261012.md`.)*
- [x] 1.3b **`relations` stays an honest shell until 1.3a lands**, and its absence names the missing
      construction rather than a missing input. It runs, returns that named absence, and renders a
      frame showing it. Verify the absence it returns is not one of 1.2's three input silences, since
      it is not about an input at all.
      *(PARTLY done 2026-10-12, `1b4a96d` + `2cb49e3`: built, 10 intent tests, Detective-COMPLETE
      with all six equivalent survivors flagged with their proof, CrossHair confirmed over all paths,
      consumed by `run_study`. Frame completed in this session by local sub-agent, lead-read
      and tested with 1.3; the same real-study gallery shows construction_absent for all five
      series. ROUTE remains not_built for actual relation construction.)*

## 2. The lenses MVP — delegable

- [x] 2.1 Correct `knee.lenses.digits.digit_code` to take a **low and a high edge**, both belonging to
      the middle row, replacing the withdrawn witness-middle-plus-spread-band shape. Re-pin it
      two-sign; verify no bar is a literal in the body.
      *(DONE before 2026-10-12's audit: the signature is `digit_code(place_value, low_edge,
      high_edge, population_count, minimum_population)`; certificate `complete` at digest
      `004f24d94763e508`. Box reconciled 2026-10-12.)*
- [x] 2.2 Implement the per-series edge pair from the series' own foreground, reading
      `RegimeKey.terciles`, and refuse with a named code where the population is too small to place a
      pair. Verify two acquisitions of one knee are each read against their own edges.
      *(DONE before 2026-10-12's audit, evidenced by the writer: every seated member carries its own
      `low_edge`, `high_edge`, `population_count` and `minimum_population` per series and refuses by
      name; `standing_code` and `is_retained` certificates complete. Box reconciled 2026-10-12.)*
- [x] 2.2a **Seat the second member: the background-split population.** Founder's ruling 2026-10-12,
      after both readers showed a fallback would be a *default* and project law 3 forbids one: "we
      always keep information we compute. I'll resolve what we report and how we do it, but the
      pipeline should keep everything, including where things conflict". So the terciles over the
      values above `RegimeKey.background_split` are a SECOND member seated beside the terciles over
      the noise-law cut — not a source the lens falls back to.

      **Measured 2026-10-12, before the task was written**, one study, five acquisitions, drawn in
      `data/pictures/two-populations-20261012/`: the noise-law member places a pair on 2 of 5; the
      background-split member places one on 5 of 5. Where both read they agree to within one stored
      unit (80.0/120.0 against 79.0/119.0) and are identical on another (80.0/121.0, population
      1,581,244 both). **That agreement is NOT interchangeability** — both readers said so
      independently, Codex: "agreement on two acquisitions is evidence of agreement there, not proof
      of interchangeability"; Fable: "what they say on the rest is the information". The two
      populations encode different invariants: carries-signal-above-the-noise-floor, and
      tissue-against-air.

      Its own unit, its own contract, pinned two-sign. Verify that neither member is read only when
      the other is absent, that a place where the two digits differ retains both, and that no field
      of the record names a single edge pair for the series. The quorum question — what coverage is
      *sufficient* — is NOT settled by this task: both readers showed counts are the input to that
      judgement and not the judgement, and the judgement is the founder's.
      *(DONE 2026-10-12, `bd9e9b0`, before the audit: both members seated per series with their own
      edges and populations, and the standing between them per place retained. Box reconciled
      2026-10-12.)*
- [ ] 2.3 Write the digits for every place of every acquisition, recording `normalisation: none` and
      keeping an unread place **silent** rather than writing it as the middle digit. Verify silence
      and the middle digit are distinguishable in the record.
      *(Candidate implemented and rendered, not certified. The 2026-10-12 Detective run for
      `place_codes_reference` returned UNGATEABLE because mutants could not be BUILT; counts are
      a floor, not a verdict. Array CrossHair contracts were Not confirmed. Read the full evidence
      and limits in `workbench/consults/openspec-contract-audit-20261012.md`; this task remains open.)*
- [ ] 2.4 Wire it into the production route and render it: the three-colour digit map per
      acquisition, with silence drawn as silence. **Record the dispatch answer first.** Verify the
      renderer arranges only what the stage computed, then run it over one study through the real
      entry point.
      *(Dispatch answer, recorded 2026-10-12: the digit map is keyed on the native place index of
      the series' own volume, and each member's edges come from a population the regime measured
      (the noise-law foreground, the background split) — relational facts an earlier stage computed,
      no kind-label anywhere, so the task proceeds. Wired: `read_lenses` runs in `run_study` and
      `lenses.produced` is consumed by vectors; drawn by `lens_frames` through the one command. Open
      as a candidate with 2.3 while `place_codes_reference` is UNGATEABLE.)*

## 3. The bundles MVP — delegable

- [x] 3.1 Implement the profile as row counts over named banks, with every bank present and the
      unwritable ones carried as a **named unavailable status, never rows of zero**, and with **the
      subject kind it was keyed on recorded** so a consumer handed a territory-keyed profile can
      abstain rather than take the territory for its subject. **Record the dispatch answer first**:
      if "subject kind" is anatomical this task stops. Verify a zero count can only mean a reading
      was made and found nothing.
      *(DONE 2026-10-12 under 6.7, where the dispatch answer is recorded: the subject kind is
      `indexed_extent_of_the_selected_native_plane`, a relational fact ownership's solitary member
      resolved; every reading carries `subject_kind`, and an unavailable bank carries a named
      status. Box reconciled 2026-10-12.)*
- [ ] 3.2 Write the two banks this build can honestly fill — the place's own reading (recorded as a
      single plane, never as a volume) and how the object came out (its seeds, its edge counts and
      the two typings of each edge). Verify the record names the stage each quantity came from.
      *(PARTLY under 6.7: `own_reading:<member>` per seated lens member, `lens_standing`, `came_out`
      with edge kinds and trace codes, and `through_plane:<uid>` are written, each naming its source
      stage. The SEEDS are not in `came_out` and are owed. Candidate while `count_by_extent` is
      UNGATEABLE.)*
- [ ] 3.3 Wire and render it: the count table, with unavailable banks visible as unavailable. Verify
      no bank is written under the name of a bank whose definition is unsettled.
      *(Wired and drawn under 6.7: `bundle_frames` draws one table per profile with unavailable banks
      visible, and the four unsettled banks are carried by name in `UNAVAILABLE_BANKS`. Open with
      3.2 under the candidate rule.)*

## 4. The predicates and output MVP — delegable

- [x] 4.1 Implement the twelve as named decisions over the subjects the object model gives them, each
      returning the abstention code with a reason naming what was not resolved, **and each reading a
      RELATION between its subjects rather than a property of one** (capacity property 3). **Record
      the dispatch answer first**: how does a predicate come to receive `<object>` 3 and 7 rather than
      4 and 9? Verify the stage refuses any input from a label, a score or a previous outcome.

      **The answer recorded here on 2026-10-12 has been DELETED, not amended.** It said no resolved
      fact selects any subject. That was written after reading two fields — `ownership.code` and
      `relations.code` — while `measurements.boundaries` sat unread on the same object. It carries
      `pair_labels` (Q,2), "the touching pairs, each ascending and listed once", in production, with
      their sites, saddle and codes. So a record of which two territories face each other already
      exists; only the pairs separated **across dark** are missing, which is what
      `relations/shell.py` already said. The founder's standing ruling is that an unauthorised
      finding is deleted rather than kept with a note, so it is gone.

      Code from that attempt is in `8a0e8d1`/`21f6b41` and still runs; whether it stays, is rewired
      to what the pipeline already computes, or comes out is the founder's call, not the lead's.

      *(DONE 2026-10-12 as 6.4, declared under the founder's instruction of that day to repair the
      audit: the `21f6b41` code was REWIRED to what the pipeline computes. Dispatch answer, recorded:
      a finding's subject is selected by the construction KIND the object model gives it, read from
      the `Interstice` records relations produces — a relational fact an earlier stage computes,
      never a kind-label; several of one kind return `dispatch_undeclared`. Capacity property 3 is
      scoped as at the top of this file. Box reconciled 2026-10-12.)*
- [x] 4.2 Implement the submission serialiser against `sample_submission.csv`'s schema, taking the
      abstention value as an argument **declared in the spec before CSV emission** — it is not declared
      there today. Founder correction, 2026-10-12: "I don't know, that should resolve
      experientially, when actually running and seeing it in action". Run and render the named
      decisions first; the numeric projection remains undeclared until that inspection and the
      serialiser refuses CSV emission without it. Write the companion record of
      codes and reasons **in the same run**; the submission is its lossy projection. Verify a
      submission without its companion record is refused.
      *(DONE 2026-10-12 as 6.8. Box reconciled 2026-10-12.)*
- [x] 4.3 Wire and render both: the twelve-row table per study, each row showing its abstention and
      reason. Verify the wires by `just graph` and telemetry, **never** by the submission file — a
      disconnected stage returning twelve abstentions would produce the same file.
      *(DONE 2026-10-12: `predicate_frames` and `output_frames` draw both halves through the one
      command; the wires are evidenced by the composition test and the real run's ledger, never by
      the file. Box reconciled 2026-10-12.)*

## 4b. ONE COMMAND — the pipeline as a single object. Founder, 2026-10-12

His authorisation and its shape, verbatim: *"this is a production pipeline. Everything connected
properly as a coherent instantiation of the thesis, as the thesis itself lays out. That's all I
wanted"* — and, on scope: *"Not a 'small piece', there is no such thing as a 'small piece' of a
single object. All of it."*

On what the drawing IS, which removes the obstacle the lead had invented: *"the analysis isn't
LITERALLY done off a drawn image … 'Drawing' is just the output of the analysis, but since this is
visual data, it can most effectively be judged visually, so why not print? … it should be something
that can be turned off for an actual competition setting, where the output is just the diagnosis …
but it should be absurdly cheap to put out, since it's just a printed copy of the analysis that is
already required."*

Nothing forbade this. Thesis §13.7 (`what_an_object_is.md:4332`) puts **"drawing pictures"** at the
thin impure edge beside *"reading a movie, writing the output"*, and its purpose clause is *"so
pictures are a layer that can be switched off."* The enforced contract forbids only the **`knee`**
package from importing matplotlib; the entry point lives in `workbench` and is outside it.

MEASURED before this section was written, one study, every switch on: `reached: ownership`;
**zero images**; 27 ledger events from four sources only (lenses, boundary census, pairings,
predicates) with **study, collapse, ownership, relations and conversation recording nothing**;
conversation one exchange on four of five series and `solitary` on the fifth; lenses `no_edges` on
three of five; relations `construction_absent` on all five.

- [x] 4b.1 **Give every drawing module one entry a caller can use.** The eight renderers
      (`object_packet`, `object_interiors`, `object_conversation`, `object_boundaries`,
      `partition_frames`, `pair_frames`, `lens_frames`, `predicate_frames`) each expose only
      `main()` behind argparse, which is why nothing can join them. Each gains
      `draw(run, study_uid, out) -> dict` and `main()` becomes a thin wrapper over it. Verify each
      existing command still works unchanged and its manifest is byte-identical.

      **Two defects the refactor surfaced, both reported by the sub-agent rather than papered
      over, and both OWED:**
      - `object_packet.draw` cannot be called as `draw(run, study_uid, out)`: its
        `--probe-fraction-rc` is `required=True` with no default, so the signature is
        `draw(..., *, probe_fraction_rc)`. The agent refused to invent a value, correctly — a
        probe fraction is a bar, and bars are the founder's. Until he gives one the joiner records
        that stage `not_drawn` with the reason, which is honest but means **one stage of the
        single command does not draw**. HIS RULING: what probe fraction the one command uses.
      - `main()` now catches every `ValueError` from `draw()`, not only the argument refusals it
        was meant to catch. That swallows `saved_array_digest_mismatch` and `json.JSONDecodeError`
        into an exit-2 usage error. A corruption signal must never be dressed as a typo. The fix
        is a dedicated refusal type the argument checks raise and `main()` alone catches, leaving
        real `ValueError`s to propagate. **The joined run is unaffected** — the joiner calls
        `draw()` directly and records the true reason — so this degrades only the hand-typed
        command, and it is owed before this section is checked off.

      *(DONE: both defects were repaired in `object_packet.py` before §6 was declared, as its
      preamble records from source — `CENTRE_OF_THE_FRAME` is a declared display default, not a
      measurement bar, and `main()` catches `ArgumentRefusal` only. Box reconciled 2026-10-12.)*
- [x] 4b.2 **One joiner** that takes the saved run and draws every stage, collecting each
      renderer's manifest into a single gallery index. A stage whose reading is a named absence
      draws its absence and the joiner records it; **one renderer failing never fails the run**, it
      returns its named code. Verify the index names every stage of `ROUTE`, present or absent.
- [x] 4b.3 **The entry point draws.** `workbench.measure.object_analysis` calls the joiner after
      writing its receipt, under `--pictures/--no-pictures`, default ON; `--no-pictures` disables the drawing edge for eventual competition use. It does
      not itself implement the competition kernel, output projection or DEPLOY proof. The `analyze-objects` recipe
      becomes `uv run --with matplotlib` so the one command has it; `knee` still never imports it
      and `just imports` must still pass.
- [x] 4b.4 **The acquisitions converse by default**, not behind a flag — "the combined sum total of
      all the analyses we have in conversation with one another" is what the one command does.
      Mind `AnalysisRequest.__post_init__`, which couples `conversation` to `prominence_mm`.
- [x] 4b.5 **Telemetry everywhere.** The five silent stages — study, collapse, ownership, relations,
      conversation — each record what they produced and what was consumed, as lenses and pairings
      already do. Verify by re-running and counting ledger sources, not by reading the code.
      *(DONE 2026-10-12 as 6.5, verified by the real run's ledger sources. Box reconciled
      2026-10-12.)*
- [x] 4b.6 **Run the one command and measure it against the five rows above.** Each row moves or is
      reported unmoved with its reason. Nothing here may call the pipeline coherent on the strength
      of one function; the evidence is the re-run.

- [x] 4b.7 **The field keeps what it computed, and draws it.** `collapse` computes two things per
      series — the regime key (sixteen readings when this was written; 23 since the second lens
      member was seated) and the squint — and the writer reads **one** field
      off the regime key (`background_split`) and drops the other fifteen. The squint is saved and
      nothing draws it. The founder, 2026-10-12: *"we compute the required object, we drop it"*, and
      on why it matters: *"any compute process here is done for the purpose of visual reasoning. If
      the lenses don't have information that they can literally show, then what are we doing?"*

      **No new measurement.** Serialise the whole regime key beside the squint; give `collapse` a
      drawer registered in the joiner like every other stage; and correct `knee.pictures.collapse`,
      whose `panels()` asks for a leg, a superior–inferior profile and an axis sign that this stage
      does not compute and that nothing calls (`find_referencing_symbols`: **zero references** on
      both `panels` and `over`, 2026-10-12). Those words came from the adapter's docstring, not from
      the route.

      Verify the drawer arranges only values already saved and recomputes no reading; that the
      joined run reports `collapse` **drawn** rather than `no_drawer`; and that a series whose
      regime could not be read still draws, naming the absence.
      *(Declared before any code was written. The founder: "This IS what the production pipeline is
      for ... do NOT make it some random script in a throwaway folder somewhere.")*
      *(DONE 2026-10-12: the writer enumerates every regime field; `field_frames` draws the regime
      key and the squint through `field_panels`, and the joined run reports `collapse` drawn.
      `panels()` and `over()` are untouched, per 6.9 and 7.1. Box reconciled 2026-10-12.)*

Joined-task evidence (4b.2/3/4/6): implemented in `92e5b7e`; fresh one-command
run recorded in `docs/chapters/02-collapse/measurements/documentation-reconciliation-20261012.md`.
Seven drawings, one named failure, three `no_drawer` stages; conversation 4 measured/1 solitary;
60 ledger events. No capacity completion follows. 4b.1 and 4b.5 closed under §6, as their notes
say; §5 remains wholly open.

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

## 6. The composition repairs — `docs/HANDOFF_WIRING.md` and its Codex reading, 2026-10-12

The founder, 2026-10-12: *"So much of the work needed for me to actually perform reasoning and
design is just not built right. I need the thing to actually work and be wired right, after which
I can actually do the REAL work."* Declared before any code. The capability is
`specs/route-composition/spec.md`. Each item names what consumes what, and the verification is
the re-run's ledger and the gate, never the artifact (design.md, correction two).

Corrected from source before declaring, because the handoff was written to guide this fix and a
fix-guiding note goes stale: both 4b.1 defects are already repaired in `object_packet.py`
(`CENTRE_OF_THE_FRAME` is a declared display default, `main()` catches `ArgumentRefusal` only),
and `REQUIREMENTS` in `findings.py` follows the object model's table order, not the competition's
column order its comment claimed — the index-to-column correspondence is `knee.output`'s.

**The candidate rule** (made explicit 2026-10-12 and applied retroactively to 6.7): a task whose
numeric kernel Detective returns UNGATEABLE stays open as a candidate with its standing written
beside it, exactly as 2.3 and 1.3a do. The engine defect is reported and never waived, and a green
ordinary gate never closes the task.

- [x] 6.1 **The route runs in dependency order.** *(DONE 2026-10-12; measured on the real study:
      `conversation.produced` at ledger index 47, first `ownership.produced` at 53 —
      `measurements/composition-repair-20261012.md`.)* `run_study` measures every series, then
      converses, then partitions, relates, bundles, predicates and projects — so the conversation's
      refined parse is an INPUT to ownership and relations instead of a record computed after the
      findings. `SeriesRun` carries its own conversation reading and `StudyRun.conversations` is
      derived from it. Verify by the ledger: `conversation.produced` precedes `ownership.produced`
      and ownership records `conversation.consumed_by.ownership`.
- [x] 6.2 **Ownership seats one member per parse.** *(DONE 2026-10-12: three members on every
      series of the real study, disagreeing places 225/464/290/215/0; `members_code` and
      `comparison_code` Detective-COMPLETE, `comparison_code` CrossHair-confirmed.)* The solitary parse (`interiors.labels`) and,
      where the conversation read the series, its concurrent and conditional subdivisions, each
      read with the same `read_ownership` and kept; the disagreement between solitary and
      concurrent claims retained as a mask and a count. No member is a fallback and no field
      names a winner (founder: "keep everything, including where things conflict"). Pure
      decisions `members_code` and `comparison_code`, pinned two-sign. Verify: a series the
      conversation could not read seats one member; a measured one seats three; the writer saves
      each and `partition_frames` draws each.
- [x] 6.3 **Relations carries its pairings.** *(DONE 2026-10-12: the same 597 pairs on the real
      study; `read_relations` Detective-COMPLETE modulo 7 unproven ledger survivors and 10 flagged
      with proofs — standing in `measurements/composition-repair-20261012.md`.)* `read_relations(interiors, spacing_rc)` calls
      `read_pairings` itself and returns the reading as `RelationsReading.pairings`; `code` stays
      `construction_absent` for the interstice extent, which is still unbuilt, and `why`
      inventories what IS retained. `SeriesRun.pairings` is removed; the writer, the graph and
      `pair_frames` read `relations.pairings`. `Interstice` and `KINDS` are declared so the
      construction, when built, fills a shape predicates already read. `read_pairings` becomes
      total over a malformed predecessor (`invalid_count`), as `read_ownership` is. Verify the
      shell's must-nots still hold and the real run retains the same 597 pairs.
- [ ] 6.3a **Pairings under the conversed parses** — declared, not built here. Each edge's source
      label must be translated to the piece containing its territory-side pixel (the edge point
      minus half the sign of its normal, which is exact) before the same `read_pairings` can run
      on a subdivided parse; without that, every near footprint reads `source_mismatch`. Its own
      unit, its own contract, pinned two-sign.
- [x] 6.4 **Predicates read per-finding construction facts.** *(DONE 2026-10-12; `finding_code`
      Detective-COMPLETE 112/112; the must-not still holds; `dispatch_undeclared` reachable only
      with several candidates.)* Each requirement names the KIND of
      construction it selects from; `_one_finding` reads the study's `Interstice` records of that
      kind from relations — none → `subject_unconstructed`, read and never hardcoded; one → its
      two indices; several → `dispatch_undeclared`, the selection rule being the founder's (4.1).
      `finding_code` takes the candidate count in place of a boolean. Verify the must-not
      `test_a_global_construction_count_never_supplies_a_subject` still holds and the new code is
      reachable only with several candidates.
- [x] 6.5 **A consumed event is recorded by the consumer.** *(DONE 2026-10-12: on the real run
      every producer but `output` has a consumer and no consumer lacks a producer;
      `tests/knee/test_pipeline_composition.py`.)* `<producer>.consumed_by.<consumer>`,
      recorded inside the consuming stage at the point of reading, never by the route after
      production; the route records only the two pinned multi-exit readers (`read_study`,
      `read_regime`). A composition test over the synthetic corpus checks every `<stage>.produced`
      has a consumer event. Verify by the real run's ledger sources.
- [x] 6.6 **The attendance roster.** *(DONE 2026-10-12; saved in the receipt.)* `StudyRun.attendance` names every stage with its own code
      (the conclave reading: coverage is a population, not a high-water mark); `reached` stays as
      the telemetry scalar it is. Saved in the receipt.
- [ ] 6.7 **The bundles stage, first increment (§3).** *(CANDIDATE 2026-10-12, open under the
      candidate rule: built, wired, 51 profiles on the real study, drawn; `stage_code` and
      `bank_status_code` Detective-COMPLETE; `count_by_extent` Detective-UNGATEABLE (engine defect
      reported, no retry, no waiver), its CrossHair blocked by the audit wall. Body by a scoped
      Sonnet builder, read whole by the lead. The seeds are not yet in the `came_out` bank, see
      3.2.)* Dispatch answer, recorded first: the
      subject kind is the indexed extent of the selected native plane, which ownership's solitary
      member resolved — a relational fact, not a kind-label, so the task proceeds. Banks this
      build can write, each naming its source stage: the place's own reading per seated lens
      member (counts over the digit codes at the object's places); the members' standing; how
      the object came out (its edge kinds and its profile trace codes); and through-plane support
      per other acquisition (counts over `SLAB_CODES`, which is the slab rule's first consumer).
      Banks it cannot write are carried as `unavailable` with the reason, never as zeros. One
      plane read, recorded. Verify a zero count can only mean a reading was made and found
      nothing, and that `slabs.py` is reached from the route.
- [x] 6.8 **The output stage, first increment (4.2).** *(DONE 2026-10-12; `output_code`
      Detective-COMPLETE and CrossHair-confirmed; the bijection test holds; no row written.)* The declared index-to-column table, checked
      as a bijection onto `LABELS`; the companion record on every run; submission rows refused
      with `projection_undeclared` while the value is undeclared (founder: "that should resolve
      experientially"). Verify a submission without its companion is refused, and that no row is
      written today.
- [x] 6.9 **Every stage draws.** *(DONE 2026-10-12: 12 drawn, 0 not drawn, no stage without a
      drawer on the real study; the study stage retains its walk and per-slice codes.
      `panels()`/`over()` in `pictures/collapse.py` untouched, the founder's ruling.)* `collapse` from the saved regime key and squint, leaving
      `pictures/collapse.py`'s `panels()` and `over()` untouched pending the founder's ruling on
      the leg and profile panels; `study` from a saved walk through the stack with per-slice codes
      the stage records; `vectors` and `output` from their records; `DRAWINGS` files
      `object_packet` under `objects`, where its values come from, so `knee.pictures.study` is
      the study stage's one drawer. Verify `route_stages_without_a_drawer` is empty.
- [x] 6.10 **The record corrections of HANDOFF §8.** *(DONE 2026-10-12.)* `OBJECT_MODEL.md` and `PIPELINE_AS_OBJECT.md`
      no longer say the four diagnosis packages are deferred "by his ruling"; the universal
      relational clause is scoped to relation-subject findings by his own Fracture sentence;
      `places.json` drops `runs_on_import`; `wiring-gaps-fable.md` Q2 is annotated struck;
      `WIRING_GAPS.md` is marked superseded with its false tooling claim corrected.
- [x] 6.11 **The real run, the gate, the profile.** *(DONE 2026-10-12; the run, the gate log and
      the profile are named in `measurements/composition-repair-20261012.md`; budgets undeclared.)* `just analyze-objects` on the demonstration
      study; `just gate`; `just profile-tree` on the one command; counted work per stage read
      from the ledger and reported; budgets left undeclared because a budget is a bar.

## 7. The remaining gaps — declared 2026-10-12 from the computed list, under the founder's instruction

The founder, 2026-10-12: *"The purpose of this session is to simply take that which already exists
and is fully in-line with the thesis and design and simply make it a functional, production system,
in the manner I had specified, using the tooling that I specified."* And: *"Reconcile the
documentation/record drift, then, with detective two-sign and vulture and anything else that would
be useful, start up some sonnet sub-agents (or workflow, if that helps), and knock out the remaining
gaps."* The list below is the lead's computed inventory of that session (`just places`, both vulture
scopes, Detective's certificates, a first LintGate run, deptry, ty), declared before any code. Each
item is engineering on work that exists; none builds new design content, which stays with §1–§5 and
the other changes. The delegation contract at the top of this file governs every packet.

- [ ] 7.1 **Every probe becomes production.** Founder: *"I don't run ANY by hand. ALL probes are
      supposed to be part of production."* For each of the five render probes `just places`
      reports unwired (`seam`, `structure`, `objects`, `axial`, `look`): establish from a whole
      reading what it computes and which stage's record holds, or would hold, that quantity. Where
      the route already computes it, the probe's drawing joins `DRAWINGS` over the saved record.
      Where it does not, the measurement moves into the stage as a unit with its contract and pure
      decisions, is retained in the record, and is drawn by a renderer that only arranges. `seam`
      and `structure` compute the leg, the superior–inferior axis and profile, and the seam that
      `pictures/collapse.py`'s `panels()` and `over()` ask for, so they come first and those two
      functions get their caller. A probe whose work is in production moves to `archive/workbench/`
      under its path, the 0.6 precedent, and is never deleted. Verify by `just places` (the unwired
      count falls by the probe) and by the real run's gallery.
- [ ] 7.1a **The eight measurement probes** (`corpus_shape`, `noise_floor`, `regime_key`,
      `regime_run`, `geometry_spread`, `object_toolkit_geometry`, `machinery_facts`, `reports`):
      the same rule. The corpus-wide tabulations among them become a corpus summary the writer
      computes from the per-study records when the one command runs without `--uid`, saved in the
      receipt and drawn; a probe that only re-runs a stage over the corpus is superseded by that
      run and archived.
- [ ] 7.2 **Every production name vulture reports without a production caller gets its consumer, or
      its archive.** The list, computed 2026-10-12 over `src workbench scripts`: `is_silence`,
      `coil_count`, `signal_squared`, `was_measured`, `gap_fraction`, `carries_prominence`, `over`,
      `parted_more_by`, `route_state`, `decoder_plugins`, `split_uids`, `READ_STANDINGS`,
      `elapsed_ns`, `trace_points_rc`, `seed_quantile`, `LOCAL_ROOT`, `KAGGLE_ROOT`, the regime
      constants `QUIET_SHARE` and `GAUSSIAN_SPREAD_RATIO`, and the four names §6 itself added
      without a consumer: `STAGES`, `KINDS`, `COMPARISONS`, `SLICE_CODES`. Each is resolved by a
      whole reading and a reference query into one of three: a consumer owed, which is built; a
      dynamic consumer vulture cannot see (a field the writer enumerates, a name Hamilton resolves),
      recorded in a vulture allowlist that names the reason beside the name; or dead, archived under
      its path and never silently deleted. Founder's law on the first class: *"the lack of a
      consumer IS the fucking problem."* Verify by both vulture scopes in the gate.
- [ ] 7.3 **The compute contracts are read by a tool.** Every `ComputeContract` is declared on a
      kernel and read by nothing. The receipt carries each kernel's contract beside the ledger's
      counted work for that run, so the declared `work` and the measured count sit in one record
      where a reader can compare them. A budget stays undeclared: it is a bar.
- [ ] 7.4 **The real run's composition is a verb.** The producer/consumer check the lead ran with a
      scratch probe becomes `scripts/composition_check.py <run>` and `just composition <run>`: every
      `<stage>.produced` has a consumer, no consumer lacks a producer, and the conversation precedes
      ownership, read from the receipt's ledger. Advisory in the gate like `places`; run after every
      real run and its output kept with the measurement record.
- [ ] 7.5 **6.3a built.** The edge-to-piece translation (the edge point minus half the sign of its
      normal, exact) so `read_pairings` runs on the concurrent and conditional parses: one unit, its
      contract, its pure decision pinned two-sign; the relations record carries one pairing reading
      per seated parse; drawn beside the solitary pairing.
- [ ] 7.6 **The unconverged readers converge.** `walk_indices`, `conversed_parses`,
      `read_ownership_members`, `read_pairings`, `read_bundles`, `read_findings`, `read_output` and
      `submission_rows` have no certificate. `just detective converge` each, every survivor judged by
      the lead and never by a builder; the standing recorded here per digest. `read_ownership`'s
      certificate is UNGATEABLE (`mutant_construction_failed`), which the record had not said.
- [ ] 7.7 **LintGate's first run answered.** Run 2026-10-12: 8 blocking, 695 warnings, coherence
      "systemic". The blockers: `scripts/places.py::main` (complexity 32) and
      `lenses/places.py::read_member` (31) decomposed with behaviour unchanged, which the tests,
      the pins and the receipt digests hold; the writer's four `attr-defined` findings traced to
      their cause and fixed; `RegimeKey` and `BoundaryExchange` at 23 attributes each recorded as
      the design's record shapes and not split for a style limit. The writer's one 585-line `main`
      decomposed into per-stage record functions with the receipt byte-identical on the synthetic
      corpus. The warnings read whole and triaged into this list or a reasoned allowlist.
- [ ] 7.8 **deptry and ty.** `pandas` and `SimpleITK` are declared and imported by nothing; removed
      from the declared dependencies with `uv lock`, under the global repo-hygiene reference, if
      7.1 and 7.2 leave no production import of either. The two `src` ty diagnostics fixed; the
      three in tests read and either fixed or recorded with their reason.
- [ ] 7.9 **The profile read.** The `just profile-tree` output of the one command read whole for
      work repeated across stages, the audit's own class of defect; each instance found becomes a
      7.x task here; counted work per stage reported from the ledger beside it.

## Beside this change, unparked rather than duplicated

**Borders — §6 — is `object-resolution-toolkit` tasks 3.8–3.12**, unparked 2026-10-12 on the argument
that if no pipeline record ever carries an anatomical name and §6's precondition were an anatomical
name, §6 could never run *in principle*. Its "role" is the structural role a lens assigns. It is
sequenced after §1, does not block §2–§4, and is **not delegable**: its own task text requires the
support contract specified before implementation.

Readings: `docs/chapters/02-collapse/readings/breadth-first-mvp-{codex,fable}.md`,
`faithfulness-{codex,fable}.md`, `pipeline-as-object-{codex,fable}.md`; the lead's own readings,
written before each, in `workbench/consults/`.
