"""The frames preserve the readings, including their silences; they invent no partition."""

from types import SimpleNamespace

import numpy as np
import pytest

from knee.ownership.claims import OwnershipReading, read_ownership
from knee.pictures.ownership import panels as ownership_panels
from knee.pictures.relations import panels as relations_panels
from knee.relations.shell import Interstice, RelationsReading, read_relations


@pytest.mark.parametrize(
    "source",
    [
        None,
        SimpleNamespace(labels="malformed", available=None),
        SimpleNamespace(
            labels=np.zeros((2, 3), dtype=np.int32),
            available=np.array([[True, False, True], [True, True, True]]),
            code="no_interior_seeds",
        ),
        SimpleNamespace(
            labels=np.array([[1, 0, 2], [0, 0, 2]], dtype=np.int32),
            available=np.array([[True, False, True], [True, True, True]]),
            code="measured",
        ),
    ],
)
def test_ownership_frame_preserves_the_actual_partition_or_absence(source) -> None:
    reading = read_ownership(source)
    frame = ownership_panels(reading)
    assert frame.claims is reading.claims
    assert frame.residual is reading.residual
    for name in (
        "code",
        "why",
        "claimed_places",
        "residual_places",
        "unavailable_places",
        "objects",
    ):
        assert getattr(frame, name) == getattr(reading, name)


def test_no_claims_does_not_erase_the_residual_picture() -> None:
    source = SimpleNamespace(
        labels=np.zeros((2, 2), dtype=np.int32),
        available=np.array([[True, False], [True, True]]),
        code="no_interior_seeds",
    )
    frame = ownership_panels(read_ownership(source))
    assert frame.code == "predecessor_empty"
    np.testing.assert_array_equal(frame.residual, source.available)
    assert frame.residual_places == 3
    assert frame.unavailable_places == 1


def test_drawing_does_not_repair_counts_by_measuring_the_masks() -> None:
    reading = OwnershipReading(
        "present",
        "unaltered",
        np.ones((1, 1), dtype=bool),
        np.zeros((1, 1), dtype=bool),
        19,
        23,
        29,
        31,
    )
    frame = ownership_panels(reading)
    assert (
        frame.claimed_places,
        frame.residual_places,
        frame.unavailable_places,
        frame.objects,
    ) == (
        19,
        23,
        29,
        31,
    )


@pytest.mark.parametrize("source", [None, object(), SimpleNamespace(code="measured")])
def test_relations_absence_is_not_drawn_as_a_study_without_interstices(source) -> None:
    reading = read_relations(source)
    frame = relations_panels(reading)
    assert frame.code == "construction_absent"
    assert frame.why == reading.why
    assert frame.interstices is reading.interstices


def test_relations_renderer_does_not_replace_a_future_reading_with_the_shell() -> None:
    subjects = (Interstice("facing_pair", 3, 7, "series", "a future construction"),)
    frame = relations_panels(RelationsReading("present", "given reading", subjects))
    assert frame.code == "present"
    assert frame.why == "given reading"
    assert frame.interstices is subjects
    assert frame.pairings is None


def _saved_record(tmp_path, comparison: str, interstices: list[dict]) -> tuple:
    """A minimal saved record for `partition_frames.saved_panels`: one member, every array real."""
    claims = np.array([[True, False], [False, True]])
    residual = ~claims
    disagreement = np.zeros((2, 2), dtype=bool)
    arrays = {
        "ownership_solitary_claims": claims,
        "ownership_solitary_residual": residual,
        "ownership_disagreement": disagreement,
    }
    artifact = tmp_path / "series.npz"
    np.savez_compressed(artifact, allow_pickle=False, **arrays)
    from hashlib import sha256

    descriptors = {
        name: {
            "shape": list(a.shape),
            "dtype": a.dtype.str,
            "digest": sha256(
                a.dtype.str.encode() + str(a.shape).encode() + a.tobytes()
            ).hexdigest(),
        }
        for name, a in arrays.items()
    }
    metadata = {
        "artifact": "series.npz",
        "arrays": descriptors,
        "ownership": {
            "code": "present",
            "why": "measured",
            "comparison": comparison,
            "disagreeing_places": 0,
            "disagreement_array": "ownership_disagreement",
            "members": [
                {
                    "parse": "solitary",
                    "code": "present",
                    "why": "measured",
                    "claimed_places": 2,
                    "residual_places": 2,
                    "unavailable_places": 0,
                    "objects": 2,
                    "claims_array": "ownership_solitary_claims",
                    "residual_array": "ownership_solitary_residual",
                }
            ],
        },
        "relations": {
            "code": "construction_absent",
            "why": "nothing built",
            "interstices": interstices,
            "pairings_code": None,
        },
    }
    return tmp_path, metadata


def test_the_partition_renderer_rebuilds_a_saved_interstice_as_the_stages_record(
    tmp_path,
) -> None:
    """Task 7.2: a saved interstice comes back as an `Interstice`, never as a bare dict."""
    partition_frames = pytest.importorskip("workbench.render.partition_frames")
    run, metadata = _saved_record(
        tmp_path,
        "member_absent",
        [
            {
                "kind": "facing_pair",
                "first": 1,
                "second": 2,
                "series_uid": "s",
                "provenance": "test",
            }
        ],
    )
    _, members, _, relations_frame = partition_frames.saved_panels(run, metadata)
    assert [parse for parse, _ in members] == ["solitary"]
    assert relations_frame.interstices == (
        Interstice("facing_pair", 1, 2, "s", "test"),
    )


def test_the_partition_renderer_never_draws_a_comparison_code_it_does_not_know(
    tmp_path,
) -> None:
    """MUST NOT: a saved comparison word outside `COMPARISONS` is refused by name, not drawn."""
    partition_frames = pytest.importorskip("workbench.render.partition_frames")
    run, metadata = _saved_record(tmp_path, "resolved_in_favour_of_solitary", [])
    with pytest.raises(ValueError, match="saved_comparison_code_unknown"):
        partition_frames.saved_panels(run, metadata)


def test_the_partition_renderer_never_draws_an_interstice_of_an_undeclared_kind(
    tmp_path,
) -> None:
    """MUST NOT: a saved construction with an anatomical kind is refused by the record itself."""
    partition_frames = pytest.importorskip("workbench.render.partition_frames")
    run, metadata = _saved_record(
        tmp_path,
        "compared",
        [
            {
                "kind": "femur_tibia",
                "first": 1,
                "second": 2,
                "series_uid": "s",
                "provenance": "test",
            }
        ],
    )
    with pytest.raises(ValueError, match="invalid_interstice_kind"):
        partition_frames.saved_panels(run, metadata)
