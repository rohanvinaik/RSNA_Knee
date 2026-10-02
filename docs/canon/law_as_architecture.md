---
tags: [paper, classical-ai, hdc, physics-structured, grey-box, inverse-problems, society-of-mind, near-miss, sparse-distributed-memory, geosteering, vibe-physics]
type: paper
stream: classical-ai
concepts: [law-structured network, differential-equation topology, composed first-order specialists, vibe physics, society of mind, sparse distributed memory, recollective k-line memory, near-miss censor, regime stratification, coherent-replicate imputation, intrinsic error propagation, delta-method uncertainty, structure over scale]
status: draft
---

# Law as Architecture: Differential-Equation Structure as Network Topology, with a Recollective Memory and Coherent-Replicate Imputation

**Abstract.** A large class of practical inference problems shares a shape the dominant
paradigm handles badly: a known physical law relates observable signals to a hidden state we
want, but the unknowns inside the law are not constants — they drift with regime, geology,
provenance — and the signal that would pin them is *incomplete*, sparse or locally ambiguous
exactly where it matters. The reflex response is to fit a flexible function to a corpus of solved
cases and hope scale fills the gaps. This paper argues that scale is the wrong axis, and that the
problem has a deterministic, auditable solution assembled from classical parts. The load-bearing
move is structural and specific: **the governing equation's *structure* becomes the network's
*topology*.** An nth-order law is realized as *n* composed first-order specialists — Minsky-style
agents in a Society of Mind — wired together exactly the way the equation composes its terms, each
specialist supplying ("vibing") the one unknown it owns, and the *only* quantity ever supervised is
the **composed output**, never a specialist in isolation. This is the grey-box discipline of
universal differential equations, but transposed: the differential structure is not a fixed solver
wrapped around one learned residual, it is the wiring itself, and so two things come for free that
are usually bolted on. First, **the error propagates through the same composition as the signal** —
a term that enters the law squared enters the uncertainty through its derivative, the couplings
between terms appear as cross-terms — so confidence is intrinsic, not a fitted afterthought. Second,
the thin unknowns each *mean* something, which lets us store them. The second load-bearing move is
that memory: the vibed coefficients are **recalled by resemblance** in a Kanerva sparse distributed
memory — k-lines rendered not as activation sets but as balanced-ternary hypervectors over a smeared
codebook, a *recollection* ("this resembles what we saw") rather than a byte-perfect rule, and a
truer model of memory than the literal K-line for being so. Around this engine we assemble the rest
from established primitives: hard **near-miss censors** that make the physically impossible
unrepresentable rather than merely penalized; coefficients **stratified by regime** so distinct
physics do not contaminate one another; and — as a downstream refinement that *conditions the
engine's inputs* rather than carrying the inference — **coherent-replicate imputation**, which
recovers the missing inputs of one instance from physically-linked neighbors treated as a Kuramoto
field of replicated experiments. We develop the architecture against a running inverse problem —
recovering a horizontal wellbore's stratigraphic position from a gapped gamma-ray log — and report
honestly on what runs and what the framework organizes. The contribution is not a new primitive;
every primitive here is decades old and credited. It is the **composition**: a governing law made
literally into a network, its unknowns vibed by a society of specialists and remembered by
resemblance, its errors riding the law's own derivatives, its inputs repaired from the field of its
replicates.

---

## 1. Two regimes, and the residue that scale does not reach

There are two ways to predict a quantity you cannot directly see. One *learns the mapping* from
inputs to the quantity by fitting a flexible function to a corpus of solved examples; the other
*inverts a known law* that relates the two, solving for the hidden state that best explains the
observed signal. The first regime has eaten the field, for a defensible reason: where the law is
unknown or intractable, fitting is the only move, and at scale it is astonishingly effective. A
companion paper [1] argues that this victory has been over-generalized — that there are layers of
understanding the fitting regime cannot reach by construction — and a second [2] locates a specific
linguistic tail where the right computation is a *relation* the fitting regime cannot represent.
This paper concerns a different residue, an engineering one, where the law is in fact *known* and
the difficulty is somewhere else entirely.

The residue is this. We have a physical law — a geometry, a transport equation, a known response
function — that ties an observable signal to a hidden state. The law's *form* is known exactly; what
is unknown is a handful of *coefficients* inside it, and those coefficients are not constants. They
shift with physical regime, with material, with location; they are precisely the quantities a
textbook leaves as "depends on the formation." We have many solved instances from which those
coefficients could in principle be read. And yet the inversion fails on the instances that matter,
because the signal that would pin the coefficients is **incomplete**: it has holes (missing
samples), or it is locally *non-injective* (the same observed value is consistent with many hidden
states), so that over the gapped or ambiguous stretches the law admits a whole family of solutions
and the data cannot choose among them. With complete signal the inversion meets the physics — it is
accurate to the limit the geometry allows. The entire error lives in the holes.

The reflex prescription is more data and a bigger model: learn a mapping flexible enough to paper
over the gaps. We will argue this mislocates the difficulty in the same way the companion paper [2]
shows the "subjective" label mislocated irony. The information that resolves a hole is not, in
general, present in the corpus statistics of the gapped signal — averaging a thousand other
instances does not tell you what *this* instance's missing samples were. It lives in two places the
fitting regime is structurally blind to: in the **law** (which, given its surrounding values,
sharply constrains what the missing coefficients *could* be), and in the **replicates** (other
instances of the same physical system, close enough to share its dynamics, which sampled what this
one missed). The job of the architecture is to make the law itself the computational object that
brings the first to bear, deterministically and per-instance, and to bring the second in as a
conditioning step — and to be honest about the residue that genuinely remains.

## 2. The thesis, restated

