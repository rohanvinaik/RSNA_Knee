# Twelve diagnostic seed pairs: images, object bundles and the remaining connections

This packet contains one source-labeled positive and one condition-negative case for each of the twelve competition questions, drawn from the 58 labeled studies. There are **24 case pages, 12 paired pages and 52 distinct study/object bundle exports**, sharing ten source studies. Every case links its acquired images, the pipeline's saved candidate supports, its exact encoded measurements and the independent teaching call.

These are the seed examples for the next layer. Rohan's requested order is: build this basis, implement functional K-line memory and recall, use the cases for the first normal-versus-disease capacity test, then expand into mass training. The [AI design](AI_DIAGNOSTIC_DESIGN.md) specifies that continuation. **The current packet does not establish that all twelve diagnoses can already be recalled.** It exposes which observations are available and which distinctions have not reached the encoded content.

## How to read the evidence

The positive/negative labels come from `train.csv`, with verbatim supporting report excerpts below. A negative belongs to its particular condition; these knees can have other injuries. The reports and labels are teaching evidence, never image-resemblance features. Full reports and exact study identities are retained in [the v3 selection](../data/readings/diagnostic-pairs-20261020/selected-pairs.v3.json).

The overlays are the pipeline's actual saved candidates. **A verified source address means the saved support is being drawn on the correct acquired frame; it does not certify the anatomical name.** Some candidates are visibly misplaced. They remain visible so the distinction between candidate selection, encoding and subsequent learned interpretation can be examined. No mask was hand-drawn to improve a demonstration.

Case pages show the available views and the actual Hadamard rows. Missing views or content are explicitly marked. The complete record retains every observation; a page displays representative observations, not every measured place. Raw all-slice contacts are linked through the [render manifest](../data/readings/diagnostic-pairs-20261020/rendering/pair-pages-v3.json). Series-table view names and DICOM orientation metadata are retained separately; a filename alone is not an orientation check.

Each NPZ contains the exact object content count rows, their 512-component Hadamard vectors, bank identities and layout/source identities. The vectors were reconstructed from the saved object-composition counts and decoded back exactly. These are actual measurements, not invented features. Many currently occupied content banks encode the low-signal lens's Boolean reading. `True` and `False` there mean what that lens measured, not disease and health. Metadata, status and authored anatomical-definition banks are excluded from the comparisons.

Only compatible banks measured on both sides enter a comparison. The displayed cosine is resemblance between these two examples, not a probability or a diagnostic result. An empty comparison is **silent**, never zero similarity or normality. An exactly parallel pair can have different counts but cosine one; multiplying a profile by its size does not encode a size distinction for cosine.

## What this baseline actually contains

| Evidence | Result |
|---|---|
| Independent condition calls and full selected reports | 24 exact label joins; ten selected study reports match their source |
| Object exports, including separately labeled context objects | 52; 35 with occupied content banks, 17 empty/unmeasured |
| Exact counts → Hadamard → counts | All 52 exports pass |
| Opposing-label object comparisons | 20: seven nonparallel, seven exactly parallel, six silent |
| Actual diagnosis from functional K-line recall | Not run; this is the next-layer test |

The comparison counts include shared objects reused for different questions; they are not independent successes. Medial and lateral OA currently reuse whole-cartilage descriptions. Contusion and fracture reuse the same bone descriptions and source pair. They require their distinct anatomical questions and readings, not relabeling one generic similarity result.

The [catalogue-wide seed coverage index](../data/readings/diagnostic-pairs-20261020/encoding/seed-object-coverage-index.md) separately inventories all 44 canonical objects. These cases reference 18 of them; 26 have no case reference in this seed packet. A reference can be context rather than an independently taught object state.

The [numerical audit](../data/readings/diagnostic-pairs-20261020/encoding/v3-bundle-cosine-audit.md) gives exact terms. The [source audit](../data/readings/diagnostic-pairs-20261020/labels/final-evidence-audit.md) checks labels, supports and source frames. These audits establish provenance and arithmetic, not anatomy or diagnostic performance.

The [root visual inspection](../data/readings/diagnostic-pairs-20261020/root-visual-review.md)
records what the twelve pair pictures and four representative case pages actually show,
including misplaced candidates and unavailable encodings.

## The paired cases

### ACL

**Positive:** `1.2.826.0.1.3680043.8.498.18392509497170616983977319528036573378`. Source label `1`.

> Anterior çapraz bağ komplet rüptürü.

**Condition-negative:** `1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149`. Source label `0`.

