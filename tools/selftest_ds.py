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
  release_state 2.2.2-ds.3: release.py dry run on temp bare repos: BEHIND and DIVERGED stop, --merge predicts the
              conflicted file, AHEAD plans push / tag / release, a version below a remote tag and a VERSION that
              differs from the CHANGELOG top stop; version_key orders 2.2.0-ds.2 below 2.2.1-ds.1; a -ds.N
              not above every remote tag's -ds.N stops (1.1.0-ds.1 after v1.0.0-ds.2), 1.1.0-ds.3 passes; a
              VERSION changed in the working tree but not committed stops before anything else (any modified
              tracked file stops a dry run too; the version is read from HEAD)
  release_scan  2.2.2-ds.3: release.py public scan stops an API key, a key = value secret, a private email, a
              <drive>:/Users path, DIRECTOR/ / _work/ / session files and a private author email, never prints a secret;
              noreply / .invalid emails and DIRECTOR/ named in text pass
  base_ref_fresh 2.2.2-ds.3: gate_check --order fetches and compares BASE_REF with origin/main in a temp clone:
              up to date is confirmed, 1 behind is a WARN note (--strict-base: FAIL), a missing commit is noted,
              a failed fetch says it did not compare (--strict-base: FAIL)
  verify_dsh_run_unit 2.2.2-ds.3: tools/test_verify_dsh_run.py: the 11 D08 peek cases of WO-101, config / order
              settings, a synthetic project run (--no-dsh) with a clean, a test-editing and a wrong worker branch,
              and the D13 step markers (acceptance is not a --help read, verdict / summary found by file name)
  report_skeleton 2.2.2-ds.3: gate_check --report-skeleton fills the order's fields, hash and one row per AC; left
              unfilled it fails --report; filled with the evidence its printed commands record, it passes --match
  release_execute 2.2.2-ds.3: release.py --merge --execute on a temp bare origin: merge --no-ff into release/<v>,
              push and tag verified with ls-remote, the release step stops on a non-GitHub remote, a rerun skips
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
import re
import shlex
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
             "metrics_report", "memory_size_check", "secret_mask", "pause_ctl", "audit_log", "sdd_gate", "release",
             "verify_dsh_run")
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


def rgit(repo, *args):
    proc = run_prog(["git", "-C", repo] + list(args))
    require(proc.returncode == 0, "git %s: %s" % (" ".join(map(str, args)), tail(text_of(proc))))
    return proc.stdout.strip()


def release_clone(origin, folder, email="selftest@example.invalid"):
    rgit(folder.parent, "clone", "-q", "-c", "core.autocrlf=false", origin, folder.name)  # before checkout: LF stays LF
    rgit(folder, "config", "user.email", email)
    rgit(folder, "config", "user.name", "selftest")
    return folder


def release_commit(work, version, files=None, top=None):
    """A release commit: VERSION, a CHANGELOG with <top or version> on top, and any extra files."""
    write(work / "VERSION", version + "\n")
    write(work / "CHANGELOG.md", "# CHANGELOG\n\n## %s（2026-11-14）\n\n- notes for %s\n\n## 1.0.0\n\n- first\n"
          % (top or version, version))
    for name, text in (files or {}).items():
        write(work / name, text)
    rgit(work, "add", "-A")
    rgit(work, "commit", "-q", "-m", "release " + version)


def release_origin(tmp, name):
    """A bare origin with main at 1.0.0 and tag v1.0.0, a config whose selftest is trivial, and a first clone."""
    base = tmp / name
    base.mkdir(parents=True)
    rgit(base, "init", "-q", "--bare", "-b", "main", "origin.git")
    origin = base / "origin.git"
    seed = release_clone(origin, base / "seed")
    write(seed / "a.txt", "base\n")
    release_commit(seed, "1.0.0")
    rgit(seed, "push", "-q", "origin", "HEAD:refs/heads/main")
    rgit(seed, "tag", "-a", "v1.0.0", "-m", "v1.0.0")
    rgit(seed, "push", "-q", "origin", "refs/tags/v1.0.0")
    config = write(base / "director_work.json", json.dumps({"release": {"selftest": "python -I -c pass"}}) + "\n")
    return origin, base, config


