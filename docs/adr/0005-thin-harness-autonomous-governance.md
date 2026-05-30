# ADR-0005: ハーネス減量と自律統治モード（Autonomous Governance Mode）の導入

## メタ情報
| 項目 | 内容 |
|------|------|
| ステータス | **Accepted**（2026-05-29 ユーザー承認） |
| 日付 | 2026-05-29 |
| 意思決定者 | sougetuOte（最終承認）/ Living Architect（起草・合議） |
| 関連ADR | [ADR-0001](./0001-model-routing-strategy.md)（モデル出し分け）, [ADR-0004](./0004-bash-read-commands-allow-list.md)（Read-Only 許可と Write の PM ガード） |
| 関連仕様 | [autonomous-mode/requirements.md](../specs/autonomous-mode/requirements.md), [green-state-definition.md](../specs/green-state-definition.md) |

---

## コンテキスト

### 背景

LAM の起源は2点に集約される。

1. **長期記憶への欲求** — セッションをまたいで文脈を保持したい。これは現在 `quick-save` / `quick-load`（SESSION_STATE.md）として結実している。
2. **モデルが指示を守らない問題への対症療法** — 当時のモデルは、目的（仕様・設計）を剥がすと設計せずに実装へ着手し、気になった箇所を勝手に改変してコードを増やし、気ままに進行した。これを引き止めるために、承認ゲート・フェーズ規律（PLANNING/BUILDING/AUDITING）・権限等級（PG/SE/PM）・Zero-Regression Policy が段階的に育っていった。

**つまり LAM のハーネスの相当部分は「抽象的に統治が善だから」ではなく、「特定の故障モード（暴走）への反応」として存在する。**

### 2026年のプラットフォーム状況（裏取り済み）

Anthropic は自律方向へ大きく舵を切っている。

- **Opus 4.8 + dynamic workflows**（research preview）: 単一セッションで最大「同時16 / 累計1000」subagent を並列実行、iterative verification と resumable state を内蔵。十万行規模の migration を test suite を合格バーに kickoff→merge。Max/Team/Enterprise 限定・token 消費は桁違い。
- **/goal**（v2.1.139）: 検証可能な完了条件を宣言すると、独立した小型 validator モデルが毎ステップ「ゴール達成か？」を判定しつつ、ターンをまたいで数時間〜数日 自律実行。
- **Agent Teams**（Opus 4.6 同時・experimental）: 複数セッションが相互にメッセージし、互いの findings を challenge する。
- **Opus 4.8 自身の自己門番化**: コード欠陥の黙過が前世代比 約 1/4、不確かな計画に push back、clarifying question を投げる。Anthropic の表明は一貫して **"work with human judgment, not replace it"**（classifier による破壊的操作・prompt injection 遮断、worktree 隔離、Rubber Duck critic、承認権限の保持）。

**観察**: Anthropic は「自律性」と「検証・統治」を同時にスケールさせている。門番を消したのではなく、門番を人間の手動承認から checker モデル・classifier・敵対的エージェントへ移管している。LAM の既存概念（Green State / lam-orchestrate / MAGI / PG-SE-PM）は、これら新機能とほぼ一対一で対応する。

### 判断対象

LAM をこの潮流に対しどう位置づけ、ハーネスをどう扱うか。

### 制約条件

- **個人プロジェクト**（意思決定者＝単独）。実行プラン: **Claude Max 5x（$100/月）**。週 Opus 約45–60h（2026-07-13 まで暫定 +50% 込み）、5h枠あたり約 88k tokens、claude.ai / Claude Code / Desktop で共用プール。
- dynamic workflows は Max でも使えるが消費が桁違い（参考: 3エージェントで単発の約7倍）。$100 では scoped 実験までが現実的で、daily core 用途は Max 20x（$200）相当が前提との見解が一般的。
- Zero-Regression Policy と Hierarchy of Truth は憲法であり、減量しても核は保持する。

### 要求事項

- 自律性を取り込みつつ、不可逆な事故を防ぐ。
- 起源（長期記憶・暴走抑止）を裏切らない。
- $100 Max で実運用可能であること。

---

## 検討した選択肢

### Option A: 現状維持（control-first を貫き、自律は様子見）

**概要**: ハーネスを現状のまま維持し、`/goal` や dynamic workflows を取り込まない。

**メリット**:
- 既存の安定性・Zero-Regression が無傷。
- 実装コストゼロ。

