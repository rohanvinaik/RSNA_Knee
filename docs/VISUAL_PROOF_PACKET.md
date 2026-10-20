# Seeing the knee: from measured images to anatomical objects

This is a visual account of the pre-AI pipeline. The question throughout is concrete: **what in these acquired images distinguishes this anatomical object, and what does the pipeline actually extract from it?** The figures come from the operation’s measured arrays. Their captions explain the reasoning connecting the panels.

The argument begins with the leg and its large bones. Their resolved structure supplies information about the smaller objects. It follows the anatomy into its useful slices, through measured lenses and spatial relations, and into one multiview object representation. Every anatomical entry has a place in the visual atlas, including its unresolved views. Later diagnostic and classical-AI interpretation is introduced after the reader has seen the information it will consume.

The governing sources are the author’s [original knee conversation](conversations/2026-10-13-the-thesis.md), [structural-information and HDC conversation](conversations/2026-10-19-structural-information-and-exact-hdc.md), and [*What an <Object> Is*](../../cell_tracking/docs/pipeline_thesis/paper/what_an_object_is.md). The account below uses the knee build’s own images and operations.

## 1. One physical knee, several acquisitions

An MRI study supplies several series: different orientations and different acquisition contrasts. A dark tendon, cortex and meniscus can have similar signal. They remain different objects because they have different shapes, locations, neighbours and attachments. A change of acquisition can make a feature more visible while the physical object stays the same.

Our running example is the proof study ending `...20594649149`. It contains sagittal and coronal series with fluid-sensitive/fat-suppression flags `0/0`, and sagittal, coronal and axial series with flags `1/1`. A second study ending `...27729200903` supplies the bursa example. Full study and series addresses accompany the figures.

The standard first reading is a middle slice of each series. That gives the shared leg/bone context from which the pipeline asks more specific questions. An object’s eventual key slice can differ from this initial view.

![One knee, five acquired views](../data/pictures/visual-proof-20261020/domain/one-knee-five-acquired-views.png)

**Figure 1. What the pipeline is given.** These are the five acquired middle planes, read from the new run's saved arrays. Compare each sagittal and coronal pair: the same bone and soft-tissue arrangement persists while signal changes with acquisition. Axial cuts across the same physical anatomy. `FS` and `Fat` are the recorded fluid-sensitive and fat-suppression flags. Each image has its own display stretch; measured pixel values are unchanged.

![Five acquisitions through the first measured layers](../data/pictures/visual-proof-20261020/current-run/interiors/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/series.png)

**Figure 2. The same knee through five acquisitions and successive measured layers.** Each row is a series’ actual initial slice in the new drawing-enabled production run. Read left to right: acquired signal; measured low signal; distance from surrounding constraints; resulting interior territories; native edges; and sampled dark-band traces. The sagittal/coronal pairs show how contrast changes measurements without changing anatomical arrangement. The axial section cuts across the bones and gives a different partition. Numbers identify measured territories, not tissue classes. Full-resolution stage images: [surrounding field](../data/pictures/visual-proof-20261020/current-run/interiors/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/01-surrounding-field.png), [interiors](../data/pictures/visual-proof-20261020/current-run/interiors/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/02-interiors.png), [native traces](../data/pictures/visual-proof-20261020/current-run/interiors/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/03-native-traces.png).

## 2. The first measurements already expose structure

Low signal marks exterior darkness and dark structures inside the leg. Its scope is precise: it measures low signal under the retained acquisition-specific reading. It assigns no anatomical identity. Distance asks how far an interior place lies from surrounding constraints. Its peaks and territories organize the image into enclosed regions.

Look at Figure 2’s first row. The two large bone interiors evident in the acquired image also form large territories, with deep interior peaks and boundaries following surrounding low signal. On the coronal rows their arrangement differs but remains intelligible. The measured sets supply a visible basis for identifying femur and tibia.

This is the author’s thermometer distinction: a measurement has a quantity and scope; anatomical meaning follows from how several facts stand together. The validity of a measurement is separate from the success of a particular anatomical inference.

The outside of the leg has the same role. A useful exterior/leg prior narrows later work. The skin-contact edge, residual fat and residual muscle fields supply shared context at their actual scope. Computation is directed toward the question that remains.