@test
def release_state(tmp):
    module = load_tool("release")
    key = module.version_key
    require(key("2.2.0-ds.2") < key("v2.2.1-ds.1") < key("2.2.1-ds.2") < key("2.2.1") < key("2.10.0-ds.1"),
            "release.version_key orders 2.2.0-ds.2 / 2.2.1-ds.1 / 2.2.1-ds.2 / 2.2.1 / 2.10.0-ds.1 wrong")
    origin, base, config = release_origin(tmp, "rel-state")
    late = release_clone(origin, base / "late")  # cloned before the remote moves on: BEHIND, then DIVERGED
    other = release_clone(origin, base / "other")
    write(other / "a.txt", "theirs\n")
    rgit(other, "commit", "-q", "-am", "remote work")
    rgit(other, "push", "-q", "origin", "HEAD:refs/heads/main")

    def release(work, *extra):
        proc = run_tool("release", "--repo", work, "--config", config, *extra)
        return proc.returncode, text_of(proc)

    code, out = release(late)
    require(code == 1 and "BEHIND 1" in out and "NEXT: git merge --ff-only" in out and "RELEASE: FAIL" in out,
            "a branch behind origin/main was not stopped as BEHIND: " + tail(out))
    release_commit(late, "1.1.0", {"a.txt": "mine\n"})
    code, out = release(late)
    require(code == 1 and "DIVERGED ahead 1 / behind 1" in out and "--merge" in out,
            "a diverged branch without --merge was not stopped as DIVERGED: " + tail(out))
    code, out = release(late, "--merge")
    require(code == 0 and "STEP state: PLAN DIVERGED" in out and "1 conflicted file(s): a.txt" in out
            and "PLAN git switch -c release/1.1.0" in out, "--merge dry run did not predict the a.txt conflict: " + tail(out))
    ahead = release_clone(origin, base / "ahead")
    release_commit(ahead, "1.1.0")
    code, out = release(ahead)
    require(code == 0 and "AHEAD 1" in out and "PLAN git push origin HEAD:refs/heads/main" in out
            and "PLAN git tag -a v1.1.0" in out and "RELEASE: DRY_RUN 3 remote step(s)" in out,
            "a branch ahead of origin/main did not plan push, tag and release: " + tail(out))
    low = release_clone(origin, base / "low")
    release_commit(low, "0.9.0-ds.5")
    code, out = release(low)
    require(code == 1 and "does not sort above the remote tag(s) v1.0.0" in out,
            "a version below a remote tag was not stopped: " + tail(out))
    # VERSION bumped in the working tree but not committed: HEAD says 1.1.0, the tag would say 1.2.0 -> stop
    loose = release_clone(origin, base / "loose")
    release_commit(loose, "1.1.0")
    write(loose / "VERSION", "1.2.0\n")
    code, out = release(loose)
    require(code == 1 and "VERSION differ(s) from HEAD (uncommitted); HEAD says 1.1.0" in out
            and "NEXT: commit them" in out and "STEP version: OK" not in out and "STEP state" not in out,
            "an uncommitted VERSION different from HEAD was not stopped: " + tail(out))
    mismatch = release_clone(origin, base / "mismatch")
    release_commit(mismatch, "1.2.0", top="1.1.0")
    code, out = release(mismatch)
    require(code == 1 and "VERSION is 1.2.0 but the first CHANGELOG.md heading is 1.1.0" in out,
            "VERSION different from the CHANGELOG top was not stopped: " + tail(out))
    # the -ds.N serial: after v1.0.0-ds.2, 1.1.0-ds.1 stops although 1.1.0 is a higher base; 1.1.0-ds.3 passes
    rgit(other, "tag", "-a", "v1.0.0-ds.2", "-m", "v1.0.0-ds.2")
    rgit(other, "push", "-q", "origin", "refs/tags/v1.0.0-ds.2")
    restart = release_clone(origin, base / "restart")
    release_commit(restart, "1.1.0-ds.1")
    code, out = release(restart)
    require(code == 1 and "-ds.1 is not above the -ds.N of the remote tag(s) v1.0.0-ds.2" in out
            and "use -ds.3" in out, "a -ds.N serial that restarted was not stopped: " + tail(out))
    serial = release_clone(origin, base / "serial")
    release_commit(serial, "1.1.0-ds.3")
    code, out = release(serial)
    require(code == 0 and "STEP version: OK 1.1.0-ds.3" in out, "a -ds.N above every remote one was stopped: " + tail(out))
    return "BEHIND, DIVERGED (+ --merge conflict a.txt), AHEAD, version order, -ds.N serial, uncommitted VERSION and CHANGELOG mismatch"


