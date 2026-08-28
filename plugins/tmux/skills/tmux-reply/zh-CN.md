---
name: tmux-reply
description: |
  向派活给你的那个 tmux pane 回报结果：把报告作为 `## Report` 一节追加进任务过来的那份频道文档，再通过 tmux 发回一行状态（`DONE:` / `BLOCKED:` / `QUESTION:`）加这份文档的路径。当你手上的任务是从别的 pane 派过来的（消息指向一份文档，并带着 `[dispatched from tmux pane %5]` 这样的戳），而你现在做完了、卡住了、或者需要派发方拍板时，主动使用——不用等人再问一遍。用户说「通知 5」「告诉派活给我那个 pane」「回报一下进展」「跟 %3 说我做完了」时同样触发。这是 tmux-dispatch 的返回半程：派发方从不轮询你，报告没写进文档就等于没人知道这活干过。
when_to_use: |
  当前任务带着 `[dispatched from tmux pane %N]` 戳且已完成或卡住时触发；或用户说「通知 {number}」「回报给 {number}」「告诉那个派活的 pane」「跟 {number} 说我做完了」时触发。
argument-hint: "[<pane_id>] [<文档路径>] [DONE:|BLOCKED:|QUESTION: <一行>]"
disable-model-invocation: false
---

# tmux-reply

把报告写进任务过来的那份频道文档，然后带着那行状态去敲派活那个 pane 的门。

为什么这件事需要专门写下来：派发方是**故意**不看着你的。它把任务交出去就走了，所以没有进度条、没有轮询、没有超时——唯一能闭合这个环的就是这条消息。活干完了却不说话，和从来没开始过，在派发方看来一模一样。

**状态走 tmux，证据留文档。** 穿过 tmux 的只有两样东西：一行以 `DONE:`、`BLOCKED:` 或 `QUESTION:` 开头的状态，和文档的绝对路径。这个切分两头都是有意的。状态是派发方**唯一要据以行动**的部分——结掉任务、解你的阻塞、回答你的问题——让它为了搞清是这三者中的哪一种而先去开一个文件，等于在它和下一步动作之间塞了一次磁盘读取。而状态背后的一切——改了什么、跑了什么命令、真实输出、你跳过了什么——都写进文档，因为派发方必须拿你的结果去对照任务书；在文档里这两段一上一下挨着，一周后照样能读，而粘进 pane 的报告在对方压缩上下文的那一刻就没了。

所以：绝不要把报告正文粘进 pane，也绝不要让文档退化成那一行状态。两者互换位置都读不成。

## 找到文档和派发方的 pane id

两样都在启动这项工作的那条消息里：

```
Task document: /Users/me/proj/docs/tmux-channel/20260426-1930-fix-verify-token.md

[dispatched from tmux pane %5. That document is the task -- read it; ...]
```

那个路径是你要写的地方，`%5` 是你要敲的门。绝对路径照抄消息里的原样——绝不要拿同一个相对路径在自己的 cwd 下解析，在同一个 repo 的另一个 worktree 里那是另一个文件，你的报告会落在没人看的地方。

如果任务上没有戳，那它不是派发来的，没人在等报告，正常回答用户就好。如果你确信需要回报但找不到 pane id，用纯文本询问——不要列 pane 清单，也不要发给一个你推断出来的 pane，报告落进陌生人的 session 比迟到更糟。

## 追加报告

在文档**末尾**新增一节，上面的内容一律不动——频道是只追加的，而且你收到的那份任务书正是别人用来验收你结果的东西：

```markdown
## Report — %7 → %5 — 2026-04-26 20:05

DONE: 修好了 verifyToken 的毫秒/秒比较问题。
改动：/Users/me/proj/src/auth.ts:42 改为 `payload.exp < Date.now()`；
新增 /Users/me/proj/test/auth.test.ts 里的 "freshly signed token is valid" 用例。
验证：cd /Users/me/proj && npm test -- auth → 14 passed, 0 failed。
未处理：refreshToken 里有同样的秒/毫秒混用（auth.ts:71），按你的要求没动。
```

标题保持英文、以 `Report` 开头——`reply.sh` 会检查文档最后一节是不是报告，不是就拒绝敲门。这个检查正是重点：它拦住「宣布干完了、却什么都没写下来」这种代价最高的失败。

正文欠派发方的东西——它是另一个 agent，读到这段时没有任何你的上下文：

- **第一行就是状态**：`DONE: …`、`BLOCKED: …` 或 `QUESTION: …`——和你等下要传给 `reply.sh` 的那行一致，让文档和 pane 对结论说同一句话。这三种情况下派发方的下一步动作完全不同。
- **所有碰过的文件用绝对路径。** 派发方可能在别的目录或别的 worktree。
- **给证据，不是给保证。** 「跑了什么命令 + 实际输出」胜过「测试通过了」——派发方可能要把这话转述给一个会去核对的用户。
- **说清你没做什么**，以及为什么：跳过的范围、你判断超出边界的修复、你不得不做的猜测。沉默的省略会变成派发方的 bug。
- **`BLOCKED` / `QUESTION` 要点明需要什么决定**，以及你已经试过什么。含糊的阻塞只会把这趟往返又弹回给你。

单薄 —— `做完了`。有实质 —— 上面那一段。只写派发方为了行动所需要的东西；把你调试的完整经过铺开，只会让它多读一遍，而且没有一个字是它能用的。

## 脚本路径

所有 `scripts/` 路径相对于**本 SKILL.md 文件所在目录**。执行前必须先解析为绝对路径，因为插件可能装在缓存目录而不是仓库里：

```bash
SKILL_DIR="<本 SKILL.md 所在目录的绝对路径>"
```

## 发送

```bash
bash "$SKILL_DIR/scripts/reply.sh" "<pane_id>" "<文档路径>" "DONE: <一行>"
```

三个参数都是必填的，状态行必须以 `DONE:`、`BLOCKED:` 或 `QUESTION:` 开头——不符合的脚本直接报错退出，而不是发出一行让派发方无法分诊的字。它通常就是你刚写进 `## Report` 那节的第一行，压成一行。脚本会把换行压掉、超过 160 字符截断，所以别想把证据塞进去。

派发方 pane 里收到的样子，状态在最前：

```
DONE: verifyToken 的毫秒/秒比较已修好，auth 测试 14 passed
Report in: /Users/me/proj/docs/tmux-channel/20260426-1930-fix-verify-token.md

[reply from tmux pane %7, re: the task you dispatched. The status line above is the outcome; the evidence behind it is the last "## Report" section of that document.]
```

**必须且只能**通过脚本发送，绝不要直接用 `tmux send-keys` 发报告正文。脚本做的事：文档最后一节不是你的报告就拒发、状态行没有那三个前缀就拒发、把路径解析成绝对路径、bracketed paste 让这两行不会各自提交一次、Enter 单独发一次让派发方的 TUI 真的收到、盖上你的 pane id、以及派发方 pane 已消失时明确报错——那意味着活干了、报告也安全落在磁盘上，只是没人被通知到。这种情况要连同文档路径告诉你自己这边的用户。

## 一个任务只敲一次门

发一次，然后停。不要再补一条确认；如果派发方回答了你的 `QUESTION`，把那个回答当成要执行的指令，而不是需要回执的消息。

原因是结构性的：进入一个 pane 的每条消息都会给那边的 agent 开启一个新轮次。两个 agent 各自讲礼貌，就会无限互致谢，而且双方都在烧真金白银的 token。只有确实有新实质时才敲第二次——后续发现、更晚出现的失败、第一次回报之后才完成的工作——而且那时要追加一节新的 `## Report`，不要去改旧的那节。
