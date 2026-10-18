"""The SonarQube check in RSNA_Knee's gate: SquishOS `verification-gates.md`, "Local SonarQube Docker
check (pre-push)", applied here and made part of `scripts/ci_local.sh` at Rohan's request (2026-10-18:
«Sonar should be part of the CI gate for this project»), on this machine and on GitHub alike.

One pinned server and scanner, one rule set, on both: Rohan, 2026-10-18, «Both git and local should
use a sane profile of Sonar rules». The rule set is the server's full "Sonar way comprehensive"; the
images are pinned by digest so neither machine drifts to another version's default.

What blocks is bare correctness only: Rohan, «don't over-fit to targets, only bare correctness issues
should be blocking». The step fails when the scan or its analysis fails, when the open bugs and
vulnerabilities cannot be read, or when one is open. The quality gate and its new-code conditions, the
code smells (per rule), the coverage and the duplication are printed as information, read at every gate.

The server is the kept container `rsna-knee-sonar` (host port 9001, named volume
`rsna-knee-sonar-data`, as Peitho's `peitho-sonar` is set up). Its credentials live outside the repo,
minted once per container, in `~/.config/rsna-knee/sonar-local.env` (mode 600): a fresh container resets
them, so the container is kept. A GitHub runner starts a fresh one each run and mints there.

    .venv/bin/python scripts/sonar_local.py gate            # the gate's step (see `gate`)
    .venv/bin/python scripts/sonar_local.py start           # start the container, wait until it is UP
    .venv/bin/python scripts/sonar_local.py mint            # once per container: admin password, token
    .venv/bin/python scripts/sonar_local.py rebuild         # a new container on the pinned image
    .venv/bin/python scripts/sonar_local.py scan            # coverage.xml from the tests, then analyse
    .venv/bin/python scripts/sonar_local.py report <out>    # every answer the gate reads, whole

No credential is printed or put on a command line: the token reaches the scanner through its
environment, and the env file is read here, never sourced into a shell.
"""

from __future__ import annotations

import base64
import json
import os
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PROJECT = "RSNA_Knee"
CONTAINER = "rsna-knee-sonar"
# SonarQube Community Build 26.10.0.133078 (an index of amd64 and arm64 images) and the SonarScanner
# CLI image of 2026-09-17 (amd64 only; it runs emulated on Apple silicon), pinned by digest.
IMAGE = (
    "sonarqube@sha256:0b3408443fb6a311253de27941b10977c9b977fd53be2265947bfe14161308b8"
)
SCANNER = "sonarsource/sonar-scanner-cli@sha256:a3f4215076706c95a17a68c19322ee916e40a3acd081a8c1a1e839e0194afa57"
PROFILE = "Sonar way comprehensive"
PORT = 9001
SERVER = f"http://localhost:{PORT}"
SERVER_FROM_DOCKER = f"http://host.docker.internal:{PORT}"
ENV_FILE = Path.home() / ".config" / "rsna-knee" / "sonar-local.env"
# The scanner's working folder, inside the mounted project (git-ignored), so this scan's own task id
# can be read back. The scanner image runs as its own user (1000), which on a GitHub runner does not
# own the checkout, so the folder is made here and opened to it.
WORK = ROOT / ".scannerwork"
MEASURES = (
    "bugs",
    "vulnerabilities",
    "code_smells",
    "security_hotspots",
    "coverage",
    "duplicated_lines_density",
    "ncloc",
)
UP_WITHIN_S = 600
DOCKER_WITHIN_S = 180
TASK_WITHIN_S = 600


def call(
    path: str,
    *,
    auth: tuple[str, str] | None = None,
    form: dict[str, str] | None = None,
) -> tuple[int, Any]:
    """One request to the local server: its HTTP status and its JSON body ({} when it has none)."""
    data = urllib.parse.urlencode(form).encode() if form is not None else None
    request = urllib.request.Request(
        SERVER + path, data=data, method="GET" if form is None else "POST"
    )
    if auth is not None:
        pair = base64.b64encode(f"{auth[0]}:{auth[1]}".encode()).decode()
        request.add_header("Authorization", f"Basic {pair}")
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            status, body = response.status, response.read()
    except urllib.error.HTTPError as error:
        status, body = error.code, error.read()
    text = body.decode("utf-8", errors="replace").strip()
    if not text:
        return status, {}
    try:
        return status, json.loads(text)
    except ValueError:
        return status, {"text": text}


def credentials() -> dict[str, str]:
    """The minted values (KEY='value' lines); missing file, no values."""
    if not ENV_FILE.exists():
        return {}
    values: dict[str, str] = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if sep:
            values[key.strip()] = value.strip().strip("'")
    return values


