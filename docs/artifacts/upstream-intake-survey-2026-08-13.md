# Upstream 取り込み判断用 事実調査報告書（2026-08-13）

**作成**: L2 調査担当（cc-update-survey 系列）/ 調査のみ・採否判断は含まない
**一次資料取得日**: 2026-08-13（WebFetch / 15 分キャッシュ）

## 要約（5 行）

1. §A: upstream「Resume from summary」は**同一セッションの transcript 内**で history を要約置換する機構。quick-save の保存物 9 要素中、**完全カバーは 0**・部分カバー 4・非カバー 5（Daily / KPI / ループログ / ダッシュボード / rule-001 連動は全て非カバー）。
2. §B: 公式 docs の現行記述では **1M モデルの既定 auto-compact は「モデルの context limit 到達時」**であり、200K 発火は `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` 等の**列挙された例外時のみ**。CLAUDE.md 注記の仮説「1M でも 200K 付近で発火」は**現行公式挙動としては確認できない**（2026-06-06 観測当時の挙動は別問題 / unverified）。
3. §B 補足: v2.1.223 は「1M モデルを 200K に抑える」変更を入れたが、それは **env var 設定時の enforcement 拡大**であり既定挙動の変更ではない。`/autocompact <値>` で発火点は 100K〜1M にユーザー設定可能。
4. §C: メモリ（2026-07-25）の「#1/#3/#5 は LAM に対応条項不在」のうち **#1・#3 は現在も不在（drift なし）**、**#5 は部分 drift**（2026-07-26 の model-roster.md §2 閾値 1 が委譲抑制側の基準を新設済み）。
5. 本報告書は事実整理のみ。改稿案テキスト（§B.3）は判断材料であり適用は L1・ユーザーの決定に委ねる。

---

## §A. "Resume from summary" と /quick-save・/quick-load の機能比較

### A.1 quick-save / quick-load が実際に保存・復元しているもの

出典: `.claude/skills/quick-save/SKILL.md`（全 97 行）/ `.claude/skills/quick-load/SKILL.md`（全 38 行）。

**quick-save の保存物**（SKILL.md の節番号で列挙）:

| # | 保存物 | 出典 (file:line) | 実体 |
|:-:|:--|:--|:--|
| 1 | `SESSION_STATE.md`（プロジェクトルート / gitignore 済） | quick-save/SKILL.md:14-37 | 完了タスク / 進行中タスク / 次のステップ（優先順位付き）/ 変更ファイル一覧 / 未解決の問題 / コンテキスト情報（フェーズ・git ブランチ・関連 SPEC/ADR/設計書名） |
| 2 | ループログの記録取り込み | quick-save/SKILL.md:39-42 | `.claude/logs/loop-*.txt` が存在する場合に未コミット分を記録へ含める（スキーマ: `docs/specs/loop-log-schema.md`） |
| 3 | Daily 記録 | quick-save/SKILL.md:44-56 | `docs/daily/YYYY-MM-DD.md` に本日完了 / 明日の最優先 / 課題・気づき |
| 4 | KPI 集計 | quick-save/SKILL.md:57-65 | `loop-*.txt` から K1〜K5、`permission.log` から PG/SE/PM 等級分布（定義: `docs/specs/evaluation-kpi.md`） |
| 5 | ダッシュボード更新（SHOULD） | quick-save/SKILL.md:85-97 | `build_dashboard.py` → `docs/artifacts/dashboard/dashboard.html` |

**quick-save が明示的にやらないこと**: git commit（quick-save/SKILL.md:11「git commit は行わない（コミットは `/ship` を使用）」）。

**rule-001 retention 確認との関係**: `SESSION_STATE.md` を編集する際は Milestone 表記（`[A-Z]-\d+`）と Wave 表記を最低 1 箇所残し、編集後に parser retention テスト 2 件（`test_parse_real_session_state_contains_milestone` / `_contains_wave`）を回すことが `.claude/rules/auto-generated/rule-001.md` §ルール で定められている。**quick-save/SKILL.md 自体にはこの確認手順への言及がない**（同 SKILL.md を `retention|pytest` で Grep → 0 件 / 本セッション実測）。rule-001 観測 #5（2026-07-27）は quick-save 実行時の全面書き換えで Wave 表記が消えた事例（rule-001.md §根拠パターン #5）。

**quick-load の復元物**（quick-load/SKILL.md:12-38）: `SESSION_STATE.md` の読込 → 「コンテキスト情報」から次のステップに必要な関連ドキュメントの**特定のみ**（読込は遅延 / :20「読み込みはまだ行わない」）→ 復帰サマリー報告 → ユーザー指示待ち。**transcript（会話履歴）には一切依存しない** — 新規セッション・`/clear` 後・別マシンでも SESSION_STATE.md がディスクにあれば機能する。

