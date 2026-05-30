# タスク定義: 自律統治モード（autonomous-mode）

最終更新: 2026-05-30 / フェーズ: PLANNING（tasks）/ ステータス: **approved（2026-05-30 ユーザー承認）**
親: [requirements.md](requirements.md)（approved・FR-1〜9 / SC-1〜7）/ [design.md](design.md)（approved・D1〜D6）
関連: [green-state-definition.md](../green-state-definition.md)（checker 接地・MVP=G1/G2/G5）, [ADR-0005](../../adr/0005-thin-harness-autonomous-governance.md)

## 凡例

- 等級: PG（自動）/ SE（修正後報告）/ PM（人間承認必須）。出典は `.claude/rules/permission-levels.md`
- 各タスクは原則 1 コミット。WBS の起点は design §7「影響を受けるコンポーネント」表。
- 分割方針: **SPIDR 垂直分割**（全層を薄く貫通）。Wave 1 を「動く最小の縦串」とし、以降の Wave で境界・安全・賢さを厚くする。

---

## Wave 0（着手ゲート）— `/goal` 機構の裏取り

> **upstream-first §7（二段構え）**: design は `/goal` を core 実行手段（FR-6.2）と前提するが、completion / validator 接続の**具体書式は未確認（要裏取り）**。確定前に Wave 1 へ進まない。

### T0-1: `/goal` 機構の二段裏取り（着手ゲート） — SE

- **対象**: Claude Code の `/goal`（自律実行）機構
- **段階1（実在性）**: context7 優先・WebFetch フォールバックで以下を確認
  - `/goal` の起動書式・引数
  - **completion（完了条件）の宣言方法**と validator の接続点（design D1「validator が毎ステップ Green State 達成かを問う」の実現手段）
  - **resumable / 中断再開**の仕様（FR-7.1 と整合するか）
  - ターンをまたぐ自律継続のセマンティクス（FR-1.1）
- **段階2（LAM 適合性）**: `/goal` が承認ゲート（FR-1.2）・決定的 checker 接地（FR-4）・FR-9 強制と整合するかを評価
- **成果物**: `docs/artifacts/research/2026-05-30-goal-survey/` に裏取り結果（各項目に「確認済み(出典) / 未確認(理由)」ラベル）
- **完了条件**:
  - 上記4項目すべてにラベル付与
  - **completion 接続と resumable が確定**（未確定なら Wave 1 をブロック）
  - 段階2 で不整合が判明した場合は理由を `future-candidates.md` に記録し、代替手段を design 差し戻しで再検討
  - 未確認項目は「未確認」明示・推測実装禁止
- **トレース**: FR-6.2 / FR-1.1 / FR-7.1
- **依存**: なし（最初の着手ゲート）
- **✅ 状態**: 完了（2026-05-30）。裏取り結果は [findings.md](../../artifacts/research/2026-05-30-goal-survey/findings.md)。結論=案1（アップグレード後 `/goal` core 維持）。段階1/2 完了、残るは下記 P-2 のみ

---

## Wave 1 着手の前提条件（T0-1 裏取りで確定）

- **P-1 ✅**: Claude Code を v2.1.139+ にアップグレード（完了: **2.1.158**）。`/goal` 利用可。
- **P-2 ✅ 完了（2026-05-30 実機検証）**: 複数 Stop hook の合成は **「いずれか block→継続」（OR / most-restrictive）** を隔離 headless（`claude -p`）で実機確定（[findings](../../artifacts/research/2026-05-30-goal-survey/findings.md) P-2c・`num_turns=2`）。決定的 `lam-stop-hook`(block) が `/goal` evaluator(stop) に**優先**し gate を維持。block cap（既定 8 / `0` 無効化）・`stop_hook_active`・auto mode（`claude auto-mode config` 動作・`permissions.deny` 前段 override 不可）も 2.1.158 で確定。→ **Wave 1 着手の技術前提クリア**。

---

## Wave 1（MVP 縦串）— `/goal` × Green State(G1) + FR-9 最小強制

