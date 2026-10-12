# Second reader's response

I take as **established** only what is quoted or stated in the brief: the six prompts, the route table, the registry fields, the §0–§5 change, the binding constraints, the parking of contour refinement, and your own reading. Everything else is marked as inference or as undeterminable from this text. I have run nothing and read nothing.

---

## 1. Does the breadth-first pass deliver 22:31's purpose, or only 22:38's letter?

**Established.** 22:31 asks for hardware "sufficient to enable us … to assign meaning to the tooling's output as annotated/processed visual data," and opens with "I will rate objects when shown as an actual image I can use for visual reasoning." 22:38 asks that "each step can put out a non-stupid image, even if it's not actually good quality," so that a baseline pipeline "actually EXISTS." §5 ends with the founder inspecting one image series over one study.

**Inferred.** Walk the nine stages against "something he can reason over visually":

- study, field, objects: render today, over real data. Meaning can be assigned.
- lenses (§2): a three-colour digit map per acquisition. Real processed data, meaning assignable.
- bundles (§3): row counts over banks per territory. Whether this *renders as a picture* is not stated in the brief; I cannot determine what §3's picture is. If it arranges counts per territory over the territory map, it is data he can reason over.
- relations, ownership (§1): "honest shells that run, return a named absence … and render a frame showing it." This is a picture of the pipeline's state, not of the knee.
- predicates, output (§4): twelve abstentions with reasons. Same.

So the pass is not uniformly "22:38's letter while missing 22:31." It delivers 22:31 for roughly five of nine stages and delivers only existence for four. Your sharper claim — "a picture of a named absence is not something meaning can be assigned to" — I would narrow: meaning about *the pipeline* can be assigned to it (he can see which stage is hollow and why), meaning about *the knee* cannot. 22:31's "annotated/processed visual data" is the second kind.

**The gap is real, and here is why it is specifically about relations and ownership.** The three silences in the §1 vocabulary are all silences about *inputs*: predecessor absent, predecessor present but empty, item unread. The §1 shells return "a named absence saying why their record shape is unsettled." That is not any of the three. It is a silence about the stage's own design. This is a small provable inconsistency in the plan text as given: either the vocabulary needs a fourth kind, or the shells will be forced to misuse one of the three (most likely "predecessor present but empty," which would be false — objects is present and non-empty). I flag it because it is also the diagnosis: relations is hollow not because anything upstream is missing but because a design decision has been deferred.

And the decision is the founder's, per the project description: "an interstice … is constructed, not detected — it exists the moment its two bounding objects do." If territories carrying index numbers count as "bounding objects" for this purpose, the gap between any two facing territories is constructible today from objects' output, with no anatomical name and no admission — which would make the §1 shell a choice not to compute something computable. If they do not count, then relations genuinely cannot run until roles exist, and the shell is honest. I cannot determine which from the text.

**Smallest change that closes the gap without assigning meaning on his behalf:** not code. It is to put that one question to the founder *before* §1 rather than discovering its answer at §5: *does an interstice exist between two index-numbered territories, or only between two role-bearing objects?* His answer settles the relations record shape, which is the stated reason the stage is a shell. If the answer is "yes," relations stops being a shell with no further design work from the lead. If "no," the §5 image series is what it is, and he has been told in advance that two frames will be pipeline-state frames, so the inspection is not a surprise. Either way no meaning is assigned by the machine, and §5 stays the point of the change.

A second, cheaper thing that does not close the gap but makes it measurable: the §5 deliverable could carry, per stage, whether its frame arranges values computed *from the study* or values computed *about the pipeline*. Today "built = renders" cannot distinguish them, which means after §1 the state table will say relations is built while 22:31's purpose for it is unserved.

---

## 2. Is there a §6 trap inside §3?

**Established.** Founder on §6: borders are refined "*given*" an assigned role. Contour refinement was parked because territories carry index numbers and no role. §3 writes "an object's profile … as row counts," with unavailable banks named, never zeroed. The brief states the spec forbids deriving identity or resemblance from the profile (I take your word for the spec; I have not read it).

**Reasoning, not verdict.** §6 is a trap when run early because refinement *uses* the role to decide what the border should become; without a role, the refinement optimises toward something arbitrary and then that arbitrary border becomes the territory everything downstream sees. The error is that an unjustified decision gets baked into the thing it was supposed to be justified by.

A row count over a territory makes no decision. It tallies which lens digits fall inside a region whose extent was fixed upstream. It cannot bake anything in, because nothing downstream is changed by it except the record itself, and the record is forbidden from asserting identity. So on the structural reading, it is not the same category as §6-early. It is a measurement over a provisional region.

But "provisional" is the word that matters, and it connects to your Q4. Once roles exist and §6 runs, territories will be re-cut, and every profile keyed to the old territory index is dead. So bundles-over-territories is not an *error*; it is a value that will be computed, discarded, and recomputed — the exact pattern 23:28 names. That is admissible for a breadth-first pass whose purpose is that the route exists, provided the record names its subject kind. If the bundle record says "object" while the key is a territory index, that is the vocabulary slip, and the question itself makes it ("an object's profile" over "territories carrying index numbers"). The mechanical guard is small: the bundle record carries the subject kind it was keyed on, so a predicate handed a territory-keyed profile can abstain with "subject not resolved" rather than silently treating the territory as its subject. §4 already says predicates abstain naming what was not resolved; this just gives them the field to read.

