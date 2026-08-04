#!/usr/bin/env bash
# dispatch.sh - Hand a task to an agent running in another tmux pane.
# Usage: dispatch.sh <pane_id> <task_or_file> [--loop] [--fix]
#   pane_id      %7 | 7 | session:window.pane
#   task_or_file literal task text, or a path starting with / or ./ to read it from
#   --loop       mark this as a review-fix loop, so the dispatcher's gate-review
#                may redispatch fixes automatically instead of stopping to ask
#   --fix        this is a fix instruction, not a first-time task; gate-evaluate on
#                the receiving side verifies each reported issue rather than judging
#                whether the task is reasonable

set -euo pipefail

TARGET_ARG="${1:?Usage: dispatch.sh <pane_id> <task_or_file> [--loop] [--fix]}"
TASK="${2:?Usage: dispatch.sh <pane_id> <task_or_file> [--loop] [--fix]}"
LOOP="false"
MODE="task"
for flag in "${@:3}"; do
  case "$flag" in
    --loop) LOOP="true" ;;
    --fix)  MODE="fix" ;;
    *) echo "Error: unknown flag '$flag' (expected --loop or --fix)" >&2; exit 1 ;;
  esac
done

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

if [[ "$TASK" == /* || "$TASK" == ./* ]]; then
  [[ -f "$TASK" ]] || { echo "Error: file '$TASK' not found" >&2; exit 1; }
  BODY="$(cat "$TASK")"
else
  BODY="$TASK"
fi

# The stamp is the whole point of dispatch rather than a plain send: it tells the
# receiving agent where the task came from, so it can report back on its own
# instead of leaving the dispatcher to poll. It also asks for loop to be echoed
# back, because gate-review on this side reads it off the incoming report to
# decide whether it may redispatch fixes on its own -- and the stamp is the only
# place that information survives the trip.
if [[ -n "$SENDER" ]]; then
  FOOTER="[dispatched from tmux pane ${SENDER}, mode: ${MODE}, loop: ${LOOP}. When you finish, get blocked, or need a decision, notify ${SENDER} using your tmux_reply skill, and carry loop: ${LOOP} back in that reply.]"
else
  FOOTER="[dispatched by an agent outside tmux -- no reply channel available.]"
fi

# Bracketed paste (-p) is what keeps a multi-line task intact: without it the
# receiving TUI reads every newline as a submit and the task arrives shredded
# into fragments, each one interpreted as a separate instruction.
BUF="tmux-dispatch-$$"
printf '%s\n\n%s\n' "$BODY" "$FOOTER" | tmux load-buffer -b "$BUF" -
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
echo "--- last lines of ${TARGET} ---"
tmux capture-pane -p -t "$TARGET" | awk 'NF' | tail -n 6
