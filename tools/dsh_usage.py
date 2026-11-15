r"""Usage / context report for dsh-DIRECTOR-WORKER (dshdw), DIRECTOR-WORK on DeepSeek Harness (DSH).

Reads the DSH projection cache (plain JSON, no Node needed) and prints numbers only; message content is never printed.

  python -I -X utf8 <WS>/DIRECTOR/tools/dsh_usage.py [--sessions-root DIR] [--cache-root DIR]
      [--project-dir PATH] [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--session ID|PREFIX|AGENT]
      [--json] [--out FILE] [--from-jsonl | --no-fallback] [--loops [--loops-config FILE]]

Per session: id, role (director/worker/unknown), agent name, cwd, started (local time), turns, steps, token totals
(input = uncached input, output, cacheRead, cacheWrite, total), last prompt tokens (= input + cacheRead + cacheWrite of
the newest assistant message), contextWindow, percent used, model and reasoning effort. Then a daily table (by the
session's local start date) and the totals.

Sources, in order:
  1. <DSH_HOME>/storages/session_projcache/sessions/<session-id>.json  (default; pure Python)
     --cache-root overrides, env DSH_PROJCACHE_ROOT too. Fields come from record.rows.* (see dsh_session.py).
  2. the append-only event log below is the fallback for a missing/unreadable projection or a missing field.
     --sessions-root overrides (env DSH_SESSIONS_ROOT); default %USERPROFILE%\.dsh\sessions.
     Decoding it needs Node 22+ (zstd); --no-fallback keeps the report Node-free.

--session takes a full id, an id prefix, or an agent name (e.g. a subagent name from the parent's catalog); repeatable.
--project-dir matches the session's STARTUP folder: the DSH session is logged under the folder the session started in,
so a match includes that folder and its subfolders. Subagent sessions are logged under the director's startup folder,
not under a repo a worker edits; therefore --project-dir <REPO> does not find worker sessions. Use the workspace root
(<WS>, the director's startup folder) for a project report, and --session <agent> for one worker line. Repeatable.
--since / --until are local dates (YYYY-MM-DD), both inclusive, compared with the session start time.
--json prints the report as JSON; --out FILE always writes the JSON report to FILE (and says so on stderr).
--loops (2.4.0-ds.6, DW 2.4.0 usage_mix's LOOPS line) adds one line, `LOOPS repeat=n retry_same_error=n ... calls=n
sessions=n`, from `dsh_audit.py loops` over the same sessions and filters (counts only; "loops" in --json). It is off by
default, unlike DW: it decodes the event logs, which needs Node and took about 105 s for 103 sessions here, while this
report reads only the plain-JSON cache. --loops-config FILE passes a loops config (thresholds, allow list). When the
logs cannot be read the line is `LOOPS NOT_RUN <reason>` and the report is unchanged.

Exit codes: 0 report written, 2 nothing found (NO_DATA: ...) or a root is missing, 2 also for usage errors.

Examples:
  python -I -X utf8 tools/dsh_usage.py
  python -I -X utf8 tools/dsh_usage.py --project-dir <WS> --since 2026-11-01 --json
  python -I -X utf8 tools/dsh_usage.py --session tools-port --out DIRECTOR/research/usage-tools-port.json
"""
import argparse
import datetime
import importlib.util
import json
import pathlib
import re
import sys


