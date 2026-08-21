# `maxTurns` 実測記録 — subagent frontmatter のターン打ち切り

**実施日**: 2026-08-21
**契機**: `docs/artifacts/prescription-audit-2026-08-20.md` §2 / §5 #2（「`maxTurns` が `.claude/agents/` に効くかの実測が先」）
**結論**: **`maxTurns`（camelCase）は `.claude/agents/*.md` で有効**。`max_turns`（snake_case）は無効。

---

## 1. 何が問題だったか

`docs/specs/goal-driven-orchestration/` は「L3 の暴走はフロントマターの `max_turns`（小 10 / 中 20 / 大 15）で打ち切る」と記述していたが、2026-08-20 の処方監査で **`max_turns` は subagent frontmatter の有効キーではなく、bound は一度も機能していなかった**ことが判明した。

このとき `maxTurns`（camelCase）へ書き換えなかったのは、**効くかを検証せずに直すと「担保した」という記述だけが復活し、同じ失敗を作り直す**ためである。公式ドキュメントで `maxTurns` が現れるのは plugin agent の例のみで、`.claude/agents/` に効くかは未確認だった。

## 2. 静的証拠（Claude Code バイナリ実測）

`~/.local/bin/claude.exe` の文字列を検査した。

| # | 証拠 | 内容 |
|:-:|:-----|:-----|
| 1 | **ローダのエラーメッセージが 2 系統** | `Agent file ${e} has invalid maxTurns '${T}'. Must be a positive integer.` が、`basename(e, ".md")` で agent 名を決めるローダ（= `.claude/agents/*.md` 用）の中に存在する。plugin 用は別に `Plugin agent file ${e} has invalid maxTurns ...` がある |
| 2 | **スキーマに含まれる** | `maxTurns: z.number().int().positive().optional()` が `memory` / `skills` / `initialPrompt` と同一スキーマにある。`memory` は公式が `.claude/agents/` のフィールドと明記しており、LAM も全 12 エージェントで使用中 |
| 3 | **実行ループが打ち切りを処理** | `"max_turns_reached"` → `[Agent: ${agentType}] Reached max turns limit (${maxTurns})` |
| 4 | **組み込み agent が使用** | `fork` = `maxTurns: 200` / `read-analyst` = `maxTurns: 6` |

**副産物**: 同じローダが `effort` と `permissionMode` も検証している。`docs/specs/cc-spec-alignment/future-candidates.md` がこれらを「見送り」に置いた際の前提（plugin 専用）は、少なくとも `maxTurns` / `effort` / `permissionMode` については成り立たない。

## 3. 対照実験

同一本文・同一プロンプトの agent 定義を 2 本用意し、**frontmatter の `maxTurns` の有無だけを変えた**（差分は `name` / `description` / `maxTurns` の 3 行のみを確認済み）。

**課題**: 「10 個のファイルを、1 回の Bash 呼び出しにつき 1 個ずつ作れ」（ループ・`&&` 連結・brace 展開を明示禁止）。10 個作るには最低 10 ターンを要する。

**観測指標**: 出力ディレクトリのファイル数（= 外部の不動点。エージェントの自己申告に依存しない）。

| プローブ | frontmatter | tool_uses | 生成ファイル数 |
|:---|:---|--:|--:|
| `probe-maxturns-bound` | **`maxTurns: 2`** | **2** | **2**（file-01, file-02） |
| `probe-maxturns-control` | なし | 10 | 10（file-01〜10） |

bound 側は "Created: 1 file" と報告した時点で打ち切られており、10 個の完走報告に到達していない。control 側は "DONE: 10 files" まで到達した。

### 再現方法

プローブ定義（実測後に削除済）の frontmatter は以下のとおり。本文は両者同一で、「1 回の Bash 呼び出しにつきファイルをちょうど 1 個だけ作る」ことだけを指示する。

```yaml
---
name: probe-maxturns-bound
description: 【実測用プローブ】
tools: Bash
model: haiku
maxTurns: 2
---
```

## 4. 副次的に判明したこと（前提の誤り）

**agent レジストリはセッション開始時に固定されない。** 本実測は「新規 agent 定義は同一セッションでは反映されないので、次セッションで検証する」という前提で始めたが、定義ファイルを作成した直後に新しい agent type として利用可能になり、**同一セッション内で実測できた**。

memory `dw-agent-registry-resolution` の「Agent ツール = セッション開始時に解決」という記述は、少なくとも本環境の現行バージョンでは成り立たない。

## 5. 適用（2026-08-21）

- `.claude/agents/goal-driven-l3-executor.md` に **`maxTurns: 20`** を設定
- **値は 20 固定でルート別ではない**。frontmatter は静的であり L3 定義は 1 ファイルのため、設計値（小 10 / 中 20 / 大 15）の**最大値をバックストップとして採った**
- **`goal-driven` は Plan B（`/goal` 不使用）確定済**であり、ルート別の値を運ぶはずだった `/goal` 条件文が存在しない。したがって **Plan B におけるターン数打ち切りは `maxTurns` 20 のみ**が担う。小タスクでも 20 ターンまで走るのは設計意図より緩いが、改訂前は打ち切りが一切効いていなかったため後退ではない
- ルート別の粒度を取り戻すには L3 agent 定義のファイル分割が要る（**2026-08-21 に見送りを決定** / ユーザー承認）

## 6. 射程の限界

- 本実測が示したのは「`maxTurns` がターンを打ち切る」ことのみ。**打ち切られた L3 が構造化報告に `next_suggestion: "ESCALATE"` を設定するか**（design.md §10 の「超過時の動作」）は**未検証**である。打ち切りは Claude Code 側で起きるため、agent が最終報告を書く前に止まる可能性がある
- `maxTurns: 2` は tool_uses 2 と一致したが、**1 ターン = 1 tool_use が常に成り立つかは未確認**（並列 tool 呼び出しがある場合の数え方は検証していない）

## 7. 参照

- `docs/artifacts/prescription-audit-2026-08-20.md` §2 / §5（本実測の契機）
- `docs/specs/goal-driven-orchestration/design.md` §10 層別 bound（改訂後）
- `.claude/skills/goal-driven/SKILL.md` / `references/route-and-bound.md`（改訂後）
