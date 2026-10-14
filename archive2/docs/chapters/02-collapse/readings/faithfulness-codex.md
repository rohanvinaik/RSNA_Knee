# Codex on the breadth-first scaffold's faithfulness

GPT-6.1 Sol at high effort, model-only home (no MCP servers), read-only, one turn, answering from
`workbench/consults/faithfulness-prompt-as-sent.md` alone — the same prompt Fable received. The
lead's own reading was written first and is in `workbench/consults/faithfulness-breadth-first.md`.

Its answer, verbatim:

```text
I treat the reported state and constraints as established **within this account**. I have not
inspected the implementation or pictures. The distinctions below are my reading, not a verdict on
the founder's design.

For **question 1**, twelve abstentions do not themselves establish that the pass misses 22:31. His
purpose is to make the hardware's visual output available for subsequent meaning assignment; it does
not require the hardware already to resolve the findings. A spatially registered ternary map can
serve that purpose without naming any tissue. Row counts can also supply evidence, provided the
founder can see which places contributed them. Conversely, an absence frame explains why evidence is
unavailable, but supplies no observation of the missing stage's subject.

My inference is that the pass could deliver the purpose, but its stated completion criterion does not
establish that it will. "One picture per stage" admits a run consisting largely of honest absence
frames. Whether §2 produces usable measurements on the selected study, and whether those
measurements remain inspectable through later stages, cannot be determined here.

If that gap occurs, the smallest change I can identify is to the **completion condition**, without
choosing a new design: §5 must present some actual computed observations, visibly attributable to
their locations in the study, for the founder to interpret. The specified lens map could already
satisfy that condition. Honest absence pictures would still document the unfinished breadth; they
would not count as the observations enabling meaning assignment. This requires neither anatomical
labels nor successful predicates.

There is also a scope error in your own reading: §12 being extra does **not** establish that the
unbuilt route stages are not omissions. The quoted passage excludes operations beyond recognition,
with tracking as its example. It does not exempt the listed recognition stages. Their temporary
incompleteness may be consistent with breadth-first construction; §12 is not the evidence for that
allowance.

For **question 2**, the supplied §6 explanation establishes a precondition for *role-conditioned
border refinement*. It does not establish that every measurement of a territory requires an assigned
role. Computing a territory's measured profile could therefore precede identity assignment without
violating that passage. Indeed, such evidence could help the founder make the assignment later.

The distinction is what the profile asserts. A record saying, in effect, "these counts came from
these indexed places" need not admit an object. A record asserting "these places constitute this
object" has crossed into an assignment that the binding constraints currently forbid. Calling the
former "an object's profile" obscures that distinction, even if the arithmetic remains admissible.

I cannot determine whether §3 has valid membership information. The ownership stage is unavailable,
and the text does not establish whether the territories already supply the membership needed for the
proposed counts, or whether those counts require unresolved ownership. If they require it, the
specified unavailable status is the honest result. The question I would put back is: **what
established assignment licenses each place's inclusion in this bundle?** The answer determines
whether this is a provisional measurement record or an unsupported object assertion. §6 alone does
not decide it.

For **question 3**, I would distinguish a declared obligation from an observed fact, rather than
count registry fields. Your account establishes that several properties already have homes outside
the registry. Consequently, four registry fields versus fourteen requested properties does not prove
that ten properties are missing from the scaffold. It establishes a question about their coverage and
enforcement.

Intent, prohibited behavior, allowed dependencies, promised outputs, and required consumption belong
to declarations: inspecting code cannot establish what it *ought* to do. Actual imports, actual
consumers, executed work, allocations, rendering, and import-time behavior are observations to
compute. Some properties need both: a declared output contract and an observed output; a declared
reference relationship and a computed equivalence result; a required consumer and an observed
connection to it.

That is the line I infer: **declare the obligation; compute whether the implementation fulfills it**.
A registry can locate the authoritative contracts without copying their contents. Copying
interfaces, dependencies, and other observable facts into prose would introduce additional
representations that can disagree. Mechanical checks still need declarations for obligations they
cannot discover—especially intent and negative specification. They cannot replace those with
inference from whatever the implementation happens to do.

The reported six compute contracts do not establish how many contracts are missing: the text does not
identify every numeric kernel. They do establish that contract count alone cannot answer coverage.
The structural check must identify the relevant kernels and reference/twin pairs, then compare them
with the required declarations.

For **question 4**, the bounded mechanical check I can name is a **duplicate-computation provenance
check**. It would need to read the actual execution record through the production route, including:

- The operation's declared identity and every result-affecting input and parameter.
- Each execution's produced artifact identity.
- The downstream consumers and the artifacts they actually used.
- Any declared reason that repeated execution is required.

Those records can establish a concrete case: the same declared operation ran twice on equivalent
inputs, produced equivalent artifacts, and separate downstream stages consumed the separately
produced results. They can also establish successful sharing: one production event supplied several
consumers.

Two function calls alone would not prove the founder's named failure. Their parameters could differ,
or repetition could be intentional reference verification. Conversely, different functions could
repeat equivalent work. Detecting that latter case requires an established equivalence between the
operations; telemetry cannot discover arbitrary computational equivalence by itself.

Thus the check can mechanically catch repeated work **within its declared operation vocabulary and
recorded execution coverage**. I cannot claim it would catch every possible recomputation. With the
ledger off and unwired, the supplied account establishes that this runtime evidence is currently
unavailable. The check must report that missing coverage explicitly; an empty ledger cannot establish
that sharing succeeded.
```

