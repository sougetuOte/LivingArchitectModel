# gabriel メトリクス計測環境定義（Wave C Stage 5 T11）

- 作成日: 2026-07-05
- 作成者: L1 (Opus 4.7)
- 対応仕様:
  - `docs/specs/magi-v2-gabriel/requirements.md` NFR-W-C-4 (SHOULD / 監視メトリクス) + NFR-W-C-5 (SHOULD / Sonnet 起動コスト抑制)
  - `docs/specs/magi-v2-gabriel/tasks.md` §6 WC-B5-T11
- ステータス: **定義完了 / BUILDING 後 retro での実運用開始待ち**

---

## §1 目的

Wave C（骨子 ②）で導入した gabriel probe の実運用状況を **月次 retro** で評価するための計測環境を定義する。

- **NFR-W-C-4 (SHOULD)**: gabriel 起動回数 / refute 率 / inconclusive 率を月間集計して retro で議題化
- **NFR-W-C-5 (SHOULD)**: Sonnet 起動コスト (回数 × 平均 tokens) を計測し AoT 適用時のみ起動制約の費用対効果を裏付ける

## §2 ログ保存位置と形式

### ログファイル

- **パス**: `.claude/gabriel-metrics.log`
- **gitignore**: **含める** (ローカル限定 / セッション情報を含むため公開しない)
- **フォーマット**: 1 行 1 JSON エントリー (JSONL / newline-delimited JSON)

### 追加設定

`.gitignore` に以下を追記する（BUILDING 実装時 / T11 サブタスク）:

```
# gabriel metrics log (Wave C / NFR-W-C-4 / NFR-W-C-5)
.claude/gabriel-metrics.log
```

### JSONL 1 エントリーのスキーマ

```json
{
  "timestamp": "2026-07-05T14:30:00+09:00",
  "session_id": "84742b87-3779-4b16-b6e6-37614a6b20a7",
  "mode": "aot" | "lightweight",
  "gate_decision": "run" | "skip_lightweight" | "skip_opt_out" | "reject_opt_out",
  "invoked": true | false,
  "gabriel_output": {
    "verdict": "confirmed" | "refuted" | "inconclusive" | null,
    "severity": "critical" | "warning" | "info" | null,
    "affected_atoms_count": 0,
    "recommended_action": "proceed" | "re-magi" | "abort" | null,
    "confidence": 0.0
  } | null,
  "resolved_action": "proceed_confirmed" | "proceed_inconclusive" | "record_only"
                    | "annotate_warning" | "re_magi" | "escalate_critical_max"
                    | "escalate_abort" | "handle_timeout" | "handle_format_error"
                    | null,
  "retry_count": 0,
  "elapsed_ms": 0,
  "opt_out": {
    "reason": "...",
    "declarer": "user" | "L1" | "autonomous"
  } | null,
  "phase": "standard" | "AUTONOMOUS"
}
```

**必須フィールド**: `timestamp` / `session_id` / `mode` / `gate_decision` / `invoked`。
**gate 経路別 nullable 判定**:
- `invoked=false` (skip_lightweight / skip_opt_out) → `gabriel_output=null` / `resolved_action=null`
- `invoked=true` → `gabriel_output` は 6 フィールド JSON (`.claude/tests/wave_c/test_wave_c_gabriel_output.py` の schema 準拠) / `resolved_action` は 9 分岐のいずれか

## §3 記録タイミング（実装方針）

BUILDING フェーズでの実装イメージ:

```python
# .claude/scripts/magi_metrics.py (T11 実装対象 / 将来 Wave での作業)
from magi_dispatch import (
    resolve_action, render_log_entry, should_run_gabriel, OptOutRecord,
)
import json, time

def log_gabriel_probe_attempt(*, session_id, mode, gate_decision,
                              gabriel_output, resolved, retry_count,
                              elapsed_ms, opt_out, phase):
    entry = {
        "timestamp": datetime.now(timezone(timedelta(hours=9))).isoformat(),
        "session_id": session_id,
        "mode": mode,
        "gate_decision": gate_decision.gate_action,
        "invoked": gate_decision.should_run,
        "gabriel_output": _summarize_gabriel(gabriel_output) if gabriel_output else None,
        "resolved_action": resolved.action if resolved else None,
        "retry_count": retry_count,
        "elapsed_ms": elapsed_ms,
        "opt_out": {"reason": opt_out.reason, "declarer": opt_out.declarer} if opt_out else None,
        "phase": phase,
    }
    with open(".claude/gabriel-metrics.log", "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
```

