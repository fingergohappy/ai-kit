---
name: commit
description: commit 
model: haiku
context: fork
argument-hint: "push | --no-verify "
disable-model-invocation: false
---

# Commit

Create a clean, reviewable git commit from the current working tree.

**Input**: `$ARGUMENTS`

---

## Phase 1 — Validation

If `$ARGUMENTS` contains `--no-verify`, skip this phase.

Otherwise:

1. Detect the project toolchain from the repository root.
2. Run the test/lint/build commands that actually exist in the project.
3. On failure, stop and report — do not proceed with the commit.

Only run commands that actually exist in the project.

---

## Phase 2 — Staging

Check the current state:

```bash
git status --short
git diff --cached --stat
```

Staging rules:

1. If files are already staged, use the staged changes as the commit candidate.
2. If no files are staged, run:

```bash
git add -A
```

3. Check the staged diff again:

```bash
git diff --cached --stat
git diff --cached
```

If there are still no staged changes, stop: `Nothing to commit.`

---

## Phase 3 — Analysis

Review the staged diff and determine whether it is a single logical change or a mix of multiple concerns.

Signals that suggest splitting:

- Unrelated features or fixes in different areas
- Source code changes mixed with large-scale formatting changes
- Refactoring mixed with behavioral changes
- Pure documentation changes unrelated to code changes
- Large generated file updates mixed with hand-written code

If the staged diff contains multiple logical changes:

1. **Do not** commit immediately.
2. Automatically split into multiple staging groups by logical concern.
3. Generate a commit message for each group and commit them individually.

If the staged diff is a cohesive change, proceed directly.

---

## Phase 4 — Commit Message

Generate a conventional commit message:

```text
<type>: <description>
```

Allowed types:

- `✨ feat` — new feature
- `🐛 fix` — bug fix
- `📝 docs` — documentation only
- `♻️ refactor` — structural changes with no behavior change
- `✅ test` — tests only
- `🔧 chore` — tooling, configuration, dependencies, maintenance
- `⚡ perf` — performance optimization
- `👷 ci` — CI/CD changes

Message rules:

- Imperative mood
- Lowercase description
- No trailing period
- Keep within 72 characters
- Describe what changed, not implementation steps

Examples:

- `✨ feat: add codex commit workflow prompt`
- `🐛 fix: handle empty staged diff before commit`
- `📝 docs: clarify codex sync behavior`

---

## Phase 5 — Commit

First, show the proposed message and a summary of the commit scope.

Then commit:

```bash
git commit -m "<type>: <description>"
```

If hooks or validation fail at this stage, report the failure clearly — do not modify unrelated files.

---

## Phase 6 — Output

Report:

- Commit hash
- Final commit message
- Number of changed files
- Whether validation was run or skipped

If `$ARGUMENTS` contains `push`, run:

```bash
git push
```

Report the push result. Otherwise, suggest:

- `git push`
