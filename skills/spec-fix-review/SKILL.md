---
name: spec-fix-review
description: |
  将 review 文档发送到指定 tmux pane，让另一个 AI agent 先调用 tco-spec:spec-check-review
  技能审查 review 文档，确认问题准确后再执行修复。当用户有 review 文档，
  想让另一个 agent 去修复其中列出的问题时使用。
  即使用户只是说"修复 review"、"执行修复"、"fix review"，
  都应触发此 skill。
disable-model-invocation: true
argument-hint: [review文档路径, 如 docs/spec/xxx_review.md]
---

# spec-fix-review

把 review 文档发给另一个 AI agent，让它先审查文档准确性，再执行修复。

## 执行步骤

1. 获取当前 pane ID:
   ```bash
   tmux display-message -p '#{pane_id}'
   ```
2. 从 $ARGUMENTS 获取 review 文档路径
3. 如果没有提供路径，询问用户要修复哪个 review 文档
4. **更新关联文档状态为 `doing`**：找到 review 文档对应的 feature/change 文档，将其 frontmatter 中的 `status` 改为 `doing`
5. 生成修复指令消息（末尾附带反馈指令）
6. 通过 tco-spec:tmux-send skill 发送（由 tco-spec:tmux-send 负责确定目标 pane）

## 消息格式

固定开头 + review 文档路径：

```
使用 tco-spec:spec-check-review skill 查看以下 review 文档，并完成修复：

{review 文档路径}

---

执行完成后，调用 tco-spec:spec-feedback skill 向 pane {当前pane_id} 反馈结果。

[task from {当前AI工具名称, 如 Claude Code/Codex/OpenCode 等}: {当前对话的简要描述}, pane_id: {当前pane_id}]
```

## 发送方式

使用 tco-spec:tmux-send skill 发送，由它负责处理目标 pane 的选择。
