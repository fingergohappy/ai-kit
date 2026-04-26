---
name: review-full
description: |
  全量代码审查。启动子代理并行调用所有 review skills 扫描整个项目，汇总结果。
  Full project code review. Launches sub-agents in parallel calling all review skills to scan the entire project, then aggregates results.
  当用户说「全量审查」「review all」「review full」「全面检查」时触发。
  审查角度：shell 脚本质量、架构、skill 规范。
argument-hint: "[<directory path>]"
---

# review-full

Full code review with sub-agents calling all review skills in parallel to scan the entire project.

## Execution Steps

### 1. Determine Review Scope

- If `$ARGUMENTS` specifies a directory path, only scan that directory
- Otherwise scan the entire project (excluding common ignored directories like `node_modules`, `.git`, `vendor`, `dist`, `build`, `__pycache__`)

Collect project source code file list:

```bash
find . -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.py' -o -name '*.go' -o -name '*.rs' -o -name '*.java' -o -name '*.php' -o -name '*.swift' -o -name '*.kt' -o -name '*.rb' -o -name '*.sh' -o -name '*.md' \) \
  ! -path '*/node_modules/*' ! -path '*/.git/*' ! -path '*/vendor/*' ! -path '*/dist/*' ! -path '*/build/*' ! -path '*/__pycache__/*' ! -path '*/.next/*' ! -path '*/target/*'
```

### 2. Launch Sub-agents in Parallel

Launch one sub-agent for each of the following review skills (using Agent tool), passing the file list as input:

- `review-shell` — shell script quality review
- `review-architecture` — architecture review
- `review-skill-quality` — skill specification review

Each sub-agent:
- Reads the corresponding `.claude/skills/review-{angle}/SKILL.md`
- Checks items according to the review checklist defined therein
- Outputs issues found

Sub-agent prompt format:

```
Read .claude/skills/review-{angle}/SKILL.md and review the following files according to its checklist:

{file list}

Output issues found, each including: severity level, file path:line number, issue description, fix suggestion.
```

### 3. Aggregate Results

After all sub-agents complete, aggregate review results:

1. Sort by severity level: CRITICAL → HIGH → MEDIUM → LOW
2. Merge and deduplicate (different angles may find the same issue)
3. Count issues at each level

Output summary:

```
## Review Summary

| Level | Count |
|-------|-------|
| CRITICAL | {n} |
| HIGH | {n} |
| MEDIUM | {n} |
| LOW | {n} |

{Issues sorted by level}
```

### 4. Ask to Generate Report

After the summary output, ask the user:

```
Generate review report to docs/review/?
```

- User confirms → read report template, fill in review results, output to `docs/review/{date}_full_review.md`
- User declines → exit
