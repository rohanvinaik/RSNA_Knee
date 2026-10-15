"""TELEMETRY: where the compute went, and what was recomputed.

Not a stage. A project-wide layer, pulled in by any stage that wants to say what it did. Created
2026-10-11 at the founder's word:

    "Telemetry, too, should be put in a clean, central place, so it can be pulled in to monitor and
    analyze the code so we understand how it works and where compute goes, and how we can
    efficiently save or paralellize or cache or save ourselves from re-computing things we've
    computed before, etc. Central home for all the general, project-wide tooling like this."

THE RULE THAT SHAPES IT: nothing here may import structlog, OpenTelemetry or any profiler, because
this package sits on the PRODUCTION import path and those tools must never reach a Kaggle kernel
(the global performance.md: "Each is per project, never on a production import path"). So the
ledger is plain stdlib, and the dev-side instruments read the run from outside.

COUNTED WORK, NOT WALL TIME. A speed claim is a paired measurement, never an informal timing. What a
stage records here is the work it actually did: planes read, places visited, values made and handed
on. Those numbers are deterministic, so they are evidence; a duration measured under a profiler is
behaviour, and the two are reported separately.

OFF BY DEFAULT. A disabled ledger does no allocation and no formatting, so a production run pays
nothing for the instrumentation being present.

COMPUTED ONCE (`once`, `computing`): a value two stages need is made by the first to ask for it and
handed to every later asker, within one study's scope, and the ledger counts each making and each
handing-on. The founder, 2026-10-15: «ALL repetitious operations need to be centralized and
deduplicated across the whole codebase».
"""

from knee.telemetry.ledger import Event, Ledger, ledger, recording
from knee.telemetry.once import computing, once

__all__ = ["Event", "Ledger", "computing", "ledger", "once", "recording"]
