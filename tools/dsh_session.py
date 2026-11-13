r"""Shared library of the DIRECTOR-WORK DeepSeek Harness (DSH) edition: read DSH session data.

No side effects on import: nothing is printed, written or listed until a function is called.

DSH keeps two things per session (both under the DSH home, default %USERPROFILE%\.dsh, override DSH_HOME):

  1. a plain-JSON projection cache
       storages/session_projcache/sessions/<session-id>.json
     One file per session. Verified shape (DSH desktop 0.2.2, projection version 7):
       record.identity            {formatVersion, createdAt(ms), cwd, isSeeded, inheritedEventCount}
       record.rows.tokenUsage.val {totals:{uncachedInputTokens, outputTokens, cacheReadTokens, cacheWriteTokens},
                                   last:{turn, step, buckets:{... the same four ...}}}
       record.rows.contextPressure.val {surfaceTokens, contextWindow, pressureTokens, sampledSurfaceTokens}
       record.rows.sessionStats.val    {turns, steps, llmMs, toolMs, ..., lastTurn, openStep, pendingCalls}
       record.rows.modelSelection.val  {lastUsed:{provider, model, reasoningEffort}, pending}
       record.rows.sandboxMode.val, approvalState.val {policy, turnOpen}, agentPreset.val, title.val,
       record.rows.permissions.val {preset, sandbox, approval, seeded}
       record.rows.subagentCatalog.val {head:{values:[{version, childId, childCreatedAt, mode, label, name}]}}
       record.rows.subagent.val {identity:{mode, label, seq}}     (only in subagent sessions)
       record.rows.agentTeam.val {id, tasks:[{id, ..., ownerId, ownerName}], ...}
     Pure Python: dsh_usage.py reads this first and needs no Node.

  2. the append-only event log
       sessions/--<normalised cwd>--/<session-id>/session.v4.jsonl.zstd
     A concatenation of independently compressed zstd frames; the concatenated payload is newline-delimited
     JSON events (session header, assistant/message with usage, tool/call, tool/ptc-dispatch, tool/result, ...).
     Python 3.12 has no zstd module, so Node 22+ (zlib.zstdDecompressSync) is required for this source.
     dsh_audit.py needs it; dsh_usage.py uses it only as a fallback for fields the cache lacks.

Session identity, verified against real DSH sessions: a root (human) session has an id of the form
"session-<uuid>" and its projection cache has no subagent identity; a subagent session has a bare "<uuid>" id and a
subagent identity row. The parent root's subagentCatalog names its children (childId -> name, e.g. "tools-port").
The root agent is called "lead" (docs/01_roles_authority.md, docs/11_dsh_operations.md); a root session may also be
marked by
".sessions/delegationDepth" 0 in the event-log header.

Node is found as: env DSH_NODE, else <DSH_HOME>/dsh-runtimes/*/dependencies/node/bin/node.exe (or .../node), else
"node"/"node.exe" on PATH. Set DSH_NODE to override. All paths are handled with pathlib so Windows backslashes work.

Errors are clean exceptions: DshError (base), NodeMissing (no Node to decode zstd), DecodeError (file/frame cannot be
decoded), SessionNotFound. Callers print the message and choose their own exit code.
"""
import datetime
import glob
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import traceback

VERSION = 1
SESSION_FILE = "session.v4.jsonl.zstd"
FRAME_MAGIC = b"\x28\xb5\x2f\xfd"
PROJECTION_VERSION = 7
ROOT_PREFIX = "session-"
ROOT_AGENT = "lead"

