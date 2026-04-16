---
name: rebase-to-root
description: |
  将 worktree 的 feature 分支 rebase 回 root (main) 分支。
  支持在 worktree 中直接调用（自动检测当前分支），也支持在 root 中调用（列出所有 worktree 供选择）。
  即使用户只是说"rebase"、"合入 main"、"merge 回去"、"rebase 到 root"，
  都应触发此 skill。
disable-model-invocation: true
argument-hint: [feature 名称，留空则自动检测]
---

# rebase-to-root

使用 git 原生命令，将 worktree 的 feature 分支 rebase 回 root (main) 分支。

## 前提条件

- 当前处于 git 仓库中（root 或 worktree 均可）
- 目标 worktree 的工作已提交（无未提交的变更）

## 执行步骤

### 1. 判断当前所处位置

```bash
git rev-parse --show-toplevel
git worktree list
```

对比当前路径与 `git worktree list` 第一行（主仓库 root 路径）：
- **在 worktree 中** → 直接获取当前分支名，跳到步骤 3
- **在 root 中** → 进入步骤 2，让用户选择目标 worktree

### 2. 选择目标 worktree（仅在 root 中时执行）

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

### 3. 检查 worktree 状态

```bash
git -C "<worktree-path>" status --porcelain
```

- 如果有输出 → **停止**，提示用户先到对应 worktree 提交或 stash 变更
- 无输出 → 继续

### 4. 执行 rebase

```bash
git -C "<project-root>" rebase "<feature-name>"
```

此命令将 feature 分支的提交 replay 到 root 分支（通常是 main）上。

### 5. 检查 rebase 结果

```bash
git -C "<project-root>" log --oneline -5
```

- 成功：root 分支已包含 feature 的所有提交
- 冲突：需要手动解决

### 6. 输出结果

- 成功：报告 rebase 完成，显示 root 分支最近提交
- 冲突：报告冲突文件列表，提示用户手动解决
- 失败：报告错误信息

## 冲突处理

如果 rebase 过程中发生冲突：

1. 列出冲突文件：
   ```bash
   git -C "<project-root>" diff --name-only --diff-filter=U
   ```
2. 报告冲突情况给用户，等待用户决定：
   - 手动解决冲突后执行 `git -C "<project-root>" rebase --continue`
   - 放弃 rebase：`git -C "<project-root>" rebase --abort`

## 生成规则

- 通过 `git worktree list` 判断当前位置和定位 root 路径
- 在 root 中时，必须让用户选择或确认目标 worktree
- rebase 前必须确认工作已提交，避免丢失变更
- rebase 失败时不自动 abort，让用户决定如何处理
- 如果仓库没有任何 worktree，直接报错退出
