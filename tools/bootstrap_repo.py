#!/usr/bin/env python3
r"""BOOTSTRAP helper for the project repo (2.2.3-ds.3): the mechanical steps the lead used to do by hand.

  python -I -X utf8 <WS>/DIRECTOR/tools/bootstrap_repo.py --repo <REPO> --config <WS>/DIRECTOR/director_work.json
  python -I -X utf8 <WS>/DIRECTOR/tools/bootstrap_repo.py --repo <REPO> --config ... --check

Steps, each skipped when already done (so a rerun changes nothing):
  exclude   `.memsearch/` (the DSH memory search index, a tool product, not project source) is in
            <REPO>/.git/info/exclude; evidence_record.py wants a worktree without untracked files (WO-DS-004 DD-11)
  openspec  find the openspec CLI (sdd_gate.find_cli: OPENSPEC_BIN, sdd.openspec_bin, %LOCALAPPDATA%/dw-ds-tools/
            openspec-*/, PATH). Found and sdd.openspec_bin is null: write the found path into director_work.json
            (level 3 keeps the variable: %LOCALAPPDATA%/dw-ds-tools/...). Not found: print the PO_PENDING item to
            write (installing is a download, the PO decides, BOOTSTRAP 10.5); nothing is installed here.
  init      the CLI is found and <REPO>/openspec/ is missing: `openspec init --tools agents --language zh-TW
            --no-animation` in <REPO> (OPENSPEC_TELEMETRY=0). Then merge <RULES>/templates/openspec_config.yaml
            `rules:` into openspec/config.yaml yourself (the tool does not edit YAML).

--check only reports (exit 1 when a step still has work to do). Without it the steps run. Never commits; the repo
changes from init (openspec/, .agents/skills/) are committed by the project's own rules.
Prints one line per step and BOOTSTRAP_REPO: DONE|TODO|FAIL. Exit 0 done, 1 work left (--check) or a step failed,
2 usage error.
"""
import argparse
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
EXCLUDES = (".memsearch/",)
INIT_ARGS = ["init", "--tools", "agents", "--language", "zh-TW", "--no-animation"]


