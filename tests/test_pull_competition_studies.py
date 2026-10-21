"""The competition-study puller (`scripts/pull_competition_studies.py`, a development tool beside the run,
loaded here from its path). Nothing here reaches the network: a fake competition serves a listing a few
rows at a time and files of the listed sizes, a stub `kaggle` executable stands in for the CLI, and
`sleep` and the free-disk figure are handed in.

Pinned: the CLI's output is parsed (a token line or none, an unexpected line before the header fails
loudly) and its errors are cleaned; the listing is cached page by page, stops once past the studies
asked for, resumes, survives an uncommitted page file, and walks again when the server ignores a stale
cursor; studies are chosen in file order and without `train.csv`; a study reaches `train_series/` only
whole, by renaming, and one already there is neither listed nor touched; staged files are skipped by
size, a wrong size is fetched again, failures are named and kept for the rerun, 429s are counted, 401
and 403 stop the run, a study the listing does not hold is a named failure; the disk margin refuses."""

import errno
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

TOOL = (
    Path(__file__).resolve().parent.parent / "scripts" / "pull_competition_studies.py"
)
STUDIES = ["1.2.100", "1.2.200", "1.2.300", "1.2.400"]
FILES_PER_SERIES = 3
BYTES_PER_STUDY = 2 * sum(140 + number for number in range(1, FILES_PER_SERIES + 1))


