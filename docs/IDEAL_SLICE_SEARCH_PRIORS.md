# Where the selected slices lie, and what a search prior can honestly save

Light, descriptive analysis of the 58 labelled studies (336 series) after the dimensional-collapse build
(`a118db8`). It uses the build's own selections; it tunes no definition, fits no model and uses no diagnosis
label (the labels only say which studies are in the cohort). It is not a claim that any of these slices is the
anatomically ideal one for all knees. Rohan's criterion governs: «capacity to recognize ... correct in the
general case, not perfect or complete».

**2026-10-17:** Rohan's later direction, which this document describes as queued, is the relative position map,
NOT offsets tabulated from the studies: one 3D map of the whole knee, every object against every other object, from
anatomy and physiology («I told you to base this on knee anatomy, NOT on statistics»). Its understanding:
`docs/RELATIVE_POSITION_MAP.md` §0. The tables here describe the pipeline's own selections; they are not the map.

**Historical cohort analysis only.** The current map is one 3D all-pairs representation grounded in anatomy and
physiology. Each object's position is constrained by three independently selected key planes, one per anatomical
orientation, in shared physical coordinates; those planes jointly establish position, not a centroid from one
section. Sequences do not get separate anatomy maps. The 58 studies measure pair-vector range and standard
deviation only. The statistics below remain observations of earlier pipeline selections, not current search
directives or the source of the ideal.

Evidence (ignored `data/`, never staged): tables and stats in `data/readings/collapse-20261016/search-priors/`,
plots in `data/pictures/collapse-20261016/search-priors/`, the one cohort run they come from in
`.../search-priors/cohort-run/` (drawing off, 4 workers, frozen source `a118db8`, 58 studies, 6 min 41 s).
Rebuild: `.venv/bin/python scripts/slice_positions.py --run <interiors dir> --main-run <main dir> --out <dir>`
(`scripts/slice_positions.py`, tested by `tests/test_slice_positions.py`); the stats, plots, leave-one-out
checks and candidate table are the small dev scripts in `.../search-priors/analysis/`.

## Coordinate convention

Every position is physical and normalized, from the series' saved tile centres (`squint_centres_lps`), never
from a raw index. A slice's place is the mean of its tiles' centres; the stack runs along the LPS axis its
mean step points along (x toward the patient's left, y toward the posterior, z toward the head); `q_mm` is the
distance from the stack's lowest place along it; `t = q / extent`, 0 to 1. A reversed stack gives the same `t`
(136 of 336 series are stored reversed: all 136 sagittals, and no coronal or axial series that has an observation). Spacing was equal in
every stack here (largest gap ratio 1.0004), but `t` is made from the actual places, so unequal spacing would be
carried (tested). Sagittal series also get `t_side`, 0 lateral to 1 medial, from the header's knee (a right
knee's medial side is toward the patient's left); **only 59 of the 136 sagittal series name a knee**, so the
sagittal medial/lateral statistics rest on those, and the others keep their patient-axis position and the
reason `header_names_no_knee`. Axial rows also keep millimetres from the tibia's top and the femur's lowest
place where a posterior trace kept them. The fraction by index is kept beside for comparison:
`index-vs-physical-sagittal.png` shows every sagittal selection on one of the two diagonals (right/left knee,
reversed stack), so a raw index would have mixed lateral and medial. Unknowns are None with a reason, never 0.

## What is in the table

