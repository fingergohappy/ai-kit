#!/usr/bin/env python3
"""crew-models.py - which crew tools exist, what each can run right now, and how to launch it.

A crew window is chosen as one "pick": <tool>[:<model>[:<effort>]]
    codex:gpt-6-astra:high      pi:xai/grok-4.6:xhigh      codex      (= tool's own default)

Usage:
    crew-models.py tools [--default]        registered tools: on PATH?, in the default lineup?, footer
                                            to check after launch; --default prints just the names of
                                            the default tools that are on PATH, one per line
    crew-models.py catalog [<tool>...]      menu: each tool's default and every model with its efforts
    crew-models.py check <pick>...          validate picks; exit 1 if any is unusable
    crew-models.py launch <pick>            print the command to exec in the tmux window
    crew-models.py assign <n> <pick>...     give n windows a pick each: drop unusable picks, rotate
                                            the rest; if none is usable fall back to the default tools
    (`-` in place of the picks reads them from stdin, one per line, `#` comments allowed.)

Tools are not listed here. Each is one adapter file, tools/<name>.py next to this script, or
~/.config/agent-crew/tools/<name>.py (same name overrides the built-in one). An adapter defines
    catalog() -> ({model: {"efforts": [...], "default_effort"?: str, "listed"?: bool}},
                  (default_model, default_effort), note)
    launch(model, effort) -> argv list          (model / effort may be "" = the tool's default)
    FOOTER, CONFIG                              strings shown by `tools`
    BIN                                         optional, the executable when it isn't <name>
An empty efforts list means the tool can't tell, and the effort is not validated.

Default tools (the lineup when nothing more specific is given) come from
~/.config/agent-crew/config.json: {"default_tools": ["codex", "pi", ...]}; without it, every tool.

Models change often, so no model is hard-coded anywhere: each adapter reads its tool's own files.
"""

import glob
import importlib.util
import json
import os
import shlex
import shutil
import sys

sys.dont_write_bytecode = True  # adapters are loaded from the skill directory; keep it clean

HERE = os.path.dirname(os.path.abspath(__file__))
USER_DIR = os.path.expanduser("~/.config/agent-crew")


def die(msg):
    print("crew-models: " + msg, file=sys.stderr)
    sys.exit(2)


# ---------- registry ----------

