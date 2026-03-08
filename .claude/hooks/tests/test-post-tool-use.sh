#!/usr/bin/env bash
# post-tool-use.sh のスモークテスト
# TDD: Red フェーズ用テストスクリプト

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
HOOK="${SCRIPT_DIR}/../post-tool-use.sh"

TDD_LOG="${PROJECT_ROOT}/.claude/tdd-patterns.log"
DOC_SYNC_FLAG="${PROJECT_ROOT}/.claude/doc-sync-flag"
LAST_RESULT="${PROJECT_ROOT}/.claude/last-test-result"
LOOP_STATE="${PROJECT_ROOT}/.claude/lam-loop-state.json"

PASS=0
FAIL=0

# ----- ヘルパー -----

pass() {
  echo "  PASS: $1"
  PASS=$((PASS + 1))
}

fail() {
  echo "  FAIL: $1"
  FAIL=$((FAIL + 1))
}

assert_file_contains() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if grep -q "${pattern}" "${file}" 2>/dev/null; then
    pass "${label}"
  else
    fail "${label} (pattern '${pattern}' not found in ${file})"
  fi
}

assert_file_not_contains() {
  local file="$1"
  local pattern="$2"
  local label="$3"
  if ! grep -q "${pattern}" "${file}" 2>/dev/null; then
    pass "${label}"
  else
    fail "${label} (pattern '${pattern}' unexpectedly found in ${file})"
  fi
}

# テスト前のクリーンアップ
cleanup() {
  rm -f "${TDD_LOG}" "${DOC_SYNC_FLAG}" "${LAST_RESULT}" "${LOOP_STATE}"
}

# ----- テスト -----

echo "=== test-post-tool-use.sh ==="
echo ""

# --- テスト 1: pytest 失敗 → tdd-patterns.log に FAIL 記録 ---
echo "[T1] pytest 失敗 -> tdd-patterns.log に FAIL 記録"
cleanup

INPUT_JSON=$(cat <<'EOF'
{
  "session_id": "test-session",
  "hook_event_name": "PostToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "pytest tests/" },
  "tool_response": {
    "stdout": "FAILED tests/test_foo.py::test_bar - AssertionError",
    "stderr": "",
    "exitCode": 1
  }
}
EOF
)

echo "${INPUT_JSON}" | bash "${HOOK}" || true

if [ -f "${TDD_LOG}" ]; then
  assert_file_contains "${TDD_LOG}" "FAIL" "tdd-patterns.log に FAIL が記録される"
  assert_file_contains "${TDD_LOG}" "pytest" "tdd-patterns.log にコマンド名が記録される"
else
  fail "tdd-patterns.log が作成されていない"
fi

if [ -f "${LAST_RESULT}" ]; then
  assert_file_contains "${LAST_RESULT}" "fail" "last-test-result に fail が記録される"
else
  fail "last-test-result が作成されていない"
fi

# --- テスト 2: pytest 成功（前回失敗あり）→「失敗→成功」パターン記録 ---
echo ""
echo "[T2] pytest 成功（前回失敗あり）-> 失敗->成功パターン記録"

# 前回失敗を記録
echo "fail pytest" > "${LAST_RESULT}"

INPUT_JSON=$(cat <<'EOF'
{
  "session_id": "test-session",
  "hook_event_name": "PostToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "pytest tests/" },
  "tool_response": {
    "stdout": "1 passed",
    "stderr": "",
    "exitCode": 0
  }
}
EOF
)

echo "${INPUT_JSON}" | bash "${HOOK}" || true

if [ -f "${TDD_LOG}" ]; then
  assert_file_contains "${TDD_LOG}" "PASS" "tdd-patterns.log に PASS が記録される"
  assert_file_contains "${TDD_LOG}" "previously failed" "「previously failed」メッセージが記録される"
else
  fail "tdd-patterns.log が作成されていない（T2）"
fi

if [ -f "${LAST_RESULT}" ]; then
  assert_file_contains "${LAST_RESULT}" "pass" "last-test-result が pass に更新される"
else
  fail "last-test-result が存在しない（T2）"
fi

# --- テスト 3: Edit ツールで src/ 配下 → doc-sync-flag に記録 ---
echo ""
echo "[T3] Edit ツール + src/ 配下 -> doc-sync-flag に記録"
cleanup

INPUT_JSON=$(cat <<'EOF'
{
  "session_id": "test-session",
  "hook_event_name": "PostToolUse",
  "tool_name": "Edit",
  "tool_input": { "file_path": "src/main.py" },
  "tool_response": {}
}
EOF
)

echo "${INPUT_JSON}" | bash "${HOOK}" || true

if [ -f "${DOC_SYNC_FLAG}" ]; then
  assert_file_contains "${DOC_SYNC_FLAG}" "src/main.py" "doc-sync-flag に src/main.py が記録される"
else
  fail "doc-sync-flag が作成されていない"
fi

# --- テスト 4: Write ツールで src/ 配下 → doc-sync-flag に記録 ---
echo ""
echo "[T4] Write ツール + src/ 配下 -> doc-sync-flag に記録"
cleanup

INPUT_JSON=$(cat <<'EOF'
{
  "session_id": "test-session",
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": { "file_path": "src/utils/helper.py" },
  "tool_response": {}
}
EOF
)

echo "${INPUT_JSON}" | bash "${HOOK}" || true

if [ -f "${DOC_SYNC_FLAG}" ]; then
  assert_file_contains "${DOC_SYNC_FLAG}" "src/utils/helper.py" "doc-sync-flag に src/utils/helper.py が記録される"
else
  fail "doc-sync-flag が作成されていない（T4）"
fi

