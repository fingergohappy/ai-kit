---
name: spec-implement
model: haiku
description: |
  将设计文档发送到指定 tmux pane 执行。
  执行完成后会通过 spec-feedback 反馈结果。
  当用户说"发过去"、"send 过去"、"开始干"、"implement"时触发。
argument-hint: [文档路径, 如 docs/spec/xxx_feature.md]
context: fork
---

将设计文档发到指定 tmux 窗口执行。

## 输入

$ARGUMENTS

## 执行步骤

1. 获取当前 pane ID:
   ```bash
   echo $TMUX_PANE
   ```
2. 确定目标 pane_id:
   - 如果 $ARGUMENTS 中指定了 pane_id（格式如 `@pane_id` 或 `pane_id:`），使用指定的 pane_id
   - 如果未指定，列出可用 pane 供用户选择：
     ```bash
     tmux list-panes -F "#{pane_id}: #{pane_current_command} [#{pane_width}x#{pane_height}]"
     ```
3. 读取 $ARGUMENTS 中指定的文档路径，如果参数不是文件路径，则将参数内容作为内联任务发送
4. 如果文档有 frontmatter，将 `status` 从 `draft` 改为 `doing`
5. 严格按照下面的格式生成消息
6. 通过 tmux-send skill 发送到目标 pane

## 发送格式

### 如果是文档路径：

```
请按照以下设计文档实现：{文档路径}

完成每个任务后，将文档中对应的"实现状态"从 [todo] 更新为 [done]。
如果某个任务跳过，更新为 [skip] 并注明原因。

---

执行完成后，调用 spec-feedback skill 向 pane {当前pane_id} 反馈结果。

[task from {当前AI工具名称}, pane_id: {当前pane_id}: {简要描述}]
```

### 如果是内联任务内容，直接将 $ARGUMENTS 内容发送，末尾附加：

```
---

执行完成后，调用 spec-feedback skill 向 pane {当前pane_id} 反馈结果。

[task from {当前AI工具名称}, pane_id: {当前pane_id}: {简要描述}]
```

## 发送方式

使用 tmux-send skill 发送。
