"""The free lenses, paired: which two series of a study are the two acquisitions of one plane.

**Why it exists, against the thesis.** The thesis's lenses are separate readings of one field whose
conjunction resolves meaning (§4.2, §5.4: "Two lenses at about one depth read one plane two ways,
and each corrects the other's borders"). The knee's lens axis is the acquisitions
(`docs/OBJECT_MODEL.md`). The founder, 2026-10-12: "fat-dark vs fat-bright? These aren't
independent views. These two are basically "lenses" that are given to us for free, by the
competition itself." And 2026-10-13, on what may be laid over what: "the other views shouldn't
speak to the axial view. It's of the same leg, so it speaks to diagnosis, but it's NOT the same
picture. Unlike, say, the coronal view fat bright vs fat dark, it's not "basically" the same view".
So a pair is two series of ONE plane, one fat-bright and one fat-dark, and nothing else is paired.

**What it reads.** The competition's own series table, told: `SeriesRow.anatomical_plane` and
`SeriesRow.fat_suppression` ("0" is fat-bright, "1" is fat-dark; `knee.collapse.structure.told_sign`
reads the flag). Never a header description (`docs/OBJECT_MODEL.md`: the sequence type is read from
the header's own fields, never from a series description; here the table's flag is the told sign).

This is the funnel's operation 0 (`openspec/changes/the-funnel/design.md` R0, task 0.1). The pure
decision is `pair_code`; `read_pairs` is orchestration and decides nothing itself.
"""

from __future__ import annotations

from dataclasses import dataclass

from knee.absence import absence_code
from knee.collapse.structure import told_sign
from knee.study.corpus import Study
from knee.telemetry import ledger

#: Every code `pair_code` returns. A plane's pairing is one of these, never a bool.
PAIR_CODES: tuple[str, ...] = ("paired", "solitary", "surplus", "none", "invalid_count")


def pair_code(n_bright: int, n_dark: int) -> str:
    """How one plane's series pair up, as a named code (pure -- pinned).

    `n_bright` counts the plane's fat-bright series and `n_dark` its fat-dark ones. Exactly one of
    each is "paired": the two free lenses. One series alone is "solitary": the plane has one
    picture, and its conjunction will be silence, never a negative. More than one of either flavour
    is "surplus": all are kept and none is paired, because which two to lay over each other is not
    settled by this count and a wrong pairing would read two different pictures as one. No series
    at all is "none". A count below zero is "invalid_count": an argument that cannot be read is a
    refusal, not a finding about the study.

    post: __return__ in PAIR_CODES
    """
    if n_bright < 0 or n_dark < 0:
        return "invalid_count"
    if n_bright == 0 and n_dark == 0:
        return "none"
    if n_bright == 1 and n_dark == 1:
        return "paired"
    if n_bright + n_dark == 1:
        return "solitary"
    return "surplus"


@dataclass(frozen=True, slots=True)
class AcquisitionPair:
    """One plane's pairing: its fat-bright and fat-dark series, and the code that says how they pair.

    `plane` is the table's `anatomical_plane` string as told. `bright_uids` and `dark_uids` hold
    every series of that flavour in table order, so a "surplus" plane keeps all of them.
    `unreadable_uids` holds series whose fat-suppression flag `told_sign` could not read; they
    count as neither flavour and are never paired. `code` is from `PAIR_CODES`.
    """

    plane: str
    bright_uids: tuple[str, ...]
    dark_uids: tuple[str, ...]
    unreadable_uids: tuple[str, ...]
    code: str


@dataclass(frozen=True, slots=True)
class AcquisitionPairs:
    """Every plane of one study with its pairing, in the order the planes first appear in the table.

    `code` is `present` when the study has at least one series, else `predecessor_empty`
    (`knee.absence`). A study with series but no "paired" plane is still `present`: the pairs
    record says, per plane, that each is solitary, surplus or none.
    """

    study_uid: str
    pairs: tuple[AcquisitionPair, ...]
    code: str


def read_pairs(study: Study) -> AcquisitionPairs:
    """Group a study's series by plane and name each plane's pairing (orchestration).

    For each `series.row` in `study.series`, in order: the plane is `row.anatomical_plane`; the
    flavour is `told_sign(row.fat_suppression)`: False is fat-bright, True is fat-dark, None is
    unreadable. Planes keep the order of first appearance. Each plane's code is
    `pair_code(len(bright_uids), len(dark_uids))`. The study's code is `present` when it has any
    series and `predecessor_empty` otherwise. Records `study.consumed_by.pairs` and
    `pairs.produced` on the ledger with the count of paired planes. Decides nothing itself.
    """
    # The consumption is recorded where the record is read, by its consumer (task 6.5 of
    # `every-stage-renders`): here, before the first row is looked at.
    ledger.record("study.consumed_by.pairs", series=len(study.series))
    # Only `series.row` is read: the table's plane and its fat-suppression flag. Nothing of the
    # pixels or the header reaches this operation, so a series without a volume pairs like any
    # other.
    planes: list[str] = []
    bright: dict[str, list[str]] = {}
    dark: dict[str, list[str]] = {}
    unreadable: dict[str, list[str]] = {}
    for series in study.series:
        row = series.row
        plane = row.anatomical_plane
        if plane not in bright:
            planes.append(plane)
            bright[plane], dark[plane], unreadable[plane] = [], [], []
        flavour = told_sign(row.fat_suppression)
        if flavour is None:
            unreadable[plane].append(row.series_uid)
        elif flavour:
            dark[plane].append(row.series_uid)
        else:
            bright[plane].append(row.series_uid)
    pairs = tuple(
        AcquisitionPair(
            plane=plane,
            bright_uids=tuple(bright[plane]),
            dark_uids=tuple(dark[plane]),
            unreadable_uids=tuple(unreadable[plane]),
            code=pair_code(len(bright[plane]), len(dark[plane])),
        )
        for plane in planes
    )
    ledger.record(
        "pairs.produced", paired=sum(1 for pair in pairs if pair.code == "paired")
    )
    # The study's own code is the shared vocabulary's: a study was handed over, and either it
    # holds series (`present`) or it holds none (`predecessor_empty`).
    return AcquisitionPairs(
        study_uid=study.row.uid,
        pairs=pairs,
        code=absence_code(
            construction_built=True,
            predecessor_returned=True,
            item_count=len(study.series),
            item_read=True,
        ),
    )
