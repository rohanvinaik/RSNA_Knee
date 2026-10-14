"""The real entry point on the real files (knee.study.corpus): the 58 labeled studies and the 3 public test studies
in data/raw/, read whole. Skipped, with its reason shown, where the competition's files are not present."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from knee.study.corpus import LOCAL_ROOT, open_corpus, read_study
from knee.study.tables import labeled_uids, split_uids

ROOT = Path(__file__).resolve().parents[3] / LOCAL_ROOT
pytestmark = pytest.mark.skipif(
    not (ROOT / "train.csv").is_file(),
    reason="the competition's files are not in data/raw/",
)


def test_the_tables_hold_both_splits_and_the_58_labeled_studies() -> None:
    tables = open_corpus(ROOT).tables
    assert len(split_uids(tables, "train")) == 4407
    assert len(labeled_uids(tables)) == 58
    assert len(split_uids(tables, "test")) == 3
    assert tables.orphan_series == ()


@pytest.mark.parametrize("split", ["labeled", "test"])
def test_every_study_reads_whole_and_every_series_stacks(split: str) -> None:
    corpus = open_corpus(ROOT)
    uids = (
        labeled_uids(corpus.tables)
        if split == "labeled"
        else split_uids(corpus.tables, "test")
    )
    for uid in uids:
        study = read_study(corpus, uid)
        assert len(study.series) == len(study.row.series) > 0
        for series in study.series:
            on_disk = len(list(series.directory.glob("*.dcm")))
            assert series.stack == ("stackable",), (
                uid,
                series.row.series_uid,
                series.stack,
            )
            assert series.volume is not None and series.geometry is not None
            assert series.volume.shape[0] == len(series.slices) == on_disk
            assert series.volume.dtype in (np.dtype(np.uint16), np.dtype(np.int16))
            assert bool(np.all(np.diff(series.geometry.along_normal) > 0))
