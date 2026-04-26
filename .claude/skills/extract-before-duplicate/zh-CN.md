---
name: extract-before-duplicate
description: |
  修改分支逻辑（if/else、switch、match）时，防止在多个分支中复制粘贴相同代码。先提取差异为变量，公共操作放到分支外面。
  Prevent code duplication in branch logic by extracting differences as variables before adding common operations outside branches. Use when writing or modifying code with if/else, switch, or match branches.
when_to_use: |
  当用户说「修改分支逻辑」「if/else 重构」「分支去重」「提取公共代码」「防止复制粘贴」时触发。在编写或修改任何包含分支结构的代码时都应检查此 skill。
argument-hint: ""
---

# extract-before-duplicate

## Anti-pattern

修改分支逻辑时，只关注新增的功能点，把新逻辑直接塞进每个分支，导致公共操作被复制多份。

```bash
# 错误：load-buffer 调用在两个分支中重复
if [[ -f "$CONTENT" ]]; then
  BODY=$(cat "$CONTENT")
  tmux load-buffer - <<< "${BODY}[tag]"
else
  tmux load-buffer - <<< "${CONTENT}[tag]"
fi
```

## Correct Approach

先让分支只负责解析差异（赋值变量），公共操作提到分支外面。

```bash
# 正确：分支只解析 BODY，load-buffer 只写一次
if [[ -f "$CONTENT" ]]; then
  BODY=$(cat "$CONTENT")
else
  BODY="$CONTENT"
fi
tmux load-buffer - <<< "${BODY}[tag]"
```

## Checklist

1. 写完分支代码后，对比每个分支的内容
2. 如果有相同或高度相似的行，提取为变量或函数
3. 分支内只保留真正有差异的部分
