# Object resolution: the next build, Codex's reading and proposal

2026-10-10. Requested by the founder after the cell residual figure and the knee's first red/squint
panels. This is a proposed build plan, not a new founder ruling or an implemented stage. Production
code and existing chapter decisions have not been changed by this reading.

## The request and the result to build

The founder asks for the stage 0–4 homolog: take the current readings and make a full toolkit for
clean, precise anatomical object tracing. Resolve the main parts and their relations before asking
the twelve finding questions. His central premise is that the knee supplies much stronger placement
and relational constraints than the crowded, stacked cells did. The cell project is the worked
engineering oracle for how to exploit visual structure, not merely an analogy.

My reading: build an anatomical decomposition that retains the data supporting it. Its first result
is the femur, tibia, their facing surfaces and the interstitial region, with extent through the
stack, original values, and explicit unresolved boundaries. The same operations can then trace
additional structures by their own geometry, signal profiles and relationships. The twelve findings
are later questions about this decomposition; they can coexist in a study.

## What I actually traced

### The knee

- `workbench/render/look.py`, whole: the original panel calls `background_split` on the whole
  volume, overlays `middle_slice <= split`, and computes 8×8 median tiles. There is no anatomical
  label, boundary solver or object prior in that red overlay. The spatial alignment in the image
  is therefore evidence to exploit in subsequent resolution, not the output of a hidden tibia/femur
  selector.
- `structure.py`, `objects.py`, `seam.py`, `axial.py`, whole: the later probes explore border-connected
  low signal, leg closure, unsuccessful intensity-based splitting, a header-derived axis and an
  axial stack walk. `seam.py` currently seeds the first and last fifths of the image and watersheds
  the entire leg support. It does not implement the chapter's proposed central anatomical profile
  markers or a fine bone boundary trace. Its fills change support, not stored pixel values.
- `src/knee/pictures/collapse.py::panels`: arranges supplied readings; does not compute segmentation.
- `src/knee/pipeline.py::run_study` and `open_and_run`: the production route currently reads studies
  and regime keys, not these object/seam probes. `run_study` loads a whole study and then rereads its
  series. The next implementation should consume the already loaded series and route the actual
  object result to both the next stage and the renderer.
- `study/corpus.py::{open_corpus,read_study}`, `study/series.py::{read_series,stack_geometry}` and
  their record types: provide stored values, per-slice LPS positions, row/column directions,
  spacing and stack order. They are the entry for the measurement beside this reading.

### The cell build, symbolically located and read as whole functions

| mechanism | source and consumer | what it actually does |
|---|---|---|
| bounded border movement | `cassette/outlines.py::border_band` (line 124), `pulled_shape` (line 679), `_pulled_taut_reference` (line 309); consumed by `lenses_talk.py::smoothed` and `conversation` | computes flicker/slope leeway; works in a cropped window; shortens a loop within that leeway, with the cell's own oval and area pull; retains shed material separately |
| bodies before parting | `cassette/bodies.py::step_two` (line 968), `bodies_of` (line 1021), `centres_in` (line 908) | cuts contiguous support, stitches eligible pieces, records scale exclusions; does not part a body during this pass; center count is not consumed as an early identity decision |
| neighboring peaks and their separation | `instruments/support.py::read_dips` (line 310), `_saddle_reference` (line 532); `read_dips` is consumed by `record/record.py::record_frame` | reads local maxima, touching watershed territories, the pass between them, distance/direction and dip depth in counts and flickers; it is a support reading, not the cassette's whole resolution procedure |
| footprint extent through depth | `cassette/columns.py::column_of` (line 74), `band_of` (line 149), `_walk` (line 119); consumed by the traced cassette pull-out route | gathers only the footprint's samples before conversion; walks its own hump, stopping at a meaningful dip/rise, missing reading or stack edge |
| preserve separate readings | `cassette/lenses_talk.py::smoothed` (line 219), `counted_once` (line 257), `conversation` (line 433) | processes each body's contour separately, retains shed places, compares overlap with depth, keeps over/under and disagreements rather than merging everything that overlaps |
| own signal and residual | `cassette/resolve.py::{one_round,resolved}`, `cassette/pullout.py::pulled_out`, traced in the preceding reading | retains footprint, band, route and untouched own light while subsequent rounds read the remaining field |

