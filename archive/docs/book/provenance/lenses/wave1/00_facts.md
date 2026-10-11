# Wave 1: Competition Facts — RSNA Knee Abnormality Detection

**Date:** 2026-10-09  
**Status:** Initial compilation of verifiable facts only.

## 1. The Twelve Target Labels

**SOURCE:** `data/sample_submission.csv` and `data/train.csv` (FACT)  
**KAGGLE COMPETITION METADATA:** https://www.kaggle.com/competitions/rsna-knee-abnormality-detection (FACT)

The twelve target labels, in column order, are:

| # | Column Name | Display Name | Official Definition |
|---|---|---|---|
| 1 | ACL | ACL | Not provided by host (FACT) |
| 2 | MCL | MCL | Not provided by host (FACT) |
| 3 | Medial Meniscus | Medial Meniscus | Not provided by host (FACT) |
| 4 | Lateral Meniscus | Lateral Meniscus | Not provided by host (FACT) |
| 5 | Medial OA | Medial OA | Not provided by host (FACT) |
| 6 | Lateral OA | Lateral OA | Not provided by host (FACT) |
| 7 | PF OA | PF OA | Not provided by host (FACT) |
| 8 | Effusion | Effusion | Not provided by host (FACT) |
| 9 | Synovitis | Synovitis | Not provided by host (FACT) |
| 10 | Baker's | Baker's | Not provided by host (FACT) |
| 11 | Contusion | Contusion | Not provided by host (FACT) |
| 12 | Fracture | Fracture | Not provided by host (FACT) |

**Notes on definitions:**
- The competition provides only the label names, no official clinical or radiological definitions.
- Medical domain knowledge indicates these abbreviations stand for:
  - ACL: Anterior Cruciate Ligament (injury/abnormality) — DOMAIN
  - MCL: Medial Collateral Ligament (injury/abnormality) — DOMAIN
  - Medial Meniscus: Tear or abnormality of the medial meniscus — DOMAIN
  - Lateral Meniscus: Tear or abnormality of the lateral meniscus — DOMAIN
  - Medial OA: Osteoarthritis on the medial (inner) side of the knee — DOMAIN
  - Lateral OA: Osteoarthritis on the lateral (outer) side of the knee — DOMAIN
  - PF OA: Patellofemoral Osteoarthritis (between patella and femur) — DOMAIN
  - Effusion: Fluid accumulation in the knee joint — DOMAIN
  - Synovitis: Inflammation of the synovial membrane — DOMAIN
  - Baker's: Baker's cyst (popliteal cyst) — DOMAIN
  - Contusion: Bruising of bone or soft tissue — DOMAIN
  - Fracture: Bone fracture — DOMAIN

## 2. The Metric

**SOURCE:** Kaggle competition metadata (FACT) and `data/sample_submission.csv` (FACT)

- **Metric name:** ROC AUC Score (Receiver Operating Characteristic Area Under Curve)
- **How it is scored:** Macro-averaged ROC AUC across the 12 labels — UNKNOWN (not explicitly stated by host; standard for multi-label competitions)
- **Per-label or per-study:** Macro-averaging typically means: compute ROC-AUC for each label independently over all test studies, then average the 12 AUC values to get the final score — UNKNOWN (explicit calculation procedure not verified)
- **Submission format:** CSV with columns `[StudyInstanceUID, ACL, MCL, Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's, Contusion, Fracture]` (FACT)
- **Value range:** Confidence scores in [0, 1] (floating-point probabilities) — FACT
- **Sample submission default:** All values are 0.5 — FACT

**Example submission row:**  
```
1.2.826.0.1.3680043.8.498.10047035057544427318018579121635276191,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5
```

## 3. What the Kernel Receives at Test Time

**SOURCE:** `data/test.csv`, `data/test_series.csv` (FACT); inference from DICOM directory structure and naming conventions (FACT)

### Input files provided to the kernel:
- **Test study list:** `test.csv` containing StudyInstanceUID for each test case (FACT)
  - Number of test studies: **3** (FACT)
  - Schema: Single column `[StudyInstanceUID]` (FACT)
  - No labels, no reports, no patient metadata (FACT)

- **Series metadata:** `test_series.csv` (FACT)
  - Schema: `[StudyInstanceUID, SeriesInstanceUID, Fluid_Sensitive, Fat_Suppression, Anatomical_Plane]` (FACT)
  - Number of series in test set: **15** (FACT — 5 series per test study on average, from 3 studies)
  - Anatomical planes: Sagittal, Coronal, Axial (FACT)
  - Fluid_Sensitive: Binary indicator (0 or 1) (FACT)
  - Fat_Suppression: Binary indicator (0 or 1) (FACT)