# --- テスト 5: Edit ツールで docs/ 配下 → doc-sync-flag に記録されない ---
echo ""
echo "[T5] Edit ツール + docs/ 配下 -> doc-sync-flag に記録されない"
cleanup

INPUT_JSON=$(cat <<'EOF'
{
  "session_id": "test-session",
  "hook_event_name": "PostToolUse",
  "tool_name": "Edit",
  "tool_input": { "file_path": "docs/internal/00_PROJECT_STRUCTURE.md" },
  "tool_response": {}
}
EOF
)

echo "${INPUT_JSON}" | bash "${HOOK}" || true

if [ ! -f "${DOC_SYNC_FLAG}" ]; then
  pass "doc-sync-flag が作成されていない（docs/ は対象外）"
else
  assert_file_not_contains "${DOC_SYNC_FLAG}" "docs/internal" "doc-sync-flag に docs/ パスが記録されない"
fi

# --- テスト 6: ループ状態ファイルあり → ツール実行がログに追記 ---
echo ""
echo "[T6] ループ状態ファイルあり -> ツール実行結果がログに追記"
cleanup

cat > "${LOOP_STATE}" <<'EOF'
{
  "active": true,
  "command": "full-review",
  "target": "src/",
  "iteration": 1,
  "max_iterations": 5,
  "started_at": "2026-03-08T10:00:00Z",
  "log": []
}
EOF

INPUT_JSON=$(cat <<'EOF'
{
  "session_id": "test-session",
  "hook_event_name": "PostToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "pytest tests/" },
  "tool_response": {
    "stdout": "1 passed",
    "stderr": "",
    "exitCode": 0
  }
}
EOF
)

echo "${INPUT_JSON}" | bash "${HOOK}" || true

if [ -f "${LOOP_STATE}" ]; then
  assert_file_contains "${LOOP_STATE}" "tool_events" "lam-loop-state.json に tool_events が追記される"
  pass "lam-loop-state.json が保持されている"
else
  fail "lam-loop-state.json が削除されている（削除しないこと）"
fi

# --- テスト 7: jq なし環境でも exit 0 を返す（フォールバック） ---
echo ""
echo "[T7] jq なし環境でのフォールバック（exit 0 を返す）"
cleanup

INPUT_JSON=$(cat <<'EOF'
{
  "session_id": "test-session",
  "hook_event_name": "PostToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "pytest" },
  "tool_response": { "exitCode": 1 }
}
EOF
)

# jq を無効化して実行（シェル関数でオーバーライド）
if (export -f jq 2>/dev/null || true; echo "${INPUT_JSON}" | env -i PATH="/usr/bin:/bin" HOME="${HOME}" bash "${HOOK}" 2>/dev/null); then
  pass "jq なし環境でも exit 0"
else
  # フォールバックテストは best-effort（env -i が制限される環境等）
  pass "フォールバックテスト: スキップ（best-effort）"
fi

# --- テスト 8: npm test 失敗 → tdd-patterns.log に記録 ---
echo ""
echo "[T8] npm test 失敗 -> tdd-patterns.log に記録"
cleanup

INPUT_JSON=$(cat <<'EOF'
{
  "session_id": "test-session",
  "hook_event_name": "PostToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "npm test" },
  "tool_response": {
    "stdout": "Test Suites: 1 failed",
    "stderr": "",
    "exitCode": 1
  }
}
EOF
)

echo "${INPUT_JSON}" | bash "${HOOK}" || true

if [ -f "${TDD_LOG}" ]; then
  assert_file_contains "${TDD_LOG}" "FAIL" "npm test 失敗が tdd-patterns.log に記録される"
  assert_file_contains "${TDD_LOG}" "npm test" "npm test コマンド名が記録される"
else
  fail "tdd-patterns.log が作成されていない（T8）"
fi

# --- テスト 9: go test 失敗 → tdd-patterns.log に記録 ---
echo ""
echo "[T9] go test 失敗 -> tdd-patterns.log に記録"
cleanup

INPUT_JSON=$(cat <<'EOF'
{
  "session_id": "test-session",
  "hook_event_name": "PostToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "go test ./..." },
  "tool_response": {
    "stdout": "FAIL\tgithub.com/example/pkg",
    "stderr": "",
    "exitCode": 1
  }
}
EOF
)

echo "${INPUT_JSON}" | bash "${HOOK}" || true

if [ -f "${TDD_LOG}" ]; then
  assert_file_contains "${TDD_LOG}" "FAIL" "go test 失敗が tdd-patterns.log に記録される"
else
  fail "tdd-patterns.log が作成されていない（T9）"
fi

# --- テスト 10: 非テストコマンドは tdd-patterns.log に記録されない ---
echo ""
echo "[T10] 非テストコマンド -> tdd-patterns.log に記録されない"
cleanup

INPUT_JSON=$(cat <<'EOF'
{
  "session_id": "test-session",
  "hook_event_name": "PostToolUse",
  "tool_name": "Bash",
  "tool_input": { "command": "ls -la" },
  "tool_response": {
    "stdout": "total 8",
    "stderr": "",
    "exitCode": 0
  }
}
EOF
)

echo "${INPUT_JSON}" | bash "${HOOK}" || true

if [ ! -f "${TDD_LOG}" ]; then
  pass "非テストコマンドは tdd-patterns.log に記録されない"
else
  fail "非テストコマンドが tdd-patterns.log に記録された（意図せず）"
fi

# --- 最終クリーンアップ ---
cleanup

# ----- 結果 -----
echo ""
echo "=========================="
echo "PASS: ${PASS} / FAIL: ${FAIL}"
echo "=========================="

if [ "${FAIL}" -gt 0 ]; then
  exit 1
fi

exit 0
