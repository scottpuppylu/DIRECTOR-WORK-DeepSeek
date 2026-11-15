"""Warn when a tool output holds text that tries to give the agent orders (prompt injection), after the fact
(dsh-DIRECTOR-WORKER 2.4.0-ds.6, from DIRECTOR-WORK 2.4.0 inject_scan.py). It only reports; it never blocks, changes
or hides anything.

  python -I -X utf8 inject_scan.py scan FILE [FILE ...] [--json]
  python -I -X utf8 dsh_audit.py inject [filters] [--events FILE ...] [--json]   (the outputs in the DSH session logs)

DSH has no PostToolUse hook, so DW's live hook mode (a warning beside the tool result) is not ported: dshdw scans
afterwards, a file (scan) or the tool outputs the DSH session logs hold (dsh_audit.py inject, which calls scan_text()
on each output). Run it at a checkpoint, and before trusting what a web page, a downloaded file or another agent's
output told the agent to do.

Categories (line numbers are of the scanned text; the matched text itself is never printed, so a warning cannot
carry the injection on):
  override      "ignore / disregard / forget (all) previous instructions" and the like, also in Chinese
  role_rewrite  "you are now ...", "act as the system / developer", a line that starts with "system:" or a chat-format
                role tag, "developer mode", 「從現在起你是」
  hidden        zero-width characters (3 or more), Unicode tag characters, bidi override controls
  encoded       a base64 run of 200+ characters that decodes to readable text (an image or key decodes to bytes
                and is not reported)
  exfiltration  send / post / upload ... to a URL, or reveal / print the system prompt, API keys, tokens or passwords
scan: one line per finding `INJECT <category> line=N file=F`, then `INJECT_SCAN: FOUND n` (exit 1) or
`INJECT_SCAN: NONE` (exit 0); a missing file is exit 2. At most the first 2 MB of each file is scanned.

Known false positives (it is a warning for this reason): documents and tests about prompt injection (this file,
security write-ups, selftest samples), chat transcripts and logs that quote "system:" lines, code that sends data to
a URL on purpose (an upload script), and base64 that holds plain text by design (a data: URL of an SVG or a JSON
config). Misses: anything paraphrased, in other languages, split over lines or encoded another way. This is a seat
belt, not a security boundary: the instruction-source rule (orders come only from the user) still decides.
Concepts borrowed (no code): the warn-only approach and its category list from an MIT-licensed hook project
(CHANGELOG 2.4.0-ds.6 Credits, as DW 2.4.0). Standard library only.
"""
import argparse
import base64
import binascii
import json
import pathlib
import re
import sys

SCAN_LIMIT = 2 * 1024 * 1024
PATTERNS = {
    "override": [
        r"\b(?:ignore|disregard|forget|override|skip)\b[^.\n]{0,30}\b(?:previous|prior|above|earlier|preceding|all|any|your)\b"
        r"[^.\n]{0,20}\b(?:instructions?|prompts?|rules|directions|guidelines|messages)\b",
        r"(?:忽略|無視|忘記|忘掉|不要理會)[^。\n]{0,12}(?:之前|先前|以上|前面|上面|所有)[^。\n]{0,8}(?:指示|指令|規則|提示)",
        r"\bnew (?:system )?instructions?\s*:",
    ],
    "role_rewrite": [
        r"\byou are now (?:a|an|the|my)\b",
        r"\b(?:act|behave|respond) as (?:the |an? )?(?:system|developer|administrator|admin|root)\b",
        r"(?m)^\s*(?:system|developer)\s*:\s*\S",
        r"<\|?im_start\|?>\s*system|\[/?(?:SYSTEM|INST)\]|<<SYS>>",
        r"\b(?:developer|god|jailbreak|DAN) mode\b",
        r"(?:從現在起|从现在起)[^。\n]{0,6}你(?:是|就是|扮演)",
    ],
    "exfiltration": [
        r"\b(?:send|post|upload|forward|exfiltrate|transmit|email|submit)\b[^.\n]{0,60}\b(?:to|at|into)\s+https?://",
        r"\b(?:reveal|print|show|output|leak|repeat|dump|tell me)\b[^.\n]{0,30}\b(?:system prompt|api[ _-]?keys?|secret keys?|"
        r"access tokens?|tokens|passwords?|credentials|private keys?|\.env)\b",
        r"(?:把|將)[^。\n]{0,20}(?:金鑰|密碼|token|權杖|憑證)[^。\n]{0,12}(?:傳|送|貼|寄)到",
    ],
}
COMPILED = {k: [re.compile(p, re.I) for p in v] for k, v in PATTERNS.items()}
ZERO_WIDTH = re.compile("[​‌‍⁠⁡⁢⁣⁤﻿]")
TAGS = re.compile("[\U000e0000-\U000e007f]")
BIDI = re.compile("[‪-‮⁦-⁩]")
BASE64 = re.compile(r"[A-Za-z0-9+/]{200,}={0,2}")
CATEGORIES = ("override", "role_rewrite", "hidden", "encoded", "exfiltration")


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def readable(raw):
    """True when bytes decode to mostly printable text with words (planted instructions), not an image or a key."""
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return False
    printable = sum(ch.isprintable() or ch in "\n\t" for ch in text)
    return bool(text) and printable / len(text) > 0.95 and text.count(" ") >= len(text) / 20


