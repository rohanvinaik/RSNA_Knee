"""The pre-push gate, which git runs before every push (`.githooks/pre-push`, set up once per clone with
`.venv/bin/python scripts/push_checks.py install`), and the lockfile audit the GitHub gate runs too.

Rohan, 2026-10-18: «Set it as an automatic hook», of the gate and the security checks the lead ran by hand
before each push (HOW_TO_BUILD, "Commit and push"; SquishOS repo-hygiene.md: the lockfile audit with all
extras and groups, zizmor on the workflows, and a secret scan of the commits being pushed, not only of the
files on disk). Git hands the hook each ref being pushed, with its local and remote commits, and the hook:

- runs the declared gate (`scripts/ci_local.sh`, zizmor and Sonar included) unless it has already passed on
  exactly the tree being pushed. The gate stamps the tree it ran on when it passes and the tree did not
  change during the run. A tree the gate has not passed on is gated now when it is the clean checkout being
  pushed; any other is refused, since the gate checks the working tree;
- scans every line the pushed commits add, file by file under each file's own name, for secrets
  (detect-secrets); a merge adds the lines it writes itself, in none of its parents (`commit_additions`).
  It recognizes the kernel-benchmark recording's own digests/commit and Detective's typed
  16-hex function digests, only at their respective manifest paths and matched exactly against that
  commit's fields. The Kaggle wrapper's two public SHA-256 release pins are recognized only at their
  own assignments in that commit, matched to the finding's added line. This recognizes digest data,
  never a certificate's completeness. Other findings
  remain unexplained. A line carrying `# pragma: allowlist secret`, detect-secrets' own mark for a
  finding reviewed as no secret, is not a finding: that is how a false finding is answered, never
  `--no-verify`;
- audits the lockfile with all extras and groups (pip-audit), once per push, and names its result
  (`audit_result`): no known flaws; flaws found, each printed with its package, its other names and the
  versions that fix it; or the audit did not run, with pip-audit's own messages saying why. Every package
  it could not audit is printed with its reason, since pip-audit's JSON report alone names them.

The gate and the secret scan refuse the push when they fail or cannot run: a check that did not run is never
a pass. The audit refuses nothing, whatever its result: its findings are leads, not verdicts
(repo-hygiene.md: "ground against current state, then decide"); a flaw reported in a dependency is no worse
after a push than before it, while a secret that leaves this machine cannot be taken back. That was the
lead's proposal, which Rohan accepted, 2026-10-18: «Agree with your fixes, implement them so we have a
working gate/CI action». `git push --no-verify` skips the whole hook. The GitHub gate runs the gate and the
audit again on every push, but not the secret scan, which matters before the commits leave this machine.

    .venv/bin/python scripts/push_checks.py install          # once per clone: git runs .githooks/pre-push
    .venv/bin/python scripts/push_checks.py audit            # the lockfile audit alone (the GitHub gate's step);
                                                             # it exits 0 only when no flaw is known
    .venv/bin/python scripts/push_checks.py scan <revisions> # the secret scan alone, of `git rev-list <revisions>`
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ZERO = "0" * 40
RECORDING = "benchmarks/recorded/manifest.json"
CERTIFICATES = "tests/detective/certificates.json"
RELEASE_PINS = "kaggle/squint-production/run_squint.py"
# Both are public SHA-256 identities: tree_id hashes the bundle's file records;
# memory_manifest_sha256 reads the memory manifest's recorded file digest.
RELEASE_PIN_NAMES = frozenset(
    {"EXPECTED_RUNTIME_BUNDLE_ID", "EXPECTED_MEMORY_MANIFEST_SHA256"}
)
HEX = "Hex High Entropy String"
# Pinned, as the gate pins zizmor, so every push is checked with the same versions. detect-secrets reads the
# next line's name as a secret keyword; the pragma on it is detect-secrets' own mark for a finding reviewed as
# no secret (the hook refused the first push of this file over that line, 2026-10-18).
DETECT_SECRETS = "detect-secrets@1.5.0"  # pragma: allowlist secret
PIP_AUDIT = "pip-audit@2.10.1"


class Unchecked(Exception):
    """A check that could not run, with the reason: the push is refused for it, except in the lockfile
    audit, which prints it as the cause of `audit_did_not_run` and refuses nothing."""


def run(
    command: list[str], cwd: Path | None = None, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    """`command` run to its end, its output kept; a command that cannot start is Unchecked."""
    try:
        return subprocess.run(
            command,
            cwd=cwd or ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as error:
        raise Unchecked(f"{command[0]} could not be run: {error}") from error


def git(*arguments: str) -> str:
    """What `git <arguments>` prints in the project; a git command that fails is Unchecked."""
    done = run(["git", *arguments])
    if done.returncode != 0:
        raise Unchecked(f"git {' '.join(arguments)} failed: {done.stderr.strip()}")
    return done.stdout


def ref_check(
    local_sha: str, local_tree: str, passed: frozenset[str], head: str, clean: bool
) -> str:
    """What one pushed ref needs from the gate, as a named code: nothing for a deletion ("deletion");
    nothing when the gate has passed on exactly its tree ("gate_passed_on_this_tree"); the gate now when
    it is the clean checkout ("gate_runs_now", since the gate checks the working tree); otherwise the push
    is refused ("gate_not_run_on_this_tree")."""
    if local_sha == ZERO:
        return "deletion"
    if local_tree in passed:
        return "gate_passed_on_this_tree"
    if local_sha == head and clean:
        return "gate_runs_now"
    return "gate_not_run_on_this_tree"


def finding_verdict(
    path: str, kind: str, hashed: str, recording: frozenset[str]
) -> str:
    """Recognize only exact typed digest fields at their own path.

    The recognized set is derived from the same commit and file, and for release
    pins from the finding's exact added line. All other findings remain
    unexplained; a function digest does not certify its standing.
    """
    if kind == HEX and hashed in recording:
        if path == RECORDING:
            return "recording_digest"
        if path == CERTIFICATES:
            return "function_digest"
        if path == RELEASE_PINS:
            return "public_digest_pin"
    return "unexplained"


def addition_records(diff: str) -> list[tuple[int, str]]:
    """Added lines with their resulting source line numbers, including combined diffs.

    A hunk header's run of '@' gives the number of parents, one prefix column
    each. Only an all-'+' prefix is new to every parent. Context and partial
    additions advance the resulting line number; deletions do not.
    """
    lines: list[tuple[int, str]] = []
    columns = 0
    number = 0
    for line in diff.splitlines():
        if line.startswith("diff "):
            columns = 0
        elif line.startswith("@@"):
            columns = len(line) - len(line.lstrip("@")) - 1
            result_range = line.split()[columns + 1]
            number = int(result_range[1:].split(",")[0])
        elif columns:
            prefix = line[:columns]
            if prefix == "+" * columns:
                lines.append((number, line[columns:]))
            if len(prefix) == columns and set(prefix) <= {" ", "+"}:
                number += 1
    return lines


def added_lines(diff: str) -> list[str]:
    """The lines a diff of one file adds, its headers and prefix columns left out."""
    return [text for _, text in addition_records(diff)]


def release_pin_hashes(sha: str) -> dict[int, frozenset[str]]:
    """The wrapper's public pin hashes keyed by added-line number in this commit.

    Read syntax, never execute the wrapper. Only a single-name, module-level
    assignment to one of the two documented pins can explain a 64-hex literal.
    Map its source line through the commit's diff so an identical string in an
    untyped assignment (or another commit) is not excused by the pin.
    """
    try:
        source = ast.parse(git("show", f"{sha}:{RELEASE_PINS}"))
    except SyntaxError as error:
        raise Unchecked(f"release pin source cannot be parsed: {error}") from error
    pins: dict[int, set[str]] = {}
    for node in source.body:
        if isinstance(node, ast.AnnAssign):
            target, value = node.target, node.value
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        else:
            continue
        if (
            isinstance(target, ast.Name)
            and target.id in RELEASE_PIN_NAMES
            and isinstance(value, ast.Constant)
            and isinstance(value.value, str)
            and value.lineno == value.end_lineno
            and len(value.value) == 64
            and all(character in "0123456789abcdefABCDEF" for character in value.value)
            and not any(
                other is not node
                and other.end_lineno is not None
                and other.lineno <= value.lineno <= other.end_lineno
                for other in source.body
            )
        ):
            pins.setdefault(value.lineno, set()).add(
                hashlib.sha1(value.value.encode(), usedforsecurity=False).hexdigest()
            )
    diff = git(
        "show",
        "--format=",
        "--unified=0",
        "--no-color",
        "--no-ext-diff",
        "--cc",
        sha,
        "--",
        RELEASE_PINS,
    )
    return {
        added: frozenset(pins[number])
        for added, (number, _) in enumerate(addition_records(diff), start=1)
        if number in pins
    }


def recording_hashes(sha: str) -> frozenset[str]:
    """detect-secrets' SHA-1 of each digest and of the commit that the recording at `sha` names."""
    manifest = json.loads(git("show", f"{sha}:{RECORDING}"))
    strings = [*manifest["arrays"], manifest["commit"]]
    return frozenset(
        hashlib.sha1(text.encode(), usedforsecurity=False).hexdigest()
        for text in strings
    )


