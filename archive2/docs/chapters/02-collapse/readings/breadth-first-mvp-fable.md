# Consult — breadth-first MVP

Conventions: **[stated]** = taken from the text or figure as given. **[mine]** = my inference. **undetermined** = the text does not fix it.

---

## 1. Is "total over a missing predecessor" sufficient?

**[stated]** Totality gives: a stage runs when its input is absent and returns a named code. **[mine]** That makes stages *wireable in any order*. It does not make them *buildable in any order*, because a stage is built against the *shape* of its predecessor's record, and abstention only covers a predecessor that is absent, not one whose record shape is unsettled. Two concrete cases:

**(a) objects → relations — a real ordering dependency.**
- **[stated]** Objects today returns an *unordered set of directed interface points*; the MVP table says objects will add *ordered contour chains*, which are not built. Relations' MVP record is "per touching pair … divide sites, relief, the places between — all already measured."
- **[stated]** A divide exists only where the interior is connected across; the interior excludes dark. So "touching pair" means watershed-adjacent. The figure's third column plots exactly those pairs (36 / 12 / 9 / 20 / 9 read pairs across the five series), and for them relief and pass width are indeed measured.
- **[stated]** The thesis's interstice is "constructed, not detected — it exists the moment its two bounding objects do." **[mine]** The pairs the thesis cares about are bounded *across dark*, i.e. precisely the pairs that are *not* touching under the current definition. For those, "the places between" is not measured: 68–92% of interfaces have dark across them, only 22–41% bracketed anything, and the record does not (per the text) say *which* territory a bracketed profile reached — the across-typing is `low_signal`, not a peer identity. Whether a bracketed profile records its far-side territory: **undetermined**.
- Consequence [mine]: relations built now against unordered points and watching-only touching pairs must be rebuilt when chains and dark-bounded pairing arrive. Abstention cannot paper this over because it is not an absence; it is a contract that will change under relations' feet. The record shape of objects (chains yes/no; whether a bracket carries a far-side identity) must be frozen before relations is specified, even if relations' code is written later.

**(b) the absent-code vocabulary itself — a dependency on no stage.**
[mine] "Total over a missing predecessor" requires every stage to distinguish at least: predecessor *absent*, predecessor *present but empty* (e.g. zero territories), predecessor *present and this item unread*. If each stage coins its own codes, the dependency graph passes vacuously while the codes do not compose. The text does not say whether a shared code vocabulary exists: **undetermined**. If it does not, that one artefact has a hard ordering before every stage.

Pairs where totality *is* sufficient [mine]: lenses ↔ objects (objects uses the background split, not lenses, per the text — whether the background split *is* a lens is undetermined); relations → ownership (places outside any territory or interstice are honestly `unassigned`); anything → predicates/output (abstain).

---

## 2. Is an all-abstaining predicates/output pair honest?

**[stated]** Law: a missing reading is silence, never a negative. **[stated]** The output MVP writes "twelve confidences per study in the submission's schema, all at the abstention value." The abstention value itself: **undetermined**.

**[mine]** The predicates stage is honest as described: a named decision returning `abstained` with a reason is silence in the project's own vocabulary.

The output stage is the one place the epistemology is forcibly violated by an external schema: a confidence column cannot carry silence; it carries a number, and a number in a submission-shaped file *will be read as a prediction* by anything that consumes it. That is the false-artefact risk — not that the file exists, but that the file alone cannot say it is abstaining. Three conditions make it honest, each a contract rather than advice:

