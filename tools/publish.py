#!/usr/bin/env python3
"""VLA 学习日志 · 本地写作与发布

常用：
  python3 tools/publish.py serve                  # 本地预览 http://localhost:8000
  python3 tools/publish.py new "新笔记标题"        # 新建草稿
  python3 tools/publish.py up 笔记本.md            # 导入本地 md -> 构建 -> 提交 -> 推送
  python3 tools/publish.py up                     # 只构建 + 提交 + 推送已有改动
  python3 tools/publish.py build / status         # 只构建 / 只看状态

推送认证：
  export GITHUB_TOKEN=<你的 Personal Access Token>（需要 repo 权限）
  未设置时回退到系统已配置的 git 凭据。
仓库信息读 site.json 的 owner / repo / branch；owner 为空时回退到 origin 远程地址。
"""
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
ASSETS_IMG = os.path.join(ROOT, "assets", "img")


def sh(cmd, check=True, capture=True):
    res = subprocess.run(
        cmd,
        cwd=ROOT,
        shell=isinstance(cmd, str),
        capture_output=capture,
        text=True,
    )
    if check and res.returncode != 0:
        print((res.stderr or res.stdout or "").strip())
        sys.exit(1)
    return res


def load_site():
    with open(os.path.join(ROOT, "site.json"), encoding="utf-8") as f:
        return json.load(f)


def build():
    sh([sys.executable, os.path.join(ROOT, "tools", "build.py")], capture=False)


# ---------------------------------------------------------------- 导入本地内容
def slug_of(path):
    name = os.path.splitext(os.path.basename(path))[0]
    name = re.sub(r"^[0-9]+-", "", name)
    s = re.sub(r"[^0-9a-zA-Z\-]+", "-", name).strip("-").lower()
    return s


def unique_name(slug):
    n = len([f for f in os.listdir(CONTENT) if f.endswith(".md")]) + 1
    while True:
        cand = "%03d-%s.md" % (n, slug)
        if not os.path.exists(os.path.join(CONTENT, cand)):
            return cand
        n += 1


def add(paths):
    added = []
    for p in paths:
        if not os.path.exists(p):
            print("跳过（找不到）：%s" % p)
            continue
        ext = os.path.splitext(p)[1].lower()
        if ext == ".md":
            slug = slug_of(p) or ("note-" + date.today().isoformat())
            target = unique_name(slug)
            shutil.copyfile(p, os.path.join(CONTENT, target))
            added.append("content/" + target)
        elif ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"):
            os.makedirs(ASSETS_IMG, exist_ok=True)
            shutil.copyfile(p, os.path.join(ASSETS_IMG, os.path.basename(p)))
            added.append("assets/img/" + os.path.basename(p))
        else:
            print("只支持 .md 与图片，已跳过：%s" % p)
    for a in added:
        print("已导入 %s" % a)
    if any(a.startswith("assets/img/") for a in added):
        print("提醒：在 md 里引用图片写成 ![说明](assets/img/文件名)")
    return added


# ---------------------------------------------------------------- git
def ensure_git():
    if not os.path.isdir(os.path.join(ROOT, ".git")):
        sh(["git", "init", "-b", "main"])
        print("已初始化 git 仓库")
    site = load_site()
    if not sh(["git", "config", "user.name"], check=False).stdout.strip():
        sh(["git", "config", "user.name", site.get("owner") or "VLA Notes"])
    if not sh(["git", "config", "user.email"], check=False).stdout.strip():
        owner = site.get("owner") or "vla-notes"
        sh(["git", "config", "user.email", "%s@users.noreply.github.com" % owner])


def remote_target():
    site = load_site()
    owner, repo, branch = site.get("owner"), site.get("repo"), site.get("branch") or "main"
    if not owner:
        url = sh(["git", "remote", "get-url", "origin"], check=False).stdout.strip()
        m = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", url)
        if not m:
            print("site.json 里 owner 为空，且没有可解析的 origin 远程。请先填写 owner / repo。")
            sys.exit(1)
        owner, repo = m.group(1), m.group(2)
    return owner, repo, branch


def push(message):
    ensure_git()
    sh(["git", "add", "-A"])
    status = sh(["git", "status", "--porcelain"]).stdout.strip()
    if status:
        sh(["git", "commit", "-m", message])
        print("已提交：%s" % message)
    else:
        print("没有需要提交的改动")

    owner, repo, branch = remote_target()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        url = "https://x-access-token:%s@github.com/%s/%s.git" % (token, owner, repo)
        res = sh(["git", "push", url, "HEAD:%s" % branch], check=False)
    else:
        if not sh(["git", "remote", "get-url", "origin"], check=False).stdout.strip():
            sh(["git", "remote", "add", "origin",
                "https://github.com/%s/%s.git" % (owner, repo)], check=False)
        res = sh(["git", "push", "-u", "origin", "%s" % branch], check=False)
    if res.returncode != 0:
        out = ((res.stderr or "") + (res.stdout or "")).strip()
        print("推送失败：")
        print(out)
        print("检查：GITHUB_TOKEN 是否有 repo 权限；owner/repo 是否写对；分支是否存在。")
        sys.exit(1)
    print("已推送到 https://github.com/%s/%s （分支 %s）" % (owner, repo, branch))


# ---------------------------------------------------------------- serve
def serve():
    import http.server
    import socketserver

    port = 8000
    os.chdir(ROOT)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print("本地预览：http://localhost:%d  （Ctrl+C 退出）" % port)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


def status():
    print("仓库目录：%s" % ROOT)
    if os.path.isdir(os.path.join(ROOT, ".git")):
        print(sh(["git", "status", "--short"], check=False).stdout.rstrip() or "工作区干净")
        print(sh(["git", "log", "--oneline", "-5"], check=False).stdout.rstrip())


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    cmd = args[0]
    if cmd == "build":
        build()
    elif cmd == "serve":
        serve()
    elif cmd == "new":
        build_note = os.path.join(ROOT, "tools", "build.py")
        sh([sys.executable, build_note, "new"] + args[1:], capture=False)
    elif cmd == "add":
        files = add(args[1:])
        if files:
            build()
            print("下一步：python3 tools/publish.py push -m \"add: %s\"" % os.path.basename(files[0]))
    elif cmd == "push":
        msg = None
        if "-m" in args:
            idx = args.index("-m")
            msg = args[idx + 1] if idx + 1 < len(args) else None
        build()
        push(msg or "update: 站点内容更新 %s" % date.today().isoformat())
    elif cmd == "up":
        files = args[1:]
        if files:
            add(files)
        build()
        push("update: 新增/更新笔记 %s" % date.today().isoformat())
    elif cmd == "status":
        status()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
