---
name: agent-crew
description: |
  在专用的 `agents` tmux session 里让外部 CLI agent（codex、pi……）干活，一个 window 一个——不管是把一件事交给其中一个、把一件事拆给几个、让两个各做一遍同一道题作对照，还是让几个从不同角度审同一份东西。当用户说「让 codex 去做这个」「让 codex 和 pi 一起做」「起个 agent 跑一下」「让 pi 也做一遍看看」「起几个 agent 分头审」「多角度并行 review」「一个车道一个模型」「开几个窗口跑」时触发。本 skill 管的是：怎么把 window 起得能看见对方在想什么、各工具的模型参数、活怎么拆才不打架、写代码的 agent 怎么隔离才不互相毁、结果怎么收怎么验、跑完怎么收摊（问一句再关，别让 window 越堆越多）。每个 window 的任务书怎么写、怎么送，是 `tmux-dispatch` 的事。
argument-hint: "[<要干的活>] [<交给谁: codex|pi|...>]"
disable-model-invocation: false
---

# agent-crew

让不是你的 agent 去干活——在它们自己的 tmux session 里，一个 window 一个，结果收得回来、验得了。

四种形态，本 skill 讲的就是它们之间的区别：

- **委派（delegate）**——一个 agent，一件事。它写代码，你验收。
- **拆分（split）**——几个 agent，同一件事的互不重叠的几块。最快，也是唯一一种它们能互相毁掉工作的形态。
- **对照（duplicate）**——几个 agent，**同一道题**，各做各的。适合那种「与其信一个答案不如比两个答案」的问题：难缠的 bug、没有明显形状的设计、棘手的迁移。两份解摆在一起是信息；一份解只是一个语气笃定的猜测。
- **审查（review）**——几个 agent，同一份东西，一人一个角度，只读，最后合成一个结论。

前三种要写文件，最后一种不写。就这一个区别，决定了要不要做隔离。

## `agents` session

所有 crew 的 window 都放在名为 `agents` 的 tmux session 里，一个 agent 一个 window，window 名就是它干的活（`codex-migrate`、`pi-arith`……）。这个 session 专门用于此，可以随意创建和销毁 window，不会打扰用户自己的布局。

```sh
tmux has-session -t agents 2>/dev/null || tmux new-session -d -s agents
```

## 必须交互式启动，不要 `-p`

```sh
# 对：交互式，输出实时可见
tmux new-window -t agents -n <名字> "cd <绝对路径> && exec pi --provider xai --model grok-4.6 --thinking xhigh"
tmux new-window -t agents -n <名字> "cd <绝对路径> && exec codex -m gpt-5.6-sol -c model_reasoning_effort=\"max\""

# 错：非交互 + 管道，全程没有任何输出
pi -p "$(cat brief.md)" 2>&1 | tee out.log
```

`-p` 是非交互模式，再把 stdout 接进管道（`| tee`）会让它块缓冲：高思考等级下 agent 会先想很久再一次性输出，中间 pane 里什么都不打印，日志也是 0 字节，跟根本没启动一模一样。交互式启动可以实时看到它在读什么、想什么，出问题也能直接接管对话。

`exec` 同样要写：不写的话 agent 是一个活得比它更久的 shell 的子进程，agent 退出后 window 停在光秃秃的提示符上，看起来像还在干活。

启动命令里的 `cd` 决定了这个 agent 的工作目录——**要写代码的 agent，隔离就是在这一步定下来的**，见下面那节。

## 模型约定

原样照抄，模型 id 是完整的那一整串：

| 工具 | 怎么起 |
|---|---|
| `pi` | `pi --provider xai --model grok-4.6 --thinking xhigh` |
| `codex` | `codex -m gpt-5.6-sol -c model_reasoning_effort="max"` |

`sol`、`grok`、`5.6` 是外号，不是模型 id。用外号起的 window 会在启动瞬间因未知模型报错退出，留下一个停在 shell 提示符上的 pane——看起来跟正在思考的 agent 一模一样。不要简写，不要凭记忆拼。

codex 没有 `--thinking` 这个 flag，思考等级是 config override，所以要写 `-c`。即便用户的 `~/.codex/config.toml` 里默认就是这两个值，启动命令里也要显式写全：对照和审查形态要求每个 window 用不同模型，而继承默认值意味着每个 window 都是同一个模型。

**对照**和**审查**这两种形态，在成本允许时刻意让各 window 用不同模型——两个盲区相同的模型把同一个问题回答两遍，比回答一遍多不出任何东西。**拆分**则无所谓，哪个更擅长那一块就用哪个。

## 给每个 window 发任务书

window 起好、agent 进入交互界面之后，先拿 pane id：

```sh
tmux list-panes -t agents:<名字> -F '#{pane_id}'
```

然后用 **`tmux-dispatch`** skill 把 brief 发给这个 pane id。brief 怎么传、怎么写，一律以那个 skill 为准——不要在这里凭记忆复述它的命令行，更不要自己 `send-keys` 硬塞任务文本。

它那边的两条规矩，在带一队人时比单次派活更致命：

