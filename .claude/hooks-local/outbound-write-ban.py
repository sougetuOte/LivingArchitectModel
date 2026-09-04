"""Outbound Write Ban — **作者環境限定の PreToolUse hook**（project 層）。

`docs/private/fable-l3-protocol.md` §2 が定める全レベル共通 **MUST NOT**
（外部リポジトリ配下への書込・編集の禁止）を執行する。

## なぜ `.claude/hooks/` ではなくここにあるか

2026-09-04 に配布形態を plugin へ移すにあたり、`.claude/hooks/pre-tool-use.py` は
**配布物（plugin コンポーネント）**になった。そこに作者マシンの絶対パスを埋めたままにすると、
利用者は「**動いているように見えて何も守らないコード**」を受け取る。

D-1 の設計（`docs/specs/d-1-distribution-boundary/design.md` §5 決定 D4）は目標状態を
「**hook・テスト・条文がすべて配布物から外れる**」と定義し、それを「hooks を対象に含む
後続 Milestone の仕事」として送っていた。本ファイルがその達成である。

- **条文**: `docs/private/fable-l3-protocol.md` §0-§2（配布されない）
- **機構**: 本ファイル（`.claude/hooks-local/` = 配布されない）
- **テスト**: `.claude/tests/hooks/test_outbound_write_ban.py`（配布されない）

## なぜ「追加」であって「置換」ではないか

Claude Code の hook は**設定レベル間で merge され、置換されない**
（公式: "All matching hooks run in parallel. ... A plugin's or skill's copy of the same handler
stays separate."）。したがって本 hook は配布物の `pre-tool-use.py` の**横に 1 本足す**形で動く。
これは不変条件「私的規範は『追加』のみ許し『置換』を許さない」に厳密に一致する。

また `exit 2` は blocking であり、他の hook が JSON で `permissionDecision: allow` を返しても
**覆せない**（公式 / fail-secure）。よって独立した hook でも deny の実効性は落ちない。

## 自己完結である理由

本ファイルは `_hook_utils.py` を import **しない**。あちらは配布物側へ移るため、
project 層が配布物の内部実装に依存すると層の独立が崩れる。パス判定の小さな helper は
意図的に複製している（約 30 行）。

## 権限等級

本ファイルの変更: **SE 級**（`.claude/` 配下だが `rules` でも `settings*.json` でもない）。
ただし **`docs/private/fable-l3-protocol.md` §2 の記載と本ファイルの定数は同時に更新する**
（drift 検査: `.claude/tests/hooks/test_outbound_write_ban.py::test_banned_root_matches_rule_document`）。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# SSOT は条文側（`docs/private/fable-l3-protocol.md` §2）。パス移動時は両方を更新する。
_BAN_ROOTS = (Path("D:/work7/Fable-Alembic"),)

# ADR-0008 D1（deny ↔ allow 二重化必須 / deny 単独で守らない）に対応する allow。
# 条文 §2 が定めた**唯一の正規経路**であり、deny より先に照合して優先させる。
_ALLOW_ROOTS = (Path("D:/work7/etc-to-alembic/handoff"),)


def is_under(path: Path, root: Path) -> bool:
    """`path` が `root` 配下かを判定する（Windows の大小文字非区別に対応）。"""
    try:
        path.relative_to(root)
        return True
    except ValueError:
        pass
    # Windows のファイルシステムは大小文字を区別しない。`resolve()` は実在パスを
    # 正規化するが、未作成パスでは元の表記が残るため casefold で再照合する。
    try:
        Path(str(path).casefold()).relative_to(Path(str(root).casefold()))
        return True
    except ValueError:
        return False


def resolve_target(file_path: str, project_root: Path) -> Path | None:
    """判定用にパスを実体解決する。

    セパレータ違い（`\\` / `/`）・相対 traversal・symlink を吸収するため `resolve()` を通す。
    resolve に失敗した場合は生パスで照合を続行する（**フェイルクローズ寄り** /
    絶対禁止ガードのため素通しにしない）。
    """
    try:
        p = Path(file_path)
    except (TypeError, ValueError) as e:
        sys.stderr.write(f"WARNING: outbound ban: Path() failed for {file_path!r}: {e}\n")
        return None
    if not p.is_absolute():
        p = project_root / p
    try:
        return p.resolve()
    except (OSError, RuntimeError) as e:
        sys.stderr.write(f"WARNING: outbound ban: resolve() failed for {file_path!r}: {e}\n")
        return p


def check(file_path: str, project_root: Path) -> str | None:
    """禁止に該当するなら理由文字列を返す（該当なしは None）。"""
    resolved = resolve_target(file_path, project_root)
    if resolved is None:
        return None
    for allow_root in _ALLOW_ROOTS:
        if is_under(resolved, allow_root):
            return None
    for banned_root in _BAN_ROOTS:
        if is_under(resolved, banned_root):
            return (
                f"Outbound Write Ban: {banned_root} 配下は書込・編集できません"
                "（docs/private/fable-l3-protocol.md §2 / 全レベル共通 MUST NOT）。"
                "受け渡しは handoff 経路を使ってください。"
            )
    return None


def get_project_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2]


def main() -> int:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # 入力を解釈できないときは黙って通す（他 hook の判定を邪魔しない）

    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return 0

    reason = check(file_path, get_project_root())
    if reason is None:
        return 0

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            },
            ensure_ascii=False,
        )
    )
    sys.stderr.write(reason + "\n")
    return 2  # blocking（他 hook の allow では覆せない）


if __name__ == "__main__":
    sys.exit(main())
