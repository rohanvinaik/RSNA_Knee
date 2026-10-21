"""Pull more training studies of the competition into a local root: a development tool, never imported
by production code.

Growth rounds run locally on training studies fetched as they are needed. The competition serves every
DICOM (819,635 files, about 570 GB) one file per request; the local root keeps the studies pulled so far,
`train_series/<study>/<series>/<instance>.dcm`, which is the layout the readers expect.

    .venv/bin/python scripts/pull_competition_studies.py index --root data/raw --studies 25
    .venv/bin/python scripts/pull_competition_studies.py pull  --root data/raw --studies 25
    .venv/bin/python scripts/pull_competition_studies.py pull  --root data/raw --study-uid UID [UID ...]
    .venv/bin/python scripts/pull_competition_studies.py pull  --root data/raw --studies 25 --dry-run

`index` pages through the competition's file listing once and caches it (path and size of every file).
Given `--studies N` or `--study-uid ...` it stops as soon as the listing has passed the last of those
studies; given neither it lists everything (about 4,100 pages, some 50 minutes). It resumes where it
stopped, and `pull` extends it by itself when it does not yet cover the studies chosen, so `index` alone
is only needed to list everything ahead of time. `pull` downloads every file of the chosen studies,
`--workers` at once (8) and `--retries` retries each (3), checks each against the index, and puts a study
into `train_series/` only when all of its files are there.

Choosing: `--studies N` takes the first N studies in `train_series.csv` order that are not on disk, so it
is stable and blind to the labels (`train.csv` is never opened). A study whose pull failed is not on disk,
so the next `--studies` run chooses it again, first; no other study stands in for it. `--study-uid` names
studies; one already on disk is skipped and named in the receipt. Nothing inside a study directory that
exists is ever written, replaced or removed: a study appears under `train_series/` only by renaming its
finished staging directory onto a path that did not exist.

What the CLI does (kaggle 2.2.4, checked 2026-10-21). `kaggle competitions files <slug> --page-size 200
--format csv [--page-token T]` prints `Next Page Token = <T>` as its first line (absent on the last page),
then `name,size,creationDate` rows of full paths, in plain string order. `--format json` prints that same
first line before its JSON, which is why the whole output does not parse as JSON. `-v` also means csv, but
the SDK source (`build_kaggle_client_with_params`) turns its client's verbose mode on whenever `-v` is in
the arguments (read there, not observed), so it is never passed. A page token the server does not
recognise is not an error: it silently returns the first page again. Every page is therefore checked to
continue after the last indexed name, and when one does not, the listing is walked again from the start,
skipping the rows already kept. `kaggle competitions download <slug> -f <path> -p <dir> -q` writes the
file named by the last segment of the path into <dir>, as it is, not zipped, at its listed size; a missing
file exits 1 with a 404 line. Each download goes into its own new empty directory, is accepted only at the
listed size with `DICM` at offset 128, and is then renamed into the study's staging directory. A zip
delivery would be unpacked from its one member without trusting the member's own name. 401 and 403 stop
the run; 429 and 5xx are retried with backoff and counted.

Rates, measured 2026-10-21 on this machine with one study of 94 files and 61.6 MB (no 429 was seen): a
200-row listing page takes about 0.7 s, so the whole listing about 50 minutes; every file is a CLI process
of about 0.37 s of CPU, which is what limits the rate here, not bandwidth: 8 workers took 20.9 s (4.5 files
a second), 24 workers 9.1 s (10.3 files a second). A projection from that one study, not a measurement:
the 4,407 studies, 819,635 files, would take about 22 hours at 24 workers.

State sits beside the root, in `<root>.pull/` (`--state-dir`): `index/` (one gzip page file for each page
of new rows, then `state.json`, which counts the committed pages and holds the next page token, a
pagination cursor and not a credential, written last; `--index-dir` moves it), `staging/<study>/` (the
verified files of a study not yet complete, kept so a rerun skips them) and `receipts/pull-<time>-NN.json`
(studies, file counts, bytes, failures named, retries, elapsed time). Nothing here reads, prints or stores
a Kaggle credential: the CLI authenticates itself, and error text kept in receipts is cut to one line with
URL queries, tokens and the page cursor removed.

Free disk: a pull refuses to start when the disk would be left with less than `--min-free-gib` (100 GiB
by default; this machine runs near 80% full and needs room for swap, snapshots and Docker) once the files
still to be fetched are in, and stops before a further study if the disk has dropped under it meanwhile.

Exit status: 0 when every chosen study is on disk afterwards, 1 when a study failed or the run was stopped,
2 when nothing was started (a bad argument, the disk margin, a missing file or root).
"""

