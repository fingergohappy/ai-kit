---
name: fix-review-all
description: |
  并行修复代码审查报告中的所有待处理问题。当用户说「修复所有问题」、「fix all review」、「批量修复审查」时触发。
  Batch-fix all pending issues from a code review report in parallel. Accepts the report document path as an argument, extracts all [todo] issues, and invokes fix-review via sub-agents in parallel.
argument-hint: "<报告文档路径>"
---

# fix-review-all

Batch-fix all pending issues from a code review report in parallel.

## Parameters

`$ARGUMENTS` is the path to the review report document, for example:

```
/code-kit:fix-review-all docs/review/2026-04-26_full_review.md
```

## Execution Steps

### 1. Read the Report

1. Read the report document at the specified path
2. Validate the document format: check that the frontmatter contains `type: code-review`
3. If the file does not exist or has an invalid format, prompt the user to check the path

### 2. Extract Issues to Fix

Extract all issue blocks with `[todo]` status from the report. Each issue block has this format:

```markdown
### #N [角度] 问题标题

**文件**: `path/to/file:line`
**问题**: ...
**建议**: ...
**状态**: `[todo]`
```

List the issues to fix, sorted by severity (CRITICAL > HIGH > MEDIUM > LOW):

```
发现 N 个待修复问题：

| # | 级别 | 角度 | 标题 |
|---|------|------|------|
| 3 | HIGH | shell | here-string 中变量未加引号 |
| 4 | HIGH | skill | when_to_use 非标准字段 |
| 1 | MEDIUM | shell | cat 命令替换丢失尾部换行 |
| ... | ... | ... | ... |

确认批量修复？
```

Wait for user confirmation. The user can:
- Confirm fixing all issues
- Specify only certain issue numbers (e.g., "only fix #3 and #4")
- Cancel

### 3. Launch Sub-Agents in Parallel

For each issue to fix, launch a sub-agent (using the Agent tool) in parallel.

Sub-agent prompt:

```
使用 fix-review skill 处理 {报告路径}:{问题块起始行号}
```

The main agent is only responsible for:
- Extracting the issue list and presenting it to the user for confirmation
- Launching sub-agents in parallel with correct arguments
- Waiting for all sub-agents to complete, then updating the frontmatter `issue_stats` and change history

All sub-agents must be launched in parallel; do not wait for each one sequentially.

### 4. Wait and Summarize

Wait for all sub-agents to complete, then summarize the results:

```
修复汇总：

| # | 级别 | 状态 | 说明 |
|---|------|------|------|
| 3 | HIGH | ✅ 已修复 | 改用 printf 写入临时文件 |
| 4 | HIGH | ✅ 已修复 | 将 when_to_use 合并进 description |
| 1 | MEDIUM | ❌ 失败 | 源文件路径已变更 |
```

### 5. Update Report Statistics and Change History

Update the report based on actual fix results:

1. Count the number of fixes per severity level and update `issue_stats` in the frontmatter
2. Append a row to the change history table:

```markdown
| 2026-04-26 | 批量修复: 修复 N 个问题（CRITICAL n, HIGH n, MEDIUM n, LOW n） |
```

### 6. Completion Notice

```
批量修复完成：
- 报告: docs/review/2026-04-26_full_review.md
- 成功: N 个
- 失败: N 个
- 跳过: N 个
```

## Edge Cases

- **Invalid report path** > Prompt the user to check the path
- **No [todo] issues** > Display "All issues have been resolved" and exit
- **Sub-agent fix failure** > Mark as failed in the summary; do not affect other issues
- **Multiple issues modifying the same file** > Sub-agents may conflict; the main agent checks for conflicting changes in the summary and prompts the user for manual confirmation if needed
- **Sub-agent unable to update report** > The main agent handles all status updates and statistics in step 5
