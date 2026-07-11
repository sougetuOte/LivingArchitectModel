# R-1 W-R4 S3-T4 hooks 統合 変更記録 (2026-07-11)

> 詰まり仮説: 「なぜ pre-tool-use.py だけ out-of-root パターンを持ち、post-tool-use.py の
> キャッシュ判定には無いのか」で次に hook を触る開発者は詰まる。
> 実況第 1 文: 開発者は `_PM_PATTERNS` と `_PM_PATH_PATTERNS_FOR_CACHE` の 2 つの定義を
> 見比べ、内容がほぼ同じなのに 1 個だけ多い pre 側の out-of-root エントリに気づいて
> 「片方の更新漏れでは？」と手を止める（Fable-Alembic L3 §5.4 ガード4 準拠 / 受け手 =
> 次に hooks/*.py を触る開発者・制約 = 設計意図のコメントを読まずにコードだけ見ている）。

対応 tracker issue: `docs/artifacts/r-1-audit-tracker.md` R1-033 / R1-034 / R1-I18
（W-R4 S3-T4 消化対象）

## 1. R1-034 + R1-I18: PM パターン重複統合

### 問題

- `post-tool-use.py` の `_PM_PATH_PATTERNS_FOR_CACHE`（L55-61）と
  `pre-tool-use.py` の `_PM_PATTERNS`（L92-99）が手書きで別々に複製されており
  （4 pattern）、片方だけ更新すると PM 級判定とセッションスコープ降格キャッシュ
  判定が drift するリスクがあった。
- out-of-root pattern（`^__out_of_root__/`）は pre 側のみが持ち、post 側の
  キャッシュ判定に含まれない非対称設計だったが、これが意図的か未検証かが
  ドキュメント上判別できなかった（R1-I18）。

### 修正

- `.claude/hooks/_hook_utils.py` に `_PM_PATH_PATTERNS`（path-only / out-of-root
  を含まない 4 pattern のタプル）と `is_pm_path_pattern(path_str) -> bool` を新設。
- `.claude/hooks/pre-tool-use.py`: `_PM_PATTERNS` を `_hook_utils._PM_PATH_PATTERNS`
  由来のリスト + ローカル定義の out-of-root pattern の結合に変更。out-of-root を
  ローカルに残す理由をコメントで明示（下記「設計意図」参照）。
- `.claude/hooks/post-tool-use.py`: `_PM_PATH_PATTERNS_FOR_CACHE = _PM_PATH_PATTERNS`
  （`_hook_utils` からの import をそのまま再エクスポート）に置換。

### 設計意図の明示化（R1-I18 の解消）

out-of-root（project_root 外のパス）は信頼度が低いパスであるため、承認後も
セッションスコープ降格キャッシュ（`.session-pm-edit-cache.json`）の対象にしない
**安全側の意図的設計**であることをコードコメントで明示した。結果として
out-of-root パス書込は同一セッション内でも毎回 PM ダイアログが再表示される
（実害なし）。この非対称性は R1-034 と一体で消化し、キャッシュ対象化はしない
方針で確定した。

### テスト

`.claude/tests/hooks/test_pm_patterns_unified.py`（新規 7 テスト）:
- `_hook_utils._PM_PATH_PATTERNS` の存在・件数
- `is_pm_path_pattern()` の動作
- pre / post 両モジュールの path-only pattern 集合が `_hook_utils` と完全一致
- pre 側のみ out-of-root pattern を保持（R1-I18 非対称性の意図的維持を回帰保護）
- post 側キャッシュ判定は out-of-root を含まない
- pre / post が `_hook_utils._PM_PATH_PATTERNS` と同一オブジェクトを import
  している（identity 一致 = 手書き複製ではないことの証跡）

## 2. R1-033: settings.json の python3 hardcode 環境非依存化

### PM 級編集宣言

`.claude/settings.json` の L74/80/86/91/96（hook 起動コマンド 5 箇所）を編集。
単一 Edit（replace_all なし・旧 hooks セクション全体を新セクションに置換）で
`python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/<hook>.py` を
`bash -c 'command -v python3 >/dev/null 2>&1 && python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/<hook>.py || python "$CLAUDE_PROJECT_DIR"/.claude/hooks/<hook>.py'`
形式の fallback シェルに統一した。

### 問題

CLAUDE.md は実行環境を「Windows 11 Pro + Git Bash」と明記するが、素の
Windows Python installer は `python3` エイリアスを提供しない（現行開発環境は
pyenv-win 経由で偶然解決していたため、これまで顕在化しなかった）。将来の環境
変更・新規 contributor 環境で hook 起動コマンド自体が silent failure し、
permission システム全体（PG/SE/PM 判定）が機能しなくなる構造的リスクがあった。

### 修正

推奨修正方針 (b)（`command -v python3 >/dev/null && python3 ... || python ...`
fallback シェル）を採用。`python3` が利用可能な環境ではこれまで通り `python3`
で起動し、利用不可能な環境（素の Windows Python installer 等）では `python`
にフォールバックする。

### テスト

`.claude/tests/hooks/test_settings_hook_portability.py`（新規 4 テスト）:
- hook command が 5 件存在する（回帰前提の確認）
- 全 command に `command -v python3` の可用性チェックが含まれる
- 全 command に `python3` 以外への fallback 分岐（`|| python ...`）が含まれる
- fallback 化後も各 hook が正しいスクリプトパスを参照し続けている

### 実行確認（Refactor ステップ）

```bash
export CLAUDE_PROJECT_DIR="$(pwd)"
echo '{"tool_name":"Read","tool_input":{"file_path":"README.md"}}' | \
  bash -c 'command -v python3 >/dev/null 2>&1 && python3 "$CLAUDE_PROJECT_DIR"/.claude/hooks/pre-tool-use.py || python "$CLAUDE_PROJECT_DIR"/.claude/hooks/pre-tool-use.py'
# exit=0 （PG 級 Read ツールで stdout 出力なし・正常終了を確認）
```

`.claude/settings.json` は JSON として有効であることも `json.load()` で確認済み。
settings.json は自動 reload されないため、次回セッション開始時に実 hook 起動が
新 fallback シェル経由で動作することは本 Task の範囲外（次回セッションで確認）。

## 3. 影響範囲・回帰確認

| 対象 | 結果 |
|---|---|
| `.claude/tests/hooks/`（新規 11 + 既存 13） | 24 passed |
| `.claude/hooks/tests/` + `.claude/hooks/analyzers/tests/` | 951 passed / 1 failed（`test_distill_lessons.py::TestSmallTaskRoute::test_small_task_grader_only_input_flag` — 本 Task 対象外ファイル `distill_lessons.py` の既存失敗。本セッションで一切変更していないことを確認済み・未修正のまま報告） |

## 4. 変更ファイル一覧

- `.claude/hooks/_hook_utils.py`（`_PM_PATH_PATTERNS` 定数 + `is_pm_path_pattern()` 追加 / SE 級）
- `.claude/hooks/pre-tool-use.py`（`_PM_PATTERNS` を `_hook_utils` 由来に置換 / SE 級）
- `.claude/hooks/post-tool-use.py`（`_PM_PATH_PATTERNS_FOR_CACHE` を `_hook_utils` 由来に置換 / SE 級）
- `.claude/settings.json`（hook 起動コマンド 5 箇所を fallback シェルに変更 / **PM 級**）
- `.claude/tests/hooks/test_pm_patterns_unified.py`（新規 / SE 級）
- `.claude/tests/hooks/test_settings_hook_portability.py`（新規 / SE 級）
