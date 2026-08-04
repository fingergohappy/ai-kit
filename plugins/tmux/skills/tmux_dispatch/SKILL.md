---
name: tmux_dispatch
description: Dispatch a task to an agent running in another tmux pane, addressed by pane id, stamping your own pane id so that agent reports back when it finishes. Use this whenever the user hands work off to another pane or another agent — "让 7 去做…", "把这个任务发给 %3", "dispatch this to pane 5", "叫 codex 那边处理这个", "这块你派出去" — including when they describe splitting work across panes without naming a tool. Fire-and-forget: it returns the moment the task lands and never waits or polls; the receiving agent notifies you through its tmux_reply skill.
when-to-use: when say 让 {number} 去做, 派给 {number}, 把任务发给 {number}, dispatch to pane, 让另一个 agent 处理, 叫那个 pane 跑一下
argument-hint: "[<pane_id>] [<task>]"
disable-model-invocation: false
---

# tmux_dispatch

Hand a task to an agent running in another tmux pane, then get out of the way.

The pairing with `tmux_reply` is the point. This skill only delivers; it does not watch the other pane, and it must not — polling `capture-pane` in a loop burns your turn on a screen only the other agent can advance. Instead every dispatched task carries a stamp with your pane id and an instruction to report back via `tmux_reply`. The other agent knocks when it's done; you stay free in the meantime.

## Resolve the pane id

The pane id is always explicit, taken from `$ARGUMENTS` (`%7 …`, `7 …`) or from what the user just said ("让 7 去修这个", "发给 %3"). A bare number means `%<number>`.

If there's no pane id anywhere, ask for it in plain prose — don't render a menu of panes. The user is looking at their own tmux layout and already knows which pane they mean, so a generated list is noise; and guessing is worse than asking, because a wrong guess drops a task into an unrelated session.

## Write the task before you send it

This is the part that decides whether the delegation succeeds, and it's where dispatching differs from sending a shell command. The receiving agent starts from nothing: it cannot see this conversation, the files you have open, your cwd, or the conclusion you just reached. Every reference that only makes sense *here* arrives *there* as a puzzle — and a confused agent doesn't stall, it guesses, then confidently does the wrong work.

So rewrite the request as a standalone brief:

- **Absolute paths only.** The other pane may sit in a different directory, or a different checkout of the same repo.
- **Expand every pointer.** "刚才那个函数", "上面那个报错", "the file we changed" → the real path, the real symbol, the actual error text inlined.
- **Say what "done" looks like** — the command that should pass, the behavior that should change. Without a finish line the other agent invents its own, usually more ambitious than you wanted.
- **Fence off what's fragile** if the work sits next to something you don't want touched.
- **Keep your uncertainty visible.** If you don't know whether the fix belongs in A or B, say so. Asserting a guess as fact is how a small task becomes a wrong refactor.

Same request, thin versus self-contained:

Thin — `把刚才那个 token 的 bug 修一下`

Self-contained:

```
修复 /Users/me/proj/src/auth.ts 中 verifyToken 的过期判断。
当前写的是 `if (payload.exp < Date.now() / 1000)`，但本服务签发的 exp 是毫秒时间戳，
结果所有 token 一律被判为已过期。改成毫秒比较，并补一个单测覆盖「刚签发的 token 仍有效」。
验收：cd /Users/me/proj && npm test -- auth 全绿。
不要改动 refreshToken 的逻辑，那部分另有 issue 在跟。
```

The second one is longer, and that length is the entire value being added.

## Script paths

All `scripts/` paths are relative to **the directory containing this SKILL.md file**. Resolve to an absolute path before running anything, since the plugin may be installed under a cache directory rather than the repo:

```bash
SKILL_DIR="<absolute path of the directory holding this SKILL.md>"
```

## Send it

```bash
# Short task, passed inline
bash "$SKILL_DIR/scripts/dispatch.sh" "<pane_id>" "<task>"

# Longer or multi-line task — write it to a file first, pass the path
bash "$SKILL_DIR/scripts/dispatch.sh" "<pane_id>" "/tmp/task.txt"

# Review-fix loop: gate-review may redispatch fixes on its own instead of stopping to ask
bash "$SKILL_DIR/scripts/dispatch.sh" "<pane_id>" "/tmp/task.txt" --loop
```

Pass `--loop` only when the user wants the review-fix cycle to run unattended — it is what licenses `gate-review` to send fixes back without checking in first. Leave it off by default, since a wrong automatic redispatch costs more than a question. The flag travels in the stamp and the receiving agent echoes it back in its reply, which is the only way it survives the round trip.

Prefer the file form as soon as the task has multiple lines, backticks, or quotes. It sidesteps shell quoting entirely, and a mangled brief is much harder to notice than a failed command.

Send only through this script — never `tmux send-keys` with the task text directly. The script handles what quietly breaks otherwise: bracketed paste so newlines don't submit the task in fragments, Enter as a separate event so TUI agents actually receive it, the sender stamp that creates the reply channel, validation that fails closed instead of pasting into whichever pane happens to be active, a guard against dispatching to your own pane, and buffer cleanup so the user's paste stack stays theirs.

## After sending

Report which pane you dispatched to, a one-line summary of what you handed off, and the receipt lines the script printed. Then stop and move on to other work.

Read the receipt before claiming success. If it shows the other agent mid-task, your dispatch is queued behind that work rather than started — say so, since "dispatched" and "being worked on" are different claims. If it shows a shell prompt or an unrelated program, the task probably landed in the wrong pane; surface that immediately instead of reporting a clean handoff.

When the reply eventually arrives in your pane, treat it as a report to relay to the user, not as a message needing an answer. Dispatch again only if there is genuinely new work.
