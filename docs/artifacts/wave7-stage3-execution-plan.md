# Wave 7 Stage 3 実行計画 — execution-plan.md

- バージョン: 0.4.0
- 作成日: 2026-06-27
- 更新日: 2026-06-28 (v0.3.0 → v0.4.0: NFR-W7-1 CSS 予算根本見直し連動補追 / 上限 10,240 → 16,384 bytes / SHOULD 化 / 3 段階レベル制)
- 作成者: L1 (Opus 4.7)
- ステータス: **Approved** (v0.3.0 ユーザー承認済 + v0.4.0 NFR-W7-1 改定連動補追)
- 根拠文書:
  - `docs/specs/b4-dashboard/wave7/design.md` v0.2.3 Approved
  - `docs/specs/b4-dashboard/wave7/tasks.md` v0.2.3 Approved
  - `docs/specs/b4-dashboard/wave7/requirements.md` v0.2.3 Approved
  - `docs/artifacts/2026-06-27-magi-wave7-stage3-html-structure.md` (本書の方針確定根拠)
- 関連: 本書は Stage 3 (FR-W7-4 / NFR-W7-1) の実行段取りを定義する補助文書。Wave 7 design.md / tasks.md の仕様には踏み込まない (実装手順と並列化方針のみ)

---

## §1 Problem Statement (本書のスコープ)

Wave 7 Stage 3 (T51 + T52 + T53) は以下の高リスク要素を含む:

1. **CSS 予算 18 bytes**: design.md §8 事前評価「Wave 6 終端 9,922 bytes + 追加 ~300 bytes ≈ 10,222 bytes (上限 10,240 / 残 18 bytes)」(v0.2.0 で実機確認: 現状 CSS = 9,922 bytes / utf-8 計測)
2. **既存 V-2 テスト大幅破損**: T51 で V-2 HTML 構造が table → section/article に変わるため、test_v2_view.py 24 件 (実機計測済) のうち table 構造前提の assert が大規模に変わる
3. **同一ファイル並列の困難性**: T51 と T52 が同じ builder.py の別メソッドを編集 → worktree 隔離 overhead と利得のトレードオフ
4. **v0.1.0 で未認識だった構造的乖待**: 現状 `_render_v2_milestones()` は既に複数 Milestone 表示を実装済 (Stage 2 同パターンの先取り実装) だが、HTML 構造が design.md §8 と乖離 → MAGI 合議で「案 A (完全準拠 / 工数増容認)」確定 (v0.2.0 で反映)

本書は上記リスクを踏まえた実行段取り (並列化案・直列化判断・承認ゲート・実機計測手順) を定義する。

---

## §1.5 実装現状調査結果 (v0.2.0 追記 / Stage 1 教訓「PLANNING 段階での実装コード照合」反映)

### Step 1 着手前の L1 実機確認結果

| 項目 | 確認結果 | design.md §8 との照合 |
|:---|:---|:---|
| `MilestoneInfo` フィールド | `name: str, current_step: str, status: str` | ✅ 完全一致 |
| `DashboardData` フィールド | `milestones, waves, tasks, current_phase, generated_at, parser_errors` | ✅ 完全一致 |
| `_render_v2_milestones()` 実装 | builder.py L546-590 / 複数 Milestone ループ + table 構造 | ⚠️ 構造乖離 (table vs section/article) |
| 出力 HTML | `<section id="v2-milestones"><table><tr data-milestone>` | ⚠️ section は OK / 内側 article ではなく table |
| `data-milestone` 属性 | 既に付与 (L570) | ✅ 一致 |
| Milestone 名ソート | **未実装** (出現順そのまま / L567) | ❌ design.md §8 要求の昇順ソート未対応 |
| CSS 現状 | 9,922 bytes (utf-8 / `_render_style()` 戻り値) | ✅ design.md §8 事前評価と完全一致 |
| CSS メソッド名 | 実装 `_render_style` / 仕様 `_render_css` | ⚠️ 用語乖離 (本書 §7 で計測手順に明記) |
| test_v2_view.py 件数 | 24 件 全 PASS | (§8 ロールバック閾値の根拠) |

### MAGI 合議結論 (詳細: `docs/artifacts/2026-06-27-magi-wave7-stage3-html-structure.md`)

- **採用**: 案 A (design.md §8 完全準拠 / section/article 構造)
- **却下**: 案 B (table 維持 + ソートのみ / v0.2.4 補追必要)
- **追加遵守**: Step 5 で Lighthouse 実測 (a11y ≥ 95) を必須化 (Stage 4 T-S4-1 を前倒し相当)

---

## §2 Non-Goals (本書のスコープ外)