> Ligamentos cruzados y colaterales dentro de límites normales.

The stored sagittal candidate in the positive case extends behind the joint rather than isolating a clean ACL. Its nonparallel profile is a real encoding difference, but cannot by itself be attributed to the reported tear. This is a candidate/interpretation issue to retain in teaching, not a successful ACL diagnosis.

![ACL: source-labeled pair and actual pipeline candidates](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/pairs/acl-pair.png)

| Object role | Shared measured banks | Cosine | Encoded comparison |
|---|---:|---:|---|
| acl | 2 | 0.736153 | Different directions |

[Positive case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/acl-positive.png) · [acl bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.18392509497170616983977319528036573378/acl.npz)

[Negative case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/acl-negative.png) · [acl bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/acl.npz)

### MCL

**Positive:** `1.2.826.0.1.3680043.8.498.62549354677638403845904556149868367236`. Source label `1`.

> Parti ële scheur proximaal op het mediale collaterale ligament, graad 2.

**Condition-negative:** `1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149`. Source label `0`.

> Ligamentos cruzados y colaterales dentro de límites normales.

The initial coronal positive marker lies centrally near the notch rather than clearly along the medial ligament course. Zero cosine therefore does not establish injury discrimination. The actual source image and all measured candidates remain available for an appropriate object/course cue.

![MCL: source-labeled pair and actual pipeline candidates](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/pairs/mcl-pair.png)

| Object role | Shared measured banks | Cosine | Encoded comparison |
|---|---:|---:|---|
| mcl | 2 | 0.000000 | Different directions |

[Positive case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/mcl-positive.png) · [mcl bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.62549354677638403845904556149868367236/mcl.npz)

[Negative case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/mcl-negative.png) · [mcl bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/mcl.npz)

### Medial Meniscus

**Positive:** `1.2.826.0.1.3680043.8.498.11382021393803389951964005983002209238`. Source label `1`.

> there is longitudinal vertical tear at the body and posterior horn of the medial meniscus.

**Condition-negative:** `1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149`. Source label `0`.

> Menisco medial de morfología y señal
> conservada, sin signos de rotura.

The sagittal positive candidate includes a large condylar region; the other views expose the same need to distinguish a named candidate from anatomical acceptance. The shared low-signal and directional rows differ, but the existing label does not validate the mask.

![Medial Meniscus: source-labeled pair and actual pipeline candidates](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/pairs/medial-meniscus-pair.png)

| Object role | Shared measured banks | Cosine | Encoded comparison |
|---|---:|---:|---|
| medial_meniscus | 5 | 0.549535 | Different directions |

[Positive case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/medial-meniscus-positive.png) · [medial_meniscus bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.11382021393803389951964005983002209238/medial_meniscus.npz)

[Negative case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/medial-meniscus-negative.png) · [medial_meniscus bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/medial_meniscus.npz)

### Lateral Meniscus

**Positive:** `1.2.826.0.1.3680043.8.498.10170898615867673028696505248839028269`. Source label `1`.

> Horizontal tear at anterior horn of the lateral meniscus is noted.

**Condition-negative:** `1.2.826.0.1.3680043.8.498.11382021393803389951964005983002209238`. Source label `0`.

> The lateral compartment, the meniscus is not torn and there is no focal chondrosis or chondral injury.

The positive coronal candidate marks a small joint-margin region. Some retained negative candidates lie in bone rather than the meniscus. The measured difference remains traceable; it is not a warrant to call the normal-versus-tear question solved.

![Lateral Meniscus: source-labeled pair and actual pipeline candidates](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/pairs/lateral-meniscus-pair.png)

| Object role | Shared measured banks | Cosine | Encoded comparison |
|---|---:|---:|---|
| lateral_meniscus | 1 | 0.000000 | Different directions |

[Positive case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/lateral-meniscus-positive.png) · [lateral_meniscus bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10170898615867673028696505248839028269/lateral_meniscus.npz)

[Negative case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/lateral-meniscus-negative.png) · [lateral_meniscus bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.11382021393803389951964005983002209238/lateral_meniscus.npz)

### Medial OA

**Positive:** `1.2.826.0.1.3680043.8.498.65708905118633339771181857781063784327`. Source label `1`.

> There is diffuse high grade and low grade chondrosis (less than and more than 50% thickness cartilage loss) along weightbaring medial femoral condyle and medial tibial plateau.

**Condition-negative:** `1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149`. Source label `0`.

> Cartílagos de los compartimentos femorotibiales sin alteraciones.