**デメリット**:
- モデル自身が自己門番化した今、常時ON の重い強制ゲートは「払うコストに見合わない摩擦」に転化しつつある。
- 意思決定者が長年抱いてきた「AI が自律的に作り上げる」という目標を逃す。
- エコシステムの潮流から徐々に乖離する。

### Option B: 統治層化・in-place・category 別ハーネス減量 ＋ 自律統治モード新設（採用）

**概要**: LAM を「autonomy の統治・検証レイヤー」へ再定義する。ハーネスを一律ではなく**3つの category 別**に減量し、`/goal` ベースの自律統治モードを既存3モードの隣に in-place で追加する。

**メリット**:
- 起源を裏切らずに目標へ寄せられる（後述の category 分割が鍵）。
- 潮流に乗りつつ「autonomy with a constitution」という差別化ポジションを取れる。
- 資産（rules / specs / skills）を分断しない。

**デメリット**:
- 設計と移行の手間。減量の度合いを誤ると回帰リスク。

### Option C: 自律ファースト別プロジェクトを新設（fork / extract）

**概要**: LAM の思想を種に、autonomy 前提の別プロダクトを fork または抽出で新規作成。LAM 本体は control-first のまま温存。

**メリット**:
- 制御版を温存しつつ自由に実験できる。

**デメリット**:
- 個人開発で**二つの憲法を保守 → drift 地獄**。改善が双方向に取り込めず腐る。
- 統治機構を再実装することになり、本家と乖離。最大資産（積み上げた rules/specs）を捨てる。

---

## 3 Agents Analysis

### [Affirmative] MELCHIOR（推進者の視点）

- モデルが自己門番化した（欠陥黙過 1/4、push back、clarifying question）以上、暴走抑止のための重い A 強制ゲートは存在意義が後退している。減量は原理的に正しい。
- ハーネスを薄くすることは、意思決定者が憧れてきた「AI が勝手にやって勝手に作り上げる」という目標の方向を見せる。個人プロジェクトだからこそ取れる賭け。
- LAM の概念は新機能と 1:1 で対応する（Green State↔/goal checker、lam-orchestrate↔dynamic workflows、MAGI↔Agent Teams、PG/SE/PM↔auto-mode classifier）。先回りして作っていた統治層を、潮流に接続するだけで価値が立つ。

### [Critical] BALTHASAR（批判者の視点）

- **「4x less ≠ zero」**。欠陥黙過は減ったがゼロではない。A を薄くした隙間を埋める backstop がなければ回帰が漏れる。
- dynamic workflows は $100 Max では token 的に daily core に使えない。これを核に据える設計は破綻する。
- in-place で雑に混ぜると Zero-Regression という看板が濁る。憲法本体への汚染リスク。
- 自律ループは週 Opus 枠を食い切りうる。
- PM事項のキュー化（バッチ審議）は、人間の監督が遅延することを意味する。不可逆な PM ミスがキューで未審査のまま長く居座る危険。

### [Mediator] CASPAR（調停者の視点）

両視点を統合した方針:

1. **A は「強制ゲート」を薄くするが「道具」は捨てない**。フェーズ強制・TDD強制・per-step承認は常時ON のハードブロックから助言/シグナル起動トリガへ降格。一方 MAGI / full-review / 8 subagent / 敵対 verify は **last-line（事後・オンデマンドの break-glass）として保持**する。逆説的に、前段の儀式を薄くするほど、後段に強い検証を一発落とせること（back-stop）の価値が上がる。front-loaded ceremony → back-loaded verification。
2. **B（連続性インフラ）と C（blast-radius ガード）は維持**。原則: **信頼はモデル品質とともにスケールするが、blast radius はスケールしない。**
3. **checker は決定的 Green State（G1/G2/G5）に接地**。「モデルが達成と言ったか」を完了の唯一根拠にしない。安い自動ネット（test/lint/security 実行）は減量後も残す。
4. **核は /goal ベース**（単一持続エージェント、$100 で可）。dynamic workflows / Agent Teams は future-candidates へ送り、scoped 実験で実測後に採用判断。
5. **in-place だが新モードを隔離**。憲法本体は不変、自律モードは既存3モードの隣に独立追加。
6. **キューは bounded + merge前審議ゲート**。バッチ化が監督を骨抜きにしないよう、PM事項が残る限り merge/ship を禁止し、キュー上限到達で停止して人間に上げる。

