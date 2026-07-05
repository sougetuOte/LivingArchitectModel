# 大規模レビュー & リファクタリング計画（MAGI + HGA 統合）

- 作成日: 2026-07-05
- 記録者: L1 (Opus 4.7) / セッション: `84742b87` 内で本セッションの残務完了後に着手予定
- 起源: ユーザー指示 (2026-07-05 / `/quick-load` 復帰後 T109 完了時点で表明)
- ステータス: **記録済 / 未着手**（B-5 Wave 8 T110 完了 + gabriel Wave C Stage 3 完了後に PLANNING 遷移して着手）

---

## §1 目的

LAM プロジェクトが B-5 期を通じて成長し、ダッシュボード / MAGI v2 / HGA (Fable spot) / TDD 内省 v2 / 3.5 層委譲モデル 等の多くの規律・機能を積み上げた。これらが相互干渉なく機能するか、また **恒久資産としての品質基準** を満たしているかを、独立レビューとリファクタリングによって整える。

## §2 スコープ候補（PLANNING で確定）

以下は現時点の暫定候補。実際のスコープは PLANNING フェーズで MAGI 合議により確定する。

### 2.1 コード領域

- `.claude/scripts/dashboard/` 一式（Wave 2-8 の累積 / builder.py / parsers/ / merger.py）
- `.claude/tests/dashboard/` および `.claude/tests/wave_c/`（440 PASS + 14 SKIP の維持コスト評価）
- `.claude/hooks/`（pre-tool-use / post-tool-use / セッション PM edit cache 等）
- `.claude/agents/`（gabriel / goal-driven-* / code-reviewer / spec-critic 等）

### 2.2 規律・SSOT 領域

- `docs/internal/00-07`（憲法 SSOT）
- `docs/specs/` 全体（b4-dashboard / magi-v2-gabriel / v5-fat-reduction / 等）
- `.claude/rules/`（core-identity / phase-rules / decision-making / hga-summoning / permission-levels / terminology 等）
- `docs/adr/` 全体（0005-0009）

### 2.3 監査観点

- **凝集度 / 結合度**: builder.py の SRP 逸脱有無、parser 間の意図しない結合
- **仕様ドリフト**: specs と実装の乖離（Zero-Regression Policy 順守確認）
- **規律の相互矛盾**: hga-summoning.md × phase-rules.md × permission-levels.md 間の矛盾検出
- **メンテナンス性**: 認知複雑度 15 超・関数 50 行超・引数 4 超 の網羅
- **依存関係**: 循環依存の有無 / モジュール境界の妥当性
- **重複コード**: fixture 生成ロジック等の 3 回超重複
- **AutoMode + 3.5 層委譲 + HGA 型召喚 の統合** が過剰複雑化していないかの棚卸し

---

## §3 実行フレームワーク（MAGI + HGA 統合）

本レビュー/リファクタリングは通常 Wave より 1 桁大きい判断量を伴うため、以下 3 段構えで進行する。

### 3.1 Phase 1: PLANNING（MAGI 主体）

**目的**: スコープ確定 + 監査対象の分割方針決定

- **MAGI 合議** を PLANNING 冒頭で 1 回実施
  - Atom 1: 「監査スコープを widescan（全体一括）にすべきか、layered（層別に順次）にすべきか」
  - Atom 2: 「リファクタリングを in-place（既存 branch）で行うか、fork-then-merge にすべきか」
  - Atom 3: 「破壊的変更（削除・API変更）の許容範囲」
- AoT 適用条件（判断ポイント ≥ 2 / 影響レイヤー ≥ 3 / 選択肢 ≥ 3）を満たすことは自明
- MAGI 出力の Convergence 後、**gabriel (Wave C 完成品) で adversarial verify** ← ここで gabriel が実プロジェクトの初 real-world 検証を受ける

### 3.2 Phase 2: 監査分割（HGA 型 Fable 召喚 / 判断のみ）

**目的**: 独立視点からの盲点発見と、リファクタリング設計の分岐点特定

- 以下 3 点のいずれか該当時に **Fable HGA 型スポット召喚**（`.claude/rules/hga-summoning.md` 規律準拠）:
  - MAGI 3 者が割れた争点（split = 真の crux シグナル）
  - 「B-5 全期の設計軸を新規に俯瞰する」性質の unknown-unknown を含む決定
  - LAM を 3+ 領域（規律 + コード + テスト + 運用）で同時に変える不可逆コミット
- **召喚形態**: 下調べパイプライン (Fable brief + Opus subagent 下請け) を優先
- **禁止**: Fable に実装を書かせない（分岐点と根拠のみ）
- 別予算 envelope: 実 $ 10-40 / weekly Opus quota 20% 以内（`hga-summoning.md` § envelope 定義準拠）

