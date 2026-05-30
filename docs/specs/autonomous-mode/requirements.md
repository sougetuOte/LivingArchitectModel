# 要件定義: 自律統治モード（autonomous-mode）

最終更新: 2026-05-30 / フェーズ: PLANNING（requirements）/ ステータス: **approved（2026-05-29 ユーザー承認）**
関連 ADR: [ADR-0005](../../adr/0005-thin-harness-autonomous-governance.md)（ハーネス減量と自律統治モードの導入）

> 本書は「何を（What）」を定義する要件書である。「どう実現するか（How）」は要件承認後の design で扱う。
> 設計判断の合議（MAGI）と category 別減量の根拠は ADR-0005 に置き、ここでは重複させない。

## 1. Problem Statement

LAM のハーネスは、当時のモデルが指示を守らず暴走した（設計せず実装着手・気ままな改変・コード増殖）ことへの対症療法として育った。2026年、モデルは自己門番化し（Opus 4.8: 欠陥黙過 約1/4・push back・clarifying question）、Anthropic は自律機構（/goal・dynamic workflows・Agent Teams）を提供し始めた。暴走という前提が後退した今、常時ON の強制ゲートは過剰摩擦に転化しつつある。

本要件は、LAM を「autonomy の統治・検証レイヤー」へ再定義し（ADR-0005）、**起源（長期記憶・暴走抑止）を裏切らずに自律実行を取り込む**ための、自律統治モードの要件を定義する。

## 2. Goals / Non-Goals

### Goals
- ユーザーの逐次承認なしに、対象 spec の Green State 達成まで自律的に実装を進められるモードを定義する。
- 自律の境界を権限等級（PG/SE/PM）の役割転換として定義する。
- $100 Max（Max 5x）で実運用可能な実装手段（/goal ベース）に限定する。
- ハーネス減量を category 別（A 減量 / B・C 維持 / 重量級ツールは last-line 保持）に規定する。

### Non-Goals（非スコープ）
- dynamic workflows / Agent Teams を core 依存として採用すること（future-candidates。FR-6.3 で実測後判断）。
- 別プロジェクトへの fork / extract（ADR-0005 で Option C を却下済み）。
- 憲法本体（CLAUDE.md / docs/internal/）の思想変更。Hierarchy of Truth と Zero-Regression は維持。
- 自律ループの具体的アルゴリズム・状態機械の設計（design で扱う）。

## 3. 機能要件（RFC 2119）

### FR-1 自律実行モードの定義と起動
- **FR-1.1 (MUST)**: 自律統治モードは、対象 spec を入力に取り、完了条件を「対象 spec の Green State 達成」として、ユーザーの逐次承認なしにターンをまたいで実装を進められなければならない。
- **FR-1.2 (MUST)**: 起動時、対象 spec と完了条件（適用する Green State 条件群）を明示し、ユーザーの確認を1度得てから自律ループに入らなければならない。
- **FR-1.3 (SHOULD)**: 既存の PLANNING/BUILDING/AUDITING 三フェーズ規律と整合する形で追加されるべきである（第4モードか BUILDING の自律変種かは RQ-6）。

### FR-2 権限エンベロープ（自律の境界）
- **FR-2.1 (MUST)**: PG級操作は自律ループ内で無断実行してよい。
- **FR-2.2 (MUST)**: SE級操作は自律実行してよいが、内容をログに蓄積し、完了時に一括報告しなければならない。
- **FR-2.3 (MUST NOT)**: PM級操作を無断実行してはならない。到達した場合は当該操作を実行せず、ループを停止または保留し人間の判断に委ねなければならない。
- **FR-2.4 (MUST)**: 等級判定は既存 `permission-levels.md` と PreToolUse hook のパス/操作分類を再利用しなければならない（新規等級体系を作らない）。

### FR-3 PM ハードストップのキュー化
- **FR-3.1 (SHOULD)**: 可逆な PM級事項は即時割り込みではなくキューに蓄積し、まとめて審議できるべきである（ユーザー選好: バッチ）。
- **FR-3.2 (MUST NOT)**: PM事項がキューに1件以上残る状態で、最終成果を merge / ship してはならない（merge 前審議ゲート）。
- **FR-3.3 (SHOULD)**: キューは無制限に溜めず、上限到達時はループを停止して人間に上げるべきである（溜め込み防止）。
- **FR-3.4 (MUST)**: 不可逆操作（`security-commands.md` の deny 系 = C層: rm / push / 秘密情報露出 / spec・ADR・rules 書換）は**キュー化対象外とし即時ハードストップしなければならない**（RQ-2 確定 2026-05-29）。

