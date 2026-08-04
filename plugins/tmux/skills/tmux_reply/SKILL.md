---
name: tmux_reply
description: Report back to the tmux pane that dispatched a task to you. Use this proactively — without being asked again — whenever the task you are working on arrived from another pane (the message carried a stamp like "[dispatched from tmux pane %5 ...]") and you have now finished it, hit a blocker, or need a decision only the dispatcher can make. Also use it when the user says "通知 5"、"告诉 dispatch 我的那个 pane"、"回报一下进展"、"跟 %3 说我做完了", "reply to the pane that sent this", "tell the other agent I'm done". This is the return half of tmux_dispatch: the dispatcher never polls you, so an unsent report means nobody knows the work happened.
argument-hint: "[<pane_id>] [<message>]"
---

# tmux_reply

Send a report back to the pane that dispatched your current task.

Why this needs saying at all: the dispatcher deliberately does not watch you. It handed off the task and moved on, so there is no progress bar, no polling, no timeout — the *only* thing that closes the loop is you sending this message. Finishing the work and staying quiet looks identical to never having started.

## Find the dispatcher's pane id

It's in the stamp on the task you received: `[dispatched from tmux pane %5, loop: false. When you finish, ...]`. That `%5` is the target — look back at the message that started this work rather than guessing from the current tmux layout.

Note the `loop` value in the same stamp: if it says `loop: true`, pass `--loop` when you send (see below). That flag is what tells the dispatcher's `gate-review` it may send fixes back without stopping to ask, and the stamp is the only place it survives the trip — drop it and an unattended loop silently turns into one that waits for a human.

If the task carried no stamp, it wasn't dispatched and there is nobody expecting a report; just answer the user normally. If you're sure a report is wanted but can't find the pane id, ask in plain prose — don't list panes and don't send to a pane you inferred, since a report landing in a stranger's session is worse than a report that arrives late.

## Write the report

The dispatcher is another agent, and your message arrives there as a fresh turn with none of your working context. It has to decide in one glance whether the task is closed, so lead with the verdict and then support it:

- **First line is the verdict**: `DONE: …`, `BLOCKED: …`, or `QUESTION: …`. Nothing else reads as fast, and the dispatcher's next action is entirely different in each case.
- **Absolute paths** for every file you touched. The dispatcher may be in a different directory or checkout.
- **Evidence, not assurance.** The command you ran and its actual result beats "tests pass" — the dispatcher may need to relay this to a user who will check.
- **What you did not do**, and why: skipped scope, a fix you judged out of bounds, a guess you had to make. Silent omissions become the dispatcher's bugs.
- **For `BLOCKED` / `QUESTION`, state the specific decision needed** and what you already tried. A vague blocker just bounces the round trip back to you.

Thin — `做完了`

Substantive:

```
DONE: 修好了 verifyToken 的毫秒/秒比较问题。
改动：/Users/me/proj/src/auth.ts:42 改为 `payload.exp < Date.now()`；
新增 /Users/me/proj/test/auth.test.ts 里的 "freshly signed token is valid" 用例。
验证：cd /Users/me/proj && npm test -- auth → 14 passed, 0 failed。
未处理：refreshToken 里有同样的秒/毫秒混用（auth.ts:71），按你的要求没动。
```

Keep it to what the dispatcher needs in order to act. A full narrative of your debugging costs it a re-read and adds nothing it can use.

## Script paths

All `scripts/` paths are relative to **the directory containing this SKILL.md file**. Resolve to an absolute path before running anything, since the plugin may be installed under a cache directory rather than the repo:

```bash
SKILL_DIR="<absolute path of the directory holding this SKILL.md>"
```

## Send it

```bash
# Short report, passed inline
bash "$SKILL_DIR/scripts/reply.sh" "<pane_id>" "<message>"

# Longer or multi-line report — write it to a file first, pass the path
bash "$SKILL_DIR/scripts/reply.sh" "<pane_id>" "/tmp/reply.txt"

# The task you received was stamped loop: true — echo it back
bash "$SKILL_DIR/scripts/reply.sh" "<pane_id>" "/tmp/reply.txt" --loop
```

Use the file form as soon as the report is multi-line or contains backticks or quotes — shell quoting mangles reports quietly, and a garbled report is worse than none.

Send only through this script — never `tmux send-keys` with the report text. The script handles bracketed paste so your multi-line report doesn't submit itself line by line, sends Enter as a separate event so the dispatcher's TUI actually receives it, stamps your pane id, and fails loudly if the dispatcher's pane is gone (which means the work happened but the report has nowhere to land — worth telling your own user about).

## One report per task

Send the report once, then stop. Don't follow up with an acknowledgement, and if the dispatcher answers your `QUESTION`, treat the answer as instructions to act on — not as something to confirm receipt of.

The reason is structural: every message into a pane starts a new turn for the agent there. Two agents each being polite will trade acknowledgements indefinitely, and both burn real tokens doing it. Send a second message only when there is new substance: a follow-up finding, a later failure, work that finished after your first report.