![Cheap series readings and the saved work scope](../data/pictures/visual-proof-20261020/domain/shared-lens-scope-from-saved-squint.png)

**Figure 3. The cheap reading that scopes a lens request.** Each row shows a native plane, the retained squint's tile maxima and finite-pixel coverage at that slice, and the actual in-scope tile prior. The yellow rectangle is the retained work window. On this sagittal slice the prior falls back to the full frame; on axial the tile mask excludes exterior corners, while its rectangular envelope still spans the frame. Tile counts alone therefore do not establish an equal reduction in expensive pixel work. This is the actual prior, with its useful information and its limits visible.

![Saved exterior and contact-edge assignments](../data/pictures/visual-proof-20261020/domain/outside-air-skin-contact-remaining-assignments.png)

**Figure 4. Exterior and contact-edge descriptions.** Cyan and yellow show the saved air and skin code masks. The coronal and axial rows supply recognizable exterior/contact descriptions. These code masks are empty on the displayed sagittal record, which is shown honestly. Pink is the literal complement of the air code and includes unassigned places. It is not substituted for the distinct computation-scope prior of Figure 3.

### The outside field and skin contact

![The actual exterior and skin operation](../data/pictures/visual-proof-20261020/operations/field/002-read_field-Coronal-1-1-z015.png)

**Figure 4a. Each relation is visible.** The filled territories define this reading's leg prior. Stored zero margin is distinguished from the observed exterior low signal. The exterior component operation retains air fields; the leg-side contact with those fields supplies the skin description. These panels come from the inputs and outputs recorded around the unchanged production `read_field` call. Reconstructing the displayed sets gives exactly its recorded result.

## 3. The bones give the rest of the knee a place

Femur and tibia establish the principal articular relationship. The patella occupies an anterior relation to the femur; the fibula occupies the lateral lower neighbourhood. Those structures supply information about where to read the joint, articular layers, ligament attachments and surrounding tissues.

Searches use that shared context and the cheap squint. A representative plane is selected separately in each orientation. A fine lens runs where its producer points; the map receives the measured candidate plane and criterion. Three available selected planes constrain one object’s physical reference. Partial constraints remain partial.

The following figures trace the actual selected planes. A coarse estimate keeps its coarse scale; a native support keeps its own pixels. A three-plane reference locates and describes the object, rather than reconstructing tissue volume.

### A bone's interior points to the slice; native territories supply its section

The bootstrap asks a geometric question on sagittal and coronal planes: which deep interior territory has another deep territory above or below it along the patient's leg? The superior territory is the femur; the inferior territory is the tibia. The patient's coordinate basis supplies “above,” rather than an assumption about the screen. This is the initial anatomical assignment in `assign_plane`.

Those named places constrain the stack reading. A cheap marrow-body profile measures support through depth. Its supported runs and maxima point to native planes for the detailed lens. The sagittal example below selects z22; the red line lets the reader check that choice against the actual profile.

![Femur: slice profile, native lenses, anatomical context and isolated pixels](../data/pictures/visual-proof-20261020/keyplanes/chains/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/femur/sagittal_z022.png)

**Figure 5. Follow the femur through one complete reading.** At the top, the saved marrow-body profile reaches its greatest displayed support at z22. Below it, the same acquired crop is shown through low signal, distance and interior territories. The lower context panel shows this bone's profile body in cyan, its carried footprint in yellow, and the other bone's section in pink. The naming operation keeps territories supported by this bone's places, removes territories also claimed by the other bone, and checks agreement with the measured marrow body. The last two panels show the resulting 23,742 native pixels as isolated original signal and as an overlay. The profile's 2,724 mm² body measurement and the final territory's pixel count are different quantities. The small attached overreach remains visible.

The rule asks which measured territory belongs to the anatomically located bone, with an independent interior measurement to check the attribution. The [territory naming operation](../src/knee/collapse/bones.py) is consumed by the [production caller](../scripts/run_interiors.py).

![The femur in the selected coronal plane](../data/pictures/visual-proof-20261020/keyplanes/chains/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/femur/coronal_z017.png)

**Figure 6. The same physical bone, a different section.** The coronal profile points to z17. The native lens and carried/profile context resolve a 38,507-pixel section. This is an additional section of the same femur, rather than an unrelated object inferred from its signal alone.

