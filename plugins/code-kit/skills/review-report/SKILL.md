---
name: review-report
description: |
  根据审查结果生成结构化的审查报告文档 / Generate structured review report from audit results.
  触发词：生成报告、生成审查报告、review report、导出报告、generate report。
  也可由其他 review skill 在审查完成后自动调用 / Can also be invoked by other review skills after audit completion.
argument-hint: ""
---

# review-report

根据审查结果，读取模板生成结构化的审查报告文档，输出到 `docs/review/`。

## 执行步骤

### 1. 收集审查结果

从前置审查流程（如 review-full、review-diff）获取以下信息：

- 审查模式：`full`（全量）或 `diff`（增量）
- base branch（仅 diff 模式）
- 变更文件数量
- 参与的 review skill 列表
- 问题列表（每个问题包含：严重级别、审查角度、文件路径:行号、问题描述、修复建议）

如果审查结果不在当前对话上下文中，提示用户先运行 `/review-full` 或 `/review-diff`。

### 2. 读取模板

读取 [report_template.md](references/report_template.md)，按模板格式生成报告。

### 3. 填充报告

将审查结果填入模板：

- **frontmatter**：填写标题、日期、模式、base branch、范围、问题统计、参与的 review skills
- **概述**：一句话总结审查了什么、发现了什么级别的问题
- **审查范围**：模式、文件数、审查角度列表
- **问题汇总**：各级别数量表格
- **问题详情**：按 CRITICAL → HIGH → MEDIUM → LOW 分组，每个问题包含审查角度、文件路径:行号、问题描述、修复建议、状态（默认 `[todo]`）
- **变更历史**：初始审查记录

### 4. 输出文件

- 全量审查：`docs/review/{YYYY-MM-DD}_full_review.md`
- 增量审查：`docs/review/{YYYY-MM-DD}_diff_review.md`

如果 `docs/review/` 目录不存在，先创建。

如果目标文件已存在，递增 frontmatter 中的 `version` 字段并覆盖写入。

### 5. 完成

输出文件路径，并提示用户可以通过 `/fix-review` 来修复发现的问题。
