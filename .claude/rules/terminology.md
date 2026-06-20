# 用語ガイドライン

v4.0.0 以降、プロジェクト内の用語を統一し、ドキュメント・コミット・口頭での誤用を防ぐ。
2026-06-20 MAGI 合議（Atom2）で方針確定（案 E 採用）。

## §1 用語階層

LAM プロジェクトの作業単位は以下の 4 層で構成される。

```
Project
  └─ Milestone（例: B-4, B-5）
       └─ Step（例: PLANNING, BUILDING, AUDITING、または準備段階）
            └─ Wave（例: Wave 1, Wave 1.5）
                 └─ Task（例: PR-A, PR-B, T9）
```

### 主要用語

| 用語 | 位置 | 形式の例 |
|------|------|---------|
| Project | 最上位 | LAM（Living Architect Model） |
| Milestone | Project 直下 | B-4, B-5, cc-spec-alignment |
| Step | Milestone 直下 | PLANNING, BUILDING, AUDITING |
| Wave | Step 直下 | Wave 1, Wave 1.5, Wave 2 |
| Task | Wave 直下 | PR-A, PR-B, T9, W7-B4-T9 |

### 補助用語

| 用語 | 説明 |
|------|------|
| **Phase** | PLANNING / BUILDING / AUDITING の三フェーズ規律（`phase-rules.md` で定義）。「どのモードで作業するか」を示す。Step の概念とは独立しており、Step 名が Phase 名と一致する場合でも混同しないこと |
| **PR** | Pull Request または作業パッケージ（コード変更を PR として提出しない場合でも、Wave 内の論理的なグループ単位として使用する） |

## §2 各用語定義

### Project

最上位の識別子。複数の Milestone を包含する。
LAM（Living Architect Model）が現プロジェクトの Project 名。

### Milestone

Project 内の大きな区切り。アルファベット 1 文字 + ハイフン + 数字の形式（例: B-4, B-5）。
四半期やリリースに相当する粒度で区切られる。一度クローズした Milestone は再開しない。
次のアクションを定義した `tasks.md` を持ち、retro（振り返り）でクローズする。

> **Milestone と Step の区別**: Milestone は「何を達成するか」という目標の束。
> Step は「どの段階にいるか」というプロセスの位置。
> B-4 PLANNING は「Milestone B-4 の PLANNING Step（段階）」であり、
> 「Milestone B-4 は PLANNING フェーズにある」ではない。

### Step

Milestone 内の段階。典型的には PLANNING / BUILDING / AUDITING の Phase 名と対応するが、
「準備段階」や「調査段階」等の固有名を付ける場合もある。
1 Milestone は複数の Step を順番に経由する。
Step は Phase 規律（`phase-rules.md`）と紐付き、承認ゲートで遷移する。

> **Step と Phase の二面性**: 「PLANNING」はフェーズ規律としての Phase 名でもあり、
> Milestone 内の段階としての Step 名でもある。文脈に応じて「PLANNING フェーズ」（規律的意味）か
> 「PLANNING Step」（進行位置の意味）かを使い分ける。

### Wave

Step 内の実装の波。同一 Step 内で複数の Wave が存在することがある（例: Wave 1, Wave 1.5）。
Wave 1.5 は Wave 1 の後処理・修正として付番するパターン（影響波及修正等）。
Wave は必ず正整数または「整数.5」形式で付番する（Wave 1a 等のアルファベット混在は使わない）。

> **Wave と Task の区別**: Wave は複数の Task をまとめた「実装のバッチ」。
> Task は Wave 内の個別作業単位（例: 1 PR、1 ファイル変更グループ）。

### Task

Wave 内の個別作業。PR 単位または論理的なグループ単位で定義する。
`tasks.md` 内では `W<wave>-<milestone>-T<number>` の形式で記録する（例: W7-B4-T9）。
口語では PR-A, PR-B 等の短縮形も許容する。

### Phase（補助用語）

`phase-rules.md` が定義する三フェーズ規律（PLANNING / BUILDING / AUDITING）。
「現在のフェーズ」は `.claude/current-phase.md` で管理される。
Step と重複する用語であるが、Phase は**規律・ガードレール**の文脈で使い、
Step は**Milestone 内の進行位置**の文脈で使う。

## §3 正例・誤例

### ペア 1: Milestone と Step の混在

| | 表現 |
|---|------|
| 誤 | 「B-4 の Wave 1 PLANNING を開始する」（PLANNING は Step であり Wave の修飾語ではない） |
| 正 | 「B-4 PLANNING Step の Wave 1 を開始する」または「B-4 Wave 1 を開始する（BUILDING Step）」 |

### ペア 2: Phase と Step の混同

| | 表現 |
|---|------|
| 誤 | 「B-4 は現在 PLANNING フェーズにある」（フェーズは規律の文脈で使う） |
| 正 | 「B-4 は現在 PLANNING Step にある」または「現在のフェーズ（規律）は PLANNING である」 |

### ペア 3: Wave の付番形式

| | 表現 |
|---|------|
| 誤 | 「B-4 Wave 1a（後処理）」、「B-4 Wave 1-hotfix」 |
| 正 | 「B-4 Wave 1.5（後処理・影響波及修正）」 |

### ペア 4: Task と Wave の粒度混在

