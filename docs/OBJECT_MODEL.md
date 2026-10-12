# The object model: what the knee is, and why diagnosis falls out of it

<!-- The settled design, agreed with the founder 2026-10-11. This supersedes the chapter table of
docs/SPINE.md as the project's structure; SPINE.md keeps the way of working. Read this FIRST in a
new session or after a compaction, then docs/chapters/<stage>/README.md for where a stage stands. -->

## Runtime vocabulary and evidence

The later founder rulings in `chapters/02-collapse/teachings.md` distinguish an
`<object>` (a resolved visual subset) from an anatomically meaningful human object.
Anatomy informs the design and the inventory below; runtime subjects are indexed and
selected by retained structural facts. No anatomical naming stage is required. See
[PIPELINE_AS_OBJECT.md](PIPELINE_AS_OBJECT.md).

This document states intended structure. Historical observations below do not certify
current resolution of named anatomy. [PIPELINE.md](PIPELINE.md) maps the actual interfaces;
[the reconciliation evidence](chapters/02-collapse/measurements/documentation-reconciliation-20261012.md)
is a dated run, and `just unit`/source/returned records recompute standing.

## The claim

**A finding is a predicate violation on an object, or on a relation between objects.** It is never a
pattern to be found in a field.

Resolve every element of the knee that matters to its operation, and the twelve findings are read off
the objects by arithmetic. Nothing is searched for. The founder, 2026-10-11:

> "if you actually CAN resolve objects, then 'visual reasoning' is basically common sense + math"

> "the mapping to diagnoses here isn't just statistics, it's *literally* recapitulating the exact
> process that a doctor/radiologist would *themselves* be using for THEIR diagnosis. They THEMSELVES
> would be thinking 'this is the femur, I see a discontinuity in its cohesion, a structural fault,
> this is defined as a "fracture"'"

> "for medical conditions, because of the inherent epistemology of medicine as a field, diagnosis is
> *inherently* mechanical in nature, and diagnosis of physical ailments from scan data is *literally*
> object-oriented reasoning"

This is why the project is not ML and does not need to be. A radiologist is not running a classifier
over pixels; they are naming objects and checking each against what that object should be. The
system recapitulates that procedure, which is the strongest possible form of "it works for a reason".

