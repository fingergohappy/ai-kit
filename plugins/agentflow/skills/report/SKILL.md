---
name: report
model: haiku
description: Report task results to originator.
argument-hint: "[<target_pane_id>]"
context: fork
disable-model-invocation: false
---

# report

After a task completes, report the results to the originating tmux pane.

## Workflow

1. Determine target_pane_id:
   - First, extract from the received `[task from ..., pane_id: xxx, loop: xxx]` or `[fix from ..., pane_id: xxx, loop: xxx]` tag
   - Then fall back to the value passed via `$ARGUMENTS`
   - If still unknown, ask the user
2. Extract the loop field:
   - Extract `loop: true` or `loop: false` from the received tag
   - If the tag has no loop field, default to `false`
   - **Must be passed verbatim into the report message tag**
3. Generate the report message and send it to target_pane_id via the tmux-send skill

## Script Path

All `scripts/` paths are relative to **the directory containing this SKILL.md file**. Resolve them to absolute paths before execution:

```bash
SKILL_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"  # 或直接使用本文件所在目录的绝对路径
```

Use `"$SKILL_DIR/scripts/xxx.sh"` instead of bare `scripts/xxx.sh` in subsequent commands.

## Generate Report Message

Use `"$SKILL_DIR/scripts/generate_message.sh"` to generate the full report message. Do not assemble template content manually.

You **must** use this script exclusively to generate the message. Never assemble or hand-write it yourself -- this ensures consistent formatting and prevents missing fields.

### Parameter Reference

Required parameters:
- `--tool-name`: Current AI tool name (e.g., `Claude Code`, `Cursor`, etc.)
- `--loop`: Loop value extracted from the received tag (`true` or `false`)
- `--desc`: One-sentence summary of the execution result
- `--original-task`: Original task content (document path or inline task description)
- `--completed`: Number of completed tasks
- `--skipped`: Number of skipped tasks

Optional parameters:
- `--unprocessed`: Number of unprocessed tasks (omit if none)
- `--evaluate`: gate-evaluate assessment conclusion (omit if empty)
- `--skip-reasons`: Explanation for skipped items (omit if empty)
- `--issues`: Outstanding issues (omit if empty)

### Invocation Example

```bash
MSG_FILE=$(bash "$SKILL_DIR/scripts/generate_message.sh" \
  --tool-name "{tool_name}" \
  --loop "{loop值}" \
  --desc "{简要描述}" \
  --original-task "{文档路径或内联任务描述}" \
  --completed {数量} \
  --skipped {数量} \
  --unprocessed {数量} \
  --evaluate "{gate-evaluate 评估结论摘要}" \
  --skip-reasons "{跳过的任务及原因}" \
  --issues "{遗留问题说明}")
```

When everything completes successfully, omit the optional parameters:

```bash
MSG_FILE=$(bash "$SKILL_DIR/scripts/generate_message.sh" \
  --tool-name "{tool_name}" \
  --loop "{loop值}" \
  --desc "{简要描述}" \
  --original-task "{文档路径}" \
  --completed {数量} \
  --skipped 0)
```

## Send Message

Send the generated message file to target_pane_id via the tmux-send skill:

```
/tmux-send {target_pane_id} {MSG_FILE}
```

## Generation Rules

- Original task type: **document path** -> reference the path; **inline content** -> include verbatim
- Completion status must be quantified
- When everything completes successfully, omit `--evaluate`, `--skip-reasons`, and `--issues`
- If gate-evaluate causes tasks to be skipped or rejected, this must be reflected via `--evaluate` and `--skip-reasons`
