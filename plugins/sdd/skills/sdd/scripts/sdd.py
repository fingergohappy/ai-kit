#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sdd.py - REQ / CR / spec / review 工作流的确定性部分.

只依赖 Python 3 标准库, Claude Code / Codex / pi 下都能直接跑.
文档根默认 docs/sdd (从当前目录向上查找), 可用 --root 或环境变量 SDD_ROOT 覆盖.

子命令:
  init                    建目录 + INDEX + notcommit/.gitignore (约定只在 skill 里, 不放 README)
  status [CR-NNN] [--write]  全局状态; 给 CR 时输出 8 关的进度表 (每关带文件证据) 与下一步;
                          --write 另把这份表写进工作目录的 PROGRESS.md
  next-id REQ|CR          下一个可用编号
  new-req <slug> [标题]    从模板建 REQ
  new-cr <slug> [标题] [--new]   从模板建 CR (--new: 新增业务的立项 CR; 不带则是变更 CR).
                          同时把草稿目录 notcommit/<slug> 改名为 CR 目录
  new-draft <slug|CR-NNN> <topic>   建草稿文件
  new-spec <CR-NNN>       从模板建实施 spec
  new-review <CR-NNN> docs|spec|impl   从模板建 review
  validate                一致性检查 (退出码: 有 error 时 1)
  index                   重新生成 INDEX.md
  lessons [--init] [--next-id]   错题本 docs/sdd/lessons.md: 摘要 / 建文件 / 下一个 L 编号
  prune <CR-NNN> [--dry-run] [--keep draft|spec|reviews]
                          删除 CR 工作目录里的 draft/ spec.md reviews/ (--keep 逐项保留);
                          CR fixed, 各 review fixed 且头部 "提炼" 已填, 才删
"""
import argparse
import datetime as _dt
import os
import re
import shutil
import subprocess
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATES = os.path.normpath(os.path.join(HERE, "..", "assets", "templates"))

REQ_STATUS = ("draft", "implemented", "superseded", "retired")
CR_STATUS = ("to fix", "fixing", "fixed", "rejected")
REVIEW_STATUS = ("to fix", "fixing", "fixed")
STAGES = ("docs", "spec", "impl")
STAGE_FILE = {"docs": "01-docs.md", "spec": "02-spec.md", "impl": "03-impl.md"}
STAGE_PREFIX = {"docs": "D", "spec": "S", "impl": "I"}
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ID_RE = re.compile(r"^(REQ|CR)-(\d{3,})-([a-z0-9-]+)\.md$")


# ---------- 基础 ----------

def die(msg, code=2):
    sys.stderr.write("错误: %s\n" % msg)
    sys.exit(code)


def today():
    return _dt.date.today().isoformat()


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def git_head(root):
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=root,
                             capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or "(无 git)"
    except Exception:
        return "(无 git)"


def find_root(explicit):
    if explicit:
        return os.path.abspath(explicit)
    env = os.environ.get("SDD_ROOT")
    if env:
        return os.path.abspath(env)
    cur = os.getcwd()
    while True:
        cand = os.path.join(cur, "docs", "sdd")
        if os.path.isdir(os.path.join(cand, "req")) and os.path.isdir(os.path.join(cand, "cr")):
            return cand
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def need_root(args):
    root = find_root(args.root)
    if not root:
        die("找不到 docs/sdd (需含 req/ 与 cr/). 先运行 `sdd.py init`, 或用 --root 指定.")
    return root


COMMENT_RE = re.compile(r"<!--.*?-->", re.S)


FRONTMATTER_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n?", re.S)
FM_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(.*)$")


def _strip_comment(v):
    """剥行尾注释. 引号内的 # 不算; 必须在判断值的类型之前做 -- 否则 `>- # 说明` 不等于 `>-`,
    `[L-1] # ... [L-3] ...` 的右括号也会找错."""
    v = v.strip()
    if v.startswith("#"):     # 整行只有注释 (如 `affects:   # 说明`)
        return ""
    if v[:1] in ('"', "'"):
        end = v.find(v[0], 1)
        if end > 0:
            tail = v[end + 1:]
            return v[:end + 1] if "#" in tail else v
    i = v.find(" #")
    return v[:i].rstrip() if i >= 0 else v


def _scalar(raw):
    """标量: 引号 / 布尔 / null / 裸串 (中文, 空格, 括号原样保留)."""
    v = _strip_comment(raw)
    if v[:1] in ('"', "'"):
        end = v.find(v[0], 1)
        if end > 0:
            return v[1:end]
    low = v.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    return v


def parse_frontmatter(text, where=""):
    """解析文档头部的 YAML frontmatter, 只认这几种写法 (够用且能自己解析, 不依赖 PyYAML):

        key: 标量            key: [a, b]          key:            key: >-
                                                    - a             一段折叠成
                                                    - b             一行的文字

    嵌套映射不支持 -- 用不到, 遇到直接报错, 免得静默解析成别的东西.
    返回 (dict, 正文); 没有 frontmatter 返回 (None, 原文).
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None, text
    body, lines, data, i = text[m.end():], m.group(1).split("\n"), {}, 0
    while i < len(lines):
        line = lines[i].rstrip(); i += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        km = FM_KEY_RE.match(line)
        if not km:
            die("%s frontmatter 无法解析的行: %r\n  只支持 key: 标量 / key: [a, b] / key: 后跟 \"- 项\" / key: >- 块标量" % (where, line))
        key, rest = km.group(1), _strip_comment(km.group(2))
        if rest in (">", ">-", "|", "|-"):
            buf = []
            while i < len(lines) and (not lines[i].strip() or lines[i][:1] in (" ", "\t")):
                buf.append(lines[i].strip()); i += 1
            sep = " " if rest[0] == ">" else "\n"
            data[key] = sep.join(x for x in buf if x)
        elif rest == "":
            items = []
            while i < len(lines) and lines[i].lstrip().startswith("- "):
                items.append(_scalar(lines[i].lstrip()[2:])); i += 1
            data[key] = items
        elif rest.startswith("["):
            inner = rest[1:rest.rfind("]")] if "]" in rest else rest[1:]
            data[key] = [_scalar(x) for x in inner.split(",") if x.strip()]
        else:
            data[key] = _scalar(rest)
    return data, body