### A.2 upstream "Resume from summary" が転送するもの

出典: https://code.claude.com/docs/en/sessions §Resume from a summary（2026-08-13 取得）。

- **発動条件**: Pro / Max プランで、**約 1 時間以上非アクティブ**かつ **100,000 tokens 超**のセッションを resume したとき、最初のメッセージ送信前にダイアログが開く（同ページ逐語: "when you resume a session that has been inactive for more than about an hour and is over 100,000 tokens"）。
- **動作**: `/compact` を即時実行する。逐語: "runs /compact immediately. Claude Code sends one summarization request over the full history, then replaces the history with the summary, your most recent exchanges, and up to five recently read files."
- つまり**転送物は 3 つ**: (1) 全履歴の要約（内容はモデル生成 / 非決定的）、(2) 直近のやり取り、(3) 直近に読んだファイル最大 5 件。
- **失われるもの**: 要約が落とした詳細はコンテキストから消える（逐語: "whatever the summary leaves out is no longer in Claude's context"）。
- **compaction を生き残る恒久機構**（https://code.claude.com/docs/en/context-window §What survives compaction / 2026-08-13 取得）: system prompt / プロジェクトルート CLAUDE.md と unscoped rules（ディスクから再注入）/ auto memory（再注入）。一方 `paths:` 付き rules と nested CLAUDE.md は**失われる**（該当ファイル再読込まで）。skill 本文は再注入だが 1 skill 5,000 tokens・合計 25,000 tokens で truncate。
- なお通常 resume（summary 経由でない）が復元するのは会話履歴・モデル・agent・permission mode・active goal・scheduled tasks 等（sessions ページ §What a resumed session restores）。

### A.3 対応表: quick-save 保存要素 × Resume from summary のカバー

判定凡例 — **される**: 同等の内容が確実に転送される / **部分的**: 要約に含まれ得るが構造・網羅の保証がない / **されない**: 機構上転送されない。

| quick-save の保存要素 | Resume from summary でのカバー | 根拠 |
|:--|:--|:--|
| 完了タスク・進行中タスク・次のステップ | **部分的** — 要約に含まれ得るが、構造（優先順位付き箇条書き）と網羅の保証がない。要約が落とせば消える | sessions §Resume from a summary（"whatever the summary leaves out is no longer in Claude's context"） |
| 変更ファイル一覧 | **部分的** — 「直近に読んだファイル最大 5 件」+ 要約言及分のみ。5 件超・読んでいないが変更対象だったファイルは保証外 | 同上（"up to five recently read files"） |
| 未解決の問題 | **部分的** — 同上（要約依存） | 同上 |
| コンテキスト情報（フェーズ / ブランチ / SPEC・ADR 名） | **部分的** — 要約依存。ただしフェーズの SSOT は `.claude/current-phase.md`（ディスク）でありどちらの機構にも依存しない（memory: phase-ssot-is-md-not-json） | 同上 |
| ループログ記録の取り込み（`.claude/logs/loop-*.txt`） | **されない** — Resume from summary はディスクファイルを生成・収集しない | sessions §Resume from a summary（転送物は summary + recent exchanges + 5 files のみ） |
| Daily 記録（`docs/daily/*.md`） | **されない** — 同上。ディスクへの日次記録という成果物自体が生成されない | 同上 |
| KPI 集計（K1〜K5 / 等級分布） | **されない** — 同上 | 同上 |
| ダッシュボード更新（dashboard.html） | **されない** — 同上 | 同上 |
| rule-001 retention 検査（SESSION_STATE.md 編集の付随義務） | **されない** — SESSION_STATE.md 自体を読み書きしないため、義務も検査も発生しない | rule-001.md §適用範囲（対象操作 Edit/Write）+ sessions ページ |

### A.4 機構としての差（事実整理）

| 軸 | /quick-save + /quick-load | Resume from summary |
|:--|:--|:--|
| 保存先 | プロジェクトディスク（SESSION_STATE.md / docs/daily/ / dashboard） | 当該セッションの transcript（`~/.claude/projects/<project>/<session-id>.jsonl`） |
| 到達経路 | 任意の新規セッション・`/clear` 後・`claude -c` いずれからも `/quick-load` で読める | **同一セッションを resume したときのみ**。新規セッションには効かない |
| 発動条件 | ユーザーが任意時点で実行 | Pro/Max + 非アクティブ約 1h + 100K tokens 超のときだけダイアログ提示 |
| 内容の決定性 | SKILL.md のテンプレートに従う構造化記録 | モデル生成の要約（非決定的） |
| 副産物 | Daily 記録・KPI・ダッシュボード（プロジェクト履歴として蓄積） | なし |
| 重複しうる部分 | 「前回何をやって次に何をするか」をコンテキストへ復帰させる、という目的部分 | 同左（A.3 の「部分的」4 行が重複域） |