> **狙い**: 「対象 spec を入力に、人間の逐次承認なしに build → 決定的 checker → 完了」という**背骨を最短で通す**。正常系（Green State 一発達成）に絞り、SC-1 / SC-7 を**最小成立**させる。
> **FR-9 を MVP に含める判断**: 自己統治の不可侵（FR-9.1 MUST NOT）は安全の要であり、強制点の追加は小さい（PreToolUse の条件分岐 1 つ）。autonomous エンジンが自身の定義を書き換えられる状態でループを回さないため、Wave 3 の PM キューと分離して MVP に前倒しする。

### T1-1: `autonomous-state.json` 最小スキーマ — SE

- **対象**: `.claude/autonomous-state.json`（新規・design D1）
- **変更**: MVP に必要な最小フィールドを定義（`active` / `mode` / `spec_target` / `phase` / `iteration` / `max_iterations` / `checker_results` / `log`）。`pm_queue` / `se_log` / `escalation_budget` / `tripwire_*` は後続 Wave で追加する前提のキーとして空で確保
- **完了条件**: スキーマが design D1 と文字単位で一致 / `.gitignore` 方針を確認（状態ファイルの扱い）/ `lam-loop-state.json` と独立（D1 の分離理由）
- **トレース**: FR-1.1 / design D1
- **依存**: T0-1

### T1-2: checker スクリプト G1（test）— SE

- **対象**: `.claude/hooks/checkers/`（新規ディレクトリ・design §7）
- **変更**: G1（テスト exit0）を実行する checker スクリプト。`green-state-definition.md` §3.1 のテストFW自動検出（pyproject→pytest 等）と timeout（既定120s）を実装。**出力規約（findings B）: PASS=exit 0 / FAIL=exit 2（stderr に赤の詳細）**
- **完了条件**: 実 exit code を返す / 自プロジェクト（pytest）で PASS/FAIL を正しく判定 / Red→Green でテスト追加（checker 自体の単体テスト）
- **トレース**: FR-4.1a / FR-4.3 / design D3
- **依存**: T0-1

### T1-3: Stop hook に autonomous 検出 + checker(G1) 厳密実行 — SE

- **対象**: [.claude/hooks/lam-stop-hook.py](../../../.claude/hooks/lam-stop-hook.py)（design §7・SE）
- **変更**: `autonomous-state.json` の `active=true` を検出したら、Stop hook 自身が T1-2 の checker(G1) をサブプロセス実行し、実 exit code を `checker_results` に記録（モデル改竄不能・design D3）。全 PASS→ completion 許可 / FAIL→ `{"decision":"block","reason":"<赤の checker>"}` でループ継続（FR-4.1a / D1 遷移）。**block cap=8 対策（findings A）: `stop_hook_active` を見て進捗なしなら早期 exit、自律ラン中は `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP` を `max_iterations` 以上に設定**
- **完了条件**: completion 主張時のみ発火（作業継続中は発火しない・D3 コスト配慮）/ block 時に「どの checker が赤か」を返す / 既存 Stop hook 機能（full-review 連携等）が回帰なし
- **トレース**: FR-4.1a / FR-4.1b / design D3
- **依存**: T1-1, T1-2

### T1-4: FR-9 最小強制（PreToolUse hook + permissions.deny の二重防御）— SE/PM

- **対象**: [.claude/hooks/pre-tool-use.py](../../../.claude/hooks/pre-tool-use.py)（SE）+ `.claude/settings.json` の `permissions.deny`（**PM**・settings 変更）
- **変更**: (a) `pre-tool-use.py`: `current_phase == "AUTONOMOUS"` かつ書込先が `FR9_PATTERNS`（`.claude/rules/**` / `docs/adr/**` / `.claude/settings*.json` / `.claude/hooks/**` / `.claude/skills/autonomous/**`）に一致したら **deny**（design D5・プロンプティング層）。(b) **`permissions.deny` に FR9_PATTERNS を固定**（design D7 層1・classifier 前段・上書き不可・決定的）。**二重防御**。既存 deny 系（C層・不可逆操作）は隔離と独立に維持（FR-9.2）
- **完了条件**: FR9_PATTERNS への書込が AUTONOMOUS 下で block される（特に `.claude/hooks/**` と `.claude/skills/autonomous/**` を含む＝自己破壊的再帰防止）/ `permissions.deny` が hook・classifier より前段で効く（決定的）/ 既存フェーズの判定が回帰なし / Red→Green でパターン一致テスト追加
- **トレース**: FR-9.1 / FR-9.2 / FR-3.4 / SC-7 / design D5・D7
- **依存**: T0-1（AUTONOMOUS モード値の確定は T1-6 と並行可）。**settings.json 変更は PM 承認ゲート**

