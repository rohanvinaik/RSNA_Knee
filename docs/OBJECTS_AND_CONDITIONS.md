# The objects and the twelve conditions — draft

**Status:** draft for Rohan's correction, 2026-10-14. Domain knowledge only.

His ask: «I want you to draft a simple explanation for what each of the 12 conditions are, and the anatomical objects
they involve are, and what discriminates each of those objects from each other and the rest of the visual field.»
His limits on it: «Basic domain knowledge about the condition. How a computer vision pipeline resolves this, I will
tell you later» · «First objects, injury diagnosis later» · «Just what's correct and knowable. Inference for later.»

So each condition gets only what it is and the objects it involves; how medicine detects the damage is left out. Each
object gets what and where it is, how it shows on each kind of sequence, and what tells it apart from its neighbours
and the rest of the field. Every statement ends with its source key (list at the end). A "told apart by" line puts
sourced facts side by side: the facts are the sources', the pairing is mine. Any other line of mine is marked
*(Claude)*. Nothing here says how the pipeline resolves anything.

**Medicine's method.** Rohan: «"define rules to discriminate between objects in a field" is LITERALLY how medicine
itself does it. What else do you think is the definition of "interstitial" fluid??» Medicine's definition:
«Interstitial fluid is the body fluid between blood vessels and cells» [W-ECF]. The same word reaches the knee:
Wilson et al. (1988), who first described bone marrow edema on MRI, read the signal as «an increase in free water
content in the bone marrow "interstitium"» [R-BME].

## 1. What the competition gives

- Each study is several MRI series from one scanning session; each series is one acquisition. The twelve labels
  (0/1) attach to the **study**; the task is a per-study probability for each [K].
- Each series has three tags: `Anatomical_Plane` (sagittal, coronal or axial); `Fluid_Sensitive`, 1 if the sequence
  emphasizes fluid signal («T2, PD, STIR, and similar»); `Fat_Suppression`, 1 if the sequence applies fat suppression.
  The two flags are often correlated but not equivalent [K].
- Series typically hold 20–45 slices (median 30); intensities, orientations and resolutions vary across series and
  studies [K]. Only a small subset of training studies carry labels; the radiology report is given for training
  studies only [K].
- The proof study (`…10095687…`) has five series: sagittal and coronal with both flags 0; coronal, sagittal and axial
  with both flags 1 (titles of `data/pictures/interiors/<uid>/series.png`).

## 2. How medicine reads a knee MRI

- **The acquisition.** Three orthogonal planes, with fluid-sensitive fat-saturated sequences (T2W FS or PDW FS) and
  T1W without fat saturation [C]. T1W without fat saturation shows the bone-marrow fat; PDW is more sensitive than T2W
  for meniscal pathology [C]. Intravenous contrast is not indicated for internal derangement but is useful for
  synovitis [C]; no tag marks it [K].
- **The first steps.** Determine the pulse sequence; find the normal anatomy on T1W, proton-density and gradient-echo
  images; confirm the tissues are homogeneous on T1W, and check T2W where they are not [Kh].
