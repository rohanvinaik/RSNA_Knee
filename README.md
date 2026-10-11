# RSNA Knee

A classical-AI entry for RSNA Knee Abnormality Detection: 12 findings per knee MRI study, scored by
macro-averaged ROC-AUC. There is no machine learning in the architecture.

- `src/knee/`: the build, one package per stage of Figure 8 of *What an \<Object> Is* (§2.8), built
  in order with the founder.
- `tests/`: its tests.
- `data/raw/`: the competition's files, in Kaggle's own layout (gitignored; never redistributed).
- `archive/`: everything from before 2026-10-10, under its old path.

Agents start at `AGENTS.md` (`CLAUDE.md` imports it).

Development setup and commands: [docs/TOOLING.md](docs/TOOLING.md).

Chapter-by-chapter work packets and tool roles: [docs/BUILD_PLAN.md](docs/BUILD_PLAN.md).
