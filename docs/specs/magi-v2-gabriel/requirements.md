# 要件定義書: MAGI v2 — gabriel Adversarial Verifier Integration

- バージョン: 0.4.0
- 作成日: 2026-06-29
- ステータス: Draft（PM 承認待ち）
- 対応フェーズ: PLANNING（requirements）
- 関連 Milestone: B-5（Wave C / 骨子 ②）
- 起草者: design-architect subagent
- 関連 ADR: `docs/adr/0007-magi-v2-gabriel-integration.md`（意思決定根拠）

---

## §1 Problem Statement

### 背景

LAM の MAGI System（`docs/internal/06_DECISION_MAKING.md`）は
AoT Decomposition + 3 ペルソナ合議（MELCHIOR / BALTHASAR / CASPAR）+ Reflection（Step 4）
という 5 ステップ構造で複雑な意思決定を行う。

B-4 監査（2026-06-19）にて Reflection の全適用事例を調査した結果、
変更率 **0%**（7 件中 7 件が「致命的な見落とし: なし → 結論確定」テンプレ出力）が判明した。
根本原因は Step 3（CASPAR 収束）直後の同一文脈再処理にある。
Reflection が MAGI 合議と同一のセッションコンテキスト内で実施されるため、
新たな入力が追加されず構造的に結論が変わらない。

対照的に、ADR-0005 Reflection 追補（2026-05-29）では別セッションの
Dynamic Workflows ブラインド検証（独立文脈での adversarial 検証）が 3 件の catch を発見し、
FR-9.1/9.2/9.3 として格上げされた。この実証が gabriel 統合の設計根拠となる。

### 課題

| 課題 | 現状 | 影響 |
|:-----|:-----|:-----|
| Reflection の形骸化 | 変更率 0% / 同一文脈再処理で有効性がない | 安全網として機能せず、形式的なコスト消費のみ発生する |
| CASPAR の二重負荷 | 収束（Step 3）と検証（Step 4）の両責務を CASPAR が担う | 純粋な調停者として機能できず、役割が不明確 |
| 独立検証の欠如 | 3 ペルソナすべてが同一セッション内に存在する | 外部視点からの異議申し立てが構造的に不可能 |

### 期待効果

- MAGI adversarial 検証の実効化（変更率 0% の解消）
- CASPAR の純調停者化（役割の明確化）
- Loop Engineering の verifier 分離（ADR-0006 Glossary 整合）の LAM 実装

---

## §2 Goals / Non-Goals

### Goals

| Goal | 指標 | 達成判定 |
|:-----|:-----|:--------|
| G1: gabriel 独立 subagent の実装 | `.claude/agents/gabriel.md` が存在し、MAGI フローから呼び出せる | BUILDING 完了後に `gabriel.md` が存在し、仕様通りの JSON 出力が得られる |
| G2: Reflection 廃止と gabriel probe への代替 | MAGI Step 4 Reflection が gabriel probe に代替される | **BUILDING 完了後に**、`SKILL.md` / `06_DECISION_MAKING.md` / `decision-making.md` から Reflection（Step 4）が削除または代替済みであることが確認できる |
| G3: 失敗時挙動の 3 段階制御の実装 | severity（critical / warning / info）に応じた挙動が MAGI フローで機能する | 各 severity 別の動作が受入テストで確認できる |
| G4: AoT 適用時のみのトリガー制御 | AoT 適用 MAGI では gabriel が自動起動し、非 AoT MAGI ではスキップされる | トリガー条件の計測可能な AC を満たす（AC-W-C-4 参照）|
| G5: 監視メトリクスの定義 | gabriel の refute 率 / inconclusive 率を追跡する手順が存在する | NFR-W-C-4 を満たすメトリクス記録手順が MAGI 合議ログに組み込まれる |

### Non-Goals（明示的に本 Wave で対応しないこと）

