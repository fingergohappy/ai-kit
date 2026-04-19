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

## 核心行为

- **窗口命名**: `<项目名>_<分支名>`（从 git 信息派生）
- **会话**: 固定使用 `agent-dev` session
- **幂等性**: 已运行的服务不会重复启动
- **脚本位置**: `plugins/tmux/skills/agent-tmux/scripts/agent-tmux`

## Workflow

1. 解析 `path` 参数（必需）和启动命令
2. 检查 git 仓库获取分支名，非 git 目录只使用目录名
3. 执行对应命令：
   - `start`: 幂等启动，已运行时返回现有窗口
   - `restart`: 发送 C-c 中断后重启
   - `stop`: 发送 C-c 信号
   - `status`: 检查运行状态（RUNNING/IDLE/NONE）
   - `exists`: 检查窗口是否存在（exit code）
   - `window`: 获取窗口名

## 快速示例

```bash
# 启动服务
./plugins/tmux/skills/agent-tmux/scripts/agent-tmux start --path ~/myproject -- npm run dev

# 重启服务
./plugins/tmux/skills/agent-tmux/scripts/agent-tmux restart --path ~/myproject -- python -m http.server 8000

# 检查状态
./plugins/tmux/skills/agent-tmux/scripts/agent-tmux status --path ~/myproject
# 输出: RUNNING 或 IDLE

# 检查是否存在（用于脚本判断）
if ./plugins/tmux/skills/agent-tmux/scripts/agent-tmux exists --path ~/myproject; then
    echo "服务已运行"
fi

# 获取窗口名
WINDOW=$(./plugins/tmux/skills/agent-tmux/scripts/agent-tmux window --path ~/myproject)
tmux capture-pane -t agent-dev:$WINDOW -p
```

## 启动逻辑

```
检查窗口是否存在？
  ↓
 否 → 创建新窗口并启动命令
 是 → 检查前台进程？
        ↓
       有进程 → 返回 existing/RUNNING（不重启）
       只有 shell → 直接启动命令
```

## 命令约束

- 不要包装成 `sh -lc ...` 或 `bash -lc ...`
- 直接把原始命令放在 `--` 后面
- 需要重定向、管道时直接传原始命令：
  ```bash
  ./plugins/tmux/skills/agent-tmux/scripts/agent-tmux start --path ~/project -- atlas-run --http-port 2991 2>&1 | tee -a ./atlas-run.log
  ```

## 命名规则

| 组件 | 值 | 示例 |
|------|-----|------|
| 会话 | 固定 `agent-dev` | `agent-dev` |
| 窗口 | `<项目名>_<分支名>` | `jira-infraflow_feat-login` |

非 git 目录：窗口名 = 目录名（无分支后缀）

## 状态说明

| 状态 | 含义 |
|------|------|
| `RUNNING` | 窗口前台有非 shell 进程在运行 |
| `IDLE` | 窗口存在但只有 shell 空闲 |
| `NONE` | 窗口不存在 |

## 查看输出

```bash
# 附加到共享会话
tmux attach -t agent-dev

# 查看特定窗口输出
tmux capture-pane -t agent-dev:<window> -p

# 列出所有窗口
tmux list-windows -t agent-dev
```
