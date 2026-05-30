# future-candidates: 採用見送り技術（autonomous-mode）

最終更新: 2026-05-30 / フェーズ: PLANNING

> 本書は autonomous-mode で **core 採用を見送った**外部技術と、その理由・再評価条件を記録する。
> 根拠: RQ-5（[requirements §6](./requirements.md)）/ FR-6.3 / [ADR-0005](../../adr/0005-thin-harness-autonomous-governance.md) Non-Goals。
> [design.md](./design.md) の D6 から参照される。

## 見送り候補1: Dynamic Workflows（DW）

### 決定
core 採用を**見送る**。`/goal` を core とし、DW は scoped 実験のみ可（FR-6.2 / FR-6.3）。

### 見送り理由
- $100 Max（Max 5x）ではトークン消費が桁違い（参考: 3エージェントで単発の約7倍。ADR-0005 制約条件）。daily core 用途には Max 20x（$200）相当が前提との見解が一般的。
- core を `/goal` に置けば $100 Max で完結でき、コスト制約（requirements Goals）を満たす。「DW を尻尾、core(/goal) を犬として分離」（ADR-0005 Reflection 追補）。

### 実証データ（dw-experiment ブラインド検証 2026-05-29）
LAM ツール群を DW で**対話文脈ゼロのコールド分析**させた実走の実測:
- 構成: sonnet×3 + opus×1 並列、約133秒。
- 出力増分: `outputTokensDelta` ≈ **20,934 tokens**（`rawSpent` 22,440 / エージェント総消費 252,259。入力・キャッシュ込みの実勢は `/usage` 参照）。
- 所見: 絞った構成（同スコープ・同モデル）なら破綻的コストにはならず、奥の手3兄弟（MAGI / full-review / lam-orchestrate）と同オーダー。「10分で5時間溶けた」級の消費は throttle 全開時の話。
- DW はコールド fan-out のみで対話結論の骨格（最重要論点含む）の約7割を独力再発見し、加えて FR-9 の3 catch（自己破壊的再帰 / 隔離≠不可逆境界 / 敵対検証の非決定性）を返した。
- 実験記録の所在: `docs/memos/dw-experiment/`（**ローカルスクラッチ・非コミット**。comparison.md / dw-output.md 等）。

### 採用再評価条件（昇格トリガー）
以下のいずれかで再評価（ADR-0005 見直しトリガーと整合）:
- $200 Max（Max 20x）以上へ移行した場合。
- 絞った構成（fan-out 幅 × モデル階級 × 反復を限定）の実測コストが、週 Opus 枠の許容内（例: 1ラン週枠 5% 未満）と確認できた場合。
- `/goal` core では到達困難なスケール（十万行規模 migration 等）の必要が生じた場合。

### 採用する場合の統治ガードレール（要点）
DW を A 層の実行エンジンとして採用する場合も、**統治（B 層 / C 層 / PM 境界）は DW の外側に必ず残す**:
- DW スクリプト内 `agent()` に PM 級書込権限を与えてはならない（FR-9.1 と整合）。
- 決定的 checker は DW の budget 例外を流用せず独立に張る（FR-4 / FR-9.3 と整合）。
- worktree 隔離を C 層遮断と混同しない。merge / push / 隔離外操作の不可逆ガードは隔離の外で張る（FR-9.2）。
- DW 採用時の完全な must-preserve 制約（9項目）と移植ロードマップ（4フェーズ）は `dw-experiment/dw-output.md`（ローカル）に記録済み。昇格判断時に参照。

## 見送り候補2: Agent Teams

### 決定
core 採用を**見送る**（experimental・$100 Max 制約）。

### 見送り理由
- experimental 機能であり、core 依存は安定性リスク。
- MAGI が Agent Teams と概念対応する（ADR-0005）が、MAGI は in-context で安価に同等の多視点合議を提供でき、core には MAGI で足りる（D4 の last-line 段階化）。

### 採用再評価条件
- Agent Teams が GA（一般提供）化し、$100 Max 枠で実用的になった場合。
- MAGI（in-context）では不足する規模の相互チャレンジ（findings の相互 challenge）が必要になった場合。

## 参照
- [requirements.md](./requirements.md) FR-6.2 / FR-6.3 / RQ-5
- [ADR-0005](../../adr/0005-thin-harness-autonomous-governance.md) Non-Goals / 見直しトリガー / Reflection 追補
- [design.md](./design.md) D6