from __future__ import annotations

import argparse
import csv
import dataclasses
import errno
import gzip
import itertools
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

COMPETITION = "rsna-knee-abnormality-detection"
PAGE_SIZE = 200  # the listing's largest page
WORKERS = 8
RETRIES = 3
MIN_FREE_GIB = 100.0
GIB = 1024**3
SCHEMA = 1
TRAIN = "train_series"
CURSOR_LINE = "Next Page Token = "
HEADER = "name,size,creationDate"
FATAL_STATUS = frozenset({401, 403})
UID = r"[0-9]+(?:\.[0-9]+)*"
UID_FULL = re.compile(UID)
TRAIN_FILE = re.compile(rf"{TRAIN}/({UID})/({UID})/({UID})\.dcm")
STATUS_LINE = re.compile(r"\b([45][0-9]{2}) (?:Client|Server) Error")
# Two studies in a row with nothing fetched and nothing staged means the fault is not the studies'.
GIVE_UP_AFTER = 2


class PullError(Exception):
    """Something that stops the run or refuses to start it."""


class FetchError(Exception):
    """A listing or download call failed; `status` is the HTTP status when the CLI named one."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class StudyStopped(PullError):
    """A fatal error ended the run during a study; that study's partial result rides along."""

    def __init__(self, result: StudyResult, cause: PullError) -> None:
        super().__init__(str(cause))
        self.result = result


class Fetcher(Protocol):
    """The two calls made of the competition: one page of the listing, and one file."""

    def list_page(
        self, cursor: str | None, page_size: int
    ) -> tuple[list[tuple[str, int]], str | None]: ...

    def download(self, name: str, directory: Path) -> None: ...


def clean_error(text: str, redact: Sequence[str] = ()) -> str:
    """One line of CLI error text that is safe to keep: no URL query (a signed URL carries one), no
    token, no page cursor. A traceback is summed up by its last line, any other text by its first."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "no error text"
    line = lines[-1] if lines[0].startswith("Traceback") else lines[0]
    for secret in redact:
        if secret:
            line = line.replace(secret, "<cursor>")
    line = re.sub(r"\?\S*", "", line)
    line = re.sub(r"KGAT_\S+", "<token>", line)
    line = re.sub(r"(?i)bearer\s+\S+", "<token>", line)
    return line[:200]


def parse_listing(stdout: str) -> tuple[list[tuple[str, int]], str | None]:
    """The rows and the next page token of one `files --format csv` output. Anything before the header
    other than the token line is an error, not something to skip."""
    lines = stdout.splitlines()
    cursor = None
    if lines and lines[0].startswith(CURSOR_LINE):
        cursor = lines[0][len(CURSOR_LINE) :].strip() or None
        lines = lines[1:]
    if lines and lines[0].strip() == "No files found":
        return [], cursor
    if not lines or lines[0].strip() != HEADER:
        first = clean_error(lines[0] if lines else "", [cursor or ""])
        raise PullError(f"unexpected listing output, its first line being: {first!r}")
    rows: list[tuple[str, int]] = []
    for fields in csv.reader(lines[1:]):
        if not fields:
            continue
        if len(fields) != 3 or not fields[1].isdigit():
            raise PullError(f"unexpected listing row with {len(fields)} fields")
        rows.append((fields[0], int(fields[1])))
    return rows, cursor


class KaggleCli:
    """The `kaggle` command line as a Fetcher. Each call is a process that authenticates itself; this
    module never touches the credential files."""

    def __init__(
        self, executable: str, competition: str, timeout: float = 300.0
    ) -> None:
        self.executable = executable
        self.competition = competition
        self.timeout = timeout

    def _run(self, arguments: list[str], redact: Sequence[str] = ()) -> str:
        command = [self.executable, "competitions", *arguments]
        try:
            done = subprocess.run(
                command,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=self.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise FetchError(f"no answer within {self.timeout:.0f} s") from error
        except OSError as error:
            raise PullError(
                f"cannot run {self.executable!r}: {error.strerror}"
            ) from error
        if done.returncode != 0:
            text = done.stderr or done.stdout
            found = STATUS_LINE.search(text)
            raise FetchError(
                clean_error(text, redact), int(found.group(1)) if found else None
            )
        return done.stdout

    def list_page(
        self, cursor: str | None, page_size: int
    ) -> tuple[list[tuple[str, int]], str | None]:
        arguments = [
            "files",
            self.competition,
            "--page-size",
            str(page_size),
            "--format",
            "csv",
        ]
        if cursor:
            arguments += ["--page-token", cursor]
        return parse_listing(self._run(arguments, [cursor or ""]))

    def download(self, name: str, directory: Path) -> None:
        self._run(
            ["download", self.competition, "-f", name, "-p", str(directory), "-q"]
        )


def write_atomic(path: Path, data: bytes) -> None:
    """The whole file or nothing: written beside it, flushed to disk, then renamed over it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def study_bound(study: str) -> str:
    """Every file of a study sorts below this name and the names after the study sort at or above it:
    `train_series/<study>/...` is below `train_series/<study>0`, since `/` comes just before `0`."""
    return f"{TRAIN}/{study}0"