- **MAGI SKILL.md / decision-making.md / 06_DECISION_MAKING.md の実際の改訂**（BUILDING フェーズで実施）
- **ADR-0006 Glossary への gabriel 追記**（BUILDING フェーズで実施）
- **gabriel の tasks.md 起草**（次 Wave で起草）
- **AoT 適用判定の自動化（hooks 等）**: AoT 適用判定自体の形骸化防止を hooks で自動検出する機構は将来 Wave の OQ として記録（OQ-W-C-3 参照）
- **Dynamic Workflows / Agent Teams を core 依存として採用すること**（ADR-0005 RQ-5 方針に従い future-candidates）
- **gabriel の POO（骨子 ⑥）との統合設計**: POO との統合は POO v2 以降の別 ADR で扱う

---

## §3 機能要件（RFC 2119）

ID 体系: `FR-W-C-N`（Wave: C = 骨子 ②、N = 連番）

---

### FR-W-C-1: gabriel subagent の実装（MUST）

`.claude/agents/gabriel.md` を新規作成しなければならない（MUST）。
gabriel は既存 spec-critic / goal-driven-grader と同一の subagent 形式とする。

- デフォルトモデル: Sonnet（rubric 突合 + 自由理由生成の両方に対応可能なモデル）
- 入力契約: MAGI 合議の AoT Synthesis 結論全体（Atom 別結論 + 統合結論）を受け取ること
- 出力契約: FR-W-C-2 で定義する JSON フォーマットを出力しなければならない（MUST）

---

### FR-W-C-2: gabriel 出力フォーマット（MUST）

gabriel は以下の必須フィールドを持つ JSON オブジェクトを出力しなければならない（MUST）。

| フィールド名 | 型 | 取りうる値 | 説明 |
|:------------|:---|:----------|:-----|
| `verdict` | string | `confirmed` / `refuted` / `inconclusive` | 総合判定 |
| `severity` | string | `critical` / `warning` / `info` | 問題の深刻度（`verdict=refuted` 時のみ実質的意味を持つ）|
| `affected_atoms` | string[] | Atom 識別子の配列（例: `["A1", "A3"]`）| 問題が検出された AoT Atom の識別子リスト |
| `reasoning` | string | 自由テキスト（200 字以上 1000 字以内）| 判定理由の詳細（明確な根拠を記述すること）|
| `recommended_action` | string | `proceed` / `re-magi` / `abort` | MAGI フローへの推奨アクション。`abort` は gabriel が verdict / severity 問わず「即時人間判断必須」と判定した場合に独立して返す値。`re-magi` とは独立した経路となる |
| `confidence` | number | 0.0 以上 1.0 以下 | gabriel 自身の判定確信度。プロンプト指示で 0.05 刻みを推奨するが、検証は型・範囲のみ |

`reasoning` フィールドは「なぜ refuted/confirmed/inconclusive と判定したか」を
具体的な根拠（仕様参照 / ロジック指摘 / リスク特定）とともに記述しなければならない（MUST）。
「判定できない」のみを `reasoning` に記述することは禁止とする（MUST NOT）。

**クロスフィールド制約 (MUST)**:

以下のクロスフィールド制約は requirements が WHAT の SSOT として明記する。詳細な JSON schema 表現は design §3 を参照。

- `severity=critical` の場合、`recommended_action` は `re-magi` または `abort` でなければならない（`proceed` 禁止）
- `verdict=confirmed` または `verdict=inconclusive` の場合、`severity` は `info` を設定する
- FR-W-C-6 既定の追加制約: `confidence<0.3` → `verdict=inconclusive` 必須 / `affected_atoms=[]` → `verdict=refuted` 禁止

---

### FR-W-C-3: MAGI フロー変更（MUST）

MAGI フローにおいて、Reflection（Step 4）を廃止し、
AoT 適用 MAGI における Convergence（Step 3）直後に gabriel adversarial probe を挿入しなければならない（MUST）。

変更後のフローは以下の順序とする:

1. Step 0: AoT Decomposition（分解）
2. Step 1: Divergence（発散）
3. Step 2: Debate（議論）
4. Step 3: Convergence（収束 / CASPAR が完結）
5. **Step 4: gabriel adversarial probe**（AoT 適用時のみ）
6. Step 5: AoT Synthesis（統合 / gabriel 結果を反映）

