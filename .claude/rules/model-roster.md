# モデルロスター（モデル名束縛の単一 SSOT）

**制定日**: 2026-07-26
**根拠**: ADR-0011 決定 2 / `docs/specs/m-1-opus5-migration/design.md` §6.1 / requirements FR-10・FR-14
**位置づけ**: LAM 内で「どの層にどのモデルを割り当てるか」を書いてよい**唯一の場所**。

## §0 本ファイルが持つもの / 持たないもの

| | 内容 | 所在 |
|:--|:-----|:-----|
| **持つ** | モデル名の束縛（層 → モデル ID）/ 層内閾値 / 挙動デルタ / 単価・envelope | 本ファイル |
| 持たない | **層の定義**（L1 = 判断 / L1.5 = 司令塔 / L2 = 実行 / L3 = 採点） | `CLAUDE.md` §作業体制 |
| 持たない | **ルーティングの構造**（どの層で誰が判定するか / Opus をメインセッション専用にする） | `docs/adr/0001-model-routing-strategy.md` |

### ADR-0001 との関係（FR-14 / **supersede しない**）

本ファイルは **ADR-0001 を supersede しない。両者は直交する**。ADR-0001 が決めたのは**ルーティングの構造**であり、本ファイルが持つのは**モデル名の束縛**である。モデル世代が変わっても ADR-0001 の決定（Opus を hooks/subagents で使わない）は不変であり、変わるのは本ファイルの表の値だけである。

**モデルが変わったときに更新するのは本ファイル 1 枚**。他のファイル（`CLAUDE.md` / 各 rules / ADR）はモデル名を持たないため更新不要——これが SSOT 化の目的。

---

## §1 現行ロスター表

| 層 | 役割 | モデル | API ID | 有効日 | 根拠 |
|:---|:-----|:-------|:-------|:-------|:-----|
| **L1** | 統括（判断・査定・PM 整理・ユーザー対話） | **Opus 5** | `claude-opus-5` | 2026-07-25 | M-1 W0 で実行モデルを切替（`m-1-baseline-w0.md`） |
| **L1.5** | 司令塔（並列子分配・プロンプト書き分け・兄弟間衝突回避） | **Sonnet 5** | `claude-sonnet-5` | —（既存運用 / 起点未特定） | `.claude/agents/goal-driven-l2-foreman.md` の `model: sonnet` 実測。ADR-0001 により Opus は割当不可 |
| **L2** | 実行（実装・編集・調査） | **Sonnet 5** | `claude-sonnet-5` | 2026-07-07 | `model-delegation-prompting.md` 制定時に Sonnet 5 を対象として明文化 |
| **L3** | 採点（事実突合・rubric 判定・軽集計） | **Haiku 4.5** | `claude-haiku-4-5-20251001` | — （既存運用 / 起点未特定） | `.claude/agents/goal-driven-grader.md` 他 3 agents の `model: haiku` 実測 |
| **HGA** | スポット召喚（spec/design 初期・不可逆な設計コミット・真の行き詰まり） | **Fable 5** | `claude-fable-5` | 2026-07-02 | ADR-0009 / `.claude/rules/hga-summoning.md`（**常駐させない**） |

### hooks / subagents への Opus 非割当（FR-14 受け入れ条件 3 / ADR-0001 制約）

**上表の L2 / L3 に Opus は割り当てられていない**。ADR-0001「Opus は hooks/subagents で使用しない。メインセッション専用」の遵守状態は以下のとおり。

| 対象 | 実装 | Opus の有無 |
|:-----|:-----|:------------|
| hooks（第 1 層） | 全 5 件が `type: command` = 純粋 Python（LLM 不使用） | **なし**（LLM を呼ばない） |
| subagents | `.claude/agents/*.md` の `model:` frontmatter | **なし**（実測 sonnet 9 / haiku 3 / 未設定 0 / 2026-07-25） |

> **例外の唯一の経路**: `Agent` ツール呼び出し時の `model` パラメータで L1 が明示指定した場合のみ。frontmatter 既定を Opus に変更することは ADR-0001 に反するため **MUST NOT**。

---

## §2 層内閾値

現行ロスター（§1）における層の内側の運用閾値。**モデルが変われば見直す対象**であるため本ファイルに置く。

