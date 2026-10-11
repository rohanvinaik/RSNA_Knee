# Resume the accepted object-resolution build

> ## ⇒ FIRST: `just unit`. It prints the build loop with the route's live state.

## The agreed sequence, settled 2026-10-11

Reached with the founder and two independent readers, after a reading put an unresolved design
question ahead of work whose production inputs already exist. **Dependencies decide the order.**

**1. Reconcile the accounting.** Three items, all bookkeeping rather than design, and each cheap:
   the boundary census is built, pinned, wired, rendered and run on real data but unchecked in the
   task list (**done** — task 2.5); `ROUTE` still carries the superseded SPINE stage names
   (**task 1.4, open**); and `docs/OBJECT_MODEL.md`'s laterality passage contradicted the spec
   (**done** — the frame fixes the axis, a witness fixes the sign).

**2. Complete OpenSpec task 3.8** — supported connectivity within bands and constrained contour
   shortening — through `just unit`. It is the next increment because it is **unblocked**: it
   consumes original boundaries, native profiles, conversation outcomes and the boundary census,
   and all four are already in production. Its own task text requires the contract for *what support
   licenses connection and movement* to be specified **before** implementation.

   **The milestone, worded carefully:** *one study's refined outline chains, with closure standing
   per chain and every arc's support shown beside the original.* **Closure is an observed outcome,
   never the acceptance bar** — a correct implementation may return an open chain, and requiring
   closure would invite inventing the missing boundary, which is the one thing this stage must not
   do. Gaps, shed places, clipping and competing subdivisions stay visible.

**3. Inspect the supported arcs and the remaining gaps with the founder.** Nobody has yet looked at
   how far a territory boundary actually sits from a cortical surface.

**4. Then the two tracks that are gated, each on its own question:**
   - **The anatomical inventory** (task 2.1) is gated on the founder's teaching. Its *form* may be
     proposed — identity, extent, boundary, internal structure, relations, standing — but which
     elements and what warrants each name are his, and the list is stated *before* any round is run
     against it. Cartilage, a meniscus and a ligament each need their own definition rather than
     inheriting the name of the space containing them.
   - **The lens stage** is gated on the knee's local structural normalisation. The founder's ruling
     settled the ordering and the tercile mechanism, not the normalisation itself, and Fable's
     levels consult establishes that the knee's analogue — the coil's S/I falloff — is
     **multiplicative on signal**, so the sibling's additive haze does not port. Measurements can
     inform that decision and cannot substitute for it. The `digit_code` low/high-edge correction is
     *independently settled* and may proceed on its own; it must not block 3.8, and it must not make
     the lens stage appear complete.

Today's teachings and what they settle: [`../03-lenses/teachings.md`](../03-lenses/teachings.md).

---

