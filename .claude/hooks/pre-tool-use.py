#!/usr/bin/env python3
"""
pre-tool-use.py - LAM PreToolUse hook: 権限等級判定（PG/SE/PM）

bash 版 pre-tool-use.sh の Python 移植版。
stdin から JSON を受け取り、ツール名とファイルパスに基づいて
PG/SE/PM の等級を判定する。

判定結果:
  PG級  → exit 0（許可）
  SE級  → exit 0 + ログ記録
  PM級  → stdout に hookSpecificOutput JSON（permissionDecision: "ask"）を出力して exit 0
         Claude Code のネイティブ許可ダイアログでユーザーに判断を委ねる
  DENY → stdout に hookSpecificOutput JSON（permissionDecision: "deny"）を出力して exit 0
         FR-9（自己統治の不可侵・design D5）: AUTONOMOUS フェーズでの統治ファイル
         書込をブロックする層2（プロンプティング層）。層1（permissions.deny の
         決定的層）は T1-5 後に autonomous 専用 settings で別途固定する

対応仕様: docs/design/hooks-python-migration-design.md H1（pre-tool-use）
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

# sys.path に hooks ディレクトリを追加（_hook_utils を import するため）
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from _hook_utils import (  # noqa: E402
    get_project_root,
    get_tool_input,
    get_tool_name,
    log_entry,
    normalize_path,
    read_stdin_json,
)

# セッションスコープの PM 級降格キャッシュ（案 A）。
# 同一セッション内で 2 回目以降の Edit/Write は SE 級に降格する。
# キャッシュは PostToolUse hook が「正常完了した PM 級書込」を検知した時点で追加する。
# セッション境界（session_id 変化）で自動失効。
_PM_CACHE_FILENAME = ".session-pm-edit-cache.json"

# 読み取り専用ツール: 常に PG 許可
_READ_ONLY_TOOLS = frozenset({"Read", "Glob", "Grep", "WebSearch", "WebFetch"})

# AUDITING フェーズの PG 許可コマンドのプレフィックス
# 注: settings.json の allow リストにも同コマンドが登録されている。
# Claude Code は allow マッチ時に hook をスキップする場合があるため、
# このブラックリストチェックは「二重防御」として機能する。
# allow 側の粗いワイルドカード（例: "Bash(ruff check --fix *)"）を
# hook 側で精密にフィルタする設計。実害が確認された場合は
# allow からの削除を検討し、hook に一元化すること。
_AUDITING_PG_COMMANDS = (
    "npx prettier",
    "npx eslint --fix",
    "ruff check --fix",
    "ruff format",
)

# PG コマンドで禁止する引数（悪意ある設定ファイル読み込み等を防止）
_PG_BLACKLISTED_ARGS = (
    "--config",
    "--settings",
    "--ruleset",
    "--rule-dir",
    "--rulesdir",
    "--plugin",
    "--resolve-plugins-relative-to",
    "--stdin-filename",
    "--ignore-path",
    "--ext",
)

# パス判定パターン（PM 級）
_PM_PATTERNS = [
    (re.compile(r"^__out_of_root__/"), "out-of-root path"),
    (re.compile(r"^docs/specs/.*\.md$"), "specs/ path"),
    (re.compile(r"^docs/adr/.*\.md$"), "adr/ path"),
    (re.compile(r"^\.claude/rules/.*\.md$"), "rules/ path"),
    (re.compile(r"^\.claude/settings.*\.json$"), "settings path"),
]

# パス判定パターン（SE 級）
_SE_PATTERNS = [
    (re.compile(r"^docs/"), "docs/ path (non-specs/adr)"),
    (re.compile(r"^src/"), "src/ path"),
]

# FR-9 自己統治の不可侵（design D5）: AUTONOMOUS フェーズでのみ書込を deny する
# 統治ファイル群。.claude/hooks/** と .claude/skills/autonomous/** を含めることで、
# 自律エンジンが FR-9 強制機構そのもの（hook / モード定義）を書き換える再帰ハザードを塞ぐ。
# これは層2（プロンプティング層）。層1（permissions.deny の決定的層・override 不可）は
# .claude/settings.autonomous.json で固定済み（T1-4 層1, 5af4a63）。両層で二重防御する。
_FR9_PATTERNS = [
    (re.compile(r"^\.claude/rules/"), "rules/"),
    (re.compile(r"^docs/adr/"), "adr/"),
    (re.compile(r"^\.claude/settings.*\.json$"), "settings"),
    (re.compile(r"^\.claude/hooks/"), "hooks/"),
    (re.compile(r"^\.claude/skills/autonomous/"), "skills/autonomous/"),
]

# FR-3.4 spec freeze（requirements FR-3.4 MUST / design D2 §4・D7 層1）: AUTONOMOUS フェーズで
# docs/specs/ 配下の書込を deny する。spec は FR-9 の統治ファイル（自己統治の強制点）ではなく
# 「成果物」だが、FR-3.4 が「spec 書換」を不可逆 C 操作の即時ハードストップに明示列挙するため、
# FR-9 とは別系統で deny する（成果物と統治ファイルの混同を避ける）。層1（permissions.deny の
# 決定的層・override 不可）は .claude/settings.autonomous.json に docs/specs/** を併記済み（二重防御）。
_FR34_SPEC_PATTERNS = [
    (re.compile(r"^docs/specs/"), "specs/"),
]


def _determine_by_path(
    file_path: str,
    project_root: Path,
    phase_file: Path,
) -> tuple[str, str]:
    """ファイルパスから権限等級を判定する（パスベース判定）。"""
    normalized = normalize_path(file_path, project_root)

    # FR-9（自己統治の不可侵）: AUTONOMOUS フェーズでは統治ファイルへの書込を
    # deny する（design D5・自己破壊的再帰防止）。PM 照合より前段で判定する。
    if _read_current_phase(phase_file) == "AUTONOMOUS":
        for pattern, fr9_reason in _FR9_PATTERNS:
            if pattern.match(normalized):
                return "DENY", f"FR-9 self-governance immutability ({fr9_reason})"
        # FR-3.4 spec freeze（FR-9 とは別系統・成果物の即時ハードストップ）。
        # reason の "FR-3.4" 接頭辞を main() が見て deny 文言を出し分ける。
        for pattern, spec_reason in _FR34_SPEC_PATTERNS:
            if pattern.match(normalized):
                return "DENY", f"FR-3.4 spec freeze ({spec_reason})"

    # PM パターン照合
    for pattern, reason in _PM_PATTERNS:
        if pattern.match(normalized):
            return "PM", reason

    # SE パターン照合
    for pattern, reason in _SE_PATTERNS:
        if pattern.match(normalized):
            return "SE", reason

    return "SE", "default path"


def _determine_by_command(
    command: str,
    phase_file: Path,
) -> tuple[str, str]:
    """コマンド文字列から権限等級を判定する（コマンドベース判定・Bash ツール等）。"""
    # AUDITING フェーズの PG コマンド特別処理
    if _read_current_phase(phase_file) == "AUDITING":
        for pg_prefix in _AUDITING_PG_COMMANDS:
            if command == pg_prefix or command.startswith(pg_prefix + " "):
                # ブラックリスト引数チェック（単語境界で照合し誤マッチを防止）
                args_part = command[len(pg_prefix):]
                if any(
                    re.search(r'(?:^|\s)' + re.escape(bl) + r'(?:\s|=|$)', args_part, re.IGNORECASE)
                    for bl in _PG_BLACKLISTED_ARGS
                ):
                    return "PM", "PG command with blacklisted arg"
                return "PG", "AUDITING phase PG allow"

    return "SE", "command (default SE)"


def _determine_level_and_reason(
    tool_name: str,
    file_path: str,
    command: str,
    project_root: Path,
    phase_file: Path,
) -> tuple[str, str]:
    """ツール名とパスから権限等級とその理由を判定する。

    パスがあればパスベース判定、なければコマンドベース判定に委譲する。

    Returns:
        (level, reason): level は "PG" | "SE" | "PM" | "DENY"
    """
    # 1. ファイルパスが存在する場合はパスベース判定
    if file_path:
        return _determine_by_path(file_path, project_root, phase_file)

    # 2. コマンドベース判定（Bash ツール等）
    if command:
        return _determine_by_command(command, phase_file)

    # 3. パスもコマンドもない（Agent 等）
    return "SE", "no-path (default SE)"


def _sanitize_target(raw: str) -> str:
    """ログ用ターゲット文字列を無害化する（100 文字トランケート + 制御文字除去）。

    タブ/改行に加え、Unicode 双方向制御文字（U+202E 等の Cf カテゴリ）や C0/C1
    制御文字（Cc カテゴリ）を半角スペースへ置換する。これらはログ表示時に
    パス偽装（Trojan Source 型）やターミナル制御列注入を引き起こしうるため、
    記録前に除去する。
    """
    return "".join(
        " " if unicodedata.category(ch) in ("Cc", "Cf") else ch
        for ch in raw[:100]
    )


def _is_pm_already_approved(
    session_id: str,
    normalized_path: str,
    cache_file: Path,
) -> bool:
    """同一セッション内で当該 PM 級パスが既に承認済かを判定する（案 A）。

    キャッシュは PostToolUse hook が「正常完了した PM 級書込」を検知した時点で追加する。
    つまりここで True を返すのは「ユーザーが過去に同一セッション内で同一パスを承認した」場合のみ。

    Returns:
        True: 承認済（SE 級に降格すべき）
        False: 未承認・キャッシュ無効・session_id 不一致（通常の PM 級判定を維持）
    """
    if not session_id or not normalized_path or not cache_file.exists():
        return False
    try:
        cache = json.loads(cache_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        # キャッシュ破損時はフェイルセーフで「未承認」扱い（安全側 / PM ダイアログ維持）
        return False
    if cache.get("session_id") != session_id:
        return False
    approved = cache.get("approved_paths")
    if not isinstance(approved, list):
        return False
    return normalized_path in approved


def _read_current_phase(phase_file: Path) -> str:
    """current-phase.md から現在のフェーズ名を読み取る。

    **PHASE** 形式から PHASE を抽出する。
    ファイルが存在しない/読み込み失敗時は空文字を返す。
    """
    if not phase_file.exists():
        return ""
    try:
        content = phase_file.read_text(encoding="utf-8")
        for line in content.splitlines():
            match = re.match(r"^\*\*([A-Z]+)\*\*", line)
            if match:
                return match.group(1)
    except Exception as e:
        # フェーズ読取失敗は AUTONOMOUS の FR-9/FR-3.4 判定を無効化しうる
        # （フェイルオープン方向）。黙殺せず stderr に記録する（iter1 W-2 同型）。
        sys.stderr.write(
            f"WARNING: failed to read phase file {phase_file}: "
            f"{type(e).__name__}: {e}\n"
        )
    return ""


def _build_deny_reason(reason: str, target: str) -> str:
    """DENY 応答の説明文言を構築する。

    DENY は2系統: FR-9（統治ファイルの自己統治不可侵）と FR-3.4（spec freeze・成果物の
    即時ハードストップ）。reason 接頭辞で説明文言を出し分ける（reason は内部生成で安定）。
    """
    if reason.startswith("FR-3.4"):
        return (
            f"FR-3.4 spec freeze: AUTONOMOUS モードでは仕様（docs/specs/）を変更できません"
            f"（{reason}）。spec 書換は不可逆 C 操作として即時ハードストップに当たり、"
            f"自律ループ外の人間承認ゲートでのみ変更可。対象: {target}"
        )
    return (
        f"FR-9 自己統治の不可侵: AUTONOMOUS モードでは統治ファイルを変更できません"
        f"（{reason}）。自律ループ外の人間承認ゲートでのみ変更可。対象: {target}"
    )


def _emit_permission_response(level: str, reason: str, target: str) -> None:
    """判定結果に応じて hookSpecificOutput を stdout に出力する。

    DENY → permissionDecision=deny / PM → ask / それ以外は出力なし（許可）。
    """
    if level == "DENY":
        decision, decision_reason = "deny", _build_deny_reason(reason, target)
    elif level == "PM":
        decision, decision_reason = "ask", f"PM級変更です。承認してください: {target}"
    else:
        return
    print(json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": decision_reason,
            }
        },
        ensure_ascii=False,
    ))


def main() -> None:
    project_root = get_project_root()
    log_file = project_root / ".claude" / "logs" / "permission.log"
    phase_file = project_root / ".claude" / "current-phase.md"

    # stdin から JSON 読み込み
    data = read_stdin_json()

    # ツール名を取得（取得失敗時は SE 扱いで終了）
    tool_name = get_tool_name(data)
    if not tool_name:
        log_entry(log_file, "SE", "unknown", "tool_name extraction failed")
        sys.exit(0)

    # 1. 読み取り専用ツールは常に PG 許可
    if tool_name in _READ_ONLY_TOOLS:
        log_entry(log_file, "PG", tool_name, "- read-only tool")
        sys.exit(0)

    # ファイルパスとコマンドを取得
    file_path = get_tool_input(data, "file_path")
    command = get_tool_input(data, "command")

    # 権限等級判定
    level, reason = _determine_level_and_reason(
        tool_name, file_path, command, project_root, phase_file
    )

    # 案 A: 同一セッション内で 2 回目以降の PM 級 Edit/Write は SE 級に降格する。
    # DENY 経路（FR-9 / FR-3.4）は対象外（AUTONOMOUS の deny は不可侵）。
    # キャッシュ追加は post-tool-use.py が「正常完了した PM 級書込」を検知した時点で行う。
    if level == "PM" and file_path:
        session_id = data.get("session_id", "")
        cache_file = project_root / ".claude" / _PM_CACHE_FILENAME
        normalized = normalize_path(file_path, project_root)
        if _is_pm_already_approved(session_id, normalized, cache_file):
            level = "SE"
            reason = f"PM downgraded to SE (session-scoped re-edit) / original: {reason}"

    # ログ用のターゲット文字列（100 文字トランケート + 制御文字・双方向制御文字を除去）
    raw_target = file_path or command or "-"
    target = _sanitize_target(raw_target)

    # ログ記録（TSV 形式: timestamp\tlevel\ttool_name\ttarget\t"reason"）
    log_entry(log_file, level, tool_name, f"{target}\t\"{reason}\"")

    _emit_permission_response(level, reason, target)
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # フック障害時にも Claude をブロックしない
        sys.exit(0)
