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

以下いずれかに該当する場合に Fable を召喚する（内部確信度に依存しない、事前観測可能な軸）。

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
として扱う。再送コストは 1 回あたり概算 $0.15 程度（フル召喚 $1-4 とは別物）であり、
被害は指数でなく線形に留まる。

## 漏れ回収の 3 経路

以下 3 経路は混同しやすいため区別すること。

| 経路 | 内容 | 回収手段 |
|------|------|---------|
| 見える漏れ | 索引 push で存在が示された資料 | Fable が pull 要求可 |
| 鮮度（currency） | 知識の鮮度ギャップ | Fable からは要求不能・push のみ |
| 概念的 crux | ブリーフ・索引双方に現れない天井起因の不足 | 既約・2 段召喚で縮小するが完全解消はしない |

## 別予算 2 枠

以下は月 $40-80 の envelope の**外**とする。計上ラベルを分離し、コスト暴発源を切り分ける。

| 枠 | 内容 |
|----|------|
| 対話モード召喚 | 真の行き詰まり時のみ、人間を含めた協議を行う召喚 |
| branch モード | Fable に Sonnet を直接ぶら下げる tight な適応探索のみ（稀・バウンド付き） |

### envelope 定義（2026-07-04 二軸化 / 下調べパイプライン導入後）

Fable = credit 従量（実 $）、Opus subagent = subscription quota（weekly cap %）に切り分けて監視する。

| envelope 軸 | 対象 | 目安 |
|:-----------|:-----|:-----|
| **実 $ envelope** | Fable brief 分のみ（メーター実 $） | 月 **$10-40**（下調べパイプライン導入後・削減見込） |
| **Opus quota envelope** | Opus subagent の subscription 消費 | weekly cap **20% 以内**（大型探索 3-5 回/週相当） |

### 実測単価（2026-07-04 #5 実測後の更新）

- Fable 単独召喚（旧型）: **$1.84（tool_uses=0 短答）〜 $12.66（tool_uses 17 大型）** / 平均 ~$5-8/回
- 下調べパイプライン（Fable brief + Opus 下請け）: Fable brief 分 **~$0.20/回**（未実測 / パイロット #5 で確定予定）
- **envelope 監視は API 実メータリング（jsonl 集計）基準**（`docs/artifacts/hga-summon-log.md` §day-1 実測メモ #5 参照）
- branch モード ($13+/回) は別予算枠を維持

## 下調べパイプライン（research 委譲パターン / 2026-07-04 新設）

大型探索型の召喚（旧 #3 型 = tool_uses 10+ / 資料収集主体）は、Fable 単独ではなく
**Fable brief + Opus subagent 下請け** の 2 段構成で実施する。「下調べは Fable の弱点、
Opus の強み」を反映した委譲パターン。

### 根拠

- **Fable は doc pull / web 検索が苦手**（X community 定説 / 2026-07 実測でも本体は tool 使用が薄い）
- **Opus 4.7/4.8 は Fable の半額**（$5/$25 vs $10/$50 / 2026-07-04 公式取得）
- **Opus は Claude Code 上で subscription 吸収**（credit 従量ではなく weekly quota 消費）→ 実 $ には効かない
- **Anthropic 内部評価**: Opus lead + Sonnet subagent = 単独 Opus 比 **+90.2%**（multi-agent research system 論文）
- **retrieval 能力**: Opus 4.6 = 76% vs Sonnet 4.5 = 18.5%（8-needle 1M MRCR v2 / emergent.sh）

### 委譲先モデル選定

| 委譲先 | 用途 | 判断 |
|:------|:-----|:-----|
| **Opus 4.7 / Opus 4.8** | 検索・doc pull・retrieval 全般（**primary**） | 単価半分 + subscription 吸収 + retrieval 優位で最適 |
| Sonnet 5 | **使わない** | Anthropic 公式 Sonnet 5 プロンプトガイドが「literal interpretation / does not silently generalize / does not infer requests you didn't make」と明記。loose brief で under-deliver するため下調べ用途に不適 |
| Haiku 4.5 | 事実突合・rubric 採点のみ | 判断・多段推論には非採用（既存規律通り） |

### tight brief 4-slot テンプレート