| # | 閾値 | 値 | 根拠 |
|:-:|:-----|:---|:-----|
| 1 | **委譲可否の第一基準** | F0 の「検証方法」が**実コマンド 1 行**で書けるか。書けなければ L1 直 | `docs/artifacts/knowledge/l2-delegation-guardrails.md` §8（2026-07-26 実測） |
| 2 | **L1 直作業の自己チェック** | Edit 5 回 + Write 1 回を超えるなら「Sonnet に委譲できないか」を自問する | `CLAUDE.md` §担当層の判断基準 |
| 3 | **司令塔（L1.5）の投入** | 並列子 **2 名超**かつ複数ファイル横断のとき投入。2 名以下は L1 → L2 → L3 | `CLAUDE.md` §委譲の閾値ルール |
| 4 | **並列度の既定** | 独立タスクは **3-4 並列**（L1 直の Edit/Read/Bash を含む） | `CLAUDE.md` §自律実行の既定 |

**閾値 1 と 2 の関係**: 2 は「量」の目安、1 は「性質」の判定。**量が閾値を超えても検証コマンドが書けないなら委譲しない**（1 が優先）。

---

## §3 挙動デルタ

現行ロスターのモデルが、前世代と比べて**委譲プロンプトの書き方を変える**点。

> **本節の状態**: Sonnet 5 分は **W2-M1-T2 で `model-delegation-prompting.md` §1 から移設済**（2026-07-26）。移設元には参照のみが残る。**デルタ番号（1〜7）は移設前後で不変**であり、`model-delegation-prompting.md` §2〜§5 の「デルタ N」参照はそのまま本節を指す。

### Opus 5（L1 / 2026-07-24 GA）

| # | デルタ | 影響 |
|:-:|:-------|:-----|
| 1 | **thinking は既定 ON**、effort は 5 段階（`low` / `medium` / `high` / `xhigh` / `max`）で **default は `high`** | 明示指定しない限り high 相当のコストとレイテンシで動く |
| 2 | `thinking: {"type": "disabled"}` は **effort `high` 以下でのみ受理**。`xhigh` / `max` と併用すると **400 エラー**（Opus 4.8 では独立していた） | API 直叩き経路での破壊的変更 |
| 3 | reliable knowledge cutoff = **May 2026** | 2026-05 以前の事実は問い合わせ不要 / 以後は要裏取り |

### Sonnet 5（L1.5 / L2 / 4.x 比 / 委譲影響順）

**出典**: 公式 "Prompting Claude Sonnet 5" + "What's new in Claude Sonnet 5"（platform.claude.com / 2026-07-07 取得）/ community 実運用報告（HN launch thread / CodeRabbit 実測 / claudefa.st 他 / 2026-06-30〜07-03）。

| # | デルタ | 出典 | 委譲への影響 |
|---|--------|------|------------|
| 1 | **リテラル解釈**: 指示をアイテム間で暗黙一般化しない / 依頼外を推論しない ("does not silently generalize / does not infer requests you didn't make") | 公式 | 適用範囲の明示が必須 (「最初の 1 件だけでなく全て」式) |
| 2 | **effort 遵守が厳格** (low/medium は「言われた分だけ」に絞る) / Sonnet 5 の medium ≈ 4.6 の high 相当 | 公式 | 多段推論・TDD 委譲は high 以上 |
| 3 | **実装詳細の over-delivery** (依頼外 helper・テスト・依存追加 / 「boilerplate だけ書け」無視の報告) | community (2+ 独立源) | 下方向フェンス (do NOT 境界) + 親側 diff 検証 |
| 4 | **否定形制約の drop-through** (「install するな」が無視された報告複数) | community | 重要制約は task prompt 内に再掲 (CLAUDE.md 頼み禁止) + 親検収 |
| 5 | adaptive thinking 既定 ON + 新トークナイザで **同一テキスト ~30% トークン増** | 公式 | 予算・max_tokens 見積の再校正 |
| 6 | **レビュー系で recall 低下**: 「高重要度のみ報告」指示をリテラルに実行し絞り込む (4.6 は低重要度も報告していた) | 公式 + community (CodeRabbit 実測: catch 率 63%→50%) | coverage 目的は loose 指示 (`model-delegation-prompting.md` §3) |
| 7 | sampling params (temperature / top_p / top_k) は **400 エラー** | 公式 | 委譲設定・API 呼び出しに含めない |

