# 設計書: Claude Code 仕様すり合わせ更新（cc-spec-alignment）

最終更新: 2026-05-28 / フェーズ: PLANNING（design）/ ステータス: **approved（2026-05-28 ユーザー承認）**
親要件: [requirements.md](requirements.md)（approved 2026-05-28）

## 1. Problem Statement

[requirements.md](requirements.md) §1 を参照。破壊的乖離はゼロだが、ドキュメント陳腐化（要更新7件）・
未確認5件・新機能未活用（64件）が判明している。本設計は承認済み要件（FR-1〜FR-6 + Wave 構成）を
実行可能な変更単位に落とし込む。Wave 1（即時）の起点は **FR-3 裏取りファースト**。

## 2. Non-Goals（非スコープ）

- 64件の新機能の網羅実装（§7 で選定したもののみ）
- hooks Python 移行アーキテクチャの再設計（v4.6 系完了済み）
- 要件書・ADR の API 書式非依存箇所の改訂（Upstream First 原則）
- 裏取り未確認項目の推測実装（FR-3.2 = MUST NOT）

## 3. 裏取り計画（FR-3 — Wave 1 最初のタスク）

各項目を「確認済み（出典付き URL/節）」または「未確認（理由付き）」でラベル付けし、
`docs/artifacts/research/` 配下に結果を追記する。手段: context7 MCP 優先・WebFetch フォールバック（対話モード）。

| # | 確認対象 | 関連 | 確認後の分岐 |
|---|----------|------|-------------|
| V-1 | PostToolUse 入力キーは `tool_response` か `tool_result` か | H-20 / FR-2.1 | `tool_response` 正なら現状維持・誤りなら FR-2.2 是正 |
| V-2 | PreCompact のブロック出力可否（公式掲載の有無） | H-02 / FR-1.1 | 掲載済み確認 → コメント是正文言を確定 |
| V-3 | `type: "mcp_tool"` hook の完全スキーマ | FR-3.1 / FR-5 | スキーマ確定 → 新ハンドラ採用判断の材料 |
| V-4 | Windows managed-settings 旧パス廃止の確定バージョン | S-1 / FR-3.1 | LAM に直接参照なし → 影響有無を記録 |
| V-5 | `xhigh` effort 対応モデル一覧 / `policyHelper`・`disableRemoteControl` バージョン | FR-3.1 | 記録のみ（実装影響は低） |
| V-6 | 公式 `memory:` の書込タイミング・スコープ（user/project/local）・既存ファイル扱い（上書き/追記） | C-2/C-3 / FR-4 | **RQ-1 段階移行の (b)/(c) 分岐を決する核** |
| V-7 | `isolation: worktree` / `background` の挙動・制約・隔離範囲 | FR-3.3 / RQ-2低 | 採用可否と昇格後優先度を記録 |
| V-8 | `effort.level` hook 入力 / 新 hook ハンドラ（mcp_tool/agent/prompt）の効果と影響範囲 | FR-3.3 / RQ-2低 | 採用可否と昇格後優先度を記録 |

**ゲート**: V-1・V-2・V-6 が未確認のまま Wave 1 の是正実装に進んではならない（FR-3.2）。

## 4. Wave 1 設計 — 陳腐化是正（FR-1, FR-2）

### 4.1 FR-1.1: pre-compact.py コメント是正（PG級）
- 対象: [.claude/hooks/pre-compact.py:8](../../../.claude/hooks/pre-compact.py)
- 現状: `NOTE: PreCompact は公式ドキュメント未掲載だが動作確認済み（2026-03時点）`
- 変更: V-2 確認後、PreCompact が正式イベントである旨へ書き換え。「ブロック不可・exit 0」の事実は維持。
- コミット単位: 単独（PG級・コメントのみ）

