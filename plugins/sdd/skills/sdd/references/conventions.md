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
/implement-cr CR-NNN   按 spec 分步实施 (TDD), 提交可跨步, 填落点   [CR: fixing]
/review-cr CR-NNN impl 审实现                                 -> reviews/03-impl.md
/implement-cr CR-NNN   落实: 更新 REQ 正文 + 变更记录, CR 置 fixed, 重生成 INDEX
/review-cr CR-NNN distill  提炼教训进 lessons.md, 清理工作目录      -> lessons.md   [notcommit/CR-NNN-* 删除]
```

`/implement-cr` 是 "做下一件事": 它先看状态 -- 有未处置的 review 发现就先处理, 有待办步骤就实施,
都齐了就落实 (没 spec 时它让你去 `/spec`). `/sdd` 或 `sdd.py status CR-NNN` 告诉你下一步是什么.

六个命令里只有 `/implement-cr` 会改项目代码 (`/auto-cr` 内含它); `/draft` `/req` `/create-cr` `/spec` `/review-cr`
都只读代码, 只写文档 -- 想只要方案不要改动时, 停在 `/spec` 即可.

review 是软闸门: 跳过某次 review 直接往下走需要人明确说 "跳过", AI 不自行跳过.

**六个命令里只有 review 能并行**. 三次 review 的车道之间本来就互斥, 可以一个车道派一个 agent
并行审再合成一份 (怎么做见 `review-cr` 的 `## 并行审`). 用不用并行**在 `/create-cr` 立 CR 时问
用户一次**, 答案写进工作目录的 `.parallel` (`yes` / `no`, notcommit 不入库, `sdd.py status` 会
显示); 三次 review 都读它, 不重问 -- 三次 review 横跨好几天好几个会话, 每次问就是每次打断.
环境不支持 (没 tmux, 或 codex / pi 都不在 PATH) 就不问也不写, 读不到即串行.
`/draft` `/req` `/create-cr` `/spec` `/implement-cr` 都是串行的活: spec 是一份连贯文档, 拆开写
会互相矛盾; 分步实施前后依赖, 并行只会制造冲突, 真要并行写还得先做 worktree 隔离.

## 提交

**只有代码改动值得单独一个提交.** 文档不占提交: `notcommit/` 下的 spec / review / draft 本来
就不入库; 入库的 REQ / CR 搭在同一分支的代码提交里走 (落实那一步与 REQ 更新同一个提交), 不要
为 "写完 CR" "审完 docs" 单独提交一次 -- 那两步没有代码, 提交里只有文档, 合进主干就是纯噪音.

**一个提交可以覆盖连续几步**, 前提是这几步的回退单元一体; 一个提交不能只做半步. 详见
`implement-cr` 的分步实施那节.

**一轮 review 的修复合一个提交.** 逐条发现各提交一次会让一个 CR 堆出十几个 `fix:` --
处置列各条填同一个 hash 即可, 那是它们同批修掉的记录. P0 与其余分开提交是允许的例外
(P0 常要单独回退).

### 压缩提交 (squash)

**只压没 push 过的提交.** 边界是 push 不是 main: push 出去就该当共享的看 -- 别人可能已经拉了,
或者在 PR 里逐个提交读过并引用了 hash, 改写要 force push, 代价不对称. 已经进了 main 的更是
到此为止, 只能往前加提交, 不能回头改写.

时机是**三次 review 都 fixed, 落实之前**. 不是怕压两次麻烦, 是 review 处置列里的
`修复 <hash>` 正是复核人 (`/review-cr` 第 6 步) 用来核 "这条发现真的修了没有" 的凭据 --
复核还没做完就把那些 hash 压没了, 复核就无从下手, 只能凭处置栏那句自述. 落实之前压完, 三处
hash 一次换对, CR 第 5 节填的就是最终值.

**这个窗口只在代码还攒在分支上时存在.** 边做边合的节奏 (实施提交随做随进主干, CR 还在 fixing
就已经 merge 了) 根本等不到它 -- impl review 复核完的时候代码早在 main 上, 只能往前加提交.
那种节奏下提交数只能从源头控: 提交可跨步, 一轮 review 的修复合一个提交. 想留压缩的余地, 就得
让一个 CR 的实施提交攒在自己的分支上, 落实之后连同文档一起合.

压完必须做三件事, 少一件就有指向不存在的提交的 hash:

1. `spec.md` §4 落点列的 hash 换成压缩后的
2. 三份 review 处置列里的 `修复 <hash>` 换成压缩后的
3. CR 第 5 节 "实现提交" 换成压缩后的

**每个压出来的提交要自己说清干了什么** -- 一句话, 按项目自己的提交约定写, 不塞 CR 编号与步号.
`fix(paymenttracking): close the four P0s the implementation review found` 这样就够了: 读的人
知道这是什么修复, 不需要 "CR-019 step 11" 才看得懂. 压缩是为了让主干读得懂, 压完只剩一句
`wip` 或一堆 `fix` 摞在一起, 白压.

