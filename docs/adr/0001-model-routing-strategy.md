# ADR-0001: モデルルーティング戦略

**日付**: 2026-03-08
**ステータス**: Proposed
**関連要件**: NFR-1〜5, DP-4, DP-6

---

## コンテキスト

LAM v4.0.0 では hooks（PreToolUse, PostToolUse, Stop, PreCompact）と subagents でモデルを使用する。Claude Code Max 契約では Opus にフォールバック閾値があり、hooks で Opus を消費するとメインセッションの Opus 枠を圧迫するリスクがある。

## 判断対象

hooks と subagents でどのモデルを使用するか。

## 選択肢

### A: 等級に応じてモデルを上げる（PG=なし, SE=Haiku, PM=Opus）

- **[Affirmative]**: PM級判定に Opus を使えば精度が最も高い
- **[Critical]**: Opus 枠を hooks が消費し、メインセッションで Opus が使えなくなるリスク。PM級の hook は「この変更は PM 級か？」の分類判定であり、Opus の推論力は不要

### B: 3層アプローチ（command → Haiku → Sonnet）— **採用**

- **[Affirmative]**: Haiku は hooks のデフォルト（公式設計意図と一致）。Sonnet は agent 型で十分な精度。Opus 枠をメインセッションに温存
- **[Critical]**: Sonnet での PM 級判定精度が不十分な場合、誤分類リスク。ただし「迷ったら SE」原則で安全側に倒せる

### C: 全て command 型（LLM 不使用）

- **[Affirmative]**: コストゼロ、レイテンシ最小
- **[Critical]**: ファイルパス・ツール名のパターンマッチだけでは SE/PM の判定が不十分。変更内容の意味理解が必要なケースに対応できない

## 決定

**選択肢 B を採用。**

| レイヤー | handler type | model | 用途 |
|---------|-------------|-------|------|
| 第1層: パスベース | `command` | なし | ファイルパス・ツール名で PG/SE/PM を粗分類 |
| 第2層: 内容ベース | `prompt` | `haiku` | 第1層で判定不能なグレーゾーンを LLM で判定 |
| 第3層: 深い検証 | `agent` | `sonnet` | ファイル内容を読む必要がある場合（agent は tool access あり） |

**Opus は hooks/subagents で使用しない。** メインセッション専用。

## 補足事項

- `model` フィールドのエイリアス（`haiku`, `sonnet`, `opus`）は公式ドキュメント（model-config, sub-agents）に記載あり。実機検証は Wave 1 実装時に実施
- 環境変数 `ANTHROPIC_DEFAULT_HAIKU_MODEL` 等で解決先を上書き可能
- `opusplan` エイリアス（planning 時 Opus、execution 時 Sonnet）はメインセッションのモデルとして検討に値する

## 結果

- hooks のコスト影響を最小化
- メインセッションの Opus 枠を保護
- 「迷ったら SE」原則により、分類精度不足時も安全側に倒れる
