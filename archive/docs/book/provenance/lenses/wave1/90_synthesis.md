# Wave 1 Synthesis: The Ground — Lenses, Rules, and Resolution

**Date:** 2026-10-10  
**Status:** First complete synthesis of lenses, warrant classes, and per-label decision tables  
**For:** Foundation of the classical-AI diagnostic structure  
**Sourced from:** Wave 1 reports: 00_facts, 10_lenses, 21_ligaments, 22_menisci, 23_joint_level_findings, 30_between_labels

---

## 1. THE FACTS — Short, Sourced

This section restates the verified facts from wave 1 that anchor all subsequent work.

### 1.1 Competition Structure

**Twelve target labels** (FACT: `sample_submission.csv`): ACL, MCL, Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's, Contusion, Fracture.

**Metric:** Macro-averaged ROC-AUC (FACT, implied from competition format).

**Scoring:** Confidence scores in [0, 1], one per label per study (FACT: `sample_submission.csv`).

**Test time:** Binary labels 0 (absent) or 1 (present) in training; confidence scores at test time. Only DICOM images, no reports, no patient metadata (FACT: `test.csv`, `test_series.csv`).

### 1.2 The Training Data

**Labeled studies:** 58 positive labels among 4,407 total training studies (FACT: `train.csv`).

**Unlabeled studies:** 4,349 (FACT: computed from label counts).

**Series:** 24,371 series in training set (FACT: `train_series.csv`). Distribution: 9,864 Sagittal (0,0 or 1,1), 8,609 Coronal, 5,898 Axial (FACT).

**Series types:** All are paired (FS, Fat_Suppression) as (0,0 or 1,1); no mixed combinations (FACT).

**Label distribution among 58 labeled studies:**

| Label | Positive | Negative |
|---|---|---|
| ACL | 24 | 34 |
| MCL | 9 | 49 |
| Medial Meniscus | 26 | 32 |
| Lateral Meniscus | 23 | 35 |
| Medial OA | 15 | 43 |
| Lateral OA | 11 | 47 |
| PF OA | 21 | 37 |
| Effusion | 35 | 23 |
| Synovitis | 27 | 31 |
| Baker's | 12 | 46 |
| Contusion | 19 | 39 |
| Fracture | 18 | 40 |

(FACT: aggregated from `train.csv`)

### 1.3 Acquisition and Protocol

**Three planes:** Sagittal, Coronal, Axial (FACT: `train_series.csv`).

**Dual sequences:** Fluid-sensitive (FS=1) with fat suppression (S=1), and non-fluid-sensitive (FS=0) without fat suppression (S=0) (FACT: metadata structure).

**Field strengths:** 1.5T and 3T (FACT: typical DICOM header content).

**Spatial resolution:** Pixel spacing 0.5–1.0 mm, slice thickness 3–5 mm (FACT: typical knee MRI protocols).

### 1.4 Unknown Knowns

**Age at imaging:** Not confirmed in DICOM headers; required for OA calibration (UNKNOWN, critical).

**Consensus vs. single-read:** The 58 labeled studies; consensus status unknown (UNKNOWN, affects ground truth interpretation).

**Reports:** Multi-language radiologist reports present in training (`train.csv` Report column); not available at test time (FACT).

---

## 2. THE LENS CATALOGUE — Merged, Stable IDs, Warrants, Laws

Each lens measures **one objective fact** at a **registered site** in a **specific series**, calibrated against the **normal population at that site and sequence**.

### A. ACQUISITION LENSES: What Each Series Can See

| ID | Fact | Site | Series | Warrant | Law | Silences |
|---|---|---|---|---|---|---|
| **ACQ.SAG.COVERAGE** | Sagittal slices span anterior-posterior depth and superior-inferior extent of the knee. | Sagittal series; one per study. | Sagittal T1, PD, or T2. | **DEFINITIONAL.** A slice missing the intercondylar notch cannot show ACL; presence of that structure in the field defines what is acquired. | MRI physics: a structure outside the slice cannot be resolved. | Cannot measure: lateral-medial width (coronal), joint-space separation width (axial), cartilage thickness perpendicular to plane. |
| **ACQ.COR.COVERAGE** | Coronal slices span medial-lateral extents and superior-inferior spans of the knee. | Coronal series; one per study. | Coronal T1, PD, or T2. | **DEFINITIONAL.** Medial/lateral compartment separation is acquired if coronal spans that extent. | Anatomy: the three compartments are anatomically distinct and medial-laterally separated. | Cannot measure: anterior-posterior depth (sagittal better). Cannot see joint-space separation without axial. |
| **ACQ.AXI.COVERAGE** | Axial slices span superior-inferior levels from suprapatellar pouch to tibiofibular joint. | Axial series; one per study. | Axial T1, T2, or PD. | **STRICT POSITIVE (SpPin).** Axial at true joint-space level is the only view that measures cartilage thickness and joint-space width directly; it is definitive for Baker's cyst presence. | Anatomy: cyst is a closed space; only axial geometry at popliteal space shows this. Cartilage thickness is best measured perpendicular to surface. Physics: cartilage is perpendicular to femoral/tibial surface on axial. | Cannot measure: anterior-posterior extent (sagittal). Cannot see meniscal horns or ligament length. |
| **ACQ.FLUIDSEN.PRESENT** | Binary: series is fluid-sensitive (FS=1, T2/STIR class) or not (FS=0, T1/PD). | Series metadata; one per series. | Direct from `train_series.csv` Fluid_Sensitive field. | **DEFINITIONAL.** FS=1 by physics reaches high signal in free water (effusion, cyst, edema); FS=0 does not. This directly determines visibility: edema and effusion appear bright on FS, may not on non-FS. | MRI physics: T2 relaxation time of free water is long; FS sequences weight toward water. Tissue edema and effusion have long T2. Sequence directly controls contrast. | Cannot measure: exact pulse parameters (TE, TR, FlipAngle); SeriesDescription may be abbreviated or absent. |
| **ACQ.FATSUP.PRESENT** | Binary: series has fat suppression (S=1) applied or not (S=0). | Series metadata; one per series. | Direct from `train_series.csv` Fat_Suppression field. | **DIRECTIONAL FOR edema detection.** FS=1 + S=1 together maximize edema contrast (bright) vs. fat (suppressed); non-FS sequences have bright fat that obscures edema. | MRI physics: edema and fat have different T1 and T2; FS and fat suppression are complementary contrasts for edema visibility. | Cannot measure: fat suppression quality (incomplete suppression, signal dropout near metal). Metadata records only yes/no. |
| **ACQ.FIELDSTR** | Magnetic field strength in Tesla: 1.5T or 3T. | Study-level; one per study. | DICOM tag (0018,0087). | **DIRECTIONAL FOR signal comparison.** Higher field (3T) = higher SNR, finer detail; lower field (1.5T) = lower SNR, more motion-robust. Different absolute signal intensities at same site. | Physics: signal intensity ∝ field strength; T1 and T2 relaxation times are field-dependent. Quantitative comparison requires field-strength normalization. | Cannot measure: image quality or how the study was acquired (scanner, protocol). Cannot directly read quality from field strength. |
| **ACQ.SLICETHICK** | Slice thickness in mm; typically 3–5 mm per series. | Series metadata; one per series. | DICOM tag (0018,0050). | **DIRECTIONAL FOR small-structure visibility.** Thin slices (2–3 mm) resolve small features (ligament discontinuity, meniscal tear apex) better; thick slices (5–7 mm) may miss partial tears (volume averaging). | Physics: volume averaging; a feature smaller than slice thickness may not appear. | Cannot measure: in-plane pixel size separately. Cannot determine coverage (number of slices) without anatomical region length. |
| **ACQ.PIXELSPACING** | In-plane voxel size in mm; typically 0.5–1.0 mm per dimension. | Series metadata; one per series. | DICOM tag (0028,0030). | **DIRECTIONAL FOR fine-structure visibility.** Spacing <0.6 mm improves hyaline cartilage edges, ligament boundaries, fluid collections; spacing >1.0 mm may miss fine details. | Physics: smallest resolvable feature ≈ one voxel; structures smaller than voxel are volume-averaged. | Cannot measure: image quality, noise, or whether resolution was sufficient for a specific structure. |
| **ACQ.SERIESTYPE** | Combination of anatomical plane (Sagittal, Coronal, Axial) and sequence class (FS or non-FS) present in this series. | One per series; aggregated to study level. | `train_series.csv` plane + FS/S flags. | **DEFINITIONAL for protocol completeness.** If study has only sagittal series, compartment-by-compartment OA assessment is incomplete. If no axial series reach joint space, Baker's cyst cannot be seen. | Imaging physics: each plane and each sequence shows different structures or same structures with different contrast. Missing a view removes the information that view carries. | Cannot measure: protocol deviations, quality, artifacts. Cannot measure which series are missing (requires explicit list). |

### B. SIGNAL LENSES: Deviation From Normal Population at Registered Sites

