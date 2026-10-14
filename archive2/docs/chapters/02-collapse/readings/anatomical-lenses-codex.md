# Anatomical lenses and their composition — lead reading

2026-10-10, written before the Fable workshop. This develops the accepted
object-resolution-toolkit reading; it is a proposal, not an anatomical admission
rule or a claim of implemented resolution.

## Correction after the founder's pause: negative resolution is information

The founder challenged my phrase "spreads into surrounding tissue" and directed
me to read the thesis's there-is-no-noise argument. The workshop has not been
sent, and implementation has not resumed from this proposal.

I then read whole current §§1.1, 1.2, 1.5, 1.9, 1.10, 5.2, 7.3 and 8.5. Section
1.2 explicitly makes confidently resolving a reading to its cause informational,
including a reading resolved to belong to no object of interest. Section 1.5
explains why: laws tie the parts together, so a warranted exclusion constrains
the rest of the problem. Its Sudoku and Monty Hall examples preserve the source
of the exclusion and what it implies elsewhere. Section 1.9 retains every
resolved removal and its lineage; the residual is the same problem with added
context. Section 5.2 removes only in one lens's view and deletes nothing. Section
7.3 keeps sparse readings and the measured absence even where full analysis
is omitted. Section 8.5 distinguishes confirmed negative expertise from refusal:
an unanswered question never manufactures a censor.

My earlier visual remark does not establish a defect. A basin containing material
outside the visible bone outline is a statement about its support. What that
support means depends on the operation's contract, its readings and the
structural resolution they warrant. I prematurely assessed the panel as if its
sole task were to supply finished bone masks. The producer's contract must be
traced before interpreting that panel as success or failure.

The reading below is incomplete in a load-bearing respect: it mostly describes
candidate construction and retained context, without making the consequence of
confident negative resolution explicit. Preserving raw samples is necessary but
does not itself express the information in an exclusion. A warranted negative
needs its subject, question, scope, supporting readings and lineage, together
with the downstream constraints it licenses. "Not femur" does not thereby mean
"irrelevant to every finding"; an unread or unresolved place does not thereby
mean "not femur". Geometry or scalar brightness alone must not silently supply
that warrant. These are corrections to my understanding, not newly settled knee
admission rules or authorization to restart the paused build.

### Grounding after the correction

The founder then instructed use of cheap miners and symbolic tracing, reiterated
the two oracles' distinct roles, and explained that inspecting the actual image
should prevent this kind of misreading. The next pass remained reading/tracing
and idea work; no anatomical production code was changed.

**Knee producer, current source read whole after a Serena overview:**
`workbench/render/seam.py` intentionally calls a seeded watershed with
`mask=inside`, the coarse closed-leg support. Its two markers occupy the first
and last fifths along the selected header axis. The plotting code colors the
result as two basins. Partitioning that whole support is what the operation was
asked to do; the colored territories' inclusion of extra material is not proof
of a malfunction. The module does not produce an admitted per-bone ownership map.
The observed panel and this source are historical exploration, not the current
production entry point. No algorithm change follows merely from my visual remark.

**Cell implementation, whole units symbolically located and read:**

| unit | fact established by its implementation |
|---|---|
| `cassette.bodies.PlaceRecord` | per-place OPEN/REMOVED/SET_ASIDE state; deciding step index and ordered step names; `still_open` supplies later search support |
| `decide` | updates only open selected places; a prior decision retains state and deciding step; new arrays preserve the prior value |
| `step_one` | removes under separate dark/haze step names; unavailable readings remain open; returns the place record and measured light |
| `places_left` | starts a slice record open, then marks previously taken voxels SET_ASIDE under PULLED_OUT |
| `bodies_of` | consumes that record's open support to construct the slice composite and run steps 1/2; a refused stage-0 slice returns None |
| `resolve.what_is_left` | consumes the take, rereads residual, reconstructs lens bodies; composite alive support is `step_one(...).still_open()` with prior takes set aside |
| `box.sites_of` | uses alive support, absence from held bodies, and additional positive composite support to nominate search sites; absence from a lens's bodies alone is insufficient |

References connect `places_left` to `bodies_of`, `what_is_left` and vector inputs;
the already read `one_round` consumes `what_is_left` and `sites_of`. This traces
actual consumption of negative-resolution state rather than merely finding a
record type. I have not audited the entire cell code or the entire vector path.
The older `squint` implementations remain separate paths named by the contracts.

**Additional thesis units read whole by the lead:** §§4.6 and 10.5. A cheap miner
read whole §§4.6, 5.6, 5.7, 10.2–10.5 and reported its limits. Section 4.6 gives
the direct visual principle: bodies can outline cells poorly yet lie on cells,
while no lens draws on open field; a view useful for exclusion need not finish a
positive outline. Section 10.5 keeps another candidate's material distinct from
noise and keeps disputed/unassigned material visible. Its cell-specific larger
claim rule is not adopted as a knee ownership policy.

