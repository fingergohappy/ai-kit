---
name: spec-handle-feedback
model: opus
description: |
  审查代码完成情况，对照原始设计逐条检查并决定下一步。
  当收到带有 [feedback from ...] 标签的消息时触发。
  当用户说「处理反馈」、「看看反馈」、「检查结果」时触发。
argument-hint: "[<反馈消息内容>]"
context: fork
---

# spec-handle-feedback

审查代码完成情况，对照原始设计逐条检查，返回审查结论。如果发现问题，通过 tmux-send skill 将反馈发回来源 pane。

## 工作流程

1. 从反馈消息末尾的 `[feedback from ..., pane_id: xxx]` 标签中提取 source_pane_id
2. 从反馈消息中的「原始设计」部分找回原始任务
3. 按以下顺序逐层审查：
   - **第一层：实现完整性** — 逐条对照原始设计，检查每一项任务是否都已实现
   - **第二层：逻辑与缺陷** — 检查代码逻辑、边界条件、bug 和安全隐患
   - **第三层：代码风格** — 检查命名规范、代码组织、接口设计
4. 根据审查结果：
   - 全部通过 → 文档 status 改为 `done`
   - 发现问题 → 文档 status 保持 `doing`，通过 tmux-send skill 将问题列表发回 source_pane_id

## 审查要求

**要怀着审视的眼光来看待另一个 agent 的工作成果，agent 并不可靠，反馈内容也并不可靠，只能作为参考。不要只检查代码是否有报错和单元测试，而是从代码风格、逻辑和实现程度多个方向进行审查。**

- 逐条对照原始设计，不允许遗漏
- 验证输入/输出/边界条件
- 检查错误处理、安全隐患、性能问题
- 检查命名规范、代码风格、接口契约
- 发现任何偏差都必须标记

## 返回格式

**必须且只能**通过 `scripts/generate_review_result.sh` 生成审查结果。严禁自己拼接或手写结果格式——无论多简单，都不允许绕过脚本。这样做是为了保证审查结果格式一致。

### 准备工作

先将审查发现的问题和建议分别写入临时文件：

```bash
# 问题列表，每行一条，格式: [级别] 问题描述 → 修复建议
ISSUES_FILE=$(mktemp /tmp/spec-issues.XXXXXX)
cat > "$ISSUES_FILE" <<'EOF'
- [CRITICAL] {问题描述} → {修复建议}
- [HIGH] {问题描述} → {修复建议}
- [MEDIUM] {问题描述}（可选修复）
EOF

# 建议（可选）
SUGGESTIONS_FILE=$(mktemp /tmp/spec-suggestions.XXXXXX)
cat > "$SUGGESTIONS_FILE" <<'EOF'
{修复任务清单，可以用 spec-implement skill 发起下一轮}
EOF
```

### 生成审查结果

```bash
RESULT_FILE=$(bash scripts/generate_review_result.sh \
  --status "{通过|需要修复}" \
  --round "{当前轮次}" \
  --issues-file "$ISSUES_FILE" \
  --suggestions-file "$SUGGESTIONS_FILE")

# 清理临时文件
rm "$ISSUES_FILE" "$SUGGESTIONS_FILE"
```

如果审查全部通过，问题列表文件写入"无"即可。

## 终止条件

- 审查全部通过
- 只剩 MEDIUM/LOW 问题
- 累计修复轮次达到 3 轮