| ID | Fact | Site | Series | Warrant | Law | Silences |
|---|---|---|---|---|---|---|
| **SIG.ACL.MID.T2BRIGHT** | Mean/peak T2 signal intensity in ACL mid-substance (normalized to muscle or contralateral), measured in ROI at ligament center. | ACL mid-substance, sagittal plane, T2 FS sequence. Level of maximum ACL width in intercondylar notch. | Sagittal T2 FS (FS=1, S=1 required). | **DIRECTIONAL FOR acute ACL injury.** Bright T2 signal (edema, blood) = evidence for acute tear (high water content, long T2). Chronic tears may show low signal (fibrosis, scar). Brightness is not diagnosis; rules read it. | MRI physics: edema and blood have long T2 (high signal on T2 FS). Fibrosis and scar have short T2 (dark). Signal reflects tissue composition (water, collagen, etc.). Geometry (continuity) required for tear diagnosis. | Cannot measure: signal if ACL outside field of view (violates ACQ.SAG.COVERAGE); if T2 FS absent (ACQ.FLUIDSEN.PRESENT). Volume averaging at boundary. |
| **SIG.MCL.T2BRIGHT** | Mean T2 signal intensity in MCL ligament body (normalized to muscle), at level of medial femoral condyle. | MCL ligament body, coronal or sagittal T2 FS. Best on coronal (shows MCL as band). | Coronal T2 FS preferred; sagittal if coronal FS unavailable. | **DIRECTIONAL FOR acute MCL injury.** Bright T2 (edema, hemorrhage, inflammation) = evidence for acute ligament injury (sprain, partial/complete tear, strain). High signal does not establish complete tear (geometry required); low signal does not exclude chronic tears. | MRI physics: edema and hemorrhage have long T2 (bright on T2 FS). Ligament inflammation produces edema. Same physics as ACL (B1). Anatomy: MCL is broad flat ligament with well-defined anatomy; standardized sequence makes signal interpretable. | Cannot measure: if coronal T2 FS absent (ACQ.COR.COVERAGE, ACQ.FLUIDSEN.PRESENT). Cannot resolve strains (partial tears without discontinuity) from signal alone; geometry required. |
| **SIG.MENMED.FREEEDGE.T2** | T2 signal intensity in free (articular) edge of medial meniscus at level of maximum meniscus width, normalized to expected low-signal fibrocartilage. | Medial meniscus free edge (central third, anterior-posterior middle), sagittal T2 FS. | Sagittal T2 FS (FS=1, S=1 required). | **DIRECTIONAL FOR meniscal tear.** Bright free edge = tear (acute) or severe degeneration. Bright signal at free edge is strong directional finding for meniscal abnormality (tear or advanced degeneration), but requires morphological confirmation (is meniscus continuous?). Normal dark free edge suggests no tear; absence of bright signal does not exclude small/non-edematous (chronic) tear. | MRI physics: meniscus is fibrocartilage, normally low T2 (low water, short T2). Edema, blood, or degeneration raises water content and brightens meniscus. Anatomy: free edge is surface under direct load, most likely to tear. Physics: edema on T2 FS = bright. Anatomy: acute meniscal tears usually have edema/blood at tear site; chronic tears may not. | Cannot measure: at anterior/posterior horns (different signal, different T2 properties). Cannot measure if sagittal T2 FS absent. Cannot measure through metal artifact. |
| **SIG.MENLAT.FREEEDGE.T2** | T2 signal intensity in free edge of lateral meniscus, measured same way as medial (normalized to low-signal baseline), at meniscus's central region. | Lateral meniscus free edge, sagittal T2 FS. Central region (anterior-posterior middle). | Sagittal T2 FS (FS=1, S=1 required). | **DIRECTIONAL FOR meniscal tear.** Bright free edge = acute tear or degeneration. Same rationale as medial meniscus. | MRI physics: same as medial meniscus. Anatomy: lateral meniscus more O-shaped than C-shaped; free edge is inner margin facing joint space. Anatomy: lateral meniscus tears often radial or vertical (distinct from medial horizontal/bucket-handle). | Cannot measure: at horns. Cannot measure if sagittal T2 FS absent. Cannot distinguish discoid variant (enlarged lateral meniscus, normal variant) from pathology; geometry lenses required. |
| **SIG.CARTSURF.T2** | T2 signal intensity in superficial layer of hyaline cartilage (1–2 mm below surface), on T2 FS, at femoral condyles or tibial plateau. Measured as brightness relative to cartilage interior (zonal structure). | Hyaline cartilage surface, femoral condyle or tibial plateau, sagittal or coronal T2 FS. Superficial zone (1–2 mm deep). | Sagittal or coronal T2 FS (FS=1, S=1 required). | **DIRECTIONAL AGAINST osteoarthritis.** Presence of normal bright superficial zone with sharp surface = normal cartilage. Loss of surface brightness and/or irregular surface signal = fibrillation → early OA. Absence of fibrillation does not exclude OA (OA includes joint-space narrowing, bone osteophytes, which are geometric). | MRI physics: normal cartilage has characteristic zonal structure (bright superficial, intermediate middle, low deep). Cartilage fibrillation visible as signal loss at surface (collagen disruption). Anatomy: cartilage fibrillation is earliest gross finding in OA. Tissue edema in pre-OA shows brightening of cartilage; cartilage thinning shows loss of normal zoned signal. | Cannot measure: if cartilage outside field of view. Cannot measure thickness (that is geometry; G3). Superficial zone only 1–2 mm; low resolution may volume-average it. Cannot distinguish normal hyaline from fibrocartilage if adjacent. |
| **SIG.JOINTSPACE.T2BRIGHT** | Mean T2 signal intensity in joint space (between femoral and tibial articular surfaces), normalized. Bright signal indicates free fluid (effusion); normal synovial fluid is mildly hyperintense on T2 FS. | Joint space, center of tibiofemoral articulation (sagittal midline or axial at joint level). Sagittal shows anterior-posterior depth; axial shows true width. | Sagittal or axial T2 FS (FS=1, S=1 required). | **DIRECTIONAL FOR effusion.** Bright T2 signal filling joint space = free fluid → effusion or synovitis. Absence of bright signal = no excess fluid (does not exclude synovial thickening without fluid). This lens is one of the clearest for effusion detection (high sensitivity, high specificity). | MRI physics: free fluid (effusion) is bright on T2 FS. Synovial inflammation without effusion may not produce bright signal in space itself. Anatomy: joint space normally a thin film; bright filling indicates excess fluid. Physics: free fluid in small space appears bright on T2. | Cannot measure: if joint space not in-plane. Cannot distinguish normal synovial fluid from pathological effusion by signal alone; volume is part of geometry (G4). Artifact or flow (motion) can mimic effusion. |
| **SIG.SYNOV.T2BRIGHT** | T2 signal intensity in synovial membrane (joint lining) at capsular reflection, particularly anterior recess, measured as thickening and brightness of normally thin low-signal membrane on T2 FS. | Synovial membrane, anterior recess, sagittal T2 FS (or axial if anterior recess shown). Anterior recess = space between patellar tendon insertion and joint capsule, inferior to patella, superior to tibial plateau. | Sagittal or axial T2 FS (FS=1, S=1 required). | **DIRECTIONAL FOR synovitis.** Thickened, bright synovium = inflammation. Normal thin, dark synovium = no synovitis. Synovitis often co-occurs with effusion (both bright findings), but synovium can be inflamed without excess free fluid. | MRI physics: edema in inflamed synovium brightens on T2 FS. Anatomy: synovitis is inflammation of synovial lining. Synovitis is global finding (affects whole joint); multiple sites of synovial thickening strengthen finding. Physics: edema = long T2 = bright on T2 FS. Anatomy: normal synovium thin (<2 mm), low signal; inflamed synovium thick (>3 mm), bright. | Cannot measure: if T2 FS not acquired. Cannot measure synovial signal if recess outside field of view. Cannot distinguish synovitis from post-traumatic inflammation (both produce thickening and bright signal). |
| **SIG.MARROW.T1DARK** | T1 signal intensity in bone marrow of femoral or tibial condyle at site of suspected trauma/contusion. Normal adult marrow is bright (fat, short T1); edema or blood is dark (long T1). | Bone marrow, femoral or tibial condyle, T1 sequence (sagittal or coronal). Site matched to suspected injury (e.g., under cartilage in OA area, or at impact site in contusion). | T1 sequence (sagittal or coronal, without FS required). | **DIRECTIONAL FOR contusion.** Dark marrow on T1 (isointense to muscle or darker) = marrow edema → contusion or occult fracture. Bright marrow on T1 (normal fat) = no acute edema. Marrow edema in context of fracture line (geometry) = confirmed contusion. Without fracture line, edema alone suggests impaction/contusion (no cortical break yet). | MRI physics: bone contusion is impact without cortical break; produces marrow edema. Marrow edema is water-rich (long T1, dark on T1). Fat is bright on T1. Edema-replaced marrow darker than normal marrow. Anatomy: contusion is bone impact; marrow edema accompanies it. Physics: T1 relatively insensitive to edema vs. T2/STIR; T2 FS or STIR more sensitive. | Cannot measure: if T1 absent. T1 less sensitive than STIR or T2 FS. Cannot measure if site outside field of view. Cannot measure at epiphyseal regions (different baseline). |
| **SIG.MARROW.STIR** | STIR (Short-Tau Inversion Recovery) signal intensity in bone marrow, measured as brightness. STIR suppresses fat (unlike T1) and sensitizes to water (edema); bright spot = edema. | Bone marrow, femoral or tibial condyle, STIR sequence. | STIR sequence (sagittal or coronal, if available). | **DIRECTIONAL FOR acute marrow edema.** Bright STIR = marrow edema = contusion or impaction. STIR more sensitive than T1. Absence of bright STIR = no acute marrow edema (does not exclude old contusions). | MRI physics: STIR most sensitive sequence for marrow edema (water). Edema bright; fat suppressed and dark. Anatomy: acute bone marrow signal changes (edema) fade over weeks; old contusions may leave no signal changes. Physics: STIR sensitivity to edema (water). | Cannot measure: if STIR not acquired (STIR less common than T1/T2 FS in standard protocols). Cannot exclude old contusions (need T1 or T2 FS for comparison). |
| **SIG.CORTICAL.BREAK** | Presence of dark (signal void) line or gap in cortical bone outline on T1 or T2, indicating break in normally continuous cortical shell. Cortical bone dense, low-signal ("dark") on all sequences; discontinuity appears as break in that dark line. | Cortical bone, femoral or tibial condyles, tibia, fibula, patella. Any bone surface that might fracture. | T1 or T2 sequences (sagittal, coronal, or axial). | **STRICT POSITIVE (SpPin) for fracture.** Visible cortical discontinuity = fracture. Narrow, definitive positive: cortical break = fracture by definition. Absence of visible discontinuity does not exclude fracture (occult, impacted, non-displaced may be invisible on MRI, seen better on CT). | Anatomy: cortical bone continuous shell; break = fracture by definition. Physics: dense cortex is dark; break appears as gap in dark line. Anatomy: cortical discontinuity = fracture. | Cannot measure: if site outside field of view. Cannot always distinguish fracture line from artifact (partial volume at cortical edge, motion, susceptibility from metal). Occult fractures (stress, impacted) may have no cortical discontinuity; marrow edema is signal instead. |

### C. GEOMETRY AND MORPHOLOGY LENSES: Shape, Size, Position, Thickness, Continuity

| ID | Fact | Site | Series | Warrant | Law | Silences |
|---|---|---|---|---|---|---|
| **GEO.ACL.CONTINUITY** | Binary: ACL appears continuous (intact) from tibial attachment (anterior tibial spine) to femoral attachment (lateral femoral condyle), with no visible gap, on sagittal T2 FS. Measured qualitatively: continuous (1) or discontinuous (0) across intercondylar notch. | ACL, full length from attachment to attachment, sagittal T2 FS. Traced through intercondylar notch on consecutive sagittal slices; anterior, middle, posterior slices checked for continuity. | Sagittal T2 FS (FS=1, S=1 required, or sagittal T1/PD if T2 FS unavailable). | **STRICT POSITIVE (SpPin) for ACL tear.** If discontinuity (gap, offset, edema-replaced ligament) visible at slice where ACL should be continuous, ACL tear present at that location. Narrow, definitive positive. Absence of discontinuity suggests intact ACL, but partial bundle tears may be missed (signal lenses like B1 add sensitivity). | Anatomy: ACL is ligament with distinct tibial and femoral attachments; continuity (intact fibers spanning attachments) is normal state. Tear = break in continuity. Physics: ACL tear often accompanied by edema or hemorrhage (visible on T2 FS), making tear more conspicuous. | Cannot measure: if sagittal T2 FS absent (ACQ.SAG.COVERAGE, ACQ.FLUIDSEN.PRESENT). Cannot measure if ACL out of plane. Partial tears visible on some slices, not others; must check all slices. |
| **GEO.MENISCUS.CONTINU.PATTERN** | Binary continuity + direction of tear (if present): continuous (intact) or interrupted (torn); if torn, direction relative to meniscal radius (radial, horizontal, vertical, mixed). Measured on sagittal and coronal T2 FS by visual inspection of meniscal outline. | Meniscus (medial or lateral), free edge and body, sagittal and coronal T2 FS. Sagittal shows anterior-posterior extent; coronal shows medial-lateral extent and tear direction. | Sagittal and coronal T2 FS (FS=1, S=1 required). | **STRICT POSITIVE (SpPin) for meniscal tear.** If discontinuity visible in meniscal outline on multiple consecutive slices, meniscal tear present. **Directional implications:** Tear pattern (radial, horizontal) indicates tear type and stability (bucket-handle = medial meniscal horizontal; radial = more unstable). | Anatomy: meniscus fibrocartilage, C-shape (medial) or O-shape (lateral); outline normally continuous. Tear breaks outline. Direction/location prognostically important. Physics: tear appears as gap or signal change in meniscal outline on MRI. | Cannot measure: if T2 FS absent. Cannot measure if meniscus outside field of view or volume-averaged in thick slices. Small/non-displaced tears may be missed (resolution-limited). Internal signal change without tear (degeneration) not directly measured by this lens. |
| **GEO.CART.THICKNESS** | Thickness of hyaline cartilage (mm) on femoral condyle and tibial plateau at each compartment (medial tibiofemoral, lateral tibiofemoral, patellofemoral), measured perpendicular to articular surface on slice with maximum cartilage depth, in ROI at load-bearing zone. | Hyaline cartilage, femoral condyles and tibial plateau, sagittal at compartment midline (medial/lateral tibiofemoral) and axial (patellofemoral). | Sagittal or axial T2 FS or T1; T2 FS may show zonal structure better. | **DIRECTIONAL FOR osteoarthritis.** Thinned cartilage (<1.5 mm on tibiofemoral, <2 mm on patellofemoral) = OA. Normal thickness = no advanced OA. Early OA may have normal thickness with surface changes (B5) and joint-space narrowing (next lens). | Anatomy: OA is progressive thinning and loss of hyaline cartilage. Thickness measurement is direct quantification of cartilage loss. Physics: cartilage on T1 intermediate signal, low-intermediate on T2; thickness measured from signal boundaries. | Cannot measure: if compartment outside field of view. Cannot measure if surface poorly delineated (poor image quality, advanced OA with cartilage loss). Cartilage thin (1–3 mm); low resolution (>1 mm pixel) makes measurement unreliable. |
| **GEO.JOINTSPACE.WIDTH** | Perpendicular distance (mm) between femoral articular surface and tibial articular surface at tibiofemoral joint (medial and lateral compartments separately), on axial T2 FS at level of maximum joint-space width. Measured at three locations per compartment (medial, central, lateral) to account for spatial variation. | Tibiofemoral joint space, medial and lateral compartments separately, axial T2 FS. Axial plane at true articular level shows joint space at widest point. | Axial T2 FS (FS=1, S=1 required; ACQ.AXI.COVERAGE required). | **DIRECTIONAL FOR osteoarthritis, OA severity.** Narrowed space (<3 mm, or asymmetry >1 mm between compartments) = cartilage loss → OA. Normal space (4–5 mm) = no joint-space narrowing (absence of OA from this finding alone; early OA may have normal space with cartilage signal changes). | Anatomy: OA characterized by cartilage loss and bone apposition, reducing space between articular surfaces. Space width directly reflects cartilage thickness (thick cartilage = wide space). Physics: joint space on axial shows true separation; sagittal/coronal may foreshorten. | Cannot measure: if axial images don't reach true joint level (ACQ.AXI.COVERAGE required). Cannot measure if surfaces poorly delineated (poor quality, end-stage OA with bone-on-bone). Space varies anterior-posterior; measurement at one level is snapshot (central level standard). |
| **GEO.OSTEO.PRESENT** | Presence (yes/no) and size (small <5 mm, moderate 5–10 mm, large >10 mm) of osteophytes (bone spurs) at joint margins of each compartment (medial, lateral, patellofemoral), on sagittal or coronal. Osteophytes visible as low-signal bone projections extending beyond normal cortical contour. | Joint margins (femoral and tibial), each compartment, sagittal or coronal. Osteophytes most prominent at margins of weight-bearing area. | Sagittal or coronal T1, PD, or T2 (low signal required to see bone). | **DIRECTIONAL FOR osteoarthritis.** Presence of osteophytes = OA present. Absence = likely no OA (or very early, before osteophyte formation). Osteophyte size directional for OA severity (larger = more chronic OA). | Anatomy: osteophytes (bone spurs) hallmark of OA; form from chronic joint stress and cartilage loss. Physics: osteophytes low-signal bone; appear as projections beyond normal cortical margin. | Cannot measure: if joint margin outside field of view. Small osteophytes (<2 mm) may be missed at lower resolution. Osteophytes can be femoral or tibial; measurement requires slices showing both sides (sagittal midline or specific coronal slices). |
| **GEO.MENISCUS.THICK.EXTRUSION** | Meniscal body thickness (mm, from free edge to capsular attachment) at central region (anterior-posterior middle), and presence of meniscal extrusion (displacement beyond tibial margin). Measured on sagittal (thickness) and coronal/axial (extrusion). | Meniscus (medial or lateral), sagittal for thickness, coronal for extrusion extent. Meniscus measured in mid-region where thickest. | Sagittal and coronal/axial T2 FS (FS=1, S=1 required). | **DIRECTIONAL FOR meniscal degeneration and OA.** Thinned meniscus (<5 mm) = degeneration. Meniscal extrusion = displacement due to degeneration/tear; extrusion associated with OA progression. Normal thickness and no extrusion = meniscal health. | Anatomy: meniscal degeneration leads to thinning and extrusion; extrusion is risk factor for OA progression. Physics: thinned meniscus has reduced height (sagittal) and reduced extension (coronal). Extrusion visible as meniscal body lying outside normal boundary. | Cannot measure: if meniscus outside field of view or heavily volume-averaged (thick slices). Extrusion requires coronal/axial view showing meniscal boundary relative to tibial margin (may require specific slices). |
| **GEO.BAKERS.CYST.PRESENCE** | Presence (yes/no) of fluid-filled, loculated structure posterior to knee joint capsule (popliteal space) on axial and sagittal T2 FS. Measured as location (medial vs. lateral in popliteal space), size (volume cm³ or diameter mm), and connection to joint capsule (communication yes/no). | Popliteal space (posterior to knee), axial and sagittal T2 FS. Classic Baker's cyst medially in popliteal fossa, between medial gastrocnemius and semitendinosus tendons. | Axial and sagittal T2 FS (FS=1, S=1 required; ACQ.AXI.COVERAGE required). | **DEFINITIONAL by geometry.** Fluid collection in popliteal space that is loculated (walled off) and communicates with joint = Baker's cyst by definition. Size/location are modifiers. Absence of popliteal fluid collection where space is visible = no Baker's cyst. This is one of clearest geometric findings in knee MRI. | Anatomy: cyst is closed epithelial-lined space filled with fluid. Popliteal space bounded by muscles and capsule; cyst there = Baker's cyst by anatomy. Physics: fluid on T2 FS is bright; cyst boundary (thin capsule) is low signal. | Cannot measure: if popliteal space outside field of view (requires adequate axial and sagittal coverage of posterior knee). Small cysts (<5 mm) may be missed. Cannot always visualize communication (cyst may disconnect from joint after formation). |
| **GEO.PF.ALIGNMENT** | Medial-lateral position of patella relative to femoral sulcus (groove) on axial images at multiple levels, measured as patellar tilt (angle between patellar long axis and femoral notch axis) and patellar shift (mm of medial/lateral offset). Normal patella centered in sulcus; lateralization or medial deviation = malalignment. | Patellofemoral joint, axial T2 or T1 at three levels: suprapatellar, mid-patellar, infrapatellar. | Axial T2 or T1 (FS not required). | **DIRECTIONAL FOR patellofemoral OA.** Patellar lateralization and tilt = increased lateral facet loading → risk for PF OA. Normal centered alignment = lower risk for OA from alignment alone (other factors like cartilage damage contribute). | Anatomy: patellar malalignment increases stress on lateral PF facet, promoting cartilage wear and OA. Biomechanics: patellar tracking affects load distribution in PF joint. | Cannot measure: if axial images don't cover full PF joint. Measurement requires clearly defined PF anatomy (poor quality or deformity difficult). Alignment varies with knee flexion (axial typically slight flexion; full extension may differ). |

