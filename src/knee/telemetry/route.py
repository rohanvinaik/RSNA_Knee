"""The route: which products of a run no stage read, from the ledger's events.

A stage that hands something on records `<stage>.<field>.produced` for each field of it, and a
stage that reads a field records `<stage>.<field>.consumed_by.<reader>` at the point of reading. A
field produced and read by no stage is an island at run time: computed, kept in the record at
most, and used by nothing. The founder, 2026-10-12: «there should be structural guards against
islands of code that compute but are never called ... they would make unused scripts that are in
the codebase impossible to miss.» Kept in the record is not read by a stage.
"""

from collections.abc import Iterable

PRODUCED = ".produced"
CONSUMED_BY = ".consumed_by."


def unread_products(names: Iterable[str]) -> tuple[str, ...]:
    """The products no stage read, in the order they were first produced (measurement).

    `names` are the ledger's event names, in order. A product is the part of a name before
    `.produced`, or before `.consumed_by.`. A product is read when it, or any field of it
    (`<product>.<field>`), is read anywhere in the run; a field is not read because its product
    is. A read of something never produced is no island and is not reported.
    """
    produced: list[str] = []
    read: set[str] = set()
    for name in names:
        if CONSUMED_BY in name:
            read.add(name.split(CONSUMED_BY, 1)[0])
        elif name.endswith(PRODUCED):
            product = name[: -len(PRODUCED)]
            if product not in produced:
                produced.append(product)
    return tuple(
        product
        for product in produced
        if product not in read
        and not any(field.startswith(product + ".") for field in read)
    )