#### リテラル × over-delivery の両立解釈（委譲指針の核）

デルタ 1 と 3 は矛盾しない: **指示された作業スコープにはリテラル**（明示されない範囲へ広げない）だが、**スコープ内の実装詳細は過剰化しがち**（余計な helper・テスト・防御コード）。よって委譲プロンプトは:

- **上方向 (適用範囲) は明示的に広げる** — 全称・列挙でスコープを書く
- **下方向 (成果物の種類) は明示的にフェンスする** — 変更可ファイル白リスト + 依頼外成果物の禁止列挙

の両建てで書く。**この解釈を委譲プロンプトの書式に落とした実体が `model-delegation-prompting.md` §2 必須 7 項**である。

### Haiku 4.5（L3）

公式ドキュメントに Sonnet 5 型「リテラル解釈」の明記は**ない**（未確認）。挙動デルタは未特定のため、委譲時は Sonnet 5 と同じ明示スコープ・明示出力契約で扱う（`model-delegation-prompting.md` §4）。**未確認事項**: effort param の可否 / adaptive thinking 適用有無。

---

## §4 単価・envelope

**一次資料**: https://platform.claude.com/docs/en/about-claude/models/overview （取得日 **2026-07-25**）
**補足一次資料**: https://platform.claude.com/docs/en/about-claude/models/whats-new-opus-5 （同）
**裏取り記録**: `docs/artifacts/m-1-baseline-w0.md` §W0-M1-T5

| 項目 | Fable 5（HGA） | **Opus 5（L1）** | Sonnet 5（L1.5 / L2） | Haiku 4.5（L3） |
|:-----|:---------------|:------------------|:----------------------|:-----------------|
| API ID | `claude-fable-5` | `claude-opus-5` | `claude-sonnet-5` | `claude-haiku-4-5-20251001` |
| 価格（in / out per MTok） | **$10 / $50** | **$5 / $25** | **$3 / $15**（**下記 (i) の期限付き特例あり**） | $1 / $5 |
| context window | 1M | **1M**（default かつ最大 / 小 variant なし） | 1M | 200k |
| max output | 128k | 128k | 128k | 64k |
| adaptive thinking | Yes（always on） | Yes | Yes | No |
| extended thinking | No | No | No | Yes |
| reliable knowledge cutoff | Jan 2026 | **May 2026** | Jan 2026 | **Feb 2025** |
| GA | 2026-06-09 | **2026-07-24** | — | — |

### 必ず参照する 3 点（W0-M1-T5 が roster への明記を指定）

1. **(i) Sonnet 5 の導入価格は期限付き**: **2026-08-31 まで $2 / $10**、以後は通常価格 $3 / $15。**期限後にコスト見積が 1.5 倍になる**ため、L2 委譲量の試算は期限を跨いで流用しない。
2. **(ii) Haiku 4.5 の knowledge cutoff は Feb 2025 と古い**: L3（採点・事実突合）に**最新事項の知識判断をさせない**根拠。突合対象の事実は必ずプロンプトまたは一次資料で与える。
3. **(iii) Opus 5 の thinking / effort 制約**: §3 デルタ 2 のとおり `xhigh` / `max` と thinking 無効化は併用不可（400）。

### その他の確定事項

- **Opus 5 は Opus 4.8 から価格据え置き**（$5 / $25）。`hga-summoning.md` §根拠の「Opus は Fable の半額」は **Opus 5 世代でも成立を継続**する（$5/$25 vs $10/$50）。
- **Opus 5 Fast mode**: $10 / $50（research preview / Claude API のみ / Bedrock・Google Cloud・Microsoft Foundry では未提供）。
- **Opus 5 の prompt cache 最小長は 512 tokens**（Opus 4.8 は 1,024）。
- **1M context は追加課金なし**（long-context 割増ではなく standard pricing）。
- **Fable 5 のトークナイザ**: Opus 4.7 導入のトークナイザを使用し、同一テキストで**約 30% 多いトークン**になる（4.7 より前のモデル比）。HGA ブリーフの実効トークン見積に影響する。

