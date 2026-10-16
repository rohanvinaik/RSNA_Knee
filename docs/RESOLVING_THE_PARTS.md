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

**How medicine reads them** (`docs/OBJECTS_AND_CONDITIONS.md` §2–§3, with their sources). Each part is
read on the view that shows it plainly, and confirmed on another. The normal anatomy is found on T1W,
proton-density and gradient-echo images; the tissues are confirmed homogeneous on T1W, and checked on
T2W where they are not [Kh]. Fluid and Baker's cyst are read on the axial T2 FS; bone bruises and
fractures with fat suppressed, the fractures confirmed on the coronal T1 without it; the meniscus on
the sagittal PD and its body on the coronal T2 FS; the cartilage on the coronal and sagittal T2 FS; the
ACL and PCL on the axial and coronal T2 FS; the MCL and the lateral complex on the coronal and axial
T2 FS; the extensor mechanism on the sagittal T2 FS; the vessels, nerves and soft tissue on the axial
T2 FS [AUR]. Three tissues are dark on every sequence, cortex, ligaments and tendons, and the menisci
[Kh], so they are told apart by place and shape, not by their light (Claude's pairing, as in that
document's §3). In the thesis's words: «No view is the truth alone, and what an <object> is, is what
the views recover together» (*What an <Object> Is* §1.3).

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
   drawn in the pictures and read for nothing else: only a run that draws (`--draw`, development
   only) reads them, on each middle slice; a run that draws nothing, as in competition, reads the
   territories alone (`interior_regions`). No rule reads them.
7. **The squint**: every slice of a series reduced to 10 mm tiles, each tile's median, minimum,
   maximum and coverage, and its centre in millimetres (`knee.collapse.squint_stack`). It is the cheap
   look at the whole series that points where the expensive work runs.
8. **The frame**: each slice's place in the scanner's millimetres, so each place's position along the
   patient's axes (toward the left, the back, the head).
9. **The twin**: the other sequence's slice of the same place, its parts and its light laid on by the
   pair's one match of places.
10. **Enclosed darkness**: how far a dark interior lies below its brighter enclosure. Erosion
    reconstruction from the acquired image border fills enclosed depressions; subtracting the
    acquired signal gives their depth (`enclosed_darkness`). No grey-level cutoff is chosen.

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
reads first of each series, the middle of its stack: «The "middle" is a fine standard first slice to
select» (§8). A part not plain there is named on "its own slice", a slice chosen for it. Over-reaches
are listed in each part's paragraph in the module note.

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

**Historical plans, now completed.** The production definitions and their inspected demonstrations
are in §9; the last four are implemented in `4a126fc`. This section preserves the original
reasoning and the cross-view tasks, not a current unresolved-anatomy list. The current checkpoint
is `docs/ANATOMY_DEFINITION_CHECKPOINT.md`.

Each entry is a plan for the loop (§7), not a rule, and every reading in it is Claude's and provisional
until the pictures check it: the part's meaning; the kind of tissue it is and how that kind is already
resolved; where it lies among the parts already found; which of the five views show it and where its
best slices lie, from the squint (each slice's 10 mm tiles, their median, minimum, maximum and coverage
and their centres in millimetres, made once over every slice of every series: §3) and from the parts
already found, carried by place; and its relation to the twelve. Rohan, 2026-10-15: «discovery of ALL
elements of the anatomy at their best slices and resolution across the 5 images/3 orientations» (§8).
Where an entry calls a tile "as white as fluid", that is Claude's provisional reading of what the
squint computes: the tile's maximum at least `FLUID_BRIGHTER` (four) times the bones' marrow light read
on the same series' middle slice, the joint fluid's own rule (§5), on a fat-dark, fluid-sensitive view.

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
  pads and the capsule. Views and slices: the fat-dark coronal and sagittal, where the recesses' white
  outlines the compartment, and the fat-dark axial for the suprapatellar and back recesses; laid onto
  the fat-bright twins by place. Its best slices are where the compartment is widest: the coronal
  slices through the condyles, where the gutters run down both sides, and the sagittal slices through
  each compartment and through the suprapatellar recess; the squint's tiles whose maximum is as white
  as fluid, beside the femur's and tibia's places, show which slices hold the recesses' fluid without
  the lens read on every slice. The twelve:
  Synovitis (its inflammation), Effusion (its excess fluid), Baker's (the cyst is synovial-lined).
  (Claude had written "not named, because the pictures do not hold it": wrong. It looked for the
  synovium's own look instead of the relation that defines it.)
- **The joint capsule.** Meaning: the sleeve that closes the joint (anatomy), lined on its inside by
  the synovium [R-KNEE]; its back wall is among Baker's objects, where the cyst's neck joins the joint
  [R-BAKER]. Kind: a thin dark line, dark on every sequence as a ligament is (Claude's reading of the
  proof's fat-dark coronal, 2026-10-15: at the outer recess the fluid lies between the capsule's thin
  dark line and the femur's shell). Where: the synovial compartment's outer edge, outside the joint's
  fluid in the recesses and inside the fat and muscle round them. Views and slices: the fat-dark
  coronal and axial, where the white inside it draws its line; the synovium's slices. Provisional
  reading: the thin low signal that bounds the joint fluid's recesses on the side away from the bones.
  The twelve: Effusion and Synovitis (it bounds their compartment), Baker's (its back wall).
- **The gastrocnemius–semimembranosus bursa** (where a Baker's cyst forms). Meaning: the bursa beneath
  the medial gastrocnemius head, between it and the semimembranosus tendon, joined to the joint
  [R-KNEE], [R-BAKER]; collapsed when there is no cyst (Claude). Interstitial again: between two parts
  already found on the axial, behind the inner condyle. Kind: fluid, white on the fat-dark
  fluid-sensitive views and dark on T1 (where muscle's rule already leaves out the twin's white, so a
  cyst is not named muscle). Views and slices: the fat-dark axial first, where medicine reads Baker's
  [AUR]: the slices from the tendon's (the top of the tibia) up to the head's (the condyles), the two
  parts carried from slice to slice by place («anatomy is contiguous from slice to slice», §8); the
  squint's tiles in the seam whose maximum is as white as fluid show which of those slices hold fluid;
  the sagittal slices through the back-inner corner show its neck. Provisional reading: the seam the
  head and the tendon share, and what the fluid lens sees in it: white, joined by a neck to the
  joint's back recess, is a distended bursa. The twelve: Baker's.
- **Lateral gastrocnemius head.** Meaning: the calf muscle's outer head, from the back of the femur's
  outer condyle (anatomy). Kind: muscle, resolved as muscle already is: on the fat-bright views the
  leg's places outside every part named, darker than fat, the bodies at least a centimetre across; on
  the fat-dark views the suppressed fat between the muscles parts each belly from the next, so the lens
  draws each as a region of its own. Where: behind the femur's outer condyle, on the knee's outer side
  of the notch, the medial head's place mirrored. Views and slices: the fat-dark axial (on the proof's
  middle axial slice the lens already draws it as a region of its own), on the axial slices through
  the condyles, which the femur carried onto the axial shows; and the sagittal and coronal slices
  behind the outer condyle, by place, where muscle is named. Provisional reading: the medial head's
  rule on the outer side of the notch, behind the outer condyle's peak, with muscle's light on the
  fat-bright twin as one more description. The twelve: none directly.
- **Popliteal vessels** (the artery in front of the vein [Kh]). Kind: tubes; on the proof's fat-dark
  slices they are as white as fluid, round on the axial and long on the sagittal. Where: behind the
  notch, between the two gastrocnemius heads, continuing from slice to slice down the axial series:
  the squint's tiles behind the notch whose maximum is as white as fluid follow them from slice to
  slice without the lens. Provisional reading: round white bodies behind the notch between the
  heads, apart from the joint (not joined to it, which parts them from a Baker's cyst), carried slice
  to slice. The twelve: none (landmarks; to be told apart from Baker's and Effusion).
- **Patellar retinacula.** Low-signal bands from the patella to the femoral condyles, best seen on the
  axial [C], [Kh]. Kind: bands dark on every sequence, as ligaments are, resolved as the MCL is: low
  signal joining two parts already found. Views and slices: the fat-dark axial slices through the
  patella, found by carrying the patella onto the axial by place (owed, Law 9), as the leg is carried
  to find the top of the tibia. Provisional reading: on those slices, the low signal joining the
  patella and each side of the femur. The twelve: none (PF OA's neighbours).
- **The lateral complex beyond the LCL: popliteus tendon, biceps femoris tendon, iliotibial band**
  [Kh], [LP-PLC]. Kind: tendons and a band, dark on every sequence. Where, relative to parts found: the
  popliteus tendon at the femur's outer condyle's notch, medial to the LCL (the LCL's band now takes
  it in); the biceps tendon reaching the fibula's head beside the LCL; the iliotibial band in front of
  them on the outer side. Views and slices: the coronal slices through the fibula's head and the outer
  condyle (the LCL's slice is one of them) and the axial slices from the condyle down to the fibula's
  head, each found from the fibula and the femur carried by place; medicine reads them on the coronal
  and axial T2 FS [AUR]. Provisional reading: the dark-band rules (thick, uniformly dark, joining two
  parts) with these targets. The twelve: none directly.
- **The other hamstring tendons.** The semitendinosus, a smaller black oval behind the semimembranosus
  tendon on its slice (seen on the proof), and the pes anserinus tendons to the front-inner tibia
  [LP-MED]. Kind: tendons, cut across on the axial as black ovals, as the semimembranosus tendon is.
  Views and slices: the fat-dark axial, from the semimembranosus tendon's slice up toward the condyles,
  each tendon followed from one slice to the next by place («anatomy is contiguous from slice to
  slice», §8); the sagittal slices through the back-inner corner by place. Provisional reading: the
  semimembranosus tendon's rule, the piece behind it. The twelve: none directly (Baker's neighbours).
- **The two fat pads above the patella, parted.** Meaning: the quadriceps (anterior suprapatellar) and
  the prefemoral (posterior suprapatellar) fat pads [R-KNEE], «on either side of the suprapatellar
  recess» [R-EFF], named together now as the suprapatellar fat (§5). Interstitial: the recess between
  them is the synovial compartment's upper reach, so the synovium's compartment, once found, parts
  them. On the proof the recess is collapsed: a film of faint white with fat suppressed and a faint
  dark curve without it (Claude's reading, 2026-10-15). Views and slices: the fat-dark and fat-bright
  sagittals through the suprapatellar recess, and the axial slices above the patella. Provisional
  reading: the suprapatellar fat split along the recess's film, the part in front of it the
  quadriceps pad, the part behind it the prefemoral pad. The twelve: none directly; the recess
  between them fills in Effusion.
- **The patella on the axial, the menisci on the sagittal.** Not new parts, but the views medicine
  reads them on (the patellofemoral joint on the axial, the menisci's horns on the sagittal): carried
  there by place from where each is found, onto the axial slices through the patella and the sagittal
  slices through each compartment.

## 7. How to build the next ones

The loop of `docs/HOW_TO_BUILD.md` §7, part by part, in the order of `docs/OBJECTS_AND_CONDITIONS.md`:
1. Read the part's provisional entry, and medicine's words for it. Ask what it lies between, beside or
   inside, among the parts already found.
2. Look at the pictures of the proof, at the part's own pixels, on every view that shows it, at its
   best slices there (its entry's views and slices, §6; the collapse, §8): which view shows it
   plainly (fat-bright or fat-dark; sagittal, coronal or axial), and which lenses (light, low signal,
   territories, distance and peaks, the twin, the squint) add up to it and take away what is not it.
   Never one lens alone.
3. Write that reading as a few descriptions, each one check with a named code, its numbers from
   anatomy, a source or the picture (labelled), its targets the parts already found; draw it on the
   proof before it touches the run, and look.
4. Write it in `src/knee/objects/assignments.py` with its paragraph, add a test, run the proof through
   `scripts/run_interiors.py`, look at every picture it reaches, run the gate, commit, and show Rohan.
5. It is done when it is resolved once. Do not chase the studies where it is a bit off.

## 8. The collapse: every part at its best slice, across the five views

Rohan, 2026-10-15, asked: «what do you mean by "all five middle slices"? Read the "what an <object> is
thesis, send a cheap agent to look into the dimensional collapse parts and slice selection parts of
the information theory parts that are relevant for this as well. I think that you missed the point of
this part of the thesis, and we need to get to fixing the implementation in another session». Told
that it meant the one slice the run reads from the middle of each of the proof's five series, he
answered: «Okay. That is a not-invalid slection. The "middle" is a fine standard first slice to
select. For other elements that are not obvious in that one slice, etc, that is a fine standard.
There are five different views (different angles and fat-bright vs fat-dark), and each has multiple
z-slices. That is where the thing being mined is relevant--discovery of ALL elements of the anatomy at
their best slices and resolution across the 5 images/3 orientations». His words before it: in the
input stage's note (`knee.study`, 2026-10-10), «we need ALL the data to be available for each series,
but we will use dimensional collapse to throw away a solid majority per analysis step, yet stay
lossless ... *I* decide what gets compressed»; and 2026-10-14, «Is it not obvious which slice to use?
The one that is able to show the anatomical region needed for identification of each anatomical
object, and then for diagnosis.» · «are you actually going to re-compute on every single slice?
Because that's completely wrong».

**What the run does now** (`scripts/run_interiors.py`, read whole 2026-10-15). It reads the lens on
each series' middle slice, the floor of half its stack (`knee.study.series.selected_slice`), and names
there every part that slice shows. It makes the squint over every slice of every series once, and
keeps it; of the squint only the fibula's search reads anything, the tiles' centres and bounds, and
nothing reads the tiles' light. Four parts not plain on the middle slice get a slice of their own,
none chosen from the squint: the fibula's, where its region is largest, found by reading the lens's
territories on a block of every slice that holds it; the ACL's, the middle slice's neighbour on the
knee's outer side, by place from the header; the LCL's, the coronal slice through its attachment on
the fibula; and the semimembranosus tendon's, the top of the tibia, found by carrying the leg onto
each axial slice without reading the lens there. What the next session fixes is his sentence above.

**The thesis's own text.** *What an <Object> Is* is
`../cell_tracking/docs/pipeline_thesis/paper/what_an_object_is.md`; the information-theory corpus, his
words with the lead's reading of them, is `../cell_tracking/docs/pipeline_thesis/INFORMATION_THEORY_CORPUS.md`.
Each section below was read whole on 2026-10-15; its lines are as found then.

- The collapse (the paper's §4, lines 2113–2308): «The first move of **H1** (vision built from the
  laws) is to stop rereading what the movie's laws hold nearly constant (§3). We call this move **the
  collapse**. The movie is read as flat two-dimensional stills, one for each lens at its own depth, and
  time is followed by small shifts from three time points resolved in full.» Its warrant (§4.1): «What
  is nearly invariant is each cell's own depth ... That invariance does not put the cells in one plane.
  ... So the collapse makes several flat pictures, each at its own depth.»
- Each lens at its own depth (§4.2): «Each nucleus is sharpest at its own depth, so a flat picture at a
  well-chosen depth holds the nuclei there whole. To choose the depths, the system measures how in
  focus each slice is.» «Each lens stands at its own sharpest slice, and its picture is the recorded
  light at that slice. There it draws the **bodies** it sees ... A lens with nothing clear to say
  abstains. Nothing is averaged or merged.» «Two lenses at about one depth read one plane two ways, and
  each corrects the other's borders. Lenses at different depths are the three-dimensional structure
  itself.» «So which lenses share a plane changes from plate to plate.»
- Depth kept as a number (§4.3): «**The composite** keeps depth another way, as a number at each place.
  ... Bright spots are found through the whole volume at a nucleus's scale. Each is given its own
  slice: near where it was found, the slice at which the light over a nucleus-sized disc around it is
  brightest. Every place of the grid is then shown at the slice of its nearest spot, and keeps that
  slice as a number». «It is also the least clean of the five pictures, so it never pulls a cell and
  never decides alone: it points.» «Depth is peeled, never reconstructed. Each cell taken leaves the
  volume through its band, the slices it occupies, together with its halo, and the next round reads
  again what is left.»
- The squint (§1.3, lines 290–377; §4.5): «a view's fidelity reduced on purpose, so that the dimension
  a question reads stands clear of the variation it does not read.» «A squinted view is lossless for
  what it measures. A tile's median is exactly that tile's median, with no error in it.» «The laws say
  which reductions are safe: those that flatten only what the laws hold nearly constant». «Each lens is
  coarse, but the lenses' joint description is precise».
- What a step removes (§4.6): «In a round each lens draws the whole field from one slice of the 64».
  «Every loss is taken in a view or in how a reading is written, never in what is kept». «**reading by
  exclusion**: a reading that is poor at finding a signal can be reliable at saying where the signal is
  not.» «The collapse turns a four-dimensional search into flat, categorical questions, each asked where
  the laws say its answer lies.»
- One object, many views (§1.3): «A squinted view answers one question. An <object> is read through many
  views, each exact about what it reads. A face is often recorded in two photographs, one from the
  front and one in profile: two views at right angles.» «No view is the truth alone, and what an
  <object> is, is what the views recover together.» «Each view is incomplete by construction, and the
  pair is complete.»
- The recipe for another domain (§14.1–§14.2, lines 4342–4409): «*Name one lens per term of the law.*»
  «*Read the priors as regime keys.* The priors, cheap readings of the whole field taken once, point
  and never decide alone.» Its MRI row: the laws, «A tissue's brightness is set by its magnetic
  relaxation under the sequence; anatomy is contiguous from slice to slice»; the lenses, «One per
  sequence».
- His words in the corpus: «If a domain space is defined and constrained, information reveal in one
  axis/dimension is *implicitly* information reveal about the whole rest of the domain» (§2, lines
  84–147); «These lenses are smaller, lossy views of the whole field, and that's a STRENGTH» and
  «"colliding" doesn't mean "useless", it means what they're seeing are two lossy representations of
  the same view, which is important and makes it MORE useful» (§4, lines 210–258); «the meaning of what
  a "cell" signal is at this time point is a holographic prjection of the orthogonal, lossy vector
  representations of the truth. None is "the truth" in isolation» and «If a cheap measure can tell you
  only that something *might be* important, then when it measures that something *isn't* important,
  you can throw it away confidently» (§5, lines 259–318); «if the cells aren't really moving, why
  pretend they are? Get the position and measure the change. it's the smaller number» (§10, lines
  504–548).

How this carries onto the knee's five views and their slices (what the knee's depth is, which of its
lenses stands at which slice, what its composite is) is not stated for the knee in his words. It is
the next session's to settle with him, from his sentence above and this text. The "views and slices"
lines of §6 are Claude's provisional readings toward it, to be checked against this text with him;
they are not that mapping.

**Planning update, 2026-10-16:** The anatomy definitions are now demonstrated (§9). The proposed
MRI application of the collapse, its implementation order and the checked Fable consultation
are in `docs/DIMENSIONAL_COLLAPSE_PLAN.md`. This is a proposal, not an implemented replacement
for the current selectors. It preserves the middle as a valid bootstrap and starts with one
complete fibula selection/extent/cross-view operation through the existing lateral consumers.

## 9. Definition pass, 2026-10-15: objects first, collapse after

Rohan clarified the order: resolve every object with a stable anatomical definition and a competent
demonstration at least once; the full dimensional-collapse work follows that. Generalization and
robustness belong to the later AI work he has deliberately not explained. This supersedes the earlier
"collapse next" ordering, not the description of the intended collapse.

### Anterior synovial recess and synovial lining surface

The cavity, its fluid, and its lining are separate things. On the proof's fat-suppressed sagittal
slice 18 the bright pocket behind the patella is visibly separated from the femur and from the fat
in front of it. The rule (`anterior_synovial_recess`) reads the existing white-fluid measurement,
not the final fluid label: that label leaves out this pocket because it is not within the old rule's
reach of a bone or the tibiofemoral joint. The pocket's anatomical relation identifies it:

1. A sagittal, fat-suppressed, fluid-sensitive slice names the femur and patella.
2. The target place is behind the patella's middle, in front of the femur's middle and above the
   patella's lower end, excluding named solid structures at the target place. All positions come
   from the patient's axes and named parts.
3. Of the connected white bodies intersecting that place, keep the largest whole body. This is the
   anterior recess, not all of the synovial compartment.
4. Its anterior boundary locates the lining against the fat. The returned surface is sampled on the
   cavity side: it localizes the lining, and does not measure membrane thickness or its full extent.

The two saved masks are `a2_anterior_synovial_recess` and `a2_synovium`; they coexist with the original
fluid and tissue labels rather than erasing them. Each has its own named/abstain decision. The
existing physical-place match lays them onto the other sagittal sequence. The cavity relates to
Effusion and the lining to Synovitis. There is no new numerical cutoff. Named refusals are in
`synovium_code` and the module's numbered definition.

Checked through `scripts/run_interiors.py --draw` on the proof, with both sagittal pictures inspected.
Pictures and records: `data/pictures/definitions-20261015/assignments/<proof uid>/` and
`data/measurements/definitions-20261015/interiors/`. This supersedes the earlier statement that the
synovium has no decision of its own. Full cross-view coverage remains the later collapse work.

### Joint capsule at the side recesses

On the proof's fluid-sensitive coronal slice 15, the image-left bright gutter lies between the
femur's dark cortex and a second dark line outside it. That outer line is the capsular wall.
`capsule_at_side_recesses` describes that relation: each side recess is a connected white body
outboard of its meniscus, at or above the menisci's lower end, reaching the femur through its shell.
Use the largest eligible body on each side. The wall is measured low signal outside that body on
the side away from the femur, over the recess's height. The existing 2 mm shell/contact allowance
locates adjacent tissue; it is not a capsule-thickness estimate or a new fitted number.

The separate mask `a2_joint_capsule` preserves its overlap with collateral structures. It has its
own decision (`capsule_code`), is serialized through the real run, and is laid onto the coronal
twin by the shared physical-place match. Both coronal outputs were inspected after the proof run.
This demonstrates the wall at a side recess, not the capsule's entire envelope across all slices.

### Gastrocnemius-semimembranosus bursa: its fluid-filled body

The bursa is the pocket between the medial gastrocnemius and semimembranosus tendon. A visible
fluid-filled example is study `…13335129881737731410081002627729200903`, axial slice 14, already
selected by the tendon's existing tibial-top rule. Its report describes a popliteal cyst; the rule
does not read that report or its label. The acquired picture shows the dark tendon and, behind it,
the bright pocket along the muscle's edge.

`bursa_on_slice` reads the existing fluid/marrow contrast on that same slice, the tendon, the
posterior territory selected by the existing region rule, and patient positions. The territory is
a broad target and includes non-muscle tissue; it is not treated as an exact muscle boundary.
The body is the largest connected white component with its middle behind the tendon, before the
posterior territory's middle, on the knee's inner side, and reaching that territory through the
existing contact allowance. A direct white connection to the tendon is not required: its thin
neck can be dimmer. This replaces the preview's incorrect assumption that the bright body itself
must touch the tendon through a 2 mm gap; the visible neck is longer.

The rule reuses the tendon's lens, field and carried leg. Its independent mask is
`a2_gastrocnemius_semimembranosus_bursa`; the white reading is retained as `a2_fluid_signal`.
`bursa_code` distinguishes missing landmarks from no white body in the expected place. On the
proof's axial slice 11 it abstains because no separate posterior region is found there; that is
not a diagnosis of absence. Through the real run, the fluid body is named on the example study and
the two main-slice pictures were inspected. The neck's full extent across slices and the bursal
wall remain wider coverage, not claims made by this mask. Diagnosis is still deferred.

### Lateral gastrocnemius head

The lateral gastrocnemius head is the calf muscle's outer belly behind the femur's outer condyle,
the medial head's counterpart on the knee's outer side. This supersedes
its provisional entry in §6: no new lens was needed, and the "muscle's light on the fat-bright twin"
that entry proposed as an extra description is not used. It is named on the same fat-suppressed
axial middle slice as the medial head, from the lens already read there.

`name_the_back_of_the_knee` names both heads in one pass. The femur and tibia carried onto the
axial by place, the notch's plane from the middle sagittal slice, the slice's territories and their
ordered peaks are computed once and shared by both heads. For each patient side the same two
operations run: `inner_condyle` picks the bone-holding territory with the deepest peak on that side
of the notch, and `gastrocnemius_head` picks the deepest territory holding none of the bones' places
whose peak lies on that side and behind that condyle's peak. The lateral head negates the physical
inner-axis distance (toward the inner side becomes toward the outer side); nothing else changes and
there is no new numerical cutoff. Each head is placed only where no object is already named, so no
earlier part loses a pixel, and the two heads cannot overlap.

The common prerequisites keep their common refusals for both heads (the leg must run through the
plane, the header must name the knee, fat must be suppressed, the bones must be carried, the middle
sagittal must give the notch). The two side-specific refusals are `abstain_no_outer_condyle` and
`abstain_no_body_behind_the_outer_condyle`. Label 30 (`lateral_gastrocnemius`) is saved in
`a1_objects`, its territory in the record and its decision in the codes, through the same `save`
and receipt as every other part; the renderer draws it bright green beside the medial head's olive
and rings its territory's peak.

On the proof (a right knee, axial slice 16; the picture is
`data/pictures/definitions-20261015/assignments/<proof uid>/05-axial-fs1-fat1.png`) the outer
condyle is territory 3 (15.2 mm), the lateral head territory 5 (12.5 mm, 3203 px) and the medial
head territory 6 (10.1 mm); both heads are `identified`. Read off the picture at its own pixels:
the green fills the grey belly behind the outer condyle from the condyle's back margin to the fascia
at the back of the leg; it stops at the dark fascia on the outer side, so the tissue beyond it is
not taken, and at the territory edge toward the midline, which leaves the popliteal artery and its
bundle to the medial head's territory as before. Its limits and overreach: at its back-inner corner
it reaches into the dark fat round that bundle, with unnamed low-signal holes in it; the thin strip
under the skin along the back of the leg, below the lateral head too, is the medial head's
territory (the medial head's recorded overreach, not a lateral name); and the mask says nothing
about where the belly ends on other slices. Whether the green is the lateral head is read from the
picture; the receipt and the tests only check the bookkeeping.

Over the 58 labelled studies, after the canonical run was refreshed with this code, it is named on
9 axial series of 9 studies; of the other 72 axials, 46 abstain because the header names no knee,
8 because fat is not suppressed, 15 find no body behind the outer condyle and 3 no outer condyle;
every sagittal and coronal series says the leg runs in the plane. Both heads are named on the same
slice in 3 studies, the proof among them. Those other axials are
not checked for anatomy here: the one demonstration on the proof is the claim.

### Popliteal artery and vein lumens

On the proof's fat-suppressed axial slice 16, the artery's dark round interior is enclosed by a
brighter ring; the vein's elongated dark interior lies behind it. Both lie behind the condyles,
between the gastrocnemius heads. This supersedes §6's provisional white-body description: this
definition reads the enclosed dark lumens visible on this slice.

The rule combines the enclosed-darkness lens with the anatomical positions already measured for
the two heads and condyles. Consider complete connected interiors between the two head peaks,
behind both condyle peaks and before the heads' posterior extent. Keep interiors with a body at
the existing 2 mm small-body scale, which separates a body from a thin seam; retain the whole
component, not just its thick core. Of these, select the two with greatest mean enclosed darkness.
Their posterior positions name the anterior lumen artery and the posterior lumen vein, using
the anatomical order in `OBJECTS_AND_CONDITIONS.md` [Kh]. There are no proof coordinates or chosen
grey levels in the rule. Missing landmarks, fewer than two eligible bodies, or indistinguishable
posterior positions produce named abstentions.

Through `scripts/run_interiors.py --draw`, both are `identified` on the proof's axial slice.
The saved masks `a2_popliteal_artery` and `a2_popliteal_vein` hold 44 and 48 pixels respectively;
these are observations, not constants in the rule. The depth reading, corridor and all closed
components are retained alongside them. Both masks coexist with the earlier tissue labels.
The canonical assignment picture and the close view
`data/pictures/definitions-20261015/popliteal-lumens-proof.png` were inspected against the acquired
signal: each outline follows its separate dark lumen body.

Rohan's criterion for this stage is whether a rule can be established and the lumens measured.
Both answers are yes. Exact specification and precise measurement belong to the later AI work
he has yet to specify; this completes this element's definition pass. These vessels are landmarks,
with no direct category among the twelve conditions.

### Semitendinosus tendon — 2026-10-16

The semimembranosus tendon's axial slice also shows the semitendinosus as a separate dark oval
behind it, on the knee's inner side. In `ee5480b`, `dark_tendon_bodies` performs the existing
semimembranosus candidate construction once: low signal outside the air, skin and black margin,
with one-pixel cracks closed, the existing 2 mm small-body operation, and connected components.
It also reads each body's mean posterior and inner positions once. Both selectors receive the
same labels and positions; the semimembranosus selection keeps its established behaviour.

`semitendinosus_on_slice` selects bodies whose mean lies inside the inner condyle's peak and
behind the semimembranosus body's posterior extent. Of those, it keeps the whole body nearest
the named tendon in physical distance. Missing references, no eligible body or an exact nearest
distance tie return named abstentions. The anatomical relations select it, with no proof
coordinates, component numbers or new numerical cutoff. A separate mask, `a2_semitendinosus`,
retains the result alongside the earlier labels. The shared candidate map and positions are
kept too. There is no second slice search or lens reading.

The real entry point names the proof's axial slice 11: semitendinosus 46 pixels, semimembranosus
72 pixels. The latter and every earlier proof decision and array are unchanged. The enlarged
raw/low-signal/outline picture was inspected at its own pixels:
`data/pictures/definitions-20261016/semitendinosus-proof.png`, BROWN semimembranosus and SILVER
semitendinosus. These are two separate dark bodies. This resolves a cross-section, not the whole
tendon's course; joined dark bodies remain a limitation. No competition condition names it
directly. This supersedes the semitendinosus part of §6's provisional hamstrings entry; gracilis
and sartorius remain unresolved.

### Quadriceps and prefemoral fat pads — 2026-10-16

In `096f667` the combined suprapatellar fat is split into the anterior quadriceps wedge behind
the quadriceps tendon and the posterior prefemoral strip against the femur. Their intervening
recess is faint bright on the FS sagittal and dark on the non-FS twin. The earlier preview's
FS-only maximum sometimes followed the field's outer edge. The production definition combines
the two acquired signals at the same physical places, using the pair's existing match.

`relative_signal` is the ratio of those acquired signals, with unavailable or zero-denominator
readings kept as NaN. Positive multiplicative changes to either acquisition preserve its
within-slice ordering; additive offsets need not. `suprapatellar_pads` reads independent
cross-sections along the native axis closest to patient superior. Inside the already named fat,
the greatest internal ratio locates the seam, with fat on both sides. A flat section or separated
equal maxima gives no seam there; a contiguous maximum band is kept whole. Nothing is
interpolated between sections. The named fat anterior to the seam is the quadriceps pad;
posterior is the prefemoral pad. Patient-axis positions are shared, with no proof coordinates,
new signal cutoff or fitted smoothing.

The real entry point identifies both on the proof's FS sagittal slice 18 and lays them onto its
non-FS twin. Separate arrays are `a2_quadriceps_fat_pad`, `a2_prefemoral_fat_pad` and
`a2_suprapatellar_recess_ridge`; the source also keeps `a2_nonfs_signal` and `a2_relative_signal`.
The FS masks hold 472, 744 and 47 pixels respectively, observations rather than rules. The full
two sagittal outputs and the enlarged picture were inspected:
`data/pictures/definitions-20261016/suprapatellar-pads-proof.png`. All earlier proof decisions
and arrays are unchanged. The gate passed with 216 tests.

This is a competent partition on the selected slice. The seam can deviate near its ends, the
inherited combined mask includes neighbouring tissue, and the top of the picture clips the
pads. The result asserts neither membrane thickness nor full extent. Neither pad has a direct
competition label; their recess relates to Effusion. This supersedes §6's provisional fat-pad
entry. Fable independently described the anterior wedge and the strip on the femur, flagged the
nearby cortex and the faint upper seam, and explicitly did not claim the proposed computation
was verified; the lead checked the actual production output. The prompt, prior lead reading,
answer and API usage are retained in `data/readings/definitions-20261016/fat-pad-seam/`.

### Medial and lateral patellar retinacula — 2026-10-16

In `be52965`, both retinacula are localized as the dark outer bands beside the bright recesses
between the patella and femoral condyles. The native named patella is carried in physical space;
its centre selects one axial slice for both walls (slice 22 on the proof). The header names the
knee's inner and outer sides. The sequence must be fluid-sensitive and fat-suppressed.

The carried patella and femur are sparse targets, not segmented axial bone masks. Their native
lens regions are reach targets only. The posterior interval runs from the carried patella's mean
posterior position to the strongest existing peak in the femur-holding region. On each side of
the patella's mean inner position, select the largest connected white-fluid body in that interval
reaching both holder regions through the existing 2 mm contact allowance. The white reading uses
the existing fluid-to-marrow relation on carried femoral support.

On each native cross-section nearest patient posterior, read the acquired-signal minimum in the
available nonwhite strip extending outboard from the selected recess by that same contact
allowance. Keep the whole contiguous tied minimum only when darker than the neighbouring fluid
on that section; separated ties give no wall there. This is the lead's reading of the visible
band, without a new signal cutoff, smoothing or proof coordinates. Both sides share the lens,
landmarks and measurements. Missing landmarks and missing recesses have named refusals.

The real entry point identifies both on the proof: `a2_medial_patellar_retinaculum` holds 70 pixels
and `a2_lateral_patellar_retinaculum` 65 pixels. These counts are observations, not rules. The
selected recesses, exterior strips and per-section readings remain saved alongside the masks.
The production output and enlarged view were inspected and shown:
`data/pictures/definitions-20261016/retinacula-proof.png` (AMBER medial, ROSE lateral). Earlier
proof decisions and arrays are unchanged. The full gate passed with 229 tests, including empty
references, missing recesses, brighter exterior strips, contiguous and separated ties, transposed
native axes, reversed anatomical sides, driver refusals and individual abstention recording.

This resolves each band on one slice, not its thickness or full three-dimensional course. Coarse
holder regions can include surrounding tissue; they are never treated as exact bone boundaries.
Neither retinaculum has a direct competition label. This supersedes §6's provisional entry.

### Popliteus tendon at the lateral femoral sulcus — 2026-10-16

In `8fa091d`, the popliteus has a separate mask and decision on the LCL's existing coronal slice.
On the T1 proof picture, the tendon occupies the inward notch in the outer condyle, medial to the
longitudinal outer strip and above the joint line. The existing LCL region already includes this
body. Its identity is positional: the dark/grey tendon in the condyle's sulcus, distinguished from
the bright marrow and the more lateral cord. No new grey-level cutoff is needed.

`convex_envelope` measures the pixel-centre convex hull of a mask, with only floating-point
roundoff allowed in its half-plane test. It knows no anatomical question. `popliteus_in_notch`
intersects that envelope's exterior-to-femur places with the existing LCL region, then keeps the
largest four-connected component. The femur is the region already carried from the same series'
middle slice by the LCL step. Thus both the anatomical slice and its lens and bone target are
reused; the previously computed femoral target is now retained, rather than discarded. Empty
targets, degenerate hulls and no eligible notch have named readings/refusals.

The non-FS definition supplies `a2_popliteus_tendon`; it coexists with the original `a1_objects`
LCL label. The pair's existing match carries this independent mask onto the fat-suppressed view,
where the native femoral territory merges much of the tendon into bone. An unseen mapping is
explicitly excluded, and a transferred mask never erases another object's label. The envelope,
vertices, equations, candidate mask and candidate labels remain saved. The rule adds neither a
new anatomical scale nor a coordinate taken from the proof.

Through the real entry point, the T1 proof's coronal slice 21 returns `identified`, 251 pixels;
the paired FS slice returns `laid_from_its_partner`, 155 pixels. These are observations. Both
production pictures and the enlarged view were inspected and shown:
`data/pictures/definitions-20261016/popliteus-proof.png` (SAGE). The full gate passed with 246
tests; earlier proof decisions and arrays are preserved. The new tests include empty/collinear
inputs, a convex bone with no notch, exclusion of unrelated regions, transposition/reflection,
overlapping label and mask transfer, unavailable pixels and missing mappings.

This is a localization in the sulcus: it can include a cortex rim and leaves the outer portion
of the cross-section, and does not claim the whole tendon course. No competition category names
it directly. The independent Fable reading agreed that the notch content is consistent with
tendon by position, offered alternative local candidates and did not verify a computation;
the lead inspected the geometric preview and actual production result. Prompt, prior lead
reading, response and usage are in `data/readings/definitions-20261016/popliteus-reading/`
(9,323 input tokens, 7,619 output tokens; no monetary amount was returned). This supersedes the
popliteus part of §6's provisional lateral-complex entry; biceps femoris and iliotibial band remain.

### Iliotibial band — 2026-10-16

The ITB is localized on the existing non-fat-suppressed middle coronal: the dark fascial line
directly deep to the lateral subcutaneous fat, passing the lateral femur and reaching the
proximal tibia. Chien 2020's complete lateral-knee subsection and Figure 29 supply the anatomy;
the actual raw stack and enlarged output supply the visual check. This slice lies anterior to
the proof's LCL slice. The production rule does not add a separate LCL-slice comparison or search.

On each native cross-section across the leg, the named fat outboard of the named bones defines
the outer layer. Read the acquired-signal minimum in the available non-fat, non-bone strip within
the existing 2 mm contact allowance deep to its inner edge. Keep a contiguous minimum only when
darker than both the fat and the next equally wide strip deeper in the leg. Thus a monotonic
fat-to-muscle transition does not name a band. Separated tied minima abstain locally; nothing is
smoothed or interpolated. Keep the trace above the most superior section where it reaches the
tibia through that allowance, and require a section beside the femur. The continuation below
that level is retained as a candidate reading, without naming it ITB.

`iliotibial_band_on_slice` reads the existing named fat, bones, patient axes and shared tibial
distance. `name_iliotibial_band` runs before the existing save point and lays the separate
`a2_iliotibial_band` mask onto the FS twin through the pair's cached match. All earlier primary
labels remain intact. The layer, strip, candidate trace, per-section status and light readings,
and distal stop are retained as `a2_itb_*` arrays. Missing landmarks, no valid dark dip or a band
that does not reach the tibia have named refusals. No new signal cutoff or proof coordinate is used.

The real proof run identifies 221 pixels on non-FS coronal slice 15 and lays 139 pixels onto its
FS twin; counts and index are observations. Both acquired/output pairs were inspected at native
pixels and shown in `data/pictures/definitions-20261016/itb-proof.png` (AQUAMARINE). Earlier proof
records, their decisions and saved-array digests are unchanged, apart from added ITB fields.
This resolves a trace of the course where the band adjoins fat, not its thickness, exact Gerdy's
tubercle insertion or full extent. Thin sections can abstain, and a deeper band would not be
reached by this particular relation. There is no direct competition condition for the ITB.
Sonnet's implementation and usage are retained in `data/readings/definitions-20261016/itb-worker/`;
the lead independently inspected and integrated the result. This supersedes the ITB part of §6.

### Biceps femoris tendon — 2026-10-16

The competent portion is the substantial dark tendon below the posterior thigh muscle, reaching
toward the fibular head, on a sagittal slice near its lateral face. The first axial/distal
survey did not separate the conjoint insertion from cortex and LCL; that survey is not counted
as a resolved object. The subsequent sagittal prototype and actual production output were
inspected. The anterior arm can include the distal LCL neighbourhood; this is a localization,
not separation of every fibre at the conjoint insertion.

The already named fibula's physical places recover its main sagittal plane and provide marrow
light in both acquisitions. Walking outward from there, `lateral_to_the_head` asks only for the
marrow-like head body on each reached slice. The first body below the existing 1 cm bone-disc
area selects the lateral peripheral slice. This is a proxy for the head's lateral face, close
to its area boundary on the proof; it is not tuned to the observed index. The head's native-pixel
opening is a sampling operation. Measured-empty bodies and unreadable or unvisited slices are
kept distinct by their codes, status and NaN areas. The rule never scans full anatomical
assignments across the series.

On the selected slice, acquired light is read as a median along the leg: dark against the
non-FS marrow, and no brighter than suppressed marrow in the physically matched FS acquisition.
That combination separates the cord from fat and the brighter FS muscle. Select the largest
competent dark body below the largest muscle belly above the head and above the head, clear
of bright-body cortex, reaching both broad targets. The existing physical body and reach scales
have their roles stated in the module definition; exact largest ties abstain. An unseen pixel
gives no filter reading. The selected body and every actual contrast, head, area, status and
reach reading are retained, with an independent mask `a2_biceps_femoris_tendon` and named decision.

`biceps_native` resolves the source once; `biceps_femoris_slice` reuses it for the paired sequence.
The twin's slice is found by physical place, with no equal-index assumption. The existing match
and `lay_parts` carry the mask without changing earlier primary labels. Through the real entry
point the proof identifies 2,276 source pixels and carries 1,463 onto the FS twin, both on
slice 34 (observations). Both enlarged output pairs were inspected and shown:
`data/pictures/definitions-20261016/biceps-proof.png` (KHAKI). Source and twin reference light
are 350 and 57 on this proof; these too are observations. Besides the LCL overreach, the mask
omits tissue near bright bodies and does not claim the full course. There is no direct label
among the twelve. Sonnet's prototypes, implementation, wiring and usage are retained in the
`biceps-*` readings directories for this date. Fable's preceding sagittal reading located a
different thin-band candidate; its approximate positions were not used as selector constants.
The lead accepted the subsequent actual substantial-body output. This supersedes the biceps
part of §6's provisional lateral-complex entry.

### Gracilis tendon — 2026-10-16

On the semimembranosus tendon's existing tibial-top axial slice, gracilis is the thinner,
separate dark cord medial to both semimembranosus and semitendinosus and anterior to the latter.
`native_dark_bodies` measures the same low-signal map through a complementary sampling lens:
close native-pixel cracks with a 3×3 square, then open with the four-neighbour cross and label
the bodies. This retains a cord the existing 2 mm body operation removes. The old shared lens,
semimembranosus and semitendinosus are untouched; patient positions and available field are reused.

`gracilis_on_slice` excludes bodies overlapping either known tendon, then applies those medial
and anterior relations to whole bodies and keeps the nearest to their pair in physical distance.
Missing references, no eligible body or an exact nearest tie give named refusals. No signal
cutoff, proof coordinate, component number or new anatomical size enters this selector.
Labels, mean positions, eligible IDs and distances remain saved beside `a2_gracilis` and its
decision. It is a companion of the existing semimembranosus group, with no second slice or lens
search; the native-pixel lens is made once on that slice.

The real proof run identifies 22 pixels on axial slice 11, the inspected separate cord, while
the previous semimembranosus and semitendinosus remain 72 and 46 pixels. These counts and index
are observations. The acquired/low-signal/three-outline output was inspected and shown:
`data/pictures/definitions-20261016/gracilis-proof.png` (AZURE gracilis, BROWN semimembranosus,
SILVER semitendinosus). Native opening can trim the corners, and joined dark bodies remain a
limit; this is a competent cross-section, not the full tendon. Its anatomical relation agrees
with the medial-knee sources and Vohra 2011's Figure 1 key points (`OBJECTS_AND_CONDITIONS.md`
[V]). No competition condition names it directly. Sonnet's prototype and implementation are in
`medial-prototype-worker/` and `gracilis-implementation/`; the lead independently checked the
actual masks. This supersedes the gracilis part of §6's provisional hamstrings entry.

### Sartorius muscle — 2026-10-16

On the proof's middle fat-suppressed axial, sartorius is a flattened grey muscle sheet medial
and anterior to gracilis, rather than another black tendon cross-section. Vohra 2011's complete
Imaging Anatomy section and Figure 1 key points give the medial relationship ([V] in
`OBJECTS_AND_CONDITIONS.md`); the actual acquired slice and enlarged production output supply
the visual check. The middle slice is the existing standard first slice, not a new slice search.

`local_lightness` measures a native 3-pixel median of seen, non-low acquired samples against
the median of the seen light in a surrounding 20 mm window, whose odd pixel dimensions come
from the actual spacing. Unavailable, nonfinite, low-signal and out-of-picture samples contribute
nothing to either median; excluded places have no smoothed light or ratio. Empty or zero
surrounds give NaN. The lens measures contrast and knows no anatomical name.
`muscle_grey_bodies` opens the relative-lightness class [1.5, 3) with a native 3×3 square and
labels eight-connected bodies. These constants are explicit first visual/common-sense baseline
readings: the grey sheet is brighter than suppressed fat and below the white vessels, cartilage
and fluid. They were not searched or adjusted to recover a chosen mask, and are not claims of
universal MRI tissue ratios. The native sampling operation is not an anatomical thickness.

The established gracilis cross-section supplies scanner-space points once. Projecting those
points along the middle slice's normal gives a location target, not the gracilis boundary on
that different slice. `sartorius_on_slice` keeps the largest whole grey body whose mean lies
medial and anterior to that target and which reaches within 10 mm of it. This is a broad
locational allowance, not a muscle size or attachment measurement. Exact largest ties and
missing prerequisites have named refusals. The source points, projected target, source-plane
separation, smoothed light, surround, ratio, labelled bodies, sizes, positions, reaches and
statuses are retained beside the independent `a2_sartorius` mask.

The semimembranosus/semitendinosus/gracilis group is resolved once earlier in the same run,
before middle records are saved. Its records and upstream silences are kept, its later duplicate
call is removed, and `name_sartorius` uses the existing middle lens and shared measurements.
The middle save point remains intact. There is no second anatomical compute path and no change
to earlier primary labels.

The real proof entry point identifies 188 pixels on axial slice 16; the source gracilis is
20.12 mm away, and the surround is 41×41 pixels there. These are observations. The corrected
production picture is `data/pictures/definitions-20261016/sartorius-final-close.png`
(ULTRAMARINE sartorius; cyan squares denote only the projected gracilis target). The full gate
passed with 357 tests, including driver ordering/persistence and checks that changing an excluded
stored value cannot alter any contrast reading and that a nonfinite pixel has no light or ratio.
Those last checks caught and corrected the worker's initial median filter, which masked excluded
values only after filtering. The anatomical selector and its constants were unchanged.

This localizes one muscle sheet, not its full course or thickness. A small vessel halo and a
posterior lobe can remain in the body; the source projection alone asserts no intervening tendon
course. The source points, window, separation and body-status readings are retained and listed
as unread by the ledger, rather than represented as downstream consumers. No competition category
names sartorius directly. Sonnet's implementation and usage are retained in
`data/readings/definitions-20261016/sartorius-implementation/`; the lead corrected the measurement
and checked the final result independently. This completes the last part of §6's provisional
hamstrings entry. Full dimensional collapse remains the next phase (§8).

### Final definition-pass verification — 2026-10-16

Implementation `4a126fc` completes the anatomical list at the agreed once-per-object criterion.
The full gate passed with 357 tests; the import contract is kept, type and dependency checks
are clear, and Vulture still reports 12 advisory contract declarations/fields. Labelled and test
records were refreshed. All 351 earlier middle-slice and 48 earlier main-slice records preserve
their previous decisions, silences and saved-array digests with the four additions and optional
borders set aside; the final drawn canonical proof preserves its earlier border readings too.
All proof arrays and decisions match the inspected final alternate run. The new canonical main
record count is 50, including the two biceps records. The measurements and reports are retained
in `data/readings/definitions-20261016/remaining-production/`. These checks establish integration
and preservation, not anatomical validation on every study. Next comes §8's full collapse.

### The back of the knee in the per-study object output; tubes and the bursa — 2026-10-16

Status of one build (uncommitted, with the rest of the dimensional collapse); no definition above
was changed. The posterior family's established rules (both gastrocnemius heads, the artery and vein
lumens, semimembranosus, semitendinosus, gracilis, the sartorius, the bursa) and the three lateral
parts already resolved (iliotibial band, popliteus tendon, biceps femoris tendon) had no rows in
the grouped `objects[study_uid]` output. `index_posterior` in `scripts/run_interiors.py` now says,
from each part's own masks and codes and counting nothing again, by provenance: **native**
(resolved on the slice that named it, with that record's artifact and array), **laid** (from the
twin, where `lay_parts` laid it), **projected** (a location target on every other series' nearest
slice from its largest native section, never a boundary; skipped on the series that hold it laid)
and **unresolved** with the rule's own code (a part the rule refused is not absent; `find_part`'s
silences are said on the series that gave them). Where the support is a boolean mask there is no
label; the heads and semimembranosus are coded in `a1_objects` and carry theirs.

**The one new measurement** is `knee.collapse.posterior.trace_tube`, the cheap continuation of a
tube along the leg. A tendon, vessel lumen or bursa fluid found as a cross-section on an axial slice
is projected onto the nearest slice of each series the leg runs through. From there a ridge (dark
for the tendons and the enclosed-dark lumens; bright for the bursa's fluid, only on a fluid-sensitive
fat-suppressed series) is followed one pixel step at a time in both directions. It is the darkest
(brightest) place within the part's own measured cross width of the previous centre, and holds
only where it is darker (brighter) than an equally wide strip on each side: the iliotibial band's
relation, no signal cutoff, no lens, no extruded footprint. Each end stops by a name
(`clipped_by_the_scan`, `stopped_unseen`, `stopped_not_set_apart_from_the_flanks`,
`stopped_tied_separated_extremes`); an unseen pixel is never read as dark; a start that does not
hold the relation is a reading, not an absence. The result is a native *reading* on that series, with
its places kept (flat packed with offsets) in `a3_posterior_trace_<part>_*` of the record holding
the cross-section, beside the tibia's top and the femur's lowest place (`a3_posterior_context_up_mm`)
so its extent is read against the joint line. It is a pointer, not the part's boundary, full course or
volume, and following a neighbouring structure is not grounds to withdraw the native part. The
heads, sartorius, iliotibial band, popliteus and biceps tendon get no trace: the muscles are
bellies, and the others already are longitudinal on their own slices.

Through the real entry point, drawing off, on the proof and on the bursa study
`…13335129881737731410081002627729200903` (axial slice 14 holds its bursa, 1359 pixels; the proof's
bursa abstains, shown as an unresolved saying): all twelve parts appear in the objects output
where their rule named them or refused. On the proof the artery, semimembranosus, semitendinosus and
gracilis are followed on the sagittal and coronal series (for example gracilis 100 and 65 points on the
two sagittals; semimembranosus 8 to 59 points); the vein's start does not hold the relation
(`at_the_target_stopped_not_set_apart_from_the_flanks`, and a tie between separated extremes) and
says so. On the bursa study the bursa's fluid is followed down the coronal FS slice (164 points) and
along the sagittal FS slice (14 points, weak); on the non-fluid-sensitive series it is refused by
name (`fluid_is_not_bright_in_this_sequence`). No neck, wall or whole course is claimed. Pictures
inspected at the series' own pixels (`data/readings/collapse-20261016/api-build-and-search-priors/
child-posterior-resume/pics/`): semimembranosus on the FS sagittal 5 and T1 coronal 27, gracilis on
the T2 sagittal 3, artery on the T2 sagittal 18, bursa on the coronal FS 27 and sagittal FS 10.
The ridge follows a dark band or a bright pocket in each; whether a dark ridge is the tendon rather
than a neighbouring fascia is not decided here. Not inspected: the vein's and semitendinosus's
traces, and the laid and target rows as pictures.

Work: the ledger counts 16 trace readings on the proof (6 on the bursa study) and no lens or field
read beyond the earlier run's 37 and 30 (27 and 16). The continuation reuses `seen_native`:
the proof adds two distinct slice-light readings and hands fourteen more on from the cache.
The worker's cProfile run records about 0.14 s for the posterior index in a 16 s run. Address
corrections made at the same time: the fibula's native axial readings and the patella's projected
tendon targets no longer carry an integer label against a boolean support (the territory number
stays in `a3_fibula_axial_labels`, and a packed row is addressed by the offsets and shapes beside it);
a twin laid onto from more than one series keeps each source's rows (bones, patella, joint, recess)
under a name made from the source's full series uid, since an abbreviation does not establish
identity (`source_prefix`; before, a later source overwrote an earlier one's arrays and the earlier
rows pointed into the wrong array). The middle slices' own context naming (joint, unsided meniscus,
air, skin, subcutaneous fat, muscle) is also indexed where named, as the middle slice's naming with
no best-slice claim, no projection and no continuation; the unsided meniscus has no pixels on the
proof (the sided menisci replace it), so it says so as unresolved. A check of every observation
against the saved arrays of ten labelled studies and the proof finds no mismatched address. Limits: only the proof, the bursa study, the test split (all abstain: no knee
header) and ten labelled studies were run; the rest is the cohort run; the muscles have no
continuation; the unresolved rows for a series the leg runs through
(`abstain_leg_runs_in_the_plane`) mean the rule was not asked there, not that the part is absent.
