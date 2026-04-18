# spec-workflow

Spec-driven workflow plugin — design docs, code review, and feedback loop via tmux.

## 功能

通过结构化的设计文档驱动开发流程，协调多个 tmux pane 之间的任务分发、代码审查和反馈闭环。

| Skill | 说明 |
|-------|------|
| `spec-feature` | 从讨论中生成功能设计文档，输出到 `docs/spec/` |
| `spec-change` | 从讨论中生成变更文档（重构、API 变更等），输出到 `docs/spec/` |
| `spec-implement` | 将设计文档发送到指定 tmux pane 执行 |
| `spec-feedback` | 任务完成后向发起方反馈执行结果 |
| `spec-handle-feedback` | 审查代码完成情况，对照原始设计逐条检查并决定下一步 |
| `spec-review` | 对照设计文档审查代码实现，生成审查报告 |
| `spec-fix-review` | 将审查报告发送到指定 tmux pane 执行修复 |
| `spec-check-review` | 验证审查报告准确性并修复代码 |

## 工作流

```
1. 设计阶段
   /spec-feature <功能名>        # 讨论需求，生成设计文档

2. 实现阶段
   /spec-implement <文档路径>    # 发送到另一个 pane 执行

3. 反馈阶段
   实现方完成后调用 spec-feedback 反馈结果

4. 审查阶段
   /spec-handle-feedback         # 审查完成情况，决定通过或继续修复
```

## 安装

### Claude Code

注册插件市场后安装：

```
/plugin marketplace add fingergohappy/ai-kit
/plugin install spec-workflow@ai-kit
```

安装后重启 Claude Code，skills 以 `spec-workflow:` 前缀调用：

```
/spec-workflow:spec-feature login-system
/spec-workflow:spec-implement docs/spec/login_feature.md
```

### 本地开发

```bash
claude --plugin-dir /path/to/ai-kit/plugins/spec-workflow
```

## 依赖

- tmux（多 pane 协作）
- 各 pane 中运行 Claude Code 或其他 AI 编码工具

## License

MIT
