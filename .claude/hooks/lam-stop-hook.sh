#!/usr/bin/env bash
# LAM Stop hook: 自律ループの収束判定
# 設計書 Section 3.4 準拠
#
# 判定ロジック:
#   0. 再帰防止チェック（最優先）
#   1. 状態ファイル確認
#   2. 反復上限チェック
#   3. コンテキスト残量チェック（PreCompact 発火検出）
#   4. Green State 判定（テスト + lint）
#   5. エスカレーション条件チェック
#   6. 継続（block）
#
# 出力:
#   exit 0 のみ（hook 障害時のフォールバック対応）
#   継続時のみ stdout に {"decision": "block", "reason": "..."} を出力

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
STATE_FILE="${PROJECT_ROOT}/.claude/lam-loop-state.json"
PRE_COMPACT_FLAG="${PROJECT_ROOT}/.claude/pre-compact-fired"
LOG_FILE="${PROJECT_ROOT}/.claude/logs/loop.log"

# ログディレクトリが存在しなければ作成
mkdir -p "$(dirname "${LOG_FILE}")" 2>/dev/null || true

# 結果定数
RESULT_UNKNOWN=0
RESULT_PASS=1
RESULT_FAIL=2

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

log_entry() {
  local level="$1"
  local message="$2"
  echo "${TIMESTAMP}  ${level}  stop-hook  ${message}" >> "${LOG_FILE}" 2>/dev/null || true
}

# stdin から JSON を読み取る（エラー時は空文字列）
INPUT=$(cat 2>/dev/null || true)

# ================================================================
# jq ユーティリティ関数（jq が使えない環境のフォールバック）
# ================================================================

json_get_string() {
  local json="$1"
  local key="$2"
  if command -v jq >/dev/null 2>&1; then
    echo "${json}" | jq -r ".${key} // empty" 2>/dev/null || true
  else
    # フォールバック: Python3 または sed による簡易パース
    if command -v python3 >/dev/null 2>&1; then
      echo "${json}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('${key}',''))" 2>/dev/null || true
    else
      # 最終手段: sed（単純な文字列値のみ）
      echo "${json}" | sed -n "s/.*\"${key}\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -1 || true
    fi
  fi
}

json_get_number() {
  local json="$1"
  local key="$2"
  if command -v jq >/dev/null 2>&1; then
    echo "${json}" | jq -r ".${key} // 0" 2>/dev/null || echo "0"
  else
    if command -v python3 >/dev/null 2>&1; then
      echo "${json}" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('${key}',0))" 2>/dev/null || echo "0"
    else
      echo "${json}" | sed -n "s/.*\"${key}\"[[:space:]]*:[[:space:]]*\([0-9]*\).*/\1/p" | head -1 || echo "0"
    fi
  fi
}

json_get_bool() {
  local json="$1"
  local key="$2"
  local result
  if command -v jq >/dev/null 2>&1; then
    result=$(echo "${json}" | jq -r ".${key} // false" 2>/dev/null || echo "false")
  else
    if command -v python3 >/dev/null 2>&1; then
      result=$(echo "${json}" | python3 -c "import sys,json; d=json.load(sys.stdin); print('true' if d.get('${key}',False) else 'false')" 2>/dev/null || echo "false")
    else
      if echo "${json}" | grep -q "\"${key}\"[[:space:]]*:[[:space:]]*true" 2>/dev/null; then
        result="true"
      else
        result="false"
      fi
    fi
  fi
  echo "${result}"
}

