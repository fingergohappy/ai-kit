# 约定: 需求 / 变更 / 实施 / review

本文是 sdd 工作流的唯一约定来源, 只存在于 skill 里, 不复制进项目 (两份必漂移).
项目侧的 `docs/sdd/` 是业务逻辑的唯一现行事实来源, 以及它如何演化到今天的审计轨迹.
工作流由六个命令驱动: `/draft` `/req` `/create-cr` `/spec` `/implement-cr` `/review-cr`;
`/auto-cr` 是它们的无人值守编排 (CR 立好之后一路推到落实前, review 派给别的 agent 并行);
`/sdd` 看状态与下一步. 作为 ai-kit 插件安装时命令带前缀 (`/sdd:draft`), 本文一律写无前缀形式. 确定性的部分 (编号, 建文件, 校验, 索引) 由 `sdd.py` 做.

## 目录

```
docs/sdd/
├── INDEX.md                  # 由 sdd.py index 生成, 不手工维护
├── lessons.md                # 错题本: 从已 fixed 的 review 提炼的模式 (入库, 长期)
├── req/REQ-NNN-<slug>.md     # 业务逻辑: 当前功能的结论 (入库)
├── cr/CR-NNN-<slug>.md       # 一次工作单元 (入库): 变更 CR 写改哪些条目, 立项 CR 写新业务交付什么
└── notcommit/                # 不入库 (整体 .gitignore)
    ├── <slug>/draft/         # 还没立 CR 时的草稿 / 侦察记录
    └── CR-NNN-<slug>/        # 立 CR 后的工作目录 (草稿目录自动并入)
        ├── draft/            # 提案 / 变更草稿
        ├── spec.md           # 实施 spec: 改哪里, 按什么顺序, 怎么测, 怎么上线
        └── reviews/          # 三次 review (CR fixed 后提炼进 lessons.md, 然后删除)
            ├── 01-docs.md    #   CR + REQ delta (写 spec 之前)
            ├── 02-spec.md    #   实施 spec (写代码之前)
            └── 03-impl.md    #   实现 (落实 REQ 之前)
```

## 三份文档各写什么

| 文档 | 写什么 | 不写什么 |
|---|---|---|
| REQ | **当前功能的结论**: 逐条编号的规范文本 (FR / BR / AC), 每条可验收 | 为什么定成这样, 推导, 复现, file:line, 否决过的方案 |
| CR | 为什么原需求不再成立; 按条目号写 delta (现行 -> 变更后); 影响; 否决的替代方案 | 实现步骤 |
| spec | 改哪里 (侦察, file:line), 顺序, 测试, 上线, 实际落点 | 业务规则 (引用 REQ 条目号) |
| review | 发现 (带证据与复现), 处置, 复核 | -- (过程产物, 提炼后删除) |
| lessons | 从 review 提炼的模式: 犯了什么错, 怎么识别, 以后怎么做, 犯过几次 | 具体发现的原文, 一次性笔误 |

判别 "这句话该放 REQ 还是 review": **能不能被验收**. "费率组合上限 90%" 可验收, 进 REQ;
"90% 来自反向搜索步数 <= 30 的推导" 不可验收, 留在 review, REQ 只在变更记录里指过去.
反过来: review 的结论一旦被接受, 必须落成 REQ 的编号条款才算生效; 只在 review 里写着而
REQ 没有对应条目的, 视为未采纳.

## 文档头部: YAML frontmatter

每份 REQ / CR / spec / review / draft 的状态写在文件最前面的 frontmatter 里 (`---` 之间), 不写在正文表格.
这样任何工具 (脚本, Obsidian, 静态站点, 别的 agent) 都能可靠读到, 不用去正则匹配表格行.

| 文档 | 字段 |
|---|---|
| REQ | `id` `status` `created` `updated` `related` `summary` |
| CR | `id` `kind` (change / charter) `status` `created` `affects` `summary` |
| spec | `cr` `base` (侦察基点 commit) `created` `updated` |
| review | `cr` `stage` `status` `verdict` `base` `reviewer` `date` `distilled` |
| draft | `topic` `date` `key` `kind` |

`affects` 是列表, 每项 `REQ-NNN (FR-x, AC-y)`; 立项 CR 写 `REQ-NNN (全文)`.
`distilled`: 未提炼写 `false`, 已提炼写 `[L-3, L-4]`, 无可提炼写 `"无可提炼: 理由"`.

**写值的一条硬规矩**: 值里只要有 `": "` (中文标点后跟空格也算), 或以 `[ { & * ! | > % @ \`` 开头,
就必须加引号或写成 `>-` 块标量 -- 否则标准 YAML 解析器会把它读成嵌套映射 (pi 就是这样报错的).
`summary` 一律用 `>-`. `sdd.py validate` 会扫出这类值并警告.

