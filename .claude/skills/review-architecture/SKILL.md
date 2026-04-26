---
name: review-architecture
description: |
  从架构角度审查代码。检查插件结构、skill 依赖关系、目录组织、模块边界和职责划分。
  Review code from an architecture perspective. Checks plugin structure, skill dependencies, directory organization, module boundaries, and responsibility separation.
  接收文件列表作为输入，输出该角度的审查发现。
argument-hint: "[<file path or directory>]"
---

# review-architecture

Review the project's plugin structure and organization from an architecture perspective.

## Review Scope

Focus on overall project structure: plugin boundaries, skill organization, directory hierarchy, dependency direction. Does not review specific code implementation details.

## Checklist

### Plugin Boundaries [HIGH]

- Does each plugin have a clear responsibility boundary (single concern)
- Are there unreasonable couplings between plugins (one plugin's skill directly referencing another plugin's internal files)
- Do cross-plugin calls use skill names rather than file paths

### Directory Organization [HIGH]

- Is the directory structure consistent: does each plugin follow the same `skills/`, `agents/`, `references/`, `scripts/` conventions
- Is file placement reasonable: templates in `references/`, scripts in `scripts/`, skill definitions in `SKILL.md`
- Are there orphan files (files not belonging to any plugin or skill)

### Dependency Direction [HIGH]

- Are skill dependencies unidirectional (no circular dependencies)
- Are shared capabilities (e.g., tmux-send) properly reused rather than duplicated
- Do generated artifacts (`.claude/skills/`) only depend on themselves, not reverse-depend on plugin source code

### Responsibility Separation [MEDIUM]

- Does each skill do only one thing
- Are there skills with too many responsibilities that need splitting
- Is the responsibility distinction between agents and skills clear

### Extensibility [MEDIUM]

- Can new plugins or skills be added by just adding files, without modifying existing code
- Are templates and scripts parameterized, avoiding hardcoding
- Are naming conventions consistent and predictable

## Output Format

Review results follow this format:

### [{Severity Level}] {Issue Summary}

**Scope**: `{involved directories or files}`
**Issue**: {specific description}
**Suggestion**: {adjustment direction}
