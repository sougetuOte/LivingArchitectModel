# MAGI v2 SSOT 改訂案（Wave C Stage 4 T7/T8/T9）

- 作成日: 2026-07-05
- 作成者: L1 (Opus 4.7)
- ステータス: **draft / L1 review 済 / PM 承認待ち**
- 対象ファイル:
  - **T7**: `docs/internal/06_DECISION_MAKING.md`（238 行 → §5.4/§6 セクション改訂 / 全面書換ではなく差分）
  - **T8**: `.claude/rules/decision-making.md`（63 行 → §Execution Flow / §AoT ワークフロー / §Output Format 差分）
  - **T9**: `docs/adr/0006-loop-engineering-vocabulary-and-lam-alignment.md`（Glossary 1 行更新）
- 根拠文書:
  - `docs/specs/magi-v2-gabriel/requirements.md` v0.4.0（Approved）
  - `docs/specs/magi-v2-gabriel/design.md` v0.4.0（Approved）
  - `docs/adr/0007-magi-v2-gabriel-integration.md`（Accepted 2026-07-02）
  - `.claude/skills/magi/SKILL.md`（Stage 3 T5 適用済 / commit `e3887d1`）
- 関連タスク: `docs/specs/magi-v2-gabriel/tasks.md` §6 WC-B5-T7 / T8 / T9

---

## §1 改訂サマリ（3 件統合）

| 対象 | 種別 | 内容 |
|:-----|:-----|:-----|
| **T7** `06_DECISION_MAKING.md` §5.4 | 差分 | Step 4 Reflection → Step 4 gabriel probe（AoT 適用時のみ）に置換 |
| **T7** `06_DECISION_MAKING.md` §5.5 | 差分 | 出力フォーマットの Reflection セクションを gabriel probe セクションに置換 |
| **T7** `06_DECISION_MAKING.md` §6 | 全面書換 | 「§6 Reflection」を「§6 gabriel Adversarial Probe（旧 Reflection）」に置換 + Step 番号体系 (0-5) 説明 + 軽量モード注記 + NFR-W-C-6 AoT 温存明示 |
| **T8** `.claude/rules/decision-making.md` §Execution Flow | 差分 | Reflection 行を gabriel probe (AoT 適用時のみ) に置換 |
| **T8** `.claude/rules/decision-making.md` §AoT ワークフロー | 差分 | Reflection → gabriel probe |
| **T8** `.claude/rules/decision-making.md` §Output Format | 差分 | Reflection セクションを gabriel probe セクションに置換 |
| **T9** `ADR-0006` Glossary | 1 行更新 | `Reflection を gabriel に統合予定（②）` → `MAGI v2 で gabriel adversarial probe を verifier として統合済 (Wave C / 2026-07-05 / ADR-0007)` |

## §2 依存関係 + 整合性

本改訂は Wave C の他タスク完了物との整合を保つ:

- **Stage 3 完了物**: `SKILL.md` / `magi_dispatch.py` / test suite（26+21 テスト全 PASS）
- **Stage 5 完了物**: `test_wave_c_e2e_integration.py` (SkillMdConsistency drift ガード 5 件で SSOT 一貫性を検証)
- **本 T7/T8 適用後**: `test_wave_c_e2e_integration.py::TestAoTFrameworkPreservation` 3 件が Wave C の SSOT 3 系統（SKILL.md / 06_DECISION_MAKING.md / decision-making.md）の一貫性を保証
- **T9 Glossary 更新後**: ADR-0006 が Wave C 完了状態を正しく記録

## §3 破壊的変更の有無

- **後方互換**: 軽量モード (非 AoT) のフローは Step 1-3 で完結（Reflection なし / gabriel なし）→ 従来運用に影響なし
- **AoT 適用時**: Step 4 が Reflection → gabriel probe に置換 / CASPAR の Step 3 完結性は保たれる
- **AoT フレームワーク**: §5.1-5.3 (Atom 定義 / 適用判断 / 適用条件) は無改変（NFR-W-C-6 MUST NOT）
- **既存 anchor ファイル**: 過去の Reflection 記録は追跡目的で保持（削除しない）/ 今後の anchor は gabriel probe 形式に移行

