# Classical-AI training experimental notebook

This is the research record of the local bootstrap and Society of Mind training loop. The
author's design remains in the conversation documents and CLASSICAL_AI_BUILD_DESIGN. The sole
current work queue remains FULL_BUILD_PLAN §13's packet. This notebook records experiments and
their evidence; it does not create a second queue or change the learning mechanism.

Rohan's requested experimental unit, 2026-10-22: try the current society on new studies, compare
diagnoses with independent truth where available, inspect uncertainties and mistakes, retain
warranted teaching, then try the enlarged memory on the next studies. Capture how discrimination,
uncertainty and useful procedures change at each iteration.

His [literal clarification about informative disagreement](conversations/2026-10-22-bootstrap-iteration-and-informative-disagreement.md)
governs candidate review: review the strongest unresolved matches across anatomical and diagnostic
categories, including conflicting ones. A K-line retains the contextual meaning of a joint measured
pattern; its disagreement is not discarded to make the signals agree. Record the competing
assertions, what their measurements and scopes actually establish, the independently reviewed
interpretation and the agency consumer that uses it. A final signed name plus an audit note alone
does not establish a learned disagreement-interpretation mechanism. Preserve useful measured
patterns while later agency training learns from the retained interpretations.

## Experiment register

| Experiment | Population and purpose | Memory tested | Evidence |
|---|---|---|---|
| [001 — first 58-study readback](experiments/training/001-first-58-study-readback.md) | 58 labelled teaching studies; 696 condition questions; readback after reviewed visual teaching | Reviewed 922-case memory, `97e7aede…` | Independently recounted saved findings, exact per-condition ordering and source-pinned row ledger |
| [002 — next fresh SSD wave](experiments/training/002-next-fresh-ssd-wave.md) | 20 fresh studies; 148 independently report-backed condition calls and 92 unavailable truths | Clinical/procedure child, 952 case records, `c03785b1…` | Completed two-machine inference, per-condition outcomes, 240-row ledger and subsequent signed teaching |
| [003 — forty-study paired learning](experiments/training/003-forty-study-paired-learning.md) | Same40 fresh studies before/after teaching;312 signed report calls and168 unknowns | Frozen993-case `ef68a24b…` versus1,005-case `1feeee1d…` | Actual480 paired transitions, per-condition discrimination, gains and regressions; subsequent1,061-case teaching child recorded separately |

[004 — three-stage navigation pilot](experiments/training/004-three-stage-navigation-pilot.md) records specialist → frozen-specialist orchestrator → joint-refinement training: the original60-study pilot, the later118-row dataset including58 official teaching studies, separate teacher/validation replays, consumer repairs and the interrupted fresh58-study check. The author’s wind-down is recorded in its closeout. This parameter learning is distinct from signed-case growth; neither training fit nor a partial run is transfer validation.

## What every completed iteration records

1. **Question and intervention.** What this round tests; the actual teaching or code changes since
   its parent; which parts are held fixed. Record hypotheses as hypotheses and conclusions as
   conclusions. A post-run explanation is not a preregistered prediction.
2. **Population.** Exact study UIDs and selection method; number of distinct studies; available
   series/views; source inventory and extraction-completeness checks; teaching/validation role.
   Twelve conditions in one study are correlated questions, not twelve independent patients.
   Views of the same object and multiple bundles of that view are not independent patients either.
3. **Memory and implementation.** Parent and tested-child manifest hashes, revisions, case kinds,
   signed identity/censor records, procedure experiences, preparation cache, actual runtime code
   and environment pins, command, machine, workers and declared budgets. When an execution pin was
   not captured, say so; a hash measured later identifies inspected source, not proven runtime code.
4. **Independent teaching and truth.** Official numeric label or exact report sentence and report
   digest; actual reviewer; question, view, site and diagnostic scope. Separate a confirmed object
   identity from a study-wide diagnosis. A recalled answer is not independent confirmation of itself.
   Missing truth stays unavailable. A report's silence does not teach normality. Preserve the
   author's separate rule for the fully labelled 58: correctly identified, unimplicated objects can
   supply normal presentations.
5. **Results for each of the twelve conditions.** Label-positive and label-negative denominators;
   identified / abstained / wrong on each side; false-positive and false-negative counts; exact
   pairwise ranking AUC including ties; positive and negative ranking-value distributions. These
   emitted values are ranking readouts, not calibrated patient probabilities. Categorical decisions
   retain their balanced-ternary meaning: absent −1, unresolved 0, present +1. Healthy physiological
   zero and signed physical deviations remain their own representational meanings.
6. **Residual and visual evidence.** Which actual studies/questions remain wrong or open; their
   support addresses, identity decisions, named HDC banks/differences, opposing cases, requested
   looks and source pictures. A proposed box is not certified tissue. Record the reviewer's actual
   call, its reason, any usable partial knowledge and genuine unresolved questions separately.
7. **What was learned.** New positive presentations, scoped negative precedents, warranted
   censors/splits and contextual procedure memories, each linked to its episode and immutable child.
   A checked procedure may be correct, wrong, or leave its question open. Retention alone does not
   demonstrate that a future action changed; record the actual consuming agency and its outcome.
8. **Compute and failures.** Measured run duration, workload, study completion, bounded looks,
   full-anatomy count, memory measurement and what that measurement covers; timeouts, source/input
   changes, refused publications and retries. Preserve failed attempts. Never turn an unfinished
   or unexamined study into a negative answer.
