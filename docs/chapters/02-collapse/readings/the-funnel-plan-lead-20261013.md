# The funnel, as a plan: the lead's reading, written before the Codex consult

Date: 2026-10-13. The founder confirmed the lead's statement of the epistemology and workflow
("Excellent work! For once, you actually AREN'T wrong about this! This is the correct epistemology
and workflow.") and asked for a plan: "I'd like to plan it out properly. Work through this, send off
a codex consult (do big-boy consult; GPT-6 Astra on Max). Once it's set, then let's work through a
RIGOROUS and unambiguous plan to implement, then fire it off with a workflow or something to plow
through it as mechanically as we can." His words of this session are verbatim in `../teachings.md`.

This file is the lead's own reading, written before opening the consult's answer. It is one reading.
Where it goes beyond his words it says so.

## 1. What he said the pipeline is, in his words

- The first lens resolves background versus leg, **per view**, and its authority is being correct:
  "We make a lens that looks for what we define as background, and when it works and only finds
  things that aren't bones or other anatomical features, then it works and we use it." Once right on
  all five views, "we should NEVER spend a SECOND of compute on this ever again."
- Two jobs at two resolutions: "(1) high-level localization and targeting, and (2) fine-grained
  targeting and boundary-drawing. The 'squint' view is WAAAAY cheaper." "you only spend expensive
  compute to try and find the exact boundary of things in the places where they actually look like
  they might exist." "Why compute vectors and shit where we know the knee isn't?"
- The two acquisitions of one orientation are lenses "given to us for free, by the competition
  itself", and they line up by place on the knee: "the squint is how you make it cheap, you just
  kinda...line it up. That's all. The lenses, the actual analyses do the actual line-drawing and
  precise resolution. But for information, to help understand the significance, and eventually to
  diagnose the condition? It's the same fucking image, just sorta scootch it a bit, and you're good."
- The objects are grounded at interior peaks: the "interior peaks" picture "is VERY useful for
  specific selection of <object>s that are potentially significant, treating them as physical
  objects that are grounded and connected as a singular whole, will be useful for diagnosing; i.e.,
  what is 'wrong' with the coherent object that is grounded to those interior peaks".
- Where the expensive work runs is defined "by looking at it (common-sense border estimation) and by
  using domain knowledge for where these elements are supposed to be on these really fixed and
  almost identical-looking images".
- The scope: "I only talked about the tibia/femur, we need to be able to resolve ALL of the relevant
  anatomical objects to diagnose between the 12 conditions the competition asks us to resolve."
- The engineering shape he specified: "performance engineer, SICP-style, one compute operation per
  script, paralelizable compute, shared information, superposition of lenses resolving meaning".
- Nothing is removed: "don't delete/remove lenses"; "Keep all".

## 2. The settled record this plan is written inside

From `docs/OBJECT_MODEL.md` and `docs/PIPELINE_AS_OBJECT.md`, settled with him on 2026-10-11 and
2026-10-12, and not reopened here:

- A finding is a predicate violation on an object, or on a relation between objects. An interstice
  is constructed, not detected: it exists the moment its two bounding objects do. Compartments are
  enumerated by which surfaces face each other.
- Anatomy lives in the design, never in the record. Objects are indexed; what selects an object for
  a rule or a predicate is a structural fact an earlier stage computed (what is superior, what is
  anterior, what lies across, whether a ring closes), never a kind-label. "Femur" in this file is a
  design gloss.
- The lens axis is the acquisitions. A tissue class is a conjunction of digits across acquisitions,
  never a threshold on one image (the table in `OBJECT_MODEL.md`: fat is bright on the non-fat-
  suppressed and dark on the fat-suppressed; fluid bright on the fat-suppressed; cortex, tendon,
  ligament and meniscus dark on everything; cartilage intermediate; marrow edema dark on T1 and
  bright on the fat-suppressed, inside a bone). The digits stay separate; a question reads the
  conjunction.
- Laterality: the frame gives superior and anterior; the fibula is the sign for lateral; with no
  witness, medial and lateral abstain with a named code.
- Every stage renders what it resolved; the renderer only arranges. Measurements, decisions and
  orchestrations are kept apart; a decision returns a named code and every bar is an argument. A
  reference exists before any accelerated twin. Nothing is deleted: a cleared place keeps its
  readings, and the clearing is a decision kept as a record.
- The twelve, from the competition's own file: ACL, MCL, Medial Meniscus, Lateral Meniscus, Medial
  OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's, Contusion, Fracture.

## 3. The plan: the funnel, round by round

The route keeps its nine names (study, collapse, lenses, objects, relations, ownership, vectors,
predicates, output). What changes is scale, scope and order: every stage after the first lens
computes only inside what the stages before it left, the squint does the targeting, native
resolution is spent only along edges, and the objects are found in rounds, each round located by the
objects the round before resolved. Each step below is one compute operation, or a few, each a pure
function of kept readings, parallel over series, tiles or objects, computed once and consulted.

### Step 0. The study, as now

Consumes the competition's files. Produces each series at stored fidelity with its geometry in
millimetres from the header: pixel size, slice position, orientation, and the sequence type read
from TR/TE/flip angle/inversion time. Adds one fact the funnel needs: which series are the two
acquisitions of one orientation (fat-bright and fat-dark), paired. Exists today (`knee.study`).

### Step 1. The squint, per series, in millimetres

Consumes a series. Produces the tile grid, each tile the median of its places, with the tile's
centre in the scanner's millimetres. The tile size is declared in millimetres, not pixels, so that
a tile on one acquisition and a tile on the other cover the same patch of knee whatever their pixel
counts. His figure is 16 × 16 on 256 × 256; at half a millimetre a pixel that is a tile about eight
millimetres across. The size is his design constant, declared once with the pattern it encodes
(coarse enough to absorb a millimetre or two of shift between acquisitions, fine enough to localise a
bone), and it is the lead's inference that eight millimetres is what his figure means. Exists today
in `knee.collapse` as a pixel-sized grid; the change is the unit. Picture: the squint over the
acquired plane.

### Step 2. The first lens: background versus leg, per view, at the squint

Consumes one series' squint and that series' own histogram. Produces, per tile, one decision:
`background`, `leg`, or an abstention code, with its reason. The candidate rule: a tile is
background when its median lies at or below the series' own first valley AND it is connected to
the picture's border through such tiles. The second clause is the lead's addition, for the fat-dark
views, where marrow is dark and a darkness rule alone could clear the inside of a bone; connection
to the border separates air, which touches the frame, from a dark interior, which does not. His
check decides: on each of the five views, the lens is right when it marks nothing that is bone or
any other part of the knee. Where a view fails, that view gets its own rule, and the rule's
provenance is recorded. Once right, the reading is frozen: computed once, saved, handed to every
later step, which receives the leg tiles and never computes outside them. The background tiles keep
their medians; the decision is a record, not a discard. Exists today: the valley rule in
`knee.collapse` (`read_regime`), the border-connection idea in the field's structural reading, both
at native resolution; the change is scale and the freeze. Picture: per view, the squint with the
background tiles marked, over the acquired plane, so he can check by eye.

### Step 3. The free lenses, lined up, at the squint

Consumes the two squints of one orientation and their geometry. Produces, for every leg tile, the
tile of the other acquisition that covers the same millimetres of knee (nearest centre, nearest
slice), and for each leg tile one balanced-ternary digit per acquisition against that acquisition's
own tercile edges over its own leg tiles. The digit rule exists today in `knee.lenses` at native
resolution over the whole volume; the change is scale and population: tiles, inside the leg. The two
digits are kept separately. The conjunction of the two is read by the settled table, as a named
code per tile; the names of the classes are his. Where an orientation has one acquisition, as the
axial does on this study, the second digit is silence and the conjunction abstains with a code.
Picture: the two digit grids on the shared frame, side by side, and the conjunction code as colour.

### Step 4. The dome at the squint: the big objects

Consumes the leg tiles, their conjunction codes, and the picture's axes from the header (which way is
superior, which is anterior). Produces the interior peaks and the territories at tile scale, and the
first indexed objects. The dome's height is distance from what is not bone: from background and from
the tiles that are dark on every acquisition (cortex, the gap, tendon). Peaks by prominence, never by
a level; each territory is the tiles that climb to one peak. Then the selection by structural facts,
which is the lead's reading of "no recognition, pure math": on a coronal or sagittal series the two
largest territories are the two big bones, the superior one and the inferior one by the header's
axis; on a sagittal series the small territory anterior to the superior bone's end is the patella; on
a coronal series a small territory inferior to the inferior bone's upper surface, with its own closed
dark ring, is the fibula and the laterality witness. Each object carries its peak, its tiles and the
facts that selected it. Exists today in `knee.objects` (B1: the distance transform, prominence peaks
and watershed, at native resolution over the whole plane, drawn as the "interior peaks" sheet and
panel 11); the change is scale and the mask. Picture: peaks and territories on the squint, and the
selection facts written beside each index.

