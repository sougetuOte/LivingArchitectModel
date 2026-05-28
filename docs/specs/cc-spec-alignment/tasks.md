# タスク定義: Claude Code 仕様すり合わせ更新（cc-spec-alignment）

最終更新: 2026-05-28 / フェーズ: PLANNING（tasks）/ ステータス: **approved（2026-05-28 ユーザー承認）**
親: [requirements.md](requirements.md)（approved）/ [design.md](design.md)（approved）

## 凡例
- 等級: PG（自動）/ SE（修正後報告）/ PM（人間承認必須）
- 各タスクは原則1コミット。コミットIDは design §6 の C1〜C5 に対応。

---

## Wave 1（即時）— 裏取り → 陳腐化是正 → Memory Policy 確定

### T1-0: FR-3 裏取り（着手ゲート） — SE / コミット C1
- **対象**: V-1〜V-8（design §3）を context7 優先・WebFetch フォールバックで確認
- **成果物**: `docs/artifacts/research/2026-05-27-cc-spec-survey/` に裏取り結果を追記（各 V に「確認済み(出典)/未確認(理由)」ラベル）
- **完了条件**:
  - V-1〜V-8 全件にラベル付与（SC-2）
  - **V-1・V-2・V-6 が確定**（未確定なら後続 T1-* をブロック）
  - FR-3.2: 未確認項目は「未確認」明示、推測実装禁止
- **トレース**: FR-3.1 / FR-3.2 / FR-3.3
- **依存**: なし（Wave 1 の最初）

### T1-1: pre-compact.py コメント是正 — PG / コミット C2
- **対象**: [.claude/hooks/pre-compact.py:8](../../../.claude/hooks/pre-compact.py)
- **変更**: V-2 確認結果に基づき「公式未掲載」注記を「正式イベント」へ書換。「ブロック不可・exit 0」は維持
- **完了条件**: コメントが事実と一致 / 既存テスト回帰なし
- **トレース**: FR-1.1（H-02）
- **依存**: T1-0（V-2 確定）

### T1-2: PostToolUse 入力キー是正（条件付き） — SE / コミット C3
- **対象**: [.claude/hooks/_hook_utils.py:81-89](../../../.claude/hooks/_hook_utils.py) `get_tool_response` + [test_hook_utils.py](../../../.claude/hooks/tests/test_hook_utils.py)
- **分岐**:
  - V-1 = `tool_response` 正 → **本タスク省略**（確認記録のみ、コード変更なし）
  - V-1 = `tool_result` 正 → 両キー併存フォールバックへ是正。Red→Green でキー両系統テスト追加
- **完了条件**: 是正時 — 新旧キー両方でテスト通過 / 波及先（post-tool-use.py の TDD 記録）が機能
- **トレース**: FR-2.1 / FR-2.2（H-20）
- **依存**: T1-0（V-1 確定）

### T1-3: Memory Policy 分岐確定（PM承認ゲート） — PM
- **対象**: V-6 裏取り結果を提示し、(b)/(c) 分岐を人間が決定
- **成果物**: 決定内容と承認ログを記録（design §5）
- **完了条件**: 分岐が1つに確定（SC-3 の前段）
- **トレース**: FR-4.1
- **依存**: T1-0（V-6 確定）

### T1-4a: 分岐(b) — 8エージェントへ memory: project 付与 — PM / コミット C4
- **対象**: [.claude/agents/](../../../.claude/agents/) の8ファイル
- **変更**: フロントマターに `memory: project` を付与
- **完了条件**: 8ファイル全付与 / フロントマター構文エラーなし
- **トレース**: FR-4.2（C-3）
- **依存**: T1-3 で分岐(b)確定時のみ実行（(c)なら本タスクは「見送り・理由記録」）

### T1-4b: CLAUDE.md「Subagent Persistent Memory」節の更新 — PM / コミット C5
- **対象**: `CLAUDE.md`「Memory Policy > Subagent Persistent Memory」節
- **変更**:
  - 分岐(b): 「公式 `memory:` 機構を利用」へ更新
  - 分岐(c): 「公式 `memory:` も同一パスをサポートするが LAM は意図的に自前運用を採用」へ事実修正
- **完了条件**: 陳腐化記述（「公式機能ではない」）が解消（FR-1.2）/ 分岐方針と整合
- **トレース**: FR-1.2 / FR-4.1（C-2）
- **依存**: T1-3（分岐確定）

### Wave 1 完了判定
- SC-1（要更新のうち H-02/H-20/C-2/C-3 対応）、SC-2、SC-3、SC-4（pytest 回帰なし）を確認

---

## Wave 2（後続）— 新機能採用（既存7スキル）