@test
def release_execute(tmp):
    origin, base, config = release_origin(tmp, "rel-exec")
    late = release_clone(origin, base / "late")
    other = release_clone(origin, base / "other")
    write(other / "b.txt", "theirs\n")
    rgit(other, "add", "b.txt")
    rgit(other, "commit", "-q", "-m", "remote work")
    rgit(other, "push", "-q", "origin", "HEAD:refs/heads/main")
    release_commit(late, "1.1.0")
    proc = run_tool("release", "--repo", late, "--config", config, "--merge", "--execute")
    out = text_of(proc)
    head = rgit(late, "rev-parse", "HEAD")
    require("merged into release/1.1.0" in out and rgit(late, "rev-parse", "--abbrev-ref", "HEAD") == "release/1.1.0",
            "--merge --execute did not merge into release/1.1.0: " + tail(out))
    require(len(rgit(late, "rev-list", "--parents", "-n", "1", "HEAD").split()) == 3, "the release merge is not --no-ff")
    require("STEP push: OK ls-remote main = " + head in out and "STEP tag: OK v1.1.0^{} = " + head in out,
            "push / tag did not verify with ls-remote: " + tail(out))
    require(proc.returncode == 1 and "cannot tell the GitHub repository" in out,
            "the release step on a non-GitHub remote did not stop with a clear reason: " + tail(out))
    require(rgit(origin, "rev-parse", "main") == head and rgit(origin, "rev-parse", "v1.1.0^{commit}") == head,
            "the bare origin does not have main and v1.1.0 at the merge")
    again = text_of(run_tool("release", "--repo", late, "--config", config, "--execute"))
    require("STEP push: SKIP" in again and "STEP tag: SKIP" in again and "UP_TO_DATE" in again,
            "a rerun did not skip what was already done: " + tail(again))
    return "merge --no-ff into release/1.1.0, push and tag verified, rerun skips them"


