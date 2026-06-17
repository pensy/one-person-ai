#!/usr/bin/env bash
# 提交当前工作区所有变更，并同步推送到 gitee 和 origin。
# 用法: sync.sh "<commit message>"
set -uo pipefail

MSG="${1:-}"
if [ -z "$MSG" ]; then
  echo "❌ 用法: sync.sh \"<commit message>\"" >&2
  exit 1
fi

# 1. 暂存全部变更（新增、修改、删除）
git add -A

# 2. 没有可提交的内容则直接退出
if git diff --cached --quiet; then
  echo "ℹ️  工作区干净，没有变更需要提交"
  exit 0
fi

# 3. 提交
if ! git commit -m "$MSG"; then
  echo "❌ git commit 失败" >&2
  exit 1
fi

# 4. 取当前分支，分别推送到两个远程
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
fail=0

echo ""
echo "→ 推送到 gitee ($BRANCH) ..."
if git push gitee "$BRANCH"; then
  echo "✅ gitee 推送成功"
else
  echo "❌ gitee 推送失败（可能是 non-fast-forward，需要先 pull --rebase）" >&2
  fail=1
fi

echo ""
echo "→ 推送到 origin ($BRANCH) ..."
if git push origin "$BRANCH"; then
  echo "✅ origin 推送成功"
else
  echo "❌ origin 推送失败（可能是 non-fast-forward，需要先 pull --rebase）" >&2
  fail=1
fi

echo ""
exit $fail
