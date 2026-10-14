# Packet A: the lead's reading before the external code audit

2026-10-10. This reading precedes opening Fable's code-audit answer. The earlier
`compute-build-codex.md` preceded the plan consultation. Neither reader assigns
anatomical meaning or changes the founder's theory.

The implemented measurement route uses Chapter 1's already decoded series. Its
stored dtype and per-plane geometry survive. The native bilinear loop reads only
positive-weight contributors, in a fixed order shared by the reference and Numba.
Support means an acquired coordinate with finite positive-weight contributors;
it is deliberately a conjunction of geometric and finite-value support. Separate
geometric and missing-value reasons may be useful to later packets, but their
absence is not an inconsistency with this declared meaning.

The frame's basis is the original rounded DICOM basis with row/column spacing.
Its inverse uses a pseudoinverse. The profile wrapper, however, assumes physical
row/column axes are Euclidean orthonormal. The series adapter currently obtains
direction components by dot products. Rounded or slightly nonorthogonal axes
therefore need a precise metric statement: exact patient millimetres do not follow
from nominal spacing alone. An explicit affine step with its physical length can
settle this without reorienting or resampling the source image. I will test that
identity rather than install an anatomical tolerance.

The numeric plane validation admits float16 and extended floats, although Numba
may not. Backend admission must be explicit before compilation. Invalid settings
also ought to fail before an unavailable in-plane axis can hide them. Read-only
NumPy outputs prevent ordinary consumer writes; this is a cooperation contract,
not protection against a caller deliberately re-enabling its owned buffer.

The saved receipt already contains request settings, source-file hashes, array
shape/dtype digests and environment versions. It still needs the selected source
plane's identity, verification linkage, backend-not-invoked standing, and a source
snapshot taken before execution. Hashing is a separate file read, so the proven
read-once claim is one pixel decode per series, not one byte read per file.

The graph executes one production study node and derives observations from its
returned records. It does not expose every internal kernel as an independent DAG
node. The integration test currently exercises the unavailable-axis branch; a
measured branch must also witness graph sample counts. The existing SAME proof
covers saved profiles within this environment; it does not prove platform-wide
bit equality, anatomical boundaries, all compiler versions, or every input dtype.

My audit questions are those contracts and their real consumers. Native C/Rust
admission remains a computation-shape decision backed by telemetry and SAME.
Nothing in this packet licenses a new knee classification bar.