@pytest.fixture(scope="module")
def tool():
    spec = importlib.util.spec_from_file_location("pull_competition_studies", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # the dataclasses look their module up here
    spec.loader.exec_module(module)
    yield module
    del sys.modules[spec.name]


def series_of(study: str) -> list[str]:
    return [f"{study}.1", f"{study}.2"]


def listing(skip_series=(), extra=()) -> list[tuple[str, int]]:
    """The competition's files in its order: a few top-level files, one test study, four training studies
    of two series with three files each."""
    rows = [
        ("sample_submission.csv", 470),
        ("test.csv", 212),
        ("test_series.csv", 2213),
        ("test_series/9.9/9.9.1/9.9.1.1.dcm", 150),
        ("train.csv", 99),
        ("train_series.csv", 98),
    ]
    for study in STUDIES:
        for series in series_of(study):
            if series in skip_series:
                continue
            for number in range(1, FILES_PER_SERIES + 1):
                rows.append(
                    (f"train_series/{study}/{series}/{number}.dcm", 140 + number)
                )
    return sorted(rows + list(extra))


def dicom(size: int) -> bytes:
    return b"\0" * 128 + b"DICM" + b"x" * (size - 132)


class FakeCompetition:
    """The two calls of the Fetcher, served from a list. Cursors carry an epoch: one from another epoch
    is not recognised and gets the first page, as the real server does with a cursor it does not know."""

    def __init__(self, rows, page_len=4, epoch="E1"):
        self.rows = rows
        self.sizes = dict(rows)
        self.page_len = page_len
        self.epoch = epoch
        self.list_calls: list[str | None] = []
        self.list_failures: list[Exception] = []
        self.downloads: list[str] = []
        self.failures: dict[str, list[Exception]] = {}
        self.writer = None  # replaces the file written: writer(directory, name, size)

    def pages(self) -> int:
        return -(-len(self.rows) // self.page_len)

    def list_page(self, cursor, page_size):
        self.list_calls.append(cursor)
        if self.list_failures:
            raise self.list_failures.pop(0)
        start = 0
        epoch, _, offset = (cursor or "").partition(":")
        if epoch == self.epoch:
            start = int(offset)
        end = start + self.page_len
        following = f"{self.epoch}:{end}" if end < len(self.rows) else None
        return self.rows[start:end], following

    def download(self, name, directory):
        self.downloads.append(name)
        queue = self.failures.get(name)
        if queue:
            raise queue.pop(0)
        size = self.sizes[name]
        if self.writer:
            self.writer(directory, name, size)
        else:
            (directory / name.rsplit("/", 1)[1]).write_bytes(dicom(size))


def make_root(tmp_path: Path, on_disk=()) -> Path:
    root = tmp_path / "root"
    root.mkdir(parents=True)
    lines = [
        "StudyInstanceUID,SeriesInstanceUID,Fluid_Sensitive,Fat_Suppression,Anatomical_Plane"
    ]
    lines += [f"{s},{one},1,1,Sagittal" for s in STUDIES for one in series_of(s)]
    (root / "train_series.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for study in on_disk:
        for one in series_of(study):
            folder = root / "train_series" / study / one
            folder.mkdir(parents=True)
            (folder / "1.dcm").write_bytes(b"existing")
    return root


def snapshot(path: Path) -> dict:
    found = {}
    for entry in sorted(path.rglob("*")):
        info = entry.stat()
        found[str(entry.relative_to(path))] = (info.st_size, info.st_mtime_ns)
    return found


def tree(path: Path) -> set[str]:
    return {str(p.relative_to(path)) for p in path.rglob("*") if p.is_file()}


class Run:
    def __init__(self, tool, tmp_path: Path, fetcher, on_disk=()):
        self.tool = tool
        self.fetcher = fetcher
        self.root = make_root(tmp_path, on_disk)
        self.state = tmp_path / "state"
        self.log: list[str] = []
        self.sleeps: list[float] = []
        self.free = 10**13

    def args(self, command, *extra):
        return [
            command,
            "--root",
            str(self.root),
            "--state-dir",
            str(self.state),
            *extra,
        ]

    def go(self, command, *extra, free=None):
        free = free or self.free
        measure = free if callable(free) else (lambda path: free)
        return self.tool.main(
            self.args(command, *extra),
            fetcher=self.fetcher,
            say=self.log.append,
            sleep=self.sleeps.append,
            free_bytes=measure,
        )

    def receipt(self) -> dict:
        found = sorted((self.state / "receipts").glob("pull-*.json"))
        return json.loads(found[-1].read_text(encoding="utf-8"))

    def index(self):
        return self.tool.Index.load(self.state / "index", self.tool.COMPETITION)

    def final(self, study: str) -> Path:
        return self.root / "train_series" / study


# The CLI's output and errors.


def test_listing_output_with_a_token_line_is_parsed(tool) -> None:
    out = "Next Page Token = abc\nname,size,creationDate\nx.csv,5,2026-09-19 00:43:32.131000\ny/z.dcm,7,2026\n"
    assert tool.parse_listing(out) == ([("x.csv", 5), ("y/z.dcm", 7)], "abc")


def test_the_last_page_has_no_token_line(tool) -> None:
    rows, cursor = tool.parse_listing(
        "name,size,creationDate\nx.csv,5,2026-09-19 00:43:32\n"
    )
    assert rows == [("x.csv", 5)] and cursor is None
    assert tool.parse_listing("No files found\n") == ([], None)


def test_an_unexpected_line_before_the_header_fails_loudly_without_the_cursor(
    tool,
) -> None:
    out = "Next Page Token = SECRETCURSOR\nWarning: something new\nname,size,creationDate\nx.csv,5,0\n"
    with pytest.raises(tool.PullError) as caught:
        tool.parse_listing(out)
    assert "Warning: something new" in str(caught.value)
    assert "SECRETCURSOR" not in str(caught.value)
    with pytest.raises(tool.PullError):
        tool.parse_listing("name,size,creationDate\nx.csv,not-a-number,0\n")
    with pytest.raises(tool.PullError):
        tool.parse_listing("")


def test_error_text_keeps_one_line_without_urls_queries_tokens_or_the_cursor(
    tool,
) -> None:
    text = (
        "404 Client Error: Not Found for url: https://api.example/x?sig=ABC&t=1\nmore\n"
    )
    assert (
        tool.clean_error(text)
        == "404 Client Error: Not Found for url: https://api.example/x"
    )
    assert tool.clean_error("denied for KGAT_abc123 here") == "denied for <token> here"
    assert tool.clean_error("Authorization: Bearer abc.def") == "Authorization: <token>"
    assert "CURSOR1" not in tool.clean_error("bad token CURSOR1 given", ["CURSOR1"])
    assert (
        tool.clean_error(
            "Traceback (most recent call last):\n  File x\nValueError: nope\n"
        )
        == "ValueError: nope"
    )
    assert tool.clean_error("  \n") == "no error text"


STUB = """
import json, pathlib, sys
here = pathlib.Path(sys.argv[0]).resolve().parent
with (here / "calls.jsonl").open("a") as handle:
    handle.write(json.dumps(sys.argv[1:]) + "\\n")
args = sys.argv[1:]
if args[1] == "files":
    if "--page-token" in args:
        print("name,size,creationDate")
        print("b.dcm,3,2026-01-01 00:00:00")
    else:
        print("Next Page Token = tok-1")
        print("name,size,creationDate")
        print("a.csv,2,2026-01-01 00:00:00")
elif args[1] == "download":
    name = args[args.index("-f") + 1]
    if name == "missing":
        sys.stderr.write("404 Client Error: Not Found for url: https://api.example/x?sig=SECRET\\n")
        sys.exit(1)
    (pathlib.Path(args[args.index("-p") + 1]) / name.rsplit("/", 1)[1]).write_bytes(b"abc")
"""


def test_the_cli_is_called_with_csv_never_verbose_and_its_errors_are_cleaned(
    tool, tmp_path
) -> None:
    stub = tmp_path / "bin" / "kaggle"
    stub.parent.mkdir()
    stub.write_text(f"#!{sys.executable}\n{STUB}", encoding="utf-8")
    stub.chmod(0o755)
    cli = tool.KaggleCli(str(stub), "comp")
    assert cli.list_page(None, 200) == ([("a.csv", 2)], "tok-1")
    assert cli.list_page("tok-1", 200) == ([("b.dcm", 3)], None)
    cli.download("train_series/s/t/u.dcm", tmp_path)
    assert (tmp_path / "u.dcm").read_bytes() == b"abc"
    with pytest.raises(tool.FetchError) as caught:
        cli.download("missing", tmp_path)
    assert caught.value.status == 404
    assert "SECRET" not in str(caught.value) and "?" not in str(caught.value)
    calls = [
        json.loads(line)
        for line in (stub.parent / "calls.jsonl").read_text().splitlines()
    ]
    assert all("-v" not in call and "--verbose" not in call for call in calls)
    listing_calls = [call for call in calls if call[1] == "files"]
    assert all(call[call.index("--format") + 1] == "csv" for call in listing_calls)
    assert ["--page-token" in call for call in listing_calls] == [False, True]
    with pytest.raises(tool.PullError, match="cannot run"):
        tool.KaggleCli(str(tmp_path / "nope"), "comp").list_page(None, 200)


# Choosing.


def test_studies_are_chosen_in_file_order_among_those_not_on_disk(tool) -> None:
    order = ["a", "b", "c", "d"]
    series = {s: [s + "1"] for s in order}
    assert tool.choose_studies(order, series, {"a", "c"}, 2, None) == (["b", "d"], [])
    assert tool.choose_studies(order, series, {"a", "c"}, 1, None) == (["b"], [])
    assert tool.choose_studies(order, series, {"a"}, None, ["d", "a", "b"]) == (
        ["b", "d"],
        ["a"],
    )
    with pytest.raises(tool.PullError, match="not a training study"):
        tool.choose_studies(order, series, set(), None, ["zz"])


def test_choosing_never_opens_train_csv(tool, tmp_path) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    (run.root / "train.csv").mkdir()  # opening it as a file would fail
    assert run.go("pull", "--studies", "2", "--dry-run") == 0
    assert run.fetcher.downloads == []


def test_studies_n_skips_studies_on_disk_and_stands_nothing_in_for_a_failure(
    tool, tmp_path
) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()), on_disk=["1.2.100"])
    bad = "train_series/1.2.200/1.2.200.1/2.dcm"
    run.fetcher.failures[bad] = [tool.FetchError("boom", 500)] * 10
    assert run.go("pull", "--studies", "2", "--retries", "0") == 1
    assert run.final("1.2.300").is_dir()
    assert not run.final("1.2.200").exists() and not run.final("1.2.400").exists()
    assert [f["file"] for f in run.receipt()["failures"]] == [bad]
    run.fetcher.failures.clear()
    assert (
        run.go("pull", "--studies", "1") == 0
    )  # the failed study is chosen again, first
    assert run.final("1.2.200").is_dir() and not run.final("1.2.400").exists()


# The listing cache.


def bound(tool, study: str) -> str:
    return tool.study_bound(study)


def test_a_study_is_covered_only_past_its_path_prefix(tool, tmp_path) -> None:
    index = tool.Index.load(tmp_path / "idx", "c")
    assert not index.covers(bound(tool, "1.2.200"))
    index.state["last_name"] = (
        "train_series/1.2.200/1.2.200.2/3.dcm"  # inside the study
    )
    assert not index.covers(bound(tool, "1.2.200"))
    assert index.covers(bound(tool, "1.2.100"))
    index.state["last_name"] = "train_series/1.2.300/1.2.300.1/1.dcm"  # beyond it
    assert index.covers(bound(tool, "1.2.200"))
    index.state["last_name"] = ""
    index.state["complete"] = True
    assert index.covers(bound(tool, "1.2.200")) and index.covers(None)
    assert bound(tool, "1.2.200") > "train_series/1.2.200/zzz"
    assert bound(tool, "1.2.200") < "train_series/1.2.2000/a"


def test_index_stops_once_past_the_studies_asked_for(tool, tmp_path) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    assert run.go("index", "--study-uid", "1.2.100") == 0
    assert len(run.fetcher.list_calls) < run.fetcher.pages()
    index = run.index()
    assert not index.state["complete"] and index.covers(bound(tool, "1.2.100"))
    files = index.files_of({"1.2.100"})["1.2.100"]
    assert len(files) == 2 * FILES_PER_SERIES


def test_index_resumes_from_the_saved_cursor_and_lists_every_row_once(
    tool, tmp_path
) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    assert run.go("index", "--study-uid", "1.2.100") == 0
    first_calls = len(run.fetcher.list_calls)
    assert run.go("index") == 0
    assert (
        run.fetcher.list_calls[first_calls] is not None
    )  # it went on from the saved cursor
    index = run.index()
    assert index.state["complete"] and index.state["rows"] == len(listing())
    rows = [row for number in range(index.state["pages"]) for row in index.page(number)]
    assert rows == listing()


def test_an_uncommitted_page_file_is_ignored_and_overwritten(tool, tmp_path) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    assert run.go("index", "--study-uid", "1.2.100") == 0
    index = run.index()
    stray = index.page_path(
        index.state["pages"]
    )  # a page written, its state never saved
    stray.write_bytes(b"not a gzip file")
    assert run.go("index") == 0
    index = run.index()
    rows = [row for number in range(index.state["pages"]) for row in index.page(number)]
    assert rows == listing()


def test_a_stale_cursor_walks_the_listing_again_without_duplicates(
    tool, tmp_path
) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing(), epoch="E1"))
    assert run.go("index", "--study-uid", "1.2.200") == 0
    run.fetcher = FakeCompetition(
        listing(), epoch="E2"
    )  # the saved cursor means nothing to it
    assert run.go("index") == 0
    assert any("walking it again" in line for line in run.log)
    index = run.index()
    rows = [row for number in range(index.state["pages"]) for row in index.page(number)]
    assert rows == listing() and index.state["complete"]


