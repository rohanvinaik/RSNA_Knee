# Candidate validation history

All entries concern only the isolated candidate tree.

1. The first focused pytest invocation used a wrong relative path to the project interpreter; the shell returned “no such file or directory” and pytest did not start.
2. A combined invocation requested `tests/test_study_map.py`, which is not in the pinned candidate snapshot; pytest collected zero tests and stopped on the missing path.
3. The first handoff test run passed map admission/idempotency and failed an AST-order assertion because it looked for the top-level helper instead of the local wrapper. That AST-only test was later removed per review.
4. The first guide fixture omitted the required `spacing_rc` argument to `PlaneFrame.from_dicom`; the setup failed before exercising the handoff. Unit spacing was supplied.
5. Final focused run after review corrections: 32 tests passed. Ruff check and format check passed.
6. Global `ty` returned 45 diagnostics for both the frozen baseline and candidate, with no added or removed fingerprints. The candidate check is non-clean but introduces no diagnostic delta.
