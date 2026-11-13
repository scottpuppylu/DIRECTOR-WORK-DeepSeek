#!/usr/bin/env python3
"""Smoke tests for the DIRECTOR-WORK DeepSeek Harness (DSH) edition toolchain.

  python -I -X utf8 tools/selftest_ds.py [--verbose] [--keep]

Runs, on this machine and offline:
  help        --help of every tool that has a CLI
  library     tools/dsh_session.py imports and exposes the documented API
  usage       dsh_usage.py on the real DSH projection cache (exit 0, or 2 with NO_DATA)
  audit       dsh_audit.py build on the newest DSH session log, its verify, then report_vs_audit.py
              on a tiny synthetic TASK REPORT made from one line of that audit
  setup       dsh_setup_check.py on a temp DIRECTOR folder
  status      status_gen.py on a temp config, then the generated status.py compiles and runs
  doctor      dsh_doctor.py (exit 0 when no check FAILs)
  guard       dsh_guard.py clean / remind / block / pause-flag cases
  hash        gate_check.py --hash on a sample file
  evidence    evidence_record.py run + verify in a temp git repo (SKIP when git is missing)
  matching    report_vs_audit.py on synthetic wrapped / absolute-path / cut-at-500 audit lines:
              the DSH PTC form a report's friendly RAN line has to match, plus one negative case
  matching_221  2.2.1-ds.1: report_vs_audit matches() on 21 cut / backslash / quote / launcher / wildcard cases
              in process, two of them through the CLI, and 6 mutations of the matcher that must each get a case wrong
  setup_shadow  2.2.1-ds.1: dsh_setup_check shadow lines (PO IDs, RESUME values, director_work.json keys) stay
              notes without --strict and fail with it; a clean folder passes --strict
  audit_rebuild 2.2.1-ds.1: dsh_audit.chain_lines writes the kind=rebuild first line, dsh_audit verify accepts the
              chain and report_vs_audit reads it with a note (no DSH session log needed)

Prints PASS / FAIL / SKIP per test and a summary line
  SELFTEST_DS: PASS|FAIL tests=n pass=n fail=n skip=n
Exit codes: 0 all tests passed (SKIP is not a failure), 1 any FAIL, 2 cannot run.
Standard library only; no network; the temp folder is removed unless --keep.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import pathlib
import py_compile
import shutil
import subprocess
import sys
import tempfile
import time

TOOLS = pathlib.Path(__file__).resolve().parent
PY_ARGS = [sys.executable, "-I", "-X", "utf8"]
TIMEOUT = 240
BT = chr(96)
CLI_TOOLS = ("dsh_usage", "dsh_audit", "dsh_doctor", "dsh_setup_check", "dsh_guard", "gate_check",
             "scope_check", "evidence_record", "report_vs_audit", "trace_report", "round_check", "status_gen",
             "metrics_report", "memory_size_check", "secret_mask", "pause_ctl", "audit_log")
TESTS = []


class Skip(Exception):
    """The test cannot run here (missing optional dependency, no DSH data); not a failure."""


def test(function):
    TESTS.append(function)
    return function


def run_tool(name, *args, cwd=None):
    return subprocess.run(PY_ARGS + [str(TOOLS / (name + ".py"))] + [str(a) for a in args],
                          cwd=str(cwd) if cwd else None, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=TIMEOUT)


def run_prog(args, cwd=None):
    return subprocess.run([str(a) for a in args], cwd=str(cwd) if cwd else None, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=TIMEOUT)


def text_of(proc):
    return (proc.stdout or "") + (proc.stderr or "")


def tail(text, limit=700):
    text = (text or "").strip()
    return text if len(text) <= limit else "..." + text[-limit:]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def load_tool(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def dsh_home():
    value = os.environ.get("DSH_HOME")
    return pathlib.Path(value) if value else pathlib.Path.home() / ".dsh"


@test
def help_every_tool(tmp):
    bad = []
    for name in CLI_TOOLS:
        path = TOOLS / (name + ".py")
        if not path.is_file():
            bad.append(name + ": file missing")
            continue
        proc = run_tool(name, "--help")
        if proc.returncode != 0 or "usage:" not in text_of(proc).lower():
            bad.append("%s: exit=%s" % (name, proc.returncode))
    require(not bad, "; ".join(bad))
    return "%d tools" % len(CLI_TOOLS)


@test
def session_library(tmp):
    module = load_tool("dsh_session")
    for name in ("VERSION", "decode_session", "list_session_files", "find_node", "session_role",
                 "agent_catalog", "default_sessions_root", "default_projcache_root"):
        require(hasattr(module, name), "dsh_session.py has no " + name)
    require(isinstance(module.VERSION, int) and module.VERSION >= 1, "dsh_session.VERSION is not an int >= 1")
    return "VERSION=%s sessions-root=%s" % (module.VERSION, module.default_sessions_root())


@test
def dsh_usage(tmp):
    proc = run_tool("dsh_usage", "--json")
    if proc.returncode == 0:
        try:
            data = json.loads(proc.stdout)
        except ValueError:
            raise AssertionError("dsh_usage --json exit 0 but stdout is not JSON: " + tail(proc.stdout))
        require(isinstance(data, dict) and isinstance(data.get("sessions"), list),
                "dsh_usage --json has no sessions list")
        return "rc=0 sessions=%d source=%s" % (len(data["sessions"]), (data.get("source") or {}).get("cache_root"))
    if proc.returncode == 2:
        text = text_of(proc)
        require(any(word in text for word in ("NO_DATA", "not found", "missing", "no session")),
                "dsh_usage exit 2 without a clear message: " + tail(text))
        return "rc=2 no data: " + tail(text, 160)
    raise AssertionError("dsh_usage --json exit %s: %s" % (proc.returncode, tail(text_of(proc))))


def newest_session_log():
    root = dsh_home() / "sessions"
    files = sorted(root.glob("*/*/session.v*.jsonl.zstd"), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


@test
def dsh_audit_and_report(tmp):
    log = newest_session_log()
    if log is None:
        raise Skip("no DSH session log under " + str(dsh_home() / "sessions"))
    out = tmp / "audit.jsonl"
    proc = run_tool("dsh_audit", "build", "--out", out, "--session", log.parent.name, "--force")
    text = text_of(proc)
    if proc.returncode != 0 and "node" in text.lower() and "not found" in text.lower():
        raise Skip("Node is needed to decode the session log: " + tail(text, 200))
    require(proc.returncode == 0, "dsh_audit build exit %s: %s" % (proc.returncode, tail(text)))
    require(out.is_file() and out.stat().st_size > 0, "dsh_audit build wrote no audit file")
    entries = [json.loads(line) for line in out.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    require(entries, "the built audit has no lines")
    verify = run_tool("dsh_audit", "verify", "--log", out)
    require(verify.returncode == 0 and "OK" in text_of(verify),
            "dsh_audit verify exit %s: %s" % (verify.returncode, tail(text_of(verify))))
    require(entries[0].get("kind") == "rebuild" and (entries[0].get("source") or {}).get("by") == "dsh_audit.py",
            "line 1 of the built audit is not the dsh_audit.py rebuild line: " + tail(json.dumps(entries[0]), 300))
    session = next((entry.get("session_id") for entry in entries if entry.get("session_id")), None)
    require(session, "no audit line has a session_id")
    command = None
    for entry in entries:
        if str(entry.get("tool") or "").lower() not in ("powershell", "bash", "pwsh"):
            continue
        if entry.get("kind") != "result":
            continue
        try:
            value = json.loads(entry.get("input") or "")
        except ValueError:
            continue
        found = str(value.get("command") or "") if isinstance(value, dict) else ""
        if found and "\n" not in found and len(found) < 380:
            command = found
            break
    report = tmp / "TASK_REPORT.md"
    if command:
        write(report, "SESSION_ID: " + session + "\n\nRAN:\n- " + BT + command + BT + " exit=0\n")
    else:
        write(report, "SESSION_ID: " + session + "\n\nRAN:\n")
    check = run_tool("report_vs_audit", "--report", report, "--log", out)
    require(check.returncode == 0, "report_vs_audit exit %s: %s" % (check.returncode, tail(text_of(check))))
    require("REPORT_VS_AUDIT:" in text_of(check), "report_vs_audit printed no summary: " + tail(text_of(check)))
    return "%d audit lines, %s" % (len(entries), "claim checked" if command else "no claim (NONE)")


def director_fixture(folder):
    write(folder / "DIRECTOR_STATE.md",
          "# DIRECTOR_STATE\n\nUPDATED: 2026-11-12\nPENDING_METHOD: ask_user_question; open questions are kept in "
          "DIRECTOR/PO_PENDING.md\n\n## SECTIONS\n")
    write(folder / "ACTIVE_WORKSTREAMS.md", "# ACTIVE_WORKSTREAMS\n\n| ID | STATE |\n|---|---|\n| W1 | running |\n")
    write(folder / "DECISION_REGISTER.md", "# DECISION_REGISTER\n\n| ID | DECISION |\n|---|---|\n| D1 | test |\n")
    write(folder / "DIRECTOR_OPERATING_RULES.md", "# DIRECTOR_OPERATING_RULES\n\n1. Keep the folder authoritative.\n")
    write(folder / "PO_PENDING.md",
          "## 未關閉\n\nID: OD-001\nSTATUS: open\nQUESTION: Which database?\nOPTIONS: a) sqlite b) none\n"
          "RECOMMENDED: a\nSOURCE: BOOTSTRAP\nANSWER:\n\n## 已關閉\n\nID: ACT-002\nSTATUS: answered\n"
          "QUESTION: Old question?\nOPTIONS: a) yes b) no\nRECOMMENDED: a\nSOURCE: DIRECTOR\nANSWER: yes\n")
    write(folder / "RESUME_STATE.md",
          "PROGRESS: setup checked\nDOING: nothing\nNEXT_STEP: wait for the PO\nCOMMS: NONE\n\n# RESUME_STATE\n")
    write(folder / "director_work.json", json.dumps({"schema_version": 1}, indent=1) + "\n")
    return folder


@test
def dsh_setup_check(tmp):
    folder = director_fixture(tmp / "DIRECTOR")
    proc = run_tool("dsh_setup_check", folder)
    text = text_of(proc)
    require(proc.returncode == 0 and "DSH_SETUP_CHECK: PASS" in text,
            "dsh_setup_check exit %s: %s" % (proc.returncode, tail(text)))
    return "fixture PASS"


@test
def status_gen_round_trip(tmp):
    base = tmp / "status"
    write(base / "po" / "PO_PENDING.md",
          "## 未關閉\n\nID: OD-001\nSTATUS: open\nQUESTION: q\nOPTIONS: a, b\nRECOMMENDED: a\nSOURCE: test\nANSWER:\n\n"
          "## 已關閉\n\nID: ACT-002\nSTATUS: answered\nQUESTION: q2\nOPTIONS: a, b\nRECOMMENDED: a\nSOURCE: test\n"
          "ANSWER: a\n")
    write(base / "po" / "DIRECTOR_STATE.md", "# DIRECTOR_STATE\n\nPENDING_METHOD: ask_user_question\n")
    write(base / "orders" / "WO-1.md", "# WO-1\nSTATUS: OPEN\n")
    write(base / "audit" / "audit-s1.jsonl",
          json.dumps({"seq": 1, "ts": "2026-11-12T10:00:00+08:00", "session_id": "s1", "agent_id": "w1",
                      "tool": "PowerShell", "tool_use_id": "t1", "kind": "result",
                      "input": json.dumps({"command": "tail -n 5 run.log"}), "result": {"status": "ok"}}) + "\n")
    config = {
        "schema_version": 1, "name": "selftest-director",
        "po_pending": {"path": "po/PO_PENDING.md", "counts": [
            {"label": "pending open", "regex": "(?m)^STATUS:\\s*open\\b"},
            {"label": "pending answered", "regex": "(?m)^STATUS:\\s*answered\\b"}]},
        "orders": {"dir": "orders", "glob": "WO-*.md", "closed": "(?im)^STATUS\\s*:\\s*CLOSED", "show": 8},
        "audit": {"globs": ["audit/audit-*.jsonl"], "hours": 24},
        "disk": str(pathlib.Path(tmp.anchor)), "disk_min_gib": 0, "max_lines": 60,
    }
    cfg = write(base / "config.json", json.dumps(config, indent=1) + "\n")
    script = base / "status.py"
    proc = run_tool("status_gen", "--config", cfg, "--out", script)
    require(proc.returncode == 0, "status_gen exit %s: %s" % (proc.returncode, tail(text_of(proc))))
    require(script.is_file(), "status_gen wrote no status.py")
    try:
        py_compile.compile(str(script), doraise=True)
    except py_compile.PyCompileError as error:
        raise AssertionError("generated status.py does not compile: " + str(error))
    run = run_prog(PY_ARGS + [str(script)], cwd=base)
    text = text_of(run)
    require(run.returncode == 0, "generated status.py exit %s: %s" % (run.returncode, tail(text)))
    require("STATUS selftest-director" in text, "generated status.py printed no STATUS line: " + tail(text))
    require("PENDING_METHOD_MISSING" not in text, "generated status.py warns PENDING_METHOD_MISSING: " + tail(text))
    return "generated script ran: " + text.splitlines()[0]


@test
def dsh_doctor(tmp):
    proc = run_tool("dsh_doctor")
    text = text_of(proc)
    require("DSH_DOCTOR:" in text, "dsh_doctor printed no summary: " + tail(text))
    if proc.returncode != 0:
        failed = [line for line in text.splitlines() if "FAIL" in line]
        raise AssertionError("dsh_doctor exit %s: %s" % (proc.returncode, tail("; ".join(failed) or text)))
    return "no FAIL"


@test
def dsh_guard(tmp):
    clean = run_tool("dsh_guard", "--command", "git status")
    require(clean.returncode == 0, "git status exit %s: %s" % (clean.returncode, tail(text_of(clean))))
    remind = run_tool("dsh_guard", "--command", "git push origin main")
    require(remind.returncode == 1 and ("G02" in text_of(remind) or "push" in text_of(remind).lower()),
            "git push exit %s: %s" % (remind.returncode, tail(text_of(remind))))
    block = run_tool("dsh_guard", "--command", "git push origin main", "--mode", "block")
    require(block.returncode == 2, "block mode exit %s: %s" % (block.returncode, tail(text_of(block))))
    flag = write(tmp / "PAUSE", "")
    pause = run_tool("dsh_guard", "--command", "git status", "--pause-flag", flag)
    require(pause.returncode == 2 and "pause" in text_of(pause).lower(),
            "existing pause flag exit %s: %s" % (pause.returncode, tail(text_of(pause))))
    absent = run_tool("dsh_guard", "--command", "git status", "--pause-flag", tmp / "NO_PAUSE")
    require(absent.returncode == 0, "absent pause flag exit %s: %s" % (absent.returncode, tail(text_of(absent))))
    return "clean/remind/block/pause-present/pause-absent"


@test
def gate_check_hash(tmp):
    sample = write(tmp / "sample.txt", "selftest sample\n")
    proc = run_tool("gate_check", "--hash", sample)
    text = text_of(proc)
    require(proc.returncode == 0, "gate_check --hash exit %s: %s" % (proc.returncode, tail(text)))
    sha = hashlib.sha256(sample.read_bytes()).hexdigest()
    require(sha in text, "gate_check --hash printed no sha256 of the sample: " + tail(text))
    return "sha256 matches"


@test
def evidence_record(tmp):
    if shutil.which("git") is None:
        raise Skip("git is not on PATH")
    repo = tmp / "repo"
    repo.mkdir()
    write(repo / "calc.py", "def add(a, b):\n    return a + b\n")
    for args in (["git", "init", "-q"], ["git", "config", "user.email", "selftest@example.invalid"],
                 ["git", "config", "user.name", "Selftest"], ["git", "add", "calc.py"],
                 ["git", "commit", "-q", "-m", "init"]):
        proc = run_prog(args, cwd=repo)
        require(proc.returncode == 0, " ".join(args) + " failed: " + tail(text_of(proc)))
    out = tmp / "evidence"
    run = run_tool("evidence_record", "run", "--out-dir", out, "--label", "SELFTEST", "--cwd", repo,
                   "--", "git", "status", "--porcelain")
    require(run.returncode == 0, "evidence_record run exit %s: %s" % (run.returncode, tail(text_of(run))))
    records = sorted(out.glob("*.json"))
    require(records, "evidence_record run wrote no record under " + str(out))
    verify = run_tool("evidence_record", "verify", records[-1])
    require(verify.returncode == 0 and "EVIDENCE_VERIFY: OK" in text_of(verify),
            "evidence_record verify exit %s: %s" % (verify.returncode, tail(text_of(verify))))
    return "record+verify OK"


def synthetic_audit(tmp, audit):
    commands = [
        r'& "C:\Tools\python.exe" -I -X utf8 "C:\ws\tools\scope_check.py" --order "C:\ws\orders\WO-7.md" --repo "C:\ws" 2>&1; Write-Output "EXIT=$LASTEXITCODE"',
        r'& "C:\Python312\python.exe" -I -X utf8 "D:\ws\tools\evidence_record.py" run --out-dir "D:\ws\evidence" --label AC-1 --order "D:\ws\WO-1.md" --artifact calculator.py -- python -X utf8 -m unittest -v test_calculator 2>&1',
        r'& "C:\Tools\python.exe" -I -X utf8 "D:\ws\tools\gate_check.py" --order "D:\ws\orders\WO-9.md" ' + "--note x " * 80,
    ]
    claims = [
        "scope_check.py --order WO-7.md --repo <repo>",
        "evidence_record.py run --out-dir ... --label AC-1 --order ... --artifact calculator.py -- python -X utf8 -m unittest -v test_calculator",
        "gate_check.py --order WO-9.md",
    ]
    lines, prev = [], audit.GENESIS
    for number, command in enumerate(commands, 1):
        raw = json.dumps({"command": command})
        entry = {"ts": "2026-11-12T23:40:0%d+08:00" % number, "session_id": "selftest-session",
                 "agent_id": "selftest", "tool": "PowerShell", "tool_use_id": "call-%d" % number, "kind": "result",
                 "input": raw if len(raw) <= 500 else raw[:500] + "\u2026",
                 "result": {"status": "ok", "sha256": "0" * 64, "length": 0}, "seq": number, "prev": prev}
        entry["hash"] = audit.digest(entry)
        prev = entry["hash"]
        lines.append(json.dumps(entry, ensure_ascii=False))
    log = write(tmp / "synthetic-audit.jsonl", "\n".join(lines) + "\n")
    body = "".join("- " + BT + claim + BT + " exit=0\n" for claim in claims)
    report = write(tmp / "synthetic-report.md", "SESSION_ID: selftest-session\n\nRAN:\n" + body)
    return log, report


@test
def report_matching(tmp):
    audit = load_tool("audit_log")
    log, report = synthetic_audit(tmp, audit)
    proc = run_tool("report_vs_audit", "--report", report, "--log", log)
    text = text_of(proc)
    require(proc.returncode == 0, "wrapped/absolute/cut claims exit %s: %s" % (proc.returncode, tail(text)))
    require("REPORT_VS_AUDIT: PASS" in text and "claims=3 ok=3" in text,
            "wrapped/absolute/cut claims did not all match: " + tail(text))
    negative = write(tmp / "synthetic-negative.md",
                     "SESSION_ID: selftest-session\n\nRAN:\n- " + BT + "git push origin main" + BT + " exit=0\n")
    bad = run_tool("report_vs_audit", "--report", negative, "--log", log)
    require(bad.returncode == 1 and "FAIL" in text_of(bad),
            "a claim that was never run did not FAIL: " + tail(text_of(bad)))
    return "3 DSH-form claims PASS, 1 false claim FAIL"


RVA_WIN = '"C:\\Program Files\\Python312\\python.exe" -I -X utf8 D:\\w\\tools\\build_all.py ' + "--flag " * 90 + "--end"
RVA_UNC = "Get-FileHash \\\\server\\share\\out\\pack.zip; " + "Write-Output done; " * 40
RVA_QUOTE = 'python -I -X utf8 tools/report.py --title "say \\"hi\\" twice" ' + "--x " * 140
RVA_PLAIN = 'python -I -X utf8 tools/report.py --title "big title" --out "D:/w/out dir" ' + "--x " * 140
RVA_CLOSED = "python -I -X utf8 tools/selftest.py --quick --group report_vs_audit"
# (name, tool, tool input, claimed command, should match); the log lines are cut at 500 characters by audit_log.summary,
# the same cases as upstream selftest.py test_report_vs_audit_221
RVA_221_CASES = [
    ("cut Windows command with a quoted path", "Bash", {"command": RVA_WIN, "description": "build"},
     '"C:\\Program Files\\Python312\\python.exe" -I -X utf8 D:\\w\\tools\\build_all.py --flag --flag', True),
    ("cut Windows command, other slash direction", "PowerShell", {"command": RVA_WIN},
     "C:/Program Files/Python312/python.exe -I -X utf8 D:/w/tools/build_all.py --flag", True),
    ("cut command with a UNC backslash path", "PowerShell", {"command": RVA_UNC},
     "Get-FileHash \\\\server\\share\\out\\pack.zip", True),
    ("cut UNC path, wrong file", "PowerShell", {"command": RVA_UNC}, "Get-FileHash \\\\server\\share\\out\\other.zip", False),
    ("cut command with quotes", "Bash", {"command": RVA_PLAIN},
     'tools/report.py --title "big title" --out "D:/w/out dir" --x --x', True),
    ("quotes, wrong title", "Bash", {"command": RVA_PLAIN}, 'tools/report.py --title "small title"', False),
    ("cut command with shell-escaped quotes, claimed as typed", "Bash", {"command": RVA_QUOTE},
     'python -I -X utf8 tools/report.py --title "say \\"hi\\" twice" --x', True),
    ("escaped quotes, wrong title", "Bash", {"command": RVA_QUOTE}, 'tools/report.py --title "say bye twice"', False),
    ("closed command in a cut line: same command", "Bash", {"command": RVA_CLOSED, "description": "d " * 300},
     RVA_CLOSED, True),
    ("closed command in a cut line: a longer claim is not a prefix match", "Bash",
     {"command": RVA_CLOSED, "description": "d " * 300}, RVA_CLOSED + " --full", False),
    ("launcher and startup flags dropped", "Bash", {"command": RVA_CLOSED}, "py tools\\selftest.py --quick", True),
    ("leading & of PowerShell dropped", "PowerShell", {"command": '& "C:\\Py\\python.exe" -I tools\\selftest.py --quick'},
     "python tools/selftest.py --quick", True),
    ("a file name matches a longer path", "PowerShell", {"command": "Get-FileHash D:\\w\\out\\pack.zip"},
     "Get-FileHash pack.zip", True),
    ("a file name does not match a different file", "PowerShell", {"command": "Get-FileHash D:\\w\\out\\pack.zip"},
     "Get-FileHash ack.zip", False),
    ("... skips words", "Bash", {"command": RVA_WIN}, "build_all.py ... --flag", True),
    ("<name> skips words", "Bash", {"command": RVA_CLOSED}, "tools/selftest.py <mode> --group report_vs_audit", True),
    ("one real word with wildcards proves nothing", "Bash", {"command": RVA_CLOSED}, "... selftest.py", False),
    ("only wildcards prove nothing", "Bash", {"command": RVA_CLOSED}, "... <x> ...", False),
    ("words out of order do not match", "Bash", {"command": RVA_CLOSED}, "--group tools/selftest.py", False),
    ("a launcher alone is not a claim", "Bash", {"command": RVA_CLOSED}, "python -I -X utf8", False),
    ("only Bash / PowerShell / pwsh lines count", "Agent", {"command": RVA_CLOSED}, "tools/selftest.py --quick", False)]
RVA_MUTATIONS = [
    ("no JSON decoding of a cut line", [("        text, closed = json_string_prefix(body[found.end():])\n",
                                         "        text, closed = body[found.end():], False\n")]),
    ("a closed command still counts as cut", [('        return text, not closed and raw.endswith("\u2026")\n',
                                               '        return text, raw.endswith("\u2026")\n')]),
    ("no launcher drop", [("    if parts and LAUNCHER.search(parts[0]):\n", "    if False:\n")]),
    ("no path-suffix word", [('    return claim_word == log_word or log_word.endswith("/" + claim_word.lstrip("/"))\n',
                              "    return claim_word == log_word\n")]),
    ("no 2-word guard", [("MIN_WORDS = 2  #", "MIN_WORDS = 0  #")]),
    ("no shell-tool check", [('    if str(entry.get("tool") or "").lower() not in SHELL_TOOLS:\n', "    if False:\n")])]


def mutated(name, swaps):
    """A copy of a tool module with one check taken out; each (old, new) anchor must occur exactly once."""
    path = TOOLS / (name + ".py")
    source = path.read_text(encoding="utf-8")
    for old, new in swaps:
        require(source.count(old) == 1, "mutation anchor in %s.py found %d times: %r" % (name, source.count(old), old))
        source = source.replace(old, new)
    module = type(sys)(name + "_mutant")
    module.__file__ = str(path)  # the tools load their neighbours from their own folder
    exec(compile(source, str(path), "exec"), module.__dict__)
    return module


def rva_wrong(module, audit):
    return [name for name, tool, data, claim, want in RVA_221_CASES
            if bool(module.matches({"command": claim}, {"tool": tool, "input": audit.summary(data)})) != want]


def chain_file(path, audit, rows, source=None):
    """Write rows (session, tool, input dict, kind, status) as a hash-chained log; a source adds a rebuild line 1."""
    entries, prev = [], audit.GENESIS
    if source is not None:
        rows = [(None, None, None, "rebuild", "rebuilt")] + list(rows)
    for seq, (session, tool, data, kind, status) in enumerate(rows, 1):
        entry = {"seq": seq, "ts": "2026-11-14T03:%02d:00.000+08:00" % seq, "session_id": session, "agent_id": None,
                 "tool": tool, "tool_use_id": "t%d" % seq if tool else None,
                 "input": audit.summary(data) if tool else "", "kind": kind, "result": {"status": status},
                 "duration_ms": None, "prev": prev}
        if kind == "rebuild":
            entry["source"] = source
        entry["hash"] = audit.digest(entry)
        prev = entry["hash"]
        entries.append(audit.canonical(entry))
    return write(path, "\n".join(entries) + "\n")


@test
def matching_221(tmp):
    audit = load_tool("audit_log")
    cut = [name for name, _, data, _, _ in RVA_221_CASES[:10] if not audit.summary(data).endswith("\u2026")]
    require(not cut, "these log lines are not cut at 500, so they test nothing: %s" % cut)
    wrong = rva_wrong(load_tool("report_vs_audit"), audit)
    require(not wrong, "report_vs_audit gets these 2.2.1 cases wrong: %s" % wrong)
    log = chain_file(tmp / "rva221.jsonl", audit,
                     [("S1", tool, data, "result", "ok") for _, tool, data, _, _ in RVA_221_CASES[:2]])
    good = write(tmp / "rva221-good.md", "SESSION_ID: S1\nRAN: " + BT + RVA_221_CASES[0][3] + BT + " exit=0\n")
    proc = run_tool("report_vs_audit", "--report", good, "--log", log)
    require(proc.returncode == 0 and "REPORT_VS_AUDIT: PASS claims=1 ok=1" in text_of(proc),
            "a cut Windows command did not match through the CLI: " + tail(text_of(proc)))
    require("rebuilt after the fact" not in text_of(proc), "a log without a rebuild line got the rebuild note")
    bad = write(tmp / "rva221-bad.md", "SESSION_ID: S1\nRAN: " + BT + RVA_221_CASES[3][3] + BT + " exit=0\n")
    proc = run_tool("report_vs_audit", "--report", bad, "--log", log)
    require(proc.returncode == 1 and "FAIL" in text_of(proc), "a wrong file name matched through the CLI: "
            + tail(text_of(proc)))
    survived = [name for name, swaps in RVA_MUTATIONS if not rva_wrong(mutated("report_vs_audit", swaps), audit)]
    require(not survived, "these matcher mutations get no case wrong, so the cases do not test them: %s" % survived)
    return "%d cases in process, 2 CLI, %d mutations killed" % (len(RVA_221_CASES), len(RVA_MUTATIONS))


def shadow_fixture(folder):
    director_fixture(folder)
    write(folder / "PO_PENDING.md",
          "## 未關閉\n\nID: OD-001\nCREATED: 2026-11-14 03:00\nSTATUS: open\nQUESTION: Which database?\n"
          "OPTIONS: a) sqlite b) none\nRECOMMENDED: a\nSOURCE: BOOTSTRAP\nANSWER:\n\n## 已關閉\n\nID: ACT-002\n"
          "CREATED: 2026-11-13 10:00\nSTATUS: answered\nQUESTION: Old question?\nOPTIONS: a) yes b) no\n"
          "RECOMMENDED: a\nSOURCE: DIRECTOR\nANSWER: yes\n")
    write(folder / "RESUME_STATE.md", "PROGRESS: setup checked\nDOING: nothing\nNEXT_STEP: wait for the PO\n"
          "COMMS: NONE\n\n# RESUME_STATE\nUPDATED: 2026-11-14 03:00 +08:00\n")
    write(folder / "director_work.json", json.dumps({
        "_comment": "selftest", "schema_version": 1, "mode": "general", "trace_id_pattern": "^(B|DD|OD)-\\d+$",
        "po_pending_files": ["PO_PENDING.md"], "po_item_pattern": "^\\s*ID\\s*:\\s*(OD|ACT)-\\w+",
        "po_open_pattern": "^\\s*STATUS\\s*:\\s*open\\b"}, indent=1) + "\n")
    return folder


# (what is broken, file, new text or a function of the old text, shadow text that must show up)
SHADOW_CASES = [
    ("an ID used twice", "PO_PENDING.md",
     lambda old: old.replace("ID: ACT-002", "ID: OD-001"), "the ID is used again"),
    ("a RESUME header value left as a placeholder", "RESUME_STATE.md",
     lambda old: old.replace("DOING: nothing", "DOING: <what>"), "RESUME_STATE: DOING"),
    ("no dated UPDATED line", "RESUME_STATE.md",
     lambda old: old.replace("UPDATED: 2026-11-14 03:00 +08:00", "UPDATED: today"), "RESUME_STATE: UPDATED"),
    ("schema_version 2", "director_work.json",
     lambda old: old.replace('"schema_version": 1', '"schema_version": 2'), "schema_version 2 is not 1"),
    ("an unknown mode", "director_work.json",
     lambda old: old.replace('"mode": "general"', '"mode": "expert"'), "mode: general / beginner"),
    ("a broken regular expression", "director_work.json",
     lambda old: old.replace('"trace_id_pattern": "^(B|DD|OD)-\\\\d+$"', '"trace_id_pattern": "^(B|DD"'),
     "trace_id_pattern: not a valid regular expression"),
    ("po_pending_files as one string", "director_work.json",
     lambda old: old.replace('[\n  "PO_PENDING.md"\n ]', '"PO_PENDING.md"'), "po_pending_files: a list")]


@test
def setup_shadow(tmp):
    clean = shadow_fixture(tmp / "shadow-clean" / "DIRECTOR")
    proc = run_tool("dsh_setup_check", "--strict", clean)
    require(proc.returncode == 0 and "DSH_SETUP_CHECK: PASS" in text_of(proc) and "shadow:" not in text_of(proc),
            "a clean folder did not pass --strict: " + tail(text_of(proc)))
    for number, (name, file_name, change, said) in enumerate(SHADOW_CASES):
        folder = shadow_fixture(tmp / ("shadow-%d" % number) / "DIRECTOR")
        old = (folder / file_name).read_text(encoding="utf-8")
        new = change(old)
        require(new != old, "%s: the fixture change did nothing" % name)
        write(folder / file_name, new)
        soft = run_tool("dsh_setup_check", folder)
        require(soft.returncode == 0 and ("~ shadow: " in text_of(soft)) and said in text_of(soft),
                "%s: without --strict expected exit 0 and a shadow line with %r: %s" % (name, said, tail(text_of(soft))))
        hard = run_tool("dsh_setup_check", "--strict", folder)
        require(hard.returncode == 1 and ("  - " in text_of(hard)) and said in text_of(hard)
                and "DSH_SETUP_CHECK: FAIL" in text_of(hard),
                "%s: with --strict expected exit 1 and a problem with %r: %s" % (name, said, tail(text_of(hard))))
    notes = shadow_fixture(tmp / "shadow-notes" / "DIRECTOR")
    data = json.loads((notes / "director_work.json").read_text(encoding="utf-8"))
    data.update(window=250000, colour="blue")
    write(notes / "director_work.json", json.dumps(data, indent=1) + "\n")
    write(notes / "PO_PENDING.md", (notes / "PO_PENDING.md").read_text(encoding="utf-8")
          .replace("CREATED: 2026-11-13 10:00\n", "") + "\nID: CH-003\nSTATUS: open\n")
    proc = run_tool("dsh_setup_check", "--strict", notes)
    text = text_of(proc)
    for said in ("Claude-only keys the DSH edition does not read: window", "keys no tool reads: colour",
                 "ACT-002 (line", "no CREATED line", "`ID: CH-003` is not OD-xx / ACT-xx"):
        require(said in text, "expected the note %r: %s" % (said, tail(text)))
    require(proc.returncode == 0, "notes alone failed --strict: " + tail(text))
    return "clean PASS --strict, %d cases shadow then FAIL --strict, 5 notes" % len(SHADOW_CASES)


@test
def audit_rebuild(tmp):
    module = load_tool("dsh_audit")
    audit = load_tool("audit_log")
    require(module.BUILD_VERSION == 2, "dsh_audit BUILD_VERSION is %r, not 2" % module.BUILD_VERSION)
    entries = []
    for number, command in enumerate(("git status", RVA_CLOSED), 1):
        entries.append({"ts": "2026-11-14T03:0%d:00.000+08:00" % number, "session_id": "dsh-s1", "agent_id": "w1",
                        "tool": "PowerShell", "tool_use_id": "c%d" % number, "kind": "result",
                        "input": audit.summary({"command": command}), "result": {"status": "ok"}, "duration_ms": 5})
    source = {"by": "dsh_audit.py", "version": module.BUILD_VERSION,
              "sessions": [{"session_id": "dsh-s1", "log": "session.v4.jsonl.zstd", "sha256": "0" * 64, "bytes": 1}],
              "lines": len(entries), "warnings": 0, "skipped": 0}
    lines, head = module.chain_lines(entries, source, now="2026-11-14T03:10:00.000+08:00")
    log = write(tmp / "rebuilt.jsonl", "".join(lines))
    first = json.loads(lines[0])
    require(first.get("kind") == "rebuild" and first.get("seq") == 1 and first.get("source") == source
            and first.get("prev") == audit.GENESIS and first.get("session_id") is None,
            "line 1 is not the rebuild line: " + tail(lines[0], 300))
    require(len(lines) == 3 and json.loads(lines[-1]).get("hash") == head and json.loads(lines[1]).get("seq") == 2,
            "the tool calls are not chained from seq 2 up to the returned head")
    verify = run_tool("dsh_audit", "verify", "--log", log)
    require(verify.returncode == 0 and "OK" in text_of(verify),
            "dsh_audit verify of a rebuilt chain exit %s: %s" % (verify.returncode, tail(text_of(verify))))
    report = write(tmp / "rebuilt.md", "SESSION_ID: dsh-s1\nRAN: " + BT + RVA_CLOSED + BT + " exit=0\n")
    check = run_tool("report_vs_audit", "--report", report, "--log", log)
    require(check.returncode == 0 and "REPORT_VS_AUDIT: PASS claims=1 ok=1" in text_of(check)
            and "~ note: a log was rebuilt after the fact (dsh_audit.py)" in text_of(check),
            "report_vs_audit on the rebuilt log: " + tail(text_of(check)))
    edited = "".join(lines).replace("git status", "git push")
    require(edited != "".join(lines), "the edit for the broken-chain case changed nothing")
    broken = write(tmp / "broken.jsonl", edited)
    bad = run_tool("dsh_audit", "verify", "--log", broken)
    require(bad.returncode != 0, "dsh_audit verify accepted an edited line")
    return "rebuild line 1, verify OK, edited line refused, report note shown"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verbose", action="store_true", help="print full detail for passing tests too")
    parser.add_argument("--keep", action="store_true", help="keep the temp folder (printed at the end)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="dw-selftest-"))
    passed = failed = skipped = 0
    try:
        for function in TESTS:
            name = function.__name__
            started = time.time()
            try:
                detail = function(tmp)
                passed += 1
                line = "PASS %-22s %5.2fs  %s" % (name, time.time() - started, detail or "")
                if not args.verbose:
                    line = "PASS %-22s %5.2fs" % (name, time.time() - started)
            except Skip as error:
                skipped += 1
                line = "SKIP %-22s %s" % (name, error)
            except AssertionError as error:
                failed += 1
                line = "FAIL %-22s %s" % (name, error)
            except Exception as error:
                failed += 1
                line = "FAIL %-22s %s: %s" % (name, type(error).__name__, error)
            print(line)
    finally:
        if args.keep:
            print("temp: " + str(tmp))
        else:
            shutil.rmtree(tmp, ignore_errors=True)
    total = passed + failed + skipped
    print("SELFTEST_DS: %s tests=%d pass=%d fail=%d skip=%d" %
          ("PASS" if failed == 0 else "FAIL", total, passed, failed, skipped))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
