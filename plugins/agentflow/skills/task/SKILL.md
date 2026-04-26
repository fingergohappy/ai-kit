---
name: task
model: opus
description: Organize requirements into task documents.
argument-hint: [任务名称]
disable-model-invocation: false
---

# task

Organize requirement discussions into structured task documents, providing a clear basis for subsequent implementation.

## Document Types

Automatically determined based on conversation content (`references/` paths are relative to this SKILL.md's directory):

| Type | Decision Criteria | Template | Output Filename |
|------|-------------------|----------|-----------------|
| feature | Discussing new features, capabilities, or modules | [feature_template.md](references/feature_template.md) | `{name}_feature.md` |
| change | Discussing refactoring, API changes, breaking changes | [change_template.md](references/change_template.md) | `{name}_change.md` |
| task | General tasks that don't fit the above categories | No fixed template, free format | `{name}_task.md` |

If the type cannot be determined, default to `task`.

## Two Modes

### Mode A: Discussion Mode (Triggered at Conversation Start)

If this skill is triggered at the beginning of a conversation, enter discussion mode:

- **Discuss only, do not modify code** — the goal at this stage is to clarify requirements, not to write code
- Guide the discussion based on the type:
  - feature: background, core concepts, core flow, key mechanisms, interface definitions
  - change: change motivation, impact scope, change checklist, compatibility considerations
  - task: objectives, scope, steps, acceptance criteria
- You may read existing code to understand context, but make no modifications
- Generate the document when the user says things like "生成文档", "输出文档", "写下来" (generate doc, output doc, write it down)

### Mode B: Direct Generation (Triggered Mid-Conversation)

If triggered mid-conversation (when there is already discussion content):

- Directly summarize the existing conversation and generate the document
- Skip the guided discussion phase

## How to Determine the Mode

- Conversation just started, no substantial prior discussion → Mode A
- Conversation already contains discussion of approaches with sufficient context → Mode B

## Document Generation Steps

1. If `$ARGUMENTS` is empty, automatically generate a concise task name based on the conversation content
2. Determine the document type (feature / change / task)
3. If the type is feature or change, read the corresponding template and fill in the content
4. If the type is task, generate in free format with at least: objectives, scope, task list, acceptance criteria
5. Auto-fill metadata:
   - `title`: `$ARGUMENTS` (task name)
   - `type`: feature / change / task
   - `date`: current date (YYYY-MM-DD)
   - `status`: `draft`
   - `version`: `"1.0"`
   - `summary`: extract 1-2 sentences describing the purpose from the conversation
   - `scope`: list the file/module paths involved
6. Output to `docs/tasks/{name}_{type}.md` under the project root directory
   - If the `docs/tasks/` directory does not exist, create it first
   - Use English for filenames, with underscores between words
   - After generation, inform the user of the full file path

## Generation Rules

- Task lists must use checkbox format (`- [ ]`) so items can be checked off as completed
  - Not done: `- [ ] task description`
  - Done: `- [x] task description`
  - Skipped: `- [skip] task description — reason`
- Template placeholders `{xxx}` must all be replaced; none should remain
- Code examples should use the project's actual language
- File paths must reflect actual code paths, making it easy to cross-reference later with the gate-review skill
- For topics not covered in the conversation, infer and supplement based on existing code context
- If a section truly cannot be filled, keep the heading and note the reason ("待讨论" or "待确认", i.e., "to be discussed" or "to be confirmed")

## Follow-Up Workflow

After the document is generated, the user can:
- Call the dispatch skill to assign the task to a receiving end for execution
- Call the gate-review skill to self-review code implementation locally
