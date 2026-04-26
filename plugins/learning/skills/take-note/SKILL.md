---
name: take-note
description: |
  Generate structured learning notes with Markdown docs and runnable code examples. Each note gets its own directory.
argument-hint: "[<topic>] [--dir <path>] [--from <url|file>]"
disable-model-invocation: true
---

# take-note

After the user finishes learning, organize the learning content into structured notes. Each note corresponds to a standalone directory containing a Markdown document and runnable minimal code examples.

## Overview

The skill accepts three kinds of input (can be combined):
1. **Oral description** — the user verbally describes what they learned
2. **Reference materials** — URLs, files, or screenshots provided by the user
3. **Conversation context** — what was discussed/learned in the current session

When reference materials are provided, read them first (fetch URL / read file), then combine with the user's oral description to produce notes.

## Directory Structure

Notes go in `docs/learning/`, runnable examples go in the project's test directory as learning tests:

```
docs/learning/
├── react-context/
│   └── README.md
├── rust-ownership/
│   └── README.md
└── grpc-basics/
    └── README.md

tests/learn/                          # 或项目对应的测试目录
├── react-context.test.tsx
├── rust-ownership_test.rs
├── grpc-basics-server_test.go
└── grpc-basics-client_test.go
```

Note directory name is the topic in kebab-case. Example code lives in the test directory so it stays runnable.

## Workflow

### 1. Gather input

If the learning topic is already clear from context, start immediately. Otherwise, ask the user. Collect:

- **Topic**: What was learned (e.g., "Rust ownership", "React Context")
- **Materials**: URLs, files, or screenshots from the user. Read them before organizing.
- **Context**: What was already mentioned in conversation about this topic
- **Output dir**: Defaults to `docs/learning/`, override via `--dir` argument

If the user provides a `--from` argument, fetch/read that resource first to extract key points, then let the user supplement with their own understanding.

### 2. Generate notes

Use the structure below. Adapt section depth based on topic complexity — a small topic may not need all sections, while a large one may need more sub-sections.

```markdown
# {Topic}

## Core Understanding

Summarize the core flow or key idea of this topic as concisely as possible.
If it's a process, use numbered steps.
If it's a concept, explain in 2-3 sentences what it is and what problem it solves.

Include a minimal example (code goes to the test directory as a runnable test; reference the test file path here).
Explain what each part of the example does in plain language.

## How It Maps to {Specific Scenario in Project}

If what was learned is used in the current project, show the real project code.
Break it down step by step: creation → configuration/usage → wrapping/invocation.
Compare the minimal example with the project usage and explain why the project does it differently.

## Data Flow / Call Chain

If multiple components/modules are involved, use a text-based flow diagram to illustrate data flow.

## Key Takeaways

List all knowledge points covered in this learning session. One point per line, concise but complete.
Include both direct API/syntax knowledge and indirect design patterns/best practices.

```

### 3. Generate learning tests

Create runnable unit tests in the project's test directory (under a `learn/` subdirectory):

- Locate test directory from project structure; create `learn/` under it. If unsure, ask the user.
- File naming: follow the project's test file convention (e.g., `{topic}.test.ts`, `{topic}_test.go`)
- One test file per concept, one test case per key behavior
- Test case names use natural language describing the knowledge point
- Tests must pass (assert actual behavior, not empty assertions)
- Key lines annotated with comments explaining their purpose
- In the note's README.md, reference the test file path

### 4. Write and confirm

1. Create the note directory (`docs/learning/{topic}/`) and README.md
2. Create the learning test file in the test directory
3. Show the user:
   - Note directory path + test file path
   - Note title + first paragraph of Core Understanding
   - Ask if any section needs adjustment

## Notes

- Follow the language the user uses. If the user mixes languages, follow the mix.
- The Core Understanding section is the most important — write it in a way the user can remember, not a copy-paste from documentation.
- Minimal examples should focus on one point. Don't try to cover all use cases in a single example.
- If the topic doesn't involve code (e.g., design philosophy, architecture concepts), don't force code file generation.
- If the project contains related code, always show the real usage — this is what sets learning notes apart from tutorials.
