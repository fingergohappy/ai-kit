#!/usr/bin/env bash
# generate_message.sh - Generate spec-fix-review message from template
# Usage:
#   generate_message.sh --review-path <path> --tool-name <name> --desc <desc>
# Requires: $TMUX_PANE (auto-detected from tmux environment)
#
# Output: formatted message written to a temp file, path printed to stdout

set -euo pipefail

REVIEW_PATH=""
TOOL_NAME=""
DESC=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --review-path) REVIEW_PATH="$2"; shift 2 ;;
    --tool-name)   TOOL_NAME="$2";   shift 2 ;;
    --desc)        DESC="$2";        shift 2 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

[[ -z "$REVIEW_PATH" ]] && { echo "Error: --review-path required" >&2; exit 1; }
[[ -z "$TOOL_NAME" ]]   && { echo "Error: --tool-name required" >&2; exit 1; }
[[ -z "$DESC" ]]         && { echo "Error: --desc required" >&2; exit 1; }

PANE_ID="${TMUX_PANE:?Error: not running inside tmux}"

OUTFILE=$(mktemp /tmp/spec-fix-review-msg.XXXXXX)

cat > "$OUTFILE" <<EOF
使用 ai-kit:spec-check-review skill 查看以下 review 文档，并完成修复：

${REVIEW_PATH}

---

执行完成后，调用 ai-kit:spec-feedback skill 向 pane ${PANE_ID} 反馈结果。

[task from ${TOOL_NAME}: ${DESC}, pane_id: ${PANE_ID}]
EOF

echo "$OUTFILE"
