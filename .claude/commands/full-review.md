---
description: "並列監査 + 全修正 + 検証の一気通貫レビュー"
---

# /full-review - 並列監査 + 全修正

引数: 対象ファイルまたはディレクトリ（必須）

## /auditing との使い分け

- `/auditing`: フェーズ切替。AUDITING モードに入り、手動で段階的に監査
- `/full-review`: ワンショット実行。並列監査 -> 修正 -> 検証を一気に完了

## Phase 1: 並列監査

対象に対して以下のサブエージェントを並列起動:

| エージェント | 観点 |
|-------------|------|
| `code-reviewer` (1) | ソースコード品質（命名、構造、エラー処理） |
| `code-reviewer` (2) | テストコード品質（網羅性、可読性、テストパターン） |
| `quality-auditor` | アーキテクチャ・仕様整合性（依存関係、仕様ドリフト） |

プロジェクト規模に応じてエージェント構成を調整可能。
小規模の場合は `code-reviewer` x1 + `quality-auditor` x1 でもよい。

各エージェントは独立した監査レポートを生成する。

## Phase 2: レポート統合

1. 各エージェントの結果を統合
2. 重複 Issue を排除
3. 重要度分類: Critical / Warning / Info
4. 統合レポートをユーザーに提示し、修正方針の承認を得る

```
=== 監査統合レポート ===
Critical: X件 / Warning: X件 / Info: X件

[C-1] Critical: <内容> (file:line)
[W-1] Warning: <内容> (file:line)
...

修正に進みますか？（承認 / 一部除外 / 中止）
```

## Phase 3: 全修正（audit-fix-policy）

承認後、以下のポリシーで全 Issue を修正:

- **A-1**: 全重篤度（Critical / Warning / Info）に対応する
- **A-2**: 対応不可の Issue は理由 + 追跡先 + 暫定対策を明記
- **A-3**: 仕様ズレが発見された場合は `docs/specs/` も同時修正
- **A-4**: 修正は1件ずつ、テストが壊れないことを確認しながら進める

## Phase 4: 検証

全修正完了後、以下の3点検証を実行:

1. テスト: 全テストが PASSED
2. lint: lint エラーがゼロ（lint が設定されている場合）
3. 仕様突合: 修正した箇所の仕様書との整合性を再確認

検証に失敗した場合は修正 -> 再検証のループを回す（最大2回）。

## Phase 5: 完了報告

```
=== Full Review 完了 ===

Before: Critical X / Warning X / Info X
After:  Critical 0 / Warning 0 / Info X（対応不可: X件）

修正ファイル: X件
テスト: PASSED (X tests)
lint: PASSED

対応不可 Issue:
- [I-3] <理由> → 追跡先: docs/tasks/xxx.md
```