### T1-5: autonomous スキル最小版 — PM（モード追加）

- **対象**: `.claude/skills/autonomous/SKILL.md`（新規・design D5・**PM級**）
- **変更**: MVP の責務に限定 ——
  - **起動**: `spec_target` を引数に取り、完了条件（適用 Green State 条件＝MVP は G1）を明示してユーザーの **1 回承認**を得てループに入る（FR-1.2）
  - **駆動**: build サブルーチン → checker(G1) → Green State 達成まで反復（既存 build スキルは変更せず内側で駆動・ADR CASPAR 方針5）
  - **終了**: 完了報告（PM キュー・se_log・last-line は後続 Wave で追加）
- **完了条件**: 起動時に承認ゲートが効く / `/goal` ベースで回る（T0-1 の確定書式に準拠）/ FR-6.1 のモデル委譲方針を記述（本体は下位モデル）
- **トレース**: FR-1.1 / FR-1.2 / FR-1.3 / FR-6.2 / FR-6.1
- **依存**: T0-1, T1-1, T1-3。**PM 承認ゲート**

### T1-6: AUTONOMOUS モード登録（current-phase.md）— PM相当（運用値）

- **対象**: [.claude/current-phase.md](../../../.claude/current-phase.md)（design §7・PM相当）
- **変更**: `**AUTONOMOUS**` 値を追加（既存フォーマット）。PreToolUse の `_read_current_phase()`（`**([A-Z]+)**` 抽出）が変更なしで動作することを確認（design D5）
- **完了条件**: モード切替が機能 / 既存3フェーズの読取が回帰なし
- **トレース**: FR-1.3 / design D5
- **依存**: なし（T1-4 / T1-5 と整合）。**PM 承認ゲート**

### Wave 1 完了判定

- SC-1（**最小**）: 対象 spec 1 本を AUTONOMOUS で起動し、build → checker(G1) → 完了の end-to-end が 1 回成立
- SC-7（**最小**）: AUTONOMOUS 下で FR9_PATTERNS への書込が deny される（ログで検証）
- SC-4 部分: 既存テストスイートが回帰なし（Wave 1 で触れた hook の既存テスト）
- ⚠️ **MVP 運用注意**: 権限エンベロープ（FR-2）・PM キュー（FR-3）・last-line 自己起動（FR-5.6）は未実装。Wave 1 の実証は**人間監視下**で、`se_log` 相当を手動確認しながら実施する

---

## Wave 2（権限エンベロープ + checker 完備）— FR-2 / FR-4 完成

### T2-1: checker を G2(lint) + G5(security) に拡張 — SE

- **対象**: `.claude/hooks/checkers/` + T1-3 の Stop hook 連携
- **変更**: G2（lint exit0・`green-state-definition.md` §3.2 自動検出）と G5（依存脆弱性+シークレット+危険パターン・§3.5）を追加。checker_results に g2/g5 を記録
- **完了条件**: G1/G2/G5 の3点を厳密実行 / ツール未導入時は PASS スキップ+ログ（§3.2/3.5）/ Red→Green
- **トレース**: FR-4.1a / FR-4.3 / SC-3
- **依存**: T1-3

### T2-2: 権限エンベロープ実装（PG無断 / SE蓄積 / PM分岐）— SE

- **対象**: `.claude/skills/autonomous/SKILL.md` の駆動部 + `autonomous-state.json`（`se_log`）
- **変更**: ループ内で PG は無断実行 / SE は `se_log` に蓄積 / PM 到達時は無断実行せず分岐（可逆→保留・不可逆→停止）。等級判定は既存 `permission-levels.md` と PreToolUse 分類を**再利用**（新体系を作らない・FR-2.4）。**PG 無断実行は `claude --permission-mode auto`（auto mode classifier・design D7 層3）で自動化。決定的境界は層1 `permissions.deny` が担保**
- **完了条件**: PG/SE/PM の振り分けがログで検証可能 / PM 級操作の無断実行が 0（SC-2）
- **トレース**: FR-2.1 / FR-2.2 / FR-2.3 / FR-2.4 / FR-4.2（非決定的観点は audit サブルーチンへ委譲・根拠明示）
- **依存**: T1-5