- Wave 7 design.md / tasks.md / requirements.md の仕様変更 (既に Approved / v0.2.3 / MAGI 合議で案 A 採用により仕様補追不要)
- T51/T52/T53 の実装内容そのもの (design.md §8 が SSOT)
- Stage 4 (T54/T55) の段取り (別途実施)
- CSS 縮退オプション選定 (実測超過時に L1 が design.md §8 から選定)
- メソッド名乖離 (`_render_css` vs `_render_style`) の解消 (用語整理は本書 §7 で計測手順上「実体は `_render_style`」と明記するに留め、リファクタリングは将来課題)

---

## §3 Alternatives Considered (並列化案の評価)

### A1: T51 + T53a 並列 → T52 → T53b → Lighthouse 実測 (**採用** / MAGI 案 A 反映)

```
Step 1 (並列子 2 / 司令塔不要 / 根拠: CLAUDE.md「委譲の閾値ルール」並列子 2 名以下):
  ┌─ L2#1: T51 builder.py render_v2 改修 (table → section/article + ソート追加)
  └─ L2#2: T53a test_wave7_stage3_milestones.py 新規 (mock fixture 駆動)
  ↓
Step 2 (L1 リレー):
  pytest 全件
  期待値: Step 1 完了時点で T53a 新規 ~10 件 PASS + 既存 test_v2_view.py 破損 N 件
  L1 が破損内容を把握 → §8 閾値照合 → T53b 着手承認 + 修正方針 L2 への伝達材料準備
  ↓
Step 3 (L2 直列):
  T52 CSS 追加 + 実測値報告 (builder.py / `_render_style()`)
  ↓
Step 4 (L2 直列):
  T53b test_v2_view.py 期待値更新 (L1 事前承認済方針)
  ↓
Step 5 (L1 直):
  pytest 全件 PASS 最終確認 + dashboard 再生成 + T-S3-4 視覚確認 +
  Lighthouse 実測 (a11y ≥ 95) + §3.5 更新 + ship + push
```

| 項目 | 評価 |
|:---|:---|
| 並列利得 | Step 1 で T53a を T51 に重ねる ≈ 20-25 分短縮 |
| TDD 順序 | T53a Red 先行 → T51 実装で Green 化 (理想的) |
| 同一ファイル衝突 | T51 (render_v2) と T52 (CSS) を別 Step に分離 → 衝突回避 |
| L1 事前承認タイミング | Step 2 で破損件数確定後に承認 → 待機ゼロ |
| Lighthouse 実測組み込み | MAGI 合議結論で Step 5 に追加 |
| 想定総時間 | ~95 分 (Step 5 Lighthouse 実測 +10 分 を含む) |

### A2: T51 + T52 + T53a 三並列 (**却下**)

- T51 と T52 が同一 builder.py の別メソッド → 並列 Edit で後勝ち衝突 or worktree 隔離必須
- worktree overhead 200-500ms × ファイル管理コスト > 規模 S+M の利得
- → **却下**

### A3: 全直列 (T51 → T52 → T53 → 検証) (**却下**)

- 並列利得ゼロ。安全だが ~110-120 分
- T53a が T51 完了を待つ必要なし (mock fixture 駆動)
- → **却下**

### A4: T51 → T52 並列 + T53a → T53b (**却下**)

- T51 完了後に T52 と T53a を並列するパターン
- T53a は T51 と並列可能なため、Step 1 で重ねた方が並列利得大 (A1 が優越)
- → **却下**

### B / C (元の MAGI 合議候補): **却下**

- MAGI 合議 (詳細: `docs/artifacts/2026-06-27-magi-wave7-stage3-html-structure.md`) で案 A 採用確定済

---

## §4 採用案 (A1) の詳細

### Step 1: T51 + T53a 並列委譲 (並列子 2 / L1.5 司令塔不要)

**司令塔不要の根拠**: CLAUDE.md 「委譲の閾値ルール」 — 並列子 2 名以下は L1 → L2 直 (司令塔起動コストが節約分を食う)

#### L2#1: T51 (tdd-developer / Sonnet)

- 対象: `.claude/scripts/dashboard/builder.py` の `_render_v2_milestones()` (L546-590)
- 仕様: design.md §8「HTML 構造設計」サンプル HTML 通り
- 必須実装:
  - `sorted(self.data.milestones, key=lambda m: m.name)` で **Milestone 名昇順ソート** (文字列辞書順)
  - 既存 table 構造を **完全削除** し `.milestones-container` div ラッパ + `.milestone-card` article × Milestone 件数に置換
  - `data-milestone="{name}"` 属性を `<article>` に付与
  - `<h3>{name}</h3>` + `<p>Step: <span class="step">{current_phase}</span></p>` + `<p>状態: <span class="status">{status}</span></p>`
  - 状態 (status) はバッジ表示しない (design.md §8 サンプル準拠 / `<span class="status">` のみ)
- スコープ外:
  - CSS 追加 (T52 で別途)
  - 既存 test_v2_view.py 修正 (T53b で別途)
  - status バッジ表示 (現状実装と design.md §8 で乖離があるが、本 Step では仕様 = §8 に従う / L2 は判断不要)
- 委譲 prompt 冒頭: `knowledge/l2-delegation-guardrails.md` 4 点挿入 (本書 §7)

