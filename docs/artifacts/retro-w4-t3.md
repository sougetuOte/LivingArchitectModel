# Retrospective: W4-T3 中タスク実機リハーサル

**Date**: 2026-06-17
**Scope**: W4-T3 中タスク実機リハーサル + W6-T1 / W6-T2 並列処理
**Phase**: BUILDING / B-3
**Wave**: W4 (W4-T3) + W6 (W6-T1, W6-T2)
**Facilitator**: Opus 4.8（L1 統括）

---

## 1. スコープ

本セッションで実施した作業の範囲:

- **コミット（5 件）**:
  - `63d0915` docs(specs): handoff-format.md v0.1.0 — lam-orchestrate 受け渡し形式（W6-T1 / FR-10 / AC-15）
  - `481285e` docs(artifacts): W6-T2 DW 排除検証レポート（AC-10 Pass）
  - `4c87c4e` docs(artifacts): W4-T3 中タスク実機リハーサル準備パッケージ
  - `7cc1c39` chore(tasks): docs-stub-sync タスク定義配置（W4-T3 リハーサル用）
  - `a321c3c` docs(specs): tasks.md v1.4.3 — W6-T1 / W6-T2 完了チェック記入
- **追加作業**: `.gitignore` に `.claude/gd-session-state.json` 追加（A1 実施済み）

- **新規ファイル（6 件）**:
  - `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-package.md`
  - `docs/artifacts/W6-T2-dw-exclusion-report.md`
  - `docs/specs/goal-driven-orchestration/handoff-format.md`
  - `docs/tasks/docs-stub-sync/design.md`
  - `docs/tasks/docs-stub-sync/rubric-draft.md`
  - `docs/tasks/docs-stub-sync/task-list.md`
  - `docs/tasks/docs-stub-sync/rubric.md`（リハーサル実行時生成）
  - `.claude/agent-memory/goal-driven-l3-executor/lessons.md`（蒸留結果）
  - `docs/artifacts/retro-w4-t3.md`（本ファイル）

- **変更ファイル（2 件）**:
  - `docs/specs/goal-driven-orchestration/tasks.md`（v1.4.2 → v1.4.3）
  - `docs/artifacts/goal-driven-demo/README.md`（ファイル一覧テーブル追記）

---

## 2. 定量メトリクス

| 項目 | 値 |
|------|-----|
| コミット数 | 5 件（+ .gitignore 編集） |
| リハーサル route | medium |
| ループ回数 | 1（loop_count=0、grader ログ -loop01- より確認） |
| total_tokens | 75,342 / 150,000 (50.2%) |
| grader 判定 | 4/4 Pass |
| L1 最終検収 | 承認（5 項目全充足） |
| l3 乖離 ratio | 0.82（self=6,800 / measured=37,783） |
| l3 subagent_tokens | 37,783 |
| grader subagent_tokens | 37,559 |
| 蒸留 lessons.md | 1 エントリ追記（395 bytes） |
| L1 セッション全体目安 | Opus 4.7 入力 49.7k + 出力 2.6k = 52.3k（リハーサル単独切り出しは不能） |
| l1_ratio | 0.0000（本体トークン未計上・設計通り） |
| サブエージェント消費累計 | ~770k（B: 232k, C: 220k, E: ~108k, F: ~125k, GD全体: ~200k+） |
| TDD パターンログ | 本セッション新規 FAIL→PASS なし（docs のみのため） |

---

## 3. KPT 整理

### Keep（続けること）

1. **3 層体制（Opus 4.8 統括 / Sonnet 実装 / Haiku 採点・軽作業）が本セッション全体で機能**
   - 統括 = Opus 4.8 が Bash/Edit/Write を直接叩かず委譲徹底
   - 同時並列最大 3 で速度確保
   - サブエージェント消費累計 ~770k（B: 232k, C: 220k, E: ~108k, F: ~125k, GD全体: ~200k+）に対し本体（私）は浅く維持
2. **goal-driven リハーサルで L1 役を私が直接担う設計バランス**
   - FR-2「独立した Agent 呼び出し」順守（l3-executor / grader を私が直接 Agent ツールで起動）
   - Bash 系（gd_guard / gd_state 各 API / distill_lessons / .gitignore 編集）は Haiku 委譲
3. **独立採点（Haiku × 3）が成果物を実物突合で検証**
   - B-3 採点が行番号一致まで再確認 → grader 設計の「別コンテキスト独立」が実機でも有効
   - 全 3 件 Pass
4. **乖離検知が設計通り発動**
   - l3 ratio=0.82 を WARN + _divergences 記録（W4-T3 主要観測 #2 達成）

### Problem（問題だったこと）

1. **Sonnet 529 Overloaded × 2 連続（/ship Phase 5）**
   - 起動失敗 → Haiku 代替で commit 5 件実行成功
   - サブエージェント起動の堅牢性に課題
2. **L1 トークン未計上 / リハーサル単独切り出し不能**
   - 本体は subagent_tokens 経由でないため cost_log.l1_tokens=0 / l1_ratio=0 固定
   - PM 使用量表示は「セッション全体」累計（Opus 4.7 入力 49.7k + 出力 2.6k = 52.3k）でリハーサル単独計測は不能
   - 次回はリハーサル直前のスナップショットを PM が記録する運用が必要