### T2-3: 完了時 SE バッチ報告 — SE

- **対象**: `.claude/skills/autonomous/SKILL.md` の終了部
- **変更**: ループ完了時に `se_log` を一括報告（FR-2.2）
- **完了条件**: SE 操作がバッチで報告される（SC-2）
- **トレース**: FR-2.2 / 依存: T2-2

### Wave 2 完了判定

- SC-2（PG無断 / SE バッチ / PM 無断 0）/ SC-3（決定的 Green State 接地・test/lint/security 実行記録）

---

## Wave 3（PM キュー）— FR-3 完成（可逆 PM のバッチ + merge前ゲート）

> 不可逆 C（rm/push/秘密露出 等）の即時ハードストップは既存 deny + Wave 1 の FR-9 強制で成立済み（FR-3.4）。本 Wave は**可逆 PM**のキュー化を担う。

### T3-1: pm_queue 構造 + 蓄積ロジック — SE

- **対象**: `autonomous-state.json`（`pm_queue` / `pm_queue_limit`）+ autonomous スキル
- **変更**: 可逆 PM 事項を `{item, reason, level, timestamp}` で蓄積（design D2 / FR-3.1）
- **完了条件**: 可逆 PM が即時割り込みせずキューに入る / 不可逆 C はキュー化されず即時停止（FR-3.4 回帰確認）
- **トレース**: FR-3.1 / FR-3.4 / 依存: T2-2

### T3-2: merge 前審議ゲート（PreToolUse 拡張）— SE

- **対象**: [.claude/hooks/pre-tool-use.py](../../../.claude/hooks/pre-tool-use.py)
- **変更**: `pm_queue` 非空 かつ `git push`/`git merge`/`/ship` 相当を検出したら **block**（design D2 / FR-3.2）
- **完了条件**: キュー非空時に merge/ship 不可 / 空になると解除 / 既存 deny 回帰なし / Red→Green
- **トレース**: FR-3.2 / SC-6 / 依存: T3-1

### T3-3: bounded（上限到達でループ停止）— SE

- **対象**: autonomous スキル + `autonomous-state.json`（`pm_queue_limit` 暫定5）
- **変更**: `pm_queue.length >= pm_queue_limit` で `active=false` 停止し、キュー一覧を報告（FR-3.3 / design D2）
- **完了条件**: 上限到達でループ停止＋報告
- **トレース**: FR-3.3 / 依存: T3-1

### Wave 3 完了判定

- FR-3.1/3.2/3.3 充足 / SC-6（C層: deny + PM 境界が機能）/ SC-7（完全: FR-9 + PM キュー併存）

---

## Wave 4（last-line 段階化 + tripwire）— FR-5.4/5.5/5.6 完成

### T4-1: escalation_budget + MAGI 自己起動（安価・広く）— SE

- **対象**: `autonomous-state.json`（`escalation_budget`）+ autonomous スキル
- **変更**: 難所（G1/G2 が N 回連続 FAIL / 想定外エラー / 設計分岐）で安価な MAGI（in-context・fan-out なし）を自己起動。`magi_limit`（暫定3）で上限（design D4 / FR-5.6）
- **完了条件**: MAGI が難所で起動 / 予算内に収まる
- **トレース**: FR-5.4 / FR-5.6 / 依存: T2-2

### T4-2: full-review 予算ガード + 超過時 PM キュー降格 — SE

- **対象**: autonomous スキル + `escalation_budget`（`full_review_limit` 暫定1）
- **変更**: 高価な full-review は予算内のみ自己起動。超過時は実行せず「human review 推奨」を `pm_queue` へ降格（FR-5.6）。人間はいつでも起動可
- **完了条件**: 予算超過時に full-review を実行せず PM キューへ降格
- **トレース**: FR-5.4 / FR-5.6 / 依存: T4-1, T3-1

