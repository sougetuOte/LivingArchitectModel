---
name: magi
description: >
  MAGI System v2 — AoT 分解 + MELCHIOR/BALTHASAR/CASPAR 合議 + gabriel adversarial probe による
  構造化意思決定フレームワーク。判断ポイント 2+ / 影響レイヤー 3+ / 選択肢 3+ で使用。
  Use when facing complex decisions with multiple trade-offs or architectural choices.
when_to_use: "判断ポイント 2+ / 影響レイヤー 3+ / 選択肢 3+ の複雑な意思決定・アーキテクチャ選択を行うとき。"
---

# /magi — 構造化意思決定（MAGI System v2）

名前の由来: エヴァンゲリオンの MAGI システム（3 つの独立した思考体による合議意思決定）+ **gabriel adversarial verifier**（4 番目の独立検証者）。

## MAGI System v2

**SSOT**: `docs/internal/06_DECISION_MAKING.md` を精読すること。
**Wave C 統合仕様**: `docs/specs/magi-v2-gabriel/{requirements,design}.md` v0.4.0。

| MAGI | ペルソナ | フォーカス |
|:-----|:--------|:----------|
| **MELCHIOR** | 科学者（推進者）[旧: Affirmative] | Value, Speed, Innovation |
| **BALTHASAR** | 母（批判者）[旧: Critical] | Risk, Security, Debt |
| **CASPAR** | 女（調停者）[旧: Mediator] | Synthesis, Balance, Decision（**純調停者化**: Step 3 で完結） |
| **gabriel** | 独立検証者（4 番目）| Adversarial probe / 外部視点からの Convergence 検証 / **AoT 適用時のみ起動** |

## 適用条件

以下のいずれかに該当する場合に発動する:

- 判断ポイントが 2 つ以上
- 影響するレイヤー/モジュールが 3 つ以上
- 有効な選択肢が 3 つ以上

**ユーザーが明示的に `/magi` を呼び出した場合は、条件に合致しなくても必ず実行する。**

条件に合致しないかつ明示呼出しでない場合は「従来手法で十分です」と案内する。

## モード判定: AoT 適用 vs 軽量モード

MAGI は 2 つのモードを持つ:

- **AoT 適用モード**: 判断ポイント 2+ / 影響 3+ / 選択肢 3+ の **いずれか** を満たす → Step 0-5 実施（gabriel probe 含む）
- **軽量モード（非 AoT）**: 上記条件を満たさない → Step 1-3 のみ / **gabriel probe は起動しない**（FR-W-C-3 MUST NOT）

MAGI ログ冒頭で必ずモード（`AoT` または `軽量`）を宣言する。

## 実行フロー

### Step 0: AoT Decomposition（分解 / AoT 適用モードのみ）

議題を独立した Atom（判断単位）に分解し、依存 DAG を構築する。

分解の前に **`docs/adr/` の既存 ADR 一覧を走査**し、同じ判断が既に決定済みでないか（または前提が失効していないか）を確認する。

Atom の 3 条件:
- **自己完結性**: 他の Atom に依存せず独立処理可能
- **インターフェース契約**: 入力と出力が明確
- **エラー隔離**: 失敗しても他 Atom に影響しない

```markdown
### AoT Decomposition

| Atom | 判断内容 | 依存 |
|:-----|:---------|:-----|
| A1 | [判断1] | なし |
| A2 | [判断2] | A1 |
```

### Step 1: Divergence（発散）

MELCHIOR と BALTHASAR がそれぞれの立場から意見を出し尽くす。

- **MELCHIOR**: メリット、開発効率、革新性を列挙
- **BALTHASAR**: リスク、セキュリティ懸念、保守コストを列挙

### Step 2: Debate（議論）

対立するポイントについて、具体的な解決策や緩和策を検討する。

### Step 3: Convergence（収束）

CASPAR が議論を整理し、結論を下す。**CASPAR は Step 3 で完結し、gabriel の結果を受けて再処理を行わない**（純調停者化 / gabriel 統合後の設計原則）。

```markdown
### Atom A1: [判断内容]

**[MELCHIOR]**: ...
**[BALTHASAR]**: ...
**[CASPAR]**: 結論: ...
```

