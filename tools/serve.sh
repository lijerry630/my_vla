#!/usr/bin/env bash
# 本地预览：在仓库根目录起一个静态服务
set -e
cd "$(dirname "$0")/.."
PORT="${1:-8000}"
echo "本地预览：http://localhost:${PORT}  （Ctrl+C 退出）"
python3 -m http.server "$PORT"
