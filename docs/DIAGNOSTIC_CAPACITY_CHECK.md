# Twelve diagnostic cases: acquired images and named HDC differences

This is the visual capacity check requested by Rohan. It presents one independently labeled condition-negative and one diagnosed case for each of the twelve competition questions, drawn from ten of the 58 official labeled studies. These are individual contextual case memories, not averaged class prototypes or pixel templates.

The purpose is to establish useful normal/diagnosed precedents for K-line recognition. A diagnostic interpretation may follow from the remembered configuration without reconstructing every object or requiring each individual lens to diagnose anything. The current run below exercises that memory path; it does not yet demonstrate warranted diagnosis for all twelve conditions.

## What the pictures and numbers mean

- Negative is a negative call for this condition. Other conditions may occur in the same study. Labels and reports teach the memory; they are not resemblance features.
- Pictures use actual acquired DICOM pixels. Overlays are saved rule-named candidates with verified source addresses, not hand-drawn truth. Black support panels can mean an empty or unavailable support; the caption distinguishes these.
- `low_signal:True` and `low_signal:False` are the B1 lens words. They do not mean disease and health. Counts are contributions to the declared HDC rows, not MRI intensity or probability.
- A measured word count of **0** differs from **—**, an unavailable/silent bank contribution. Delta means diagnosed minus negative and is shown only where both sides measured that bank.
- F/S below are the competition series-table fluid-sensitivity/fat-suppression flags. They do not identify T1 versus PD or prove a contrast protocol. DICOM orientation vectors remain in the source record; the dominant-normal check agrees with the table labels for all 24 shown frames.
- An object is one combined representation across the available views, scales and directions. A figure shows a representative frame; its HDC table can include other addressed observations. The bone context overrides are explicit and preserve the original measured-frame addresses.

## The executed memory check

The real production command taught **108 individual signed cases** from the ten selected products and queried all ten studies with their own cases excluded. It loaded memory once and ran no full anatomical reconstruction. Teaching took 71.764 seconds (2.615 GB peak RSS); querying took 120.240 seconds (1.265 GB peak RSS). Those costs exclude the earlier creation of the retained products. Stronger source-group linkage was unavailable and remains unknown.

All twelve questions returned proposals or `unresolved_missing_reading`. No trusted speaking call was emitted: this run installed no MRI trust records. This is an executed recall/evidence test, not twelve successful diagnoses. The [complete run report](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/query-capacity/report.md) keeps each question, official label, supporting/opposing precedent and actual bank set separate.

## The twelve pairs

### ACL

The remembered case is the ACL in its attachment context, with an independent injury call. The displayed negative support is empty on this one frame, although another retained sagittal reading contributes counts. The positive saved candidate extends posteriorly; a source-verified candidate is not an independently accepted ACL outline.

![ACL: condition-negative left, diagnosed right, acquired images and named HDC count differences](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v4/named-pairs/acl-named-pair.png)

**Independent report evidence:**

- Negative: Ligamentos cruzados y colaterales dentro de límites normales.
- Diagnosed: Anterior çapraz bağ komplet rüptürü.

| Object | View; F/S | Measured row | Negative | Diagnosed | Delta |
|---|---|---|---:|---:|---:|
| acl | Sagittal; 0/0 | `low_signal:False` | 2384 | 1047 | -1337 |
| acl | Sagittal; 1/1 | `low_signal:False` | 1700 | 4963 | 3263 |

This compact table shows the complete overview banks. All directional rows and source addresses are retained in the [complete row table](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/acl.csv) and [case record](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/acl.json).

### MCL

The two acquisitions write different low-signal words. Those are real named observations; neither word alone means a torn ligament. The displayed positive marker is central rather than a complete medial ligament course. The broader configuration and independent case call must retain their own roles.

![MCL: condition-negative left, diagnosed right, acquired images and named HDC count differences](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v4/named-pairs/mcl-named-pair.png)

**Independent report evidence:**

- Negative: Ligamentos cruzados y colaterales dentro de límites normales.
- Diagnosed: Parti ële scheur proximaal op het mediale collaterale ligament, graad 2.

| Object | View; F/S | Measured row | Negative | Diagnosed | Delta |
|---|---|---|---:|---:|---:|
| mcl | Coronal; 0/0 | `low_signal:False` | 82 | 0 | -82 |
| mcl | Coronal; 0/0 | `low_signal:True` | 0 | 44 | 44 |
| mcl | Coronal; 1/1 | `low_signal:False` | 0 | 10 | 10 |
| mcl | Coronal; 1/1 | `low_signal:True` | 51 | 0 | -51 |

This compact table shows the complete overview banks. All directional rows and source addresses are retained in the [complete row table](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/mcl.csv) and [case record](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/mcl.json).

### Medial Meniscus