# 状態ファイルの iteration をインクリメントして書き戻す
increment_iteration() {
  local current_iter="$1"
  local new_iter=$((current_iter + 1))

  if command -v jq >/dev/null 2>&1; then
    local tmp_file
    tmp_file=$(mktemp)
    if jq ".iteration = ${new_iter}" "${STATE_FILE}" > "${tmp_file}" 2>/dev/null; then
      mv "${tmp_file}" "${STATE_FILE}"
    else
      rm -f "${tmp_file}"
    fi
  elif command -v python3 >/dev/null 2>&1; then
    python3 - "${STATE_FILE}" "${new_iter}" << 'PYEOF'
import sys, json
path, new_iter = sys.argv[1], int(sys.argv[2])
with open(path) as f:
    d = json.load(f)
d['iteration'] = new_iter
with open(path, 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
PYEOF
  else
    # フォールバック: sed による単純置換（整数のみ対応）
    sed -i "s/\"iteration\"[[:space:]]*:[[:space:]]*${current_iter}/\"iteration\": ${new_iter}/" "${STATE_FILE}" 2>/dev/null || true
  fi
}

# ================================================================
# STEP 0: 再帰防止チェック（最優先）(AC-2.8c)
# ================================================================
STOP_HOOK_ACTIVE=$(json_get_bool "${INPUT}" "stop_hook_active")

if [ "${STOP_HOOK_ACTIVE}" = "true" ]; then
  # 再帰防止: Stop hook が発動させたセッション内では常に終了
  log_entry "INFO" "stop_hook_active=true → recursion guard exit"
  exit 0
fi

# ================================================================
# STEP 1: 状態ファイル確認 (AC-2.5)
# ================================================================
if [ ! -f "${STATE_FILE}" ]; then
  log_entry "INFO" "no state file → normal stop"
  exit 0
fi

# 状態ファイルの内容を読み取る
STATE_JSON=$(cat "${STATE_FILE}" 2>/dev/null || echo '{}')

# active フラグ確認 — false ならループ無効
ACTIVE=$(json_get_bool "${STATE_JSON}" "active")
if [ "${ACTIVE}" != "true" ]; then
  log_entry "INFO" "active=false → loop disabled, normal stop"
  exit 0
fi

ITERATION=$(json_get_number "${STATE_JSON}" "iteration")
MAX_ITERATIONS=$(json_get_number "${STATE_JSON}" "max_iterations")
COMMAND=$(json_get_string "${STATE_JSON}" "command")

log_entry "INFO" "loop active: command=${COMMAND}, iteration=${ITERATION}/${MAX_ITERATIONS}"

# ================================================================
# STEP 2: 反復上限チェック (AC-2.6)
# ================================================================
if [ "${ITERATION}" -ge "${MAX_ITERATIONS}" ]; then
  log_entry "WARN" "max_iterations reached (${ITERATION}/${MAX_ITERATIONS}) → stop loop"
  rm -f "${STATE_FILE}" 2>/dev/null || true
  exit 0
fi

# ================================================================
# STEP 3: コンテキスト残量チェック (AC-2.7, AC-2.11a)
# ================================================================
# PreCompact 発火フラグのタイムスタンプを確認する
# 直近10分以内に PreCompact が発火していた場合、コンテキスト圧迫と判断
PRE_COMPACT_THRESHOLD_SECONDS=600

if [ -f "${PRE_COMPACT_FLAG}" ]; then
  FLAG_CONTENT=$(cat "${PRE_COMPACT_FLAG}" 2>/dev/null || true)
  FLAG_EPOCH=0

  # タイムスタンプ文字列をエポック秒に変換
  if command -v date >/dev/null 2>&1; then
    # GNU date と BSD date の両方に対応
    if date -d "${FLAG_CONTENT}" +%s >/dev/null 2>&1; then
      # GNU date
      FLAG_EPOCH=$(date -d "${FLAG_CONTENT}" +%s 2>/dev/null || echo "0")
    elif date -j -f "%Y-%m-%dT%H:%M:%SZ" "${FLAG_CONTENT}" +%s >/dev/null 2>&1; then
      # BSD date
      FLAG_EPOCH=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "${FLAG_CONTENT}" +%s 2>/dev/null || echo "0")
    else
      # フォールバック: ファイルの mtime を使用
      FLAG_EPOCH=$(stat -c %Y "${PRE_COMPACT_FLAG}" 2>/dev/null || stat -f %m "${PRE_COMPACT_FLAG}" 2>/dev/null || echo "0")
    fi
  fi

  CURRENT_EPOCH=$(date +%s 2>/dev/null || echo "0")
  ELAPSED=$(( CURRENT_EPOCH - FLAG_EPOCH ))

  if [ "${FLAG_EPOCH}" -gt 0 ] && [ "${ELAPSED}" -le "${PRE_COMPACT_THRESHOLD_SECONDS}" ]; then
    log_entry "WARN" "PreCompact fired ${ELAPSED}s ago → context pressure, stop loop"
    rm -f "${STATE_FILE}" 2>/dev/null || true
    exit 0
  fi
fi

# ================================================================
# STEP 4: Green State 判定 (AC-2.8, AC-2.8a, AC-2.8b)
# ================================================================

# テストフレームワーク・lint ツールの検出先 (入力JSONの cwd か PROJECT_ROOT)
CWD=$(json_get_string "${INPUT}" "cwd")
CHECK_DIR="${CWD:-${PROJECT_ROOT}}"