def test_a_listing_out_of_order_is_refused(tool, tmp_path, capsys) -> None:
    within = listing()
    within[1], within[2] = within[2], within[1]  # inside the first page
    run = Run(tool, tmp_path / "within", FakeCompetition(within))
    assert run.go("index", "--study-uid", "1.2.100") == 2
    assert "not in increasing path order" in capsys.readouterr().err
    assert not (run.state / "index" / "state.json").exists()  # nothing was kept
    across = listing()
    across[3], across[4] = across[4], across[3]  # a row that belongs to the page before
    run = Run(tool, tmp_path / "across", FakeCompetition(across))
    assert run.go("index", "--study-uid", "1.2.100") == 2
    assert "across pages" in capsys.readouterr().err


def test_a_failed_listing_call_is_retried_unless_it_is_401_or_403(
    tool, tmp_path, capsys
) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    run.fetcher.list_failures = [
        tool.FetchError("slow", 429),
        tool.FetchError("down", 503),
    ]
    assert run.go("index", "--study-uid", "1.2.100") == 0
    assert len(run.sleeps) == 2
    run = Run(tool, tmp_path / "again", FakeCompetition(listing()))
    run.fetcher.list_failures = [tool.FetchError("no", 403)]
    assert run.go("index", "--study-uid", "1.2.100") == 2
    assert (
        run.sleeps == [] and "listing the competition failed" in capsys.readouterr().err
    )