The description includes coronal and axial contributions and directional facets. The reports teach the meniscal question. The visible candidate remains a candidate; recognizing the remembered configuration does not require redrawing a perfect meniscus first.

![Medial Meniscus: condition-negative left, diagnosed right, acquired images and named HDC count differences](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v4/named-pairs/medial-meniscus-named-pair.png)

**Independent report evidence:**

- Negative: Menisco medial de morfología y señal
conservada, sin signos de rotura.
- Diagnosed: there is longitudinal vertical tear at the body and posterior horn of the medial meniscus.

| Object | View; F/S | Measured row | Negative | Diagnosed | Delta |
|---|---|---|---:|---:|---:|
| medial_meniscus | Axial; 1/1 | `low_signal:False` | — | 19 | — |
| medial_meniscus | Axial; 1/1 | `low_signal:True` | — | 41 | — |
| medial_meniscus | Coronal; 0/0 | `low_signal:False` | 100 | 0 | -100 |
| medial_meniscus | Coronal; 0/0 | `low_signal:True` | 0 | 67 | 67 |
| medial_meniscus | Coronal; 1/1 | `low_signal:False` | 0 | 54 | 54 |
| medial_meniscus | Coronal; 1/1 | `low_signal:True` | 67 | 7312 | 7245 |

This compact table shows the complete overview banks. All directional rows and source addresses are retained in the [complete row table](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/medial-meniscus.csv) and [case record](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/medial-meniscus.json).

### Lateral Meniscus

The shared coronal bank changes its measured word; other banks are one-sided. Unavailable observations remain unavailable. The picture and the remembered call do not certify every marked pixel as meniscus.

![Lateral Meniscus: condition-negative left, diagnosed right, acquired images and named HDC count differences](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v4/named-pairs/lateral-meniscus-named-pair.png)

**Independent report evidence:**

- Negative: The lateral compartment, the meniscus is not torn and there is no focal chondrosis or chondral injury.
- Diagnosed: Horizontal tear at anterior horn of the lateral meniscus is noted.

| Object | View; F/S | Measured row | Negative | Diagnosed | Delta |
|---|---|---|---:|---:|---:|
| lateral_meniscus | Coronal; 0/0 | `low_signal:True` | — | 356 | — |
| lateral_meniscus | Coronal; 1/1 | `low_signal:False` | 0 | 312 | 312 |
| lateral_meniscus | Coronal; 1/1 | `low_signal:True` | 17460 | 0 | -17460 |

This compact table shows the complete overview banks. All directional rows and source addresses are retained in the [complete row table](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/lateral-meniscus.csv) and [case record](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/lateral-meniscus.json).

### Medial OA

The current femoral and tibial cartilage rows are whole-object descriptions. Medial context belongs to this question, but the same cartilage counts are also reused by the lateral question. Reuse is valid; treating these as an already measured compartment-specific distinction is not.

![Medial OA: condition-negative left, diagnosed right, acquired images and named HDC count differences](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v4/named-pairs/medial-oa-named-pair.png)

**Independent report evidence:**

- Negative: Cartílagos de los compartimentos femorotibiales sin alteraciones.
- Diagnosed: There is diffuse high grade and low grade chondrosis (less than and more than 50% thickness cartilage loss) along weightbaring medial femoral condyle and medial tibial plateau.

| Object | View; F/S | Measured row | Negative | Diagnosed | Delta |
|---|---|---|---:|---:|---:|
| femoral_cartilage | Coronal; 0/0 | `low_signal:False` | 609 | — | — |
| femoral_cartilage | Coronal; 1/1 | `low_signal:False` | 367 | 394 | 27 |
| tibial_cartilage | Coronal; 0/0 | `low_signal:False` | 372 | 184 | -188 |
| tibial_cartilage | Coronal; 1/1 | `low_signal:False` | 241 | 483 | 242 |
| medial_meniscus | Coronal; 0/0 | `low_signal:False` | 100 | — | — |
| medial_meniscus | Coronal; 1/1 | `low_signal:True` | 67 | — | — |

This compact table shows the complete overview banks. All directional rows and source addresses are retained in the [complete row table](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/medial-oa.csv) and [case record](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/medial-oa.json).

### Lateral OA

This pair shares its studies and whole-cartilage counts with medial OA. The questions retain their separate anatomical roles. These are not two independent demonstrations of diagnostic separation.

![Lateral OA: condition-negative left, diagnosed right, acquired images and named HDC count differences](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v4/named-pairs/lateral-oa-named-pair.png)

**Independent report evidence:**

- Negative: Cartílagos de los compartimentos femorotibiales sin alteraciones.
- Diagnosed: There is focal high grade chondrla defectat mid lateral tibial plateau (about 1.2* 1.1 cm).

