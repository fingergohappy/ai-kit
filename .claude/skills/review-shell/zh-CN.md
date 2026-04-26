---
name: review-shell
description: |
  从 shell 脚本质量角度审查代码。检查变量引用、错误处理、可移植性、临时文件清理等 shell 编程规范。接收文件列表作为输入，只审查 .sh 文件。
  Review code from a shell script quality perspective. Checks variable quoting, error handling, portability, temp file cleanup, and shell scripting best practices. Accepts file list as input, only reviews .sh files.
when_to_use: |
  当用户说「shell 审查」「shell 脚本质量」「review shell」「检查 shell 脚本」时触发。
argument-hint: "[<文件路径或目录>]"
---

# review-shell

从 shell 脚本质量角度审查代码。

## Review Scope

关注所有 `.sh` 文件。不审查 markdown 内容、不审查架构设计。

## Checklist

### Variable Safety [HIGH]

- 变量引用是否加双引号：`"$VAR"` 而非 `$VAR`
- 路径拼接是否安全：`"${dir}/${file}"` 而非 `$dir/$file`
- 命令替换是否加引号：`"$(command)"` 而非 `$(command)`
- 是否存在未声明就使用的变量

### Error Handling [HIGH]

- 脚本开头是否有 `set -euo pipefail` 或等效的错误处理策略
- 管道命令是否考虑了中间失败（`pipefail`）
- 关键命令后是否检查退出码
- `mktemp` 创建的临时文件是否有 `trap` 清理

### Command Injection [CRITICAL]

- 用户输入或外部数据是否直接拼入命令字符串
- `eval` 的使用是否安全
- `xargs` 是否处理了特殊字符（空格、引号）

### Portability [MEDIUM]

- shebang 是否明确：`#!/usr/bin/env bash` 或 `#!/bin/bash`
- 是否使用了 bash 特有语法但 shebang 写的是 `sh`
- `local` 关键字是否在函数内使用
- 数组语法是否兼容目标 shell

### Readability [LOW]

- 长管道是否用 `\` 换行
- 复杂逻辑是否提取为函数
- 魔法数字或硬编码路径是否提取为变量

## Output Format

审查结果按以下格式输出：

### [{严重级别}] {问题概述}

**文件**: `{文件路径}:{行号}`
**问题**: {具体描述}
**建议**: {修复方向}
