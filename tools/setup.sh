#!/usr/bin/env bash
# 首次配置：把当前目录接到已有仓库上（远程可能有 README 等提交），然后构建并推送
# 用法：
#   export GITHUB_TOKEN=ghp_xxx   # 可选；不设则用系统 git 凭据（Windows 会弹浏览器授权）
#   bash tools/setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."

read_cfg() {
  grep -o "\"$1\"[^,}]*" site.json 2>/dev/null | sed 's/.*: *"//; s/".*//' | head -1
}

OWNER="$(read_cfg owner)"
REPO="$(read_cfg repo)"
BRANCH="$(read_cfg branch)"
BRANCH="${BRANCH:-main}"

if [ -z "${OWNER}" ] || [ -z "${REPO}" ]; then
  echo "请先在 site.json 里填写 owner（GitHub 用户名）与 repo（仓库名）"
  exit 1
fi

URL="${GIT_REMOTE_URL:-https://github.com/${OWNER}/${REPO}.git}"

if [ ! -d .git ]; then
  git init -b "$BRANCH" >/dev/null
  echo "已初始化本地仓库（分支 $BRANCH）"
fi

git config user.name "${GIT_AUTHOR_NAME:-$OWNER}"
git config user.email "${GIT_AUTHOR_EMAIL:-${OWNER}@users.noreply.github.com}"
git config core.quotepath false

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$URL"
else
  git remote add origin "$URL"
fi
echo "远程：$URL"

# 关键一步：如果远程已经有提交（例如建仓库时勾了 README），
# 先取回来，把本地 HEAD 挂到远程历史上，避免首次 push 被 rejected。
if git fetch origin "$BRANCH" --quiet 2>/dev/null; then
  if git rev-parse --verify --quiet "origin/${BRANCH}" >/dev/null && ! git rev-parse --verify --quiet HEAD >/dev/null; then
    git reset --soft "origin/${BRANCH}"
    echo "已接上远程历史（远程已有提交：$(git log -1 --format=%s "origin/${BRANCH}")）"
  fi
fi

if command -v python3 >/dev/null 2>&1; then
  python3 tools/build.py
else
  echo "未检测到 python3：跳过本地构建（推送后由 GitHub Actions 自动构建）"
fi

git add -A
if git diff --cached --quiet; then
  echo "没有需要提交的改动"
else
  git commit -q -m "init: VLA 学习日志站点"
  echo "已创建提交：$(git log -1 --format=%s)"
fi

if [ -n "${GITHUB_TOKEN:-}" ]; then
  git push "https://x-access-token:${GITHUB_TOKEN}@github.com/${OWNER}/${REPO}.git" "HEAD:${BRANCH}"
else
  git push -u origin "$BRANCH"
fi

echo
echo "推送完成 → https://github.com/${OWNER}/${REPO}"
echo "下一步：仓库 Settings → Pages → Source 选 Deploy from a branch，分支 ${BRANCH}，目录 / (root)"
echo "约 1 分钟后访问 https://${OWNER}.github.io/${REPO}/"
