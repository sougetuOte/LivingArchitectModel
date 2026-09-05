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
    _PM_PATH_PATTERNS,
    get_project_root,
    get_tool_input,
    get_tool_name,
    log_entry,
    normalize_path,
    read_stdin_json,
)
from _incident_patterns import (  # noqa: E402
    PatternMatch,
    load_patterns,
    match_input,
)

# セッションスコープの PM 級降格キャッシュ（案 A）。
# 同一セッション内で 2 回目以降の Edit/Write は SE 級に降格する。
# キャッシュは PostToolUse hook が「正常完了した PM 級書込」を検知した時点で追加する。
# セッション境界（session_id 変化）で自動失効。
_PM_CACHE_FILENAME = ".session-pm-edit-cache.json"

# 読み取り専用ツール: 常に PG 許可
_READ_ONLY_TOOLS = frozenset({"Read", "Glob", "Grep", "WebSearch", "WebFetch"})

# subagent 起動を表すツール名。CC SDK で Task/Agent 両方が存在する旨が
# 公式に明示されているため両対応。ADR-0008 Phase B-2b / MAGI 合議 C5。
_SUBAGENT_TOOLS = frozenset({"Task", "Agent"})

# additionalContext の上限（公式仕様 10,000 文字 / 余裕を見て 9,500 でトランケート）
_ADDITIONAL_CONTEXT_LIMIT = 9500

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

# R1-032 + R1-052: PG コマンドで禁止する shell メタ文字（コマンド連結・置換演算子）。
# `ruff format x.py; rm -rf /tmp` のような合成が settings.json Layer 1 allow の
# prefix ワイルドカードマッチと hook 側 PG 判定の両方を通過する gap を塞ぐ。
#
# R1-052 (HGA #7 Fable 2026-07-06 検出): 初期修正 (";", "&&", "||", "|", "`", "$(") では
# 単体 `&` (バックグラウンド区切り) / `\n` (改行連結) / `<(` (プロセス置換) が素通し。
# 同一 attack class の追加 3 パターンを網羅。
_SHELL_METACHARACTERS = (";", "&&", "||", "|", "`", "$(", "&", "\n", "<(")

# パス判定パターン（PM 級）
# R1-034: path-only 部分（out-of-root を除く）は _hook_utils._PM_PATH_PATTERNS に
# 一本化されている（post-tool-use.py の _PM_PATH_PATTERNS_FOR_CACHE と共有）。
# out-of-root pattern はここでのみローカル定義する（R1-I18 / 理由は下記コメント）。
#
# R1-I18 non-symmetry: なぜ pre 側だけ out-of-root を持つのか。
# out-of-root（project_root 外のパス）は信頼度が低いため、承認後も
# セッションスコープ降格キャッシュ（.session-pm-edit-cache.json）の対象にしない
# 設計判断（安全側維持）。post-tool-use.py 側のキャッシュ記録判定
# （_PM_PATH_PATTERNS_FOR_CACHE）が out-of-root を含まないのはこのため。
# 結果として out-of-root パス書込は同一セッション内でも毎回 PM ダイアログが
# 再表示される（実害なし・意図的な非対称設計）。
_PM_OUT_OF_ROOT_PATTERN = (re.compile(r"^__out_of_root__/"), "out-of-root path")
# 要素数は `_hook_utils._PM_PATH_PATTERNS` と一致させること（zip は末尾を静かに
# 切り捨てるため、不一致だと追加した pattern が PM 判定に載らない）。
# 検査: .claude/tests/hooks/test_pm_path_claude_md.py::test_pm_reasons_length_matches_patterns
_PM_PATH_REASONS = (
    "specs/ path",
    "adr/ path",
    "internal/ path",
    "rules/ path",
    "settings path",
    "root CLAUDE.md",
    "hook-owned trust anchor (pm-edit-cache)",
    "hook-owned trust anchor (autonomous-state)",
    "hook-owned trust anchor (gd-session-state)",
    "hook-owned trust anchor (lam-loop-state)",
)
_PM_PATTERNS = [_PM_OUT_OF_ROOT_PATTERN] + list(zip(_PM_PATH_PATTERNS, _PM_PATH_REASONS))

