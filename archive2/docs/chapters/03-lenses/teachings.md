# Chapter 3 — the founder's teaching, verbatim and dated

His words, in the order given, never paraphrased. Where a ruling answers a question the lead put to
him, the question is quoted too, so the ruling is legible on its own.

---

## 2026-10-11 — THE STATIC MIDDLE: tercile edges, after a local structural normalisation

**The question put to him**, after both oracles were read whole on the single question *what is a
digit written against?* (`readings/the-static-middle.md`), and after both second readers had
independently proposed something different (`readings/witnesses-codex.md`,
`readings/witnesses-fable.md`):

> "Does the knee take **tercile edges after a local structural normalisation** — the thesis's and
> the sibling's mechanism, where the haze-analogue absorbs coil falloff *because it's local* — or
> **witness-tissue middles**, as both second readers proposed?
>
> My inference, labelled as mine: the first subsumes the second, and the tissue conjunction then
> lives in the rows *across acquisitions* rather than in the middle. If that's right, `witnesses.py`
> becomes a small thing — structural selection of which places enter a population — and the
> three-fat-witness apparatus mostly dissolves."

**His ruling, verbatim:**

> "Your inference is correct"

### What that settles

1. **A middle is a pair of edges at the terciles of a structurally selected population** — §7.2's
   shape, which the sibling implements as `np.quantile(finite, (1/3, 2/3))` with **both edges in the
   0 row**. Not a centre plus a band.
2. **The spatial problem is solved before the digit, never by the middle.** The local structural
   normalisation comes first; the middle then carries no spatial correction at all.
3. **The tissue conjunction lives in the rows across acquisitions.** "Fat = bright(non-FS) ∧
   dark(FS)" is two rows against two per-series middles, conjoined — never one row against a named
   fat witness.
4. **`witnesses.py` as designed is withdrawn**, with the three-fat-witness apparatus and the
   per-witness spread that entered the band. What survives is the small true thing: structure
   selects which places enter the population; the distribution's own terciles then set the edges.

**Historical implementation annotation, at this ruling (2026-10-11):**
`knee.lenses.digits.digit_code` then had the wrong shape against the oracle — it takes a
`witness_middle` plus a band computed from spreads. Nothing consumes it (verified by
`find_referencing_symbols`: test callers only), so the cost of correcting it is one pinned module.
Its *silence* rules were retained. The later candidate replaces this shape with low/high
edges and is connected by `read_lenses`; see this chapter’s README for current evidence.
The founder’s quotation and ruling above remain unchanged.

### What his ruling did NOT settle, recorded so it is not assumed

He confirmed the reconciliation. He did **not** specify the knee's local structural baseline itself.
What the record already holds is Fable's levels consult
(`chapters/02-collapse/readings/there-is-no-level-map.md`): the haze analogue is the coil's S/I
falloff, read as a running median of the foreground, **but multiplicative on signal**, so additive
subtraction is the wrong operation — "it is a reading handed on, and what it leaves is a sheet."

Two rulings that chapter raised are still open: **valleys or terciles** for a series whose foreground
is multimodal (his ruling here settles terciles as the shape; whether a valley reads them better in a
multimodal series is a separate question), and **values or digits into the stack**.

---

## 2026-10-11 — ON THE PROJECT'S LICENCE TO EXPERIMENT

> "Remember, knee images are WAY easier than cells, so we can be licensed to fuck around a lot more"

Taken as it reads: a measurement that is read-only, cheap and reversible is run rather than proposed.
It does not license reading *meaning* off what comes back — that remains his.

## 2026-10-11 — ON THE WORKFLOW ITSELF

> "Cleanliness is the next thing to godliness."

> "What we need to do is make sure that everything is built in the proper, SICP-style clean code,
> everything in its own, correct place, everythig registered and consuming/consumed by the main
> production pipeline, with photo output at every state. The full process, the full workflow of the
> project, managed diligently."

> "Remember, every step should produce an image output"

Recorded as the loop in `docs/STAGE_CONTRACT.md` and made runnable as `just unit`, at his request
that the workflow become something reached for naturally rather than remembered.
