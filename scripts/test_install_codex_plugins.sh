#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
TMP_HOME="$(mktemp -d)"
SKILL_HOME="$(mktemp -d)"

cleanup() {
  rm -rf "${TMP_HOME}"
  rm -rf "${SKILL_HOME}"
}
trap cleanup EXIT

HOME="${TMP_HOME}" bash "${REPO_ROOT}/scripts/install_codex_plugins.sh"

python3 - "${REPO_ROOT}" "${TMP_HOME}" <<'PY'
from pathlib import Path
import json
import sys

repo_root = Path(sys.argv[1])
home = Path(sys.argv[2])

manifests = sorted((repo_root / "plugins").glob("*/.codex-plugin/plugin.json"))
expected_plugins = sorted(
    json.loads(path.read_text()).get("name") or path.parent.parent.name
    for path in manifests
)

marketplace_path = home / ".agents" / "plugins" / "marketplace.json"
payload = json.loads(marketplace_path.read_text())
marketplace_plugins = sorted(item["name"] for item in payload["plugins"])

local_plugins = sorted(
    path.parent.parent.name
    for path in (home / ".codex" / "plugins").glob("*/.codex-plugin/plugin.json")
)

expected_agents = sorted(path.stem for path in (repo_root / "plugins").glob("*/agents/*.md"))
installed_agents = sorted(path.stem for path in (home / ".codex" / "agents").glob("*.toml"))

assert expected_plugins, "repo should contain Codex plugin manifests"
assert marketplace_plugins == expected_plugins, (marketplace_plugins, expected_plugins)
assert local_plugins == expected_plugins, (local_plugins, expected_plugins)
assert not (home / ".agents" / "skills").exists(), "default install should not link user skills"
assert installed_agents == expected_agents, (installed_agents, expected_agents)
PY

HOME="${SKILL_HOME}" bash "${REPO_ROOT}/scripts/install_codex_plugins.sh" --link-skills

python3 - "${REPO_ROOT}" "${SKILL_HOME}" <<'PY'
from pathlib import Path
import sys

repo_root = Path(sys.argv[1])
home = Path(sys.argv[2])

expected_skills = sorted(
    path.name
    for path in (repo_root / "plugins").glob("*/skills/*")
    if path.is_dir()
)
linked_skills = sorted(path.name for path in (home / ".agents" / "skills").iterdir())

assert linked_skills == expected_skills, (linked_skills, expected_skills)
PY
