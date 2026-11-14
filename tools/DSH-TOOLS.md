# DSH edition tools

Tools of the DIRECTOR-WORK DeepSeek Harness (DSH) edition. Run every Python tool as:

    python -I -X utf8 tools/<tool>.py ...

DSH has no hooks and no PO page, so nothing fires automatically: dsh_usage / dsh_audit / dsh_doctor read the DSH
session files after the fact, and dsh_guard is a voluntary self-check the worker or Director runs by hand.

## New DSH tools

- dsh_session.py (library, no CLI) - Node discovery, decode of session.v4.jsonl.zstd, session listing, role / agent
  name mapping from the parent's catalog, and the plain-JSON projection cache.
- dsh_usage.py - token / context report per session plus daily totals, from the projection cache (no Node).
  `dsh_usage.py [--sessions-root DIR] [--cache-root DIR] [--project-dir PATH] [--since YYYY-MM-DD] [--until YYYY-MM-DD]
  [--session ID|PREFIX|AGENT] [--json] [--out FILE] [--from-jsonl | --no-fallback]`
  exit 0 report written, 2 NO_DATA / missing root / usage error.
- dsh_audit.py - rebuild the hash-chained action audit (same schema as audit_log.py / report_vs_audit.py) from the
  session event logs; needs Node 22+ for zstd. It is after-the-fact reconstruction, not a live hook. Since
  2.2.1-ds.1 line 1 of a built log is kind=rebuild with a `source` field (session log names, sha256, sizes), the same
  first line as upstream transcript_audit.py, and report_vs_audit.py prints a note for it; tool calls start at seq 2.
  `dsh_audit.py build --out FILE [--force] [--log-root DIR] [--cache-root DIR] [--project-dir PATH] [--since DATE]
  [--until DATE] [--session ID|PREFIX|AGENT] [--json]`
  `dsh_audit.py verify --log FILE [--from N --to M] [--anchor-log FILE] [--anchor-rev REV --anchor-path PATH [--repo DIR]]`
  exit 0 written / verified, 1 refused (output exists) or write problem, 2 cannot run.
- dsh_doctor.py - environment self-check: python, node, DSH home / sessions / projection cache, latest session decode,
  profile model / effort, latest session sandbox / approval, git, required tools, docs and templates.
  `dsh_doctor.py [--tools-dir DIR] [--sessions-root DIR] [--cache-root DIR] [--profile-config FILE] [--json]`
  exit 0 no FAIL, 1 any FAIL, 2 the check itself cannot run.
- dsh_setup_check.py - validate a DIRECTOR folder built by the DSH BOOTSTRAP: required files, the PENDING_METHOD line,
  PO_PENDING entry fields, the RESUME_STATE header and director_work.json. 2.2.1-ds.1 shadow checks (printed as
  `~ shadow:`; `--strict` makes them fail): an ID used twice, filled RESUME header values and a dated UPDATED line
  (gate_check --resume rule), director_work.json schema_version / mode / *_pattern regexes / po_pending_files types.
  2.2.2-ds.3 (upstream 2.2.2 setup_check): RESUME_SIZE (the RESUME_STATE over resume.max_bytes / max_line_bytes) and
  the resume / base_ref / release blocks of director_work.json, shadow too.
  `dsh_setup_check.py [--json] [--strict] DIR [DIR ...]`
  exit 0 no problems, 1 any problem, 2 usage error.
- dsh_guard.py - advisory risky-command check (no hook; run it yourself): force push, push, delete, send / publish,
  pay, config, secrets, always-forbidden git / process patterns, and the pause flag.
  `dsh_guard.py --command "git push" [--mode remind|block] [--profile worker|director] [--pause-flag FILE]
  [--rules FILE] [--shell bash|powershell|cmd] [--cwd DIR] [--json]`
  exit 0 clean, 1 remind (default), 2 block / pause flag exists / rules unreadable.
