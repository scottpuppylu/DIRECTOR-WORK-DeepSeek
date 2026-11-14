#!/usr/bin/env python3
"""SDD gate (ds.2): the glue between DIRECTOR-WORK work orders and OpenSpec. Only reads.

Why this file exists: OpenSpec (Fission-AI/OpenSpec, MIT) already writes and validates the spec of a change
(proposal.md, specs/, design.md, tasks.md; `openspec validate <change> --strict --json`). It knows nothing about our
work orders, governance levels, DIRECTOR_LOG or locked tests, so this file only links the two. Each check below says
what OpenSpec lacks for it. Nothing here re-implements a spec format or a validator.

Switches: the "sdd" object of director_work.json (all on when missing; docs/02). gate_check.py finds the file with
--config, else next to the order's folder (DIRECTOR/orders/.. = DIRECTOR/director_work.json).

  require_spec_for_strict    true  a Strict order names an OpenSpec change and it validates
  require_spec_for_standard  true  the same for a Standard order (was: Standard optional)
  spec_review_for_standard   true  --match with --dispatch-log needs a `SPEC_REVIEW <WO>` line for Standard too
  tests_first                true  Standard/Strict orders carry TESTS_LOCKED; a locked test that changed fails
  plan_gate                  true  --match with --dispatch-log needs `PLAN_APPROVED <WO> sha=<tasks hash>`, and
                                   tasks.md may only differ from the approved one by ticked boxes, and every
                                   task is ticked at hand-in (OpenSpec's rule: only a box holding `x` is done)
  max_files_per_order        3     scope_check.py: more changed files than this fails a Standard/Strict order
  max_lines_per_order        200   scope_check.py: more changed lines (added + deleted) than this fails it
  stop_after_rounds          1     STOP_RULES of a Standard/Strict order may not allow more rounds than this
  prefer_auto                true  a note when a Standard/Strict order has no AUTO criterion
  openspec_bin               null  the openspec command (path to openspec(.cmd) or to bin/openspec.js); the
                                   environment variable OPENSPEC_BIN wins over it; else `openspec` on PATH

Set a switch to false (or a limit to 0) to turn that rule off for a project; say why in DIRECTOR_LOG.

CLI:
  sdd_gate.py --lock-tests FILE ... [--repo DIR]  print the `TESTS_LOCKED:` list to paste into the order
  sdd_gate.py --plan-hash TASKS_MD --order WO.md  print the `PLAN_APPROVED` line for DIRECTOR_LOG
  sdd_gate.py --which [--config FILE]             where the openspec CLI is found and its version
Exit 0 done, 1 a file or the CLI is missing.
"""
import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

DEFAULTS = {
    "require_spec_for_strict": True,
    "require_spec_for_standard": True,
    "spec_review_for_standard": True,
    "tests_first": True,
    "plan_gate": True,
    "max_files_per_order": 3,
    "max_lines_per_order": 200,
    "stop_after_rounds": 1,
    "prefer_auto": True,
    "openspec_bin": None,
}
GOVERNED = ("Standard", "Strict")
CHANGE_NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
INSTALL_HINT = ("install it (docs/11 「OpenSpec」: npm install --prefix <user folder> @fission-ai/openspec@1.16.0) "
                "and put it on PATH, or set OPENSPEC_BIN / sdd.openspec_bin")
LOG_PREFIX = r"(?:\d{4}-\d{2}-\d{2}[^|\n`]*\|[ \t]*)?"
TIMEOUT = 120


def load_config(order_path=None, config_path=None):
    """(switches, problem or None). Missing file or missing keys: the defaults (all rules on)."""
    config = dict(DEFAULTS)
    path = pathlib.Path(config_path) if config_path else None
    if path is None and order_path is not None:
        guess = pathlib.Path(order_path).resolve().parent.parent / "director_work.json"
        path = guess if guess.is_file() else None
    if path is None:
        return config, None
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as error:
        return config, f"SDD config {path}: cannot read ({error}); the defaults (all rules on) are used"
    sdd = data.get("sdd") if isinstance(data, dict) else None
    if isinstance(sdd, dict):
        config.update({key: value for key, value in sdd.items() if key in DEFAULTS})
    return config, None


