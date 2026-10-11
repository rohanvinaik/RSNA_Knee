# Wave 1: Lenses for the Menisci — Medial and Lateral

**Date:** 2026-10-10  
**Analyst:** Claude Code (via workflow)  
**Status:** Proposals for founder ruling on definitions, structural reasoning, and lens warrant  
**Reading base:** Thesis section 1 (information theory, measurement, warrant); thesis_reading_claude.md (lens principle and thermometer analogy); 00_facts.md (competition data)  

---

## Part 1: Medial Meniscus

### 1.1 Definition

**Host's label:** "Medial Meniscus" (FACT — from `sample_submission.csv` column name)

**Official definition from host:** None provided (FACT — 00_facts.md §1)

**Medical domain interpretation:** A tear or other abnormality of the medial meniscus (DOMAIN)

**What the label includes:** 
- Radiologist's detection of an abnormality in the medial meniscal structure on MRI (DOMAIN)
- The abnormality that warrants the diagnosis "present" / confidence score > 0 (DOMAIN)

**What the label excludes (PROPOSAL for founder ruling):**
- The scope of "abnormality" is not defined by the host. A reasonable structural reading: the label assigns confidence when the medial meniscus differs from the population of normal knees at the same site in a way anatomy and MR physics account for by the rules a radiologist uses.
- A normal medial meniscus, even if hypersignal or mild degenerative change within the range of normal variation, would score low confidence.

---

### 1.2 Structural Reason It Can Be Diagnosed

**Anatomy (DOMAIN):**

The medial meniscus is a C-shaped fibrocartilage structure within the knee joint, positioned between the medial femoral condyle (above) and the medial tibial plateau (below). It is held in place by:
- Capsular attachments (coronary ligaments) at its periphery
- Meniscofemoral ligaments at its posterior horn
- Loose attachment to the joint capsule, allowing limited movement (DOMAIN — Mink et al., "Radiography of the Knee")

**MR physics and imaging visibility (DOMAIN):**

1. **Tissue composition:** Fibrocartilage has a water content intermediate between hyaline cartilage and ligament. On standard MRI sequences:
   - T1-weighted (T1): Intermediate signal, slightly lower than muscle (DOMAIN)
   - T2-weighted (T2): Intermediate to high signal; the meniscus is normally low to intermediate signal (homogeneous, dark gray) due to low free water (DOMAIN)
   - Fluid-sensitive (FS) T2 or STIR: Suppresses fat, enhances fluid. Normal meniscus remains dark; joint fluid is bright; a tear with fluid intrusion becomes bright (DOMAIN)

2. **The tear mechanism:** When the meniscus is torn, the tear margins separate slightly. Joint fluid (synovial fluid, and in acute tears hemorrhage) fills the tear space. This creates a region of higher T2 signal within or at the surface of the normally dark meniscus (DOMAIN)

3. **Visibility by sequence:**
   - **Sagittal T2 / Sagittal FS T2:** Best planes to see meniscal tears because slices run through the meniscus from anterior to posterior, and both the tear location and morphology are visible (DOMAIN)
   - **Sagittal PD (proton density):** Also good, shows intermediate signal changes (DOMAIN)
   - **Coronal T2 / Coronal FS T2:** Shows medial vs. lateral meniscus separation; coronal plane best for seeing peripheral tears and capsular strain (DOMAIN)
   - **Axial T2 / Axial FS T2:** Less sensitive for meniscal tears; better for seeing meniscal extrusion or subluxation (DOMAIN)

**Mechanics of injury (DOMAIN):**

Meniscal tears typically occur by one of three mechanisms:
1. **Vertical or radial tears:** occur from sudden rotation or cutting injuries; the tear runs perpendicular or nearly perpendicular to the long axis of the meniscus (DOMAIN)
2. **Horizontal or cleavage tears:** occur from degenerative changes, often in middle-aged or older patients; the tear runs parallel to the meniscal surface (DOMAIN)
3. **Complex or bucket-handle tears:** a tear with multiple planes of cleavage; the handle can prolapse into the joint space, mechanically locking the knee (DOMAIN)

All produce a visible bright signal (T2 hyperintensity) at the tear site when imaged on FS T2 sequences.

**Degeneration and mimics (DOMAIN):**

Over time, menisci degenerate. Degeneration produces:
- Intra-meniscal signal change (bright areas within the dark meniscus)
- Fragmentation at the edges
- Loss of the sharp meniscal margin

A subtle degeneration may show as mild T2 signal change that does NOT reach the joint surface or tear margin. This grades on a scale from normal to torn.

---

### 1.3 Its Thermometers (Lenses)

Each lens is a simple, objective measurement at a registered site, calibrated against the population of normal knees at that site in the same sequence.

#### Lens M1: Medial Meniscal T2 Signal Intensity at the Posterior Horn (Sagittal FS T2)

**Measurement fact:** The pixel intensity (or voxel intensity in 3D) in the T2 FS image at the posterior horn of the medial meniscus, measured against a fixed reference in normal knees (PROPOSAL)

**Site:** Posterior horn of the medial meniscus, in the sagittal plane, at the largest diameter slice through the meniscus (DOMAIN — standard radiological landmark; the posterior horn is the thickest part)

**Series and sequence:** Sagittal, Fluid-Sensitive T2-weighted (FS T2) or STIR (FACT — standard in RSNA knee protocols; 00_facts.md lists Sagittal FS=1/1 as 4,667 series)

**Calibration:** The population reference is the distribution of T2 signal intensity at the posterior horn in normal (healthy) knees at the same site, in sagittal FS T2 sequences. A normal meniscus shows low-to-intermediate signal (dark gray in most displays). A tear shows high T2 signal (bright) (DOMAIN)

**Warrant:** Wide lens (SnNout mechanism). High sensitivity: if the meniscus is torn at this site, the signal will nearly always be elevated. Low specificity: elevation can occur from degeneration, magic angle artifact, or partial-volume effect (DOMAIN). Therefore: a HIGH reading raises confidence in a tear; a LOW reading argues against a tear at this site (DOMAIN)

---

#### Lens M2: Meniscal Signal Morphology — Tear vs. Degeneration (Sagittal FS T2)

**Measurement fact:** The geometry and extent of the T2 signal abnormality: is it linear (tear-like) or diffuse (degeneration-like)? Does it extend to the meniscal surface, or is it intra-meniscal only? (PROPOSAL)

**Site:** The entire medial meniscus, from anterior horn through body to posterior horn, imaged on sagittal slices (DOMAIN)

**Series and sequence:** Sagittal FS T2 (FACT)

**Calibration:** In normal knees, the meniscus is homogeneously dark. In torn knees, the bright signal follows a linear path (the tear direction) from one surface to another, or forms a visible disruption at the meniscal margin. In degenerative knees, the signal is more diffuse, fragmented at the edge, or poorly demarcated (DOMAIN)

**Warrant:** Narrow lens (SpPin, "first among equals"). Where this lens speaks clearly (a linear tear extending to the surface), it settles the question of whether a tear exists. Degeneration is not a "tear abnormality" in the sense the competition likely scores — PROPOSAL for founder ruling: does the label "Medial Meniscus" include degeneration alone, or only tears? Or both with equal weight? (UNKNOWN — to be set by founder)

**Note on independence:** This lens and M1 are not independent — both measure T2 signal in the same sequence. They are two aspects of the same measurement system. No evidence is double-counted; rather, they address different faces of the same phenomenon (DOMAIN)

---

#### Lens M3: Meniscal Extrusion (Coronal FS T2)

**Measurement fact:** The medial meniscus's position relative to the tibial margin (the edge of the tibial plateau). Is the meniscus extruded (displaced outward from its normal location beneath the femoral and tibial condyles)? Measured as distance from the meniscal margin to the tibial cortex (DOMAIN)