| | 表現 |
|---|------|
| 誤 | 「Wave PR-A を実施する」（PR-A は Task であり Wave ではない） |
| 正 | 「Wave 1 の Task PR-A を実施する」または「PR-A を実施する（Wave 1 内）」 |

### ペア 5: Milestone の再利用・重複

| | 表現 |
|---|------|
| 誤 | 「B-4 Wave 3 を開始する」（Milestone B-4 を終了後に B-4 内の Wave を追加する） |
| 正 | 「Milestone B-4 はクローズ済みのため、追加作業は B-5 として立ち上げる」 |

### ペア 6: Project と Milestone の混同

| | 表現 |
|---|------|
| 誤 | 「cc-spec-alignment プロジェクト B-4 を開始する」（cc-spec-alignment は Milestone） |
| 正 | 「LAM プロジェクトの cc-spec-alignment Milestone を開始する」 |

### ペア 7: Step 省略による曖昧さ

| | 表現 |
|---|------|
| 誤 | 「B-4 の Wave 1 が完了した」（どの Step の Wave 1 か不明） |
| 正 | 「B-4 BUILDING Step の Wave 1 が完了した」 |

## §4 命名規則

### ファイル名

| 成果物 | 命名パターン | 例 |
|--------|------------|-----|
| Milestone の仕様書ディレクトリ | `docs/specs/<milestone-slug>/` | `docs/specs/v5-fat-reduction/` |
| Milestone の retro | `docs/artifacts/retro-<milestone>-<wave>-<date>.md` | `retro-B4-W1-W15-2026-06-20.md` |
| Milestone の監査成果物 | `docs/artifacts/<topic>-<date>.md` | `v5-fat-audit-2026-06-19.md` |
| Wave 別のタスクログ | `docs/artifacts/tdd-patterns/<YYYYMMDD>-<topic>.md` | — |

ファイル名に Milestone・Wave を含める場合は以下の略記を使用:
- Milestone B-4 → `B4`（ハイフンを除く）
- Wave 1 → `W1`、Wave 1.5 → `W15`

### コミットメッセージ接頭辞

Conventional Commits に従い、スコープに Milestone を記載する:

```
<type>(<milestone>): <subject>
```

| type | 用途 |
|------|------|
| `feat` | 新機能・新仕様の実装 |
| `fix` | バグ修正・誤用修正 |
| `docs` | ドキュメント・仕様書更新 |
| `chore` | 管理作業（gitignore, phase 切替等） |
| `refactor` | 振る舞いを変えないリファクタリング |
| `test` | テスト追加・修正 |

例: `docs(B-4): Wave 1.5 波及不整合修正（W-1〜W-5）`

> Task 単位のコミットは Wave 番号を subject 末尾に付記することを推奨する（例: `Wave 1 PR-A`）。

### ブランチ名

```
<milestone>/<step>-<brief-topic>
```

例: `B-4/building-wave1-nfr-cleanup`

ただし本プロジェクトは master 直コミット体制が多く、ブランチを切る場合のみ適用する。

### SESSION_STATE・タスクリスト内の参照

- Milestone を参照する場合: `B-4`（大文字・ハイフンあり）
- Wave を参照する場合: `Wave 1`（大文字 W + 半角スペース + 数字）
- Task を参照する場合: `PR-A`、`T9`、`W7-B4-T9` のいずれかを文脈に応じて使用

## §5 移行猶予条項

### 適用開始日

本ガイドラインは **2026-06-20 00:00:00 JST（commit タイムスタンプ基準）** 以降に
作成・更新されるドキュメント・コミットメッセージ・ブランチ名に適用する。

### 猶予期間

| 対象 | 猶予 |
|------|------|
| 2026-06-20 より前に作成済みのファイル（SESSION_STATE, retro, specs 等）の既存記述 | 修正不要（旧表記のまま維持してよい） |
| 2026-06-20 以降に同ファイルを **更新** する場合の追記部分 | 本ガイドラインに従う |
| 2026-06-20 以降に **新規作成** するファイル | 本ガイドラインに完全準拠 |

### 判定基準

- コミットのタイムスタンプ（author date）が 2026-06-20 以降であれば新規適用対象
- PR 単位で複数コミットを含む場合、最初のコミットのタイムスタンプで判定する

### 経過措置

既存ドキュメントの誤用を発見しても、猶予期間内の旧記述を理由に監査 Warning を起票しない。
ただし、CLAUDE.md への 5 行ミニ辞書追記（別タスク）完了後は、
新規記述での用語誤用を **Info** レベルで指摘することを許容する。

## §6 権限等級

本ルールファイル（`.claude/rules/terminology.md`）の変更: **PM級**

用語の追加・削除・定義変更はプロジェクト全体の一貫性に影響するため、
必ず人間の承認を得てから変更すること。

## 参照

- `docs/internal/06_DECISION_MAKING.md`（MAGI 合議ログ、Atom2 用語方針）
- `.claude/rules/phase-rules.md`（フェーズ規律の定義）
- `.claude/rules/permission-levels.md`（権限等級分類基準）
- `CLAUDE.md`（5 行ミニ辞書を §Terminology に記載済み）
- `SESSION_STATE.md`（MAGI 合議結果 2026-06-20）