### T4-3: tripwire 昇格ロジック — SE

- **対象**: `autonomous-state.json`（`consecutive_clean_runs` / `tripwire_n` 暫定3 / `tripwire_level`）+ Stop hook
- **変更**: checker が赤を1件も拾わなかった連続ラン数が `tripwire_n` に達したら `tripwire_level` を1段上げ、A層の自動起動トリガを1段緩める（FR-5.5・観測可能な昇格）。段階表は design 付録に定義
- **完了条件**: 連続クリーンで tripwire_level が昇格 / 段階表どおりトリガが緩む
- **トレース**: FR-5.5 / 依存: T4-1

### Wave 4 完了判定

- FR-5.4/5.5/5.6 充足 / SC-5（MAGI/full-review が last-line として残存・呼び出し可能）

---

## Wave 5（継続性 + phase-rules + 仕上げ）— FR-7 / 回帰 / 全 SC 確認

### T5-1: quick-save 統合（区切りで状態保存・resumable）— SE

- **対象**: autonomous スキル + 既存 quick-save 連携
- **変更**: 長時間ループの区切りで quick-save 相当の状態保存を行い、中断・再開できる（FR-7.1 / `/goal` resumable と整合・T0-1 の確定仕様に準拠）
- **完了条件**: 区切りで状態保存 / 中断後に再開できる
- **トレース**: FR-7.1 / FR-5.2（B層維持）/ 依存: T1-1, T0-1

### T5-2: phase-rules.md に `## AUTONOMOUS` 節追加 — PM（rules 変更）

- **対象**: [.claude/rules/phase-rules.md](../../../.claude/rules/phase-rules.md)（**PM級**）
- **変更**: 既存 PLANNING/BUILDING/AUDITING と同等構造で `## AUTONOMOUS` 節を追加。記述 = 権限エンベロープ（FR-2）/ PM キュー運用 / FR-9 制約 / ループ終了条件 / 信頼ゲートの降格方針（FR-5.1: 常時ONハードブロック→助言・シグナル起動）
- **完了条件**: 節が既存構造と整合 / FR-5.1 の減量方針が明文化
- **トレース**: FR-1.3 / FR-5.1 / 依存: Wave 1〜4 の挙動確定後。**PM 承認ゲート**

### T5-3: 全 SC 回帰・確認 — SE

- **対象**: テストスイート全体 + 全 SC
- **変更**: SC-4 回帰確認（参考値 576 passed / 20 skipped が回帰なく全通過）。SC-1〜SC-7 を端から端まで再確認（SC-5 last-line 残存 / SC-6 B層+C層機能）
- **完了条件**: 全テスト通過 / 全 SC 充足を記録
- **トレース**: SC-4 / SC-5 / SC-6 / FR-5.2 / FR-5.3 / 依存: 全 Wave

### Wave 5 完了判定

- 全 FR / 全 SC 充足 / SC-4 回帰なし → autonomous-mode 完成

---

## トレーサビリティ（WBS 100% Rule 検証）

### FR → タスク

| FR | 対応タスク | 状態 |
|----|-----------|------|
| FR-1.1 | T1-1 / T1-5 | カバー |
| FR-1.2 | T1-5 | カバー |
| FR-1.3 | T1-5 / T1-6 / T5-2 | カバー |
| FR-2.1〜2.4 | T2-2（FR-2.2 は +T2-3）| カバー |
| FR-3.1 | T3-1 | カバー |
| FR-3.2 | T3-2 | カバー |
| FR-3.3 | T3-3 | カバー |
| FR-3.4 | T1-4（既存 deny + FR-9 強制）/ T3-1 回帰 | カバー |
| FR-4.1a | T1-2 / T1-3 / T2-1 | カバー |
| FR-4.1b | T1-3（hook 厳密実行）| カバー |
| FR-4.2 | T2-2（非決定的観点を audit/last-line へ・根拠明示）| カバー |
| FR-4.3 | T1-2 / T2-1 | カバー |
| FR-5.1 | T1-5 / T5-2 | カバー |
| FR-5.2 | T5-1 / T5-3（B層維持確認）| カバー |
| FR-5.3 | T1-4 / T5-3（C層維持確認）| カバー |
| FR-5.4 | T4-1 / T4-2 | カバー |
| FR-5.5 | T4-3 | カバー |
| FR-5.6 | T4-1 / T4-2 | カバー |
| FR-6.1 | T1-5 / T2-2（モデル委譲）| カバー |
| FR-6.2 | T0-1 / T1-5（/goal core）| カバー |
| FR-6.3 | future-candidates.md（作成済み・MAY）| カバー |
| FR-7.1 | T5-1 | カバー |
| FR-8.1 | 本トレーサビリティ表 + requirements §7 | カバー |
| FR-9.1 | T1-4 | カバー |
| FR-9.2 | T1-4（隔離と独立に C層）| カバー |
| FR-9.3 | T1-3（決定的接地を唯一根拠）/ T4-* 設計 | カバー |

