# TDD 内省パイプライン v2 仕様書

**バージョン**: 1.0
**作成日**: 2026-03-13
**ステータス**: approved
**前提**: v4.0.0 免疫系アーキテクチャ（`docs/design/v4.0.0-immune-system-design.md`）

---

## 1. 背景と課題

### 1.1 v1 の問題

v4.0.0 で設計された TDD 内省パイプラインは、PostToolUse hook の `tool_response` から
`exitCode` を取得してテスト成否を判定する設計だった。

しかし、**Claude Code の PostToolUse 入力には `exitCode` フィールドが存在しない**ことが
2026-03-13 のデバッグで判明した。実際の `tool_response` 構造:

```json
{
  "stdout": "...",
  "stderr": "...",
  "interrupted": false,
  "isImage": false,
  "noOutputExpected": false
}
```

この結果、`_extract_exit_code()` は常に空文字を返し、
TDD パターン記録が一切動作していなかった（実績ゼロ）。

### 1.2 v2 の方針

exit code に依存せず、**テストフレームワーク自身が出力する結果ファイル**を情報源とする。
パターン分析は自動化せず、**`/retro` に統合**して人間のタイミングで実施する。

---

## 2. アーキテクチャ

### 2.1 データフロー

```
テスト実行（pytest, jest, go test 等）
    │
    ├──→ JUnit XML 結果ファイル (.claude/test-results.xml)
    │
    ▼
[PostToolUse hook]
    ├── テストコマンド検出
    ├── 結果ファイル読取（JUnit XML パース）
    ├── pass/fail を tdd-patterns.log に1行記録
    └── FAIL→PASS 遷移時に systemMessage で /retro 推奨（通知A）

[Stop hook]（ループ終了時）
    ├── tdd-patterns.log の未分析エントリ数チェック
    └── 閾値超えなら /retro 推奨通知（通知B）

[/retro]（人間が実行）
    ├── tdd-patterns.log を読込・集計
    ├── 繰り返し失敗パターンを特定
    └── ルール候補を提案（人間が承認/却下）
```

### 2.2 責務分離

| コンポーネント | 責務 | 権限等級 |
|--------------|------|---------|
| テストFW設定 | 結果ファイル出力 | PG（設定のみ） |
| PostToolUse | 記録 + 通知A | PG（自動） |
| Stop hook | 通知B | PG（自動） |
| `/retro` | 分析 + ルール候補提案 | PM（人間実行） |

---

## 3. テスト結果ファイル

### 3.1 統一出力先

すべての言語で `.claude/test-results.xml`（JUnit XML 形式）に出力する。

### 3.2 言語別設定例

#### Python (pytest)

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--junitxml=.claude/test-results.xml"
```

#### JavaScript/TypeScript (Jest)

```json
// package.json
{
  "jest": {
    "reporters": [
      "default",
      ["jest-junit", { "outputDirectory": ".claude", "outputName": "test-results.xml" }]
    ]
  }
}
```

`jest-junit` パッケージの devDependencies 追加が必要。

#### JavaScript/TypeScript (Vitest)

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    reporters: ['default', 'junit'],
    outputFile: { junit: '.claude/test-results.xml' },
  },
});
```

#### Go

Go は標準で JUnit XML を出力しない。`gotestsum` を使用:

```bash
gotestsum --junitfile .claude/test-results.xml ./...
```

`go install gotest.tools/gotestsum@latest` が必要。

#### Rust (cargo-nextest)

```bash
cargo nextest run --message-format libtest-json | nextest-to-junit > .claude/test-results.xml
```

または `cargo2junit`:

```bash
cargo test -- -Z unstable-options --format json | cargo2junit > .claude/test-results.xml
```

#### Make (ラッパー)

Makefile の `test` ターゲット内で上記コマンドを呼び出す。

### 3.3 .gitignore

`.claude/test-results.xml` を `.gitignore` に追加すること。

---

## 4. PostToolUse の変更

### 4.1 テスト結果読取

`_handle_test_result()` を以下のロジックに変更:

1. テストコマンドを検出（既存の `_is_test_command()` を流用）
2. `.claude/test-results.xml` の存在を確認
3. JUnit XML をパースして `tests`, `failures`, `errors` を取得
4. `tdd-patterns.log` に記録

```
{timestamp}\t{PASS|FAIL}\t{framework}\ttests={N} failures={N}\t"{失敗テスト名 要約}"
```

PostToolUseFailure イベント（テストコマンドが非ゼロ exit で失敗）の場合、
JUnit XML は古い結果が残っている可能性があるため読み取らず、直接 FAIL を記録する:

```
{timestamp}\tFAIL\t{framework}\ttests=? failures=?\t"PostToolUseFailure event"
```

5. 前回 FAIL → 今回 PASS の場合、systemMessage で通知A を出力

