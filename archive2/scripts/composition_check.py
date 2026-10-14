"""A saved run's composition, read from its receipt's ledger. Advisory: it reports and never gates.

Why this is a command. The route's composition was first checked with a scratch probe, and the same
three questions are owed to every real run, so the probe became a verb that answers back (task 7.4,
`openspec/changes/every-stage-renders`). It reads the `ledger` of each study in a
`physical-measurements-v2` receipt, and nothing else:

  1. Is every produced record consumed? A stage records `<producer>.produced`, and whatever reads
     it records `<producer>.consumed_by.<consumer>` at the point of reading (task 6.5). A producer
     with no such event is DANGLING. `output` alone may have none: its consumer is the file the
     impure edge writes, which the ledger does not see.
  2. Does any consumer event name a producer that never produced? That is a PHANTOM.
  3. Does `conversation.produced` come before the first `ownership.produced`? The conversation's
     refined parse is an input to ownership (task 6.1), so after it is OUT OF ORDER.

A producer is the first dotted component of an event name, so `ownership.member.produced` belongs
to `ownership`. Ledger indexes count from 0. An event in neither vocabulary, such as
`objects.boundary_census`, is listed and never read.

What it cannot do. It compares what stages SAID they produced and read. An event is a stage's own
statement, and agreement between statements does not show that the value read was the value made;
`just graph` observes the wiring itself.

Usage: PYTHONPATH=.:src .venv/bin/python scripts/composition_check.py <run-dir>

The exit status is 0 whatever the verdict, since the check is advisory like `scripts/places.py`. It
is 2 only when the receipt cannot be read as the schema says, with a named refusal. The last line is
always `COMPOSITION: <status>`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCHEMA = "physical-measurements-v2"
PRODUCED = ".produced"
CONSUMED_BY = ".consumed_by."

#: The one producer allowed no consumer in the ledger: `output` is read by the file the impure edge
#: writes. tests/knee/test_pipeline_composition.py makes the same exemption, and no other.
FILE_CONSUMED = frozenset({"output"})

#: What the order reading can say. Only AFTER is a failure; the rest are a pass or a silence.
ORDER_BEFORE = "conversation_precedes_ownership"
ORDER_AFTER = "conversation_after_ownership"
NO_CONVERSATION = "conversation_absent"
NO_OWNERSHIP = "ownership_absent"


class Refusal(Exception):
    """The receipt cannot be read as `physical-measurements-v2` says. `code` is the named reason."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def classify(name: str) -> tuple[str, str, str]:
    """How the ledger names one event: `(kind, producer, consumer)`.

    `kind` is `produced`, `consumed` or `other`. A name that belongs to both vocabularies at once
    (`a.consumed_by.b.produced`), or whose producer or consumer would be empty, is `other`: it is
    listed and never read, so no event is mislabelled to make a count come out.
    """
    consumed = CONSUMED_BY in name
    if consumed == name.endswith(PRODUCED):
        return "other", "", ""
    if consumed:
        head, _, consumer = name.partition(CONSUMED_BY)
    else:
        head, consumer = name.removesuffix(PRODUCED), ""
    producer = head.split(".", 1)[0]
    if not producer or (consumed and not consumer):
        return "other", "", ""
    return ("consumed" if consumed else "produced"), producer, consumer


def order_code(conversation: list[int], ownership: list[int]) -> str:
    """Whether the conversation was produced before ownership began, as a named reading.

    Every conversation event must come before the first ownership event: the refined parse is an
    input to ownership, so one arriving after ownership started is an input some ownership never
    saw. With a single conversation event this is exactly `conversation.produced` before the first
    `ownership.produced`. A conversation with no ownership beside it has no order to read.
    """
    if not conversation:
        return NO_CONVERSATION
    if not ownership:
        return NO_OWNERSHIP
    return ORDER_BEFORE if conversation[-1] < ownership[0] else ORDER_AFTER


def verdict_code(dangling: list[str], phantom: list[str], out_of_order: bool) -> str:
    """The status, the first that applies: dangling, phantom, out_of_order, else composed."""
    if dangling:
        return "dangling:" + ",".join(dangling)
    if phantom:
        return "phantom:" + ",".join(phantom)
    return "out_of_order" if out_of_order else "composed"


def read_receipt(run_dir: Path) -> dict[str, Any]:
    """The receipt under a run directory, or a named refusal."""
    path = run_dir / "receipt.json"
    if not path.is_file():
        raise Refusal("receipt_missing", f"no receipt.json under {run_dir}")
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise Refusal("receipt_unreadable", f"{path}: {error}") from error
    except ValueError as error:
        raise Refusal("receipt_not_json", f"{path}: {error}") from error
    if not isinstance(receipt, dict):
        raise Refusal(
            "receipt_not_an_object", f"{path} holds a {type(receipt).__name__}"
        )
    found = receipt.get("schema")
    if found != SCHEMA:
        raise Refusal(
            "schema_unexpected", f"schema is {found!r}; this check reads {SCHEMA!r}"
        )
    return receipt


