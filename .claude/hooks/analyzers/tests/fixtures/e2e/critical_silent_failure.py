"""E2E テストフィクスチャ: Critical - Silent Failure (3箇所)

仕込み箇所:
  FIXTURE-ISSUE-1 (line ~12): process_payment — 例外握りつぶし
  FIXTURE-ISSUE-2 (line ~23): load_config — 空 dict で隠蔽
  FIXTURE-ISSUE-3 (line ~38): DataProcessor.transform — エラースキップ
"""
from __future__ import annotations

import json


def process_payment(amount: float) -> bool:
    try:
        result = _call_payment_api(amount)
        return result.success
    except Exception:
        # FIXTURE-ISSUE-1: Silent Failure — 例外握りつぶし
        return False


def load_config(path: str) -> dict:
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        # FIXTURE-ISSUE-2: Silent Failure — 空 dict で隠蔽
        return {}


class DataProcessor:
    def transform(self, data: list) -> list:
        results = []
        for item in data:
            try:
                results.append(self._process_item(item))
            except ValueError:
                # FIXTURE-ISSUE-3: Silent Failure — エラースキップ
                pass
        return results

    def _process_item(self, item):
        return item * 2


def _call_payment_api(amount):
    raise NotImplementedError
