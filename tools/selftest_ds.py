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
  matching_223  2.2.3-ds.3 (upstream 2.2.3, L-052 / L-054): report_vs_audit splits statements (new line ; && ||),
              reads a ``` block under RAN, ends at= at the time, leaves a full-width note out, needs one run per listed
              AC ID, lets an abbreviated claim skip options and match short words (x..., a bare name, 同上), matches 3
              words at the end of a cut line, calls an exit of a statement that is not the last "not checkable", and
              prints shadow WARNs (a RAN line with no command, SCOPE_CHECK PASS before the agent's last commit):
              15 matcher cases, 14 CLI runs, the same in process, 16 mutations killed
  evidence_git_223 2.2.3-ds.3 (upstream 2.2.3, L-055): evidence_record --rerun lets git run for read-only
              subcommands only (diff show log status rev-parse ls-files cat-file); push / commit / reset / checkout,
              no subcommand, an option before it and --output / --ext-d / --textconv are refused; git_argv turns
              off pager, replace refs, fsmonitor, optional locks, external diff and textconv; 4 mutations killed
  setup_shadow  2.2.1-ds.1: dsh_setup_check shadow lines (PO IDs, RESUME values, director_work.json keys) stay
              notes without --strict and fail with it; a clean folder passes --strict. 2.2.2-ds.3: RESUME_SIZE and
              the resume / base_ref / release blocks too; the example config is clean
  audit_rebuild 2.2.1-ds.1: dsh_audit.chain_lines writes the kind=rebuild first line, dsh_audit verify accepts the
              chain and report_vs_audit reads it with a note (no DSH session log needed)
  release_state 2.2.2-ds.3: release.py dry run on temp bare repos: BEHIND and DIVERGED stop, --merge predicts the
              conflicted file, AHEAD plans push / tag / release, a version below a remote tag and a VERSION that
              differs from the CHANGELOG top stop; version_key orders 2.2.0-ds.2 below 2.2.1-ds.1; 2.2.3-ds.3:
              the (upstream, ds) pair as a whole, after v2.2.2-ds.3: 2.2.3-ds.3 passes, 2.2.2-ds.2 and 2.2.2-ds.3
              stop, release.py has no flag that skips a check; a
              VERSION changed in the working tree but not committed stops before anything else (any modified
              tracked file stops a dry run too; the version is read from HEAD)
  release_scan  2.2.2-ds.3: release.py public scan stops an API key, a key = value secret, a private email, a
              <drive>:/Users path, DIRECTOR/ / _work/ / session files and a private author email, never prints a secret;
              noreply / .invalid emails and DIRECTOR/ named in text pass
  base_ref_fresh 2.2.2-ds.3: gate_check --order fetches and compares BASE_REF with origin/main in a temp clone:
              up to date is confirmed, 1 behind is a WARN note (--strict-base: FAIL), a missing commit is noted,
              a failed fetch says it did not compare (--strict-base: FAIL)
  resume_size   2.2.2-ds.3 (upstream 2.2.2): memory_size_check --kind resume with several --file, --glob,
              --workstreams, movable bytes, a config key of the wrong type; gate_check --resume shadow, --strict and
              limits from director_work.json / --config; the example's resume block; 2 size-rule mutations
  resume_archive 2.2.2-ds.3 (upstream 2.2.2): resume_archive.py by count only (keep_recent; no keep_days): newest
              sections and Before: entries stay, protected / undated / unclear-order parts stay, dry-run writes
              nothing, --execute backs up and verifies (a) (b) (c), a failed check restores; 9 mutations caught
  verify_dsh_run_unit 2.2.2-ds.3: tools/test_verify_dsh_run.py: the 11 D08 peek cases of WO-101, config / order
              settings, a synthetic project run (--no-dsh) with a clean, a test-editing and a wrong worker branch,
              and the D13 step markers (acceptance is not a --help read, verdict / summary found by file name)
  report_skeleton 2.2.2-ds.3: gate_check --report-skeleton fills the order's fields, hash and one row per AC; left
              unfilled it fails --report; filled with the evidence its printed commands record, it passes --match
  release_execute 2.2.2-ds.3: release.py --merge --execute on a temp bare origin: merge --no-ff into release/<v>,
              push and tag verified with ls-remote, the release step stops on a non-GitHub remote, a rerun skips
  order_oversize ds.2: scope_check on a Standard order: 4 changed files OVERSIZE, 3 pass
  revision_sync 2.2.3-ds.3: gate_check --order on REVISION 2 notes BRIEF / tasks.md / RESUME_STATE to sync and
              marks a WORK_DIR file older than the order `shadow: REVISION_SYNC`; exit code unchanged; REVISION 1 silent
  bootstrap_repo 2.2.3-ds.3: bootstrap_repo.py adds .memsearch/ to .git/info/exclude once, a rerun is clean, --check
              writes nothing. 2.2.5-ds.5 (B1 / B3, L-061): a ds.4 config with the old sdd block (openspec_bin null or
              a missing path) and a stand-in CLI on OPENSPEC_BIN: only the B1 WARN lines, no lookup, nothing written,
              no init, no install TODO, exit 0
  safety_tests_locked_225 / safety_plan_and_review_225 / spec_review_224 / safety_switch_off_225 /
  safety_legacy_block_225 / safety_mutations_225 2.2.5-ds.5 B1 (A4c): the safety gates without OpenSpec: edited
              locked test, missing TESTS_LOCKED, STOP_RULES 2 輪, changed or unticked PLAN.md, no PLAN_APPROVED, no
              SPEC_REVIEW, a switch turned off without the PO's answer all FAIL; an old sdd block: switches read with
              請搬到 safety, OpenSpec keys ignored with a WARN; 5 mutations
  worker_worktree_225 2.2.5-ds.5 B4: dsh_session --worker-worktree opens <REPO>/../wt/<WO> on its own branch; the
              WORKTREE line (--worktree-status, gate_check --report-skeleton) comes from git worktree list
              (main = 共用 checkout（主 checkout）, linked = 隔離 worktree, with the root and the list count, upstream
              2.2.5 scope_check's line); an existing folder or a bad id is refused; 2 mutations
  usage_final_225 2.2.5-ds.5 B2: gate_check --final DIRECTOR: without evidence/E2E/ it is FAIL final, exit 1; with an
              E2E record, usage.json missing, unreadable or NO_DATA is `~ WARN USAGE` with exit 0; a dsh_usage.py
              --out file is `ok USAGE`; --final runs beside --order; 3 mutations in gate_check.usage_lines
  after_verdict_224 2.2.4-ds.4 (upstream 2.2.4 B2), expectations of upstream 2.2.5 B4: gate_check --after-verdict fails
              a late code commit by default (--warn: WARN, exit 0), code inside SCOPE counts too, docs/ and DIRECTOR/
              and .md are documents; the last of several verdicts; NOT_CHECKED candidate; 5 mutations
  report_vs_audit_225 2.2.5-ds.5 (upstream 2.2.5 B2, H1 classes of WO-DS-008): 10 matcher cases, 18 CLI runs (same in
              process): at= span with ～, long calls kept whole, input_cut lines are cut lines, left-out options, TEMP=x,
              workdir, shell functions, /d/ = D:/, 時間不符 / 沒跑, --tolerance-min, --lead stamps (COMMIT with --repo),
              entry_point never prints a Traceback; 13 mutations. DS: dsh_audit.py keeps an input whole by default and
              build --input-limit N cuts it and marks input_cut, read by report_vs_audit as a cut line
  weird_inputs_225 2.2.5-ds.5 (upstream 2.2.5 B7): templates/weird_inputs.py writes 11 awkward files, each checked by
              its bytes; a folder it cannot write is one line and exit 2
  ran_line_225  2.2.5-ds.5 (upstream 2.2.5 B1, B9, A5): ran_line.py run / record / --stamp modes, the RAN: block, a
              program that cannot start writes nothing; report_vs_audit accepts its line; WORK_DIR/tmp wins over TMPDIR
              (ran_line, evidence_record, release); 5 mutations
  gate_order_225 2.2.5-ds.5 (upstream 2.2.5 B3, A4): gate_check --sequence: PLAN_APPROVED before the first commit on any
              branch, dated headings, append-only log, SPEC_REVIEW needed, same-session review / verdict fails, missing
              session id WARN, Direct skipped; 10 orders worked out by hand; 5 mutations
  after_verdict_225 2.2.5-ds.5 (upstream 2.2.5 B4): late code commit FAIL by default, documents pass, a new verdict for
              the new candidate passes, a rewritten branch is `~ FAIL REWRITTEN`, --warn; 1 mutation
  final_225     2.2.5-ds.5 (upstream 2.2.5 B5, A4): gate_check --final: no / empty E2E record FAIL, no ENTRY_POINT: WARN,
              DD rows without 驗收案例 WARN, SUPERSEDED skipped, the folder holding DIRECTOR/; 3 mutations
  scope_shared_225 2.2.5-ds.5 (upstream 2.2.5 B10, B11): scope_check shared mode (WORKTREE 共用 or --shared, whole-word
              order ID, --candidate), OTHER files, WORKTREE line from git worktree list, BASE_REF bracket comment
              (scope_check and gate_check --order), long-path line, bad --base NOT_RUN; 4 mutations
(2.2.5-ds.5 drops upstream 2.2.5's browser_check.py use_work_temp check: DS has no browser_check.py.)
(2.2.5-ds.5 B1 removed the OpenSpec-only tests: sdd_spec_ok, sdd_no_spec_change, sdd_validate_fails, sdd_no_cli,
sdd_real_openspec, sdd_cli_lookup, sdd_cli_setup, sdd_which_off_224. The safety gates of sdd_tests_locked,
sdd_plan_and_review and sdd_spec_off_gate were rewritten without OpenSpec as safety_tests_locked_225,
safety_plan_and_review_225 and safety_switch_off_225; spec_review_224 is kept.)

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
# 2.2.4-ds.4 (upstream 2.2.4): under a long TMP, git on Windows stops at 260 characters ("Filename too long").
# core.longpaths=true for every git that selftest starts, also inside the tools it runs; an existing GIT_CONFIG_COUNT
# list is kept and extended. A local remote does not inherit it: the bare origins set it in their own config.
_GIT_N = int(os.environ.get("GIT_CONFIG_COUNT") or 0)
os.environ.update({"GIT_CONFIG_COUNT": str(_GIT_N + 1), "GIT_CONFIG_KEY_%d" % _GIT_N: "core.longpaths",
                   "GIT_CONFIG_VALUE_%d" % _GIT_N: "true"})
CLI_TOOLS = ("dsh_usage", "dsh_audit", "dsh_doctor", "dsh_setup_check", "dsh_guard", "gate_check",
             "scope_check", "evidence_record", "report_vs_audit", "trace_report", "round_check", "status_gen",
             "metrics_report", "memory_size_check", "secret_mask", "pause_ctl", "audit_log", "release",
             "verify_dsh_run", "bootstrap_repo", "dsh_session")
TESTS = []


class Skip(Exception):
    """The test cannot run here (missing optional dependency, no DSH data); not a failure."""


def test(function):
    TESTS.append(function)
    return function


def run_tool(name, *args, cwd=None, env=None):
    full = None
    if env:
        full = dict(os.environ)
        for key, value in env.items():
            if value is None:
                full.pop(key, None)
            else:
                full[key] = value
    return subprocess.run(PY_ARGS + [str(TOOLS / (name + ".py"))] + [str(a) for a in args],
                          cwd=str(cwd) if cwd else None, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=TIMEOUT, env=full)


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
    with open(path, "w", encoding="utf-8", newline="\n") as handle:  # Path.write_text(newline=) needs 3.10
        handle.write(text)
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


@test
def dsh_usage_out_224(tmp):
    """2.2.4-ds.4 B9: --out on NO_DATA writes a file with the reason (was: rc=2 and no file); a --project-dir below
    the startup folder gets a hint naming that folder."""
    empty = tmp / "usage224" / "empty"
    (empty / "cache").mkdir(parents=True)
    (empty / "sessions").mkdir(parents=True)
    out = tmp / "usage224" / "out" / "none.json"
    proc = run_tool("dsh_usage", "--cache-root", empty / "cache", "--sessions-root", empty / "sessions", "--out", out)
    require(proc.returncode == 2 and out.is_file(), "NO_DATA with --out wrote no file: " + tail(text_of(proc)))
    data = json.loads(out.read_text(encoding="utf-8"))
    require(data.get("status") == "NO_DATA" and "NO_DATA" in data.get("reason", "") and data.get("sessions") == [],
            "the NO_DATA file lacks status / reason: %s" % data)
    cache = sorted(dsh_home().glob("storages/session_projcache/sessions/*.json"))
    usage = load_tool("dsh_usage")
    picked = None
    for path in cache[-40:]:
        try:
            row = usage.row_from_projection(usage.dsh.read_projection(path))
        except Exception:
            continue
        if row.get("cwd"):
            picked = (path, row["cwd"])
            break
    if picked is None:
        return "NO_DATA file written (no DSH projection here for the hint half)"
    one = tmp / "usage224" / "one"
    one.mkdir()
    shutil.copy(picked[0], one / picked[0].name)  # a copy in the selftest temp folder, removed afterwards
    below = str(pathlib.Path(picked[1]) / "sub-folder-of-startup")
    out2 = tmp / "usage224" / "out" / "below.json"
    proc = run_tool("dsh_usage", "--cache-root", one, "--sessions-root", empty / "sessions", "--project-dir", below,
                    "--no-fallback", "--out", out2)
    text = text_of(proc)
    require(proc.returncode == 2 and out2.is_file() and "a parent of --project-dir" in text,
            "a --project-dir below the startup folder got no hint: " + tail(text))
    proc = run_tool("dsh_usage", "--cache-root", one, "--sessions-root", empty / "sessions", "--project-dir", picked[1],
                    "--no-fallback", "--out", tmp / "usage224" / "out" / "ok.json")
    require(proc.returncode == 0 and (tmp / "usage224" / "out" / "ok.json").is_file(),
            "the startup folder itself did not give rc=0 and a file: " + tail(text_of(proc)))
    return "NO_DATA --out writes status/reason, rc 2; subfolder hint names the startup folder; startup folder rc 0"


@test
def temp_env_224(tmp):
    """2.2.4-ds.4 B10: dsh_session.py --temp-env WORK_DIR points TEMP / TMP / TMPDIR at WORK_DIR/tmp; a child process
    started with that environment writes its temp files there; the report skeleton prints the same line."""
    work = tmp / "temp224" / "work dir"
    proc = run_tool("dsh_session", "--temp-env", work)
    text = text_of(proc)
    want = str((work / "tmp").resolve())
    require(proc.returncode == 0 and (work / "tmp").is_dir() and f"TEMP_ENV: {want}" in text
            and "$env:TEMP=" in text and "$env:TMPDIR=" in text and "export TEMP=" in text,
            "--temp-env did not print the lines or make the folder: " + tail(text))
    session = load_tool("dsh_session")
    env = session.temp_env(work)
    require(sorted(env) == ["TEMP", "TMP", "TMPDIR"] and set(env.values()) == {want}, "temp_env: %s" % env)
    child = subprocess.run(PY_ARGS + ["-c", "import tempfile; print(tempfile.gettempdir())"], capture_output=True,
                           text=True, env=dict(os.environ, **env), timeout=TIMEOUT)
    require(child.returncode == 0 and os.path.normcase(child.stdout.strip()) == os.path.normcase(want),
            "a child's tempfile.gettempdir() is not WORK_DIR/tmp: " + child.stdout.strip())
    order = wo_text("NONE", governance="Direct").replace(
        "FALLBACK       = 同名子代理續談", "FALLBACK       = 同名子代理續談\nWORK_DIR       = D:/work/wo-7  # 腳本與暫存")
    order_path = write(tmp / "temp224" / "DIRECTOR" / "orders" / "WO-7.md", order)
    gate = load_tool("gate_check")
    _, commands = gate.report_skeleton(order_path, tmp / "temp224")
    require(any(line.startswith("# TEMP first:") and "$env:TEMP='D:/work/wo-7/tmp'" in line for line in commands),
            "the skeleton has no TEMP line for WORK_DIR: %s" % commands[:3])
    return "folder made; PowerShell + bash lines; child gettempdir == WORK_DIR/tmp; skeleton TEMP line"


@test
def effort_check_224(tmp):
    """2.2.4-ds.4 B8: the order's EFFORT against the session's; EFFORT_ACTUAL line; shadow WARN on a mismatch."""
    usage, gate = load_tool("dsh_usage"), load_tool("gate_check")
    order = wo_text("NONE")  # PRIMARY_WORKER = 子代理「w1」, MODEL / EFFORT = deepseek-flash / high
    require(usage.order_effort(order) == ("w1", "deepseek-flash", "high"), "order_effort: %s" % (usage.order_effort(order),))
    rows = [{"agent": "lead", "effort": "max", "id": "session-1"}, {"agent": "w1", "effort": "max", "id": "w1-a"}]
    lines, off = usage.effort_lines(order, "WO-7", rows)
    require(off == 1 and lines[0].startswith("EFFORT_ACTUAL WO-7 agent=w1 effort=max order=high")
            and any(line.startswith("SHADOW WARN: WO-7 says EFFORT high, the session ran at max") for line in lines),
            "a max session for a high order gave no WARN: %s" % lines)
    same, off = usage.effort_lines(order, "WO-7", [{"agent": "W1", "effort": "high", "id": "w1-b"}])
    require(off == 0 and not any("WARN" in line for line in same), "a matching effort warned: %s" % same)
    none, _ = usage.effort_lines(order, "WO-7", rows[:1])
    require(none and none[0].startswith("SHADOW WARN: no DSH session of agent w1"), "no session: %s" % none)
    notes = []
    gate.effort_notes(order, ["WO-7"], "2026-11-14 09:01 | EFFORT_ACTUAL WO-7 agent=w1 effort=max order=high\n", notes)
    require(any(n.startswith("SHADOW WARN EFFORT: WO-7 says EFFORT high, the session ran at max") for n in notes),
            "gate_check did not warn on the logged mismatch: %s" % notes)
    notes = []
    gate.effort_notes(order, ["WO-7"], "EFFORT_ACTUAL WO-7 agent=w1 effort=high order=high\n", notes)
    require(notes == [], "a matching logged effort was noted: %s" % notes)
    gate.effort_notes(order, ["WO-7"], "DISPATCH WO-7 rev=1\n", notes)
    require(any("no `EFFORT_ACTUAL WO-7" in n for n in notes), "a missing EFFORT_ACTUAL line was not noted")
    empty = tmp / "effort224"
    (empty / "c").mkdir(parents=True)
    (empty / "s").mkdir(parents=True)
    order_path = write(empty / "WO-7.md", order)
    proc = run_tool("dsh_usage", "--effort-check", order_path, "--cache-root", empty / "c", "--sessions-root", empty / "s")
    require(proc.returncode == 2 and "NO_DATA" in text_of(proc), "--effort-check without sessions: " + tail(text_of(proc)))
    return "order high vs session max WARNs; same effort quiet; gate_check reads EFFORT_ACTUAL from the log"


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


CALC_TEST = "import unittest\n\nclass T(unittest.TestCase):\n    def test_add(self):\n        self.assertEqual(1 + 1, 2)\n"


def wo_text(tests, governance="Standard", stop="1"):
    return "\n".join([
        "# WO-7 — selftest", "**selftest order**", "", "```text",
        "ISSUED_BY      = 總監 2026-11-14 09:00", "REVISION       = 1", "TRACES_TO      = NONE",
        "PRIMARY_WORKER = 子代理「w1」", "MODEL / EFFORT = deepseek-flash / high", "FALLBACK       = 同名子代理續談",
        f"GOVERNANCE     = {governance}", "BASE_REF       = main @ abc1234", "```", "",
        "```text", "SCOPE:", "- calc.py", "FORBIDDEN:", "- NONE", "```", "",
        "```text", "TESTS_LOCKED:", f"- {tests}", "```", "",
        "| ID | 類型 | 要求 | 驗證方法 | 預期 |", "|---|---|---|---|---|",
        "| AC-1 | AUTO | add returns the sum | python -m unittest test_calc | exit 0 |", "",
        "- DELIVERABLES: one commit", f"- STOP_RULES: 同一根因 {stop} 輪沒進展就停", ""])


def wo_fixture(tmp, name):
    """A project folder with a locked test (TESTS_LOCKED line) for gate_check --order."""
    repo = tmp / name
    test_file = write(repo / "test_calc.py", CALC_TEST)
    lock = "test_calc.py sha256=" + hashlib.sha256(test_file.read_bytes()).hexdigest()
    return repo, lock


def wo_run(repo, order_text, *extra):
    order = write(repo / "orders" / "WO-7.md", order_text)
    proc = run_tool("gate_check", "--order", order, "--repo", repo, *extra)
    return proc, text_of(proc)


def safety_dir(tmp, name, safety=None, legacy=None):
    """A DIRECTOR folder with director_work.json ("safety" and / or an old "sdd" block) for the safety gates."""
    director = tmp / name / "DIRECTOR"
    data = {"schema_version": 1}
    if safety is not None:
        data["safety"] = safety
    if legacy is not None:
        data["sdd"] = legacy
    return director, write(director / "director_work.json", json.dumps(data))


@test
def safety_tests_locked_225(tmp):
    """2.2.5-ds.5 B1 (A4c; was sdd_tests_locked of ds.2): TESTS_LOCKED and STOP_RULES without OpenSpec: an edited
    locked test FAILs, a Standard order without TESTS_LOCKED FAILs, STOP_RULES 2 輪 FAILs, safety.stop_after_rounds=2
    relaxes it only with the PO's answer (總監 ruling 2026-11-15: raising it loosens the gate), and an old
    sdd.stop_after_rounds=2 still counts with 「請搬到 safety」."""
    repo, lock = wo_fixture(tmp, "safety_tests")
    proc, text = wo_run(repo, wo_text(lock))
    require(proc.returncode == 0 and "OK   order" in text, "a locked, unchanged test was refused: " + tail(text))
    write(repo / "test_calc.py", CALC_TEST + "    def test_more(self):\n        pass\n")
    proc, text = wo_run(repo, wo_text(lock))
    require(proc.returncode == 1 and "test_calc.py changed since it was locked" in text,
            "an edited locked test did not FAIL: " + tail(text))
    proc, text = wo_run(repo, wo_text(lock).replace("TESTS_LOCKED:\n- " + lock + "\n", ""))
    require(proc.returncode == 1 and "TESTS_LOCKED: missing" in text, "no TESTS_LOCKED did not FAIL: " + tail(text))
    stop, stext = wo_run(repo, wo_text("NONE", stop="2"))
    require(stop.returncode == 1 and "STOP_RULES: allows 2 rounds" in stext, "STOP_RULES 2 輪 did not FAIL: " + tail(stext))
    director, config = safety_dir(tmp, "safety_rounds", safety={"stop_after_rounds": 2})
    raised, rtext = wo_run(repo, wo_text("NONE", stop="2"), "--config", config)
    require(raised.returncode == 1 and "safety.stop_after_rounds is raised to 2 (default 1)" in rtext
            and "STOP_RULES: allows" not in rtext, "stop_after_rounds=2 without the PO's answer passed: " + tail(rtext))
    write(director / "PO_PENDING.md", "ID: OD-1\nSTATUS: answered\nQUESTION: raise stop_after_rounds to 2?\n"
          "OPTIONS: a) yes b) no\nRECOMMENDED: b\nSOURCE: lead\nANSWER: a) yes\n")
    relaxed, rtext = wo_run(repo, wo_text("NONE", stop="2"), "--config", config)
    require(relaxed.returncode == 0 and "the PO answered it" in rtext,
            "stop_after_rounds=2 with the PO's answer did not relax the rule: " + tail(rtext))
    old_dir, old = safety_dir(tmp, "safety_rounds_old", legacy={"stop_after_rounds": 2})
    write(old_dir / "PO_PENDING.md", "ID: OD-1\nSTATUS: answered\nQUESTION: raise stop_after_rounds to 2?\n"
          "OPTIONS: a) yes b) no\nRECOMMENDED: b\nSOURCE: lead\nANSWER: a) yes\n")
    legacy, ltext = wo_run(repo, wo_text("NONE", stop="2"), "--config", old)
    require(legacy.returncode == 0 and "sdd.stop_after_rounds 照讀，請搬到 safety" in ltext,
            "an old sdd.stop_after_rounds was not read with 請搬到 safety: " + tail(ltext))
    return ("edited test FAILs; no TESTS_LOCKED FAILs; STOP_RULES 2 輪 FAILs; raised to 2 FAILs without the PO, "
            "relaxes with the PO's answer; old sdd key read + WARN")


@test
def safety_plan_and_review_225(tmp):
    """2.2.5-ds.5 B1 (A4c; was sdd_plan_and_review): the plan gate with <WORK_DIR>/<WO>/PLAN.md, no OpenSpec: an
    unticked task FAILs, ticks keep the plan hash, an added task FAILs, no PLAN_APPROVED FAILs, no PLAN.md FAILs,
    and a log without SPEC_REVIEW FAILs."""
    safety = load_tool("safety_gate")
    repo, lock = wo_fixture(tmp, "safety_plan")
    work = tmp / "safety_plan_work"
    plan = write(work / "WO-7" / "PLAN.md", "## 1. Code\n\n- [ ] 1.1 Add subtract\n")
    order = wo_text(lock).replace("BASE_REF       =", "WORK_DIR       = %s\nBASE_REF       =" % work.as_posix())
    approved = safety.plan_hash(plan)
    log = f"2026-11-14 09:00 | SPEC_REVIEW WO-7 tokens=UNKNOWN issues=0/0/0 adopted=0\nPLAN_APPROVED WO-7 sha={approved}\n"
    config = dict(safety.DEFAULTS)
    unticked = safety.match_problems(order, ["WO-7"], log, repo, config, [])
    require(any("not ticked" in p for p in unticked), "a hand-in with an unticked task was not caught: %s" % unticked)
    write(plan, "## 1. Code\n\n- [x] 1.1 Add subtract\n")
    require(safety.match_problems(order, ["WO-7"], log, repo, config, []) == [], "approved plan + review was refused")
    printed = run_tool("safety_gate", "--plan-hash", plan, "--order", write(repo / "orders" / "WO-7.md", order))
    require(printed.returncode == 0 and ("PLAN_APPROVED WO-7 sha=" + approved) in text_of(printed),
            "--plan-hash did not print the approved line (ticks must keep the hash): " + tail(text_of(printed)))
    write(plan, "## 1. Code\n\n- [x] 1.1 Add subtract\n- [x] 1.2 Also refactor everything\n")
    changed = safety.match_problems(order, ["WO-7"], log, repo, config, [])
    require(any("differs from the approved plan" in p for p in changed), "an added task was not caught: %s" % changed)
    missing = safety.match_problems(order, ["WO-7"], "DISPATCH WO-7 rev=1 sha=" + "0" * 64 + "\n", repo, config, [])
    require(any(p.startswith("SPEC_REVIEW") for p in missing) and any(p.startswith("PLAN_APPROVED: no") for p in missing),
            "a log without SPEC_REVIEW / PLAN_APPROVED was not caught: %s" % missing)
    plan.unlink()
    gone = safety.match_problems(order, ["WO-7"], log, repo, config, [])
    require(any("PLAN.md not found" in p for p in gone), "a missing PLAN.md passed: %s" % gone)
    direct = safety.match_problems(wo_text(lock, governance="Direct"), ["WO-7"], "", repo, config, [])
    require(direct == [], "a Direct order was asked for a plan: %s" % direct)
    return "unticked FAILs; ticks keep the hash; added task FAILs; no PLAN_APPROVED / SPEC_REVIEW / PLAN.md FAILs"