def load_local(name):
    """Load a sibling module (the tools are run with -I, so the script folder is not on sys.path)."""
    path = pathlib.Path(__file__).with_name(name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dsh = load_local("dsh_session")

TOOL = "dsh_usage"
REPORT_VERSION = 1
FALLBACK_KEYS = ("cwd", "createdAt", "model", "effort")


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else 0


def sum_usage(usage):
    """(input, output, cache_read, cache_write) from a DSH usage object; 0 for missing fields."""
    usage = usage if isinstance(usage, dict) else {}
    return (number(usage.get("uncachedInputTokens", usage.get("inputTokens"))),
            number(usage.get("outputTokens")),
            number(usage.get("cacheReadTokens")),
            number(usage.get("cacheWriteTokens")))


def human_tokens(count):
    if count is None:
        return "-"
    count = int(count)
    if abs(count) < 1000:
        return str(count)
    if abs(count) < 1000000:
        return f"{count / 1000:.1f}k"
    if abs(count) < 1000000000:
        return f"{count / 1000000:.2f}M"
    return f"{count / 1000000000:.2f}G"


def row_from_projection(projection):
    """The usage fields of one projection cache record (dict; never None when the record parses)."""
    identity = projection.identity()
    usage = projection.row("tokenUsage") or {}
    totals = usage.get("totals") if isinstance(usage, dict) else {}
    last = usage.get("last") if isinstance(usage, dict) else {}
    buckets = last.get("buckets") if isinstance(last, dict) else {}
    stats = projection.row("sessionStats") or {}
    pressure = projection.row("contextPressure") or {}
    selection = projection.row("modelSelection") or {}
    last_used = selection.get("lastUsed") if isinstance(selection, dict) else {}
    outline = projection.row("turnOutline") or {}
    approval = projection.row("approvalState") or {}
    totals = totals if isinstance(totals, dict) else {}
    buckets = buckets if isinstance(buckets, dict) else {}
    last_used = last_used if isinstance(last_used, dict) else {}
    stats = stats if isinstance(stats, dict) else {}
    pressure = pressure if isinstance(pressure, dict) else {}
    approval = approval if isinstance(approval, dict) else {}
    turns = stats.get("turns")
    if not isinstance(turns, int) or isinstance(turns, bool):
        turns = len(outline.get("turns") or []) if isinstance(outline, dict) else 0
    steps = stats.get("steps") if isinstance(stats.get("steps"), int) else 0
    last_prompt = sum(sum_usage(buckets))
    return {
        "started_ms": identity.get("createdAt"),
        "cwd": identity.get("cwd") or projection.row("workingDirectory"),
        "title": projection.row("title"),
        "turns": turns,
        "steps": steps,
        "input": sum_usage(totals)[0],
        "output": sum_usage(totals)[1],
        "cacheRead": sum_usage(totals)[2],
        "cacheWrite": sum_usage(totals)[3],
        "total": sum(sum_usage(totals)),
        "lastPromptTokens": last_prompt,
        "lastTurn": last.get("turn") if isinstance(last, dict) else None,
        "lastStep": last.get("step") if isinstance(last, dict) else None,
        "contextWindow": pressure.get("contextWindow"),
        "surfaceTokens": pressure.get("surfaceTokens"),
        "model": last_used.get("model"),
        "provider": last_used.get("provider"),
        "effort": last_used.get("reasoningEffort"),
        "sandbox": projection.row("sandboxMode"),
        "approval": approval.get("policy"),
        "agentPreset": projection.row("agentPreset"),
        "lastActivityMs": (projection.row("timeContext") or {}).get("lastMessageTime")
        if isinstance(projection.row("timeContext"), dict) else None,
        "source": "projcache",
    }


def row_from_jsonl(ref, warnings):
    """Usage fields rebuilt from the event log (needs Node); the fallback for a missing projection cache."""
    events, noted = dsh.read_events(ref.path)
    warnings.extend(f"{ref.session_id}: {w}" for w in noted)
    header = dsh.session_header(events)
    totals = {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0}
    turns = 0
    steps = 0
    last_usage = None
    context_window = None
    model = effort = provider = title = None
    last_activity = None
    last_turn = last_step = None
    for event in events:
        kind = event.get("type")
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        if kind == "turn/start":
            turns += 1
        elif kind == "step/start":
            steps += 1
        elif kind == "assistant/message":
            usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
            last_usage = usage
            values = sum_usage(usage)
            totals["input"] += values[0]
            totals["output"] += values[1]
            totals["cacheRead"] += values[2]
            totals["cacheWrite"] += values[3]
            last_turn = data.get("turn")
            last_step = data.get("step")
            last_activity = event.get("time")
            source = ((data.get("message") or {}).get("source") if isinstance(data.get("message"), dict) else None) or {}
            if isinstance(source, dict) and source.get("model"):
                model = source["model"]
                provider = source.get("provider") or provider
        elif kind == "request/context":
            context_window = data.get("contextWindow") or context_window
            model = data.get("model") or model
            provider = data.get("provider") or provider
        elif kind == "request/header":
            config = ((data.get("header") or {}).get("config") if isinstance(data.get("header"), dict) else None) or {}
            if isinstance(config, dict):
                model = config.get("model") or model
                provider = config.get("provider") or provider
                effort = config.get("reasoningEffort") or effort
        elif kind == "session/title":
            title = data.get("title") or title
    last_prompt = sum(sum_usage(last_usage or {}))
    depth = header.get("delegationDepth", 0)
    role = "worker" if isinstance(depth, int) and depth > 0 or header.get("origin") == "subagent" else "director"
    return {
        "started_ms": header.get("createdAt"),
        "cwd": header.get("cwd"),
        "title": title,
        "turns": turns,
        "steps": steps,
        "input": totals["input"], "output": totals["output"],
        "cacheRead": totals["cacheRead"], "cacheWrite": totals["cacheWrite"],
        "total": sum(totals.values()),
        "lastPromptTokens": last_prompt,
        "lastTurn": last_turn, "lastStep": last_step,
        "contextWindow": context_window,
        "surfaceTokens": None,
        "model": model, "provider": provider, "effort": effort,
        "sandbox": None, "approval": None, "agentPreset": header.get("agentPreset"),
        "lastActivityMs": last_activity,
        "source": "jsonl",
        "role_hint": role,
        "parent": header.get("parentSession"),
        "delegationDepth": depth if isinstance(depth, int) else None,
    }


def enrich_from_header(row, ref, warnings):
    """Fill a cache row's missing lineage / role / agent fields from the event-log header (Node required)."""
    header, noted = dsh.decode_header(ref.path)
    warnings.extend(f"{ref.session_id}: {w}" for w in noted)
    if not header:
        return row
    depth = header.get("delegationDepth")
    is_child = header.get("origin") == "subagent" or (isinstance(depth, int) and depth > 0)
    row["parent"] = header.get("parentSession")
    row["delegationDepth"] = depth if isinstance(depth, int) else (1 if is_child else 0)
    row["role_hint"] = "worker" if is_child else "director"
    for key, source in (("cwd", "cwd"), ("started_ms", "createdAt")):
        if not row.get(key):
            row[key] = header.get(source)
    row["cwd_verified"] = header.get("cwd")
    row["source"] = row["source"] + "+header" if not row["source"].endswith("+header") else row["source"]
    return row


def build_report(args):
    """(report dict, warnings list); raises SystemExit value through the caller for NO_DATA."""
    warnings = []
    cache_root = pathlib.Path(args.cache_root).expanduser() if args.cache_root else dsh.default_projcache_root()
    sessions_root = pathlib.Path(args.sessions_root).expanduser() if args.sessions_root else dsh.default_sessions_root()
    projections = {}
    cache_problem = None
    if cache_root.is_dir():
        projections = dsh.load_projections(cache_root)
        for projection in projections.values():
            if projection.error:
                warnings.append(f"projection {projection.session_id}: {projection.error}")
    else:
        cache_problem = f"projection cache not found: {cache_root}"
        warnings.append(cache_problem + " (falling back to the event logs, which need Node)")
    session_files = {}
    sessions_problem = None
    try:
        session_files = {ref.session_id: ref for ref in dsh.list_session_files(sessions_root)}
    except dsh.DshError as error:
        sessions_problem = str(error)
        warnings.append(str(error))
    if not projections and not session_files:
        return None, warnings, ("NO_DATA: no sessions found. " + (cache_problem or "") + " "
                                 + (sessions_problem or "")).strip()
    catalog = dsh.agent_catalog(projections)
    since = dsh.parse_day(args.since) if args.since else None
    until = dsh.parse_day(args.until, end=True) if args.until else None
    rows, parents = [], {}
    for session_id in sorted(set(projections) | set(session_files)):
        projection = projections.get(session_id)
        ref = session_files.get(session_id)
        row, row_warnings = build_row(args, session_id, projection, ref, catalog)
        warnings.extend(row_warnings)
        if row is None:
            continue
        if not in_filters(row, args, session_id, since, until):
            cwd = row.get("cwd")
            if cwd and args.project_dir and any(dsh.path_is_under(root, cwd) and not dsh.path_is_under(cwd, root)
                                                for root in args.project_dir):
                parents[cwd] = parents.get(cwd, 0) + 1
            continue
        rows.append(row)
    rows.sort(key=lambda row: (row.get("started_ms") or 0, row["id"]))
    # 2.2.4-ds.4 (B9): a --project-dir below the startup folder matches nothing (WO-DS-006 #16: the repo subfolder)
    args.hints = [f"HINT: {count} session(s) started in {cwd}, a parent of --project-dir; sessions are recorded under "
                  f"their startup folder: use --project-dir {cwd} (and --session <agent> for one worker)"
                  for cwd, count in sorted(parents.items())] if not rows else []
    report = make_report(rows, warnings, args, cache_root, sessions_root, projections, session_files)
    return report, warnings, None


def build_row(args, session_id, projection, ref, catalog):
    """One output row, or (None, [warning]) when neither source can describe the session."""
    warnings = []
    row = None
    if projection is not None and not projection.error:
        row = row_from_projection(projection)
        missing = not row.get("cwd") or not row.get("started_ms") or row.get("turns") in (None, 0) and row.get("total") == 0
        needs_header = args.from_jsonl or missing
        if needs_header and ref is not None and not args.no_fallback:
            if row.get("total") == 0 and row.get("steps") == 0 and not args.from_jsonl:
                try:
                    row = row_from_jsonl(ref, warnings)
                except dsh.DshError as error:
                    warnings.append(f"{session_id}: event-log fallback failed: {error}")
            else:
                try:
                    row = enrich_from_header(row, ref, warnings)
                except dsh.DshError as error:
                    warnings.append(f"{session_id}: header fallback failed: {error}")
    elif ref is not None and not args.no_fallback:
        try:
            row = row_from_jsonl(ref, warnings)
        except dsh.DshError as error:
            return None, [f"{session_id}: no usable source: {error}"]
    else:
        if projection is not None and projection.error:
            return None, [f"{session_id}: projection unreadable ({projection.error}) and no event log"]
        if args.no_fallback:
            return None, [f"{session_id}: only an event log exists and --no-fallback was given"]
        return None, [f"{session_id}: no event log and no projection"]
    role, evidence = dsh.session_role(session_id, projection)
    if row.get("role_hint"):
        role, evidence = row["role_hint"], "event-log-header"
    name, name_source = dsh.session_agent(session_id, role, catalog, projection)
    started = dsh.iso_from_ms(row.get("started_ms"))
    context_window = row.get("contextWindow")
    last_prompt = row.get("lastPromptTokens")
    percent = None
    if context_window and last_prompt is not None:
        percent = round(100.0 * last_prompt / context_window, 1)
    return {
        "id": session_id,
        "short_id": (session_id[len(dsh.ROOT_PREFIX):] if session_id.startswith(dsh.ROOT_PREFIX) else session_id)[:8],
        "role": role,
        "role_evidence": evidence,
        "agent": name,
        "agent_source": name_source,
        "parent": row.get("parent"),
        "delegationDepth": row.get("delegationDepth"),
        "cwd": row.get("cwd"),
        "project": None,
        "title": row.get("title"),
        "started": started,
        "started_ms": row.get("started_ms"),
        "day": dsh.day_of_ms(row.get("started_ms")),
        "last_activity": dsh.iso_from_ms(row.get("lastActivityMs")),
        "turns": row.get("turns"),
        "steps": row.get("steps"),
        "input": row.get("input"),
        "output": row.get("output"),
        "cacheRead": row.get("cacheRead"),
        "cacheWrite": row.get("cacheWrite"),
        "total": row.get("total"),
        "lastPromptTokens": last_prompt,
        "lastTurn": row.get("lastTurn"),
        "lastStep": row.get("lastStep"),
        "contextWindow": context_window,
        "surfaceTokens": row.get("surfaceTokens"),
        "percentUsed": percent,
        "provider": row.get("provider"),
        "model": row.get("model"),
        "effort": row.get("effort"),
        "sandbox": row.get("sandbox"),
        "approval": row.get("approval"),
        "agentPreset": row.get("agentPreset"),
        "source": row.get("source"),
        "log_file": str(ref.path) if ref is not None else None,
        "cache_file": str(projection.path) if projection is not None else None,
    }, warnings


def in_filters(row, args, session_id, since, until):
    if args.project_dir:
        cwd = row.get("cwd")
        if not cwd or not any(dsh.path_is_under(cwd, root) for root in args.project_dir):
            return False
    if since or until:
        started = row.get("started_ms")
        if not isinstance(started, (int, float)) or isinstance(started, bool):
            return False
        when = datetime.datetime.fromtimestamp(started / 1000.0).astimezone()
        if since and when < since:
            return False
        if until and when >= until:
            return False
    if args.session:
        wanted = [value.lower() for value in args.session]
        id_lower = session_id.lower()
        bare = id_lower[len(dsh.ROOT_PREFIX):] if id_lower.startswith(dsh.ROOT_PREFIX) else id_lower
        agent = (row.get("agent") or "").lower()
        label_source = row.get("agent_source") or ""
        label = label_source.split("label-only:", 1)[1].lower() if "label-only:" in label_source else ""
        if not any(w in id_lower or bare.startswith(w) or id_lower.startswith(w) or (agent and w == agent)
                   or (label and w in label) for w in wanted):
            return False
    return True


def make_report(rows, warnings, args, cache_root, sessions_root, projections, session_files):
    days = {}
    for row in rows:
        key = row.get("day") or "unknown"
        day = days.setdefault(key, {"date": key, "sessions": 0, "turns": 0, "steps": 0, "input": 0,
                                    "output": 0, "cacheRead": 0, "cacheWrite": 0, "total": 0})
        day["sessions"] += 1
        for field in ("turns", "steps", "input", "output", "cacheRead", "cacheWrite", "total"):
            if isinstance(row.get(field), (int, float)) and not isinstance(row.get(field), bool):
                day[field] += row[field]
    totals = {"sessions": len(rows), "turns": 0, "steps": 0, "input": 0, "output": 0,
              "cacheRead": 0, "cacheWrite": 0, "total": 0}
    for row in rows:
        for field in ("turns", "steps", "input", "output", "cacheRead", "cacheWrite", "total"):
            if isinstance(row.get(field), (int, float)) and not isinstance(row.get(field), bool):
                totals[field] += row[field]
    return {
        "tool": TOOL,
        "version": REPORT_VERSION,
        "generated_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": {
            "sessions_root": str(sessions_root),
            "sessions_root_readable": sessions_root.is_dir(),
            "cache_root": str(cache_root),
            "cache_root_readable": cache_root.is_dir(),
            "projection_files": len(projections),
            "session_logs": len(session_files),
        },
        "filters": {"project_dir": args.project_dir or [], "since": args.since, "until": args.until,
                    "session": args.session or []},
        "totals": totals,
        "days": [days[key] for key in sorted(days)],
        "sessions": rows,
        "warnings": warnings,
    }


def loops_section(args):
    """2.4.0-ds.6: the LOOPS line (dsh_audit.py loops over the same sessions and filters), or None without --loops."""
    if not getattr(args, "loops", False):
        return None
    if getattr(args, "no_fallback", False):
        return {"status": "NOT_RUN", "line": "LOOPS NOT_RUN --no-fallback: loops read the event logs (Node)"}
    try:
        tool = load_local("dsh_audit")
        result = tool.loops(argparse.Namespace(
            log_root=args.sessions_root, cache_root=args.cache_root, project_dir=args.project_dir, since=args.since,
            until=args.until, session=args.session, events=None, config=getattr(args, "loops_config", None)))
    except Exception as error:  # noqa: BLE001 - a missing Node or log must not cost the usage report
        return {"status": "NOT_RUN", "line": f"LOOPS NOT_RUN {type(error).__name__}: {error}"}
    return {"status": "OK", "line": tool.summary_line(result), "counts": result["counts"],
            "findings_total": result["findings_total"], "not_verified": result["not_verified"],
            "calls": result["calls"], "sessions": result["sessions"]}


def render_text(report):
    lines = []
    source = report["source"]
    filters = report["filters"]
    parts = [f"sessions={report['totals']['sessions']}", f"cache={source['cache_root']}"]
    if filters["project_dir"]:
        parts.append("project=" + ",".join(filters["project_dir"]))
    if filters["since"] or filters["until"]:
        parts.append(f"dates={filters['since'] or '...'}..{filters['until'] or '...'}")
    if filters["session"]:
        parts.append("session=" + ",".join(filters["session"]))
    lines.append("DSH USAGE  " + "  ".join(parts))
    if not source["cache_root_readable"]:
        lines.append(f"WARN projection cache not readable: {source['cache_root']}")
    if not source["sessions_root_readable"]:
        lines.append(f"WARN sessions root not readable: {source['sessions_root']}")
    header = (f"{'ID':8} {'ROLE':8} {'AGENT':12} {'STARTED':19} {'TURNS':>5} {'INPUT':>7} {'OUTPUT':>7} "
              f"{'CACHE_R':>7} {'CACHE_W':>7} {'TOTAL':>7} {'LAST':>7} {'CTX%':>5} {'EFFORT':6} MODEL")
    lines.append(header)
    for row in report["sessions"]:
        lines.append(
            f"{row['short_id']:8} {row['role'][:8]:8} {(row['agent'] or '-')[:12]:12} "
            f"{(row['started'] or '-')[:19]:19} {str(row['turns'] if row['turns'] is not None else '-'):>5} "
            f"{human_tokens(row['input']):>7} {human_tokens(row['output']):>7} "
            f"{human_tokens(row['cacheRead']):>7} {human_tokens(row['cacheWrite']):>7} "
            f"{human_tokens(row['total']):>7} {human_tokens(row['lastPromptTokens']):>7} "
            f"{(str(row['percentUsed']) if row['percentUsed'] is not None else '-'):>5} "
            f"{(row['effort'] or '-')[:6]:6} {row['model'] or '-'}")
    lines.append("")
    lines.append(f"{'DATE':10} {'SESSIONS':>8} {'TURNS':>6} {'INPUT':>8} {'OUTPUT':>8} {'CACHE_R':>8} {'CACHE_W':>8} {'TOTAL':>8}")
    for day in report["days"]:
        lines.append(f"{day['date']:10} {day['sessions']:>8} {day['turns']:>6} {human_tokens(day['input']):>8} "
                     f"{human_tokens(day['output']):>8} {human_tokens(day['cacheRead']):>8} "
                     f"{human_tokens(day['cacheWrite']):>8} {human_tokens(day['total']):>8}")
    totals = report["totals"]
    lines.append(f"{'TOTAL':10} {totals['sessions']:>8} {totals['turns']:>6} {human_tokens(totals['input']):>8} "
                 f"{human_tokens(totals['output']):>8} {human_tokens(totals['cacheRead']):>8} "
                 f"{human_tokens(totals['cacheWrite']):>8} {human_tokens(totals['total']):>8}")
    if report.get("loops"):
        lines.append(report["loops"]["line"])
    if report["warnings"]:
        lines.append(f"WARNINGS {len(report['warnings'])}")
        for warning in report["warnings"][:10]:
            lines.append("  ~ " + warning)
        if len(report["warnings"]) > 10:
            lines.append(f"  ... {len(report['warnings']) - 10} more (see --json)")
    return "\n".join(lines)


EFFORTS = ("off", "minimal", "low", "medium", "high", "xhigh", "max")


def order_effort(text):
    """2.2.4-ds.4 (B8): (worker name, model, effort) from a work order's PRIMARY_WORKER and MODEL / EFFORT lines.
    The worker is the name in 「」 (子代理「w1」), else the first word; None for what the order does not say."""
    worker = re.search(r"^[ \t]*PRIMARY_WORKER[ \t]*=[ \t]*(.*)$", text, re.M)
    name = None
    if worker:
        quoted = re.search(r"「([^」]+)」", worker.group(1))
        name = quoted.group(1).strip() if quoted else (worker.group(1).split() or [None])[0]
    line = re.search(r"^[ \t]*MODEL[ \t]*/[ \t]*EFFORT[ \t]*=[ \t]*(.*)$", text, re.M)
    model = effort = None
    if line:
        parts = line.group(1).split("/")
        model = parts[0].strip() or None
        found = re.match(r"\s*([A-Za-z]+)", parts[1]) if len(parts) > 1 else None
        effort = found.group(1).lower() if found else None
    return name, model, effort


def effort_lines(order_text, order_id, rows):
    """2.2.4-ds.4 (B8, WO-DS-006 #14): one `EFFORT_ACTUAL <WO> agent=<name> effort=<session> order=<order>` line per
    session of the order's worker (the lead pastes it into DIRECTOR_LOG next to DISPATCH), and a shadow WARN when
    the session ran at another effort than the order says (the trial: order high, every session max)."""
    name, _, wanted = order_effort(order_text)
    if not name:
        return ["SHADOW WARN: the order has no PRIMARY_WORKER name; pass --session <agent>"], 0
    mine = [row for row in rows if (row.get("agent") or "").lower() == name.lower()]
    if not mine:
        return [f"SHADOW WARN: no DSH session of agent {name} matched the filters (add --project-dir <startup folder>)"], 0
    lines, off = [], 0
    for row in mine:
        actual = (row.get("effort") or "UNKNOWN").lower()
        lines.append(f"EFFORT_ACTUAL {order_id} agent={name} effort={actual} order={wanted or 'UNKNOWN'} "
                     f"session={str(row.get('id'))[:20]} started={row.get('started') or '?'}")
        if wanted and actual != wanted:
            off += 1
            lines.append(f"SHADOW WARN: {order_id} says EFFORT {wanted}, the session ran at {actual}; dispatch with "
                         f"subagent(..., reasoning_effort=\"{wanted}\") or fix the order (docs/11)")
    return lines, off


def write_no_data(args, reason, warnings):
    """2.2.4-ds.4 (B9, WO-DS-006 #16): --out on NO_DATA. Before, the exit 2 came before --out was written, so a
    caller saw rc=2 and no file and could not tell why. Now the file holds the reason (exit stays 2)."""
    if not args.out:
        return
    out = pathlib.Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    data = {"tool": "dsh_usage", "status": "NO_DATA", "reason": reason, "hints": getattr(args, "hints", []),
            "filters": {"project_dir": args.project_dir, "since": args.since, "until": args.until,
                        "session": args.session}, "warnings": warnings[:50], "sessions": []}
    out.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"WROTE {out} (NO_DATA)", file=sys.stderr)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sessions-root", help="DSH sessions root (default %%USERPROFILE%%\\.dsh\\sessions)")
    ap.add_argument("--cache-root", help="DSH projection cache root (default <DSH_HOME>/storages/session_projcache/sessions)")
    ap.add_argument("--project-dir", action="append", default=[],
                    help="only sessions whose STARTUP folder is this folder or below (subagent sessions are logged "
                         "under the director's startup folder; use --session <agent> for one worker; repeatable)")
    ap.add_argument("--since", help="local date YYYY-MM-DD, inclusive (session start)")
    ap.add_argument("--until", help="local date YYYY-MM-DD, inclusive (session start)")
    ap.add_argument("--session", action="append", default=[],
                    help="only this session id / id prefix / agent name (repeatable)")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    ap.add_argument("--out", help="also write the JSON report to this file")
    ap.add_argument("--effort-check", metavar="ORDER", help="2.2.4-ds.4: print `EFFORT_ACTUAL <WO> ...` for the "
                    "sessions of the order's PRIMARY_WORKER and a shadow WARN when their effort differs from the "
                    "order's MODEL / EFFORT (exit 0; paste the line into DIRECTOR_LOG)")
    ap.add_argument("--loops", action="store_true", help="2.4.0-ds.6: add the LOOPS line (dsh_audit.py loops over the "
                    "same sessions; needs Node, slow on many sessions)")
    ap.add_argument("--loops-config", help="loops config JSON for --loops (thresholds, allow list)")
    fallback = ap.add_mutually_exclusive_group()
    fallback.add_argument("--from-jsonl", action="store_true",
                          help="confirm roles/lineage from the event-log headers (needs Node)")
    fallback.add_argument("--no-fallback", action="store_true",
                          help="never read the event logs; the projection cache only (no Node)")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    effort_order_text = effort_order_id = None
    if a.effort_check:
        order_path = pathlib.Path(a.effort_check)
        if not order_path.is_file():
            print(f"dsh_usage: --effort-check {a.effort_check}: file not found", file=sys.stderr)
            return 2
        effort_order_text = order_path.read_text(encoding="utf-8-sig")
        title = re.search(r"^#\s+([A-Za-z]+(?:-[A-Za-z]+)*-\d+)", effort_order_text, re.M)
        stem = re.match(r"[A-Za-z]+(?:-[A-Za-z]+)*-\d+", order_path.stem)
        effort_order_id = (title or stem).group(1 if title else 0) if (title or stem) else order_path.stem
    for field in ("since", "until"):
        value = getattr(a, field)
        if value:
            try:
                dsh.parse_day(value)
            except ValueError:
                print(f"dsh_usage: --{field} {value} is not YYYY-MM-DD", file=sys.stderr)
                return 2
    a.hints = []
    try:
        report, warnings, no_data = build_report(a)
    except dsh.DshError as error:
        print(f"NO_DATA: {error}", file=sys.stderr)
        write_no_data(a, f"NO_DATA: {error}", [])
        return 2
    if report is None or not report["sessions"]:
        reason = no_data or (f"NO_DATA: {len(warnings)} session(s) found but none matched the filters"
                             if warnings else "NO_DATA: no sessions matched the filters")
        print(reason)
        for line in a.hints + ["  ~ " + warning for warning in warnings[:10]]:
            print(line)
        write_no_data(a, reason, warnings)
        return 2
    looped = loops_section(a)
    if looped is not None:
        report["loops"] = looped
    if a.out:
        out = pathlib.Path(a.out).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"WROTE {out}", file=sys.stderr)
    if a.effort_check:
        for line in effort_lines(effort_order_text, effort_order_id, report["sessions"])[0]:
            print(line)
        return 0
    if a.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        print(render_text(report))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
