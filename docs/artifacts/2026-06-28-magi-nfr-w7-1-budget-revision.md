# MAGI 議事録 — NFR-W7-1 CSS 予算根本見直し（AoT 5 Atom）

- 日付: 2026-06-28
- 起案者: L1（Opus 4.7）
- 起案契機: Wave 7 Stage 3 BUILDING 着手時に CSS 予算逼迫（残 18 bytes 想定）が顕在化。L2 (T52 担当) が +499 bytes (181 超過) を L1 に保留報告 → L1 が「予算根拠そのものの再検討」を提起 → ユーザー指示で AoT 合議実施。
- 議事方式: AoT（Atom of Thought）5 Atom 分解 + 各 Atom で MAGI（MELCHIOR / BALTHASAR / CASPAR）合議 + Reflection 1 回
- 適用条件確認（CLAUDE.md decision-making.md）:
  - 判断ポイント 2 以上 ✅（予算値妥当性 / 改定タイミング / 改定範囲 / 形式 / 運用ポリシー）
  - 影響レイヤー/モジュール 3 以上 ✅（requirements.md / design.md / tasks.md / execution-plan.md / Wave 6 NFR との関係）
  - 有効な選択肢 3 以上 ✅（撤廃 / 維持 / 緩和 / SHOULD 化 / 動的計算 / レベル制 etc.）

---

## §1 関係する諸条件（広めに設定）

- **配信モデル**: dashboard.html は `file://` + ローカル localhost 限定（wave6 + wave7 requirements で確認）
- **将来計画**: Phase 2（B-5 future-candidates）で MCP サーバー化案あり → HTML 配信モデル自体が変わる可能性
- **利用シーン**: 個人開発 + AI 補助（LAM 単独利用）
- **業界相場**: 初期 CSS の Performance budget は 14 KiB（TCP slow-start）/ 一般 web では 50-150 KiB 初期 CSS が普通
- **過去経緯**: Wave 6 NFR-W6-3 = 「追加 CSS ≤ 10 KB」（キリ番 / 業界相場 14 KiB 未満）
- **設計哲学**: ミニマル dashboard / 規律自体に教育的価値あり
- **B-5 残骨子**: ⑥ プロジェクト俯瞰オーケストレータ = dashboard 拡張余地大
- **技術負債**: 案 H minify 強制で Section 1-14 と一貫性喪失
- **MUST/SHOULD レベル**: NFR-W7-1 は **MUST**（RFC 2119）→ 変更は PM 級

---

## §2 AoT Decomposition

| Atom | 判断内容 | 依存 |
|:-----|:---------|:-----|
| **A1** | NFR（CSS 予算）の存在意義の根本検証 — そもそも何のための規律か | なし |
| **A2** | 完全撤廃 vs 数値設定 vs 別形式の比較評価 | A1 |
| **A3** | 数値設定の場合の妥当な値（10 KiB / 16 KiB / 32 KiB / 動的） | A2(維持) |
| **A4** | 改定後の運用ポリシー — 同事象再発時の対応 | A2 |
| **A5** | NFR 改定プロセスのメタ規約 — 今回の教訓の制度化 | A1-A4 |

---

## §3 各 Atom の MAGI 合議

### Atom A1: NFR（CSS 予算）の存在意義

**[MELCHIOR]**（推進 / 規律維持の価値）:
予算規律は 3 つの価値を持つ —
1. 教育的規律: 「際限なく CSS 追加できない」制約が設計の純度を保つ。Wave 6 が 9,922 bytes でミニマル CSS を実現できたのは予算のおかげ
2. 将来の MCP サーバー化に備えた CSS Mass 管理: Phase 2 で動的 HTML になる場合、CSS バンドルサイズは依然意味がある
3. 退行防止: 「気付いたら 50 KiB」を防ぐ CI 的な数値ゲート

