# Joint-Level Findings: Lenses and Diagnostic Paths

**Wave 1 Report: Medial OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's, Contusion, Fracture**

*Status:* PROPOSALS for the founder's ruling. No finding is yet pinned.

---

## Overview

The 8 joint-level findings differ from ligament and meniscal injuries: they are compartmental (OA in specific chambers), fluid-space features (effusion, synovitis), capsular (Baker's), or traumatic bone/soft-tissue changes (contusion, fracture). Each is a conjunction of simple thermometer readings—measurements at registered sites, calibrated against the normal-knee population.

**Data available:**
- 58 labeled studies (1.3% of 4407 training).
- Label distribution: ranging from 21 pos (PF OA) to 9 pos (MCL) in labeled subset.
- Series: Sagittal, Coronal, Axial (Fluid-Sensitive 0/1, Fat-Suppressed 0/1).
- Reports: Free text, radiologist-written, in multiple languages. Test set has no reports.

**Method:** For each finding, restate (i) its host definition, (ii) the radiological and anatomical basis for diagnosis, (iii) the thermometers (one objective reading per site), (iv) the paths (which conjunctions assign, which exclude, which are directional), (v) confounders and near misses, (vi) interactions with other labels, (vii) what the host labels confirm.

---

## 1. MEDIAL OA (Medial Compartment Osteoarthritis)

### 1.1 Definition

**Host definition (FACT):** Not explicitly provided by competition. **Domain reading:** Degenerative changes in the medial tibiofemoral compartment, characterized by cartilage loss, osteophytes, joint space narrowing, and/or subchondral bone changes on the medial (inner) side of the knee joint.

**Scope (PROPOSAL):** The medial tibiofemoral compartment includes the medial femoral condyle and medial tibial plateau. The patellofemoral joint (medial facet) is separate (PF OA). The medial meniscus injury is a distinct label; OA is degeneration of the underlying bone and cartilage.

### 1.2 Structural Reason

**Anatomy (DOMAIN):**
- **Medial compartment:** Bounded by medial femoral condyle (superior), medial tibial plateau (inferior), medial capsule and MCL (medial wall).
- **Cartilage:** Thin hyaline layer on articular surfaces. In OA, cartilage thins, fibrillates, and erodes, exposing subchondral bone.
- **Osteophytes:** Bony spurs at joint margins, a hallmark of OA. Form at load-bearing edges.
- **Subchondral changes:** Sclerosis (bone hardening), cyst formation, marrow edema in early/active OA.
- **Joint space:** The gap between femoral and tibial cartilage. Narrowing indicates cartilage loss.

**MR Physics (DOMAIN):**
- **T2-weighted (Fluid-Sensitive):** Cartilage appears intermediate-to-high signal; degenerative loss shows thinning, fibrillation (signal intensity changes), or complete loss.
- **T1-weighted (standard):** Cartilage appears as low-signal line; loss makes the line thinner or absent.
- **Fat-suppressed (FS=1):** Suppresses fat, enhances visibility of fluid, edema, and cartilage interfaces.
- **Sagittal plane:** Best for viewing medial condyle profile, cartilage thickness, osteophytes on the medial edge.
- **Coronal plane:** Visualizes medial tibial plateau, compartment width, osteophytes on medial femoral condyle summit.
- **Axial plane:** Shows medial facet of femur, medial tibial margin, less commonly used for OA staging.

**Mechanics of degeneration (DOMAIN):**
- OA is a degenerative condition, not typically acute or traumatic (though trauma can accelerate it).
- Develops over time, correlates with age, prior meniscal injury, and mechanical stress.
- Cartilage loss is progressive; mild (early) to severe (advanced).

### 1.3 Thermometers (Lenses)

Each lens measures one objective quantity at a registered site. All are calibrated against the population of normal (OA-negative) knees at the same site and sequence.

| # | Lens Name | Site | Series/Plane | Measurement | Calibration | Notes |
|---|-----------|------|--------------|-------------|-------------|-------|
| M1 | Medial Cartilage Thickness | Medial femoral condyle, central weight-bearing zone | Sagittal T2 (FS=1) | Thickness in mm (or normalized to contralateral) | Population mean ± SD at this site; normal >3 mm | Directly measures cartilage; thinning is OA |
| M2 | Medial Cartilage Signal Loss | Medial femoral condyle surface | Sagittal T2 (FS=1) | Signal homogeneity: score 0 (normal), 1 (mild fibrillation), 2 (severe) | Normal knees show uniform intermediate signal | Fibrillation indicates early degeneration |
| M3 | Joint Space Width, Medial | Medial tibiofemoral articulation at widest point on coronal | Coronal T2 (FS=1) | Width in mm | Population median; normal typically 4–6 mm | Narrowing = cartilage loss |
| M4 | Subchondral Sclerosis, Medial | Medial tibial plateau, just below cartilage | Coronal T1 (standard) | Density (visual score: 0=normal, 1=mild, 2=marked) or HU units if available | Normal is homogeneous low-signal marrow | Sclerotic bone is denser, appears as low-signal band |
| M5 | Osteophyte Presence, Medial Femur | Medial femoral condyle margin, at cartilage-bone junction | Sagittal T2 (FS=1) | Size in mm (0 if none, 1–2 mm small, 3+ mm large) | Normal knees have none or <1 mm | Osteophytes are hallmark of OA |
| M6 | Osteophyte Presence, Medial Tibia | Medial tibial plateau margin | Coronal T2 (FS=1) | Size in mm | Normal knees have none or <1 mm | Osteophytes at load-bearing edges |
| M7 | Subchondral Cyst, Medial | Medial femoral condyle or tibial plateau, just under cartilage | Sagittal T2 (FS=1) | Diameter in mm (0 if none) | Normal knees do not have cysts | Cyst = small fluid pocket in bone, OA marker |
| M8 | Cartilage Integrity, Medial | Full cartilage layer, medial compartment | Sagittal + Coronal T2 (FS=1) | Continuous (0), frayed (1), defect <50% (2), defect >50% (3) | Intact, smooth in normals | Structural integrity score |

**Calibration note:** Each lens is calibrated against a registered reference image of a normal knee at the same anatomical site. Deviation from normal is the *deviation*, not yet a diagnosis.

### 1.4 Paths (Diagnostic Rules)

#### 1.4.1 DEFINITIONAL Paths (Assign Medial OA)

**PATH D1:** Cartilage loss (M1 < normal−1σ) AND joint space narrowing (M3 < median−2mm) AND osteophyte (M5 OR M6 > 2mm).

- **Law:** Full OA syndrome is a triad: cartilage thinning, space loss, and bone remodeling (osteophytes). All three together define the condition per standard radiology criteria (Ahlback grading, Outerbridge chondromalacia scale). If all three are present, OA is certain.
- **Warrant:** STRICT. A radiologist diagnosing OA from imaging checks all three. The law is anatomical/biomechanical: the three are not independent; they coexist in OA.
- **Confidence:** High (near 1.0) if all three are marked.

**PATH D2:** Severe cartilage loss (M1 < normal−2σ) AND (osteophyte > 3mm OR subchondral sclerosis grade 2).

- **Law:** Severe thinning with bone remodeling is diagnostic of advanced OA even without space narrowing measurement (space may be hard to measure if severely narrowed or fused).
- **Warrant:** STRICT by definition of advanced OA.
- **Confidence:** High.

**PATH D3:** (M8 cartilage integrity score = 3, complete loss) with (M3 space <2mm) in a weight-bearing zone.

- **Law:** Complete cartilage loss with bone-on-bone contact is end-stage OA, unmistakable.
- **Warrant:** STRICT.
- **Confidence:** Very high.

#### 1.4.2 STRICT EXCLUSION (Exclude Medial OA)

**EXCL E1:** Normal cartilage thickness (M1 ≥ normal−0.5σ) AND normal joint space (M3 ≥ median) AND no osteophytes (M5=0, M6=0) AND no sclerosis (M4=0) on **all** series where the medial compartment is visible (Sagittal + Coronal FS=1).

- **Law:** Absence of all four cardinal OA signs rules it out. The law is definitional: OA requires at least one of these signs; none = no OA.
- **Warrant:** STRICT. Complete coverage required: if medial compartment is visible and shows none of the four signs, OA is not present.
- **Completeness gate:** If Sagittal FS=1 OR Coronal FS=1 is missing/unreadable, this rule does not apply (see ABSTAIN).

**EXCL E2:** Young patient (age <40 if available) + M1 ≥ normal AND M3 ≥ median.

- **Law:** OA is rare in young people without prior trauma; normal cartilage + space in a young knee rules out primary OA.
- **Warrant:** DIRECTIONAL AGAINST (not strict, because early OA and post-traumatic OA can occur in younger patients).
- **Note:** Test set does not provide age; this rule applies only if demographics are added.

#### 1.4.3 DIRECTIONAL FOR / AGAINST (Confidence Modulation)

| Lens | Reading | Direction | Reason | Strength |
|------|---------|-----------|--------|----------|
| M1 (Cartilage thickness) | < normal−1σ | FOR | Thinning is the primary pathology of OA | Strong |
| M1 | normal−1σ to normal | – | Baseline; no signal | – |
| M2 (Signal loss) | Score 2 (severe fibrillation) | FOR | Early OA signature; indicates degeneration | Moderate |
| M2 | Score 1 (mild fibrillation) | FOR (weak) | Can appear in young knees without OA (normal variant); directional only | Weak |
| M3 (Joint space) | < median−2mm | FOR | Space loss indicates advanced cartilage wear | Strong |
| M3 | median−2 to median | – | Normal; no signal | – |
| M4 (Sclerosis) | Grade 2 (marked) | FOR | Reactive bone hardening; OA sign | Moderate–Strong |
| M4 | Grade 1 (mild) | FOR (weak) | Can be normal variant or age-related; not diagnostic alone | Weak |
| M5, M6 (Osteophytes) | >2mm | FOR | Large osteophytes are OA hallmark | Strong |
| M5, M6 | 1–2mm | FOR (weak) | Small osteophytes; can be normal aging or from old trauma | Weak |
| M7 (Subchondral cyst) | Present, >3mm | FOR | Cyst indicates OA stress; associated with cartilage loss | Moderate |
| M8 (Cartilage integrity) | Score 2–3 (defect) | FOR | Structural break is pathology | Moderate–Strong |
| Effusion presence | Large (>5mm) | AGAINST (weak) | Large effusion can signal acute inflammation, not primary OA; suggests synovitis or other cause | Weak-moderate |

#### 1.4.4 ABSTAIN (Missing Data, Gaps)

- **Series missing:** If Sagittal FS=1 is absent, rules relying on M1, M2, M5, M8 cannot be executed; abstain on those paths.
- **Series missing:** If Coronal FS=1 is absent, rules relying on M3, M6 cannot be executed; abstain.
- **Both missing:** If both Sagittal FS=1 and Coronal FS=1 are missing or unreadable, no definitive reading of medial OA; abstain.
- **Artifact:** Motion artifact, metal artifact (from prior surgery), or fat-suppression failure in FS=1 images prevents measurement; abstain for affected paths.

### 1.5 Mimics and Confounders

| Mimic | Distinguishing Lens | How to Isolate |
|-------|-------------------|-----------------|
| **Meniscal tear** with secondary changes | M1 (cartilage thickness), M8 (integrity) | Meniscal tear is in meniscus structure; cartilage remains normal unless advanced tear exposes bone. Separate the two lesions anatomically. |
| **Acute cartilage injury / acute chondral flake** | M2 (fibrillation pattern), onset (not available here) | Acute injury shows sharper edges, focal defect; OA shows gradual thinning over broad surface. Pattern differs. |
| **Edema adjacent to joint** (from injury, cyst rupture) | M4 (subchondral sclerosis grade, location) | Edema appears high-signal on T2; sclerotic bone is low-signal, dense. Location differs: edema is often focal; sclerosis is at load-bearing surfaces. |
| **Osteophytes from old healed fracture** (e.g., plateau fracture) | M1 (cartilage thickness), mechanism (absent here) | Osteophytes post-fracture occur at fracture site, often asymmetric. OA osteophytes are bilateral (often) and at joint margins. Context: fracture history, fracture line visibility. |
| **Rheumatoid or inflammatory arthritis** | M4 (sclerosis—absent in early RA), distribution (bilateral ankle OA ≠ RA pattern in knee) | RA shows cartilage loss without prominent osteophytes; OA shows both. RA is symmetric, systemic; OA can be unilateral. Reports mention "rheumatoid arthritis" vs "osteoarthritis" explicitly. |

### 1.6 Effects on Other Labels

- **Medial Meniscus tear:** Prolonged mechanical stress from OA can accelerate meniscal degeneration. However, a torn meniscus can *cause* OA later. The two are distinct but related. OA does not imply meniscal tear, nor vice versa.
- **Medial MCL strain / integrity:** OA compartment narrowing can secondarily stress the MCL; but MCL is not directly damaged by OA cartilage loss.
- **Effusion:** OA can produce a chronic small effusion (reactive synovial fluid). Conversely, large acute effusion suggests acute inflammation (synovitis, acute tear), not primary OA.
- **Synovitis:** Chronic OA may cause mild synovitis (inflammatory response); large synovitis suggests acute process.
- **Medial contusion / fracture:** Trauma can cause both acute contusion and accelerate OA if significant. OA alone does not cause acute bone bruising.

### 1.7 What Host Labels Confirm; Near Misses

**Host label = 1 (Medial OA present) confirms:**
- At least one of the three cardinal signs is present (cartilage loss, space narrowing, osteophytes, sclerosis).
- The radiologist visually recognized degenerative joint disease in the medial compartment.

**Near misses (expected from the 58 labeled studies):**
- Early OA with only M2 (mild fibrillation) visible; cartilage thickness and space appear normal. Host labels it as OA (physician's confidence threshold lower than strict conjunction). Teaches the weak directional reading of M2.
- OA + concurrent effusion. Teaches the independence of effusion from OA (or the common co-occurrence if both are present).
- Post-traumatic OA: cartilage loss after healed meniscal or ligament injury. Teaches the causality from prior injury, if reports mention it.

---

## 2. LATERAL OA (Lateral Compartment Osteoarthritis)

### 2.1 Definition

**Host definition (FACT):** Not explicitly provided. **Domain reading:** Degenerative changes in the lateral tibiofemoral compartment (lateral femoral condyle and lateral tibial plateau).

**Scope (PROPOSAL):** Lateral compartment excludes patellofemoral joint (PF OA) and lateral meniscus injury (separate label). The lateral meniscus occupies the lateral compartment; OA is degeneration of bone/cartilage separate from meniscal injury.

### 2.2 Structural Reason

**Anatomy (DOMAIN):**
- **Lateral compartment:** Lateral femoral condyle (superior), lateral tibial plateau (inferior), fibular collateral ligament (FCL) and lateral capsule (lateral wall).
- **Cartilage, osteophytes, subchondral changes:** Same pathology as medial OA; located on the lateral side.

**MR Physics (DOMAIN):**
- Same as Medial OA: T2-weighted (FS=1) best for cartilage; Sagittal and Coronal planes show the compartment.
- **Sagittal plane:** Shows lateral femoral condyle profile, less bulbous than medial (different anatomy).
- **Coronal plane:** Visualizes lateral tibial plateau width, lateral femoral condyle summit.

**Mechanics (DOMAIN):**
- Lateral OA is less common than medial OA in primary (non-post-traumatic) knees, because the lateral compartment bears less load in most people.
- Post-meniscectomy lateral OA is common (meniscus removal increases load on cartilage).

### 2.3 Thermometers (Lenses)

Identical structure to Medial OA (M1–M8), applied to lateral sites.

| # | Lens Name | Site | Series/Plane | Measurement |
|---|-----------|------|--------------|-------------|
| L1 | Lateral Cartilage Thickness | Lateral femoral condyle, central zone | Sagittal T2 (FS=1) | Thickness in mm |
| L2 | Lateral Cartilage Signal Loss | Lateral femoral condyle surface | Sagittal T2 (FS=1) | Score 0–2 |
| L3 | Joint Space Width, Lateral | Lateral tibiofemoral articulation | Coronal T2 (FS=1) | Width in mm |
| L4 | Subchondral Sclerosis, Lateral | Lateral tibial plateau, just below cartilage | Coronal T1 (standard) | Density score 0–2 |
| L5 | Osteophyte Presence, Lateral Femur | Lateral femoral condyle margin | Sagittal T2 (FS=1) | Size in mm |
| L6 | Osteophyte Presence, Lateral Tibia | Lateral tibial plateau margin | Coronal T2 (FS=1) | Size in mm |
| L7 | Subchondral Cyst, Lateral | Lateral femoral or tibial, under cartilage | Sagittal T2 (FS=1) | Diameter in mm |
| L8 | Cartilage Integrity, Lateral | Full cartilage layer, lateral compartment | Sagittal + Coronal T2 (FS=1) | Score 0–3 |

### 2.4 Paths (Diagnostic Rules)

**DEFINITIONAL:**
- **PATH D1:** (L1 < normal−1σ) AND (L3 < median−2mm) AND (L5 OR L6 > 2mm). [Lateral OA triad]
- **PATH D2:** (L1 < normal−2σ) AND (L4 grade 2 OR L5 > 3mm).
- **PATH D3:** (L8 score 3) AND (L3 < 2mm).

**STRICT EXCLUSION:**
- **EXCL E1:** (L1 ≥ normal−0.5σ) AND (L3 ≥ median) AND (L5=0, L6=0) AND (L4=0) on all visible series.

**DIRECTIONAL:** Same mechanism as medial; lateral-specific mimics and near misses below.

**ABSTAIN:** Same conditions as medial; Sagittal FS=1 and Coronal FS=1 required for full assessment.

### 2.5 Mimics and Confounders

| Mimic | Distinguishing Lens |
|-------|-------------------|
| **Lateral meniscus tear** | L1, L8 (cartilage integrity). Meniscal tear is in meniscus; cartilage normal unless advanced. |
| **Lateral ligament (FCL) injury** | L1–L8 do not directly measure ligament. Ligament tears do not thin cartilage acutely. |
| **Post-meniscectomy changes** | History (absent here). Osteophytes post-meniscectomy can mimic primary OA. Mechanism differs (iatrogenic), but imaging appearance is identical. |
| **Avascular necrosis (lateral femoral condyle)** | L1 (cartilage may be normal early); L4 (subchondral cyst, sclerosis). AVN shows focal subchondral lucency / cyst; OA is broad cartilage loss. Anatomical location narrows: AVN is often medial femoral condyle (not lateral, though possible). |

### 2.6 Effects on Other Labels

- **Lateral Meniscus tear:** Similar to medial; distinct injuries but mechanically linked over time.
- **Lateral OA + Medial OA:** Both compartments can be affected. Bilateral involvement suggests systemic (RA, HA) or mechanical overload. Independent assessment per compartment.
- **Effusion, Synovitis:** Same as medial OA.
- **Lateral ligament (FCL) injury:** OA does not imply ligament injury, though chronic laxity can accelerate load-bearing changes.

### 2.7 What Host Labels Confirm; Near Misses

**Host label = 1 confirms:**
- Lateral compartment shows ≥1 cardinal OA sign (cartilage loss, space narrowing, osteophytes, sclerosis).

**Near misses:**
- Post-meniscectomy lateral OA: cartilage loss after lateral meniscus removal (not recorded in this dataset).
- Lateral OA + medial OA (both compartments affected).
- Early lateral OA with only L2 (signal loss) visible.

---

## 3. PF OA (Patellofemoral Osteoarthritis)

### 3.1 Definition

**Host definition (FACT):** Not explicitly provided. **Domain reading:** Degenerative changes between the patella and femur (patellofemoral joint), including cartilage loss, osteophytes, and subchondral changes at the patellofemoral articulation.

**Scope (PROPOSAL):** Patellofemoral compartment comprises the patellar articular surface (posterior face) and the patellar groove (femoral trochlea). Separate from tibiofemoral OA (medial and lateral).

### 3.2 Structural Reason

**Anatomy (DOMAIN):**
- **Patellofemoral joint:** Patella (small bone anterior to knee) articulates with femoral trochlea (groove in distal femur).
- **Cartilage:** Articular cartilage on patella (posterior) and trochlea; thicker than tibiofemoral cartilage due to higher contact stresses.
- **Alignment:** Patellar tracking and alignment affect load distribution; malalignment increases OA risk.
- **Osteophytes:** Occur at patellar margins (medial and lateral edges) and trochlear margins.

**MR Physics (DOMAIN):**
- **Sagittal plane:** Best for viewing patella in profile, trochlea depth, patellar cartilage thickness, patellar osteophytes.
- **Coronal plane:** Shows patellar medial/lateral facets relative to femoral condyles; less commonly used for PF OA.
- **Axial plane:** Excellent for patellar facet alignment, facet-specific cartilage loss, medial vs lateral facet asymmetry.
- **T2-weighted (FS=1):** Cartilage signal and thickness; fluid in patellofemoral recess.

**Mechanics (DOMAIN):**
- Patellar malalignment (lateral tracking) or weakness of quadriceps can lead to increased load on lateral patellar facet.
- Patellofemoral OA can occur independent of tibiofemoral OA, or in combination.

### 3.3 Thermometers (Lenses)

| # | Lens Name | Site | Series/Plane | Measurement |
|---|-----------|------|--------------|-------------|
| P1 | Patellar Cartilage Thickness | Patellar surface, central ridge | Sagittal T2 (FS=1) | Thickness in mm; if asymmetric, measure medial and lateral facets separately |
| P2 | Patellar Cartilage Signal | Patellar surface | Sagittal T2 (FS=1) | Fibrillation score 0–2 |
| P3 | Trochlear Cartilage Thickness | Femoral trochlea, floor of groove | Sagittal T2 (FS=1) | Thickness in mm |
| P4 | Trochlear Cartilage Signal | Femoral trochlea surface | Sagittal T2 (FS=1) | Fibrillation score 0–2 |
| P5 | Patellar Facet Asymmetry | Medial vs lateral patellar facet width/depth | Axial T2 (FS=1) | Asymmetry index (medial−lateral) / medial; score for predominant load on one facet |
| P6 | Osteophyte, Patellar Margin | Medial and/or lateral patellar edge | Sagittal T2 (FS=1) | Size in mm (separate medial/lateral) |
| P7 | Osteophyte, Trochlear Edge | Trochlear margins (medial/lateral) | Sagittal T2 (FS=1) | Size in mm |
| P8 | Subchondral Sclerosis, Patella | Patella bone just under cartilage | Sagittal T1 (standard) | Density score 0–2 |
| P9 | Subchondral Sclerosis, Trochlea | Femoral trochlea bone just under cartilage | Sagittal T1 (standard) | Density score 0–2 |
| P10 | Patellar Malalignment | Patellar tracking; lateral shift or rotation | Axial T1 (standard) or Sagittal | Alignment index (medial/lateral shift in mm, or angle); 0=centered, positive=lateral shift |
| P11 | Patellofemoral Joint Space | Distance between patellar cartilage and trochlear cartilage | Sagittal T2 (FS=1) | Width in mm at the closest point |
| P12 | Cartilage Defect, Patellofemoral | Focal loss of cartilage surface | Sagittal T2 (FS=1) | Defect size (mm²) or depth score 0–3 |

### 3.4 Paths (Diagnostic Rules)

**DEFINITIONAL:**
- **PATH D1:** (P1 < normal−1σ) AND (P3 < normal−1σ) AND (P6 OR P7 > 2mm). [PF OA triad: thin patellar cartilage + thin trochlear cartilage + osteophytes]
- **PATH D2:** (P1 < normal−2σ) AND (P8 grade 2 OR P9 grade 2). [Severe patellar thinning + sclerosis]
- **PATH D3:** (P12 defect score 3) AND (P11 < 2mm). [End-stage: cartilage loss + space loss]
- **PATH D4:** (P5 severe asymmetry, one facet loaded) AND (P2 OR P4 score 2) AND (P6 OR P7 > 1mm, asymmetric). [Facet-specific OA: concentrated load on one patellar facet]

**STRICT EXCLUSION:**
- **EXCL E1:** (P1 ≥ normal−0.5σ) AND (P3 ≥ normal−0.5σ) AND (P6=0, P7=0) AND (P8=0, P9=0) AND (P12 defect score 0) on visible Sagittal FS=1 and Axial FS=1.

**DIRECTIONAL:**
- Asymmetric patellar facet wear (P5 + P2 or P4 showing signal loss on the loaded facet) → FOR (moderate). Lateral facet OA is common in lateral malalignment.
- Malalignment (P10 lateral shift) without cartilage changes → AGAINST (weak). Malalignment is a risk factor, not OA itself.

**ABSTAIN:**
- Sagittal FS=1 required for P1–P4, P6–P9, P11, P12.
- Axial FS=1 required for P5, P10.
- If either is missing, abstain on facet-specific and malalignment paths.

### 3.5 Mimics and Confounders

| Mimic | Distinguishing Lens |
|-------|-------------------|
| **Patellar cartilage injury (acute chondral flake)** | P2, P4 (fibrillation pattern); P12 (defect appearance). Acute injury shows sharp edge, focal; OA is gradual, broad thinning. |
| **Patellofemoral pain syndrome (PFPS) / patellar malalignment without OA** | P10 (malalignment index); P1–P3 (cartilage normal). Malalignment predisposes to OA but is distinct; thin cartilage is OA. |
| **Patellar subluxation or lateral tracking** | P10 (shift/rotation). Subluxation is a biomechanical instability; OA is tissue degeneration. Can co-occur but are distinct. |
| **Quadriceps atrophy** (seen on axial, muscle signal) | Not a cartilage/OA measure; muscle is outside the scope. |

### 3.6 Effects on Other Labels

- **Tibiofemoral OA (Medial + Lateral):** PF OA can occur alone or with either/both tibiofemoral compartments affected. Independent questions.
- **Medial Meniscus tear:** No direct mechanical link; distinct anatomies (meniscus is in tibiofemoral compartment; PF joint is separate).
- **Lateral Meniscus tear:** Same as medial.
- **Effusion:** PF OA can produce chronic small joint effusion; large effusion suggests other pathology.
- **Patellar ligament / quadriceps injury:** Not directly related to OA cartilage; distinct lesions.

### 3.7 What Host Labels Confirm; Near Misses

**Host label = 1 confirms:**
- At least one cardinal PF OA sign is present.

**Near misses:**
- Early PF OA: only P2 or P4 (cartilage signal loss) visible; thickness normal. Teaches weak directional reading.
- Lateral facet OA (P5 asymmetry + P6 or P4 changes) with medial facet normal. Teaches compartment-specific assessment.
- PF OA with concurrent malalignment (P10 positive, P1–P3 borderline). Teaches the distinction between predisposing factor and OA.

---

## 4. EFFUSION (Joint Fluid)

### 4.1 Definition

**Host definition (FACT):** Not explicitly provided. **Domain reading:** Abnormal accumulation of fluid in the knee joint space and/or joint recesses (suprapatellar, infrapatellar, lateral/medial gutters).

**Scope (PROPOSAL):** Effusion is a volume of fluid, measured in the joint capsule. It can be a reactive (inflammatory) response to OA, injury, or inflammation; or it can be a primary finding (synovial inflammation). The size defines severity: small (<5 mm thickness in the recess), moderate (5–10 mm), large (>10 mm).

### 4.2 Structural Reason

**Anatomy (DOMAIN):**
- **Joint capsule:** Fibrous bag enclosing the knee joint. Contains synovial fluid (normally ~2–5 mL in healthy knee).
- **Joint recesses:** Pockets of the capsule; key sites are suprapatellar recess (above patella), infrapatellar recess (below patella), lateral and medial gutters (sides).
- **Synovial membrane:** Lines the inner capsule; produces synovial fluid.
- **Fluid mechanics:** Synovial fluid increases with inflammation, injury, or chronic joint disease.

**MR Physics (DOMAIN):**
- **T2-weighted (Fluid-Sensitive, FS=1):** Fluid is high-signal (bright) on T2; easily visualized.
- **Best planes for measurement:**
  - **Sagittal T2 (FS=1):** Shows suprapatellar recess (largest, easiest to measure). Fluid appears as bright band posterior to quadriceps.
  - **Axial T2 (FS=1):** Shows joint space, lateral/medial gutters, circumferential fluid distribution.
  - **Coronal T2 (FS=1):** Shows medial/lateral gutters.
- **Measurement:** Thickness of fluid layer in mm, or volume estimation (small/moderate/large).

**Pathophysiology (DOMAIN):**
- **Reactive effusion:** Secondary to OA, meniscal tear, or acute trauma. Usually small to moderate, resolves slowly.
- **Inflammatory effusion:** From synovitis, RA, infection. Often larger, associated with synovial thickening.
- **Hemorrhagic effusion:** Post-traumatic; can be large, presents with acute symptoms.
- **Mechanical:** Obstruction in joint space from loose body or meniscal displacement can cause fluid accumulation.

### 4.3 Thermometers (Lenses)

| # | Lens Name | Site | Series/Plane | Measurement |
|---|-----------|------|--------------|-------------|
| E1 | Suprapatellar Effusion Thickness | Suprapatellar recess, between quadriceps tendon and femur | Sagittal T2 (FS=1) | Maximum thickness in mm |
| E2 | Suprapatellar Effusion Signal | Suprapatellar recess fluid | Sagittal T2 (FS=1) | Signal homogeneity: 0=none, 1=simple fluid (homogeneous), 2=complex (internal signal, debris, blood) |
| E3 | Infrapatellar Effusion Thickness | Infrapatellar recess, below patella | Sagittal T2 (FS=1) | Maximum thickness in mm |
| E4 | Lateral Gutter Fluid | Lateral joint gutter | Coronal T2 (FS=1) | Thickness in mm at the widest point |
| E5 | Medial Gutter Fluid | Medial joint gutter | Coronal T2 (FS=1) | Thickness in mm at the widest point |
| E6 | Circumferential Joint Space Fluid | Fluid in the tibiofemoral joint space proper (not recesses) | Axial T2 (FS=1) | Maximum width in mm; taken at several axial slices, average or maximum |
| E7 | Effusion Volume Estimate | Sum of recess + gutter + space fluid | Sagittal + Coronal T2 (FS=1) | Category: 0=none/trace (<2mm max), 1=small (2–5mm), 2=moderate (5–10mm), 3=large (>10mm) |
| E8 | Effusion Complexity | Presence of internal signal (blood, debris, inflammatory cells) | Sagittal + Coronal T2 (FS=1) | Simple (0) vs complex (1) |
| E9 | Associated Synovial Thickening | Thickened synovial membrane lining the capsule | Sagittal T2 (FS=1) + Coronal | Thickness in mm (normal <2mm) |

**Calibration note:** Normal knee has trace fluid only (<2mm). Positive effusion is >2mm in any recess; scoring by volume/thickness relates to severity.

### 4.4 Paths (Diagnostic Rules)

**DEFINITIONAL Effusion:**
- **PATH D1:** E7 volume estimate ≥ 1 (small: max thickness ≥ 2mm in any recess). [Simple definition: any measurable effusion]
- **PATH D2:** (E1 ≥ 5mm) OR (E3 ≥ 5mm) OR (E4 ≥ 5mm) OR (E5 ≥ 5mm). [Moderate or larger effusion in at least one location]

**STRICT EXCLUSION:**
- **EXCL E1:** (E1 < 2mm) AND (E3 < 2mm) AND (E4 < 2mm) AND (E5 < 2mm) AND (E6 < 2mm) on all visible planes (Sagittal FS=1, Coronal FS=1). [No effusion if all recesses/gutters show <2mm]

**DIRECTIONAL:**
- **(E1 or E3 or E4 or E5) = 2–5mm → FOR (moderate confidence).** Small effusion is mild but present.
- **(E1 or E3 or E4 or E5) > 10mm → FOR (high confidence).** Large effusion is certain.
- **E8 (complex/internal signal present) → FOR (strong).** Complex fluid (blood, debris) indicates recent inflammation or hemorrhage; confirms significant process.
- **E9 (synovial thickening > 2mm) + E1–E5 any size → FOR (moderate).** Thickened synovium suggests active inflammation; supports effusion from synovitis rather than just reactive.
- **E8 (simple) + small E1–E5 + old OA history → AGAINST (weak).** Small simple effusion in chronic OA is expected; not a new finding.

**ABSTAIN:**
- Sagittal FS=1 required for E1–E3, E8, E9.
- Coronal FS=1 required for E4–E5, E9.
- If both missing, cannot measure effusion; abstain.
- Fat-suppression failure (FS=1 image unreadable) → abstain for that plane.

### 4.5 Mimics and Confounders

| Mimic | Distinguishing Lens |
|-------|-------------------|
| **Normal synovial fluid / trace effusion** | E7 (volume category). Trace (<2mm) is normal; ≥2mm is abnormal. |
| **Synovitis without large effusion** | E9 (synovial thickening) + E1–E5 size. Synovitis can present with thickened membrane, small/no effusion. |
| **Hemorrhagic effusion** (acute, post-traumatic) | E8 (complex signal). Blood appears intermediate-to-high signal on T2, not simple fluid bright-signal. Associated with acute trauma history (absent here). |
| **Pseudoeffusion** (artifact, partial volume from cartilage or meniscus) | E2 (signal homogeneity). True effusion is homogeneous high-signal on T2; artifact or tissue signal is heterogeneous. |

### 4.6 Effects on Other Labels

- **Medial/Lateral/PF OA:** Chronic OA commonly produces small-moderate effusion (reactive). Does not *cause* OA; is secondary.
- **Meniscal tears (Medial/Lateral):** Acute meniscal tear can produce effusion. Large effusion + tear indicates acute injury.
- **ACL/MCL injury:** Acute ligament tear produces effusion (hemarthrosis). Large complex effusion suggests acute tear.
- **Synovitis:** Inflamed synovium produces effusion; the two are related but distinct. Thick synovium + effusion = synovitis.
- **Baker's cyst:** Does not directly cause intra-articular effusion, but can co-occur.
- **Fracture/Contusion:** Acute bone injury produces hemorrhagic effusion (complex). Helps identify recent trauma.

### 4.7 What Host Labels Confirm; Near Misses

**Host label = 1 (Effusion present) confirms:**
- Measurable fluid (≥2mm in at least one recess/gutter) is present on the scans.
- Radiologist judged it abnormal (beyond normal trace).

**Near misses:**
- Small effusion (2–5mm) in setting of chronic OA. Teaches distinction between reactive and pathologic effusion.
- Complex vs simple effusion. If complex (blood/debris) but small, teaches that inflammatory nature matters, not just size.
- Effusion + concurrent synovitis. Teaches the two are often together.

---

## 5. SYNOVITIS (Inflammation of Synovial Membrane)

### 5.1 Definition

**Host definition (FACT):** Not explicitly provided. **Domain reading:** Thickening and/or enhancement of the synovial membrane lining the joint capsule, indicating inflammatory process.

**Scope (PROPOSAL):** Synovitis includes any inflammation of synovium: acute (infectious, post-traumatic), chronic (RA, spondyloarthropathy, chronic mechanical irritation), or reactive (secondary to joint pathology like OA).

### 5.2 Structural Reason

**Anatomy (DOMAIN):**
- **Synovial membrane:** Thin vascularized tissue lining the inner joint capsule. Produces synovial fluid and protective factors.
- **Normal synovium:** <2 mm thick, low signal on T1.
- **Inflamed synovium:** Thickened (>2 mm), increased cellularity, edema, increased vascularity. On MRI, appears as intermediate-to-high signal, especially on T2 and post-contrast T1.

**MR Physics (DOMAIN):**
- **T2-weighted (FS=1):** Inflamed (edematous) synovium appears higher signal; synovial fluid is bright. Synovitis thickening can be distinguished from effusion if synovial layer is thickened and the central fluid is separate.
- **T1-weighted (standard):** Normal synovium is low signal; inflamed synovium is intermediate. Post-contrast (if available, not mentioned in this task) shows enhancement (gadolinium uptake).
- **Fat-suppressed (FS=1):** Enhances visibility of synovial thickening against low-signal fat.
- **Best planes:** Sagittal T2 (FS=1) shows suprapatellar recess synovium well; Coronal shows medial/lateral gutters.

**Pathophysiology (DOMAIN):**
- **Acute synovitis:** Infection, acute trauma, crystal arthropathy. Often presents with pain, swelling, effusion.
- **Chronic synovitis:** RA, seronegative spondyloarthropathy, chronic mechanical irritation from loose body or meniscal tear.
- **Reactive synovitis:** Secondary to OA, meniscal injury. Mild, progressive.

### 5.3 Thermometers (Lenses)

| # | Lens Name | Site | Series/Plane | Measurement |
|---|-----------|------|--------------|-------------|
| S1 | Synovial Thickness, Suprapatellar | Synovial lining of suprapatellar recess capsule | Sagittal T2 (FS=1) | Thickness in mm (normal ≤2mm; abnormal >2mm) |
| S2 | Synovial Thickness, Lateral Gutter | Synovial lining, lateral gutter | Coronal T2 (FS=1) | Thickness in mm |
| S3 | Synovial Thickness, Medial Gutter | Synovial lining, medial gutter | Coronal T2 (FS=1) | Thickness in mm |
| S4 | Synovial Signal | Synovium signal intensity on T2 (FS=1) | Sagittal + Coronal T2 (FS=1) | Intensity: 0=low (normal), 1=intermediate (mild inflammation), 2=high (marked) |
| S5 | Synovial Enhancement Pattern | Presence of granulation tissue, enhancement (best seen post-contrast; not available in this task) | Post-contrast T1 or inferred from T2 | Pattern: homogeneous (0) vs heterogeneous with nodules (1) |
| S6 | Pannus-like Signal | Proliferative synovium with intermediate signal in recess (can suggest RA) | Sagittal T2 (FS=1) | Presence (0=none, 1=mild, 2=marked) |
| S7 | Associated Effusion | Volume of effusion accompanying synovitis | Sagittal + Coronal T2 (FS=1) | Size category (0–3, as per Effusion lenses) |
| S8 | Synovial Complexity | Heterogeneous signal, presence of debris, inflammatory signal | Sagittal T2 (FS=1) | Score 0–2 (simple/homogeneous to complex/nodular) |

**Calibration note:** Normal synovium is <2 mm thick and low-intermediate signal on T2. Abnormal is thickened, higher signal, or complex (nodular).

### 5.4 Paths (Diagnostic Rules)

**DEFINITIONAL Synovitis:**
- **PATH D1:** (S1 > 2mm) OR (S2 > 2mm) OR (S3 > 2mm), in two or more locations. [Synovial thickening ≥2mm in multiple recesses = synovitis]
- **PATH D2:** (S1 > 3mm) OR (S2 > 3mm) OR (S3 > 3mm), with (S4 ≥ 1, intermediate signal). [Marked thickening + intermediate-high signal = definite synovitis]
- **PATH D3:** (S6 pannus-like signal present) AND (S1 or S2 or S3 > 2mm). [Pannus (RA-like pattern) + thickening = RA synovitis]

**STRICT EXCLUSION:**
- **EXCL E1:** (S1 ≤ 2mm) AND (S2 ≤ 2mm) AND (S3 ≤ 2mm) AND (S4 = 0, low signal) on visible Sagittal and Coronal FS=1. [No thickening, normal signal = no synovitis]

**DIRECTIONAL:**
- **(S1 or S2 or S3) 2–3mm + S4 ≥ 1 → FOR (moderate).** Borderline thickening + elevated signal suggests mild synovitis.
- **(S1 or S2 or S3) > 3mm → FOR (strong).** Marked thickening is high-confidence synovitis.
- **S7 (large effusion) + (S1 or S2 or S3) > 2mm → FOR (strong).** Effusion + thickening together indicate active inflammation.
- **S8 (complex/nodular pattern) → FOR (moderate–strong).** Heterogeneous synovium suggests active inflammatory process, granulation, or RA.
- **S6 (pannus) → FOR (moderate).** Pannus-like synovium suggests RA-type inflammation; directional (not definitive without serologic confirmation).
- **S1–S3 borderline (2–2.5mm) + S4 = 0 (low signal) + small effusion → AGAINST (weak).** Minimal thickening with normal signal in chronic OA is reactive, not significant synovitis.

**ABSTAIN:**
- Sagittal FS=1 required for S1, S4–S6.
- Coronal FS=1 required for S2–S3, S4.
- If both missing, abstain.
- No post-contrast T1 in this dataset; S5 cannot be measured. Rely on T2 and clinical history (absent here).

### 5.5 Mimics and Confounders

| Mimic | Distinguishing Lens |
|-------|-------------------|
| **Simple effusion without synovitis** | S1–S3 (synovial thickness). Large effusion can appear as fluid without thickened synovial rim. Measure rim separately from fluid. |
| **Normal synovium** | S1–S3 ≤ 2mm; S4 = 0. Normal is thin and low signal. |
| **Hypertrophic synovium from chronic OA** | S1–S3 > 2mm + S4 ≥ 1, but in patient with chronic OA. OA synovitis is usually mild, reactive. Distinguish from acute RA by pattern (RA often has pannus, heterogeneity). |
| **Pigmented villonodular synovitis (PVNS)** | Rare. Shows hemosiderin (low signal) on T2; heterogeneous pattern. S8 (complex) present; but history and pattern distinct. |
| **Infection / septic arthritis** | Marked synovitis + complex effusion + fever (absent data). Distinction depends on clinical context. |

### 5.6 Effects on Other Labels

- **Meniscal tears (Medial/Lateral):** Torn meniscus can irritate synovium, causing reactive synovitis. The tear is the primary pathology; synovitis is secondary.
- **OA (Medial/Lateral/PF):** Chronic OA produces mild reactive synovitis. The two are linked; mild synovitis is expected with OA.
- **Ligament injuries (ACL/MCL):** Acute ligament tear causes inflammatory synovitis (hemosynovitis). Distinguishes acute from chronic injury.
- **Effusion:** Synovitis and effusion often co-occur; both indicate an inflammatory process.
- **Contusion/Fracture:** Acute bone injury triggers synovitis.
- **Baker's cyst:** Not directly related; separate structure.
- **Synovitis + RA pattern + systematic involvement:** Suggests systemic disease; but this dataset provides no systemic information.

### 5.7 What Host Labels Confirm; Near Misses

**Host label = 1 (Synovitis present) confirms:**
- Synovial thickening (>2 mm) or signal changes consistent with inflammation are visible.

**Near misses:**
- Mild reactive synovitis (S1–S3 = 2–2.5mm, low signal) in setting of chronic OA. Teaches the distinction between significant and trivial synovitis.
- Synovitis + concurrent effusion. Both present; cannot separate their contributions to symptoms.
- Synovitis + pannus-like pattern, suggesting RA, but no other RA features (no systemic markers available here). Teaches the pattern but cannot confirm disease.

---

## 6. BAKER'S (Baker's Cyst, Popliteal Cyst)

### 6.1 Definition

**Host definition (FACT):** Not explicitly provided. **Domain reading:** Fluid-filled cyst in the popliteal fossa (posterior knee space, behind the knee), typically arising from the posterior joint capsule or a sac connected to the tibiofemoral joint.

**Scope (PROPOSAL):** Baker's cyst is a *structure* (a sac or cavity filled with fluid), not a pathological state like OA or inflammation. Presence vs absence is binary. Size and presence of internal signal (degeneration, hemorrhage) are secondary.

### 6.2 Structural Reason

**Anatomy (DOMAIN):**
- **Popliteal fossa:** Space behind the knee, bounded by hamstring tendons (medial: semitendinosus/semimembranosus; lateral: biceps), skin, and deeper structures (popliteal vessels, nerves, fat).
- **Baker's cyst origin:** Arises from the posterior joint capsule (often at the junction of medial and lateral recesses), or connects to the joint via a stalk. The cyst is a hernia or outpouching of the synovial sac.
- **Mechanism:** Forms when synovial fluid is forced backward through the capsule under pressure; can happen in knees with effusion, meniscal pathology, or inflammation.
- **Content:** Synovial fluid (simple, similar to joint fluid), or may become thick and gelatinous over time.

**MR Physics (DOMAIN):**
- **Sagittal plane:** Best view of popliteal cyst; fluid appears as high-signal (bright) mass behind the knee.
- **Coronal plane:** Shows cyst location relative to medial/lateral compartments.
- **Axial plane:** Can show cyst cross-section, size, relation to vessels.
- **T2-weighted (FS=1):** Cyst fluid is high-signal. Interior is usually homogeneous (simple fluid), but can be heterogeneous if complex/hemorrhagic.
- **T1-weighted (standard):** Fluid is low signal. Allows differentiation from fat or hemorrhage (which have different T1 signals).

**Pathophysiology (DOMAIN):**
- **Mechanical valve mechanism:** Joint fluid flows backward into cyst when knee moves/pressure rises; valve prevents backflow when pressure drops.
- **Associated pathology:** Common in knees with meniscal tears, OA, or chronic effusion.
- **Symptoms:** Can cause posterior knee pain, swelling behind knee. May rupture (rare; causes pain, swelling downward into calf).
- **Prognosis:** Many remain stable; some resolve spontaneously.

### 6.3 Thermometers (Lenses)

| # | Lens Name | Site | Series/Plane | Measurement |
|---|-----------|------|--------------|-------------|
| B1 | Popliteal Cyst Presence | Popliteal fossa, posterior knee | Sagittal T2 (FS=1) | Present (1) or absent (0) |
| B2 | Cyst Size (Maximum Diameter) | Largest dimension of cyst | Sagittal T2 (FS=1) | Diameter in mm |
| B3 | Cyst Location | Medial vs lateral popliteal fossa | Sagittal + Coronal | Location: medial (0), midline (1), lateral (2) |
| B4 | Cyst–Joint Connection | Visible stalk/tract connecting cyst to joint capsule | Sagittal T2 (FS=1) + Coronal | Present (1) or not visible/unclear (0) |
| B5 | Cyst Fluid Signal Homogeneity | Interior signal of cyst on T2 | Sagittal T2 (FS=1) | Homogeneous (0=simple fluid) vs heterogeneous (1=internal signal, debris, hemorrhage) |
| B6 | Cyst Compression / Symptoms | Cyst size relative to popliteal space and vessels | Sagittal + Axial | Compressing adjacent structures? 0=no, 1=borderline, 2=yes (calf swelling likely) |
| B7 | Associated Medial Recess Fluid | Fluid extending from medial recess toward cyst origin (suggests connection) | Sagittal + Coronal T2 (FS=1) | Present (1) or absent (0) |

**Calibration note:** Presence of a fluid-filled sac in the popliteal fossa = Baker's cyst. Size distinguishes small (incidental) from large (symptomatic).

### 6.4 Paths (Diagnostic Rules)

**DEFINITIONAL Baker's Cyst:**
- **PATH D1:** (B1 = present) AND (B2 ≥ 1mm) AND (B5 = homogeneous or heterogeneous, does not matter) AND (B4 connection visible OR B7 medial recess fluid present). [Cyst + at least one sign of joint connection = Baker's]
- **PATH D2:** (B1 present) AND (B2 > 10mm). [Large cyst, any signal, even if stalk not visible, is Baker's cyst]
- **PATH D3:** (B1 present) AND (B2 > 20mm) AND (B6 = 1 or 2, compression). [Large symptomatic cyst]

**STRICT EXCLUSION:**
- **EXCL E1:** (B1 = 0, no cyst seen) on visible Sagittal T2 (FS=1) and Coronal T2 (FS=1). [No fluid sac visible = no cyst]
- **Exclusion by anatomy:** Cyst-like structure in popliteal fossa with T1 signal that is not low (e.g., high signal = hemorrhage or fat) is not a fluid-filled cyst. Use T1 to differentiate.

**DIRECTIONAL:**
- **(B1 present) + (B4 connection visible) → FOR (high confidence).** Direct evidence of joint connection confirms cyst origin from joint.
- **(B1 present) + (B7 medial recess fluid) → FOR (moderate).** Recess fluid feeding the cyst suggests connection.
- **(B2 > 20mm) → FOR (high confidence).** Large cyst is unmistakable.
- **(B2 < 5mm) + (B4 no connection) + (no recess fluid) → AGAINST (weak).** Tiny sac without visible connection could be lymph node, bursa, or artifact.
- **(B5 heterogeneous) → FOR (moderate).** Complex signal suggests hemorrhage or thick, degenerative cyst content; still a Baker's cyst, but unusual.

**ABSTAIN:**
- Sagittal T2 (FS=1) required for B1, B2, B4, B5, B7.
- Coronal T2 (FS=1) helpful for B3, B4, B7.
- If Sagittal T2 (FS=1) is missing or unreadable, abstain on cyst detection.

### 6.5 Mimics and Confounders

| Mimic | Distinguishing Lens |
|-------|-------------------|
| **Popliteal lymph node** | B2 (size, rounded), B4 (no connection to joint capsule), T1 signal (may vary). Lymph nodes are typically <1 cm, don't connect to joint. |
| **Bursa** (e.g., gastrocnemius-semimembranosus bursa, popliteus bursa) | B4 (bursa does not connect to joint). T2 shows fluid-filled sac, but location and anatomy differ. Bursa is a separate structure. |
| **Edema from trauma / cyst rupture** | B1 (cyst structure), B5 (signal). Edema is diffuse high signal on T2; cyst is a well-defined sac. If cyst has ruptured, edema is present below + empty sac above. |
| **Ganglion cyst** (rare in knee, more common wrist) | B4 (no connection), T1 signal. Ganglion is a distinct sac, does not connect to joint. |
| **Hemangioma or other vascular lesion** | T1 signal (fat sat, gadolinium if available). Hemangiomas have characteristic high signal on T1; simple cyst fluid is low on T1. |

### 6.6 Effects on Other Labels

- **Meniscal tears (Medial/Lateral):** Torn meniscus is a common cause of Baker's cyst (mechanical irritation → effusion → cyst). The two frequently co-occur; meniscal tear is the predisposing cause.
- **OA (Medial/Lateral/PF):** Chronic OA can cause effusion → Baker's cyst. Link is indirect.
- **Effusion:** Large joint effusion can feed a Baker's cyst. Effusion is the supply; cyst is the outcome.
- **Synovitis:** Inflammatory synovitis can increase fluid production → effusion → cyst. Indirect link.
- **ACL/MCL injury:** Acute ligament tear causes hemarthrosis → cyst. Possible but less common than with meniscal pathology.
- **Fracture/Contusion:** Trauma → hemarthrosis → cyst possible, but cyst formation is delayed.

### 6.7 What Host Labels Confirm; Near Misses

**Host label = 1 (Baker's Cyst present) confirms:**
- A popliteal cyst (fluid sac) is visible on imaging, >1 mm diameter, with at least one sign of joint origin (connection or recess fluid).

**Near misses:**
- Tiny cyst (<5mm) without visible stalk. Teaches the lower size threshold.
- Cyst + concurrent effusion. Teaches that both are present and related.
- Cyst + meniscal tear. Teaches the mechanical link.
- Ruptured cyst: empty sac in popliteal space + edema/fluid in calf. Teaches the clinical outcome and imaging appearance of rupture.

---

## 7. CONTUSION (Bone Bruise, Bone Marrow Edema)

### 7.1 Definition

**Host definition (FACT):** Not explicitly provided. **Domain reading:** Edema (fluid/swelling) in bone marrow, typically in the subchondral or cancellous bone, secondary to trauma or impact injury. Characterized by high signal on T2-weighted imaging within bone.

**Scope (PROPOSAL):** Contusion is an acute bone injury (microfractures, blood vessel rupture, marrow edema) without a visible cortical or trabecular fracture line. Often seen in ACL injuries or other blunt trauma.

### 7.2 Structural Reason

**Anatomy (DOMAIN):**
- **Bone structure:** Cortex (dense outer shell), trabeculae (inner lattice), bone marrow (fat and blood cells).
- **Contusion mechanism:** Impact or stress causes microfractures in trabeculae and rupture of small blood vessels; blood and edema accumulate in marrow spaces.
- **Subchondral location:** Contusions often occur in the bone just under articular cartilage (subchondral bone) due to high contact stresses.
- **Common sites in knee injury:** Femoral condyles, tibial plateau, lateral aspect (in ACL injury from pivot mechanism).

**MR Physics (DOMAIN):**
- **T2-weighted (FS=1, Fluid-Sensitive):** Edema is high-signal (bright) because edema = water, and water is bright on T2.
- **T1-weighted (standard):** Edema is low-signal (dark) because fat (normal marrow signal) is replaced by water.
- **STIR (another T2-sensitive sequence):** Suppresses fat, making edema (water) even brighter.
- **Best planes:** Sagittal and Coronal T2 (FS=1) show bone contusions.
- **Timing:** Edema appears within minutes to hours of injury; resolves over weeks to months.

**Pathophysiology (DOMAIN):**
- **Acute (days):** Edema is fresh, maximal signal.
- **Subacute (weeks):** Edema may persist, but marrow signal normalizes as healing occurs.
- **Chronic (months):** Edema resolves; may be replaced by fibrosis or cyst formation.
- **Associated injury:** Contusion often accompanies acute meniscal tear or ACL tear (from the same trauma).

### 7.3 Thermometers (Lenses)

| # | Lens Name | Site | Series/Plane | Measurement |
|---|-----------|------|--------------|-------------|
| C1 | Bone Marrow Edema Presence | Bone marrow space, typically subchondral | Sagittal T2 (FS=1) + Coronal T2 (FS=1) | Present (1) or absent (0) |
| C2 | Edema Location | Anatomical site of edema (e.g., medial femoral condyle, lateral tibial plateau) | Sagittal + Coronal | Specific location named |
| C3 | Edema Volume / Extent | Size of edematous region | Sagittal + Coronal T2 (FS=1) | Small (≤1 cm²), moderate (1–3 cm²), large (>3 cm²) |
| C4 | T2 Signal Intensity of Edema | Brightness of edema on T2 | Sagittal T2 (FS=1) | Mild (faint, low signal), moderate (intermediate), marked (very high signal) |
| C5 | T1 Signal Drop | Dark signal on T1 (indicating water/edema displacing fat) | Sagittal T1 (standard) | Present (1) or not clearly seen (0) |
| C6 | Fracture Line Presence | Visible fracture line in the same region as edema | Sagittal + Coronal T1 (standard) | Present (1) or absent (0) |
| C7 | Location Relative to Anatomical Structure | Subchondral (under cartilage), trabecular (deeper in bone), or other | Sagittal + Coronal | Depth/location category |
| C8 | Associated Effusion / Hemarthrosis | Joint effusion near the contusion site (suggests acute trauma) | Sagittal T2 (FS=1) | Small, moderate, or large effusion present (0–3) |
| C9 | T2 Hyperintensity Pattern | Shape/pattern of edema: band-like, round, linear (suggests direction of force) | Sagittal T2 (FS=1) | Pattern type (can infer mechanism) |

**Calibration note:** Normal bone marrow is low-intermediate signal on T2 (fat). Edema (high signal on T2, low on T1) is abnormal and indicates recent trauma.

### 7.4 Paths (Diagnostic Rules)

**DEFINITIONAL Contusion:**
- **PATH D1:** (C1 = present) AND (C4 = moderate or marked) AND (C6 = 0, no fracture line) AND (C8 ≥ 1, some effusion). [Bone edema without fracture + effusion = contusion from acute trauma]
- **PATH D2:** (C1 present) AND (C3 large, >3 cm²) AND (C5 T1 dark signal present). [Large edema + T1 confirmation = definite contusion]
- **PATH D3:** (C1 present) AND (C2 location matches ACL injury pattern, e.g., lateral femoral condyle + posterolateral tibia) AND (C8 moderate-large effusion). [Classic ACL injury contusion pattern + hemarthrosis]

**STRICT EXCLUSION:**
- **EXCL E1:** (C1 = 0, no edema) AND (C6 = 0, no fracture) on visible Sagittal and Coronal T2/T1. [Absence of edema and fracture = no contusion]
- **Note:** Fractured bone is separate (fracture label); contusion without fracture line is this label.

**DIRECTIONAL:**
- **(C1 present) + (C4 marked) + (C8 large effusion) → FOR (high confidence).** Severe edema + hemarthrosis = acute trauma.
- **(C1 present) + (C3 large) → FOR (moderate–high).** Large edema is significant.
- **(C1 present) + (C4 mild, faint) + (no effusion) → AGAINST (weak).** Faint edema in chronic knee could be old/resolved contusion or artifact.
- **(C2 location typical for ACL injury) → FOR (moderate–high).** Specific location pattern enhances confidence.
- **(C9 linear/band pattern) → FOR (moderate).** Pattern can indicate direction of force.

**ABSTAIN:**
- Sagittal T2 (FS=1) and Sagittal T1 required for edema detection.
- Coronal T2 (FS=1) helpful for location.
- If T2 sequence is motion-corrupted or unreadable, abstain.
- If no clear T1 drop, harder to confirm edema (could be artifact on T2 alone).

### 7.5 Mimics and Confounders

| Mimic | Distinguishing Lens |
|-------|-------------------|
| **Normal bone marrow signal** (especially in distal femur, which can be bright) | C4 (intensity), C5 (T1). Normal marrow is low-intermediate on T2; very high signal is edema. T1 should be dark in edema. |
| **Fat necrosis / marrow infarction** | C6 (fracture/infarction line), clinical history (absent here). Infarction has a geographic boundary with a sclerotic line; contusion edge is more diffuse. |
| **Artifact or motion** | C1 (distribution), C4 (signal intensity). Artifact is often geometric or patchy; contusion is organic, respects anatomy. |
| **Cystic or lytic lesion** (bone tumor, infection) | History, location (rare in condyles), progression (absent data). Lesions are often focal, well-defined; contusion is diffuse edema. |
| **Osteochondral injury** | C6 (fracture line), cartilage damage. Osteochondral injury includes a fracture line separating a cartilage + bone fragment; contusion is marrow edema without separation. |

### 7.6 Effects on Other Labels

- **Fracture:** Contusion often accompanies fracture (same trauma). They are distinct: fracture has a line; contusion is just edema. Both can be present.
- **ACL/MCL injury:** Contusion is the bone's response to the force that tore the ligament. Contusion presence and location help confirm acute ACL injury.
- **Meniscal tears (Medial/Lateral):** Trauma causing meniscal tear can also cause contusion. Two outcomes of the same mechanism.
- **Ligament injuries:** Acute ligament tear → hemarthrosis → contusion. The soft-tissue tear is primary; contusion is secondary.
- **Effusion:** Contusion (acute) produces hemarthrosis (complex effusion). Effusion is a consequence.

### 7.7 What Host Labels Confirm; Near Misses

**Host label = 1 (Contusion present) confirms:**
- Bone marrow edema (high T2 signal, low T1 signal) is visible without a fracture line.
- Radiologist judged it to be bone bruising (from trauma).

**Near misses:**
- Contusion + concurrent fracture. Both are trauma outcomes; teaches distinction (edema vs line).
- Contusion + ligament tear (ACL/MCL). Teaches the pattern in acute ACL injury.
- Contusion + meniscal tear. Teaches mechanism (rotational injury damages both).
- Chronic contusion (old edema, partially resolved). Teaches the age-dependent appearance.

---

## 8. FRACTURE (Bone Fracture)

### 8.1 Definition

**Host definition (FACT):** Not explicitly provided. **Domain reading:** Disruption of bone continuity (cortical or trabecular) visible as a line or gap on imaging. Includes acute (traumatic) and stress fractures.

**Scope (PROPOSAL):** Fracture is a structural break in bone, not just edema (contusion). Common knee fractures: tibial plateau, femoral condyle, patellar, fibular head.

### 8.2 Structural Reason

**Anatomy (DOMAIN):**
- **Cortex:** Dense outer shell of bone; fractures of cortex are usually visible as a dark line on T1 and T2.
- **Trabeculae:** Inner lattice of cancellous bone; fractures disrupt the trabecular pattern.
- **Fracture types:** Simple (clean break), comminuted (fragmented), intra-articular (extends into joint surface), and others.
- **Common sites in knee:** Tibial plateau (from varus/valgus stress), femoral condyle (from direct impact or rotational injury), patellar (direct blow), fibular head (avulsion or direct).

**MR Physics (DOMAIN):**
- **Cortical fracture:** Appears as a dark (low-signal) line on both T1 and T2, because cortex is dense (low water content).
- **Trabecular fracture:** May show as a line of low signal on T2 (impacted trabeculae), or as a disruption of the normal trabecular pattern.
- **Fracture gap:** If separated, appears as fluid (high T2 signal) in the gap.
- **Associated edema:** Fractures are nearly always accompanied by edema in surrounding bone and soft tissues.
- **Best planes:** Sagittal and Coronal T1/T2 for line detection; Axial for cross-section.

**Biomechanics (DOMAIN):**
- **Mechanism:** Direct impact, torsional (rotational) load, axial compression, or stress (repetitive microtrauma).
- **Age factor:** Older bone (osteoporotic) fractures more easily; younger bone is more ductile (stress fracture more common).

### 8.3 Thermometers (Lenses)

| # | Lens Name | Site | Series/Plane | Measurement |
|---|-----------|------|--------------|-------------|
| F1 | Fracture Line Presence | Visible dark line of cortical or trabecular disruption | Sagittal T1 (standard) + Coronal T1 | Present (1) or absent (0) |
| F2 | Fracture Line Visibility on T2 | Fracture line on T2 (darker line, may be less obvious than T1) | Sagittal T2 (FS=1) or (FS=0) | Visible (1) or not (0) |
| F3 | Fracture Location | Anatomical site (tibial plateau, femoral condyle, patella, fibular head, etc.) | Sagittal + Coronal | Site name (e.g., "posteromedial tibial plateau") |
| F4 | Fracture Extent / Orientation | Length and orientation of fracture line | Sagittal + Coronal | Linear dimension in mm, orientation (transverse, sagittal, coronal, rotational) |
| F5 | Fracture Gap / Displacement | Separation between bone fragments (0 if nondisplaced) | Sagittal + Coronal + Axial | Displacement distance in mm (0 = nondisplaced) |
| F6 | Fracture Pattern | Simple (one line), comminuted (multiple fragments), intra-articular (extends to joint surface) | Sagittal + Coronal | Pattern type |
| F7 | Subchondral / Articular Surface Involvement | Does fracture extend into joint cartilage / articular surface? | Sagittal T2 (FS=1) + Coronal | Involvement present (1) or confined to metaphysis/diaphysis (0) |
| F8 | Associated Edema / Hemorrhage | Surrounding bone edema or soft-tissue hemorrhage | Sagittal + Coronal T2 (FS=1) | Edema volume: small, moderate, large |
| F9 | Impaction / Compression Fracture | Evidence of bone impaction (flattening of surface) | Sagittal T1/T2 | Present (1) or not (0) |
| F10 | Healing Stage / Age | Acute (sharp line, max edema), subacute (blurred, edema present), chronic (sclerotic border, no edema) | Sagittal T1 + T2 | Stage: acute (<3 weeks), subacute (3–12 weeks), chronic (>12 weeks)—estimated from appearance |

**Calibration note:** Fracture line is a dark line on T1. Edema and hemorrhage are high signal on T2. The two together (line + edema) = fracture.

### 8.4 Paths (Diagnostic Rules)

**DEFINITIONAL Fracture:**
- **PATH D1:** (F1 = present, line visible on T1) AND (F4 ≥ 5mm length) AND (F8 associated edema). [Clear fracture line + surrounding edema = fracture]
- **PATH D2:** (F1 present) AND (F7 = 1, extends to joint surface) AND (F9 = 0, not impacted). [Intra-articular fracture without impaction]
- **PATH D3:** (F1 present) AND (F5 > 2mm displacement). [Displaced fracture]
- **PATH D4:** (F9 = 1, impaction/flattening) AND (F8 edema present) AND (F1 may or may not show clear line). [Impaction fracture; line may not be obvious, but flattening + edema = fracture]

**STRICT EXCLUSION:**
- **EXCL E1:** (F1 = 0, no line on T1) AND (F2 = 0, no line on T2) AND (F9 = 0, no impaction) AND (F8 absent on T2) on visible Sagittal T1, Sagittal T2, Coronal T1. [Absence of line, impaction, and edema = no fracture]

**DIRECTIONAL:**
- **(F1 present) + (F4 ≥ 5mm) + (F8 large) → FOR (high confidence).** Clear line + large edema = definite fracture.
- **(F1 present) + (F4 < 3mm) + (F8 small) → FOR (moderate).** Tiny line + minimal edema; could be old or artifactual.
- **(F5 > 5mm displacement) → FOR (high confidence).** Displaced fracture is unmistakable.
- **(F6 = comminuted) → FOR (high confidence).** Multiple fragments = severe fracture.
- **(F7 = 1, intra-articular) → FOR (moderate–high).** Joint surface involvement worsens prognosis; confirms fracture.
- **(F10 = chronic, sclerotic border) + (F8 = no edema) → AGAINST (weak).** Chronic healed fracture is not acute.

**ABSTAIN:**
- Sagittal T1 (standard) and Sagittal T2 required for fracture line and edema.
- Coronal T1/T2 helpful for location and extent.
- If motion artifact or metal artifact obscures the region, abstain.
- If no edema and line is equivocal, abstain (could be old, artifact, or normal variant).

### 8.5 Mimics and Confounders

| Mimic | Distinguishing Lens |
|-------|-------------------|
| **Cortical irregularity / normal variant** | F1 (line), F4 (continuous line vs surface irregularity), F8 (edema). Normal variants don't have edema. |
| **Stress fracture (fatigue fracture)** | F1 (line may be subtle or absent initially), F4 (oriented along stress lines), F8 (edema may be marked despite hairline). Stress fractures are common in runners; mechanism differs but imaging is similar. |
| **Contusion / bone bruising** | F1 (no line), F6 (pattern). Contusion is just edema; fracture has a line. |
| **Healed fracture with callus** | F10 (sclerotic border, chronic). Old fracture has remodeled bone, no acute edema. |
| **Artifact / motion** | F4 (line should be geometrically plausible), F2 (line should be visible on T2 as well as T1). Artifact is patchy or directional; fracture line is organic. |
| **Metal or motion artifact mimicking a line** | Relation to metallic object (none here; no surgical hardware mentioned), artifact direction. |

### 8.6 Effects on Other Labels

- **Contusion:** Fractures are accompanied by contusion (edema in surrounding bone from the trauma). Contusion alone is a milder injury (no break).
- **Effusion / Hemarthrosis:** Fracture extending into joint (intra-articular) causes hemarthrosis. Effusion presence and complexity help confirm.
- **Ligament injuries (ACL/MCL):** Some fractures (e.g., avulsion of ligament attachment) occur with ligament tears. Pattern differs: fracture is bone break, ligament is soft tissue.
- **Meniscal tears:** Trauma causing fracture can also tear meniscus (e.g., tibial plateau fracture + medial meniscus tear). Two injury patterns from one mechanism.
- **OA (Medial/Lateral/PF):** Post-fracture arthritis can develop if intra-articular fracture or step-off. OA is a later consequence, not immediate.

### 8.7 What Host Labels Confirm; Near Misses

**Host label = 1 (Fracture present) confirms:**
- A fracture line (disruption of bone continuity) is visible on imaging, with or without displacement.
- Radiologist identified the break anatomically.

**Near misses:**
- Nondisplaced fracture (line visible, no gap). Teaches that lack of displacement doesn't exclude fracture.
- Intra-articular fracture + concurrent effusion/hemarthrosis. Teaches the joint involvement.
- Fracture + contusion (both present from same trauma). Teaches the distinction.
- Stress fracture (hairline, subtle edema). Teaches the mechanism and appearance differences.
- Fracture + subsequent healing (sclerotic border, edema resolving). Teaches temporal progression.

---

## Summary: Lenses and Conjunctions

The 8 joint-level findings are diagnosed through conjunctions of simple thermometer readings:

1. **Medial OA / Lateral OA / PF OA:** Cartilage thinning + joint space narrowing + osteophytes + sclerosis.
2. **Effusion:** Fluid thickness >2 mm in joint recesses; volume category.
3. **Synovitis:** Synovial thickening >2 mm, intermediate-high signal, possibly pannus pattern.
4. **Baker's Cyst:** Popliteal fossa fluid sac, with stalk or recess connection.
5. **Contusion:** Bone marrow edema (high T2, low T1) in subchondral/cancellous bone, without fracture line.
6. **Fracture:** Visible line disruption (low signal T1/T2) in cortex or trabeculae, ± displacement, ± impaction.

Each reading is calibrated against normal population values at the registered anatomical site and sequence. Conjunctions assign labels (DEFINITIONAL), exclude them (STRICT EXCLUSION), or modulate confidence (DIRECTIONAL). Abstention is principled: missing series, artifacts, or truly ambiguous readings.

---

## Open Questions for the Founder

1. **Scope and severity thresholds:** The lenses use size cutoffs (mm, cm²) and signal intensity scores (0–2 or 0–3). Are these thresholds correct? Example: Is joint space < median−2mm the right cutoff for "narrowing," or should it be different?

2. **Weighting among lenses:** A conjunction like "cartilage thinning + space narrowing + osteophytes" assigns OA. If only two of the three are present (e.g., thin cartilage + osteophytes, but space normal), is that enough? What is the confidence?

3. **Interaction effects:** Some lenses can cancel or amplify others. Example: large effusion *suggests* acute inflammation (synovitis, recent injury), not just reactive OA. Should effusion *lower* confidence in primary OA diagnosis, or is the two labels' co-occurrence expected?

4. **Synovitis vs OA:** Is mild synovitis (S1–S3 = 2–2.5 mm, low signal) in a patient with chronic OA diagnostic of synovitis, or is it just reactive inflammation and not counted as synovitis? Should there be a minimum severity?

5. **Baker's cyst connection:** Is a visible stalk (B4) required, or is cyst presence + medial recess fluid (B7) enough to confirm joint origin? Can a cyst be present without visible connection?

6. **Contusion vs fracture:** If bone shows edema (high T2) but the fracture line is very subtle or not visible on T1, is this contusion or undiagnosed fracture? What is the decision boundary?

7. **Fracture displacement threshold:** Is any displacement (F5 > 0) enough to note it, or is there a minimum (e.g., >1 mm, >2 mm) below which it is classified as nondisplaced? Does displacement change the diagnosis or just severity?

8. **Age / temporal context:** Some lenses depend on the assumption that edema/effusion is acute (days). Without patient age or symptom onset (absent in test data), how is a chronic knee assessed? Example: old contusion with residual edema.

9. **Prevalence and balancing:** The labeled dataset is 58 studies, with widely varying label prevalence (Effusion 35 pos, PF OA 21 pos, Baker's 12 pos). Should low-prevalence labels (MCL 9 pos) be treated differently? Should the training path weight near-miss learning differently?

10. **Category mapping:** The host provides binary labels (0/1) per study. Are these "presence of *any* severity" (even trace/mild)? Or is there an implicit severity threshold (e.g., >mild = 1, mild or none = 0)? This affects how to tune lens thresholds.

---

## Remarks on Method and Warrant

Each lens is built on **measurement theory** (mapping an empirical structure to numbers without interpretation) and **structure** (anatomy, MR physics, mechanics of injury—the domain's laws). Conjunctions are written before running the data; thresholds (e.g., "cartilage <1σ below normal") reflect normal-population variation and are anchored in radiology textbooks, not fit to the host labels.

**Near-miss learning:** Where a lens fires and the host label disagrees, the residual is recorded (e.g., "early OA with only fibrillation visible, host labels it positive"). This teaches the directional confidence: a single weak lens can assign a label in isolation, or several weak lenses must combine.

**Abstention is a virtue:** Missing series, motion artifact, or truly ambiguous readings warrant silence, not guessing.

This report is a proposal. Each lens, threshold, and path stands only if the founder agrees it measures what it claims and is calibrated correctly. The next step is to pin the paths with host labels, discover near misses, and iterate thresholds.