def certificate_hashes(sha: str) -> frozenset[str]:
    """Recognize Detective's 16-lowercase-hex function_digest fields only."""
    certificates = json.loads(git("show", f"{sha}:{CERTIFICATES}"))
    if not isinstance(certificates, dict):
        raise Unchecked("Detective certificate document is not an object")
    strings = []
    for record in certificates.values():
        value = record.get("function_digest") if isinstance(record, dict) else None
        if (
            isinstance(value, str)
            and len(value) == 16
            and all(character in "0123456789abcdef" for character in value)
        ):
            strings.append(value)
    return frozenset(
        hashlib.sha1(value.encode(), usedforsecurity=False).hexdigest()
        for value in strings
    )


def pushed_commits(local_sha: str, remote_sha: str, remote: str) -> list[str]:
    """The commits a push of `local_sha` over `remote_sha` sends, oldest first: those the remote does not
    hold already."""
    known = run(["git", "cat-file", "-e", f"{remote_sha}^{{commit}}"])
    if remote_sha != ZERO and known.returncode == 0:
        span = [f"{remote_sha}..{local_sha}"]
    else:
        span = [local_sha, "--not", f"--remotes={remote}"]
    return git("rev-list", "--reverse", *span).split()


def commit_additions(sha: str) -> dict[str, list[str]]:
    """The lines one commit adds, by file. A merge is read as its combined diff (`--cc`), so its own lines
    are those in none of its parents, a conflict's resolution; what it brings from a parent is that
    parent's commits' work, scanned with them or already on the remote."""
    additions: dict[str, list[str]] = {}
    changed = git(
        "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", "--cc", sha
    )
    for path in changed.splitlines():
        diff = git(
            "show",
            "--format=",
            "--unified=0",
            "--no-color",
            "--no-ext-diff",
            "--cc",
            sha,
            "--",
            path,
        )
        lines = added_lines(diff)
        if lines:
            additions[path] = lines
    return additions