@test
def spec_review_224(tmp):
    """2.2.4-ds.4 B4 (kept in 2.2.5-ds.5, A4c): a Standard/Strict order with no SPEC_REVIEW fails --match, with or
    without --dispatch-log."""
    safety = load_tool("safety_gate")
    director = tmp / "review224" / "DIRECTOR"
    order_path = write(director / "orders" / "WO-7.md", wo_text("NONE"))
    order = order_path.read_text(encoding="utf-8")
    config = dict(safety.DEFAULTS, plan_gate=False)
    none = safety.match_problems(order, ["WO-7"], None, tmp, config, [], order_path)
    require(any(p.startswith("SPEC_REVIEW: no") for p in none),
            "no --dispatch-log and no review anywhere did not FAIL (the old behaviour passed): %s" % none)
    write(director / "reviews" / "WO-70_SPEC_REVIEW.md", "another order's review\n")
    other = safety.match_problems(order, ["WO-7"], None, tmp, config, [], order_path)
    require(any(p.startswith("SPEC_REVIEW: no") for p in other), "WO-70's review counted for WO-7: %s" % other)
    write(director / "reviews" / "WO-7_SPEC_REVIEW.md", "審查紀錄\n")
    notes = []
    found = safety.match_problems(order, ["WO-7"], None, tmp, config, notes, order_path)
    require(found == [] and any("review file" in n for n in notes), "a review file was not found: %s %s" % (found, notes))
    (director / "reviews" / "WO-7_SPEC_REVIEW.md").unlink()
    write(director / "DIRECTOR_LOG.md", "2026-11-14 09:00 | SPEC_REVIEW WO-7 done\n")
    notes = []
    logged = safety.match_problems(order, ["WO-7"], None, tmp, config, notes, order_path)
    require(logged == [] and any("no tokens/issues/adopted" in n for n in notes),
            "a DIRECTOR_LOG line was not read, or its missing fields not noted: %s %s" % (logged, notes))
    given = safety.match_problems(order, ["WO-7"], "DISPATCH WO-7 rev=1\n", tmp, config, [], order_path)
    require(any("looked in: --dispatch-log" in p for p in given), "--dispatch-log without the line passed: %s" % given)
    direct = safety.match_problems(wo_text("NONE", governance="Direct"), ["WO-7"], None, tmp, config, [], order_path)
    off = safety.match_problems(order, ["WO-7"], "", tmp, dict(config, spec_review_for_standard=False), [], order_path)
    strict = safety.match_problems(wo_text("NONE", governance="Strict"), ["WO-7"], "", tmp,
                                   dict(config, spec_review_for_standard=False), [], order_path)
    require(direct == [] and off == [] and any(p.startswith("SPEC_REVIEW") for p in strict),
            "Direct, or spec_review_for_standard false, was asked for a review; or Strict was let off")
    return "no review FAILs (was: passed without --dispatch-log); review file / DIRECTOR_LOG found; Direct not asked"


@test
def safety_switch_off_225(tmp):
    """2.2.5-ds.5 B1 (A4c; the 2.2.3-ds.3 require_spec rule moved to the safety switches): a safety gate loosened
    for a Standard/Strict order (a switch off, or stop_after_rounds raised above 1) FAILs gate_check --order until a
    PO_PENDING entry naming it is answered; the same for an old sdd.<switch>; prefer_auto off is only a note (a hint,
    not a gate; 總監 ruling 2026-11-15); Direct orders are not asked."""
    repo, lock = wo_fixture(tmp, "safety_off")
    for key, value, state in (("tests_first", False, "is off"), ("plan_gate", False, "is off"),
                              ("spec_review_for_standard", False, "is off"), ("stop_after_rounds", 0, "is off"),
                              ("stop_after_rounds", 2, "is raised to 2 (default 1)")):
        director, config = safety_dir(tmp, f"safety_off_{key}_{value}", safety={key: value})
        proc, text = wo_run(repo, wo_text(lock), "--config", config)
        require(proc.returncode == 1 and f"safety.{key} {state} for a Standard order" in text
                and "may not loosen a safety gate" in text, f"{key}={value} passed without the PO: " + tail(text))
        write(director / "PO_PENDING.md", f"ID: OD-1\nSTATUS: open\nQUESTION: turn {key} off?\n"
              "OPTIONS: a) yes b) no\nRECOMMENDED: b\nSOURCE: lead\nANSWER:\n")
        proc, text = wo_run(repo, wo_text(lock), "--config", config)
        require(proc.returncode == 1 and "still open: wait for the PO" in text, f"{key}: an open entry passed: " + tail(text))
        write(director / "PO_PENDING.md", f"ID: OD-1\nSTATUS: answered\nQUESTION: turn {key} off?\n"
              "OPTIONS: a) yes b) no\nRECOMMENDED: b\nSOURCE: lead\nANSWER: a) yes\n")
        proc, text = wo_run(repo, wo_text(lock), "--config", config)
        require(proc.returncode == 0 and "the PO answered it" in text, f"{key}: the PO's answer did not allow it: " + tail(text))
    _, config = safety_dir(tmp, "safety_off_prefer_auto", safety={"prefer_auto": False})
    proc, text = wo_run(repo, wo_text(lock).replace("| AC-1 | AUTO |", "| AC-1 | REVIEW |"), "--config", config)
    require(proc.returncode == 0 and "safety.prefer_auto is off" in text and "a hint, not a gate" in text
            and "no AUTO criterion" not in text, "prefer_auto off was not just a note: " + tail(text))
    for value in (1, True):
        _, config = safety_dir(tmp, f"safety_rounds_{value}", safety={"stop_after_rounds": value})
        proc, text = wo_run(repo, wo_text(lock), "--config", config)
        require(proc.returncode == 0 and "stop_after_rounds" not in text, f"stop_after_rounds={value} was held: " + tail(text))
    director, config = safety_dir(tmp, "safety_off_legacy", legacy={"tests_first": False, "openspec_bin": None})
    proc, text = wo_run(repo, wo_text(lock), "--config", config)
    require(proc.returncode == 1 and "safety.tests_first is off" in text and "sdd.tests_first 照讀，請搬到 safety" in text,
            "an old sdd.tests_first=false was not read as the switch: " + tail(text))
    proc, text = wo_run(repo, wo_text(lock, governance="Direct"), "--config", config)
    require(proc.returncode == 0 and "is off" not in text, "a Direct order was held to the switches: " + tail(text))
    strict = safety_dir(tmp, "safety_off_strict", safety={"spec_review_for_standard": False})[1]
    proc, text = wo_run(repo, wo_text(lock, governance="Strict"), "--config", strict)
    require(proc.returncode == 0, "spec_review_for_standard off held a Strict order: " + tail(text))
    return ("4 gates off + stop_after_rounds raised: FAIL, open PO entry FAILs, answered passes; prefer_auto off a note; "
            "old sdd switch counts; Direct / Strict review ok")


@test
def safety_legacy_block_225(tmp):
    """2.2.5-ds.5 B1 (A4c): an old ds.4 "sdd" block reads without error: OpenSpec keys (openspec_bin, require_spec_*)
    are ignored with 「OpenSpec 已在 2.2.5-ds.5 移除，此鍵被忽略」, safety switches still count with 「請搬到 safety」, a
    switch also in "safety" is ignored with a WARN, a SPEC_CHANGE line is only a note; no CLI is looked up."""
    safety = load_tool("safety_gate")
    old = {"require_spec_for_strict": True, "require_spec_for_standard": False, "openspec_bin": None,
           "tests_first": True, "plan_gate": False, "stop_after_rounds": 1}
    director, path = safety_dir(tmp, "legacy", safety={"plan_gate": True}, legacy=old)
    config, problem = safety.load_config(None, path)
    notes = safety.legacy_notes(config)
    require(problem is None and config["plan_gate"] is True and config["tests_first"] is True
            and "require_spec_for_standard" not in config and "openspec_bin" not in config,
            "the old block was not read as designed: %s %s" % (problem, config))
    require(len(notes) == 3 and safety.REMOVED_WARN in notes[0] and "sdd.openspec_bin" in notes[0]
            and "sdd.require_spec_for_standard" in notes[0] and safety.MOVE_WARN in notes[1]
            and "sdd.stop_after_rounds" in notes[1] and "sdd.plan_gate 被忽略" in notes[2],
            "the WARN lines are wrong: %s" % notes)
    mark = tmp / "legacy" / "cli_was_run.txt"
    stand_in = write(tmp / "legacy" / "stand_in.py", "import pathlib\npathlib.Path(%r).write_text('ran')\n" % str(mark))
    repo, lock = wo_fixture(tmp, "legacy_repo")
    order = wo_text(lock).replace("BASE_REF       =", "SPEC_CHANGE    = openspec/changes/x\nBASE_REF       =")
    proc = run_tool("gate_check", "--order", write(repo / "orders" / "WO-7.md", order), "--repo", repo,
                    "--config", path, env={"OPENSPEC_BIN": str(stand_in)})
    text = text_of(proc)
    require(proc.returncode == 0 and text.count(safety.REMOVED_WARN) == 1 and "SPEC_CHANGE: the field is ignored" in text
            and not mark.exists(), "gate_check --order with the old block: " + tail(text))
    empty = safety_dir(tmp, "legacy_empty", legacy={})[1]
    require(safety.legacy_notes(safety.load_config(None, empty)[0]) == [
        "WARN: director_work.json 的 \"sdd\" 區塊是空的，2.2.5-ds.5 起沒有作用，可以刪掉（安全開關在 \"safety\"）"],
        "an empty sdd block is not one WARN")
    require(safety.legacy_notes(safety.load_config(None, safety_dir(tmp, "legacy_none", safety={})[1])[0]) == [],
            "a config without sdd printed a WARN")
    return "OpenSpec keys ignored + WARN, switches read + 請搬到 safety, safety wins + WARN, no CLI run, empty block WARN"


SAFETY_MUTATIONS = [
    ("locked test hash not compared", [("        elif file_hash(path) != m.group(2).lower():",
                                        "        elif False:")]),
    ("plan hash not compared", [("    elif plan_hash(plan) != sha.group(1).lower():", "    elif False:")]),
    ("PLAN_APPROVED not required", [("    if not approved:\n", "    if not approved:\n        return problems\n")]),
    ("switch may be turned off", [("        how = loosening(key, config.get(key))\n        if how is None:\n            continue\n",
                                   "        continue\n")]),
    ("stop_after_rounds may be raised", [("            return \"raised\"\n", "            return None\n")]),
    ("old sdd switch not read", [("        config.update(moved)\n", "")]),
]


@test
def safety_mutations_225(tmp):
    """2.2.5-ds.5 B1: each safety gate is needed: a safety_gate.py with one check taken out lets a bad case through."""
    good = load_tool("safety_gate")
    repo, lock = wo_fixture(tmp, "safety_mut")
    work = tmp / "safety_mut_work"
    plan = write(work / "WO-7" / "PLAN.md", "- [x] 1.1 a\n")
    order = wo_text(lock).replace("BASE_REF       =", "WORK_DIR       = %s\nBASE_REF       =" % work.as_posix())
    review = "SPEC_REVIEW WO-7 tokens=1 issues=0/0/0 adopted=0\n"
    other_plan = good.plan_hash(plan).replace(good.plan_hash(plan)[0], "0" if good.plan_hash(plan)[0] != "0" else "1", 1)
    _, path = safety_dir(tmp, "safety_mut_cfg", legacy={"tests_first": False})

    def wrong_with(module):
        notes = []
        cfg = dict(module.DEFAULTS)
        edited = write(tmp / "safety_mut_edit" / "test_calc.py", CALC_TEST + "# edited\n")
        bad = [module.order_problems(order, None, edited.parent, cfg, notes),
               module.match_problems(order, ["WO-7"], review + f"PLAN_APPROVED WO-7 sha={other_plan}\n", repo, cfg, []),
               module.match_problems(order, ["WO-7"], review, repo, cfg, []),
               module.order_problems(order, None, repo, dict(cfg, tests_first=False), []),
               module.order_problems(order, None, repo, dict(cfg, stop_after_rounds=2), [])]
        old_cfg = module.load_config(None, path)[0]
        bad.append(["read"] if old_cfg.get("tests_first") is False else [])
        return any(not problems for problems in bad)

    require(not wrong_with(good), "the real safety_gate.py lets a bad case through")
    survived = [name for name, swaps in SAFETY_MUTATIONS if not wrong_with(mutated("safety_gate", swaps))]
    require(not survived, "these safety mutations get nothing wrong: %s" % survived)
    return ("%d mutations killed (locked hash, plan hash, PLAN_APPROVED, switch off, rounds raised, old sdd switch)"
            % len(SAFETY_MUTATIONS))


@test
def order_oversize(tmp):
    if shutil.which("git") is None:
        raise Skip("git is not on PATH")
    repo = tmp / "order_size"
    repo.mkdir()
    write(repo / "calc.py", "x = 1\n")
    for args in (["git", "init", "-q", "-b", "main"], ["git", "config", "user.email", "selftest@example.invalid"],
                 ["git", "config", "user.name", "Selftest"], ["git", "config", "core.autocrlf", "false"],
                 ["git", "add", "calc.py"], ["git", "commit", "-q", "-m", "init"]):
        proc = run_prog(args, cwd=repo)
        require(proc.returncode == 0, " ".join(args) + " failed: " + tail(text_of(proc)))
    order = write(tmp / "order_size_order" / "WO-7.md", wo_text("NONE").replace("- calc.py", "- src/**"))
    for n in range(4):
        write(repo / "src" / f"m{n}.py", "a = 1\n")
    proc = run_tool("scope_check", "--order", order, "--repo", repo, "--base", "main")
    text = text_of(proc)
    require(proc.returncode == 1 and "OVERSIZE" in text and "files=4/3" in text, "4 changed files did not FAIL: " + tail(text))
    (repo / "src" / "m3.py").unlink()
    proc = run_tool("scope_check", "--order", order, "--repo", repo, "--base", "main")
    require(proc.returncode == 0 and "SIZE: files=3" in text_of(proc), "3 files did not pass: " + tail(text_of(proc)))
    return "4 files OVERSIZE, 3 files PASS"


def git_repo(path, files):
    """A git repo at path with `files` ({name: text}) committed on main."""
    path.mkdir(parents=True, exist_ok=True)
    for name, body in files.items():
        write(path / name, body)
    for args in (["git", "init", "-q", "-b", "main"], ["git", "config", "user.email", "selftest@example.invalid"],
                 ["git", "config", "user.name", "Selftest"], ["git", "config", "core.autocrlf", "false"],
                 ["git", "add", "-A"], ["git", "commit", "-q", "-m", "init"]):
        proc = run_prog(args, cwd=path)
        require(proc.returncode == 0, " ".join(args) + " failed: " + tail(text_of(proc)))
    return path


def git_commit(repo, message, *paths):
    for args in (["git", "add", "--", *paths], ["git", "commit", "-q", "-m", message]):
        proc = run_prog(args, cwd=repo)
        require(proc.returncode == 0, " ".join(args) + " failed: " + tail(text_of(proc)))


@test
def order_limits_224(tmp):
    """2.2.4-ds.4 B1: limits in the top-level order_limits block; test files apart; an old sdd.max_* key still
    counts with 「請搬到 order_limits」 (kept in 2.2.5-ds.5, read by safety_gate.py)."""
    if shutil.which("git") is None:
        raise Skip("git is not on PATH")
    repo = git_repo(tmp / "limits", {"calc.py": "x = 1\n"})
    order = write(tmp / "limits_order" / "WO-7.md",
                  wo_text("NONE").replace("- calc.py", "- src/**\n- tests/**\n- test_*.py"))
    write(repo / "src" / "a.py", "a = 1\n" * 150)
    write(repo / "tests" / "test_a.py", "b = 1\n" * 300)  # 300 test lines: over 200, under the test limit 400
    write(repo / "test_b.py", "c = 1\n" * 50)
    proc = run_tool("scope_check", "--order", order, "--repo", repo, "--base", "main")
    text = text_of(proc)
    require(proc.returncode == 0 and "SIZE: files=3 lines=150 test_lines=350 limit=3/200/400" in text,
            "test lines were not counted apart (defaults): " + tail(text))
    new = write(tmp / "limits_cfg" / "new.json", json.dumps({"order_limits": {"max_lines_per_order": 100}}))
    proc = run_tool("scope_check", "--order", order, "--repo", repo, "--base", "main", "--config", new)
    text = text_of(proc)
    require(proc.returncode == 1 and "OVERSIZE" in text and "lines=150/100" in text and "SHADOW" not in text,
            "order_limits.max_lines_per_order was not read: " + tail(text))
    old = write(tmp / "limits_cfg" / "old.json", json.dumps({"sdd": {"max_lines_per_order": 100}}))
    proc = run_tool("scope_check", "--order", order, "--repo", repo, "--base", "main", "--config", old)
    text = text_of(proc)
    require(proc.returncode == 1 and "lines=150/100" in text and "請搬到 order_limits" in text,
            "an old sdd.max_lines_per_order was not read with its shadow WARN: " + tail(text))
    both = write(tmp / "limits_cfg" / "both.json", json.dumps({"sdd": {"max_lines_per_order": 100},
                                                              "order_limits": {"max_lines_per_order": 500}}))
    proc = run_tool("scope_check", "--order", order, "--repo", repo, "--base", "main", "--config", both)
    text = text_of(proc)
    require(proc.returncode == 0 and "limit=3/500/400" in text and "is ignored (order_limits" in text,
            "order_limits did not win over an old sdd key: " + tail(text))
    tests = write(tmp / "limits_cfg" / "tests.json", json.dumps({"order_limits": {"max_test_lines_per_order": 300}}))
    proc = run_tool("scope_check", "--order", order, "--repo", repo, "--base", "main", "--config", tests)
    text = text_of(proc)
    require(proc.returncode == 1 and "test_lines=350/300" in text, "the test-line limit did not FAIL: " + tail(text))
    limits = load_tool("safety_gate")
    require(limits.is_test_file("tests/x/helper.py") and limits.is_test_file("a/test_x.py")
            and limits.is_test_file("x_test.py") and not limits.is_test_file("src/testing.py")
            and not limits.is_test_file("contest_x.py"), "is_test_file is wrong")
    return "defaults 3/200/400; order_limits read; old sdd.* + WARN; both: order_limits wins; test limit FAILs"


@test
def scope_shared_224(tmp):
    """2.2.4-ds.4 B2: two orders in one checkout; each sees only its own commits and in-scope uncommitted files."""
    if shutil.which("git") is None:
        raise Skip("git is not on PATH")
    repo = git_repo(tmp / "shared", {"a.py": "a = 1\n", "b.py": "b = 1\n"})
    base = wo_text("NONE", governance="Direct").replace(
        "PRIMARY_WORKER = 子代理「w1」", "PRIMARY_WORKER = 子代理「w1」\nWORKTREE       = 共用 checkout")
    one = write(tmp / "shared_orders" / "WO-11.md", base.replace("# WO-7", "# WO-11").replace("- calc.py", "- a.py"))
    two = write(tmp / "shared_orders" / "WO-12.md", base.replace("# WO-7", "# WO-12").replace("- calc.py", "- b.py"))
    write(repo / "a.py", "a = 2\n")
    git_commit(repo, "WO-11: change a", "a.py")
    write(repo / "b.py", "b = 2\n")
    git_commit(repo, "WO-12: change b", "b.py")
    write(repo / "b.py", "b = 3\n")  # WO-12's worker, not committed yet
    write(repo / "notes_w2.txt", "scratch of the other worker\n")
    proc = run_tool("scope_check", "--order", one, "--repo", repo, "--base", "main~2")
    text = text_of(proc)
    require(proc.returncode == 0 and "shared=1" in text and "OTHER     b.py" in text and "OUTSIDE" not in text
            and "changed=1" in text, "WO-11 in a shared checkout counted the other worker's files: " + tail(text))
    proc = run_tool("scope_check", "--order", two, "--repo", repo, "--base", "main~2")
    text = text_of(proc)
    require(proc.returncode == 0 and "OTHER     a.py" in text and "changed=1" in text,
            "WO-12 did not count its own commit and uncommitted file: " + tail(text))
    write(repo / "a.py", "a = 3\n")
    git_commit(repo, "WO-11: also touch b", "a.py")
    write(repo / "b.py", "b = 4\n")
    git_commit(repo, "WO-11 sneaks into b.py", "b.py")
    proc = run_tool("scope_check", "--order", one, "--repo", repo, "--base", "main~4")
    text = text_of(proc)
    require(proc.returncode == 1 and "OUTSIDE   b.py" in text,
            "an out-of-scope file in this order's own commit was not caught: " + tail(text))
    plain = write(tmp / "shared_orders" / "WO-13.md", base.replace("# WO-7", "# WO-13").replace(
        "WORKTREE       = 共用 checkout", "WORKTREE       = D:/wt/13").replace("- calc.py", "- a.py"))
    proc = run_tool("scope_check", "--order", plain, "--repo", repo, "--base", "main~4")
    require(proc.returncode == 1 and "shared=1" not in text_of(proc),
            "an order with its own worktree went into shared mode: " + tail(text_of(proc)))
    return "two orders, one checkout: each PASS on its own files; own out-of-scope commit FAILs; own worktree off"


@test
def protected_tests_224(tmp):
    """2.2.4-ds.4 B5: a protected test file may be added or appended to; changing existing content FAILs."""
    if shutil.which("git") is None:
        raise Skip("git is not on PATH")
    test_text = "import unittest\n\nclass T(unittest.TestCase):\n    def test_a(self):\n        self.assertEqual(1, 1)\n"
    repo = git_repo(tmp / "protect", {"calc.py": "x = 1\n", "test_money.py": test_text, "test_csv.py": test_text})
    order = write(tmp / "protect_order" / "WO-7.md", wo_text("NONE", governance="Direct").replace(
        "- calc.py", "- calc.py\n- test_*.py"))
    config = write(tmp / "protect_order" / "cfg.json", json.dumps({"protected_tests": ["test_money.py", "test_csv.py"]}))
    write(repo / "test_money.py", test_text + "\n    def test_b(self):\n        self.assertEqual(2, 2)\n")
    write(repo / "test_new.py", test_text)
    proc = run_tool("scope_check", "--order", order, "--repo", repo, "--base", "main", "--config", config)
    text = text_of(proc)
    require(proc.returncode == 0 and "PROTECTED_CHANGED: test_money.py" in text,
            "an appended test was refused or not listed: " + tail(text))
    write(repo / "test_csv.py", test_text.replace("assertEqual(1, 1)", "assertEqual(1, 1 or 2)"))
    proc = run_tool("scope_check", "--order", order, "--repo", repo, "--base", "main", "--config", config)
    text = text_of(proc)
    require(proc.returncode == 1 and "PROTECTED test_csv.py" in text and "protected=1" in text,
            "an edited protected test did not FAIL: " + tail(text))
    (repo / "test_csv.py").unlink()
    proc = run_tool("scope_check", "--order", order, "--repo", repo, "--base", "main", "--config", config)
    require(proc.returncode == 1 and "was deleted" in text_of(proc), "a deleted protected test did not FAIL")
    write(repo / "test_csv.py", test_text.replace("\n", "\r\n"))  # line endings only
    proc = run_tool("scope_check", "--order", order, "--repo", repo, "--base", "main", "--config", config)
    require(proc.returncode == 0, "CRLF alone counted as a change: " + tail(text_of(proc)))
    locked = write(tmp / "protect_order" / "WO-8.md", wo_text("test_csv.py sha256=" + "0" * 64,
                                                               governance="Direct").replace("- calc.py", "- test_*.py"))
    write(repo / "test_csv.py", "# rewritten\n")
    proc = run_tool("scope_check", "--order", locked, "--repo", repo, "--base", "main")
    require(proc.returncode == 1 and "PROTECTED test_csv.py" in text_of(proc),
            "a TESTS_LOCKED file was not protected without a config: " + tail(text_of(proc)))
    return "append PASS + listed; edit FAILs; delete FAILs; CRLF only PASS; TESTS_LOCKED protected"


