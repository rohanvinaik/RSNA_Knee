# What we are shown — the corpus's view structure, measured

2026-10-10. Measured from the tables only (`knee.study.tables.read_tables`), no pixel decode.
Probe: `scratchpad/probe_corpus_shape.py`. This answers the founder's "what is the format of the
data we are presented? What are we shown?"

## Counts

| quantity | value |
|---|---|
| studies in the tables (train + test) | 4410 |
| labeled studies | 58 |
| orphan series (series with no study row) | 0 |

The 4410 matters: the founder asked whether we "can even throw in the others from the competition
that aren't labeled." We can — there are thousands.

## Series per labeled study — not uniform

| series | studies |
|---|---|
| 4 | 8 |
| 5 | 24 |
| 6 | 12 |
| 7 | 6 |
| 8 | 2 |
| 9 | 6 |

## The views

A view is the triple the series table gives: (anatomical_plane, fluid_sensitive, fat_suppression).

**`fluid_sensitive` and `fat_suppression` are perfectly correlated in this corpus**: 192 series
have both '1', 144 have both '0'. There is no series with one and not the other. So the corpus
holds **two sequence types**, not four:

- **(1,1)** — fluid-sensitive with fat suppression. The pathology-sensitive sequence.
- **(0,0)** — neither. The anatomy sequence.

Three planes x two sequence types = six possible views, and all six occur:

| view | series | in how many of the 58 |
|---|---|---|
| Sagittal (0,0) | 72 | 57 |
| Coronal (1,1) | 65 | 56 |
| Sagittal (1,1) | 64 | 56 |
| **Axial (1,1)** | 63 | **58 — the only universal view** |
| Coronal (0,0) | 54 | 45 |
| Axial (0,0) | 18 | 13 |

Series counts exceed study counts for several views, so some studies carry more than one series of
the same view.

**Consequence for the collapse:** the stacking and subtraction happen within a view type, and the
view types are not uniformly available. One view is in all 58; four are in >= 56; one (Axial 0,0)
is in only 13. A per-view platonic artifact therefore rests on a different number of studies per
view, and one view is nearly absent.

## Label prevalence over the 58

| finding | positive | negative |
|---|---|---|
| ACL | 24 | 34 |
| MCL | 9 | 49 |
| Medial Meniscus | 26 | 32 |
| Lateral Meniscus | 23 | 35 |
| Medial OA | 15 | 43 |
| Lateral OA | 11 | 47 |
| PF OA | 21 | 37 |
| Effusion | 35 | 23 |
| Synovitis | 27 | 31 |
| Baker's | 12 | 46 |
| Contusion | 19 | 39 |
| Fracture | 18 | 40 |

Every finding has both positives and negatives; none is degenerate. Effusion is the most common
(35/58), MCL the rarest (9/58).