9. **Next comparison.** Publish one child from the accepted parent, preserving all signed stores
   and lineage. Record the next test's population and teaching relationship. All useful clear
   examples may teach; no arbitrary seed quota or score threshold is introduced by this notebook.

## How successive entries are compared

Keep three different readings visible:

- **Teaching-set readback:** the memory can include the queried study. This tests whether the
  hand-defined reference material is usable by the running agencies.
- **Whole-study-excluded check:** the queried study's positive, negative, configuration, censor
  and procedure teaching is removed through the actual memory-view consumers. Record the exclusion
  evidence; do not infer exclusion from an experiment's name.
- **Fresh-study transfer:** the study supplied no teaching of any kind to the frozen tested parent.
  Pin the all-source exclusion list. If it teaches the child after review, its later readback is
  recorded as readback, while the next fresh batch tests transfer again.

On a fixed cohort, align results by `(StudyInstanceUID, condition)` and preserve the full transition
table: uncertain→correct, uncertain→wrong, wrong→correct, correct→wrong, decisive→uncertain, and
unchanged states. Show the per-condition AUC change and ranking shifts on those same rows. State any
code, representation, truth or protocol change alongside the memory change; a bundled intervention
does not isolate the effect of one added case or censor.

Across different fresh batches, show their class counts and distributions side by side. A numerical
change across different populations alone does not identify a learning effect. If a paired rerun is
useful, freeze its population, truth, implementation and reading protocol, and vary the declared
memory only. Do not hold up normal teaching rounds while waiting for a perfect experiment.

There is no single aggregate score replacing the twelve questions. Ranking, decisive correctness,
uncertainty, coverage and work are separate observations. A small number of correct decisive calls
is reported with its denominator. No zero-error or clinical-validation claim follows from this
bootstrap notebook.

## Entry and artifact discipline

Each experiment has a numbered Markdown entry, a machine-readable measured result and a row-level
ledger linked from that entry. Keep exact input/output hashes and the original run immutable.
Correct an interpretation in a dated addendum; preserve what was originally observed. Append the
next entry rather than replacing a previous measurement with the latest one. Link complete reports
and actual images at their existing retained paths; do not duplicate or truncate their evidence.

Record experiments while running when possible. Entry 001 was registered after its result existed;
entry 002 was registered during inference. Neither is described as prospectively preregistered.

## Reproducible recorder for completed labelled runs

`scripts/record_squint_experiment.py` reads the saved run, reconciles its actual submission values
with its retained findings, verifies the supplied memory bytes, and writes a fresh `report.json`,
`rows.csv` and `report.md`. It runs no inference and changes no memory. Give each recording a new
output path:

```sh
PYTHONPATH=src .venv/bin/python scripts/record_squint_experiment.py \
  --run data/readings/grounded-teaching-20261022/r4-all58-infer \
  --labels data/raw/train.csv \
  --memory data/readings/grounded-teaching-20261022/growth-batch-20/gemini-visual-reviewed-r2/memory \
  --protocol teacher-readback \
  --output /absolute/new/iteration-record
```

For a later comparable run, append `--compare /absolute/existing/previous-record/report.json`.
The new JSON includes per-condition exact AUC changes, class-specific count/mean changes and full
assessment/outcome transition counts. A different cohort, protocol or truth-source digest returns
`incomparable` with its reasons, never a fabricated paired improvement. Recorded numerical changes
can include code, policy and readout effects; name those changes before attributing a gain to memory.

`--protocol whole-study-excluded` additionally executes the existing capacity reporter's complete
exclusion/preparation checks. Neither mode accepts an unexamined budget-stopped study as a semantic
abstention. Both preserve blank truth as unavailable, use actual serialized CSV decimals for ties,
and refuse an existing output directory.

This first recorder supports those two protocols. `fresh-transfer` explicitly refuses until supplied
with verified teacher-population evidence; the notebook's fresh-wave entry retains that evidence
and its separate report-truth measurement instead. Do not relabel a fresh run as teaching readback
or a teacher run as held-out to make a command accept it. No report call becomes an official numeric
label merely by being serialized for research analysis.

The final-source recorder was exercised on all 696 real questions and against itself, with zero
per-condition self-comparison deltas. Its 13 intent cases and the 20 existing capacity tests passed.
Full commands, source hashes and output digests are retained in
[the validation receipt](../data/readings/grounded-teaching-20261022/growth-batch-20/teacher-readback-analysis-r1/recorder-final-validation-r2.json).
This verifies the recorder; it is not a learning-benefit experiment or a full project gate.

### Entry template

```text
Experiment number / title / recorded date and timezone:
Registration timing / investigator and actual readers:
Question / hypothesis / intervention versus parent:
Population / exact UID list / selection / teaching relationship / exclusions:
Parent and tested memory paths, hashes, revisions and record-kind counts:
Execution code/environment pins / command / machine / workload and budgets:
Independent truth and annotation protocol / unavailable truth / diagnostic scope:
Per-condition measured results / exact row ledger / input-output artifact digests:
Comparable prior experiment / paired transitions / distribution and ordering changes:
Actual image/HDC residual observations / inference and alternatives still unresolved:
New teaching and learned procedures / accepted child / actual consumers:
Compute / incomplete work / refusals / deviations:
Conclusion supported by this experiment / next experiment:
Addenda with timestamp and superseded interpretation, if any:
```
