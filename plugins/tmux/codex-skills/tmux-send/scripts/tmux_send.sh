#!/usr/bin/env bash
# tmux_send.sh - Send content to a tmux pane via paste buffer, then press Enter
# Usage: tmux_send.sh <pane_id> <content_or_file>
#   pane_id: tmux pane ID (e.g. %7)
#   content_or_file: text content, or a file path starting with / or ./

set -euo pipefail

PANE_ID="${1:?Usage: tmux_send.sh <pane_id> <content_or_file>}"
CONTENT="${2:?Usage: tmux_send.sh <pane_id> <content_or_file>}"

# Verify pane exists
if ! tmux list-panes -t "$PANE_ID" >/dev/null 2>&1; then
  echo "Error: pane $PANE_ID not found" >&2
  exit 1
fi

# If content is a file path, read from file; otherwise use as-is
if [[ "$CONTENT" =~ ^/ ]] || [[ "$CONTENT" =~ ^\./ ]]; then
  if [[ ! -f "$CONTENT" ]]; then
    echo "Error: file $CONTENT not found" >&2
    exit 1
  fi
  tmux load-buffer "$CONTENT"
else
  tmux load-buffer - <<< "$CONTENT"
fi

# Paste content to pane (must be separate from send-keys)
tmux paste-buffer -p -r -t "$PANE_ID"

# Send Enter key as a separate command to ensure TUI tools can receive it
tmux send-keys -t "$PANE_ID" Enter
