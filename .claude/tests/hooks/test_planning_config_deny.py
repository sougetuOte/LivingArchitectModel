"""PLANNING フェーズの設定ファイル変更 deny の TDD（HGA #24 手 2 / W2）.

`.claude/rules/phase-rules.md` PLANNING §禁止 の 3 項目め
「設定ファイル変更（package.json, pyproject.toml 等）」に執行歯を付ける。

## なぜ 3 項目めだけか（4 項のうち 3 項を落とした理由）

MAGI + gabriel 2 巡（`docs/artifacts/2026-07-27-magi-planning-hook.md`）の結論:

- **1 項目め「実装コード生成」**: 実測で `src/` は不在、リポジトリ内の `.py` は 1 件を除き
  すべて `.claude/` 配下。ハーネス自身の保守は PLANNING 中も正当なので `.claude/` は
  除外せざるを得ず、**除外した瞬間に守る対象が消える**。唯一の例外
  （`docs/artifacts/cross-module-blame-package/blame_hint_parser.py`）は PLANNING
  **許可**範囲内であり、実装すれば**誤ブロックだけが残る**
- **2 項目め「`src/` への変更」**: **`src/` が存在しない**（dead letter / 記録のみ・条文は残す）
- **4 項目め「未承認での次サブフェーズ開始」**: 「承認」の有無は意味判断であり機構化できない

## この deny の射程（**過大評価しないこと** / gabriel G-1）

**Edit / Write 経路のみを保護する。** `Bash("cat >> pyproject.toml")` は `file_path` を
持たないため `_determine_by_command` に落ち、パス判定に到達しない（実測:
`pre-tool-use.py` の `_determine_by_command` は AUDITING 以外で常に SE を返す）。
Bash 経路の遮断は Layer 1（`.claude/settings.json` の `permissions.deny`）の領分であり、
**同じ穴は既存の AUTONOMOUS FR-9 / FR-3.4 deny にも空いている**。

## 列挙外は「許可」の意味ではない（ADR-0008 D4 / BALTHASAR 指摘）

条文は「package.json, pyproject.toml **等**」と**開いた列挙**で書かれている。機構は
ADR-0008 D4（ワイルドカード非依存・明示列挙）に従い閉じた集合で実装するため、
**列挙から漏れた設定ファイルは deny されない**。これは「許可された」という意味ではなく
「機構が捕捉していない」という意味である（条文側の禁止は引き続き有効）。
本ファイルの `test_unenumerated_config_file_is_not_denied` がこの境界を明示的に記録する。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_HOOKS_DIR = Path(__file__).resolve().parents[2] / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))


def _load_pre_tool_use():
    spec = importlib.util.spec_from_file_location(
        "pre_tool_use_for_planning_test", _HOOKS_DIR / "pre-tool-use.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def ptu():
    return _load_pre_tool_use()


def _phase_file(tmp_path: Path, phase: str) -> Path:
    f = tmp_path / f"phase-{phase}.md"
    f.write_text(f"# Current Phase\n\n**{phase}**\n", encoding="utf-8")
    return f


# --- deny: PLANNING フェーズの設定ファイル ------------------------------------


@pytest.mark.parametrize(
    "file_path",
    [
        "pyproject.toml",
        "requirements-dev.txt",
        "package.json",
        "package-lock.json",
        "tsconfig.json",
        "Cargo.toml",
        "go.mod",
    ],
)
def test_config_file_denied_in_planning(ptu, tmp_path: Path, file_path):
    """PLANNING フェーズでは列挙済みの設定ファイル変更が DENY となる。"""
    level, reason = ptu._determine_by_path(
        file_path, _REPO_ROOT, _phase_file(tmp_path, "PLANNING")
    )
    assert level == "DENY", f"{file_path!r} が DENY にならない（level={level} / {reason}）"
    assert "PLANNING" in reason


# --- フェーズ依存: 他フェーズでは無影響 ----------------------------------------


@pytest.mark.parametrize("phase", ["BUILDING", "AUDITING", "AUTONOMOUS"])
def test_config_file_not_denied_outside_planning(ptu, tmp_path: Path, phase):
    """PLANNING 以外では本 deny は発動しない（条文が PLANNING §禁止 のため）。"""
    level, _reason = ptu._determine_by_path(
        "pyproject.toml", _REPO_ROOT, _phase_file(tmp_path, phase)
    )
    assert level != "DENY", f"phase={phase} で誤って DENY された"


def test_config_file_not_denied_when_phase_unreadable(ptu, tmp_path: Path):
    """phase が読めない場合は発動しない（フェイルオープン / 既存 `_read_current_phase` 準拠）。

    真の問題は読取失敗ではなく stale（読めてしまう）であり、フェイルクローズ化しても
    stale には無力な一方、読取失敗時に全作業が止まる代償が過大であるため
    （MAGI Atom A2 の「採用しなかった選択肢」参照）。
    """
    level, _reason = ptu._determine_by_path(
        "pyproject.toml", _REPO_ROOT, tmp_path / "no-such-phase.md"
    )
    assert level != "DENY"


# --- allow 対（ADR-0008 D1 / deny 単独で守らない） -----------------------------


@pytest.mark.parametrize(
    "file_path",
    [
        ".claude/states/cc-spec-alignment.json",
        ".claude/states/magi-skill.json",
    ],
)
def test_planning_states_json_is_allowed(ptu, tmp_path: Path, file_path):
    """`.claude/states/*.json` は PLANNING §許可 に明記された出力先であり DENY されない。

    **これが allow 対の実体**（ADR-0008 D1）。`.json` という見た目だけで設定ファイルと
    みなす実装にすると、PLANNING が正規に書き込むべき状態ファイルを殺す。
    """
    level, reason = ptu._determine_by_path(
        file_path, _REPO_ROOT, _phase_file(tmp_path, "PLANNING")
    )
    assert level != "DENY", f"{file_path!r} が誤って DENY された（{reason}）"


@pytest.mark.parametrize(
    "file_path",
    [
        "docs/specs/x/design.md",
        "docs/adr/0012-x.md",
        "docs/tasks/x.md",
        "docs/artifacts/x.md",
    ],
)
def test_planning_allowed_outputs_are_not_denied(ptu, tmp_path: Path, file_path):
    """PLANNING §許可 の出力先は DENY されない（等級は従来どおり PM / SE）。"""
    level, reason = ptu._determine_by_path(
        file_path, _REPO_ROOT, _phase_file(tmp_path, "PLANNING")
    )
    assert level != "DENY", f"{file_path!r} が誤って DENY された（{reason}）"


def test_settings_json_is_not_denied_but_stays_pm(ptu, tmp_path: Path):
    """`.claude/settings*.json` は本 deny の対象外（意図的）。

    統治ファイルであり既に PM 級パスで、AUTONOMOUS では FR-9 が別系統で deny する。
    「プロジェクトのビルド設定」を対象とする本条項の射程とは別物であるため、
    列挙に含めない。
    """
    level, _reason = ptu._determine_by_path(
        ".claude/settings.json", _REPO_ROOT, _phase_file(tmp_path, "PLANNING")
    )
    assert level == "PM"


# --- 境界: 列挙外は「許可」の意味ではない --------------------------------------


def test_unenumerated_config_file_is_not_denied(ptu, tmp_path: Path):
    """列挙外の設定ファイルは DENY されない（**これは許可の意味ではない**）。

    条文は「等」と開いた列挙で書かれており、機構は ADR-0008 D4 に従って閉じた集合で
    実装する。両者の差分は**機構が捕捉していない領域**であり、条文側の禁止は有効。
    この境界を沈黙させないために本テストを置く（BALTHASAR 指摘 / 過少ブロックの沈黙）。

    `.gitleaks.toml` は実在するがツール設定であり、本条項が想定する
    「プロジェクトのビルド・依存設定」とは性格が異なるため列挙していない。
    """
    level, _reason = ptu._determine_by_path(
        ".gitleaks.toml", _REPO_ROOT, _phase_file(tmp_path, "PLANNING")
    )
    assert level != "DENY"


def test_basename_match_is_not_substring_match(ptu, tmp_path: Path):
    """basename 完全一致であり部分一致ではない（誤 deny の回帰）。"""
    for file_path in (
        "docs/artifacts/pyproject.toml.md",
        "docs/specs/x/my-package.json.md",
        "docs/artifacts/notes-about-pyproject.toml.md",
    ):
        level, reason = ptu._determine_by_path(
            file_path, _REPO_ROOT, _phase_file(tmp_path, "PLANNING")
        )
        assert level != "DENY", f"{file_path!r} が誤って DENY された（{reason}）"


# --- Outbound Write Ban との優先順位 ------------------------------------------


def test_outbound_ban_takes_precedence_over_planning_deny(ptu, tmp_path: Path):
    """Outbound Write Ban はフェーズ非依存で最優先（PLANNING でも理由が上書きされない）。"""
    level, reason = ptu._determine_by_path(
        r"D:\work7\Fable-Alembic\pyproject.toml",
        _REPO_ROOT,
        _phase_file(tmp_path, "PLANNING"),
    )
    assert level == "DENY"
    assert "Outbound Write Ban" in reason
