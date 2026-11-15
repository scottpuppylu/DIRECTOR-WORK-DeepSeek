r"""Rebuild the DIRECTOR-WORK action audit from DeepSeek Harness (DSH) session logs.

DSH has no PreToolUse / PostToolUse hooks, so nothing writes an action log while the agents work. This tool
reconstructs the SAME hash-chained JSONL schema that audit_log.py documents and report_vs_audit.py consumes,
after the fact, from the append-only session event logs:

  sessions/--<normalised cwd>--/<session-id>/session.v4.jsonl.zstd

Every nested tool call a run_code program makes (event tool/ptc-dispatch, e.g. pwsh / read / write) and every
top-level tool call (event tool/call, e.g. run_code / subagent) becomes one line:
  seq, ts (local ISO with offset), session_id, agent_id, tool, tool_use_id, kind (result / failure), input
  (the tool input masked by tools/secret_mask.py; 2.2.5-ds.5, as upstream transcript_audit.py 2.2.5: whole, no
  500-character cut; with --input-limit N cut at N characters and marked "input_cut": true so report_vs_audit.py
  matches that call on its first part only), result (status ok / error / interrupted,
  sha256 and length of the masked output, never the output itself), duration_ms (when the start event is there),
  prev, hash (the same chain algorithm as audit_log.py: sha256 of the line's other fields as sorted compact JSON;
  64 zeros before the first line). A tool call whose result is not in the log yet is kind=failure status=interrupted.
Since 2.2.1-ds.1 (build version 2) line 1 is kind=rebuild, result status rebuilt, with a `source` field (by
"dsh_audit.py", version, sessions with session_id / log file name / sha256 / bytes of the session log read, lines,
warnings, skipped), the same first line as upstream transcript_audit.py 2.2.1, so the log says it was rebuilt after
the fact; report_vs_audit.py prints a note for it. The tool calls follow from seq 2.

Shell tool names are mapped for report_vs_audit.py: pwsh -> PowerShell, bash -> Bash (the original stays in tool_raw
when it differs). The DSH session id is written to session_id; the DSH subagent name (e.g. "w1", from the parent's
subagent catalog) is written to agent_id. report_vs_audit.py --session therefore takes the DSH session id — a TASK
REPORT must write SESSION_ID: <that session id> (agent names select sessions in this tool: --session w1 works here).

  python -I -X utf8 tools/dsh_audit.py build --out FILE [--force] [--log-root DIR] [--cache-root DIR]
      [--project-dir PATH] [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--session ID|PREFIX|AGENT] [--json]
      [--input-limit N]
  python -I -X utf8 tools/dsh_audit.py verify --log FILE [--from N --to M] [--anchor-log FILE]
      [--anchor-rev REV --anchor-path PATH [--repo DIR]] [--cite "AUDIT_RANGE ..."]
      (delegates to audit_log.py verify, so the format is not forked; same output and exit codes)

build writes a new file (refuses to overwrite an existing one without --force) and prints one summary line plus the
file's sha256 and head hash; --json prints the summary as JSON. A parent session's subagent catalog and the projection
cache (default <DSH_HOME>/storages/session_projcache/sessions) supply the childId -> agent name mapping.

loops (2.3.0-ds.6) reads the same sessions (same filters) and prints the calls that look like going in circles. It
reads only and prints tool names and hashes, never an input, an output or a message (as dsh_usage):

  python -I -X utf8 tools/dsh_audit.py loops [--log-root DIR] [--cache-root DIR] [--project-dir PATH] [--since DAY]
      [--until DAY] [--session ID|PREFIX|AGENT] [--events FILE ...] [--repeat N] [--window W] [--rounds R]
      [--poll N] [--show N] [--json] [--out FILE]

  repeat            the same call (tool + hash of the masked input) N times (--repeat, default 3) within W calls
                    (--window, default 20)
  retry_same_error  the same call failed again with the same error (hash of the masked error) within W calls, and
                    the agent wrote no text between the two (reasoning does not count: the rule asks for a written line)
  ping_pong         two calls A, B alternate R rounds (--rounds, default 3) and neither result changes
  poll_no_progress  a read / query call (read, grep, glob, list_agents, job_list, job_output, team_task_list,
                    team_task_get, acp_status, web_fetch, web_search, read_image, get_goal, search_context,
                    list_subagent_models) gives the same result N times running (--poll, default 3), each within W
                    calls of the one before
  bad_args          the tool refused the arguments (error code INVALID_ARGS or name ToolArgsError, as DSH logs them)
                    or a top-level arguments string is not JSON: the count, the share of all calls, the top 5 tools
  child_error_unhandled  NOT_VERIFIED: in the local DSH logs a child's end is a user/message whose source.kind is
                    subagent-settled, and its stopReason was only ever "completed"; no event for a failed child has
                    been seen, so the category prints `~ NOT_VERIFIED` and reports nothing (event names are not guessed)

wait_agent is left out of repeat, retry_same_error, ping_pong and poll_no_progress: calling it again while a child
works is the normal way to wait. A forked session repeats its seed's events, so a finding with the same category,
call key and time in several sessions is counted once (copies=N on its line, also_in in --json). One line per finding:
category, session, agent, call number in the session, time, tool, hashes. --events
reads plain JSONL event files (one session each; for synthetic fixtures) instead of the DSH logs. --json prints the
result as JSON; --out FILE also writes that JSON (status_gen.py's "loops" section reads it).

Exit codes: 0 written / verified / no loop found, 1 refused (output exists without --force) or a write problem, or
loops found something, 2 cannot run (no Node for zstd, sessions root missing, nothing to audit, a read error, bad
usage). Requires Node 22+ for zstd; there is no
offline Python zstd in 3.12. The log records facts read from the files; it cannot prove the agent did nothing else.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
import pathlib
import sys


def load_local(name):
    """Load a sibling module (the tools are run with -I, so the script folder is not on sys.path)."""
    path = pathlib.Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dsh = load_local("dsh_session")
audit = load_local("audit_log")

TOOL = "dsh_audit"
BUILD_VERSION = 2  # 2: line 1 is kind=rebuild with a source field (2.2.1-ds.1)
INPUT_LIMIT = None  # 2.2.5-ds.5: None keeps each input whole (upstream 2.2.5 H1); build --input-limit N sets it
TOOL_NAMES = {"pwsh": "PowerShell", "powershell": "PowerShell", "bash": "Bash", "sh": "Bash", "zsh": "Bash"}


def map_tool(name):
    if not isinstance(name, str) or not name:
        return "unknown", None
    mapped = TOOL_NAMES.get(name.lower())
    return (mapped, name) if mapped else (name, None)


def text_of(value):
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, sort_keys=True)


def parse_arguments(value):
    """A tool input as a JSON-like value: event arguments may be a JSON string (tool/call) or an object (ptc-dispatch)."""
    if isinstance(value, str):
        stripped = value.strip()
        if stripped[:1] in ("{", "["):
            try:
                return json.loads(stripped)
            except ValueError:
                return value
        return value
    return value


def duration(start_ms, end_ms):
    """Milliseconds from start to end, or None when either is missing or negative."""
    if not isinstance(start_ms, (int, float)) or not isinstance(end_ms, (int, float)):
        return None
    if isinstance(start_ms, bool) or isinstance(end_ms, bool):
        return None
    value = int(end_ms) - int(start_ms)
    return value if value >= 0 else None


def start_time(candidates, end_ms):
    """The latest start time not after the end event (a call is retried, so take the one that ended)."""
    usable = [ms for ms in candidates if isinstance(ms, (int, float)) and not isinstance(ms, bool)
              and (end_ms is None or ms <= end_ms)]
    return max(usable) if usable else None


def make_entry(session_id, agent_id, tool, tool_use_id, kind, raw_input, status, output, duration_ms, event_ms, tool_raw):
    """One audit line (before seq/prev/hash are chained on)."""
    entry = {
        "ts": dsh.iso_from_ms(event_ms),
        "session_id": session_id,
        "agent_id": agent_id,
        "tool": tool,
    }
    if tool_raw:
        entry["tool_raw"] = tool_raw
    entry["tool_use_id"] = tool_use_id
    entry["kind"] = kind
    entry["input"] = audit.summary(raw_input, INPUT_LIMIT)
    if INPUT_LIMIT is not None and entry["input"] != audit.summary(raw_input, None):
        entry["input_cut"] = True  # 2.2.5-ds.5: marked, so the reader matches this call on its first part (已截斷)
    entry["result"] = audit.output_record(status, output)
    if duration_ms is not None:
        entry["duration_ms"] = duration_ms
    return entry


def session_entries(events, session_id, agent_id, warnings):
    """[audit line] for the tool actions in one session's events, in event order."""
    starts = {}
    for event in events:
        if event.get("type") != "tool/ptc-dispatch-start":
            continue
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        sub_id = data.get("subCallId")
        if isinstance(sub_id, str) and sub_id:
            starts.setdefault(sub_id, []).append(event.get("time"))
    results = {}
    for event in events:
        if event.get("type") != "tool/result":
            continue
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        message = data.get("message") if isinstance(data.get("message"), dict) else {}
        call_id = message.get("toolCallId") or data.get("toolCallId") or (message.get("source") or {}).get("callId")
        if isinstance(call_id, str) and call_id:
            results[call_id] = event
    entries = []
    for event in events:
        kind = event.get("type")
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        event_ms = event.get("time")
        seq = event.get("seq")
        if kind == "tool/ptc-dispatch":
            name, raw = map_tool(data.get("name"))
            sub_id = data.get("subCallId")
            failed = bool(data.get("isError"))
            output = data.get("content")
            if failed and output is None:
                output = {"error": data.get("error")}
            entries.append({
                "entry": make_entry(session_id, agent_id, name, sub_id, "failure" if failed else "result",
                                    parse_arguments(data.get("arguments")), "error" if failed else "ok", output,
                                    duration(start_time(starts.get(sub_id) or [], event_ms), event_ms),
                                    event_ms, raw),
                "_ms": event_ms, "_seq": seq if isinstance(seq, int) else -1})
        elif kind == "tool/call":
            name, raw = map_tool(data.get("name"))
            call_id = data.get("callId")
            result = results.get(call_id)
            result_data = result.get("data") if result is not None and isinstance(result.get("data"), dict) else {}
            message = result_data.get("message") if isinstance(result_data.get("message"), dict) else {}
            failed = bool(message.get("isError") or result_data.get("isError"))
            output = message.get("content")
            error = result_data.get("error")
            if error is not None:
                output = {"content": output, "error": error} if output is not None else error
            status = "error" if failed or error is not None else ("ok" if result is not None else "interrupted")
            entries.append({
                "entry": make_entry(session_id, agent_id, name, call_id,
                                    "failure" if status != "ok" else "result",
                                    parse_arguments(data.get("arguments")), status, output,
                                    duration(event_ms, result.get("time")) if result is not None else None,
                                    event_ms, raw),
                "_ms": event_ms, "_seq": seq if isinstance(seq, int) else -1})
    return entries


