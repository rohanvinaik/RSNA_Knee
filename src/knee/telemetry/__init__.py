"""TELEMETRY: where the compute went, and what was recomputed.

Not a stage. A project-wide layer, pulled in by any stage that wants to say what it did. Created
2026-10-11 at the founder's word:

    "Telemetry, too, should be put in a clean, central place, so it can be pulled in to monitor and
    analyze the code so we understand how it works and where compute goes, and how we can
    efficiently save or paralellize or cache or save ourselves from re-computing things we've
    computed before, etc. Central home for all the general, project-wide tooling like this."

THE RULE THAT SHAPES IT: nothing here may import structlog, OpenTelemetry or any profiler, because
this package sits on the PRODUCTION import path and those tools must never reach a Kaggle kernel
(docs/STAGE_CONTRACT.md; the global performance.md: "Each is per project, never on a production
import path"). So the ledger is plain stdlib, and the dev-side exporters read it from outside.

COUNTED WORK, NOT WALL TIME. A speed claim is a paired measurement -- Detective's opcode budget plus
pyperf -- never an informal timing. What a stage records here is the work it actually did: samples
taken, places visited, candidates proposed, raster cells written. Those numbers are deterministic, so
they are evidence; a duration measured under a profiler is behaviour, and the two are reported
separately. `elapsed_ns` is recorded only when a ledger is explicitly asked for timings, and it is
never the basis of a claim.

OFF BY DEFAULT. A disabled ledger does no allocation and no formatting, so a production run pays
nothing for the instrumentation being present.
"""

from knee.telemetry.ledger import Event, Ledger, ledger, recording

__all__ = ["Event", "Ledger", "ledger", "recording"]
