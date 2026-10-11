# Build plan

## Authority and navigation

The founder's decisions, `docs/SPINE.md`, and the chapter teaching govern the build. The accepted Chapter 2 reading is [`object-resolution-toolkit-codex.md`](chapters/02-collapse/readings/object-resolution-toolkit-codex.md); the compute decisions are recorded in [`compute-build-codex.md`](chapters/02-collapse/readings/compute-build-codex.md). The tracked proposal, design, scenario contract, and atomic tasks are in [`object-resolution-toolkit`](../openspec/changes/object-resolution-toolkit/).

For each chapter, read the thesis section in full and trace the cell project's source and production callers. Write the lead reading before asking Fable for an answer. State the atomic contract and its consumers before implementation. Intent and property tests precede the reference implementation. Detective applies to pure named-code decisions through the local `just detective` wrapper; report standing per current digest. Numeric array loops are not automatically pinned. Compare an accelerated twin to its reference with exact SAME requirements and refuse a required backend that is unavailable. Run through the real corpus from Chapter 1, inspect saved-record visuals, and keep profiler behavior and counted work separate. The lead compares Fable's external audit as independent evidence, not as warrant. Finish with `just gate`.

## Work packets

The founder's clarification in this build governs the reading: orthogonality is
constructed by definition, not established by empirical correlation. Thesis §1.12
describes the orthogonality of claims; §13.1 supplies the exact carrier construction.
The DICOM coordinate adapter is a separate numerical contract.

**A — Physical measurements.** Establish the DICOM patient frame, ragged physical squints, and native bilinear profiles. Keep a Python reference and an exact Numba SAME twin. Preserve source arrays and expose read-only newly owned outputs. Route the optional Chapter 1 production entry through the measurement once, with a development Hamilton DAG around one production run. Produce the receipt and make the returned record available to rendering and telemetry.

**B1 — Geometric interiors and native border readings.** Consume surrounding-field readings to measure interior distance, declared prominence markers, all proposed territories, directed native edges and bracketed dark intervals. The [continuing contract](chapters/02-collapse/object-resolution-contract.md) gives their exact scopes. The [B1 record](chapters/02-collapse/measurements/geometric-interiors-b1.md) locates production receipts, SAME, telemetry and the separate color image series. Compute current standing with `just interiors-status`.

**B2 — Lens conversation and supported contour chains.** Same-orientation sequences measure the same knee and objects. The general exchange uses original boundary bands, unchanged native readings, explicit acquisition support and separate concurrent/conditional parent-preserving subdivisions. The founder's coronal pair is an illustrative inspection case, never a hard-coded pair/region rule. Trace and contract: [same-knee conversation](chapters/02-collapse/readings/same-knee-conversation-codex.md) and [checked workshop](chapters/02-collapse/readings/b2-workshop-resolution.md). [B2's evidence](chapters/02-collapse/measurements/same-knee-conversation-b2.md) links the production run, exact SAME, compute evidence and color series. Generic closure and constrained chain refinement remain task 3.8, retaining original/refined traces and shed places.

**C — Facing surfaces and extent.** Specify facing surfaces, the interstitial region, extent through neighboring slices, and separately acquired views. The founder teaches admission and meaning before implementation.

**D — Ownership and residual loop.** Specify peer ownership, own-signal views, and residual scheduling. The founder teaches the knee version and loop policy before implementation.

The remaining B2 contour operation and C–D continue toward **every significant
knee element relevant to the twelve findings, cleanly and deterministically
resolved**. Completion of an instrument's contract does not mean completion of
that anatomical goal. Meaning, extent and ownership require the subsequent
conjunctions and the founder's teaching.

Every distinct step saves an actual image series from the production records:

| packet | visual deliverable |
|---|---|
| A | acquired image, full red annotation from the recorded background split, physical squint, cyan native sampling locations and measured profiles, with magenta missing support |
| B | candidate interiors, native profiles, original/refined supported contour chains, gaps, clipping and shed places |
| C | paired facing surfaces, intervening support, neighboring slices and separately acquired views, with disagreement and alignment uncertainty |
| D | unchanged own-object signal, excluded peers, disputed/unclaimed material and successive residual rounds |

Keep raw coordinates, series/slice identity and source digests with those panels.
The cell-source trace and thesis sections supporting each operation are recorded
in the accepted reading above. Its mechanism table is the reuse map; copying a
cell constant or its oval/fluorescence assumptions is not reuse warranted by that map.

## Tool roles

- Serena supplies references. OpenSpec tracks the packet contracts and tasks.
- Hamilton is a development observer around one production run; it does not turn every internal kernel operation into a graph node.
- Hypothesis covers declared properties; CrossHair covers supported symbolic contracts; SAME compares reference and accelerated behavior within one environment.
- Detective covers pure named-code decisions through the local wrapper. Numeric array loops are not pinned automatically.
- Memray measures tracked allocations. VizTracer is intended to record a project-scoped timeline; verify that project calls are actually present, and use cProfile when they are absent. Scalene separates Python/native CPU and samples. Line profiler targets named repeated loops. Pyinstrument supplies a call tree.
- Native `perf`, C sanitizers, and Rust are admitted only when the computation shape calls for them. Import Linter checks package boundaries and dependency hygiene.

Use the existing commands: `just setup`, `just setup-profile`, `just plan-status`, `just plan-check`, `just graph`, `just graph-interiors`, `just graph-conversation`, `just analyze-objects`, `just interiors-status`, `just conversation-status`, `just same-interiors`, `just same-conversation`, `just render-interiors`, `just render-conversation`, and `just gate`. Per-run Matplotlib rendering stays outside project dependencies.

## Resume and evidence

Start at [Chapter 2's resume entry](chapters/02-collapse/RESUME.md). Run
`just interiors-status data/measurements/object-conversation-b2-v1` and
`just conversation-status data/measurements/object-conversation-b2-v1` to recompute
the original B1 and B2
source standing, receipt/SAME linkage, saved-artifact integrity and verifier
identity. The [B2 record](chapters/02-collapse/measurements/same-knee-conversation-b2.md)
locates that run and its staged photos. The [B1 record](chapters/02-collapse/measurements/geometric-interiors-b1.md)
and earlier [Packet A record](chapters/02-collapse/measurements/physical-packet-a.md)
retain their historical receipts and audits; an older source digest is not a claim
about the current build. No prose status substitutes for the status command.

Future measurements publish one atomic study checkpoint under the run's
`checkpoints/` directory. After interruption, inspect completed/partial records and
rerun the affected study into a fresh directory; never silently merge different
source snapshots. Save the receipt, images, checks and the next unresolved contract
before handing off. Update OpenSpec task checkboxes only for work with that evidence.