### Step 5. The edge, at native resolution, only along the edge

Consumes each object's tiles and the native series. Produces the object's boundary, drawn only in a
strip a few millimetres wide along the tile boundary where the territory meets a neighbour, the gap
or the background. In that strip and nowhere else: the native digit per acquisition (the existing
lenses rule, scoped), the native dome and its edges (the existing B1 edges and profile traces, scoped),
and the two acquisitions read against each other at the same millimetres (the existing B2
conversation, scoped). The outline is pulled taut as the thesis's §6.1 says. The strip's width is a
design constant in millimetres with its pattern recorded. Exists today as whole-plane work in
`knee.objects`; the change is scope. Picture: the refined boundary over the acquired plane, the strip
visible, silence drawn as silence elsewhere.

### Step 6. The spaces between: the first relations, and the objects inside them

Consumes the boundaries of the big objects and the facing-pair graph. Produces, for each pair of
facing surfaces, the interstice: its extent between the two surfaces, its walls read as three layers
(cartilage, the dark plate, the marrow behind) by the conjunction digits in the wall strip, its fill
by the conjunction class inside, and its contents: each body of tiles or places inside it that is
dark on every acquisition becomes a new indexed object, located by the interstice that holds it.
This is the second round of the loop: the menisci are the dark bodies at the periphery of the
tibiofemoral interstices (the triangles on coronal, the horns on sagittal); the cruciates are the
dark bands in the notch interstice on sagittal; the trochlear cartilage faces the patella. Compartments
are enumerated by which surfaces face; medial and lateral are named by the fibula witness or
abstained. Exists today in part: `knee.relations` declares the record and carries sampled pairings;
the extent is unbuilt. Picture: each interstice drawn between its two objects, its contents outlined.

