# Wave 2 将来候補記録（FR-5.2）

最終更新: 2026-05-28 / フェーズ: BUILDING（Wave 2 完了時）
親: [requirements.md](requirements.md) FR-5.2 / [design.md](design.md) §7.6

Wave 2 で検討対象としたが採用しなかった新機能、および今回スコープ外とした
新機能群を将来の再検討候補として記録する。

## 1. Wave 2 で検討して見送った機能（理由付き）

| 機能 | 見送り理由 | 再検討の条件 |
|------|-----------|------------|
| `permissionDecision: "defer"` | PM級 ask の defer 化は「人間承認必須」憲法を settings 設定ミスで後退させうる。LAM の等級判定設計と不整合（MAGI 合議 [2026-05-28-magi-t2-2-defer.md](../../artifacts/2026-05-28-magi-t2-2-defer.md)） | LAM が「hook では判断が曖昧で settings に委ねたいケース」を持つ運用形態に変化した場合。ただし PM級ゲートの後退を伴わない設計が前提 |
| `isolation: worktree` | デフォルトで origin/master から分岐するため、未コミット変更を対象とするレビュー/実装と矛盾。`worktree.baseRef: "head"` 明示でも常用ワークフローと乖離 | 複数機能を同時並行で実装し、書き込み衝突が現実問題化した場合。かつ `baseRef: "head"` 運用を前提化できる場合 |
| `background: true` | 権限プロンプト自動拒否が LAM の ask ガード（PM/SE級）と衝突。8エージェントは全てオンデマンド起動で常駐不要 | 常駐監視型エージェント（例: 継続的なログ監視）を新設し、かつ ask 不要な読み取り専用に限定できる場合 |
| `effort.level`（hook 入力） | 明確な活用箇所がなく行動変化を生まない。PG判定への統合は effort 低→PG緩和となり危険 | effort 別の観測メトリクスが必要になった場合（観測記録のみ・行動分岐なし） |
| 新 hook ハンドラ（http/mcp_tool/prompt/agent） | 現行 command 型の確実性・フェイルセーフ（exit 0）を損なう。prompt 型は等級判定を非決定化 | 決定論では表現困難な判定が必要になった場合。agent 型は experimental 解除後に再評価 |

## 2. 今回スコープ外とした新機能群（参照）

DQ-2（案A）により Wave 2 は既存7スキルへの適用に限定したため、以下は未検討。
網羅列挙は差分マッピング文書に記載済み。再検討時はそちらを一次資料とする。

- Skills/Sub-agents 領域の未採用 B 機能: [diff-skills-subagents.md](diff-skills-subagents.md) §5
  （`hooks` フロントマター, `context: fork`, `disable-model-invocation`, `user-invocable`,
  `shell`, `argument-hint`/`arguments`, `disallowedTools`, `permissionMode`, `maxTurns`,
  `skills` プリロード, `color`, `mcpServers`, `Agent(name)` deny 記法 等）
- MCP/Settings/Permissions 領域の未採用 B 機能: [diff-mcp-settings.md](diff-mcp-settings.md) §1〜3
  （`alwaysLoad`, `${CLAUDE_PROJECT_DIR}` 展開, `skillOverrides`, `$schema`,
  `permissions.defaultMode`, `additionalDirectories`, `PermissionRequest`/`PermissionDenied` hook 等）

## 3. 所見（retro 記録対象）

Wave 2 計画（design §7）では機能の**実在性**を裏取り（V-1〜V-8）したが、**LAM 設計思想への適合性**の
事前評価が不足していた。結果、昇格組3つ（defer / worktree・background / effort.level）が
実装段階で軒並み見送りとなった。今後の新機能採用 Wave では「実在性の裏取り」と
「プロジェクト思想との適合性評価」を計画段階で二段構えにすることを推奨する。
