# goal-driven デモ・スモークテスト成果物

`goal-driven` スキル（B-3）の実機検証に関する成果物を格納するディレクトリ。

## W1-T3 スモークテスト結果

| 項目 | 値 |
|------|-----|
| 実施日時 | 2026-06-13 07:06 |
| task_id | gd-smoke-20260613-001 |
| ルート | 小タスク（small） |
| l1_tokens | 30k程度（load時60k終了時90k） |
| total_tokens（state 累積） | 100（スタブ固定値） |
| 実測 subagent 消費 | L3: 26,305 / grader: 22,722 |
| フロー完走 | [1]→[2]→[4]→[5] |
| 結果 | **合格** |

- 実行ログ: `smoke-test-20260613.log`
- grader ログ: `.claude/logs/gd/gd-smoke-20260613-001-loop1-grader.json`
- 手順書（SSOT）: `smoke-test-runbook.md`

## ファイル一覧

| ファイル | 説明 |
|---------|------|
| `smoke-test-runbook.md` | W1-T3 実行手順書（PM 向け） |
| `smoke-test-20260613.log` | W1-T3 実行ログ |
| `smoke-hello.txt` | スモークタスク成果物（固定文字列 `smoke-test-ok`） |