### Step 7. The spans and the envelope: the third round

Consumes the objects so far and the leg tiles outside the interstices. Produces: the spans, dark-on-
every-acquisition bodies running from one big bone to the other outside the interstice along the
medial and lateral exteriors (the MCL on the medial side; the lateral structures as its reference);
and the envelope, the fluid-class component connected to the interstices, with its volume, lining
and outline, including the recess above the patella and any outpouching posterior to the bones'
envelope. Each is located by the objects already resolved and the picture's axes. Picture: spans and
envelope over the acquired plane, by index.

### Step 8. The residual, and ownership

Consumes every claim. Produces every place inside the leg owned by one object or named unassigned,
and the residual map: what no object claims, with its conjunction classes. The residual is the next
structure argument, read again if it holds anything object-shaped. Exists today (`knee.ownership`);
the change is that it now runs on a field most of which is already claimed. Picture: the residual.

### Step 9. The bundles, the predicates and the output

Consumes each object's places and digits. Produces the count table per object over the named banks
(`knee.vectors`, exists), then the twelve decisions, each on the subject the object model gives it,
selected by structural facts, each a named code with its reason, abstaining where its subject was not
resolved (`knee.predicates`, exists as twelve abstentions), then the confidences under his declared
projection with the companion record (`knee.output`, exists). The mapping from the twelve to the
objects the rounds must produce:

| finding | needs resolved | from round |
|---|---|---|
| Fracture, Contusion | the big bones, the patella, the fibula; their cortex ring and interior | 1 |
| Medial OA, Lateral OA, PF OA | the three interstices' walls: cartilage over the dark plate, per compartment, opposite compartment as control | 2 |
| Medial Meniscus, Lateral Meniscus | the dark bodies at the periphery of the two tibiofemoral interstices | 2 |
| ACL | the dark band in the notch interstice, its course from one bone to the other | 2 |
| MCL | the medial span | 3 |
| Effusion, Synovitis, Baker's | the envelope: its fill, its lining, its posterior outpouching; the post-contrast flag from the regime | 3 |

The expected reading `e` for each predicate is his to declare, as the record already says.

## 4. The build order, and what each step must show before the next begins

The order is the funnel's own: 2 (on all five views, until each is right by his eye), then 1 and 3
(the squint in millimetres, the free lenses lined up), then 4, then 5, then 6, then 7, then 8, then
9. Each step is built as a unit under `docs/STAGE_CONTRACT.md`'s loop: declared first in the
OpenSpec change; its docstring naming the thesis role and his words; the pure decision first, total,
named codes, bars as arguments; contracts; two-sign intent tests; Detective; wired so something
consumes it; rendered; run on the one real study through the real entry point; gate; recorded. Each
step's sheet goes in front of him before the next step is built, because the picture is the channel
through which he supplies the next lens.

## 5. What stays, and what is not on the route

Every lens that exists stays in the tree, callable and drawable from a saved run: the air and the
closed leg at native resolution, the basins and seam, the darkest tiles and bodies, the whole-volume
digit maps, the whole-plane territories, the whole-plane traces and conversation, the ownership and
pairings as they are. None is deleted. The route no longer calls the whole-field forms; where a step
above reuses one, it reuses it scoped. This is the lead's default under "don't delete/remove lenses",
and whether the whole-field forms stay reachable behind a switch on the route, or only as drawings,
is his to say.

## 6. What the funnel dissolves, and what it leaves open

- The local structural normalisation before the digits, an open ruling: the funnel gives each digit a
  structurally selected population for free, the leg tiles for step 3 and each object's own places
  for step 9. Whether that is the normalisation he meant is his to say.
- The frame for the two acquisitions is settled by his answer today: place on the knee, in the
  scanner's millimetres, at the squint; native only along edges.
- The tile size and the strip width are his design constants, each declared with its pattern.
- The first lens's rule per view is settled by his eye, view by view.
- Which whole-field lenses, if any, return to the route is his.

## 7. The lead's own uncertainties, stated as such

- Step 2 on the fat-dark views: whether the border-connection clause is enough, or whether the dark
  marrow needs the conjunction (step 3) before the leg can be cleanly told from the air. If so, steps
  2 and 3 swap their order on those views, and the first lens reads two acquisitions, not one.
- Step 4 on the axial series, which has one acquisition here and shows the patella and the femur's
  end rather than two long bones: the "two largest territories" selection does not apply as written,
  and the axial may be a view that is located by the others rather than resolving the big objects
  itself.
- Step 6's contents at tile scale: a meniscus is a few millimetres across, so at an eight-millimetre
  tile it is one tile or none. The contents may need the native strip of step 5 widened into the
  interstice, which is still scoped work, not whole-field work.
- The 58-study run comes after the one study shows each step; it is engineering, not the proof.