| Object | View; F/S | Measured row | Negative | Diagnosed | Delta |
|---|---|---|---:|---:|---:|
| femoral_cartilage | Coronal; 0/0 | `low_signal:False` | 609 | — | — |
| femoral_cartilage | Coronal; 1/1 | `low_signal:False` | 367 | 394 | 27 |
| tibial_cartilage | Coronal; 0/0 | `low_signal:False` | 372 | 184 | -188 |
| tibial_cartilage | Coronal; 1/1 | `low_signal:False` | 241 | 483 | 242 |
| lateral_meniscus | Coronal; 0/0 | `low_signal:False` | 89 | — | — |
| lateral_meniscus | Coronal; 1/1 | `low_signal:True` | 61 | — | — |

This compact table shows the complete overview banks. All directional rows and source addresses are retained in the [complete row table](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/lateral-oa.csv) and [case record](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/lateral-oa.json).

### PF OA

The positive report localizes the finding to trochlear cartilage; it does not mark every constituent object diseased. Native support/raw values exist in sibling artifacts, while the chosen product lacks the relevant b1_dark readings. Both current cartilage comparisons are silent. Support membership must not be relabeled as low-signal.

![PF OA: condition-negative left, diagnosed right, acquired images and named HDC count differences](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v4/named-pairs/pf-oa-named-pair.png)

**Independent report evidence:**

- Negative: Eklem kıkırdakları ve kemikler bunların dışında normal.
- Diagnosed: Condropatía focal grado 4 del aspecto inferior de la vertiente medial de la tróclea femoral .

| Object | View; F/S | Measured row | Negative | Diagnosed | Delta |
|---|---|---|---:|---:|---:|
| patellar_cartilage | Sagittal; 1/1 | `low_signal:False` | 107 | — | — |
| trochlear_cartilage | Sagittal; 1/1 | `low_signal:False` | 204 | — | — |

This compact table shows the complete overview banks. All directional rows and source addresses are retained in the [complete row table](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/pf-oa.csv) and [case record](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/pf-oa.json).

### Effusion

The memory subject includes the joint space and recesses, including an inspected region without a distended object. The shared joint-fluid profile is proportional in this comparison, while additional positive-only views/directions are available. Neither missing fluid candidates nor mere fluid presence supplies a negative diagnostic call.

![Effusion: condition-negative left, diagnosed right, acquired images and named HDC count differences](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v4/named-pairs/effusion-named-pair.png)

**Independent report evidence:**

- Negative: No knee effusion is present.
- Diagnosed: Leve derrame articular.

| Object | View; F/S | Measured row | Negative | Diagnosed | Delta |
|---|---|---|---:|---:|---:|
| joint_fluid | Coronal; 0/0 | `low_signal:False` | — | 541 | — |
| joint_fluid | Coronal; 1/1 | `low_signal:False` | 515 | 330 | -185 |
| joint_fluid | Sagittal; 0/0 | `low_signal:False` | — | 216 | — |
| joint_fluid | Sagittal; 1/1 | `low_signal:False` | — | 142 | — |
| anterior_synovial_recess | Sagittal; 0/0 | `low_signal:False` | — | 122 | — |
| anterior_synovial_recess | Sagittal; 1/1 | `low_signal:False` | — | 75 | — |

This compact table shows the complete overview banks. All directional rows and source addresses are retained in the [complete row table](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/effusion.csv) and [case record](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/effusion.json).

### Synovitis

The official positive label/report supplies the synovitis call; the negative is condition-specific. The retained support is a local marker, not a complete lining. The named differences are local observations available to contextual recall.

![Synovitis: condition-negative left, diagnosed right, acquired images and named HDC count differences](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v4/named-pairs/synovitis-named-pair.png)

**Independent report evidence:**

- Negative: Leve derrame articular.
- Diagnosed: Leve a moderado derrame articular con mínima sinovitis.

| Object | View; F/S | Measured row | Negative | Diagnosed | Delta |
|---|---|---|---:|---:|---:|
| synovium | Sagittal; 0/0 | `low_signal:False` | 26 | 1 | -25 |
| synovium | Sagittal; 1/1 | `low_signal:False` | 18 | 6 | -12 |

This compact table shows the complete overview banks. All directional rows and source addresses are retained in the [complete row table](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/synovitis.csv) and [case record](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/synovitis.json).

### Baker's

The acquired positive image supplies conspicuous posterior fluid context alongside its report. The saved bursa content bundle is empty on both sides. There is no named bursa-vector difference to report from this product. That is a missing input to this particular memory cue, not a reason to withdraw the anatomical definition.

