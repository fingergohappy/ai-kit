---
name: gate-review
description: |
  派发端出口守卫。对照原始设计文档审查接收端的工作成果，决定批准、要求修复或升级。也支持本地代码对照设计文档的自审。
  Exit guard for the dispatching end. Reviews the receiving agent's work against the original design document. Determines whether to approve, request fixes, or escalate. Also supports local self-review.
when_to_use: |
  当用户说「审查下」「review」「看看做得怎么样」「检查结果」时触发。收到带有 [report from ...] 标签的消息时自动触发。
argument-hint: "[<汇报内容或设计文档路径>]"
model: opus
context: fork
---

# gate-review

发起端的出口守卫。审查工作成果是否达标，决定通过还是要求修复。

**核心原则：以审视的眼光评估另一个 agent 的工作成果。agent 并不可靠，汇报内容仅作参考。从实现完整性、代码逻辑、代码风格多个方向进行审查，而非仅检查报错和单元测试。**

## Workflow

1. 从对话上下文或 `$ARGUMENTS` 获取待审查的内容
2. 找到原始任务/设计文档（用于对照）
3. 从标签中提取 `loop` 字段（`[report from ..., loop: true/false]`）
   - 如果标签中没有 loop 字段，默认为 `false`
4. 逐条审查
5. 输出审查结论
6. 根据结论和 loop 字段决定下一步：
   - `loop: true` + 需修复 → 自动调用 `/dispatch` 发送修复指令（redo）
   - `loop: false` + 需修复 → 输出结论就结束，不自动发起修复
   - 通过 → 标记完成（无论 loop 值）

## Trigger Scenarios

### 场景 A: Cross-agent Review

收到接收端通过 report skill 汇报的执行结果后，审查工作成果。

从汇报消息中提取：
- 「原始任务」部分找回原始设计

### 场景 B: Local Self-review

代码实现完成后、提交前，对照设计文档审查自己的代码。

从 `$ARGUMENTS` 或对话上下文获取设计文档路径。

## Review Dimensions

| 维度 | 检查内容 |
|------|---------|
| 实现完整性 | 逐条对照原始设计，每项任务是否都已实现 |
| 代码逻辑 | 逻辑错误、边界条件、bug、安全隐患 |
| 代码风格 | 命名规范、代码组织、接口设计 |
| 评估反馈 | 如果接收端跳过或拒绝了部分任务，判断其理由是否成立 |

## Review Requirements

- 逐条对照原始设计，不允许遗漏
- 验证输入/输出/边界条件
- 检查错误处理、安全隐患、性能问题
- 检查命名规范、代码风格、接口契约
- 发现任何偏差都必须标记
- 如果接收端通过 gate-evaluate 跳过了某些任务，审查其跳过理由是否成立

## Issue Classification

- `[偏离]` — 设计文档定义的内容与代码实现不一致
- `[逻辑]` — 代码逻辑错误或缺陷
- `[缺陷]` — 代码质量问题：安全、性能、可维护性

严重级别：`[CRITICAL]` `[HIGH]` `[MEDIUM]` `[LOW]`

CRITICAL 意味着必须修复。

## Output

审查完成后输出结论，格式：

```
## 审查结论

- 总体判断: 通过 | 需要修复
- 修复轮次: {当前轮次}
- 问题统计: CRITICAL: N, HIGH: N, MEDIUM: N, LOW: N

### 问题列表

1. [CRITICAL] [偏离] {问题描述} — {文件路径:行号范围}
   → 修复建议: {具体建议}
2. [HIGH] [逻辑] {问题描述} — {文件路径:行号范围}
   → 修复建议: {具体建议}
3. [MEDIUM] [缺陷] {问题描述}（可选修复）

### 跳过项审查

{如果接收端跳过了任务，逐条审查跳过理由}
- {跳过的任务}: 理由成立 / 理由不成立（需重新执行）

### 结论

{通过：标记完成 / 需修复：列出修复任务清单}
```

## Post-review Behavior

行为取决于审查结论和 loop 标签：

### loop: true（循环模式）

| 结论 | 行为 |
|------|------|
| 通过 | 标记完成，文档 status → done |
| 需修复 | 自动调用 `/dispatch` 将问题列表和修复建议发回接收端（redo） |
| 接收端拒绝有理 | 接受拒绝，调整任务或标记完成 |
| 接收端拒绝无理 | 自动调用 `/dispatch` 重新发送，附上反驳说明 |

### loop: false（非循环模式）

| 结论 | 行为 |
|------|------|
| 通过 | 标记完成，文档 status → done |
| 需修复 | 输出问题列表和修复建议，**不自动发起修复**，由用户决定下一步 |
| 接收端拒绝有理 | 接受拒绝，告知用户 |
| 接收端拒绝无理 | 告知用户，由用户决定是否重新派发 |

## Termination Conditions

以下任一条件满足时停止循环：

- 审查全部通过（无 CRITICAL/HIGH）
- 仅剩 MEDIUM/LOW 问题
- 累计修复轮次达到 3 轮
- 用户手动中断
