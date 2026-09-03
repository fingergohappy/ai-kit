---
name: sync-main
description: |
  把默认分支（main）的最新改动带进当前特性分支，让分支是在 main 现在的样子上被测试和 review 的。用 merge 还是 rebase 由仓库自己的惯例决定（检测，不假设），也可以用 `--merge` / `--rebase` 指定。冲突时停下交给人处理，不自作主张解决。
when_to_use: |
  当用户说「把 main 合进来」「同步一下 main」「pull main 的改动」「main 更新了，合到我这个分支」「sync main」时触发。
argument-hint: "[--rebase] [--merge]"
disable-model-invocation: false
---

# sync-main

把默认分支上的新提交带进当前特性分支，这样分支是在 `main` 现在的样子上被测试和 review 的。

> **结果**: 当前分支包含了 `origin/<默认分支>` 上的每一个提交，或者合并停在了只该由人来解决的冲突上。

这个 skill 对 merge 还是 rebase 没有立场 —— 它读仓库的。见 Phase 1。

## Phase 1 — 确定事实

绝不假设分支名。

```sh
git rev-parse --abbrev-ref HEAD                                   # 当前分支
git symbolic-ref --quiet refs/remotes/origin/HEAD                 # -> refs/remotes/origin/main
```

`origin/HEAD` 没设置时，按这个顺序回退：`main`、`master`，再没有就问。不要猜第三个名字。

以下情况停下来报告，什么都不要改：

- **当前就在默认分支上**。没有可以同步进去的地方；用户想要的是 `git pull`，那该由他明说。
- **工作树是脏的**（`git status --porcelain` 非空）。在未提交的改动上合并，会把它们混进冲突解决里，之后没有干净的退路。说清楚哪些文件脏了，让用户自己 commit 或 stash。
- **已经有合并 / rebase / cherry-pick 在进行中**（`git rev-parse --verify MERGE_HEAD` / `REBASE_HEAD` / `CHERRY_PICK_HEAD` 成功）。

### 这个仓库用哪种整合方式？

动手之前先按这个顺序定下来：

1. **用户说了** —— `$ARGUMENTS` 里的 `--rebase` / `--merge` 压过下面所有判断。
2. **历史说了** —— 这个仓库以前怎么同步的？
   ```sh
   git log --merges --oneline -30 | grep "Merge remote-tracking branch 'origin/<默认分支>'"
   ```
   有命中说明这个仓库是把默认分支 merge 进来的。没有命中，而且特性分支都是线性叠在 `<默认分支>` 上的，说明它 rebase。
3. **还是判断不了** —— 问。一句话，两个选项。不要自己悄悄选一个：在用 merge 的仓库里猜 rebase 会重写已发布的历史，在用 rebase 的仓库里猜 merge 会往一个有人刻意保持线性的历史里塞一个 merge commit。

**`git config pull.rebase` 回答的不是这个问题。** 它管的是 `git pull` 怎么整合**同名**分支的远程版本，不是默认分支怎么进到特性分支里。两者经常不一样：一个仓库完全可以 `pull.rebase=true`，同时仍然把 `origin/main` merge 进特性分支 —— 这个 skill 面对的仓库就是这样。把它当答案会判错。

## Phase 2 — 取回并比较

```sh
git fetch origin
git log --oneline HEAD..origin/<默认分支>     # 要进来的
git log --oneline origin/<默认分支>..HEAD     # 这个分支新增的
```

第一条为空说明分支已经是最新的 —— 说一句就停。这是成功的结果，不是失败，而且它应该不花什么代价。

合并前先报告要进来多少个提交。落后 200 个提交的分支和落后 3 个的，是完全不同的处境，用户应该在冲突冒出来之前就知道。

## Phase 3 — 整合

按 Phase 1 定下来的方式：

```sh
git merge origin/<默认分支>       # merge 型仓库
git rebase origin/<默认分支>      # rebase 型仓库 —— 见文末警告
```

**有冲突就停。** 不要解决，也不要替用户 `--abort`。报告：

- 冲突的路径（`git diff --name-only --diff-filter=U`）
- 每个路径一句话，说明两边各改了什么
- 两条出路：解决后继续（`git commit`，或 `git rebase --continue`），或者中止（`git merge --abort` / `git rebase --abort`）回到原地

没被要求就去解决别人的合并冲突，是工作悄悄消失的方式 —— 选错了一边，而 diff 看上去像是故意的。用户想要人帮忙解决，那是另一个请求（环境里有 `resolving-merge-conflicts` 时用它）。

## Phase 4 — 验证与报告

干净合并之后，**如果项目里明显有测试命令**就跑一次（`make test`、`npm test`、`go test ./...` —— 检测，不要编）。文本上合并成功的改动照样可能让构建挂掉，现在发现比 PR 开出去之后便宜得多。

报告：

1. 进来了多少提交，范围是什么
2. 用了哪种方式、依据是什么（用户指定 / 历史惯例），以及结果是 fast-forward、真的 merge commit、还是 rebase
3. 测试结果，或者说明没检测到测试命令
4. 分支**没有**被 push —— 这个 skill 不 push

## 当答案是 rebase

rebase 会重写这个分支的提交。不管它是来自 `--rebase` 还是 Phase 1 的检测：

- 分支要是已经 push 过，下次 push 需要 `--force-with-lease`（绝不用裸 `--force`）—— **这一点要写进报告**，别让用户到 push 的时候才发现
- 别人要是 checkout 了这个分支，他们的历史会悄无声息地分叉
- 冲突可能在每个被重放的提交上重复出现；`git rebase --abort` 是退路

绝不要因为历史「看起来更干净」就自己切到 rebase。在一个用 merge 的仓库里，被 rebase 过的分支才是异类 —— 而定下那个惯例的人不在这场对话里。
