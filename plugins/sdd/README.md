# sdd skills: 需求 / 变更 / 实施 / review 工作流

八个 skill, 一个底座 (`sdd`) 加七个命令. 只有 `implement-cr` 与含它的 `auto-cr` 会改项目代码, 其余都只读代码. 只用 SKILL.md 的 `name` / `description`, 脚本只依赖
Python 3 标准库, Claude Code / Codex / pi 都能用.

| skill | 做什么 | 产出 | 改代码? |
|---|---|---|---|
| `sdd` | 底座: 模板, 脚本, 约定; `/sdd` 看状态与下一步 | INDEX.md | 否 |
| `draft` | 只读侦察 + 思考伙伴, 想清楚再立 CR | `notcommit/<slug>/draft/*.md` | 否 |
| `req` | 把现行业务逻辑写成 REQ (先收集旧的) | `req/REQ-NNN-<slug>.md` | 否 |
| `create-cr` | 立一次工作单元: 变更 CR (按条目号写 delta) 或立项 CR (全新业务) | `cr/CR-NNN-<slug>.md` + 工作目录 | 否 |
| `spec` | 写实施 spec: 侦察 (file:line) -> 改动总览 / 分步 / 测试 / 上线 | `notcommit/CR-NNN-*/spec.md` | 否 |
| `implement-cr` | 做下一件事: 处理发现 / TDD 分步实施 / 落实 REQ | 提交, REQ 更新 | **是** |
| `review-cr` | 三次 review: docs / spec / impl, 及复核; `distill` 模式把教训提炼进错题本并清理工作目录 | `reviews/0N-<stage>.md`, `lessons.md` | 否 |
| `auto-cr` | 无人值守推进一个已立的 CR 到落实前: review 派给 tmux 里的 codex / pi 并行审, 业务歧义记成 OQ 往下走 | 提交, reviews, REQ 第 10 节的 OQ | **是** |

## 安装

作为 ai-kit 插件 (Claude Code / Codex):

```
/plugin marketplace add fingergohappy/ai-kit
/plugin install sdd@ai-kit
```

装好后命令带插件前缀: `/sdd:sdd` `/sdd:draft` `/sdd:req` `/sdd:create-cr` `/sdd:implement-cr` `/sdd:review-cr` `/sdd:auto-cr`
(Codex 为 `$sdd` 等). 参数写在命令后面 (`/sdd:review-cr CR-005 docs`).

pi 或不走插件系统的工具: 用软链接装进项目:

```bash
./install.sh /path/to/project          # 软链接到 .claude/skills .agents/skills .pi/skills (命令无前缀: /draft)
./install.sh --copy /path/to/project   # 拷贝 (要随仓库提交时)
```

首次使用: `python3 skills/sdd/scripts/sdd.py init --root /path/to/project/docs/sdd` (只建目录与 INDEX).

## 文档头部

状态写在 YAML frontmatter 里 (不是正文表格), 任何工具都能读:

```yaml
---
id: CR-004
kind: change          # change 变更 | charter 全新业务立项
status: fixed         # to fix | fixing | fixed | rejected
created: 2026-08-27
affects:
  - REQ-006 (FR-8, BR-19, AC-8)
summary: >-
  一句话, 进 INDEX
---
```

值里含 `": "` 或以 `[{&*!|>%@` 开头必须加引号或用 `>-`, 否则标准 YAML 解析器会读成嵌套映射;
`sdd.py validate` 会扫出这类值. 脚本自带一个受限子集的解析器, 不依赖 PyYAML.

## 项目里长什么样

```
docs/sdd/
├── INDEX.md (生成; 约定不复制进项目, 只在 skill 的 references/conventions.md)
├── lessons.md                   错题本: 从已 fixed 的 review 提炼的模式 (入库)
├── req/REQ-NNN-<slug>.md        当前功能的结论 (入库)
├── cr/CR-NNN-<slug>.md          工作单元 (入库): 变更 CR 或立项 CR   to fix -> fixing -> fixed
└── notcommit/                   不入库
    └── CR-NNN-<slug>/{draft/, spec.md, reviews/01-docs.md 02-spec.md 03-impl.md}
                                  CR fixed 并提炼后整个删除 (sdd.py prune)
```

## 流程

```
/draft -> /req -> /create-cr -> /review-cr docs -> /spec -> /review-cr spec
       -> /implement-cr (TDD 实施, 每步一提交) -> /review-cr impl -> /implement-cr (落实, CR fixed)
       -> /review-cr distill (提炼教训进 lessons.md, 清理工作目录)
```

`sdd.py status CR-NNN` 随时告诉你下一步. `sdd.py validate` 可挂 CI.

## 目录

```
plugins/sdd/
├── .claude-plugin/ .codex-plugin/   插件清单
├── install.sh                      软链接安装 (pi 等)
├── skills/sdd/
│   ├── SKILL.md
│   ├── scripts/sdd.py                 init / status / new-* / validate / index / lessons / prune
│   ├── assets/templates/              req cr cr-new spec review draft lessons (注释 = 写法)
│   └── references/                    conventions (唯一约定来源) writing-guide review-lanes tdd openspec-borrowings
├── skills/draft/SKILL.md
├── skills/req/SKILL.md
├── skills/create-cr/SKILL.md
├── skills/spec/SKILL.md
├── skills/implement-cr/SKILL.md
├── skills/review-cr/SKILL.md
└── skills/auto-cr/SKILL.md     无人值守编排 (tmux-dispatch + agent-crew)
                             (每个 skill 另有 agents/openai.yaml)
```

`auto-cr` 的并行 review 依赖 ai-kit 的 `tmux` 插件 (`tmux-dispatch` 送 brief, `agent-crew` 起窗口)
与 PATH 上的 `codex` / `pi`. 缺任何一样它降级成串行自审, 流程照走, 不会中止.

从 OpenSpec 借了什么、没借什么: `sdd/references/openspec-borrowings.md`.
