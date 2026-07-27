# Rule 001: SESSION_STATE.md 編集時の SessionStateParser fallback 保守

**生成日**: 2026-07-05
**承認日**: 2026-07-05
**観測回数**: 5 (2026-06-27, 2026-07-05, 2026-07-06, 2026-07-07, **2026-07-27**)
**ステータス**: approved (2026-07-06 R-1 拡張実施 / 2026-07-07 テスト側同期完了 / **2026-07-27 観測 #5 は原因が異なる** → 下記「構造的論点」)
**last_matched**: **2026-07-27**
**閾値到達**: `trust-model.md` の初期閾値 2 回に到達 / 3 回目発火で **fallback regex 恒久拡張** を実施 (R-1 W-R1 S1 T6)

## 根拠パターン

| # | 日付 | テスト名 | 失敗内容 |
|---|------|---------|---------|
| 1 | 2026-06-27 | `test_parse_real_session_state_contains_b5_milestone` + `_contains_wave` | SESSION_STATE.md 編集で B-N / Wave N パターンが欠落し、`SessionStateParser` の fallback 正規表現が空マッチ |
| 2 | 2026-07-05 | 同上 | ヘッダから `B-5 BUILDING 着手` 表記を除去した副次影響で再発 |
| 3 | 2026-07-06 | 同上 | R-1 Milestone 遷移により SESSION_STATE.md が `R-1` / `W-R1` 系表記のみとなり、B-N 専用 fallback regex が空マッチ (Fable→Opus 実装ギャップ #1 の実測発火) |
| 4 | 2026-07-07 | `test_parse_real_session_state_contains_b5_milestone` (旧名) | T6 で parser regex は `[A-Z]-\d+` に恒久拡張済みだったが、**テスト側の literal `"B-5"` assert が未同期のまま残存** (T6 実装ギャップの残滓)。R-1 期 SESSION_STATE で発火し parser は `['R-1']` を正常抽出 = SESSION_STATE 側は本ルール準拠・**テストが根本原因**。テストを `test_parse_real_session_state_contains_milestone` に改名し milestone 非依存のパターン検証 (`[A-Z]-\d+` fullmatch) に更新 (W-R2 S2 / 2026-07-07) |
| **5** | **2026-07-27** | `test_parse_real_session_state_contains_wave` | **原因が #1-#4 と異なる。** parser もテストも正常で、**SESSION_STATE.md から Wave 表記が実際に消えていた**。L1 が `/quick-save` で全面書き換えを行った際、セッション実績行から `（Wave 1 / Wave 2）` を落とした。**かつ本ルールが定める「編集後の retention 確認」を実行しなかった** ため、後続の追記時まで発覚が遅れた。すなわち **parser の欠陥ではなく確認手順の不履行**。復元して緑化 (49 passed)。→ 下記「構造的論点」 |

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

## 構造的論点（2026-07-27 / 観測 #5 / **未解決 · 記録のみ**）

観測 #5 は本ルールの妥当性そのものに疑問を提起する。**記録に留め、対処は次の発火まで保留する。**

### 論点: Milestone・Wave 不在期に、retention は痕跡テキストの保持を強制する

2026-07-26 の M-1 完了以降、プロジェクトは **Milestone を持たない**（`SESSION_STATE.md` は `Milestone: なし` と記載）。当然 Wave も存在しない。

このとき本ルールが要求する Milestone 表記 / Wave 表記は、**現在の状態の記述ではなく過去セッションの履歴参照としてしか残せない**。観測 #5 で消えたのも実績欄の `（Wave 1 / Wave 2）` であり、L1 はそれを「冗長な括弧書き」として落とした —— **意味的には正しい編集だった**。

つまり本ルールは今、次の性質を持つ:

- **履歴を整理するたびに発火する**（履歴こそが唯一の Wave 表記の在処であるため）
- **痕跡テキスト（vestigial text）の保持を強制する**方向に働く
- これは `fable-l3-protocol.md` §9 が扱う「観測チャンネル」の問題と同型で、**計器が測れる形を保つために対象を変形させている**

### なぜ即座に恒久解へ進まないか

`trust-model.md` §「N 回目発火時の恒久解検討」は N=3 で構造的恒久解の検討を求めており、本ルールは 2026-07-06 に regex 汎化（`B-\d+` → `[A-Z]-\d+`）でそれを実施済みである。**観測 #5 は同じ系列の 5 回目ではなく、別系列の 1 回目**（parser 追随の失敗ではなく、対象の消滅）と読むのが正確である。

別系列として数え直すなら閾値未到達であり、**本節は「1 回目の記録」に当たる**。次に同型（Milestone/Wave 不在に起因する retention 失敗）が起きた時点で恒久解を検討する。想定される選択肢を先に置いておく（**採用は次回 / 今は決めない**）:

- (a) parser の fallback を「不在も正常」として扱えるようにし、テストを retention 検査から外す
- (b) 本ルールの適用条件に「Milestone が存在する期間」を加える
- (c) `SESSION_STATE.md` に Milestone/Wave 欄を構造として常設し、`なし` を明示的な値として書く

**カウント単位の注記**: `trust-model.md` は検出イベント単位で数えると定める。本節の「別系列」判定は**原因の異同に基づく判断**であり、単位の変更ではない。判定が誤りであれば観測 #5 は同系列の 5 回目となり、恒久解の検討は既に済ませておくべき状態になる —— **この読み替えの可否自体が PM 級の判断**として残る。

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
