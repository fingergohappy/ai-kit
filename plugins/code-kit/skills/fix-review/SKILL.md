---
name: fix-review
description: |
  Fix issues found in code review reports and automatically update the report status. Triggered when the user says "fix review", "修这个问题", "处理这条审查意见", "修复审查".
  Supports locating issues by report path + line number, or by searching with a natural language description.
  Before fixing, evaluate whether the report's suggestion is reasonable, then formulate a fix plan. After the fix is applied, automatically update the report status from [todo] to [done] and append a fix description.
argument-hint: "<report-path:line-number | issue-description>"
---

# fix-review

Fix issues from code review reports and keep the report status in sync.

## Argument Parsing

`$ARGUMENTS` supports two input formats:

| Format | Example | Parsing |
|--------|---------|---------|
| Report path + line number | `docs/review/2026-04-26_full_review.md:69` | Read content around the specified line and locate the `### #N` issue block |
| Natural language description | `修复 tmux_send.sh 中变量未加引号的问题` | Search for keyword-matched issues under `docs/review/` |

## Execution Steps

### 1. Parse Arguments

Determine the type of `$ARGUMENTS`:

- Matches `^.+\.md:\d+$` → path + line number mode
- Otherwise → description text mode

### 2. Locate Issue

#### Path + Line Number Mode

1. Read the specified report file and navigate to the specified line
2. Search upward to find the `### #N` heading that starts the issue block
3. Read downward until the next `### #` or blank line to extract the complete issue block

#### Description Text Mode

1. Scan all `*.md` report files under `docs/review/`
2. Extract all issue blocks with status `[todo]` or `[doing]`
3. Extract keywords from the description (file names, issue characteristics, etc.)
4. Match against issue titles, file paths, and issue description fields
5. **0 matches** → inform the user that no match was found; suggest refining the description or using path + line number
6. **1 match** → proceed directly to evaluation
7. **Multiple matches** → list all matches and let the user choose

### 3. Evaluate Issue

After locating the issue, do not apply the suggested fix blindly. First read the source file context referenced by the report's suggestion and evaluate independently:

1. Read the source file indicated by the `**文件**` field to understand the actual code
2. Judge whether the `**建议**` in the report is reasonable:
   - Does the suggestion accurately address the root cause described in `**问题**`?
   - Is there a simpler or better fix?
   - Could the fix introduce new issues or affect other functionality?
3. If the suggestion is reasonable → adopt it and formulate the fix plan
4. If the suggestion needs adjustment → explain the reasoning and provide an alternative fix plan

Present the evaluation result to the user:

```
Issue Evaluation:

Report: docs/review/2026-04-26_full_review.md
### #3 [shell] Variable unquoted in here-string

**文件**: `plugins/tmux/skills/tmux-send/scripts/tmux_send.sh:30`
**问题**: ${BODY} comes from an external file or user-supplied parameter, content is uncontrolled...
**建议**: Use printf '%s\n' "$BODY" to write to a temp file...

Evaluation: {Suggestion is reasonable / Suggestion needs adjustment, reasoning}

Fix plan:
- {Specific fix steps}

Confirm fix?
```

Wait for user confirmation. The user can:
- Confirm → execute the fix
- Suggest modifications → adjust the plan
- Cancel → exit

### 4. Fix Code

Apply the fix based on the confirmed evaluation plan:

1. Extract the file path and line number from `**文件**: \`path/to/file:line\``
2. Read the corresponding region of the source file
3. Apply the modification
4. If multiple files are involved, fix them one by one

Record a brief fix description during the fix for updating the report later.

### 5. Update Report

After the fix is applied, update the corresponding issue block in the report document:

**Before:**
```markdown
**状态**: `[todo]`
```

**After:**
```markdown
**状态**: `[done]`
**修复**: {Brief description of what was changed, one sentence}
```

Notes:
- Keep the backticks around the status marker: `` `[done]` ``
- The fix description should be concise, describing what was actually done

### 6. Update Statistics and Change History

#### Update issue_stats

If the report frontmatter contains `issue_stats`, decrement the count for the corresponding severity level:

```yaml
# Before fix
issue_stats:
  high: 9

# After fix
issue_stats:
  high: 8
```

Determine the severity level by reading the issue's status before the fix (whether the issue is under the `## CRITICAL`, `## HIGH`, `## MEDIUM`, or `## LOW` section).

#### Update Change History

Append a row to the change history table at the end of the report:

```markdown
| 2026-04-26 | 修复 #3: {one-sentence fix description} |
```

### 7. Completion Notice

```
Fixed and report updated:
- Source file: plugins/tmux/skills/tmux-send/scripts/tmux_send.sh
- Report: docs/review/2026-04-26_full_review.md
- Status: [todo] → [done]
```

## Edge Cases

- **Issue already has `[done]` or `[skip]` status** → inform the user that the issue has already been handled and confirm whether to re-fix
- **Source file does not exist or path has changed** → inform the user and suggest manual location
- **Fix scope exceeds a single issue** → clearly state the impact range in the fix plan
- **Multiple issues point to the same file** → fix one by one, updating each issue's status after each fix
- **Report suggestion is outdated** → the source file may have been modified by other changes; adjust the fix plan based on the current code
