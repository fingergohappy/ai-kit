"""codex: models from ~/.codex/models_cache.json, default from ~/.codex/config.toml; model and effort
are launch flags."""

import json
import os
import re

FOOTER = "`<Model> <effort> · ... weekly N% left` (`weekly 0% left` = out of quota)"
CONFIG = "~/.codex/config.toml"


def catalog():
    models = {}
    try:
        with open(os.path.expanduser("~/.codex/models_cache.json")) as f:
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
        with open(os.path.expanduser(CONFIG)) as f:
            for line in f:
                if line.startswith("["):
                    break  # only top-level keys
                mt = re.match(r'\s*(model|model_reasoning_effort)\s*=\s*"([^"]*)"', line)
                if mt:
                    cfg[mt.group(1)] = mt.group(2)
    except OSError:
        pass
    note = "cache fetched %s" % data.get("fetched_at", "?")
    return models, (cfg.get("model", ""), cfg.get("model_reasoning_effort", "")), note


def launch(model, effort):
    cmd = ["codex"]
    if model:
        cmd += ["-m", model]
    if effort:
        cmd += ["-c", "model_reasoning_effort=" + effort]
    return cmd