# パス判定パターン（SE 級）
_SE_PATTERNS = [
    (re.compile(r"^docs/"), "docs/ path (non-specs/adr/internal)"),
    (re.compile(r"^src/"), "src/ path"),
]

# FR-9 自己統治の不可侵（design D5）: AUTONOMOUS フェーズでのみ書込を deny する
# 統治ファイル群。.claude/hooks/** と .claude/skills/autonomous/** を含めることで、
# 自律エンジンが FR-9 強制機構そのもの（hook / モード定義）を書き換える再帰ハザードを塞ぐ。
# これは層2（プロンプティング層）。層1（permissions.deny の決定的層・override 不可）は
# .claude/settings.autonomous.json で固定済み（T1-4 層1, 5af4a63）。
#
# **「二重防御」の射程（2026-07-27 訂正 / WC-18「層 1 の空手形」）**:
#   両層とも **Edit / Write 経路のみ**を守る。**Bash 経路はどちらの層も素通りする**
#   （層1 の deny は `Edit(...)` / `Write(...)` のみで `Bash(...)` を 1 件も持たない /
#    層2 の本判定は file_path を要するため `_determine_by_command` に落ちる）。
#   したがって `Bash("echo x >> .claude/rules/foo.md")` は AUTONOMOUS でも通る。
#
#   **これは実装漏れではなく基質の制約である**: upstream の専用機構
#   `sandbox.filesystem.denyWrite`（OS レベルで全サブプロセスに適用し、`Edit(...)` deny の
#   パスを自動併合する）は **macOS / Linux / WSL2 のみで、native Windows は非サポート**
#   （code.claude.com/docs/en/sandboxing / 2026-07-27 裏取り）。`Bash(...)` ルールは
#   コマンド文字列の prefix マッチでありパス解析ではないため、書込可能なコマンド形の
#   列挙による代替は原理的に不完全になる。
#
#   hook 側の regex による Bash 遮断は **既に棄却済み**（MAGI CASPAR / 死んだ案 #15 =
#   ① Bash の command は自由文字列でスキーマ契約を持たない ② 散文結合機構を執行層に
#   新造することになる ③ 層の誤り）。本注記を残すのは、**穴を「二重防御」と呼ばない
#   ため**である（`fable-l3-protocol.md` §2 の裏返し = 沈黙している機構を鳴っていると
#   称さない）。検査: tests/test_settings_autonomous.py::test_layer1_does_not_cover_bash。
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
# 決定的層・override 不可）は .claude/settings.autonomous.json に docs/specs/** を併記済み。
# **射程は FR-9 と同じく Edit / Write のみ**（Bash 経路は両層とも素通り / 上記 _FR9_PATTERNS の
# 「二重防御」の射程 を参照）。
_FR34_SPEC_PATTERNS = [
    (re.compile(r"^docs/specs/"), "specs/"),
]

# Outbound Write Ban は **project 層へ分離した**（2026-09-04 / ADR-0010 追補 1）。
#
# 本ファイルは plugin コンポーネントとして配布されるため、作者マシンの絶対パスを
# 埋めたままにすると、利用者は「動いているように見えて何も守らないコード」を受け取る。
# D-1 design §5 決定 D4 が定めた目標状態「**hook・テスト・条文がすべて配布物から外れる**」
# に従い、機構を `.claude/hooks-local/outbound-write-ban.py`（配布されない project 層）へ移した。
#
# 分離しても deny の実効性は落ちない —— hook は設定レベル間で merge され置換されず、
# `exit 2` は他 hook の `permissionDecision: allow` では覆せない（公式 / fail-secure）。