### Step 4: gabriel adversarial probe（AoT 適用モードのみ / 新設）

> **旧 Step 4 Reflection は廃止**（gabriel probe に統合）。
> B-4 監査（2026-06-19）実機計測: Reflection の初回変更率 0%（全 7 件「致命的な見落とし: なし → 結論確定」）で「無効な安全網」であったため、Wave C（骨子 ②）で構造的解決として gabriel に置換した（ADR-0007 Accepted）。

CASPAR の Convergence 結論に対し、**独立コンテキスト**で動作する gabriel subagent が adversarial verification を実施する。

**起動条件**:
- AoT Decomposition（Step 0）が実施されていること
- gabriel opt-out 記録がないこと（下記 §Step 4.2 参照）

**gabriel の役割**: CASPAR の統合結論を **そのまま正としてではなく**、結論に至った前提・根拠・棄却された代替案を独立に再検証する（design.md §4 / FR-W-C-1）。

**プローブ観点（rubric 5 観点）**:
1. **論理的一貫性**: 各 Atom の結論に矛盾がないか
2. **仕様整合**: CASPAR の結論が既存仕様（`docs/specs/` / `docs/internal/`）と矛盾しないか
3. **リスク見落とし**: MELCHIOR / BALTHASAR が検討していない重大なリスクの有無
4. **前提検証**: AoT Decomposition で設定した Atom の依存関係が結論に反映されているか
5. **境界条件**: 結論が適用できないエッジケース（スコープ外・例外）が未記録ではないか

**呼び出し方法**: Task ツール経由で `subagent_type=gabriel` を起動する。gabriel は独立コンテキストで動作し、Read/Glob/Grep/Write/Edit のみ利用可（Bash・Agent ツール禁止 / NFR-W-C-3 暴走リスク抑制）。

**タイムアウト**: 360 秒（NFR-W-C-1 / SHOULD / 2026-07-26 改訂）。呼び出し元で経過時間を計測し、超過時は `verdict=inconclusive + timeout 注記` として扱う。

**gabriel 出力**: 6 フィールド JSON（design.md §3 参照）:
- `verdict`: `confirmed` / `refuted` / `inconclusive`
- `severity`: `critical` / `warning` / `info`
- `affected_atoms`: Atom 識別子リスト（`verdict=refuted` 時は非空必須）
- `reasoning`: 判定理由（200-1000 字）
- `recommended_action`: `proceed` / `re-magi` / `abort`
- `confidence`: 0.0-1.0（0.3 未満は `verdict=inconclusive` 強制）

### Step 4.1: verdict 別分岐処理

gabriel の返り値に応じて以下のいずれかの経路を辿る。**優先順位は `recommended_action=abort` > `severity=critical` > `warning` > `info` > `confirmed` > `inconclusive`**。

| gabriel 出力 | 挙動 | 参照 |
|:------------|:-----|:-----|
| `recommended_action=abort`（verdict / severity 問わず） | **即時人間エスカレーション**（再 MAGI なし / MAGI 結論を「保留」記録） | AC-W-C-5 補完 |
| `verdict=refuted & severity=critical`（初回） | **再 MAGI 1 ラウンド**（`gabriel.reasoning` を Divergence 入力に追加）→ Step 1 に戻る | AC-W-C-5 |
| `verdict=refuted & severity=critical`（2 回目） | **人間エスカレーション**（再 MAGI 上限到達 / MAGI 結論を「保留」記録） | AC-W-C-7 |
| `verdict=refuted & severity=warning` | MAGI 結論に **gabriel 指摘を併記** + 警告ラベル | AC-W-C-6 |
| `verdict=refuted & severity=info` | **記録のみ** / MAGI 結論不変 | — |
| `verdict=confirmed` | MAGI 結論を確定（gabriel 補強として記録） | — |
| `verdict=inconclusive` | MAGI 結論を確定（inconclusive 注記を添付） | — |
| timeout（> 360 秒 / NFR-W-C-1） | `verdict=inconclusive` として扱う / 再 MAGI なし | NFR-W-C-1 |
| format_error（JSON 欠損 / 型不一致 / NFR-W-C-2） | `verdict=inconclusive` として扱う / 再 MAGI なし | NFR-W-C-2 |

