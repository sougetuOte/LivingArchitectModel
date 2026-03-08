#!/usr/bin/env bash
# LAM PreToolUse hook: 権限等級判定（PG/SE/PM）
# 設計書 Section 3.2 準拠
#
# stdin から JSON を受け取り、ツール名とファイルパスに基づいて
# PG/SE/PM の等級を判定する。
#
# 判定結果:
#   PG級 → exit 0（許可）
#   SE級 → exit 0 + ログ記録
#   PM級 → JSON で block を返す

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_FILE="${PROJECT_ROOT}/.claude/logs/permission.log"
PHASE_FILE="${PROJECT_ROOT}/.claude/current-phase.md"

# ログディレクトリが存在しなければ作成
mkdir -p "$(dirname "${LOG_FILE}")" 2>/dev/null || true

# stdin から JSON を読み取る
INPUT=$(cat)

# ツール名を抽出（jq なし環境でもフォールバック）
if command -v jq >/dev/null 2>&1; then
  TOOL_NAME=$(echo "${INPUT}" | jq -r '.tool_name // empty' 2>/dev/null || echo "")
else
  # jq なしフォールバック: grep + sed で簡易抽出
  TOOL_NAME=$(echo "${INPUT}" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' 2>/dev/null \
    | sed 's/.*:[[:space:]]*"\([^"]*\)"/\1/' | head -1 || echo "")
fi

# ツール名が取得できない場合は SE 級扱い（安全側に倒す）
if [ -z "${TOOL_NAME}" ]; then
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  echo "${TIMESTAMP}  SE  unknown  -  \"tool_name extraction failed (no jq?)\"" >> "${LOG_FILE}" 2>/dev/null || true
  exit 0
fi

# 1. 読取り専用ツールは常に許可（PG級としてログ記録）
case "${TOOL_NAME}" in
  Read|Glob|Grep|WebSearch|WebFetch)
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "${TIMESTAMP}  PG  ${TOOL_NAME}  -  \"read-only tool\"" >> "${LOG_FILE}" 2>/dev/null || true
    exit 0
    ;;
esac

# ファイルパスを抽出（Edit/Write の場合）
# Bash コマンドの場合、コマンド文字列を取得
if command -v jq >/dev/null 2>&1; then
  FILE_PATH=$(echo "${INPUT}" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo "")
  COMMAND=$(echo "${INPUT}" | jq -r '.tool_input.command // empty' 2>/dev/null || echo "")
else
  FILE_PATH=$(echo "${INPUT}" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' 2>/dev/null \
    | sed 's/.*:[[:space:]]*"\([^"]*\)"/\1/' | head -1 || echo "")
  COMMAND=$(echo "${INPUT}" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' 2>/dev/null \
    | sed 's/.*:[[:space:]]*"\([^"]*\)"/\1/' | head -1 || echo "")
fi

# ファイルパスもコマンドもない場合（Agent 等）は SE級扱い
if [ -z "${FILE_PATH}" ] && [ -z "${COMMAND}" ]; then
  LEVEL="SE"
  REASON="no-path (default SE)"
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  echo "${TIMESTAMP}  ${LEVEL}  ${TOOL_NAME}  -  \"${REASON}\"" >> "${LOG_FILE}" 2>/dev/null || true
  exit 0
fi

# 2. ファイルパスベース判定
LEVEL="SE"
REASON="default (safe side)"

if [ -n "${FILE_PATH}" ]; then
  case "${FILE_PATH}" in
    # PM級: 仕様書
    docs/specs/*.md|*/docs/specs/*.md)
      LEVEL="PM"
      REASON="specs/ path"
      ;;
    # PM級: ADR
    docs/adr/*.md|*/docs/adr/*.md)
      LEVEL="PM"
      REASON="adr/ path"
      ;;
    # PM級: ルールファイル（サブディレクトリ含む）
    .claude/rules/*.md|*/.claude/rules/*.md|.claude/rules/*/*.md|*/.claude/rules/*/*.md)
      LEVEL="PM"
      REASON="rules/ path"
      ;;
    # PM級: 設定ファイル
    .claude/settings*.json|*/.claude/settings*.json)
      LEVEL="PM"
      REASON="settings path"
      ;;
    # SE級: docs/ 配下（上記以外）
    docs/*|*/docs/*)
      LEVEL="SE"
      REASON="docs/ path (non-specs/adr)"
      ;;
    # SE級: src/ 配下（実装コード）
    src/*|*/src/*)
      LEVEL="SE"
      REASON="src/ path"
      ;;
    # SE級: その他（デフォルト、安全側）
    *)
      LEVEL="SE"
      REASON="default path"
      ;;
  esac
fi

# 3. AUDITING フェーズの特別処理
CURRENT_PHASE=""
if [ -f "${PHASE_FILE}" ]; then
  # **PHASE** 形式から PHASE を抽出（grep -P 非依存）
  CURRENT_PHASE=$(sed -n 's/^\*\*\([A-Z]*\)\*\*.*/\1/p' "${PHASE_FILE}" 2>/dev/null | head -1 || echo "")
fi

# AUDITING フェーズでは PG級ツール（lint修正等）は allow
if [ "${CURRENT_PHASE}" = "AUDITING" ] && [ -n "${COMMAND}" ]; then
  case "${COMMAND}" in
    "npx prettier"*|"npx eslint --fix"*|"ruff check --fix"*|"ruff format"*)
      LEVEL="PG"
      REASON="AUDITING phase PG allow"
      ;;
  esac
fi

# 4. ログ記録
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TARGET="${FILE_PATH:-${COMMAND}}"
echo "${TIMESTAMP}  ${LEVEL}  ${TOOL_NAME}  ${TARGET}  \"${REASON}\"" >> "${LOG_FILE}" 2>/dev/null || true

# 5. 応答
case "${LEVEL}" in
  PG)
    exit 0
    ;;
  SE)
    # SE級: 許可 + ログ記録（ログは上で記録済み）
    exit 0
    ;;
  PM)
    # PM級: deny（hookSpecificOutput 形式、最新 Claude Code 仕様準拠）
    if command -v jq >/dev/null 2>&1; then
      jq -n --arg reason "PM級変更です。承認してください: ${TARGET}" '{
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "deny",
          permissionDecisionReason: $reason
        }
      }'
    else
      SAFE_TARGET=$(echo "${TARGET}" | tr -d '"\\')
      echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"PM級変更です。承認してください: ${SAFE_TARGET}\"}}"
    fi
    exit 0
    ;;
esac

exit 0
