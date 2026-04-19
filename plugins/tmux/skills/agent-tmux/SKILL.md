---
name: agent-tmux
model: haiku
description: |
  Start, restart, stop, or inspect long-running commands in a shared tmux session.
  Auto-isolates by project path and git branch to prevent conflicts.
  Use when user says "启动 dev server", "run in tmux", "后台运行", "长期运行服务".
argument-hint: <path> [-- <command>]
context: fork
---

# agent-tmux

在共享 tmux 会话中管理长期运行的服务，自动按项目目录和 git 分支隔离窗口。

## 脚本位置

`plugins/tmux/skills/agent-tmux/scripts/agent-tmux`

## Workflow

1. 解析用户意图，确定操作：`start` / `restart` / `stop` / `status`
2. 调用脚本执行，所有判断逻辑由脚本内部处理
3. 报告脚本输出结果给用户

## 命令约束

- 不要包装成 `sh -lc ...` 或 `bash -lc ...`
- 直接把原始命令放在 `--` 后面

## 查看输出

```bash
# 获取窗口名
WINDOW=$(./plugins/tmux/skills/agent-tmux/scripts/agent-tmux window --path ~/myproject)

# 查看窗口输出
tmux capture-pane -t agent-dev:$WINDOW -p
```