def governance(text):
    m = re.search(r"^\s*GOVERNANCE\s*=\s*(\w+)", text, re.M)
    return m.group(1) if m else None


def field(text, key):
    """The value of a `KEY = value` line without a trailing ` # comment`; None when absent."""
    m = re.search(rf"^[ \t]*{key}[ \t]*=[ \t]*(.*)$", text, re.M)
    return re.split(r"\s+#", m.group(1))[0].strip() if m else None


def list_items(text, key):
    """Items of a `KEY:` line followed by `- item` lines (comments after ` #` dropped); None when the key is missing."""
    lines = text.splitlines()
    for n, line in enumerate(lines):
        if re.fullmatch(rf"\s*{key}\s*[:：]\s*", line):
            items = []
            for item in lines[n + 1:]:
                m = re.match(r"\s*-\s+(.*)", item)
                if not m:
                    break
                items.append(re.split(r"\s+#", m.group(1))[0].strip())
            return items
    return None


def file_hash(path):
    """sha256 of a text file with CRLF read as LF, so a checkout's line endings do not change it."""
    return hashlib.sha256(pathlib.Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def plan_hash(path):
    """sha256 of tasks.md with every box unticked and trailing spaces dropped: ticking `- [x]` keeps the hash,
    changing, adding or removing a task does not. OpenSpec tracks ticks but has no notion of an approved plan."""
    text = pathlib.Path(path).read_bytes().decode("utf-8-sig").replace("\r\n", "\n")
    text = re.sub(r"^(\s*[-*]\s+)\[\s*[xX]\s*\]", r"\1[ ]", text, flags=re.M)  # OpenSpec: `[ x]` is done too
    text = "\n".join(line.rstrip() for line in text.split("\n")).strip() + "\n"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def find_cli(config):
    """(command list or None, how it was found or why not). OPENSPEC_BIN wins over sdd.openspec_bin, which wins over
    PATH. An explicit setting that points nowhere is not replaced by PATH: the project asked for that one."""
    for source, value in (("OPENSPEC_BIN", os.environ.get("OPENSPEC_BIN")), ("sdd.openspec_bin", config.get("openspec_bin"))):
        if value:
            path = pathlib.Path(value)
            found = str(path) if path.is_file() else shutil.which(value)
            if not found:
                return None, f"{source}={value} does not exist"
            if found.lower().endswith(".js"):
                node = shutil.which("node")
                return ([node, found], f"{source} (node)") if node else (None, f"{source}={value} needs node on PATH")
            if found.lower().endswith(".py"):  # a stand-in CLI for tests (selftest_ds.py); not for real use
                return [sys.executable, "-I", found], f"{source} (python stand-in)"
            return [found], source
    found = shutil.which("openspec")
    return ([found], "PATH") if found else (None, "no `openspec` on PATH")


def run_cli(command, args, cwd):
    env = dict(os.environ, OPENSPEC_TELEMETRY="0", DO_NOT_TRACK="1", NO_COLOR="1")
    return subprocess.run(command + args, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=TIMEOUT, env=env)


def change_folder(repo, name):
    """(folder, archived): the change folder, or its archived copy `openspec/changes/archive/<date>-<name>`."""
    folder = pathlib.Path(repo) / "openspec" / "changes" / name
    if folder.is_dir():
        return folder, False
    archive = pathlib.Path(repo) / "openspec" / "changes" / "archive"
    hits = sorted(archive.glob(f"*-{name}")) if archive.is_dir() else []
    return (hits[-1], True) if hits else (None, False)


def validate_change(value, repo, config, gov, problems, notes):
    """SPEC_CHANGE names a change folder that exists and passes `openspec validate --strict --json`. OpenSpec
    validates; it cannot know which change a work order is about, or that a missing CLI must not count as a pass."""
    m = re.fullmatch(r"(?:\./)?openspec/changes/([^/\\]+)/?", value.replace("\\", "/"))
    if not m or not CHANGE_NAME.fullmatch(m.group(1)):
        problems.append(f"SPEC_CHANGE: must be `openspec/changes/<name>` (lower-case letters, digits, -) or NONE, got: {value}")
        return None
    name = m.group(1)
    folder, archived = change_folder(repo, name)
    if folder is None:
        problems.append(f"SPEC_CHANGE: {value} not found under {pathlib.Path(repo).resolve()} "
                        "(pass --repo <the project checkout>; create it with `openspec new change <name>`)")
        return None
    if archived:
        notes.append(f"SPEC_CHANGE: {name} is archived ({folder.name}); its deltas are merged into openspec/specs, "
                     "validate skipped")
        return folder
    meta = folder / ".openspec.yaml"
    if meta.is_file() and re.search(r"^\s*skip_specs\s*:\s*true\b", meta.read_text(encoding="utf-8-sig"), re.M):
        if gov == "Strict":
            problems.append(f"SPEC_CHANGE: {name} sets skip_specs: true; a Strict change must carry spec deltas")
        else:
            notes.append(f"SPEC_CHANGE: {name} sets skip_specs: true (no spec deltas); fine for docs or tooling only")
    command, how = find_cli(config)
    if command is None:
        problems.append(f"SPEC_CHANGE: openspec CLI not found ({how}); the change was NOT validated; {INSTALL_HINT}")
        return folder
    try:
        done = run_cli(command, ["validate", name, "--strict", "--json", "--no-interactive"], repo)
    except (OSError, subprocess.SubprocessError) as error:
        problems.append(f"SPEC_CHANGE: openspec could not run ({how}: {error}); the change was NOT validated")
        return folder
    try:
        result = json.loads(done.stdout)
    except ValueError:
        problems.append(f"SPEC_CHANGE: `openspec validate {name} --strict --json` exit {done.returncode}, output is not "
                        f"JSON: {(done.stdout + done.stderr).strip()[:300]}")
        return folder
    items = result.get("items") or []
    failed = (result.get("summary") or {}).get("totals", {}).get("failed")
    if done.returncode == 0 and items and all(item.get("valid") is True for item in items) and not failed:
        return folder
    messages = [issue.get("message", "") for item in items for issue in item.get("issues") or []]
    messages += [s.get("message", "") for s in result.get("status") or []]
    shown = "; ".join(msg[:200] for msg in messages[:3]) or "no message"
    problems.append(f"SPEC_CHANGE: `openspec validate {name} --strict --json` failed (exit {done.returncode}): {shown}")
    return folder


def check_tests(text, repo, problems, notes):
    """TESTS_LOCKED: `- <path> sha256=<64 hex>` per acceptance test, written before dispatch. OpenSpec has scenarios
    but no test files or hashes; the lock is what stops a worker from editing a test until it passes."""
    items = list_items(text, "TESTS_LOCKED")
    if items is None:
        problems.append("TESTS_LOCKED: missing; write the acceptance tests before dispatch, then paste the lines "
                        "`sdd_gate.py --lock-tests <test files>` prints (or `- NONE  # why there is no test`)")
        return
    if not items or items == ["NONE"]:
        notes.append("TESTS_LOCKED: NONE; no locked acceptance test (fine for docs-only work)")
        return
    for item in items:
        m = re.fullmatch(r"(\S+)\s+sha256=([0-9a-fA-F]{64})", item)
        if not m:
            problems.append(f"TESTS_LOCKED: `{item}` is not `<path> sha256=<64 hex>`")
            continue
        path = pathlib.Path(repo) / m.group(1)
        if not path.is_file():
            problems.append(f"TESTS_LOCKED: {m.group(1)} not found under {pathlib.Path(repo).resolve()} (pass --repo)")
        elif file_hash(path) != m.group(2).lower():
            problems.append(f"TESTS_LOCKED: {m.group(1)} changed since it was locked; a worker may not edit the "
                            "acceptance tests (report BLOCKED instead)")


def order_problems(text, order_path, repo, config, notes):
    """The SDD rules for one work order (gate_check.py --order and --match)."""
    problems = []
    gov = governance(text)
    value = field(text, "SPEC_CHANGE")
    governed = gov in GOVERNED
    needed = governed and config.get(f"require_spec_for_{gov.lower()}", True)
    if value is None or value in ("", "NONE"):
        if needed:
            problems.append(f"SPEC_CHANGE: a {gov} order names its OpenSpec change (`SPEC_CHANGE = openspec/changes/"
                            f"<name>`), written and validated before dispatch (sdd.require_spec_for_{gov.lower()})")
        elif value is None and governed:
            notes.append("SPEC_CHANGE: missing; write `SPEC_CHANGE = NONE` when this order has no OpenSpec change")
    else:
        validate_change(value, repo, config, gov, problems, notes)
    if not governed:
        return problems
    if config.get("tests_first", True):
        check_tests(text, repo, problems, notes)
    limit = config.get("stop_after_rounds")
    stop = re.search(r"STOP_RULES\s*[:：=]\s*(.*)", text)
    if limit and stop:
        rounds = [int(n) for n in re.findall(r"(\d+)\s*(?:輪|rounds?)", stop.group(1))]
        if not rounds:
            notes.append(f"STOP_RULES: no round count; write 「同一根因 {limit} 輪沒進展就停」")
        elif max(rounds) > int(limit):
            problems.append(f"STOP_RULES: allows {max(rounds)} rounds on one root cause; at most {limit} "
                            "(sdd.stop_after_rounds)")
    if config.get("prefer_auto", True) and not re.search(r"^\|\s*AC-\d+\s*\|\s*AUTO\s*\|", text, re.M):
        notes.append("acceptance: no AUTO criterion; prefer a condition a command can decide (sdd.prefer_auto)")
    return problems


def log_lines(log_text, event):
    """(id, rest) of each whole-line `<event> <id> ...` in DIRECTOR_LOG, oldest first; lines inside fences skipped."""
    out, fence = [], False
    for line in log_text.splitlines():
        if re.match(r" {0,3}(`{3,}|~{3,})", line):
            fence = not fence
            continue
        m = None if fence else re.fullmatch(LOG_PREFIX + rf"{event}[ \t]+([^\s|`]+?)(?:\.md)?(?:[ \t]+(.*))?", line.strip())
        if m:
            out.append((m.group(1), m.group(2) or ""))
    return out


def match_problems(order_text, ids, log_text, repo, config, notes):
    """--match with --dispatch-log: the spec review and the approved plan are in DIRECTOR_LOG. OpenSpec has no review
    record and no approval step between `propose` and `apply`; the log line is ours."""
    problems = []
    gov = governance(order_text)
    if gov not in GOVERNED or log_text is None:
        return problems
    wanted = {name.upper() for name in ids}
    label = next(iter(ids), "the order")
    if gov == "Strict" or config.get("spec_review_for_standard", True):
        if not any(name.upper() in wanted for name, _ in log_lines(log_text, "SPEC_REVIEW")):
            problems.append(f"SPEC_REVIEW: no `SPEC_REVIEW {label} tokens=... issues=... adopted=...` line in the "
                            "dispatch log; review the order before dispatch (templates/SPEC_REVIEW.md)")
    if config.get("plan_gate", True):
        approved = [rest for name, rest in log_lines(log_text, "PLAN_APPROVED") if name.upper() in wanted]
        if not approved:
            problems.append(f"PLAN_APPROVED: no `PLAN_APPROVED {label} sha=<64>` line in the dispatch log; the worker "
                            "hands in tasks.md and the Director approves it before any code (sdd.plan_gate)")
        else:
            sha = re.search(r"\bsha=([0-9a-fA-F]{64})\b", approved[-1])
            value = field(order_text, "SPEC_CHANGE")
            m = re.fullmatch(r"(?:\./)?openspec/changes/([a-z0-9][a-z0-9-]*)/?", (value or "").replace("\\", "/"))
            folder = change_folder(repo, m.group(1))[0] if m else None
            tasks = folder / "tasks.md" if folder else None
            if not sha:
                problems.append("PLAN_APPROVED: the line has no sha=<64 hex> (sdd_gate.py --plan-hash prints it)")
            elif tasks is None or not tasks.is_file():
                notes.append("PLAN_APPROVED: tasks.md not found under --repo; the approved plan was not compared")
            elif plan_hash(tasks) != sha.group(1).lower():
                problems.append(f"PLAN_APPROVED: {tasks.as_posix()} differs from the approved plan (more than ticked "
                                "boxes); a changed plan goes back to the Director first")
            else:  # handed in: every approved task is done (OpenSpec checks this only for archived changes)
                # OpenSpec reads only a box holding `x` (any case, any spacing) as done; `[ ]`, `[]`, `[~]`, `[-]` are open
                open_tasks = re.findall(r"^\s*[-*]\s+\[(?!\s*[xX]\s*\])[^\]\n]*\]\s*(.*)$",
                                        tasks.read_text(encoding="utf-8-sig"), re.M)
                if open_tasks:
                    problems.append(f"PLAN_APPROVED: {len(open_tasks)} task(s) in tasks.md not ticked, e.g. "
                                    f"{open_tasks[0].strip()[:80]}; finish them or report PARTIAL")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lock-tests", nargs="+", metavar="FILE", help="print TESTS_LOCKED lines (paths relative to --repo)")
    ap.add_argument("--plan-hash", metavar="TASKS_MD", help="print the PLAN_APPROVED line for this tasks.md")
    ap.add_argument("--order", help="with --plan-hash: the work order the plan belongs to")
    ap.add_argument("--repo", default=".", help="the project checkout (default: current folder)")
    ap.add_argument("--which", action="store_true", help="show where the openspec CLI is found and its version")
    ap.add_argument("--config", help="director_work.json (for --which: sdd.openspec_bin)")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if not (a.lock_tests or a.plan_hash or a.which):
        ap.error("give --lock-tests, --plan-hash or --which")
    status = 0
    if a.lock_tests:
        print("TESTS_LOCKED:")
        root = pathlib.Path(a.repo).resolve()
        for name in a.lock_tests:
            path = pathlib.Path(name)
            path = path if path.is_absolute() else pathlib.Path.cwd() / path
            if not path.is_file():
                print(f"# not found: {name}")
                status = 1
                continue
            try:
                rel = path.resolve().relative_to(root).as_posix()
            except ValueError:
                print(f"# outside --repo {root}: {name}")
                status = 1
                continue
            print(f"- {rel} sha256={file_hash(path)}")
    if a.plan_hash:
        if not a.order or not pathlib.Path(a.order).is_file() or not pathlib.Path(a.plan_hash).is_file():
            print("PLAN_HASH: NOT_RUN give an existing --order and tasks.md")
            status = 1
        else:
            title = re.search(r"^#\s+(\S+)", pathlib.Path(a.order).read_text(encoding="utf-8-sig"), re.M)
            ident = title.group(1) if title else pathlib.Path(a.order).stem
            print(f"PLAN_APPROVED {ident} sha={plan_hash(a.plan_hash)}")
    if a.which:
        config, problem = load_config(None, a.config)
        if problem:
            print(f"# {problem}")
        command, how = find_cli(config)
        if command is None:
            print(f"OPENSPEC: NOT_FOUND {how}; {INSTALL_HINT}")
            status = 1
        else:
            try:
                version = run_cli(command, ["--version"], ".").stdout.strip()
            except (OSError, subprocess.SubprocessError) as error:
                version = f"cannot run: {error}"
            print(f"OPENSPEC: {' '.join(command)} ({how}) version={version}")
    return status


if __name__ == "__main__":
    sys.exit(main())
