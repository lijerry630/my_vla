#!/usr/bin/env python3
"""VLA 学习日志 · 静态站点构建

用法：
  python3 tools/build.py             # 构建全站
  python3 tools/build.py new 标题    # 新建一篇笔记草稿（content/ 下）

约定：
  content/*.md            笔记与页面源文件，开头是 YAML 风格的 front matter
  content/page-*.md       独立页面（type: page），输出到站点根目录
  theme/*.html            页面骨架模板，$NAME 为占位符
  assets/                 样式、脚本、图片（图片放 assets/img/）
输出：
  notes/<slug>.html  notes.html  index.html  about.html  resources.html
"""
import html as H
import json
import os
import re
import sys
import unicodedata
from datetime import date, datetime
from string import Template

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
THEME = os.path.join(ROOT, "theme")

with open(os.path.join(ROOT, "site.json"), encoding="utf-8") as f:
    SITE = json.load(f)

LINK_PREFIX = ""  # 笔记页里相对资源路径要加 ../


# ---------------------------------------------------------------- 基础工具
def esc(t):
    return H.escape(str(t), quote=True)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def theme(name):
    return read(os.path.join(THEME, name))


def write(rel_path, text):
    p = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    return rel_path


def render(name, mapping):
    return Template(theme(name)).substitute(mapping)


# ---------------------------------------------------------------- front matter
def parse_front_matter(text):
    meta = {}
    body = text
    if text.startswith("---"):
        end = re.search(r"\n---\s*\n", text)
        if end:
            block = text[3:end.start()]
            body = text[end.end():]
            for line in block.split("\n"):
                if not line.strip() or line.lstrip().startswith("#"):
                    continue
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"').strip("'")
    return meta, body


def parse_tags(v):
    if not v:
        return []
    return [t.strip() for t in re.split(r"[,，、;；]", v) if t.strip()]


# ---------------------------------------------------------------- Markdown
INLINE_CODE = re.compile(r"`([^`\n]+)`")
INLINE_MATH = re.compile(r"(?<!\\)\$([^$\n]+?)\$")
IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
AUTOLINK_RE = re.compile(r"&lt;(https?://[^\s&]+)&gt;")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
STRIKE_RE = re.compile(r"~~(.+?)~~")
EM_RE = re.compile(r"(?<!\*)\*([^\s*][^*\n]*?)\*(?!\*)")


def fix_url(u):
    if re.match(r"(https?:|mailto:|ftp:|#|/|data:)", u):
        return u
    if LINK_PREFIX and not u.startswith("../"):
        return LINK_PREFIX + u
    return u


def inline(raw, protect=None):
    """行内语法：代码 → 行内公式 → 转义 → 链接/图片/强调"""
    prot = [] if protect is None else protect

    def keep(s):
        prot.append(s)
        return "\ue000%d\ue002" % (len(prot) - 1)

    text = INLINE_CODE.sub(lambda m: keep("<code>" + esc(m.group(1)) + "</code>"), raw)
    text = INLINE_MATH.sub(lambda m: keep("$" + m.group(1) + "$"), text)
    text = esc(text)

    def img(m):
        return '<img src="%s" alt="%s" loading="lazy">' % (fix_url(m.group(2)), m.group(1))

    text = IMG_RE.sub(img, text)
    text = LINK_RE.sub(
        lambda m: '<a href="%s">%s</a>' % (fix_url(m.group(2)), m.group(1)), text
    )
    text = AUTOLINK_RE.sub(lambda m: '<a href="%s">%s</a>' % (m.group(1), m.group(1)), text)
    text = BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = STRIKE_RE.sub(r"<del>\1</del>", text)
    text = EM_RE.sub(r"<em>\1</em>", text)

    for i, s in enumerate(prot):
        text = text.replace("\ue000%d\ue002" % i, s)
    return text


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", s)


def text_len(s):
    return len(re.sub(r"\s+", "", strip_tags(s)))


HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")
LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
TABLE_SEP_RE = re.compile(r"^\|[\s:\-\|]+$")


