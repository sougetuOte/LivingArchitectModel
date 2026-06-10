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


# W-14: hook サブプロセスへ継承する環境変数の allowlist。
# 機密（AWS_SECRET_ACCESS_KEY / GITHUB_TOKEN 等）の漏出を防ぐ。
CHECKER_ENV_ALLOWLIST: tuple[str, ...] = (
    "PATH", "HOME", "LANG", "LC_ALL", "TERM",
    "TMPDIR", "TEMP", "TMP",
    "VIRTUAL_ENV", "CONDA_PREFIX",
    "PYTHONPATH", "PYTHONDONTWRITEBYTECODE",
    "LAM_PROJECT_ROOT",
    # Windows: pytest/checker 起動に必須のシステム変数
    "SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "COMSPEC",
    "USERPROFILE", "APPDATA", "LOCALAPPDATA",
    "PATHEXT", "PROCESSOR_ARCHITECTURE",
)


def build_allowlisted_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    """親 os.environ から CHECKER_ENV_ALLOWLIST のキーのみを抽出し、extra をマージして返す。

    W-14 対応: G1 checker 等のサブプロセスに機密環境変数を継承させないための共通ヘルパー。
    extra は最後にマージされるので、LAM_PROJECT_ROOT 等の上書きが可能。
    """
    env = {k: v for k, v in os.environ.items() if k in CHECKER_ENV_ALLOWLIST}
    if extra:
        env.update(extra)
    return env


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
        # テスト用変数が不正なパスの場合はフォールバック（握りつぶさずログに残す）
        sys.stderr.write(
            f"WARNING: LAM_PROJECT_ROOT is not a directory: {env_root!r}, "
            "falling back to __file__\n"
        )
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


def _normalize_relative_segments(file_path: str) -> tuple[str, bool]:
    """相対パスを字句的に正規化する（W-16・cwd 非依存・FS 非アクセス）。

    `.`/`..` をスタックで畳み込み、(正規化パス, 越境フラグ) を返す。
    越境フラグは先頭に `..` が残った（project_root を越えた）場合に True。
    FS にアクセスしないため cwd・実在性に依存せず、`..` を含まない通常パスは
    結果が不変（素通し契約の維持）。\\ は / に正規化してから処理する。
    """
    stack: list[str] = []
    escaped = False
    for seg in file_path.replace("\\", "/").split("/"):
        if seg in ("", "."):
            continue
        if seg == ".." and stack and stack[-1] != "..":
            stack.pop()
        elif seg == "..":
            # 畳み込めない .. は root 越境。マーカーとして積み、escaped を立てる。
            escaped = True
            stack.append("..")
        else:
            stack.append(seg)
    return "/".join(stack), escaped


def normalize_path(file_path: str, project_root: pathlib.Path) -> str:
    """
    絶対パスを project_root からの相対パスに変換する。
    すでに相対パスの場合は字句的に正規化して返す。
    返却値は文字列（スラッシュ区切り）。

    W-15: 絶対パスの境界判定は resolve() で symlink を実体に展開してから行う。
    root 内の symlink が project_root 外を指す偽装（`<root>/link/x` → 外部）を
    out-of-root として捕捉するため。resolve(strict=False) のため未作成パス
    （Write 新規）も親まで解決される。
    W-16: 相対パス分岐は `..` を字句的に畳み込んで境界判定する。root を越境する
    相対 traversal（`../../etc/passwd` 等）は out-of-root とし、root 内に収まる
    良性の `..`（`docs/../specs` 等）は正規化して返す。`..` を含まない通常パスは
    結果が不変で素通し契約を維持する。
    project_root は resolve 済み/未 resolve のどちらも受け付ける（内部で再 resolve・べき等）。
    """
    p = pathlib.Path(file_path)
    # POSIX形式の絶対パス（/etc/... 等）は Windows では is_absolute()=False に
    # なるため、先頭スラッシュも絶対パスとして扱い out-of-root 判定を効かせる。
    if not p.is_absolute() and not file_path.startswith("/"):
        # W-16: 相対パスの .. を字句的に畳み込んで境界判定する（cwd 非依存・FS 非アクセス）。
        # \ 区切りも / に正規化されるため、pre-tool-use.py の PM 保護パターン
        # （/ 区切り前提）への権限分類すり抜けも併せて防ぐ。
        norm, escaped = _normalize_relative_segments(file_path)
        if escaped:
            # root を越境する相対 traversal は out-of-root マーカーで PM 級に捕捉させる。
            return f"__out_of_root__/{file_path}"
        # 空（root 自身に畳み込まれた）場合は絶対分岐の root 自身と整合させ '.' を返す。
        return norm or "."
    # 絶対パス: symlink を展開した実体で境界判定する（両辺 resolve）。
    # strict=False（デフォルト）なので未作成の Write 新規パスも親まで解決される。
    root = project_root.resolve()
    try:
        resolved = p.resolve()
    except (OSError, RuntimeError) as e:
        # resolve 失敗時は生パスにフォールバック（握りつぶさず WARNING）。
        # 生パスで relative_to に失敗すれば out-of-root（厳しい側）に倒れる。
        #   OSError    : 循環 symlink（POSIX ELOOP / Windows WinError）等の OS エラー。
        #   RuntimeError: 現行 resolve(strict=False) では通常発生しないが、予期せぬ
        #                 内部エラーでも hook をクラッシュさせず out-of-root へ倒す
        #                 フェイルセーフとして併せて捕捉する（意図的に広め）。
        sys.stderr.write(
            f"WARNING: normalize_path: resolve() failed for {file_path!r}: {e}\n"
        )
        resolved = p
    try:
        relative = resolved.relative_to(root)
        # pre-tool-use.py のパターンは / 区切り前提のため as_posix() で正規化
        return relative.as_posix()
    except ValueError:
        # project_root の外のパスは out-of-root マーカー付きで返す。
        # 表示は resolve 前の生 file_path を保持（既存テスト互換・ログ可読性）。
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
