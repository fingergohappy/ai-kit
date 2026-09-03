---
name: review-cr
description: >-
  对一个变更 CR-NNN 做三次 review 之一: docs (CR + REQ delta, 写 spec 前), spec (实施计划, 写代码前), impl (代码 vs spec vs AC, 落实前); 或对已处置的发现做复核. 按车道审, 每条发现带 file:line 证据与最小修复, 写进 notcommit/CR-NNN-<slug>/reviews/0N-<stage>.md, 状态 to fix / fixing / fixed. CR fixed 后用 distill 模式把 review 里犯过的错提炼进入库的错题本 docs/sdd/lessons.md, 再盘点工作目录 (草稿, spec, review 都是过程产物), 与用户确认后删除. 当用户说 "review / 审一下 / 复审 / 检查这个 CR / spec / 实现", "看看有没有问题", "并行审这个 CR / 派给 codex 审", "提炼 / 总结 review 的教训 / 清理 review", 或 sdd status 的下一步指向 review 或 distill 时使用. 不改代码.
---

# /review-cr: 三次 review

review 是这套流程里真正拦住问题的环节: 文档错了在 docs 阶段拦, 计划错了在 spec 阶段拦, 代码错了
在 impl 阶段拦. 它的产出是可复现的发现, 不是意见.

## 步骤

1. **定位与状态**. `../sdd/scripts/sdd.py status CR-NNN`; 读约定 `../sdd/references/conventions.md`. 确定阶段: 用户给了 (`docs` / `spec` /
   `impl`) 就用; 没给按状态推 -- 缺哪个审哪个; 某个 review 处于 `fixing` 且发现都有处置 -> 进复核模式.
   宣布 "review CR-NNN 的 <stage> 阶段".
2. **读车道清单与错题本**: `../sdd/references/review-lanes.md` 对应阶段的那张表, 每条问题都要过;
   再读 `docs/sdd/lessons.md` (有的话) 里本阶段车道的行 -- 那是这个仓库真犯过的错, 次数 >= 2 的当硬性检查项,
   逐条对照本次对象. 发现命中时在发现栏注明 "命中 L-n", 提炼时次数才能累加.
   顺手数出对本 CR **适用**的车道有几条 (不适用的记下理由, 第 5 步填车道结论表要用).
   并行还是串行**读工作目录下的 `.parallel`** (`/create-cr` 立 CR 时问过并写下的): `yes` 就按
   `## 并行审` 派窗口, `no` 或文件不存在就串行. 不要在这里重问 -- 那是干活中途打断用户.
3. **从磁盘重读对象**. docs: CR + 影响的每份 REQ + 草稿; spec: spec.md + CR + REQ; impl: 基点到当前
   的代码 diff + spec + CR 的 AC, 并**实际跑测试**, 不看声明.
4. **逐车道审**. 每条发现: 位置 (file:line 或条目号), 证据 (代码怎么写的 / 与哪条 AC 冲突), 级别
   (P0 不修不能合并 / P1 应修 / P2 建议), 最小修复 (具体改法). P0 在 "附" 里写复现步骤.
   拿不准的降级并注明 "未核实" -- 误报的 P0 比漏报更伤信任.
   **CR / REQ 里白纸黑字写了的业务决策是前提, 不是待议项**: 不同意也不报成发现, 那是用户拍过板的.
   真觉得那条决策有问题, 单独写进 "附" 里建议改 CR, 别混进发现表 -- 发现表是拿来修的.
   这一步是串行路线; 走并行的话它由各窗口分头做, 见 `## 并行审`.
5. **落盘**. 首次: `sdd.py new-review CR-NNN <stage> --reviewer "<模型或人>"`, 按模板填
   (`../sdd/assets/templates/review.md`): 车道结论表, 发现表 (编号 D-/S-/I- 连续), 测试缺口表
   (spec / impl 必填), 附. 有发现 -> 状态 `to fix`; 没有 -> 状态 `fixed`, 结论 OK, 文件照样要有.
   整体结论取车道里最严的.
6. **复核模式** (review 已存在且发现都有处置): 逐条核 -- 修复的看提交是否真的修了且没引入新问题;
   接受风险 / 不采纳的看理由是否成立. 在原文件填复核列 (`已核 <日期>` / `未修复: <说明>`); 不成立的
   把处置改回 `待修`. 全部通过 -> 状态 `fixed`, 结论更新 (如 BLOCK -> OK with notes). 有打回 ->
   状态保持 `fixing`, 提示 `/implement-cr` 处理.
7. **汇报**: 结论, P0 列表 (编号 + 一句话), 下一步 (`/implement-cr CR-NNN` 处理 / 或进入下一阶段).

## 并行审 (一个车道一个窗口)

三次 review 都可以并行: 车道之间本来就互斥, 一个车道派一个 agent 各审各的, 最后合成一份.
串行自审同样有效, 只是慢, 而且同一个模型把五个角度审一遍, 带着的还是同一个盲点.