Line numbers above are one-based starts of function definitions as read in this session. They
locate evidence, not a claim that the entire cell project was audited. The live cassette route is
`entry.rows_of_movie → movie.movie_graph → grounds_resolved → resolve.resolved`. There is also an
older `squint` route; a matching name alone does not establish that a mechanism runs on both paths.

The thesis grounding is current §§4–6 and §8.2, with the larger theory read in the preceding pass.
In particular: a shape being *domed* and a nearest-center *dome territory* are distinct; centers
and watersheds propose structure but do not establish object count; the outline keeps meaningful
waists; post-take parting follows the call/recall warrant and never makes a part the signal will
not give. The knee's existing detailed readings also condition polarity and per-slice object count.

## Proposed toolkit

### 1. A physical frame, support and a cheap location map

Retain the stored image and every source coordinate. Derive the actual in-plane superior vector
from both DICOM directions, rather than selecting image rows as an approximation. In axial views
the main superior direction runs through the stack; use stack position and the joint neighborhood.
An oblique acquisition gets its measured projection, not the most common view's default.

Keep three separate facts: outside/support, original signal, and unresolved places. Border-connected
air is a candidate exterior reading. Leg closure supplies a search support; it must not turn an
internal dark structure into air, erase it, or certify it irrelevant to the twelve findings. A
cropped leg is explicitly clipped. The general knee meaning of *black* is data irrelevant both
to the findings and to the context needed to resolve them, never an intensity class.

Use median squints at declared physical scales to locate broad masses and the joint neighborhood.
Keep coverage and within-tile variation beside the median, and the mapping back to native samples.
Coarse views route work. They never supply the final thin-structure boundary or replace the raw
values. The founder's 8×8 visual demonstration remains evidence for this cheap routing role.

### 2. Anatomical candidates and the relation between them

Implement the chapter's central anatomical profile proposal as a candidate generator: two broad
interiors on opposite sides of the joint neighborhood in applicable vertical sections. Keep each
marker, profile, plateau and proposed separation inspectable. The first and last image fifths are
not an anatomical marker contract.

Read the candidate masses' containment, position, continuity, facing borders and the intervening
region. The proposed femur/tibia assignment path combines these readings of their joint relation;
its precise admitted conditions belong in the first packet's contract and visual calls. Do not promote
"upper basin" alone to femur, or two local peaks to two bones. Expected roles persist through the
volume, while visible components can enter, leave, fork or be clipped in an individual slice.
The patella or fibula must not steal a role because it is another large basin.

The told view/weighting is an explicit input. Measure its actual candidate profiles. A polarity
change in a measurement does not warrant blindly negating an image and treating its extrema as
bone interiors. Where the facing surfaces establish the relation more directly, read those.

### 3. Native border profiles and constrained traces

Within a candidate window, sample short profiles across each proposed border in physical distance.
Keep the values, signed fall/rise, local slope, ridge/valley width, and competing neighboring
boundaries. Measure a dark boundary as a valley where that is what the image gives; measure a
step or bright boundary according to its actual profile. No global brightness bin owns all tissue.

Trace the supported boundary segments with deterministic connectivity and path operations.
Choose the tracing operation in the first packet from those measured profiles and pin its contract;
do not create an uncontrolled bank of interchangeable algorithms. Keep incomplete arcs incomplete.
Refine in a narrow band at native resolution rather than repeatedly solving the whole volume.

Port the cell's useful constraint: contour motion is bounded by local uncertainty relative to
edge slope. Port neither its nucleus-sized constants nor its oval pull into a femoral contour.
Use the knee object's stated geometry and preserve supported notches, waists, gaps, discontinuities
and nearby objects. Store the original contour and what a refinement sheds. Do not silently heal
a fracture-shaped break or close a thin anatomical interval to make an attractive smooth outline.

The current noise-law disagreement is retained. Counts, physical widths and gradients can already
be read; a value is called a flicker only where its calibration is warranted. Until then, the
normalized uncertainty reading is absent, and the supported/raw contour is still available.
The move from candidate trace to admitted precision must state the uncertainty it actually has.

