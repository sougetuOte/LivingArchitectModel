# Retrospective: cc-spec-alignment（Wave 1/2/3 完了）

実施日: 2026-05-29 / スコープ: cc-spec-alignment 機能全体（Claude Code 仕様すり合わせ更新）
対象期間: 2026-05-28 〜 2026-05-29 / コミット: 12件 / テスト: 580 passed（全 Wave で Zero-Regression 維持）

## Step 1: スコープ

| Wave | 内容 | 主要タスク |
|:----:|------|-----------|
| 1 | 裏取り → 陳腐化是正 → Memory Policy 確定 | T1-0〜T1-4b（FR-3 裏取り / hooks 是正 / 8エージェント `memory: project`） |
| 2 | 新機能採用（既存7スキル） | T2-1〜T2-7（paths / model / when_to_use / allowed-tools 採用、defer・worktree・effort.level 見送り） |
| 3 | commands → skills 移行（C-1 解消） | T3-0〜T3-11（11本移行、全本 `disable-model-invocation: true`） |

## Step 2: 定量分析

| 指標 | 値 |
|:-----|:---|
| コミット数 | 12 |
| 実装タスク数 | 25（Wave1: 6 / Wave2: 7 / Wave3: 12） |
| テスト | 580 passed・Zero-Regression（全 Wave 通じて回帰ゼロ） |
| 新規テスト追加 | Wave 1 のみ（PostToolUse キー両系統テスト）。Wave 2/3 は設定・移行作業のため新規テストなし |
| 監査 Issue | 該当なし（`/full-review` 非実施。設定・ドキュメント主体のため） |
| 仕様/ドキュメント更新 | design §7.6 / future-candidates.md / wave3-migration-table.md / CHANGELOG / doc 参照7箇所 |
| 採用/見送り | 新機能 採用4 / 見送り5（実在性は全裏取り済み、見送りは LAM 適合性で判断） |

## Step 2.5: TDD パターン分析

`.claude/tdd-patterns.log`（12行）を分析。FAIL→PASS 遷移は主に v4.6.2 / scalable-code-review 期（05-26）と
Wave 1 の PostToolUse 是正（05-28: `test_get_tool_response_prefers_tool_result_over_tool_response` 等）。
同一セッション内の反復（`test_single_function` 等）は通常の TDD イテレーションであり、
**ルール化に値する横断的・再発パターンはなし**。`ANALYZED` マーカーを追記済み。

## Step 3: 定性分析（KPT）

### Keep（続けること）
- **裏取りファースト**: context7 で公式書式（`tool_result` キー、`memory:`、`disable-model-invocation`）を確認してから実装 → 推測実装ゼロ・手戻りゼロ
- **Zero-Regression の徹底**: 全 Wave で 580 passed を維持。設定変更でも毎回 pytest で確認
- **PM級論点の絞り込み**: 起動セマンティクス判定で AskUserQuestion を使い、明白な10本は自動確定・論点（project-status）1点のみ人間に諮った
- **歴史記録の保護**: doc 参照クリーンアップで「変更記録（過去の成果物）」と「現在地ポインタ（今壊れるリンク）」を区別し、完了機能 doc / artifacts を不変扱い
- **コミット粒度の合理的判断**: git rename 認識を活かしクリーンな移行履歴。design「1本1コミット」から逸脱する際は理由を明示し承認

### Problem（問題だったこと）
- **計画時の評価軸欠落（Wave 2）**: 機能の実在性は裏取りしたが LAM 適合性評価が抜け、昇格組3機能（defer / worktree・background / effort.level）が着手後に全見送り。計画の手戻り
- **設計書の書式未裏取り（Wave 3）**: design §7.5 が存在しないキー `user-invocable` に言及していた（実体は `disable-model-invocation: true`）。設計フェーズで API キー名を裏取りしていなかった
- **移行タスクの構造的制約**: 旧コマンド削除を AI が実行できず（憲法で削除禁止）、手動依頼の往復が発生。事前に削除方式を決めていなかった
- **参照陳腐化の慣習的放置**: 完了機能 doc の旧パス参照（`daily.md` 等）が削除後も放置される慣習。移行のたびに「現在地ポインタ」が壊れる構造的問題

### Try（次に試すこと）
- **新機能採用の二段構え評価**: 「実在性（裏取り）＋ LAM 設計思想への適合性」を必須2段階に。future-candidates.md §3 に記録済み → ルール化
- **upstream-first を PLANNING にも適用**: 設計書に API キー名・書式を書く前に context7 で裏取り（現状 upstream-first は実装前提）
- **移行系タスクのテンプレ化**: 「AI 削除不可」を見越し、着手時に削除方式（手動 / git rm 承認 / /ship 一括）を先決めする手順
- **参照 SSOT 化**: commands/skills のような互換シム→正統移行では、所在地ポインタを1箇所に集約し散逸を防ぐ（将来の移行コスト低減）

## Step 4: アクション抽出

| # | アクション | 反映先 | 等級 | 優先度 |
|:-:|:---------|:-------|:----:|:------:|
| A1 | 新機能採用の二段構え評価（実在性＋LAM 適合性）をルール化 | `.claude/rules/planning-quality-guideline.md` | PM | 高 |
| A2 | upstream-first を PLANNING/設計書執筆にも明示適用 | `.claude/rules/upstream-first.md` | PM | 中 |
| A3 | 移行系タスクの削除方式先決め手順を知見化 | `docs/artifacts/knowledge/` | SE | 中 |
| A4 | design §7.5 の `user-invocable` 記述の事後注記 | `docs/specs/cc-spec-alignment/design.md` | PM | 低（完了機能のため任意） |

## Step 6: 次サイクルへの引き継ぎ

- cc-spec-alignment は機能クローズ可。CHANGELOG は [Unreleased] に蓄積済み（次リリースで確定）
- **A1 反映済み**: `planning-quality-guideline.md` §7 新機能採用の二段構え評価（2026-05-29 承認）
- **A2 反映済み**: `upstream-first.md` 設計フェーズ（PLANNING）への適用（2026-05-29 承認）
- **A3 反映済み**: `docs/artifacts/knowledge/pitfalls.md` に「移行系タスクで AI が旧ファイルを削除できず往復が発生」を記録（SE級）
- **A4 反映済み**: `design.md` §7.5 に user-invocable→disable-model-invocation の書式事後注記（2026-05-29）
- **全アクション（A1〜A4）反映完了**
