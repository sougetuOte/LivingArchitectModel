# HGA 型 Fable 召喚規律

[ADR-0009](../../docs/adr/0009-hga-fable-summoning.md) の運用規律。Fable 5 は常駐させず、
低頻度・高 stakes の局面にのみ「儀式的に召喚する上位オラクル」として起用する
（HolyGuardianAngel = HGA 型）。日常の判断・実装・査定は既存の 3.5 層委譲モデル
（`CLAUDE.md` §作業体制）が引き続き担う。

## 体制

| 層 | 担当 | 役割 |
|----|------|------|
| L1 | Opus | 媒体・正本保持。ブリーフの選別・圧縮、Fable への召喚、召喚結果の統合 |
| HGA | Fable | スポット召喚のみ（使い捨て・leaf）。設計上の分岐点と根拠を返す |
| L2 | Sonnet | 資料取得・肉付け（Fable が要求した追加資料の取得、確定した設計軸の実装） |
| L3 | Haiku | 事実突合・軽集計 |

人間との協議は **Opus 側のみ**で行う。Fable を人間の判断待ちで開けたまま保持しない
（下記「ステートレス規律」参照）。

## 召喚ゲート

### 発効中のゲート（ADR-0011 決定 4）

いずれかに該当する場合に召喚する。**1・2 はいずれも「現行 L1 モデルで試行した結果」を要する事後条件**である。

| # | 条件 | 種別 |
|:-:|------|------|
| **1** | MAGI（AoT + gabriel）を実施し、gabriel が `verdict=refuted & severity=critical` を **2 回**出した（= `AC-W-C-7` 再 MAGI 上限到達 / 人間エスカレーション経路への到達） | 事後条件 |
| **2** | 第 0 原則 3 変数で「**不可逆 かつ 復旧コスト極大**」と判定され、**かつ L1 の結論に L1 自身が確信を持てない** | 事後条件 |
| **3** | ユーザーが明示的に召喚を指示 | 明示 |

**新規の判定機構は作らない**。条件 1 は既存の MAGI 人間エスカレーション経路（`docs/internal/06_DECISION_MAKING.md` §6.6 / `AC-W-C-7`）への**接続**であり、従来「人間に投げる」で終端していた経路に「**または HGA 召喚**」を追加する形を取る。

### 旧ゲートの 3 軸（条件 2 の判定材料 / 無条件召喚の資格は失効済）

以下は **M-1 完了（2026-07-26）まで**「無条件召喚」の効力を持っていた軸である（内部確信度に依存しない、事前観測可能な軸）。**現在は上表 条件 2 を判定するための材料**であり、それ単独では召喚の根拠にならない —— spec/design 初期・不可逆な設計コミット・新規／複数ドメイン統合の 3 軸は「無条件召喚」の資格を失った。

> **失効の記録（2026-08-21）**: 発効条件（M-1 完了）は 2026-07-26 に満たされていたが、移行期規定の条文が約 4 週間残置され、**新旧どちらのゲートが有効かが曖昧な状態**が続いていた。移行期規定を除去し、上表を発効中のゲートとして確定した（誕生ゲート取引 #14 / 純退出）。

| 軸 | 判定 |
|----|------|
| spec/design 初期 | **無条件召喚**（stakes・novelty がともに最大のため判断すら不要） |
| 不可逆な設計コミット | **無条件召喚** |
| 新規／複数ドメイン統合 | **既定で召喚** |
| MAGI 敵対テスト（「合意しろ」でなく「壊せ／最悪ケースを出せ」）で自力で塞げない破綻 | 召喚 |
| 過去に rework／ドリフトを出した問題種別に該当 | 召喚 |

MAGI の split は非対称シグナルとして扱う。MELCHIOR / BALTHASAR / CASPAR は同一モデル（Opus）の
別ペルソナであり盲点が相関するため、**割れた場合は真の crux として召喚する**（正の信号は有効）。
**割れない場合でも安全の証明にはならない**（負の信号は無効）。上表の召喚ゲートで判定すること。

## 召喚手順

