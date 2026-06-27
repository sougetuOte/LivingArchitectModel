# MAGI 議事録 — Wave 7 Stage 3 V-2 HTML 構造選定

- 日付: 2026-06-27
- 場所: LAM プロジェクト / Wave 7 Stage 3 PLANNING 段階
- 議題: V-2 (Milestone 一覧ビュー) の HTML 構造を table 維持 (案 B) か section/article 変換 (案 A) か
- 参加: L1 (Opus 4.7) として MELCHIOR / BALTHASAR / CASPAR を演じる単一 Atom 合議
- 形式: AoT 分解は省略 (判断ポイント 1 / 影響レイヤー 2 / 選択肢 3 → 1 Atom 単純合議)
- 起因: spec-critic 独立レビュー後の L1 実機確認で先取り実装発見 + 構造的乖離検出

---

## §1 前提情報

### 実機確認結果 (L1 検出)

| 項目 | 結果 |
|:---|:---|
| `_render_v2_milestones()` 現状 | `<table>/<tr>` 構造で複数 Milestone をループ表示 (builder.py L546-590) |
| design.md v0.2.3 §8 要求 | `<section>/<article class="milestone-card">` + `<h3>` + `<p>Step:</p>` 構造 |
| test_v2_view.py | 24 件全 PASS (table 構造前提の assert を含む) |
| 既達 FR | 複数 Milestone 表示 (FR-W7-4) は実質達成済 / ソート (Milestone 名昇順) 未実装 |
| CSS 現状 | 9,922 bytes (utf-8 / `_render_style()` 戻り値) — design.md §8 と完全一致 |
| メソッド名 | 実装 `_render_style` / 仕様 `_render_css` (用語乖離 / 別途記録) |

### 選択肢の整理

| 案 | 内容 | 工数 | 仕様忠実性 |
|:---|:---|:---|:---|
| A | design.md §8 通り table → section/article 変換 + ソート追加 + CSS 追加 | L (~85 分) | ✅ 完全準拠 |
| B | 現状 table 維持 + ソートのみ追加 | S (~30 分) | ❌ v0.2.4 補追必要 |
| C | MAGI 合議で再決定 (本議事録) | — | — |

---

## §2 MELCHIOR (Affirmative / 推進者 / Value, Speed, Innovation)

**案 B (table 維持 + ソート追加) 推進**

- **Value**: 既存 24 件全 PASS の安定動作を維持しつつ、要件 (FR-W7-4) は既達 + ソート追加で完全達成
- **Speed**: 工数 ~30 分 / 案 A の ~85 分から 65% 短縮
- **Innovation**: Stage 1 (実装→仕様一致化) と Stage 2 (先取り実装発見) を経た**柔軟性の発露**
- **隠れた利点**: table `<th>` ヘッダはスクリーンリーダーで「列見出し」として announce される
- **CSS 余裕**: 残 318 bytes → 将来拡張余地

**結論**: 案 B + v0.2.4 補追 (design.md / tasks.md / requirements.md) で進めるべき。

---

## §3 BALTHASAR (Critical / 批判者 / Risk, Security, Debt)

**案 B の致命的リスクを指摘**

1. **仕様信頼性損傷 (最重要)**: design.md v0.2.3 は PM (ユーザー) 自身が 2026-06-27 朝に補追承認したばかり。同日中に v0.2.4 補追で否定すれば**「approved → 即否定」の前例**が確立 → 将来 PLANNING の重みが薄れる
2. **debt 蓄積**: Stage 1 で「実装→仕様一致化」(T56 ディレクトリ再帰走査)、Stage 3 で「仕様→実装一致化」(案 B) は**真逆の判断**。一貫性のない判断パターンを retro で正当化する負債
3. **HTML semantics**: Milestone 一覧は「複数エンティティ集合」であり tabular data ではない。HTML5 semantics では section/article が正しい
4. **将来拡張**: chip `task_68008f88` (Milestone 別 Step 表示 / Milestone カード展開) 等の将来要件が来た時、table 構造では拡張困難 → 結局後で section/article 化する → **二度手間**
5. **a11y 実測未確認**: MELCHIOR の「table は a11y で実装的に強い」主張は Lighthouse 実測で確認していない。Wave 6 終端 97 は table 構造での値だが、section/article でも維持可能と推定
6. **CSS 18 bytes ギリギリ問題**: 案 A の懸念だが、縮退オプション 4 件が design.md §8 に既に用意されている → リスク低

**結論**: 案 A (完全準拠) を強く推奨。短期工数削減と引き換えに長期負債を蓄積するのは不可。

---

## §4 CASPAR (Mediator / 調停者 / Synthesis, Balance, Decision)

### 論点整理