_DECODER = r"""
const fs = require('fs'), zlib = require('zlib');
const MAGIC = Buffer.from([0x28, 0xb5, 0x2f, 0xfd]);
function positions(buf) {
  const out = [];
  let i = 0;
  for (;;) {
    const k = buf.indexOf(MAGIC, i);
    if (k < 0) break;
    out.push(k);
    i = k + 4;
  }
  return out;
}
function frameText(buf, start, end) {
  return zlib.zstdDecompressSync(buf.subarray(start, end)).toString('utf8');
}
// Split on the zstd magic but keep only splits that really decompress: a magic sequence inside compressed data is
// not a frame boundary, so a candidate that fails is skipped and the frame is merged with the next candidate.
function decode(buf) {
  const pos = positions(buf);
  const text = [], warnings = [];
  if (!pos.length) { warnings.push('no zstd frame found'); return { text: '', warnings: warnings }; }
  let start = pos[0], cand = 1;
  while (start < buf.length) {
    let done = false;
    while (cand < pos.length) {
      const end = pos[cand];
      try { text.push(frameText(buf, start, end)); start = end; cand++; done = true; break; }
      catch (e) { cand++; }
    }
    if (!done) {
      try { text.push(frameText(buf, start, buf.length)); start = buf.length; }
      catch (e) {
        warnings.push('last frame not decoded (' + String(e && e.message || e) + '); the session may still be being written');
        break;
      }
    }
  }
  return { text: text.join(''), warnings: warnings };
}
const mode = process.argv[1];
const files = process.argv.slice(2);
if (mode === 'header') {
  for (const f of files) {
    const out = { path: f, ok: false, line: null, warnings: [] };
    let buf = null;
    try { buf = fs.readFileSync(f); } catch (e) { out.warnings.push('cannot read: ' + String(e && e.message || e)); }
    if (buf) {
      const pos = positions(buf);
      if (!pos.length) {
        out.warnings.push('no zstd frame found');
      } else {
        let start = pos[0], cand = 1, text = '';
        while (text.indexOf('\n') < 0 && start < buf.length) {
          let done = false;
          while (cand < pos.length) {
            const end = pos[cand];
            try { text += frameText(buf, start, end); start = end; cand++; done = true; break; }
            catch (e) { cand++; }
          }
          if (!done) {
            try { text += frameText(buf, start, buf.length); start = buf.length; }
            catch (e) { out.warnings.push('last frame not decoded'); break; }
          }
        }
        const nl = text.indexOf('\n');
        const line = (nl >= 0 ? text.slice(0, nl) : text).replace(/^\uFEFF/, '').trim();
        if (line) { out.line = line; out.ok = true; }
      }
    }
    process.stdout.write(JSON.stringify(out) + '\n');
  }
} else {
  for (const f of files) {
    let buf = null;
    try { buf = fs.readFileSync(f); } catch (e) {
      process.stdout.write('' );
      process.stderr.write(JSON.stringify({ path: f, error: 'cannot read: ' + String(e && e.message || e) }) + '\n');
      continue;
    }
    const got = decode(buf);
    process.stdout.write(got.text);
    process.stderr.write(JSON.stringify({ path: f, warnings: got.warnings }) + '\n');
  }
}
"""


class DshError(Exception):
    """Base: the library cannot give the caller what it asked for."""


class NodeMissing(DshError):
    """No Node.js executable is available, so zstd session logs cannot be decoded."""


class DecodeError(DshError):
    """A session log or projection file cannot be decoded."""


class SessionNotFound(DshError):
    """A requested session id / prefix does not match any session file."""


# ---------------------------------------------------------------- paths and Node


def dsh_home():
    r"""The DSH home: env DSH_HOME, else %USERPROFILE%\.dsh (or ~/.dsh)."""
    value = os.environ.get("DSH_HOME")
    return pathlib.Path(value).expanduser() if value else pathlib.Path.home() / ".dsh"


def default_sessions_root():
    """The sessions root: env DSH_SESSIONS_ROOT, else <DSH_HOME>/sessions."""
    value = os.environ.get("DSH_SESSIONS_ROOT")
    return pathlib.Path(value).expanduser() if value else dsh_home() / "sessions"


def default_projcache_root():
    """The projection cache root: env DSH_PROJCACHE_ROOT, else <DSH_HOME>/storages/session_projcache/sessions."""
    value = os.environ.get("DSH_PROJCACHE_ROOT")
    return pathlib.Path(value).expanduser() if value else dsh_home() / "storages" / "session_projcache" / "sessions"


def find_node():
    """Path to a Node executable that has zlib.zstdDecompressSync, or None.

    Looked up in this order: env DSH_NODE (an executable or a folder holding one), DSH_HOME/dsh-runtimes/*/
    dependencies/node/bin/node.exe (and .../node), then "node"/"node.exe" on PATH.
    """
    candidate = os.environ.get("DSH_NODE")
    if candidate:
        found = _node_candidate(pathlib.Path(candidate))
        if found:
            return str(found)
    pattern = str(dsh_home() / "dsh-runtimes" / "*" / "dependencies" / "node" / "bin" / "node*")
    for path in sorted(glob.glob(pattern), reverse=True):
        found = _node_candidate(pathlib.Path(path))
        if found:
            return str(found)
    found = shutil.which("node") or shutil.which("node.exe")
    return found or None


def _node_candidate(path):
    """PATH as a Node executable: the file itself, or node.exe/node inside a folder."""
    if path.is_file():
        return path
    if path.is_dir():
        for name in ("node.exe", "node"):
            inner = path / name
            if inner.is_file():
                return inner
    return None


