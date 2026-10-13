"""What vulture cannot see, each name beside the consumer that reads it (task 7.2).

Passed to BOTH vulture scans in `scripts/ci_local.sh`. The gate's earlier comment refused any
whitelist, because a whitelist is how a guard stops being read. The rule that keeps this one a
guard: a name is listed here ONLY when its consumer exists in production and vulture cannot see
it -- a field the writer serialises by its name, a label read through an f-string, a node Hamilton
resolves by name -- and the consumer's location is written beside it. A name whose consumer is
still owed stays OUT of this file and visible in the gate, because that is what the gate is for.
A dead name is never listed; it is archived under its path (tasks.md 7.2).

vulture reads a bare name here as a use of that name everywhere, so an entry must name the one
thing it means to admit and nothing wider. ruff's B018 and F821 are lifted for this file alone in
pyproject.toml, since bare undefined names are exactly how vulture reads a whitelist.
"""

# InteriorReading.trace_points_rc: serialised by name in workbench/measure/interior_records.py,
# in `interior_record`'s tuple of field names.
trace_points_rc

# RegimeKey fields: the writer enumerates every field with `dataclasses.fields(regime)` in
# workbench/measure/object_analysis.py, so a field added later is saved by construction. Of the
# 26, these are read by no stage and saved whole; they are drawn by workbench/render/field_frames.py
# (`regime_lines`, every saved reading by name). `zero_share` and `foreground_share` joined the
# list on 2026-10-12 when the `regime_key` and `look` probes that read them by name were archived
# (task 7.1a); their consumer is the same enumeration.
dark_count
bright_count
storage
normalization
foreground_count
split_population_count
zero_share
foreground_share

# SeriesGeometry.along_normal in knee/study/series.py: read as
# `getattr(geometry, name, None) for name in ("normal", "position", "along_normal")` in
# knee/vectors/bundles.py (`_stack`), which the through-plane banks and the gap fraction read
# every other acquisition's stack through. The `geometry_spread` probe that read it by name was
# archived 2026-10-12 (task 7.1a).
along_normal

# SeriesConversation.concurrent_labels and .conditional_labels: read as
# `getattr(conversation, f"{name}_labels")` for each parse in knee/ownership/claims.py
# (`conversed_parses`), which seats one ownership member per parse.
concurrent_labels
conditional_labels

# Hamilton nodes in workbench/graph/object_measurements.py: resolved by name when
# scripts/object_graph.py requests them as outputs ("support/work records" in `just graph`).
support_records
work_counts

# ComputeContract fields: carried as data on every kernel. Their reader is the receipt, which
# serialises every contract with `dataclasses.asdict` (task 7.3), so a field added later is
# written by construction; no code reads a field by name, and none should.
language
reads
writes
allocation
work
parallel_unit
proof_gate

# Event.elapsed_ns in knee/telemetry/ledger.py: set by `Ledger.span` when the ledger was asked
# for timings (behaviour, never counted work) and serialised by `dataclasses.asdict` in the
# writer's ledger block. No stage times itself today, so the receipt carries it as None.
elapsed_ns

# BoundaryExchange's per-exchange arrays in knee/objects/conversation.py: every one is
# serialised by its name through `getattr` in workbench/measure/conversation_records.py and
# saved in the series artifact beside the labels and barriers.
source_regions
donor_quads_rc
off_plane_mm
coverage_codes
derived_trace_rc
concurrent_quads_rc