class Index:
    """The competition's listing as far as it has been read: `<dir>/pages/NNNNNN.tsv.gz` (the rows each
    page added, `name<TAB>size`) and `<dir>/state.json`. A page file is whole before it appears and the
    state that counts it is written after it, so a stop at any moment leaves the committed pages whole
    and at most one uncommitted page file, which the next page overwrites."""

    def __init__(self, directory: Path, state: dict) -> None:
        self.directory = directory
        self.state = state

    @classmethod
    def load(cls, directory: Path, competition: str) -> Index:
        path = directory / "state.json"
        if not path.exists():
            return cls(
                directory,
                {
                    "schema": SCHEMA,
                    "competition": competition,
                    "page_size": PAGE_SIZE,
                    "pages": 0,
                    "rows": 0,
                    "last_name": "",
                    "cursor": None,
                    "complete": False,
                },
            )
        try:
            state = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise PullError(
                f"{path} is unreadable; remove {directory} to list again"
            ) from error
        if state.get("schema") != SCHEMA or state.get("competition") != competition:
            raise PullError(
                f"{directory} holds an index of {state.get('competition')!r} "
                f"(schema {state.get('schema')}), not of {competition!r}; point --index-dir elsewhere"
            )
        return cls(directory, state)

    def page_path(self, number: int) -> Path:
        return self.directory / "pages" / f"{number:06d}.tsv.gz"

    def page(self, number: int) -> list[tuple[str, int]]:
        try:
            with gzip.open(
                self.page_path(number), "rt", encoding="utf-8", newline=""
            ) as handle:
                lines = handle.read().splitlines()
            return [
                (name, int(size)) for name, size in (line.split("\t") for line in lines)
            ]
        except (OSError, EOFError, ValueError) as error:
            raise PullError(
                f"index page {number} is unreadable; remove {self.directory} to list again"
            ) from error

    def covers(self, bound: str | None) -> bool:
        """Whether the committed names reach `bound`, or the listing is complete; `None` asks for all."""
        if self.state["complete"]:
            return True
        return bound is not None and self.state["last_name"] >= bound

    def add_page(self, rows: list[tuple[str, int]], cursor: str | None) -> None:
        """Commit the new rows of one page, and the token of the page after it."""
        state = self.state
        if rows:
            payload = "".join(f"{name}\t{size}\n" for name, size in rows).encode(
                "utf-8"
            )
            write_atomic(
                self.page_path(state["pages"]), gzip.compress(payload, mtime=0)
            )
            state["pages"] += 1
            state["rows"] += len(rows)
            state["last_name"] = rows[-1][0]
        state["cursor"] = cursor
        state["complete"] = cursor is None
        write_atomic(
            self.directory / "state.json", json.dumps(state, indent=1).encode("utf-8")
        )

    def files_of(self, studies: set[str]) -> dict[str, list[tuple[str, int]]]:
        """Every listed file of each study in listing order, reading pages only as far as the last."""
        found: dict[str, list[tuple[str, int]]] = {study: [] for study in studies}
        stop = max((study_bound(study) for study in studies), default="")
        for number in range(self.state["pages"]):
            page = self.page(number)
            for name, size in page:
                parts = name.split("/", 2)
                if len(parts) == 3 and parts[0] == TRAIN and parts[1] in found:
                    found[parts[1]].append((name, size))
            if page and page[-1][0] >= stop:
                break
        return found


def check_page(rows: list[tuple[str, int]]) -> None:
    names = [name for name, _ in rows]
    if any("\t" in name or "\n" in name for name in names):
        raise PullError("a listed name holds a tab or a line break")
    if any(first >= second for first, second in itertools.pairwise(names)):
        raise PullError(
            "the listing is not in increasing path order, so stopping early is unsafe"
        )


def list_with_retries(
    fetcher: Fetcher,
    cursor: str | None,
    retries: int,
    sleep: Callable[[float], None],
) -> tuple[list[tuple[str, int]], str | None]:
    """One page of the listing; a failed call is retried with backoff unless it is a 401 or 403."""
    attempt = 0
    while True:
        try:
            return fetcher.list_page(cursor, PAGE_SIZE)
        except FetchError as error:
            if error.status in FATAL_STATUS or attempt >= retries:
                raise PullError(
                    f"listing the competition failed after {attempt + 1} tries: {error}"
                ) from error
            sleep(backoff(attempt))
            attempt += 1