**[BALTHASAR]**（批判 / 規律の実害）:
存在意義は薄い —
1. 配信モデルが `file://`: TCP slow-start も CRP も無関係。Performance budget の理論的根拠が消える
2. Lighthouse Performance スコア: 10 KiB と 50 KiB で誤差レベル（Wave 6 で Performance 言及なし）
3. 判断ループ overhead: 今回のように毎回 MAGI 合議発生 = 認知コスト累積。規律のメンテナンスコスト > 規律の便益になっている
4. キリ番継承: 「10 KiB = 1024 × 10」は技術根拠ゼロ。Wave 6 から「なんとなく」継承
5. 代替手段あり: Lighthouse Performance スコア閾値（例: ≥ 90）で代替可能 = NFR-W7-2 の Accessibility ≥ 95 と同様の「結果ベース」NFR で代替できる

**[CASPAR]**（調停 / 結論）:
規律の教育的価値は認めるが、現状の数値ゲート形式は実害が便益を上回る。
- MELCHIOR の (1)(3) の規律価値は否定しない → 何らかの規律は維持
- BALTHASAR の (1)(2)(3)(4) は妥当 → 現状の固定数値ゲートは見直し
- 結論: NFR は存続させるが、形式を「固定 bytes 値」から「上限値 + 3 段階レベル制 + SHOULD」にシフト

---

### Atom A2: 完全撤廃 vs 数値設定 vs 別形式

**[MELCHIOR]**（推進 / 撤廃推進）:
- 完全撤廃: ローカル `file://` で実害ゼロ → 制約を消すべき
- 案: NFR-W7-1 を Wave 8 で撤廃 + Lighthouse Performance ≥ 90（SHOULD）で代替

**[BALTHASAR]**（批判 / 完全撤廃のリスク）:
- 退行防止の喪失: 「気付いたら CSS が肥大」を検知する手段が消える（Lighthouse Performance はネットワーク条件依存で安定しない）
- ミニマル設計哲学の風化: Wave 6 のミニマル達成は規律のおかげ
- MCP サーバー化時の手戻り: Phase 2 で配信モデル変わったら予算を再設定するコストが大

**[CASPAR]**（調停 / 結論）:
3 案を整理 —
- (a) 完全撤廃 — 規律喪失リスク
- (b) 固定数値維持 — 今回の問題が再発
- (c) 緩和 + SHOULD 化 — 数値は持つが MUST → SHOULD に降格 + 「次マイルストーン値」を倍以上に設定

**結論**: **(c) 緩和 + SHOULD 化** を採用。
理由: A1 結論「規律存続 + 形式シフト」と整合。MUST → SHOULD で「絶対遵守」から「目安」に変わり、判断ループが減る。「何バイトにするか」は A3 で詳細化。

---

### Atom A3: 数値設定の場合の妥当な値

**[MELCHIOR]**（推進 / 大胆な拡張）:
- 32 KiB（32,768 bytes）— 業界相場 50-150 KiB 初期 CSS から見れば十分ミニマル / 当面 3-5 倍の余裕 / Wave 8〜10 でも余裕
- Wave 6 → 7 で +2,300 bytes（314 bytes/Wave 平均 ≈ 100 Wave 分の余裕）

**[BALTHASAR]**（批判 / 緩和し過ぎ）:
- 32 KiB は過剰。ミニマル設計哲学から逸脱 → 「予算ある意味」が消える
- 現状 10,201 → 16 KiB（16,384 bytes）で残 6,183 bytes ≈ 20 Wave 分。十分長い目に取れる
- Wave 6 ベース 9,922 / Wave 7 ベース 10,201 → 1 Wave あたり ~300 bytes 成長率
- 20 Wave 分余裕 = B-5 完走 + B-6 中盤までカバー