## What the lead takes from it

**Its scope error finding is correct, and the lead's claim is withdrawn.** See the correction at the
head of `workbench/consults/faithfulness-breadth-first.md`.

**Where it and Fable agree, independently, from different routes — so this is evidence:**

1. **The weak point is §5's completion condition, not the design.** Codex: *"'One picture per stage'
   admits a run consisting largely of honest absence frames… §5 must present some actual computed
   observations, visibly attributable to their locations in the study."* Fable reached the same place
   through the enforcement mechanism: *"'a stage is not built until it renders' cannot distinguish"*
   a frame arranging study values from one arranging pipeline state, so the route will report
   `relations` as `built` while 22:31's purpose for it is unserved.
2. **§3's arithmetic is admissible; the word "object" is what is wrong.** Codex: *"Calling the former
   'an object's profile' obscures that distinction."* Fable: the record must carry *"the SUBJECT KIND
   it was keyed on"*, so a predicate abstains with "subject not resolved" rather than silently taking
   a territory for its subject.
3. **Declare obligations, compute facts.** Codex: *"declare the obligation; compute whether the
   implementation fulfills it. A registry can locate the authoritative contracts without copying
   their contents."* Fable: declare a property only where a disagreement would sometimes be resolved
   by changing the **code**; a property whose disagreement is always resolved by editing the
   declaration is a fact and should only be computed.

**Where each saw something the other did not:**

- **Codex only:** the §12 scope error above. And — load-bearing for task 0.3b and for any recompute
  check — *"repetition could be intentional reference verification."* The reference/twin SAME harness
  computes the same thing twice **on purpose**, so a naive duplicate-computation check would report
  the project's own correctness machinery as the defect. Any such check must carry a declared reason
  that repeated execution is required.
- **Codex only:** *"the reported six compute contracts do not establish how many contracts are
  missing: the text does not identify every numeric kernel."* The lead quoted a numerator with no
  denominator. The structural check has to enumerate the kernels and reference/twin pairs first.
- **Fable only:** tasks 1.2 and 1.3 contradict each other on the absence vocabulary — 1.2's three
  silences are all about an input, 1.3's shells need a silence about the stage's own design. The
  `stage-totality` spec says "at least three", so a fourth kind is already permitted.
- **Fable only:** `role` has no disagreement class, so closing the unwritten count to 0 of 83 left
  the registry's largest field entirely unchecked. Codex reframed the same area as a coverage and
  enforcement question rather than a field count.

**The question both put back to the founder, in different words:** what licenses a place's inclusion
in a bundle, and does an interstice exist between two index-numbered territories or only between two
role-bearing objects? Neither reader would answer it, and neither should.
