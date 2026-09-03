---
name: ship-pr
description: |
  把当前分支从「活干完了」推到「PR 开好了」：先把 main 带进来（merge 还是 rebase 看仓库惯例），push，提 PR，然后问用户要不要自动接受 —— 要的话就守着 CI，绿了按仓库的 PR 合并方式合进 main，红了带着失败详情回来问。
when_to_use: |
  当用户说「提个 PR」「push 提 PR」「合并 main 然后提 PR」「开个 pull request」「ship 一下」「提 PR 然后 CI 过了就合」时触发。
argument-hint: "[--draft] [--no-merge]"
disable-model-invocation: false
---

# ship-pr

把当前特性分支从「活干完了」带到「PR 开好了」，如果用户点头，就一直守到 CI 出结果 —— 绿了合并，红了回来找他。

> **结果**: 一个开在默认分支上的 PR，要么已经合并，要么停在某个点名的失败检查上。

## Phase 1 — 同步

做 `sync-main` skill 做的全部事情：确定真实分支名，工作树脏或有合并进行中就拒绝，**判断这个仓库是 merge 还是 rebase**（它的 Phase 1 —— 两边都不要假设），fetch，整合 `origin/<默认分支>`，冲突就停。

**冲突直接结束这个 skill。** 不要把处在冲突中的分支 push 出去，也不要「开个 PR 看看 CI 怎么说」—— 照 `sync-main` 的做法报告冲突然后停下。

分支本来就是最新的，没关系，继续 Phase 2 —— 还是有东西要 ship。

如果 Phase 1 走的是 rebase 而分支之前 push 过，Phase 2 的 push 会需要 `--force-with-lease`。在走到那一步之前就要知道这件事。

## Phase 2 — Push

```sh
git push -u origin HEAD          # 这个分支第一次 push
git push                         # 之后
```

push 被拒绝（non-fast-forward）说明有别人动了这个分支。**停。** 不要 `--force`。报告分叉在哪，让用户决定。

如果 Phase 1 做的是 rebase，push 要用 `--force-with-lease`，绝不用裸 `--force` —— 而且只在「远程分叉是这次 rebase 造成的」这个前提下。一个你**没有** rebase 过的分支被拒 non-fast-forward，意味着是别人 push 了，也就是上面那种情况，force 会毁掉他的工作。

## Phase 3 — 提 PR

先看这个分支是不是已经有 PR 了：

```sh
gh pr view --json number,url,state,isDraft 2>/dev/null
```

已经有而且是 open 的，就**直接用它** —— Phase 2 的 push 已经更新了它。说明这一点，不要去建重复的。

没有就创建：

```sh
gh pr create --base <默认分支> --head <分支> --title "<标题>" --body "<正文>"
```

- **标题**: 从这个分支新增的提交里来（`git log --oneline origin/<默认分支>..HEAD`）。一个提交就用它的 subject；多个就写它们合起来做成了什么，用最近历史里在用的风格 —— 读 `git log --oneline -20` 然后对齐它（conventional 前缀、gitmoji、还是白话句子：每个仓库都不一样，不要强加一种）。
- **正文**: 有 `.github/pull_request_template.md` 就**把模板填完**，不要无视它，也不要原样贴一份空模板回去。没有模板就写：改了什么、为什么，然后附提交列表。两种情况都要加上下面那节运维事项。
- **语言**: 跟现有 PR 保持一致（`gh pr list --limit 10 --json title,body`）。不要把仓库换成另一种语言。
- 用户传了 `--draft` 就加上。

### 运维事项这一节不是可选的

一份只讲代码的 PR，会让部署它的人在部署那一刻才发现它需要一个没人设过的变量。**这些要从 diff 里查出来** —— 不要让用户凭记忆报，也绝不在没查的情况下写「无」。

```sh
git diff origin/<默认分支>...HEAD --stat
git diff origin/<默认分支>...HEAD --diff-filter=A --name-only    # 新增的文件：迁移和 seed 都落在这里
```

至少要逐条查这几类：

| 是什么 | 怎么找 | PR 里必须写清楚 |
|---|---|---|
| **新环境变量 / 配置项** | diff 里新出现的读取（`os.Getenv`、`process.env.`、`getenv`、`ENV[`），`.env.example` / `.env.sample` / chart values 的新行 | 变量名、有没有默认值、不设会怎样、生产建议值 |
| **数据库迁移** | 新增在项目迁移目录下的文件 | 文件 / 版本号、做什么、会不会锁表、`down` 安不安全 |
| **Seed / 回填 SQL** | 新增的含 `INSERT`/`UPDATE` 的 `.sql`，`scripts/`、`db/seeds/` 下的新脚本 | 什么时候跑（迁移之后？切流之前？）、是否幂等、跑第二遍会怎样 |
| **新依赖或外部服务** | `go.mod` / `package.json` / `requirements.txt` / `Cargo.toml` 的变化；新的 API 域名、队列、cron、bucket | 要开通什么、要哪些凭证、要放通哪些网络 |
| **功能开关** | 新的 flag 及其默认值 | 上线时开还是关、谁来翻、怎么回退 |
| **先后顺序** | 上面命中不止一条时 | 明确的执行序列 |