def header_info(events, fallback_id):
    """(session_id, cwd, created_ms, is_worker, parent) from the session header event, with sensible fallbacks."""
    header = dsh.session_header(events)
    session_id = header.get("id") if isinstance(header.get("id"), str) and header.get("id") else fallback_id
    depth = header.get("delegationDepth")
    worker = header.get("origin") == "subagent" or (isinstance(depth, int) and depth > 0)
    return (session_id, header.get("cwd"), header.get("createdAt"), worker, header.get("parentSession"))


def collect_catalog(events, catalog):
    """childId -> name from this log's subagent/catalog events (parents name their children here)."""
    for event in events:
        if event.get("type") != "subagent/catalog":
            continue
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        child, name = data.get("childId"), data.get("name")
        if isinstance(child, str) and child and isinstance(name, str) and name:
            catalog.setdefault(child, {"name": name, "label": data.get("label"), "parent": None})


def matches_session(args, session_id, cwd, created_ms, agent, catalog):
    """Whether one session passes --session / --project-dir / --since / --until."""
    if args.session:
        wanted = [value.lower() for value in args.session]
        id_lower = session_id.lower()
        bare = id_lower[len(dsh.ROOT_PREFIX):] if id_lower.startswith(dsh.ROOT_PREFIX) else id_lower
        name = (agent or "").lower()
        labels = []
        entry = catalog.get(session_id)
        if entry and isinstance(entry.get("label"), str):
            labels.append(entry["label"].lower())
        if not any(w in id_lower or bare.startswith(w) or id_lower.startswith(w) or (name and w == name)
                   or any(w in label for label in labels) for w in wanted):
            return False
    if args.project_dir:
        if not cwd or not any(dsh.path_is_under(cwd, root) for root in args.project_dir):
            return False
    if args.since or args.until:
        if not isinstance(created_ms, (int, float)) or isinstance(created_ms, bool):
            return False
        when = datetime.datetime.fromtimestamp(created_ms / 1000.0).astimezone()
        if args.since and when < dsh.parse_day(args.since):
            return False
        if args.until and when >= dsh.parse_day(args.until, end=True):
            return False
    return True


