#!/bin/bash
cd "$(dirname "$0")"

echo "正在从Git历史中删除包含敏感信息的文件..."

git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch "部署平台到公网.md"' \
  --prune-empty -- --all

echo "清理完成！正在推送到GitHub..."
git push origin main --force

echo "完成！"
