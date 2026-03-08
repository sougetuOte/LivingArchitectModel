# Upstream First（上流仕様優先）原則

## 概要

Claude Code の hooks、settings、permissions 等のプラットフォーム機能を実装・修正する際は、
**実装前に最新の公式ドキュメントを確認する**こと。

## 背景

Claude Code は活発に開発されており、設定書式やAPI が頻繁に変更される。
過去の記憶や既存実装に基づいて書くと、旧書式で実装してしまい手戻りが発生する。

## ルール

### 必須: 実装前の仕様確認

以下のいずれかに該当する変更を行う前に、公式ドキュメントを確認すること:

- `.claude/settings.json`（permissions, hooks 等）
- `.claude/hooks/` 配下のスクリプト（入出力形式、イベントタイプ）
- skills / subagents のフロントマター
- MCP サーバー設定

### 確認先

| 対象 | 公式ドキュメント |
|------|----------------|
| Hooks | https://code.claude.com/docs/en/hooks |
| Settings | https://code.claude.com/docs/en/settings |
| Permissions | https://code.claude.com/docs/en/permissions |
| Skills | https://code.claude.com/docs/en/skills |
| Sub-agents | https://code.claude.com/docs/en/sub-agents |

### 確認手順

1. WebFetch で該当ページを取得
2. 現行実装との差分を特定
3. 差分があれば修正方針をユーザーに報告
4. 承認後に実装

### 適用タイミング

- Wave の開始時（新しい hook/settings を実装する前）
- 起動時エラーが発生した時
- プラットフォーム機能に関する変更を行う時

## 権限等級

本ルールファイル自体の変更: **PM級**
