"""The SonarQube check in RSNA_Knee's gate: SquishOS `verification-gates.md`, "Local SonarQube Docker
check (pre-push)", applied here and made part of `scripts/ci_local.sh` at Rohan's request (2026-10-18:
«Sonar should be part of the CI gate for this project»), on this machine and on GitHub alike.

The server is the kept container `rsna-knee-sonar` (image `sonarqube:latest`, host port 9001, named
volume `rsna-knee-sonar-data`, as Peitho's `peitho-sonar` is set up). Its credentials live outside the
repo, minted once per container, in `~/.config/rsna-knee/sonar-local.env` (mode 600): a fresh container
resets them, so the container is kept. A GitHub runner starts a fresh one each run and mints there. The
scanner is the `sonarsource/sonar-scanner-cli` image, which reads `sonar-project.properties` and
`coverage.xml` from the project root.

    .venv/bin/python scripts/sonar_local.py gate            # the gate's step: blocking (see `gate`)
    .venv/bin/python scripts/sonar_local.py start           # start the container, wait until it is UP
    .venv/bin/python scripts/sonar_local.py mint            # once per container: admin password, token
    .venv/bin/python scripts/sonar_local.py scan            # coverage.xml from the tests, then analyse
    .venv/bin/python scripts/sonar_local.py report <out>    # quality gate, measures, issues, hotspots

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
IMAGE = "sonarqube:latest"
SCANNER = "sonarsource/sonar-scanner-cli:latest"
PORT = 9001
SERVER = f"http://localhost:{PORT}"
SERVER_FROM_DOCKER = f"http://host.docker.internal:{PORT}"
ENV_FILE = Path.home() / ".config" / "rsna-knee" / "sonar-local.env"
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
    """Start the kept container (create it the first time), then wait until the server is UP."""
    if not docker_ready():
        return 1
    inspected = subprocess.run(
        ["docker", "container", "inspect", CONTAINER], capture_output=True, check=False
    )
    if inspected.returncode == 0:
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


def analyse() -> int:
    """The scanner on the project as it stands, with the coverage.xml already written, waiting for
    the server's quality gate (the scanner exits non-zero when the gate fails)."""
    token = credentials().get("SONAR_TOKEN", "")
    if not token:
        print(f"no SONAR_TOKEN in {ENV_FILE}: run mint first")
        return 1
    command = [
        "docker", "run", "--rm", "--add-host=host.docker.internal:host-gateway",
        "-e", f"SONAR_HOST_URL={SERVER_FROM_DOCKER}", "-e", "SONAR_TOKEN",
        "-v", f"{ROOT}:/usr/src", SCANNER, "-Dsonar.qualitygate.wait=true",
    ]  # fmt: skip
    environment = os.environ | {"SONAR_TOKEN": token}
    return subprocess.run(command, cwd=ROOT, env=environment, check=False).returncode


def scan() -> int:
    """coverage.xml from the whole test suite, then the scanner (for a run outside the gate)."""
    for command in (
        [sys.executable, "-m", "coverage", "run", "-m", "pytest", "-q"],
        [sys.executable, "-m", "coverage", "xml", "-o", "coverage.xml"],
    ):
        if subprocess.run(command, cwd=ROOT, check=False).returncode != 0:
            print(f"failed: {' '.join(command[1:])}")
            return 1
    return analyse()


def results() -> dict[str, Any]:
    """The quality gate, the measures, every bug and vulnerability issue and every hotspot."""
    auth = (credentials().get("SONAR_TOKEN", ""), "")
    queries = {
        "quality_gate": f"/api/qualitygates/project_status?projectKey={PROJECT}",
        "measures": f"/api/measures/component?component={PROJECT}&metricKeys={','.join(MEASURES)}",
        "bugs_and_vulnerabilities": f"/api/issues/search?componentKeys={PROJECT}"
        "&types=BUG,VULNERABILITY&resolved=false&ps=500",
        "hotspots": f"/api/hotspots/search?project={PROJECT}&ps=500",
    }
    found = {}
    for name, path in queries.items():
        status, body = call(path, auth=auth)
        found[name] = {"http": status, "body": body}
    return found


def summary(found: dict[str, Any]) -> tuple[str, dict[str, str | None]]:
    gate = (
        found["quality_gate"]["body"].get("projectStatus", {}).get("status", "unknown")
    )
    listed = found["measures"]["body"].get("component", {}).get("measures", [])
    return gate, {m["metric"]: m.get("value") for m in listed}


def report(out: Path) -> int:
    found = results()
    out.write_text(json.dumps(found, indent=2), encoding="utf-8")
    gate, measures = summary(found)
    print(f"quality gate: {gate}")
    for key in MEASURES:
        print(f"{key}: {measures.get(key, 'absent')}")
    print(f"every response, whole: {out}")
    return 0


def gate() -> int:
    """The gate's step. Blocking: the scanner ran, the server's quality gate is OK, and no bug or
    vulnerability is open (the guidance's bar). Code smells, coverage and duplication are printed as
    information. Needs the coverage.xml the gate's test step writes."""
    if start() != 0:
        return 1
    if not credentials().get("SONAR_TOKEN") and mint() != 0:
        return 1
    if not (ROOT / "coverage.xml").exists():
        print("no coverage.xml: the gate's test step writes it")
        return 1
    scanned = analyse()
    found = results()
    gate_status, measures = summary(found)
    issues = found["bugs_and_vulnerabilities"]["body"].get("issues", [])
    print(f"sonar quality gate: {gate_status}")
    print(
        f"sonar open bugs: {measures.get('bugs')}; vulnerabilities: {measures.get('vulnerabilities')};"
        f" security hotspots: {measures.get('security_hotspots')}"
    )
    print(
        f"sonar (information) code smells: {measures.get('code_smells')}; coverage:"
        f" {measures.get('coverage')}%; duplicated lines: {measures.get('duplicated_lines_density')}%;"
        f" lines of code: {measures.get('ncloc')}"
    )
    for issue in issues:
        where = issue.get("component", "").removeprefix(f"{PROJECT}:")
        print(
            f"  {issue.get('type')} {issue.get('rule')} {where}:{issue.get('line')}"
            f" {issue.get('message')}"
        )
    failures = [
        reason
        for reason, failed in (
            ("the scanner failed", scanned != 0),
            (f"quality gate {gate_status}", gate_status != "OK"),
            ("open bugs or vulnerabilities", bool(issues)),
        )
        if failed
    ]
    print("SONAR: PASSED" if not failures else f"SONAR: FAILED ({'; '.join(failures)})")
    return 1 if failures else 0


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "report" and len(sys.argv) == 3:
        return report(Path(sys.argv[2]))
    commands = {"gate": gate, "start": start, "mint": mint, "scan": scan}
    if command in commands and len(sys.argv) == 2:
        return commands[command]()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
