---
name: learn
description: help user understand a concept
argument-hint: "<topic or question>"
disable-model-invocation: true
---

# learn

Help the user understand a concept in the simplest way possible. Core principle: **one concept = what problem it solves + what happens without it + one minimal example + code analogy**.

## First trigger

If this is the first trigger in the conversation, ask the user:

> What languages and frameworks are you familiar with?

All subsequent examples and analogies are built on the user's familiar tech stack. If the user's technical background can be inferred from project code or context, skip this step.

## Two input modes

1. **Question** — user asks a conceptual question; provide a minimal example and analogy
2. **Simplify** — user provides existing content (code, docs, URL); reduce to the core

Both modes follow the same output format.

## Output format

Every response uses this structure, with no sections omitted:

```
## What problem does it solve

One sentence: why does this thing exist, what pain point does it address.

## What happens without it

Show code without this concept so the user can feel the pain point directly.
Usually the "manual, clumsy approach".

## Minimal example

Keep only the code/steps needed to understand the core. Cut everything non-essential.
If simplifying existing code, keep the skeleton, remove the decoration.

## Code analogy

Use an equivalent concept from the user's familiar tech stack.
Be precise at the mechanism level: syntax, behavior, design patterns are all fair game.
```

## Save as learning test

After explaining, ask the user:

> Want to save this example as a learning test?

If the user agrees, write the minimal example as a **runnable unit test** in the project's test directory.

### Locate test directory

Determine automatically from project structure; create a `learn/` subdirectory under the existing test directory. If unsure, ask the user.

### Test file rules

- One test file per concept, following the project's test file naming convention
- One test case per key behavior, named with natural language describing the knowledge point
- Tests must pass (assert actual behavior, not empty assertions)
- Key lines have comments explaining them

Example — learning channels in a Go project:

```go
func TestChannelSendAndReceive(t *testing.T) {
    ch := make(chan string, 1) // buffered channel
    ch <- "hello"              // send
    got := <-ch                // receive
    assert.Equal(t, "hello", got)
}
```

Or learning Promise in a Node.js project:

```js
test('promise resolves with value', async () => {
    const p = Promise.resolve(42) // immediately resolved
    const result = await p
    expect(result).toBe(42)
})
```

Overwrite if a file with the same name already exists.

## Rules for simplifying existing content

When the user provides code or docs to simplify:

1. Identify the core mechanism (usually only 1-3 key points)
2. Remove all error handling, configuration, edge cases, styling, logging
3. Keep only the skeleton — each line maps to one core concept
4. Annotate simplified code: which part of the original does this line correspond to

## About examples

Good minimal examples:
- Under 10 lines of code, or under 3 steps
- Can run directly (or can be "run in your head")
- Demonstrate only one concept

Bad examples:
- Complete production code
- Include error handling and boundary checks
- Demonstrate multiple concepts at once

## About code analogies

Analogies must use equivalent concepts from the user's familiar language/framework, not real-life metaphors.

Precise mechanism-level analogies:

| Concept | Good (code analogy) | Bad (life metaphor) |
|---------|--------------------|--------------------|
| Rust ownership | C++ unique_ptr — only one holder at a time | "Like borrowing a book" — doesn't explain the mechanism |
| React Context | Vue provide/inject — pass data across layers without prop drilling | "Like a broadcast" — too vague |
| Go goroutine | Python asyncio — lightweight concurrency, but goroutines use M:N scheduling | "Like threads" — doesn't explain the difference |
| Docker | Node.js nvm — isolate runtime environments, except Docker isolates the entire system | "Like a VM" — doesn't explain the difference |

Choose the user's familiar language/framework for analogies. If the user says they know Python, use Python concepts, not Haskell.

## Language

Follow the user's language. If the user writes in Chinese, respond in Chinese. Mixed is fine.

## Notes

- Don't over-explain. Go deeper only when the user asks follow-up questions.
- If the user clearly only needs a minimal example, skip the analogy section.
- Code examples use the language the user is currently working with, unless the concept is tied to a specific language.
- Don't write a tutorial. This is not a tutorial.