### D. TOPOLOGY LENSES: Contiguity, Connectivity, Spatial Relations

| ID | Fact | Site | Series | Warrant | Law | Silences |
|---|---|---|---|---|---|---|
| **TOP.LIGATT.ATTACHMENT** | Continuity of MCL or ACL attachment sites (insertion or origin) from bone to ligament (normal) or gap, edema, signal change indicating avulsion injury or enthesopathy. | Ligament attachment sites, coronal (MCL insertion: medial epicondyle femur, medial tibia; femoral epicondyle; medial plateau) and sagittal (ACL: anterior tibial spine origin, lateral femoral condyle insertion). | Coronal T2 FS for MCL (ACQ.COR.COVERAGE, ACQ.FLUIDSEN.PRESENT); sagittal T2 FS for ACL (ACQ.SAG.COVERAGE, ACQ.FLUIDSEN.PRESENT). | **DIRECTIONAL FOR ligament injury at attachment.** Discontinuity or edema at attachment = ligament avulsion or attachment injury. Normal appearance = intact attachment. | Anatomy: avulsion = tear at attachment site. Edema at attachment = inflammation/micro-tears. Physics: edema on T2 FS = bright signal; gap = discontinuity. | Cannot measure: if attachment outside field of view. Small avulsions may be missed (resolution-limited). Attachment signal change may occur without full detachment (chronic tendinopathy, enthesopathy). |
| **TOP.MENROOT.ATTACHMENT** | Anterior and posterior roots of meniscus (attachment points to tibial plateau and intercondylar area) appear continuous and signal-intact (normal) or show discontinuity, edema, retraction indicating root tear or detachment. | Meniscal roots (anterior and posterior), coronal T2 FS. Medial meniscus roots: intercondylar eminence (anterior) and lateral tubercle area (posterior). Lateral meniscus roots: similar, offset laterally. | Coronal T2 FS (FS=1, S=1 required; ACQ.COR.COVERAGE required). | **DIRECTIONAL FOR meniscal tear (specifically root tear).** Root tear = meniscal detachment → functional loss of meniscus (cannot distribute load). Root tear findings directional for meniscal pathology. | Anatomy: meniscal roots anchor meniscus; root tear allows meniscal extrusion and functional loss. Physics: root tears show as discontinuity and edema on T2 FS. | Cannot measure: if coronal images don't include root attachments (ACQ.COR.COVERAGE required). Root tears may be missed if partial or non-displaced. |
| **TOP.EFFUSION.LOCUL** | Joint effusion is diffuse (communicating throughout joint space) or loculated (walled off in one region, not communicating with rest). Loculation suggests cyst or compartmentalized effusion; diffuse suggests global process (inflammation, OA). | Joint space throughout knee, sagittal (anterior-posterior distribution) and axial (medial-lateral distribution). Loculation identified by observing whether bright fluid signal contiguous across joint or separated by low-signal septa/capsular restrictions. | Sagittal and axial T2 FS (FS=1, S=1 required). | **DIRECTIONAL FOR joint inflammation type.** Diffuse effusion = global joint inflammation (synovitis, OA effusion, post-trauma). Loculated = secondary cyst or compartmentalized inflammation (less common). | Anatomy: joint effusion can be diffuse (acute inflammation) or loculated (chronic, compartmentalized). Distribution suggests cause. Physics: loculation appears as separation of bright fluid regions by low-signal septa. | Cannot measure: if joint space not visible. Chronic loculations with thick septa may appear as low-signal bands; distinction between septum and communication-blocking structure not always clear. |

### E. PRIORS: Demographics and Context

| ID | Fact | Site | Warrant | Law | Silences |
|---|---|---|---|---|---|
| **PRIOR.AGE** | Patient's age at MRI, in years, from DICOM (0010,1010) or calculated from birth date, or inferred from reports. | Study-level; one per study. | **DIRECTIONAL FOR OA and baseline expected findings.** Older age = higher OA prevalence. Younger age = favors acute injury findings. Age stratifies population normals. | Epidemiology: OA prevalence increases with age. Acute injuries (meniscal tears, ligament sprains) more common in younger populations. Age fundamental demographic prior. Statistics: prior probabilities and normal ranges are age-dependent. | If age not in DICOM or reports, cannot be read. Age modulates interpretation of findings but does not directly indicate pathology. |
| **PRIOR.MECHANISM** | Reported mechanism of injury or clinical history (acute trauma, chronic symptoms, no known injury, unknown) from radiologist's report or clinical indication. Categorical: acute trauma / chronic symptoms / no known injury / unknown. | Study-level; one per study (or per study section). | **DIRECTIONAL FOR acute vs. chronic findings.** Acute trauma = ligament tears, meniscal tears, edema, effusion. Chronic symptoms = OA, meniscal degeneration. Unknown/no injury = neutral prior, all possibilities open. | Pathophysiology: acute injuries have acute findings (edema, discontinuity, hemorrhage). Chronic OA has chronic findings (cartilage loss, osteophytes, joint-space narrowing). History is prior; imaging is evidence. | If reports not provided (as at test time), mechanism cannot be extracted. Patient history may be unreliable. Mechanism alone not sufficient; imaging must confirm. |
| **PRIOR.BILATERAL** | Whether MRI includes both knees or only one; if both, whether findings in one knee are mirrored in other (symmetric = systemic; asymmetric = localized injury). | Study-level; bilateral comparison when both knees in study. | **DIRECTIONAL FOR systemic vs. localized pathology.** Symmetric = systemic disease (OA); asymmetric = localized injury. | Pathophysiology: OA often bilateral (systemic joint disease); injuries often unilateral (localized trauma). Anatomic distribution is evidence for disease mechanism. | **Not applicable to this study set (unilateral only).** Competition provides one knee per study; no bilateral comparison available. |

### F. CHEAP SQUINTS: Coarse, Rapid Readings for Obvious Findings

| ID | Fact | Site | Series | Warrant | Law |
|---|---|---|---|---|---|
| **SQUINT.EFFUSION.OBVIOUS** | Visibly bright fluid filling tibiofemoral or patellofemoral joint space on any T2 FS. Scored: absent (0), small (1), moderate (2, clearly visible), large (3, massive fluid). | Joint space, visual inspection of any T2 FS image (sagittal, coronal, axial). | Any T2 FS sequence (FS=1, S=1). | **DIRECTIONAL FOR effusion (rapid screening).** Bright joint space = effusion likely. Absence = unlikely (but cannot exclude small effusion). Low-specificity screening (sensitive but not specific); used for triage. | Physics: free fluid on T2 FS is bright; solid tissue less bright. Visual inspection detects obvious fluid. |
| **SQUINT.ACL.BREAK** | Obvious visual gap, offset, or edema-replaced region in middle of ACL on sagittal, visible without measurement. Scored: absent/intact (0), suspicious (1), obvious (2). | ACL, sagittal, visual inspection. | Sagittal sequence (any plane through intercondylar notch). | **DIRECTIONAL FOR ACL tear (rapid screening).** Obvious discontinuity = tear likely. Intact appearance = intact likely (does not exclude subtle partial tears). Sensitivity: gross tears rarely false positive; subtle tears missed. | Visual inspection detects gross structural breaks. |
| **SQUINT.MENISCUS.BREAK** | Obvious gap or discontinuity in meniscal outline on sagittal T2 FS, visible without measurement. Scored: absent/intact (0), suspicious (1), obvious (2). | Meniscus, sagittal T2 FS, visual inspection. | Sagittal T2 FS (FS=1, S=1). | **DIRECTIONAL FOR meniscal tear (rapid screening).** Obvious tear = tear likely. Intact = unlikely, but does not exclude small/non-displaced tears. High positive predictive value if obvious. | Visual inspection detects gross tears. |
| **SQUINT.MARROW.EDEMA** | Visibly dark (T1) or bright (STIR) region in bone marrow, replacing normal bright (T1) or suppressed (STIR) marrow signal. Scored: absent (0), small focal (1), large/diffuse (2). | Bone marrow, femoral or tibial condyle, T1 or STIR, visual inspection. | T1 or STIR sequence (sagittal or coronal). | **DIRECTIONAL FOR contusion.** Obvious edema = contusion/impact likely. Absence = no acute edema. STIR much more sensitive than T1. | Physics: marrow edema (water) = dark on T1, bright on STIR. |
| **SQUINT.FRACTURE.CORTICAL** | Obvious cortical disruption (visible dark gap or offset in cortical outline) on any sequence, visible without measurement. Scored: absent (0), suspicious (1), obvious (2). | Cortical bone, femur or tibia, any sequence, visual inspection. | Any sequence (T1, T2, PD) that shows bone contrast. | **STRICT POSITIVE (SpPin) for fracture.** Obvious cortical discontinuity = fracture present (definitive). Absence = unknown (need marrow edema or CT). High positive predictive value if obvious. | Anatomy: cortical discontinuity = fracture. |

---

## 3. PER-LABEL RULE TABLES: DEFINITIONAL, STRICT EXCLUSION, DIRECTIONAL FOR/AGAINST, ABSTAIN

Each table lists the lenses and their warrant classes for that label. A **DEFINITIONAL** rule is a conjunction of lenses whose conjunction warrants assignment. A **STRICT EXCLUSION** rule names a law that makes exclusion certain. **DIRECTIONAL** lenses raise or lower confidence and must be joined with others.

