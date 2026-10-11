# The object model: what the knee is, and why diagnosis falls out of it

<!-- The settled design, agreed with the founder 2026-10-11. This supersedes the chapter table of
docs/SPINE.md as the project's structure; SPINE.md keeps the way of working. Read this FIRST in a
new session or after a compaction, then docs/chapters/<stage>/README.md for where a stage stands. -->

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

Resolved today by the dome, re-derived for bone. The thesis's centres are brightness peaks because a
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

A relation carries its **gap** (extent across), its **walls** (the bounding surfaces of each object),
its **fill** (what occupies it), and its **contents** (tier-1 objects lying inside it, such as a
meniscus or a cruciate).

### Tier 3 — spans
An object attached to two bones and running **outside** the interstice between them. The MCL is the
scored instance: superficial, on the medial exterior, extra-articular. A span is not interstitial
content, and treating it as such was a reading error corrected on 2026-10-11.

### Tier 4 — the envelope (the capsule)
The volume enclosing the articulation, **larger than the union of the interstices** — it includes the
suprapatellar recess, which extends well above the patella. It carries a **volume**, a **lining**, and
an **outline**.

## The twelve findings as predicates

Each row is a measurement on a named object or relation. None is a search over an image.

| finding | subject | predicate |
|---|---|---|
| Fracture | a bone (T1) | break in the structural coherence of its outline/interior |
| Contusion | a bone (T1) | interior (marrow) signal anomaly, boundary intact |
| Medial OA | femur↔tibia medial (T2) | gap narrowed; walls degraded; margin outgrowth |
| Lateral OA | femur↔tibia lateral (T2) | gap narrowed; walls degraded; margin outgrowth |
| PF OA | femur↔patella (T2) | gap narrowed; walls degraded; margin outgrowth |
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

**The fibula settles it geometrically.** It is always lateral to the tibia, in both legs, without
exception. Resolve the small bone territory adjacent to the large inferior one and its direction from
the tibia *is* the lateral direction in patient coordinates. No tag, no recognition, no learning.
Where the fibula is out of field, the series abstains rather than guesses.

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

| stage | what it produces | state |
|---|---|---|
| study | files → series, whole at stored fidelity | built |
| field | regime, noise law, physical frame, squint | built (Packet A) |
| objects | every diagnostically significant element of the knee | partly (B1 territories, B2 conversation); the residual is open |
| relations | interstices per facing pair, with gap/walls/fill/contents | not built (Packet C) |
| ownership | every place owned; residual pulled out until nothing significant is unassigned | not built (Packet D) |
| predicates | the twelve, each on its subject | not built |
| output | twelve confidences per study | not built |

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