**注意**: 上記 `.claude/scripts/magi_metrics.py` は本 Wave では未実装（設計方針のみ）。L1 が MAGI 合議実施時にログ書き込みを手動または hook 経由で実施する体制を想定。

## §4 月次 retro での集計手順

`/retro` (SESSION_STATE 前月分) または月末 milestone retro で以下を実施:

### 集計コマンド (bash 例)

```bash
# 起動回数
jq -c '.invoked' .claude/gabriel-metrics.log | grep -c true

# refute 率
INVOKED=$(jq -c 'select(.invoked==true)' .claude/gabriel-metrics.log | wc -l)
REFUTED=$(jq -c 'select(.gabriel_output.verdict=="refuted")' .claude/gabriel-metrics.log | wc -l)
echo "refute 率: $(echo "scale=3; $REFUTED / $INVOKED" | bc)"

# inconclusive 率
INCONCLUSIVE=$(jq -c 'select(.gabriel_output.verdict=="inconclusive")' .claude/gabriel-metrics.log | wc -l)
echo "inconclusive 率: $(echo "scale=3; $INCONCLUSIVE / $INVOKED" | bc)"

# 平均 elapsed_ms (パフォーマンス regression 検出)
jq -c '.elapsed_ms' .claude/gabriel-metrics.log | awk '{s+=$1; c++} END {print "avg elapsed:", s/c, "ms"}'

# opt-out 却下試行数 (AUTONOMOUS ガード実効性の裏付け)
jq -c 'select(.gate_decision=="reject_opt_out")' .claude/gabriel-metrics.log | wc -l
```

### retro で議題化する観点

1. **起動頻度と AoT 判定の妥当性**: gabriel が実質役立っている割合 (refute 率が高ければ safety net として機能 / 極端に低ければ AoT トリガー閾値の見直し検討)
2. **inconclusive 率**: 20% を超える場合、gabriel の rubric / confidence 閾値 (0.3) の見直しを検討
3. **timeout / format_error 頻度**: NFR-W-C-1 (60s SHOULD) / NFR-W-C-2 (フォーマット準拠 MUST) の regression 兆候
4. **AUTONOMOUS 却下試行**: 自律ループが opt-out を試みた回数 (ADR-0005 FR-9.1 ガードの実効性確認)
5. **Sonnet コスト**: gabriel 起動回数 × 平均 tokens (Sonnet subscription quota への影響)

## §5 実運用開始条件

以下を満たした時点で `.claude/gabriel-metrics.log` への実書き込みを開始する:

- [ ] `.gitignore` に `.claude/gabriel-metrics.log` を追加 (次コミットに含める / 本 T11 の副次サブタスク)
- [ ] `.claude/scripts/magi_metrics.py` の実装（将来 Wave / 本 Wave では設計のみ）
- [ ] MAGI 合議実施時のフロー整備（L1 が合議終了時に metrics 書き込み手順を踏む / hook 化検討は future-candidates）
- [ ] 月次 retro テンプレートに集計手順追加 (`.claude/skills/retro/` 配下 / 別 Wave)

## §6 実運用開始まで暫定運用

正式ログが立ち上がるまでの間、gabriel 実運用が発生した場合は以下で暫定記録する:

- SESSION_STATE.md の `## MAGI 合議記録` 節にフリーフォーマットで gabriel 結果を記録
- MAGI 合議 anchor ファイル (`docs/artifacts/YYYY-MM-DD-magi-*.md`) に gabriel probe セクションを追記
- 月次 retro で当該 anchor ファイルを目視集計

## §7 権限等級

- 本 artifact ファイル (`docs/artifacts/`): SE 級
- `.gitignore` 更新 (`.claude/gabriel-metrics.log` 追加): SE 級
- `.claude/scripts/magi_metrics.py` 新規 (将来 Wave): SE 級
- `.claude/skills/retro/` テンプレート更新 (将来 Wave): PM 級 (スキル変更 / draft-first 推奨)

## §8 参照

- `docs/specs/magi-v2-gabriel/requirements.md` NFR-W-C-4 / NFR-W-C-5
- `docs/specs/magi-v2-gabriel/design.md` §3 (JSON スキーマ)
- `.claude/scripts/magi_dispatch.py` (verdict 分岐 SSOT)
- `.claude/tests/wave_c/test_wave_c_gabriel_output.py` (schema 検証)
- `docs/adr/0005-thin-harness-autonomous-governance.md` FR-9.1 (AUTONOMOUS ガード根拠)
