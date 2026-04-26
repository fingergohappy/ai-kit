---
name: skill-i18n
description: |
  当用户说「翻译 skill」「skill 双语」「生成 zh-CN」「同步翻译」时触发。skill-creator 完成创建/迭代、手动编辑了 SKILL.md 时也会自动触发。支持单个或多个 skill 路径，自动检测源语言，已有 zh-CN.md 时执行增量同步。
  Bilingual skill management: generates SKILL.md (English) + zh-CN.md (Chinese) pairs, and auto-syncs zh-CN.md when SKILL.md changes. Auto-triggers after creating a new skill, editing an existing SKILL.md, or skill-creator workflow completion. Supports single or multiple skill paths, auto-detects source language, and performs incremental sync when zh-CN.md already exists.
argument-hint: "<skill path> [skill path 2] ..."
---

# skill-i18n

Convert skills in the ai-kit project to bilingual format: SKILL.md (English) + zh-CN.md (Chinese).

## Hard Constraints

- **During incremental sync and auto-sync, modifying the original SKILL.md is prohibited** — only zh-CN.md may be modified
- SKILL.md is only written or overwritten during the full generation phase (when SKILL.md doesn't exist in the directory or the original is Chinese and needs English translation)
- If the user only says "sync translation" or "update translation", only update zh-CN.md, do not touch SKILL.md
- **The `description` field in both SKILL.md and zh-CN.md must always be bilingual (Chinese + English)** — never write a monolingual description

## Argument Parsing

`$ARGUMENTS` supports the following inputs:

| Form | Example | How to Parse |
|------|---------|-------------|
| Directory path | `plugins/code-kit/skills/fix-review` | Read SKILL.md in the directory |
| File path | `plugins/code-kit/skills/fix-review/SKILL.md` | Read directly |
| Multiple paths | `plugins/code-kit/skills/fix-review plugins/tmux/skills/tmux-send` | Process each one |

If a directory is passed, automatically find the SKILL.md within it.

## Bilingual Format Specification

Use nvim-lsp-init as the reference template. The two file formats are:

### SKILL.md (English Version)

```yaml
---
name: <skill-name>
description: <Chinese trigger phrases>. <English description of what the skill does>
argument-hint: "<parameter description>"
---
```

- frontmatter `description`: **must be bilingual** — Chinese trigger phrases first (triggered when user says "..."), then English functional description
- Body entirely in English
- Code blocks, commands, paths kept as-is

### zh-CN.md (Chinese Version)

```yaml
---
name: <skill-name>
description: <Chinese description>. <English description of what the skill does>
when_to_use: |
  当用户说「...」「...」时触发。
argument-hint: "<parameter description>"
---
```

- frontmatter `description`: **must be bilingual** — Chinese functional description first, then English functional description
- frontmatter `when_to_use`: Chinese trigger scenarios
- Body entirely in Chinese
- Section headers kept in English (e.g., `## Overview`, `### 1. Detect environment`)
- Code blocks, commands, paths, variable names kept as-is

## Execution Steps

### 1. Read Original Skill

1. Parse arguments, locate each SKILL.md
2. Read complete content, parse frontmatter and body

### 2. Detect Language

Determine the primary language of the body:

- Chinese character ratio > 30% → original language is Chinese
- Otherwise → original language is English

### 3. Generate Bilingual Versions

#### Original is Chinese

1. **SKILL.md** (English version):
   - Translate body to English
   - Preserve all code blocks, commands, paths, table structures
   - frontmatter description: keep original Chinese trigger phrases + translate English functional description
   - Translate section headers to English

2. **zh-CN.md** (Chinese version):
   - Keep original Chinese body content
   - Translate section headers to English (matching SKILL.md)
   - Reorganize frontmatter per zh-CN.md format (bilingual description, when_to_use in Chinese)

#### Original is English

1. **SKILL.md** (English version):
   - Keep original English body content
   - frontmatter description: add Chinese trigger phrases + keep English description

2. **zh-CN.md** (Chinese version):
   - Translate body to Chinese
   - Keep section headers in English
   - Preserve all code blocks, commands, paths, table structures
   - Reorganize frontmatter per zh-CN.md format

### 4. Translation Principles

- Keep technical terms as-is: LSP, PATH, frontmatter, skill, plugin, etc.
- Don't translate code block content, do translate code comments
- Keep table structures consistent, only translate text content
- Keep markdown format markers unchanged
- If the original SKILL.md already has a zh-CN.md, read existing translation as reference to avoid terminology inconsistency

### 5. Write Files

Write both files to the same directory as the original skill:

```
plugins/code-kit/skills/fix-review/
├── SKILL.md      # English version (newly generated or updated)
└── zh-CN.md      # Chinese version (newly generated or updated)
```

### 6. Output Confirmation

For each processed skill, display:

```
skill-i18n: fix-review
  Original language: Chinese
  SKILL.md: Generated (English)
  zh-CN.md: Generated (Chinese)
```

For multiple skills, summarize:

```
Completed bilingual conversion for 3 skills:
  - fix-review ✅
  - fix-review-all ✅
  - tmux-send ✅
```

## Auto Sync

When the following operations involve SKILL.md, **must** proactively sync the corresponding zh-CN.md:

| Trigger Scenario | Sync Behavior |
|-----------------|---------------|
| skill-creator completes creation/iteration | Auto-update that skill's zh-CN.md |
| SKILL.md content manually edited | Auto-update that skill's zh-CN.md |
| User says "update translation" or "sync translation" | Regenerate/update zh-CN.md |

### Sync Workflow

1. Check if zh-CN.md already exists in the target skill directory
2. If yes → incremental sync: compare SKILL.md and zh-CN.md, update changed sections, preserve unchanged translations
3. If no → full generation: generate zh-CN.md per "Execution Steps" above
4. Output sync result: `Synced zh-CN.md (incremental/full)`

### Translation Quality Assurance

Translation documents (zh-CN.md) can be verified through the `skill-creator` skill's evaluation workflow:

1. Use the generated SKILL.md (English version) as input
2. Use `skill-creator` to create zh-CN.md, following the bilingual format specification defined in this skill
3. `skill-creator`'s iteration and evaluation workflow also applies to translation document quality control

This way translation documents also go through skill-creator's testing and evaluation loop, ensuring translation quality.

## Edge Cases

- **Existing bilingual files** → Prompt user whether to overwrite, default to overwrite
- **Mixed Chinese/English in SKILL.md** → Use the higher ratio language as original language
- **Non-standard fields in frontmatter** → Keep as-is, do not remove
- **Relative paths referencing other files in body** → Keep unchanged
- **Empty arguments** → Show usage instructions