TEST_PASS=${RESULT_UNKNOWN}
LINT_PASS=${RESULT_UNKNOWN}
TEST_COUNT=0  # 現在のテスト数

# -- G1: テストフレームワーク自動検出と実行 (AC-2.8a) --
detect_and_run_tests() {
  local dir="$1"
  local test_cmd=""
  local test_framework=""

  # 検出順序（green-state-definition.md 3.1 準拠）
  if [ -f "${dir}/pyproject.toml" ]; then
    if grep -qE '\[tool\.pytest|pytest' "${dir}/pyproject.toml" 2>/dev/null; then
      test_cmd="pytest"
      test_framework="pytest"
    fi
  fi

  if [ -z "${test_cmd}" ] && [ -f "${dir}/package.json" ]; then
    if grep -q '"test"' "${dir}/package.json" 2>/dev/null; then
      test_cmd="npm test"
      test_framework="npm"
    fi
  fi

  if [ -z "${test_cmd}" ] && [ -f "${dir}/go.mod" ]; then
    test_cmd="go test ./..."
    test_framework="go"
  fi

  if [ -z "${test_cmd}" ] && [ -f "${dir}/Makefile" ]; then
    if grep -q '^test:' "${dir}/Makefile" 2>/dev/null || grep -q '^test ' "${dir}/Makefile" 2>/dev/null; then
      test_cmd="make test"
      test_framework="make"
    fi
  fi

  if [ -z "${test_cmd}" ]; then
    log_entry "INFO" "G1: no test framework found in ${dir} → PASS (skip)"
    TEST_PASS=${RESULT_PASS}
    return
  fi

  log_entry "INFO" "G1: running ${test_framework}: ${test_cmd}"

  # timeout 120秒でテストを実行 (AC-2.8b)
  local test_output
  local test_exit=0
  test_output=$(cd "${dir}" && timeout 120 bash -c "${test_cmd}" 2>&1) || test_exit=$?

  if [ "${test_exit}" -eq 0 ]; then
    log_entry "INFO" "G1: tests PASSED (${test_framework})"
    TEST_PASS=${RESULT_PASS}

    # テスト数の抽出（エスカレーション条件チェック用）
    case "${test_framework}" in
      pytest)
        TEST_COUNT=$(echo "${test_output}" | grep -oE '[0-9]+ passed' | grep -oE '[0-9]+' | tail -1 || echo "0")
        ;;
      npm)
        TEST_COUNT=$(echo "${test_output}" | grep -oE 'Tests:[[:space:]]*[0-9]+ passed' | grep -oE '[0-9]+' | head -1 || echo "0")
        ;;
      go)
        TEST_COUNT=$(echo "${test_output}" | grep -c '^ok' 2>/dev/null || echo "0")
        ;;
    esac
    TEST_COUNT=${TEST_COUNT:-0}
  elif [ "${test_exit}" -eq 124 ]; then
    log_entry "WARN" "G1: test timeout (120s) → FAIL"
    TEST_PASS=${RESULT_FAIL}
  else
    log_entry "INFO" "G1: tests FAILED (exit ${test_exit})"
    TEST_PASS=${RESULT_FAIL}
  fi
}

