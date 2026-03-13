"""
_hook_utils.py - フックスクリプト共通ユーティリティ

bash 版で各フックに重複していた処理を集約する。
標準ライブラリのみ使用（外部パッケージ不要）。

対応仕様: design.md Section 2
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time

# exponential backoff: 最大3回リトライ (100ms / 200ms / 400ms)
_ATOMIC_WRITE_RETRY_DELAYS: tuple[float, ...] = (0.1, 0.2, 0.4)


def now_utc_iso8601() -> str:
    """UTC の ISO 8601 タイムスタンプ文字列を返す。"""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_project_root() -> pathlib.Path:
    """
    プロジェクトルートの Path を返す。

    テスト用: 環境変数 LAM_PROJECT_ROOT が設定されていればそちらを優先。
    通常: __file__ から ../../ を辿って PROJECT_ROOT を取得
          (.claude/hooks/_hook_utils.py -> .claude/hooks/ -> .claude/ -> PROJECT_ROOT)
    """
    env_root = os.environ.get("LAM_PROJECT_ROOT")
    if env_root:
        resolved = pathlib.Path(env_root).resolve()
        if resolved.is_dir():
            return resolved
        # テスト用変数が不正なパスの場合はフォールバック
    # __file__ は .claude/hooks/_hook_utils.py
    # parent   -> .claude/hooks/
    # parent.parent -> .claude/
    # parent.parent.parent -> PROJECT_ROOT
    return pathlib.Path(__file__).resolve().parent.parent.parent


def read_stdin_json() -> dict:
    """
    stdin から JSON を読み取って dict を返す。
    失敗時（不正 JSON、空入力）は空 dict を返す。
    """
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError, OSError):
        return {}


def get_tool_name(data: dict) -> str:
    """data["tool_name"] を返す。存在しない場合は空文字。"""
    return data.get("tool_name", "")


def get_tool_input(data: dict, key: str) -> str:
    """
    data["tool_input"][key] を返す。
    tool_input またはキーが存在しない場合は空文字。
    """
    tool_input = data.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return ""
    return tool_input.get(key, "")


def get_tool_response(data: dict, key: str, default: object):
    """
    data["tool_response"][key] を返す。
    tool_response またはキーが存在しない場合は default を返す。
    """
    tool_response = data.get("tool_response", {})
    if not isinstance(tool_response, dict):
        return default
    return tool_response.get(key, default)


def normalize_path(file_path: str, project_root: pathlib.Path) -> str:
    """
    絶対パスを project_root からの相対パスに変換する。
    すでに相対パスの場合はそのまま返す。
    返却値は文字列（スラッシュ区切り）。
    """
    p = pathlib.Path(file_path)
    if not p.is_absolute():
        return file_path
    try:
        relative = p.relative_to(project_root)
        return str(relative)
    except ValueError:
        # project_root の外のパスは out-of-root マーカー付きで返す
        # pre-tool-use.py のパターンマッチで PM級として捕捉される
        return f"__out_of_root__/{file_path}"


def log_entry(log_file: pathlib.Path, level: str, source: str, message: str):
    """
    TSV 形式でログを追記する。

    形式: timestamp\tlevel\tsource\tmessage
    タイムスタンプは UTC ISO 8601 形式。
    """
    timestamp = now_utc_iso8601()
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8", newline="\n") as f:
        f.write(f"{timestamp}\t{level}\t{source}\t{message}\n")


def atomic_write_json(path: pathlib.Path, data: dict):
    """
    JSON データをアトミックに書き込む。

    tempfile + os.replace によるアトミック書き込み。
    tempfile の dir= に対象ファイルと同ディレクトリを指定（クロスデバイス回避）。
    Windows での PermissionError は exponential backoff で retry (3回, 100ms/200ms/400ms)。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    json_bytes = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")

    max_attempts = len(_ATOMIC_WRITE_RETRY_DELAYS) + 1
    # 全リトライ失敗時のフォールバック（通常到達しない）
    last_error: Exception | None = None

    for attempt in range(max_attempts):
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(json_bytes)
            os.replace(tmp_path, path)
            return
        except PermissionError as e:
            last_error = e
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            if attempt < len(_ATOMIC_WRITE_RETRY_DELAYS):
                time.sleep(_ATOMIC_WRITE_RETRY_DELAYS[attempt])
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    raise last_error if last_error else RuntimeError("atomic_write_json: all retries exhausted")


def run_command(args: list[str], cwd: str, timeout: int) -> tuple[int, str, str]:
    """
    subprocess.run のラッパー。

    - shutil.which() でコマンドを解決する
    - shell=False 固定
    - timeout は subprocess パラメータで制御
    - 戻り値: (exit_code, stdout, stderr)
    """
    if not args:
        return (1, "", "no command specified")

    resolved = shutil.which(args[0])
    if resolved is None:
        return (1, "", f"command not found: {args[0]}")

    cmd = [resolved] + list(args[1:])
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )
        return (result.returncode, result.stdout, result.stderr)
    except subprocess.TimeoutExpired:
        return (1, "", f"command timed out after {timeout}s: {args[0]}")
    except Exception as e:
        return (1, "", str(e))


def safe_exit(code: int = 0):
    """sys.exit のラッパー。"""
    sys.exit(code)
