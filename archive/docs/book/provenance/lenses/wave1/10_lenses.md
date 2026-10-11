# Wave 1: The Body of Lenses — RSNA Knee Abnormality Detection

**Date:** 2026-10-10  
**Status:** Initial comprehensive catalogue of lenses, organized by kind.  
**Method:** Thermometer principle applied to knee MRI (v7 §1.1–§1.10). Each lens measures one objective fact at a registered site. No classifier, no fitted weight.

---

## A. ACQUISITION LENSES: What Each Series Is and Can See

A series is defined by its plane (Sagittal, Coronal, Axial), fluid sensitivity (FS=0 or FS=1), fat suppression (S=0 or S=1), field strength (1.5T or 3T), and spatial resolution (pixel spacing, slice thickness). These lenses measure what the series can and cannot resolve.

### A1: Sagittal Plane Coverage

| Property | Value |
|---|---|
| **Lens ID** | ACQ.SAG.COVERAGE |
| **One Fact** | Sagittal slices, when registered to the platonic knee frame, cover which anterior-posterior depths and which superior-inferior extents of the knee. |
| **Site** | Sagittal series; measured once per study. |
| **Calibration** | Standard knee anatomy: sagittal plane shows the profile from medial to lateral, from patellar tendon to posterior capsule. Coverage boundaries (anterior-most and posterior-most slices) define what structures are in-plane. |
| **Silences** | Cannot measure: lateral-medial width (measured by coronal), joint-space separation in axial (measured by axial), thickness of cartilage perpendicular to plane. |
| **Warrant** | **DEFINITIONAL** (geometry of the acquisition). The sagittal plane at each depth shows specific structures: ACL, PCL ligaments, anterior meniscal horn, posterior meniscal horn, intercondylar notch. A slice missing from the series is a structure not acquired. |
| **Standing** | **Wide lens with strict negative warrant (SnNout).** If no sagittal slice reaches the intercondylar notch, ACL abnormality cannot be seen; absence of evidence warrants refusal, never absence of ACL. If sagittal coverage reaches deep into the notch, ACL visibility is established and silence is not an excuse. — **Law:** MRI physics: a structure not in the slice cannot be resolved. |
| **Labels** | ACL, MCL, Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA, PF OA (all benefit from sagittal). |

### A2: Coronal Plane Coverage

| Property | Value |
|---|---|
| **Lens ID** | ACQ.COR.COVERAGE |
| **One Fact** | Coronal slices, when registered, cover which medial-lateral extents and which superior-inferior spans of the knee. |
| **Site** | Coronal series; measured once per study. |
| **Calibration** | Standard anatomy: coronal plane shows the joint from medial compartment through midline to lateral compartment. It shows the meniscal roots, the tibial and femoral condyles, and ligament attachments (MCL insertion sites, ACL origin). |
| **Silences** | Cannot measure: anterior-posterior depth of structures (sagittal shows this). Cannot see joint-space separation quantitatively without axial. |
| **Warrant** | **DEFINITIONAL.** Meniscal tears in the coronal plane appear as discontinuities in the fibrocartilage. MCL attachment points are visible. OA compartment-by-compartment (medial vs lateral) is defined by the plane: compartments are separated medial-laterally. |
| **Standing** | **Wide lens.** If no coronal slice reaches the medial compartment, medial OA and medial meniscal pathology cannot be seen. If coverage spans medial to lateral, the compartment separation is acquired. — **Law:** Anatomy: the three compartments (medial tibiofemoral, lateral tibiofemoral, patellofemoral) are distinct spaces, and coronal separates medial from lateral. |
| **Labels** | MCL, Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA, Synovitis (distribution by compartment). |

### A3: Axial Plane Coverage