**再 MAGI カウンター**: 1 ラウンド上限（AC-W-C-7）。2 回目の critical refute で自動的に人間エスカレーション。カウンターは MAGI ログセッション単位で管理する。

**実装参照**: verdict 別分岐の Python 実装 SSOT は `.claude/scripts/magi_dispatch.py` (`resolve_action()` + `render_log_entry()`) を参照。テストは `.claude/tests/wave_c/test_wave_c_magi_integration.py` で全 8 パターンを網羅。

### Step 4.2: opt-out 経路

以下 2 条件を **すべて** 満たす場合のみ gabriel probe をスキップできる:

1. opt-out 理由を MAGI ログに 1 文以上記録すること
2. **ユーザー（L1 統括）** がスキップを明示すること

**AUTONOMOUS フェーズでの自律ループ実行者の opt-out 宣言は却下される**（ADR-0005 FR-9.1 統治への自己書込禁止の趣旨に従う / design.md §6.1）。試行された場合は MAGI ログに「opt-out 試行 / 却下」を記録し、通常通り gabriel probe を実施する。

**opt-out 記録形式**:
```markdown
### gabriel opt-out

- 理由: [opt-out の理由を 1 文以上記述]
- opt-out 宣言者: [ユーザー / L1 統括]
- 記録日時: YYYY-MM-DD
```

**正当理由の例**:
- 時間的緊急性（締め切り前の軽微な仕様確認等）
- gabriel 判定に必要な情報が揮発的で正確な判定が期待できない場合
- ユーザーがリスクを承知の上で速度優先を選択する場合

### Step 5: AoT Synthesis（統合 / AoT 適用モードのみ）

各 Atom の結論 + gabriel probe 結果を統合し、最終決定と Action Items を導出する。

```markdown
### AoT Synthesis

**統合結論**: [CASPAR の Convergence 結論を記述]

**gabriel probe 結果**:
- verdict: [confirmed / refuted / inconclusive]
- severity: [critical / warning / info]
- confidence: [0.0-1.0]
- affected_atoms: [Atom 識別子リスト]
- reasoning: [gabriel の判定理由]
- recommended_action: [proceed / re-magi / abort]

**最終結論**:
[gabriel 結果を反映した後の最終結論。warning/info の場合は CASPAR 結論に指摘を併記]

**Action Items**:
1. ...
2. ...
```

## §4.1 軽量モード（非 AoT）でのステップ体系

AoT 適用条件を満たさない軽量 MAGI では以下のステップ体系となる:

- Step 0（AoT Decomposition）: **存在しない**
- Step 1（Divergence）: 実施
- Step 2（Debate）: 実施
- Step 3（Convergence）: CASPAR 結論で完結（直接結論確定）
- Step 4（gabriel probe）: **起動しない**（FR-W-C-3 MUST NOT）
- Step 5（AoT Synthesis）: 存在しない

MAGI ログ記録時は「MAGI 軽量モード」と明示し、Step 番号体系の混乱を避ける。

## verdict 別ログテンプレート

> **共通注記**: JSON 出力時は §Step 4 の required フィールド 6 件（verdict / severity / affected_atoms / reasoning / recommended_action / confidence）を必ず出力する。以下のログ表示形式は代表フィールドのみを示している。

**confirmed**:
```markdown
### gabriel probe

- verdict: confirmed
- confidence: X.XX
- reasoning: [gabriel の判定理由]
- 処理: MAGI 結論を確定（gabriel 補強として記録）
```

**refuted + severity=critical**:
```markdown
### gabriel probe

- verdict: refuted
- severity: critical
- affected_atoms: [A1, A2]
- reasoning: [gabriel の判定理由]
- 処理: MAGI 結論を破棄し、再 MAGI 1 ラウンドを指示する（初回のみ / 上限 1 回）

> [CRITICAL by gabriel]: [reasoning の要約]
> MAGI 結論を破棄します。gabriel.reasoning を新入力として再 MAGI を実施してください。
```