def file_record(path):
    """Name, sha256 and size of a session log file, for the rebuild line's source (None values when unreadable)."""
    try:
        data = pathlib.Path(path).read_bytes()
    except OSError:
        return {"log": pathlib.Path(path).name, "sha256": None, "bytes": None}
    return {"log": pathlib.Path(path).name, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def chain_lines(entries, source, now=None):
    """The kind=rebuild first line, then the entries (dicts, changed in place), hash-chained from seq 1 by
    audit_log.py's rule. Returns (lines, head hash)."""
    stamp = now or datetime.datetime.now().astimezone().isoformat(timespec="milliseconds")
    first = {"ts": stamp, "session_id": None, "agent_id": None, "tool": None, "tool_use_id": None, "input": "",
             "kind": "rebuild", "result": {"status": "rebuilt"}, "duration_ms": None, "source": source}
    prev = audit.GENESIS
    lines = []
    for seq, entry in enumerate([first] + list(entries), 1):
        entry.pop("hash", None)
        entry["seq"] = seq
        entry["prev"] = prev
        entry["hash"] = audit.digest(entry)
        prev = entry["hash"]
        lines.append(audit.canonical(entry) + "\n")
    return lines, prev


def session_files(args, warnings):
    """(session files, projections, catalog) under --log-root / --cache-root (shared by build and loops)."""
    log_root = pathlib.Path(args.log_root).expanduser() if args.log_root else dsh.default_sessions_root()
    cache_root = pathlib.Path(args.cache_root).expanduser() if args.cache_root else dsh.default_projcache_root()
    sessions = dsh.list_session_files(log_root)
    projections = {}
    if cache_root.is_dir():
        projections = dsh.load_projections(cache_root)
        for projection in projections.values():
            if projection.error:
                warnings.append(f"projection {projection.session_id}: {projection.error}")
    else:
        warnings.append(f"projection cache not found: {cache_root} (agent names may be missing)")
    return sessions, projections, dsh.agent_catalog(projections)


def selected_sessions(args, sessions, projections, catalog, warnings, skipped):
    """Yield (index, ref, events, header_id, agent_id, role, name_source, cwd, created_ms, parent) for each session
    that passes the filters, in build's order (subagents first, then roots; the catalog fills as it goes)."""
    for index, ref in enumerate(sorted(sessions, key=lambda item: (item.session_id.startswith(dsh.ROOT_PREFIX),
                                                                   item.session_id))):
        events, noted = dsh.read_events(ref.path)
        warnings.extend(f"{ref.session_id}: {note}" for note in noted)
        if not events:
            skipped.append({"session_id": ref.session_id, "reason": "no events decoded"})
            continue
        header_id, cwd, created_ms, worker, parent = header_info(events, ref.session_id)
        collect_catalog(events, catalog)
        role = "worker" if worker else "director"
        agent, name_source = dsh.session_agent(header_id, role, catalog, projections.get(header_id))
        if not matches_session(args, header_id, cwd, created_ms, agent, catalog):
            continue
        yield index, ref, events, header_id, agent or header_id, role, name_source, cwd, created_ms, parent


def build(args):
    """Write the audit log; returns the summary dict (raises DshError for cannot-run cases)."""
    global INPUT_LIMIT
    INPUT_LIMIT = getattr(args, "input_limit", 0) or None  # 2.2.5-ds.5: 0 / None = keep each input whole
    warnings = []
    sessions, projections, catalog = session_files(args, warnings)
    entries = []
    audited = []
    skipped = []
    for (index, ref, events, header_id, agent_id, role, name_source, cwd, created_ms,
         parent) in selected_sessions(args, sessions, projections, catalog, warnings, skipped):
        found = session_entries(events, header_id, agent_id, warnings)
        for item in found:
            item["_session"] = header_id
            item["_index"] = index
        entries.extend(found)
        audited.append({"session_id": header_id, "agent_id": agent_id, "cwd": cwd,
                        "started": dsh.iso_from_ms(created_ms), "role": role,
                        "events": len(events), "lines": len(found),
                        "agent_source": name_source, "parent": parent,
                        "log_file": str(ref.path), "_file": file_record(ref.path)})
    if not entries:
        raise dsh.DshError("nothing to audit: no tool calls found in the selected sessions"
                           + (f" ({len(sessions)} session log(s) read)" if sessions else ""))
    entries.sort(key=lambda item: (item["_ms"] if isinstance(item["_ms"], (int, float)) else 0,
                                   item["_index"], item["_seq"]))
    files = [dict(session_id=item["session_id"], **item.pop("_file")) for item in audited]
    source = {"by": "dsh_audit.py", "version": BUILD_VERSION, "sessions": files, "lines": len(entries),
              "warnings": len(warnings), "skipped": len(skipped), "input_limit": INPUT_LIMIT}
    lines, head = chain_lines([item["entry"] for item in entries], source)
    kinds = {}
    tools = {}
    for item in entries:
        entry = item["entry"]
        kinds[entry["kind"]] = kinds.get(entry["kind"], 0) + 1
        tools[entry["tool"]] = tools.get(entry["tool"], 0) + 1
    out = pathlib.Path(args.out).expanduser()
    if out.exists() and not args.force:
        raise BuildRefused(f"refusing to overwrite {out}; pass --force to replace an existing audit log")
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(lines).encode("utf-8")
    try:
        temp = out.with_name(out.name + ".tmp")
        with open(temp, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, out)
    except OSError as error:
        raise BuildRefused(f"cannot write {out}: {error}") from error
    first_ts = entries[0]["entry"].get("ts")
    last_ts = entries[-1]["entry"].get("ts")
    return {
        "tool": TOOL,
        "version": BUILD_VERSION,
        "command": "build",
        "out": str(out),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
        "lines": len(entries),
        "rebuild_line": 1,
        "sessions": audited,
        "sessions_total": len(sessions),
        "kinds": kinds,
        "tools": tools,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "head_seq": len(lines),
        "head_hash": head,
        "warnings": warnings,
        "skipped": skipped,
        "note": "after-the-fact reconstruction from DSH session logs; DSH has no real-time hook",
    }


class BuildRefused(Exception):
    """The output file cannot be written (exists without --force, or an OS error)."""


def cmd_build(args):
    try:
        summary = build(args)
    except dsh.DshError as error:
        print(f"NOT_RUN {error}")
        return 2
    except BuildRefused as error:
        print(f"REFUSED {error}")
        return 1
    except dsh.NodeMissing as error:
        print(f"NOT_RUN {error}")
        return 2
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=1))
        return 0
    warnings = summary["warnings"]
    print(f"DSH_AUDIT sessions={len(summary['sessions'])} lines={summary['lines']} "
          f"kinds={','.join(f'{k}:{v}' for k, v in sorted(summary['kinds'].items()))} "
          f"first={summary['first_ts']} last={summary['last_ts']}")
    hidden = []
    for tool_name, count in sorted(summary["tools"].items(), key=lambda pair: (-pair[1], pair[0])):
        if len(hidden) < 10:
            hidden.append(f"{tool_name}:{count}")
    print("TOOLS " + ", ".join(hidden) + (" ..." if len(summary["tools"]) > 10 else ""))
    for session in summary["sessions"]:
        print(f"  {session['session_id']} agent={session['agent_id']} role={session['role']} "
              f"events={session['events']} lines={session['lines']}")
    print(f"WROTE {summary['out']} sha256={summary['sha256']} head_seq={summary['head_seq']} "
          f"head_hash={summary['head_hash']}")
    for warning in warnings[:8]:
        print(f"  ~ {warning}")
    if len(warnings) > 8:
        print(f"  ~ ... {len(warnings) - 8} more warning(s); see --json")
    return 0