We make six claims. The first two are the load-bearing engine; the next two are the parts that make
it sound and bound; the fifth is the downstream refinement that conditions the engine's inputs; the
sixth is the consequence that makes the whole trustworthy. The order is the architecture's order of
importance, and getting it right matters — an earlier draft of this account inverted it, crowning
the refinement and demoting the memory, and the correction is the spine of what follows.

**The Law-as-Architecture Thesis (load-bearing).** When the functional form relating signal to
hidden state is known, its *structure should become the network's topology.* An nth-order law is
not wrapped around a learned residual; it is *decomposed into n composed first-order specialists*,
each a Minsky-style agent [10] that supplies the one unknown variable it owns, wired together
exactly as the equation composes its terms — so that a second-order dynamic is literally two
first-order specialists whose composition is the modeled signal, and the *product of their outputs*,
not either output alone, is the quantity training is measured against. Each specialist "vibes" its
unknown: it knows the *shape* of its term and shrugs out a stratified estimate of the coefficient
the textbook leaves open. This is the established grey-box pattern — universal differential equations
[3], physics-informed networks [4], structure-encoded Lagrangian models [5] — but pushed to its
literal conclusion: the differential structure *is* the wiring, supervision happens only at the
composite, and the discipline is sharper than usual. The learned part must be kept *minimal*
relative to the fixed structure, because an over-flexible specialist absorbs the contributions of
the terms it composes with and corrupts the physical meaning of every coefficient [6]. The structure
carries the inference; each vibe is a thin, identifiable correction the structure cannot itself
supply.

**The Recollective-Memory Thesis (load-bearing).** Because the vibed coefficients each *mean* one
thing — a dip, a stretch factor, a regime gate — they can be *stored and recalled by similarity*
rather than re-derived from scratch per instance or frozen into weights. They live in a Kanerva
sparse distributed memory [7], keyed by a hypervector encoding of the instance's context (its
geometry, its log character, its regime) and recalled by *resemblance*: a new context activates the
stored coefficients of the contexts that resemble it, weighted by closeness. The encoding is the
project's own substrate — balanced-ternary hypervectors over a smeared codebook [13], the same
representation the signals themselves live in — so the memory is native, not bolted on. This is
Minsky's K-line [8] rendered as a hypervector rather than an activation set, and the substitution is
not cosmetic: recall is reconstructive and graceful — "this resembles cases we have seen,"
degrading smoothly as the context drifts — rather than the brittle hit-or-miss of an exact key. It
is, not incidentally, a closer model of biological memory than the literal K-line it replaces, and
it is where the *messy, vibed* unknowns of the first thesis become addressable: the field's
accumulated experience, made recallable by overlap. The engine and its memory are the two pieces
that carry the work; everything below serves them.

**The Censor Thesis (guardrail).** Physical validity is enforced by *hard constraints learned from
near misses*, not by soft penalties. A candidate solution that is locally plausible but globally
impossible — a configuration no real instance of the system ever produces — is made
*unrepresentable*, vetoed at inference time, rather than merely scored down. This is Winston's
near-miss learner [9] turned into a censor in Minsky's sense [10]: the boundary of the valid region
is carved by the examples that *just* fail, and crossing it is forbidden.

**The Stratification Thesis (regimes).** A vibed coefficient means one thing inside a physical
regime and another across one. A wellbore's build section and its lateral obey the same law with
*different* coefficients; a geological domain shifts them again. The unknowns are therefore fit and
recalled *block-diagonally* — each regime identified only by its own data, with strict
no-contamination — so the memory of the second thesis is queried with the regime already known.
This is the established stratified-regression apparatus [14,15,16]; the architecture's commitment is
only that the regime is part of the key.

**The Coherent-Replicate Refinement (downstream input-conditioning).** Where even the law and the
memory leave a coefficient under-determined — a stretch the signal never resolves — the missing
*input* is recovered from *coherent replicates*: other instances of the same physical system, linked
closely enough in space and provenance that their dynamics are shared, treated as a Kuramoto field
[12] of oscillators locked to one rhythm while keeping their own phase. This is a refinement, not the
engine: it does not perform the inference, it *conditions the engine's inputs*, supplying a clean,
mechanistically-imputed value where the instance's own signal is silent. We are explicit that it sits
downstream of the law and the memory, because a clean imputed input is exactly what a physics-based
model most wants — and because mistaking this conditioning step for the central move (as an earlier
draft did) misreads the whole architecture.

**The Honesty Consequence.** Because the law *is* the computation, uncertainty is not fitted but
*propagated through the law's own structure*: each term's local sensitivity is the gain on that
term's vibe-error, and the couplings between terms appear as cross-terms — the delta method [6], but
here a structural inevitability rather than an add-on. The error rides the same composition as the
signal. The system therefore reports where its answer is well-determined and abstains, with a graded
score, where the propagated error is wide. As in the companion comparator [2], the one thing the
architecture structurally cannot do is fabricate a confident answer in a region the evidence leaves
open.

The rest of the paper develops these in order of weight, with the engineering made concrete against
a running problem, and closes on an honest account of what is built.

## 3. The mistake that makes it look like a scaling problem

The error worth naming is the habit of reading every "the model is wrong here" as "the model needs
more capacity or more data." For the residue of §1 this is category-wrong, and seeing why fixes the
design.

Take the running problem. A horizontal well is drilled through a layered rock formation; a gamma-ray
tool logs the rock's natural radioactivity along the borehole; a nearby vertical *reference well*
gives the gamma-ray signature as a function of stratigraphic depth. The hidden state is the bit's
stratigraphic position — where in the layer-cake it sits — and the law that ties signal to state is
geometric: the logged gamma-ray at a point equals the reference log read at the bit's true depth,
shifted by the bedding *dip* through the known trajectory geometry. The law's form is exact; the
unknown inside it is the dip, which varies along the well. With a clean, information-rich log this
inversion is accurate to a few feet. But the log is roughly a third missing, and over the long
near-horizontal stretches the rock barely changes, so the gamma-ray is nearly flat and the *same
flat reading is consistent with a wide band of depths* — the inversion is locally non-injective. A
flexible model trained on a thousand solved wells does not help here: it regresses to the population
mean over the flat stretches, because the population mean is what minimizes its loss when the input
carries no discriminating signal. We measured exactly this — a gradient-boosted predictor with rich
features tied the trivial persistence baseline, recovering the easy wells and washing out on the
hard ones.

