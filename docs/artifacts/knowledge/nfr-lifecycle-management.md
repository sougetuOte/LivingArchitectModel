# NFR 寿命管理ルール（Knowledge）

- 起源: Wave 7 Stage 3 NFR-W7-1 CSS 予算根本見直し MAGI 合議（A5 結論）
- 確定日: 2026-06-28
- 議事録: `docs/artifacts/2026-06-28-magi-nfr-w7-1-budget-revision.md`

---

## 背景

Wave 7 Stage 3 BUILDING 着手時、NFR-W7-1（CSS 予算 10,240 bytes）が Wave 6 NFR-W6-3 から無検証で継承され、Wave 7 で予算逼迫を引き起こした。原因分析:

- Wave 6 設定時の「10 KiB = キリ番」根拠が Wave 7 までの 7 Wave で再評価されなかった
- 継承元の追跡情報が requirements.md に明示されていなかった
- 「MUST 規定」が「絶対遵守」のシグナルとして機能した結果、CSS 拡張余地を縛り続けた

本ルールはこの種の構造的問題を防ぐためのメタ規約。

---

## §1 NFR 継承履歴タグ

NFR が他 Wave / Milestone から継承される場合、以下の継承履歴を NFR 本文に必須付与する:

```markdown
### NFR-W{n}-{m}: {タイトル}（{義務レベル}）

**継承履歴**: {継承元 NFR ID}「{継承元のタイトルまたは要旨}」継承（{バージョン範囲}）→ {現バージョン}で{再評価/上書き/維持}
**次回再評価**: {Milestone / Wave / 期日}
```

### 例

```markdown
### NFR-W7-1: CSS 予算管理（SHOULD / v0.2.4 改訂）

**継承履歴**: Wave 6 NFR-W6-3「追加 CSS ≤ 10 KB」継承（v0.1.0〜v0.2.3）→ v0.2.4 で再評価上書き
**次回再評価**: Milestone B-5 完了時 retro
```

---

## §2 Milestone 完了時の再評価走査

Milestone（B-N）完了時の retro Step 4（知見蓄積）で、以下を 1 行追加する:

```
- 継承 NFR の妥当性チェック: 本 Milestone で継承された NFR を列挙し、(a) 適用根拠が今も有効 / (b) 緩和すべき / (c) 削除すべき のいずれかを判定
```

判定方法:
- NFR 本文に「**継承履歴**」タグがあるものを抽出
- 各継承 NFR について MELCHIOR / BALTHASAR の 2 視点で「今も妥当か」を 1-2 行評価
- 妥当でない場合は次 Milestone で改定議題化

---

## §3 数値ゲート系 NFR の原則

NFR の義務レベル選定原則:

| 義務レベル | 適用基準 | 例 |
|:----------:|:--------|:---|
| **MUST** | 違反が実害（バグ / 退行 / セキュリティ）を直接引き起こす | pytest 全件 PASS / Accessibility ≥ 95 |
| **SHOULD** | 退行検知 / 規律の目安 / 違反しても直接実害なし | CSS バンドルサイズ上限 / Performance スコア |
| **MAY** | 推奨事項 / 任意の改善目標 | 統合テスト記録 |

数値ゲート系 NFR（バイトサイズ / ms / スコア閾値）は **原則 SHOULD**。MUST は「数値違反 = 仕様違反 = バグ」が明確な場合のみ。

---

## §4 3 段階レベル制（数値ゲート系 NFR）

数値ゲート系 NFR は以下の 3 段階で運用:

| レベル | 範囲 | 対応 |
|:------:|:----:|:-----|
| **緑帯** | < 70% | 自由 |
| **黄帯** | 70-90% | Wave 開始時に追加見込みを記録 + 縮退検討 |
| **赤帯** | ≥ 90% | retro で改定議題化必須 + 改定 or ミニマル化 |

赤帯到達自体は MUST 違反ではない（SHOULD のため）。ただし retro 議題化は **プロセスの MUST**。

---

## §5 改定プロセス（標準ルート）

NFR 改定が必要と判明した場合の標準ルート:

```
retro 議題化（赤帯到達 / 妥当性チェック失敗 / その他）
  ↓
MAGI 合議（AoT 適用条件を満たすなら AoT 分解）
  ↓
ユーザー承認（PM 級）
  ↓
仕様書補追（requirements / design / tasks / 関連 execution-plan）v0.X.Y bump
  ↓
連動文書（knowledge / 議事録）更新
```

---

## §6 適用範囲

本ルールは以下のスコープに適用:

- ✅ Project: LAM
- ✅ NFR を持つ Milestone（B-1 以降の全 Milestone）
- ✅ requirements.md 内の NFR セクション
- 〜 既存 NFR への遡及適用は Milestone 完了 retro 時に判断（Wave 8+ で B-5 内の他 NFR を点検）

---

## §7 権限等級

- 本ルールファイルの変更: **PM 級**（メタ規約のため）
- NFR への「継承履歴」タグ付与: **SE 級**（既存 NFR の意味を変えない）
- NFR の数値変更 / 義務レベル変更: **PM 級**

---

## §8 参照

- [.claude/rules/permission-levels.md](../../../.claude/rules/permission-levels.md)
- [.claude/rules/planning-quality-guideline.md](../../../.claude/rules/planning-quality-guideline.md) §2 RFC 2119 キーワード
- [Wave 7 NFR-W7-1 改定議事録](../2026-06-28-magi-nfr-w7-1-budget-revision.md)
