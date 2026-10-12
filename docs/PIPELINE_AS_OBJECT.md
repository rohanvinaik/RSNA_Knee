# The pipeline as one functional object

<!-- Written 2026-10-12 after the founder's "Helen Keller visual processing" teaching, which settled
what the pipeline IS rather than what it computes. Read with docs/OBJECT_MODEL.md (what the knee is),
docs/INSTANTIATION.md (which thesis section each stage builds) and docs/STAGE_CONTRACT.md (what every
stage owes). The declared change that builds it is openspec/changes/every-stage-renders/. -->

## What it is

**A symbolic associative reasoning architecture whose atoms are `<object>`s.**

Not a chain of image-processing steps that ends in a number. The founder, 2026-10-12:

> "the pipeline simply needs to be able to apply the constructed associative reasoning of 'this
> object vs this object showing this signal vs this expected signal means this label gets applied'.
> **None of those words need to be filled in with medicine or anatomy for the system to work
> perfectly.**"

So the finished sentence the machine speaks is:

    <object> 3  |  <object> 7  |  the interstice constructed between them
    reads DIGIT d  where the expected reading is e
    -> named code C, with its reason

and every term in it is a symbol the pipeline resolved for itself. "Femur", "medial meniscus" and
"effusion" are glosses **we** attach — to design the rule, and to read the output. The system is not
incomplete without them, and no stage record carries them.

An **`<object>`** is *"a resolvable sub-set of the visual field presented to a computer vision
pipeline"*. An **"object"** *"carries known semantic importance, a role that is definable and
correct, an artifact of human visual reasoning"*. They are not the same thing, and resolving the
first is **a direct homology** to reasoning over the second — which is the thesis.

## What makes it ONE object rather than ten scripts

The failure it is built against, in his words (2026-10-11): *"a mountain of code in one arbitrary
spot, one function at a time … just functionalities in islands, entire unto themselves. And it makes
efficiency terrible, since things computed for one step are completely forgotten about and
re-computed from scratch."*

Three properties, each mechanical, make it one object:

1. **One value, computed once where it becomes known, handed to every consumer.** Stages measure and
   decide; the route moves values and decides nothing. A value nothing consumes shows as dangling
   (`just graph`).
2. **Every stage is total over its predecessor's absence**, returning a named code rather than
   raising, and never substituting a default, a zero or a neighbouring reading. So the whole object
   runs end to end *whatever is missing* — which is what makes it an object rather than a chain that
   breaks at the first gap.
3. **Every stage renders what it resolved**, and the renderer may only ARRANGE values the stage
   already computed. A picture that needs work the stage did not do is evidence against the **stage**.
   So the object is inspectable at every joint.

## What "the symbolic capacity to resolve and reason on `<object>`s" means, checkably

His bar for this build, verbatim: *"it has to have the requisite component of the full thesis, and
have the symbolic **capacity** to resolve and reason on these `<object>`s."*

That capacity is not a score and not a diagnosis. It is three structural properties, and each can be
checked without judging whether any particular rule is good yet:

| the capacity | what makes it present |
|---|---|
| **symbols exist** | the field is parsed into `<object>`s with extents and boundaries, and every place is owned by one or named unassigned |
| **a language exists** | every place carries a balanced-ternary digit per acquisition against a pair of edges from that series' own distribution, with silence kept distinct from the middle digit |
| **reasoning composes** | every decision is a **named code**, total over its arguments, with every bar an **argument** and never a constant — **and the decision reads a RELATION between its subjects, not a property of one.** The relational clause was added 2026-10-12 after both readers independently found the property too weak: *"'Reasoning composes' as written admits a predicate over a single object; his sentence is intrinsically relational"* (Fable); *"passing two objects … into a total function is different from demonstrating that the function reasons with their relationship"* (Codex) |
| **the correspondence is named** | the **expected reading `e`** exists and is declared as a hand-given correspondence with its author and date — not computed, not fitted, and not silently a magic number. Added 2026-10-12: `e` appeared in the finished sentence and in none of the properties, which left the one thing the founder's own argument *requires* to be hand-given looking like a violation of the rule above |

A pipeline with all four has the capacity, even while every rule in it is still crude. A pipeline
missing any one of them does not, however good its numbers.

**On `e`, because it is the hinge.** Every other bar in the system is an argument read from the
data. `e` is not: it is the water written on the hand — the designer-supplied correspondence that the
Helen Keller argument says must be given and cannot be derived. **It is the one legitimate constant
in the architecture**, and it is legitimate precisely because it is declared rather than tuned. The
standing risk, which Fable named: if `e` is ever supplied from `memory` instead of declared, that is
the door a fitted value re-enters the architecture through.

**On generativity — WITHDRAWN as an acceptance condition, 2026-10-12.** The lead had written: *a lens
that needs re-tuning per study is brittle; one that does not is a correspondence.* Both readers
independently refused it as a bar, because it is a counterfactual about a **second** study and
acceptance is one. Codex: *"if 'needs no retuning per study' is presented as something the one-study
acceptance demonstrates, that claim is unsupported."*

