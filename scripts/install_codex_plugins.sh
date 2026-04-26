#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
PLUGINS_TARGET_DIR="${HOME}/.codex/plugins"
MARKETPLACE_PATH="${HOME}/.agents/plugins/marketplace.json"
AGENTS_TARGET_DIR="${HOME}/.codex/agents"
SKILLS_TARGET_DIR="${HOME}/.agents/skills"
INSTALL_AGENTS=1
INSTALL_SKILL_LINKS=0

usage() {
  cat <<'EOF'
Usage:
  bash scripts/install_codex_plugins.sh [options]

Description:
  Install this repository's Codex plugins into the user's personal Codex
  plugin directory, merge the personal marketplace entry, and install bundled
  Codex custom agents.

Options:
  --plugins-target DIR    Install plugin directories to DIR instead of ~/.codex/plugins
  --marketplace PATH      Write marketplace metadata to PATH instead of ~/.agents/plugins/marketplace.json
  --agents-target DIR     Install custom agents to DIR instead of ~/.codex/agents
  --skills-target DIR     Install optional skill symlinks to DIR instead of ~/.agents/skills
  --no-agents             Skip installing Codex custom agents
  --link-skills           Also expose plugin skills as user skill symlinks
  --no-skill-links        Deprecated no-op; skill symlinks are disabled by default
  -h, --help              Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --plugins-target)
      PLUGINS_TARGET_DIR="$2"
      shift 2
      ;;
    --marketplace)
      MARKETPLACE_PATH="$2"
      shift 2
      ;;
    --agents-target)
      AGENTS_TARGET_DIR="$2"
      shift 2
      ;;
    --skills-target)
      SKILLS_TARGET_DIR="$2"
      shift 2
      ;;
    --no-agents)
      INSTALL_AGENTS=0
      shift
      ;;
    --link-skills)
      INSTALL_SKILL_LINKS=1
      shift
      ;;
    --no-skill-links)
      INSTALL_SKILL_LINKS=0
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

python3 - "${REPO_ROOT}" "${PLUGINS_TARGET_DIR}" "${MARKETPLACE_PATH}" <<'PY'
from pathlib import Path
import json
import os
import shutil
import sys

repo_root = Path(sys.argv[1]).expanduser().resolve()
plugins_target = Path(sys.argv[2]).expanduser().resolve()
marketplace_path = Path(sys.argv[3]).expanduser().resolve()
home = Path(os.environ["HOME"]).expanduser().resolve()
repo_plugins = repo_root / "plugins"

manifests = sorted(repo_plugins.glob("*/.codex-plugin/plugin.json"))
if not manifests:
    raise SystemExit("no Codex plugin manifests found under " + str(repo_plugins))

try:
    plugins_relative = plugins_target.relative_to(home)
except ValueError:
    raise SystemExit("plugins target must be inside HOME: " + str(plugins_target))

plugins_target.mkdir(parents=True, exist_ok=True)
marketplace_path.parent.mkdir(parents=True, exist_ok=True)

plugins = []
for manifest_path in manifests:
    with manifest_path.open() as f:
        manifest = json.load(f)

    plugin_dir = manifest_path.parent.parent
    name = manifest.get("name") or plugin_dir.name
    interface = manifest.get("interface", {})
    target_dir = plugins_target / name

    if target_dir.exists() or target_dir.is_symlink():
        if target_dir.is_dir() and not target_dir.is_symlink():
            shutil.rmtree(target_dir)
        else:
            target_dir.unlink()

    shutil.copytree(plugin_dir, target_dir, symlinks=True)
    plugins.append(
        {
            "name": name,
            "category": interface.get("category", "Productivity"),
        }
    )

payload = {
    "name": "ai-kit",
    "interface": {
        "displayName": "ai-kit",
    },
    "plugins": [],
}

if marketplace_path.exists():
    with marketplace_path.open() as f:
        payload = json.load(f)

payload.setdefault("name", "ai-kit")
payload.setdefault("interface", {})
payload["interface"].setdefault("displayName", "ai-kit")
payload.setdefault("plugins", [])

entries = [
    {
        "name": plugin["name"],
        "source": {
            "source": "local",
            "path": "./" + (plugins_relative / plugin["name"]).as_posix(),
        },
        "policy": {
            "installation": "AVAILABLE",
            "authentication": "ON_INSTALL",
        },
        "category": plugin["category"],
    }
    for plugin in plugins
]

managed = {plugin["name"] for plugin in plugins}
payload["plugins"] = [
    item
    for item in payload["plugins"]
    if not (isinstance(item, dict) and item.get("name") in managed)
]
payload["plugins"].extend(entries)

with marketplace_path.open("w") as f:
    json.dump(payload, f, indent=2)
    f.write("\n")

print("plugins_installed:" + ",".join(sorted(managed)))
print("marketplace:" + str(marketplace_path))
PY

if [[ "${INSTALL_AGENTS}" -eq 1 ]]; then
  ARGS=(
    "--target" "${AGENTS_TARGET_DIR}"
    "--skills-target" "${SKILLS_TARGET_DIR}"
    "--no-skill-links"
  )

  if [[ "${INSTALL_SKILL_LINKS}" -eq 1 ]]; then
    ARGS=(
      "--target" "${AGENTS_TARGET_DIR}"
      "--skills-target" "${SKILLS_TARGET_DIR}"
      "--link-skills"
    )
  fi

  bash "${REPO_ROOT}/scripts/install_codex_agents.sh" "${ARGS[@]}"
fi

cat <<'EOF'

Next steps:
1. Restart Codex.
2. Open /plugins and install or enable the ai-kit plugins shown there.
3. Run list skills or /skills after installing plugins.
EOF