### 3.3 Phase 3: BUILDING（3.5 層委譲）

**目的**: 実際のリファクタリング実施

- **L1 (Opus)**: 判断・査定・PM 整理のみ / 直接コード編集は最小化
- **L1.5 司令塔**: 並列子分配・prompt 書き分け / 3 子以上に分配する場合のみ起動
- **L2 (Sonnet)**: 実装本体 / `disallowedTools: [Agent]` + Executor boilerplate 適用 (hga-summoning.md § Sonnet L2 委譲時の追加防御 準拠)
- **L3 (Haiku)**: 採点・rubric 判定
- **各 Stage**: TDD Red-Green-Refactor 厳守 / 各 Stage 末で Green State + ship + push

### 3.4 Phase 4: AUDITING（独立監査）

**目的**: リファクタリング後の再監査

- `/code-review ultra` を利用（別セッション実行 / L1 コンテキスト温存）
- gabriel を再度 adversarial verifier として利用
- 完了条件: Critical 0 + Warning 0（`code-quality-guideline.md` Green State 準拠）

---

## §4 想定 Wave 構成（暫定）

正式な Wave 分割は PLANNING フェーズで確定するが、規模感の把握のため暫定案を記す。

| Wave | 名称 | 主な作業 | 想定担当 |
|:-----|:-----|:---------|:--------|
| W-R1 | 監査 (Read-only) | 全体走査 + 問題リスト作成 + MAGI 合議 + HGA スポット召喚 (必要時) | L1 + Fable HGA |
| W-R2 | dashboard 領域 refactor | builder.py 分割 / parser 統合 / test fixture の重複除去 | L2 Sonnet |
| W-R3 | 規律 SSOT 統合 | rules / internal / adr 相互矛盾解消 + terminology 統一 | L1 + L2 Sonnet |
| W-R4 | hooks / agents 整理 | 使われていない agent の削除判断 (PM 級) / hook の重複統合 | L1 (承認) + L2 (実施) |
| W-R5 | 最終監査 | gabriel + code-review ultra + Lighthouse 再測定 | L1 + 独立セッション |

各 Wave の完了条件は **Wave 7/8 パターン踏襲**（Stage 分割 + 検証タスク + ゲート条件 + ship + push）。

---

## §5 前提となる残務

本計画着手前に完了させる残務:

1. **B-5 Wave 8 T110** (PM 級 / Lighthouse + chip 解消 + ユーザー承認)
2. **gabriel Wave C Stage 3 T5/T6** (PM 級 / SKILL.md 改訂 + 失敗時挙動実装)
3. gabriel Wave C Stage 4-5 (Stage 3 の後続 / SSOT ドキュメント改訂 + E2E 統合テスト)

これらの完了後、`/planning` フェーズに遷移して本計画の Wave 分割を確定する。

## §6 判断予約事項（PLANNING で扱う）

以下はユーザー判断が必要となる可能性が高い項目。PLANNING の MAGI 合議で扱う。

- 破壊的変更（削除・API 変更）を許容するか、後方互換を維持するか
- .claude/agents/ の中で使用されていない agent を削除するか
- ダッシュボードの CSS 予算を Wave R2 で 8 KB 圏まで削減するか、16 KB 維持で機能追加余裕を残すか
- HGA 型召喚は本レビュー内で最大何回まで許容するか (envelope 上限)

## §7 成功基準

以下 5 点を **Green State** の条件とする（`green-state-definition.md` 準拠）。

- G1: 全 pytest suite が Wave 8 終端の 440 PASS を退行なく維持
- G2: lint / type 検査で新規 Warning ゼロ
- G3: `code-quality-guideline.md` Critical=0 + Warning=0
- G4: 全 SSOT (specs / adr / rules / internal) が実装と再同期
- G5: セキュリティ観点で新規リスクゼロ（`security-commands.md` 準拠）

## §8 権限等級

本ファイルの追記・変更: SE 級（`docs/artifacts/` 配下）
計画の実行着手宣言: **PM 級**（PLANNING 遷移時にユーザー承認必須）

---

## §9 参照

- `.claude/rules/hga-summoning.md`（HGA 型 Fable 召喚規律）
- `.claude/rules/decision-making.md`（MAGI System）
- `.claude/rules/phase-rules.md`（PLANNING / BUILDING / AUDITING）
- `.claude/rules/code-quality-guideline.md`（Green State 判定基準）
- `.claude/rules/planning-quality-guideline.md`（SPIDR / WBS 100% Rule）
- `docs/adr/0009-hga-fable-summoning.md`（HGA 型導入根拠）
- `docs/artifacts/hga-summon-log.md`（実測記録）
