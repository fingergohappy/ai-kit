---
cr: {{CR}}
stage: {{STAGE}}                   # docs | spec | impl
status: to fix                     # to fix | fixing | fixed
verdict:                           # BLOCK | OK with notes | OK
base: {{BASE}}                     # 审的是哪个 commit
reviewer: "{{REVIEWER}}"
date: {{DATE}}
distilled: false                   # CR fixed 后由 /review-cr distill 改成 [L-3, L-4] 或 "无可提炼: 理由"
---

# {{CR}} review: {{STAGE}}

<!-- 审查对象按阶段: docs = CR + 受影响 REQ 的 delta (+ 草稿); spec = 实施 spec;
     impl = 代码 vs spec vs CR 的 AC. 车道清单与每条要问的问题见 sdd/references/review-lanes.md.
     没有发现也要出这份文件 (状态直接 fixed), 否则无法区分 "审过没问题" 和 "没审". -->

## 车道结论

| 车道 | 结论 | 一句话 |
|---|---|---|
| | BLOCK / OK with notes / OK | |

## 发现

<!-- 编号 {{PREFIX}}-1, {{PREFIX}}-2 ... (docs=D, spec=S, impl=I), 一个 CR 内唯一, 跨文档引用写
     "{{CR}} {{PREFIX}}-1". 级别: P0 = 不修不能合并 (错误放行, 超付, 卡死队列, 审计缺失);
     P1 = 应修; P2 = 建议.
     每条发现必须能被别人复现或核对: 位置给 file:line (或 REQ / CR 条目号), 发现里写证据
     (代码怎么写的, 与哪条 AC / BR 冲突), P0 附复现步骤 (放在下方 "附" 里). 没有证据的
     怀疑写成 P2 并注明 "未核实". 最小修复给具体改法, 不写 "考虑改进".
     处置列由 /implement-cr 填: "修复 <提交>" / "接受风险: <理由>" / "不采纳: <理由>" / 待修.
     复核列由复审填: "已核 <日期>" / "未修复: <说明>". -->

| 编号 | 级别 | 车道 | 位置 | 发现 | 最小修复 | 处置 | 复核 |
|---|---|---|---|---|---|---|---|
| {{PREFIX}}-1 | P0 | | | | | 待修 | |

## 测试缺口

<!-- spec / impl 阶段: 哪条 AC 没有测试, 哪个测试断言不到位 (同一事务里测并发等). -->

| AC / 场景 | 缺口 | 对应发现 |
|---|---|---|

## 附: 复现步骤与证据

<!-- 每条 P0 一小节: 编号做标题, 步骤 1 2 3, 预期 vs 实际. 引用的 SQL / 代码片段贴关键几行. -->
