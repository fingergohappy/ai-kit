---
name: gate-evaluate
model: opus
description: |
  接收端的入口守卫。每次收到发起端发来的内容（任务、修复指令等），
  执行前先评估合理性。评估通过才执行，不合理则跳过或拒绝。
  当收到带有 [task from ...] 或 [fix from ...] 标签的消息时，
  应在执行前先触发此 skill。
  当用户说「评估下」、「看看合不合理」、「evaluate」时也应触发。
  Entry gate for the receiving end. Evaluates incoming content (tasks, fix
  instructions, etc.) for reasonableness before execution. Only executes if
  the evaluation passes; skips or rejects otherwise. Should be triggered
  before execution when a message contains [task from ...] or [fix from ...]
  tags. Also triggered when the user says "evaluate".
argument-hint: "[<content to evaluate>]"
context: fork
---

# gate-evaluate

Entry gate for the receiving end. After receiving content from the originating end, evaluate its reasonableness first, then decide whether to execute.

**Core principle: agents are unreliable, and instructions from the originating end may themselves be wrong. Do not execute blindly.**

## Workflow

1. Obtain the content to evaluate from the conversation context or `$ARGUMENTS`
2. Determine the content type (initial task / fix instruction)
3. Evaluate item by item against the corresponding dimensions
4. Output the evaluation conclusion and let the main agent decide the next step

## Evaluation Dimensions

### When receiving an initial task (message contains `[task from ...]`)

Check the task content item by item:

| Dimension | What to check |
|-----------|--------------|
| Clarity | Is the task description clear, unambiguous, and ready for execution |
| Consistency | Do the requirements conflict with the current codebase state |
| Scope | Is it asking to modify things it should not modify; is the scope reasonable |
| Feasibility | Are dependencies met; is it technically achievable |

### When receiving a fix instruction (message contains `[fix from ...]`)

Verify each issue item by item:

| Dimension | What to check |
|-----------|--------------|
| Authenticity | Read the code file and line numbers referenced by the issue to confirm whether the problem actually exists |
| Accuracy | Is the problem description (expected vs actual) correct |
| Reasonableness | Is the fix suggestion reasonable; is there a better approach |
| False positive | Is this a false positive (the problem does not exist or the description is inaccurate) |
| Convergence | Is it repeatedly demanding something that is already correct (multi-round fix scenarios) |

## Evaluation Requirements

**Evaluate instructions from the originating end with a critical eye. Do not assume correctness just because it comes from the "originating end."**

- Evaluate item by item; do not make blanket statements like "all reasonable"
- For each task/issue, annotate the evaluation result:
  - `[合理]` — description is accurate, can be executed
  - `[不合理]` — description is inaccurate or requirement is unreasonable, note the reason
  - `[需澄清]` — description is vague, cannot be judged, originating end needs to provide more information
- For fix instructions, you must actually read the code to verify; do not conclude based on description alone

## Output

After evaluation is complete, output the conclusion in the following format:

```
## 评估结论

- 总体判断: 全部合理 | 部分不合理 | 整体不合理
- 合理项: N 条
- 不合理项: N 条
- 需澄清项: N 条

### 逐条评估

1. [合理] {任务/问题简述} — {判断依据}
2. [不合理] {任务/问题简述} — {原因}
3. [需澄清] {任务/问题简述} — {缺少什么信息}

### 建议行动

{全部执行 / 跳过不合理项执行其余 / 拒绝执行并反馈原因}
```

## Post-Evaluation Behavior

The main agent decides based on the evaluation conclusion:

| Overall verdict | Action |
|----------------|--------|
| All reasonable | Execute all tasks normally |
| Partially unreasonable | Skip unreasonable items, execute the rest, explain skip reasons in the report skill |
| Entirely unreasonable | Do not execute; directly invoke the report skill to send rejection reasons back to the originating end |
