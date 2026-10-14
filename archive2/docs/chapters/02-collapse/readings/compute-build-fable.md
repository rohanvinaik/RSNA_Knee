# Historical Fable plan consultation

The lead reading `compute-build-codex.md` preceded this independent answer. This is a plan consultation, not a source audit or design authority. The completed CLI response below supersedes the initial API answer that ended at its token limit. No competition pixels or reports were sent.

**Scope note.** I read as an external checker of the written contract only; where I propose a definition it is the *form* of what must be pinned, not the choice itself, and nothing below assigns anatomical meaning.

## A. Demonstrable defects (the text as written admits divergent correct implementations)

**A1. Index↔LPS map is only half-pinned.** The text fixes triplet→index direction but not (a) whether ImagePositionPatient is the *center* of pixel (0,0), (b) which PixelSpacing element pairs with which triplet (the attribute lists row spacing first, so the first triplet pairs with the *second* spacing value), (c) the phrase "column-index direction" (direction along which the column index increases vs. the direction of a column). Any axial, square-pixel, square-image fixture passes a transposed implementation.
*Remedy:* write the forward map as a formula in index terms with named attributes and element indices.
*Proof:* fixture with anisotropic spacing, non-square image, obliquely rounded cosines; the physical position computed for pixel (r,c) samples that pixel with exactly one positive weight; inverse returns (r,c).

**A2. "Rounded cosines retained; inverse projects to same plane" has no tolerance and no stated operator.** Retained rounded triplets are not exactly orthonormal and their cross product is not exactly unit, so "unit normals" is a *derived* quantity. Whether the inverse is a true 3×3 inverse or a transpose decides whether round-trip drifts.
*Remedy:* declare which columns of the frame are raw vs derived, the inverse operator, the round-trip tolerance (index units), and record the non-orthogonality residual in the record rather than silently re-orthogonalising.
*Proof:* property test over cosines rounded to DICOM string precision: forward→inverse of the four corner pixel centers within tolerance, out-of-plane component within tolerance.

**A3. "Exactly axial" is not a robust degeneracy test under retained rounding.** A plane whose cosines differ from axial by rounding noise gives a tiny nonzero projection whose direction is noise; a bitwise-zero test accepts it as available.
*Remedy:* state the degeneracy criterion as an explicit numerical magnitude (derivable from the retained decimal precision — numerical, not anatomical) and store the projected magnitude in every record.
*Proof:* exact-axial, axial-plus-rounding-noise, and known-tilt fixtures → unavailable, unavailable, available with magnitude = cos(tilt).

**A4. Offset semantics after projection are undefined.** If a requested axis is projected in-plane and renormalised, "physical offsets" along the in-plane vector are not offsets along the requested axis. Whether out-of-plane requests are projected or rejected is unstated.
*Remedy:* state offsets are along the recorded in-plane unit vector; record that vector and the retained fraction; state accept/reject rule.
*Proof:* linear-ramp image on a tilted plane; measured slope equals the known gradient component along the recorded vector.

**A5. "Rectangle" is undefined.** Pixel-center rectangle [0, n−1] or pixel-extent [−0.5, n−0.5]? Behaviour at coordinate exactly n−1 (zero-weight neighbour n is out of bounds) is unspecified and interacts with the zero-weight rule.
*Remedy:* define support as *all positive-weight neighbours in bounds*; zero-weight neighbours are neither read nor checked.
*Proof:* boundary samples at 0, −ulp, n−1, n−1+ulp on both axes, both backends.

**A6. Support vs validity precedence, and aggregate derivation, are unspecified.** Can "complete support" coexist with invalid count > 0? Is an inside sample with a positive-weight NaN neighbour "supported"? "Empty" vs "no" is undefined. How is the aggregate code derived from mixed per-profile codes?
*Remedy:* support purely geometric, validity purely value-based, both counted independently; per-profile code as a stated function of (offsets, supported); aggregate as a stated function; emit a per-sample code array (unsupported / invalid / ok) — downstream slopes and any later chain cannot distinguish the two NaN causes otherwise.
*Proof:* enumerated truth-table test over every (support × validity) combination, per-profile and mixed-aggregate.

**A7. The zero-weight rule requires a branch, not a weighted sum.** 0×NaN = NaN, so a vectorised reference violates "zero-weight nonfinite neighbours do not invalidate" while a branching JIT satisfies it; SAME would fail or, worse, the reference would be wrong. Also a weight of 1e−17 is "positive", so classification flips on 1-ulp coordinate differences; the index-coordinate arithmetic must be bit-identical in both backends.
*Remedy:* reference is a scalar loop with identical operation order; strict `> 0` test on identically computed weights.
*Proof:* poison test (every non-dependent pixel NaN; sample stays finite; dependency count 1/2/4 at node/edge/interior) — this also substitutes for the unobservable "≤ 4 reads" claim in the JIT; near-node ±1-ulp fixtures compared bit-exactly.

