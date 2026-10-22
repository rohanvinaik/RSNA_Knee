# Hand-defined normal and condition teaching references

The labelled studies also supply the normal corpus: once an anatomical object is correctly
identified, it is a valid normal example when none of that study's positive conditions implicates
it. The official labels supply this meaning; no additional normality annotation is required.
Keep the object's confirmed views and the condition/object relationships. A normal object in an
injured knee is still a useful normal example. The pictures below define starting contrasts;
they are not the only objects eligible to teach.

These are independently source-labeled, visually addressed teaching presentations. The 24 regions are annotations of these images, not rules for locating new knees. Identity and state stay separate. The existing 852-case signed parent is untouched.

This workset uses the production 10 mm and 2 mm writers, exact Hadamard carrier and ordinary case-recall engine. Labels and written meanings are not feature banks. Teaching replay checks the supplied examples, not held-out transfer. Named bank differences are image measurements, not automatically clinical causes.

Clinical reference: [Chien et al., MRI of the knee](https://doi.org/10.5114/pjr.2020.99415). Each case retains the entire independent official report and label row.

[Workset files, reproduction, replay and scope](teaching/README.md).


## ACL — acl

Ligament course in the notch, joining anterior tibial and femoral attachments, anterior to the PCL. Bone identity alone does not establish a ligament.

**Normal reference:** Coherent ligament course.

**Altered reference:** Interrupted or disorganized course.

![ACL](../data/readings/grounded-teaching-20261022/references-r3/acl.png)

**Normal image:** Oblique striated ACL course anterior to the dark curved PCL; report says cruciates normal.

**Diagnosed image:** Disorganized ACL course in the notch; this is the previously independently reviewed teaching support. Report localizes a complete midsubstance rupture.

**Encoding:** distinct_measured_profiles; 187 nonproportional named banks. Teaching replay: absent / present.

[All named differences and actual recall](../data/readings/grounded-teaching-20261022/references-r3/receipt.json)

Representative 2 mm object-associated measurement rows (below/middle/above the scan-local reference; **not** disease labels):

| Reading | Normal presentation | Diagnosed presentation |
|---|---|---|
| local_range | [19, 33, 10] | [35, 11, 5] |
| gradient_row | [26, 3, 33] | [24, 7, 20] |
| gradient_column | [24, 13, 25] | [26, 15, 10] |
| signal_median | [22, 13, 27] | [0, 12, 39] |

## MCL — mcl

Medial femoral-to-tibial collateral band outside the medial joint margin, identified relative to the bones and fibular side.

**Normal reference:** Continuous slim collateral band.

**Altered reference:** Altered band with surrounding injury signal.

![MCL](../data/readings/grounded-teaching-20261022/references-r3/mcl.png)

**Normal image:** Slim dark band along the medial condyle and proximal tibia, opposite the fibula. Official report calls collateral ligaments normal.

**Diagnosed image:** Medial collateral course with local surrounding bright injury signal. Previously reviewed support; report names grade-II proximal partial MCL tear.

**Encoding:** distinct_measured_profiles; 192 nonproportional named banks. Teaching replay: absent / present.

[All named differences and actual recall](../data/readings/grounded-teaching-20261022/references-r3/receipt.json)

Representative 2 mm object-associated measurement rows (below/middle/above the scan-local reference; **not** disease labels):

| Reading | Normal presentation | Diagnosed presentation |
|---|---|---|
| signal_median | [24, 18, 53] | [16, 32, 33] |
| local_range | [60, 31, 4] | [65, 13, 3] |
| gradient_column | [35, 26, 34] | [60, 12, 9] |

## Medial Meniscus — medial_meniscus

Fibrocartilage at the medial femorotibial joint margin; the compartment is established from knee side and fibular side.

**Normal reference:** Preserved meniscal wedge.

**Altered reference:** Cleft, loss or displacement of meniscal tissue.

![Medial Meniscus](../data/readings/grounded-teaching-20261022/references-r3/medial-meniscus.png)

**Normal image:** Dark medial joint-margin wedge between the femur and tibia. Report says preserved morphology and signal without tear.

**Diagnosed image:** Medial meniscal margin is displaced toward the gutter with abnormal surrounding fluid/interface. The report independently establishes tear and displaced/extruded meniscal tissue; this is its presentation, not a traced root tear.

**Encoding:** distinct_measured_profiles; 185 nonproportional named banks. Teaching replay: absent / present.

[All named differences and actual recall](../data/readings/grounded-teaching-20261022/references-r3/receipt.json)

Representative 2 mm object-associated measurement rows (below/middle/above the scan-local reference; **not** disease labels):

| Reading | Normal presentation | Diagnosed presentation |
|---|---|---|
| signal_maximum | [11, 18, 6] | [33, 15, 12] |
| local_range | [11, 11, 13] | [31, 11, 18] |
| gradient_row | [19, 3, 13] | [24, 4, 32] |

## Lateral Meniscus — lateral_meniscus

Meniscal horn between lateral femoral condyle and tibial plateau, with its horn and compartment retained.

**Normal reference:** Preserved meniscal wedge.

**Altered reference:** Cleft, loss or displacement of meniscal tissue.

![Lateral Meniscus](../data/readings/grounded-teaching-20261022/references-r3/lateral-meniscus.png)

**Normal image:** Preserved dark lateral meniscal wedge at the lateral femorotibial margin. The report explicitly says the lateral meniscus is not torn; this replaces the initial anterior-region support, which did not isolate meniscus.

**Diagnosed image:** Irregular, displaced lateral meniscal margin and associated interface, on the fibular side. The independent report names complex degenerative lateral meniscal tearing with extrusion; the contour is not a pixelwise tear boundary.

**Encoding:** distinct_measured_profiles; 177 nonproportional named banks. Teaching replay: absent / present.

[All named differences and actual recall](../data/readings/grounded-teaching-20261022/references-r3/receipt.json)

Representative 2 mm object-associated measurement rows (below/middle/above the scan-local reference; **not** disease labels):

| Reading | Normal presentation | Diagnosed presentation |
|---|---|---|
| signal_maximum | [11, 2, 7] | [21, 24, 10] |
| local_range | [8, 4, 8] | [16, 31, 8] |
| gradient_row | [7, 6, 7] | [20, 7, 28] |

## Medial OA — femoral_cartilage

Medial weight-bearing articular surface and its opposing tibial surface; compartment identity precedes the state question.

**Normal reference:** Preserved articular covering.

**Altered reference:** Loss or irregularity of articular covering.

![Medial OA](../data/readings/grounded-teaching-20261022/references-r3/medial-oa.png)

**Normal image:** Medial articular interface. The report explicitly states no medial focal chondrosis or chondral injury.

**Diagnosed image:** Medial weight-bearing interface with irregular reduced covering and displaced meniscal context. Report establishes medial cartilage loss; the region is scoped to this compartment.

**Encoding:** distinct_measured_profiles; 175 nonproportional named banks. Teaching replay: absent / present.

[All named differences and actual recall](../data/readings/grounded-teaching-20261022/references-r3/receipt.json)

Representative 2 mm object-associated measurement rows (below/middle/above the scan-local reference; **not** disease labels):

| Reading | Normal presentation | Diagnosed presentation |
|---|---|---|
| local_range | [10, 14, 25] | [13, 6, 32] |
| gradient_row | [24, 6, 19] | [28, 1, 22] |
| signal_maximum | [16, 9, 24] | [18, 6, 27] |

## Lateral OA — tibial_cartilage

Lateral tibial articular surface beneath the lateral femoral condyle, not all cartilage from an OA-positive knee.

**Normal reference:** Preserved articular covering.

**Altered reference:** Focal loss or irregularity of covering.

![Lateral OA](../data/readings/grounded-teaching-20261022/references-r3/lateral-oa.png)

**Normal image:** Lateral articular interface with preserved covering; report explicitly states no focal lateral chondrosis or injury.

**Diagnosed image:** Lateral tibial surface and adjacent joint interface; report localizes a high-grade lateral tibial plateau defect. This is the compartment presentation; the exact defect boundary is not claimed.

**Encoding:** distinct_measured_profiles; 188 nonproportional named banks. Teaching replay: absent / present.

[All named differences and actual recall](../data/readings/grounded-teaching-20261022/references-r3/receipt.json)

Representative 2 mm object-associated measurement rows (below/middle/above the scan-local reference; **not** disease labels):

| Reading | Normal presentation | Diagnosed presentation |
|---|---|---|
| local_range | [11, 9, 27] | [19, 18, 5] |
| gradient_row | [22, 9, 16] | [21, 3, 18] |
| signal_maximum | [16, 5, 26] | [29, 6, 7] |

## PF OA — trochlear_cartilage

Opposed patellar and trochlear articular surfaces in the anterior knee.

**Normal reference:** Preserved patellofemoral covering.

**Altered reference:** Thinned or disrupted patellofemoral covering.

![PF OA](../data/readings/grounded-teaching-20261022/references-r3/pf-oa.png)

**Normal image:** Congruent patellofemoral surfaces with covering visible; report explicitly says no chondral lesion.

**Diagnosed image:** Irregular patellofemoral interface beneath the patella. Report independently establishes diffuse patellar/trochlear chondrosis; this is a joint-surface presentation, not a claim every covered pixel is diseased.

**Encoding:** distinct_measured_profiles; 188 nonproportional named banks. Teaching replay: absent / present.

[All named differences and actual recall](../data/readings/grounded-teaching-20261022/references-r3/receipt.json)

Representative 2 mm object-associated measurement rows (below/middle/above the scan-local reference; **not** disease labels):

| Reading | Normal presentation | Diagnosed presentation |
|---|---|---|
| local_range | [64, 9, 12] | [45, 20, 19] |
| gradient_row | [57, 16, 12] | [38, 11, 35] |
| gradient_column | [24, 21, 40] | [29, 14, 41] |

## Effusion — anterior_synovial_recess

Fluid-bearing joint recess bounded by the femur and extensor mechanism; normal fluid is not itself effusion.

**Normal reference:** Nondistended recess.

**Altered reference:** Expanded fluid-filled recess.

![Effusion](../data/readings/grounded-teaching-20261022/references-r3/effusion.png)

**Normal image:** Anterior suprapatellar recess contains a thin fluid cleft; report states no knee effusion. Normal here means condition-negative, not zero fluid.

**Diagnosed image:** Expanded bright suprapatellar fluid pocket; the report independently calls effusion. The support contains the pocket and its limiting interfaces.

**Encoding:** distinct_measured_profiles; 190 nonproportional named banks. Teaching replay: absent / present.

[All named differences and actual recall](../data/readings/grounded-teaching-20261022/references-r3/receipt.json)

Representative 2 mm object-associated measurement rows (below/middle/above the scan-local reference; **not** disease labels):

| Reading | Normal presentation | Diagnosed presentation |
|---|---|---|
| signal_median | [112, 43, 7] | [32, 4, 75] |
| signal_maximum | [147, 8, 7] | [27, 17, 67] |
| gradient_column | [61, 73, 28] | [45, 10, 56] |

## Synovitis — synovium

Synovial lining/recess interface, distinct from fluid alone. Noncontrast regional appearance is interpreted with the independent call.

**Normal reference:** No conspicuously thickened lining in this presentation.

**Altered reference:** Irregular or thickened lining in the recess configuration.

![Synovitis](../data/readings/grounded-teaching-20261022/references-r3/synovitis.png)

**Normal image:** Anterior synovial recess interface with little distension and no conspicuous thickened lining at this address. Official Synovitis=0 supplies the condition call; absence is not inferred merely from absence of effusion.

**Diagnosed image:** Synovial recess/lining margin alongside bright suprapatellar fluid. The report establishes thickened synovial tissue and chronic reactive synovitis. The support is a rough lining-bearing interface, not pure synovium; the first bone-dominated rectangle was withdrawn.

**Encoding:** distinct_measured_profiles; 186 nonproportional named banks. Teaching replay: absent / present.

[All named differences and actual recall](../data/readings/grounded-teaching-20261022/references-r3/receipt.json)

Representative 2 mm object-associated measurement rows (below/middle/above the scan-local reference; **not** disease labels):

| Reading | Normal presentation | Diagnosed presentation |
|---|---|---|
| local_range | [145, 38, 15] | [0, 6, 41] |
| gradient_row | [26, 113, 59] | [23, 6, 18] |
| gradient_column | [58, 96, 44] | [32, 3, 12] |

## Baker's — gastrocnemius_semimembranosus_bursa

Posteromedial gastrocnemius-semimembranosus bursal site, distinguished from vessels and other posterior fluid.

**Normal reference:** Nondistended bursal site.

**Altered reference:** Distended bursal fluid structure.

![Baker's](../data/readings/grounded-teaching-20261022/references-r3/bakers.png)

**Normal image:** Posteromedial bursal-site context without the lobulated fluid expansion shown by the positive. Official Baker label is 0. This is an absence-bearing site, not a mask claiming an expanded bursa exists.

**Diagnosed image:** Conspicuous lobulated fluid-bright posteromedial structure, separate from the vessel course; report explicitly calls a Baker cyst at this site.

**Encoding:** distinct_measured_profiles; 192 nonproportional named banks. Teaching replay: absent / present.

[All named differences and actual recall](../data/readings/grounded-teaching-20261022/references-r3/receipt.json)

Representative 2 mm object-associated measurement rows (below/middle/above the scan-local reference; **not** disease labels):

| Reading | Normal presentation | Diagnosed presentation |
|---|---|---|
| signal_median | [88, 63, 53] | [8, 20, 122] |
| local_range | [135, 38, 31] | [61, 33, 56] |
| gradient_column | [39, 81, 84] | [77, 25, 48] |

## Contusion — femur

Marrow within an established bone; marrow change is a state question, not a different bone identity.

**Normal reference:** Usual marrow appearance.

**Altered reference:** Localized marrow oedema presentation.

![Contusion](../data/readings/grounded-teaching-20261022/references-r3/contusion.png)

**Normal image:** Medial femoral marrow inside the cortex, away from joint fluid. Report states no significant marrow signal alteration.

**Diagnosed image:** Peripheral medial femoral marrow high-signal focus inside the bone. The report separately localizes medial-condyle marrow oedema without associated fracture; do not import the lateral fracture into this site.

**Encoding:** distinct_measured_profiles; 190 nonproportional named banks. Teaching replay: absent / present.

[All named differences and actual recall](../data/readings/grounded-teaching-20261022/references-r3/receipt.json)

Representative 2 mm object-associated measurement rows (below/middle/above the scan-local reference; **not** disease labels):

| Reading | Normal presentation | Diagnosed presentation |
|---|---|---|
| signal_median | [4, 80, 6] | [21, 15, 4] |
| signal_maximum | [80, 6, 4] | [34, 4, 2] |
| local_range | [80, 6, 4] | [36, 2, 2] |

## Fracture — tibia

Tibial articular bone/spine and continuity, with the joint and femur providing context.

**Normal reference:** Preserved bone continuity at the pictured site.

**Altered reference:** Disrupted or displaced bone continuity.

![Fracture](../data/readings/grounded-teaching-20261022/references-r3/fracture.png)

**Normal image:** Intact central tibial plateau/spine interface. Official Fracture=0 and report without marrow alteration teach this condition-negative presentation.

**Diagnosed image:** Abnormal tibial spine/articular interface with displaced/irregular bone structure. Report localizes comminuted tibial spine/plateau fracture; edema alone is not the defining fracture distinction.

**Encoding:** distinct_measured_profiles; 190 nonproportional named banks. Teaching replay: absent / present.

[All named differences and actual recall](../data/readings/grounded-teaching-20261022/references-r3/receipt.json)

Representative 2 mm object-associated measurement rows (below/middle/above the scan-local reference; **not** disease labels):

| Reading | Normal presentation | Diagnosed presentation |
|---|---|---|
| gradient_row | [85, 36, 103] | [43, 33, 84] |
| gradient_column | [79, 85, 60] | [43, 49, 68] |
| local_range | [140, 52, 32] | [77, 63, 20] |