# Pulling.


def test_studies_are_downloaded_checked_and_promoted_whole(tool, tmp_path) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing(), epoch="CURSOR9"))
    assert run.go("pull", "--studies", "2") == 0
    for study in STUDIES[:2]:
        for one in series_of(study):
            for number in range(1, FILES_PER_SERIES + 1):
                made = run.final(study) / one / f"{number}.dcm"
                assert made.read_bytes() == dicom(140 + number)
    assert not run.final("1.2.300").exists()
    assert not (run.state / "staging" / "1.2.100").exists()
    assert not (run.state / "staging" / ".tmp").exists()
    receipt = run.receipt()
    assert receipt["status"] == "complete" and receipt["failures"] == []
    assert receipt["selection"]["chosen"] == STUDIES[:2]
    done = receipt["totals"]
    assert (done["studies_promoted"], done["files"], done["files_downloaded"]) == (
        2,
        12,
        12,
    )
    assert done["bytes"] == done["bytes_downloaded"] == 2 * BYTES_PER_STUDY
    assert receipt["index"]["pages"] > 0 and receipt["elapsed_seconds"] >= 0
    assert "CURSOR9" not in json.dumps(receipt)


def test_staged_files_are_skipped_by_size_and_a_wrong_size_is_fetched_again(
    tool, tmp_path
) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    stage = run.state / "staging" / "1.2.100" / "1.2.100.1"
    stage.mkdir(parents=True)
    (stage / "1.dcm").write_bytes(dicom(141))  # right size: skipped
    (stage / "2.dcm").write_bytes(b"short")  # wrong size: fetched again
    assert run.go("pull", "--study-uid", "1.2.100") == 0
    names = {
        name.rsplit("/", 1)[1] for name in run.fetcher.downloads if "1.2.100.1" in name
    }
    assert names == {"2.dcm", "3.dcm"}
    assert run.receipt()["totals"]["files_reused_from_staging"] == 1
    assert (run.final("1.2.100") / "1.2.100.1" / "2.dcm").read_bytes() == dicom(142)