| Property | Value |
|---|---|
| **Lens ID** | ACQ.AXI.COVERAGE |
| **One Fact** | Axial slices, when registered, span which superior-inferior levels of the knee, from suprapatellar pouch to tibiofibular joint. |
| **Site** | Axial series; measured once per study. |
| **Calibration** | Standard anatomy: axial plane shows the joint space true width, the femoral and tibial articular surfaces face-on, and the popliteal structures (Baker's cyst origin). Axial levels define: patellofemoral joint (proximal), tibiofemoral joint (middle), tibiofibular joint (distal). |
| **Silences** | Cannot measure: anterior-posterior extent of structures (sagittal). Cannot see meniscal horns or ligament length (those are anterior-posterior). Cannot see meniscal root attachments in detail (coronal better). |
| **Warrant** | **DEFINITIONAL.** Axial at the true joint-space level is the only view that measures true cartilage thickness and joint-space width directly. It is the only view that can resolve the popliteal cyst (Baker's) as a separate space behind the joint capsule. |
| **Standing** | **Narrow lens with strict positive warrant (SpPin) for joint-space width, Baker's cyst presence.** If an axial slice at the joint-space level shows a fluid-filled space posterior to the capsule, that space is a cyst by geometry (a cyst is a closed space filled with fluid). Absence of this finding on axial, where coverage is present, means no Baker's cyst. — **Law:** Anatomy: a cyst is a closed epithelial space; its geometry defines it. Axial is the only plane that sees the popliteal space filled or empty. Cartilage thickness is best measured perpendicular to the surface, and axial provides that (perpendicular to the femoral/tibial surface). |
| **Labels** | Baker's, PF OA (cartilage thickness), Effusion (true width of joint fluid). |

### A4: Fluid-Sensitive Sequence Availability

| Property | Value |
|---|---|
| **Lens ID** | ACQ.FLUIDSEN.PRESENT |
| **One Fact** | Whether this series is a fluid-sensitive (FS) sequence (T2, STIR, FLAIR class) or not, as recorded in train_series.csv column Fluid_Sensitive. |
| **Site** | Series metadata; one value per series. |
| **Calibration** | FS=1 means the pulse sequence was tuned to make free fluid (water) bright relative to solid tissue. FS=0 means a non-fluid-sensitive sequence (T1, PD weighted without FS). |
| **Silences** | Sequence name is not always explicit in the metadata (only SeriesDescription, which may be abbreviated). Exact pulse parameters (TE, TR, FlipAngle) are in DICOM headers but cannot always distinguish T2 FS from STIR by name alone. |
| **Warrant** | **DEFINITIONAL.** A fluid-sensitive sequence by physics reaches high signal in free water (effusion, cyst fluid, edema). A non-fluid-sensitive sequence does not. This fact directly determines what can be seen: edema and effusion appear as bright regions on FS sequences and may not appear on non-FS. |
| **Standing** | **Narrow lens.** FS=1 is required to detect effusion and synovitis with confidence (bright joint space, bright synovium). On non-FS sequences, these findings may not be visible. — **Law:** MRI physics: T2 relaxation time of free water is long; fluid-sensitive sequences weight the image to show long-T2 tissues brightly. Tissue edema and free fluid (effusion) have long T2. Acute ligament/meniscal injury has edema (long T2). The sequence FS directly determines the signal contrast. |
| **Labels** | Effusion, Synovitis, Medial Meniscus, Lateral Meniscus (edema around tears), ACL, MCL (edema in ligaments). |

### A5: Fat Suppression Availability

| Property | Value |
|---|---|
| **Lens ID** | ACQ.FATSUP.PRESENT |
| **One Fact** | Whether this series has fat-suppression (S=1) applied, as recorded in train_series.csv column Fat_Suppression. |
| **Site** | Series metadata; one value per series. |
| **Calibration** | S=1 means the pulse sequence actively suppresses the signal from fat (chemical shift or SPAIR/SPIR pulse). S=0 means fat is not suppressed and appears bright (T1 or PD without FS). |
| **Silences** | Fat suppression quality may vary (incomplete suppression artifacts, signal dropout near metal). Metadata records only yes/no, not quality. |
| **Warrant** | **DIRECTIONAL FOR edema detection.** Fat-suppressed + fluid-sensitive (FS=1, S=1) sequences maximize contrast between edema (bright) and fat (suppressed). Non-fat-suppressed sequences have bright fat that can obscure edema. This fact determines the sequence's utility for acute injury (edema) vs chronic changes (see fat clearly on non-FS). |
| **Standing** | **Directional, not strict.** FS=1, S=1 together are ideal for edema (acute ligament tear, meniscal tear, bone marrow edema, synovitis). FS=1, S=0 can still see edema but with more fat in the background. — **Law:** MRI physics: edema and fat have different T1 and T2; FS and fat suppression are complementary contrasts. |
| **Labels** | ACL, MCL, Medial Meniscus, Lateral Meniscus, Synovitis, Contusion (edema in bone marrow). |

### A6: Field Strength (Magnetic Field)

| Property | Value |
|---|---|
| **Lens ID** | ACQ.FIELDSTR |
| **One Fact** | The magnetic field strength (1.5 Tesla or 3 Tesla, sometimes 1T), as read from DICOM tag (0018,0087) or metadata. |
| **Site** | Study-level; one value per study. All series in a study are acquired at the same field strength. |
| **Calibration** | Higher field strength (3T) provides higher signal-to-noise ratio (SNR) and faster T1 relaxation, allowing finer detail and shorter sequences. 1.5T is lower SNR but more stable for motion and artifact. Both are diagnostic for knee. |
| **Silences** | Cannot measure from the field strength alone: how the study was acquired (which radiologist, which scanner model, which protocol). Cannot measure image quality directly (that requires pixel analysis). |
| **Warrant** | **DIRECTIONAL FOR signal comparison.** A 3T study has higher SNR and may show finer detail in ligaments and cartilage. A 1.5T study has lower SNR but may be more robust to motion. When calibrating normal population signal intensity, field strength is a parameter: the same structure at the same site has different absolute signal values at 1.5T vs 3T. |
| **Standing** | **Not strict in isolation.** Field strength does not definitively establish absence or presence of a finding, but it is part of the calibration context. — **Law:** Physics: signal intensity is proportional to field strength; T1 and T2 relaxation times are field-dependent. Quantitative comparison requires field strength normalization. |
| **Labels** | All (field strength affects signal-intensity calibration for all structures). |

### A7: Slice Thickness

| Property | Value |
|---|---|
| **Lens ID** | ACQ.SLICETHICK |
| **One Fact** | The slice thickness in millimeters (typically 3–5 mm), as read from DICOM tag (0018,0050) per series. |
| **Site** | Series metadata; one value per series. |
| **Calibration** | Thin slices (2–3 mm) give better through-plane resolution but require more slices for full coverage and take more time. Thick slices (5–7 mm) sacrifice through-plane resolution but are faster and have better SNR. Standard knee protocols use 3–4 mm. |
| **Silences** | Slice thickness alone does not specify in-plane pixel size (that is pixel spacing). Cannot determine coverage (number of slices) without knowing the anatomical region length. |
| **Warrant** | **DIRECTIONAL FOR small-structure visibility.** Thin slices resolve small features (ligament discontinuity, meniscal tear apex) better. Thick slices may miss partial tears (volume averaging). An ACL tear in a thick slice may be missed if the tear is thin and in-plane. |
| **Standing** | **Wide lens with strict negative warrant for certain structures.** If slice thickness is 6+ mm and the meniscal tear is <5 mm, silence on that slice does not exclude the tear (volume averaging). If slice thickness is 2–3 mm and no tear signal is seen across the meniscus's anterior-posterior extent, the absence is more confident. — **Law:** Physics: volume averaging; a feature smaller than the slice thickness may not appear in the slice. |
| **Labels** | Medial Meniscus, Lateral Meniscus, ACL, MCL, Fracture (small fracture lines), Contusion (small edema). |

### A8: In-Plane Resolution (Pixel Spacing)

| Property | Value |
|---|---|
| **Lens ID** | ACQ.PIXELSPACING |
| **One Fact** | The in-plane voxel size (mm per pixel), typically [0.5–1.0 mm, 0.5–1.0 mm] in (row, column) order, as read from DICOM tag (0028,0030). |
| **Site** | Series metadata; one value per series. |
| **Calibration** | Smaller pixel spacing (0.4–0.6 mm) resolves fine detail (cartilage surface, ligament edges). Larger spacing (1.0+ mm) is lower detail but faster and better SNR. Diagnostic protocols aim for 0.5–0.6 mm. |
| **Silences** | Does not directly measure image quality, noise level, or whether the resolution was sufficient to resolve a specific structure. |
| **Warrant** | **DIRECTIONAL FOR fine-structure visibility.** Pixel spacing <0.6 mm improves visualization of hyaline cartilage edges, ligament boundaries, and small fluid collections. Spacing >1.0 mm may miss these details. |
| **Standing** | **Directional, not strict.** Fine structures (thin ligaments, cartilage surface irregularity) are better seen with fine spacing, but their absence on coarser images is not a negative finding (cannot exclude based on poor resolution). — **Law:** Physics: the smallest resolvable feature is roughly one voxel; structures smaller than the voxel are volume-averaged. |
| **Labels** | All (affects visibility of all structures, but especially: ACL, MCL, cartilage thickness, Baker's cyst membrane). |

### A9: Series Type (Plane × Sequence Class)

| Property | Value |
|---|---|
| **Lens ID** | ACQ.SERIESTYPE |
| **One Fact** | The combination of anatomical plane (Sagittal, Coronal, Axial) and sequence class (Fluid-Sensitive or not) present in this series. Recorded in train_series.csv as plane and FS/S flags. |
| **Site** | One per series; aggregated to the study level. |
| **Calibration** | Standard knee protocols use 6–7 series: Sagittal T1, Sagittal T2 FS, Coronal T1 or PD, Coronal T2 FS, Axial T2 FS, and sometimes Sagittal or Coronal STIR. The presence of all three planes, with FS available, is the baseline for full diagnostics. |
| **Silences** | Does not measure: whether any series is missing or which series are actually present (that requires a list). Cannot measure quality, artifacts, or protocol deviations from the metadata alone. |
| **Warrant** | **DEFINITIONAL for protocol completeness.** If the study has only sagittal series and no coronal, then compartment-by-compartment OA assessment is incomplete. If no axial series reach the joint space, Baker's cyst cannot be seen. |
| **Standing** | **Wide lens.** Each plane-sequence pair establishes what can be seen. Absence of a plane or sequence is a boundary of what the study acquired. — **Law:** Imaging physics: each plane and each sequence shows different structures or the same structures with different contrast. Missing a view removes the information that view carries. |
| **Labels** | All (protocol completeness determines what can be evaluated for each label). |

---

## B. SIGNAL LENSES: Deviation From Normal Population at Registered Sites

These lenses measure signal intensity, texture, or brightness at specific anatomical sites, calibrated against a population of normal knees at the same site, plane, and sequence. A deviation is the "temperature"; its meaning (fever, infection, etc.) is for the rules to assign.

### B1: T2 Signal Intensity in ACL, Mid-Substance (Sagittal T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | SIG.ACL.MID.T2BRIGHT |
| **One Fact** | The mean or peak T2 signal intensity in the mid-substance of the ACL in sagittal T2 FS images at the level of maximum ACL width, measured in a region-of-interest (ROI) at the ligament's center, expressed as a normalized value (ratio to muscle or to contralateral knee's ACL). |
| **Site** | ACL, mid-substance, sagittal plane, T2 FS sequence. The ACL runs from the anterior tibial spine to the lateral femoral condyle; the mid-substance is the region between these attachments, visible in the intercondylar notch on sagittal. |
| **Calibration** | Normal ACL on T2 FS is isointense or slightly hyperintense to muscle (baseline signal). A population normal at this site is acquired from 100+ normal knees imaged on the same protocol (scanner, field strength, sequence parameters). The population distribution (mean, ±2 SD) defines the digital thermometer's gradations. |
| **Silences** | Cannot measure: ACL signal if the ligament is outside the field of view (violates site coverage, checked by ACQ.SAG.COVERAGE). Cannot measure if T2 FS sequence is not present (FS=0; see ACQ.FLUIDSEN.PRESENT). Cannot measure if the ROI overlaps adjacent structures (requires segmentation, which is not a lens). Volume averaging at the ligament boundary. |
| **Warrant** | **DIRECTIONAL FOR acute ACL injury.** Acute ACL tears are accompanied by hemorrhage and edema, which are bright on T2 FS (high water content, long T2). Chronic tears may show low signal (fibrosis, scar). The brightness is not the diagnosis; the rules read it. — **Rationale:** Physics: edema and blood have long T2 (low proton density weighting, high T2 weighting). The sequence FS enhances this contrast. |
| **Standing** | **Directional, not strict.** High T2 signal in the ACL is evidence for acute injury (edema, blood), but it is not pathognomonic (other structures, noise, sequence artifact can produce bright signal). Very low signal in a torn ACL at the site of discontinuity is directional against integrity, but absence of very low signal does not exclude a tear. A normal or near-normal signal intensity in an intact ACL is evidence for no acute edema (negative directional warrant), but it does not exclude chronic tear (that requires geometric, morphological assessment). — **Law:** MRI physics: edema and hemorrhage have long T2 and appear bright on T2 FS. Fibrosis and scar have short T2 and appear dark. The signal reflects tissue composition (water, collagen, etc.), not the presence of a tear alone. Geometry (continuity, shape) is required to establish a tear. |
| **Labels** | ACL (primary), MCL (secondary; ligaments may co-injure). |

### B2: T2 Signal in MCL (Sagittal or Coronal T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | SIG.MCL.T2BRIGHT |
| **One Fact** | The mean T2 signal intensity in the MCL proper (the ligament itself, not its insertion points) at the level of the medial femoral condyle, measured as a normalized value against muscle, on T2 FS. Site preference: coronal (shows MCL as a band) better than sagittal. |
| **Site** | MCL, ligament body, coronal plane, T2 FS sequence (or sagittal if coronal FS unavailable). The MCL extends from the medial epicondyle of the femur to the medial tibia (below the joint line), visible as a thick band on coronal images. |
| **Calibration** | Normal MCL on T2 FS is isointense to muscle or mildly hyperintense (slightly wavy, low-signal fibers interspersed). Population normal for the MCL at this level and sequence. |
| **Silences** | Cannot measure if coronal T2 FS is not acquired (check ACQ.COR.COVERAGE, ACQ.FLUIDSEN.PRESENT). Signal heterogeneity at the insertion sites makes mid-ligament measurement cleaner. Cannot resolve strains (partial tears with no discontinuity) from signal alone; geometry is required. |
| **Warrant** | **DIRECTIONAL FOR acute MCL injury.** Bright T2 signal = edema, hemorrhage, inflammation → evidence for acute ligament injury (sprain, partial tear, strain). High signal does not establish a complete tear (geometry does); low signal does not exclude chronic tears. — **Law:** Physics: same as B1 (ACL). |
| **Standing** | **Directional.** High T2 in MCL is evidence for acute injury. — **Law:** Anatomy: the MCL is a broad, flat ligament with well-defined anatomy; its signal on a standardized sequence is interpretable. |
| **Labels** | MCL (primary). |

### B3: T2 Signal in Medial Meniscus, Free Edge (Sagittal T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | SIG.MENMED.FREEEDGE.T2 |
| **One Fact** | The T2 signal intensity in the free (articular) edge of the medial meniscus at the level where the meniscus appears widest (usually central third of the meniscus in anterior-posterior extent), measured as a normalized value against the expected low-signal fibrocartilage. |
| **Site** | Medial meniscus, free edge (central region, anterior-posterior middle), sagittal T2 FS. The meniscus is C-shaped; the free edge is the inner margin facing the joint space. |
| **Calibration** | Normal medial meniscus free edge on T2 FS is LOW signal (dark), because the meniscus is fibrocartilage with low water content and short T2 relaxation. A population baseline shows the typical low signal; any bright signal here is abnormal (represents edema, degeneration, or tear). |
| **Silences** | Cannot measure at the anterior and posterior horns (different signal, different anatomy, different T2 properties — see separate lenses). Cannot measure if sagittal T2 FS is absent. Cannot measure through metal artifact (joint hardware). |
| **Warrant** | **DIRECTIONAL FOR meniscal tear.** Bright (edematous) free edge = tear (acute) or severe degeneration. Bright signal at the free edge is a strong directional finding for meniscal abnormality (tear or advanced degeneration), but it requires morphological confirmation (is the meniscus continuous?). A normal dark free edge suggests no tear, but absence of bright signal does not exclude a small or non-edematous (chronic) tear. — **Law:** Anatomy and physics: the meniscus is fibrocartilage, normally low T2. Edema, blood, or degeneration raises water content and brightens the meniscus. The free edge is the surface under direct load and most likely to tear. |
| **Standing** | **Directional FOR meniscal abnormality.** Bright free edge strongly suggests pathology, but requires geometry confirmation. Normal/dark free edge (directional against tear) is less definitive for absence of a non-edematous tear. — **Law:** Anatomy: a torn meniscus usually has edema or blood at the tear site on acute imaging. Chronic tears may not. |
| **Labels** | Medial Meniscus (primary), Synovitis (secondary; edema at free edge may reflect synovitis). |

### B4: T2 Signal in Lateral Meniscus, Free Edge (Sagittal T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | SIG.MENLAT.FREEEDGE.T2 |
| **One Fact** | The T2 signal intensity in the free edge of the lateral meniscus, measured the same way as B3 (normalized to expected low signal), at the meniscus's central region (anterior-posterior middle). |
| **Site** | Lateral meniscus, free edge, sagittal T2 FS. The lateral meniscus is more O-shaped than C-shaped; the free edge is the inner margin facing the joint space. |
| **Calibration** | Same as medial meniscus: normal is low signal (dark fibrocartilage). Population baseline from normal knees. |
| **Silences** | Cannot measure at horns. Cannot measure if sagittal T2 FS absent. The lateral meniscus has a discoid variant (enlarged, filling the joint space) that affects its baseline signal and morphology; this lens cannot distinguish variant from pathology (geometry lenses do). |
| **Warrant** | **DIRECTIONAL FOR meniscal tear, same rationale as B3.** Bright free edge = acute tear or degeneration. — **Law:** Physics and anatomy: same as medial meniscus. |
| **Standing** | **Directional FOR meniscal abnormality.** — **Law:** Anatomy: lateral meniscus tears are often radial or vertical (distinct from medial tears, which are more often horizontal or bucket-handle). |
| **Labels** | Lateral Meniscus (primary), Synovitis (secondary). |

### B5: T2 Signal in Hyaline Cartilage Surface (Sagittal or Coronal T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | SIG.CARTSURF.T2 |
| **One Fact** | The T2 signal intensity in the superficial layer of hyaline cartilage (the articular surface at the cartilage-fluid interface) on a T2 FS sequence, at the femoral condyles or tibial plateau, measured as brightness relative to cartilage interior (cartilage zonal structure). |
| **Site** | Hyaline cartilage surface, femoral condyle or tibial plateau, sagittal or coronal T2 FS. Measured at the most superficial layer (1–2 mm below the surface). |
| **Calibration** | Normal hyaline cartilage has a characteristic zonal structure: bright in the superficial zone (high water, low collagen alignment), intermediate in the middle zone, and low in the deep zone (low water, aligned collagen). Population normal shows the expected layering. Fibrillation (osteoarthritis) disrupts this layering and breaks the surface signal. |
| **Silences** | Cannot measure if cartilage is not in-plane or is outside the field of view. Cannot measure thickness (that is geometry; see G3). The superficial zone is only 1–2 mm; at low resolution, it may be volume-averaged. Cannot distinguish between normal hyaline cartilage and fibrocartilage (meniscus) if they are adjacent (requires geometric separation). |
| **Warrant** | **DIRECTIONAL AGAINST osteoarthritis (OA).** Presence of normal bright superficial zone with sharp surface = normal cartilage. Loss of surface brightness and/or irregular surface signal = fibrillation → early OA. But absence of fibrillation does not exclude OA (OA includes joint-space narrowing, bone osteophytes, which are geometric findings). — **Law:** Anatomy: cartilage fibrillation is visible as signal loss at the surface on T2; it reflects collagen disruption (loss of organized collagen matrix). Tissue edema in pre-OA shows as brightening of cartilage; cartilage thinning with OA shows as loss of the normal zoned signal. |
| **Standing** | **Directional FOR early OA, not strict for OA diagnosis.** Sharp bright surface = no fibrillation. Loss of surface signal or irregular surface = fibrillation, directional FOR OA. But fibrillation is only one criterion for OA; joint space narrowing and osteophytes are required for full OA diagnosis. — **Law:** Anatomy: cartilage fibrillation is the earliest gross finding in OA. |
| **Labels** | Medial OA, Lateral OA, PF OA (all depend on cartilage assessment). |

### B6: T2 Signal in Joint Space (Sagittal or Axial T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | SIG.JOINTSPACE.T2BRIGHT |
| **One Fact** | The mean T2 signal intensity in the joint space (the space between femoral and tibial articular surfaces), measured on T2 FS as a normalized brightness. Presence of bright signal filling the joint space indicates fluid (normal synovial fluid is mildly hyperintense on T2 FS; excess fluid = effusion). |
| **Site** | Joint space, measured in the center of the tibiofemoral articulation (sagittal midline or axial at the joint level). Sagittal shows the anterior-posterior depth; axial shows true width. |
| **Calibration** | Normal joint space contains thin layer of synovial fluid (barely visible to dark on T2 FS). A bright joint space indicates excess fluid (effusion). Population normal defines the upper limit of normal joint space signal (e.g., <5 mm of bright signal in the anterior recess on sagittal). |
| **Silences** | Cannot measure if the joint space is not in-plane (requires sagittal or axial series through the joint center). Cannot distinguish between normal synovial fluid and pathological effusion by signal alone; volume is part of geometry (G4). Bright signal from artifact or flow (motion of synovial fluid) can mimic effusion. |
| **Warrant** | **DIRECTIONAL FOR effusion, joint inflammation.** Bright T2 signal filling the joint space = free fluid → effusion or synovitis. Absence of bright signal in the joint space = no excess fluid (but does not exclude synovial thickening without fluid accumulation). — **Law:** Physics: free fluid (effusion) is bright on T2 FS. Synovial inflammation without effusion may not produce bright signal in the space itself. — **Anatomy:** The joint space is normally a thin film. Bright filling of the space indicates excess fluid. |
| **Standing** | **Directional FOR effusion.** Bright joint space = effusion present (high sensitivity). Absence of bright signal = no effusion (high specificity). This lens is one of the clearest for effusion detection. — **Law:** MRI physics: free fluid in a small space appears bright on T2. |
| **Labels** | Effusion (primary), Synovitis (secondary; synovitis often co-occurs with effusion). |

### B7: T2 Signal in Synovial Membrane (Sagittal or Axial T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | SIG.SYNOV.T2BRIGHT |
| **One Fact** | The T2 signal intensity in the synovial membrane (the joint lining) at the capsular reflection, particularly in the anterior recess (the space between the patellar tendon insertion and the joint capsule), measured on T2 FS as thickening and brightness of the normally thin low-signal membrane. |
| **Site** | Synovial membrane, anterior recess, sagittal T2 FS (or axial if anterior recess is shown). The anterior recess is the anterior-most point of the joint cavity, visible as a recessed space in the sagittal plane inferior to the patella and superior to the tibial plateau. |
| **Calibration** | Normal synovium is thin (<2 mm) and low signal. Inflamed (edematous) synovium is thick (>3 mm) and bright on T2 FS (edema in the synovial tissue). Population normal defines the upper limit of normal thickness and signal. |
| **Silences** | Cannot measure if T2 FS is not acquired. Cannot measure synovial signal if the recess is not in the field of view. Cannot distinguish synovitis from post-traumatic inflammation (both produce synovial thickening and bright signal). |
| **Warrant** | **DIRECTIONAL FOR synovitis.** Thickened, bright synovium = inflammation (synovitis). Normal thin, dark synovium = no synovitis. Synovitis often co-occurs with effusion (both bright findings), but synovium can be inflamed without excess free fluid. — **Law:** Anatomy: synovitis is inflammation of the synovial lining. Edema in the inflamed synovium brightens on T2. **Physics:** Edema = long T2 = bright on T2 FS. |
| **Standing** | **Directional FOR synovitis.** Bright, thickened synovium suggests inflammation. Absence of thickening and brightness suggests no acute synovitis. Synovitis is a global finding (affects the whole joint), so multiple sites of synovial thickening strengthen the finding. — **Law:** Anatomy: synovitis is an inflammatory process affecting the synovial lining. |
| **Labels** | Synovitis (primary), Effusion (secondary; effusion and synovitis often co-occur). |

### B8: T1 Signal in Bone Marrow (Sagittal or Coronal T1)

| Property | Value |
|---|---|
| **Lens ID** | SIG.MARROW.T1DARK |
| **One Fact** | The T1 signal intensity in the bone marrow of the femoral or tibial condyle at the site of suspected trauma or contusion, measured as brightness on a T1 sequence. Normal bone marrow in an adult is bright (fat = short T1). Edema or blood in marrow is dark (long T1). |
| **Site** | Bone marrow, femoral or tibial condyle, T1 sequence (sagittal or coronal). Site is matched to the suspected injury (e.g., marrow edema under the cartilage at the area of loading in OA, or at the site of impact in contusion). |
| **Calibration** | Normal marrow is bright (fat = short T1, bright on T1). Marrow edema (water, long T1) is dark. Population normal marrow has consistent brightness within a study and is bright relative to muscle. Edematous marrow is dark relative to normal marrow. |
| **Silences** | Cannot measure if T1 sequence is not acquired. T1 is less sensitive to edema than STIR or T2 FS, so absence of dark signal on T1 does not exclude marrow edema (see T2 FS or STIR if available). Cannot measure marrow signal if the site is at a metaphyseal epiphysis (resides in two different regions with different baseline). |
| **Warrant** | **DIRECTIONAL FOR contusion (bone bruise).** Dark marrow on T1 (isointense to muscle or darker) = marrow edema → contusion or occult fracture. Bright marrow on T1 (normal fat signal) = no acute edema. Marrow edema in the context of a fracture line (see geometry) = confirmed contusion. Without a fracture line, marrow edema alone suggests impaction or contusion (no break in the cortex yet). — **Law:** Anatomy and physics: bone contusion is impact to bone without cortical break; it produces marrow edema. Marrow edema is water-rich and has long T1 (appears dark on T1 weighted images). Fat is bright on T1. On T1, edema-replaced marrow is darker than normal marrow. |
| **Standing** | **Directional FOR contusion.** Dark marrow signal on T1 is directional evidence for marrow edema (contusion, impaction). Bright marrow is directional against acute marrow edema, but does not exclude old contusions or healed contusions (those may leave no marrow signal abnormality). — **Law:** Physics: T1 is relatively insensitive to edema compared to T2 or STIR. T2 FS or STIR (if available) is more sensitive. |
| **Labels** | Contusion (primary), Fracture (secondary; marrow edema around a fracture indicates impact and healing). |

### B9: T2 STIR Signal in Marrow (Sagittal or Coronal STIR, if available)

| Property | Value |
|---|---|
| **Lens ID** | SIG.MARROW.STIR |
| **One Fact** | The STIR (Short-Tau Inversion Recovery) signal intensity in bone marrow, measured as brightness. STIR suppresses fat (unlike T1, which doesn't) and sensitizes to water (edema), making it the most sensitive sequence for marrow edema. A bright spot on STIR = edema. |
| **Site** | Bone marrow, femoral or tibial condyle, STIR sequence. |
| **Calibration** | Normal marrow on STIR is suppressed (fat suppression) and appears dark. Edematous marrow (water) appears bright on STIR. Population normal marrow is dark and uniform; edematous regions are focal or diffuse bright spots. |
| **Silences** | Cannot measure if STIR is not acquired (STIR is less common than T1 or T2 FS in standard protocols; presence not guaranteed). Acute bone marrow signal changes (edema) fade over weeks; old contusions may not show signal changes. |
| **Warrant** | **DIRECTIONAL FOR acute marrow edema.** Bright STIR = marrow edema = contusion or impaction. STIR is more sensitive than T1. Absence of bright STIR = no acute marrow edema (but does not exclude old contusions). — **Law:** Physics: STIR is the most sensitive MRI sequence for detection of marrow edema (water). Edema appears bright; fat is suppressed and dark. |
| **Standing** | **Narrow lens with strong directional FOR marrow edema.** Bright STIR in the marrow is a sensitive finding for contusion. Absence of STIR signal does not exclude contusion (need T1 or T2 FS for comparison; T1 is less sensitive). — **Law:** Physics: STIR sensitivity to edema. |
| **Labels** | Contusion (primary), Fracture (secondary; marrow edema around fracture). |

### B10: Cortical Discontinuity Signal (Sagittal, Coronal, or Axial T1 or T2)

| Property | Value |
|---|---|
| **Lens ID** | SIG.CORTICAL.BREAK |
| **One Fact** | The presence of a dark (signal void) line or gap in the cortical bone outline on T1 or T2 sequences, indicating a break in the normally continuous cortical shell. Cortical bone is dense, low-signal ("dark") on all sequences; a discontinuity appears as a break in that dark line. |
| **Site** | Cortical bone, femoral or tibial condyles, tibia, fibula, patella. Any bone surface that might fracture. |
| **Calibration** | Normal cortical bone is a continuous, thin, dark line. A fracture line shows as a dark gap or offset in this line (sometimes with bright edema or blood around it on T2 FS). Population normal is a smooth, continuous cortical outline. |
| **Silences** | Cannot measure if the site is outside the field of view. Cannot always distinguish between a true fracture line and artifact (partial volume at the cortical edge, motion artifact, susceptibility from metal). Occult fractures (stress fractures, impacted fractures) may have no cortical discontinuity (see marrow edema as the signal instead). |
| **Warrant** | **STRICT EXCLUSION for fracture (SpPin).** Visible cortical discontinuity = fracture. This is a narrow lens, definitive positive: a cortical break is by definition a fracture. However, absence of a visible discontinuity does not exclude a fracture (occult fracture, impacted fracture with no cortical offset, or a non-displaced fracture may be invisible on MRI, seen better on CT). — **Law:** Anatomy: cortical bone is a continuous shell; a break is a fracture by definition. Physics: dense cortex is dark; a break appears as a gap in the dark line. |
| **Standing** | **Narrow lens with strict POSITIVE warrant (SpPin) for fracture presence.** If visible cortical discontinuity is seen, a fracture is present (definitive). Absence of visible discontinuity = unknown (need additional evaluation, e.g., marrow edema, CT). — **Law:** Anatomy: cortical discontinuity = fracture. |
| **Labels** | Fracture (primary), Contusion (secondary; fractures are often accompanied by marrow edema and cortical contusion). |

---

## C. GEOMETRY AND MORPHOLOGY LENSES: Shape, Size, Position, Thickness, Continuity

These lenses measure structural features: is the structure intact, what size and shape is it, how thick is it, does it contact a surface?

### G1: ACL Continuity (Sagittal T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | GEO.ACL.CONTINUITY |
| **One Fact** | Whether the ACL appears as a continuous structure from its tibial attachment (anterior tibial spine) to its femoral attachment (lateral femoral condyle), with no visible gap, on sagittal T2 FS images. Measured qualitatively: continuous (1) or discontinuous (0) across the intercondylar notch. |
| **Site** | ACL, full length from attachment to attachment, sagittal T2 FS. The ACL is traced through the intercondylar notch on consecutive sagittal slices, and the anterior-most, middle, and posterior-most slices are checked for continuity. |
| **Calibration** | Normal ACL is continuous (intact) across all sagittal slices. A torn ACL shows a gap or offset at the tear site, usually visible as a break in the ligament fiber continuity or as edema replacing the ligament at the tear. Population normal: 100% continuity in uninjured knees. |
| **Silences** | Cannot measure if sagittal T2 FS is not acquired. Cannot measure if the ACL is out of plane (attachment site is not visible). Partial tears may show continuity on some slices and discontinuity on others; must check all slices. The anterior or posterior fibers of the ACL can tear independently; a complete continuity map requires bundle-level assessment (more advanced than this single lens; see sub-lenses for specific bundles if needed). |
| **Warrant** | **STRICT POSITIVE warrant (SpPin) for ACL tear.** If discontinuity (gap, offset, edema-replaced ligament) is visible at a slice where the ACL should be continuous, an ACL tear is present at that location. This is a narrow, definitive positive lens. Absence of discontinuity suggests an intact ACL, but partial bundle tears may be missed (geometry alone may not resolve them; signal lenses like B1 add sensitivity). — **Law:** Anatomy: the ACL is a ligament with distinct tibial and femoral attachments. Continuity (intact fibers spanning the attachments) is the normal state. A tear is a break in that continuity. Physics: an ACL tear is often associated with edema or hemorrhage, visible on T2 FS, which can make the tear more conspicuous. |
| **Standing** | **Narrow lens with strict POSITIVE warrant for ACL tear.** Discontinuity = tear. Continuity = intact (but does not exclude small bundle tears or strain injuries without full discontinuity). — **Law:** Anatomy: ligament continuity is the definition of an intact ligament. |
| **Labels** | ACL (primary). |

### G2: Meniscal Continuity and Radial vs. Horizontal Tear Pattern (Sagittal and Coronal T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | GEO.MENISCUS.CONTINU.PATTERN |
| **One Fact** | Whether the meniscal free edge is continuous (intact) or interrupted (torn), and if torn, the direction of the tear relative to meniscal radius (radial, horizontal, vertical, or mixed). Measured on sagittal and coronal T2 FS by visual inspection of the meniscal outline. |
| **Site** | Meniscus (medial or lateral), free edge and body, sagittal and coronal T2 FS. Sagittal best shows anterior-posterior extent of tears; coronal shows medial-lateral extent and tear direction relative to the meniscal body. |
| **Calibration** | Normal meniscus: uninterrupted outline of the meniscal wedge (C-shape for medial, O-shape for lateral) across all sagittal and coronal slices. Torn meniscus: visible discontinuity or gap in the outline at the tear site, with a specific directional pattern (radial tears originate from the free edge and run toward the capsular attachment; horizontal tears run parallel to the tibial plateau; vertical tears are complex and less common). |
| **Silences** | Cannot measure if T2 FS is not acquired. Cannot measure if the meniscus is outside the field of view or is volume-averaged in thick slices. Small tears, especially non-displaced tears, may be missed (resolution limited). Meniscal degeneration (internal signal change without tear) is not directly measured by this lens; see B3 (signal) and G6 (meniscal thickness). |
| **Warrant** | **STRICT POSITIVE warrant for meniscal tear.** If discontinuity is visible in the meniscal outline on multiple consecutive slices, a meniscal tear is present. — **Directional implications:** Tear pattern (radial, horizontal) helps indicate tear type and stability (bucket-handle tears are usually medial meniscal horizontal tears; radial tears are more unstable). — **Law:** Anatomy: the meniscus is a fibrocartilage structure with a C-shape (medial) or O-shape (lateral); the outline is normally continuous. A tear breaks that outline. The direction and location of the tear are prognostically important. Physics: the tear appears as a gap or signal change in the meniscus outline on MRI. |
| **Standing** | **Narrow lens with strict POSITIVE warrant for meniscal tear.** Visible discontinuity = tear. Continuous meniscus = intact meniscus (high confidence for absence of tear). This lens is sensitive and specific for meniscal tears when MRI resolution is adequate (thin slices, fine pixel spacing). — **Law:** Anatomy: meniscal continuity is the normal state. A tear is a discontinuity. |
| **Labels** | Medial Meniscus, Lateral Meniscus (primary for each). |

### G3: Cartilage Thickness in Each Compartment (Sagittal or Axial T2 FS or T1)

| Property | Value |
|---|---|
| **Lens ID** | GEO.CART.THICKNESS |
| **One Fact** | The thickness of hyaline cartilage (millimeters) on the femoral condyle and tibial plateau at each joint compartment (medial tibiofemoral, lateral tibiofemoral, patellofemoral), measured perpendicular to the articular surface on a slice that shows maximum cartilage depth. Measured in a region-of-interest (ROI) at the central portion of each articulation (load-bearing zone). |
| **Site** | Hyaline cartilage, femoral condyles and tibial plateau, sagittal at the compartment midline (for medial and lateral tibiofemoral compartments) and axial (patellofemoral compartment). T2 or T1 can be used; T2 FS may show zonal structure better. |
| **Calibration** | Normal cartilage thickness varies by age, sex, and compartment. Population normal for the medial and lateral tibiofemoral compartments is typically 2–3 mm in young adults, and decreases with age and OA. Patellofemoral cartilage is typically thicker (3–4 mm). A thinned cartilage (<1.5 mm on tibiofemoral, <2 mm on patellofemoral) indicates OA. Population normal is established from age-matched control knees. |
| **Silences** | Cannot measure if the compartment is not in the field of view. Cannot measure if the cartilage surface is not clearly delineated (poor image quality, advanced OA with cartilage loss making borders unclear). Cartilage is thin (1–3 mm); at poor resolution (>1 mm pixel spacing), measurement is unreliable. |
| **Warrant** | **DIRECTIONAL FOR osteoarthritis.** Thinned cartilage = OA. Normal cartilage thickness = no advanced OA. However, early OA may have normal thickness with surface changes (see B5, cartilage surface signal) and joint-space narrowing (next lens, G4). — **Law:** Anatomy: OA is progressive thinning and loss of hyaline cartilage. Thickness measurement is a direct quantification of cartilage loss. Physics: cartilage is imaged as a band of intermediate signal on T1, low-to-intermediate on T2; the thickness can be measured from the signal boundaries. |
| **Standing** | **Directional FOR OA.** Thinned cartilage (<1.5 mm) is directional evidence for OA. Normal thickness suggests no advanced OA (but does not exclude early OA with surface changes). — **Law:** Anatomy: cartilage thinning is part of the OA grading. |
| **Labels** | Medial OA, Lateral OA, PF OA (each is assessed in its respective compartment). |

### G4: Joint Space Width (Axial T2 FS at the Joint Level)

| Property | Value |
|---|---|
| **Lens ID** | GEO.JOINTSPACE.WIDTH |
| **One Fact** | The perpendicular distance (millimeters) between the femoral articular surface and the tibial articular surface at the tibiofemoral joint (medial and lateral compartments separately) on axial T2 FS at the level of maximum joint-space width (usually at the central articular surfaces). Measured in three locations per compartment (medial, central, lateral within the compartment) to account for spatial variation. |
| **Site** | Tibiofemoral joint space, medial and lateral compartments separately, axial T2 FS. The axial plane at the true articular level shows the joint space at its widest point. |
| **Calibration** | Normal joint space on axial is typically 4–5 mm (medial and lateral should be similar in an unaffected knee). Narrowed joint space (<3 mm, or asymmetry >1 mm between compartments) indicates OA-related cartilage loss and bone apposition. Population normal: 4–5 mm; OA progression: <3 mm. |
| **Silences** | Cannot measure if axial images do not include the true joint level (coverage check: ACQ.AXI.COVERAGE). Cannot measure if the articular surfaces are not clearly delineated (poor image quality, end-stage OA with bone-on-bone). The joint space varies along the anterior-posterior extent; measurement at one level is a snapshot (but central level is standard). |
| **Warrant** | **DIRECTIONAL FOR osteoarthritis, progressive OA severity.** Narrowed joint space = cartilage loss → OA. Normal joint space = no joint-space narrowing (absence of evidence for OA from this finding alone; early OA may have normal space with cartilage signal changes). — **Law:** Anatomy: OA is characterized by cartilage loss and bone apposition, reducing the space between articular surfaces. Measurement of space width directly reflects cartilage thickness (thick cartilage = wide space). Physics: the joint space on axial shows true separation; sagittal and coronal may foreshorten it. |
| **Standing** | **Directional FOR OA.** Narrowed space = strong directional evidence for advanced OA. Normal space = directional against OA (but does not exclude early OA with cartilage swelling or surface fibrillation). — **Law:** Anatomy: joint-space narrowing is a diagnostic criterion for OA. |
| **Labels** | Medial OA, Lateral OA (each assessed in its compartment). |

### G5: Osteophyte Presence and Size (Sagittal or Coronal)

| Property | Value |
|---|---|
| **Lens ID** | GEO.OSTEO.PRESENT |
| **One Fact** | The presence (yes/no) and size (small <5 mm, moderate 5–10 mm, large >10 mm) of osteophytes (bone spurs) at the joint margins of each compartment (medial, lateral, patellofemoral), measured on sagittal or coronal images. Osteophytes are small bony projections at the joint margin, visible as low-signal bone extending beyond the normal cortical contour. |
| **Site** | Joint margins (femoral and tibial), each compartment, sagittal or coronal. Osteophytes are most prominent at the margins of the weight-bearing area. |
| **Calibration** | Normal knee: no osteophytes (or minimal, <2 mm marginal lipping). OA-affected knee: osteophytes present and sized. Size classification helps grade OA severity (Kellgren-Lawrence grading). |
| **Silences** | Cannot measure if the joint margin is not in the field of view. Small osteophytes (<2 mm) may be missed at lower resolution. Osteophytes can be on the femoral or tibial side; measurement requires slices that show both sides (sagittal midline or specific coronal slices). |
| **Warrant** | **DIRECTIONAL FOR osteoarthritis.** Presence of osteophytes = OA present. Absence of osteophytes = likely no OA (or very early, before osteophyte formation). Osteophyte size is directional for OA severity (larger osteophytes = more chronic OA). — **Law:** Anatomy: osteophytes (bone spurs) are a hallmark of OA. They form from chronic joint stress and cartilage loss. Physics: osteophytes are low-signal bone; they appear as projections beyond the normal cortical margin. |
| **Standing** | **Directional FOR OA.** Presence of osteophytes is strong directional evidence for OA. Size is directional for OA severity. Absence of osteophytes is directional against OA (but does not exclude early OA before osteophytes form). — **Law:** Anatomy: osteophyte formation is part of the OA process (secondary to cartilage loss and bone remodeling). |
| **Labels** | Medial OA, Lateral OA, PF OA (presence of osteophytes in each compartment indicates OA in that compartment). |

### G6: Meniscal Thickness and Extrusion (Sagittal and Coronal T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | GEO.MENISCUS.THICK.EXTRUSION |
| **One Fact** | The meniscal body thickness (millimeters, from the free edge to the capsular attachment) at the central region (anterior-posterior middle), and the presence of meniscal extrusion (displacement of the meniscus beyond the tibial margin on axial or coronal images). Measured on sagittal (thickness) and coronal/axial (extrusion). |
| **Site** | Meniscus (medial or lateral), sagittal for thickness, coronal for extrusion extent. The meniscus is measured in its mid-region where it is thickest. |
| **Calibration** | Normal meniscal thickness is typically 8–12 mm (medial), 7–10 mm (lateral) at the central region. Thinned meniscus (<5 mm) indicates degeneration. Extrusion is graded by degree of displacement beyond the tibial margin (none, partial, complete). Population normal: unextruded meniscus within the joint margins. |
| **Silences** | Cannot measure if the meniscus is outside the field of view or is heavily volume-averaged (thick slices). Extrusion measurement requires a coronal or axial view that shows the meniscal boundary relative to the tibial margin (may require specific slices). |
| **Warrant** | **DIRECTIONAL FOR meniscal degeneration and OA.** Thinned meniscus = degeneration. Meniscal extrusion = displacement due to degeneration or tear; extrusion is associated with OA progression. Normal thickness and no extrusion = meniscal health. — **Law:** Anatomy: meniscal degeneration leads to thinning and extrusion. Extrusion is a risk factor for OA progression. Physics: thinned meniscus has reduced height on sagittal and reduced extension on coronal. Extrusion is visible as the meniscal body lying outside the normal boundary. |
| **Standing** | **Directional FOR meniscal degeneration and OA.** Thinned meniscus and extrusion are directional for degenerative changes. Normal thickness and no extrusion suggest meniscal health. — **Law:** Anatomy: meniscal degeneration (thinning, extrusion) is part of OA. |
| **Labels** | Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA (meniscal degeneration and extrusion are associated with OA). |

### G7: Baker's Cyst Presence, Location, and Size (Axial T2 FS, Sagittal T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | GEO.BAKERS.CYST.PRESENCE |
| **One Fact** | The presence (yes/no) of a fluid-filled, loculated structure posterior to the knee joint capsule (popliteal space) on axial and sagittal T2 FS, measured as location (medial vs. lateral in the popliteal space), size (volume in cm³ or diameter in mm), and connection to the joint capsule (communication yes/no). |
| **Site** | Popliteal space (posterior to the knee), axial and sagittal T2 FS. The classic Baker's cyst is found medially in the popliteal fossa, between the medial gastrocnemius and semitendinosus tendons. |
| **Calibration** | Normal popliteal space: no fluid collection, or small <1 cm³ (normal anatomic recess). Baker's cyst: fluid collection >1 cm³, loculated, often with a neck connecting to the joint space (communication with posterior joint capsule). |
| **Silences** | Cannot measure if the popliteal space is not in the field of view (requires adequate axial and sagittal coverage of the posterior knee). Small cysts (<5 mm) may be missed. Cannot always visualize the communication (cyst may disconnect from joint after formation). |
| **Warrant** | **DEFINITIONAL by geometry.** A fluid collection in the popliteal space that is loculated (walled off) and communicates with the joint = Baker's cyst by definition. Size and location are modifiers. Absence of a popliteal fluid collection where the popliteal space is visible = no Baker's cyst. — **Law:** Anatomy: a cyst is a closed epithelial-lined space filled with fluid. The popliteal space is bounded by muscles and joint capsule. A cyst there is a Baker's cyst by anatomy. Physics: fluid on T2 FS is bright. The boundary of the cyst is visible as the thin capsule (low signal). |
| **Standing** | **Narrow lens with strict POSITIVE warrant (SpPin) for Baker's cyst.** Visible fluid collection in the popliteal space = Baker's cyst. Absence of popliteal fluid collection = no Baker's cyst (when popliteal space is visible). This is one of the clearest geometric findings in knee MRI. — **Law:** Anatomy and geometry: a loculated fluid collection in the popliteal space is a cyst. |
| **Labels** | Baker's (primary, definitional). Effusion (secondary; Baker's cysts are associated with joint effusion in many cases, suggesting shared cause like OA or synovitis). |

### G8: Patellofemoral Alignment and Tracking (Axial T2 FS or T1)

| Property | Value |
|---|---|
| **Lens ID** | GEO.PF.ALIGNMENT |
| **One Fact** | The medial-lateral position of the patella relative to the femoral sulcus (groove) on axial images at multiple levels (proximal, mid, distal patellofemoral articulation), measured as the patellar tilt (angle between the patellar long axis and the femoral notch axis) and the patellar shift (millimeters of medial or lateral offset). A normal patella is centered in the sulcus; lateralization or medial deviation indicates malalignment. |
| **Site** | Patellofemoral joint, axial T2 or T1 at three levels: suprapatellar, mid-patellar, and infrapatellar regions. |
| **Calibration** | Normal patellar alignment: patella centered in the femoral sulcus, with no tilt or <8° lateral tilt and <5 mm lateral shift. Patellar malalignment (lateral tracking, excessive tilt) is associated with patellofemoral OA and increased lateral facet loading. |
| **Silences** | Cannot measure if axial images do not cover the full patellofemoral joint. Measurement requires clearly defined patellofemoral anatomy (poor image quality or marked deformity makes measurement difficult). Alignment varies with knee flexion (axial images are typically taken in slight flexion; full-extension images may show different alignment). |
| **Warrant** | **DIRECTIONAL FOR patellofemoral OA.** Patellar lateralization and tilt = increased lateral facet loading → risk for PF OA. Normal centered alignment = lower risk for OA from alignment alone (other factors like cartilage damage contribute). — **Law:** Anatomy and biomechanics: patellar malalignment increases stress on the lateral patellofemoral facet, promoting cartilage wear and OA. |
| **Standing** | **Directional FOR patellofemoral OA.** Malalignment is directional for PF OA risk but is not itself OA (OA requires cartilage damage, joint-space narrowing, osteophytes). Normal alignment is directional against OA from this factor. — **Law:** Anatomy: patellar tracking affects biomechanical load distribution in the patellofemoral joint. |
| **Labels** | PF OA (primary). |

---

## D. TOPOLOGY LENSES: Contiguity, Connectivity, and Spatial Relations From Slice to Slice

### T1: Ligament Attachment Integrity (Coronal T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | TOP.LIGATT.ATTACHMENT |
| **One Fact** | Whether the MCL or ACL attachment sites (insertion or origin) show continuous signal from bone to ligament (normal) or show a gap, edema, or signal change indicating an avulsion injury or enthesopathy (attachment damage). Measured on coronal for MCL attachment (femoral epicondyle and tibial medial plateau) and sagittal for ACL origin (anterior tibial spine) and insertion (lateral femoral condyle). |
| **Site** | Ligament attachment sites, coronal (MCL) and sagittal (ACL), T2 FS. The attachment is the junction between bone and ligament. |
| **Calibration** | Normal attachment: continuous, dark low-signal ligament merging with bone cortex. Injury at attachment: edema, high T2 signal, visible gap between bone and ligament (avulsion), or heterogeneous signal (chronic attachment inflammation). |
| **Silences** | Cannot measure if the attachment site is out of plane or out of field of view. Small avulsions may be missed (resolution-limited). Attachment signal change may occur without full detachment (chronic tendinopathy, enthesopathy). |
| **Warrant** | **DIRECTIONAL FOR ligament injury at the attachment.** Discontinuity or edema at attachment = ligament avulsion or attachment injury. Normal appearance = intact attachment. — **Law:** Anatomy: an avulsion is a tear at the attachment site. Edema at attachment indicates inflammation or micro-tears. Physics: edema on T2 FS = bright signal; a gap is a discontinuity. |
| **Standing** | **Directional FOR ligament injury.** Visible gap at attachment (avulsion) is directional FOR ligament tear (the tear is at the attachment rather than mid-substance). Edema at attachment is directional FOR injury. Normal attachment = no injury at that site. — **Law:** Anatomy: ligament injuries can occur mid-substance or at attachment sites. |
| **Labels** | ACL, MCL. |

### T2: Meniscal Root Attachment (Coronal T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | TOP.MENROOT.ATTACHMENT |
| **One Fact** | Whether the anterior and posterior roots of the meniscus (attachment points to the tibial plateau and intercondylar area) appear continuous and signal-intact or show discontinuity, edema, or retraction indicating a root tear or detachment. Measured on coronal T2 FS. |
| **Site** | Meniscal roots (anterior and posterior), coronal T2 FS. The medial meniscus roots are at the intercondylar eminence (anterior) and near the lateral tubercle (posterior). Lateral meniscus roots are similar but offset laterally. |
| **Calibration** | Normal root: continuous, low-signal fibrocartilage anchoring the meniscus. Root tear: discontinuity, edema, or retracted meniscus with increased distance from the expected attachment point. |
| **Silences** | Cannot measure if coronal images don't include the root attachments (coverage check: ACQ.COR.COVERAGE). Root tears may be missed if they are partial or non-displaced. |
| **Warrant** | **DIRECTIONAL FOR meniscal tear.** Root tear = meniscal detachment → functional loss of meniscus (cannot distribute load). Root tear findings are directional for meniscal pathology. — **Law:** Anatomy: meniscal roots anchor the meniscus; a root tear allows meniscal extrusion and loss of function. Physics: root tears show as discontinuity and edema on T2 FS. |
| **Standing** | **Directional FOR meniscal tear (specifically root tear).** Discontinuity or retraction at a meniscal root is directional evidence for root tear. Normal root attachment = intact root. — **Law:** Anatomy: root tears are a subtype of meniscal tear with specific functional consequences. |
| **Labels** | Medial Meniscus, Lateral Meniscus. |

### T3: Effusion Loculation and Communication (Sagittal and Axial T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | TOP.EFFUSION.LOCUL |
| **One Fact** | Whether joint effusion (excess synovial fluid) is diffuse and communicating throughout the joint space or is loculated (walled off in one region, not communicating with the rest of the joint). Loculation suggests a cyst or compartmentalized effusion; diffuse effusion suggests a global process (inflammation, OA). Measured on sagittal (anterior-posterior distribution) and axial (medial-lateral distribution). |
| **Site** | Joint space throughout the knee joint, sagittal and axial T2 FS. Loculation is identified by observing whether bright fluid signal is contiguous across the joint or separated by low-signal septa or capsular restrictions. |
| **Calibration** | Normal/diffuse effusion: bright signal filling the joint space continuously from anterior to posterior and medial to lateral. Loculated: bright signal isolated to one region (e.g., anterior recess, posterolateral pouch), not contiguous with other parts of the joint. |
| **Silences** | Cannot measure if the joint space is not visible on the slices obtained. Chronic loculations may have thick septa that appear as thick low-signal bands; the distinction between a thick septum and a communication-blocking structure is not always clear from MRI. |
| **Warrant** | **DIRECTIONAL FOR joint inflammation (synovitis, OA).** Diffuse effusion = global joint inflammation (synovitis, OA effusion, post-trauma). Loculated effusion = secondary cyst or compartmentalized inflammation (less common). — **Law:** Anatomy: joint effusion can be diffuse (acute inflammation) or loculated (chronic, compartmentalized). Distribution suggests the cause. Physics: loculation appears as separation of bright fluid regions by low-signal septa. |
| **Standing** | **Directional FOR inflammation type.** Diffuse effusion is directional for systemic joint inflammation. Loculation is directional for a more localized or chronic process (cyst formation). — **Law:** Anatomy: effusion distribution reflects the underlying process. |
| **Labels** | Effusion (primary), Synovitis (secondary; both use this finding). |

---

## E. WHOLE-STUDY PRIORS: Regime Keys and Context Information

### P1: Patient Age (from DICOM Demographics or Reports)

| Property | Value |
|---|---|
| **Lens ID** | PRIOR.AGE |
| **One Fact** | The patient's age at the time of the MRI study, in years, as extracted from DICOM tag (0010,1010) or calculated from birth date, or inferred from clinical reports. |
| **Site** | Study-level; one value per study. |
| **Calibration** | Age is a continuous variable. It affects normal reference ranges for many findings (e.g., cartilage thickness and OA prevalence increase with age; meniscal tears and acute ligament injuries are more common in younger, active populations). A 70-year-old with mild OA is normal; a 20-year-old with the same finding is abnormal. Population normals are age-stratified. |
| **Silences** | If age is not in DICOM or reports, it cannot be read. Age does not directly indicate the presence of pathology but modulates the interpretation of findings. |
| **Warrant** | **DIRECTIONAL FOR OA prevalence and baseline expected findings.** Older age is directional for OA (higher prevalence). Younger age is directional against OA and favors acute injury findings. Age stratifies the normal reference population. — **Law:** Epidemiology and biology: OA prevalence increases with age. Acute injuries (meniscal tears, ligament sprains) are more common in younger populations. Age is a fundamental demographic prior. |
| **Standing** | **Not sufficient alone for any diagnosis, but essential for calibration.** Age must be used to select the appropriate population normal for other lenses (e.g., cartilage thickness normal for age 50 is different from age 20). — **Law:** Statistics: prior probabilities and normal ranges are age-dependent. |
| **Labels** | All (prior for all age-dependent conditions, especially OA). |

### P2: Mechanism of Injury or Clinical History (from Reports, if Available)

| Property | Value |
|---|---|
| **Lens ID** | PRIOR.MECHANISM |
| **One Fact** | The patient's reported mechanism of injury or clinical history (e.g., fall, twisting injury, sports trauma, insidious onset, no reported injury), as extracted from the radiologist's report or clinical indication. This is a categorical variable: (acute trauma / chronic symptoms / no known injury / unknown). |
| **Site** | Study-level; one value per study (or per study section if multiple mechanisms are mentioned). |
| **Calibration** | Acute trauma is associated with ligament tears, meniscal tears, and contusions (edema). Chronic symptoms are associated with OA and meniscal degeneration. No reported injury suggests a degenerative or inflammatory process. Unknown mechanism leaves findings interpretation open. |
| **Silences** | If reports are not provided (as at test time in this competition), mechanism cannot be extracted. Patient history may not be reliable or may not be recorded. |
| **Warrant** | **DIRECTIONAL FOR acute vs. chronic findings.** Acute trauma history is directional FOR ligament tears, meniscal tears, edema, effusion. Chronic symptoms history is directional FOR OA and degenerative changes. Unknown or no reported injury is a neutral prior, leaving all possibilities open. — **Law:** Pathophysiology: acute injuries (tears) have acute imaging findings (edema, discontinuity, hemorrhage). Chronic OA has chronic findings (cartilage loss, osteophytes, joint-space narrowing). |
| **Standing** | **Directional, not sufficient alone.** History modulates the likelihood of certain findings, but imaging must confirm. A history of trauma biases toward acute findings, but absence of imaging confirmation means the trauma did not cause detectable injury (or injury has healed). — **Law:** Clinical reasoning: mechanism is a prior; imaging is the evidence. |
| **Labels** | All (prior for all conditions, directional based on mechanism). |

### P3: Bilateral Knee Comparison (if Both Knees Imaged)

| Property | Value |
|---|---|
| **Lens ID** | PRIOR.BILATERAL |
| **One Fact** | Whether the MRI study includes both knees or only one, as recorded in the study metadata. If both are imaged, whether each finding in one knee is mirrored in the other knee (symmetric, suggesting a systemic condition) or unilateral (suggesting a local injury or compartmental pathology). |
| **Site** | Study-level; bilateral comparison when both knees are in the study. |
| **Calibration** | Most knee MRI studies are unilateral (one injured knee). Bilateral studies allow comparison: symmetric findings (e.g., bilateral OA) suggest systemic OA; asymmetric findings (e.g., tear in one meniscus) suggest localized injury. |
| **Silences** | This competition provides imaging for one knee per study (no bilateral comparison available in the data). Bilateral comparison would require both knees to be imaged in the same study. |
| **Warrant** | **DIRECTIONAL FOR systemic vs. localized pathology.** Symmetric findings = systemic disease (e.g., bilateral OA). Asymmetric findings = localized injury (meniscal tear in one knee). — **Law:** Pathophysiology: OA is often bilateral (systemic joint disease); injuries are often unilateral (localized trauma). |
| **Standing** | **Not applicable to this study set (unilateral data only).** If bilateral data were available, symmetric findings would be directional for systemic conditions; asymmetric would be directional for localized injury. — **Law:** Clinical reasoning: anatomic distribution of findings is evidence for disease mechanism (localized trauma vs. systemic degeneration). |
| **Labels** | All (prior for systemic vs. localized interpretation). |

---

## F. CHEAP SQUINTS: Coarse, Rapid Readings for Obvious Findings

These lenses are low-resolution, rapid readings (visual inspection without measurement) used as screening or confirmation tools. They are "cheap" in computation (fast to evaluate) but have lower sensitivity and specificity than detailed measurements.

### S1: Obvious Effusion (Bright Joint Space on Any T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | SQUINT.EFFUSION.OBVIOUS |
| **One Fact** | The presence of visibly bright fluid filling the tibiofemoral or patellofemoral joint space on any T2 FS sequence, visible to the naked eye on visual inspection without measurement. Scored qualitatively: absent (0), small (1, barely visible), moderate (2, clearly visible but not massive), or large (3, massive fluid distending the joint). |
| **Site** | Joint space, visual inspection of any T2 FS image (sagittal, coronal, or axial). |
| **Calibration** | Normal joint has minimal fluid (barely visible dark line). Obvious effusion is bright signal filling the joint space, visible on multiple consecutive slices. |
| **Silences** | Cannot distinguish between normal synovial fluid (normally present, thin layer) and pathological effusion by eyeball inspection alone; measurement (B6, G4) is needed. Artifact or flow-related signal can mimic effusion. Partial volume in thick slices can simulate fluid. |
| **Warrant** | **DIRECTIONAL FOR effusion, rapid screening.** Bright joint space = effusion likely present. Absence of bright signal = effusion unlikely (but cannot exclude small effusion). This lens is sensitive but not specific; it is used for rapid screening, not definitive diagnosis. — **Law:** Physics: free fluid on T2 FS is bright; solid tissue is less bright. Visual inspection detects obvious fluid. |
| **Standing** | **Directional FOR effusion, low-specificity screening.** Obvious bright signal = effusion likely. Used to triage cases for detailed measurement (B6) when needed. — **Law:** Visual inspection is sensitive for gross findings. |
| **Labels** | Effusion (primary, screening), Synovitis (secondary; synovitis often co-occurs with effusion). |

### S2: Obvious ACL Tear or Discontinuity (Visual Inspection, Any Sagittal Sequence)

| Property | Value |
|---|---|
| **Lens ID** | SQUINT.ACL.BREAK |
| **One Fact** | The presence of an obviously visible gap, offset, or edema-replaced region in the middle of the ACL on sagittal images, visible without measurement. Scored: absent or intact (0), suspicious (partial discontinuity, 1), or obvious (clear gap, offset, or edema replacement, 2). |
| **Site** | ACL, sagittal, visual inspection. |
| **Calibration** | Intact ACL: continuous low-to-intermediate signal band from anterior tibial spine to lateral femoral condyle. Torn ACL: visible gap, offset, or bright edema/blood replacing the ligament at the tear site. |
| **Silences** | Requires sagittal images through the intercondylar notch. Partial bundle tears may be subtle (visual inspection may miss them; geometry measurement, G1, is more sensitive). Edema without full discontinuity is ambiguous. |
| **Warrant** | **DIRECTIONAL FOR ACL tear, rapid screening.** Obvious discontinuity = ACL tear likely. Intact appearance = ACL likely intact (but does not exclude subtle partial tears). This is a sensitivity lens: visible tears are rarely false positives, but many subtle tears are missed by eyeball inspection alone. — **Law:** Visual inspection detects gross structural breaks. |
| **Standing** | **Directional FOR ACL tear (high positive predictive value if positive, lower sensitivity).** Used to triage cases for detailed assessment (G1) when needed. — **Law:** Gross visual findings are reliable; subtle findings require measurement. |
| **Labels** | ACL (primary, screening). |

### S3: Obvious Meniscal Tear (Visual Inspection, Sagittal T2 FS)

| Property | Value |
|---|---|
| **Lens ID** | SQUINT.MENISCUS.BREAK |
| **One Fact** | The presence of an obvious gap or discontinuity in the meniscal outline on sagittal T2 FS, visible on inspection without measurement. Scored: absent/intact (0), suspicious (1), or obvious (clear break, offset, 2). |
| **Site** | Meniscus, sagittal T2 FS, visual inspection. |
| **Calibration** | Intact meniscus: continuous smooth outline. Torn meniscus: visible break or offset in the outline. |
| **Silences** | Small tears, non-displaced tears, and degenerated (but intact) menisci may not show obvious visual breaks. Sagittal may not show the tear's full extent or direction (coronal better for that). |
| **Warrant** | **DIRECTIONAL FOR meniscal tear, rapid screening.** Obvious tear = meniscal tear likely. Intact appearance = tear unlikely but does not exclude small or non-displaced tears. — **Law:** Visual inspection detects gross tears. |
| **Standing** | **Directional FOR meniscal tear (high positive predictive value if obvious).** Used for triage; detailed assessment (G2) recommended for subtle cases. — **Law:** Gross visual findings are reliable; subtle findings require careful measurement. |
| **Labels** | Medial Meniscus, Lateral Meniscus (primary, screening). |

### S4: Obvious Bone Marrow Edema (Visual Inspection, Sagittal T1 or STIR)

| Property | Value |
|---|---|
| **Lens ID** | SQUINT.MARROW.EDEMA |
| **One Fact** | The presence of a visibly dark (on T1) or bright (on STIR) region in bone marrow, replacing the normal bright (T1) or suppressed (STIR) marrow signal, visible on inspection. Scored: absent (0), small focal region (1), or large/diffuse region (2). |
| **Site** | Bone marrow, femoral or tibial condyle, T1 or STIR, visual inspection. |
| **Calibration** | Normal marrow: bright on T1, dark/suppressed on STIR (fat). Edema: dark on T1, bright on STIR (water). |
| **Silences** | Small edema may be missed. STIR is much more sensitive than T1; if only T1 is available, sensitivity is lower (see B9). |
| **Warrant** | **DIRECTIONAL FOR contusion or acute bone injury.** Obvious marrow edema = contusion or impaction present. Absence = no acute edema. — **Law:** Physics: marrow edema (water) is visible as dark on T1, bright on STIR. |
| **Standing** | **Directional FOR contusion (high sensitivity if STIR available, lower if only T1).** Used for triage; detailed assessment with measured signal (B8, B9) when needed. — **Law:** Visual inspection detects gross edema; subtle or small edema may be missed. |
| **Labels** | Contusion (primary, screening), Fracture (secondary; bone marrow edema around fracture). |

### S5: Obvious Cortical Fracture Line (Visual Inspection, Any Sequence)

| Property | Value |
|---|---|
| **Lens ID** | SQUINT.FRACTURE.CORTICAL |
| **One Fact** | The presence of an obvious cortical disruption (visible dark gap or offset in the cortical bone outline) on any sequence, visible on inspection. Scored: absent (0), suspicious (1), or obvious (2). |
| **Site** | Cortical bone, femur or tibia, any sequence, visual inspection. |
| **Calibration** | Intact cortex: smooth continuous dark line. Fracture: visible gap, offset, or jagged appearance in the cortical line. |
| **Silences** | Requires adequate image quality and the fractured region to be in the field of view. Occult fractures (stress fractures, impacted fractures with no cortical offset) are not visible on MRI and are not detected by this lens. |
| **Warrant** | **STRICT POSITIVE warrant for fracture.** Obvious cortical discontinuity = fracture present. This is a narrow, definitive lens. Absence of visible cortical break does not exclude an occult or non-displaced fracture. — **Law:** Anatomy: cortical discontinuity is a fracture. |
| **Standing** | **Narrow lens with strict POSITIVE warrant (SpPin) for fracture (same as B10, SIG.CORTICAL.BREAK, but without measurement).** Obvious visual break = fracture. Used for rapid detection; measurement-based confirmation (B10) when needed. — **Law:** Gross cortical breaks are reliably identified visually. |
| **Labels** | Fracture (primary, definitive if positive). |

---

## Summary Table: Lens Catalogue by Type and Count

| Type | Category | Count | Purpose |
|---|---|---|---|
| **A** | Acquisition (Series and Protocol) | 9 | What each series is and can see |
| **B** | Signal (Intensity, Brightness, Deviation from Normal) | 10 | Abnormal signal at registered sites |
| **G** | Geometry & Morphology (Structure, Size, Continuity) | 8 | Shape, size, integrity, location |
| **T** | Topology (Contiguity, Connectivity, Attachment) | 3 | Structural relationships across slices |
| **P** | Priors (Demographics, History, Context) | 3 | Study-level context and calibration |
| **S** | Cheap Squints (Rapid Visual Screening) | 5 | Gross, obvious findings (screening) |
| | **TOTAL** | **38** | |

---

## How Each Lens Serves the Diagnoses

| Diagnosis | Primary Lenses | Secondary Lenses | Key Warrants |
|---|---|---|---|
| **ACL** | G1 (continuity), B1 (signal), SG.CORTICAL.BREAK | T1 (attachment), SQUINT.ACL | Continuity (strict +), Signal (directional) |
| **MCL** | B2 (signal), G1 (continuity), T1 (attachment) | SQUINT.* (if gross) | Signal (directional), Continuity (strict +) |
| **Medial Meniscus** | G2 (continuity, pattern), B3 (signal), G6 (thickness) | T2 (root), SQUINT.MENISCUS | Continuity (strict +), Signal (directional) |
| **Lateral Meniscus** | G2 (continuity, pattern), B4 (signal), G6 (thickness) | T2 (root), SQUINT.MENISCUS | Continuity (strict +), Signal (directional) |
| **Medial OA** | G3 (cart. thickness), G4 (JSW), G5 (osteo) | B5 (cart. surface), P1 (age), SQUINT.MARROW | Thinning (directional), JSW (directional) |
| **Lateral OA** | G3 (cart. thickness), G4 (JSW), G5 (osteo) | B5 (cart. surface), P1 (age), SQUINT.MARROW | Thinning (directional), JSW (directional) |
| **PF OA** | G3 (cart. thickness), G8 (alignment), G5 (osteo) | B5 (cart. surface), P1 (age) | Cart. loss (directional), Alignment (directional) |
| **Effusion** | B6 (JSW signal), B7 (synovium), G4 (JSW width), T3 (locul.) | SQUINT.EFFUSION | Bright JSW (directional, sensitive) |
| **Synovitis** | B7 (synovium), B6 (JSW signal), T3 (locul.) | SQUINT.EFFUSION (if co-occurring) | Thickened, bright synovium (directional) |
| **Baker's** | G7 (cyst presence, size, location) | ACQ.AXI.COVERAGE (if coverage fails) | Popliteal fluid-filled space (strict +) |
| **Contusion** | B8 (T1 marrow), B9 (STIR), G7 (size) | SQUINT.MARROW, P2 (mechanism) | Marrow edema (directional) |
| **Fracture** | B10 (cortical break), SIG.CORTICAL.BREAK, G7 (size) | B8/B9 (marrow edema), SQUINT.FRACTURE | Cortical discontinuity (strict +) |

---

## Notes for the Founder's Review

1. **One fact per lens:** Every lens is a single measurement, never a mix. No lens classifies or decides.

2. **Warrant classes:** Each lens is classified DEFINITIONAL, STRICT EXCLUSION, DIRECTIONAL FOR, DIRECTIONAL AGAINST, or ABSTAIN, with the law or reason explicitly stated.

3. **Standing:** Strict lenses (narrow and wide) are identified; directional lenses are noted as such. Silence is silence, never absence of evidence.

4. **Missing pieces:** This catalogue is built on the available data structure (DICOM + CSVs). Additions and corrections are expected as the actual imaging and clinical rules are clarified. In particular:
   - The exact roles of T1, T2, STIR, and PD sequences in the protocols used for these studies are not yet fully specified in the metadata.
   - Age at imaging is critical for calibration but is not yet confirmed to be in the DICOM headers.
   - Consensus vs. single-read for the 58 labeled studies is unknown; this affects interpretation of the labels as ground truth.

5. **Lenses as a harness:** The lenses form a committee (F, the Founding Prompts §9 restatement). Each lens measures one thing and knows no question. Decisions are made by reading the lenses together, by the rules a radiologist uses (anatomy, physics, imaging criteria). The rules are the work of the next steps.

---

**Version:** 1.0  
**Status:** Initial comprehensive catalogue. Ready for founder's review and amendment. Lenses await the rules that link them to diagnoses and the acceptance criteria that use them to decide.
