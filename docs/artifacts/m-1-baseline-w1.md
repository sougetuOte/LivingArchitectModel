# M-1 ベースライン測定（W1 末）

## メタ情報

| 項目 | 内容 |
|:-----|:-----|
| Milestone | M-1 / Wave 1（トリアージ）末 |
| 測定 Task | W1-M1-T7（W1 末測定 + 安定性ゲート判定入力の収集） |
| 測定日 | 2026-07-25 |
| 手順 | `tasks.md` §9 Wave 末測定の共通手順（全 Wave 共通 / 変更なし = 比較可能性の担保） |
| 比較対象 | `docs/artifacts/m-1-baseline-w0.md`（W0 起点） |
| 対応仕様 | requirements.md FR-8 / NFR-3 / FR-2 |

> **新規機構を追加していない**（NFR-2）: 6 項目のいずれについても新規の集計スクリプト・新規ログファイルを作成していない。既存コマンド・既存文書の手順をそのまま用いた。

---

## 1. 測定 6 項目

| # | 項目 | W0 起点 | **W1 末** | 差分 |
|:-:|:-----|:--------|:----------|:-----|
| 1 | pytest 全数 | 1047 passed + 14 skipped | **1047 passed + 14 skipped**（exit 0 / 27.69s） | **±0（regression ゼロ）** |
| 2 | Green State 件数 | Critical 0 / Warning 0 | **Critical 0 / Warning 0**（下記 1.2） | ±0 |
| 3 | `tdd-patterns.log` FAIL→PASS 率 | 算定せず（synthetic のみ） | **算定不能（母数 0）**（下記 1.3） | — |
| 4 | gabriel verdict 分布 | refuted 3（母数 3） | **W1 中の probe 実行 0 件** / 累計は母数 3・refuted 3 で不変 | W1 中の増加なし |
| 5 | PM 級ダイアログ発火数 | 0 | **0**（下記 1.5） | ±0 |
| 6 | `CLAUDE.md` + rules 文字数 | 154,837 字 / 2,749 行 | **154,837 字 / 2,749 行** | **±0** |

### 1.1 項目 1（pytest）

```bash
bash .claude/scripts/py_invoke.sh -m pytest
```

`1047 passed, 14 skipped in 27.69s` / exit code 0。**NFR-3 の起点（`2ac4e91` / 1043 passed + 14 skipped）および W0 起点（1047 + 14）に対して PASS 数の減少なし・FAIL 0 件**。

### 1.2 項目 2（Green State 件数）

**W1 では監査（AUDITING）を実施していない**ため、共通手順の定義「直近 Wave 末ゲート記録の Critical / Warning 件数」に従い R-2 W1 末ゲート記録の値（Critical 0 / Warning 0）を転記した。W1 は判定のみの Wave であり実ファイル変更がゼロであることから、Issue が新たに発生する経路が存在しない。

### 1.3 項目 3（`tdd-patterns.log` FAIL→PASS 率）

- ログ総行数 **248**、最終 `ANALYZED` マーカーは 244 行目
- 以降のエントリは **W0-M1-T1 の probe による synthetic 3 行のみ**（`PROBE` マーカー行 248 で識別 / 2026-07-25T07:11:36Z・07:11:58Z・07:13:38Z）
- **`PROBE` マーカー以降の新規エントリは 0 行** = W1 中の FAIL→PASS 遷移は発生していない
- synthetic 3 行を除外すると**母数 0** のため、FAIL→PASS 率は**算定不能**

> **本 T7 の pytest 実行でエントリが追記されなかった理由**: PostToolUse hook は「直前に FAIL があった場合の PASS」を遷移として記録する（`trust-model.md` §パターン照合ロジック）。W1 では FAIL が 1 件も発生していないため、遷移として記録される条件を満たさない。**hook の仕様どおりの挙動であり、W0-M1-T2 で修正した XML 鮮度判定の不具合ではない**。

### 1.4 項目 4（gabriel verdict 分布）

- `.claude/gabriel-metrics.log` の最終更新は **2026-07-18**（W1 着手日 2026-07-25 より前）
- `invoked=true` の累計 **3 件**、うち 2026-07-25 のものは **0 件**
- **W1 中の gabriel probe 実行は 0 件**。W1 は MAGI 合議を要する判断（AoT 適用条件 = 判断ポイント 2+ / 影響レイヤー 3+ / 選択肢 3+）を含まず、軽量モードでも合議を起動していないため、probe が発火する経路がなかった

### 1.5 項目 5（PM 級ダイアログ発火数）

**0 件**。W1 の K5 宣言（`tasks.md` §4）は「**なし**」であり、トリアージ表の出力先 `docs/artifacts/m-1-triage-table.md` は SE 級。

