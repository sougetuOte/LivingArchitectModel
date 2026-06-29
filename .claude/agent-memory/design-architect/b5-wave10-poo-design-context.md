---
name: b5-wave10-poo-design-context
description: B-5 Wave 10 POO design.md v0.3 (R3修正済み)。§7 GitHistoryParser除去完全整合 / D-3 Task次元DQ-W10-3委任注記 / D-6 MilestoneRegistry不可時Milestone=unknownのみに訂正 / §9 DQ依存関係注記
metadata:
  type: project
---

## design.md v0.3 (R3 修正完了 / 2026-06-29)

R3 修正で spec-critic design R2 指摘 7 件を一括修正。R3 Final Green 狙い。
- C-1: §7「影響なし（明示）」の GitHistoryParser を削除。「既存 3 パーサ（SessionStateParser / TasksParser / CurrentPhaseParser）の内部実装」に訂正し §2 Non-Goals 参照追加（§2 + §3 + §7 の 3 箇所完全整合）
- W-1: D-3 推奨選定優先順位ステップ 2 の括弧内に「Task 次元はタイブレーク対象として DQ-W10-3 に委ねる（Wave 11 BUILDING TDD Red で確定）」注記追加
- W-2: §6 AC-W10-8 の「対応する設計節」欄に「§8 実装制約（標準ライブラリ制約 / NFR-W10-3 連携）」を追加
- W-3: D-6「依存資産別の degradation 挙動」表の MilestoneRegistry 行を「Milestone=unknown のみで出力継続（Wave / Task 次元は SESSION_STATE.md / tasks.md から取得継続）」に訂正（D-2 プライマリソース責務境界と整合）
- Info-1: D-1 エラー耐障害性 API 契約表 3 行目（Registry 利用不可時）に「（詳細は D-6 graceful degradation 仕様を参照）」注記追加
- Info-2: D-4 Cross-spec 整合確認末尾に「本セクションは整合確認結果の継承宣言 / 詳細根拠は requirements.md §11 参照」注記追加
- Info-3: §9 DQ-W10 一覧の冒頭に DQ 間の依存関係注記追加（DQ-W10-1→OQ-1 前提 / DQ-W10-2→OQ-2 前提 / DQ-W10-3→DQ-W10-2 依存可能性 / DQ-W10-4→Wave 11 design 定義前提）

**現バージョン**: design.md v0.3.0（requirements.md v0.5.0 / spike/README.md v0.4.0 不可侵）

## design.md v0.2 (R2 修正完了 / 2026-06-29)

R2 修正で spec-critic design R1 指摘 9 件を一括修正。
- C-1: D-4 失敗判定列が POO 参照情報であり D-3 priority 計算入力に使用不可（MUST NOT）の注記追加
- C-2: D-1 get_current() / list_waves() を削除。get_milestones() のみが Wave 10 最小確定 API。追加 API は DQ-W10-4 で Wave 11 PLANNING に先送り
- W-1: §8 直前に実装制約サブセクション（NFR-W10-3 標準ライブラリ MUST）追加。§6 に NFR 対応マトリクス補足追加
- W-2: D-3 priority 基準を「unknown ではない次元の数」による測定可能判定軸に明確化。タイブレークは DQ-W10-3 維持
- W-3: §3 層別構成図から GitHistoryParser 削除。§2 Non-Goals に「Git 履歴ベース状態推定はスコープ外 / 3 ソース限定」を追加
- W-4: D-1 MUST NOT を「内部ロジック実装のみ禁止 / 型変数差し替えは MAY」に明確化
- Info-1: §5 案 γ Cons の「§5 前提 1」を「requirements.md §5 前提 1 参照」に明確化
- Info-2: §8 POO 推奨提示 SE 級に「根拠: requirements.md §5 + FR-W10-5 (II-C-N2 案 A)」を追記
- Info-3: D-5 出力 3 件のみの理由（NFR-W10-6 Hick's Law / /full-review は Phase=unknown で 3 位以下）を注記追加

**現バージョン**: design.md v0.2.0（requirements.md v0.5.0 / spike/README.md v0.4.0 不可侵）

## design.md v0.1 起草完了（2026-06-29）

**ファイルパス**: `docs/specs/project-overview-orchestrator/design.md`