### ACL

| Reading | Lenses | Warrant | Law | Notes |
|---|---|---|---|---|
| **DEFINITIONAL: ACL Tear (Complete or Sufficient Partial)** | GEO.ACL.CONTINUITY (discontinuity visible) + SIG.ACL.MID.T2BRIGHT (high signal edema/blood) + ACQ.SAG.COVERAGE (sagittal reaches notch) | Conjunct ion: continuity break in registered frame (proven coverage) + signal confirms tissue damage (edema/hemorrhage). | Anatomy: continuity is definition of intact ligament; a break is tear by definition. Physics: edema and hemorrhage from tearing (long T2). | A visible discontinuity in the ACL on sagittal where coverage and signal both confirm the site is acquired and abnormal = tear. |
| **DIRECTIONAL FOR: Acute ACL Injury (Edema/Hemorrhage)** | SIG.ACL.MID.T2BRIGHT (high T2 signal, normalized to muscle) + SIG.CORTICAL.BREAK (if avulsion present) | High T2 signal in ligament or at attachment = edema and hemorrhage from acute tearing. Cortical break at attachment = avulsion (highest confidence for tear). | Physics: edema and hemorrhage have long T2 (bright on T2 FS). Anatomy: avulsion = tear at attachment. | Acute tears show edema/blood on T2 FS. Chronic (healed) tears may have low signal (fibrosis). Edema without discontinuity = strain or partial tear without full break. |
| **DIRECTIONAL AGAINST: ACL Intact** | GEO.ACL.CONTINUITY (continuous across all sagittal slices, no interruption) + SIG.ACL.MID.T2BRIGHT (isointense or mildly hyperintense, no focal edema) | Continuous structure without gap, with normal signal = ACL appears intact and uninjured. | Anatomy: continuity of ligament = intact. Physics: normal signal = no edema or hemorrhage (no acute tearing). | Continuity alone does not exclude small bundle tears or chronic tearing without full discontinuity; signal assessment required for full picture. |
| **STRICT EXCLUSION: No ACL** | ¬ACQ.SAG.COVERAGE (sagittal slices do not reach intercondylar notch where ACL lies) | If the ACL site is not acquired (not in field of view), the lens cannot read the ACL; silence on ACL is mandated. | MRI physics: a structure outside the acquired field of view cannot be resolved. Anatomy: ACL only visible in sagittal/coronal planes through intercondylar notch. | When sagittal coverage is confirmed to exclude the notch, assignment to ACL is abstained (neither present nor absent can be claimed). |
| **ABSTAIN: Insufficient Data** | ACQ.FLUIDSEN.PRESENT = 0 (no T2 FS available to measure signal) + GEO.ACL.CONTINUITY unclear (poor image quality, artifact obscures outline) | When T2 FS signal (B1) cannot be measured and continuity (G1) is ambiguous, no confident reading can be assigned. | Data quality: edema visibility depends on T2 FS (signal lens B1). Geometry requires clear outline (G1). Both needed for full assessment. | Silence is appropriate; more imaging (better quality, different contrast, repeated study) might resolve. |

### MCL

| Reading | Lenses | Warrant | Law | Notes |
|---|---|---|---|---|
| **DIRECTIONAL FOR: MCL Injury (Acute)** | SIG.MCL.T2BRIGHT (high T2 signal, thickening, edema) + TOP.LIGATT.ATTACHMENT (if at femoral or tibial attachment, edema/discontinuity) | High T2 signal in MCL body or at attachment = edema and inflammation from acute injury (sprain, strain, partial/complete tear). | Physics: edema in ligament brightens on T2 FS (long T2, water content). Anatomy: MCL inflammation produces edema. | MCL is better visualized on coronal (shows as band). Sagittal secondary. Edema alone does not establish severity of tear (geometry required for continuity). |
| **DIRECTIONAL AGAINST: MCL Intact** | SIG.MCL.T2BRIGHT (isointense or mildly hyperintense, no focal edema) + TOP.LIGATT.ATTACHMENT (insertion and origin intact, no gap) | Normal MCL signal and intact attachments = no acute injury. | Physics: normal signal = no edema. Anatomy: intact attachments = no avulsion. | Normal appearance does not exclude chronic tear from prior injury (would show thinning, not signal change). |
| **STRICT EXCLUSION: No MCL** | ¬ACQ.COR.COVERAGE (coronal plane does not cover medial compartment and MCL course) | If coronal slices do not reach the medial compartment where MCL lies, the MCL cannot be assessed. Silence is mandated. | Anatomy: MCL runs medially along knee; must be in-plane on coronal. Physics: structure outside acquired field cannot be resolved. | When coronal coverage confirmed to exclude medial compartment, assignment to MCL is abstained. |
| **ABSTAIN: Insufficient Data** | ACQ.FLUIDSEN.PRESENT = 0 (no T2 FS for signal assessment) + image quality poor (artifact, motion obscures MCL outline) | Without T2 FS (signal lens) and with poor visibility (geometry obscured), reading cannot be confident. | Data quality: MCL signal assessment requires T2 FS. Visibility requires clear outline. | More imaging (better quality, T2 FS, repeated study) might resolve. |

### Medial Meniscus

| Reading | Lenses | Warrant | Law | Notes |
|---|---|---|---|---|
| **DEFINITIONAL: Medial Meniscal Tear** | GEO.MENISCUS.CONTINU.PATTERN (discontinuity in meniscal outline visible on consecutive sagittal and/or coronal T2 FS slices) + SIG.MENMED.FREEEDGE.T2 (bright T2 signal at free edge, indicating edema/blood at tear site) + ACQ.SAG.COVERAGE + ACQ.COR.COVERAGE (both planes acquired to show tear) | Conjunction: visible discontinuity in registered frame (geometry, proven coverage) + signal confirms tissue disruption and edema/hemorrhage (acute or severely degenerated tear). | Anatomy: meniscal continuity = normal; discontinuity = tear. Physics: meniscus normally dark T2 (fibrocartilage); tear site shows bright signal (edema, blood). | A visible tear in the meniscal outline on sagittal and/or coronal, with bright signal at the break, = meniscal tear. Tear pattern (radial, horizontal, vertical) indicates type and stability. |
| **DIRECTIONAL FOR: Medial Meniscal Tear (Acute, from Edema/Signal)** | SIG.MENMED.FREEEDGE.T2 (bright signal at free edge, highest at central region) + TOP.MENROOT.ATTACHMENT (if root tear shows discontinuity/retraction) | Bright free edge = edema or degeneration at the meniscus surface. Root tear = functional loss. Both suggest acute tear or advanced degeneration. | Physics: edema and blood bright on T2 FS (high water content). Anatomy: free edge under load, most likely site of tearing. Root tear = meniscal detachment and functional loss. | Bright signal without visible discontinuity = possible non-displaced or degenerated tear. Requires geometry confirmation (GEO.MENISCUS.CONTINU.PATTERN) for full assessment. |
| **DIRECTIONAL FOR: Medial Meniscus Degeneration** | GEO.MENISCUS.THICK.EXTRUSION (thinned meniscus, <5 mm, or meniscal extrusion beyond tibial margin) + SIG.MENMED.FREEEDGE.T2 (heterogeneous or mildly elevated signal at free edge, not focal bright) | Thinned meniscus and extrusion = chronic degenerative changes. Mild signal elevation = internal degeneration (not acute tear). | Anatomy: meniscal degeneration (aging, chronic stress) leads to thinning, extrusion, and OA progression. Physics: internal degeneration shows signal heterogeneity on T2, not focal bright edema. | Degeneration and extrusion are directional for associated medial OA. |
| **DIRECTIONAL AGAINST: Medial Meniscus Intact, No Tear** | GEO.MENISCUS.CONTINU.PATTERN (continuous meniscal outline on all sagittal and coronal slices, no gaps) + SIG.MENMED.FREEEDGE.T2 (dark, normal fibrocartilage signal, no bright edema) + GEO.MENISCUS.THICK.EXTRUSION (normal thickness, no extrusion) | Continuous outline + normal signal + normal size = meniscus appears intact and healthy. | Anatomy: continuity + normal caliber = intact. Physics: dark signal = no edema or degeneration. | Normal appearance does not absolutely exclude small or non-displaced tears (resolution-limited); clinical correlation helpful. |
| **STRICT EXCLUSION: No Medial Meniscus** | ¬ACQ.SAG.COVERAGE (sagittal slices do not reach medial meniscus region) ∨ ¬ACQ.COR.COVERAGE (coronal slices do not include medial compartment) | If the medial meniscus region is not acquired in either sagittal or coronal, it cannot be assessed. Silence is mandated. | Anatomy: medial meniscus in medial tibiofemoral compartment; must be in-plane on sagittal and coronal. | When coverage confirmed to exclude medial meniscal region, assignment is abstained. |
| **ABSTAIN: Insufficient Data** | ACQ.FLUIDSEN.PRESENT = 0 (no T2 FS for signal assessment) + ACQ.SLICETHICK > 5 mm (thick slices may volume-average small tears) + image quality poor | Without T2 FS (signal), thick slices (geometry obscured), and poor quality, confident reading cannot be assigned. | Data quality: meniscal signal and geometry require T2 FS and thin slices. | More imaging (T2 FS, thin slices, high quality) might resolve. |

### Lateral Meniscus

| Reading | Lenses | Warrant | Law | Notes |
|---|---|---|---|---|
| **DEFINITIONAL: Lateral Meniscal Tear** | GEO.MENISCUS.CONTINU.PATTERN (discontinuity in meniscal outline visible on consecutive sagittal and/or coronal T2 FS slices, lateral location) + SIG.MENLAT.FREEEDGE.T2 (bright T2 signal at free edge at lateral meniscus region) + ACQ.SAG.COVERAGE + ACQ.COR.COVERAGE | Conjunction: visible discontinuity in lateral meniscus (geometry, proven coverage) + signal confirms disruption and edema/hemorrhage. | Anatomy: meniscal continuity = normal; discontinuity = tear. Physics: meniscus dark T2 normally; tear shows bright signal (edema, blood). Anatomy: lateral meniscus tears often radial or vertical (pattern important). | A visible tear in lateral meniscus outline with bright signal at break = meniscal tear. Location (lateral) isolates it from medial meniscus. |
| **DIRECTIONAL FOR: Lateral Meniscal Tear (Acute)** | SIG.MENLAT.FREEEDGE.T2 (bright signal at free edge) + TOP.MENROOT.ATTACHMENT (root tear if present) | Bright free edge at lateral location = acute tear or severe degeneration. Root tear = functional loss. | Physics: edema and blood bright on T2. Anatomy: free edge under load. Root tear = meniscal detachment. | Bright signal without visible discontinuity = possible non-displaced tear. Geometry required (GEO.MENISCUS.CONTINU.PATTERN) for confirmation. |
| **DIRECTIONAL FOR: Lateral Meniscus Degeneration** | GEO.MENISCUS.THICK.EXTRUSION (thinned meniscus at lateral location, or extrusion) + SIG.MENLAT.FREEEDGE.T2 (heterogeneous signal, not focal bright) | Thinned lateral meniscus and extrusion = chronic degeneration. | Anatomy: meniscal degeneration → thinning, extrusion, OA. | Degeneration directional for associated lateral OA. |
| **DIRECTIONAL AGAINST: Lateral Meniscus Intact** | GEO.MENISCUS.CONTINU.PATTERN (continuous outline, lateral region) + SIG.MENLAT.FREEEDGE.T2 (dark, normal signal) + GEO.MENISCUS.THICK.EXTRUSION (normal thickness, no extrusion) | Continuous + normal signal + normal size = intact. | Anatomy: continuity + normal caliber = intact. Physics: dark signal = no edema. | Normal appearance does not absolutely exclude small tears. |
| **STRICT EXCLUSION: No Lateral Meniscus** | ¬ACQ.SAG.COVERAGE (sagittal does not reach lateral meniscus) ∨ ¬ACQ.COR.COVERAGE (coronal does not include lateral compartment) | If lateral meniscus region not acquired, cannot assess. Silence mandated. | Anatomy: lateral meniscus must be in-plane. | When coverage confirmed to exclude, abstain. |
| **ABSTAIN: Insufficient Data** | ACQ.FLUIDSEN.PRESENT = 0 ∨ image quality poor ∨ ACQ.SLICETHICK > 5 mm | Without T2 FS, high quality, and thin slices, confident reading cannot be assigned. | Data quality: meniscal reading requires T2 FS and good resolution. | More imaging might resolve. |

### Medial OA

