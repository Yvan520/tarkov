#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "=== Tarkov 每日内容更新 ==="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo

echo "[1/3] 收集数据..."
python3 tools/content_collector.py
echo

echo "[2/3] 写入文章并重新生成..."
python3 tools/content_writer.py
echo

echo "[3/3] 提交并推送..."
git add -A
if git diff --cached --stat | grep -q 'changed'; then
    git commit -m "auto: daily content update $(date +%Y-%m-%d)"
    git push
    echo "✅ 已推送"
else
    echo "无新内容"
fi
