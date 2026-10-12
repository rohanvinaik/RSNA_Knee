# Bounded implementation task

Rohan: "I was thinking of some cheap agents, like sonnet over the API, for mechanized building,
in addition to your own sub-agents". He has authorized this body, overriding the usual reader-only
consultation role. You type this settled mechanical body only. No architectural advice or tests.

Project: classical AI, no ML. A resolved object is an indexed extent, not an anatomical identity.
The founder requires each stage to render. Thesis §13.7: a picture arranges the run's values;
the production run imports no drawing code. A renderer may not measure, threshold, count or infer.

Return ONLY raw Python source for src/knee/pictures/ownership.py, no Markdown fences or explanation.

Exact interface supplied by the lead: import dataclass, numpy as np (only for type annotation),
OwnershipReading from knee.ownership.claims. Define frozen slots dataclass OwnershipPanels with fields
code:str, why:str, claims:np.ndarray, residual:np.ndarray, claimed_places:int,
residual_places:int, unavailable_places:int, objects:int, in that order. Define
panels(reading: OwnershipReading)->OwnershipPanels. Return those eight attributes unchanged.
Preserve array identity, no copies/coercion/recomputation/validation/new decisions/I/O/matplotlib.
Use explicit keyword arguments. Module/class/function docstrings describe the residual map and why
unread is not residual. Module docstring names OpenSpec every-stage-renders task1.3 and thesis §13.7.
OwnershipReading already returns readonly bool(R,C) claims/residual with real masks even when code
is predecessor_empty. Missing/malformed input has empty(0,0) masks and a named code. Existing counts
and code/reason are authoritative computed values and must never be replaced by renderer arithmetic.
Unread locations are not present in this record, only their count; do not invent an unread mask.
