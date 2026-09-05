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
- **I-4**: CLAUDE.md 等からの**スキル参照および agent 参照**は名前空間を常に明示する
  （例: `/lam-harness:ship` / `subagent_type="lam-harness:gabriel"` / frontmatter の `tools: Agent(lam-harness:...)`）。
  **拘束するのは著者が書く正本であり、正本から機械的に導出された派生物は対象外**（射程の限定は追補 2）。
  agents への射程は追補 1 の R-1 で判明していたが**条文本体は約 2 か月未追随だった**（追補 2 で是正）。
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

---

## 追補 1（2026-09-04 / **所在の変更** / ユーザー決定）

### 決定

**`lam-harness` plugin の所在を `~/claude-global-assets/lam-marketplace/` から LAM リポジトリ内へ移す。**
marketplace の登録元も `source: directory`（ローカルパス）から **GitHub リポジトリ `sougetuOte/LivingArchitectModel`** へ変更する。

### 変えないもの（本 ADR の本体は存続する）

**統治不変条件 I-1 〜 I-6 はすべて存続する。** 特に:

- **I-1**: 共有 harness は名前空間付き plugin としてのみ配布する（**本 ADR の核心であり、2026-09-04 の MAGI + HGA #29 も独立に同じ結論に到達した**）
- **I-2**: enable はプロジェクトスコープ限定
- **I-4**: スキル参照は名前空間を常に明示する（**下記 R-1 再裏取りにより、射程が agents にも及ぶことが判明**）
- **I-6**: 共有 agent も同一チャネルで配布

バックアップ不変条件 **B-1 / B-3**、移行順序不変条件 **M-1 / M-2** も存続する。

### 変わるもの

| # | 旧 | 新 |
|:-:|:--|:--|
| 決定 1 の所在 | `~/claude-global-assets/lam-marketplace/` | **LAM リポジトリ内の plugin ディレクトリ**（`.claude-plugin/marketplace.json` はリポジトリルート） |
| marketplace source | `directory`（ローカルパス） | `github` / `sougetuOte/LivingArchitectModel` |
| **B-2 の位置づけ** | `~/claude-global-assets` = **harness SSOT 兼バックアップ** | harness SSOT ではなくなる。**同リポジトリ自体の存廃は本追補では決めない** |

### 変更の根拠

**1. K4「配布集合 ⊆ 開発ロード集合」が実際に破れており、2 か月間検出されなかった。**

2026-09-04 の実測: `lam-harness` 1.0.0 の skills 14 件のうち **9 件が現行 LAM に存在しない**
（`audit-mode` / `build-mode` / `design-mode` / `clarify` / `project-status` / `session-load` /
`session-save` / `tdd-twada` / `ui-design-guide`）。2026-07-02 の世代で凍っていた。

別リポジトリに置く構成は、**同期の仕組みを持たない限り必ず drift する**。これは本 ADR の欠陥ではなく、
「配布物と開発物を別の場所に置く」構成そのものの性質である。

**2. D-1（2026-08-13 クローズ）がリポジトリ分割を死んだ案 #5 として棄却している。**

D-1 は「self-hosting 維持下では開発環境 = 製品リポジトリであり分割対象が存在しない」とし、
境界は**パッケージング境界**として実装せよと定めた。plugin ディレクトリをリポジトリ内に置く構成は、
この命令に正面から合致する（リポジトリを割らずにパッケージング境界を得る）。

**3. GitHub の star・URL・31 リリースが公開の動機に直結する資産である**（ユーザー明示）。
配布の入口が `LivingArchitectModel` であることは、この資産と整合する。

**4. K4 をテストにできる。** plugin ディレクトリがリポジトリ内に実在すれば、
「配布物が自分の外を参照しない」「開発側が配布物を包含する」を**基質から導出できる検査**として置ける
（HGA #29 §13.5-B / R3 機構 #7・#10 と同型 / 維持リスト不要）。別リポジトリ構成ではこの検査が置けない。

### R-1（再検証トリガー）の実施記録

本 ADR の **R-1**「Claude Code のメジャー更新時、I-1 / I-2 の前提を公式ドキュメントで再裏取りする」を
**2026-09-04 に実施した**（制定時 v2.1.x 初期 → 現在 **v2.1.259**）。結果:

| 前提 | 判定 |
|:--|:--|
| `personal > project` の解決順 | 本追補では未再確認（**残課題**） |
| plugin 名前空間の非衝突 | **確認**。skills は `/plugin:skill`、**agents も `plugin:agent`**（本セッションの agent 一覧に `hookify:conversation-analyzer` が実在 / ファイル側 frontmatter は `name: conversation-analyzer`）。→ **I-4 の射程は skills だけでなく agents にも及ぶ**（LAM の `subagent_type` 参照が該当） |
| `skillOverrides` の plugin 無効 | 本追補では未再確認（**残課題**） |

