---
name: b5-wave-c-magi-v2-gabriel-context
description: B-5 Wave C 骨子②起草の文脈。gabriel adversarial verifier 統合設計。req/design v0.4.0 (R3完了) / abort=任意タイミング独立分岐 / opt-out主体=L1統括のみ / §5全7パターンテンプレ揃い / NFR-W-C-2主体2パラ統合 / FR-W-C-2クロスフィールド制約追加
metadata:
  type: project
---

## B-5 Wave C（骨子 ②）MAGI v2 gabriel 統合 — 設計起草文脈

**起草日**: 2026-06-29
**起草対象**: ADR-0007 + `docs/specs/magi-v2-gabriel/requirements.md` v0.1.0 + `docs/specs/magi-v2-gabriel/design.md` v0.1.0

### 既決事項（再合議不要）

- gabriel = `.claude/agents/gabriel.md` 独立 subagent（spec-critic / goal-driven-grader と同形式）
- デフォルトモデル: Sonnet（rubric 突合 + 自由理由生成の両方が必要）
- 出力契約: 6 フィールド JSON（verdict / severity / affected_atoms / reasoning / recommended_action / confidence）
- Reflection（Step 4）廃止 → Convergence（Step 3）直後に gabriel probe を挿入
- AoT 適用時のみ自動起動（非 AoT 軽量決定はスキップ）
- 再 MAGI 上限 1 回（2 回目 critical refute は人間エスカレーション）

### 設計上の重要判断

- `confidence < 0.3` の場合 `verdict=inconclusive` 強制（暴走リスク抑制）
- `affected_atoms=[]` で `verdict=refuted` 禁止（根拠なし refute 防止）
- AoT フレームワーク自体は MUST NOT 物理削除
- SKILL.md / 06_DECISION_MAKING.md / decision-making.md の実際の改訂は BUILDING で実施（本 Wave は reference 言及のみ）

### FR/NFR/AC/OQ/DQ 件数

- FR: FR-W-C-1〜7（7件）
- NFR: NFR-W-C-1〜6（6件）
- AC: AC-W-C-1〜11（11件）
- OQ: OQ-W-C-1〜5（5件）
- DQ: DQ-W-C-1〜5（5件、うち2件は OQ から転化済み）

### R1 修正後の状態（v0.2.0）

- requirements v0.2.0: 9件修正済み（FR-W-C-3 MUST NOT / NFR-W-C-1 責任者明示 / NFR-W-C-3 SHOULD NOT 降格 / G2 判定タイミング / FR-W-C-5 abort 行 / confidence 刻み制約緩和 / OQ-W-C-4,5 解消タイミング / OQ-W-C-6 新設 / AC-W-C-4 計測方法）
- design v0.2.0: 9件修正済み（mermaid 終端ノードT / §4.1 軽量モード / §9.1 AC対応表 / §6.1 opt-out 権限境界 / verdict 連動制約注記 / confirmed テンプレ注記 / タイムアウト行 / §8 SSOT 注記 / confidence multipleOf 削除）
- ADR-0007: Proposed のまま / 関連 ADR 行に Proposed 状態・Rejected 時再評価義務を注記 / 改訂履歴追記

### R2 修正後の状態（v0.3.0）

- requirements v0.3.0: 6件修正済み（W-R2-1: FR-W-C-4 opt-out 主体「ユーザー（L1統括）のみ」に統一 + 自律ループ却下MUST追記 / W-R2-2: NFR-W-C-2 検出主体明示 + FR-W-C-5 フォーマット不備行追加 / W-R2-3: FR-W-C-2 abort 独立経路説明追記 / I-R2-1: warning行 MUST明示 / I-R2-2: AC-W-C-4 deterministic stub テスト形式 / I-R2-3: ADR-0007 v0.3.0参照）
- design v0.3.0: 7件修正（+ §6 opt-out 条件整合追加）（C-D-R2-1: §3 abort 独立分岐 / §2 mermaid ABノード / §5 abort/refuted+critical/timeout/format_errorテンプレ追加 + abort/format_error行追加 / W-D-R2-1: §3 proceed に inconclusive 追加 / W-D-R2-2: §5 refuted+info テンプレ追加 / W-D-R2-3: §9.1 AC-W-C-10 参照先修正 / I-D-R2-1: §4 冒頭宣言 / I-D-R2-2: Step4入力定義 / I-D-R2-3: mermaid O/Pノード）
- ADR-0007: Proposed のまま / 関連仕様を v0.3.0 に機械更新 / 改訂履歴追記

