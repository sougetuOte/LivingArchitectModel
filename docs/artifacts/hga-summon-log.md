# HGA 召喚ログ

Fable 5 への全召喚を追記する記録簿。目的は 2 点:
1. 争点 E（枠棄却）再論禁止の決定記録の裏付け（`.claude/rules/hga-summoning.md` 参照）
2. envelope（月 $40-80）の監視。対話モード召喚・branch モードは別予算枠のためラベルを分離する

召喚を行った場合は必ず本ログに 1 行追記すること（`.claude/rules/hga-summoning.md` §召喚記録）。

| # | 日付 | トリガ軸 | モード (通常/対話/branch) | ブリーフ実効入力 | 往復数 | 概算コスト | 成果参照 |
|---|------|---------|---------------------------|-------------------|--------|-----------|---------|
| 0 | 2026-07-02 | inception (枠是非=争点E) | 対話 (移行期・50%枠内) | n/a (Fable直セッション) | - | 枠内 | ADR-0009 |
| 1 | 2026-07-02 | spec/design 判断 (親 tasks 改訂の構造選定 / ユーザー明示指示) | 通常 (スポット召喚) | 本体 ~2.5k / **API 総 tok 1,154,345 (#5 実測 2026-07-04 更新)** | **0** (追加資料要求なし・索引 push 有効) | **$5.85 (#5 補正・下記)** | 本セッション 親 tasks 改訂判断 (案 A + 所在一意性 invariant) / day-1 #2・#5 実測 |

## day-1 実測メモ (召喚 #1 / 2026-07-02)

- **#2 往復抑制 = 実証**: 索引 push (未収録原資料の目次同梱) により Fable が自力で parser・親・子 4 文書を Read し、L1 への資料要求往復 0 回で完結。
- **#5 実効入力 = 部分実測**: 送信ブリーフ ~2.5k に対し召喚総消費 ~84.8k tok。**先載りコンテキスト (system prompt + CLAUDE.md + rules 群) が支配的**であることを示唆。厳密な input/output 分離は subagent 完了 usage / transcript からは取得できず (transcript がフラッシュ済で空)、別手段 (専用軽量召喚での /cost 相当取得等) が必要。
- **含意**: 従量移行後のコスト最適化は「ブリーフ縮小」より「先載り縮小」の寄与が大きい可能性。envelope 監視は総消費 tok ベースで実施可能。

| 2 | 2026-07-02 | spec/design 完全設計 (親改訂 Wave1-6 全可視化 / ユーザー指示 + branch 許可) | **branch (別予算枠)** | 確定争点 push (ステートレス) | Fable ターン中断 1 (孫 3 体の完了を L1 が観測して再統合要) | **API 総 tok 2,910,797 = $13.81 (#5 補正)** ※以前記載の ~646k は L1 側 StatusLine 観測値・API 実メータリングと乖離 | 親 tasks 改訂の実装設計データ (parser 挙動監査 + Zero-Regression 検証) |

## day-1 実測メモ (召喚 #2 / branch モード / 2026-07-02)

- **branch モード成立確認**: Fable が Agent ツールで Sonnet subagent 3 体を起動できた (技術的可否 = 可)。
- **コスト暴発を実証**: 通常召喚 #1 ~85k に対し branch #2 は ~646k tok (約 7.6 倍)。規律「branch モードは稀・バウンド付き」の裏付け。孫の 1 体 (sweep) が監視/待機に終始し実質重複 = branch は制御が緩いと孫が暴走する。
- **オーケストレーション特性**: Fable はターンを中断して中間報告を返し、孫完了は L1 に通知された (Fable に自動再開なし)。branch の統合には L1 の再介入が必要 = 通常召喚より往復構造が重い。
- **運用結論**: branch モードは今回の実測で「高コスト・制御難」が確認できたため、既定は通常召喚 (索引 push で自力調査) とし、branch は真に必要な適応探索に限りバウンド (孫数・深さ) を明示して使う。本件の設計統合は L1 が引き取る (これ以上の再帰を避ける)。

| 3 | 2026-07-03 | spec/design 実装計画レビュー (ユーザー明示指示 / HGA 運用テスト) | 通常 (スポット召喚 / 索引 push + 実装コード禁止縛り) | ブリーフ実効 ~7k / **API 総 tok 4,100,192 (#5 実測 tool_uses 17)** | **0** (資料要求なし・自力 pull 8 回) | **$12.66 (#5 補正)** ※旧 ~$7 上限想定は誤り (cache_c $7.15 単独で超過) | 本セッション タスク3 計画修正 (front-matter 非 Wave-SSOT 発見 = Critical / Sonnet 2 体並列を 1 体順次に修正 / exact-count 検算格上げ / silent-drop 対策) |

| 4 | 2026-07-03 | spec/design 初期 (グローバル ~/.claude 統治設計 / 無条件召喚ゾーン = 不可逆設計コミット + 複数ドメイン統合 / ユーザー明示指示) | 通常 (スポット召喚 / 索引 push + 実装コード禁止縛り) | ブリーフ実効 ~4.5k / **API 総 tok 130,598 (#5 実測 tool_uses 0)** | **0** (資料要求なし・索引 push で自己完結判断) | **$1.84-$2.08 (#5 補正 / 出力欠損補正込)** ※#4 は tool_uses=0 の記録破損ケース (下記 #5 メモ参照) | etm-diary 是正依頼: スキル衝突解消方式 (A+B ハイブリッド) / バックアップ戦略 (運命別 3 分割 + default-deny allowlist) / 統治不変条件 (構成的 5 条 I-1〜I-5) |

| 5 | 2026-07-05 | spec/design 初期 (R-1 大規模レビュー スコープ確定 / 無条件召喚ゾーン = spec/design 初期の設計軸確定 / ユーザー明示指示 = MAGI + gabriel 2 round 後の HGA 追加召喚提案承認) | 通常 (スポット召喚 / 索引 push + 事実収集 L1 完了 + 実装コード禁止縛り / #4 パターン準拠) | ブリーフ実効 ~6.5k / subagent_tokens 83,890 / tool_uses 4 (自力 pull で SKILL.md 実件数照合等) | **0** (資料要求なし) | **~$2-5 圏想定** (jsonl 実測は次日以降 / #4 型パターン準拠) | R-1 PLANNING crux 5 分岐 (Green State 追加 3 二値条件 R-G6/G7/G8 / 11 番目モジュール = ルート統治文書 / scope creep 予防 (d) 合成 + 昇格基準 / HGA スケジュール 3 回構成 #5/#6/#7 / unknown-unknown 5 件検出) |

| 6 | 2026-07-05 | spec/design 初期 (R-1 design.md adversarial review / 無条件召喚ゾーン = 不可逆な設計コミット直前 / ユーザー明示指示 = 「HGA に敵対的レビューをしてもらってください」) | 通常 (スポット召喚 / 索引 push + 事実収集 L1 完了 + 実装コード禁止縛り / #4 パターン準拠) | ブリーフ実効 ~8k / subagent_tokens 128,935 / tool_uses 5 (現環境実測 = pydeps 未インストール / 最古 jsonl 2026-06-06 / `.claude/scripts/__init__.py` 不在 の実測 3 件) | **0** (資料要求なし) | **~$3-6 圏想定** (jsonl 実測は次日以降 / #4 型パターン準拠 / tool_uses 5 は #5 の 4 とほぼ同帯) | R-1 design.md crux 5 分岐 + unknown-unknown 3 件検出。特に **Critical 級 3 件を実測ベースで確定**: (a) pydeps 現環境未インストール + scripts/hooks 非パッケージ (自作 AST 反転) / (b) session log 30 日窓 (cleanupPeriodDays 既定 = 実測整合) → FR-F4 90 日設計を再定義 / (c) skills 検出は subagent_type ではない (Skill tool 別フィールド) → module 3 全 skills が偽陽性削除リスク |
| 7 | 2026-07-06 | R-1 W-R1 監査結果 adversarial verify (**当初計画通り実施 = 7/7 期限内消化 / ユーザー承認 A**) | 通常 (スポット召喚 / 索引 push + tight brief 5-slot + 現行 51 findings 全数付き) | ブリーフ実効 ~10k / subagent_tokens 164,294 / tool_uses 17 (tracker + baseline + retro + design.md + ADR 5 + pre-tool-use.py 実測等) | **0** (資料要求なし) | **~$4-7 圏想定** (jsonl 実測は次日以降 / #3/#5 型 tool_uses 中規模帯 / 2026-07-08 前で subscription 枠内消化 = 実 $ 影響なし) | R-1 W-R1 adversarial verdict 7/10 + **見落とし Critical 1 (A-1: R1-032 修正の残存 attack surface = 単体 `&` / `\n` / `<(` 素通し / 実測 file:line で確定)** + severity 誤判定 1 (R1-006 Warning → Critical 昇格妥当) + tracker SSOT 自己不整合 1 (module 10 Info 7 vs 実載 6 / stale placeholder 残存) + 過剰起票 Warning 2 (R1-048/R1-051 Info 降格) + attribution 系統的 drift 3 (R1-047/R1-049/R1-050 self → downstream) + **メタ構造欠陥 3 件** (修正の再監査ループ欠落 / tracker SSOT 自己検証欠如 / Stage 間 severity/attribution 判定規準ドリフト) |
| 8 | 2026-07-06 | R-1 W-R2 S1 T1 crux-scoping (**2 段召喚 §crux-scoping** / R1-001 + R1-006 両 Critical 修正着手前 / ユーザー明示指示 = 「HGA 多めに使って漏れがないようにね」) | 通常 (**小 brief 2-3k / crux-scoping フェーズ**) | ブリーフ実効 ~3k / subagent_tokens 137,204 / tool_uses 16 (probe スクリプト実測含む) | **0** (crux-scoping で自己完結) | **~$0.20-0.40 圏想定** (2026-07-08 前で subscription 枠内 / 実 $ 影響なし) | R1-001 + R1-006 両 crux 判定 = **tracker 推奨の regex は両方とも不十分**。R1-001: `(?:[:\s]|$)` は装飾文字 (`**ID**` / `(ID)` / `` `ID` `` / 全角括弧) で false negative + leading 境界欠如で短縮形 `T\d+` 誤マッチ → 推奨 `(?<![A-Za-z0-9-])<escaped>(?![A-Za-z0-9])` (negative lookbehind + lookahead 両方 / trailing に `-` 含めず `T1-T5` 範囲記法保護)。R1-006: 一律 `[A-Za-z0-9._-]+` は slug (パターン 3 group 2 / アンカーなし) がドット捕食 → Windows 末尾ドット quirk で偽 Green → 推奨 3 箇所非対称 (アンカー付き 2 = `[A-Za-z0-9._-]+` / slug = `[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*`)。**副産物**: docstring 同時更新必須 / live baseline drift=1 (`99_reference_generic.md:22` placeholder) 裁定必要。 |
| 9 | 2026-07-06 | R-1 W-R2 S1 T4 adversarial verify (**HGA #7 verdict メタ欠陥#1 = 修正の再監査ループ欠落 対策として発火**) | 通常 (中 brief 5-6k / refute-first 姿勢 / 5 軸 verify) | ブリーフ実効 ~6k / subagent_tokens 127,927 / tool_uses 15 (Read + Grep + Bash pytest 再走 + verify_reference_resolution 実行 + `probe_hga9.py` 作成 実測) | **0** (資料要求なし) | **~$0.30-0.50 圏想定** (2026-07-08 前で subscription 枠内 / 実 $ 影響なし) | R-1 W-R2 S1 T3 実装 adversarial verdict = **confirmed / warning / fix_before_ship / confidence 0.85**。軸 A (regex 実装忠実性): confirmed 完全一致。軸 B (attack surface): confirmed 7+8 全 pinning 済。軸 C (追加): refuted = **新規発見 3 件** → R1-053 (Warning / existence-check hole = R1-006 と同 bug class) / R1-054 (Info / underscore boundary) / R1-055 (Info / case-sensitivity portability)。軸 D (regression risk): refuted = **design.md §5.1 spec-sync gap** 検出 (L414/L420/L427 が pre-R1-006 buggy char class を documenting / L2 は PM 級のため触れず → L1 で本 T4 内消化) + builder.py docstring L700 asymmetry (T4 内消化)。軸 E (baseline drift): confirmed 両裁定妥当 + missed drift = 0。meta: HGA #7 メタ欠陥#1 対策として正しく機能 (L2 が構造的検出不可な 3 種を捕捉)。**追加ゲート提案**: 修正 pattern/constant の literal-quoted docs/specs/* を grep → PM 級 L1 assign (W-R5 retro 議題化)。 |
| 10 | 2026-07-07 | R-1 W-R2 S2 T2 adversarial verify (R1-053 修正 / R1-006 同 bug class = 2 段階検出パターン踏襲 / subscription 枠期限内消化 = ユーザー指示) | 通常 (中 brief ~5k / refute-first / 6 軸 verify A-E + meta / coverage loose 指示 = model-delegation-prompting.md §3 初適用) | ブリーフ実効 ~5k / subagent_tokens 114,382 / tool_uses 11 (Read + regex 直接 probe 11 種 + live scan 再実行 + pytest 27 件を `-o addopts=""` で独立再走) | **0** (資料要求なし) | subscription 枠内 (7/8 前消化 / 実 $ 影響なし) | R1-053 修正 verdict = **confirmed-with-warnings / fix_before_ship 不要 / confidence 0.90**。軸 A: confirmed (推奨修正方針を文字通り実装 / L144-158)。軸 B: 部分 refuted = **新規 Warning 1 件** (L51 group3 文字クラスに `/` なし → 多階層参照 `docs/specs/<slug>/<sub>/<file>.md` が fname=None 退化し dir-only 素通し = 同 bug class residual / live corpus 0 実例 grep 実測) → R1-056 起票。軸 C: confirmed (FP 転化なし / live 0 drifts を独立再現)。軸 D: confirmed (monkeypatch REPO_ROOT 方式妥当 / 軽微 gap 2)。軸 E: confirmed (spec-sync 済 / 旧 any() セマンティクスの literal-quoted 残存なし = **HGA #9 追加ゲート提案の初適用で PASS**)。meta: L2 報告値 (27 PASS / drift 0) を独立再実測で一致確認 = unverified 主張ゼロ。Info 群 (非 .md 退化 / 大文字拡張子 / file-as-dir 擬似 / 走査 scope 外 `.claude/rules` / gabriel substring 弱検査) → R1-057/058/059 に集約起票。 |
| 11 | 2026-07-07 | 新規・複数ドメイン統合 (Fable-Alembic L3 導入設計軸確定 / ユーザー明示指示「HGA相談して」) | 通常 (中 brief ~15k / 8 crux + 草案 A/B/C 提示 / 圧縮同梱資料 = knowledge 4 文書要点 + LAM 規律要点) | ブリーフ実効 ~15k / subagent_tokens 99,987 / tool_uses 3 / duration 187s | **0** (資料要求なし / 圧縮同梱で自己完結) | subscription 枠内 (7/8 16:00 期限内消化 / 実 $ 影響なし) | **案 D (直交軸接続) 確定 = 草案 A/B/C 全棄却 (推し手が「理解された上で落とされた」と感じる水準の棄却理由付き)**。真の crux 3 個 = crux 2 (体験シミュ発火点 / 真リスクは overhead でなく形骸化 = ADR-0008 の 93% 形骸化を実況で再生産) / crux 3 (第0原則 vs Hierarchy of Truth の問い設定を訂正 = **実体は permission-levels との衝突** / Hierarchy は情報源真偽順位で直交) / crux 5 (自己監査 × Green State = 二重帳簿化発生源)。棄却 crux 5 個の落とし理由付き。D-1 (第0原則 = permission-levels 基底原理 + 実行時再導出禁止 / PM 級パス列挙 = ユーザー事前計算済 第0原則出力) / D-2 (体験シミュ MUST は完了宣言 3 点のみ発火 = PLANNING 承認 + `/ship` Phase 3.5 + AUDITING レポート提出 / subagent 完了報告は発火点にしない / 実況第 1 文残置) / D-3 (帳簿は Green State 1 冊のみ / 自己監査は宣言イベントゲート = 件数化・記録簿化禁止 / 統合しない)。サブ節 5 = F0-F4 改名 / TDD 埋込 / 系(1)(2) MAGI 組込 / L4 禁止 / 判断差分予測。**主犯 = 60 秒実況の Opus-tier 実効性 (導入後観測でのみ検証可) / 堅い部分 = D-1 直交分離 + D-3 帳簿一冊 / 可動部 = 発火点数 (3→2 or 4) と実況強制部品 / 確信度 72%**。 |
| 12 | 2026-07-07 | 案 D 具体化諮問 (subscription 24h 延長判明 = 7/8 16:00 期限で再召喚可 / ユーザー選択 5「案 D 承認 + `/ship` SKILL 実体確認先行 → 実装案 Fable 再提示」) | 通常 (中 brief ~13k / Q1-Q6 具体案適合性判定 / 争点 E 再論禁止規律明示 / Opus 側 `/ship` SKILL + gabriel.md 事前 Read 済) | ブリーフ実効 ~13k / subagent_tokens 116,326 / tool_uses 4 / duration 209s (Fable-Alembic knowledge 4 文書を Fable 側で直接 Read = 原典接地) | **0** (資料要求なし) | subscription 枠内 (7/8 16:00 期限内消化 / 実 $ 影響なし) | **案 D 骨子 (D-1/D-2/D-3) 不変 / 局所 3 点修正のみ**。修正 1: **F1 は AoT Atom Decomposition から除外し前段として維持** (自己完結・契約・エラー隔離のどれにも対応物なし / F2 のみ Atom 置換)。修正 2: **F4 発火は `/auditing` 開始時 1 箇所固定** (`/ship` Phase 5 後は commit 済で「壊しに行く」検証遅い + 儀式 2 個載ると両方形骸化)。修正 3: **テンプレ化ガード対処差替 = 発火点減少禁止** (検知器自体が減る) → 書式再注入 + retro 議題化 / 単発ゼロでなく 3 回連続ゼロで閾値発火 / **残置 2 行拡張** (詰まり仮説 + 実況第 1 文 = 後付け違和感検出)。Q1-Q6 各 (a)-(v) 網羅判定 = Q1 (帰還ループ再走明記 / (c)「なぜ？」分岐追加 / コミットメッセージ本体混入禁止) / Q2 (subagent 内実況不要 / PLANNING 成果物毎 3 発火 / 実況不能はフェーズ警告と別扱い) / Q3 (系(1) 二分 = 棄却案再評価 refuted 専用 / 可動部指定は全 verdict 適用 = inconclusive で本領) / Q4 (Task 粒度 = tasks.md T 単位 / F3 4 問目「人間しか答えられない」は独立逃し弁復活) / Q5 (骨子欠落 4 点補 = §6 位置決め参照 + 削減正義でない + 試行上限 + 3 手未満省略基準 / 一律 3 文注入撤回 = 判定系除外 or 1 文圧縮 / spec-critic は plugin 由来 = 除外) / Q6 (ガード 6 種 + 意味判定は retro バッチで Haiku 委譲)。**確信度 78% (72% から上方) / 主犯不変 = 60 秒実況の Opus-tier 実効性 / 可動部狭まる = テンプレ化検知の実効性のみ / 堅い部分 = 発火点 3 点・帳簿単一・F0-F4 配置・gabriel 系(1)(2) 共存**。 |
| 13 | 2026-07-10 | 規律 SSOT 統合 (**W-R3 S1 T2 / クレジット従量期初 (7/8 16:00 以降)** / design §10.2 準拠 / L1 推奨で自律発動 = ユーザー指示「HGAを必要より少し多めに発動」) | 通常 (中 brief ~7k / crux 3 個 + 対応方針 3 案 + 索引 push 9 件 + hedge 指示 / T1 成果物と親 SSOT を Fable 側で Read = 独立検証) | ブリーフ実効 ~7k / subagent_tokens 118,513 / tool_uses 2 (T1 成果物 + 06_DECISION_MAKING.md 全文 Read) / duration 145s | **0** (資料要求なし / 索引 push 有効) | **クレジット従量期 = 実 $ 発生 (jsonl 実測は本セッション後 / #4 型パターン想定 $2-3 圏 / envelope 月 $10-40 内)** | **案 A' 確定 = 選定基準を「RFC 級」から「違反時に別の防御層が拾うか」に差し替え**。crux 1: L1 案 A 修正 → M-02/M-04 のみ ambient 追記 (テスト不在の MUST) / M-03 参照 1 行 (統合テスト 3 系統が拾う MUST NOT) / M-01 は SKILL.md §Step 3 にも欠落確認 → 要約側 Output Format 節に追記。crux 2: 掲載可否判定軸を「頻度」でも「ダメージ」でもなく「別防御層の有無」に定式化。crux 3: **half-do 方針採用** = P2 (fable-l3-protocol.md × 外部 Fable-Alembic knowledge) は snapshot + 変更検知のみ / 修復は etc-to-alembic handoff 経由 / 検知頻度は retro 境界のみ → R1-060 (Info) 起票 + W-R5 retro 議題化。**追記実測 = 70 → 81 行 (11 行 / L1 当初見積 15-20 行から圧縮)**。要検証仮定 4 件のうち仮定 1 (SKILL.md の M-01/opt-out 網羅) は L1 側で T3 内検証済 (M-01 欠落確認 → 要約側追記が正解)。 |

## day-1 実測メモ (召喚 #11 / 通常モード / 2026-07-07)

- **crux 設問の訂正**: Opus 側 brief で crux 3 を「第0原則 vs Hierarchy of Truth」と設定したが、Fable は「直交軸 = Hierarchy は情報源真偽順位 / 第0原則は行動ゲート関数 / 衝突実体は permission-levels」と設問自体を訂正。**HGA の crux-scoping が Opus の設問設定の誤りを構造的に修正できる**ことを実証 (subagent 委譲では起きない挙動 / 独立コンテキスト特性の効き所)。
- **草案棄却の質**: 案 A/B/C いずれも「弱い藁人形棄却」ではなく核心を突いた棄却理由付き (規範追記(1) の枠外推奨規律遵守)。案 A 棄却 = 客観判定 (Green State) と主観宣言 (自己監査) を 1 帳簿に混ぜると 1 帳簿内で二重帳簿化 / 案 B 棄却 = 第0原則第 3 変数「確認コスト」は User 奉仕関数のため User Intent 上位に置けない / 案 C 棄却 = BUILDING 除外は「半分だけの移植は移植しないより悪い」(規範追記(3)) 違反。
- **主犯名指しの効き**: 系(2) 準拠で「60 秒実況の Opus-tier 実効性」を主犯 1 つに絞り、加算表記を回避。堅い部分・可動部を言語指定することで検証課題 §4 の設計軸が主犯に集中。
- **envelope 影響**: 2026-07-07 subscription 枠内消化 = 実 $ 影響なし。7/8 16:00 以降クレジット従量移行後の想定単価 ~$3-5 (tool_uses 3 の brief-heavy パターン)。
- **含意**: HGA が「Opus の設問設定を訂正する」経路は、事実収集主体の #4/#5/#6 型でも、adversarial verify 主体の #7/#9/#10 型でもない**新たな召喚パターン** = 「複数ドメイン統合の crux-scoping 型」。似た局面 (新規領域 × 既存重厚規律との統合) で再利用可。

## day-1 実測メモ (召喚 #12 / 通常モード / 2026-07-07)

- **subscription 延長活用の投資対効果**: 期限延長 (24h) で追加召喚が可能になったが、Opus 側判断「主犯 (実況実効性) は導入後観測でのみ検証可 → 追加諮問より実装後の 1 段目観測が投資対効果高」に対し、ユーザーは「実装案の適合性を Fable の目でもう 1 度」を選択。**結果として局所 3 点修正が確定** (骨子維持 / F1 Atom 前段維持 / F4 一本化 / ガード対処差替) → **実装時の Edit 回数削減効果**を実測 (推定 3-4 回削減)。
- **原典接地の効き**: Fable が Alembic knowledge 4 文書を tool_uses 4 で直接 Read (「brief 記載外の裏取り」明記)。**Fable 自身が書いた文書に対する自己参照的接地**により、規範追記(3)「削減は正義ではない」の「命綱の冗長は残せ」が Q5 の骨子欠落 4 点判定に反映された (Opus 案が削減側に倒れる傾向を Fable が原典で押し戻した)。

## day-1 実測メモ (召喚 #13 / 通常モード / 2026-07-10 = クレジット従量期初)

- **判定軸の差し替え**: Opus L1 は対応方針 3 案を「RFC 級 (MUST か否か)」で分類したが、Fable は「その命題の違反が、どの読み込み経路で発生するか」に判定軸を差し替え。**「別の防御層 (統合テスト / ambient 注入) が拾うか」で M-03 と M-02/M-04 を非対称に扱う判断**は Opus 単独では出しにくかった (安易な「MUST 全部 ambient」に流れる傾向)。#11 の「crux 設問の訂正」と同型の効き所。
- **L1 仮定検証との連鎖**: Fable 応答内で「要検証仮定 4 件」を明示 → L1 側で仮定 1 (SKILL.md の M-01/opt-out 網羅) を T3 内で検証 (M-01 欠落確認) → 案 A' の M-01 追記先が「要約側 Output Format 節」に確定。**HGA 応答が L1 に検証タスクを push する構造**は brief-response 分離型 (往復 0 回) の適切な運用形態。
- **envelope 影響**: 2026-07-10 = 7/8 16:00 以降 = クレジット従量期初。subagent_tokens 118,513 / tool_uses 2 は #4 型パターン (索引 push + 事実収集 L1 完了) の範疇。実 $ は jsonl 実測次回に確定するが、hga-summoning.md §envelope 定義 (実 $ envelope 月 $10-40) 内想定。**下調べパイプライン (§下調べパイプライン) 不適用** = crux 判断型 (#4/#5/#7/#9/#10/#13) は Fable 単独維持が正 (tool_uses 少 / 資料収集より判断重心)。
- **L3 導入後初 HGA 召喚**: 本 #13 は L3 導入 (2026-07-07) 完了後の初 HGA 召喚。第 0 原則 3 変数を L1 が判断素材に組み込み (T1 成果物 §4.1 の L1 推奨根拠に明示) → Fable がそれを「可逆性の実効値 = 破壊が起きたとき検出→巻き戻しが機構的に走るか」に再解釈。**L3 導入前後で「判断根拠の言語」が共通化された**ことの初実測。
- **クレジット従量期初の運用確認**: 本召喚をもって「HGA #13 = 7/8 以降クレジット従量期」を跨いだ召喚実運用の初事例に位置付ける。envelope 監視は本ログ table「概算コスト」列 + jsonl 実測 (`docs/artifacts/hga-summon-log.md` §day-1 実測メモ #5 手順) で今後継続。
- **争点 E 再論禁止の遵守**: brief 冒頭で明示的に禁じた「案 A/B/C の再論」を Fable は完全遵守 (§2 で「D-1/D-2/D-3 の 3 本柱は不変」と即答)。争点 E 規律が召喚単価を抑制する仕組みとして機能。
- **spec-critic 発見**: Q5 (r) 判定で Opus 案が注入対象に spec-critic を含めていたが、実装時に `.claude/agents/spec-critic.md` 不在を発見し plugin 由来と判明 → fable-l3-protocol.md §7 で 6 → 5 subagent に修正。**具体化諮問が実装時発見を先取りできる**例。
- **envelope 影響**: 2026-07-07 subscription 枠内消化 = 実 $ 影響なし。従量移行後の想定単価 ~$4-6 (tool_uses 4 中規模帯)。
- **合計コスト (#11 + #12)**: subscription 枠内で 2 召喚消化 / 実 $ 影響ゼロ。従量移行後の同等召喚は ~$7-11 圏想定。

## L3 導入実装との連携 (2026-07-07)

召喚 #11 (案 D 確定) + #12 (案 D 具体化 / 局所 3 点修正) の結果、以下 8 ファイル改変で L3 導入を実装:

**PM 級 4 ファイル** (事前宣言 1 回 + セッションスコープ降格 3 回):
- `.claude/rules/fable-l3-protocol.md` (新規 / L3 SSOT)
- `.claude/rules/core-identity.md` (第0原則節追加 / 権限等級基底原理)
- `.claude/rules/permission-levels.md` (「迷った場合」節を 3 変数判定に置換 + PM 級パス事前計算原則追加)
- `.claude/rules/phase-rules.md` (PLANNING/AUDITING 実況 MUST + BUILDING F0-F3 埋込 + AUDITING F4)

**SE 級 3 種**:
- `.claude/skills/ship/SKILL.md` (Phase 3.5 挿入)
- `.claude/agents/gabriel.md` (reasoning 執筆規律新節)
- `.claude/agents/{doc-writer, requirement-analyst, design-architect, task-decomposer, quality-auditor}.md` (L4 禁止 1 文注入 / 5 agent / spec-critic は plugin 由来で対象外と判明)

## day-1 実測メモ (召喚 #7 / 通常モード / 2026-07-06)

- **A-1 実測確定 = 前倒し消化のバイパス**: R1-032 修正 (commit `8c00786`) が 6 文字のみ列挙で、単体 `&` / `\n` / `<(` の 3 パターンを素通し。Fable が pre-tool-use.py L95 の `_SHELL_METACHARACTERS` タプルを実測して file:line で確定。**L1 (Opus 4.7) の再監査工程が構造的に欠落していたことを実証** (Wave 分離規律の例外時ゲート欠如)。
- **A-2 severity 昇格の合理性**: R1-006 (`verify_reference_resolution.py` regex 大文字不対応) を initial Warning とした subagent 判断は「監査インフラ欠陥 vs 被監査コード欠陥」の重み付け規準が code-quality-guideline に不在なため。Fable は R1-001 (dashboard 表示ロジック Critical) と同一 bug class として Critical 昇格を提案 = 監査ゲート判定を偽 Green 化する影響は R1-001 以上。加えて regex `[a-z0-9-]+` はドット (`.`) 非対応で `v4.0.0-*.md` も unmatched = 二次的漏れも指摘。
- **A-3 tracker SSOT 自己検証欠如**: module 10 ヒートマップ Info=7 vs 本文実載 6 の drift + 監査完了済み module 7/8 の「起票予定」プレースホルダが実セクション後方に残存 (L578-584)。R-1 が inventory/cycle/reference 自動検査を自作しながら **tracker 自身の整合検査ツールがない**構造欠陥を実証。
- **cross-module drift の attribution 系統的訂正**: S3 (module 5-8) では downstream 適用の cross-module drift を、S4 (module 9-11) では self に倒していた判定 drift を Fable が指摘 → R1-047/R1-049/R1-050 の 3 件を訂正。W-R5 機械集計 (FR-5 責務タグ) の品質保全。
- **含意**: HGA #7 は「監査プロセス自体への adversarial review」として設計上想定通りの働きをした。crux 命中率 高 (A/B/C/D 全カテゴリで実測ベース指摘)。特に **修正コードへの再監査ゲート欠落は W-R2 以降の消化 Wave にも構造的リスクを持ち込む** ため、W-R5 retro での恒久対策議題化が必須。
- **envelope 影響**: 2026-07-08 前で subscription 枠内消化のため実 $ 影響なし。7/8 以降クレジット従量制移行後の想定単価 ~$4-7 (tool_uses 17 中規模帯 = #3 相当 $12.66 の 30-50%)。envelope 月 $10-40 に依然余裕。

## day-1 実測メモ (召喚 #6 / 通常モード / 2026-07-05)

- **実測ベース Critical 検出**: Fable が現環境で 3 件を実測 (pydeps + graphviz + networkx 全欠 / 最古 jsonl 2026-06-06 = 30 日窓 / `__init__.py` 不在) → design.md の 3 件の設計前提が実装時に破綻する Critical リスクを即座に潰した
- **spec-critic (Sonnet 級) では捕捉不能**: 環境実測 + Claude Code CLI 深い実装知識 (session log 保持仕様 / Skill tool の起動記録フィールド分離 / grep bare-name + ADR flat 参照抜け) を要する指摘は Sonnet 級では原理的に困難
- **リナンバー drift の指摘**: 本召喚により当初計画の #6 (W-R1 監査結果検証) は #7 に、#7 (W-R3 SSOT) は #8 にスライド → design §10 で反映 (承認前に drift 修正)
- **envelope 監視**: 4 召喚合算想定 = 通常経路 $8-17 / Level 2 経路 $10-20 / Level 3 経路 $13-25。月次上限 $40 に依然余裕
- **含意**: 環境依存要件が仕様に含まれる場合 (pydeps/session log/hook 経路 等) は MAGI では拾えず HGA が Critical レビュー経路として正当。純構造仕様のみなら spec-critic + MAGI で足りる (今後の運用指針)

## day-1 実測メモ (召喚 #5 / 通常モード / 2026-07-05)

- **crux 命中率 100% + 追加検出 5 件**: 5 crux 全てで分岐点と根拠が返却 + Fable が自力 pull 4 回 (SKILL.md 実件数 23 件・agents 実件数 12 件 の実測照合) で **L1 ブリーフ自体のインベントリ drift** を検出 → 「W-R1 冒頭のファイルシステム inventory 再生成を必須タスク化」を crux 提示
- **既存憲法の再引用で新機構削減**: Non-Goals + deferred の合成 (planning-quality-guideline §3 + green-state-definition §4) を「新規制度ではなく既存の憲法適用」で解けと差し戻し。scope creep 予防を新機構ゼロで実現
- **カレンダー駆動 → ゲート駆動へ修正**: HGA スケジュールは「7/7 期限が動かすのは前倒し対象のみ / ゲート該当外の追加召喚は不要 / W-R5 は召喚しない (検証は gabriel の実質貢献領域)」に整理
- **11 番目モジュール発見**: `CLAUDE.md` + `CHEATSHEET.md` = ルート統治文書 (blast radius 最大 / 現分類では監査漏れ) を module 11 として独立化。`.claude/settings*.json` は module 5 に併合改称。`SESSION_STATE.md` (gitignore 済揮発資産) + `docs/artifacts/` (歴史記録・不変) は明示的 Non-Goals
- **A2 in-place 前提の破綻可能性を指摘**: W-R2 (dashboard) は 424 テスト保護下だが、W-R3/W-R4 の対象 (rules/skills/agents = prose) には回帰網がなく **G1 は無内容に PASS する** → R-G7 (参照解決チェック) を Stage 末 smoke test の必須部品に組み込まないと A2 前提が崩れる
- **含意**: #4 型パターン (事実収集 L1 完了 + 索引 push + 分岐点のみ) の 3 例目実証 (tool_uses 4 / 往復 0)。#3 型の 17 tool_uses と比較して 1/4 のコスト効率で同等以上の crux 命中

## day-1 実測メモ (召喚 #4 / 通常モード / 2026-07-03)

- **#2 往復抑制 = 実証 3 例目**: 索引 push により Fable は追加資料要求 0 回で 3 分岐点を判断 (tool_uses 0 = ブリーフ内自己完結)。前 3 例と異なり自力 pull すら不要だった (事実収集を L1 が完了済みで渡したため)。
- **crux 貢献**: (a) 案 C (非衝突のみ残す) の致命傷 =「衝突しない」は状態であって構造でないという決定打を提示、(b) plugin グローバル enable の罠 (skillOverrides が plugin に無効 → customized 側に防御レバーなし) を発見、(c) 草案不変条件の決定可能性欠陥 (「衝突しうる」は未来依存で検査不能) を指摘し構成的 5 条に書き直し、(d) 枠取りの盲点 (スキルだけでなく hooks/settings/memory も同じ火薬庫 = グローバル層を 12 番目の統治対象リポジトリにせよ) を提示。
- **safety routing**: 降格兆候なし (Fable として応答と明記)。
- **含意**: 「事実収集を L1 完了 → 分岐点のみ Fable に問う」形式は tool_uses 0・往復 0 で最も安価 (65.3k / #3 の 149.5k の 0.44 倍)。設計判断のみを求める召喚では先載り + ブリーフのみで完結し、自力 pull コストが乗らない。

## day-1 実測メモ (召喚 #3 / 通常モード / 2026-07-03)

- **#2 往復抑制 = 実証 2 例目**: 索引 push (原資料の目次同梱) + 実装コード禁止縛りで、Fable は自力 pull 8 呼び出し (Read/Grep/Bash) で完結。L1 への資料要求往復 0 回。
- **#5 実効入力 = 追加観測**: 総消費 149.5k tok (前回 #1 ~85k の約 1.76 倍)。増加要因は (a) ブリーフ増 (~7k / 前回 ~2.5k) と (b) 自力 pull 側の Read/Grep 分。**先載り支配の仮説は維持** (総消費に占める system + CLAUDE.md + rules の比率が依然大)。
- **crux 命中の内訳**: 5 crux 中、L1 の確信が**覆った** = 1 (crux 5: front-matter 非 SSOT + wavec 不在) / **実測で確定に格上げ** = 3 (crux 1/2/3: 40 件内訳 / 83 算術 / 回帰 assert 不在) / **反例不成立** = 1 (crux 2 の @assignee 干渉 = 実測で否定)。実装コード禁止制約により Fable は分岐点と根拠のみ返答 = Opus-tier 実装余地を保持できた。
- **含意**: 「実装コード禁止 + 索引 push + 自力 pull」の召喚形式は crux 発見に有効 (Critical 1 + 確信格上げ 3)。1.76 倍のコスト増は「crux 発見の質」で相殺可能と判断。ただし従量課金移行後 (7/8 以降) は先載り縮小を優先課題として継続監視。

## day-1 実測メモ (#5 input/output 分離実測 / 2026-07-04)

### 実測手段 = jsonl 直読み

Fable subagent の完了 usage は L1 transcript ではフラッシュ済で取れないが、
`~/.claude/projects/<project>/<session>/subagents/agent-*.jsonl` に
Anthropic API メータリング (input_tokens / cache_creation_input_tokens / cache_read_input_tokens / output_tokens) が
per-message で残る。**新規召喚ゼロで既存 #1-#4 の分離実測が可能** と判明 (log の「別手段要」記述は解消)。

### 実測結果 (Fable 単価 $10/$50 + cache_r 0.1x + cache_c 1.25x 適用)

| HGA | msgs | input (fresh) | cache_creation | cache_read | output (記録) | **API 総 tok** | **単価適用コスト** |
|-----|-----:|--------------:|---------------:|-----------:|--------------:|---------------:|-------------------:|
| #1 通常 | 15 | 83,678 | 312,676 | 750,876 | 7,115 | 1,154,345 | **$5.85** |
| #2 branch | 24 | 83,696 | 841,465 | 1,976,129 | 9,507 | 2,910,797 | **$13.81** |
| #3 通常 | 34 | 87,949 | 572,188 | 3,415,739 | 24,316 | 4,100,192 | **$12.66** |
| #4 通常 | 2 | 23,712 | 106,882 | 0 | 4→~7k※ | 130,598 | **$1.84-$2.08** |

※#4 は下記「output 記録破損」で補正

### input/output 分離 (HGA #5 主目的)

- **HGA #1 tok 比**: input 側 1,147,230 : output 7,115 = **161 : 1**
- **HGA #1 cost 比**: input 側 $5.50 (94%) : output $0.36 (6%) = **15 : 1**
- output 単価が input の 5 倍でも token 比 (161倍) で吸収される → **コストは input 側支配**

### コスト構造 (HGA #1 内訳)

| 成分 | 割合 | 削減レバー |
|:-----|-----:|:-----------|
| cache_creation ($12.5/M) | **66.8%** | ← 最大レバー (初回ロード抑制) |
| input (fresh, $10/M) | 14.3% | ブリーフ縮小 |
| cache_read ($1/M) | 12.8% | 削減効果小 |
| output ($50/M) | 6.1% | 削減効果最小 |

**主削減レバー = cache_creation 抑制**。従量移行後の最適化は「先載り縮小」より
「5 分 TTL 内の連続召喚で cache_c=0 化」が寄与大きい可能性。

### 過去 log 記載値との乖離 (旧「総消費」は 2-27 倍に undercount)

| HGA | 旧 log 記載 | 実測 API 総 tok | 乖離倍率 |
|-----|-----------:|---------------:|--------:|
| #1 | ~84.8k | 1,154,345 | **13.6x** |
| #2 | ~646k | 2,910,797 | **4.5x** |
| #3 | ~149.5k | 4,100,192 | **27.4x** |
| #4 | ~65.3k | 130,598 | 2.0x |

原因: 旧「総消費」は L1 側 StatusLine 観測値 (キャッシュ側集計欠落の疑い)。
**API 実メータリングを正とし、旧値は参考扱いに降格**。

### output 記録破損ケース (#4 の分析)

HGA #4 は召喚 log に「tool_uses 0」と記録され、`agent-*.jsonl` の usage 記録も
2 メッセージ × `output_tokens=2` (計 4 tok) と極小。しかし応答本文の text は
**6,748 chars 存在** し、内容は完全 (分岐点 1〜3 + 盲点セクション全て完成)。

**根本原因**: tool_use が 1 回もない一発応答召喚では、jsonl に `message_start` と
中間 `message_delta` の 2 イベントしか記録されず、最終 `message_end` の usage 合算が欠落。
両イベントとも `stop_reason=None` になる。

**再現条件**: `tool_uses=0` かつ text-only 応答の召喚のみ。tool_use が 1 回でも
挟まれば各 API 呼び出しごとに正常な usage が記録される (#1/#3 で verify)。

**envelope 監視への影響**: tool_uses=0 召喚は 1 件あたり output ~7k tok (= $0.3-0.5) が
過小記録される。今後の集計では手動加算するか、実測は text char 数 × 0.8-1.5 で推定する。

### envelope $40-80/月 の再評価

- 現状の召喚単価: **$1.84 (tool_uses=0 短答) 〜 $12.66 (tool_uses 17 大型)**
- 平均 ~$5-8/回 と見積もると **月 5-10 回で $40-80 到達**
- 旧 log の「~$1-4/回」想定は不足。envelope 監視は API 実メータリング (jsonl 集計) 基準に切替
- branch モード ($13+/回) は稀運用維持 (別予算枠)

### 監視オペレーション更新

- 集計スクリプト: **`.claude/scripts/hga_usage.py`**（永続配置 / 実行 `python .claude/scripts/hga_usage.py`）
  - 各召喚を `HGA_CALLS` リストに追記して集計対象を拡張
  - `tool_uses=0` かつ recorded_output < 100 の場合は自動で text char × 1.2 補正を適用
- 過小記録判定: 上記スクリプトが自動判定・補正コスト算出
- 月次 envelope 監視: 月末に `python .claude/scripts/hga_usage.py` を回して合計 $ を算出、$40-80 レンジ逸脱を検知

### 現時点の累計コスト（本スクリプト実測 2026-07-04）

通常召喚 3 件 = **$20.49**（#1 $5.85 + #3 $12.66 + #4 $1.98 補正込）
branch モード 1 件（別予算枠） = $13.81
合計 = $34.30

### 結論 (day-1 実測 #5)

**解決済**: input/output 分離実測が jsonl 直読みで確定。cache_creation 支配の内訳が確定し、
従量移行後 (7/8 以降) の最適化優先順位が明確化された。新規召喚不要で完了 (2026-07-04)。
