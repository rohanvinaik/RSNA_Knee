# What the current machinery actually does — the CODE facts

OpenSpec task 3.8a, first half. Every fact below is read from a production unit **whole**, located
with Serena, and quoted with its file and line. **No fact here is a measurement on an image**: the
run facts are a separate half of this task and are not in this file, because a reader can establish
what the code does and only a run can establish what the data does.

Why this exists: both second readers refused the lead's completion bar, and a third found that the
convexity argument for the ported shape prior describes an update the sibling does not perform. Each
of task 3.8's four terms turned out to rest on a property of the machinery that nobody had measured.
Declaring the contract first would have written those terms from a reconstruction.

---

## 1. What the distance transform's `interior` admits

**A convention, and why.** Every quotation below is in a `text` fence, never a `python` one, and
carries its source's own indentation. A `python` fence is reformatted by this repository's own ruff
settings, which silently rewrites the quotation — and a quotation from the sibling repository, which
writes to a different line length, can never satisfy them at all. The gate caught exactly that on the
first version of this file, where several quotes had been reflowed and were therefore not what the
source says.

`src/knee/objects/interiors.py:150-267`, `read_interiors`:

```text
    available = np.isfinite(plane)
    dark = (
        available & (plane <= split)
        if np.isfinite(split)
        else np.zeros(plane.shape, dtype=bool)
    )
        ...
        interior = available & ~dark
        padded = np.pad(interior, 1)
        distances, nearest = ndi.distance_transform_edt(
            padded, sampling=spacing, return_indices=True
        )
        ...
            labels = watershed(
                -distance, markers, mask=interior, connectivity=1
            ).astype(np.int32)
```

**The interior EXCLUDES dark.** It is the finite places strictly above the series' background split
— neither an admitted bone mask nor a separately resolved leg mask. The EDT is taken on it and the
watershed is masked by it.

**What that settles.** A constructed divide is a place where two **non-dark** interior places are
4-adjacent across it. So a divide exists only where the interior is *connected across* — through
continuous tissue, or through a bright bridge in an otherwise dark line. It is **never "a divide in
the middle of a dark cortical gap, on neither bone's surface"**, which is what an earlier lead
reading claimed and the lead carried into the consult brief. The second reader flagged exactly this
as undetermined and said it had to be settled before his Q2 meant anything
(`central-pull-fable.md`, point A). It is now settled, in his favour.

**What it leaves open, as a run fact.** Whether the interior leaks across a notch mouth or a bright
joint space, joining two bones into one territory — possible by construction on a fluid-sensitive
series, where the joint space is bright.

## 2. The guard that says WHY a distance is what it is

Same unit:

```text
        causes = np.pad(
            np.where(dark, 1, np.where(~available, 2, 0)), 1, constant_values=3
        )
        distance = distances[1:-1, 1:-1].copy()
        distance_guard = causes[nearest[0], nearest[1]][1:-1, 1:-1].astype(np.uint8)
        distance_guard[~interior] = 0
```

and the docstring: *"The outside guard is a computational bound, never an acquired dark reading."*

Each place records whether its distance is bounded by **dark** (1), by **unavailable** (2), or by the
**padded frame** (3). A territory whose centre is frame-bounded has a depth that is an artefact of
the picture's edge, not of anatomy — and the code already distinguishes the two. Nothing in the
contract discussion had this.

## 3. Whether a loop is read per slice or through the volume

`src/knee/objects/analysis.py:87-201`, `measure_series`:

```text
    index = (
        len(series.volume) // 2 if request.slice_index is None else request.slice_index
    )
    ...
    plane = series.volume[index]
```

**One 2D plane per series, defaulting to the middle slice.** The squint, the EDT, the watershed, the
territories, the boundary profiles and the census all run on that one plane. Loops are per-slice.

**What that settles.** The second reader's through-plane bound on how far a cortex can be missed —
a surface at angle φ crosses a slab of thickness T over an in-plane length `T·cot φ`, unbounded as
φ → 0 — concerns a dimension this pipeline does not currently traverse. And his strongest form of
the "could the instrument have missed it" licence, corroboration of a span at z±1, **is not
available without new work**. The slab thickness itself *is* captured and carried
(`slice_thickness_mm`, from the header), so the number exists even though the analysis is 2D.

