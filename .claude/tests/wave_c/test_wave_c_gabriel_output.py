"""gabriel 出力契約テスト (WC-B5-T4)

design.md §3 の JSON スキーマ（draft-07）+ クロスフィールド制約（FR-W-C-6）を
mock/fixture ベースで検証する契約テスト。実 LLM 呼び出しは行わない。

fixtures/*.json は「gabriel 出力を模した stub データ」であり、
このテストは「stub データが仕様通りの制約を満たすか（または意図的な違反を
バリデータが正しく検出できるか）」を確認する。

参照:
- docs/specs/magi-v2-gabriel/design.md §3 (JSON スキーマ完全定義)
- docs/specs/magi-v2-gabriel/requirements.md FR-W-C-2 / FR-W-C-6
- docs/specs/magi-v2-gabriel/tasks.md §6 WC-B5-T4 (テストケース 8 件)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# 契約の正本は本番モジュール側にある（2026-09-05 移設 / /full-review iter0 C-5）。
# 以前はこのテストファイル内に転記した定義を、同じファイル内の fixture に対して
# 通しているだけで、本番から import される経路が 0 件だった。
from magi_dispatch import (  # noqa: E402
    GABRIEL_OUTPUT_SCHEMA,
    CrossFieldConstraintError,
    validate_gabriel_output,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
_SKILL_MD = Path(__file__).resolve().parent.parent.parent / "skills" / "magi" / "SKILL.md"


def _load_fixture(filename: str) -> dict:
    path = FIXTURES_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# 1. verdict=confirmed で confidence >= 0.3 -> schema PASS
# ---------------------------------------------------------------------------
def test_confirmed_with_sufficient_confidence_passes():
    data = _load_fixture("01_confirmed.json")
    validate_gabriel_output(data)  # 例外が出なければ PASS
    assert data["verdict"] == "confirmed"
    assert data["confidence"] >= 0.3


# ---------------------------------------------------------------------------
# 2. verdict=refuted & severity=critical で affected_atoms 非空 -> schema PASS
# ---------------------------------------------------------------------------
def test_refuted_critical_with_affected_atoms_passes():
    data = _load_fixture("02_refuted_critical.json")
    validate_gabriel_output(data)
    assert data["verdict"] == "refuted"
    assert data["severity"] == "critical"
    assert data["affected_atoms"]
    assert data["recommended_action"] in ("re-magi", "abort")


# ---------------------------------------------------------------------------
# 3. verdict=refuted & severity=warning で affected_atoms 非空 -> schema PASS
# ---------------------------------------------------------------------------
def test_refuted_warning_with_affected_atoms_passes():
    data = _load_fixture("03_refuted_warning.json")
    validate_gabriel_output(data)
    assert data["verdict"] == "refuted"
    assert data["severity"] == "warning"
    assert data["affected_atoms"]


# ---------------------------------------------------------------------------
# 4. verdict=refuted & severity=info -> schema PASS
# ---------------------------------------------------------------------------
def test_refuted_info_passes():
    data = _load_fixture("04_refuted_info.json")
    validate_gabriel_output(data)
    assert data["verdict"] == "refuted"
    assert data["severity"] == "info"


# ---------------------------------------------------------------------------
# 5. verdict=inconclusive -> schema PASS
# ---------------------------------------------------------------------------
def test_inconclusive_passes():
    data = _load_fixture("05_inconclusive.json")
    validate_gabriel_output(data)
    assert data["verdict"] == "inconclusive"
    assert data["severity"] == "info"


# ---------------------------------------------------------------------------
# 6. confidence=0.25 (<0.3) かつ verdict!=inconclusive -> バリデータ側で拒否 (AC-W-C-8)
# ---------------------------------------------------------------------------
def test_low_confidence_with_confirmed_verdict_is_rejected():
    data = _load_fixture("06_low_confidence_invalid.json")
    assert data["confidence"] < 0.3
    assert data["verdict"] != "inconclusive"
    with pytest.raises(CrossFieldConstraintError, match="confidence"):
        validate_gabriel_output(data)


# ---------------------------------------------------------------------------
# 7. verdict=refuted & affected_atoms=[] -> バリデータ側で拒否 (AC-W-C-9)
# ---------------------------------------------------------------------------
def test_refuted_with_empty_affected_atoms_is_rejected():
    data = _load_fixture("07_empty_atoms_refuted_invalid.json")
    assert data["verdict"] == "refuted"
    assert data["affected_atoms"] == []
    with pytest.raises(CrossFieldConstraintError, match="affected_atoms"):
        validate_gabriel_output(data)


# ---------------------------------------------------------------------------
# 8. timeout stub (gabriel 応答なし想定 -> fallback で verdict=inconclusive) -> schema PASS
# ---------------------------------------------------------------------------
def test_timeout_fallback_passes():
    data = _load_fixture("08_timeout_fallback.json")
    validate_gabriel_output(data)
    assert data["verdict"] == "inconclusive"
    assert data["confidence"] == 0.0


# ---------------------------------------------------------------------------
# 追加: 全 fixture の reasoning が 200〜1000 字の範囲内であることを一括確認
# (NFR-W-C-2 / FR-W-C-2 のフォーマット準拠率確認の補助)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "filename",
    [
        "01_confirmed.json",
        "02_refuted_critical.json",
        "03_refuted_warning.json",
        "04_refuted_info.json",
        "05_inconclusive.json",
        "06_low_confidence_invalid.json",
        "07_empty_atoms_refuted_invalid.json",
        "08_timeout_fallback.json",
    ],
)
def test_all_fixtures_reasoning_length_within_bounds(filename):
    data = _load_fixture(filename)
    assert 200 <= len(data["reasoning"]) <= 1000


# ---------------------------------------------------------------------------
# 追加 (2026-09-05 / /full-review iter0 C-5): 契約の正本が SKILL.md の宣言と一致する
#
# スキーマは design.md からの手動転記に依存しており、転記元との乖離を検出する経路が
# 無かった。SKILL.md §Step 4 の「required フィールド 6 件」という宣言を証人として
# 使い、本番側スキーマがそれと食い違ったら赤くする。
# ---------------------------------------------------------------------------
def test_production_schema_required_fields_match_skill_md():
    """`GABRIEL_OUTPUT_SCHEMA` の required が SKILL.md の宣言 6 件と一致する。"""
    text = _SKILL_MD.read_text(encoding="utf-8")
    declared = [
        name
        for name in (
            "verdict",
            "severity",
            "affected_atoms",
            "reasoning",
            "recommended_action",
            "confidence",
        )
        if name in text
    ]
    assert len(declared) == 6, f"SKILL.md に載っていないフィールドがある: {declared}"
    assert set(GABRIEL_OUTPUT_SCHEMA["required"]) == set(declared)
