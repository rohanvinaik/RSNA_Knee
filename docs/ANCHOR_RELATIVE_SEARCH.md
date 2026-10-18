# Anatomical reference first, then the patella: what was built and what it found

**Framing superseded, 2026-10-17.** This document records a statistical framing: one bone's key slice as the
reference, and cohort windows of where other parts lie against it (the patella's quartiles; the joint's ranges,
found empty). Rohan: «It's a reasoning and symbolic  approach, not statistical. [...] Not "bone then patella".»
The mechanism is the relative position map, whose understanding is `docs/RELATIVE_POSITION_MAP.md` §0: one 3D map
of the whole knee, every object against every other object as a 3D vector from anatomy and physiology, the 58
studies giving only each pair's range and standard deviation, the map a guide where each object's key slice is
looked for. Still valid from here: the bone's key plane (an anchor's key slice, `select_reference`), physical
coordinates with no slice-index arithmetic, and the measured work. The windows below are what one statistical link
gives; they are not the map.

Rohan's direction (2026-10-16): «Knee anatomy is physically linked. Get the one that is cheapest to resolve with the squint system
(I imagine the tibia/femur?), Get its "key slice", use that as a normalizer, get the statistical slice range and position estimation
*relative* to the obvious elements, to make the hard compute, the expensive process, sanely targeted where they likely are». Accepted
explanation: recognise one easy part cheaply, pick the plane that shows it clearly, use that resolved anatomy as the study's reference,
measure across the labelled studies where the other objects' useful slices lie relative to it, and for a new study read the finer
measurements there first, broadening when the expected neighbourhood does not resolve the part. Criterion unchanged: the capacity to
recognise, not completeness. The statistics point; the anatomical definitions establish what is there; nothing here changes a
definition or a threshold of one, and no diagnosis label is used.

**Historical experiment record only.** The current map is one 3D all-pairs representation of the whole knee,
grounded in anatomy and physiology in shared physical coordinates. Each object's position is constrained by three
independently selected key planes, one in each anatomical orientation; those planes jointly establish position,
not a centroid from one section. Sequences do not get separate anatomy maps. The 58 studies measure pair-vector
range and standard deviation only. The statistical windows, consumers and expansion plan recorded below are not
current directives. The valid key-plane, physical-coordinate, lens and measured-work evidence remains historical
input where useful.

## What this document replaces

