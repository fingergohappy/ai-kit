---
name: fix-review
description: |
  修复代码审查报告中的问题并自动更新报告状态。修复前评估建议的合理性，将状态从 [todo] 更新为 [done]。
  Fix issues found in code review reports and automatically update report status. Evaluates the reasonableness of report suggestions before fixing, then updates status from [todo] to [done] with fix description.
when_to_use: |
  当用户说「fix review」「修这个问题」「处理这条审查意见」「修复审查」时触发。
argument-hint: "<报告路径:行号 | 问题描述>"
---

# fix-review

修复代码审查报告中的问题，同步更新报告状态。

## Argument Parsing

`$ARGUMENTS` 支持两种输入形式：

| 形式 | 示例 | 解析方式 |
|------|------|---------|
| 报告路径+行号 | `docs/review/2026-04-26_full_review.md:69` | 读取指定行附近内容，定位 `### #N` 问题块 |
| 一句话描述 | `修复 tmux_send.sh 中变量未加引号的问题` | 在 `docs/review/` 下搜索关键词匹配的问题 |

## Execution Steps

### 1. Parse Arguments

判断 `$ARGUMENTS` 的类型：

- 匹配 `^.+\.md:\d+$` → 路径+行号模式
- 其他 → 描述文字模式

### 2. Locate Issue

#### 路径+行号模式

1. 读取指定报告文件，定位到指定行
2. 向上搜索找到 `### #N` 开头的问题块起始行
3. 向下读取到下一个 `### #` 或空行前，提取完整问题块

#### 描述文字模式

1. 扫描 `docs/review/` 下所有 `*.md` 报告文件
2. 提取所有状态为 `[todo]` 或 `[doing]` 的问题块
3. 从描述中提取关键词（文件名、问题特征等）
4. 匹配问题的标题、文件路径、问题描述字段
5. **匹配到 0 个** → 提示用户未找到，建议检查描述或使用路径+行号
6. **匹配到 1 个** → 直接进入评估
7. **匹配到多个** → 列出所有匹配项，让用户选择

### 3. Evaluate Issue

定位到问题后，不要直接按建议修复。先阅读报告中建议涉及的源文件上下文，独立评估：

1. 读取问题中 `**文件**` 字段指向的源文件，了解实际代码
2. 判断报告中 `**建议**` 是否合理：
   - 建议是否准确解决了 `**问题**` 中描述的根因？
   - 是否存在更简单或更好的修复方式？
   - 修复是否会引入新问题或影响其他功能？
3. 如果建议合理 → 沿用建议制定修复计划
4. 如果建议需要调整 → 说明调整理由，给出自己的修复方案

向用户展示评估结果：

```
问题评估：

报告: docs/review/2026-04-26_full_review.md
### #3 [shell] here-string 中变量未加引号

**文件**: `plugins/tmux/skills/tmux-send/scripts/tmux_send.sh:30`
**问题**: ${BODY} 来自外部文件或用户传入参数，内容不受控...
**建议**: 通过 printf '%s\n' "$BODY" 写入临时文件...

评估: {建议合理 / 建议需要调整，理由}

修复计划：
- {具体的修复步骤}

确认修复？
```

等待用户确认。用户可以：
- 确认 → 执行修复
- 提出修改意见 → 调整计划
- 取消 → 结束

### 4. Fix Code

根据评估确认的方案修复：

1. 从 `**文件**: \`path/to/file:line\`` 提取文件路径和行号
2. 读取源文件对应区域
3. 执行修改
4. 如果涉及多个文件，逐个修复

修复时记录简要的修复说明，用于后续更新报告。

### 5. Update Report

修复完成后，更新报告文档中的对应问题块：

**修改前：**
```markdown
**状态**: `[todo]`
```

**修改后：**
```markdown
**状态**: `[done]`
**修复**: {简要说明做了什么修改，一句话}
```

注意：
- 状态标记两边的反引号要保留：`` `[done]` ``
- 修复说明要简洁，描述实际做了什么

### 6. Update Statistics and Change History

#### 更新 issue_stats

如果报告 frontmatter 包含 `issue_stats`，将对应级别数量减 1：

```yaml
# 修复前
issue_stats:
  high: 9

# 修复后
issue_stats:
  high: 8
```

通过读取修复前的状态确定级别（问题在 `## CRITICAL`、`## HIGH`、`## MEDIUM` 还是 `## LOW` 区段下）。

#### 更新变更历史

在报告末尾的变更历史表格追加一行：

```markdown
| 2026-04-26 | 修复 #3: {一句话修复说明} |
```

### 7. Completion Notice

```
已修复并更新报告：
- 源文件: plugins/tmux/skills/tmux-send/scripts/tmux_send.sh
- 报告: docs/review/2026-04-26_full_review.md
- 状态: [todo] → [done]
```

## Edge Cases

- **问题已是 `[done]` 或 `[skip]` 状态** → 提示用户该问题已处理，确认是否要重新修复
- **源文件不存在或路径已变更** → 提示用户，建议手动定位
- **修复涉及范围超出单个问题** → 在修复计划中明确说明影响范围
- **多个问题指向同一文件** → 逐个修复，每次修复后更新对应问题状态
- **报告中建议过时** → 源文件可能已经过其他修改，以当前代码为准调整修复方案