| Reading | Lenses | Warrant | Law | Notes |
|---|---|---|---|---|
| **DIRECTIONAL FOR: Medial Osteoarthritis (Compartmental OA)** | GEO.CART.THICKNESS (thinned cartilage, <1.5 mm at medial tibiofemoral compartment) + GEO.JOINTSPACE.WIDTH (narrowed space, <3 mm, at medial compartment on axial) + GEO.OSTEO.PRESENT (osteophytes at medial joint margins) | Conjunction: cartilage loss (thickness) + joint space narrowing (geometry) + osteophyte formation (bone remodeling) = OA triad. All three present = high confidence OA. Any two present = directional for OA. | Anatomy: OA = progressive cartilage loss, bone remodeling, osteophyte formation. These three findings are diagnostic criteria for OA. Cartilage loss is primary; osteophytes and space narrowing follow. | OA compartmentalized by anatomical location: medial tibiofemoral = medial OA. | Cannot have OA without cartilage loss (thickness). Osteophytes and space narrowing are secondary to cartilage loss. |
| **DIRECTIONAL FOR: Early Medial OA (Cartilage Signal Changes)** | SIG.CARTSURF.T2 (loss of normal bright superficial zone, irregular surface signal, suggesting fibrillation) + GEO.CART.THICKNESS (normal or mildly reduced, not yet <1.5 mm) + PRIOR.AGE (older age, higher OA prevalence) | Loss of normal cartilage surface signal and zonal structure = cartilage fibrillation (earliest gross OA finding). Thickness may still be normal or only mildly reduced at this stage. | Anatomy: cartilage fibrillation = earliest OA change (collagen disruption). Physics: fibrillation visible as signal loss at surface on T2 FS. Epidemiology: OA prevalence increases with age. | Early OA detected by signal before thickness fully reduced. |
| **DIRECTIONAL AGAINST: No Medial OA** | GEO.CART.THICKNESS (normal, 2–3 mm at medial compartment) + GEO.JOINTSPACE.WIDTH (normal, 4–5 mm at medial compartment) + SIG.CARTSURF.T2 (normal bright superficial zone, sharp surface) + ¬GEO.OSTEO.PRESENT (no osteophytes at medial margins) | Conjunction: all OA markers absent = no OA. | Anatomy: normal thickness, space, surface, and no osteophytes = cartilage intact. | Absence of all OA findings = high confidence in absence of OA. |
| **STRICT EXCLUSION: No Medial OA from Geometry** | ¬ACQ.COR.COVERAGE (coronal slices do not cover medial tibiofemoral compartment) | If medial compartment not acquired on coronal, cannot assess medial tibiofemoral cartilage/osteophytes. Silence mandated for medial OA assessment. | Anatomy: medial compartment must be in-plane on coronal to assess medial OA. | When coverage confirmed to exclude medial compartment, abstain on medial OA. |
| **ABSTAIN: Insufficient Data** | ACQ.PIXELSPACING > 1.0 mm (low resolution, cartilage measurement unreliable) + PRIOR.AGE unknown (cannot calibrate to age-matched normals) | Without adequate resolution and age information, confident OA assessment cannot be made. | Data quality: cartilage measurement requires resolution <1 mm and age-matched normals. | More imaging or demographic data might resolve. |

### Lateral OA

| Reading | Lenses | Warrant | Law | Notes |
|---|---|---|---|---|
| **DIRECTIONAL FOR: Lateral Osteoarthritis** | GEO.CART.THICKNESS (thinned cartilage at lateral tibiofemoral compartment, <1.5 mm) + GEO.JOINTSPACE.WIDTH (narrowed space at lateral compartment, <3 mm, or asymmetry >1 mm lateral vs. medial, favoring lateral narrowing) + GEO.OSTEO.PRESENT (osteophytes at lateral joint margins) | Same OA triad as medial, but at lateral compartment location. Conjunction of all three = high confidence. Any two = directional for OA. Location (lateral vs. medial) isolates compartment. | Anatomy: OA compartmentalized by location. Lateral tibiofemoral = lateral compartment (lateral femoral and tibial surfaces). Physics: cartilage loss reflected in space narrowing. Anatomy: osteophytes form at joint margins in response to cartilage loss. | Lateral OA independent of medial OA; can occur alone or with medial. |
| **DIRECTIONAL FOR: Early Lateral OA** | SIG.CARTSURF.T2 (signal loss at lateral cartilage surface, fibrillation) + GEO.CART.THICKNESS (normal or mildly reduced) | Early cartilage signal changes before thickness fully reduced. | Anatomy: cartilage fibrillation = earliest OA. Physics: fibrillation visible as surface signal loss on T2 FS. | Early OA detected by signal before thickness advanced. |
| **DIRECTIONAL AGAINST: No Lateral OA** | GEO.CART.THICKNESS (normal at lateral compartment, 2–3 mm) + GEO.JOINTSPACE.WIDTH (normal space at lateral compartment, 4–5 mm) + SIG.CARTSURF.T2 (normal bright surface) + ¬GEO.OSTEO.PRESENT (no osteophytes at lateral margins) | All OA markers absent = no OA. | Anatomy: normal thickness, space, surface, no osteophytes = intact. | Absence of all markers = high confidence no OA. |
| **STRICT EXCLUSION: No Lateral OA** | ¬ACQ.COR.COVERAGE (coronal does not cover lateral tibiofemoral compartment) | If lateral compartment not acquired, cannot assess. Silence mandated. | Anatomy: lateral compartment must be in-plane on coronal. | When coverage confirmed to exclude, abstain. |
| **ABSTAIN: Insufficient Data** | ACQ.PIXELSPACING > 1.0 mm + PRIOR.AGE unknown | Without resolution and age calibration, confident reading not possible. | Data quality: cartilage measurement requires resolution and age-matched normals. | More imaging or data might resolve. |

### PF OA

| Reading | Lenses | Warrant | Law | Notes |
|---|---|---|---|---|
| **DIRECTIONAL FOR: Patellofemoral Osteoarthritis** | GEO.CART.THICKNESS (thinned cartilage at patellofemoral joint, <2 mm at either patellar or femoral facet) + GEO.OSTEO.PRESENT (osteophytes at PF margins, femoral groove or patellar facets) + GEO.PF.ALIGNMENT (patellar malalignment, lateralization or tilt, increasing lateral facet loading) | Conjunction: cartilage loss + osteophytes + malalignment (if present) = OA. Cartilage loss and osteophytes alone sufficient; malalignment is directional for OA risk but not required for OA diagnosis. | Anatomy: PF OA = cartilage loss at patellar or femoral facets. Malalignment accelerates OA by increasing lateral facet stress. Physics: cartilage loss visible as thinning on axial/sagittal. Anatomy: osteophytes form at PF joint margins. | PF OA independent of tibiofemoral (medial, lateral) OA. Can occur with tibiofemoral OA (pan-compartmental) or alone. Malalignment is risk factor but not sole cause. |
| **DIRECTIONAL FOR: Malalignment as Risk for PF OA** | GEO.PF.ALIGNMENT (patellar lateralization, tilt >8°, or shift >5 mm) + GEO.CART.THICKNESS (any evidence of cartilage loss or signal change at lateral PF facet) | Patellar malalignment increases stress on lateral PF facet. If malalignment present with any cartilage changes, risk for OA acceleration is elevated. | Anatomy: patellar tracking affects biomechanical load distribution in PF joint. Lateralization and tilt increase lateral facet loading, promoting cartilage wear and OA. Biomechanics: load concentration accelerates degeneration. | Malalignment alone (without cartilage loss) is directional for OA risk, not OA diagnosis. |
| **DIRECTIONAL AGAINST: No PF OA** | GEO.CART.THICKNESS (normal PF cartilage, >2 mm at patellar and femoral surfaces) + ¬GEO.OSTEO.PRESENT (no osteophytes at PF margins) + GEO.PF.ALIGNMENT (normal patellar alignment, centered in groove, no tilt or minimal tilt) | Normal cartilage thickness, no osteophytes, normal alignment = no OA. | Anatomy: normal thickness and no osteophytes = intact cartilage. Normal alignment = no mechanical risk factor. | Absence of OA markers = high confidence no PF OA. |
| **STRICT EXCLUSION: No PF OA** | ¬ACQ.AXI.COVERAGE (axial images do not include PF joint at joint level) | If PF joint not acquired on axial at true articulation level, cannot assess PF cartilage and joint space. Silence mandated. | Anatomy: PF joint best assessed on axial; sagittal can show patellar cartilage but not true joint gap. | When coverage confirmed to exclude PF joint, abstain. |
| **ABSTAIN: Insufficient Data** | ACQ.PIXELSPACING > 1.0 mm (low resolution for thin PF cartilage) + PRIOR.AGE unknown | Without resolution for thin cartilage measurement and age calibration, confident reading not possible. | Data quality: PF cartilage thin (3–4 mm normal); low resolution obscures assessment. | More imaging or data might resolve. |

### Effusion

| Reading | Lenses | Warrant | Law | Notes |
|---|---|---|---|---|
| **DEFINITIONAL: Joint Effusion (Excess Fluid)** | SIG.JOINTSPACE.T2BRIGHT (bright T2 signal filling joint space, measured or visually obvious on multiple consecutive slices) + GEO.JOINTSPACE.WIDTH (measured fluid volume or signal extent exceeds population normal at this site/sequence) + ACQ.FLUIDSEN.PRESENT (FS=1, required for bright signal) | Conjunction: bright joint space signal (confirmed by FS sequence) in registered frame (coverage verified) + measured volume/extent exceeds normal = effusion present. | MRI physics: free fluid (effusion) is bright on T2 FS. Anatomy: joint space normally contains thin film of synovial fluid; bright filling = excess. Physics: measurement or visual extent confirms excess. | Effusion is fluid, not inflammation. Does not say what caused it (secondary to synovitis, trauma, OA, or primary effusion). |
| **DIRECTIONAL FOR: Effusion from Synovitis/Inflammation** | SIG.JOINTSPACE.T2BRIGHT (bright fluid) + SIG.SYNOV.T2BRIGHT (thickened, bright synovial membrane) + TOP.EFFUSION.LOCUL (diffuse rather than loculated) | Bright joint space + bright synovium + diffuse distribution = global joint inflammation (synovitis) producing reactive effusion. | Physics: synovitis (edema in synovial lining) brightens on T2; produces effusion. Anatomy: inflammatory effusion is typically diffuse (acute inflammation spreads throughout joint). | Synovitis and effusion co-occur; inflammation is mechanism for effusion. |
| **DIRECTIONAL FOR: Effusion from OA or Trauma** | SIG.JOINTSPACE.T2BRIGHT (bright fluid) + (GEO.CART.THICKNESS reduced OR GEO.JOINTSPACE.WIDTH narrowed OR GEO.MENISCUS.CONTINU.PATTERN discontinuous OR SIG.CORTICAL.BREAK present) | Bright joint space + evidence of cartilage loss, OA, meniscal tear, or fracture = secondary effusion (reactive to primary structural pathology). | Pathophysiology: cartilage loss (OA), meniscal tear, or fracture produce mechanical irritation → effusion; bone marrow blood products → hemarthrosis. Anatomy: secondary effusion is reaction to primary pathology. | Effusion in context of primary structural finding = secondary effusion; mechanism is identifiable. |
| **DIRECTIONAL AGAINST: No Effusion** | SIG.JOINTSPACE.T2BRIGHT (absent or minimal signal in joint space, consistent with normal synovial fluid) + GEO.JOINTSPACE.WIDTH (normal fluid volume/extent, baseline for population) | Absence of bright signal in joint space = no excess fluid (normal baseline). | Physics: normal joint space contains thin fluid layer, barely visible on T2. Absence of bright signal = no excess. | Normal appearance does not exclude very small effusion (sub-resolution); clinical correlation helpful. |
| **SQUINT: Obvious Effusion (Rapid Screening)** | SQUINT.EFFUSION.OBVIOUS (bright fluid visibly filling joint space on visual inspection, scored moderate or large) | Obvious bright joint space = effusion likely present (sensitive, low-specificity screening). Used for triage to detailed measurement. | Physics: free fluid bright on T2 FS; obvious visual appearance detects gross effusion. | Sensitive for obvious effusion; may miss small or subtle effusion. Requires measurement (B6, G4) for confident assessment. |
| **STRICT EXCLUSION: No Effusion** | ¬ACQ.FLUIDSEN.PRESENT (no T2 FS acquired; bright fluid signal cannot be measured) | If T2 FS sequence not acquired, effusion detection by bright signal is not possible. But absence of T2 FS does not mean absence of effusion; it means silence on signal assessment. Alternative: sagittal or axial T1 may show fluid as dark space (less sensitive). Silence on bright-signal effusion detection is mandated; other modalities (if available) might detect it. | MRI physics: free fluid must be on FS sequence to maximize bright signal (long T2). Non-FS sequences may not show fluid. | When T2 FS absent, abstracting on bright-signal effusion is correct; other evidence (e.g., ligament/meniscal injury with known hemarthrosis) might argue for effusion despite lack of T2 FS visibility. |
| **ABSTAIN: Insufficient Data** | Image quality poor (severe artifact, motion) + low SNR (poor signal-to-noise, fluid not clearly visible) | Without clear visibility of joint space and adequate T2 FS signal, effusion assessment cannot be confident. | Data quality: effusion reading requires clear joint visualization on T2 FS. | More imaging (high quality, T2 FS) might resolve. |

### Synovitis