# ---------------------------------------------------------------- loops (2.3.0-ds.6)

LOOPS_VERSION = 1
CATEGORIES = ("repeat", "retry_same_error", "ping_pong", "poll_no_progress", "bad_args")
NOT_VERIFIED = ("child_error_unhandled",)
WAIT_TOOLS = ("wait_agent",)  # waiting on a child is calling it again; not a loop by itself
QUERY_TOOLS = ("read", "grep", "glob", "list_agents", "job_list", "job_output", "team_task_list", "team_task_get",
               "acp_status", "web_fetch", "web_search", "read_image", "get_goal", "search_context",
               "list_subagent_models")
BAD_ARGS_CODES = ("INVALID_ARGS",)  # as the DSH logs write a refused argument (error.code / error.name)
BAD_ARGS_NAMES = ("ToolArgsError",)


def short_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def call_problems(events):
    """{call id: reason} for calls whose arguments the tool refused, or whose arguments string is not JSON."""
    found = {}
    errors = {}
    for event in events:
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        kind = event.get("type")
        if kind == "tool/ptc-dispatch":
            errors[data.get("subCallId")] = data.get("error")
        elif kind == "tool/result":
            message = data.get("message") if isinstance(data.get("message"), dict) else {}
            errors[message.get("toolCallId") or data.get("toolCallId")] = data.get("error")
        elif kind == "tool/call" and isinstance(data.get("arguments"), str):
            try:
                json.loads(data["arguments"])
            except ValueError:
                found[data.get("callId")] = "ARGS_NOT_JSON"
    for call_id, error in errors.items():
        if isinstance(error, dict) and (error.get("code") in BAD_ARGS_CODES or error.get("name") in BAD_ARGS_NAMES):
            found.setdefault(call_id, str(error.get("code") or error.get("name")))
    return found


