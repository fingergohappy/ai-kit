---
name: agent-tmux
model: haiku
description: |
  Start, restart, stop, or inspect long-running commands in a shared tmux session.
  Auto-isolates by project path and git branch to prevent conflicts.
  在共享 tmux 会话中管理长期运行的服务，自动按项目目录和 git 分支隔离窗口。
  Use when user says "启动 dev server", "run in tmux", "后台运行", "长期运行服务".
argument-hint: <path> [--cmd <command>]
context: fork
---

# agent-tmux

Manage long-running services in a shared tmux session, automatically isolating windows by project directory and git branch.

## Script Location

`plugins/tmux/skills/agent-tmux/scripts/agent-tmux`

## Command Constraints

- Pass the raw command directly after `--cmd`. Do not wrap the input command with `sh -lc ...` or `bash -lc ...`.

## Workflow

1. Call `status` first to check the current running state.
2. Based on the state and user intent, decide the operation:
   - To start a new service: already running -> `restart`, not running -> `start`
   - To stop a service: `stop`
   - To check status: report the `status` output directly
3. Report the script output to the user.