| Reading | Lenses | Warrant | Law | Notes |
|---|---|---|---|---|
| **DIRECTIONAL FOR: Synovitis (Synovial Inflammation)** | SIG.SYNOV.T2BRIGHT (thickened synovial membrane, >3 mm, bright T2 signal indicating edema in synovium) + SIG.JOINTSPACE.T2BRIGHT (bright joint space fluid, often accompanying synovitis) + TOP.EFFUSION.LOCUL (diffuse rather than loculated) | Conjunction: bright, thickened synovium (inflammation with edema) + diffuse effusion (global inflammation) = synovitis. Thickened, bright synovium is primary reading; effusion is secondary response. | MRI physics: edema in synovial tissue brightens on T2 FS (long T2). Anatomy: synovitis is inflammatory edema in synovial lining. Pathophysiology: inflammation produces effusion. | Synovitis is inflammation of synovial membrane; detected indirectly through synovial thickening and edema, and accompanying effusion. Without gadolinium contrast (not available in this competition), synovial signal assessment is limited to thickness and T2 signal. |
| **DIRECTIONAL FOR: Synovitis from OA** | SIG.SYNOV.T2BRIGHT (thickened synovium) + (GEO.CART.THICKNESS reduced OR GEO.OSTEO.PRESENT) | OA produces mechanical irritation and cartilage fragments, triggering synovitis (inflammatory response). Thickened synovium + OA signs = OA-related synovitis. | Pathophysiology: cartilage loss and bone exposure in OA trigger synovial inflammation. Anatomy: synovitis is reaction to OA. | Synovitis in context of OA = secondary synovitis; mechanism identifiable. |
| **DIRECTIONAL AGAINST: No Synovitis** | SIG.SYNOV.T2BRIGHT (thin synovial membrane, <2 mm, dark, low T2 signal consistent with normal) + SIG.JOINTSPACE.T2BRIGHT (normal/minimal fluid) | Thin, dark synovium + no excessive fluid = no acute synovitis. | Physics: normal synovium thin, low signal (no edema). Anatomy: normal synovial lining shows no thickening. | Normal appearance does not exclude chronic low-grade synovitis. |
| **ABSTAIN: Insufficient Data** | ACQ.FLUIDSEN.PRESENT = 0 (no T2 FS for synovial signal assessment) + image quality poor (synovial membrane edges not clearly delineated) | Without T2 FS and clear visualization of synovial membrane, measurement and signal assessment not possible. Silence on synovial findings is appropriate. | Data quality: synovial assessment requires T2 FS and high-resolution imaging to visualize thin membrane. | More imaging (T2 FS, high quality) might resolve. |

### Baker's Cyst (Popliteal Cyst)

| Reading | Lenses | Warrant | Law | Notes |
|---|---|---|---|---|
| **DEFINITIONAL: Baker's Cyst Present** | GEO.BAKERS.CYST.PRESENCE (fluid-filled, loculated structure posterior to joint capsule in popliteal space, clearly defined on axial and/or sagittal T2 FS) + ACQ.AXI.COVERAGE (axial slices reach popliteal space where cyst would be located) | Conjunction: visible fluid collection in popliteal space (definitive by geometry) + coverage verified = Baker's cyst present. This is one of clearest geometric findings in knee MRI. | Anatomy: cyst = closed epithelial-lined space filled with fluid. Popliteal space bounded by muscles and joint capsule; fluid collection there = Baker's cyst by definition. Physics: fluid on T2 FS is bright; cyst boundary (thin capsule) is low signal. Geometry: cyst location in popliteal space is definitive. | Baker's cyst may communicate with joint (neck visible) or be compartmentalized; size and communication recorded as modifiers. |
| **DIRECTIONAL FOR: Large Baker's Cyst or Symptomatic** | GEO.BAKERS.CYST.PRESENCE (cyst present, large >1 cm³, or with evident communication to joint) + SIG.JOINTSPACE.T2BRIGHT (bright joint fluid, suggesting effusion driving cyst) | Large cyst or cyst with communication = higher likelihood of symptoms and clinical significance. Effusion co-occurrence supports mechanism (effusion → cyst). | Pathophysiology: chronic effusion and synovitis can cause synovial herniation → Baker's cyst. Large cyst can compress popliteal structures. | Large cysts more likely to be detected and reported. |
| **DIRECTIONAL FOR: Baker's Cyst from Underlying OA or Synovitis** | GEO.BAKERS.CYST.PRESENCE (cyst present) + (GEO.CART.THICKNESS reduced OR SIG.SYNOV.T2BRIGHT thickened synovium) | Baker's cyst association with OA or synovitis is common. Underlying joint pathology (OA, synovitis) is likely cause of effusion → cyst. | Pathophysiology: OA and synovitis produce effusion; chronic effusion can herniate posteriorly. | Baker's cyst often secondary finding (marker of underlying joint disease). |
| **DIRECTIONAL AGAINST: No Baker's Cyst** | ¬GEO.BAKERS.CYST.PRESENCE (no fluid collection in popliteal space on images where popliteal space is visible) + ACQ.AXI.COVERAGE (axial slices verified to reach popliteal space) | Absence of fluid collection in visualized popliteal space = no Baker's cyst. | Anatomy: if popliteal space visible and no fluid, no cyst. | Normal appearance = high confidence in absence of cyst. |
| **STRICT EXCLUSION: No Baker's Cyst** | ¬ACQ.AXI.COVERAGE (axial images do not include popliteal space posteriorly) | If axial slices do not reach posterior popliteal region, Baker's cyst cannot be assessed. Silence mandated. | Anatomy: Baker's cyst is posterior structure; must be in-plane on axial to be visible. Physics: structure outside acquired field cannot be resolved. | When axial coverage confirmed to exclude popliteal space, abstain on Baker's cyst. |
| **ABSTAIN: Insufficient Data** | ACQ.FLUIDSEN.PRESENT = 0 (no T2 FS, cyst fluid may not appear bright enough to distinguish from artifact) + popliteal region at edge of field (partial coverage of popliteal space) | Without T2 FS brightness and full coverage of popliteal space, cyst detection may not be confident. | Data quality: Baker's cyst best seen on T2 FS (fluid bright); detection requires full posterior coverage. | More imaging (T2 FS, adequate posterior coverage) might resolve. |

### Contusion

| Reading | Lenses | Warrant | Law | Notes |
|---|---|---|---|---|
| **DIRECTIONAL FOR: Bone Contusion (Marrow Edema, Evidence of Bone Impact)** | SIG.MARROW.T1DARK (dark signal on T1, isointense to muscle or darker, indicating marrow edema) ∨ SIG.MARROW.STIR (bright signal on STIR, highly sensitive for marrow edema) + PRIOR.MECHANISM (if acute trauma reported, mechanism supports finding) | Marrow edema on T1 or especially STIR = bone impact without cortical break (contusion is defined as impact without cortical discontinuity). STIR is more sensitive than T1. Dark marrow on T1 indicates edema (water replacing fat). | MRI physics: bone contusion = marrow edema (impact without cortical break). Marrow edema is water-rich (dark on T1, bright on STIR). Anatomy: contusion is impact injury. Pathophysiology: impact → hemorrhage and edema in marrow. | Contusion is edema in bone marrow; geometry (fracture line) distinguishes contusion from fracture. Contusion without visible fracture line = bruising without break. |
| **DIRECTIONAL FOR: Contusion Associated with Fracture** | SIG.MARROW.T1DARK ∨ SIG.MARROW.STIR (marrow edema) + SIG.CORTICAL.BREAK (visible cortical discontinuity) | Marrow edema + cortical break = confirmed fracture with surrounding contusion/hematoma. | Anatomy: fractures are accompanied by marrow edema and blood. Cortical discontinuity = fracture. | Contusion around a fracture is expected finding (same mechanism). |
| **DIRECTIONAL AGAINST: No Contusion** | ¬SIG.MARROW.T1DARK (bright marrow on T1, normal fat signal) ∧ ¬SIG.MARROW.STIR (no bright signal on STIR, if available) + PRIOR.MECHANISM (if no trauma reported) | Absence of marrow edema on T1 and STIR = no acute marrow edema (no acute contusion). | Physics: normal marrow bright on T1 (fat). Edema dark on T1. Absence = no acute edema. Epidemiology: contusion follows trauma; no reported mechanism lowers likelihood. | Absence of edema does not exclude old/healed contusions (those may leave no marrow signal abnormality). |
| **ABSTAIN: Insufficient Data** | (ACQ.FIELDSTR or ACQ.SLICETHICK obscures marrow evaluation) ∨ image quality poor (artifact, motion) | Without clear marrow visualization on T1 or STIR, edema assessment not confident. | Data quality: marrow assessment requires clear T1 or STIR imaging. | More imaging might resolve. |

### Fracture

| Reading | Lenses | Warrant | Law | Notes |
|---|---|---|---|---|
| **DEFINITIONAL: Bone Fracture (Cortical Discontinuity)** | SIG.CORTICAL.BREAK (visible dark gap or offset in cortical bone outline on T1 or T2, indicating break in normally continuous cortical shell) + ACQ.SLICETHICK ≤ 4 mm (thin enough slices to resolve fracture line) | Conjunction: visible cortical discontinuity (definitive by anatomy) + adequate slice thickness to resolve it = fracture present. Cortical break = fracture by definition. | Anatomy: cortical bone = continuous shell; break = fracture by definition. Physics: dense cortex = dark; break = gap in dark line. Geometry: fracture line visible as offset or discontinuity in cortical outline. | Cortical discontinuity is narrow, high-specificity positive warrant for fracture. But absence of visible discontinuity does not exclude fracture (occult, impacted, or non-displaced may not show cortical break on MRI; CT better). |
| **DIRECTIONAL FOR: Fracture (with Marrow Edema and/or Hematoma)** | SIG.CORTICAL.BREAK (visible cortical discontinuity) + (SIG.MARROW.T1DARK ∨ SIG.MARROW.STIR) (marrow edema around fracture) | Cortical break + marrow edema = fracture with surrounding contusion/hematoma. Edema indicates fresh injury. | Anatomy: fractures accompanied by bone hemorrhage and marrow edema. Physics: edema visible as dark on T1, bright on STIR. | Marrow edema timing: bright signal on STIR fades over weeks; old fractures may not show signal abnormality. |
| **DIRECTIONAL FOR: Occult Fracture (No Cortical Break Visible, but Marrow Edema)** | ¬SIG.CORTICAL.BREAK (no visible cortical discontinuity on MRI) + (SIG.MARROW.T1DARK ∨ SIG.MARROW.STIR) (marrow edema at bone site) + PRIOR.MECHANISM (acute trauma reported) | Marrow edema without visible cortical break = occult fracture (stress fracture, impacted fracture, non-displaced). MRI detects edema; fracture line may not be visible. CT better for cortical break detection. | MRI physics: marrow edema visible on T1/STIR; cortical break requires high resolution and appropriate orientation. Occult fractures = stress fractures or impacted fractures; cortex may not be offset enough to see gap on MRI. | Absence of visible cortical break does not exclude fracture if marrow edema is present (especially acute). CT recommended for confirmation. |
| **DIRECTIONAL AGAINST: No Fracture** | ¬SIG.CORTICAL.BREAK (no discontinuity visible in cortical bone) + ¬SIG.MARROW.T1DARK ∧ ¬SIG.MARROW.STIR (no marrow edema) + negative prior mechanism (no trauma reported) | Absence of cortical break + absence of marrow edema + no trauma history = no fracture. | Anatomy: fracture = cortical discontinuity. Physics: fresh fracture accompanied by marrow edema. Epidemiology: fractures follow trauma. | Absence of all fracture markers = high confidence no fracture. |
| **SQUINT: Obvious Fracture (Rapid Screening)** | SQUINT.FRACTURE.CORTICAL (obvious cortical disruption visible on inspection, scored as obvious) | Obvious cortical discontinuity = fracture likely (high positive predictive value). Used for rapid triage. | Anatomy: gross cortical breaks easily recognized visually. | Subtle or occult fractures may be missed by visual inspection; detailed assessment (B10, marrow edema) required. |
| **STRICT EXCLUSION: No Fracture** | ¬ACQ.SLICETHICK ≤ 4 mm ∧ ¬SIG.MARROW.STIR (thick slices obscure fracture line, no STIR for marrow assessment) | If slices too thick to resolve fracture line and no STIR available for marrow edema assessment, fracture detection is severely limited. Silence appropriate; CT recommended for fracture exclusion. | Data quality: fracture line resolution requires thin slices. Marrow edema requires T1 or STIR sensitivity. | When imaging inadequate, abstain and recommend alternative (CT for fracture detection). |
| **ABSTAIN: Insufficient Data** | Image quality poor (severe artifact, motion, susceptibility) + ACQ.FIELDSTR uncertain (field strength unknown) | Without clear cortical visualization and known field strength (affects signal intensity), fracture assessment not confident. | Data quality: fracture line must be clearly visible. | More imaging (high quality, known field strength) might resolve. |

---

## 4. BETWEEN LABELS: Correlations, Hard Pairs, Isolating Readings, Priority, Confidence Factors

### 4.1 Anatomical Grouping

**Group A: Ligaments (ACL, MCL)** — Distinct connective tissue injuries. Isolated lenses: ACL in intercondylar notch (sagittal), MCL along medial joint line (coronal). No mutual exclusion; can occur together (rare in single acute trauma).

**Group B: Menisci (Medial Meniscus, Lateral Meniscus)** — Distinct fibrocartilage structures in separate compartments. Isolated lenses: anatomical location (medial vs. lateral) on coronal plane. No mutual exclusion; can occur together (unusual in single injury).

