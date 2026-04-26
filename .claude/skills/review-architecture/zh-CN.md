---
name: review-architecture
description: |
  从架构角度审查代码。检查插件结构、skill 之间的依赖关系、目录组织、模块边界和职责划分。接收文件列表作为输入，输出该角度的审查发现。
  Review code from an architecture perspective. Checks plugin structure, skill dependencies, directory organization, module boundaries, and responsibility separation. Accepts file list as input, outputs review findings.
when_to_use: |
  当用户说「架构审查」「review 架构」「检查插件结构」「模块边界审查」时触发。
argument-hint: "[<文件路径或目录>]"
---

# review-architecture

从架构角度审查项目的插件结构和组织方式。

## Review Scope

关注项目整体结构：插件划分、skill 组织、目录层级、依赖方向。不审查具体代码实现细节。

## Checklist

### Plugin Boundaries [HIGH]

- 每个插件是否有明确的职责边界（单一关注点）
- 插件之间是否存在不合理的耦合（一个插件的 skill 直接引用另一个插件的内部文件）
- 跨插件调用是否通过 skill 名称而非文件路径

### Directory Organization [HIGH]

- 目录结构是否一致：每个插件是否遵循相同的 `skills/`、`agents/`、`references/`、`scripts/` 约定
- 文件放置是否合理：模板在 `references/`、脚本在 `scripts/`、skill 定义在 `SKILL.md`
- 是否有孤立文件（不属于任何插件或 skill 的文件）

### Dependency Direction [HIGH]

- skill 之间的依赖是否单向（无循环依赖）
- 公共能力（如 tmux-send）是否被合理复用而非重复实现
- 生成物（`.claude/skills/`）是否只依赖自身，不反向依赖插件源码

### Responsibility Separation [MEDIUM]

- 每个 skill 是否只做一件事
- 是否有 skill 承担了过多职责需要拆分
- agents 和 skills 的职责是否清晰区分

### Extensibility [MEDIUM]

- 新增插件或 skill 是否只需添加文件，不需修改已有代码
- 模板和脚本是否参数化，避免硬编码
- 命名约定是否一致且可预测

## Output Format

审查结果按以下格式输出：

### [{严重级别}] {问题概述}

**范围**: `{涉及的目录或文件}`
**问题**: {具体描述}
**建议**: {调整方向}
