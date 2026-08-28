#!/usr/bin/env bash
# reply.sh - Tell the dispatching pane that your report is in the channel document.
# Usage: reply.sh <pane_id> <doc_path> [verdict]
#   pane_id   %5 | 5 | session:window.pane  (the dispatcher's pane)
#   doc_path  the same channel document the task arrived in, with your report appended
#   verdict   optional one line, e.g. "DONE: ..."; the document carries the evidence
#
# The report itself never travels through tmux -- it is appended to the document
# both agents already share, so the dispatcher can re-read it, quote it, and check
# the deliverable against the original brief sitting right above it.

set -euo pipefail

TARGET_ARG="${1:?Usage: reply.sh <pane_id> <doc_path> [verdict]}"
DOC_ARG="${2:?Usage: reply.sh <pane_id> <doc_path> [verdict]}"
VERDICT="${3:-}"

# A bare number is shorthand for a pane id; anything else (%5, dev:1.2) passes through.
if [[ "$TARGET_ARG" =~ ^[0-9]+$ ]]; then
  TARGET_ARG="%${TARGET_ARG}"
fi

# The dispatcher's pane may have been closed while we were working. Say so
# clearly rather than failing obscurely -- the work still happened and the report
# is safe in the document, only the knock has nowhere to land.
die_no_pane() {
  echo "Error: pane '$TARGET_ARG' no longer exists -- the dispatcher may have closed it." >&2
  echo "Your report is still in the channel document; tell your own user where it is." >&2
  echo "Available panes:" >&2
  tmux list-panes -a -F '  #{pane_id}  #{pane_current_command}  #{pane_current_path}' >&2 || true
  exit 1
}

# Validate with list-panes, not display-message: for an unknown target the latter
# exits 0 and prints nothing, which would leave TARGET empty -- and an empty -t
# means "the active pane", so the message would be pasted into whatever pane the
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

if [[ ! -f "$DOC_ARG" ]]; then
  echo "Error: channel document '$DOC_ARG' not found." >&2
  echo "reply sends a document path, not report text: append your report to the document the task arrived in, then pass that path." >&2
  exit 1
fi

if command -v realpath >/dev/null 2>&1; then
  DOC="$(realpath "$DOC_ARG")"
else
  DOC="$(cd "$(dirname "$DOC_ARG")" && pwd -P)/$(basename "$DOC_ARG")"
fi

# The failure this catches is the expensive one: knocking on the dispatcher's door
# with nothing written down. If the last section of the document is still the task
# (or a follow-up), the report was never appended -- or was appended above an older
# round, where the dispatcher will not look for it.
LAST_HEADING="$(grep -E '^##[[:space:]]+' "$DOC" | tail -n 1 || true)"
if ! printf '%s' "$LAST_HEADING" | grep -qiE '^##[[:space:]]+(report|回报)'; then
  echo "Error: the last section of '$DOC' is not a report section${LAST_HEADING:+ (found: $LAST_HEADING)}." >&2
  echo "Append your report to the end of that document as '## Report — <your pane> → <dispatcher pane> — <timestamp>', then reply." >&2
  exit 1
fi

# The verdict is a label, not the report: one short line so the dispatcher can
# triage at a glance and read the substance in the document.
if [[ -n "$VERDICT" ]]; then
  VERDICT="$(printf '%s' "$VERDICT" | tr '\n\r\t' '   ')"
  if (( ${#VERDICT} > 160 )); then
    VERDICT="${VERDICT:0:160}..."
  fi
  case "$VERDICT" in
    DONE:*|BLOCKED:*|QUESTION:*) ;;
    *) echo "Warning: verdict does not start with DONE: / BLOCKED: / QUESTION: -- the dispatcher's next move differs for each." >&2 ;;
  esac
fi

# Note what this footer does NOT say: it carries no instruction to reply. The
# dispatcher's pane treats any incoming message as a fresh turn, so an invitation
# to respond would set two agents acknowledging each other indefinitely.
if [[ -n "$SENDER" ]]; then
  FOOTER="[reply from tmux pane ${SENDER}, re: the task you dispatched. The report is the last \"## Report\" section of that document.]"
else
  FOOTER="[reply from a dispatched agent. The report is the last \"## Report\" section of that document.]"
fi

# Bracketed paste (-p) keeps the multi-line pointer intact; without it every newline
# reads as a submit and the message arrives as a series of stray fragments.
BUF="tmux-reply-$$"
{
  printf 'Report in: %s\n' "$DOC"
  if [[ -n "$VERDICT" ]]; then printf '%s\n' "$VERDICT"; fi
  printf '\n%s\n' "$FOOTER"
} | tmux load-buffer -b "$BUF" -
tmux paste-buffer -p -r -b "$BUF" -t "$TARGET"
tmux delete-buffer -b "$BUF" 2>/dev/null || true

# Enter has to be its own command: TUI agents read the paste and the submit as
# distinct events, and firing them together can drop the submit entirely.
sleep 0.5
tmux send-keys -t "$TARGET" Enter

sleep 1
echo "Replied to ${TARGET}."
echo "Report in: ${DOC}"
echo "--- last lines of ${TARGET} ---"
tmux capture-pane -p -t "$TARGET" | awk 'NF' | tail -n 6