def token_auth() -> tuple[str, str]:
    return credentials().get("SONAR_TOKEN", ""), ""


def write_env(values: dict[str, str]) -> None:
    ENV_FILE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(ENV_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write("".join(f"{key}='{value}'\n" for key, value in values.items()))


def docker_ready() -> bool:
    """Docker answers; on this Mac, Docker Desktop is started first when it is not running."""

    def answers() -> bool:
        return (
            subprocess.run(
                ["docker", "info"], capture_output=True, check=False
            ).returncode
            == 0
        )

    if answers():
        return True
    if sys.platform != "darwin":
        print("docker does not answer")
        return False
    print("starting Docker Desktop")
    subprocess.run(["open", "-a", "Docker"], check=False)
    deadline = time.monotonic() + DOCKER_WITHIN_S
    while time.monotonic() < deadline:
        if answers():
            return True
        time.sleep(3)
    print(f"docker did not answer within {DOCKER_WITHIN_S} s")
    return False


def start() -> int:
    """Start the kept container (create it the first time, on the pinned image), then wait until
    the server is UP. A container made from another image is refused: `rebuild` replaces it."""
    if not docker_ready():
        return 1
    inspected = subprocess.run(
        ["docker", "container", "inspect", "--format", "{{.Config.Image}}", CONTAINER],
        capture_output=True,
        text=True,
        check=False,
    )
    if inspected.returncode == 0:
        made_from = inspected.stdout.strip()
        if made_from != IMAGE:
            print(
                f"{CONTAINER} runs {made_from}, not the pinned {IMAGE}: run `rebuild`"
            )
            return 1
        command = ["docker", "start", CONTAINER]
    else:
        command = [
            "docker", "run", "-d", "--name", CONTAINER, "-p", f"{PORT}:9000",
            "-v", f"{CONTAINER}-data:/opt/sonarqube/data", IMAGE,
        ]  # fmt: skip
    subprocess.run(command, capture_output=True, check=True)
    deadline = time.monotonic() + UP_WITHIN_S
    status = "unreachable"
    while time.monotonic() < deadline:
        try:
            status = call("/api/system/status")[1].get("status", "unknown")
        except OSError:
            status = "unreachable"
        if status == "UP":
            print(f"{CONTAINER}: UP at {SERVER}")
            return 0
        time.sleep(3)
    print(f"{CONTAINER}: not UP after {UP_WITHIN_S} s (last status: {status})")
    return 1


def mint() -> int:
    """Once per container: replace the default admin password and make a token, kept in ENV_FILE."""
    if ENV_FILE.exists():
        print(
            f"already minted: {ENV_FILE}. A new container needs a new mint; this one is kept."
        )
        return 1
    # The server's rule: 12 or more characters with an upper, a lower, a digit and a special one.
    password = secrets.token_urlsafe(24) + "-Aa9"
    status, body = call(
        "/api/users/change_password",
        auth=("admin", "admin"),
        form={"login": "admin", "previousPassword": "admin", "password": password},
    )
    if status not in (200, 204):
        print(f"change_password refused: HTTP {status} {body.get('errors', '')}")
        return 1
    status, body = call(
        "/api/user_tokens/generate",
        auth=("admin", password),
        form={"name": "rsna-knee-local"},
    )
    token = body.get("token", "") if status == 200 else ""
    # The password has changed either way: keep it, or the container is locked out.
    write_env(
        {"SONAR_ADMIN_PASSWORD": password} | ({"SONAR_TOKEN": token} if token else {})
    )
    if not token:
        print(f"user_tokens/generate refused: HTTP {status} {body.get('errors', '')}")
        return 1
    print(f"minted into {ENV_FILE} (mode 600); the values are not printed")
    return 0


def rebuild() -> int:
    """A new container on the pinned image: the old container, its data volume and its credentials
    go (they belong to that container alone), then start and mint again."""
    if not docker_ready():
        return 1
    subprocess.run(["docker", "rm", "-f", CONTAINER], capture_output=True, check=False)
    subprocess.run(
        ["docker", "volume", "rm", f"{CONTAINER}-data"],
        capture_output=True,
        check=False,
    )
    ENV_FILE.unlink(missing_ok=True)
    if start() != 0:
        return 1
    return mint()


def ensure_project() -> int:
    """The project exists and analyses with PROFILE: created on a fresh server, the profile set,
    then read back, so the rule set is the one named here and never a version's silent default."""
    auth = token_auth()
    status, body = call(f"/api/projects/search?projects={PROJECT}", auth=auth)
    if status != 200:
        print(f"projects/search refused: HTTP {status} {body.get('errors', '')}")
        return 1
    if not body.get("components"):
        status, body = call(
            "/api/projects/create",
            auth=auth,
            form={"project": PROJECT, "name": PROJECT},
        )
        if status != 200:
            print(f"projects/create refused: HTTP {status} {body.get('errors', '')}")
            return 1
    status, body = call(
        "/api/qualityprofiles/add_project",
        auth=auth,
        form={"language": "py", "qualityProfile": PROFILE, "project": PROJECT},
    )
    if status not in (200, 204):
        print(
            f"qualityprofiles/add_project refused: HTTP {status} {body.get('errors', '')}"
        )
        return 1
    status, body = call(
        f"/api/qualityprofiles/search?project={PROJECT}&language=py", auth=auth
    )
    held = [p for p in body.get("profiles", []) if p.get("language") == "py"]
    if status != 200 or not held or held[0].get("name") != PROFILE:
        print(f"the project's Python rule set is not {PROFILE}: {held}")
        return 1
    print(f"sonar rule set: {PROFILE} ({held[0].get('activeRuleCount')} rules)")
    return 0


def wait_for_task(task_id: str) -> str:
    """This scan's own analysis task, waited on until it ends: its final status."""
    deadline = time.monotonic() + TASK_WITHIN_S
    status = "unknown"
    while time.monotonic() < deadline:
        _, body = call(f"/api/ce/task?id={task_id}", auth=token_auth())
        status = body.get("task", {}).get("status", "unknown")
        if status in ("SUCCESS", "FAILED", "CANCELED"):
            return status
        time.sleep(2)
    return f"not finished after {TASK_WITHIN_S} s (last status: {status})"


def analyse() -> tuple[int, str]:
    """The scanner on the project as it stands, with the coverage.xml already written, then this
    scan's own analysis task waited on: the scanner's exit code and the task's final status."""
    if not credentials().get("SONAR_TOKEN"):
        print(f"no SONAR_TOKEN in {ENV_FILE}: run mint first")
        return 1, "not run"
    if ensure_project() != 0:
        return 1, "not run"
    if not WORK.exists():
        WORK.mkdir()
        WORK.chmod(0o777)
    task_file = WORK / "report-task.txt"
    task_file.unlink(missing_ok=True)
    # The image's entrypoint turns SCANNER_WORKDIR_PATH into sonar.working.directory.
    command = [
        "docker", "run", "--rm", "--add-host=host.docker.internal:host-gateway",
        "-e", f"SONAR_HOST_URL={SERVER_FROM_DOCKER}", "-e", "SONAR_TOKEN",
        "-e", "SCANNER_WORKDIR_PATH=/usr/src/.scannerwork", "-v", f"{ROOT}:/usr/src", SCANNER,
    ]  # fmt: skip
    environment = os.environ | {"SONAR_TOKEN": credentials()["SONAR_TOKEN"]}
    scanned = subprocess.run(command, cwd=ROOT, env=environment, check=False).returncode
    if scanned != 0 or not task_file.exists():
        return scanned or 1, "no task"
    task = dict(
        line.split("=", 1)
        for line in task_file.read_text(encoding="utf-8").splitlines()
        if "=" in line
    )
    task_id = task.get("ceTaskId", "")
    return 0, wait_for_task(task_id) if task_id else "no task id"


def scan() -> int:
    """coverage.xml from the whole test suite, then the scanner (for a run outside the gate)."""
    for command in (
        [sys.executable, "-m", "coverage", "run", "-m", "pytest", "-q"],
        [sys.executable, "-m", "coverage", "xml", "-o", "coverage.xml"],
    ):
        if subprocess.run(command, cwd=ROOT, check=False).returncode != 0:
            print(f"failed: {' '.join(command[1:])}")
            return 1
    scanned, task_status = analyse()
    print(f"scanner exit {scanned}; analysis task {task_status}")
    return 0 if scanned == 0 and task_status == "SUCCESS" else 1


def results() -> dict[str, Any]:
    """Every answer the gate reads: the quality gate, the measures, the open bugs and
    vulnerabilities, the code smells by rule, the hotspots and the project's rule set."""
    queries = {
        "quality_gate": f"/api/qualitygates/project_status?projectKey={PROJECT}",
        "measures": f"/api/measures/component?component={PROJECT}&metricKeys={','.join(MEASURES)}",
        "bugs_and_vulnerabilities": f"/api/issues/search?componentKeys={PROJECT}"
        "&types=BUG,VULNERABILITY&resolved=false&ps=500",
        "smells_by_rule": f"/api/issues/search?componentKeys={PROJECT}"
        "&types=CODE_SMELL&resolved=false&ps=1&facets=rules",
        "hotspots": f"/api/hotspots/search?project={PROJECT}&ps=500",
        "rule_set": f"/api/qualityprofiles/search?project={PROJECT}&language=py",
    }
    found = {}
    for name, path in queries.items():
        status, body = call(path, auth=token_auth())
        found[name] = {"http": status, "body": body}
    return found


def measures_of(found: dict[str, Any]) -> dict[str, str | None]:
    listed = found["measures"]["body"].get("component", {}).get("measures", [])
    return {m["metric"]: m.get("value") for m in listed}


def issue_total(answer: dict[str, Any]) -> int | None:
    """An issue search's own count of what matched; None when the search was not answered."""
    body = answer["body"]
    if answer["http"] != 200 or "issues" not in body:
        return None
    return int(body.get("paging", {}).get("total", len(body["issues"])))


def blocking_failures(
    scanned: int, task_status: str, answer: dict[str, Any]
) -> list[str]:
    """The step's blocking decision, bare correctness only: one named reason per failure, none when
    it passes. The scan failed; its analysis task did not succeed; the search for open bugs and
    vulnerabilities was not answered; or some are open."""
    open_total = issue_total(answer)
    return [
        reason
        for reason, failed in (
            ("the scanner failed", scanned != 0),
            (f"the analysis task: {task_status}", task_status != "SUCCESS"),
            (
                f"the open bugs and vulnerabilities were not read (HTTP {answer['http']})",
                open_total is None,
            ),
            (f"{open_total} open bugs or vulnerabilities", bool(open_total)),
        )
        if failed
    ]


def smells_by_rule(found: dict[str, Any]) -> list[tuple[str, int]]:
    facets = found["smells_by_rule"]["body"].get("facets", [])
    return [
        (value["val"], value["count"])
        for facet in facets
        if facet.get("property") == "rules"
        for value in facet.get("values", [])
    ]


def report(out: Path) -> int:
    found = results()
    out.write_text(json.dumps(found, indent=2), encoding="utf-8")
    measures = measures_of(found)
    for key in MEASURES:
        print(f"{key}: {measures.get(key, 'absent')}")
    print(f"every answer, whole: {out}")
    return 0


def gate() -> int:
    """The gate's step. Blocking, bare correctness only: the scan and its analysis ran, the open bugs
    and vulnerabilities were read, and none is open. Everything else is information. Needs the
    coverage.xml the gate's test step writes."""
    if start() != 0:
        return 1
    if not credentials().get("SONAR_TOKEN") and mint() != 0:
        return 1
    if not (ROOT / "coverage.xml").exists():
        print("no coverage.xml: the gate's test step writes it")
        return 1
    scanned, task_status = analyse()
    found = results()
    measures = measures_of(found)
    answer = found["bugs_and_vulnerabilities"]
    open_total = issue_total(answer)
    project_status = found["quality_gate"]["body"].get("projectStatus", {})
    print(f"sonar analysis task: {task_status}")
    print(
        f"sonar open bugs and vulnerabilities: {open_total} (the measures: bugs"
        f" {measures.get('bugs')}, vulnerabilities {measures.get('vulnerabilities')})"
    )
    for issue in answer["body"].get("issues", []):
        where = issue.get("component", "").removeprefix(f"{PROJECT}:")
        print(
            f"  {issue.get('type')} {issue.get('rule')} {where}:{issue.get('line')}"
            f" {issue.get('message')}"
        )
    print(
        f"sonar (information) quality gate: {project_status.get('status', 'unknown')}; coverage:"
        f" {measures.get('coverage')}%; duplicated lines: {measures.get('duplicated_lines_density')}%;"
        f" lines of code: {measures.get('ncloc')}; security hotspots to review:"
        f" {measures.get('security_hotspots')}"
    )
    for condition in project_status.get("conditions", []):
        print(
            f"  (information) {condition.get('metricKey')}: {condition.get('actualValue')}"
            f" against {condition.get('comparator')} {condition.get('errorThreshold')}:"
            f" {condition.get('status')}"
        )
    print(
        f"sonar (information) code smells: {issue_total(found['smells_by_rule'])}, by rule:"
    )
    for rule, count in smells_by_rule(found):
        print(f"  {count:5d}  {rule}")
    failures = blocking_failures(scanned, task_status, answer)
    print("SONAR: PASSED" if not failures else f"SONAR: FAILED ({'; '.join(failures)})")
    return 1 if failures else 0


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "report" and len(sys.argv) == 3:
        return report(Path(sys.argv[2]))
    commands = {
        "gate": gate,
        "start": start,
        "mint": mint,
        "rebuild": rebuild,
        "scan": scan,
    }
    if command in commands and len(sys.argv) == 2:
        return commands[command]()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
