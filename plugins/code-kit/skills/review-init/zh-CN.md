---
name: review-init
description: |
  分析项目技术栈，生成定制的代码审查 skills。已有 review skills 时执行合并。
when_to_use: |
  当用户说「生成 review」「初始化 review」「review init」「生成代码审查」时触发。
argument-hint: ""
disable-model-invocation: false
---

# review-init

分析项目，生成定制化的 review skills 到 `.claude/skills/`。

## Execution Steps

### 1. 分析项目

收集以下信息：

- **语言和框架**：检查 `package.json`、`go.mod`、`Cargo.toml`、`pyproject.toml`、`requirements.txt`、`composer.json`、`Gemfile`、`pom.xml`、`build.gradle` 等
- **目录结构**：`find . -type f -name '*.ts' -o -name '*.tsx' -o -name '*.py' -o -name '*.go' -o -name '*.rs' -o -name '*.java' -o -name '*.php' -o -name '*.swift' | head -50` 了解主要语言分布
- **依赖特征**：ORM/数据库、认证库、API 框架、测试框架、前端框架等
- **已有规则**：检查 `CLAUDE.md`、`.claude/rules/`、`.eslintrc`、`.golangci.yml` 等
- **已有 review skills**：检查 `.claude/skills/review-*/SKILL.md` 是否已存在

### 2. 推荐 review 角度

根据分析结果，从以下候选角度中筛选适合当前项目的，每个附带一句话说明为什么推荐：

#### 通用角度（大多数项目适用）

| 角度 | 生成条件 | 说明 |
|------|---------|------|
| `security` | 始终推荐 | 硬编码密钥、注入、未验证输入、敏感数据泄露 |
| `error-handling` | 始终推荐 | 静默吞错、缺少边界处理、错误信息质量 |
| `code-quality` | 始终推荐 | 大函数、深嵌套、命名、重复代码、文件组织 |
| `architecture` | 始终推荐 | 模块边界、依赖方向、分层合理性、目录组织、循环依赖、职责划分 |

#### 语言/框架角度

| 角度 | 生成条件 | 说明 |
|------|---------|------|
| `type-safety` | TypeScript 项目 | any 滥用、类型断言、缺少类型定义 |
| `react-patterns` | React 项目 | hooks 规则、组件设计、状态管理、渲染性能 |
| `vue-patterns` | Vue 项目 | 组合式 API、响应式、组件通信 |
| `concurrency` | Go/Rust/Java 项目 | goroutine 泄漏、竞态条件、死锁、channel 使用 |
| `memory-safety` | Rust/C/C++ 项目 | 生命周期、所有权、unsafe 使用 |
| `python-idioms` | Python 项目 | 类型提示、异常处理、生成器使用 |

#### 领域角度

| 角度 | 生成条件 | 说明 |
|------|---------|------|
| `api-design` | 检测到 API 路由定义 | 接口一致性、输入验证、响应格式、版本控制 |
| `database` | 检测到 ORM/SQL 依赖 | N+1 查询、索引、事务、SQL 注入 |
| `accessibility` | 检测到前端 HTML/JSX | ARIA 属性、键盘导航、颜色对比、语义化 |
| `performance` | 检测到前端框架或高并发后端 | 包体积、懒加载、缓存、渲染优化 |
| `test-quality` | 检测到测试文件 | 测试覆盖率、测试隔离、mock 质量、边界用例 |
| `rules-compliance` | 检测到 CLAUDE.md 或项目规则 | 代码是否符合项目已定义的规则和约定 |

### 3. 用户确认

将推荐的角度列出，格式如下：

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

等待用户确认后再生成。

### 4. 生成 review skills

对用户确认的每个角度，生成 `.claude/skills/review-{角度}/SKILL.md`。

每个 review skill 的内容结构：

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

生成时根据项目实际情况定制检查项内容。例如：
- 如果项目用 Express，`api-design` 的检查项应包含 Express 中间件相关内容
- 如果项目用 Prisma，`database` 的检查项应包含 Prisma 特有的 N+1 模式
- 如果项目有 CLAUDE.md 规则，`rules-compliance` 的检查项应引用具体规则

### 5. 生成汇总 skills

读取本 SKILL.md 同目录下的模板生成两个汇总 skill：

- `.claude/skills/review-full/SKILL.md` — 基于 `references/review_full_template.md`
- `.claude/skills/review-diff/SKILL.md` — 基于 `references/review_diff_template.md`

生成时将模板中的 `{review_skill_list}` 替换为实际生成的 review skill 名称列表，格式如下：

```markdown
- `review-security` — 安全审查
- `review-architecture` — 架构审查
- `review-error-handling` — 错误处理审查
```

同时更新 review-full 和 review-diff 的 description，列出包含的审查角度。

### 6. 合并逻辑（重复执行时）

如果 `.claude/skills/` 下已有 `review-*` skills：

1. 列出已有的 review skills
2. 列出本次新推荐的角度
3. 标记哪些是新增、哪些已存在
4. 让用户决定：保留全部 / 删除某些 / 新增某些
5. 只生成/删除用户确认的部分，不动未提及的已有 skill

### 7. 完成提示

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