def load_tools():
    files = {}
    for d in (os.path.join(HERE, "tools"), os.path.join(USER_DIR, "tools")):
        for path in sorted(glob.glob(os.path.join(d, "*.py"))):
            name = os.path.basename(path)[:-3]
            if not name.startswith("_"):
                files[name] = path
    tools = {}
    for name, path in sorted(files.items()):
        spec = importlib.util.spec_from_file_location("crew_tool_" + name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        tools[name] = mod
    return tools


TOOLS = load_tools()


def default_tools():
    try:
        with open(os.path.join(USER_DIR, "config.json")) as f:
            names = json.load(f).get("default_tools") or []
    except (OSError, ValueError):
        names = []
    names = [n for n in names if n in TOOLS]
    return names or list(TOOLS)


def binary(tool):
    return getattr(TOOLS[tool], "BIN", tool)


def on_path(tool):
    return shutil.which(binary(tool)) is not None


_cache = {}


def catalog(tool):
    if tool not in _cache:
        _cache[tool] = TOOLS[tool].catalog()
    return _cache[tool]


# ---------- picks ----------

def parse(pick):
    pick = pick.strip()
    tool, _, rest = pick.partition(":")
    if tool not in TOOLS:
        return None
    if rest in ("", "default"):
        return tool, "", ""
    model, sep, effort = rest.rpartition(":")
    if not sep:  # tool:model, no effort
        return tool, effort, ""
    return tool, model, effort


def problem(pick):
    """None if usable, else why not."""
    p = parse(pick)
    if p is None:
        return "unknown tool (registered: %s)" % " / ".join(TOOLS)
    tool, model, effort = p
    if not on_path(tool):
        return "%s is not on PATH" % binary(tool)
    if not model:
        return None
    models = catalog(tool)[0]
    if model not in models:
        return "%s has no model %s right now" % (tool, model)
    efforts = models[model]["efforts"]
    if effort and efforts and effort not in efforts:
        return "%s supports efforts %s, not %s" % (model, ",".join(efforts), effort)
    return None


def launch(pick):
    tool, model, effort = parse(pick)
    return " ".join(shlex.quote(a) for a in TOOLS[tool].launch(model, effort))


def read_picks(args):
    if args == ["-"]:
        args = sys.stdin.read().splitlines()
    picks = []
    for a in args:
        a = a.split("#", 1)[0].strip()
        if a:
            picks.append(a)
    return picks


# ---------- commands ----------

def cmd_tools(args):
    defaults = default_tools()
    if args == ["--default"]:
        for tool in defaults:
            if on_path(tool):
                print(tool)
        return
    if args:
        die("tools: only --default is accepted")
    for tool, mod in TOOLS.items():
        flags = ["on PATH" if on_path(tool) else "NOT on PATH"]
        if tool in defaults:
            flags.append("default")
        print("## %s (%s)" % (tool, ", ".join(flags)))
        print("config: %s" % getattr(mod, "CONFIG", "?"))
        print("footer: %s" % getattr(mod, "FOOTER", "?"))
        print()


def cmd_catalog(args):
    for tool in args or list(TOOLS):
        if tool not in TOOLS:
            die("unknown tool %s (registered: %s)" % (tool, " / ".join(TOOLS)))
        if not on_path(tool):
            print("## %s: not on PATH\n" % tool)
            continue
        models, (dm, de), note = catalog(tool)
        print("## %s%s" % (tool, " (%s)" % note if note else ""))
        if not dm:
            # The tool's built-in default can't always be read from disk (codex's isn't its
            # top-priority model), so don't guess: a bare launch shows it in the window footer.
            print("default: %s  (none configured: the tool's built-in default, shown in the window footer)" % tool)
        elif not de:
            de = models.get(dm, {}).get("default_effort", "")
            print("default: %s:%s%s" % (tool, dm, ":%s  (the model's own default effort)" % de if de else ""))
        else:
            print("default: %s:%s:%s" % (tool, dm, de))
        for name in sorted(models):
            info = models[name]
            if not info.get("listed", True):
                continue
            mark = " (default)" if name == dm else ""
            print("  %-34s %s%s" % (name, ",".join(info["efforts"]) or "?", mark))
        print()


def cmd_check(args):
    picks = read_picks(args)
    if not picks:
        die("check: no picks given")
    bad = 0
    for pick in picks:
        why = problem(pick)
        if why:
            bad += 1
            print("bad  %s: %s" % (pick, why))
        else:
            print("ok   %s" % pick)
    sys.exit(1 if bad else 0)


def cmd_launch(args):
    if len(args) != 1:
        die("launch: exactly one pick")
    why = problem(args[0])
    if why:
        die("launch %s: %s" % (args[0], why))
    print(launch(args[0]))


def cmd_assign(args):
    if not args or not args[0].isdigit() or int(args[0]) < 1:
        die("assign: first argument is the number of windows")
    n = int(args[0])
    picks, seen = [], set()
    for pick in read_picks(args[1:]):
        if pick in seen:
            continue
        seen.add(pick)
        why = problem(pick)
        if why:
            print("# dropped %s: %s" % (pick, why))
        else:
            picks.append(pick)
    if not picks:
        picks = [t for t in default_tools() if on_path(t)]
        if not picks:
            die("assign: no usable pick and none of the default tools (%s) is on PATH" % ", ".join(default_tools()))
        print("# no usable pick in the lineup; falling back to tool defaults: %s" % ", ".join(picks))
    for i in range(n):
        print("%d %s" % (i + 1, picks[i % len(picks)]))


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        return
    cmd, args = sys.argv[1], sys.argv[2:]
    fn = {"tools": cmd_tools, "catalog": cmd_catalog, "check": cmd_check, "launch": cmd_launch,
          "assign": cmd_assign}.get(cmd)
    if not fn:
        die("unknown command " + cmd)
    fn(args)


if __name__ == "__main__":
    main()
