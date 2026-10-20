# Competition output retention — 2026-10-20

This exchange is the human specification, preserved verbatim. It changes competition-mode retention, not the anatomy, measurements, precision or later AI design.

## Agent question

> One output-contract clarification affects storage: the current plan requires every intermediate lens array to remain saved after a study finishes. For competition mode, should we instead retain the complete object pixel/HDC bundles, their measured values and necessary provenance, and release intermediate lens files after their consumers finish? I’ll continue the lossless build work while you answer.

## Rohan's answer

> Retain complete object outputs; release consumed intermediate files

## Implementation consequence

The competition publisher must make the complete final object outputs independently readable, including their actual pixel/support addresses, HDC/count/profile information, measured values and necessary provenance. Active array links resolve inside the retained final product; original acquisition/artifact addresses remain historical provenance. Only after final publication and readback verification may the coordinator release this run's consumed intermediate files. Missing required dependencies or a failed publication leave the intermediates intact and return a named failure. Development output keeps diagnostic intermediates. This decision does not authorize deleting prior runs or source studies.

## Rohan — subsequent efficiency direction

> Align efficiency considerations with the fact of the upcoming AI aspects in line with the "what an <object> is" thesis is, and with the actual competition task will be