3. **gd-session-state.json が .gitignore 未登録だった**
   - 他 state ファイル（lam-loop-state.json / autonomous-state.json）と不統一
   - 本セッションで A 案（.gitignore 追加）で修正
   - 設計時の手当て漏れ
4. **distill_lessons.py が即合格ケースで「未検証」記録**
   - 1 ループ即 pass のとき fail→pass 遷移なし → 自動判定で「未検証・要人間確認」記録
   - 仕様通りだが、知見学習機会が限定
5. **委譲プロンプトの集計依頼で Haiku の実態把握が浅い**
   - 「3 層動作実態」「Sonnet 失敗」「Phase 並列」を例示しないと git log 中心の判断になる
   - 実態として Sonnet × 7+ / Haiku × 10+ の並列実行があったが、Haiku 集計では「委譲なし」と書かれた

### Try（次に試すこと）

1. リハーサル直前の使用量スナップショット運用化
2. design.md §10 に gd-session-state.json lifecycle 章追加
3. distill_lessons.py の即合格対応（設計検討）
4. Sonnet 529 連続失敗時の Haiku 代替を明文化
5. 委譲プロンプト雛形に「実態集計の例示」を含める

---

## 4. アクション

| # | アクション | 反映先 | 優先度 | ステータス |
|---|---|---|---|---|
| A1 | .gitignore に `.claude/gd-session-state.json` 追加 | `.gitignore` | 高 | **実施済**（本セッション内）|
| A2 | design.md §10 に gd-session-state.json lifecycle 章を追加（生成→更新→完了→次回起動時の上書き挙動を明文化） | `docs/specs/goal-driven-orchestration/design.md` | 中 | 次サイクル |
| A3 | W4-T3 結果報告書 §5 に「リハーサル直前の使用量スナップショット運用」を追記 | `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-results.md` | 中 | 次サイクル |
| A4 | distill_lessons.py の即合格対応（成功パターン記録 or --best-case フラグ） | `docs/specs/goal-driven-orchestration/design.md` §13 + `.claude/scripts/distill_lessons.py` | 低 | 次サイクル |
| A5 | Sonnet 529 連続失敗時の Haiku 代替戦略を明文化 | `CLAUDE.md` or `.claude/rules/` | 中 | 次サイクル |
| A6 | L1 トークン目視計測の正式運用化（次回中タスクから） | `W4-T3-rehearsal-results.md` §5 注記 + 運用メモ | 中 | 次サイクル |
| A7 | 委譲プロンプト雛形に「実態集計例示」セクション追加 | （個人運用メモ / SESSION_STATE） | 低 | 次サイクル |

---

## 5. ハイライト・教訓

**乖離検知が実機で設計通りに発動した（W4-T3 主要観測 #2 達成）**。l3-executor の自己申告トークン（6,800）が実測値（37,783）の約 18% に過ぎないという乖離率 0.82 は、W1-T3 の観測（自己申告 100 vs 実測 26,305）と同様の傾向を追認するものであった。`cost_log._divergences` への自動記録と WARN ログ出力が正常動作し、設計上の乖離検知機構がリハーサル環境で実証された。

**3 層体制は並列処理スループットの主要因となった一方、Sonnet 529 のロバスト性課題が顕在化した**。/ship Phase 5 でのオーバーロード × 2 連続は、サブエージェント起動の信頼性が本番運用の前提条件になることを示唆する。Haiku による代替実行が成功したことは Fallback パスの有効性を示すが、明文化された戦略（A5）がなければ次回も同じ判断コストが発生する。

**gd-session-state.json の .gitignore 漏れは「設計時の運用面検討の不足」を示す典型例である**。同種の state ファイル（lam-loop-state.json / autonomous-state.json）は既に除外登録済みであったにもかかわらず、新規追加時にチェックが抜けた。design 起票時のチェックリストに「揮発性ファイルの .gitignore 登録」を追加することで再発を防げる（A2 と連動して検討する）。

---

## 6. 次のステップ

1. `/ship` でリハーサル成果物 + .gitignore + retro 記録を commit
2. PM が Settings > Usage を見て本セッション全体の L1 消費を W4-T3 results に追記（A6）
3. 次サイクルで A2 / A3 / A4 / A5 / A7 を順次着手

---

## 7. 関連ドキュメント

| ドキュメント | 備考 |
|-------------|------|
| `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-package.md` | 観測ポイント原本・bound 校正基準 |
| `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-results.md` | リハーサル実測結果（フロー[1]〜[9] 全確認） |
| `docs/specs/goal-driven-orchestration/requirements.md` | v1.2.0 |
| `docs/specs/goal-driven-orchestration/design.md` | v0.3.3 |
| `docs/specs/goal-driven-orchestration/tasks.md` | v1.4.3（本セッションで更新） |
| `docs/specs/goal-driven-orchestration/handoff-format.md` | v0.1.0（W6-T1 成果物） |
| 過去 retro: `docs/artifacts/retro-b-2-iter7.md` | 前回 B-2 完了時の振り返り |
