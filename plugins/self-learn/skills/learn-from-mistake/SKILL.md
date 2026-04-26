---
name: learn-from-mistake
description: |
  当 AI 被用户纠正错误后，主动询问用户是否要将这个教训固化为防护规则。
  触发前提：当前对话中 AI 刚犯了错误并被用户纠正（如「你这里写错了」「不是这样的」「不对」）。
  AI 应在纠正后主动提议：「要不要把这个教训固化下来？」，用户同意后再执行。
  产出物根据错误性质决定：生成新的防护 skill，或向 CLAUDE.md 追加约束规则。
  不触发的场景：用户只是在讨论错误但不针对当前 AI 行为；用户想创建与错误无关的新 skill（应触发 skill-creator）。
  After the AI is corrected by the user, proactively ask whether to固化 (solidify) the lesson as a guardrail rule.
  Trigger前提: the AI just made a mistake in the current conversation and was corrected by the user (e.g., "you got this wrong", "that's not right", "incorrect").
  The AI should proactively suggest after the correction: "Want to solidify this lesson?" and only proceed after the user agrees.
  The output depends on the nature of the error: generate a new guardrail skill, or append a constraint rule to CLAUDE.md.
  Do not trigger when: the user is merely discussing errors without targeting the current AI behavior; the user wants to create a new skill unrelated to a mistake (should trigger skill-creator instead).
argument-hint: "[<error description>]"
---

# learn-from-mistake

After being corrected, proactively propose solidifying the lesson, then generate a guardrail rule upon user approval.

## Workflow

1. **Identify the error**: Triggered when the user corrects the AI. Extract the following:
   - Error behavior: what the AI did
   - Trigger condition: under what circumstances it happened
   - User correction: what the user expects as the correct behavior
   - If the user's correction is unclear, confirm first: "I understand you think [X] is the problem, and the correct approach should be [Y] — is that right?"

2. **Summarize and propose**: Abstract the specific error into a general pattern, present it to the user, and ask for their opinion:
   - Use the pattern: "When X, the AI tends to Y, but the correct approach is Z"
   - Show the summary directly so the user can decide whether to solidify based on the concrete content
   - Stop if the user disagrees

3. **Generalization self-check**: After summarizing the pattern, run a self-check to ensure appropriate granularity:
   - X describes an identifiable coding/operational scenario, not something vague like "when writing code"
   - Z describes an executable check step, not "be more careful"
   - If the self-check fails, adjust the granularity — err on the side of being too specific rather than too abstract

4. **Determine output form**:
   - **Requires an "incorrect vs correct" behavior/operation/code comparison to explain clearly** → generate a skill
   - **A rule that can be stated in one sentence** → update CLAUDE.md
   - When both are needed, do both

5. **Generate output**: Execute according to the determined form

6. **Quality assurance**: If the output is a skill, call `skill-creator:skill-creator` before writing the file to evaluate the description's trigger coverage and content quality, then revise based on the evaluation before writing

## Generate a Skill

Place it in `.claude/skills/{name}/SKILL.md` in the current project root (not the user home directory `~/.claude/skills/`).

Before generating, check whether a similar skill already exists under `.claude/skills/` — update it rather than creating a new one.

### Content Guidelines

The generated skill should include the following core elements (format is flexible; organize based on the nature of the error):

- **Trigger condition**: under what circumstances this mistake tends to occur
- **Error behavior**: what the AI typically does (can be illustrated with code, operational procedures, behavioral descriptions, etc.)
- **Correct approach**: the corrected approach (also not limited to code)
- **Check steps**: 2–4 actionable check actions that the AI can actually perform during coding

### Requirements

- Skill name in kebab-case
- Error patterns should be generalized, not limited to the current case only
- Correct approach should be specific enough for the AI to follow directly
- Check steps should be actionable — each step is a concrete action

## Update CLAUDE.md

Append to the project's `CLAUDE.md`. If `CLAUDE.md` does not exist, create it first with a basic structure.

When appending, find the semantically most relevant section to insert into — do not pile everything at the end of the file. If no suitable section exists, create a new one.
