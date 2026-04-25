---
name: spec-fix-review
description: |
  将 review 文档发送到指定 tmux pane，让另一个 AI agent 先调用 ai-kit:spec-check-review
  技能审查 review 文档，确认问题准确后再执行修复。当用户有 review 文档，
  想让另一个 agent 去修复其中列出的问题时使用。
  即使用户只是说"修复 review"、"执行修复"、"fix review"，
  都应触发此 skill。
argument-hint: [review文档路径, 如 docs/spec/xxx_review.md]
---

# spec-fix-review

把 review 文档发给另一个 AI agent，让它先审查文档准确性，再执行修复。

## 执行步骤

1. 从 $ARGUMENTS 获取 review 文档路径
2. 如果没有提供路径，询问用户要修复哪个 review 文档
3. **更新关联文档状态为 `doing`**：找到 review 文档对应的 feature/change 文档，将其 frontmatter 中的 `status` 改为 `doing`
4. 通过脚本生成修复指令消息
5. 通过 ai-kit:tmux-send skill 发送（由 ai-kit:tmux-send 负责确定目标 pane）

## 生成消息

**必须且只能**通过 `scripts/generate_message.sh` 生成消息。严禁自己拼接或手写消息内容——无论多简单，都不允许绕过脚本。

需要准备的参数：
- `review_path`：review 文档路径
- `tool_name`：当前 AI 工具名称（如 `Claude Code`、`Cursor` 等）
- `desc`：对当前对话的一句话简要描述（由你生成）

```bash
MSG_FILE=$(bash scripts/generate_message.sh \
  --review-path "{review文档路径}" \
  --tool-name "{tool_name}" \
  --desc "{简要描述}")
```

## 发送方式

通过 ai-kit:tmux-send skill 发送，由它负责处理目标 pane 的选择：

```
/tmux-send {target_pane_id} {MSG_FILE}
```
