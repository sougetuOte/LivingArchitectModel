#!/usr/bin/env bash
# テスト共通ヘルパー関数
# source で読み込んで使用する。
# 前提: 呼び出し元で PASS=0, FAIL=0 を初期化済みであること。

assert_exit() {
  local test_name="$1"
  local expected_exit="$2"
  local actual_exit="$3"

  if [ "${actual_exit}" -eq "${expected_exit}" ]; then
    echo "  PASS: ${test_name}"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: ${test_name} (expected exit ${expected_exit}, got ${actual_exit})"
    FAIL=$((FAIL + 1))
  fi
}

assert_stdout_contains() {
  local test_name="$1"
  local pattern="$2"
  local actual="$3"

  if echo "${actual}" | grep -q "${pattern}"; then
    echo "  PASS: ${test_name}"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: ${test_name} (expected pattern '${pattern}' in stdout)"
    echo "    actual: ${actual}"
    FAIL=$((FAIL + 1))
  fi
}

assert_stdout_empty() {
  local test_name="$1"
  local actual="$2"

  if [ -z "${actual}" ]; then
    echo "  PASS: ${test_name}"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: ${test_name} (expected empty stdout)"
    echo "    actual: ${actual}"
    FAIL=$((FAIL + 1))
  fi
}

assert_file_exists() {
  local test_name="$1"
  local file_path="$2"

  if [ -f "${file_path}" ]; then
    echo "  PASS: ${test_name}"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: ${test_name} (file not found: ${file_path})"
    FAIL=$((FAIL + 1))
  fi
}

assert_file_not_exists() {
  local test_name="$1"
  local file_path="$2"

  if [ ! -f "${file_path}" ]; then
    echo "  PASS: ${test_name}"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: ${test_name} (file should not exist: ${file_path})"
    FAIL=$((FAIL + 1))
  fi
}

assert_json_field() {
  local test_name="$1"
  local file_path="$2"
  local field="$3"

  if command -v jq >/dev/null 2>&1; then
    if jq -e ".${field}" "${file_path}" >/dev/null 2>&1; then
      echo "  PASS: ${test_name}"
      PASS=$((PASS + 1))
    else
      echo "  FAIL: ${test_name} (field '${field}' not found in ${file_path})"
      FAIL=$((FAIL + 1))
    fi
  else
    echo "  SKIP: ${test_name} (jq not available)"
  fi
}
