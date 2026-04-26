---
name: nvim-lsp-init
description: |
  生成 Neovim LSP 环境配置脚本，在启动 nvim 前配置 PATH 和环境变量。分析项目技术栈和 SDK 工具生成可 source 的 shell 脚本。
  Generate Neovim LSP environment setup scripts that configure PATH and env vars before launching nvim. Analyzes project tech stack and SDK tools to produce a source-able shell script.
when_to_use: |
  当用户说「生成 lsp 脚本」「初始化 lsp 环境」「nvim lsp」「lsp 环境配置」时触发。
  Also triggers on "generate lsp script", "setup lsp environment", "nvim lsp init".
argument-hint: "[<输出路径>]"
---

# nvim-lsp-init

分析项目技术栈，搜索所需的 LSP server，生成一个可 `source` 的 shell 脚本，在启动 nvim 前配置好环境。

## Overview

生成的脚本做两件事：
1. **PATH 设置** — 将项目本地的 bin 目录加入 PATH（如 `node_modules/.bin`、`.venv/bin` 等）
2. **依赖检查** — 检查每个 LSP 工具是否存在，不存在则打印安装命令

## Workflow

### 1. Detect environment

先检查机器的 SDK 管理工具，再检查项目的语言/框架。

**安装优先级**（从高到低）：
1. SDK 管理工具：`asdf`、`mise`、`sdkman` — 用于管理运行时和全局 LSP 依赖
2. 项目包管理器：`pnpm add -D`、`uv add --dev` — 用于项目级别的 LSP 依赖
3. 系统包管理器：`brew`、`apt` — 仅作备选

```bash
# SDK 管理工具
asdf --version && asdf list      # asdf 插件和版本
mise --version                   # mise (rtx)
sdk version                      # sdkman (Java)

# 项目标识文件
ls package.json go.mod Cargo.toml pyproject.toml pom.xml build.gradle* 2>/dev/null
```

### 2. Search LSP requirements

对检测到的每种语言/框架，搜索确认：
- LSP server 的二进制文件名
- 最佳安装方式（按上述优先级）
- 是否需要特殊环境变量（如 JAVA_HOME、lombok agent 等）

### 3. Generate script

默认输出路径：`scripts/env-lsp.sh`。可通过参数指定。

脚本必须包含：

**基础工具函数**（始终包含）：
- `path_prepend` — 幂等的 PATH 前置添加
- `check_lsp_dep <bin> <install_cmd> [search_path]` — 检查依赖是否存在，不存在则打印安装命令

**按语言生成代码块** — 只生成项目实际检测到的语言对应的代码块。每个代码块：
- 将相关的项目本地 bin 目录加入 PATH（如适用）
- 对每个需要的 LSP server 调用 `check_lsp_dep`
- 设置需要的环境变量（如 JAVA_HOME、JDTLS_JVM_ARGS 等）

**PROJECT_ROOT 解析** — 根据项目需要选择：
- 简单方式：`PROJECT_ROOT="$(pwd)"` — 从项目根目录 source 时可用
- 脚本路径方式：从 `${BASH_SOURCE}` / `${(%):-%N}` 解析 — 需要从其他目录 source 时使用

### 4. Output

写入脚本，`chmod +x`，然后显示：

```
Generated: scripts/env-lsp.sh

Usage:
  source scripts/env-lsp.sh
  nvim

Detected LSP config:
  - TypeScript (vtsls)
  - ...

Edit scripts/env-lsp.sh to customize.
```

## Reference Examples

以下是按语言生成的代码块示例。**只生成项目需要的 — 不要把所有示例都加进去。**

### Node / TypeScript / Frontend

```bash
if [ -d "$PROJECT_ROOT/node_modules/.bin" ]; then
  path_prepend "$PROJECT_ROOT/node_modules/.bin"
fi

check_lsp_dep "vtsls" "pnpm add -D @vtsls/language-server" "$PROJECT_ROOT/node_modules/.bin"
check_lsp_dep "vscode-eslint-language-server" "pnpm add -D vscode-langservers-extracted" "$PROJECT_ROOT/node_modules/.bin"
```

### Python

```bash
if [ -d "$PROJECT_ROOT/.venv/bin" ]; then
  path_prepend "$PROJECT_ROOT/.venv/bin"
fi

check_lsp_dep "pylsp" "uv add --dev python-lsp-server" "$PROJECT_ROOT/.venv/bin"
```

### Java / Gradle / lombok

```bash
_java_home="$(asdf where java 2>/dev/null | tr -d '\r')"
if [ -z "${_java_home}" ]; then
  _java_home="$(/usr/libexec/java_home 2>/dev/null | tr -d '\r')"
fi
if [ -n "${_java_home}" ] && [ -d "${_java_home}" ]; then
  export JAVA_HOME="${_java_home}"
fi

if [ -x "$PROJECT_ROOT/gradlew" ]; then
  _lombok_jar="$("$PROJECT_ROOT/gradlew" -p "$PROJECT_ROOT" -q printLombokJarPath 2>/dev/null | tr -d '\r')"
  if [ -n "${_lombok_jar}" ] && [ -f "${_lombok_jar}" ]; then
    export JDTLS_LOMBOK_JAR="${_lombok_jar}"
    export JDTLS_JVM_ARGS="-javaagent:${_lombok_jar}"
  fi
fi

unset _java_home _lombok_jar
```

### Go

```bash
check_lsp_dep "gopls" "go install golang.org/x/tools/gopls@latest"
```

### Rust

```bash
check_lsp_dep "rust-analyzer" "rustup component add rust-analyzer"
```
