# ADR-0002: Stop hook 実装方式（Ralph Wiggum vs 独自実装）

**日付**: 2026-03-08
**ステータス**: Accepted
**関連要件**: P2-FR-1, P5-FR-1〜5, DP-6

---

## コンテキスト

LAM v4.0.0 の柱2（ループ統合）では、`/full-review` を自動収束ループ化する。Claude Code には公式プラグイン「Ralph Wiggum」（Stop hook による自律ループ）が存在する。

## 判断対象

Ralph Wiggum プラグインをそのまま利用するか、独自の Stop hook を実装するか。

## 選択肢

### A: Ralph Wiggum プラグインをそのまま利用

- **[Affirmative]**: 導入コスト最小。Anthropic がメンテナンス。実績あり
- **[Critical]**: 完了判定が `<promise>` タグの単一文字列マッチのみ。LAM の Green State（テスト全パス + lint全パス + Critical 0件）という複合条件を判定できない。`/full-review` の Phase 1-5 段階的フローと「同じプロンプトを繰り返す」方式が噛み合わない。LAM のフェーズガードレールを認識しない

### B: 独自 Stop hook を実装（Ralph を参考実装として活用）— **採用**

- **[Affirmative]**: Green State の複合条件を直接判定可能。フェーズ状態を読み取りフェーズ別の制御が可能。`/full-review` の検証フェーズを hook 化し自然に統合できる。`last_assistant_message`（最新 API）を直接利用でき transcript 解析不要
- **[Critical]**: 自前メンテナンスが必要。Ralph の ~180 行の bash スクリプトと同等以上の実装が必要

### C: 両方を併用

- **[Critical]**: 複数 Stop hook は並列実行される。片方が `block` を返せば停止しない。意図しない干渉の温床。実質的に排他利用が推奨される

## 決定

**選択肢 B を採用。** Ralph Wiggum の設計パターン（状態ファイル管理、frontmatter 方式、反復カウント）を参考に、LAM 固有の Stop hook を実装する。

### 実装方針

- スクリプト: `.claude/hooks/lam-stop-hook.py`
- 状態ファイル: `.claude/lam-loop-state.json`（ループ起動時に生成、完了時に削除）
- 判定ロジック:
  1. 状態ファイルの存在確認（なければ `exit 0` で通過）
  2. `stop_hook_active` で無限ループ防止
  3. 反復回数チェック（上限: デフォルト5回）
  4. Green State 判定（テスト + lint を外部コマンドで実行）
  5. 未達なら `{"decision": "block", "reason": "..."}` で継続

## 結果

- LAM の収束条件を直接 hook で判定でき、Claude に判定を委ねない（premature promise リスク排除）
- `/full-review` との自然な統合
- Ralph の設計パターンを再利用し、開発コストを抑制
