# The anatomical reference used by the relative map

Built 2026-10-17 under Rohan's instruction, «Fix the documentation, then build please».
The governing mechanism remains `RELATIVE_POSITION_MAP.md` §0 and §8.8: three key planes construct
each study object's position; the anatomy map guides searches from the objects already found.

## Where the reference comes from

The numerical teaching reference is the [SPL MRI-based Atlas of the Knee](https://www.openanatomy.org/atlas-pages/atlas-spl-knee.html),
Richolt, Jakab and Kikinis (2015), Brigham and Women's Hospital / Harvard Medical School.
It supplies its original MRI, authoritative label maps and models. This project uses selected label-plane
coordinates and extents, not a recognizer trained on its images. It is one reference specimen, not a
population distribution or a claim that every knee has its exact proportions.

The builder inspected all six sheets of native reference sections with MRI sampled at the labels' actual
physical coordinates. The MRI and label grids differ; equal array indices would not overlay them correctly.
The retained development evidence is
`data/readings/collapse-20261017/three-plane-map/anatomy-sources/`:

- `spl-knee-atlas-evidence/pages/`: three section views per object and complete area profiles.
- `reference-selection-facts.json` and `.md`: selected planes, all tied maxima, actual areas, physical bounds,
  label names and source checksums. Every selected plane intersects its label.
- `spl-knee-2016-09.zip` and its extraction: original source, including licence notice.

Source archive SHA-256: `2f61002f42843910eada3877adf4229ef845bf87cc1e422b719c930dfadc5f6a`.
Authoritative `seg.nrrd` SHA-256: `7b1eba4d06a24d8d769fe0342bf57042d6a6d3afb67da04f2749f62007670091`.

The compact production derivative is `src/knee/collapse/_atlas_reference.py`; it contains no competition
study values. Attribution and the complete licence are preserved in `THIRD_PARTY_LICENSES/SPL_KNEE_ATLAS.txt`.
These selections are this project's modified derivative, not a claim made by the atlas authors.

## The reference-plane choices

These are the builder's choices for this first reference, justified by the visible anatomy. They do not
create a universal maximum-area recognizer for all objects.

- Bones: the large sections expose their enclosed bodies, condyles, plateau, fibular head and patella.
  The sagittal, coronal and axial planes are selected separately. The patella's sagittal plane is the
  explicitly chosen index 282 from the two equal maxima 277 and 282. That is a documented reference choice;
  an automatic study selector still retains a genuine unresolved tie.
- Menisci: longitudinal wedge/body sections and axial C/ring sections. The two sided objects keep separate
  reference planes. The unsided class uses the union of both atlas labels.
- Cartilage: the visible articular layer in three sections; the tibial class uses the two labelled tibial
  surfaces together. The shared contiguous plateau for lateral tibial cartilage uses its central native plane.
- Cruciate and collateral ligaments, patellar tendon, biceps tendon, popliteus tendon, iliotibial tract,
  gracilis and Hoffa's pad: the sections display their body or course. The tract label covers a proximal
  portion; the reference does not assert its distal insertion.
- Gastrocnemius heads and sartorius: longitudinal body sections, with the axial section at the femur's
  condylar plane (atlas k68). A cropped distal calf or proximal thigh maximum does not define knee level.
- Popliteal artery and vein: longitudinal course sections and the same axial condylar plane, exposing their
  separate lumens at knee level. The vein's sagittal plane is explicitly index 302 from two equal maxima.
- Semitendinosus tendon: longitudinal body sections and the proximal-tibial axial plane (k30), rather than
  a thigh-level maximum. The atlas's semitendinosus muscle is a separate structure.

These 25 sites retain their three plane addresses and labels. Their coordinates are the intersection of those
planes, never the centroid of any section. The frame is medial, posterior, superior in millimetres. The specimen's
fibula lies to the left of its tibia in LPS coordinates, identifying a left knee by anatomy; medial therefore
negates its LPS-left coordinate. A study's own knee side converts the common reference into its patient frame.

## Explicit constructions where the atlas has no separate label

`src/knee/collapse/anatomy_map.py` records 14 further first expectations, each with its relation and source.
These are authored geometric guides from the sourced anatomy in `OBJECTS_AND_CONDITIONS.md` §4. Midpoints are
simple constructions between anatomical neighbours, not published measurements or observed study key planes.

| object | initial reference construction |
|---|---|
| Joint | Midway between the two meniscal reference-plane positions, between condyles and plateau. |
| Joint fluid, synovium, capsule | The joint reference supplies a first location for its contents, lining and sleeve; it does not supply a membrane boundary. |
| Anterior synovial recess and the grouped recess class | Between patella and femur, at patellar level. |
| Quadriceps tendon | The superior patellar attachment plane. |
| Combined suprapatellar fat | Above patella, between quadriceps tendon and femur. |
| Quadriceps and prefemoral fat pads | Respectively anterior and posterior to the intervening suprapatellar reference. |
| Semimembranosus tendon | Posteromedial tibial top, just distal to joint line (LP-MED); reference planes from the medial meniscus's medial/posterior extent and inferior plane. The atlas's semimembranosus muscle is not substituted. |
| Gastrocnemius–semimembranosus bursa | Between the medial head and that tendon (R-BAKER, LP-MED); collapse or lack of visible fluid is not diagnosed by the reference. |
| Medial and lateral retinacula | Between the corresponding patellar side and femoral condyle, at patellar level. |

These guides can overreach or predict an imperfect first slice. The native search refines them and broadens
when they fail. They never replace the anatomical recognition rules or move an observed object to fit the map.

The reference-image review corrected an interstitial construction: the recess and upper pads must be between
the **facing surfaces**, rather than between the bones' internal reference points. The atlas label boundaries at
i282/k80 put the posterior patellar face at P=−25.65396818 mm and anterior femoral face at P=−20.38450445 mm.
The recess's first posterior plane lies between them. Above patella, the femur's front surfaces at S43 and S44 mm
bound its interpolated front at the superior patellar reference; both pad guides remain anterior to that cortex,
on opposite sides of the intervening recess. These are retained source measurements in
`ANTERIOR_CONTACTS_LPS_MM`, with complete cuts, neighbour labels and a reproducible measurement script in
`anatomy-sources/reference-pictures/anterior-surface-measurements.*`. A regression checks the surface ordering.

## Whole map and the remaining gaps

The catalogue has 43 semantic object slots: the 42 anatomical `OBJECT_CODES` plus the receipt's grouped `recess`.
There are 39 reference positions (25 selected atlas sites and 14 constructions). Air, skin, generic muscle and
subcutaneous fat are explicit `reference_not_defined` sites: a unique key-plane reference for these diffuse field
classes has not been authored. They remain in the catalogue and pair queries; missing does not become zero.

Every ordered pair is obtained from the same reference positions, bones included. Reversing a pair negates its
vector; composing through any intermediate object gives the same vector. No separate map exists for a view or
sequence. Millimetre vectors and search extents can be uniformly scaled by the study's observed femoral
mediolateral breadth relative to the reference breadth (81.53801779 mm, including voxel support). An unknown study
scale keeps reference millimetres explicitly; it is not silently treated as a measured individual scale.

The reference's searchable extent is a location allowance, not a segmentation mask. Native study positions and
their three selected planes are separate from reference sites and predictions. Only actual complete study
positions may supply observed pair vectors. Partial positions retain their known planes.

The 58 competition studies have not supplied any reference centre, midpoint or offset. Their contribution remains
the measured range and standard deviation of actual pair vectors; unknown pairs must retain their coverage and
missingness. A reference catalogue alone does not establish automatic production key-plane selection or that
cohort measurement: those require the integrated real run and inspected pictures.
