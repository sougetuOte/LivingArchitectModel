# ADR-0007: MAGI v2 — gabriel Adversarial Verifier Integration

## メタ情報

| 項目 | 内容 |
|------|------|
| ステータス | **Proposed**（2026-06-29 起草） |
| 日付 | 2026-06-29 |
| 意思決定者 | sougetuOte（最終承認）/ Living Architect（起草・合議） |
| 関連 ADR | [ADR-0005](./0005-thin-harness-autonomous-governance.md)（ハーネス減量・Reflection 追補 / gabriel 設計根拠の発端）, [ADR-0006](./0006-loop-engineering-vocabulary-and-lam-alignment.md)（Loop Engineering 語彙 / verifier 分離 ↔ gabriel 対応）（両者とも Proposed / 万が一 Rejected 化された場合は本 ADR の Glossary 整合性を再評価する） |
| 関連仕様 | `docs/specs/magi-v2-gabriel/requirements.md` v0.4.0, `docs/specs/magi-v2-gabriel/design.md` v0.4.0 |
| 関連資産 | `docs/specs/v5-fat-reduction/future-candidates.md` FC-1, `.claude/skills/magi/SKILL.md`, `docs/internal/06_DECISION_MAKING.md`, `.claude/agent-memory/quality-auditor/magi-reflection-audit-2026-06-19.md` |

---

## コンテキスト

### 背景: Reflection 変更率 0% の実機計測

B-4 監査（2026-06-19）にて MAGI Reflection（Step 4）を全適用事例で調査した結果、
以下の実機データが得られた（詳細: `.claude/agent-memory/quality-auditor/magi-reflection-audit-2026-06-19.md`）。

- 全 MAGI 適用 9 件のうち Reflection 記録は 7 件
- 全 7 件が「致命的な見落とし: なし → 結論確定」テンプレ出力
- **結論変更率 0%**

この根本原因は **Step 3（CASPAR 収束）直後の同一文脈再処理** にある。
Reflection は CASPAR が結論を下したセッションと同一のコンテキスト内で実施されるため、
新たな視点が入力されず構造的に結論が変わらない。

### 唯一の有効事例: ADR-0005 Reflection 追補

ADR-0005（2026-05-29）の Reflection 追補は、MAGI Reflection 本体ではなく、
**別セッションでの Dynamic Workflows ブラインド検証**（独立文脈での adversarial 検証）が
3 件の catch を発見し FR-9.1/9.2/9.3 に格上げした事例である。

この実証から「**独立文脈での敵対的検証が MAGI の盲点を補完できる**」という設計根拠が確立され、
`docs/specs/v5-fat-reduction/future-candidates.md` FC-1 として
gabriel adversarial verifier の統合方針が PM 決定（2026-06-19）された。

### 問題

1. **Reflection の形骸化**: 同一文脈再処理では入力が変わらないため結論も変わらず、安全網として機能しない
2. **CASPAR の二重負荷**: 現行 Reflection では CASPAR が収束と検証の両責務を負い、純粋な調停者として機能していない
3. **独立検証の欠如**: MELCHIOR / BALTHASAR / CASPAR はいずれも同一セッション内に存在し、外部視点からの異議申し立てが不可能な構造になっている

### 制約条件

- AoT（Atom of Thought）フレームワークは実績があり温存する（MUST NOT 物理削除）
- 既存 3 ペルソナ（MELCHIOR / BALTHASAR / CASPAR）の役割定義は変更しない
- gabriel の常時起動はコスト過剰のため、AoT 適用時のみ自動起動する
- 無限ループ対策として再 MAGI は最大 1 回に制限する
- 権限等級: PM 級（アーキテクチャ変更・ADR 新設）

---

## 検討した選択肢

### 案 1: 却下 — Dynamic Workflows 別セッションでの adversarial 検証

**概要**: ADR-0005 Reflection 追補と同様に、Dynamic Workflows で別セッションを起動し
独立文脈での検証を行う。

**採用候補としての魅力**:
- ADR-0005 追補での実証事例あり（3 catch 発見）
- 完全な文脈独立性

**却下理由**:
- Dynamic Workflows は $100 Max では token 消費が桁違いであり、
  毎回の MAGI 適用に組み込むコスト（約 7 倍）が現実的でない（ADR-0005 RQ-5 での core 見送り方針と整合）
- セッション管理の複雑化（worktree / セッション状態の引き渡し）が常駐利用を困難にする

### 案 2: 却下 — 同一セッション内に別 system prompt を持つシミュレーション