#### L2#2: T53a (tdd-developer / Sonnet)

- 対象: `.claude/tests/dashboard/test_wave7_stage3_milestones.py` (**新規作成**)
- 仕様: tasks.md §6 T53 のフィクスチャ実装例 + 期待値テーブル
- 必須実装パターン: pytest fixture で `DashboardData` モック構築 (実 SESSION_STATE.md に依存しない)
- 必須テストケース (~10 件想定):
  1. 昇順ソート確認 (入力 [B-5, B-4] → 出力で B-4 が B-5 より先)
  2. `data-milestone` 属性付与確認
  3. `.milestone-card` 件数 = Milestone 件数
  4. `.milestones-container` div ラッパ存在確認
  5. Step 列が全 Milestone 共通 (current_phase) 確認
  6. `<h3>` 内に Milestone 名表示確認
  7. 単一 Milestone 入力時の挙動 (1 件のみ)
  8. 空 milestones 入力時の挙動 (empty state 維持)
  9. (任意) 中間文字含む Milestone 名のソート挙動
  10. (任意) status 文字列の表示確認
- スコープ外:
  - 既存 test_v2_view.py 修正 (T53b で別途)
  - CSS 関連テスト (T52 完了後に追加判断)
- 委譲 prompt 冒頭: ガードレール 4 点挿入 (本書 §7)
- TDD Red 期待: **Step 1 完了時点 (T51 + T53a 両方完了) で全件 PASS** が期待値。T51 未完了の中間段階では FAIL するのが TDD 正常動作

### Step 2: L1 リレー (破損件数把握 + T53b 承認準備)

- pytest 全件実行: `cd D:/work7/LivingArchitectModel && python -m pytest .claude/tests/dashboard/ -q`
- 期待: T53a 新規テスト ~10 件 PASS
- 予測: 既存 test_v2_view.py が複数件 FAIL (V-2 HTML 構造変更による)
- L1 タスク:
  1. FAIL 件数 + 失敗内容を確認 (grep + assertion 内容把握)
  2. **§8 ロールバック判断基準と照合** (破損件数 ≥ 20 件 → ユーザー相談 / v0.2.0 で閾値見直し済)
  3. **「修正方針」を構造化** (v0.3.0 / Warning-4 解消) — 最低構成要素:
     - **(i) 破損テスト名リスト**: pytest 出力から FAIL テスト名を全件列挙
     - **(ii) 改修パターンマッピング**: table → section/article 置換の典型パターンを 3-5 件サンプル化
       - 例: `'<table>'` → `'<section id="v2-milestones">'` の expected 文字列置換
       - 例: `'<tr data-milestone='` → `'<article class="milestone-card" data-milestone='`
       - 例: `'<td>{name}</td>'` → `'<h3>{name}</h3>'`
     - **(iii) 期待値テキストの新旧対応表**: 主要 3-5 テストの before/after 期待値文字列
  4. 既存テスト緩和 (破棄ではなく期待値更新) であることを承認
  5. L2 への次工程委譲材料準備 (構造化方針を T53b prompt に組み込む)

### Step 3: T52 CSS 追加 (L2 直列 / tdd-developer)