AoT 非適用 MAGI（軽量決定）では gabriel を起動してはならない（MUST NOT）。Convergence（Step 3）後に直接結論を確定する。

---

### FR-W-C-4: トリガー条件（MUST）

gabriel の自動起動トリガーは以下の条件で制御しなければならない（MUST）。

**自動起動条件（すべて満たす場合）**:
- AoT Decomposition が実施された MAGI 合議であること
- 適用判断条件（判断ポイント 2+、影響レイヤー 3+、選択肢 3+）のいずれかを満たしていること

**opt-out 条件（すべて明示した場合のみスキップ可）**:
- **ユーザー（L1 統括）または MAGI フロー実行者**が opt-out 理由を MAGI ログに 1 文以上記録すること（MUST）
- ユーザー（L1 統括）がスキップを明示すること

AoT 適用条件を満たすにもかかわらず gabriel をスキップする場合、
理由の記録なしにスキップすることは禁止とする（MUST NOT）。

自律ループ実行者（AUTONOMOUS フェーズ）の opt-out 宣言は MAGI ログに記録されるが、ADR-0005 FR-9.1（自律エンジンは自身の統治への書込権限を持たない）の趣旨に従い**却下される**（MUST）。詳細な権限境界は design §6.1 を参照。

---

### FR-W-C-5: 失敗時挙動の 3 段階制御（MUST）

gabriel の出力に基づき、MAGI フローは以下の挙動を取らなければならない（MUST）。

| 条件 | 挙動 |
|:-----|:-----|
| `verdict=refuted` かつ `severity=critical` | MAGI 結論を破棄し、再 MAGI を 1 ラウンド指示する。再 MAGI 後も `severity=critical` の refute が返された場合は人間エスカレーション必須として結論を保留する |
| `verdict=refuted` かつ `severity=warning` | MAGI 結論に gabriel 指摘を併記し、警告ラベルを添付して進む（人間（L1 統括）が警告添付された結論を確認し、最終判断を行わなければならない（MUST））|
| `verdict=refuted` かつ `severity=info` | gabriel 指摘を記録し、MAGI 結論は変更しない |
| `verdict=confirmed` | MAGI 結論を確定する（gabriel による補強として記録）|
| `verdict=inconclusive` | MAGI 結論を確定する（inconclusive 注記を添付）|
| `recommended_action=abort`（verdict / severity 問わず） | MAGI 結論を保留し、人間エスカレーションを直ちに行う（再 MAGI を経由しない）|
| フォーマット不備（NFR-W-C-2 / 必須フィールド欠損 / 型不一致） | `verdict=inconclusive` として扱い、MAGI ログに `format_error` 注記を記録。再 MAGI は実施しない |

再 MAGI の上限は 1 回とする（MUST NOT exceed）。
再 MAGI が 1 回を超えて必要と判断される場合は、人間エスカレーションを行わなければならない（MUST）。

---

### FR-W-C-6: gabriel の根拠品質要件（MUST）

gabriel の判定は以下の品質基準を満たさなければならない（MUST）。

- `verdict=refuted` を返す場合、`reasoning` に具体的な問題箇所（Atom ID / ロジック / 仕様参照）を明記すること
- `confidence` が 0.3 未満の場合、`verdict` は `inconclusive` でなければならない（MUST）
  （確信度 30% 未満で refuted/confirmed を断言することは禁止）
- `affected_atoms` が空配列（`[]`）の場合、`verdict` は `refuted` であってはならない（MUST NOT）
  （影響 Atom 不明での refute は禁止）

---

### FR-W-C-7: 再 MAGI 時のコンテキスト初期化（SHOULD）

`verdict=refuted & severity=critical` による再 MAGI を実施する場合、
gabriel の `reasoning` を「新たな入力」として再 MAGI の Divergence ステップに渡すべきである（SHOULD）。
gabriel 指摘を起点にした議論のやり直しで、同一バイアスによる再収束を防ぐことを目的とする。

---

