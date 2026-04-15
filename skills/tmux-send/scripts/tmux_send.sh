#!/usr/bin/env bash
# Send content to a tmux pane via paste buffer, then press Enter.
# Usage: tmux_send.sh <pane_id> <content>
#   pane_id: tmux pane ID (e.g. "%7")
#   content: text to send

set -euo pipefail

PANE_ID="${1:?Usage: tmux_send.sh <pane_id> <content>}"
shift
CONTENT="$*"

if [ -z "$CONTENT" ]; then
  echo "Error: no content to send" >&2
  exit 1
fi

# Verify the pane exists
if ! tmux list-panes -t "$PANE_ID" &>/dev/null; then
  echo "Error: tmux pane '$PANE_ID' not found" >&2
  exit 1
fi

# Paste content via buffer (handles multi-line without triggering execution)
tmux load-buffer - <<< "$CONTENT"
tmux paste-buffer -t "$PANE_ID"

# Press Enter to execute
tmux send-keys -t "$PANE_ID" Enter
echo "Sent to $PANE_ID: $CONTENT"