**My revised synthesis for workshopping:** represent positive resolution,
warranted exclusion, not-read, unresolved identity and disputed ownership apart.
Each claim is scoped to its question/view/place and retains the measurement route.
Other resolved material can constrain a target without becoming globally
irrelevant. A subsequent boundary search consumes both its remaining possibilities
and the explanations already established around them. The image series must show
those explanations and unresolved material as well as proposed positive contours.
This is the conceptual correction to the earlier candidate-heavy reading; the
specific knee warrants are still to be worked out from its domain and examples.

## Goal and evidence read

Build the stage 0–4 homolog that resolves the knee's objects and preserves their
own source signal. The founder's latest request is to work out the lenses and
their wiring for the key components in the competition's views. Diagnosis remains
a later question over those objects. The thesis governs the decomposition; the
cell implementation supplies literal mechanics.

Read whole: SPINE, Chapter 2 teaching and design, the accepted toolkit reading;
current thesis §§1.12, 5.3–5.5, 6.1, 14.1. The factual miner read whole §§4–6 and
14.1 across the two passes, with its limits reported. A miner's extraction does
not settle interpretation. The founder's definition of a lens, black and speck
governs the transfer.

Symbolically located and read whole in this pass:

* `cassette.resolve.one_round`: independent depth readings, bodies, conversation,
  take, residual site search and reaching down; the production caller `rounds`
  references this function. Earlier tracing connects `resolved` through
  `grounds_resolved`, `movie_graph` and `entry.rows_of_movie`.
* `cassette.outlines.border_band → _widths → pulled_shape`; `pulled_shape` is
  consumed by `lenses_talk.smoothed`, which `conversation` consumes; `one_round`
  calls `conversation`. Other consumers include last look, cleanup and reaching
  down. `smoothed` preserves each body, prevents neighbor ownership collisions,
  and retains shed places.
* `instruments.support.read_dips`, referenced by `record.record_frame`, is a
  3-D support-window measurement of neighboring peaks/watershed passes. It is
  not the cassette's entire candidate resolver or an existing 1-D knee routine.

The source contracts retain the older `squint` replacements as lineage. We do
not infer that editing the cassette would change that older route.

## Images inspected

Actually viewed `data/pictures/object-toolkit/packet-a-annotated/series.png`,
`data/pictures/structure.png`, `data/pictures/seam.png`, and
`data/pictures/axial.png` at their saved resolution. These are historical
artifacts, not a fresh execution of their source.

Observed: the squints retain the large rounded masses and the interval between
them in the vertical examples. Native red low-signal samples often lie on those
contours, but also mark other dark tissue. In `seam.png` the seeded basins extend
into surrounding tissue; their labels do not trace each bone's enclosing border.
In `axial.png` the visible components change along the stack; a two-part vertical
image split cannot represent that sequence. The saved cyan probes are useful
measurements, but their central display location often misses the actual facing
surfaces.

My inference: spend fine work on candidate border bands and candidate-to-candidate
relations. First expose what native profiles say along those contours and at the
joint. Keep broad routing, fine tracing and anatomical identity separate.

## Lens meanings: questions constructed apart

Each lens has one measured quantity and a scope. Multiple quantities obtained
from the same samples are separate readings with shared provenance. They are
not made statistically independent by renaming them. Constructed orthogonality
concerns which question a claim answers (§1.12); it is not a correlation cutoff.

Candidate measurement contracts:

| ID | one quantity | consumer |
|---|---|---|
| acquired | native sample support | every reading's availability |
| location | signed position on a declared patient-frame axis, mm | candidate relation and routing |
| level | stored signal along a declared physical path | profile inspection and sequence-specific interpretation |
| change | first difference per physical distance, counts/mm | transition locations and movement-band reading |
| trough | interval between two flanks of a local minimum, mm | boundary-layer candidates; no cortex identity alone |
| enclosure | winding/inside relation of a specified chain | candidate interior support |
| connection | component membership under declared adjacency | contour chains, region extent and residual search |
| facing | separation between nominated facing patches, mm | paired-surface/intervening-region record |
| continuation | overlap/displacement of nominated supports in adjacent physical slices | extent links, branching and clipping |
| view-agreement | displacement of corresponding nominated surfaces after stated alignment, mm | cross-view conversation |
| ownership | source-place membership in nominated peer supports | shared, own and unclaimed signal |

These are proposals, with interface names to specify atomically. They do not
write anatomical or diagnostic digits. A profile minimum, a membership label,
an absent sample and an unanswered identity question are different facts.