def test_a_failed_file_is_named_and_kept_in_staging_for_the_rerun(
    tool, tmp_path
) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    bad = "train_series/1.2.100/1.2.100.2/3.dcm"
    run.fetcher.failures[bad] = [tool.FetchError("boom", 500)] * 5
    assert run.go("pull", "--study-uid", "1.2.100", "--retries", "1") == 1
    failure = run.receipt()["failures"][0]
    assert (failure["study"], failure["file"], failure["attempts"]) == (
        "1.2.100",
        bad,
        2,
    )
    assert failure["error"] == "boom"
    assert not run.final("1.2.100").exists()
    assert len(tree(run.state / "staging" / "1.2.100")) == 5
    assert len(run.sleeps) == 1
    run.fetcher.failures.clear()
    run.fetcher.downloads.clear()
    assert run.go("pull", "--studies", "1") == 0
    assert run.fetcher.downloads == [bad]  # only the missing file
    assert (
        run.final("1.2.100").is_dir()
        and not (run.state / "staging" / "1.2.100").exists()
    )


def test_retries_and_rate_limits_are_counted(tool, tmp_path) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    slow = "train_series/1.2.100/1.2.100.1/1.dcm"
    run.fetcher.failures[slow] = [
        tool.FetchError("slow", 429),
        tool.FetchError("down", 503),
    ]
    assert run.go("pull", "--study-uid", "1.2.100") == 0
    done = run.receipt()["totals"]
    assert (done["retries"], done["rate_limited"]) == (2, 1)
    assert len(run.sleeps) == 2


def test_401_and_403_stop_the_run(tool, tmp_path) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    run.fetcher.failures["train_series/1.2.100/1.2.100.1/2.dcm"] = [
        tool.FetchError("no", 403)
    ]
    assert run.go("pull", "--studies", "3") == 1
    receipt = run.receipt()
    assert receipt["status"].startswith("stopped") and "403" in receipt["status"]
    assert [s["status"] for s in receipt["studies"]] == ["stopped"]
    assert not run.final("1.2.100").exists() and not run.final("1.2.200").exists()


def test_a_full_disk_stops_the_run(tool, tmp_path) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    run.fetcher.failures["train_series/1.2.100/1.2.100.1/2.dcm"] = [
        OSError(errno.ENOSPC, "no space")
    ]
    assert run.go("pull", "--studies", "2") == 1
    assert "the disk is full" in run.receipt()["status"]
    assert not run.final("1.2.200").exists()