def scan(commits: list[str]) -> list[str]:
    """Scan added lines, recognizing exact digest fields at their declared locations."""
    if not commits:
        return []
    with tempfile.TemporaryDirectory() as folder:
        base = Path(folder)
        written = 0
        for sha in commits:
            for path, lines in commit_additions(sha).items():
                target = base / sha / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("\n".join(lines) + "\n", encoding="utf-8")
                written += 1
        done = run(["uvx", DETECT_SECRETS, "scan", "--all-files", "."], cwd=base)
        if done.returncode != 0:
            raise Unchecked(f"detect-secrets failed: {done.stderr.strip()}")
        results = json.loads(done.stdout)["results"]
    print(
        f"secret scan ({DETECT_SECRETS}): the added lines of {written} files, over"
        f" {len(commits)} {'commit' if len(commits) == 1 else 'commits'}"
    )
    refusals: list[str] = []
    accepted = 0
    hashes: dict[tuple[str, str], frozenset[str]] = {}
    pins: dict[str, dict[int, frozenset[str]]] = {}
    for name, findings in sorted(results.items()):
        sha, _, path = name.removeprefix("./").partition("/")
        key = (sha, path)
        if key not in hashes:
            if path == RECORDING:
                hashes[key] = recording_hashes(sha)
            elif path == CERTIFICATES:
                hashes[key] = certificate_hashes(sha)
        if path == RELEASE_PINS and sha not in pins:
            pins[sha] = release_pin_hashes(sha)
        for finding in findings:
            recognized = (
                pins[sha].get(finding["line_number"], frozenset())
                if path == RELEASE_PINS
                else hashes.get(key, frozenset())
            )
            verdict = finding_verdict(
                path,
                finding["type"],
                finding["hashed_secret"],
                recognized,
            )
            where = f"{sha[:7]} {path}, added line {finding['line_number']}: {finding['type']}"
            if verdict in ("recording_digest", "function_digest", "public_digest_pin"):
                accepted += 1
            else:
                refusals.append(f"a possible secret in {where}")
    print(
        f"secret scan: {accepted} findings are exact recorded kernel/function digests or public release pins;"
        f" {len(refusals)} are not"
    )
    return refusals