**A8. SAME "values" and numeric domains are unspecified.** Bit-exact or tolerance? Output dtype and intermediate precision across uint8/uint16/int16/float32 inputs? Critically, CPython and Numba differ on NumPy *integer scalar* arithmetic (unbounded int vs wrapping), so any integer-domain intermediate breaks SAME.
*Remedy:* declare bit-exact comparison (bit view + NaN mask + signbit), float64 intermediates after explicit conversion, fixed output dtype, flags included.
*Proof:* SAME matrix over input dtypes including negative int16; include a constructed value set where fused multiply-add differs from separate multiply/add, to catch contraction.

**A9. Primitives with known backend divergence are not pinned.** floor vs `int()` truncation for negative coordinates; median even-count and NaN propagation; min/max NaN propagation; sort NaN ordering; rounding of physical tile extent to index extent; division by zero (Numba `error_model` unset: raise vs inf).
*Remedy:* each becomes a named primitive pin with chosen semantics; set `error_model` explicitly.
*Proof:* pins executed against both backends; degenerate inputs (zero-length direction, zero-size tile) return the same named code in both, never exception-in-one/inf-in-other.

**A10. Ragged squint quantities are undefined.** Median of what set, NaN treatment, coverage denominator (requested physical area vs native clipped count), border clipping (ragged or unsupported), tile anchoring (center/corner at what point).
*Remedy:* define each; emit the exact index slices used as "native bounds".
*Proof:* interior/edge/corner tiles with hand-computed expectations.

**A11. Slope is undefined.** Stencil or least squares? Over the supported subset (shifting baseline) or unavailable under partial support? Unsorted/duplicate offsets?
*Remedy:* state formula, missing-sample rule and its code, and that offsets are used and recorded as given.
*Proof:* ramp fixture exact slope; partial-support fixture gives the stated outcome.

**A12. Input-array contract conflicts with the scratch bound.** Numba needs native byte order and contiguity; DICOM arrays may be big-endian; any conversion copy is image-proportional, violating "scratch ∝ profiles×offsets". "Native" is undefined if Chapter1 applies rescale or photometric inversion.
*Remedy:* state preconditions (dtype set, native order, C-contiguous, value domain) enforced by a named error; state which array (stored vs rescaled) is measured and digested; pass a non-writeable view into the JIT so "source unchanged" is type-enforced, not hash-inferred.
*Proof:* non-native-endian and Fortran-order fixtures raise without allocation; tracemalloc for reference, peak RSS on the actual route for JIT.

**A13. Receipts cannot reproduce the measurement.** Listed fields omit the settings (tile size, offsets, direction, requested axis, anchor positions), the selected plane's identity, compiled signature, and cache state; "array digest" preimage must include dtype/shape/byteorder.
*Remedy:* enumerate receipt fields; digest over (dtype, shape, canonical bytes).
*Proof:* receipt + data/ alone regenerates identical digests.

**A14. "Once" is contradicted by source-file hashing and per-plane geometry.** Hashing requires re-reading bytes; IOP/IPP/PixelSpacing per plane require headers Chapter1 may not retain.
*Remedy:* define "once" (pixel decode) and have Chapter1 expose hashes and per-plane geometry at load.
*Proof:* file-open counter around `open_and_run`.

**A15. "Middle acquired plane" is undefined** for even counts and for the ordering key (instance number vs spatial vs acquisition time).
*Remedy:* state key and tie rule; record the chosen plane identifier.
*Proof:* even-count fixture; fixture with instance order permuted relative to spatial order.

**A16. Read-only outputs that are views do not protect their base.**
*Remedy:* outputs own memory or base is also flagged; add flags to SAME.
*Proof:* `writeable` False, base None or non-writeable, write attempt raises.

## B. Questions (may be fine; the text does not let a reader decide)

**B1.** Do optional analysis records leave existing regime readings bit-identical? *Proof:* golden digests with/without the option.

**B2.** Do Hamilton nodes each call `open_and_run` (multiple loads in the dev DAG)? Which ImportLinter contract forbids production→Hamilton, and does deptry classify Hamilton as dev-only? *Proof:* contract files plus digest equality between Hamilton-consumed and directly returned records.

**B3.** Are Linux/Kaggle digests expected to equal macOS digests, or is cross-environment equality a declared non-goal? Does provenance record Numba/LLVM/NumPy versions, host CPU target, and cache hit/miss/write-failed (read-only filesystems make caching fail with only a warning)? Is nopython enforced, and does Numba absence raise a named error? *Proof:* absence-simulation test; provenance field list.

**B4.** CrossHair cannot analyse compiled code; which claims does each tool cover (CrossHair/Hypothesis on the reference, SAME as the Hypothesis property)? *Proof:* a coverage map of claim→tool.

**B5.** Are non-unit "unit normals" normalised or rejected, with what tolerance? Are requested axes other than SI accepted? *Proof:* validation tests.

**B6.** Is `nogil` intended for concurrent calls? If so, scratch must be per-call and aggregates deterministic. *Proof:* concurrent vs serial equality.

**B7.** Are A's record schemas versioned so later packets extend without invalidating A receipts? (Assignment semantics stay yours; only the versioning is asked.)

**B8.** Rust/C admission says "measured" — which profiler record on which route, stored where?

**B9.** In the first demonstration, are anchor positions explicit recorded settings (whatever they are)?

**B10.** Which header fields, if any, enter committed receipts? (Your decision; the text is silent.)