## §4 検証観点（L1 review 済）

- ✅ AoT 温存 (NFR-W-C-6): §5.1-5.3 変更なし / §5.4 のみ Step 4 差分 / SKILL.md との整合
- ✅ 軽量モード注記: 3 ファイル全てで「軽量モードでは gabriel を起動しない」明示
- ✅ 用語一貫性: SKILL.md / 06_DECISION_MAKING.md / decision-making.md で「gabriel adversarial probe」/「§Step 4.1 verdict 別分岐」の呼称統一
- ✅ 参照リンク: 3 ファイル全てで ADR-0007 / gabriel subagent / magi_dispatch.py 相互参照
- ✅ ADR-0006 Glossary 一貫性: T9 更新後、行 81 が Wave C 完了状態を反映

---

## §5 T7: `docs/internal/06_DECISION_MAKING.md` 差分（適用対象）

### §5.4 AoT + MAGI ワークフロー（差分 / 行 123-149）

**現行**:
```
┌─────────────────────────────────────────────────────────┐
│ Step 4: Reflection（振り返り — 1回限り）                │
│   全員で結論を検証。致命的な見落としがあれば修正。      │
│   なければ確定。                                        │
└─────────────────────────────────────────────────────────┘
```

**改訂後**:
```
┌─────────────────────────────────────────────────────────┐
│ Step 4: gabriel Adversarial Probe（AoT 適用時のみ）     │
│   独立コンテキストで動作する gabriel subagent が        │
│   CASPAR の結論を外部視点から adversarial verification  │
│   軽量モード (非 AoT) では起動しない (FR-W-C-3 MUST NOT)│
│   詳細: §6 / .claude/skills/magi/SKILL.md §Step 4       │
└─────────────────────────────────────────────────────────┘
```

### §5.5 出力フォーマット（差分 / 行 187-193）

**現行**:
```
### Reflection

致命的な見落とし: なし → 結論確定
（or: 致命的な見落とし: [内容] → 結論修正: [修正内容]）
```

**改訂後**:
```
### gabriel probe（AoT 適用時のみ / 軽量モードでは省略）

- verdict: [confirmed / refuted / inconclusive]
- severity: [critical / warning / info]
- confidence: [0.0-1.0]
- affected_atoms: [Atom 識別子リスト]
- reasoning: [gabriel の判定理由]
- recommended_action: [proceed / re-magi / abort]
- 処理: verdict に応じて Step 5 へ / 詳細分岐は SKILL.md §Step 4.1
```

### §6 全面書換（行 204-238 全体を置換）

**改訂後（全文）**:

```markdown
## 6. gabriel Adversarial Probe（AoT 適用時のみ / 旧 Reflection）

MAGI Debate（Step 1-3）で CASPAR が結論を下した後、**AoT 適用モード** では独立コンテキストで動作する **gabriel subagent** が adversarial verification を実施する。

### 6.1. 背景 — Reflection からの置換

B-4 監査（2026-06-19）実機計測: 旧 Reflection の初回変更率 0%（全 7 件「致命的な見落とし: なし → 結論確定」）で「無効な安全網」であったことが判明した。根本原因は Step 3（CASPAR）直後の同一文脈再処理による入力同一問題。Wave C（骨子 ②）で構造的解決として、独立 subagent による adversarial probe に置換した（ADR-0007 Accepted 2026-07-02）。

### 6.2. Step 番号体系

- **AoT 適用モード**: Step 0（AoT Decomposition）→ Step 1（Divergence）→ Step 2（Debate）→ Step 3（Convergence / CASPAR 完結）→ **Step 4（gabriel probe）** → Step 5（AoT Synthesis）
- **軽量モード（非 AoT）**: Step 1（Divergence）→ Step 2（Debate）→ Step 3（Convergence / 直接結論確定）/ **Step 4-5 は存在しない**

軽量モードで gabriel は起動しない（FR-W-C-3 MUST NOT）。MAGI ログ冒頭で必ずモード（AoT または 軽量）を宣言する。

### 6.3. AoT フレームワークの温存

本改訂で AoT Decomposition（§5.1-5.3 の Atom 定義・適用判断・適用条件）は **無改変** で保存される（NFR-W-C-6 MUST NOT）。gabriel は AoT Synthesis の結論を入力として受け取る位置に挿入されるのみで、AoT 自体には手を加えない。

### 6.4. gabriel の役割

CASPAR の統合結論を **そのまま正としてではなく**、結論に至った前提・根拠・棄却された代替案を独立に再検証する（FR-W-C-1）。

**プローブ観点（rubric 5 観点）**:

1. **論理的一貫性**: 各 Atom の結論に矛盾がないか
2. **仕様整合**: CASPAR の結論が既存仕様（`docs/specs/` / `docs/internal/`）と矛盾しないか
3. **リスク見落とし**: MELCHIOR / BALTHASAR が検討していない重大なリスクの有無
4. **前提検証**: AoT Decomposition の Atom 依存関係が結論に反映されているか
5. **境界条件**: 結論が適用できないエッジケース（スコープ外・例外）が未記録ではないか

### 6.5. gabriel 出力契約

6 フィールド JSON（design.md §3 詳細）:

- `verdict`: `confirmed` / `refuted` / `inconclusive`
- `severity`: `critical` / `warning` / `info`
- `affected_atoms`: Atom 識別子リスト（`verdict=refuted` 時は非空必須）
- `reasoning`: 判定理由（200-1000 字）
- `recommended_action`: `proceed` / `re-magi` / `abort`
- `confidence`: 0.0-1.0（0.3 未満は `verdict=inconclusive` 強制）

### 6.6. 失敗時挙動（3 段階 + 追加）

- **critical (初回)**: 再 MAGI 1 ラウンド（gabriel.reasoning を Divergence 入力に追加）
- **critical (2 回目)**: 人間 escalation（AC-W-C-7 / 上限 1 回）
- **warning**: MAGI 結論に指摘併記 + 警告ラベル
- **info**: 記録のみ / MAGI 結論不変
- **abort** (recommended_action=abort): 即時人間 escalation（verdict/severity 問わず）
- **inconclusive / timeout / format_error**: MAGI 結論を確定（inconclusive 注記添付）

分岐優先順位（MUST）: **abort > critical > warning > info > confirmed > inconclusive**

### 6.7. 実装 SSOT + テスト

- **実装 SSOT**: `.claude/scripts/magi_dispatch.py`（`resolve_action()` + `render_log_entry()` + `should_run_gabriel()` + `OptOutRecord` + `GateDecision`）
- **統合テスト**: `.claude/tests/wave_c/test_wave_c_magi_integration.py` (26 件) + `test_wave_c_e2e_integration.py` (21 件) + `test_wave_c_gabriel_output.py` (16 件)
- **月次メトリクス**: `docs/artifacts/gabriel-metrics-environment-2026-07-05.md`（JSONL 12 フィールド）

### 6.8. opt-out 経路

以下 2 条件を **すべて** 満たす場合のみスキップ可能:

1. opt-out 理由を MAGI ログに 1 文以上記録
2. **ユーザー（L1 統括）** がスキップを明示

**AUTONOMOUS フェーズでの自律ループ実行者の opt-out は却下**（ADR-0005 FR-9.1 統治への自己書込禁止）。試行された場合は MAGI ログに「opt-out 試行 / 却下」を記録し、通常通り gabriel probe を実施する。

### 6.9. 参照

- `.claude/skills/magi/SKILL.md`（skill 定義 / L1 宣言的仕様）
- `docs/specs/magi-v2-gabriel/{requirements,design}.md` v0.4.0
- `docs/adr/0007-magi-v2-gabriel-integration.md`（Accepted 2026-07-02）
- `docs/adr/0005-thin-harness-autonomous-governance.md` FR-9.1（AUTONOMOUS ガード）
- `.claude/agents/gabriel.md`（subagent 実装 / commit `6880421`）
```

---

## §6 T8: `.claude/rules/decision-making.md` 差分（適用対象）