**[CASPAR]**（調停 / 結論）:
- MELCHIOR の「将来余地」と BALTHASAR の「ミニマル哲学」を両立
- 結論: **16 KiB（16,384 bytes）** + SHOULD 化
- 16 KiB は 14 KiB（TCP slow-start）を僅かに超えるが、`file://` で TCP 関係ないので問題なし
- 16 KiB = 約 60% の余裕（現状 10,201 / 上限 16,384 / 残 6,183 bytes）
- 1 Wave +300 bytes 成長で 20 Wave 分 ≈ 約 5 年の改修余地（個人開発ペース）

---

### Atom A4: 改定後の運用ポリシー（再発対応）

**[MELCHIOR]**（推進 / 軽量プロセス）:
- SHOULD なら違反しても警告のみ → 自動失敗しない → MAGI 合議発生しない
- 上限到達時は L1 がワンライナーで「Wave X で 16 KiB → 24 KiB に拡張」と PM 補追

**[BALTHASAR]**（批判 / 自堕落リスク）:
- SHOULD でも「警告無視」が常態化する危険
- 「予算到達 = 設計の見直しタイミング」という重要シグナルを失う
- 自動失敗しない代わりに、到達時に必ず retro 議題化という別ガードが必要

**[CASPAR]**（調停 / 結論）:
- 3 段階レベル制を導入 —
  1. **緑帯（< 70% = < 11,469 bytes）**: 自由に追加
  2. **黄帯（70-90% = 11,469-14,745 bytes）**: Wave 開始時に CSS 追加見込みを記録 + 適宜縮退検討
  3. **赤帯（≥ 90% = ≥ 14,746 bytes）**: その Wave の retro で予算改定議題を必須化 + 改定 or ミニマル化を選ぶ
- 上限到達自体は MUST 違反にしない（SHOULD）が、retro 議題化（プロセスの MUST）は維持
- 改定プロセス: 改定は PM 級だが「retro 議題から MAGI 合議 → 補追」の標準ルートを用意

---

### Atom A5: NFR 改定プロセスのメタ規約

**[MELCHIOR]**（推進 / 制度化メリット）:
- 今回の教訓: 「Wave 6 のキリ番継承を v0.2.3 まで 7 Wave 検証なし」は構造的問題
- メタ規約: NFR は Milestone（B-N）完了時に必ず再評価（寿命管理）
- これにより Wave 6 → Wave 12 まで継承し続ける事故を防ぐ

**[BALTHASAR]**（批判 / 制度の重さ）:
- 全 NFR を Milestone 単位で再評価 = retro が重くなる
- 多くの NFR は変更不要（「pytest 全件 PASS」等は常識）
- 「変更候補がある NFR のみ再評価」に絞るべき

**[CASPAR]**（調停 / 結論）:
- メタ規約として以下を制度化 —
  1. **NFR 寿命タグ**: NFR に「継承元 / 最終再評価」のような継承履歴を必須付与
  2. **Milestone 完了時のリスト走査**: retro Step 4（知見蓄積）で「継承 NFR の妥当性チェック」を 1 行追加
  3. **数値ゲートは原則 SHOULD**: MUST は「実害が明確な NFR」のみ（例: pytest 全件 PASS, Accessibility ≥ 95）
- 今回の予算問題を `docs/artifacts/knowledge/` に「NFR 寿命管理」として記録

---

## §4 Reflection

致命的な見落としチェック:

1. **MCP サーバー化（Phase 2 future-candidates）の影響**: A1 で言及済 / A3 16 KiB は Phase 2 でも妥当 ✅
2. **既存 Wave 6 NFR-W6-3 との整合**: Wave 6「10 KB」を Wave 7+ で「16 KiB」に上書きする場合、Wave 6 設計書との整合は注記対応（Wave 7 NFR で「Wave 6 NFR-W6-3 を上書き」と明記）
3. **A3 16 KiB の根拠の弱さ**: 「20 Wave 分の余裕」は推測。実際の成長率は Wave 6 → 7 の 1 サンプルのみ。ただし SHOULD なので超過しても破綻しない → 16 KiB の数値根拠の弱さは問題にならない ✅
4. **MUST → SHOULD 降格の意味**: Wave 7 内で MUST 規約を SHOULD に降格は PM 級 + 仕様精神の変更 → ユーザー判断必須。本合議で結論を提示しユーザーが最終承認する形式 ✅
5. **設計哲学への影響**: 「ミニマル dashboard」哲学を弱めるか → A1 結論「規律存続 + 形式シフト」で哲学維持 ✅
6. **見落とし**: dashboard 以外の CSS バンドル（LAM 全体の CSS 設計指針）との関係 → 影響なし（dashboard は単一 file の閉じたスコープ）

**致命的見落とし: なし → 結論確定**

---

## §5 AoT Synthesis（統合結論）

| 項目 | 改定案 |
|:---|:---|
| NFR-W7-1 義務レベル | MUST → **SHOULD**（実害は限定的 / 規律目安として残す） |
| 上限値 | 10,240 bytes → **16,384 bytes（16 KiB）**（現状の約 1.6 倍） |
| 形式 | 固定数値ゲート → **3 段階レベル制（緑/黄/赤）** |
| 赤帯到達時 | retro 議題化必須 + MAGI 合議 → 改定 or ミニマル化判断 |
| 継承管理 | NFR に「継承元 / 最終再評価」タグ付与 + Milestone 完了 retro で走査 |
| Lighthouse Performance | 補助 NFR として NFR-W7-2 Performance ≥ 90（SHOULD）を Wave 7+ で追加検討（代替担保 / 別議題） |
| Wave 6 NFR-W6-3 との関係 | Wave 7 で上書き（Wave 6 設計書は歴史的記述として保持 / Wave 8 以降は本改定値） |

### Stage 3（進行中）への影響

| 案 | 内容 | 評価 |
|:---|:---|:---|
| **案 α**（採用） | Stage 3 を巻き戻し → T52 を素直実装（design.md §8 サンプル CSS そのまま + コメント付き）→ 新予算 16 KiB 下で完成 | minify 技術負債ゼロ / overhead = T52 再委譲分 |
| 案 β（不採用） | 案 H（minify）で Stage 3 完了 → 次セッションで予算改定 → 後追いで Stage 3 CSS を素直化 | 後追いリファクタ発生 |

---

## §6 改定の実施プロセス（PM 級）

1. MAGI 合議完了（本書 A1-A5 / Reflection 済）
2. **ユーザー承認**（2026-06-28: ユーザーが案 α を選択）
3. requirements.md v0.2.4 補追（NFR-W7-1 改定 + AC-W7-5 + G4）
4. design.md v0.2.4 補追（§8 予算事前評価 + 縮退オプション参考保持）
5. tasks.md v0.2.4 補追（T-S3-3 / T-S4-4 / リスク表 / T52 完了条件）
6. execution-plan.md v0.4.0 補追（§6 / §8 / §9）
7. `docs/artifacts/knowledge/nfr-lifecycle-management.md` 新設（NFR 寿命管理ルール）

---

## §7 参照

- [Wave 7 requirements.md](../specs/b4-dashboard/wave7/requirements.md) v0.2.4 Approved
- [Wave 7 design.md](../specs/b4-dashboard/wave7/design.md) v0.2.4 Approved
- [Wave 7 tasks.md](../specs/b4-dashboard/wave7/tasks.md) v0.2.4 Approved
- [Wave 7 Stage 3 execution-plan.md](./wave7-stage3-execution-plan.md) v0.4.0 Approved
- [NFR 寿命管理ルール](./knowledge/nfr-lifecycle-management.md)
- [Wave 6 NFR-W6-3 原典](../specs/b4-dashboard/wave6/design.md#css-10-kb-超過時の対応フロー)
- [.claude/rules/decision-making.md](../../.claude/rules/decision-making.md) MAGI System SSOT
