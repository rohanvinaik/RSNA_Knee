# Dimensional collapse for knee MRI

**Status: approved plan; implementation in progress, 2026-10-16.** Prepared at Rohan's request
after the anatomical definition pass (`4a126fc`, checkpoint `3bede6a`), then approved: «I like it!
Use the same "cheap sub agents and Anthropic API sub-agents" to build the thing as mechanized
and effective/clean as possible». The steps below specify the full build; their presence here
does not report that they are implemented. The first fibula case is undergoing integration and
verification; later anatomical families remain to be built.

Rohan's scope is both selection of the slice ideal for resolving each object and resolution of
that object across all available study information. The established anatomical definitions stay
the basis. The later AI work and diagnosis remain his to specify.

## 1. The mechanism

**Whole acquired stacks → shared cheap readings → anatomical neighbourhood and local depth
profiles → detailed resolution on useful native planes → one anatomical object described by
all its sourced observations and measured extent.**

Rohan's implementation requirement, 2026-10-16: “Also, note that computational efficiency in the
production path is a key output. Full compute for building and diagnosis is fine, but the
production path should be computationally minimal.” Production compute is an acceptance output:
measure the real drawing-off path, share identical readings, avoid development-only work and
unnecessary detailed planes, and preserve measurements when optimizing. Rohan subsequently
emphasized that the collapse is itself computationally efficient: the low-resolution lenses
resolve the best view for recognition, and recognition computes against that selected view.
This is the mechanism the implementation must preserve, rather than merely optimizing loops
after doing unnecessary recognition work. Development evidence can
read the full data to establish the method; that exploration does not become production work.

The original stacks stay available. Every measured value is retained and shared with its actual
consumers. Reduced views expose the dimensions a question reads; they do not replace the record.
A new local reading runs when another view, continuation, surface, branch or unresolved candidate
has information still to contribute.

A best slice belongs to an **object property in a particular view**. A meniscal body and its
horns, a tendon's longitudinal course and its cross-section, or different cartilage surfaces can
have different useful planes. Keep them as descriptions of the same anatomy. Do not force every
object onto one global plane or pool its lenses into a fitted quality score.

Two outputs must be kept separate and connected:

- **Representative observation:** where the relevant lens can resolve that part cleanly.
- **Extent and identity:** what the study establishes about the part's continuation, boundaries,
  attachments and other appearances, with unobserved portions stated explicitly.

A representative mask alone is not the complete object. Completion also does not require a
fabricated dense segmentation between sampled planes. It requires the descriptions the supplied
views actually recover, including their physical support and remaining uncertainty.

## 2. Grounding in the object thesis

Read the complete named sections of
`../cell_tracking/docs/pipeline_thesis/paper/what_an_object_is.md` from the project root:

| Source | Mechanism carried into this plan |
|---|---|
| §1.3 | The squint removes irrelevant variation from a reading; original information remains available; complementary views jointly describe the object. |
| §4.1–4.2 | Laws justify the collapse; each lens chooses the plane where its own reading is clearest. |
| §4.3 | The composite keeps local depth and points to signal other planes missed; it does not decide identity. |
| §5.6 | A bounded site gets local readings through depth; another local peak or residual can point to another useful observation. |
| §6.4 | A resolved footprint can supply a depth profile, representative depth and occupied band. |
| §13.4 | Fine work runs where coarse measurements point; any coarser representation must preserve the distinctions its question needs. |
| §14.1–14.2 | Use the target domain's laws and lenses. MRI supplies sequence-dependent tissue signal and anatomical continuity. |

The cell implementation's optical focus measures, camera flicker, nuclear hump and one depth per
planar location are not MRI specifications. A knee structure can curve, branch or change
cross-section; one femur has two condyles. Retain multiple useful peaks, patches or bands where
the anatomy warrants them. A second peak does not itself establish a second anatomical identity.

Likewise, a depth interval is meaningful with its **source frame, normal and in-plane support**.
Its millimetre endpoints alone cannot become an interval along an orthogonal acquisition's axis
or a segmented volume. Physical geometry maps the supported observation to the target view.

## 3. What already exists

Static source review establishes the following integration points; this is not a new runtime
measurement:

- `scripts/run_interiors.py::measure` reads each series' background split, finite mask, geometry
  and `read_squint_stack`, then resolves the standard middle slice. Rohan has accepted that middle
  as a valid first slice. It remains a bootstrap observation.