def test_two_studies_in_a_row_with_nothing_fetched_stop_the_run(tool, tmp_path) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    for name in run.fetcher.sizes:
        run.fetcher.failures[name] = [tool.FetchError("down", 500)] * 10
    assert run.go("pull", "--studies", "3", "--retries", "0") == 1
    receipt = run.receipt()
    assert len(receipt["studies"]) == 2 and "two studies running" in receipt["status"]


def test_an_unexpected_crash_still_writes_its_receipt(tool, tmp_path) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    run.fetcher.failures["train_series/1.2.100/1.2.100.1/1.dcm"] = [RuntimeError("bug")]
    with pytest.raises(RuntimeError):
        run.go("pull", "--study-uid", "1.2.100")
    assert run.receipt()["status"].startswith("crashed: RuntimeError")


def test_a_study_on_disk_is_skipped_untouched_and_not_even_listed(
    tool, tmp_path
) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()), on_disk=["1.2.100"])
    before = snapshot(run.root)
    assert run.go("pull", "--study-uid", "1.2.100") == 0
    assert snapshot(run.root) == before
    assert run.fetcher.downloads == [] and run.fetcher.list_calls == []
    receipt = run.receipt()
    assert receipt["selection"]["skipped_existing"] == ["1.2.100"]
    assert receipt["studies"] == [{"study": "1.2.100", "status": "skipped_existing"}]


def test_a_study_that_appears_while_pulling_is_not_replaced(tool, tmp_path) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    appears = "train_series/1.2.100/1.2.100.2/3.dcm"
    original = run.fetcher.download

    def download(name, directory):
        original(name, directory)
        if name == appears:
            (run.final("1.2.100") / "1.2.100.1").mkdir(parents=True)
            (run.final("1.2.100") / "1.2.100.1" / "1.dcm").write_bytes(b"theirs")

    run.fetcher.download = download
    assert run.go("pull", "--study-uid", "1.2.100", "--workers", "1") == 1
    assert (run.final("1.2.100") / "1.2.100.1" / "1.dcm").read_bytes() == b"theirs"
    assert "appeared while pulling" in run.receipt()["failures"][0]["error"]


def test_a_study_the_listing_does_not_hold_is_a_named_failure_and_never_promoted(
    tool, tmp_path
) -> None:
    rows = listing(skip_series=series_of("1.2.200"))
    run = Run(tool, tmp_path, FakeCompetition(rows))
    assert run.go("pull", "--study-uid", "1.2.200") == 1
    failure = run.receipt()["failures"][0]
    assert (
        failure["study"] == "1.2.200"
        and "no file of this study is listed" in failure["error"]
    )
    assert not run.final("1.2.200").exists() and run.fetcher.downloads == []


def test_unexpected_listed_names_fail_the_study(tool, tmp_path) -> None:
    rows = listing(extra=[("train_series/1.2.100/1.2.100.1/notes.txt", 5)])
    run = Run(tool, tmp_path, FakeCompetition(rows))
    assert run.go("pull", "--study-uid", "1.2.100") == 1
    assert "unexpected form" in run.receipt()["failures"][0]["error"]
    assert not run.final("1.2.100").exists() and run.fetcher.downloads == []


def test_a_series_mismatch_is_named_and_what_the_competition_serves_is_promoted(
    tool, tmp_path
) -> None:
    extra = [(f"train_series/1.2.100/7.7/{n}.dcm", 150) for n in (1, 2)]
    rows = listing(skip_series=["1.2.100.2"], extra=extra)
    run = Run(tool, tmp_path, FakeCompetition(rows))
    assert run.go("pull", "--study-uid", "1.2.100") == 0
    notes = " ".join(run.receipt()["studies"][0]["notes"])
    assert "1.2.100.2 of train_series.csv is not listed" in notes
    assert "7.7 is listed but not in train_series.csv" in notes
    assert {p.name for p in run.final("1.2.100").iterdir()} == {"1.2.100.1", "7.7"}


def test_the_size_and_the_dicom_mark_are_required(tool, tmp_path) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    run.fetcher.writer = lambda directory, name, size: (
        directory / name.rsplit("/", 1)[1]
    ).write_bytes(
        b"x" * size  # the right size but no DICM at offset 128
    )
    assert run.go("pull", "--study-uid", "1.2.100", "--retries", "0") == 1
    assert "not DICOM" in run.receipt()["failures"][0]["error"]
    run.fetcher.writer = lambda directory, name, size: (
        directory / name.rsplit("/", 1)[1]
    ).write_bytes(dicom(size + 1))
    assert run.go("pull", "--study-uid", "1.2.100", "--retries", "0") == 1
    assert "bytes arrived" in run.receipt()["failures"][0]["error"]
    assert not run.final("1.2.100").exists()


