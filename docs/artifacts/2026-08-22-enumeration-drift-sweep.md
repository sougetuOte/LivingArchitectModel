# 条文 ↔ 実装の「列挙ドリフト」横断掃き

**実施日**: 2026-08-22
**契機**: HGA #28 が付随観測として発見した 1 件（PM 級パス列挙に `CLAUDE.md` が欠落 / 約 4 週間未発見）を**欠陥クラス**と見なし、同型が他にないかを横断で洗った。
**方法**: 4 スライス並列（hooks / MAGI / モデル・委譲 / 台帳・自動生成）+ L1 による裏取り + **権限境界の canary 実測 1 件**。全 19 対を両方向（条文にあって実装にない / 実装にあって条文にない）で突合。

> **本掃きは修正を行っていない。** 検出と仕分けのみ。修正は等級ごとに別途判断する。

---

## 0. 結果サマリ

| スライス | 対 | 一致 | 乖離 | 備考 |
|:---|--:|--:|--:|:---|
| 台帳・自動生成 | 13 | **13** | **0** | §C 機構 9 件は判定コマンドを**実際に実行**して全通過 |
| モデル・委譲 | 9 | 8 | 1 | 安全側の乖離 |
| MAGI / skills | 9 | 6 | 3 | うち 1 件は仕様文書の陳腐化 |
| hooks / 権限 | 11 | 2 | 6 | 3 件は**条文が要求する防御が実装に不在** |
| **canary 実測** | 1 | — | **1** | **読み取り専用の保証が破れている**（下記 §1） |

**総計: 乖離 11 件**（うち条文が安全側 = 4 / 実装が安全側 = 5 / 記述漏れ = 2）。

---

## 1. 最重要 — `memory: project` が読み取り専用の保証を無効化している

### 事実（canary で実測 / 2026-08-22）

`gabriel` サブエージェントに **scratchpad へのファイル作成を指示したところ、成功した**（`Write` が拒否されず `probe-2026-08-22` が書かれた / L1 が存在と内容を確認後に削除）。

