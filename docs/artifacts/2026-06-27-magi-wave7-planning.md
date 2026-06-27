# MAGI 議事録: B-5 Wave 7 PLANNING

**日時**: 2026-06-27
**起動者**: L1（Opus 4.7）
**フェーズ**: PLANNING（design-mode 起動済）
**議題**: B-5 Wave 7 のスコープ・進行順序・分割粒度の決定
**背景**: Wave 6 PoC レビューで挙がった 4 chip のうち 3 件を「PoC 指摘パッケージ」として統合した
スコープ (C) で着手する方針が確定。本合議は (C) を 4 Stage の実装計画に落とすための意思決定。

---

## 適用条件確認

| 条件 | 該当 |
|:-----|:-----|
| 判断ポイント 2+ | ✅（a/b/c/d の 4 ポイント） |
| 影響レイヤー 3+ | ✅（TasksParser / データモデル / V-2/V-3/V-4 ビュー / builder.py / tasks.md フォーマット = 5 レイヤー） |
| 有効な選択肢 3+ | ✅（並列対応方式だけでも 4 option） |

→ MAGI 合議の適用条件を満たす。

---

## Step 0: AoT Decomposition

| Atom | 判断内容 | 依存 |
|:-----|:--------|:-----|
| A1 | 着手順序（#1 規約 / #2 parser 修正 / #3 並列対応 をどう並べるか） | なし |
| A2 | Stage 分割数と境界 | A1 |
| A3 | 並列対応の方式（V-2/V-3 を物理的にどう表現するか） | なし |
| A4 | design.md §5 の wave7/ への切り出し範囲 | なし |

---

## Atom A1: 着手順序

### 選択肢

- option 1: #2 → #1 → #3（parser 基盤 → 規約 → ビュー拡張）
- option 2: #1 → #2 → #3（規約から / 既存 §5 を起点）
- option 3: #3 → #1 → #2（影響大きい方から）
- option 4: 並列着手

### Step 1: Divergence

**[MELCHIOR]**:
- option 1 推奨。#2 は既存 parser のバグ修正で他の改修の基盤になる
- 誤抽出を直してから Assignee タグ抽出を追加する方が無駄な書き直しが減る
- 並列は不要（依存関係明確 / シーケンシャルで十分）

**[BALTHASAR]**:
- option 1 で #2 を先に置くこと自体には賛成
- 懸念: #2 単独完了時点では V-4 Assignee 列は `-` のまま（中途半端）
- 逆に option 2（#1 → #2）だと誤抽出行に意味ないタグが付与され混乱する
- option 3（#3 先行）にすると V-2/V-3 のテスト負荷が Stage 末に集中する
- リリース戦略として「Stage 1 完了でも価値が出るか」の評価は別途必要

### Step 2: Debate

- 中途半端さの懸念は Stage 完了ごとの ship + push（Wave 6 戦略踏襲）で許容可能
- 各 Stage 単位で価値ある PR 群を生むことで「中途半端」を回避できる

### Step 3: Convergence

**[CASPAR] 結論**: **#2 → #1 → #3**

**理由**:
1. parser 基盤の修正は #1/#3 の正確性に直結する依存関係
2. #2 単体でも V-4 task 行の正しさは改善する（Assignee 表示が `-` でも task 行は正しい）
3. #1 と #3 の逆順は Assignee 規約と V-2/V-3 ビューの一貫性が崩れる

---

## Atom A2: Stage 分割数と境界

### 選択肢

- option 1: 3 Stage（#2 / #1 / #3 を各 Stage）
- option 2: 4 Stage（#2 / #1 / #3 のビュー / #3 のデータモデル）
- option 3: 5 Stage（#2 / #1-parser / #1-表示 / #3-モデル / #3-ビュー）
- option 4: 2 Stage（#2 + #1 を 1 stage / #3 を 1 stage）

### Step 1: Divergence

**[MELCHIOR]**:
- Wave 6 は 4 Stage で成功した → 同じ流儀でリズム維持
- option 2（4 Stage）が Wave 6 のサイクル感に最も近い
- 1 Stage あたり 2-3 タスク + 統合テスト + 採点で 1 セッション分のサイズ