@test
def protected_report_224(tmp):
    """2.2.4-ds.4 B5: the report's PROTECTED_CHANGED is held against git by gate_check --match."""
    if shutil.which("git") is None:
        raise Skip("git is not on PATH")
    gate, limits = load_tool("gate_check"), load_tool("safety_gate")
    body = "import unittest\n\nclass T(unittest.TestCase):\n    def test_a(self):\n        self.assertEqual(1, 1)\n"
    repo = git_repo(tmp / "protect_report", {"calc.py": "x = 1\n", "test_money.py": body, "test_csv.py": body})
    start = run_prog(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    order_path = write(tmp / "protect_report_dir" / "orders" / "WO-7.md", wo_text("NONE", governance="Direct")
                       .replace("- calc.py", "- calc.py\n- test_*.py").replace("main @ abc1234", "main @ " + start))
    write(tmp / "protect_report_dir" / "director_work.json", json.dumps({"protected_tests": ["test_money.py",
                                                                                            "test_csv.py"]}))
    order = order_path.read_text(encoding="utf-8")
    config, problem = limits.load_config(order_path)
    require(problem is None and config.get("_protected_tests"), "protected_tests not loaded: %s" % problem)
    write(repo / "test_money.py", body + "\n    def test_b(self):\n        pass\n")
    git_commit(repo, "WO-7: add a test", "test_money.py")
    head = run_prog(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()

    def check(report):
        notes = []
        return gate.protected_report_problems(report, order, order_path, repo, config, head, notes), notes

    said_none, _ = check("PROTECTED_CHANGED: 無\n")
    require(any("git shows protected test files changed: test_money.py" in p for p in said_none),
            "無 while test_money.py changed did not FAIL: %s" % said_none)
    listed, _ = check("PROTECTED_CHANGED: test_money.py\n")
    require(listed == [], "a correct list was refused: %s" % listed)
    missing, notes = check("RESULT: PASS\n")
    require(missing == [] and any("missing in the report" in n for n in notes), "a missing field was not noted")
    write(repo / "test_csv.py", "# rewritten\n")
    git_commit(repo, "WO-7: rewrite csv test", "test_csv.py")
    head = run_prog(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    partial, _ = check("PROTECTED_CHANGED: test_money.py\n")
    require(any("leaves out: test_csv.py" in p for p in partial) and any(p.startswith("PROTECTED: test_csv.py")
                                                                          for p in partial),
            "a left-out, rewritten protected file did not FAIL: %s" % partial)
    return "無 vs diff FAILs; correct list passes; missing field noted; left-out + rewritten file FAILs"


@test
def checks_paths_224(tmp):
    """2.2.4-ds.4 B3: a CHECKS line with a backslash path is refused at --order, naming the line and forward slashes."""
    gate = load_tool("gate_check")
    lines = ["# WO-9", "", "```text", "CHECKS:",
             '- AC-1: ["python", "-I", "D:/w/tools/scope_check.py", "--order", "D:/w/orders/WO-9.md"]',
             '- AC-2: ["python", "-I", "D:\\wods\\tools\\scope_check.py"]',
             '- AC-3: ["python", "-I", "D:\\tmp\\new\\run.py"]',
             '- AC-4: ["python", "-I", "D:\\\\ok\\\\escaped.py"]', "```", ""]
    problems = []
    checks = gate.order_checks("\n".join(lines), problems)
    require(list(checks) == ["AC-1", "AC-4"], "only the forward-slash and escaped lines should parse: %s" % checks)
    require(any(p.startswith("CHECKS line 6 (AC-2): backslash path `D:\\wods\\tools\\scope_check.py` is not valid "
                             "JSON") and "forward slashes" in p for p in problems),
            "the invalid \\w escape was not named with its line: %s" % problems)
    require(any(p.startswith("CHECKS line 7 (AC-3)") and "control character" in p for p in problems),
            "\\t / \\n turned into control characters were not caught: %s" % problems)
    require(len(problems) == 2, "unexpected problems: %s" % problems)
    order = wo_text("NONE", governance="Direct").replace(
        "- DELIVERABLES", "```text\nCHECKS:\n" + lines[5] + "\n```\n\n- DELIVERABLES")
    order_path = write(tmp / "checks224" / "orders" / "WO-7.md", order)
    proc = run_tool("gate_check", "--order", order_path, "--repo", tmp / "checks224")
    text = text_of(proc)
    require(proc.returncode == 1 and "backslash path" in text and "CHECKS line " in text,
            "gate_check --order did not block the backslash path before dispatch: " + tail(text))
    return "\\w invalid and \\t silent both refused with the line number; forward / escaped slashes pass; --order FAILs"


# 2.2.4-ds.4 (upstream 2.2.4, WO-DW-224 B1): report_vs_audit and the 64 false FAILs of the WO-DS-006 trial. The case,
# log and run tables are upstream selftest.py's, byte for byte (de-identified, made-up paths).
RVA_EV224 = ("python tools/evidence_record.py run --label AC-1 --order D:/w/orders/wo-9.md --cwd D:/w/repo -- "
             "python -m unittest")
RVA_SCOPE224 = "python D:/w/tools/scope_check.py --order D:/w/orders/wo-9.md --repo D:/w/repo"
# (name, tool, command in the log, claimed command, should match) for matches() in process; 2.2.4 (WO-DS-006 misses,
# de-identified: the shapes of the 64 FAILs in H1_CLASSIFY, with made-up paths)
RVA_224_CASES = [
    ("git -C DIR x is cd DIR then git x", "Bash", "cd D:/w/repo && ls; git status --short", "git -C D:/w/repo status",
     True),
    ("git -C with another folder", "Bash", "cd D:/w/repo && ls; git status --short", "git -C D:/w/other status", False),
    ("bash variables are put back", "Bash", "T=D:/w/tools; O=D:/w/orders/wo-9.md\npython $T/gate_check.py --hash $O",
     "python D:/w/tools/gate_check.py --hash D:/w/orders/wo-9.md", True),
    ("a put-back variable still has to match", "Bash", "T=D:/w/tools; O=D:/w/orders/wo-9.md\n"
     "python $T/gate_check.py --hash $O", "python D:/w/tools/gate_check.py --hash D:/w/orders/wo-8.md", False),
    ("PowerShell $x = a + b is put back", "PowerShell",
     '$r = "D:\\w\\repo"; $o = $r + "\\orders\\wo-9.md"; python D:\\w\\tools\\scope_check.py --order $o --repo $r',
     "scope_check.py --order D:/w/repo/orders/wo-9.md --repo D:/w/repo", True),
    ("a here-string is a value", "PowerShell", "$o = @\"\nD:\\w\\orders\\wo-9.md\n\"@\npython tools/gate_check.py --hash $o",
     "gate_check.py --hash D:/w/orders/wo-9.md", True),
    ("a here-string value still has to match", "PowerShell",
     "$o = @\"\nD:\\w\\orders\\wo-9.md\n\"@\npython tools/gate_check.py --hash $o", "gate_check.py --hash D:/w/orders/wo-8.md",
     False),
    ("a bash heredoc does not hide the next line", "Bash",
     "cat <<'EOF' > D:/w/a.txt\nhello\nEOF\npython tools/gate_check.py --hash D:/w/orders/wo-9.md",
     "gate_check.py --hash D:/w/orders/wo-9.md", True),
    (".../x and ...\\x inside a word", "Bash", RVA_SCOPE224, "scope_check.py --order .../wo-9.md --repo ...\\repo", True),
    (".../x with another file", "Bash", RVA_SCOPE224, "scope_check.py --order .../wo-8.md --repo ...\\repo", False),
    ("a short hex is a prefix of the logged sha", "Bash",
     "python tools/scope_check.py --base a0b1c2d3e4f5a6 --candidate 5e6f7a8b9c0d1e2f3a4b",
     "scope_check.py --base a0b1c2d3e4 --candidate 5e6f7a8b9c0d", True),
    ("a short hex with another start", "Bash", "python tools/scope_check.py --base a0b1c2d3e4f5a6 --candidate 5e6f7a8b9c0d1e",
     "scope_check.py --base a0b1c2d3e4 --candidate 5e6f7a8b9c0e", False),
    ("an absolute claimed path ends with the logged relative one", "Bash",
     "python DIRECTOR/tools/gate_check.py --report DIRECTOR/reports/r.md",
     "python D:/w/DIRECTOR/tools/gate_check.py --report D:/w/DIRECTOR/reports/r.md", True),
    ('python -c "..." is compared with its launcher', "Bash", 'python -B -c "import ast; print(1)"',
     'python -B -c "..."', True),
    ('python -c "..." against another call', "Bash", "python -B -m unittest", 'python -B -c "..."', False),
    ("options in another order", "Bash", RVA_EV224,
     "evidence_record.py run --order .../wo-9.md --cwd .../repo --label AC-1 -- python -m unittest", True),
    ("options in another order, another value", "Bash", RVA_EV224,
     "evidence_record.py run --order .../wo-9.md --cwd .../repo --label AC-2 -- python -m unittest", False),
    ("a full claim in another order names every option", "Bash", RVA_EV224,
     "evidence_record.py run --cwd D:/w/repo --label AC-1 -- python -m unittest", False),
    ("a full-width ； ends a statement and a word between CJK words is a note", "Bash",
     "git clone --quiet D:/w/repo D:/w/tmp/c1; cd D:/w/tmp/c1; python D:/w/tools/scope_check.py --repo .",
     "git clone --quiet ...；複製 w9 三檔後 scope_check.py --repo .", True),
    ("； with another option", "Bash",
     "git clone --quiet D:/w/repo D:/w/tmp/c1; cd D:/w/tmp/c1; python D:/w/tools/scope_check.py --repo .",
     "git clone --depth ...；複製 w9 三檔後 scope_check.py --repo .", False)]
RVA_CUT224 = "python tools/build_all.py --mode full --target alpha " + "--x " * 140 + "; python tools/lint.py --all"
# log rows: (MM:SS, agent, command, kind, status, tool_raw); session S1, 2026-11-14 03:MM:SS UTC
RVA_224_ROWS = [
    ("01:10", "w1", "python -m unittest tests.test_a", "result", "ok", None),
    ("02:00", "w1", "T=D:/w/tools", "result", "ok", None),
    ("02:30", "w1", "python $T/gate_check.py --hash D:/w/orders/wo-9.md", "result", "ok", None),
    ("03:00", "w1", "python -m py_compile a.py", "result", "ok", None),
    ("03:20", "w1", "git status --porcelain", "result", "ok", None),
    ("10:00", "w1", RVA_CUT224, "result", "ok", None),
    ("20:00", "w1", "for l in AC-1 AC-2 AC-3; do python tools/evidence_record.py run --label $l -- python -m unittest; "
     "done", "result", "ok", None),
    ("30:00", "w2", "python tools/scope_check.py --order D:/w/orders/wo-9.md --repo D:/w/repo", "result", "ok", "pwsh"),
    ("35:00", "w1", "python tools/report.py --week", "result", "ok", None),
    ("41:00", "w1", "python tools/books.py --strict", "result", "ok", None)]
RVA_224_LOGS = {"main": RVA_224_ROWS,
                "pwsh_error": RVA_224_ROWS + [("50:00", "w2", "python tools/x.py", "failure", "error", "pwsh")]}
# (name, report body after SESSION_ID: S1, log, exit, says, lacks); run by the CLI and, for mutants, in process
RVA_224_RUNS = [
    ("at=HH:MM:SS", "RAN: `python -m unittest tests.test_a` exit=0 at=03:01:10\n", "main", 0,
     ["seq 1 at", "PASS claims=1 ok=1"], []),
    ("at= span HH:MM–HH:MM widens the tolerance", "RAN: `python tools/report.py --week` exit=0 at=03:00–03:40\n", "main",
     0, ["seq 9 at", "PASS claims=1 ok=1"], []),
    ("variables carry from call to call of the agent",
     "RAN: `python D:/x/other/gate_check.py --hash D:/w/orders/wo-9.md` exit=0\n", "main", 1,
     ["not run in session S1"], []),
    ("a fence opened outside RAN: closes there; a table after it is no claim",
     "```text\nRAN:\n  - `python -m py_compile a.py` exit=0\n```\n\nACCEPTANCE:\n| AC-1 | `python -m nothing_ran` | PASS |\n"
     "\n```text\nNEXT: x\n```\n", "main", 0, ["PASS claims=1 ok=1"], []),
    ("statements run in separate calls", "RAN: `python -m py_compile a.py; git status --porcelain` exit=0\n", "main", 0,
     ["its statements were run in separate calls, seq 4, 5", "PASS claims=1 ok=1"], []),
    ("statements in separate calls must keep their order",
     "RAN: `git status --porcelain; python -m py_compile a.py` exit=0\n", "main", 1, ["not run in session S1"], []),
    ("a claim in the cut part of a call another claim matched is UNVERIFIED, not OK",
     "RAN: `build_all.py --mode full --target alpha ...` exit=0\nRAN: `python tools/lint.py --all` exit=0\n", "main", 0,
     ["UNVERIFIED command: `python tools/lint.py --all`: in log cut part: no call shows it, but seq 6 was cut at the "
      "log's input limit", "OK   command: `build_all.py", "PASS claims=2 ok=1 failed=0", "unverified=1"],
     ["OK   command: `python tools/lint.py"]),
    ("a claim found in the kept part of a cut call stays OK",
     "RAN: `python tools/build_all.py --mode full --target alpha` exit=0\n", "main", 0,
     ["OK   command: `python tools/build_all.py --mode full --target alpha`: seq 6", "PASS claims=1 ok=1 failed=0",
      "unverified=0"], ["UNVERIFIED"]),
    ("a cut call no other claim matched covers nothing", "RAN: `python tools/lint.py --all` exit=0\n", "main", 1,
     ["`python tools/lint.py --all`: not run in session S1"], ["may be in the cut part"]),
    ("a cut call outside at= covers nothing",
     "RAN: `build_all.py --mode full --target alpha ...` exit=0\nRAN: `python tools/lint.py --all` exit=0 at=03:50\n",
     "main", 1, ["`python tools/lint.py --all`: not run in session S1"], ["may be in the cut part"]),
    ("exit=1 on a mapped tool that never reports error: not checkable", "RAN: `" + RVA_SCOPE224.replace("D:/w/tools/", "tools/")
     + "` exit=1\n", "main", 0, ["seq 8 is a pwsh call and no pwsh call of this session has status error",
                                  "PASS claims=1 ok=1"], []),
    ("exit=1 on a mapped tool that does report error is checked", "RAN: `"
     + RVA_SCOPE224.replace("D:/w/tools/", "tools/") + "` exit=1\n", "pwsh_error", 1,
     ["exit=1, but the log says ok (seq 8)"], ["not checkable"]),
    ("exit=1 on a hook-logged call is checked", "RAN: `python tools/books.py --strict` exit=1\n", "main", 1,
     ["exit=1, but the log says ok (seq 10)"], ["not checkable"]),
    ("AC-1 .. AC-3 with spaces is a range (a $l loop)",
     "RAN: `evidence_record.py run --label AC-1 .. AC-3 -- python -m unittest` exit=0\n", "main", 0,
     ["seq 7, 7, 7 at", "PASS claims=1 ok=1"], []),
    ("a command nobody ran stays FAIL", "RAN: `python tools/deploy.py --prod` exit=0\n", "main", 1,
     ["not run in session S1"], [])]
# (name, swaps, checked by the runs instead of the matcher cases); each anchor must occur once in report_vs_audit.py
RVA_224_MUTATIONS = [
    ("no git -C", [('    for statement in norm(GIT_C.sub(lambda found: f"cd {found.group(1)} ; git ", command))'
                    '.split(" ; "):\n', '    for statement in norm(command).split(" ; "):\n')], False),
    ("no variables", [("            out.append(refs(part))\n", "            out.append(part)\n")], False),
    ("no here-string", [("    for found in HERE_STRING.finditer(command):\n", "    for found in []:\n")], False),
    ("no ... inside a word", [("    pattern = word_pattern(claim_word)\n", "    pattern = None\n")], False),
    ("no hex prefix", [("    if HEX.fullmatch(claim_word) and HEX.fullmatch(log_word) and "
                        "log_word.startswith(claim_word):\n", "    if False:\n")], False),
    ("no absolute claim, relative log", [('    return ("/" in log_word and not log_word.startswith(("/", ".", "-"))'
                                          ' and re.match(', '    return (False and re.match(')], False),
    ("no launcher-kept compare", [('        return word_match(fold(launched), norm(command).split(" "), cut, '
                                   'short)\n', "        return False\n")], False),
    ("no options in another order", [('            or any_order(words, have.split(" "), leaves_out(words) if '
                                      'short is None else short))\n', "            or False)\n")], False),
    ("another order may leave options out", [("            if used != sorted(used) and (short or len(used) == "
                                              "len(log_options)):\n", "            if used != sorted(used):\n")],
     False),
    ("no ；", [('text.replace("；", ";")', 'text.replace("；", "；")')], False),
    ("no CJK-note fold", [('    words = fold(want.split(" "))\n', '    words = want.split(" ")\n')], False),
    ("no carry between calls", [("            expanded, envs[agent] = expand_line(command, cut, "
                                 "envs.get(agent))\n", "            expanded, _ = expand_line(command, cut)\n")],
     True),
    ("no HH:MM:SS", [('    clock = re.fullmatch(r"(\\d{1,2}):(\\d{2})(?::\\d{2}(?:\\.\\d+)?)?", value)\n',
                      '    clock = re.fullmatch(r"(\\d{1,2}):(\\d{2})", value)\n')], True),
    ("no span", [("    span = AT_SPAN.fullmatch(value)\n", "    span = None\n")], True),
    ("no outer fence", [('and (outer or field != "RAN"):', "and False:")], True),
    ("no separate calls", [("        parts = split_runs(claim, mine, offset, tolerance)\n",
                            "        parts = None\n")], True),
    ("no cut cover", [("                if cover is not None:\n", "                if False:\n")], True),
    ("cut part printed as OK", [("        if index in in_cut:\n", "        if False:\n")], True),
    ("the kept part of a cut call is UNVERIFIED", [("        if index in in_cut:\n",
                                                    "        if index in in_cut or any(command_of(e)[1] for e in "
                                                    "shown):\n")], True),
    ("UNVERIFIED not counted", [("            unverified += 1\n", "            pass\n")], True),
    ("UNVERIFIED fails the run", [("            unverified += 1\n", "            failed += 1\n")], True),
    ("cut cover without another claim", [('    pool = [e for e in mine if e.get("seq") in anchors and',
                                          "    pool = [e for e in mine if True and")], True),
    ("cut cover outside at=", [('            and command_of(e)[1] and (at is None or near(str(e.get("ts")), at, '
                                'offset, tolerance + extra))]\n', "            and command_of(e)[1]]\n")], True),
    ("no mapped-tool exit rule", [('        elif (raw and claim["exit"] != 0', '        elif (False and raw')],
     True),
    ("mapped-tool exit rule with an error seen", [('not any(e.get("tool_raw") == raw and',
                                                   'not any(False and e.get("tool_raw") == raw and')], True),
    ("no spaced range", [('    command = ID_SPACED.sub(r"\\1..\\2", command)\n', "    pass\n")], True)]


def rva224_matches_wrong(module, audit):
    return [name for name, tool, command, claim, want in RVA_224_CASES
            if bool(module.matches({"command": claim}, {"tool": tool, "input": audit.summary({"command": command})})) != want]


def rva224_runs_wrong(module, reports, logs):
    wrong = []
    for (name, _, log, code, says, lacks), report in zip(RVA_224_RUNS, reports):
        try:
            got, out = call_main(module, "--report", report, "--log", logs[log], "--utc-offset", "+00:00")
        except Exception as error:  # a mutant that crashes is a wrong answer
            wrong.append("%s: crashed %s" % (name, type(error).__name__))
            continue
        if rva223_wrong(name, code, says, lacks, got, out):
            wrong.append(name)
    return wrong


@test
def report_vs_audit_224(tmp):
    audit = load_tool("audit_log")
    cut = audit.summary({"command": RVA_CUT224})
    require(cut.endswith("\u2026") and "lint.py" not in cut, "the RVA_CUT224 log line is not cut before lint.py, so it "
            "tests nothing")
    folder = tmp / "rva224"
    logs = {}
    for log_name, rows in RVA_224_LOGS.items():
        prev, out = audit.GENESIS, []
        for seq, (clock, agent, command, kind, status, raw) in enumerate(rows, 1):
            entry = {"seq": seq, "ts": "2026-11-14T03:%s.000+00:00" % clock, "session_id": "S1", "agent_id": agent,
                     "tool": "Bash", "tool_use_id": "t%d" % seq, "input": audit.summary({"command": command}),
                     "kind": kind, "result": {"status": status}, "duration_ms": None, "prev": prev}
            if raw:
                entry["tool_raw"] = raw
            entry["hash"] = audit.digest(entry)
            prev = entry["hash"]
            out.append(audit.canonical(entry))
        logs[log_name] = write(folder / (log_name + ".jsonl"), "".join(line + "\n" for line in out))
    reports = [write(folder / ("r%d.md" % n), "SESSION_ID: S1\n" + body) for n, (_, body, *_) in enumerate(RVA_224_RUNS)]
    cli = []
    for (name, _, log, code, says, lacks), report in zip(RVA_224_RUNS, reports):
        proc = run_tool("report_vs_audit", "--report", report, "--log", logs[log], "--utc-offset", "+00:00")
        if rva223_wrong(name, code, says, lacks, proc.returncode, text_of(proc)):
            cli.append("%s (exit %s): %s" % (name, proc.returncode, tail(text_of(proc), 300)))
    require(not cli, "report_vs_audit CLI gets these 2.2.4 runs wrong: %s" % cli)
    real = load_tool("report_vs_audit")
    wrong = rva224_matches_wrong(real, audit)
    require(not wrong, "report_vs_audit gets these 2.2.4 matcher cases wrong: %s" % wrong)
    wrong = rva224_runs_wrong(real, reports, logs)
    require(not wrong, "report_vs_audit in process gets these 2.2.4 runs wrong: %s" % wrong)
    survived = []
    for name, swaps, by_runs in RVA_224_MUTATIONS:
        module = mutated("report_vs_audit", swaps)
        if not (rva224_runs_wrong(module, reports, logs) if by_runs else rva224_matches_wrong(module, audit)):
            survived.append(name)
    require(not survived, "these 2.2.4 mutations get no case wrong, so the cases do not test them: %s" % survived)
    return "%d matcher cases, %d CLI runs (+ in process), %d mutations killed" % (
        len(RVA_224_CASES), len(RVA_224_RUNS), len(RVA_224_MUTATIONS))


# 2.2.4-ds.4 (upstream 2.2.4, WO-DW-224 B2): gate_check --after-verdict; order and verdict text are upstream's
AV224_ORDER = """# WO-002 app fix
ORDER_ID: WO-002
REVISION = 1
SCOPE:
- app.py
- lib/**
FORBIDDEN:
- secret.py
"""
AV224_VERDICT = """# GATE VERDICT {wo}
ORDER: {order} REVISION 1
CANDIDATE_HEAD: {head}
"""
# 2.2.5-ds.5: upstream 2.2.5's list (its tool changed: a top-level docs/ is a document, SCOPE no longer exempts code,
# the FAIL / WARN word is set once)
AV224_MUTATIONS = (
    ("no document rule", [('    return "DIRECTOR" in parts[:-1] or parts[0] == "docs" and len(parts) > 1 \\\n'
                           '        or parts[-1].lower().endswith((".md", ".rst", ".txt"))', '    return False')]),
    ("no docs folder", [('parts[0] == "docs" and len(parts) > 1', "False")]),
    ("no strict", [('word = "FAIL" if strict else "WARN"', 'word = "WARN"')]),
    ("first verdict, not last", [("last = next((f for f in found if all(leads_to(o[0], f[0]) for o in found)), None)",
                                  "last = found[-1]")]),
    ("every commit is late", [("        if code_files:\n", "        if True:\n")]))


@test
def after_verdict_224(tmp):
    """2.2.4-ds.4 (upstream 2.2.4, WO-DW-224 B2): gate_check --after-verdict; the last of several verdicts is the one
    the others lead to; a candidate that does not resolve is NOT_CHECKED. 2.2.5-ds.5: upstream 2.2.5 (WO-DW-225 B4)
    changed what this test expects: a late commit fails by default (--warn gives the old WARN, exit 0), code inside
    SCOPE counts too (every non-document file counts), and a top-level docs/ folder is a document."""
    folder = tmp / "after_verdict_224"
    repo, gates, orders = folder / "repo", folder / "DIRECTOR" / "gates", folder / "DIRECTOR" / "orders"
    for d in (repo / "lib", gates, orders):
        d.mkdir(parents=True)

    def git(*args):
        return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args], cwd=repo,
                              check=True, capture_output=True, text=True).stdout.strip()

    def commit(message, files):
        for name, text in files.items():
            write(repo / name, text)
        git("add", "-A")
        git("commit", "-q", "-m", message)
        return git("rev-parse", "HEAD")

    git("init", "-q", "-b", "main")
    first = commit("start", {"app.py": "a = 1\n", "other.py": "b = 1\n"})
    write(orders / "WO-002-app.md", AV224_ORDER)
    old = write(gates / "WO-001-GATE.md", AV224_VERDICT.format(wo="WO-001", order="WO-001-none.md", head=first[:12]))
    second = commit("candidate", {"app.py": "a = 2\n"})
    verdict = write(gates / "WO-002-GATE.md", AV224_VERDICT.format(wo="WO-002", order="WO-002-app.md", head=second))
    both = [verdict, old]
    expect_tool("after-verdict: HEAD is the candidate", "gate_check", 0, "--after-verdict", old, verdict, "--repo", repo,
                says=["OK   AFTER_VERDICT", "candidate %s (the others lead to it)" % second[:12], "HEAD is the candidate"],
                lacks="LATE_COMMIT")
    stages = [("none", both, False)]
    docs = commit("docs only", {"README.md": "x\n", "docs/guide.md": "y\n", "docs/diagram.svg": "<svg/>\n",
                                "DIRECTOR/state.json": "{}\n"})
    expect_tool("after-verdict: documents only", "gate_check", 0, "--after-verdict", *both, "--repo", repo,
                says=["OK   AFTER_VERDICT", "is 1 commit(s) later, 0 change files that are not documents"],
                lacks="LATE_COMMIT")
    stages.append(("docs", both, False))
    inside = commit("code inside SCOPE", {"app.py": "a = 3\n", "lib/x.py": "c = 1\n"})
    expect_tool("after-verdict: code inside SCOPE is late too (2.2.5 B4)", "gate_check", 1, "--after-verdict", *both,
                "--repo", repo, says=["FAIL AFTER_VERDICT",
                                      "~ FAIL LATE_COMMIT %s code inside SCOPE: app.py, lib/x.py" % inside[:12]])
    late = commit("code outside SCOPE", {"other.py": "b = 2\n", "notes.md": "z\n"})
    expect_tool("after-verdict: with --warn a late code commit is a WARN, exit unchanged", "gate_check", 0,
                "--after-verdict", *both, "--repo", repo, "--warn",
                says=["WARN AFTER_VERDICT", "~ WARN LATE_COMMIT %s code outside SCOPE: other.py" % late[:12],
                      "--warn, exit unchanged", "is 3 commit(s) later, 2 change files"], lacks=[docs[:12], "notes.md"])
    expect_tool("after-verdict: a late code commit fails by default (2.2.5 B4)", "gate_check", 1, "--after-verdict",
                *both, "--repo", repo, says=["FAIL AFTER_VERDICT", "~ FAIL LATE_COMMIT %s" % late[:12]],
                lacks="--warn, exit unchanged")
    expect_tool("after-verdict: --strict fails", "gate_check", 1, "--after-verdict", *both, "--repo", repo, "--strict",
                says=["FAIL AFTER_VERDICT", "~ FAIL LATE_COMMIT %s" % late[:12]], lacks="--warn, exit unchanged")
    expect_tool("after-verdict: the older verdict alone counts every later commit", "gate_check", 1, "--after-verdict",
                old, "--repo", repo,
                says=["order not found; every non-document file counts", "~ FAIL LATE_COMMIT " + second[:12]])
    stages += [("late", both, False), ("strict", both, True)]
    bad = write(gates / "WO-003-GATE.md", AV224_VERDICT.format(wo="WO-003", order="WO-002-app.md", head="deadbeef0"))
    expect_tool("after-verdict: a candidate that is not a commit is NOT_CHECKED", "gate_check", 0, "--after-verdict", bad,
                "--repo", repo, says=["NOT_CHECKED after-verdict", "~ NOT_CHECKED", "deadbeef0 is not a commit"])
    expect_tool("after-verdict: needs --repo", "gate_check", 2, "--after-verdict", verdict)
    expect_tool("after-verdict: a missing verdict file fails", "gate_check", 1, "--after-verdict", folder / "nope.md",
                "--repo", repo, says="file not found")
    expect_tool("after-verdict: --strict alone is still refused", "gate_check", 2, "--verdict", verdict, "--strict")
    expect_tool("after-verdict: --orders needs --after-verdict", "gate_check", 2, "--verdict", verdict, "--orders", orders)
    real = load_tool("gate_check")
    for path in ("DIRECTOR/a.json", "x/y.MD", "a\\DIRECTOR\\b.py"):
        require(real.is_document(path), "after-verdict: %s is not a document" % path)
    require(not real.is_document("DIRECTORY/a.py"), "after-verdict: DIRECTORY/a.py counted as a document")
    expected = {"none": 0, "docs": 0, "late": 2, "strict": 2}

    def wrong_with(module):
        got = []
        for head, part in ((second, stages[:1]), (docs, stages[1:2]), ("main", stages[2:])):
            git("checkout", "-q", "--detach", head) if head != "main" else git("checkout", "-q", "main")
            for name, paths, strict in part:
                try:
                    lines, count, _ = module.after_verdict([str(v) for v in paths], str(repo), None, strict)
                except Exception as error:  # a mutant that crashes is a wrong answer
                    got.append("%s: crashed %s" % (name, type(error).__name__))
                    continue
                text = "\n".join(lines)
                if count != expected[name] or (name == "strict") != ("~ FAIL LATE_COMMIT" in text) \
                        or (name == "late") != ("~ WARN LATE_COMMIT" in text) \
                        or (name in ("late", "strict")) != ("%s (the others lead to it)" % second[:12] in text and count > 0):
                    got.append(name)
        git("checkout", "-q", "main")
        return got
    wrong = wrong_with(real)
    require(not wrong, "after-verdict: after_verdict() is wrong at %s" % wrong)
    survived = [name for name, swaps in AV224_MUTATIONS if not wrong_with(mutated("gate_check", swaps))]
    require(not survived, "these after-verdict mutations get no stage wrong: %s" % survived)
    return "12 CLI checks, 4 stages in process, %d mutations killed" % len(AV224_MUTATIONS)

def path_line(out, prefix, path, suffix):
    """2.2.4 (upstream): a status line that names a path: the whole line, or (cut to the width) the same line with the
    middle of the path turned into "…" while the prefix, the start of the path, its file name and the suffix stay."""
    path = str(path)
    for line in out.splitlines():
        if line == prefix + path + suffix:
            return True
        if not (line.startswith(prefix) and line.endswith(suffix) and len(line) > len(prefix) + len(suffix)):
            continue
        middle = line[len(prefix):len(line) - len(suffix)]
        if middle.count("\u2026") == 1:
            head, end = middle.split("\u2026")
            if head and path.startswith(head) and path.endswith(end) and end.endswith(pathlib.PurePath(path).name):
                return True
    return False


STATUS_LONG_MUTATIONS = [
    ("cut from the end of the line", ('    out.append(fit(str(text), CONFIG["width"]))\n',
                                      '    out.append(str(text)[:CONFIG["width"]])\n')),
    ("a line without a path cut from its end",
     ('    return text[:head] + "\u2026" + text[len(text) - (width - 1 - head):]\n', '    return text[:width]\n'))]


@test
def status_long_path_224(tmp):
    d = tmp / "status_long"
    while len(str(d)) < 150:
        d = d / ("long_path_" + "p" * 30)
    d.mkdir(parents=True)
    write(d / "run.log", "first\n" + "x" * 300 + " END\n")
    (d / "out").mkdir()
    (d / "out" / "a.png").write_bytes(b"x")
    write(d / "PO_PENDING.md", "ID: OD-1\nSTATUS: answered\n")
    conf = write(d / "status.json", json.dumps({
        "schema_version": 1, "name": "long", "logs": ["run.log"], "log_lines": 2, "outputs": ["out"], "disk": str(d),
        "disk_min_gib": 0.001, "po_pending": {"path": "PO_PENDING.md", "counts": [
            {"label": "answered", "regex": "^STATUS:\\s*answered\\b"}]}}))
    script = d / "status.py"
    proc = run_tool("status_gen", "--config", conf, "--out", script)
    require(proc.returncode == 0, "status_gen exit %s: %s" % (proc.returncode, tail(text_of(proc))))

    def wrong(swap=None):
        run = script
        if swap:
            source = script.read_text(encoding="utf-8")
            if source.count(swap[0]) != 1:
                return ["anchor %r not found once" % swap[0]]
            run = d / "mutant.py"
            run.write_text(source.replace(*swap), encoding="utf-8")
        done = run_prog(PY_ARGS + [str(run)], cwd=d)
        out, lines = done.stdout, done.stdout.splitlines()
        bad = ["exit %s" % done.returncode] if done.returncode != 0 else []
        bad += ["%d characters: %s" % (len(x), x) for x in lines if len(x) > 160]
        for start, end in (("DISK ", " OK"), ("OUT ", ": 1 files, newest 1"), ("LOG ", " ago)"), ("  xxx", "x END"),
                           ("~ PENDING_METHOD_MISSING: ", " in DIRECTOR_STATE.md")):
            if not any(x.startswith(start) and x.endswith(end) for x in lines):
                bad.append("no line %s...%s" % (start, end))
        if not any(x.startswith("LOG ") and "run.log (" in x for x in lines):
            bad.append("LOG line lost the file name")
        if not path_line(out, "PO ", d / "PO_PENDING.md", ": answered=1"):
            bad.append("PO line")
        return bad + ([out[-600:]] if bad else [])

    bad = wrong()
    require(not bad, "status.py under a %d-character folder: %s" % (len(str(d)), bad))
    survived = [name for name, swap in STATUS_LONG_MUTATIONS if not wrong(swap)]
    require(not survived, "these status long-path mutations get no line wrong: %s" % survived)
    return "%d-character folder: every line fits 160 and keeps its end; %d mutations killed" % (
        len(str(d)), len(STATUS_LONG_MUTATIONS))

@test
def revision_sync(tmp):
    """2.2.3-ds.3 (WO-DS-005 B5): gate_check --order on REVISION 2 notes the files to sync and marks a WORK_DIR
    tasks.md written before the order with `shadow: REVISION_SYNC`; the exit code does not change."""
    repo, lock = wo_fixture(tmp, "revsync")
    work = tmp / "revsync_work"
    tasks = write(work / "tasks.md", "- [ ] 1.1 expect 9\n")
    resume = write(work / "RESUME_STATE.md", "PROGRESS: x\n")
    text1 = wo_text(lock).replace(
        "BASE_REF       =", "WORK_DIR       = %s\nBASE_REF       =" % work)
    order = write(repo / "orders" / "WO-7.md", text1.replace("REVISION       = 1", "REVISION       = 2")
                  + "\n## H. 變更紀錄\n| 版次 | 日期 | 變更 | 原因 |\n|---|---|---|---|\n| 2 | 2026-11-14 | 9 -> 11 | fix |\n")
    old = order.stat().st_mtime - 600
    os.utime(tasks, (old, old))
    os.utime(resume, (old + 1200, old + 1200))
    proc = run_tool("gate_check", "--order", order, "--repo", repo)
    text = text_of(proc)
    require(proc.returncode == 0 and "REVISION 2: sync BRIEF.md" in text and "shadow: REVISION_SYNC" in text
            and "tasks.md was last written before REVISION 2" in text and "RESUME_STATE.md was last" not in text,
            "REVISION 2 did not mark only the older tasks.md: " + tail(text))
    write(order, text1)
    proc = run_tool("gate_check", "--order", order, "--repo", repo)
    require(proc.returncode == 0 and "REVISION_SYNC" not in text_of(proc) and "REVISION 1" not in text_of(proc),
            "REVISION 1 printed sync notes: " + tail(text_of(proc)))
    return "REVISION 2: sync note, older tasks.md marked, newer RESUME_STATE not, exit 0; REVISION 1 silent"


@test
def bootstrap_repo(tmp):
    """2.2.3-ds.3 (WO-DS-005 B1): bootstrap_repo.py excludes .memsearch/ once and changes nothing on a rerun.
    2.2.5-ds.5 (WO-DS-009 B1 / B3, L-061): the spec-first steps are gone. With the shipped example nothing is said
    about them; a ds.4 config that still has the sdd block (openspec_bin null, or a path that does not exist), with a
    stand-in CLI on OPENSPEC_BIN, prints only the B1 WARN lines (one for the ignored OpenSpec keys, one 「請搬到
    safety」 for the switches it still reads), looks up no CLI (the stand-in leaves a mark when run), writes nothing
    into the config, runs no init, prints no install TODO, and exits 0."""
    if shutil.which("git") is None:
        raise Skip("git is not on PATH")
    repo = tmp / "boot" / "demo"
    repo.mkdir(parents=True)
    proc = run_prog(["git", "init", "-q", "-b", "main"], cwd=repo)
    require(proc.returncode == 0, "git init failed: " + tail(text_of(proc)))
    exclude = repo / ".git" / "info" / "exclude"
    write(exclude, "# git's own comment\n*.log")  # no newline at the end
    example = (TOOLS.parent / "director_work.example.json").read_text(encoding="utf-8")
    require('"sdd"' not in example, "the example still has the sdd block")
    config = write(tmp / "boot" / "DIRECTOR" / "director_work.json", example)
    warn = "OpenSpec 已在 2.2.5-ds.5 移除，此鍵被忽略"
    check = run_tool("bootstrap_repo", "--repo", repo, "--config", config, "--check")
    require(check.returncode == 1 and "TODO  exclude" in text_of(check) and warn not in text_of(check)
            and ".memsearch" not in exclude.read_text(encoding="utf-8"),
            "--check changed something or did not list the work: " + tail(text_of(check)))
    proc = run_tool("bootstrap_repo", "--repo", repo, "--config", config)
    text = text_of(proc)
    lines = exclude.read_text(encoding="utf-8").splitlines()
    require(proc.returncode == 0 and "BOOTSTRAP_REPO: DONE" in text and "*.log" in lines and ".memsearch/" in lines
            and config.read_text(encoding="utf-8") == example,
            "the exclude line was not added after the last line: %s %s" % (lines, tail(text)))
    again = run_tool("bootstrap_repo", "--repo", repo, "--config", config, "--check")
    require(again.returncode == 0 and "TODO" not in text_of(again)
            and exclude.read_text(encoding="utf-8").count(".memsearch/") == 1,
            "a rerun was not clean or added the line twice: " + tail(text_of(again)))
    mark = tmp / "boot" / "cli_was_run.txt"
    stand_in = write(tmp / "boot" / "stand_in_cli.py", "import pathlib, sys\npathlib.Path(%r).write_text(' '.join("
                     "sys.argv[1:]))\nprint('1.16.0')\n" % str(mark))
    old = {"require_spec_for_strict": True, "require_spec_for_standard": True, "spec_review_for_standard": True,
           "tests_first": True, "plan_gate": True, "stop_after_rounds": 1, "prefer_auto": True}
    for case, value in (("bin null", None), ("bin missing", str(tmp / "boot" / "no" / "openspec.cmd"))):
        legacy = json.loads(example)
        legacy.pop("safety"), legacy.pop("_comment_safety")  # a ds.4 config has no "safety" block
        legacy["sdd"] = dict(old, openspec_bin=value)
        path = write(tmp / "boot" / ("L061_" + case.replace(" ", "_")) / "director_work.json",
                     json.dumps(legacy, ensure_ascii=False, indent=2))
        before = path.read_bytes()
        proc = run_tool("bootstrap_repo", "--repo", repo, "--config", path, env={"OPENSPEC_BIN": str(stand_in)})
        text = text_of(proc)
        warns = [line for line in text.splitlines() if line.startswith("WARN")]
        require(proc.returncode == 0 and text.count(warn) == 1 and "BOOTSTRAP_REPO: DONE" in text
                and len(warns) == 2 and "請搬到 safety" in warns[1] and "sdd.openspec_bin" in warns[0]
                and path.read_bytes() == before and not mark.exists() and not (repo / "openspec").exists()
                and "TODO" not in text and "PO_PENDING" not in text
                and all(warn in line for line in text.splitlines() if "openspec" in line.lower()),
                "L-061 %s: %s" % (case, tail(text)))
    return ".memsearch/ excluded once (file without final newline kept), rerun clean, example silent; L-061: old sdd " \
           "block (bin null / bin missing) -> B1 WARNs only, no lookup, no write, no init, no TODO, exit 0"




WORKTREE_MUTATIONS = [  # 2.2.5-ds.5: worktree_kind now reads scope_check.worktree_line; the kind is taken from it
    ("main reads as isolated", [('    return ("isolated" if "隔離 worktree" in line else "shared"), line',
                                 '    return "isolated", line')]),
    ("worktree inside the repo", [('target = (pathlib.Path(root) if root else repo.parent / "wt") / order_id',
                                   'target = (pathlib.Path(root) if root else repo / "wt") / order_id')]),
]


@test
def worker_worktree_225(tmp):
    """2.2.5-ds.5 B4: dsh_session.py --worker-worktree REPO --order WO opens <REPO>/../wt/<WO> on its own branch; the
    WORKTREE line (--worktree-status, and gate_check --report-skeleton) comes from git worktree list: the main checkout
    is 「共用 checkout」, a linked one 「隔離 worktree」; an existing folder or a bad id is refused. 2.2.5-ds.5: the line
    is upstream 2.2.5 scope_check's: `WORKTREE: 共用 checkout（主 checkout） <root> (git worktree list: N)` or
    `WORKTREE: 隔離 worktree <root> (git worktree list: N)`."""
    if shutil.which("git") is None:
        raise Skip("git is not on PATH")
    repo = tmp / "wt225" / "ws" / "proj"
    write(repo / "a.py", "x = 1\n")
    rgit(repo, "init", "-q", "-b", "main")
    rgit(repo, "config", "user.email", "selftest@example.invalid")
    rgit(repo, "config", "user.name", "Selftest")
    rgit(repo, "add", "-A")
    rgit(repo, "commit", "-q", "-m", "base")
    proc = run_tool("dsh_session", "--worktree-status", repo)
    require(proc.returncode == 0 and "WORKTREE: 共用 checkout（主 checkout） " in text_of(proc)
            and "(git worktree list: 1)" in text_of(proc), "main checkout: " + tail(text_of(proc)))
    proc = run_tool("dsh_session", "--worker-worktree", repo, "--order", "WO-01", "--branch", "wo-01-x")
    target = tmp / "wt225" / "ws" / "wt" / "WO-01"
    require(proc.returncode == 0 and "WORKTREE: 隔離 worktree" in text_of(proc) and (target / "a.py").is_file()
            and rgit(target, "rev-parse", "--abbrev-ref", "HEAD") == "wo-01-x", "worker worktree: " + tail(text_of(proc)))
    proc = run_tool("dsh_session", "--worktree-status", target)
    require(proc.returncode == 0 and "WORKTREE: 隔離 worktree " in text_of(proc)
            and "(git worktree list: 2)" in text_of(proc) and "共用" not in text_of(proc),
            "linked worktree status: " + tail(text_of(proc)))
    again = run_tool("dsh_session", "--worker-worktree", repo, "--order", "WO-01")
    require(again.returncode == 1 and "exists" in text_of(again), "an existing worktree folder was reused")
    bad = run_tool("dsh_session", "--worker-worktree", repo, "--order", "../x")
    require(bad.returncode == 2, "a bad order id was accepted: " + tail(text_of(bad)))
    session = load_tool("dsh_session")
    require(session.worktree_kind(repo)[0] == "shared" and session.worktree_kind(target)[0] == "isolated",
            "worktree_kind is wrong")
    gate = load_tool("gate_check")
    require("WORKTREE: 隔離 worktree" in gate.worktree_line(target) and "WORKTREE: 共用 checkout" in gate.worktree_line(repo),
            "the report skeleton's WORKTREE line is not the tool's")
    survived = []
    for number, (name, swaps) in enumerate(WORKTREE_MUTATIONS, 2):
        module = mutated("dsh_session", swaps)
        kinds = (module.worktree_kind(repo)[0], module.worktree_kind(target)[0])
        code, _ = module.worker_worktree(repo, "WO-0%d" % number)
        if kinds == ("shared", "isolated") and code == 0 and (target.parent / ("WO-0%d" % number)).is_dir():
            survived.append(name)
    require(not survived, "these worktree mutations get nothing wrong: %s" % survived)
    return "main = 共用 checkout, --worker-worktree = 隔離 worktree on its branch, existing folder / bad id refused, " \
           "skeleton line from the tool; %d mutations killed" % len(WORKTREE_MUTATIONS)


USAGE_MUTATIONS = [  # 2.2.5-ds.5: anchors in gate_check.usage_lines (the final mode's pass / fail is upstream's E2E rule)
    ("missing usage not warned", [('return [f"  ~ WARN USAGE: {usage_path} not found',
                                   'return [f"  ok USAGE: {usage_path} not found')]),
    ("NO_DATA taken as data", [('    if status == "NO_DATA":', '    if status == "NO_DATA_NEVER":')]),
    ("unreadable taken as data", [('        return [f"  ~ WARN USAGE: {usage_path} unreadable: {error}"]',
                                   '        return [f"  ok USAGE: {usage_path}"]')]),
]


@test
def usage_final_225(tmp):
    """2.2.5-ds.5 B2: gate_check --final DIRECTOR looks for DIRECTOR/usage.json (or --usage FILE), the file the lead's
    last step writes with dsh_usage.py --out. Missing, unreadable or NO_DATA: `~ WARN USAGE`, never a failure; a usage
    file: `ok USAGE`. The usage lines come after upstream 2.2.5's `OK|FAIL final` lines: without a non-empty
    evidence/E2E/ record the final mode is `FAIL final`, exit 1 (final_225); with one (ENTRY_POINT:) it is `OK   final`."""
    director = tmp / "final225" / "DIRECTOR"
    director.mkdir(parents=True)

    def final(*extra):
        proc = run_tool("gate_check", "--final", director, *extra)
        return proc.returncode, text_of(proc)

    code, out = final()
    require(code == 1 and "FAIL final" in out and "  - E2E: no end-to-end evidence in" in out and "~ WARN USAGE" in out,
            "--final without E2E evidence is not FAIL final, exit 1: " + tail(out))
    write(director / "evidence" / "E2E" / "run.txt", "ENTRY_POINT: python -m calc 1 + 2\n3\n")
    cases = []
    code, out = final()
    cases.append(("missing", code == 0 and "~ WARN USAGE" in out and "not found" in out and "OK   final" in out
                  and "WARN E2E" not in out, out))
    write(director / "usage.json", "{not json")
    code, out = final()
    cases.append(("unreadable", code == 0 and "~ WARN USAGE" in out and "unreadable" in out, out))
    write(director / "usage.json", json.dumps({"status": "NO_DATA", "reason": "no sessions"}))
    code, out = final()
    cases.append(("NO_DATA", code == 0 and "~ WARN USAGE" in out and "NO_DATA" in out, out))
    other = write(tmp / "final225" / "elsewhere.json", json.dumps({"status": "OK", "sessions": []}))
    code, out = final("--usage", other)
    cases.append(("--usage", code == 0 and "ok USAGE" in out and "WARN" not in out, out))
    bad = [name + ": " + tail(out) for name, ok, out in cases if not ok]
    require(not bad, "gate_check --final: %s" % bad)
    # 2.2.5-ds.5: as upstream 2.2.5, --final runs beside the other checks (ds.5 B2 refused that); each prints its own
    # result and any FAIL sets the exit code
    proc = run_tool("gate_check", "--final", director, "--order", director / "x.md")
    require(proc.returncode == 1 and "OK   final" in text_of(proc) and "FAIL order" in text_of(proc),
            "--final beside --order (a missing order): " + tail(text_of(proc)))
    (director / "usage.json").unlink()

    def wrong_with(module):
        got = []
        for name, content in (("missing", None), ("unreadable", "{not json"),
                              ("NO_DATA", json.dumps({"status": "NO_DATA", "reason": "x"}))):
            if content is not None:
                write(director / "usage.json", content)
            lines = module.usage_lines(str(director))
            if module.final_problems(str(director), []) or not any("~ WARN USAGE" in line for line in lines):
                got.append(name)
            if content is not None:
                (director / "usage.json").unlink()
        return got

    wrong = wrong_with(load_tool("gate_check"))
    require(not wrong, "usage_lines() / final_problems() is wrong at %s" % wrong)
    survived = [name for name, swaps in USAGE_MUTATIONS if not wrong_with(mutated("gate_check", swaps))]
    require(not survived, "these usage mutations get nothing wrong: %s" % survived)
    return "no E2E -> FAIL final exit 1; with E2E: missing / unreadable / NO_DATA -> ~ WARN USAGE exit 0, --usage " \
           "file -> ok, beside --order; %d mutations killed" % len(USAGE_MUTATIONS)


# 2.2.5-ds.5 (upstream DW 2.2.5, WO-DW-225): the tests of upstream selftest.py 2.2.5 lines 3948-4770; case tables,
# fixtures and mutations are upstream's word for word, only the harness is DS's (require / expect_tool / mutated).
RVA_LONG225 = "python tools/build_all.py --mode full " + "--x " * 140 + "; python tools/lint.py --all"
RVA_CUT225 = "python tools/pack.py --target beta " + "--y " * 140 + "; python tools/sign.py --all"
# log rows of 2.2.5 (H1 classes of WO-DS-008, de-identified, made-up paths): (HH:MM:SS, agent, tool, input, kind,
# status, tool_raw, cut); session S1 on 2026-11-14 UTC; cut N keeps the first N characters of the command (the
# input stays whole JSON) and marks the row "input_cut", as a tool that cuts inside a field writes it
RVA_225_ROWS = [
    ("00:30:20", "w1", "Bash", {"command": "python -B -m unittest test_a"}, "result", "ok", None, None),
    ("00:40:00", "w1", "Bash", {"command": RVA_LONG225}, "result", "ok", None, None),
    ("00:45:00", "w1", "Bash", {"command": RVA_CUT225}, "result", "ok", None, 200),
    ("01:00:00", "w2", "Bash", {"command": "$env:TEMP='D:\\w\\tmp'; python tools\\evidence_record.py run --out-dir evidence "
                                           "--label AC-1 --order orders\\wo-6.md --cwd D:\\w\\repo -- python -B -m unittest "
                                           "test_b", "workdir": "D:\\w\\DIRECTOR"}, "result", "ok", "pwsh", None),
    ("01:05:00", "w2", "Bash", {"command": "python tools\\scope_check.py --order orders\\wo-6.md --repo D:\\w\\repo --base "
                                           "abc1234 --candidate HEAD --shared", "workdir": "D:\\w\\DIRECTOR"},
     "result", "ok", "pwsh", None),
    ("01:10:00", "w1", "Bash", {"command": 'run(){ python -B "$@"; }\nrun tests/check.py --all'}, "result", "ok", None, None),
    ("01:12:00", "w1", "Bash", {"command": "TMPDIR=/d/w/tmp python -B /d/w/scripts/ac6.py"}, "result", "ok", None, None),
    ("02:00:00", "w3", "Bash", {"command": "cd D:/w/repo; python -B -m unittest test_gas"}, "result", "ok", None, None),
    ("02:01:00", "w3", "Bash", {"command": 'git commit -m "WO-2 gas parser" -- gas.py'}, "result", "ok", None, None),
    ("02:15:00", "lead", "Write", {"file_path": "D:\\w\\DIRECTOR\\GATE_VERDICT_WO-2.md",
                                   "content": "# GATE VERDICT WO-2\n2026-11-14 02:30 | VERDICT | PASS\n"},
     "result", "ok", None, None),
    ("02:20:00", "lead", "Write", {"file_path": "D:\\w\\DIRECTOR\\DIRECTOR_LOG.md",
                                   "content": "2026-11-14 02:00 | GATE | WO-2 late line\n"
                                              "2026-11-14 02:20 | GATE | WO-2 on time\n"}, "result", "ok", None, None)]
RVA_225_VERDICT = "# GATE VERDICT WO-2\n2026-11-14 02:30 | VERDICT | PASS\n"
RVA_225_LOG = "2026-11-14 02:00 | GATE | WO-2 late line\n2026-11-14 02:20 | GATE | WO-2 on time\n"
# (name, report or lead file body ({sha} = the test repo's commit), mode, extra args, exit, says, lacks)
RVA_225_RUNS = [
    ("claude 1: at= span with a full-width ～", "RAN: `python -B -m unittest test_a` exit=0 at=00:30～00:31\n",
     "report", (), 0, ["OK   command: `python -B -m unittest test_a`: seq 1", "PASS claims=1 ok=1"], []),
    ("claude 2: a long uncut call holds its last statement", "RAN: `python tools/lint.py --all` exit=0\n", "report", (),
     0, ["OK   command: `python tools/lint.py --all`: seq 2", "unverified=0"], ["UNVERIFIED"]),
    ("a line rebuilt with input_cut matches on its kept part", "RAN: `python tools/pack.py --target beta` exit=0\n",
     "report", (), 0, ["OK   command: `python tools/pack.py --target beta`: seq 3"], ["UNVERIFIED"]),
    ("a line rebuilt with input_cut is a cut line", "RAN: `python tools/pack.py --target beta ...` exit=0\n"
     "RAN: `python tools/sign.py --all` exit=0\n", "report", (), 0,
     ["UNVERIFIED command: `python tools/sign.py --all`: in log cut part", "unverified=1"], []),
    ("nosdd 6-7: a claim may leave out options; TEMP and the workdir",
     "RAN: `python DIRECTOR/tools/evidence_record.py run --label AC-1 -- python -B -m unittest test_b` exit=0\n",
     "report", (), 0, ["seq 4 also has --out-dir, --order, --cwd, which the claim leaves out", "PASS claims=1 ok=1"], []),
    ("nosdd 8-9: relative paths are read against the workdir",
     "RAN: `python DIRECTOR/tools/scope_check.py --order DIRECTOR/orders/wo-6.md --repo D:/w/repo --base abc1234 "
     "--candidate HEAD --shared` exit=0\n", "report", (), 0, ["OK   command: `python DIRECTOR/tools/scope_check.py",
                                                              "PASS claims=1 ok=1"], []),
    ("a shell function call is its body", "RAN: `python -B tests/check.py --all` exit=0\n", "report", (), 0,
     ["OK   command: `python -B tests/check.py --all`: seq 6"], []),
    ("a Git Bash /d/ path is D:/", "RAN: `python -B D:\\w\\scripts\\ac6.py` exit=0\n", "report", (), 0,
     ["OK   command: `python -B D:\\w\\scripts\\ac6.py`: seq 7"], []),
    ("nosdd 1-4 / 10: a run an hour away is 時間不符",
     "RAN: `cd D:/w/repo; python -B -m unittest test_gas` exit=0 at=03:00\n", "report", (), 1,
     ["at=03:00, but the runs were at", "(類別：時間不符)", "time_mismatch=1 not_run=0"], []),
    ("nosdd 5: another commit message is 沒跑", 'RAN: `git commit -m "WO-2 other text..." -- gas.py` exit=0\n', "report",
     (), 1, ["not run in session S1 (類別：沒跑)", "time_mismatch=0 not_run=1"], []),
    ("tolerance default 10", "RAN: `python -B -m unittest test_a` exit=0 at=00:45\n", "report", (), 1,
     ["(類別：時間不符)"], []),
    ("--tolerance-min widens it", "RAN: `python -B -m unittest test_a` exit=0 at=00:45\n", "report",
     ("--tolerance-min", "20"), 0, ["PASS claims=1 ok=1"], []),
    ("lead: a verdict stamped after the time it was written", RVA_225_VERDICT, "lead", (), 1,
     ["FAIL stamp: lead.md:2 `2026-11-14 02:30`: seq 10 wrote it at", "15 min before the time it states (類別：時間不符)",
      "stamps=1 stamps_unfound=0"], []),
    ("lead: a log line written long after its stamp", RVA_225_LOG, "lead", (), 1,
     ["FAIL stamp: lead.md:1 `2026-11-14 02:00`: seq 11", "20 min after the time it states (tolerance 10)",
      "stamps=2 stamps_unfound=0"], ["lead.md:2"]),
    ("lead: --tolerance-min covers a late line", RVA_225_LOG, "lead", ("--tolerance-min", "30"), 0,
     ["REPORT_VS_AUDIT: PASS", "stamps=2"], ["FAIL"]),
    ("lead: a COMMIT stamp before the commit", "2026-11-14 02:22 | DOC_COMMIT | {sha}\n", "lead_repo", (), 1,
     ["after the time it states (a commit is logged once it is made)", "stamps_unfound=1"], []),
    ("lead: a COMMIT stamp just after the commit", "2026-11-14 02:26 | DOC_COMMIT | {sha}\n", "lead_repo", (), 0,
     ["REPORT_VS_AUDIT: PASS", "stamps=1 stamps_unfound=1"], ["FAIL"]),
    ("lead: a COMMIT stamp long after the commit", "2026-11-14 02:50 | DOC_COMMIT | {sha}\n", "lead_repo", (), 1,
     ["min before the time it states (tolerance 10)"], [])]
# (name, command in the log, claimed command, should match) for matches() in process
RVA_225_CASES = [
    ("a claim may leave out a harmless option", "python tools/gate_check.py --out-dir D:/w/ev --final",
     "python tools/gate_check.py --final", True),
    ("a left-out option that can weaken the run", "python tools/gate_check.py --warn --final",
     "python tools/gate_check.py --final", False),
    ("a left-out option with another value still differs", "python tools/gate_check.py --out-dir D:/w/ev --final --order a",
     "python tools/gate_check.py --final --order b", False),
    ("a claim in another order leaving options out", "python tools/x.py --a 1 --b 2 --c 3", "python tools/x.py --c 3 --a 1",
     False),
    ("TEMP=x in front is left out", "TEMP=D:/w/tmp python tools/x.py --a 1", "python tools/x.py --a 1", True),
    ("TEMP=x does not hide another command", "TEMP=D:/w/tmp python tools/y.py --a 1", "python tools/x.py --a 1", False),
    ("a function call with its arguments", 'f(){ python tools/x.py "$1" --b "$2"; }; f one two',
     "python tools/x.py one --b two", True),
    ("a function call with other arguments", 'f(){ python tools/x.py "$1" --b "$2"; }; f one three',
     "python tools/x.py one --b two", False),
    ("/d/ is D:/", "python /d/w/x.py", "python D:/w/x.py", True),
    ("/d/ is not E:/", "python /d/w/x.py", "python E:/w/x.py", False)]
# (name, swaps, checked by the runs instead of the matcher cases); upstream's 13, each anchor once in report_vs_audit.py
RVA_225_MUTATIONS = [
    ("no ～ span", [("[–—~～〜-]", "[–—~-]")], True),
    ("no TEMP drop", [("    parts = drop_env(parts)\n", "")], False),
    ("no workdir", [('        return next((value[key] for key in ("workdir", "cwd")', '        return next((None '
                     'for key in ("workdir", "cwd")')], True),
    ("no left-out options", [("    return subset and left_out(claim, entry, short) is not None\n",
                              "    return False\n")], True),
    ("left-out options may weaken", [("    for have in log_forms(entry, command):\n        found = "
                                      "omitted_options(words, have.split(\" \"), short)\n",
                                      "    for have in log_forms(entry, command):\n        found = "
                                      "omitted_options(words, have.split(\" \"), short) or [\"x\"]\n")], False),
    ("no shell functions", [("    command = functions(command, env)  # 2.2.5\n", "")], False),
    ("no /d/ drive", [('        parts = [MSYS_DRIVE.sub(r"\\1\\2:/", part) for part in parts]\n', "")], True),
    ("input_cut ignored", [('entry.get("input_cut") is True', "False")], True),
    ("no time class", [('        elif ", but the runs were at " in problem:\n', "        elif False:\n")], True),
    ("no stamp ahead", [("            if ahead > STAMP_AHEAD_MIN:\n", "            if False:\n")], True),
    ("no late stamp", [("            elif late > tolerance:\n", "            elif False:\n")], True),
    ("no commit before stamp", [("                if after < 0:\n", "                if False:\n")], True),
    ("no commit long before", [("                elif after > tolerance:\n", "                elif False:\n")], True)]


def rva225_logs(audit, folder):
    """The 2.2.5 log (hash chain as audit_log.py writes it)."""
    prev, out = audit.GENESIS, []
    for seq, (clock, agent, tool, tool_input, kind, status, raw, limit) in enumerate(RVA_225_ROWS, 1):
        entry = {"seq": seq, "ts": "2026-11-14T%s.000+00:00" % clock, "session_id": "S1", "agent_id": agent, "tool": tool,
                 "tool_use_id": "t%d" % seq, "kind": kind,
                 "input": audit.summary(dict(tool_input, command=tool_input["command"][:limit]) if limit else tool_input,
                                        None),
                 "result": {"status": status}, "duration_ms": None, "prev": prev}
        if raw:
            entry["tool_raw"] = raw
        if limit:
            entry["input_cut"] = True
        entry["hash"] = audit.digest(entry)
        prev = entry["hash"]
        out.append(entry)
    return write(folder / "log.jsonl", "".join(audit.canonical(e) + "\n" for e in out))


def rva225_args(mode, extra, report, log, repo):
    args = ["--lead" if mode.startswith("lead") else "--report", report, "--log", log, "--utc-offset", "+00:00", *extra]
    if mode == "lead_repo":
        args += ["--repo", repo, "--session", "S1"]
    return args


def rva225_runs_wrong(module, reports, log, repo):
    wrong = []
    for (name, _, mode, extra, code, says, lacks), report in zip(RVA_225_RUNS, reports):
        try:
            got, out = call_main(module, *rva225_args(mode, extra, report, log, repo))
        except Exception as error:  # a mutant that crashes is a wrong answer
            wrong.append("%s: crashed %s" % (name, type(error).__name__))
            continue
        if rva223_wrong(name, code, says, lacks, got, out):
            wrong.append(name)
    return wrong


def rva225_matches_wrong(module, audit):
    return [name for name, command, claim, want in RVA_225_CASES
            if bool(module.matches({"command": claim}, {"tool": "Bash", "input": audit.summary({"command": command})}))
            != want]


@test
def report_vs_audit_225(tmp):
    """2.2.5-ds.5 (upstream 2.2.5, WO-DW-225 B2, the H1 classes of WO-DS-008): at= span with ～; a log rebuilt without
    a cut holds a long call whole; a line marked input_cut is a cut line; a claim may leave out harmless options (named
    in a note) but not one that can weaken the run, nor in another order; TEMP=x in front is left out; relative log
    paths are read against the call's workdir; a shell function call is its body; /d/ is D:/; each FAIL names its class
    (時間不符 / 沒跑); --tolerance-min; --lead stamps (and, with --repo, a COMMIT stamp); no Traceback at the top level.
    DS: dsh_audit.py (the DS counterpart of transcript_audit.py) keeps an input whole by default, and build
    --input-limit N cuts it and marks input_cut, which report_vs_audit reads as a cut line."""
    import contextlib
    if shutil.which("git") is None:
        raise Skip("git is not on PATH")
    folder = tmp / "rva225"
    folder.mkdir()
    audit = load_tool("audit_log")
    require(not audit.summary({"command": RVA_LONG225}, None).endswith("\u2026") and "sign.py" not in RVA_CUT225[:200]
            and len(audit.summary({"command": RVA_LONG225})) < len(RVA_LONG225),
            "the long log lines are not whole / cut as the cases need")
    log = rva225_logs(audit, folder)
    repo = folder / "repo"
    repo.mkdir()
    env = dict(os.environ, GIT_COMMITTER_DATE="2026-11-14T02:25:30+00:00", GIT_AUTHOR_DATE="2026-11-14T02:25:30+00:00")
    for args in (["init", "-q"], ["commit", "-q", "--allow-empty", "-m", "doc"]):
        subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args], cwd=repo, check=True,
                       capture_output=True, env=env)
    sha = rgit(repo, "rev-parse", "--short=9", "HEAD")
    reports = []
    for n, (_, body, mode, *_) in enumerate(RVA_225_RUNS):
        if mode.startswith("lead"):
            reports.append(write(folder / ("lead%d" % n) / "lead.md", body.replace("{sha}", sha)))
        else:
            reports.append(write(folder / ("r%d.md" % n), "SESSION_ID: S1\n" + body))
    cli = []
    for (name, _, mode, extra, code, says, lacks), report in zip(RVA_225_RUNS, reports):
        proc = run_tool("report_vs_audit", *rva225_args(mode, extra, report, log, repo))
        if rva223_wrong(name, code, says, lacks, proc.returncode, text_of(proc)):
            cli.append("%s (exit %s): %s" % (name, proc.returncode, tail(text_of(proc), 300)))
    require(not cli, "report_vs_audit CLI gets these 2.2.5 runs wrong: %s" % cli)
    real = load_tool("report_vs_audit")
    wrong = rva225_matches_wrong(real, audit)
    require(not wrong, "report_vs_audit gets these 2.2.5 matcher cases wrong: %s" % wrong)
    wrong = rva225_runs_wrong(real, reports, log, repo)
    require(not wrong, "report_vs_audit in process gets these 2.2.5 runs wrong: %s" % wrong)
    real.main = lambda argv=None: 1 / 0
    err = _Out()
    with contextlib.redirect_stderr(err):
        code = real.entry_point([])
    text = "".join(err.parts)
    require(code == 2 and "Traceback" not in text and "cannot run: ZeroDivisionError" in text,
            "an unexpected error is not one line and exit 2: %s %r" % (code, text))
    survived = []
    for name, swaps, by_runs in RVA_225_MUTATIONS:
        module = mutated("report_vs_audit", swaps)
        if not (rva225_runs_wrong(module, reports, log, repo) if by_runs else rva225_matches_wrong(module, audit)):
            survived.append(name)
    require(not survived, "these 2.2.5 mutations get no case wrong, so the cases do not test them: %s" % survived)
    # DS: the cut row made by dsh_audit.py itself (upstream: transcript_audit.py), then read by report_vs_audit
    rebuild = load_tool("dsh_audit")
    require(rebuild.INPUT_LIMIT is None, "dsh_audit.INPUT_LIMIT is not None (whole input) by default")
    ms = 1794617100000  # 2026-11-14T00:45:00Z
    whole = rebuild.make_entry("S1", "w1", "Bash", "t1", "result", {"command": RVA_CUT225}, "ok", "", None, ms, None)
    require("input_cut" not in whole and "sign.py --all" in whole["input"], "dsh_audit cut a whole input: %r"
            % whole.get("input", "")[-80:])
    rebuild.INPUT_LIMIT = 200
    try:
        cut = rebuild.make_entry("S1", "w1", "Bash", "t1", "result", {"command": RVA_CUT225}, "ok", "", None, ms, None)
    finally:
        rebuild.INPUT_LIMIT = None
    require(cut.get("input_cut") is True and "sign.py" not in cut["input"] and len(cut["input"]) == 200,
            "dsh_audit --input-limit 200 did not cut and mark input_cut: %r" % cut)
    cut = dict(cut, seq=1, prev=audit.GENESIS)
    cut["hash"] = audit.digest(cut)
    ds_log = write(folder / "dsh_cut.jsonl", audit.canonical(cut) + "\n")
    for name, body, says, lacks in (
            ("dsh_audit cut line: kept part", "RAN: `python tools/pack.py --target beta` exit=0\n",
             ["OK   command: `python tools/pack.py --target beta`: seq 1", "PASS claims=1 ok=1"], ["UNVERIFIED"]),
            ("dsh_audit cut line: cut part", "RAN: `python tools/pack.py --target beta ...` exit=0\n"
             "RAN: `python tools/sign.py --all` exit=0\n",
             ["UNVERIFIED command: `python tools/sign.py --all`: in log cut part", "unverified=1"], [])):
        expect_tool(name, "report_vs_audit", 0, "--report", write(folder / "ds_cut.md", "SESSION_ID: S1\n" + body),
                    "--log", ds_log, "--utc-offset", "+00:00", says=says, lacks=lacks)
    expect_tool("dsh_audit --input-limit -1", "dsh_audit", 2, "build", "--out", folder / "never.jsonl",
                "--input-limit", "-1", says="NOT_RUN --input-limit")
    return "%d matcher cases, %d CLI runs (+ in process), entry_point, %d mutations killed; dsh_audit whole / " \
           "--input-limit input_cut read as a cut line" % (len(RVA_225_CASES), len(RVA_225_RUNS), len(RVA_225_MUTATIONS))


