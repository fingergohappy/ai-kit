#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
TARGET_DIR="${HOME}/.codex/agents"
MAP_CLAUDE_MODELS=1
FORCE=1

usage() {
  cat <<'EOF'
Usage:
  bash scripts/install_codex_agents.sh [--target DIR] [--no-model-map] [--no-force]

Description:
  Convert Claude-style plugin agents in this repository into Codex custom agent TOML
  files and install them into the target agent directory.

Options:
  --target DIR     Install to DIR instead of ~/.codex/agents
  --no-model-map   Do not map Claude model aliases like haiku/opus to OpenAI models
  --no-force       Do not overwrite existing TOML files
  -h, --help       Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET_DIR="$2"
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