## §4 非機能要件（NFR）

ID 体系: `NFR-W-C-N`

---

### NFR-W-C-1: レスポンス時間（SHOULD）

gabriel の出力（JSON + reasoning）は Sonnet モデルの通常レスポンスタイム内（60 秒以内）に
完了するべきである（SHOULD）。
60 秒を超える場合は timeout として `verdict=inconclusive` と扱う。

タイムアウト検出は MAGI フロー実行者（gabriel 呼び出し元）が担う。LAM の subagent 基盤が
タイムアウト機構を提供しない場合、呼び出し元が経過時間を計測し inconclusive として扱う。

---

### NFR-W-C-2: 出力フォーマット準拠率（MUST）

gabriel は FR-W-C-2 で定義した必須フィールドをすべて含む JSON を出力しなければならない（MUST）。

**MAGI フロー実行者（gabriel 呼び出し元）はフォーマット不備（必須フィールド欠損 / 型不一致）を検出する責任を負う**（MUST）。検出時は `verdict=inconclusive` として扱い、MAGI フローを止めない（NFR-W-C-1 のタイムアウト処理と同じ構造）。

---

### NFR-W-C-3: gabriel 暴走リスクの抑制（MUST）

gabriel が全判定を `refuted` とする暴走を防ぐため、以下の制約を満たさなければならない（MUST）。

- FR-W-C-6 の根拠品質要件（`confidence` 閾値 / `affected_atoms` 必須）を適用することで、
  根拠のない `refuted` を構造的に排除する
- MAGI 合議の結論には CASPAR の決定理由が含まれており、gabriel はその理由と
  明確に対立する証拠なしに `refuted` を返さないようにすべきである（SHOULD NOT）。
  本制約は gabriel の system prompt 品質に依存する設計帰結であり、検証は FR-W-C-6 の
  confidence 閾値 / affected_atoms 必須要件で間接的に担保する

---

### NFR-W-C-4: 監視メトリクス（SHOULD）

MAGI 合議ログに gabriel の判定結果を記録し、以下のメトリクスを追跡するべきである（SHOULD）。

| メトリクス | 記録単位 | 目的 |
|:----------|:--------|:-----|
| gabriel 起動回数 | 合議 1 件ごと | AoT 適用率との比較 |
| `verdict=refuted` 件数・率 | 週次 / 月次 | 形骸化（0% 収束）/ 暴走（100% 収束）の双方を検出 |
| `verdict=inconclusive` 件数・率 | 週次 / 月次 | gabriel の判定能力の評価 |
| `severity=critical` で再 MAGI 実施件数 | 累積 | 無限ループリスクの観測 |
| 再 MAGI 後の結論変更有無 | 累積 | gabriel の実効性評価 |

refute 率が 0% または 100% に収束した場合、形骸化または暴走の証拠として
直近の `/retro` で評価対象とするべきである（SHOULD）。

---

### NFR-W-C-5: Sonnet 起動コスト（SHOULD）

gabriel の Sonnet 起動は AoT 適用 MAGI に限定し、非 AoT 合議では起動しないことで
週次レート消費を抑制するべきである（SHOULD）。
BUILDING 完了後の retro で実際の起動頻度と token 消費量を実測し、
超過が継続する場合はモデルを Haiku に降格するか起動条件を見直す。

---

### NFR-W-C-6: AoT フレームワークの非改変（MUST NOT）

本 Wave の変更は AoT（Atom of Thought）フレームワーク自体を物理削除または無効化してはならない（MUST NOT）。
AoT は独立した実績ある機構であり、gabriel probe の前提基盤として温存する。

---

## §5 受入条件（AC）

ID 体系: `AC-W-C-N`

