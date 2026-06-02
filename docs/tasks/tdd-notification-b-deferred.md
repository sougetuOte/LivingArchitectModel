# tdd 通知B（未分析パターン通知）の実装

**起票日**: 2026-06-02
**起票元**: full-review iter1（`docs/artifacts/audit-reports/2026-06-02-iter1.md` W-9）
**権限等級**: PG（通知機能・自動）
**ステータス**: 未実装（genuine spec_drift）
**仕様**: `docs/specs/tdd-introspection-v2.md` §5.1（通知B: 未分析パターン通知）/ 同 §7 実装手順 step 7

## 概要

`tdd-introspection-v2.md` は Stop hook に「通知B」を要求するが、`lam-stop-hook.py` に未実装。

仕様（§5.1）:
1. `tdd-patterns.log` の最終 `ANALYZED` マーカー以降のエントリ数をカウント
2. 未分析エントリが1件以上あれば、ループ終了ログに `/retro` 推奨を注記
   - `_log(log_file, "INFO", "TDD patterns: N件の未分析パターンあり。/retro を推奨。")`

## なぜ spec_drift か

仕様 §5.1 / §7 step 7 に明記され、Phase/Wave 未実装マークが付いていない。
仕様にあるが実装にない＝Zero-Regression Policy（Spec Synchronization）違反。

## 方針

- PG級の通知機能であり実装は小規模（Stop hook のループ終了ログ生成箇所に数行追加）。
- 実装するか、または「現時点では不要」と判断するなら仕様側に Phase マークを付けてドリフトを解消する（暗黙スキップ禁止 S-3）。

## 参照

- 仕様: `docs/specs/tdd-introspection-v2.md` §2.1, §5.1, §7
- 対象: `.claude/hooks/lam-stop-hook.py`（`_save_loop_log` 周辺）
- 信頼度モデル: `.claude/rules/auto-generated/trust-model.md`