- `SquintStack` retains per-slice tile minimum, median, maximum, finite coverage, native bounds
  and scanner-space centres. The existing 10 mm squint already supplies broad spatial readings.
  Those values measure tiles, not anatomical identities.
- `read_part_slice` obtains shared `lens_of` and `field_of` readings on a selected native plane;
  it does not invoke every anatomical assignment on every slice. `Measures`, `once`, frames and
  directional matches provide the existing reuse path.
- `find_fibula` still runs detailed territories across its candidate block before selecting its
  main slice. This exception is documented in its own source and is the first target to replace.
- Other selectors already use useful landmarks: tibial top for the posteromedial tendons,
  patella centre for the retinacula, fibular attachment for LCL, lateral head support for biceps.
  Their positional observations remain evidence; a new profile can add a different useful plane.
- Same-place matching and cross-plane targets already exist. The ledger distinguishes values
  made, handed on and actually read. Drawing stays optional and off by default.

Extend this path. No new pipeline framework or parallel production recognizer is needed.

## 4. Ordered implementation

### Step 1 — Keep the definitions and make observations addressable

Preserve the completed rules, receipts and inspected pictures as the starting point. Trace the
consumers of the selector and its outputs before changing it.

Extend the existing records with the smallest shared index that associates observations with an
anatomical part. Reuse the existing arrays rather than copying masks into another storage path.
An observation needs its series, acquisition type, native slice/frame and support, actual
mask/readings, selection reason and named outcome. Keep the profile and measured continuation
beside it. Air, skin and general tissue fields remain useful spatial context without assigning
them a fictitious universally best slice.

Retain three distinct provenances: native identification, a warranted same-place transfer, and
a projected location target. Rohan already authorized same-place transfer: it is the same leg.
That remains anatomical evidence with its provenance. A target projected from a different plane
points where a native question should be asked; it is not an independently observed boundary.

### Step 2 — Make the shared scouts point to anatomy

Use middle-slice bones and joint context to establish the first physical neighbourhoods. Reuse
the whole-stack squint to locate candidate ranges before asking finer questions. A profile may
keep several separate quantities: contrast, support, enclosure or a spatial relation. Do not
combine them into an invented weighted verdict.

A tile maximum can point to possible bright signal; a minimum can point to possible darkness.
Neither names a pocket or tendon. A tile median can locate broad marrow or muscle support while
missing a thin structure. Exclude a location only when the reading actually excludes the
requested property; otherwise retain an unknown. Coverage of finite pixels is not anatomical
visibility. Add a cheap finer local lens where the existing summary lacks the required fact,
using an anatomical or already justified sampling scale.

### Step 3 — First complete case: fibula and its lateral consumers

Use the named tibia, knee side and non-FS marrow reading to restrict the fibula's neighbourhood.
Within that corridor, preview cheap marrow-support and surrounding-contrast readings through
physical depth. Establish from the actual pictures which reading points to the competent bone
body. The precise function is a build task, not an asserted result of this plan.

Retain the candidate peaks or ranges and their measured reasons. Run the established fibula
resolver on the representative native plane(s) they point to, sharing any detailed plane already
read. A plateau or separated equal candidates remains visible; there is no proof index,
arbitrary top-N list or parameter search to make an answer land on a preferred slice. A clear
landmark slice can coexist with another profile-selected observation.

Then measure its continuation and useful observations in the other acquisitions. Map supported
physical places into each acquisition's own geometry; resolve locally where that view supplies
new information. Feed the resulting fibula observations to the existing LCL/popliteus and biceps
dependencies. Reuse the head support, marrow references, frames, matches and detailed lenses.

**This first deliverable includes slice choice, extent, cross-view evidence and real consumers.**
It is not finished at a nicer fibula picture. It must remove the expensive all-slice territory
search without silently losing the competent anatomical demonstration. Differences from the old
choice are inspected anatomically; matching the old index is not the objective.

### Step 4 — Establish continuation without expanding full recognition everywhere

From an identified observation, read a bounded anatomical neighbourhood through depth using the
appropriate cheap signal. Let its changes and other views point to additional native readings
where an end, turn, branch, ambiguity or distinct useful description needs resolution.

Move the neighbourhood with supported anatomy; do not extrude a fixed footprint through the
stack. Retain all relevant intervals/patches, their source geometry and whether an end is
observed, clipped by the scan or unresolved. A neighbour's band bounds a search for a thin wall
or cartilage layer; it does not establish that layer throughout the band.

Cheap stack/ROI profiles are allowed across depth. Running all detailed anatomical recognition
on all slices is not the collapse. The measured work should follow the remaining anatomical
questions and the information needed to answer them.

