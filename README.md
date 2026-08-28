# ai-kit

Multi-agent collaboration plugin suite for AI coding tools — task-driven workflow via tmux, code review, and learning aids.

## Overview

ai-kit provides a collection of plugins that coordinate multiple AI agents (Claude Code, Codex, OpenCode, etc.) working in separate tmux panes through a structured task-driven workflow. Instead of ad-hoc communication, agents exchange documents: the task and the report are written to a shared channel file under `docs/tmux-channel/`, and only that file's path travels between panes — so every handoff leaves a traceable record instead of scrollback. Additional plugins provide code review, learning, and self-reflection capabilities.

```
┌─────────────┐   path of task   ┌─────────────┐
│  Agent A     │ ───────────────→ │  Agent B     │
│  (Sender)    │                  │  (Receiver)  │
│              │ ←─────────────── │              │
└─────────────┘  path of report  └─────────────┘
        │                                │
        └──── docs/tmux-channel/*.md ────┘
            ## Task  →  ## Report
```

## Installation

### Claude Code

Register this repository as a plugin marketplace, then install:

```
/plugin marketplace add fingergohappy/ai-kit
```

Install the plugins you need:

```
/plugin install agentflow@ai-kit
/plugin install tmux@ai-kit
/plugin install git@ai-kit
/plugin install code-kit@ai-kit
/plugin install learning@ai-kit
/plugin install self-learn@ai-kit
```

After installation, restart Claude Code. Skills will be available with the plugin prefix:

```
/agentflow:task login-system
/tmux:tmux-dispatch %7 docs/tmux-channel/20260426-1930-login-system.md "实现登录系统"
/code-kit:evaluate "use postgres vs mysql"
/learning:learn rust lifetimes
/git:commit
/tmux:tmux-reply %5 docs/tmux-channel/20260426-1930-login-system.md "DONE: login feature implemented"
```

<details>
<summary>Alternative: local development</summary>

```bash
claude --plugin-dir /path/to/ai-kit
```

</details>

### Codex (OpenAI)

This repository includes Codex plugin manifests for `agentflow`, `tmux`, and `git`.

Register this repository as a Codex plugin marketplace:

```bash
codex plugin marketplace add https://github.com/fingergohappy/ai-kit
```

Quick AI-driven install/update:

Paste this URL into Codex and ask it to follow the runbook:

```
follow this install https://github.com/fingergohappy/ai-kit/blob/main/docs/codex_plugin_install_update.md
```

Detailed guide:

- [`docs/codex_plugin_install_update.md`](docs/codex_plugin_install_update.md)

## Plugins

### agentflow

Agent collaboration loop: task → dispatch → evaluate → report → review → redo. The dispatch and report legs are provided by the `tmux` plugin (`tmux-dispatch` / `tmux-reply`).

| Skill | Purpose |
|-------|---------|
| `agentflow:task` | Generate structured task documents (feature / change / task) |
| `agentflow:gate-evaluate` | Receiver-side input guard — evaluate incoming tasks before execution |

### code-kit

Code review and evaluation utilities for single-agent workflows.

| Skill | Purpose |
|-------|---------|
| `code-kit:evaluate` | Rigorous evidence-based evaluation (tech selection, architecture, claim verification) |
| `code-kit:review-init` | Analyze project tech stack and generate customized review skills |
| `code-kit:review-report` | Generate structured review report from audit results |
| `code-kit:fix-review` | Fix a specific issue from a review report and update its status |
| `code-kit:fix-review-all` | Batch-fix all pending issues from a review report in parallel |
| `code-kit:nvim-lsp-init` | Generate Neovim LSP environment setup scripts for the project |

### learning

Personal learning and note-taking aids.

| Skill | Purpose |
|-------|---------|
| `learning:learn` | Explain concepts with minimal examples, code analogies, and simplification |
| `learning:take-note` | Generate structured learning notes with runnable code examples |

### self-learn

AI self-reflection and lesson capture.

| Skill | Purpose |
|-------|---------|
| `self-learn:learn-from-mistake` | After AI is corrected, propose solidifying the lesson as a guardrail rule |

### tmux

Tmux infrastructure utilities for inter-pane communication and long-running service management.

| Skill | Purpose |
|-------|---------|
| `tmux:tmux-dispatch` | Write the task to a channel document and point another pane's agent at it, stamping a reply channel |
| `tmux:tmux-reply` | Append the report to that same document and knock on the pane that dispatched the task |
| `tmux:agent-tmux` | Start/restart/stop long-running commands in shared tmux session (auto-isolates by project/branch) |

### git

Git worktree and branching utilities.

