---
name: wikijs
description: |
  查询、搜索、读取、发布和更新公司内网 Wiki.js（http://192.168.251.30:3000）上的文档，通过 GraphQL API 操作。只要用户提到 wiki、wikijs、内网文档、知识库，想查找或搜索部署信息、服务器信息、数据库信息、中间件、应用配置等运维资料，或想把文档、笔记、总结、部署记录发布/更新到 wiki，就使用本 skill——即使用户没有明确说出"wikijs"这个词。
when_to_use: |
  用户说「查下 wiki」「搜下内网文档」「xxx 的部署信息在哪」「把这个发布到 wiki」「更新一下 wiki 上那篇 xxx」时触发；查询运维知识库（服务器、数据库、中间件、应用部署）时同样触发。
disable-model-invocation: false
---

# 内网 Wiki.js 操作

通过 GraphQL API 操作公司内网 Wiki.js，完成查询、搜索、读取、发布、更新页面。

## 基本信息

- **GraphQL 端点**: `${WIKIJS_URL:-http://192.168.251.30:3000}/graphql`（可用 `WIKIJS_URL` 环境变量覆盖基址）
- **认证**: HTTP 头 `Authorization: Bearer $WIKIJS_TOKEN`（环境变量）
- **站点 locale**: `zh`（所有读写操作都用这个值）
- **编辑器**: `markdown`

开始任何操作前先确认 token 存在：

```bash
[ -n "$WIKIJS_TOKEN" ] && echo ok || echo missing
```

如果输出 `missing`，停下来告诉用户：请在 `~/.zshrc`（或对应 shell 配置）中添加 `export WIKIJS_TOKEN=<你的token>` 后重启会话，token 可在 Wiki.js 管理后台的 API Access 页面生成。不要继续尝试其他获取 token 的方式。

## 通用调用模式

所有操作都是向端点 POST 一个 JSON（`{"query": "...", "variables": {...}}`）：

```bash
curl -s -m 10 -X POST "${WIKIJS_URL:-http://192.168.251.30:3000}/graphql" \
  -H "Authorization: Bearer $WIKIJS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"..."}'
```

内容较长（发布/更新正文）时不要在 shell 里拼接转义——用 Python 生成 payload 文件再 `curl -d @payload.json`，见下文发布模板。临时文件放在 scratchpad 目录。

## 查询与搜索

### 列出所有页面

```graphql
{ pages { list { id path title description isPublished updatedAt } } }
```

页面总量约 100，直接全量拉取再自己过滤是可行且常用的兜底手段。

### 关键词搜索

```graphql
{ pages { search(query: "关键词") { results { id title path description } totalHits } } }
```

**中文搜索要拆词**：搜索接口对长中文短语匹配很差（搜"nas的测试环境"可能零结果）。把用户的问题拆成独立关键词分别搜（如"NAS"、"测试环境"），合并结果。英文缩写、产品名（kafka、jira、ceph）单独搜效果最好。搜不到时退回全量 `list` 按 path/title 过滤。

**注意**：search 返回的 `id` 是哈希字符串，不是页面数字 id，不能用于 `single`/`update`。拿到结果后用 `path` 走 `singleByPath` 读取内容。

### 读取页面内容

按路径（搜索结果衔接用这个）：

```graphql
{ pages { singleByPath(path: "app/kafka/info", locale: "zh") { id path title content updatedAt } } }
```

按数字 id（来自 `list` 或创建/更新的返回值）：

```graphql
{ pages { single(id: 120) { id path title content updatedAt } } }
```

## 发布新页面

发布前先做两件事，避免破坏 wiki 结构：

1. **查重**：搜索或 list 确认没有内容重复的已有页面；如有，改为更新那个页面。
2. **选对路径**：浏览现有目录结构，把新页面放进合适的分类。现有顶级目录及约定：
   - `app/<应用名>/...` — 应用信息（部署服务器、状态、启动命令、关联的数据库/中间件，页面间要互相加链接）
   - `服务器信息/` — 每台服务器一页
   - `基础设施/`（含 `数据库信息/`）、`中间件信息/`、`knowledge/`、`汇理/`、`test/`（测试用）
   - 目录可以有同名页面作为描述页（保证面包屑可用），新建深层路径时如果父级没有页面，考虑一并创建。

路径规则：不以 `/` 开头，可用中文，用 `-` 代替点号（如 `192-168-251-30`）。

发布模板（长内容安全写法）：

```bash
cat > content.md <<'MDEOF'
# 页面正文（markdown）
...
MDEOF

python3 - <<'PYEOF'
import json
payload = {
    "query": """mutation Create($content: String!, $title: String!, $path: String!, $desc: String!) {
      pages { create(content: $content, description: $desc, editor: "markdown",
        isPublished: true, isPrivate: false, locale: "zh",
        path: $path, tags: [], title: $title) {
        responseResult { succeeded errorCode message } page { id path title } } } }""",
    "variables": {
        "content": open("content.md").read(),
        "title": "页面标题",
        "path": "app/xxx/yyy",
        "desc": "一句话描述",
    },
}
json.dump(payload, open("payload.json", "w"), ensure_ascii=False)
PYEOF

curl -s -m 10 -X POST "${WIKIJS_URL:-http://192.168.251.30:3000}/graphql" \
  -H "Authorization: Bearer $WIKIJS_TOKEN" -H "Content-Type: application/json" \
  -d @payload.json
```

所有字段（`description`、`editor`、`isPublished`、`isPrivate`、`locale`、`tags`、`title`、`path`、`content`）都必须提供，缺字段会报错。

## 更新已有页面

先用 `single`/`singleByPath` 读出当前内容，在其基础上修改（不要凭空重写整页，会丢掉别人写的内容），再提交：

```graphql
mutation Update($id: Int!, $content: String) {
  pages { update(id: $id, content: $content, editor: "markdown", isPublished: true, tags: []) {
    responseResult { succeeded errorCode message } page { id updatedAt } } }
}
```

**关键坑**：`update` 必须显式带上 `tags` 字段，否则 Wiki.js 2.x 报 `Cannot read properties of undefined (reading 'map')`。如果原页面本来有标签，先从读取结果里拿到 `tags` 原样传回，避免清空标签。长内容同样走 payload 文件方式。

## 操作完成后

- 发布/更新成功后，把页面链接给用户：`http://192.168.251.30:3000/<path>`。
- 检查 `responseResult.succeeded`，失败时把 `message` 原样报告给用户，不要静默重试超过一次。

## 删除

删除不属于常规操作。仅当用户明确要求删除某个页面时，先复述页面标题和路径请用户确认，确认后执行：

```graphql
mutation { pages { delete(id: <数字id>) { responseResult { succeeded message } } } }
```
