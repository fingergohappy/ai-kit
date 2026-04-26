---
name: rebase-to-root
description: |
  将 worktree 的功能分支 rebase 回根仓库的当前分支。支持从 worktree 内或根仓库调用。
when_to_use: |
  当用户说「rebase」「合回去」「merge 回去」「rebase 到 root」时触发。
argument-hint: "[feature 名称，留空则自动检测]"
disable-model-invocation: false
---

# rebase-to-root

使用 git 原生命令，将 worktree 的 feature 分支 rebase 回 root 仓库的当前分支。

> **注意**：root 的当前分支不一定是 main，可能是 dev、release 等任意分支。
> rebase 的目标始终是 root 所在的分支，不是固定的 main。

## Core Concepts

- **root**：主仓库目录（`.git` 所在目录）。无论当前在 root 还是 worktree，都可通过 `git rev-parse --git-common-dir` 的父目录定位。
- **root 分支**：root 仓库当前 checkout 的分支，即 rebase 的目标分支。

## Prerequisites

- 当前处于 git 仓库中（root 或 worktree 均可）
- 目标 worktree 的工作已提交（无未提交的变更）

## Execution Steps

### 1. Locate Root

```bash
# 定位 root 目录（所有 worktree 共享的 .git 的父目录）
PROJECT_ROOT="$(dirname "$(git rev-parse --git-common-dir)")"

# 获取当前所在目录
CURRENT_TOPLEVEL="$(git rev-parse --show-toplevel)"
```

判断：
- `$CURRENT_TOPLEVEL == $PROJECT_ROOT` → **在 root 中** → 进入步骤 2
- `$CURRENT_TOPLEVEL != $PROJECT_ROOT` → **在 worktree 中** → 获取当前分支名，跳到步骤 3

### 2. Select Target Worktree

列出所有 worktree 及其分支：

```bash
git worktree list
```

格式化输出供用户选择：

```
可用 worktree:
1. feature/login (分支: feature-login) - /path/to/worktree-login
2. feature/api (分支: feature-api) - /path/to/worktree-api
```

- 如果 `$ARGUMENTS` 提供了 feature 名称 → 直接使用，无需询问
- 否则 → 询问用户选择哪个 worktree 进行 rebase
- 如果只有一个 worktree → 直接使用，无需询问

### 3. Confirm Root Branch

获取 rebase 目标分支：

```bash
git -C "$PROJECT_ROOT" branch --show-current
```

向用户确认：`将 rebase <feature-name> 到 root 分支 <root-branch>，是否继续？`

检查 worktree 状态：

```bash
git -C "<worktree-path>" status --porcelain
```

- 如果有输出 → **停止**，提示用户先到对应 worktree 提交或 stash 变更
- 无输出 → 继续

### 4. Execute Rebase

```bash
git -C "$PROJECT_ROOT" rebase "<feature-name>"
```

此命令将 feature 分支的提交 replay 到 root 当前分支上。

### 5. Forward Worktree Branch

rebase 成功后，root 分支已前进，但 worktree 的 feature 分支仍指向旧位置。需要将 worktree fast-forward 到 root 当前分支：

```bash
git -C "<worktree-path>" merge --ff-only "<root-branch>"
```

这样 feature 分支就与 root 当前分支保持同步。

### 6. Check Results

```bash
git -C "$PROJECT_ROOT" log --oneline -5
```

- 成功：root 分支和 feature 分支都已包含所有提交
- 冲突：需要手动解决

### 7. Output Results

- 成功：报告 rebase 完成，显示 root 分支最近提交
- 冲突：报告冲突文件列表，提示用户手动解决
- 失败：报告错误信息

## Conflict Resolution

如果 rebase 过程中发生冲突：

1. 列出冲突文件：
   ```bash
   git -C "$PROJECT_ROOT" diff --name-only --diff-filter=U
   ```
2. 报告冲突情况给用户，等待用户决定：
   - 手动解决冲突后执行 `git -C "$PROJECT_ROOT" rebase --continue`
   - 放弃 rebase：`git -C "$PROJECT_ROOT" rebase --abort`

## Generation Rules

- 通过 `git rev-parse --git-common-dir` 定位 root（比 `git worktree list` 第一行更可靠）
- 在 root 中时，必须让用户选择或确认目标 worktree
- rebase 前确认 root 当前分支并向用户展示，避免 rebase 到错误的分支
- rebase 前必须确认工作已提交，避免丢失变更
- rebase 失败时不自动 abort，让用户决定如何处理
- 如果仓库没有任何 worktree，直接报错退出
