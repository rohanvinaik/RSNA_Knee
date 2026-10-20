"""The parallel branch of `run_interiors.main()` keeps at most `workers` studies, the head result
included, in order, and cancels what is queued when it stops."""

import gc
import importlib.util
import sys
import weakref
from pathlib import Path
from types import SimpleNamespace
from typing import ClassVar

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


@pytest.fixture(scope="module")
def run_interiors():
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "run_interiors", SCRIPTS / "run_interiors.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_interiors"] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop("run_interiors", None)
        sys.path.remove(str(SCRIPTS))


class Result:
    def __init__(self, uid):
        self.uid = uid


class FakeFuture:
    def __init__(self, fn, args, defer, on_result):
        self.fn, self.args, self.on_result = fn, args, on_result
        self.value = None
        self.done = False
        if not defer:
            self._run()

    def _run(self):
        self.value = self.fn(*self.args)
        self.on_result(self.value)
        self.done = True

    def result(self):
        if not self.done:
            self._run()
        return self.value

    def cancel(self):
        return True


class FakePool:
    """Runs every job at submit except the first, the slow one, which runs when asked for."""

    instances: ClassVar[list] = []

    def __init__(self, max_workers=None):
        self.max_workers = max_workers
        self.futures: list = []
        self.results: list = []
        self.submitted: list = []
        self.max_owned = 0
        FakePool.instances.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def track_result(self, result):
        self.results.append(weakref.ref(result))

    def owned(self):
        gc.collect()
        futures = [f for f in (w() for w in self.futures) if f is not None]
        results = [r for r in (w() for w in self.results) if r is not None]
        held_ids = {id(f.value) for f in futures if f.value is not None}
        unheld_results = sum(1 for result in results if id(result) not in held_ids)
        return len(futures) + unheld_results

    def submit(self, fn, *args):
        defer = not self.submitted
        self.submitted.append(args[1])
        future = FakeFuture(fn, args, defer, self.track_result)
        self.futures.append(weakref.ref(future))
        self.max_owned = max(self.max_owned, self.owned())
        return future


def drive(run_interiors, monkeypatch, tmp_path, uids, workers, failing_uid=None):
    FakePool.instances = []
    reported = []

    def stub_measure(root, uid, run_dir, main_run, drawn):
        return Result(uid)

    def stub_report(result, args, receipt_batches):
        pool = FakePool.instances[0]
        pool.max_owned = max(pool.max_owned, pool.owned())
        reported.append((result.uid, len(pool.submitted), receipt_batches))
        if result.uid == failing_uid:
            raise RuntimeError("report failed")

    monkeypatch.setattr(run_interiors, "ProcessPoolExecutor", FakePool)
    monkeypatch.setattr(
        run_interiors, "opened", lambda root: SimpleNamespace(tables=None)
    )
    monkeypatch.setattr(run_interiors, "measure_study_at", stub_measure)
    monkeypatch.setattr(run_interiors, "report", stub_report)
    argv = [
        "run_interiors",
        "--study-uid",
        *uids,
        "--workers",
        str(workers),
        "--root",
        str(tmp_path),
        "--run",
        str(tmp_path / "run"),
        "--main-run",
        str(tmp_path / "main"),
    ]
    monkeypatch.setattr(sys, "argv", argv)
    run_interiors.main()
    return reported, FakePool.instances[0]


def test_main_keeps_at_most_workers_studies_and_reports_in_order(
    run_interiors, monkeypatch, tmp_path
):
    uids = [f"s{i}" for i in range(7)]
    workers = 3
    reported, pool = drive(run_interiors, monkeypatch, tmp_path, uids, workers)
    assert [uid for uid, _, _ in reported] == uids
    assert all(owner is reported[0][2] for _, _, owner in reported)
    assert reported[0][2] is not None
    assert pool.submitted == uids
    assert pool.max_workers == workers
    assert pool.max_owned <= workers
    # While a report runs, nothing beyond the window has been pulled or submitted.
    for k, (_, submitted, _) in enumerate(reported):
        assert submitted == min(len(uids), workers + k)


def test_main_with_fewer_studies_than_workers(run_interiors, monkeypatch, tmp_path):
    reported, pool = drive(run_interiors, monkeypatch, tmp_path, ["a", "b"], 8)
    assert [uid for uid, _, _ in reported] == ["a", "b"]
    assert all(owner is reported[0][2] for _, _, owner in reported)
    assert reported[0][2] is not None
    assert pool.max_workers == 2
    assert pool.max_owned <= 2