def text_positions(events):
    """Event positions of assistant messages that carry written text (a "text" part; reasoning is not counted)."""
    positions = []
    for position, event in enumerate(events):
        if event.get("type") != "assistant/message":
            continue
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        message = data.get("message") if isinstance(data.get("message"), dict) else {}
        parts = message.get("content") if isinstance(message.get("content"), list) else []
        if any(isinstance(part, dict) and part.get("type") == "text" and str(part.get("text") or "").strip()
               for part in parts):
            positions.append(position)
    return positions


def session_calls(events, session_id, agent_id, warnings):
    """The session's calls in event order: number, tool, key (hash of tool + masked input), status, result hash,
    time, event position, refused-argument reason. Reuses session_entries (same parsing and masking as build)."""
    position = {}
    for index, event in enumerate(events):
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        if event.get("type") == "tool/ptc-dispatch":
            position[("sub", data.get("subCallId"))] = index
        elif event.get("type") == "tool/call":
            position[("call", data.get("callId"))] = index
    problems = call_problems(events)
    calls = []
    for item in session_entries(events, session_id, agent_id, warnings):
        entry = item["entry"]
        call_id = entry.get("tool_use_id")
        where = position.get(("sub", call_id), position.get(("call", call_id), -1))
        calls.append({"n": len(calls) + 1, "tool": entry["tool"], "key": short_hash(entry["tool"] + "\n" + entry["input"]),
                      "status": entry["result"]["status"], "result": entry["result"]["sha256"][:12],
                      "ts": entry["ts"], "pos": where, "bad": problems.get(call_id)})
    return calls


