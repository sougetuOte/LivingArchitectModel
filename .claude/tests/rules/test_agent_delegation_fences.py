"""委譲受領側の恒久制約が全 agent 定義に配送されていることの検査。

`.claude/rules/model-delegation-prompting.md` は 2026-07-26 に R1（常駐）から
R2（条件ロード）へ降格した。降格の条件は「実際の配送先を明記する」ことであり
（誕生ゲート設計 §1.2 の R2 要件 (ii)）、受領側に効く条項は `.claude/agents/**`
の各定義へ移設した。

本テストはその配送を出口で固定する。設計 §8 の既知の弱点 WC-1（「R2 沈殿池」=
条項が存在するのに二度と読まれない）のうち、**omission による潜伏**をこの
ファイル集合については塞ぐ。新規 agent を追加してブロックを入れ忘れると落ちる。

台帳: docs/artifacts/clause-gate-ledger.md §B 取引 #3-#7 / §C 機構 #3
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"

# 全 agent に配送する共通制約（移設元: model-delegation-prompting.md §2-2 / 2-5 / 2-6 / 2-7）。
# 照合は短い特徴語で行う（文面の微修正で落ちないように / 意味解釈は含まない）。
COMMON_MARKERS = (
    "直接の実行者",  # Direct Executor（§2-5 / 再委譲・meta-response 早期終了の防止）
    "依頼外の成果物を作らない",  # 下方向フェンス（§2-2）
    "「未検証」と明記",  # grounding bolt-on（§2-6）
    "境界からの逸脱を自己申告",  # 親側検収の予告（§2-7）
)

# レビュー・監査系のみに配送する追加制約（移設元: §3 / roster §3 デルタ 6）。
REVIEW_MARKER = "確信度で絞らない"
REVIEW_AGENTS = ("code-reviewer", "gabriel", "quality-auditor")


def _agent_files() -> "list[Path]":
    return sorted(AGENTS_DIR.glob("*.md"))


def test_agents_dir_is_not_empty():
    assert _agent_files(), "agent 定義が 1 件も見つからない: {0}".format(AGENTS_DIR)


def test_review_agents_exist():
    """REVIEW_AGENTS の名前が実在すること（改名時に本テストが空振りしないため）。"""
    names = {path.stem for path in _agent_files()}
    missing = sorted(set(REVIEW_AGENTS) - names)
    assert not missing, "REVIEW_AGENTS に実在しない名前がある: {0}".format(missing)


@pytest.mark.parametrize("path", _agent_files(), ids=lambda p: p.stem)
def test_common_fences_are_delivered(path):
    """全 agent 定義が受領側の恒久制約 4 件を持つこと。

    落ちた場合は `.claude/agents/` の当該ファイルに「受領側の恒久制約」節を
    追加する（既存 12 件と同一文面 / 誕生ゲートの再判定は不要 = 配送の是正）。
    """
    text = path.read_text(encoding="utf-8")
    missing = [marker for marker in COMMON_MARKERS if marker not in text]
    assert not missing, (
        "{0}: 受領側の恒久制約が未配送: {1}"
        "（R2 移設先 = 本ファイル / 台帳 §B #3-#6）".format(path.name, missing)
    )


@pytest.mark.parametrize("name", REVIEW_AGENTS)
def test_coverage_first_is_delivered_to_review_agents(name):
    """レビュー・監査系に coverage-first（デルタ 6 対策）が届いていること。"""
    text = (AGENTS_DIR / "{0}.md".format(name)).read_text(encoding="utf-8")
    assert REVIEW_MARKER in text, (
        "{0}: coverage-first 条項が未配送（roster §3 デルタ 6 = "
        "「高重要度のみ報告」で recall が落ちる / 台帳 §B #7）".format(name)
    )


def test_residual_rule_file_is_conditional_load():
    """移設元ファイルが R2（`paths:` つき）であること。

    R1 に戻ると台帳 §A（TOTAL 90）と乖離し test_clause_gate_ledger.py も落ちるが、
    移設と降格が同一の不動点で守られるよう本ファイルでも検査する。
    """
    rule = REPO_ROOT / ".claude" / "rules" / "model-delegation-prompting.md"
    assert rule.is_file(), "移設元ファイルが存在しない: {0}".format(rule)
    head = rule.read_text(encoding="utf-8").splitlines()[:3]
    assert any(line.startswith("paths:") for line in head), (
        "model-delegation-prompting.md に `paths:` frontmatter がない = R1 に復帰している"
        "（台帳 §A / 誕生ゲート §1.2）"
    )
