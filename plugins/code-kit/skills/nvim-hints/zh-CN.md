---
name: nvim-hints
description: |
  在用户正在运行的 Neovim 实例中可视化标注代码链路——用 quickfix 列表按执行顺序列出调用路径的每一步，并在每个位置行尾添加 virtual text 说明。
when_to_use: |
  当用户给出 nvim socket 路径，或提到「梳理链路」「调用链」「调用路径」「在 nvim 里标记/标注」「qflist」「quickfix」「virtual text」，或想看某个请求/函数在代码里怎么一路走下来时触发——即使用户没有明确说「标注」二字。
---

# nvim-hints：在 Neovim 中标注代码链路

把代码链路分析结果直接送进用户正在使用的 Neovim：quickfix 列表承载「按执行顺序排列的步骤清单」（可用 `:cnext`/`:cprev` 逐步跳转，默认快捷键 `]q`/`[q`），virtual text 承载「每一步在做什么」的行内说明。用户不用离开编辑器就能顺着链路走一遍。

## 工作流程

### 1. 拿到 socket

socket 由用户提供（形如 `/run/user/1000/nvim.12345.0` 或 `/tmp/nvim.sock`）。如果这次对话里用户还没给，就先问。拿到后立刻验证连通性：

```bash
python3 scripts/nvim_hints.py check <socket>
```

`check` 会顺带返回 nvim 当前打开的文件和工作目录——这往往就是用户关心的代码所在位置，可以作为分析起点的线索。

### 2. 分析链路

用平时的手段（Grep、Read、LSP 等）把用户要的链路梳理清楚。两点要求：

- **行号必须新鲜准确**。virtual text 和 qflist 都锚定到具体行号，行号错一行，标注就贴到无关代码上，比不标还糟。确定每个步骤的行号时，要基于刚刚 Read 过的文件内容，不要凭 grep 的模糊印象或记忆中的旧行号。
- **每步选「最能代表该步骤」的那一行**。通常是函数定义行，或发起下一步调用的那一行调用语句。一个链路步骤只标一行，不要把整个函数体撒满标注。

### 3. 生成 hints.json

写到 scratchpad 目录，格式：

```json
{
  "title": "支付创建链路",
  "items": [
    {
      "file": "/abs/path/handler.go",
      "line": 42,
      "text": "1. HandleCreatePayment — HTTP 入口",
      "hint": "① 解析请求，校验参数后交给 service 层"
    },
    {
      "file": "/abs/path/service.go",
      "line": 108,
      "text": "2. PaymentService.Create — 业务编排",
      "hint": "② 开启事务，依次调用风控与账务"
    }
  ]
}
```

- `items` 按**执行顺序**排列（这就是用户在 quickfix 里 `:cnext` 走的顺序），不要按文件顺序。
- `text` 是 quickfix 列表里的一行：以序号开头，给出符号名和一句话定位（如「HTTP 入口」「业务编排」），让用户扫一眼列表就能看懂整条链路的骨架。
- `hint` 是行尾 virtual text：说明这一步「做了什么、为什么走到下一步」。控制在 40 字以内——过长会被窗口截断。省略 `hint` 时会退回用 `text`。
- 分叉链路（一处调用走向多个分支）也能表达：让序号带层级，如 `3a.`、`3b.`，并在 `text` 里说明分支条件。
- `file` 用绝对路径。文案语言跟随当前对话语言。

### 4. 应用

```bash
python3 scripts/nvim_hints.py apply <socket> <hints.json>
```

脚本会自动：清空上一次的全部标注（namespace `claude_hints`）→ 加载涉及的 buffer 并打上 virtual text → 用新列表替换 qflist → `copen` 打开 quickfix 窗口（焦点留在原窗口）。输出形如 `applied 5 hints`；若有文件不存在或行号越界会附带说明——出现这种情况说明第 2 步的分析有误，回去修正后重新 apply，不要放着不管。

### 5. 汇报

向用户简要总结链路（几步、从哪到哪），并提醒操作方式：quickfix 窗口里回车跳转，`]q`/`[q`（即 `:cnext`/`:cprev`）顺链路走，想清除标注时说一声即可（执行 `python3 scripts/nvim_hints.py clear <socket>`）。

## 注意事项

- 每次 apply 都会先清空旧标注，所以同一会话里多次梳理不同链路无需手动清理；用户明确要求「清掉」时用 `clear` 子命令。
- 用户可能在分析期间编辑了文件。如果距离上次 Read 已隔了较多操作，apply 前重新确认关键行号。
- 不要用 `--remote-send` 向 nvim 发送按键——那会干扰用户当前的编辑状态。所有交互都通过本技能的脚本（内部用 `--remote-expr`）完成。
- 标注只存在于运行中的 nvim 会话内存里，不会修改任何文件。