**[BALTHASAR]**:
- option 3（5 Stage）は細かすぎる → ship × 5 / 採点 × 5 のオーバーヘッド増
- option 4（2 Stage）は粗すぎる → stage 内で複数レイヤーに触れるとガードレールが効きにくい
- #2 単体は規模が小さい（regex 1 つ + テスト数件）が parser テスト品質を独立に担保することで #1/#3 の安心感が増す
- option 1（3 Stage / #2 #1 #3 を独立）も妥当

### Step 2: Debate

- option 1 と option 2 の差分: 統合 Stage の有無
- Wave 6 の Stage 4 は「統合テスト + Lighthouse + PoC」を担っていた → Wave 7 でも同等の段階が必要かは Reflection で再評価

### Step 3: Convergence（一旦）

**[CASPAR] 結論（一旦）**: **3 Stage（#2 / #1 / #3）**

→ Reflection で再評価へ

---

## Atom A3: 並列対応の方式

### 選択肢

- option 1: 横並び表示（複数 Milestone を 1 画面に並べる / 比較容易）
- option 2: フィルタトグル（チェックボックスで複数 Milestone を選択可 / 切替式）
- option 3: タブ切替（Milestone ごとにタブ / 比較は手動）
- option 4: 全 Milestone 一覧化（既存 V-2 を「全 Milestone を縦に列挙」する形に拡張）

### Step 1: Divergence

**[MELCHIOR]**:
- option 1（横並び）が視認性最高 → 比較目的に直結
- option 4（全 Milestone 一覧化）は CSS のみで実現可能 → Wave 6 Stage 1〜2 の知見で実装軽い

**[BALTHASAR]**:
- option 1（横並び）は responsive 設計が大変 → Wave 6 で達成した Lighthouse 97 維持が不安
- option 3（タブ切替）は「並列」とは言いがたく chip task_52c46569 の意図に反する
- option 2（フィルタトグル）は既存ソート/フィルタ機構と相性良いが比較体験は弱い（切替必要）
- option 4（全 Milestone 一覧化）が最も軽い + LAM 現状（active = B-5 のみ / B-4 + B-5 で 2 件）と整合
- 将来 Milestone が 5+ になったら option 2 を追加実装可能

### Step 2: Debate

- option 4 の弱点: Milestone が将来増えた時に縦長になる
- 対策: option 2（フィルタ）を後方互換で追加可能な設計にしておく
- CSS 予算（残 318 bytes）の事前評価が必要 → NFR 化必須

### Step 3: Convergence

**[CASPAR] 結論**: **option 4（全 Milestone 一覧化）主軸 + フィルタは後方互換で追加可能設計**

**理由**:
1. 現 Milestone 数 2 件で option 4 で十分機能
2. CSS のみで実現 → builder.py 改修小 → Stage 3 単体で完結
3. responsive 負担が option 1 より圧倒的軽い
4. 将来 Milestone 5+ になったら option 2 フィルタ追加可能（後方互換性あり）
5. **CSS 予算（残 318 bytes）の事前評価を NFR に組込み**（retro Try A4 の早期回収）

---

## Atom A4: design.md §5 の wave7/ への切り出し範囲

### 選択肢

- option 1: 全切り出し（§5 を wave7/design.md に丸ごと移動 / 元 §5 はリンクのみ）
- option 2: 部分切り出し（§5 の概要は元のまま / 詳細は wave7/design.md に拡張）
- option 3: 切り出さない（wave7/design.md は §5 への参照 + 追加事項のみ）
- option 4: 元 design.md を v0.4.0 に bump して §5 を更新、wave7/design.md は別観点（#2/#3）のみ

### Step 1: Divergence

**[MELCHIOR]**:
- option 1（全切り出し）は wave7/ の自己完結性高い
- 元 design.md の肥大化（既に 400 行超）を防ぐ

**[BALTHASAR]**:
- option 1 だと元 §5 が空洞化 → SSOT 一意性が崩れる
- option 3（切り出さない）が SSOT 維持に最適
- 既存 §5 は「Wave 7+ 追加」と明記されており実質 wave7 起点になっている → 切り出し不要
- option 4 は元 design.md を v0.4.0 に bump する変更コミットが増える

### Step 2: Debate

- 重複記述を避けると保守コスト下がる
- Wave 6 の wave6/design.md もスコープ固有部分のみ書く方針だった（既存パターンに整合）

### Step 3: Convergence

