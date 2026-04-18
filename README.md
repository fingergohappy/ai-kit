# ai-kit

Multi-agent collaboration plugin for AI coding tools — spec-driven workflow via tmux.

## Overview

ai-kit coordinates multiple AI agents (Claude Code, Codex, OpenCode, etc.) working in separate tmux panes through a structured spec-driven workflow. Instead of ad-hoc communication, agents exchange structured messages with task labels and feedback tags, creating a traceable collaboration loop.

```
┌─────────────┐    task from     ┌─────────────┐
│  Agent A     │ ───────────────→ │  Agent B     │
│  (Designer)  │                  │  (Implementer)│
│              │ ←─────────────── │              │
└─────────────┘  feedback from   └─────────────┘
                  ┌─────────────┐
                  │  Agent C     │
                  │  (Reviewer)  │
                  └─────────────┘
```

## Installation

### Claude Code

Register this repository as a plugin marketplace, then install:

```
/plugin marketplace add fingergohappy/ai-kit
```

Install the plugin:

```
/plugin install spec-workflow@ai-kit
/plugin install tmux@ai-kit
/plugin install git@ai-kit
```

After installation, restart Claude Code. Skills will be available with the plugin prefix:

```
/spec-workflow:spec-feature login-system
/spec-workflow:spec-implement docs/spec/login_feature.md
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

Use the built-in `$skill-installer` inside Codex to install from GitHub:

```
$skill-installer install https://github.com/fingergohappy/ai-kit/tree/main/skills/spec-feature
```

Repeat for each skill you need, or install all at once by cloning:

```bash
# User scope (available across all projects)
git clone https://github.com/fingergohappy/ai-kit.git ~/.agents/skills/ai-kit

# Project scope (shared with team)
git clone https://github.com/fingergohappy/ai-kit.git .agents/skills/ai-kit
```

After installation, restart Codex. Skills auto-discover on startup and can be invoked by name:

```
$spec-feature login-system
$spec-implement docs/spec/login_feature.md
```

## Plugins

### spec-workflow

Spec-driven workflow: design docs, code review, and feedback loop.

| Skill | Purpose |
|-------|---------|
| `spec-workflow:spec-feature` | Generate feature design documents from discussions |
| `spec-workflow:spec-change` | Generate change documents for refactoring/modifications |
| `spec-workflow:spec-implement` | Send design document to a tmux pane for execution |
| `spec-workflow:spec-review` | Review code against design documents |
| `spec-workflow:spec-feedback` | Send execution results back to the task originator |
| `spec-workflow:spec-handle-feedback` | Review code completion, check against original design, decide next steps |
| `spec-workflow:spec-check-review` | Verify review document accuracy and fix code |
| `spec-workflow:spec-fix-review` | Send review document to a tmux pane for verification and fix |

### tmux

Tmux infrastructure utilities for inter-pane communication.

| Skill | Purpose |
|-------|---------|
| `tmux:tmux-send` | Send text content to a tmux pane |

### git

Git worktree and branching utilities.

| Skill | Purpose |
|-------|---------|
| `git:rebase-to-root` | Rebase worktree feature branch back to root's current branch (supports both worktree and root invocation) |
| `git:commit` | Create atomic git commits with validation and conventional commit messages |

## Workflow

### 1. Design Phase

```
/spec-workflow:spec-feature <feature-name>   # or /spec-workflow:spec-change <change-name>
```

Enter design discussion mode — discuss without writing code, generate document when ready.

### 2. Implementation Phase

```
/spec-workflow:spec-implement <doc-path>
```

Send the design document to another agent's tmux pane. The receiving agent gets a `[task from ...]` labeled message with clear instructions and a feedback directive.

### 3. Feedback Loop

The implementer completes work and calls `spec-workflow:spec-feedback` to send results back:

```
[feedback from Claude Code: implemented 3 tasks, pane_id: %5]
```

### 4. Review & Fix

The originator receives feedback and `spec-workflow:spec-handle-feedback` triggers automatically:

- Calls `spec-workflow:spec-review` to review the code
- If issues found → sends fix tasks back via `spec-workflow:spec-implement` (up to 3 rounds)
- If all passed → done

```
/spec-workflow:spec-fix-review <review-doc>   # Send review to another pane for fix
```

## Message Protocol

### Task Dispatch

```
[task from {agent-name}: {task-summary}, pane_id: {pane_id}]
```

### Execution Feedback

```
[feedback from {agent-name}: {result-summary}, pane_id: {pane_id}]
```

Agents use these tags to identify message types and route responses correctly.

## Requirements

- tmux session with multiple panes
- AI coding tool running in each pane (Claude Code, Codex, OpenCode, etc.)
- `tmux:tmux-send` skill available for inter-pane communication

### rebase-to-root

No extra dependencies — uses native `git worktree` and `git rebase` commands (requires git 2.5+).

Supports two invocation modes:
- In a worktree: auto-detects current branch and rebases back to root
- In root: lists all worktrees for selection

```
/git:rebase-to-root                    # auto-detect or select worktree
/git:rebase-to-root my-feature         # specify feature name
```

## License

MIT
