#!/usr/bin/env bash
# ループ統合テスト（T2-5 AC-2.26）
# Stop hook + full-review 状態ファイルの連携をシミュレーション
# 実行: bash .claude/hooks/tests/test-loop-integration.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
HOOK="${PROJECT_ROOT}/.claude/hooks/lam-stop-hook.sh"
STATE_FILE="${PROJECT_ROOT}/.claude/lam-loop-state.json"
PRE_COMPACT_FLAG="${PROJECT_ROOT}/.claude/pre-compact-fired"

PASS=0
FAIL=0

TEMP_FILES=()

cleanup() {
  rm -f "${STATE_FILE}" 2>/dev/null || true
  rm -f "${PRE_COMPACT_FLAG}" 2>/dev/null || true
  for f in "${TEMP_FILES[@]+"${TEMP_FILES[@]}"}"; do
    rm -rf "${f}" 2>/dev/null || true
  done
}
trap cleanup EXIT

# 共通ヘルパー読み込み
# shellcheck source=test-helpers.sh
source "$(dirname "$0")/test-helpers.sh"

# ================================================================
# S-1: 正常収束シミュレーション
# PG級のみ → 1-2サイクルで Green State 達成 → 自動停止
# ================================================================
echo ""
echo "=== S-1: 正常収束シミュレーション ==="
echo ""

# --- S-1 サイクル1: テスト成功環境 → Green State → 停止 ---
echo "S-1-1: Green State 達成環境 → ループ停止"

cleanup

# テスト・lint ともに成功する環境を作成
FAKE_DIR=$(mktemp -d)
TEMP_FILES+=("${FAKE_DIR}")
cat > "${FAKE_DIR}/Makefile" << 'MAKEFILE'
test:
	@exit 0
lint:
	@exit 0
MAKEFILE

# iteration 1（1サイクル目完了）の状態ファイル
cat > "${STATE_FILE}" << 'STATE'
{
  "active": true,
  "command": "full-review",
  "target": "src/",
  "iteration": 1,
  "max_iterations": 5,
  "started_at": "2026-03-08T10:00:00Z",
  "log": [
    {"iteration": 0, "issues_found": 2, "issues_fixed": 2, "pg": 2, "se": 0, "pm": 0}
  ]
}
STATE

INPUT="{\"session_id\":\"test\",\"transcript_path\":\"/tmp/t\",\"cwd\":\"${FAKE_DIR}\",\"permission_mode\":\"default\",\"hook_event_name\":\"Stop\",\"stop_hook_active\":false,\"last_assistant_message\":\"Green State 達成。全修正完了。\"}"

actual_stdout=$(echo "${INPUT}" | bash "${HOOK}" 2>/dev/null)
actual_exit=$?

assert_exit "exit 0 (停止 = Green State 達成)" 0 "${actual_exit}"
assert_stdout_empty "stdout empty (通過 = 停止)" "${actual_stdout}"
assert_file_not_exists "状態ファイルが削除された" "${STATE_FILE}"

rm -rf "${FAKE_DIR}" 2>/dev/null || true

# ================================================================
# S-2: PM級エスカレーション シミュレーション
# PM級問題検出 → ループ停止
# ================================================================
echo ""
echo "=== S-2: PM級エスカレーション シミュレーション ==="
echo ""

echo "S-2-1: テスト失敗 → block で継続（PM級検出は Claude の責務のため hook では未検証）"

cleanup

# テスト失敗環境（PM級問題があるためまだ Green ではない）
FAKE_DIR=$(mktemp -d)
TEMP_FILES+=("${FAKE_DIR}")
cat > "${FAKE_DIR}/Makefile" << 'MAKEFILE'
test:
	@exit 1
MAKEFILE

cat > "${STATE_FILE}" << 'STATE'
{
  "active": true,
  "command": "full-review",
  "target": "src/",
  "iteration": 1,
  "max_iterations": 5,
  "started_at": "2026-03-08T10:00:00Z",
  "log": [
    {"iteration": 0, "issues_found": 5, "issues_fixed": 3, "pg": 2, "se": 1, "pm": 2}
  ]
}
STATE

# PM級検出メッセージ（full-review Phase 2 がこのメッセージで応答を終了する想定）
INPUT="{\"session_id\":\"test\",\"transcript_path\":\"/tmp/t\",\"cwd\":\"${FAKE_DIR}\",\"permission_mode\":\"default\",\"hook_event_name\":\"Stop\",\"stop_hook_active\":false,\"last_assistant_message\":\"PM級の問題が2件検出されました。ループを停止してエスカレーションします。\"}"

actual_stdout=$(echo "${INPUT}" | bash "${HOOK}" 2>/dev/null)
actual_exit=$?

