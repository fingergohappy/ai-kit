---
name: rebase-to-root
description: |
  自动将当前 worktree 的 feature 分支 rebase 回 root (main) 分支。
  当用户在 worktree 中完成工作后，想把改动合入主分支时使用。
  即使用户只是说"rebase"、"合入 main"、"merge 回去"、"rebase 到 root"，
  都应触发此 skill。
disable-model-invocation: true
argument-hint: [feature 名称，留空则自动检测当前 worktree]
---

# rebase-to-root

使用 git 原生命令，将 worktree 的 feature 分支 rebase 回 root (main) 分支。

## 前提条件

- 当前处于 git worktree 中
- worktree 中的工作已提交（无未提交的变更）

## 执行步骤

1. **定位 project root**:
   ```bash
   git -C "$(git rev-parse --show-toplevel)" config --get remote.origin.url 2>/dev/null || echo "not-a-repo"
   ```
   通过 worktree 定位到主仓库 root：
   ```bash
   git worktree list
   ```
   第一行（`working tree` 不带括号的）即为 project root 路径。

2. **检测 feature 分支名称**:
   - 如果 `$ARGUMENTS` 提供了 feature 名称 → 使用该名称
   - 否则 → 自动检测当前 worktree 所在分支：
     ```bash
     git -C "$(pwd)" branch --show-current
     ```

3. **检查 worktree 状态**:
   ```bash
   git -C "$(pwd)" status --porcelain
   ```
   - 如果有输出 → **停止**，提示用户先提交或 stash 变更
   - 无输出 → 继续

4. **执行 rebase**:
   在 project root 目录下执行：
   ```bash
   git -C "<project-root>" rebase "<feature-name>"
   ```
   此命令将 feature 分支的提交 replay 到 root 分支（通常是 main）上。

5. **检查 rebase 结果**:
   ```bash
   git -C "<project-root>" log --oneline -5
   ```
   - 成功：root 分支已包含 feature 的所有提交
   - 冲突：需要手动解决

6. **输出结果**:
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

- 通过 `git worktree list` 定位 project root（第一行的路径）
- rebase 前必须确认工作已提交，避免丢失变更
- rebase 失败时不自动 abort，让用户决定如何处理
- 如果不在 git worktree 中，直接报错退出