def ran_line_run(*args, env=None):
    proc = run_tool("ran_line", *args, env=env)
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def ran_line_wrong(module, folder):
    """In process: the cases a ran_line.py module gets wrong (for the mutation tests)."""
    import contextlib
    import datetime
    wrong = []
    if (folder / "m.md").exists():  # a mutant before may have written it
        (folder / "m.md").unlink()
    clock = datetime.datetime(2026, 11, 14, 2, 59, 50, tzinfo=datetime.timezone.utc)
    if module.ran_line("python -m x", 0, clock, clock + datetime.timedelta(seconds=20)) != "- `python -m x` exit=0 at=02:59-03:00":
        wrong.append("span")
    if module.ran_line("python -m x", 3, clock, clock) != "- `python -m x` exit=3 at=02:59":
        wrong.append("one minute")
    if "`" in module.ran_line("echo `a`", 0, clock)[3:-len("` exit=0 at=02:59")]:
        wrong.append("backtick")
    if module.insert_ran("# R\nRAN:\n- `a` exit=0\n\nNEXT: x\n", "- `b` exit=0") != "# R\nRAN:\n- `a` exit=0\n- `b` exit=0\n\nNEXT: x\n":
        wrong.append("after the RAN block")
    if module.insert_ran("# R\nNEXT: x\n", "- `b` exit=0") != "# R\nNEXT: x\nRAN:\n- `b` exit=0\n":
        wrong.append("new RAN block")
    out = _Out()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(_Out()):
        try:
            code = module.main(["--to", str(folder / "m.md"), "--", str(folder / "no_such_program_225")])
        except Exception:  # a mutant that crashes is a wrong answer
            code = None
    if code != 2 or (folder / "m.md").exists():
        wrong.append("missing program")
    return wrong


