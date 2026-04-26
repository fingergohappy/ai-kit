---
name: rebase-to-root
description: |
  将 worktree 的 feature 分支 rebase 回 root 仓库的当前分支。
  root 分支不一定是 main，可能是任意分支（如 dev、release 等）。
  支持在 worktree 中直接调用（自动检测当前分支），也支持在 root 中调用（列出所有 worktree 供选择）。
  即使用户只是说"rebase"、"合回去"、"merge 回去"、"rebase 到 root"，
  都应触发此 skill。
  Rebase a worktree's feature branch onto the root repository's current branch.
  The root branch is not necessarily main — it can be any branch (e.g. dev, release, etc.).
  Supports invocation from within a worktree (auto-detects current branch) or from the root (lists all worktrees for selection).
  Triggers even when the user simply says "rebase", "merge back", "rebase to root", etc.
argument-hint: [feature name, leave empty to auto-detect]
---

# rebase-to-root

Use native git commands to rebase a worktree's feature branch onto the root repository's current branch.

> **Note**: The root's current branch is not necessarily main — it could be dev, release, or any other branch.
> The rebase target is always whichever branch the root is checked out on, not a fixed main branch.

## Key Concepts

- **root**: The main repository directory (where `.git` resides). Can be located from either root or a worktree via the parent directory of `git rev-parse --git-common-dir`.
- **root branch**: The currently checked-out branch of the root repository, i.e. the target branch for the rebase.

## Prerequisites

- Currently inside a git repository (root or worktree)
- The target worktree has no uncommitted changes

## Execution Steps

### 1. Locate Root and Determine Current Position

```bash
# Locate the root directory (parent of the shared .git)
PROJECT_ROOT="$(dirname "$(git rev-parse --git-common-dir)")"

# Get the current working directory
CURRENT_TOPLEVEL="$(git rev-parse --show-toplevel)"
```

Determine:
- `$CURRENT_TOPLEVEL == $PROJECT_ROOT` → **In root** → proceed to step 2
- `$CURRENT_TOPLEVEL != $PROJECT_ROOT` → **In worktree** → get the current branch name, skip to step 3

### 2. Select Target Worktree (only when in root)

List all worktrees and their branches:

```bash
git worktree list
```

Format the output for user selection:

```
Available worktrees:
1. feature/login (branch: feature-login) - /path/to/worktree-login
2. feature/api (branch: feature-api) - /path/to/worktree-api
```

- If `$ARGUMENTS` provides a feature name → use it directly, no prompt needed
- Otherwise → ask the user which worktree to rebase
- If there is only one worktree → use it directly, no prompt needed

### 3. Confirm Root Branch and Check Worktree Status

Get the rebase target branch:

```bash
git -C "$PROJECT_ROOT" branch --show-current
```

Confirm with user: `Rebase <feature-name> onto root branch <root-branch>. Continue?`

Check worktree status:

```bash
git -C "<worktree-path>" status --porcelain
```

- If there is output → **STOP**, prompt the user to commit or stash changes in that worktree first
- No output → continue

### 4. Execute Rebase

```bash
git -C "$PROJECT_ROOT" rebase "<feature-name>"
```

This command replays the feature branch's commits onto the root's current branch.

### 5. Fast-Forward Worktree Branch

After a successful rebase, the root branch has advanced, but the worktree's feature branch still points to the old position. Fast-forward the worktree to the root's current branch:

```bash
git -C "<worktree-path>" merge --ff-only "<root-branch>"
```

This keeps the feature branch in sync with the root's current branch.

### 6. Verify Result

```bash
git -C "$PROJECT_ROOT" log --oneline -5
```

- Success: Both the root branch and feature branch include all commits
- Conflict: Requires manual resolution

### 7. Output Result

- Success: Report rebase completed, show recent root branch commits
- Conflict: Report conflicted file list, prompt user to resolve manually
- Failure: Report error message

## Conflict Handling

If conflicts occur during rebase:

1. List conflicted files:
   ```bash
   git -C "$PROJECT_ROOT" diff --name-only --diff-filter=U
   ```
2. Report the conflicts to the user and wait for their decision:
   - Resolve conflicts manually, then run `git -C "$PROJECT_ROOT" rebase --continue`
   - Abort the rebase: `git -C "$PROJECT_ROOT" rebase --abort`

## Generation Rules

- Locate root via `git rev-parse --git-common-dir` (more reliable than parsing the first line of `git worktree list`)
- When in root, the user must select or confirm the target worktree
- Before rebasing, confirm and display the root's current branch to avoid rebasing onto the wrong branch
- Before rebasing, verify all work is committed to prevent losing changes
- Do not auto-abort on rebase failure; let the user decide how to proceed
- If the repository has no worktrees at all, report an error and exit immediately
