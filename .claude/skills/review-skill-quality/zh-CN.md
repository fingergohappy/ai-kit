---
name: review-skill-quality
description: |
  从 skill 规范角度审查代码。检查 SKILL.md 是否符合 Claude Code 官方插件规范、frontmatter 格式、description 触发覆盖面、执行步骤可操作性、模板完整性。只审查 SKILL.md 文件。
  Review SKILL.md files for compliance with Claude Code official plugin specifications. Checks frontmatter format, description trigger coverage, execution step operability, and template completeness. Only reviews SKILL.md files.
when_to_use: |
  当用户说「skill 规范审查」「review skill 质量」「检查 SKILL.md」「skill 合规检查」时触发。
argument-hint: "[<文件路径或目录>]"
---

# review-skill-quality

从 skill 规范角度审查所有 SKILL.md 文件的质量。

官方规范参考（按权威性排序）：

- https://code.claude.com/docs/en/skills — 最权威，包含 Frontmatter reference 完整字段表
- https://code.claude.com/docs/en/plugins — 插件开发指南
- https://code.claude.com/docs/en/plugins-reference — 插件技术参考
- https://code.claude.com/docs/en/plugin-marketplaces#overview — 插件市场与分发规范
- https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/skill-development/SKILL.md — skill-development skill 的建议（非平台规范）

## Review Scope

关注所有 `SKILL.md` 文件。不审查 shell 脚本实现、不审查架构设计。

## Checklist

### Claude Code Official Spec Compliance [CRITICAL]

依据官方文档（code.claude.com/docs/en/skills），检查以下硬性要求：

- description 是否包含功能描述和触发场景。官方推荐格式为直述句：`"功能描述. Use when 触发场景1, 触发场景2, or when the user asks '触发短语'"`。注意：官方未强制要求第三人称格式，"This skill should be used when..." 仅为 skill-development skill 的建议
- description 是否包含具体的触发短语或触发场景，而非仅描述功能
- frontmatter 是否只使用官方支持的字段（完整列表）：`name`、`description`、`when_to_use`、`argument-hint`、`arguments`、`disable-model-invocation`、`user-invocable`、`allowed-tools`、`model`、`effort`、`context`、`agent`、`hooks`、`paths`、`shell`
- `when_to_use` 是官方支持字段，会追加到 description 后参与触发匹配，受 1,536 字符上限约束。可用于存放触发短语
- 资源目录是否遵循官方约定：`references/`（参考文档）、`examples/`（示例）、`scripts/`（脚本）
- 信息层级是否遵循渐进式披露原则：frontmatter（高层元数据，~100 词）→ SKILL.md 正文（详细指令，<500 行）→ references/（深度参考）

### Frontmatter Standards [HIGH]

- `name` 是否与目录名一致
- `description` 是否存在且非空
- `description` 是否包含触发条件（用户说什么话时应触发此 skill）
- `argument-hint` 是否存在（即使为空字符串）
- 可选字段 `model`、`context` 是否合理使用

### Description Trigger Coverage [HIGH]

- description 是否覆盖了用户可能的多种表述方式（中文、英文、口语化）
- 是否有明确的"不触发"边界（避免误触发）
- 触发条件是否与 skill 实际功能匹配

### Execution Steps [HIGH]

- 步骤是否有明确的顺序和编号
- 每个步骤是否可操作（AI 能直接执行，而非模糊的"注意 xxx"）
- 是否处理了 `$ARGUMENTS` 为空的情况
- 是否有明确的完成条件或输出说明

### Templates and References [MEDIUM]

- `references/` 下的模板是否被 SKILL.md 正确引用
- 模板中的占位符 `{xxx}` 是否在 SKILL.md 中说明了如何填充
- `scripts/` 下的脚本是否被 SKILL.md 正确调用
- 引用路径是否使用相对路径

### Consistency [MEDIUM]

- 同一插件内的 skills 是否遵循相同的格式约定
- 输出格式是否在 skill 之间保持一致
- 错误处理和边界情况的描述风格是否统一

### Maintainability [LOW]

- SKILL.md 长度是否合理（过长应拆分，过短可能缺少关键信息）
- 是否有过时的引用或不存在的文件路径
- 代码示例是否与实际脚本一致

## Output Format

审查结果按以下格式输出：

### [{严重级别}] {问题概述}

**文件**: `{SKILL.md 路径}`
**问题**: {具体描述}
**建议**: {修复方向}