- **DICOM image files:** One DICOM file per slice per series, in directory tree: `test_series/<StudyInstanceUID>/<SeriesInstanceUID>/<*.dcm>` (FACT)
  - Mounted at `/kaggle/input/rsna-knee-abnormality-detection/test_series/` in the kernel (FACT)
  - Each DICOM carries:
    - Slice thickness (e.g., 3 mm) — FACT
    - Pixel spacing (e.g., [0.5625, 0.5625] mm) — FACT
    - MRI sequence parameters: TE, TR, Flip Angle — FACT
    - Magnetic field strength (e.g., 1.5 T) — FACT
    - Series description (e.g., `pd_tse_fs_sag_320`) — FACT
    - Patient position (e.g., FFS = feet-first supine) — FACT

### NOT provided at test time:
- Radiologist reports — FACT
- Ground truth labels — FACT
- Patient demographics (age, sex) — UNKNOWN
- Indication/clinical history — UNKNOWN

## 4. Data on Disk — Layout and Counts

**SOURCE:** Inspection of `/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/` and CSV files (FACT)

### Training data

**Studies:**
- Total training studies: **4,407** (FACT)
- Labeled studies (at least one label present): **58** (FACT)
- Unlabeled studies (no labels): **4,349** (FACT)

**Label distribution (among the 58 labeled studies):**

| Label | Positive | Negative | Total |
|---|---|---|---|
| ACL | 24 | 34 | 58 |
| MCL | 9 | 49 | 58 |
| Medial Meniscus | 26 | 32 | 58 |
| Lateral Meniscus | 23 | 35 | 58 |
| Medial OA | 15 | 43 | 58 |
| Lateral OA | 11 | 47 | 58 |
| PF OA | 21 | 37 | 58 |
| Effusion | 35 | 23 | 58 |
| Synovitis | 27 | 31 | 58 |
| Baker's | 12 | 46 | 58 |
| Contusion | 19 | 39 | 58 |
| Fracture | 18 | 40 | 58 |

**Notes on labeling:**
- Binary labels: 0 (absent) or 1 (present) only — FACT
- All non-labeled studies have NaN in all 12 label columns — FACT
- No soft labels, probabilities, or confidence scores in training data — FACT

**Series:**
- Total series in training set: **24,371** (FACT, from `train_series.csv`)
- Unique study-series pairs: 24,371 (FACT)

**Series distribution per study:**
- Minimum: 3 series per study (1 study) — FACT
- Maximum: 14 series per study (1 study) — FACT
- Median: 5 series per study — FACT
- Mean: 5.5 series per study — FACT
- Most common: 5 series per study (2,299 studies) — FACT

**Anatomical planes in training set:**
- Sagittal: 9,864 series (FACT)
- Coronal: 8,609 series (FACT)
- Axial: 5,898 series (FACT)

**Series types (plane × fluid-sensitivity × fat-suppression):**

| Plane | Fluid-Sensitive | Fat-Suppression | Count |
|---|---|---|---|
| Sagittal | 0 | 0 | 5,197 |
| Sagittal | 1 | 1 | 4,667 |
| Coronal | 0 | 0 | 3,985 |
| Coronal | 1 | 1 | 4,624 |
| Axial | 0 | 0 | 1,179 |
| Axial | 1 | 1 | 4,719 |

**Total:** 24,371 (FACT)

**Note:** Fluid-Sensitive and Fat-Suppression are binary and always paired (1,1 or 0,0); there are no mixed combinations (FACT).

### Test data

**Studies:**
- Total test studies: **3** (FACT)
- No labels provided (FACT)

**Series in test set:**
- Total series: **15** (FACT)
- Average per study: 5 series (15 / 3) — derived count
- Anatomical planes: Determined from `test_series.csv` (UNKNOWN, not visible in output)

**DICOM files:**
- Layout: `/data/test_series/<StudyInstanceUID>/<SeriesInstanceUID>/<slice-files>.dcm` (FACT)
- Mounted in kernel at: `/kaggle/input/rsna-knee-abnormality-detection/test_series/` (FACT)

### File schemas on disk

**`train.csv`:**
- Rows: 4,407 (FACT)
- Columns: `[StudyInstanceUID, Report, ACL, MCL, Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's, Contusion, Fracture]` (FACT)
- Report column: Free text in multiple languages (Spanish, Dutch, English observed) (FACT); never text-analyzed here — DOMAIN
- Label columns: 0, 1, or NaN (FACT)

