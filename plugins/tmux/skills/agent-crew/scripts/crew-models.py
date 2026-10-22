#!/usr/bin/env python3
"""crew-models.py - what each crew tool can run right now, and how to launch it.

A crew window is chosen as one "pick": <tool>[:<model>[:<effort>]]
    codex:gpt-6-astra:high      pi:xai/grok-4.6:xhigh      codex      (= tool's own default)

Usage:
    crew-models.py catalog [codex|pi]       menu: each tool's default and every model with its efforts
    crew-models.py check <pick>...          validate picks; exit 1 if any is unusable
    crew-models.py launch <pick>            print the command to exec in the tmux window
    crew-models.py assign <n> <pick>...     give n windows a pick each: drop unusable picks, rotate
                                            the rest; if none is usable fall back to tool defaults
    (`-` in place of the picks reads them from stdin, one per line, `#` comments allowed.)

Models change often, so nothing here is hard-coded: codex is read from ~/.codex/models_cache.json
and ~/.codex/config.toml, pi from `pi --list-models`, `pi --help` and ~/.pi/agent/settings.json.
"""

import json
import os
import re
import shutil
import subprocess
import sys

HOME = os.path.expanduser("~")
TOOLS = ("codex", "pi")


def die(msg):
    print("crew-models: " + msg, file=sys.stderr)
    sys.exit(2)


def run(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as e:
        return "", str(e)
    return out.stdout, out.stderr


# ---------- catalogs ----------

def codex_catalog():
    """{model: {"efforts": [...], "default_effort": str, "listed": bool}}, default (model, effort)."""
    models = {}
    path = os.path.join(HOME, ".codex", "models_cache.json")
    try:
        with open(path) as f:
            data = json.load(f)
    except (OSError, ValueError):
        data = {}
    for m in data.get("models", []):
        models[m["slug"]] = {
            "efforts": [lv["effort"] for lv in m.get("supported_reasoning_levels", [])],
            "default_effort": m.get("default_reasoning_level", ""),
            "listed": m.get("visibility") != "hide",
        }
    cfg = {}
    try:
        with open(os.path.join(HOME, ".codex", "config.toml")) as f:
            for line in f:
                if line.startswith("["):
                    break  # only top-level keys
                mt = re.match(r'\s*(model|model_reasoning_effort)\s*=\s*"([^"]*)"', line)
                if mt:
                    cfg[mt.group(1)] = mt.group(2)
    except OSError:
        pass
    return models, (cfg.get("model", ""), cfg.get("model_reasoning_effort", "")), data.get("fetched_at", "")


def pi_catalog():
    """{provider/model: {"efforts": [...]}}, default (model, effort)."""
    help_out, _ = run(["pi", "--help"])
    mt = re.search(r"--thinking <level>.*?:\s*([a-z, ]+)", help_out)
    levels = [s.strip() for s in mt.group(1).split(",")] if mt else []
    out, _ = run(["pi", "--list-models"])
    models = {}
    for line in out.splitlines():
        cols = line.split()
        if len(cols) < 6 or cols[0] == "provider" or line.startswith("["):
            continue
        thinking = cols[4] == "yes"
        models[cols[0] + "/" + cols[1]] = {"efforts": levels if thinking else ["off"]}
    st = {}
    try:
        with open(os.path.join(HOME, ".pi", "agent", "settings.json")) as f:
            st = json.load(f)
    except (OSError, ValueError):
        pass
    dm = "%s/%s" % (st.get("defaultProvider", ""), st.get("defaultModel", "")) if st.get("defaultModel") else ""
    return models, (dm, st.get("defaultThinkingLevel", ""))


_cache = {}


def catalog(tool):
    if tool not in _cache:
        if tool == "codex":
            m, d, _ = codex_catalog()
        else:
            m, d = pi_catalog()
        _cache[tool] = (m, d)
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
        return "unknown tool (expected %s)" % " / ".join(TOOLS)
    tool, model, effort = p
    if not shutil.which(tool):
        return "%s is not on PATH" % tool
    if not model:
        return None
    models, _ = catalog(tool)
    if model not in models:
        return "%s has no model %s right now" % (tool, model)
    if effort and effort not in models[model]["efforts"]:
        return "%s supports efforts %s, not %s" % (model, ",".join(models[model]["efforts"]), effort)
    return None


def launch(pick):
    tool, model, effort = parse(pick)
    cmd = [tool]
    if tool == "codex":
        if model:
            cmd += ["-m", model]
        if effort:
            cmd += ["-c", "model_reasoning_effort=" + effort]
    else:
        if model:
            cmd += ["--model", model]
        if effort:
            cmd += ["--thinking", effort]
    return " ".join(cmd)


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

def cmd_catalog(args):
    tools = args or list(TOOLS)
    for tool in tools:
        if tool not in TOOLS:
            die("unknown tool " + tool)
        if not shutil.which(tool):
            print("## %s: not on PATH\n" % tool)
            continue
        models, (dm, de) = catalog(tool)
        note = ""
        if tool == "codex":
            note = " (cache fetched %s)" % codex_catalog()[2]
        print("## %s%s" % (tool, note))
        if not dm:
            # The tool's built-in default can't be read from disk (codex's isn't its top-priority
            # model), so don't guess: a bare launch shows it in the window footer.
            print("default: %s  (none configured: the tool's built-in default, shown in the window footer)" % tool)
        elif not de:
            de = models.get(dm, {}).get("default_effort", "")
            print("default: %s:%s%s" % (tool, dm, ":%s  (the model's own default effort)" % de if de else ""))
        else:
            print("default: %s:%s:%s" % (tool, dm, de))
        for name in sorted(models):
            info = models[name]
            if tool == "codex" and not info["listed"]:
                continue
            mark = " (default)" if name == dm else ""
            print("  %-34s %s%s" % (name, ",".join(info["efforts"]), mark))
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
        picks = [t for t in TOOLS if shutil.which(t)]
        if not picks:
            die("assign: no usable pick and neither codex nor pi is on PATH")
        print("# no usable pick in the lineup; falling back to tool defaults: %s" % ", ".join(picks))
    for i in range(n):
        print("%d %s" % (i + 1, picks[i % len(picks)]))


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__.strip())
        return
    cmd, args = sys.argv[1], sys.argv[2:]
    fn = {"catalog": cmd_catalog, "check": cmd_check, "launch": cmd_launch, "assign": cmd_assign}.get(cmd)
    if not fn:
        die("unknown command " + cmd)
    fn(args)


if __name__ == "__main__":
    main()