**Site:** The medial meniscus in the coronal plane, at its widest extent (typically the mid-body) (DOMAIN)

**Series and sequence:** Coronal FS T2 (FACT — standard; 00_facts.md lists Coronal FS=1/1 as 4,624 series)

**Calibration:** In normal knees, the meniscus is fully covered by the femoral and tibial articular surfaces; its margin stays inward (does not protrude beyond the tibial edge). Extrusion is measured as the millimeter distance the meniscus extends beyond this margin. A threshold of ~2–3 mm is typical; beyond this, extrusion is significant (DOMAIN)

**Warrant:** Directional for a tear. Extrusion is suggestive of meniscal pathology but not definitive: it can occur with a tear (the tear margin allows the meniscus to slip outward) or with degeneration (the meniscus loses structural integrity). It also can occur with age and OA alone. (DOMAIN) So: extrusion RAISES confidence in a meniscal abnormality but does NOT assign it alone.

**Note on mechanical coupling:** Extrusion mechanically reflects the loss of meniscal structural integrity, which is caused by a tear. So extrusion is a secondary sign of a tear mechanism (DOMAIN)

---

#### Lens M4: Meniscal Root Integrity (Sagittal FS T2 and T1)

**Measurement fact:** The integrity of the meniscal roots (the attachment points where the meniscus inserts into the tibial plateau at its anterior and posterior ends). Are the roots intact (low signal, sharp insertion) or disrupted (high signal, blurred attachment)? (DOMAIN)

**Site:** The anterior and posterior meniscal roots, where the meniscus inserts into the tibial plateau (DOMAIN)

**Series and sequence:** Sagittal FS T2 and sagittal T1 (or sagittal PD) (FACT)

**Calibration:** In normal knees, the meniscal roots show sharp, low-signal insertions into the tibia, anchored by the root ligaments. When torn or avulsed, the root shows signal change or bony avulsion (DOMAIN)

**Warrant:** Narrow lens (SpPin). A clearly torn or avulsed root is definitive evidence of meniscal tear. However, this lens is slow to acquire because only specific slices (at the very anterior and very posterior of the meniscus) carry the information. Many studies may not resolve these slices with clarity, leading to ABSTAIN (DOMAIN / PROPOSAL)

---

#### Lens M5: Pattern of T2 Signal on Coronal and Axial Views (Coronal and Axial FS T2)

**Measurement fact:** In coronal and axial views, does the meniscus show the characteristic C-shape (normal) or displacement, fragmentation, or bucket-handle appearance? (DOMAIN)

**Site:** The entire medial meniscus, viewed in coronal and axial planes (DOMAIN)

**Series and sequence:** Coronal FS T2 and Axial FS T2 (FACT)

**Calibration:** In normal knees, the meniscus appears as a uniform, dark C-shaped or O-shaped structure. In bucket-handle tears, a portion of the meniscus is displaced toward the center of the joint, sometimes visible as a double-peaked contour or an infolded structure (DOMAIN)

**Warrant:** Directional for a tear. Bucket-handle configuration is pathognomonic (disease-specific, strongly suggestive) of a tear. However, some tear patterns are not bucket-handle, so absence of this finding does not exclude a tear. (DOMAIN)

---

#### Lens M6: Associated Findings — Effusion and Synovitis (All Planes, FS T2)

**Measurement fact:** Is there an effusion (joint fluid) or synovitis (inflamed synovial membrane, shown as T2 signal change at the capsule)? (DOMAIN)

**Site:** The entire knee joint, focally at the region of the meniscal tear (DOMAIN)

**Series and sequence:** All planes, FS T2 (best for seeing fluid)

**Calibration:** Small amounts of joint fluid are normal (a few mL). Effusion is an accumulation beyond normal. Synovitis is inflammation at the synovial lining, shown as abnormal T2 signal or enhancement (DOMAIN)

**Warrant:** Directional for a tear. A meniscal tear produces an acute inflammatory response, which may manifest as effusion or synovitis. However, effusion and synovitis can occur independently (from OA, RA, other inflammation). So this is evidence FOR a tear, but NOT definitive (it does not assign alone) and could be EXPLAINED AWAY by other causes (DOMAIN)

**Note on effects on other labels:** Effusion and synovitis are themselves labels in this competition. A meniscal tear that produces an effusion will RAISE the confidence score for the Effusion label. Conversely, a high Effusion score might LOWER a meniscal score if the effusion is explained entirely by OA. (PROPOSAL — founder to rule on independence)

---

### 1.4 Paths: Classification of Diagnostic Rules

#### Definitional Paths (Strict Assignment)

**PROPOSAL:** The following ARE definitive conjunctions IF the warrant holds:

**Path D1: Linear Tear to Surface + Root Integrity Check**

*Conjunction:* 
- Lens M2 (morphology): A linear, high-T2 signal abnormality extending from the meniscal surface into the substance OR from the surface through to the opposite surface
- AND Lens M4 (roots): The meniscal roots are intact (no tear at the insertion points)
- AND Lens M1 (posterior horn signal): Elevated T2 at the site of the apparent tear

*Warrant:* The structure of the anatomy and MR physics: a tear is a discontinuity in the fibrocartilage. The discontinuity fills with fluid (joint fluid or hemorrhage), creating a bright T2 signal in the plane of the tear. If this pattern is clear and linear (not diffuse), and the roots are intact (so the tear is within the body, not at the attachment), then by the laws of MR physics and meniscal anatomy, a tear is the only mechanism that explains the finding. (DOMAIN)

*Law that makes it strict:* MR physics: a tear must fill with fluid to become visible. The fibrocartilage cannot hold fluid internally unless it is torn. A continuous meniscus does not show this pattern. Conversely, a tear MUST show high T2 signal where fluid enters, by the physics of T2 relaxation. (DOMAIN)

*Classification:* DEFINITIONAL (pending founder ruling on whether this warrant holds for this label)

---

**Path D2: Bucket-Handle Configuration + Coronal/Axial Morphology**

*Conjunction:*
- Lens M5 (pattern): Bucket-handle configuration visible on coronal or axial views — a displaced meniscal fragment lying horizontally across the joint space
- AND Lens M1 or M2: Elevated T2 signal at the parent meniscus
- AND Lens M3: Possible extrusion of the main meniscal body

*Warrant:* Bucket-handle tears are a specific tear type: a peripheral vertical tear with the inner meniscal fragment displaced into the joint space. The configuration is mechanical and unmistakable. By the anatomy and mechanics, a bucket-handle configuration means a tear. (DOMAIN)

*Law:* Anatomy: the meniscus cannot naturally fold or double over into the joint space unless a tear creates the displaced fragment. (DOMAIN)

*Classification:* DEFINITIONAL (if the bucket-handle configuration is clear)

---

**Note on Degeneration:** 
A high T2 signal within the meniscus that is diffuse, fragmented, or not reaching the surface (Lens M2: intra-meniscal signal only) is degeneration, not a tear. Degeneration is NOT included in the DEFINITIONAL paths if the label "Medial Meniscus" means "tear" (PROPOSAL — founder to rule). If the label includes degeneration, a separate DEFINITIONAL path is needed.

---

#### Strict Exclusion

**PROPOSAL:** The following scenarios completely exclude a meniscal tear:

**Exclusion E1: Normal Meniscal Morphology + Population-Calibrated Normal Signal**

*Statement:* 
- The medial meniscus shows normal C-shape on all views (Lens M5)
- The T2 signal is low, homogeneous, and within the normal range for the population at this site and sequence (Lens M1, calibrated against healthy knees)
- No linear signal abnormality (Lens M2: morphology normal)
- Meniscal roots are intact and sharp (Lens M4)
- No extrusion (Lens M3)

