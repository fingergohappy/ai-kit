#!/usr/bin/env bash
# generate_message.sh - Generate spec-implement message from template
# Usage:
#   generate_message.sh --mode doc  --doc-path <path> --tool-name <name> --desc <desc>
#   generate_message.sh --mode inline --tool-name <name> --desc <desc>
# Requires: $TMUX_PANE (auto-detected from tmux environment)
#
# Output: formatted message written to a temp file, path printed to stdout

set -euo pipefail

MODE=""
DOC_PATH=""
TOOL_NAME=""
DESC=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)      MODE="$2";      shift 2 ;;
    --doc-path)  DOC_PATH="$2";  shift 2 ;;
    --tool-name) TOOL_NAME="$2"; shift 2 ;;
    --desc)      DESC="$2";      shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

[[ -z "$MODE" ]]      && { echo "Error: --mode required (doc|inline)" >&2; exit 1; }
[[ -z "$TOOL_NAME" ]] && { echo "Error: --tool-name required" >&2; exit 1; }
[[ -z "$DESC" ]]      && { echo "Error: --desc required" >&2; exit 1; }

PANE_ID="${TMUX_PANE:?Error: not running inside tmux}"

OUTFILE=$(mktemp /tmp/spec-implement-msg.XXXXXX)

if [[ "$MODE" == "doc" ]]; then
  [[ -z "$DOC_PATH" ]] && { echo "Error: --doc-path required for doc mode" >&2; exit 1; }
  cat > "$OUTFILE" <<EOF
请按照以下设计文档实现：${DOC_PATH}

完成每个任务后，将文档中对应的"实现状态"从 [todo] 更新为 [done]。
如果某个任务跳过，更新为 [skip] 并注明原因。

---

执行完成后，调用 spec-feedback skill 向 pane ${PANE_ID} 反馈结果。

[task from ${TOOL_NAME}, pane_id: ${PANE_ID}: ${DESC}]
EOF
elif [[ "$MODE" == "inline" ]]; then
  cat > "$OUTFILE" <<EOF
---

执行完成后，调用 spec-feedback skill 向 pane ${PANE_ID} 反馈结果。

[task from ${TOOL_NAME}, pane_id: ${PANE_ID}: ${DESC}]
EOF
else
  echo "Error: --mode must be 'doc' or 'inline'" >&2
  exit 1
fi

echo "$OUTFILE"
