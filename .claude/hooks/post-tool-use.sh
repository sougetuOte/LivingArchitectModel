#!/usr/bin/env bash
# LAM PostToolUse hook: ツール実行後の処理
# 設計書 Section 3.3 準拠
#
# 責務:
#   1. TDD パターン検出（テスト結果の記録）
#   2. doc-sync-flag の設定（src/ 配下の Edit/Write 検知）
#   3. ループログへの記録（lam-loop-state.json が存在する場合）
#
# エラーが発生しても exit 0 を返す（PostToolUse hook は Claude の動作をブロックしない）

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

TDD_LOG="${PROJECT_ROOT}/.claude/tdd-patterns.log"
DOC_SYNC_FLAG="${PROJECT_ROOT}/.claude/doc-sync-flag"
LAST_RESULT="${PROJECT_ROOT}/.claude/last-test-result"
LOOP_STATE="${PROJECT_ROOT}/.claude/lam-loop-state.json"

# ログディレクトリ確保
mkdir -p "${PROJECT_ROOT}/.claude" 2>/dev/null || true

# stdin から JSON を読み取る（エラー時は何もせず exit 0）
INPUT=$(cat) || exit 0

# ----- jq の有無を確認 -----

HAS_JQ=false
if command -v jq >/dev/null 2>&1; then
  HAS_JQ=true
fi

# ----- フィールド取得 -----

TOOL_NAME=""
COMMAND=""
FILE_PATH=""
EXIT_CODE=""
STDOUT=""

if "${HAS_JQ}"; then
  TOOL_NAME=$(echo "${INPUT}" | jq -r '.tool_name // empty' 2>/dev/null || echo "")
  COMMAND=$(echo "${INPUT}" | jq -r '.tool_input.command // empty' 2>/dev/null || echo "")
  FILE_PATH=$(echo "${INPUT}" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo "")
  # exitCode と exit_code の両方を試みる
  EXIT_CODE=$(echo "${INPUT}" | jq -r '(.tool_response.exitCode // .tool_response.exit_code // "") | tostring' 2>/dev/null || echo "")
  STDOUT=$(echo "${INPUT}" | jq -r '.tool_response.stdout // empty' 2>/dev/null || echo "")
else
  # jq なし: tool_name のみ簡易抽出
  TOOL_NAME=$(echo "${INPUT}" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' 2>/dev/null \
    | sed 's/.*:[[:space:]]*"\([^"]*\)"/\1/' | head -1 || echo "")
  COMMAND=$(echo "${INPUT}" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' 2>/dev/null \
    | sed 's/.*:[[:space:]]*"\([^"]*\)"/\1/' | head -1 || echo "")
  FILE_PATH=$(echo "${INPUT}" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' 2>/dev/null \
    | sed 's/.*:[[:space:]]*"\([^"]*\)"/\1/' | head -1 || echo "")
  EXIT_CODE=$(echo "${INPUT}" | grep -o '"exitCode"[[:space:]]*:[[:space:]]*[0-9]*' 2>/dev/null \
    | sed 's/.*:[[:space:]]*//' | head -1 || echo "")
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ----- 1. テスト結果の記録 -----

is_test_command() {
  local cmd="$1"
  echo "${cmd}" | grep -qE '(^|[[:space:]])(pytest|npm[[:space:]]+test|go[[:space:]]+test)([[:space:]]|$)' 2>/dev/null
}

