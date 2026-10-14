# Bounded mechanical NumPy reference body

User explicitly authorized Sonnet API mechanized building. Classical AI, no ML. No architectural
policy or tests. Return ONLY raw Python statements indented four spaces; no def/import/docstring,
fences, explanation, tests or changes to contracts. This is the reference, no accelerated twin.

Signature supplied by lead:
place_codes_reference(values:np.ndarray,low_edge:float|None,high_edge:float|None,
population_count:int,minimum_population:int)->np.ndarray

Module already imports np, digit_code, handed_on. CODE_VALUES maps scalar named codes to uint8 indices
in order below,at,above,place_unread,no_edges,population_too_small,invalid_measurement (0..6).
Input real numeric ndarray native values, finite or nan/infinite. Output same shape readonly owned
uint8 code array. Every place must match scalar digit_code exactly; no source writes or rescaling.

Use scalar digit_code(float('nan'), low_edge, high_edge, population_count, minimum_population) ONCE
to obtain base code. It returns place_unread when edges/population valid; otherwise returns one
silence/refusal code for all values. Allocate np.full(values.shape,CODE_VALUES[base],dtype=np.uint8).
ONLY when base == place_unread: compute finite=np.isfinite(values), assign at to finite places,
below to finite & (values<low_edge), above to finite & (values>high_edge). Equal edges stay at.
Return handed_on(array). No per-pixel Python loop, quantile, copies, dtype conversion of source,
other constants/bars, interpolation, anatomical names, I/O, timing or telemetry in this body.