**走不走这条路不由这里决定**: `/create-cr` 立 CR 时已经问过用户, 答案在工作目录的 `.parallel` 里
(`yes` / `no`; `sdd.py status CR-NNN` 也会显示). 第 2 步读它 -- `yes` 就照下面五步做, `no` 或
读不到就回 `## 步骤` 第 4 步自己逐车道审. 两条路的产出文件与格式完全一样.

**不要在这里重问用户**. 三次 review 横跨好几天好几个会话, 每次问一遍就是每次打断; 一个 CR 只在
立项时定一次策略. 用户中途想改主意, 改那个文件即可. `/auto-cr` 连文件都不读 -- 无人值守没人可问,
环境满足就并行.

照 `agent-crew` 的 review 形状做 (它管怎么起窗口和收结果, 这里管审什么和怎么合), 审完 kill 掉.

**1. 定窗口数**: 按 `../sdd/references/review-lanes.md` 里**该阶段**那张表, 逐条车道判断对本 CR 适不适用,
适用的各起一个窗口. 所以窗口数是 1 到 5 个 (每阶段车道表 A-E 五条), 由 CR 的性质决定, 不是固定两个.

车道表是唯一的切分依据: 不要自己发明角度, 也不要为了省窗口把两个车道塞给同一个 agent, 更不要
把一个车道拆给两个 agent -- 同一个角度审两遍只会产生两份重复发现, 还要你去合.

不适用的车道不开窗口, 但要在合并后的 review 的车道结论表里写明 "C 算术与不变量: 本 CR 不涉及金额计算,
未审". 没开的窗口和审过没发现是两回事, 分不清就等于没审.

**2. 起窗口** (每阶段新起, 不复用 -- 上一阶段的上下文会污染这一阶段的结论):

```sh
tmux has-session -t agents 2>/dev/null || tmux new-session -d -s agents
# 一个车道一个窗口, 窗口名带车道号, 便于 tmux list-windows 一眼看出谁在审什么
tmux new-window -t agents -n codex-CR-NNN-<stage>-A "cd <repo 绝对路径> && exec codex -m gpt-5.6-sol -c model_reasoning_effort=\"max\""
tmux new-window -t agents -n pi-CR-NNN-<stage>-B    "cd <repo 绝对路径> && exec pi --provider xai --model grok-4.6 --thinking xhigh"
tmux list-panes -t agents:codex-CR-NNN-<stage>-A -F '#{pane_id}'
```

模型 id 照抄, 不要缩写 -- 写错了窗口会停在 shell 提示符上, 看起来跟 "正在思考" 一模一样.

**模型分配**: 车道之间交替换工具, 别让所有车道都用同一个模型 -- 同一个盲点审五遍还是那个盲点.
要跑代码 / 跑测试的车道 (docs A, spec A, impl A / B / E) 优先给手上更强的那个.
只有一个工具可用时全给它, 车道照样一个一个开.

**3. 派发**: 用 `tmux-dispatch` skill 送 brief, 一个窗口一份, 不要自己 `send-keys`. 每份 brief 必须自带:

- 审什么: CR / REQ / spec 的**绝对路径**, impl 阶段另给基点 commit 与 `git diff` 范围
- 审哪个车道: 车道名 + review-lanes.md 里那一行原文 (对方读不到你的上下文), 并写明
  **只审这一个车道**, 别的角度留给别的窗口
- 错题本: `docs/sdd/lessons.md` 的绝对路径, 本车道且次数 >= 2 的行当硬性检查项
- 写哪里: `notcommit/CR-NNN-<slug>/reviews/0N-<stage>-<车道字母>.md` -- 按车道命名, 一个窗口一个文件,
  绝不让两个窗口写同一个文件. 格式照 `../sdd/assets/templates/review.md`, 发现编号在自己文件里从 1 编起
- 边界: **只读, 不改任何代码与文档**; CR / REQ 里已写明的业务决策当既定前提, 不同意也不报成发现
  (那是用户拍过板的, 你读不到那次讨论), 有意见写进自己文件的 "附"
- 完成线: 本车道结论 + 发现表填完, 每条发现带 file:line 或条目号与最小修复

**4. 收**: **所有**窗口都 `DONE:` 之后再合并. 少任何一个都不要开始合 -- 一个窗口没产出不等于
它没发现问题, 等于它没跑成. 缺谁就看那个窗口的 pane, 报出来, 别拿部分结果当全份.

**5. 合并**成 `reviews/0N-<stage>.md` (这才是 sdd.py 认的文件名):

- 车道结论表逐条填: 开了窗口的填该窗口的结论, 没开的填 "未审" 加理由
- 发现表按 `D-`/`S-`/`I-` **重新连续编号**, 各车道文件里的编号丢掉 (它们马上要删)
- 车道之间本来就不该重叠, 真出现同一问题两条 -> 合成一条, 保留更具体的那句, 级别取高的
- 结论冲突 -> 保留最严的, 在发现栏注明分歧 (照 `## 步骤` 第 4 步)
- 整体 verdict 取所有车道里最严的: 一个 BLOCK 就是 BLOCK
- 合并完删掉 `0N-<stage>-<车道>.md` 中间文件, kill 这一轮的全部窗口

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