def ledger_names(study: object, index: int) -> list[str]:
    """One study's event names in ledger order, or a named refusal.

    A ledger with nothing in it, or with no `<producer>.produced` event in it, has no composition
    to compare, and a verdict of `composed` over it would be a pass that checked nothing.
    """
    where = f"studies[{index}]"
    if not isinstance(study, dict):
        raise Refusal("study_not_an_object", f"{where} is a {type(study).__name__}")
    ledger = study.get("ledger")
    if not isinstance(ledger, list):
        raise Refusal("ledger_missing", f"{where} has no ledger list")
    if not ledger:
        raise Refusal(
            "ledger_empty", f"{where} ledger holds no events, so nothing was compared"
        )
    names: list[str] = []
    for position, event in enumerate(ledger):
        name = event.get("name") if isinstance(event, dict) else None
        if not isinstance(name, str) or not name:
            raise Refusal(
                "event_malformed", f"{where} ledger[{position}] has no event name"
            )
        names.append(name)
    if not any(classify(name)[0] == "produced" for name in names):
        raise Refusal(
            "no_produced_events", f"{where} ledger holds no <producer>.produced event"
        )
    return names


def read_studies(receipt: dict[str, Any]) -> list[tuple[dict[str, Any], list[str]]]:
    """Every study with its event names, refusing at the first that cannot be read."""
    studies = receipt.get("studies")
    if not isinstance(studies, list):
        raise Refusal("studies_missing", "the receipt has no `studies` list")
    if not studies:
        raise Refusal("studies_empty", "the receipt's `studies` list holds no study")
    return [(study, ledger_names(study, index)) for index, study in enumerate(studies)]


def produced_row(
    event: str, at: list[int], readers: dict[str, set[str]]
) -> dict[str, Any]:
    """One produced event name: how often, where first, and who read its producer."""
    producer = classify(event)[1]
    consumed_by = sorted(readers.get(producer, ()))
    return {
        "producer": producer,
        "event": event,
        "count": len(at),
        "first_index": at[0],
        "consumed": bool(consumed_by),
        "consumed_by": consumed_by,
        "allowed": not consumed_by and producer in FILE_CONSUMED,
    }


def read_ledger(names: list[str]) -> dict[str, Any]:
    """What one ledger says about its own composition. Pure and total over any list of strings."""
    produced_at: dict[str, list[int]] = {}
    readers: dict[str, set[str]] = {}
    consumer_events: dict[str, str] = {}
    unclassified: dict[str, int] = {}
    for index, name in enumerate(names):
        kind, producer, consumer = classify(name)
        if kind == "produced":
            produced_at.setdefault(name, []).append(index)
        elif kind == "consumed":
            readers.setdefault(producer, set()).add(consumer)
            consumer_events.setdefault(name, producer)
        else:
            unclassified[name] = unclassified.get(name, 0) + 1
    rows = [produced_row(event, at, readers) for event, at in produced_at.items()]
    producers = {row["producer"] for row in rows}
    phantom_events = [
        event
        for event, producer in consumer_events.items()
        if producer not in producers
    ]
    dangling = sorted(
        {row["producer"] for row in rows if not row["consumed"] and not row["allowed"]}
    )
    phantom = sorted({consumer_events[event] for event in phantom_events})
    conversation = [
        i for i, name in enumerate(names) if name == "conversation.produced"
    ]
    ownership = [i for i, name in enumerate(names) if name == "ownership.produced"]
    order = order_code(conversation, ownership)
    return {
        "events": len(names),
        "produced": rows,
        "dangling": dangling,
        "phantom": phantom,
        "phantom_events": phantom_events,
        "unclassified": unclassified,
        "order": {
            "conversation_produced": conversation,
            "ownership_produced_first": ownership[0] if ownership else None,
            "verdict": order,
        },
        "verdict": verdict_code(dangling, phantom, order == ORDER_AFTER),
    }


def attendance_of(study: dict[str, Any]) -> list[list[str]] | None:
    """The receipt's attendance roster as `[stage, code]` pairs, or None if it is not that shape."""
    roster = study.get("attendance")
    if not isinstance(roster, list):
        return None
    pairs: list[list[str]] = []
    for entry in roster:
        valid = isinstance(entry, (list, tuple)) and len(entry) == 2
        if not (valid and all(isinstance(cell, str) for cell in entry)):
            return None
        pairs.append([entry[0], entry[1]])
    return pairs


def study_summary(
    index: int, study: dict[str, Any], names: list[str]
) -> dict[str, Any]:
    """One study's identity, its ledger reading and its attendance, the verdict last."""
    uid = study.get("study_uid")
    reading = read_ledger(names)
    verdict = reading.pop("verdict")
    return {
        "study": uid[-12:] if isinstance(uid, str) else None,
        "index": index,
        "code": study.get("code"),
        "reached": study.get("reached"),
        **reading,
        "attendance": attendance_of(study),
        "verdict": verdict,
    }