### Step 5 — Extend by anatomical dependency, with the same end-to-end loop

After the fibula case works, extend foundational bone/joint observations, then the dependent
families below. Within a family, keep each object's existing definition and share literal
measurements. Every family goes through representative choice, extent and useful cross-view
observations before the next family; do not select all peaks first and postpone whole objects.

| Order/family | What points | What the useful local reading must establish |
|---|---|---|
| Bones, marrow and joint frame | Existing bone observations, marrow/cortex contrast and patient-space relations | Bone identity and useful body/articular-end observations; two condyles remain one femur. |
| Patella, extensor tendons, Hoffa and two suprapatellar pads | Patella and tibia; anterior compartment; paired acquisition contrast | The tendon course and the separate fat/recess relations, at the planes that expose each. |
| Sided menisci, cartilage, ACL/PCL and collaterals | Condyles, plateau, notch and attachment neighbourhoods | Dark wedges/cords and joint-surface layers in their anatomical relations; coronal body and sagittal horns contribute to one sided meniscus. |
| Recesses, fluid, synovial surface, capsule and retinacula | Known bones/fat and the visible compartment | Fluid in the named compartment and the correct boundary against its neighbours. A finer local wall reading follows the compartment pointer. |
| Gastrocnemius heads, posteromedial tendons, sartorius and biceps | Existing condyle, tibial-top and fibular-head context | Distinct muscle/tendon tissue and neighbour order; retain useful cross-sections and longitudinal descriptions. |
| Artery, vein and gastrocnemius-semimembranosus bursa | Bundle corridor between heads; tendon–posterior-tissue seam | Separate enclosed lumens or fluid in the named bursal relation, with continuation and any neck/wall actually shown. |

ITB and popliteus share the lateral context established by the first case; general fat and muscle
remain shared supporting fields. An acquisition can supply context even where it cannot resolve
the final part alone. No requirement is added that each object must identify independently in
every view.

### Step 6 — Combine the descriptions and revisit unresolved sites

For each anatomical object, retain what every provided view contributes: native observations,
valid transfers, physical support and compatible relations. Keep disagreement and unavailable
information. Same-place twin measurements can be compared; intensities from different sequences
are not averaged into a replacement image. Coincident projections alone do not establish equal
boundaries; useful native observations add what the other view could not show.

The knee counterpart of the composite is a shared pointer to unresolved object/property sites,
with candidate depths and their provenance. Build a displayed composite only if it has an actual
consumer. The data need not be forced into one nearest-brightest-depth image.

Revisit an unexamined band, expected continuation, compartment or complementary view when the
object's existing definition points there. Earlier resolved parts provide context. Broad muscle
or bone labels must not erase a finer structure whose definition reads that field. Preserve raw
MRI signal; this plan does not introduce literal intensity peeling or a nuclear-halo model.

An unanswered question is a named unresolved portion, not false absence. A complete object record
accounts for all relevant supplied evidence; it does not pretend the scan contains anatomy
outside its field of view.

### Step 7 — Verify through the one production operation

For each family, inspect a raw stack overview, local profile with selected physical planes,
native masks, and cross-view support together, at the object's own pixels. Keep the picture-first
loop of `HOW_TO_BUILD.md` §7.

Through `scripts/run_interiors.py`, verify drawing on and off and trace selected-plane products
to their actual consumers. Meaningful adversarial cases include reversed stack order; unequal
spacing/oblique geometry; ties and plateaus; empty, zero, nonfinite or unavailable signal;
clipped ends; separated depth components of one anatomy; a coarse median hiding a thin part;
and disagreement between acquisitions. A selection must not silently erase another useful peak
or mistake an unmeasured depth for an empty one.

Use the existing ledger to count cheap and detailed reads and show reuse. Cache identity must
include the actual measurement context so distinct crops/settings are not aliased. A selected
plane shared by several objects is read once for those consumers. Retained diagnostics are
reported as retained if nothing consumes them. Measure hot loops before compiling them with the
existing JIT discipline, preserving their readings run against run. Run the local gate before
committing and refresh canonical records after verified code changes.

## 5. What remains to establish during the build

The architecture is specified here at the level the thesis warrants. The concrete MRI profile
functions, qualifying structures and continuation/stop conditions must be demonstrated from the
existing anatomical definitions and actual pictures, one family at a time. This is normal
implementation work; it is not permission to fit an index or import the later AI machinery.

