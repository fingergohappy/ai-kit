---
name: review-full
description: |
  全量代码审查。启动子代理并行调用所有 review skills 扫描整个项目，汇总结果。审查角度：shell 脚本质量、架构、skill 规范。
  Full project code review. Launches sub-agents in parallel calling all review skills to scan the entire project, then aggregates results. Reviews from shell quality, architecture, and skill specification perspectives.
when_to_use: |
  当用户说「全量审查」「review all」「review full」「全面检查」「审查整个项目」时触发。
argument-hint: "[<目录路径>]"
---

# review-full

全量代码审查，子代理并行调用所有 review skills，扫描整个项目。

## Execution Steps

### 1. Determine Review Scope

- 如果 `$ARGUMENTS` 指定了目录路径，只扫描该目录
- 否则扫描整个项目（排除 `node_modules`、`.git`、`vendor`、`dist`、`build`、`__pycache__` 等常见忽略目录）

收集项目源代码文件列表：

```bash
find . -type f \( -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.py' -o -name '*.go' -o -name '*.rs' -o -name '*.java' -o -name '*.php' -o -name '*.swift' -o -name '*.kt' -o -name '*.rb' -o -name '*.sh' -o -name '*.md' \) \
  ! -path '*/node_modules/*' ! -path '*/.git/*' ! -path '*/vendor/*' ! -path '*/dist/*' ! -path '*/build/*' ! -path '*/__pycache__/*' ! -path '*/.next/*' ! -path '*/target/*'
```

### 2. Launch Sub-agents in Parallel

对以下 review skills 各启动一个子代理（使用 Agent 工具），将文件列表作为输入：

- `review-shell` — shell 脚本质量审查
- `review-architecture` — 架构审查
- `review-skill-quality` — skill 规范审查

每个子代理：
- 读取对应的 `.claude/skills/review-{角度}/SKILL.md`
- 按其中定义的审查清单逐项检查
- 输出发现的问题

子代理 prompt 格式：

```
请读取 .claude/skills/review-{角度}/SKILL.md，按其中的审查清单审查以下文件：

{文件列表}

输出发现的问题，每个问题包含：严重级别、文件路径:行号、问题描述、修复建议。
```

### 3. Aggregate Results

等待所有子代理完成后，汇总审查结果：

1. 按严重级别排序：CRITICAL → HIGH → MEDIUM → LOW
2. 合并去重（不同角度可能发现同一问题）
3. 统计各级别问题数量

输出汇总：

```
## 审查汇总

| 级别 | 数量 |
|------|------|
| CRITICAL | {n} |
| HIGH | {n} |
| MEDIUM | {n} |
| LOW | {n} |

{按级别排序的问题列表}
```

### 4. Ask to Generate Report

汇总输出后询问用户：

```
是否生成审查报告到 docs/review/？
```

- 用户确认 → 读取报告模板，填入审查结果，输出到 `docs/review/{日期}_full_review.md`
- 用户拒绝 → 结束