The positive report supplies a medial-compartment call. Current cartilage rows are whole-object measurements, not a newly established medial compartment profile. The femoral-cartilage pair is parallel; the tibial-cartilage pair differs; the medial-meniscus comparison is silent. Preserve compartment roles and local surface relationships in the diagnostic case.

![Medial OA: source-labeled pair and actual pipeline candidates](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/pairs/medial-oa-pair.png)

| Object role | Shared measured banks | Cosine | Encoded comparison |
|---|---:|---:|---|
| femoral_cartilage | 1 | 1.000000 | Exactly parallel |
| tibial_cartilage | 2 | 0.806874 | Different directions |
| medial_meniscus | 0 | — | Silent: no shared measured bank |

[Positive case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/medial-oa-positive.png) · [femoral_cartilage bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.65708905118633339771181857781063784327/femoral_cartilage.npz) · [tibial_cartilage bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.65708905118633339771181857781063784327/tibial_cartilage.npz) · [medial_meniscus bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.65708905118633339771181857781063784327/medial_meniscus.npz)

[Negative case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/medial-oa-negative.png) · [femoral_cartilage bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/femoral_cartilage.npz) · [tibial_cartilage bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/tibial_cartilage.npz) · [medial_meniscus bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/medial_meniscus.npz)

### Lateral OA

**Positive:** `1.2.826.0.1.3680043.8.498.65708905118633339771181857781063784327`. Source label `1`.

> There is focal high grade chondrla defectat mid lateral tibial plateau (about 1.2* 1.1 cm).

**Condition-negative:** `1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149`. Source label `0`.

> Cartílagos de los compartimentos femorotibiales sin alteraciones.

This uses the same source studies and whole-cartilage counts as the medial OA example. That is honest reuse, but those counts alone do not distinguish the two compartment questions. The lateral-meniscus comparison is silent. A compartment-specific relation must be represented as such, not inferred from the label.

![Lateral OA: source-labeled pair and actual pipeline candidates](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/pairs/lateral-oa-pair.png)

| Object role | Shared measured banks | Cosine | Encoded comparison |
|---|---:|---:|---|
| femoral_cartilage | 1 | 1.000000 | Exactly parallel |
| tibial_cartilage | 2 | 0.806874 | Different directions |
| lateral_meniscus | 0 | — | Silent: no shared measured bank |

[Positive case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/lateral-oa-positive.png) · [femoral_cartilage bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.65708905118633339771181857781063784327/femoral_cartilage.npz) · [tibial_cartilage bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.65708905118633339771181857781063784327/tibial_cartilage.npz) · [lateral_meniscus bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.65708905118633339771181857781063784327/lateral_meniscus.npz)

[Negative case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/lateral-oa-negative.png) · [femoral_cartilage bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/femoral_cartilage.npz) · [tibial_cartilage bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/tibial_cartilage.npz) · [lateral_meniscus bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/lateral_meniscus.npz)

### PF OA

**Positive:** `1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149`. Source label `1`.

> Condropatía focal grado 4 del aspecto inferior de la vertiente medial de la tróclea femoral .

**Condition-negative:** `1.2.826.0.1.3680043.8.498.17844546765907321649997094867791102711`. Source label `0`.

> Eklem kıkırdakları ve kemikler bunların dışında normal.

The positive report localizes the cartilage abnormality to the trochlea and describes the patellar cartilage as unaltered. The retained supports and raw measurements exist, but the selected positive object-composition content is empty, so both cartilage comparisons are silent. The negative candidate also needs anatomical interpretation; a correct frame address does not validate its location. Do not label every pixel in this positive compartment diseased.

![PF OA: source-labeled pair and actual pipeline candidates](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/pairs/pf-oa-pair.png)

| Object role | Shared measured banks | Cosine | Encoded comparison |
|---|---:|---:|---|
| patellar_cartilage | 0 | — | Silent: no shared measured bank |
| trochlear_cartilage | 0 | — | Silent: no shared measured bank |

[Positive case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/pf-oa-positive.png) · [patellar_cartilage bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/patellar_cartilage.npz) · [trochlear_cartilage bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/trochlear_cartilage.npz)

[Negative case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/pf-oa-negative.png) · [patellar_cartilage bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.17844546765907321649997094867791102711/patellar_cartilage.npz) · [trochlear_cartilage bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.17844546765907321649997094867791102711/trochlear_cartilage.npz)

### Effusion

**Positive:** `1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149`. Source label `1`.

