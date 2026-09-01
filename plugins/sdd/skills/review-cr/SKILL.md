---
name: review-cr
description: >-
  对一个变更 CR-NNN 做三次 review 之一: docs (CR + REQ delta, 写 spec 前), spec (实施计划, 写代码前), impl (代码 vs spec vs AC, 落实前); 或对已处置的发现做复核. 按车道审, 每条发现带 file:line 证据与最小修复, 写进 notcommit/CR-NNN-<slug>/reviews/0N-<stage>.md, 状态 to fix / fixing / fixed. CR fixed 后用 distill 模式把 review 里犯过的错提炼进入库的错题本 docs/sdd/lessons.md, 再盘点工作目录 (草稿, spec, review 都是过程产物), 与用户确认后删除. 当用户说 "review / 审一下 / 复审 / 检查这个 CR / spec / 实现", "看看有没有问题", "提炼 / 总结 review 的教训 / 清理 review", 或 sdd status 的下一步指向 review 或 distill 时使用. 不改代码.
---

# /review-cr: 三次 review

review 是这套流程里真正拦住问题的环节: 文档错了在 docs 阶段拦, 计划错了在 spec 阶段拦, 代码错了
在 impl 阶段拦. 它的产出是可复现的发现, 不是意见.

## 步骤

1. **定位与状态**. `../sdd/scripts/sdd.py status CR-NNN`. 确定阶段: 用户给了 (`docs` / `spec` /
   `impl`) 就用; 没给按状态推 -- 缺哪个审哪个; 某个 review 处于 `fixing` 且发现都有处置 -> 进复核模式.
   宣布 "review CR-NNN 的 <stage> 阶段".
2. **读车道清单与错题本**: `../sdd/references/review-lanes.md` 对应阶段的那张表, 每条问题都要过;
   再读 `docs/sdd/lessons.md` (有的话) 里本阶段车道的行 -- 那是这个仓库真犯过的错, 次数 >= 2 的当硬性检查项,
   逐条对照本次对象. 发现命中时在发现栏注明 "命中 L-n", 提炼时次数才能累加.
3. **从磁盘重读对象**. docs: CR + 影响的每份 REQ + 草稿; spec: spec.md + CR + REQ; impl: 基点到当前
   的代码 diff + spec + CR 的 AC, 并**实际跑测试**, 不看声明.
4. **逐车道审**. 每条发现: 位置 (file:line 或条目号), 证据 (代码怎么写的 / 与哪条 AC 冲突), 级别
   (P0 不修不能合并 / P1 应修 / P2 建议), 最小修复 (具体改法). P0 在 "附" 里写复现步骤.
   拿不准的降级并注明 "未核实" -- 误报的 P0 比漏报更伤信任.
   环境支持子代理或派发给其它 agent / 模型时, 可一个车道一个, 各自独立结论, 汇总到同一文件;
   汇总时去重, 冲突的结论保留最严的并注明分歧.
5. **落盘**. 首次: `sdd.py new-review CR-NNN <stage> --reviewer "<模型或人>"`, 按模板填
   (`../sdd/assets/templates/review.md`): 车道结论表, 发现表 (编号 D-/S-/I- 连续), 测试缺口表
   (spec / impl 必填), 附. 有发现 -> 状态 `to fix`; 没有 -> 状态 `fixed`, 结论 OK, 文件照样要有.
   整体结论取车道里最严的.
6. **复核模式** (review 已存在且发现都有处置): 逐条核 -- 修复的看提交是否真的修了且没引入新问题;
   接受风险 / 不采纳的看理由是否成立. 在原文件填复核列 (`已核 <日期>` / `未修复: <说明>`); 不成立的
   把处置改回 `待修`. 全部通过 -> 状态 `fixed`, 结论更新 (如 BLOCK -> OK with notes). 有打回 ->
   状态保持 `fixing`, 提示 `/implement-cr` 处理.
7. **汇报**: 结论, P0 列表 (编号 + 一句话), 下一步 (`/implement-cr CR-NNN` 处理 / 或进入下一阶段).

## 提炼模式 (`/review-cr CR-NNN distill`)