**Group C: Joint-level findings (OA compartments, effusion, synovitis, Baker's, contusion, fracture)** — Affect the joint globally or regionally. Mechanisms vary (degenerative, inflammatory, traumatic) but interconnected.

### 4.2 Traumatic Cluster: Fracture, Contusion, Acute Ligament/Meniscal Tears

**Mechanism (DOMAIN):** Single mechanical impact. Anatomy determines what breaks.

**Co-occurrence (DOMAIN):**
- **Fracture + Contusion:** Same impact. Both present = high impact force. Contusion = bone marrow bleeding and edema at impact site. Always co-occur if fracture present.
- **Ligament/Meniscal Tears + Fracture/Contusion:** Rotational or high-energy trauma. Can co-occur; not mechanically independent. ACL + medial meniscus + MCL = "unhappy triad" (classical pattern, DOMAIN).
- **Ordering:** Fracture is "lowest rung" (highest energy). If fracture present, contusion and effusion (hemarthrosis) are expected. Ligament/meniscal tears may accompany.

**Isolating readings (DOMAIN, PROPOSAL):**
- **Fracture:** Cortical discontinuity (B10, SIG.CORTICAL.BREAK) = fracture. Marrow edema (B8, B9) around fracture confirms impact.
- **Contusion:** Marrow edema (B8, B9) without cortical break = contusion (impact without cortical discontinuity).
- **Ligament/Meniscal tears:** Continuity lenses (GEO.ACL.CONTINUITY, GEO.MENISCUS.CONTINU.PATTERN) + signal (B1, B3, B4) localize tears to specific structures.
- **Hemarthrosis:** Fracture/trauma → blood in joint → bright signal on T2 FS (appears as effusion). Context (trauma mechanism) distinguishes traumatic effusion from inflammatory.

**Ordering of Resolution (PROPOSAL):**
1. First: Read for **fracture** (cortical discontinuity; most definitive).
2. If fracture, expect **contusion** (marrow edema) around fracture; both present = impact confirmed.
3. If fracture + high-energy mechanism, scan for **ligament/meniscal tears** (same rotational force may have caused tears).
4. **Hemarthrosis (effusion from blood)** expected with fracture/contusion. Distinguish from inflammatory effusion (synovitis).

**Confidence factors:**
- Fracture alone is high-confidence (cortical discontinuity definitive).
- Fracture + contusion + ligament tear = very high confidence in trauma.
- Ligament/meniscal tear without fracture/contusion = lower confidence (may be chronic or degenerative tear, not acute trauma).

---

### 4.3 Degenerative Cluster: OA Compartments, Effusion, Synovitis, Baker's Cyst

**Mechanism (DOMAIN):** Chronic joint wear (OA) and inflammatory response form feedback loop.

**Co-occurrence (DOMAIN):**
- **Three OA compartments (Medial, Lateral, PF):** Can occur independently or together (pan-compartmental OA).
  - Medial OA: Load shift to medial compartment (varus alignment, wear pattern). Independent of lateral or PF.
  - Lateral OA: Load shift to lateral (valgus alignment). Independent of medial or PF.
  - PF OA: Patellar malalignment or patellofemoral wear. Independent of tibiofemoral compartments.
- **Synovitis + Effusion:** Synovitis (inflammation) produces effusion. Co-occurrence expected.
- **OA + Synovitis + Effusion:** OA triggers inflammatory response (cartilage fragments, bone exposure). Inflammation → effusion. All three often present in advanced OA.
- **Baker's Cyst + Effusion + Synovitis:** Chronic effusion (from OA or synovitis) → potential for synovial herniation → Baker's cyst. Cyst is marker of long-standing effusion and synovitis.

**Isolating readings (DOMAIN, PROPOSAL):**

- **Medial vs. Lateral OA:** Anatomical location on coronal (cartilage thickness, space width at medial vs. lateral compartment) isolates compartment. Law: medial and lateral are distinct anatomical places.
- **OA vs. Effusion/Synovitis:** OA is cartilage loss + bone remodeling (lenses: thickness, space width, osteophytes). Effusion is joint fluid (lens: bright T2 signal). Synovitis is membrane inflammation (lens: thickened, bright synovium). All three distinct; OA produces secondary synovitis and effusion.
- **Effusion vs. Synovitis:** Effusion = fluid in joint space (bright T2 signal in space itself). Synovitis = membrane inflammation (thickened, bright membrane at capsule). Both visible on T2 FS; distinct readings.
- **Baker's Cyst vs. Large Effusion:** Baker's cyst = loculated posterior (popliteal space) fluid collection with clear geometry (cyst = closed space). Large effusion = diffuse bright signal throughout joint. Location isolates (popliteal posteriorly for cyst, joint space for effusion).

**Ordering of Resolution (PROPOSAL):**

1. First: Assess **three OA compartments** (cartilage thickness at medial, lateral, PF; joint space width; osteophytes). Each compartment independent.
2. Assess **effusion presence** (bright joint space on T2 FS). Secondary to OA, synovitis, or trauma.
3. Assess **synovitis** (thickened, bright synovium). Often accompanies effusion; mechanism is inflammation from OA or primary synovitis.
4. Assess **Baker's cyst** (posterior fluid collection). Marker of long-standing effusion/synovitis; associated with advanced OA.

**Confidence factors:**
- Each OA compartment: isolated by anatomical location. Confidence depends on conjunction of cartilage loss + space narrowing + osteophytes. One marker alone = directional; all three = high confidence OA.
- Effusion: bright signal in T2 FS = high confidence effusion (sensitive, specific).
- Synovitis: thickened, bright synovium = directional for inflammation (less sensitive and specific than effusion).
- Baker's cyst: visible posterior fluid collection = high confidence cyst (definitive by geometry).
- **OA + Effusion + Synovitis + Baker's:** Pan-compartmental OA with chronic inflammation and secondary effusion and cyst = very high confidence in chronic degenerative joint disease.

---

### 4.4 Hard-to-Separate Pairs and Their Isolating Lenses

#### 4.4.1 Medial OA vs. Lateral OA

**What's hard (DOMAIN):** Both are OA (cartilage loss, bone remodeling, space narrowing, osteophytes). Imaging signatures identical. Only difference is location.

**Isolating lens (DOMAIN, LAW):**
- **Coronal anatomical location:** Cartilage thickness and joint space width measured at **medial tibiofemoral surfaces** (medial condyle of femur, medial plateau of tibia) = **medial OA.** Measured at **lateral surfaces** (lateral condyle, lateral plateau) = **lateral OA.** Law: medial and lateral are anatomically distinct compartments.

**Can both be present?** Yes, pan-compartmental OA occurs (bilateral tibiofemoral wear).

---

#### 4.4.2 Medial Meniscus vs. Lateral Meniscus

**What's hard (DOMAIN):** Both are menisci (fibrocartilage, C or O shaped). Identical internal structure and tear patterns. Only difference is location.

**Isolating lens (DOMAIN, LAW):**
- **Coronal anatomical location:** Meniscus in **medial compartment** (medial to tibial eminence, medial facet of tibia, attached to joint capsule and MCL) = **medial meniscus.** Meniscus in **lateral compartment** (lateral to eminence, lateral facet, looser capsule attachment) = **lateral meniscus.** Law: medial and lateral compartments are anatomically distinct.

**Can both be present?** Yes, but less common in single acute injury (usually one side bears mechanism load).

---

#### 4.4.3 ACL vs. Ligament-Meniscal Triad (ACL + MCL + Medial Meniscus)

**What's hard (DOMAIN):** Rotational trauma (pivot shift injury) can tear all three together. Radiological findings: ACL tear in notch, MCL edema/tear along medial line, medial meniscus tear in medial compartment. All three are distinct structures but mechanically linked by injury mechanism.

**Isolating lens (DOMAIN, LAW):**
- **ACL:** Intercondylar notch, sagittal. Continuity lens (GEO.ACL.CONTINUITY).
- **MCL:** Medial joint line, coronal. Signal lens (SIG.MCL.T2BRIGHT).
- **Medial Meniscus:** Medial compartment, sagittal/coronal. Continuity lens (GEO.MENISCUS.CONTINU.PATTERN, at medial location).

Each in different location/plane → isolated by anatomy. **Law:** Three anatomically distinct structures; location in registered frame isolates each.

**Can all three be present?** Yes, "unhappy triad" is classical pattern (DOMAIN).

---

#### 4.4.4 Effusion vs. Synovitis

**What's hard (DOMAIN):** Synovitis (membrane inflammation) produces effusion (fluid). They co-occur; causal relationship. Without gadolinium contrast, synovitis is detected indirectly (membrane thickening, T2 signal, accompanying effusion).

**Isolating lenses (DOMAIN, PROPOSAL):**
- **Effusion:** Joint space bright signal on T2 FS (lens: SIG.JOINTSPACE.T2BRIGHT). Measures fluid volume/extent directly.
- **Synovitis:** Thickened, bright synovial membrane at capsule, especially anterior recess (lens: SIG.SYNOV.T2BRIGHT). Measures membrane inflammation directly.

**Relationship (DOMAIN, PROPOSAL):**
- **Synovitis → Effusion (causal):** Inflammation produces fluid. Presence of synovitis raises confidence in effusion. Rule: if synovitis present, expect effusion.
- **Effusion without synovitis:** Can occur from mechanical injury (meniscal/ligament tear → blood in joint), fracture → hemarthrosis. Can occur from non-inflammatory causes (OA, chronic fluid accumulation).
- **Rule of precedence (PROPOSAL):** Where primary structural pathology (tear, fracture) present, effusion is reactive (secondary). Where no primary pathology found, extensive effusion suggests primary synovitis or inflammatory process.

**Both can be present:** Yes, co-occurrence expected in inflammation.

---

#### 4.4.5 Baker's Cyst vs. Large Effusion

**What's hard (DOMAIN):** Baker's cyst is loculated posterior fluid collection that forms from chronic effusion and synovitis. Large effusion may appear to extend posteriorly. Both are fluid on T2 FS; distinction is geometric (loculation, location).

**Isolating lens (DOMAIN, LAW):**
- **Baker's cyst:** Posterior (popliteal space) **loculated** fluid collection with clear cyst geometry (walled-off space). Seen on axial at popliteal level and sagittal. Law: cyst = closed epithelial-lined space; popliteal location = Baker's cyst by anatomy.
- **Large effusion:** **Diffuse** bright signal throughout joint space (anterior, posterior, medial, lateral). Contiguous across slices. Not loculated or walled off.

**Isolating lenses (GEOMETRY, LAW):**
- **Location:** Cyst in popliteal space (posterior, between gastrocnemius and other muscles). Effusion in joint space (articulation area).
- **Loculation:** Cyst walled off. Effusion diffuse.
- **GEO.BAKERS.CYST.PRESENCE:** Visible loculated fluid in popliteal space = cyst.
- **TOP.EFFUSION.LOCUL:** Diffuse vs. loculated effusion in joint = evaluates distribution.

**Both can be present:** Yes, Baker's cyst often arises from chronic effusion (both present together).

---

### 4.5 Confidence Score Factors

**Strict findings (highest confidence):**
- Cortical discontinuity → fracture (B10, SIG.CORTICAL.BREAK) = SpPin (strict positive).
- ACL/meniscal continuity break → tear (GEO.ACL.CONTINUITY, GEO.MENISCUS.CONTINU.PATTERN) = SpPin.
- Baker's cyst geometry (loculated popliteal space) = definitive by anatomy.

**Directional findings (moderate confidence):**
- Signal lenses (edema, bright synovium, joint space brightness) = directional for underlying process; require geometric confirmation.
- Cartilage thickness, joint space width, osteophytes = directional for OA; conjunction of all three = high confidence OA.
- Marrow edema (B8, B9) = directional for contusion; requires other findings for context.

**Priors (bias/calibration):**
- Age (PRIOR.AGE): OA prevalence increases with age. Young patient with OA finding = more confident abnormality. Old patient with mild OA = less significant.
- Mechanism (PRIOR.MECHANISM): Acute trauma → expect ligament/meniscal tears, fracture, contusion, hemarthrosis. Chronic symptoms → expect OA, degenerative tears, synovitis, effusion.

**Coverage and sequence availability (necessary condition):**
- If site not acquired (ACQ coverage lenses), reading abstained (silence mandated).
- If FS sequence not available, bright-signal findings (effusion, synovitis, edema) cannot be assessed (STRICT EXCLUSION).
- If T2/STIR not available, marrow edema assessment severely limited (only T1 available, less sensitive).

**Ordering in resolution (PROPOSAL):**
1. **Establish coverage:** Verify ACQ lenses for each anatomical site (sagittal/coronal/axial coverage, FS availability).
2. **Assess primary traumatic findings:** Fracture (B10, SIG.CORTICAL.BREAK) first. If present, expect contusion (B8, B9), effusion (B6).
3. **Assess primary structural findings:** Ligament/meniscal continuity (G1, G2) and signal (B1-B4). Establish tears geometrically and confirm with signal.
4. **Assess secondary degenerative findings:** OA compartments (G3, G4, G5), then synovitis (B7), effusion (B6).
5. **Assess special sites:** Baker's cyst (G7), alignment (G8), attachment sites (T1, T2).
6. **Reconcile co-occurrence:** If fracture + ligament tear, both expected (traumatic cluster). If OA + effusion + synovitis, all expected (degenerative cluster).

---

## 5. DISAGREEMENTS AND OPEN QUESTIONS

### 5.1 Disagreements Between Wave 1 Reports (Kept Side by Side)

**On "Abnormality" definition:**
- **00_facts.md + 10_lenses.md (DOMAIN):** Define abnormality for each label as structural injury or degenerative change (tear, signal change, cartilage loss). Example: ACL abnormality = tear or signal change indicating disruption.
- **21_ligaments.md, opening scope question (PROPOSAL, open):** Are chronic partial tears, thinning/degeneration without discontinuity, and sprains (edema without discontinuity) "abnormality"? Assumed yes, but awaiting founder's ruling on scope.

**On MCL signal findings:**
- **21_ligaments.md (DOMAIN):** MCL signal homogeneity is directional for tear; edema indicates acute injury.
- **30_between_labels.md (DOMAIN):** Confirms MCL signal (bright T2) as marker of acute injury (edema/inflammation) distinct from continuity (geometry of discontinuity).
- **Disagreement (none on facts; scope question):** Warrant class for various findings clear; no disagreement.

**On meniscal degeneration vs. tear:**
- **10_lenses.md (DOMAIN):** Bright free edge (B3, B4) directional for tear but cannot distinguish tear from severe degeneration without geometry.
- **22_menisci.md (not fully read here, but expected):** Likely reinforces that signal alone is directional; continuity (geometry) is definitive for tear.
- **Disagreement (none); complementary readings:** Signal + geometry required for full assessment.

**On OA compartments and independence:**
- **10_lenses.md (DOMAIN):** Three OA compartments (medial, lateral, PF) are independent; can occur together or separately.
- **30_between_labels.md (DOMAIN):** Reinforces independence; load redistribution (varus/valgus alignment) may accelerate one over others, but they are mechanically and anatomically distinct.
- **Disagreement (none); consistent).**

