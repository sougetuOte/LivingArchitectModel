# Fable-Alembic L3 Protocol (LAM 適用)

**制定日**: 2026-07-07
**根拠**: HGA #11 (案 D 直交軸接続確定) + HGA #12 (案 D 具体化 / 修正 3 点反映) / `docs/artifacts/hga-summon-log.md` §11-12
**位置づけ**: LAM は Fable-Alembic を L3 (深く同化) で運用する。本ファイルは L3 導入の SSOT。

## §0 導入宣言 (`etc-to-alembic` テンプレ準拠 / L3)

> 以下は `D:\work7\etc-to-alembic\README.md` §他プロジェクト向けセットアップテンプレートの原文を L3 で貼付したもの。SSOT の貼付場所は本ファイル (`.claude/rules/fable-l3-protocol.md` §0)。

### Fable-Alembic 連携 (受け入れレベル: **L3**)

Fable 5 の judgment heuristics を継承する `D:\work7\Fable-Alembic\` を、レベル **L3** で参照する。

#### 参照ファイル
- SSOT: `D:\work7\Fable-Alembic\knowledge\`
- 連携規律: `D:\work7\etc-to-alembic\README.md`

#### 読み込み規律
(レベル別マトリクス `D:\work7\etc-to-alembic\README.md` §レベル別の読み込み規律マトリクス に従う / L3 = 全 MUST 発動)

#### 書き込み境界 (全レベル共通、MUST NOT)
- `D:\work7\Fable-Alembic\` 配下への書き込み・編集は行わない
- Alembic への提案・観察の受け渡しは `D:\work7\etc-to-alembic\handoff\` を経由する

#### 模倣禁止 (L4 禁止)
- Fable の文体・比喩をコピーしない。判断の理由 (第 0 原則の 3 変数) を継ぐ
- 「Fable ならこう言いそう」を出力する誘惑にブレーキをかける

---

## §1 L3 宣言

LAM は Fable-Alembic (`D:\work7\Fable-Alembic\`) を **L3** で運用する
(`D:\work7\etc-to-alembic\README.md` §受け入れレベル 準拠)。

参考実装: `C:\etm-diary` (L3 運用中 / `fable-heritage.md`)。

L3 の意味: 第0原則を default 判断基準として採用 / 自己監査 14 項目を完了宣言前ゲート / 体験シミュを完了宣言 3 点で MUST 発動 / 実行プロトコル F0-F4 を BUILDING の運転規則として採用。

## §2 参照 SSOT (Outbound Write Ban 全レベル共通)

| # | ファイル | 用途 |
|---|---------|------|
| 1 | `D:\work7\Fable-Alembic\knowledge\Fable行動規範.md` | 判断規範 (第0原則 + 系(1)(2)(3)) |
| 2 | `D:\work7\Fable-Alembic\knowledge\自己監査チェックリスト.md` | 完了宣言前 14 項目 |
| 3 | `D:\work7\Fable-Alembic\knowledge\体験シミュレーション・プロトコル.md` | 60 秒実況 + §6 位置決め |
| 4 | `D:\work7\Fable-Alembic\knowledge\実行プロトコル.md` | F0-F4 運転規則 |
| 補 | `D:\work7\Fable-Alembic\knowledge\判断差分の予測.md` | 導入 retro 1 回のみベースライン照合 (§8 参照) |

**Outbound Write Ban** (全レベル共通 / MUST NOT): `D:\work7\Fable-Alembic\` 配下への書き込み・編集は行わない。
Alembic への感想・提案の受け渡しは `D:\work7\etc-to-alembic\handoff\` を経由する。

パス移動時の対応: Fable-Alembic 側のリポジトリ位置が変更された場合、本節のパスのみ更新すれば LAM 側の他規律は無変更で吸収する。

## §3 帳簿単一原則 (crux 5 対応)

成果物判定の帳簿は **Green State 1 冊のみ** (Critical/Warning 件数 / `.claude/rules/code-quality-guideline.md`)。

自己監査 14 項目 (§4) は**宣言イベントのゲート**であり、成果物に残るのは実況第 1 文 + △項目明記 1-2 行のみ。以下を明文で禁ずる:

- 自己監査結果の件数化 (「14 中 12 pass」等のスコア化)
- 監査履歴の記録簿化 (`docs/artifacts/` への保存禁止 / 導入 retro のベースライン照合は例外 §8)
- 自己監査 pass を Green State の第 6 条件として追加すること (二重帳簿化の芽)

**削減は正義ではない** (Fable 規範追記 (3)): 帳簿単一化は Green State の客観性を守るためであり、Fable 側の受け手体験シミュレーションという「命綱」を落とすことは目的ではない。半分だけの移植 (削減の色だけ規範化し命綱を落とす) は移植しないより悪い。

## §4 自己監査 14 項目 (完了宣言前 / knowledge/自己監査チェックリスト.md 準拠)

宣言直前に走らせる。全 14 項目は原典 (`knowledge/自己監査チェックリスト.md`) を正本とし、**LAM が条文として明示的に持つのは以下 2 群のみ**。他の群 (A 要求照合 / B 動作事実 / E 報告) は基質の既定挙動として条文を持たない (M-1 W1 判定 / 判定根拠は `docs/artifacts/m-1-triage-table.md`)。

**C. 波及** (8-10): 同型パターン検索 (△: 検索と 1 件目修正必須) / 嘘文書更新 (△) / 数値検算 — **全域の同型パターン検索は既定挙動ではない**（rule-001 / rule-002 の parser drift 再発 = 計 7 検出イベントが実測発火）

**D. 受け手体験** (11-12): §5 の 60 秒実況を正本とする (二重生成しない) / 「明日困ること」(△)

## §5 体験シミュ発火点 (D-2 対応 / 3 点のみ MUST)

以下 3 点でのみ「60 秒実況 MUST」を発動する。それ以外での MUST 発動は形骸化リスクを持ち込むため禁ずる。

### §5.1 発火点

1. **PLANNING 承認要求提出直前** (`phase-rules.md` PLANNING §承認ゲート / 各成果物毎 3 発火)
2. **`/ship` Phase 3-4 境界 = Phase 3.5** (`.claude/skills/ship/SKILL.md`)
3. **AUDITING 監査レポート提出直前** (`phase-rules.md` AUDITING §レポート形式)

### §5.2 強制部品

- **60 秒実況 3-5 文** (原典 §3-4 / 主語は受け手 / 詰まる・迷う・イラつく瞬間を拾う / 成果物の説明文になったら失敗)
- **詰まり仮説 1 行を先に立てる** (原典 §4-1 書式規則 / 形骸化サイン検知)
- **実況第 1 文を成果物に残す** (テンプレ化ガード外形証跡 / 監査項目 11 準拠)
- **書けない場合は宣言中止** (原典 §4 表(e) / 唯一の例外 = 確信度判定を経ずに受け手をユーザー確認可)

### §5.3 位置決め (原典 §6)

要素の負荷は「存在ではなく位置で決まる」。要素採否 (§5.2) と位置決めは独立判断。教材・技術文書・エラー報告・UI フロー等で位置の負荷差が効く場合は原典 §6 の細分実況 (10 秒×6 コマ) を追加適用する。

### §5.4 テンプレ化ガード (HGA #12 Q6 修正反映)

Opus-tier で 60 秒実況が形骸化しないためのガード:

- **ガード 2 (同型構文検出)**: 過去 3 回分の実況第 1 文を並置し構文が同型なら形骸化として原典 §4-1 書式規則 (「詰まり仮説 1 行を先に立てる」) を再注入 + retro 議題化。**発火点数の一時的減少は禁止** (検知器自体が減る)
- **ガード 4 (残置 2 行拡張)**: 実況第 1 文だけでなく**詰まり仮説 1 行 + 実況第 1 文の 2 行**を成果物に残す。後付け違和感 (実況を書いてから違和感を作文する形骸化) を証跡構造で検出可能にする
- **ガード 5 (受け手制約必須)**: 受け手指定に必ず制約 1 つを付ける (時間がない / 文脈を知らない / 前提が 1 個抜けている 等 / 原典 §1 例 B が原型)。「全部読む従順な読者」を走らせると詰まりようがない

意味判定 (同型構文) は hook で機構化不能 (正規表現では精度が出ない)。ガード 2 は `/retro` バッチで L3 判定 (事実突合の既存運用圏内)。第 1 文の存在チェックのみ hook で機構化可能。

## §6 F0-F4 埋込 (BUILDING / 実行プロトコル.md 準拠 / HGA #12 Q4 修正反映)

実行プロトコル Phase 0-4 は LAM 内では **F0-F4** と表記する (`.claude/rules/terminology.md` の Phase/Step/Wave 名前空間と衝突回避 + 出自明示)。

### §6.1 発火粒度と省略基準

- **発火粒度**: `docs/specs/<milestone>/tasks.md` の Task 単位 (例: W7-B4-T9) を 1 単位とする。TDD 1 サイクル毎に F0 生成は儀式過剰
- **省略基準**: 3 手未満の自明タスクは F0-F2 を省略可 (原典冒頭「衝突した場合は第0原則が勝つ」+ 省略基準 / F3-F4 は省略不可)

### §6.2 F0 (4 行アンカー / 常時)

BUILDING 開始時、`phase-rules.md` BUILDING §必須「実装前に `docs/specs/` を確認」の**直後**に発火:

- 完了条件 (観測可能な形で)
- 検証方法 (実コマンド or 手順 1 つ)
- やらないこと (スコープ拡大の錨)
- 受け手 (規範§5「受け手を特定する」/ §5.4 ガード 5 の制約付き)

F0 は常時発動 (AoT 適用でも軽量モードでも実施)。

### §6.3 F1 (事実/仮定/不明の仕分け)

**AoT Atom Decomposition から除外し、Atom 分解の前段として維持する** (HGA #12 Q4 (l) 判定)。

Atom 分解の 3 条件 (自己完結性 / 契約 / エラー隔離) には F1 に対応する要素がない。F1 を落とすと Atom の入力自体が「事実のふりをした仮定」で汚染されるため、F1 は AoT 適用時でも各 Atom の前提への事実/仮定タグ付けとして維持する。

依頼文中の名詞 (ファイル名・関数名・「〜のはず」) に仮定タグを付ける。

### §6.4 F2 (リスク順分解)

**AoT 適用時は Atom Decomposition で置換される**。軽量モード (非 AoT) では F2 のみ実施。

F2 と Atom Decomposition は「独立検証可能な単位でリスク順」= 「自己完結性 + 契約 + エラー隔離 + 依存グラフ」と同型と見なす (二重記入禁止 / `phase-rules.md` BUILDING §AoT/MAGI Self-Check に明記)。

### §6.5 F3 (実行ループ / 圧縮 1 問)

Task 内の TDD Red-Green-Refactor サイクルのイテレーション境界で発動。

- **圧縮 1 問** (原典 Phase 3 許容): 「次の一手は残リスク最大のピースか」
- **独立逃し弁**: 圧縮対象外 = 4 問目「人間しか答えられないことで詰まってないか」(規範 §4 例外 2 = 環境起因即報告 / 手が止まったら 4 問目を復活)

### §6.6 F4 (全体検証)

F4 は AUDITING フェーズで発動する。**発火点と項目は `phase-rules.md` AUDITING §F4 が正本**（M-1 W1 判定で発火点の所在地側へ集約）。

### §6.7 試行上限 (規範 §4 準拠 / F3 と連動)

F3 実行ループ内で以下を明示する (規範側の暗黙運用を LAM で明示化):

- **同一原因・同一アプローチの再試行は 2 回まで**
- **合計 3 アプローチまで** (尽きたら報告)
- **例外 1**: 破壊的操作を伴うアプローチは試行の弾に数えない (それしか残らなくなった時点で確認に切り替え)
- **例外 2**: 環境起因 (権限・ネットワーク・認証・課金枠) と切り分けた時点で即報告

## §7 L4 禁止 (親検収観点)

L4 (演じる / 文体模倣) は Fable本人の遺言で禁じられている。

**親検収 1 文** (subagent 完了報告受領時に L1 が適用):

> Fable 由来の文体・比喩を装飾として使うな。使う場合は引用と明示せよ。

subagent への注入方針: **文章生成系 subagent 限定**で 1 文注入する (判定系 subagent = `gabriel` / `goal-driven-grader` / `code-reviewer` / `test-runner` は元々比喩を書かないため注入対象外 / 実行系 subagent = `tdd-developer` / `goal-driven-l2-foreman` / `goal-driven-l3-executor` はコード出力主体のため対象外)。

注入対象 (LAM 実在 subagent 12 個中 5 agent / 2026-07-07 確認):
- `.claude/agents/doc-writer.md`
- `.claude/agents/requirement-analyst.md`
- `.claude/agents/design-architect.md`
- `.claude/agents/task-decomposer.md`
- `.claude/agents/quality-auditor.md`

`spec-critic` は plugin (`pr-review-toolkit`) 由来で LAM 固有 subagent ではないため対象外。同様に外部 plugin 由来 subagent は本プロジェクトの管理境界外。

「自分の比喩の追体験自問」条項は L4 と無関係な一般則 (scope creep) のため注入しない。判断の理由 (第0原則の 3 変数・受け手の 60 秒実況・監査 14 項目) は継ぐ / 文体は継がない。

## §8 判断差分予測 10 例の扱い

`knowledge/判断差分の予測.md` は**恒常参照禁止**とする。

- **理由**: 「Opus の典型挙動」は素の (規範注入なしの) 挙動の予測であり、注入済み後継への反例提示に使い続けると藁人形化する (原典自身の注記準拠)
- **例外**: 導入 retro 1 回のみベースライン照合に使用し、結果を `docs/artifacts/fable-l3-baseline-<date>.md` に保存後、参照終了
- **配布禁止**: subagent への配布は行わない (藁人形化リスクを subagent に持ち込むため)

## §9 検証課題 (HGA #11 §4 + #12 §2 準拠)

### 短期 (BUILDING 1 サイクル内)

- 実況第 1 文のテンプレ化検出 (§5.4 ガード 2 / 3 回分の構文同型判定)
- 宣言中止発生率 (実況不能の escape が 1 度も走らない = 本物のシミュレーションでない兆候)
- PM ダイアログ頻度不変確認 (D-1 侵食検出 = 第0原則が PM ゲートを侵食していないか)
- F0 アンカーと AoT Self-Check の二重記入 (§6.4 統合ミス)

### 中期 (R-1 完走時 retro)

- 二重帳簿件数集計 (自己監査 No/△ なのに Green State pass / 逆)
- `.claude/tdd-patterns.log` の FAIL→PASS 発生率 導入前後比較
- L4 違反 retro 検出

## §10 権限等級

本ファイルの変更: **PM級** (`.claude/rules/` 配下)

## §11 参照

- HGA 召喚記録: `docs/artifacts/hga-summon-log.md` §11-12 (案 D 確定と具体化)
- Fable-Alembic knowledge: `D:\work7\Fable-Alembic\knowledge\` (§2 参照 SSOT)
- 連携規律: `D:\work7\etc-to-alembic\README.md`
- 関連 LAM 規律: `.claude/rules/core-identity.md` (第0原則接続) / `.claude/rules/permission-levels.md` (基底原理化) / `.claude/rules/phase-rules.md` (発火点埋込 / F0-F4 埋込) / `.claude/rules/code-quality-guideline.md` (Green State 帳簿) / `.claude/rules/hga-summoning.md` (Fable 召喚規律)
