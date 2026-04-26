---
name: tmux-send
model: haiku
description: |
  Send content to a tmux pane and auto-execute. Triggers on "send to pane", "run in tmux", or any phrase targeting a specific pane number.
argument-hint: "[<pane_id>] [<内容>]"
disable-model-invocation: false
---

# tmux-send

Send content to a specified tmux pane and automatically press Enter.

## Workflow

Check `$ARGUMENTS` first; otherwise parse from natural language:

1. `$ARGUMENTS` contains both pane_id and content (e.g. `%7 ls` or `7 ls`) → send directly
2. `$ARGUMENTS` has only pane_id (no trailing content) → ask the user what to send
3. `$ARGUMENTS` is empty → extract pane_id and content from conversation context; the user may say things like "send that code snippet to 7" or "send what you just modified to %3", where the content comes from existing code or text in the conversation
4. pane_id is still unknown → ask the user (plain text, do not display a list of options)

## Script Paths

All `scripts/` paths are relative to **the directory containing this SKILL.md file**. Resolve them to absolute paths before execution:

```bash
SKILL_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"  # or use the absolute path of this file's directory directly
```

In subsequent commands, replace bare `scripts/xxx.sh` with `"$SKILL_DIR/scripts/xxx.sh"`.

## Sending Content

Content **must** be sent exclusively through the script. Directly calling `tmux send-keys` or any other tmux command is strictly forbidden — no matter how simple the content, bypassing the script is not allowed. This ensures consistent behavior, avoids escaping issues, and simplifies maintenance.

```bash
# Method 1: pass content directly
bash "$SKILL_DIR/scripts/tmux_send.sh" "<pane_id>" "<content>"

# Method 2: pass a file path (suitable for long content)
bash "$SKILL_DIR/scripts/tmux_send.sh" "<pane_id>" "/tmp/message.txt"
```
