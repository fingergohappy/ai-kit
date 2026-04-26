---
name: review-diff
description: |
  增量代码审查。基于 git diff 获取变更文件，启动子代理并行调用所有 review skills，汇总结果。审查角度：shell 脚本质量、架构、skill 规范。
  Incremental code review based on git diff. Launches sub-agents in parallel calling all review skills and aggregates results. Reviews from shell quality, architecture, and skill specification perspectives.
when_to_use: |
  当用户说「review diff」「审查变更」「review 改动」「检查 diff」「增量审查」时触发。
argument-hint: "[<base_branch>]"
---

# review-diff

增量代码审查，基于 git diff 变更文件，子代理并行调用所有 review skills。

## Execution Steps

### 1. Get Changed Files

- 如果 `$ARGUMENTS` 指定了 base branch，使用 `git diff {base_branch}...HEAD --name-only`
- 否则检测默认分支：

```bash
# 尝试获取默认分支
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
if [ -z "$DEFAULT_BRANCH" ]; then
  # fallback: 检查 main 或 master
  if git show-ref --verify --quiet refs/heads/main; then
    DEFAULT_BRANCH="main"
  elif git show-ref --verify --quiet refs/heads/master; then
    DEFAULT_BRANCH="master"
  fi
fi
```

- 如果当前分支就是默认分支，使用 `git diff HEAD~1 --name-only` 获取最近一次提交的变更
- 同时获取未暂存和已暂存的变更：`git diff --name-only && git diff --cached --name-only`
- 合并去重，过滤掉已删除的文件

如果没有变更文件，告知用户并结束。

### 2. Get Diff Content

对每个变更文件获取 diff 详情：

```bash
git diff {base}...HEAD -- {file_path}
```

### 3. Launch Sub-agents in Parallel

对以下 review skills 各启动一个子代理（使用 Agent 工具），将变更文件和 diff 内容作为输入：

- `review-shell` — shell 脚本质量审查
- `review-architecture` — 架构审查
- `review-skill-quality` — skill 规范审查

每个子代理：
- 读取对应的 `.claude/skills/review-{角度}/SKILL.md`
- 按其中定义的审查清单逐项检查
- 重点关注变更部分，但也检查变更可能影响的上下文代码

子代理 prompt 格式：

```
请读取 .claude/skills/review-{角度}/SKILL.md，按其中的审查清单审查以下变更：

变更文件：
{文件列表}

Diff 内容：
{diff 详情}

重点关注变更部分，但也检查变更可能影响的上下文代码。
输出发现的问题，每个问题包含：严重级别、文件路径:行号、问题描述、修复建议。
```

### 4. Aggregate Results

等待所有子代理完成后，汇总审查结果：

1. 按严重级别排序：CRITICAL → HIGH → MEDIUM → LOW
2. 合并去重（不同角度可能发现同一问题）
3. 统计各级别问题数量

输出汇总：

```
## 审查汇总（增量）

基准: {base_branch}
变更文件: {n} 个

| 级别 | 数量 |
|------|------|
| CRITICAL | {n} |
| HIGH | {n} |
| MEDIUM | {n} |
| LOW | {n} |

{按级别排序的问题列表}
```

### 5. Ask to Generate Report

汇总输出后询问用户：

```
是否生成审查报告到 docs/review/？
```

- 用户确认 → 读取报告模板，填入审查结果，输出到 `docs/review/{日期}_diff_review.md`
- 用户拒绝 → 结束
