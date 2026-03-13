---
description: "振り返り - Wave/Phase完了時の学習サイクル"
---

# Retrospective（振り返り）

Wave または Phase の完了時に実施する構造化振り返り。
発見したパターンを rules/commands/agents に反映し、プロジェクトの学習サイクルを回す。

## 引数

- `/retro wave` — 直近の Wave を振り返る（デフォルト）
- `/retro phase` — Phase 全体を振り返る（Phase 完了時）

## 実行ステップ

### Step 1: スコープ確認

SESSION_STATE.md と git log から対象範囲を特定:

```
--- Retro: スコープ ---
対象: Wave X（YYYY-MM-DD 〜 YYYY-MM-DD）
タスク: T-XX, T-YY, T-ZZ
コミット: N件
テスト: N passed / N% cov
```

### Step 2: 定量分析

以下のメトリクスを収集:

| 指標 | 値 |
|:-----|:---|
| 実装タスク数 | N |
| テスト追加数 | N |
| 監査 Issue 数（修正前） | Critical: N / Warning: N / Info: N |
| 監査 Issue 数（修正後） | Critical: 0 / Warning: 0 / Info: 0 |
| 対応不可 Issue | N件 |
| 仕様書更新数 | N |

### Step 2.5: TDD パターン分析

`.claude/tdd-patterns.log` が存在する場合、以下を実施:

1. ログを読み込み、FAIL→PASS 遷移ペアを抽出
2. 同一テスト名・同一ファイルの繰り返し失敗を集計
3. 頻出パターン（2回以上）があれば:
   - パターンの要約を提示
   - ルール候補（`.claude/rules/auto-generated/draft-NNN.md`）を提案
   - ユーザーが承認/却下を判断（PM級）
4. 分析完了後、`tdd-patterns.log` に `ANALYZED` マーカーを追記:
   ```
   {timestamp}\tANALYZED\tretro\t"analyzed N patterns"
   ```

ログが存在しない場合はこのステップをスキップする。

対応仕様: `docs/specs/tdd-introspection-v2.md` Section 6

### Step 3: 定性分析（KPT）

以下の3カテゴリで振り返る:

```markdown
### Keep（続けること）
- [うまくいったプラクティス]
- [効果的だったツール・コマンド]

### Problem（問題だったこと）
- [つまずいたポイント]
- [時間がかかった作業]
- [再発した不具合パターン]

### Try（次に試すこと）
- [改善案]
- [新しいアプローチ]
```

### Step 4: アクション抽出

定性分析から具体的なアクションを抽出:

```markdown
### 反映先の分類

| アクション | 反映先 | 優先度 |
|:---------|:-------|:------|
| [ルール追加/修正] | `.claude/rules/xxx.md` | 高/中/低 |
| [コマンド改善] | `.claude/commands/xxx.md` | 高/中/低 |
| [エージェント調整] | `.claude/agents/xxx.md` | 高/中/低 |
| [知見の蓄積] | `docs/artifacts/knowledge/xxx.md` | 高/中/低 |
| [ドキュメント更新] | `docs/xxx` | 高/中/低 |
```

### Step 5: 記録

振り返り結果を以下に記録:

- **出力先**: `docs/artifacts/retro-wave-{N}.md`、`docs/artifacts/retro-phase-{N}.md`、またはリリース単位の場合 `docs/artifacts/retro-<version>.md`
- 高優先度のアクションはユーザー承認後に即時反映

### Step 6: 完了報告

```
--- Retro 完了 ---
Keep: X件 / Problem: X件 / Try: X件
アクション: X件（即時反映: X件、次Wave: X件）
記録: docs/artifacts/retro-wave-{N}.md / retro-phase-{N}.md / retro-<version>.md
```

## Phase 振り返り（`/retro phase`）の追加ステップ

Phase 全体の場合、Step 2-3 に加えて以下を実施:

### Phase 横断分析

- 各 Wave の Retro 記録を読み込み、繰り返し出現するパターンを特定
- rules/commands の有効性を評価（導入前後の比較）
- 次 Phase への引き継ぎ事項をまとめる

### 出力

- `docs/artifacts/retro-phase-{N}.md`
- 次 Phase の PLANNING 開始時に参照すべき教訓リスト

## 注意事項

- 振り返りは **批判ではなく学習** が目的
- Problem には必ず Try（改善案）を対にする
- アクションは具体的・実行可能な粒度にする
