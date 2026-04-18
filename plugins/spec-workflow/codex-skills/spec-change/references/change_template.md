---
title: {变更名称}
type: change          # breaking / compatible / refactor
date: {YYYY-MM-DD}
status: draft          # draft → review → final
version: "1.0"
summary: {1-2 句说明变更目的}
scope:
  - {涉及的文件/模块路径}
changes:
  - action: change | new | delete
    target: {文件路径}
    desc: {变更概述}
---

# {变更名称}

## 概述

{一句话说明要变更什么}

## 变更动机

{为什么要改，不改会怎样}

## 变更清单

变更类型: `[change]` 修改现有代码 | `[new]` 新增文件/类型/方法 | `[delete]` 删除文件/类型/方法

### [change] `{文件路径}` — {变更概述}

#### 变更思路

{描述为什么要改、怎么改}

#### 变更内容

```
// {TypeName}
{变更后的类型定义}

// {MethodName}
{变更后的方法签名}
```

- `{TypeName}`: {变更了什么、为什么}
- `{MethodName}`: {变更了什么、为什么}

#### 实现状态 [todo/doing/done/skip]

{描述实现结果}

### [new] `{文件路径}` — {新增概述}

#### 设计思路

{描述为什么新增、设计意图}

#### 新增内容

```
// {TypeName}
{类型定义}

// {MethodName}
{方法签名}
```

- `{TypeName}`: {职责和设计意图}
- `{MethodName}`: {逻辑和调用时机}

#### 实现状态 [todo/doing/done/skip]

{描述实现结果}

### [delete] `{文件路径}` — {删除概述}

#### 删除原因

{描述为什么可以安全删除、影响范围}

#### 删除内容

- `{TypeName}`: {原来做什么}
- `{MethodName}`: {原来做什么}

#### 实现状态 [todo/doing/done/skip]

{描述实现结果}

## 变更历史

| 版本 | 日期 | 状态 | 说明 |
|------|------|------|------|
| 1.0 | {YYYY-MM-DD} | draft | 初始版本 |