# テスト失敗なので block で継続するが、PM級エスカレーションは Claude 側の判断
# Stop hook 自体は Green State 未達 → block（継続）を返す
assert_exit "exit 0" 0 "${actual_exit}"
assert_stdout_contains "decision:block を返す（テスト未通過）" "block" "${actual_stdout}"

rm -rf "${FAKE_DIR}" 2>/dev/null || true

# --- S-2-2: active=false の場合 → 停止 ---
echo ""
echo "S-2-2: active=false → ループ無効で停止"

cleanup

cat > "${STATE_FILE}" << 'STATE'
{
  "active": false,
  "command": "full-review",
  "target": "src/",
  "iteration": 1,
  "max_iterations": 5,
  "started_at": "2026-03-08T10:00:00Z",
  "log": []
}
STATE

INPUT='{"session_id":"test","transcript_path":"/tmp/t","cwd":"/tmp","permission_mode":"default","hook_event_name":"Stop","stop_hook_active":false,"last_assistant_message":"done"}'

actual_stdout=$(echo "${INPUT}" | bash "${HOOK}" 2>/dev/null)
actual_exit=$?

assert_exit "exit 0 (active=false → 停止)" 0 "${actual_exit}"
assert_stdout_empty "stdout empty (active=false)" "${actual_stdout}"

# ================================================================
# S-3: 上限到達停止 シミュレーション
# max_iterations に到達 → 強制停止
# ================================================================
echo ""
echo "=== S-3: 上限到達停止 シミュレーション ==="
echo ""

echo "S-3-1: iteration=4, max_iterations=5 → まだ継続可能"

cleanup

FAKE_DIR=$(mktemp -d)
TEMP_FILES+=("${FAKE_DIR}")
cat > "${FAKE_DIR}/Makefile" << 'MAKEFILE'
test:
	@exit 1
MAKEFILE

cat > "${STATE_FILE}" << 'STATE'
{
  "active": true,
  "command": "full-review",
  "target": "src/",
  "iteration": 4,
  "max_iterations": 5,
  "started_at": "2026-03-08T10:00:00Z",
  "log": [
    {"iteration": 0, "issues_found": 10, "issues_fixed": 8, "pg": 5, "se": 3, "pm": 0},
    {"iteration": 1, "issues_found": 5, "issues_fixed": 4, "pg": 3, "se": 1, "pm": 0},
    {"iteration": 2, "issues_found": 3, "issues_fixed": 2, "pg": 1, "se": 1, "pm": 0},
    {"iteration": 3, "issues_found": 2, "issues_fixed": 1, "pg": 1, "se": 0, "pm": 0}
  ]
}
STATE

INPUT="{\"session_id\":\"test\",\"transcript_path\":\"/tmp/t\",\"cwd\":\"${FAKE_DIR}\",\"permission_mode\":\"default\",\"hook_event_name\":\"Stop\",\"stop_hook_active\":false,\"last_assistant_message\":\"Green State 未達。残 Issue: 1件\"}"

actual_stdout=$(echo "${INPUT}" | bash "${HOOK}" 2>/dev/null)
actual_exit=$?

assert_exit "exit 0" 0 "${actual_exit}"
assert_stdout_contains "block で継続（まだ上限未到達）" "block" "${actual_stdout}"

rm -rf "${FAKE_DIR}" 2>/dev/null || true

# --- S-3-2: iteration=5 (== max_iterations) → 強制停止 ---
echo ""
echo "S-3-2: iteration=5 == max_iterations=5 → 強制停止"

cleanup

cat > "${STATE_FILE}" << 'STATE'
{
  "active": true,
  "command": "full-review",
  "target": "src/",
  "iteration": 5,
  "max_iterations": 5,
  "started_at": "2026-03-08T10:00:00Z",
  "log": [
    {"iteration": 0, "issues_found": 10, "issues_fixed": 8, "pg": 5, "se": 3, "pm": 0},
    {"iteration": 1, "issues_found": 5, "issues_fixed": 4, "pg": 3, "se": 1, "pm": 0},
    {"iteration": 2, "issues_found": 3, "issues_fixed": 2, "pg": 1, "se": 1, "pm": 0},
    {"iteration": 3, "issues_found": 2, "issues_fixed": 1, "pg": 1, "se": 0, "pm": 0},
    {"iteration": 4, "issues_found": 1, "issues_fixed": 0, "pg": 0, "se": 1, "pm": 0}
  ]
}
STATE

INPUT='{"session_id":"test","transcript_path":"/tmp/t","cwd":"/tmp","permission_mode":"default","hook_event_name":"Stop","stop_hook_active":false,"last_assistant_message":"Green State 未達。残 Issue: 1件"}'

actual_stdout=$(echo "${INPUT}" | bash "${HOOK}" 2>/dev/null)
actual_exit=$?

