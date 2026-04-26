---
name: dispatch
description: |
  将设计文档或任务内容派发到指定 tmux 面板执行。接收端先通过 gate-evaluate 评估再执行。支持首次派发（设计→执行）和修复派发（审查→重做）。
  Dispatch design documents or task content to a specified tmux pane for execution. The receiving end evaluates first via gate-evaluate, then executes. Supports first-time dispatch and fix dispatch.
when_to_use: |
  当用户说「发过去」「send 过去」「开始干」「dispatch」「派发到某个 pane」「让他去做」「让{number}去做」「让{number}来」时触发。
argument-hint: "[loop] [<target_pane_id>] [<文档路径或内联任务>]"
model: haiku
context: fork
---

# dispatch

将设计文档或任务内容派发到指定 tmux pane 执行。接收端会先评估再执行。

## Loop Parameter

`loop` 标记会写入消息标签，通过 report 传回发起端，gate-review 据此决定行为。

## Workflow

优先检查 `$ARGUMENTS`，否则从对话上下文中解析：

1. `$ARGUMENTS` 同时包含 target_pane_id 和文档路径/内容 → 直接执行
2. `$ARGUMENTS` 只有 target_pane_id → 询问用户文档路径或任务内容
3. `$ARGUMENTS` 只有文档路径/内容，未指定 target_pane_id → 询问用户要发送到哪个 pane
4. `$ARGUMENTS` 为空 → 从对话上下文提取；用户可能说「把这个发到 7」，此时文档路径或内容来自对话中已有内容
5. target_pane_id 仍未知 → 询问用户（纯文本，不显示选项列表）

## Two Modes

### 首次派发（design → do）

将设计文档或任务内容发给接收端执行。

### 修复派发（review → redo）

gate-review 审查后发现问题，将修复指令发给接收端。此时 dispatch 的输入是 gate-review 输出的问题列表和修复建议。

## Execution Steps

1. 确定 target_pane_id（见工作流程）
2. 确定派发模式（首次 / 修复）
3. 若参数是文件路径，读取文档内容；若文档有 frontmatter，将 `status` 从 `draft` 改为 `doing`
4. 按下方说明生成消息，通过 tmux-send skill 发送到 target_pane_id

## Script Paths

所有 `scripts/` 路径相对于**本 SKILL.md 文件所在目录**。执行前必须先解析为绝对路径：

```bash
SKILL_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"  # 或直接使用本文件所在目录的绝对路径
```

后续命令中用 `"$SKILL_DIR/scripts/xxx.sh"` 替代裸 `scripts/xxx.sh`。

## Generate Send Message

使用 `"$SKILL_DIR/scripts/generate_message.sh"` 生成格式化消息，不要手动拼接模板内容。

**必须且只能**通过该脚本生成格式化消息。严禁自己拼接或手写消息内容——无论多简单，都不允许绕过脚本。这样做是为了保证消息格式一致、避免遗漏字段。

需要准备的参数：
- `tool_name`：当前 AI 工具名称（如 `Claude Code`、`Cursor` 等，从环境或对话上下文判断）
- `desc`：对任务的一句话简要描述（由你生成）
- `loop`：如果用户要求启用循环，加上 `--loop` 标志

### 首次派发（文档路径模式）：

```bash
MSG_FILE=$(bash "$SKILL_DIR/scripts/generate_message.sh" \
  --mode doc \
  --doc-path "{文档路径}" \
  --tool-name "{tool_name}" \
  --desc "{简要描述}" \
  [--loop])
```

### 首次派发（内联任务模式）：

先将内联任务内容写入临时文件，然后追加脚本生成的尾部：

```bash
# 1. 将内联任务内容写入临时文件
MSG_FILE=$(mktemp /tmp/dispatch-inline-task.XXXXXX)
echo "{内联任务内容}" > "$MSG_FILE"

# 2. 生成尾部并追加
FOOTER_FILE=$(bash "$SKILL_DIR/scripts/generate_message.sh" \
  --mode inline \
  --tool-name "{tool_name}" \
  --desc "{简要描述}" \
  [--loop])
cat "$FOOTER_FILE" >> "$MSG_FILE"
rm "$FOOTER_FILE"
```

### 修复派发：

```bash
# 1. 将修复指令写入临时文件
MSG_FILE=$(mktemp /tmp/dispatch-fix-task.XXXXXX)
echo "{gate-review 输出的问题列表和修复建议}" > "$MSG_FILE"

# 2. 生成尾部并追加
FOOTER_FILE=$(bash "$SKILL_DIR/scripts/generate_message.sh" \
  --mode fix \
  --tool-name "{tool_name}" \
  --desc "{简要描述}" \
  --loop)
cat "$FOOTER_FILE" >> "$MSG_FILE"
rm "$FOOTER_FILE"
```

注意：修复派发一定带 `--loop`，因为只有循环模式下才会触发修复派发。

## Send Message

通过 tmux-send skill 将生成的消息文件发送到 target_pane_id：

```
/tmux-send {target_pane_id} {MSG_FILE}
```