ただし **W1-M1-T6 の承認イベント 1 件**が別途存在する。これは「PM 級ファイルの編集承認」ではなく「**トリアージ表という決定内容の承認**」であり（design §3.2 / §5.4）、ファイルパスベースの PM 級ダイアログとは別カテゴリのため項目 5 には計上しない。混同を避けるため本注記を残す。

### 1.6 項目 6（`CLAUDE.md` + rules 文字数）

```bash
cat CLAUDE.md .claude/rules/*.md .claude/rules/*/*.md | wc -m   # 154837
cat CLAUDE.md .claude/rules/*.md .claude/rules/*/*.md | wc -l   # 2749
```

**W0 と完全一致**。これは W1 が判定のみの Wave であり、順序制約 3（W1 判定 → W2 適用）が守られたことの数値的裏付けでもある。

> **NFR-6 の遵守**: 本項目は記録であり、削減率・削減行数を W1 の完了条件として用いていない。W1 で文字数が減っていないことは**仕様どおり**である（減っていたら順序制約違反）。

---

## 2. Opus 5 安定性ゲートの判定入力（§5 / FR-2）

### ゲート入力 1: セッション数と malformed インシデント

| 項目 | 実測 |
|:-----|:-----|
| W1 着手〜完了の全セッション数 | **1**（2026-07-25 セッション 7 / `/quick-load` から本測定まで） |
| `docs/artifacts/` の tool malformed インシデント文書（新規起票） | **0 件**（既存の `incident-2026-06-02-tool-malformed.md` 1 件のみ = W1 より前の起票） |

#### ゲート入力 1 の補足: upstream の malformed 事象の現況（2026-07-25 調査 / `upstream-first.md` 準拠）

