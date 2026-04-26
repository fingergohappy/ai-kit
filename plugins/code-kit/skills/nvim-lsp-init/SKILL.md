---
name: nvim-lsp-init
description: Generate Neovim LSP setup script.
argument-hint: "[<输出路径>]"
disable-model-invocation: true
---

# nvim-lsp-init

Analyze the project tech stack, search for required LSP servers, and generate a `source`-able shell script that sets up the environment before launching nvim.

## Overview

The generated script does two things:
1. **PATH setup** — prepend project-local bins (`node_modules/.bin`, `.venv/bin`, etc.)
2. **Dependency check** — verify each LSP tool exists; print install command if missing

## Workflow

### 1. Detect environment

Check the machine's SDK management tools first, then the project's language/framework.

**Install priority** (highest to lowest):
1. SDK managers: `asdf`, `mise`, `sdkman` — use for runtime and global LSP deps
2. Project package managers: `pnpm add -D`, `uv add --dev` — for project-local LSP deps
3. System package managers: `brew`, `apt` — fallback only

```bash
# SDK managers
asdf --version && asdf list      # asdf plugins & versions
mise --version                   # mise (rtx)
sdk version                      # sdkman (Java)

# Project identity files
ls package.json go.mod Cargo.toml pyproject.toml pom.xml build.gradle* 2>/dev/null
```

### 2. Search LSP requirements

For each detected language/framework, search to determine:
- LSP server binary name
- Best install method (per the priority above)
- Any special env vars needed (JAVA_HOME, lombok agent, etc.)

### 3. Generate script

Default output: `scripts/env-lsp.sh`. Override via argument.

The script must include:

**Base utilities** (always present):
- `path_prepend` — idempotent PATH prepend
- `check_lsp_dep <bin> <install_cmd> [search_path]` — check existence, print install command if missing

**Per-language blocks** — only include blocks for languages actually detected in the project. Each block:
- Prepends relevant project-local bin to PATH (if applicable)
- Calls `check_lsp_dep` for each required LSP server
- Sets any needed environment variables (JAVA_HOME, JDTLS_JVM_ARGS, etc.)

**PROJECT_ROOT resolution** — choose based on project needs:
- Simple: `PROJECT_ROOT="$(pwd)"` — works when sourcing from project root
- Script-path: resolve from `${BASH_SOURCE}` / `${(%):-%N}` — needed for projects that may source from elsewhere

### 4. Output

Write the script, `chmod +x`, then show:

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

These are examples of per-language blocks. **Generate only what the project needs — don't include all of these.**

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
