# Resolving the two objects: markers from anatomy, a told sign, two lenses

2026-10-10. Fable and Codex on the port; a miner on §6 and another on §8. The lead's reading was
right in frame and wrong at step 3, and the correction is the mechanism.

## The lead's error: markers from maxima

The lead proposed: watershed the negated squint, take the two largest basins, name them femur and
tibia. Three sources say no, independently.

- **The thesis (§6.2):** "Two centers alone do not make two cells, nor does one center make one
  cell." Figure S5 gives the counterexample: two bodies each holding two centres, one called two
  cells and one called one.
- **Codex:** "A watershed basin is territory held by an intensity extremum. It is **not
  automatically a bone**... 'the two largest' can select muscle, merge neighboring structures, or
  favor the patella over a partially imaged tibia." And: "**two anatomically supported objects
  first; their intervening intensity relation second.**"
- **Fable:** seeding with every local maximum "over-segments each marrow block (marrow is textured
  even at 8x8)", and subcutaneous fat is "a third bright mass on PD, wrapping both", the patella a
  fourth.

## The fix: the markers come from anatomy, and the sibling's own tool finds them

> "N = 2 and the told axis let you skip discovery: take the leg's **central third across its
> width**, median each row into a **1-D profile along the header's S/I axis**, and **`read_dips` in
> one dimension** finds two broad plateaus and the deepest dip between them, depth in noise units.
> Seed the 2-D watershed with exactly **those two plateau interiors** as markers; the basins are
> then the femur's and the tibia's territories and the saddle set between them is **the seam as a
> curve**, with a depth profile along it, not a row."

> "**Marker-controlled watershed with anatomically supplied markers is still the sibling's
> machinery; only the marker source changes.**"

So the sibling's `read_dips` runs in **one dimension** to find the markers, and the 2-D watershed
then runs marker-controlled. Nothing is invented; the discovery step is replaced by what anatomy
already tells us.

**Free landmark, and a hazard:** "The physeal scars appear in the same profile as shallower dips a
few cm from the joint: a second landmark pair for free, and a false-seam risk."

**And it closes the registration problem:** "**The seam is the registration landmark rounds 1-3
hunted by intensity; align seam to seam.**"

## The polarity: ONE algorithm, a TOLD sign, TWO readings

This answers the founder's open question, and the answer is not "flip the sign and carry on".

The algorithm ports: run the same marker-controlled watershed on `+v` for fluid-sensitive
(dark-seeking basins), and the saddle is the ridge; `depth = saddle − the higher plateau`, in noise
units. **The sign comes from the header's fluid-sensitive / fat-sat flag — told, never inferred
from pixels.**

But what the two seams *measure* is physically different, and they must stay **two columns, never
merged by a sign flip**:

| weighting | the seam is | what it contains |
|---|---|---|
| anatomy (PD) | a **valley** | the **cortex-to-cortex interval**: cortex, menisci, cartilage, a fluid film — one broad dip at squint scale |
| fluid-sensitive | a **ridge** | **cartilage and fluid only** — cortex is dark on *both*, so the profile reads marrow (mid) → cortex (dip) → **ridge** → cortex (dip) → marrow (mid): a ridge **flanked by two dips** |

**The check that the two seams are the same seam** is their width difference: about twice the
cortical thickness plus the menisci at the periphery.

**And their disagreement is where the information lives:**
- fluid **raises the PD valley floor** and **widens the FS ridge**;
- marrow oedema puts **a dip inside the PD plateau** and **a bright shoulder on the FS plateau** at
  the same place.

### The two weightings make a tissue truth table

Per place, the pair (PD digit, FS digit) identifies tissue — a 3x3 truth table, which is the
carrier's own form:

| tissue | (PD, FS) |
|---|---|
| fat | (+, −) |
| fluid / oedema | (0 or −, +) |
| cortex / meniscus / ligament | (−, −) |
| cartilage | (0, +) |

Two ternary digits from two lenses, conjoined, name the tissue. Neither alone can.

## N is a per-slice table, not the constant 2

| where | N |
|---|---|
| sagittal, medial condyle | 2 (femur, tibia) |
| sagittal, midline | 3 (+ patella; the notch and the cruciates sit in the femur) |
| sagittal, lateral | 3–4 (+ fibula) |
| coronal, mid | 3 — **the femur forks into two condyles at the joint** |
| coronal, posterior | 4 (+ fibula) |
| axial | one bone per slice; patella + trochlea in-plane at the trochlea |

Knowing N lets the method **seed with N markers and stop**, so no merge bar is needed; attach every
free basin to a seed by its **shallowest** seam; name objects by **told direction** (superior
femur, inferior tibia, anterior patella, lateral-inferior fibula); and **expect seams by
orientation** — the joint seam is crossed moving S/I, the notch seam moving M/L, the patellofemoral
seam moving A/P. So **a seam where none is expected is a reading, and a missing one is a reading.**