The first attempt (`child-anchor-relative-build`) took the median and the interval of the middle-slice bone point clouds already
collected, along each series' normal, and bounded the bones' search with 20 mm beyond them. That is not the mechanism Rohan described:
a cloud median is not a plane that shows a bone, its in-plane positions were ignored, and a fixed margin is an envelope, not a measured
relation. It saved about 4% of the bones' cheap readings. It is removed (`anchor_of`, `anchor_window`, `anchor_visits`,
`ANCHOR_MARGIN_MM`, `scripts/anchor_offsets.py`, `tests/test_anchor_relative.py`); what stays from before: the exact `thinned()` lattice
and `scripts/slice_positions.py`, `merge_profiles` (now the patella's broadening). Its evidence stays in
`data/readings/collapse-20261016/search-priors/anchor-relative/` as a record of that experiment.

## The reference (`select_reference`, `knee.collapse.reference`)

The femur and the tibia are already named on the middle slices (the bootstrap), which supplies which bone, its marrow light and its
carried places. The reference answers where along the stack a bone shows clearly, from the cheap profile alone
(`bone_profile_of`: the squint's tiles and a finer block reading only where they cannot say, one supported marrow-body area per slice,
made once and handed to the bones' own reading):

- Key plane, in plain words: the slice on which the bone's marrow body, inside the corridor of the bone already known, is the largest
  supported body the whole depth holds, **named as that bone by the lens** (`bone_plane_read`: the established carried-bone rule).
  One existing measurement, no weighted score. Not a centroid.
- Looked for on the first series without fat suppression (sagittal first, since its depth axis is the one the patella search runs along;
  then coronal), over both bones. The planes the profile points to (each run's maximum) are asked first, strongest first; only where none
  is named as the bone, every other supported slice, strongest first (a territory can refuse a plane its neighbour is named on). Equal
  areas are one group and a tie is never broken; every tied slice is asked and every named one kept. A slice not read, unreadable or cut
  is no candidate (unknown, never empty); the slices the profile did not point to are never read in detail.
- Kept: series, view, bone, key slice(s), supported area, why, every plane asked with its outcome, the resolved bone's places in the
  scanner's millimetres (`a3_reference_support_lps`), the plane's origin, normal and thickness, in the series' record `reference` and
  `a3_reference_*`, and handed to the consumer. Or why there is none (`no_confirmed_key_plane`, no series without fat suppression).

## Coordinates: no raw index subtraction, no plane pretending to be a position

A key plane supplies its **depth**, the place along its own normal; the resolved bone's places on it supply the **in-plane** positions.
The reference's place along a target series' normal is the mean of its support's places along that normal (`reference_position`): for a
parallel plane the support lies in the plane and this is the plane's depth (kind `depth`); for a plane across the target's axis it
spreads along it and is the bone's own landmark (kind `in_plane`). Offsets are signed by physical direction (`offset_sign`: toward the
patient's left, or medially where a sagittal header names the knee; unknown knee stays unknown), so a reversed stack, unequal spacing
and the other knee give the same offset (`tests/test_reference.py`).

## The cohort: where the patella lies relative to the reference

`scripts/reference_offsets.py`; tables in `data/readings/collapse-20261016/search-priors/anatomical-reference-first/`
(`reference-table`, `offset-table`, `reference-accounting`, `reference-stats`, all 58 studies accounted).
Source: the baseline cohort run (`cohort-run-final`, 58 studies, 336 series) for the patella's native-resolved sections (transfers,
projected targets and continuation pointers are not observations) and a production run of the new code (`cohort-window`) for each study's
reference, computed live, so a widened plane's native confirmation was computed and not invented. Derived from the baseline's saved
profiles and outcomes alone, the reference is the same in 49 studies, different in 5 (a widened plane was never saved there) and
unconfirmed in 4 (`reference-stats.json`).

- References: 54 of 58 studies (49 on a sagittal series: 25 femur, 24 tibia; 5 on a coronal one: 3 femur, 2 tibia); 26 confirmed at the
  first group asked, 28 asked 2 to 24 groups; no confirmed key plane in 4 studies. No reference is a tie (3 tied groups were asked among the widened planes, in 3 studies, and none was named; they are kept in the table).
- Patella native-resolved sections against the reference, millimetres along the stack's normal, toward the patient's left:

| | n | mean | sample SD | median | quartiles | range |
|---|---|---|---|---|---|---|
| representatives (largest section per series), reference kind depth | 39 series, 35 studies | -1.3 | 19.4 | 0.0 | -13.1 to 5.2 | -39.6 to 54.0 |
| all sections, depth | 71 sections, 39 series | 0.4 | 17.6 | 0.0 | -9.9 to 8.9 | -39.6 to 54.0 |
| representatives, medial (header names the knee), depth | 17 | 0.9 | 23.4 | -0.03 | -16.5 to 11.2 | -39.6 to 54.0 |
| representatives, reference a landmark within the plane (kind in_plane) | 5 series, 4 studies | -25.0 | 29.0 | -32.9 | -50.4 to 3.0 | -52.9 to 8.1 |

  Of the 58 studies: 44 fat-suppressed sagittal series measured (39 studies), 15 with no native-resolved patella section, 4 studies with
  no reference. Offsets are not tight (SD about 20 mm against a stack about 100 mm wide), so a centre-and-SD start would say little; the
  usable quantity is the central half. Out of sample (leave one study out) the central half held the series' representative in 19 of 39
  and covered 19% of its slices. The medial convention is no narrower, so it is not wired; the in-plane kind has too few series to
  point anywhere.
- Other objects were not tabulated: this build's deliverable is the first consumer.

## Historical consumer: the patella searched in a statistical window (`read_patella`)

`PATELLA_FROM_REFERENCE_MM[("depth", "left")] = (-13.1, 5.3)` (the quartiles of the representatives' offsets) is read by
`patella_neighbourhood` before the patella's profile is made: which slices of the fat-suppressed series lie within that range of the
reference's place along its normal, by the scanner's millimetres; the middle slice is always among them. Then, one coherent path through
the existing rules (`patella_corridor`, `bone_profile`, `patella_plane`, `twin_reading`, the tendons and pads on the twin, unchanged):

1. the cheap profile over the window only (the rest `not_read`: unknown, never empty);
2. a run whose strongest slice lies at the edge of what was read is walked on, a slice at a time, to where it peaks, so the plane asked
   is the run's own representative and not the window's edge;
3. runs are asked at their maxima (every tie) strongest first, until one names the patella: the representative question is answered and
   the other runs stay pointers (`not_read_natively`), as do the slices never visited;
4. only if no run names it, the rest of the depth is read (`merge_profiles`) and asked the same way: the broad fallback, in which no slice's cheap
   profile is read twice and a plane already read is not read again; beyond what the old search read it can add only the plane of a run the
   window cut whose true maximum lay beyond the window.

An unknown anywhere gives no window and the whole depth, strongest run first: no reference, a reference that is a landmark within the
plane, an axis the offsets were not measured on, unsound slice places. The search is recorded (`patella.search`, `a3_patella_search_*`):
the reference series, key slices, kind and place, the range and sign used, slices visited and never visited, planes asked, why it stopped.
Downstream the tendons, pads and recess family read the planes it names exactly as before.

## Measured work (58 labelled studies, 336 series, drawing off, 4 workers; baseline `cohort-run-final`)

| ledger | baseline | now |
|---|---|---|
| patella cheap profile slices | 1,899 | 1,243 (-34.5%) |
| patella lens readings | 111 | 67 (-39.6%) |
| recess family cheap slices / lens readings (reads the patella's planes) | 394 / 54 | 262 / 40 |
| every family's cheap profile slices | 10,977 | 10,189 (-7.2%) |
| lens readings made (`lens`) | 1,461 | 1,493 (+2.2%) |
| fields made | 786 | 727 (-7.5%) |

The reference costs: 282 planes asked, 249 lens readings, of which the bones' own reading reuses most (its own lens readings fall from
702 to 547) but, derived from the totals, about 90 more lens readings are made than the old path made (the widening to supported slices beside a
plane the lens refuses), which is why lens readings overall rise by 32 although the patella and the recess save 58. Of 50 series searched in a window, 20 were named inside
it and 30 broadened; 10 had no window (8 reference a landmark in the plane, 2 no reference). The proof (`...10095687...`): patella
profile slices 36 to 9, lens readings made 37 to 34, fields 30 to 27, the same patella plane (21, 2,676 pixels) with its tendon, Hoffa's
pad and the suprapatellar fat; the bursa study (`...13335129...`): reference on the coronal femur slice 14, no window (landmark), work
unchanged, bursa still `identified`. Time, six studies under cProfile (`profile-after/six.prof` against `profile-six/six.prof`), the
machine loaded (load average about 14; the unchanged `measure` stage ran 38% slower than in the earlier profile): 80.5 s then, 101.6 s
now raw; normalised by the unchanged stage 3.39 then and 3.09 now (-8.8%): the patella phase -40%, the bones plus the reference +6.5%.
A claimed saving beyond that is not made.

## What changed, honestly

- All 58 studies' middle-slice decisions, the bones, the joint and the fibula records are identical; 239 of 336 records differ in the
  reference, the patella's and the recess family's records and the observations that read them. Of the 45 series with a native patella
  section both before and after, the representative is the same slice in 32 and at least half the baseline's largest section in 80%; 9
  are smaller (the window did not hold the true peak and the middle slice's own naming answered). Three series that were `unresolved`
  are now `identified`; none lost. One patellar-retinacula record was lost (study `...18305500`: its old patella centre came from
  sections that included 37,000-pixel over-reaches of the patella rule; fewer sections move the centre and the retinacula abstain).
  Fewer patella sections are read per series (the rest are pointers), so extent and pole readings rest on fewer.
- **The reference is weakest where it was widened.** 26 of the 54 references were named on the first plane asked; 28 needed the next
  planes because the lens's carried-bone rule refuses the strongest ones (`territory_holding_most`, `territory_is_mostly_not_marrow`:
  the same refusals the bones' own pointed planes meet). Twenty of the 54 references are the series' own middle slice (16 of the 28
  widened: the bootstrap's naming is the plane the rule does accept), so for them the reference adds no plane the run did not have.
  One widened case was inspected (study `...83976756`, sagittal femur, key slice 12): the lens named a region of the thigh's soft tissue
  there, since on a series where fat and marrow share a light the carried femur's footprint can land on soft tissue off the bone, an
  over-reach of the existing rule that also shows in the baseline; the key plane's depth is still close to the strongest peak
  (slice 11). The offsets of the widened references are tighter (quartiles -6.6 to 1.2 mm, n 20) than those named first (-16.9 to 6.3,
  n 19), probably for that reason (`offsets-by-reference-confidence.json`, `reference-at-middle-slice.json`); the window uses all 39.
  A reference named on the first plane asked and not on the middle slice is the clean case (22 of 54).
- Vulture (advisory): only the contract fields it listed before; none from this build. ty clean. `Reference.origin_lps`, `normal`,
  `knee`, `reason`, `area_mm2`, `candidates` and the view are kept (record and arrays) and read by no stage; the patella reads
  `support_lps`, `thickness_mm`, `series_uid`, `bone` and `slices`.
- The range is measured on the same 58 studies; the leave-one-out figures above are the out-of-sample statement.

## Historical remaining-expansion proposal

Other families read relative to the same reference (joint and meniscal planes, the fibula's corridor, the recess, the posterior
family), once each has its own cohort range; the bones' own pointed planes could be asked only near the reference; the coronal
reference needs more series before its in-plane landmark points anywhere; other-axis consumers (axial) have no offsets yet.

## Second consumer: the joint family (`read_joint`, 2026-10-17)

Scope: the sided menisci, femoral/tibial cartilage and the PCL/ACL/MCL relations read through `name_the_joint`, with every existing
rule, gate and observation provenance unchanged. Evidence: `data/readings/collapse-20261016/search-priors/reference-joint-first/`
(`scripts/joint_reference_offsets.py`, `scripts/joint_work_counts.py`).

**What was measured, and the honest result.** The joint family is already narrow in the baseline: it is profiled only where the bones'
family identified both bones, so 223 series read 798 cheap block readings and 162 non-middle detailed planes (0.7 per series).
Native-resolved joint sections on profile-selected planes are sparse (2-6 series per object/view/sequence); nearly every larger
population is the bootstrap middle slice, a fixed place that is not evidence of where a part is best seen, so the tables keep roles apart
(`bootstrap`, `own_slice`, `profile_resolved`, `profile_reading`, `cruciate_reading`) and nothing is pooled. The candidate-pointer population
(each quantity's strongest non-middle run maximum, baseline, independent of any reference-limited result) is usable only on coronal series
(11-23 series). There the central half held the pointed plane 36-44% of the time over windows covering 33-57% of the slices read: no
lift over its own coverage. A coronal in-plane landmark (the sagittal reference's anterior-posterior position, explicit new convention
`offset_direction`, "posterior") was measured, and the reference support's span contained only about half of the named joint sections.
Sagittal populations hold 3-4 series. **Therefore `JOINT_FROM_REFERENCE_MM` is empty: no cohort range is wired, and every joint search
reads its whole established depth with the reason recorded** (`no_supported_cohort_range_for_a_question`, 217 of 336 series; 6 no
reference). The window machinery is real, tested and exercised on real images by a scratch demonstration with the unsupported coronal
ranges (`proof-bursa-window-demo`: proof coronal FS, 18 of 30 slices in the window, answered on the middle slice, 12 unvisited and kept
NOT_READ), but that run is a demonstration, not a result.

**What the consumer does now (the part that ran on the cohort).**
- `joint_profile(visit=)`: slices not visited stay NOT_READ/NaN (counted `joint.slices_not_visited`, not as empty and not as lacking
  bones); default whole depth, so the recess callers are unchanged. `merge_joint_profiles` merges a broadening pass without rereading a slice.
- Questions by view (`joint_questions`): coronal: each sided meniscus body separately, the MCL (decided where the medial meniscus it hangs
  from is named), and with fat suppression the femoral and tibial cartilage; sagittal: each compartment's horn candidates, the PCL
  (no fat suppression), cartilage candidates and ACL (fat suppression). A quantity no question names on the view (ligament and fluid on
  coronal, whose cruciate rules the plane's gate refuses) keeps its pointers and is asked nothing.
- `read_joint` asks runs strongest first (every tie, every plateau slice; equal runs are one group), only while a question of their quantity
  is open; every plane read answers every question its rules can (`joint_answers`). A plane naming one meniscus leaves the other side open.
  Once all are answered the rest stay pointers (`not_read_natively`); otherwise a window (if any) broadens by merge. Runs cut at a window edge
  are walked to their own peak. Recorded in `joint.search`, `a3_joint_search_window`, `a3_joint_search_visited`.

**Measured work** (58 studies, 336 series, drawing off, 4 workers; against the source-matched reference-patella cohort `anatomical-reference-first/cohort-window`):

| ledger | before | now |
|---|---|---|
| joint cheap profile readings | 798 | 798 (no window wired) |
| joint detailed plane reads (lens) | 135 | 102 (-24.4%) |
| joint planes asked / pointed | 352 pointed, all asked | 304 asked of 352 pointed |
| all lens readings made | 1,493 | 1,460 (-2.2%) |
| fields made | 727 | 686 (-5.6%) |
| all cheap profile slices | 10,189 | 10,187 |

The saving comes from asking only the questions a view's gates admit and stopping once they are answered, not from the reference. No
runtime saving is claimed.

**What changed, honestly.** 23 series asked fewer planes; 17 have different native joint observations, all losses and none new: 57 reading rows
(MCL, meniscus, cartilage, PCL) and 10 resolved rows (meniscus, cartilage, MCL) on planes no longer asked, where the middle slice or another
plane already answered the question (laid and projected rows follow). The proof's coronal fat-suppressed slice 17 is no longer read
(the middle slice names both menisci and the cartilage); the non-fat-suppressed coronal slice 17, pointed only by the ligament quantity, is
not read. Known overreach retained: the PCL rule outlines soft tissue behind the knee on sagittal extra planes (still readings, never
promoted), and the cruciate/horn questions often stay open, so those series ask everything as before. Candidates are not promoted.

**Remaining.** A reference-relative joint range needs more non-middle native observations than this cohort holds (the bones' pointed planes limit them);
the next useful move is feeding the reference to the bones' own pointed planes, which is what gates the joint.
