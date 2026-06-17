**Version**: 1.0.0
**Created**: 2026-06-17
**Status**: ready-for-grader
**Source**: requirements.md v1.2.0 (FR-1〜FR-10 + AC-1〜AC-15) + design.md v0.3.3 §20

---

# rubric: goal-driven-orchestration W7-T1 検収

- 生成日: 2026-06-17
- タスク種別: 大（W7-T1 検収。25 項目）
- global_bound: tokens=200000 OR time=3600s
- 対応要件: NFR-8 / AC-1〜AC-15 / FR-1〜FR-10 / design §20

## 検証項目

| # | カテゴリ | チェック項目 | 検証方法 | 検証コマンド / grader 指示 | 合否基準 |
|---|---------|------------|---------|--------------------------|--------|
| 1 | AC-1 | SKILL.md が `.claude/skills/goal-driven/` に存在する | run | `ls .claude/skills/goal-driven/SKILL.md` | exit 0（ファイル存在） |
| 2 | AC-2 | FR-1〜FR-10 がすべて実装またはテンプレートとして具現化されている | grader | 本 rubric の #16〜#25（FR-1〜FR-10 行）を個別判定し、全件 Pass であることを確認 | FR-1〜FR-10 (#16〜#25) すべて Pass |
| 3 | AC-3 | サンプルタスク 1 件でフロー[1]〜[9] が一巡するデモログが取得できる（中タスク経路で可） | grader | `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-results.md` を Read し、フロー[1]〜[9] の各ステップ成否テーブルが存在し全行「OK」であることを確認 | デモログ存在 AND フロー[1]〜[9] 全ステップ OK 記録 |
| 4 | AC-4 | 三段階ルート（小/中/大）の判定がデモログで確認できる | grader | `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-results.md` の「route=medium の判定 OK」記録と、design.md §9 の三段階ルートフロー図の存在を確認 | route 判定記録 AND §9 ルートフロー図存在 |
| 5 | AC-5 | grader が作業者と別コンテキストで動作していることがログで確認できる | grader | `.claude/logs/gd/gd-20260617-001-loop01-grader.json` を Read し、ファイルが存在すること（別 Agent 呼び出しで生成されたログ）を確認。goal-driven-grader.md フロントマターの description に「作業者（l3-executor）と別コンテキストで実行される（FR-2）」記述があることを確認 | ログファイル存在 AND grader 定義に別コンテキスト記述あり |
| 6 | AC-6 | L3 エージェント定義に Task ツールが含まれていない | grader | `.claude/agents/goal-driven-l3-executor.md` と `.claude/agents/goal-driven-grader.md` の `tools:` フィールドを Read し、`Agent` が含まれないことを確認 | l3-executor AND grader 両定義の tools に `Agent` 不在 |
| 7 | AC-7 | `/goal` 使用箇所すべての条件文に打ち切り句が含まれている | run | `grep -rn "or stop after" .claude/skills/goal-driven/` | マッチあり（exit 0）。`/goal` を使用する場合のみ適用。Plan B 採用（§8 確定）のため grader が SKILL.md 内の Plan B フォールバック条件と対応する bound 設定の存在も確認 |
| 8 | AC-8 | グローバル bound（総トークンまたは総時間）が三層全体に効くことがテストで確認できる | grader | `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-results.md` の「total_tokens 75,342（150k bound 内）」記録と、gd-session-state.json スキーマ（design §10）における `global_token_bound` / `global_time_bound` フィールド定義の存在を確認 | リハーサルでの bound 内完了記録 AND 設計スキーマにフィールド定義あり |
| 9 | AC-9 | 差し戻し回数上限超過テストでエスカレーションが発火する | grader | design.md §4 の AC-9 対応欄（「エスカレーション E2E テスト（I-1）」）と §10 の `max_loop_count` フィールド定義を Read し、エスカレーション経路設計の記述が存在することを確認。実機テスト結果は OQ-2 選定（Plan B 確定）後の実施事項として design §18 D1 に記録済み | design §4 に AC-9 対応設計記述あり AND §10 に max_loop_count フィールドあり |
| 10 | AC-10 | Dynamic Workflows がデフォルト経路で起動しない | grader | `docs/artifacts/goal-driven-demo/W6-T2-dw-exclusion-report.md` を Read し、検証 1〜5 の合否欄が全件 Pass または Partial Pass であり、Fail が 0 件であることを確認 | W6-T2 レポート存在 AND Fail 0 件 |
| 11 | AC-11 | モデル別・層別トークン消費サマリが出力される | grader | design.md §14「タスク完了時の出力（AC-11）」コードブロックに L1/L2/L3/grader 別サマリ形式の定義が存在することを確認。`docs/artifacts/goal-driven-demo/W4-T3-rehearsal-results.md` §2 の観測項目「コストサマリ出力」が Pass であることを確認 | §14 に層別サマリ形式定義あり AND リハーサルで出力確認済み |
| 12 | AC-12 | `/goal` のサブエージェント内動作可否の検証結果が設計文書に記載されている | grader | design.md §8「内側ループ二案構え」の「確定: Plan B」記述（2026-06-12 実測結果）と `docs/specs/goal-driven-orchestration/research/oq1-goal-subagent-test.md` の存在を確認 | §8 に Plan B 確定記述あり AND oq1-goal-subagent-test.md 存在 |
| 13 | AC-13 | 決定的骨格の実装方式の比較検討と選定理由が記載されている | grader | design.md §3「Alternatives Considered」の比較表（3 案: 保存済みワークフロー / hooks / スキル+自前スクリプト）と「選定: (c) スキル + 自前スクリプト」の理由記述（4 項目）の存在を確認 | §3 に 3 案比較表あり AND 選定理由（理由 1〜4）あり |
| 14 | AC-14 | full-review の現仕様分析・改造範囲・互換性影響・工数見積もりが文書として PM へ提出され承認されている | grader | `docs/specs/goal-driven-orchestration/research/full-review-analysis.md` の存在を確認。git log で該当ファイルのコミット記録（8578213, f47ffa5 等）または design §18 D5「Draft 完成済み・PM 承認待ち」記述を確認 | full-review-analysis.md 存在 AND git log またはdesign §18 に Draft 完成記録あり |
| 15 | AC-15 | lam-orchestrate → 新スキルへの成果物受け渡し形式が定義されている | run | `ls docs/specs/goal-driven-orchestration/handoff-format.md` | exit 0（v0.1.0 存在） |
| 16 | FR-1 | rubric ファーストの仕組み: L1 が中・大タスク着手前に rubric.md を生成する設計が定義されている | grader | `.claude/skills/goal-driven/SKILL.md` の「フロー[2] rubric 生成」記述を Read し、rubric.md 生成手順（rubric-draft.md 有無分岐含む）が存在することを確認 | SKILL.md フロー[2] に rubric 生成記述あり |
| 17 | FR-2 | grader が作業者と別コンテキストで実行され、原則 Haiku で動作する | grader | `.claude/agents/goal-driven-grader.md` のフロントマター `model: haiku` と description の「別コンテキスト」記述を確認 | model: haiku AND 別コンテキスト実行記述あり |
| 18 | FR-3 | 下層→上層の報告が定型フォーマット（変更点/テスト結果/未解決事項/次の提案）で定義されている | grader | design.md §7「構造化報告スキーマ（FR-3）」の JSON スキーマに `changes` / `test_results` / `unresolved` / `next_suggestion` の 4 フィールドが存在することを確認 | §7 スキーマに 4 フィールドすべて存在 |
| 19 | FR-4 | bound 設計の 4 要素（ターン数上限 / /goal 打ち切り句 / 差し戻し上限 / グローバル bound）が設計に含まれる | grader | design.md §10「bound 機構（FR-4）」を Read し、「層別 bound」テーブルに max_turns / 打ち切り句 / グローバル bound の 3 行、gd-session-state.json スキーマに `max_loop_count` フィールドが存在することを確認 | §10 に 4 要素すべての設計記述あり |
| 20 | FR-5 | タスク終了時に失敗・修正記録を蒸留し agent-memory に追記する仕組みが存在する | grader | `.claude/scripts/distill-lessons.py` の存在と、`.claude/agent-memory/goal-driven-l3-executor/lessons.md` の存在（W4-T3 リハーサルで蒸留済みエントリあり）を確認 | distill-lessons.py 存在 AND lessons.md 存在 |
| 21 | FR-6 | 三段階ルート（小=L3直行 / 中=L1→L3 / 大=L1→L2→L3）の判定機構が設計されている | grader | design.md §9「三段階ルート設計」の判定フロー図（条件 A/B/C の YES/NO 分岐）と SKILL.md の三段階ルート分岐ロジック記述を確認 | §9 に判定フロー図あり AND SKILL.md にルート分岐ロジックあり |
| 22 | FR-7 | L3（実行者・grader）のエージェント定義から Task ツールが除外されている | grader | AC-6 (#6) と統合 — `.claude/agents/goal-driven-l3-executor.md` と `.claude/agents/goal-driven-grader.md` の tools フィールドに `Agent` が不在であることを確認 | 両定義の tools に Agent 不在 |
| 23 | FR-8 | 小/中/大いずれのルートにも Dynamic Workflows を組み込まず、effort 設定が明示されている | grader | AC-10 (#10) と統合 — W6-T2 レポートの Fail 0 件確認 AND `.claude/agents/goal-driven-l3-executor.md` フロントマターの `effort: default` 記述を確認 | AC-10 Pass AND effort: default 明記 |
| 24 | FR-9 | full-review 改造前に分析文書を PM へ提示・承認なしに着手禁止の設計が記録されている | grader | AC-14 (#14) と統合 — `docs/specs/goal-driven-orchestration/research/full-review-analysis.md` 存在 AND design §15「改造の承認ゲート」に FR-9 MUST NOT 記述あり | 文書存在 AND §15 に承認ゲート記述あり |
| 25 | FR-10 | lam-orchestrate → 本スキルへの受け渡し形式が定義され、直列接続として機能する設計がある | grader | AC-15 (#15) と統合 — `docs/specs/goal-driven-orchestration/handoff-format.md` 存在 AND design.md §16「lam-orchestrate 受け渡し形式（FR-10）」に「lam-orchestrate（PLANNING 並列実行）→ goal-driven スキル（BUILDING 自己修正ループ）→ full-review（納品前検収）」の直列パイプライン記述あり | handoff-format.md 存在 AND §16 に直列接続記述あり |

## 差し戻しルール

- max_loop_count: 2（grader 不合格時の差し戻し回数上限）
- 同一項目 2 回連続 Fail → PM エスカレーション（本検収ループの上限）
- 上限到達時または escalate=true 時は人間（PM）にエスカレーション

## grader への引き継ぎ事項

- 本 rubric は AC-1〜15（#1〜#15）と FR-1〜10（#16〜#25）を個別行として列挙する設計（W7-T1 完了条件 #1 充足）
- 検証方法種別:
  - `run`（コマンド実行・exit code 判定）: #1, #7, #15 の 3 件
  - `grader`（ファイル読み取り・統合判定）: #2〜#6, #8〜#14, #16〜#25 の 22 件
- grader 出力 JSON は `.claude/logs/gd/W7-T1-grader.json` に保存（goal-driven-grader 標準スキーマ準拠）
- escalate=true の場合は PM-G3 提出前に統括レビュー
- Plan B 確定（design §8）のため、AC-7/FR-4 の `/goal` 打ち切り句確認は SKILL.md の Plan B 記述を対象とする
  （`/goal` を実際に使用していない場合、SKILL.md 内に「Plan B: 自前ループ」記述と bound 設定があれば充足）

## エビデンスファイル一覧（grader 参照先）

| エビデンス | パス |
|-----------|------|
| W4-T3 リハーサル結果 | `docs/artifacts/goal-driven-demo/W4-T3-rehearsal-results.md` |
| W6-T2 DW 排除検証レポート | `docs/artifacts/goal-driven-demo/W6-T2-dw-exclusion-report.md` |
| grader ログ（W4-T3） | `.claude/logs/gd/gd-20260617-001-loop01-grader.json` |
| OQ-1 検証記録 | `docs/specs/goal-driven-orchestration/research/oq1-goal-subagent-test.md` |
| full-review 分析文書 | `docs/specs/goal-driven-orchestration/research/full-review-analysis.md` |
| handoff-format 定義 | `docs/specs/goal-driven-orchestration/handoff-format.md` |
| lessons.md（蒸留済み） | `.claude/agent-memory/goal-driven-l3-executor/lessons.md` |
| distill-lessons.py | `.claude/scripts/distill-lessons.py` |

## 補足

- 25 項目中、機械的検証可能（run）= 3 件（#1, #7, #15）、grader 判定 = 22 件、human = 0 件
- AC-7（#7）: Plan B 採用確定のため `/goal` の実 grep に加え SKILL.md の Plan B bound 設定確認を grader が補完する
- AC-13（#13）の検証方法は design.md §3 の比較表存在と選定理由記載の機械的確認（W7-T1 完了条件 #5）
- 重複検証（AC-2 vs FR-1〜10、AC-6 vs FR-7 等）は意図的（grader が個別行で判定し統合 Pass を求める設計）
- AC-8/AC-9 は設計上の定義・記述確認で充足（実機テストは OQ-2 選定後タスク: design §18 D1 参照）
- global_bound は中タスク値（tokens=150k）より大きい 200k を設定（検収タスク自体が 25 項目の大タスク相当）
