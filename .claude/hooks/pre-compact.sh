#!/usr/bin/env bash
# LAM PreCompact hook: コンテキスト圧縮前の状態保存
# 設計書 Section 3.5 準拠
#
# PreCompact hook は圧縮前に SESSION_STATE.md を自動保存する。
# エラーが発生しても exit 0 を返し、圧縮をブロックしない。

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SESSION_STATE="${PROJECT_ROOT}/SESSION_STATE.md"
LOOP_STATE="${PROJECT_ROOT}/.claude/lam-loop-state.json"
PRE_COMPACT_FLAG="${PROJECT_ROOT}/.claude/pre-compact-fired"

# PreCompact 発火フラグを記録（Stop hook が参照する）
date -u +"%Y-%m-%dT%H:%M:%SZ" > "${PRE_COMPACT_FLAG}" 2>/dev/null || true

# SESSION_STATE.md に PreCompact 発火を記録（冪等: 既存エントリは上書き）
if [ -f "${SESSION_STATE}" ]; then
  # 既存の PreCompact セクションがあれば時刻のみ更新、なければ追記
  if grep -q "## PreCompact 発火" "${SESSION_STATE}" 2>/dev/null; then
    # 既存エントリの時刻行を更新
    sed -i "s/- 時刻: .*/- 時刻: $(date -u +"%Y-%m-%dT%H:%M:%SZ")/" "${SESSION_STATE}" 2>/dev/null || true
  else
    echo "" >> "${SESSION_STATE}" 2>/dev/null || true
    echo "## PreCompact 発火" >> "${SESSION_STATE}" 2>/dev/null || true
    echo "- 時刻: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" >> "${SESSION_STATE}" 2>/dev/null || true
  fi
else
  # SESSION_STATE.md が存在しない場合はログにフォールバック記録
  echo "$(date -u +"%Y-%m-%dT%H:%M:%SZ") PreCompact fired (no SESSION_STATE.md)" >> "${PROJECT_ROOT}/.claude/logs/loop.log" 2>/dev/null || true
fi

# ループ中であれば lam-loop-state.json のバックアップ
if [ -f "${LOOP_STATE}" ]; then
  cp "${LOOP_STATE}" "${LOOP_STATE}.bak" 2>/dev/null || true
fi

# 常に exit 0（圧縮を許可）
exit 0