### FR-4 決定的 checker（完了判定）
- **FR-4.1 (MUST)**: 完了判定は決定的 Green State シグナル（G1 テスト exit0 / G2 lint exit0 / G5 セキュリティ）に接地しなければならない。「モデルが達成と宣言したこと」を完了の唯一根拠にしてはならない（MUST NOT）。
- **FR-4.2 (SHOULD)**: 非決定的観点（G3 Issue / G4 仕様差分 / 設計品質・命名）はモデル判断または監査エージェントに委ねてよいが、その判断根拠を報告に明示すべきである。
- **FR-4.3 (MUST)**: ハーネス減量後も、安い自動ネット（test / lint / security の実行）は維持しなければならない。判断（judgment）は honesty へ委譲してよいが、決定的チェックは残す。

### FR-5 ハーネス減量（category 別 — ADR-0005 準拠）
- **FR-5.1 (MUST)**: 信頼ゲート（A: フェーズ強制・TDD強制・per-step承認）は、常時ON のハードブロックから助言またはシグナル起動トリガへ降格しなければならない。
- **FR-5.2 (MUST)**: 連続性インフラ（B: quick-save/load, SESSION_STATE, retro, agent-memory）は維持しなければならない。
- **FR-5.3 (MUST)**: blast-radius ガード（C: security-commands deny, PM 境界）は維持しなければならない。
- **FR-5.4 (MUST)**: 重量級検証ツール（MAGI, full-review, 8 subagent, 敵対 verify）は削除せず、last-line（事後・オンデマンドの break-glass）として保持しなければならない。
- **FR-5.5 (SHOULD)**: 減量度合いはモデル品質に比例すべきで、ADR-0005 の見直しトリガーに従い再調整できるべきである。昇格条件は観測可能であるべきで、例として「自律ラン N 回連続で決定的 checker が赤を1件も拾わなかった場合に tripwire を1段緩める」を design で具体化する（RQ-1）。
- **FR-5.6 (MUST)**: last-line の自己起動（self-escalation）はコストで段階化しなければならない。安価な MAGI（in-context 合議・fan-out なし）は自律ループが広く自己起動してよい。高価な full-review / lam-orchestrate（マルチ subagent）は、1ランあたりのエスカレーション予算（回数・トークン上限）内でのみ自己起動でき、予算超過時は full-review を実行せず「human review 推奨」を PM キューへ積まなければならない。人間はいつでも last-line を起動できる（RQ-3 確定 2026-05-29）。
  > 注記: MAGI を「安価（in-context・fan-out なし）」と前提している。将来 MAGI を subagent 並列実装へ変える場合、本段階分けを見直す。

### FR-6 コスト / モデル出し分け（$100 Max 制約）
- **FR-6.1 (SHOULD)**: 自律ループ本体は下位モデル / 低 effort（例: Sonnet / 低）で回し、難所のみ Opus / 高 effort に上げるべきである。
- **FR-6.2 (MUST)**: core の実行手段は /goal ベースとし、dynamic workflows を必須依存にしてはならない（$100 Max で完結可能なこと）。
- **FR-6.3 (MAY)**: dynamic workflows / Agent Teams は scoped 実験として試用してよいが、採用は実測（token 消費・週枠影響）後に判断する。採用見送り時は理由を `future-candidates.md` に記録する。

### FR-7 継続性統合
- **FR-7.1 (SHOULD)**: 長時間ループは区切りで quick-save 相当の状態保存を行い、中断・再開できるべきである（/goal の resumable と整合）。

### FR-8 トレーサビリティ
- **FR-8.1 (MUST)**: 全 FR が、LAM の起源（長期記憶 / 暴走抑止）または ADR-0005 の決定にトレースできなければならない（§7）。

### FR-9 自己統治の不可侵（self-governance immutability / DW ブラインド検証の知見）
- **FR-9.1 (MUST NOT)**: 自律エンジン（/goal ループおよび将来の DW 実行を含む）は、自身の統治を定義するファイル群 —— `.claude/rules/` / `docs/adr/` / `.claude/settings*.json` / 自律モード自身のスキル・スクリプト定義 —— への書込権限を持ってはならない。これらの変更は常に自律ループの*外側*の人間承認ゲート（PM）を経由しなければならない（自己破壊的再帰の防止）。
- **FR-9.2 (MUST)**: 隔離（worktree 等）を不可逆境界の遮断と見なしてはならない。隔離は実行中の作業空間を守るが、merge / push / 隔離外への不可逆操作は隔離の外で成立する。C層の即時ハードストップ（FR-3.4）は隔離と独立に張らなければならない。
- **FR-9.3 (SHOULD)**: 機械的検証の合意収束（adversarial verify 等）を決定的シグナルと見なしてはならない。相関した盲点で偽収束しうるため、完了判定は FR-4.1 の決定的 Green State 接地を唯一の根拠とし、合意収束は非決定的観点（G3/G4）の補助に留めるべきである。