- release.py (2.2.2-ds.3) - release this repository in one pass: fetch, any modified or staged tracked file stops
  (dry run too; VERSION and CHANGELOG are read from HEAD), HEAD vs <remote>/<branch> (UP_TO_DATE / AHEAD /
  BEHIND / DIVERGED; --merge merges into release/<version> with --no-ff and stops on conflicts), VERSION = CHANGELOG top
  and the tag sorts above every remote tag, selftest, a scan of everything about to go public, then push (no --force),
  annotated tag, `gh release create --verify-tag --latest`, each checked with ls-remote / gh release view. Dry run by
  default. Glue over git and gh: release-please / semantic-release need CI and conventional commits (see CHANGELOG).
  `release.py [--repo DIR] [--config FILE] [--version X] [--merge] [--execute]`
  exit 0 dry run clean or release done, 1 a step failed (a NEXT: line says what to do), 2 cannot run.
- verify_dsh_run.py (2.2.2-ds.3) - verify a DSH trial run of one spec-first order from the files it left and the session
  logs (R01-R21 repo half, D01-D14 DSH half; the WO-101 checks of _work/ds2-openspec, made generic). The run's names
  come from a JSON config (templates/VERIFY_DSH_RUN.json). Unit tests: test_verify_dsh_run.py.
  `verify_dsh_run.py --config FILE [--project-dir DIR] [--repo DIR] [--order FILE] [--out DIR] [--sessions-root DIR]
  [--cache-root DIR] [--no-dsh]`
  exit 0 PASS, 1 any FAIL, 2 SKIP only (INCOMPLETE) or cannot run.
- selftest_ds.py - offline smoke tests of this toolchain (help, usage, audit + report, setup fixture, generated status,
  doctor, guard, gate hash, evidence record, report matching). `selftest_ds.py [--verbose] [--keep]`
  exit 0 all pass (SKIP is not a failure), 1 any FAIL.

## Kept upstream tools (platform-neutral)

gate_check.py (2.2.2-ds.3: --resume prints `~ shadow: RESUME_SIZE` over resume.max_bytes / max_line_bytes, --strict
fails it; --order fetches and compares the BASE_REF commit with the remote branch; stale or missing
is a `~ WARN BASE_REF` note, --strict-base fails it; a failed fetch is said, never passed; --report-skeleton ORDER
prints a TASK REPORT with the order's fields, hash and AC rows filled in plus the evidence / scope_check / --match
commands, so a DSH worker does not read the checker's source to learn the format), scope_check.py, evidence_record.py, report_vs_audit.py (DSH wrapped-command matching; 2.2.1 cut-line
JSON decoding and the 2-real-word rule),
trace_report.py, round_check.py, status_gen.py (po_pending / orders / audit; PENDING_METHOD instead of PO_PAGE_URL),
metrics_report.py, memory_size_check.py (defaults to the nearest AGENTS.md; 2.2.2-ds.3 as upstream 2.2.2: --kind resume,
several --file, --glob, --workstreams, one line per file and `SIZE: PASS|OVER|MISSING`), resume_archive.py
(2.2.2-ds.3, upstream 2.2.2 unchanged: moves old RESUME_STATE sections word for word to RESUME_HISTORY_<YYYYMMDD>.md;
dry-run by default, --execute backs up, verifies and restores on any failed check), secret_mask.py, pause_ctl.py (no hook
reads the flag in DSH: workers check it themselves),
audit_log.py (verify / head / cite / recover; append is unused in DSH), vocabulary.json, guard_rules.json (used by
dsh_guard.py).

## Removed Claude-only tools

hook_guard.py (its rules survive in guard_rules.json), setup_project_settings.py, context_probe.py, usage_report.py,
usage_mix.py, doctor.py, setup_check.py, choice_reconcile.py, browser_check.py, poll_hint.py, selftest.py, container/.

Exit-code convention: 0 success, 1 problem / remind found, 2 cannot run (usage error or missing data, e.g. NO_DATA).
