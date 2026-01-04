# PLANNING フェーズ ガードレール

## Purpose

PLANNING フェーズにおいて、ドキュメント作成に集中させ、実装を抑制するガードレール。

## Activation

- `.claude/current-phase.md` が `PLANNING` である
- `/planning` コマンド実行後

## Approval Gates

```
requirements → [承認] → design → [承認] → tasks → [承認] → BUILDING へ
```

成果物完成時は必ず「承認」を求める。ユーザーが「承認」と言うまで次へ進まない。

## MUST NOT（禁止）

1. **実装コードの生成**: `.ts`, `.py`, `.go` 等のソースファイル作成
2. **`src/` への変更**: 実装ディレクトリへのファイル作成・編集
3. **設定ファイルの変更**: `package.json`, `pyproject.toml` 等
4. **未承認での進行**: 前サブフェーズ未承認での次サブフェーズ開始

## MAY（許可）

1. `docs/specs/`, `docs/adr/`, `docs/tasks/`, `docs/memos/` への出力
2. 既存コードの読み取り（仕様策定のため）
3. Mermaid 図表の作成
4. `.claude/states/*.json` の更新

## Warning Template

実装を求められた場合:
```
⚠️ フェーズ警告
現在は PLANNING フェーズです。
1. 仕様策定を続ける
2. /building で BUILDING に移行
3. 「承知の上で実装」と明示して続行
```

## References

- `docs/internal/01_REQUIREMENT_MANAGEMENT.md`
- `docs/internal/02_DEVELOPMENT_FLOW.md` (Phase 1)
- `docs/internal/06_DECISION_MAKING.md`