### 4.2 FR-2: PostToolUse 入力キー是正（SE級・条件付き）
- 対象: [.claude/hooks/_hook_utils.py:81-89](../../../.claude/hooks/_hook_utils.py) `get_tool_response`
- 現状: `data["tool_response"][key]` を参照
- 分岐:
  - V-1 で `tool_response` が正 → **変更なし**（FR-2.2 は発動せず、確認記録のみ）
  - V-1 で `tool_result` が正 → 正キーへ是正。**両キー併存フォールバック**（`tool_response` → 無ければ `tool_result`）を第一候補とし、後方互換を確保
- 波及: `post-tool-use.py`（TDD パターン記録）が本関数経由。是正時は [test_hook_utils.py](../../../.claude/hooks/tests/test_hook_utils.py) にキー両系統のテストを追加（Red→Green）
- コミット単位: 単独（テスト+実装）

## 5. Wave 1 設計 — Memory Policy 確定（FR-4・PM級）

V-6 の裏取り結果により、CASPAR 段階移行の分岐を確定する。

### 分岐 (b): 公式挙動が自前運用の想定と一致する場合
- **C-3**: 8エージェント定義（[.claude/agents/](../../../.claude/agents/) の8ファイル）に `memory: project` フロントマターを付与
- **C-2 / FR-1.2**: CLAUDE.md「Subagent Persistent Memory」節を「公式 `memory:` 機構を利用」へ更新
- コミット単位: ①8エージェント frontmatter ②CLAUDE.md 記述 を分離

### 分岐 (c): 不一致 / 不明の場合
- 現行の自前運用（CLAUDE.md 指示による自発書込）を維持
- **C-2 / FR-1.2**: CLAUDE.md の陳腐化記述（「公式フロントマター機能ではない」）のみ、
  「同一パスを公式 `memory:` もサポートするが、LAM は意図的に自前運用を採用」と事実に即して修正
- C-3（frontmatter 付与）は見送り、見送り理由を記録
- コミット単位: CLAUDE.md 記述のみ単独

> どちらの分岐でも FR-1.2 は満たされる。確定は **人間承認必須**（V-6 結果を提示して判断を仰ぐ）。

## 6. Wave 1 のコミット分割（RQ-3 細分化方針）

```
C1: FR-3 裏取り結果の記録（docs/artifacts/research/ 追記）
C2: FR-1.1 pre-compact.py コメント是正（PG）
C3: FR-2 _hook_utils キー是正（条件付き・SE）※ V-1 が現状維持なら省略
C4: FR-4 分岐確定 — agent frontmatter または CLAUDE.md 記述（PM承認後）
C5: FR-1.2 CLAUDE.md 記述更新（C4 と同方針）
```

## 7. Wave 2 設計 — 新機能採用（FR-5）

裏取り（V-3/V-7/V-8）完了後に着手。優先度高→中→低（昇格判断後）の順。
**適用対象は既存7スキル `.claude/skills/*/SKILL.md` に限定**（DQ-2 = 案A 確定）。
commands 11本の Skills 化は本 Wave に含めず、Wave 3 へ分離（§7.5）。

| 優先 | 機能 | 対象ファイル | 変更概要 |
|:----:|------|-------------|----------|
| 高 | `paths`（自動起動） | `.claude/skills/*/SKILL.md`（7スキル） | 対象パターンに応じた自動適用を frontmatter で宣言（例: spec-template に `docs/specs/*.md`） |
| 高 | `permissionDecision: "defer"` | `.claude/settings.json` + `pre-tool-use.py` | 既存 ask ガードの一部を settings 委譲へ |
| 中 | `model` 上書き | `.claude/skills/*/SKILL.md` / `.claude/agents/*.md` | 下位モデル委譲を frontmatter で恒久化 |
| 中 | `when_to_use` / `allowed-tools` | `.claude/skills/*/SKILL.md` | 起動精度・ツール最小権限の明示 |
| 低→要調査 | `isolation: worktree` / `background` | `.claude/agents/*.md`（並列レビュー系） | V-7 結果で昇格判断 |
| 低→要調査 | `effort.level` / 新 hook ハンドラ | `.claude/hooks/*.py` + settings | V-8 結果で昇格判断 |