Start with [the continuing contract](object-resolution-contract.md),
[B2's evidence record](measurements/same-knee-conversation-b2.md), and
[the checked conversation contract](readings/b2-workshop-resolution.md).
The target is every significant knee element relevant to the twelve findings,
resolved cleanly and deterministically. Geometric territories and subdivisions
remain measurements on the way to those objects, with their anatomical meaning
and ownership still to be established.
The latest founder correction: same-orientation sequences read the same knee
and its objects. Do not carry over the cell instance's depth-nearness rule.
His blue/orange coronal example is a pointer to a general conversation, never
a pair-specific rule. The thesis supplies theory; the live cell build supplies
engineering guidance. Retain independent readings and use resolved boundaries
to clarify the other readings' ambiguities.

Recompute the latest increment's standing:

```sh
just interiors-status data/measurements/object-conversation-b2-v1
just conversation-status data/measurements/object-conversation-b2-v1
just conversation-picture-status data/pictures/object-toolkit/conversation-b2
just plan-status
just plan-next
just plan-check
```

The original B1 and B2 source, writer, serializer, verifier, environment, receipt
and artifact links are checked together. Read the complete status records and
their checks; never carry an earlier current/stale result into a later source
version. The canonical run retains the exact SAME proofs, telemetry, Hamilton
execution and per-study checkpoints.
`plan-status` checks planning artifacts; `plan-next` computes completed and
remaining implementation tasks. Planning artifacts being complete does not mean
the anatomical build is complete.

Staged photos are under `data/pictures/object-toolkit/conversation-b2/`: original
readings, transported donor bands, native outcomes, concurrent subdivision and
conditional subdivision. `series.png` compares all saved views, and `view-01.png`
onward gives every view its own five-panel image. The manifest binds the receipt,
arrays, source UIDs/planes, renderer and image hashes. The former B1 gallery and
[B1 record](measurements/geometric-interiors-b1.md) retain the preceding increment.

Resume at OpenSpec task 3.8. First inspect the coronal focus images: exchanged
bands follow the boundary within the originally merged territory, but leave
gaps. Contract closure, support and permissible movement before implementing
generic connected chains and constrained shortening. Keep original/refined
traces, open chains, shed places, all small pieces and clipping visible. Do not
close a gap by appearance alone or turn territory IDs into anatomical labels.
The [source trace](readings/same-knee-conversation-codex.md), checked workshop and
thesis guide that contract; the founder's example does not select its rules.

The material below retains Packet A's earlier evidence and correction history.

Read the latest [visual/exclusion clarification](readings/anatomical-lenses-workshop-resolution.md)
and the correction at the top of [the lead reading](readings/anatomical-lenses-codex.md)
before interpreting the earlier candidate proposal. The founder's original
red/squint argument is about spatially meaningful resolution of the surrounding
field: confident negatives actively constrain the objects. The old seam probe
partitions closed-leg support and must not be judged as an admitted bone mask.
The conceptual Fable workshop is saved beside those readings; it is not an
anatomical production result or design authority.

Read `../../BUILD_PLAN.md`, then `readings/object-resolution-toolkit-codex.md` in
full. Those are the accepted plan and its engineering index. `../../SPINE.md`
and the founder's teaching govern meaning. OpenSpec's `object-resolution-toolkit`
change carries the scenario contracts and atomic tasks.

The founder clarified during this build: orthogonality is constructed by
definition. Thesis §1.12 distinguishes the constructed orthogonality of claims
from the exact carrier-row orthogonality (§13.1). DICOM header coordinates are a
separate numerical interface. A header-format observation never changes either
construction or becomes evidence against it.

The founder also requires an actual image series at every distinct step. Use the
pipeline's returned records, with their source coordinates and unresolved places.
Do not substitute workbench segmentation. The requested progression is acquired
image → location/interior proposals → native profiles and supported chains → facing
surfaces → extent → own-object/residual views. Packet A supplies the measurement
foundation; B–D are the contour/relation/ownership packets in the accepted plan.

To recover state, run:

```sh
just plan-status
just plan-check
just packet-status data/measurements/physical-packet-a-v3
```

The last command computes receipt counts and whether saved source digests still
match, checks SAME's receipt/verifier/artifact links, and saves `status.json`.
Read its output, the complete receipt, SAME result and Detective report.
Never treat a prose checkpoint or an audit of an older snapshot as current state.
If digests changed, rerun the admitted packet and its SAME comparison.

Readings are in `readings/`; measured records are in `measurements/`. Bulk run
arrays and image series remain under ignored `data/`. The Fable audit is a
historical independent reading of the approved source snapshot; current source,
intent tests, receipts and gate outputs establish what now works.

The [Packet A measurement record](measurements/physical-packet-a.md) names the
exact run directories and visual manifest. The [Fable audit resolution](readings/packet-a-audit-resolution.md)
records checked fixes and remaining qualifications. The full approved audit text
and API metadata are beside it; its prompt stays under private `data/audits/`.

The corrected image series is `data/pictures/object-toolkit/packet-a-annotated/series.png`.
Red is the saved production background-split mask; cyan is profile support;
magenta is missing support. Its manifest links the v3 receipt and saved arrays.
The profile-only earlier gallery omitted the requested color overlay and is
historical. Do not resume from it as the admitted visual deliverable.

For an interrupted future run, read its `checkpoints/<study_uid>.json`. Each
checkpoint is atomically published after that study and includes request, source
snapshot, writer identity, saved records, and failures. Rerun a partial/affected
study with `--uid` into a fresh directory. A checkpoint is inspectable evidence,
not permission to claim a whole-corpus run or silently merge different snapshots.

Work through one OpenSpec task and its consumers at a time. Save the image series
and measurement receipt before marking that task done. The next visual packet
must retain candidate gaps, original/refined chains, shed places and clipping.
An unresolved boundary remains visible; the founder supplies the anatomical call.

Known tooling limits to recheck rather than work around silently: VizTracer on
this VERIFY interpreter did not observe project calls even with project filters;
the recorded fallback is cProfile. LintGate's exposed API has no requested
strictness argument. Matplotlib is deliberately supplied per renderer run, not
installed as a production dependency. Linux/Kaggle remains a separate deployment
proof.
