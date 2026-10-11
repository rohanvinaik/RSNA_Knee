# Chapter 2 — `collapse`. Where it stands.

For the accepted object-resolution toolkit build and an interrupted-session handoff,
start at [RESUME.md](RESUME.md), [the build index](../../BUILD_PLAN.md), and
[B2's evidence record](measurements/same-knee-conversation-b2.md). The
[continuing contract](object-resolution-contract.md) and
[same-knee conversation reading](readings/same-knee-conversation-codex.md) record
the founder's latest guidance. Compute current
standing with the commands there. The earlier readings and noise-law history below
remain context; their past measurements are not current status.

The continuing target is every significant anatomical element relevant to all
twelve findings. The implemented increment exchanges original same-knee boundary
readings through the read-once production route, returning separate concurrent
and conditional subdivisions. All territories, unsupported divisions, source
bands, disputes and missing support remain accessible. Its staged photos and
per-view comparisons are in `data/pictures/object-toolkit/conversation-b2/`.
The next operation is supported chain closure and constrained refinement
(OpenSpec task 3.8), before facing surfaces, extent and anatomical ownership.
The coronal example guides inspection; the theory and live cell implementation
guide the general mechanism.

**Read this first** in a new session or after a compaction. Then `teachings.md` for the founder's
words verbatim, then `design.md`.

Figure 8's text for this stage is in `src/knee/collapse/__init__.py`.

---

## What this chapter is for, in one line

**Resolve the femur, resolve the tibia, resolve the joint space between them — structurally and
deterministically — so that diagnosis becomes reasoning over how the two objects sit relative to
each other.**

The founder, 2026-10-10: *"Knees are two objects that combine... An injury is a breakage, an issue
in the way they sit in one another."*

Every one of the twelve findings is a deviation in that relation:

| | the findings |
|---|---|
| the objects themselves | Fracture, Contusion |
| the space between them | Medial / Lateral / PF OA, Effusion, Synovitis |
| what maintains the relation | Medial / Lateral Meniscus, ACL, MCL |
| fluid leaving the space | Baker's cyst |

## Earlier object/seam mechanism discussion

This section preserves the earlier discussion. It is not the implemented B1
contract or a settled specification for B2. In particular, B1's geometric
prominence markers measure proposed interiors, not anatomical identity, and
the sibling's `read_dips` is not a supplied 1D knee-seam implementation. Follow
the current contract and source traces above when building.

1. **Close the leg.** Air is what connects to the frame's border, after a morphological opening at
   the tile scale; the leg is the rest, with its holes filled. Two fills, both answering only
   *inside or outside the body* — never tissue against background. Fill the **mask**, never the
   **values**, or a fracture disappears from the representation.
2. **Read the superior–inferior axis from the header**, never from the pixels. In-plane for
   sagittal and coronal; **along the stack normal for axial**. The frames are visibly rotated, so
   image rows are not the anatomical axis.
3. **Markers from anatomy, not from maxima.** Profile the leg's central third along that axis;
   the sibling's `read_dips` **in one dimension** gives two broad plateaus and the deepest dip
   between them, in noise units. Seed a marker-controlled watershed with exactly those two plateau
   interiors. *A basin is evidence, never identity* — all three sources said so independently.
4. **The seam is the saddle set between the two basins**, as a curve with a depth profile — the
   joint line, found as a *relation between two objects* rather than hunted by intensity.
   It is also **the registration landmark**: align seam to seam.
5. **Two weightings, one algorithm, a told sign.** The sign comes from the header's
   fluid-sensitive flag. But the seams measure different tissue and stay **two columns**: the
   anatomy valley is the cortex-to-cortex interval; the fluid-sensitive ridge is cartilage and
   fluid only, flanked by two cortical dips. Their width difference (≈ 2× cortex + menisci) is the
   **check that they are the same seam**, and their **disagreement is where the information
   lives**.
6. **Per place, the digit pair names the tissue** — fat (+,−), fluid/oedema (0/−,+), cortex and
   meniscus (−,−), cartilage (0,+). Two lenses conjoined name what neither names alone.

Detail and quotations: `readings/resolving-the-two-objects.md`, `readings/the-dome-and-the-seam.md`.

## Earlier noise-law build record

| module | what it is |
|---|---|
| `codes.py` | the chapter's pure decisions — five, all Detective-converged COMPLETE |
| `noise.py` | the noise law per series: background population, channel count from the background's **quartile** ratio, a dark estimator, and a bright estimator reading the noise **floor** among local blocks with its sampling bias derived and corrected |
| `units.py` | the variance-stabilizing transform (Rician / noncentral chi), tabulated per series |
| `regime.py` | the regime key — the cheap whole-field readings taken once per series |

## Earlier noise-law measurements and their traced reason

Over all 336 series the two noise estimators concur on **4**. The ratio between them flipped from
5.5× to 0.2× across a rebuild, so the instrument moved and the disagreement did not resolve.
See `measurements/the-noise-law-fails-on-real-data.md`.

**Do not resume by trying a fifth intensity instrument.** Four have failed, each for a different
reason, and they are listed in `teachings.md`. These are objects, not intensity classes.

The founder's ruling is outstanding. The three options put to him:
1. keep refining the background instrument;
2. accept that the dark estimator works only where a clean background exists, and let abstention
   carry the rest — so concurrence becomes a **reading about comparability**, not a target;
3. make the bright estimator primary and the dark its check.

## Earlier questions retained for context

1. the noise law's three options above;
2. **valleys or terciles** for a middle's edges, and **values or digits** into the stack;
3. what the per-slice N table should be where it is uncertain (the femur forks at the joint in
   coronal; patella and fibula enter by slice position).

## A claim withdrawn

It was said that *"there is no background noise in this corpus to measure."* That came from **three
rendered series** whose air was nearly all zeros. The 336-series run reported **18.8%**
`background_masked`, not 100%. The corpus-wide air distribution has not been measured.

## Vocabulary, so the next chapter does not inherit a collision

- **Chapter** — a row of SPINE's table, one package under `src/knee/`.
- **Stage 0–4** — the thesis's own numbering for the *loop's* stages (§5). It belongs to chapter 3
  (`loop`), **not** to this chapter.
- The parts of this chapter are named, never numbered: **the noise law**, **the transform**, **the
  regime key**, **the objects and the seam**. Earlier notes called these "stage 1/2/3"; that
  numbering is retired because it collided with both of the above.

## Where everything is

| | |
|---|---|
| `teachings.md` | the founder's words, verbatim and dated, including the four failed instruments |
| `design.md` | the chapter's design, with provenance per element |
| `readings/` | what the oracles say — the thesis read, the sibling build traced, the second readers |
| `measurements/` | what was measured on the real corpus, through Chapter 1's entry point |

**The readings are the oracle's; the measurements are the corpus's.** A reading never substitutes
for a measurement, and state is computed from code, tests and git — these say what was measured and
what it meant.