RAN_LINE_MUTATIONS = [
    ("no span", [('        at += "-" + end.strftime("%H:%M")\n', "        pass\n")]),
    ("no backtick swap", [('        command = command.replace("`", "\'")\n', "        pass\n")]),
    ("no RAN block end", [("    while end + 1 < len(lines) and RAN_ITEM.match(lines[end + 1]):\n",
                           "    while False:\n")]),
    ("no new RAN block", [('else "\\n") + "RAN:\\n" + line', 'else "\\n") + line')]),
    ("missing program writes", [("            return 2\n        line = ran_line(command_text(command)",
                                 "            code = 2\n        line = ran_line(command_text(command)")])]


@test
def weird_inputs_225(tmp):
    """2.2.5-ds.5 (upstream 2.2.5, WO-DW-225 B7): templates/weird_inputs.py writes the awkward-file set a worker feeds
    its own tool: each file is checked by what it is (bytes, BOM, depth, not UTF-8), not by what the script prints; a
    folder it cannot write gives one line and exit 2, never a Traceback."""
    script = TOOLS.parent / "templates" / "weird_inputs.py"
    out = tmp / "weird_inputs_225"
    done = run_prog(PY_ARGS + [script, out, "--deep", "50", "--long", "7000"])
    require(done.returncode == 0 and "Traceback" not in text_of(done),
            "weird_inputs: exit %s: %s" % (done.returncode, tail(text_of(done), 300)))

    def data(name):
        path = out / name
        return path.read_bytes() if path.is_file() else None

    def not_utf8(raw):
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            return True
        return False

    checks = {
        "empty.txt": lambda b: b == b"",
        "bom.txt": lambda b: b.startswith(b"\xef\xbb\xbf") and len(b) > 3 and b"\n" in b,
        "bom_only.txt": lambda b: b == b"\xef\xbb\xbf",
        "control.txt": lambda b: all(c in b for c in (b"\x00", b"\x07", b"\x1b", b"\x0c", b"\x7f")) and b"\r" in b,
        "long_line.txt": lambda b: len(b) == 7000 and b"\n" not in b,
        "deep.json": lambda b: b == b"[" * 50 + b"]" * 50,
        "deep_parens.txt": lambda b: b.count(b"(") == 50 and b.count(b")") == 50,
        "bad_utf8.txt": not_utf8,
        "utf16.txt": lambda b: b[:2] == b"\xff\xfe" and not_utf8(b),
        "mixed_newlines.txt": lambda b: b"\r\n" in b and b"lf\n" in b and b"\rend" in b,
        "fullwidth.txt": lambda b: "１２３" in b.decode("utf-8") and "\u0301" in b.decode("utf-8"),
    }
    bad = []
    for name, ok in checks.items():
        raw = data(name)
        if raw is None or not ok(raw):
            bad.append("%s: %r" % (name, raw[:60] if raw is not None else "missing"))
    require(not bad, "weird_inputs: these files are not what they should be: %s" % bad)
    blocker = write(tmp / "weird_inputs_225_file", "a file, not a folder\n")
    done = run_prog(PY_ARGS + [script, blocker / "sub"])
    require(done.returncode == 2 and "Traceback" not in text_of(done) and "cannot write" in (done.stdout or ""),
            "weird_inputs: a folder it cannot write gave exit %s: %s" % (done.returncode, tail(text_of(done), 200)))
    return "%d files checked by their bytes; an unwritable folder: one line, exit 2" % len(checks)


@test
def ran_line_225(tmp):
    """2.2.5-ds.5 (upstream 2.2.5, WO-DW-225 B1, B9, A5): ran_line.py writes RAN lines and stamps from the clock: run
    mode returns the command's exit code and records it, record mode (--exit --cmd), --stamp prints / appends
    YYYY-MM-DD HH:MM, the line goes after the RAN: block (a new RAN: block when there is none), a program that cannot
    start writes nothing (exit 2, no Traceback). report_vs_audit.py accepts the line it writes against a log call made
    at that time. With WORK_DIR set the tools put temp files in WORK_DIR/tmp even when TMPDIR names another folder.
    DS has no browser_check.py: use_work_temp() is checked in evidence_record and release only."""
    import datetime
    folder = tmp / "ran_line_225"
    folder.mkdir()
    report = write(folder / "r.md", "# REPORT\nSESSION_ID: S1\nRAN:\n- `python -m old` exit=0\n\nNEXT: x\n")
    code, out, err = ran_line_run("--to", report, "--utc-offset", "+00:00", "--", sys.executable, "-c",
                                  "import sys; sys.exit(3)")
    text = report.read_text(encoding="utf-8")
    require(code == 3 and re.search(r"^- `.+ -c [\"']?import sys; sys\.exit\(3\)[\"']?` exit=3 at=\d\d:\d\d(-\d\d:\d\d)?$", text, re.M)
            and text.index("python -m old") < text.index("exit=3") and text.rstrip().endswith("NEXT: x"),
            "ran_line run mode: exit %s, report %r, stderr %r" % (code, text, err))
    before = datetime.datetime.now(datetime.timezone.utc)
    code, out, err = ran_line_run("--to", report, "--utc-offset", "+00:00", "--exit", "0", "--cmd", "python -m unittest")
    after = datetime.datetime.now(datetime.timezone.utc)
    found = re.search(r"^- `python -m unittest` exit=0 at=(\d\d:\d\d)$", report.read_text(encoding="utf-8"), re.M)
    require(code == 0 and found and found.group(1) in {before.strftime("%H:%M"), after.strftime("%H:%M")},
            "ran_line record mode: exit %s, line %r (clock %s)" % (code, found and found.group(0), before.strftime("%H:%M")))
    # the independent oracle: report_vs_audit reads the line ran_line wrote against a log call made now
    audit = load_tool("audit_log")
    entry = {"seq": 1, "ts": before.isoformat(timespec="milliseconds"), "session_id": "S1", "agent_id": "w1",
             "tool": "Bash", "tool_use_id": "t1", "input": audit.summary({"command": "python -m unittest"}),
             "kind": "result", "result": {"status": "ok"}, "duration_ms": None, "prev": audit.GENESIS}
    entry["hash"] = audit.digest(entry)
    log = write(folder / "log.jsonl", audit.canonical(entry) + "\n")
    oracle = write(folder / "oracle.md", "SESSION_ID: S1\n")
    ran_line_run("--to", oracle, "--utc-offset", "+00:00", "--exit", "0", "--cmd", "python -m unittest")
    expect_tool("ran_line: report_vs_audit accepts the line it writes", "report_vs_audit", 0, "--report", oracle, "--log",
                log, "--utc-offset", "+00:00", says=["OK   command: `python -m unittest`: seq 1", "PASS claims=1 ok=1"])
    code, out, err = ran_line_run("--stamp", "--utc-offset", "+00:00")
    require(code == 0 and re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d\n", out), "ran_line --stamp: exit %s, %r" % (code, out))
    log_md = write(folder / "DIRECTOR_LOG.md", "# log\n")
    code, out, err = ran_line_run("--stamp", "--to", log_md, "--text", "| GATE | WO-1 PASS", "--utc-offset", "+00:00")
    require(code == 0 and re.fullmatch(r"# log\n\d{4}-\d\d-\d\d \d\d:\d\d \| GATE \| WO-1 PASS\n",
                                       log_md.read_text(encoding="utf-8")),
            "ran_line --stamp --to: exit %s, %r" % (code, log_md.read_text(encoding="utf-8")))
    missing = folder / "missing.md"
    code, out, err = ran_line_run("--to", missing, "--", folder / "no_such_program_225")
    require(code == 2 and not missing.exists() and "nothing written" in err and "Traceback" not in err,
            "ran_line: a program that cannot start: exit %s, wrote %s, %r" % (code, missing.exists(), err))
    for name, args in (("no mode", []), ("two modes", ["--stamp", "--exit", "0", "--cmd", "x"]),
                       ("record without --cmd", ["--to", missing, "--exit", "0"]),
                       ("bad offset", ["--stamp", "--utc-offset", "8"])):
        code, out, err = ran_line_run(*args)
        require(code == 2 and "Traceback" not in err, "ran_line %s: exit %s, %r" % (name, code, err))
    # B9 / A5: TMPDIR wins over TEMP in Python; WORK_DIR wins over both in the DW tools
    other = folder / "system_tmp"
    other.mkdir()
    probe = [sys.executable, "-c", "import tempfile; print(tempfile.gettempdir())"]
    env = dict(os.environ, TMPDIR=str(other), TEMP=str(folder), TMP=str(folder))
    env.pop("WORK_DIR", None)
    shown = subprocess.run([sys.executable, "-I", "-c", "import tempfile; print(tempfile.gettempdir())"], env=env,
                           capture_output=True, encoding="utf-8").stdout.strip()
    require(os.path.normcase(shown) == os.path.normcase(str(other)),
            "B9: Python read TEMP before TMPDIR here (%s); the B9 note needs another reason" % shown)
    work = folder / "work"
    work.mkdir()
    code, out, err = ran_line_run("--print", "--", *probe, env={"TMPDIR": str(other), "TEMP": str(folder),
                                                                 "TMP": str(folder), "WORK_DIR": str(work)})
    require(code == 0 and out.splitlines() and os.path.normcase(out.splitlines()[0].strip()) == os.path.normcase(str(work / "tmp")),
            "B9: with WORK_DIR set, ran_line's command did not get WORK_DIR/tmp: %r %r" % (out, err))
    for tool in ("evidence_record", "release"):  # upstream also browser_check, which DS does not have
        module = load_tool(tool)
        saved = {name: os.environ.get(name) for name in ("WORK_DIR", "TMPDIR", "TEMP", "TMP")}
        saved_dir = module.tempfile.tempdir
        try:
            os.environ["WORK_DIR"] = str(work)
            got = module.use_work_temp()
            seen = module.tempfile.gettempdir()
        finally:
            module.tempfile.tempdir = saved_dir
            for name, value in saved.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
        require(os.path.normcase(str(got)) == os.path.normcase(str(work / "tmp"))
                and os.path.normcase(seen) == os.path.normcase(str(work / "tmp")),
                "B9: %s.use_work_temp() gave %s, tempfile %s" % (tool, got, seen))
    wrong = ran_line_wrong(load_tool("ran_line"), folder)
    require(not wrong, "ran_line in process gets these cases wrong: %s" % wrong)
    survived = [name for name, swaps in RAN_LINE_MUTATIONS if not ran_line_wrong(mutated("ran_line", swaps), folder)]
    require(not survived, "these ran_line mutations get no case wrong: %s" % survived)
    return "run / record / --stamp / --stamp --to / missing program / 4 usage errors, report_vs_audit oracle, " \
           "WORK_DIR temp (ran_line, evidence_record, release); %d mutations killed" % len(RAN_LINE_MUTATIONS)


def git225(repo, *args, when=None):
    """git in a 2.2.5 fixture repo; when sets the author and committer date (ISO 8601 with a zone)."""
    env = dict(os.environ, GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when) if when else None
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "core.autocrlf=false",
                           *map(str, args)], cwd=str(repo), check=True, capture_output=True, text=True, encoding="utf-8",
                          env=env).stdout.strip()


