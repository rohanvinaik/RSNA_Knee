# Between the Twelve Labels: Structure, Co-Occurrence, and Resolution Order

**Date:** 2026-10-10  
**Status:** First structural analysis of label relationships, anatomical clustering, and diagnostic interdependencies  
**For:** The founder's ruling on warrant classes, exclusions, and resolution order

---

## 1. Overview: The Twelve Labels and Their Clustering

**SOURCE:** Medical domain knowledge (DOMAIN); facts from 00_facts.md (FACT)

The twelve target labels cluster into three anatomical and functional groups by the structures and processes they describe:

| Group | Labels | Nature | Anatomical Basis |
|-------|--------|--------|------------------|
| **A: Ligaments** | ACL, MCL | Discrete structural injuries | Connective tissue; each serves a specific biomechanical role |
| **B: Menisci** | Medial Meniscus, Lateral Meniscus | Discrete structural injuries | Paired fibrocartilage discs in tibiofemoral joint |
| **C: Joint-level findings** | Medial OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's, Contusion, Fracture | Degenerative, inflammatory, or traumatic | Three compartments (tibiofemoral medial, tibiofemoral lateral, patellofemoral) + joint inflammation + joint fluid + posterior cyst + bone trauma |

Group C is heterogeneous by mechanism (degeneration vs. inflammation vs. trauma) but unified by affecting the joint as a whole organ.

---

## 2. Co-Occurrence by Mechanism and Anatomy

### 2.1 The Traumatic Cluster: Fracture, Contusion, Acute Ligament/Meniscal Tears

**Co-occurrence mechanism (DOMAIN):**  
All four result from a single mechanical impact. The anatomy determines what breaks:
- **Fracture:** High-energy impact; bone gives way. The most severe traumatic finding.
- **Contusion:** Bone or soft tissue bruising from impact; indicates trauma occurred.
- **Ligament tears (ACL/MCL):** Sudden deceleration + rotation, or direct force. Common in high-energy trauma.
- **Meniscal tears:** Rotation + flexion, often paired with ligament injuries. The "unhappy triad" (ACL + MCL + medial meniscus) is a classical pattern (DOMAIN).

**What this means for structure (DOMAIN):**  
If a fracture is present, contusion is likely (same impact). If ACL is torn by mechanism, a meniscal tear on the same side is plausible (same rotational mechanism). The co-occurrence is not random; it follows injury mechanics.

**Observed in training labels (FACT):**  
Among 58 labeled studies:
- Fracture: 18 positive (31% of labeled studies)
- Contusion: 19 positive (33%)
- ACL: 24 positive (41%)
- Medial Meniscus: 26 positive (45%)
- Lateral Meniscus: 23 positive (40%)

High prevalence of all four suggests they may travel together, but the facts alone do not prove co-occurrence counts.

---

### 2.2 The Degenerative Cluster: OA Compartments, Effusion, Synovitis, Baker's Cyst

**Co-occurrence mechanism (DOMAIN):**  
Chronic joint wear (OA) and inflammatory response form a feedback loop:
- **OA progression:** Cartilage loss → bone remodeling → joint space narrowing → irregular articular surfaces.
- **Synovitis response:** Inflammation of the synovial membrane, triggered by cartilage fragments, bone exposure, or mechanical irritation.
- **Effusion consequence:** Synovial inflammation produces fluid. Effusion fills the joint space.
- **Baker's cyst formation:** Chronic effusion + synovitis can allow synovial herniation through the posterior joint capsule, forming the popliteal (Baker's) cyst.

**The three OA compartments (DOMAIN):**  
The knee has three articulations, each can degenerate independently:
1. **Medial tibiofemoral:** Inner compartment. OA here reflects wear on the medial surfaces.
2. **Lateral tibiofemoral:** Outer compartment. OA here reflects lateral-side wear.
3. **Patellofemoral (PF):** Knee cap articulation. OA here reflects wear on the undersurface of the patella and femoral groove.

These can occur together (pan-compartmental OA) or in any combination, depending on load distribution, alignment, and injury history (DOMAIN).

**Observed in training labels (FACT):**  
Among 58 labeled studies:
- Medial OA: 15 positive (26%)
- Lateral OA: 11 positive (19%)
- PF OA: 21 positive (36%)
- Effusion: 35 positive (60%)
- Synovitis: 27 positive (47%)
- Baker's: 12 positive (21%)

Effusion is the most common (60%), consistent with it being secondary to multiple primary pathologies. High prevalence of synovitis (47%) suggests strong association with OA and effusion.

**Dependency structure (DOMAIN, PROPOSAL):**  
- **Synovitis → Effusion:** Inflammation is a mechanism that produces fluid. A reading of synovitis warrants higher confidence in effusion.
- **OA → Effusion:** Chronic cartilage loss and bone exposure trigger inflammation → effusion. All three OA compartments can independently drive effusion.
- **Effusion → Baker's:** Chronic effusion under pressure can herniate posteriorly. Effusion presence raises confidence in Baker's.

---

### 2.3 The Ligament-Meniscal Association: ACL + Menisci, MCL + Medial Meniscus

**Co-occurrence mechanism (DOMAIN):**  
The "unhappy triad" (or "terrible triad" with ACL) is a classical injury pattern:
- **Pivot shift injury:** Internal rotation of the tibia relative to femur while the foot is planted. This mechanism can tear:
  - ACL (anterior cruciate ligament ruptures from tension)
  - Medial meniscus (inner meniscus gets pinched and tears)
  - MCL (medial collateral can also be stretched/torn)

