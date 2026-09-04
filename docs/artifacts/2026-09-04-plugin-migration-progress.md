# plugin 移行の進捗台帳（セッション 28 → 次セッション引き継ぎ）

**日付**: 2026-09-04（セッション 28）
**等級**: SE 級（`docs/artifacts/`）
**位置づけ**: 配布形態を plugin へ移す作業の**実行状態**を持つ。**決定の正本は別**（下記）。

| 種別 | 正本 |
|:--|:--|
| **決定** | `docs/artifacts/2026-09-04-magi-distribution-form.md`（MAGI AoT 6 Atom + gabriel 2 巡 + HGA #29） |
| **所在の決定** | `docs/adr/0010-global-claude-assets-governance.md` **追補 1** |
| **3 層分類** | `docs/artifacts/2026-09-04-distribution-layer-classification.md` |
| **実行状態** | **本ファイル** |

---

## §1 これだけは再導出しないこと（結論の要約）

1. **配布形態は plugin + marketplace**。ADR-0010（2026-07-04）が既に決めており、本セッションの MAGI + HGA も独立に同じ結論に到達した。**争点ではない**
2. **リポジトリは割らない**（D-1 死んだ案 #5 / ユーザー撤回 + HGA #22）。plugin は LAM リポジトリ内に置く（ADR-0010 追補 1 / ユーザー決定 2026-09-04）
3. **self-hosting は維持**（ユーザー裁定 2026-07-27 / 「放棄可」は**同日中に本人が撤回済**）
4. **名前空間は受容済**（ADR-0010 **I-4**「スキル参照は名前空間を常に明示する」）。`/lam-harness:ship` になる。**agents も `plugin:agent` に名前空間化される**（V6 実測）
5. **rules は plugin では配れない**（コンポーネント在庫は skills / agents / hooks / MCP / LSP の 5 種のみ）。`/lam-harness:init` がプロジェクトへ敷く
6. **managed 集合は「大きく始める」**（ユーザー決定 2026-09-04）。starter → managed の昇格は利用者の編集を壊すため事実上不可逆
7. **ランタイム不在時は init が完了を拒む**（ユーザー確認済 / 不可逆点 I4）

### 本セッション最大の発見

**D-1 は `fable-l3-protocol.md` を「S（要分割）を認める理由」の実例として名指ししながら、判定は X（丸ごと私物）を出していた。** 243 行中 25 行（10%）の私的記述のために、約 218 行の製品中核が配布境界の外へ出ていた。design §4 が「どちらも誤りである」と書いた 2 択のうち、誤りの側の結果になっていた。2026-08-29 に直した「`CLAUDE.md` の実況発火点から `PLANNING` 修飾が脱落」は、その最初の実害である。

---

## §2 実行状態

| 手順 | 内容 | 状態 |
|:-:|:--|:--|
| 0 | `init-harness` 欠陥 2 件の修正（`.json` → `.md` / 過大な名乗り） | **完了** |
| 0' | 条文の S 分割（§2 \| §3 / §3-§9 → `docs/internal/08_EXECUTION_DISCIPLINE.md`） | **完了** |
| 0'' | 要検証 V1-V8 | **完了**（結果は MAGI §13.6） |
| 1 | plugin 骨格 + T1/T2 検査（R3 機構 #11 / #12） | **完了** |
| 2 | Outbound Write Ban を project 層へ分離 | **完了**（D-1 決定 D4 の目標状態を達成） |
| **3** | **`/lam-harness:init` の実装 + ランタイム検査** | **次はここ** |
| 4 | `subagent_type` 参照の名前空間化（agents 12 × 参照元すべて） | 未 |
| 5 | hooks / agents / skills / scripts を plugin へ移動 + local install で self-hosting 切替 | 未 |
| 6 | clone-template の廃止判断 | 未 |

### 手順 3 の要件（次セッションの入口）

- `init-harness` を **`/lam-harness:init` へ置換**（skill 自体は廃止 / MAGI §13.5-D）
- 敷く対象は `templates/managed/`（rules 14 + docs-internal 10）+ starter（`CLAUDE.md` / `CHEATSHEET.md` / `CHANGELOG.md` / `SESSION_STATE.md` / `.claude/current-phase.md` / `.claude/harness.json` / `model-roster.md` / `terminology.md`）
- **ランタイム検査**: Python / bash が無ければ**完了を拒む**。根拠は V4 —— hook の `exit 2` 以外の非零終了は**非ブロッキング**で、トランスクリプトに `hook error` 通知 + stderr 1 行目が出る。**インタプリタ不在の 127 も同じバケツ**なので、放置すると fail-open とノイズが同時に起きる。init は「一度きり・利用者起動・対話的」を満たす唯一の地点であり、K6 が棄却した 7 案のいずれにも触れない
- **Layer 1（`settings.json` の `permissions.deny`）は届かないことを明示的に宣言する**（HGA §13.5-E）。「入れた瞬間に使える」の射程は Layer 0（規範）+ Layer 2（hook）まで

---

