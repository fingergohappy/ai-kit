---
name: learn
description: |
  用最简单的方式帮助用户理解概念，通过最小示例、简化和代码类比。
  Help the user understand a concept in the simplest way possible using minimal examples, simplification, and code analogies.
when_to_use: |
  当用户说「学」「学习」「解释」「举例」「举个例子」「simplify」「explain」时触发。
  或者用户问了一个概念性问题想快速理解，或者用户想让复杂内容变简单，或者用户想用类比理解某个东西。
argument-hint: "<topic or question>"
---

# learn

用最简单的方式帮用户理解一个概念。核心理念：**一个概念 = 它解决什么问题 + 没有它会怎样 + 一个最小例子 + 代码类比**。

## First trigger

如果是本次对话第一次触发，先问用户：

> 你熟悉哪些语言和框架？

后续的所有例子和类比都基于用户熟悉的技术栈来构建。如果对话中已经能判断用户的技术背景（从项目代码、上下文），跳过这一步。

## Two input modes

1. **提问** — 用户问一个概念性问题，给出最简例子和类比
2. **简化** — 用户给出现有内容（代码、文档、URL），简化到核心

两种情况都遵循相同的输出格式。

## Output format

每次回答都使用以下结构，不遗漏任何部分：

```
## 解决什么问题

一句话说清：这个东西为什么存在，它解决什么痛点。

## 没有它会怎样

用代码展示没有这个概念时的写法，让用户直观感受到痛点。
通常就是"手写的笨办法"。

## 最简例子

只保留理解核心所需的代码/步骤。砍掉一切非必要细节。
如果已有代码需要简化，保留骨架，删除装饰。

## 代码类比

用用户熟悉的技术栈中的等价概念来类比。
精准到机制层面：语法、行为、设计模式都可以类比。
```

## Save as learning test

解释完之后，问用户：

> 要把这个例子保存为学习测试吗？

如果用户同意，将最简例子写成一个**可运行的单元测试**，放到项目的测试目录中。

### Locate test directory

根据项目结构自动判断，在现有测试目录下创建 `learn/` 子目录。不确定时直接问用户。

### Test file rules

- 每个概念一个测试文件，遵循项目的测试文件命名惯例
- 每个关键行为一个 test case，命名用自然语言描述知识点
- 测试必须能跑通（assert 实际行为，不是空断言）
- 关键行有注释解释

举个例子 — 比如 Go 项目学 channel：

```go
func TestChannelSendAndReceive(t *testing.T) {
    ch := make(chan string, 1) // 带缓冲的 channel
    ch <- "hello"              // 发送
    got := <-ch                // 接收
    assert.Equal(t, "hello", got)
}
```

或者 Node.js 项目学 Promise：

```js
test('promise resolves with value', async () => {
    const p = Promise.resolve(42) // 立即 resolved
    const result = await p
    expect(result).toBe(42)
})
```

如果已存在同名文件，覆盖。

## Rules for simplifying existing content

当用户提供代码或文档要求简化时：

1. 先识别核心机制（通常只有 1-3 个关键点）
2. 删掉所有错误处理、配置、边界情况、样式、日志
3. 只保留骨架，每一行都对应一个核心概念
4. 在简化后的代码旁标注：这行对应原文的哪个部分

## About examples

好的最简例子：
- 10 行以内的代码，或 3 步以内的流程
- 能直接运行（或能直接在脑子里跑）
- 只展示一个概念

坏的例子：
- 完整的生产代码
- 包含错误处理和边界检查
- 同时展示多个概念

## About code analogies

类比要用用户熟悉的语言/框架中的等价概念，不是生活比喻。

精准到机制层面的类比：

| 概念 | 好（代码类比） | 坏（生活比喻） |
|------|---------------|---------------|
| Rust 所有权 | C++ 的 unique_ptr — 同一时刻只有一个持有者 | "像借书" — 没说清机制 |
| React Context | Vue 的 provide/inject — 跨层级传数据不用 props 层层透传 | "像广播" — 太模糊 |
| Go goroutine | Python 的 asyncio — 轻量并发，但 goroutine 是 M:N 调度 | "像线程" — 没解释区别 |
| Docker | Node.js 的 nvm — 隔离运行环境，只是 Docker 隔离的是整个系统 | "像虚拟机" — 没说清区别 |

选择用户熟悉的语言/框架来做类比。如果用户说熟悉 Python，就用 Python 的概念类比，不要用 Haskell。

## Language

跟随用户的语言。用户用中文就用中文，中英混合就混合。

## Notes

- 不要展开讲。用户追问了再深入。
- 如果用户明显只需要最简例子，省略类比部分。
- 代码例子用用户正在用的语言，除非概念本身绑定特定语言。
- 不要写成教程。这不是教程。
