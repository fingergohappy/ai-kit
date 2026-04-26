---
name: review-shell
description: |
  从 shell 脚本质量角度审查代码。检查变量引用、错误处理、可移植性、临时文件清理等 shell 编程规范。
  Review code from a shell script quality perspective. Checks variable quoting, error handling, portability, temp file cleanup, and shell scripting best practices.
  接收文件列表作为输入，只审查 .sh 文件，输出该角度的审查发现。
argument-hint: "[<file path or directory>]"
---

# review-shell

Review code from a shell script quality perspective.

## Review Scope

Focus on all `.sh` files. Does not review markdown content or architecture design.

## Checklist

### Variable Safety [HIGH]

- Are variables double-quoted: `"$VAR"` instead of `$VAR`
- Is path concatenation safe: `"${dir}/${file}"` instead of `$dir/$file`
- Are command substitutions quoted: `"$(command)"` instead of `$(command)`
- Are there variables used without being declared

### Error Handling [HIGH]

- Does the script start with `set -euo pipefail` or equivalent error handling strategy
- Do piped commands account for intermediate failures (`pipefail`)
- Are exit codes checked after critical commands
- Are temp files created with `mktemp` cleaned up via `trap`

### Command Injection [CRITICAL]

- Is user input or external data directly concatenated into command strings
- Is `eval` usage safe
- Does `xargs` handle special characters (spaces, quotes)

### Portability [MEDIUM]

- Is the shebang explicit: `#!/usr/bin/env bash` or `#!/bin/bash`
- Is bash-specific syntax used while the shebang says `sh`
- Is the `local` keyword used inside functions
- Is array syntax compatible with the target shell

### Readability [LOW]

- Are long pipelines broken with `\`
- Is complex logic extracted into functions
- Are magic numbers or hardcoded paths extracted as variables

## Output Format

Review results follow this format:

### [{Severity Level}] {Issue Summary}

**File**: `{file path}:{line number}`
**Issue**: {specific description}
**Suggestion**: {fix direction}