## §3 いま触ると壊れるもの（重要）

**hooks / agents / skills / scripts はまだ `.claude/` にある。移動は手順 5 まで待つこと。**

plugin コンポーネントは**インストールされて初めて有効になる**。いま `.claude/` から `plugins/` へ移すと、その瞬間に無効化される（LAM 自身のハーネスが死ぬ）。移動と local install は同じ波で行う。

**templates が二重に存在するのは意図的**。rules と docs/internal は plugin コンポーネントとして配れないため、リポジトリ内に 2 部できる。これは `lam-harness` 1.0.0 を殺したのと同じ構造だが、**恒等性を機構 #11 が強制する**点が違う。「重複しているから片方消そう」としないこと —— **消すと K4 の検査対象が消える**。

---

## §4 未コミット（`/ship` はユーザー実行）

推奨コミット分割（依存順）:

| # | type(scope) | 内容 |
|:-:|:--|:--|
| 1 | `fix(skills)` | `init-harness` 欠陥 2 件（`current-phase.json` → `.md` / 名乗りの縮小） |
| 2 | `docs(dist)` | **S 分割** —— `docs/internal/08_EXECUTION_DISCIPLINE.md` 新設 / `fable-l3-protocol.md` 273→95 行 / 参照 12 箇所付替 / 配布物 8 枚追随（日英 + スライド） |
| 3 | `feat(dist)` | plugin 骨格（`.claude-plugin/marketplace.json` / `plugins/lam-harness/` / managed templates 24 件） |
| 4 | `feat(clause-gate)` | **R3 機構 #11 / #12**（`verify_plugin_containment.py` + 15 tests）/ `/release` Phase 2.5 接続 / 台帳 §C |
| 5 | `refactor(hooks)` | **Outbound Write Ban の project 層分離**（`.claude/hooks-local/` 新設 / `pre-tool-use.py` -3,079 字 / `settings.json` に追加登録 / テスト retarget） |
| 6 | `docs(adr)` | **ADR-0010 追補 1**（所在変更 + R-1 再検証記録）※ **PM 級** |
| 7 | `docs(magi)` | MAGI アンカー / 3 層分類 / 本進捗台帳 / HGA 召喚ログ #29 |

**gitignore 対象**: `SESSION_STATE.md` / `docs/daily/` / `.claude/test-results.xml`
**意図的に未追跡**: `docs/private/2026-08-26-positioning-and-lecture-notes.md`（既存 / ユーザーの別案件資料）

---

## §5 検証状態（セッション終了時点）

```
pytest .claude/tests .claude/hooks/tests   → 1301 passed / 14 skipped
verify_distributable_claims.py (機構 #10)  → OK
verify_plugin_containment.py  (機構 #11/#12) → OK
追跡ソースへの作者絶対パス混入            → 0
```

**fresh clone の 3 件の赤は未解消**（`test_parse_with_real_git_log` = 履歴依存 / `test_outbound_write_ban` の相対形 2 件 = 配置依存）。手順 5・6 の範囲。

---

## §6 未解決（送り先つき）

| # | 内容 | 送り先 |
|:-:|:--|:--|
| A | `distill_lessons.py` / `distill-lessons.py` の重複 | 手順 5 の前に確定 |
| B | `model-roster.md` / `terminology.md` の「構造は配る・値は配らない」分離 | v2 |
| C | managed 規範から `docs/artifacts/` 等への dangling 参照 **60 件超** | T2 の射程 v2 / 公開前 |
| D | `personal > project` 解決順と `skillOverrides` の plugin 無効の再裏取り | **ADR-0010 R-1 の未了分** |
| E | `~/claude-global-assets` の `lam-harness` 1.0.0（4 プロジェクトに project スコープで導入済・**全て disabled**）の quarantine | ADR-0010 **M-2** 準拠 |
| F | `CLAUDE.md` 251 行（公式目安 200 行超） | 前セッションからの持ち越し |
| G | `docs/private/` と規律 8 件の所在整理 | **S 分割で部分的に前進**（`fable-l3-protocol.md` は 95 行に縮小）。残りは未着手 |

---

## §7 このセッションで判明した運用上の事実（次セッションが同じ轍を踏まないため）

- **`settings.json` の `hooks` セクションは AI から編集できる**。auto mode がブロックするのは `permissions` 固有。記憶 `settings-json-edit-blocked` を同日修正済（丸ごと「編集不可」と覚えていると不要な手作業依頼を出す）
- **記憶ファイルの frontmatter が本文と食い違っていた** —— `lam-positioning-and-motive` の description が撤回済みの内容を述べており、L1 がそれを読んで**幻の争点を MAGI に立てた**（gabriel 第 1 回が指摘）。同日修正済
- **heredoc 経由の Python で `\n` のエスケープが潰れる**ことがある。改行を含む文字列を書くときは `splitlines()` 等でエスケープを避ける
- **台帳 §C の機構件数が「8 件」のまま 2 週間ずれていた**（#9 / #10 追加時に未追随）。12 に是正済
