# Consult: `knee.lenses.witnesses` — what a witness IS, and how one is admitted (2026-10-11)

READ-ONLY. Do not run any command and do not read any file. Answer from this text alone.

## The frame, which you must not reframe

Classical-AI, **no machine learning**: no CNN, no transformer, no fitted weight, no learned
embedding, no "small learned component". RSNA Knee Abnormality Detection, 12 binary findings,
macro ROC-AUC. Laws that bind any answer: **decide or abstain, unknown is never false**; a missing
reading is **silence**, never a negative; **no level is ever chosen to separate the gold labels**;
every bar a decision reads is an **argument**, never a constant inside it.

## Where this sits

A finding is a **predicate violation on an object, or on a relation between objects**. An interstice
is *constructed* between facing objects, never detected. The `lenses` stage writes every place as
**balanced-ternary digits against named witnesses**, so a tissue class is a **conjunction of rows**:

    fat = bright(non-FS) ∧ dark(FS)     fluid = bright(FS) ∧ bright(T2) ∧ dark(T1)
    cortex/tendon/ligament/meniscus = dark on everything
    cartilage = intermediate: always below fluid, always above meniscus

Built and pinned already: the noise law and a Rician variance-stabilising transform (one "flicker" =
one sigma at any intensity); `digit_code`, which places one reading against one witness with a band
of `k·sqrt(place_sigma² + witness_spread²)`; and `slab_code`, the through-plane rule — a series is a
stack of **slabs**, so a place inside a foreign slab IS measured and a place in the gap is silent.

**Everything now rests on the witnesses.** A digit is meaningless if its witness is not what it
claims to be.

## What you both already told me, and which I accept

- My first bootstrap — "subcutaneous fat is the band just inside the leg boundary" — **fails**. That
  band holds **skin** before fat, plus fascia, vessels, scar; over the patella the subcutaneous layer
  is a millimetre or two and the band reaches tendon or cortex. **Position establishes peripheral
  soft tissue, not fat.**
- The mechanism that makes this urgent is **coil falloff**: a surface array is brightest at the
  periphery, where subcutaneous fat sits, and dimmest centrally, where marrow and the intercondylar
  structures sit. So a single per-series middle is still "an absolute level with respect to
  position" — the failure that killed four intensity instruments on this corpus, in a new coat.
- The remedy: **three fat witnesses at three radii** — subcutaneous (touching air), **marrow** (the
  interior of an already-resolved B1 dome, bounded by dark cortex), and **Hoffa's fat pad**
  (constructible as an interstice, which is this project's own tier-2 move). Their **disagreement is
  the bias-field measurement**.
- A witness must be allowed to come back **absent**: "a reference manufactured by necessity would
  undermine every later row."
- **Estimation precision and population heterogeneity are different failures.** "A heterogeneous
  mixture can yield a very precise median and still be an invalid reference. Do not hide that failure
  by widening the ternary band."
- The witness population and its middle must be **fixed before any target object is evaluated**, or
  an abnormal target moves its own standard.

## My own design, written before asking you

**1. A witness is an OBJECT, not a region of intensity.** It is resolved structurally, admitted by
stated criteria, carries its own location *and* spread, and may be absent. It is never "the places
that look like fat", which would be circular.

**2. Admission is a three-step sequence with named codes at each step**, so a failure says which step
refused: `structural candidate → acquisition evidence → admitted witness`. A candidate that passes
structure but fails evidence is a different fact from one that never had a candidate.

**3. The three fat witnesses are a THREE-LEGGED STOOL**, which is this project's own named principle
(founder, 2026-10-10): *"when sources of truth are defined as correct but are incomplete but
overlapping in their coverage, then the places in which they seem to disagree are not noise to wipe
away, but are some of the MOST informative information we can have."* So I would NOT average the
three into one fat level. I would keep three rows, and treat their disagreement as the bias-field
reading — a measurement the stage emits, not an error it resolves.

**4. Each witness is found by structure that is already resolved**, never by intensity:
- *subcutaneous*: the compartment between the skin envelope and the first dark line inward (fascia),
  seeded only where the boundary is **against air** and not against the frame edge — our
  air-connectivity mask gives that distinction for free;
- *marrow*: the interior of a B1 dome, which is by construction bounded by dark cortex;
- *Hoffa's*: the interstice bounded anteriorly by the patellar tendon's dark band and posteriorly by
  the femoral trochlea;
- *muscle*: a large compartment touching neither air nor a bone interior, bounded by fascia — not
  "the biggest non-bone thing", which is not an identity;
- *fluid*: I would **not** admit a fluid witness at all, because a distended recess is itself a
  finding (effusion) and using it as a standard entangles the witness with a label. The table does
  not need one: fluid is *above fat on FS*, *above muscle on non-FS T2*, *below muscle on T1* — all
  statements against witnesses that exist in every knee.

**5. The middle is per slice where the witness has enough places, falling back to the series**, with
which was used recorded as provenance — because a per-slice median tracks the bias field along the
stack, which is the thing a single series-wide number cannot do.

**6. Eligibility requires physical support, not a count of pixels.** A witness place is eligible only
if a native measurement support fits inside the compartment; a one-voxel-wide sliver of fat is
partial volume, not fat.

## What I am asking you

Be concrete and specific; a general caution is worth nothing here.

1. **Attack the admission criteria.** For each of subcutaneous, marrow, Hoffa's and muscle: where
   does my structural definition admit something that is not that tissue, on a real knee MRI? Name
   the case.
2. **The circularity I may not have escaped.** Every criterion above is structural, but "the first
   dark line inward" is itself a reading. Is there a genuinely non-circular order of operations, and
   if not, what is the smallest honest circularity to accept and declare?
3. **Homogeneity without a tuned threshold.** A witness must be refused when its population is a
   mixture, and I may not pick a cut to make that work. What deterministic test admits or refuses a
   witness population, stated in units the noise law already provides?
4. **Is refusing a fluid witness right?** Or does something in the knee give a fluid standard that is
   not also a finding?
5. **Three rows or one?** Should a place be stated against its *nearest* fat witness (one row,
   provenance recording which), or against all three (three rows, the conjunction consuming them)?
   The three-legged-stool principle argues for three; compute and sparsity may argue for one.
6. **What breaks first at scale?** Of everything above, which assumption fails earliest across 58
   studies from mixed scanners and protocols, and what would the failure look like in the output?
7. **What am I not asking that I should be?**

Answer in prose with headed sections. Distinguish what you know from what you are inferring, and say
plainly where you are uncertain.
