---
name: spec-implement
model: haiku
description: |
  将设计文档发送到指定 tmux pane 执行。执行完成后会通过 spec-feedback 反馈结果。
  只要用户提到「发过去」、「send 过去」、「开始干」、「implement」、「发到某个 pane 执行」，就应该使用此 skill。
argument-hint: "[<target_pane_id>] [<文档路径或内联任务>]"
context: fork
---

# spec-implement

将设计文档或任务内容发送到指定 tmux pane 执行，执行完成后由目标 pane 通过 spec-feedback 反馈结果。

## 工作流程

优先检查 `$ARGUMENTS`，否则从对话上下文中解析：

1. `$ARGUMENTS` 同时包含 target_pane_id 和文档路径/内容 → 直接执行
2. `$ARGUMENTS` 只有 target_pane_id → 询问用户文档路径或任务内容
3. `$ARGUMENTS` 只有文档路径/内容，未指定 target_pane_id → 列出可用 pane 供用户选择：
   ```bash
   tmux list-panes -F "#{pane_id}: #{pane_current_command} [#{pane_width}x#{pane_height}]"
   ```
4. `$ARGUMENTS` 为空 → 从对话上下文提取；用户可能说「把这个发到 7」，此时文档路径或内容来自对话中已有内容
5. target_pane_id 仍未知 → 询问用户（纯文本，不显示选项列表）

## 执行步骤

1. 确定 target_pane_id（见工作流程）
2. 若参数是文件路径，读取文档内容；若文档有 frontmatter，将 `status` 从 `draft` 改为 `doing`
3. 按下方说明生成消息，通过 tmux-send skill 发送到 target_pane_id

## 生成发送消息

使用 `scripts/generate_message.sh` 生成格式化消息，不要手动拼接模板内容。

**必须且只能**通过 `scripts/generate_message.sh` 生成格式化消息。严禁自己拼接或手写消息内容——无论多简单，都不允许绕过脚本。这样做是为了保证消息格式一致、避免遗漏字段。

需要准备的参数：
- `tool_name`：当前 AI 工具名称（如 `Claude Code`、`Cursor` 等，从环境或对话上下文判断）
- `desc`：对任务的一句话简要描述（由你生成）

### 文档路径模式：

```bash
MSG_FILE=$(bash scripts/generate_message.sh \
  --mode doc \
  --doc-path "{文档路径}" \
  --tool-name "{tool_name}" \
  --desc "{简要描述}")
```

### 内联任务模式（将内容写入临时文件，再追加尾部）：

先将内联任务内容写入临时文件，然后追加脚本生成的尾部：

```bash
# 1. 将内联任务内容写入临时文件
MSG_FILE=$(mktemp /tmp/spec-inline-task.XXXXXX)
echo "{内联任务内容}" > "$MSG_FILE"

# 2. 生成尾部并追加
FOOTER_FILE=$(bash scripts/generate_message.sh \
  --mode inline \
  --tool-name "{tool_name}" \
  --desc "{简要描述}")
cat "$FOOTER_FILE" >> "$MSG_FILE"
rm "$FOOTER_FILE"
```

## 发送消息

通过 tmux-send skill 将生成的消息文件发送到 target_pane_id：

```
/tmux-send {target_pane_id} {MSG_FILE}
```