# PLANNING §禁止 3 項目め「設定ファイル変更（package.json, pyproject.toml 等）」の執行
# （`.claude/rules/phase-rules.md` PLANNING §禁止）。**PLANNING フェーズ限定**。
#
# 射程の限界（過大評価しないこと / MAGI + gabriel 2 巡の結論）:
#   - **Edit / Write 経路のみを保護する。** `Bash("cat >> pyproject.toml")` は
#     file_path を持たないため `_determine_by_command` に落ち、本判定に到達しない。
#     Bash 経路の遮断は Layer 1（settings.json の permissions.deny）の領分であり、
#     同じ穴は既存の AUTONOMOUS FR-9 / FR-3.4 deny にも空いている。
#   - 条文の 4 項のうち機構化したのはこの 1 項のみ。「実装コード生成」は `src/` 不在 +
#     `.py` が `.claude/` に集中（ハーネス保守は PLANNING 中も正当なので除外必須）で
#     守る対象が消え、「`src/` への変更」は `src/` 自体が存在せず、「未承認での次
#     サブフェーズ開始」は意味判断のため機構化できない。
#
# ADR-0008 D4（ワイルドカード非依存・明示列挙）に従い閉じた集合で持つ。条文側は
# 「等」と開いた列挙であるため、**列挙外は「許可」ではなく「機構が捕捉していない」**
# を意味する（条文側の禁止は引き続き有効 / 境界テスト:
# test_planning_config_deny.py::test_unenumerated_config_file_is_not_denied）。
#
# `.claude/settings*.json` は意図的に含めない（統治ファイルであり既に PM 級パス /
# AUTONOMOUS では FR-9 が別系統で deny する / 本条項が想定する「プロジェクトの
# ビルド・依存設定」とは射程が異なる）。
_PLANNING_CONFIG_DENY_BASENAMES = frozenset({
    # Node / TypeScript
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock",
    "tsconfig.json",
    # Python
    "pyproject.toml", "setup.py", "setup.cfg",
    "requirements.txt", "requirements-dev.txt",
    # Rust / Go
    "Cargo.toml", "Cargo.lock", "go.mod", "go.sum",
    # Ruby / Java / PHP
    "Gemfile", "Gemfile.lock", "pom.xml", "build.gradle", "build.gradle.kts",
    "composer.json",
})

# ADR-0008 D1（deny ↔ allow 二重化必須 / deny 単独で守らない）に対応する allow。
# `phase-rules.md` PLANNING §許可 の出力先。deny より先に照合して優先させる。
# 特に `.claude/states/*.json` は PLANNING が正規に書き込む状態ファイルであり、
# 「.json だから設定ファイル」とみなす実装がこれを殺す事故を防ぐ。
_PLANNING_ALLOW_PATTERNS = [
    re.compile(r"^docs/(?:specs|adr|tasks|artifacts)/"),
    re.compile(r"^\.claude/states/"),
]


def _check_planning_config_freeze(normalized: str) -> tuple[str, str] | None:
    """PLANNING フェーズの設定ファイル変更なら DENY を返す（該当なしは None）。

    呼び出し元が phase == "PLANNING" を確認済みであることを前提とする。
    basename の**完全一致**で判定する（部分一致にすると
    `docs/artifacts/notes-about-pyproject.toml.md` 等を誤 deny する）。
    """
    for pattern in _PLANNING_ALLOW_PATTERNS:
        if pattern.match(normalized):
            return None
    basename = normalized.rsplit("/", 1)[-1]
    if basename in _PLANNING_CONFIG_DENY_BASENAMES:
        return "DENY", f"PLANNING config freeze ({basename})"
    return None


