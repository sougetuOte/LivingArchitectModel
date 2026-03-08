#!/usr/bin/env bash
# PreToolUse hook のスモークテスト
# 実行: bash .claude/hooks/tests/test-pre-tool-use.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
HOOK="${PROJECT_ROOT}/.claude/hooks/pre-tool-use.sh"
LOG_FILE="${PROJECT_ROOT}/.claude/logs/permission.log"

PASS=0
FAIL=0
TOTAL=0

pass() { PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); echo "  FAIL: $1"; }

cleanup() {
  rm -f "${LOG_FILE}" 2>/dev/null || true
}

echo "=== PreToolUse hook smoke tests ==="
echo ""

# --- TC-1: shellcheck ---
echo "[TC-1] shellcheck"
if command -v shellcheck >/dev/null 2>&1; then
  if shellcheck -S warning "${HOOK}" 2>/dev/null; then
    pass "shellcheck passed"
  else
    fail "shellcheck warnings"
  fi
else
  pass "shellcheck not installed (skip)"
fi

# --- TC-2: 読み取り専用ツールは PG 許可 ---
echo ""
echo "[TC-2] Read tool -> PG allow (exit 0)"
cleanup

INPUT_JSON='{"tool_name":"Read","tool_input":{"file_path":"src/main.py"}}'
if echo "${INPUT_JSON}" | bash "${HOOK}" >/dev/null 2>&1; then
  pass "Read tool: exit 0"
else
  fail "Read tool: non-zero exit"
fi

# --- TC-3: PM 級パス (docs/specs/) -> deny ---
echo ""
echo "[TC-3] Edit docs/specs/foo.md -> PM deny"
cleanup

INPUT_JSON='{"tool_name":"Edit","tool_input":{"file_path":"docs/specs/foo.md","old_string":"a","new_string":"b"}}'
RESULT=$(echo "${INPUT_JSON}" | bash "${HOOK}" 2>/dev/null || true)

if echo "${RESULT}" | grep -q '"permissionDecision"[[:space:]]*:[[:space:]]*"deny"'; then
  pass "PM deny returned"
else
  fail "PM deny not returned: ${RESULT}"
fi

# hookEventName が含まれていないことを確認（最新仕様準拠）
if echo "${RESULT}" | grep -q 'hookEventName'; then
  fail "hookEventName should not be present in output"
else
  pass "hookEventName correctly absent"
fi

# --- TC-4: PM 級パス (.claude/rules/auto-generated/) -> deny ---
echo ""
echo "[TC-4] Edit .claude/rules/auto-generated/draft-001.md -> PM deny"
cleanup

INPUT_JSON='{"tool_name":"Edit","tool_input":{"file_path":".claude/rules/auto-generated/draft-001.md","old_string":"a","new_string":"b"}}'
RESULT=$(echo "${INPUT_JSON}" | bash "${HOOK}" 2>/dev/null || true)

if echo "${RESULT}" | grep -q '"permissionDecision"[[:space:]]*:[[:space:]]*"deny"'; then
  pass "rules/auto-generated/ PM deny returned"
else
  fail "rules/auto-generated/ not PM protected: ${RESULT}"
fi

# --- TC-5: 絶対パス正規化 ---
echo ""
echo "[TC-5] Absolute path docs/specs/ -> PM deny"
cleanup

INPUT_JSON="{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\"${PROJECT_ROOT}/docs/specs/test.md\",\"content\":\"test\"}}"
RESULT=$(echo "${INPUT_JSON}" | bash "${HOOK}" 2>/dev/null || true)

if echo "${RESULT}" | grep -q '"permissionDecision"[[:space:]]*:[[:space:]]*"deny"'; then
  pass "Absolute path PM deny returned"
else
  fail "Absolute path not PM protected: ${RESULT}"
fi

# --- TC-6: SE 級パス (src/) -> exit 0 ---
echo ""
echo "[TC-6] Edit src/main.py -> SE allow (exit 0)"
cleanup

INPUT_JSON='{"tool_name":"Edit","tool_input":{"file_path":"src/main.py","old_string":"a","new_string":"b"}}'
if echo "${INPUT_JSON}" | bash "${HOOK}" >/dev/null 2>&1; then
  pass "SE path: exit 0"
else
  fail "SE path: non-zero exit"
fi

# --- TC-7: ログトランケート ---
echo ""
echo "[TC-7] Log truncation (command > 100 chars)"
cleanup

LONG_CMD=$(printf 'echo "%0200d"' 0)
INPUT_JSON="{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"${LONG_CMD}\"}}"
echo "${INPUT_JSON}" | bash "${HOOK}" >/dev/null 2>&1 || true

if [ -f "${LOG_FILE}" ]; then
  LINE_LEN=$(awk '{if(length>max)max=length}END{print max+0}' "${LOG_FILE}" 2>/dev/null || echo "0")
  # 行の長さが妥当な範囲内か（トランケート込みで200文字以下を期待）
  if [ "${LINE_LEN}" -lt 250 ]; then
    pass "Log line length reasonable (${LINE_LEN} chars)"
  else
    fail "Log line too long (${LINE_LEN} chars)"
  fi
else
  fail "Log file not created"
fi

# --- 結果サマリー ---
echo ""
echo "=== Results: ${PASS} passed, ${FAIL} failed, ${TOTAL} total ==="

cleanup

if [ "${FAIL}" -gt 0 ]; then
  exit 1
fi
exit 0
