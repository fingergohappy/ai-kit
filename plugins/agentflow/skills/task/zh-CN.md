---
name: task
description: |
  将需求整理为结构化任务文档（功能设计、变更提案或任务描述）。输出到 docs/tasks/。
when_to_use: |
  当用户说「整理下」「总结下」「写个文档」「生成任务」「讨论新功能」「代码变更」「任务规划」时触发。
argument-hint: "[任务名称]"
model: opus
disable-model-invocation: false
---

# task

将需求讨论整理为结构化的任务文档，让后续实现有据可依。

## Document Types

根据对话内容自动判断（`references/` 路径相对于本 zh-CN.md 所在目录）：

| 类型 | 判断依据 | 模板 | 输出文件名 |
|------|---------|------|-----------|
| feature | 讨论新功能、新能力、新模块 | [feature_template.md](references/feature_template.md) | `{名称}_feature.md` |
| change | 讨论重构、API 变更、破坏性改动 | [change_template.md](references/change_template.md) | `{名称}_change.md` |
| task | 通用任务、不属于以上两类 | 无固定模板，自由格式 | `{名称}_task.md` |

如果无法判断，默认为 task 类型。

## Two Modes

### Mode A: Discussion Mode（对话开头触发）

如果在对话开头触发此 skill，进入讨论模式：

- **只讨论，不修改代码** — 这个阶段的目标是把需求想清楚，不是写代码
- 根据类型引导讨论：
  - feature：背景、核心概念、核心流程、关键机制、接口定义
  - change：变更动机、影响范围、变更清单、兼容性考虑
  - task：目标、范围、步骤、验收标准
- 可以阅读现有代码来理解上下文，但不做任何修改
- 当用户说"生成文档"、"输出文档"、"写下来"之类的指令时，执行文档生成

### Mode B: Direct Generation（对话中途触发）

如果在对话中途触发（对话中已有讨论内容）：

- 直接总结已有对话，生成文档
- 跳过引导讨论环节

## Determination Method

- 对话刚开始、之前没有实质性的讨论 → 模式 A
- 对话中已经讨论过方案、有足够上下文 → 模式 B

## Document Generation Steps

1. 若 $ARGUMENTS 为空，根据对话内容自动生成一个简明的任务名称
2. 判断文档类型（feature / change / task）
3. 如果是 feature 或 change，读取对应模板，填入内容
4. 如果是 task，用自由格式生成，至少包含：目标、范围、任务清单、验收标准
5. 自动填充元数据:
   - `title`: $ARGUMENTS（任务名称）
   - `type`: feature / change / task
   - `date`: 当前日期 (YYYY-MM-DD)
   - `status`: `draft`
   - `version`: `"1.0"`
   - `summary`: 从对话中提取 1-2 句目的
   - `scope`: 列出涉及的文件/模块路径
6. 输出到项目根目录下 `docs/tasks/{名称}_{类型}.md`
   - 如果 `docs/tasks/` 目录不存在，先创建
   - 文件名使用英文，单词间用下划线连接
   - 生成完成后告知用户文件的完整路径

## Generation Rules

- 任务清单必须使用 checkbox 格式（`- [ ]`），方便逐条勾选完成状态
  - 未完成：`- [ ] 任务描述`
  - 已完成：`- [x] 任务描述`
  - 跳过：`- [skip] 任务描述 — 原因`
- 模板占位符 `{xxx}` 必须全部替换，不能残留
- 代码示例用项目实际语言
- 文件路径必须反映实际代码路径，方便后续用 gate-review skill 对照
- 对话中未涉及的内容，根据已有代码上下文推断补充
- 如果某个 section 确实无法填充，保留标题并注明原因（"待讨论" 或 "待确认"）

## Next Steps

文档生成后，用户可以：
- 调用 dispatch skill 将任务派发给接收端执行
- 调用 gate-review skill 在本地自检代码实现