1. The abstention constant is declared in the output spec *before* the run, as a named value, and the contract forbids it being chosen by reference to any score or label. (If it were set to whatever minimises the metric, that is "calibrate on the data" in the plan's own forbidden list.) What value the schema or sample submission prescribes, if any: **undetermined**.
2. The output stage writes, alongside the submission file, a record carrying the twelve named codes per study and the constant used, so the submission file is derivable from the codes and never the reverse.
3. The ledger entry for the run records that every row is `abstained`; any score computed on the file is logged as a score of the constant, not of a pipeline.

With those, "proves every wire" holds. Without (1) and (2), the file is a constant wearing a prediction's shape.

A smaller provable point [mine]: "validated against the sample submission" validates shape only. It cannot certify that the numbers mean abstention; only (2) can.

---

## 3. Bundles — which banks are honestly writable today?

Banks named: voxel · 16×16 neighbourhood · lens · plate · dome link · ring · lenses' conversation · how the object came out. What the pipeline measures today [stated]: per-place intensity on one 2D middle slice; a background split; distance transform; watershed territories with prominence seeds; per directed interface point two typings (across / found) and a position where they agree; per-series noise scalars (consumed by nothing in objects).

| bank | today | basis |
|---|---|---|
| voxel | **writable, with a caveat** | Per-place intensity inside a territory exists; row counts over intensity bins are arithmetic on it. Caveat [mine]: it is one 2D slice, so the bank is a *pixel* bank; calling it "voxel" without the ledger saying `planes: 1` would misreport dimensionality. |
| 16×16 neighbourhood | **not writable from existing measurements** | Nothing in the text computes any neighbourhood statistic. [mine] It is computable deterministically without assigning meaning, but it is not "already measured"; writing it means building a unit, not reading a value. |
| lens | **fabrication today** | Lenses stage is `not_built`. Becomes writable the moment the ternary-digit MVP exists (counts of digit 0/1/2 per territory). |
| plate | **not writable; undetermined what it is** | The text never defines "plate". [mine] If it is a cortex-like structure, writing it requires deciding "a reading means a cortex," which is exactly what no stage may do now. |
| dome link | **not writable; undetermined** | Undefined in the text. |
| ring | **undetermined as a bank; the loop census is writable** | [stated] Per territory the boundary census exists — edges by across-typing and found-typing, the share bracketed (the figure's second column). [mine] Whether "ring" *is* that census is not given; writing the census under the name `ring` would assert an equivalence the founder has not made. Write it under the name the stage already uses (loop census) and leave `ring` absent-coded. |
| lenses' conversation | **fabrication** | Needs ≥2 lenses; none built. |
| how the object came out | **writable** | This is the provenance already in hand: seed/prominence, number of edges, each edge's two typings, count measured vs watershed-decided (e.g. the 38-edge / 0-measurement territory), frame contact. |

Discipline point [mine]: the count table must list every bank, with the unwritable ones as absent-coded rows (not zeros, not omitted) — the same law as everywhere else.

---

## 4. Must the rename precede everything?

**[stated]** The route's names are superseded; the settled list is study · field · lenses · objects · relations · ownership · bundles · predicates · output; correcting the route is declared, not done. **[stated]** Each MVP unit must be wired into the production route with a dependency graph showing nothing dangling.

**[mine]** Diff of the two lists:
- Common: study, lenses, objects, relations, predicates, output.
- New in settled: field, ownership, bundles.
- Only in old: collapse (*partly built*), loop, candidates, cleanup, vectors, every_object.

So the rename need not precede everything, but **one mapping must precede the first wiring**: where the already-built `collapse` code goes, and whether `field` is its successor or a different thing. The text does not say: **undetermined**. Without it, the "nothing dangling" check either fails (new stage has no slot) or passes vacuously (old slot kept alive as a stub). The remaining five old names (loop, candidates, cleanup, vectors, every_object) are `not_built` with no renderer; removing them costs nothing but the table edit.

What breaks if built in parallel without that mapping: two stages wired against two vocabularies; a dependency graph that cannot be read as one route. What breaks if the rename is done first in full: only risk is renaming `collapse` to `field` by assumption, which would be a stage boundary decision made without the founder's ruling. The cheap safe order is: write the old→settled mapping as a spec (including the `collapse` ruling), then build wide.

---

## 5. Where does this plan hide a week?

**Relations**, on the strength of its own description: "the constructed interstice … the places between — *all already measured*."

**[stated]** What is measured is relief and pass between *touching* pairs — pairs sharing a watershed divide — and the figure's third column is that, for 36/12/9/20/9 pairs. **[stated]** The picture promised is "the interstice drawn between two territories." **[stated]** The thesis's interstice is bounded by two objects and exists when they do; the interior excludes dark, so two territories separated by dark are *not* a touching pair.

**[mine]** Therefore the "non-stupid image" for the pairs that matter (the ones with a gap between them) needs, in order:
1. ordered contour chains (objects, not built — and ordering an unordered point set with three-territory junctions, frame clipping, and the isolated cyan specks visible in every left-column panel is several named decisions, each carrying the full two-sign / mutation / symbolic-contract discipline);
2. a rule for which bracketed profiles across dark belong to which far-side territory (the far-side identity of a bracket: undetermined whether recorded);
3. a region construction between two chains from a 22–41% subset of bracketed points.

None of that is "already measured"; it is three units, and the discipline is per unit. Ownership then inherits this: with no dark-bounded interstices, every dark place is `unassigned`, which is honest but means ownership's picture is just the watershed plus black until relations lands — so the week is borrowed by two stages.

Second candidate, lower [mine]: the objects stage's "ordered contour chains" line item is the same week counted under a different name. Lenses, by contrast, is cheap as described — the tercile edges already exist in the regime key.

---

## 6. What the MVP must refuse — as forbiddable contract clauses

Each written so a contract can reject the code, not as counsel.

1. **Lenses.** The `normalisation` field is mandatory and its only admissible value in this spec is `none`; any spatially varying edge is a contract violation. The two edges must be computed from the series' own population; a literal edge is forbidden.
2. **Objects.** A territory record carries an index and provenance only; the record schema has no field whose type is an anatomical name, and no field of the form `is_<anything>`. No territory may be dropped by a size, intensity or edge-count filter; a doubtful territory is coded, not removed. An interface position may be set only where the across-typing and found-typing agree (already law; keep it symbolic-checked). The record must declare `planes: 1`.
3. **Relations.** An interstice may be constructed only for a pair whose bounding relation the objects record asserts; the stage may not infer a bounding pair across dark by proximity or by nearest territory. Relief, pass and "places between" are absent-coded when unread, never 0 — the figure already says "an unread pair is absent, never zero"; make it a contract, not a title.
4. **Ownership.** The residual is a counted quantity; a residual of 0 while any place is unassigned is a violation. No place may be assigned by a default (nearest, largest, background-unless-proven).
5. **Bundles.** A bank row may be written only from a quantity some stage's record contains; every bank in the thesis's list appears, absent ones as coded rows, and a bank may not be renamed to an existing measurement (`ring` ≠ loop census until ruled). The dimensionality of the voxel bank is recorded.
6. **Predicates.** In this spec the decision's codomain is `{abstained} × reason`; any other code is a violation. The stage's inputs exclude any label, score or submission file.
7. **Output.** The abstention constant is a spec-declared argument, not a runtime choice; the contract forbids any input path from a label or score to the output stage. The submission file may not be written unless the companion code record is written in the same run.
8. **Everywhere.** No bar is a literal in a stage body; every bar is an argument (already law). No stage consumes a noise figure it has not declared. A renderer computes nothing it did not receive (already law). Nothing in any record or picture names anatomy or asserts that a reading *is* a cortex, a plate, a joint — those words are reserved for the founder's ruling on a rendered image.

---

One question back, since it conditions answers 1 and 5: **does a bracketed profile cast across dark record the territory it reached on the far side?** If yes, dark-bounded pairing is a lookup and the hidden week shrinks; if no, it is a construction. The text does not say.