# Rule 001: SESSION_STATE.md 編集時の SessionStateParser fallback 保守

**生成日**: 2026-07-05
**承認日**: 2026-07-05
**観測回数**: 2 (2026-06-27, 2026-07-05)
**ステータス**: approved
**last_matched**: 2026-07-05
**閾値到達**: `trust-model.md` の初期閾値 2 回に到達

## 根拠パターン

| # | 日付 | テスト名 | 失敗内容 |
|---|------|---------|---------|
| 1 | 2026-06-27 | `test_parse_real_session_state_contains_b5_milestone` + `_contains_wave` | SESSION_STATE.md 編集で B-N / Wave N パターンが欠落し、`SessionStateParser` の fallback 正規表現が空マッチ |
| 2 | 2026-07-05 | 同上 | ヘッダから `B-5 BUILDING 着手` 表記を除去した副次影響で再発 |

パターン詳細ログ: `.claude/tdd-patterns.log` (`ANALYZED` マーカー以降)
retro 記録: `docs/artifacts/retro-B5-W8-WC-2026-07-05.md` §2.5

## ルール

`SESSION_STATE.md` を編集する際は、以下を破らないこと。

- **B-N 表記** (`\bB-\d+\b` パターン): 最低 1 箇所以上残す
  - 根拠: `SessionStateParser._FALLBACK_MILESTONE_RE`
- **Wave N 表記** (`\bWave\s+\d+(?:\.\d+)?\b`): 最低 1 箇所以上残す
  - 根拠: `SessionStateParser._FALLBACK_WAVE_RE`
- 編集後は以下のコマンドで retention を確認すること:

```bash
python -m pytest \
  .claude/tests/dashboard/test_session_state_parser.py::test_parse_real_session_state_contains_b5_milestone \
  .claude/tests/dashboard/test_session_state_parser.py::test_parse_real_session_state_contains_wave
```

## 適用範囲

- 対象ファイル: `SESSION_STATE.md`（gitignore 対象・ローカル限定)
- 対象操作: `Edit` / `Write`
- 適用者: L1 / L2 (Sonnet 委譲経路含む)

## 権限等級

- 本ルールの改訂・削除: **PM 級**（`trust-model.md` 準拠）
- パターン記録の追加: **PG 級**（PostToolUse hook が自動記録）

## 寿命管理

- `last_matched`: 2026-07-05（承認と同時に初期化）
- 90 日以上マッチしない場合、`/quick-save` の Daily 記録で棚卸し対象として通知される
- 削除は PM 級承認必須

## 参照

- `.claude/rules/auto-generated/trust-model.md`（信頼度モデル / 閾値 2 の根拠）
- `.claude/rules/auto-generated/README.md`（ライフサイクル）
- `docs/artifacts/retro-B5-W8-WC-2026-07-05.md` §2.5（本ルールの生成契機）
- `docs/specs/tdd-introspection-v2.md`（TDD 内省パイプライン v2 仕様）