def scan_text(text):
    """Findings in text (pure): [(category, line)], at most one per category and line, in text order."""
    text = text[:SCAN_LIMIT]
    found = set()
    for category, patterns in COMPILED.items():
        for pattern in patterns:
            for m in pattern.finditer(text):
                found.add((category, line_of(text, m.start())))
    marks = list(ZERO_WIDTH.finditer(text))
    if len(marks) >= 3:
        found.add(("hidden", line_of(text, marks[0].start())))
    for pattern in (TAGS, BIDI):
        m = pattern.search(text)
        if m:
            found.add(("hidden", line_of(text, m.start())))
    for m in BASE64.finditer(text):
        run = m.group(0)
        try:
            raw = base64.b64decode(run[: len(run) - len(run) % 4] or run, validate=False)
        except (binascii.Error, ValueError):
            continue
        if readable(raw):
            found.add(("encoded", line_of(text, m.start())))
    return sorted(found, key=lambda f: (f[1], CATEGORIES.index(f[0])))


def text_of(value, out=None, budget=None):
    """All strings in a tool response (str, or nested dict / list), joined by newlines, at most SCAN_LIMIT chars."""
    out = [] if out is None else out
    budget = [SCAN_LIMIT] if budget is None else budget
    if budget[0] <= 0:
        return out
    if isinstance(value, str):
        out.append(value[: budget[0]])
        budget[0] -= len(value)
    elif isinstance(value, dict):
        for item in value.values():
            text_of(item, out, budget)
    elif isinstance(value, list):
        for item in value:
            text_of(item, out, budget)
    return out


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")  # before parse_args: --help prints during parsing
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scan", help="scan files after the fact (DSH has no PostToolUse hook)")
    s.add_argument("files", nargs="+")
    s.add_argument("--json", action="store_true")
    try:
        a = ap.parse_args(argv)
    except SystemExit as stop:
        return 0 if stop.code in (0, None) else 2
    results = []
    for name in a.files:
        try:
            text = pathlib.Path(name).read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            print(f"INJECT_SCAN: INPUT_ERROR {name}: {type(error).__name__}")
            return 2
        results += [(name, c, n) for c, n in scan_text(text)]
    if a.json:
        print(json.dumps([{"file": f, "category": c, "line": n} for f, c, n in results], ensure_ascii=False))
    else:
        for f, c, n in results:
            print(f"INJECT {c} line={n} file={f}")
        print(f"INJECT_SCAN: FOUND {len(results)}" if results else "INJECT_SCAN: NONE")
    return 1 if results else 0


if __name__ == "__main__":
    sys.exit(main())
