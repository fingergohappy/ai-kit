---
name: tmux-send
model: haiku
description: Send text content to a tmux pane using tmux send-keys, with automatic Enter. Use this skill whenever the user wants to send commands, code, or any text to a tmux pane, terminal panel, or another terminal window. Triggers on phrases like "send to tmux", "run in that pane", "execute in tmux", "send this to terminal", "paste to pane".
argument-hint: [<pane_id>] [<content>]
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

使用脚本 `scripts/tmux_send.sh` 发送内容.


```bash
# 方式 1：直接传内容
bash scripts/tmux_send.sh "<pane_id>" "<content>"

# 方式 2：传文件路径（适合长内容）
bash scripts/tmux_send.sh "<pane_id>" "/tmp/message.txt"
```

