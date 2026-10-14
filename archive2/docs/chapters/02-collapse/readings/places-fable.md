# Consult

Conventions: **[text]** = follows from the stated mechanism. **[mine]** = my inference. **undetermined** = this text does not fix it.

## 1. Does the registry earn its keep?

**[text]** Detectors 1 and 2 close existence-level drift in both directions: a module cannot appear or vanish without the check going red. That is sufficient for *membership*.

**[text]** It is not sufficient for *content*, and the plan's own fields show which content is unchecked:

- *role in one sentence* — nothing observable corresponds to it. No detector reads it. By the lead's own criterion ("documents lose"), this field is a document stored inside a command.
- *consumes/produces by named record* — the compute contract per kernel already declares `reads`/`writes`. The registry would be a second declaration of the same fact. None of the six detectors compares registry consumes/produces against contract reads/writes. **Provable gap:** two declarations of one fact with no check across them is exactly the "second source of truth" the question fears, and the plan as written creates it.
- *stage* — checkable only if the route exposes, observably, which modules each stage calls. **undetermined** whether it does; the route reports stage *state*, not stage *membership*.
- *renderer* — detector 6 checks that a stage *has* a picture, not that the registry's named renderer is the one drawing it. The field can name a renderer that no longer runs and stay green.

**[mine]** What rots first is whatever is declared but never compared. Of the four fields, one (role) is uncomparable by construction, two (consumes/produces, renderer) have an existing or possible observable but no detector wired to it, and one (stage) depends on an undetermined route property. The membership check will keep the registry *complete*; nothing in the plan keeps it *true*.

**Question:** is the role sentence meant to be read by any check, ever? If not, what distinguishes it from the loop that was "written down three times"?

## 2. Is "unreached from the entry point" the right island test?

**[text]** Granularity mismatch, provable from the author's own words: the failure mode is "a mountain of code in one arbitrary spot, **one function at a time**." Detector 3 operates per *module*. A 2,000-line function inside a module the route imports is reached and passes. The project already has a **function-level** dependency graph over the production functions; detector 3 is coarser than an existing tool.

**Wrongly flags [text + mine]:**
- Reference implementations named in compute contracts — by definition reached from the proof gate, not the route.
- Modules belonging to a stage the route reports `not_built` — unwired, hence unreached, hence red. Per the thesis this *is* an island, but it is red for the whole period during which a stage is being built, and the gate blocks commits. **[mine]** The cheapest way to go green is to declare the module *workbench*; the gate then teaches people to misdeclare place, which is the registry rotting by hand.
- The dev-only graph, planning tool, mutation checker: "beside the route" is a declared escape, so these pass only because they are declared out — the detector doesn't decide, the declaration does.

**Wrongly passes [mine, since static vs dynamic reachability is undetermined]:** if reachability is import-reachability, a module imported for one constant passes whole; a branch never taken on real data passes; a module reached whose output goes nowhere passes detector 3 (detector 4 may catch it only if the output is a *named record*).

**Question:** why module-level, when the project already has the function-level graph?

## 3. Is "same `writes`" a real recomputation detector?

**[text]** It detects one case: two kernel authors who independently chose the same record name. Provable miss from the quote: the failure mode is values "**completely forgotten about**." A forgotten value is not re-declared under the same name — the second author did not know the first name existed. The detector catches recomputation that happened *without* forgetting, which is the rare case.

**[text]** Also misses anything without a compute contract (non-kernel modules), and anything computed inline rather than as a declared `writes`.

**[text]** The second clause — "two kernels reading the same source per study" — flags legitimate fan-out (a raw volume read by two stages for different purposes). It is a proxy with structural false positives. **undetermined** what "source" means here.

**[mine]** Detector 5 is the only one of the six that compares *declaration to declaration*; the other five compare observed to declared. The project already holds an observed signal: the function-level graph where "a value nothing consumes shows as dangling." A value computed in stage N and re-derived in stage N+1 presents, in that graph, as a dangling output at N. That signal exists today, costs nothing new, and catches the *forgotten* case the name-collision test cannot.

**Question:** was the dangling-value report consulted when the recomputation that motivates this plan was found? If it was dangling there, detector 5 is redundant; if it was not, what did it look like?

## 4. §6 ordering error — structural or reader-only?

**[text]** The project's own `built` rule does not catch it: a stage is `built` when it has run on real data through the real entry point. Refinement on roleless territories can run on real data. The rule tests execution, not input provenance. Provable.

**[text]** None of the six detectors is a stage-order or input-provenance check.

**[mine]** It becomes structural iff three things hold: (a) *role* is a named record produced by some kernel's `writes`; (b) the refinement kernel's contract declares that record in `reads`; (c) a check matches declared reads to existing writes. Then refinement-before-role shows as "consumes a record nothing produces." But (b) requires the contract author to already know §6 — a contract honestly written as `reads: {territory}` passes. The check can only enforce an ordering that has been declared somewhere observable. Whether stage contracts declare *required input records* is **undetermined**; if they do, the detector is one comparison away; if they don't, it is reader-only.

**Question:** is "role" a record in this project, or a property of one?

## 5. What is ceremony?

**[text]** The duplicated consumes/produces: every change to a kernel's `reads`/`writes` is made twice, and the mismatch is not among the six checks. Double entry, zero detection — that costs on every edit and catches nothing it would not catch from the compute contract alone.

**[mine]** Folder-level entries: nothing observes a folder except its membership; its "role" is its modules' roles. The role sentence (uncheckable). Registering workbench probes with stage and record declarations, when the workbench exists so that probes are cheap.

**[text]** The second half of detector 5 (same source read) will fire on correct fan-out; a detector that is routinely overridden stops being red and becomes a note, which the plan explicitly did not want.

## 6. What the registry should refuse

**[mine, using only the project's own existing homes for each]**

- Status (`built`/`partly`/`not_built`) — the route reports it live; a status field here rots on the first run.
- Compute facts (kind, language, allocation, work, parallel unit, proof gate) — the compute contract.
- Bars and thresholds — written down before the run, elsewhere.
- Stage definitions and order — the route.
- Renderer behaviour — the rule already says a renderer only arranges.
- The *why* — the thesis.
- Any field no detector reads.

**[text]** The lead's own stated criterion supplies the filter: what changed behaviour was a tool that answered back. A field the check cannot compare to something observed is a document inside the registry, and the project's record is that documents lose.

**Question:** should consumes/produces live in the registry at all, or should the registry name the kernel and let the compute contract remain the single declaration of what it reads and writes?