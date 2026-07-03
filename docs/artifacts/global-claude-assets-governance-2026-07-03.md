# グローバル ~/.claude 資産の統治整備 — 実施記録

- **日付**: 2026-07-03
- **依頼元**: etm-diary L1（Fable）セッション経由 / ETM（小野哲也）承認
- **依頼書**: `C:\etm-diary\ops\handoff\2026-07-03-global-claude-assets-fix-request.md`
- **担当**: LAM（Living Architect Model）
- **HGA 協議**: 召喚 #4（2026-07-03 / `docs/artifacts/hga-summon-log.md`）
- **フェーズ**: PLANNING → 一部実行（Stage 1-4）

---

## 1. 背景と実害

etm-diary の全方位監査で Critical ②「グローバル `C:\Users\metral\.claude\` 資産の統治不在」が検出された。
実害: etm-diary で `/ship` 実行時、プロジェクト版でなく**グローバル汎用版が起動**し、規約の
CHANGELOG 再生成工程が欠落した（手動補完で事なきを得た）。

---

## 2. 根本原因（upstream-first で確定 / 2026-07-03 公式ドキュメント裏取り）

Claude Code のスキル名解決は **`enterprise > personal(~/.claude/skills) > project(.claude/skills) > bundled`**。
**personal（グローバル）が project を常に上書き**する（公式原文: "enterprise overrides personal, and personal
overrides project"）。逆転設定は存在しない。

→ etm-diary の `/ship` 事故は**バグではなく仕様どおりの挙動**。
→ 影響は etm-diary 単独でなく、**独自スキルを持つ全プロジェクトがグローバル汎用版に shadow されていた**。

### スキル衝突マトリクス（グローバル 15 スキル）

| 分類 | スキル |
|:---|:---|
| 衝突あり（customized PJ を shadow）9 個 | adr-template, clarify, init-harness, magi, project-status, retro, ship, spec-template, ui-design-guide |
| 衝突なし 6 個 | audit-mode, build-mode, design-mode, session-load, session-save, tdd-twada |

補助事実:
- plugin スキルは `plugin-name:skill-name` 名前空間で**どの層とも衝突しない**（公式明記）。
- plugin スキルは `skillOverrides` 設定の影響を**受けない**。
- skills-dir plugin のスコープは配置場所で決まる: `~/.claude/skills/` = personal（全PJ自動ロード）/
  `<project>/.claude/skills/` = project（当該PJのみ）。
- 既知バグ #25209: project と global の同名で「両方表示」される表示非決定性。
  → **是正検証は一覧でなく実挙動（成果物差分）で行う**こと。

---

## 3. HGA 協議の設計判断（正本）

| 分岐点 | 決定 |
|:---|:---|
| 1. 衝突解消 | **A+B ハイブリッド**: 共有 harness を名前空間 plugin 化 / personal skills 層を原則ゼロに空化 / customization は project の vendored 実ファイル。plugin の enable は**プロジェクトスコープ限定**（skillOverrides が plugin に無効なため、グローバル enable すると customized 側に防御レバーがない） |
| 2. バックアップ | 「運命別」3 分割 + `~/.claude` は default-deny allowlist git + private remote。memory(PII) は**別 private GitHub リポジトリ**（ETM 承認済み）。`.credentials.json` は git 化しない |
| 3. 再発防止 | 構成的不変条件 I-1〜I-5 を ADR 化（enterprise 層 / symlink / plugin 意味衝突 / #25209 検証 / 機構名腐敗の 5 穴封鎖） |

### 統治不変条件 I-1〜I-5（ADR 化予定 = Stage 6）

- **I-1**: project を名前解決で上書きできる層（enterprise / personal）には、ユーザー起動・モデル起動
  スキルを置かない（原則ゼロ）。共有 harness は名前空間付き plugin としてのみ配布する。
- **I-2**: plugin の enable はプロジェクト設定スコープでのみ行う。project 層に機能的対応物を持つ PJ は
  重複 plugin スキルを enable しない（skillOverrides は plugin に無効 = enable 粒度が唯一の防御線）。
- **I-3**: project 層のスキルは実体ファイル（vendored）。他所への symlink 禁止。
- **I-4**: CLAUDE.md 等からのスキル参照は名前空間を常に明示（`/lam-harness:ship`）。
- **I-5**: personal 層に残る共有可変資産（hooks / settings）は版管理下に置き、変更は commit を伴う。

**HGA 盲点指摘**: 本質は「全 governed PJ の上に無統治の可変層が座っていた」こと。ADR は
「グローバル層を 12 番目の統治対象リポジトリにする」と枠取りする。

---

## 4. 実施した是正（Stage 0-4）

### Stage 0: スナップショット
`~/.claude/backups/snapshot-2026-07-03-pre-governance/`（skills / hooks / settings / keybindings）

### Stage 1: lam-harness plugin 構築
- 新規: `C:\Users\metral\claude-global-assets\lam-marketplace\`（将来の「12番目の統治対象リポジトリ」）
  - `.claude-plugin/marketplace.json`（marketplace 名 `lam-global`）
  - `plugins/lam-harness/.claude-plugin/plugin.json`（plugin 名 `lam-harness` → `/lam-harness:<skill>`）
  - `plugins/lam-harness/skills/`（グローバル 15 スキルをコピー）
- グローバル `settings.json` の `extraKnownMarketplaces` に `lam-global` を追加（CLI 経由・追加のみ）
- `claude plugin validate` 合格

### Stage 2 + 2-bis: harness 依存プロジェクトの移行
project スコープで `lam-harness@lam-global` を enable + CLAUDE.md 等の参照を `/lam-harness:*` へ書換:
- **godot-test**: `/magi` `/session-save` `/session-load` `/design-mode` 系 → 名前空間化 + 注記追加
- **plactice-range**: `/init-harness` `/retro` `/session-save` `/ship` `/design-mode` `/spec-template` 系 → 同上
- **Kyozai-Athanor**（Stage 4 前の blast radius 精査で新規発見）: グローバル `/design-mode` `/build-mode`
  `/audit-mode` `/project-status` に実依存（自前 planning/building/auditing を cleanup spec で削除済み）。
  CLAUDE.md 表 + `.claude/rules/phase-rules.md:201` を `/lam-harness:*` へ書換 + 注記追加。
  （magi/ship/retro/adr-template/clarify/spec-template/ui-design-guide は Kyozai 自前保有のため裸のまま）

### Stage 3: 実機検証（構造レベル）
- godot-test / plactice-range / Kyozai: `lam-harness@lam-global` **enabled**（project スコープ）
- LAM / etm-diary: available だが **disabled**（意味 shadow 回避 = I-2 成立）
- グローバル / LAM / etm settings に `enabledPlugins.lam-harness` の誤混入なし
- plugin details で 15 スキルが `/lam-harness:*` として解決を確認

### Stage 4: グローバル 15 裸スキルの空化
`~/.claude/skills/` の 15 スキルを `~/.claude/backups/skills-emptied-2026-07-03/` へ quarantine 移動
（削除でなく移動 = 1 行復元可能）。**復元**: `mv "$HOME/.claude/backups/skills-emptied-2026-07-03/"* "$HOME/.claude/skills/"`

---

## 5. blast radius 分析（Stage 4 実行前の全 PJ 依存精査）

`.claude/skills/` **と** `.claude/commands/`（スキル旧形式）両方でローカル保有を判定し、
アクティブファイル（CLAUDE.md / rules / commands / CHEATSHEET / SESSION_STATE）の裸参照のみを実依存と扱った
（歴史 doc・init-harness 雛形は除外）。

| プロジェクト | 判定 | 備考 |
|:---|:---|:---|
| LAM / Novel-Athanor-v2 / Kage-Shiki / Tegetege-dice | 安全 | 使うスキルは skills/commands で自前保有 |
| godot-test / plactice-range / Kyozai-Athanor | 移行済 | plugin 名前空間化 |
| pdf2xlsx | 無依存 | スキル参照なし |
| **etm-diary** | **要自己対応** | `/retro` をローカル未保有 + グローバル依存（SESSION_STATE:66）。当方は etm リポジトリ不介入のため未対応。**etm 側で lam-harness enable か local retro 追加が必要** |

---

## 6. 残タスク（承認ゲート）

- **Stage 5**〔**完了 2026-07-04**〕バックアップ体制 — 2 repo 構成に変更の上、push 完了:
  - repo1 = `~/.claude` → `https://github.com/sougetuOte/claude-global-config`（**PRIVATE** / memory を統合）
  - repo2 = `~/claude-global-assets` → `https://github.com/sougetuOte/claude-global-assets`（当面 PRIVATE / 公開はスクラブゲート後）
  - 変更解釈（3 分割 → 2 repo / memory 統合）は [ADR-0010](../adr/0010-global-claude-assets-governance.md) §バックアップ不変条件に明記
  - 以下は旧計画（記録として保持）:
  - `~/.claude`: default-deny allowlist git（`*` ignore + `!skills/` `!hooks/` `!settings.json` opt-in）+ private remote。
    `.credentials.json` / `projects/` transcript / `backups/` / `.session-*` は絶対除外。
  - memory(PII): 別 private GitHub リポジトリ（ETM 承認済み）。公開候補資産と同一 repo に同居させない。
  - `claude-global-assets`（marketplace）: git 化 → harness の SSOT 兼バックアップ。公開する場合は絶対パス・
    ユーザー名スクラブをゲートに。