**What I cannot determine, and it governs the answer.** The route has no stage named for role assignment. §6's precondition — "identified meaningfully, its role assigned" — happens nowhere in the nine. Meanwhile the binding constraint forbids any stage record from marking an element as an admitted object or carrying an anatomical name. Read together with 22:31 ("I will rate objects when shown"), this is coherent: admission is the founder's act, not the machine's, during the hardware phase. But then either (a) the constraint is phase-scoped and a role-bearing stage will later exist on the route, or (b) the constraint is permanent and roles live outside the route entirely, in the founder's rating. Under (b), §6 never runs on the route, bundles-over-territories is the only bundles there will be, and the "provisional" worry above dissolves. Under (a), the recompute cost is real and should be expected. The brief does not say which; it is worth asking, because the answer decides whether §3 is building the final shape or a disposable one.

---

## 3. The fourteen properties

**Established.** 23:46 lists them; the registry declares four (`where`, compute-contract boolean, `role`, runs-on-import). `places.py` computes disagreement classes and reports a count of roles nothing can check. All 83 roles are written. Six modules carry compute contracts; nothing checks which should.

**Where I would put the line.** A property is worth *declaring* when the declaration states what the module is *meant* to do, so that disagreement between declaration and observed code is informative — i.e., when a disagreement would sometimes be resolved by changing the code. A property should only ever be *computed* when it is a fact about the code — because declaring it creates a second copy that drifts, and a disagreement would always be resolved by editing the declaration, which teaches nothing. `contract_disagrees` is the model of the first kind; an `imports` field would be the second kind.

Applying that to the ten you list as unclaimed:

- *How the pipeline consumes it, interface to neighbours, output, import/export surface, language*: facts. Compute them from the import graph, signatures, file types, the dependency graph. Declare at most the one intent-shaped bit: which stage records it is permitted to read (a layer contract — you say one exists).
- *Compute in the step*: the compute contract already is this. What is missing is not a field but the check that modules which should carry one do — the open §0 item.
- *Intent and negative contract*: declarative by nature, but their natural home is the two-sign loop (tests), not a registry sentence; a test is a declaration a machine can disagree with.
- *Shared compute*: see Q4; it is a computed property of a run, not a declared one.
- *Atomic decomposition*: neither declarable nor computable well. It is a review property. The role sentence is its proxy; a function count per module is a weak proxy. I did not find a mechanical answer and do not want to imply one exists.

So of ten, I would declare about two, compute about six, and leave two as review. A registry carrying all fourteen would be the documentation layer you fear.

**One thing in the registry already cuts against this line.** `runs work on import` is a fact; it is computable. I cannot determine why it is declared rather than computed — perhaps as a deliberate flag ("this one is allowed to"). If so, that is fine, and it is the right pattern: declare the *permission*, compute the *fact*, report disagreement.

**The number that matters.** The registry's stated purpose (23:46) is that new sessions do not lose the plot. A false declaration is worse than none for that purpose. `places.py` reports "the count of roles nothing can check"; by the brief, that is all 83. So the registry's largest field is currently entirely unchecked. The founder's 23:28 asks for *contracts* on every module, and a contract is a declaration plus something that can disagree with it. I would not add fields until that count comes down, and I would admit a new field only alongside its disagreement class or an explicit entry in the unchecked count.

---

## 4. Shared compute: what would mechanically catch recomputation?

**Established.** A telemetry ledger exists whose stated job includes what was recomputed; it is off by default and not wired through the route. The dependency graph shows a value nothing consumes as dangling. Compute contracts carry `reads` and `writes`.

**Inferred.** There are three distinct things 23:28 could mean, and they need different checks:

1. *Literal recomputation*: the same kernel on the same inputs run twice in one pass. Check: a run ledger keyed by (kernel id, hash of inputs, parameters), with a report of any key hit twice. It must read the ledger produced by the real entry point — which means the ledger must be on and the route must emit into it, otherwise this is unmeasured, as you say. This is the only check that proves the failure occurred.

2. *Re-derivation*: a later stage reads the study files, or an early record, and rebuilds something a predecessor already produced (a VST'd series, a gradient, a mask) by a different path. The ledger will not catch this because the keys differ. The check is static and reads the compute contracts' `reads` plus the import graph: a stage after `study` whose `reads` includes raw study files, or whose `reads` includes a record more than one stage upstream when the intermediate stage carries a derivative of it, is flagged. This only works if `reads`/`writes` are *named quantities* drawn from a shared vocabulary rather than free text — I cannot determine from the brief whether they are. If they are free text, the check cannot be built on them, and that is the first thing to change.

3. *Forgetting*: a value computed and never consumed, with a near-duplicate built elsewhere. The dangling-value report already catches half of this. The other half is the pairing: a dangling value in stage A plus a raw read in stage C. Reading both reports together is the mechanical form of the check.

The cheapest first step that measures rather than disciplines: turn the ledger on for the §5 run, and have the §5 record state, per stage, how many times each raw series was loaded from storage and how many times the field stage's transform was applied to it. Over one study through the real entry point, any number above one is the failure, named.

**What I cannot determine:** what the ledger actually records, whether it keys on inputs, whether `reads`/`writes` are structured, whether the layer contract already forbids downstream stages from reading study files. Each of those changes which of the three checks is already free.

---

## Things I did not consider

I did not consider the cell-tracking project's instantiation beyond the quoted sentence; I did not consider the renderer constraint ("may only arrange") beyond its interaction with Q1; and I did not consider whether the 12-stage figure in the measurement line ("3 renderers against 12 route stages") versus the nine-stage table indicates anything beyond the measurement predating §1 — I take it as the old table, but that is an assumption.