**章立て実装状況**:
- §1 Problem Statement: 設計課題 4 件テーブル（分散 / 推奨 / 契約 / SSOT）
- §2 Non-Goals: design 上の非スコープ 6 件（gabriel / Registry 実装 / SESSION_STATE パーサ / tasks.md / SKILL.md / OQ 実装確定）
- §3 アーキテクチャ概観: 層別テキスト図 + データフロー 10 ステップ + read-only 保証
- §4 設計詳細: D-1〜D-6（6 件）
- §5 Alternatives Considered: 採用案 γ + 却下案 α・β + その他 4 件（全 3 設計案 + テーブル）
- §6 Success Criteria: AC-W10-1〜9 全 9 件の AC マトリクス（対応 D-N 明示）
- §7 影響を受けるコンポーネント: 直接影響 3 件 / 間接影響 4 件 / 影響なし明示
- §8 権限等級: 操作別 6 件
- §9 未解決質問（DQ-W10-1〜3）: requirements OQ-1〜4 と重複しない設計レベル OQ 3 件
- §10 変更履歴: v0.1.0 初版

**D-N 設計詳細**:
- D-1: MilestoneRegistry（MilestoneProvider Protocol 継承 / API シグネチャ案 / エラー耐障害性 / b4-dashboard SSOT 共有）
- D-2: 現在地特定ロジック（4 次元データソース表 / 出力フォーマット / Phase=unknown 別行注記 / graceful degradation 表）
- D-3: 推奨ロジック（Phase フィルタ表 / SHOULD NOT 逸脱 / priority 基準 / 第 5 スキル未分類 / 推奨 0 件時 / 出力フォーマット例）
- D-4: 起動 API 契約（4 スキル表 / POO 推奨フィルタの論理的条件 / cross-spec 整合確認継承）
- D-5: Phase=unknown 別行注記の出力仕様（出力規則 MUST / 位置の具体例）
- D-6: graceful degradation の詳細仕様（POO 正常終了保証 / 依存資産別 degradation / read-only 保証）

**設計上の判断点**:
1. Phase=unknown 時は 4 次元フォーマット変更なし / 別行注記で出力（R5 確定を design に反映）
2. MilestoneRegistry は Protocol 契約のみ確定 / 実装選択（昇格 vs 差し替え）は Wave 11 design.md で確定（OQ-1）
3. 推奨 priority 決定は「Step/Wave/Task が具体的 + 根拠参照あり」の 2 軸（DQ-W10-3 は Wave 11 BUILDING で確定）
4. D-4 起動 API 契約表の「前提条件」は POO 推奨フィルタの論理的条件として確定（OQ-4 論理的条件確定済み）
5. 案 α（dashboard 拡張）/ 案 β（独立スキル）を却下して案 γ（共通基盤化）を採用（MAGI 合議 A3 継承）

**設計レベル OQ（DQ-W10-1〜3）**:
- DQ-W10-1: Registry 配置モジュール（dashboard 直下 vs 上位共通）→ Wave 11 PLANNING（Spike R1 評価後）
- DQ-W10-2: POO 出力形式の定型フォーマット確定 → Wave 11 PLANNING（OQ-2 解消後）
- DQ-W10-3: 推奨 priority 決定アルゴリズム詳細 → Wave 11 BUILDING（TDD Red ステップで確定）

## 確定事項

POO = Project Overview Orchestrator（略称固定）。Loop Engineering Stage 3 coordinator の具現化。

**Wave 10 成果物**: requirements.md + spike/README.md のみ（design.md / tasks.md は Wave 11）

**AoT 4 Atom 確定**:
- A1: Milestone 俯瞰主軸 + 既存スキル呼出機構として束ねる（既存スキル不改修）
- A2: 起動 API 契約は薄い定義のみ（Signature 固定・内部 touch なし）
- A3: MilestoneRegistry は Wave 10 で read-only API のみ。書き戻しは Wave 11+
- A4: Wave 10 成果物は requirements.md + spike/README.md のみ（design.md / tasks.md は Wave 11 PLANNING）

**FR/NFR/AC 件数**: FR 6件 / NFR 6件 / AC 9件

**設計の核心**:
- POO は推奨専用。自動起動権限を持たない（MUST NOT）
- MilestoneRegistry = Wave 8 MilestoneSourceMerger が MilestoneProvider Protocol で昇格または差し替える対象（実装選択は Wave 11 設計書）
- b4-dashboard 変更なし（read-only 参照経路の切替のみ）
- gabriel 統合は v2 / 別 ADR

