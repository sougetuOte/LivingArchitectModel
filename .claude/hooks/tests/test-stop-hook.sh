#!/usr/bin/env bash
# Stop hook のスモークテスト
# 実行: bash .claude/hooks/tests/test-stop-hook.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
HOOK="${PROJECT_ROOT}/.claude/hooks/lam-stop-hook.sh"
STATE_FILE="${PROJECT_ROOT}/.claude/lam-loop-state.json"
PRE_COMPACT_FLAG="${PROJECT_ROOT}/.claude/pre-compact-fired"

PASS=0
FAIL=0

# テスト用一時ファイルの追跡
TEMP_FILES=()

cleanup() {
  # 状態ファイルを元の状態に戻す
  rm -f "${STATE_FILE}" 2>/dev/null || true
  rm -f "${PRE_COMPACT_FLAG}" 2>/dev/null || true
  # 一時ファイルを削除
  for f in "${TEMP_FILES[@]+"${TEMP_FILES[@]}"}"; do
    rm -f "${f}" 2>/dev/null || true
  done
}
trap cleanup EXIT

# 共通ヘルパー読み込み
# shellcheck source=test-helpers.sh
source "$(dirname "$0")/test-helpers.sh"

# ================================================================
# TC-1: shellcheck 構文チェック
# ================================================================
echo ""
echo "TC-1: shellcheck 構文チェック"
if command -v shellcheck >/dev/null 2>&1; then
  shellcheck_exit=0
  shellcheck_output=$(shellcheck -S warning "${HOOK}" 2>&1) || shellcheck_exit=$?
  if [ ${shellcheck_exit} -eq 0 ]; then
    echo "  PASS: shellcheck clean"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: shellcheck エラーあり"
    echo "${shellcheck_output}"
    FAIL=$((FAIL + 1))
  fi
else
  echo "  SKIP: shellcheck not available"
fi

# ================================================================
# TC-2: 状態ファイルなし → exit 0（通過）(AC-2.5)
# ================================================================
echo ""
echo "TC-2: 状態ファイルなし → exit 0"

cleanup

INPUT='{"session_id":"test","transcript_path":"/tmp/t","cwd":"/tmp","permission_mode":"default","hook_event_name":"Stop","stop_hook_active":false,"last_assistant_message":"done"}'

actual_stdout=$(echo "${INPUT}" | bash "${HOOK}" 2>/dev/null)
actual_exit=$?

assert_exit "exit code is 0" 0 "${actual_exit}"
assert_stdout_empty "stdout is empty (no block decision)" "${actual_stdout}"

# ================================================================
# TC-3: 状態ファイルあり + iteration >= max_iterations → exit 0 + 状態ファイル削除 (AC-2.6)
# ================================================================
echo ""
echo "TC-3: iteration >= max_iterations → 停止"

cleanup

cat > "${STATE_FILE}" << 'STATE'
{
  "active": true,
  "command": "full-review",
  "target": "src/",
  "iteration": 5,
  "max_iterations": 5,
  "started_at": "2026-03-08T10:00:00Z",
  "log": []
}
STATE

INPUT='{"session_id":"test","transcript_path":"/tmp/t","cwd":"/tmp","permission_mode":"default","hook_event_name":"Stop","stop_hook_active":false,"last_assistant_message":"done"}'

actual_stdout=$(echo "${INPUT}" | bash "${HOOK}" 2>/dev/null)
actual_exit=$?

assert_exit "exit code is 0 (stop)" 0 "${actual_exit}"
assert_stdout_empty "stdout is empty when stopping" "${actual_stdout}"

if [ ! -f "${STATE_FILE}" ]; then
  echo "  PASS: 状態ファイルが削除された"
  PASS=$((PASS + 1))
else
  echo "  FAIL: 状態ファイルが残っている"
  FAIL=$((FAIL + 1))
fi

