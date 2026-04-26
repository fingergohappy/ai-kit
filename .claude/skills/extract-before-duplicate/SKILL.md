---
name: extract-before-duplicate
description: |
  修改分支逻辑（if/else、switch、match）时，防止在多个分支中复制粘贴相同代码。
  Prevent code duplication in branch logic by extracting differences as variables before adding common operations outside branches.
  在编写或修改任何包含分支结构的代码时都应检查此 skill。
---

# extract-before-duplicate

## Anti-pattern

When modifying branch logic, focusing only on the new feature and stuffing the new logic into every branch, causing the common operation to be duplicated.

```bash
# Wrong: load-buffer call is duplicated in both branches
if [[ -f "$CONTENT" ]]; then
  BODY=$(cat "$CONTENT")
  tmux load-buffer - <<< "${BODY}[tag]"
else
  tmux load-buffer - <<< "${CONTENT}[tag]"
fi
```

## Correct Approach

Let the branch only handle parsing differences (assigning variables), and move common operations outside the branch.

```bash
# Correct: branch only resolves BODY, load-buffer is written once
if [[ -f "$CONTENT" ]]; then
  BODY=$(cat "$CONTENT")
else
  BODY="$CONTENT"
fi
tmux load-buffer - <<< "${BODY}[tag]"
```

## Checklist

1. After writing branch code, compare the content of each branch
2. If there are identical or highly similar lines, extract them as variables or functions
3. Only keep the truly different parts inside the branch