### 4.2 通知A: FAIL→PASS 遷移時

PostToolUse の stdout に以下の JSON を出力:

```json
{
  "systemMessage": "TDD パターンが記録されました。セッション終了時に /retro でパターン分析を推奨します。"
}
```

これは提案であり、強制ではない。Claude に情報として伝わるのみ。

### 4.3 JUnit XML パーサー

標準ライブラリ `xml.etree.ElementTree` で十分。最小限のパース:

```python
import xml.etree.ElementTree as ET

def parse_junit_xml(path: Path) -> dict:
    tree = ET.parse(path)
    root = tree.getroot()
    # <testsuites> or <testsuite> がルート
    if root.tag == "testsuites":
        suites = root.findall("testsuite")
    else:
        suites = [root]

    total_tests = sum(int(s.get("tests", 0)) for s in suites)
    total_failures = sum(int(s.get("failures", 0)) for s in suites)
    total_errors = sum(int(s.get("errors", 0)) for s in suites)

    # 失敗テスト名の収集
    failed_names = []
    for suite in suites:
        for tc in suite.findall("testcase"):
            if tc.find("failure") is not None or tc.find("error") is not None:
                failed_names.append(tc.get("name", "unknown"))

    return {
        "tests": total_tests,
        "failures": total_failures + total_errors,
        "failed_names": failed_names,
    }
```

---

## 5. Stop hook の変更

### 5.1 通知B: 未分析パターン通知

ループ終了（Green State 達成）時に `tdd-patterns.log` をチェック:

1. ファイルが存在し、FAIL→PASS 遷移が1件以上あるか確認
2. 最終分析日時（`tdd-patterns.log` 内の `ANALYZED` マーカー）以降のエントリ数をカウント
3. 未分析エントリが1件以上あれば、ループ終了ログに注記

```
_log(log_file, "INFO", "TDD patterns: N件の未分析パターンあり。/retro を推奨。")
```

これはログ出力のみ。ループの動作には影響しない。

---

## 6. /retro への統合

### 6.1 新ステップ: TDD パターン分析

`/retro` の Step 2 と Step 3 の間に挿入:

```
Step 2.5: TDD パターン分析
  1. .claude/tdd-patterns.log を読込
  2. FAIL→PASS 遷移ペアを抽出
  3. 同一ファイル・同一テスト名の繰り返しを集計
  4. 頻出パターン（2回以上）があれば:
     - パターンの要約を提示
     - ルール候補（draft）を提案
     - 人間が承認/却下を判断
  5. 分析済みマーカー（ANALYZED タイムスタンプ）を tdd-patterns.log に追記
```

### 6.2 ルール候補の出力先

従来通り `.claude/rules/auto-generated/draft-NNN.md`。
ただし生成タイミングが「PostToolUse の自動生成」から「/retro 内での人間との対話」に変更。

---

## 7. 移行計画

### 7.1 v1 からの変更点

| 項目 | v1 | v2 |
|------|----|----|
| テスト成否の判定 | exit code（動作せず） | JUnit XML 結果ファイル |
| パターン記録 | PostToolUse 自動 | PostToolUse 自動（情報源が変更） |
| カウント・閾値判定 | PostToolUse 自動（未実装） | /retro で人間が実行 |
| ルール候補生成 | 自動（未実装） | /retro 内で対話的に |
| 通知 | なし | systemMessage（A: 遷移時、B: ループ終了時） |

### 7.2 実装タスク

1. `.claude/rules/test-result-output.md` 作成（本仕様と同時）
2. `pyproject.toml` に `--junitxml` 設定追加
3. `.gitignore` に `.claude/test-results.xml` 追加
4. `post-tool-use.py` の `_handle_test_result()` を結果ファイル方式に改修
5. `post-tool-use.py` に JUnit XML パーサー追加
6. `post-tool-use.py` に通知A（systemMessage）追加
7. `lam-stop-hook.py` に通知B（未分析パターンチェック）追加
8. `/retro` スキルに Step 2.5 追加
9. テスト更新（`test_post_tool_use.py`）
10. 信頼度モデル (`trust-model.md`) の更新

### 7.3 v1 コードの扱い

- `_extract_exit_code()`: 削除
- `_record_tdd_fail()` / `_record_tdd_pass()`: 改修（情報源を結果ファイルに変更）
- `_is_test_command()` / `_get_test_cmd_label()`: 流用

---

## 8. 注意事項

- JUnit XML のスキーマはフレームワークごとに微妙に異なる。パーサーは寛容に実装すること
- 結果ファイルが存在しない場合（設定漏れ等）は WARNING ログを出し、記録をスキップ
- `/retro` のパターン分析は提案であり、ルール化は常に人間の承認が必要（PM級）
- 通知 A/B はいずれも提案のみ。Claude の動作を変更しない