def skipped_entry(entry: dict) -> bool:
    """Whether a pip-audit report entry is a package it could not audit: a name and a reason, no flaws."""
    return "vulns" not in entry and "skip_reason" in entry


def audit_result(report: object) -> str:
    """The lockfile audit's result, as a named code, from the report pip-audit wrote (None when it wrote
    none): "flaws_found" when a package it audited has a known flaw; "no_known_flaws" when it audited at
    least one package, found no flaw, and every entry of its report can be read; otherwise
    "audit_did_not_run" (no report, an unreadable one, or no package audited), since an audit that did not
    run is never a clean one."""
    entries = report.get("dependencies") if isinstance(report, dict) else None
    if not isinstance(entries, list):
        return "audit_did_not_run"
    audited = [
        entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("vulns"), list)
    ]
    skipped = [
        entry for entry in entries if isinstance(entry, dict) and skipped_entry(entry)
    ]
    if any(entry["vulns"] for entry in audited):
        return "flaws_found"
    if audited and len(audited) + len(skipped) == len(entries):
        return "no_known_flaws"
    return "audit_did_not_run"


def audit_lines(report: object) -> list[str]:
    """What pip-audit's report says, a line each: every known flaw once per package (a report can list one
    twice), with its other names and the versions that fix it, and every package it could not audit, with
    its reason. An entry that cannot be read is printed as written."""
    entries = report.get("dependencies") if isinstance(report, dict) else None
    lines: list[str] = []
    for entry in entries if isinstance(entries, list) else []:
        if not isinstance(entry, dict):
            lines.append(f"an entry that cannot be read: {entry!r}")
            continue
        package = f"{entry.get('name', '?')} {entry.get('version', '')}".strip()
        flaws = entry.get("vulns")
        if skipped_entry(entry):
            lines.append(f"{package}: not audited: {entry['skip_reason']}")
        elif not isinstance(flaws, list):
            lines.append(f"{package}: an entry that cannot be read: {entry!r}")
        else:
            shown: set[str] = set()
            for flaw in flaws:
                if not isinstance(flaw, dict):
                    lines.append(f"{package}: a flaw that cannot be read: {flaw!r}")
                    continue
                name = str(flaw.get("id", "?"))
                if name in shown:
                    continue
                shown.add(name)
                aliases, fixes = flaw.get("aliases"), flaw.get("fix_versions")
                also = ", ".join(map(str, aliases)) if isinstance(aliases, list) else ""
                fixed = ", ".join(map(str, fixes)) if isinstance(fixes, list) else ""
                lines.append(
                    f"{package}: {name}"
                    + (f" (also {also})" if also else "")
                    + (f"; fixed in {fixed}" if fixed else "; no fixed version yet")
                )
    return lines


