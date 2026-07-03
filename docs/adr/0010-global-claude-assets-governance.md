# ADR-0010: グローバル ~/.claude 資産の統治（12 番目の統治対象リポジトリ化）

## メタ情報

| 項目 | 内容 |
|------|------|
| ステータス | **Accepted**（2026-07-04） |
| 日付 | 2026-07-04 |
| 意思決定者 | sougetuOte（最終承認）/ Living Architect（起草）/ Fable 5 HGA 召喚 #4（設計分岐点の正本） |
| 関連 ADR | [ADR-0009](./0009-hga-fable-summoning.md)（HGA 召喚 #4 の運用根拠）, [ADR-0007](./0007-magi-v2-gabriel-integration.md)（gabriel = agent 伝播の最初の適用対象） |
| 関連資産 | `docs/artifacts/global-claude-assets-governance-2026-07-03.md`（実施記録・全記録）, `docs/artifacts/hga-summon-log.md`（召喚 #4）, `C:\etm-diary\ops\handoff\2026-07-03-global-claude-assets-fix-request.md`（依頼書原本） |

---

## コンテキスト

### 背景

etm-diary の全方位監査で Critical ②「グローバル `C:\Users\metral\.claude\` 資産の統治不在」が検出された。
実害として、etm-diary で `/ship` 実行時にプロジェクト版でなく**グローバル汎用版が起動**し、
規約の CHANGELOG 再生成工程が欠落した（手動補完で回復）。

根本原因は upstream-first で確定済み（2026-07-03 公式ドキュメント裏取り）:
Claude Code のスキル名解決は **`enterprise > personal(~/.claude/skills) > project(.claude/skills) > bundled`**
であり、**personal（グローバル）が project を常に上書きする**。逆転設定は存在しない。
つまり事故はバグではなく仕様どおりの挙動であり、独自スキルを持つ全プロジェクト
（グローバル 15 スキル中 9 スキルが customized PJ を shadow）に波及していた。

**問題の本質（HGA #4 盲点指摘）**: 個別のスキル衝突ではなく、
「全 governed プロジェクトの上に、無統治の可変層（skills / hooks / settings / memory）が座っていた」こと。
したがって解は衝突の個別解消ではなく、**グローバル層そのものを 12 番目の統治対象リポジトリにする**
という枠取りである。

### 制約条件

- plugin スキルは `plugin-name:skill-name` 名前空間でどの層とも衝突しない（公式明記）
- plugin スキルは `skillOverrides` 設定の影響を**受けない** → enable 粒度が唯一の防御線
- 既知バグ #25209: project と global の同名スキルが一覧に「両方表示」される表示非決定性
  → 検証は一覧でなく実挙動（成果物差分）で行う必要がある
- `~/.claude` には PII（memory）・credential（`.credentials.json`）・transcript が同居しており、
  バックアップ設計は漏洩防止と不可分
- 権限等級: **PM 級**（`docs/adr/` の新規作成）

### 要求事項

1. スキル shadow の構造的解消（再発を状態でなく構造で防ぐ）
2. グローバル資産のバックアップ体制（PII / credential を漏らさない）
3. 再発防止の不変条件を検査可能な形で明文化する
4. 将来の agent 配布（gabriel 等）に耐える伝播経路を予約する

---

## 検討した選択肢

### Option A: 共有 harness の名前空間 plugin 化

**概要**: グローバル 15 スキルを `lam-harness` plugin として marketplace（`lam-global`）経由で配布し、
`/lam-harness:<skill>` 名前空間で解決させる。

**メリット**: 名前空間によりどの層とも構造的に衝突しない / versioned SSOT 化できる
**デメリット**: 単独では personal 層の裸スキルが残り shadow が解消しない

### Option B: personal 層のゼロ空化 + project vendored

**概要**: `~/.claude/skills/` を原則ゼロに空化し、customization は各 project の実体ファイル（vendored）で持つ。

**メリット**: shadow の発生源そのものを除去
**デメリット**: 単独では harness 依存 PJ（godot-test / plactice-range / Kyozai-Athanor）が全損する

### Option C: 非衝突スキルのみグローバルに残す

**概要**: 衝突マトリクスで「衝突なし」と判定された 6 スキルだけを personal 層に残す。

**メリット**: 移行作業が最小
**デメリット**: **致命傷 —「衝突しない」は現時点の状態であって構造ではない**（HGA #4 決定打）。
どの PJ かが将来同名スキルを作った瞬間に shadow が再発し、検査で防げない。

---

## 3 Agents Analysis

> 本決定の敵対的検証は HGA 召喚 #4（Fable 5 / 無条件召喚ゾーン = 不可逆設計コミット + 複数ドメイン統合）
> が担った。以下はその要約を 3 Agents 形式に写像したもの。

### [Affirmative] 推進者の視点

- A+B ハイブリッドで shadow の構造的解消と harness 共有を両立できる
- plugin 化により harness が versioned SSOT になり、配布・ロールバックが git 操作に還元される
- グローバル層の git 化で「12 番目の統治対象リポジトリ」として既存の LAM 統治に編入できる

### [Critical] 批判者の視点（HGA #4 の指摘を含む）

- **plugin のグローバル enable は罠**: skillOverrides が plugin に無効なため、グローバル enable すると
  customized PJ 側に防御レバーが一切なくなる → enable はプロジェクトスコープ限定が必須
- 草案不変条件の「衝突しうるスキルを置かない」は**未来依存で検査不能**（決定可能性欠陥）
  → 構成的（その場で検査可能な）条件に書き直す必要
- スキルだけ塞いでも hooks / settings / memory が同じ火薬庫として残る
- バックアップで PII（memory）と公開候補資産が同居すると漏洩リスク
- #25209 により「一覧で確認した」は検証にならない

### [Mediator] 調停者の視点

- A+B ハイブリッドを採用し、不変条件は**構成的 5 条 + 追補**として ADR 化する
- バックアップは repo の「運命」（private 必須 / 公開候補）で分割し、PII は公開候補と決して同居させない
- 検証は実挙動（成果物差分）ベースに統一する

---

## 決定

**採用**: Option A + B のハイブリッド（Option C は棄却）

1. 共有 harness は `lam-harness` plugin（marketplace `lam-global` / 実体 `~/claude-global-assets/lam-marketplace/`）
   としてのみ配布する
2. personal 層（`~/.claude/skills/`）は原則ゼロに空化する
3. customization は各 project の vendored 実ファイルで持つ
4. plugin の enable はプロジェクトスコープ限定とする
5. グローバル層を git 統治下に置く（下記バックアップ不変条件）

### 却下理由

- **Option A 単独 / B 単独**: 上記デメリットのとおり片翼では要求を満たさない
- **Option C**:「衝突しない」は状態であって構造でない。将来の同名スキル作成で無検査に再発する

### 統治不変条件（構成的 / その場で検査可能）

- **I-1**: project を名前解決で上書きできる層（enterprise / personal）には、ユーザー起動・モデル起動
  スキルを置かない（原則ゼロ）。共有 harness は名前空間付き plugin としてのみ配布する。
- **I-2**: plugin の enable はプロジェクト設定スコープでのみ行う。project 層に機能的対応物を持つ PJ は
  重複 plugin スキルを enable しない（skillOverrides は plugin に無効 = enable 粒度が唯一の防御線）。
- **I-3**: project 層のスキルは実体ファイル（vendored）。他所への symlink 禁止。
- **I-4**: CLAUDE.md 等からのスキル参照は名前空間を常に明示する（例: `/lam-harness:ship`）。
- **I-5**: personal 層に残る共有可変資産（hooks / settings）は版管理下に置き、変更は commit を伴う。
- **I-6**（agent 伝播 / gabriel 前準備）: 共有 **agent** の配布もスキルと同一チャネル
  （versioned plugin の `agents/` ディレクトリ）で行う。personal 層（`~/.claude/agents/`）への
  共有 agent 直置きは I-1 と同型の無統治層を作るため禁止。`lam-harness` plugin は現状 `skills/` のみで
  あり、gabriel 配布時に `agents/` 追加 + plugin version bump を伴う（未 versioned 状態への
  先行投入はしない — 2026-07-03 PM 決定「本筋先行 → 整備済 channel で一度だけ配布」）。

### バックアップ不変条件（2 repo 構成 / 2026-07-03 PM 判断）

- **B-1（repo1 / private 絶対）**: `~/.claude` を default-deny allowlist git 化
  （`*` ignore + `!skills/ !hooks/ !settings.json !memory/` opt-in）。**private remote 限定**。
  remote = `https://github.com/sougetuOte/claude-global-config`（private / 2026-07-04 push 済み）。