**[CASPAR] 結論**: **option 3（切り出さない）**

**理由**:
1. 既存 §5 が「Wave 7+ 追加」と明記され SSOT として既に整備
2. wave7/design.md には #2/#3 設計 + §5 への参照 + 必要なら §5 の追補（実装詳細）のみ書く
3. 重複記述を避けると保守コスト下がる
4. Wave 6 wave6/design.md もスコープ固有部分のみ書く方針（既存パターン整合）

---

## Step 4: Reflection

各 Atom の結論を見直す:

| Atom | 結論 | 致命的見落とし |
|:-----|:-----|:--------------|
| A1 | #2 → #1 → #3 | なし |
| A2 | 3 Stage | **あり** → 修正 |
| A3 | option 4 主軸 / CSS 予算 NFR 組込み | なし |
| A4 | 切り出さない | なし |

**A2 致命的見落とし**:
Wave 7 全体の **統合テスト + Lighthouse + PoC レビュー** の段階が欠落。
Wave 6 と同じリズム（最終 Stage で AC 集約）が無いと:
- Lighthouse 退行検出ができない（CSS 予算ギリギリの中で追加するため退行リスクあり）
- PoC レビューをどこで行うか不明瞭になる
- AC-W7-* の総括判定が散在する

→ **A2 結論修正**: **4 Stage**（Stage 1〜3 + Stage 4 統合）

Reflection の Reflection は禁止 → ここで確定。

---

## Step 5: AoT Synthesis

### 統合結論

| 項目 | 決定 |
|:-----|:----|
| 着手順序 | **#2 → #1 → #3** |
| Stage 分割 | **4 Stage**（Wave 6 リズム踏襲） |
| 並列対応方式 | **option 4（全 Milestone 一覧化）** + フィルタは後方互換で追加可能設計 |
| design.md §5 切り出し | **しない**（wave7/design.md は追加事項のみ） |

### Wave 7 Stage 構成（確定）

| Stage | 内容 | 主担当層 |
|:------|:-----|:--------|
| Stage 1 | **TasksParser Task ID 誤抽出修正** — `W{n}-B{n}-T{n}` regex 強化 + parser テスト | Sonnet（L2） |
| Stage 2 | **Assignee タグ規約の実装** — TasksParser 拡張 + V-4 表示 + tasks.md フォーマット運用 | Sonnet（L2） |
| Stage 3 | **複数 Milestone 一覧化** — V-2 全 Milestone 表示 + データモデル / CSS 予算管理 | Sonnet（L2） |
| Stage 4 | **統合テスト + Lighthouse + PoC レビュー** — Wave 6 と同じパターン | L1 統括 + Haiku 採点 |

### Action Items

1. Wave 7 PLANNING を本 MAGI 合議の結論で進行
2. **requirements.md v0.1.0 起稿** — スコープ (C) + 4 Stage + 並列対応方式 option 4 + **CSS 予算管理 NFR**（残 318 bytes の事前評価必須化 / retro Try A4 早期回収）
3. **design.md v0.1.0 起稿** — #2/#3 設計（§5 は元 design.md 参照）+ Stage 内訳 + Atom A4 方針明記
4. **tasks.md v0.1.0 起稿** — 4 Stage の SPIDR 分割 + AC 起票
5. **L2 委譲ガードレール 4 点** を Stage 1 委譲時に prompt 冒頭挿入（[knowledge/l2-delegation-guardrails.md](knowledge/l2-delegation-guardrails.md) を活用）
6. 本議事録を後段 retro 参照用に保存（本ファイル）

---

## 参照

- 起源 chip:
  - `task_eec7ce2d`（Assignee 列 data 仕様 / Wave 7 #1 に統合）
  - `task_954a1e90`（TasksParser Task ID 誤抽出 / Wave 7 #2 に統合）
  - `task_52c46569`（複数 Milestone/Wave 並列対応 / Wave 7 #3 に統合）
- 関連 retro: [retro-W6-B5-2026-06-27.md](retro-W6-B5-2026-06-27.md)
- L2 委譲ガードレール: [knowledge/l2-delegation-guardrails.md](knowledge/l2-delegation-guardrails.md)
- 起点 design: `docs/specs/b4-dashboard/design.md` §5（commit 4448d4c）
- 関連 ADR: なし（必要なら本 Wave で起票検討）