## 业务决策: 谁拍板, 什么时候问

**先分清三类**, 处理方式完全不同:

| 类型 | 例子 | 怎么办 |
|---|---|---|
| 技术选择 | 用哪个实现, 分几步, 表怎么建 | 自己定, 理由写进 spec §6 或 CR 第 4 节. 不问, 不记 OQ |
| **业务决策** | 规则没定, 边界没说, 两种读法都说得通, **会改变验收标准** | 见下 |
| review 发现 | 审出来的 bug, 漏测, 与 AC 不符 | 直接修, 不问 (见 `review-cr` / `implement-cr`) |

**业务决策再看它定没定过**:

- **CR 里已经和用户确认过** -> 照 CR 执行, **不记 OQ, 不重问**. 已经拍过板的事不是开放问题,
  再问一遍是让用户为同一件事拍两次板.
- **CR 里没定** (新冒出来的歧义) -> 取决于当前是不是被授权自动推进:

| 何时 | 遇到未定的业务决策 |
|---|---|
| `/auto-cr` | 按自己推荐的做法执行 + 在 REQ 第 10 节记一条 OQ, 往下走 |
| 用户说了 "推进到 X" / "一路做到 X" / "别问我" | **同上** -- 那句话就是授权, 记 OQ 往下走, 不要逐个打断 |
| 普通逐步模式 (用户没给这种话) | **停下来问用户**. 这一条只管业务决策, 不要顺手把 review 发现也拿去问 |

OQ 的四段格式 (问题 / 已按 / 理由 / 影响) 见 `auto-cr` 的 "歧义" 节, 缺 "影响" 那段用户没法判断
改判代价, OQ 就成了没人敢碰的悬案.

**无论哪种模式都必须当场停**的越权项: 要动 CR 影响范围之外的 REQ 条目; 要改已 fixed 的 review
的结论; 要跳过某次 review; 迁移会销毁审计数据. 这几样代价不对称, 记 OQ 往下走等于把错误做实.

### CR 已确认的逻辑 > review 的意见

review 的 agent (尤其是派出去的 codex / pi) 读不到你和用户之前的讨论, 会把**用户已经拍板的设计**
当成缺陷报上来. 这类发现**不改代码**: 处置写 `不采纳: CR 第 N 节已确认 <那条决策>`, 复核照此认.

判断标准是 CR / REQ 里有没有白纸黑字: 有, 以它为准 -- 用户的决策不因为一个审查者不同意就失效;
没有, 那才是真发现, 该修就修. 真觉得用户那条决策错了, 是**提出来让用户改 CR**, 不是绕过它改代码.

## 每推进一步就贴进度

做完任何一件让状态变化的事 -- 建了 review, 写完 spec, 提交了一步, 处置完发现, 置了 fixed --
立刻跑一次 `sdd.py status CR-NNN --write`, **把进度表原样贴出来**, 再做下一件.

`--write` 会把同一份表落进工作目录的 `PROGRESS.md`. 这一份是给人看的: 用户想知道走到哪了,
不必回头翻聊天记录, 也不必开口问 agent, 打开那个文件就是最新的. 它是生成物, 每次覆写,
所以**不许手工编辑, 也不许 agent 用自然语言往里补写** -- 手写的进度和勾一样会骗人.

进度表是这样的 (八关, 走过的 ✓, 当前的 →, 还没轮到的 ·):

```
  进度: 4/8
    ✓ 1 立项    CR-010 [fixing]
    ✓ 2 docs审  01-docs.md [fixed]
    ✓ 3 spec    spec.md 4 步
    ✓ 4 spec审  02-spec.md [fixed]
    → 5 实施    2/4 步已提交, 2 步待办
      · 6 impl审  审代码
      · 7 落实    REQ→implemented, CR→fixed
      · 8 提炼    提炼进 lessons.md, 清工作目录
```

每关后面是脚本从文件里读出来的证据 (文件名 + frontmatter 状态 + 未处置发现数 + 填了 hash 的步数),
所以**不要自己复述 "第 5 步做完了"** -- 自述和勾一样不可验证, 贴脚本输出用户看到的才是磁盘上的事实.
一步一贴还顺带把没落盘的活当场照出来: 该变 ✓ 的关没变, 说明上一步只写进了 agent 的上下文.

贴完别再用自然语言把八行重讲一遍. 要补的只有进度表说不出的那部分 -- 这一步为什么这么做, 遇到了什么.

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
python3 <skills>/sdd/scripts/sdd.py status [CR-NNN]   # 状态; 给 CR 时出八关进度表与下一步
python3 <skills>/sdd/scripts/sdd.py validate          # 一致性检查 (CI 可用, 有错退出 1)
python3 <skills>/sdd/scripts/sdd.py index             # 重生成 INDEX.md
```

约定生效日期: 2026-08-28.