### SC → タスク

| SC | 対応タスク | 状態 |
|----|-----------|------|
| SC-1 | Wave 1（最小）→ T5-3（完全）| カバー |
| SC-2 | T2-2 / T2-3 | カバー |
| SC-3 | T1-3 / T2-1 | カバー |
| SC-4 | T5-3（+各 Wave の回帰）| カバー |
| SC-5 | T4-1 / T4-2 | カバー |
| SC-6 | T3-2 / T5-3 | カバー |
| SC-7 | T1-4（最小）→ Wave 3（完全）| カバー |

- 実装漏れ（Gap）: なし（全 FR-1.1〜9.3 / 全 SC-1〜7 に対応タスクあり）
- 孤児タスク（仕様にトレース不能）: なし
- design §7 コンポーネント網羅: `autonomous-state.json`(T1-1) / `lam-stop-hook.py`(T1-3) / `pre-tool-use.py`(T1-4,T3-2) / `checkers/`(T1-2,T2-1) / `skills/autonomous/`(T1-5) / `current-phase.md`(T1-6) / `phase-rules.md`(T5-2) / `future-candidates.md`(作成済み) ← 全8件カバー

## 等級サマリー（PM 承認ゲートを要するタスク）

| タスク | 等級 | 承認タイミング |
|--------|------|---------------|
| T1-5（autonomous スキル新規）| PM | Wave 1 実装前 |
| T1-6（current-phase.md にモード追加）| PM相当 | Wave 1 実装前 |
| T5-2（phase-rules.md に節追加）| PM | Wave 5 実装前 |

その他（T0-1 / T1-1〜1-4 / T2-* / T3-* / T4-*）は SE 級（修正後報告）。

## 未解決質問

- **DQ-1**: T0-1 の裏取り結果次第で、`/goal` の completion/validator 接続が design D1 の想定と乖離する可能性。乖離時は design 差し戻し（PM）。← Wave 0 で解決
- **DQ-2**: FR-9 最小強制を Wave 1 に前倒しする本案の是非（安全優先 vs MVP 最小化）。← **解決済み（2026-05-30 承認）: 前倒しを採用**

## 変更履歴

| 日付 | 変更者 | 内容 |
|------|--------|------|
| 2026-05-30 | Living Architect(Opus) + sougetuOte | 初版起草（draft）。Wave 0〜5・SPIDR 垂直分割・WBS 100% 検証・FR-9 を Wave 1 前倒し |
| 2026-05-30 | sougetuOte | tasks 承認（approved）。DQ-2 = FR-9 前倒し採用で確定 |
| 2026-05-30 | Living Architect(Opus) + sougetuOte | T0-1 裏取り反映: 前提条件 P-1（✅アップグレード済）/P-2 追加・T1-2/T1-3 に exit code & block cap 仕様・T1-4 を permissions.deny 二重防御へ・T2-2 に auto mode classifier。design 同期（D1精緻化/D7新節）|
| 2026-05-30 | Living Architect(Opus) + sougetuOte | P-2 実機検証完了を反映（前提条件 P-2 を ✅ クローズ）。複数 Stop hook 合成 = **OR 確定**・auto mode/permissions.deny を 2.1.158 再確認。→ Wave 1 着手可 |