- **B-2（repo2 / 公開候補）**: `~/claude-global-assets`（marketplace）を git 化 = harness SSOT 兼バックアップ。
  **PII 混入禁止**。公開する場合は絶対パス・ユーザー名スクラブをゲートとする。
  remote = `https://github.com/sougetuOte/claude-global-assets`（当面 private で運用 / 2026-07-04 push 済み）。
- **B-3（絶対除外）**: `.credentials.json` / `projects/` transcript / `backups/` / `.session-*` は
  いかなる repo にも含めない。
- **memory 統合の解釈（HGA #4 からの変更を明文化)**: HGA #4 正本は「memory(PII) は別 private repo」
  （運命別 3 分割）だったが、**A+B 統合（2 repo）に変更**した。PII 不変条件の本質は
  「**PII を公開候補 repo（B-2）と同居させない**」ことであり、非公開が保証された repo1 への統合は
  不変条件を破らない。変更理由 = 人間の操作ミス最小化（push 先取り違えの機会削減）。

### 移行順序不変条件

- **M-1**: 空化（personal 層からの除去）は、依存 PJ 全ての plugin 移行（enable + 参照書換）が
  完了した**後**にのみ実行する。逆順は依存 PJ の全損を招く（Kyozai-Athanor が実例:
  自前フェーズスキルを削除しグローバル依存だったため、空化先行なら全損だった）。
