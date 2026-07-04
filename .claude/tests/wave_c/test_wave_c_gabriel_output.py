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
from pathlib import Path

import jsonschema
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"

# design.md §3 の JSON スキーマ完全定義（そのまま転記）。
# additionalProperties: false により、未定義フィールドの混入も検出する。
GABRIEL_OUTPUT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "GabrielOutput",
    "type": "object",
    "required": [
        "verdict",
        "severity",
        "affected_atoms",
        "reasoning",
        "recommended_action",
        "confidence",
    ],
    "additionalProperties": False,
    "properties": {
        "verdict": {
            "type": "string",
            "enum": ["confirmed", "refuted", "inconclusive"],
        },
        "severity": {
            "type": "string",
            "enum": ["critical", "warning", "info"],
        },
        "affected_atoms": {
            "type": "array",
            "items": {"type": "string"},
        },
        "reasoning": {
            "type": "string",
            "minLength": 200,
            "maxLength": 1000,
        },
        "recommended_action": {
            "type": "string",
            "enum": ["proceed", "re-magi", "abort"],
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
        },
    },
}


class CrossFieldConstraintError(ValueError):
    """クロスフィールド制約違反を表す例外（JSON schema だけでは表現できない制約）。"""


def validate_gabriel_output(data: dict) -> None:
    """gabriel 出力の完全な契約検証を行う。

    1. JSON schema（draft-07）検証（design.md §3）
    2. クロスフィールド制約検証（FR-W-C-6 / design.md §3 フィールド制約テーブル）

    いずれかに違反する場合は例外を送出する。
    Silent Failure を避けるため、違反時は必ず例外を投げる（None 等での握りつぶし禁止）。
    """
    jsonschema.validate(instance=data, schema=GABRIEL_OUTPUT_SCHEMA)
    _validate_cross_field_constraints(data)


def _validate_cross_field_constraints(data: dict) -> None:
    """FR-W-C-6 / design.md §3 のクロスフィールド制約を検証する。"""
    verdict = data["verdict"]
    severity = data["severity"]
    affected_atoms = data["affected_atoms"]
    recommended_action = data["recommended_action"]
    confidence = data["confidence"]

    # AC-W-C-8: confidence < 0.3 の場合、verdict は inconclusive でなければならない
    if confidence < 0.3 and verdict != "inconclusive":
        raise CrossFieldConstraintError(
            f"confidence={confidence} (<0.3) requires verdict=inconclusive, "
            f"got verdict={verdict!r}"
        )

    # AC-W-C-9: affected_atoms=[] の場合、verdict は refuted であってはならない
    if verdict == "refuted" and not affected_atoms:
        raise CrossFieldConstraintError(
            "verdict=refuted requires non-empty affected_atoms, got []"
        )

    # design.md §3: verdict=confirmed または inconclusive の場合、severity は info
    if verdict in ("confirmed", "inconclusive") and severity != "info":
        raise CrossFieldConstraintError(
            f"verdict={verdict!r} requires severity=info, got severity={severity!r}"
        )

    # design.md §3: severity=critical の場合、recommended_action は re-magi または abort
    if severity == "critical" and recommended_action not in ("re-magi", "abort"):
        raise CrossFieldConstraintError(
            "severity=critical requires recommended_action in "
            f"{{'re-magi', 'abort'}}, got {recommended_action!r}"
        )


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