@test
def base_ref_fresh(tmp):
    base = tmp / "bref"
    base.mkdir(parents=True)
    rgit(base, "init", "-q", "--bare", "-b", "main", "origin.git")
    proj = release_clone(base / "origin.git", base / "proj")
    repo, lock, env = sdd_fixture(base, "proj")
    rgit(proj, "add", "-A")
    rgit(proj, "commit", "-q", "-m", "base")
    rgit(proj, "push", "-q", "origin", "HEAD:refs/heads/main")
    sha = rgit(proj, "rev-parse", "--short=7", "HEAD")

    def order(ref):
        return sdd_order("openspec/changes/good-change", lock).replace("BASE_REF       = main @ abc1234",
                                                                        "BASE_REF       = " + ref)

    proc, text = sdd_run(repo, order("origin/main @ " + sha), env)
    require(proc.returncode == 0 and "BASE_REF %s = origin/main (fetched now)" % sha in text,
            "an up-to-date BASE_REF was not confirmed after a fetch: " + tail(text))
    other = release_clone(base / "origin.git", base / "other")
    write(other / "later.txt", "x\n")
    rgit(other, "add", "later.txt")
    rgit(other, "commit", "-q", "-m", "later")
    rgit(other, "push", "-q", "origin", "HEAD:refs/heads/main")
    proc, text = sdd_run(repo, order("origin/main @ " + sha), env)
    require(proc.returncode == 0 and "~ WARN BASE_REF: %s is 1 commit(s) behind origin/main" % sha in text,
            "a BASE_REF behind origin/main was not a WARN note: " + tail(text))
    proc, text = sdd_run(repo, order("origin/main @ " + sha), env, "--strict-base")
    require(proc.returncode == 1 and "  - BASE_REF: %s is 1 commit(s) behind" % sha in text,
            "--strict-base did not fail a stale BASE_REF: " + tail(text))
    proc, text = sdd_run(repo, order("origin/main @ deadbee"), env)
    require(proc.returncode == 0 and "WARN BASE_REF: commit deadbee does not exist" in text,
            "a BASE_REF commit that does not exist was not noted: " + tail(text))
    rgit(proj, "remote", "set-url", "origin", str(base / "gone.git"))
    proc, text = sdd_run(repo, order("origin/main @ " + sha), env)
    require(proc.returncode == 0 and "WARN BASE_REF: not compared with the remote: git fetch origin failed" in text,
            "a failed fetch was not said out loud: " + tail(text))
    proc, text = sdd_run(repo, order("origin/main @ " + sha), env, "--strict-base")
    require(proc.returncode == 1 and "  - BASE_REF: not compared with the remote" in text,
            "--strict-base did not fail when the fetch failed: " + tail(text))
    return "fresh = origin/main, 1 behind WARN / --strict-base FAIL, missing commit, fetch failure WARN / FAIL"


@test
def release_scan(tmp):
    origin, base, config = release_origin(tmp, "rel-scan")
    work = release_clone(origin, base / "work")
    secret = "sk-" + "A1b2" * 6
    cases = [  # (name, files, author email, text that must show up)
        ("api key", {"conf.py": 'KEY = "%s"\n' % secret}, None, "openai_key"),
        ("key = value secret", {"conf.ini": "api_key = " + "Zx9q" * 4 + "\n"}, None, "secret_assignment"),
        ("private email", {"README.md": "mail alice@" + "example.com\n"}, None, "email alice@" + "example.com"),
        ("user path", {"notes.md": "see C:" + "/Users/alice/notes.txt\n"}, None, "user_path"),
        ("DIRECTOR file", {"DIRECTOR/RESUME_STATE.md": "x\n"}, None, "a DIRECTOR/ file"),
        ("_work file", {"_work/x/out.txt": "x\n"}, None, "a _work/ file"),
        ("session file", {"logs/session.v4.jsonl.zstd": "x\n"}, None, "a DSH session file"),
        ("author email", {"b.txt": "x\n"}, "bob@" + "example.com", "author: email bob@" + "example.com")]
    for number, (name, files, email, said) in enumerate(cases):
        rgit(work, "switch", "-q", "-c", "case-%d" % number, "origin/main")
        rgit(work, "config", "user.email", email or "selftest@example.invalid")
        release_commit(work, "1.1.0", files)
        proc = run_tool("release", "--repo", work, "--config", config)
        out = text_of(proc)
        require(proc.returncode == 1 and "STEP FAIL:" in out and "must not go public" in out and said in out,
                "%s: the public scan did not stop it with %r: %s" % (name, said, tail(out)))
        require(secret not in out and "Zx9q" * 4 not in out, "%s: the scan printed a secret value" % name)
    rgit(work, "switch", "-q", "-c", "clean", "origin/main")
    rgit(work, "config", "user.email", "selftest@example.invalid")
    release_commit(work, "1.1.0", {"README.md": "mail 1+me@users.noreply.github.com or me@example.invalid; "
                                               "DIRECTOR/RESUME_STATE.md is named in docs\n"})
    proc = run_tool("release", "--repo", work, "--config", config)
    require(proc.returncode == 0 and "STEP scan: OK" in text_of(proc),
            "a clean change (noreply / .invalid emails, DIRECTOR/ only named in text) did not pass: " + tail(text_of(proc)))
    return "%d private kinds stopped, no secret printed, clean change passes" % len(cases)