## 4. Whether the flicker is read at the place or once per series

`src/knee/collapse/regime.py:53-84`, `RegimeKey`: `dark: float`, `dark_count: int`, `bright: float`,
`bright_count: int` — **scalars, one per series**, and the docstring: *"Every reading is in the
series' own stored values unless named otherwise."* Raw stored intensity; not per place, not
physical.

And `find_referencing_symbols(RegimeKey)` returns **only** `src/knee/pipeline.py` (as
`SeriesRun.regime`) and `regime.py` itself. Nothing in `knee/objects/` references it. The one
regime-derived value that crosses into the object stage is the histogram valley,
`src/knee/pipeline.py:99`:

```text
                else measure_series(
                    series,
                    analysis,
                    background_split=key.background_split
                    if key is not None
                    else float("nan"),
                )
```

**So no flicker, noise figure or movement allowance of any kind reaches the contour machinery
today.** There is no allowance to consume, and none to be wrong.

**What that settles.** The second reader proved by chain rule that a variance-stabilising
composition confers no width the raw `flicker / slope` ratio lacks (to first order); what it buys is
making **one global** noise figure valid at every intensity. The knee's figure *is* global. So his
conditional resolves to the global branch: a per-series scalar cannot be "the flicker of the light
there", and the band would be wrong place by place by the ratio of the true local noise to that
scalar. Either the composition is done, or the flicker is read at the place, or the contract may not
promise a **measured** allowance. That is a question for task 3.8, and it is now a decision with a
known premise rather than an open one.

## 5. Whether any dark reading is made that is not on a loop

`read_interiors` returns `handed_on(dark)` — the **whole plane's** boolean mask of places at or below
the split — alongside the per-boundary-point readings `lower`, `upper`, `trace` and `codes`.

**Yes.** The full-plane dark mask is retained on the reading; the bracketed intervals on the loop
points are an *additional* reading. So if a territory swallows a notch, the notch walls are still
recorded in `dark` — they are simply not typed as anyone's boundary, and nothing consumes them. The
second reader's proposed law for that case — *a dark reading found inside a territory is kept as a
finding about that territory, never discarded* — is already satisfied by the data the stage returns;
what is missing is a consumer.

## 6. What the sibling's chord step actually moves a point onto

`~/Projects/Kaggle_Killer/competitions/cell_tracking/src/cell_tracking/cassette/outlines.py:337-346`:

```text
def _on_the_chord(loop: np.ndarray) -> np.ndarray:
    """Each point's nearest place on the straight line between its two neighbours: where it makes
    the loop shortest while moving least."""
    before, after = np.roll(loop, 1, axis=0), np.roll(loop, -1, axis=0)
    chord = after - before
    span = (chord * chord).sum(axis=1)
    along = np.divide(
        ((loop - before) * chord).sum(axis=1), span, out=np.full(len(loop), 0.5), where=span > 0
    )
    return before + np.clip(along, 0.0, 1.0)[:, None] * chord
```

**The orthogonal projection onto the segment, clamped to it — not the neighbours' midpoint.** The
midpoint appears only as the degenerate fallback when the two neighbours coincide (`span == 0`).

Checked against the counterexample: neighbours (0,0) and (4,0), point (0,1). `chord = (4,0)`,
`span = 16`, `(loop − before)·chord = 0`, `along = 0`, clipped to 0, so the target is **(0,0)** and
the half-step gives **(0, 0.5)**. A midpoint step would give **(1, 0.5)**.

**What that strikes.** The convexity argument the lead reported — that chord-plus-clamp is projected
gradient descent on `Σ|p_{i+1} − p_i|²`, hence a rate-independent minimiser that can be *stated* as a
contract — is a property of the midpoint update, and the sibling does not perform it. **The
least-squared-segment-length minimiser, the rate independence, and "chord-only can be written as a
specification rather than a procedure" are all withdrawn.** The `cos²(κ/2)` decay inherits the same
defect; whether it survives linearised about a nearly-straight trace, where the perpendicular foot
and the midpoint agree to first order, is the lead's conjecture and is **not established**.

