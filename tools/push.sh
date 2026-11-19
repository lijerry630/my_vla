#!/usr/bin/env bash
# 日常提交：构建站点 → 提交改动 → 推送到 GitHub
# 用法：
#   export GITHUB_TOKEN=ghp_xxx        # 可选，不设则用系统已登录的 git 凭据
#   bash tools/push.sh                 # 提交信息自动生成
#   bash tools/push.sh "改了几个错字"    # 自定义提交信息
set -euo pipefail
cd "$(dirname "$0")/.."

read_cfg() {
  grep -o "\"$1\"[^,}]*" site.json 2>/dev/null | sed 's/.*: *"//; s/".*//' | head -1
}

OWNER="$(read_cfg owner)"
REPO="$(read_cfg repo)"
BRANCH="$(read_cfg branch)"
BRANCH="${BRANCH:-main}"
MSG="${1:-}"

if [ ! -d .git ]; then
  echo "还没有本地仓库，请先运行：bash tools/setup.sh"
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  python3 tools/build.py
else
  echo "未检测到 python3：跳过构建（新增或修改的 .md 不会反映到页面）"
fi

git add -A
if git diff --cached --quiet; then
  echo "没有需要提交的改动"
  exit 0
fi

if [ -z "$MSG" ]; then
  MSG="content: 更新 $(date '+%Y-%m-%d %H:%M')"
fi
git commit -q -m "$MSG"
echo "已提交：$MSG"

if [ -n "${GITHUB_TOKEN:-}" ]; then
  git push "https://x-access-token:${GITHUB_TOKEN}@github.com/${OWNER}/${REPO}.git" "HEAD:${BRANCH}"
else
  git push origin "$BRANCH"
fi

echo "已推送 → https://github.com/${OWNER}/${REPO} （Pages 约 1 分钟后更新）"
