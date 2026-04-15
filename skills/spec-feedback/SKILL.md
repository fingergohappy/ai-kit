---
name: spec-feedback
description: |
  任务完成后向发起方反馈执行结果。当收到带有 [task from ...] 标签的消息
  并完成任务后，使用此 skill 向发起方的 tmux pane 发送反馈。
  即使用户只是说"反馈"、"汇报结果"、"完成了"，都应触发此 skill。
disable-model-invocation: true
argument-hint: [目标pane_id]
---

# spec-feedback

任务完成后，向发起方的 tmux pane 反馈执行结果。

## 触发条件

当收到包含 `[task from ...]` 标签的消息时，完成任务后调用此 skill 反馈。

## 执行步骤

1. 获取当前 pane ID:
   ```bash
   tmux display-message -p '#{pane_id}'
   ```
2. 从收到的 `[task from ...]` 标签中提取目标 pane_id
3. 生成反馈消息
4. 通过 tco-spec:tmux-send skill 发送到目标 pane

## 反馈格式

```
## 执行反馈

### 完成情况

- 已完成: {数量} 项
- 已跳过: {数量} 项
- 未处理: {数量} 项（如有）

### 跳过项说明

- {跳过的任务}: {原因}
- {跳过的任务}: {原因}

### 遗留问题

- {未处理的问题说明}（如有）

---

[feedback from {当前AI工具名称}: {执行结果简要描述}, pane_id: {当前pane_id}]
```

## 生成规则

- 完成情况必须量化（完成/跳过/未处理各多少）
- 跳过的任务必须注明原因
- 未处理的任务必须说明原因和后续建议
- 如果全部顺利完成，跳过"跳过项说明"和"遗留问题"部分

## 发送方式

使用 tco-spec:tmux-send skill 发送反馈消息到目标 pane。