| 情報源 | gabriel の tools |
|:---|:---|
| `.claude/agents/gabriel.md:10`（frontmatter） | `Read, Glob, Grep` |
| `.claude/agents/gabriel.md:228`（本文の自己記述） | 「**Write / Edit / Bash ツールを持たない**」 |
| `.claude/skills/magi/SKILL.md:112` | 「Read/Glob/Grep/**Write/Edit** のみ利用可」 |
| **実行時に付与された実体**（canary + エージェント登録情報） | **Read, Glob, Grep, Write, Edit** |

### 原因

`CLAUDE.md` §Memory Policy が既に明記していた —— 「公式機構により…**Read/Write/Edit が自動有効化される**」。**`memory: project` を設定した時点で、frontmatter の `tools:` から Write/Edit を外しても付与される。**

自然実験がこれを裏づける: `.claude/agents/` の 12 件（全て `memory: project`）は登録情報上すべて Write/Edit を持つ一方、`memory` を持たない他のエージェント（`spec-critic` = Read/Glob/Grep、`error-triager` = Read/Glob/Grep/Bash）には付与されていない。

### 影響を受ける定義（frontmatter で Write/Edit を意図的に外している 5 件）

| agent | frontmatter `tools:` | 実体 | 文書上の主張 |
|:---|:---|:---|:---|
| **gabriel** | Read, Glob, Grep | +Write, Edit | 「ファイル変更・git 操作は行わず、**読み取り専用の検証のみ**」（NFR-W-C-3 暴走リスク抑制） |
| **goal-driven-grader** | Read, Glob, Grep, Bash | +Write, Edit | 「**ファイル変更・git 操作・パッケージ操作は禁止**（W-2）」 |
| code-reviewer | Read, Grep, Glob, Bash | +Write, Edit | 明示の禁止記述なし |
| quality-auditor | Read, Glob, Grep, Bash | +Write, Edit | 同上 |
| test-runner | Read, Grep, Glob, Bash | +Write, Edit | 同上 |

**gabriel と goal-driven-grader は「書けないこと」を安全根拠として文書に書いており、その根拠が実際には成立していない。**

### 性質

これは「条文 ↔ 実装」の乖離ではなく、**「LAM の 2 つの正しい記述が、接続されていなかった」**種類の欠陥である。`CLAUDE.md` は機構を正確に記述し、agent 定義は制限を正確に記述していたが、**前者が後者を打ち消すことに誰も気づいていなかった**。今回も、条文の突合ではなく**登録情報との食い違い → canary 実測**という別経路で発見された。

### 対策の実測（2026-08-22 / **未決着** / 交絡の記録）

**上流仕様の確定**（context7 + 公式ドキュメント / 同日）:

| # | 事実 | 出典 |
|:-:|:---|:---|
| U1 | **`PreToolUse` はサブエージェント内でも発火する**。入力に **`agent_id`**（サブエージェント時のみ存在）/ `agent_type` が乗る | `…/hooks` |
| U2 | **`disallowedTools` は公式フィールド**で、`tools` より**先に適用**される（「両方に載ったツールは除去」） | `…/sub-agents` |
| U3 | **`memory:` が Read/Write/Edit を自動有効化する**のは公式明示。**read-only memory の指定手段は存在しない**（値は `user` / `project` / `local` のみ） | 同上 |
| U4 | **`disallowedTools` が memory の自動付与を打ち消せるかは公式記述なし**（相互作用の記述が皆無） | — |
| U5 | `permissions` のルール構文では**呼び出し元エージェントを条件にできない**。`Agent(name)` deny は**起動の禁止**であって内部呼び出しの拒否ではない | `…/permissions` |

**試行と結果**:

| 回 | 変更 | canary の結果 | 有効性 |
|:-:|:---|:---|:---|
| 1 | なし（変更前の定義） | **書けた** | **確定**（§1 の根拠） |
| 2 | `disallowedTools: Write, Edit` を追加 | 書けた | **交絡 = 結論に使えない** |
| 3 | さらに `memory: project` 行を削除 | 書けた。かつ **memory 指示が system prompt に注入されたまま** | **交絡 = 結論に使えない** |

**交絡の正体**: canary 3 が報告した「`memory:` を消したのに memory 指示が残っている」は、**使われている定義がセッション開始時のスナップショットである**ことの直接証拠である。すなわち回 2・3 は**変更前の定義で走っていた**。

> **L1 の誤り（記録）**: 2026-08-21 の `maxTurns` 実測（同一セッション内で効いた）を「レジストリは再解決される」と一般化したことが原因。**解決時点はパラメータごとに異なる** —— `maxTurns` は spawn 時に効いたが、`tools` / `disallowedTools` / `memory` は反映されない。2026-06-12 に「N=1 からの一般化は危険」と学んだのと同型の誤りを、逆向きに繰り返した。

**現在のリポジトリ状態**: `gabriel.md` / `goal-driven-grader.md` に **`disallowedTools: Write, Edit` の 1 行のみ追加**（`memory: project` は復元済 = 変更前と同じ）。これは**仮説の適用であって検証済みの対策ではない**。

**次セッションでの検証手順（必須 / 同一セッションでは測れない）**:

1. 新セッションで gabriel に scratchpad へのファイル作成を指示する
2. **拒否されたら** `disallowedTools` が有効 = 対策完了。`gabriel.md:228` の自己記述が真に戻る
3. **書けたら** `disallowedTools` は無効。次の候補は (a) `memory:` の除去（gabriel / grader は agent-memory が **0 ファイル**のため損失なし。ただし `CLAUDE.md` の「全 12 エージェントに `memory: project`」が偽になり **PM 級編集**が発生）(b) subagent frontmatter の `hooks: PreToolUse`（U1 / そのエージェント実行中のみ登録される）(c) 主 hook で `agent_id` を見て deny（U1）
4. いずれの場合も**結果を本文書に追記**する

### 取りうる手（**本文書では選ばない**）

| # | 手 | 備考 |
|:-:|:---|:---|
| 1 | 文書側を実態に合わせる（「書ける」と明記し、読み取り専用を安全根拠から外す） | 最小コスト。ただし**安全性そのものは回復しない** |
| 2 | 該当 agent の `memory:` を外す | 蓄積した agent-memory の配送が止まる。`gabriel` は 12 件中 memory 実績の有無を要確認 |
| 3 | 機構で守る（Outbound Write Ban と同型の hook で、特定 agent の Write を deny） | 実装コスト大。ただし**唯一、実効を回復する手** |
| 4 | 何もしない（リスクを受容する） | gabriel は毎回 L1 が「編集するな」と明示している運用実績がある = プロンプト依存の防御 |

---

## 2. hooks / 権限（乖離 6 件 / L1 が `settings.json` を実測して裏取り済）

**`.claude/settings.json` の実測**: allow 29 / ask 17 / deny 16。

| # | 内容 | 条文 | 実装 | 安全側 |
|:-:|:---|:---|:---|:---|
| D-1 | **out-of-root パス**の PM 判定が条文の表に無い | 記載なし | `pre-tool-use.py:114` `^__out_of_root__/` | 実装 |
| D-2 | PLANNING 許可の `.claude/states/` が**拡張子無制限** | `*.json` のみ | `^\.claude/states/`（全ファイル） | 条文 |
| D-3 | **`mv`** が条文 Ask / 実装 Deny | Ask（引数明示） | `Bash(mv *)` = deny | 実装 |
| **D-4** | **`git push --force` / `git reset --hard` の deny が実装に無い** | Deny を明示要求 | deny 16 件に**不在**。`Bash(git push *)` は ask のみ | **条文** |
| **D-5** | **`curl \| bash` / `wget <不明ホスト>` の deny が実装に無い** | Deny を明示要求 | deny に**不在**。`Bash(curl *)` `Bash(wget *)` は ask のみ | **条文** |
| D-6 | allow の lint / format / gitleaks / py_invoke 群（10 件）が**マトリクス表に無い** | 表に行なし（別節 §79 で一般論のみ言及） | allow に実在 | 記述漏れ |

**D-4 / D-5 の読み方**: `security-commands.md` は D-4 に「AutoMode soft_deny と二重」と注記しており、**Layer 1 単独での防御を前提していない**可能性がある。ただし条文の表は「Deny（実行禁止）」列に置いており、表だけを読む者は Layer 1 で止まると理解する。**実害の有無は AutoMode 側の挙動に依存し、本掃きでは未検証。**

**検査の不在**: `permissions.allow/ask/deny` の**配列内容そのものを検査するテストは 0 件**（`settings.json` を扱うテストは hook 起動経路のポータビリティ検査のみ）。out-of-root の PM 分類テストも無い。

> **`settings.json` は AI が編集できない**（auto-mode のハードブロック）。修正は「**案提示 → ユーザーが手動編集 → AI が検証**」の 3 手順を要する。

---

## 3. MAGI / skills（乖離 3 件）

| # | 内容 | 実態 | 影響 |
|:-:|:---|:---|:---|
| M-1 | `SKILL.md:142`「全 **8** パターンを網羅」 | 実装の `Action` は **9 種**（`escalate_critical_max` = 再 MAGI 2 回目が別行）。テスト側コメントも「全 **9** 分岐」と自己申告 | 実行時挙動は正しい。「8」を信じて保守すると 9 番目を見落とす |
| M-2 | `SKILL.md:112`「Read/Glob/Grep/**Write/Edit** のみ利用可」 | **実体と一致していた**（§1 の canary により、これが唯一正しい記述だったと判明）。一方 `gabriel.md:228` の「Write/Edit を持たない」と `SKILL.md:317`「書き込み権限: CASPAR のみ」が実態と食い違う | §1 に統合 |
| M-3 | `docs/specs/magi-skill-spec.md`（v1.0 / **draft** / 2026-03-16）が **gabriel 統合前の Reflection 仕様のまま** | `magi-v2-gabriel/requirements.md` v0.4.0（Approved）が Reflection 廃止を MUST 化済。実装は後者に追随 | 実行時影響なし（どこからも参照されない）。ただし `docs/specs/` 直下に draft のまま在り、**仕様アーカイブとして読む者を誤誘導** |

> **M-2 の逆転に注意**: 当初「SKILL.md が誤記」と見えたが、canary の結果は逆で、**誤っていたのは agent 定義自身の自己記述**だった。条文同士の突合だけでは向きを誤る。

---

## 4. モデル・委譲（乖離 1 件 / 安全側）

`hga-summoning.md` が名指しする **`disallowedTools: [Agent]` は、リポジトリ内に 1 件も存在しない**（12 件 grep で 0 マッチ）。実装は `tools:` の正リスト方式で同じ目的を達成しており（11/12 は `Agent` を持たず、`goal-driven-l2-foreman` のみ `Agent(goal-driven-l3-executor)` とスコープ限定）、**機能的には安全側**。

ただし条文が指す安全網の**形**が存在しないため、将来 `tools:` に `Agent` が足された場合、条文の想定は働かない。

**一致した項目**（記録）: 層 → モデル束縛（sonnet 9 / haiku 3 / opus 0）/ hooks 全 5 件が `type: command` / py_invoke の Context 別 form（settings.json 5 件は env var 形式・skills 29 箇所すべて相対パス・混入 0）/ 全 12 件に `memory: project` と保存先ディレクトリ / 受領側の恒久制約 12/12。

> **既存機構の射程の限界**: `verify_model_reference.py` は `_iter_scan_lines` で **frontmatter ブロックを明示的にスキップ**するため、`model:` / `memory:` の値自体は検査対象外。「機構があるから守られている」は成り立たない領域だった。

---

## 5. 台帳・自動生成ルール（乖離 0）

13 対すべて一致。特筆すべきは **§C R3 台帳の機構 9 件について、判定コマンドを実際に実行して全通過**を確認したこと（21 / hook 直接実行 / 18 / 1 / 18 / 21 / 24 / 18 / 1 passed）。§A の R2 表 6 ファイルも実測集合と一致。`rule-001` が指定するテスト名 2 件、`rule-002` の参照先 4 ファイルもすべて実在。

### 観測（乖離ではない / 記録のみ）

機構 #1 を**複数の pytest と並列実行**した際、`test_debt_detector_accepts_settlement` の teardown で「計器隔離ガード: テストがリポジトリ実体の計器を書き換えた（`.claude/logs/permission.log`）」という ERROR が 1 件発生した。**単独再実行では再現せず**（21 passed / error 0）。原因は他プロセス由来の hook ログ書込を機構 #8（計器隔離ガード）が横から観測した相互干渉と推定される（**未検証の仮定**）。

**`security-commands.md` §計器への書き込みを伴う検証**が「計器に書き込みうる検証の前に隔離を確認せよ」と定めた条項の、**射程外の失敗形**である可能性がある（条項は手動実行を想定しており、並列 pytest は想定していない）。

---

## 6. 仕分けと次の手（**本文書では実施しない**）

| 優先 | 件 | 等級 | 誰の手が要るか |
|:---:|:---|:---|:---|
| **1** | §1 読み取り専用の保証の破れ（gabriel / goal-driven-grader） | 文書修正なら SE、機構化なら PM | 判断はユーザー。手 3（機構）を採るなら実装は L1 |
| **2** | D-4 / D-5（deny の不在） | **`settings.json` は AI 編集不可** | 案提示 → **ユーザーが手動編集** → AI が検証 |
| 3 | M-3（`magi-skill-spec.md` の陳腐化 / draft 放置） | PM（`docs/specs/`） | superseded マークか削除かの判断 |
| 4 | M-1（8 vs 9）/ D-6（マトリクス記述漏れ）/ D-1・D-2（条文の記載精度） | PM（条文修正） | まとめて 1 承認で処理可能 |
| 5 | §4 `disallowedTools`（安全側 / 実害なし） | PM | 条文を実態に合わせるか、形を実装に入れるか |
| 6 | §5 の並列実行時 flaky | SE | 再現条件の特定が先 |

**共通の教訓**: 今回 11 件のうち **最も重いものは条文同士の突合では見つからず、登録情報との食い違いに気づいた L1 が canary を実測して初めて確定した**。「文書 A と文書 B が一致しているか」の検査は、**両方が同じ思い込みを共有している場合に無力**である。
