---
name: skill-i18n
description: |
  将 ai-kit 项目中的 skill 转换为双语版本：SKILL.md（英文）+ zh-CN.md（中文），并自动同步。支持单个或多个 skill 路径，自动检测源语言，已有 zh-CN.md 时执行增量同步。
  Bilingual skill management for ai-kit. Generates SKILL.md (English) + zh-CN.md (Chinese) pairs, auto-syncs zh-CN.md when SKILL.md changes. Supports single or multiple skill paths, auto-detects source language, and performs incremental sync.
when_to_use: |
  当用户说「翻译 skill」「skill 双语」「生成 zh-CN」「同步翻译」「更新翻译」时触发。skill-creator 完成创建/迭代、手动编辑了 SKILL.md 时也会自动触发。
argument-hint: "<skill路径> [skill路径2] ..."
---

# skill-i18n

将 ai-kit 项目中的 skill 转换为双语版本：SKILL.md（英文）+ zh-CN.md（中文）。

## Hard Constraints

- **增量同步和自动同步时，禁止修改 SKILL.md 原文档** — 只允许修改 zh-CN.md
- SKILL.md 只在全量生成阶段（目录下不存在 SKILL.md 或原始为中文需要翻译为英文）才会被写入或覆盖
- 如果用户仅说「同步翻译」「更新翻译」，则只更新 zh-CN.md，不触碰 SKILL.md
- **SKILL.md 和 zh-CN.md 的 `description` 字段必须始终保持中英双语** — 禁止写单语描述

## Argument Parsing

`$ARGUMENTS` 支持以下输入：

| 形式 | 示例 | 解析方式 |
|------|------|---------|
| 目录路径 | `plugins/code-kit/skills/fix-review` | 读取目录下的 SKILL.md |
| 文件路径 | `plugins/code-kit/skills/fix-review/SKILL.md` | 直接读取 |
| 多个路径 | `plugins/code-kit/skills/fix-review plugins/tmux/skills/tmux-send` | 逐个处理 |

如果传入目录，自动查找其中的 SKILL.md。

## Bilingual Format Specification

以 nvim-lsp-init 为参照模板，两个文件的格式如下：

### SKILL.md (English Version)

```yaml
---
name: <skill-name>
description: <中文触发词>。<English description of what the skill does>
argument-hint: "<参数说明>"
---
```

- frontmatter `description`：**必须中英双语** — 先写中文触发短语（当用户说「...」时触发），再写英文功能描述
- body 全部用英文
- 代码块、命令、路径保持原样

### zh-CN.md (Chinese Version)

```yaml
---
name: <skill-name>
description: <English description of what the skill does>
when_to_use: |
  当用户说「...」「...」时触发。
argument-hint: "<参数说明>"
---
```

- frontmatter `description`：**必须中英双语** — 先写中文功能描述，再写英文功能描述
- frontmatter `when_to_use`：中文触发场景
- body 全部用中文
- section 标题保持英文（如 `## Overview`、`### 1. Detect environment`）
- 代码块、命令、路径、变量名保持原样

## Execution Steps

### 1. Read Original Skill

1. 解析参数，定位每个 SKILL.md
2. 读取完整内容，解析 frontmatter 和 body

### 2. Detect Language

判断 body 的主要语言：

- 中文字符占比 > 30% → 原始语言为中文
- 否则 → 原始语言为英文

### 3. Generate Bilingual Versions

#### 原始为中文

1. **SKILL.md**（英文版）：
   - 翻译 body 为英文
   - 保留所有代码块、命令、路径、表格结构不变
   - frontmatter description：保留原始中文触发词 + 翻译英文功能描述
   - section 标题翻译为英文

2. **zh-CN.md**（中文版）：
   - body 保留原始中文内容
   - section 标题翻译为英文（与 SKILL.md 一致）
   - frontmatter 按 zh-CN.md 格式重组（description 英文、when_to_use 中文）

#### 原始为英文

1. **SKILL.md**（英文版）：
   - body 保留原始英文内容
   - frontmatter description：添加中文触发词 + 保留英文描述

2. **zh-CN.md**（中文版）：
   - 翻译 body 为中文
   - section 标题保持英文
   - 保留所有代码块、命令、路径、表格结构不变
   - frontmatter 按 zh-CN.md 格式重组

### 4. Translation Principles

- 技术术语保持原文：LSP、PATH、frontmatter、skill、plugin 等
- 代码块内容不翻译，代码注释翻译
- 表格结构保持一致，只翻译文字内容
- markdown 格式标记保持不变
- 如果原始 SKILL.md 已有 zh-CN.md，读取现有翻译作为参考，避免术语不一致

### 5. Write Files

将两个文件写入原始 skill 的同一目录：

```
plugins/code-kit/skills/fix-review/
├── SKILL.md      # 英文版（新生成或更新）
└── zh-CN.md      # 中文版（新生成或更新）
```

### 6. Output Confirmation

对每个处理的 skill 显示：

```
skill-i18n: fix-review
  原始语言: 中文
  SKILL.md: 已生成（英文）
  zh-CN.md: 已生成（中文）
```

多个 skill 时汇总：

```
完成 3 个 skill 的双语转换：
  - fix-review ✅
  - fix-review-all ✅
  - tmux-send ✅
```

## Auto Sync

当检测到以下操作涉及 SKILL.md 时，**必须**主动同步对应的 zh-CN.md：

| 触发场景 | 同步行为 |
|----------|---------|
| skill-creator 完成创建/迭代 | 自动更新该 skill 的 zh-CN.md |
| 手动编辑了 SKILL.md 内容 | 自动更新该 skill 的 zh-CN.md |
| 用户说「更新翻译」「同步翻译」 | 重新生成/更新 zh-CN.md |

### Sync Workflow

1. 检测目标 skill 目录下是否已有 zh-CN.md
2. 如果有 → 增量同步：对比 SKILL.md 和 zh-CN.md，更新变更的 section，保留未变更的翻译
3. 如果没有 → 全量生成：按上方「执行步骤」生成 zh-CN.md
4. 输出同步结果：`已同步 zh-CN.md (增量/全量)`

### Translation Quality Assurance

翻译文档（zh-CN.md）可通过 `skill-creator` skill 的评估流程来验证质量：

1. 将已生成的 SKILL.md（英文版）作为输入
2. 使用 `skill-creator` 创建 zh-CN.md，遵循本 skill 定义的双语格式规范
3. `skill-creator` 的迭代和评估流程同样适用于翻译文档的质量把控

这样翻译文档也能经过 skill-creator 的测试和评估循环，确保翻译质量。

## Edge Cases

- **已有双语文件** → 提示用户是否覆盖，默认覆盖
- **SKILL.md 中混合中英文** → 以占比高的语言为原始语言
- **frontmatter 中有非标准字段** → 原样保留，不删除
- **body 中有引用其他文件的相对路径** → 保持不变
- **参数为空** → 提示用法