### R3 修正後の状態（v0.4.0）

- requirements v0.4.0: 5件修正済み（W-R3-1: NFR-W-C-2 3パラ→2パラ統合・MAGI フロー実行者が検出主体であること主語を2段目に明示 / W-R3-2: FR-W-C-2 クロスフィールド制約ブロック追加（severity=critical→proceed禁止 / confirmed/inconclusive→severity=info / confidence<0.3+affected_atoms=[]の制約再掲）/ I-R3-1: ADR-0007 D-3 abort行追加はADR側で対応 / I-R3-2: AC-W-C-10 計測方法にdesign §5+§6参照先追記 / I-R3-3: FR-W-C-4 opt-out理由記録主語を「ユーザー（L1統括）またはMAGI フロー実行者」に明示）
- design v0.4.0: 3件修正済み（W-D-R3-1: §5 severity=critical詳細フロー冒頭にabort優先順序注記1文追加 / I-D-R3-1: §5テンプレート共通注記をセクション冒頭に集約・confirmed後の重複注記削除 / I-D-R3-2: §9末尾Gap分析を削除・§9.1への参照リンクに統一）
- ADR-0007: Proposed のまま / D-3テーブルにabort行追加 / 関連仕様をv0.4.0に更新 / 改訂履歴追記

### §5 テンプレート網羅状況（v0.3.0 達成）

全7パターン揃い済み: confirmed / refuted+critical / refuted+warning / refuted+info / inconclusive / abort（任意タイミング独立） / timeout / format_error

### spec-critic R3 への引き渡しメモ

- abort = verdict/severity 問わず独立経路（L1確定方針）/ design §3 テーブル + §2 mermaid ABノード + §5テンプレ + §5テーブル の4箇所整合済み
- opt-out 主体: requirements FR-W-C-4（ユーザーのみ）/ design §6 opt-out 条件（ユーザーのみ + 自律ループ却下は§6.1参照）/ design §6.1 権限境界テーブル（不許容）の3箇所整合済み
- NFR-W-C-2 フォーマット不備: requirements（検出主体明示） + design §5 テーブル + design §5 format_errorテンプレの3箇所整合済み
- AC-W-C-4 を deterministic stub テスト形式に変換済み（OQ-W-C-5→DQ-W-C-2 解消との整合を spec-critic で確認すること）
- design §3 recommended_action テーブルの `severity=critical` 制約行（`proceed` 禁止）は inconclusive が proceed を返す新設計と矛盾しないか確認（inconclusive の severity は info 設定のため問題なし）

### 未解決の主な課題（OQ/DQ）

- OQ-W-C-1: gabriel の実際のコンテキスト分離度（BUILDING 実機テストで解消）
- OQ-W-C-2: Sonnet vs Haiku 品質比較（BUILDING 後 retro）
- OQ-W-C-3: AoT 適用判定自動化（将来 Wave / future-candidates）
- DQ-W-C-3: `gabriel.md` フロントマター書式の upstream-first 確認（BUILDING で実施）

**Why:** MAGI Reflection 変更率 0%（B-4 監査）が gabriel 統合の根本動機。ADR-0005 追補の独立文脈検証が唯一の有効事例であり、その構造を常時利用可能にする実装が本 Wave。

**How to apply:** 次回 gabriel 関連の設計・レビューでは、(1) 文脈独立性の確保、(2) 暴走防止の confidence 閾値、(3) AoT 連動トリガー の3点が設計の核であることを念頭に置く。
