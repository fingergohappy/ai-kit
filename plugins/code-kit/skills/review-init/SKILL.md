---
name: review-init
description: |
  分析当前项目的技术栈、依赖和代码结构，生成定制化的 code review skills。
  当用户说「生成 review」、「初始化 review」、「review init」、「生成代码审查」时触发。
  如果项目已有 review skills，走合并逻辑：展示已有 + 新建议，让用户决定增删。
  Analyze the current project's tech stack, dependencies, and code structure to generate customized code review skills.
  Triggered when the user says "generate review", "initialize review", "review init", or "generate code review".
  If the project already has review skills, use merge logic: show existing + new suggestions, and let the user decide what to add or remove.
argument-hint: ""
---

# review-init

Analyze the project and generate customized review skills into `.claude/skills/`.

## Execution Steps

### 1. Analyze the Project

Collect the following information:

- **Languages and frameworks**: Check `package.json`, `go.mod`, `Cargo.toml`, `pyproject.toml`, `requirements.txt`, `composer.json`, `Gemfile`, `pom.xml`, `build.gradle`, etc.
- **Directory structure**: `find . -type f -name '*.ts' -o -name '*.tsx' -o -name '*.py' -o -name '*.go' -o -name '*.rs' -o -name '*.java' -o -name '*.php' -o -name '*.swift' | head -50` to understand the primary language distribution
- **Dependency characteristics**: ORM/database, authentication libraries, API frameworks, testing frameworks, frontend frameworks, etc.
- **Existing rules**: Check `CLAUDE.md`, `.claude/rules/`, `.eslintrc`, `.golangci.yml`, etc.
- **Existing review skills**: Check whether `.claude/skills/review-*/SKILL.md` already exists

### 2. Recommend Review Perspectives

Based on the analysis results, filter suitable perspectives from the candidates below for the current project. Include a one-sentence explanation for each recommendation.

#### General Perspectives (Applicable to Most Projects)

| Perspective | Generation Condition | Description |
|-------------|---------------------|-------------|
| `security` | Always recommended | Hardcoded secrets, injection, unvalidated input, sensitive data leakage |
| `error-handling` | Always recommended | Silently swallowing errors, missing boundary handling, error message quality |
| `code-quality` | Always recommended | Large functions, deep nesting, naming, duplicate code, file organization |
| `architecture` | Always recommended | Module boundaries, dependency direction, layering soundness, directory organization, circular dependencies, responsibility separation |

#### Language/Framework Perspectives

| Perspective | Generation Condition | Description |
|-------------|---------------------|-------------|
| `type-safety` | TypeScript projects | `any` overuse, type assertions, missing type definitions |
| `react-patterns` | React projects | Hooks rules, component design, state management, render performance |
| `vue-patterns` | Vue projects | Composition API, reactivity, component communication |
| `concurrency` | Go/Rust/Java projects | Goroutine leaks, race conditions, deadlocks, channel usage |
| `memory-safety` | Rust/C/C++ projects | Lifetimes, ownership, unsafe usage |
| `python-idioms` | Python projects | Type hints, exception handling, generator usage |

#### Domain Perspectives

| Perspective | Generation Condition | Description |
|-------------|---------------------|-------------|
| `api-design` | API route definitions detected | Interface consistency, input validation, response format, versioning |
| `database` | ORM/SQL dependencies detected | N+1 queries, indexing, transactions, SQL injection |
| `accessibility` | Frontend HTML/JSX detected | ARIA attributes, keyboard navigation, color contrast, semantic markup |
| `performance` | Frontend framework or high-concurrency backend detected | Bundle size, lazy loading, caching, render optimization |
| `test-quality` | Test files detected | Test coverage, test isolation, mock quality, edge cases |
| `rules-compliance` | CLAUDE.md or project rules detected | Whether the code conforms to the project's defined rules and conventions |

### 3. User Confirmation

List the recommended perspectives in the following format:

```
根据项目分析，建议生成以下 review 角度：

✅ 推荐：
  1. security — 项目有用户认证和 API 接口
  2. error-handling — 通用必备
  3. code-quality — 通用必备
  4. type-safety — TypeScript 项目
  5. api-design — 检测到 Express 路由

你可以：
- 去掉不需要的（输入编号）
- 补充自定义角度（描述审查关注点，我来生成）
- 直接确认开始生成
```

Wait for user confirmation before generating.

### 4. Generate Review Skills

For each confirmed perspective, generate `.claude/skills/review-{perspective}/SKILL.md`.

The content structure of each review skill:

```markdown
---
name: review-{角度}
description: |
  从{角度名称}角度审查代码。
  接收文件列表作为输入，输出该角度的审查发现。
argument-hint: "[<文件路径或目录>]"
---

# review-{角度}

## 审查范围

{该角度关注什么，不关注什么}

## 审查清单

{具体的检查项，每项包含：}
- 检查什么
- 怎么判断是问题
- 严重级别（CRITICAL/HIGH/MEDIUM/LOW）

## 输出格式

审查结果按以下格式输出：

### [{严重级别}] {问题概述}

**文件**: `{文件路径}:{行号}`
**问题**: {具体描述}
**建议**: {修复方向}
**状态**: `[todo]`

状态值：`[todo]` 待修复 | `[doing]` 修复中 | `[done]` 已修复 | `[skip]` 跳过
```

Customize the checklist content based on the project's actual situation during generation. For example:

- If the project uses Express, `api-design` checklists should include Express middleware-related content
- If the project uses Prisma, `database` checklists should include Prisma-specific N+1 patterns
- If the project has CLAUDE.md rules, `rules-compliance` checklists should reference specific rules

### 5. Generate Summary Skills

Read the templates in the same directory as this SKILL.md to generate two summary skills:

- `.claude/skills/review-full/SKILL.md` — based on `references/review_full_template.md`
- `.claude/skills/review-diff/SKILL.md` — based on `references/review_diff_template.md`

During generation, replace `{review_skill_list}` in the templates with the actual list of generated review skill names, in the following format:

```markdown
- `review-security` — 安全审查
- `review-architecture` — 架构审查
- `review-error-handling` — 错误处理审查
```

Also update the descriptions of review-full and review-diff to list the included review perspectives.

### 6. Merge Logic (When Re-run)

If `review-*` skills already exist under `.claude/skills/`:

1. List the existing review skills
2. List the newly recommended perspectives
3. Mark which are new and which already exist
4. Let the user decide: keep all / remove some / add some
5. Only generate/delete the parts the user confirmed; do not touch existing skills that were not mentioned

### 7. Completion Message

```
已生成 {N} 个 review skills：
  - review-security
  - review-error-handling
  - ...
  - review-full（全量审查）
  - review-diff（增量审查）

使用方式：
  /review-full    — 全量审查整个项目
  /review-diff    — 审查 git diff 变更
  /review-{角度}  — 单独运行某个角度的审查
```