*Warrant for strict exclusion:* By MR physics, if the meniscus is intact (unbroken), joint fluid cannot enter, and the signal must be low. If all these lenses are negative, the conjunction warrants exclusion. (DOMAIN)

*Law:* MR physics: a tear MUST allow fluid in. No fluid intrusion = no tear. The measurements are lossless for this fact. (DOMAIN)

*Classification:* STRICT EXCLUSION (pending founder approval of the threshold for "normal")

---

#### Directional Evidence

**DIRECTIONAL FOR (raises confidence):**

1. **M1 High + M2 Linear:** Elevated T2 signal in a linear pattern, even if not pathognomonic, raises confidence. Reason: the linear pattern is more typical of a tear than diffuse degeneration. Strength: moderate to strong, depending on how clear the linearity is. (DOMAIN)

2. **M3 Extrusion + M1 Signal Change:** Extrusion (meniscus displaced outward) with elevated signal at the site. Reason: extrusion reflects loss of structural integrity, which a tear causes. Strength: moderate (extrusion alone can occur with age/OA, but with T2 signal change, the pair is more suggestive of pathology). (DOMAIN)

3. **M6 Associated Effusion + M1 Signal at Tear Site:** An effusion or synovitis localized to the region of a meniscal signal abnormality. Reason: a meniscal tear produces an acute inflammatory response. Strength: moderate (the inflammation could be from other causes, but co-localization is suggestive). (DOMAIN)

4. **M5 Bucket-Handle or Infolding Pattern:** A displaced meniscal fragment on coronal or axial imaging. Reason: bucket-handle is pathognomonic for a tear. Strength: strong. (DOMAIN)

---

**DIRECTIONAL AGAINST (lowers confidence):**

1. **M2 Diffuse, Not Linear + M1 Mild Signal Change:** A diffuse T2 signal change without a clear linear or tear-like morphology. Reason: diffuse signal is more typical of degeneration than tear. Strength: moderate (degeneration and tear can co-occur). (DOMAIN)

2. **M4 Root Integrity Intact + No Surface-Reaching Signal:** If the roots are clearly intact and the T2 signal does not reach the meniscal surface, the finding is more consistent with degeneration (intra-meniscal signal) than tear. Reason: tears typically extend to at least one surface. Strength: moderate to strong (intra-meniscal signal alone is not a tear). (DOMAIN)

3. **No Associated Effusion or Synovitis in Acute Imaging:** A meniscal tear should produce some acute inflammatory response if recent. Absence of effusion or synovitis when T2 signal is present could suggest degeneration (chronic, no acute inflammation) rather than acute tear. Reason: acute tears provoke effusion/synovitis. Chronic tears or degeneration may not. Strength: weak to moderate (the tear could be chronic, with inflammation resolved). (DOMAIN)

---

#### Abstain

The system abstains (no reading; next acquisition needed) in these scenarios:

**Abstain A1: Series not available**
- Sagittal FS T2 not present in the series set
- All coronal or axial views missing

**Reason:** The lenses cannot read without the series. The meniscus cannot be imaged in sagittal plane alone; multiple views are needed for confident diagnosis. (DOMAIN / PROPOSAL — founder to define the minimum series set required)

---

**Abstain A2: Image artifact or degraded quality**
- Fat suppression artifact (incomplete fat suppression makes FS T2 uninterpretable; fat appears bright, mimicking fluid)
- Motion artifact obscuring the meniscal outline
- Magic angle artifact (artifact from the 54.7° angle between the meniscus fiber orientation and the main magnetic field, creating high T2 signal in a normal meniscus at certain orientations) (DOMAIN)

**Reason:** The lens cannot distinguish true signal from artifact. Reading is unreliable. (DOMAIN)

---

**Abstain A3: Meniscal slices not resolved (partial volume)**
- The meniscus is very small or the slice thickness is too thick for the posterior horn or anterior horn to be clearly seen in multiple slices.
- Only 1 slice shows meniscal signal; the adjacent slices don't (likely partial volume).

**Reason:** A single slice could be noise or artifact. Multiple slices confirming the finding are needed for warrant. (PROPOSAL)

---

### 1.5 Mimics and Confounders

**Mimic 1: Magic Angle Artifact**

What it is: A bright T2 signal in a normal meniscus, produced by the fiber orientation of the meniscus at 54.7° to the main magnetic field. This is a pure artifact of MR physics (DOMAIN)

How to isolate from tear:
- The signal is usually at the periphery or in one specific location (the magic angle region)
- It is homogeneous, not linear
- It is NOT associated with meniscal morphology change or extrusion
- Using a T1 sequence or a sequence with different flip angle can resolve it (the magic angle effect is sequence-dependent) (DOMAIN)

Lens that isolates: M2 (morphology) and M4 (roots) — if these are normal, magic angle is the diagnosis. M3 (extrusion) is absent.

---

**Mimic 2: Meniscal Degeneration Without Tear**

What it is: Intra-meniscal signal change from collagen breakdown and degeneration, without a tear (DOMAIN)

How to isolate from tear:
- Lens M2: The signal is diffuse and fragmented, not linear. It does NOT extend to the meniscal surface (intra-meniscal only, NOT surface-reaching) (DOMAIN)
- Lens M3: No extrusion; the meniscal margin is intact in place
- Lens M4: Roots are intact
- Lens M5: No bucket-handle or displacement
- Lens M6: No acute effusion or synovitis (degeneration is chronic)

PROPOSAL: If the label "Medial Meniscus" means "tear," degeneration scores low confidence. If it includes degeneration, a separate DIRECTIONAL FOR path is needed for intra-meniscal signal.

---

**Mimic 3: Partial-Volume Artifact or Pseudolesion**

What it is: At the margin of the meniscus or where the meniscus adjoins other structures (ligament, capsule, subarticular bone), a small region of intermediate signal can arise from averaging (partial volume) of two tissues with different signals (DOMAIN)

How to isolate:
- Lens M1 and M2: The signal is not clearly within the meniscal body; it is at the edge or margin, and it is not reproducible across multiple slices in the same sequence
- Lens M5: No morphology change

---

**Mimic 4: Meniscal Cyst**

What it is: A fluid collection at the meniscal margin, often associated with a horizontal cleavage tear or degenerative changes (DOMAIN)

How to isolate:
- Lens M1 and M2: The signal is bright (high T2) and well-circumscribed, NOT linear across the meniscal body
- Lens M3: The cyst may cause extrusion or be visible as a localized outpouching
- Lens M5: The meniscal morphology may show a bulge at the margin, but the main meniscal body is usually intact

---

### 1.6 Effects on Other Labels

**On Effusion:**
- A meniscal tear produces an effusion as an acute inflammatory response. If a meniscal tear is present, this RAISES the expected confidence in Effusion.
- However, effusion can occur from OA, synovitis, or other causes independent of meniscal pathology.
- PROPOSAL: When scoring meniscal tears, the Effusion label should not be allowed to "explain away" the meniscal finding. But the two are mechanically coupled, and the joint harness (the committee) must decide whether effusion is evidence for a tear or a separate finding. (PROPOSAL for founder)

---

**On Synovitis:**
- A meniscal tear can produce synovitis (inflammation of the synovial lining in response to the tear).
- Synovitis also occurs independently (from RA, OA, other systemic inflammation).
- A meniscal tear + synovitis is a coherent finding; synovitis without meniscal pathology is also coherent.
- PROPOSAL: Synovitis is directional evidence for a tear, but not definitive.

---

