# v5 Fat Audit Summary（2026-06-20 抽出）

## §1 KPI / NFR 項目仕分け（候補 ④）

- **削除候補 4 件**: NFR-6, NFR-7, NFR-8（応答時間）、NFR-17（集計スクリプト）。仕様書自身が「努力目標」と宣言
- **温存 11 件**: NFR-1, 2, 4, 5, 9, 10, 11, 12, 13, 15, 16（fail-safe または運用実績ログあり）
- **共通化検討 1 件**: NFR-3（PM 級は Opus が CLAUDE.md 人間体制と実装にズレ。仕様書との整合要）
- **要追加調査 1 件**: NFR-14a（Wave 1 完了チェック済みも実計測ゼロ。v5 計測基盤構築タスク再起票）
- **PM 採用プラン**: NFR-17 削減プラン A（自動集計要件削除、手動スナップショット再定義）。NFR-6/7/8 削除、NFR-14a 再起票
- **注目**: NFR-15（permission.log 8260 行）・NFR-16（loop.log 436 エントリ）は最も健全。毎日更新稼働中
- **highest_risk**: NFR-14a（tasks 完了チェック済み、実計測ゼロ。ゾンビ NFR）
- **最終判定**: 監査完了、採用プラン確定、実施フェーズ B-4 後 PLANNING/BUILDING へ

## §2 distill-lessons skip 機構（候補 ②）

- **既存重複スキップ**: task_id 単位の idempotency あり（distill_lessons.py L241-244）。意味的重複は非対応
- **新規性チェック**: 未実装（設計で MUST 追記と規定されているため意図的空白）。未検証エントリが全体化する懸念
- **現状 fat**: 無し（2 エントリ・19 行は最小規模）。6 ヶ月で月 20 タスク実行時は 120 エントリ（未検証が大多数）に膨張予測
- **lessons.md 品質**: 2 件とも未検証・定型文（「一般則: 参照のこと」）。grader ループ 0 件で修正内容不明
- **PM 採用プラン**: プラン A 採用（grader ログ空 = スキップ。SE 級。判定基準は「全フィールド空 / 定型文のみ」）
- **プラン B/C 後送り**: /retro チェックリスト追加は v5 PLANNING 検討。セマンティック重複チェックは 30 件超後に再評価
- **副次所見**: gd-20260617-001 ループ回数 0 根本原因は別タスク起票不要。本記録留めで対応
- **最終判定**: fat 予防型。実装追加で長期膨張を防ぐ。B-4 後 PLANNING/BUILDING で他候補と一括実施

## §3 /full-review Phase 数削減（候補 ③）

- **Stage 数**: 6 Stage（内部 23 Step）。実機機能 Stage は 5 Stage（コア）、no-op Step は 4（計 1 Step 調査要）
- **実機実行実績**: loop-*.txt 19 ファイル、audit-reports 27 ファイル。found 合計 395、fixed 合計 337
- **no-op Step の内訳**: Stage 1 Step 3（import-map.json 未生成）、Stage 2 Step 1-2（tree-sitter 未インストール）、Stage 3 Step 1/3（ast_map / import_map 縮退）→ 計 4 Step
- **根本原因**: Plan A/B/C/D 閾値（10K/30K/100K/300K 行）に対して現プロジェクト 16K 行は Plan A のみ有効。Plan B 以上の Step は構造的に 0 回機能
- **PM 採用プラン**: 方針 X 採用（プラン A のみ実施）。SKILL.md に「現状 no-op（前提条件未充足）」マーカー追記。Stage 1/3 物理撤去は行わない（v5 復活余地残す）
- **Stage 別ログ出力**: 見送り（方針 X との整合性優先）。Sonnet 主張 17 → Opus 訂正 23 Step
- **幽霊連鎖**: ast-map.json / import-map.json 未生成による連鎖 no-op は構造的負債だが Plan B/C/D 復活時に解消余地あり
- **最終判定**: Stage 削減ではなく「no-op 明示」が本質。認知的負荷軽減が主効果。B-4 後 PLANNING/BUILDING で実施

## §4 MAGI Reflection 廃止 or 統合（候補 ①）

- **MAGI 適用件数**: 9 件（推定。daily 言及のみの 2 件含む）。独立アンカーファイル 2 件、記録されたもの 7 件
- **Reflection 結論変更**: 0 件 / 0%。7 件すべて「致命的な見落とし: なし → 結論確定」テンプレ出力
- **機能停止の根因**: 入力同一問題（Step 3 直後の同一文脈再処理）+ CASPAR 既に致命的排除済み + 高閾値（致命的のみ）+ テンプレ形骸化
- **唯一の実質 catch**: ADR-0005 Reflection 追補（2026-05-29）で別セッション DW ブラインド検証が 3 catch 発見。MAGI Reflection 機構ではなく adversarial 外部検証が機能
- **PM 採用プラン**: プラン B 採用（v5 構想 ② gabriel 統合・長期方針）。暫定「警告ラベル付き温存」（物理削除・コメントアウト不採用）
- **AoT 分解は温存**: Reflection と別機構。W5-T2 で 6 隠れリスク顕在化は AoT の貢献。v5 ② でも維持
- **再帰的自己例**: 本 artifact 内で MAGI を 5 回適用、全 Reflection が 0% 変更率という再帰証拠が査定自己一貫性を担保
- **最終判定**: 機能停止を実装的に裏付け。v5 ② gabriel adversarial probe に統合予定。B-4 後に警告ラベル標記

## §5 B-4 監査総合報告

- **全 4 候補採用プラン確定**: ④ NFR-17 削減 A + ⑥7/8 削除 + NFR-14a 再起票 / ② プラン A（SE 級）+ B/C 後送り / ③ 方針 X（no-op マーカー追記）/ ① プラン B（gabriel 統合・長期）暫定温存
- **fat の本質は文書と実装のズレ**: NFR-14a（完了チェックあり実体なし）/ /full-review ast-map 未生成（幽霊 Step）/ Reflection 形式実行効果 0% は同型パターン
- **削減と予防の峻別**: ④③① は削除型、② は予防型。v5 で別カテゴリ扱い
- **Sonnet 監査の質**: 集計限界・推定値を自発明示。査定降格 3 件のみ（NFR-14a 分類訂正、Step 数 17→23、NFR-2/1 訂正）
- **次フェーズへの引き継ぎ**: PLANNING 切替 → spec 化（docs/specs/v5-fat-reduction/）→ SESSION_STATE.md v5 ② 補強記述 → 実装 → B-5 候補へ進路
