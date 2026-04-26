---
name: tmux-send
description: |
  向 tmux 面板发送内容并自动执行。当用户说「发到面板」「在 tmux 运行」或指定面板编号时触发。
when_to_use: |
  当用户说「发给 7」「发到 %3」「给那边发一下」「发送到 tmux」「在那个面板运行」时触发。只指定了数字目标时，内容从对话上下文中自动提取。
argument-hint: "[<pane_id>] [<内容>]"
model: haiku
disable-model-invocation: false
---

# tmux-send

将内容发送到指定的 tmux pane，并自动按下 Enter。

## Workflow

优先检查 `$ARGUMENTS`，否则从自然语言中解析：

1. `$ARGUMENTS` 同时包含 pane_id 和内容（如 `%7 ls` 或 `7 ls`）→ 直接发送
2. `$ARGUMENTS` 只有 pane_id（无后续内容）→ 询问用户要发送的内容
3. `$ARGUMENTS` 为空 → 从对话上下文中提取 pane_id 和内容；用户可能说「把刚才那段代码发到 7」、「将你修改的内容发送到 %3」等，此时内容来自对话中已有的代码或文本
4. pane_id 仍未知 → 询问用户（纯文本，不显示选项列表）

## Script Paths

所有 `scripts/` 路径相对于**本 SKILL.md 文件所在目录**。执行前必须先解析为绝对路径：

```bash
SKILL_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"  # 或直接使用本文件所在目录的绝对路径
```

后续命令中用 `"$SKILL_DIR/scripts/xxx.sh"` 替代裸 `scripts/xxx.sh`。

## Send Content

**必须且只能**通过脚本发送内容。严禁直接调用 `tmux send-keys` 或任何其他 tmux 命令——无论内容多简单，都不允许绕过脚本。这样做是为了保证行为一致、避免转义问题，以及便于统一维护。

```bash
# 方式 1：直接传内容
bash "$SKILL_DIR/scripts/tmux_send.sh" "<pane_id>" "<内容>"

# 方式 2：传文件路径（适合长内容）
bash "$SKILL_DIR/scripts/tmux_send.sh" "<pane_id>" "/tmp/message.txt"
```