```yaml
---
id: CR-004
kind: change
status: fixed
created: 2026-08-27
affects:
  - REQ-006 (FR-8, BR-19, AC-8)
  - REQ-002 (FR-7, AC-11)
summary: >-
  安全垫从部署级环境变量改为运行时设置白名单键, 闸门每次判定现读免重启
---
```

标题仍写在正文的 h1 (`# CR-004: 余额闸门安全垫改为落库热配置`), frontmatter 不重复放,
省得两处漂移. 链接也不进 frontmatter (`related` / `affects` 只写编号), 正文里引用时才写链接 --
路径调整时不用改一堆头部.

## 编号与引用

- `REQ-NNN` / `CR-NNN` 各自全局递增, 永不复用, 文件名 `<编号>-<slug>.md`, slug 小写短横线.
- REQ 内条目: `FR-n` 功能需求, `BR-n` 业务规则, `AC-n` 验收标准 (标注来源 FR / BR).
  **条目号一旦发布不重排**: 内容改了 FR-5 仍叫 FR-5, 删除保留编号并标 "已删除, 见 CR-NNN",
  新增续编当前最大号. CR 与 review 都按条目号引用, 编号稳定是整套体系能互相引用的前提.
- review 内发现: `D-n` (docs) / `S-n` (spec) / `I-n` (impl), 一个 CR 内唯一.
  跨文档引用写 `CR-005 I-3`, 不写路径 (notcommit 不入库, 路径在别的机器上不成立).
- 引用其它 REQ 连条目号一起写 ("REQ-002 BR-17"), 不写 "见汇出需求".

## 状态

```
REQ:    draft -> implemented -> superseded | retired
CR:     to fix -> fixing -> fixed        (决定不做: rejected, 在落实一节写原因)
review: to fix -> fixing -> fixed -> (CR fixed 后) 提炼进 lessons.md -> 删除   (没有发现: 直接 fixed)
```

- CR `to fix`: 写好了, 还没开工. `fixing`: `/implement-cr` 已开始 (代码 / review 处理中).
  `fixed`: 代码就绪, 三次 review 都 fixed, REQ 已更新到新结论, 变更记录已追加.
- review `fixed` 的含义是每条发现都有处置 (修复 <提交> / 接受风险 <理由> / 不采纳 <理由>),
  不是 "都修了". 接受与不采纳必须有理由, 复核人可以推翻.
- 时间锚点是代码库不是上线: REQ 更新与实现同分支同提交, 合并瞬间文档与代码一致.
- notcommit 的工作目录不长期保存: CR fixed 后 `/review-cr CR-NNN distill` 把处置为 "修复" 的发现归并成模式写进
  `lessons.md` (同模式只累加次数), review 的 `distilled` 填上 L 编号, 再盘点 `CR-NNN-<slug>/` 里的
  draft/ spec.md reviews/, **与用户确认哪些删**, 用 `sdd.py prune` 执行 (`--keep` 保留某项). 三样都是过程产物: 草稿在 docs review 里已被当证据核过
  (见 review-lanes 车道 A), 结论进了 CR 与 REQ; spec 的落点已写进 CR 第 5 节. CR 不动 --
  它是业务文档, 工程教训不进去, 反查靠 lessons.md 的来源列. 之后的 review 与实施都先读错题本,
  次数 >= 2 的必查.

## 流程

```
/draft <slug>          想清楚 (只读代码, 不写代码)           -> notcommit/<slug>/draft/
/req <slug>            写 REQ: 已有业务收集现行逻辑,         -> req/REQ-NNN-<slug>.md
                       全新业务写本期目标形态 (draft)
/create-cr <slug>      立 CR: 有 REQ 写 delta, 无则立项      -> cr/CR-NNN-<slug>.md   [to fix]
/review-cr CR-NNN docs 审 CR + REQ delta                     -> reviews/01-docs.md
/spec CR-NNN           写实施 spec (先侦察 file:line)         -> notcommit/CR-NNN-*/spec.md
/review-cr CR-NNN spec 审实施计划                             -> reviews/02-spec.md
/implement-cr CR-NNN   按 spec 分步实施 (TDD), 每步一提交, 填落点   [CR: fixing]
/review-cr CR-NNN impl 审实现                                 -> reviews/03-impl.md
/implement-cr CR-NNN   落实: 更新 REQ 正文 + 变更记录, CR 置 fixed, 重生成 INDEX
/review-cr CR-NNN distill  提炼教训进 lessons.md, 清理工作目录      -> lessons.md   [notcommit/CR-NNN-* 删除]
```

