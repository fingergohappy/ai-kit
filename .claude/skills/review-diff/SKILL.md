---
name: review-diff
description: |
  增量代码审查。基于 git diff 获取变更文件，启动子代理并行调用所有 review skills，汇总结果。
  Incremental code review based on git diff. Launches sub-agents in parallel calling all review skills and aggregates results.
  当用户说「review diff」「审查变更」「review 改动」「检查 diff」时触发。
  审查角度：shell 脚本质量、架构、skill 规范。
argument-hint: "[<base_branch>]"
---

# review-diff

Incremental code review based on git diff changes, with sub-agents calling all review skills in parallel.

## Execution Steps

### 1. Get Changed Files

- If `$ARGUMENTS` specifies a base branch, use `git diff {base_branch}...HEAD --name-only`
- Otherwise detect the default branch:

```bash
# Try to get the default branch
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@')
if [ -z "$DEFAULT_BRANCH" ]; then
  # fallback: check main or master
  if git show-ref --verify --quiet refs/heads/main; then
    DEFAULT_BRANCH="main"
  elif git show-ref --verify --quiet refs/heads/master; then
    DEFAULT_BRANCH="master"
  fi
fi
```

- If the current branch is the default branch, use `git diff HEAD~1 --name-only` to get the latest commit's changes
- Also get unstaged and staged changes: `git diff --name-only && git diff --cached --name-only`
- Merge, deduplicate, and filter out deleted files

If there are no changed files, inform the user and exit.

### 2. Get Diff Content

Get diff details for each changed file:

```bash
git diff {base}...HEAD -- {file_path}
```

### 3. Launch Sub-agents in Parallel

Launch one sub-agent for each of the following review skills (using Agent tool), passing changed files and diff content as input:

- `review-shell` — shell script quality review
- `review-architecture` — architecture review
- `review-skill-quality` — skill specification review

Each sub-agent:
- Reads the corresponding `.claude/skills/review-{angle}/SKILL.md`
- Checks items according to the review checklist defined therein
- Focuses on changed parts but also checks context code that changes may affect

Sub-agent prompt format:

```
Read .claude/skills/review-{angle}/SKILL.md and review the following changes according to its checklist:

Changed files:
{file list}

Diff content:
{diff details}

Focus on changed parts but also check context code that changes may affect.
Output issues found, each including: severity level, file path:line number, issue description, fix suggestion.
```

### 4. Aggregate Results

After all sub-agents complete, aggregate review results:

1. Sort by severity level: CRITICAL → HIGH → MEDIUM → LOW
2. Merge and deduplicate (different angles may find the same issue)
3. Count issues at each level

Output summary:

```
## Review Summary (Incremental)

Base: {base_branch}
Changed files: {n}

| Level | Count |
|-------|-------|
| CRITICAL | {n} |
| HIGH | {n} |
| MEDIUM | {n} |
| LOW | {n} |

{Issues sorted by level}
```

### 5. Ask to Generate Report

After the summary output, ask the user:

```
Generate review report to docs/review/?
```

- User confirms → read report template, fill in review results, output to `docs/review/{date}_diff_review.md`
- User declines → exit
