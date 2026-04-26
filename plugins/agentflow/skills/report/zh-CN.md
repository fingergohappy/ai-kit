---
name: report
description: |
  任务完成后向派发端 tmux 面板汇报执行结果。通过脚本生成格式化报告消息，经 tmux-send skill 发送。
  Report task execution results back to the dispatching tmux pane after task completion. Generates formatted report messages via script and sends through tmux-send skill.
when_to_use: |
  当用户说「汇报结果」「告诉对方完成了」「report」时触发。任务完成、收到 [task from ...] 或 [fix from ...] 标签时也应使用此 skill。
argument-hint: "[<target_pane_id>]"
model: haiku
context: fork
---

# report

任务完成后，向发起方的 tmux pane 汇报工作成果。

## Workflow

1. 确定 target_pane_id：
   - 优先从收到的 `[task from ..., pane_id: xxx, loop: xxx]` 或 `[fix from ..., pane_id: xxx, loop: xxx]` 标签中提取
   - 其次使用 `$ARGUMENTS` 传入的值
   - 仍未知则询问用户
2. 提取 loop 字段：
   - 从收到的标签中提取 `loop: true` 或 `loop: false`
   - 如果标签中没有 loop 字段，默认为 `false`
   - **必须原样传递到汇报消息的标签中**
3. 生成汇报消息，通过 tmux-send skill 发送到 target_pane_id

## Script Paths

所有 `scripts/` 路径相对于**本 SKILL.md 文件所在目录**。执行前必须先解析为绝对路径：

```bash
SKILL_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"  # 或直接使用本文件所在目录的绝对路径
```

后续命令中用 `"$SKILL_DIR/scripts/xxx.sh"` 替代裸 `scripts/xxx.sh`。

## Generate Report Message

使用 `"$SKILL_DIR/scripts/generate_message.sh"` 生成完整汇报消息，不要手动拼接模板内容。

**必须且只能**通过该脚本生成消息。严禁自己拼接或手写——保证格式一致、避免遗漏字段。

### 参数说明

必填参数：
- `--tool-name`：当前 AI 工具名称（如 `Claude Code`、`Cursor` 等）
- `--loop`：从收到的标签中提取的 loop 值（`true` 或 `false`）
- `--desc`：执行结果的一句话简要描述
- `--original-task`：原始任务内容（文档路径或内联任务描述）
- `--completed`：已完成的任务数量
- `--skipped`：已跳过的任务数量

可选参数：
- `--unprocessed`：未处理的任务数量（无则省略）
- `--evaluate`：gate-evaluate 评估结论（空则省略该节）
- `--skip-reasons`：跳过项说明（空则省略该节）
- `--issues`：遗留问题（空则省略该节）

### 调用示例

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

全部顺利完成时，省略可选参数即可：

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

通过 tmux-send skill 将生成的消息文件发送到 target_pane_id：

```
/tmux-send {target_pane_id} {MSG_FILE}
```

## Generation Rules

- 原始任务类型：**文档路径** → 引用路径；**内联内容** → 原样附上
- 完成情况必须量化
- 全部顺利完成时，省略 `--evaluate`、`--skip-reasons`、`--issues`
- 如果 gate-evaluate 评估导致跳过或拒绝，必须通过 `--evaluate` 和 `--skip-reasons` 体现