# ================================================================
# TC-4: stop_hook_active=true + 状態ファイルなし → exit 0（再帰防止）(AC-2.8c)
# ================================================================
echo ""
echo "TC-4: stop_hook_active=true + 状態ファイルなし → 再帰防止で exit 0"

cleanup

INPUT='{"session_id":"test","transcript_path":"/tmp/t","cwd":"/tmp","permission_mode":"default","hook_event_name":"Stop","stop_hook_active":true,"last_assistant_message":"done"}'

actual_stdout=$(echo "${INPUT}" | bash "${HOOK}" 2>/dev/null)
actual_exit=$?

assert_exit "exit code is 0 (recursion guard)" 0 "${actual_exit}"
assert_stdout_empty "stdout is empty (recursion guard)" "${actual_stdout}"

# ================================================================
# TC-5: 状態ファイルあり + テスト失敗環境 → decision:block を返す (AC-2.10)
# ================================================================
echo ""
echo "TC-5: 状態ファイルあり + テスト失敗環境 → decision:block を返す"

cleanup

cat > "${STATE_FILE}" << 'STATE'
{
  "active": true,
  "command": "full-review",
  "target": "src/",
  "iteration": 1,
  "max_iterations": 5,
  "started_at": "2026-03-08T10:00:00Z",
  "log": []
}
STATE

# テストが失敗する環境を擬似的に作成（Makefile で exit 1 するテスト）
FAKE_DIR=$(mktemp -d)
TEMP_FILES+=("${FAKE_DIR}")
cat > "${FAKE_DIR}/Makefile" << 'MAKEFILE'
test:
	@exit 1
MAKEFILE

INPUT="{\"session_id\":\"test\",\"transcript_path\":\"/tmp/t\",\"cwd\":\"${FAKE_DIR}\",\"permission_mode\":\"default\",\"hook_event_name\":\"Stop\",\"stop_hook_active\":false,\"last_assistant_message\":\"done\"}"

actual_stdout=$(echo "${INPUT}" | bash "${HOOK}" 2>/dev/null)
actual_exit=$?

assert_exit "exit code is 0 (hook always exits 0)" 0 "${actual_exit}"
assert_stdout_contains "stdout contains 'decision'" "decision" "${actual_stdout}"
assert_stdout_contains "stdout contains 'block'" "block" "${actual_stdout}"

# iteration がインクリメントされているか確認
if [ -f "${STATE_FILE}" ]; then
  if command -v jq >/dev/null 2>&1; then
    new_iter=$(jq '.iteration' "${STATE_FILE}" 2>/dev/null || echo "0")
    if [ "${new_iter}" -eq 2 ]; then
      echo "  PASS: iteration がインクリメントされた (1 -> 2)"
      PASS=$((PASS + 1))
    else
      echo "  FAIL: iteration が正しくない (expected 2, got ${new_iter})"
      FAIL=$((FAIL + 1))
    fi
  else
    # jq なし: grep で確認
    if grep -q '"iteration": 2' "${STATE_FILE}" || grep -q '"iteration":2' "${STATE_FILE}"; then
      echo "  PASS: iteration がインクリメントされた (1 -> 2)"
      PASS=$((PASS + 1))
    else
      echo "  FAIL: iteration が正しくない"
      cat "${STATE_FILE}"
      FAIL=$((FAIL + 1))
    fi
  fi
else
  echo "  FAIL: 状態ファイルが存在しない（継続のはずなのに削除された）"
  FAIL=$((FAIL + 1))
fi

rm -rf "${FAKE_DIR}" 2>/dev/null || true

# ================================================================
# TC-6: PreCompact 発火フラグが直近（5分以内）にある → 停止 (AC-2.7)
# ================================================================
echo ""
echo "TC-6: PreCompact 直近発火 → コンテキスト圧迫でループ停止"

cleanup

cat > "${STATE_FILE}" << 'STATE'
{
  "active": true,
  "command": "full-review",
  "target": "src/",
  "iteration": 1,
  "max_iterations": 5,
  "started_at": "2026-03-08T10:00:00Z",
  "log": []
}
STATE

