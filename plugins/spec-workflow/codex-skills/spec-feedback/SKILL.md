---
name: spec-feedback
description: 任务完成后向发起方反馈执行结果
---


任务完成后，向发起方的 tmux pane 反馈执行结果。

## 输入

目标 pane ID: $ARGUMENTS

## 执行步骤

1. 获取当前 pane ID:
   ```bash
   echo $TMUX_PANE
   ```
2. 从收到的 `[task from ...]` 标签中提取目标 pane_id（或使用 $ARGUMENTS 传入的 pane_id）
3. 生成反馈消息
4. 通过 tmux:tmux-send skill 发送到目标 pane

## 反馈格式

根据收到的原始任务消息类型附上设计上下文：

- **如果对方发送的是文档路径** → 引用路径
- **如果对方发送的是内联内容** → 原样附上

```
## 原始设计

{文档路径，或从 implement 发送过来的任务清单}

---

## 执行反馈

### 完成情况

- 已完成: {数量} 项
- 已跳过: {数量} 项
- 未处理: {数量} 项（如有）

### 跳过项说明

- {跳过的任务}: {原因}

### 遗留问题

- {未处理的问题说明}（如有）

---

使用 spec-workflow:spec-handle-feedback skill 检查以上反馈。

[feedback from {当前AI工具名称}, pane_id: {当前pane_id}: {执行结果简要描述}]
```

## 生成规则

- 完成情况必须量化
- 跳过的任务必须注明原因
- 如果全部顺利完成，跳过"跳过项说明"和"遗留问题"部分

## 发送方式

使用 tmux:tmux-send skill 发送。
