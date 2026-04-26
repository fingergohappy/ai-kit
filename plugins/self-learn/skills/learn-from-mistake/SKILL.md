---
name: learn-from-mistake
description: |
  Solidify AI corrections into guardrail rules. Triggers when the user corrects the AI's behavior, generating a new skill or CLAUDE.md rule.
argument-hint: "[<error description>]"
disable-model-invocation: false
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
