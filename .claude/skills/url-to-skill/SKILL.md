---
name: url-to-skill
description: |
  从 URL 自动生成 Claude Code skill 文件。用户提供一个链接，
  自动抓取内容并生成 SKILL.md 保存到 .claude/skills/ 目录。
  当用户说"转成 skill"、"从链接生成 skill"、"把这个变成 skill"时触发。
model: haiku
context: fork
argument-hint: <URL>
---

# URL to Skill

从用户提供的 URL 抓取内容，自动生成结构化的 skill 文件。

**输入**: `$ARGUMENTS`（URL）

---

## 执行步骤

### 1. 抓取内容

使用 `mcp__web_reader__webReader` 工具抓取 URL 内容：

- URL: `$ARGUMENTS`
- 格式: markdown
- 保留图片摘要: 开启

如果抓取失败，报告错误并停止。

### 2. 分析内容

分析抓取到的内容，提取以下信息：

- **主题**: 这篇内容讲什么？
- **适用场景**: 什么情况下应该使用这个 skill？
- **触发词**: 用户说什么话时应该触发？
- **核心知识**: 关键的规则、模式、步骤
- **代码示例**: 如果有代码，提取关键示例

### 3. 生成 skill 文件

根据分析结果，按以下模板生成 SKILL.md：

```markdown
---
name: <从内容提取的简短英文名，kebab-case>
description: |
  <1-2 句中文描述这个 skill 做什么>
  触发词：<3-5 个触发短语，用顿号分隔>
model: <根据复杂度选择：简单工具用 haiku，需要推理用 sonnet，深度分析用 opus>
context: subagent
---

# <Skill 名称>

<从内容提取的核心说明>

## <按内容结构组织的各个章节>

<保留原文中的关键规则和模式>

<保留有价值的代码示例>
```

### 4. 确定模型

根据内容复杂度自动选择模型：

| 内容类型 | 模型 |
|---------|------|
| 简单工具操作、格式化、模板 | haiku |
| 编码模式、最佳实践、架构指南 | sonnet |
| 深度分析、安全审查、复杂推理 | opus |

### 5. 保存文件

1. 从内容主题生成英文目录名（kebab-case）
2. 创建目录: `.claude/skills/<skill-name>/`
3. 写入文件: `.claude/skills/<skill-name>/SKILL.md`
4. 报告文件路径

### 6. 输出结果

报告：

- 生成的 skill 名称
- 文件路径
- 选择的模型及原因
- 内容摘要（一句话）

---

## 生成规则

- frontmatter 中的 description 用中文
- 正文内容保留原文语言（英文内容保持英文，中文内容保持中文）
- 代码示例保留原文
- 不要照搬全文，提取核心可操作的内容
- 确保生成的 skill 是可执行的指令，不是知识科普
- 如果原内容太长，按重要度裁剪，保留最可操作的部分
