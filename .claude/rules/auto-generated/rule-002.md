# Rule 002: parser regex の Milestone/Task 記法追随保守（verify_reference_resolution.py 系 + GitHistoryParser）

**生成日**: 2026-07-25
**ステータス**: approved（2026-07-25 / R-2 PLANNING 承認済み `docs/specs/r-2-consolidation/tasks.md` W1-R2-T4 に基づき起票と同時承認）
**観測回数**: 3（2026-07-06 HGA #9, 2026-07-07 HGA #10, 2026-07-15 W-R5 監査）
**last_matched**: 2026-07-25（起票と同時に初期化 / 直近の検出イベントは 2026-07-15 = W-R5 監査）
**閾値到達**: `trust-model.md` の初期閾値 2 回（§閾値）を超過し、N=3 の恒久解検討ライン（§N 回目発火時の恒久解検討）に到達済み。GitHistoryParser 側（R1-061）は W-R3 S1 T5（2026-07-10 commit `6b836e5`）で `_TASK_PATTERN` の regex 汎化を恒久解として実施済み（rule-001 の `B-\d+` → `[A-Z]-\d+` 拡張と同型パターン）。一方 `verify_reference_resolution.py` 側の residual（R1-054〜058）は 2026-07-15 W-R5 S1 で全件 `deferred` 裁定済みのため、本ルールの機構実体（下記 parser 世代追随 pytest 群）が「現状の挙動」を pin し、次回（4 回目）同型が発火した場合は fallback の場当たり拡張ではなく構造的恒久解（パターン 3 の再設計等）の検討を必須とする。

## 根拠パターン

| # | 日付 | 検出イベント | 内容 |
|---|------|-------------|------|
| 1 | 2026-07-06 | HGA #9 | R1-054 / R1-055（多階層参照退化・regex 非捕捉退化） |
| 2 | 2026-07-07 | HGA #10 | R1-056 / R1-057 / R1-058（多階層参照退化・regex 非捕捉退化 3 態様・走査 scope 外） |
| 3 | 2026-07-15 | W-R5 監査 | R1-061（GitHistoryParser dashboard 系） |

**注記**: R1-059（gabriel 契約 substring 弱検査）は上記検出イベント（HGA #10）に付随して起票されたが、T6（gabriel strict enum 検証）の対象であり本ルールの根拠パターンには含めない（design.md §4.3 W-h 反映）。
**注記 2**: R1-054 の実際の `evidence_file` は design.md 表記上の一括ラベル「verify_reference_resolution.py 系」とは異なり `.claude/scripts/dashboard/builder.py`（`_resolve_task_status` の lookbehind/lookahead）である（`docs/artifacts/r-1-audit-tracker.md` R1-054 実測）。HGA #9 の同一検出イベント内で見つかった issue のため根拠パターン表の記載はそのまま維持し、本注記で事実関係を明示する。

出典: `docs/artifacts/hga-summon-log.md` #9（2026-07-06）/ #10（2026-07-07）/ `docs/artifacts/r-1-audit-tracker.md` R1-054〜058, R1-061（2026-07-15 W-R5 監査）。

## ルール

`.claude/scripts/dashboard/parsers/git_history.py` の `_TASK_PATTERN` / `_WAVE_PATTERN`、`.claude/scripts/verify_reference_resolution.py` の `_W_R3_PAT_*` 系正規表現、および `.claude/scripts/dashboard/builder.py` の `_resolve_task_status` トークン境界 regex を編集・追加する際は、以下を守ること。

