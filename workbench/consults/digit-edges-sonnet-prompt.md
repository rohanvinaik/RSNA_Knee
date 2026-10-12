# Mechanized body only

Rohan explicitly authorized "cheap agents, like sonnet over the API, for mechanized building".
Classical AI project, no ML. Type one settled pure decision; lead owns intent, tests, contracts,
survivor judgments and integration. Return ONLY raw Python statements constituting the function BODY,
indented four spaces. No def, imports, docstring, fences, explanation, tests or policy.

Module imports math. Constants DIGIT_CODES and READ_CODES exist. Signature supplied by lead:
digit_code(place_value:float|None,low_edge:float|None,high_edge:float|None,
population_count:int,minimum_population:int)->str.

Rules, in priority order (OpenSpec ternary-place-digits):
1. Negative population_count or minimum_population returns invalid_measurement.
2. If BOTH edges are non-None and finite but low_edge>high_edge, invalid_measurement.
3. If count==0 OR either edge is None/nonfinite, no_edges.
4. count<minimum_population returns population_too_small.
5. place is None/nonfinite returns place_unread.
6. place<low_edge returns below; place>high_edge returns above; else at.

Both edges inclusive at; equal edges valid. No epsilon/band/spread/threshold literal (zero is a
count validity boundary, not an admission bar), no conversions, fitted parameters, I/O or exceptions.
Total on annotated domain including None, nan and infinities. Contract promises code in DIGIT_CODES
and every READ_CODES result has count>0 and count>=minimum_population.