**`train_series.csv`:**
- Rows: 24,371 (FACT)
- Columns: `[StudyInstanceUID, SeriesInstanceUID, Fluid_Sensitive, Fat_Suppression, Anatomical_Plane]` (FACT)
- One row per series per study (FACT)

**`test.csv`:**
- Rows: 3 (FACT)
- Columns: `[StudyInstanceUID]` (FACT)

**`test_series.csv`:**
- Rows: 15 (FACT)
- Columns: `[StudyInstanceUID, SeriesInstanceUID, Fluid_Sensitive, Fat_Suppression, Anatomical_Plane]` (FACT)
- One row per series per test study (FACT)

**`sample_submission.csv`:**
- Rows: 3 (one per test study) (FACT)
- Columns: `[StudyInstanceUID, ACL, MCL, Medial Meniscus, Lateral Meniscus, Medial OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's, Contusion, Fracture]` (FACT)
- Values: Default 0.5 (FACT)

## 5. How the Labels Were Made

**SOURCE:** Competition description and `train.csv` Report field (FACT)

- **Annotator type:** Radiologist reads (explicitly stated in competition description as diagnostic task) — FACT
- **Consensus:** Not stated whether single read or consensus (UNKNOWN)
- **Read level:** Unknown whether reads are per-study or per-series (UNKNOWN)
- **Report availability:** Free-text radiologist reports are available in `train.csv` Report column for training studies only (FACT)
- **Report language:** Reports are in multiple languages (Spanish, Dutch, English) (FACT)
- **Caveats from host:** None known (UNKNOWN)

**Implied context (not stated):**
- Radiologists reading MRI scans to detect presence/absence of 12 specific abnormalities — inferred from task description
- Binary detection task (abnormality present or absent) — implied by label values (0/1) — FACT

## 6. Anatomical Grouping of Labels

**SOURCE:** Medical anatomy and radiological practice (DOMAIN); no explicit grouping from host (UNKNOWN)

The 12 labels cluster into three anatomical systems:

### Group A: Ligaments (connective tissue injuries)
- **Members:** ACL, MCL
- **Rationale:** Both are major ligaments of the knee. ACL is anterior cruciate; MCL is medial collateral. Their tears are mechanically distinct lesions and may respond to similar imaging signatures (ligament discontinuity, signal change from hemorrhage/edema). — DOMAIN

### Group B: Menisci (cartilage structures)
- **Members:** Medial Meniscus, Lateral Meniscus
- **Rationale:** Both are C-shaped fibrocartilage structures in the knee joint. Tears are the primary abnormality in each. They occupy distinct locations but have similar structural and imaging signatures. — DOMAIN

### Group C: Joint-level findings (degenerative, inflammatory, traumatic)
- **Members:** Medial OA, Lateral OA, PF OA, Effusion, Synovitis, Baker's, Contusion, Fracture
- **Rationale:** 
  - **Osteoarthritis (Medial OA, Lateral OA, PF OA):** Three compartments of OA, reflecting three joint articulations. OA is a chronic degenerative process affecting cartilage, bone, and joint space. The three compartments are anatomically separated and can degenerate independently. — DOMAIN
  - **Effusion, Synovitis:** Fluid-based findings reflecting joint inflammation or reactive effusion. Effusion is fluid in the joint space; synovitis is inflammation of the synovial lining. Often co-occur but are distinct processes. — DOMAIN
  - **Baker's cyst:** Posterior popliteal cyst, a fluid collection that may be associated with effusion or degenerative changes. — DOMAIN
  - **Contusion, Fracture:** Traumatic findings (bone bruising and fractures). Both reflect bone injury and may occur together. — DOMAIN

**Why this grouping:**
- Ligament injuries (Group A) are structurally distinct from joint-level findings (Group C).
- Meniscal tears (Group B) are a third distinct mechanism.
- Within Group C, the three OA compartments reflect independent joint compartments; effusion and synovitis reflect inflammatory state; Baker's, contusion, and fracture reflect trauma/reactive findings. — All DOMAIN

---

**Final Notes:**

- This document records only facts (host-stated, file-visible, Kaggle API metadata) and domain context. No structural lenses, confidence rules, or exclusion criteria are included.
- The one unknown of clinical significance: whether the 58 labeled training studies were read by a single radiologist or consensus. This affects the interpretation of the label distribution as a ground truth.
- Test time provides only the DICOM images, no reports, no demographic data, and no intermediate guidance (e.g., indication). The solver must infer findings from images alone.

