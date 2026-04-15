---
name: spec-implement
description: |
  将讨论结论或设计文档发送到指定 tmux pane，让另一个 AI agent 去执行。
  执行完成后对方会通过 tco-spec:tmux-send 反馈结果。
  当用户完成设计讨论想把任务分发出去时使用，支持从对话总结或直接发送已有文档。
  即使用户只是说"发过去"、"send 过去"、"开始干"、"implement"，
  都应触发此 skill。
disable-model-invocation: true
argument-hint: [文档路径, 如 docs/spec/xxx_feature.md]
---

# spec-implement

把讨论的结论或已有的设计文档发到另一个 tmux 窗口的 AI agent 去执行。

## 执行步骤

1. 获取当前 pane ID:
   ```bash
   tmux display-message -p '#{pane_id}'
   ```
2. 判断输入来源:
   - 如果 $ARGUMENTS 包含 `.md` 文件路径 → 读取文档内容，走模式 B
   - 否则 → 从当前对话上下文总结，走模式 A
3. **更新文档状态为 `doing`**：如果输入来源是已有文档，将该文档 frontmatter 中的 `status` 从 `draft` 改为 `doing`
4. 生成消息内容（末尾附带反馈指令）
5. 通过 tco-spec:tmux-send skill 发送（由 tco-spec:tmux-send 负责确定目标 pane）

## 模式 A：从对话总结

从当前对话上下文中提取变更信息，合成消息。

```
## 变更方向

{1-2 句说明这次要做什么、为什么}

## 关键决策

- {决策点}: {结论}
- {决策点}: {结论}

## 任务清单

1. [ ] {具体任务 - 包含文件路径/函数名/做什么}
2. [ ] {具体任务 - 包含文件路径/函数名/做什么}

---

执行完成后，调用 tco-spec:spec-feedback skill 向 pane {当前pane_id} 反馈结果。

[task from {当前AI工具名称, 如 Claude Code/Codex/OpenCode 等}: {当前对话的简要描述}, pane_id: {当前pane_id}]
```

## 模式 B：发送已有文档

读取指定的 feature/change 文档，附加执行指令后发送。

```
请按照以下设计文档实现：

{文档内容}

完成每个任务后，将文档中对应的"实现状态"从 [todo] 更新为 [done]。
如果某个任务跳过，更新为 [skip] 并注明原因。

---

执行完成后，调用 tco-spec:spec-feedback skill 向 pane {当前pane_id} 反馈结果。

[task from {当前AI工具名称, 如 Claude Code/Codex/OpenCode 等}: {当前对话的简要描述}, pane_id: {当前pane_id}]
```

## 生成规则

- 变更方向只说结论（做什么、为什么），不说讨论过程
- 关键决策只列出最终选择，不列被否决的方案
- 任务要具体到文件路径和函数名，让接收端可以直接开始工作
- 任务按依赖顺序排列（前置依赖在前）
- 任务粒度适中：一个任务对应一个明确、可验证的改动

## 发送方式

使用 tco-spec:tmux-send skill 发送，由它负责处理目标 pane 的选择。