def commit225(repo, message, files, when=None):
    for name, text in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git225(repo, "add", "-A")
    git225(repo, "commit", "-q", "--allow-empty", "-m", message, when=when)
    return git225(repo, "rev-parse", "HEAD")


GO225_LOG = """# DIRECTOR_LOG
## 2026-11-14 09:00 +08:00
PLAN_APPROVED WO-003
2026-11-14 10:00 +08:00 | PLAN_APPROVED WO-001
2026-11-14 10:01 +08:00 | SPEC_REVIEW WO-001 tokens=10 issues=1 adopted=1 session=S2
2026-11-14 10:02 +08:00 | SPEC_REVIEW WO-003 tokens=10 issues=0 adopted=0 session=S2
2026-11-14 11:00 +08:00 | PLAN_APPROVED WO-002
2026-11-14 11:01 +08:00 | SPEC_REVIEW WO-002 tokens=1 issues=0 adopted=0 session=S2
2026-11-14 11:02 +08:00 | PLAN_APPROVED WO-006
2026-11-14 11:03 +08:00 | PLAN_APPROVED WO-007
2026-11-14 11:04 +08:00 | PLAN_APPROVED WO-008
2026-11-14 11:05 +08:00 | SPEC_REVIEW WO-008 tokens=1 issues=0 adopted=0 session=S1
2026-11-14 11:06 +08:00 | PLAN_APPROVED WO-009
2026-11-14 11:07 +08:00 | SPEC_REVIEW WO-009 tokens=1 issues=0 adopted=0
2026-11-14 11:08 +08:00 | PLAN_APPROVED WO-011
2026-11-14 11:09 +08:00 | SPEC_REVIEW WO-011 tokens=1 issues=0 adopted=0 session=S2
2026-11-14 12:00 +08:00 | NOTE a later line
2026-11-14 08:00 +08:00 | PLAN_APPROVED WO-004
2026-11-14 12:01 +08:00 | SPEC_REVIEW WO-004 tokens=1 issues=0 adopted=0 session=S2
"""
# what each order must give: the problem kinds (text before the first colon), worked out by hand from the log above
# and the commit times in gate_order_225 (approval time vs the first commit naming the order)
GO225_EXPECTED = {"WO-001": [], "WO-002": ["GATE_ORDER"], "WO-003": [], "WO-004": ["GATE_ORDER"],
                  "WO-005": ["PLAN_APPROVED", "SPEC_REVIEW"], "WO-006": ["SPEC_REVIEW"], "WO-007": [],
                  "WO-008": ["SESSION"], "WO-009": [], "WO-011": ["SESSION"]}
GO225_MUTATIONS = (
    ("no append-only rule", [("if when is not None and latest is not None and",
                              "if False and when is not None and latest is not None and")]),
    ("HEAD only, not every branch", [('"log", "--all", "--format', '"log", "--format')]),
    ("approval after the work passes", [("if approved > at:", "if False:")]),
    ("spec review optional", [('problems.append(f"SPEC_REVIEW: no', 'notes.append(f"SPEC_REVIEW: no')]),
    ("same session passes", [("if theirs and own and theirs == own:", "if False:")]))


def gate_order_wrong(module, orders, log, repo, side):
    """In process: the cases a gate_check module gets wrong for --sequence (for the mutation tests)."""
    wrong = []
    log_text = log.read_text(encoding="utf-8")
    for key, want in GO225_EXPECTED.items():
        path = orders / ("%s.md" % key)
        notes = []
        try:
            problems = module.sequence_problems(path.read_text(encoding="utf-8"), str(path), log_text, str(log),
                                                str(repo), notes)
        except Exception as error:  # a mutant that crashes is a wrong answer
            wrong.append("%s: crashed %s" % (key, type(error).__name__))
            continue
        text = "\n".join(problems + notes)
        if [p.split(":")[0] for p in problems] != want:
            wrong.append("%s: %s" % (key, problems))
        elif key == "WO-002" and side[:10] not in text:
            wrong.append("WO-002: the first commit is on another branch")
        elif key == "WO-003" and "(from the dated heading or line above it)" not in text:
            wrong.append("WO-003: time from the heading")
        elif key == "WO-004" and "append-only" not in text:
            wrong.append("WO-004: a backdated line")
        elif key == "WO-007" and "review file WO-007-SPEC_REVIEW.md" not in text:
            wrong.append("WO-007: review file")
        elif key == "WO-009" and "WARN SESSION: SPEC_REVIEW WO-009: no session id for the reviewer" not in text:
            wrong.append("WO-009: missing session id")
    return wrong


@test
def gate_order_225(tmp):
    """2.2.5-ds.5 (upstream 2.2.5, WO-DW-225 B3, A4): gate_check --sequence. For each Standard / Strict order: the
    PLAN_APPROVED (else DISPATCH) time must not be later than the first commit on any branch whose subject starts with
    the order ID; a line without a time takes the dated heading above it; the log is append-only (a backdated approval
    fails). Every order needs a SPEC_REVIEW log line or a reviews/*SPEC_REVIEW* file; a review from the author's session
    (or a verdict from the task report's session) fails; a missing session id is a WARN note. Direct orders are
    skipped. Expected values are worked out by hand in GO225_EXPECTED."""
    if shutil.which("git") is None:
        raise Skip("git is not on PATH")
    folder = tmp / "gate_order_225"
    repo, director = folder / "repo", folder / "DIRECTOR"
    orders = director / "orders"
    for d in (repo, orders, director / "reviews", director / "gates", director / "reports"):
        d.mkdir(parents=True)
    git225(repo, "init", "-q", "-b", "main")
    commit225(repo, "start", {"a.txt": "0\n"}, when="2026-11-14T08:30:00+08:00")
    git225(repo, "checkout", "-q", "-b", "side")
    side = commit225(repo, "WO-002 early try", {"b.txt": "0\n"}, when="2026-11-14T10:20:00+08:00")
    git225(repo, "checkout", "-q", "main")
    for subject, when in (("WO-003 start", "09:30"), ("WO-001 start", "10:30"), ("WO-002: work", "10:40"),
                          ("WO-004 work", "11:00"), ("WO-005 x", "11:30"), ("WO-006 x", "11:30"), ("WO-007 x", "11:30"),
                          ("WO-008 x", "11:30"), ("WO-009 x", "11:30"), ("WO-010 x", "11:30"), ("WO-011 x", "11:30")):
        # WO-004's commit is written in UTC (git prints ...Z, which Python 3.9's fromisoformat does not take): same
        # moment; if it were skipped its GATE_ORDER FAIL would be missed
        stamp = "2026-11-14T03:00:00+00:00" if subject == "WO-004 work" else "2026-11-14T%s:00+08:00" % when
        commit225(repo, subject, {"a.txt": subject + "\n"}, when=stamp)
    for key in list(GO225_EXPECTED) + ["WO-010"]:
        mode = "Direct" if key == "WO-010" else "Strict" if key == "WO-003" else "Standard"
        write(orders / ("%s.md" % key), "# %s test\nGOVERNANCE = %s\nSESSION_ID: S1\n" % (key, mode))
    write(director / "reviews" / "WO-007-SPEC_REVIEW.md", "# SPEC_REVIEW WO-007\nSESSION_ID: S9\n")
    write(director / "gates" / "WO-001-GATE_VERDICT.md", "SESSION_ID: S3\n")
    write(director / "reports" / "WO-001-TASK_REPORT.md", "SESSION_ID: S5\n")
    write(director / "gates" / "WO-011-GATE_VERDICT.md", "SESSION_ID: S4\n")
    write(director / "reports" / "WO-011-TASK_REPORT.md", "SESSION_ID: S4\n")
    log = write(director / "DIRECTOR_LOG.md", GO225_LOG)
    every = [str(orders / ("%s.md" % key)) for key in sorted(list(GO225_EXPECTED) + ["WO-010"])]
    g = "gate_check"
    expect_tool("gate order 2.2.5: every case", g, 1, "--sequence", *every, "--dispatch-log", log, "--repo", repo,
                says=["OK   sequence %s (GOVERNANCE Standard)" % (orders / "WO-001.md"),
                      "FAIL sequence %s (GOVERNANCE Standard)" % (orders / "WO-002.md"),
                      "OK   sequence %s (GOVERNANCE Strict)" % (orders / "WO-003.md"),
                      "SKIP sequence %s (GOVERNANCE Direct: only Standard / Strict)" % (orders / "WO-010.md"),
                      "  - GATE_ORDER: PLAN_APPROVED WO-002 at 2026-11-14 11:00 +0800 is later than the worker's first "
                      "commit %s" % side[:10], "  - PLAN_APPROVED: no `PLAN_APPROVED WO-005",
                      "  - SPEC_REVIEW: no `SPEC_REVIEW WO-006",
                      "  - SESSION: the SPEC_REVIEW for WO-008 came from session S1, the same as the order's author",
                      "  - SESSION: the GATE_VERDICT for WO-011 came from session S4, the same as the task report's",
                      "  ~ WARN SESSION: SPEC_REVIEW WO-009", "(from the dated heading or line above it)",
                      "comes below a line dated 2026-11-14 12:00"], lacks="Traceback")
    fine = [str(orders / ("%s.md" % key)) for key, want in GO225_EXPECTED.items() if not want]
    expect_tool("gate order 2.2.5: approvals before the work pass", g, 0, "--sequence", *fine, "--dispatch-log", log,
                "--repo", repo, says="OK   sequence", lacks=["FAIL", "Traceback"])
    expect_tool("gate order 2.2.5: --warn reports and exits 0", g, 0, "--sequence", *every, "--dispatch-log", log,
                "--repo", repo, "--warn", says="WARN sequence %s" % (orders / "WO-002.md"), lacks="FAIL")
    expect_tool("gate order 2.2.5: needs --dispatch-log", g, 2, "--sequence", *fine, "--repo", repo)
    expect_tool("gate order 2.2.5: needs --repo", g, 2, "--sequence", *fine, "--dispatch-log", log)
    expect_tool("gate order 2.2.5: a folder that is not a git checkout is NOT_CHECKED, not a pass or a crash", g, 0,
                "--sequence", orders / "WO-001.md", "--dispatch-log", log, "--repo", director,
                says=["~ NOT_CHECKED", "OK   sequence"], lacks="Traceback")
    wrong = gate_order_wrong(load_tool("gate_check"), orders, log, repo, side)
    require(not wrong, "gate order 2.2.5: in process: %s" % wrong)
    survived = [name for name, swaps in GO225_MUTATIONS
                if not gate_order_wrong(mutated("gate_check", swaps), orders, log, repo, side)]
    require(not survived, "these gate order mutations get no case wrong: %s" % survived)
    return "6 CLI checks, %d orders in process, %d mutations killed" % (len(GO225_EXPECTED), len(GO225_MUTATIONS))


@test
def spec_fields_shared_225(tmp):
    """2.2.5-ds.5 (B7, 總監 ruling 3): --match (safety_gate.spec_review_problems) and --sequence
    (gate_check.sequence_problems) check the fields of a `SPEC_REVIEW <WO>` line with one function,
    safety_gate.review_fields_lacking; gate_check keeps no REVIEW_FIELDS of its own. A safety_gate mutant whose function
    finds nothing missing silences the note in both checks."""
    folder = tmp / "spec_fields_shared_225"
    order = write(folder / "orders" / "WO-021.md", "# WO-021 test\nGOVERNANCE = Standard\nSESSION_ID: S1\n")
    log = write(folder / "DIRECTOR_LOG.md", "2026-11-14 10:00 +08:00 | PLAN_APPROVED WO-021\n"
                "2026-11-14 10:01 +08:00 | SPEC_REVIEW WO-021 tokens=1 issues=0 session=S2\n")
    text, log_text = order.read_text(encoding="utf-8"), log.read_text(encoding="utf-8")
    gate, safety = load_tool("gate_check"), load_tool("safety_gate")
    require(safety.review_fields_lacking("tokens=1 issues=0") == ["adopted="]
            and safety.review_fields_lacking("tokens=UNKNOWN issues=0/0/0 adopted=0") == []
            and safety.review_fields_lacking(None) == list(safety.REVIEW_FIELDS),
            "review_fields_lacking: %r" % safety.review_fields_lacking("tokens=1 issues=0"))
    require(not hasattr(gate, "REVIEW_FIELDS"), "gate_check keeps its own REVIEW_FIELDS")

    def both(safety_module):
        """(--match note, --sequence note) about the missing adopted= field, with safety_module as safety_gate."""
        notes = []
        safety_module.spec_review_problems(text, {"WO-021"}, log_text, {}, notes, str(order))
        match = any("WO-021" in n and "has no adopted" in n for n in notes)
        notes = []
        gate.safety_module = lambda: safety_module
        gate.sequence_problems(text, str(order), log_text, str(log), str(folder), notes)
        return match, any("SPEC_REVIEW WO-021: the log line lacks adopted=" in n for n in notes)

    require(both(safety) == (True, True), "the missing adopted= field: (--match, --sequence) = %s" % (both(safety),))
    mutant = mutated("safety_gate", [('    return [key for key in REVIEW_FIELDS if key not in (rest or "")]\n',
                                      "    return []\n")])
    require(both(mutant) == (False, False),
            "a safety_gate mutant that finds no missing field leaves (--match, --sequence) = %s; one of them does "
            "not use review_fields_lacking" % (both(mutant),))
    return "one function for both checks, 1 mutation killed in both"


@test
def after_verdict_225(tmp):
    """2.2.5-ds.5 (upstream 2.2.5, WO-DW-225 B4): gate_check --after-verdict fails by default. A commit after the
    verdict's candidate that changes code (inside SCOPE too) is `~ FAIL LATE_COMMIT` until a new verdict names the new
    candidate; documents (DIRECTOR/, a top-level docs/, .md / .rst / .txt) pass; a candidate that is no longer in
    HEAD's history (the branch was rewritten) is `~ FAIL REWRITTEN`; --warn prints WARN and exits 0."""
    if shutil.which("git") is None:
        raise Skip("git is not on PATH")
    folder = tmp / "after_verdict_225"
    repo, gates, orders = folder / "repo", folder / "DIRECTOR" / "gates", folder / "DIRECTOR" / "orders"
    for d in (repo, gates, orders):
        d.mkdir(parents=True)
    git225(repo, "init", "-q", "-b", "main")
    first = commit225(repo, "start", {"app.py": "a = 1\n"})
    write(orders / "WO-002-app.md", AV224_ORDER)
    cand = commit225(repo, "candidate", {"app.py": "a = 2\n"})
    verdict = write(gates / "WO-002-GATE.md", AV224_VERDICT.format(wo="WO-002", order="WO-002-app.md", head=cand))
    g = "gate_check"
    commit225(repo, "documents", {"docs/diagram.svg": "<svg/>\n", "DIRECTOR/x.json": "{}\n", "notes.MD": "x\n"})
    expect_tool("after-verdict 2.2.5: documents (docs/, DIRECTOR/, .md) pass", g, 0, "--after-verdict", verdict, "--repo",
                repo, says=["OK   AFTER_VERDICT", "is 1 commit(s) later, 0 change files that are not documents"],
                lacks="LATE_COMMIT")
    inside = commit225(repo, "in scope", {"lib/y.py": "y = 1\n"})
    expect_tool("after-verdict 2.2.5: code inside SCOPE after the verdict fails by default", g, 1, "--after-verdict",
                verdict, "--repo", repo, says=["FAIL AFTER_VERDICT", "~ FAIL LATE_COMMIT %s in scope: lib/y.py" % inside[:12],
                                               "a code change needs a new GATE_VERDICT for the new candidate"])
    expect_tool("after-verdict 2.2.5: --warn", g, 0, "--after-verdict", verdict, "--repo", repo, "--warn",
                says=["WARN AFTER_VERDICT", "~ WARN LATE_COMMIT", "--warn, exit unchanged"], lacks="FAIL")
    second = write(gates / "WO-002-GATE-r2.md", AV224_VERDICT.format(wo="WO-002", order="WO-002-app.md", head=inside))
    expect_tool("after-verdict 2.2.5: a new verdict for the new candidate passes", g, 0, "--after-verdict", verdict,
                second, "--repo", repo, says=["OK   AFTER_VERDICT", "HEAD is the candidate"])
    git225(repo, "checkout", "-q", "-b", "rewritten", first)
    again = commit225(repo, "candidate again", {"app.py": "a = 2\n", "lib/y.py": "y = 1\n"})
    expect_tool("after-verdict 2.2.5: a rewritten branch fails", g, 1, "--after-verdict", verdict, second, "--repo", repo,
                says=["FAIL AFTER_VERDICT: no verdict candidate is in the history of HEAD %s" % again[:12],
                      "~ FAIL REWRITTEN %s: CANDIDATE_HEAD %s (candidate)" % (verdict, cand[:12]),
                      "~ FAIL REWRITTEN %s: CANDIDATE_HEAD %s (in scope)" % (second, inside[:12])])
    expect_tool("after-verdict 2.2.5: a rewritten branch with --warn", g, 0, "--after-verdict", verdict, second,
                "--repo", repo, "--warn", says=["WARN AFTER_VERDICT: no verdict candidate", "~ WARN REWRITTEN"])
    old = write(gates / "WO-001-GATE.md", AV224_VERDICT.format(wo="WO-001", order="WO-002-app.md", head=first))
    expect_tool("after-verdict 2.2.5: one candidate kept, one rewritten", g, 1, "--after-verdict", old, second, "--repo",
                repo, says=["FAIL AFTER_VERDICT %s candidate %s" % (old, first[:12]), "~ FAIL LATE_COMMIT %s" % again[:12],
                            "~ FAIL REWRITTEN %s" % second])

    def wrong_with(module):
        try:
            lines, count, _ = module.after_verdict([str(old), str(second)], str(repo), None, True)
        except Exception as error:  # a mutant that crashes is a wrong answer
            return ["crashed %s" % type(error).__name__]
        return [] if count == 2 and any("~ FAIL REWRITTEN" in line for line in lines) else ["%s: %s" % (count, lines)]
    wrong = wrong_with(load_tool("gate_check"))
    require(not wrong, "after-verdict 2.2.5: in process: %s" % wrong)
    require(wrong_with(mutated("gate_check", [("if not leads_to(full, head_sha):", "if False:")])),
            "the mutation 'no rewritten check' gets no case wrong")
    git225(repo, "checkout", "-q", "main")
    return "7 CLI checks, 1 in process, 1 mutation killed"


FINAL225_REGISTER = """# DECISION_REGISTER
## B. 決定
| ID | 日期 | 決定 | 驗收案例 |
|---|---|---|---|
| DD-01 | 2026-11-14 | x | `tool run a.csv` -> 3 rows |
| DD-02 | 2026-11-14 | y |  |
| DD-03 | 2026-11-14 | SUPERSEDED by DD-05 | |

## C. older table
| ID | 日期 | 決定 |
|---|---|---|
| DD-04 | 2026-11-14 | z |
"""
FINAL225_DD_NOTES = ["WARN DD_CASE: DD-02 have no 驗收案例",
                     "WARN DD_CASE: 1 DD row(s) in DECISION_REGISTER.md are in a table without a 驗收案例 column"]
FINAL225_MUTATIONS = (
    ("no E2E rule", [('problems.append(f"E2E: no', 'notes.append(f"E2E: no')]),
    ("an empty file counts", [("p.is_file() and p.stat().st_size > 0", "p.is_file()")]),
    ("SUPERSEDED rows count", [(' or any("SUPERSEDED" in c for c in cells)', "")]))


def final_wrong(module, base):
    """In process: the cases a gate_check module gets wrong for --final (base holds DIRECTOR/ and nothing_here/)."""
    wrong = []
    run_file = base / "DIRECTOR" / "evidence" / "E2E" / "run.txt"
    for name, folder, content, want_problem, want_notes, not_notes in (
            ("no evidence folder", base / "nothing_here", None, True, [], []),
            ("only an empty file", base / "DIRECTOR", None, True, FINAL225_DD_NOTES, ["DD-03"]),
            ("evidence", base / "DIRECTOR", "ENTRY_POINT: python -m tool run\n3 rows\n", False, FINAL225_DD_NOTES,
             ["DD-03", "WARN E2E"])):
        if content is None:
            if run_file.exists():
                run_file.unlink()
        else:
            run_file.write_text(content, encoding="utf-8")
        notes = []
        try:
            problems = module.final_problems(str(folder), notes)
        except Exception as error:  # a mutant that crashes is a wrong answer
            wrong.append("%s: crashed %s" % (name, type(error).__name__))
            continue
        text = "\n".join(notes)
        if bool(problems) != want_problem or any(s not in text for s in want_notes) or any(s in text for s in not_notes):
            wrong.append("%s: %s %s" % (name, problems, notes))
    return wrong


@test
def final_225(tmp):
    """2.2.5-ds.5 (upstream 2.2.5, WO-DW-225 B5, A4): gate_check --final DIR. No non-empty file under evidence/E2E/
    fails; a record without `ENTRY_POINT:` is a WARN note; DD rows of DECISION_REGISTER without a 驗收案例 (or in a
    table without that column) are WARN notes; SUPERSEDED rows are skipped. DIR may be the DIRECTOR folder or the
    folder holding it. (DS adds the usage lines after these: usage_final_225.)"""
    base = tmp / "final_225"
    director = base / "DIRECTOR"
    e2e = director / "evidence" / "E2E"
    e2e.mkdir(parents=True)
    (base / "nothing_here").mkdir()
    write(director / "DECISION_REGISTER.md", FINAL225_REGISTER)
    g = "gate_check"
    expect_tool("final 2.2.5: no E2E evidence fails", g, 1, "--final", director,
                says=["FAIL final", "  - E2E: no end-to-end evidence in"] + FINAL225_DD_NOTES, lacks=["DD-03", "DD-01,"])
    expect_tool("final 2.2.5: the folder holding DIRECTOR/ works too", g, 1, "--final", base,
                says="  - E2E: no end-to-end")
    expect_tool("final 2.2.5: --warn", g, 0, "--final", director, "--warn", says="WARN final")
    write(e2e / "empty.txt", "")
    expect_tool("final 2.2.5: an empty file is no evidence", g, 1, "--final", director, says="  - E2E: no end-to-end")
    run_file = write(e2e / "run.txt", "python -m tool run a.csv\n3 rows\n")
    expect_tool("final 2.2.5: evidence without ENTRY_POINT is a WARN", g, 0, "--final", director,
                says=["OK   final", "~ WARN E2E: no record in", "`ENTRY_POINT:`"])
    run_file.write_text("ENTRY_POINT: python -m tool run\n3 rows\n", encoding="utf-8")
    expect_tool("final 2.2.5: evidence with ENTRY_POINT", g, 0, "--final", director, says="OK   final", lacks="WARN E2E")
    expect_tool("final 2.2.5: a folder that does not exist", g, 2, "--final", base / "nope")
    wrong = final_wrong(load_tool("gate_check"), base)
    require(not wrong, "final 2.2.5: in process: %s" % wrong)
    survived = [name for name, swaps in FINAL225_MUTATIONS if not final_wrong(mutated("gate_check", swaps), base)]
    require(not survived, "these final mutations get no case wrong: %s" % survived)
    return "7 CLI checks, 3 cases in process, %d mutations killed" % len(FINAL225_MUTATIONS)


SC225_ORDER = """# {wo} shared work
BASE_REF = main @ {base}（v2.2.4，註解）
WORKTREE = {worktree}
SCOPE:
- app.py
- lib/**
FORBIDDEN:
- secret.py
"""
SC225_MUTATIONS = (
    ("scope no bracket comment", [('BRACKETED.sub(" ", re.split(r"\\s+#", m.group(1))[0])',
                                   're.split(r"\\s+#", m.group(1))[0]')]),
    ("scope ID not a whole word", [(r'rf"(?<![\w-]){re.escape(i)}(?!\w)"', "re.escape(i)")]),
    ("scope main checkout called isolated",
     [('kind = "共用 checkout（主 checkout）" if same else "隔離 worktree"', 'kind = "隔離 worktree"')]))