def extend_index(
    index: Index,
    fetcher: Fetcher,
    bound: str | None,
    say: Callable[[str], None],
    retries: int = RETRIES,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    """List pages until the index covers `bound` (all of it, for `None`). A page must continue after the
    last committed name. When it does not (a stale cursor the server ignored), the listing is walked again
    from the first page and only the rows after that name are kept, so none is ever added twice."""
    state = index.state
    cursor = state["cursor"]
    rewalking = False
    met_last = False
    previous_end = ""  # the last name of the page before, in this walk
    while not index.covers(bound):
        rows, following = list_with_retries(fetcher, cursor, retries, sleep)
        check_page(rows)
        if rows and rows[0][0] <= previous_end:
            raise PullError(
                "the listing is not in increasing path order across pages, so stopping early is unsafe"
            )
        previous_end = rows[-1][0] if rows else previous_end
        last = state["last_name"]
        if not rewalking and rows and rows[0][0] <= last:
            say(
                "index: the saved page cursor does not continue the listing; walking it again"
            )
            rewalking = True
        kept = rows
        if rewalking:
            met_last = met_last or not last or any(name == last for name, _ in rows)
            if not met_last and rows and rows[-1][0] > last:
                raise PullError(
                    "the competition's listing changed under the index; remove it"
                )
            kept = [row for row in rows if row[0] > last]
        index.add_page(kept, following)
        if kept and state["pages"] % 25 == 0:
            say(f"index: {state['pages']} pages, {state['rows']} rows")
        cursor = following
        if following is None:
            break
    kind = "complete" if state["complete"] else "partial"
    say(f"index: {state['pages']} pages, {state['rows']} rows, {kind}")


def read_train_series(path: Path) -> tuple[list[str], dict[str, list[str]]]:
    """The studies of `train_series.csv` in file order, and each study's series."""
    order: list[str] = []
    series: dict[str, list[str]] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            study, one = row["StudyInstanceUID"], row["SeriesInstanceUID"]
            if not (UID_FULL.fullmatch(study) and UID_FULL.fullmatch(one)):
                raise PullError(
                    f"{path} names a study or series that is not a UID: {study!r}"
                )
            if study not in series:
                order.append(study)
                series[study] = []
            series[study].append(one)
    return order, series


def studies_on_disk(root: Path) -> set[str]:
    directory = root / TRAIN
    if not directory.is_dir():
        return set()
    return {entry.name for entry in directory.iterdir() if entry.is_dir()}


def choose_studies(
    order: list[str],
    series: dict[str, list[str]],
    on_disk: set[str],
    count: int | None,
    uids: list[str] | None,
) -> tuple[list[str], list[str]]:
    """The studies to pull and those named but already on disk. `count` means the first N not on disk in
    file order; named studies are taken in file order too."""
    if uids:
        unknown = [uid for uid in uids if uid not in series]
        if unknown:
            raise PullError(
                f"not a training study of train_series.csv: {', '.join(unknown)}"
            )
        wanted = [study for study in order if study in set(uids)]
        return [s for s in wanted if s not in on_disk], [
            s for s in wanted if s in on_disk
        ]
    return [study for study in order if study not in on_disk][: count or 0], []


@dataclasses.dataclass(frozen=True)
class Entry:
    name: str
    size: int
    study: str
    series: str

    @property
    def basename(self) -> str:
        return self.name.rsplit("/", 1)[1]

    @property
    def relative(self) -> str:
        return f"{self.series}/{self.basename}"


@dataclasses.dataclass
class StudyPlan:
    study: str
    entries: list[Entry]
    bad_names: list[str]
    csv_series: list[str]

    @property
    def total_bytes(self) -> int:
        return sum(entry.size for entry in self.entries)

    @property
    def listed_series(self) -> list[str]:
        return sorted({entry.series for entry in self.entries})


def make_plan(
    study: str, listed: list[tuple[str, int]], csv_series: list[str]
) -> StudyPlan:
    entries: list[Entry] = []
    bad: list[str] = []
    for name, size in listed:
        match = TRAIN_FILE.fullmatch(name)
        if match and match.group(1) == study:
            entries.append(Entry(name, size, study, match.group(2)))
        else:
            bad.append(name)
    return StudyPlan(study, entries, bad, csv_series)


@dataclasses.dataclass
class StudyResult:
    study: str
    status: str = "pending"
    series: int = 0
    files: int = 0
    bytes: int = 0
    downloaded: int = 0
    downloaded_bytes: int = 0
    reused_from_staging: int = 0
    retries: int = 0
    rate_limited: int = 0
    seconds: float = 0.0
    notes: list[str] = dataclasses.field(default_factory=list)
    failures: list[dict] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Outcome:
    attempts: int = 0
    rate_limited: int = 0
    error: str = ""
    downloaded: bool = False


def backoff(attempt: int) -> float:
    return min(60.0, 2.0 * 2**attempt) * (0.5 + random.random())


def unzip_single(archive_path: Path, entry: Entry) -> Path:
    """The one member of a zip delivery, written to a name of ours whatever the member is called."""
    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = [info for info in archive.infolist() if not info.is_dir()]
            if len(members) != 1 or members[0].file_size != entry.size:
                raise FetchError("the zip does not hold the one listed file")
            out = archive_path.with_name(entry.basename)
            with archive.open(members[0]) as source, out.open("wb") as target:
                shutil.copyfileobj(source, target, 1 << 20)
    except zipfile.BadZipFile as error:
        raise FetchError("the zip is damaged") from error
    return out


def accept_download(directory: Path, entry: Entry) -> Path:
    """The downloaded file, picked by the listed name, if it has the listed size and the DICOM mark."""
    produced = directory / entry.basename
    if not produced.is_file():
        zipped = directory / f"{entry.basename}.zip"
        if not zipped.is_file():
            raise FetchError("the download left no file of the listed name")
        produced = unzip_single(zipped, entry)
    size = produced.stat().st_size
    if size != entry.size:
        raise FetchError(f"{size} bytes arrived, the listing says {entry.size}")
    with produced.open("rb") as handle:
        head = handle.read(132)
    if head[128:132] != b"DICM":
        raise FetchError("the file is not DICOM (no DICM at offset 128)")
    return produced


def same_device(first: Path, second: Path) -> bool:
    return first.stat().st_dev == second.stat().st_dev


def free_disk(path: Path) -> int:
    while not path.exists():
        path = path.parent
    return shutil.disk_usage(path).free


def gib(count: float) -> str:
    return f"{count / GIB:.1f} GiB"


def short(uid: str) -> str:
    return f"...{uid[-12:]}"


@dataclasses.dataclass
class Paths:
    root: Path
    csv: Path
    state: Path
    index: Path
    staging: Path
    receipts: Path


def resolve_paths(args: argparse.Namespace) -> Paths:
    root = args.root.resolve()
    state = (args.state_dir or root.with_name(f"{root.name}.pull")).resolve()
    return Paths(
        root=root,
        csv=(args.train_series_csv or root / "train_series.csv").resolve(),
        state=state,
        index=(args.index_dir or state / "index").resolve(),
        staging=state / "staging",
        receipts=state / "receipts",
    )


def read_studies(paths: Paths) -> tuple[list[str], dict[str, list[str]]]:
    if not paths.csv.is_file():
        raise PullError(f"{paths.csv} is not a file; --root must hold train_series.csv")
    return read_train_series(paths.csv)


class Puller:
    """One `pull` run: choose, list, check the disk, then fetch and promote study by study."""

    def __init__(
        self,
        args: argparse.Namespace,
        fetcher: Fetcher,
        say: Callable[[str], None],
        sleep: Callable[[float], None],
        free_bytes: Callable[[Path], int],
    ) -> None:
        self.args = args
        self.fetcher = fetcher
        self.say = say
        self.sleep = sleep
        self.free_bytes = free_bytes
        self.paths = resolve_paths(args)
        self.margin = int(args.min_free_gib * GIB)
        self.stop = threading.Event()
        self.scratch = self.paths.staging / ".tmp"
        self.results: list[StudyResult] = []
        self.receipt: dict = {}
        self.began = time.monotonic()

    def run(self) -> int:
        order, series = read_studies(self.paths)
        chosen, skipped = choose_studies(
            order,
            series,
            studies_on_disk(self.paths.root),
            self.args.studies,
            self.args.study_uid,
        )
        for study in skipped:
            self.say(f"{short(study)}: already on disk, left untouched")
        self.receipt = {
            "schema": SCHEMA,
            "competition": self.args.competition,
            "root": str(self.paths.root),
            "started": datetime.now(UTC).isoformat(timespec="seconds"),
            "selection": {
                "requested": self.args.studies or self.args.study_uid,
                "chosen": chosen,
                "skipped_existing": skipped,
            },
            "settings": {
                "workers": self.args.workers,
                "retries": self.args.retries,
                "min_free_gib": self.args.min_free_gib,
            },
        }
        self.began = time.monotonic()
        status = "complete"
        try:
            if chosen:
                status = self.pull(chosen, series)
        except StudyStopped as stopped:
            self.results.append(stopped.result)
            status = f"stopped: {stopped}"
        except PullError as error:
            status = f"stopped: {error}" if self.results else f"refused: {error}"
        except KeyboardInterrupt:
            status = "interrupted"
        except Exception as error:
            # The receipt must say how the run ended, whatever went wrong; then the error goes on.
            crashed = f"crashed: {type(error).__name__}: {clean_error(str(error))}"
            self.finish(crashed, skipped, bool(chosen))
            raise
        return self.finish(status, skipped, bool(chosen))

    def pull(self, chosen: list[str], series: dict[str, list[str]]) -> str:
        index = Index.load(self.paths.index, self.args.competition)
        bound = max(study_bound(study) for study in chosen)
        extend_index(
            index, self.fetcher, bound, self.say, self.args.retries, self.sleep
        )
        self.receipt["index"] = {
            key: index.state[key] for key in ("pages", "rows", "complete", "last_name")
        }
        listed = index.files_of(set(chosen))
        plans = [make_plan(study, listed[study], series[study]) for study in chosen]
        self.check_capacity(plans)
        if self.args.dry_run:
            return "dry run"
        return self.pull_all(plans)

    def to_fetch(self, plan: StudyPlan) -> int:
        staged = 0
        for entry in plan.entries:
            path = self.paths.staging / plan.study / entry.relative
            if path.is_file() and path.stat().st_size == entry.size:
                staged += entry.size
        return plan.total_bytes - staged

    def check_capacity(self, plans: list[StudyPlan]) -> None:
        need = sum(self.to_fetch(plan) for plan in plans)
        free = self.free_bytes(self.paths.root)
        self.receipt["disk"] = {
            "free_before": free,
            "to_fetch": need,
            "margin": self.margin,
        }
        files = sum(len(plan.entries) for plan in plans)
        self.say(
            f"plan: {len(plans)} studies, {files} files, {gib(need)} to fetch; "
            f"{gib(free)} free, margin {gib(self.margin)}"
        )
        if self.args.dry_run:
            for plan in plans:
                self.say(
                    f"  {short(plan.study)}: {len(plan.entries)} files in "
                    f"{len(plan.listed_series)} series, {plan.total_bytes / 1e6:.1f} MB"
                )
        if free - need < self.margin:
            raise PullError(
                f"{gib(free)} free less {gib(need)} to fetch would leave {gib(free - need)}, "
                f"under the {gib(self.margin)} margin (--min-free-gib)"
            )

    def pull_all(self, plans: list[StudyPlan]) -> str:
        self.paths.staging.mkdir(parents=True, exist_ok=True)
        (self.paths.root / TRAIN).mkdir(parents=True, exist_ok=True)
        if not same_device(self.paths.staging, self.paths.root / TRAIN):
            raise PullError(
                f"{self.paths.staging} and {self.paths.root / TRAIN} are on different devices; "
                "a study could not be renamed into place (use --state-dir)"
            )
        shutil.rmtree(self.scratch, ignore_errors=True)
        self.scratch.mkdir()
        status = "complete"
        barren = 0
        try:
            with ThreadPoolExecutor(max_workers=self.args.workers) as pool:
                try:
                    for position, plan in enumerate(plans, 1):
                        result = self.pull_study(pool, plan)
                        self.results.append(result)
                        self.say(
                            f"[{position}/{len(plans)}] {short(plan.study)}: {result.status}, "
                            f"{result.files} files, {result.bytes / 1e6:.1f} MB, "
                            f"{result.seconds:.1f} s"
                        )
                        if result.status == "not started: disk margin":
                            status = "stopped: the free disk fell under the margin"
                            break
                        empty = (
                            result.files > 0
                            and result.downloaded == 0
                            and result.reused_from_staging == 0
                        )
                        barren = (
                            barren + 1 if result.status == "failed" and empty else 0
                        )
                        if barren >= GIVE_UP_AFTER:
                            status = "stopped: nothing could be fetched for two studies running"
                            break
                finally:
                    self.stop.set()
        finally:
            shutil.rmtree(self.scratch, ignore_errors=True)
        return status

    def pull_study(self, pool: ThreadPoolExecutor, plan: StudyPlan) -> StudyResult:
        """One study: the files not yet staged fetched together, promoted only when all are there."""
        began = time.monotonic()
        result = StudyResult(
            plan.study,
            series=len(plan.listed_series),
            files=len(plan.entries),
            bytes=plan.total_bytes,
        )
        if not plan.entries or plan.bad_names:
            result.status = "failed"
            reason = (
                "no file of this study is listed"
                if not plan.entries
                else "listed names of an unexpected form: "
                + ", ".join(plan.bad_names[:3])
            )
            result.failures.append({"file": plan.study, "attempts": 0, "error": reason})
            return result
        if self.free_bytes(self.paths.root) - self.to_fetch(plan) < self.margin:
            result.status = "not started: disk margin"
            return result
        listed = set(plan.listed_series)
        for name in sorted(set(plan.csv_series) - listed):
            result.notes.append(
                f"series {name} of train_series.csv is not listed by the competition"
            )
        for name in sorted(listed - set(plan.csv_series)):
            result.notes.append(f"series {name} is listed but not in train_series.csv")
        stage = self.paths.staging / plan.study
        todo = []
        for entry in plan.entries:
            path = stage / entry.relative
            if path.is_file() and path.stat().st_size == entry.size:
                result.reused_from_staging += 1
            else:
                todo.append(entry)
        futures = [pool.submit(self.fetch_one, entry, stage) for entry in todo]
        fatal: PullError | None = None
        for entry, future in zip(todo, futures, strict=True):
            try:
                outcome = future.result()
            except PullError as error:
                fatal = fatal or error
                continue
            result.retries += max(outcome.attempts - 1, 0)
            result.rate_limited += outcome.rate_limited
            if outcome.downloaded:
                result.downloaded += 1
                result.downloaded_bytes += entry.size
            else:
                failure = {
                    "file": entry.name,
                    "attempts": outcome.attempts,
                    "error": outcome.error,
                }
                result.failures.append(failure)
        result.seconds = time.monotonic() - began
        if fatal:
            result.status = "stopped"
            raise StudyStopped(result, fatal)
        result.status = (
            "failed" if result.failures else self.promote(plan, stage, result)
        )
        return result

    def promote(self, plan: StudyPlan, stage: Path, result: StudyResult) -> str:
        """Rename the finished staging directory to its place; a path that exists is never replaced."""
        expected = {entry.relative for entry in plan.entries}
        present = {
            str(path.relative_to(stage)) for path in stage.rglob("*") if path.is_file()
        }
        for extra in sorted(present - expected):
            (stage / extra).unlink()
            result.notes.append(
                f"removed {extra} from staging: it is not in the listing"
            )
        final = self.paths.root / TRAIN / plan.study
        if final.exists():
            failure = {
                "file": str(final),
                "attempts": 0,
                "error": "appeared while pulling",
            }
            result.failures.append(failure)
            return "failed"
        os.replace(stage, final)
        return "promoted"

    def fetch_one(self, entry: Entry, stage: Path) -> Outcome:
        """One file into its study's staging directory, retried; each try has a new empty directory."""
        outcome = Outcome()
        target = stage / entry.relative
        for attempt in range(self.args.retries + 1):
            if self.stop.is_set():
                outcome.error = "stopped before this file was fetched"
                return outcome
            outcome.attempts += 1
            work = Path(tempfile.mkdtemp(dir=self.scratch))
            try:
                self.fetcher.download(entry.name, work)
                produced = accept_download(work, entry)
                target.parent.mkdir(parents=True, exist_ok=True)
                os.replace(produced, target)
                outcome.downloaded, outcome.error = True, ""
                return outcome
            except FetchError as error:
                if error.status in FATAL_STATUS:
                    self.stop.set()
                    raise PullError(
                        f"HTTP {error.status} from the competition (credentials, or the rules "
                        "not accepted?)"
                    ) from error
                if error.status == 429:
                    outcome.rate_limited += 1
                outcome.error = str(error)
            except OSError as error:
                if error.errno == errno.ENOSPC:
                    self.stop.set()
                    raise PullError("the disk is full") from error
                outcome.error = clean_error(f"{type(error).__name__}: {error}")
            finally:
                shutil.rmtree(work, ignore_errors=True)
            if attempt < self.args.retries:
                self.sleep(backoff(attempt))
        return outcome

    def finish(self, status: str, skipped: list[str], pulled: bool) -> int:
        results = self.results
        self.receipt["status"] = status
        self.receipt["elapsed_seconds"] = round(time.monotonic() - self.began, 3)
        self.receipt["studies"] = [dataclasses.asdict(result) for result in results]
        self.receipt["studies"] += [
            {"study": s, "status": "skipped_existing"} for s in skipped
        ]
        self.receipt["failures"] = [
            {"study": result.study, **failure}
            for result in results
            for failure in result.failures
        ]
        self.receipt["totals"] = {
            "studies_promoted": sum(result.status == "promoted" for result in results),
            "studies_failed": sum(
                result.status in ("failed", "stopped") for result in results
            ),
            "files": sum(result.files for result in results),
            "files_downloaded": sum(result.downloaded for result in results),
            "files_reused_from_staging": sum(
                result.reused_from_staging for result in results
            ),
            "bytes": sum(result.bytes for result in results),
            "bytes_downloaded": sum(result.downloaded_bytes for result in results),
            "retries": sum(result.retries for result in results),
            "rate_limited": sum(result.rate_limited for result in results),
        }
        if not self.args.dry_run and (pulled or skipped):
            self.say(f"receipt: {self.write_receipt()}")
        done = self.receipt["totals"]
        seconds = self.receipt["elapsed_seconds"]
        rate = done["bytes_downloaded"] / seconds / 1e6 if seconds else 0.0
        self.say(
            f"{status}: {done['studies_promoted']} studies promoted, {done['studies_failed']} failed, "
            f"{done['files_downloaded']} files ({done['bytes_downloaded'] / 1e6:.1f} MB) fetched, "
            f"{done['files_reused_from_staging']} reused from staging, {done['retries']} retries, "
            f"{done['rate_limited']} rate-limited, {seconds:.1f} s, {rate:.1f} MB/s"
        )
        for failure in self.receipt["failures"]:
            self.say(
                f"  failed: {failure['file']} after {failure['attempts']} tries: {failure['error']}"
            )
        if status.startswith("refused"):
            return 2
        return (
            0
            if status in ("complete", "dry run") and not self.receipt["failures"]
            else 1
        )

    def write_receipt(self) -> Path:
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        serial = 1  # zero-padded, so receipts of one second still sort in the order they were made
        target = self.paths.receipts / f"pull-{stamp}-{serial:02d}.json"
        while target.exists():
            serial += 1
            target = self.paths.receipts / f"pull-{stamp}-{serial:02d}.json"
        write_atomic(target, json.dumps(self.receipt, indent=1).encode("utf-8"))
        return target


def run_index(
    args: argparse.Namespace,
    fetcher: Fetcher,
    say: Callable[[str], None],
    sleep: Callable[[float], None],
) -> int:
    paths = resolve_paths(args)
    chosen: list[str] = []
    if args.studies or args.study_uid:
        order, series = read_studies(paths)
        on_disk = studies_on_disk(paths.root)
        chosen, _ = choose_studies(order, series, on_disk, args.studies, args.study_uid)
    index = Index.load(paths.index, args.competition)
    bound = max((study_bound(study) for study in chosen), default=None)
    extend_index(index, fetcher, bound, say, args.retries, sleep)
    return 0


def positive(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pull training studies of the competition into a local root.",
        epilog="The module note of this file gives the layout, the margin and the exit status.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for name, text in (
        ("index", "list the competition's files and cache the listing"),
        ("pull", "download whole training studies"),
    ):
        command = commands.add_parser(name, help=text)
        command.add_argument(
            "--root", type=Path, required=True, help="holds train_series.csv"
        )
        command.add_argument("--competition", default=COMPETITION)
        command.add_argument(
            "--train-series-csv", type=Path, help="default: <root>/train_series.csv"
        )
        command.add_argument(
            "--state-dir", type=Path, help="default: <root>.pull, beside the root"
        )
        command.add_argument(
            "--index-dir", type=Path, help="default: <state-dir>/index"
        )
        command.add_argument("--kaggle", default=shutil.which("kaggle") or "kaggle")
        command.add_argument("--retries", type=int, default=RETRIES)
        which = command.add_mutually_exclusive_group(required=name == "pull")
        which.add_argument(
            "--studies", type=positive, metavar="N", help="the first N not on disk"
        )
        which.add_argument(
            "--study-uid", nargs="+", metavar="UID", help="these studies"
        )
        if name == "pull":
            command.add_argument("--workers", type=positive, default=WORKERS)
            command.add_argument("--min-free-gib", type=float, default=MIN_FREE_GIB)
            command.add_argument(
                "--dry-run", action="store_true", help="plan and check the disk only"
            )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    fetcher: Fetcher | None = None,
    say: Callable[[str], None] | None = None,
    sleep: Callable[[float], None] = time.sleep,
    free_bytes: Callable[[Path], int] = free_disk,
) -> int:
    args = build_parser().parse_args(argv)
    out = say or (lambda text: print(text, flush=True))
    fetcher = fetcher or KaggleCli(args.kaggle, args.competition)
    try:
        if args.command == "index":
            return run_index(args, fetcher, out, sleep)
        return Puller(args, fetcher, out, sleep, free_bytes).run()
    except PullError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