def require_node():
    """The Node executable, or NodeMissing with the places that were tried."""
    node = find_node()
    if not node:
        raise NodeMissing("no Node.js found to decode zstd session logs; set DSH_NODE to a Node 22+ executable "
                          f"or install the DSH runtime under {dsh_home() / 'dsh-runtimes'} "
                          "(dsh_usage.py can still read the plain-JSON projection cache)")
    return node


def _run_node(mode, paths, timeout=300):
    node = require_node()
    command = [node, "-e", _DECODER, mode] + [str(p) for p in paths]
    try:
        done = subprocess.run(command, capture_output=True, timeout=timeout)
    except (OSError, subprocess.SubprocessError) as error:
        raise DecodeError(f"node failed to run ({node}): {error}") from error
    stdout = done.stdout.decode("utf-8", "replace")
    stderr = done.stderr.decode("utf-8", "replace")
    if done.returncode != 0:
        raise DecodeError(f"node decoder exited {done.returncode}: {_short(stderr)}")
    return stdout, stderr


def _short(text, limit=400):
    text = " ".join((text or "").split())
    return text if len(text) <= limit else text[:limit] + "..."


# ---------------------------------------------------------------- session log decoding


class DecodeResult:
    """Decoded payload text plus non-fatal warnings."""

    def __init__(self, text, warnings=None):
        self.text = text
        self.warnings = list(warnings or [])

    def __repr__(self):
        return f"DecodeResult(text={len(self.text)} chars, warnings={len(self.warnings)})"


def decode_session(path, timeout=300):
    """Decoded text of one .jsonl.zstd session log (DecodeResult), sorted by file order.

    Raises NodeMissing when no Node exists and DecodeError when no frame can be decoded."""
    path = pathlib.Path(path)
    if not path.is_file():
        raise DecodeError(f"no such session log: {path}")
    stdout, stderr = _run_node("all", [path], timeout=timeout)
    warnings = []
    for line in stderr.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            note = json.loads(line)
        except ValueError:
            warnings.append(_short(line))
            continue
        for warning in note.get("warnings") or []:
            warnings.append(str(warning))
        if note.get("error"):
            warnings.append(str(note["error"]))
    if stdout and not warnings:
        pass
    if not stdout and warnings:
        raise DecodeError(f"{path}: {warnings[-1]}")
    return DecodeResult(stdout, warnings)


def decode_headers(paths, timeout=300):
    """{path: (header dict or None, warnings list)} for many logs in ONE Node process (fast enumeration).

    A header is the first JSON event of the log ({"type": "session", ...})."""
    paths = [pathlib.Path(p) for p in paths]
    result = {str(p): (None, []) for p in paths}
    if not paths:
        return result
    stdout, stderr = _run_node("header", paths, timeout=timeout)
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            note = json.loads(line)
        except ValueError:
            continue
        key = str(note.get("path"))
        warnings = [str(w) for w in (note.get("warnings") or [])]
        header = None
        if note.get("ok") and note.get("line"):
            try:
                header = json.loads(note["line"])
            except ValueError:
                warnings.append("first line is not JSON")
        result[key] = (header if isinstance(header, dict) else None, warnings)
    for line in stderr.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            note = json.loads(line)
        except ValueError:
            continue
        key = str(note.get("path"))
        if key in result:
            result[key][1].append(str(note.get("error") or "node decoder warning"))
    return result


def decode_header(path, timeout=300):
    """(header dict or None, warnings) of one log, one Node process."""
    return decode_headers([path], timeout=timeout)[str(pathlib.Path(path))]


def parse_jsonl(text):
    """([event dict], [warning]) from newline-delimited JSON text; bad lines are warned about, not fatal."""
    events, warnings = [], []
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip().lstrip("\ufeff")
        if not line:
            continue
        try:
            event = json.loads(line)
        except ValueError:
            warnings.append(f"line {number}: not JSON; skipped")
            continue
        if not isinstance(event, dict):
            warnings.append(f"line {number}: not a JSON object; skipped")
            continue
        events.append(event)
    return events, warnings


def read_events(path, timeout=300):
    """([event dict], [warning]) of one session log; raises NodeMissing/DecodeError."""
    result = decode_session(path, timeout=timeout)
    events, warnings = parse_jsonl(result.text)
    return events, result.warnings + warnings


# ---------------------------------------------------------------- session files


class SessionRef:
    """One session log found under the sessions root."""

    def __init__(self, path, project_dir=None):
        self.path = pathlib.Path(path)
        self.project_dir = project_dir
        self.session_id = self.path.parent.name
        try:
            stat = self.path.stat()
        except OSError:
            stat = None
        self.mtime = stat.st_mtime if stat else 0.0
        self.size = stat.st_size if stat else 0

    @property
    def dir_name(self):
        return self.path.parent.name

    def __repr__(self):
        return f"SessionRef({self.session_id}, {self.path})"