# 旧写法 (正文顶部的 | 字段 | 值 | 表) -> frontmatter 的键. 迁移期降级用, 会出警告.
LEGACY_FIELDS = (("编号", "id"), ("状态", "status"), ("创建日期", "created"), ("最后更新", "updated"),
                 ("提出日期", "created"), ("关联需求", "related"), ("影响需求", "affects"),
                 ("立项需求", "affects"), ("摘要", "summary"), ("变更", "cr"), ("基点", "base"),
                 ("阶段", "stage"), ("结论", "verdict"), ("审查者", "reviewer"), ("日期", "date"),
                 ("提炼", "distilled"), ("关联", "key"), ("性质", "kind"), ("主题", "topic"))


def table_field(text, name):
    m = re.search(r"^\|\s*%s\s*\|\s*(.*?)\s*\|\s*$" % re.escape(name), text, re.M)
    return COMMENT_RE.sub("", m.group(1)).strip() if m else None


def doc_meta(text, where=""):
    """(元数据 dict, 是否旧表格写法). 优先 frontmatter, 没有则回退旧表格."""
    d, _ = parse_frontmatter(text, where)
    if d is not None:
        return d, False
    d = {}
    for zh, en in LEGACY_FIELDS:
        v = table_field(text, zh)
        if v and not d.get(en):
            d[en] = v
    return d, True


FM_RISKY_RE = re.compile(r"[:]\s")