各機能を独立コミットとする（機能名 → 1コミット）。`paths` と `defer` は影響が settings/権限に及ぶため、
変更前に該当差分マッピング（[diff-skills-subagents.md](diff-skills-subagents.md) / [diff-mcp-settings.md](diff-mcp-settings.md)）を再読。

## 7.5. Wave 3 設計 — commands → skills 移行（C-1 解消・新規）

### 背景・方針（2026-05-28 ユーザー承認）
公式仕様上、`.claude/commands/` は「Skills に統合済み・引き続き動作」とされ、新フロントマター機能は
すべて Skills 側にのみ実装される（出典: [20-anthropic-official-spec.md:904](../../artifacts/research/2026-05-27-cc-spec-survey/20-anthropic-official-spec.md)）。
commands は機能凍結された互換シムであり、Anthropic は漸次縮小に向かうとの推論に基づき、
**後の手戻りを避けるため今のうちに 11本を Skills 形式へ移行する**。Wave 2 で 7スキルへの新機能適用を
実証してから着手する。

### 質的注意点（クリティカル）— 起動セマンティクスの判定
commands は **Claude が自動起動しない**が、skills は **自動起動しうる**（`disable-model-invocation` / `user-invocable` で制御）。
これは単なる量的移行ではなく、移行作業の核は **各コマンドの起動方針を1本ずつ判定すること**:

- **手動限定を維持すべきもの**（例: `ship`, `quick-save`, `quick-load`, `retro`, `wave-plan` 等の運用系）
  → `disable-model-invocation: true` を付与し、移行前と同じ「人間が明示起動」を保証
- **自動起動を意図的に活用してよいもの**（移行後に新たに享受できる挙動変化）
  → 個別に妥当性を判断のうえ自動起動を許可（C-1 移行を機に LAM の運用改善余地として検討）

> 移行前は commands だったため自動起動は考慮対象外だった。skills 化後はこの挙動変化を
> **意図的に利用する選択肢が生まれる**ため、1本ごとに「手動維持／自動活用」を設計判断する（PM級）。

### 対象・コミット単位
- 対象: `.claude/commands/*.md`（11本）→ `.claude/skills/<name>/SKILL.md` へ
- 1本1コミット（起動セマンティクス判定 + フロントマター付与）。同名スキルとの競合がないか移行前に確認
- 回帰確認: 既存テスト + 各コマンドの手動起動が従来どおり機能するか

## 8. Success Criteria（要件 SC-1〜SC-5 への対応）

| SC | 検証方法 |
|----|----------|
| SC-1（要更新7件） | §7 トレーサビリティ表で全件「是正済み/対応不要記録」を確認 |
| SC-2（未確認5件+α） | §3 の V-1〜V-8 全件にラベル付与 |
| SC-3（Memory 確定） | §5 の分岐が1つに確定し CLAUDE.md 反映 + 人間承認ログ |
| SC-4（回帰なし） | `.venv/Scripts/python.exe -m pytest`（576 passed / 20 skipped 相当）が回帰なし |
| SC-5（採用機能列挙） | §7 表に対象ファイル・変更概要が記載済み |

## 9. Alternatives Considered

- **即時全面移行（公式 memory へ一括移行）**: BALTHASAR 指摘の Zero-Regression リスクで却下。V-6 裏取り前の移行は推測実装に該当。
- **現状維持固定（陳腐化記述のみ修正）**: 新機能の効果（特に RQ-2 低優先度）を享受できず、ユーザー方針「できれば採用」に反するため却下。
- **単一 Wave 一括実行**: コミット粒度が粗くなりレビュー困難。RQ-3 で分割を承認済み。

## 10. 未解決質問（design レベル）→ 全て解決済み（2026-05-28）

- ~~DQ-1~~: **解決**。V-1 が `tool_response` 正なら FR-2 は確認記録のみ・コード変更なしを既定とする（ユーザー承認）。
- ~~DQ-2~~: **解決**。Wave 2 の `paths` は既存7スキルに限定（案A）。commands 11本の Skills 化は
  Wave 3 として分離（§7.5）。移行後に自動起動挙動を意図的に活用する選択肢も Wave 3 で個別判断する。
