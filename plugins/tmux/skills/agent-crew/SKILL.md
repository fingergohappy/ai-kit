---
name: agent-crew
description: |
  Put outside CLI agents (codex, pi, ...) to work in a dedicated `agents` tmux session, one window each — whether that is handing one of them a job, splitting a job across several, having two solve the same problem independently, or having several review one artifact from different angles. Use whenever the user says "让 codex 去做这个", "让 codex 和 pi 一起做", "起个 agent 跑一下", "让 pi 也做一遍看看", "起几个 agent 分头审", "多角度并行 review", "一个车道一个模型", "开几个窗口跑", "fan this out", "have codex do it", "run these in parallel". Covers launching the windows so their thinking stays visible, the per-tool model flags, how work is split so the results compose, how writing agents are isolated so they don't destroy each other's work, and how the results are collected and checked, and how camp is broken afterwards (ask before closing, so windows don't pile up). Writing and delivering each window's brief is `tmux-dispatch`'s job.
argument-hint: "[<the work>] [<who: codex|pi|...>]"
disable-model-invocation: false
---

# agent-crew

Get work done by agents that aren't you — in their own tmux session, one window each, with results that come back checkable.

Three shapes, and the differences between them are what this skill is about:

- **Delegate** — one agent, one job. It writes code, you check the result.
- **Split** — several agents, disjoint pieces of one job. Fastest, and the only shape where they can destroy each other's work.
- **Duplicate** — several agents, the *same* job, independently. For a problem where you'd rather compare two answers than trust one: a hard bug, a design with no obvious shape, a tricky migration. Two solutions side by side is information; one solution is a guess with a confident tone.
- **Review** — several agents, one artifact, one angle each, read-only. Verdicts merge into one.

The first three write. The last one doesn't, and that single fact changes what has to be set up.

## The `agents` session

All crew windows live in a tmux session named `agents`, one window per agent, named after its job (`codex-migrate`, `pi-arith`, …). The session exists for this and nothing else, so windows can be created and killed freely without disturbing the user's own layout.

```sh
tmux has-session -t agents 2>/dev/null || tmux new-session -d -s agents
```

## Launch interactively — never `-p`

```sh
# right: interactive, output visible as it happens
tmux new-window -t agents -n <name> "cd <absolute path> && exec pi --provider xai --model grok-4.6 --thinking xhigh"
tmux new-window -t agents -n <name> "cd <absolute path> && exec codex -m gpt-5.6-sol -c model_reasoning_effort=\"max\""

# wrong: non-interactive plus a pipe — silent for the entire run
pi -p "$(cat brief.md)" 2>&1 | tee out.log
```

`-p` is non-interactive, and piping its stdout into `tee` makes it block-buffer on top of that. At high thinking levels the agent reasons for a long time and then emits everything at once, so the pane prints nothing and the log stays 0 bytes — indistinguishable from a process that never started. Launched interactively you can watch what it reads and how it reasons, and take over the conversation directly when it goes wrong.

`exec` matters too: without it the agent runs as a child of a shell that outlives it, so the window sits on a bare prompt after the agent exits, which reads as "still working".

The `cd` in the launch command sets that agent's working directory — for writing agents, see the isolation section below, because this is where the isolation is decided.

## Model flags

Copy these verbatim — the model id is the whole string:

| tool | how to launch it |
|---|---|
| `pi` | `pi --provider xai --model grok-4.6 --thinking xhigh` |
| `codex` | `codex -m gpt-5.6-sol -c model_reasoning_effort="max"` |

`sol`, `grok`, `5.6` are nicknames, not model ids. A window launched with one exits on an unknown-model error the moment it starts, and what's left is a pane sitting at a shell prompt — which looks exactly like an agent that's thinking. Never shorten, never reconstruct from memory.

codex has no `--thinking` flag; the reasoning level is a config override, hence the `-c`. Write both out in the launch command even when the user's `~/.codex/config.toml` already defaults to them: duplicate and review need a different model per window, and an inherited default is the same model in every window.

For **duplicate** and **review**, deliberately use different models per window where it's cheap to do so — two models with the same blind spot answering the same question twice buys nothing over asking once. For **split**, it doesn't matter; pick whichever is better at that piece.

## Hand each window its brief

Once the window is up and the agent has reached its interactive prompt, get the pane id and dispatch:

```sh
tmux list-panes -t agents:<name> -F '#{pane_id}'
```

Then use the **`tmux-dispatch`** skill to deliver the brief to that pane id. Follow that skill for how the brief travels and how it must be written — don't reconstruct its command line from memory here, and never `send-keys` the task text yourself.

Two of its rules bite harder with a crew than with a single hand-off:

- **The brief is self-contained.** Each window starts from nothing: it can't see this conversation, this cwd, or the conclusion you just reached. Absolute paths, every pointer expanded, an explicit finish line, and an explicit boundary — `read only, do not edit code` for reviewers, and for writers, which paths are theirs and which are off limits.
- **Don't poll.** Dispatch every window, then go do something else. Looping `capture-pane` across N panes burns your whole turn on screens only those agents can advance; they knock back through `tmux-reply` when they're done. A single `capture-pane` to check one is alive is fine — a loop is not.

## Isolate the writers

Reviewers are read-only and can share one checkout safely. **Writers cannot.** Two agents editing in the same working tree will overwrite each other's edits, stage each other's files into their commits, fight over the build cache, and produce a diff nobody can untangle — and none of them will notice, because each one sees a tree that keeps changing under it and assumes it did that itself.

So before launching any writing agent, decide where it writes:

- **One worktree per writing agent**, and `cd` the launch command into it. The window name and the branch name should match, so `tmux list-windows` tells you what's checked out where.
- **Duplicate mode always needs separate worktrees** — the whole point is two independent attempts, and sharing a tree collapses them into one mess.
- **Split mode needs them too** unless the pieces are genuinely in different repos.
- If the project has its own worktree convention (a helper script, a fixed parent directory, files that must be linked in), follow it rather than a bare `git worktree add`.
- Say in each brief which tree is that agent's and that it must not touch the others. An agent that wanders into a sibling worktree does damage that looks, in the diff, exactly like your own work.

The merge is yours, not theirs. Don't ask a crew member to merge into a branch a sibling is still working on.

## Splitting the work

However the work is cut, the cut must be **disjoint** — pieces that don't overlap, angles that don't argue the same point in two places. Overlap is where the parallelism gets paid back in conflicts and duplicate reports.

For a **split**, cut along file and module boundaries, not along "you do the easy half". Name in every brief exactly which paths belong to that agent.

For a **review**, cut along axes that fail independently: correctness, arithmetic and units, state machine and concurrency, scope and non-goals, tests, operability. An axis the artifact can't fail is a window not worth opening. For an sdd review (CR / spec / implementation), don't invent axes — the lane table for that stage in `sdd/references/review-lanes.md` already is the cut.

Every brief names that window's **output path**, and for reviews its **finding-id prefix**, so nothing is written to a shared file concurrently.

## Collecting the results

Each window reports through `tmux-reply` and writes its own file. What you do with those depends on the shape:

- **Delegate / split** — a report saying `DONE` is a claim, not evidence. Read the diff and run the tests yourself before you relay it as finished. An agent that hit something it couldn't solve and worked around it will report done, honestly, and never mention the workaround unless the brief asked what it skipped.
- **Duplicate** — compare the two solutions and say which you're taking and why. Where they diverge is the interesting part; the divergence usually marks the spot where the problem was actually hard.
- **Review** — **a finding is a claim, not a fact.** Check it yourself before merging: is that `file:line` really there, does the code really read that way, does the rule it cites actually say that? Drop what doesn't hold up and leave a trace (how many were dropped and why); downgrade and mark "unverified" what you can't check right now. Taking them on faith means changing correct code on the strength of a false finding. Then merge into one file: keep the sharper statement when lanes overlap, don't average them. **The overall verdict is the strictest lane's verdict** — one BLOCK makes the whole review BLOCK, however many lanes came back OK.

Report which windows ran, what each produced, and the merged outcome. A window that produced nothing is not a window that found nothing — it's one that didn't run, and saying so is the difference between "done, checked" and "never happened".

## Breaking camp: ask before you close

Once the results are in, verified, and relayed to the user, **ask whether those windows can go**
instead of leaving them up by default:

> codex-migrate and pi-arith have both finished and their results are collected. OK to kill them?

Skip it once and it accrues. After a few rounds the `agents` session holds a dozen windows that
finished days ago, `tmux list-windows` no longer tells you which one is still working and which is
last week's corpse, and a new window is more likely to collide with a stale name.

Ask rather than just closing, because the conversation inside a window is sometimes still worth
something — the user may want to read the agent's reasoning, or take over that pane and keep
pressing it. Closing loses that; the document `tmux-reply` wrote back holds only conclusions.

On a yes, kill them one at a time:

```sh
tmux kill-window -t agents:codex-migrate
tmux list-windows -t agents          # confirm what's left is still working
```

Don't bother removing an empty session — the next `has-session` reuses it.

**Review windows come down later.** A review isn't over when the findings land: they get fixed, and
then the agent **that raised them** should check the fix (anyone else has to re-read the code to
reach the same judgement, and the one who wrote the fix checking their own work is player and
referee at once). So a review window lives until that round actually closes — recheck passed,
verdict settled — and only then is it time to ask. Closing mid-round throws away the context and
the recheck along with it.

**Only close windows you launched.** The boundary is the `agents` session: crew windows are yours
to start, so they're yours to clean up. A pane you sent work to with `tmux-dispatch` — that `%7` in
the user's own layout, a session belonging to another project — **is never yours to touch**. You
didn't start it, the user is working in it, and closing it upends someone else's desk. If you can't
tell who started it, don't close it. Ask.

Unattended flows like `/auto-cr` don't ask, they just kill — there's nobody to ask, and since each
stage launches fresh windows, leftovers only pollute the next stage's context.
