# VLA 学习日志

记录学习 VLA 的项目内容。一个纯静态、用 Markdown 维护的学习站点，系统整理视觉-语言-动作模型（VLA）的概念、架构与实验记录。托管在 GitHub Pages 上，本地写、一条命令发布。

## 目录结构

```text
vla-notes/
├─ content/              笔记与页面源文件（Markdown + front matter）
├─ theme/                页面骨架模板（$NAME 为占位符）
├─ assets/               样式、脚本、图标、图片（assets/img/）
├─ tools/
│  ├─ build.py           构建：md -> notes/*.html / index.html / notes.html
│  ├─ setup.sh           首次配置：绑定远程 + 身份 + 首次推送（bash）
│  ├─ push.sh            日常提交：构建 + commit + push（bash）
│  ├─ setup.bat          同上，Windows CMD 版（推荐）
│  ├─ push.bat           同上，Windows CMD 版（推荐）
│  ├─ setup.ps1          同上，Windows PowerShell 版
│  ├─ push.ps1           同上，Windows PowerShell 版
│  ├─ publish.py         一站式：导入本地文件 -> 构建 -> 提交 -> 推送
│  └─ serve.sh           本地预览
├─ docs/                 写作、发布、本地提交的说明
├─ notes/                生成产物（勿手改）
├─ index.html            生成产物
├─ notes.html            生成产物
├─ about.html            生成产物
├─ resources.html        生成产物
└─ site.json             站点与仓库配置
```

## 本地预览

```bash
python3 tools/serve.sh      # 或 python3 tools/publish.py serve
# 打开 http://localhost:8000
```

## 写一篇新笔记

```bash
python3 tools/publish.py new "动作分块与滚动重规划"
# 编辑 content/ 下新生成的 md，然后
python3 tools/build.py
```

front matter 字段：

```yaml
---
title: 标题
date: 2026-11-18
tags: 概念, 入门
summary: 一句话说清这篇回答什么问题
order: 8
slug: my-note
---
```

`order` 决定笔记顺序与 `LOG 0x` 编号；`slug` 决定 URL（`notes/<slug>.html`）。图片放到 `assets/img/`，正文里写 `![说明](assets/img/xxx.png)`，构建时会自动改写成笔记页可用的相对路径。

## 从本地提交到 GitHub

完整步骤见 [`docs/本地提交指南.md`](docs/本地提交指南.md)（含 PAT、SSH、Windows/macOS 差异与报错排查）。最短路：

```bash
# 一次性
export GITHUB_TOKEN=ghp_xxxxxxxx    # 需要 repo 权限；PowerShell 用 $env:GITHUB_TOKEN
bash tools/setup.sh                 # Windows: tools\setup.bat（或 setup.ps1）

# 日常（会先构建，再提交，再推送）
bash tools/push.sh "add: 新笔记"     # Windows: tools\push.bat "add: 新笔记"
```

也可以用 Python 一站式导入外部文件：

```bash
python3 tools/publish.py up ~/Documents/我的笔记.md
```

> 改了 `content/*.md` 必须重新构建，`notes/*.html` 才会更新。`push.sh` 已内置构建，只上传 md 页面不会变。

## 开启 GitHub Pages

仓库推上去之后，在 GitHub 上：

1. 进入仓库 `Settings → Pages`
2. `Build and deployment → Source` 选 `Deploy from a branch`
3. 分支选 `main`，目录选 `/ (root)`，保存
4. 等 1 到 2 分钟，访问 `https://<用户名>.github.io/<仓库名>/`

仓库根目录已有 `.nojekyll`，Jekyll 不会介入，`notes/` 这类以下划线或特殊命名的文件都能正常访问。

## 只用网页上传（不装 Python）

生成的 HTML 已经在仓库里了，只是新增/修改笔记时需要重新构建。如果不能或不想在本地跑 Python：

1. 新建一个空仓库，把本目录的所有文件拖进 GitHub 网页的 `Add file → Upload files`
2. 提交后按上面的步骤开启 Pages
3. 以后要加新笔记，在本地跑一次 `python3 tools/build.py`，再把变化过的 `index.html`、`notes.html`、`notes/*.html`、`content/*.md` 一起上传覆盖

换句话说：**改 md 必须重新构建**，只上传 md 不会让页面变。

## 许可

正文内容为个人学习记录，欢迎引用并注明来源；站点代码可自由复用。