| issue | 対象 | 症状 | 状態 |
|:---|:---|:---|:---|
| [#63604](https://github.com/anthropics/claude-code/issues/63604) | **Opus 4.8**（4.7 は正常と明記） | malformed な `tool_use` ブロックを繰り返し emit し応答全体が破棄される | open |
| [#67295](https://github.com/anthropics/claude-code/issues/67295) | **Opus 4.8** | `/compact` 後の長セッションで malformed による stall が再発 | open |
| [#65787](https://github.com/anthropics/claude-code/issues/65787) | Opus 4.8 / CC 2.1.167 | 実際には成功した tool 呼び出しの直後に**偽の** malformed が注入される | **closed as not planned**（duplicate / stale） |
| [#61133](https://github.com/anthropics/claude-code/issues/61133) | Opus 4.7 | 2026-05-20 以降「could not be parsed (retry also failed)」 | open |
| [#64235](https://github.com/anthropics/claude-code/issues/64235) | 複数 | 2026-05-29 以降のリグレッション（`stop_reason=tool_use` なのに `tool_use` ブロックが無い） | open |
| [#66153](https://github.com/anthropics/claude-code/issues/66153) / [#60584](https://github.com/anthropics/claude-code/issues/60584) | Opus 4.8 | tool markup が `court` として出力され実行されない | open |

**報告されている発生条件（共通項）**: 長セッション / 高 tool-call volume / `/compact` 後 / MCP ツール / 並列 tool 呼び出し / deferred-tool loading。

**Opus 5 での報告は 2026-07-25 時点で見当たらない**。ただし Opus 5 のリリースは 2026-07-24 であり、**母数が小さいため「報告がない」ことは「安全」の証明ではない**（FR-19 受け入れ条件 2 に準じ、断定しない）。

**本セッション（W1）の該当性**: 上記の発生条件のうち **5 つ**（長セッション / 高 tool-call volume / 並列 tool 呼び出し / deferred-tool loading = ToolSearch / background subagent）に該当したが、**malformed は 1 件も発生しなかった**。これはゲート条件 1 の**質的な補強材料**だが、母数が 1 セッションである事実を変えるものではない。

> **LAM 側の既存記述との関係**: `CLAUDE.md` §Context Management が引用する「malformed の高コンテキスト相関」は、上記 #65787 / #67295 の「長セッション・高 tool-call volume との相関」報告と整合する。一方 `docs/artifacts/incident-2026-06-02-tool-malformed.md` および memory の「Opus 4.8 は malformed 多発のため 4.7 据え置き」判断は **Opus 4.x 世代の観測**であり、Opus 5 に対する据え置き根拠としては失効している（実行モデルは既に Opus 5）。

### ゲート入力 2: pytest 差分

| 項目 | 実測 |
|:-----|:-----|
| W0 ベースライン比の PASS 数差分 | **±0**（1047 → 1047） |
| FAIL 件数 | **0** |

### ゲート入力 3: gabriel probe

| 項目 | 実測 |
|:-----|:-----|
| W1 中の probe 実行件数 | **0 件** |
| `verdict=refuted & severity=critical` の連続発生 | **なし**（probe 実行が 0 のため発生しえない） |

---

## 3. ゲート判定: **保留**（W1 延長 / FR-2・design §5.5）

| # | 条件 | 実測 | 判定 |
|:-:|:-----|:-----|:-----|
| 1 | malformed / tool 呼び出し異常ゼロ | 新規起票 0 件。ただし**母数が 1 セッション**（規定は最低 3 セッション） | **判定保留（母数不足）** |
| 2 | pytest regression ゼロ | PASS 数減少なし・FAIL 0 | **合格** |
| 3 | gabriel verdict 分布に異常なし | probe 実行 0 回 | **skip（判定不能）**（§5 条件 3 の規定どおり） |

### 3.1 保留の理由と根拠

`tasks.md` §5 は条件 1 の母数を「**W1 着手から完了までの全セッション（最低 3 セッション）。3 未満なら判定を保留し W1 を延長**」と定める。W1 は**本セッション 1 つで T1〜T7 を完走した**ため、母数が規定を満たさない。

**したがって Opus 5 安定性ゲートは合格とせず、判定を保留し W1 を延長する**（design §5.5 / W1-M1-T7 完了条件の最終項）。条件 2 は合格、条件 3 は規定どおり skip であり、**不合格ではない**点を明記する（不合格時のフォールバック手順 = Opus 4.7 への切替・M-1 一時停止は発動しない）。

### 3.2 構造的な論点（W4-M1-T5 retro の入力）

ゲート条件 1 の母数は「セッション数」で定義されているため、**Wave を効率よく 1 セッションで完走するほど母数が不足して先に進めなくなる**という逆インセンティブが存在する。W1 の作業自体は全 Task が完了しており、延長中に実施すべき残作業は存在しない。

この論点は本測定の範囲外（母数定義の変更は `tasks.md` §5 の改訂 = PM 級）であるため、**判定は仕様どおり「保留」とし、母数定義の妥当性は retro で扱う**。W1 を実質的に前進させる選択肢は次の 3 つがあり、いずれも PM 級の判断を要する。

| 選択肢 | 内容 | 等級 |
|:-------|:-----|:-----|
| (a) セッションを重ねる | 次セッション以降で W1 の状態のまま観測を継続し、3 セッション到達時にゲートを再判定する | 判断不要（仕様どおり） |
| (b) 母数定義を見直す | 「セッション数」から「実作業量」等への変更を検討する | **PM 級**（`tasks.md` §5 改訂） |
| (c) 母数不足を承知でゲート通過を宣言する | リスク受容としてユーザーが明示的に承認する | **PM 級**（軸 1 = リスク許容度の宣言） |

---

## 4. W1 の成果（参考 / 判定入力ではない）

| Task | 成果 |
|:-----|:-----|
| W1-M1-T1 | 条項抽出 + ID 付与（Sonnet 委譲 → L1 親検収で 14 条項補修 / 92 → 106 件） |
| W1-M1-T2 | 未執筆条項 6 件の組込み（閉集合確定） |
| W1-M1-T3 | 不変制約 4 対象による除外 12 件 / FR-5 受け入れ条件 2 の grep 検証（成立） |
| W1-M1-T4 | Phase A veto 40 件（軸 1 = ユーザー意思）/ Phase B 送り 60 件 |
| W1-M1-T5 | Phase B 判定 60 件（保全 15 / 圧縮 15 / 削減 27 / SSOT 退避 1 / 運用移管 2） |
| W1-M1-T6 | PM 級一括承認（1 承認イベント / 運用移管のリスク受容 + 上限 5 件維持） |
| W1-M1-T7 | 本測定 |

**トリアージ表**: `docs/artifacts/m-1-triage-table.md`（112 条項 / 11 列 / §G に承認記録）

---

## 5. 参照

- `docs/artifacts/m-1-baseline-w0.md`（W0 起点 / 比較対象）
- `docs/artifacts/m-1-triage-table.md`（W1 の主成果物 / §G 承認記録）
- `docs/specs/m-1-opus5-migration/tasks.md` §5（安定性ゲート 3 条件）/ §9（Wave 末測定の共通手順）
- `docs/specs/m-1-opus5-migration/design.md` §5.5（ゲートの設計 / セッション数 3 未満の保留規定）
- `.claude/rules/auto-generated/trust-model.md` §パターン照合ロジック（項目 3 の集計手順）