It survives as a **design principle** and is replaced, as a check, by what both proposed
independently — **read the procedure, not repeated trials**:

> **The provenance check.** Every threshold a lens reads has a declared provenance: either computed
> from that series' own distribution, or a **named design constant declared together with the general
> pattern it encodes**. That is a property of the code and the record, readable in **one** run.

This is the same thing the founder's addition analogy already says: you confirm long addition by
inspecting that no step depends on the particular digits, then watching it run once.

**Corrected 2026-10-12 by the founder, because both readers drafted it too strictly.** Their version
ended "and nothing was set by looking at this study" — which forbids his actual design method. His
ruling:

> "looking at the output and coming up with arbitrary lenses/analyses that make the `<object>`
> recognition work **is** valid. **'Fitting' would be choosing specific metrics and numbers that work
> on one image.** … 'draw a line when there's a white line that's less than X pixels wide with a
> "grey" pixel on the "inside" of the object and "black" pixel on the other side'. **Arbitrary,
> entirely hand-built by looking at the actual image, but it's a *general* lens that applies
> *anywhere* that pattern appears, and the pattern is about the way the anatomical object shows up in
> the images generally, not THIS image specifically.**"

So **the line is not where a number came from — it is what the rule is about.** A constant found by
eye is legitimate when the rule it serves describes how the anatomy presents in images *generally*;
it is over-fitting when it is a value that happens to separate *this* study. The check reports
provenance and never rules on generality, **because the guard is him**: *"It's on me to not over-fit
to a specific image, and I'm pretty good about that."*

**It is necessary and not sufficient**, which only Codex caught: *"absence of retuning alone does not
establish generativity: a fixed procedure can consistently fail to perform its promised
association."* So a clean provenance check never shows that a lens works — only that it is not tuned.

**And this is why rendering is load-bearing rather than a nicety.** *"Its why I want to see the actual
processing output as much as possible; this is how I'll give you the 'Arbitrary' structure that can
solve this cleanly."* Every stage's picture is the channel through which the oracle supplies the next
lens. A stage that does not render is not merely unfinished — it is closed to the only input that can
improve it.

**And evidence is existential, not statistical.** *"If you have a set of rules that are able to do a
thing, one that isn't based on fitting/tuning metrics, then if it works properly once, then it works
period."* One study through the real entry point proves the mechanism exists. The 58-study run is
**engineering** — accuracy, cleanliness, robustness — and information about where the structure
fails. It never licenses the existence claim, because that claim is already licensed.

## The ten operations

Each row: what it does, what it consumes, what it produces, **what its picture shows**, and the
thesis section it instantiates. The picture is not documentation of the stage; it is the stage's
output in the only form that demonstrates visual reasoning.

**Ten operations, NINE stages.** Corrected 2026-10-12: the lead's first draft of this page listed
`borders` as a tenth route stage, which added one to the founder's settled route table
(`docs/OBJECT_MODEL.md`) on the lead's own authority. §6 refines **an object's** borders — it is work
*inside* `objects`, not a stage beside it, and `knee.pipeline.ROUTE` carries the nine.

| # | stage | consumes | produces | its picture shows | § |
|---|---|---|---|---|---|
| 1 | **study** | the competition's files | series, slices, geometry (LPS), tables — nothing compressed, rescaled, resampled or dropped | the acquired views as recorded, with what each series IS | 3 |
| 2 | **field** | a series | the regime key, the noise law, the variance-stabilising transform, the physical frame, the squint | the field it stands on: the squint, and where the quiet population lies | 4 |
| 3 | **lenses** | a series + its regime | one ternary digit per place per acquisition against a pair of edges, silence kept silent | the three-colour digit map per acquisition, silence drawn as silence | 7 |
| 4 | **objects** | the field | `<object>`s: territories with extents, boundaries, and the census of what bounds each and what lies across | the parse — every `<object>` in the field, by index, with its boundary and what was measured versus constructed | 5 |
| 5 | **borders** — *not a stage; work inside `objects`* | `<object>`s + their structural role + native profiles | each `<object>`'s border refined **given** its role: supported connectivity, constrained shortening, closure standing per chain | original trace beside refined, with every arc's support, shed places and open chains visible | 6 |
| 6 | **relations** | the facing-pair graph among `<object>`s | one interstice per facing pair, **constructed not detected**, with its gap, walls, fill and contents | each interstice drawn as the thing between its two bounding `<object>`s | 2 |
| 7 | **ownership** | every place + every `<object>`'s claim | every place owned by one `<object>` or named **unassigned**; each round records claimed / disputed / unassigned | **the residual map** — every place nothing claims, which is the next structure argument | 10 |
| 8 | **bundles** | each `<object>`'s places + their digits | the profile as row counts over named banks, unavailable banks named and never zeroed, the **subject kind** it was keyed on recorded | the count table per `<object>`, with unavailable banks visible as unavailable | 7, 13 |
| 9 | **predicates** | the subjects the object model gives each of the twelve | twelve named decisions, each with the reason naming what was not resolved | the twelve-row table per study, each row showing its code and reason | 2, 11 |
| 10 | **output** | the twelve codes and reasons | twelve confidences **plus the companion record**, written in the same run | the submission beside the record it is a projection of | — |

