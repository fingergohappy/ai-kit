---
name: review-skill-quality
description: |
  从 skill 规范角度审查代码。检查 SKILL.md 是否符合 Claude Code 官方插件规范、frontmatter 格式、description 触发覆盖面、执行步骤可操作性、模板完整性。
  Review SKILL.md files for compliance with Claude Code official plugin specifications. Checks frontmatter format, description trigger coverage, execution step operability, and template completeness.
  接收文件列表作为输入，只审查 SKILL.md 文件，输出该角度的审查发现。
argument-hint: "[<file path or directory>]"
---

# review-skill-quality

Review all SKILL.md files from a skill specification quality perspective.

Official spec references (ordered by authority):

- https://code.claude.com/docs/en/skills — Most authoritative, includes complete Frontmatter reference field table
- https://code.claude.com/docs/en/plugins — Plugin development guide
- https://code.claude.com/docs/en/plugins-reference — Plugin technical reference
- https://code.claude.com/docs/en/plugin-marketplaces#overview — Plugin marketplace and distribution specs
- https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/skill-development/SKILL.md — skill-development skill suggestions (not platform spec)

## Review Scope

Focus on all `SKILL.md` files. Does not review shell script implementations or architecture design.

## Checklist

### Claude Code Official Spec Compliance [CRITICAL]

Based on official docs (code.claude.com/docs/en/skills), check these hard requirements:

- Does description include functional description and trigger scenarios. The official recommended format is a direct statement: `"Functional description. Use when trigger scenario 1, trigger scenario 2, or when the user asks 'trigger phrase'"`. Note: the official spec does not mandate third-person format; "This skill should be used when..." is only a suggestion from the skill-development skill
- Does description include specific trigger phrases or trigger scenarios, not just functional description
- Does frontmatter only use officially supported fields (complete list): `name`, `description`, `when_to_use`, `argument-hint`, `arguments`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `model`, `effort`, `context`, `agent`, `hooks`, `paths`, `shell`
- `when_to_use` is an officially supported field that appends to description for trigger matching, subject to 1,536 character limit. Can be used for trigger phrases
- Do resource directories follow official conventions: `references/` (reference docs), `examples/` (examples), `scripts/` (scripts)
- Does information layering follow progressive disclosure: frontmatter (high-level metadata, ~100 words) → SKILL.md body (detailed instructions, <500 lines) → references/ (deep reference)

### Frontmatter Standards [HIGH]

- Does `name` match the directory name
- Does `description` exist and is non-empty
- Does `description` include trigger conditions (what the user says to trigger this skill)
- Does `argument-hint` exist (even if empty string)
- Are optional fields `model`, `context` used reasonably

### Description Trigger Coverage [HIGH]

- Does description cover multiple ways users might express the intent (Chinese, English, colloquial)
- Is there a clear "do not trigger" boundary (to avoid false triggers)
- Do trigger conditions match the skill's actual functionality

### Execution Steps [HIGH]

- Do steps have clear ordering and numbering
- Is each step actionable (AI can directly execute, not vague "watch out for xxx")
- Does it handle the case when `$ARGUMENTS` is empty
- Is there a clear completion condition or output description

### Templates and References [MEDIUM]

- Are templates under `references/` correctly referenced by SKILL.md
- Are template placeholders `{xxx}` explained in SKILL.md for how to fill
- Are scripts under `scripts/` correctly called by SKILL.md
- Do reference paths use relative paths

### Consistency [MEDIUM]

- Do skills within the same plugin follow the same format conventions
- Is the output format consistent across skills
- Are error handling and edge case description styles unified

### Maintainability [LOW]

- Is SKILL.md length reasonable (too long should be split, too short may lack critical info)
- Are there outdated references or non-existent file paths
- Do code examples match actual scripts

## Output Format

Review results follow this format:

### [{Severity Level}] {Issue Summary}

**File**: `{SKILL.md path}`
**Issue**: {specific description}
**Suggestion**: {fix direction}