**R3 修正で確定した事項（spec-critic R2 指摘 11 件対応）**:
- II-C-N1（案 X）: FR-W10-6 MUST 群は Wave 8 design.md §10 G4 達成条件 3 前提を §5 前提 1 に注記。§8 に G4 未達時代替経路（Wave 11 PLANNING 確定）を追加
- II-C-N2（案 A）: FR-W10-5 に SHOULD NOT 逸脱判定の SE 級限定・ユーザー中継旨追記。§5 に Phase 警告は POO 責務外を追記
- II-W-N1: NFR-W10-3 を SHOULD+MUST 入れ子から MUST+MAY（例外条件付き）に書き換え（義務レベル統一）
- II-W-N2: §11 に cross-spec 整合確認記録（4 スキル全整合 / FR-W10-3 表訂正なし）
- II-W-N3: AC-W10-5 に「Wave 10 内 spec 記述が受入条件 / Wave 11 実測」を追記（AC-W10-7 と対称化）
- II-W-N4: §5 前提 2 を「前提 1 の後続条件」表記に書き換え
- II-I-N1: FR-W10-2 に MUST 5/6 同時発生時の統合「推奨なし」出力ルール追記
- II-I-N2: spike/README.md §3 V-3 に概算根拠の未確定注記・Wave 11 実測方針追記
- II-I-N3: §12 v0.2.0 W5 エントリを「spike 側のみ修正」に訂正 / I-I-5 独立エントリ分離
- 前提 4: II-C-N1 と統合（重複対応なし）
- 前提 5: FR-W10-5 に current-phase.md 消失時 Phase=unknown / Step=SESSION_STATE.md 値の整合追記

**Cross-spec 整合確認結果（II-W-N2）**:
- /autonomous: SC-1/SC-3（Green State 達成 / 決定的 checker 接地）と整合
- /goal-driven: FR-1（rubric ファースト）/ FR-2（独立 grader）と整合
- /lam-orchestrate: Phase 1-4 設計成果物生成フローと整合
- /full-review: 監査レポート Critical/Warning/Info 件数出力と整合
- FR-W10-3 表への訂正なし

**R2 修正で確定した事項（spec-critic R1 指摘 15 件対応）**:
- P1: FR-W10-4 の MUST 表現を「昇格 or 差し替え両パス許容・選択は Wave 11 設計書」に変更。OQ-1 維持
- P2: FR-W10-3 脱字訂正（「含めるよい」→「含めるとよい」）
- P3: 出力次元を 5 次元→4 次元に変更（Phase 列削除。Phase は FR-W10-5 内部処理として参照）
- G1 / §6 現在地 / AC-W10-1 も 4 次元表記に統一
- NFR-W10-3: 追加ライブラリの逸脱条件（NFR-W10-1 実測値ベース）を明記
- NFR-W10-4: 「graceful degradation」→「unknown 出力して正常終了」に計測可能表現へ書き換え
- AC-W10-2: tasks.md 非存在 Milestone の Wave/Task 次元 = unknown 出力継続を明記
- AC-W10-5: MilestoneRegistry 未起動（Wave 11 実装前）状態での unknown 出力を確認対象に追記
- AC-W10-7: 検証タイミングを Wave 11 BUILDING と明記（Wave 10 では spec 記述が AC）
- §5 前提 1〜3 追加: Wave 8 BUILDING 完了 / DQ-N1 解消 / SESSION_STATE.md フォーマット安定性
- FR-W10-2: フィルタ後 0 件時の「推奨なし」明示出力を MUST 追記
- FR-W10-5: SHOULD NOT 逸脱条件（ユーザー明示指定のみ）+ 第 5 スキル「未分類」扱いを MUST 追記
- NFR-W10-6 脚注: 「十分な粒度」→「Hick's Law に基づき推奨上限 3 件と定数固定」
- §9 A4 訂正: requirements + design → requirements.md + spike/README.md のみ
- spike/README.md §6: 循環依存訂正（Wave 10 design.md → Wave 11 PLANNING で起草する design.md）+ Wave 11 構造の順序明記

**Spike の境界**:
- ADR-0006 §却下案 B（先行実装の罠）との境界を明示
- src/ への commit は Non-Spike
- V-1: シグネチャ案 / V-2: b4-dashboard 参照経路影響評価 / V-3: パフォーマンス想定