def render_list(items, prot):
    if not items:
        return ""

    root = {"ind": -1, "children": []}
    stack = [root]
    for ind, marker, text in items:
        node = {"ind": ind, "marker": marker, "text": text, "children": []}
        while len(stack) > 1 and stack[-1]["ind"] >= ind:
            stack.pop()
        stack[-1]["children"].append(node)
        stack.append(node)

    def render_nodes(nodes):
        if not nodes:
            return ""
        tag = "ol" if nodes[0]["marker"][0].isdigit() else "ul"
        parts = ["<%s>" % tag]
        for n in nodes:
            parts.append("<li>" + inline(n["text"], prot) + render_nodes(n["children"]) + "</li>")
        parts.append("</%s>" % tag)
        return "".join(parts)

    return render_nodes(root["children"])


def cell_width(s):
    plain = strip_tags(inline(s, None))
    w = 0
    for ch in plain:
        w += 2 if "\u4e00" <= ch <= "\u9fff" else 1
    return w


def build_table(header, aligns, rows):
    n = len(header)
    lens = []
    for i in range(n):
        longest = cell_width(header[i]) if i < len(header) else 0
        for r in rows:
            if i < len(r):
                longest = max(longest, cell_width(r[i]))
        lens.append(min(max(longest, 6), 34))
    total = float(sum(lens)) or 1.0
    widths = [round(100.0 * l / total, 2) for l in lens]
    widths[-1] = round(100.0 - sum(widths[:-1]), 2)
    cols = ['<col style="width:%s%%">' % w for w in widths]
    out = ['<div class="table-scroll"><table><colgroup>%s</colgroup><thead><tr>' % "".join(cols)]
    for i, cell in enumerate(header):
        al = aligns[i] if i < len(aligns) else "left"
        out.append('<th style="text-align:%s">%s</th>' % (al, inline(cell, None)))
    out.append("</tr></thead><tbody>")
    for r in rows:
        out.append("<tr>")
        for i in range(n):
            cell = r[i] if i < len(r) else ""
            al = aligns[i] if i < len(aligns) else "left"
            out.append('<td style="text-align:%s">%s</td>' % (al, inline(cell, None)))
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def markdown(md):
    lines = md.replace("\r\n", "\n").split("\n")
    out = []
    toc = []
    para = []
    sec_no = [0]
    i = 0

    def flush():
        if para:
            out.append("<p>" + inline(" ".join(para).strip(), None) + "</p>")
            del para[:]

    def heading_id():
        sec_no[0] += 1
        return "sec-%02d" % sec_no[0]

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 代码块
        if stripped.startswith("```"):
            flush()
            info = stripped[3:].strip()
            i += 1
            buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            code = "\n".join(buf)
            label = esc(info) if info else "text"
            out.append(
                '<figure class="code"><div class="code-bar"><span>%s</span>'
                '<button class="copy" type="button" data-copy>复制</button></div>'
                "<pre><code>%s</code></pre></figure>" % (label, esc(code))
            )
            continue

        # 块级公式
        if stripped.startswith("$$"):
            flush()
            chunk = [stripped]
            if not (len(stripped) > 4 and stripped.endswith("$$")):
                i += 1
                while i < len(lines) and not lines[i].strip().endswith("$$"):
                    chunk.append(lines[i])
                    i += 1
                if i < len(lines):
                    chunk.append(lines[i])
                    i += 1
            else:
                i += 1
            out.append('<div class="math-block">' + "\n".join(chunk) + "</div>")
            continue

        # 标题
        m = HEAD_RE.match(line)
        if m:
            flush()
            level = len(m.group(1))
            text = m.group(2).strip()
            hid = heading_id()
            out.append(
                '<h%d id="%s">%s</h%d>' % (level, hid, inline(text, None), level)
            )
            if level in (2, 3):
                toc.append((level, hid, strip_tags(inline(text, None))))
            i += 1
            continue

        # 分隔线
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", stripped):
            flush()
            out.append("<hr>")
            i += 1
            continue

        # 表格
        if stripped.startswith("|") and i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if TABLE_SEP_RE.match(nxt) and "|" in nxt:
                flush()
                header = split_row(line)
                aligns = []
                for c in split_row(nxt):
                    if c.startswith(":") and c.endswith(":"):
                        aligns.append("center")
                    elif c.endswith(":"):
                        aligns.append("right")
                    else:
                        aligns.append("left")
                i += 2
                rows = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    rows.append(split_row(lines[i]))
                    i += 1
                out.append(build_table(header, aligns, rows))
                continue

        # 列表
        m = LIST_RE.match(line)
        if m:
            flush()
            items = []
            while i < len(lines):
                mm = LIST_RE.match(lines[i])
                if not mm:
                    if lines[i].strip() == "":
                        # 空行后仍是列表项则继续
                        if i + 1 < len(lines) and LIST_RE.match(lines[i + 1]):
                            i += 1
                            continue
                    break
                items.append((len(mm.group(1)), mm.group(2), mm.group(3)))
                i += 1
            out.append(render_list(items, None))
            continue

        # 引用
        if line.startswith("> "):
            flush()
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip())
                i += 1
            out.append("<blockquote><p>" + inline(" ".join(buf), None) + "</p></blockquote>")
            continue

        # 空行
        if stripped == "":
            flush()
            i += 1
            continue

        para.append(stripped)
        i += 1

    flush()
    return "\n".join(out), toc