def overall(summaries: list[dict[str, Any]]) -> str:
    """The run's status: what every study found, under the same rule as one study."""
    return verdict_code(
        sorted({name for summary in summaries for name in summary["dangling"]}),
        sorted({name for summary in summaries for name in summary["phantom"]}),
        any(summary["order"]["verdict"] == ORDER_AFTER for summary in summaries),
    )


def columns(rows: list[tuple[str, ...]], right: tuple[int, ...]) -> list[str]:
    """Rows of cells in aligned columns. The last column is left as written, never padded."""
    widths = [max(len(row[i]) for row in rows) for i in range(len(rows[0]))]
    lines = []
    for row in rows:
        cells = [
            cell.rjust(widths[i])
            if i in right
            else cell.ljust(widths[i])
            if i < len(row) - 1
            else cell
            for i, cell in enumerate(row)
        ]
        lines.append("  ".join(cells))
    return lines


def produced_table(rows: list[dict[str, Any]]) -> list[str]:
    """Every produced event name against whether its producer was ever recorded as read."""
    cells = [
        ("producer", "produced event", "events", "first at", "consumed", "consumed by")
    ]
    for row in rows:
        if row["consumed"]:
            answer, note = "yes", ", ".join(row["consumed_by"])
        elif row["allowed"]:
            answer, note = (
                "no",
                "allowed: the output file is its consumer, outside the ledger",
            )
        else:
            answer, note = "NO", "DANGLING: nothing recorded reading it"
        cells.append(
            (
                row["producer"],
                row["event"],
                str(row["count"]),
                str(row["first_index"]),
                answer,
                note,
            )
        )
    return ["  " + line for line in columns(cells, right=(2, 3))]


def order_text(order: dict[str, Any]) -> str:
    """The order reading with the indexes it rests on."""
    seen = ", ".join(str(index) for index in order["conversation_produced"]) or "never"
    first = order["ownership_produced_first"]
    return (
        f"conversation.produced at {seen}; first ownership.produced at "
        f"{'never' if first is None else first} -> {order['verdict']}"
    )


def attendance_lines(roster: list[list[str]] | None) -> list[str]:
    """The roster as the receipt records it, or the plain statement that it cannot be read."""
    if roster is None:
        return [
            "  attendance    not in this receipt, or not a list of [stage, code] pairs"
        ]
    if not roster:
        return ["  attendance    recorded empty"]
    stages = columns([(stage, code) for stage, code in roster], right=())
    return [
        "  attendance    each stage with the code it returned for this study",
        *(f"      {line}" for line in stages),
    ]


def phantom_text(summary: dict[str, Any]) -> str:
    """Each phantom producer with the consumer events that named it, or `none`."""
    named = [
        f"{producer} (via "
        + ", ".join(
            event
            for event in summary["phantom_events"]
            if classify(event)[1] == producer
        )
        + ")"
        for producer in summary["phantom"]
    ]
    return "; ".join(named) or "none"


def unclassified_text(summary: dict[str, Any]) -> str:
    """The event names in neither vocabulary with how often each occurred, or `none`."""
    named = [f"{name} x{count}" for name, count in summary["unclassified"].items()]
    return ", ".join(named) or "none"


def render(summary: dict[str, Any]) -> list[str]:
    """One study's table, then its readings, then its JSON summary."""
    tail = summary["study"]
    label = f"...{tail}" if tail else "(no study_uid)"
    code = "?" if summary["code"] is None else summary["code"]
    reached = "?" if summary["reached"] is None else summary["reached"]
    header = (
        f"STUDY {label}  studies[{summary['index']}]  code {code}  reached {reached}  "
        f"ledger events {summary['events']}"
    )
    return [
        "",
        header,
        "",
        *produced_table(summary["produced"]),
        "",
        f"  dangling      {', '.join(summary['dangling']) or 'none'}",
        f"  phantom       {phantom_text(summary)}",
        f"  unclassified  {unclassified_text(summary)}  (in neither vocabulary: never read)",
        f"  order         {order_text(summary['order'])}",
        *attendance_lines(summary["attendance"]),
        "",
        f"SUMMARY {label} (JSON)",
        json.dumps(summary, indent=2),
    ]


def main(argv: list[str]) -> int:
    try:
        if len(argv) != 1:
            raise Refusal("usage", "composition_check.py <run-dir>")
        run_dir = Path(argv[0])
        receipt = read_receipt(run_dir)
        studies = read_studies(receipt)
    except Refusal as refusal:
        print(f"refused {refusal.code}: {refusal.detail}")
        print(f"COMPOSITION: refused:{refusal.code}")
        return 2
    failures = receipt.get("failures")
    recorded = len(failures) if isinstance(failures, list) else "not recorded"
    print(f"COMPOSITION CHECK of {run_dir}")
    print(
        f"  schema {SCHEMA}; studies checked {len(studies)}; "
        f"failures the receipt records {recorded}"
    )
    print(
        "  ledger indexes count from 0; a producer is the first dotted component of a name"
    )
    summaries = [
        study_summary(index, study, names)
        for index, (study, names) in enumerate(studies)
    ]
    for summary in summaries:
        print("\n".join(render(summary)))
    print(f"\nCOMPOSITION: {overall(summaries)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
