"""Outbound Write Ban の R3 二重化 TDD（HGA #24 手 2 / W1）.

`.claude/rules/fable-l3-protocol.md` §2 の **Outbound Write Ban**
（`D:\\work7\\Fable-Alembic\\` 配下への書込・編集の禁止 / 全レベル共通 **MUST NOT**）は、
制定（2026-07-07）以来 **条文のみで機構を持たなかった**。

実測（2026-07-27）: 当該パスへの書込は `normalize_path` で `__out_of_root__/` マーカーが
付き、`_PM_OUT_OF_ROOT_PATTERN` により **PM 級（ask ダイアログ）** として扱われる。
すなわち「ユーザーが承認すれば書ける」状態であり、条文の **MUST NOT（絶対禁止）** と
格差がある。かつ違反しても誰も気づかない = **静かに潜伏する失敗クラス**（HGA #17 crux 3）
であり、同 crux の基準では**永久に運用移管不可 = 機構化が必須**の類に当たる。

設計上の位置づけ:
- clause-gate Step 1 を全通過（入力 = tool_input のパス = スキーマ契約あり /
  `relative_to` による機械判定 / 意味解釈不要）
- 軸 1 = ユーザー意思（triage `#2-01`）/ 軸 3 = 不可逆（他リポジトリの破壊）
- 設計 §1.3 により **不可逆ガードは R1 + R3 の複宛先を許す** → 条文は残したまま機構を建てる

MAGI 記録: `docs/artifacts/2026-07-27-magi-planning-hook.md`
（gabriel 第 1 回 `refuted/critical` → 再 MAGI → 第 2 回 `refuted/warning/proceed`）

**gabriel G-3 が要求した境界条件テストを本ファイルが担う**:
(a) セパレータ正規化（`\\` / `/` / 相対 / symlink）—— `normalize_path` は out-of-root 時に
    **生の file_path 文字列**を保持する（`_hook_utils.py:218-220`）ため、素朴な前方一致
    regex では `D:\\...` と `D:/...` が別文字列となり片方が検知漏れする
(b) `etc-to-alembic` の誤 deny —— 部分一致で実装すると **allow 対である handoff 経路**を
    殺す（ADR-0008 D1 違反）
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
        "pre_tool_use_for_ban_test", _HOOKS_DIR / "pre-tool-use.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def ptu():
    return _load_pre_tool_use()


@pytest.fixture
def nonexistent_phase_file(tmp_path: Path) -> Path:
    """存在しない phase ファイル（`_read_current_phase` は "" を返す）。

    Outbound Write Ban は**フェーズ非依存**であることを示すため、
    フェーズが読めない状態でも deny されねばならない。
    """
    return tmp_path / "no-such-phase.md"


# --- (a) セパレータ 4 形すべてで deny されること -------------------------------


@pytest.mark.parametrize(
    "file_path",
    [
        r"D:\work7\Fable-Alembic\knowledge\Fable行動規範.md",
        "D:/work7/Fable-Alembic/knowledge/Fable行動規範.md",
        r"D:\work7\Fable-Alembic\README.md",
        "D:/work7/Fable-Alembic/",
        "../Fable-Alembic/knowledge/x.md",
        r"..\Fable-Alembic\knowledge\x.md",
    ],
)
def test_outbound_write_ban_denies_all_separator_forms(
    ptu, nonexistent_phase_file, file_path
):
    """`Fable-Alembic` 配下は表記形によらず DENY となる。

    gabriel G-3(a): out-of-root は生の file_path を保持するため、素朴な前方一致では
    セパレータ違いを取りこぼす。実装は `Path.resolve()` による正規化を経ること。
    """
    level, reason = ptu._determine_by_path(
        file_path, _REPO_ROOT, nonexistent_phase_file
    )
    assert level == "DENY", f"{file_path!r} が DENY にならない（level={level} / {reason}）"
    assert "Outbound Write Ban" in reason


def test_outbound_write_ban_is_phase_independent(ptu, tmp_path: Path):
    """フェーズによらず DENY（既存の FR-9 deny が AUTONOMOUS 限定なのと対照的）。

    条文は「全レベル共通 MUST NOT」であり、フェーズに条件づけられていない。
    """
    for phase in ("PLANNING", "BUILDING", "AUDITING", "AUTONOMOUS"):
        phase_file = tmp_path / f"phase-{phase}.md"
        phase_file.write_text(f"# Current Phase\n\n**{phase}**\n", encoding="utf-8")
        level, reason = ptu._determine_by_path(
            r"D:\work7\Fable-Alembic\knowledge\x.md", _REPO_ROOT, phase_file
        )
        assert level == "DENY", f"phase={phase} で DENY にならない"


# --- (b) allow 対: handoff 経路を殺さないこと（ADR-0008 D1） --------------------


@pytest.mark.parametrize(
    "file_path",
    [
        r"D:\work7\etc-to-alembic\handoff\observation-2026-07-27.md",
        "D:/work7/etc-to-alembic/handoff/observation-2026-07-27.md",
        r"D:\work7\etc-to-alembic\README.md",
        "D:/work7/etc-to-alembic/",
    ],
)
def test_etc_to_alembic_is_not_denied(ptu, nonexistent_phase_file, file_path):
    """`etc-to-alembic` は DENY されない（**allow 対** / ADR-0008 D1）。

    gabriel G-3(b): 実装が `"alembic"` の部分一致（case-insensitive 含む）で
    書かれると、条文が明示的に許可した唯一の受け渡し経路を殺す。

    なお「DENY されない」= 素通しではない。out-of-root として **PM 級（ask）** に
    留まる（`_PM_OUT_OF_ROOT_PATTERN` / R1-I18 の意図的設計）。PG 級 auto allow に
    しないのは、リポジトリ外書込を無確認で通すことが R1-I18 の「安全側維持」
    判断を覆すため（設計判断は MAGI ログ §Step 5 に記録）。
    """
    level, reason = ptu._determine_by_path(
        file_path, _REPO_ROOT, nonexistent_phase_file
    )
    assert level != "DENY", f"{file_path!r} が誤って DENY された（{reason}）"
    assert level == "PM", f"{file_path!r} は out-of-root PM 級であるべき（level={level}）"


# --- 既存挙動の回帰（リポジトリ内は無影響） ------------------------------------


@pytest.mark.parametrize(
    ("file_path", "expected_level"),
    [
        (".claude/rules/fable-l3-protocol.md", "PM"),
        ("docs/specs/x/design.md", "PM"),
        ("docs/artifacts/x.md", "SE"),
        ("CLAUDE.md", "PM"),
    ],
)
def test_in_repo_paths_are_unaffected(
    ptu, nonexistent_phase_file, file_path, expected_level
):
    """リポジトリ内パスの判定は本変更で一切変わらない（Zero-Regression）。"""
    level, _reason = ptu._determine_by_path(
        file_path, _REPO_ROOT, nonexistent_phase_file
    )
    assert level == expected_level


# --- drift 検査: 機構と条文の SSOT 整合 ---------------------------------------


def test_banned_root_matches_rule_document():
    """hook の禁止ルートが `fable-l3-protocol.md` の記載と一致する。

    条文側（§2 / §0）が SSOT であり、パス移動時は条文のみ更新すれば足りるという
    設計になっている。機構側が別の値を持つと **沈黙して守らなくなる**ため、
    文字列の存在を突合する（**部分文字列の存在確認のみ**で、prose の構造解析は
    行わない —— rule-001 / rule-002 型の drift 保守負債を作らないため）。
    """
    ptu = _load_pre_tool_use()
    rule_text = (_REPO_ROOT / ".claude" / "rules" / "fable-l3-protocol.md").read_text(
        encoding="utf-8"
    )
    for banned in ptu._OUTBOUND_WRITE_BAN_ROOTS:
        # 条文は Windows 表記（`D:\work7\Fable-Alembic\`）で書かれている。
        windows_form = str(banned).replace("/", "\\")
        assert windows_form in rule_text, (
            f"禁止ルート {windows_form!r} が fable-l3-protocol.md に見つからない。"
            "条文と機構が drift している可能性がある"
        )
