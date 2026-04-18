---
name: commit
description: |
  创建原子 git commit，包含验证、拆分建议和 conventional commit message。
  当用户说"提交"、"commit"、"commit一下"时触发。
---


# Commit

从当前工作区创建一个干净、可审查的 git commit。

**输入**: `$ARGUMENTS`

---

## 阶段 1 — 验证

如果 `$ARGUMENTS` 包含 `--no-verify`，跳过此阶段。

否则：

1. 从仓库根目录检测项目工具链。
2. 运行项目中实际存在的 test/lint/build 命令。
3. 失败时停止并报告，不继续提交。

仅运行项目中实际存在的命令。

---

## 阶段 2 — 暂存

检查当前状态：

```bash
git status --short
git diff --cached --stat
```

暂存规则：

1. 如果文件已暂存，使用已暂存的变更作为提交候选。
2. 如果没有暂存的文件，执行：

```bash
git add -A
```

3. 再次检查暂存的 diff：

```bash
git diff --cached --stat
git diff --cached
```

如果仍然没有暂存的变更，停止：`没有可提交的内容。`

---

## 阶段 3 — 分析

审查暂存的 diff，判断它是一个逻辑变更还是多个关注点的混合。

建议拆分的信号：

- 不同区域中不相关的功能或修复
- 源码变更混入了大范围的格式化改动
- 重构混入了行为变更
- 纯文档变更与代码变更无关
- 大量生成的文件更新混入手写代码

如果暂存的 diff 包含多个逻辑变更：

1. **不要**立即提交。
2. 自动按逻辑拆分为多个暂存分组。
3. 依次为每个分组生成提交消息并单独提交。

如果暂存的 diff 是一个内聚的变更，直接继续。

---

## 阶段 4 — 提交消息

生成 conventional commit 消息：

```text
<type>: <description>
```

允许的类型：

- `✨ feat` — 新功能
- `🐛 fix` — bug 修复
- `📝 docs` — 仅文档
- `♻️ refactor` — 不改变行为的结构调整
- `✅ test` — 仅测试
- `🔧 chore` — 工具、配置、依赖、维护
- `⚡ perf` — 性能优化
- `👷 ci` — CI/CD 变更

消息规则：

- 祈使语气
- 小写描述
- 不加句号
- 控制在 72 字符以内
- 描述改了什么，而不是实现步骤

示例：

- `✨ feat: add codex commit workflow prompt`
- `🐛 fix: handle empty staged diff before commit`
- `📝 docs: clarify codex sync behavior`

---

## 阶段 5 — 提交

先展示提议的消息和提交范围摘要。

然后提交：

```bash
git commit -m "<type>: <description>"
```

如果 hooks 或验证在此阶段失败，清晰报告失败原因，不要修改无关文件。

---

## 阶段 6 — 输出

报告：

- Commit hash
- 最终提交消息
- 变更文件数量
- 验证是否运行或跳过

建议的后续步骤：

- `git push`
- `/code-review`
