"""HGA 召喚コスト集計スクリプト.

Fable subagent の Anthropic API 実メータリングを jsonl から抽出し、
input / cache_creation / cache_read / output の分離と Fable 単価適用コストを算出する。

使い方:
    python .claude/scripts/hga_usage.py

出力: 各 HGA 召喚の per-message tokens と単価適用コスト.

参照:
    - docs/artifacts/hga-summon-log.md § day-1 実測メモ (#5)
    - .claude/rules/hga-summoning.md § day-1 実測チェックリスト #5

注意事項:
    - tool_uses=0 の一発応答召喚では jsonl の output_tokens が過小記録される
      (message_end イベント欠落のため). 補正は text char 数 * 0.8-1.5 で推定.
    - 新規召喚を追加する場合は下記 HGA_CALLS リストに (label, session_id, agent_id) を追記.
      session_id は ~/.claude/projects/D--work7-LivingArchitectModel/<session>.jsonl から,
      agent_id は同ディレクトリの subagents/agent-*.meta.json から取得できる.
"""

import json
import os
import sys

BASE = os.path.expanduser("~/.claude/projects/D--work7-LivingArchitectModel")

# Fable 単価 (2026-07 時点 / 従量移行後).
PRICE_INPUT = 10.0        # $/MTok  fresh input
PRICE_CACHE_C = 12.5      # $/MTok  cache_creation (1.25x baseline)
PRICE_CACHE_R = 1.0       # $/MTok  cache_read (0.1x baseline)
PRICE_OUTPUT = 50.0       # $/MTok  output

# 既知の HGA 召喚一覧. 追加は末尾に append.
HGA_CALLS = [
    ("#1 通常 (親tasks敵対検証)",       "3f0194fe-b268-4e00-8625-f06f53821de2", "agent-ac30aee520b7db98e"),
    ("#2 branch (別予算)",              "3f0194fe-b268-4e00-8625-f06f53821de2", "agent-acf3e131b7c3508a3"),
    ("#3 通常 (タスク3計画)",           "14741519-9450-4df6-a8d5-14009653efe3", "agent-a909577de81bea2cc"),
    ("#4 通常 (統治設計協議)",          "def0eb3d-1931-44d0-a8e1-a61d320faade", "agent-a86821db391ef7654"),
    ("#5 通常 (R-1 scope crux)",        "5c5c9c7d-3284-4404-b3d2-20b8b8e631c9", "agent-acea673e64f4085d4"),
    ("#6 通常 (R-1 design adv review)", "5c5c9c7d-3284-4404-b3d2-20b8b8e631c9", "agent-ac0223b277fd0a674"),
    ("#7 通常 (W-R1 adv verify)",       "09d5f803-c73a-47b8-b23c-f6b1c738b759", "agent-a3b531327c44ec724"),
    ("#8 通常 (crux-scoping R1-001+006)","4a38dbbf-5527-457d-9d2e-faa59235c0e0", "agent-a151d2bb93bcc81a0"),
    ("#9 通常 (verify R1-001+006)",     "4a38dbbf-5527-457d-9d2e-faa59235c0e0", "agent-aec18707a6937ef98"),
    ("#10 通常 (R1-053 verify)",        "98d911bf-f890-4f15-a03a-781ec6d77de0", "agent-a19bb687a9efb6a0b"),
    ("#11 通常 (L3 導入設計軸)",        "3d1ccd4a-a312-4959-bfe8-a761d69fbaa8", "agent-a867990302ce1ef86"),
    ("#12 通常 (案 D 具体化)",          "3d1ccd4a-a312-4959-bfe8-a761d69fbaa8", "agent-a4fb4a67823034c3b"),
    ("#13 通常 (規律 SSOT 統合 / 従量期初)", "c9cacac9-99aa-45da-bb23-67710145874f", "agent-a0f31d0f355459ac0"),
    ("#14 通常 (Phase A adv review)",   "6b87cdbe-50b3-46be-bd87-7d9993a45dbd", "agent-aca17a44be8f84ff8"),
]


def summarize(path):
    tot_in = tot_cc = tot_cr = tot_out = 0
    msgs = tool_use_msgs = text_chars = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            msg = d.get("message", {}) or {}
            if msg.get("role") != "assistant":
                continue
            msgs += 1
            usage = msg.get("usage", {}) or {}
            tot_in += usage.get("input_tokens", 0)
            tot_cc += usage.get("cache_creation_input_tokens", 0)
            tot_cr += usage.get("cache_read_input_tokens", 0)
            tot_out += usage.get("output_tokens", 0)
            content = msg.get("content", [])
            if isinstance(content, list):
                for c in content:
                    if c.get("type") == "tool_use":
                        tool_use_msgs += 1
                        break
                for c in content:
                    if c.get("type") == "text":
                        text_chars += len(c.get("text", ""))
    return msgs, tool_use_msgs, tot_in, tot_cc, tot_cr, tot_out, text_chars


def cost(i, cc, cr, out):
    return (i * PRICE_INPUT + cc * PRICE_CACHE_C + cr * PRICE_CACHE_R + out * PRICE_OUTPUT) / 1_000_000


def main():
    total_cost = 0.0
    print(f"{'HGA':30} {'msgs':>4} {'tool':>4} {'input':>7} {'cache_c':>8} {'cache_r':>9} {'output':>7} {'chars':>6} {'cost':>8}")
    print("-" * 92)
    for label, sid, aid in HGA_CALLS:
        p = os.path.join(BASE, sid, "subagents", aid + ".jsonl")
        if not os.path.exists(p):
            print(f"MISSING: {label} -> {p}")
            continue
        m, tm, i, cc, cr, out, chars = summarize(p)
        c = cost(i, cc, cr, out)
        note = ""
        if tm == 0 and out < 100 and chars > 100:
            est_out = int(chars * 1.2)
            corrected_c = cost(i, cc, cr, est_out)
            note = f" [!] tool_uses=0 で output 過小記録. text 補正で ~${corrected_c:.2f}"
            c = corrected_c
        total_cost += c
        print(f"{label:30} {m:>4} {tm:>4} {i:>7} {cc:>8} {cr:>9} {out:>7} {chars:>6} ${c:>6.2f}{note}")
    print("-" * 92)
    print(f"{'合計':30} {'':>4} {'':>4} {'':>7} {'':>8} {'':>9} {'':>7} {'':>6} ${total_cost:>6.2f}")
    print()
    print(f"envelope 目安: 月 $40-80 (branch モードは別予算枠のため除外して確認)")


if __name__ == "__main__":
    sys.exit(main())