**refuted + severity=warning**:
```markdown
### gabriel probe

- verdict: refuted
- severity: warning
- affected_atoms: [A1, A2]
- reasoning: [gabriel の判定理由]
- 処理: 以下の指摘を MAGI 結論に併記して進む

> [WARNING by gabriel]: [reasoning の要約]
> 最終判断はユーザー（L1 統括）に委ねます。
```

**refuted + severity=info**:
```markdown
### gabriel probe

- verdict: refuted
- severity: info
- affected_atoms: [A1]
- reasoning: [gabriel の判定理由]
- 処理: 以下の指摘を記録するのみ。MAGI 結論は変更しない

> [INFO by gabriel]: [reasoning の要約]
> 指摘を記録するのみ、結論は変更されない。
```

**inconclusive**:
```markdown
### gabriel probe

- verdict: inconclusive
- confidence: X.XX
- reasoning: [gabriel の判定理由]
- 処理: MAGI 結論を確定（inconclusive 注記を添付）

> [NOTE]: gabriel は確信をもって判定できませんでした（confidence=X.XX）。
> 結論は CASPAR の判断を維持します。
```

**abort**（verdict / severity 問わず）:
```markdown
### gabriel probe

- verdict: [任意]
- severity: [任意]
- recommended_action: abort
- reasoning: [abort 判定理由 / なぜ直ちに人間判断が必須か]
- 処理: MAGI 結論を保留し、人間エスカレーションを直ちに行う（再 MAGI なし）

> [ABORT by gabriel]: 即時人間判断必須。
> MAGI 結論を「保留」として記録し、人間（L1 統括）の対応を待ちます。
```

**timeout**（> 360 秒 / NFR-W-C-1）:
```markdown
### gabriel probe

- verdict: inconclusive
- (timeout 注記)
- 処理: タイムアウトにより inconclusive として扱う。MAGI 結論を確定。

> [NOTE]: gabriel がタイムアウト（> 360 秒）しました。inconclusive として処理します。
> 結論は CASPAR の判断を維持します。再 MAGI は実施しません。
```

**format_error**（JSON 必須フィールド欠損 / 型不一致 / NFR-W-C-2）:
```markdown
### gabriel probe

- verdict: inconclusive
- (format_error 注記)
- 処理: フォーマット不備により inconclusive として扱う。MAGI 結論を確定。

> [NOTE]: gabriel の出力にフォーマット不備（必須フィールド欠損 / 型不一致）が検出されました。
> inconclusive として処理します。結論は CASPAR の判断を維持します。再 MAGI は実施しません。
```

## アンカーファイル

思考過程を必ず `docs/artifacts/YYYY-MM-DD-magi-{用途}.md` に書き出す。
フォーマットは `references/anchor-format.md` を参照。

- 書き込み権限: CASPAR のみ（Single-Writer）
- 読み取り権限: 全 MAGI + gabriel（Multi-Reader）
- 削除: ユーザーのみ可能

## 参照

- SSOT: `docs/internal/06_DECISION_MAKING.md`（Reflection セクションは Wave C の後続 Stage 4 で gabriel probe 記述に置換予定）
- Wave C 統合仕様: `docs/specs/magi-v2-gabriel/{requirements,design}.md` v0.4.0
- ADR-0007: `docs/adr/0007-magi-v2-gabriel-integration.md`（gabriel 統合根拠 / Accepted 2026-07-02）
- ADR-0005: `docs/adr/0005-thin-harness-autonomous-governance.md`（Reflection 追補 / FR-9.1 opt-out 権限境界の根拠）
- gabriel subagent: `.claude/agents/gabriel.md`（Wave C Stage 2 実装済 / 2026-07-04 commit `6880421`）
- verdict 別分岐 Python SSOT: `.claude/scripts/magi_dispatch.py` (Wave C Stage 3 T6 / 2026-07-05 実装)
- 統合テスト: `.claude/tests/wave_c/test_wave_c_magi_integration.py` (T6 / 全 8 verdict パターン)
- アンカーフォーマット: `.claude/skills/magi/references/anchor-format.md`
- decision-making ルール: `.claude/rules/decision-making.md`（Step 4 は Wave C 後続 Stage 4 で gabriel probe 記述に置換予定）
