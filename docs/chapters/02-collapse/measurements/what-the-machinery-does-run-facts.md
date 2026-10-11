# What the current machinery actually does — the RUN facts

OpenSpec task 3.8a, second half. Computed 2026-10-11 by
`workbench/measure/machinery_facts.py` through the production entry point
(`knee.pipeline.run_study`), on study
`1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149`, five series. The probe arranges
values the stage returned and measures nothing of its own. **No parameter was chosen for it**: the
analysis request was read from `data/measurements/boundary-census-one-study/receipt.json` — tile
3.0 mm, offsets −3.0…3.0 by 0.5, axis superior, backend jit, prominence 3.0 mm, minimum divide sites 1.

The code facts are kept separately, in
[`../readings/what-the-machinery-does-code-facts.md`](../readings/what-the-machinery-does-code-facts.md).

## 1. The headline: "measured share" is not the share that was measured

| series | directed interfaces | `low_signal` kind | **bracketed** |
|---|---|---|---|
| Sagittal fs0 | 13,028 | 8,824 (68%) | **2,877 (22%)** |
| Coronal fs0 | 6,774 | 5,012 (74%) | **1,849 (27%)** |
| Coronal fs1 | 5,176 | 4,756 (92%) | **2,118 (41%)** |
| Sagittal fs1 | 8,464 | 5,902 (70%) | **2,047 (24%)** |
| Axial fs1 | 5,728 | 4,286 (75%) | **1,666 (29%)** |

The boundary-census picture's middle panel — "share of each territory's loop on a measured dark
reading", which reads 0.88–0.94 on the coronal fat-suppressed row — is the share whose **edge kind**
is `low_signal`, i.e. whose immediate four-neighbour is below the split. Here that is 92%, and it
matches. **The share that actually returned a bracketed interval, and therefore a position, is 41%.**
Of the `low_signal` edges alone, 2,088 of 4,756 bracketed — **44%**.

So the number the lead quoted to both second readers as "0.88–0.94 supported" answers *what lies
across this interface*, not *was a boundary located here*. Roughly half the arcs that look supported
in that panel carry no measured position.

## 2. A constructed divide can still bracket

`peer_territory` edges that returned `bracketed`: **210, 22, 30, 62, 58** across the five series.

The edge kind is a **one-pixel** fact — what the immediate four-neighbour is. The trace code is a
**±3 mm** fact — what the profile cast along the normal found. They answer at different scales, so a
divide between two territories can have a measured dark band within reach of its normal even though
its neighbouring place is not dark.

This breaks the clean dichotomy that the lead's brief, both second readers and the lead's own
proposed contract all assumed: *constructed ⇒ no reading*. It is not true, and the contract cannot
be written as though it were.

## 3. Being `low_signal` mostly does NOT mean a position was measured

Sagittal fs0, `low_signal` edges: `bracketed=2667  no_dark_bracket=4064  multiple_brackets=1384
missing_profile=709`. The majority outcome is **`no_dark_bracket`** — dark is across the interface,
and the profile along the normal did not find a single bounded dark run. `multiple_brackets` is also
large (1,384), meaning several dark runs were found and none is *the* boundary.

## 4. Territories with no measured boundary at all

Coronal fs0, territory **#4: 33 places, 5.0 mm², peak depth 8.99 mm, 38 edges — every one
`peer_territory`, 0 bracketed.** A sliver whose entire boundary is a watershed decision.

Others that are nearly so: Sagittal fs0 #16 (896 places, 178 edges, 5 bracketed); Sagittal fs1 #12
(342 edges, 12 bracketed), #2 (316 edges, 19 bracketed).

And the converse exists: Sagittal fs0 #11 (1,474 edges, 1,450 `low_signal`, 385 bracketed) and
Coronal fs1 #3 (1,028 edges, 504 bracketed) are mostly measured. **The spread between territories is
large, and it is per-territory, not per-series** — so a bar on a series' average would hide it.

## 5. Interior claimed by no territory

**213, 176, 754, 153, 341** places across the five series — interior tissue above the split that the
watershed left unlabelled.

But `unseeded_available` **never appears in the edge-kind counts**: every series shows only
`low_signal`, `peer_territory` and `frame`. The unclaimed regions are therefore not four-adjacent to
any territory — islands of interior with no marker, enclosed by dark. A code with no instances on
this study, not a code that cannot fire. `acquisition_missing` likewise fired zero times here.

## 6. Depth bounded by the picture, not by anatomy

Interior places whose `distance_guard` is `virtual_frame`: **947, 10, 0, 364, 0**. And `frame` edges:
**98, 20, 0, 84, 0**. So on two of five series a non-trivial number of places have an EDT depth set
by the edge of the picture. Sagittal fs0 territories #11 (23 frame edges) and #9 (75) are the ones
touching it.

## 7. The speckle question, answered and re-opened

**No territory lies outside the leg.** The smallest on any series is the 33-place interior sliver
above. This follows from the code fact: background is below the split, therefore `dark`, therefore
not `interior`, therefore it can hold no territory and generate no edge.

So the scattered cyan speckle outside the leg in `boundaries/series.png` is **not** supported-typed
boundary. The lead's inference, labelled as the lead's and **not established here**: those marks are
likely `trace_points_rc`, which `interiors.py:133` places at the bracket's midpoint along the normal,
`trace = points + ((lower + upper) / 2) * normals / spacing` — up to ±3 mm from the edge it belongs
to. A cortical edge near the skin can therefore draw its trace point in the air. That is a rendering
question with a measurable answer and it has not been measured.

## What this half does not establish

The knee's ceiling in physical units; whether the interior leaks across a bright joint space joining
two bones (the territory table suggests not on this study, since the tibia and femur appear as
separate territories, but that was not measured directly); anything about the other 57 studies.
