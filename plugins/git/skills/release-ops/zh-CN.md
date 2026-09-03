---
name: release-ops
description: |
  发布前把这次要人工做的运维动作收齐：从上次发布以来合并的每个 PR 里取运维事项，再拿 diff 反过来核一遍，找出代码需要、却没有任何 PR 声明的那些（包括直接推到 main 的提交）。产出一份每条都能追溯到 PR 或 commit 的检查单。
when_to_use: |
  当用户说「准备发布」「拉一下这次发布的 PR」「发布检查单」「这次要动哪些运维」「上次发布到现在有什么」「release notes 里的运维部分」时触发。
argument-hint: "[<上次发布的 tag>] [--to <ref>]"
disable-model-invocation: false
---

# release-ops

切版本之前，把部署这次发布需要人工执行的动作收齐 —— 新环境变量、迁移、seed SQL、要开通的服务、功能开关 —— 再拿 diff 核一遍，确认该做的事没有从清单里漏掉。

> **结果**: 一份检查单，每条都能追溯到某个 PR 或某个 commit，外加一节「diff 需要但没人声明」的东西。

重点不是汇总。把各个 PR 已经写好的东西拼起来是容易的那一半，也是抓不到任何问题的那一半。**价值在 Phase 4 的反向核对** —— 找出代码需要、而没有 PR 提过的东西。

## Phase 1 — 定锚点，并确认这个锚点能用

```sh
git fetch origin --tags
git tag -l 'v*' --sort=-v:refname | grep -v -- '-rc' | head -1     # 上次稳定发布
```

用户给了参数就用参数。否则取最新的**稳定** tag —— 排除 `-rc` / `-alpha` / `-beta`。RC tag 是很差的锚点：它们常常打在后来被 rebase 或 squash 掉的分支上，于是 tag 落在主线之外，尽管它的内容已经上线了。

然后确认这个锚点在你要发布的那条线上：

```sh
git merge-base --is-ancestor <tag> <to-ref>      # --to, 默认 origin/main
```

**结果是 false 就停下来说明。** 这个 tag 指向的提交不在当前分支的历史里 —— 可能是某次发布切在了没合回来的分支上，也可能是分支被 rebase 过。在这种状态下，下面所有「已发布 / 本次待发」的判断都不可靠。报告这一点，把查到的东西照样列出来，然后请用户给一个真正的起点 commit。不要靠猜绕过去：猜错要么让清单少一条运维动作，要么把已经执行过的又列一遍 —— 而重跑一个非幂等的 seed 本身就是一次事故。

## Phase 2 — 收集 PR

**不要**从 merge commit 的消息里 grep PR 号。那样会漏掉所有 squash 和 rebase 合并的 PR（它们根本不产生 `Merge pull request` 这一行），而那些 PR 的运维事项会静默消失。

问 GitHub 要清单，再让 git 判断哪些已经发布过：

```sh
gh pr list --state merged --base <默认分支> --limit 100 \
  --json number,title,body,mergedAt,mergeCommit,author
```

每个 PR 的 `mergeCommit.oid` 是真正落到 base 分支上的那个提交 —— merge、squash、rebase 三种方式都有：

```sh
git merge-base --is-ancestor <oid> <tag>    # 0 = 已发布, 非 0 = 属于本次发布
```

两个必须处理对的点：

- **返回条数等于 `--limit` 说明被截断了。** 调大或者翻页；被悄悄截掉的是这次发布里最早的那批 PR，而那批恰恰是大家已经忘掉的。
- **PR 编号顺序不等于合并顺序。** 一个几个月前开的长命分支可以昨天才合，带着一个很小的编号。绝不要按编号范围过滤，也绝不要因为编号小就当成「老黄历」—— 只认 `--is-ancestor` 的判断。

## Phase 3 — 取出已声明的运维事项

从每个属于本次发布的 PR 正文里，取那节运维事项（`ship-pr` 写的那节）。每一条都带上 PR 号 —— 读的人会想点进去看。

在那个约定出现之前合的 PR 没有这一节。标成**「未声明」**，不要标成「无」—— Phase 4 就是用来兜住它们的。

## Phase 4 — 反向核对：diff 需要什么，而没人说过？

这是真正能抓到问题的部分。对整个发布区间跑一遍同样的检测，再减去 Phase 3 里已经声明过的。

```sh
git diff <tag>..<to-ref> --stat
git diff <tag>..<to-ref> --diff-filter=A --name-only     # 新增的文件
git log  <tag>..<to-ref> --oneline
```

| 信号 | 怎么找 |
|---|---|
| 新环境变量 / 配置项 | diff 里新出现的 `os.Getenv` / `process.env.` / `getenv` / `ENV[` 读取；`.env.example`、chart values、配置 schema 的新行 |
| 迁移 | 新增在项目迁移目录下的文件 —— 改名和版本号撞车也要看，不只是新增 |
| Seed / 回填 SQL | 新增的含 `INSERT`/`UPDATE` 的 `.sql`；`scripts/`、`db/seeds/` 下的新脚本 |
| 新依赖或外部服务 | `go.mod` / `package.json` / `requirements.txt` / `Cargo.toml` 的变化；新的 API 域名、队列、cron、bucket |
| 功能开关 | 新的 flag 及其默认值 |

diff 需要、但没有任何 PR 声明过的，单独成一节。它有两个来源：

- **直接推到默认分支的提交**，它们不属于任何 PR。在管理员可以绕过分支保护的仓库里这不是边角情况 —— 用 `git log <tag>..<to-ref> --no-merges` 找那些没有 PR 出处的提交。
- **正文早于这个约定的 PR**，或者作者漏写了那一节。

这些条目按 commit SHA 归属，不按 PR，这样读的人仍然查得到是谁、为什么。

## Phase 5 — 出检查单

按**必须执行的顺序**排，不是按发现的顺序。迁移排在读新列的代码之前；seed 排在迁移之后；开关放最后。

```markdown
# Release <下个版本> — 运维检查单
自 v1.3.3 (2026-09-01) 起 · 7 个 PR · 12 个直推提交

## PR 里已声明
- [ ] **迁移** `000085_screening_waiver.up.sql` —— 由 000074 撞车改名而来；确认没有环境跑过旧号 (#43)
- [ ] **环境变量** `PAYMENT_TIMEOUT_MS` —— 无默认值，不设服务起不来；生产 3000 (#45)

## 未声明 —— 从 diff 里查出来的
- [ ] **迁移** `000086_address_lookup.up.sql` —— 直推，无 PR (7f5867ff)

## 顺序
1. migrate  2. 滚动容器  3. seed  4. 打开开关

## 待确认
- #44「Ib 139」—— 正文没有运维那一节，而 diff 动了 `internal/ledger`，找作者确认
```

这份输出的规矩：

- **每条都要写明出处** —— PR 号或 commit SHA。追溯不到出处的条目，没人会信。
- **「未声明」不等于「无」** —— 两节分开。前者说明 PR 作者查过了；后者说明是机器查出来的。
- **清单为空也要明说** —— 「本次发布无运维动作，已对 diff 核过」。少一节读起来像「没看」。
- 不要因为某条看起来「应该已经做过了」就悄悄划掉。Phase 1 如果警告过锚点有问题，就在那些条目上逐条注明「可能已随上次发布执行」。

## 不归这个 skill 管

- 打 tag、构建、promote —— 它只产出清单
- 判断这次发布能不能发
- 替作者补写 PR 里缺的运维章节（说它缺，让作者自己补）
