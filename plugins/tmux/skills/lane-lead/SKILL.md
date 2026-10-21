---
name: lane-lead
description: |
  Act as the lead: you talk with the user, and the actual work goes to Claude Code workers you start as new windows in your own tmux session, one window per job. Covers taking stock before handing anything off (also after a crash or reboot cut running lanes short), launching each worker so it runs unattended under the same account and permissions as you, writing and dispatching its brief, keeping every decision and every outward-facing action with the user, relaying reports after checking them, and closing windows only when asked. Use whenever the user says "开个 window 去修", "启动个 claude 去做", "你派出去", "在这个 session 里开窗口处理", "你负责和我沟通, 活派给 claude", "帮我看下派出去的做完没有", "电脑关机了, 看下车道到哪了", "spin up a claude for this", "hand this to a new window". For codex / pi in the separate `agents` session use `agent-crew`; for the brief itself and its delivery use `tmux-dispatch`.
argument-hint: "[<the work>]"
disable-model-invocation: false
---

# lane-lead

You are the lead. The user talks to you; the work happens in Claude Code windows you start next to yourself, one window per job (a "lane"). You keep the overview, the user's decisions and every outward-facing action; the lanes do the reading, coding, testing and PRs.

That split is the point. A lead that starts doing a lane's work itself stops answering the user and loses the overview; a lane that decides a business question or posts to Jira on its own does something the user never approved.

## 1. Take stock before you hand anything off

A brief is only as good as your picture of where the work stands. Before you dispatch, find out — especially when the user says earlier lanes may have been cut short ("电脑关机了", "不知道有没有做完"):

- **Channel documents**: `docs/tmux-channel/*.md` in the main checkout **and in every worktree** (`find <repo-parent> -path '*/docs/tmux-channel/*' -newermt '<when>'`). A `## Task` without a `## Report` after it is unfinished work; a `## Follow-up` without a report after it is a follow-up nobody did.
- **Worktrees**: `git status -sb` and `git log origin/<base>..HEAD` in each lane's tree. Uncommitted diffs are half-finished work, not garbage.
- **Transcripts**: `~/.claude/projects/<cwd-slug>/*.jsonl`, and the same under every other `CLAUDE_CONFIG_DIR` the user runs (a second account's lanes are invisible from the first). The last assistant lines tell you exactly where a lane stopped. The session id is the file name; `claude --resume <id>` continues it.
- **Shared environments the lanes touched**: anything a lane may have switched (a mock flipped to a real upstream, a test fixture bound, a feature switch). An interrupted lane never switched it back. Check the current state yourself before you report "nothing is broken".
- **The tracker**: ticket status and the newest comments. Testers may have reported something new while the lanes were down.

Report this to the user as: per lane, what is done, what is half done (and where the half-finished work sits), what never started, and anything left switched on. Then ask what to start, unless they already told you.

## 2. Start each worker

Find your own pane and session; workers go into **your** session, not a new one:

```sh
echo "$TMUX_PANE"                                    # e.g. %0 — the reply channel
tmux display -p -t "$TMUX_PANE" '#{session_name}'    # e.g. thunes
```

Launch under the same account and permission mode you run with. If you run with bypassed permissions, the worker must too, or it stalls on a prompt nobody is watching. Check your own config dir with `cat /proc/$PPID/environ | tr '\0' '\n' | grep CLAUDE_CONFIG_DIR`, and pass it on when it is set:

```sh
tmux new-window -d -t <session> -n <job-name> -c <dir> \
  "cd <dir> && exec claude --dangerously-skip-permissions"
tmux list-windows -t <session> -F '#{window_index} #{window_name} #{pane_id}'
```

- `-d` keeps the user's focus where it is. `exec` makes the window close when claude exits instead of leaving a bare shell that looks busy.
- Name the window after the job (`cr118-wrapup`, `fb-flaky`), so `list-windows` reads as a status board.
- **One worktree per writing lane**, created the way the project prescribes (its helper, its directory, its "ask first" rule). A lane that only edits shared docs or runs checks can start in the main checkout. Read the project's CLAUDE.md on worktrees before you open one. If it says to ask the user, ask, or say plainly in your reply that you opened one and why.
- Wait about 10 s for the prompt, then `capture-pane` once. Dim text in the input box (`Try "..."`) is a suggestion placeholder, not user input.

## 3. Brief and dispatch

Write one channel document per lane, **in the tree that lane works in**, then deliver it with the `tmux-dispatch` skill. Follow that skill for the command and for the self-contained-brief rules. Put the lane's pane id in the `panes:` line once you know it.

A lead's brief carries a few things a plain hand-off doesn't:

- **What is already done and where it stopped.** Name the commit, the uncommitted diff, the root cause already found, and the repro already run, so the lane continues instead of starting over.
- **Which questions come back to you.** Business semantics, anything that reverses a decision the user already made, a new config switch, touching production code where only a test fix was expected. List the ones you can foresee, quoting the code comment or ticket line that marks them as decided.
- **Outward-facing actions are drafts.** Jira or PR comments, emails and status transitions are written into the report for the user to approve, never posted by the lane. Merging is the user's.
- **The other lanes, by name and path**, as off limits.
- **The finish line**: the commands that must pass, the PR to open, and the status to knock back with (`QUESTION: 待合` when a PR waits for the user's merge).

Dispatch them all, then tell the user in one table: window, pane, tree, job, and what will come back to them. Then stop. Don't poll; the lanes knock back through `tmux-reply`.

## 4. While they work: you are the user's interface

- **The user asks "what is X about?"**: answer from what you already know (the ticket, the brief, the code), in plain language with the concrete numbers. Don't interrupt a lane to ask it.
- **A lane knocks back `QUESTION:`**: put it to the user as background first, then the options and your recommendation, one question at a time. Append the user's answer as a `## Follow-up` in that lane's document and dispatch the path again. Before sending, `capture-pane` the lane once. If it has a menu open ("Enter to select"), your Enter would pick an option for it.
- **`BLOCKED:`**: unblock it yourself if it's mechanical (a missing tunnel, a stale branch); otherwise it's a question for the user.
- **`DONE:`**: a claim. Read the `## Report`, look at the diff or PR, check the command output it quotes. Then relay the result, the evidence and what it skipped. Relaying only the status line passes on something you haven't checked.

## 5. Closing windows

The windows sit in the user's own session, next to their other work. When a lane has finished and its result is relayed, **ask** before closing it. The user may want to read its reasoning or keep using it. On a yes, close **by pane id**, one at a time (`tmux kill-pane -t %7`), since window indexes shift when renumbering is on. Never close a pane you didn't start, including the one the user resumed themselves.