---

## §B. CLAUDE.md §Context Management 注記の確定化材料

### B.1 現行の注記（読み取りのみ / 編集していない）

`CLAUDE.md`:216-221 の注記は「1M モデルでも auto-compact が 200K 付近で発火する」を 2026-06-06 観測（400k→131.8k 圧縮）に基づく**仮説（未確定）**とし、実測確定後に更新すると定めている。閾値運用（180K で quick-save 提案 / 200K 超で新セッション推奨）は `CLAUDE.md`:198-206。

### B.2 upstream 一次資料の裏取り結果

**(1) 既定の auto-compact 発火点** — https://code.claude.com/docs/en/model-config §Default auto-compact thresholds（2026-08-13 取得）:

> "If you don't set an auto-compact window, Claude Code compacts when the conversation reaches the model's context limit, except in these sessions:"

例外として列挙されているのは: Cloud sessions（limit 接近時）/ **200K ウィンドウで動く場合の** Sonnet 4.6・Opus 4.6・Opus 4.8・Opus 5（Bedrock 等）/ `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` 設定時の native 1M モデル（Sonnet 5・Fable 5 等）/ Sonnet 5 の構成別閾値 / 未認識モデル ID。

**(2) 1M モデルの具体値** — 同 §Sonnet 5 context window:

> "Sessions auto-compact before the window fills, at about 967K tokens by default"

（Sonnet 5 の例。1M ウィンドウのモデルは既定では 200K ではなく limit 付近で compact する、という現行記述の具体例。）

**(3) 200K 抑止は env var の機能** — 同 §Extended context:

> "To turn off 1M context, set `CLAUDE_CODE_DISABLE_1M_CONTEXT=1`. ... With auto-compaction on, sessions compact at the 200K boundary"

**(4) v2.1.223 の変更内容** — https://github.com/anthropics/claude-code/releases/tag/v2.1.223（2026-08-13 取得 / release notes 逐語）:

> "Changed `CLAUDE_CODE_DISABLE_1M_CONTEXT` to hold every Claude model with a native 1M window to 200K via auto-compaction, not just a fixed list; a startup warning now appears when auto-compaction isn't holding the session to 200K"

および model-config §Extended context 末尾:

> "Before v2.1.223, Claude Code held only Sonnet 5, Opus 4.8, and Opus 5 sessions to 200K."

**(5) 発火点はユーザー設定可能** — model-config §Set the auto-compact window: `/autocompact <値>`（100K〜1M / `autoCompactWindow` 設定として保存）、`--autocompact` フラグ、`CLAUDE_CODE_AUTO_COMPACT_WINDOW` env var の 3 経路。

### B.3 裏取りの結論（事実）と改稿案

**結論**: 「1M モデルでも auto-compact が 200K 付近で発火する」は、**現行の公式ドキュメント上、既定挙動としては確認できない**。公式挙動は「既定 = モデルの context limit 到達時に compact / 200K 発火は列挙された例外条件（env var 設定・200K ウィンドウ動作・未認識 ID 等）のみ」。v2.1.223 の変更も既定を 200K にしたものではなく、**env var 設定時**の対象モデル拡大である。2026-06-06 観測（400k→131.8k）が当時の実挙動だったか・どの例外条件に該当したかは本調査では確認できない（**unverified** — 当時の CC バージョンと環境変数の記録が必要）。なお CLAUDE.md 注記が確定情報として併記する #65247（malformed と高コンテキストの相関）の実在は本調査では再確認していない（**unverified** / 調査スコープ外）。

**改稿案テキスト**（報告書内の案であり、CLAUDE.md は編集していない。適用判断は L1・ユーザー）:

```markdown
> **注記（2026-08-13 公式 docs 裏取り済）**: 公式ドキュメント（code.claude.com/docs/en/model-config
> §Default auto-compact thresholds / 2026-08-13 取得）によれば、auto-compact の既定発火点は
> 「モデルの context limit 到達時」であり、1M モデルが既定で 200K 付近で発火するという記述はない
> （200K 発火は `CLAUDE_CODE_DISABLE_1M_CONTEXT=1` 設定時・モデルが 200K ウィンドウで動作する場合・
> 未認識モデル ID の場合等の列挙例外のみ）。発火点は `/autocompact <値>`（100K〜1M）で明示設定できる。
> 2026-06-06 セッションの観測（400k→131.8k 圧縮）は当時のバージョン・環境条件が未記録のため
> 現行挙動への外挿はしない。本節の 180K/200K 閾値は「auto-compact 対策」ではなく
> 「malformed の高コンテキスト相関（upstream #65247）への保険」として維持根拠を持つ。
```