![Baker's: condition-negative left, diagnosed right, acquired images and named HDC count differences](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v4/named-pairs/bakers-named-pair.png)

**Independent report evidence:**

- Negative: No Baker's cyst.
- Diagnosed: A 1.5*1.5* 4.5 cm baker's cyst at the posteromedial aspect of left knee.

| Object | View; F/S | Measured row | Negative | Diagnosed | Delta |
|---|---|---|---:|---:|---:|
| bursa | — | No retained measured content | — | — | — |

This compact table shows the complete overview banks. All directional rows and source addresses are retained in the [complete row table](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/bakers.csv) and [case record](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/bakers.json).

### Contusion

An interior coronal fluid-sensitive image is shown as raw diagnostic context after visual inspection of every slice. Its report describes marrow edema. The current compared HDC banks come from different retained sagittal observations; the coronal context image is not being passed off as their encoded source.

![Contusion: condition-negative left, diagnosed right, acquired images and named HDC count differences](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v4/named-pairs/contusion-named-pair.png)

**Independent report evidence:**

- Negative: No hay alteraciones de señal significativas de la médula ósea.
- Diagnosed: Additional small area of bone marrow edema on the medial side of medial femoral condyle without evidence of associated fracture.

| Object | View; F/S | Measured row | Negative | Diagnosed | Delta |
|---|---|---|---:|---:|---:|
| femur | Sagittal; 0/0 | `low_signal:False` | 14415 | 230655 | 216240 |
| tibia | Sagittal; 0/0 | `low_signal:False` | 21134 | 103449 | 82315 |

This compact table shows the complete overview banks. All directional rows and source addresses are retained in the [complete row table](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/contusion.csv) and [case record](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/contusion.json).

### Fracture

This uses the same source study pair as contusion, with a separately sourced fracture call. The raw interior coronal view is context; the same generic bone count comparison cannot be claimed as a separately encoded fracture-continuity distinction.

![Fracture: condition-negative left, diagnosed right, acquired images and named HDC count differences](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/pictures/diagnostic-pairs-20261020/v4/named-pairs/fracture-named-pair.png)

**Independent report evidence:**

- Negative: No hay alteraciones de señal significativas de la médula ósea.
- Diagnosed: Small osteochondral impaction fracture of the lateral corner of lateral femoral condyle.

| Object | View; F/S | Measured row | Negative | Diagnosed | Delta |
|---|---|---|---:|---:|---:|
| femur | Sagittal; 0/0 | `low_signal:False` | 14415 | 230655 | 216240 |
| tibia | Sagittal; 0/0 | `low_signal:False` | 21134 | 103449 | 82315 |

This compact table shows the complete overview banks. All directional rows and source addresses are retained in the [complete row table](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/fracture.csv) and [case record](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/conditions/fracture.json).

## What remains before expanding training

The carrier, individual-case store, signed teaching, role-preserving composition, exact retrieval, cohort selection, evidence persistence and real-command dispatch exist. The remaining work is to connect the useful image descriptions needed by these cases, pair them with compatible input-available cheap descriptions, and exercise the thesis’s warranted recall and independent near-miss teaching. This is not a requirement for perfect masks or a complete numerical atlas of healthy knees. Literature can ground a finding’s meaning; official labels/reports can ground the case’s diagnostic interpretation.

The clinical source supports using anatomical structure, sequence-specific appearance and multi-plane context: [ESSR knee MRI recommendations](https://link.springer.com/article/10.1007/s00330-024-10706-7). Project-specific declarations must preserve the exact measured quantity and its reference meaning; a support mask is not automatically a low-signal reading.

The ordered implementation contracts are in [AI_DIAGNOSTIC_DESIGN §15](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/docs/AI_DIAGNOSTIC_DESIGN.md). The sole live status and worker handoff remain [the current task packet](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/docs/work/current/README.md).

## Reproduction and evidence

- [Named-row inputs, exact facets, source/bundle hashes](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/named-pair-data/renderer-input.json).
- [All 193 row checks, case identities and unchanged-source checks](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/check-result.json).
- [DICOM frame addresses, raw/support hashes, source checks and overrides](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/render-record.json).
- [Raw bone contact sheets and key-plane/source records](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/frame-review/README.md).
- [DICOM geometry audit](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/orientation-audit.json).
- [PF content connection check](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/pf-content-bridge/facts.md).
- [Shared gate result](/Users/rohanvinaik/Projects/Kaggle_Killer/competitions/RSNA_Knee/data/readings/ai-diagnostic-build-20261020/wave-3/final-gate/result.json).

```sh
PYTHONPATH=src .venv/bin/python data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/render_named_pairs.py --differences data/readings/ai-diagnostic-build-20261020/wave-3/named-pair-data/renderer-input.json --frame-overrides data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/frame-overrides.json
PYTHONPATH=src .venv/bin/python data/readings/ai-diagnostic-build-20261020/wave-3/claude-max-renderer/check_named_pairs.py
```

The images/data are local competition-derived artifacts under the ignored data tree. Publishing this Markdown alone does not include those artifacts.