> Leve derrame articular.

**Condition-negative:** `1.2.826.0.1.3680043.8.498.11382021393803389951964005983002209238`. Source label `0`.

> No knee effusion is present.

The images and retained fluid/recess readings supply an actual starting point. The current shared joint-fluid bank is exactly parallel and the recess comparison is silent. Fluid presence alone is not the same reading as excess fluid; extent and distribution need their declared encoding if the diagnostic question uses them.

![Effusion: source-labeled pair and actual pipeline candidates](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/pairs/effusion-pair.png)

| Object role | Shared measured banks | Cosine | Encoded comparison |
|---|---:|---:|---|
| joint_fluid | 1 | 1.000000 | Exactly parallel |
| anterior_synovial_recess | 0 | — | Silent: no shared measured bank |

[Positive case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/effusion-positive.png) · [joint_fluid bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/joint_fluid.npz) · [anterior_synovial_recess bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/anterior_synovial_recess.npz)

[Negative case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/effusion-negative.png) · [joint_fluid bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.11382021393803389951964005983002209238/joint_fluid.npz) · [anterior_synovial_recess bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.11382021393803389951964005983002209238/anterior_synovial_recess.npz)

### Synovitis

**Positive:** `1.2.826.0.1.3680043.8.498.39500553372517290823815606829518305500`. Source label `1`.

> Leve a moderado derrame articular con mínima sinovitis.

**Condition-negative:** `1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149`. Source label `0`.

> Leve derrame articular.

The retained synovial support is small: a marker/local reading, not a recovered complete lining. The positive report explicitly calls minimal synovitis. The negative is supported by the condition label; its report does not explicitly certify a normal synovium. Different encoded readings therefore establish a comparison, not a completed lining diagnosis.

![Synovitis: source-labeled pair and actual pipeline candidates](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/pairs/synovitis-pair.png)

| Object role | Shared measured banks | Cosine | Encoded comparison |
|---|---:|---:|---|
| synovium | 2 | 0.696633 | Different directions |

[Positive case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/synovitis-positive.png) · [synovium bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.39500553372517290823815606829518305500/synovium.npz)

[Negative case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/synovitis-negative.png) · [synovium bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/synovium.npz)

### Baker's

**Positive:** `1.2.826.0.1.3680043.8.498.65708905118633339771181857781063784327`. Source label `1`.

> A 1.5*1.5* 4.5 cm baker's cyst at the posteromedial aspect of left knee.

**Condition-negative:** `1.2.826.0.1.3680043.8.498.10306159113324811538703788080836752052`. Source label `0`.

> No Baker's cyst.

The positive raw image shows a conspicuous lobulated bright posterior structure, while the negative report explicitly states no Baker cyst. These are deliberately raw illustrative slices: the retained bursa object has no measured composition content or source support in this cohort product. The image pair is usable teaching context; no bursa vector comparison is claimed.

![Baker's: source-labeled pair and actual pipeline candidates](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/pairs/baker's-pair.png)

| Object role | Shared measured banks | Cosine | Encoded comparison |
|---|---:|---:|---|
| gastrocnemius_semimembranosus_bursa | 0 | — | Silent: no shared measured bank |

