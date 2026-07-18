# Rule 001: SESSION_STATE.md 編集時の SessionStateParser fallback 保守

**生成日**: 2026-07-05
**承認日**: 2026-07-05
**観測回数**: 4 (2026-06-27, 2026-07-05, 2026-07-06, 2026-07-07)
**ステータス**: approved (2026-07-06 R-1 拡張実施 / 2026-07-07 テスト側同期完了)
**last_matched**: 2026-07-07
**閾値到達**: `trust-model.md` の初期閾値 2 回に到達 / 3 回目発火で **fallback regex 恒久拡張** を実施 (R-1 W-R1 S1 T6)

## 根拠パターン

| # | 日付 | テスト名 | 失敗内容 |
|---|------|---------|---------|
| 1 | 2026-06-27 | `test_parse_real_session_state_contains_b5_milestone` + `_contains_wave` | SESSION_STATE.md 編集で B-N / Wave N パターンが欠落し、`SessionStateParser` の fallback 正規表現が空マッチ |
| 2 | 2026-07-05 | 同上 | ヘッダから `B-5 BUILDING 着手` 表記を除去した副次影響で再発 |
| 3 | 2026-07-06 | 同上 | R-1 Milestone 遷移により SESSION_STATE.md が `R-1` / `W-R1` 系表記のみとなり、B-N 専用 fallback regex が空マッチ (Fable→Opus 実装ギャップ #1 の実測発火) |
| 4 | 2026-07-07 | `test_parse_real_session_state_contains_b5_milestone` (旧名) | T6 で parser regex は `[A-Z]-\d+` に恒久拡張済みだったが、**テスト側の literal `"B-5"` assert が未同期のまま残存** (T6 実装ギャップの残滓)。R-1 期 SESSION_STATE で発火し parser は `['R-1']` を正常抽出 = SESSION_STATE 側は本ルール準拠・**テストが根本原因**。テストを `test_parse_real_session_state_contains_milestone` に改名し milestone 非依存のパターン検証 (`[A-Z]-\d+` fullmatch) に更新 (W-R2 S2 / 2026-07-07) |

パターン詳細ログ: `.claude/tdd-patterns.log` (`ANALYZED` マーカー以降)
retro 記録: `docs/artifacts/retro-B5-W8-WC-2026-07-05.md` §2.5

## ルール (2026-07-06 R-1 W-R1 S1 T6 拡張)

`SESSION_STATE.md` を編集する際は、以下を破らないこと。

- **Milestone 表記** (`\b[A-Z]-\d+\b` パターン / **任意 1 文字 prefix**): 最低 1 箇所以上残す
  - 根拠: `SessionStateParser._FALLBACK_MILESTONE_RE` (2026-07-06 拡張 / B → [A-Z])
  - 例: `B-5`, `R-1`, `S-3` 等
- **Wave 表記** (次のいずれか): 最低 1 箇所以上残す
  - `\bWave\s+\d+(?:\.\d+)?\b` (旧記法 / 例: `Wave 8`, `Wave 1.5`)
  - `\bW-[A-Z]\d+(?:\.\d+)?\b` (ハイフン記法 / 例: `W-R1`, `W-R2` / 2026-07-06 追加)
  - 根拠: `SessionStateParser._FALLBACK_WAVE_RE` + `_FALLBACK_WAVE_HYPHEN_RE`
- 編集後は以下のコマンドで retention を確認すること:

```bash
python -m pytest \
  .claude/tests/dashboard/test_session_state_parser.py::test_parse_real_session_state_contains_milestone \
  .claude/tests/dashboard/test_session_state_parser.py::test_parse_real_session_state_contains_wave
```

> 注 (2026-07-07): 旧テスト名 `test_parse_real_session_state_contains_b5_milestone` は W-R2 S2 で
> `test_parse_real_session_state_contains_milestone` に改名 (literal "B-5" assert の恒久解 / 観測 #4)。

### 拡張の根拠 (2026-07-06 / R-1 W-R1 S1 T6)

パターン発火 3 回目 (2026-07-06) は「ルール自体が構造欠陥」の実証。B-N 専用 regex は Milestone 命名体系が変わる度 (R-1 / S-1 / T-1 …) に破綻する。そのため以下 2 点を恒久解として実施:

1. `_FALLBACK_MILESTONE_RE` を `\b(B-\d+)\b` → `\b([A-Z]-\d+)\b` に拡張
2. `_FALLBACK_WAVE_HYPHEN_RE` を新設 (`\bW-([A-Z]\d+(?:\.\d+)?)\b`)

これにより SESSION_STATE.md 冒頭に「B-5 Wave 8」応急措置を残す必要がなくなり、将来の命名体系変更に対しても Milestone/Wave 抽出が破綻しない。関連: `~/.claude/projects/<>/memory/fable-spec-opus-implementation-gap.md` §事例 #1。

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