- **Stage 6**〔PM級〕ADR 起票: I-1〜I-5 + 移行順序不変条件 + 再検証トリガー条項（CC メジャー更新時に I-2 前提を裏取り）。
  → **起票済み（2026-07-04）**: [ADR-0010](../adr/0010-global-claude-assets-governance.md)。I-6（agent 伝播 / gabriel 前準備）と
  バックアップ 2 repo 構成への変更解釈（memory を repo1 に統合 / PII 不変条件は「公開候補と非同居」）を追補した。
- **Stage 7**〔**完了 2026-07-04**〕etm-diary への完了報告（下記様式）。
  → 報告文書: `D:\work7\claude.md_dev\【完了報告】グローバルclaude資産統治是正-2026-07-04.md`
  （ユーザー経由で etm 側へ受け渡し。etm リポジトリへは不介入）。

---

## 7. etm-diary への完了報告様式（依頼書 §5 対応）

1. **変更一覧**: §4 のとおり（グローバル settings への marketplace 追加 / 15 裸スキル quarantine 移動 /
   godot・plactice・Kyozai の enable + 参照書換。**etm-diary リポジトリは不介入**）。
2. **スキル解決仕様**: §2（personal > project 確定 / plugin 名前空間は非衝突）。
3. **バックアップ所在**: snapshot（`~/.claude/backups/snapshot-2026-07-03-pre-governance/`）+ quarantine
   （`~/.claude/backups/skills-emptied-2026-07-03/`）+ plugin SSOT（`~/claude-global-assets/`）。恒久体制は Stage 5。
4. **etm 側で行う検証手順**:
   - (a) 新セッションで `/ship` を dry-run し、base directory が **etm-diary プロジェクト版**であることを確認
     （personal 層が空になったため、etm 自前の project ship が解決されるはず）。
   - (b) `/magi` も同様に etm 自前版が起動することを確認。
   - (c) **`/retro` は etm がローカル未保有**。空化後は解決不能になるため、**lam-harness plugin を project
     スコープで enable**（`claude plugin install lam-harness@lam-global --scope project` → `/lam-harness:retro`）
     **または** local retro スキルを追加すること。
   - (d) 検証は #25209 のため一覧でなく**実挙動（生成された成果物が規約工程を含むか）**で判定。

---

## 8. 未完了・申し送り

- **behavioral 確認未実施**: 実セッションで `/lam-harness:*` が実起動するかの成果物差分確認は未実施。
  各 harness 依存 PJ（godot-test / plactice-range / Kyozai）の次回実セッションで確認。不良時は §4 の 1 行復元。
- **etm-diary `/retro`**: §5 / §7(c) のとおり etm 側対応要。
- Stage 5-7 は未着手（承認ゲート）。