各タスク1コミット。優先度高→中→低の順。着手前に diff 該当文書を再読。

### T2-1: `paths` 自動適用の付与（高） — SE
- **対象**: `.claude/skills/*/SKILL.md`（適用候補: spec-template, adr-template 等）
- **変更**: 対象パターンを `paths:` で宣言（例: spec-template → `docs/specs/*.md`）
- **完了条件**: 対象スキルが該当パスで自動適用される / 誤起動しない
- **トレース**: FR-5.1
- **依存**: T1-0（V-3）

### T2-2: `permissionDecision: "defer"` 導入（高） — SE/PM
- **対象**: `.claude/settings.json` + [.claude/hooks/pre-tool-use.py](../../../.claude/hooks/pre-tool-use.py)
- **変更**: 既存 ask ガードの一部を settings 委譲（defer）へ
- **完了条件**: 委譲後も権限境界が後退しない / hook テスト通過
- **トレース**: FR-5.1
- **依存**: T1-0 / diff-mcp-settings 再読。settings 変更は PM級

### T2-3: `model` 上書きの恒久化（中） — SE
- **対象**: `.claude/skills/*/SKILL.md` / `.claude/agents/*.md`
- **変更**: 下位モデル委譲を `model:` で宣言
- **トレース**: FR-5.1 / 依存: T1-0

### T2-4: `when_to_use` / `allowed-tools` 付与（中） — SE
- **対象**: `.claude/skills/*/SKILL.md`
- **変更**: 起動精度向上と最小権限ツール宣言
- **トレース**: FR-5.1 / 依存: T1-0

### T2-5: `isolation: worktree` / `background`（低→昇格判断） — SE/PM
- **対象**: `.claude/agents/*.md`（並列レビュー系）
- **前提**: T1-0 の V-7 で採用可・昇格と記録された場合のみ着手
- **トレース**: FR-3.3 / FR-5.1 / 依存: T1-0（V-7）

### T2-6: `effort.level` / 新 hook ハンドラ（低→昇格判断） — SE/PM
- **対象**: `.claude/hooks/*.py` + settings
- **前提**: T1-0 の V-8 で採用可・昇格と記録された場合のみ着手
- **トレース**: FR-3.3 / FR-5.1 / 依存: T1-0（V-8）

### T2-7: 選定外機能の将来候補記録 — SE
- **対象**: 本 Wave で採用しなかった新機能
- **成果物**: 将来候補として記録（FR-5.2）
- **トレース**: FR-5.2

---

## Wave 3（後続・新規）— commands → skills 移行（C-1）

design §7.5 準拠。Wave 2 で 7スキルの新機能適用を実証後に着手。

### T3-0: 移行方針の確定（起動セマンティクス判定表） — PM
- **対象**: `.claude/commands/*.md`（11本）
- **成果物**: 各コマンドを「手動限定（`disable-model-invocation: true`）」/「自動起動活用」に分類した判定表
- **完了条件**: 11本すべてに起動方針が割当 / 同名スキル競合の有無を確認
- **トレース**: C-1（FR-5 派生）/ 依存: Wave 2 完了

### T3-1〜T3-11: 各コマンドの移行（1本1コミット） — PM
- **対象**: `.claude/commands/<name>.md` → `.claude/skills/<name>/SKILL.md`
- **変更**: T3-0 の判定に従いフロントマター付与（起動制御キー含む）
- **完了条件（各本）**: 手動起動が従来どおり機能 / 自動起動方針が判定表どおり / 既存テスト回帰なし
- **トレース**: C-1 / 依存: T3-0

### Wave 3 完了判定
- 11本すべて移行済み / 各コマンドの起動挙動が判定表と一致 / SC-4 回帰なし

---

## トレーサビリティ（WBS 100% Rule 検証）

| 要件 | 対応タスク | 状態 |
|------|-----------|------|
| FR-1.1 | T1-1 | カバー |
| FR-1.2 | T1-4b | カバー |
| FR-2.1/2.2 | T1-2 | カバー |
| FR-3.1/3.2 | T1-0 | カバー |
| FR-3.3 | T1-0 → T2-5/T2-6 | カバー |
| FR-4.1 | T1-3 | カバー |
| FR-4.2 | T1-4a | カバー |
| FR-5.1 | T2-1〜T2-6 | カバー |
| FR-5.2 | T2-7 | カバー |
| FR-6.1 | 本表 | カバー |
| C-1 | T3-0〜T3-11 | カバー |

- 実装漏れ（Gap）: なし
- 孤児タスク（仕様にトレース不能）: なし

## 未解決質問
- なし（DQ-1/DQ-2 は design §10 で解決済み）