Two further properties of the real operation, which the midpoint reading hid: the clamp to `[0,1]`
means a sharply folded point moves toward a **neighbour**, never past it; and the step is purely
transverse for a straight-ish run, so it does not redistribute spacing along the trace the way a
midpoint step does.

## 7. The real vocabulary is two typings, and it has five kinds, not three

`src/knee/objects/interiors.py:21-36`:

```text
TRACE_CODES = {
    "bracketed": 1,
    "no_dark_bracket": 2,
    "multiple_brackets": 3,
    "missing_profile": 4,
    "frame_clipped": 5,
    "empty_profile": 6,
    "invalid_measurement": 7,
}
EDGE_KINDS = {
    "low_signal": 1,
    "peer_territory": 2,
    "acquisition_missing": 3,
    "frame": 4,
    "unseeded_available": 5,
}
```

An arc carries **two independent typings**, not one: what lies **across** it (`EDGE_KINDS`, set in
`boundary_edges`, lines 89-93) and what the profile cast across it **found** (`TRACE_CODES`, decided
in `dark_bands` through the pinned `border_code`). They are not the same question, and
`dark_bands:128` sets a position only where they agree: `good = codes == TRACE_CODES["bracketed"]`.

So the brief's three words — *supported, constructed, absent* — collapsed a 5 × 7 vocabulary that is
already built, already pinned, and already rendered (the B2 legend's `native_open: 252`,
`native_missing: 49`, `native_multiple: 20` are these codes). An edge can lie against dark and still
fail to bracket. **Neither second reader could have known this, because my brief did not contain it.**

**And one kind nobody has discussed: `unseeded_available`.** An interface whose neighbour is finite,
above the split, and belongs to **no territory** — interior tissue the watershed left unclaimed,
which happens wherever a connected component of the interior holds no marker. A territory can border
material that is neither another object nor background nor dark. That is a fourth class of arc, it
has an implemented code, and the contract must say what it licenses.

## 8. There are no chains yet

`boundary_edges:71-102`, whose docstring is *"All directed four-neighbor interfaces"*:

```text
    for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
        neighbor = padded[
            1 + dr : 1 + dr + labels.shape[0], 1 + dc : 1 + dc + labels.shape[1]
        ]
        rows, cols = np.nonzero((labels > 0) & (neighbor != labels))
        ...
        points.append(np.column_stack((rows + dr / 2, cols + dc / 2)))
```

The stage returns a **concatenated, unordered set of directed interface points** at half-place
offsets — one per (place, direction) crossing a label change. **Nothing orders them into a curve.**
There is no loop, no traversal, no neighbour-along-the-trace.

**What that strikes.** The whole discussion — mine and both readers' — assumed a closed loop whose
*support typing* was dotted, and asked when a gap in it may be completed. That is not the object the
code holds. The capability is named `supported-contour-chains`, and **the chains do not exist**: the
first thing the operation must do is build ordered chains out of an unordered directed-edge set, and
that is where "what support licenses a connection" actually bites — not as *may I bridge a gap in a
curve*, but as *which of these interface points join into one ordered arc at all*.

It also makes the sibling's analogy weaker again, in a new way: `borders_of` runs marching squares on
a filled mask and gets ordered closed loops for free. This stage never produces one.

---

## On the four facts a second reader supplied

All four were checked here against the units rather than adopted: the interior's content, the single
2D plane, the scalar noise with no allowance consumed, and the retained full-plane dark mask. **All
four hold.** The third is stronger than stated — it is not merely that the contour path does not
consume a pointwise allowance, but that `RegimeKey` has no referencing symbol anywhere in
`knee/objects/` at all.

## What this half does NOT establish

Whether a place outside the leg can be typed supported; the inter-arc gap lengths; whether the
interior leaks across a notch mouth on a real series; and the knee's ceiling in physical units. All
four are run facts or the founder's, and none is in this file.