| 軸 | 案 A 評価 | 案 B 評価 | 重要度 |
|:---|:---|:---|:---|
| 仕様忠実性 | ◎ | ✗ v0.2.4 必要 | 高 |
| 工数 | △ 85 分 | ◎ 30 分 | 中 |
| 既存テスト破損 | ✗ 大 | ◎ 小 | 中 |
| HTML semantics | ◎ | △ | 中 |
| a11y (Lighthouse) | ? 未測定 | ◎ 97 維持確認済 | 高 |
| CSS 予算 | △ 18 bytes (縮退準備済) | ◎ 318 bytes | 中 |
| 将来拡張性 | ◎ | △ | 中 |
| 判断一貫性 (Stage 1 とのアラインメント) | ◎ | ✗ 真逆 | 高 |
| Stage 4 PoC レビュー時の見栄え | ◎ カード明確 | △ 詰まった見え方 | 中 |

### Mediation 候補 (中間案 A')

> **案 A': 完全準拠だが Stage 4 で再評価**
>
> Stage 3 では design.md §8 通り section/article に変換 (案 A) する。
> Stage 4 PoC レビュー (T-S4-7 / T-S4-8) で a11y 退行・視覚的 UX 後退が確認された場合は、
> Stage 5+ または別 Wave で table への巻き戻しを検討する余地を将来候補として記録。

### CASPAR 結論: **案 A (design.md §8 完全準拠)** を採用

理由:
1. **Risk 1 (仕様信頼性損傷) の重み**: 同日内 v0.2.3 → v0.2.4 補追は PM 承認の信頼性を傷つける → BALTHASAR 主張が圧倒的に正しい
2. **判断一貫性**: Stage 1 で「実装→仕様一致化」を選択した以上、Stage 3 でも同方向を維持
3. **工数 +55 分は許容範囲**: 本セッションの時間・コンテキスト余裕は十分
4. **CSS 縮退オプション準備済**: design.md §8 に 4 件のオプション定義済 → 超過時の対応は明確
5. **既存テスト破損 = TDD の正常動作**: Red になることで「実装↔仕様」の一致を検証する機会

部分採用 (MELCHIOR の主張):
- Lighthouse 実測を Step 5 に組み込む (Stage 4 T-S4-1 を前倒し)
- a11y 退行 (97 から) が起きていないか確認
- 退行確認時のみ Stage 4 で巻き戻し検討 (案 A' のフォールバック)

---

## §5 Reflection (全員で結論を検証)

**MELCHIOR**: 工数増は承知。Stage 5 フォールバック条項組み込み条件で案 A 受諾。

**BALTHASAR**: 異議なし。a11y 実測条項追加で完璧。

**CASPAR**: 致命的見落とし → **1 件あり**:
- 「table → section/article 変換時、`<th>` 列見出しが失われる」→ 列見出しに依存していたスクリーンリーダーユーザー体験が変わる
- ただし design.md §8 サンプルでは `<h3>` + `<p>Step:</p>` + `<p>状態:</p>` でセマンティック構造が確保されている → a11y 上は問題ない見込み
- **要 Step 5 で chrome-devtools-mcp による aria-* 属性確認 + Lighthouse 実測**

---

## §6 統合結論

### 採用案

**案 A: design.md §8 完全準拠 (section/article 構造 + Milestone 名昇順ソート + CSS 追加)**

### Stage 3 実行時の追加遵守事項 (MAGI 合議で確定)

1. **Lighthouse 実測を Step 5 に必須化** (Stage 4 T-S4-1 を前倒し相当)
2. **Lighthouse Accessibility ≥ 95 確認** (目標 97 維持)
3. **退行発生時は Stage 5+ で巻き戻し検討の余地を将来候補として記録** (`future-candidates.md`)
4. **chrome-devtools-mcp で aria-* 属性 + 構造化見出し階層を確認**

### execution-plan v0.2.0 への反映項目

- 案 A 採用 (案 B / C は却下)
- Step 5 に Lighthouse 実測ステップ追加
- §5 リスク表に「R-7: a11y 退行リスク (table → section/article 変換)」追加
- §6 成功基準に「Lighthouse a11y ≥ 95」追加

---

## §7 PM 承認記録

- 2026-06-27 (本日): ユーザーが「C」選択により MAGI 合議を依頼 → MAGI 合議の結論 (案 A 採用) を承諾

---

## §8 参照

- `docs/specs/b4-dashboard/wave7/design.md` v0.2.3 §8
- `docs/specs/b4-dashboard/wave7/tasks.md` v0.2.3 §3 Stage 3 / §6 T51-T53
- `docs/artifacts/wave7-stage3-execution-plan.md` v0.1.0 → v0.2.0 (本議事録反映)
- `.claude/rules/decision-making.md` (MAGI System SSOT)
- `docs/internal/06_DECISION_MAKING.md` (MAGI SSOT)