The reference to **object-oriented programming is deliberate** (founder, 2026-10-11: "I'm being
intentional with the cute reference ... The epistemology and carry-over of the ideation is quite
relevant"). Objects carry invariants; findings are violated invariants; relations are first-class.

## Why the interstice needs no detector — the load-bearing move

The findings that read as "squishy" — effusion, synovitis, OA, meniscus, ligament — are all about the
space **between** bones. That space looks hard to define until you notice what the word means. The
founder, 2026-10-11:

> "'Interstitial space'-related conditions are complex, hard to resolve. It's all squishy oddness.
> But here we can be *precise* about what the interstitial space is like...because its role
> identification is *relative*. Interstitial space...is the space between the two bones we resolve as
> objects! That's LITERALLY what the term means, and here it's *inherent* in the structure of the way
> we build the computer vision project itself!"

> "the role is *definitionally* defined as a *relative* one, because that's literally how the
> physical object works. Its shape, the forces that are acting on it, the shear or crush force, the
> over-fill of fluid or tear or wear in the space is *defined* by how it interfaces with the bones it
> is 'interstitial' to"

So an interstice is **constructed, not detected**. The moment two bones are objects, the space between
them exists as a relation, with its own extent, its own walls, and its own fill. There is no search,
no threshold, and no name to recognise.

The same move kills the compartment problem. Medial, lateral and patellofemoral are not three things
to find: they are **enumerated by which bone surfaces face each other**. A compartment cannot be
missed, because the bones produce it.

## The tiers

### Tier 1 — objects
The elements of the knee, each resolved from the data's own geometry. Bones first, because they are
what the rest is defined against: **femur, tibia, patella, fibula**.

The current geometric instrument is the dome re-derived for bone; its territories are
indexed proposals, not certificates that the anatomical inventory has been resolved. The thesis's centres are brightness peaks because a
nucleus is brightest at its centre; a bone is not an emitter, it is a solid bounded by dark cortex, so
it is **deepest** at its centre. The distance transform replaces brightness as the dome's height
field, and §6.2's law survives: prominence, never a level, so "nothing is cut on strength" and a thin
bone is never silenced by a thick one.

The tier is **not complete**. The goal, founder 2026-10-11:

> "Our goal here is to resolve every single element that is significant in any way to the operation of
> the knee, and thus carries diagnostic relevance."

What remains is the residual, and the method is the cell project's pull-out:

> "this is homologous to the 'pull out' from the cell-tracking project; once you can confidently
> resolve \<object>s in the visual data, the roles that are still unassigned in the visual field are a
> lot easier to figure out, since they're definitionally NOT the things you already DO know how to
> resolve. And since these scans all look SUPER similar...finding ways to get that final resolution of
> every object should be a snap"

### Tier 2 — relations (interstices)
One per facing pair of tier-1 objects. Constructed, never detected:

| interstice | exists because |
|---|---|
| femur ↔ tibia, medial | the femur has two condyles |
| femur ↔ tibia, lateral | the femur has two condyles |
| femur ↔ tibia, intercondylar | the notch between them |
| femur ↔ patella | the patella faces the trochlea |

A relation carries its **gap** (extent across), its **walls**, its **fill** (what occupies it), and
its **contents** (tier-1 objects lying inside it, such as a meniscus or a cruciate).

**A wall is cartilage backed by a subchondral plate — not bone.** Corrected 2026-10-11 after both
second readers reached it independently, which makes it evidence rather than one voice. Fable:

> "'gap narrowed' is a **radiograph concept imported into MRI**. On a non-weight-bearing supine MRI
> the bone-to-bone gap is nearly uninformative. What MRI shows directly is the *cartilage*: two
> hyaline layers, one on each subchondral plate, each with a measurable thickness profile."

So each wall is **three distinguishable objects** — articular cartilage, the subchondral plate (the
dark lamina beneath it), and the marrow behind that — and the OA predicate reads the **cartilage
thickness profile**, not the gap. Full-thickness loss is the plate facing the interstice with no
intermediate layer in front of it. The opposite compartment of the same knee is the natural control,
which is a concurrence with no external threshold.

### Tier 3 — spans
An object attached to two bones and running **outside** the interstice between them. The MCL is the
scored instance: superficial, on the medial exterior, extra-articular. A span is not interstitial
content, and treating it as such was a reading error corrected on 2026-10-11.

### Tier 4 — the envelope (the capsule)
The volume enclosing the articulation, **larger than the union of the interstices** — it includes the
suprapatellar recess, which extends well above the patella. It carries a **volume**, a **lining**, and
an **outline**.

## The inventory: every element that must get an `<object>` role

The goal, founder 2026-10-11: *"resolve every single element that is significant in any way to the
operation of the knee, and thus carries diagnostic relevance."* This is the design inventory, assembled
from both second readers’ answers and checked against the twelve. Bold is historical emphasis,
not current resolution standing; current records do not certify anatomical identities.

**Bones and their sub-objects (T1).** **Femur** → shaft, medial condyle, lateral condyle, trochlea,
notch roof and walls, epicondyles, adductor tubercle. **Tibia** → shaft, medial plateau, lateral
plateau, intercondylar eminence and spines, anterior and posterior intercondylar areas, tibial
tubercle, Gerdy's tubercle. **Patella** → median ridge, medial and lateral facets. **Fibula** → head,
styloid, neck. For each: cortex, **subchondral plate**, marrow (fat vs red marrow), physeal scar.

The watershed already tends to split the distal femur at the notch and the tibia at the eminence,
because both are saddles in the distance field. **That split motivates the intended compartment
enumeration.** A watershed saddle is not by itself a certificate of a complete interstice;
the retained touching-pair census and sampled dark pairings have different scopes.

**The articular layer (new, and the largest omission).** Articular cartilage on the femoral condyles,
trochlea, tibial plateaus and patellar facets, each with a thickness profile; the subchondral plate
beneath each; marginal osteophytes; subchondral cysts and sclerosis. *Needed by all three OA rows,
and by Fracture and Contusion.*

**Interstitial contents.** Medial and lateral menisci → anterior horn, body, posterior horn, both
roots and their tibial insertions, the meniscocapsular junction, both articular surfaces. ACL → its
femoral and tibial footprints, its band. PCL (unscored, but needed as the ACL's reference and
buckling witness). *Needed by the meniscus and ACL rows.*

**Spans and attachments.** Superficial MCL, deep MCL (meniscofemoral and meniscotibial), MCL bursa,
posterior oblique ligament, medial retinaculum/MPFL, pes anserinus and its bursa. LCL, biceps femoris,
iliotibial band (unscored; they define the lateral wall and the Segond region). *Needed by MCL, and
by ACL's secondary signs.*

**The cavity and its bounds.** The synovial cavity as the fluid-class component connected to the
tibiofemoral interstices; the suprapatellar recess, medial and lateral gutters, posterior femoral
recesses; plicae. Its bounds: **Hoffa's**, suprapatellar and prefemoral fat pads; quadriceps and
patellar tendons; the gastrocnemius origins. *Needed by Effusion and Synovitis.*

**The popliteal group.** Medial head of gastrocnemius, semimembranosus tendon, the bursa between them
and its neck through the posteromedial capsule; popliteal artery and vein; tibial nerve. *Needed by
Baker's — and the muscle and tendon are not incidental boundaries, they are the definition.*

**Distractors, which must be resolved as objects so they can be excluded.** This is the "black"
principle: positive assignment of what a thing *is not* resolves what it is. Physeal scar, bipartite
patella, bone islands, red marrow (vs Fracture and Contusion); popliteus tendon and its hiatus,
meniscofemoral ligaments (Humphrey, Wrisberg), transverse intermeniscal ligament (each makes a
pseudo-tear at a meniscal horn); MCL bursa and pes bursitis (medial fluid that is not MCL injury);
non-communicating bursae, parameniscal cysts, cruciate ganglia, popliteal aneurysm (vs Baker's and
Effusion); **ACL graft and its femoral/tibial tunnels**, which will otherwise fire Fracture.

**Two regime flags, read before any predicate runs.** A T1 fat-suppressed series is almost never
acquired without gadolinium, so its presence is probable post-contrast evidence; MR arthrography also
uses T1 FS but with intra-articular contrast and deliberate distension, and its tell is that the
*fluid itself* is bright on T1 FS. Both must be flagged from the regime key or the predicates invert.

## The twelve findings as predicates

Each row names the human design subject of a measurement on an object or relation.
Production uses indexed subjects selected by structural facts, not the anatomical words.
None is a search over an image.

| finding | subject | predicate |
|---|---|---|
| Fracture | a bone (T1) | break in the structural coherence of its outline/interior |
| Contusion | a bone (T1) | interior (marrow) signal anomaly, boundary intact |
| Medial OA | femur↔tibia medial (T2) | cartilage thickness loss; marginal osteophyte; subchondral change |
| Lateral OA | femur↔tibia lateral (T2) | cartilage thickness loss; marginal osteophyte; subchondral change |
| PF OA | femur↔patella (T2) | cartilage thickness loss; marginal osteophyte; subchondral change |
| Medial Meniscus | content of femur↔tibia medial (T2) | its continuity |
| Lateral Meniscus | content of femur↔tibia lateral (T2) | its continuity |
| ACL | content of the intercondylar interstice (T2) | its continuity and course |
| MCL | medial span, femur→tibia (T3) | its continuity |
| Effusion | the capsule (T4) | over-fill of its volume |
| Synovitis | the capsule's lining (T4) | excess thickness |
| Baker's | the capsule (T4) | posterior outpouching beyond the bones' envelope |

**Ten of the twelve take a non-bone subject; Fracture and Contusion take a bone.** All twelve depend
on the bones, because the other ten's subjects are constructed from them.

*(Corrected 2026-10-11. This passage first read "Zero of the twelve are about a bone as such", which
contradicted its own table two rows above. Codex reported the contradiction with both passages
quoted, which `AGENTS.md` law 9 admits as provable, so it was fixed rather than referred:
`chapters/02-collapse/readings/object-model-codex.md`.)*

Synovitis is the worked example of how trivial a predicate becomes once its subject exists. The
founder, 2026-10-11:

> "given an object named 'the capsule', synovitis is defined as an abnormality/excess thickness in the
> lining, resolved by contrast imagery ... Look at the picture, if signal do big number, is '-itis, if
> not, is normal. Done. Given \<object>s as the basis of reasoning...how absurdly simple it all is!"

## Laterality without a tag

Medial versus lateral decides four findings, and the laterality tag is **absent from 181 of 336
series** (measured). It is not needed. DICOM's LPS frame already fixes superior/inferior and
anterior/posterior; the only unknown is which patient side is lateral.

**Every axis has an anatomical witness, and the frame's handedness closes it.** Settled 2026-10-11,
the founder agreeing with Fable's reading over the lead's single-witness version:

| axis | its witness |
|---|---|
| superior | the direction the femoral shaft leaves the condyles — the longer shaft |
| anterior | where the patella sits |
| lateral | where the fibula sits |

**LPS is right-handed, so given S and A, the patient LEFT–RIGHT AXIS follows by cross product.** That
is what the handedness buys, and it is worth having: only **one** anatomical witness is then needed
rather than three.

**But the axis is not the anatomical lateral direction, and the frame can never give the sign.**
Corrected 2026-10-11 by arithmetic, after a second reader caught it: in LPS, `S = (0,0,1)` and
`A = (0,−1,0)`, so `S × A = (1,0,0)` — **patient-left**, which is *lateral* for a left knee and
**medial for a right one**. Which knee it is was the unknown all along. So the fibula is not a
cross-check that could be dispensed with: it is **the sign**, being lateral in both legs, with the
fabella, the popliteus groove and the condylar asymmetries available for concurrence.

Where no laterality witness resolves — common, since the fibular head sits 1–2 cm below the lateral
plateau, so coronal stacks reach it only posteriorly and sagittal stacks only laterally — medial and
lateral are **abstained** with a named code, and every side-dependent finding abstains with them.
Two witnesses placing lateral at opposite ends of the axis keep both readings rather than resolving
in favour of either.

On the fibula's own invariance the two readers disagreed, and the founder ruled: Fable's position
stands — *"Anatomically, true without exception. The fibula is lateral (and slightly posterior) to the
tibia in every human leg; there is no situs inversus of a limb."* The only anatomical exception is
**absence** (fibular hemimelia, amputation), which correctly abstains. Codex's counterexample, a
posteromedial dislocation of the proximal tibiofibular joint, is recorded in its reading.

Every other way the fibula misleads is **pipeline, not anatomy**, and each has a structural guard:
the fibular head's dome may merge into the tibial territory across the thin proximal tibiofibular
joint, or fall below the prominence floor; and a watershed split of the tibial plateau at the
intercondylar eminence could present a "small lateral-ish territory" that is *medial* plateau. The
guard is that a fibula candidate must be enclosed by its own closed cortical ring on every slice it
occupies, lie inferior to the tibial plateau, and have a long axis parallel to the tibial shaft.

Secondary lateral witnesses, for concurrence and never alone: the **fabella** (a sesamoid in the
lateral gastrocnemius head, present in roughly a quarter of people), the **popliteus tendon** in its
groove on the lateral femoral condyle, and — as statistical tendencies only — the medial femoral
condyle being larger in anteroposterior dimension, and the medial tibial plateau being concave where
the lateral is convex.

## The lenses and the bundle: every place and every object in one language

Settled 2026-10-11 from the thesis's own figures H2a2 and H2b, which the founder attached. The
"tissue fingerprint by conjunction" is **not a new mechanism** — it is the thesis's bundle, and the
cell project already built it.

**A bundle crosses scale with lens.** In the sibling: the voxel · the 16×16 neighbourhood · the lens ·
the plate, each read by Gradient · Contrast · Split Quality · Dark Share · Composite; plus relational
banks (the dome link's eight compass directions, the ring) and provenance banks (the lenses'
conversation, **how its cell came out**, its own voxels). Every row is one **balanced-ternary digit
against a static middle** — below / at / above — and the figure shades each by how many of the
object's places wrote it.

**For the knee, the lens axis is the acquisitions.** T1, T2 and PD, fat-suppressed and not, of the
same knee. A tissue class is a conjunction of rows, never a threshold on one image:

| class | its conjunction |
|---|---|
| fat | bright(non-FS) ∧ dark(FS) |
| fluid | bright(FS) ∧ bright(T2 non-FS) ∧ dark(T1) |
| cortex, tendon, ligament, meniscus | dark on everything |
| hyaline cartilage | intermediate — always below fluid, always above meniscus |
| muscle | intermediate(T1) ∧ intermediate-dark(T2, FS) |
| marrow edema | dark(T1) ∧ bright(FS), inside a bone |

**The middle is read from the image, never from an absolute level** — and *how* it is read was
settled on 2026-10-11 ("Your inference is correct", `chapters/03-lenses/teachings.md`). It is a
**pair of edges at the terciles of a structurally selected population**, both edges in the 0 row,
read **after** a local structural normalisation that carries the spatial correction. The middle
itself names no tissue: the earlier proposal — subcutaneous and marrow fat as the fat reference,
muscle as the intermediate, a distended recess as the fluid — is **withdrawn**, and the tissue
conjunction lives in the rows **across acquisitions** instead. That is what defeats the failure that
killed four intensity instruments here, since scanner scaling cannot move a reading stated against
the image's own distribution. The sequence type is read from TR/TE/flip
angle/ScanOptions/InversionTime, never from a series description.

**Lineage is a bank, not metadata.** "How its cell came out" sits *inside* the profile, so how an
object was resolved is part of its identity (§6.6: "how it came out is a physical fact: a nucleus
resolved cleanly in a first pass and one found only beneath another are different objects").

**The full profile and the cheap profile are the compute contract.** H2b sets a full profile (the
whole pipeline, at the anchor) beside a cheap one (the raw picture alone), bank by bank, marking each
`Same rows` / `Whole pipeline only` / `Reads no Composite` / `Not written`. This is the mechanism for
the trade the founder named — "balance resolution and diagnosis quality with computational efficiency
for the competition submission pipeline" — and it is already specified: the cheap profile is what
survives a budget, and the figure says exactly which banks it loses.

## Recognition is mechanical, and recall comes later

A knee is a fixed anatomy. Cells need recall because you do not know how many there are, where, or
which; the femur is just *the superior bone*. Identity is fixed by invariant relations, so it is
resolved by structure, not resemblance. The founder, 2026-10-11:

> "Recognition SHOULD actually be something we can do mechanically! Right now I want to really iron
> down how to resolve EVERY relevant component of the knee anatomy PROPERLY, get EVERY \<object>
> cleanly, then work on diagnosis, which is where recall of specific presentations ... will matter.
> But for now, we should be able to isolate the components of the knee with NO recognition, pure math."

So the thesis's memory, buckets and recall (§8) are **not** part of the object parse. They arrive at
the diagnosis stage, for the presentations a predicate cannot settle alone.

## The route

| route package | design role |
|---|---|
| study | files → series, whole at stored fidelity |
| collapse (field) | regime, noise law, physical frame, squint |
| lenses | per-place readings per acquisition as ternary digits |
| objects | diagnostically significant visual subsets; border refinement inside this stage |
| relations | interstices per facing pair, with gap, walls, fill and contents |
| ownership | claims and residual scheduling |
| vectors (bundles) | bank/row counts, lineage among them |
| predicates | the twelve, each on its structurally selected subject |
| output | twelve confidences, with a companion named-code record |

This is the intended nine-stage route, not a cached status table. Compute declared
standing with `just unit`, then check actual invocation/consumption and drawing outcomes
through [PIPELINE.md](PIPELINE.md) and the real entry point.

Beside the route: **memory** and **expert** (diagnosis-stage recall of presentations), **record**,
**agencies**.

The conversation between series is same-orientation only, and that is its purpose — founder,
2026-10-11: "the same view/orientation of the knee in two image series to be able to help resolve
\<object>s in the visual field more cleanly than any one can resolve alone".

## What this supersedes, and what survives

**Superseded:** the chapter table of `docs/SPINE.md` (Figure 8's sixteen stages transcribed in order).
It was written before the knee's \<object> was known, and five of its package names were cell-tracking
content rather than roles.

**Survives unchanged:** the thesis as the theory oracle and the cell-tracking build as the engineering
oracle; the PI–undergrad pass and the working loop (`docs/SPINE.md`); the lens principle as the rigid
oracle (`AGENTS.md`); every project law. Figure 8's roles still apply where the route names them —
the collapse, the loop, the residual, the vectors, the agencies — and they fold into the stages above
rather than ordering the build.

## A note on the lineage

Minsky assigned computer vision to Sussman as a 1966 summer project. The founder, 2026-10-11:

> "he lacked the tooling to actually make the mechanics work as code, even with one of the most
> brilliant programmers in history ... as his student, but if you actually CAN resolve objects, then
> 'visual reasoning' is basically common sense + math"

The missing piece was never the reasoning; it was the object layer beneath it. The SICP-style build
here is both the practical discipline for a layered system and a deliberate nod to that lineage.