assert_exit "exit 0 (max_iterations 到達 → 停止)" 0 "${actual_exit}"
assert_stdout_empty "stdout empty (停止)" "${actual_stdout}"
assert_file_not_exists "状態ファイルが削除された" "${STATE_FILE}"

# ================================================================
# S-4: コンテキスト枯渇 シミュレーション
# PreCompact 発火 → 安全のためループ停止
# ================================================================
echo ""
echo "=== S-4: コンテキスト枯渇 → ループ停止 ==="
echo ""

echo "S-4-1: PreCompact フラグが直近 → ループ停止"

cleanup

cat > "${STATE_FILE}" << 'STATE'
{
  "active": true,
  "command": "full-review",
  "target": "src/",
  "iteration": 2,
  "max_iterations": 5,
  "started_at": "2026-03-08T10:00:00Z",
  "log": []
}
STATE

# 直近のタイムスタンプで pre-compact-fired を生成
date -u +"%Y-%m-%dT%H:%M:%SZ" > "${PRE_COMPACT_FLAG}"

INPUT='{"session_id":"test","transcript_path":"/tmp/t","cwd":"/tmp","permission_mode":"default","hook_event_name":"Stop","stop_hook_active":false,"last_assistant_message":"done"}'

actual_stdout=$(echo "${INPUT}" | bash "${HOOK}" 2>/dev/null)
actual_exit=$?

assert_exit "exit 0 (PreCompact → 停止)" 0 "${actual_exit}"
assert_stdout_empty "stdout empty (停止)" "${actual_stdout}"
assert_file_not_exists "状態ファイルが削除された" "${STATE_FILE}"

# ================================================================
# S-5: ループライフサイクル全体（初期化→複数サイクル→収束）
# ================================================================
echo ""
echo "=== S-5: ループライフサイクル全体 ==="
echo ""

echo "S-5-1: Phase 0 初期化 → サイクル1(失敗) → サイクル2(成功) の流れ"

cleanup

# Phase 0: 初期化（full-review.md の指示に従い状態ファイル生成）
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
cat > "${STATE_FILE}" << STATE
{
  "active": true,
  "command": "full-review",
  "target": "src/",
  "iteration": 0,
  "max_iterations": 5,
  "started_at": "${TIMESTAMP}",
  "log": []
}
STATE

assert_file_exists "Phase 0: 状態ファイル生成" "${STATE_FILE}"

# サイクル1: テスト失敗 → block で継続
FAKE_DIR=$(mktemp -d)
TEMP_FILES+=("${FAKE_DIR}")
cat > "${FAKE_DIR}/Makefile" << 'MAKEFILE'
test:
	@exit 1
MAKEFILE

INPUT="{\"session_id\":\"test\",\"transcript_path\":\"/tmp/t\",\"cwd\":\"${FAKE_DIR}\",\"permission_mode\":\"default\",\"hook_event_name\":\"Stop\",\"stop_hook_active\":false,\"last_assistant_message\":\"Green State 未達。残 Issue: 3件\"}"

actual_stdout=$(echo "${INPUT}" | bash "${HOOK}" 2>/dev/null)
actual_exit=$?

assert_exit "サイクル1: exit 0" 0 "${actual_exit}"
assert_stdout_contains "サイクル1: block で継続" "block" "${actual_stdout}"
assert_file_exists "サイクル1: 状態ファイルが残っている" "${STATE_FILE}"

# iteration が 1 にインクリメントされたか確認
if command -v jq >/dev/null 2>&1; then
  iter=$(jq '.iteration' "${STATE_FILE}" 2>/dev/null || echo "-1")
  if [ "${iter}" -eq 1 ]; then
    echo "  PASS: サイクル1: iteration 0→1"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: サイクル1: iteration が不正 (expected 1, got ${iter})"
    FAIL=$((FAIL + 1))
  fi
else
  echo "  SKIP: jq not available"
fi

# サイクル2: テスト成功環境に切り替え → Green State → 停止
cat > "${FAKE_DIR}/Makefile" << 'MAKEFILE'
test:
	@exit 0
lint:
	@exit 0
MAKEFILE

INPUT="{\"session_id\":\"test\",\"transcript_path\":\"/tmp/t\",\"cwd\":\"${FAKE_DIR}\",\"permission_mode\":\"default\",\"hook_event_name\":\"Stop\",\"stop_hook_active\":false,\"last_assistant_message\":\"Green State 達成。全修正完了。\"}"

actual_stdout=$(echo "${INPUT}" | bash "${HOOK}" 2>/dev/null)
actual_exit=$?

assert_exit "サイクル2: exit 0 (Green State → 停止)" 0 "${actual_exit}"
assert_stdout_empty "サイクル2: stdout empty (停止)" "${actual_stdout}"
assert_file_not_exists "サイクル2: 状態ファイル削除 (ループ終了)" "${STATE_FILE}"

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