# 直近のタイムスタンプで pre-compact-fired を作成
date -u +"%Y-%m-%dT%H:%M:%SZ" > "${PRE_COMPACT_FLAG}"

INPUT='{"session_id":"test","transcript_path":"/tmp/t","cwd":"/tmp","permission_mode":"default","hook_event_name":"Stop","stop_hook_active":false,"last_assistant_message":"done"}'

actual_stdout=$(echo "${INPUT}" | bash "${HOOK}" 2>/dev/null)
actual_exit=$?

assert_exit "exit code is 0 (context pressure stop)" 0 "${actual_exit}"
assert_stdout_empty "stdout is empty (context pressure stops loop)" "${actual_stdout}"

if [ ! -f "${STATE_FILE}" ]; then
  echo "  PASS: 状態ファイルが削除された（ループ停止）"
  PASS=$((PASS + 1))
else
  echo "  FAIL: 状態ファイルが残っている（ループが停止されていない）"
  FAIL=$((FAIL + 1))
fi

# ================================================================
# TC-7: スキーマ正当性（状態ファイルの読み書き）
# ================================================================
echo ""
echo "TC-7: 状態ファイルスキーマの正当性確認（テスト失敗環境での継続後）"

cleanup

cat > "${STATE_FILE}" << 'STATE'
{
  "active": true,
  "command": "full-review",
  "target": "src/",
  "iteration": 2,
  "max_iterations": 5,
  "started_at": "2026-03-08T10:00:00Z",
  "log": [
    {"iteration": 1, "issues_found": 3, "issues_fixed": 3, "pg": 2, "se": 1, "pm": 0}
  ]
}
STATE

# テストが失敗する環境（Makefile で exit 1）
FAKE_DIR=$(mktemp -d)
TEMP_FILES+=("${FAKE_DIR}")
cat > "${FAKE_DIR}/Makefile" << 'MAKEFILE'
test:
	@exit 1
MAKEFILE

INPUT="{\"session_id\":\"test\",\"transcript_path\":\"/tmp/t\",\"cwd\":\"${FAKE_DIR}\",\"permission_mode\":\"default\",\"hook_event_name\":\"Stop\",\"stop_hook_active\":false,\"last_assistant_message\":\"done\"}"

actual_stdout=$(echo "${INPUT}" | bash "${HOOK}" 2>/dev/null)
actual_exit=$?

assert_exit "exit code is 0" 0 "${actual_exit}"

# 継続シナリオなので状態ファイルは残っているはず
if [ -f "${STATE_FILE}" ]; then
  if command -v jq >/dev/null 2>&1; then
    if jq empty "${STATE_FILE}" 2>/dev/null; then
      echo "  PASS: 状態ファイルは有効なJSON"
      PASS=$((PASS + 1))
      # 必須フィールドの存在確認
      for field in active command target iteration max_iterations started_at log; do
        if jq -e ".${field}" "${STATE_FILE}" >/dev/null 2>&1; then
          echo "  PASS: フィールド '${field}' が存在する"
          PASS=$((PASS + 1))
        else
          echo "  FAIL: フィールド '${field}' が存在しない"
          FAIL=$((FAIL + 1))
        fi
      done
    else
      echo "  FAIL: 状態ファイルが無効なJSON"
      cat "${STATE_FILE}"
      FAIL=$((FAIL + 1))
    fi
  else
    echo "  SKIP: jq not available, skipping JSON validation"
  fi
else
  echo "  FAIL: 継続のはずなのに状態ファイルが削除された"
  FAIL=$((FAIL + 1))
fi

rm -rf "${FAKE_DIR}" 2>/dev/null || true

# ================================================================
# 結果サマリ
# ================================================================
echo ""
echo "================================"
echo "結果: PASS=${PASS} FAIL=${FAIL}"
echo "================================"

if [ "${FAIL}" -eq 0 ]; then
  echo "全テスト通過"
  exit 0
else
  echo "失敗あり"
  exit 1
fi
