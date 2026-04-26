# ai-kit

Multi-agent collaboration plugin suite for AI coding tools — task-driven workflow via tmux, code review, and learning aids.

## Overview

ai-kit provides a collection of plugins that coordinate multiple AI agents (Claude Code, Codex, OpenCode, etc.) working in separate tmux panes through a structured task-driven workflow. Instead of ad-hoc communication, agents exchange structured messages with task labels and report tags, creating a traceable collaboration loop. Additional plugins provide code review, learning, and self-reflection capabilities.

```
┌─────────────┐    task from     ┌─────────────┐
│  Agent A     │ ───────────────→ │  Agent B     │
│  (Sender)    │                  │  (Receiver)  │
│              │ ←─────────────── │              │
└─────────────┘   report from    └─────────────┘
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
/agentflow:dispatch %7 docs/tasks/login_feature.md
/code-kit:evaluate "use postgres vs mysql"
/learning:learn rust lifetimes
/git:commit
/tmux:tmux-send %7 "hello"
```

<details>
<summary>Alternative: local development</summary>

```bash
claude --plugin-dir /path/to/ai-kit
```

</details>

### Codex (OpenAI)

This repository includes Codex plugin manifests for `agentflow`, `tmux`, and `git`.

Quick AI-driven install/update:

Paste this URL into Codex and ask it to follow the runbook:

```
follow this install https://github.com/fingergohappy/ai-kit/blob/main/docs/codex_plugin_install_update.md
```

Detailed guide:

- [`docs/codex_plugin_install_update.md`](docs/codex_plugin_install_update.md)

## Plugins

### agentflow

Agent collaboration loop: task → dispatch → evaluate → report → review → redo.

| Skill | Purpose |
|-------|---------|
| `agentflow:task` | Generate structured task documents (feature / change / task) |
| `agentflow:dispatch` | Send task or fix instructions to a tmux pane for execution |
| `agentflow:gate-evaluate` | Receiver-side input guard — evaluate incoming tasks before execution |
| `agentflow:report` | Report execution results back to the sender |
| `agentflow:gate-review` | Sender-side output guard — review work results, decide pass or redo |

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
| `tmux:tmux-send` | Send text content to a tmux pane |
| `tmux:agent-tmux` | Start/restart/stop long-running commands in shared tmux session (auto-isolates by project/branch) |

### git

Git worktree and branching utilities.

| Skill | Purpose |
|-------|---------|
| `git:rebase-to-root` | Rebase worktree feature branch back to root's current branch |
| `git:commit` | Create atomic git commits with validation and conventional commit messages |

## Workflow

### Agent Collaboration (agentflow)

#### 1. Design Phase

```
/agentflow:task <task-name>
```

Enter design discussion mode — discuss without writing code, generate document when ready. Outputs to `docs/tasks/`.

#### 2. Dispatch Phase

```
/agentflow:dispatch [loop] <pane_id> <doc-path>
```

Send the task document to another agent's tmux pane. The receiving agent gets a `[task from ...]` labeled message. Add `loop` to enable automatic review-fix cycling.

#### 3. Execution & Report

The receiver evaluates the task via `gate-evaluate`, executes, then calls `report` to send results back:

```
[report from Claude Code, pane_id: %5, loop: true: completed 3 tasks]
```

#### 4. Review & Fix

The sender receives the report and `gate-review` triggers:

- Reviews work against original design
- If `loop: true` + issues found → auto-dispatches fix instructions (up to 3 rounds)
- If `loop: false` + issues found → outputs conclusions, user decides next step
- If all passed → done

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

### Task Dispatch

```
[task from {agent-name}, pane_id: {pane_id}, loop: {true|false}: {task-summary}]
```

### Fix Dispatch

```
[fix from {agent-name}, pane_id: {pane_id}, loop: {true|false}: {fix-summary}]
```

### Execution Report

```
[report from {agent-name}, pane_id: {pane_id}, loop: {true|false}: {result-summary}]
```

Agents use these tags to identify message types and route responses correctly.

## Requirements

- tmux session with multiple panes
- AI coding tool running in each pane (Claude Code, Codex, OpenCode, etc.)
- `tmux:tmux-send` skill available for inter-pane communication

## License

MIT