@test
def report_skeleton(tmp):
    """ds.3 token saving: gate_check --report-skeleton fills what the order fixes; left as is it fails --report; filled
    in with the evidence its own printed commands record, it passes --match (and its scope_check command passes)."""
    python = shutil.which("python")
    if shutil.which("git") is None or python is None:
        raise Skip("git or python is not on PATH")
    root = tmp / "skeleton"
    repo = root / "demo"
    write(repo / "calc.py", "def add(a, b):\n    return 0\n")
    write(repo / "test_calc.py", "import unittest\nfrom calc import add\n\n\nclass T(unittest.TestCase):\n"
          "    def test_add(self):\n        self.assertEqual(add(1, 2), 3)\n")
    rgit(repo, "init", "-q")
    rgit(repo, "config", "user.email", "selftest@example.invalid")
    rgit(repo, "config", "user.name", "Selftest")
    rgit(repo, "config", "core.autocrlf", "false")
    rgit(repo, "add", "-A")
    rgit(repo, "commit", "-q", "-m", "base")
    base = rgit(repo, "rev-parse", "HEAD")
    check = ["python", "-B", "-I", "-m", "unittest", "discover", "-s", ".", "-p", "test_*.py"]
    order = write(root / "DIRECTOR" / "orders" / "WO-8-add.md", "\n".join([
        "# WO-8 — skeleton selftest", "**fix add**", "", "```text",
        "ISSUED_BY      = 總監 2026-11-14 09:00", "REVISION       = 1", "TRACES_TO      = NONE",
        "PRIMARY_WORKER = 子代理「w8」（DSH）", "MODEL / EFFORT = deepseek-flash / high（理由：小改動）",
        "FALLBACK       = 同名子代理續談", "GOVERNANCE     = Standard", f"BASE_REF       = main @ {base}",
        "```", "", "```text", "SCOPE:", "- calc.py", "FORBIDDEN:", "- test_calc.py", "```", "",
        "| ID | 類型 | 要求 | 驗證方法 | 預期 |", "|---|---|---|---|---|",
        "| AC-1 | AUTO | add returns the sum | `python -B -I -m unittest discover -s . -p \"test_*.py\"` | exit 0 |",
        "| AC-2 | REVIEW | the code reads well | 總監看 diff | 好讀 |", "",
        "```text", "CHECKS:", "- AC-1: " + json.dumps(check), "```", "",
        "- DELIVERABLES: one commit", "- STOP_RULES: 同一根因 1 輪沒進展就停", ""]))
    # this test is about the report, not SDD: the order's folder config turns the spec and locked-test rules off
    write(root / "DIRECTOR" / "director_work.json",
          json.dumps({"schema_version": 1, "sdd": {"require_spec_for_standard": False, "tests_first": False}}) + "\n")
    write(repo / "calc.py", "def add(a, b):\n    return a + b\n")
    rgit(repo, "commit", "-q", "-am", "WO-8: add returns the sum")
    head = rgit(repo, "rev-parse", "HEAD")
    report = root / "DIRECTOR" / "reports" / "WO-8_TASK_REPORT.md"
    proc = run_tool("gate_check", "--report-skeleton", order, "--repo", repo, "--out", report)
    out = text_of(proc)
    require(proc.returncode == 0 and report.is_file(), "skeleton not written: " + tail(out))
    skeleton = report.read_text(encoding="utf-8")
    for want in ("WO-8 / w8 / deepseek-flash (EFFORT high) / ", f"/ {base} / <HEAD 40 位>", "ORDER: WO-8-add.md REVISION 1",
                 "| AC-1 | <實際結果> | <evidence .json 檔名> | <PASS / FAIL / BLOCKED / UNVERIFIED> |",
                 "| AC-2 | <實際結果> | <證據路徑> | <READY_FOR_REVIEW / FAIL / BLOCKED / UNVERIFIED> |"):
        require(want in skeleton, "skeleton lacks " + want)
    again = run_tool("gate_check", "--report-skeleton", order, "--repo", repo, "--out", report)
    require(again.returncode == 1 and "not overwritten" in text_of(again), "an existing report was overwritten")
    raw = run_tool("gate_check", "--report", report)
    require(raw.returncode == 1 and "placeholder left" in text_of(raw), "an unfilled skeleton passed --report")
    commands = [line for line in out.splitlines() if line.startswith("python ")]
    require(len(commands) == 3, "expected evidence + scope_check + match commands, got: " + tail(out))
    require(" ".join(check) in commands[0].replace('"test_*.py"', "test_*.py"), "evidence command is not the CHECKS one")
    ran = run_prog(shlex.split(commands[0]), cwd=repo)
    require(ran.returncode == 0, "the printed evidence command failed: " + tail(text_of(ran)))
    record = sorted((root / "DIRECTOR" / "evidence").glob("*.json"))[-1]
    scope = run_prog(shlex.split(commands[1].replace("<git rev-parse HEAD>", head)), cwd=repo)
    scope_line = (text_of(scope).strip().splitlines() or [""])[-1]
    require(scope.returncode == 0 and scope_line.startswith("SCOPE_CHECK: PASS"),
            "the printed scope_check command failed: " + tail(text_of(scope)))
    filled = (skeleton.replace("<HEAD 40 位>", head).replace("<yes|no>", "yes")
              .replace("<PASS | PARTIAL | BLOCKED | FAIL>", "PASS")
              .replace("SCOPE_CHECK: <貼 scope_check.py 的最後一行>", scope_line)
              .replace("<evidence .json 檔名>", record.name)
              .replace("<PASS / FAIL / BLOCKED / UNVERIFIED>", "PASS")
              .replace("<證據路徑>", "calc.py").replace("<READY_FOR_REVIEW / FAIL / BLOCKED / UNVERIFIED>", "READY_FOR_REVIEW")
              .replace("<實際跑過的指令，一行一個>", "python -B -I -m unittest").replace("exit=<N> at=<HH:MM>", "exit=0 at=09:00"))
    filled = "\n".join(line for line in filled.splitlines() if not line.startswith("SESSION_ID"))
    filled = re.sub(r"<NONE[^<>\n]*>", "NONE", filled)
    filled = re.sub(r"<[^<>\n]+>", "filled in", filled)
    report.write_text(filled, encoding="utf-8")
    match = run_prog(shlex.split(commands[2]), cwd=repo)
    require(match.returncode == 0, "the filled skeleton failed --match: " + tail(text_of(match)))
    return "skeleton -> unfilled FAIL, filled + printed commands -> scope PASS, --match OK"


@test
def verify_dsh_run_unit(tmp):
    proc = run_prog([sys.executable, "-B", "-I", "-X", "utf8", "-m", "unittest", "discover", "-s", TOOLS, "-p",
                     "test_verify_dsh_run.py"], cwd=tmp)
    ran = re.search(r"Ran (\d+) test", text_of(proc))
    require(proc.returncode == 0 and ran, "test_verify_dsh_run.py failed: " + tail(text_of(proc)))
    return "%s unit tests (D08 peek cases, settings, synthetic run)" % ran.group(1)


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
