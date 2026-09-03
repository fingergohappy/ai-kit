---
name: sdd
description: >-
  需求 (REQ) / 变更 (CR) / 实施 spec / review 工作流的共享底座与状态入口. 当用户问 "到哪一步了", "下一步做什么", "检查一下文档一致性 / 索引", "这个 CR 什么状态", 或提到 REQ-NNN / CR-NNN / docs/sdd 时使用; /draft /req /create-cr /implement-cr /review-cr /auto-cr 六个命令的模板, 脚本与约定都在这里, 那六个命令运行前也要读本文的约定部分.
---

# sdd: 需求 / 变更 / 实施 / review 的底座

六个命令共用这里的三样东西:

| 东西 | 位置 (相对本文件) | 用途 |
|---|---|---|
| 脚本 | `scripts/sdd.py` | 编号, 建文件, 状态与下一步, 校验, 索引 -- 确定性的活不让 AI 手做 |
| 模板 | `assets/templates/*.md` | REQ / CR (变更 `cr.md`, 立项 `cr-new.md`) / spec / review / draft / lessons, 注释里写着每节怎么写 |
| 参考 | `references/` | `conventions.md` **全部约定 (唯一来源, 项目里不放副本)**; `writing-guide.md` 怎么写条目; `review-lanes.md` 三次 review 各查什么; `tdd.md` 实施循环; `openspec-borrowings.md` 借鉴与取舍 |

## 直接调用 (`/sdd`)

1. 定位脚本: 本文件所在目录下的 `scripts/sdd.py`. 用 `python3` 跑, 只依赖标准库.
2. `python3 <此目录>/scripts/sdd.py status` -- 列出全部 REQ / CR, 每个 CR 的 review 状态和下一步命令.
   (`status CR-NNN --write` 另把这份表落进该 CR 工作目录的 `PROGRESS.md`, 给人随时翻.)
   带参数 `status CR-NNN` 出这个 CR 的**八关进度表**: 走过哪几关 (✓), 卡在哪 (→), 后面还剩什么 (·),
   每关后面跟的是文件里读出来的证据 (文件名 + frontmatter 状态 + 未处置发现数 + 已填 hash 的步数).
3. 用户要查一致性: `sdd.py validate` (有错退出码 1, 可挂 CI). 逐条解释输出, 错误先于警告.
4. 用户要更新索引: `sdd.py index`. INDEX.md 是生成物, 手改会被覆盖.
5. `docs/sdd` 不存在时: 先问是否初始化 (`sdd.py init` 会建目录, INDEX, 和 notcommit 的 .gitignore;
   不生成 README, 约定只在本 skill), 不要在用户没确认的情况下往仓库里加目录.

把 `status` 的 "下一步" 原样告诉用户 -- 它是由文件状态推出来的, 比记忆可靠.

**进度表里没有勾**. 每一关过没过是脚本读文件算的 (review 的 frontmatter `status` 与处置列,
spec §4 表里填没填提交 hash), 不是 agent 自述. 所以换个会话接手, 或者自动推进跑了半天回头看,
跑一次 `status CR-NNN` 就够 -- 不要凭上下文里的记忆判断做到哪了, 那是唯一会骗人的来源.
这与 "落点填提交 hash 不填勾" 是同一条约定: 进度表本身也不许有勾.

## 约定 (六个命令共同遵守)

完整版在 `references/conventions.md`. 最容易违反的几条:

- **REQ 只写结论**. 每条 FR / BR / AC 都能拿去验收. 推导, 复现, file:line, 否决的方案不进
  REQ 正文 -- 它们在 CR 与 review 里, REQ 的变更记录只指过去 (写 "CR-005 I-3" 这样的编号).
  反过来 review 的结论被接受后必须落成 REQ 条款, 只在 review 里写着的等于未采纳.
- **条目号不重排**. FR-5 改了内容仍叫 FR-5; 删除保留编号标 "已删除, 见 CR-NNN"; 新增续编.
  整套体系靠条目号互相引用, 重排一次全断.
- **CR 必须挂在具体条目上**. 变更 CR 的影响需求精确到 FR-x / BR-y / AC-z, 新增 FR 必带新增 AC;
  全新业务用立项 CR (`new-cr --new`), 挂在新建的 draft REQ 上, 交付范围通常是全文.
- **notcommit 不入库, 且跨文档引用不写它的路径**. 引用 review 写 `CR-NNN D-2`.
- **review 是软闸门**. 下一阶段发现上一阶段 review 缺失或未 fixed 时, 停下来说明; 只有
  用户明确说 "跳过" 才继续.
- **落点填提交 hash 不填勾**. 提交可验证, 勾是自述.
- **每推进一步就跑 `status CR-NNN --write`**: 贴进度表给用户, 同时落进工作目录的 `PROGRESS.md`
  (人随时翻, 不必开口问). 不要自己复述做到哪了 -- 自述和勾一样不可验证.
- **状态在 frontmatter 里**, 不在正文表格. 值含 `": "` 或以 `[{&*!|>%@` 开头必须加引号 (或用 `>-`),
  否则标准 YAML 解析器会读错; `summary` 一律 `>-`. `validate` 会扫这类值.

## 状态与流程

```
REQ:    draft -> implemented -> superseded | retired
CR:     to fix -> fixing -> fixed  (| rejected)
review: to fix -> fixing -> fixed
```

```
/draft -> /req -> /create-cr -> /review-cr docs -> /spec -> /review-cr spec
       -> /implement-cr (TDD 实施, 提交可跨步) -> /review-cr impl
       -> /implement-cr (落实 REQ, CR fixed) -> /review-cr distill (提炼进 lessons.md, 清理工作目录)
```

`/auto-cr CR-NNN` 是这条链从 `/create-cr` 之后到落实之前的无人值守版: 照同样的步骤走, 不逐步问用户,
三次 review 派给 tmux 里的 codex / pi 并行审, 业务歧义先按推荐做法执行并记成 REQ 第 10 节的 OQ,
到落实那步停下等用户确认 OQ.

只有 `/implement-cr` 会改项目代码 (`/auto-cr` 内含它, 所以也会), 其余都只读代码 (写文档不算).

全新业务与改已有业务走同一条链, 只有 `/create-cr` 那一步分形态 (立项 CR / 变更 CR).

`/implement-cr` 是 "做下一件事", 由状态决定做什么 (`sdd.py status CR-NNN` 的下一步).

## 跨工具

本 skill 与六个命令只用 SKILL.md 的 `name` / `description` 两个字段, 不依赖任何工具专属
变量; 作为 ai-kit 插件时 Claude Code 里是 `/sdd:sdd` `/sdd:draft` 等, 软链接安装时无前缀 (`/sdd`), Codex 里是 `$sdd`, pi 按其 skill 调用方式. 命令后面的
参数 (如 `CR-005`, `docs`) 从用户消息里取; 没给就按各命令 SKILL.md 里的规则推断或询问.
安装: `/plugin install sdd@ai-kit`; 或 `install.sh` 把八个目录链接进 `.claude/skills/`, `.agents/skills/`, `.pi/skills/`.
