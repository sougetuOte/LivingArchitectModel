# R-1 W-R3 S1 T1: 規範文の重複ペア検査 (2026-07-10)

**起票**: 2026-07-10 (L1 = Opus 4.7 / 第 5 コミット目 70cfb78 の F0 アンカー準拠実施)
**Task**: W-R3-S1-T1 (`docs/specs/large-scale-review/tasks.md` L170)
**F0 アンカー**: `docs/artifacts/f0-anchor-r-1-w-r3-s1-t1.md` (Fable-Alembic L3 §6.2 初発火)
**参照設計**: `docs/specs/large-scale-review/design.md` §9 (規範文の重複ペア検査手法)
**次工程**: W-R3 S1 T2 = HGA #13 (旧 #8) 召喚 (7/8 以降クレジット従量 / 本成果物を brief 素材とする)

---

## §1 検査対象一覧

design §9.2 Step 1 で示された grep pattern を実行:

```bash
grep -lE '(SSOT.*docs/internal|実行時要約|要約版|元.*は)' .claude/rules/*.md
```

**ヒット 2 件** (2026-07-10 時点 / `.claude/rules/*.md` = 13 ファイル対象):

| # | ファイル | 冒頭 SSOT 宣言文 (30 行以内) |
|---|---------|-----------------------------|
| 1 | `.claude/rules/decision-making.md` L5 | `> **SSOT**: docs/internal/06_DECISION_MAKING.md。本ファイルは実行時の要約版。` |
| 2 | `.claude/rules/fable-l3-protocol.md` L5, L9 | `**位置づけ**: LAM は Fable-Alembic を L3 (深く同化) で運用する。本ファイルは L3 導入の SSOT。` / `> ... SSOT の貼付場所は本ファイル (.claude/rules/fable-l3-protocol.md §0)。` |

### §1.1 拡張 pattern 検証 (F0 の F1 仮定検証)

F0 アンカー §F1 で「grep pattern が過不足なく捕捉するかは仮定」と明記。仮定検証として拡張 pattern を実測:

```bash
for f in .claude/rules/*.md; do
  head -30 "$f" | grep -qiE "(SSOT|本ファイル.*要約|詳細は.*docs/internal|基底原理|参照SSOT|参照 SSOT|親.*規範|原典)" && echo "HIT: $f"
done
```

→ **ヒット 2 件で同一** (decision-making.md + fable-l3-protocol.md)。**F1 仮定は実測で裏付け** = design §9.2 の grep pattern は本 T1 実施時点で過不足なく捕捉している。

**追加 pattern を検討したが本 Task では不採用**:
- 「原典」パターンは fable-l3-protocol.md §1 のみで発火するが同ファイルは既に捕捉済
- 「詳細は」パターンは全 rules で頻出 (相互参照レベル) のため SSOT 親宣言と区別不能 → scope 外

## §2 重複ペア一覧

### §2.1 検査対象 pair 表

