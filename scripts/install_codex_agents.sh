#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${HOME}/.codex/agents"
SKILLS_TARGET_DIR="${HOME}/.agents/skills"
MAP_CLAUDE_MODELS=1
FORCE=1
INSTALL_SKILL_LINKS=0

usage() {
  cat <<'EOF'
Usage:
  bash scripts/install_codex_agents.sh [--target DIR] [--skills-target DIR] [--no-model-map] [--no-force] [--link-skills]

Description:
  Convert Claude-style plugin agents in this repository into Codex custom agent TOML
  files and install them into the target agent directory.

Options:
  --target DIR          Install agents to DIR instead of ~/.codex/agents
  --skills-target DIR   Install optional skill symlinks to DIR instead of ~/.agents/skills
  --no-model-map        Do not map Claude model aliases like haiku/opus to OpenAI models
  --no-force            Do not overwrite existing TOML files
  --link-skills         Also expose plugin skills as user skill symlinks
  --no-skill-links      Deprecated no-op; skill symlinks are disabled by default
  -h, --help            Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET_DIR="$2"
      shift 2
      ;;
    --skills-target)
      SKILLS_TARGET_DIR="$2"
      shift 2
      ;;
    --no-model-map)
      MAP_CLAUDE_MODELS=0
      shift
      ;;
    --no-force)
      FORCE=0
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

ARGS=(
  "--output" "${TARGET_DIR}"
)

if [[ "${MAP_CLAUDE_MODELS}" -eq 1 ]]; then
  ARGS+=("--map-claude-models")
fi

if [[ "${FORCE}" -eq 1 ]]; then
  ARGS+=("--force")
fi

python3 "${REPO_ROOT}/scripts/convert_claude_agents_to_codex.py" "${ARGS[@]}"

if [[ "${INSTALL_SKILL_LINKS}" -eq 1 ]]; then
  mkdir -p "${SKILLS_TARGET_DIR}"

  linked=0
  for skills_root in "${REPO_ROOT}"/plugins/*/skills; do
    if [[ ! -d "${skills_root}" ]]; then
      continue
    fi

    for skill_dir in "${skills_root}"/*; do
      if [[ ! -d "${skill_dir}" ]]; then
        continue
      fi

      skill_name="$(basename -- "${skill_dir}")"
      ln -sfn "${skill_dir}" "${SKILLS_TARGET_DIR}/${skill_name}"
      echo "linked:${SKILLS_TARGET_DIR}/${skill_name}"
      linked=$((linked + 1))
    done
  done

  echo "skills_linked:${linked}"
fi