@test
def scope_shared_225(tmp):
    """2.2.5-ds.5 (upstream 2.2.5, WO-DW-225 B10, B11; upstream ported DS ds.4 B2): scope_check --shared counts only the
    commits naming the order (a whole-word ID) plus its in-scope uncommitted files; the rest prints OTHER; on by itself
    when WORKTREE says 共用. BASE_REF text in brackets is a comment (scope_check and gate_check --order). A WORKTREE:
    line comes from git worktree list (main checkout = 共用 checkout, linked = 隔離 worktree). A too-long path gives
    one line with the path and how far over 259 it is; a bad --base is NOT_RUN."""
    if shutil.which("git") is None:
        raise Skip("git is not on PATH")
    folder = tmp / "scope_shared_225"
    repo = folder / "repo"
    repo.mkdir(parents=True)
    git225(repo, "init", "-q", "-b", "main")
    base = commit225(repo, "base", {"app.py": "1\n", "other.py": "1\n"})
    mine1 = commit225(repo, "WO-7: app", {"app.py": "2\n"})
    commit225(repo, "WO-8: other worker", {"other.py": "2\n", "secret.py": "x\n"})
    commit225(repo, "WO-70 another order", {"other.py": "3\n"})
    mine2 = commit225(repo, "fix lib (WO-7)", {"lib/a.py": "1\n"})
    write(repo / "lib" / "b.py", "1\n")
    write(repo / "loose.py", "1\n")
    shared = write(folder / "WO-7-shared.md", SC225_ORDER.format(wo="WO-7", base=base, worktree="D:/w/x（共用）"))
    alone = write(folder / "WO-7-alone.md", SC225_ORDER.format(wo="WO-7", base=base, worktree="D:/w/x"))
    s = "scope_check"
    expect_tool("scope 2.2.5: WORKTREE 共用 turns on shared mode; other workers' files are OTHER", s, 0, "--order", shared,
                "--repo", repo, says=["STATES: own_commits=2 own_uncommitted=1", "OTHER     other.py  (shared checkout",
                                      "OTHER     secret.py", "OTHER     loose.py", "WORKTREE: 共用 checkout（主 checkout）",
                                      "SCOPE_CHECK: PASS", "changed=3", "shared=1 others=3"],
                lacks=["FORBIDDEN", "OUTSIDE"])
    expect_tool("scope 2.2.5: without shared mode the whole checkout counts", s, 1, "--order", alone, "--repo", repo,
                says=["FORBIDDEN secret.py", "OUTSIDE   other.py", "SCOPE_CHECK: VIOLATION"], lacks="shared=1")
    expect_tool("scope 2.2.5: --shared turns it on too", s, 0, "--order", alone, "--repo", repo, "--shared",
                says="shared=1 others=3")
    expect_tool("scope 2.2.5: --candidate counts the order's commits up to it", s, 0, "--order", shared, "--repo", repo,
                "--candidate", mine1, says=["STATES: own_commits=1 own_uncommitted=0", "shared=1 others=0"])
    none = write(folder / "WO-9.md", SC225_ORDER.format(wo="WO-9", base=base, worktree="shared"))
    expect_tool("scope 2.2.5: no commit names the order", s, 0, "--order", none, "--repo", repo,
                says="NOTE: SHARED: no commit in", lacks="Traceback")
    commit225(repo, "WO-7 more", {"other.py": "4\n"})
    expect_tool("scope 2.2.5: an out-of-scope file in the order's own commit is OUTSIDE", s, 1, "--order", shared,
                "--repo", repo, says=["OUTSIDE   other.py", "SCOPE_CHECK: VIOLATION"])
    git225(repo, "worktree", "add", "-q", "-b", "side", folder / "wt", mine2)
    expect_tool("scope 2.2.5: a linked worktree says 隔離 worktree", s, 0, "--order", shared, "--repo", folder / "wt",
                says="WORKTREE: 隔離 worktree")
    expect_tool("scope 2.2.5: a bad --base is NOT_RUN, no Traceback", s, 2, "--order", alone, "--repo", repo, "--base",
                "no_such_ref_225", says="SCOPE_CHECK: NOT_RUN", lacks="Traceback")
    # gate_check --order reads the same BASE_REF with the bracket comment (DS order fixture: wo_text, as base_ref_fresh)
    bref = folder / "bref"
    bref.mkdir()
    rgit(bref, "init", "-q", "--bare", "-b", "main", "origin.git")
    rgit(bref / "origin.git", "config", "core.longpaths", "true")  # a local remote ignores GIT_CONFIG_COUNT
    proj = release_clone(bref / "origin.git", bref / "proj")
    proj, lock = wo_fixture(bref, "proj")
    rgit(proj, "add", "-A")
    rgit(proj, "commit", "-q", "-m", "base")
    rgit(proj, "push", "-q", "origin", "HEAD:refs/heads/main")
    sha = rgit(proj, "rev-parse", "--short=7", "HEAD")
    proc, text = wo_run(proj, wo_text(lock).replace("BASE_REF       = main @ abc1234",
                                                    "BASE_REF       = main @ %s（v2.2.4）" % sha))
    require(proc.returncode == 0 and "~ BASE_REF %s = origin/main (fetched now)" % sha in text
            and "WARN BASE_REF" not in text, "BASE_REF 2.2.5: a bracket comment after the commit: " + tail(text))
    # in process: an independent oracle for each part
    root = git225(repo, "rev-parse", "--show-toplevel")
    long_name = "a/" * 140 + "x.txt"
    want_size = len("D:/r/" + long_name)  # computed here, not by the tool: 290
    message = "error: unable to create file %s: Filename too long" % long_name

    def scope_wrong(module):
        got = []
        try:
            if module.order_base(shared.read_text(encoding="utf-8")) != base:
                got.append("BASE_REF bracket")
            if module.own_commits(root, base, "HEAD", ["WO-7"])[:2] != [mine1, mine2]:
                got.append("own commits")
            if not (module.worktree_line(root) or "").startswith("WORKTREE: 共用 checkout"):
                got.append("main checkout")
            if "(%d characters, %d over the 259" % (want_size, want_size - 259) not in (module.long_path(message, "D:/r") or ""):
                got.append("long path")
        except Exception as error:  # a mutant that crashes is a wrong answer
            got.append("crashed %s" % type(error).__name__)
        return got

    def gate_long_wrong(module):
        shown = module.long_path("fatal: cannot create directory at '%s': Filename too long" % long_name, "D:/r")
        if not shown or "D:/r/%s (%d characters, %d over" % (long_name, want_size, want_size - 259) not in shown \
                or module.long_path("fatal: not a git repository", "D:/r") is not None:
            return ["gate_check gave %r" % shown]
        return []
    wrong = scope_wrong(load_tool("scope_check"))
    require(not wrong, "scope 2.2.5: in process: %s" % wrong)
    wrong = gate_long_wrong(load_tool("gate_check"))
    require(not wrong, "long path 2.2.5: %s" % wrong)
    survived = [] if gate_long_wrong(mutated("gate_check", [("if size > WINDOWS_PATH_MAX", "if False")])) \
        else ["long path without the size"]
    survived += [name for name, swaps in SC225_MUTATIONS if not scope_wrong(mutated("scope_check", swaps))]
    require(not survived, "these scope 2.2.5 mutations get no case wrong: %s" % survived)
    return "8 scope_check CLI checks, BASE_REF bracket in gate_check --order, 4 parts in process, %d mutations killed" \
        % (len(SC225_MUTATIONS) + 1)


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


# 2.2.3-ds.3: upstream 2.2.3 report_vs_audit (L-052, L-054); the cases are upstream selftest.py test_report_vs_audit_223
RVA_MULTI = "python -m unittest tests.test_calc -v\ngit status --short"
RVA_EVIDENCE = "python tools/evidence_record.py run --order D:/w/orders/wo-9.md --label {} -- python -m unittest tests.test_a"
RVA_GATE = "python tools/gate_check.py --hash D:/w/orders/wo-003-expression.md"
RVA_SCOPE = "python tools/scope_check.py --candidate 427fcef0123456789abcdef --base main"
RVA_CUT = "python tools/build_all.py --mode full --target alpha " + "--x " * 140
# (name, tool, command in the log, claimed command, should match) for matches() in process
RVA_223_CASES = [
    ("statements in order", "Bash", RVA_MULTI, "python -m unittest tests.test_calc -v; git status --short", True),
    ("statements out of order", "Bash", RVA_MULTI, "git status --short; python -m unittest tests.test_calc -v", False),
    ("&& ends a statement like a new line", "Bash", "git status --short && python -m unittest tests.test_calc -v",
     "git status --short\npython -m unittest tests.test_calc -v", True),
    ("words do not run across a statement end", "Bash", RVA_MULTI, "tests.test_calc -v git status", False),
    ("a claim with ... skips log options", "Bash", RVA_EVIDENCE.format("AC-1"), "evidence_record.py run --label AC-1 ...",
     True),
    ("a full claim does not skip log options", "Bash", RVA_EVIDENCE.format("AC-1"), "evidence_record.py run --label AC-1",
     False),
    ("x... matches a word that starts with x", "Bash", RVA_SCOPE, "scope_check.py --candidate 427fcef...", True),
    ("x... with another start", "Bash", RVA_SCOPE, "scope_check.py --candidate 9999abc...", False),
    ("a bare name matches a file name that starts with it", "Bash", RVA_GATE, "gate_check.py --hash wo-003 ...", True),
    ("a bare name must end at - _ or .", "Bash", RVA_GATE, "gate_check.py --hash wo-00 ...", False),
    ("a CJK-only word (同上) skips words", "Bash", RVA_GATE, "gate_check.py --hash 同上", True),
    ("同上 with one real word proves nothing", "Bash", RVA_GATE, "gate_check.py 同上", False),
    ("3 claim words reach the end of a cut line", "Bash", RVA_CUT, "build_all.py --mode full ... out.txt", True),
    ("2 claim words at the end of a cut line are not enough", "Bash", RVA_CUT, "build_all.py --mode ... out.txt", False),
    ("a line that is not cut does not match past its end", "Bash", "python tools/build_all.py --mode full --target alpha",
     "build_all.py --mode full ... out.txt", False)]
# log rows: (minute, agent, command, kind, status); session S1, 2026-11-14 03:MM UTC
RVA_223_ROWS = [
    (1, "w1", RVA_MULTI, "result", "ok"),
    (5, "w1", RVA_EVIDENCE.format("AC-1"), "result", "ok"),
    (6, "w1", RVA_EVIDENCE.format("AC-2"), "result", "ok"),
    (10, "w1", RVA_GATE, "failure", "error"),
    (20, "w1", RVA_GATE, "result", "ok"),
    (30, "w1", RVA_SCOPE, "result", "ok"),
    (40, "w1", "git -C D:/w commit -m fix", "result", "ok")]
RVA_223_LOGS = {
    "late_commit": RVA_223_ROWS + [(50, "w2", "git commit -m other", "result", "ok")],
    "checked": RVA_223_ROWS + [(45, "w1", RVA_SCOPE, "result", "ok"), (50, "w2", "git commit -m other", "result", "ok")]}
# (name, report body after SESSION_ID: S1, log, exit, says, lacks)
RVA_223_RUNS = [
    ("two statements in one claim", "RAN: `python -m unittest tests.test_calc -v; git status --short` exit=0\n",
     "late_commit", 0, ["seq 1 at", "PASS claims=1 ok=1"], []),
    ("a ``` block under RAN is one claim", "RAN:\n```\npython -m unittest tests.test_calc -v\ngit status --short\n```"
     " exit=0\n", "late_commit", 0, ["PASS claims=1 ok=1"], []),
    ("an unclosed ``` block is no claim", "RAN:\n```\ngit status --short\n", "late_commit", 0,
     ["REPORT_VS_AUDIT: NONE claims=0"], []),
    ("exit of a statement that is not the last: not checkable", "RAN: `python -m unittest tests.test_calc` exit=1\n",
     "late_commit", 0, ["not checkable: seq 1 goes on with other statements", "PASS claims=1 ok=1"], []),
    ("exit of the last statement is still checked", "RAN: `git status --short` exit=1\n", "late_commit", 1,
     ["exit=1, but the log says ok (seq 1)"], ["not checkable"]),
    ("at= ends at the time; the nearest run is shown", "RAN: `tools/gate_check.py --hash wo-003 ...` at=03:12（重跑）\n",
     "late_commit", 0, ["`: seq 4 at", "PASS claims=1 ok=1"], []),
    ("a full-width note in the claim is left out", "RAN: `python -m unittest tests.test_calc -v（第二次）` exit=0\n",
     "late_commit", 0, ["PASS claims=1 ok=1"], []),
    ("AC-1/AC-2 needs one run per ID", "RAN: `evidence_record.py run ... --label AC-1/AC-2` exit=0\n", "late_commit", 0,
     ["seq 2, 3 at", "PASS claims=1 ok=1"], []),
    ("AC-1/2 is the same list", "RAN: `evidence_record.py run ... --label AC-1/2` exit=0\n", "late_commit", 0,
     ["seq 2, 3 at"], []),
    ("AC-1..AC-3 names the missing ID", "RAN: `evidence_record.py run ... --label AC-1..AC-3` exit=0\n", "late_commit",
     1, ["`evidence_record.py run ... --label AC-3`: not run in session S1"], ["AC-1`: not run", "AC-2`: not run"]),
    ("a RAN line with no `command` is a shadow WARN", "RAN:\n- 三支鎖定測試 sha256 比對\n", "late_commit", 0,
     ["WARN ran: a RAN line with no `command`", "三支鎖定測試", "REPORT_VS_AUDIT: NONE"], []),
    ("SCOPE_CHECK PASS before the agent's last commit: shadow WARN",
     "SCOPE_CHECK: PASS\nRAN: `scope_check.py --candidate 427fcef...` exit=0\n", "late_commit", 0,
     ["WARN scope_check:", "agent w1 committed last at seq 7", "its last scope_check.py run is seq 6",
      "(shadow, exit code unchanged)", "PASS claims=1 ok=1"], []),
    ("scope_check after the agent's last commit: no WARN (another agent's commit does not count)",
     "SCOPE_CHECK: PASS\nRAN: `scope_check.py --candidate 427fcef...` exit=0\n", "checked", 0, ["PASS claims=1 ok=1"],
     ["WARN scope_check"]),
    ("no SCOPE_CHECK PASS line: no WARN", "RAN: `scope_check.py --candidate 427fcef...` exit=0\n", "late_commit", 0,
     ["PASS claims=1 ok=1"], ["WARN scope_check"])]
# (name, swaps, checked by the runs instead of the matcher cases); each anchor must occur once in report_vs_audit.py
RVA_223_MUTATIONS = [
    ("no statement split", [('SEPARATOR = re.compile(r"\\r?\\n|\\r|;|&&|\\|\\|")', 'SEPARATOR = re.compile(r"(?!)")')],
     False),
    ("no option skip", [('            if not found and short and log[li].startswith("-"):\n',
                         "            if False:\n")], False),
    ("no x... prefix", [("        return log_word.startswith(found.group(1)) or base.startswith(found.group(1))\n",
                         "        return False\n")], False),
    ("no bare-name prefix", [('    return base.startswith(claim_word) and len(base) > len(claim_word) and '
                              'base[len(claim_word)] in "-_."\n', "    return False\n")], False),
    ("no CJK placeholder", [('PLACEHOLDER = re.compile(r"^[\\u2e80', 'PLACEHOLDER = re.compile(r"^(?!)[\\u2e80')],
     False),
    ("no cut-end match", [("            found = cut and long_enough and n >= CUT_WORDS  #",
                           "            found = False  #")], False),
    ("cut-end match from 2 words", [("CUT_WORDS = 3  #", "CUT_WORDS = 2  #")], False),
    ("no ``` block", [('        if field == "RAN" and FENCE.match(line) and not FIELD.match(line):\n',
                       "        if False:\n")], True),
    ("no not-checkable exit", [('    return not hits or ";" in have[hits[-1] + 1:]\n', "    return False\n")], True),
    ("at= takes the note too", [('AT = re.compile(r"\\bat=([^\\s（(，,；;]+)")', 'AT = re.compile(r"\\bat=(\\S+)")')],
     True),
    ("the last run, not the nearest", [("reverse=True)  # nearest last", "reverse=False)  # nearest last")], True),
    ("no note strip", [('    words = re.split(r"(\\s+)", ANNOTATION.sub(" ", command).strip())\n',
                        '    words = re.split(r"(\\s+)", command.strip())\n')], True),
    ("no ID list", [("        if ids:\n", "        if False:\n")], True),
    ("no RAN WARN", [("                loose.append(rest.strip())\n", "                pass\n")], True),
    ("scope WARN for any agent", [('        pool = [e for e in mine if e.get("agent_id") == agent]\n',
                                   "        pool = mine\n")], True),
    ("scope WARN never", [("    if later:\n", "    if True:\n")], True)]


def rva223_matches_wrong(module, audit):
    return [name for name, tool, command, claim, want in RVA_223_CASES
            if bool(module.matches({"command": claim}, {"tool": tool, "input": audit.summary({"command": command})})) != want]


def rva223_wrong(name, code, says, lacks, got, out):
    return got != code or any(s not in out for s in says) or any(s in out for s in lacks)


def rva223_runs_wrong(module, reports, logs):
    wrong = []
    for (name, _, log, code, says, lacks), report in zip(RVA_223_RUNS, reports):
        try:
            got, out = call_main(module, "--report", report, "--log", logs[log], "--utc-offset", "+00:00")
        except Exception as error:  # a mutant that crashes is a wrong answer
            wrong.append("%s: crashed %s" % (name, type(error).__name__))
            continue
        if rva223_wrong(name, code, says, lacks, got, out):
            wrong.append(name)
    return wrong


@test
def matching_223(tmp):
    audit = load_tool("audit_log")
    require(audit.summary({"command": RVA_CUT}).endswith("\u2026"), "the RVA_CUT log line is not cut, so it tests nothing")
    folder = tmp / "rva223"
    logs = {}
    for log_name, rows in RVA_223_LOGS.items():
        prev, out = audit.GENESIS, []
        for seq, (minute, agent, command, kind, status) in enumerate(rows, 1):
            entry = {"seq": seq, "ts": "2026-11-14T03:%02d:00.000+00:00" % minute, "session_id": "S1",
                     "agent_id": agent, "tool": "Bash", "tool_use_id": "t%d" % seq,
                     "input": audit.summary({"command": command}), "kind": kind, "result": {"status": status},
                     "duration_ms": None, "prev": prev}
            entry["hash"] = audit.digest(entry)
            prev = entry["hash"]
            out.append(audit.canonical(entry))
        logs[log_name] = write(folder / (log_name + ".jsonl"), "".join(line + "\n" for line in out))
    reports = [write(folder / ("r%d.md" % n), "SESSION_ID: S1\n" + body) for n, (_, body, *_) in enumerate(RVA_223_RUNS)]
    cli = []
    for (name, _, log, code, says, lacks), report in zip(RVA_223_RUNS, reports):
        proc = run_tool("report_vs_audit", "--report", report, "--log", logs[log], "--utc-offset", "+00:00")
        if rva223_wrong(name, code, says, lacks, proc.returncode, text_of(proc)):
            cli.append("%s (exit %s): %s" % (name, proc.returncode, tail(text_of(proc), 300)))
    require(not cli, "report_vs_audit CLI gets these 2.2.3 runs wrong: %s" % cli)
    real = load_tool("report_vs_audit")
    wrong = rva223_matches_wrong(real, audit)
    require(not wrong, "report_vs_audit gets these 2.2.3 matcher cases wrong: %s" % wrong)
    wrong = rva223_runs_wrong(real, reports, logs)
    require(not wrong, "report_vs_audit in process gets these 2.2.3 runs wrong: %s" % wrong)
    survived = []
    for name, swaps, by_runs in RVA_223_MUTATIONS:
        module = mutated("report_vs_audit", swaps)
        if not (rva223_runs_wrong(module, reports, logs) if by_runs else rva223_matches_wrong(module, audit)):
            survived.append(name)
    require(not survived, "these 2.2.3 mutations get no case wrong, so the cases do not test them: %s" % survived)
    return "%d matcher cases, %d CLI runs (+ in process), %d mutations killed" % (
        len(RVA_223_CASES), len(RVA_223_RUNS), len(RVA_223_MUTATIONS))


# 2.2.3-ds.3: upstream 2.2.3 evidence_record --rerun read-only git (L-055); the commands of upstream selftest.py
# test_trusted_isolation, checked on check_program / git_argv in process (evidence_record.py is upstream's file)
GIT_READ_ONLY = [["git", "diff", "--exit-code", "HEAD~1", "--", "payload.txt"], ["git", "status", "--porcelain"],
                 ["git", "rev-parse", "HEAD"], ["git", "ls-files"], ["git", "log", "--oneline", "-1"],
                 ["git", "show", "--stat", "HEAD"], ["git", "cat-file", "-e", "HEAD"],
                 ["C:/Program Files/Git/cmd/git.exe", "status"]]
GIT_REFUSED = [
    (["git", "push", "origin", "main"], "'push', which is not a read-only git subcommand"),
    (["git", "commit", "--allow-empty", "-m", "x"], "'commit', which is not a read-only git subcommand"),
    (["git", "reset", "--hard", "HEAD~1"], "'reset', which is not a read-only git subcommand"),
    (["git", "checkout", "other"], "'checkout', which is not a read-only git subcommand"),
    (["git"], "which is not a read-only git subcommand"),
    (["git", "-c", "diff.external=x", "diff"], "before the subcommand"),
    (["git", "diff", "--output=out.txt"], "'--output=out.txt', which writes a file"),
    (["git", "diff", "--ext-d"], "which writes a file or runs a program"),
    (["git", "cat-file", "--textconv", "HEAD:payload.txt"], "which writes a file"),
    (["/usr/bin/git", "commit", "-m", "x"], "which is not a read-only git")]
GIT_MUTATIONS = [
    ("git takes the normal program rule", [("    if is_git(command):\n        return read_only_git(command)\n", "")]),
    ("any subcommand", [("    if sub not in READ_ONLY_GIT:\n", "    if False:\n")]),
    ("no write-option check", [('    bad = [arg for arg in command[2:] if writes(arg.split("=", 1)[0])]\n',
                                "    bad = []\n")]),
    ("no cut-short option", [("any(option.startswith(name) for option in GIT_WRITE_OPTIONS)",
                              "name in GIT_WRITE_OPTIONS")])]


def git_rule_wrong(module):
    wrong = []
    for command in GIT_READ_ONLY:
        try:
            module.check_program(command)
        except module.Refused as why:
            wrong.append("%s refused: %s" % (" ".join(command), why))
    for command, says in GIT_REFUSED:
        try:
            module.check_program(command)
            wrong.append("%s allowed" % " ".join(command))
        except module.Refused as why:
            if says not in str(why):
                wrong.append("%s: %s" % (" ".join(command), why))
    return wrong