**Open Questions（Wave 11 前に要解決）**:
- OQ-1: MilestoneRegistry は昇格（extend）か差し替え（replace）か → Wave 11 設計書で確定
- OQ-2: POO 出力形式（Markdown vs 構造化データ）→ Wave 11 設計書
- OQ-3: tasks.md 未確定 Milestone の現在地特定方法 → Wave 10 Spike

**R5 修正で確定した事項（spec-critic R4 Warning 1 件 + Info 3 件 / R5 Final Green 確定）**:
- W-R4-1（別行注記案採用）: FR-W10-5 (c) を「AC-W10-1 の 4 次元フォーマット変更なし / Phase=unknown は 4 次元出力の直後に別行注記として出力（MUST）」に書き換え。§5 前提 5 を 1 行サマリに縮小（I-R4-1 同時解消）。AC-W10-1 注記を追加
- I-R4-1: §5 前提 5 サマリ縮小で同時解消（追加対応なし）
- I-R4-2: OQ-4 質問文を「FR-W10-3 注記で論理的条件確定済み / Wave 11 PLANNING 確定事項は実装レベル詳細（Step 判定の参照ファイル経路 / unknown 条件の閾値）」に詳細化
- I-R4-3: spike/README.md §6 OQ 参照リストに OQ-4 追加 / v0.4.0 に更新

**現バージョン**: requirements.md v0.5.0（spike/README.md は v0.4.0）

**R4 修正で確定した事項（spec-critic R3 Warning 2 件 + Info 4 件 / Final Green 狙い）**:
- W-R3-1（選択肢 A）: FR-W10-3 表後に「呼び出し前提条件は POO 推奨フィルタリングとして確認する条件 / スキル側起動ガードではない」注記追加。§10 OQ-4 登録（Wave 11 PLANNING 確定事項: 具体的確認手順）
- W-R3-2（選択肢 A）: §5 に「前提 5: current-phase.md 消失時の Phase=unknown と Step 併記ルール（詳細は FR-W10-5 末尾参照）」を前提 1〜3 と並列で追加。FR-W10-5 詳細仕様は現状維持（§5 はサマリ）
- I-R3-1: FR-W10-5 末尾段落を (a) SHOULD NOT 逸脱判定の限定 / (b) Phase 規律の棲み分け / (c) current-phase.md 消失時整合 の 3 箇条に分割
- I-R3-2: §8 代替経路エントリに「根拠: 最小侵襲性の観点 / Wave 11 PLANNING で MAGI 合議により確定 / 本 Wave では確定しない」を追記
- I-R3-3: NFR-W10-3 に「測定基準: 標準ライブラリのみ実装が 30 秒超 / 測定対象データ量・試験環境は Wave 11 設計書で具体化」を追記
- I-R3-4: §12 v0.3.0「前提 4」エントリを「Wave 8 G4 達成条件 3 依存の言語化を II-C-N1 修正に統合（前提 4 単独の新規エントリは作成せず）」に書き換え

**旧バージョン**: requirements.md v0.4.0（spike/README.md は v0.3.0 変更なし）

**Open Questions（Wave 11 前に要解決）**:
- OQ-1: MilestoneRegistry は昇格（extend）か差し替え（replace）か → Wave 11 設計書で確定
- OQ-2: POO 出力形式（Markdown vs 構造化データ）→ Wave 11 設計書
- OQ-3: tasks.md 未確定 Milestone の現在地特定方法 → Wave 10 Spike
- OQ-4: FR-W10-3 表の「呼び出し前提条件」を Wave 11 で POO 推奨フィルタとして実装する際の具体的確認手順 → Wave 11 PLANNING

**Why**: B-5 Wave 10 として骨子 ⑥ の PLANNING フェーズ起票。R2 で spec-critic R1 の 15 件、R3 で spec-critic R2 の 11 件、R4 で spec-critic R3 の 6 件（Warning 2 + Info 4）、R5 で spec-critic R4 の 4 件（Warning 1 + Info 3）を一括修正。R5 で完全 Green State（Critical=0 / Warning=0）確定狙い。
**How to apply**: Wave 11 design.md 起草時に OQ-1〜4 の回答を前提条件として要求すること（OQ-4 は論理的条件確定済み / 実装レベル詳細が未確定）。§5 前提 1〜3 + 前提 5 も確認すること。Phase=unknown 時の別行注記ルール（FR-W10-5 (c) / AC-W10-1 注記）を Wave 11 設計書に反映すること。