Anthropic 公式 multi-agent research paper の failure mode（「research the semiconductor shortage」で
subagent が 2021 と 2025 を独立探索し labor division 失敗）を修正する形式。全 4 slot 必須。

1. **objective**（何を達成するか / 単一文で）
2. **output format**（返却形式 / JSON or 箇条書き or dimension 別）
3. **tool guidance**（使うべきツール・情報源の順序 / 具体パス OK）
4. **task boundaries**（触らない領域・停止条件）

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

### 技術制約: flat fan-out のみ

Fable subagent は **1 レベル深さのみ、nested 不可**（2026-06 コミュニティ実測 / digitalapplied.com）。
「Fable → Opus → Sonnet」の 3 段チェーンは実行されない。必ず flat fan-out（Fable → Opus 直接）で構成する。

### コスト構造

| 成分 | 支払い形態 | 目安/回 |
|:-----|:----------|-------:|
| Fable brief（in + out 少量） | credit 実 $ | **~$0.20** |
| Opus subagent（retrieval 主体） | subscription quota | weekly cap **3-5%** |
| **合計 実 $** | | **~$0.20** |

現状の Fable 単独大型探索 $12.66 に対し、下調べパイプライン化で **実 $ は 1/50 以下**（$0.20 圏）。
ただし subscription quota は消費するため、L1 常用 Opus と合算した weekly cap 監視は必須。

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
のみ**問う。毎召喚では問わない（$50/MTok 出力の膨張防止）。一度回答を得たら**決定として記録し、
条件変化（価格レジーム変化・サブスク復帰・Fable 能力の大幅変化）まで再論しない**
（ADR-0009 決定記録を参照）。

## day-1 実測チェックリスト

| # | 確かめること | 状況 |
|---|---|---|
| 1 | プロンプトキャッシュがクレジット従量 Fable に効くか | **解決済み**（公式確認 / read 0.1x） |
| 2 | 自己修復ループの往復回数を実際に抑えられるか | **実測済**（召喚 #1 / 2026-07-02 / 往復 0 回・索引 push 有効。`docs/artifacts/hga-summon-log.md` 参照） |
| 3 | Fable が Claude Code で web/tool を使えるか | **解決済み**（実セッションで確認） |
| 4 | routing/Opus フォールバックの発火頻度と可視性 | 公式仕様は transcript 可視通知。**監視で対応**（発火領域は攻撃的セキュリティ等で設計討議では稀） |
| 5 | ブリーフの実効入力トークン / input・output 分離 | **解決済**（2026-07-04 実測完了 / jsonl 直読み手段確定 = 新規召喚不要）。実測結果: HGA #1 で API 総 tok 1,154,345 / input:output = 161:1 / **cache_creation が cost 66.8% を支配**（fresh input 14.3% / cache_read 12.8% / output 6.1%）。従量移行後の最適化優先順位 = cache_creation 抑制（先載り縮小より 5 分 TTL 内連続召喚で cache_c=0 化のほうが寄与大）。詳細は `docs/artifacts/hga-summon-log.md` §day-1 実測メモ (#5)。**注意**: `tool_uses=0` の一発応答召喚では jsonl の output_tokens が過小記録される（実測時は text char 数 × 0.8-1.5 で補正） |

#2 は召喚 #1（2026-07-02）で実測済（往復 0 回・索引 push 有効）。#5 は 2026-07-04 に jsonl 直読み手段で
input/output 分離を実測完了（新規召喚ゼロ）。結果、cache_creation 支配の内訳が確定し、
従量移行後の最適化優先順位が明確化された。

## 移行期注記

2026-07-07 までは Pro/Max weekly limit の 50% 枠内であるため、L1=Fable による直セッション運用
（本規律の召喚ゲートを介さない常駐的利用）も許容する。2026-07-07 以降のクレジット従量移行後は
本規律（スポット召喚・ステートレス化）を既定とする。

## 権限等級

本ファイルの変更: **PM級**

## 参照

- [ADR-0009](../../docs/adr/0009-hga-fable-summoning.md)（HGA 型 Fable 召喚アプローチ / 本規律の根拠）
- `docs/artifacts/hga-approach-2026-07-01.md`（討議録・原本 / ローカル限定・gitignore 済）
- `docs/artifacts/hga-summon-log.md`（召喚記録）
- `CLAUDE.md` §作業体制（3.5 層委譲モデルとの整合）
