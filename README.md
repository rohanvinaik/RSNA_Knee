# RSNA Knee

A classical-AI entry for RSNA Knee Abnormality Detection. The intended system resolves
structural `<object>`s and their relations, then reads twelve findings as predicates.
There is no machine learning in the architecture. Anatomy informs the design; runtime
records use indexed subjects and named codes.

Start with [the object model](docs/OBJECT_MODEL.md), [the pipeline as one object](docs/PIPELINE_AS_OBJECT.md),
and [the current route](docs/PIPELINE.md). [The build plan](docs/BUILD_PLAN.md) identifies each
OpenSpec change's responsibility; [the resume entry](docs/chapters/02-collapse/RESUME.md) points to
remaining work and evidence. [The reconciliation record](docs/RECONCILIATION.md) traces how this
scaffold became the current architecture.

- `src/knee/`: nine route stages, with separate compute, telemetry and drawing layers.
- `tests/`: engineering checks and intent tests.
- `workbench/`: execution, saved-record rendering, development observers and historical probes.
- `openspec/`: declared changes, scenario contracts and implementation checklists.
- `data/`: private source data and derived runs; gitignored.
- `archive/`: retired design, code and dated planning snapshots, consulted as history.

Agents start at `AGENTS.md`. The PI–undergrad workflow remains in [SPINE.md](docs/SPINE.md);
its original Figure 8 chapter table is historical. Use `just unit` to compute planning and
structural state. Commands and environment limits: [TOOLING.md](docs/TOOLING.md).