1. **（無条件召喚ゾーンのみ）2 段召喚の crux-scoping**: フルブリーフの前に 2-3k の問題スケッチ
   のみを Fable に渡し、「crux の所在と必要資料」を先に問う。返ってきた指示に基づいて Opus が
   本ブリーフを編む
2. **ブリーフ構成（15-20k）**: crux + 索引 push + currency push（下表）+ hedge 指示を含める。
   索引 push は「Opus が要約対象から外した原資料の目次・ファイル名一覧」を数百トークンで同梱する
   ことを**必須部品**とする（ブリーフに載らない資料の存在を Fable が pull できるようにするため）
3. **召喚**: 出力を「設計上の分岐点と根拠のみ」に縛る指示を必ず添える。実装詳細を書かせない。
   「Opus-tier で実装可能な方向に制約せよ」を明示する
4. **資料要求往復**: 原則 1 回以内に抑える。初回ブリーフに「Fable が要求しそうな資料」を
   予め同梱しておくことで往復自体を減らす
5. **正本化**: 召喚結果（分岐点と根拠）を Opus が正本として保持する。以降の肉付け・実装は
   Sonnet に指示する

**大型探索型の分岐**: 予想 tool_uses 10+ の資料収集主体召喚は、上記手順ではなく
下記「下調べパイプライン（research 委譲パターン）」に従い、Fable brief + Opus subagent 下請け構成にする。
判断・crux 追及型（旧 #1・#4 型）は本手順を維持。

## currency push

Fable は自分の知識が古いと気づけないため、鮮度ギャップは pull では回収できない。召喚前に
Opus が currency sweep を行い、以下をブリーフに畳み込む（**push 必須**）。

| push する currency | 中身 |
|---|---|
| バージョン pin | 使う言語/ランタイム/主要 lib の現行版を日付付きで断定 |
| 変化点 delta（最重要） | 直近の非推奨化・API 改変・改名・新推奨パターンだけ（全部でなく差分） |
| 新規参入 | cutoff 後に生えた/成熟した選択肢 |
| 環境現況 | 実スタックの現在値 |

### hedge 指示（ブリーフに必ず含める 2 項）

- バージョン/API の事実はブリーフ記載を正とし、記載外の事実に依存する箇所は
  **要検証の仮定**として明示させる
- 応答が safety routing で Opus に降格された兆候があれば明示させる
  （routing は transcript で可視のため、Fable の自己申告と併せて監視する）

## ステートレス規律

人間との協議は Opus 側のみで完結させる。Fable への再召喚は**確定争点のみ**をステートレスに
渡す。人間の判断待ちで Fable セッションを開けたまま保持することを **MUST NOT**。
1 召喚内の資料要求往復は原則 1 回以内で可とする。

再召喚はブリーフの再 push のみで済むため、TTL 漏れは「守る対象」ではなく「無視してよい対象」
として扱う。再送コストはフル召喚より 1 桁以上小さく（実測値は `docs/artifacts/hga-summon-log.md` §day-1 実測メモ参照）、
被害は指数でなく線形に留まる。

## 漏れ回収の 3 経路

以下 3 経路は混同しやすいため区別すること。

| 経路 | 内容 | 回収手段 |
|------|------|---------|
| 見える漏れ | 索引 push で存在が示された資料 | Fable が pull 要求可 |
| 鮮度（currency） | 知識の鮮度ギャップ | Fable からは要求不能・push のみ |
| 概念的 crux | ブリーフ・索引双方に現れない天井起因の不足 | 既約・2 段召喚で縮小するが完全解消はしない |

## 別予算 2 枠

以下 2 枠は **envelope 軸（weekly quota / `model-roster.md` §4）の外**とする。計上ラベルを分離し、コスト暴発源を切り分ける。

| 枠 | 内容 |
|----|------|
| 対話モード召喚 | 真の行き詰まり時のみ、人間を含めた協議を行う召喚 |
| branch モード | Fable に Sonnet を直接ぶら下げる tight な適応探索のみ（稀・バウンド付き） |

### envelope 定義 / 実測単価 → `model-roster.md` §4（SSOT 退避済 / 2026-07-26 W2-M1-T2）

