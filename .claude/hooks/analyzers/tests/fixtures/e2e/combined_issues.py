"""E2E テストフィクスチャ: 複合 - Critical + Warning + Security 各1箇所

仕込み箇所:
  FIXTURE-ISSUE-1 (line ~16): process_order — Critical: Silent Failure
  FIXTURE-ISSUE-2 (line ~21): validate_and_process — Warning: Long Function (51行超)
  FIXTURE-ISSUE-3 (line ~80): DB_PASSWORD — Security: Hardcoded Password (bandit B105)
"""
from __future__ import annotations

import json


def process_order(order_id: str) -> dict:
    try:
        return _fetch_order(order_id)
    except Exception:
        # FIXTURE-ISSUE-1: Critical - Silent Failure — 例外握りつぶし
        return {}


# FIXTURE-ISSUE-2: Warning - Long Function — 検証 + 処理 + レポートを1関数に詰め込む (51行超)
def validate_and_process(items: list[dict]) -> dict:
    # ステップ1: 入力チェック
    if not items:
        raise ValueError("items is empty")

    if not isinstance(items, list):
        raise TypeError("items must be a list")

    # ステップ2: 各アイテムのバリデーション
    validated = []
    errors = []
    for idx, item in enumerate(items):
        if "id" not in item:
            errors.append(f"item[{idx}]: missing id")
            continue
        if "price" not in item:
            errors.append(f"item[{idx}]: missing price")
            continue
        price = item["price"]
        if not isinstance(price, (int, float)):
            errors.append(f"item[{idx}]: price must be numeric")
            continue
        if price < 0:
            errors.append(f"item[{idx}]: price must be non-negative")
            continue
        validated.append(item)

    # ステップ3: 集計
    total = sum(item["price"] for item in validated)
    count = len(validated)
    avg = total / count if count > 0 else 0.0

    # ステップ4: 結果フォーマット
    return {
        "validated_count": count,
        "error_count": len(errors),
        "errors": errors,
        "total_price": total,
        "average_price": avg,
        "items": validated,
    }


# FIXTURE-ISSUE-3: Security - Hardcoded Password (bandit B105)
DB_PASSWORD = "p@ssw0rd_production"  # noqa: S105


def _fetch_order(order_id: str) -> dict:
    raise NotImplementedError