def audit() -> str:
    """The lockfile audit with all extras and groups (the flags are the rule: a narrower export is a false
    clean), as a named result (`audit_result`), printed with what pip-audit's report says (`audit_lines`)
    and its own messages whole. It refuses nothing: the result is the caller's to print and go on."""
    report: object = None
    messages = ""
    with tempfile.TemporaryDirectory() as folder:
        requirements = Path(folder) / "requirements.txt"
        written = Path(folder) / "pip-audit.json"
        try:
            exported = run(
                [
                    "uv",
                    "export",
                    "--frozen",
                    "--no-hashes",
                    "--no-emit-project",
                    "--all-extras",
                    "--all-groups",
                    "--format",
                    "requirements-txt",
                    "--output-file",
                    str(requirements),
                ]
            )
            if exported.returncode != 0:
                raise Unchecked(f"uv export failed: {exported.stderr.strip()}")
            done = run(
                [
                    "uvx",
                    PIP_AUDIT,
                    "-r",
                    str(requirements),
                    "--no-deps",
                    "--disable-pip",
                    "--format",
                    "json",
                    "--output",
                    str(written),
                ]
            )
            messages = done.stdout + done.stderr
            if written.is_file():
                report = json.loads(written.read_text(encoding="utf-8"))
        except Unchecked as error:
            messages = str(error)
        except (OSError, ValueError) as error:
            messages = f"{messages.rstrip()}\nits report could not be read: {error}"
    result = audit_result(report)
    print(f"lockfile audit ({PIP_AUDIT}, all extras and groups): {result}")
    for line in audit_lines(report):
        print(f"  {line}")
    print(messages.rstrip())
    print(
        "lockfile audit: a lead, not a verdict (SquishOS repo-hygiene.md); it refuses no push"
    )
    return result


def git_path(name: str) -> Path:
    """A path inside this clone's git folder."""
    path = Path(git("rev-parse", "--git-path", name).strip())
    return path if path.is_absolute() else ROOT / path


def worktree_tree() -> str:
    """The tree the working tree would be committed as (every file git does not ignore), written through a
    copy of the index so the real one is left as it was."""
    with tempfile.TemporaryDirectory() as folder:
        index = Path(folder) / "index"
        current = git_path("index")
        if current.exists():
            index.write_bytes(current.read_bytes())
        env = {**os.environ, "GIT_INDEX_FILE": str(index)}
        added = run(["git", "add", "-A", "."], env=env)
        if added.returncode != 0:
            raise Unchecked(
                f"git add -A (to a copy of the index) failed: {added.stderr.strip()}"
            )
        written = run(["git", "write-tree"], env=env)
        if written.returncode != 0:
            raise Unchecked(f"git write-tree failed: {written.stderr.strip()}")
        return written.stdout.strip()


def passed_trees() -> frozenset[str]:
    """The trees the gate has passed on in this clone."""
    folder = git_path("gate-passed")
    return (
        frozenset(entry.name for entry in folder.iterdir())
        if folder.is_dir()
        else frozenset()
    )