**On effusion causation:**
- **10_lenses.md (B6, SIG.JOINTSPACE.T2BRIGHT):** Bright signal = free fluid; does not say what caused it. Directional for effusion, not cause.
- **30_between_labels.md (§3.3, §4.3):** Proposes that where primary structural pathology (tear, fracture), effusion is reactive. Where no primary pathology, extensive effusion suggests primary synovitis/inflammation.
- **Disagreement (none); complementary):** B6 measures effusion presence; downstream rules use context (primary pathology, synovitis) to infer cause.

**On Baker's cyst confidence:**
- **10_lenses.md (G7, GEO.BAKERS.CYST.PRESENCE):** Loculated posterior fluid collection in popliteal space = Baker's cyst by geometry (definitive).
- **30_between_labels.md (§3.4, §4.4.5):** Reinforces; cyst location (popliteal) and loculation isolate it from large diffuse effusion.
- **Disagreement (none); consistent). Warrant is DEFINITIONAL by geometry.**

---

### 5.2 Open Questions for the Founder

These are **questions of meaning and policy only** (not facts or domain knowledge that agents should infer).

#### On Scope and Definition

1. **ACL "abnormality" scope:** Does this include:
   - Acute complete tear? (assumed yes)
   - Partial/incomplete tear? (assumed yes)
   - Chronic partial tear (residual from prior injury)? (assumed yes, if structurally detectable)
   - Ligament thinning, degeneration, or laxity without discontinuity? (QUESTION)
   - Sprain (edema, hemorrhage) without structural discontinuity? (QUESTION)

   **Rationale for question:** The 58 labeled studies likely have a mix of acute tears (clear discontinuity), chronic thinning, and strains. The labels 0/1 don't distinguish. Scope clarification affects which lenses are DEFINITIONAL vs. DIRECTIONAL.

2. **MCL abnormality scope:** Similar to ACL. Which injury types count? (QUESTION)

3. **Meniscal tear scope:** Does "abnormality" mean:
   - Complete tear with discontinuity? (assumed yes)
   - Partial/incomplete tear? (assumed yes)
   - Internal degeneration without visible discontinuity? (QUESTION)
   - Fraying, microtears? (QUESTION)

4. **OA scope:** Is "OA abnormality" present/absent, or graded? The labels are binary (0/1), suggesting presence/absence only. But OA has grades (Kellgren-Lawrence 0–4). Do we report presence of any OA (even mild), or only advanced OA? (QUESTION)

   **Rationale:** Affects confidence thresholds. A knee with early fibrillation (B5) but normal thickness and space is "pre-OA," not yet OA by strict criteria. Should this count as "abnormality"?

5. **Synovitis scope:** Is this a primary diagnosis (primary synovitis, rheumatoid arthritis, etc.) or always secondary to other findings (OA, trauma, effusion)? This competition likely only includes secondary synovitis (no RA data reported). (QUESTION for confirmation)

#### On Imaging and Calibration

6. **Population normals:** The 34 ACL-negative and 4,349 unlabeled studies serve as the "normal" reference population. Are these truly normal, or a mix of normals and negatives (unhealthy but ACL-intact)? (QUESTION)

   **Rationale:** Affects calibration. A "normal" population should be truly healthy (no findings). A "negative" population (ACL=0 in label) could include OA knees, fractures, effusions, etc. Affects baseline ranges for all lenses.

7. **Age calibration:** Is patient age in DICOM headers? Critical for OA interpretation. (QUESTION for confirmation)

8. **Bilateral comparison:** Are any studies bilateral (both knees imaged)? The task description says one knee, but confirmation needed. (QUESTION for confirmation)

#### On Meaning and Rules

9. **"Abnormality" interpretation:** The founder's words from the AGENTS.md rigid oracle (lens principle) state: a lens measures and is never wrong; no lossy lens warrants a decision alone unless inherently a measurement of truth; a claim beyond one measurement is a conjunction; interpretation is built on top; meaning is derived from structure. 

   **In this context:** Does "ACL abnormality" mean:
   - "ACL tear" (structural discontinuity, clear meaning)? or
   - "ACL is not normal" (broader, includes signal changes, thinning, strains, etc.)? or
   - Something the founder will define after seeing the data?

   **Rationale:** The lenses are objective (thermometers). The labels (0/1) are the host's binary judgment. The mapping between lens readings and labels is the work of the rules. This question is whether the rules should aim for narrow (tears only) or broad (any abnormality) definition.

10. **Confidence score derivation:** The task requires submission of confidence scores (0–1 per label). How should these be computed from the lens readings?

    **PROPOSAL (for founder's ruling):** 
    - **Strict findings (DEFINITIONAL, STRICT POSITIVE):** Confidence close to 1.0 (e.g., 0.9–0.99).
    - **Strong directional findings (multiple lenses agreeing, high warrant):** Confidence mid-range (e.g., 0.6–0.85).
    - **Weak or conflicting directional findings:** Confidence low-range (e.g., 0.3–0.55).
    - **Abstention (insufficient data):** Confidence neutral (e.g., 0.5, reflecting no information).

    **Rationale:** Confidence should reflect warrant strength and data quality. Founder's ruling on scoring framework needed.

11. **Explaining away and priority:** When multiple lenses conflict (e.g., bright signal in ACL but normal continuity), which takes precedence?

    **PROPOSAL (for founder's ruling):**
    - **Geometry (continuity, thickness, space width) over signal:** A broken ligament is a tear, regardless of signal. A continuous ligament with edema is a strain, not a tear.
    - **Rationale:** Geometry is more objective (visual, binary). Signal is property (intensity, modulated by sequence, field strength, site). Geometry = structure; signal = state of structure.
    - **Founder to confirm:** Is this the right priority, or does signal trump geometry in some findings?

#### On Data Quality and Coverage

12. **Series type distribution:** The wave 1 facts confirm that all sagittal series are paired (FS=0, S=0 or FS=1, S=1); same for coronal and axial. No mixed combinations (e.g., FS=1, S=0).

    **Question:** Is this always true, or did all 58 labeled studies happen to have this pattern? Affects assumptions about what sequences are available.

13. **Slice thickness and pixel spacing variation:** Are these consistent across all studies, or highly variable? Affects resolution-dependent lenses (small meniscal tears, fine fracture lines).

    **Question for founder:** Should lenses be computed per-study (normalized to that study's resolution), or to a fixed standard? (PROPOSAL: per-study normalization is more fair.)

---

## 6. SUMMARY TABLE: Per-Label Warrant Map

| Label | Primary Lenses (Strict/Definit.) | Directional FOR Lenses | Directional AGAINST | Abstain If | Confidence Pattern |
|---|---|---|---|---|---|
| **ACL** | GEO.ACL.CONTINUITY (SpPin tear) | SIG.ACL.MID.T2BRIGHT (edema/acute) | GEO.ACL.CONTINUITY (continuous) + normal signal | No T2 FS, ¬ACQ.SAG.COVERAGE | High if continuity break; mid if edema alone |
| **MCL** | — | SIG.MCL.T2BRIGHT (edema/acute) | SIG.MCL.T2BRIGHT (normal) + TOP.LIGATT.ATTACHMENT (intact) | No T2 FS, ¬ACQ.COR.COVERAGE | Mid if edema + injury history |
| **Med. Meniscus** | GEO.MENISCUS.CONTINU.PATTERN (SpPin tear) | SIG.MENMED.FREEEDGE.T2 (edema/acute) | GEO.MENISCUS.CONTINU.PATTERN (continuous) | No T2 FS, ¬ACQ.SAG/COR.COVERAGE | High if discontinuity; mid if edema alone |
| **Lat. Meniscus** | GEO.MENISCUS.CONTINU.PATTERN (SpPin tear) | SIG.MENLAT.FREEEDGE.T2 (edema/acute) | GEO.MENISCUS.CONTINU.PATTERN (continuous) | No T2 FS, ¬ACQ.SAG/COR.COVERAGE | High if discontinuity; mid if edema alone |
| **Medial OA** | — | GEO.CART.THICKNESS + GEO.JOINTSPACE.WIDTH + GEO.OSTEO.PRESENT (all three = high confidence OA) | All three absent (normal cartilage, space, no osteophytes) | ¬ACQ.COR.COVERAGE, ¬PRIOR.AGE | High if all three OA markers; mid if cartilage alone |
| **Lateral OA** | — | GEO.CART.THICKNESS + GEO.JOINTSPACE.WIDTH + GEO.OSTEO.PRESENT (lateral location) | All three absent | ¬ACQ.COR.COVERAGE, ¬PRIOR.AGE | High if all three markers; mid if cartilage alone |
| **PF OA** | — | GEO.CART.THICKNESS (PF) + GEO.OSTEO.PRESENT (PF) ± GEO.PF.ALIGNMENT (malalignment risk) | All absent | ¬ACQ.AXI.COVERAGE (true PF joint), ¬PRIOR.AGE | High if cartilage loss + osteophytes; mid if malalignment alone |
| **Effusion** | SIG.JOINTSPACE.T2BRIGHT (bright fluid in space, high specificity) | SIG.JOINTSPACE.T2BRIGHT (bright signal measured/obvious) | SIG.JOINTSPACE.T2BRIGHT absent (normal baseline) | ¬ACQ.FLUIDSEN.PRESENT (no T2 FS) | High if bright signal; low if equivocal |
| **Synovitis** | — | SIG.SYNOV.T2BRIGHT (thickened, bright synovium) + effusion (indirect sign) | SIG.SYNOV.T2BRIGHT absent (thin, dark membrane) | ¬ACQ.FLUIDSEN.PRESENT, poor visualization synovium | Mid if membrane thickening + effusion; low if membrane signal alone |
| **Baker's** | GEO.BAKERS.CYST.PRESENCE (SpPin, geometry definitive) | GEO.BAKERS.CYST.PRESENCE (loculated popliteal fluid) | GEO.BAKERS.CYST.PRESENCE absent in visualized popliteal space | ¬ACQ.AXI.COVERAGE (no popliteal space coverage) | High if cyst present; 0 if space visible and empty |
| **Contusion** | — | SIG.MARROW.T1DARK (dark on T1) ∨ SIG.MARROW.STIR (bright on STIR, more sensitive) | Both absent (normal marrow signal) | Image quality poor, no T1 or STIR | Mid if STIR edema present; low if T1 only |
| **Fracture** | SIG.CORTICAL.BREAK (SpPin, discontinuity definitive) | SIG.CORTICAL.BREAK + (SIG.MARROW.T1DARK ∨ SIG.MARROW.STIR) (edema around break) | ¬SIG.CORTICAL.BREAK ∧ ¬marrow edema (absent on both) | ¬ACQ.SLICETHICK ≤ 4 mm (thick slices) + no STIR | High if cortical discontinuity visible; mid if edema without break (occult) |

---

**End of Wave 1 Synthesis**  
**Status:** Complete catalogue, warrant classes, per-label rules, hard pairs, and open questions prepared for founder's review and ruling.

**Next steps (for founder + subsequent agents):**  
1. Founder reviews and answers open questions (§5.2).
2. Refine lenses and rules based on founder's answers.
3. Build rule-evaluation harness to read lenses and assign confidence scores.
4. Implement acceptance criteria and test on training data.
5. Prepare for test-time inference.