# ---------------------------------------------------------------- 数据装载
def load_items():
    notes, pages = [], []
    for fn in sorted(os.listdir(CONTENT)):
        if not fn.endswith(".md"):
            continue
        meta, body = parse_front_matter(read(os.path.join(CONTENT, fn)))
        item = {
            "file": fn,
            "title": meta.get("title") or fn[:-3],
            "date": meta.get("date") or "",
            "tags": parse_tags(meta.get("tags")),
            "summary": meta.get("summary") or "",
            "order": int(meta.get("order") or 0),
            "type": meta.get("type") or ("page" if fn.startswith("page-") else "note"),
            "body": body,
        }
        slug = meta.get("slug") or fn[:-3]
        slug = re.sub(r"^[0-9]+-", "", slug)
        slug = unicodedata.normalize("NFKD", slug)
        slug = re.sub(r"[^0-9a-zA-Z\-]+", "-", slug).strip("-").lower()
        if not slug:
            slug = "note-" + (item["date"] or date.today().isoformat())
        item["slug"] = slug
        (pages if item["type"] == "page" else notes).append(item)

    def key(x):
        return (x["order"] or 99, x["date"] or "", x["slug"])

    notes.sort(key=key)
    for idx, n in enumerate(notes, start=1):
        n["num"] = "%02d" % idx
    pages.sort(key=lambda x: x["slug"])
    return notes, pages


def reading_minutes(html_body):
    chars = text_len(html_body)
    minutes = max(1, round(chars / 380)) if chars else 1
    return minutes


def tag_list(notes):
    tags, counter = [], {}
    for n in notes:
        for t in n["tags"]:
            if t not in counter:
                counter[t] = 0
                tags.append(t)
            counter[t] += 1
    return tags, counter


# ---------------------------------------------------------------- 页面拼装
def head_html(title, desc, active, root, extra=""):
    out = render(
        "head.html",
        {"TITLE": esc(title), "DESC": esc(desc), "ROOT": root, "EXTRA": extra},
    )
    return out.replace('data-nav="%s"' % active, 'data-nav="%s" data-current' % active)


def foot_html(root):
    repo_url = SITE.get("repo_url") or "https://github.com"
    return render("foot.html", {"ROOT": root, "REPO_URL": esc(repo_url)})


def note_meta_line(n):
    bits = ["LOG " + n["num"]]
    if n["date"]:
        bits.append(n["date"])
    bits.append("%d min" % n["minutes"])
    return "".join("<span>%s</span>" % esc(b) for b in bits)