**On Ligament Labels (ACL, MCL):**
- A meniscal tear does NOT mechanically cause ligamentous injury.
- However, a traumatic injury that tears the meniscus might also tear a ligament.
- Co-occurrence in the same study raises suspicion of a single traumatic event, but is NOT evidence for either alone.
- PROPOSAL: Meniscal and ligament findings are independent observations; one does not drive the other mechanically, but both might arise from the same injury mechanism.

---

**On Osteoarthritis (Medial OA, Lateral OA, PF OA):**
- A meniscal tear can accelerate OA over time (chronic degenerative pathway).
- Early OA can produce meniscal degeneration and fragmentation, which may resemble a tear.
- A patient with OA may have both meniscal degeneration and osteoarthritic changes.
- PROPOSAL: Meniscal tear and OA are separable by the lenses: tear = linear signal change reaching the surface; OA = joint-space narrowing, osteophyte formation. But in a single study, they may co-occur, and the committee must handle the co-variance.

---

**On Contusion and Fracture:**
- A meniscal tear from a traumatic injury may be accompanied by bone contusion (marrow edema) or fracture in the adjacent tibial plateau.
- The meniscal tear and contusion/fracture are distinct findings from the same injury.
- PROPOSAL: They are independent lenses on the same trauma, not dependent on each other.

---

### 1.7 What the Host Labels Can Confirm and Near Misses They Expose

**What the 58 labeled studies can confirm (PROPOSAL):**

Among the 58 labeled studies in the training set, 26 are labeled positive for "Medial Meniscus" (00_facts.md, §4). For each of these 26 studies, the radiologist read the medial meniscus and marked it as abnormal (1, present).

- These 26 cases are confirmations that the lenses M1–M6 should detect a meniscal abnormality when present.
- The lenses should be calibrated such that the 26 positive cases show detectable signal changes, morphology changes, extrusion, or other findings aligned with the paths.
- The 32 negative cases (medial meniscus = 0, absent) should show normal meniscal morphology and signal, confirming the STRICT EXCLUSION and normal-baseline calibration.

---

**Near misses the labels expose (PROPOSAL):**

A near miss is a study where the lenses predict a certain finding, but the host label differs, revealing a misunderstanding of the underlying mechanism or a boundary case.

Example near misses to watch for:

1. **False positive: High T2 signal, linear morphology, but host label = 0 (normal).**
   - This suggests the linear signal change is NOT a tear (likely degeneration or magic angle artifact).
   - LEARNING: The Lens M2 (morphology) needs refinement; a fully linear signal without clear tear mechanics (no extrusion, no effusion) might be degeneration.
   - The warranty of Lens M2 may need narrowing: it settles the question only when certain conditions are met (e.g., extrusion present, effusion present).