| # | 要約側 (LAM 内) | 親 SSOT | 親 SSOT の所在 | 本 Task scope |
|---|----------------|--------|---------------|---------------|
| P1 | `.claude/rules/decision-making.md` (70 行) | `docs/internal/06_DECISION_MAKING.md` (286 行) | LAM 内 (`docs/internal/`) | **対象** |
| P2 | `.claude/rules/fable-l3-protocol.md` (自身が SSOT) | `D:\work7\Fable-Alembic\knowledge\{Fable行動規範,自己監査チェックリスト,体験シミュレーション・プロトコル,実行プロトコル}.md` | 外部リポジトリ (`D:\work7\Fable-Alembic\`) | **scope 外** (docs/internal 内に親を持たない / Outbound Write Ban 対象 / §4 で対応方針記録のみ) |

### §2.2 P1 概要 (decision-making.md × 06_DECISION_MAKING.md)

- **要約側 (実行時参照)**: `.claude/rules/decision-making.md` = 70 行 / MAGI System + Execution Flow + AoT + Output Format のみ
- **親 SSOT (詳細正本)**: `docs/internal/06_DECISION_MAKING.md` = 286 行 / §1 Core Concept 〜 §6.9 参照までフル記述
- **意図**: decision-making.md は「実行時要約」と自己宣言。詳細は親 SSOT 参照が正規経路
- **既知 issue**: `docs/specs/large-scale-review/design.md` §9.1 で「意図された重複ペア」と明示

### §2.3 P2 概要 (fable-l3-protocol.md / scope 外)

- 自身が「LAM 内の SSOT」= 親 SSOT を LAM 内に持たない
- 外部 SSOT (`D:\work7\Fable-Alembic\knowledge\`) は `fable-l3-protocol.md` §2 で「参照 SSOT」と明示 / **Outbound Write Ban** (全レベル共通 MUST NOT) により LAM 側から編集不能
- 従って **本 Task の「規範文重複ペア検査 (rules × docs/internal)」の scope 外**
- ただし HGA #13 brief には「fable-l3-protocol.md は自身が SSOT の非対称構造 / 外部参照 SSOT を持つ唯一の rules」を参考情報として渡す (crux 判定素材)

---

## §3 差分要約 (P1 のみ / 見出し diff + M 命題以上の欠落列挙)

### §3.1 見出し diff (実測)

```bash
diff <(grep -oE '^###?\s.*' .claude/rules/decision-making.md) \
     <(grep -oE '^###?\s.*' docs/internal/06_DECISION_MAKING.md)
```

**要約側にある見出し** (7 件):
- `## MAGI System` / `## Execution Flow` / `## AoT（Atom of Thought）` / `### 適用条件（いずれか該当）` / `### Atom の定義` / `### ワークフロー` / `## Output Format`

**親側にのみある見出し** (要約側で欠落 / 20 件):
- `## 1. Core Concept` / `## 2. Execution Flow` (`### Step 1: Divergence` / `### Step 2: Debate` / `### Step 3: Convergence`)
- `## 3. Output Format (Example)` / `### Multi-Perspective Analysis`
- `## 4. When to Use`
- `## 5. Atom of Thought (AoT) による前処理` (`### 5.1. Atom の定義` / `### 5.2. 適用判断フローチャート` / `### 5.3. 適用条件` / `### 5.4. AoT + MAGI ワークフロー` / `### 5.5. 出力フォーマット`)
- `## 6. gabriel Adversarial Probe（AoT 適用時のみ / 旧 Reflection）` (`### 6.1. 背景` / `### 6.2. Step 番号体系` / `### 6.3. AoT フレームワークの温存` / `### 6.4. gabriel の役割` / `### 6.5. gabriel 出力契約` / `### 6.6. 失敗時挙動` / `### 6.7. 実装 SSOT + テスト` / `### 6.8. opt-out 経路` / `### 6.9. 参照`)

### §3.2 M/S 命題以上の欠落 (要約側にない親側 MUST/SHOULD)

design §9.3「M 命題以上」= RFC 2119 の MUST/SHOULD レベル規範と定義。Info 級 (mermaid 図 / 実装パス列挙 / 参照リスト) は表から除外し、欠落 12 件を M/S/I の 3 段階で分類:

| # | 親側 節 | 命題内容 | 級 | 要約側の現状 |
|---|--------|---------|:-:|-------------|
| M-01 | §2 Step 3 | 「必ず『採用しなかった選択肢』とその理由も記録すること」 | **M** (MUST) | 完全欠落 |
| M-02 | §6.2 | 「軽量モードで gabriel は起動しない (FR-W-C-3 **MUST NOT**)」+「MAGI ログ冒頭で必ずモード (AoT / 軽量) 宣言」 | **M** (MUST NOT + MUST) | gabriel probe 節に「AoT 適用時のみ」の但し書きはあるが**モード宣言 MUST** は欠落 |
| M-03 | §6.3 | 「AoT フレームワーク (§5.1-5.3) は無改変で保存する (NFR-W-C-6 **MUST NOT**)」 | **M** (MUST NOT) | 完全欠落 |
| M-04 | §6.8 | opt-out 2 条件 (理由 1 文以上記録 + ユーザー L1 明示) + **AUTONOMOUS フェーズでの自律ループ opt-out は却下** (ADR-0005 FR-9.1) | **M** (MUST) | 完全欠落 |
| S-01 | §1 CASPAR 行 | CASPAR は「合意に至らない場合は独断で決定を下す**権限**を持つ」 | **S** (SHOULD) | フォーカスのみ (Synthesis, Balance, Decision) / 権限記述欠落 |
| S-02 | §4 When to Use | 4 種の適用場面 (ライブラリ選定 / DB スキーマ / 大規模リファクタ / 曖昧要件) | **S** | 完全欠落 |
| S-03 | §6.4 プローブ観点 | rubric 5 観点 (論理的一貫性 / 仕様整合 / リスク見落とし / 前提検証 / 境界条件) | **S** | 完全欠落 (「詳細分岐は SKILL.md §Step 4.1」参照へ丸投げ) |
| S-04 | §6.6 失敗時挙動 | 5 段階挙動 (critical 初回=再 MAGI / critical 2 回目=人間 esc / warning=併記 / info=記録 / abort=即時 esc) | **S** | 「詳細分岐は SKILL.md §Step 4.1」で参照丸投げ = **参照先明示のため許容範囲** |
| I-01 | §5.2 | 適用判断フローチャート (mermaid) | I | 欠落 (Info = 要約に不要) |
| I-02 | §5.4 | AoT + MAGI ワークフロー 6 段階図 (Step 0-5) | I | 3 行圧縮あり |
| I-03 | §6.7 | 実装 SSOT パス (`magi_dispatch.py`) + 統合テスト 3 種 (26+21+16 件) | I | 欠落 (Info = 実装詳細) |
| I-04 | §6.9 | 参照リスト 6 件 (SKILL.md / requirements+design v0.4.0 / ADR-0007 / ADR-0005 FR-9.1 / gabriel.md / MAR 論文) | I | 「親 SSOT: §6.5-6.6」の 1 行のみ |

**M/S 級欠落集計**: MUST 級 4 件 (M-01/02/03/04) + SHOULD 級 3-4 件 (S-01/02/03、S-04 は許容範囲) = **7-8 件**

### §3.3 要約側で維持されている M 命題 (裏取り)

要約側 `.claude/rules/decision-making.md` L38-45 の gabriel probe 節に以下 M 命題が明記されている:

- `verdict / severity / affected_atoms (verdict=refuted 時は非空必須) / reasoning (200-1000 字) / recommended_action / confidence (0.3 未満なら verdict=inconclusive 強制)`
- **分岐優先順位 (MUST)**: `abort > critical+re-magi > warning > info > confirmed > inconclusive`
- 「親 SSOT: `docs/internal/06_DECISION_MAKING.md` §6.5-6.6」の明示

これにより gabriel 出力契約と分岐優先順位という**最重要 M 命題群**は要約側に保存されている。§3.2 の欠落は主に「モード宣言 / opt-out / When to Use / 採用しなかった選択肢の記録」等の**運用 MUST/SHOULD** に集中。

---

## §4 対応方針 (3 分類 / 候補 / HGA #13 で確定)

design §9.3 の対応方針 3 分類 (更新 / 省略明記 / 統合) をペア別に付与。**確定は W-R3 S1 T2 = HGA #13 (Fable) に委譲** (本 Task は候補列挙のみ / F0 §「やらないこと」= 「検査結果に基づく rules の実修正禁止」準拠)。

### §4.1 P1 (decision-making.md × 06_DECISION_MAKING.md) 対応方針候補

| 案 | 分類 | 内容 | メリット | デメリット |
|:-:|:----|-----|---------|-----------|
| A | **更新** | MUST 級 4 件 (M-01/02/03/04) を要約側に追記 + SHOULD 級 3 件 (S-01/02/03) は「詳細は 06_DECISION_MAKING.md §X 参照」の 1 行で参照丸投げ | 実行時参照速度を保ちつつ MUST 級規範漏れゼロ | 追記行数 +15〜20 行 (現 70 行 → 85〜90 行) / 「要約」の存在意義に若干の緊張 |
| B | **省略明記** | 要約側に「本ファイルは実行時要約であり、以下の運用 MUST/SHOULD は親 SSOT §2/§6.2/§6.3/§6.8 参照必須」の 1 段落追加 (要約側追記なし) | 最小改変 / 「要約」責務境界を明確化 | 実行時に MUST 級を見落とすリスク残存 (LAM 起動時に CLAUDE.md 経由で decision-making.md のみ読まれる) |
| C | **統合** | decision-making.md 廃止 / 06_DECISION_MAKING.md 直参照に統一 | SSOT 一元化 / 重複ペア構造の根本解消 | 実行時読取コスト増 (286 行常時ロード) / CLAUDE.md 参照経路の全面変更 (§References 表更新必要) |

**L1 推奨 (HGA #13 前の暫定)**: **案 A** (更新)

理由:
- **可逆性 高**: 追記のみで既存構造・参照経路無変更 (git 巻き戻し可)
- **復旧コスト 低**: 追記 15-20 行の再修正で完了
- **確認コスト 低**: HGA #13 で crux 分岐せず即進行できる
- 案 B は「実行時に MUST 級見落とし」のリスクが第 0 原則の可逆性に反する (見落として作った結論の巻き戻しは高コスト)
- 案 C は現状 286 行を実行時常時ロードすることになり、CLAUDE.md 冒頭からの参照速度を犠牲にする / 影響レイヤーが「全 rules 参照経路」に拡大 (単一ペア対応の scope 逸脱)

### §4.2 P2 (fable-l3-protocol.md) 対応方針

| 分類 | 内容 |
|:----|-----|
| **該当なし (scope 外)** | 親 SSOT が LAM 外部 (`D:\work7\Fable-Alembic\knowledge\`) にあり Outbound Write Ban で編集不能。本 Task の「rules × docs/internal ペア検査」の scope 外。将来的な検査軸として「LAM 内 SSOT × 外部参照 SSOT」ペアが必要かは W-R5 retro 議題化候補 (fable-l3-protocol.md §9 検証課題との合算で判断) |

### §4.3 HGA #13 brief 想定素材 (T2 引き継ぎ)

W-R3 S1 T2 で Fable に渡すべき crux 素材 (F0 §受け手 = 「時間がない Fable / brief 15-20k 制約」対応):

1. **§3.2 表の M/S 級欠落 8 件** (crux = 「MUST 級 4 件のうち M-03 = AoT フレームワーク無改変保存 MUST NOT を要約側に書くべきか」= AoT 実装の非対称関与ゾーン / gabriel 実装の温存責任所在で意見が割れる可能性大)
2. **§4.1 案 A/B/C の crux 分岐** (可逆性 3 変数で L1 は案 A 推奨だが、Fable 独自の受け手体験シミュから見て別軸が湧く可能性)
3. **§2.3 P2 の非対称構造** (fable-l3-protocol.md × 外部 SSOT のペア構造 / 本 Task scope 外だが Fable にとっては自ファイル関連 = 発言する立場と発言される立場が同居する構造)

---

## §5 検証

### §5.1 F0 完了条件のセルフチェック (F4 相当 / 提出前の観測)

| # | F0 完了条件 | 本成果物での充足 |
|:-:|-------------|-----------------|
| 1 | §1 検査対象一覧 (grep 結果反映) | §1 に grep 結果 2 件 + 拡張 pattern の仮定検証 |
| 2 | §2 重複ペア一覧 (最低 1 件 = decision-making.md × 06_DECISION_MAKING.md) | §2 に P1 + P2 (scope 外扱い) |
| 3 | §3 差分要約 (見出し diff + M 命題以上の欠落列挙) | §3.1 実 diff + §3.2 M/S/I 分類表 12 件 |
| 4 | §4 対応方針 3 分類 (更新 / 省略明記 / 統合) | §4.1 に 3 案 + L1 推奨 (第 0 原則 3 変数根拠) |

### §5.2 検証コマンド (F0 §検証方法準拠)

```bash
# Step 1 grep 再走 (§1 の裏取り)
grep -lE '(SSOT.*docs/internal|実行時要約|要約版|元.*は)' .claude/rules/*.md
# → 2 件ヒット (decision-making.md + fable-l3-protocol.md) を期待

# 成果物存在確認
test -f docs/artifacts/r-1-duplicate-pair-audit-2026-07-10.md && echo "OK"
```

### §5.3 体験シミュ (Fable-Alembic L3 §5.1 発火点該当 = **なし**)

本成果物は「監査レポート」ではなく「検査記録 + HGA brief 素材」であり、`fable-l3-protocol.md` §5.1 の 3 発火点 (PLANNING 承認要求提出直前 / /ship Phase 3.5 / AUDITING 監査レポート提出直前) に該当しない。従って **60 秒実況 MUST 発火点なし**。

### §5.4 tracker 反映 (T5 = Stage 末 ship で実施)

- `docs/artifacts/r-1-audit-tracker.md` への reflection は W-R3 S1 T5 = Stage 末 ship (T2/T3/T4 完了後) で一括反映
- 本 T1 単独では tracker 変更なし (F0 §「やらないこと」= 検査結果に基づく実修正禁止 準拠)

---

## §6 参照

- **F0 アンカー**: `docs/artifacts/f0-anchor-r-1-w-r3-s1-t1.md`
- **設計手順**: `docs/specs/large-scale-review/design.md` §9 (規範文の重複ペア検査手法)
- **Tasks 表**: `docs/specs/large-scale-review/tasks.md` §4 (W-R3 逐次) L164-174
- **L3 規律**: `.claude/rules/fable-l3-protocol.md` §6.2 (F0 4 行アンカー / 常時発動) / §5.1 (体験シミュ 3 発火点)
- **要約側**: `.claude/rules/decision-making.md` (70 行 / 実行時要約)
- **親 SSOT**: `docs/internal/06_DECISION_MAKING.md` (286 行 / MAGI + AoT + gabriel フル)
- **外部 SSOT (P2 scope 外)**: `D:\work7\Fable-Alembic\knowledge\` (Outbound Write Ban 対象)
- **HGA #10 実績**: `docs/artifacts/hga-summon-log.md` §10 (W-R2 S2 で回収可能 = 本 T2 の envelope 想定 = $2-3 圏 = #4 型パターン準拠)
