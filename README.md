# tco-spec

Multi-agent collaboration plugin for AI coding tools — spec-driven workflow via tmux.

## Overview

tco-spec coordinates multiple AI agents (Claude Code, Codex, OpenCode, etc.) working in separate tmux panes through a structured spec-driven workflow. Instead of ad-hoc communication, agents exchange structured messages with task labels and feedback tags, creating a traceable collaboration loop.

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

## Skills

| Skill | Purpose |
|-------|---------|
| `tco-spec:spec-feature` | Generate feature design documents from discussions |
| `tco-spec:spec-change` | Generate change documents for refactoring/modifications |
| `tco-spec:spec-implement` | Dispatch tasks to a remote agent's tmux pane |
| `tco-spec:spec-review` | Review code against design documents |
| `tco-spec:spec-feedback` | Send execution results back to the task originator |
| `tco-spec:spec-handle-feedback` | Process feedback, trigger review, and decide next steps |
| `tco-spec:spec-check-review` | Verify review document accuracy and fix code |
| `tco-spec:spec-fix-review` | Send review document to another agent for verification and fix |
| `tco-spec:tmux-send` | Send text content to a tmux pane |

## Workflow

### 1. Design Phase

```
/tco-spec:spec-feature <feature-name>   # or /tco-spec:spec-change <change-name>
```

Enter design discussion mode — discuss without writing code, generate document when ready.

### 2. Implementation Phase

```
/tco-spec:spec-implement <doc-path>
```

Send the design document to another agent's tmux pane. The receiving agent gets a `[task from ...]` labeled message with clear instructions and a feedback directive.

### 3. Feedback Loop

The implementer completes work and calls `tco-spec:spec-feedback` to send results back:

```
[feedback from Claude Code: implemented 3 tasks, pane_id: %5]
```

### 4. Review & Fix

The originator receives feedback and `tco-spec:spec-handle-feedback` triggers automatically:

- Calls `tco-spec:spec-review` to review the code
- If issues found → sends fix tasks back via `tco-spec:spec-implement` (up to 3 rounds)
- If all passed → done

```
/tco-spec:spec-fix-review <review-doc>   # Send review to another agent for fix
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

## Installation

### Claude Code

Register this repository as a plugin marketplace, then install:

```
/plugin marketplace add fingergohappy/tco-spec
```

Then install the plugin:

```
/plugin install tco-spec
```

After installation, restart Claude Code. Skills will be available with the `tco-spec:` prefix:

```
/tco-spec:spec-feature login-system
/tco-spec:spec-implement docs/spec/login_feature.md
```

<details>
<summary>Alternative: local development</summary>

```bash
claude --plugin-dir /path/to/tco-spec
```

</details>

### Codex (OpenAI)

Use the built-in `$skill-installer` inside Codex to install from GitHub:

```
$skill-installer install https://github.com/fingergohappy/tco-spec/tree/main/skills/spec-feature
```

Repeat for each skill you need, or install all at once by cloning:

```bash
# User scope (available across all projects)
git clone https://github.com/fingergohappy/tco-spec.git ~/.agents/skills/tco-spec

# Project scope (shared with team)
git clone https://github.com/fingergohappy/tco-spec.git .agents/skills/tco-spec
```

After installation, restart Codex. Skills auto-discover on startup and can be invoked by name:

```
$spec-feature login-system
$spec-implement docs/spec/login_feature.md
```

## Requirements

- tmux session with multiple panes
- AI coding tool running in each pane (Claude Code, Codex, OpenCode, etc.)
- `tco-spec:tmux-send` skill available for inter-pane communication

## License

MIT