2. **False negative: No signal change, normal morphology, but host label = 1 (abnormal).**
   - The radiologist detected a meniscal abnormality (probably a tear or complex finding) that the T2 signal lenses did not catch.
   - LEARNING: A non-displaced tear (vertical tear that doesn't reach the surface, or a root tear not imaged at good resolution) might be missed by surface-T2-signal lenses.
   - This exposes a gap: Root lenses (M4) and detailed morphology on multiple planes might be needed.

3. **Borderline case: Equivocal signal, morphology unclear, but host label decisive (0 or 1).**
   - This reveals a decision rule the radiologist applied (e.g., "if signal is mild and no extrusion, it's degeneration, not a tear" vs. "any signal change is abnormal").
   - LEARNING: The founder must rule on what "Medial Meniscus abnormality" includes: tear only, or tear + degeneration + cyst?

---

### 1.8 Open Questions for Founder Ruling

1. **Scope of "Medial Meniscus" abnormality:**
   - Does the label assign confidence only for tears, or also for degeneration, cysts, partial tears, and other meniscal pathology?
   - If degeneration counts, what grade of degeneration (intra-meniscal signal? surface-reaching? extrusion required?)?
   - PROPOSAL: Refine the label definition from "abnormality" to a specific set of pathologies.

2. **Threshold for diagnosis:**
   - At what size, signal intensity, or morphology does a meniscal finding become "present" in the host's radiologist's judgment?
   - Is a 2-mm extrusion alone sufficient, or does it require T2 signal change?
   - Does a root tear without body signal count?
   - PROPOSAL: The founder (or the radiology team) supplies example cases (ideally the 26 positive studies) so the lenses can be calibrated to the actual threshold.

3. **Independence of M1, M2, M3, M4, M5, M6:**
   - Are these lenses truly independent (measuring different aspects of the meniscus), or are some redundant?
   - How should the committee weight them if they disagree (one high, one low)?
   - PROPOSAL: Define the downward-looking contract: "All four signal-based lenses agree" vs. "Any one is high" vs. "A majority are high".

4. **Magic angle artifact:**
   - The RSNA dataset includes FS sequences (fat-suppressed), which somewhat mitigate magic angle. But some protocols might still show it.
   - Should the Lens M2 (morphology) be trained to reject magic angle automatically, or is a separate "check for magic angle" step needed?
   - PROPOSAL: Example images showing magic angle artifact would help calibrate M2.

5. **Degeneration vs. tear:**
   - Clinically, the distinction between meniscal degeneration (intra-meniscal signal, no tear) and tear (signal reaching the surface) is central.
   - The host labels seem to be radiologist reads, likely following standard definitions (tear = signal reaching surface; degeneration = intra-meniscal only).
   - PROPOSAL: Confirm that the host labels follow this standard, so Lens M2 can assign DEFINITIONAL warrant when signal reaches the surface.

6. **Mechanical coupling of meniscal and effusion findings:**
   - A meniscal tear typically causes some effusion or reactive fluid.
   - Should the Effusion label score high whenever a meniscal tear is present, or are they independent dimensions?
   - PROPOSAL: The founder (or the radiologist) rules on whether a meniscal tear and effusion are mechanically linked (should be scored together) or independent (each has its own warrant).

---

---

## Part 2: Lateral Meniscus

### 2.1 Definition

**Host's label:** "Lateral Meniscus" (FACT — from `sample_submission.csv` column name)

**Official definition from host:** None provided (FACT — 00_facts.md §1)

**Medical domain interpretation:** A tear or other abnormality of the lateral meniscus (DOMAIN)

**What the label includes:** 
- Radiologist's detection of an abnormality in the lateral meniscal structure on MRI (DOMAIN)
- The abnormality that warrants the diagnosis "present" / confidence score > 0 (DOMAIN)

**What the label excludes (PROPOSAL for founder ruling):**
- By the same reasoning as the medial meniscus, the label assigns confidence when the lateral meniscus differs from the population of normal knees at the same site in a way anatomy and MR physics account for by the rules a radiologist uses.
- A normal lateral meniscus, even if hypersignal or mild degenerative change within the range of normal variation, would score low confidence.

---

### 2.2 Structural Reason It Can Be Diagnosed

**Anatomy (DOMAIN):**

The lateral meniscus is a more O-shaped (nearly circular) fibrocartilage structure within the knee joint, positioned between the lateral femoral condyle (above) and the lateral tibial plateau (below). It is held in place by:
- Capsular attachments (coronary ligaments) at its periphery
- Meniscofemoral ligaments (anterior and posterior) connecting it to the femur
- Loose attachment to the joint capsule, similar to the medial meniscus but with different geometry (DOMAIN — Mink et al.)

**Key anatomical difference from medial meniscus:**
- The lateral meniscus is more mobile (less firmly attached) than the medial meniscus
- This mobility makes the lateral meniscus more prone to DISPLACEMENT and BUCKET-HANDLE TEARS, whereas the medial meniscus is more prone to PERIPHERAL and DEGENERATIVE tears (DOMAIN)
- The lateral meniscus is smaller in volume and less weight-bearing than the medial meniscus (DOMAIN)

**MR physics and imaging visibility (DOMAIN):**

The MR signal properties are identical to the medial meniscus:
- T1: Intermediate signal
- T2: Low to intermediate signal (normally dark due to low free water)
- FS T2 / STIR: High signal in a tear (fluid-filled), low signal in a normal meniscus

**Visibility by sequence:**
- **Sagittal T2 / Sagittal FS T2:** Best for seeing the lateral meniscus from anterior to posterior horn
- **Coronal T2 / Coronal FS T2:** Shows the lateral meniscus in profile; good for seeing extrusion and bucket-handle configuration
- **Axial T2 / Axial FS T2:** Less sensitive; useful for seeing meniscal extrusion or subluxation

(All per DOMAIN — standard knee MRI protocols)

**Mechanics of injury (DOMAIN):**

Lateral meniscal tears typically occur by:
1. **Vertical/radial tears:** Acute, from rotational injury; tear runs perpendicular to the long axis
2. **Horizontal/cleavage tears:** Degenerative; tear runs parallel to the meniscal surface (rarer in lateral than medial)
3. **Bucket-handle tears:** COMMON in the lateral meniscus; the meniscus is more mobile, so a peripheral tear can flip the inner fragment into the joint space
4. **Popliteal cyst:** A fluid collection at the posterior capsule, often associated with a lateral meniscal tear (especially horizontal tears)

All produce bright T2 signal on FS T2 when imaged at the tear site.

---

### 2.3 Its Thermometers (Lenses)

The lenses for the lateral meniscus are structurally identical to those of the medial meniscus, with a location difference (lateral vs. medial). For brevity, I describe the differences and cross-reference the medial lenses.

#### Lens L1: Lateral Meniscal T2 Signal Intensity at the Posterior Horn (Sagittal FS T2)

**Measurement fact:** The pixel intensity in the T2 FS image at the posterior horn of the lateral meniscus, measured against the population baseline (PROPOSAL)

**Site:** Posterior horn of the lateral meniscus, in the sagittal plane, at the largest diameter slice

**Difference from M1:** Location is lateral instead of medial; otherwise identical. The lateral meniscus posterior horn is slightly anterior (more toward the front of the knee) than the medial meniscus posterior horn, due to the O-shaped geometry. (DOMAIN)

**Calibration:** The population reference is the distribution of T2 signal intensity at the lateral meniscal posterior horn in normal (healthy) knees in sagittal FS T2 sequences.

**Warrant:** Wide lens (SnNout). Same reasoning as M1: high signal raises confidence in a tear; low signal argues against a tear at this site.

---

#### Lens L2: Meniscal Signal Morphology — Tear vs. Degeneration (Sagittal FS T2)

**Measurement fact:** The geometry and extent of the T2 signal abnormality in the lateral meniscus: linear (tear) or diffuse (degeneration)? Does it extend to the meniscal surface?

**Site:** The entire lateral meniscus, from anterior horn through body to posterior horn

**Series and sequence:** Sagittal FS T2

**Warrant:** Narrow lens (SpPin). Same reasoning as M2: a clear linear tear extending to the surface settles the question.

**Difference from M2:** None structural; location only (lateral vs. medial).

---

#### Lens L3: Meniscal Extrusion (Coronal FS T2)

**Measurement fact:** The lateral meniscus's position relative to the tibial margin. Is it extruded (displaced outward)?

**Site:** The lateral meniscus in the coronal plane, at its widest extent (typically the mid-body)

**Series and sequence:** Coronal FS T2

**Warrant:** Directional for a tear. Same reasoning as M3, except: the lateral meniscus is normally more mobile, so subtle extrusion is more common in normal knees. A threshold for "abnormal" extrusion may differ slightly from the medial meniscus. (PROPOSAL — founder to set the threshold)

**Difference from M3:** The lateral meniscus baseline extrusion may be slightly higher (more mobile), so the calibration reference might differ. Otherwise identical.

---

#### Lens L4: Meniscal Root Integrity — Anterior and Posterior Roots (Sagittal FS T2 and T1)

**Measurement fact:** The integrity of the lateral meniscal roots (anterior horn and posterior horn attachments to the tibia). Are they intact (low signal, sharp insertion) or disrupted (high signal, avulsion)?

**Site:** The anterior and posterior lateral meniscal roots, at the tibial insertions

**Series and sequence:** Sagittal FS T2 and sagittal T1 (or sagittal PD)

**Warrant:** Narrow lens (SpPin). Same as M4: a clearly torn or avulsed root is definitive evidence of meniscal tear. But the lens may be slow to acquire (specific slices only), leading to ABSTAIN on many studies.

**Difference from M4:** The lateral posterior root has a special relevance: it is not directly attached to the tibia but inserts into the popliteal hiatus (a notch between the meniscus and the joint capsule). A tear at the posterior lateral root can allow meniscal extrusion and is sometimes associated with a popliteal cyst. (DOMAIN)

---

#### Lens L5: Pattern of T2 Signal on Coronal and Axial Views — Bucket-Handle Configuration (Coronal and Axial FS T2)

**Measurement fact:** In coronal and axial views, does the lateral meniscus show the characteristic O-shape (normal) or bucket-handle/displaced appearance?

**Site:** The entire lateral meniscus, viewed in coronal and axial planes

**Series and sequence:** Coronal FS T2 and Axial FS T2

**Warrant:** Narrow lens (SpPin). Bucket-handle configuration is pathognomonic for a tear. Same as M5, except: the LATERAL meniscus is MORE prone to bucket-handle tears (higher prior probability), so this finding is even more definitive for the lateral meniscus than the medial. (DOMAIN)

**Difference from M5:** The lateral meniscus's greater mobility makes bucket-handle tears more common. When present, this lens is very strong evidence of a tear.

---

#### Lens L6: Associated Popliteal Cyst (Sagittal FS T2 and Coronal FS T2)

**Measurement fact:** Is there a popliteal cyst (Baker's cyst) at the posterior capsule? (DOMAIN) Popliteal cysts are commonly associated with lateral meniscal tears, especially horizontal cleavage tears.

**Site:** The posterior-medial aspect of the popliteal space, visible in sagittal and coronal views

**Series and sequence:** Sagittal FS T2 (best for seeing the cyst)

**Calibration:** A normal knee has no cyst or a tiny (< 5 mm) cyst. A significant cyst (> 5 mm) is abnormal and often indicates an underlying pathology (meniscal tear, OA, synovitis). (DOMAIN)

**Warrant:** Directional for a lateral meniscal tear. A popliteal cyst is NOT a direct measure of the lateral meniscus, but it is mechanically linked: a horizontal cleavage tear in the lateral meniscus can create a communication with the posterior capsule, allowing fluid to bulge out, forming a cyst. (DOMAIN)

**Difference from medial lenses (M1–M6):** This is a NEW lens, specific to the lateral meniscus, because popliteal cysts are much more common with lateral meniscal tears than medial. For the medial meniscus, no such mechanically-linked finding is typical. (DOMAIN)

---

#### Lens L7: Meniscal Capsular Separation (Coronal FS T2)

**Measurement fact:** Is there a separation between the meniscus and the joint capsule? A small gap (1–2 mm) is normal; a larger gap or fluid between them indicates a meniscal or capsular abnormality. (DOMAIN)

**Site:** The periphery of the lateral meniscus, in the coronal plane, along the capsular attachment

**Series and sequence:** Coronal FS T2

**Warrant:** Directional for a tear or capsular strain. A torn meniscus may pull away from the capsule, or a capsular injury may separate from the meniscus. (DOMAIN)

**Difference from medial meniscus lenses:** The lateral meniscus has a more mobile capsular attachment, so separation is more meaningful. This lens may be more specific to the lateral meniscus. (PROPOSAL)

---

### 2.4 Paths: Classification of Diagnostic Rules

#### Definitional Paths (Strict Assignment)

**Path D1: Linear Tear to Surface + Root Integrity Check (Lateral)**

*Conjunction:*
- Lens L2 (morphology): Linear, high-T2 signal extending from the meniscal surface into the substance or through to the opposite surface
- AND Lens L4 (roots): Meniscal roots are intact (no tear at the insertion points)
- AND Lens L1 (posterior horn signal): Elevated T2 at the site of the apparent tear

*Warrant:* Identical to the medial meniscus (M2 + M4 + M1). The MR physics is the same. A tear is a discontinuity that fills with fluid.

*Law:* MR physics: tear must contain fluid; fluid creates high T2 signal. A normal meniscus cannot hold fluid internally.

*Classification:* DEFINITIONAL

---

**Path D2: Bucket-Handle Configuration — Lateral**

*Conjunction:*
- Lens L5 (pattern): Bucket-handle configuration visible on coronal or axial views — displaced meniscal fragment in the joint space
- AND Lens L1 or L2: Elevated T2 signal at the parent meniscus

*Warrant:* Bucket-handle is pathognomonic for a tear. The lateral meniscus's greater mobility makes this finding highly specific. (DOMAIN)

*Law:* Anatomy: the meniscus cannot naturally fold into the joint space unless a tear creates the displaced fragment.

*Classification:* DEFINITIONAL

---

**Path D3: Horizontal Cleavage Tear + Popliteal Cyst (Lateral)**

*Conjunction:*
- Lens L2 (morphology): Horizontal (parallel-to-surface) T2 signal abnormality, possibly intra-meniscal
- AND Lens L6 (popliteal cyst): A significant popliteal cyst (> 5 mm) at the posterior capsule
- AND Lens L1: Elevated T2 signal at the tear site
- AND Lens L4 (roots): Posterior root is intact OR disrupted (depends on tear location)

*Warrant:* A horizontal cleavage tear can create a direct communication with the posterior capsule (if the tear extends to the posterior-medial edge of the meniscus). This allows synovial fluid to form a cyst. The combination of a cleavage tear signature + a popliteal cyst is highly specific for this tear type. (DOMAIN)

*Law:* Anatomy: a communication between the meniscal tear and the posterior capsule allows fluid to collect in the cyst. This is mechanical.

*Classification:* DEFINITIONAL (for lateral meniscus, given the mechanical linkage to the popliteal cyst)

---

#### Strict Exclusion

**Exclusion E1: Normal Meniscal Morphology + Population-Calibrated Normal Signal (Lateral)**

*Statement:*
- The lateral meniscus shows a normal O-shape on all views (Lens L5)
- The T2 signal is low, homogeneous, and within the normal range (Lens L1, calibrated against healthy knees)
- No linear signal abnormality (Lens L2: morphology normal)
- Meniscal roots are intact and sharp (Lens L4)
- No extrusion (Lens L3)
- No popliteal cyst (Lens L6)
- No capsular separation (Lens L7)

*Warrant:* Identical to medial meniscus (E1). If all lenses are negative, the meniscus is intact.

*Law:* MR physics: a tear must show fluid intrusion; if no signal change, no tear.

*Classification:* STRICT EXCLUSION

---

#### Directional Evidence

**DIRECTIONAL FOR:**

1. **L1 High + L2 Linear:** Elevated T2 signal in linear pattern. Strength: moderate to strong. (DOMAIN)

2. **L3 Extrusion + L1 Signal Change:** Extrusion with elevated signal. Strength: moderate to strong. (The lateral meniscus's mobility means extrusion alone is less definitive, but with signal change, the pair is strongly suggestive.) (DOMAIN)

3. **L5 Bucket-Handle or Infolding:** Displaced meniscal fragment. Strength: strong (pathognomonic for tear). (DOMAIN)

4. **L6 Significant Popliteal Cyst + L1 Signal Change:** Cyst with T2 signal abnormality at the meniscus. Strength: moderate to strong (the mechanical linkage is strong). (DOMAIN)

5. **L7 Capsular Separation + L1 or L2:** Meniscal-capsular separation with signal change. Strength: moderate (could indicate tear or capsular injury). (DOMAIN)

---

**DIRECTIONAL AGAINST:**

1. **L2 Diffuse, Not Linear + L1 Mild Signal Change:** Diffuse signal change without linear morphology. Strength: moderate (suggests degeneration rather than tear). (DOMAIN)

2. **L4 Roots Intact + No Surface-Reaching Signal:** Intact roots with intra-meniscal signal only. Strength: moderate to strong (intra-meniscal signal is degeneration, not tear). (DOMAIN)

3. **No Popliteal Cyst When Expecting One:** If a horizontal cleavage tear is suspected based on Lenses L1 and L2, but no popliteal cyst is present, this weakens the horizontal cleavage diagnosis. Strength: weak to moderate (the cyst is not always present, or the communication may not be patent). (DOMAIN)

---

#### Abstain

**Abstain A1: Series not available**
- Sagittal FS T2 not present
- All coronal or axial views missing

**Reason:** The lenses cannot read without the series.

---

**Abstain A2: Image artifact or degraded quality**
- Fat suppression artifact
- Motion artifact
- Magic angle artifact (at the lateral meniscus periphery, this can be visible)

**Reason:** The lens cannot distinguish true signal from artifact.

---

**Abstain A3: Meniscal slices not resolved (partial volume)**
- The lateral meniscus is less thick than the medial meniscus in many patients, making it more prone to partial-volume artifact.
- Only 1 or 2 slices show meniscal signal.

**Reason:** Multiple slices confirming the finding are needed for warrant.

---

### 2.5 Mimics and Confounders

**Mimic 1: Magic Angle Artifact (Lateral)**

The lateral meniscus, especially at the periphery where the fibers may be more aligned at 54.7° to the main field, can show bright T2 signal from magic angle artifact. (DOMAIN)

How to isolate:
- Lens L2 (morphology): The signal is peripheral, not linear across the meniscus.
- Lens L4 and L5: Morphology is normal.
- Sequence check: The signal resolves with a different flip angle or sequence.

---

**Mimic 2: Meniscal Degeneration Without Tear (Lateral)**

Intra-meniscal signal from collagen breakdown, without a tear.

How to isolate:
- Lens L2: Signal is diffuse and does NOT reach the surface.
- Lens L3: No extrusion.
- Lens L4: Roots intact.
- Lens L5: No bucket-handle or displacement.
- Lens L6: No popliteal cyst (unless degeneration has created an underlying tear).

---

**Mimic 3: Popliteal Cyst Without Lateral Meniscal Tear (Lateral)**

A Baker's cyst can be associated with OA, synovitis, or medial meniscal pathology, not necessarily a lateral meniscal tear.

How to isolate:
- Lens L1, L2: No T2 signal change in the lateral meniscus itself.
- Lens L6: The cyst is present, but the meniscus appears normal.
- Lens L4, L5: Normal morphology and roots.
- CHECK: If a cyst is present but the lateral meniscus is normal, look for MEDIAL meniscal pathology or OA (which are other label questions for the committee).

---

**Mimic 4: Meniscal-Capsular Separation Without Tear**

A small gap between the meniscus and capsule can occur from capsular laxity, age, or inflammation, without a meniscal tear.

How to isolate:
- Lens L7 (capsular separation): Present.
- Lens L1, L2, L5: Meniscal signal and morphology are normal.
- Lens L4: Roots are intact.
- DISTINCTION: Isolated capsular separation (without meniscal signal change) is NOT a meniscal tear.

---

### 2.6 Effects on Other Labels

**On Popliteal Cyst (Baker's Cyst):**

A lateral meniscal tear, especially a horizontal cleavage tear, is a common cause of a Baker's cyst. The cyst is mechanically linked to the tear.

- If a lateral meniscal tear is present, this RAISES the expected confidence in Baker's cyst.
- However, Baker's cyst can occur without a meniscal tear (from OA, synovitis, other causes).
- PROPOSAL: The two labels are mechanically coupled for the lateral meniscus. The committee must decide whether Baker's cyst is counted as evidence for a lateral meniscal tear, or whether they are independent findings.

---

**On Effusion and Synovitis:**

A lateral meniscal tear can produce an effusion or synovitis, same as the medial meniscus.

- The tear's acute inflammatory response raises the expected confidence in Effusion and Synovitis.
- However, these can occur independently from other causes (OA, RA, inflammation).
- PROPOSAL: Same as medial meniscus — mechanical coupling must be decided by the committee.

---

**On Ligament Labels (ACL, MCL):**

A traumatic injury that tears the lateral meniscus might also injure ligaments.

- No direct mechanical link between the two.
- Co-occurrence suggests a single traumatic event.
- PROPOSAL: Independent findings, but with possible co-variance from injury mechanism.

---

**On Osteoarthritis (Lateral OA, PF OA):**

A lateral meniscal tear can accelerate OA in the lateral compartment.

- A meniscal tear raises the expected confidence in Lateral OA over time (degenerative pathway).
- However, OA can occur without meniscal tear (primary OA from age, biomechanics).
- A patient with OA often has meniscal degeneration or tears.
- PROPOSAL: Meniscal tear and Lateral OA are separable by lenses (tear = signal change, OA = joint-space narrowing, osteophytes) but may co-occur and have mechanical coupling.

---

**On Contusion and Fracture:**

A traumatic lateral meniscal tear may be accompanied by bone contusion or fracture in the adjacent lateral tibial plateau.

- Distinct findings from the same injury.
- PROPOSAL: Independent lenses on the same trauma.

---

### 2.7 What the Host Labels Can Confirm and Near Misses They Expose

**What the 58 labeled studies can confirm (PROPOSAL):**

Among the 58 labeled studies, 23 are labeled positive for "Lateral Meniscus" (00_facts.md, §4). For each of these 23 studies, the radiologist read the lateral meniscus and marked it as abnormal (1, present).

- These 23 cases are confirmations that the lenses L1–L7 should detect a lateral meniscal abnormality when present.
- The lenses should be calibrated such that the 23 positive cases show detectable signal changes, morphology changes, bucket-handle configuration, or other findings aligned with the paths.
- The 35 negative cases (lateral meniscus = 0, absent) should show normal meniscal morphology and signal, confirming the STRICT EXCLUSION and normal-baseline calibration.

---

**Near misses the labels expose (PROPOSAL):**

1. **False positive: High T2 signal, linear morphology, but host label = 0 (normal).**
   - This suggests the linear signal change is not a tear (likely degeneration or magic angle).
   - LEARNING: Lens L2 (morphology) or L5 (pattern) may need refinement to reject artifact or intra-meniscal signal.
   - LEARNING: The context of the lateral meniscus (more mobile, more prone to bucket-handle) might require stronger warrant for assignment.

2. **False negative: No signal change, normal morphology, but host label = 1 (abnormal).**
   - The radiologist detected a lateral meniscal abnormality that the signal lenses did not catch.
   - LEARNING: A non-displaced tear (vertical tear that doesn't reach the surface, or a root tear not imaged at good resolution) might be missed.
   - LEARNING: A popliteal cyst without obvious meniscal signal could indicate a tear that the meniscal lenses missed (Lens L6 would have caught this if it were checked).

3. **Bucket-handle tear not detected.**
   - If a bucket-handle configuration is present (Lens L5 would catch it) but the system misses it.
   - LEARNING: The coronal and axial views must be carefully read for this specific morphology; it can be subtle if the displaced fragment is small.

4. **Popliteal cyst present, but no lateral meniscal tear detected.**
   - A significant popliteal cyst (Lens L6) without obvious meniscal signal change (Lenses L1, L2).
   - LEARNING: The cyst might indicate a tear that doesn't show high T2 signal (e.g., a healed tear, a tear with poor communication to the cyst, or a tear in a region not imaged clearly).
   - PROPOSAL: If the cyst is the only finding, the committee must decide whether to raise the lateral meniscus confidence based on the mechanical linkage alone, or wait for meniscal signal confirmation.

---

### 2.8 Open Questions for Founder Ruling

1. **Scope of "Lateral Meniscus" abnormality:**
   - Does the label assign confidence only for tears, or also for degeneration, cysts, partial tears, and other meniscal pathology?
   - If degeneration counts, what grade?
   - PROPOSAL: Same question as for medial meniscus; refinement of the label definition is needed.

2. **Popliteal cyst as evidence:**
   - A popliteal cyst is mechanically linked to a lateral meniscal tear (especially horizontal cleavage).
   - Should the presence of a significant popliteal cyst (Lens L6) raise the lateral meniscus confidence even without obvious meniscal signal change?
   - PROPOSAL: The founder rules on whether the mechanical linkage is tight enough to include a cyst as DIRECTIONAL FOR or even DEFINITIONAL evidence.

3. **Bucket-handle tears:**
   - The lateral meniscus is more prone to bucket-handle tears than the medial meniscus (higher prior probability).
   - Should a bucket-handle configuration (Lens L5) be weighted more heavily as evidence for the lateral meniscus than for the medial meniscus?
   - PROPOSAL: The founder confirms this anatomical prior and its weight in the scoring.

4. **Capsular separation (Lens L7):**
   - Meniscal-capsular separation is visible in some lateral meniscal tears but is not specific (can occur with capsular laxity or age).
   - Is Lens L7 sufficiently specific to contribute to the diagnostic path, or is it too directional and weak?
   - PROPOSAL: Example images with and without tears would help calibrate the warrant of L7.

5. **Comparison of medial vs. lateral menisci:**
   - The medial meniscus is more firmly attached, more weight-bearing, and more prone to degenerative changes.
   - The lateral meniscus is more mobile, less weight-bearing, and more prone to traumatic bucket-handle tears.
   - Should the diagnostic thresholds or weights differ between the two?
   - PROPOSAL: The founder considers whether separate calibrations (different baseline signal thresholds, different warrant weights) are justified.

6. **Independence of meniscal findings:**
   - The medial and lateral menisci can be torn independently or together in a single injury.
   - Should the scoring of one raise or lower the expected score of the other?
   - PROPOSAL: The founder rules on independence vs. mechanical coupling.

---

---

## Part 3: Integration — The Meniscal Committee

### 3.1 The Two Menisci as Separate Agencies

The medial and lateral menisci are distinct structures in distinct locations. Each is assigned its own question by the diagnostic radiologist:
- "Is the medial meniscus abnormal?" → Confidence score for Medial Meniscus label
- "Is the lateral meniscus abnormal?" → Confidence score for Lateral Meniscus label

By the lens principle (thesis_reading_claude.md §3.2), each meniscus is an independent lens reading, measured by its own lenses (M1–M6 and L1–L7).

### 3.2 Downward-Looking Contract for the Meniscal Committee

**PROPOSAL for founder ruling:**

A meniscal finding is assigned (confidence > some threshold) when:
- **Strict assignment:** A DEFINITIONAL path holds (Path D1, D2, D3 per meniscus), AND
- **Warrant:** The law (MR physics, anatomy, mechanics) that makes the path definitive is satisfied.

A meniscal finding is refuted (confidence ≈ 0) when:
- **Strict exclusion:** The EXCLUSION path holds (E1 per meniscus), AND
- **Warrant:** The law that makes the exclusion strict is satisfied.

In all other cases (multiple DIRECTIONAL evidence, missing series, artifact, ambiguous morphology):
- **Abstain:** The system withholds a confident score and returns an abstention, naming the next acquisition (which series, which sequence) or the next call (founder to refine the definition of "abnormality").

**PROPOSAL:** The downward-looking contract for the meniscal committee is:
- "A meniscal abnormality is assigned when the DEFINITIONAL paths are met; refuted when EXCLUSION is clear; otherwise abstain."
- No weighting by majority of lenses, no averaging, no single-lens dominance (unless a narrow lens like L5 or L4 is definitive).
- A disagreement between lenses (e.g., M1 high, M2 normal morphology) is recorded and investigated as a near-miss, not averaged away.

---

### 3.3 The Meniscal Group vs. Other Labels

The meniscal labels (Medial Meniscus, Lateral Meniscus) are part of Group B in the facts file (00_facts.md §6). They are distinct from:
- **Group A (Ligaments):** ACL, MCL — different structures, different imaging signatures
- **Group C (Joint-level findings):** OA, Effusion, Synovitis, Baker's, Contusion, Fracture — different mechanisms (degenerative, inflammatory, traumatic)

However, meniscal tears can MECHANICALLY CAUSE or RAISE the expected scores of:
- **Effusion and Synovitis:** acute inflammatory response to a tear
- **Baker's cyst (for lateral meniscus):** mechanical communication to the posterior capsule
- **OA:** degenerative pathway over time (tear accelerates OA)
- **Contusion and Fracture:** co-injury from the same trauma

The committee must handle these mechanical couplings without allowing one label to "explain away" another. (PROPOSAL — founder to set the contracts for the committee's downward-looking decisions.)

---

## Summary: Proposals for Founder Ruling

### Definitional Questions

1. **What is "abnormality" for the meniscal labels?**
   - Tears only, or also degeneration, cysts, partial tears, capsular injuries?
   - If both, what grades of degeneration count?

2. **What is the radiological standard for tear vs. degeneration?**
   - Tear: T2 signal reaching the meniscal surface (or visible tear morphology)
   - Degeneration: Intra-meniscal signal without surface involvement?
   - This would warrant the Lens M2 and L2 (morphology) as DEFINITIONAL.

3. **Mechanical coupling of meniscal findings to other labels:**
   - Does a meniscal tear mechanically drive (or raise) the expected confidence in Effusion, Synovitis, Baker's cyst, OA, etc.?
   - Or are meniscal findings independent observations, scored on their own lenses?

### Operational Questions

4. **Calibration of signal intensity thresholds:**
   - What T2 signal intensity in the posterior horn (Lenses M1, L1) is "elevated" enough to raise confidence?
   - Reference: the population distribution in normal knees at the same site and sequence.
   - PROPOSAL: The founder (or radiology team) supplies example images from the 58 labeled studies to set these thresholds.

5. **Extrusion threshold:**
   - At what millimeter distance is meniscal extrusion (Lenses M3, L3) "abnormal"?
   - The lateral meniscus has higher baseline mobility; should the threshold differ?

6. **Warrant for narrow lenses (L4, L5, L2, L2 when linear):**
   - When do these lenses "settle the question" and assign DEFINITIONAL warrant?
   - Do they need agreement from other lenses, or is one narrow lens sufficient?
   - PROPOSAL: The downward-looking contract specifies this.

7. **The minimum series set required for a reading:**
   - Must ALL planes (sagittal, coronal, axial) be present, or can a confident reading be made from sagittal + coronal alone?
   - For the test set, define when to ABSTAIN due to missing series.

8. **Magic angle artifact:**
   - How to train Lens M2 and L2 (morphology) to reject magic angle automatically, or is a separate check needed?
   - PROPOSAL: Example images showing the artifact.

9. **Degeneration vs. tear — the boundary case:**
   - Example near-misses from the 58 labeled studies would expose the radiologist's threshold.
   - Does a study with "mild intra-meniscal signal, no extrusion, intact roots" score positive or negative?

10. **Lateral meniscus and popliteal cyst:**
    - Is the mechanical linkage tight enough that a significant cyst (Lens L6) without obvious meniscal signal raises confidence in a lateral meniscal tear?
    - PROPOSAL: Founder rules on the warrant of L6 alone vs. L6 + L1 together.

---

## Appendix: Lens Table Summary

| Meniscus | Lens | Measurement | Site | Series | Warrant | Classification |
|---|---|---|---|---|---|---|
| Medial | M1 | T2 signal at posterior horn | Post. horn, sagittal | Sag FS T2 | Wide (SnNout) | DIRECTIONAL FOR |
| Medial | M2 | Signal morphology — linear vs. diffuse | All slices, sagittal | Sag FS T2 | Narrow (SpPin) | DEFINITIONAL (if linear to surface) |
| Medial | M3 | Extrusion distance from tibial margin | Mid-body, coronal | Cor FS T2 | Directional | DIRECTIONAL FOR |
| Medial | M4 | Root integrity — insertion sharp vs. blurred | Ant. & post. roots | Sag FS T2, T1 | Narrow (SpPin) | DEFINITIONAL (if clearly torn) |
| Medial | M5 | Meniscal morphology — C-shape, bucket-handle | All views, coronal & axial | Cor/Ax FS T2 | Narrow (SpPin) | DEFINITIONAL (if bucket-handle) |
| Medial | M6 | Associated effusion or synovitis | Focal to tear site, all planes | FS T2 | Directional | DIRECTIONAL FOR |
| Lateral | L1 | T2 signal at posterior horn | Post. horn, sagittal | Sag FS T2 | Wide (SnNout) | DIRECTIONAL FOR |
| Lateral | L2 | Signal morphology — linear vs. diffuse | All slices, sagittal | Sag FS T2 | Narrow (SpPin) | DEFINITIONAL (if linear to surface) |
| Lateral | L3 | Extrusion distance from tibial margin | Mid-body, coronal | Cor FS T2 | Directional | DIRECTIONAL FOR |
| Lateral | L4 | Root integrity — insertion sharp vs. blurred | Ant. & post. roots | Sag FS T2, T1 | Narrow (SpPin) | DEFINITIONAL (if clearly torn) |
| Lateral | L5 | Meniscal morphology — O-shape, bucket-handle | All views, coronal & axial | Cor/Ax FS T2 | Narrow (SpPin) | DEFINITIONAL (if bucket-handle) |
| Lateral | L6 | Popliteal cyst presence and size | Post. capsule | Sag FS T2 | Directional | DIRECTIONAL FOR (mechanic link) |
| Lateral | L7 | Meniscal-capsular separation | Periphery, coronal | Cor FS T2 | Directional | DIRECTIONAL FOR |

---

## Notes for the Next Phase

This document is a **proposal** for founder ruling. Each section marked PROPOSAL is a structural decision or a lens warranty that only the founder can confirm or refine.

The next phase will:
1. The founder rules on the definitions, the warrants, and the mechanical couplings.
2. Other agents analyze the remaining 10 labels using this meniscal lens-building as a template.
3. The lenses are coded and integrated into a reference implementation (in Python, per Law 3 of AGENTS.md).
4. The 58 labeled studies are reviewed to calibrate the thresholds (signal intensity, extrusion distance, morphology criteria) and expose near misses.
5. The meniscal committee (M1–M6 for medial, L1–L7 for lateral) is assembled in the detective/acceptance harness as pure decision functions, pinned and property-tested.

---

**Prepared for:** The founder  
**Date:** 2026-10-10  
**Status:** Proposals for ruling; no code, no calibration, no testing until founder confirms the structural reasoning.
