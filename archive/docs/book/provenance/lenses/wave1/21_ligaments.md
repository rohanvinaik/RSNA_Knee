# Wave 1: Ligament Lenses — ACL and MCL

**Date:** 2026-10-10  
**Author:** Claude Code (RSNA Knee workflow agent)  
**Status:** Initial structural derivation for founder's ruling on scope, meaning, and warrant.

---

## Overview

This report derives the lens framework for detecting abnormalities of two knee ligaments: the **Anterior Cruciate Ligament (ACL)** and the **Medial Collateral Ligament (MCL)**. Each ligament is analyzed as a structure whose injury can be diagnosed through a combination of simple, objective measurements (thermometers) read at registered anatomical sites, against a population of normal knees.

The method follows the thesis epistemology: each lens is a single objective measurement that knows no question; combinations of lenses form decision paths classified as DEFINITIONAL, STRICT EXCLUSION, DIRECTIONAL FOR, DIRECTIONAL AGAINST, or ABSTAIN. Categories of image (intact, torn, degenerated, artifact) are distinguished by what the lenses resolve. Diagnosis (the competition's binary "abnormality present/absent") is the founder's interpretation of those categories.

---

## 1. ACL (Anterior Cruciate Ligament)

### 1.1 Definition

**HOST'S WORDS:** ACL [FACT: column name from `sample_submission.csv`]

**DOMAIN EXPANSION:** The Anterior Cruciate Ligament is a major intra-articular ligament of the knee, running from the anterior intercondylar area of the tibia to the lateral condyle of the femur, providing anterior stability of the tibiofemoral joint and restraining internal rotation. An "ACL abnormality" in radiology parlance refers to injury: **partial tear, complete tear, or acute/chronic signal abnormality indicating disruption of the ligament's normal structural continuity and mechanical integrity.** — DOMAIN

**SCOPE (QUESTION FOR FOUNDER):** Does "ACL abnormality" include:
- Acute complete tear? —  assumed yes, most common pathology
- Partial/incomplete tear? — assumed yes, visible and clinically significant
- Chronic partial tear (residual from prior injury)? — assumed yes if structurally detectable
- Ligament thinning, degeneration, or laxity without discontinuity? — assumed yes, structural change; clarification needed
- Sprain (edema, hemorrhage) without structural discontinuity? — assumed yes, acute injury; clarification needed

---

### 1.2 The Structural Reason It Can Be Diagnosed

**ANATOMY (DOMAIN):**
- **Location:** The ACL is intra-articular, running obliquely from anteroinferior tibia (anterior intercondylar eminence) to posterolateral femur (lateral femoral condyle), occupying the intercondylar notch. It passes through multiple planes and is best visualized in **sagittal and coronal planes**. — DOMAIN, standard anatomy (Anatomy of the Knee, Platzer; MRI of the Knee, Stoller)
- **Gross anatomy:** The ACL has two functional bundles: the **anterolateral bundle (ALB, stronger, anteromedial fibers)** and **posteromedial bundle (PMB)**. Their distinction is clinically important but may not be resolvable at the image resolution available here. — DOMAIN
- **Normal appearance on MRI:** Continuous, homogeneous signal, usually low signal on most sequences. On **T1-weighted and PD (proton density) sequences**, the ACL appears as a **thin, well-defined, linear structure** with gradual taper from proximal to distal. On **T2-weighted and fluid-sensitive sequences**, the ACL has **low-to-intermediate signal**, standing out against the bright joint effusion (if present). — DOMAIN, MRI physics

**MRI PHYSICS (DOMAIN):**
- **T1-weighted sequences (e.g., T1 SE):** Low signal from organized collagen/fibrous tissue. ACL appears dark, contrasting with bright fat (marrow), allowing visualization of ligament course and continuity. — DOMAIN
- **PD (proton density) sequences:** Intermediate signal; collagen gives low-intermediate signal; excellent T1/T2 contrast allows clear delineation of ligament edges. — DOMAIN
- **T2-weighted sequences (T2 SE, T2 FSE):** Low signal from organized collagen (short T2); bright signal from fluid (joint effusion, edema). Torn ligament = interrupted low-signal line + high-signal fluid filling the gap or within the ligament substance. — DOMAIN
- **STIR or T2 TIRM (fluid-sensitive fat-suppressed):** Collagen = dark; fluid and edema = bright. Acute tear shows **high-signal edema and hemorrhage** within the ligament and gap space, and **discontinuity of the dark line**. — DOMAIN
- **Gradient echo (GRE, SSFP):** Sensitive to susceptibility and field inhomogeneities from hemorrhage and mineralization. Acute hematoma = signal loss or phase artifact at site of tear. — DOMAIN

**MECHANICS OF INJURY (DOMAIN):**
- **Mechanism:** The ACL is primarily stressed by **anterior translation of the tibia relative to the femur** (deceleration, cutting, pivoting) and **internal rotation** of the tibia or external rotation of the femur. The injury is often non-contact in sports. — DOMAIN, orthopedic biomechanics
- **Acute injury:** When torn, the ACL fibers separate, leaving a gap filled with blood, synovial fluid, and loose connective tissue. The proximal stump may fold posteriorly ("Segond sign" variant) or retract. Edema and hemorrhage surround the tear acutely. — DOMAIN
- **Chronic injury:** Healing by scar tissue; the ACL may be thin, frayed, or permanently lax. Chronic tears may have less edema but show **loss of normal bulk and continuity**. — DOMAIN
- **Visibility in MRI:** A **continuous, uniform, thin linear structure** is the normal ACL. A **gap, a kink, a retracted fragment, a bulbous or swollen middle, or high-signal infiltration** all indicate abnormality. The **sagittal plane** is the single best view for assessing overall continuity along the entire course. — DOMAIN

---

### 1.3 The Thermometers (Lenses)

Each lens measures **one objective fact** at a **registered site** in a **specific series**, calibrated against the **population of normal knees at that same site and sequence**.

#### Lens 1: ACL Continuity in Sagittal Plane

**FACT:** Binary assessment of whether the ACL appears as a **continuous, uninterrupted linear structure** along its entire course from tibia to femur, or shows a **gap, discontinuity, or separation**. — DOMAIN, standard radiological assessment

**SITE:** The intercondylar notch, sagittal midline to lateral sagittal plane. The ACL spans from the **anterior intercondylar eminence of the tibia** (distal-anterior) to the **lateral femoral condyle** (proximal-posterior). — DOMAIN, anatomy

**SERIES:** 
- **Primary:** Sagittal T1 (or PD T1-like sequence). Standard sequences include **PD TSE**, **T1 SE**, or **3D-VIBE** reconstructed in sagittal. — DOMAIN, MRI practice
- **Secondary (if available):** Sagittal T2 or STIR for edema confirmation. — DOMAIN
- Note from FACTS: All sagittal series in training set are either (FS=0, FAT_SUP=0) or (FS=1, FAT_SUP=1); no mixed; this determines what is available. — FACT

**CALIBRATION:** The lens reads against **the population normal**: in a normal knee, the ACL is **always continuous and uninterrupted**, a straight or gently curved line of low signal bounded by bright marrow and joint space. Any **interruption is abnormal by definition in a normal-knee population**. The population reference is the ensemble of the unlabeled 4,349 studies and the 34 studies labeled ACL=0 (negative). — FACT, DOMAIN

**WHAT IT MEASURES:** The presence or absence of a **visible gap** (zero signal, or high-signal fluid in the gap) between the proximal and distal ends of the ACL structure. It **does not measure the degree of tear**, the size of the gap, or the presence of retracted fragments (those are secondary findings). It measures **continuity: yes or no**. — DOMAIN

**WARRANT:** This is a **WIDE LENS** (high sensitivity, lower specificity). A **continuous ACL rejects severe/complete tear but not partial tear**. A **discontinuous ACL strongly indicates tear** but is rare in a normal population (SnNout principle: "if sensitivity is high, a negative test rules out the condition"). An ACL showing **clear discontinuity is narrow (high specificity)**. — DOMAIN

---

#### Lens 2: ACL Bulk (Thickness and Integrity of Substance)

**FACT:** Assessment of whether the ACL **maintains normal bulk and uniform cross-section** along its course, or shows **thinning, swelling, fraying, or abnormal heterogeneous signal within the substance**. — DOMAIN

**SITE:** Same as Lens 1: the intercondylar notch, measured mid-sagittal and comparing proximal 1/3, middle 1/3, and distal 1/3 of the ligament's course. — DOMAIN, anatomy

**SERIES:** 
- **Primary:** Sagittal T1 or PD (same as Lens 1). Bulk is assessed by the **width of the low-signal line** as it crosses the intercondylar notch. — DOMAIN
- **Secondary:** Axial T1 or PD at the level of the femoral and tibial attachment sites for cross-sectional bulk. — DOMAIN

**CALIBRATION:** In a normal knee, the ACL has a **consistent, uniform width of approximately 6–10 mm (measured in cross-section or midsagittal)**. Thinning below 5 mm or enlargement above 12 mm is abnormal. Chronic tears may be notably thinner; acute tears may be swollen locally. — DOMAIN, MRI morphometry

**WHAT IT MEASURES:** The **structural integrity and homogeneity of the ligament's substance**. A thin, frayed, or locally swollen ACL indicates **degeneration, partial tearing, or healing scarring**. A uniform, normal-bulk ACL may still harbor a small incomplete tear (not always visible). — DOMAIN

**WARRANT:** This is a **DIRECTIONAL FOR tear; narrow warrant (SpPin)** if the ACL is markedly thinned or swollen. Chronic tears are very thin; acute tears may be swollen proximal to the tear. Thinning is a sign of chronic partial or healed tear. However, **thinning alone is not definitional**; it is evidence strengthening a tear diagnosis when joined with other findings. — DOMAIN

---

#### Lens 3: ACL Signal Homogeneity

**FACT:** Assessment of whether the ACL shows **uniform, low signal (normal)** or **heterogeneous, mixed signal, or high-signal foci within the ligament substance**. — DOMAIN

**SITE:** The entire substance of the ACL, sagittal midline. — DOMAIN

**SERIES:** 
- **Primary:** Sagittal T1 or PD. In T1, normal ACL = low (dark); inhomogeneity = patches of higher signal. — DOMAIN
- **Confirmatory:** Sagittal T2 or STIR. In T2/STIR, normal ACL = low; edema, hemorrhage, or cystic change = HIGH signal. — DOMAIN

**CALIBRATION:** A normal ACL is **homogeneous, low signal on T1 and PD, remaining low on T2** (because organized collagen has short T2). Any **high-signal focus within the ACL on T2/STIR is abnormal** (indicates edema, hemorrhage, or intrinsic degeneration). — DOMAIN, MRI physics

**WHAT IT MEASURES:** The presence of **edema, hemorrhage, or cystic degeneration within the ligament**. Acute tears show **bright signal on STIR/T2** from edema and blood. Chronic partial tears may show **intralesional cyst or signal change from scarring**. — DOMAIN

**WARRANT:** **DIRECTIONAL FOR tear, acute.** High-signal edema on T2/STIR is highly suggestive of acute injury; the edema is an **inflammatory response to tearing**. However, edema can also be seen in **inflammatory conditions (synovitis) or overuse without complete tear**. Inhomogeneity alone is **not definitional** but **strongly suggestive when present**. — DOMAIN

---

#### Lens 4: Gap at Tibia-ACL Insertion (Proximal Attachment)

**FACT:** Visual assessment of whether the ACL's **distal (tibial) attachment appears intact and continuous with the tibia**, or shows a **gap, edema, or avulsion**. — DOMAIN

**SITE:** The anterior intercondylar eminence of the tibia, sagittal and coronal planes. — DOMAIN

**SERIES:** 
- **Primary:** Sagittal T1 and PD (standard). — DOMAIN
- **Secondary:** Coronal T1 and PD for alternative angle. — DOMAIN
- **Axial:** T1 or PD at the tibial attachment level for cross-sectional view. — DOMAIN

**CALIBRATION:** In a normal knee, the ACL inserts continuously into the bone; there is no gap or edema at the insertion. Any **separation, edema, or cyst at the insertion site** is abnormal. — DOMAIN

**WHAT IT MEASURES:** Whether the **proximal (tibial) insertion is intact or shows avulsion, insertion-site tear, or inflammation**. An avulsion with bone fragment is visible on CT better than MRI, but **edema at the insertion and displacement of the ligament** are visible on MRI. — DOMAIN

**WARRANT:** **DIRECTIONAL FOR tear, proximal attachment.** If the insertion is clearly intact, it **partially rules out proximal tears**, but does not rule out midsubstance tears. If the insertion shows edema or separation, it **suggests proximal attachment injury**. — DOMAIN

---

#### Lens 5: Gap at Femur-ACL Insertion (Distal Attachment)

**FACT:** Visual assessment of whether the ACL's **proximal (femoral) attachment appears intact**, or shows a **gap, edema, or avulsion at the lateral femoral condyle**. — DOMAIN

**SITE:** The lateral femoral condyle, posterior-lateral aspect. The ACL attaches to the **medial wall of the lateral femoral condyle** in the intercondylar notch. — DOMAIN

**SERIES:** 
- **Primary:** Sagittal T1 and PD. The femoral attachment is best seen in sagittal views. — DOMAIN
- **Secondary:** Coronal T1 and PD. — DOMAIN

**CALIBRATION:** In a normal knee, the ACL attaches continuously without gap or edema. — DOMAIN

**WHAT IT MEASURES:** **Femoral attachment integrity**. Femoral avulsions are less common than tibial, but do occur (posterolateral femoral condyle can fracture with ACL avulsion). — DOMAIN

**WARRANT:** **DIRECTIONAL FOR tear, distal attachment.** Similar to Lens 4: edema or separation is suggestive of femoral attachment injury. — DOMAIN

---

#### Lens 6: Retraction or Posterior Buckle of ACL (Chronic Tear Sign)

**FACT:** Visual assessment of whether the ACL appears to **retract posteriorly (fold backward) or kink**, rather than maintaining its linear anterior-to-posterior course. — DOMAIN

**SITE:** The course of the ACL in the sagittal plane. — DOMAIN

**SERIES:** Sagittal T1 and PD. — DOMAIN

**CALIBRATION:** In a normal knee, the ACL runs **straight or with a gentle anterior convexity (bows forward slightly)**. A **sharp posterior kink or fold** indicates that the ligament is no longer under tension, a **sign of complete tear**. — DOMAIN, orthopedic MRI

**WHAT IT MEASURES:** **Loss of normal tension and mechanical continuity**. The ACL under tension maintains its position; a ruptured, unattached ACL may sag or coil posteriorly. This is often called a **"posterior buckle"** or **"stranded ACL"** sign. — DOMAIN

**WARRANT:** **NARROW, STRICT indicator of tear.** If the ACL shows a clear posterior buckle or coil, it is **nearly pathognomonic of complete tear**. However, this finding may be subtle and not always present. — DOMAIN

---

#### Lens 7: Secondary Signs — Tibial Spine Fracture or Avulsion

**FACT:** Assessment of whether there is a **visible fracture or bony avulsion at the anterior intercondylar eminence of the tibia**, which may accompany ACL avulsion injury. — DOMAIN

**SITE:** Anterior intercondylar eminence, sagittal and coronal views. — DOMAIN

**SERIES:** Sagittal T1, T2, and coronal views. T2 shows the **edema around the fracture line**. — DOMAIN

**CALIBRATION:** In a normal knee, the tibial spine is intact. A **visible fracture or displaced fragment** is abnormal. — DOMAIN

**WHAT IT MEASURES:** **Mechanical evidence of ACL avulsion or attachment-site injury**. This is a **traumatic sign** specific to mechanism. — DOMAIN

**WARRANT:** **DEFINITIONAL when present (SpPin, high specificity).** A **clear tibial spine avulsion with the ACL displaced** is diagnostic of ACL avulsion injury. However, many ACL tears do **not** have an avulsion, so **absence of avulsion does not rule out tear**. — DOMAIN

---

#### Lens 8: ACL-Related Joint Effusion

**FACT:** Assessment of whether there is an **increase in joint fluid (effusion) associated with the ACL region**, versus **no effusion or effusion elsewhere in the joint**. — DOMAIN

**SITE:** The intercondylar notch and anterior joint space. — DOMAIN

**SERIES:** 
- **Primary:** T2 or STIR (fluid-sensitive sequences) where fluid appears bright. — DOMAIN
- **Secondary:** Sagittal and coronal for anatomical context. — DOMAIN

**CALIBRATION:** In a normal knee, the joint space contains a small amount of lubricating synovial fluid (usually <2 mm). An **acute tear with hemarthrosis** (blood in the joint) causes an **increase in total joint effusion**, though it is **not specific to the ACL** (many injuries cause effusion). — DOMAIN

**WHAT IT MEASURES:** **Acute inflammation or hemorrhage from the recent injury**, localized to the area of the tear. — DOMAIN

**WARRANT:** **DIRECTIONAL FOR acute injury, low specificity (wide lens).** Effusion is suggestive but non-specific; it can be seen with **any knee injury, inflammation, or effusion from other sources**. An **acute hemarthrosis with a torn ACL on exam is strong evidence**, but effusion alone is not. — DOMAIN

---

### 1.4 Decision Paths: ACL Abnormality

**DEFINITIONAL ASSIGNMENTS (Strict Warrant):**

1. **DEFINITIONAL PATH A: Complete ACL tear with clear structural signs**
   - AND: Lens 1 (ACL Continuity) = **discontinuous** (gap visible)
   - AND: Lens 3 (Signal Homogeneity) = **high-signal edema on STIR/T2**
   - AND: At least one of: Lens 6 (posterior buckle), Lens 7 (tibial spine avulsion), Lens 4 or 5 (insertion-site edema/gap)
   - **LAW:** In a normal knee, an **ACL cannot simultaneously appear discontinuous AND have edema AND show mechanical signs of retraction/avulsion**. The conjunction of these three observations is **diagnostically sufficient for complete tear**. — DOMAIN, MRI interpretation standard (Stoller)
   - **CLASSIFICATION:** DEFINITIONAL (T=1 for ACL abnormality)

2. **DEFINITIONAL PATH B: ACL avulsion with bony involvement**
   - AND: Lens 7 = **visible tibial spine fracture or femoral avulsion**
   - AND: Lens 6 = **posterior buckle or retraction**
   - AND: Lens 1 = **discontinuous or markedly abnormal**
   - **LAW:** An ACL with bony avulsion is **mechanically incompatible with normal function** and is **unambiguously a structural injury**. — DOMAIN
   - **CLASSIFICATION:** DEFINITIONAL

---

**STRICT EXCLUSION (Strict Warrant):**

1. **STRICT EXCLUSION PATH: Normal ACL Anatomy**
   - AND: Lens 1 (ACL Continuity) = **continuous, uninterrupted line from tibia to femur**
   - AND: Lens 2 (ACL Bulk) = **normal, uniform width**
   - AND: Lens 3 (Signal Homogeneity) = **homogeneous, low signal on all sequences**
   - AND: Lens 4 and 5 (Insertions) = **intact without gap or edema**
   - AND: Lens 6 (Retraction) = **normal linear course, no buckle**
   - **LAW:** In the **population of normal knees**, an ACL satisfying all six criteria (continuity + bulk + signal + insertions + course) is **anatomically normal by definition**. The imaging appearance **is the measurement; it cannot be wrong**. — DOMAIN, measurement theory
   - **LOGIC:** "All anatomy normal AND all signal normal" → "not abnormal" by **conjunction of six negative readings**. However, **this is a wide lens**: a normal-appearing ACL on standard planes can still harbor a small, incomplete tear not visible at the resolution available. So the absence of tears does **not rule out very small, partial tears**.
   - **CLASSIFICATION:** STRICT EXCLUSION of complete/large tear. Abstains on very small tears.

---

**DIRECTIONAL FOR (Suggestive, non-exclusive):**

1. **DIRECTIONAL FOR PATH: Acute partial tear or edema**
   - AND: Lens 1 = **continuous or only borderline discontinuous**
   - AND: Lens 2 = **thinning or focal swelling**
   - AND: Lens 3 = **high-signal edema on T2/STIR**
   - **REASON:** Acute partial tears show **edema and bulk changes but may not show frank discontinuity** if the tear is incomplete. Edema is an **inflammatory marker** for recent injury. — DOMAIN
   - **STRENGTH:** Moderate-to-strong; ACL edema is **typically associated with injury**, but can be seen in **inflammatory conditions or overuse**. Without discontinuity on standard planes, **remains an incomplete diagnosis**.
   - **CLASSIFICATION:** DIRECTIONAL FOR ACL abnormality (acute)

2. **DIRECTIONAL FOR PATH: Chronic partial tear or scarring**
   - AND: Lens 1 = **continuous but with irregularity or narrowed segment**
   - AND: Lens 2 = **marked thinning (< 5 mm)**
   - AND: Lens 3 = **heterogeneous signal, no bright edema**
   - **REASON:** Chronic tears have healed; the **ligament is now scar tissue, thin and weak**, but may still appear continuous on casual inspection. **Thinning and irregularity are signs of healing/scarring**. — DOMAIN
   - **STRENGTH:** Moderate; suggests **prior tear now scarred**, but **thin ACL can also be a variant of normal anatomy** in some individuals (rare).
   - **CLASSIFICATION:** DIRECTIONAL FOR ACL abnormality (chronic)

3. **DIRECTIONAL FOR PATH: Insertion-site injury**
   - AND: One of Lens 4 or 5 = **edema or gap at insertion**
   - AND: Lens 1 or 2 = **otherwise relatively intact**
   - **REASON:** Insertion-site injuries can occur **without frank discontinuity of the midsubstance**. Edema at the attachment indicates **local trauma**. — DOMAIN
   - **STRENGTH:** Moderate; suggests **attachment injury**, but **not all insertion edema is ACL tear** (can be synovitis, meniscal root inflammation).
   - **CLASSIFICATION:** DIRECTIONAL FOR

---

**DIRECTIONAL AGAINST (Counter-evidence):**

1. **DIRECTIONAL AGAINST PATH: Normal signal and continuity**
   - AND: Lens 1 = **continuous**
   - AND: Lens 3 = **homogeneous, low signal on T2 (no edema)**
   - **REASON:** A **continuous ACL with normal signal is the most common finding in uninjured knees**. The absence of edema argues **against acute injury**. — DOMAIN
   - **STRENGTH:** Moderate; does **not exclude chronic tear or small partial tear on the plane imaged**, but **argues against recent, significant injury**.
   - **CLASSIFICATION:** DIRECTIONAL AGAINST acute ACL tear

---

**ABSTENTION (Missing or Insufficient Information):**

1. **ABSTENTION A: Sagittal plane not adequately imaged**
   - CONDITION: The series available are **only coronal and axial** (no sagittal), or sagittal images are **artifact-obscured, non-diagnostic, or motion-degraded**.
   - **REASON:** The ACL's **best visualization is the sagittal plane**; without sagittal views, **continuity assessment is severely limited**. Coronal and axial views are **perpendicular to the ACL's course** and provide **limited information on the ligament's continuity**. — DOMAIN, MRI anatomy
   - **WHAT WOULD RESOLVE IT:** Diagnostic sagittal T1 or PD images.
   - **CLASSIFICATION:** ABSTAIN; unprocessed information (missing series).

2. **ABSTENTION B: Artifact obscures the ligament**
   - CONDITION: Motion artifact, metal artifact, or field-inhomogeneity artifact obscures the **ACL region in all available series**.
   - **REASON:** The **measurement cannot be taken** if the signal is degraded. — Measurement theory
   - **WHAT WOULD RESOLVE IT:** High-quality images or sequences less sensitive to artifact (e.g., STIR instead of GRE).
   - **CLASSIFICATION:** ABSTAIN; unprocessed information (artifact).

3. **ABSTENTION C: Small, incomplete tear not visible at scanner resolution**
   - CONDITION: All imaged planes show **continuous, intact-looking ACL**, but **clinical examination or surgical findings confirm partial tear** (a posterior-sided tear, for example, or a tear in a region not traversed by the imaging plane).
   - **REASON:** The **resolution of the MRI scanner** may not be sufficient to detect **very small discontinuities**. The imaging protocol chosen (slice thickness, in-plane resolution) **determines the smallest visible tear**. — DOMAIN, MRI physics (voxel size, signal-to-noise)
   - **WHAT WOULD RESOLVE IT:** Higher-resolution sequences or 3D reconstructions with thin slices; clinical correlation.
   - **CLASSIFICATION:** ABSTAIN; unprocessed information (measurement not performed at required resolution).

---

### 1.5 Mimics and Confounders

**MIMIC 1: PCL (Posterior Cruciate Ligament) Misidentification in Coronal Plane**
- **What it looks like:** The **PCL, running posteriorly**, can be **confused with the ACL** in inexperienced review, especially in coronal images where the two may overlap. — DOMAIN
- **How to isolate:** The **ACL runs anteriorly (toward front of knee)**; the **PCL runs posteriorly (toward back)**. In **sagittal plane, the ACL is anterior to the PCL**. Tracing the ligament from its **tibial to femoral insertion** resolves the ambiguity. **The ACL inserts on the anterior intercondylar eminence; the PCL on the posterior eminence**. — DOMAIN, anatomy
- **Lens to discriminate:** Lens 4 & 5 (insertions) will show **distinct attachment sites**. A **true PCL lesion involves different anatomy**.
- **CLASSIFICATION:** Discriminable by systematic anatomical tracing; not a true confounder if insertion landmarks are read.

---

**MIMIC 2: ACL Remnant vs. Complete Tear**
- **What it looks like:** A **torn ACL may leave a short remnant**, still attached at one end (usually proximal/femoral), that can **appear as a "partial" or "incomplete" ACL**. — DOMAIN
- **How to isolate:** A **remnant is a retracted, non-functional stub**; it does **not span the entire intercondylar notch**. A **true partial tear has a continuous strand bridging tibia to femur**. Measurement of the **length of residual ligament** and **whether it reaches both attachments** resolves it. — DOMAIN
- **Lens to discriminate:** Lens 1 (continuity measured over the **full distance**) and Lens 6 (retraction) help; a remnant will show **discontinuity in the span or evidence of retraction**.
- **CLASSIFICATION:** Discriminable by full-length assessment; important for surgical planning but both are "abnormal" for the competition's binary label.

---

**MIMIC 3: Periligamentous Edema vs. Intrinsic ACL Injury**
- **What it looks like:** **Edema in the synovium or fat around the ACL**, from **effusion, synovitis, or hemorrhage from a meniscal injury**, can create the **appearance of ACL signal change**. — DOMAIN
- **How to isolate:** True **ACL edema is within the ligament substance**; periligamentous edema is **surrounding the ACL**. Careful **anatomical localization** on multiple planes and **high-resolution imaging** can distinguish. **Synovitis may be global (entire knee joint), whereas ACL edema is localized to the ligament**. — DOMAIN
- **Lens to discriminate:** Lens 3 (signal homogeneity) specifies **within-ligament vs. outside**. Lens 8 (joint effusion) can help: **global effusion without ACL changes suggests effusion alone**.
- **CLASSIFICATION:** Discriminable but requires careful plane-by-plane assessment; can be a **true confounder if only coronal or axial images available**.

---

**MIMIC 4: Prior ACL Reconstruction (ACLR) Graft vs. Native Tear**
- **What it looks like:** Patients with **prior ACLR have a surgical graft** in place of the native ACL. A **graft has a different signal** and appearance from a **native ligament**. A **graft can itself tear**, but the **anatomy is different**. — DOMAIN, orthopedic surgery
- **How to isolate:** A **prior ACLR graft** is often **thicker, has altered signal (from scar/fibrosis)**, and may have **tunnel widening** visible on axial/coronal views at the tibial and femoral tunnels. **Native ACL rupture has no tunnels**. Clinical history (not available at test time) would be definitive. — DOMAIN
- **Lens to discriminate:** Lens 2 (bulk) and Lens 3 (signal) can help: a **graft is thicker and has different signal from native ACL**. **Tunnel widening** would be visible on axial/coronal.
- **CLASSIFICATION:** Can be a **true confounder if no clinical history available**; distinguishable on anatomical grounds (tunnels, graft signal characteristics). **NOT expected at test time unless some test patients have prior surgery** (unknown from the facts provided).

---

**MIMIC 5: Mucoid Degeneration or Cystic Change in ACL**
- **What it looks like:** **Degenerative cystic changes within the ACL** can appear as **high-signal foci within the ligament on T2/STIR**, mimicking **edema or hemorrhage from a tear**. — DOMAIN, MRI pathology
- **How to isolate:** **True edema from acute tear is diffuse and associated with other acute findings** (effusion, hemorrhage, mechanical disturbance). **Cystic degeneration is localized to a cavity within the ligament**, often **without surrounding edema or mechanical signs**. **Chronicity** can be inferred from the **absence of acute signs**. — DOMAIN
- **Lens to discriminate:** Lens 3 (signal), Lens 1 (continuity), and Lens 8 (joint effusion) together: a **small high-signal cavity with intact continuity and no effusion suggests cyst, not tear**.
- **CLASSIFICATION:** Discriminable by **systematic assessment of associated findings**; requires **domain expertise to distinguish on imaging alone**.

---

### 1.6 Effects on Other Labels

**ACL Abnormality → Effusion (often increases)**
- **MECHANISM:** An **acute ACL tear typically causes hemarthrosis** (blood in the joint space). Blood raises the **total fluid volume in the joint**. — DOMAIN, orthopedic pathology
- **EFFECT:** If Effusion = yes, and ACL = yes, the **effusion is likely traumatic in origin** (ACL tear + hemarthrosis). If ACL = no, effusion may be from **other causes (meniscal tear, synovitis, OA)**. — DOMAIN
- **CLASSIFICATION:** **Explains away** effusion as a secondary finding of ACL injury; does not **reduce confidence in effusion**, but **explains its cause**.

---

**ACL Abnormality → Synovitis (may increase)**
- **MECHANISM:** **Acute ACL injury triggers inflammatory response** in the synovial membrane, causing **synovitis**. — DOMAIN
- **EFFECT:** ACL tear + Synovitis are often **co-present in acute injury**. If both are present, it **strengthens the interpretation** of acute inflammatory trauma. If ACL = yes and Synovitis = no, the **tear may be chronic (old, scarred, less inflammatory)**. — DOMAIN
- **CLASSIFICATION:** **Supports ACL diagnosis** when both are present (acute injury); absence of synovitis **does not reduce ACL confidence** (can be chronic).

---

**ACL Abnormality → Contusion (may increase)**
- **MECHANISM:** The **mechanism of injury** (pivoting, deceleration) that tears the ACL **often involves impact** between tibial and femoral condyles, causing **bone bruising (contusion)**. — DOMAIN, biomechanics
- **EFFECT:** ACL tear + Contusion may be **mechanically linked** (same injury event). Presence of contusion **strengthens the interpretation** of traumatic ACL injury. — DOMAIN
- **CLASSIFICATION:** **Supports ACL diagnosis** when both present; does **not reduce ACL confidence** if absent (contusion is optional).

---

**ACL Abnormality → Fracture (may be related, but not a tight link)**
- **MECHANISM:** An **ACL tear can be accompanied by fracture** (e.g., **tibial spine avulsion, femoral condyle fracture**). But **isolated ACL tears without fracture are very common**. — DOMAIN
- **EFFECT:** If ACL = yes and Fracture = yes (especially tibial spine), it **strongly supports traumatic ACL mechanism**. If ACL = yes and Fracture = no, it is **not diagnostic of anything**; most ACL tears have no fracture. — DOMAIN
- **CLASSIFICATION:** Fracture **supports ACL diagnosis** when present; absence **does not challenge ACL diagnosis**.

---

**ACL Abnormality → Medial Meniscus, Lateral Meniscus (independent)**
- **MECHANISM:** The **ACL and menisci are separate structures**, but they are **mechanically linked** in some injury patterns. An **ACL tear can occur with or without meniscal involvement**. Some **mechanisms (pivoting, cutting)** injure both. — DOMAIN
- **EFFECT:** If ACL = yes and Meniscus = yes, it suggests **complex, multi-ligament traumatic injury**. If ACL = yes and Meniscus = no, it is a **ligament-specific injury**. They **do not explain away each other**. — DOMAIN
- **CLASSIFICATION:** **Independent** diagnoses; co-occurrence is plausible but **not required**.

---

**ACL Abnormality → OA (may be related long-term)**
- **MECHANISM:** A **chronic, untreated ACL tear leads to instability**, which over time **damages cartilage and causes osteoarthritis** in one or more compartments. But **OA can also develop without ACL tear**. — DOMAIN, orthopedic natural history
- **EFFECT:** If ACL = yes (chronic) and OA = yes, it may **explain the OA as a consequence of chronic instability**. But **OA is not present in acute ACL tears** (OA takes years/decades to develop). So OA **does not make ACL more likely in acute cases**. In chronic cases, OA **may be a sequela**. — DOMAIN
- **CLASSIFICATION:** **May explain OA when both are present and chronicity suggests causation**; does not **directly change ACL confidence**.

---

**ACL Abnormality → MCL (may be related; "combined ligamentous injury")**
- **MECHANISM:** Some **injury mechanisms (e.g., valgus stress with internal rotation)** can damage **both ACL and MCL**. But **isolated ACL tears are common without MCL involvement**. — DOMAIN
- **EFFECT:** If ACL = yes and MCL = yes, it suggests **complex valgus-rotation injury**. If ACL = yes and MCL = no, it is **ACL-specific injury**. The two are **mechanically plausible together but not required**. — DOMAIN
- **CLASSIFICATION:** **Independent diagnoses**; co-occurrence is mechanically plausible but **not obligatory**.

---

### 1.7 What the Host Labels Confirm; Near Misses They Expose

**CONFIRMED CASES (ACL = 1 in training data):**
- **Count:** 24 studies labeled ACL = 1 (FACT, from 00_facts.md)
- **What they confirm:** These **24 labeled-positive studies represent the radiologist's read** that the ACL shows abnormality sufficient to **mark as 1 = abnormal**. Each **can be examined to see**:
  - **Which lenses fire?** (Continuity? Edema? Bulk change?)
  - **What is the pattern of findings?** (Complete tear + hemarthrosis? Chronic thinning? Avulsion?)
  - **Which paths (DEFINITIONAL vs. DIRECTIONAL) are engaged?**
  - **How consistent are the findings?** (All 24 show the same signature, or is there variation?)
- **Expected signature:** The 24 should mostly show **path 1A or 1B** (discontinuity + edema + mechanical signs, or avulsion). If many show **only Lens 2 or Lens 3 without Lens 1**, it suggests **the radiologist's threshold includes partial tears and edema-only injuries**.

---

**NEGATIVE CASES (ACL = 0 in training data):**
- **Count:** 34 studies labeled ACL = 0 (FACT)
- **What they confirm:** These **34 labeled-negative studies show** what the radiologist **did not mark as abnormal**. They are the **population reference** for normal anatomy. Each should show:
  - **Lens 1 = continuous**
  - **Lens 2 = normal bulk**
  - **Lens 3 = homogeneous signal, low on T2**
  - **Lenses 4, 5 = intact insertions**
  - **Lens 6 = normal linear course**
- **Expected signature:** Uniform normal appearance; any that show **edema (Lens 3) or bulk change (Lens 2) without continuity break** should be **examined carefully** — they may represent **near misses** (partial tears the radiologist did not mark, or truly normal variants).

---

**NEAR MISSES (Expected from label distribution):**

1. **Type A: Small partial tear, radiologist-missed**
   - **Picture:** Lens 1 = continuous, but Lens 2 = thinning, Lens 3 = edema, Lens 6 = subtle retraction
   - **Why it matters:** The **radiologist may have missed a small tear** if it is **not obvious on casual inspection**. This is a **false negative** in the training data (should be ACL = 1, but marked 0).
   - **What would expose it:** High-detail review of the 34 negative cases for **any showing Lens 2 or 3 abnormality**. Surgical or follow-up imaging would confirm.

2. **Type B: Chronic, healed ACL tear misidentified as normal**
   - **Picture:** Lens 1 = continuous but irregular, Lens 2 = marked thinning, Lens 3 = heterogeneous signal without bright edema
   - **Why it matters:** A **old, healed ACL tear is mechanically abnormal** (lax, non-functional) but may **appear "intact" on casual MRI assessment**. Radiologist may have called it "normal" if the discontinuity is not obvious. This is a **false negative**.
   - **What would expose it:** Clinical correlation (patient has physical exam findings of ACL laxity) or comparison to **healthy age-matched normal knees** (the chronic-tear ACL is thinner).

3. **Type C: Periligamentous edema without intrinsic ACL injury, radiologist-marked as abnormal**
   - **Picture:** Lens 1 = continuous, Lens 2 = normal, Lens 3 = signal change from **external edema (synovitis, meniscal tear), not ACL itself**, Lens 8 = effusion
   - **Why it matters:** **Synovitis or meniscal injury can create the appearance of ACL edema** if not carefully distinguished. Radiologist may have **marked ACL = 1 when the primary finding is meniscal or synovitis**, not ACL injury. This is a **false positive**.
   - **What would expose it:** Careful **plane-by-plane anatomical localization** of edema (within ACL vs. periligamentous). Surgical findings or imaging of the meniscus would confirm.

4. **Type D: Minor signal irregularity, radiologist-marked as normal**
   - **Picture:** Lens 3 = slight heterogeneity on T2 (borderline signal), Lenses 1, 2 = normal
   - **Why it matters:** **Very subtle edema or early degenerative change** may appear **minimally abnormal** and be **dismissed as normal variant**. This is a **borderline false negative**.
   - **What would expose it:** Clinical examination (positive Lachman test) or follow-up imaging showing progression to clear tear.

---

**SUMMARY: Host Labels as Teacher**

The **58 labeled studies (24 ACL = 1, 34 ACL = 0)** are the **teacher in the classical sense**: they **confirm or refute a structural path**. 

**Confirmations expected:**
- The **24 positive cases should show consistent signatures** (e.g., discontinuity + edema) across most or all.
- The **34 negative cases should show normal anatomy** across all lenses.

**Near misses expected:**
- The **34 negative cases likely contain some false negatives** (small tears missed), which would be **exposed by clinical review** or by **comparing their lenses to the 24 positive cases**.
- The **24 positive cases may include some false positives** (periligamentous edema from other sources), which would be **exposed by anatomical detail (exact localization of edema)**.

**Building the system:**
- Extract the **lenses from all 58 cases**.
- Compare the **distributions of Lens 1, 2, 3 between the 24 positive and 34 negative**.
- Identify **where the distributions overlap or separate**.
- Use that **separation** to refine the **decision thresholds (DEFINITIONAL vs. DIRECTIONAL)** and the **near-miss learning** (what combinations are borderline).

---

### 1.8 Open Questions for the Founder

1. **Scope of "ACL abnormality":** Does it include:
   - Only **complete tears and avulsions** (mechanically non-functional)? 
   - Also **partial tears** (some fibers torn, some intact)?
   - Also **chronic thinning and laxity without frank tear**?
   - Also **acute swelling and edema without visible discontinuity**?
   - **Clarification needed to anchor the DEFINITIONAL paths.**

2. **Radiological criterion level:** The 24 positive cases likely show varying **degrees of tear severity**. Should the system:
   - Assign **high confidence only to clear, complete tears** (small set)?
   - Assign **medium confidence to partial tears and edema** (larger set)?
   - **Abstain on subtle, borderline findings**?
   - **Clarification needed to set the warrant for DIRECTIONAL paths.**

3. **Imaging protocol sensitivity:** The available **sagittal T1 and T2 sequences** may not be sensitive to **very small, incomplete tears**. Should the system:
   - Assign **high confidence only to findings clearly visible on standard sequences**?
   - Expect **higher-resolution or special sequences** as part of the imaging protocol?
   - **Clarify the baseline imaging protocol used by the radiologist to generate the labels.**

4. **Chronic vs. acute distinction:** Should the system:
   - Distinguish **acute tear (with edema) from chronic tear (thin, scarred, no edema)**?
   - Output a **single binary "abnormality present/absent"** for both acute and chronic?
   - **Both are structurally abnormal; clarify whether the competition's label bundles them.**

5. **Coexistence with other findings:** When **ACL tear coexists with hemarthrosis (effusion) or synovitis or contusion**, should the system:
   - Use **the coexistence as strong evidence of traumatic mechanism**?
   - Or treat **ACL and effusion independently**?
   - **Clarification on whether a "committee" logic (all agree = higher confidence) applies.**

---

---

## 2. MCL (Medial Collateral Ligament)

### 2.1 Definition

**HOST'S WORDS:** MCL [FACT: column name from `sample_submission.csv`]

**DOMAIN EXPANSION:** The Medial Collateral Ligament is a broad, flat, extra-articular ligament on the medial (inner) side of the knee, running from the medial epicondyle of the femur to the medial tibia below the knee joint line, providing medial stability and restraint to valgus (outward) stress and external tibial rotation. An "MCL abnormality" in radiology refers to injury: **partial tear, complete tear, or acute/chronic signal abnormality indicating disruption of the ligament's continuity or integrity**. — DOMAIN

**SCOPE (QUESTION FOR FOUNDER):** Same as ACL: does "MCL abnormality" include:
- Complete tear?
- Partial tear?
- Chronic thinning or laxity?
- Acute sprain with edema?
- **Clarification needed.**

---

### 2.2 The Structural Reason It Can Be Diagnosed

**ANATOMY (DOMAIN):**
- **Location:** The MCL is a broad, flat ligament on the **medial (inner) aspect of the knee**, distinct from the **ACL and PCL which are intra-articular**. The MCL is **extra-articular** (outside the joint capsule in most of its course). — DOMAIN, anatomy
  - **Proximal attachment:** **Medial epicondyle of the femur** (at the posteromedial corner, slightly posterior to the medial condyle center)
  - **Distal attachment:** **Medial tibia, 4–6 cm below the knee joint line**, spreading over the medial tibial shaft
  - **Course:** Runs **vertically and slightly posteriorly** from femur to tibia, **parallel to the tibial shaft** in the coronal plane. — DOMAIN
- **Structure:** The MCL is composed of **two layers**: 
  - **Superficial MCL (sMCL):** The main, broad band
  - **Deep MCL (dMCL):** Fibers attaching to the joint capsule and medial meniscus (meniscofemoral and meniscotibial ligaments)
  - **The competition's label "MCL" likely refers to the superficial MCL**, which is the **dominant, primary restraint**. — DOMAIN

- **Appearance on MRI:** On **T1 and PD sequences**, the MCL appears as a **linear, low-signal band** on the **medial side of the knee**. It is best visualized in the **coronal plane**, where it runs **vertically from femoral to tibial attachment**. In the **sagittal plane**, the MCL may be seen at the **medial margin** of the knee, but is less clearly delineated than in coronal. — DOMAIN, MRI anatomy

**MRI PHYSICS (DOMAIN):**
- **T1-weighted sequences:** MCL = low signal (organized collagen), **bright fat on either side**. — DOMAIN
- **PD (proton density):** Intermediate signal from MCL, **good T1/T2 contrast** with surrounding fat and muscle. — DOMAIN
- **T2-weighted (T2 FSE, T2 SE):** MCL = low signal; **edema or hemorrhage = bright**. — DOMAIN
- **STIR or T2 TIRM (fat-suppressed, T2-weighted):** MCL = dark; **edema = bright**. Very **sensitive to edema and hemorrhage**. — DOMAIN
- **Gradient echo (GRE):** Sensitive to **susceptibility from hemorrhage**. Acute hematoma = **signal loss, phase artifact**. — DOMAIN

**MECHANICS OF INJURY (DOMAIN):**
- **Mechanism:** The MCL is stressed by **valgus stress** (pushing the knee outward, opening the medial side). Common mechanisms include **landing, cutting, or direct blow to the lateral knee**. It is also stressed by **external tibial rotation** (turning the tibia outward). — DOMAIN
- **Acute injury:** A **torn MCL has separating fibers, edema, and hemorrhage**. The ligament may show a **partial tear (fibers disrupted but some intact) or complete tear (full separation)**. — DOMAIN
- **Chronic injury:** **Healed MCL tears may show thinning, scarring, and laxity**. — DOMAIN
- **Visibility in MRI:** A **continuous, uniform band of low signal** is normal MCL. A **gap, disruption, swelling, or high-signal infiltration** indicates abnormality. The **coronal plane is the single best view**. — DOMAIN

---

### 2.3 The Thermometers (Lenses)

#### Lens 1: MCL Continuity in Coronal Plane

**FACT:** Binary assessment of whether the MCL appears as a **continuous, uninterrupted linear band** from femoral to tibial attachment, or shows a **gap, separation, or disruption**. — DOMAIN

**SITE:** The medial side of the knee, from **medial epicondyle of femur** to **medial tibia below the knee joint line**. The measurement is taken in the **coronal plane**. — DOMAIN, anatomy

**SERIES:**
- **Primary:** Coronal T1 or PD. Standard sequences include **PD TSE**, **T1 SE**, or **3D-VIBE** reconstructed in coronal. — DOMAIN
- **Secondary:** Coronal T2 or STIR for edema confirmation. — DOMAIN
- Note from FACTS: All coronal series in training set are either (FS=0, FAT_SUP=0) or (FS=1, FAT_SUP=1). — FACT

**CALIBRATION:** In a normal knee, the MCL is **always continuous** from proximal to distal attachment. Any **gap or discontinuity is abnormal by definition** in a normal-knee population. — DOMAIN

**WHAT IT MEASURES:** **Continuity of the MCL band: yes or no.** Does **not measure the degree of tear, or signal change**, only **structural interruption**. — DOMAIN

**WARRANT:** **WIDE LENS.** A **continuous MCL rejects severe tear** but not partial tear. A **discontinuous MCL indicates tear** and is rare in normal population (SnNout). — DOMAIN

---

#### Lens 2: MCL Bulk (Thickness and Integrity)

**FACT:** Assessment of whether the MCL **maintains normal bulk (width) and uniform cross-section**, or shows **thinning, swelling, fraying, or irregularity**. — DOMAIN

**SITE:** Same as Lens 1: the **medial band measured in coronal plane**, assessing **proximal 1/3, middle 1/3, distal 1/3**. — DOMAIN

**SERIES:** Coronal T1 or PD. The **width of the MCL band** (perpendicular to its long axis) is measured. Normal MCL is approximately **3–8 mm wide** (in coronal view, the full thickness of the ligament). — DOMAIN

**CALIBRATION:** Normal MCL = **uniform, 3–8 mm**. Thinning below 2 mm or swelling above 10 mm is abnormal. Chronic tears = thin and frayed. Acute tears = locally swollen or gapped. — DOMAIN

**WHAT IT MEASURES:** **Structural integrity and homogeneity**. Thin, frayed, or locally swollen MCL = degeneration, partial tearing, or healing scarring. — DOMAIN

**WARRANT:** **DIRECTIONAL FOR tear; narrow warrant (SpPin) if markedly thinned or swollen.** Thinning suggests chronic injury; swelling suggests acute. — DOMAIN

---

#### Lens 3: MCL Signal Homogeneity

**FACT:** Assessment of whether the MCL shows **uniform, low signal** or **heterogeneous, mixed, or high-signal foci within the ligament**. — DOMAIN

**SITE:** The entire MCL band, coronal plane. — DOMAIN

**SERIES:**
- **Primary:** Coronal T1 or PD. Normal = low signal. Heterogeneity = patches of higher signal. — DOMAIN
- **Confirmatory:** Coronal T2 or STIR. Normal = low signal. Edema/hemorrhage = HIGH signal. — DOMAIN

**CALIBRATION:** Normal MCL = homogeneous, low on T1 and PD, remaining low on T2. Any **high-signal focus on T2/STIR is abnormal**. — DOMAIN

**WHAT IT MEASURES:** **Edema, hemorrhage, or intrinsic degeneration**. Acute tears show **bright signal on STIR/T2** from edema/blood. Chronic tears may show **cystic change or signal heterogeneity**. — DOMAIN

**WARRANT:** **DIRECTIONAL FOR acute tear.** High-signal edema is suggestive of acute injury; not specific (can be from inflammation). — DOMAIN

---

#### Lens 4: MCL Femoral Attachment Integrity

**FACT:** Assessment of whether the MCL's **proximal (femoral) attachment is intact**, or shows **gap, edema, or avulsion at the medial epicondyle**. — DOMAIN

**SITE:** The **medial epicondyle of the femur**, coronal and sagittal planes. — DOMAIN

**SERIES:** Coronal T1, T2, and sagittal T1, T2. The attachment is visualized at the **posteromedial corner of the femur**. — DOMAIN

**CALIBRATION:** Normal = continuous attachment without gap or edema. — DOMAIN

**WHAT IT MEASURES:** **Femoral attachment integrity**. Edema or separation at the epicondyle indicates **proximal attachment injury**. — DOMAIN

**WARRANT:** **DIRECTIONAL FOR tear, proximal.** Edema/separation is suggestive. — DOMAIN

---

#### Lens 5: MCL Tibial Attachment Integrity

**FACT:** Assessment of whether the MCL's **distal (tibial) attachment is intact**, or shows **gap, edema, or avulsion at the medial tibia**. — DOMAIN

**SITE:** The **medial tibia, 4–6 cm below the knee joint line**, where the MCL fans out over the tibial shaft. Coronal and sagittal views. — DOMAIN

**SERIES:** Coronal T1, T2; sagittal T1, T2. — DOMAIN

**CALIBRATION:** Normal = continuous without gap. — DOMAIN

**WHAT IT MEASURES:** **Distal attachment integrity**. MCL avulsions at the tibia are **less common than femoral, but do occur**. — DOMAIN

**WARRANT:** **DIRECTIONAL FOR tear, distal.** — DOMAIN

---

#### Lens 6: MCL-Associated Edema in Medial Joint Space and Subsynovial Region

**FACT:** Assessment of whether there is **edema or hemorrhage in the region immediately surrounding the MCL**, in the **subsynovial fat** or **medial joint capsule**. — DOMAIN

**SITE:** The medial side of the knee, **adjacent to the MCL**, in the **coronal and sagittal planes**. — DOMAIN

**SERIES:**
- **Primary:** Coronal T2 or STIR (shows edema as bright signal). — DOMAIN
- **Secondary:** Sagittal T2 or STIR. — DOMAIN

**CALIBRATION:** In a normal knee, there is **minimal or no high-signal edema** in the MCL region. Any **bright signal (edema/hemorrhage) surrounding the MCL indicates inflammation or bleeding from injury**. — DOMAIN

**WHAT IT MEASURES:** **Acute inflammatory response or hemorrhage associated with MCL injury**. Acute tears show **extensive periligamentous edema and blood**. Chronic tears have **less edema**. — DOMAIN

**WARRANT:** **DIRECTIONAL FOR acute MCL injury.** High-signal edema is suggestive of recent tear. — DOMAIN

---

#### Lens 7: Medial Meniscal Root Edema and Proximity to MCL

**FACT:** Assessment of whether the **medial meniscal root (posterior attachment of the medial meniscus) shows edema or is displaced**, and whether this is **associated with MCL findings**. — DOMAIN

**SITE:** The **posteromedial joint space**, where the **medial meniscal root attaches to the medial tibia**. — DOMAIN

**SERIES:** Coronal T1, T2; sagittal T1, T2. — DOMAIN

**CALIBRATION:** Normal = medial meniscal root is intact at the tibial attachment, no edema. — DOMAIN

**WHAT IT MEASURES:** **Secondary effect of MCL injury or associated medial capsular injury**. The MCL, meniscal root attachment, and joint capsule are **anatomically linked**; injury to one can affect the others. **Edema at the root may indicate capsular injury or meniscal root tear** concomitant with MCL injury. — DOMAIN

**WARRANT:** **DIRECTIONAL FOR MCL injury, but non-specific (wide lens).** Meniscal root edema can occur **independently of MCL**, so it is supportive but **not diagnostic of MCL alone**. — DOMAIN

---

#### Lens 8: Valgus Stress Response or Lateral Compartment Changes (Indirect Evidence)

**FACT:** Assessment of whether there are **secondary findings on the lateral side of the knee** (e.g., **lateral ligament strain, lateral compartment joint space changes, lateral femoral condyle contusion**) that would suggest **valgus stress injury mechanism**, which would **support MCL injury as part of the injury pattern**. — DOMAIN

**SITE:** The **lateral side of the knee**, including **lateral ligaments, lateral compartment, lateral femoral condyle**. — DOMAIN

**SERIES:** Coronal T1, T2. — DOMAIN

**CALIBRATION:** In a pure **valgus injury mechanism**, there may be **secondary findings on the lateral side** (e.g., **lateral ligament strain, lateral compartment cartilage contact/changes**). However, MCL injury can occur **without lateral findings** (isolated valgus stress), so **absence of lateral findings does not rule out MCL injury**. — DOMAIN

**WHAT IT MEASURES:** **Injury mechanism and energy distribution**. Lateral findings support a **valgus mechanism** but are **not required for MCL diagnosis**. — DOMAIN

**WARRANT:** **DIRECTIONAL FOR MCL, but low warrant (weak support).** Lateral findings may co-occur but are **not essential** and are **non-specific** (can be from other mechanisms). — DOMAIN

---

### 2.4 Decision Paths: MCL Abnormality

**DEFINITIONAL ASSIGNMENTS:**

1. **DEFINITIONAL PATH A: Complete MCL tear with clear structural signs**
   - AND: Lens 1 (MCL Continuity) = **discontinuous** (gap visible)
   - AND: Lens 3 (Signal Homogeneity) = **high-signal edema on STIR/T2**
   - AND: At least one of: Lens 4 or 5 (attachment-site edema/gap), Lens 6 (periligamentous edema)
   - **LAW:** In a normal knee, an **MCL cannot simultaneously be discontinuous AND have edema AND show attachment-site involvement**. The conjunction is **diagnostically sufficient for complete tear**. — DOMAIN
   - **CLASSIFICATION:** DEFINITIONAL (T=1 for MCL abnormality)

2. **DEFINITIONAL PATH B: MCL avulsion with bony involvement**
   - AND: Lens 4 or 5 = **visible femoral or tibial avulsion (bone fragment, displaced attachment)**
   - AND: Lens 1 = **discontinuous or abnormal**
   - **LAW:** MCL **avulsion with bony fragment is mechanically incompatible with normal function** and is **unambiguously abnormal**. — DOMAIN
   - **CLASSIFICATION:** DEFINITIONAL

---

**STRICT EXCLUSION:**

1. **STRICT EXCLUSION PATH: Normal MCL Anatomy**
   - AND: Lens 1 = **continuous, uninterrupted band from femur to tibia**
   - AND: Lens 2 = **normal, uniform width (3–8 mm)**
   - AND: Lens 3 = **homogeneous, low signal on all sequences**
   - AND: Lens 4 and 5 = **intact attachments without edema**
   - **LAW:** An MCL satisfying all criteria is **anatomically normal by definition**. — DOMAIN
   - **LOGIC:** "All anatomy normal AND all signal normal" → "not abnormal" by **conjunction of five negative readings**. However, this is a **wide lens**: does **not exclude very small, incomplete tears not visible at the resolution imaged**.
   - **CLASSIFICATION:** STRICT EXCLUSION of complete/large tear; abstains on very small tears.

---

**DIRECTIONAL FOR:**

1. **DIRECTIONAL FOR PATH: Acute partial tear or edema**
   - AND: Lens 1 = **continuous or borderline discontinuous**
   - AND: Lens 2 = **thinning or focal swelling**
   - AND: Lens 3 = **high-signal edema on T2/STIR**
   - **REASON:** Acute partial tears show **edema and bulk changes but may not show frank discontinuity** if incomplete. Edema is an **inflammatory marker**. — DOMAIN
   - **STRENGTH:** Moderate-to-strong; MCL edema is **typically associated with injury**. — DOMAIN
   - **CLASSIFICATION:** DIRECTIONAL FOR

2. **DIRECTIONAL FOR PATH: Chronic partial tear or scarring**
   - AND: Lens 1 = **continuous but irregular**
   - AND: Lens 2 = **marked thinning**
   - AND: Lens 3 = **heterogeneous signal, no bright edema**
   - **REASON:** Chronic tears have healed as scar; ligament is **thin and weak but may appear continuous**. — DOMAIN
   - **STRENGTH:** Moderate; suggests **prior tear now scarred**. — DOMAIN
   - **CLASSIFICATION:** DIRECTIONAL FOR

3. **DIRECTIONAL FOR PATH: Attachment-site injury**
   - AND: Lens 4 or 5 = **edema or gap at attachment**
   - AND: Lens 1 or 2 = **otherwise relatively intact**
   - **REASON:** Insertion injury without midsubstance disruption. — DOMAIN
   - **STRENGTH:** Moderate. — DOMAIN
   - **CLASSIFICATION:** DIRECTIONAL FOR

---

**DIRECTIONAL AGAINST:**

1. **DIRECTIONAL AGAINST PATH: Normal signal and continuity**
   - AND: Lens 1 = **continuous**
   - AND: Lens 3 = **homogeneous, low signal on T2 (no edema)**
   - **REASON:** **Continuous MCL with normal signal is the common finding in uninjured knees**. Absence of edema argues **against acute injury**. — DOMAIN
   - **STRENGTH:** Moderate; does **not exclude chronic tear or small partial tear**. — DOMAIN
   - **CLASSIFICATION:** DIRECTIONAL AGAINST

---

**ABSTENTION:**

1. **ABSTENTION A: Coronal plane not adequately imaged**
   - CONDITION: Series available are **only sagittal and axial** (no coronal), or coronal images are **artifact-obscured or non-diagnostic**.
   - **REASON:** The **MCL's best visualization is the coronal plane**. Without coronal views, **continuity assessment is severely limited**. — DOMAIN
   - **WHAT WOULD RESOLVE IT:** Diagnostic coronal T1 or PD images.
   - **CLASSIFICATION:** ABSTAIN; unprocessed information (missing series).

2. **ABSTENTION B: Artifact obscures the ligament**
   - CONDITION: Motion, metal, or field artifact obscures the **MCL in all available series**.
   - **REASON:** Measurement cannot be taken. — DOMAIN
   - **WHAT WOULD RESOLVE IT:** High-quality images.
   - **CLASSIFICATION:** ABSTAIN.

3. **ABSTENTION C: Small, incomplete tear not visible**
   - CONDITION: All imaged planes show **continuous, intact-looking MCL**, but **clinical examination or imaging confirms partial tear**.
   - **REASON:** MRI resolution may not detect **very small gaps**. — DOMAIN
   - **WHAT WOULD RESOLVE IT:** Higher-resolution sequences.
   - **CLASSIFICATION:** ABSTAIN.

---

### 2.5 Mimics and Confounders

**MIMIC 1: Medial Joint Effusion vs. MCL Edema**
- **What it looks like:** **Joint effusion in the medial recess of the knee** can appear as **high-signal fluid near the MCL** on T2/STIR, mimicking **MCL edema**. — DOMAIN
- **How to isolate:** **True MCL edema is within the ligament substance or surrounding subsynovial fat**. **Joint effusion is typically within the joint capsule space** and has a **smooth, rounded margin** (fluid outline). **MCL edema is more infiltrative** and extends into the **medial musculature**. Careful **anatomical localization** on **multiple planes** can distinguish. — DOMAIN
- **Lens to discriminate:** Lens 3 (is the high signal **within the MCL or adjacent to it?**). Lens 6 (periligamentous edema specifically). Lens 8 (global effusion vs. localized).
- **CLASSIFICATION:** Discriminable with careful assessment.

---

**MIMIC 2: Medial Meniscal Root Edema or Meniscal Tear vs. MCL Tear**
- **What it looks like:** **Edema or tear of the medial meniscal root** (which attaches near the MCL insertion) can appear as **edema in the medial joint space**, mimicking **MCL injury**. — DOMAIN
- **How to isolate:** The **medial meniscal root is a distinct structure** within the joint. **MCL is a ligament on the medial side**. A **meniscal root tear would show continuity disruption of the root itself** (visible on coronal and sagittal), and the **edema would be more localized to the meniscal attachment**. The **MCL can be normal** even with meniscal root pathology. — DOMAIN
- **Lens to discriminate:** Lens 1 (MCL continuity can be normal with meniscal root injury). Lens 7 (assesses meniscal root separately). Meniscal lenses (not in this ACL/MCL report).
- **CLASSIFICATION:** Discriminable by focusing on **MCL-specific findings**; requires meniscal assessment in tandem.

---

**MIMIC 3: Medial Collateral Ligament Reconstruction vs. Native Tear**
- **What it looks like:** Prior **MCL reconstruction (rare; less common than ACL reconstruction)** would have a **different appearance and anatomy**. — DOMAIN
- **How to isolate:** **Prior surgery would be visible as tunnel widening, graft signal**, or **surgical scars**. Clinical history (not available) would clarify. — DOMAIN
- **Lens to discriminate:** Lens 2 (bulk) and Lens 3 (signal) — a graft would have **different signal** than native MCL. **Tunnels** visible on axial/coronal.
- **CLASSIFICATION:** Can be a confounder if **no clinical history available**; **not expected at test time unless test has prior MCL surgery**.

---

**MIMIC 4: Muscle Edema (Medial Musculature) vs. MCL Edema**
- **What it looks like:** **Edema in the medial thigh musculature** (e.g., gracilis, semitendinosus) adjacent to the MCL can appear as **high-signal near the MCL** on T2/STIR. — DOMAIN
- **How to isolate:** **Muscle edema is within muscle (intramuscular)**; **MCL edema is in the ligament or subsynovial fat**. The **two have different anatomical distributions**. **Careful plane-by-plane assessment** can localize the edema. — DOMAIN
- **Lens to discriminate:** Lens 6 (specifically periligamentous edema, distinct from intramuscular edema).
- **CLASSIFICATION:** Discriminable by **careful anatomical assessment**.

---

### 2.6 Effects on Other Labels

**MCL Abnormality → Effusion (may increase)**
- **MECHANISM:** **Acute MCL tear causes hemarthrosis**; blood raises **total joint fluid**. — DOMAIN
- **EFFECT:** MCL = yes + Effusion = yes → **traumatic injury mechanism (MCL tear + hemarthrosis)**. Explains effusion as secondary. — DOMAIN
- **CLASSIFICATION:** **Explains away** effusion; **supports MCL diagnosis**.

---

**MCL Abnormality → Synovitis (may increase)**
- **MECHANISM:** **Acute MCL injury triggers inflammatory response** in the synovial membrane. — DOMAIN
- **EFFECT:** MCL = yes + Synovitis = yes → **acute injury**. Absence of synovitis suggests **chronic**. — DOMAIN
- **CLASSIFICATION:** **Supports MCL diagnosis** when co-present.

---

**MCL Abnormality → ACL (may be related, but independent)**
- **MECHANISM:** Some **injury mechanisms (valgus + rotation)** damage **both MCL and ACL**. But they can be **injured independently**. — DOMAIN
- **EFFECT:** MCL = yes + ACL = yes → **complex ligamentous injury**. MCL = yes + ACL = no → **MCL-specific injury**. — DOMAIN
- **CLASSIFICATION:** **Independent diagnoses**; co-occurrence is mechanically plausible but **not required**.

---

**MCL Abnormality → Medial Meniscus (may be related)**
- **MECHANISM:** The **medial meniscal root and capsule are anatomically linked to the MCL**. Some **injury mechanisms injure both**. — DOMAIN
- **EFFECT:** MCL = yes + Medial Meniscus = yes → **medial-sided ligamentous and meniscal injury**. MCL = yes + Medial Meniscus = no → **ligament-specific**. — DOMAIN
- **CLASSIFICATION:** **May explain meniscal injury** if both co-present; **independent otherwise**.

---

**MCL Abnormality → Contusion, Fracture (may be related)**
- **MECHANISM:** The **valgus stress mechanism** that tears the MCL can also cause **bone bruising (contusion)** and sometimes **fracture** on the medial or lateral side. — DOMAIN
- **EFFECT:** MCL = yes + Contusion/Fracture = yes → **traumatic mechanism**. Supports **MCL as part of injury pattern**. — DOMAIN
- **CLASSIFICATION:** **Supports MCL diagnosis** when co-present; **does not reduce MCL confidence** if absent.

---

**MCL Abnormality → OA (may be related long-term)**
- **MECHANISM:** **Chronic, untreated MCL tear causes medial instability**, leading to **cartilage damage and medial OA over time**. — DOMAIN
- **EFFECT:** MCL = yes (chronic) + Medial OA = yes → **MCL injury may have caused OA**. But OA takes **years/decades to develop**; acute MCL tears do **not immediately show OA**. — DOMAIN
- **CLASSIFICATION:** **May explain OA** in chronic cases; **does not directly change MCL confidence** in acute cases.

---

### 2.7 What the Host Labels Confirm; Near Misses They Expose

**CONFIRMED CASES (MCL = 1):**
- **Count:** 9 studies labeled MCL = 1 (FACT)
- **What they confirm:** These **9 positive cases represent the radiologist's reads** of MCL abnormality. Each should show:
  - **Which lenses fire?** (Continuity? Edema? Bulk change?)
  - **What is the signature pattern?** (Complete tear + hemarthrosis? Chronic thinning? Attachment injury?)
  - **Which decision paths are engaged?** (DEFINITIONAL vs. DIRECTIONAL)
- **Expected signature:** The 9 should mostly show **path 1A** (discontinuity + edema + attachment involvement). If many show **only Lens 2 or Lens 3 without Lens 1**, it suggests **radiologist's threshold includes partial tears and edema-only**.

---

**NEGATIVE CASES (MCL = 0):**
- **Count:** 49 studies labeled MCL = 0 (FACT)
- **What they confirm:** These **49 negative cases** are the **population reference** for normal MCL anatomy. Each should show:
  - **Lens 1 = continuous**
  - **Lens 2 = normal bulk**
  - **Lens 3 = homogeneous, low signal on T2**
  - **Lenses 4, 5 = intact attachments**

---

**NEAR MISSES:**

1. **Type A: Small partial tear, radiologist-missed**
   - **Picture:** Lens 1 = continuous, but Lens 2 = thinning, Lens 3 = edema, Lens 6 = periligamentous edema
   - **Why it matters:** **False negative** (should be MCL = 1, marked 0). **Small tears may be missed** on casual inspection. — DOMAIN
   - **What would expose it:** Detailed review of the 49 negative cases for **any showing Lens 2 or 3 abnormality**.

2. **Type B: Chronic, healed MCL tear misidentified as normal**
   - **Picture:** Lens 1 = continuous but irregular, Lens 2 = marked thinning, Lens 3 = heterogeneous without bright edema
   - **Why it matters:** **False negative** (mechanically abnormal, but labeled "normal"). Old, healed tear is lax but appears "intact" on casual review. — DOMAIN
   - **What would expose it:** Clinical correlation or **comparison to healthy age-matched normals**.

3. **Type C: Periligamentous edema without intrinsic MCL injury, marked as abnormal**
   - **Picture:** Lens 1 = continuous, Lens 2 = normal, Lens 3 = high signal **from external edema (meniscal tear, synovitis)**, not MCL itself
   - **Why it matters:** **False positive** (MCL normal, but radiologist marked MCL = 1 due to mislocalization of edema). — DOMAIN
   - **What would expose it:** Careful **anatomical localization** of edema (within MCL vs. periligamentous).

---

### 2.8 Open Questions for the Founder

1. **Scope of "MCL abnormality":** Same as ACL. Does it include:
   - Complete tears?
   - Partial tears?
   - Chronic thinning/laxity?
   - Acute swelling without discontinuity?
   - **Clarification needed.**

2. **MCL-specific vs. medial capsule:** The MCL is distinct from the **medial joint capsule** and **medial meniscal attachments**. Does the label:
   - Include **only native MCL pathology**?
   - Also include **capsular injuries and root injuries?**
   - **Clarification on scope.**

3. **Superficial vs. deep MCL:** The MCL has **two layers** (superficial and deep). Does the label:
   - Refer to **only the superficial MCL** (primary restraint, visible on standard imaging)?
   - Or include **deep MCL and capsular structures?**
   - **Clarification on anatomical scope.**

4. **Radiological criterion:** The **9 positive cases** likely show varying severity. Should the system:
   - Assign **high confidence only to clear, complete tears?**
   - Assign **medium confidence to partial tears and edema?**
   - **Abstain on subtle, borderline findings?**
   - **Clarification needed.**

5. **Low prevalence of positive cases:** Only **9 out of 58 labeled studies (15.5%) are MCL = 1**, compared to **24/58 (41.4%) for ACL**. This suggests:
   - **MCL injuries are rarer in this cohort** (plausible; ACL injury is more common in modern sports injury patterns).
   - **Or the radiologist's threshold for MCL is more strict** (only obvious tears marked; subtle MCL changes not marked).
   - **Clarification on radiologist's criteria and population makeup.**

---

---

## 3. Summary: Ligament Lenses as a Foundation

The **lenses derived above** for ACL and MCL form a **complete, objective measurement framework**. Together, they answer:

1. **What can be measured?** — Eight lenses per ligament, measuring objective facts (continuity, bulk, signal, attachment integrity, secondary signs).

2. **At what sites?** — Registered anatomical sites (ACL in the intercondylar notch; MCL on the medial side), in specific imaging planes.

3. **Calibrated against what?** — The population of normal knees (the 34 ACL = 0 and 49 MCL = 0 studies, plus unlabeled studies).

4. **What do they combine into?** — Decision paths: DEFINITIONAL (strict warrant), DIRECTIONAL (suggestive), and STRICT EXCLUSION (rule-out). Also ABSTAIN (missing information).

5. **What are the confounders?** — Periligamentous edema, meniscal root pathology, muscle edema, periarticular structures. All discriminable with systematic anatomical assessment.

6. **What next?** — The **host labels (24 ACL = 1, 34 ACL = 0, 9 MCL = 1, 49 MCL = 0)** confirm or refute each path. The **near-miss analysis** will expose **which lenses separate the two groups** and where **the radiologist's threshold lies**.

This **foundation** enables the next steps:

- **Building the lenses:** Extract lens readings from all labeled studies and build their **distributions**.
- **Refining the paths:** Use the **distributions to set decision thresholds** (at what confidence does the path fire?).
- **Teaching the agencies:** Each finding (ACL, MCL) is an agency; it **learns the paths from the host labels and teaches itself** on the 58 cases.
- **Testing on the 3 test studies:** The system will **read the test series, extract lenses, fire paths, and assign confidence scores** [0, 1] for each finding.

---

## Appendix: Sequence and Plane Coverage

**What the training data provides (FACT):**

| Plane | Fluid-Sensitive | Fat-Suppression | Count |
|---|---|---|---|
| Sagittal | 0 | 0 | 5,197 |
| Sagittal | 1 | 1 | 4,667 |
| Coronal | 0 | 0 | 3,985 |
| Coronal | 1 | 1 | 4,624 |
| Axial | 0 | 0 | 1,179 |
| Axial | 1 | 1 | 4,719 |

**Sagittal (9,864 series, 39.9% of training data):**
- **Sagittal FS=0 (standard T1/PD):** ACL best plane; MCL visible at margin
- **Sagittal FS=1 (T2/STIR):** Edema assessment for both ligaments

**Coronal (8,609 series, 35.3%):**
- **Coronal FS=0 (standard T1/PD):** MCL best plane; ACL visible
- **Coronal FS=1 (T2/STIR):** Edema assessment

**Axial (5,898 series, 24.1%):**
- **Axial FS=0 (standard T1/PD):** Cross-sectional view; attachment sites
- **Axial FS=1 (T2/STIR):** Edema at attachment level

**Coverage at test time (FACT):** 3 studies, 15 series total (~5 per study), distributed across sagittal, coronal, axial. **Exact breakdown not visible in facts.** All series are either (FS=0, FAT_SUP=0) or (FS=1, FAT_SUP=1).

**Implications:**
- **Sagittal and coronal planes are both available** (39.9% + 35.3% = 75.2% of training data).
- **Axial is available but less common** (24.1%), and may have **limited diagnostic value for ACL and MCL**.
- **Both standard (FS=0) and fluid-sensitive (FS=1) series are available**, enabling **continuity assessment and edema assessment**.
- **At test time, the system must work with whatever mix of series is available** (likely both sagittal and coronal, possibly axial, in both sequence types).

---

**End of Report**

Status: Ready for founder's ruling on scope, meaning, warrant, and radiological criteria for ACL and MCL abnormality. All structural paths, lenses, and near-miss learning hinge on these clarifications.