def finding(category, session_id, agent_id, call, **extra):
    row = {"category": category, "session_id": session_id, "agent_id": agent_id, "call": call["n"], "ts": call["ts"],
           "tool": call["tool"], "key": call["key"]}
    row.update(extra)
    return row


def loop_findings(calls, session_id, agent_id, texts, settings):
    """[finding] of one session's calls (see the module docstring for each category)."""
    found = []
    looped = [c for c in calls if c["tool"] not in WAIT_TOOLS]
    seen = set()
    for i, call in enumerate(looped):  # repeat
        window = looped[max(0, i - settings["window"] + 1):i + 1]
        count = sum(1 for c in window if c["key"] == call["key"])
        if count >= settings["repeat"] and call["key"] not in seen:
            seen.add(call["key"])
            found.append(finding("repeat", session_id, agent_id, call, count=count, window=settings["window"],
                                 total=sum(1 for c in looped if c["key"] == call["key"])))
    by_key = {}
    for call in calls:
        by_key.setdefault(call["key"], []).append(call)
    place = {c["n"]: index for index, c in enumerate(looped)}
    for same in by_key.values():  # retry_same_error: the next run of the same call, same error, no text between
        if same[0]["tool"] in WAIT_TOOLS:
            continue
        run = 1
        for before, after in zip(same, same[1:]):
            again = (before["status"] == "error" and after["status"] == "error" and before["result"] == after["result"]
                     and place[after["n"]] - place[before["n"]] <= settings["window"]
                     and not any(before["pos"] < p < after["pos"] for p in texts))
            run = run + 1 if again else 1
            if again and run == 2:
                found.append(finding("retry_same_error", session_id, agent_id, after, result=after["result"],
                                     previous_call=before["n"]))
    pairs = set()
    i = 0
    span = 2 * settings["rounds"]
    while i + span <= len(looped):  # ping_pong
        a, b = looped[i], looped[i + 1]
        run = looped[i:i + span]
        if a["key"] != b["key"] and all(c["key"] == (a, b)[j % 2]["key"] and c["result"] == (a, b)[j % 2]["result"]
                                        for j, c in enumerate(run)):
            pair = tuple(sorted((a["key"], b["key"])))
            if pair not in pairs:
                pairs.add(pair)
                found.append(finding("ping_pong", session_id, agent_id, a, other_tool=b["tool"], other_key=b["key"],
                                     rounds=settings["rounds"]))
            i += span
            continue
        i += 1
    for same in by_key.values():  # poll_no_progress
        if same[0]["tool"] not in QUERY_TOOLS:
            continue
        run = 1
        for before, after in zip(same, same[1:]):
            gap = place[after["n"]] - place[before["n"]]
            steady = (before["status"] == after["status"] == "ok" and before["result"] == after["result"]
                      and gap <= settings["window"])
            run = run + 1 if steady else 1
            if steady and run == settings["poll"]:
                found.append(finding("poll_no_progress", session_id, agent_id, after, result=after["result"],
                                     times=run))
    for call in calls:  # bad_args
        if call["bad"]:
            found.append(finding("bad_args", session_id, agent_id, call, reason=call["bad"]))
    order = {name: index for index, name in enumerate(CATEGORIES)}
    found.sort(key=lambda row: (row["call"], order[row["category"]]))
    return found