- **M-2**: 除去は削除でなく quarantine 移動（1 行で復元可能な状態を維持）とし、
  behavioral 検証グリーンまで quarantine を保持する。

### 再検証トリガー条項

- **R-1**: Claude Code のメジャー更新時、I-1 / I-2 の前提（`personal > project` 解決順・
  plugin 名前空間の非衝突・skillOverrides の plugin 無効）を公式ドキュメントで再裏取りする。
- **R-2**: 検証は #25209（一覧表示の非決定性）が解消されるまで、一覧でなく
  **実挙動（生成された成果物が規約工程を含むか）** で判定する。
- **R-3**: 新規プロジェクト立ち上げ時・plugin への skill/agent 追加時に I-1〜I-6 への適合を確認する。

---

## 影響

### ポジティブな影響

- スキル shadow の構造的解消（behavioral 検証で 6 PJ グリーン確認済み / 2026-07-03）
- グローバル層が versioned SSOT + バックアップ体制下に入り、「無統治の可変層」が消滅
- gabriel 以降の agent 配布経路が予約済みになる（I-6）

### ネガティブな影響

- harness 利用 PJ はスキル名が長くなる（`/ship` → `/lam-harness:ship`）
  （緩和策: 自前 customize したい PJ は vendored 化すれば短名を維持できる）
- plugin enable / 参照書換が新規 PJ セットアップの追加手順になる
  （緩和策: R-3 をセットアップチェックリストに含める）

### 影響を受けるコンポーネント

- `~/.claude/skills/`（空化済み / quarantine: `~/.claude/backups/skills-emptied-2026-07-03/`）
- `~/claude-global-assets/lam-marketplace/`（plugin SSOT / repo2）
- godot-test / plactice-range / Kyozai-Athanor（enable + 参照書換済み）
- etm-diary（`/retro` の自己対応が必要 — 当方不介入）

## 実装計画

- [x] Stage 1-4: plugin 構築 / 依存 PJ 移行 / 構造検証 / 空化（2026-07-03 完了）
- [x] behavioral 検証: 6 PJ グリーン（2026-07-03）
- [x] Stage 5（ローカル）: repo1 `58a603c` / repo2 `ae958e5` 初回 commit + allowlist 検証
      （credential / transcript / secret 混入 0）
- [x] Stage 5（残）: private remote 作成 + push（2026-07-04 完了 / gh CLI 認証済み環境で AI 実行・
      両 repo の visibility=PRIVATE を API 確認。repo1 は push 前に memory 差分 commit `03c1fc2` を追加）
- [ ] Stage 7: etm-diary へ完了報告（実施記録 §7 の様式）
- [ ] gabriel 配布時: `lam-harness` に `agents/` 追加 + version bump（I-6 / ADR-0007 側の BUILDING と連動）

## 検証方法

- 実挙動検証（R-2 方式）: 各 harness 依存 PJ の実セッションで `/lam-harness:*` の成果物差分を確認
  → 2026-07-03 グリーン（`SESSION_STATE.md` 検証チェックリスト / 実施記録 §8）
- 見直しトリガー: R-1〜R-3 のとおり

## 参考資料

- `docs/artifacts/global-claude-assets-governance-2026-07-03.md`（実施記録 = 本 ADR の事実基盤）
- `docs/artifacts/hga-summon-log.md` 召喚 #4（設計分岐点の正本）
- `docs/artifacts/2026-07-03-magi-4th-launch-test.md`（gabriel 配布順序の PM 決定・合議録）
- Claude Code 公式: スキル解決順 / plugin 名前空間 / skillOverrides 仕様（2026-07-03 裏取り）
- 既知バグ #25209（スキル一覧の表示非決定性）