あわせて確認した上流事実（詳細は `docs/artifacts/2026-09-04-magi-distribution-form.md` §13.6）:

- plugin のコンポーネント在庫は **skills / agents / hooks / MCP / LSP の 5 種のみ**。**`rules` は配れない**
- **hook は設定レベル間で merge され置換されない**。plugin hook と project hook は**両方走る**
- `marketplace add` は**リポジトリ全体**をディスクに置くが、`plugin install` が展開するのは **plugin ディレクトリのみ**
- **hook の exit 2 以外の非零終了は非ブロッキング**で、トランスクリプトに `hook error` 通知 + stderr 1 行目が出る（**インタプリタ不在の 127 も同じ**）→ ランタイム不在時は **fail-open とノイズが同時に起きる**
- plugin manifest に**ランタイム依存の宣言機構は無い**（公式 plugin `security-guidance` は `sg-python.sh` で自力解決している）

### 移行の残課題（本追補では決めない）

1. `~/claude-global-assets/lam-marketplace/` の `lam-harness` 1.0.0（現在 4 プロジェクトに project スコープで導入済・**全て disabled**）の扱い。**M-2 に従い削除ではなく quarantine とする**
2. `personal > project` 解決順と `skillOverrides` の再裏取り（R-1 の未了分）
3. ランタイム不在時の挙動をどう扱うか（`/lam:init` で検査して完了を拒む案が HGA #29 の推奨）

### 経緯

`docs/artifacts/2026-09-04-magi-distribution-form.md`（MAGI AoT 6 Atom + gabriel 2 巡 + **HGA #29**）§15。
本追補の所在変更はユーザー決定（2026-09-04 / 選択肢 3 案の提示に対し「LAM リポジトリ内に plugin を移す」）。

---

## 追補 2（2026-09-05 / **複製の向きの確定と I-4 の射程限定** / ユーザー決定 + HGA #33）

### 契機

第 1 段 E2E（`docs/artifacts/2026-09-05-magi-migration-sequence.md` §(D)）で、**plugin 由来の agent は
`subagent_type` において必ず名前空間が付き、bare 名は解決しない**ことを実測した（生エラーで確認）。
これは追補 1 の R-1 が観測メモとして記していた「I-4 の射程は agents にも及ぶ」の**独立な再確認**であり、
同時に **Accepted な不変条件が約 2 か月実装されていなかった**という遵守ギャップの発見でもある。

MAGI（AoT）2 巡 + gabriel 2 巡がいずれも `refuted & critical`（AC-W-C-7 到達）に至り、**HGA #33** を召喚した。

### 決定 1: 複製の向きの一般規則 —— **正本は、第 2 段の後に生き残る側**

LAM は現在、skills / agents / hooks を `.claude/` と `plugins/` の**両方に実体を持つ複製相**で運用し、
機構 #11 の T3 が**バイト恒等性**を強制している。この構造は「**同じ事実を 2 人が書き、検査で一致を強制する**」形であり、
「LAM 本体は bare で動く」と「配布物は namespaced」を**定義上同時に成立させられない**（二律背反の原因は条件ではなく構造）。

**複製相は「手で 2 部 + 恒等性検査」から「正本 1 部 + 変換つき生成」へ解体する。導出の向きは次の規則で決める:**

> **正本は、第 2 段（self-hosting = project 側撤去）の後に生き残る側に置く。**

| 領域 | 正本 | 派生 |
|:--|:--|:--|
| rules（規範 markdown） | **`.claude/rules/`** | `plugins/*/templates/managed/rules/`（plugin は rules を運べないため） |
| skills / agents / hooks | **`plugins/lam-harness/`** | `.claude/{skills,agents,hooks}/`（第 2 段で撤去される側） |

**T1（templates は `.claude/` から派生）と T3（`.claude/` は `plugins/` から派生）の向きが逆に見えるのは正しい** ——
どちらも同じ規則の帰結である。

**根拠（HGA #33 裁定 1）**:

1. **情報量の向き**: `lam-harness:gabriel → gabriel` は固定 prefix の除去で**無損失**。
   逆向きは 63 箇所の `gabriel` を「実行指示か概念名か」**分類**する必要があり、**分類は導出ではない**
2. **第 2 段との整合**: 撤去されるのは `.claude/` 側である。**派生側 = 撤去される側**にしておけば、
   第 2 段は「生成を止めて派生物を消す」**純粋な削除**になる
