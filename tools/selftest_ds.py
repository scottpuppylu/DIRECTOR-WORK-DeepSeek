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
  sdd_*       ds.2 SDD gate through gate_check.py / scope_check.py with a stand-in openspec CLI (OPENSPEC_BIN=<.py>):
              a valid Standard order passes; SPEC_CHANGE = NONE on Standard, a change that fails validate, a missing
              CLI, an edited locked test, STOP_RULES over 1 round, a changed approved plan, a missing SPEC_REVIEW /
              PLAN_APPROVED line and 4 changed files all FAIL. sdd_real_openspec runs the real CLI (SKIP when
              neither OPENSPEC_BIN nor PATH has one)

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
             "metrics_report", "memory_size_check", "secret_mask", "pause_ctl", "audit_log", "sdd_gate")
TESTS = []


class Skip(Exception):
    """The test cannot run here (missing optional dependency, no DSH data); not a failure."""


def test(function):
    TESTS.append(function)
    return function


def run_tool(name, *args, cwd=None, env=None):
    return subprocess.run(PY_ARGS + [str(TOOLS / (name + ".py"))] + [str(a) for a in args],
                          cwd=str(cwd) if cwd else None, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=TIMEOUT,
                          env=dict(os.environ, **env) if env else None)


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
    session = entries[0].get("session_id")
    require(session, "the first audit line has no session_id")
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


# ds.2 SDD gate (sdd_gate.py through gate_check.py / scope_check.py). A stand-in openspec CLI (a .py file named by
# OPENSPEC_BIN) answers `validate` so the glue is tested on any machine; sdd_real_openspec uses the real CLI when found.
FAKE_OPENSPEC = '''import json, sys
args = sys.argv[1:]
if args[:1] == ["--version"]:
    print("0.0.0-selftest-stand-in"); sys.exit(0)
name = args[1] if len(args) > 1 else ""
ok = name == "good-change"
issues = [] if ok else [{"level": "ERROR", "path": "file", "message": "Change must have at least one delta."}]
print(json.dumps({"items": [{"id": name, "type": "change", "valid": ok, "issues": issues}],
                  "summary": {"totals": {"items": 1, "passed": int(ok), "failed": int(not ok)}}}))
sys.exit(0 if ok else 1)
'''
SDD_TEST = "import unittest\n\nclass T(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(1 + 1, 2)\n"


def sdd_order(spec, tests, governance="Standard", stop="1"):
    return "\n".join([
        "# WO-7 — sdd selftest", "**selftest order**", "", "```text",
        "ISSUED_BY      = 總監 2026-11-14 09:00", "REVISION       = 1", "TRACES_TO      = NONE",
        "PRIMARY_WORKER = 子代理「w1」", "MODEL / EFFORT = deepseek-flash / high", "FALLBACK       = 同名子代理續談",
        f"GOVERNANCE     = {governance}", "BASE_REF       = main @ abc1234", f"SPEC_CHANGE    = {spec}", "```", "",
        "```text", "SCOPE:", "- calc.py", "FORBIDDEN:", "- NONE", "```", "",
        "```text", "TESTS_LOCKED:", f"- {tests}", "```", "",
        "| ID | 類型 | 要求 | 驗證方法 | 預期 |", "|---|---|---|---|---|",
        "| AC-1 | AUTO | add returns the sum | python -m unittest test_calc | exit 0 |", "",
        "- DELIVERABLES: one commit", f"- STOP_RULES: 同一根因 {stop} 輪沒進展就停", ""])


def sdd_fixture(tmp, name):
    """A project folder with openspec/changes/{good,bad}-change, a locked test, a stand-in CLI and an order writer."""
    repo = tmp / name
    for change in ("good-change", "bad-change"):
        write(repo / "openspec" / "changes" / change / ".openspec.yaml", "schema: spec-driven\n")
    test_file = write(repo / "test_calc.py", SDD_TEST)
    lock = "test_calc.py sha256=" + hashlib.sha256(test_file.read_bytes()).hexdigest()
    fake = write(tmp / (name + "_fake_openspec.py"), FAKE_OPENSPEC)
    return repo, lock, {"OPENSPEC_BIN": str(fake)}


def sdd_run(repo, order_text, env, *extra):
    order = write(repo / "orders" / "WO-7.md", order_text)
    proc = run_tool("gate_check", "--order", order, "--repo", repo, *extra, env=env)
    return proc, text_of(proc)