def list_session_files(sessions_root=None):
    """[SessionRef] for every session log under SESSIONS_ROOT (one level of project folders).

    Raises DshError when the root is missing so tools can print one clear message."""
    root = pathlib.Path(sessions_root) if sessions_root else default_sessions_root()
    if not root.is_dir():
        raise DshError(f"sessions root not found: {root} (pass --sessions-root, or set DSH_SESSIONS_ROOT)")
    paths = sorted(root.glob("*/*/session.v*.jsonl.zstd"))
    if not paths:
        paths = sorted(root.glob("*/session.v*.jsonl.zstd"))
    if not paths:
        paths = sorted(root.rglob("session.v*.jsonl.zstd"))
    return [SessionRef(path, path.parent.parent.name) for path in paths]


def find_session_files(root=None, session_filters=None):
    """SessionRef list restricted by id / id-prefix / session-dir-name filters (case-insensitive)."""
    sessions = list_session_files(root)
    if session_filters:
        wanted = [w.lower() for w in session_filters if w]
        sessions = [s for s in sessions
                    if any(w in (s.session_id.lower(), s.session_id.lower().removeprefix(ROOT_PREFIX))
                           or (s.session_id.lower().removeprefix(ROOT_PREFIX)).startswith(w)
                           or s.session_id.lower().startswith(w) for w in wanted)]
    return sessions


def read_session_header(session, node=None):
    """(header dict or None, warnings) for one SessionRef (Node required)."""
    return decode_header(session.path)


# ---------------------------------------------------------------- projection cache


class Projection:
    """One projection-cache JSON file (record part) with its read error, if any."""

    def __init__(self, path, session_id, record=None, version=None, error=None, modified=0.0):
        self.path = pathlib.Path(path)
        self.session_id = session_id
        self.record = record if isinstance(record, dict) else None
        self.version = version
        self.error = error
        self.modified = modified

    def row(self, key, default=None):
        """record.rows[key].val (DSH 0.2.2), or the raw row if it has no "val" wrapper."""
        if not self.record:
            return default
        rows = self.record.get("rows")
        if not isinstance(rows, dict):
            return default
        row = rows.get(key)
        if isinstance(row, dict) and "val" in row:
            return row["val"]
        return default if row is None else row

    def identity(self):
        value = self.record.get("identity") if self.record else None
        return value if isinstance(value, dict) else {}

    def __repr__(self):
        return f"Projection({self.session_id}, error={self.error!r})"


def read_projection(path):
    """A Projection read from one cache file; a read/parse error is kept on the object, not raised."""
    path = pathlib.Path(path)
    session_id = path.stem
    try:
        modified = path.stat().st_mtime
    except OSError:
        modified = 0.0
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as error:
        return Projection(path, session_id, error=f"cannot read: {error}", modified=modified)
    try:
        data = json.loads(text)
    except ValueError as error:
        return Projection(path, session_id, error=f"not JSON: {error}", modified=modified)
    if not isinstance(data, dict):
        return Projection(path, session_id, error="not a JSON object", modified=modified)
    record = data.get("record")
    if not isinstance(record, dict):
        return Projection(path, session_id, error="no record object", version=data.get("version"),
                          modified=modified)
    return Projection(path, session_id, record=record, version=data.get("version"), modified=modified)


def load_projections(cache_root=None, session_ids=None):
    """{session_id: Projection} for every .json under the projection cache root.

    Raises DshError when the root is missing. Files that cannot be read keep an error on their Projection."""
    root = pathlib.Path(cache_root) if cache_root else default_projcache_root()
    if not root.is_dir():
        raise DshError(f"projection cache not found: {root} (pass --cache-root, or set DSH_PROJCACHE_ROOT)")
    out = {}
    for path in sorted(root.glob("*.json")):
        projection = read_projection(path)
        if session_ids is not None and projection.session_id not in session_ids:
            continue
        out[projection.session_id] = projection
    return out


# ---------------------------------------------------------------- identity, role, agent names


