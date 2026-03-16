# E2E テストフィクスチャ

Plan E FR-E3b に基づく E2E 検出率テスト用のフィクスチャ。

## ファイル一覧

| ファイル | Issue 種別 | 仕込み箇所数 |
|:--------|:----------|:-----------|
| `critical_silent_failure.py` | Critical: Silent Failure | 3 |
| `warning_long_function.py` | Warning: Long Function (51行+) | 2 |
| `security_hardcoded_password.py` | Security: ハードコードパスワード (bandit B105/B106) | 3 |
| `combined_issues.py` | Critical + Warning + Security 各1 | 3 |

## Issue マーカー規則

各 Issue 箇所には `# FIXTURE-ISSUE-N:` コメントを付与する。
フィクスチャの変更は PM 級扱い（テスト基準の変更に相当）。

## 設計原則

- 各ファイルは単一の Issue 種別に特化（`combined_issues.py` を除く）
- Security フィクスチャは bandit B105/B106 が確実に検出するパターンを使用
- フィクスチャは意図的にバグを含む（テスト用途のため lint 警告は無視してよい）

## 参照

- 仕様: `docs/specs/scalable-code-review-phase5-spec.md` FR-E3b
- 設計: `docs/design/scalable-code-review-design.md` Section 6.4.3