（最終文の #65247 の実在は unverified のまま既存注記から引き継いでいる。確定記述化の際は #65247 側も再裏取りが望ましい、というのが事実上の残課題。）

---

## §C. Opus 5 プロンプトガイド未反映 3 項目（#1/#3/#5）の現状確認

### C.1 メモリの主張

出典: `C:/Users/metral/.claude/projects/D--work7-LivingArchitectModel/memory/opus-5-prompting-guide.md`（2026-07-25 記録 / 18 日前）。§How to apply: 「特に #1 / #3 / #5 は LAM に対応条項が存在しないため、新設か既存条項への吸収かを棚卸し時に判定する」。

### C.2 現状 Grep による再確認

検索対象: `D:/work7/LivingArchitectModel/.claude/rules/` 全体 + `CLAUDE.md`（本セッション実測）。使用パターン: `簡潔|冗長|応答.{0,6}長|長さ|filler|boilerplate|verbosity|concise` / `応答|報告.{0,8}簡潔|出力.{0,6}長|成果物.{0,8}長|長さキャリブ|行数.{0,10}(上限|抑|目安)` / `委譲しすぎ|過剰委譲|over-deleg|数回のツール|委譲.{0,10}overhead` / `検証方法.{0,20}実コマンド|書けなければ L1 直`。

| 項目 | メモリの主張（2026-07-25） | 現状の実態（2026-08-13 Grep 実測） | drift |
|:-:|:--|:--|:--|
| #1 応答が長い（L1 応答の簡潔性指示） | LAM に簡潔性の指示は不在 | **不在のまま**。`.claude/rules/` の「応答」該当 4 件はすべて別文脈（safety routing 降格・meta-response 早期終了 / hga-summoning.md:88,209 / model-roster.md:144 / upstream-first.md:42）。L1 応答長を制御する条項なし。quick-save/SKILL.md:12 の「簡潔に実行」は skill 内ローカル指示であり L1 応答の一般規律ではない | **なし** |
| #3 ディスク成果物が長い（長さキャリブレーション） | 長さキャリブレーションは LAM に不在 | **不在のまま**。rules 内で「長さ」系ヒットは code-quality-guideline.md の「Long Function > 50行」（コード関数対象）のみで、文書成果物の長さ規律は 0 件 | **なし** |
| #5 委譲しすぎ（委譲抑制の基準） | 対応条項が存在しない | **部分的に存在するようになった**。`model-roster.md`:60（§2 閾値 1 / 2026-07-26 新設）「委譲可否の第一基準: F0 の『検証方法』が実コマンド 1 行で書けるか。書けなければ L1 直」（根拠 = `docs/artifacts/knowledge/l2-delegation-guardrails.md` §8 の 2026-07-25 実測 — メモリ #5 行が引く同一の失敗事例）。一方 `CLAUDE.md`:140「委譲を優先」/:157「迷ったら委譲側に寄せる」の委譲促進側規律は現存し、ガイド #5 の他の要素（「1 体で足りるなら 1 体」「自己出力の検証に subagent を使うな」）に対応する条項は**依然として不在** | **あり（部分）** — メモリ記録後の 2026-07-26 に委譲抑制側の基準が 1 本入った。全面不在という記述はもはや正確でない |

### C.3 補足事実

- メモリが「対応文書不在」の傍証として挙げる「`model-delegation-prompting.md` は Sonnet 5 / Haiku 4.5 向け」という位置づけは現存する（`model-roster.md`:200 参照欄: 「委譲プロンプトの書き方 / R2 = 条件ロード」/ 挙動デルタは §3 へ移設済）。Opus 5（L1 自身）向けのプロンプト規律ファイルは `.claude/rules/` に Grep で見つからない（パターン `Opus 5|opus-5|prompting-claude-opus-5` のヒットはすべて model-roster.md の価格・スペック・世代管理文脈 / hga-summoning.md:133 は単価比較）。
- ガイド原典のローカルコピー所在（`D:/work7/2026-07-26Opusプロンプトガイド/readme.md`）は本調査では開いていない（**unverified** — メモリ記載のまま）。

---

## 調査の限界（unverified 一覧）

1. 2026-06-06 の auto-compact 観測が当時の実挙動として正しかったか、およびその際の CC バージョン・env var 状態（§B.3）。
2. upstream issue #65247 の現在の状態（§B.3 / スコープ外につき未再確認）。
3. Opus 5 プロンプトガイド原典の現内容（§C.3 / ローカルコピー未読。項目 #1/#3/#5 の要旨はメモリファイルの記述に依拠）。
4. §C の「不在」判定は列挙した Grep パターンの範囲内での不在であり、パターン外の語彙で書かれた同等条項が存在する可能性は排除できない。
