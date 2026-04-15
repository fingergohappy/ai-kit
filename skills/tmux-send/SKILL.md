---
name: tmux-send
description: Send text content to a tmux pane using tmux send-keys, with automatic Enter. Use this skill whenever the user wants to send commands, code, or any text to a tmux pane, terminal panel, or another terminal window. Triggers on phrases like "send to tmux", "run in that pane", "execute in tmux", "send this to terminal", "paste to pane".
arguments:
  - name: pane_id
    description: tmux pane ID（如 %7，用 tmux list-panes 查看）
    required: false
  - name: content
    description: 要发送的内容（命令、代码等）
    required: false
---

# tmux-send

Send content to a tmux pane via paste buffer, then auto-press Enter.

## Workflow

Check `$ARGUMENTS` first, then fall back to natural language parsing:

1. `$ARGUMENTS` contains both pane_id and content (e.g. `%7 ls`) → send directly
2. `$ARGUMENTS` contains only pane_id (matches `%\d+` but no content after) → ask user for content
3. `$ARGUMENTS` is empty → extract content and pane_id from user's message context
4. If pane_id is still unknown → ask the user (plain text, no option list)

## pane_id

使用 tmux pane ID（如 `%7`），不是 session:window.pane 格式。pane ID 不会变，更稳定。

## Sending content

Use tmux paste buffer directly (no external script needed):

```bash
# 1. Verify the pane exists
tmux list-panes -t "<pane_id>"

# 2. Send content via paste buffer, then press Enter
tmux load-buffer - <<< "<content>"
tmux paste-buffer -p -r -t "<pane_id>"
tmux send-keys -t "<pane_id>" Enter
```

This handles multi-line content correctly via paste buffer, then auto-presses Enter to execute.
