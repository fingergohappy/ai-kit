---
name: wt-rebase
description: |
  使用 git-wt 插件，自动将当前 worktree 的 feature 分支 rebase 回 root (main) 分支。
  当用户在 worktree 中完成工作后，想把改动合入主分支时使用。
  即使用户只是说"rebase"、"合入 main"、"merge 回去"、"rebase 到 root"，
  都应触发此 skill。
disable-model-invocation: true
argument-hint: [feature 名称，留空则自动检测当前 worktree]
---

# wt-rebase

使用 git-wt 插件，将 worktree 的 feature 分支 rebase 回 root (main) 分支。

## 前提条件

- 已安装 git-wt 插件（https://github.com/fingergohappy/git-wt）
- 当前处于 git-wt 管理的项目中
- worktree 中的工作已提交（无未提交的变更）

## 执行步骤

1. **检测 feature 名称**:
   - 如果 `$ARGUMENTS` 提供了 feature 名称 → 使用该名称
   - 否则 → 自动检测当前所在的 worktree:
     ```bash
     git-wt status
     ```
     从输出中提取当前 worktree 名称。

2. **检查 worktree 状态**:
   ```bash
   git-wt list
   ```
   确认目标 feature 的状态：
   - 如果有未提交的变更 → **停止**，提示用户先提交
   - 如果状态为 unmerged → 提示存在未解决的冲突

3. **执行 rebase**:
   ```bash
   git-wt rebase <feature-name>
   ```
   此命令会在 project root 执行 `git rebase <feature>`，将 feature 的改动合入 root 分支。

4. **检查 rebase 结果**:
   ```bash
   git-wt status
   ```
   - 成功：root 分支已包含 feature 的所有提交
   - 冲突：需要手动解决冲突后继续

5. **输出结果**:
   - 成功：报告 rebase 完成，显示 root 分支当前状态
   - 冲突：报告冲突文件列表，提示用户手动解决
   - 失败：报告错误信息

## 冲突处理

如果 rebase 过程中发生冲突：

1. 列出冲突文件：
   ```bash
   git diff --name-only --diff-filter=U
   ```
2. 报告冲突情况给用户，等待用户决定：
   - 手动解决冲突后执行 `git rebase --continue`
   - 放弃 rebase：`git rebase --abort`

## 生成规则

- 自动检测 feature 名称时，优先使用 `git-wt status` 的输出
- rebase 前必须确认工作已提交，避免丢失变更
- rebase 失败时不自动 abort，让用户决定如何处理
- 如果不在 git-wt 管理的项目中，直接报错退出
