from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from knee.encoding import h5_store, mri_spec, operation
from knee.encoding.places import (
    BankSpec,
    LayoutSpec,
    MetricKind,
    MetricSpec,
    compile_layout,
)

RUNNER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "run_interiors.py"
SPEC = importlib.util.spec_from_file_location("candidate_run_interiors", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def _manifest(study_uid: str) -> dict:
    spec = LayoutSpec(
        "raw-runner-test-v1",
        "carrier-raw-runner-test-v1",
        (
            BankSpec(
                "signal", "signal facet", (MetricSpec("tone", MetricKind.DIGIT, ()),)
            ),
        ),
    )
    compiled = compile_layout(spec)
    assert compiled is not None
    reference = "reference:raw-runner-test"
    return {
        "study_uid": study_uid,
        "encoded_arrays": {},
        "mode": "full",
        "object_composition": {
            "schema": "knee_object_profiles/v1",
            "carrier_identity": compiled.carrier_id,
            "layout_fingerprint": compiled.fingerprint,
            "registry_fingerprint": "raw-runner-registry",
            "layout": {
                "version": compiled.version,
                "carrier_id": compiled.carrier_id,
                "fingerprint": compiled.fingerprint,
                "banks": [
                    {
                        "name": "signal",
                        "facet": "signal facet",
                        "metrics": [{"name": "tone", "kind": "digit", "words": []}],
                    }
                ],
            },
            "objects": {
                "acl": {
                    "status": "partial",
                    "preparation_status": "ok",
                    "reference_set_identity": reference,
                    "count_layout_id": f"{compiled.version}:{compiled.fingerprint}:{reference}",
                    "sparse_counts": [["signal", 2, 5]],
                    "assembly": {"code": "partial", "batches": []},
                }
            },
        },
    }


def _corpus(uids: tuple[str, ...]):
    return SimpleNamespace(
        tables=SimpleNamespace(
            studies={
                uid: SimpleNamespace(study_uid=uid, series=(f"series-{uid}",))
                for uid in uids
            }
        )
    )


def _patch_encoder(monkeypatch, calls: dict):
    def make_spec(*, retained_ordinary_profiles, include_coarse):
        calls["make_spec"] = calls.get("make_spec", 0) + 1
        calls["make_options"] = (retained_ordinary_profiles, include_coarse)
        return {"storage": "h5", "base": "built-in"}

    def validate(spec):
        calls["validate"] = calls.get("validate", 0) + 1
        calls["spec_retain_sources"] = spec["retain_object_sources"]
        return {
            "storage": "h5",
            "retain_object_sources": True,
            "spec": spec,
        }

    monkeypatch.setattr(mri_spec, "make_mri_spec", make_spec)
    monkeypatch.setattr(operation, "validate_spec", validate)

    def encode(result, run_dir, main_run, spec, output, *, prepared):
        calls["encode"] = calls.get("encode", 0) + 1
        assert result["study_uid"] in output.name
        assert prepared["spec"] is spec
        archive = output.with_name(output.name.removesuffix(".json.xz") + ".h5")
        h5_store.write_h5(archive, _manifest(result["study_uid"]), {})
        return {
            "archive": str(archive),
            "manifest": str(archive),
            "work": {"encoder_fixture": 1},
        }

    monkeypatch.setattr(operation, "encode_study", encode)


def test_raw_source_factory_reuses_corpus_and_spec_and_cleans_per_study(
    tmp_path, monkeypatch
):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    uids = ("study-001", "study-002")
    corpus = _corpus(uids)
    series_paths = {}
    for uid in uids:
        path = tmp_path / uid / "series"
        path.mkdir(parents=True)
        series_paths[uid] = path
    calls: dict = {"open": 0, "measure": []}
    monkeypatch.setattr(
        runner,
        "opened",
        lambda root: calls.__setitem__("open", calls["open"] + 1) or corpus,
    )
    monkeypatch.setattr(
        runner,
        "series_directory",
        lambda corpus, study, series: series_paths[study.study_uid],
    )

    def measure(corpus_arg, uid, run_dir, main_run, drawn):
        calls["measure"].append((uid, drawn))
        run_dir.mkdir()
        main_run.mkdir()
        return {"study_uid": uid}

    def verify(encoded, *, work):
        calls["verify"] = calls.get("verify", 0) + 1
        assert Path(encoded["archive"]).is_file()
        work["verified"] = 1

    monkeypatch.setattr(runner, "measure_study", measure)
    monkeypatch.setattr(runner, "_verify_competition_product", verify)
    _patch_encoder(monkeypatch, calls)
    args = SimpleNamespace(
        root=tmp_path,
        study_uid=list(uids),
        labeled=False,
        split=None,
        diagnostic_scratch=scratch,
        diagnostic_output=tmp_path / "diagnostic-output",
    )
    factory = runner._generated_study_source_factory(args)
    studies = factory(None)
    first_uid, first_profiles, first_source = next(studies)
    first_product = first_source["product_path"]
    assert first_uid == uids[0]
    assert first_profiles[0].source_id == first_uid
    assert first_profiles[0].bundle.counts[0][2] == 5
    assert first_source["product_transient"] is False
    assert first_source["product_retained"] is True
    assert first_product.parent == args.diagnostic_output / "objects"
    assert first_source["source_concurrency"] == 1
    assert first_source["full_anatomy_runs"] == 1
    assert first_product.is_file()
    assert calls["open"] == calls["validate"] == calls["make_spec"] == 1
    assert calls["make_options"] == (True, True)
    assert calls["spec_retain_sources"] is True
    assert calls["measure"] == [(uids[0], False)]
    assert calls["verify"] == 1

    second_uid, second_profiles, _ = next(studies)
    assert second_uid == uids[1]
    assert second_profiles[0].source_id == second_uid
    assert first_product.is_file()
    assert calls["measure"] == [(uids[0], False), (uids[1], False)]
    studies.close()
    assert not tuple(scratch.iterdir())
    assert first_product.is_file()
    assert len(tuple((args.diagnostic_output / "objects").glob("*.h5"))) == 2


@pytest.mark.parametrize(
    ("uids", "expected"),
    [
        (("missing",), "diagnostic_generated_study_uid_missing"),
        (("study-001", "study-001"), "diagnostic_generated_duplicate_study_uid"),
    ],
)
def test_raw_source_factory_refuses_missing_or_duplicate_uid_before_measurement(
    tmp_path, monkeypatch, uids, expected
):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    corpus = _corpus(("study-001",))
    calls = {"measure": 0}
    monkeypatch.setattr(runner, "opened", lambda root: corpus)
    monkeypatch.setattr(
        runner, "measure_study", lambda *args: calls.__setitem__("measure", 1)
    )
    args = SimpleNamespace(
        root=tmp_path,
        study_uid=list(uids),
        labeled=False,
        split=None,
        diagnostic_scratch=scratch,
        diagnostic_output=tmp_path / "diagnostic-output",
    )
    with pytest.raises(ValueError, match=expected):
        runner._generated_study_source_factory(args)(None)
    assert calls["measure"] == 0


def test_raw_source_factory_uses_pipeline_selected_cohort_uids(tmp_path, monkeypatch):
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    corpus = _corpus(("study-001", "study-002"))
    series_paths = {}
    for uid in corpus.tables.studies:
        path = tmp_path / uid / "series"
        path.mkdir(parents=True)
        series_paths[uid] = path
    calls: dict = {}
    monkeypatch.setattr(runner, "opened", lambda root: corpus)
    monkeypatch.setattr(
        runner,
        "series_directory",
        lambda corpus_arg, study, series: series_paths[study.study_uid],
    )

    def measure(corpus_arg, uid, run_dir, main_run, drawn):
        calls.setdefault("measured", []).append(uid)
        run_dir.mkdir()
        main_run.mkdir()
        return {"study_uid": uid}

    monkeypatch.setattr(runner, "measure_study", measure)
    monkeypatch.setattr(
        runner, "_verify_competition_product", lambda encoded, *, work: None
    )
    _patch_encoder(monkeypatch, calls)
    args = SimpleNamespace(
        root=tmp_path,
        study_uid=["study-001"],
        labeled=False,
        split=None,
        diagnostic_scratch=scratch,
        diagnostic_output=tmp_path / "diagnostic-output",
    )
    studies = runner._generated_study_source_factory(args)(("study-002",))
    try:
        uid, profiles, source = next(studies)
        assert uid == "study-002"
        assert profiles[0].source_id == uid
        assert source["selection"] == "pipeline_cohort"
    finally:
        studies.close()
    assert calls["measured"] == ["study-002"]


@pytest.mark.parametrize(
    ("specification", "exception", "expected"),
    [
        ("invalid", ValueError, "diagnostic_readout_malformed"),
        (
            "not_a_real_module_983abc:call",
            ValueError,
            "diagnostic_readout_import_failed",
        ),
        ("math:missing_name", ValueError, "diagnostic_readout_callable_missing"),
        ("math:pi", TypeError, "diagnostic_readout_not_callable"),
    ],
)
def test_diagnostic_readout_plugin_loader_names_invalid_plugin_states(
    specification, exception, expected
):
    with pytest.raises(exception, match=expected):
        runner._diagnostic_readout(specification)


def test_main_passes_raw_selector_factory_and_no_default_readout_to_pipeline(
    tmp_path, monkeypatch, capsys
):
    from knee.diagnosis import pipeline

    scratch = tmp_path / "scratch"
    scratch.mkdir()
    corpus = _corpus(("study-001",))
    series_path = tmp_path / "study-001" / "series"
    series_path.mkdir(parents=True)
    monkeypatch.setattr(runner, "opened", lambda root: corpus)
    monkeypatch.setattr(runner, "series_directory", lambda *args: series_path)
    calls: dict = {"measure": [], "open": 0}
    monkeypatch.setattr(
        runner,
        "opened",
        lambda root: calls.__setitem__("open", calls["open"] + 1) or corpus,
    )

    def measure(corpus_arg, uid, run_dir, main_run, drawn):
        calls["measure"].append(uid)
        run_dir.mkdir()
        main_run.mkdir()
        return {"study_uid": uid}

    monkeypatch.setattr(runner, "measure_study", measure)
    monkeypatch.setattr(
        runner, "_verify_competition_product", lambda encoded, *, work: None
    )
    _patch_encoder(monkeypatch, calls)

    def dispatch(args, *, study_source, source_mode, probability_readout):
        args.diagnostic_output.mkdir()
        assert source_mode == "generated_full_reference"
        assert probability_readout is None
        source_iterator = study_source(None)
        try:
            uid, profiles, source = next(source_iterator)
            assert uid == "study-001"
            assert profiles[0].source_id == uid
            assert source["source_concurrency"] == 1
        finally:
            source_iterator.close()
        return {"action": "teach", "studies": 1}

    monkeypatch.setattr(pipeline, "run_diagnostic_cli", dispatch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(RUNNER_PATH),
            "--study-uid",
            "study-001",
            "--diagnostic-mode",
            "teach",
            "--diagnostic-memory",
            str(tmp_path / "memory"),
            "--diagnostic-output",
            str(tmp_path / "output"),
            "--diagnostic-revision",
            "test-r1",
            "--diagnostic-scratch",
            str(scratch),
        ],
    )
    runner.main()
    assert calls["measure"] == ["study-001"]
    assert calls["open"] == 1
    assert not tuple(scratch.iterdir())
    assert '"action": "teach"' in capsys.readouterr().out
