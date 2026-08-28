---
name: tmux-reply
description: |
  Report back to the tmux pane that dispatched a task to you by appending a "## Report" section to the channel document the task arrived in, then sending that pane a one-line status — DONE: / BLOCKED: / QUESTION: — together with the document's path. Use this proactively — without being asked again — whenever the task you are working on arrived from another pane (the message pointed at a document and carried a stamp like "[dispatched from tmux pane %5 ...]") and you have now finished it, hit a blocker, or need a decision only the dispatcher can make. Also use it when the user says "通知 5"、"告诉 dispatch 我的那个 pane"、"回报一下进展"、"跟 %3 说我做完了", "reply to the pane that sent this", "tell the other agent I'm done". This is the return half of tmux-dispatch: the dispatcher never polls you, so an unwritten report means nobody knows the work happened.
argument-hint: "[<pane_id>] [<doc_path>] [DONE:|BLOCKED:|QUESTION: <one line>]"
---

# tmux-reply

Write your report into the channel document the task came in, then knock on the pane that dispatched it with the one-line status.

Why this needs saying at all: the dispatcher deliberately does not watch you. It handed off the task and moved on, so there is no progress bar, no polling, no timeout — the *only* thing that closes the loop is this message. Finishing the work and staying quiet looks identical to never having started.

**The status travels, the evidence stays.** Exactly two things go through tmux: one line beginning `DONE:`, `BLOCKED:` or `QUESTION:`, and the document's path. That split is deliberate on both sides. The status is the only part the dispatcher must act on — close the task, unblock you, answer you — and making it open a file to learn which of the three happened would put a disk read between it and its next move. Everything the status is *based on* — diffs, commands, actual output, what you skipped — goes in the document, because the dispatcher has to check your result against the brief, and in the document the two sit one under the other and stay readable a week later, whereas a pasted report is gone the moment that agent compacts its context.

So: never paste the report into the pane, and never reduce the document to the status line. Each one is unreadable in the other's place.

## Find the document and the dispatcher's pane id

Both are in the message that started this work:

```
Task document: /Users/me/proj/docs/tmux-channel/20260426-1930-fix-verify-token.md

[dispatched from tmux pane %5. That document is the task -- read it; ...]
```

That path is where you write, and `%5` is where you knock. Use the absolute path from the message verbatim — never the same relative path resolved in your own cwd, which in another checkout of the same repo is a different file, and your report would land where nobody is looking.

If the task carried no stamp, it wasn't dispatched and there is nobody expecting a report; just answer the user normally. If you're sure a report is wanted but can't find the pane id, ask in plain prose — don't list panes and don't send to a pane you inferred, since a report landing in a stranger's session is worse than a report that arrives late.

## Append the report

Add a new section at the **end** of the document, leaving everything above it untouched — the channel is append-only, and the brief you were given is the thing your result will be checked against:

```markdown
## Report — %7 → %5 — 2026-04-26 20:05

DONE: 修好了 verifyToken 的毫秒/秒比较问题。
改动：/Users/me/proj/src/auth.ts:42 改为 `payload.exp < Date.now()`；
新增 /Users/me/proj/test/auth.test.ts 里的 "freshly signed token is valid" 用例。
验证：cd /Users/me/proj && npm test -- auth → 14 passed, 0 failed。
未处理：refreshToken 里有同样的秒/毫秒混用（auth.ts:71），按你的要求没动。
```

Keep the heading in English and starting with `Report` — `reply.sh` checks that the document's last section is one, and refuses to knock otherwise. That check is the point: it catches the expensive failure of announcing work that was never written down.

What the body owes the dispatcher, which is another agent reading this cold:

- **First line is the status**: `DONE: …`, `BLOCKED: …`, or `QUESTION: …` — the same line you will pass to `reply.sh`, so the document and the pane agree on the outcome. The dispatcher's next action is entirely different in each case.
- **Absolute paths** for every file you touched. The dispatcher may be in a different directory or checkout.
- **Evidence, not assurance.** The command you ran and its actual result beats "tests pass" — the dispatcher may need to relay this to a user who will check.
- **What you did not do**, and why: skipped scope, a fix you judged out of bounds, a guess you had to make. Silent omissions become the dispatcher's bugs.
- **For `BLOCKED` / `QUESTION`, state the specific decision needed** and what you already tried. A vague blocker just bounces the round trip back to you.

Thin — `做完了`. Substantive — the block above. Keep it to what the dispatcher needs in order to act; a full narrative of your debugging costs it a re-read and adds nothing it can use.

## Script paths

All `scripts/` paths are relative to **the directory containing this SKILL.md file**. Resolve to an absolute path before running anything, since the plugin may be installed under a cache directory rather than the repo:

```bash
SKILL_DIR="<absolute path of the directory holding this SKILL.md>"
```

## Send it

```bash
bash "$SKILL_DIR/scripts/reply.sh" "<pane_id>" "<doc_path>" "DONE: <one line>"
```

All three arguments are required, and the status must open with `DONE:`, `BLOCKED:` or `QUESTION:` — the script rejects anything else rather than sending a line the dispatcher cannot triage. Normally it is the first line of the `## Report` section you just wrote, trimmed to fit one line; the script collapses newlines and truncates past 160 characters, so don't try to fit the evidence in it.

What lands in the dispatcher's pane, status first:

```
DONE: verifyToken 的毫秒/秒比较已修好，auth 测试 14 passed
Report in: /Users/me/proj/docs/tmux-channel/20260426-1930-fix-verify-token.md

[reply from tmux pane %7, re: the task you dispatched. The status line above is the outcome; the evidence behind it is the last "## Report" section of that document.]
```

Send only through this script — never `tmux send-keys` with report text. It refuses to send if the document's last section isn't your report, rejects a status without one of the three prefixes, resolves the path to an absolute one, uses bracketed paste so the two lines don't submit themselves one at a time, sends Enter as a separate event so the dispatcher's TUI actually receives it, stamps your pane id, and fails loudly if the dispatcher's pane is gone — which means the work happened and the report is safely on disk, but nobody has been told. Say that to your own user, with the document path.

## One knock per task

Send once, then stop. Don't follow up with an acknowledgement, and if the dispatcher answers your `QUESTION`, treat the answer as instructions to act on — not as something to confirm receipt of.

The reason is structural: every message into a pane starts a new turn for the agent there. Two agents each being polite will trade acknowledgements indefinitely, and both burn real tokens doing it. Knock a second time only when there is new substance — a follow-up finding, a later failure, work that finished after your first report — and when you do, append a new `## Report` section rather than editing the old one.
