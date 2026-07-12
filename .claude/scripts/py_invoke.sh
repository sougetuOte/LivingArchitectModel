#!/usr/bin/env bash
# LAM Python Invoke Helper
# 目的: pyenv-win shim 経由の VBScript 発火を回避 (2027 VBScript 廃止対策)
#
# 動作:
#   1. $CLAUDE_PROJECT_DIR/.venv 内の interpreter を優先探索
#   2. 存在確認だけでなく実起動可能性を "-c 'import sys'" で実測
#      (存在するが起動不能な .venv による silent failure 対策 / HGA #14 F11)
#   3. .venv 未利用 or 起動不能なら python3 -> python の fallback chain
#   4. いずれも失敗なら exit 127 + stderr メッセージ (explicit fail)
#
# 呼び出し例:
#   bash "$CLAUDE_PROJECT_DIR/.claude/scripts/py_invoke.sh" \
#        "$CLAUDE_PROJECT_DIR/.claude/hooks/pre-tool-use.py"
#
# 参照: .claude/rules/hga-summoning.md #14 応答 / CLAUDE.md Execution Environment
set -eu

ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"

_resolve_python() {
  local candidate
  for candidate in \
    "$ROOT/.venv/Scripts/python.exe" \
    "$ROOT/.venv/bin/python"; do
    if [ -x "$candidate" ]; then
      if "$candidate" -c "import sys" >/dev/null 2>&1; then
        printf '%s\n' "$candidate"
        return 0
      fi
    fi
  done
  if command -v python3 >/dev/null 2>&1; then
    printf 'python3\n'
    return 0
  fi
  if command -v python >/dev/null 2>&1; then
    printf 'python\n'
    return 0
  fi
  return 1
}

if ! PY="$(_resolve_python)"; then
  printf 'LAM py_invoke: no python interpreter available (.venv / python3 / python all failed)\n' >&2
  exit 127
fi

exec "$PY" "$@"