**Anatomical basis (DOMAIN):**  
The medial meniscus is attached to the joint capsule and MCL. A valgus (inward-bending) + rotational force can tear both MCL and the meniscus as a unit. The lateral meniscus is less firmly attached, so lateral-side pivoting more often tears the lateral meniscus alone or with ACL but not MCL.

**Lenses that isolate them (DOMAIN, PROPOSAL):**  
- **ACL:** Typically seen at the intercondylar notch. Discontinuity of the ligament, edema in the notch, or Segond fracture (small fracture of the lateral tibial rim, pathognomonic for ACL tear).
- **MCL:** Runs along the medial joint line. Edema/signal change along its course, thickening, or discontinuity.
- **Medial Meniscus:** Crescent-shaped, internal to the medial joint line. Tear patterns: vertical split (bucket-handle), horizontal, or radial cleavage.
- **Lateral Meniscus:** Crescent-shaped, internal to the lateral joint line. Tear patterns similar but location differs by 360° rotation around the joint.

The location in the registered frame (medial vs. lateral compartment, intercondylar notch vs. joint line, anterior vs. posterior) is the primary lens for separating them.

---

## 3. Hard-to-Separate Pairs and Sets

### 3.1 Medial OA vs. Lateral OA: Same Mechanism, Different Compartments

**What makes them hard to separate (DOMAIN):**  
Both are osteoarthritis (cartilage loss, bone remodeling, joint space narrowing). The imaging signatures are identical:
- Thinned articular cartilage
- Bone marrow edema
- Marginal osteophytes (bone spurs)
- Joint space narrowing
- Subchondral cysts

The only difference is **location** (medial vs. lateral tibiofemoral compartment).

**Isolating lens (DOMAIN, PROPOSAL):**  
**Anatomical compartment in the coronal plane:**
- **Medial:** The reading sits on the medial (inner) surfaces of tibia and femur, measured in coronal images.
- **Lateral:** The reading sits on the lateral (outer) surfaces of tibia and femur, measured in coronal images.

A single lens — cartilage thickness or joint space width measured at the medial vs. lateral compartment in a coronal view, compared against the population normal at that exact location — isolates the two with certainty. The law is anatomy: medial and lateral are distinct places.

**Cross-label effects (DOMAIN):**  
- **Load redistribution (PROPOSAL):** In varus knee alignment (bow-legged), load shifts medially, accelerating medial OA. In valgus alignment (knock-kneed), load shifts laterally, accelerating lateral OA. Presence of one may raise confidence in the other if they appear together, but they are independent in principle.
- **PF OA independence (DOMAIN):** Patellofemoral OA is entirely independent of medial/lateral tibiofemoral OA. A person can have PF OA without tibiofemoral OA, or vice versa, or all three. The patella articulates with a different bone surface (femoral groove) and experiences different biomechanics.

---

### 3.2 Medial Meniscus vs. Lateral Meniscus: Same Structure, Mirror Locations

**What makes them hard to separate (DOMAIN):**  
Both are menisci (fibrocartilage, C-shaped discs sitting in the tibiofemoral joint). They have:
- Similar internal architecture (peripheral vascular supply, central avascular zone)
- Similar tear patterns (vertical, horizontal, radial cleavage, bucket-handle)
- Similar imaging appearances (dark on T2, bright signal in tear)

The lenses that detect a tear in one look identical to lenses that detect a tear in the other.

**Isolating lens (DOMAIN, PROPOSAL):**  
**Anatomical location in the coronal plane:**
- **Medial meniscus:** Sits medial to the tibial eminence, on the medial facet of the tibia. Attached to the joint capsule and MCL.
- **Lateral meniscus:** Sits lateral to the tibial eminence, on the lateral facet of the tibia. Looser attachment to capsule.

The location in the registered frame (coronal plane, medial vs. lateral position) is the isolating lens. Sagittal images can sometimes see a meniscal tear, but the coronal plane best shows which meniscus.

**Cross-label effects (DOMAIN):**  
- **Mechanism-based association:** As noted in §2.3, ACL injuries tend to accompany medial meniscus tears; lateral meniscus tears occur more often with ACL alone or in chronic instability. But the association is probabilistic, not deterministic (DOMAIN).
- **Independence:** The two menisci are independent structures. A person can have one torn without the other.

---

### 3.3 Effusion vs. Synovitis: Fluid vs. Inflammation