- **Milestone/Task 命名体系が変わったら parser regex の追随を確認する**。`terminology.md` §4 で定義される Milestone/Wave/Task の命名規則が拡張・変更された場合（例: `W-R1-S1-T6` のようなハイフン Milestone 記法の登場）、既存 parser regex がその新記法を捕捉できるかを必ず確認する（rule-001.md の SessionStateParser fallback 保守と同型の予防措置）。
- **追随確認は下記 (a)(b) の pytest 群で行う**。regex を変更した場合は必ず `.claude/tests/rules/test_parser_generation_tracking.py` を実行し、全ケースが PASS することを確認してから commit する。
- **機構実体 = 「parser 世代追随 pytest 群」**（design.md §4.3 準拠）:
  - **(a) GitHistoryParser Task ID regex テスト**: `_TASK_PATTERN` が現行世代記法（`W-R1-S1-T6`, `W1-R2-T4`, `W1-R2-T4a`, `W-R2-S2-T3`, `W7-B4-T9` 等）を正しく捕捉することを assert する回帰保護テスト。加えて、拡張前（2026-07-10 以前）の旧 regex を文字列としてテスト内に保持し、同じ記法を投入すると捕捉に失敗する（誤例）ことを実証し、「規則を守らないとテストが落ちる」ことを機構的に担保する。
  - **(b) verify_reference_resolution.py 系 characterization テスト**: R1-054〜058（多階層参照退化 / 非 `.md` 拡張子・大文字 `.MD` 退化 / underscore 境界未対応 / 走査 scope 限定）の **現状挙動を pin する**。これらは 2026-07-15 W-R5 S1 で `deferred`（live corpus 実例 0 件のため即時修正不要）と裁定済みのため、本テスト群は「直す」のではなく「意図しない挙動変化を検出可能にする」ことを目的とする。**将来 R1-054〜058 を恒久解として修正する場合は、対応する characterization test も同一 commit で更新すること**（pin の更新漏れを regression と誤読しないため）。
- **N 回目発火時の恒久解検討（`trust-model.md` §N 回目発火時の恒久解検討 準拠）**: 本ルールは観測 3 回目（N=3）到達で起票された。GitHistoryParser（R1-061）はこの時点で既に恒久解（regex 汎化）を実施済みだが、`verify_reference_resolution.py` 系の residual（R1-054〜058）は deferred のまま維持されている。**次回（4 回目）同型パターンが発火した場合は、fallback regex の場当たり的拡張ではなく、パターン 3（`_W_R3_PAT_SPEC_REF`）自体の構造的再設計（例: group3 の多階層 `/` 対応拡張）を検討必須とする。**

## 検証コマンド

```bash
bash .claude/scripts/py_invoke.sh -m pytest .claude/tests/rules/test_parser_generation_tracking.py
```

## 適用範囲

- 対象ファイル:
  - `.claude/scripts/dashboard/parsers/git_history.py`（`_TASK_PATTERN` / `_WAVE_PATTERN`）
  - `.claude/scripts/verify_reference_resolution.py`（`_W_R3_PAT_*` 系正規表現）
  - `.claude/scripts/dashboard/builder.py`（`_resolve_task_status` トークン境界 regex）
- 対象操作: `Edit`（正規表現パターンの追加・変更）
- 適用者: L1 / L2（Sonnet 委譲経路含む）

## 権限等級

- 本ルールの改訂・削除: **PM 級**（`trust-model.md` 準拠）
- パターン記録の追加: **PG 級**（PostToolUse hook が自動記録）

## 寿命管理

- `last_matched`: 2026-07-25（起票と同時に初期化）
- 90 日以上マッチしない場合、`/quick-save` の Daily 記録で棚卸し対象として通知される
- 削除は PM 級承認必須

## 参照

- `.claude/rules/auto-generated/rule-001.md`（兄弟ルール / SessionStateParser の同型 parser drift 予防）
- `.claude/rules/auto-generated/trust-model.md`（信頼度モデル / カウント単位 / N 回目発火時の恒久解検討）
- `.claude/rules/auto-generated/README.md`（ライフサイクル）
- `docs/specs/r-2-consolidation/design.md` §4.3（rule-002 起票の設計 SSOT）
- `docs/specs/r-2-consolidation/tasks.md` W1-R2-T4（本ルールの完了条件 SSOT）
- `docs/artifacts/hga-summon-log.md` #9 / #10
- `docs/artifacts/r-1-audit-tracker.md` R1-054 / R1-055 / R1-056 / R1-057 / R1-058 / R1-061
- `.claude/tests/rules/test_parser_generation_tracking.py`（機構実体 = parser 世代追随 pytest 群）