**Beside the route, and not stages:** `compute` (the `ComputeContract` each kernel carries, and
`handed_on`), `telemetry` (the ledger: counted work, and what was recomputed), `pictures` (the
drawing layer, switchable off without the run noticing). **Deferred to diagnosis, by his ruling:**
`memory`, `expert`, `agencies`, `record` — *"we should be able to isolate the components of the knee
with NO recognition, pure math."*

**Out of scope by his word:** §12, operations *on* resolved objects. *"this knee project stops at
recognition, so this part is literally extra!"*

## Where the anatomy lives

In the **design**, never in the **record**.

> "A bone looks like a bone and acts like a bone, which is why we build the lenses and rules that are
> able to define that `<object>` in the field deterministically. The *meaning* of the object doesn't
> need to exist for the computer to pull them out as `<object>`s, but **you do need to hold it in your
> head to be able to design the correct logic that is able to parse it out.**"

So: designing a lens *because* a bone behaves a certain way is required. Writing "femur" into a stage
record, code or picture is forbidden. `stage-totality`'s no-anatomy rule is the system's **correct
final form**, not a concession during a hardware phase.

**And guarding the record is not enough.** Codex, 2026-10-12, and this is the sharpest line in either
reading: *"Removing anatomical words from records does not establish that anatomical classification
is absent from **dispatch**."* A route that never writes "femur" anywhere can still have a step that
decides "`<object>` 3 is the femur" in order to choose which refinement rule to run, which bank to
key, or which subject a predicate receives — and identity would then be a destination the route must
reach, whatever its records say.

**The decisive question, which both readers arrived at independently and which no stage currently
answers:** *what resolved facts select the structural role, the subject kind, and the predicate's
subject — and where were those facts obtained?* If the selector is a relational fact an earlier stage
computed (what bounds this, what lies across it, whether its chain closes), identity is not assumed.
If the selector is a kind-label, it is. **Three places this must be answered before each is built:**
operation 5's "given its structural role", operation 8's "subject kind", and operation 9's choice of
which `<object>`s a predicate receives.

## The grading loop, which is finite

Helen Keller *"didn't need to be graded on every single word ever written"* — the atomic
correspondences were enough, after which synthesis was general. The founder is that external oracle:
*"If you build it and show me how each stage works, I am your fluid intelligence oracle 'Advisor' you
can call, I will tell you how to get the good numbers."*

So what goes in front of him is **the smallest set of atomic correspondences whose confirmation makes
a lens rule generative** — never a corpus of territories to name. His time is the project's scarce
resource and the ask is aimed at it.

## The build, in order

The declared change is `openspec/changes/every-stage-renders/`. Its shape is unchanged; what tonight's
teachings changed is recorded here.

**§0 — the scaffold, before anything is delegated.**
Done: the place registry and its check; both compute-contract idioms known to it; all 83 roles
written. Open: a structural check that every reference/twin pair declares a `ComputeContract`
(enumerating the kernels first, since a count of six has no denominator); `renders` in the registry.

**§1 — the route and the vocabulary. The lead's own, and first.**
The route table becomes the ten operations above. The shared absence vocabulary distinguishes its
silences, pinned two-sign. **Changed tonight:** `relations` and `ownership` were declared as honest
shells returning "the record shape is unsettled". That silence is no longer true — an interstice is
constructible between two `<object>`s today, and ownership is every place's claim or `unassigned`.
Both become thin **real** stages. Fable's proved gap (task 1.2 names three silences, all about an
*input*; task 1.3 needed a fourth about the stage's own design) **dissolves** rather than needing a
fourth code.

**§2–§4 — delegable**, under his 22:48 authorization: a sub-agent writes the body, the renderer and
the serialiser; never the contract, the intent tests, a bar, or a Detective survivor's verdict. A body
lands only with its certificate and after the lead has read it.

**§5 — borders (§6 of the thesis), rejoining the plan.** Parked while "role assigned" was read as
*anatomically named*; unparked on the argument that if no record ever carries an anatomical name, that
reading makes §6 unrunnable **in principle**. Not delegable: its own task text requires the support
contract specified before implementation.

**The acceptance**, in his words: *"Doesn't have to be good, or able to diagnose — it has to have the
requisite component of the full thesis, and have the symbolic capacity to resolve and reason on these
`<object>`s."* So the pass is complete when **one study, through the real entry point, produces ten
stages that each ran, each returned a record or a named absence, and each rendered what it resolved**
— and the three capacity properties above hold.

Then he inspects the image series. That is the point of the change, and nothing in it may assign
meaning on his behalf.
