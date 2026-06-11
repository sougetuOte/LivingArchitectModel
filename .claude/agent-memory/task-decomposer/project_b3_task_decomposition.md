---
name: project-b3-task-decomposition
description: B-3 ゴール駆動オーケストレーション・スキルのタスク分解で確立したパターン
metadata:
  type: project
---

B-3 では 8 Wave / 18 タスク（PM ゲート 3 件含む）の構成で tasks.md を生成した。

**Why:** 設計書に OQ（未確定事項）が残っており、OQ-1 の実測結果（Plan A/B）が後続 Wave 全体に影響するため、W0 を Spike 専用 Wave として分離した。

**How to apply:**
- 設計書に「Plan A/B 分岐」「PM級変更」「6/22 等の期限制約」が含まれる場合、それぞれを独立タスクとして明示する
- PM ゲートはタスク列に「承認ゲート」として組み込み、依存関係に明示する（承認前着手禁止の可視化）
- WBS 100% Rule: FR/NFR → タスク、タスク → FR/NFR、AC → 検証タスクの 3 方向の表を全て作成する
- 6/22 期限タスク（L1 モデルでの実機確認）は Wave 構成概要と個別タスクの両方に期限注記を入れる
- full-review 改造のようなスコープ外候補は「フェーズ 3 はスコープ外（future-candidates 扱い）」と明示し、フェーズ 2 先行案を本マイルストーン内の選択タスクとして構成した
