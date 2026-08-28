#!/usr/bin/env bash
# dispatch.sh - Point an agent in another tmux pane at a task document.
# Usage: dispatch.sh <pane_id> <doc_path> [headline]
#   pane_id   %7 | 7 | session:window.pane
#   doc_path  the channel document holding the task, normally docs/tmux-channel/<name>.md
#   headline  optional one line shown in the other pane; the document carries the rest
#
# Only the document's absolute path travels through tmux. The brief itself stays
# on disk, where it survives the other agent's context compaction, can be re-read
# and diffed later, and cannot be shredded into fragments on the way over.

set -euo pipefail

TARGET_ARG="${1:?Usage: dispatch.sh <pane_id> <doc_path> [headline]}"
DOC_ARG="${2:?Usage: dispatch.sh <pane_id> <doc_path> [headline]}"
HEADLINE="${3:-}"

# A bare number is shorthand for a pane id; anything else (%7, dev:1.2) passes through.
if [[ "$TARGET_ARG" =~ ^[0-9]+$ ]]; then
  TARGET_ARG="%${TARGET_ARG}"
fi

die_no_pane() {
  echo "Error: pane '$TARGET_ARG' not found." >&2
  echo "Available panes:" >&2
  tmux list-panes -a -F '  #{pane_id}  #{pane_current_command}  #{pane_current_path}' >&2 || true
  exit 1
}

# Validate before resolving, and use list-panes to do it: for an unknown target
# `display-message` exits 0 and prints nothing, so trusting its status would leave
# TARGET empty -- and an empty -t means "the active pane", i.e. the task lands in
# whichever pane the user happens to be looking at. Fail closed instead.
tmux list-panes -t "$TARGET_ARG" >/dev/null 2>&1 || die_no_pane
TARGET=$(tmux display-message -p -t "$TARGET_ARG" '#{pane_id}' 2>/dev/null || true)
[[ -n "$TARGET" ]] || die_no_pane
tmux list-panes -a -F '#{pane_id}' | grep -qxF "$TARGET" || die_no_pane

SENDER="${TMUX_PANE:-}"
if [[ -n "$SENDER" && "$TARGET" == "$SENDER" ]]; then
  echo "Error: refusing to dispatch to the calling pane ($SENDER) -- that would feed the task back to yourself." >&2
  exit 1
fi

# The second argument is a path, never task text. Catching that here is what keeps
# the protocol honest: a pasted brief would look delivered and leave nothing behind.
if [[ ! -f "$DOC_ARG" ]]; then
  echo "Error: task document '$DOC_ARG' not found." >&2
  echo "dispatch sends a document path, not task text: write the brief to docs/tmux-channel/<name>.md first, then pass that path." >&2
  exit 1
fi
[[ -s "$DOC_ARG" ]] || { echo "Error: task document '$DOC_ARG' is empty -- write the task into it first." >&2; exit 1; }

# The receiving pane may sit in another directory, or another worktree of the same
# repo where this relative path resolves to a different file. Send an absolute one.
if command -v realpath >/dev/null 2>&1; then
  DOC="$(realpath "$DOC_ARG")"
else
  DOC="$(cd "$(dirname "$DOC_ARG")" && pwd -P)/$(basename "$DOC_ARG")"
fi

case "$DOC" in
  */docs/tmux-channel/*) ;;
  *) echo "Warning: '$DOC' is outside docs/tmux-channel/ -- the exchange will not be found where the other agent expects the channel to live." >&2 ;;
esac

# The headline is a label, not a smuggling route for the brief: collapse it to a
# single short line so the document stays the only place the task is written down.
if [[ -n "$HEADLINE" ]]; then
  HEADLINE="$(printf '%s' "$HEADLINE" | tr '\n\r\t' '   ')"
  if (( ${#HEADLINE} > 160 )); then
    HEADLINE="${HEADLINE:0:160}..."
  fi
fi

# The stamp is the whole point of dispatch rather than a plain send: it tells the
# receiving agent where the task came from and where to write the answer, so it can
# report back on its own instead of leaving the dispatcher to poll.
if [[ -n "$SENDER" ]]; then
  FOOTER="[dispatched from tmux pane ${SENDER}. That document is the task -- read it; this message is only the pointer. When you finish, get blocked, or need a decision, append a \"## Report\" section to the same document and notify ${SENDER} using your tmux-reply skill.]"
else
  FOOTER="[dispatched by an agent outside tmux -- read that document for the task; no reply channel available.]"
fi

# Bracketed paste (-p) is what keeps the multi-line pointer intact: without it the
# receiving TUI reads every newline as a submit and the message arrives shredded
# into fragments, each one interpreted as a separate instruction.
BUF="tmux-dispatch-$$"
{
  printf 'Task document: %s\n' "$DOC"
  if [[ -n "$HEADLINE" ]]; then printf '%s\n' "$HEADLINE"; fi
  printf '\n%s\n' "$FOOTER"
} | tmux load-buffer -b "$BUF" -
tmux paste-buffer -p -r -b "$BUF" -t "$TARGET"
# Delete our buffer so it does not sit on top of the user's own paste stack.
tmux delete-buffer -b "$BUF" 2>/dev/null || true

# Enter has to be its own command: TUI agents read the paste and the submit as
# distinct events, and firing them together can drop the submit entirely.
sleep 0.5
tmux send-keys -t "$TARGET" Enter

# Delivery receipt. We deliberately do not wait for the task to finish, but
# showing the pane right after submit catches silent failures -- copy mode,
# a confirmation prompt that ate the input, or simply the wrong pane.
sleep 1
echo "Dispatched to ${TARGET}${SENDER:+ (reply channel: $SENDER)}."
echo "Task document: ${DOC}"
echo "--- last lines of ${TARGET} ---"
tmux capture-pane -p -t "$TARGET" | awk 'NF' | tail -n 6