**envelope の定義（2026-08-17 に weekly quota 一軸へ集約 / 旧・実 $ 月次枠は Fable のサブスク化により破棄）と実測単価は `.claude/rules/model-roster.md` §4 が正本**。Fable / Opus subagent の単価、branch モードの単価も同節を参照する。本節が持つのは「**どの枠を envelope の外に置くか**」という運用規律のみ。

## 下調べパイプライン（research 委譲パターン / 2026-07-04 新設）

大型探索型の召喚（旧 #3 型 = tool_uses 10+ / 資料収集主体）は、Fable 単独ではなく
**Fable brief + Opus subagent 下請け** の 2 段構成で実施する。「下調べは Fable の弱点、
Opus の強み」を反映した委譲パターン。

### 根拠

- **Fable は doc pull / web 検索が苦手**（X community 定説 / 2026-07 実測でも本体は tool 使用が薄い）
- **Opus は Fable の半額**（単価は `model-roster.md` §4 / Opus 5 世代でも成立を継続）
- **Opus は Claude Code 上で subscription 吸収**（credit 従量ではなく weekly quota 消費）。**2026-07-20 以降は Max / premium seat では Fable も同じ weekly quota から引かれる**ため、本パターンの利得は「実 $ 削減」から「**quota 節約**」へ移った（Fable は同じ枠をより速く食うため利得自体は存続 / `model-roster.md` §4）
- **Anthropic 内部評価**: Opus lead + Sonnet subagent = 単独 Opus 比 **+90.2%**（multi-agent research system 論文）
- **retrieval 能力**: Opus 4.6 = 76% vs Sonnet 4.5 = 18.5%（8-needle 1M MRCR v2 / emergent.sh）

### 委譲先モデル選定

| 委譲先 | 用途 | 判断 |
|:------|:-----|:-----|
| **Opus 4.7 / Opus 4.8** | 検索・doc pull・retrieval 全般（**primary**） | 単価半分 + subscription 吸収 + retrieval 優位で最適 |
| Sonnet 5 | **使わない** | Anthropic 公式 Sonnet 5 プロンプトガイドが「literal interpretation / does not silently generalize / does not infer requests you didn't make」と明記。loose brief で under-deliver するため下調べ用途に不適 |
| Haiku 4.5 | 事実突合・rubric 採点のみ | 判断・多段推論には非採用（既存規律通り） |

### tight brief 5-slot テンプレート (2026-07-06 拡張 / R-1 W-R1 S1+S2 retro 由来)

Anthropic 公式 multi-agent research paper の failure mode（「research the semiconductor shortage」で
subagent が 2021 と 2025 を独立探索し labor division 失敗）を修正する形式。全 5 slot 必須。

1. **objective**（何を達成するか / 単一文で）
2. **output format**（返却形式 / JSON or 箇条書き or dimension 別）
3. **tool guidance**（使うべきツール・情報源の順序 / 具体パス OK）
4. **task boundaries**（触らない領域・停止条件）
5. **primary_sources**（絶対視すべき一次資料の URL または context7 library ID / 2026-07-06 追加）

#### primary_sources 追加の根拠 (2026-07-06 / R-1 W-R1 S2 retro 事例 #4)

subagent (L2) は「与えられた一次資料を絶対視する癖」と「context7 等の rich source を能動的に
引かない癖」を持つ。R-1 W-R1 S2 T4 (module 3 skills 監査) で subagent がローカルの `skill-creator/SKILL.md`
(R-1 W-R4 S3 で削除済 / `docs/artifacts/r-1-deletions.md` 参照)
を Claude Code SKILL.md の公式スキーマ一次情報源と誤認し、`allowed-tools:` を「非公式フィールド」と
誤判定した実測がある (R1-016 / tracker 参照)。L1 側で context7 の `/websites/code_claude`
を fetch → 公式仕様と判明 → subagent 判定を訂正した。

primary_sources を明示的に指定することで:
- subagent が最初から正しい一次資料を絶対視する (誤ったローカル文書を一次と誤認しない)
- context7 library ID を書いておけば subagent が能動的に fetch する動線が生まれる
- L1 監督工程での upstream 裏取り往復回数を削減 (2026-07-06 実測: R1-016 の訂正で 1 往復)