| AC-ID | 対応 FR/NFR | 受入条件 | 計測方法 |
|:------|:-----------|:--------|:--------|
| AC-W-C-1 | FR-W-C-1 | `.claude/agents/gabriel.md` が存在する | ファイルの存在確認 |
| AC-W-C-2 | FR-W-C-1 | gabriel が Sonnet をデフォルトモデルとして定義している | `gabriel.md` フロントマターの `model` フィールド確認 |
| AC-W-C-3 | FR-W-C-2 | gabriel が `verdict / severity / affected_atoms / reasoning / recommended_action / confidence` の 6 フィールドを含む JSON を出力する | テスト入力に対する出力の JSON スキーマ検証 |
| AC-W-C-4 | FR-W-C-4 | AoT 適用 MAGI では gabriel が自動起動し、非 AoT MAGI では gabriel が起動しない | AoT 適用 stub（適用条件満たす）/ 非 AoT stub（適用条件満たさない）の各テストケースに対して、それぞれ gabriel 起動 / スキップが正しく実行されることを deterministic に検証する。ログ形式は design.md §6 で定義（OQ-W-C-5 → DQ-W-C-2 解消後に具体化）|
| AC-W-C-5 | FR-W-C-5 | `verdict=refuted & severity=critical` の入力に対して「再 MAGI 1 ラウンド指示」の出力が得られる | 擬似入力（stub MAGI 結論）に対する gabriel 呼び出しの結果確認 |
| AC-W-C-6 | FR-W-C-5 | `verdict=refuted & severity=warning` の入力に対して MAGI 結論に gabriel 指摘の併記が行われる | 擬似入力（stub MAGI 結論）に対する MAGI フロー出力の確認 |
| AC-W-C-7 | FR-W-C-5 | 再 MAGI が 2 回以上発生しない（上限 1 回が機能する）| 再 MAGI カウンターが 1 を超えた場合に人間エスカレーション出力が得られることを確認 |
| AC-W-C-8 | FR-W-C-6 | `confidence < 0.3` の場合に `verdict=confirmed` または `verdict=refuted` を返さない | `confidence=0.25` の stub 出力に対するスキーマ検証 |
| AC-W-C-9 | FR-W-C-6 | `affected_atoms=[]` の場合に `verdict=refuted` を返さない | `affected_atoms=[]` の stub 出力に対するスキーマ検証 |
| AC-W-C-10 | NFR-W-C-4 | MAGI 合議ログに gabriel の `verdict` / `severity` / `confidence` が記録される | 合議ログの形式確認（gabriel 記録セクションの存在 / 形式は design §5 各 verdict パターンテンプレート + §6 opt-out 記録形式に準拠） |
| AC-W-C-11 | NFR-W-C-6 | AoT Decomposition（Step 0）が廃止または無効化されていない | `SKILL.md` / `06_DECISION_MAKING.md` に AoT Decomposition の記述が残っていることを確認 |

### FR/NFR ↔ AC トレーサビリティ表

| FR/NFR | 対応 AC | カバー状態 |
|:-------|:-------|:---------|
| FR-W-C-1 | AC-W-C-1, AC-W-C-2 | 完全カバー |
| FR-W-C-2 | AC-W-C-3 | 完全カバー |
| FR-W-C-3 | AC-W-C-4, AC-W-C-11 | 完全カバー |
| FR-W-C-4 | AC-W-C-4 | 完全カバー |
| FR-W-C-5 | AC-W-C-5, AC-W-C-6, AC-W-C-7 | 完全カバー |
| FR-W-C-6 | AC-W-C-8, AC-W-C-9 | 完全カバー |
| FR-W-C-7 | (SHOULD / BUILDING で確認) | 部分カバー（実装確認は BUILDING）|
| NFR-W-C-1 | (BUILDING で計測) | BUILDING で対応 |
| NFR-W-C-2 | AC-W-C-3 | 完全カバー（フォーマット準拠）|
| NFR-W-C-3 | AC-W-C-8, AC-W-C-9 | 完全カバー（根拠品質要件で暴走抑制）|
| NFR-W-C-4 | AC-W-C-10 | 完全カバー |
| NFR-W-C-5 | (BUILDING retro で計測) | BUILDING 後評価 |
| NFR-W-C-6 | AC-W-C-11 | 完全カバー |

Gap: なし（全 FR/NFR に対応 AC が存在する）
Orphan: なし（全 AC が FR/NFR にトレースできる）

