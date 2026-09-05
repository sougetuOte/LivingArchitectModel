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
import re
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


# R1-034: PM 級パス判定パターン（path-only / out-of-root マーカーを含まない）。
# pre-tool-use.py の `_PM_PATTERNS`（PM 級判定）と post-tool-use.py の
# `_PM_PATH_PATTERNS_FOR_CACHE`（セッションスコープ降格キャッシュ対象判定）が
# 手書きで別々に複製されていたため、ここに一本化して両モジュールから import する。
#
# out-of-root pattern（`^__out_of_root__/`）は意図的にここへ含めない（R1-I18）。
# out-of-root 経由の PM 判定はキャッシュ機構の対象外とし、承認後も同一セッション内で
# 毎回 PM ダイアログを再表示させる（安全側維持 / root 外パスは信頼度が低いため
# セッションスコープ降格の対象にしない設計判断）。pre-tool-use.py 側では
# `^__out_of_root__/` を別途ローカルで維持する。
#
# 大文字小文字を区別しない（2026-09-05 追加 / /full-review iter0 C-2 / ユーザー承認済）。
# 実行環境は Windows（`CLAUDE.md` §Execution Environment）であり NTFS は既定で
# case-insensitive かつ case-preserving である。一方 `normalize_path` の相対パス分岐は
# FS へ問い合わせない設計（意図的）なので、`.claude/Rules/security-commands.md` は
# 正規化後も大文字 R のまま残り、大小文字を区別する正規表現に一致しなかった。
# 実測（2026-09-05）: `.claude/Rules/security-commands.md` -> ('SE', 'default path') /
# `Claude.md` -> ('SE', 'default path') となる一方、`head -1 ".claude/Rules/..."` は
# 実ファイルを読み出す。**判定は SE、書込先は PM 級ファイル本体**という経路が
# 成立していた。判定側を FS の性質に合わせることで塞ぐ。
# 検査: .claude/tests/hooks/test_pm_gate_case_and_state_files.py
_PM_PATH_FLAGS = re.IGNORECASE
_PM_PATH_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^docs/specs/.*\.md$", _PM_PATH_FLAGS),
    re.compile(r"^docs/adr/.*\.md$", _PM_PATH_FLAGS),
    # docs/internal/（2026-09-04 追加 / retro-2026-09-04 A1 / ユーザー承認済）。
    # Hierarchy of Truth（CLAUDE.md）は docs/internal/00-08 を level 2、docs/specs/ を
    # level 3 と定めるのに、等級は specs=PM / internal=SE と逆転していた。
    # 実測（2026-09-04）: 247 行の新規 SSOT `08_EXECUTION_DISCIPLINE.md` が無ゲートで
    # 生まれ、PM ダイアログは参照側（.claude/rules/ の 12 箇所付替）にのみ発火した。
    # さらに docs/internal/ は managed 配布物であり、無ゲートの条文が利用者へ配られる。
    # docs/ 配下の他（artifacts / private / daily）は記録であり規範ではないため SE のまま。
    re.compile(r"^docs/internal/.*\.md$", _PM_PATH_FLAGS),
    re.compile(r"^\.claude/rules/.*\.md$", _PM_PATH_FLAGS),
    re.compile(r"^\.claude/settings.*\.json$", _PM_PATH_FLAGS),
    # ルート CLAUDE.md（2026-07-26 追加 / 誕生ゲート設計 §4.2-4.3 / ユーザー承認済）。
    # 無条件ロードされる最も常駐性の高い 1 ファイルであり、条項追加が PM ダイアログも
    # 事前宣言義務も経ないという穴になっていた（HGA #19 仮定 5-iii）。
    # nested な CLAUDE.md を含めないのは、`/compact` 後に再注入されるのが
    # プロジェクトルートのみであり、常駐性の根拠がルートに限られるため。
    re.compile(r"^CLAUDE\.md$", _PM_PATH_FLAGS),
    # hook が書く信頼アンカー（2026-09-05 追加 / /full-review iter0 C-3・C-4 /
    # ユーザー承認済）。これらは「hook が書き、hook が読んで判断の根拠にする」
    # ファイルであり、モデルが直接書けると判断の前提そのものを偽造できる。
    # 実測（2026-09-05）: いずれも ('SE', 'default path') で無条件に書けた。
    #   - .session-pm-edit-cache.json: 偽造すると以後の PM 承認が全て SE へ降格する
    #     （判定は session_id とパス文字列の一致のみで偽造耐性が無く、session_id は
    #     トランスクリプトのファイル名として `ls` だけで得られる）
    #   - autonomous-state.json: active=false にすると G1 checker を一度も評価せずに
    #     ループが「正常終了」した体で止まる
    #   - gd-session-state.json: token/time bound による PM エスカレーションを回避できる
    #   - lam-loop-state.json: ループ制御そのものを外側から書き換えられる
    # 射程は Edit / Write 経路のみ（Bash 経由は `file_path` を持たず到達しない）。
    # これは FR-9 / FR-3.4 deny や PLANNING 設定凍結と同じ既知の限界であり、
    # ここで変えるものではない。
    re.compile(r"^\.claude/\.session-pm-edit-cache\.json$", _PM_PATH_FLAGS),
    re.compile(r"^\.claude/autonomous-state\.json$", _PM_PATH_FLAGS),
    re.compile(r"^\.claude/gd-session-state\.json$", _PM_PATH_FLAGS),
    re.compile(r"^\.claude/lam-loop-state\.json$", _PM_PATH_FLAGS),
)