The information to resolve a flat stretch is simply not in that stretch's signal, and no amount of
model capacity manufactures it. It is in the *law* (the bit was steered to hold a target layer, so
the dip is bounded and smooth, not free) and in the *replicates* (a well two hundred feet away
through the same beds sampled the structure this well's flat stretch could not resolve). The fitting
regime is blind to both: it has nowhere to put a hard geometric constraint, and it dissolves the
per-instance, spatially-local replicate relationship into a global average the moment it pools the
corpus. The failure is not under-capacity; it is *looking for the answer in the wrong place* — in
the gapped signal, where it was never going to be. The fix is to make the law the computation, vibe
its unknowns through a society of specialists, and let the memory and the replicates supply those
unknowns where the signal cannot.

## 4. The architecture

The system is a per-instance inversion in which the law is the network. Its components are named
below; §§5–10 develop them in order of weight. We state it for the running problem and generalize in
§11.

Let `x` be the hidden state (stratigraphic position, TVT), `g(s)` the observed signal (gamma-ray
along measured depth `s`), `R(·)` the known reference response (the type-log), and `T` the trajectory
geometry. The law composes as

```
x(s)   = a(s) − ΔZ(s) − dip(s)·ΔL(s)        (geometry: state from an anchor through a dip term)
dip(s) = ∂_s S( X(s), Y(s) )                 (structure: the dip is the gradient of a surface S)
ĝ(s)   = R( x(s) )                            (response: predicted signal from state, in TST [11])
```

Read this not as three equations but as **three composed specialists**: a geometry specialist that
turns a dip into a state through the trajectory, a structure specialist that supplies the dip as the
gradient of a surface `S` it vibes the coefficients of, and a response specialist that maps state to
predicted signal through the reference log and the inclination-dependent stratigraphic stretch [11].
None is supervised alone. The only error that exists is between the *composed* prediction `ĝ` and the
observed `g`; it flows back through all three. The unknowns are thin — chiefly the coefficients of
`S` — and the structure carries everything else. Three facts make the design:

- **The match is a sequence problem, not a per-point one.** Locally the signal is non-injective;
  globally, the whole path against the whole reference under a continuity constraint is far less so.
  We solve it as a band-limited dynamic program (a Viterbi over a depth lattice) whose emission is a
  shape-correlation between the synthesised and observed log and whose transition cost is the
  dip-roughness — the deterministic forward-model-and-match the field itself uses [11].
- **The unknowns are regime-dependent and recalled, not re-fit.** The coefficients of `S` differ by
  drilling phase and geological domain; they are stratified block-diagonally (§8) and stored and
  recalled by similarity in the HDC memory (§6).
- **The inputs can be repaired before the engine runs.** Where the signal never resolves a stretch,
  the coherent-replicate refinement (§9) supplies the missing input from neighbors, so the engine
  inverts against a conditioned signal rather than a silent one.

The completion runs as a grey-box loop:

```
1. invert the RESOLVED stretches (where the signal is informative) → a partial state estimate + a per-stretch confidence
2. fit/recall the surface coefficients of S from those stretches (and, where thin, the imputed neighbor inputs of §9)
3. the structure specialist's gradient supplies dip over the HOLEY stretches — the value they inherit
4. re-invert with that value, under the near-miss censors (§7)
5. repeat to convergence; the error propagates through the composed law (§10) into a per-point confidence
```

Censors guard every step; the memory supplies the vibed coefficients; the replicate refinement
conditions the inputs where the signal is silent; the uncertainty layer reports where the answer is
earned and where it is abstained.

## 5. The law as architecture — composing the equation into specialists

This is the heart, so we develop it past the slogan. The claim is *not* the familiar one that a
known law should regularize a fitted model, nor even only that a thin coefficient should be learned
inside a fixed solver. It is that the **order and structure of the governing equation should be the
topology of the network**, and that this buys two things a wrapped-residual grey-box does not.

Begin with the decomposition. A dynamic governed by an nth-order relation is, by the elementary
theory of differential equations, equivalent to a coupled system of *n* first-order relations. We
take that equivalence literally as an architectural instruction: instantiate *n* first-order
specialists, one per reduced state, and wire them so their composition reconstructs the original
dynamic. Each specialist is a classical Minsky agent [10] of definitionally first-order character —
it knows the *form* of its own term and carries the one coefficient that term leaves open. A
second-order law becomes two specialists whose outputs *multiply (or otherwise compose, as the law
dictates) into the modeled signal*; the signal against which training is measured is that
composition, never a specialist's isolated output. The society computes the law; no member computes
a supervised target. This is "vibe physics" with a precise meaning: we know the general shape of how
the inputs drive the output — the equation gives it to us exactly — and the specialists supply only
the stratified coefficients the equation leaves to the world, a shrug-and-estimate where genuine
knowledge runs out, disciplined by the surrounding structure that will not let the shrug wander far.

The first dividend is *identifiability as a built-in, not a hope.* The grey-box literature names the
central failure exactly: when the learned component is over-parameterized, it *absorbs*
contributions that belong to the mechanistic terms, and the fitted coefficients lose their physical
meaning even as the output fit improves [6]. The decomposition makes the discipline structural. Each
specialist owns exactly one term's coefficient and is composed — not blended — with the others
through the equation's own operators, so there is no flexible blob to absorb a neighbor's
contribution; the only way to fit the composite is to get each term approximately right. *Keep the
learned part thin and let the law dominate* is here not a regularization choice but the shape of the
wiring. This is what makes the recalled coefficients of §6 *mean* something stable enough to store: a
surface dip, a phase stretch factor, rather than an entangled parameter valid only locally.

The second dividend is the one usually paid for separately: *the error propagates through the same
composition as the signal.* Because the output is literally a composition of the specialists'
terms, its sensitivity to each vibed coefficient is that term's own derivative, and the couplings
between terms are the law's own cross-terms. If a law composes as `f = c² + log(d)` for vibed `c`
and `d`, the uncertainty composes as the derivatives demand — a gain of `2c` on `c`'s error, a gain
of `1/d` on `d`'s, and a cross-term wherever the structure couples them — not as a separate noise
model laid on top. The delta method [6] is the formal name for this push of input covariance through
the law's Jacobian, but in this architecture it is not a post-hoc analysis: the Jacobian *is* the
network, so the confidence falls out of the same forward object that produced the answer. A
specialist that vibes its coefficient with wide spread widens the composite's error precisely along
the direction its term steers — automatically, auditable, per-point. §10 makes this the honesty
mechanism; here the point is only that it is free, because the law was wired in rather than wrapped
around.

The reader should see why neither dividend survives the soft-penalty alternative. A physics penalty
competes, in a single loss, against a data-fit term, with a balance no principle sets; worse, a
model flexible enough to need the penalty is flexible enough to satisfy it dishonestly, locally
plausible everywhere and globally wrong, because nothing forbids the wrong region — it is only
taxed. The structure is not a prior over a flexible model; it *is* the model, and the vibes are the
small, identifiable corrections the structure cannot itself supply. Boundedness — the same property
the companion paper [2] shows is the precondition for sound local-to-global inference — appears here
as the precondition for *interpretable, transferable, storable* coefficients.

## 6. The memory — vibed coefficients recalled by resemblance

The thin coefficients of §5 vary by context, and re-deriving them per instance wastes the field's
accumulated structure. They are instead stored in a Kanerva sparse distributed memory [7], keyed by
a hypervector encoding of the instance's context — its geometry, its log character, its regime — and
recalled by *similarity*: a new context activates the stored coefficients of the contexts that
resemble it, weighted by closeness. Recall is reconstructive and graceful — a context near several
stored ones returns their blend; a context far from all of them returns a weak, low-confidence prior
the uncertainty layer respects — rather than the brittle hit-or-miss of an exact key. Storing and
regressing *continuous* coefficients in a high-dimensional vector memory is itself established
[17]; the architecture's commitment is to make that memory the home of every vibe.

The encoding is not generic. It is the project's own substrate — balanced-ternary hypervectors over
a smeared codebook [13] — the same representation in which the signals are carried, so the memory
keys, the stored coefficients, and the data all live in one space. This is Minsky's K-line [8] — a
stored pattern that completes a partial cue — realized as a hypervector rather than a literal
activation set, and the substitution earns its keep three times. It is *more efficient*: recall is a
dot product over a distributed code, not a search over a rule table. It is *more faithful*: a
hypervector memory returns "the resolved coefficients of cases like this," degrading smoothly with
distance, which is the character of human recollection — Kanerva offered SDM explicitly as a model
of human long-term memory [7] — rather than the all-or-nothing of an indexed store. And it is
*native*: because the key is the same ternary substrate as the data, the memory is a fingerprint of
the model's own state, not a translation of it. This is where the "messy, vibed BS" of §5 is meant
to live — the unknowns the law leaves open, made addressable by resemblance, so that "we have seen
wells like this before" becomes a computation rather than a wish. The engine of §5 and this memory
are the architecture's two load-bearing organs; the sections that follow protect them, scope them,
feed them, and audit them.

## 7. The censors — forbidding what no real instance does

The dynamic program of §4 will, left unconstrained, occasionally lock onto a globally impossible
solution: a path locally well-correlated against the reference (an alias) that drifts into a
configuration no real well occupies. These are *near misses* in Winston's exact sense [9] —
solutions almost valid but violating one structural constraint — and the right response is not to
score them down but to forbid them.

Two censors, learned from the field, illustrate the form:

- **The envelope censor.** Real wells stray from their reference horizon within a bounded envelope
  that grows with distance drilled; the boundary is read directly off the field's solved cases. A
  candidate path that exceeds it is made unrepresentable in the lattice — a hard veto, an `−∞` in the
  dynamic program, not a penalty.
- **The motion-evidence censor.** This one is pure law: the signal *is* a function of the state, so
  the bit cannot move through varying rock without the log varying. A candidate that claims the
  state moved while the observed signal stayed flat — motion the log does not show — is physically
  impossible and is vetoed wherever the synthesised signal's variation exceeds the observed.

These are Minsky censors [10] carved by Winston near-misses [9]: the half of the 1970 learner that
*specializes* a concept by the example that just fails, here applied to a continuous geometric state
rather than a blocks-world arch. They compose with the same engine the companion paper [1] uses to
carve a story-rule exception from a surprising counterexample — one near-miss mechanism, a narrative
censor there, a physical censor here.

## 8. Regime stratification — keeping the phases from contaminating each other

The vibed coefficients are not global. A wellbore passes through physically distinct *phases* — a
steep build section and a near-horizontal lateral — in which the same geological dip projects into a
*different* signal stretch, because the inclination-dependent map from measured depth to
stratigraphic thickness changes with the angle between borehole and bedding [11]. Fit one set of
coefficients across both and each corrupts the other; recall a coefficient without knowing its
regime and the memory of §6 returns a blend of incompatible cases.

The fix is the established stratified-regression apparatus, chosen by how hard the regime boundary
is. Where the boundary is known and sharp (the kickoff between build and lateral), a *block-diagonal*
design [14] gives each phase its own coefficient vector, identified only by that phase's data, with
strict no-contamination — and optionally shares the coefficients that *are* common while splitting
only those that differ. Where the boundary is a soft geological domain across the field,
*spatially-clustered regression* [15] assigns neighborhoods to regimes by a penalized likelihood with
a spatial-smoothness term. Where we would rather the boundary itself be learned, a *mixture-of-experts*
gate [16] routes each input to the regime that claims it. The choice is engineering; the principle is
invariant — *a coefficient means one thing within a regime and another across one, so the regime must
be part of the key before the law's unknowns are read off the memory.*

## 9. The coherent replicate — imputation as a measured experiment

We come to the refinement, and we are deliberate about its station: it conditions the engine's
inputs, it does not carry the inference. Where the law (§5) and the memory (§6) still leave a
coefficient under-determined — a stretch this instance's signal never resolves — the missing *input*
is recovered from *coherent replicates*, and handed to the engine as if the instrument had measured
it.

The instances are not independent draws; they are replicates of one physical system. In the running
problem, wells in a development field are drilled hundreds of feet apart through the same beds; the
structural surface `S(X,Y)` that governs the dip is *one surface*, sampled by every well that crosses
it. So a stretch where this well's log is flat and uninformative is a stretch where a neighbor —
which crossed the same structure at a slightly different angle, and whose state is *known* — already
measured what we need. The neighbor is not a similar example to average; it is a replicate of the
same experiment that happened to record the channel this one missed. The imputation is then a *fit of
the shared surface from pooled replicate control*, with the replicates' real differences carried
explicitly rather than smoothed away:

- **Shape from the field, level from the self.** The neighbors pin the *structure* — the dip field
  `∂S`, the undulation, the regional trend — because that is the shared physical object. The
  instance's *own* known boundary (its heel, where its position is given) pins the *absolute level*,
  because that is the part the replicate does not share — a neighbor may hold a different target
  layer. Structure is coherent across the field; offset is individual. We separate them.
- **Replication is the confidence.** Because many neighbors sample the same surface, the fit has an
  error bar that *shrinks with the replicate count* — a measured quantity, not an assumption — and
  that error bar enters the engine's intrinsic uncertainty (§10) as the spread on the imputed input.

The right formalism for "physically-linked systems share a rhythm but keep their own phase" is a
Kuramoto coupling [12]. Treat each well's dip-along-path as an oscillatory state with an intrinsic
phase (its own offset, its own steering history) and a coupling to its spatial neighbors through the
shared surface. The coherent regime — high order parameter — is the field locking to one structural
rhythm; the residual phase spread is exactly the physical individuality we must *not* average out.
The order parameter is then a direct, computable gate on the imputation: where the neighborhood is
coherent, the surface is trustworthy and the input is supplied with conviction; where it
desynchronizes (a fault, a facies change), the coupling weakens and the system correctly trusts the
local signal over the field.

It is worth saying plainly what this is and is not, because an earlier draft of this paper made it
the centerpiece. It is *not* the engine: it does not invert the law, it does not carry the
inference, and the architecture stands without it on every stretch the signal resolves. It *is* the
best possible input-conditioning for a physics-based engine — a mechanistic, measured imputation of
exactly the quantity the law next consumes, which is a far cleaner thing to feed an inversion than a
statistical guess. Read against the companion comparator [2], the move is a Janus operation at the
level of *data*: the gapped local signal is the literal face (what this instance measured, bottom-up),
the field-structural expectation from coherent neighbors is the world face (what the shared physics
licenses, top-down), and the conditioned input is their relation — trust the local where it is
informative, inherit the structural where it is not, and pass the disagreement forward as the
input's uncertainty. That is the sense in which the companion stack's two-views-plus-coherence
operator recurs here; but it recurs as a *feeder*, one stage upstream of the engine, not as the
engine itself.

## 10. Uncertainty as a structural inevitability

Because the law *is* the computation, the system's confidence is not a fitted afterthought but a
propagation — and, by §5, one that costs nothing extra to obtain. The covariance of the inputs — the
signal noise, the trajectory error, the surface fit's replicate-count-dependent spread (§9), the
recall confidence of each vibed coefficient (§6) — is pushed through the composed law by a
first-order Taylor expansion in the law's own Jacobian [6]. Each specialist's term contributes its
derivative as the gain on its coefficient's error; the equation's couplings contribute the
cross-terms; the result is a per-point error bar on the recovered state, assembled from the very
same forward composition that produced the state. The error rides the signal's own wiring.

Two independent channels join this propagated bar: the Kuramoto order parameter of the neighbor
field (§9), which reports where the imputed inputs are trustworthy, and the dynamic program's
emission margin (§7), which reports where the shape-match is decisive. Where the three agree the
answer is trustworthy; where they diverge the system flags the disagreement. The consequence is the
same honesty the companion comparator makes its centerpiece [2]: in a region the signal and the
replicates both under-determine, the architecture does not emit a confident number in the register it
uses for a well-pinned one. It reports a wide bar and abstains toward the safe structural prior. This
is not a limitation bolted on; it is what an explicit law buys — the ability to know, mechanically
and per-point, the difference between *what was inferred* and *what could not be*, and to say so. A
fitting model forced to emit one number over a flat stretch emits a confident wrong one; a
law-structured network reports the band the physics leaves open, because the band is just the
forward composition run on the error.

## 11. The running proof, and what generalizes

The architecture is developed here against geosteering because that problem exhibits every feature
the design targets: a known geometric law with a small, regime-varying unknown (the dip), a signal
both gapped and locally non-injective, abundant spatial replicates, sharp physical phases, and a
real ground truth to score against. The honest status (§12) is that the law-structured inversion —
the composed forward-model-and-match specialists — the near-miss censors, and the similarity memory
*run* and beat the trivial baseline; the coherent-replicate input-conditioning is designed and its
precondition *measured* (the replicate density is real and abundant), with the field-coupled fit the
immediate work the framework organizes.

The shape generalizes past wells. A **law-structured network** is any inversion where the forward law
is known and *wired in as the topology* — its order decomposed into composed first-order specialists
that vibe the thin unknowns and are supervised only at the composite — its coefficients stored and
recalled by resemblance, its validity enforced by near-miss censors, its regimes stratified, its
missing inputs conditioned from coherent replicates where the signal is silent, and its uncertainty
read off the law's own Jacobian. The pattern fits any setting with the signature: a mechanistic
forward model of known structure, thin regime-varying unknowns inside it, incomplete per-instance
observation, and a field of linked instances that share the hidden dynamics — subsurface and medical
imaging from sparse views, sensor networks with dropout, any reconstruction where neighboring
deployments of the same system are the replicate that fills the gap. The thread tying it to the
companion stack is the recurrence of the two-views-plus-coherence operator [1,2] — but here, kept in
its proper place: not as the inference, which the law performs, but as the feeder that conditions the
law's inputs, one of several organs around an engine that is itself the governing equation made into
a network.

**A second running instantiation, in a different domain.** The strongest evidence that the
contribution is the composition and not the geosteering particulars is that the whole five-part
architecture transposes — intact, and *built* rather than retrofitted — into a problem with no
geometry, no wells, and no continuous signal at all: recovering clean propositional *statements* from
the degraded per-sentence output of the deterministic semantic parser of the companion understanding
stack [1]. The mapping is exact. The *law* is the structure of a well-formed statement, decomposed
into a society of single-distinction repair specialists — a copula-to-type-assertion lens, a
participial-adjunct recovery lens, and so on — each owning one thin unknown the structure cannot
itself supply; for the participial lens that unknown is the *subject binding*, the one quantity a
degraded parse routinely drops. It is stored and recalled exactly as §6 prescribes: a balanced-ternary
hypervector over the parser's own codebook, keyed by the statement's local-token context and its
register (the regime of §8), recalled by resemblance and reconstructed as a closeness-weighted blend —
never the specific referent, whose storage would destroy transferability precisely as §5 warns. The
censor of §7 is the clean-or-hole contract: a recalled binding whose confidence falls below threshold
is made unrepresentable, the lens abstaining rather than emit a fabricated statement, with the
threshold read off the memory's own recall confidence — the §10 honesty mechanism in miniature. Even
the coherent-replicate refinement of §9 recurs, as a document-scale "fold-reader" that pins the
recurring protagonist from the field of an entity's mentions and conditions the lens where the local
signal is silent, leaving the memory to carry the residual. What runs, reported honestly: on real
corpus text the trained memory recalls a held-out participle's dropped subject at 62% against a 53%
best-single-rule baseline; wired into the downstream reasoner and gated at its high-confidence regime,
the bindings it emits are ~90% correct on real output — with the architecture's *own* confidence
signal, not a hand-built filter, rejecting the implausible ones, and no malformed statement reaching
the reasoner. Coverage at that clean threshold is deliberately modest: the confidence only partly
separates right from wrong, so correct-but-uncertain bindings abstain alongside the wrong ones, and
tightening the context key until more correct recalls clear the censor is the immediate engineering
the framework organizes — the linguistic analogue of the geosteering surface-fit. That the same
composition carries an inference in a domain of pure discrete structure is the transposition this
paper predicts, and the first confirmation that the residue of §1 has the shape claimed for it
wherever a known law meets an incomplete signal.

## 12. Status, and what would falsify the account

Honesty about maturity is part of the proposal, as in the companion papers. The components are at
different stages. The **law-structured inversion** runs: the composed forward-model-and-match
specialists, the shape-correlation emission, the dip-smoothness prior, and the two **near-miss
censors** are built and tested, and beat the persistence baseline on held-out wells. The
**similarity-memory** completion of per-stretch dip from analogous cases runs and helps the holey
stretches measurably. The **coherent-replicate input-conditioning** — the refinement — is specified
and its precondition is *measured and strong* (every held-out well has dense, known-state neighbors),
but the field-coupled surface fit and its Kuramoto gating are the immediate engineering, not yet a
reported result. The **regime stratification** and the **intrinsic delta-method uncertainty** are
designed from the cited apparatus and the engine's own Jacobian, and partially wired. The defensible
present claim is therefore not "the inverse problem is solved," but that it is correctly *factored*:
the error is relocated from a gapped signal that cannot supply it to a law that constrains it, a
memory that recalls it, and a field of replicates that conditions it — and the components that
realize each are either running or precondition-verified.

A second instantiation now runs, and its evidence is independent. The architecture has been
transposed in full to the statement-healing inversion of the companion understanding stack [1]
(§11) — a different domain, a different signal, the same five parts. The law-as-society, the
resemblance memory over the parser's native hypervector codebook, and the clean-or-hole censor are
built and validated on real corpus text: the recollective memory beats the best single rule on
held-out subject recovery, and the censor is calibrated enough that the bindings it admits at its
high-confidence regime are ~90% correct downstream, the implausible ones rejected by the recall
confidence itself rather than a bespoke filter. As with geosteering, the maturity is mixed and stated
plainly — clean coverage is modest because the confidence only partly separates, and the context-key
tightening that would raise it is named as the immediate work, exactly as the field-coupled surface
fit is named here. The two instantiations falsify or confirm the thesis on disjoint evidence: if the
composition were carrying the geosteering particulars rather than a domain-general shape, it would not
have transposed to a problem with no geometry and no continuous signal at all.

The account makes commitments that could fail. It predicts that decomposing the law into composed,
separately-vibed specialists *preserves the coefficients' physical meaning* well enough to store and
recall across instances — that an over-flexible variant, one specialist allowed to absorb its
neighbors, should degrade both interpretability and transfer, per the identifiability hazard [6]. It
predicts that the coherent-replicate conditioning breaks the under-determination — that supplying the
engine the neighbors' *known structure* (not their signals) where its own signal is silent sharply
outperforms both the per-instance fit and the cross-sample mapping; if neighbor structure carried no
information about a held-out well's hidden state once its own heel is controlled, the refinement would
be inert. And it predicts that the uncertainty read off the law's Jacobian is *calibrated* — that
error rises precisely where the propagated bar widens and where the neighbor field desynchronizes;
that is a measurable calibration claim. We mark these as the seams where the account could break, and
intend to measure them.

## 13. Conclusion

The problems offered as proof that an inverse task "needs scale" — the gapped signal, the flat
non-injective stretch, the under-determined reconstruction — were rarely evidence about capacity.
They were evidence about *where the information lives*, and about *what shape a model must have to
use it*. Wire the governing law in as the architecture itself — its order decomposed into a society
of first-order specialists that vibe the thin unknowns and are judged only at their composition, so
the structure carries the inference, the coefficients stay meaningful enough to remember, and the
error rides the same wiring as the signal. Store those vibed unknowns in a memory that recalls by
resemblance rather than exact key. Forbid the physically impossible with censors carved from near
misses; keep the regimes from contaminating one another; and, where the signal falls silent,
condition the engine's inputs from the coherent field of its replicates — a refinement that feeds the
law, not a rival to it. Propagate the uncertainty through the law, because an explicit law makes
confidence a structural fact rather than a fitted guess. None of these primitives is new — universal
differential equations, sparse distributed memory, the near-miss learner, the Society of Mind,
Kuramoto coupling — and that is the point this collection keeps making: the work is the *composition*.
The same two-views-and-coherence signature that mechanizes narrative understanding [1] and figuration
[2] appears here too, but in its proper subordinate place, conditioning the inputs of an engine that
is the law made into a network. The wager throughout has been that a small, deterministic, auditable
system, pointed at the right problems and built from the right old parts, does what the scaling era
assumed only scale could. This is one more place the wager holds — written, this time, in the
language of an equation made into an architecture.

---

## Note (speculative frontier): the level above — a society of *understandings*

*This is a margin note, not part of the validated thesis — the direction the architecture points once
the unit of composition is allowed to grow. It is recorded because the gap it steps into is, on
inspection, an old and unclosed one.*

Read this paper's Society of Mind honestly about its scale. The agents here are **first-order law
specialists** — each scoped to a single term of an equation, composed by the equation's own operators,
supervised only at the composite. That is composition over a *small, sub-symbolic* space: the unit is a
coefficient, and the compose-operator, for all the structure around it, is at bottom a *blend* of
specialist outputs. This is where every descendant of the Society of Mind has actually lived —
mixtures of experts, ensembles, neuro-symbolic hybrids: many small specialists, fused by weighting,
*under* the symbols. Minsky [10] named the society and its arbiter (the censor, the B-brain watching
the A-brain) but never specified the operator by which whole agents *combine*; the tradition that
followed supplied one, but only at the node level, and broadly in the connectionist register — a soft
vote over a narrow space of specialists, not over knowledge.

The speculative move is to keep the architecture intact and **lift the unit of composition from the
coefficient to the entire understanding.** A single run of the companion understanding stack [1] emits a
*crystallized* object — an elaboration graph: the entities, the derived-but-unstated facts, the
recognized frames, the rules the run learned. That crystal is a K-line in Minsky's exact sense [8] — a
stored pattern that completes a partial cue — and it is *already serialized*, the artifact every run
produces. So the agent need no longer be a term-specialist; it can be a whole read of *Macbeth*, of a
failed venture, of a clinical case. The society becomes a **society of understandings**, and composition
happens over units of human knowledge, symbolically, rather than over coefficients beneath them.

The operator Minsky left implicit, made explicit, is `union → correspondence → coherence-gate`. *Union*
overlays the crystals' graphs. *Correspondence* aligns their entities and relations — that a usurper's
`doomed` in one crystal answers to a founder's `overreaching` in another — and this is the load-bearing
unsolved step: it is the analogy/precedent problem the companion stack [1] names as its one real
remaining build, and without it composition is noisy set-union, mush. *Coherence-gate* is the arbiter,
and it is already in hand: the same coherence-veto that certifies a single understanding [1], lifted to
the *seam between crystals*. Almost no composition coheres; the rare ones that do are exactly the
cross-crystal inferences worth having — a rule that recurs across many crystals self-promotes (the
cross-genre promotion gate, generalized), and a structure shared by two is the analogy itself (the
WarGames port: extract `no move wins` from one crystal, map it onto another). The combinatorial
explosion of "compose all permutations" is bounded the same way: not enumerated, but coherence-gated,
the non-cohering majority pruned by the validator the stack already runs — chaos with an attractor.

Everything else transposes unchanged, which is the tell that this is the same paper and not a new one:
the near-miss censor [9,10] forbids incoherent joins; the resemblance memory [6,7,8] recalls which
crystals tend to compose; the regime key [8] keeps incommensurate domains from contaminating one
another; the honesty-by-abstention [10] reports when no coherent composition exists rather than
fabricating one. Only two things change, and they are the whole point: the **unit** shifts from
coefficient to understanding, and the **goodness signal** shifts from the loss-gradient to the
coherence-veto. It is composition over symbolic knowledge with an auditable operator — the one thing the
fitting regime genuinely does well (fuse many signals into one) performed *without going neural*, at the
scale where neural normally wins. The lineage, then, is exact: the Society of Mind named the society but
could not compose it; the law-structured networks of this paper compose, but only at the specialist-node
level, in the connectionist register; the extension composes at the level of *whole understandings*,
symbolically, with coherence as the arbiter — a narrative Society of Mind. Working name: **Continuation**
(Genesis emits the origins; Continuation is the society they form). The honest seam is the one named
above and not pretended away: the correspondence step is unbuilt, and the value of the whole rests on it.

---

## References

[1] R. Vinaik. *Understanding, Mechanized: Reviving and Extending Winston's Strong Story
Hypothesis.* Companion paper, this collection. (The deterministic understanding stack — the GSE
semantic compiler and the revived Genesis engine — and the near-miss / coherence mechanisms reused
here at the level of physical state.)

[2] R. Vinaik. *Two-Faced Meaning: A Relational Account of Irony, Humor, and the "Subjective" Tail
of Machine Understanding.* Companion paper, this collection. (The two-faces-plus-comparator form; the
contamination argument that one face must stand outside the fit; the coherent-replicate conditioning
of §9 is its data-level instance, kept upstream of the engine.)

[3] C. Rackauckas et al. *Universal Differential Equations for Scientific Machine Learning.*
arXiv:2001.04385, 2020. (Embedding a learned term inside a fixed mechanistic differential equation;
loss measured at the composed, solver-integrated output — the grey-box discipline this paper pushes
into a specialist topology.)

[4] M. Raissi, P. Perdikaris, and G. E. Karniadakis. *Physics-Informed Neural Networks.* Journal of
Computational Physics 378:686–707, 2019. (Hard-coding a differential operator as a residual; joint
learning of solution and unknown coefficients in the inverse problem.)

[5] M. Cranmer et al. *Lagrangian Neural Networks.* arXiv:2003.04630, 2020. (The known
Euler–Lagrange form wired into the graph; only the scalar Lagrangian learned; conservation as a
structural consequence, not a penalty.)

[6] B. Gusmão and A. Medford. *Maximum-Likelihood Inverse PINNs and Delta-Method Uncertainty.*
Computers & Chemical Engineering, 2024 (arXiv:2304.05991); and the universal-ODE identifiability
analysis, npj Systems Biology and Applications, 2025. (Principled, hyperparameter-free data-vs-physics
balance; first-order covariance propagation through the law; the over-flexible-learned-term
identifiability hazard that the composed-specialist decomposition makes structural.)

[7] P. Kanerva. *Sparse Distributed Memory.* MIT Press, 1988; and *Hyperdimensional Computing.*
Cognitive Computation 1(2), 2009. (Similarity-addressed, reconstructive memory offered as a model of
human long-term memory; the hypervector substrate.)

[8] M. Minsky. *K-lines: A Theory of Memory.* Cognitive Science 4(2), 1980. (Stored patterns that
complete a partial cue — here realized as hypervectors rather than activation sets.)

[9] P. H. Winston. *Learning Structural Descriptions from Examples.* MIT AI-TR-231, 1970. (The
near-miss learner; concept boundaries carved by the examples that just fail.)

[10] M. Minsky. *The Society of Mind.* Simon & Schuster, 1986. (Specialists scoped to their own
distinctions — the first-order agents the law is decomposed into — and censors that veto inferences.)

[11] J. Berg and M. Newson. *True Stratigraphic Thickness and the Forward-Model Correlation of
Horizontal Wells.* URTeC-2013-121, 2013; and ROGII Inc., *Geosteering by Synthetic-Log Matching,*
US Patent 11,480,045 B2. (The inclination-dependent measured-depth-to-stratigraphic-thickness map;
the per-segment dip search maximizing a shape-plus-smoothness correlation — the response and
geometry specialists of §4.)

[12] Y. Kuramoto. *Chemical Oscillations, Waves, and Turbulence.* Springer, 1984. (Coupled-oscillator
synchronization; the order parameter as a coherence measure — here, over a field of replicate systems
sharing a structural rhythm, used to gate the input-conditioning of §9.)

[13] R. Vinaik. *Smeared Balanced-Ternary Codebooks for Continuous Values.* GSE substrate
engineering notes, this collection. (Sub-bin-resolution hypervector encoding of continuous signals;
the shared representation in which the data, the memory keys, and the vibed coefficients all live.)
*[Citation detail to be finalized against the GSE engineering record.]*

[14] L. Anselin et al. *Spatial Regimes Models.* Journal of Spatial Econometrics, 2023. (Block-diagonal
per-regime coefficients identified without cross-contamination; optional shared/varying split.)

[15] S. Sugasawa and D. Murakami. *Spatially Clustered Regression.* Spatial Statistics 44:100525,
2021. (Region-wise-constant coefficients via a K-means-like penalized likelihood with a spatial
neighbor penalty.)

[16] R. A. Jacobs, M. I. Jordan, et al. *Adaptive Mixtures of Local Experts.* Neural Computation
3(1), 1991. (Soft, learned gating routing inputs to regime-local experts; the learned-boundary
alternative to hard stratification.)

[17] D. Kleyko et al. *Regression in Hyperdimensional Computing / Vector-Symbolic Architectures.*
arXiv:2112.15424, 2021. (Storing and recovering continuous-valued mappings in a high-dimensional
distributed memory — the mechanism by which the vibed coefficients are held and recalled.)

---

*Status: framework proposal with running components. The law-structured forward-model inversion (the
composed first-order specialists), the near-miss censors, and the similarity-memory completion are
built and tested against held-out wells; the coherent-replicate input-conditioning — a downstream
refinement, not the engine — is specified and its replicate-density precondition measured and strong,
with the field-coupled surface fit, the Kuramoto gating, the regime stratification, and the
delta-method uncertainty named as the immediate engineering the framework organizes. Developed
against the geosteering inverse problem; the buildable design is recorded in the companion
`DESIGN.md`.*
