# 怎么写条目: 好例子与坏例子

## 头部 frontmatter

好:
```yaml
summary: >-
  报价改为镜像参考汇率本地定价: 客户汇率 = min(参考价 - iBnk 手续费, cohort 上限)
affects:
  - "REQ-001 (全文: FR-1 ~ FR-6, BR-1 ~ BR-8)"
```

坏 (标准 YAML 会读成嵌套映射, pi / Obsidian 直接报错):
```yaml
summary: 报价改为镜像参考汇率本地定价: 客户汇率 = ...
affects:
  - REQ-001 (全文: FR-1 ~ FR-6)
```

规则: 值里有 `": "` 就加引号或用 `>-`. `validate` 会扫出来.

模板注释说的是 "每节放什么", 这里说 "一条怎么写才算好". 例子取自真实 REQ (略作缩写).

## FR: 一条一件事, 规范语气, 可验收

好:
> **FR-7**: 闸门不通过是等待, 不是失败: 出金必须保持 ROUTED, 由物化轮询在后续轮次自动复检;
> 不得进入失败或退款路径, 不得产生 SGB provider operation, 不得消耗 Create 幂等键.

为什么好: 说清了 "是什么" (等待) 和 "不是什么" (失败), 三个 "不得" 每个都能写成断言.

坏:
> **FR-7**: 余额不足时系统应妥善处理并重试.

为什么坏: "妥善" 不可验收; "重试" 没说重试什么, 幂等键怎么办; 没有 "不得" 边界.

坏 (混入实现):
> **FR-5**: `requireMasterPoolLiquidity` 在 `factory.go:96` 检查 `sgb_balance_snapshots` ...

为什么坏: 函数名与行号是 spec §1 的内容. FR 只写业务语言: "物化 SGB 汇款前必须通过余额闸门:
快照可用余额 - 未反映在途 - 旧模型占用 - 安全垫 >= 本笔总借记".

## BR: 状态机迁移表的一行, 规则表的一行

好 (迁移表):
> | BR-4 | ROUTED -> EXECUTING | 物化 worker + SGB 受理 | 余额闸门通过 (FR-5/FR-6), SGB 接受 Create | 发出 `sgb.create_remittance_payout`; 闸门不通过时停留 ROUTED, 无副作用 |

为什么好: 触发者, 前置条件 (回指 FR), 副作用, 以及 "不通过时" 的分支都在一行里.

好 (规则表, 自上而下首条命中):
> | BR-10 | transaction 筛查结果为 severe | manual_review, 原因 SEVERE_RISK_MANUAL_REVIEW; 不产生风险决策 |
> | BR-11 | source wallet 结果为 high 或 severe | manual_review, 原因 SOURCE_WALLET_RISK_MANUAL_REVIEW |

坏: 把上面两行写成一段散文 "如果交易是 severe 或者钱包是 high 或 severe 就转人工".
散文没有编号, CR 无法说 "BR-11 变更后: ..."; 顺序也丢了 (首条命中的语义).

## AC: 给定什么输入, 看到什么结果, 标注来源

好:
> **AC-16** (FR-16/BR-30): 开关开启, provider 零返回 (无裁决且无 severe 信号) -> 不被处置, request 保持 submitted.

好 (负例):
> **AC-8** (FR-8): production 且出金开启时写入安全垫 `0` 被拒绝; 其它环境允许.

坏:
> **AC-8** (FR-8): 安全垫功能正常工作.

## 已接受风险: 是结论, 论证在 review

好 (REQ 5.4):
> 已接受风险 (2026-08-26 产品定): 本期不设观测最长可用年龄的硬上限; 参考价下跌方向的敞口由
> 告警响应时效兜底. 论证与最坏损失估算见 CR-002 D-7.

坏: 把 "最坏损失 = notional x (客户汇率 - 真实可成交价), 10000 USDT 在 0.95 市价下多付 475 USD,
建议阈值 5 / 15 / 30 分钟 ..." 整段写进 BR. 那是论证与未落地的运维建议; 决定落地的阈值才写成
BR 并配 AC.

## CR 变更内容表的一行

好:
> | FR-8 | 安全垫是部署级参数 `SGB_LIQUIDITY_SAFETY_BUFFER_MINOR`, 缺失或全零令进程启动失败, 重启后生效 | 安全垫是落库热配置, 由 `PUT /api/v1/settings/{key}` 写入并记录操作者; 闸门每次判定现读; production 非零由写入期校验 + 闸门 fail-closed + 旧模型 cursor 拒绝零垫初始化三处保证 |

为什么好: "现行" 与 REQ 原文一致 (review 车道 B 会逐字核), "变更后" 可以直接替换进 REQ.

## spec §1 侦察结论的一条

好:
> 2. **force 模式必须换 claim 查询, 否则队首堵塞**: 现行 `ChainScanAutoKYTClaimDisposition`
>    (`money_chain_scan_auto_kyt.sql:161-166`) 的进入条件是 ..., 且 `ORDER BY submitted_at ASC
>    LIMIT 1`. 开关开启后 "wallet=high 且裁决未出" 的行既不能扣又不能放, 若领出后跳过, 下一轮
>    仍领同一行, **队列头永久堵塞**. 解法: force 模式用专用 claim, 进入条件收窄为 ...

为什么好: 事实 (file:line) -> 推论 (会堵) -> 对改动的约束 (必须换查询). 三段齐全.

坏:
> 2. 需要修改 claim 查询以支持 force 模式.

## 错题本的一条

好:
> | L-3 | B 金融安全 | 在途占用按时间戳与快照切分, 已登记但尚未被权威观测证明的支出被踢出扣减集, 同一份余额可被答应两次 | 任何 `created_at` / `resolved_at` 与 `observed_at` 的比较; "已提交即已扣" 的假设 | 非终态支出无论时间一律计入占用; 终态只在权威观测 (银行借记 / 对账) 证明后剔除; 本地时间戳不算证据 | CR-001 I-19, I-39 | 2 |

为什么好: 模式脱离了具体函数名仍能读懂; 识别信号能直接当 grep 关键词和审查问题; 规则一句话可执行; 来源
留着编号, review 删了也能追到 CR 第 5 节; 次数 2 说明它该进硬性检查.

坏:
> | L-3 | B | money_sgb_factory.sql 在途查询漏了 pending 的 Create | - | 加上 pending | CR-001 F0 | 1 |

为什么坏: 只是把发现抄过来, 换个仓库 / 换个表就用不上; 没有识别信号, 下次不会警觉; 规则不泛化.

## review 的一条发现

好:
> | I-3 | P0 | B 金融安全 | `money_sgb_factory.sql:165-174`, 调用点 `liquidity.go:72-80` | 在途只认 `created_at > observed_at`; 快照写入不拿 allocation 锁; 物化与发送是两条循环 -> 已 enrol 未发送的 Create 在下一张快照后被排除, 同一份余额可被答应两次 (复现见附) | 非终态 Create 无论 `created_at` 都计入: `AND (created_at > $observed_at OR status IN ('pending','executing','unknown'))` | 待修 | |

为什么好: 位置精确, 证据是代码怎么写的, 后果具体 (答应两次), 修复是可以直接贴的 SQL.
