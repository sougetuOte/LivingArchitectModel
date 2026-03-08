# ADR-0003: 公式仕様取得における context7 MCP vs WebFetch の使い分け

**日付**: 2026-03-09
**ステータス**: Accepted
**関連ルール**: `.claude/rules/upstream-first.md`

---

## コンテキスト

Claude Code 公式ドキュメント（code.claude.com/docs/en/*）を WebFetch で取得しようとすると、
JS レンダリングの問題で正しくコンテンツが取得できないケースがあった。
context7 MCP を使うことで回避できた。

## 判断対象

1. upstream-first ルールの確認手順を context7 MCP に統一するか
2. WebFetch でうまく処理する方法があるか
3. 両者の併用ルール

## 選択肢

### A: context7 MCP に完全統一

- **[Affirmative]**: シンプル。仕様確認の精度が上がる
- **[Critical]**: context7 は MCP サーバー依存。環境必須化で導入障壁が上がる。対応外ドキュメントもある

### B: context7 優先 + WebFetch フォールバック（段階的） — **採用**

- **[Affirmative]**: context7 の精度を活かしつつ、未設定環境でも劣化動作する。対話モードでは WebFetch をフォールバックとして利用可能
- **[Critical]**: WebFetch は自動フロー内で無応答になった場合、プログラム的にタイムアウトを設定する手段がなく、無限待機のリスクがある

### C: WebFetch のみ（現状維持）

- **[Critical]**: JS レンダリング問題が既知。`code.claude.com` で取得失敗の実績あり

## 決定

**選択肢 B を採用。** context7 MCP を「強く推奨（strongly recommended）」とし、場面に応じて使い分ける。

### 使い分けルール

| 場面 | context7 あり | context7 なし |
|------|-------------|-------------|
| full-review（自動） | context7 で確認 | スキップ + 警告 |
| planning（対話的） | context7 優先 | WebFetch 可（人間が止められる） |
| upstream-first（対話的） | context7 優先 | WebFetch 可 |

### 自動フローでの WebFetch 禁止理由

WebFetch は対話モードではユーザーが手動キャンセルできるが、`/full-review` 等の自動フローでは無応答時にプログラム的にタイムアウトを設定する手段がなく、無限待機のリスクがある。

## 結果

- `.claude/rules/upstream-first.md` — 確認手順を context7 優先に更新済み
- `.claude/commands/full-review.md` — Phase 0.5 として context7 検出 + 警告ロジック追加済み
- README — 推奨環境に context7 MCP セットアップを記載（後続タスク）