@test
def sdd_spec_ok(tmp):
    repo, lock, env = sdd_fixture(tmp, "sdd_ok")
    proc, text = sdd_run(repo, sdd_order("openspec/changes/good-change", lock), env)
    require(proc.returncode == 0 and "OK   order" in text, "a valid Standard order did not pass: " + tail(text))
    return "Standard + SPEC_CHANGE + locked test + validate OK"


@test
def sdd_no_spec_change(tmp):
    repo, lock, env = sdd_fixture(tmp, "sdd_none")
    proc, text = sdd_run(repo, sdd_order("NONE", lock), env)
    require(proc.returncode == 1 and "SPEC_CHANGE: a Standard order" in text,
            "a Standard order with SPEC_CHANGE = NONE did not FAIL clearly: " + tail(text))
    direct, dtext = sdd_run(repo, sdd_order("NONE", lock, governance="Direct"), env)
    require("SPEC_CHANGE" not in dtext, "a Direct order was asked for SPEC_CHANGE: " + tail(dtext))
    return "NONE on Standard FAILs; Direct is not asked"


@test
def sdd_validate_fails(tmp):
    repo, lock, env = sdd_fixture(tmp, "sdd_bad")
    proc, text = sdd_run(repo, sdd_order("openspec/changes/bad-change", lock), env)
    require(proc.returncode == 1 and "openspec validate bad-change --strict --json` failed" in text,
            "a change that fails validate did not FAIL: " + tail(text))
    gone, gtext = sdd_run(repo, sdd_order("openspec/changes/no-such-change", lock), env)
    require(gone.returncode == 1 and "not found under" in gtext, "a missing change folder did not FAIL: " + tail(gtext))
    return "validate failure FAILs; missing folder FAILs"


@test
def sdd_no_cli(tmp):
    repo, lock, env = sdd_fixture(tmp, "sdd_nocli")
    env = {"OPENSPEC_BIN": str(tmp / "no-such-dir" / "openspec.cmd")}
    proc, text = sdd_run(repo, sdd_order("openspec/changes/good-change", lock), env)
    require(proc.returncode == 1 and "openspec CLI not found" in text and "NOT validated" in text
            and "install" in text, "a missing openspec CLI did not FAIL with an install hint: " + tail(text))
    return "missing CLI FAILs with an install hint"


@test
def sdd_tests_locked(tmp):
    repo, lock, env = sdd_fixture(tmp, "sdd_tests")
    write(repo / "test_calc.py", SDD_TEST + "    def test_more(self):\n        pass\n")
    proc, text = sdd_run(repo, sdd_order("openspec/changes/good-change", lock), env)
    require(proc.returncode == 1 and "test_calc.py changed since it was locked" in text,
            "an edited locked test did not FAIL: " + tail(text))
    stop, stext = sdd_run(repo, sdd_order("openspec/changes/good-change", "NONE", stop="2"), env)
    require(stop.returncode == 1 and "STOP_RULES: allows 2 rounds" in stext, "STOP_RULES 2 輪 did not FAIL: " + tail(stext))
    config = write(repo / "director_work.json", json.dumps({"schema_version": 1, "sdd": {"stop_after_rounds": 2}}))
    relaxed, rtext = sdd_run(repo, sdd_order("openspec/changes/good-change", "NONE", stop="2"), env, "--config", config)
    require(relaxed.returncode == 0, "sdd.stop_after_rounds=2 did not relax the rule: " + tail(rtext))
    return "edited test FAILs; STOP_RULES 2 輪 FAILs; switch relaxes it"


@test
def sdd_plan_and_review(tmp):
    sdd = load_tool("sdd_gate")
    repo, lock, env = sdd_fixture(tmp, "sdd_plan")
    tasks = write(repo / "openspec" / "changes" / "good-change" / "tasks.md", "## 1. Code\n\n- [ ] 1.1 Add subtract\n")
    order = sdd_order("openspec/changes/good-change", lock)
    approved = sdd.plan_hash(tasks)
    log = f"2026-11-14 09:00 | SPEC_REVIEW WO-7 tokens=UNKNOWN issues=0/0/0 adopted=0\nPLAN_APPROVED WO-7 sha={approved}\n"
    config = dict(sdd.DEFAULTS)
    unticked = sdd.match_problems(order, ["WO-7"], log, repo, config, [])
    require(any("not ticked" in p for p in unticked), "a hand-in with an unticked task was not caught: %s" % unticked)
    write(tasks, "## 1. Code\n\n- [x] 1.1 Add subtract\n")
    require(sdd.match_problems(order, ["WO-7"], log, repo, config, []) == [], "approved plan + review was refused")
    write(tasks, "## 1. Code\n\n- [x] 1.1 Add subtract\n- [x] 1.2 Also refactor everything\n")
    changed = sdd.match_problems(order, ["WO-7"], log, repo, config, [])
    require(any("differs from the approved plan" in p for p in changed), "an added task was not caught: %s" % changed)
    missing = sdd.match_problems(order, ["WO-7"], "DISPATCH WO-7 rev=1 sha=" + "0" * 64 + "\n", repo, config, [])
    require(any(p.startswith("SPEC_REVIEW") for p in missing) and any(p.startswith("PLAN_APPROVED") for p in missing),
            "a log without SPEC_REVIEW / PLAN_APPROVED was not caught: %s" % missing)
    return "unticked task FAILs; ticks keep the plan hash; changed plan FAILs; missing log lines FAIL"