def stamp(tree: str) -> int:
    """Stamp `tree`, read when the gate began, as passed, if the working tree is still exactly it."""
    if not tree or worktree_tree() != tree:
        print(
            "push gate: the tree changed during the gate (or was not read), so it is not stamped"
        )
        return 0
    folder = git_path("gate-passed")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / tree).write_text(
        datetime.now(UTC).isoformat(timespec="seconds") + "\n", encoding="utf-8"
    )
    print(
        f"push gate: stamped tree {tree}; a push of exactly this tree will not run the gate again"
    )
    return 0


def hook(remote: str, pushed: list[list[str]]) -> int:
    """The pre-push gate over the refs git is pushing to `remote`; 1 refuses the push. The gate and the
    secret scan refuse; the lockfile audit's result is printed and refuses nothing."""
    refusals: list[str] = []
    audited = ""
    try:
        head = git("rev-parse", "HEAD").strip()
        clean = git("status", "--porcelain") == ""
        passed = passed_trees()
        gated = False
        sending: list[str] = []
        for local_ref, local_sha, remote_ref, remote_sha in pushed:
            tree = (
                git("rev-parse", f"{local_sha}^{{tree}}").strip()
                if local_sha != ZERO
                else ""
            )
            code = ref_check(local_sha, tree, passed, head, clean)
            print(f"push gate: {local_ref} -> {remote_ref}: {code}")
            if code == "deletion":
                continue
            if code == "gate_runs_now" and not gated:
                gated = True
                if subprocess.run(
                    ["bash", "scripts/ci_local.sh"], cwd=ROOT, check=False
                ).returncode:
                    refusals.append(f"the gate failed on {local_ref} ({local_sha[:7]})")
            elif code == "gate_not_run_on_this_tree":
                refusals.append(
                    f"the gate has not passed on the tree of {local_ref} ({local_sha[:7]}), and it can"
                    " check only the clean checkout being pushed: commit or stash the changes, or check"
                    " that commit out, then push again"
                )
            for sha in pushed_commits(local_sha, remote_sha, remote):
                if sha not in sending:
                    sending.append(sha)
        if sending:
            refusals.extend(scan(sending))
            audited = audit()
    except (Unchecked, OSError, ValueError, KeyError) as error:
        refusals.append(f"the push gate could not finish: {error}")
    for refusal in refusals:
        print(f"push gate: REFUSED: {refusal}")
    if audited and audited != "no_known_flaws":
        print(
            f"push gate: the lockfile audit's result is {audited}, printed above: a lead to look into,"
            " which refuses nothing"
        )
    if refusals:
        return 1
    print("push gate: PASSED")
    return 0


def install() -> int:
    """Have git run `.githooks/pre-push` before every push from this clone."""
    hook_file = ROOT / ".githooks" / "pre-push"
    if not hook_file.is_file() or not os.access(hook_file, os.X_OK):
        print(f"{hook_file} is missing or not executable")
        return 1
    git("config", "core.hooksPath", ".githooks")
    print("git now runs .githooks/pre-push before every push from this clone")
    return 0


def main(arguments: list[str]) -> int:
    command, rest = (arguments[0], arguments[1:]) if arguments else ("", [])
    try:
        if command == "hook" and rest:
            pushed = [
                line.split() for line in sys.stdin.read().splitlines() if line.strip()
            ]
            return hook(rest[0], pushed)
        if command == "audit":
            # Its result is printed; the exit is 1 for any result but no known flaws. The GitHub gate's
            # step carries on past it (continue-on-error), so the gate after it always runs.
            return 0 if audit() == "no_known_flaws" else 1
        if command == "scan" and rest:
            refusals = scan(git("rev-list", "--reverse", *rest).split())
        elif command == "tree":
            print(worktree_tree())
            return 0
        elif command == "stamp":
            return stamp(rest[0] if rest else "")
        elif command == "install":
            return install()
        else:
            print(__doc__)
            return 2
    except Unchecked as error:
        refusals = [str(error)]
    for refusal in refusals:
        print(f"REFUSED: {refusal}")
    return 1 if refusals else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