def test_a_zip_delivery_is_unpacked_from_its_one_member_under_our_name(
    tool, tmp_path
) -> None:
    def zipped(directory, name, size):
        with zipfile.ZipFile(
            directory / (name.rsplit("/", 1)[1] + ".zip"), "w"
        ) as archive:
            archive.writestr("../../evil.dcm", dicom(size))

    run = Run(tool, tmp_path, FakeCompetition(listing()))
    run.fetcher.writer = zipped
    assert run.go("pull", "--study-uid", "1.2.100") == 0
    assert (run.final("1.2.100") / "1.2.100.1" / "1.dcm").read_bytes() == dicom(141)
    assert list(tmp_path.rglob("evil*")) == []

    def two_members(directory, name, size):
        with zipfile.ZipFile(
            directory / (name.rsplit("/", 1)[1] + ".zip"), "w"
        ) as archive:
            archive.writestr("a", dicom(size))
            archive.writestr("b", dicom(size))

    run = Run(tool, tmp_path / "second", FakeCompetition(listing()))
    run.fetcher.writer = two_members
    assert run.go("pull", "--study-uid", "1.2.100", "--retries", "0") == 1
    assert "one listed file" in run.receipt()["failures"][0]["error"]


# The disk.


def test_the_margin_refuses_before_anything_is_fetched_or_made(
    tool, tmp_path, capsys
) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    assert run.go("pull", "--studies", "1", free=10) == 2
    assert run.fetcher.downloads == [] and not (run.root / "train_series").exists()
    assert not (run.state / "staging").exists()
    assert run.receipt()["status"].startswith("refused")
    assert "margin" in " ".join(run.log)
    assert capsys.readouterr().err == ""


def test_the_margin_is_met_exactly_at_the_free_space_it_names(tool, tmp_path) -> None:
    margin = int(1e-6 * tool.GIB)
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    args = ("pull", "--studies", "1", "--min-free-gib", "1e-6")
    assert run.go(*args, free=BYTES_PER_STUDY + margin - 1) == 2
    assert run.go(*args, free=BYTES_PER_STUDY + margin) == 0


def test_staged_bytes_are_not_counted_as_still_to_fetch(tool, tmp_path) -> None:
    margin = int(1e-6 * tool.GIB)
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    stage = run.state / "staging" / "1.2.100" / "1.2.100.1"
    stage.mkdir(parents=True)
    for number in range(1, FILES_PER_SERIES + 1):
        (stage / f"{number}.dcm").write_bytes(dicom(140 + number))
    staged = sum(140 + number for number in range(1, FILES_PER_SERIES + 1))
    free = BYTES_PER_STUDY - staged + margin
    assert run.go("pull", "--studies", "1", "--min-free-gib", "1e-6", free=free) == 0


def test_a_disk_that_fills_during_the_run_stops_before_the_next_study(
    tool, tmp_path
) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    readings = iter([10**13, 10**13, 10])  # the plan, the first study, the second

    def free(path):
        return next(readings, 10)

    assert run.go("pull", "--studies", "3", free=free) == 1
    assert run.final("1.2.100").is_dir() and not run.final("1.2.200").exists()
    assert "fell under the margin" in run.receipt()["status"]


def test_staging_on_another_device_is_refused_before_anything_is_fetched(
    tool, tmp_path, monkeypatch
) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    monkeypatch.setattr(tool, "same_device", lambda first, second: False)
    assert run.go("pull", "--studies", "1") == 2
    assert (
        run.fetcher.downloads == [] and "different devices" in run.receipt()["status"]
    )


def test_a_dry_run_plans_and_writes_no_study_files(tool, tmp_path) -> None:
    run = Run(tool, tmp_path, FakeCompetition(listing()))
    assert run.go("pull", "--studies", "2", "--dry-run") == 0
    assert run.fetcher.downloads == []
    assert (
        not (run.root / "train_series").exists()
        and not (run.state / "staging").exists()
    )
    assert not (run.state / "receipts").exists()
    assert any(line.startswith("plan: 2 studies, 12 files") for line in run.log)