@test
def sdd_oversize(tmp):
    if shutil.which("git") is None:
        raise Skip("git is not on PATH")
    repo = tmp / "sdd_size"
    repo.mkdir()
    write(repo / "calc.py", "x = 1\n")
    for args in (["git", "init", "-q", "-b", "main"], ["git", "config", "user.email", "selftest@example.invalid"],
                 ["git", "config", "user.name", "Selftest"], ["git", "config", "core.autocrlf", "false"],
                 ["git", "add", "calc.py"], ["git", "commit", "-q", "-m", "init"]):
        proc = run_prog(args, cwd=repo)
        require(proc.returncode == 0, " ".join(args) + " failed: " + tail(text_of(proc)))
    order = write(tmp / "sdd_size_order" / "WO-7.md", sdd_order("NONE", "NONE").replace("- calc.py", "- src/**\n- openspec/**"))
    for n in range(4):
        write(repo / "src" / f"m{n}.py", "a = 1\n")
    write(repo / "openspec" / "changes" / "x" / "tasks.md", "- [ ] 1.1 not counted\n")
    proc = run_tool("scope_check", "--order", order, "--repo", repo, "--base", "main")
    text = text_of(proc)
    require(proc.returncode == 1 and "OVERSIZE" in text and "files=4/3" in text, "4 changed files did not FAIL: " + tail(text))
    (repo / "src" / "m3.py").unlink()
    proc = run_tool("scope_check", "--order", order, "--repo", repo, "--base", "main")
    require(proc.returncode == 0 and "SIZE: files=3" in text_of(proc), "3 files did not pass: " + tail(text_of(proc)))
    return "4 files OVERSIZE, 3 files PASS, openspec/ not counted"


@test
def sdd_real_openspec(tmp):
    sdd = load_tool("sdd_gate")
    command, how = sdd.find_cli(dict(sdd.DEFAULTS))
    if command is None or how.endswith("stand-in)"):
        raise Skip("no real openspec CLI (%s); set OPENSPEC_BIN or put openspec on PATH" % how)
    repo = tmp / "sdd_real"
    change = repo / "openspec" / "changes" / "add-subtract"
    write(repo / "openspec" / "config.yaml", "schema: spec-driven\n")
    write(change / ".openspec.yaml", "schema: spec-driven\n")
    write(change / "proposal.md", "## Why\nNeed subtraction.\n\n## What Changes\n- Add subtract.\n")
    spec = "## ADDED Requirements\n\n### Requirement: Subtract\nThe calculator SHALL subtract b from a.\n\n"
    write(change / "specs" / "calc" / "spec.md", spec + "#### Scenario: basic\n- **WHEN** subtract(5, 3)\n- **THEN** 2\n")
    write(change / "tasks.md", "## 1. Code\n\n- [ ] 1.1 Add subtract\n")
    write(repo / "test_calc.py", SDD_TEST)
    lock = "test_calc.py sha256=" + hashlib.sha256((repo / "test_calc.py").read_bytes()).hexdigest()
    proc, text = sdd_run(repo, sdd_order("openspec/changes/add-subtract", lock), None)
    require(proc.returncode == 0, "a valid change failed the real openspec validate: " + tail(text))
    write(change / "specs" / "calc" / "spec.md", spec)  # no scenario: --strict must refuse it
    bad, btext = sdd_run(repo, sdd_order("openspec/changes/add-subtract", lock), None)
    require(bad.returncode == 1 and "--strict --json` failed" in btext, "a requirement without a scenario passed: " + tail(btext))
    return "real CLI (%s): valid change OK, scenario-less change FAIL" % how


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
