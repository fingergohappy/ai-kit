---
name: tmux-dispatch
description: |
  Dispatch a task to an agent (Claude Code, Codex, ...) running in another tmux pane by writing the brief to a document under docs/tmux-channel/ and sending that pane only the document's path, stamped with your own pane id so the agent reports back into the same document. Use this whenever the user wants work handed off to another pane or another agent — "让 7 去做…", "把这个任务发给 %3", "dispatch this to pane 5", "让另一个 agent 跑一下", "叫 codex 那边处理这个", "这块你派出去" — and also when they describe splitting work across panes or agents without naming any tool. Delivery is fire-and-forget: it returns the moment the pointer lands and never waits or polls; the receiving agent appends its report to the document and knocks back through its tmux-reply skill with a one-line DONE: / BLOCKED: / QUESTION: status.
argument-hint: "[<pane_id>] [<task>]"
---

# tmux-dispatch

Hand a task to an agent in another tmux pane by leaving it a document, then get out of the way.

Two rules shape everything below.

**The document is the message.** The brief goes into a file under `docs/tmux-channel/`; what travels through tmux is its absolute path and nothing else. Pasted task text exists only in the other pane's scrollback — it cannot be re-read after that agent compacts its context, cannot be quoted back when you review the result, and arrives shredded if a newline lands wrong. A document survives all of that, and afterwards both agents can point at the same text and disagree about it precisely.

**Deliver, then stop.** This skill does not watch the other pane, and must not — polling `capture-pane` in a loop burns your turn on a screen only the other agent can advance. Every dispatch carries a stamp with your pane id and an instruction to append the report to the same document, then knock back with one line starting `DONE:`, `BLOCKED:` or `QUESTION:`. That line is what wakes you: you learn the outcome without opening anything, and open the document only when you need the evidence behind it. The other agent knocks when it's done; you stay free in the meantime.

**And don't close their pane either.** The pane you dispatched to is a window in the user's own
layout — you didn't start it, and finishing the task doesn't make it yours. The windows that need
breaking down afterwards are the ones `agent-crew` launched in the `agents` session (see its
"breaking camp" section); not this one.

## Resolve the pane id

The pane id is always explicit, taken from `$ARGUMENTS` (`%7 …`, `7 …`) or from what the user just said ("让 7 去修这个", "发给 %3"). A bare number means `%<number>`.

If there's no pane id anywhere, ask for it in plain prose — don't render a menu of panes. The user is looking at their own tmux layout and already knows which pane they mean, so a generated list is noise; and guessing is worse than asking, because a wrong guess drops a task into an unrelated session.

## The channel

`docs/tmux-channel/` at the root of the project the work belongs to — `git rev-parse --show-toplevel`, falling back to the cwd. Create the directory if it isn't there yet.

One document per exchange, named `<YYYYMMDD-HHMM>-<slug>.md`, and it is append-only: task, report, follow-up, second report all accumulate in the same file, so the whole round trip can be read top to bottom later.

```markdown
# 修复 verifyToken 的过期判断

- panes: %5 → %7
- repo: /Users/me/proj

## Task — %5 → %7 — 2026-04-26 19:30

<the brief>

## Report — %7 → %5 — 2026-04-26 20:05

DONE: <the receiving agent appends this, evidence below the status line>
```

The `## Task` / `## Report` / `## Follow-up` headings are the protocol, not decoration: `reply.sh` refuses to knock unless the document's last section is a report, which is what stops an agent from announcing work it never wrote down. Keep the headings in English exactly as above; the body can be any language.

When the task already has a document elsewhere — an `agentflow:task` brief under `docs/tasks/`, a spec, a review report — don't dispatch that file. Write a channel document that links to it and adds what this particular handoff needs, so the report lands in the channel instead of mutating a document someone else owns.

## Write the task before you send it

This is the part that decides whether the delegation succeeds, and it's where dispatching differs from sending a shell command. The receiving agent starts from nothing: it cannot see this conversation, the files you have open, your cwd, or the conclusion you just reached. Every reference that only makes sense *here* arrives *there* as a puzzle — and a confused agent doesn't stall, it guesses, then confidently does the wrong work.

So write the `## Task` section as a standalone brief:

- **Absolute paths only.** The other pane may sit in a different directory, or a different checkout of the same repo — where the same relative path is a different file.
- **Expand every pointer.** "刚才那个函数", "上面那个报错", "the file we changed" → the real path, the real symbol, the actual error text inlined.
- **Say what "done" looks like** — the command that should pass, the behavior that should change. Without a finish line the other agent invents its own, usually a more ambitious one than you wanted.
- **Fence off what's fragile** if the work sits next to something you don't want touched.
- **Keep your uncertainty visible.** If you don't know whether the fix belongs in A or B, say that. Asserting a guess as fact is how a small task turns into a wrong refactor.

Same request, thin versus self-contained:

Thin — `把刚才那个 token 的 bug 修一下`

Self-contained, as `docs/tmux-channel/20260426-1930-fix-verify-token.md`:

```markdown
# 修复 verifyToken 的过期判断

- panes: %5 → %7
- repo: /Users/me/proj

## Task — %5 → %7 — 2026-04-26 19:30

修复 /Users/me/proj/src/auth.ts 中 verifyToken 的过期判断。
当前写的是 `if (payload.exp < Date.now() / 1000)`，但本服务签发的 exp 是毫秒时间戳，
结果所有 token 一律被判为已过期。改成毫秒比较，并补一个单测覆盖「刚签发的 token 仍有效」。
验收：cd /Users/me/proj && npm test -- auth 全绿。
不要改动 refreshToken 的逻辑，那部分另有 issue 在跟。
```

The second one is longer, and that length is the entire value being added.

## Script paths

All `scripts/` paths are relative to **the directory containing this SKILL.md file**. Resolve to an absolute path before running anything, since this skill may be installed under a plugin cache rather than the repo:

```bash
SKILL_DIR="<absolute path of the directory holding this SKILL.md>"
```

## Send it

```bash
bash "$SKILL_DIR/scripts/dispatch.sh" "<pane_id>" "docs/tmux-channel/<name>.md" "<one-line headline>"
```

The headline is optional and is the only content that travels with the pointer — one line for the other agent to recognize the task by, nothing it must act on. The script collapses newlines and truncates it, so don't try to smuggle the brief through it; anything the other agent needs belongs in the document.

Send only through this script — never `tmux send-keys` with task text directly. The script handles the things that quietly break otherwise: it refuses text that isn't an existing document, resolves the path to an absolute one so it still means the same file in the other pane's cwd, warns when the document sits outside the channel, uses bracketed paste so the pointer doesn't submit in fragments, sends Enter as a separate event so TUI agents actually receive it, stamps the sender so the reply has somewhere to go, guards against dispatching to your own pane, and cleans up the buffer so the user's paste stack stays theirs.

## After sending

Report which pane you dispatched to, the channel document path, one line on what you handed off, and the receipt lines the script printed. Then stop and move on to other work.

Read the receipt before you report success. If it shows the other agent mid-task, your dispatch is queued behind that work rather than started — say so, since "dispatched" and "being worked on" are different claims. If it shows a shell prompt or an unrelated program, the pointer probably landed in the wrong pane; surface that immediately instead of reporting a clean handoff.

## When the reply arrives

It lands as two lines: a status and the same document path.

```
BLOCKED: refreshToken 也有秒/毫秒混用，需要你决定是否一并改
Report in: /Users/me/proj/docs/tmux-channel/20260426-1930-fix-verify-token.md
```

The status decides your next move, and the three are genuinely different: `DONE:` closes the round trip, `BLOCKED:` means the task is stalled until you act, `QUESTION:` means the other agent is waiting on an answer you owe it. Act on that line — don't open the document just to find out which one it was.

Then read the `## Report` section before you relay anything. The status is a headline; the evidence a user might check — the commands, the actual output, what the other agent skipped — is in the file, directly under the brief it should be measured against. Relaying the status alone passes on a claim you haven't looked at.

Treat the reply as a report, not a message needing an answer. Respond only when the status asks you to: answer a `QUESTION:` or unblock a `BLOCKED:` by appending a `## Follow-up` section to the same document and sending its path once more. A `DONE:` needs nothing back — an acknowledgement just starts another turn over there.
