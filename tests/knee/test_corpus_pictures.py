"""The corpus drawing (task 7.1a), both signs: its reader reconstitutes the study stage's own count
from the receipt the writer saves, refuses every drift by name, and the drawer refuses before it
draws. Every refusal is a returned code; nothing here raises."""

import json
import shutil
from types import MappingProxyType

import pytest

from knee.study.shape import CorpusShape
from knee.study.tables import LABELS
from workbench.measure.object_analysis import corpus_record
from workbench.render._out import PROJECT
from workbench.render.corpus_frames import Refusal, draw, saved_shape

FINDINGS = ("Fracture", "ACL", "Baker's")


def _shape() -> CorpusShape:
    """A corpus shape as the study stage would count it, with every mapping read-only."""
    return CorpusShape(
        studies=MappingProxyType({"train": 3, "test": 1}),
        series=MappingProxyType({"train": 7, "test": 2}),
        orphan_series=1,
        labeled=2,
        views=((("Axial", "1", "1"), 4, 2), (("Coronal", "0", "0"), 2, 1)),
        views_per_labeled_study=MappingProxyType({2: 1, 1: 1}),
        labels=MappingProxyType(
            {
                finding: MappingProxyType(
                    {"1": 1, "0": 1, "not_given": 1, "unrecognized": 0}
                )
                for finding in FINDINGS
            }
        ),
        reports=MappingProxyType({"present": 2, "blank": 1, "not_given": 0}),
        report_lengths=(10, 20, 30),
    )


def _saved() -> dict:
    """The receipt's `corpus` entry as the writer saves it: JSON round-tripped."""
    return json.loads(json.dumps(corpus_record(_shape()), allow_nan=False))


def test_the_corpus_reader_reconstitutes_the_stages_own_count() -> None:
    shape = _shape()
    read = saved_shape(_saved())
    assert isinstance(read, CorpusShape)
    assert dict(read.studies) == dict(shape.studies)
    assert dict(read.series) == dict(shape.series)
    assert (read.orphan_series, read.labeled) == (1, 2)
    assert read.views == shape.views
    assert dict(read.views_per_labeled_study) == {2: 1, 1: 1}
    assert {f: dict(c) for f, c in read.labels.items()} == {
        f: dict(c) for f, c in shape.labels.items()
    }
    assert dict(read.reports) == dict(shape.reports)
    assert read.report_lengths == (10, 20, 30)


def test_the_corpus_reader_refuses_every_drift_by_name_and_never_raises() -> None:
    # MUST NOT: draw a word the study stage does not say, a count that is not a whole number, a
    # finding the table does not carry, or two mappings that disagree about the splits.
    def drifted(change) -> dict:
        saved = _saved()
        change(saved)
        return saved

    def set_label_code(saved):
        saved["labels"]["ACL"]["maybe"] = 1

    def drop_split(saved):
        del saved["series"]["test"]

    cases = (
        ("not a record", "corpus_not_a_record"),
        (drifted(lambda s: s.pop("views")), "corpus_field_missing:views"),
        (
            drifted(lambda s: s["studies"].update(train=True)),
            "corpus_field_invalid:studies",
        ),
        (
            drifted(lambda s: s["reports"].update(spam=1)),
            "corpus_code_unknown:reports:spam",
        ),
        (
            drifted(lambda s: s["labels"].update(Femur={})),
            "corpus_finding_unknown:Femur",
        ),
        (drifted(set_label_code), "corpus_code_unknown:labels.ACL:maybe"),
        (drifted(drop_split), "corpus_splits_disagree"),
        (
            drifted(lambda s: s.update(report_lengths=[1, 2])),
            "corpus_field_invalid:report_lengths",
        ),
        (
            drifted(
                lambda s: s["views"].append({"view": ["A", "1", "1"], "series": 1})
            ),
            "corpus_field_invalid:views",
        ),
        (drifted(lambda s: s.update(labeled=-1)), "corpus_field_invalid:counts"),
    )
    for saved, code in cases:
        result = saved_shape(saved)
        assert isinstance(result, Refusal), code
        assert result.code == code
        assert result.why


def test_the_corpus_drawer_refuses_before_it_draws_and_never_raises(tmp_path) -> None:
    inside = PROJECT / "data" / "pictures" / "test-corpus-frames-refusals"
    assert draw("not a mapping", inside)["refusal"] == "receipt_not_a_mapping"
    assert draw({"records": []}, inside)["refusal"] == "corpus_not_saved"
    assert draw({"corpus": "nope"}, inside)["refusal"] == "corpus_not_a_record"
    # MUST NOT: write a rendered knee outside the private data directory.
    assert draw({"corpus": _saved()}, tmp_path)["refusal"] == "out_outside_data"
    assert not inside.exists()


def test_the_corpus_drawer_draws_the_saved_count_when_matplotlib_is_supplied() -> None:
    pytest.importorskip("matplotlib")
    target = PROJECT / "data" / "pictures" / "test-corpus-frames"
    try:
        manifest = draw({"corpus": _saved()}, target)
        assert "refusal" not in manifest
        assert manifest["image"] == "corpus.png"
        assert (target / "corpus.png").exists()
        # the findings drawn are the saved ones, in the TABLE's order and never the record's
        assert manifest["findings"] == [f for f in LABELS if f in FINDINGS]
        assert manifest["splits"] == ["train", "test"]
    finally:
        shutil.rmtree(target, ignore_errors=True)
