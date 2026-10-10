# The dome, the waist, and what actually parts two objects

2026-10-10. A miner read §6 and §4 whole; Codex answered on the port. Both correct the lead's
framing in the same direction, and the correction is load-bearing.

## The lead had the dome wrong, and said so to both consultants

The lead described the dome as "a bright centre with a **discrete fall-off in signal intensity**
that marks the border". §6.2 does not say that. Its territory is set by **distance alone**:

> "It is a cheap prior, **drawn by distance alone**, and it never decides alone: where it errs is
> information (§1.2)."

> "**Nothing is cut on strength**, so a bright nucleus never silences a dim one."

> "Each place goes to its **nearest center in the plane**."

No intensity, gradient or fall-off criterion bounds a territory. And the word "discrete" appears
nowhere in §6 or §4 — **the stated unit of knowability is one flicker of the camera.**

## There are two separate "dome" things, and §4.2 says so outright

> "The figure's first row marks where each picture is **domed**: where the light at a place
> outshines its surround at a nucleus's scale, a bright center over a darker surround, as over a
> nucleus... **The dome of §6.2 is a different thing: the territory of places that one bright
> center holds.**"

- **"domed"** (§4.2): a *shape reading* — a bright centre over a darker surround, at the object's
  scale. §4.2 names no operator.
- **"the dome"** (§6.2): a *territory* — the places a centre holds, by nearest centre in the plane.

The **centres** do have an operator (§6.2): "the peaks of the **negative Laplacian of a Gaussian
blur at a nucleus's scale** (Marr and Hildreth, 1980), a response that is **positive exactly where
a place outshines its surround**."

## What actually tells two touching objects apart: THE WAIST, at one flicker

This is the answer to the founder's question, and it is in §6's preamble and §6.1.

> "Read as a relief of light, a nucleus is a peak. **Its border is where the peak falls to its
> surroundings, and a valley is where one \<object\> ends and the next begins.**"

> "An oval laid over the body would give a border of sane length, but it would erase a dumbbell's
> waist, and **the waist is how two touching nuclei are told from one**."

> "a dumbbell **whose waist is deeper than the flicker** keeps its waist and its two centers, and
> reaches the Scissors whole."

So: **a valley is where one object ends and the next begins, and the waist must be deeper than one
flicker** — deeper than the noise. That is the criterion, and it is a measurement in noise units,
not a threshold on brightness.

For the knee the founder's point lands exactly: the joint space is the valley between two peaks,
and it is enormous rather than marginal. "two GIANT fucking objects that almost precisely split the
picture right in the middle."

The pull-taut is deliberately engineered **not to erase the waist**, which is why §6.1 constrains
the oval pull.

## Centres are EVIDENCE, never identity — both sources agree

The thesis (§6.2):

> "**Two centers alone do not make two cells, nor does one center make one cell.** Where the dome
> link and a call disagree, the disagreement is evidence, kept beside the call."

Figure S5 gives the counterexample outright: two bodies each holding two centres, and "The expert
called the first two cells and the second one cell."

Codex, independently, on the knee:

> "A watershed basin is territory held by an intensity extremum. It is **not automatically a
> bone**... 'the two largest' can select muscle, merge neighboring structures, or favor the patella
> over a partially imaged tibia."

> "**two anatomically supported objects first; their intervening intensity relation second.**
> Watershed can contribute to both readings, but its territories cannot be accepted as bone
> identities merely because there are two large ones."

**So the lead's step "take the two largest basins and name them femur and tibia" is wrong.** A basin
is a candidate; identity needs contiguous closed extent and continuity through the stack.

## §6 states the evidence and the law, and withholds the parting

Parting is deferred by name to §5.3, the Scissors (§8.2) and the clean-up (§10.5):

> "A body can be wider than a nucleus, where several nuclei pressed together stand out as one
> region, and **no body is parted until after the take** (§5.3)."

In depth (§6.4): "**A dip followed by a rise is the valley before another cell.**" The band walk
"walks down each side while the light stands above one flicker. Where the light **rises again by
more than one flicker past a dip**, the band ends at the dip."

## The polarity question, answered with its condition

The founder's open question: on the anatomy sequence the bones are bright and the seam is a dark
valley; on the fluid-sensitive sequence the joint space is bright, so the seam is a **ridge**. One
machinery with a sign flip, or two readings?

Codex's answer, with the condition stated:

> "**the signed measurement ports; unconditional sign-flipped extraction does not.**"

With intensity u in noise units and w = p·u (p = +1 for bright interiors and a dark seam, p = −1
for dark interiors and a bright seam), the sibling's calculation is unchanged:

    D = min(w_peak_A, w_peak_B) − w_saddle

> "the same watershed machinery works after sign reversal **when the bone interiors actually become
> the relevant extrema and the joint ridge separates their territories**. Fluid-sensitive weighting
> does not guarantee that condition. **Cortical rims remain darker than marrow, so negation can
> seed cortical outlines rather than bone interiors.** Fat, muscle and fluid collections supply
> other extrema."

> "**Weighting declares the expected polarity; measured profiles across the identified facing
> surfaces verify it.** When the extrema condition fails, retain the bone-boundary reading and
> measure the bright interstitial profile between those boundaries. **Do not force an intensity
> basin to become the object.**"

So: the *measurement* ports with a sign; the *extraction* does not port unconditionally. The
polarity is declared by the weighting and **verified by measurement**, and where it fails the
reading falls back to boundaries and the interstitial profile rather than forcing a basin.

## The superior direction, in physical coordinates

Codex: for slice normal n, the in-plane superior direction is proportional to

    e_Z − (e_Z · n) n

the projection of superior onto the slice plane. "**When this approaches zero, superior-inferior
separation is not available within that plane**" — which is the axial case, and why an axial view
shows no joint line. A two-basin superior/inferior split **must abstain** there.

## Closure fills support, not meaning

> "Keep the original intensities and the filled-hole mask **separately**. Filling says 'inside the
> leg envelope,' **not 'air,' 'normal tissue,' or 'irrelevant.'**"

> "**filling a bone's support must preserve its internal dark readings. Otherwise a fracture would
> disappear from the representation.**"

That last is decisive: fill the *support mask*, never the *values*, or Fracture — one of the twelve
— is erased by the very step meant to clean the field.

## The seam is a collection of readings, not one number

Codex's list, all label-free and measurable on the relation itself: **separation** (local physical
distance and its variation along the interface), **orientation** (angle between facing normals),
**congruence** (opposing curvature, shape difference), **position** (interface centroid and extent
relative to both bodies), **multiplicity** (connected components, branches, interruptions),
**profile** (signed contrast, width, extrema across the band), **support** (observed fraction,
coverage, continuity through slices).

> "The joint is a **finite interstitial region** containing cartilage, menisci and fluid — not
> necessarily one infinitesimal line."

## Failure modes named for this port

| break | what it does |
|---|---|
| **flexion** | superior-inferior ordering no longer describes the facing relation; read local body directions, never screen position |
| **rotation** | corrected by DICOM physical coordinates; treating image rows as superior-inferior is an engineering error the lead already made |
| **patella** | can become a dominant basin, especially with a cropped tibia; size ranking cannot establish identity |
| **severe effusion** | bright fluid can extend beyond the joint and dominate a fluid-sensitive watershed; the inter-bone relation stays defined by facing boundaries |
| **fracture** | can split one bone's territory into several basins; preserve the internal seam, never erase it to obtain two components |
| **axial view** | the projected superior direction may vanish; abstain |
| **thin cortex, thick slices** | partial volume can prevent a closed boundary being observed; report incomplete closure rather than inventing the contour |
