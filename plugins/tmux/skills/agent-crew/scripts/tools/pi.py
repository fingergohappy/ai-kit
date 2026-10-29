"""pi: models from `pi --list-models`, efforts from `pi --help`, default from
~/.pi/agent/settings.json; model and effort are launch flags."""

import json
import os
import re
import subprocess

FOOTER = "`(<provider>) <model> • <effort>`"
CONFIG = "~/.pi/agent/settings.json"


def run(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def catalog():
    mt = re.search(r"--thinking <level>.*?:\s*([a-z, ]+)", run(["pi", "--help"]))
    levels = [s.strip() for s in mt.group(1).split(",")] if mt else []
    models = {}
    for line in run(["pi", "--list-models"]).splitlines():
        cols = line.split()
        if len(cols) < 6 or cols[0] == "provider" or line.startswith("["):
            continue
        thinking = cols[4] == "yes"
        models[cols[0] + "/" + cols[1]] = {"efforts": levels if thinking else ["off"]}
    st = {}
    try:
        with open(os.path.expanduser(CONFIG)) as f:
            st = json.load(f)
    except (OSError, ValueError):
        pass
    dm = "%s/%s" % (st.get("defaultProvider", ""), st.get("defaultModel", "")) if st.get("defaultModel") else ""
    return models, (dm, st.get("defaultThinkingLevel", "")), ""


def launch(model, effort):
    cmd = ["pi"]
    if model:
        cmd += ["--model", model]
    if effort:
        cmd += ["--thinking", effort]
    return cmd