def build_note(n, prev, nxt, site_url=""):
    global LINK_PREFIX
    LINK_PREFIX = "../"
    body_html, toc = markdown(n["body"])
    n["minutes"] = reading_minutes(body_html)
    LINK_PREFIX = ""

    toc_html = ""
    if toc:
        items = []
        for level, hid, text in toc:
            items.append(
                '<li data-level="%d"><a href="#%s" data-toc-link>%s</a></li>'
                % (level, hid, esc(text))
            )
        toc_html = (
            '<aside class="toc"><h2>本页目录</h2><ol>%s</ol></aside>' % "".join(items)
        )

    tags_html = ""
    if n["tags"]:
        tags_html = '<span>%s</span>' % " · ".join(esc(t) for t in n["tags"])

    nav = []
    if prev:
        nav.append(
            '<a href="%s.html"><span class="dir">上一篇</span><span class="ttl">%s</span></a>'
            % (prev["slug"], esc(prev["title"]))
        )
    if nxt:
        nav.append(
            '<a href="%s.html" data-next><span class="dir">下一篇</span><span class="ttl">%s</span></a>'
            % (nxt["slug"], esc(nxt["title"]))
        )
    nav_html = ('<div class="note-foot">%s</div>' % "".join(nav)) if nav else ""

    summary_html = (
        '<p class="note-summary">%s</p>' % inline(n["summary"], None) if n["summary"] else ""
    )

    page = (
        '<section class="wrap"><div class="sheet">'
        '<div class="note-head">'
        '<div class="crumbs"><a href="../index.html">首页</a><span>/</span>'
        '<a href="../notes.html">笔记</a><span>/</span>LOG %s</div>'
        '<div class="note-meta">%s%s</div>'
        "<h1>%s</h1>%s</div>"
        '<div class="note-layout"><article class="prose">%s%s</article>%s</div>'
        "</div></section>"
    ) % (
        n["num"],
        note_meta_line(n),
        tags_html,
        inline(n["title"], None),
        summary_html,
        body_html,
        nav_html,
        toc_html,
    )

    extra = (
        '<link rel="stylesheet" href="https://fastly.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">'
        '<script defer src="https://fastly.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>'
        '<script defer src="https://fastly.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js" '
        'onload="renderMathInElement(document.body,{delimiters:[{left:\'$$\',right:\'$$\',display:true},'
        "{left:'$',right:'$',display:false}],ignoredTags:['pre','code','script','style','textarea'],"
        'throwOnError:false})"></script>'
    )

    html = (
        head_html(
            "%s · %s" % (n["title"], SITE["title"]),
            n["summary"] or SITE["description"],
            "notes",
            "../",
            extra,
        )
        + page
        + foot_html("../")
    )
    write("notes/%s.html" % n["slug"], html)


def log_row(n, root="notes/"):
    tags = " ".join(n["tags"])
    side_tag = '<span class="tag">%s</span>' % esc(n["tags"][0]) if n["tags"] else ""
    return (
        '<li class="log-row" data-tags="%s">'
        '<span class="idx">LOG %s</span>'
        '<div class="body"><h3><a href="%s%s.html">%s</a></h3><p>%s</p></div>'
        '<div class="side">%s%s%s</div>'
        "</li>"
    ) % (
        esc(tags),
        n["num"],
        root,
        n["slug"],
        inline(n["title"], None),
        inline(n["summary"], None),
        side_tag,
        "<br>" if side_tag and n["date"] else "",
        esc(n["date"]),
    )


def route_row(n):
    return (
        '<li class="route-item"><span class="num" data-done>%s</span>'
        '<div><h3><a href="notes/%s.html">%s</a></h3><p>%s</p></div>'
        '<span class="state">%d min</span></li>'
    ) % (n["num"], n["slug"], inline(n["title"], None), inline(n["summary"], None), n["minutes"])


