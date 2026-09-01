# 从 OpenSpec 借了什么, 没借什么

对照对象: https://github.com/Fission-AI/openspec (`openspec/` 两目录: `specs/` 真相 + `changes/`
变更文件夹, 每个变更 proposal / specs delta / design / tasks, 归档时 delta 并入 specs).

## 借了

| OpenSpec | 这里 | 说明 |
|---|---|---|
| 一个变更一个文件夹 | `notcommit/CR-NNN-<slug>/` | 草稿, spec, 三次 review 同处, 不散落 |
| `openspec status` / `instructions --json`: 由文件状态推下一步 | `sdd.py status CR-NNN` 的 "下一步"; `/implement-cr` 按状态决定做什么 | 状态在文件里, 不在记忆里 |
| `openspec validate --strict` | `sdd.py validate` | 条目引用存在性, CR fixed 的三件事, review fixed 无未处置, 链接可解析, INDEX 过期 |
| `openspec list` | `sdd.py index` 生成 INDEX.md | 索引是生成物, 消掉一处手工同步 |
| `/opsx:explore`: 只读的思考伙伴, 不写代码 | `/draft` | 想清楚再立 CR; 草稿必须带代码事实 |
| brownfield-first: spec 描述系统**现在**的行为 | `/req` 先收集旧的业务逻辑 | REQ 是当前功能的结论 |
| REMOVED 必须写 Reason + Migration | CR 变更内容表: 删除条目写原因与存量处置 | 没有迁移说明的删除让在途数据无处安放 |
| propose 的 "planning boundary": 规划命令不写代码 | `/draft` `/req` `/create-cr` `/review-cr` 都不改项目代码 | 只有 `/implement-cr` 动代码 |
| apply 的 "pause if": 任务不清 / 设计有问题 / 范围被迫扩大时停下来问, 不默默吸收 | `/implement-cr` 同款规则 | 尤其 "被迫放宽或跳过某条 AC 才做得下去" 必须上报 |
| verify 的三维度 (完整 / 正确 / 一致) 与 CRITICAL / WARNING / SUGGESTION | `03-impl` 的车道 A / B / D 与 P0 / P1 / P2 | 资金系统另加金融安全与合规两条车道 |
| 模板 + 每个 artifact 的 instruction | `assets/templates/*.md` 的 HTML 注释 | AI 写之前先读该节怎么写 |
| "re-read from disk, not from conversation memory" | 各命令开头都重读文件 | 用户可能在会话中间改了文档 |
| skills 跨 30+ 工具: SKILL.md 只用 name / description | 本 skill 集同样, 安装到 `.claude/` `.agents/` `.pi/` | Codex / pi 可用 |

## 没借 (以及为什么)

| OpenSpec | 不借的原因 |
|---|---|
| `### Requirement: <标题>` + `#### Scenario: WHEN/THEN`, 标题即主键 | 这里的 FR / BR / AC 编号更强: 稳定, 可被 CR / review / 测试逐条引用; 标题匹配一改措辞就断. 资金规则多是不变量与算术, WHEN/THEN 写不出 "快照余额 - 在途 - 占用 - 安全垫 >= 总借记" |
| `tasks.md` 勾选清单 | 勾是自述, 不可验证; 这里 spec §4 的落点列填提交 hash, git log 即进度. 多代理并行时共享勾选文件还是冲突源 |
| 归档时 delta 自动并入 specs | REQ 在 `/implement-cr` 落实阶段由人 / AI 通读更新, 配 validate 检查 "CR fixed 则 REQ 变更记录有行"; 自动合并对编号条目不适用 |
| "enablers not gates", 大多数变更停在 lite spec | 出金 / 合规链路需要闸门; 三次 review 是软闸门, 跳过要人明确说. 轻量路径是: 不走 CR 的东西停在 `/draft` |
| CLI 生成 30 种工具的 command 文件 | 只做 skills, 用 `install.sh` 链接三个目录; 命令文件是各工具的 slash 糖, 不值得维护 |
| Stores (跨仓共享规划仓) | 单仓阶段不需要 |
| specs 里禁止出现表 / 字段 | REQ 第 7 节专门登记数据影响 (幂等键, 唯一约束是业务规则的一部分); FR / BR 正文仍不写表字段 |
