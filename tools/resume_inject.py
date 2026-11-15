"""Print the RESUME_STATE header and its open items, capped, for the agent to read first after a resume or a
compaction (dsh-DIRECTOR-WORKER 2.4.0-ds.6, from DIRECTOR-WORK 2.4.0 resume_inject.py).

  python -I -X utf8 resume_inject.py --file RESUME_STATE.md [--max-bytes 2048] [--section NAME ...]

DSH has no SessionStart hook, so nothing runs this for the agent: the agent runs it itself, once, as the first step
after DSH compacted the context or after any resume (the rule is in templates/AGENTS_PROJECT_SECTION.md and docs/06b),
then reads the rest of the file only when it needs it. It prints, as plain text:
  - one line saying where the text comes from,
  - the first four lines of FILE (the header docs/06 asks for: PROGRESS / DOING / NEXT_STEP / COMMS),
  - each open-items section: a markdown heading or a `KEY:` line whose name is one of --section (default OPEN ITEMS,
    OPEN_ITEMS, OPEN_DECISIONS, IN_FLIGHT, 未結, 未完成, 待辦), with the lines under it up to the next heading or KEY:
    line,
all cut at --max-bytes (default 2048, UTF-8 bytes; whole lines; a note says where it was cut and that the full file is
FILE). With no open-items section it says so in one line. A missing or unreadable FILE prints one line saying so
(exit 0); bad arguments exit 2.

What it costs: at most --max-bytes of context per resume (2048 by default). The instruction that asks for it is one
line of the AGENTS.md section, counted against DSH's 65536-byte instruction chain (CHANGELOG 2.4.0-ds.6 lists the
bytes). Standard library only.
"""
import argparse
import pathlib
import re
import sys

DEFAULT_SECTIONS = ("OPEN ITEMS", "OPEN_ITEMS", "OPEN_DECISIONS", "IN_FLIGHT", "未結", "未完成", "待辦")
HEADER_LINES = 4
KEY = re.compile(r"^([A-Z][A-Z0-9_ /-]*?)\s*:")
HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*#*\s*$")


def norm(name):
    return re.sub(r"[\s_]+", " ", name.strip()).upper()


def block_name(line):
    """The name of a block that starts on this line (a heading or a KEY: line), else None."""
    found = HEADING.match(line)
    if found:
        return found.group(1)
    found = KEY.match(line)
    return found.group(1) if found else None


def open_blocks(lines, names):
    """The blocks (lists of lines) whose name is in names, in file order; the header lines are not searched."""
    wanted = {norm(n) for n in names}
    out, current = [], None
    for line in lines[HEADER_LINES:]:
        name = block_name(line)
        if name is not None:
            current = [line] if norm(name) in wanted else None
            if current is not None:
                out.append(current)
        elif current is not None:
            current.append(line)
    return [[l for l in block if l.strip()] or block for block in out]


def capped(lines, limit):
    """Whole lines up to limit UTF-8 bytes (counting newlines) and whether some were cut."""
    out, size = [], 0
    for line in lines:
        cost = len(line.encode("utf-8")) + 1
        if size + cost > limit:
            return out, True
        out.append(line)
        size += cost
    return out, False


def render(text, name, limit, sections=DEFAULT_SECTIONS):
    """The text to inject (pure: the file's text in, the context text out)."""
    lines = text.splitlines()
    head = f"[resume_inject] header and open items of {name} (the rest is in that file; read it when needed):"
    body = lines[:HEADER_LINES]
    blocks = open_blocks(lines, sections)
    if blocks:
        body.append("")
        for block in blocks:
            body += block
    else:
        body.append(f"(no open-items section: none of {', '.join(sections)})")
    note = f"[resume_inject] cut at {limit} bytes; the rest is in the file named in the first line"
    kept, cut = capped([head] + body, limit - (len(note.encode("utf-8")) + 1))
    return "\n".join(kept + ([note] if cut else [])) + "\n"


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")  # before parse_args: --help prints during parsing
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", required=True, help="the RESUME_STATE.md to read")
    ap.add_argument("--max-bytes", type=int, default=2048, help="cap of the printed text in UTF-8 bytes, 256-10000 (default 2048)")
    ap.add_argument("--section", action="append", help="name of an open-items section (repeatable; default "
                    + ", ".join(DEFAULT_SECTIONS) + ")")
    try:
        a = ap.parse_args(argv)
    except SystemExit as stop:
        return 0 if stop.code in (0, None) else 2
    if not 256 <= a.max_bytes <= 10000:
        print(f"resume_inject: --max-bytes {a.max_bytes} outside 256-10000", file=sys.stderr)
        return 2
    path = pathlib.Path(a.file)
    try:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as error:
        print(f"[resume_inject] no RESUME_STATE read from {path} ({type(error).__name__}); find the work state by hand")
        return 0
    sys.stdout.flush()  # bytes, not text: no CR added on Windows, so the cap is exact
    sys.stdout.buffer.write(render(text, path.as_posix(), a.max_bytes, tuple(a.section or DEFAULT_SECTIONS)).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
