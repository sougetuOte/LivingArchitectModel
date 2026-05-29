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

1. context7 MCP で該当ドキュメントを検索・取得（推奨）
2. context7 が利用不可 or 対応外の場合は WebFetch でフォールバック（対話モードのみ）
3. 現行実装との差分を特定
4. 差分があれば修正方針をユーザーに報告
5. 承認後に実装

> **注意**: `/full-review` 等の自動フロー内では WebFetch を使用しない（無応答リスクのため）。
> context7 が利用不可の場合は仕様確認をスキップし、対話モードでの確認を案内する。

### 適用タイミング

- **PLANNING フェーズ（設計書執筆時）**: 設計書・ADR・タスク定義に API キー名・フロントマター書式・
  設定キー・イベント名を**記述する前**に裏取りする（下記「設計フェーズへの適用」参照）
- Wave の開始時（新しい hook/settings を実装する前）
- 起動時エラーが発生した時
- プラットフォーム機能に関する変更を行う時

### 設計フェーズへの適用（PLANNING）

upstream-first は「実装前」だけでなく **「設計書に書く前」** にも適用する。
設計書に未検証の API キー名・書式を書くと、実装フェーズまで誤りが温存され手戻りが拡大する。

- 設計書・タスク定義に具体的な **キー名 / 書式 / 設定値 / イベント名** を記述する場合は、
  その時点で context7（不可なら対話モードで WebFetch）により裏取りする
- 裏取り未済のまま書く場合は「**未確認（要裏取り）**」と明示し、確定前に実装へ進まない
- 抽象的な方針記述（「自動起動を制御する」等）は裏取り不要。具体キー名（`disable-model-invocation` 等）に
  踏み込む場合のみ必須

> **根拠（cc-spec-alignment Wave 3 の教訓）**: design §7.5 が存在しないキー `user-invocable` に言及していた。
> 実体は `disable-model-invocation: true` であり、設計時に書式を裏取りしていれば設計書段階で正せた。

## 権限等級

本ルールファイル自体の変更: **PM級**

## Wave 開始前の一括すり合わせ（推奨）

プラットフォーム仕様変更の影響は後続 Wave に波及する。
個別 Wave 着手時に都度修正するのではなく、
影響が判明した時点で**全 Wave の設計書・タスク定義を一括更新**すること。

### 対象範囲

- **更新すべき**: 設計書のプラットフォーム API 依存箇所、タスク定義の完了条件
- **更新不要**: 要件書（「何をやるか」でありAPI書式に依存しない）、ADR（決定の記録）、ビジネスロジック部分