---

## 決定

**採用: Option B**。LAM を「autonomy の統治・検証レイヤー」へ再定義し、category 別ハーネス減量と /goal ベースの自律統治モードを in-place で導入する。具体方針は上記 CASPAR の6点を採る。

### ハーネス3層モデル（減量の指針）

| 層 | 存在理由 | Opus 4.8 で減量するか | 扱い |
|---|---|---|---|
| **A. 信頼ゲート（強制）** | モデルがプロセスを守れなかったから | **する** | 強制ブロック→助言/シグナル起動トリガへ降格。ただし**道具（MAGI/full-review/敵対 verify）は last-line として保持** |
| **B. 連続性インフラ** | コンテキスト消失対策（暴走と無関係） | **しない** | 維持。長時間自律でより重要（quick-save/load, SESSION_STATE, retro, agent-memory） |
| **C. blast-radius ガード** | 賢さと無関係に不可逆だから | **しない** | 維持（security-commands deny, PM 境界） |

### 決定理由

- 起源②（暴走抑止）の対象が後退した以上、A の強制ゲートの減量は筋が通る。一方、起源①（記憶＝B）と不可逆性（C）は暴走問題と無関係であり、モデルが賢くなっても価値が減らない。category 分割により「後悔しない減量」が可能になる。
- 道具を last-line として残すことで、減量による回帰リスクを back-stop で吸収できる。これは Anthropic が dynamic workflows/Agent Teams で adversarial verify を積む方向と一致する。
- /goal ベースなら $100 Max で完結でき、コスト制約を満たす。

### 却下理由

- **Option A**: モデル自己門番化により重い強制ゲートが過剰摩擦化。目標を逃し潮流から乖離。
- **Option C**: 二憲法の drift 保守コスト・資産分断・統治再実装が、個人開発では割に合わない。

---

## 影響

### ポジティブな影響
- 「AI が自律的に作り上げる」目標の方向へ前進。
- 「autonomy with a constitution」という差別化ポジション。
- B/C 維持により、不可逆境界での Zero-Regression は無傷。

### ネガティブな影響
- A 減量による残存欠陥リスク（緩和策: 決定的 Green State checker + 事後 full-review break-glass）。
- $100 Max の週枠圧迫（緩和策: ループ本体は Sonnet/低 effort、難所のみ Opus/高 effort。dynamic workflows は core 依存にしない）。
- キューによる監督遅延（緩和策: bounded queue + merge前審議ゲート + 不可逆 C は即時ハードストップ）。

### 影響を受けるコンポーネント
- `.claude/skills/`: 自律統治モードのスキル新設（既存 design/build/audit の隣）。
- `.claude/rules/phase-rules.md`, `permission-levels.md`: 権限等級の「自律ループ内の行動エンベロープ」としての役割追記。
- `docs/specs/autonomous-mode/`: 本決定に対応する要件・設計・タスク。
- `docs/specs/green-state-definition.md`: checker 接地条件としての再利用（変更は最小）。

---

## 実装計画（要件承認後に design で詳細化）

### フェーズ1: 要件確定
- [ ] [autonomous-mode/requirements.md](../specs/autonomous-mode/requirements.md) の未解決質問（RQ-1〜6）を審議で解消
- [ ] 本 ADR を Accepted へ（人間承認）

### フェーズ2: 設計
- [ ] 自律ループの状態機械・権限エンベロープ・キュー・checker 接地点を design.md に
- [ ] 既存3モードとの統合方式（第4モード or BUILDING 変種）を確定

### フェーズ3: 実装（BUILDING・別途）
- [ ] /goal ベースの薄い縦串 MVP

---

## 検証方法 / 見直しトリガー

- **検証**: $100 Max で対象 spec を1本、自律統治モードで Green State まで到達させ、PM事項がキュー経由でのみ人間に上がる end-to-end が成立すること（requirements SC-1〜SC-6）。
- **見直しトリガー**:
  - モデルの honesty が退行した場合 → A の減量を巻き戻す。
  - 決定的 checker をすり抜ける回帰が観測された場合 → backstop を強化。
  - dynamic workflows が $100 Max で現実的になった場合 → 採用を再評価（future-candidates から昇格）。

---

## 審議結果（2026-05-29・ユーザー承認）

