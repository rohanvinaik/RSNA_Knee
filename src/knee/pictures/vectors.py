"""Bundle picture panels: each object's profile as banks of counts, arranged from the run's own values.

Task 6.7 of `openspec/changes/every-stage-renders`, under thesis §13.7 and
`docs/STAGE_CONTRACT.md` §1: a picture arranges the run's values, the production run imports no
drawing code, and a renderer may not measure, threshold, count or infer. This module therefore
only carries the bundles reading's values across into frozen panels. It does no arithmetic, no
validation, no copying of arrays and no I/O.

A profile is row counts over named banks, and a bank the stage could not write is carried
`unavailable` with its reason and EMPTY rows. The panels keep exactly that: an unavailable bank
reaches the picture as an unavailable bank, and a count is the stage's own whole number. Nothing
here sums rows, normalises them, or fills a missing row with zero, because a zero count asserts
that a reading was made and found nothing.

The reading's `subject_kind` and `planes_read` are carried so a picture can say what the profiles
are keyed on and that only the selected native plane was read. No panel names what an extent is.
"""

from dataclasses import dataclass

from knee.vectors.bundles import BundlesReading


@dataclass(frozen=True, slots=True)
class BankPanel:
    """One bank exactly as the stage returned it, its rows as (row name, count) pairs in order.

    `rows` is empty when `status` is `unavailable`, and `why` then names what was missing. The
    pairs are the stage's own `rows` mapping in its own order; no count is computed here.
    """

    name: str
    source_stage: str
    status: str
    rows: tuple[tuple[str, int], ...]
    why: str


@dataclass(frozen=True, slots=True)
class ProfilePanel:
    """One object's profile: its integer index, how many places wrote it, and every bank by name."""

    index: int
    places: int
    banks: tuple[BankPanel, ...]


@dataclass(frozen=True, slots=True)
class BundlesPanels:
    """The bundles reading's unchanged values, ready for the workbench to draw.

    `code` and `why` are the stage's authoritative status and reason; when `code` is not
    `present`, `profiles` is empty and `why` names the silence. `subject_kind` says what the
    profiles are keyed on and `planes_read` how many planes were read. `backend` is the backend the
    through-plane banks were REQUESTED to use, and `slab_gaps` one (series uid, gap fraction) pair
    per other acquisition in the order the stage had them, a fraction None where it could not be
    read; both are the stage's own and have no default here, because a default would state a reading
    the stage never made.
    """

    code: str
    why: str
    subject_kind: str
    planes_read: int
    profiles: tuple[ProfilePanel, ...]
    backend: str
    slab_gaps: tuple[tuple[str, float | None], ...]


def panels(reading: BundlesReading) -> BundlesPanels:
    """Hand on the stage's profiles, banks and counts without interpreting any of them.

    Every attribute is carried across unchanged; a bank's `rows` mapping becomes the tuple of its
    own (name, count) pairs, in the stage's order, so the panel is immutable and nothing is
    recounted. A silent reading returns no profiles and keeps its code and reason.

    post: len(__return__.profiles) == len(reading.profiles)
    post: [p.index for p in __return__.profiles] == [p.index for p in reading.profiles]
    """
    return BundlesPanels(
        code=reading.code,
        why=reading.why,
        subject_kind=reading.subject_kind,
        planes_read=reading.planes_read,
        profiles=tuple(
            ProfilePanel(
                index=profile.index,
                places=profile.places,
                banks=tuple(
                    BankPanel(
                        name=bank.name,
                        source_stage=bank.source_stage,
                        status=bank.status,
                        rows=tuple(bank.rows.items()),
                        why=bank.why,
                    )
                    for bank in profile.banks
                ),
            )
            for profile in reading.profiles
        ),
        backend=reading.backend,
        slab_gaps=reading.slab_gaps,
    )
