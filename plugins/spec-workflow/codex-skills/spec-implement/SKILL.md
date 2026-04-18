---
name: spec-implement
description: |
  将设计文档发送到指定 tmux pane 执行。
  执行完成后会通过 spec-workflow:spec-feedback 反馈结果。
  当用户说"发过去"、"send 过去"、"开始干"、"implement"时触发。
---


将设计文档发到指定 tmux 窗口执行。

## 输入

$ARGUMENTS

## 执行步骤

1. 获取当前 pane ID:
   ```bash
   echo $TMUX_PANE
   ```
2. 读取 $ARGUMENTS 中指定的文档路径，如果参数不是文件路径，则将参数内容作为内联任务发送
3. 如果文档有 frontmatter，将 `status` 从 `draft` 改为 `doing`
4. 按下面的格式生成消息
5. 通过 tmux:tmux-send skill 发送

## 发送格式

如果是文档路径：

```
请按照以下设计文档实现：{文档路径}

完成每个任务后，将文档中对应的"实现状态"从 [todo] 更新为 [done]。
如果某个任务跳过，更新为 [skip] 并注明原因。

---

执行完成后，调用 spec-workflow:spec-feedback skill 向 pane {当前pane_id} 反馈结果。

[task from {当前AI工具名称}, pane_id: {当前pane_id}: {简要描述}]
```

如果是内联任务内容，直接将 $ARGUMENTS 内容发送，末尾附加：

```
---

执行完成后，调用 spec-workflow:spec-feedback skill 向 pane {当前pane_id} 反馈结果。

[task from {当前AI工具名称}, pane_id: {当前pane_id}: {简要描述}]
```

## 发送方式

使用 tmux:tmux-send skill 发送。