def session_role(session_id, projection=None):
    """("director" | "worker" | "unknown", evidence) for one session.

    worker    the projection has a subagent descriptor (rows.subagent.val.identity)
    director  id starts with "session-" and there is no subagent descriptor (root/human session)
    unknown   neither can be proven from the cache; the caller may fall back to the event-log header
              (delegationDepth 0 = director, >=1 = worker)."""
    if projection is not None and projection.record:
        subagent = projection.row("subagent")
        if isinstance(subagent, dict) and isinstance(subagent.get("identity"), dict) and subagent["identity"]:
            return "worker", "projection:subagent-descriptor"
        catalog = projection.row("subagentCatalog")
        head = ((catalog or {}).get("head") or {}).get("values") if isinstance(catalog, dict) else None
        team = projection.row("agentTeam")
        if session_id.startswith(ROOT_PREFIX):
            return "director", "session-id-prefix"
        if head or (isinstance(team, dict) and team.get("tasks")):
            return "director", "projection:child-catalog"
    if session_id.startswith(ROOT_PREFIX):
        return "director", "session-id-prefix"
    return "unknown", "not-provable-from-cache"


def agent_catalog(projections):
    """{child_session_id: {"name", "label", "parent"}} from every parent projection's subagentCatalog and task owners."""
    catalog = {}
    for parent_id, projection in projections.items():
        if projection is None or not projection.record:
            continue
        value = projection.row("subagentCatalog")
        head = ((value or {}).get("head") or {}).get("values") if isinstance(value, dict) else None
        for entry in head or []:
            if not isinstance(entry, dict):
                continue
            child = entry.get("childId")
            if isinstance(child, str) and child and child not in catalog:
                catalog[child] = {"name": _text(entry.get("name")), "label": _text(entry.get("label")),
                                  "parent": parent_id}
        team = projection.row("agentTeam")
        tasks = team.get("tasks") if isinstance(team, dict) else None
        for task in tasks or []:
            if not isinstance(task, dict):
                continue
            owner, name = task.get("ownerId"), _text(task.get("ownerName"))
            if isinstance(owner, str) and owner and name and owner not in catalog:
                catalog[owner] = {"name": name, "label": None, "parent": parent_id}
    return catalog


def _text(value):
    return value if isinstance(value, str) and value else None


def session_agent(session_id, role, catalog, projection=None):
    """(agent name, source) — the root is "lead" by convention, a subagent is named by its parent's catalog."""
    entry = catalog.get(session_id)
    if entry and entry.get("name"):
        return entry["name"], "parent-catalog"
    if role == "director":
        return ROOT_AGENT, "convention:root-is-lead"
    if projection is not None:
        subagent = projection.row("subagent")
        label = ((subagent or {}).get("identity") or {}).get("label") if isinstance(subagent, dict) else None
        if isinstance(label, str) and label:
            return None, "label-only:" + label
    return None, "unknown"


# ---------------------------------------------------------------- small shared helpers


def norm_path(value):
    """Absolute, normcase path text for comparing paths on Windows."""
    try:
        text = os.path.expanduser(os.fspath(value))
        text = os.path.abspath(text)
    except (OSError, ValueError):
        text = str(value)
    return os.path.normcase(text)


def path_is_under(path, root):
    """Whether PATH is ROOT or lies below it (normcase, absolute)."""
    if not path or not root:
        return False
    target, base = norm_path(path), norm_path(root)
    return target == base or target.startswith(base.rstrip(os.sep) + os.sep)


def iso_from_ms(milliseconds):
    """"2026-11-12T23:11:05.088+08:00" (local offset) from epoch milliseconds; None when not a number."""
    if not isinstance(milliseconds, (int, float)) or isinstance(milliseconds, bool):
        return None
    return datetime.datetime.fromtimestamp(milliseconds / 1000.0).astimezone().isoformat(timespec="milliseconds")


def parse_day(text, end=False):
    """Aware local datetime for a YYYY-MM-DD date (end=True: the next day, for an inclusive --until).

    Raises ValueError when the text is not a date."""
    day = datetime.datetime.strptime(text, "%Y-%m-%d").date()
    when = datetime.datetime.combine(day, datetime.time.min).astimezone()
    if end:
        when += datetime.timedelta(days=1)
    return when


def day_of_ms(milliseconds):
    """Local YYYY-MM-DD from epoch milliseconds."""
    if not isinstance(milliseconds, (int, float)) or isinstance(milliseconds, bool):
        return None
    return datetime.datetime.fromtimestamp(milliseconds / 1000.0).astimezone().strftime("%Y-%m-%d")


def event_time_ms(event):
    """Epoch milliseconds of an event (event.time, else event.data.time), or None."""
    value = event.get("time")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    return None


def event_seq(event):
    value = event.get("seq")
    return value if isinstance(value, int) and not isinstance(value, bool) else -1


def session_header(events):
    """The first {"type": "session"} event of a session, or {}."""
    for event in events:
        if event.get("type") == "session":
            return event
    return {}