def sdd_gate():
    spec = importlib.util.spec_from_file_location("bootstrap_repo_sdd_gate", HERE / "sdd_gate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_dir(repo):
    """<repo>/.git as a folder (a worktree's .git file names its git dir), or None."""
    dot = repo / ".git"
    if dot.is_dir():
        return dot
    if dot.is_file():
        m = re.match(r"gitdir:\s*(.+)", dot.read_text(encoding="utf-8").strip())
        if m:
            path = pathlib.Path(m.group(1))
            return path if path.is_absolute() else (repo / path).resolve()
    return None


def step_exclude(repo, check):
    gd = git_dir(repo)
    if gd is None:
        return "FAIL", f"{repo} is not a git checkout (no .git); .memsearch/ not excluded"
    path = gd / "info" / "exclude"
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    have = {line.strip() for line in text.splitlines()}
    missing = [item for item in EXCLUDES if item not in have and item.rstrip("/") not in have]
    if not missing:
        return "OK", f"{path}: {', '.join(EXCLUDES)} already excluded"
    if check:
        return "TODO", f"{path}: add {', '.join(missing)}"
    path.parent.mkdir(parents=True, exist_ok=True)
    add = ("" if not text or text.endswith("\n") else "\n") + "# DW-DS bootstrap: tool products, local only\n" + \
        "".join(item + "\n" for item in missing)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(add)
    return "DONE", f"{path}: added {', '.join(missing)}"


def write_bin(config_path, value):
    """Set sdd.openspec_bin in the file, changing only that value when the file has `"openspec_bin": null` once."""
    text = config_path.read_text(encoding="utf-8-sig")
    pattern = re.compile(r'("openspec_bin"\s*:\s*)null')
    if len(pattern.findall(text)) == 1:
        new = pattern.sub(lambda m: m.group(1) + json.dumps(value, ensure_ascii=False), text)
    else:
        data = json.loads(text)
        sdd = data.setdefault("sdd", {})
        if not isinstance(sdd, dict):
            raise ValueError("sdd is not an object")
        sdd["openspec_bin"] = value
        new = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    json.loads(new)
    config_path.write_text(new, encoding="utf-8", newline="\n")


def step_openspec(sdd, config_path, check):
    config, problem = sdd.load_config(None, config_path)
    if problem:
        return "FAIL", problem, None
    command, how = sdd.find_cli(config)
    if command is None:
        return "TODO", (f"openspec CLI {how}. Write a PO_PENDING item 「安裝 openspec」 (@fission-ai/openspec@1.16.0, "
                        "MIT, free; npm install --prefix %LOCALAPPDATA%/dw-ds-tools/openspec-1.16.0, docs/13 「安裝」) "
                        "and keep tests-first; do not record it as impossible"), None
    version = sdd.cli_version(command)
    suggest = sdd.suggested_bin(command, how)
    if config.get("openspec_bin") or not suggest:
        return "OK", f"{' '.join(command)} ({how}) version={version}", command
    if config_path is None:
        return "TODO", f"found ({how}) version={version}; give --config to write sdd.openspec_bin={suggest}", command
    if check:
        return "TODO", f"found ({how}) version={version}; write sdd.openspec_bin = {suggest}", command
    try:
        write_bin(config_path, suggest)
    except (OSError, ValueError) as error:
        return "FAIL", f"cannot write {config_path}: {error}", command
    again, _ = sdd.load_config(None, config_path)
    command2, how2 = sdd.find_cli(again)
    if command2 is None:
        return "FAIL", f"wrote sdd.openspec_bin = {suggest} but it is not found again ({how2})", None
    return "DONE", f"wrote sdd.openspec_bin = {suggest} into {config_path}; now {how2} version={version}", command2


def step_init(sdd, repo, command, check):
    if (repo / "openspec").is_dir():
        return "OK", f"{repo / 'openspec'} exists"
    if command is None:
        return "TODO", "no openspec CLI yet; init after it is installed"
    if check:
        return "TODO", "run `openspec " + " ".join(INIT_ARGS) + f"` in {repo}"
    try:
        done = sdd.run_cli(command, INIT_ARGS, repo)
    except (OSError, subprocess.SubprocessError) as error:
        return "FAIL", f"openspec init could not run: {error}"
    if done.returncode != 0 or not (repo / "openspec").is_dir():
        return "FAIL", f"openspec init exit {done.returncode}: {(done.stdout + done.stderr).strip()[-300:]}"
    return "DONE", ("openspec init done (openspec/, .agents/skills/); merge templates/openspec_config.yaml rules: "
                    "into openspec/config.yaml, commit by the project's rules")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", required=True, help="the project checkout")
    ap.add_argument("--config", help="DIRECTOR/director_work.json (sdd.openspec_bin is written here)")
    ap.add_argument("--check", action="store_true", help="only report what is left to do")
    ap.add_argument("--skip", nargs="*", default=[], choices=("exclude", "openspec", "init"), help="steps to skip")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    repo = pathlib.Path(a.repo).resolve()
    if not repo.is_dir():
        print(f"BOOTSTRAP_REPO: FAIL repo not found: {repo}")
        return 2
    config_path = pathlib.Path(a.config).resolve() if a.config else None
    if config_path is not None and not config_path.is_file():
        print(f"BOOTSTRAP_REPO: FAIL config not found: {config_path}")
        return 2
    sdd = sdd_gate()
    results = []
    if "exclude" not in a.skip:
        results.append(("exclude",) + step_exclude(repo, a.check))
    command = None
    if "openspec" not in a.skip:
        status, detail, command = step_openspec(sdd, config_path, a.check)
        results.append(("openspec", status, detail))
    else:
        command = sdd.find_cli(sdd.load_config(None, config_path)[0])[0]
    if "init" not in a.skip:
        results.append(("init",) + step_init(sdd, repo, command, a.check))
    for name, status, detail in results:
        print(f"{status:5} {name}: {detail}")
    statuses = {status for _, status, _ in results}
    overall = "FAIL" if "FAIL" in statuses else "TODO" if "TODO" in statuses else "DONE"
    print(f"BOOTSTRAP_REPO: {overall}")
    return 0 if overall == "DONE" else 1


if __name__ == "__main__":
    sys.exit(main())
