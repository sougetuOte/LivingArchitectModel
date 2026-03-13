# テスト結果ファイル出力ルール

## 概要

TDD 内省パイプライン v2 の基盤として、テスト実行結果を構造化ファイルに出力することを必須とする。

## ルール

テストフレームワークを導入・変更する際は、以下を必ず行うこと:

1. **JUnit XML 形式**の結果ファイルを `.claude/test-results.xml` に出力する設定を追加
2. `.gitignore` に `.claude/test-results.xml` を追加

## 理由

PostToolUse hook がテスト成否を判定するために、構造化された結果ファイルが必要。
Claude Code の PostToolUse 入力には exit code が含まれないため、
テストフレームワーク自身が出力する結果ファイルが唯一の信頼できる情報源となる。

## 言語別設定リファレンス

### Python (pytest)

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "--junitxml=.claude/test-results.xml"
```

### JavaScript/TypeScript (Jest)

```json
{
  "jest": {
    "reporters": [
      "default",
      ["jest-junit", {
        "outputDirectory": ".claude",
        "outputName": "test-results.xml"
      }]
    ]
  }
}
```

devDependencies に `jest-junit` を追加すること。

### JavaScript/TypeScript (Vitest)

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    reporters: ['default', 'junit'],
    outputFile: { junit: '.claude/test-results.xml' },
  },
});
```

### Go

標準の `go test` は JUnit XML を出力しない。`gotestsum` を使用:

```bash
gotestsum --junitfile .claude/test-results.xml ./...
```

インストール: `go install gotest.tools/gotestsum@latest`

### Rust

`cargo-nextest` または `cargo2junit` を使用:

```bash
# cargo-nextest
cargo nextest run --message-format libtest-json | nextest-to-junit > .claude/test-results.xml

# cargo2junit
cargo test -- -Z unstable-options --format json | cargo2junit > .claude/test-results.xml
```

### その他の言語

上記に該当しない言語・フレームワークの場合も、JUnit XML 形式での出力手段を調査し、
同一パス (`.claude/test-results.xml`) に出力すること。
大半のテストフレームワークは JUnit XML レポーターを持つか、変換ツールが存在する。

## 適用タイミング

- BUILDING フェーズでテストフレームワークを初めて導入するとき
- テストフレームワークを変更・追加するとき
- 新しい言語をプロジェクトに追加するとき

## 結果ファイルが存在しない場合

PostToolUse hook はテストコマンド検出後に `.claude/test-results.xml` を探す。
ファイルが存在しない場合は WARNING ログを出力し、TDD パターン記録をスキップする。
テスト自体の動作には影響しない。

## 権限等級

- 本ルールファイルの変更: **PM級**
- テストFW設定の追加（本ルールに従った設定変更）: **PG級**

## 参照

- 仕様書: `docs/specs/tdd-introspection-v2.md`
- 信頼度モデル: `.claude/rules/auto-generated/trust-model.md`
