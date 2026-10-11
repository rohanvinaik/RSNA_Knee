# B1: lead reading and checked Fable workshop

The lead's pre-response reading is the B1 section of
`../object-resolution-contract.md`, written before the conceptual API call.
The response and usage metadata are saved beside this file. The payload was
abstract: no source files, pixels, reports or identifiers. The consultant is a
second reader, not authority on meaning or a design oracle.

The lead checked these questions against the contract and the installed primary
API docstrings (`h_maxima`, `watershed`), read whole:

* Distance has three possible bounding causes: measured low signal, missing
  acquisition, virtual frame. The contract already names all three. Added a
  returned `distance_guard` giving the cause chosen by SciPy's nearest-index
  rule at each search pixel. It does not assert that ties have one unique cause.
  Boundedness at acquisition edges is computational support, not false anatomy.
* Tie semantics are explicit: four-neighbor h-maxima at height ≥ h, whole peak
  plateaus, C-order four-connected labeling, watershed priority by value then
  queue insertion time. Versions are recorded. SAME is within one environment,
  not a guarantee that every other correct watershed implementation agrees.
* The distance approximation concerns rounded orientation, not a claim to know
  scanner geometry more precisely than the header. The saved conservative error
  bound covers the retained Gram metric's deviation from the orthogonal metric.
  Small changes in geometry may change hypotheses; no fixed anatomical verdict
  is licensed by a seed. No empirical orthogonality test is introduced.
* These are normals to directed pixel edges, with only four native directions.
  The measured interval is along that stated direction/window. It is not called
  cortical thickness or width orthogonal to an unknown anatomical surface.
* Profiles retain offsets, samples and support. Compare bilinear native values
  to the same existing split, not a newly chosen level. This is explicit rather
  than pretending bilinear scalar sampling interpolates a binary predicate.
* Profiles cross proposed peer territory using unchanged source values. Directed
  peer copies describe opposite normal directions; they are not independent
  votes. Unseeded means available above-split support with no seed in its
  connected component. Territory IDs belong to this plane, never another slice
  or acquisition by default. Continuation and anatomical correspondence are
  subsequent measurements.

Fable's proposed claim that using the frame/missing domain boundary necessarily
means false anatomy is not adopted: neither the contract nor the implementation
makes that interpretation. The cause is retained and can inform subsequent
reasoning. Likewise a minimum prominence of one spacing step is not an imposed
bar: the library accepts fractional physical prominence on discrete distances.
Its actual result is the measurement, not a promise to resolve smaller anatomy.

First production preview was visually read after saving: sagittal and coronal
territories expose the large bone-shaped interiors, and unsupported dividing
lines are distinct from observed low-signal bands. No tissue label, completed
contour, or full-corpus success is inferred from that one study. The next build
can use the readable interfaces, alongside slope, continuity and facing-surface
measurements, while retaining every other territory and unclaimed source.
