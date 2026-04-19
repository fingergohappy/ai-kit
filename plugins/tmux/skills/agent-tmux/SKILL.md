---
name: agent-tmux
model: haiku
description: |
  Start, restart, stop, or inspect long-running commands in a shared tmux session.
  Auto-isolates by project path and git branch to prevent conflicts.
  Use when user says "启动 dev server", "run in tmux", "后台运行", "长期运行服务".
argument-hint: <path> [--cmd <command>]
context: fork
---

# agent-tmux

在共享 tmux 会话中管理长期运行的服务，自动按项目目录和 git 分支隔离窗口。

## 脚本位置

`plugins/tmux/skills/agent-tmux/scripts/agent-tmux`

## 命令约束

- `--cmd` 后面直接传原始命令,不要对输入的命令做任包装成 `sh -lc ...` 或 `bash -lc ...`

## Workflow

1. 先调用 `status` 检查当前运行状态
2. 根据状态和用户意图决定操作：
   - 要启动新服务：已运行 → `restart`，未运行 → `start`
   - 要停止服务：`stop`
   - 要查看状态：直接报告 `status` 输出
3. 报告脚本输出结果给用户