## 4. Success Criteria（成功基準・計測可能）

- **SC-1**: $100 Max で、対象 spec を1本、自律統治モードで Green State まで到達させ、PM事項はキュー経由でのみ人間に上がる、という end-to-end が1回成立する。
- **SC-2**: 自律ループのログ上、PG は無断・SE はバッチ報告で処理され、PM級操作の無断実行が 0件である。
- **SC-3**: 完了判定が決定的 Green State に接地しており、test / lint / security を実際に実行した記録が残る。
- **SC-4**: 既存テストスイート（576 passed / 20 skipped 相当）が回帰なく通過する。
- **SC-5**: MAGI / full-review が last-line として呼び出し可能な状態で残存している（削除されていない）。
- **SC-6**: B 層（quick-save/load 等）と C 層（security deny, PM 境界）が減量後も機能する。
- **SC-7**: 自律モードのいかなる構成でも、自律エンジンが自身の統治ファイル（`.claude/rules/` / `docs/adr/` / `.claude/settings*.json` / モード自身の定義）を無断改変せず、worktree 隔離を C層遮断と混同しないこと（設計・ログで検証可能）。

## 5. 設計判断（参照）

category 別減量の根拠・3案比較・MAGI 合議・Reflection は [ADR-0005](../../adr/0005-thin-harness-autonomous-governance.md) を参照（本書では重複させない）。

## 6. 未解決質問（Example Mapping: Red → 全て解決済み 2026-05-29）

審議の結果、RQ-1〜6 をユーザー承認のもと確定。Red はゼロ。

| # | 論点 | 決定（2026-05-29） |
|---|------|--------------------|
| RQ-1 | A の減量度合い | 決定的シグナルで自動起動する**薄い tripwire を残す**。将来は観測可能な昇格条件で段階的に委譲（FR-5.5） |
| RQ-2 | 不可逆操作の扱い | **不可逆 C は即時ハードストップ**、可逆 PM のみキュー化（FR-3.4） |
| RQ-3 | last-line の起動 | 自己起動を**コストで段階化**。安価な MAGI は広く自己起動可、高価な full-review はエスカレーション予算内のみ・超過時は「human review 推奨」を PM キューへ降格。人間はいつでも起動可（FR-5.6）。/goal の stuck 検知が thrash を抑止 |
| RQ-4 | checker の権限 | **block**（Green State 未達なら継続） |
| RQ-5 | dynamic workflows | **見送り**（/goal core）。future-candidates に理由付き記録、実測後に再評価（FR-6.3） |
| RQ-6 | 起動形態 | **独立第4モード**（内側で build と audit を駆動する層） |

## 7. トレーサビリティ（FR → 起源 / ADR）

| FR | 由来 | 説明 |
|----|------|------|
| FR-1 | ADR-0005 決定 | 自律統治モードの中核 |
| FR-2 | 起源②（暴走抑止）+ permission-levels | 等級の役割転換 |
| FR-3 | ユーザー選好（バッチ）+ ADR-0005 CASPAR-6 | キュー + merge ゲート |
| FR-4 | 起源②（モデルを信じ切らない）+ green-state-definition | 決定的接地 |
| FR-5 | ADR-0005 3層モデル | category 別減量 |
| FR-6 | 制約（$100 Max）| コスト適合 |
| FR-7 | 起源①（長期記憶）| 継続性 |
| FR-8 | planning-quality-guideline §5（WBS 100%）| 孤児・漏れ防止 |
| FR-9 | DW ブラインド検証の知見 + ADR-0005 Reflection 追補 | 自己統治の不可侵（authority 境界） |

孤児要件（仕様にあるが由来不明）: なし。

## 8. 権限等級サマリー

| 対象 | 等級 | 備考 |
|------|------|------|
| 本機能（自律モード）の導入そのもの | **PM** | モード追加 + rules/憲法への波及。ADR-0005 の人間承認が前提 |
| 各 FR の実装 | 実装時に再分類 | design / tasks で確定 |

## 9. 変更履歴
| 日付 | 変更者 | 内容 |
|------|--------|------|
| 2026-05-29 | Living Architect | 初版起草（審議用 Draft） |
| 2026-05-29 | sougetuOte | RQ-1〜6 審議・承認。status approved。FR-3.4 / 5.5 / 5.6 を確定 |
| 2026-05-30 | sougetuOte+LA | FR-9（自己統治の不可侵）追加。DW ブラインド検証の3 catch を反映（ADR-0005 Reflection 追補と対） |
