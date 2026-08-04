---
name: tmux_reply
description: |
  向派活给你的那个 tmux pane 回报结果。当你手上的任务是从别的 pane 派过来的（消息里带着 `[dispatched from tmux pane %5, loop: ...]` 这样的戳），而你现在做完了、卡住了、或者需要派发方拍板时，主动使用——不用等人再问一遍。用户说「通知 5」「告诉派活给我那个 pane」「回报一下进展」「跟 %3 说我做完了」时同样触发。这是 tmux_dispatch 的返回半程：派发方从不轮询你，报告不发出去就等于没人知道这活干过。
when_to_use: |
  当前任务带着 `[dispatched from tmux pane %N]` 戳且已完成或卡住时触发；或用户说「通知 {number}」「回报给 {number}」「告诉那个派活的 pane」「跟 {number} 说我做完了」时触发。
argument-hint: "[<pane_id>] [<消息>]"
disable-model-invocation: false
---

# tmux_reply

把报告发回给派活给你的那个 pane。

为什么这件事需要专门写下来：派发方是**故意**不看着你的。它把任务交出去就走了，所以没有进度条、没有轮询、没有超时——唯一能闭合这个环的就是你发出这条消息。活干完了却不说话，和从来没开始过，在派发方看来一模一样。

## 找到派发方的 pane id

它就在你收到的任务的戳里：`[dispatched from tmux pane %5, loop: false. When you finish, ...]`。那个 `%5` 就是目标——回头看启动这项工作的那条消息，不要从当前 tmux 布局里猜。

留意同一个戳里的 `loop` 值：如果是 `loop: true`，发送时要加 `--loop`（见下）。这个标志是在告诉派发方的 `gate-review`「可以不请示就把修复发回来」，而戳是它唯一能活过这趟往返的地方——丢了它，一个本该无人值守的循环就会悄无声息地变成等人的循环。

如果任务上没有戳，那它不是派发来的，没人在等报告，正常回答用户就好。如果你确信需要回报但找不到 pane id，用纯文本询问——不要列 pane 清单，也不要发给一个你推断出来的 pane，报告落进陌生人的 session 比迟到更糟。

## 写报告

派发方是另一个 agent，你的消息到那边是一个全新的轮次，带不过去任何你的工作上下文。它必须一眼判断这个任务是否已经关闭，所以先给结论，再给支撑：

- **第一行就是判定**：`DONE: …`、`BLOCKED: …` 或 `QUESTION: …`。没有比这更快能读懂的，而这三种情况下派发方的下一步动作完全不同。
- **所有碰过的文件用绝对路径。** 派发方可能在别的目录或别的 worktree。
- **给证据，不是给保证。** 「跑了什么命令 + 实际输出」胜过「测试通过了」——派发方可能要把这话转述给一个会去核对的用户。
- **说清你没做什么**，以及为什么：跳过的范围、你判断超出边界的修复、你不得不做的猜测。沉默的省略会变成派发方的 bug。
- **`BLOCKED` / `QUESTION` 要点明需要什么决定**，以及你已经试过什么。含糊的阻塞只会把这趟往返又弹回给你。

单薄 —— `做完了`

有实质：

```
DONE: 修好了 verifyToken 的毫秒/秒比较问题。
改动：/Users/me/proj/src/auth.ts:42 改为 `payload.exp < Date.now()`；
新增 /Users/me/proj/test/auth.test.ts 里的 "freshly signed token is valid" 用例。
验证：cd /Users/me/proj && npm test -- auth → 14 passed, 0 failed。
未处理：refreshToken 里有同样的秒/毫秒混用（auth.ts:71），按你的要求没动。
```

只写派发方为了行动所需要的东西。把你调试的完整经过铺开，只会让它多读一遍，而且没有一个字是它能用的。

## 脚本路径

所有 `scripts/` 路径相对于**本 SKILL.md 文件所在目录**。执行前必须先解析为绝对路径，因为插件可能装在缓存目录而不是仓库里：

```bash
SKILL_DIR="<本 SKILL.md 所在目录的绝对路径>"
```

## 发送

```bash
# 短报告，直接传内容
bash "$SKILL_DIR/scripts/reply.sh" "<pane_id>" "<消息>"

# 长报告或多行 —— 先写文件，传路径
bash "$SKILL_DIR/scripts/reply.sh" "<pane_id>" "/tmp/reply.txt"

# 收到的任务戳着 loop: true —— 原样带回去
bash "$SKILL_DIR/scripts/reply.sh" "<pane_id>" "/tmp/reply.txt" --loop
```

报告一旦是多行、含反引号或引号，就用文件形式——shell 转义会静默弄乱报告，而一份乱码报告比没有报告更糟。

**必须且只能**通过脚本发送，绝不要直接用 `tmux send-keys` 发报告文本。脚本处理的是：bracketed paste 让多行报告不会一行一行自己提交、Enter 单独发一次让派发方的 TUI 真的收到、盖上你的 pane id、校验目标以免一个过期的 pane id 把报告粘进当前活动 pane、以及派发方 pane 已消失时明确报错——那意味着活干了但报告无处可去，值得告诉你自己这边的用户。

## 一个任务只回报一次

发一次，然后停。不要再补一条确认；如果派发方回答了你的 `QUESTION`，把那个回答当成要执行的指令，而不是需要回执的消息。

原因是结构性的：进入一个 pane 的每条消息都会给那边的 agent 开启一个新轮次。两个 agent 各自讲礼貌，就会无限互致谢，而且双方都在烧真金白银的 token。只有确实有新实质时才发第二条：后续发现、更晚出现的失败、第一次回报之后才完成的工作。