- 対象: `.claude/scripts/dashboard/builder.py` の `_render_style()` メソッド (L62 / 注: design.md §8 + tasks.md §6 T52 の `_render_css` 表記は実体に対する **用語乖離**)
- 仕様: design.md §8「CSS 設計」3 ルール (`.milestones-container` + `.milestone-card` + `.milestone-card h3` / 推定 ~300 bytes)
- **CSS 実測手順 (v0.2.0 で確定 / #W-1 解消)**:
  ```python
  # スクリプト経由 (Git Bash 複数行 python -c 不可)
  from dashboard.builder import DashboardBuilder
  from dashboard.models import DashboardData
  b = DashboardBuilder(data=DashboardData())
  css = b._render_style()  # 注: 仕様は _render_css と表記するが実体は _render_style
  size = len(css.encode("utf-8"))  # utf-8 バイト計測
  ```
  Wave 6 終端 9,922 bytes はこの手法で得られた値 (L1 実機検証済 / 2026-06-27)
- 必須報告:
  - CSS 追加前のサイズ実測 (bytes / utf-8)
  - CSS 追加後のサイズ実測 (bytes / utf-8)
  - 差分 + 上限 10,240 bytes との残量
- 超過時の L1 判断フロー (v0.3.0 / Warning-2 解消):
  1. L2 (T52 担当) が実測超過を L1 に報告した時点で **L2 委譲を一旦保留** (再委譲対象として保持)
  2. L1 が design.md §8 縮退オプション 4 件から選定:
     - **SE 級 (Opt 1, 2)**: L1 直実施可 (フォーマット最適化等 / ~30-50 bytes)
     - **PM 級 (Opt 3, 4)**: ユーザー相談必須 (意匠縮小 / ~80-100 bytes)
  3. **SE 級選定時**: L1 が直接 CSS 修正 → 再実測 → 上限内なら L2 委譲を解除して Step 4 へ
  4. **PM 級選定時**: ユーザー相談 → 承認後に L1 が直接 CSS 修正 → 再実測 → Step 4 へ
  5. 縮退後も超過: §8 ロールバック判断基準に従う

### Step 4: T53b 既存 V-2 テスト期待値更新 (L2 直列 / tdd-developer)

- 対象: `.claude/tests/dashboard/test_v2_view.py` (Step 2 で破損確認したファイル / 現行 24 件)
- 仕様: Step 2 で L1 が用意した修正方針に従う
- 必須遵守:
  - 既存テスト**ロジック**は変更しない (期待値文字列のみ更新)
  - 削除は厳禁 (PM 級 / テスト削除は権限等級制約)
  - L1 承認済方針からの逸脱は事前承認
  - table assert を section/article assert に置換 (例: `<table>` → `<section>` / `<tr>` → `<article>` 等)
- 委譲 prompt 冒頭: ガードレール 4 点挿入

### Step 5: L1 直接実施 (最終検証 + Lighthouse + ship)

5-1. pytest 全件 PASS 最終確認: `cd D:/work7/LivingArchitectModel && python -m pytest .claude/tests/dashboard/ -q`

5-2. dashboard 再生成: `cd D:/work7/LivingArchitectModel && python .claude/scripts/build_dashboard.py`

5-3. **Lighthouse 実測 + aria-* 属性検証 + 構造化見出し階層確認** (MAGI 合議結論第 1〜4 項 / v0.3.0 Critical-1 解消):
  - chrome-devtools-mcp で dashboard.html を file:// ロード
  - `wait_for` で aria-* 動的属性の安定化を待機 (R-8 対応)
  - **(a) Lighthouse 実測** (snapshot モード):
    - Accessibility スコア確認 (**目標 ≥ 95 / Wave 6 終端 97 から退行ゼロ**)
    - 退行発生時: §5 R-7 対応 (Stage 5+ で巻き戻し検討を future-candidates に記録)
  - **(b) aria-* 属性検証** (MAGI 第 4 項 / v0.3.0 で実行手順化):
    - `take_snapshot` で DOM スナップショット取得
    - 各 `<article class="milestone-card">` が以下を持つことを確認:
      - `data-milestone="{name}"` 属性 (アクセシビリティ識別子としての役割)
      - 内部 `<h3>` 見出しが Milestone 名を表示 (スクリーンリーダーで「カードのラベル」として announce)
    - `<section id="v2-milestones">` の `<h2>` が「Milestone 一覧」となっていること
  - **(c) 構造化見出し階層確認** (MAGI 第 4 項):
    - DOM 階層が `h1 (ページタイトル) → h2 (v2-milestones / Milestone 一覧) → h3 (各 milestone-card の Milestone 名)` の 3 階層になっていること
    - h4 以下が含まれていないこと (Milestone カードに余分な見出しが入っていない)
    - 表記方法: `grep -E '<h[1-6]'` で dashboard.html から見出しタグを抽出し、階層順を目視確認
  - **(d) 退行 / 不整合検出時の判断**:
    - aria-* 属性欠落: Critical → L2 (T51) 再委譲して修正
    - 見出し階層乱れ: Warning → L1 が修正方針を決定
    - Lighthouse a11y < 95: Critical → §5 R-7 対応 + ロールバック検討 (§8)
    - Lighthouse a11y < 90: ロールバック実施 (§8)

5-4. T-S3-4 視覚確認:
  - 現状 SESSION_STATE.md に B-5 のみが含まれる想定 → 1 件のみ表示 → **Conditional Pass** (design.md §10.5 / tasks.md §3 Stage 3 検証 / v0.2.3 確定基準)
  - **Conditional Pass 宣言の方法 (v0.2.0 で導入 / v0.3.0 Warning-3 解消で証跡 (a) 明確化)**:
    - 宣言者: L1
    - 記録先: 本 execution-plan.md §9「実行ログ」セクション (Step 5 完了時に追記)
    - 証跡:
      - **(a) HTML 構造一致テスト PASS**: **Step 5-1 で実行する pytest 全件 PASS の中で T53a 新規テストが PASS していることを引用** (Step 5-4 で再実行はしない)。§9 記録欄には「Step 5-1 pytest 結果から T53a ___ 件 PASS」と記録
      - **(b) `data-milestone="B-5"` 属性付与確認**: dashboard.html を grep (`grep 'data-milestone="B-5"' docs/artifacts/dashboard/dashboard.html` の出力 ≥ 1 行)
      - **(c) `.milestone-card` + `.milestones-container` 存在確認**: dashboard.html を grep (`grep -E 'milestone-card|milestones-container' docs/artifacts/dashboard/dashboard.html` の出力 ≥ 2 行)
    - 3 点すべて満たせば Conditional Pass 宣言
  - chrome-devtools-mcp による視覚確認は Stage 4 T-S4-7 で実施 (本 Step で必須ではない / Step 5-3 の Lighthouse 計測時に自動でブラウザ起動するため副次確認は可能)

5-5. **T-S3-5 L3 (Haiku) 採点委譲** (tasks.md v0.2.3 §3 ゲート条件 / v0.3.0 Critical-2 解消):
  - 委譲先: `goal-driven-grader` サブエージェント (model=haiku) — MEMORY.md 「Haiku 委譲経路」記録準拠
  - rubric: **Critical 0 + Warning 0 = Green State** (`.claude/rules/code-quality-guideline.md` 準拠)
  - 採点対象: Step 1-4 の改修ファイル (builder.py / test_wave7_stage3_milestones.py / test_v2_view.py)
  - prompt 必須項目:
    - 対象ファイルパス
    - rubric: 「Stage 3 改修コードの Critical/Warning/Info を分類し Green State 判定」
    - 出力形式: 構造化報告 JSON (件数 + 各指摘の重要度 + 該当行)
  - 採点結果が Green State でない場合:
    - Critical 検出 → L2 再委譲で修正 → 再採点
    - Warning のみ検出 → L1 判断 (合理的理由があれば許容 + future-candidates に記録)

5-6. §3.5 チェックボックス更新 (T51/T52/T53 を [ ] → [x])
  - tasks.md §3.5 の同期ルール v0.2.3 では「L2 (自己更新) or L1 (委譲ガード)」と規定
  - 本書では L1 直で更新 (Step 5 が L1 単独実施のため)

5-7. /ship + push (3 commit 想定):
  - feat(B-5): T51 + T52 実装 (builder.py)
  - test(B-5): T53a 新規 + T53b 既存更新 (test_wave7_stage3_milestones.py + test_v2_view.py)
  - docs(B-5): tasks.md §3.5 完了マーク更新

---

## §5 リスクと対応

**表記注記 (v0.3.0 / Info-2 解消)**: 「発生確率」欄は **リスク事象の発生頻度 (実際にそのリスクが顕在化する確率)** を意味する。リスクの重大度 (顕在化時の影響度) は別軸であり、対応策の優先度はリスクスコア = 発生確率 × 重大度で総合判断する。

| ID | リスク | 発生確率 | 対応策 | 検出タイミング |
|:---|:------|:--------|:------|:-------------|
| R-1 | CSS 予算 10,240 bytes 超過 | **中** (残 18 bytes だが縮退 Opt 1 で ~30 bytes 節約見込み / v0.3.0 で「高」→「中」に補正) | Step 3 実測時に L1 が design.md §8 縮退オプションから選定 → 再実測 (フロー詳細は §4 Step 3) | Step 3 |
| R-2 | 既存 test_v2_view.py 破損件数が想定外に多い | 中 | Step 2 で破損件数確認 → §8 閾値 (20 件 / v0.2.0 で 30 → 20 に見直し) 以上で L1 がユーザー相談 | Step 2 |
| R-3 | T53a の mock fixture と T51 の HTML 構造に齟齬 | 中 | Step 1 委譲 prompt で design.md §8「HTML 構造設計」と「CSS 設計」を **同一テキスト** で両 L2 に渡す | Step 1 |
| R-4 | T-S3-4 視覚確認で Milestone 1 件のみ表示 | **高** (現状 SESSION_STATE.md が B-5 単独) | design.md §10.5 / tasks.md §3 で確定済の **Conditional Pass 基準** を適用 (本書 §4 Step 5-4 に手順明記)。Stage 4 T-S4-7 で再確認 | Step 5 |
| R-5 | Step 1 並列子間で進捗差が大 (T53a 早期完了 / T51 長期化) | 低 | Step 1 完了 = T51 + T53a 両方完了の同期点を意味する (v0.2.0 で明記)。T53a 完了 L2 は次工程の準備 (T52 prompt 準備等) を L1 と連携できる | Step 1 |
| R-6 | Wave 6 以前の先取り実装が Stage 3 にも存在 | **発生確認済** (v0.2.0) | §1.5 で実機確認結果を記録 → MAGI 合議で案 A 採用確定 | 完了 |
| **R-7** | **a11y 退行リスク (table → section/article 変換 / MAGI 合議追加)** | **中** | Step 5 で Lighthouse 実測 (a11y ≥ 95 / 目標 97 維持) / 退行時は Stage 5+ で巻き戻し検討を future-candidates に記録 | Step 5 |
| **R-8** | **chrome-devtools-mcp `new_page` 直後の不安定動作 (Wave 6 観測 / spec-critic 指摘)** | 中 | Step 5-3 Lighthouse 実行時に `wait_for` 等で aria-sort 等の動的属性安定化を待機 | Step 5 |

---

## §6 成功基準 (Success Criteria)

本 execution-plan の成功は以下を全て満たすこと:

- [ ] Step 1〜5 が想定順序通りに完了
- [ ] pytest 全件 PASS (最終確認)
- [ ] CSS サイズ ≤ **16,384 bytes (16 KiB / v0.4.0 改訂)** (utf-8 / `_render_style()` 戻り値で実測) — 緑帯 < 11,469 bytes が望ましい
- [ ] **Lighthouse Accessibility ≥ 95** (Wave 6 終端 97 / v0.2.0 で MAGI 合議追加)
- [ ] **aria-* 属性 + 構造化見出し階層確認 PASS** (v0.3.0 / Critical-1 解消 / §4 Step 5-3 (b)(c)(d) 全項 PASS)
- [ ] **T-S3-5 L3 (Haiku) 採点 Green State** (Critical 0 + Warning 0 / v0.3.0 / Critical-2 解消 / §4 Step 5-5 委譲完了)
- [ ] T-S3-4 が Conditional Pass 以上で通過 (本書 §4 Step 5-4 の宣言手順に従う)
- [ ] §3.5 チェックボックス更新済
- [ ] ship + push 完了
- [ ] 想定総時間 ~110 分の ±50% 以内 (=55〜165 分 / 過大超過なら次回 retro 課題 / v0.3.0 で L3 採点 +15 分追加)
  - **計測基準 (v0.2.0 で明確化)**: Step 1 L2 委譲開始 (Agent 起動) から Step 5-7 push 完了 (git push exit) までの実時間。L1 の思考時間・承認待ち時間・コンテキスト管理時間は含む

---

## §7 委譲 prompt 共通テンプレート (v0.2.0 / #W-3 修正反映)

L2 (tdd-developer / Sonnet) 委譲時、prompt 冒頭に必ず以下を挿入する:

```markdown
## 委譲ガードレール (事前合意)

実装着手前に以下 4 点を必ず確認してください:

1. **Bash 制限前提**: 権限のない Bash コマンドは試行せず、L1 に依頼する
   (Git Bash 経由のため複数行 python -c は失敗する / 必要ならスクリプトファイル経由)
2. **緩和事前承認必須**: 既存テスト・規約からの緩和は実施前に L1 へ承認依頼
3. **行数計測法明示 (全言語共通 / v0.2.0 で表記修正)**: 実装行 / コメント行 / 空行 / 合計 の 4 区分で計測して報告。
   Python / CSS / JS など対象言語にかかわらず適用
4. **既存テスト影響事前分析**: 改修対象の波及範囲を事前に列挙し、破損予測を共有

完了報告時は上記 4 点の遵守状況を明示してください。
```

根拠: `docs/artifacts/knowledge/l2-delegation-guardrails.md` (Wave 6 Stage 3 で実証 / 報告乖離 50% → 5%)

**SSOT 注記 (v0.3.0 / Warning-1 解消)**: Wave 7 tasks.md v0.2.3 §7 のガードレール表記には「JS 行数計測法明示」と書かれている (v0.2.0 で未修正)。本 Stage 3 では **本書 §7 の「全言語共通」表記を運用 SSOT** とする。tasks.md §7 の表記揺れ修正は別タスク (将来候補) として future-candidates に記録 (Wave 7 内 PM 級補追を本書のために発生させない)。

---

## §8 ロールバック判断基準 (v0.2.0 で 30 → 20 件に見直し / #I-2 反映)

以下のいずれかが発生した場合、Step 5 完了前にユーザーにロールバック相談:

- CSS が **16,384 bytes (16 KiB / v0.4.0 改訂)** 超過 + さらに縮退オプション全適用後も超過
- **既存テスト破損件数 ≥ 20 件 (V-2 関連のみ / v0.2.0 で見直し)**
  - 根拠: 現行 test_v2_view.py = 24 件 (L1 実機計測 / 2026-06-27)
  - 20 件 ≈ 83% の破損 = 「table assert がほぼ全件影響」の状態
  - これ以上は破壊規模が PLANNING 想定を大幅に超えるため、ユーザー判断を仰ぐ
- T51 で render_v2 改修が design.md §8 サンプル HTML と乖離 (仕様ドリフト発生)
- 並列子間 (T51 / T53a) で 30 分以上の進捗差が連続発生 (L2 サブエージェント不調の兆候)
- **Lighthouse Accessibility < 90** (退行が大きすぎる場合 / R-7 派生)

ロールバック方法: `git reset --soft HEAD~N` (N = 該当 commit 数 / PM 級 / **ユーザー承認必須**)

---

## §9 実行ログ (Step 5 完了時に追記 / Conditional Pass 宣言証跡)

[Step 5 完了時に L1 が追記]

例:
- 実行日時: YYYY-MM-DD HH:MM:SS JST
- pytest 結果 (Step 5-1): ___ PASS / ___ SKIP / ___ FAIL
- CSS 実測 (追加前 → 追加後): ____ bytes → ____ bytes / 上限 16,384 まで残 ____ bytes (レベル帯: 緑/黄/赤)
- 縮退オプション適用有無: なし / Opt ___ 適用 (~___ bytes 節約)
- Lighthouse Accessibility: ____ (目標 ≥ 95)
- aria-* + 見出し階層確認 (Step 5-3 b/c/d):
  - aria-* 属性検証: PASS / FAIL (失敗詳細: ___)
  - 見出し階層 (h1→h2→h3): PASS / FAIL (詳細: ___)
- T-S3-4 Conditional Pass 宣言:
  - 証跡 (a) Step 5-1 pytest から T53a PASS 件数: ____
  - 証跡 (b) `data-milestone="B-5"` 付与確認: ____ 行
  - 証跡 (c) `.milestone-card` + `.milestones-container` 存在 grep 結果: ____ 行
- T-S3-5 L3 (Haiku) 採点結果 (Step 5-5 / v0.3.0 で追加):
  - Critical: ____ 件
  - Warning: ____ 件
  - Info: ____ 件
  - Green State 判定: PASS / FAIL
- 総時間 (Step 1 開始 → Step 5-7 push 完了): ____ 分

---

## §10 改訂履歴

| バージョン | 日付 | 変更内容 |
|:----------|:-----|:--------|
| 0.1.0 | 2026-06-27 | 初版起稿 — Wave 7 Stage 2 完了時点の状況を踏まえた Stage 3 並列化計画 |
| 0.2.0 | 2026-06-27 | spec-critic 独立レビュー結果 (Critical 2 / Warning 5 / Info 3) + L1 実機確認による新規発見 (#C-3 V-2 先取り実装 + table 構造乖離) + MAGI 合議結論 (案 A 採用) を反映 |
| **0.3.0** | 2026-06-27 | spec-critic 2 回目レビュー結果 (Critical 2 / Warning 4 / Info 3) 全件反映。主な変更: §4 Step 5-3 に aria-* 属性検証 + 構造化見出し階層確認手順追加 (Critical-1 解消 / MAGI 第 4 項の実行化) / §4 Step 5-5 に T-S3-5 L3 Haiku 採点委譲を追加 + §6 成功基準に追加 (Critical-2 解消) / §4 Step 3 に縮退適用フロー詳細追加 (Warning-2 解消) / §4 Step 5-4 証跡 (a) を「Step 5-1 引用」と明示 (Warning-3 解消) / §4 Step 2 タスク 3「修正方針」の最低構成要素 3 点明示 (Warning-4 解消) / §7 末尾に tasks.md §7 との SSOT 注記追加 (Warning-1 解消 / 別タスク化) / §5 R-1 確率を「高」→「中」に補正 + 表記注記追加 (Info-2 解消) / §9 実行ログテンプレに aria-* + L3 採点結果記録欄追加 (Info-1 解消) / §6 想定総時間 ~95→~110 分 (L3 採点 +15 分) |
| **0.4.0** | 2026-06-28 | NFR-W7-1 CSS 予算根本見直し連動補追 — Stage 3 着手後の予算逼迫を契機に AoT 5 Atom MAGI 合議で NFR-W7-1 を MUST → SHOULD 降格 + 上限 10,240 → 16,384 bytes 緩和 + 3 段階レベル制（緑/黄/赤）導入を確定。本書への補追: §6 成功基準 CSS 上限を 16,384 bytes + 緑帯目標表記 / §8 ロールバック CSS 条件に 16,384 bytes 超過を明示 / §9 実行ログテンプレに上限 16,384 + レベル帯欄追加 / ステータスを Approved に更新。連動: requirements.md / design.md / tasks.md v0.2.4 + knowledge/nfr-lifecycle-management.md / 議事録: `2026-06-28-magi-nfr-w7-1-budget-revision.md` |

---

## §A 指摘・発見マッピング (v0.3.0 反映状況 / Info-3 で見出し変更)

### 1 回目 spec-critic レビュー (v0.1.0 → v0.2.0 反映)

| 指摘 ID | 内容 | 反映先 | 反映方法 |
|:---|:---|:---|:---|
| **#C-1** | T53a 独立性の DashboardData/MilestoneInfo 互換性前提 | §1.5 | L1 実機確認結果で「完全一致」確証 → 前提解消 |
| **#C-2** | Conditional Pass 宣言の方法・証跡未定義 | §4 Step 5-4 / §6 / §9 | 宣言者 (L1) / 記録先 (§9) / 証跡 (3 点) を明示 |
| #W-1 | CSS 実測方法が曖昧 | §4 Step 3 | スクリプト経由実測手順 + `_render_style()` 用語乖離注記 |
| #W-2 | Step 2 承認基準と §8 閾値の連動欠落 | §4 Step 2 タスク 2 | §8 ロールバック判断基準と照合を明示 |
| #W-3 | ガードレール「JS 行数」表記の誤誘導 | §7 | 「全言語共通」明記 |
| #W-4 | build_dashboard.py 実行パスが cwd 依存 | §4 Step 2 / Step 5-1 / Step 5-2 | `cd D:/work7/LivingArchitectModel && ...` 形式で記述 |
| #W-5 | T53a "PASS 想定" が TDD Red 先行と矛盾 | §4 Step 1 L2#2 / §5 R-5 | 「Step 1 完了 = T51 + T53a 両方完了の同期点」明記 |
| #I-1 | L1.5 司令塔不要の根拠不在 | §4 Step 1 冒頭 | CLAUDE.md「委譲の閾値ルール」参照を明記 |
| #I-2 | 30 件閾値の根拠未提示 | §8 | test_v2_view.py 現行 24 件 → 20 件閾値に見直し + 根拠明示 |
| #I-3 | 時間計測方法未定義 | §6 最終項 | 計測基準 (L2 委譲開始 → push 完了) を明示 |

### L1 自己発見 (1 回目 spec-critic レビュー後の実機確認で発覚 / 命名規則注記: spec-critic 由来と区別するため接尾辞 `(L1)`)

| 発見 ID | 内容 | 反映先 | 反映方法 |
|:---|:---|:---|:---|
| **#C-3 (L1)** | V-2 複数 Milestone 表示の先取り実装 + 構造的乖離 | §1.5 / MAGI 議事録 / §3 | 実機確認結果記録 + MAGI 合議で案 A 採用確定 |

### MAGI 合議追加事項 (v0.2.0 反映)

- Step 5 Lighthouse 実測必須化 (§4 Step 5-3 / §6 成功基準)
- R-7 (a11y 退行リスク) 追加 (§5)
- R-8 (chrome-devtools-mcp 不安定動作 / spec-critic 観点 3 漏れ補完) 追加 (§5)

### 2 回目 spec-critic レビュー (v0.2.0 → v0.3.0 反映)

| 指摘 ID | 内容 | 反映先 | 反映方法 |
|:---|:---|:---|:---|
| **Critical-1** | MAGI 第 4 項 (aria-* + 見出し階層確認) が Step 5-3 に未反映 | §4 Step 5-3 (b)(c)(d) / §6 / §9 | 具体的な確認手順 (snapshot / grep / 退行判断基準) を追加 + 成功基準に組込み |
| **Critical-2** | T-S3-5 L3 採点 (Green State) が成功基準から欠落 | §4 Step 5-5 / §6 / §9 | L3 委譲フロー (goal-driven-grader / haiku) 追加 + 成功基準 + 実行ログ記録欄追加 |
| Warning-1 | tasks.md §7 ガードレール表記との SSOT 分裂 | §7 末尾 | 「本書 §7 を Stage 3 運用 SSOT とする」明記 + tasks.md §7 修正は別タスク化 |
| Warning-2 | 縮退オプション PM 級採用時の L2/L1 切替フロー不明 | §4 Step 3 | 5 ステップフロー (SE 級 / PM 級分岐 + L2 保留→ L1 直 → L2 解除) を追加 |
| Warning-3 | Conditional Pass 証跡 (a) の引用 / 再実行が曖昧 | §4 Step 5-4 | 「Step 5-1 pytest 結果から T53a PASS 件数を引用」と明示 |
| Warning-4 | Step 2「修正方針」の最低構成要素未定義 | §4 Step 2 タスク 3 | (i) 破損テスト名 / (ii) 改修パターン / (iii) 新旧期待値対応表 の 3 点明示 |
| Info-1 | §9 に T-S3-5 採点結果記録欄なし | §9 | Critical-2 と同時に解消 |
| Info-2 | §5 R-1「発生確率: 高」表現の曖昧さ | §5 リスク表冒頭 + R-1 | 表記注記追加 + R-1 を「中」に補正 (縮退 Opt 1 で解決可能性大) |
| Info-3 | §A 見出しの「指摘」と「発見」の混在 | §A 本節 | 見出しを「指摘・発見マッピング」に変更 + spec-critic / L1 / MAGI を分節化 |

---

## §11 参照

- `docs/specs/b4-dashboard/wave7/design.md` v0.2.3 §8
- `docs/specs/b4-dashboard/wave7/tasks.md` v0.2.3 §3 Stage 3 / §6 T51-T53
- `docs/specs/b4-dashboard/wave7/requirements.md` v0.2.3 FR-W7-4 / NFR-W7-1
- `docs/artifacts/knowledge/l2-delegation-guardrails.md`
- `docs/artifacts/2026-06-27-magi-wave7-stage3-html-structure.md` (本書方針確定 MAGI 議事録)
- `SESSION_STATE.md` (Wave 7 Stage 2 完了状態)
- `.claude/rules/decision-making.md` (MAGI System SSOT)
- CLAUDE.md「委譲の閾値ルール」 (L1.5 司令塔不要の根拠 / §4 Step 1)
- MEMORY.md「Haiku 委譲経路」 (subagent_type=goal-driven-grader + model=haiku / §4 Step 5-5)