# -- G2: lint ツール自動検出と実行 (AC-2.8a) --
detect_and_run_lint() {
  local dir="$1"
  local lint_cmd=""
  local lint_tool=""

  # 検出順序（green-state-definition.md 3.2 準拠）
  if [ -f "${dir}/pyproject.toml" ]; then
    if grep -qE '\[tool\.ruff|ruff' "${dir}/pyproject.toml" 2>/dev/null; then
      lint_cmd="ruff check ."
      lint_tool="ruff"
    fi
  fi

  if [ -z "${lint_cmd}" ] && [ -f "${dir}/package.json" ]; then
    if grep -q '"lint"' "${dir}/package.json" 2>/dev/null; then
      lint_cmd="npm run lint"
      lint_tool="npm-lint"
    fi
  fi

  if [ -z "${lint_cmd}" ]; then
    # .eslintrc* の検索
    local eslint_file
    eslint_file=$(find "${dir}" -maxdepth 1 -name '.eslintrc*' 2>/dev/null | head -1 || true)
    if [ -n "${eslint_file}" ]; then
      lint_cmd="npx eslint ."
      lint_tool="eslint"
    fi
  fi

  if [ -z "${lint_cmd}" ] && [ -f "${dir}/Makefile" ]; then
    if grep -q '^lint:' "${dir}/Makefile" 2>/dev/null || grep -q '^lint ' "${dir}/Makefile" 2>/dev/null; then
      lint_cmd="make lint"
      lint_tool="make"
    fi
  fi

  if [ -z "${lint_cmd}" ]; then
    log_entry "INFO" "G2: no lint tool found in ${dir} → PASS (skip)"
    LINT_PASS=${RESULT_PASS}
    return
  fi

  log_entry "INFO" "G2: running ${lint_tool}: ${lint_cmd}"

  # timeout 60秒で lint を実行 (AC-2.8b)
  local lint_exit=0
  (cd "${dir}" && timeout 60 bash -c "${lint_cmd}" > /dev/null 2>&1) || lint_exit=$?

  if [ "${lint_exit}" -eq 0 ]; then
    log_entry "INFO" "G2: lint PASSED (${lint_tool})"
    LINT_PASS=${RESULT_PASS}
  elif [ "${lint_exit}" -eq 124 ]; then
    log_entry "WARN" "G2: lint timeout (60s) → FAIL"
    LINT_PASS=${RESULT_FAIL}
  else
    log_entry "INFO" "G2: lint FAILED (exit ${lint_exit})"
    LINT_PASS=${RESULT_FAIL}
  fi
}

detect_and_run_tests "${CHECK_DIR}"
detect_and_run_lint "${CHECK_DIR}"

# -- G5: セキュリティチェック (依存脆弱性 + シークレットスキャン) --
SECURITY_PASS=${RESULT_UNKNOWN}

detect_and_run_security() {
  local dir="$1"
  local sec_fail=0

  # 依存脆弱性チェック: npm audit / pip audit を自動検出
  if [ -f "${dir}/package-lock.json" ] || [ -f "${dir}/package.json" ]; then
    if command -v npm >/dev/null 2>&1; then
      log_entry "INFO" "G5: running npm audit"
      local audit_output
      audit_output=$(cd "${dir}" && timeout 60 npm audit --audit-level=critical 2>&1) || {
        local audit_exit=$?
        if [ "${audit_exit}" -ne 124 ]; then
          log_entry "INFO" "G5: npm audit found critical vulnerabilities"
          sec_fail=1
        else
          log_entry "WARN" "G5: npm audit timeout (60s)"
        fi
      }
    fi
  elif [ -f "${dir}/pyproject.toml" ] || [ -f "${dir}/requirements.txt" ]; then
    if command -v pip-audit >/dev/null 2>&1; then
      log_entry "INFO" "G5: running pip-audit"
      (cd "${dir}" && timeout 60 pip-audit --desc 2>/dev/null) || {
        local audit_exit=$?
        if [ "${audit_exit}" -ne 124 ] && [ "${audit_exit}" -ne 0 ]; then
          log_entry "INFO" "G5: pip-audit found vulnerabilities"
          sec_fail=1
        fi
      }
    elif command -v safety >/dev/null 2>&1; then
      log_entry "INFO" "G5: running safety check"
      (cd "${dir}" && timeout 60 safety check 2>/dev/null) || {
        local audit_exit=$?
        if [ "${audit_exit}" -ne 124 ] && [ "${audit_exit}" -ne 0 ]; then
          log_entry "INFO" "G5: safety check found vulnerabilities"
          sec_fail=1
        fi
      }
    fi
  fi

  # シークレットスキャン: 基本パターンのみ（高速）
  local secret_found=0
  if [ -d "${dir}/src" ]; then
    # API キー、パスワード、トークンのハードコードパターン検出
    secret_found=$(grep -rE \
      '(password|secret|api_key|apikey|token|private_key)\s*=\s*["\x27][^"\x27]{8,}' \
      "${dir}/src" 2>/dev/null | grep -vcE '(test|spec|mock|example|placeholder|TODO|FIXME|xxx|changeme)' 2>/dev/null || echo "0")
  fi

  if [ "${secret_found:-0}" -gt 0 ]; then
    log_entry "WARN" "G5: potential secret leak detected in src/ (${secret_found} matches)"
    sec_fail=1
  fi

  if [ "${sec_fail}" -eq 0 ]; then
    log_entry "INFO" "G5: security checks PASSED"
    SECURITY_PASS=${RESULT_PASS}
  else
    log_entry "INFO" "G5: security checks FAILED"
    SECURITY_PASS=${RESULT_FAIL}
  fi
}