### §Execution Flow（差分 / 行 13-19）

**現行**:
```markdown
1. **Divergence**: MELCHIOR と BALTHASAR が意見を出し尽くす
2. **Debate**: 対立ポイントについて解決策を検討
3. **Convergence**: CASPAR が最終決定を下す
4. **Reflection（新規追加）**: 全員で結論を検証（1回限り）。致命的な見落としがあれば修正
   > [WARNING] B-4 監査（2026-06-19）実機計測: 初回変更率 0% / v5 ② gabriel 統合予定
```

**改訂後**:
```markdown
1. **Divergence**: MELCHIOR と BALTHASAR が意見を出し尽くす
2. **Debate**: 対立ポイントについて解決策を検討
3. **Convergence**: CASPAR が最終決定を下す
4. **gabriel Adversarial Probe（AoT 適用時のみ）**: 独立コンテキストで動作する gabriel subagent が CASPAR 結論を adversarial verification。verdict={confirmed/refuted/inconclusive} + severity + confidence を返す。詳細分岐は `.claude/skills/magi/SKILL.md` §Step 4.1 参照
   > **注記**: 旧 Reflection は Wave C（骨子 ②）で gabriel に置換済（ADR-0007 Accepted 2026-07-02）。B-4 監査（2026-06-19）で Reflection 変更率 0% を実測、独立コンテキストによる adversarial probe への構造的置換で解消
```

### §AoT ワークフロー（差分 / 行 39-41）

**現行**:
```
AoT Decomposition → MAGI Debate (各Atom) → Reflection → AoT Synthesis
```

**改訂後**:
```
AoT Decomposition → MAGI Debate (各Atom) → gabriel probe → AoT Synthesis

（軽量モード / 非 AoT: MAGI Debate のみで完結 / gabriel は起動しない）
```

### §Output Format（差分 / 行 45-62）

**現行**:
```markdown
### Reflection
致命的な見落とし: なし → 結論確定
```

**改訂後**:
```markdown
### gabriel probe（AoT 適用時のみ）
- verdict: confirmed / refuted / inconclusive
- severity: critical / warning / info
- confidence: 0.0-1.0
- reasoning: [判定理由]
- 処理: verdict に応じて AoT Synthesis へ（詳細分岐は SKILL.md §Step 4.1）
```

---

## §7 T9: `docs/adr/0006-loop-engineering-vocabulary-and-lam-alignment.md` 差分（適用対象）

### Glossary 行 81 の 1 行更新

**現行**:
```markdown
| debate among specialists | 3 Agents Model（MAGI） | Reflection を gabriel に統合予定（②） |
```

**改訂後**:
```markdown
| debate among specialists | 3 Agents Model（MAGI） | MAGI v2 で gabriel adversarial probe を verifier として統合済（Wave C / 2026-07-05 / ADR-0007 Accepted） |
```

---

## §8 承認要求

**ユーザー**: 本 draft を review して以下のいずれかで応答してください:

- **Approved as-is**: L1 が T7/T8/T9 を上記 §5/§6/§7 の内容で本体ファイルに順次 Edit 適用
- **修正指示**: 具体的な修正箇所を指示
- **却下**: 現行 3 ファイル維持

## §9 権限等級

本 draft ファイル（`docs/artifacts/`）: SE 級
本 draft を SSOT へ適用（実装）: **PM 級**（3 ファイル全て / ユーザー承認必須）

## §10 参照

- `docs/specs/magi-v2-gabriel/{requirements,design}.md` v0.4.0
- `docs/adr/0007-magi-v2-gabriel-integration.md`（Accepted）
- `docs/adr/0005-thin-harness-autonomous-governance.md` FR-9.1
- `.claude/skills/magi/SKILL.md`（Stage 3 T5 適用済）
- `.claude/scripts/magi_dispatch.py`（Stage 3-5 実装 SSOT）
- `docs/artifacts/gabriel-metrics-environment-2026-07-05.md`（Stage 5 T11）
- `.claude/tests/wave_c/`（Stage 2-5 test suite / 63 テスト）
