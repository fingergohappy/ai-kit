---
name: agent-tmux
description: Use when an agent needs to start, restart, or inspect a long-running project command in a shared tmux session using a project path and startup command.
---

# agent-tmux

当 agent 需要在共享 `tmux` 会话中启动或管理长期运行的服务时，给它两项输入即可：

- `path`：项目目录
- `启动命令`：例如 `npm run dev`、`python -m http.server 8000`

优先直接执行 skill 自带脚本 `scripts/agent-tmux`。

- 不要假设存在全局 `agent-tmux` 命令
- 不要绕过 `scripts/agent-tmux` 手工重写 tmux 管理逻辑
- 相对路径按当前 skill 目录解析；默认直接运行 `scripts/agent-tmux ...`

工具会自动按 `项目名_分支` 派生 window 名。

- window 不存在：创建 window 并启动命令
- window 已存在且前台已有非 shell 进程：视为已运行，直接返回窗口信息，不重启
- window 已存在但只有 shell 空闲：在该 window 里启动命令

## 何时使用

- 用户要求把 dev server、后台任务或长期运行命令放进 `tmux` 里
- 需要按项目目录和 git 分支自动隔离 window
- 需要后续通过 `tmux` 查看输出、重启或停止进程

## 快速开始

```bash
# 启动服务
scripts/agent-tmux start --path /path/to/project -- <命令...>

# 示例
scripts/agent-tmux start --path ~/myproject -- python -m http.server 8000

# 重启
scripts/agent-tmux restart --path /path/to/project -- <命令...>

# 停止
scripts/agent-tmux stop --path /path/to/project

# 查看状态
scripts/agent-tmux status --path /path/to/project

# 检查窗口是否存在（返回 exit code）
scripts/agent-tmux exists --path /path/to/project

# 获取窗口名
scripts/agent-tmux window --path /path/to/project
```

## 命令约束

- 不要把启动命令包装成 `sh -lc ...` 或 `bash -lc ...`
- 直接把原始命令放在 `--` 后面，让 tmux window 里的 shell 自己执行
- 需要重定向、管道或 `&&` 时，也直接传原始 shell 命令，例如 `atlas-run --http-port 2991 2>&1 | tee -a ./atlas-run.log`

## 辅助命令

| 命令 | 说明 | 输出 |
|------|------|------|
| `exists --path <path>` | 检查窗口是否存在 | exit code: 0=存在, 1=不存在 |
| `window --path <path>` | 获取窗口名 | `project_branch` |

```bash
# 使用示例
if scripts/agent-tmux exists --path ~/myproject; then
    echo "服务已运行"
else
    scripts/agent-tmux start --path ~/myproject -- npm run dev
fi

# 获取窗口名用于其他操作
WINDOW=$(scripts/agent-tmux window --path ~/myproject)
tmux capture-pane -t agent-dev:$WINDOW -p
```

## 命名规则

| 组件 | 值 |
|------|-----|
| **会话** | 固定：`agent-dev` |
| **窗口** | `<project>_<branch>`（从 path 的 git 信息派生） |

示例：`/home/user/jira-infraflow` 在 `feat/login` 分支上启动，窗口名为 `jira-infraflow_feat-login`。

## 启动行为

```
窗口存在？
  ↓
 否 → 创建新窗口并启动
 是 → window 前台有非 shell 进程？
        ↓
       是 → 返回 existing / RUNNING，不重启
       否 → 复用现有 window 启动命令
```

同一个 path 就是同一个应用，不存在窗口名冲突。

## 非 git 目录

路径不是 git 仓库时，窗口名为目录名（无分支后缀）。

## 查看输出

```bash
# 附加到共享会话
tmux attach -t agent-dev

# 查看特定窗口
tmux capture-pane -t agent-dev:<window> -p
```

## 行为说明

- **start**: 幂等启动。已运行时返回已有 window，不重启。
- **restart**: 先向现有 window 发送 `C-c`，再直接发送新命令，不重建 pane。
- **status**: `RUNNING` 表示 window 前台有非 shell 进程；`IDLE` 表示 window 存在但当前只有 shell。
- **stop**: 发送 `C-c` 信号，不保证进程一定停止