**概要**: gabriel のペルソナを MAGI スキル内にインラインで追加し、
別の system prompt としてシミュレートする。

**却下理由**:
- 同一セッション内での実施はコンテキスト染み込みリスクがある。
  Convergence 後の結論が既に文脈に存在するため、gabriel シミュレーションが
  その結論に引きずられ独立性が失われる。
- 現行 Reflection と同じ「同一文脈再処理」の問題を再現するに過ぎない。

### 案 3: 却下 — 全 MAGI 適用で常時 gabriel 起動

**概要**: AoT 適用条件に関わらず、すべての MAGI 合議で gabriel を自動起動する。

**却下理由**:
- AoT 不要レベルの軽量決定にも Sonnet 起動コストが発生し、過剰投資となる。
- 軽量決定は CASPAR の Convergence で十分であり、adversarial probe の費用対効果が低い。

### 案 4: 却下 — Reflection 二段構え温存（既存 Reflection + gabriel 追加）

**概要**: 既存の Reflection（Step 4）を残した上で gabriel probe を追加し、二段構えの検証とする。

**却下理由**:
- 変更率 0% の実機データが示す通り、現行 Reflection は有効な安全網として機能していない。
  残すことで「機能している」という誤った印象を与えるリスクがある。
- 冗長な 2 ステップが認知負荷を高め、MAGI フロー全体を重くする。
- ADR-0005 Reflection 追補の知見は「同一文脈再処理は無効、独立文脈が有効」であり、
  無効なステップを温存する理由がない。

### 案 5: 採用 — `.claude/agents/gabriel.md` 独立 subagent として実装し、AoT 適用時に Convergence 後へ挿入

**概要**: gabriel を既存 spec-critic / goal-driven-grader と同形式の独立 subagent として実装し、
AoT 適用 MAGI の Step 3（Convergence）直後に adversarial probe として自動起動する。
Reflection（Step 4）はこれに代替される（物理削除は BUILDING フェーズ実施）。

**採用理由**:
- 独立 subagent として起動することで、MAGI 合議の文脈とは異なるコンテキストで検証が行われ、
  真の独立性が確保される。これは ADR-0005 追補の DW ブラインド検証と同等の構造的効果を持つ。
- spec-critic / goal-driven-grader と同形式であり、既存エコシステムに馴染む実装コストが低い。
- AoT 適用時のみ起動することでコストを抑制しつつ、複雑決定に限定した効果的な安全網を形成する。
- CASPAR を Convergence に専念させることで「純調停者」化が実現し、役割の明確化が進む。

---

## 決定

**採用: 案 5 — gabriel 独立 subagent として AoT 適用 MAGI の Convergence 後に挿入**

以下の 4 点を決定事項とする。

### D-1: gabriel 実装基盤

- 実装形態: `.claude/agents/gabriel.md` 独立 subagent（既存 spec-critic / goal-driven-grader と同形式）
- デフォルトモデル: **Sonnet**（rubric 突合 + 自由理由生成の両方が必要 / Haiku では自由理由生成の深さが不足する懸念）
- 出力契約: ハイブリッド形式（判定 JSON + 自由理由テキスト）
  - 必須フィールド: `verdict`（confirmed / refuted / inconclusive）、`severity`（critical / warning / info）、
    `affected_atoms[]`（影響を受ける AoT Atom の識別子リスト）、`reasoning`（自由文）、
    `recommended_action`（proceed / re-magi / abort）、`confidence`（0.0–1.0）

### D-2: MAGI 構造再定義

- 既存 3 ペルソナ（MELCHIOR / BALTHASAR / CASPAR）の役割定義は変更しない
- **Step 4 Reflection を廃止**し、Convergence（Step 3）直後に gabriel adversarial probe を挿入する
- AoT 不要レベルの軽量決定（適用条件に満たないケース）では gabriel スキップ（元々 safety net 不要）
- CASPAR は Convergence（Step 3）で完結し、検証の再処理責任を負わない（「純調停者化」）

### D-3: トリガー条件と失敗時挙動

**トリガー**: AoT 適用時のみ自動起動 / 明示的 opt-out 可（記録の上スキップ）

**失敗時挙動（3 段階）**:

| gabriel 結果 | 挙動 |
|---|---|
| `verdict=refuted` & `severity=critical` | 結論破棄 + 再 MAGI 1 ラウンド指示（上限 1 回 / 超過時は人間エスカレーション） |
| `verdict=refuted` & `severity=warning` | 結論にgabriel 指摘を併記 + 警告添付して進む（最終判断は人間委ね）|
| `verdict=refuted` & `severity=info` | 記録のみ（結論不変）|
| `verdict=confirmed` | 結論確定（gabriel による補強として記録）|
| `verdict=inconclusive` | 結論確定 + inconclusive 注記を添付 |
| `recommended_action=abort`（verdict / severity 問わず） | MAGI 結論を保留し、人間エスカレーションを直ちに行う。再 MAGI を経由しない |

**無限ループ対策**: 再 MAGI は最大 1 回。2 回目も `severity=critical` の refute が返された場合は
「人間エスカレーション必須」として結論を保留する。

### D-4: Loop Engineering 整合

- Loop Engineering（ADR-0006 Glossary）における `verifier / evaluator gate` の LAM 実装が gabriel である
- ADR-0006 Glossary の「Reflection を gabriel に統合予定（②）」記述と整合する（Glossary 更新は BUILDING で実施）
- gabriel を `adversarial verifier` として LAM 固有名称とする

---

## 影響

### ポジティブな影響

- Reflection の形骸化（変更率 0%）が解消され、MAGI の adversarial 検証が実効化される
- CASPAR が純調停者として機能し、合議の責務分離が明確化される
- spec-critic / goal-driven-grader と同形式の実装で、エコシステムの一貫性が保たれる
- ADR-0005 追補の「独立文脈検証が有効」という知見が構造として組み込まれる

### ネガティブな影響

- AoT 適用 MAGI ごとに Sonnet 起動が追加されるため、レート消費が増加する
  （緩和策: AoT 非適用ケースではスキップ / 起動頻度の実測を BUILDING 後 retro で評価）
- gabriel 自身が暴走（全 refute）する可能性がある
  （緩和策: rubric ベース判定 + `confidence` フィールド + 明確根拠の要件定義 / requirements NFR-W-C-3 参照）
- gabriel が形骸化（全 confirmed）する可能性がある
  （緩和策: refute 率 / inconclusive 率の監視メトリクスを NFR として定義 / requirements NFR-W-C-4 参照）

### 影響を受けるコンポーネント（BUILDING フェーズで実施）

| コンポーネント | 変更内容 | 権限等級 |
|---|---|---|
| `.claude/agents/gabriel.md` | 新規作成 | PM 級 |
| `.claude/skills/magi/SKILL.md` | Step 4 Reflection 廃止 + gabriel probe 手順追記 | PM 級 |
| `docs/internal/06_DECISION_MAKING.md` | Section 6 Reflection 廃止 + gabriel 統合の記述更新 | PM 級 |
| `.claude/rules/decision-making.md` | Step 4 Reflection → gabriel probe への記述更新 | PM 級 |
| `docs/adr/0006-loop-engineering-vocabulary-and-lam-alignment.md` | Glossary に gabriel 追加 | PM 級 |

---

## 参考資料

- `docs/specs/v5-fat-reduction/future-candidates.md` FC-1（gabriel 統合 PM 決定・2026-06-19）
- `docs/adr/0005-thin-harness-autonomous-governance.md` Reflection 追補（DW ブラインド検証 3 catch / gabriel 設計根拠の発端）
- `docs/adr/0006-loop-engineering-vocabulary-and-lam-alignment.md` Glossary（Loop Eng verifier ↔ gabriel）
- `.claude/agent-memory/quality-auditor/magi-reflection-audit-2026-06-19.md`（Reflection 変更率 0% 実機計測）
- 本 Wave MAGI 合議（4 Atom / 2026-06-29 / 既決事項として起票プロンプトに記録）
- `docs/specs/magi-v2-gabriel/requirements.md` v0.1.0 → v0.2.0
- `docs/specs/magi-v2-gabriel/design.md` v0.1.0 → v0.2.0

---

## 改訂履歴

| 日付 | 変更者 | 変更内容 |
|:-----|:------|:--------|
| 2026-06-29 | design-architect | 初版起草（Wave C / 骨子 ② PLANNING） |
| 2026-06-29 | design-architect | R1 修正適用: 関連 ADR 行に ADR-0005/0006 Proposed 状態・Rejected 時の再評価義務を注記。関連仕様を v0.2.0 参照に更新（ステータス Proposed のまま） |
| 2026-06-29 | design-architect | R2 機械更新: 関連仕様を v0.3.0 参照に更新（ステータス Proposed のまま）|
| 2026-06-29 | design-architect | R3 修正: D-3 テーブルに `recommended_action=abort` 行追加 / 関連仕様を v0.4.0 参照に更新（ステータス Proposed のまま）|