review 是过程产物, 留着只会越积越多; 值得长期保存的是 "犯过什么错". CR fixed 之后把它提炼进错题本, 然后连同
草稿与 spec 一起删掉 -- notcommit 下的三样都是过程产物, 结论该在的地方是 CR 与 REQ.
删除不可逆, 所以第 6 步是盘点完问用户, 不是一刀切.
`sdd.py status CR-NNN` 在 CR fixed 且 review 未提炼时会把下一步指到这里.

1. **前提**: CR 状态 fixed, 各份 review 状态 fixed. 不满足就停 (脚本也会拒绝删除).
2. **读全部 review 的发现表**, 挑出处置为 "修复" 的 -- 那是真犯的错. "接受风险" / "不采纳" 不是错, 不提炼;
   但被复核推翻的误报 (P0 报错了) 是审查方的错, 记车道 R.
3. **归并成模式**: 同一根因的多条发现合成一条 (例: 三条在途口径问题 = 一条 "按时间戳切在途集"). 每条写成
   模式 / 识别信号 / 规则 三段, 泛化到本 CR 之外, 不写具体函数名. 写法见 `../sdd/references/writing-guide.md`
   "错题本的一条". 一次性笔误不收.
4. **与已有错题本比对**: 没有错题本先 `sdd.py lessons --init`; 已有同模式的行, 不加新行 -- 在 "来源" 追加
   `CR-NNN I-x`, "次数" +1. 新模式用 `sdd.py lessons --next-id` 取编号追加一行.
5. **回填**: 每份 review 的 frontmatter 把 `distilled: false` 改成 `distilled: [L-3, L-4]`, 或者
   `distilled: "无可提炼: 理由"` (含 `": "` 必须加引号). CR 不动 -- 它是业务文档, 工程教训不进去;
   反查靠 lessons.md 的 "来源" 列 (grep `CR-NNN`).
6. **盘点, 问, 再删**: 删除不可逆 -- `notcommit/` 整体 gitignore, 那些文件从没进过版本库, git 恢复不了.
   所以不一刀切, 三小步:

   **6a 盘点**: `sdd.py prune CR-NNN --dry-run` 拿到清单, 然后**逐份读一遍**, 核实每样东西的内容
   有没有落到入库文档里, 列成表给用户:

   | 文件 | 内容去向 | 建议 |
   |---|---|---|
   | `draft/*.md` | 结论进了 CR 第 1 / 4 节; docs review 车道 A 已拿它核过现状 | 删 |
   | `spec.md` | 分步落点 (提交 hash) 已填进 CR 第 5 节 | 删; 上线检查单没走完则留 |
   | `reviews/0N-*.md` | 教训已提炼成 L-x 进 lessons.md | 删 |

   这张表是照着实际内容填的, 不是抄模板. 有任何一项没落地 -- 草稿里的结论没进 CR, spec 里有还没
   执行的上线步骤, 某条发现既没提炼也没写 "无可提炼" 的理由 -- 在表里写明, 建议保留, 并说清缺口在哪.

   **6b 问**: 把表给用户, 问哪些删哪些留. 不要替用户决定, 也不要因为闸门过了就默认全删.

   **6c 删**: 按回答执行 `sdd.py prune CR-NNN`; 要留某项加 `--keep spec` (可给多次, 取值
   `draft` / `spec` / `reviews`). 不要手动 rm -- 走命令才有那六道闸门挡着.

   删干净后这个 CR 只剩两样痕迹: CR 第 5 节的 review 状态与落点行, 与 lessons.md 里的来源.
7. **汇报**: 新增了哪些 L (模式一句话), 累加了哪些 L 的次数, 删了几个文件. `sdd.py validate` 应 0 错误.

## 不做

- 不改项目代码, 不改 REQ / CR / spec 正文 -- review 只产出发现, 修改由 `/implement-cr` 做, 这样处置
  有记录, 复核有对象. (distill 模式例外: 只动 review frontmatter 的 `distilled` 与 lessons.md; CR 仍不动.)
- 提炼时不把发现原样抄进错题本 -- 抄过去等于没删. 一条 L 要能脱离原 CR 读懂.
- 不用 "考虑改进 / 建议关注" 这类没有改法的措辞.
- 不在同一条发现里混两个问题; 一条一个编号.