def fm_lint(text, where):
    """检查 frontmatter 里的裸标量会不会被标准 YAML 解析器读成别的东西.

    我们自己的解析器很宽容, 但 pi / Obsidian / GitHub 用的是标准解析器: 裸标量里出现 ": "
    会被当成嵌套映射 (\"Nested mappings are not allowed\"), 以 [ { & * ! | > % @ ` 开头会被
    当成流式集合或指令. 这类值必须加引号或写成 >- 块标量. 返回警告列表.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        return []
    out, lines, i = [], m.group(1).split("\n"), 0
    while i < len(lines):
        line = lines[i]; i += 1
        st = line.strip()
        if not st or st.startswith("#"):
            continue
        km = FM_KEY_RE.match(line)
        if km and km.group(2).strip() in (">", ">-", "|", "|-"):
            while i < len(lines) and (not lines[i].strip() or lines[i][:1] in (" ", "\t")):
                i += 1                      # 块标量内部随便写, 跳过
            continue
        val = km.group(2).strip() if km else (st[2:].strip() if st.startswith("- ") else "")
        key = km.group(1) if km else "列表项"
        if not val or val[:1] in ('"', "'") or val.startswith("["):
            continue
        if FM_RISKY_RE.search(val):
            out.append("%s: frontmatter `%s` 的值含 \": \", 标准 YAML 会读成嵌套映射 -- 加引号或用 >-: %s" % (where, key, val[:60]))
        elif val[0] in "[]{}&*!|>%@`":
            out.append("%s: frontmatter `%s` 的值以 %r 开头, 标准 YAML 会当语法 -- 加引号: %s" % (where, key, val[0], val[:60]))
    return out


def as_list(v):
    """frontmatter 里是列表就原样; 旧写法是一整串 (内含 \"(FR-8, AC-8)\" 这类逗号), 不切开."""
    if v is None or v == "" or v is False:
        return []
    return list(v) if isinstance(v, list) else [v]


def h1(text):
    """一级标题, 去掉 "REQ-001: " 这类编号前缀."""
    m = re.search(r"^#\s+(.+?)\s*$", text, re.M)
    if not m:
        return ""
    return re.sub(r"^(?:REQ|CR)-\d+\s*[:：]\s*", "", m.group(1).strip())


def list_docs(root, kind):
    d = os.path.join(root, "req" if kind == "REQ" else "cr")
    out = []
    if not os.path.isdir(d):
        return out
    for fn in sorted(os.listdir(d)):
        m = ID_RE.match(fn)
        if m and m.group(1) == kind:
            out.append({"id": "%s-%s" % (m.group(1), m.group(2)), "num": int(m.group(2)),
                        "slug": m.group(3), "path": os.path.join(d, fn), "file": fn})
    return out


def next_id(root, kind):
    nums = [d["num"] for d in list_docs(root, kind)]
    return "%s-%03d" % (kind, (max(nums) + 1) if nums else 1)


def cr_dir(root, cr_id):
    """notcommit/CR-NNN-<slug>/ ; 不存在返回 None."""
    nc = os.path.join(root, "notcommit")
    if not os.path.isdir(nc):
        return None
    for fn in os.listdir(nc):
        if fn.startswith(cr_id + "-") and os.path.isdir(os.path.join(nc, fn)):
            return os.path.join(nc, fn)
    return None


def find_cr(root, cr_id):
    for d in list_docs(root, "CR"):
        if d["id"] == cr_id:
            return d
    return None


def fill(template_name, mapping):
    path = os.path.join(TEMPLATES, template_name)
    if not os.path.isfile(path):
        die("模板缺失: %s" % path)
    text = read(path)
    for k, v in mapping.items():
        text = text.replace("{{%s}}" % k, v)
    return text


# ---------- 解析 REQ / CR / review / spec ----------

FR_RE = re.compile(r"\*\*(FR-\d+)\*\*")
BR_RE = re.compile(r"\b(BR-\d+)\b")
AC_RE = re.compile(r"\*\*(AC-\d+)\*\*\s*\(([^)]*)\)")
ITEM_REF_RE = re.compile(r"\b((?:FR|BR|AC)-\d+)\b")
REQ_REF_RE = re.compile(r"\b(REQ-\d{3,})\b")
CR_REF_RE = re.compile(r"\b(CR-\d{3,})\b")


def parse_req(path):
    t = read(path)
    frs = set(FR_RE.findall(t))
    brs = set(BR_RE.findall(t))
    acs = {}
    for ac, src in AC_RE.findall(t):
        acs[ac] = set(ITEM_REF_RE.findall(src))
    log = t[t.rfind("## 变更记录"):] if "## 变更记录" in t else ""
    m, legacy = doc_meta(t, path)
    return {"text": t, "status": m.get("status"), "id": m.get("id"),
            "title": h1(t), "summary": m.get("summary") or "", "related": as_list(m.get("related")),
            "legacy": legacy, "frs": frs, "brs": brs, "acs": acs, "log": log}


def parse_cr(path):
    t = read(path)
    m, legacy = doc_meta(t, path)
    affects = {}
    # 每项形如 "REQ-006 (FR-8, AC-8)"; 立项 CR 写 "REQ-009 (全文)" 则条目集为空.
    # 编号后允许跟 markdown 链接尾 "](...)" (旧表格写法), 再跟条目括号.
    for entry in as_list(m.get("affects")):
        for mm in re.finditer(r"(REQ-\d{3,})(?:\]\([^)]*\))?\s*(?:\(([^)]*)\))?", str(entry)):
            affects.setdefault(mm.group(1), set()).update(ITEM_REF_RE.findall(mm.group(2) or ""))
    return {"text": t, "status": m.get("status"), "id": m.get("id"), "kind": m.get("kind") or "change",
            "title": h1(t), "summary": m.get("summary") or "", "affects": affects, "legacy": legacy}


FINDING_ROW_RE = re.compile(r"^\|\s*([DSI]-\d+)\s*\|(.*)$", re.M)


def parse_review(path):
    t = read(path)
    rows = []
    for m in FINDING_ROW_RE.finditer(t):
        cells = [c.strip() for c in m.group(2).strip().strip("|").split("|")]
        rows.append({"id": m.group(1), "cells": cells})
    m, legacy = doc_meta(t, path)
    return {"text": t, "status": m.get("status"), "verdict": m.get("verdict"),
            "stage": m.get("stage"), "rows": rows, "distill": m.get("distilled"), "legacy": legacy}


def distilled(value):
    """distilled: [L-1, L-3] 或 "无可提炼: 理由" 算已提炼; false / 空 / "待提炼" 算未提炼."""
    if isinstance(value, bool):
        return value
    if isinstance(value, list):
        return len(value) > 0
    v = (value or "").strip()
    return bool(v) and not v.startswith("待提炼")


def lesson_ids(value):
    if isinstance(value, list):
        return [x for x in value if isinstance(x, str) and re.fullmatch(r"L-\d+", x.strip())]
    return re.findall(r"\bL-\d+\b", value if isinstance(value, str) else "")


LESSON_ROW_RE = re.compile(r"^\|\s*(L-\d+)\s*\|", re.M)


def lessons_path(root):
    return os.path.join(root, "lessons.md")


def lesson_ids_in_file(root):
    p = lessons_path(root)
    return set(LESSON_ROW_RE.findall(read(p))) if os.path.isfile(p) else set()


def review_findings_open(rv):
    """处置列为空 / 待修 的发现. 列序: 级别 | 车道 | 位置 | 发现 | 最小修复 | 处置 | 复核"""
    open_ = []
    for r in rv["rows"]:
        disp = r["cells"][5] if len(r["cells"]) > 5 else ""
        if not disp or disp in ("待修", "-"):
            open_.append(r["id"])
    return open_


def spec_steps(path):
    """§4 表: 返回 (总步数, 待办步数). 找不到表则 (0, 0)."""
    t = read(path)
    sec = re.search(r"^## 4\..*?(?=^## |\Z)", t, re.M | re.S)
    if not sec:
        return 0, 0
    total = pending = 0
    for line in sec.group(0).splitlines():
        if re.match(r"^\|\s*\d+[a-z]?\s*\|", line):
            total += 1
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not cells or "待办" in cells[-1] or cells[-1] == "":
                pending += 1
    return total, pending


# ---------- 子命令 ----------

def cmd_init(args):
    base = os.path.abspath(args.root or os.path.join(os.getcwd(), "docs", "sdd"))
    for sub in ("req", "cr", "notcommit"):
        os.makedirs(os.path.join(base, sub), exist_ok=True)
    gi = os.path.join(base, "notcommit", ".gitignore")
    if not os.path.exists(gi):
        write(gi, "# 本目录不入库: 草稿, 实施 spec, review 都是与某次 CR 配对的工作文件\n*\n!.gitignore\n")
        print("已建", gi, "(notcommit 整体忽略)")
    write_index(base)
    print("完成. 目录:", base)


def cmd_next_id(args):
    root = need_root(args)
    print(next_id(root, args.kind))


def check_slug(slug):
    if not SLUG_RE.match(slug):
        die("slug 必须是小写字母数字加短横线, 如 openfx-direct-payout, 得到: %r" % slug)


def cmd_new_req(args):
    root = need_root(args)
    check_slug(args.slug)
    for d in list_docs(root, "REQ"):
        if d["slug"] == args.slug:
            die("同 slug 的 REQ 已存在: %s. 改行为请走 /create-cr, 只是订正请直接改它." % d["file"])
    rid = next_id(root, "REQ")
    path = os.path.join(root, "req", "%s-%s.md" % (rid, args.slug))
    write(path, fill("req.md", {"ID": rid, "SLUG": args.slug, "DATE": today(),
                                 "TITLE": args.title or args.slug}))
    draft_dir = os.path.join(root, "notcommit", args.slug, "draft")
    os.makedirs(draft_dir, exist_ok=True)
    print("已建 REQ:", path)
    print("侦察记录放:", draft_dir)
    write_index(root)


def cmd_new_cr(args):
    root = need_root(args)
    check_slug(args.slug)
    cid = next_id(root, "CR")
    path = os.path.join(root, "cr", "%s-%s.md" % (cid, args.slug))
    tmpl = "cr-new.md" if args.new else "cr.md"
    write(path, fill(tmpl, {"ID": cid, "SLUG": args.slug, "DATE": today(),
                             "TITLE": args.title or args.slug}))
    nc = os.path.join(root, "notcommit")
    target = os.path.join(nc, "%s-%s" % (cid, args.slug))
    old = os.path.join(nc, args.slug)
    if os.path.isdir(old):
        if os.path.exists(target):
            # 合并: 把旧目录内容搬过去
            for fn in os.listdir(old):
                shutil.move(os.path.join(old, fn), os.path.join(target, fn))
            os.rmdir(old)
        else:
            os.rename(old, target)
        print("草稿目录已并入:", target)
    for sub in ("draft", "reviews"):
        os.makedirs(os.path.join(target, sub), exist_ok=True)
    print("已建 CR (%s):" % ("新增业务立项" if args.new else "变更"), path)
    print("工作目录:", target)
    write_index(root)


def cmd_new_draft(args):
    root = need_root(args)
    key = args.key
    if CR_REF_RE.fullmatch(key):
        d = cr_dir(root, key)
        if not d:
            die("找不到 %s 的工作目录 (notcommit/%s-*)" % (key, key))
    else:
        check_slug(key)
        d = None
        nc = os.path.join(root, "notcommit")
        if os.path.isdir(nc):
            for fn in os.listdir(nc):
                if re.match(r"^CR-\d+-%s$" % re.escape(key), fn):
                    d = os.path.join(nc, fn)
        d = d or os.path.join(nc, key)
    topic = re.sub(r"[^a-z0-9-]+", "-", args.topic.lower()).strip("-") or "draft"
    path = os.path.join(d, "draft", "%s-%s.md" % (today(), topic))
    if os.path.exists(path):
        die("已存在: %s" % path)
    write(path, fill("draft.md", {"DATE": today(), "TOPIC": args.topic, "KEY": key}))
    print("已建草稿:", path)


def cmd_new_spec(args):
    root = need_root(args)
    cr = find_cr(root, args.cr)
    if not cr:
        die("没有这个 CR: %s" % args.cr)
    d = cr_dir(root, args.cr)
    if not d:
        d = os.path.join(root, "notcommit", "%s-%s" % (cr["id"], cr["slug"]))
        os.makedirs(os.path.join(d, "reviews"), exist_ok=True)
        os.makedirs(os.path.join(d, "draft"), exist_ok=True)
    path = os.path.join(d, "spec.md")
    if os.path.exists(path) and not args.force:
        die("spec 已存在: %s (加 --force 覆盖)" % path)
    write(path, fill("spec.md", {"CR": cr["id"], "SLUG": cr["slug"], "DATE": today(),
                                  "BASE": git_head(os.path.dirname(os.path.dirname(root))),
                                  "TITLE": h1(read(cr["path"])) or cr["slug"]}))
    print("已建 spec:", path)


def cmd_new_review(args):
    root = need_root(args)
    cr = find_cr(root, args.cr)
    if not cr:
        die("没有这个 CR: %s" % args.cr)
    d = cr_dir(root, args.cr)
    if not d:
        die("找不到 %s 的工作目录, 先 new-spec 或 new-draft 建一个" % args.cr)
    path = os.path.join(d, "reviews", STAGE_FILE[args.stage])
    if os.path.exists(path) and not args.force:
        die("review 已存在: %s (加 --force 覆盖; 复审请在原文件追加复核列)" % path)
    write(path, fill("review.md", {"CR": cr["id"], "STAGE": args.stage, "DATE": today(),
                                    "PREFIX": STAGE_PREFIX[args.stage],
                                    "BASE": git_head(os.path.dirname(os.path.dirname(root))),
                                    "REVIEWER": args.reviewer or "(填审查者 / 模型)"}))
    print("已建 review:", path)


# ---------- status ----------

def cr_state(root, cr):
    """收集一个 CR 的全部状态, 供 status / index 用."""
    info = parse_cr(cr["path"])
    d = cr_dir(root, cr["id"])
    st = {"cr": cr, "status": info["status"], "dir": d, "spec": None, "reviews": {},
          "parallel": None}
    if d:
        pf = os.path.join(d, ".parallel")
        if os.path.isfile(pf):
            st["parallel"] = read(pf).strip().lower() == "yes"
        sp = os.path.join(d, "spec.md")
        if os.path.isfile(sp):
            st["spec"] = spec_steps(sp)
        for stage in STAGES:
            rp = os.path.join(d, "reviews", STAGE_FILE[stage])
            if os.path.isfile(rp):
                rv = parse_review(rp)
                st["reviews"][stage] = {"status": rv["status"], "verdict": rv["verdict"],
                                        "open": review_findings_open(rv), "path": rp,
                                        "distilled": distilled(rv["distill"])}
    return st


def next_step(st):
    """返回 (动作, 说明). 这是 OpenSpec `status`/`instructions` 的对应物: 由状态推下一步."""
    cid = st["cr"]["id"]
    if st["status"] == "fixed":
        rv = st["reviews"]
        if rv and any(not r["distilled"] for r in rv.values()):
            return "/review-cr %s distill" % cid, "CR 已 fixed; %d 份 review 待提炼进错题本后删除" % sum(1 for r in rv.values() if not r["distilled"])
        if rv:
            return "sdd.py prune %s --dry-run" % cid, "review 都已提炼; 先看清单, 与用户确认哪些删再执行"
        return "完成", "CR 已 fixed, 工作目录已清理. 如需再改行为, 另立 CR."
    if st["status"] == "rejected":
        return "完成", "CR 已 rejected."
    rv = st["reviews"]
    # 任一 review 有未处置发现 -> 先处理
    for stage in STAGES:
        r = rv.get(stage)
        if r and r["status"] in ("to fix", "fixing"):
            if r["open"]:
                return "/implement-cr %s" % cid, "处理 %s review 的 %d 条未处置发现 (%s)" % (
                    stage, len(r["open"]), ", ".join(r["open"][:6]))
            return "/review-cr %s %s" % (cid, stage), "%s review 的发现都已处置, 待复核后置 fixed" % stage
    if "docs" not in rv:
        return "/review-cr %s docs" % cid, "CR 与 REQ delta 还没审过"
    if st["spec"] is None:
        return "/spec %s" % cid, "写实施 spec (先侦察, 每条结论带 file:line)"
    if "spec" not in rv:
        return "/review-cr %s spec" % cid, "实施 spec 还没审过"
    total, pending = st["spec"]
    if total == 0:
        return "/spec %s" % cid, "spec §4 分步表为空或格式不对 (需要 `| 步 | 内容 | 合并即生效? | 落点 |`)"
    if pending:
        return "/implement-cr %s" % cid, "实施: %d/%d 步待办 (落点填提交 hash; 回退单元一体的连续几步可共用一个提交)" % (pending, total)
    if "impl" not in rv:
        return "/review-cr %s impl" % cid, "全部步骤已落地, 实现还没审过"
    return "/implement-cr %s" % cid, "落实: 更新 REQ 正文与变更记录, CR 置 fixed, 重生成 INDEX"


def _dw(s):
    """终端显示宽度: CJK 占 2 列. 关卡名中英混排, 不算宽度对不齐."""
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


def _pad(s, n):
    return s + " " * max(0, n - _dw(s))


def _gate_review(rv, stage):
    """一个 review 关: (过没过, 证据). 证据从文件读, 不是自述."""
    r = rv.get(stage)
    if not r:
        return False, ""
    f = STAGE_FILE[stage]
    if r["status"] == "fixed":
        return True, "%s [fixed]" % f
    if r["open"]:
        return False, "%s [%s] %d 条未处置 (%s)" % (
            f, r["status"], len(r["open"]), ", ".join(r["open"][:4]))
    return False, "%s [%s] 发现已处置, 待复核" % (f, r["status"])


def checklist(st):
    """把 next_step 的状态机摊平成关卡表: [(序号, 名, 态, 证据)], 态为 done/cur/todo.

    每关的证据都是从文件里读出来的 (文件在不在, frontmatter 的 status, 表格里填没填
    提交 hash), 没有一项靠 agent 自述 -- 与 "落点填提交 hash 不填勾" 同一条约定.
    当前关 = 第一个没过的关, 所以它与 next_step 的判断必然一致.
    """
    rv = st["reviews"]
    rows = [("立项", True, "%s [%s]" % (st["cr"]["id"], st["status"]), "")]

    rows.append(("docs审",) + _gate_review(rv, "docs") + ("审 CR 与 REQ delta",))

    if st["spec"] is None:
        rows.append(("spec", False, "", "写实施 spec (先侦察, 结论带 file:line)"))
    elif st["spec"][0] == 0:
        rows.append(("spec", False, "spec.md §4 分步表为空或格式不对", ""))
    else:
        rows.append(("spec", True, "spec.md %d 步" % st["spec"][0], ""))

    rows.append(("spec审",) + _gate_review(rv, "spec") + ("审实施计划",))

    if st["spec"] is None or st["spec"][0] == 0:
        rows.append(("实施", False, "", "TDD 分步实施, 提交可跨步"))
    else:
        total, pending = st["spec"]
        rows.append(("实施", pending == 0, "%d/%d 步已提交%s" % (
            total - pending, total, ", %d 步待办" % pending if pending else ""), ""))

    rows.append(("impl审",) + _gate_review(rv, "impl") + ("审代码",))

    fixed = st["status"] == "fixed"
    # 只报 CR 自己的状态: REQ 有没有真的置 implemented 由 validate 查 (它读得到 REQ),
    # 这里说 "REQ 已置 implemented" 就成了没验证过的自述.
    rows.append(("落实", fixed, "CR [fixed]" if fixed else "", "REQ→implemented, CR→fixed"))

    undistilled = [s for s in STAGES if s in rv and not rv[s]["distilled"]]
    if not fixed:
        rows.append(("提炼", False, "", "提炼进 lessons.md, 清工作目录"))
    elif undistilled:
        rows.append(("提炼", False, "%d 份 review 待提炼进 lessons.md" % len(undistilled), ""))
    else:
        rows.append(("提炼", True, "已提炼, 工作目录可清 (prune)" if rv else "无 review 文件", ""))

    out, seen_cur = [], False
    for i, (name, ok, ev, hint) in enumerate(rows, 1):
        if ok:
            state = "done"
        elif not seen_cur:
            state, seen_cur = "cur", True
        else:
            state = "todo"
        # 有证据就报证据, 没有才说这关要干什么 -- 与它排在当前关前后无关.
        # 跳步跑出来的 CR (docs 审没过就实施完了) 全靠这条: 那几关虽然标 todo,
        # review 文件却已经在了, 用 hint 盖掉真实状态等于把跳步藏起来.
        out.append((i, name, state, ev or hint))
    return out


MARK = {"done": "✓", "cur": "→", "todo": "·"}


def fmt_checklist(st):
    """关卡表渲染成几行. rejected 的 CR 链条已中断, 调用方不该走到这里."""
    rows = checklist(st)
    done = sum(1 for _, _, s, _ in rows if s == "done")
    out = ["  进度: %d/%d" % (done, len(rows))]
    for i, name, state, ev in rows:
        # todo 项多缩进两格: 还没轮到它, 视觉上退到后面
        indent = "      " if state == "todo" else "    "
        out.append(("%s%s %d %s %s" % (indent, MARK[state], i, _pad(name, 7), ev)).rstrip())
    return out


def fmt_reviews(st):
    parts = []
    for stage in STAGES:
        r = st["reviews"].get(stage)
        if not r:
            parts.append("%s:-" % stage)
        else:
            parts.append("%s:%s%s" % (stage, r["status"], "(%d开)" % len(r["open"]) if r["open"] else ""))
    return " ".join(parts)


PROGRESS_FILE = "PROGRESS.md"


def render_cr_status(root, cr, st=None):
    """单个 CR 的状态文本. 打印的与 --write 落盘的是同一份, 不会各说一套."""
    st = st or cr_state(root, cr)
    info = parse_cr(cr["path"])
    out = ["%s %s  [%s]%s" % (cr["id"], info["title"], st["status"],
                              "  (立项 CR)" if info["kind"] == "charter" else ""),
           "  影响需求: " + (", ".join("%s(%s)" % (k, ",".join(sorted(v)) or "全文")
                                       for k, v in info["affects"].items()) or "(空!)"),
           "  工作目录: " + (st["dir"] or "(无)")]
    if st["parallel"] is not None:
        out.append("  review 策略: " + ("并行 (按车道派给 codex / pi)" if st["parallel"] else "串行 (自审)"))
    if st["status"] == "rejected":
        # 链条已中断, 摊平的关卡表会误导 (后面几关永远不会走)
        out.append("  spec: " + ("无" if st["spec"] is None else "%d 步, %d 待办" % st["spec"]))
        out.append("  reviews: " + fmt_reviews(st))
    else:
        out += fmt_checklist(st)
    act, why = next_step(st)
    out += ["  下一步: %s" % act, "    -- %s" % why]
    return "\n".join(out)


def write_progress(root, cr, st=None):
    """把进度表落进 CR 工作目录, 供人随时翻 (不必问 agent, 也不必自己跑脚本).

    生成物, 不是勾: 每次由 cr_state 重算覆写. notcommit 下不入库, prune 会清掉.
    """
    st = st or cr_state(root, cr)
    if not st["dir"]:
        return None
    path = os.path.join(st["dir"], PROGRESS_FILE)
    write(path, "# %s 进度\n\n由 `sdd.py status %s --write` 生成, 不要手工编辑 -- 每一关的状态都\n"
                "是脚本从文件读出来的 (review 的 frontmatter, spec §4 填了 hash 的步数), 手改只会骗自己.\n"
                "\n```\n%s\n```\n" % (cr["id"], cr["id"], render_cr_status(root, cr, st)))
    return path


def cmd_status(args):
    root = need_root(args)
    if args.cr:
        cr = find_cr(root, args.cr)
        if not cr:
            die("没有这个 CR: %s" % args.cr)
        st = cr_state(root, cr)
        print(render_cr_status(root, cr, st))
        if args.write:
            path = write_progress(root, cr, st)
            print("  已写: %s" % (os.path.relpath(path, root) if path else "(无工作目录, 未写)"))
        return
    reqs = list_docs(root, "REQ")
    crs = list_docs(root, "CR")
    print("REQ (%d):" % len(reqs))
    for d in reqs:
        p = parse_req(d["path"])
        print("  %s  %-14s %s" % (d["id"], "[%s]" % p["status"], p["title"]))
    print("CR (%d):" % len(crs))
    for d in crs:
        st = cr_state(root, d)
        act, _ = next_step(st)
        info = parse_cr(d["path"])
        print("  %s  %-10s %-9s %-40s reviews: %s  下一步: %s" % (
            d["id"], "[%s]" % st["status"], "(立项)" if info["kind"] == "charter" else "",
            info["title"][:40], fmt_reviews(st), act))


# ---------- validate ----------

def cmd_validate(args):
    root = need_root(args)
    errors, warns = [], []
    reqs = {d["id"]: (d, parse_req(d["path"])) for d in list_docs(root, "REQ")}
    crs = {d["id"]: (d, parse_cr(d["path"])) for d in list_docs(root, "CR")}

    def rel(p):
        return os.path.relpath(p, root)

    # 头字段与状态
    for rid, (d, p) in reqs.items():
        if p["id"] != rid:
            errors.append("%s: 头部编号 %r 与文件名不符" % (rel(d["path"]), p["id"]))
        if p["status"] not in REQ_STATUS:
            errors.append("%s: 状态 %r 不在 %s" % (rel(d["path"]), p["status"], REQ_STATUS))
        if p.get("legacy"):
            warns.append("%s: 头部还是旧的 | 字段 | 值 | 表, 应改成 frontmatter (--- 之间的 YAML)" % rel(d["path"]))
        if not p["summary"]:
            warns.append("%s: 头部缺 summary (INDEX 需要)" % rel(d["path"]))
        elif "一句话" in p["summary"]:
            warns.append("%s: summary 还是模板占位文字" % rel(d["path"]))
        # 每条 FR 至少一条 AC
        covered = set()
        for ac, src in p["acs"].items():
            covered |= src
            for s in src:
                if s.startswith("FR-") and s not in p["frs"]:
                    errors.append("%s: %s 引用了不存在的 %s" % (rel(d["path"]), ac, s))
                if s.startswith("BR-") and s not in p["brs"]:
                    errors.append("%s: %s 引用了不存在的 %s" % (rel(d["path"]), ac, s))
        for fr in sorted(p["frs"], key=lambda x: int(x.split("-")[1])):
            if fr not in covered and "已删除" not in p["text"].split("**%s**" % fr, 1)[-1][:80]:
                warns.append("%s: %s 没有任何 AC 标注它为来源" % (rel(d["path"]), fr))
        body = p["text"].split("## 变更记录", 1)[0]  # 变更记录里叙述 "移除了标注" 不算活标注
        if p["status"] == "implemented" and re.search(r"\(未实现[,，]\s*见 CR-\d+\)", body):
            errors.append("%s: implemented 但正文仍有 '(未实现, 见 CR-x)' 标注" % rel(d["path"]))
        if p["status"] == "implemented":
            oq = re.search(r"^## 10\. 开放问题\s*\n(.*?)(?=^## |\Z)", p["text"], re.M | re.S)
            if oq and re.search(r"^\s*[-*]\s+\S", oq.group(1), re.M):
                warns.append("%s: implemented 但第 10 节开放问题非空" % rel(d["path"]))

    for cid, (d, p) in crs.items():
        if p["id"] != cid:
            errors.append("%s: 头部编号 %r 与文件名不符" % (rel(d["path"]), p["id"]))
        if p["status"] not in CR_STATUS:
            errors.append("%s: 状态 %r 不在 %s" % (rel(d["path"]), p["status"], CR_STATUS))
        if p.get("legacy"):
            warns.append("%s: 头部还是旧的 | 字段 | 值 | 表, 应改成 frontmatter (--- 之间的 YAML)" % rel(d["path"]))
        if not p["summary"]:
            warns.append("%s: 头部缺 summary" % rel(d["path"]))
        elif "一句话" in p["summary"]:
            warns.append("%s: summary 还是模板占位文字" % rel(d["path"]))
        if p.get("kind") not in ("change", "charter"):
            warns.append("%s: kind 应是 change (变更) 或 charter (立项), 得到 %r" % (rel(d["path"]), p.get("kind")))
        if not p["affects"]:
            errors.append("%s: affects 为空 -- CR 必须挂在具体 REQ 上" % rel(d["path"]))
        for rid, items in p["affects"].items():
            if rid not in reqs:
                errors.append("%s: 影响需求引用了不存在的 %s" % (rel(d["path"]), rid))
                continue
            rq = reqs[rid][1]
            for it in items:
                pool = rq["frs"] if it.startswith("FR-") else rq["brs"] if it.startswith("BR-") else set(rq["acs"])
                if it not in pool and p["status"] != "fixed":
                    # 未落实前, 新增条目还不在 REQ 里, 只提示
                    if not re.search(r"%s\s*\(新增" % re.escape(it), p["text"]):
                        warns.append("%s: 引用 %s %s, REQ 里没有 (若是新增条目, 变更内容表里标 '(新增')" % (rel(d["path"]), rid, it))
                elif it not in pool and p["status"] == "fixed":
                    errors.append("%s: 已 fixed 但 %s %s 在 REQ 里不存在" % (rel(d["path"]), rid, it))
            if p["status"] == "fixed":
                if cid not in rq["log"]:
                    errors.append("%s: 已 fixed 但 %s 变更记录没有指回本 CR 的行" % (rel(d["path"]), rid))
                if rq["status"] not in ("implemented", "superseded", "retired"):
                    errors.append("%s: 已 fixed 但 %s 状态是 %s" % (rel(d["path"]), rid, rq["status"]))
        # reviews
        st = cr_state(root, d)
        for stage, r in st["reviews"].items():
            if parse_review(r["path"]).get("legacy"):
                warns.append("%s: 头部还是旧的 | 字段 | 值 | 表, 应改成 frontmatter" % rel(r["path"]))
            if r["status"] not in REVIEW_STATUS:
                errors.append("%s: 状态 %r 不在 %s" % (rel(r["path"]), r["status"], REVIEW_STATUS))
            if r["status"] == "fixed" and r["open"]:
                errors.append("%s: 状态 fixed 但仍有未处置发现: %s" % (rel(r["path"]), ", ".join(r["open"])))
            if r["verdict"] and r["verdict"].upper().startswith("BLOCK") and r["status"] == "fixed":
                warns.append("%s: 结论仍是 BLOCK 但状态 fixed -- 复审后请把结论改掉" % rel(r["path"]))
        known = lesson_ids_in_file(root)
        for stage, r in st["reviews"].items():
            rv = parse_review(r["path"])
            for lid in lesson_ids(rv["distill"]):
                if lid not in known:
                    errors.append("%s: 提炼引用了 lessons.md 里不存在的 %s" % (rel(r["path"]), lid))
        if p["status"] == "fixed" and st["reviews"] and any(not r["distilled"] for r in st["reviews"].values()):
            warns.append("%s: 已 fixed, review 待提炼后删除 (/review-cr %s distill)" % (rel(d["path"]), cid))
        if p["status"] == "fixed":
            for stage in STAGES:
                if stage not in st["reviews"]:
                    warns.append("%s: 已 fixed 但本机没有 %s review (notcommit 不入库, 换机器会看不到)" % (rel(d["path"]), stage))
                elif st["reviews"][stage]["status"] != "fixed":
                    errors.append("%s: 已 fixed 但 %s review 状态是 %s" % (rel(d["path"]), stage, st["reviews"][stage]["status"]))

    # 相对链接可解析
    for kind in ("REQ", "CR"):
        for d in list_docs(root, kind):
            t = read(d["path"])
            for m in re.finditer(r"\]\(([^)#\s]+\.md)(?:#[^)]*)?\)", t):
                target = os.path.normpath(os.path.join(os.path.dirname(d["path"]), m.group(1)))
                if not os.path.exists(target):
                    (warns if "notcommit" in m.group(1) else errors).append(
                        "%s: 链接不可解析: %s" % (rel(d["path"]), m.group(1)))

    # INDEX 是否过期
    idx = os.path.join(root, "INDEX.md")
    if os.path.exists(idx) and read(idx) != render_index(root):
        warns.append("INDEX.md 与实际不一致, 运行 `sdd.py index` 重生成")

    for kind in ("REQ", "CR"):
        for d in list_docs(root, kind):
            warns.extend(fm_lint(read(d["path"]), rel(d["path"])))
    for cid in [d["id"] for d in list_docs(root, "CR")]:
        cd = cr_dir(root, cid)
        if not cd:
            continue
        for sub in ("spec.md", "reviews/01-docs.md", "reviews/02-spec.md", "reviews/03-impl.md"):
            fp = os.path.join(cd, sub)
            if os.path.isfile(fp):
                warns.extend(fm_lint(read(fp), rel(fp)))
    for w in warns:
        print("警告:", w)
    for e in errors:
        print("错误:", e)
    print("检查完成: %d 错误, %d 警告" % (len(errors), len(warns)))
    sys.exit(1 if errors else 0)


# ---------- index ----------

def render_index(root):
    lines = ["# 索引", "",
             "由 `sdd.py index` 生成, 不要手工编辑. 约定见 sdd skill 的 `references/conventions.md` (项目里不放副本).", "",
             "## 需求 (REQ)", "", "| 编号 | 标题 | 状态 | 摘要 |", "|---|---|---|---|"]
    for d in list_docs(root, "REQ"):
        p = parse_req(d["path"])
        lines.append("| [%s](req/%s) | %s | %s | %s |" % (d["id"], d["file"], p["title"], p["status"], p["summary"]))
    lines += ["", "## 变更 (CR)", "", "| 编号 | 标题 | 影响需求 | 状态 | reviews (本机) | 摘要 |", "|---|---|---|---|---|---|"]
    for d in list_docs(root, "CR"):
        p = parse_cr(d["path"])
        st = cr_state(root, d)
        lines.append("| [%s](cr/%s) | %s | %s | %s | %s | %s |" % (
            d["id"], d["file"], p["title"],
            ", ".join(p["affects"]) or "-", p["status"], fmt_reviews(st), p["summary"]))
    return "\n".join(lines) + "\n"


def write_index(root):
    path = os.path.join(root, "INDEX.md")
    write(path, render_index(root))
    print("INDEX 已更新:", path)


def cmd_index(args):
    write_index(need_root(args))


# ---------- lessons / prune ----------

def cmd_lessons(args):
    root = need_root(args)
    p = lessons_path(root)
    if args.init:
        if os.path.exists(p):
            print("已存在:", p)
        else:
            write(p, fill("lessons.md", {"DATE": today()}))
            print("已建:", p)
        return
    ids = sorted(lesson_ids_in_file(root), key=lambda x: int(x.split("-")[1]))
    if args.next_id:
        print("L-%d" % ((int(ids[-1].split("-")[1]) + 1) if ids else 1))
        return
    if not os.path.isfile(p):
        print("没有错题本 (%s). 建一个: sdd.py lessons --init" % p)
        return
    print("错题本: %s, %d 条" % (p, len(ids)))
    for line in read(p).splitlines():
        if LESSON_ROW_RE.match(line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            # 编号 | 车道 | 模式 | 识别信号 | 规则 | 来源 | 次数
            print("  %-5s %-8s x%-2s %s" % (cells[0], cells[1][:8], cells[6] if len(cells) > 6 else "?", cells[2][:70]))


def cmd_prune(args):
    root = need_root(args)
    cr = find_cr(root, args.cr)
    if not cr:
        die("没有这个 CR: %s" % args.cr)
    st = cr_state(root, cr)
    if st["status"] != "fixed":
        die("%s 状态是 %s, 只有 fixed 的 CR 才能删工作目录" % (cr["id"], st["status"]))
    d = st["dir"]
    if not d or not os.path.isdir(d):
        die("%s 没有工作目录, 无可删" % cr["id"])
    rdir = os.path.join(d, "reviews")
    problems = []
    if not os.path.isdir(rdir):
        # 没有 reviews/: 上次 --keep 留下东西后的二次清理, 或这个 CR 跳过了 review.
        # CR 已 fixed 本身蕴含三次 review 走完 (见 conventions "状态"), 这里只提示不拦.
        print("提示: %s 已无 reviews/ (清理过, 或跳过了 review), 只清理剩下的文件" % cr["id"])
    for stage, r in st["reviews"].items():
        if r["status"] != "fixed":
            problems.append("%s review 状态 %s" % (stage, r["status"]))
        if not r["distilled"]:
            problems.append("%s review 头部 '提炼' 未填 (已提炼 (L-x) / 无可提炼: 理由)" % stage)
    known = lesson_ids_in_file(root)
    for stage, r in st["reviews"].items():
        for lid in lesson_ids(parse_review(r["path"])["distill"]):
            if lid not in known:
                problems.append("%s review 引用的 %s 不在 lessons.md" % (stage, lid))
    if os.path.isdir(rdir) and not st["reviews"]:
        problems.append("reviews/ 里没有 0N-<stage>.md (只有原件?), 请先按规范提炼")
    if problems:
        die("不能删:\n  - " + "\n  - ".join(problems))
    # 默认三样全删; --keep 逐项保留 (删除不可逆, notcommit 不入库, git 恢复不了).
    keep = set(args.keep or ())
    targets = []
    if "draft" not in keep and os.path.isdir(os.path.join(d, "draft")):
        targets.append((os.path.join(d, "draft"), True))
    if "spec" not in keep and os.path.isfile(os.path.join(d, "spec.md")):
        targets.append((os.path.join(d, "spec.md"), False))
    if "reviews" not in keep and os.path.isdir(rdir):
        targets.append((rdir, True))
    pf = os.path.join(d, ".parallel")
    if os.path.isfile(pf):
        targets.append((pf, False))  # review 策略, CR 清理了就是孤儿
    gp = os.path.join(d, PROGRESS_FILE)
    if os.path.isfile(gp):
        targets.append((gp, False))  # 进度表是生成物, 随时可再生
    if not targets:
        die("没有可删的 (--keep 留下了全部, 或工作目录已空)")
    files = []
    for path, isdir in targets:
        files += ([os.path.join(dp, f) for dp, _, fs in os.walk(path) for f in fs]
                  if isdir else [path])
    print("%s: 将删除 %d 个文件%s (%s)" % (
        cr["id"], len(files), " (保留 %s)" % ", ".join(sorted(keep)) if keep else "",
        "dry-run" if args.dry_run else "执行"))
    for f in sorted(files):
        print("  ", os.path.relpath(f, root))
    if args.dry_run:
        return
    for path, isdir in targets:
        shutil.rmtree(path) if isdir else os.remove(path)
    if not os.listdir(d):
        os.rmdir(d)
        print("已删除", os.path.relpath(d, root),
              "; 教训在 lessons.md (来源列可反查本 CR), 结论在 CR 与 REQ")
    else:
        print("已删除 %d 个文件; %s 仍保留在 %s" % (
            len(files), ", ".join(sorted(keep)), os.path.relpath(d, root)))
    write_index(root)


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", help="docs/sdd 目录 (默认向上查找; 或环境变量 SDD_ROOT)")
    # --root 也允许写在子命令后面 (sdd.py init --root X); SUPPRESS 使其不覆盖顶层已解析的值
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    sub = ap.add_subparsers(dest="cmd", required=True)
    _add = sub.add_parser
    sub.add_parser = lambda name, **kw: _add(name, parents=[common], **kw)
    sub.add_parser("init").set_defaults(fn=cmd_init)
    s = sub.add_parser("status"); s.add_argument("cr", nargs="?")
    s.add_argument("--write", action="store_true",
                   help="把这个 CR 的进度表写进工作目录的 PROGRESS.md (人随时翻, 不必问 agent)")
    s.set_defaults(fn=cmd_status)
    s = sub.add_parser("next-id"); s.add_argument("kind", choices=("REQ", "CR")); s.set_defaults(fn=cmd_next_id)
    s = sub.add_parser("new-req"); s.add_argument("slug"); s.add_argument("title", nargs="?"); s.set_defaults(fn=cmd_new_req)
    s = sub.add_parser("new-cr"); s.add_argument("slug"); s.add_argument("title", nargs="?")
    s.add_argument("--new", action="store_true", help="新增业务的立项 CR (默认是变更 CR)"); s.set_defaults(fn=cmd_new_cr)
    s = sub.add_parser("new-draft"); s.add_argument("key", help="slug 或 CR-NNN"); s.add_argument("topic"); s.set_defaults(fn=cmd_new_draft)
    s = sub.add_parser("new-spec"); s.add_argument("cr"); s.add_argument("--force", action="store_true"); s.set_defaults(fn=cmd_new_spec)
    s = sub.add_parser("new-review"); s.add_argument("cr"); s.add_argument("stage", choices=STAGES)
    s.add_argument("--reviewer"); s.add_argument("--force", action="store_true"); s.set_defaults(fn=cmd_new_review)
    sub.add_parser("validate").set_defaults(fn=cmd_validate)
    sub.add_parser("index").set_defaults(fn=cmd_index)
    s = sub.add_parser("lessons"); s.add_argument("--init", action="store_true"); s.add_argument("--next-id", action="store_true"); s.set_defaults(fn=cmd_lessons)
    for _n in ("prune", "prune-reviews"):   # prune-reviews: 旧名, 保留
        s = sub.add_parser(_n); s.add_argument("cr"); s.add_argument("--dry-run", action="store_true")
        s.add_argument("--keep", action="append", choices=("draft", "spec", "reviews"),
                       help="保留某一项, 可给多次 (如 --keep spec)")
        s.set_defaults(fn=cmd_prune)
    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
