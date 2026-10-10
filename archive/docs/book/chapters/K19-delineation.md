# K19 — Delineation: containers and identity evidence in the patient's own anatomy

| | |
|---|---|
| **Status** | computed: `git tag -l 'knee-K19'` |
| **Depends on** | K08 (search regions, attachments, landmarks), K10 (signal and signatures), K18 (first light exists, so this chapter re-runs it) |
| **Consumed by** | K20 (structure lenses), K21 (identity I), K22 (perturbation of containers), K23 (visibility certificates), K16 (fibrous and compartment agencies, via K20) |
| **Commit label / tag** | `knee/K19` · `knee-K19` |

## 1. Purpose and authority

To find where each structure *is* in this study, and what of it the acquired data shows. The atlas only proposes
where to look.
- **The accord** (change 2): "Use the atlas to propose search regions. Establish local surfaces and centerlines
  from the acquired views". Delineation "must preserve broken, displaced, absent and signal-altered structures"
  (Codex design round 2).
- **THESIS H1's second move:** borders drawn in the data's topology.

## 2. Dependencies and consumers

**Produced** (`knee.run.delineate`):
- **Containers** for the menisci, ACL, PCL, MCL, LCL, the cartilage plates per MOAKS subregion and the patellar
  tendon. Each is built from **robust neighbours**, which are surfaces found in the patient's data inside the atlas
  search region:
  - **menisci:** the femoral condyle and tibial plateau surfaces, giving the peripheral joint-space wedge between
    them;
  - **ACL and PCL:** the notch walls, the attachment sites and the tibial eminence, giving a tube between the
    attachments;
  - **plates:** the subchondral cortex, giving a shell of declared depth;
  - **MCL and LCL:** the medial or lateral cortices across the joint line, and the fibular head.
- **Identity evidence I** per structure, read **on the acquired data only, never on data blended toward a
  prior**. The outcomes:
  - `identified`: the structure's relations hold in this study (tissue along the course between the attachments;
    tissue in the wedge; a shell over the cortex);
  - `not_found_adequate_visibility`: the container is well placed and visible, and the relations fail. This is a
    *candidate* absent or destroyed structure, decided by an agency;
  - `insufficient`: visibility is not adequate;
  - `inconsistent`: the evidence conflicts across series.
- **Admissible damaged configurations** are named, so an injured structure can still read `identified` (ARCH
  §1.8 l.610–615: a structure that falls "may be misplaced, an input error, or absent, as after a complete tear"):
  - a gap along the course;
  - an absent segment;
  - a displaced fragment within the joint (a bucket-handle in the notch);
  - a flipped meniscal fragment;
  - altered signal inside an intact container.

  A damaged configuration is a *reading*, never forced into the healthy shape.
- **Visibility certificates** per structure, question and series: the effective slices along the question's axis
  (in the plane for continuity; along the normal for a cross-section); slice spacing against structure thickness;
  obliquity.
- **Local placement uncertainty:** container offsets from the atlas proposal, landmark NCC, and check-registration
  disagreement (K07).

**Consumers:** K20–K23, and K16 through K20.

## 3. Mechanism

- **Surfaces** are extracted per series, in its own plane, from K10's *identity* readings, never from deviation
  (`provenance/build/revision_1.md`, §F02). A surface is the boundary between two tissue words inside the search
  region, for example fibrous against fluid or fat, or cortex against marrow. It is located at the transition of
  the per-series tissue level along the region's normal, with its sub-voxel interpolation declared.
- **Centerlines** are minimal-cost paths between the attachment sites through places reading the structure's
  tissue word. The cost function is declared, and no weight is fitted.
- **Each container** is a deterministic geometric construction from those surfaces.
- **I** is read from the container's contents and the relations the structure's law names. A healthy signal is
  never required for `identified` when an admissible damaged configuration holds.
- A failure of identity routes to the placement check, which is *independent of this chapter's own fit*: the
  constraint reference (NCC, the placement margin, the check registration; ARCH §1.8). A constraint failure makes
  the reading `unverifiable`, never a finding.

## 4. Contracts

- **Containers:** uint8 masks on the plane grid, plus a parametric description (centerline polyline; wedge
  surfaces) in mm, with uncertainty.
- **I:** `{structure, outcome, relations: {name: held|failed|unread}, certificate, placement_uncertainty_mm}`.

## 5. Implementation choice

- **Numba** for edge and geodesic computations over crops; **SciPy** for distance transforms; **Python** for the
  constructions and decisions. Each kernel is a reference plus a SAME twin.
- **Prior art:** none in this repo. KNEE_ARCHITECTURE §2.10's zone rules propose the search regions, and
  PRIORART's surface methods are references. **Decision:** fresh.

## 6. Verification

- **Detective:** the outcome decisions, the relation tests and the certificate rules are converged.
- **Hypothesis:** container construction is deterministic and mirror-consistent.
- **Phantoms (K11):** ligament gaps, absent segments, displaced and flipped fragments, and altered signal must read
  `identified` with the right relation flags. Misregistration phantoms must read `unverifiable` or `insufficient`,
  never `identified` at a wrong place.

## 7. Integration

`knee.run.delineate.read(study, atlas, deviation) -> [StructureReading]`. Re-run `just firstlight`; the fibrous
agency still abstains until K20.

## 8. Acceptance

Written first: `acceptance/K19.toml`.
- **Behavioural correctness:**
  - the decisions are pinned, and the phantom outcomes are as specified;
  - first light is re-run, SAME holds, and its decision diff is read against this chapter's behaviour-change
    record.
- **Representation fidelity:** container placement on `checking` normals, against K08's independent truths
  (known-transform tests; the founder's landmark sheet), with error bounds. It is never measured against the
  registration's own output.
- **Domain validity:** the `identified` rate on `checking` normals per structure, with bounds; the
  `not_found_adequate_visibility` rate on normals, which should be near 0 and is reported; visibility certificate
  distributions.
- **Performance evidence:** places scanned and paths searched, counted per study per structure; seconds as
  information.
- **Evidence scope:** the atlas version and the series classes present.
- **Invalidation:** a change to the atlas, the signatures, the registration, or the admissible configurations.

## 9. Open matters

- **Facts:** how often a 3–4 mm slice spacing makes thin structures `insufficient`. That is a measured limit,
  stated rather than hidden.

## 10. Provenance and status log

- **Sources:**
  - THESIS §5;
  - KNEE_ARCHITECTURE §1.5 and §2.10;
  - Codex review round 1 (C7);
  - Codex design round 2 (C2 amendment);
  - THE_KNEE §2 (change 2).
- **2026-10-02:** specified in K00.
- **2026-10-02, revision 1:**
  - surfaces from identity readings (F02);
  - absent and flipped configurations (F22, F48);
  - placement validated on the constraint reference and against K08's independent truths (F48, F42);
  - the first-light diff read against intent (F11).
