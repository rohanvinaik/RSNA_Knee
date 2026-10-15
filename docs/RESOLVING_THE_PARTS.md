# Resolving the parts of the knee: the views, the lenses, the operations

Written 2026-10-15 at Rohan's request: «Make sure that you have this saved out somewhere. A single
document that lays out what lenses, what logical operations allow for resolution of each element. The
meaning of these objects in this computer vision implementation.» And: «We do need to find the rules
that resolve the bursa and each of the others, we should write up provisional entries with logical
inferences about how those would be resolved».

His words are quoted «». Everything else is Claude's wording, checked against the code: the exact
checks and abstain codes of each part are its paragraph in the module note of
`src/knee/objects/assignments.py` (each part an «<object>») and the main-slice stages of
`scripts/run_interiors.py`; medicine's facts and their sources are `docs/OBJECTS_AND_CONDITIONS.md`.
Read this with the thesis conversation, the theory and `docs/HOW_TO_BUILD.md`.

## 1. What resolving a part means

Recognition is the hard part of computer vision, and here it is hand-built, deterministic, simple math
on lossy lenses, with no AI in it (`docs/THEORY_OF_THE_CASE.md`). «This relies on a series of lossy
lenses, with the "truth" being recapitulated from addative and subtractive superposition of the lossy
lenses to resolve the higher-dimensional truth.»

- **Never one lens alone.** «It's not SUPPOSED to be isolateed by ANYTHING alone» (2026-10-15). A lens
  that does not single a part out by itself is doing its job; the part is the combination.
- **A lens is never wrong; a name can be.** «"never wrong" simply refers to the thing doing the
  measurment.» A name that is wrong on a few weird images is not a reason to change a rule that works:
  «Those edge cases are the ENTIRE space of where AI comes in». And (2026-10-15): «You keep trying to
  make the pre-AI part perfect, it's SLIGHTLY imperfect, just ONCE, on a lens I've already described as
  LOSSY, and you fuck everything up in response.»
- **Every part defined once comes first.** «You have yet to define what all the anatomical features
  are even ONCE, and that is a NECESSARY pre-condition to even STARTING the AI layer.» The test is
  validity: each part resolved at least once, by a rule not tuned to that view.

