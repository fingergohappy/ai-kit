"""zcode: models from ~/.zcode/v2/provider_config.json (each provider's personalModelIds, named
<providerId>/<modelId>), efforts from the cached builtin model rules.

zcode has no launch flag for the model, and its in-session `/model` and `/effort` write straight back
to the global default in provider_config.json, so switching from inside the window would change every
later zcode run and race between windows. Instead each pick launches with its own copy of that file
(ZCODE_PERSONAL_PROVIDER_CONFIG_FILE) whose default selection is the pick. The copy holds the provider
credentials, so it lives in a 0700 directory, is written 0600, and is rewritten on every launch so a
rotated key never goes stale.
"""

import glob
import json
import os
import re

FOOTER = "`<model> <providerId> | <effort>` inside the prompt box; ready once it shows `Type a prompt`"
CONFIG = "~/.zcode/v2/provider_config.json"
PICK_DIR = "~/.cache/agent-crew/zcode"


def load_config():
    try:
        with open(os.path.expanduser(CONFIG)) as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def builtin_efforts():
    """Model id -> efforts, from the last (most specific) modelRules entry that matches it."""
    paths = glob.glob(os.path.expanduser("~/.zcode/v2/runtime/provider/*/*/*/zcode-builtin.json"))
    if not paths:
        return lambda model_id: []
    try:
        with open(max(paths, key=os.path.getmtime)) as f:
            rules = json.load(f)["config"]["modelConfigRules"]["modelRules"]
    except (OSError, ValueError, KeyError):
        return lambda model_id: []

    def efforts(model_id):
        found = []
        for r in rules:
            values = r.get("config", {}).get("optionSpecs", {}).get("reasoningLevel", {}).get("values")
            try:
                hit = values and re.fullmatch(r.get("modelMatch", ""), model_id, re.IGNORECASE)
            except re.error:
                hit = False
            if hit:
                found = values
        return list(found)

    return efforts


def catalog():
    cfg = load_config().get("config", {})
    efforts = builtin_efforts()
    models = {}
    for rule in cfg.get("providerConfigRules", {}).get("providerRules", []):
        for mid in rule.get("config", {}).get("personalModelIds", []):
            models["%s/%s" % (rule["providerId"], mid)] = {"efforts": efforts(mid)}
    sel = cfg.get("defaultModelSelection") or {}
    dm = "%s/%s" % (sel["providerId"], sel["modelId"]) if sel.get("modelId") else ""
    return models, (dm, sel.get("options", {}).get("reasoningLevel", "")), ""


def launch(model, effort):
    if not model:
        return ["zcode"]
    data = load_config()
    provider, _, mid = model.partition("/")
    sel = {"providerId": provider, "modelId": mid}
    if effort:
        sel["options"] = {"reasoningLevel": effort}
    data.setdefault("config", {})["defaultModelSelection"] = sel
    d = os.path.expanduser(PICK_DIR)
    os.makedirs(d, mode=0o700, exist_ok=True)
    path = os.path.join(d, re.sub(r"[^A-Za-z0-9._-]", "_", "%s_%s" % (model, effort or "default")) + ".json")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(data, f, indent=2)
    return ["env", "ZCODE_PERSONAL_PROVIDER_CONFIG_FILE=" + path, "zcode"]
