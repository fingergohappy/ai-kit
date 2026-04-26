---
title: {审查标题}
type: code-review
mode: {full|diff}
date: {YYYY-MM-DD}
base_branch: {base_branch，仅 diff 模式}
scope:
  - {审查范围}
fix_status: {open | in_progress | fixed | partial}
version: {版本号，初始为 1，每次更新递增}
issue_stats:
  critical: {数量}
  high: {数量}
  medium: {数量}
  low: {数量}
fix_stats:
  todo: {数量}
  doing: {数量}
  done: {数量}
  skip: {数量}
review_skills:
  - {参与审查的 skill 列表}
---

# {审查标题}

## 概述

{一句话说明审查了什么，发现了什么级别的问题}

## 审查范围

- 模式: {full — 全量 | diff — 增量}
- 文件数: {n} 个
- 审查角度: {参与的 review skill 列表}

## 问题汇总

**修复状态**: `{open | in_progress | fixed | partial}`

| 级别 | 数量 | 已修复 | 修复中 | 待修复 | 跳过 |
|------|------|--------|--------|--------|------|
| CRITICAL | {n} | {n} | {n} | {n} | {n} |
| HIGH | {n} | {n} | {n} | {n} | {n} |
| MEDIUM | {n} | {n} | {n} | {n} | {n} |
| LOW | {n} | {n} | {n} | {n} | {n} |

## CRITICAL

### [{审查角度}] {问题概述}

**文件**: `{文件路径}:{行号}`
**问题**: {具体描述}
**建议**: {修复方向}
**状态**: `[todo]`

## HIGH

### [{审查角度}] {问题概述}

**文件**: `{文件路径}:{行号}`
**问题**: {具体描述}
**建议**: {修复方向}
**状态**: `[todo]`

## MEDIUM

### [{审查角度}] {问题概述}

**文件**: `{文件路径}:{行号}`
**问题**: {具体描述}
**建议**: {修复方向}
**状态**: `[todo]`

## LOW

### [{审查角度}] {问题概述}

**文件**: `{文件路径}:{行号}`
**问题**: {具体描述}
**建议**: {修复方向}
**状态**: `[todo]`

## 变更历史

| 日期 | 说明 |
|------|------|
| {YYYY-MM-DD} | 初始审查 |