requirements.md §6 の RQ-1〜6 を審議し、以下で確定（status を Proposed → Accepted）。

| RQ | 決定 |
|----|------|
| RQ-1 | 決定的シグナルで自動起動する薄い tripwire を残す。将来は観測可能な昇格条件（例: 自律ラン N 回連続で checker 赤ゼロ）で段階的に委譲を進める |
| RQ-2 | 不可逆操作（C層）は即時ハードストップ。可逆 PM のみキュー化 |
| RQ-3 | last-line の自己起動をコストで段階化。**安価な MAGI は広く自己起動可、高価な full-review はエスカレーション予算内のみ・超過時は「human review 推奨」を PM キューへ降格**。人間はいつでも起動可。/goal の stuck 検知が thrash を抑止 |
| RQ-4 | 決定的 checker は block（Green State 未達なら継続） |
| RQ-5 | dynamic workflows は core 採用せず見送り。future-candidates に理由付き記録、実測後に再評価 |
| RQ-6 | 独立第4モード（内側で build と audit を駆動する層） |

注記: MAGI を「安価（in-context・fan-out なし）」と前提した。将来 MAGI を subagent 並列実装へ変える場合、RQ-3 の段階分けを見直す。

---

## Reflection（MAGI 1回限りの検証）

致命的な見落としの点検:

- **A 減量 × C 維持の「隙間」で SE級回帰がすり抜けないか？** → PG（無断）と PM（停止）の中間にある SE級は、決定的 Green State（test/lint/security）を backstop とし、事後 full-review を break-glass とすることで吸収する。隙間は塞がれている。
- **キューが溜め込み場にならないか？** → bounded + merge前ゲートで担保。
- **不可逆操作をキューに入れてよいか？** → No。可逆 PM のみキュー化、不可逆 C は即時ハードストップ（requirements RQ-2 で要合意）。

致命的な見落とし: なし。ただし本 ADR は **PM級**であり、**最終確定（Proposed → Accepted）には人間の審議・承認が必須**。

## Reflection 追補（2026-05-29 / DW ブラインド検証の知見）

別セッションで Dynamic Workflows を用い、LAM ツール群を**対話文脈ゼロでコールド分析**させた（実験一式は `docs/memos/dw-experiment/` にスクラッチ保管・本記録には非昇格）。その独立分析が、上記 Reflection が捉えていなかった **3つの catch** を返した。うち1つは autonomous-mode の**核の不変条件**へ格上げする。

1. **自己破壊的再帰（格上げ＝不変条件）**: 自律エンジンが*自身の統治*（rules / ADR / settings / モード自身の定義）を書き換える再帰的ハザード。PM級は定義済みだが、Auto Mode + worktree 隔離下では PreToolUse の強制点が書込時に発火せず **merge 時に着地**しうる。→ **「自律エンジンは自身の統治への書込権限を持たない」を不変条件化**（requirements **FR-9.1**）。これは本 ADR が前提した「**未来の門番の本質は distrust でなく authority**」の具体的顕現であり、Mythos 級 honesty でも消えない authority 境界である。
2. **隔離 ≠ 不可逆境界の遮断**: worktree は実行中を守るが merge / push / 隔離外 rm は不可逆のまま。C層の即時ハードストップは隔離と独立に張る（**FR-9.2**）。
3. **機械的合意収束 ≠ 決定的**: adversarial verify は相関盲点で偽収束しうる。完了判定は決定的 Green State 接地（FR-4.1）を唯一根拠とし、合意収束は非決定的観点（G3/G4）の補助に留める（**FR-9.3**）。RQ-4「checker は block」の根拠を補強。

> DW 採用時の実装ガードレール（9 must-preserve 制約）と採用ロードマップ（4フェーズ）は、RQ-5 の core 見送り方針に従い **design / future-candidates の検討材料**とする（本 ADR には昇格しない。DW を尻尾、core(/goal) を犬として分離）。

## 参考資料

- [Anthropic: Introducing Claude Opus 4.8](https://www.anthropic.com/news/claude-opus-4-8)
- [Claude Code Docs: Agent Teams](https://code.claude.com/docs/en/agent-teams)
- `docs/internal/06_DECISION_MAKING.md`（MAGI System）
- `.claude/rules/permission-levels.md`, `.claude/rules/code-quality-guideline.md`
- `.claude/rules/planning-quality-guideline.md` §7（新機能・外部依存の採用評価：二段構え）