![The femur's axial coarse section estimate](../data/pictures/visual-proof-20261020/keyplanes/chains/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/femur/axial_z021.png)

**Figure 7. A useful coarse reading remains visibly coarse.** The axial selector uses carried location seeds, block medians and depth to obtain a scale-filtered section estimate at z21. The 1,089 selected grid cells supply a useful location and shape. They are expanded to their blocks for display; they are not 1,089 native pixels or a finely measured cortex. Comparing this with Figures 5–6 shows which information each view contributes. The three selected planes constrain one physical reference; they do not fill the intervening tissue or establish its volume.

### The tibia constrains a separate neighbouring bone

![Fibula: actual slice profile and anatomical predicates on sagittal territories](../data/pictures/visual-proof-20261020/operations/bones/fibula-sagittal-z030.png)

![Fibula: the corresponding native coronal operation](../data/pictures/visual-proof-20261020/operations/bones/fibula-coronal-z022.png)

**Figure 7a–b. The same signal becomes specific through a relationship.** The fibula reader starts from the named tibia and its physical top/middle. Its cheap corridor profile points to sagittal z30 and coronal z22. On those native planes, the rule asks for a substantial separate territory, with signal comparable to the tibia, below its top and behind its middle. The qualifying-set panel makes those predicates visible; the last panels keep the largest qualifying territory and expose its original signal. Replaying the unchanged selector with these saved inputs reproduces both saved supports. The pink outline is the tibial reference on that plane. The complete per-territory predicates are retained in the [figure evidence](../data/readings/visual-proof-20261020/fibula-operation-evidence.json).

### Named bone and skin constrain the remaining tissue

![Subcutaneous fat from named structures, signal and skin contact](../data/pictures/visual-proof-20261020/operations/field/006-fat_under_the_skin-Coronal-0-0-z015.png)

**Figure 4b. Brightness has different meanings in different places.** Marrow and subcutaneous fat can both be bright in this acquisition. The femur supplies a measured signal reference. The rule considers the remaining bright components, then keeps those reaching the skin shell. The last panel is the original signal at the resulting 13,126 pixels. The bone's bright interior is excluded through its already resolved identity. No tissue name is being read from brightness alone.

![The broad muscle field from remaining substantial bodies and fluid exclusion](../data/pictures/visual-proof-20261020/operations/field/007-muscle_bodies-Coronal-0-0-z015.png)

**Figure 4c. The remainder is structured too.** The muscle operation reads the unnamed darker-than-fat places inside the observed leg, retains substantial bodies at the declared physical scale, and subtracts the paired fluid-sensitive white field. The last two panels show the result over the acquired image and as isolated original pixels. This is the broad residual muscle field; the separate named heads and tendons add their own relations later.

## 4. Between the bones: joints, wedges and surface layers

With the articular neighbours in hand, a dark wedge in their intervening compartment has a different interpretation from darkness elsewhere. The two menisci are distinguished by compartment and shape. Cartilage is read as a layer belonging to a particular articular surface. Joint space, fluid, cavity-facing lining and outer capsule are separate descriptions of related places.

A lens need not isolate the whole object by itself. Low signal supplies one set; the joint or attachment neighbourhood supplies another; contact, enclosure and geometry supply further distinctions. Intermediate panels make those sets visible so the reader can follow the identity assignment.

### A small coronal wedge locates the meniscus in another view

![Medial meniscus from source wedge through the sagittal reading](../data/pictures/visual-proof-20261020/operations/joint/medial-meniscus-sagittal-z005.png)

**Figure 8. The source narrows the question; the target image supplies the section.** The coronal source is a 67-pixel medial wedge at the joint. Its physical samples produce the sagittal depth profile at upper left, pointing to z5. The source locations are yellow in the available target crop. Enclosed-darkness depth supplies positive interior support; the existing 2 mm thickness operation separates components. Contact with the source neighbourhood selects the 588-pixel component. Its isolated original signal visibly follows the dark meniscal body between the opposing surfaces. The transferred source is a location constraint, rather than an outline copied into the target.

The initial coronal name comes from thick low signal contacting the joint, at its medial end under the patient's physical side. The cross-view reader then asks which native component occupies that location. These are two linked anatomical questions, each with its own actual measurement. The [medial and lateral atlas entries](VISUAL_PROOF_ATLAS.md#the-joint-and-articular-surfaces) show their other views and retained candidates.

### A surface layer belongs to a particular bone

![Femoral cartilage: sources, bone context and measured candidate sets](../data/pictures/visual-proof-20261020/operations/joint/femoral-cartilage-axial-z014.png)

**Figure 9. Resolve a layer through its object and its contacts.** The saved sagittal/coronal source profiles point to axial z14. The coarse bone reading supplies interior context, while the two native sources supply separate target locations. The lower panels show the consumed enclosed-depth field, the measured brightness candidate and component/contact selection. The resulting 996-pixel candidate follows a surface-associated arc. Its visible breadth and overreach remain available for later refinement. The coarse interior is a context measurement, not a newly asserted exact marrow boundary.

![Tibial cartilage: its own source, native crop and selected pixels](../data/pictures/visual-proof-20261020/operations/joint/tibial-cartilage-axial-z011.png)

**Figure 10. Association distinguishes opposing layers.** The tibial source supplies a different target and native crop. The panels show its actual signal and source-distance measurements, contacted candidates and isolated selected pixels. The object's association with the tibia distinguishes this reading from the femoral layer. The crop's exterior remains unread; no complete surface outside it is asserted.

![Patellar and opposing trochlear surface candidates](../data/pictures/visual-proof-20261020/operations/joint/patellofemoral-sagittal-z021.png)

**Figure 11. The opposing-bone relation creates two separate questions.** The selected patellar plane supplies actual patella/femur inputs, availability, bridge/hull, signal band and surface reach. The final rows keep patellar-side and trochlear-side sets separate and expose their original pixels. These are candidate readings, with discontinuities and off-surface overreach plainly visible. They demonstrate the operation and its present residual; they do not establish a complete correct segmentation of both cartilage sheets.

### Fluid, lining and wall are related descriptions of the same cavity

![Joint fluid from actual recess measurements](../data/pictures/visual-proof-20261020/operations/joint/axial-joint-fluid-z021.png)

**Figure 12. The cavity relation restricts the bright field.** The saved recess profile points to the measured axial plane. Availability, the fluid-sensitive white field, wall and lining context are shown separately. The medial and lateral selected recess masks contain 1,213 and 667 pixels with no overlap; their exact union supplies the 1,880-pixel fluid reading shown as original pixels. The neighbouring lining and outer wall are retained as different observations, even where their places touch or overlap this cavity description.

## 5. Attachments distinguish structures with similar signal

ACL, PCL, collateral ligaments and tendons all contribute dark structures. Their courses and endpoints distinguish them. Around the patella, the extensor mechanism, retinacula, fat pads and cavity constrain one another. Posteriorly, muscle heads, tendons, vessel lumens and bursa occupy related but distinct places.

The object atlas follows these families through actual selected or inspected native planes, consumed measurements, structural context and resulting support. A local marker, sampled surface, physical trace and whole-region candidate are drawn at their actual scope. This exposes demonstrated competence and the useful residual for later refinement.

### The patella divides one extensor arrangement into two tendons

![Patellar tendon: sagittal attachment context, axial slice selection and actual native section](../data/pictures/visual-proof-20261020/operations/anterior/extensor/patellar_tendon_axial_operation.png)

![Quadriceps tendon: its superior sagittal source and native axial section](../data/pictures/visual-proof-20261020/operations/anterior/extensor/quadriceps_tendon_axial_operation.png)

**Figure 12a–b. Similar dark material, different connections.** The sagittal arrangement identifies the band below the patella as the patellar tendon and the band above it as the quadriceps tendon. These are separate source objects. Their physical source profiles point to different axial planes: z13 and z30. On each plane, the actual lens/context and source contact select a native component: 587 and 1,786 pixels respectively. The projected source constrains the local question; the target image supplies the component. The coronal operations, including measured refusals when both sources cannot contact one body, remain linked in each atlas entry.

### Fat pads are distinguished by the cavity and attachments around them

![Hoffa's fat pad: source, profile, native holder and compatible retained support](../data/pictures/visual-proof-20261020/operations/anterior/fatpads/hoffa_fat_pad_coronal_operation.png)

**Figure 12c. Combine the useful sets instead of demanding one perfect lens.** Hoffa's source occupies the anterior interval behind the patellar tendon. Its coronal source profile supplies z8 and z22. The green native holder is visibly broader than the object. The final row shows the opposed-acquisition readings and the consumed same-series white-fluid and coarse-core exclusions, followed by the compatible retained support. The final 7,735/1,336-pixel sets remain local candidates with visible overreach. No premise requires the green holder alone to identify Hoffa's pad.

![Quadriceps fat pad on its native coronal plane](../data/pictures/visual-proof-20261020/operations/anterior/fatpads/quadriceps_fat_pad_coronal_operation_z06.png)

![Prefemoral fat pad on its native coronal plane](../data/pictures/visual-proof-20261020/operations/anterior/fatpads/prefemoral_fat_pad_coronal_operation_z08.png)

**Figure 12d–e. The recess supplies a meaningful partition.** The quadriceps and prefemoral pads belong to opposite sides of the suprapatellar cavity: tendon-side and femur-side. The source, profile, native holder and actual compatible set are shown for each, preserving their separate anatomical identities. The suprapatellar grouping is retained as related information; it does not become an extra independent pad.

### A bright cavity helps expose its darker outer wall

![Medial retinaculum: axial source, coronal profile, fluid body, outboard strip and wall](../data/pictures/visual-proof-20261020/operations/anterior/retinacula/medial_patellar_retinaculum_coronal_z05_operation.png)

**Figure 12f. A relation can be more informative than absolute signal.** The axial medial-side source points to a coronal question at z5. The same-series bright fluid body supplies the inside reference; its outboard strip supplies the place to read a darker minimum band. The final 58-pixel wall support is a local retinacular reading. Side, cavity and adjacency distinguish this band from unrelated dark structures. The lateral counterpart uses the corresponding lateral relation and is shown separately in the atlas.

### Ligament sections retain their anatomical sources

![PCL source, sagittal sections, profiles and native axial/coronal readings](../data/pictures/visual-proof-20261020/operations/ligaments/final/pcl-ligament-chain.png)

![MCL coronal source, scoped sagittal reading and native axial candidates](../data/pictures/visual-proof-20261020/operations/ligaments/final/mcl-ligament-chain.png)

**Figure 12g–h. Follow the course and attachments into the other planes.** The PCL's sagittal band supplies native locations for axial and coronal section questions. The coronal reading uses both sagittal and axial source contact. The MCL starts from the medial coronal band and supplies a distinct axial profile and local candidates. These sheets expose the actual crops, measurements and isolated original pixels. The MCL's bone context is recorded as unavailable here, so it remains neutral; the code does not turn that into a measured bone conflict. The [ACL](../data/pictures/visual-proof-20261020/operations/ligaments/final/acl-ligament-chain.png) and [LCL](../data/pictures/visual-proof-20261020/operations/ligaments/final/lcl-ligament-chain.png) sheets keep their source relations and scoped readings separate, including the ACL's named abstentions.

### A muscle source locates a native question in another orientation

![Gastrocnemius: axial identity, sagittal profile and consumed native measurements](../data/pictures/visual-proof-20261020/operations/posterior/first-example/lateral_gastrocnemius-proof-sagittal-z23.png)

**Figure 13. Transfer the location, then read the target.** The axial source supplies a lateral-head section and its interior peak. The saved sagittal source profile selects z23. In the retained source-derived window, the native low-signal lens, domain and gradient territories are measured. The local result is the basin carrying that location marker. This establishes a scoped muscle reading around an anatomical source, not the muscle's complete anatomical boundary. The marker's recorded distance from the target slab is 1.78 mm, retained alongside the reading.

![Lateral gastrocnemius: the actual retained target pixels](../data/pictures/visual-proof-20261020/operations/posterior/lateral-example/proof-study/lateral_gastrocnemius-native-pixels-sagittal-z23.png)

The [medial-head counterpart](../data/pictures/visual-proof-20261020/operations/posterior/medial-example/proof-study/medial_gastrocnemius-proof-sagittal-z14.png) is an instructive limit: its native axial section is substantial, but the transferred sagittal marker reading retains only one acquired pixel. Its [isolated-pixel companion](../data/pictures/visual-proof-20261020/operations/posterior/medial-example/proof-study/medial_gastrocnemius-native-pixels-sagittal-z14.png) makes that scope unmissable. It is a local observation associated with the head, not successful extraction of its whole sagittal belly.

![Bursa: anatomical interval, source profile and native target reading](../data/pictures/visual-proof-20261020/operations/posterior/bursa-example/bursa-proof-sagittal-z10.png)

![Bursa: original target pixels retained by the reading](../data/pictures/visual-proof-20261020/operations/posterior/bursa-example/bursa-proof-sagittal-z10-support.png)

**Figure 14. The interval between named neighbours makes a small cavity findable.** The second study supplies the bursa example. Its axial source at z14 contains 1,359 pixels. The source profile points to sagittal z10 with 548 projected samples; the bounded native reading retains 319 target pixels. Those are shown as original acquired signal. The result is explicitly a scoped reading, with `full_boundary_asserted=false`. Its warrant is the gastrocnemius–semimembranosus interval and the target measurements, rather than a generic fluid blob anywhere in the leg.

Every named object's sagittal, coronal and axial pictures are in the [object atlas](VISUAL_PROOF_ATLAS.md). The posterior sheets additionally expose the shared source/profile/context operation across the named tendons, muscles and vessel readings. A source marker, a sampled course and a resolved section retain their actual different meanings.

## 6. One object across views, then one exact profile

Sagittal, coronal and axial observations belong to one anatomical identity. Acquisition, lens, direction and measurement scale remain named facets. Native readings, identity laid from a paired acquisition and projected search targets keep their different provenance.

Each measured place retains its original value and address. A declared numeric reference writes below/at/above as three distinct rows; a categorical measurement writes its declared word row. Unread measurements leave their banks silent and retain a reason. A missing healthy numeric reference remains `missing_reference`.

![The same patellar tendon across views and its measured directional word banks](../data/pictures/visual-proof-20261020/encoding/patellar_tendon_hdc.png)

**Figure 15. Keep identity together while retaining the facets.** The sagittal acquired image and low-signal lens refer to the same tendon places. The bars show actual word counts in the overview and direction-conditioned banks. The lower masks are retained coronal and axial sections of that same object; their acquired images are in its atlas entry and operation figures. The anatomical MPS direction triples are stored facet coordinates. `False` and `True` here are the low-signal lens's categorical words, not healthy/unhealthy diagnoses.

![Actual tendon pixels, exact row writings, bundled vector and decoded evidence](../data/pictures/visual-proof-20261020/encoding/exact-pixel-to-bundle.png)

**Figure 16. Follow the original pixels into the algebra.** The table gives actual native addresses and retained word rows. In this sagittal bank, 1,070 places write `False` and 394 write `True`. The displayed carrier coordinates are the first 64 of the actual 512: the bundle is their integer weighted sum, and exact decoding recovers both counts. Carrier coordinate signs are algebraic values, distinct from signed clinical departure. Repeated source/place/facet/metric evidence is linked without counting it twice. Missing healthy references do not become middle readings.

An object’s profile sums those row writings over its places. The composition keeps an ordered matrix of named banks; each bank uses 512-wide orthogonal Hadamard rows. Within one bank:

- `v = sum(c_i * h_i)`
- `h_i · h_j = 512` when `i == j`, and `0` otherwise.
- `c_i = (v · h_i) / 512`.

The exact count table and carrier vector describe the same bundle. Distinct below/middle/above rows preserve opposed deviations rather than cancelling them into a middle reading. Exact source/place/facet/metric repetitions count once and retain their links; conflicting codes remain named conflicts. The representation example uses an actual object from this same run, tying its counts to the anatomical pictures.

The [full-carrier check](../data/readings/visual-proof-20261020/full-object-carrier-check.json) reconstructs the declared full layout for every retained object in both studies: all 88 count tables round-trip exactly. This checks the representation algebra. The anatomical figures establish what the corresponding measurements and candidate places mean.

## 7. From an identified object to a question about its state

The author defines the diagnostic bridge through an object’s normal anatomical state and signed departures. Once its places are available, a later question can ask about continuity, extent, signal or relations in the same representation. A healthy reference and a diagnostic interpretation require their own declared meanings.

The paper’s K-line design begins with this object-bundle substrate. A confirmed case additionally retains its call, expected outcome or departure, and independent source. The knee-specific AI, diagnosis and teaching mechanisms remain the author’s next design discussion. This packet establishes what they can inspect and consume.

## 8. Structure directs computation in these actual readings

The meniscus source does two useful things at once: it distinguishes the intended anatomical body from other dark structures, and it limits the target measurement to the relevant slice and neighbourhood. The same source information serves recognition and compute placement. The lens itself still measures its declared quantity.

| Actual reading | Full acquired plane | Array supplied to this local measurement | Local pixels / full-plane pixels |
|---|---:|---:|---:|
| Sagittal femur, z22 | 400 × 400 | 400 × 300 | 120,000 / 160,000 |
| Sagittal medial meniscus, z5 | 320 × 320 | 97 × 222 | 21,534 / 102,400 |
| Sagittal lateral gastrocnemius, z23 | 400 × 400 | 240 × 254 | 60,960 / 160,000 |

These are measured input sizes for these particular calls, not whole-pipeline speed ratios. The full-frame fallbacks in Figure 3 remain visible. Shared lenses, profiles and anatomical sources are retained for their consumers; the detailed native operation is asked at the pointed planes. Production drawing stays off. These are concrete instances of the thesis's link between resolving the domain's structure and avoiding unnecessary work.

## 9. Reproducing the pictures

The new figures use [current-draw-run](../data/readings/visual-proof-20261020/current-draw-run/). Its [launch record](../data/readings/visual-proof-20261020/current-draw-run/launch.json) contains the exact production command. Both studies completed successfully in 215.612 seconds, with all 101 pinned source files unchanged between [before](../data/readings/visual-proof-20261020/current-draw-run/source-pins-before.json) and [after](../data/readings/visual-proof-20261020/current-draw-run/source-pins-after.json); [run result](../data/readings/visual-proof-20261020/current-draw-run/run-result.json). That elapsed time includes development drawing and encoding and is not competition-mode timing.

The run retains recognition receipts, measured arrays, study maps and encoding products. Figure generators read saved results and addressed acquired frames; they choose no new anatomical supports. Drawing remains optional development work, off in competition mode.

The [object atlas](VISUAL_PROOF_ATLAS.md) has 45 source entries with sagittal, coronal and axial image sections, plus the bone-associated marrow field. Of the 45 source entries, the unsided legacy meniscus and uncoded recess grouping are not extra independent anatomical objects. The [operation index](../data/readings/visual-proof-20261020/operation-figure-index.json) links the actual measured operation figures for the remaining 43 entries. The acquired-frame atlas has 261 pages; all 200 verified native masks are paired with isolated original acquired pixels. Coarse grids and non-pixel readings keep their own representation. A page showing an unresolved reading or acquired context is not a claim of successful resolution in that view.

The [extraction manifest](../data/readings/visual-proof-20261020/figure-generators/extraction-atlas-manifest.json), per-family [operation evidence](../data/readings/visual-proof-20261020/operations/), and [generators](../data/readings/visual-proof-20261020/figure-generators/) retain addresses and hashes. Generic-field intermediate figures use an additional [recorded production invocation](../data/readings/visual-proof-20261020/field-call-capture/launch.json): wrappers saved exact function arguments/results while leaving the anatomical functions unchanged. Fibula figures replay the unchanged selector on its saved arguments and check equality with the saved result. Figure annotations do not adjust a selector or its constants.

From the project directory, the retained algebra and document can be regenerated with:

```sh
.venv/bin/python data/readings/visual-proof-20261020/figure-generators/check_full_object_carriers.py
.venv/bin/python data/readings/visual-proof-20261020/figure-generators/render_exact_bundle.py
.venv/bin/python data/readings/visual-proof-20261020/figure-generators/render_fibula_operation.py
.venv/bin/python data/readings/visual-proof-20261020/figure-generators/build_visual_atlas.py
.venv/bin/python data/readings/visual-proof-20261020/figure-generators/validate_publication.py
```

These commands consume the retained local evidence. The original production command is preserved in the launch record; an independent recognition rerun should use fresh output directories so this evidence remains intact. The per-family generator records explain their image reconstruction and exact inputs.

Competition-derived figures and evidence live in the local, git-ignored `data/` tree. A checkout without that evidence cannot display them until it is generated or supplied. Figure evidence records name study, acquisition, slice, arrays and digests. The atlas exposes actual coverage; missing views stay explicit and do not become absence findings.