[Positive case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/baker's-positive.png) · [gastrocnemius_semimembranosus_bursa bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.65708905118633339771181857781063784327/gastrocnemius_semimembranosus_bursa.npz)

[Negative case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/baker's-negative.png) · [gastrocnemius_semimembranosus_bursa bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10306159113324811538703788080836752052/gastrocnemius_semimembranosus_bursa.npz)

### Contusion

**Positive:** `1.2.826.0.1.3680043.8.498.64703506772167798469048460791472465039`. Source label `1`.

> Additional small area of bone marrow edema on the medial side of medial femoral condyle without evidence of associated fracture.

**Condition-negative:** `1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149`. Source label `0`.

> No hay alteraciones de señal significativas de la médula ósea.

The report localizes additional marrow edema without fracture, but the selected retained bone candidate on the outer sagittal slice is broad and includes soft tissue. The source contacts show interior bone sections separately. Both bone count profiles are exactly parallel under the compared bank. The current encoding does not yet expose the reported marrow-state distinction.

![Contusion: source-labeled pair and actual pipeline candidates](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/pairs/contusion-pair.png)

| Object role | Shared measured banks | Cosine | Encoded comparison |
|---|---:|---:|---|
| femur | 1 | 1.000000 | Exactly parallel |
| tibia | 1 | 1.000000 | Exactly parallel |

[Positive case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/contusion-positive.png) · [femur bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.64703506772167798469048460791472465039/femur.npz) · [tibia bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.64703506772167798469048460791472465039/tibia.npz)

[Negative case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/contusion-negative.png) · [femur bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/femur.npz) · [tibia bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/tibia.npz)

### Fracture

**Positive:** `1.2.826.0.1.3680043.8.498.64703506772167798469048460791472465039`. Source label `1`.

> Small osteochondral impaction fracture of the lateral corner of lateral femoral condyle.

**Condition-negative:** `1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149`. Source label `0`.

> No hay alteraciones de señal significativas de la médula ósea.

The report supplies explicit femoral and tibial fracture findings. The same broad bone candidates and parallel profiles used for contusion do not separately encode disrupted bone continuity. Keep the actual acquired images and source report, and connect the relevant structural reading before claiming that recall can answer fracture.

![Fracture: source-labeled pair and actual pipeline candidates](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/pairs/fracture-pair.png)

| Object role | Shared measured banks | Cosine | Encoded comparison |
|---|---:|---:|---|
| femur | 1 | 1.000000 | Exactly parallel |
| tibia | 1 | 1.000000 | Exactly parallel |

[Positive case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/fracture-positive.png) · [femur bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.64703506772167798469048460791472465039/femur.npz) · [tibia bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.64703506772167798469048460791472465039/tibia.npz)

[Negative case: views and vector rows](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v3/cases/fracture-negative.png) · [femur bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/femur.npz) · [tibia bundle](../data/readings/diagnostic-pairs-20261020/encoding/bundles-v3/1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149/tibia.npz)

## From these cases to functional K-lines

The stored case must retain the image-derived cue, its object/relationship roles and its independent call. It enters the appropriate normal/condition bucket as an individual case; other diagnoses in the same study do not contaminate its scope. Full and cheap descriptions remain linked to that same case. A new input produces a compatible cheap cue and compares it with these precedents. The recalled interpretation answers a question or requests a particular missing reading. It does not require every border to be redrawn first.

This packet identifies three different kinds of next work:

1. **Source/candidate scope:** preserve useful regions and their uncertainty; a misplaced candidate cannot be promoted to an accepted anatomical example merely because its bytes decode. Candidate correction or learned interpretation must remain distinguishable from the underlying lens measurement.
2. **Representation:** connect retained readings that have not reached content banks, supply the declared reference semantics for numeric readings, and encode diagnostic relationships/extent where those are the question. PF cartilage and the bursa are explicit missing-content cases here. More copies of a silent or proportional profile do not create the missing distinction.
3. **Memory and recall:** implement the cases, answer buckets, K-lines, compatibility, warranted recall and independent teaching. Test actual normal-versus-disease recognition through that path, then expand the same machinery into mass training. Self-recall is a wiring test; a study excluded from memory is the transfer test.

These tasks do not require perfect segmentation. The aim is the useful structured description Rohan specified, with enough actual information for the question being asked. The [build plan](AI_DIAGNOSTIC_DESIGN.md#11-parallel-implementation-contracts) separates the mechanical lanes so storage, retrieval, evidence and integration can proceed concurrently.

## Reproduction and provenance

The evidence uses retained products from `data/readings/hdc-20261020/cohort/attempt-1/encoding/`, produced from the frozen source recorded with that attempt. No production recognition or diagnosis code was changed for this packet. The original cohort wrapper returned one after a macOS timing-tool error; this packet independently checks the selected readable products rather than describing that historical run as a clean successful exit.

- [Selected source cases and full reports](../data/readings/diagnostic-pairs-20261020/selected-pairs.v3.json).
- [Fixed diagnostic versus context roles](../data/readings/diagnostic-pairs-20261020/condition-objects.v3.json).
- [All observations, decoded rows, exports and exact comparison terms](../data/readings/diagnostic-pairs-20261020/encoding/pair-evidence.v3.json).
- [Image addresses, raw hashes, support checks and contact-sheet indexes](../data/readings/diagnostic-pairs-20261020/rendering/pair-pages-v3.json).
- [Carrier and cosine audit](../data/readings/diagnostic-pairs-20261020/encoding/v3-bundle-cosine-audit.md).
- [Independent source audit](../data/readings/diagnostic-pairs-20261020/labels/final-evidence-audit.md).

The source evidence and images are competition-derived local artifacts under the ignored `data/` tree. The Markdown references them; publishing the Markdown alone will not include them.