detect_and_run_security "${CHECK_DIR}"

# ================================================================
# STEP 5: エスカレーション条件チェック (AC-2.9)
# ================================================================

# 前サイクルのテスト数を取得（log の最後のエントリから）
PREV_TEST_COUNT=0
if command -v jq >/dev/null 2>&1; then
  LOG_LEN=$(echo "${STATE_JSON}" | jq '.log | length' 2>/dev/null || echo "0")
  if [ "${LOG_LEN}" -gt 0 ]; then
    PREV_TEST_COUNT=$(echo "${STATE_JSON}" | jq -r '.log[-1].test_count // 0' 2>/dev/null || echo "0")
  fi
elif command -v python3 >/dev/null 2>&1; then
  PREV_TEST_COUNT=$(echo "${STATE_JSON}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
log = d.get('log', [])
if log:
    print(log[-1].get('test_count', 0))
else:
    print(0)
" 2>/dev/null || echo "0")
fi

# テスト数減少チェック
if [ "${PREV_TEST_COUNT}" -gt 0 ] && [ "${TEST_COUNT}" -gt 0 ] && [ "${TEST_COUNT}" -lt "${PREV_TEST_COUNT}" ]; then
  log_entry "WARN" "ESC: test count decreased (${PREV_TEST_COUNT} → ${TEST_COUNT}) → escalate to human"
  rm -f "${STATE_FILE}" 2>/dev/null || true
  exit 0
fi

# 同一 Issue 再発チェック（前サイクルで issues_found があり、かつ今回も何も解決されていないケース）
# MVP では: 前サイクルで issues_found > 0 かつ issues_fixed == 0 が連続した場合にエスカレーション
check_issue_recurrence() {
  local last_found=0 last_fixed=0 prev_found=0 prev_fixed=0
  local log_len=0

  if command -v jq >/dev/null 2>&1; then
    log_len=$(echo "${STATE_JSON}" | jq '.log | length' 2>/dev/null || echo "0")
    if [ "${log_len}" -ge 2 ]; then
      last_found=$(echo "${STATE_JSON}" | jq -r '.log[-1].issues_found // 0' 2>/dev/null || echo "0")
      last_fixed=$(echo "${STATE_JSON}" | jq -r '.log[-1].issues_fixed // 0' 2>/dev/null || echo "0")
      prev_found=$(echo "${STATE_JSON}" | jq -r '.log[-2].issues_found // 0' 2>/dev/null || echo "0")
      prev_fixed=$(echo "${STATE_JSON}" | jq -r '.log[-2].issues_fixed // 0' 2>/dev/null || echo "0")
    fi
  elif command -v python3 >/dev/null 2>&1; then
    # eval を使わず、python3 出力を個別に安全に読み取る（インジェクション防止）
    PY_OUTPUT=$(echo "${STATE_JSON}" | python3 -c "
import sys, json
d = json.load(sys.stdin)
log = d.get('log', [])
if len(log) >= 2:
    # 整数値のみ出力（改行区切り）
    print(len(log))
    print(int(log[-1].get('issues_found', 0)))
    print(int(log[-1].get('issues_fixed', 0)))
    print(int(log[-2].get('issues_found', 0)))
    print(int(log[-2].get('issues_fixed', 0)))
else:
    print(0)
" 2>/dev/null || echo "0")
    # 出力を行ごとに読み取り、整数として検証
    IFS=$'\n' read -r -d '' py_log_len py_lf py_lfx py_pf py_pfx <<< "${PY_OUTPUT}" || true
    if [[ "${py_log_len:-0}" =~ ^[0-9]+$ ]]; then
      log_len="${py_log_len}"
      last_found="${py_lf:-0}"
      last_fixed="${py_lfx:-0}"
      prev_found="${py_pf:-0}"
      prev_fixed="${py_pfx:-0}"
    fi
  else
    log_entry "WARN" "ESC: jq/python3 unavailable, skipping recurrence check"
    return 1
  fi

  if [ "${log_len}" -ge 2 ] && \
     [ "${last_found}" -gt 0 ] && [ "${last_fixed}" -eq 0 ] && \
     [ "${prev_found}" -gt 0 ] && [ "${prev_fixed}" -eq 0 ]; then
    return 0  # recurrence detected
  fi
  return 1
}

if check_issue_recurrence; then
  log_entry "WARN" "ESC: same issues recurring (no fix for 2 cycles) → escalate to human"
  rm -f "${STATE_FILE}" 2>/dev/null || true
  exit 0
fi

# ================================================================
# STEP 5b: Green State 条件の総合判定
# ================================================================

GREEN_STATE=0
FAIL_REASON=""

if [ "${TEST_PASS}" -eq "${RESULT_FAIL}" ]; then
  FAIL_REASON="テスト失敗"
elif [ "${LINT_PASS}" -eq "${RESULT_FAIL}" ]; then
  FAIL_REASON="lint 失敗"
elif [ "${SECURITY_PASS}" -eq "${RESULT_FAIL}" ]; then
  FAIL_REASON="セキュリティチェック失敗"
else
  GREEN_STATE=1
fi

if [ "${GREEN_STATE}" -eq 1 ]; then
  # Green State 達成 → フルスキャン確認
  FULLSCAN_PENDING=0
  if command -v jq >/dev/null 2>&1; then
    FS=$(echo "${STATE_JSON}" | jq -r '.fullscan_pending // false' 2>/dev/null || echo "false")
    if [ "${FS}" = "true" ]; then
      FULLSCAN_PENDING=1
    fi
  elif command -v python3 >/dev/null 2>&1; then
    FS=$(echo "${STATE_JSON}" | python3 -c "import sys,json;d=json.load(sys.stdin);print('true' if d.get('fullscan_pending') else 'false')" 2>/dev/null || echo "false")
    if [ "${FS}" = "true" ]; then
      FULLSCAN_PENDING=1
    fi
  fi

  if [ "${FULLSCAN_PENDING}" -eq 1 ]; then
    log_entry "INFO" "Green State achieved, fullscan_pending=true → clear flag, continue"
    # フルスキャン済みフラグを解除して継続
    if command -v jq >/dev/null 2>&1; then
      FULLSCAN_TMP=$(mktemp)
      if jq '.fullscan_pending = false' "${STATE_FILE}" > "${FULLSCAN_TMP}" 2>/dev/null; then
        mv "${FULLSCAN_TMP}" "${STATE_FILE}"
      else
        rm -f "${FULLSCAN_TMP}"
      fi
    fi
  else
    log_entry "INFO" "Green State achieved → stop loop (normal convergence)"
    rm -f "${STATE_FILE}" 2>/dev/null || true
    exit 0
  fi
fi

# ================================================================
# STEP 6: 継続（block）(AC-2.10)
# ================================================================

NEW_ITERATION=$((ITERATION + 1))
increment_iteration "${ITERATION}"

log_entry "INFO" "continuing: iteration ${ITERATION} → ${NEW_ITERATION}, reason=${FAIL_REASON:-Green State 未達}"

# テスト数を状態ファイルの最新ログエントリに記録（エスカレーション判定用）
if [ "${TEST_COUNT}" -gt 0 ] && command -v jq >/dev/null 2>&1; then
  COUNT_TMP=$(mktemp)
  if jq ".log[-1].test_count = ${TEST_COUNT}" "${STATE_FILE}" > "${COUNT_TMP}" 2>/dev/null; then
    mv "${COUNT_TMP}" "${STATE_FILE}"
  else
    rm -f "${COUNT_TMP}"
  fi
fi

REMAINING_MSG="${FAIL_REASON:-Green State 未達}"
FAIL_PARTS=""
[ "${TEST_PASS}" -eq "${RESULT_FAIL}" ] && FAIL_PARTS="テスト失敗"
[ "${LINT_PASS}" -eq "${RESULT_FAIL}" ] && FAIL_PARTS="${FAIL_PARTS:+${FAIL_PARTS} + }lint 失敗"
[ "${SECURITY_PASS}" -eq "${RESULT_FAIL}" ] && FAIL_PARTS="${FAIL_PARTS:+${FAIL_PARTS} + }セキュリティ失敗"
if [ -n "${FAIL_PARTS}" ]; then
  REMAINING_MSG="${FAIL_PARTS}"
fi

REASON="Green State 未達。サイクル ${NEW_ITERATION} を開始。残Issue: ${REMAINING_MSG}"

# decision:block を stdout に出力（Stop hook の継続シグナル）(AC-2.10)
if command -v jq >/dev/null 2>&1; then
  jq -n --arg reason "${REASON}" '{"decision": "block", "reason": $reason}'
else
  SAFE_REASON=$(echo "${REASON}" | tr -d '"')
  echo "{\"decision\": \"block\", \"reason\": \"${SAFE_REASON}\"}"
fi

exit 0
