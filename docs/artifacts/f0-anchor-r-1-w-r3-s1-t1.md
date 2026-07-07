# F0 アンカー: R-1 W-R3 S1 T1 (規範文の重複ペア検査)

**起票**: 2026-07-07
**Task**: W-R3-S1-T1 (`docs/specs/large-scale-review/tasks.md` L170)
**担当**: L1 (Opus 4.7)
**参照**: `docs/specs/large-scale-review/design.md` §9 (規範文の重複ペア検査手法)
**L3 protocol**: `.claude/rules/fable-l3-protocol.md` §6.2 (F0 の初適用場面)

---

## 完了条件 (観測可能)

`docs/artifacts/r-1-duplicate-pair-audit-2026-07-{date}.md` が存在し、以下 4 節を含むこと:

1. **§1 検査対象一覧**: `.claude/rules/*.md` の冒頭 30 行 grep で SSOT 親宣言 (「SSOT」「実行時要約」「要約版」「元は」) を持つ rules ファイルのリスト
2. **§2 重複ペア一覧**: 各 rules × 親 SSOT (`docs/internal/*.md`) の pair 表 (最低 1 件 = decision-making.md × 06_DECISION_MAKING.md は既知)
3. **§3 差分要約**: 各ペアの見出し diff (grep で `^###?\s` レベル) + 「親側にあるが要約側にない」項目 (M 命題以上) の列挙
4. **§4 対応方針**: 各ペアに対し 3 分類 (更新 / 省略明記 / 統合) のいずれかを付与

## 検証方法 (実コマンド 1 つ)

```bash
# Step 1 grep
grep -lE '(SSOT.*docs/internal|実行時要約|要約版|元.*は)' .claude/rules/*.md
# → 結果が成果物 §1 に反映されているか目視確認
```

+ 成果物 md の存在確認: `test -f docs/artifacts/r-1-duplicate-pair-audit-2026-07-*.md`

## やらないこと (スコープ拡大の錨)

- **検査結果に基づく rules の実修正禁止** (それは W-R3 S3 の作業 / `docs/specs/large-scale-review/tasks.md` L165)
- **HGA #13 (旧 #8) 召喚禁止** (それは W-R3 S1 T2 の作業 / クレジット従量 = 2026-07-08 16:00 以降)
- **検査対象外の重複ペア検査禁止** (`docs/specs/` / `docs/adr/` の一貫性は W-R3 S4 の作業 / tasks.md L166)
- **依存関係修正・structural refactor 禁止** (対象は「文書間の重複ペア」であり内部構造改善ではない)

## 受け手 (制約 1 つ必須 / L3 §5.4 ガード 5)

**HGA #13 召喚時の Fable** (制約 = 時間がない / brief 15-20k 制約下 / 重複ペア一覧を「crux 判断素材」として即座に読める形式が必要)

- Fable は brief を読んで対応方針 3 案の crux 分岐を返す立場
- 一覧が「どの重複ペアで統合方針が割れるか」を即座に判定できる形でないと crux-scoping ができない
- したがって成果物は §3 差分要約 → §4 対応方針の対応が 1 行で追える table 形式であること

---

## 次セッションでの実装ステップ (F0 後の F1-F3 準備)

**F1 (事実/仮定/不明の仕分け / L3 §6.3)**:
- **事実**: design §9 が確定手順 (Step 1-3) を提示済 / .claude/rules/*.md の全ファイル存在済
- **仮定**: 「SSOT 親宣言」grep パターン `(SSOT.*docs/internal|実行時要約|要約版|元.*は)` が過不足なく親宣言を捕捉する (要検証 / 仮定が崩れたら追加 pattern 実測で拡張)
- **不明**: `docs/internal/*.md` の親 SSOT 側が W-R3 S2 で修正される (module 8 の drift 解消 / tasks.md L164) → 本 Task の差分要約は「本 Task 起票時点のスナップショット」であることを明記する必要

**F2 (リスク順分解 / L3 §6.4)**:
- 軽量モード (非 AoT) を選択 = 判断ポイント少 / 選択肢少 (Step 1-3 が確定手順) / 影響レイヤー 1 (docs/artifacts のみ)
- ただし対応方針 3 分類 (更新 / 省略明記 / 統合) の判断は HGA #13 に委ねる = 本 Task では方針**候補**のみ列挙、確定は HGA 後

**F3 (実行ループ / L3 §6.5)**:
- 圧縮 1 問「次の一手は残リスク最大のピースか」
- 手が止まったら 4 問目「人間しか答えられないことで詰まってないか」を復活 (対応方針判定で L1 単独では決められないケース → HGA 委譲を明示)
- 試行上限: 同一 grep pattern の再試行 2 回まで / 合計 3 アプローチまで

## セッション断絶時の復帰

本 F0 アンカーを Read → 完了条件・検証方法・やらないこと・受け手を再確認 → 未着手 or 途中の場合はここから再開する。