### 4. Facing surfaces and an interstitial object

Identify the facing portions of the two resolved bone boundaries. Read the finite region between
them: paired surface points, local separation, normal direction, profile, coverage and connected
extent. The joint-line reference is derived from this relation, with its measured band, not a
single darkest row or an infinitesimal line replacing all joint contents.

This gives later thin structures a bounded neighborhood and relational position. Fluid-like,
cartilage-like or meniscus-like candidates still need their own signal/shape and neighborhood
readings; "between bones" supplies context, not their entire identity. Connected extensions beyond
the central interval remain visible. Trace the patella/fibula and then additional relevant regions
by the same toolkit with their own nominated roles and measurements. Preserve the enclosing bone,
marrow and boundary as different levels of the object record where that distinction matters.

### 5. Extent, cross-view conversation and ownership

Carry traces through neighboring physical slices, reading appearance, change and continuity.
The cell band contributes the idea of measured extent and explicit clipping; a fixed footprint's
single intensity hump does not define the full extent of a large changing bone. Branches or
multiple contours can belong to the same anatomical object.

Compare separately acquired views in patient coordinates, retaining acquisition support and
alignment uncertainty. Cross-view alignment is a measured operation, not permission to declare
native voxels interchangeable. Use complementary views as separate readings; duplicate edge
operations on one contrast are not independent witnesses merely because their names differ.

Keep an ownership record for peers, an explicit containment relation for nested objects, and
unclaimed/disputed regions. A candidate carries its native footprint/surface, extent, original
values, supporting readings, source/view and route, role warrant and named status. A proposed
decision interface distinguishes `identified`, `unresolved_identity`, `unresolved_boundary`,
`disputed_ownership`, `clipped`, and `unreadable`; the final codes are to be specified with the
first packet's actual remedies. A missing reading never becomes rejection.

### 6. Pull-out and the remaining field

Make the cell residual demonstration useful here: show one candidate with the other resolved
peer objects excluded from the search/display, while its own recorded signal is unchanged. Keep
the excluded and unclaimed source data reachable. This is the first knee counterpart of the cell
figure: does the intended object remain legible when its neighbors are accounted for?

Use a search/ownership residual to recurse on what remains unexplained. An MR image does not
inherit the fluorescence project's inverse-square emitted-light halo by analogy. Any subtraction
of modeled acquisition spread needs its own stated MRI measurement and contract. Merely marking
resolved search support requires no invented subtraction law. A pass that finds nothing new
records what remains; it does not certify that every leftover belongs to black or noise.

## Build order and deliverables

The proposed reference primitives make the toolkit concrete. These are interfaces to specify in
the first packet, not symbols that already exist:

| primitive | reads | returns |
|---|---|---|
| physical squint | stored volume, per-slice geometry, declared physical scales | median, variation, support coverage and native-coordinate map |
| profile across a border | candidate border points, local normals, physical reach, native image | sampled counts and distances, slope, step/trough/ridge readings, missing-support status |
| supported trace | candidate transition segments, their movement bands and neighboring barriers | connected contour chains with closed/open status per chain, candidate boundary coverage/gaps, original and refined traces, shed/disputed places |
| facing surfaces | two candidate traces and their proposed relation | facing patches, separation field, intervening support and profiles, uncovered places |
| extent and agreement | per-slice traces in physical coordinates, separately acquired views | spatial links, branch/entry/exit/clipping readings and disagreements |
| own-object view | candidate source references and the ownership record | unchanged own samples, excluded peers and unclaimed/disputed context |

The supported trace's reference operation is connectivity within the measured border bands,
with a constrained contour-shortening pass. A gap has an explicit absent-support reading; the
operation cannot make it disappear merely to close the chain. Knee-specific shape constraints
and an admitted movement band are arguments. Any later accelerated implementation answers to this
reference operation and its recorded ties.

Closure is reported per contour chain. The containing candidate separately records its observed
boundary coverage, gaps and clipping; one closed chain cannot certify the entire object's boundary.
An absent-support gap leaves boundary extent unresolved, without diagnosing a break in the anatomy.