def loops(args):
    """The loops result dict (raises DshError / NodeMissing when the logs cannot be read)."""
    settings = {"repeat": args.repeat, "window": args.window, "rounds": args.rounds, "poll": args.poll}
    warnings, skipped, sessions_read = [], [], []
    if args.events:
        selected = []
        for index, name in enumerate(args.events):
            path = pathlib.Path(name)
            try:
                events, noted = dsh.parse_jsonl(path.read_text(encoding="utf-8-sig"))
            except OSError as error:
                raise dsh.DshError(f"cannot read {path}: {error}") from error
            warnings.extend(f"{path.name}: {note}" for note in noted)
            header_id, _, _, worker, _ = header_info(events, path.stem)
            agent, _ = dsh.session_agent(header_id, "worker" if worker else "director", {}, None)
            selected.append((header_id, agent or header_id, events))
    else:
        sessions, projections, catalog = session_files(args, warnings)
        if not sessions:
            raise dsh.DshError("no DSH session logs found")
        selected = [(item[3], item[4], item[2]) for item in
                    selected_sessions(args, sessions, projections, catalog, warnings, skipped)]
    findings, total, first = [], 0, {}
    for header_id, agent_id, events in selected:
        calls = session_calls(events, header_id, agent_id, warnings)
        total += len(calls)
        sessions_read.append({"session_id": header_id, "agent_id": agent_id, "calls": len(calls)})
        for row in loop_findings(calls, header_id, agent_id, text_positions(events), settings):
            # a forked DSH session carries its seed's events: the same finding (same call, same time) is counted once
            same = (row["category"], row["tool"], row["key"], row["ts"])
            if same in first:
                first[same].setdefault("also_in", []).append(header_id)
                continue
            first[same] = row
            findings.append(row)
    counts = {name: sum(1 for row in findings if row["category"] == name) for name in CATEGORIES}
    tools = {}
    for row in findings:
        if row["category"] == "bad_args":
            tools[row["tool"]] = tools.get(row["tool"], 0) + 1
    top = sorted(tools.items(), key=lambda pair: (-pair[1], pair[0]))[:5]
    return {"tool": TOOL, "command": "loops", "version": LOOPS_VERSION, "settings": settings,
            "sessions": len(sessions_read), "calls": total, "findings_total": len(findings), "counts": counts,
            "bad_args": {"count": counts["bad_args"], "calls": total,
                         "ratio": round(counts["bad_args"] / total, 6) if total else 0.0, "top": top},
            "not_verified": list(NOT_VERIFIED), "findings": findings, "per_session": sessions_read,
            "warnings": warnings, "skipped": skipped}


def loop_line(row):
    extra = {"repeat": lambda: f"count={row['count']}/{row['window']} total={row['total']}",
             "retry_same_error": lambda: f"result={row['result']} previous_call={row['previous_call']} no_text_between",
             "ping_pong": lambda: f"other={row['other_tool']}:{row['other_key']} rounds={row['rounds']}",
             "poll_no_progress": lambda: f"result={row['result']} times={row['times']}",
             "bad_args": lambda: f"reason={row['reason']}"}[row["category"]]()
    copies = f" copies={1 + len(row['also_in'])}" if row.get("also_in") else ""
    return (f"LOOP {row['category']} session={row['session_id']} agent={row['agent_id']} call={row['call']} "
            f"at={row['ts']} tool={row['tool']} key={row['key']} {extra}{copies}")


def cmd_loops(args):
    for name in ("repeat", "window", "rounds", "poll"):
        if getattr(args, name) < (2 if name in ("repeat", "rounds", "poll") else 1):
            print(f"NOT_RUN --{name} is too small")
            return 2
    try:
        result = loops(args)
    except (dsh.DshError, dsh.NodeMissing) as error:
        print(f"NOT_RUN {error}")
        return 2
    if args.out:
        out = pathlib.Path(args.out).expanduser()
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            with open(out, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(result, ensure_ascii=False, indent=1) + "\n")
        except OSError as error:
            print(f"NOT_RUN cannot write {out}: {error}")
            return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=1))
        return 1 if result["findings_total"] else 0
    for category in CATEGORIES:
        rows = [row for row in result["findings"] if row["category"] == category]
        for row in rows[:args.show]:
            print(loop_line(row))
        if len(rows) > args.show:
            print(f"  ... {len(rows) - args.show} more {category} finding(s); see --json")
    bad = result["bad_args"]
    top = ", ".join(f"{name}:{count}" for name, count in bad["top"]) or "-"
    print(f"BAD_ARGS count={bad['count']} of {bad['calls']} calls ({100 * bad['ratio']:.2f}%) top={top}")
    for name in NOT_VERIFIED:
        print(f"~ NOT_VERIFIED {name}")
    print(f"DSH_LOOPS sessions={result['sessions']} calls={result['calls']} findings={result['findings_total']} "
          + " ".join(f"{name}={count}" for name, count in result["counts"].items())
          + (f" out={args.out}" if args.out else ""))
    for warning in result["warnings"][:8]:
        print(f"  ~ {warning}")
    if len(result["warnings"]) > 8:
        print(f"  ~ ... {len(result['warnings']) - 8} more warning(s); see --json")
    return 1 if result["findings_total"] else 0


