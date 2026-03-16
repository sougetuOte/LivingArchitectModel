# E2E Review Quality Results

Plan E FR-E3 に基づく E2E テストの結果記録。

## ファイル構成

```
docs/artifacts/e2e-results/
├── README.md              # このファイル
├── latest.json            # 最新実行結果（上書き）
├── latest-summary.md      # 人間向けサマリー（上書き）
└── history/               # タイムスタンプ付き履歴
    ├── YYYYMMDD_HHMMSS.json
    └── ...
```

## 実行方法

```bash
# 決定的テストのみ（CI 対象）
pytest .claude/hooks/analyzers/tests/test_e2e_review.py

# LLM 検出率テスト（手動）
pytest -m e2e_llm .claude/hooks/analyzers/tests/test_e2e_review.py

# 収束テスト（手動）
pytest -m e2e_convergence .claude/hooks/analyzers/tests/test_e2e_review.py
```

## latest.json スキーマ

```json
{
  "run_id": "YYYYMMDD_HHMMSS",
  "executed_at": "ISO 8601",
  "test_type": "detection | convergence | scale",
  "overall_status": "passed | failed | skipped",
  "summary": "人間向けサマリー文字列",
  "details": [],
  "elapsed_seconds": 0.0
}
```

## 参照

- 仕様: `docs/specs/scalable-code-review-phase5-spec.md` FR-E3c
- 設計: `docs/design/scalable-code-review-design.md` Section 6.4.4
- テスト: `.claude/hooks/analyzers/tests/test_e2e_review.py`
- フィクスチャ: `.claude/hooks/analyzers/tests/fixtures/e2e/`
