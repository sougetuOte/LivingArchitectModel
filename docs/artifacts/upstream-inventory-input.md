# upstream 棚卸し Milestone — 入力リスト

**作成日**: 2026-07-26
**位置づけ**: M-1 完了後に実施予定の「upstream 仕様との棚卸し」Milestone（ユーザー決定 / 2026-07-25）の**入力**を 1 箇所に集約したもの。
**権限等級**: SE 級（`docs/artifacts/` 配下 / 判定を含まない収集物）

> **本文書は入力の一覧であり、判定ではない。** 各項目を「新設 / 既存条項へ吸収 / 見送り」のどれにするかは棚卸し Milestone の PLANNING で決める。
> **M-1 中に本リストの内容を規律ファイルへ反映してはならない**（design §5.3 の閉集合 / トリアージ表は W1-M1-T6 で承認済み。条項が増えれば判定のやり直しになる）。

---

## A. 委譲・subagent 系

| # | 内容 | 出典 | 現状 | 想定反映先 | 等級 |
|:-:|:-----|:-----|:-----|:-----------|:----:|
| A1 | **親検収に「spec 名指し項目の grep 突合」を組み込む** | `retro-M1-W1-2026-07-25.md` §6.2 A2（M-1 P2 = 委譲成果物の 5 種適用漏れ） | **未反映**（2026-07-26 grep 確認） | `.claude/rules/model-delegation-prompting.md` | PM |
| A2 | **抽出系委譲では「基準の一貫性」を完了条件に明記**（「同一列挙内で一部だけ抽出しない」を boundaries へ） | 同 §6.2 A4（M-1 P5 = 条項 ID の再採番） | **未反映**（同上） | 同上 | PM |
| A3 | **subagent boundary に「scratchpad 領域への書込禁止」を明示** | `retro-R1-2026-07-18.md` T24（P10 = boundary_deviations 2 件） | **未反映**（「R-2 で次 Sonnet 委譲時に反映」とされたまま滞留） | 同上 | PM |
| A4 | **委譲の振り分け判定を規律へ昇格** — 委譲可否は F0 の「検証方法」が実コマンドで書けるかで決める | `docs/artifacts/knowledge/l2-delegation-guardrails.md` §8（2026-07-26 / §7 の昇格条件を充足済と記録） | knowledge 層（SE 級）に存在 | 同上 | PM |
| A5 | **`hga-summoning.md` の引用偏りを是正** — Anthropic 推進側のみ引用しており、Cognition「Don't Build Multi-Agents」と MAST（arXiv 2503.13657）が未収載 | 同 §8.6（2026-07-26 調査） | 偏りあり | `.claude/rules/hga-summoning.md` | PM |
| A6 | **「親の auto memory は subagent にロードされない」という公式明文を根拠に加える**（委譲＝文脈の切断の一次資料裏づけ） | [Memory — Claude Code Docs](https://code.claude.com/docs/en/memory) §Auto memory「The main conversation's auto memory isn't loaded into subagents」 | knowledge §8.3 に出典未記載 | knowledge §8.3 追記（SE）→ 昇格時に A4 へ統合 | SE / PM |

> **A1〜A4 は同一ファイル（`model-delegation-prompting.md`）への追記に集約できる**。個別に条項を増やさず、1 回の改訂でまとめて入れることを検討する（規範ストックを増やさない方針と整合）。

---

## B. Opus 5 プロンプトガイド系

出典はすべて memory `opus-5-prompting-guide`（原典: `D:\work7\2026-07-26Opusプロンプトガイド\readme.md` / 公式 `/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5`）。
`model-delegation-prompting.md` は **Sonnet 5 / Haiku 4.5 向け**であり、**Opus 5（L1 自身）向けの対応文書は LAM に存在しない**。

| # | ガイドの項 | LAM 側の状態 | 想定反映先 | 等級 |
|:-:|:-----------|:-------------|:-----------|:----:|
| B1 | **#1 応答が長い**（effort は思考量を制御し発話量を制御しない / 応答長は明示指示が必要） | **対応条項が不在** | 新設 or 既存へ吸収（判定は棚卸し時） | PM |
| B2 | **#2 narration しがち**（カデンスと形を明示せよ / 肯定形の例示が有効） | `fable-l3-protocol.md` §5「60 秒実況」・`CLAUDE.md`「逸脱を 1 行で可視化」と**競合しうる** | 整理が必要（削るのではなく位置の再設計） | PM |
| B3 | **#3 ディスクに書く成果物が長い**（filler・冗長な要約・boilerplate で膨らませるなの明示が要る） | **長さキャリブレーションが不在**。実測: トリアージ表 438 行 / design.md 740 行 | 新設 or 既存へ吸収 | PM |
| B4 | **#5 委譲しすぎる**（数回のツール呼び出しで済む仕事を委譲するな / 自己出力の検証に subagent を使うな） | knowledge §8 が独立に同じ結論に到達 | **A4 と統合して 1 件で処理**（二重に条項化しない） | PM |
| B5 | **#6 自己修正する**（「ダブルチェックせよ」型は不要でコスト増） | `fable-l3-protocol.md` §4 自己監査 14 項目が #4 と同じクラス。M-1 W1 で 4 件削減 / 2 件圧縮済 | **残りの扱いのみ**（W1 処理分と二重にしない） | PM |
| B6 | **effort sweep のやり直し**（前世代から effort 既定を引き継いだ場合） | 未実施 | 運用（規律ファイル不要） | SE |

> **#4「過剰検証」は M-1 W1 の基質適合テストで消化済み**（名指し候補 21 件中 16 件を無効化 → 削減）。**二重処理しないこと。**

---

## C. Claude Code プラットフォーム仕様系

| # | 内容 | 状態 | 扱い |
|:-:|:-----|:-----|:-----|
| C1 | **`paths:` の発火条件** — 「Path-scoped rules trigger when Claude **reads** files matching the pattern, not on every tool use」（[Memory docs](https://code.claude.com/docs/en/memory)）。Write 経路では発火しない。既存ファイルの Edit / 上書き Write は harness が事前 Read を強制するため実質発火する | **2026-07-26 確定** | **M-1 W2 の入力**（棚卸し対象外 / 本リストには記録のみ） |
| C2 | **`InstructionsLoaded` hook** — どの instruction ファイルが・いつ・なぜロードされたかをログでき、公式が「path-specific rules のデバッグに有用」と明記 | **2026-07-26 に導入見送りを決定**（ユーザー判断 / C1 の明文で足りるため）。`.claude/settings.json` 編集が必要 = PM 級かつ AI 編集ハードブロック | 将来の再検討候補 |
| C3 | **memory tool（public beta）の Claude Code 提供有無** | 調査中（本セッションで L2 委譲） | 結果を本リストに追記 |
| C4 | **rules のバージョン依存挙動** — v2.1.198（symlink 経由のマッチ）/ v2.1.207（invalid glob の扱い）/ v2.1.211（`--setting-sources` から project 除外時の on-demand rules）/ v2.1.217（brace 展開の budget） | 未突合 | LAM の想定 CC バージョンと突合が必要 |
| C5 | **並列共有 XML の誤採用**（並列 subagent の pytest で `-o addopts=""` を使い JUnit XML を更新しない運用） | M-1 スコープ外 pending | 実害が出たら起票 |

---

## E. 外部パターンからの改良候補（セッション継続機構）

出典: [Memory tool — Claude Docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool) §Multisession software development pattern / [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)（2026-07-26 調査）。

**前提**: 公式パターン（initializer session → progress log → feature checklist → end-of-session update）は **LAM が独立に到達済み**である。以下は対応物の突合で見つかった**欠落 3 点**のみを挙げる。パターン全体の導入は不要。

| 公式パターンの要素 | LAM の対応物 | 状態 |
|:---|:---|:---|
| progress log | `SESSION_STATE.md` | あり |
| feature checklist（pass/fail 状態つき） | `tasks.md` の `- [ ]` | あり |
| subsequent session が読んで開始 | `/quick-load` | あり |
| end-of-session update | `/quick-save` | あり |
| **startup / initialization script への参照** | — | **欠落 → E1** |
| **各セッション冒頭の health check** | — | **欠落 → E1** |
| **完了マークは end-to-end 検証後** | Green State はあるが Task 単位の規律が曖昧 | **部分的 → E2** |

| # | 改良候補 | 根拠・実害 | 想定反映先 | 等級 |
|:-:|:---------|:-----------|:-----------|:----:|
| E1 | **`/quick-load` にセッション冒頭の health check を追加**（pytest 1 回 + 現行 Milestone の検証コマンドへの参照を `SESSION_STATE.md` に持たせる） | 公式ハーネスは「各セッションは開発サーバ起動と基本動作テストから始める」。**実害が出ている**: 2026-07-26 セッションは pytest を一度も回さず、Opus 5 安定性ゲートの条件 2（regression ゼロ）が「本セッション未実行」のまま宙に浮いた。冒頭で 1 回回せばゲート材料が毎セッション自動で貯まる | `.claude/skills/quick-load/SKILL.md`（SE）+ `SESSION_STATE.md` テンプレ | SE |
| E2 | **完了マークの規律を明文化** — 「コードを書いた時点ではなく **end-to-end 検証が済んだ時点で**完了とマークする」。`tasks.md` checkbox の更新タイミングを規定 | 公式の Key principle。LAM には F0 の「検証方法」があり原理は揃っているが、checkbox 更新の時点が未規定。**B-5 W8 で L2 が T100-T106 完了時に §3.5 checkbox を `[ ]` のまま残した**（`retro-B5-W8-WC-2026-07-05.md`）のと同じ穴 | `.claude/rules/phase-rules.md` BUILDING §F0 近傍 or `model-delegation-prompting.md` | PM |
| E3 | **ASSUME INTERRUPTION の原則を L1 自身に適用** — 「context はいつリセットされてもおかしくない。記録していない進捗は失う前提で逐次書く」 | memory tool の system prompt に明文（"ASSUME INTERRUPTION: Your context window might be reset at any moment, so you risk losing any progress that is not recorded in your memory directory"）。LAM の `/quick-save` は 180K/200K の**閾値発火**であり逐次記録の原則がない。**2026-07-26 に subagent の boundaries へ入れた「N 件ごとに進捗を追記せよ」と同型のものを、L1 自身には適用していない** | `CLAUDE.md` §Context Management | PM |

> **E1 を先に**。SE 級で単独完結し、E2/E3 の効果測定にも使える（health check が入れば「セッションごとの regression 有無」が実データで残る）。
> **E3 は §8.5 の帰結と同じ構造**（親が subagent に課した規律を親自身が守っていない）。knowledge §8 の昇格（A4）とまとめて扱うと重複を避けられる。

---

## D. 本リストの対象外（重複防止のため明記）

| 項目 | 理由 |
|:-----|:-----|
| Opus 5 ガイド **#4 過剰検証** | M-1 W1 の基質適合テストで消化済（B 表の注記参照） |
| Opus 5 ガイド **#7 thinking 無効時の artifact** | LAM は thinking 既定 ON のため現状該当しない |
| **ADR-0001 #3 の発生時期** | upstream 仕様と無関係（本セッションの別タスクで調査中） |
| **ゲート母数定義の逆インセンティブ** | M-1 の W4-M1-T5 retro 議題（`m-1-baseline-w1.md` §3.2） |

---

## 参照

- `docs/artifacts/retro-M1-W1-2026-07-25.md` §6.2（A1 / A2 の起票元）
- `docs/artifacts/retro-R1-2026-07-18.md` T24（A3 の起票元）
- `docs/artifacts/knowledge/l2-delegation-guardrails.md` §8（A4 / A5 / A6 の根拠）
- memory `opus-5-prompting-guide`（B 全項の出典 / 原典は上記ローカルコピー）
- `.claude/rules/model-delegation-prompting.md`（A1〜A4 の想定反映先 / 2026-07-26 時点で該当記述なしを grep 確認）
- `docs/specs/m-1-opus5-migration/design.md` §5.3（閉集合 = M-1 中に反映しない根拠）