**What an object is in this implementation.** A part is an «<object>»: a short, numbered set of
descriptions of how it looks in these scans, each one a check on the lenses with the code it abstains
with. On a slice, the part is the places that meet every description; on every series the run reads,
each part carries a decision: named (and how: `identified`, `agreed_with_its_partner`,
`laid_from_its_partner`, `carried_from_...`) or abstained (and why). Parts already found are the
targets of the next ones (a ligament joins two bones; a fat pad is the rest of the patella's region),
so each part is defined by its relations to the parts before it, as medicine defines parts: «"define
rules to discriminate between objects in a field" is LITERALLY how medicine itself does it. What else
do you think is the definition of "interstitial" fluid??» (2026-10-14).

## 2. The views: lossy perspectives on one leg

Rohan, 2026-10-15: «the different views, like "fat-bright" vs "fat-dark", and the different axes being
viewed, like coronal vs axial, etc, are used as lossy views from independent perspectives, which
enable resolution of anatomical elements--the LITERAL thesis of the project, as the standard operating
procedure in medicine itself».

A study is several series of one knee from one session; each series is one view, lossy in its own way
(the signal table and medicine's reading order: `docs/OBJECTS_AND_CONDITIONS.md` §2 and §3).

| view | what is bright and dark | what it shows plainly |
|---|---|---|
| fat-bright (`Fat_Suppression` 0: T1, or T2/PD) | marrow and fat bright; ligaments, tendons, menisci and cortex dark; on T1 fluid dark, as dark as muscle | bone by its marrow; fat; muscle against fat; the dark bands (PCL, tendons, the LCL's band) |
| fat-dark (`Fat_Suppression` 1, fluid-sensitive: T2 FS, PD FS) | fluid white; cartilage brighter than marrow; marrow and fat dark grey; ligaments, tendons, menisci and cortex dark | fluid and what it walls off (the ACL, the recesses); cartilage; menisci against cartilage; muscles parted by the suppressed fat |
| sagittal (front to back, along the leg) | | the cruciates; the patella, its tendons and fat pads; the menisci's horns |
| coronal (side to side, along the leg) | | the collaterals; the menisci's bodies; the cartilage of femur and tibia; the gutters; the sides of the leg |
| axial (front to back, side to side) | | the back of the knee (gastrocnemius heads, hamstring tendons, Baker's); the patellofemoral joint; vessels |

**One leg, one set of objects.** «It's literally the same leg, obviously the object would be the same in
both views. That's the WHOLE thesis». Each slice's place is known in the scanner's millimetres (its
frame), so a part found on one view is carried onto the others by place:
- onto its **twin**, the other sequence's slice of the same place (`with_partner`): a bone both name is
  named where both agree; a part only one names is laid onto the other;
- onto **other slices and planes** of the same leg: the femur and tibia onto the axial slices
  (`leg_of`, `carry_onto`), the middle slice's bones onto a part's own slice (`carried_bone`), the
  fibula onto the LCL's coronal slice (`places_on_slice`).

## 3. The lenses

Each is a measurement, never wrong and lossy.

1. **The acquired signal**: the light as stored.
2. **The background split**: one number per series, the valley after the background's mode in the
   series' own histogram (`knee.collapse.noise`). **The low signal** is every place at or under it.
3. **The black margin**: stored zeros joined to the picture's frame, where the reconstruction never
   filled (`margin`). Nothing is named in it.
4. **The distance** of each place from the low signal, in millimetres, and its **interior peaks**
   (prominent by 3 mm) (`knee.objects.interiors`).
5. **The territories**: regions grown from the peaks over the places not low signal, each with its
   strongest peak and the peak's depth.
6. **The border readings**: the territories' edges and the dark bands read across them. They are
   drawn in the pictures; no rule reads them yet.
7. **The squint**: every slice of a series reduced to 10 mm tiles, each tile's median, minimum,
   maximum and coverage, and its centre in millimetres (`knee.collapse.squint_stack`). It is the cheap
   look at the whole series that points where the expensive work runs.
8. **The frame**: each slice's place in the scanner's millimetres, so each place's position along the
   patient's axes (toward the left, the back, the head).
9. **The twin**: the other sequence's slice of the same place, its parts and its light laid on by the
   pair's one match of places.

What several rules weigh a place against is read once per slice (`Measures`): the marrow's light over a
bone's places, each place's distance from a part, its position along an axis, each region's size.

## 4. The operations

Every rule is a few of these, in plain array arithmetic:
- **add, intersect, take away**: a union, an intersection, "outside every part named";
- **light against a part**: "as bright as the femur's marrow, within a quarter" (the same tissue),
  "darker than fat", "four times the marrow's light";
- **place**: along the leg (above, below, between two parts on each line along the leg), front to
  back (in front of, behind), side to side (the knee's inner or outer side, from the header's word for
  which knee, or from the medial meniscus); "within 2 mm of" a part (it reaches it); "the rest of a
  region beyond a part";
- **shape**: thickness (every piece thinner than N mm rubbed away), size (at least a disc N mm
  across), the deepest peak, the largest piece, the piece nearest each end;
- **carrying by place**: onto the twin, onto another slice, onto another plane;
- **abstaining**: each description that fails says so by its own code.

Every number in a rule comes from anatomy, from a cited source, or from Claude's reading of the
picture, labelled as such in the code, and is set where medicine already orders the tissues (for
example, fluid is brighter than cartilage, which is brighter than suppressed marrow).

## 5. The parts resolved, each at least once on the proof study

The proof study is `…10095687747295410396510538520594649149`. "Middle slice" below is the slice the run
reads of each series (the middle of its stack: see §8, under review); a part with "its own slice" is
named on a slice chosen for it. Over-reaches are listed in each part's paragraph in the module note.

| part | meaning | views and slice | the lenses and operations | found from | the twelve |
|---|---|---|---|---|---|
| air | the field the leg lies in | any; laid on where the lens draws the air into its territories | low signal, outside the leg (every territory, holes filled) and the margin, in fields at least 1 cm thick | — | none |
| skin | the leg's edge | as air | the leg's places touching the air | air | none |
| femur, tibia | the two bones the knee is | any slice the leg runs in | the territory with the deepest peak and the deepest one above or below it along the leg; upper femur, lower tibia; kept where the twin agrees | the territories | OA (all three), Contusion, Fracture; the ACL's and MCL's attachments; the tibia as the menisci's plateau |
| bone marrow | the inside of each bone | with its bone | the bone's region, within its shell | femur, tibia | Contusion, Fracture, OA |
| joint | the space between the bones | any slice the leg runs in | what lies between the femur and the tibia on each line along the leg, outside the margin | femur, tibia | OA (narrowing), Effusion, Synovitis |
| patella | the bone in front of the femur's lower end | fat-dark sagittal; laid onto the fat-bright twin | the deepest peak in front of the femur, at most 5 cm above its lowest place; its territory's places as bright as the femur's marrow within a quarter; the piece holding the peak's disc, holes filled | femur | PF OA, Contusion, Fracture |
| menisci | the two dark wedges between condyle and plateau | coronal (fat-dark; laid onto the fat-bright twin) | in the joint, the low signal with every piece thinner than 2 mm (a bone's shell) rubbed away, the pieces touching the joint, the one nearest each end; the medial toward the other knee, from the header | joint | Medial and Lateral Meniscus, OA, MCL |
| articular cartilage | the layer on each joint surface | fat-dark coronal; laid on | the joint's places brighter than the bones' marrow (1.5 times), within 3 mm of a bone, named for the nearer bone | femur, tibia, joint | OA (all three) |
| PCL | the thick dark ligament from the notch to the back of the tibia | fat-bright sagittal; laid on | the slice's thick (3 mm), uniformly dark bands (the light over 2 mm under 0.3 of the femur's marrow), the largest reaching within 2 mm of both bones | femur, tibia | none (the ACL's neighbour) |
| ACL | the ligament in the notch outer to the PCL | its own slice: the middle slice's neighbour on the knee's outer side; fat-dark; laid onto the twin | between the femur and tibia carried there (the regions mostly theirs on the middle slice), the region the lens draws, walled off by fluid, whose peak lies in the joint | femur, tibia (carried) | ACL |
| MCL | the band on the inner side of the joint | coronal (fat-dark; laid on) | the low signal outside every part named, on the medial meniscus's side of the joint's middle, the largest piece reaching within 2 mm of both bones | femur, tibia, medial meniscus | MCL |
| LCL | the cord from the femur's outer condyle to the fibula's head | its own slice: the coronal slice through its fibular attachment, 8.2 mm behind the head's front edge (LaPrade 2003); fat-bright; laid on | the region neither the femur's nor the fibula's, on the fibula's side of the tibia's middle, reaching within 2 mm of both, the largest | fibula (carried), femur (carried), tibia | none (the MCL's counterpart) |
| fibula | the bone under the tibia's outer back | its own slice, fat-bright sagittal: where it is largest | below the tibia's top on the knee's outer side (the squint's tiles there), the region as bright as the tibia (the same tissue), at least 1 cm across, its middle 3 cm below the tibia's top and behind its middle, apart from the tibia and whole | tibia, the squint | Fracture |
| joint fluid | the fluid of the joint and its recesses | fat-dark fluid-sensitive; laid onto the fat-bright twins | outside every part named but the joint, four times the marrow's light, the pieces touching the joint or within 2 mm of a bone | femur, tibia, patella, joint | Effusion, Synovitis |
| Hoffa's fat pad | the fat behind the patellar tendon | fat-dark sagittal; laid on | the rest of the patella's region below the patella, outside every part named | patella | none |
| suprapatellar fat | the two fat pads above the patella, together | fat-dark sagittal; laid on | the rest of the patella's region above the patella | patella | none (they border Effusion's recess) |
| patellar and quadriceps tendons | the extensor mechanism's tendons | fat-bright sagittal; laid back onto the twin | of the slice's dark bands, the one joining the patella (laid on from the twin) and the tibia, split at the patella: below it the patellar tendon, above it the quadriceps tendon | patella, tibia, the PCL's bands | none |
| fat under the skin | the subcutaneous fat | fat-bright; laid onto the twin | outside every part named, at least three quarters of the marrow's light, the pieces reaching within 2 mm of the skin | skin, femur | none |
| muscle | the rest of the leg's soft tissue | fat-bright; laid onto the twin | the leg's places outside every part named, darker than fat, the bodies at least 1 cm across, minus what the fat-dark twin sees as fluid | air, femur, the twin's fluid | none (the gastrocnemius head borders Baker's) |
| medial gastrocnemius head | the calf muscle's inner head behind the inner condyle | fat-dark axial middle slice | the femur and tibia carried by place; the inner condyle (the bones' region with the deepest peak on the inner side of the notch); the deepest region not the bones', on the inner side, behind the condyle's peak | femur, tibia (carried), the notch (middle sagittal) | Baker's |
| semimembranosus tendon | the inner hamstring's tendon at the back-inner top of the tibia | its own axial slice: the top of the tibia (LaPrade 2007), found by carrying the leg onto each axial slice; laid on | the thick low signal outside every part named, its one-pixel cracks closed, inside and behind the inner condyle's peak, reaching its region; the front one | femur, tibia (carried), the inner condyle | Baker's |