`observation-table.csv/.json`: 7,960 rows, one per observation of every object in every study (2,074 native
resolved, 884 laid, 2,078 native readings, 2,924 projected targets), each with series, view, knee, native
slice(s), stack length, physical and normalized position, provenance, kind, code, pixel count, **role** (how
the slice came to be the one) and where its places are saved. Roles: `middle_bootstrap` (fixed middle),
`own_slice_rule` (a part's own landmark rule), `profile_pointed_plane` (a cheap profile pointed, the existing
rule named), `profile_run` (a cheap profile's run; position is its midpoint), `continuation_trace`,
`pointed_plane_reading` (asked, named nothing: an unknown), `context_middle_naming` (air, skin, subcutaneous
fat, muscle, joint, unsided meniscus: **no best slice is claimed**), `projected_target` (a place to ask, never
an observation). Several planes of one study stay separate rows. `object-coverage.csv`: every object of
`OBJECTS_AND_CONDITIONS.md` and every one the run names (45) by every one of the 58 studies: native resolved,
laid only, reading only, projected target only, refused (the rule's own code) or no record: an explicit unknown
each time, none omitted. Bone marrow is the named bone's interior: it has no recognizer, its representative is
the femur's and tibia's (patella's, fibula's) own observations (55 of 58 studies have one; 3 do not).
`stats-table.csv/.json`: per object, role, provenance and view, studies and observations, those without a
coordinate (and why), mean, sample SD (None for one), median, IQR, range, a 10-bin histogram, all both by
observation and by study (one value per study, since a study's planes are not independent studies).

## Findings

- **The fixed middle clusters by construction.** All 577 `middle_bootstrap` observations lie at `t` 0.47 to
  0.53 (the middle of the stack, `floor(n/2)`). That is the existing default, not evidence that anatomy was
  independently located there, and it already searches nothing, so there is nothing to save
  (`fixed-middle-default.png`).
- **Own-slice landmark rules** (from the by-study statistics; `own-slice-rule.png`): the fibula's coronal slice
  (T1) `t` 0.62, sample SD 0.08 (9 studies, 11 observations, range 0.54 to 0.76; its 2 sagittal observations
  are too few for a spread); the semimembranosus and its companions' axial slice (the top of the tibia) `t` 0.33,
  SD 0.11 (10 studies, range 0.09 to 0.51; in millimetres from the tibia's top median -12 mm, range -131 to +0.5,
  with a heavy tail); the ACL is the middle's neighbour by rule (0.46, 4 studies); the retinacula's axial slice
  about 0.7 (3 to 4 studies: too few for a spread). The gastrocnemius-semimembranosus bursa shares the
  semimembranosus's slice (6 studies).
- **Profile-pointed planes** (`profile-pointed-planes.png`, `candidate-start-spread.json`, 15 rows with 5 or
  more studies): tibia, coronal 0.55 (SD 0.08, 24 studies / 46 planes) and sagittal 0.48 (0.08, 13 / 71); femur,
  coronal 0.51 (0.17, 25 / 54), sagittal 0.40 (0.22, 12 / 41); patella, Hoffa's and the suprapatellar pads, sagittal
  about 0.44 (0.15, 12 studies); cartilage, coronal 0.55 (0.05, 5 studies). The bones are not one hump: the
  profile's runs and the named planes spread over the stack (condyles, shaft, other marrow-like tissue;
  `bones-multimodal.png`; the pooled run peaks have SD 0.29). The candidates are descriptions with their sample
  counts, **not applied to any search** (below). 12 to 25 studies per group is a small sample.
- **Continuations** (`continuation_trace`, 84 pointers) are tube readings from projected places: semimembranosus
  about 0.8 on sagittal and coronal series (7 to 10 studies). They describe where a cheap ridge was read, not
  the tendon's course.
- Unresolved and missing are counted, not hidden: for example the biceps tendon is native-resolved in 1 study,
  the popliteus tendon 1, the LCL 1, the artery and vein 2, the sartorius 2, gracilis 2 (the rest refused by the
  rule's own code or no record); the fibula 10, the bursa 6, the semimembranosus 10.

## What a search prior can save: measured, and mostly nothing

The collapse already makes search cheap: a whole-stack squint and per-slice cheap profiles point, and the
detailed lens reads only the pointed planes. Measured with cProfile on six random studies (drawing off): the
whole-stack search loops are the bones' cheap profile 10.8% of the run, the joint's 2.9%, the patella's
corridor 2.0%, the semimembranosus tibial-top loop 1.7%, the fibula's 0.7%; the lens on pointed planes 20.7%
(bones' pointed planes are about half of the cohort's 1,461 lens reads); the squint 11.8% and saving the
arrays 9.6% are not searches. So even a perfect prior is bounded by roughly 15% of the run, and:

| consumer | what a prior would restrict | measured (in-sample table, leave-one-study-out check) | applied |
|---|---|---|---|
| fixed middle (the bootstrap and the context) | nothing: no search | none to save | n/a |
| bones' cheap profile (`bone_profile`) | the slices it visits | its runs are spread (pooled peak SD 0.29): a window of mean ±1.5 SD would skip 10% of the visits and lose 38 of 402 runs (9%); ±2 SD skips 1.4% and loses 1; ±2.5 SD skips nothing | **no: no saving without losing runs** |
| bones' pointed-plane lens reads | which pointed planes are read | with the fallback "no identified plane in the window, read all": 6% of lens reads saved at ±2 SD, 0 identified planes lost (82 series, 166 identified planes), because 56 of 82 series have no identified plane inside the window and so fall back to reading every pointed plane; without a fallback 41% of the non-identified planes would be skipped at ±2 SD but 10 of 166 identified planes (6%; 24 or 14% at ±1.5 SD) would be lost: those are the planes the joint, cartilage and menisci families use | **no: 6% of one family's lens reads is under 1% of the run; the larger saving loses useful planes** |
| semimembranosus tibial-top loop, fibula, joint, patella and recess profiles | their cheap loops | each is 0.7 to 2.9% of the run in total; the joint is already limited to slices where both bones are identified (5,965 slices skipped over the cohort) | no: nothing to gain |
| ACL, LCL, biceps, retinacula, posterior family | none search by slice position: a rule or landmark picks the slice | none | n/a |

A prior that only reorders a loop which still reads every slice saves nothing, and none of these loops can drop
reads without losing planes the build already uses. So **no absolute start/spread is wired into any consumer**: the
tables are descriptions, with their sample counts and convention, and any later prior is a separate intentional
change measured against this baseline (leave-one-out results: `loso-bone-windows.json`,
`loso-bone-pointed-planes.json`).

This tested only **absolute** windows, a fixed fraction of the stack. It does not implement the current map, which
takes precedence; this analysis is historical evidence, not queued work: «Knee anatomy is physically linked. Get the
one that is cheapest to resolve with the squint system ..., Get its "key slice", use that as a normalizer, get
the statistical slice range and position estimation *relative* to the obvious elements, to make the hard
compute ... sanely targeted where they likely are». A dedicated builder was assigned that earlier task; this status
is superseded. The following saved fields are historical evidence. What already exists for it, in
every middle record the run saves: each bone's cheap profile through the whole stack (`a3_<bone>_profile_*`:
status, supported marrow area per slice, runs), its pointed planes and their places along the middle slice's
normal in millimetres (`a3_<bone>_pointed_position_mm`, `a3_<bone>_depth_offsets_mm` for every slice,
`a3_<bone>_pointer_run_envelope_mm`), its extent along the leg (`a3_<bone>_leg_extent_mm`; the femur's lower end
and the tibia's top in `landmarks`), `a3_posterior_context_up_mm` (tibia top, femur lowest) and the sided
`squint_centres_lps`. Offsets in millimetres from a bone's declared key plane, by view and side, can be tabulated
from these without new reads; a key plane needs one declared anatomical meaning (the table's `offset_from_tibia_top_mm`
is only the first such column, for axial series), and a target projected from another plane is not an independent
observed position. The roles `profile_run` (support through a band) and `continuation_trace` (a ridge read from a
projected cross-section) are context, not evidence of an independent ideal native plane; the start/spread
candidates above use only native resolved selections.

## The one speed-up made: exact, in the same consumer

The profile showed `thinned` (the carried places put on a lattice for the bones' and patella's cheap profiles,
`np.unique(axis=0)`) at 9.7% of the six-study run, called inside those profiles. It now sorts one integer per
cell, producing exactly the same cells in the same order (`tests/test_thinned_places.py`; a lattice too wide
for one integer falls back to the rows). Measured: `thinned` 8.1 and 9.3 s to 0.75 and 0.80 s in two back-to-back
A/B runs of the six studies (end to end 86.5 to 83.8 s and 95.6 to 92.4 s: about 3%, inside the run-to-run noise
of the machine, which moved totals by 10%); all 336 interiors and all main records of the 58 studies are the
same by decisions, silences and array digests (`scripts/compare_receipts.py`: `cmp-cohort-*.txt`). This is a pure
implementation optimization; it is not a prior.

## Limits

58 studies, and only some have each view: 5 to 40 studies per group that has a spread, fewer for most objects, so means and SDs
are shown only with their counts and no spread for a group of one. Many objects are native-resolved in few
studies (the rules are competent once, not complete). Roles that are profile-pointed are the build's selections,
not a universal optimum. Position is physical `t` along the stack's axis; it says nothing of the object's
extent. Sagittal side-normalized statistics rest on the 59 series whose header names the knee.
