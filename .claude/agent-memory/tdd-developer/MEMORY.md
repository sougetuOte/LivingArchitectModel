# Memory Index

- [OSError テスト手法（Windows）](feedback_oserror_test_windows.md) — 同名ディレクトリで書き込みを阻害する PermissionError 手法が Windows で有効
- [B-3 W2-T1 エージェント定義実装](project_gd_agent_w2t1.md) — goal-driven 3 エージェント静的 pytest パターン（frontmatter パーサ + tools Agent 検出）
- [B-3 W2-T2 gd_state.py 実装](project_gd_state_w2t2.md) — spawn-time enforcement・スキーマ・AC-8/AC-9・並列起動チェック・distill hook 点
- [B-3 W3-T2 gd_loop.py 実装](project_gd_loop_w3t2.md) — Plan B 制御ループ・grader retry・§11b fallback・ログ命名・DI テストパターン
- [B-3 W1-T3 スモークテスト準備](project_gd_smoke_w1t3.md) — スタブ 2 定義 + 静的 pytest + runbook（実機実行は次セッション）
- [B-3 W4-T1 distill-lessons.py 実装](project_gd_distill_w4t1.md) — FR-5 メモリ蒸留・design §13 スキーマ準拠テスト 21 件・verified 自動判定・W-5 制約・SKILL.md フロー[8] 配線
- [B-3 W4-T2 コスト集計実装](project_gd_cost_w4t2.md) — 方針 A・invoke_*_fn tuple 化・accumulate_subagent_tokens・P-2 フォールバック WARN・±20% divergence 記録
- [B-5 W2-T7 SessionStateParser 実装](project_b5_session_state_parser.md) — タスクID regex（W1-B5-T1 は B5 形式・変換必要）・「なし（...）」前方一致除外・全文 regex でテーブル行も抽出
- [B-5 W2-T9 V-2 Milestone 一覧ビュー実装](project_b5_v2_view_w2t9.md) — Step 列は current_phase 統一・_STATUS_LABELS dict・empty state 文言・24 テスト追加で計 113 件
- [B-5 W3-T14 V-3 Wave 一覧ビュー実装](project_b5_v3_view_w3t14.md) — Milestone ごとセクション分割・グループ化は order+dict・状態決定は build_dashboard.py 側の責務・30 テスト追加で計 253 件
- [B-5 W6-T32 _radix_colors.py 実装](project_b5_w6_t32_radix_colors.md) — 96 hex 値定数モジュール・int step キー・L2-B 並列作業で builder.py 変更混入に注意
- [B-5 W6-T34 セマンティック HTML 実装](project_b5_w6_t34_semantic_html.md) — nav/main ランドマーク追加・T31 分析漏れ（html.count("<li>") 全体カウント系）・緩和方針案 A
- [B-5 W6 Stage 2 ソート機能実装](project_b5_w6_stage2_sort.md) — T37+T38+T39・<th>直書き assert 緩和 2 箇所・JS 41 行・STATUS_ORDER ??99・script 配置 </body> 直前・Bash 制限で静的検証→L1 リレー
- [B-5 W6 Stage 3 フィルタ機能実装](project_b5_w6_stage3_filter.md) — T40+T41・_render_filter_controls() 新設・DOMContentLoaded 単一統合(C-NEW-2)・JS 行数 ~100 行・既存テスト破損なし
- [B-5 W6 Stage 4 統合テスト実装](project_b5_w6_stage4_integration.md) — T42・MCP skip 5 件(疑似コード残置)・自動 4 件(HTML 500KB/CSS 10KB/外部参照 regex 3 種/ファイル数 20-35)・22 件ファイル PASS
- [B-5 W7 Stage 1 影響分析](project_b5_w7_stage1_impact.md) — TasksParser regex 厳格化・実データ 378 件誤抽出確認・test_tasks_parser.py L306/L340/L387 破損リスク・test_v4_view.py は影響なし
- [B-5 W7 T53a Stage 3 milestones テスト](project_b5_w7_t53a_stage3_milestones.md) — article/milestones-container 構造テスト 10 件・_render_v2_milestones() 直接呼び出し・T51 完了で即 PASS・test_v2_view.py 7 件は T51 起因 FAIL（T53b で対処）
