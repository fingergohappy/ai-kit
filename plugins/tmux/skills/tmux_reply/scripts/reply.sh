#!/usr/bin/env bash
# reply.sh - Report back to the tmux pane that dispatched a task to you.
# Usage: reply.sh <pane_id> <message_or_file> [--loop]
#   pane_id          %5 | 5 | session:window.pane  (the dispatcher's pane)
#   message_or_file  literal report text, or a path starting with / or ./ to read it from
#   --loop           pass this when the task you received was stamped loop: true,
#                    so the dispatcher's gate-review knows it may redispatch fixes

set -euo pipefail

TARGET_ARG="${1:?Usage: reply.sh <pane_id> <message_or_file> [--loop]}"
MSG="${2:?Usage: reply.sh <pane_id> <message_or_file> [--loop]}"
LOOP="false"
[[ "${3:-}" == "--loop" ]] && LOOP="true"

# A bare number is shorthand for a pane id; anything else (%5, dev:1.2) passes through.
if [[ "$TARGET_ARG" =~ ^[0-9]+$ ]]; then
  TARGET_ARG="%${TARGET_ARG}"
fi

# The dispatcher's pane may have been closed while we were working. Say so
# clearly rather than failing obscurely -- the work still happened, only the
# report has nowhere to land, and the user needs to hear that distinction.
die_no_pane() {
  echo "Error: pane '$TARGET_ARG' no longer exists -- the dispatcher may have closed it." >&2
  echo "Available panes:" >&2
  tmux list-panes -a -F '  #{pane_id}  #{pane_current_command}  #{pane_current_path}' >&2 || true
  exit 1
}

# Validate with list-panes, not display-message: for an unknown target the latter
# exits 0 and prints nothing, which would leave TARGET empty -- and an empty -t
# means "the active pane", so the report would be pasted into whatever pane the
# user is currently looking at. Fail closed instead.
tmux list-panes -t "$TARGET_ARG" >/dev/null 2>&1 || die_no_pane
TARGET=$(tmux display-message -p -t "$TARGET_ARG" '#{pane_id}' 2>/dev/null || true)
[[ -n "$TARGET" ]] || die_no_pane
tmux list-panes -a -F '#{pane_id}' | grep -qxF "$TARGET" || die_no_pane

SENDER="${TMUX_PANE:-}"
if [[ -n "$SENDER" && "$TARGET" == "$SENDER" ]]; then
  echo "Error: refusing to reply to the calling pane ($SENDER) -- check the dispatcher pane id." >&2
  exit 1
fi

if [[ "$MSG" == /* || "$MSG" == ./* ]]; then
  [[ -f "$MSG" ]] || { echo "Error: file '$MSG' not found" >&2; exit 1; }
  BODY="$(cat "$MSG")"
else
  BODY="$MSG"
fi

# Note what this footer does NOT say: it carries no instruction to reply. The
# dispatcher's pane treats any incoming message as a fresh turn, so an invitation
# to respond would set two agents acknowledging each other indefinitely.
if [[ -n "$SENDER" ]]; then
  FOOTER="[reply from tmux pane ${SENDER}, loop: ${LOOP}, re: the task you dispatched]"
else
  FOOTER="[reply from a dispatched agent, loop: ${LOOP}]"
fi

# Bracketed paste (-p) keeps a multi-line report intact; without it every newline
# reads as a submit and the report arrives as a series of stray fragments.
BUF="tmux-reply-$$"
printf '%s\n\n%s\n' "$BODY" "$FOOTER" | tmux load-buffer -b "$BUF" -
tmux paste-buffer -p -r -b "$BUF" -t "$TARGET"
tmux delete-buffer -b "$BUF" 2>/dev/null || true

# Enter has to be its own command: TUI agents read the paste and the submit as
# distinct events, and firing them together can drop the submit entirely.
sleep 0.5
tmux send-keys -t "$TARGET" Enter

sleep 1
echo "Replied to ${TARGET}."
echo "--- last lines of ${TARGET} ---"
tmux capture-pane -p -t "$TARGET" | awk 'NF' | tail -n 6