---

## §6 Open Questions

ID 体系: `OQ-W-C-N`

| OQ-ID | 問い | 現状の仮説 / 暫定対応 | 解消タイミング |
|:------|:-----|:-------------------|:-------------|
| OQ-W-C-1 | gabriel が実際に独立文脈を持てるか（subagent 起動時のコンテキスト分離度）| `.claude/agents/` 形式の subagent は呼び出し元と分離されたコンテキストで動作すると仮定。要 BUILDING での実機確認 | BUILDING Wave（実装後の実機テスト）|
| OQ-W-C-2 | Sonnet では自由理由生成の品質が十分か（Haiku vs Sonnet の判断）| Haiku では推論の深さが不足する懸念から Sonnet を選択（D-1 既決）。BUILDING 後 retro で品質評価を行い、必要であればモデル変更を検討する | BUILDING 後 retro |
| OQ-W-C-3 | AoT 適用判定自体の形骸化をどう防ぐか（自動検出の仕組み）| 本 Wave では人間による目視判断に委ねる。hooks 等での自動検出は将来 Wave の future-candidates として記録する | 将来 Wave（future-candidates 昇格後）|
| OQ-W-C-4 | gabriel rubric の初期化内容（何をプローブするか）| 「AoT Synthesis 結論に対する adversarial probe」として MAGI 合議結論の論理的一貫性・仕様整合・リスク見落としを問う。詳細は design.md §3 で定義 | design.md §3 と同時承認（本 Wave 内 / requirements と design は本ラウンドで同時承認）|
| OQ-W-C-5 | opt-out の記録方式（MAGI ログのどのセクションに記録するか）| design.md §6 で具体的な記録形式を定義する | design.md §6 と同時承認（本 Wave 内）|
| OQ-W-C-6 | タイムアウト検出機構（LAM subagent 基盤の提供有無 / 計測実装の所在）| 呼び出し元が経過時間を計測する暫定方針。BUILDING で実装手順確定 | BUILDING Wave |

---

## §7 改訂履歴

| バージョン | 日付 | 変更者 | 変更内容 |
|:----------|:-----|:------|:--------|
| 0.1.0 | 2026-06-29 | design-architect | 初版起草（Wave C / 骨子 ② PLANNING） |
| 0.2.0 | 2026-06-29 | design-architect | R1 指摘 9 件反映（W-R1-1〜4: FR-W-C-3 MUST NOT化 / NFR-W-C-1 責任者明示 / NFR-W-C-3 SHOULD NOT 降格 / G2 判定タイミング明示 / I-R1-1〜5: FR-W-C-5 abort 行追加 / confidence 刻み制約緩和 / OQ-W-C-4,5 解消タイミング修正 / OQ-W-C-6 新設 / ADR-0006 依存リスク注記 → ADR は別ファイル / AC-W-C-4 計測方法ログ依存明示）|
| 0.3.0 | 2026-06-29 | design-architect | R2 指摘 6 件反映（W-R2-1: FR-W-C-4 opt-out 主体修正 / 自律ループ却下 MUST 追記 / W-R2-2: NFR-W-C-2 検出主体明示 / FR-W-C-5 フォーマット不備行追加 / W-R2-3: FR-W-C-2 abort 独立経路説明追記 / I-R2-1: FR-W-C-5 warning 行 L1 確認義務 MUST 明示 / I-R2-2: AC-W-C-4 deterministic stub テスト形式に変換 / I-R2-3: ADR-0007 版数は別ファイルで実施）|
| 0.4.0 | 2026-06-29 | design-architect | R3 指摘 5 件反映（W-R3-1: NFR-W-C-2 主語統合 / 3パラグラフ→2パラグラフ構造変更 / W-R3-2: FR-W-C-2 クロスフィールド制約追加 / I-R3-1: ADR-0007 D-3 abort 行追加は ADR 側で実施 / I-R3-2: AC-W-C-10 計測方法に design §5+§6 参照先明示 / I-R3-3: FR-W-C-4 opt-out 理由記録主語明示）|