def build_index(notes):
    latest = list(reversed(notes))[:3]
    count = len(notes)
    updated = max((n["date"] for n in notes), default=date.today().isoformat())
    page = render(
        "index.html",
        {
            "COUNT": str(count),
            "UPDATED": esc(updated),
            "ROUTE": "\n".join(route_row(n) for n in notes),
            "LATEST": "\n".join(log_row(n, "notes/") for n in latest),
        },
    )
    html = (
        head_html(
            "%s · 记录 VLA 的系统学习" % SITE["title"], SITE["description"], "home", "", ""
        )
        + page
        + foot_html("")
    )
    write("index.html", html)


def build_archive(notes):
    tags, counter = tag_list(notes)
    chips = ['<button class="chip-btn" data-filter="*" aria-pressed="true">全部</button>']
    for t in tags:
        chips.append(
            '<button class="chip-btn" data-filter="%s" aria-pressed="false">%s</button>'
            % (esc(t), esc(t))
        )
    page = render(
        "archive.html",
        {
            "COUNT": str(len(notes)),
            "TAGS": "\n      ".join(chips),
            "LIST": "\n".join(log_row(n, "notes/") for n in notes),
        },
    )
    html = (
        head_html(
            "全部笔记 · %s" % SITE["title"], SITE["description"], "notes", "", ""
        )
        + page
        + foot_html("")
    )
    write("notes.html", html)


def build_page(p):
    global LINK_PREFIX
    LINK_PREFIX = ""
    body_html, _ = markdown(p["body"])
    summary_html = (
        '<p class="note-summary">%s</p>' % inline(p["summary"], None) if p["summary"] else ""
    )
    meta = p["date"] if p.get("date") else ""
    page = (
        '<section class="wrap"><div class="sheet pad-sheet">'
        '<div class="page-head"><div class="meta">%s</div><h1>%s</h1>%s</div>'
        '<div class="prose prose-wide">%s</div></div></section>'
    ) % (esc(meta), inline(p["title"], None), summary_html, body_html)
    html = (
        head_html(
            "%s · %s" % (p["title"], SITE["title"]),
            p["summary"] or SITE["description"],
            p["slug"] if p["slug"] in ("about", "resources") else "",
            "",
            "",
        )
        + page
        + foot_html("")
    )
    write("%s.html" % p["slug"], html)


def build():
    notes, pages = load_items()

    # 先算阅读时长（索引页要用）
    for n in notes:
        _, _ = None, None
        probe = "".join([n["body"]])
        n["minutes"] = max(1, round(text_len(probe) / 380)) if probe else 1

    for idx, n in enumerate(notes):
        prev = notes[idx - 1] if idx > 0 else None
        nxt = notes[idx + 1] if idx + 1 < len(notes) else None
        build_note(n, prev, nxt)

    build_index(notes)
    build_archive(notes)
    for p in pages:
        build_page(p)

    # 清理已删除笔记的旧产物
    keep = {n["slug"] + ".html" for n in notes}
    notes_dir = os.path.join(ROOT, "notes")
    for fn in os.listdir(notes_dir):
        if fn.endswith(".html") and fn not in keep:
            os.remove(os.path.join(notes_dir, fn))

    print(
        "构建完成：%d 篇笔记，%d 个独立页面 -> index.html / notes.html / notes/*.html"
        % (len(notes), len(pages))
    )


def new_note(title):
    today = date.today().isoformat()
    slug = re.sub(r"[^0-9a-zA-Z\-]+", "-", title.lower()).strip("-") or "note"
    n = len([f for f in os.listdir(CONTENT) if f.endswith(".md")]) + 1
    fn = "%03d-%s.md" % (n, slug)
    tpl = """---
title: %s
date: %s
tags: 待补充
summary: 一句话说清这篇要回答什么问题
order: %d
---

## 这篇要解决的问题


## 关键结论


## 展开

""" % (title, today, n)
    path = os.path.join(CONTENT, fn)
    if os.path.exists(path):
        print("已存在：content/%s" % fn)
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write(tpl)
    print("已创建 content/%s，写完后运行：python3 tools/build.py" % fn)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "new":
        new_note(" ".join(sys.argv[2:]) or "未命名笔记")
    else:
        build()