def is_pm_path_pattern(path_str: str) -> bool:
    """正規化済みパス文字列が PM 級パスパターンのいずれかに一致するかを判定する。

    out-of-root マーカーは含まない（`_PM_PATH_PATTERNS` の docstring 参照）。
    """
    return any(p.match(path_str) for p in _PM_PATH_PATTERNS)


def now_utc_iso8601() -> str:
    """UTC の ISO 8601 タイムスタンプ文字列を返す。"""
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _env_dir(name: str) -> "pathlib.Path | None":
    """環境変数をディレクトリとして解決する。不正なら握りつぶさず警告して None を返す。"""
    raw = os.environ.get(name)
    if not raw:
        return None
    resolved = pathlib.Path(raw).resolve()
    if resolved.is_dir():
        return resolved
    sys.stderr.write(
        f"WARNING: {name} is not a directory: {raw!r}, falling back\n"
    )
    return None


def get_project_root() -> pathlib.Path:
    """
    プロジェクトルートの Path を返す。

    解決順（**上ほど強い**）:

    1. ``LAM_PROJECT_ROOT`` — テストの明示 override。**最優先を維持する**。
       ここを 2 位以下に落とすと、Claude Code セッション内で走るテストが
       ``CLAUDE_PROJECT_DIR`` 経由で実プロジェクトを掴み、tmp_path による隔離が崩れる。
    2. ``CLAUDE_PROJECT_DIR`` — Claude Code が **hook 実行時に注入する**プロジェクトディレクトリ。
       ``.claude/settings.json`` の既存 hook コマンドが ``$CLAUDE_PROJECT_DIR`` を使って
       現に動いていることが、注入の実証になっている。
    3. ``__file__`` からの導出（``.claude/hooks/_hook_utils.py`` → 2 階層上）— **最も弱い**。

    2 を追加した理由（2026-09-04 / plugin 移行 P0 / MAGI ``2026-09-04-magi-migration-order.md``）:
    hooks が plugin へ移ると ``__file__`` は **plugin cache** を指す。上流は
    「``${CLAUDE_PLUGIN_ROOT}`` に永続状態を置くな（更新でパスが変わる）」と明記している。
    そのとき被害は 3 段階で、**深いほど静かになる**:

    - 状態ファイル（``tdd-patterns.log`` / ``permission.log`` / PM キャッシュ）が
      cache に書かれ、``/plugin update`` で消える
    - ``current-phase.md`` が読めず、**フェーズ依存のガードが黙って死ぬ**
    - ``normalize_path()`` が誤った root で相対化するため ``_PM_PATH_PATTERNS`` が
      一切マッチせず、**PM 級承認ゲートが丸ごと no-op になる**

    **「root が健全か」を推測で判定しない。** 推測は必ず空振りする —— ``marketplace add`` は
    リポジトリ全体を ``.claude`` ごと clone するため（MAGI V2 実測）、
    「``.claude`` があれば健全な root」という判定は clone を健全と誤検知し、fail-open に直結する。
    代わりに **最も弱い経路（3）を使ったという事実そのものを stderr に出す**。
    hook 実行時の stderr は上流がトランスクリプトに表示するため、沈黙にならない。
    """
    root = _env_dir("LAM_PROJECT_ROOT")
    if root is not None:
        return root

    root = _env_dir("CLAUDE_PROJECT_DIR")
    if root is not None:
        return root

    # __file__ は .claude/hooks/_hook_utils.py
    # parent   -> .claude/hooks/
    # parent.parent -> .claude/
    # parent.parent.parent -> PROJECT_ROOT
    fallback = pathlib.Path(__file__).resolve().parent.parent.parent
    sys.stderr.write(
        "WARNING: neither LAM_PROJECT_ROOT nor CLAUDE_PROJECT_DIR is set; "
        f"falling back to __file__-derived project root: {fallback}\n"
    )
    return fallback


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


def safe_exit(code: int = 0):
    """sys.exit のラッパー。"""
    sys.exit(code)