class Recorded:
    def __init__(self, index, outcome):
        self.index, self.outcome = index, outcome
        self.cancelled = False

    def result(self):
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome

    def cancel(self):
        self.cancelled = True
        return True


def recording_submit(outcomes):
    made: list[Recorded] = []

    def submit(job):
        future = Recorded(job, outcomes(job))
        made.append(future)
        return future

    return submit, made


def test_empty_and_single_iterables(run_interiors):
    submit, made = recording_submit(lambda job: job)
    assert list(run_interiors.bounded_results(submit, [], 3)) == []
    assert made == []
    assert list(run_interiors.bounded_results(submit, [5], 3)) == [5]
    assert [f.cancelled for f in made] == [False]


def test_limit_must_be_positive(run_interiors):
    submit, _ = recording_submit(lambda job: job)
    with pytest.raises(ValueError):
        list(run_interiors.bounded_results(submit, [1], 0))


def test_jobs_are_pulled_lazily_up_to_the_limit(run_interiors):
    pulled = []

    def producer():
        for i in range(10):
            pulled.append(i)
            yield i

    submit, _made = recording_submit(lambda job: job)
    iterator = run_interiors.bounded_results(submit, producer(), 3)
    assert pulled == []
    assert next(iterator) == 0
    assert pulled == [0, 1, 2]
    assert next(iterator) == 1
    assert pulled == [0, 1, 2, 3]
    iterator.close()


def test_late_worker_exception_propagates_and_cancels_the_queue(run_interiors):
    boom = RuntimeError("worker failed")
    submit, made = recording_submit(lambda job: boom if job == 2 else job)
    iterator = run_interiors.bounded_results(submit, range(6), 3)
    assert next(iterator) == 0
    assert next(iterator) == 1
    with pytest.raises(RuntimeError, match="worker failed"):
        next(iterator)
    assert [f.index for f in made] == [0, 1, 2, 3, 4]
    assert [f.index for f in made if f.cancelled] == [3, 4]


def test_early_close_cancels_pending_futures(run_interiors):
    submit, made = recording_submit(lambda job: job)
    iterator = run_interiors.bounded_results(submit, range(6), 3)
    assert next(iterator) == 0
    iterator.close()
    assert [f.index for f in made] == [0, 1, 2]
    assert [f.index for f in made if f.cancelled] == [1, 2]


def test_main_closes_result_iterator_when_reporting_fails(
    run_interiors, monkeypatch, tmp_path
):
    original = run_interiors.bounded_results
    closed = []

    def tracked_results(*args):
        try:
            yield from original(*args)
        finally:
            closed.append(True)

    monkeypatch.setattr(run_interiors, "bounded_results", tracked_results)
    with pytest.raises(RuntimeError, match="report failed"):
        drive(run_interiors, monkeypatch, tmp_path, ["a", "b", "c"], 2, failing_uid="a")
    assert closed == [True]
    assert FakePool.instances[0].submitted == ["a", "b"]


def test_consumer_exception_closes_and_cancels(run_interiors):
    submit, made = recording_submit(lambda job: job)
    with pytest.raises(KeyError):
        for result in run_interiors.bounded_results(submit, range(6), 2):
            raise KeyError(result)
    gc.collect()
    assert [f.index for f in made if f.cancelled] == [1]


def test_completed_study_working_state_is_released_before_next_submit(run_interiors):
    class WorkingArray:
        def __init__(self, uid):
            self.payload = bytearray(uid.encode("utf-8") * 32)

    class WorkingState:
        def __init__(self, uid):
            self.uid = uid
            self.arrays = WorkingArray(uid)
            self.encoding_cache = {"verified_arrays": [self.arrays]}

    class CompletedFuture:
        def __init__(self, uid):
            self.uid = uid
            self.value = None

        def result(self):
            self.value = WorkingState(self.uid)
            return self.value

        def cancel(self):
            return True

    prior_states = []
    published = []

    def submit(uid):
        gc.collect()
        if prior_states:
            assert prior_states[-1]() is None
        return CompletedFuture(uid)

    results = run_interiors.bounded_results(submit, (f"study-{i}" for i in range(4)), 1)
    for state in results:
        # Model the existing encoder's source read and the writer's durable summary;
        # only the compact result outlives this iteration.
        published.append((state.uid, bytes(state.arrays.payload)))
        prior_states.append(weakref.ref(state))
        prior_states.append(weakref.ref(state.encoding_cache["verified_arrays"][0]))
        state = None

    gc.collect()
    assert [uid for uid, _payload in published] == [f"study-{i}" for i in range(4)]
    assert all(reference() is None for reference in prior_states)