def cmd_verify(args):
    """Delegate to audit_log.py verify (same format, same checks, same exit codes)."""
    argv = ["audit_log.py", "verify"]
    if args.log:
        argv += ["--log", args.log]
    if args.from_seq is not None:
        argv += ["--from", str(args.from_seq)]
    if args.to_seq is not None:
        argv += ["--to", str(args.to_seq)]
    if args.anchor_log:
        argv += ["--anchor-log", args.anchor_log]
    if args.anchor_rev:
        argv += ["--anchor-rev", args.anchor_rev]
    if args.anchor_path:
        argv += ["--anchor-path", args.anchor_path]
    if args.repo:
        argv += ["--repo", args.repo]
    if args.cite:
        argv += ["--cite", args.cite]
    saved = sys.argv
    sys.argv = argv
    try:
        return audit.main()
    finally:
        sys.argv = saved


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")  # before parse_args: --help prints during parsing
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build", help="reconstruct the action log from DSH session logs")
    build_parser.add_argument("--out", required=True, help="audit JSONL file to write")
    build_parser.add_argument("--force", action="store_true", help="replace an existing --out file")
    build_parser.add_argument("--log-root", "--sessions-root", dest="log_root",
                              help="DSH sessions root (default %%USERPROFILE%%\\.dsh\\sessions)")
    build_parser.add_argument("--cache-root", help="DSH projection cache root, for agent names")
    build_parser.add_argument("--project-dir", action="append", default=[],
                              help="only sessions whose cwd is this folder or below (repeatable)")
    build_parser.add_argument("--since", help="local date YYYY-MM-DD, inclusive (session start)")
    build_parser.add_argument("--until", help="local date YYYY-MM-DD, inclusive (session start)")
    build_parser.add_argument("--session", action="append", default=[],
                              help="only this session id / id prefix / agent name (repeatable)")
    build_parser.add_argument("--json", action="store_true", help="print the build summary as JSON")
    build_parser.add_argument("--input-limit", type=int, default=0,
                              help="2.2.5-ds.5: cut each input at this many characters (default 0: keep it whole); a cut "
                                   "line is marked input_cut")
    loops_parser = sub.add_parser("loops", help="2.3.0-ds.6: find calls that go in circles (names and hashes only)")
    loops_parser.add_argument("--log-root", "--sessions-root", dest="log_root",
                              help="DSH sessions root (default %%USERPROFILE%%\\.dsh\\sessions)")
    loops_parser.add_argument("--cache-root", help="DSH projection cache root, for agent names")
    loops_parser.add_argument("--project-dir", action="append", default=[],
                              help="only sessions whose cwd is this folder or below (repeatable)")
    loops_parser.add_argument("--since", help="local date YYYY-MM-DD, inclusive (session start)")
    loops_parser.add_argument("--until", help="local date YYYY-MM-DD, inclusive (session start)")
    loops_parser.add_argument("--session", action="append", default=[],
                              help="only this session id / id prefix / agent name (repeatable)")
    loops_parser.add_argument("--events", nargs="+", metavar="FILE",
                              help="plain JSONL event files, one session each (synthetic fixtures), instead of the logs")
    loops_parser.add_argument("--repeat", type=int, default=3, help="repeat: this many of the same call (default 3)")
    loops_parser.add_argument("--window", type=int, default=20, help="repeat / poll: within this many calls (default 20)")
    loops_parser.add_argument("--rounds", type=int, default=3, help="ping_pong: this many A-B rounds (default 3)")
    loops_parser.add_argument("--poll", type=int, default=3, help="poll_no_progress: same result this many times (default 3)")
    loops_parser.add_argument("--show", type=int, default=20, help="lines printed per category (default 20; --json has all)")
    loops_parser.add_argument("--json", action="store_true", help="print the result as JSON")
    loops_parser.add_argument("--out", help="also write the JSON result to this file (status_gen.py \"loops\" reads it)")
    verify_parser = sub.add_parser("verify", help="delegate to audit_log.py verify (hash chain, anchors)")
    verify_parser.add_argument("--log", required=True, help="audit JSONL file to verify")
    verify_parser.add_argument("--from", dest="from_seq", type=int)
    verify_parser.add_argument("--to", dest="to_seq", type=int)
    verify_parser.add_argument("--anchor-log", help="file with AUDIT_HEAD lines")
    verify_parser.add_argument("--anchor-rev", help="commit whose --anchor-path holds the AUDIT_HEAD lines")
    verify_parser.add_argument("--anchor-path", help="path of DIRECTOR_LOG inside the repo, for --anchor-rev")
    verify_parser.add_argument("--repo", help="repo for --anchor-rev")
    verify_parser.add_argument("--cite", help="an AUDIT_RANGE line to check")
    a = ap.parse_args(argv)
    for field in ("since", "until"):
        value = getattr(a, field, None)
        if value:
            try:
                dsh.parse_day(value)
            except ValueError:
                print(f"dsh_audit: --{field} {value} is not YYYY-MM-DD", file=sys.stderr)
                return 2
    if a.command == "build":
        if a.input_limit < 0:
            print("NOT_RUN --input-limit must be 0 (no cut) or more")
            return 2
        return cmd_build(a)
    if a.command == "loops":
        return cmd_loops(a)
    return cmd_verify(a)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
