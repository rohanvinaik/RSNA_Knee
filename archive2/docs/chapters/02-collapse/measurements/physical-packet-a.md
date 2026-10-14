# Packet A: saved physical measurements

This record locates a particular run, rather than declaring current state. Recompute
standing with `just packet-status data/measurements/physical-packet-a-v3`.
Its `status.json` reports source, receipt, verifier and artifact integrity.

## Run and comparison

```sh
just analyze-objects --tile-mm 4 --span-mm 8 --samples 17 --axis superior --backend jit --detective-report data/measurements/profile-support-detective.json --out data/measurements/physical-packet-a-v3
just same data/measurements/physical-packet-a-v3
just packet-status data/measurements/physical-packet-a-v3
```

The recorded receipt contains 58 studies and 336 series: 334 measured, two
`axis_unavailable`, no failures. Scope is one middle acquired plane per series.
The supplied demonstration settings are explicit inputs, not admitted anatomical
scales or a finding criterion. Original header directions and stored pixels are
retained. Profile length uses the retained direction metric, so rounded direction
cosines do not silently become an exactly orthonormal coordinate basis.

The recorded SAME comparison checked 334 series and 9,520,459 samples. It compares
reference, JIT and saved values, masks, adjacent-supported slopes, offsets, support
codes, shapes, dtypes, sign bits and NaN standing within this environment. Receipt,
NPZ and verifier digests bind the proof. This does not establish Linux/Kaggle or
compiler-wide equality, anatomical identity, or contour accuracy.

The supplied Detective report is `data/measurements/profile-support-detective.json`.
For `profile_support_code`, its diagnosis reports 45 behavioral variants, 43
distinctions pinned and two unspecified degrees of freedom. An earlier converge
reported COMPLETE modulo two unproven-equivalent survivors. Retain both statements;
do not promote that to unconditional complete pinning. Numeric kernels are checked
by contracts/properties/SAME, not blanket Detective claims. CrossHair confirmed
three of six postconditions and left three unconfirmed, with no counterexample.

## Images

`data/pictures/object-toolkit/packet-a-annotated/series.png` and five individual PNGs show all
five saved middle planes of the selected study. `manifest.json` binds receipt,
NPZ, renderer and layout identities and records each source plane and probe site.
Each row shows acquired image → full red background annotation → physical median
squint → native sample locations → actual signal profile. Red is the saved mask
from the existing production whole-series histogram split, retained in `RegimeKey`
and projected onto the acquired plane. Cyan marks supported profile samples;
magenta marks missing ones. The mask is a boolean array in native plane shape;
it is absent with a named unavailable status when the split is not finite.
This display reading does not itself assign the thesis's structural role of black.
The displayed probe is the nearest recorded site to the declared fraction
`(0.52, 0.52)`. This is a visualization choice, not anatomical selection.

```sh
just render-packet data/measurements/physical-packet-a-v3 --study-uid 1.2.826.0.1.3680043.8.498.10095687747295410396510538520594649149 --probe-fraction-rc 0.52 0.52 --out data/pictures/object-toolkit/packet-a-annotated
```

For an offline render with the already populated cache, use `UV_OFFLINE=1`,
`UV_NO_SYNC=1`, `UV_CACHE_DIR=/private/tmp/rsna-uv-cache` and a writable
`MPLCONFIGDIR`, e.g. `/private/tmp/rsna-mpl-cache`. Matplotlib remains per-run.

## Telemetry and its limits

The earlier five-series measurement route supplied these recorded artifacts:

- `data/measurements/physical-packet-a-memory.bin` and `physical-packet-a-memory-stats.json`: peak tracked
  allocation 302,690,301 bytes; no native stacks or Python-allocator tracing. This
  is a tracked-allocation result, not RSS or the final corrected source's budget.
- `data/measurements/physical-packet-a-calls.prof` and `.json`: 4,532,411 calls
  (4,472,045 primitive), 2.636631962 seconds under cProfile. Production frame
  entries include five `read_series`, five `measure_series`, five `physical_squint`
  and 164 `read_slice` calls. Instrumented time is not a speed claim.
- The unrestricted VizTracer capture overflowed; project-filtered captures contained
  three events and no project calls on this interpreter. They establish no project
  timeline. cProfile is the recorded fallback.

Numba serves the repeated numeric profile loop. C/Rust admission remains governed
by computation shape and a measured budget, with a pinned reference and SAME;
there is no native rewrite justified merely by tool availability.

## Audit and restart

See [the independent lead reading](../readings/packet-a-audit-codex.md),
[the approved Fable audit](../readings/packet-a-audit-fable.md) and
[checked resolutions](../readings/packet-a-audit-resolution.md).
The source audit contains no competition pixels or reports.

The checkpoint writer was separately exercised on the same five-series study in
`data/measurements/physical-packet-a-checkpoint-check`. The v3 corpus run saved all
58 atomic study checkpoints. `annotation-checks.json` binds the receipt and records
checks of all 336 background masks and all 58 checkpoints against their saved
production records. `gate.log` records 225 passed tests, one platform-specific skip,
clean Ruff/format and clean advisory types. The full v2 receipt and earlier image
series remain preserved as historical snapshots; their source standing must be
recomputed, not carried forward after this annotation correction.

Next packet: candidate interiors and supported contour chains, with original and
refined traces, gaps, shed places and clipping visible. Meaning and admission
follow the founder's teaching and the accepted toolkit reading. The unresolved
noise-law reading remains recorded; this packet does not turn raw counts into
calibrated flickers or choose a new noise policy.