3. **staleness は操作者に見える側へ置く**: 派生が古くなるのが `.claude/` 側なら L1 が同セッション内で踏む。
   plugin 側が古いままなら**利用者が踏むまで誰も気づかない**

**副次効果**: この向きなら **`.claude/` 側のバイトは 1 つも変わらない**。したがって
**LAM 本体を plugin 有効化する必要がなく、第 2 段の前倒しにあたらない**（HGA #31 4-a を破らない）。

### 決定 2: I-4 の射程限定 —— **拘束するのは正本のみ**

派生物はテキスト上 bare 名を含む。**I-4 は「著者が書く正本」を拘束し、機械的に導出された派生物は対象外**とする。
検査は「派生 == 導出(正本)」と「**正本側に bare の実行参照が残っていないこと**」の 2 本で閉じる
（前者だけでは、正本に bare が残ったまま両側 bare で一致し、**緑のまま配布物が壊れる**）。

### 決定 3: I-4 条文本体に agents を含める（実施済 / 本追補と同時）

追補 1 の R-1 は「射程は agents にも及ぶ」を**観測メモ**として記したが、**条文本体は更新されなかった**。
本追補で条文本体を改訂した。**観測と条文のドリフトは、条文側を直さなければまた失われる。**

### 実測に基づく重大度の更新（2026-09-05）

**bare 参照の危険は「動かない」ではなく「別物が動く」**場合がある。plugin 有効環境の agent 一覧には
**組み込みの bare `test-runner`** が存在するため:

- bare `gabriel` → `not found` で**止まる**（うるさいが安全）
- **bare `test-runner` → 止まらず「組み込みの `test-runner`」が動く**（LAM のものではない）

**エラーになる方がまだ良い。** I-4 を機構で執行する根拠はこの一点で足りる。

### 変えないもの

**統治不変条件 I-1 〜 I-6 はすべて存続する**（I-4 は射程が明確化されただけで、拘束は弱まっていない）。
バックアップ不変条件 B-1 / B-3、移行順序不変条件 M-1 / M-2 も存続する。
**第 2 段のゲート（HGA #31 4-a「第 1 段の合格は第 2 段の許可を意味しない」）も存続する。**

### 却下した案（記録 / 再論しないため）

| 案 | 却下理由 |
|:--|:--|
| **出荷用と生産用のリポジトリを分ける**（ユーザー提案 2026-09-05 / 「理に合わねば却下してよい」と明示） | **LAM 自身の実測が反証**である。`lam-harness` 1.0.0 は**まさに別リポジトリ**に置かれ、**skills 14 件のうち 9 件が 2 か月間 drift して誰も気づかなかった**（M-2 の掃除は 2026-09-05 現在も継続中）。分割は drift を「1 コミット内（検査可能）」から「**リポジトリ間（原子的に検査不能）**」へ移し、根幹目標「開発の継続性」を最も損なう。**提案の背後にある要求（出荷物に開発専用物を混ぜない）は正当**だが、それは**配布境界 `plugins/lam-harness/` と、清浄性の計数**で既に満たされる。**将来 marketplace ホスティングで公開用リポジトリが要る場合は、LAM から一方向に生成する publish target とする**（生成物なら正本は 1 つのまま） |
| project 側 agent の frontmatter `name:` に `lam-harness:gabriel` と書く | plugin 側で**さらに prefix される**ため二重 prefix。上流の name 検証が変われば黙って壊れる |
| bare / namespaced の**両建て**記述 | frontmatter `tools: Agent(...)` は**単一文字列しか書けず完全解にならない**。かつ fallback は**解決失敗を沈黙させる**（`rule-001` 観測 #6 型） |
| 97 箇所を間接記述（「§roster で解決せよ」）に畳む | 散文の間接参照を**解決する機構が無い** |

### 派生する運用変更

**配布の宣伝可否を第 2 段（LAM 自身の self-hosting 段階）に紐づけない。** 配布可否は**配布物の性質**であり、
**清浄環境で「解決しない参照 = 0」**という計数に紐づける（現況の実測は 86 件 / 182 箇所 /
`docs/artifacts/2026-09-05-distribution-scope-review.md`）。

### 参照

- `docs/artifacts/2026-09-05-magi-e2e-defect-remediation.md`（本決定の MAGI + gabriel 2 巡 + HGA #33 全文）
- `docs/artifacts/2026-09-05-magi-migration-sequence.md` §(D)（第 1 段 E2E の実行記録）
- `docs/artifacts/hga-summon-log.md` #33