`/implement-cr` 是 "做下一件事": 它先看状态 -- 有未处置的 review 发现就先处理, 有待办步骤就实施,
都齐了就落实 (没 spec 时它让你去 `/spec`). `/sdd` 或 `sdd.py status CR-NNN` 告诉你下一步是什么.

六个命令里只有 `/implement-cr` 会改项目代码 (`/auto-cr` 内含它); `/draft` `/req` `/create-cr` `/spec` `/review-cr`
都只读代码, 只写文档 -- 想只要方案不要改动时, 停在 `/spec` 即可.

review 是软闸门: 跳过某次 review 直接往下走需要人明确说 "跳过", AI 不自行跳过.

## 两种 CR: 变更与立项

每一次实现都经过 CR -- 它是工作单元, spec 与三次 review 都挂在它的目录下. 按目标业务有没有
现行 REQ 分两种形态, 编号共用一个序列, 后续步骤完全一样:

| 形态 | 何时 | 模板 | 怎么建 |
|---|---|---|---|
| **变更 CR** | 业务已有 implemented 的 REQ, 要改它的行为 | `cr.md` | `/create-cr <slug>` |
| **立项 CR** | 全新业务, 还没有 REQ | `cr-new.md` | 先 `/req <slug>` 建 draft REQ, 再 `/create-cr <slug>` (脚本 `new-cr --new`) |

差别只在第 1-3 节: 变更写 "为什么原需求不再成立" 与按条目号的 "现行 -> 变更后"; 立项写
"为什么现在做", "本期交付范围", "对现有系统的影响" -- 最后一节是新业务最容易漏的, 写新功能的人
往往只盯着新代码, 而翻车多在与现有系统的接触面 (共享表约束, 同一把锁, 队列争用, 幂等键空间,
路由冲突, 回退路径).

全新业务的 REQ **只描述本期要交付的形态**: 想好但本期不做的能力写进第 2 节非目标 (叙述, 不编号),
或等下次变更 CR 再加编号条目. 不要写了编号条目却不实现 -- implemented 的 REQ 里未带标注的条目
即已实现, 两者矛盾 (validate 会拦).

立项 CR 不是对 draft REQ 的变更管控 (draft 阶段的 REQ 本来就随便改), 是为了有地方挂 spec 与 review,
并留下 "为什么做, 交付到哪" 的记录. CR fixed 时 REQ 置 implemented, 其变更记录首行写明由该 CR 立项.

判断要不要 CR: 验收标准会不会变, 会变就要. 纯排版 / 错别字 / 措辞订正直接改 REQ,
在变更记录追一行写 "未改变既定行为".

**整份 REQ 退役也走 CR**, 不另设归档目录. 业务下线或被新 REQ 取代时开一个变更 CR, 变更内容表把
FR / BR / AC 逐条写成 "删除" 并给出原因与存量处置; CR fixed 时把 REQ 状态置 `retired` (业务没了) 或
`superseded` (被别的 REQ 取代 -- 在变更记录里写明由谁取代), 变更记录追一行指回该 CR.
文件留在 `req/` 不挪走: 编号被 CR 的影响需求, 其它 REQ 的 `related`, lessons.md 的来源列引用着, 挪走全断,
而 REQ 的演变历史本来就由 CR 链承载, 归档目录是多余的一层. 退役后在 INDEX 里靠状态列区分.
删除的条目按第 4 节的规矩保留编号标 "已删除, 见 CR-NNN"; **AC 要连 `(FR-x)` 括号一起保留** --
validate 认的是 `**AC-n** (来源)` 这个形状, 去掉括号它会判定条目不存在, CR 就 fixed 不了.

## 写作约定

- 中文正文, ASCII 标点; 代码, 接口, 字段名保持原文.
- 规范语气 "必须 / 不得"; 一条 FR 一件事; AC 写成 "给定什么输入, 看到什么结果".
- 状态机用 mermaid stateDiagram 配迁移表, 跨系统流程用 sequenceDiagram, 组合条件用决策表.
  图是导览, 编号规则是规范文本: 图上每条迁移 / 分支都对应一条 BR.
- FR / BR 只写业务语言, 表和字段统一登记在 REQ 第 7 节; 代码位置 (文件级) 登记在第 11 节.
- 面向半年后第一次读到的人写背景, 不假设读者知道当下的口头讨论.

## 工具

```
python3 <skills>/sdd/scripts/sdd.py status [CR-NNN]   # 状态与下一步
python3 <skills>/sdd/scripts/sdd.py validate          # 一致性检查 (CI 可用, 有错退出 1)
python3 <skills>/sdd/scripts/sdd.py index             # 重生成 INDEX.md
```

约定生效日期: 2026-08-28.
