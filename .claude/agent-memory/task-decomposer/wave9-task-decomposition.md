---
name: wave9-task-decomposition
description: Wave 9 (V-4 description 列追加) 起草時の タスク分解パターンと採番戦略
metadata:
  type: project
---

# Wave 9 Task Decomposition — 学習記録

## 起草日時
2026-06-29 / v0.1.0 Draft 起草

## 採番戦略（重要）

### T200 開始の根拠
- Wave 7: T44-T56 (13 件)
- Wave 8: T100 台（未確認だが 100 シリーズ確定）
- Wave 9: **T200 開始**（Wave 7 / Wave 8 と衝突回避）

採번이 단순 순서가 아니라 Milestone/Wave 별로 **100 단위 블록**을 유지하는 구조.

## 分解の要点

### Stage 構成（4 Stages）
1. **Stage 1** (T200-T203): TaskInfo.description フィールド追加 + parser 改修（2 行）+ 既存テスト互換
2. **Stage 2** (T204-T209): V-4 HTML テンプレート（thead/tbody）+ JS 定数値 + aria-sort 修正 + テスト期待値更新
3. **Stage 3** (T210-T212): CSS `.description-cell` 追加 + 予算実測
4. **Stage 4** (T213-T216): 統合テスト + Lighthouse + PoC レビュー

### SPIDR 適用のポイント
- **S (Spike)**: 影響分析が重要（T200 / design.md §8 のガードレール #4 対応）
- **I (Interfaces)**: FR-W9-N1 (a)(b)(c) の 3 段構えが Critical 回避の鍵
  - (a) JS 定数値 → (b) data-col 属性値 → (c) aria-sort 更新ロジック修正
  - 3 つが同期更新される必要性を強調
- **D (Data)**: TaskInfo フロー（parser → builder → HTML）の明確化

### テスト構成の特徴
- 検証タスク 30 件（T-S1-1 〜 T-S4-10）
- プロセスゲート（L3 採点 / 統合テスト / PoC Approved）を明確に位置付け
- aria-sort 属性更新テスト（T-S2-5 / T-S4-5）は新規（NFR-W9-4 対応）

## 設計ドキュメントとの連携ポイント

### requirements.md v0.2.7 との対応
- FR-W9-1 〜 FR-W9-5: 基本要件
- **FR-W9-N1(a)(b)(c)**: 新規追加（spec-critic ラウンド反映）
- AC-W9-N1: JS 定数値整合性確認（詳細検証手段 6 つ）
- Example Mapping §9: description 抽出の 6 シナリオ全网羅をテストカバーに反映

### design.md v0.2.7 との対応
- §3 アーキテクチャ: parser ロジック追加ゼロの保証を T202 で明確化
- §6 (a)(b)(c): 3 段構えの相互依存を T204/T205/T207 の依存グラフで可視化
- §8 既存テスト影響分析: T200 成果物 + T209 で実装化

## 波及影響の予測

### 既存テスト影響
- `test_v4_view.py`: 3 列 → 4 列化で期待値大幅更新（L1 事前承認ゲート）
- `test_tasks_parser.py`: TaskInfo の description フィールド既定値 `""` で互換保持
- aria-sort 属性更新テスト: 新規テスト領域（Wave 7 では未出現）

### CSS 予算
- Wave 7 終端: 10,400 bytes
- Wave 9 増分上限: 300 bytes (SHOULD) → 実装: 100-150 bytes 想定
- 緑帯（< 70%）維持 → 残 5,834-5,884 bytes

## タスク粒度の妥当性検証

### 実装タスク 17 件（T200-T216）
- T200-T203（Stage 1）: 基盤構築 / 粒度 S-M
- T204-T209（Stage 2）: HTML + JS + テスト期待値 / 粒度 S-M ✓ 適切
- T210-T212（Stage 3）: CSS + 実測 / 粒度 S ✓ 適切
- T213-T216（Stage 4）: 統合・Lighthouse・PoC / 粒度 M ✓ 適切

### 検証タスク 30 件（T-S1-1 〜 T-S4-10）
- Stage 1: 4 件（基本 + L3 採点 + 互換性）
- Stage 2: 6 件（HTML 構造 + ソート整合 + aria-sort + L3）
- Stage 3: 5 件（CSS 実測 + 省略表示 + tooltip + L3）
- Stage 4: 10 件（Lighthouse + pytest + 各種確認 + PoC + Wave status）

## WBS 100% Rule の達成

### FR カバー率
- FR-W9-1〜5: 100% カバー ✓
- FR-W9-N1(a)(b)(c): 100% カバー ✓（spec-critic ラウンド 対応）

### NFR / AC カバー率
- NFR-W9-1〜4: 100% カバー ✓
- AC-W9-1〜7 + AC-W9-N1: 100% カバー ✓

### 孤児タスク: 0 件
- すべてのタスクが要件またはプロセスゲートとして位置付け済

## 将来への継承事項

### Wave 10 以降への申し送り
- V-4 の 4 列構成は新標準（description 列 + ソート/フィルタ非対象の明確化）
- aria-sort 属性更新ロジック（data-col 値ベースの th 特定）は再利用パターン化の候補
- CSS 予算管理: Wave 7 終端 10,400 → Wave 9 終端 10,500-10,550 / 残 5,834-5,884 bytes

### 設計パターンの再利用価値
- **FR-N 系 採番**（spec-critic ラウンド反映の「新規 FR」マーカー）は Wave 9 で確立
- **3 文書セット一括承認体制**（Wave 7 継承）は Wave 9 でも継続
- **L2 委譲ガードレール 4 点**（ガードレール確定後の運用）の実績継承

## 知見の蓄積ポイント

### spec-critic ラウンド連動の効果
- requirements v0.2.3 → v0.2.7（ラウンド 1/2/3 反映）での Critical 3 → 0
- design v0.2.1 → v0.2.7 での Critical 1 → 0
- tasks.md v0.1.0 Draft で Green State 事前達成（ラウンド前の品質水準）

### SPIDR 分割と Critical 回避の相関
- 影響分析（Spike）の実施 → T200 成果物作成 → T209 期待値更新 が系統化
- FR-W9-N1 (a)(b)(c) の 相互依存 を 依存グラフ + WBS で可視化 → Critical 발생 부지 예방
