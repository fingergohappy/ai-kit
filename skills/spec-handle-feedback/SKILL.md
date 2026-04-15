---
name: spec-handle-feedback
description: |
  处理来自另一个 AI agent 的执行反馈，调用 tco-spec:spec-review 审查结果，
  根据审查结论决定是否继续修复。当收到带有 [feedback from ...] 标签的
  消息时自动触发。即使用户只是说"处理反馈"、"看看反馈"、
  "检查结果"，都应触发此 skill。
disable-model-invocation: true
argument-hint: [可选: 反馈消息内容]
---

# spec-handle-feedback

收到另一个 agent 的执行反馈后，审查其工作结果，决定是否继续修复。

## 触发条件

当收到包含 `[feedback from ...]` 标签的消息时触发。

## 执行步骤

1. 获取反馈来源信息（从消息末尾的 `[feedback from ...]` 标签中提取 pane_id）
2. 调用 tco-spec:spec-review 审查反馈对应的代码变更
3. 根据审查结果决定下一步：
   - 全部通过 → 结束，通知用户
   - 有 CRITICAL/HIGH 问题 → 调用 tco-spec:spec-implement 发送修复任务（再来一轮）
   - 只有 MEDIUM/LOW 问题 → 结束，将审查结果告知用户，由用户决定
4. 如果进入新一轮修复，累计轮次，达到 3 轮上限时停下来让用户决定

## 调用 tco-spec:spec-review 的规则

- 如果原始任务有对应的 feature/change 文档 → 正常调用 tco-spec:spec-review 生成审查报告
- 如果原始任务**没有文档**（如模式 A 从对话总结的任务）→ **不生成审查文档**，
  直接在对话中完成审查，将审查结果通过 tco-spec:spec-implement 发送过去

## 终止条件

以下情况停止循环，通知用户：
- 审查全部通过
- 只剩 MEDIUM/LOW 级别问题
- 累计修复轮次达到 3 轮

## 通知格式

完成或终止时，告知用户：

```
## 反馈处理结果

- 修复轮次: {N} 轮
- 最终状态: {通过 / 仍有 N 个问题}
- 审查报告: {文档路径 或 "无文档，审查在对话中完成"}
{如果有遗留问题，列出问题摘要}
```