Geometry that does not establish correspondence remains an explicit mismatch. This plan does
not silently add registration, interpolated anatomy, a universal score, new numerical cutoffs or
a general-purpose rule engine. Any genuine gap in Rohan's intended meaning is brought to him as
that specific gap, rather than handing back ordinary implementation choices.

The first build target is Step 3 together with Steps 1–2 and 4–6 as needed for that one complete
case. Its inspected result establishes the reusable operation; then Step 5 extends it.

## 6. Fable consultation and independent review

The lead saved its reading and draft before opening Fable's completed answer. The text-only
consultation used the direct Anthropic API, model `claude-fable-5-1`, with the founding
conversation, complete relevant object-thesis sections and current anatomy context. It returned
58,227 input tokens and 9,252 output tokens (including 3,626 thinking tokens), `end_turn`;
no monetary amount was returned. No image or credential was included in the source packet.

Fable: “the pointer must be a measurement on an already-made, already-cheap product, read against
an already-named definition.” This agrees with the lead's proposed shared-scout/local-profile
flow. Fable also agreed that the composite's pointing role transfers while its cell-specific
single-depth form does not, and supported the fibula as the first all-slice exception to replace.

Several suggestions were not adopted: contiguity does not prove one hump; two peaks do not
necessarily mean two anatomical objects; generic compactest-cord/largest-bone criteria are not
universal definitions of best; a bounding object's band is not observed wall extent; and a
requirement for native re-identification everywhere would withdraw the already authorized
same-place transfers. The accepted middle-slice bootstrap and permission to add lenses do not
need re-authorization. These are the lead's comparisons against Rohan's words and the source,
not verdicts assigned by an advisor.

Complete prompt, source sections, prior lead reading/draft, verbatim answer, API metadata and
comparison: `data/readings/collapse-20261016/` (ignored project evidence). The consultation
informs this proposal; it does not verify unimplemented selectors or anatomy on images.


## Implementation review, 2026-10-16

The first API family implementations are provisional until they meet this plan's end-to-end
requirements. An added observation with no real consumer, a known false anatomical name, or a
broad search that restores unnecessary detailed computation is not a completed family. Preserve
the competent definitions and inspect legitimate changed selections; receipt equality is not a
requirement to leave new observations unwired. The lead's current concrete review findings and
clarification are in `data/readings/collapse-20261016/api-build-and-search-priors/PARENT_REVIEW.md`.
Complete integration, validity and measured production efficiency before cohort search-prior
analysis treats those selections as ideal observations.

## Acceptance clarification from Rohan during implementation

Rohan: “Noted, but that's fine. We need the capacity to recognize, accuracy and completeness is for AI. We just need to define these objects as "platonic" versions of them, correct in the general case, not perfect or complete.”

This governs the implementation requirements above: the deliverable is a domain-grounded concept and competent deterministic recognition capacity, with useful slice selection and efficient wiring. Imperfect boundaries, residual misses and incomplete coverage are not new blockers. The build keeps the observations it actually makes and states unknowns without requiring exhaustive recovery or perfect continuation. Accuracy and completeness remain for the later AI layers Rohan has yet to specify.

## Volume and the encoding layer: Rohan's source pointer

Rohan: 'Do note that the "<object>" thesis lays out how volume is to be computed as a natural extension of the full encoding layer--bundling operations in HDC, specifically the idiomatic form of HDC that was created for this representation.'

The source mechanism must be read before implementing volume-dependent encoding. Generic HDC mechanics or a requirement for dense geometric reconstruction must not substitute for that account. The current recognition and useful-view build remains governed by the capacity criterion above.

## Implementation status, posterior family and lumens/bursa, 2026-10-16

The posterior family (both gastrocnemius heads, semimembranosus, semitendinosus, gracilis, the
sartorius, the biceps femoris tendon), the artery and vein lumens and the gastrocnemius-
semimembranosus bursa now reach the grouped per-study object output with native, laid, projected and
named-unresolved observations, as do the iliotibial band and the popliteus tendon. The tubes among
them (the three tendons, the lumens, the bursa's fluid) also have a cheap longitudinal ridge
reading on the series the leg runs through (`knee.collapse.posterior`), kept with its stops as a
pointer, not the part's course. The capacity is demonstrated once on the proof and the positive
bursa study through `scripts/run_interiors.py`; the cohort run and statistics, the muscles'
longitudinal descriptions and the bursa's neck and wall remain unbuilt. The record and its limits:
`docs/RESOLVING_THE_PARTS.md` §9, last section.