## How the objects would be resolved

1. Keep the already read series, per-plane physical frame and raw values. An
   exterior/support observation restricts search without painting over values
   or assigning internal dark tissue to black.
2. The squint supplies candidate windows, broad interiors and the joint
   neighborhood. Each candidate stores the readings that proposed it. Candidates
   remain plural where the data supplies alternatives. Image fractions are
   display/request inputs, not automatic anatomical identity.
3. Native short profiles cross proposed border segments in their local physical
   normals. Retain actual steps, troughs, ridges, plateaus, flank locations and
   missing support. Read all alternatives before choosing which marks the
   candidate boundary. Sequence metadata provides context; a blanket intensity
   inversion does not turn every bright peak into a marrow marker.
4. Connect supported segments within declared bands, preserving open chains,
   gaps, notches, barriers and shed material. A constrained shortening operation
   may remove grid roughness only under its movement/geometry contract. The cell
   oval pull, nucleus dimensions, hole closing and fluorescence halo do not
   transfer as knee laws. Missing uncertainty calibration remains missing; it
   must not license a free contour move.
5. Nominate the femur/tibia relation from their enclosing contours, told patient
   orientation, neighboring-slice extent and their facing surfaces together.
   Their role assignment has explicit warrant paths. Upper position or basin
   number alone does not warrant an identity. In axial, read through-stack
   superior/inferior progression and the neighboring acquired views.
6. Their facing patches delimit an intervening region. That region is context
   for cartilage, meniscal and fluid candidates; the entire region cannot be
   labeled synovial fluid by location alone. Patellofemoral facing surfaces give
   the additional anterior relation once the patella is traced. Fibula is kept
   as its own candidate/landmark where present rather than allowed to steal a
   main-bone role.
7. Nominate the smaller structures through their own topology, appearance and
   relation to the established surfaces: cartilage along nominated articular
   surfaces; meniscal sections in the joint neighborhood; ligament candidates
   by paths and attachment neighborhoods; fluid-bearing connected spaces and
   adjacent fat/synovial tissue by their own separate readings. Specific
   anatomical scope and attachment warrants need primary-source grounding and
   visual calls before admission. A low-signal component is not a ligament merely
   because it lies somewhere in the joint.
8. Keep adjacent-slice/cross-view disagreement, partial visibility, and changing
   section component count. Separate acquisitions remain separate grids; common
   patient coordinates are an initial relationship, not registration proof.
9. Record source ownership and containment, then show each object's unchanged
   own signal with peers excluded from the view. Re-read disputed/unclaimed
   support with added context. Stop/next-round policy belongs to the explicit
   knee loop contract; no MR intensity subtraction is inherited from cell optics.

## Composition and build increments

The production entry consumes each decoded series once. A per-series measurement
result flows to candidate construction, profile readings and traces; a study-level
relation result consumes the series results. The renderer only consumes returned
records. Hamilton exposes meaningful transformation dependencies and observers;
one residual round is a DAG and the repeat/stop controller is ordinary explicit
orchestration. The current Hamilton observer's one production call does not yet
expose the future anatomical dependencies.

OpenSpec should add the anatomical capability/contracts and scenario tasks to the
existing change, without marking unbuilt tasks complete. First increment:
candidate boundary-profile atlas on the coronal/sagittal examples and throughout
their stacks. Second: supported bone contours, extent and named role warrants.
Third: facing-surface/intervening support including the axial progression.
Fourth: smaller object families one at a time and ownership/residual views.
Each increment produces a saved color-annotated image series, is run through the
real entry on all 58 before building the dependent step, and retains abstentions.

Hypothesis pins geometry, support and topology invariants; Detective pins pure
named decisions per current digest. NumPy/SciPy provide reference/library-shaped
operations; custom repeated loops get strict Numba twins under SAME. Profiling
and counted work determine where Rust/C are appropriate. No native backend or
speedup is claimed by this reading. OpenSpec/Hamilton validity does not establish
anatomical correctness.

## Questions for the workshop

* Is the first candidate construction framed correctly for both illustrated
  contrasts, without assuming brightest tissue is bone or making the whole leg
  a two-basin segmentation? Compare the concrete coarse-to-local-boundary route
  against the proposed two-plateau marker route as candidate generators only.
* What is the minimum complete measurement record needed to construct a supported
  boundary with explicit missing sections and to examine each warrant visually?
* Does the proposed dependence order hide a cycle, especially axial joint
  localization, role identity, cross-view alignment and smaller-object context?
* Which statements exceed the measurements, or accidentally turn a prior or a
  geometric check into anatomical authority?

These are workshop questions, not definitive blockers. The founder can correct
a misframing with the pictures and measurements beside the question.