if [ "${TOOL_NAME}" = "Bash" ] && is_test_command "${COMMAND}"; then
  # コマンド種別を短縮形で記録
  TEST_CMD="pytest"
  if echo "${COMMAND}" | grep -q 'npm'; then
    TEST_CMD="npm test"
  elif echo "${COMMAND}" | grep -q 'go test'; then
    TEST_CMD="go test"
  fi

  # 前回の結果を読み取る
  PREV_RESULT=""
  if [ -f "${LAST_RESULT}" ]; then
    PREV_RESULT=$(head -1 "${LAST_RESULT}" 2>/dev/null || echo "")
  fi

  if [ "${EXIT_CODE}" != "0" ] && [ -n "${EXIT_CODE}" ]; then
    # 失敗パターンを記録
    SUMMARY=$(echo "${STDOUT}" | head -3 | tr '\n' ' ' | cut -c1-120)
    echo "${TIMESTAMP}  FAIL  ${TEST_CMD}  \"${SUMMARY}\"" >> "${TDD_LOG}" 2>/dev/null || true
    echo "fail ${TEST_CMD}" > "${LAST_RESULT}" 2>/dev/null || true

  elif [ "${EXIT_CODE}" = "0" ]; then
    # 成功: 前回失敗だった場合は「失敗→成功」パターンを記録
    if echo "${PREV_RESULT}" | grep -q '^fail'; then
      echo "${TIMESTAMP}  PASS  ${TEST_CMD}  \"${TEST_CMD} (previously failed)\"" >> "${TDD_LOG}" 2>/dev/null || true
    fi
    echo "pass ${TEST_CMD}" > "${LAST_RESULT}" 2>/dev/null || true
  fi
fi

# ----- 2. ドキュメント更新判定 -----

if [ "${TOOL_NAME}" = "Edit" ] || [ "${TOOL_NAME}" = "Write" ]; then
  # FILE_PATH が src/ 配下かどうかを判定
  # 絶対パスと相対パスの両方に対応
  NORMALIZED_PATH="${FILE_PATH}"

  # 絶対パスの場合、PROJECT_ROOT プレフィックスを除去して相対パスに変換
  if [[ "${FILE_PATH}" == "${PROJECT_ROOT}/"* ]]; then
    NORMALIZED_PATH="${FILE_PATH#"${PROJECT_ROOT}"/}"
  fi

  # src/ 配下かどうかチェック（正規化済みの相対パスで判定）
  if echo "${NORMALIZED_PATH}" | grep -qE '^src/' 2>/dev/null; then
    # 重複防止: 既に記録済みのパスはスキップ（AC-4.6: 承認疲れ防止）
    # NORMALIZED_PATH（相対パス）で統一して書き込み・チェックする
    if [ -f "${DOC_SYNC_FLAG}" ] && grep -qFx "${NORMALIZED_PATH}" "${DOC_SYNC_FLAG}" 2>/dev/null; then
      :  # 既に記録済み
    else
      echo "${NORMALIZED_PATH}" >> "${DOC_SYNC_FLAG}" 2>/dev/null || true
    fi
  fi
fi

# ----- 3. ループログ記録 -----

if [ -f "${LOOP_STATE}" ]; then
  if "${HAS_JQ}"; then
    # tool_events 配列に追記する
    # lam-loop-state.json を読み込み、tool_events フィールドを更新
    LOOP_JSON=$(cat "${LOOP_STATE}" 2>/dev/null) || LOOP_JSON="{}"

    EVENT=$(jq -n \
      --arg ts "${TIMESTAMP}" \
      --arg tool "${TOOL_NAME}" \
      --arg cmd "${COMMAND}" \
      --arg fp "${FILE_PATH}" \
      --arg ec "${EXIT_CODE}" \
      '{timestamp: $ts, tool_name: $tool, command: $cmd, file_path: $fp, exit_code: $ec}' \
      2>/dev/null) || EVENT="{}"

    # tool_events 配列が存在しない場合は空配列で初期化して追記
    UPDATED=$(echo "${LOOP_JSON}" | jq \
      --argjson event "${EVENT}" \
      'if .tool_events then .tool_events += [$event] else .tool_events = [$event] end' \
      2>/dev/null) || UPDATED="${LOOP_JSON}"

    echo "${UPDATED}" > "${LOOP_STATE}" 2>/dev/null || true
  else
    # jq なし: 末尾にコメント行として追記（JSON は壊れるが記録は残る）
    # ループ状態ファイルへの書き込みは best-effort
    true
  fi
fi

exit 0
