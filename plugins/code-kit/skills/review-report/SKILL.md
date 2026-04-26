---
name: review-report
description: Generate structured review report.
argument-hint: ""
disable-model-invocation: true
---

# review-report

Reads a template based on review results, generates a structured review report document, and outputs it to `docs/review/`.

## Execution Steps

### 1. Collect Review Results

Gather the following information from the preceding review workflow (e.g., review-full, review-diff):

- Review mode: `full` (entire codebase) or `diff` (incremental)
- Base branch (diff mode only)
- Number of changed files
- List of review skills that participated
- Issue list (each issue includes: severity level, review perspective, file path:line number, issue description, fix suggestion)

If the review results are not in the current conversation context, prompt the user to run `/review-full` or `/review-diff` first.

### 2. Read Template

Read [report_template.md](references/report_template.md) and generate the report according to the template format.

### 3. Populate Report

Fill the review results into the template:

- **frontmatter**: title, date, mode, base branch, scope, issue statistics, participating review skills
- **Overview**: a one-sentence summary of what was reviewed and what severity levels of issues were found
- **Review Scope**: mode, number of files, list of review perspectives
- **Issue Summary**: count table by severity level
- **Issue Details**: grouped by CRITICAL -> HIGH -> MEDIUM -> LOW; each issue includes review perspective, file path:line number, issue description, fix suggestion, and status (default `[todo]`)
- **Change History**: initial review record

### 4. Output File

- Full review: `docs/review/{YYYY-MM-DD}_full_review.md`
- Diff review: `docs/review/{YYYY-MM-DD}_diff_review.md`

Create the `docs/review/` directory first if it does not exist.

If the target file already exists, increment the `version` field in the frontmatter and overwrite the file.

### 5. Completion

Output the file path and prompt the user that issues can be fixed via `/fix-review`.