| Skill | Purpose |
|-------|---------|
| `git:rebase-to-root` | Rebase worktree feature branch back to root's current branch |
| `git:commit` | Create atomic git commits with validation and conventional commit messages |

### wikijs

Internal Wiki.js knowledge base operations via GraphQL API. Requires the `WIKIJS_TOKEN` environment variable (generated in the Wiki.js admin panel under API Access).

| Skill | Purpose |
|-------|---------|
| `wikijs:wikijs` | Query, search, read, publish, and update pages on the internal Wiki.js |

## Workflow

### Agent Collaboration (agentflow)

#### 1. Design Phase

```
/agentflow:task <task-name>
```

Enter design discussion mode — discuss without writing code, generate document when ready. Outputs to `docs/tasks/`.

#### 2. Dispatch Phase

```
/tmux:tmux-dispatch <pane_id> docs/tmux-channel/<name>.md "<one-line headline>"
```

The brief is written to a channel document under `docs/tmux-channel/` (one file per exchange, named `<YYYYMMDD-HHMM>-<slug>.md`); what reaches the other pane is that document's absolute path plus a stamp, `[dispatched from tmux pane %N. ...]`, telling the receiving agent to read the document and where to report back to. Task text is never pasted across panes — it would survive only in scrollback.

When the task already has a document elsewhere (an `agentflow:task` brief under `docs/tasks/`, a spec, a review report), the channel document links to it rather than replacing or mutating it.

#### 3. Execution & Report

The receiver evaluates the task via `gate-evaluate`, executes, appends its result to the **same document** as a `## Report` section, then calls `tmux-reply` to knock:

```
/tmux:tmux-reply <pane_id> docs/tmux-channel/<name>.md "DONE: ..."
```

```
[reply from tmux pane %9, re: the task you dispatched. The report is the last "## Report" section of that document.]
```

`reply.sh` refuses to send unless the document's last section is that report — announcing work that was never written down is the failure this protocol exists to prevent.

#### 4. Review

The sender opens the channel document and checks the deliverable against the brief sitting right above the report. Treat the report as a claim to verify rather than a result to accept -- if it does not hold up, append a `## Follow-up` section to the same document naming the specific issues and dispatch it again.

### Code Review (code-kit)

#### 1. Initialize Review

```
/code-kit:review-init
```

Analyze the project tech stack and generate customized review skills into `.claude/skills/`.

#### 2. Run Review

Use the generated review skills, then generate a report:

```
/code-kit:review-report
```

#### 3. Fix Issues

Fix individual issues or batch-fix all:

```
/code-kit:fix-review docs/review/2026-04-26_full_review.md:69
/code-kit:fix-review-all docs/review/2026-04-26_full_review.md
```

### Evaluation (code-kit)

```
/code-kit:evaluate "use postgres vs mysql for this project"
```

Collects dual-source evidence (project facts + external best practices) and produces a rigorous evaluation with cited sources.

## Message Protocol

Two things carry the protocol: the channel document on disk, and the pointer message that travels between panes.

### Channel document

`docs/tmux-channel/<YYYYMMDD-HHMM>-<slug>.md` at the project root, append-only, one file per exchange:

```markdown
# 修复 verifyToken 的过期判断

- panes: %5 → %7
- repo: /Users/me/proj

## Task — %5 → %7 — 2026-04-26 19:30
## Report — %7 → %5 — 2026-04-26 20:05
## Follow-up — %5 → %7 — 2026-04-26 20:20
```

The `## Task` / `## Report` / `## Follow-up` headings are machine-read: `reply.sh` checks that the last section of the document is a report before it will notify the dispatcher. Keep them in English; bodies can be any language.

### Task Dispatch

```
Task document: {absolute path}
{optional one-line headline}

[dispatched from tmux pane {pane_id}. That document is the task -- read it; this message is only the pointer. When you finish, get blocked, or need a decision, append a "## Report" section to the same document and notify {pane_id} using your tmux-reply skill.]
```

### Execution Report

```
Report in: {absolute path}
{optional verdict line, e.g. DONE: ...}

[reply from tmux pane {pane_id}, re: the task you dispatched. The report is the last "## Report" section of that document.]
```

Stamps are built by `tmux-dispatch` / `tmux-reply`, not hand-written. The dispatch stamp is what makes the reply possible at all: it is the only place the receiving agent learns which pane to report back to. Paths are always absolute — in another worktree of the same repo, the same relative path is a different file.

## Requirements

- tmux session with multiple panes
- AI coding tool running in each pane (Claude Code, Codex, OpenCode, etc.)
- `tmux:tmux-dispatch` and `tmux:tmux-reply` skills available for inter-pane communication
- a `docs/tmux-channel/` directory in the working project (created on first dispatch) that both panes can read and write

## License

MIT