1. **Finish the object and seam part of Chapter 2.** One production path from the existing study
   reader: physical support and squint → anatomical candidates → native boundary profiles and
   traces → facing surfaces/interstitial region → object records. Render these exact returned
   records. First demonstrate a paired coronal case and sagittal case through their stacks, then
   the axial relation; run the admitted implementation across all 58 studies before building above
   it. Both available contrasts speak separately; neither is mandatory merely by a convenient
   example's availability.
2. **Populate the stage 0–4 loop homolog with the founder's knee version.** Cheap readings,
   structural exclusions, bodies, conversation, ownership and residual rereading. Preserve
   additional components and unresolved material, then nominate the next anatomical structures.
   The loop/candidates packages currently still say their knee versions are not yet given; this
   proposal must not silently mark them settled.
3. **Carry the admitted records into later encoding/cleanup.** Preserve spatial geometry, raw
   profiles and distinct meanings beside any code or vector. Diagnostic agencies then receive
   resolved objects and relations, with explicit missing evidence.

The first implementation packet should specify a small callable contract and its consumers,
not open every later chapter at once. Suggested organization within the existing packages:
Chapter 2 owns support/frame, squint, object/surface measurements and seam; `candidates` owns the
shared record when that chapter is opened; `loop` owns residual scheduling when its teaching is
recorded; `pictures` owns rendering of returned records. Split modules by these contracts during
implementation. No second segmentation procedure hidden in workbench renderers.

## Visual and engineering checks, declared before that build's run

For each object and view, show recorded image → location map/markers → measured border profiles
and uncertainty → native trace → extent and facing surfaces → own-signal pull-out/unclaimed field.
Display source coordinates, slice and view. Permit the founder to call the actual object and
boundary; geometric laws alone do not certify anatomical correctness.

Probe the cases that expose the contracts: view rotation/reflection with geometry updated, an
oblique axial series, missing contrast, absent/empty/malformed input, unequal spacing, truncated
objects, a narrow interval, a supported notch, broken boundary, extra basin and forked section.
Separate image-frame flips from a physical reflection and do not confuse the two in the test.
Report identified, unresolved and wrong per object role after calls exist, with source examples;
no whole-volume percentage can stand in for spatial correctness.

Reference kernels precede accelerated twins. NumPy/SciPy/scikit-image handle array/library
operations; custom repeated profile and contour loops get Numba twins admitted by SAME. Python
orchestrates named decisions. Declare shapes, axes, dtype, millimetres/counts/noise units,
allocation and access order. Coarse scans happen once per series; fine work is bounded to candidate
windows/border bands. Preserve original stored arrays and gather needed samples before converting,
as the cell column implementation does. Measure CPU/allocation/repeated work through the real
route, then count the budget; no speed claim is made by this plan.

Use the installed harness for its claims: Hypothesis for geometry/ownership invariants, Detective
for named pure decisions, SAME for twins, Import Linter for rendering and stage boundaries, and
the profiling tools for finding cost. A crop at an image edge and missing readings are first-class
inputs. These checks accompany visual calls; they do not replace them.

## Open points to settle by the first visual packet

- Which measured native border profiles and anatomical contours are admitted as the first object's
  interior/boundary warrant, and where the founder wants its scope drawn.
- Physical coarse scale, contour leeway and resolved-scale/reach contracts, derived from acquisition
  geometry and the anatomy that must survive; no leaderboard fitting or new arbitrary quantile.
- The warranted uncertainty calibration and the committee's explicit assignment paths. Neither
  unanimity nor majority is silently installed as a universal law.

These are concrete readings to present together with pictures. They do not prevent locating
objects or building the measurement toolkit, and no unmeasured choice is recorded as settled.

## Measured geometry baseline

The companion record is
[`object-toolkit-geometry.md`](../measurements/object-toolkit-geometry.md): the real Chapter 1
reader opened all 58 labeled studies and 336 series with pixels and geometry; the demonstrated
8-place tile spans 1.172–6.2504 mm across acquisitions. This measures inputs and coordinates,
not contour accuracy. The rerunnable probe and its complete receipt are named in that record.
