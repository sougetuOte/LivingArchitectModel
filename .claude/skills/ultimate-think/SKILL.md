---
name: ultimate-think
description: >
  AoT + Three Agents + Reflection を統合した多層思考スキル。
  複雑な意思決定・設計判断・リスク評価でハルシネーションを抑制する。
  全フェーズ（PLANNING/BUILDING/AUDITING）で利用可能。
  手動起動専用: /ultimate-think で呼び出す。
disable-model-invocation: true
---

# ultimate-think

AoT・Three Agents・Reflection を統合した構造化思考スキル。
SSOT は `docs/internal/06_DECISION_MAKING.md` に維持。本スキルはそのラッパー。

## 実行フロー

```
Phase 0: Grounding → Level 1: AoT → Level 2: Debate → Level 3: Reflection → Synthesis
```

引数 `--level=N`（1/2/3）でレベル明示指定可。省略時は Phase 0 で自動判定。

### Phase 0: Grounding + 複雑度判定

1. 議題から重要キーワードを抽出し、WebSearch を 1-2 回実行する
   - 検索精度は完璧を求めない。失敗時は警告して続行する
2. 複雑度を判定しレベルを選択する:

| レベル | 条件 |
|:---|:---|
| 不要 | 判断ポイントが 2 つ未満 → 「ultimate-think は不要と判断します。従来手法で回答します。」と通知し終了 |
| Level 1 | 判断ポイント 2+、影響範囲が単一ドメイン |
| Level 2 | 影響レイヤー 3+ or 選択肢 3+ |
| Level 3 | 不可逆な決定 or 複数ドメインに跨る高リスク判断 |

3. アンカーファイルを作成する（命名: `docs/memos/YYYY-MM-DD-uthink-{用途}.md`）
   - 同名ファイルが存在する場合は `-v2`, `-v3` を付与する
   - アンカーの詳細フォーマットは [references/anchor-format.md](references/anchor-format.md) を参照

### Level 1: AoT Decomposition

`06_DECISION_MAKING.md` Section 5（AoT）に従い:

1. 問題を Atom に分解する（自己完結性・インターフェース契約・エラー隔離を満たすこと）
2. 依存関係 DAG を作成する
3. アンカーに Atom テーブルと DAG を書き出す

Level 1 のみの場合、各 Atom を個別に処理して Synthesis へ進む。

### Level 2: Three Agents Debate

`06_DECISION_MAKING.md` Section 1-3（Three Agents）に従い:

1. 各 Atom について Divergence → Debate → Convergence を実施する
2. **Mediator のみ**がアンカーに結論を追記する（Single-Writer）
3. Affirmative / Critical は読み取り専用（Multi-Reader）

### Level 3: Reflection Loop

Level 2 完了後、アンカー全体を再検証する:

1. アンカー全体を読み直し、矛盾・見落とし・論理的飛躍を検出する
2. Mediator が修正をアンカーに追記する
3. **安定性検知**: 前回チェックポイントと diff がなければ打ち切り
4. **最大反復回数**: 2 回固定（引数による変更不可）。到達時は強制打ち切り
5. 打ち切り理由をアンカーに記録する

### Synthesis

1. アンカー全体を読み込み、全 Atom の結論を統合する
2. Action Items を抽出・整理する
3. アンカーの Synthesis セクションに記録する
4. ユーザーへ最終報告する

## アンカーファイル管理

| ルール | 内容 |
|:---|:---|
| 保存先 | `docs/memos/` |
| 書き込み権限 | Mediator のみ（Single-Writer） |
| 読み取り権限 | 全 Agent・サブエージェント（Multi-Reader） |
| 削除 | ユーザーのみ可能。スキルによる自動削除は禁止 |
| 保持期間 | 恒久保存（思考過程の記録として） |

## サブエージェント委任

Level 1-2 の各 Atom 処理は Task ツール経由で Sonnet サブエージェントに委任可能。
Level 3 の Reflection は Opus（メインオーケストレーター）が担当する。

## 参照ドキュメント

- `docs/internal/06_DECISION_MAKING.md` — AoT + Three Agents の SSOT
- `docs/specs/ultimate-think.md` — 機能仕様書（FR/NFR/テスト観点）
- [references/anchor-format.md](references/anchor-format.md) — アンカーファイルのテンプレート
