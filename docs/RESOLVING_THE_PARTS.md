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
