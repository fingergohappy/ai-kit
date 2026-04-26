---
name: url-to-skill
description: |
  从 URL 自动生成 Claude Code skill 文件。用户提供一个链接，自动抓取内容并生成 SKILL.md 保存到 .claude/skills/ 目录。
  Auto-generate Claude Code skill files from a URL. Fetches web content and generates a structured SKILL.md saved to .claude/skills/ directory.
  当用户说"转成 skill"、"从链接生成 skill"、"把这个变成 skill"时触发。
model: haiku
context: fork
argument-hint: <URL>
---

# URL to Skill

Fetch content from a user-provided URL and auto-generate a structured skill file.

**Input**: `$ARGUMENTS` (URL)

---

## Execution Steps

### 1. Fetch Content

Use the `mcp__web_reader__webReader` tool to fetch URL content:

- URL: `$ARGUMENTS`
- Format: markdown
- Include image summary: enabled

If fetch fails, report error and stop.

### 2. Analyze Content

Analyze the fetched content and extract the following:

- **Topic**: What is this content about?
- **Use cases**: When should this skill be used?
- **Trigger phrases**: What should the user say to trigger it?
- **Core knowledge**: Key rules, patterns, steps
- **Code examples**: If there's code, extract key examples

### 3. Generate Skill File

Based on the analysis, generate SKILL.md using this template:

```markdown
---
name: <short English name extracted from content, kebab-case>
description: |
  <1-2 Chinese sentences describing what this skill does>
  Trigger phrases: <3-5 trigger phrases separated by commas>
model: <choose based on complexity: simple tools use haiku, reasoning needed use sonnet, deep analysis use opus>
context: subagent
---

# <Skill Name>

<Core instructions extracted from content>

## <Sections organized by content structure>

<Preserve key rules and patterns from original>

<Preserve valuable code examples>
```

### 4. Determine Model

Auto-select model based on content complexity:

| Content Type | Model |
|-------------|-------|
| Simple tool operations, formatting, templates | haiku |
| Coding patterns, best practices, architecture guides | sonnet |
| Deep analysis, security review, complex reasoning | opus |

### 5. Save File

1. Generate English directory name from content topic (kebab-case)
2. Create directory: `.claude/skills/<skill-name>/`
3. Write file: `.claude/skills/<skill-name>/SKILL.md`
4. Report file path

### 6. Output Result

Report:

- Generated skill name
- File path
- Selected model and reason
- Content summary (one sentence)

---

## Generation Rules

- Use Chinese for frontmatter description
- Keep body content in the original language (English content stays English, Chinese content stays Chinese)
- Keep code examples in original language
- Don't copy the entire text; extract core actionable content
- Ensure the generated skill contains executable instructions, not knowledge exposition
- If the original content is too long, trim by importance, keeping the most actionable parts