### envelope 定義（2026-07-04 二軸化 / 下調べパイプライン導入後 / W2-M1-T2 で `hga-summoning.md` から移設）

Fable = credit 従量（実 $）、Opus subagent = subscription quota（weekly cap %）に切り分けて監視する。

| envelope 軸 | 対象 | 目安 |
|:-----------|:-----|:-----|
| **実 $ envelope** | Fable brief 分のみ（メーター実 $） | 月 **$10-40**（下調べパイプライン導入後・削減見込） |
| **Opus quota envelope** | Opus subagent の subscription 消費 | weekly cap **20% 以内**（大型探索 3-5 回/週相当） |

**別予算 2 枠（対話モード召喚 / branch モード）は上記 2 軸の両方の外**として計上ラベルを分離する。枠の内容と運用は `hga-summoning.md` §別予算 2 枠。

### 実測単価（2026-07-04 #5 実測後の更新 / 同上移設）

- Fable 単独召喚（旧型）: **$1.84（tool_uses=0 短答）〜 $12.66（tool_uses 17 大型）** / 平均 ~$5-8/回
- 下調べパイプライン（Fable brief + Opus 下請け）: Fable brief 分 **~$0.20/回**（未実測 / パイロット #5 で確定予定）
- **envelope 監視は API 実メータリング（jsonl 集計）基準**（`docs/artifacts/hga-summon-log.md` §day-1 実測メモ #5 参照）
- branch モード（**$13+/回**）は別予算枠を維持

### 下調べパイプラインのコスト構造（同上移設）

| 成分 | 支払い形態 | 目安/回 |
|:-----|:----------|-------:|
| Fable brief（in + out 少量） | credit 実 $ | **~$0.20** |
| Opus subagent（retrieval 主体） | subscription quota | weekly cap **3-5%** |
| **合計 実 $** | | **~$0.20** |

Fable 単独大型探索 $12.66 に対し、下調べパイプライン化で **実 $ は 1/50 以下**（$0.20 圏）。ただし subscription quota は消費するため、**L1 常用 Opus と合算した weekly cap 監視は必須**。パターンの適用ゲートと構成は `hga-summoning.md` §下調べパイプライン。

---

## §5 更新手順

| # | 手順 | 実体 |
|:-:|:-----|:-----|
| 1 | 本ファイルの表を更新する（**ここだけ**） | `.claude/rules/model-roster.md` |
| 2 | モデル名の drift を検査する | `.claude/scripts/verify_model_reference.py`（**W2-M1-T4 で新設**） |
| 3 | 手順全体を skill 化して回す | `/update-model`（**W4-M1-T2 で新設**） |

> W2-M1-T4 完了までは手順 2 が存在しないため、更新時は本ファイルと `CLAUDE.md` の導線のみを目視で確認する。

---

## §6 権限等級

本ファイルの変更: **PM 級**（`.claude/rules/` 配下 / `permission-levels.md`）。

ただし **§1 の表の値の更新は「モデル世代交代」という予定された事象**であり、`/update-model`（W4-M1-T2）の手順に従う限り 1 承認イベントで完結させる（K5 パターン）。

---

## §7 参照

- `docs/adr/0001-model-routing-strategy.md`（ルーティングの構造 / **本ファイルと直交**）
- `docs/adr/0009-hga-fable-summoning.md`（HGA 型召喚 / Fable の位置づけ）
- `docs/adr/0011-clause-triage-and-model-generation-governance.md`（決定 2 = 本ファイルの根拠）
- `CLAUDE.md` §作業体制（**層の定義** / モデル名は持たない）
- `.claude/rules/model-delegation-prompting.md`（委譲プロンプトの書き方 / 挙動デルタは **§3 へ移設済** 2026-07-26）
- `.claude/rules/hga-summoning.md`（HGA 召喚規律 / 単価・envelope は **§4 へ移設済** 2026-07-26）
- `docs/artifacts/m-1-baseline-w0.md` §W0-M1-T5（**単価・スペックの裏取り記録** / 一次資料 URL と取得日）
- `docs/artifacts/knowledge/l2-delegation-guardrails.md` §8（§2 閾値 1 の実測根拠）