#### primary_sources の書式例

```
5. **primary_sources** (絶対視すべき一次資料 / 該当する場合):
   - context7 library: `/websites/code_claude` (topic: skill frontmatter / hooks 等)
   - upstream URL: https://code.claude.com/docs/en/skills
   - ローカル SSOT: `docs/specs/large-scale-review/design.md` §5.3 (これのみ / 他 SKILL.md 等の派生資料は参考扱い)
   - 既存ログ・既存出力を読むコマンドを書かせる場合はその**スキーマ文書**: 例 `docs/artifacts/gabriel-metrics-environment-2026-07-05.md` (JSONL 12 フィールド定義)
```

「該当する場合」は、外部ライブラリ / SaaS API / プラットフォーム機能に触れる brief でのみ必須。
純粋にプロジェクト内部の実装検証 brief では省略可 (「該当なし」を 5. に明記して skip)。

### grounding bolt-on（全 subagent 共通）

以下のブロックを全 subagent プロンプトに boilerplate として同梱する（LAM 既存の hedge 指示と統合可）。

```
Ground your claims: before reporting any finding as fact, audit it against a tool result
from this session. If you cannot point to the file, line, or command output that proves it,
mark it "unverified".
```

### loose brief の唯一例外

**adversarial coverage-first review**（MAGI 敵対テスト / spec-critic 型）のみ、Anthropic 公式が
明示的に loose 推奨。それ以外の召喚（下調べ・要件確認・crux 追及）は全て tight brief。

```
Report every issue you find, including ones you are uncertain about or consider low-severity.
Do not filter for importance or confidence at this stage - a separate verification step will
do that. Your goal here is coverage.
```

### Sonnet L2 委譲時の追加防御 (2026-07-04 実測に基づく追加)

**背景**: 2026-07-04 の Wave C Spike で Sonnet L2 subagent (`model="sonnet"`) が
meta-response 早期終了する failure mode を実測。「the agent is running in the background /
I'll wait for it to complete」型の応答で早期終了し、実作業は孫 subagent (spawnDepth 2) に
丸投げされる。**Sonnet 5 の literal interpretation 特性 + v2.1.198 以降の
「subagent が既定 background 実行」の組み合わせが原因と推定**。

**対策 (C + A の組み合わせ)**:

**C (構造的)**: Sonnet 委譲時は frontmatter で nested spawn を封じる:

```yaml
# .claude/agents/<sonnet-executor>.md 内
disallowedTools: [Agent]  # 孫 subagent spawn を封じ、Sonnet に「自分でやる」以外の選択肢を残さない
```

または委譲プロンプト側で明示的に指示:

```
You are the executor. You do NOT have permission to delegate this task to another subagent.
Complete all work in your own context and return the deliverable directly.
```

**A (保険的)**: Sonnet 委譲プロンプトの冒頭に boilerplate 追加:

```
You are the DIRECT EXECUTOR for this task. Do not describe your intent to work "in the
background" — you ARE the background worker. Do not delegate further. Write results
directly to the requested file/format before ending your turn.
```

**適用範囲**: HGA 下調べパイプラインの Sonnet 委譲だけでなく、通常の 3.5 層委譲モデル
(L1 Opus / L2 Sonnet / L3 Haiku) の L2 委譲にも適用推奨。

### 技術制約: subagent depth 制限 = 5 (2026-07-04 訂正)

**訂正**: 本節の旧記述「Fable subagent は 1 レベル深さのみ・nested 不可」は誤情報だった。
根拠として引用した digitalapplied.com（2026-06）の該当記述は、少なくとも 2026-07 時点の
Claude Code v2.1.197 では成立しない。公式仕様および実測結果は以下:

**公式仕様** (https://code.claude.com/docs/en/sub-agents 「Nested subagents」節):
> Depth is counted as the number of subagent levels below the main conversation, regardless
> of whether each level runs in the foreground or background. **A subagent at depth five
> doesn't receive the Agent tool and can't spawn further.** The limit is fixed and not
> configurable.

**実測** (2026-07-04 Wave C Spike): Sonnet L2 subagent (depth 1) が孫 subagent (depth 2) を
正常に spawn し、孫が実作業を完遂した事例を確認 (`.claude/.session-spike-w-c-1.md` 参照)。

**現行運用ガイド**: 技術的には depth 5 まで spawn 可だが、**実運用では depth 1 (flat fan-out)
を推奨**する。理由:

- 深さが増えるほど各段の failure mode (meta-response 早期終了 / literal 過剰解釈等) が
  積み重なり、最終成果物への到達確度が低下する
- コスト・レイテンシが線形以上に増える (実測: 孫 subagent は 32-158 秒とばらつきが大)
- 統合コストが増える (L1 が全 depth の中間結果を統合する必要)
- Fable HGA 召喚の下調べパイプラインでは **Fable brief → Opus subagent (depth 1) 直接**
  で構成し、Opus 内での nested spawn は不要 (Opus が Read/WebFetch 等を直接使う)

**例外的に depth 2+ を許容するケース**:
- コスト最適化のため大型探索を Sonnet に arbitration させ、実 retrieval を孫 (Opus 等) が担う場合
- ただしこの構成は本規律の「Sonnet 委譲時の追加防御」§ で述べた failure mode の影響を受けやすい
- 深さ 2 以上を採用する際は必ず Sonnet 側に `disallowedTools: [Agent]` を設定するか、
  L1 が孫の完走を明示的にモニタリングする体制を組む

### コスト構造

**`.claude/rules/model-roster.md` §4「下調べパイプラインのコスト構造」が正本**（2026-07-26 / W2-M1-T2 で SSOT 退避）。成分別の目安（Fable brief 分 = credit 実 $ / Opus subagent = subscription quota）と単独召喚との比較は roster 側を参照する。

### 適用ゲート

以下いずれかに該当する召喚に本パターンを適用する。

- 予想 tool_uses 10 回以上（資料収集主体）
- 複数ドメインの資料統合（LAM 内 + 外部 doc + web 情報 等）
- crux 探索より前段の下調べフェーズ

適用しないケース（Fable 単独維持）:
- 索引 push で自己完結できる crux 判断のみ（旧 #4 型）
- 敵対テスト / coverage 探索（loose brief 例外に該当）
- 数百トークンの短答（下請け起動コストが overhead）

## 召喚記録

**全召喚を `docs/artifacts/hga-summon-log.md` に追記すること（MUST）**。争点 E の再論禁止規律と
envelope 監視の実行基盤となる。

## 争点 E（枠棄却）再論禁止規律

「HGA 型そのものを棄却すべきか」という枠外検討（争点 E）は、**プロジェクト立ち上げ／大転換時
のみ**問う。毎召喚では問わない（Fable の出力単価は高い / `model-roster.md` §4）。一度回答を得たら**決定として記録し、
条件変化（価格レジーム変化・サブスク復帰・Fable 能力の大幅変化）まで再論しない**
（ADR-0009 決定記録を参照）。

## day-1 実測チェックリスト

**5 項目すべて解決済み**（2026-07-02〜07-04）。実測値と結論は
`docs/artifacts/hga-summon-log.md` §day-1 実測メモ が正本。要点のみ:
**cache_creation が cost の 66.8% を支配**するため、最適化は先載り縮小より
**5 分 TTL 内の連続召喚**（cache_creation=0 化）が効く。

## 移行期注記

2026-07-07 のクレジット従量移行を完了。**本規律（スポット召喚・ステートレス化）が既定**。

## 権限等級

本ファイルの変更: **PM級**

## 参照

- `.claude/rules/model-roster.md` §4（**単価・envelope の正本** / 2026-07-26 移設）/ §1（HGA の割当）
- [ADR-0009](../../docs/adr/0009-hga-fable-summoning.md)（HGA 型 Fable 召喚アプローチ / 本規律の根拠）
- `docs/artifacts/hga-approach-2026-07-01.md`（討議録・原本 / ローカル限定・gitignore 済）
- `docs/artifacts/hga-summon-log.md`（召喚記録）
- `CLAUDE.md` §作業体制（3.5 層委譲モデルとの整合）
