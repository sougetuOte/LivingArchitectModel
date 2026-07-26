"""M-1 W4-M1-T1: update-model skill 整合検証テスト.

`.claude/skills/update-model/SKILL.md` が、判断ロジックを含まない薄い順序表として
作成されており、記述されている手順が実在するスクリプト・ルールファイルを正しく
指していることを検証する（FR-13 受け入れ条件 3 / design.md §8.2 準拠）。

- FR-13 受け入れ条件 1: 判断ロジック（if/for/while を含む python コードブロック）を
  skill 内に実装していないこと
- FR-13 受け入れ条件 2: 各ステップが既存スクリプト・コマンドの呼び出しとして記述され、
  言及先が実在すること
- FR-14 受け入れ条件 2: ステップ 2（model-roster.md 更新）の直後に ADR-0001 確認
  ステップが位置すること（順序の検証）
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_PATH = REPO_ROOT / ".claude/skills/update-model/SKILL.md"

# 6 ステップの内容を特定するためのマーカー（design.md §8.2 / tasks.md W4-M1-T1 の
# 手順表と対応）。各マーカーは skill 本文中に一意に出現する見出し語を想定する。
_STEP_MARKERS = [
    "ステップ1",
    "ステップ2",
    "ステップ2直後",
    "ステップ3",
    "ステップ4",
    "ステップ5",
    "ステップ6",
]

# スクリプト参照抽出: `.claude/scripts/<filename>.py` 形式の具体的なファイル名のみを
# 対象とする（`.claude/scripts/*.py` のような glob 表記は意図的な言及であり対象外）。
_SCRIPT_REF_PAT = re.compile(r"\.claude/scripts/([A-Za-z0-9_-]+\.py)")

# ルールファイル参照抽出: `.claude/rules/<path>.md` 形式の具体的なファイル名のみを
# 対象とする。
_RULE_REF_PAT = re.compile(r"\.claude/rules/([A-Za-z0-9_./-]+\.md)")

# python コードブロック（```python ... ```）の抽出。
_PYTHON_CODE_BLOCK_PAT = re.compile(r"```python\n(.*?)```", re.DOTALL)

# 判断ロジックとみなす制御構文キーワード（単語境界付き）。
_CONTROL_FLOW_PAT = re.compile(r"\b(if|for|while)\b")


def _read_skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8", errors="replace")


def test_skill_file_exists():
    """update-model skill の SKILL.md が実在すること."""
    assert SKILL_PATH.is_file(), f"{SKILL_PATH} が存在しません"


def test_skill_contains_all_six_steps():
    """6 ステップすべてのマーカーが SKILL.md 本文に含まれること."""
    text = _read_skill_text()
    missing = [marker for marker in _STEP_MARKERS if marker not in text]
    assert not missing, f"以下のステップマーカーが SKILL.md に見つかりません: {missing}"


def test_step2_immediately_followed_by_adr0001_check():
    """ステップ 2（model-roster.md 更新）の直後にステップ 2 直後（ADR-0001 確認）が位置し、
    その後にステップ 3（verify_model_reference 実行）が続くこと（順序の検証 / FR-14）."""
    text = _read_skill_text()
    idx_step2 = text.index("ステップ2")
    idx_step2_after = text.index("ステップ2直後")
    idx_step3 = text.index("ステップ3")
    assert idx_step2 < idx_step2_after < idx_step3, (
        "ステップ順序が想定と異なります: "
        f"ステップ2={idx_step2}, ステップ2直後(ADR-0001)={idx_step2_after}, ステップ3={idx_step3}"
    )


def test_step2_after_marker_mentions_adr0001():
    """ステップ 2 直後のブロックが ADR-0001 の制約に言及していること（FR-14 受け入れ条件 2）."""
    text = _read_skill_text()
    idx_step2_after = text.index("ステップ2直後")
    idx_step3 = text.index("ステップ3")
    block = text[idx_step2_after:idx_step3]
    assert "ADR-0001" in block, "ステップ2直後ブロックに ADR-0001 への言及がありません"


def test_referenced_scripts_exist():
    """SKILL.md が言及する `.claude/scripts/*.py` 具体ファイルが実在すること."""
    text = _read_skill_text()
    referenced = sorted(set(_SCRIPT_REF_PAT.findall(text)))
    assert referenced, "SKILL.md からスクリプト参照が 1 件も抽出できませんでした"
    missing = [
        name for name in referenced if not (REPO_ROOT / ".claude/scripts" / name).is_file()
    ]
    assert not missing, f"以下のスクリプトが実在しません: {missing}"


def test_referenced_rules_exist():
    """SKILL.md が言及する `.claude/rules/*.md` 具体ファイルが実在すること."""
    text = _read_skill_text()
    referenced = sorted(set(_RULE_REF_PAT.findall(text)))
    assert referenced, "SKILL.md からルールファイル参照が 1 件も抽出できませんでした"
    missing = [
        name for name in referenced if not (REPO_ROOT / ".claude/rules" / name).is_file()
    ]
    assert not missing, f"以下のルールファイルが実在しません: {missing}"


def test_skill_has_no_python_control_flow_code_blocks():
    """SKILL.md 内に if/for/while を含む python コードブロックが存在しないこと
    （FR-13 受け入れ条件 1: 判断ロジックを skill 内に実装しない）."""
    text = _read_skill_text()
    python_blocks = _PYTHON_CODE_BLOCK_PAT.findall(text)
    offending = [block for block in python_blocks if _CONTROL_FLOW_PAT.search(block)]
    assert not offending, f"判断ロジックを含む python コードブロックが検出されました: {offending}"


def test_skill_mentions_py_invoke_relative_form():
    """python 呼び出しは skill 内 bash command の form（相対パス）に統一されていること
    （CLAUDE.md § Python Invocation Convention / context 別 form 準拠）."""
    text = _read_skill_text()
    assert "bash .claude/scripts/py_invoke.sh" in text
    assert "$CLAUDE_PROJECT_DIR" not in text
