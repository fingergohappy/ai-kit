---
name: fix-review-all
description: |
  并行修复代码审查报告中的所有待处理问题。接收报告文档路径，提取所有 [todo] 状态问题，启动子代理逐个修复。
  Fix all pending issues in a code review report in parallel. Accepts a report document path, extracts all [todo] status issues, and launches sub-agents to fix each one via fix-review skill.
when_to_use: |
  当用户说「修复所有问题」「fix all review」「批量修复审查」时触发。
argument-hint: "<报告文档路径>"
---

# fix-review-all

并行修复审查报告中的所有待处理问题。

## Arguments

`$ARGUMENTS` 为审查报告文档路径，例如：

```
/code-kit:fix-review-all docs/review/2026-04-26_full_review.md
```

## Execution Steps

### 1. Read Report

1. 读取指定路径的报告文档
2. 校验文档格式：检查 frontmatter 是否包含 `type: code-review`
3. 如果文件不存在或格式不对，提示用户检查路径

### 2. Extract Pending Issues

从报告中提取所有状态为 `[todo]` 的问题块。每个问题块格式：

```markdown
### #N [角度] 问题标题

**文件**: `path/to/file:line`
**问题**: ...
**建议**: ...
**状态**: `[todo]`
```

统计待修复问题列表，按级别排序（CRITICAL → HIGH → MEDIUM → LOW）：

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

等待用户确认。用户可以：
- 确认全部修复
- 指定只修复某些编号（如「只修 #3 和 #4」）
- 取消

### 3. Launch Sub-agents in Parallel

对每个待修复问题启动一个子代理（使用 Agent 工具），并行执行。

子代理 prompt：

```
使用 fix-review skill 处理 {报告路径}:{问题块起始行号}
```

主代理的职责仅限于：
- 提取问题列表、展示给用户确认
- 并行启动子代理并传入正确参数
- 等待所有子代理完成后统一更新 frontmatter 的 `issue_stats` 和变更历史

所有子代理并行启动，不要逐个等待。

### 4. Wait and Aggregate

等待所有子代理完成，汇总结果：

```
修复汇总：

| # | 级别 | 状态 | 说明 |
|---|------|------|------|
| 3 | HIGH | ✅ 已修复 | 改用 printf 写入临时文件 |
| 4 | HIGH | ✅ 已修复 | 将 when_to_use 合并进 description |
| 1 | MEDIUM | ❌ 失败 | 源文件路径已变更 |
```

### 5. Update Report Statistics

根据实际修复结果统一更新报告：

1. 统计每个级别的修复数量，更新 frontmatter 中的 `issue_stats`
2. 在变更历史表格追加一行：

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

- **报告路径无效** → 提示用户检查路径
- **没有 [todo] 问题** → 提示「所有问题已处理」并结束
- **子代理修复失败** → 在汇总中标记失败，不影响其他问题的修复
- **多个问题修改同一文件** → 子代理之间可能冲突，主代理在汇总时检查是否有冲突的修改，如有则提示用户手动确认
- **子代理无法更新报告** → 主代理在步骤 5 统一处理状态更新和统计