@test
def evidence_git_223(tmp):
    module = load_tool("evidence_record")
    wrong = git_rule_wrong(module)
    require(not wrong, "evidence_record read-only git rule gets these wrong: %s" % wrong)
    argv = module.git_argv(["git", "diff", "--exit-code", "HEAD"])
    for flag in ("--no-pager", "core.useReplaceRefs=false", "core.fsmonitor=false", "--no-optional-locks",
                 "--no-ext-diff", "--no-textconv"):
        require(flag in argv, "git_argv lacks %s: %s" % (flag, argv))
    require(argv.index("diff") < argv.index("--no-ext-diff") and argv[-2:] == ["--exit-code", "HEAD"],
            "git_argv puts the options in the wrong place: %s" % argv)
    require("--no-ext-diff" not in module.git_argv(["git", "status"]), "git_argv adds diff options to git status")
    try:
        module.check_program(["hostname"])
        require(False, "a bare program name other than git was allowed")
    except module.Refused as why:
        require("a bare name the PATH would resolve" in str(why), "bare name refused for another reason: %s" % why)
    survived = [name for name, swaps in GIT_MUTATIONS if not git_rule_wrong(mutated("evidence_record", swaps))]
    require(not survived, "these read-only git mutations get no case wrong: %s" % survived)
    return "%d allowed, %d refused, git_argv flags, %d mutations killed" % (
        len(GIT_READ_ONLY), len(GIT_REFUSED), len(GIT_MUTATIONS))


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
     lambda old: old.replace('[\n  "PO_PENDING.md"\n ]', '"PO_PENDING.md"'), "po_pending_files: a list"),
    # 2.2.2-ds.3 (upstream 2.2.2 setup_check): RESUME_STATE size, the resume / base_ref / release blocks
    ("an oversized RESUME_STATE", "RESUME_STATE.md",
     lambda old: old + "- 2026-11-01 filler line\n" * 1000, "RESUME_STATE: RESUME_SIZE"),
    ("resume keep_recent 0", "director_work.json",
     lambda old: old.replace('"schema_version": 1', '"schema_version": 1, "resume": {"keep_recent": 0}'),
     "resume.keep_recent: a whole number above 0"),
    ("resume max_bytes as text", "director_work.json",
     lambda old: old.replace('"schema_version": 1', '"schema_version": 1, "resume": {"max_bytes": "20480"}'),
     "resume.max_bytes: a whole number above 0"),
    ("base_ref strict as text", "director_work.json",
     lambda old: old.replace('"schema_version": 1', '"schema_version": 1, "base_ref": {"strict": "yes"}'),
     "base_ref.strict: true or false"),
    ("a release key release.py refuses", "director_work.json",
     lambda old: old.replace('"schema_version": 1', '"schema_version": 1, "release": {"remot": "origin"}'),
     "release.remot: release.py does not read it"),
    ("release gh_repo without owner", "director_work.json",
     lambda old: old.replace('"schema_version": 1', '"schema_version": 1, "release": {"gh_repo": "director-work"}'),
     "release.gh_repo: owner/name or null")]


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
    data.update(window=250000, colour="blue", sdd={}, resume={"keep_days": 3}, base_ref={"strct": True})
    write(notes / "director_work.json", json.dumps(data, indent=1) + "\n")
    write(notes / "PO_PENDING.md", (notes / "PO_PENDING.md").read_text(encoding="utf-8")
          .replace("CREATED: 2026-11-13 10:00\n", "") + "\nID: CH-003\nSTATUS: open\n")
    proc = run_tool("dsh_setup_check", "--strict", notes)
    text = text_of(proc)
    warn = "\"sdd\" 區塊是空的"
    require("keys no tool reads: colour (a typo?)" in text and "sdd" not in text.split("keys no tool reads: ")[-1]
            and text.count(warn) == 1, "an empty sdd block: not one WARN, or called a typo: " + tail(text))
    for said in ("Claude-only keys the DSH edition does not read: window", "keys no tool reads: colour",
                 "resume keys no tool reads: keep_days", "base_ref key no tool reads: strct",
                 "ACT-002 (line", "no CREATED line", "`ID: CH-003` is not OD-xx / ACT-xx"):
        require(said in text, "expected the note %r: %s" % (said, tail(text)))
    require(proc.returncode == 0, "notes alone failed --strict: " + tail(text))
    example = load_tool("dsh_setup_check")
    notes_found = []
    problems = example.shadow_config((TOOLS.parent / "director_work.example.json").read_text(encoding="utf-8"),
                                     notes_found)
    require(problems == [] and notes_found == [], "director_work.example.json is not clean for dsh_setup_check: "
            "%s %s" % (problems, notes_found))
    return "clean PASS --strict, %d cases shadow then FAIL --strict, 7 notes, example config clean" % len(SHADOW_CASES)


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
    rgit(base / "origin.git", "config", "core.longpaths", "true")  # 2.2.4: a local remote ignores GIT_CONFIG_COUNT
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
    # 2.2.3-ds.3 (總監 ruling WO-DS-005 C): the (upstream, ds) pair as a whole. After v2.2.2-ds.3: 2.2.3-ds.3 (same
    # serial, higher upstream) passes; 2.2.2-ds.2 (lower) and 2.2.2-ds.3 (the tag exists) stop
    rgit(other, "tag", "-a", "v2.2.2-ds.3", "-m", "v2.2.2-ds.3")
    rgit(other, "push", "-q", "origin", "refs/tags/v2.2.2-ds.3")
    pair = release_clone(origin, base / "pair")
    release_commit(pair, "2.2.3-ds.3")
    code, out = release(pair)
    require(code == 0 and "STEP version: OK 2.2.3-ds.3" in out and "v2.2.3-ds.3 is new" in out,
            "2.2.3-ds.3 after v2.2.2-ds.3 was stopped: " + tail(out))
    lower = release_clone(origin, base / "lower")
    release_commit(lower, "2.2.2-ds.2")
    code, out = release(lower)
    require(code == 1 and "does not sort above the remote tag(s) v2.2.2-ds.3" in out,
            "2.2.2-ds.2 after v2.2.2-ds.3 was not stopped: " + tail(out))
    same = release_clone(origin, base / "same")
    release_commit(same, "2.2.2-ds.3")
    code, out = release(same)
    require(code == 1 and "tag v2.2.2-ds.3 is already on the remote" in out,
            "2.2.2-ds.3 again (tag exists) was not stopped: " + tail(out))
    flags = run_tool("release", "--help").stdout
    usage = flags.split("\n\n")[0]  # the argparse usage block: the options release.py takes
    require("--execute" in usage and not re.search(r"\[--(force|skip|no-|allow|ignore)", usage),
            "release.py has a flag that skips a check: " + usage)
    return "BEHIND, DIVERGED (+ --merge conflict a.txt), AHEAD, version order, (upstream, ds) pair: 2.2.3-ds.3 OK, " \
           "2.2.2-ds.2 / 2.2.2-ds.3 stop, uncommitted VERSION and CHANGELOG mismatch"


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
    rgit(base / "origin.git", "config", "core.longpaths", "true")  # 2.2.4: a local remote ignores GIT_CONFIG_COUNT
    proj = release_clone(base / "origin.git", base / "proj")
    repo, lock = wo_fixture(base, "proj")
    rgit(proj, "add", "-A")
    rgit(proj, "commit", "-q", "-m", "base")
    rgit(proj, "push", "-q", "origin", "HEAD:refs/heads/main")
    sha = rgit(proj, "rev-parse", "--short=7", "HEAD")

    def order(ref):
        return wo_text(lock).replace("BASE_REF       = main @ abc1234",
                                                                        "BASE_REF       = " + ref)

    proc, text = wo_run(repo, order("origin/main @ " + sha))
    require(proc.returncode == 0 and "BASE_REF %s = origin/main (fetched now)" % sha in text,
            "an up-to-date BASE_REF was not confirmed after a fetch: " + tail(text))
    other = release_clone(base / "origin.git", base / "other")
    write(other / "later.txt", "x\n")
    rgit(other, "add", "later.txt")
    rgit(other, "commit", "-q", "-m", "later")
    rgit(other, "push", "-q", "origin", "HEAD:refs/heads/main")
    proc, text = wo_run(repo, order("origin/main @ " + sha))
    require(proc.returncode == 0 and "~ WARN BASE_REF: %s is 1 commit(s) behind origin/main" % sha in text,
            "a BASE_REF behind origin/main was not a WARN note: " + tail(text))
    proc, text = wo_run(repo, order("origin/main @ " + sha), "--strict-base")
    require(proc.returncode == 1 and "  - BASE_REF: %s is 1 commit(s) behind" % sha in text,
            "--strict-base did not fail a stale BASE_REF: " + tail(text))
    write(repo / "director_work.json", '{"base_ref": {"strict": "yes"}}')
    proc, text = wo_run(repo, order("origin/main @ " + sha))
    require(proc.returncode == 0 and "base_ref.strict: true or false, got 'yes'; false used" in text
            and "WARN BASE_REF" in text, "a base_ref switch of the wrong type was not a note: " + tail(text))
    (repo / "director_work.json").unlink()
    proc, text = wo_run(repo, order("origin/main @ deadbee"))
    require(proc.returncode == 0 and "WARN BASE_REF: commit deadbee does not exist" in text,
            "a BASE_REF commit that does not exist was not noted: " + tail(text))
    rgit(proj, "remote", "set-url", "origin", str(base / "gone.git"))
    proc, text = wo_run(repo, order("origin/main @ " + sha))
    require(proc.returncode == 0 and "WARN BASE_REF: not compared with the remote: git fetch origin failed" in text,
            "a failed fetch was not said out loud: " + tail(text))
    proc, text = wo_run(repo, order("origin/main @ " + sha), "--strict-base")
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
        ("Claude local settings", {".claude/settings.local.json": "{}\n"}, None, ".claude/settings.local.json"),
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
    # this test is about the report, not the safety gates: the order's folder config turns tests_first off, which
    # 2.2.5-ds.5 allows only with the PO's answer in PO_PENDING.md (safety_switch_off_225)
    write(root / "DIRECTOR" / "director_work.json",
          json.dumps({"schema_version": 1, "safety": {"tests_first": False}}) + "\n")
    write(root / "DIRECTOR" / "PO_PENDING.md", "ID: OD-1\nSTATUS: answered\nQUESTION: turn tests_first off for the "
          "report selftest?\nOPTIONS: a) yes b) no\nRECOMMENDED: a\nSOURCE: selftest\nANSWER: a) yes\n")
    write(root / "DIRECTOR" / "DIRECTOR_LOG.md", "2026-11-14 09:05 | SPEC_REVIEW WO-8 tokens=UNKNOWN issues=0/0/0 "
          "adopted=0\n")
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


RESUME_OK = ("PROGRESS: 1\nDOING: 2\nNEXT_STEP: 3\nCOMMS: NONE\n\n# RESUME_STATE\n"
             "UPDATED: 2026-11-14 03:00 +08:00\n")


class _Out:
    """stdout for an in-process main(): the tools call sys.stdout.reconfigure."""
    def __init__(self):
        self.parts = []

    def write(self, text):
        self.parts.append(text)
        return len(text)

    def flush(self):
        pass

    def reconfigure(self, **_):
        pass


def call_main(module, *args):
    import contextlib
    out = _Out()
    with contextlib.redirect_stdout(out):
        try:
            code = module.main([str(a) for a in args])
        except SystemExit as stop:
            code = stop.code
    return code, "".join(out.parts)


def expect_tool(name, tool, code, *args, says=(), lacks=()):
    """Run a tool; require its exit code, every text in says and none in lacks."""
    proc = run_tool(tool, *args)
    out = text_of(proc)
    says = [says] if isinstance(says, str) else says
    lacks = [lacks] if isinstance(lacks, str) else lacks
    require(proc.returncode == code, "%s: exit %s, expected %s: %s" % (name, proc.returncode, code, tail(out)))
    for text in says:
        require(text in out, "%s: expected %r: %s" % (name, text, tail(out)))
    for text in lacks:
        require(text not in out, "%s: did not expect %r: %s" % (name, text, tail(out)))
    return out


@test
def resume_size(tmp):
    """2.2.2-ds.3 (upstream 2.2.2): memory_size_check --kind resume (several --file, --glob, --workstreams, movable
    bytes, a config key of the wrong type), gate_check --resume shadow / --strict / limits from config, the example
    config, and two mutations of the size rule."""
    folder = tmp / "resume_size"
    good = write(folder / "a" / "RESUME_STATE.md", RESUME_OK)
    big = write(folder / "a" / "deep" / "RESUME_STATE_big.md", RESUME_OK + "- 2026-11-01 filler line\n" * 1000)
    long_line = write(folder / "long.md", RESUME_OK.replace("DOING: 2", "DOING: " + "x" * 5000))
    m = "memory_size_check"
    expect_tool("a good RESUME_STATE", m, 0, "--kind", "resume", "--file", good,
                says=["OK   ", "(limit 20480)", "movable 0 bytes", "SIZE: PASS files=1 over=0"], lacks="OVER")
    expect_tool("an oversized RESUME_STATE", m, 1, "--kind", "resume", "--file", big,
                says=["OVER ", "over: size", "resume_archive.py", "SIZE: OVER files=1 over=1"])
    expect_tool("one line over 4096 bytes", m, 1, "--kind", "resume", "--file", long_line,
                says=["longest line 2: 5007 bytes (limit 4096)", "over: line", "SIZE: OVER files=1 over=1"],
                lacks="over: size")
    expect_tool("two files, one over", m, 1, "--kind", "resume", "--file", good, "--file", big,
                says=["OK   ", "OVER ", "SIZE: OVER files=2 over=1"])
    expect_tool("--glob reaches subfolders", m, 1, "--kind", "resume", "--glob",
                str(folder / "**" / "RESUME_STATE*.md"), says="SIZE: OVER files=2 over=1")
    expect_tool("--glob with no match is missing", m, 1, "--kind", "resume", "--glob", str(folder / "nope" / "*.md"),
                says=["NO_MATCH", "SIZE: MISSING files=0 over=0 missing=1"])
    registry = write(folder / "ACTIVE_WORKSTREAMS.md",
                     "# 工作線\n\n| 工作線 | RESUME_STATE | 狀態 |\n|---|---|---|\n| A | " + BT + "a/RESUME_STATE.md" + BT
                     + " | open |\n| B | a/deep/RESUME_STATE_big.md | open |\n| C | NONE | closed |\n| D | <path> | new |\n")
    expect_tool("--workstreams reads the RESUME column", m, 1, "--kind", "resume", "--workstreams", registry,
                says="SIZE: OVER files=2 over=1", lacks=["missing", "<path>"])
    write(registry, registry.read_text(encoding="utf-8") + "| E | gone/RESUME_STATE.md | open |\n")
    expect_tool("--workstreams, a registered file that is gone", m, 1, "--kind", "resume", "--workstreams", registry,
                says=["NOT_FOUND", "missing=1"])
    config = write(folder / "cfg.json", '{"resume": {"max_bytes": "big", "max_line_bytes": 20}}')
    expect_tool("a config key of the wrong type is a note, the default is used", m, 1, "--kind", "resume", "--config",
                config, "--file", good,
                says=["resume.max_bytes: a whole number above 0, got 'big'; 20480 used", "(limit 20)", "over: line"])
    expect_tool("--config needs --kind resume", m, 2, "--config", config, "--file", good, "--file", big)
    expect_tool("one --file alone keeps the old report", m, 0, "--file", good, says="OK   RESUME_STATE.md:",
                lacks="SIZE:")
    g = "gate_check"
    expect_tool("gate_check: a small RESUME_STATE has no size note", g, 0, "--resume", good, lacks="RESUME_SIZE")
    expect_tool("gate_check: oversized is a shadow note, exit unchanged", g, 0, "--resume", big,
                says=["shadow: RESUME_SIZE", " tokens, longest line"])
    expect_tool("gate_check: --strict fails on it", g, 1, "--strict", "--resume", big, says="  - RESUME_SIZE",
                lacks="shadow: RESUME_SIZE")
    expect_tool("gate_check: an over-long line is a shadow note", g, 0, "--resume", long_line,
                says="longest line 2: 5007 bytes (limit 4096); over: line")
    write(folder / "a" / "director_work.json", '{"resume": {"max_bytes": 50}}')
    expect_tool("gate_check: limits from the director_work.json beside it", g, 0, "--resume", good,
                says="RESUME_SIZE %d bytes (limit 50)" % len(good.read_bytes()))
    expect_tool("gate_check: --config wins", g, 0, "--resume", good, "--config", config, says="(limit 20); over: line")
    expect_tool("gate_check: --strict needs --resume", g, 2, "--strict", "--order", good)
    real = load_tool("memory_size_check")
    notes = []
    example = json.loads((TOOLS.parent / "director_work.example.json").read_text(encoding="utf-8"))
    got = real.resume_settings(example, notes)
    require(notes == [] and got == {"max_bytes": 20480, "max_line_bytes": 4096, **real.KEEP_DEFAULTS}
            and got["keep_recent"] == 10 and "keep_days" not in got,
            "the example's resume block does not read clean with the defaults: %s %s" % (got, notes))
    for value, name in (('{"resume": {"keep_recent": 0}}', "keep_recent 0"),
                        ('{"resume": {"keep_recent": true}}', "keep_recent true"),
                        ('{"resume": {"protect_headings": "OPEN"}}', "protect_headings a string"),
                        ('{"resume": 5}', "resume a number")):
        notes = []
        got = real.resume_settings(json.loads(value), notes)
        require(len(notes) == 1 and got["keep_recent"] == 10 and got["max_bytes"] == 20480
                and got["protect_headings"][0] == "現況", "%s: expected one note and the defaults: %s %s" % (name, got, notes))
    survived = []
    for name, swaps, args in [
            ("no line limit", [('    if max_line_bytes is not None and facts["longest_bytes"] > max_line_bytes:\n',
                                "    if False:\n")], ("--kind", "resume", "--file", long_line)),
            ("no size limit", [('    over = ["size"] if facts["bytes"] > max_bytes else []\n', "    over = []\n")],
             ("--kind", "resume", "--file", big))]:
        if call_main(mutated("memory_size_check", swaps), *args)[0] == 1:
            survived.append(name)
    require(not survived, "these size-rule mutations were not caught: %s" % survived)
    return "memory_size_check 11 cases, gate_check 7 cases, example config, 2 mutations killed"


ARCHIVE_FIXTURE = (
    "PROGRESS: 進度 1 Before: p1 Before: p2 Before: p3\n"
    "DOING: (11-14 10:00) now Before: (11-14 09:00) e1 Before: (11-13 20:00) e2 Before: (11-12 10:00) e3 "
    "Before: (11-10 10:00) e4 Before: (11-09 10:00) e5\n"
    "NEXT_STEP: (11-14 10:00) next Before: (11-14 09:00) n1 Before: no time n2 Before: (11-20 10:00) n3\n"
    "COMMS: NONE\n"
    "\n# RESUME_STATE — T1\nUPDATED: 2026-11-14 10:00 +08:00\nORDER: x\n"
    "\n## 現況\n- 2026-11-01 current thing\n"
    "\n## 紀錄\n- 2026-11-01 old a\n- 2026-11-02 old b\n  continued b\n- 2026-11-05 old c\n- 2026-11-12 recent one\n"
    "- 2026-11-13 recent two\n- no date item\n- 2026-11-01 BLOCKED: waiting on x\n")
ARCHIVE_MARKERS = ["current thing", "old a", "old b", "old c", "recent one", "recent two", "no date item", "BLOCKED",
                   "p1", "p2", "p3", "e1", "e2", "e3", "e4", "e5", "n1", "n2", "n3"]
# (name, keep_recent, the markers whose text moves). Count only (PO 2026-11-14 10:13): no keep_days.
ARCHIVE_CASES = [
    ("newest 2 stay, older parts and chain entries move", 2, ["old a", "old b", "old c", "p3", "e3", "e4", "e5"]),
    ("newest 1", 1, ["old a", "old b", "old c", "recent one", "p2", "p3", "e2", "e3", "e4", "e5"]),
    ("newest 4: only the oldest section and chain entry", 4, ["old a", "e5"]),
    ("fewer parts than keep_recent: nothing moves", 10, [])]
ARCHIVE_PROTECT = ["現況", "未結", "OPEN", "BLOCKED", "TODO", "待辦", "IN_FLIGHT", "DO_NOT_REPEAT"]


def archive_moved(module, keep_recent, text=ARCHIVE_FIXTURE):
    import datetime
    settings = {"max_bytes": 20480, "max_line_bytes": 4096, "keep_recent": keep_recent,
                "protect_headings": list(ARCHIVE_PROTECT)}
    result = module.plan(text.encode("utf-8"), settings, datetime.date(2026, 11, 14), [])
    return [m for m in ARCHIVE_MARKERS if any(m in u["text"] for u in result["moved"])], result


def archive_wrong(module):
    """Names of the ARCHIVE_CASES a resume_archive module gets wrong (a crash is a wrong answer). Every case also
    needs the NEXT_STEP line (its chain order is unclear) unchanged and the header still the four lines."""
    wrong = []
    for name, keep_recent, want in ARCHIVE_CASES:
        try:
            got, result = archive_moved(module, keep_recent)
            lines = result["new_text"].splitlines()
            if got != want or lines[2] != ARCHIVE_FIXTURE.splitlines()[2] \
                    or [line.split(":")[0] for line in lines[:4]] != ["PROGRESS", "DOING", "NEXT_STEP", "COMMS"]:
                wrong.append(name)
        except Exception:
            wrong.append(name)
    try:  # same day as the last one kept: the order is unclear, both stay
        _, result = archive_moved(module, 1, "A: x\n\n## log\n- 2026-11-01 t1\n- 2026-11-05 t2\n- 2026-11-05 t3\n")
        if [u["text"] for u in result["moved"]] != ["- 2026-11-01 t1\n"]:
            wrong.append("same day as the last one kept")
    except Exception:
        wrong.append("same day as the last one kept")
    try:  # an empty Before: entry: the count is unclear, the whole line stays
        text = "PROGRESS: a Before: b Before: Before: c\nDOING: x\nNEXT_STEP: y\nCOMMS: z\n"
        _, result = archive_moved(module, 1, text)
        if result["moved"] or result["new_text"] != text or not any("is empty, the count is unclear" in n
                                                                      for n in result["notes"]):
            wrong.append("an empty Before: entry")
    except Exception:
        wrong.append("an empty Before: entry")
    return wrong


ARCHIVE_MUTATIONS = [
    ("no keep_recent for sections", [('        if cut is None or unit["date"] >= cut:\n', "        if cut is None:\n")]),
    ("same day as the last kept moves", [('        if cut is None or unit["date"] >= cut:\n',
                                         '        if cut is None or unit in newest[:keep_recent]:\n')]),
    ("no protected heading", [("        elif protect_word(heading, words):\n", "        elif False:\n")]),
    ("no protected word", [("            if word:\n", "            if False:\n")]),
    ("undated parts move", [("word, date = protect_word(part_text, words), latest_date(part_text)\n",
                             "word, date = protect_word(part_text, words), latest_date(part_text) or "
                             "datetime.date(2000, 1, 1)\n")]),
    ("an empty chain entry moves", [("    if empty:\n", "    if False:\n")]),
    ("no keep_recent for chains", [("    cut = starts[keep_recent]  #", "    cut = starts[0]  #")]),
    ("an unclear chain order moves", [("        if why is None and later > earlier:\n", "        if False:\n")])]
ARCHIVE_BREAK = ("        path.write_bytes(new_raw)\n", "        path.write_bytes(new_raw.replace(b'now', b'NOW'))\n")


@test
def resume_archive(tmp):
    """2.2.2-ds.3 (upstream 2.2.2): resume_archive.py moves old parts word for word, by count only; protected and
    undated parts stay, an unclear chain order keeps the whole line, the header stays four lines, dry-run writes
    nothing, --execute writes a .bak and verifies (a) (b) (c), a failed check restores the file and the history;
    8 keep-rule mutations and a no-restore mutation are caught."""
    folder = tmp / "resume_archive"
    folder.mkdir(parents=True)
    wrong = archive_wrong(load_tool("resume_archive"))
    require(not wrong, "resume_archive gets these keep cases wrong: %s" % wrong)
    target = folder / "RESUME_STATE.md"
    target.write_bytes(ARCHIVE_FIXTURE.encode("utf-8"))
    original = target.read_bytes()
    r = "resume_archive"
    common = ("--keep-recent", "2", "--today", "2026-11-14")
    expect_tool("dry-run lists the moves", r, 0, target, *common,
                says=["dry-run, nothing written", "MOVE lines 14-14", "MOVE lines 15-16", "MOVE lines 17-17",
                      "MOVE header PROGRESS Before: entries 3-3", "MOVE header DOING Before: entries 3-5",
                      "KEEP lines 11-11", "protected heading (現況)", "no full date (order unclear, stays)",
                      "protected word (BLOCKED)", "recent (newest 2 dated)",
                      "shadow: RESUME_HEADER line 3 NEXT_STEP: Before: entry 3 is dated after entry 1, the order is unclear",
                      "shadow: RESUME_ORDER 1 part(s)", "ARCHIVE: DRY_RUN movable=5"], lacks="keep_days")
    require(target.read_bytes() == original and sorted(p.name for p in folder.iterdir()) == ["RESUME_STATE.md"],
            "dry-run wrote something: %s" % sorted(p.name for p in folder.iterdir()))
    expect_tool("--keep-days is gone (count only)", r, 2, target, "--keep-days", "3")
    expect_tool("--execute moves and verifies", r, 0, target, "--execute", *common,
                says=["VERIFY (a) OK", "VERIFY (b) OK", "the header is still the same four lines", "VERIFY (c) OK",
                      "  SHA lines 11-11 sha256=", "ARCHIVE: DONE moved=5"])
    new = target.read_text(encoding="utf-8")
    history = folder / "RESUME_HISTORY_20261114.md"
    backups = sorted(folder.glob("RESUME_STATE.md.*.bak"))
    history_text = history.read_text(encoding="utf-8") if history.exists() else ""
    old = ARCHIVE_FIXTURE.splitlines(keepends=True)
    moved = [old[13], old[14] + old[15], old[16], "Before: p3",
             "Before: (11-12 10:00) e3 Before: (11-10 10:00) e4 Before: (11-09 10:00) e5"]
    require(len(backups) == 1 and backups[0].read_bytes() == original, "the .bak is not the original: %s" % backups)
    require(all(part in history_text for part in moved), "the history lacks a moved part: " + tail(history_text))
    require(not any(part in new for part in moved) and new.count("> RESUME_ARCHIVED:") == 3
            and new.count("[RESUME_ARCHIVED:") == 2, "moved parts or indexes wrong: " + tail(new))
    kept = [old[2], old[3], old[10], old[17], old[18], old[19], old[20], "".join(old[5:8])]
    require(all(part in new for part in kept), "a recent, protected, undated part or the unclear chain changed: "
            + tail(new))
    lines = new.splitlines()
    require(lines[1].startswith("DOING: (11-14 10:00) now Before: (11-14 09:00) e1 Before: (11-13 20:00) e2 "
                                "[RESUME_ARCHIVED: 3 older entries | 11-12 | RESUME_HISTORY_20261114.md | sha256=")
            and lines[1].endswith("]")
            and lines[0].startswith("PROGRESS: 進度 1 Before: p1 Before: p2 [RESUME_ARCHIVED: 1 older entries | ? | "),
            "the chain did not keep its newest 2 entries with an index: " + "\n".join(lines[:4]))
    expect_tool("the header still passes gate_check", "gate_check", 0, "--resume", target)
    rebuilt = new
    for part in re.findall(r"<!-- RESUME_ARCHIVE .*? -->\n(.*?)<!-- /RESUME_ARCHIVE -->\n", history_text, re.S):
        found = re.search(r"\[RESUME_ARCHIVED: [^\]]*\]|^> RESUME_ARCHIVED: .*\n", rebuilt, re.M)
        if found:
            back = part.rstrip("\n") if found.group(0).startswith("[") else part
            rebuilt = rebuilt[:found.start()] + back + rebuilt[found.end():]
    require(rebuilt == ARCHIVE_FIXTURE, "history put back at the indexes is not the original: " + tail(rebuilt))
    expect_tool("a second run has nothing to move", r, 0, target, "--execute", *common, says="ARCHIVE: NOTHING_TO_MOVE")
    require(target.read_text(encoding="utf-8") == new and len(list(folder.glob("*.bak"))) == 1,
            "the second run changed something")
    expect_tool("a missing file", r, 2, folder / "nope.md", says="NOT_FOUND")
    latin = folder / "latin.md"
    latin.write_bytes(b"PROGRESS: \xe9\n")
    expect_tool("not UTF-8 is not read", r, 2, latin, "--execute", says="NOT_UTF8")
    require(latin.read_bytes() == b"PROGRESS: \xe9\n", "a not-UTF-8 file was touched")
    for name, history_before in (("a new history", None), ("an existing history", "# old history\n")):
        case = folder / ("restore_%d" % len(name))
        case.mkdir()
        file = case / "RESUME_STATE.md"
        file.write_bytes(original)
        hist = case / "RESUME_HISTORY_20261114.md"
        if history_before:
            write(hist, history_before)
        code, out = call_main(mutated("resume_archive", [ARCHIVE_BREAK]), file, "--execute", *common)
        require(code == 1 and "ARCHIVE: FAIL restored=yes" in out and "VERIFY FAIL" in out
                and file.read_bytes() == original
                and (hist.read_text(encoding="utf-8") == history_before if history_before else not hist.exists())
                and len(list(case.glob("*.bak"))) == 1, "a failed check did not restore (%s): %s" % (name, tail(out)))
    case = folder / "no_restore"
    case.mkdir()
    (case / "RESUME_STATE.md").write_bytes(original)
    no_restore = mutated("resume_archive", [ARCHIVE_BREAK, ("        path.write_bytes(backup.read_bytes())\n",
                                                           "        pass\n")])
    require("restored=yes" not in call_main(no_restore, case / "RESUME_STATE.md", "--execute", *common)[1],
            "a resume_archive that does not restore still said restored=yes")
    survived = [name for name, swaps in ARCHIVE_MUTATIONS if not archive_wrong(mutated("resume_archive", swaps))]
    require(not survived, "these keep-rule mutations get no case wrong: %s" % survived)
    return "%d keep cases, dry-run / execute / verify / restore, %d mutations killed" % (
        len(ARCHIVE_CASES) + 2, len(ARCHIVE_MUTATIONS) + 1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--verbose", action="store_true", help="print full detail for passing tests too")
    parser.add_argument("--keep", action="store_true", help="keep the temp folder (printed at the end)")
    parser.add_argument("--only", help="2.2.4-ds.4: run only these tests (comma-separated names); the summary line "
                        "then says ONLY, so a partial run is never read as the full selftest")
    args = parser.parse_args(argv)
    wanted = [name.strip() for name in (args.only or "").split(",") if name.strip()]
    unknown = sorted(set(wanted) - {function.__name__ for function in TESTS})
    if unknown:
        parser.error("no such test: " + ", ".join(unknown))
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="dw-selftest-"))
    passed = failed = skipped = 0
    try:
        for function in TESTS:
            name = function.__name__
            if wanted and name not in wanted:
                continue
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
    print("SELFTEST_DS%s: %s tests=%d pass=%d fail=%d skip=%d" %
          (" ONLY" if wanted else "", "PASS" if failed == 0 else "FAIL", total, passed, failed, skipped))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