## 6. Provisional entries: the parts not yet resolved

Each entry is a plan for the loop (§7), not a rule: the part's meaning, the kind of tissue it is and how
that kind is already resolved, where it lies relative to the parts already found (and the squint for
which slices show it), the views medicine reads it on, and its relation to the twelve. Each is checked
on the pictures before any rule is written.

- **Synovium: the joint's lining, and the synovial fluid it holds.** Rohan, 2026-10-15: «On the
  synovium...huh? The pictures don't hold it? It's literally a form of interstitial fluid.
  Interstitial. Between the tibia and femur. We have the tibia, we have the femur. It's...obviously in
  there?» Meaning: the synovial membrane lines the joint capsule and its recesses, and the synovial
  fluid fills the cavity [C], [R-KNEE]. It is interstitial, defined by what it lies between, as
  medicine defines interstitial fluid [W-ECF]: between the femur and the tibia (and the patella),
  inside the capsule. Kind: the fluid is the white of the fat-dark, fluid-sensitive views, and the
  joint's fluid already named is synovial fluid in the recesses. Where: the joint already named and
  its recesses (suprapatellar, the gutters, the back). Provisional reading: the synovial compartment
  is the joint's places and the joint fluid's, without the parts that lie in the joint but are not
  synovium (cartilage, menisci, the cruciates); its lining is the compartment's edge against the fat
  pads and the capsule. Views: the fat-dark coronal and sagittal (the recesses' white), the fat-dark
  axial (the suprapatellar and back recesses), and the fat-bright twin by place. The twelve:
  Synovitis (its inflammation), Effusion (its excess fluid), Baker's (the cyst is synovial-lined).
  (Claude had written "not named, because the pictures do not hold it": wrong. It looked for the
  synovium's own look instead of the relation that defines it.)
- **The gastrocnemius–semimembranosus bursa** (where a Baker's cyst forms). Meaning: the bursa beneath
  the medial gastrocnemius head, between it and the semimembranosus tendon, joined to the joint
  [R-KNEE], [R-BAKER]; normally collapsed. Interstitial again: between two parts already found on the
  axial, behind the inner condyle. Kind: fluid, white on the fat-dark fluid-sensitive views and dark on
  T1 (where muscle's rule already leaves out the twin's white, so a cyst is not named muscle). Where:
  the axial slices between the semimembranosus tendon's slice (the top of the tibia) and the head's
  (the condyles), the squint showing on which of them white lies between the two. Provisional reading:
  the seam the head and the tendon share, and what the fluid lens sees in it: white, joined by a neck
  to the joint's back recess, is a distended bursa. Views: the fat-dark axial first (medicine reads
  Baker's there [AUR]), the sagittal for its neck. The twelve: Baker's.
- **Lateral gastrocnemius head.** The calf muscle's outer head, from the back of the femur's outer
  condyle; the lens already draws it as a region of its own on the fat-dark axial. Provisional reading:
  the medial head's rule on the knee's outer side of the notch. The twelve: none directly.
- **Popliteal vessels** (the artery in front of the vein [Kh]). Kind: tubes; on the proof's fat-dark
  slices they are as white as fluid, round on the axial and long on the sagittal. Where: behind the
  notch, between the two gastrocnemius heads, continuing from slice to slice down the axial series
  (the squint follows them). Provisional reading: round white bodies behind the notch between the
  heads, apart from the joint (not joined to it, which parts them from a Baker's cyst), carried slice
  to slice. The twelve: none (landmarks; to be told apart from Baker's and Effusion).
- **Patellar retinacula.** Low-signal bands from the patella to the femoral condyles, best seen on the
  axial [C], [Kh]. Needs the patella on the axial, carried by place from the sagittal (owed).
  Provisional reading: on the axial through the patella, the low signal joining the patella and each
  side of the femur, the MCL's kind of rule. The twelve: none (PF OA's neighbours).
- **The lateral complex beyond the LCL: popliteus tendon, biceps femoris tendon, iliotibial band**
  [Kh], [LP-PLC]. Kind: tendons and a band, dark on every sequence. Where, relative to parts found: the
  popliteus tendon at the femur's outer condyle's notch, medial to the LCL (the LCL's band now takes
  it in); the biceps tendon reaching the fibula's head beside the LCL; the iliotibial band in front of
  them on the outer side. Provisional reading: the dark-band rules (thick, uniformly dark, joining two
  parts) with these targets, on the coronal and axial fat-dark views [AUR]. The twelve: none directly.
- **The other hamstring tendons.** The semitendinosus, a smaller black oval behind the semimembranosus
  tendon on its slice (seen on the proof), and the pes anserinus tendons to the front-inner tibia
  [LP-MED]. Provisional reading: the semimembranosus tendon's rule, the one behind it; carried along
  the axial series. The twelve: none directly (Baker's neighbours).
- **The patella on the axial, the menisci on the sagittal.** Not new parts, but the views medicine
  reads them on (the patellofemoral joint on the axial, the menisci's horns on the sagittal): carried
  there by place from where each is found.

## 7. How to build the next ones

The loop of `docs/HOW_TO_BUILD.md` §7, part by part, in the order of `docs/OBJECTS_AND_CONDITIONS.md`:
1. Read the part's provisional entry, and medicine's words for it. Ask what it lies between, beside or
   inside, among the parts already found.
2. Look at the pictures of the proof, at the part's own pixels, on every view that shows it: which
   view shows it plainly (fat-bright or fat-dark; sagittal, coronal or axial), and which lenses
   (light, low signal, territories, distance and peaks, the twin, the squint) add up to it and take
   away what is not it. Never one lens alone.
3. Write that reading as a few descriptions, each one check with a named code, its numbers from
   anatomy, a source or the picture (labelled), its targets the parts already found; draw it on the
   proof before it touches the run, and look.
4. Write it in `src/knee/objects/assignments.py` with its paragraph, add a test, run the proof through
   `scripts/run_interiors.py`, look at every picture it reaches, run the gate, commit, and show Rohan.
5. It is done when it is resolved once. Do not chase the studies where it is a bit off.

## 8. Under review: dimensional collapse and how a slice is chosen

Rohan, 2026-10-15: «what do you mean by "all five middle slices"? Read the "what an <object> is
thesis, send a cheap agent to look into the dimensional collapse parts and slice selection parts of
the information theory parts that are relevant for this as well. I think that you missed the point of
this part of the thesis, and we need to get to fixing the implementation in another session».

What the run does now: for most parts it reads each series' middle slice (the floor of half its
stack, `knee.study.series.selected_slice`), and four parts get a slice of their own (the fibula's,
largest; the ACL's, the middle slice's neighbour; the LCL's, through its attachment; the
semimembranosus tendon's, the top of the tibia). The middle slice is the code's choice, not the
thesis's. What the thesis says about collapsing depth and choosing what to read is recorded below,
from its own text, for the session that fixes the implementation.