- **The reading order** of a radiology teaching guide [AUR]:
  1. fluid (joint effusion, Baker's cyst) on axial T2 FS;
  2. bone contusions and fractures on T2 FS, with fractures confirmed on coronal T1 without fat saturation;
  3. and 4. the medial, then the lateral compartment: the meniscus on sagittal PD, its body on coronal T2 FS, the
     hyaline cartilage on coronal and sagittal T2 FS;
  5. the ACL and PCL on axial and coronal T2 FS;
  6. the MCL, and the lateral complex (iliotibial band, fibular collateral ligament, popliteus tendon, biceps femoris
     tendon), on coronal and axial T2 FS;
  7. the extensor mechanism on sagittal T2 FS;
  8. the patellofemoral cartilage on axial and sagittal T2 FS;
  9. vessels, nerves and the surrounding soft tissue on axial T2 FS.
- **In the tags' terms** *(Claude)*: T1W without fat suppression is `Fluid_Sensitive=0, Fat_Suppression=0`; T2W or
  PD without it is `1, 0`; T2W FS or PD FS is `1, 1`. PD and T2 cannot be told apart from the tags [K].

## 3. The field: how each tissue shows

Signal by sequence, as one source tabulates it [Kh]:

| tissue | T1W | T2W | fat-suppressed T2W | proton density |
|---|---|---|---|---|
| cortical bone | very low | very low | very low | very low |
| yellow marrow | high | intermediate | very low | intermediate |
| red marrow | low/intermediate | intermediate | low/intermediate | intermediate/high |
| fat | high | intermediate | low/intermediate | intermediate/high |
| fluid | low | high | very high | low (its Table I: intermediate) |
| muscle | intermediate | intermediate | low/intermediate | low |
| ligaments and tendons | low | low | very low | very low |
| hyaline cartilage | intermediate | intermediate | intermediate | intermediate |
| meniscus | low | low | low | low |

- Normal marrow is brighter than the adjacent muscle on T1W [C]; red marrow holds about 40% fat, yellow about 80% [C].
- Hoffa's infrapatellar fat pad «follows the signal of subcutaneous fat on all pulse sequences» [Kh].
- Two dark structures are normally not uniform: the ACL is less well defined than the PCL, with brighter fibres
  [Kh], its bundles outlined by surrounding high-intensity structures [R-ACL]; the quadriceps tendon is laminated,
  its layers separated by fat [C].
- Three rows are dark on every sequence: cortical bone, ligaments and tendons, and the menisci [Kh]. Between them,
  medicine tells by place and shape, not by signal (see §4) *(Claude)*.

## 4. The objects

### Bones: femur, tibia, patella, fibula

- **What and where.** The femur's two condyles meet the tibial plateau: the medial condyle narrow and curved on an
  oval facet with a long front-to-back length, the lateral condyle wide and flat on a circular facet that overhangs
  the shaft posterolaterally [R-KNEE]. The patella's posterior facets (medial, lateral, odd) meet the femoral condyles
  in a saddle joint; the patellar ligament runs from its apex to the tibial tuberosity [R-KNEE]. The fibular head
  takes the fibular collateral ligament [R-KNEE].
- **How bone shows.** Cortex very low on every sequence; yellow marrow high on T1W and very low on fat-suppressed T2W
  [Kh].
- **Told apart by.** From the soft tissue around it, by the very-low cortex and the marrow's fat signal [Kh]. From
  each other, by which joint surface they form [R-KNEE]. Medial from lateral, on sagittal images: the lateral
  compartment has the fibular head and a convex tibial plateau contour; the medial has a concave one [Kh].
- **Where medicine looks.** Coronal images show the femoral condyles [Kh]; the axial plane shows the patella's
  relation to the trochlea [Kh].
- **Involved in:** Medial, Lateral and PF OA; Contusion; Fracture; ACL and MCL (attachments).

### Bone marrow

- **What and where.** Red and yellow marrow [C].
- **How it shows.** As in §3 [Kh].
- **Told apart by.** Subcutaneous fat shows the same fat signal [Kh], so marrow is told by place: inside the bone, within
  the cortex *(Claude)*.
- **Involved in:** Contusion; Fracture; OA (subchondral changes) [R-OA].

### Articular cartilage

- **What and where.** The layer over the articular surfaces, on the subarticular bone plate [C]; thickest at the
  patella [C].
- **How it shows.** Intermediate on T1W, T2W, fat-suppressed T2W and PD [Kh].
- **Told apart by.** It is intermediate between the very-low cortex beneath it and joint fluid: low on T1W, very high
  on fat-suppressed T2W [Kh], [C].
- **Where medicine looks.** The patellar facets and the trochlear groove on axial images [Kh]; the tibiofemoral
  cartilage on coronal and sagittal T2 FS [AUR].
- **Involved in:** Medial, Lateral and PF OA [R-OA].

### Menisci

- **What and where.** Two fibrocartilage wedges, one in each tibiofemoral compartment, between condyle and plateau
  [R-MEN], [C]. Each is C-shaped in the transverse plane (anterior root, anterior horn, body, posterior horn, posterior
  root) and triangular in cross-section, thick at the periphery and thinning to a free edge [R-MEN].
  - Medial: an open, wide, almost semicircular C; the larger; posterior horn much larger than anterior; attached to
    the deep MCL; covers about 60% of the medial plateau [R-MEN], [C].
  - Lateral: tight, nearly a closed circle; smaller; horns the same size; not attached to the LCL; the popliteus
    tendon passes its posterior periphery; covers about 80% of the lateral plateau [R-MEN], [C].
- **How it shows.** Low on all pulse sequences [Kh]; «black or charcoal grey» [C].
- **Told apart by.** Cortex, ligaments and tendons are also dark [Kh], so the meniscus is told by place and shape: at
  the joint, between condyle and plateau; an isosceles triangle on coronal images [C]; on sagittal images a bow tie
  at the periphery, then two opposing triangles, the horns, towards the intercondylar notch [Kh], [C]. Medial from
  lateral: by compartment (above), and by shape, an open C against a near-circle [Kh], [R-MEN].
- **Where medicine looks.** Sagittal PD; the body on coronal T2 FS [AUR]; PD is the sequence of choice [Kh].
- **Involved in:** Medial Meniscus; Lateral Meniscus; OA (meniscal degeneration) [R-OA].

### Ligaments

- **ACL.** From the anteromedial intercondylar area of the tibial plateau, upward and backward, to the posteromedial
  aspect of the lateral femoral condyle, inside the intercondylar notch; 31–38 mm long, 10–12 mm wide; two bundles;
  inside the capsule but outside the synovium [R-ACL].
  *Shows:* low-signal bands, taut on sagittal images and parallel to the roof of the notch [C]; normally less well
  defined than the PCL [Kh] and heterogeneous [R-ACL].
  *Told apart by:* course. On sagittal images, going lateral to medial, the ACL comes before the PCL [Kh]; on coronal
  images it is more vertical than the PCL [Kh]; on axial images it runs 15–20° anteromedially through the notch from
  the lateral condyle to the front of the tibia [Kh].
  *Where medicine looks:* sagittal images first [Kh]; axial and coronal T2 FS [AUR].
  *Involved in:* ACL.
- **PCL** (a neighbour). From the medial femoral condyle in the notch to the back of the tibia; thick, uniformly
  low-signal and curvilinear [Kh], [C]; front-to-back thickness ≤6 mm [C]; triangular on posterior coronal images,
  circular on anterior ones [Kh]. *Involved in:* no label directly; it is the ACL's neighbour in the notch.
- **MCL.** Superficial and deep layers [C]. The superficial band runs from the medial femoral epicondyle to the medial
  proximal tibia, 5–7 cm below the plateau, deep to the pes anserinus; 8–10 cm long [Kh] (about 12 cm in [R-KNEE]).
  The deep layer is a thickening of the medial capsule whose meniscofemoral and meniscotibial parts attach the
  periphery of the medial meniscus [C].
  *Shows:* a uniformly low-signal line [Kh], with no surrounding oedema or internal signal [C]; the deep parts are
  thin and hard to see unless injured [C].
  *Told apart by:* place. It is the low-signal band on the medial side of the joint, from epicondyle to tibia
  [Kh], [C], joined to the medial meniscus [R-KNEE], [C].
  *Where medicine looks:* coronal images first [Kh]; coronal and axial T2 FS [AUR], [C].
  *Involved in:* MCL.
- **LCL, the fibular collateral ligament** (a neighbour). From the lateral femoral condyle to the fibular head [Kh];
  a thin cord about 5 cm long, not attached to the lateral meniscus [R-KNEE]; with the iliotibial band and biceps
  femoris tendon it makes the lateral complex [Kh]. Its attachments: on the femur slightly proximal (1.4 mm) and
  posterior (3.1 mm) to the lateral epicondyle; on the lateral aspect of the fibular head, 8.2 mm (range 6.8–9.7)
  posterior to the head's anterior margin, on average 38% of the head's anterior-to-posterior width from its
  anterior edge; 69.6 mm long between them; the popliteus tendon runs medial to it [LP-PLC].
  *Involved in:* no label directly; it is the MCL's counterpart on the lateral side.

### Joint space, lining and fluid

- **Joint cavity and recesses.** The capsule is lined by synovial membrane; the cruciates and the popliteus tendon
  are inside the capsule but outside the synovium [R-KNEE]. The recesses are suprapatellar, infrapatellar, medial,
  lateral and intercondylar [C]. The suprapatellar bursa, the superior extension of the joint cavity [R-KNEE], lies
  between the rectus femoris (quadriceps) tendon and the femur and usually communicates with the joint [C], between
  the suprapatellar and prefemoral fat pads [R-EFF]. Normally it holds only a small amount of fluid [R-EFF].
  *Shows:* fluid is low on T1W, high on T2W, very high on fat-suppressed T2W [Kh].
  *Told apart by:* fluid signal in the joint's own recesses [C], [Kh]. Fluid outside the joint at the back, between
  the medial gastrocnemius head and the semimembranosus tendon and joined to the joint by a neck, is a Baker's cyst
  instead [R-BAKER], [AUR].
  *Where medicine looks:* axial T2 FS [AUR].
  *Involved in:* Effusion; Synovitis.
- **Synovial membrane (synovium).** A thin, highly vascularised membrane lining synovial joints, some bursae and
  tendon sheaths [C]; in the knee it lines the capsule and communicates with the suprapatellar bursa [R-KNEE]. Its
  normal look is not stated by the sources read; disease shows as thickened synovium [C].
  *Involved in:* Synovitis; Baker's (the cyst is synovial-lined) [R-BAKER].
- **Fat pads.** Three in front: infrapatellar (Hoffa), posterior suprapatellar (prefemoral), anterior suprapatellar
  (quadriceps) [R-KNEE]. Hoffa's lies just behind the patellar tendon and follows subcutaneous fat on all sequences
  [Kh].
  *Told apart by:* fat signal (high on T1W, low to intermediate on fat-suppressed T2W) [Kh], in their places:
  Hoffa's just behind the patellar tendon [Kh], the other two on either side of the suprapatellar recess [R-EFF].
  *Involved in:* no label directly; they border the suprapatellar recess (Effusion) [R-EFF].

### Back of the knee

- **The popliteal fossa: medial gastrocnemius head, semimembranosus tendon, and the bursa between them.** A bursa
  beneath the medial gastrocnemius head communicates with the joint; the semimembranosus bursa may communicate with
  it [R-KNEE]. The semimembranosus tendon is easily seen on MRI [C]. Its direct arm «attached to the proximal aspect
  of the posteromedial part of the tibia in a small groove just proximal to the tuberculum tendinis prominence. The
  attachment was posterior to the medial tibial crest and distal to the posteromedial aspect of the joint line»; its
  anterior arm attaches deep to the superficial MCL's proximal tibial attachment, distal to the tibial joint line;
  the medial gastrocnemius tendon attaches on the femur 2.6 mm proximal and 3.1 mm posterior to the gastrocnemius
  tubercle; the sartorius, gracilis and semitendinosus tendons attach on the anteromedial tibia [LP-MED].
  *Shows:* muscle intermediate, tendon low [Kh].
  *Involved in:* Baker's.

### Landmarks and the rest of the field

- **Extensor mechanism.** The quadriceps tendon, patella and patellar tendon; both tendons uniformly low and best seen
  on midsagittal images [Kh]; the quadriceps tendon laminated [C]; the patellar retinacula, low-signal bands from
  patella to femoral condyles, best seen on axial images [C], [Kh]. No label names it; the suprapatellar bursa lies
  behind the quadriceps tendon and Hoffa's fat pad behind the patellar tendon [C], [Kh].
- **The rest:** subcutaneous fat and muscle as in §3 [Kh]; the popliteal artery lies in front of the popliteal vein
  [Kh].

## 5. The twelve conditions

| label (competition's words) [K] | what it is | objects |
|---|---|---|
| **ACL**: «anterior cruciate ligament injury» | injury of the ACL; its tears are the most common knee ligament injury [R-ACLT] | ACL; its attachments on the lateral femoral condyle and the tibial intercondylar area [R-ACL] |
| **MCL**: «medial collateral ligament injury» | sprains, partial and complete tears of the superficial and/or deep MCL [R-MCLI] | MCL; medial meniscus (attached); medial femoral epicondyle; medial tibia [R-KNEE], [C] |
| **Medial Meniscus**: «medial meniscus tear» | failure of the fibrocartilaginous meniscus [R-MT] | medial meniscus; the condyle and plateau it sits between [R-MEN] |
| **Lateral Meniscus**: «lateral meniscus tear» | as above [R-MT] | lateral meniscus; the condyle and plateau it sits between [R-MEN] |
| **Medial OA**: «osteoarthritis of the medial tibiofemoral compartment» | knee osteoarthritis: joint-space narrowing, subchondral sclerosis, marginal osteophytes, subchondral cysts, altered shape of the condyles and plateau; the medial compartment is affected more often and more severely than the lateral [R-OA] | medial femoral condyle, medial tibial facet, their cartilage, medial meniscus [R-KNEE], [R-MEN] *(grouping: Claude)* |
| **Lateral OA**: «osteoarthritis of the lateral tibiofemoral compartment» | as above [R-OA] | the same on the lateral side *(Claude)* |
| **PF OA**: «patellofemoral osteoarthritis» | as above, in the patellofemoral joint [R-OA] | the patella's posterior facets, the femoral condyles they meet, their cartilage [R-KNEE] *(grouping: Claude)* |
| **Effusion**: «joint effusion / excess fluid» | an increased amount of fluid within the synovial compartment, where normally there is only a little [R-EFF] | joint cavity and its recesses; suprapatellar bursa [C], [R-KNEE] |
| **Synovitis**: «inflammation of the joint lining» | any inflammatory process of the synovium [R-SYN] | synovium; the joint fluid beside it |
| **Baker's**: «Baker's cyst» | a fluid-filled, distended, synovial-lined lesion in the popliteal fossa between the medial gastrocnemius head and the semimembranosus tendon, communicating with the knee joint [R-BAKER] | medial gastrocnemius head; semimembranosus tendon; posterior capsule; gastrocnemius–semimembranosus bursa [R-BAKER] |
| **Contusion**: «bone contusion / bone bruise» | trabecular microfractures with haemorrhage, without a discrete fracture line or contour abnormality [R-BB] | the marrow of the femur, tibia and patella |
| **Fracture**: «fracture» | on MRI, a low-signal line on T1W, surrounded by oedema-like signal on fluid-sensitive sequences; a contusion has the oedema without the line [C] | the femur, tibia, patella and fibula |

- Synovitis and effusion: «contrast-enhanced imaging allows better differentiation between joint effusion and
  synovial disorders» [C], and no tag marks contrast [K]. Rohan: «I know it's hard. I'll tell you later.»
- How medicine detects each finding is left out here on purpose («First objects, injury diagnosis later»); the
  sources below hold it *(Claude)*.

## 6. Which conditions touch each object *(Claude, compiled from §4–5)*

| object | conditions |
|---|---|
| femur | Medial OA, Lateral OA, PF OA, Contusion, Fracture, ACL and MCL (attachments) |
| tibia | Medial OA, Lateral OA, Contusion, Fracture, ACL and MCL (attachments), both meniscus tears (plateau beneath) |
| patella | PF OA, Contusion, Fracture |
| fibula | Fracture |
| bone marrow | Contusion, Fracture, all three OA |
| articular cartilage | Medial OA, Lateral OA, PF OA |
| medial meniscus | Medial Meniscus, Medial OA, MCL (attached) |
| lateral meniscus | Lateral Meniscus, Lateral OA |
| ACL | ACL |
| MCL | MCL |
| PCL, LCL | none directly (neighbours) |
| joint cavity and recesses | Effusion, Synovitis |
| synovium | Synovitis, Baker's |
| fat pads | none directly (they border the suprapatellar recess) |
| popliteal fossa: medial gastrocnemius head, semimembranosus tendon, bursa | Baker's |

## 7. Gaps

- Not described by the sources read: the normal look of the synovium.
- [Kh] gives fluid on PD as low in its Table II and water on PD as intermediate in its Table I.
- Read but not used: Kenhub's "Normal knee MRI" contradicts [C], [R-BME] and [R-BB] in places (it calls marrow
  oedema bright on T1 and fluid dark on T2).
- Not reached: Radiopaedia's "MRI of the knee (an approach)", "Fracture" and "Medial collateral ligament of the knee"
  sit behind its anti-bot check, which I did not try to get around.
- The tags cannot separate PD from T2, and none marks contrast [K]. The labels are per study, not per series [K].

## Sources (all read in full, 14 Oct 2026)

- **[K]** Kaggle, *RSNA Knee Abnormalities Detection* (`rsna-knee-abnormality-detection`), Data page.
- **[C]** Chien A, Weaver JS, Kinne E, Omar I. Magnetic resonance imaging of the knee. *Pol J Radiol.*
  2020;85:e509–e531. doi:10.5114/pjr.2020.99415 (PMC7571514; CC BY-NC-ND 4.0).
- **[Kh]** Khanna AJ, Cosgarea AJ, Mont MA, Andres BM, Domb BG, Evans PJ, Bluemke DA, Frassica FJ. Magnetic
  resonance imaging of the knee: current techniques and spectrum of disease. *J Bone Joint Surg Am.* 2001;83-A
  Suppl 2 Pt 2. Read at https://www.benjamindombmd.com/pdf/mri-knee-2001.pdf (Tables I and II).
- **[AUR]** McClure KE, Trunz LM (Jefferson). *How to approach a Knee MRI.* Association of University Radiologists,
  ACER educator resource (PDF).
- **Radiopaedia** reference articles: **[R-KNEE]** Knee joint, rID 31365 · **[R-ACL]** Anterior cruciate ligament,
  rID 23201 · **[R-ACLT]** Anterior cruciate ligament tear, rID 12490 · **[R-MCLI]** Medial collateral ligament injury
  of the knee, rID 79899 · **[R-MEN]** Knee menisci, rID 26810 · **[R-MT]** Meniscal tear, rID 32943 · **[R-OA]**
  Osteoarthritis of the knee, rID 37587 · **[R-EFF]** Joint effusion, rID 10594 · **[R-SYN]** Synovitis, rID 67379 ·
  **[R-BAKER]** Baker cyst, rID 21117 · **[R-BB]** Bone bruise, rID 32984 · **[R-BME]** Bone marrow edema, rID 62224.
  Also read in full, for the diagnosis step later: Patterns of bone bruise in knee injury (rID 43268) and Tibial
  plateau fracture (rID 15615).
- **[W-ECF]** Wikipedia, "Extracellular fluid", § Interstitial fluid (oldid 1379802233).
- **[LP-PLC]** LaPrade RF, Ly TV, Wentorf FA, Engebretsen L. The posterolateral attachments of the knee: a
  qualitative and quantitative morphologic analysis of the fibular collateral ligament, popliteus tendon,
  popliteofibular ligament, and lateral gastrocnemius tendon. *Am J Sports Med*, 2003; cadaveric study of ten knees.
  Read in full 15 Oct 2026, at
  https://www.klokeavskade.no/globalassets/publications/laprade_2003_amjs_the-posterolateral-attachments-of-the-knee--.pdf
- **[LP-MED]** LaPrade RF, Engebretsen AH, Ly TV, Johansen S, Wentorf FA, Engebretsen L. The anatomy of the medial
  part of the knee. *J Bone Joint Surg Am.* 2007;89:2000–10. doi:10.2106/JBJS.F.01176; cadaveric study of eight
  knees. Read in full 15 Oct 2026, at
  https://drrobertlaprademd.com/wp-content/uploads/2015/07/anatomy-of-the-medial-part-of-the-knee-2007.pdf; its
  tables of measurements are in the journal's online appendix, which was not read.