写成 checklist，让部署的人可以一条条勾：

```markdown
## 运维事项

- [ ] **环境变量** `PAYMENT_TIMEOUT_MS` —— 无默认值，不设服务起不来。生产建议 3000
- [ ] **迁移** `000075_add_refund_idx.up.sql` —— CONCURRENTLY 建索引，不锁表
- [ ] **Seed** `scripts/seed_refund_reasons.sql` —— 幂等；在迁移之后、开关打开之前跑
- [ ] **顺序**: migrate → 滚动容器 → seed → 打开 `refund_v2`
```

这个 diff 确实不需要任何运维动作，就明确写 **「运维事项：无」**。没有这一节读起来像「没人想过这件事」，明确写「无」读起来才是「查过了，不需要」。

如果这次改动的部署检查单已经在别处（sdd 的实施 spec 就有上线检查单那一节），从那里取条目，不要重新推导 —— 但仍然要写进 PR 正文，因为 reviewer 和部署的人读的是 PR，不是那个文件。

PR 一建出来就立刻报告 URL。那是交付物；后面的都是可选项。

## Phase 4 — 碰合并之前先问

用一句话问用户：**要自动接受这个 PR 吗？** 同一句话里说明它意味着什么 —— 守着 CI，绿了合并，红了回来找你。

没有明确的「要」就不要进 Phase 5。用户说不要（或者传了 `--no-merge`），到此为止：PR 开着，URL 报了，完事。

## Phase 5 — 守 CI

先看一眼再决定等不等：

```sh
gh pr checks <编号>
```

三种情况：

- **没有配置检查** —— 没什么可等的。告诉用户这个 PR 上没有 CI，问要不要照样合。不要把「没有检查」悄悄当成「绿了」。
- **全部已完成** —— 直接进 Phase 6。
- **还在跑** —— 等，但不要在前台等：

```sh
gh pr checks <编号> --watch --fail-fast     # 放到后台跑
```

CI 动辄跑得比一条前台命令能撑的时间还长。把 watch 放后台，让它结束时来唤醒你；不要坐在 `sleep` / 轮询循环里烧回合，也不要为了少等一会儿就替检查宣布一个它还没得出的结果。

等的时候要报告你在等，以及大致在等什么（`3 个检查在跑: ci / build / lint`）。

## Phase 6 — 绿了就合，红了就问

**绿**（`gh pr checks` 退出码 0 / 每个必需检查都通过）—— 按这个仓库合 PR 的方式来合。这跟 Phase 1 是两个问题，各有各的答案：

```sh
gh api repos/{owner}/{repo} --jq '{merge:.allow_merge_commit, squash:.allow_squash_merge, rebase:.allow_rebase_merge}'
```

1. **只允许一种** —— 用那种。其它几种是有人特意关掉的。
2. **允许好几种** —— 读历史：有 `Merge pull request #NN from …` 说明用 merge commit；`<默认分支>` 是线性的、每个 PR 落成正好一个提交，说明用 squash。
3. **还是判断不了** —— 问。在一个保留 merge commit 的仓库里 squash，会丢掉再也找不回来的作者粒度。

```sh
gh pr merge <编号> --merge|--squash|--rebase --delete-branch
git checkout <默认分支> && git pull
```

合并被拒绝 —— 分支保护、需要 review、base 过期 —— 原样报告拒绝原因然后停。那条拒绝是有人特意设的规则，不是需要绕过去的障碍。

**红**: 停下来，带着足够动手的信息回到用户面前：

- 哪个检查失败了，它的 URL
- 失败那一步的输出 —— 真正的错误行，不是「构建失败了」（`gh run view <run-id> --log-failed`，剪到有用的部分）
- 看起来是这个分支的改动引起的，还是 `<默认分支>` 上本来就有的
- PR 保持开着、未合并

然后问用户想怎么办：修了重新 push、照样合、还是先放着。

绝不在没被明确要求的情况下合并一个红的 PR，也绝不在不说明的情况下重跑 CI 指望换个答案。

## 报告

1. 同步结果 —— merge 还是 rebase（以及依据是什么）、整合进来几个提交，或者本来就是最新的
2. PR —— URL，新建的还是复用的
3. CI —— 跑了哪些检查、各自结论，或者用户没让守
4. 合并 —— 已合并并回到 `<默认分支>`，或者为什么没合