- **brief 必须自包含。** 每个 window 都从零开始：看不到本会话、本 cwd，也看不到你刚得出的结论。只用绝对路径，所有指代展开成原文，写清楚「做完长什么样」，并且明确边界——审查的写「只读，不要改代码」，干活的写清楚哪些路径是它的、哪些碰都不许碰。
- **不要轮询。** 全部派完就去干别的。跨 N 个 pane 循环 `capture-pane` 会把自己整个回合耗在只有对方能推进的屏幕上；它们干完会通过 `tmux-reply` 主动敲门。想确认某个还活着，单次 `capture-pane` 看一眼可以，循环不行。

## 写代码的必须隔离

审查是只读的，几个 agent 共用一个 checkout 没问题。**要写文件的不行。** 两个 agent 在同一个工作区里编辑，会互相覆盖对方的修改、把对方的文件 stage 进自己的提交、抢同一份构建缓存，最后产出一份谁也理不清的 diff——而且**它们全都不会察觉**，因为每一个看到的都是一棵不断在自己脚下变化的树，而它会默认那是自己刚才干的。

所以在起任何一个要写代码的 agent 之前，先定它写在哪：

- **一个写代码的 agent 一个 worktree**，启动命令的 `cd` 直接进那个目录。window 名和分支名保持一致，这样 `tmux list-windows` 一眼就能看出哪个窗口挂在哪个分支上。
- **对照模式必须分开 worktree**——它的全部意义就是两次独立尝试，共用一棵树等于把两次坍缩成一团浆糊。
- **拆分模式同样需要**，除非那几块本来就在不同的 repo 里。
- 项目自己有 worktree 约定（专用脚本、固定的父目录、必须软链进去的文件）就按它的来，不要裸 `git worktree add`。
- 每份 brief 里写明哪棵树是它的、不许碰别人的。一个跑到隔壁 worktree 里去改东西的 agent，造成的破坏在 diff 里看起来跟你自己的改动一模一样。

**合并是你的事，不是它们的事。** 不要让一个 crew 成员把代码合进另一个成员还在上面干活的分支。

## 活怎么拆

不管按什么拆，**必须互斥**——块与块不重叠，角度与角度不会在两个地方吵同一件事。重叠的地方，就是并行省下的时间被冲突和重复报告吃回去的地方。

**拆分**按文件和模块的边界切，不是按「你做简单的那一半」切。每份 brief 里点名哪些路径归它。

**审查**按「会独立出错的维度」切：正确性、算术与单位、状态机与并发、范围与非目标、测试、可运维性。这份东西不可能在某个维度上出错，那个 window 就不值得开。审 sdd 的 CR / spec / 实现时**不要自己发明角度**——`sdd/references/review-lanes.md` 里对应阶段的车道表就是切好的分法。

每份 brief 都要写明该 window 的**产出文件路径**，审查还要写明**发现编号前缀**，避免多个 agent 并发写同一个文件。

## 结果怎么收

每个 window 通过 `tmux-reply` 回报，并写自己的文件。收到之后怎么办，取决于形态：

- **委派 / 拆分**——报告里写 `DONE` 是一个**主张**，不是证据。自己读 diff、自己跑测试，然后再把「做完了」转述给用户。一个撞上解决不了的东西、绕过去了的 agent，会诚实地报告完成，并且除非 brief 问了「你跳过了什么」，否则绝不会主动提那个绕法。
- **对照**——把两份解摆在一起比，说清楚你取哪一份、为什么。**分歧处才是有价值的部分**，它通常正好标出了这道题真正难的地方。
- **审查**——把发现合进一份文件。车道之间有重叠时保留更锋利的那条表述，不要取平均。**整体结论取最严的那个车道**：只要有一条 BLOCK，整份 review 就是 BLOCK，不管另外几条报了多少个 OK。

汇报时说清楚：跑了哪几个 window、各自产出了什么、合出来的结论是什么。**没有产出的 window 不是「审过没发现问题」的 window**，那是一个没跑起来的 window——把这件事说出来，才分得清「干完了并且验过」和「压根没发生」。

## 收摊: 问一句再关

结果收完、验过、转述给用户之后，**问一句这些 window 能不能关了**，别默认留着:

> codex-migrate / pi-arith 两个 window 已经跑完并收了结果，可以 kill 掉吗?

一轮不关就攒一轮。几次下来 `agents` session 里堆着十几个早就跑完的 window，
下次 `tmux list-windows` 分不出哪个还在干活、哪个是上周的尸体，起新 window 时也更容易
撞上一个名字相同的旧窗口。

问而不是直接关，是因为窗口里那段对话有时还有用——用户可能要翻 agent 的推理过程，
或者想直接接管那个 pane 继续追问。关掉就没了，`tmux-reply` 写回的文档里只有结论。

用户点头就一个个 kill:

```sh
tmux kill-window -t agents:codex-migrate
tmux list-windows -t agents          # 确认剩下的都还在干活
```

session 空了不用特意删，下次 `has-session` 会复用它。

**只关自己起的 window.** 这条规矩的边界是 `agents` session: crew 的 window 由你起，所以由你收.
用 `tmux-dispatch` 派给别处的 pane (用户自己布局里的那个 `%7`, 另一个项目的会话) **一律不动** ——
那不是你起的，用户正用着，关掉就是掀了别人的桌子。分不清是谁起的就不关，问。

`/auto-cr` 这类无人值守的流程不问, 直接 kill (没人可问, 而且它每阶段都新起窗口, 留着只会污染
下一阶段的上下文).
