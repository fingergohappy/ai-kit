---
name: nvim-hints
description: Visualize code paths inside the user's running Neovim instance — populate the quickfix list with the ordered steps of a call chain and add virtual text explanations at each location. Use this whenever the user provides an nvim socket path, or asks to trace/mark/annotate a call path, request flow, or code chain "in nvim/vim/the editor", mentions qflist/quickfix or virtual text, or wants to see how a request or function flows through the code inside their editor — "梳理一下这个调用链", "在 nvim 里标注出来", "看看这个请求是怎么一路走下来的", "用 qflist 列一下" — even if they never say the word "annotate".
---

# nvim-hints: Annotate code paths in Neovim

Send code-path analysis straight into the user's running Neovim: the quickfix list carries the steps in execution order (navigable with `:cnext`/`:cprev`, default keys `]q`/`[q`), and virtual text carries a per-step explanation at the end of each line. The user walks the whole chain without leaving the editor.

## Workflow

### 1. Get the socket

The socket is provided by the user (e.g. `/run/user/1000/nvim.12345.0` or `/tmp/nvim.sock`). If it has not been given in this conversation, ask for it. Then verify connectivity immediately:

```bash
python3 scripts/nvim_hints.py check <socket>
```

`check` also returns the file currently open in nvim and its working directory — usually exactly the code the user cares about, a good starting point for the analysis.

### 2. Analyze the chain

Use your normal tools (Grep, Read, LSP, ...) to work out the chain the user asked about. Two requirements:

- **Line numbers must be fresh and exact.** Virtual text and qflist entries anchor to specific lines; being off by one line pins the note to unrelated code, which is worse than no note at all. Derive every line number from file content you have just Read — never from a fuzzy grep impression or a remembered older read.
- **Pick the single most representative line per step.** Usually the function definition line, or the call statement that hands control to the next step. One line per step — do not sprinkle marks across a whole function body.

### 3. Generate hints.json

Write it to the scratchpad directory:

```json
{
  "title": "payment creation path",
  "items": [
    {
      "file": "/abs/path/handler.go",
      "line": 42,
      "text": "1. HandleCreatePayment — HTTP entry point",
      "hint": "① parse request, validate, delegate to service layer"
    },
    {
      "file": "/abs/path/service.go",
      "line": 108,
      "text": "2. PaymentService.Create — orchestration",
      "hint": "② open tx, call risk check then ledger"
    }
  ]
}
```

- Order `items` by **execution order** (the order the user walks with `:cnext`), not by file.
- `text` is one quickfix line: start with a step number, then the symbol name and a few words of positioning ("HTTP entry point", "orchestration") so the list alone reads as the skeleton of the chain.
- `hint` is the end-of-line virtual text: what this step does and why it leads to the next. Keep it under ~40 characters — long hints get truncated by the window edge. When omitted it falls back to `text`.
- Branching chains are expressible: use hierarchical numbering like `3a.`, `3b.` and state the branch condition in `text`.
- Use absolute paths in `file`. Write the copy in the language of the current conversation.

### 4. Apply

```bash
python3 scripts/nvim_hints.py apply <socket> <hints.json>
```

The script automatically: clears all previous marks (namespace `claude_hints`) → loads the touched buffers and sets virtual text → replaces the qflist → runs `copen` (focus stays in the user's window). Output looks like `applied 5 hints`; missing files or out-of-range lines are reported alongside — that means step 2's analysis was wrong, so fix it and re-apply rather than leaving it.

### 5. Report

Summarize the chain briefly (how many steps, from where to where) and remind the user how to drive it: Enter jumps from the quickfix window, `]q`/`[q` (or `:cnext`/`:cprev`) walk the chain, and saying "clear the marks" runs `python3 scripts/nvim_hints.py clear <socket>`.

## Notes

- Every `apply` clears the previous marks first, so tracing several chains in one session needs no manual cleanup; use the `clear` subcommand only when the user explicitly asks to remove everything.
- The user may have edited files while you analyzed. If many operations have passed since your last Read, re-confirm the key line numbers before applying.
- Never use `--remote-send` to send keystrokes to nvim — it disturbs the user's editing state. All interaction goes through this skill's script (which uses `--remote-expr` internally).
- Marks live only in the running nvim session's memory; no file is ever modified.
