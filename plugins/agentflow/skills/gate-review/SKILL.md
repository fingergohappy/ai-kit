---
name: gate-review
model: opus
description: Review deliverables against design.
argument-hint: "[<report content or design document path>]"
context: fork
disable-model-invocation: false
---

# gate-review

Exit gate for the dispatching side. Reviews whether deliverables meet the standard, and decides whether to pass or require fixes.

**Core principle: Evaluate another agent's deliverables with a critical eye. Agents are not reliable; their reports are for reference only. Review from multiple angles — implementation completeness, code logic, and code style — rather than only checking for errors and unit tests.**

## Workflow

1. Obtain the content to review from conversation context or `$ARGUMENTS`
2. Locate the original task/design document (to compare against)
3. Extract the `loop` field from the tag (`[report from ..., loop: true/false]`)
   - If no loop field is present in the tag, default to `false`
4. Review item by item
5. Output the review conclusion
6. Decide the next step based on the conclusion and the loop field:
   - `loop: true` + fixes needed → automatically call `/dispatch` to send fix instructions (redo)
   - `loop: false` + fixes needed → output the conclusion and stop, do not automatically initiate fixes
   - Passed → mark as complete (regardless of loop value)

## Trigger Scenarios

### Scenario A: Cross-Agent Review (received report)

After receiving execution results reported by the receiving side via the report skill, review the deliverables.

Extract from the report message:
- The "original task" section to recover the original design

### Scenario B: Local Self-Review

After code implementation is complete and before committing, review your own code against the design document.

Obtain the design document path from `$ARGUMENTS` or conversation context.

## Review Dimensions

| Dimension | What to Check |
|-----------|--------------|
| Implementation completeness | Compare item by item against the original design; verify every task is implemented |
| Code logic | Logic errors, boundary conditions, bugs, security vulnerabilities |
| Code style | Naming conventions, code organization, interface design |
| Evaluate feedback | If the receiving side skipped or rejected tasks, judge whether their reasoning is valid |

## Review Requirements

- Compare item by item against the original design; no omissions allowed
- Verify inputs, outputs, and boundary conditions
- Check error handling, security vulnerabilities, and performance issues
- Check naming conventions, code style, and interface contracts
- Any deviation must be flagged
- If the receiving side skipped certain tasks via gate-evaluate, review whether the skip reasoning is valid

## Issue Classification

- `[偏离]` — Content defined in the design document is inconsistent with the code implementation
- `[逻辑]` — Code logic errors or flaws
- `[缺陷]` — Code quality issues: security, performance, maintainability

Severity levels: `[CRITICAL]` `[HIGH]` `[MEDIUM]` `[LOW]`

CRITICAL means it must be fixed.

## Output

After the review is complete, output the conclusion in this format:

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

## Behavior After Review

Behavior depends on the review conclusion and the loop tag:

### loop: true (loop mode)

| Conclusion | Behavior |
|------------|----------|
| Passed | Mark as complete, document status → done |
| Fixes needed | Automatically call `/dispatch` to send the issue list and fix suggestions back to the receiving side (redo) |
| Receiving side's rejection is justified | Accept the rejection, adjust the task or mark as complete |
| Receiving side's rejection is unjustified | Automatically call `/dispatch` to resend, with rebuttal explanation |

### loop: false (non-loop mode)

| Conclusion | Behavior |
|------------|----------|
| Passed | Mark as complete, document status → done |
| Fixes needed | Output the issue list and fix suggestions, **do not automatically initiate fixes**; let the user decide the next step |
| Receiving side's rejection is justified | Accept the rejection, inform the user |
| Receiving side's rejection is unjustified | Inform the user, let the user decide whether to redispatch |

## Termination Conditions

Stop the loop when any of the following conditions is met:

- Review passes completely (no CRITICAL/HIGH issues)
- Only MEDIUM/LOW issues remain
- Cumulative fix rounds reach 3
- User manually interrupts