def _determine_by_path(
    file_path: str,
    project_root: Path,
    phase_file: Path,
) -> tuple[str, str]:
    """ファイルパスから権限等級を判定する（パスベース判定）。"""
    normalized = normalize_path(file_path, project_root)
    phase = _read_current_phase(phase_file)

    # FR-9（自己統治の不可侵）: AUTONOMOUS フェーズでは統治ファイルへの書込を
    # deny する（design D5・自己破壊的再帰防止）。PM 照合より前段で判定する。
    if phase == "AUTONOMOUS":
        for pattern, fr9_reason in _FR9_PATTERNS:
            if pattern.match(normalized):
                return "DENY", f"FR-9 self-governance immutability ({fr9_reason})"
        # FR-3.4 spec freeze（FR-9 とは別系統・成果物の即時ハードストップ）。
        # reason の "FR-3.4" 接頭辞を main() が見て deny 文言を出し分ける。
        for pattern, spec_reason in _FR34_SPEC_PATTERNS:
            if pattern.match(normalized):
                return "DENY", f"FR-3.4 spec freeze ({spec_reason})"

    # PLANNING §禁止 3 項目め（設定ファイル変更）。PM 照合より前段で判定する。
    # 射程は Edit / Write 経路のみ（Bash 経由は本判定に到達しない / 上記定数の注記参照）。
    if phase == "PLANNING":
        planning_deny = _check_planning_config_freeze(normalized)
        if planning_deny is not None:
            return planning_deny

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
                args_part = command[len(pg_prefix):]
                # R1-032: shell メタ文字（コマンド連結・置換）を含む場合は PM に降格。
                # settings.json Layer 1 allow が prefix ベースで shell を token 化しないため
                # 「二重防御」（L65-70）の意図に沿って hook 側で必ず PM 判定する。
                if any(mc in args_part for mc in _SHELL_METACHARACTERS):
                    return "PM", "PG command contains shell metacharacter"
                # ブラックリスト引数チェック（単語境界で照合し誤マッチを防止）
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

    DENY は3系統: FR-9（統治ファイルの自己統治不可侵）と FR-3.4（spec freeze・
    成果物の即時ハードストップ）と PLANNING config freeze（設定ファイル変更の禁止）。
    reason 接頭辞で説明文言を出し分ける（reason は内部生成で安定）。

    Outbound Write Ban は 2026-09-04 に project 層（`.claude/hooks-local/`）へ分離した。
    旧 docstring は PLANNING config freeze の追加に追随しておらず「3系統」の中身がずれていた。
    """
    if reason.startswith("PLANNING config freeze"):
        return (
            f"PLANNING フェーズでは設定ファイルを変更できません（{reason}）。"
            f"`.claude/rules/phase-rules.md` PLANNING §禁止 の 3 項目めです。"
            f"仕様・設計・タスクの出力（docs/specs/ docs/adr/ docs/tasks/ "
            f"docs/artifacts/ / .claude/states/）は許可されています。"
            f"設定変更が必要なら BUILDING へフェーズを切り替えてください。対象: {target}"
        )
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


def _emit_subagent_ask_response(reason: str, target: str) -> None:
    """subagent 境界判定の ask 応答を出力する（reason をそのまま使う）。

    汎用 _emit_permission_response の PM 分岐は reason を破棄してデフォルト文言で
    上書きするため、subagent 用に専用 helper を分離する（ADR-0008 Phase B-2b）。
    """
    print(json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": reason,
            }
        },
        ensure_ascii=False,
    ))


def _handle_subagent_boundary(
    tool_name: str,
    tool_input_dict: dict,
    phase: str,
) -> tuple[str, str, str] | None:
    """subagent 起動 (Task/Agent) を検知して境界判定する（ADR-0008 Phase B-2b）。

    MAGI 合議 C5: CC v2.1.178+ classifier との二重防御で重ね掛けは避け、
    AUTONOMOUS + autonomous skill 配下のみ ask に倒す。通常フェーズは log_only。

    Returns:
        (level, reason, target):
            level="PM"  -> 呼出側で ask 応答を出力
            level="LOG" -> ログ記録のみで通常 flow 継続
        None: subagent 起動ではない
    """
    if tool_name not in _SUBAGENT_TOOLS:
        return None

    subagent_type = ""
    description = ""
    if isinstance(tool_input_dict, dict):
        subagent_type = str(tool_input_dict.get("subagent_type", "") or "")
        description = str(tool_input_dict.get("description", "") or "")

    target = _sanitize_target(subagent_type or description or "subagent")

    if phase != "AUTONOMOUS":
        return ("LOG", f"subagent launch (non-autonomous / log only): {subagent_type or '-'}", target)

    # AUTONOMOUS フェーズでは autonomous skill 配下の起動を ask に倒す。
    # subagent_type 名に "autonomous" を含む / 不明 / autonomous 系であることが
    # 確認できない場合は安全側で ask（人間判断を仰ぐ）。
    return (
        "PM",
        f"AUTONOMOUS subagent launch ({subagent_type or 'unknown'}): "
        f"approval required (classifier 重ね掛け二重防御)",
        target,
    )


def _emit_incident_response(pmatch: PatternMatch, target: str) -> None:
    """incident pattern マッチ時の permissionDecision を stdout に出力（ADR-0008 Phase B-2c）。

    B-2c: additionalContext で Claude 側 model に検知文言を残し、自己学習を促す
    （system reminder ラップで tool result の隣に挿入される / 公式仕様）。

    action="log_only" は呼出側で除外済み（出力なし）。
    """
    if pmatch.action == "deny":
        decision = "deny"
        decision_reason = (
            f"LAM incident pattern '{pmatch.incident_id}' matched "
            f"(severity={pmatch.severity}). 対象: {target}"
        )
    elif pmatch.action == "ask":
        first_desc_line = (
            pmatch.description.splitlines()[0] if pmatch.description else ""
        )
        decision = "ask"
        decision_reason = (
            f"LAM インシデント検知 '{pmatch.incident_id}' "
            f"(severity={pmatch.severity}): {first_desc_line}。対象: {target}"
        )
    else:
        return  # log_only は呼出側でフィルタ済（保険）

    additional_context = (
        f"[LAM hook] incident pattern '{pmatch.incident_id}' "
        f"(action={pmatch.action}, severity={pmatch.severity}) "
        f"matched on {target}. Source: {pmatch.source_md}. "
        f"Description: {pmatch.description}"
    )[:_ADDITIONAL_CONTEXT_LIMIT]

    print(json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": decision_reason,
                "additionalContext": additional_context,
            }
        },
        ensure_ascii=False,
    ))


def main() -> None:
    project_root = get_project_root()
    log_file = project_root / ".claude" / "logs" / "permission.log"
    phase_file = project_root / ".claude" / "current-phase.md"
    incident_yaml = project_root / "docs" / "artifacts" / "incident-patterns.yaml"

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
    tool_input_dict = data.get("tool_input", {})
    if not isinstance(tool_input_dict, dict):
        tool_input_dict = {}

    phase = _read_current_phase(phase_file)

    # 1.5 subagent 境界判定（ADR-0008 Phase B-2b / MAGI 合議 C5）
    sub_result = _handle_subagent_boundary(tool_name, tool_input_dict, phase)
    if sub_result is not None:
        sub_level, sub_reason, sub_target = sub_result
        log_entry(log_file, sub_level, tool_name, f"{sub_target}\t\"{sub_reason}\"")
        if sub_level == "PM":
            _emit_subagent_ask_response(sub_reason, sub_target)
            sys.exit(0)
        # LOG: 検知のみ → 通常 flow へ続行（Task/Agent は後段判定で SE 級に倒れる）

    # 1.6 動的 incident pattern 判定（ADR-0008 Phase B-2a / fail-open）
    patterns = load_patterns(incident_yaml)
    pmatch = match_input(patterns, tool_name, file_path, command)
    if pmatch is not None:
        target_for_incident = _sanitize_target(file_path or command or "-")
        # B-2c: incident_id + severity + description 先頭行をログに記録
        first_desc = pmatch.description.splitlines()[0] if pmatch.description else ""
        log_entry(
            log_file,
            pmatch.action.upper(),
            tool_name,
            f"{target_for_incident}\t\"incident:{pmatch.incident_id}"
            f"\t{pmatch.severity}\t{first_desc}\"",
        )
        if pmatch.action in ("deny", "ask"):
            _emit_incident_response(pmatch, target_for_incident)
            sys.exit(0)
        # log_only: 通常 flow へ続行（ユーザー摩擦なし / 頻度監視のみ）

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