**What makes them hard to separate (DOMAIN):**  
- **Effusion:** Fluid in the joint space. On T2-weighted images, appears bright (high signal).
- **Synovitis:** Inflammation of the synovial membrane (the tissue lining the joint). On T2-weighted images, the membrane itself may thicken and show enhancement with contrast (if available; no contrast in this competition's data).

Without contrast, synovitis is detected indirectly: as inflammation causing effusion, or by synovial membrane thickening visible on high-resolution sequences.

**The causal relationship (DOMAIN):**  
Synovitis (inflammation) produces effusion (fluid). But effusion can also be:
- Secondary to mechanical injury (meniscal or ligamentous tear → blood in the joint)
- Secondary to fracture (joint bleeding)
- Secondary to OA (debris in the joint, cartilage fragmentation)
- Idiopathic or from systemic inflammation (not seen as a separate label here)

**Lenses that attempt isolation (DOMAIN, PROPOSAL):**  

1. **Effusion lens: Joint fluid volume**  
   - Measure or estimate the amount of T2 bright signal (fluid) in the joint space.
   - Compare against the population normal at baseline.
   - This is a direct measurement; it never says what caused the fluid.

2. **Synovitis lens: Synovial membrane signal and thickening (NOT AVAILABLE HERE)**  
   - On high-resolution T2 or with gadolinium contrast, the synovial membrane can be seen and measured.
   - This competition provides no contrast; membrane thickness is hard to detect reliably.
   - A proxy: extensive synovitis may cause very large effusion, but large effusion ≠ synovitis necessarily.

3. **Proposed isolation strategy (DOMAIN, PROPOSAL):**  
   - **Pure effusion lens:** Measure joint fluid volume or signal intensity in the joint space (T2, STIR, or fat-saturated sequences). Calibrate against population normal. This lens reports effusion presence/absence only.
   - **Synovitis signal lens:** Look for signal within the synovial membrane itself (thickening, T2 hyperintensity of the membrane), or for extensive global effusion as an indirect sign. This is weaker; it points directionally at synovitis but cannot decide alone.
   - **Rule of precedence (PROPOSAL):** Where ligament/meniscal/fracture pathology is present, effusion is likely reactive (secondary). Where no primary structural pathology is identified, extensive effusion suggests primary synovitis or inflammatory process.

---

### 3.4 Baker's Cyst vs. Large Effusion and Synovitis

**What makes them hard to separate (DOMAIN):**  
Baker's cyst is a popliteal (posterior) fluid collection that forms from chronic synovitis and effusion. In some cases, the cyst connects to the joint through a small neck. On imaging, a cyst looks like a focal fluid collection in the popliteal space (behind the knee).

**Isolating lenses (DOMAIN, PROPOSAL):**  

1. **Anatomical location:** Baker's cyst is specifically **posterior (popliteal space)**, between the medial head of gastrocnemius and the semitendinosus. A fluid collection at that exact anatomical site is a cyst. Axial images best show this location.

2. **Morphology:** A Baker's cyst should have:
   - Fluid-filled interior (bright on T2)
   - Thin capsule (the wall of the cyst)
   - Defined borders, often oval or round
   - Can be single or multiple
   - May contain internal debris (if chronic or ruptured)

3. **Separation rule (PROPOSAL):**  
   - **Large joint effusion alone:** Fluid fills the main joint space (anterior, medial, lateral recesses). Posterior extension may spill into the popliteal space, but the fluid is contiguous with the joint.
   - **Baker's cyst:** Discrete fluid collection in the popliteal space, often separated from the main joint space by tissue (the gastrocnemius muscle and cyst wall).

The distinction is location + morphology. A popliteal fluid collection **at the popliteal space anatomical site, with defined borders** is called Baker's. General joint effusion that may extend posteriorly is not.

**Cross-label effect (DOMAIN):**  
- Presence of Baker's indicates chronic effusion/synovitis (something is driving fluid production chronically).
- Baker's presence raises confidence in effusion (by definition, it is a fluid collection).
- Baker's may be independent of synovitis in terms of definition (presence of cyst ≠ synovitis must be present), but the presence of Baker's is strong evidence that the joint environment has been chronically inflammatory.

---

### 3.5 ACL vs. MCL: Different Ligaments, Different Mechanisms

**What makes them potentially confused (DOMAIN):**  
Both are ligaments with:
- Soft tissue composition (collagen fibers)
- Can show edema and rupture on T2-weighted images
- Both are stabilizers but serve different functions

**Isolating lenses (DOMAIN, PROPOSAL):**  

1. **Anatomical location:**
   - **ACL:** Runs **diagonally through the intercondylar notch** from the anterolateral tibia to the posteromedial femur. Best seen in sagittal images.
   - **MCL:** Runs **along the medial joint line**, from the medial femoral condyle to the medial tibia. Best seen in coronal images.

2. **Tear patterns:**
   - **ACL tear:** Discontinuity in the notch. Often associated with bone bruising on the lateral tibial plateau and medial femoral condyle (from the pivot shift mechanism, DOMAIN).
   - **MCL tear/strain:** Edema along the medial joint line. May see Pellegrini-Stieda lesion (calcification at the femoral attachment) in chronic cases.

3. **Associated injuries (DOMAIN):**
   - **ACL tear:** Often with medial meniscal tear, pivot shift mechanism.
   - **MCL injury:** Often with medial meniscal tear, valgus mechanism.

The location in the registered frame (intercondylar notch vs. medial joint line) is the isolating lens. They are in different anatomical compartments.

---

## 4. Explaining Away and the Halo: Two Relevances of the Same Thing

**Foundational principle (SOURCE: v7 §1.2):**  
"In an image of a bone, the edema around a fresh break is evidence for one question, whether a line that looks like a fracture is an active one. For another, where exactly the fracture runs, it is signal to take out of view. Evidence for one question and signal to take out of another's view are two relevances of the same thing, and to take a thing out of one question's view is not to count it as evidence against anything."

### 4.1 Edema and the Halo Effect

**In the knee context (DOMAIN, PROPOSAL):**

| Finding | Produces Halo | Halo Is Evidence For | Halo Is Signal To Remove From |
|---------|---------------|----------------------|------|
| **Fracture (bone)** | Bone marrow edema around the fracture line | Acute fracture; confirms fracture | Other traumatic soft tissue findings (does not confirm primary soft tissue injury; it is from fracture) |
| **ACL tear** | Edema in the intercondylar notch and around the torn ligament; bone bruising on opposite condyles (lateral tibia, medial femur from pivot) | Acute ACL rupture | Other ligament injuries or knee injuries (edema is from ACL mechanism, not primary evidence for other pathology) |
| **Meniscal tear** | Edema in the tear, potentially adjacent to joint capsule and MCL (if medial meniscus) or to lateral capsule (if lateral) | Acute or chronic meniscal tear | MCL (if medial meniscal tear, edema adjacent to MCL does not confirm MCL injury; it is halo from meniscus) |
| **Synovitis** | Edema of the synovial membrane; diffuse joint effusion | Inflammation; synovitis present | Specific structural pathology (synovitis is a consequence, not a primary injury; treating diffuse inflammation as evidence for a particular tear would be a misattribution) |

**The resolution order (PROPOSAL):**  
To avoid misattribution, resolve findings in order from the most definite to the most general:
1. **Fracture first:** Edema around it is the fracture's halo; not evidence for other injuries.
2. **Ligament and meniscal tears:** Their edema halos are specific to each structure's location; not evidence for each other (unless they occur together by mechanism).
3. **Traumatic contusions:** Bone bruising is evidence of impact; separable by location.
4. **Osteoarthritis:** Chronic changes; distinct from acute edema.
5. **Synovitis and effusion:** General inflammation and fluid; interpreted after specific pathologies are removed.

**Implementation (PROPOSAL):**  
Once a fracture is confidently assigned, note and record the extent of its bone marrow edema halo. That edema is removed from the differential for other findings in that region. The same for ACL tears, meniscal tears, etc. The halo is taken out whole with the finding it surrounds.

---

### 4.2 Edema as Evidence For and Signal To Remove

**The mechanism (DOMAIN):**  
Edema is water in tissues. Its location and context determine its meaning:
- Edema **around a fracture** = bone marrow edema from acute fracture = evidence FOR fracture.
- Edema **around a ligament tear** = ligament edema and hematoma = evidence FOR that ligament's injury.
- Edema **around the meniscus** = meniscal tear and halo = evidence FOR that meniscus.
- Edema **diffusely in soft tissues** = synovitis, inflammatory response = evidence FOR synovitis.

Once a finding's edema is identified and taken with its halo, that tissue is removed from further consideration for other findings. The edema is not evidence against those other findings; it is simply not available as a lens for them anymore (data-processing inequality, v7 §1.2).

---

## 5. Priority and Resolution Order

**The Wayfinder move (SOURCE: v7 §1.9, §4.6):**  
"Each structure resolved goes out with what its laws say it causes, and the residual is read again."

**Proposed resolution order for the knee (DOMAIN, PROPOSAL):**

### Stage 1: Traumatic Findings (High Specificity, Definite)

**1.1 Fracture**  
- **Why first:** Most definite. Bone discontinuity is unambiguous.
- **Lenses:** Cortical discontinuity, displacement, fracture lines, associated bone marrow edema.
- **What it carries out:** Its halo (bone marrow edema) and the traumatic mechanism.
- **What it removes from view:** Uncertainty about whether bone is intact. Any bone marrow edema in the fracture region is attributed to fracture, not to other processes.

**1.2 Contusion**  
- **Why second:** Bone marrow edema without cortical discontinuity. It is traumatic and definite.
- **Lenses:** Bone marrow signal abnormality (T2 hyperintensity or STIR bright); no cortical break.
- **What it carries out:** Its edema and the signal that an impact occurred.
- **What it removes from view:** The edema halo it produces is assigned to contusion, not to inflammatory processes.

### Stage 2: Ligament Injuries (High Specificity, Structural)

**2.1 ACL**  
- **Why third:** Ligament rupture is a discrete structural finding, separable by location (intercondylar notch).
- **Lenses:** 
  - Discontinuity or absence of the ACL ligament in the notch (sagittal images)
  - Associated bone bruising (lateral tibia, medial femur) from the pivot mechanism
  - Segond fracture (small fracture of lateral tibial rim, pathognomonic for ACL tear)
- **What it carries out:** Ligament discontinuity, its edema halo, and the pivot shift mechanism.
- **What it removes from view:** Edema in the notch and bruising pattern are attributed to ACL injury, not to other processes.

**2.2 MCL**  
- **Why fourth:** Ligament rupture/strain, separable by location (medial joint line).
- **Lenses:**
  - Edema along the medial joint line and MCL course
  - MCL discontinuity (in full tears)
  - Pellegrini-Stieda lesion (calcification at femoral MCL insertion, in chronic injury)
  - Associated bone bruising (medial femoral condyle, medial tibia)
- **What it carries out:** Ligament injury, edema, and the valgus/rotational mechanism.
- **What it removes from view:** Edema along the medial joint line and bruising are attributed to MCL, not to other processes.

### Stage 3: Meniscal Injuries (High Specificity, Structural)

**3.1 Medial Meniscus**  
- **Why fifth:** Discrete structural tear, separable by location (medial compartment, medial to tibial eminence).
- **Lenses:**
  - Meniscal signal abnormality (T2 hyperintensity = torn fibers)
  - Tear morphology (vertical, horizontal, radial, bucket-handle)
  - Location (medial compartment in coronal plane)
  - Associated synovitis or joint effusion (secondary)
- **What it carries out:** Tear, its signal halo, and the associated edema/inflammation.
- **What it removes from view:** Meniscal signal change is attributed to the tear, not to general joint inflammation.

**3.2 Lateral Meniscus**  
- **Why sixth:** Same as medial but on the lateral side.
- **Lenses:** Same as medial, location lateral in coronal plane.
- **What it carries out:** Tear, signal halo, associated inflammation.
- **What it removes from view:** Lateral meniscal signal change.

### Stage 4: Bone Degenerative Findings (Chronic)

**4.1 Medial OA, Lateral OA, PF OA**  
- **Why seventh:** Chronic degenerative changes. Separable by compartment (location in registered frame).
- **Lenses (per compartment):**
  - Cartilage thinning (segmentation or morphometry)
  - Joint space narrowing (measurement in coronal plane)
  - Bone marrow edema (subarticular, in bone)
  - Osteophytes (bone spurs at margins)
  - Subchondral cysts
- **What it carries out:** Degeneration, its bone marrow edema and inflammatory consequences.
- **What it removes from view:** The chronic bone marrow edema pattern is assigned to OA, not to acute trauma.
- **Cross-compartment rule (PROPOSAL):** The three compartments can be scored independently. No law requires them to occur together, but load redistribution may create an association. Presence of OA in one compartment should not lower confidence in OA in others.

### Stage 5: Inflammatory Findings (General, Reactive)

**5.1 Synovitis**  
- **Why eighth:** Inflammation of the synovial membrane. This is often secondary to structural pathologies (OA, meniscal tears, etc.) but can be primary (systemic inflammatory conditions).
- **Lenses:**
  - Synovial membrane thickening (best on high-resolution T2; limited here without contrast)
  - Global effusion (proxy for synovitis if extensive)
  - Enhancement on contrast (NOT available in this competition)
  - Associated with OA or inflammatory conditions
- **What it carries out:** Inflammation and its consequent effusion.
- **What it removes from view:** Once synovitis is identified, the global joint inflammation it causes is not re-attributed to other findings. But synovitis is often secondary; the primary pathology (OA, meniscal tear) should be identified first.

**5.2 Effusion**  
- **Why ninth:** Joint fluid. This is the most generic finding. It can be secondary to any structural or inflammatory pathology, or to systemic processes.
- **Lenses:**
  - T2-bright fluid signal in the joint space
  - Volume or extent of fluid
  - Population-normal baseline for that joint
- **What it carries out:** Fluid presence; the mechanism that produced it remains to be determined.
- **What it removes from view:** Once effusion is measured, the finding is recorded. But interpretation of what caused it depends on the stages above.

**5.3 Baker's Cyst**  
- **Why tenth:** A popliteal fluid collection. It is a consequence of chronic synovitis/effusion.
- **Lenses:**
  - Fluid collection at the popliteal space (anatomical location, posterior)
  - Cystic morphology (defined borders, capsule)
  - Location in axial images
- **What it carries out:** Chronic synovitis and effusion; indicates a long-standing inflammatory or degenerative state.
- **What it removes from view:** Once a Baker's cyst is identified, the posterior fluid is not re-counted as undifferentiated effusion in the joint. But the cyst implies that joint effusion and synovitis are chronically present.

---

## 6. Confidence Scoring: From Warrant to Confidence Score

**The task (FACT):**  
Submit confidence scores in [0, 1] for each of the 12 labels per study. Metric is macro-averaged ROC-AUC (each label scored independently, then averaged).

**What a confidence score represents (DOMAIN, PROPOSAL):**  
A score in [0, 1] is the posterior probability that the label is present in that study, given:
- The lenses (readings at sites in the registered frame)
- The lenses' warrant classes (strict, directional, abstain)
- The population reference (normal distribution at each site)
- The cross-label dependencies identified above

**Structure of the scoring logic (PROPOSAL):**

### 6.1 Basis: Warrant Class

Each lens has a warrant class, from the founding law (AGENTS.md Law 10):

| Warrant Class | Definition | Role in Scoring |
|---|---|---|
| **DEFINITIONAL** | The reading is what was measured, or anatomy/physics makes the conjunction certain. | Raises confidence to near-certainty (0.9–0.95+) if multiple independent lenses agree. May decide alone if stated law warrants. |
| **STRICT EXCLUSION** | A law of anatomy, physics, or the label's definition says on which side the reading cannot err. | Lowers confidence to near-zero (0.05–0.1) or rejects the label entirely. Must name the law. |
| **DIRECTIONAL FOR** | Evidence that raises confidence; a mechanism explains why. Must be joined by other readings. | Raises confidence from baseline; magnitude depends on mechanism strength and independence. |
| **DIRECTIONAL AGAINST** | Evidence that lowers confidence. Must be joined by other readings. | Lowers confidence from baseline. |
| **ABSTAIN** | No reading warrants an assertion. The series cannot see the site, or no lens has fired. | Leaves confidence at baseline (0.5 or the prior). May open a question for the next observation. |

### 6.2 Baseline and Priors

**Population reference (PROPOSAL):**  
At each anatomical site (measured in each series type and anatomical plane), a normal population knee defines:
- Normal mean signal intensity or morphometry
- Normal variance (at 1 standard deviation, 2 SD, etc.)
- Normal absence of structural findings

A deviation at a site — a reading that differs from the normal range — is the temperature reading. The deviation alone does not yet say disease.

**Prior probability for each label (PROPOSAL):**  
- In the absence of any reading, the baseline confidence is the prevalence of the label in the population (or 0.5 if unknown).
- Among 58 labeled training studies:
  - Fracture: 18/58 = 31%
  - ACL: 24/58 = 41%
  - Effusion: 35/58 = 60%
  - (other labels: see 00_facts.md, §4)
  
These are not targets to tune toward. They are the prior that beliefs start from.

### 6.3 How Warrant Classes Build Confidence

**Scenario 1: Multiple DEFINITIONAL readings, independent**  
- Example: ACL tear confirmed by (a) ligament discontinuity in sagittal, (b) Segond fracture in lateral tibia, (c) bone bruising pattern.
- **Confidence:** 0.92–0.97 (high, but not 1.0 until the radiologist holds the study and rules). The three readings are independent lenses (different sites, different mechanisms); their agreement is strong.

**Scenario 2: One DEFINITIONAL reading + DIRECTIONAL FOR readings**  
- Example: Meniscal tear (DEFINITIONAL: tear signal on T2), with associated synovitis in adjacent soft tissues (DIRECTIONAL FOR: inflammation suggests recent or ongoing injury).
- **Confidence:** 0.85–0.92 (the tear is definite; the synovitis reinforces recency).

**Scenario 3: DIRECTIONAL FOR readings only, multiple and independent**  
- Example: Effusion suspected from (a) T2-bright signal in joint space (DIRECTIONAL FOR: indicates fluid), (b) synovitis on membrane (DIRECTIONAL FOR: inflammation produces fluid).
- **Confidence:** 0.70–0.85, depending on strength of mechanisms and independence of the two lenses.

**Scenario 4: DIRECTIONAL AGAINST readings**  
- Example: ACL suspected but anterior cruciate notch is clearly intact, and no bone bruising is seen on the typical impact sites.
- **Confidence:** 0.15–0.30 (evidence against, but absence of evidence is not definitive until the series reliably shows the site).

**Scenario 5: ABSTAIN**  
- Example: MCL injury suspected, but only axial images are available (not coronal), and the medial joint line is outside the field of view.
- **Confidence:** 0.5 (baseline; or the prior prevalence if known). The reading is silent. The next observation would be a coronal series.

### 6.4 Cross-Label Effects on Confidence

**Effect 1: Halo removal (PROPOSAL)**  
When finding A is identified with confidence ≥ 0.8, its halo (edema, associated inflammation) is assigned to A. Confidence in finding B (if B's lenses overlap with A's halo) should be reduced or held constant, not increased.

- Example: ACL tear (confidence 0.9) with associated bone bruising. Confidence in MCL (which might be suspected from medial-side bruising) should not rise because that bruising is halo from the ACL mechanism, not evidence of MCL injury.

**Effect 2: Mechanism-based association (PROPOSAL)**  
Where injury mechanisms cluster findings, presence of one raises posterior probability of the other.

- Example: ACL tear (confidence 0.9) and medial meniscus tear. The pivot shift mechanism that tears ACL is compatible with meniscal tear. Confidence in medial meniscus rises from baseline 45% (prevalence) toward 0.65–0.75.
- But this is not decision-making; it is a confidence adjustment based on mechanism.

**Effect 3: Dependency: Synovitis → Effusion (PROPOSAL)**  
- If synovitis confidence is 0.85, then effusion confidence should be raised to at least min(0.85, population-max-for-effusion) from its baseline, because synovitis produces effusion mechanically.
- Reverse: If effusion is seen with high confidence but no primary structural pathology is found, synovitis confidence rises directionally.

**Effect 4: OA compartments are independent (PROPOSAL)**  
- Medial OA, lateral OA, and PF OA are independent unless load redistribution or alignment is explicitly inferred.
- Presence of OA in one compartment does not raise confidence in another beyond the baseline (prevalence).

---

## 7. The Emission Policy: How Confidence Scores Are Assigned to the Submission

**The question (FOUNDER'S DECISION REQUIRED):**  
Given the warrant classes, the cross-label effects, and the resolution order, how is each label's confidence score computed?

**Options (PROPOSAL, for the founder's ruling):**

### Option A: Strict Warrant-Based Emission
- **DEFINITIONAL readings:** Confidence 0.85–0.95 (high, not absolute).
- **DIRECTIONAL FOR readings (multiple, independent):** Confidence 0.65–0.80.
- **DIRECTIONAL AGAINST readings:** Confidence 0.20–0.35.
- **ABSTAIN:** Confidence = prior prevalence (or 0.5).
- **Cross-label adjustments:** Halo removal (no boost), mechanism association (+0.10–0.15), dependency (+0.15–0.25).

**Rationale:** Conservative; confident in what is known, silent where nothing warrants.

### Option B: Probabilistic Integration
- Each lens contributes a likelihood ratio (LR) based on its warrant class and sensitivity/specificity in the domain (not tuned on training labels).
- Combine LRs via Bayesian update: P(label | lenses) ∝ P(lenses | label) × P(label).
- Emit the posterior probability.

**Rationale:** Principled; integrates mechanism and independence formally. Requires careful definition of each lens's LR.

### Option C: Conclave Voting (No Popery)
- Each lens is a member (agency) of a committee.
- Members vote: +1 (for), −1 (against), or 0 (abstain).
- Rule: Majority can decide (founder's ruling, 2026-10-10 00:15:00Z). Simple majority = 0.70 confidence. Unanimous + = 0.90. Disagreement = 0.50 (abstain).

**Rationale:** Aligns with founder's conclave epistemology. Clear contract before voting.

---

## 8. Strict Exclusions: Laws That Reject a Label

**The standard (AGENTS.md, Law 10 and revision 1 amendment):**  
"A lens takes the same standing only where the structure gives it: where a law of the domain, not a run of past successes, says on which side the lens cannot err."

### 8.1 Tautological Exclusions (Laws of Logic)

| Rule | Warrant | Source |
|------|---------|--------|
| If the **bone is intact** (no fracture), then **fracture label = 0** | STRICT EXCLUSION | Definition: fracture requires cortical discontinuity. Anatomy enforces this. |
| If the **ligament is continuous**, then **ligament tear = 0** | STRICT EXCLUSION | Definition: ligament injury requires rupture or discontinuity. Anatomy enforces this. |
| If the **meniscus is uniform in signal**, then **meniscal tear = 0** | STRICT EXCLUSION | Definition: tear requires signal abnormality or morphological disruption. Imaging physics enforces this. |

These are not domain-specific insights; they are definitions. They are useful for checking the lenses are working, but they do not narrow the problem space.

### 8.2 Anatomical/Physical Exclusions (Domain Laws)

**Candidate 1: If a **structure is not visible in a series**, then **ABSTAIN** on findings at that structure**  
- **Law:** The chain rule (v7 §1.3): a reading not made is unprocessed information. If a series cannot see a structure (FOV, sequence properties, patient position), no lens fires at that site.
- **Application:** Coronal images are required to see MCL and the medial/lateral joint line clearly. If only sagittal and axial images are available, MCL lenses cannot fire. Abstain on MCL.
- **Type:** Not an exclusion per se, but a ruling of silence. Confidence stays at baseline.

**Candidate 2: If **bone marrow edema is present but cortically the bone appears intact**, then that edema is **traumatic (contusion) not pathognomonic for fracture**, and **don't assume fracture without cortical evidence**.  
- **Law:** Bone marrow edema can be from trauma (impact), inflammation, or early fracture. The cortex is the gold standard. Edema alone cannot decide.
- **Application:** See bone marrow edema → measure confidence in contusion. See bone marrow edema + cortical disruption → measure confidence in fracture.
- **Type:** Not a strict exclusion, but a warrant-refinement rule.

**Candidate 3: If **the patellofemoral joint is normal** (no PF OA), can we exclude **significant patellofemoral subluxation or maltracking**?  
- **Law:** This is a different finding (biomechanical) than OA (degenerative). Normal PF OA does not exclude maltracking. These are independent.
- **Application:** N/A (subluxation is not in the label set).

**Candidate 4: If **Medial OA is present**, should the diagnosis **exclude Lateral OA**?  
- **Law:** No. OA in one compartment does not exclude OA in another. Load redistribution might increase risk, but they are anatomically independent.
- **Application:** No exclusion. Independence rule (§6.4, Effect 4).

**Candidate 5: Can **Effusion and Synovitis ever be strictly separated**?  
- **Law:** Synovitis produces effusion. Effusion can exist without measurable synovitis (if chronic and quiescent, or from other causes). So effusion presence does NOT exclude absence of synovitis, and synovitis presence DOES imply effusion (by mechanism).
- **Application:** Synovitis → Effusion (dependency rule). Effusion alone → ? on synovitis (silent; the mechanism is unknown).
- **Type:** Not a strict exclusion, but a dependency rule.

### 8.3 Proposed Strict Exclusions for the Founder's Ruling

**PROPOSAL 1: Silence on unseen anatomy is ABSTAIN, not EXCLUDE**  
- **Rule:** If a series cannot anatomically reach a site, no lens fires. Confidence remains at baseline.
- **Examples:** MCL in sagittal-only images (medial joint line outside FOV); anterior structures in only axial images.
- **Warrant:** Law of optics and imaging geometry (v7 §1.1).

**PROPOSAL 2: Ligament/meniscal tears cannot coexist with structural integrity at the same site**  
- **Rule:** STRICT EXCLUSION. If the ACL is continuously visible and intact throughout the registered frame, then ACL tear = 0.
- **Warrant:** Anatomical law: a ligament is either continuous or ruptured. Both cannot be true at the same site simultaneously.

**PROPOSAL 3: Fracture (cortical discontinuity) cannot coexist with intact bone at the same site**  
- **Rule:** STRICT EXCLUSION. If cortical continuity is confirmed at a site, then fracture at that site = 0.
- **Warrant:** Anatomical law: bone cortex is either continuous or broken. Both cannot be true at the same site simultaneously.

**PROPOSAL 4: No law-based strict exclusion exists between different labels (except tautologies above)**  
- **Rationale:** Most knee pathologies can coexist. Fracture + OA, ACL + meniscal + OA, synovitis + effusion are all medically plausible.
- **Exception:** The halo-removal rule means that once a finding's halo is identified, secondary edema/inflammation is not re-counted as evidence for other findings. But that is a computational rule, not a strict exclusion of the other finding's presence.

---

## 9. Summary Table: Warrant Classes for Each Label's Primary Lenses

**The table (PROPOSAL):**

| Label | Primary Lenses | Warrant Class | Can Decide Alone? | Cross-Label Dependencies |
|-------|---|---|---|---|
| **ACL** | Ligament discontinuity (sagittal); bone bruising (lateral tibia, medial femur) | DEFINITIONAL | Yes, if ligament discontinuity + bruising pattern | If present: halo removes local edema. Predicts medial meniscus tear (mechanism). |
| **MCL** | Edema along medial joint line (coronal); MCL signal/thickness | DIRECTIONAL FOR | No; needs coronal view | If ACL present: mechanism suggests MCL likely. If edema is halo from meniscal tear: adjust. |
| **Medial Meniscus** | Meniscal T2 signal abnormality (coronal); tear morphology | DEFINITIONAL | Yes, if tear is seen | If present: halo is local inflammation. Predicts synovitis/effusion. |
| **Lateral Meniscus** | Meniscal T2 signal abnormality (coronal); tear morphology | DEFINITIONAL | Yes, if tear is seen | If present: halo is local inflammation. Predicts synovitis/effusion. |
| **Medial OA** | Cartilage thinning + joint space narrowing (coronal, medial); bone marrow edema (subarticular) | DEFINITIONAL (for individual markers) | Yes, if multiple markers present | OA in one compartment is independent of others (unless load redistribution inferred). Predicts synovitis + effusion. |
| **Lateral OA** | Cartilage thinning + joint space narrowing (coronal, lateral); bone marrow edema | DEFINITIONAL (for individual markers) | Yes, if multiple markers present | Same as medial OA. |
| **PF OA** | Cartilage thinning (PF articulation); joint space narrowing (PF); bone marrow edema | DEFINITIONAL (for individual markers) | Yes, if multiple markers present | Independent of tibiofemoral OA. Predicts synovitis + effusion. |
| **Effusion** | T2-bright signal in joint space; volume/extent | DIRECTIONAL FOR | No; secondary to primary pathologies | Presence raises confidence in synovitis (if mechanism is inflammation). Presence lowers confidence if attributable to specific structural lesion (use halo-removal rule). |
| **Synovitis** | Synovial membrane thickening (DIRECTIONAL); diffuse effusion as proxy (DIRECTIONAL); absence of specific structural pathology (DIRECTIONAL FOR) | DIRECTIONAL FOR | No; needs multiple lenses | Synovitis presence predicts effusion (causal). Synovitis absence + effusion suggests structural cause. |
| **Baker's Cyst** | Popliteal fluid collection (axial, posterior space); cystic morphology; defined borders | DEFINITIONAL (for morphology) | Yes, if the popliteal collection is seen and distinct | Presence indicates chronic synovitis/effusion. Independent of other findings but implies inflammatory joint state. |
| **Contusion** | Bone marrow edema without cortical discontinuity (any sequence showing marrow signal) | DIRECTIONAL FOR | No; needs to rule out fracture first (if edema + discontinuity, it is fracture, not contusion) | Evidence of traumatic mechanism; predicts fracture/ligament/meniscal injuries. Edema is halo; remove when other findings claimed. |
| **Fracture** | Cortical discontinuity (any plane showing breach in cortex); displacement; fracture line | DEFINITIONAL | Yes, if discontinuity is seen | Halo (bone marrow edema) is assigned to fracture. Contusion and other traumatic findings are secondary to mechanism. |

---

## 10. Open Questions for the Founder

1. **Emission policy:** Which of Options A, B, or C (§7) is the approach? Or a hybrid?
2. **Conclave contract:** If conclave voting (Option C), what is the rule? Simple majority (≥6/10 lenses)? Two-thirds? Unanimous + for decision, disagreement = abstain?
3. **Synovitis definition:** Without gadolinium contrast, synovitis is hard to detect directly. Shall we treat it as a DIRECTIONAL-FOR lens that relies on global effusion + absence of structural pathology, or is there a better approach?
4. **Baker's independence:** Is Baker's presence independent of other findings, or is it best treated as a sign of chronic inflammatory state that raises confidence in synovitis/effusion jointly?
5. **Baseline and halo:** Once a finding's halo is identified and removed from view, should the confidence in other findings be re-normalized (e.g., if edema was 30% of evidence for synovitis, and edema is now assigned to ACL tear, does synovitis confidence drop?), or is halo removal passive (simply don't double-count that edema)?
6. **Near misses:** The training data has 58 labeled studies, with specific label distributions. Should these prevalences be used as priors, or should the prior be uniform (0.5) until lenses fire?

---

## Appendix: References to Founding Documents

- AGENTS.md: Project laws, warrant definitions, architect of conclave.
- thesis_reading_claude.md: The lens principle, the rigid oracle, section 9 on the thermometer and structure.
- v7 §1.1–§1.14: Information theory, lenses, warrant, halo effect, the three operations.
- 00_facts.md: Competition structure, data inventory, label definitions.
- FOUNDING_PROMPTS.md: Founder's original words on the teacher, the story, the thermometer.

---

**Status:** This report is a proposal for the founder's review. Every rule marked PROPOSAL awaits his ruling. Where consensus and warrant classes depend on the anatomy and MRI physics, those are marked DOMAIN and are checked against the radiological record.

