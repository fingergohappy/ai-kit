---
name: wikijs
description: Query, search, read, publish, and update pages on the internal Wiki.js (http://192.168.251.30:3000) via its GraphQL API. Use whenever the user mentions wiki, wikijs, 内网文档, 知识库, wants to look up ops documentation (部署信息、服务器信息、数据库信息、中间件、应用配置 — deployments, servers, databases, middleware), or wants to publish or update docs, notes, summaries, or deployment records to the wiki — even if they never say the word "wikijs".
---

# Internal Wiki.js Operations

Operate the company's internal Wiki.js through its GraphQL API: query, search, read, publish, and update pages.

## Basics

- **GraphQL endpoint**: `${WIKIJS_URL:-http://192.168.251.30:3000}/graphql` (override the base URL with the `WIKIJS_URL` env var if set)
- **Auth**: HTTP header `Authorization: Bearer $WIKIJS_TOKEN` (environment variable)
- **Site locale**: `zh` (use this value for every read and write)
- **Editor**: `markdown`

Before any operation, confirm the token exists:

```bash
[ -n "$WIKIJS_TOKEN" ] && echo ok || echo missing
```

If it prints `missing`, stop and tell the user: add `export WIKIJS_TOKEN=<token>` to `~/.zshrc` (or the shell profile) and restart the session; tokens are generated in the Wiki.js admin panel under API Access. Do not try other ways of obtaining a token.

## General call pattern

Every operation is a POST of a JSON body (`{"query": "...", "variables": {...}}`) to the endpoint:

```bash
curl -s -m 10 -X POST "${WIKIJS_URL:-http://192.168.251.30:3000}/graphql" \
  -H "Authorization: Bearer $WIKIJS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"..."}'
```

For long content (page bodies), never hand-escape quotes in shell — generate the payload file with Python and use `curl -d @payload.json` (see the publish template below). Keep temp files in the scratchpad directory.

## Query and search

### List all pages

```graphql
{ pages { list { id path title description isPublished updatedAt } } }
```

The wiki holds only ~100 pages, so pulling the full list and filtering yourself is a viable and common fallback.

### Keyword search

```graphql
{ pages { search(query: "keyword") { results { id title path description } totalHits } } }
```

**Split Chinese phrases into keywords**: the search endpoint matches long Chinese phrases poorly (searching "nas的测试环境" may return nothing). Break the user's question into standalone keywords (e.g. "NAS", "测试环境"), search each, and merge results. English abbreviations and product names (kafka, jira, ceph) work best searched alone. When search comes up empty, fall back to the full `list` filtered by path/title.

**Caveat**: `search` returns hash-string `id`s, not numeric page ids — they cannot be fed to `single`/`update`. Take the `path` from a result and read content via `singleByPath`.

### Read page content

By path (the natural follow-up to a search result):

```graphql
{ pages { singleByPath(path: "app/kafka/info", locale: "zh") { id path title content updatedAt } } }
```

By numeric id (from `list` or a create/update response):

```graphql
{ pages { single(id: 120) { id path title content updatedAt } } }
```

## Publish a new page

Do two things first, to avoid damaging the wiki's structure:

1. **Check for duplicates**: search or list to confirm no existing page covers the same content; if one does, update that page instead.
2. **Pick the right path**: browse the existing tree and place the new page in the proper category. Current top-level directories and conventions:
   - `app/<application>/...` — application info (deployment servers, status, start commands, linked databases/middleware; cross-link related pages)
   - `服务器信息/` — one page per server
   - `基础设施/` (contains `数据库信息/`), `中间件信息/`, `knowledge/`, `汇理/`, `test/` (for experiments)
   - A directory may have a same-named page acting as its description page (keeps breadcrumbs working); when creating a deep path whose parents have no page, consider creating those too.

Path rules: no leading `/`; Chinese is fine; replace dots with `-` (e.g. `192-168-251-30`).

Publish template (safe for long content):

```bash
cat > content.md <<'MDEOF'
# Page body (markdown)
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
        "title": "Page title",
        "path": "app/xxx/yyy",
        "desc": "One-line description",
    },
}
json.dump(payload, open("payload.json", "w"), ensure_ascii=False)
PYEOF

curl -s -m 10 -X POST "${WIKIJS_URL:-http://192.168.251.30:3000}/graphql" \
  -H "Authorization: Bearer $WIKIJS_TOKEN" -H "Content-Type: application/json" \
  -d @payload.json
```

All fields (`description`, `editor`, `isPublished`, `isPrivate`, `locale`, `tags`, `title`, `path`, `content`) are required — omitting any of them errors out.

## Update an existing page

First read the current content with `single`/`singleByPath` and modify on top of it (never rewrite a page from scratch — you would wipe out what others wrote), then submit:

```graphql
mutation Update($id: Int!, $content: String) {
  pages { update(id: $id, content: $content, editor: "markdown", isPublished: true, tags: []) {
    responseResult { succeeded errorCode message } page { id updatedAt } } }
}
```

**Critical gotcha**: `update` must explicitly include the `tags` field, or Wiki.js 2.x fails with `Cannot read properties of undefined (reading 'map')`. If the page already has tags, pass them back unchanged from the read result so they aren't cleared. Long content goes through the payload-file pattern as above.

## After the operation

- On successful publish/update, give the user the page link: `http://192.168.251.30:3000/<path>`.
- Check `responseResult.succeeded`; on failure report the `message` verbatim to the user and do not silently retry more than once.

## Delete

Deletion is not a routine operation. Only when the user explicitly asks to delete a page, restate its title and path and get their confirmation, then run:

```graphql
mutation { pages { delete(id: <numeric id>) { responseResult { succeeded message } } } }
```