It must abstain on: slices where observed N is below expected (stating what *is* present); the
joint-versus-physis choice when depths are comparable and the FS twin is absent (the physis is dark
on both, the joint bright on FS, so **the twin resolves it**); the identity of an extra basin
(loose body, cyst, fragment) beyond its position; and **all meaning — it resolves where, not what
is wrong.**

### A caveat on the Scissors, from the §8 miner

Two premises the lead handed the consultants are **not in §8**. The phrase "under a contract of N"
appears only as "**The contract of N is never a quota: the Scissors make no part the light will not
give**", and "out of focus" is not in the §8.2 heading — it belongs to the *Noise* branch.

More importantly: in the sibling, **N comes from the expert's call** ("Several, N"), not from
anatomy. §8 never defines N as a count of present objects. So **N-from-anatomy is a port, not a
lift**, and should be recorded as the knee's own move.

The Scissors' stated criterion is: "the most obvious places, **the valleys between its centers**,
read in part from **its waist and its dome links**" — which lines up with §6's waist rule.

## Closure: two fills, and neither reclassifies anything

> "fill holes in the **air** mask (speckle inside air is air) and fill holes in the **leg** mask
> (every enclosed dark region inside the contour is leg). The operation answers only **inside or
> outside the body**; it never says tissue versus background by intensity, so **cortex, menisci,
> ligaments and the joint line stay inside the leg**."

Two guards: air is the dark border-connected component **after a morphological opening at the tile
scale**, so a thin cortex touching the frame edge where the FOV cuts the bone is not swallowed into
air; and exact zeros are fill by definition.

Codex adds the decisive constraint: **"filling a bone's support must preserve its internal dark
readings. Otherwise a fracture would disappear from the representation."** Fill the *mask*, never
the *values*.

## The relation, measured — all in mm, degrees, noise units and counts

**The seam:** depth profile along its arc on each weighting; position along the told axis and tilt
to it; curvature (the condyle's dome radius in sagittal, the plateau's concavity); **width at half
depth as a profile along the seam** — joint-space thickness per compartment, medial against lateral
in coronal, anterior against posterior in sagittal — with its minimum and where it sits; the
shallowest point of the PD valley and of the FS ridge together (cartilage thinnest, bone on bone).

**The facing surfaces:** the femoral-side and tibial-side shoulders as curves; their separation
d(s); **congruence** = variance of d(s); **parallelism** = angle between local tangents;
**interlock** = how far the femur's inferior extent sits below the tibia's superior extent across
the leg.

**Alignment:** angle between the two shaft axes (each basin's principal axis away from the joint) —
varus/valgus in coronal, flexion in sagittal; tibial slope.

**Translation:** centroid offset perpendicular to the axis; in sagittal the posterior tibial edge
against the posterior condyle (anterior tibial translation); in coronal medial/lateral shift.

**The interstitial object:** the FS ridge territory's area per slice and volume per stack, and its
extent *away* from the bone-to-bone interval — superior-anterior into the pouch, posterior into the
fossa.

**Within-object:** dips and bright patches inside each plateau, with their (PD, FS) signature,
count, extent, and distance from the seam.

**Symmetry:** every quantity medial against lateral about the notch.

**Per stack:** one connected saddle surface or several; its area; depth mean and variance; the seam
count along the axis with positions and depths (joint, physes, anything else).

## What breaks

| break | what happens, and the handling |
|---|---|
| **flexion** | the profile along header S/I crosses the seam obliquely, so the dip broadens and shallows; re-profile along the seam's **own normal** after a first pass. Engineering |
| **rotated frame** | the header's cosines handle it; the leg's principal axis is a **concurrence check**, and disagreement is a code, never a silent pixel override |
| **patella** | taken as a bone by "largest masses"; excluded by the central-third seed rule, named by A/P; **its own seam is a second relation** (PF OA), and in axial it *is* the in-plane pair |
| **severe effusion** | the FS ridge balloons into a territory and the PD valley floor rises. A break only if the seam is assumed thin — so **the seam is a territory with a width profile**, and the two weightings disagree exactly as fluid should make them disagree |
| **fracture** | a seam crossing one plateau with an oedema signature; keep the free basins and the merge path so the **intra-bone seam's depth is reported**. A displaced fracture gives two fragments with their own seam, named by axis and size, identity abstained |
| **axial** | the tibiofemoral relation lies **along the stack normal at 3–5 mm per slice**, readable only as a slice-level position; **the in-plane relation is patellofemoral**; abstain beyond that |
| others | the physeal scar as a false PD seam (the FS twin resolves it); the notch splitting the femur in coronal (orientation resolves it); metal voids after ACL reconstruction; FOV truncating a plateau (abstain on that shaft axis); red marrow in young knees as within-plateau dips; osteophytes reshaping the facing surfaces — **a reading, not a break** |
